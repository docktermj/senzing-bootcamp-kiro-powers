"""Integration tests for the full module-completion artifact flow.

Feature: module-completion-artifacts (BUGFIX) — task 5.

These tests exercise the two cooperating pieces of the fix end-to-end against
real files on disk in ``tmp_path``:

    * the deterministic planner ``senzing-bootcamp/scripts/completion_artifacts.py``
      (gap detection, duration computation, backfill planning, and its CLI), and
    * the structural validator ``senzing-bootcamp/scripts/validate_completion_artifacts.py``.

The flow modeled here is the one the aligned hooks / ``module-completion.md``
workflow drive: on a completion boundary, run ``completion_artifacts.py --plan``,
then generate exactly the missing recap sections, journal entries, and
certificates (sourcing Durations from the planner, omitting when unreliable).

Scenarios (from the design's Integration Tests):
    1. Final module of a track (Module 7 Core, Module 11 Advanced): recap section,
       journal entry, and certificate all appear, and the validator passes.
    2. Backfill on a project mirroring the reported state ([1..7] complete with a
       partial artifact set): the artifact set is complete and consistent after.
    3. Context switching across modules then completing: correct per-module
       Durations and a monotonic Total Duration, with omission on modules lacking
       reliable timestamps.

Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make scripts importable (scripts aren't packages).
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import completion_artifacts as planner  # noqa: E402
import validate_completion_artifacts as validator  # noqa: E402

# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

BOOTCAMPER = "Bootcamper"
START_DATE = "2025-01-10"
STARTED_AT = "2025-01-10T09:00:00Z"

MODULE_NAMES: dict[int, str] = {
    1: "Business Problem",
    2: "SDK Setup",
    3: "System Verification",
    4: "Data Mapping",
    5: "Loading Records",
    6: "Querying Entities",
    7: "Exploring Results",
    8: "Data Sources at Scale",
    9: "Tuning Resolution",
    10: "Operationalizing",
    11: "Production Deployment",
}

_DURATION_RE = re.compile(r"\d+\s*(d|h|m|s)", re.IGNORECASE)
_PLACEHOLDER_RE = re.compile(r"module\s+\w+\s+session", re.IGNORECASE)


def _looks_like_duration(text: str | None) -> bool:
    """Return True when text reads as a real elapsed duration (e.g., '1h 12m')."""
    return text is not None and bool(_DURATION_RE.search(str(text)))


def _is_placeholder(text: str | None) -> bool:
    """Return True for empty/missing values and non-time 'Module N session' strings."""
    if text is None or not str(text).strip():
        return True
    if _PLACEHOLDER_RE.search(str(text)):
        return True
    return _DURATION_RE.search(str(text)) is None


def _ascending_step_history(modules: list[int], *, hours_apart: int = 1) -> dict:
    """Build a step_history with valid, ascending ISO 8601 timestamps.

    Module N's ``updated_at`` is ``STARTED_AT`` plus ``N * hours_apart`` hours, so
    every module has reliable, ordered timing.

    Args:
        modules: Module numbers to include.
        hours_apart: Hours between consecutive module completions.

    Returns:
        A step_history dict keyed by module-number strings.
    """
    base_hour = 9
    history: dict[str, dict[str, object]] = {}
    for m in sorted(modules):
        hour = base_hour + m * hours_apart
        day = 10 + hour // 24
        hour = hour % 24
        history[str(m)] = {
            "last_completed_step": 5,
            "updated_at": f"2025-01-{day:02d}T{hour:02d}:00:00Z",
        }
    return history


# ---------------------------------------------------------------------------
# On-disk artifact helpers (model what the workflow/hooks write)
# ---------------------------------------------------------------------------


def _recap_header(total_duration: str | None) -> str:
    """Format the recap file header block."""
    total = total_duration if total_duration is not None else "(in progress)"
    return (
        "# Senzing Bootcamp Recap\n"
        "\n"
        f"**Bootcamper:** {BOOTCAMPER}\n"
        f"**Started:** {STARTED_AT}\n"
        f"**Total Duration:** {total}\n"
        "\n"
        "---\n"
    )


def _recap_section(module: int, date: str, duration: str | None) -> str:
    """Format a single recap module section.

    The ``### Duration`` field is omitted entirely when ``duration`` is ``None``
    (unreliable timing), never written as a placeholder.
    """
    parts = [
        "\n",
        f"## Module {module}: {MODULE_NAMES[module]} — {date}\n",
        "\n",
        "### Information Shared\n",
        f"- Worked through Module {module}\n",
    ]
    if duration is not None:
        parts.append("\n### Duration\n")
        parts.append(f"{duration}\n")
    parts.append("\n---\n")
    return "".join(parts)


def _set_total_duration(recap_content: str, total_duration: str | None) -> str:
    """Rewrite the header ``**Total Duration:**`` line in recap content."""
    if total_duration is None:
        return recap_content
    return re.sub(
        r"^\*\*Total Duration:\*\*.*$",
        f"**Total Duration:** {total_duration}",
        recap_content,
        count=1,
        flags=re.MULTILINE,
    )


def _date_for(step_history: dict, module: int) -> str:
    """Completion date for a module (its updated_at, or a fallback)."""
    entry = step_history.get(str(module))
    if isinstance(entry, dict) and isinstance(entry.get("updated_at"), str):
        return entry["updated_at"]
    return f"2025-01-10T1{module}:00:00Z"


def _write_initial_artifacts(
    *,
    recap_path: Path,
    journal_path: Path,
    progress_dir: Path,
    step_history: dict,
    present_modules: list[int],
    durations: dict[int, str],
    total_duration: str | None,
) -> None:
    """Create the starting (partial) artifact set on disk.

    Writes recap sections, journal entries, and certificates only for
    ``present_modules`` — modeling a project where some completions never
    produced their artifacts.
    """
    recap_path.parent.mkdir(parents=True, exist_ok=True)
    progress_dir.mkdir(parents=True, exist_ok=True)

    recap = _recap_header(total_duration)
    for m in sorted(present_modules):
        recap += _recap_section(m, _date_for(step_history, m), durations.get(m))
    recap_path.write_text(recap, encoding="utf-8")

    journal = validator.format_journal_header(BOOTCAMPER, START_DATE)
    for m in sorted(present_modules):
        journal += validator.format_journal_entry(
            module_number=m,
            module_name=MODULE_NAMES[m],
            date=_date_for(step_history, m),
            summary=f"Completed Module {m}",
            artifacts=[f"docs/module_{m}.md"],
            why_it_matters=f"Module {m} matters",
            takeaway="N/A",
        )
    journal_path.write_text(journal, encoding="utf-8")

    for m in sorted(present_modules):
        (progress_dir / f"MODULE_{m}_COMPLETE.md").write_text(
            f"# Module {m} Complete\n", encoding="utf-8"
        )


def _apply_plan(
    plan,
    *,
    recap_path: Path,
    journal_path: Path,
    progress_dir: Path,
    step_history: dict,
) -> None:
    """Apply a BackfillPlan to disk: append missing artifacts, never re-emit.

    Sources per-module Durations and the header Total Duration from the plan,
    omitting the Duration field when the planner provides no value.
    """
    # Recap: append the missing sections, then refresh the header Total Duration.
    recap = recap_path.read_text(encoding="utf-8")
    for m in plan.recap_modules:
        recap += _recap_section(m, _date_for(step_history, m), plan.module_durations.get(m))
    recap = _set_total_duration(recap, plan.total_duration)
    recap_path.write_text(recap, encoding="utf-8")

    # Journal: append the missing entries.
    journal = journal_path.read_text(encoding="utf-8")
    for m in plan.journal_modules:
        journal += validator.format_journal_entry(
            module_number=m,
            module_name=MODULE_NAMES[m],
            date=_date_for(step_history, m),
            summary=f"Completed Module {m}",
            artifacts=[f"docs/module_{m}.md"],
            why_it_matters=f"Module {m} matters",
            takeaway="N/A",
        )
    journal_path.write_text(journal, encoding="utf-8")

    # Certificates: write the missing ones (uniform application).
    for m in plan.certificate_modules:
        (progress_dir / f"MODULE_{m}_COMPLETE.md").write_text(
            f"# Module {m} Complete\n", encoding="utf-8"
        )


def _write_progress(progress_path: Path, modules_completed: list[int], step_history: dict) -> None:
    """Write a minimal config/bootcamp_progress.json."""
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(
        json.dumps(
            {
                "modules_completed": modules_completed,
                "step_history": step_history,
                "started_at": STARTED_AT,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _plan_via_cli(
    *,
    progress_path: Path,
    recap_path: Path,
    journal_path: Path,
    progress_dir: Path,
    capsys,
):
    """Run the planner CLI ``--plan`` and return the parsed JSON payload.

    Exercises the full on-disk discovery + planning path the workflow uses.
    """
    capsys.readouterr()  # clear any buffered output from prior CLI runs
    with pytest.raises(SystemExit) as exc:
        planner.main(
            [
                "--progress", str(progress_path),
                "--recap", str(recap_path),
                "--journal", str(journal_path),
                "--progress-dir", str(progress_dir),
                "--plan",
            ]
        )
    assert exc.value.code == 0
    out = capsys.readouterr().out
    return json.loads(out)


def _check_via_cli(
    *,
    progress_path: Path,
    recap_path: Path,
    journal_path: Path,
    progress_dir: Path,
) -> int:
    """Run the planner CLI ``--check`` and return its exit code."""
    with pytest.raises(SystemExit) as exc:
        planner.main(
            [
                "--progress", str(progress_path),
                "--recap", str(recap_path),
                "--journal", str(journal_path),
                "--progress-dir", str(progress_dir),
                "--check",
            ]
        )
    return int(exc.value.code)


def _validate(progress_path: Path, journal_path: Path, recap_path: Path) -> int:
    """Run validate_completion_artifacts.main and return its exit code."""
    with pytest.raises(SystemExit) as exc:
        validator.main(
            [
                "--progress", str(progress_path),
                "--journal", str(journal_path),
                "--recap", str(recap_path),
            ]
        )
    return int(exc.value.code)


def _discover_certificates(progress_dir: Path) -> set[int]:
    """Return module numbers with a MODULE_N_COMPLETE.md certificate on disk."""
    found: set[int] = set()
    for child in progress_dir.iterdir():
        match = re.search(r"MODULE_(\d+)_COMPLETE\.md$", child.name, re.IGNORECASE)
        if match:
            found.add(int(match.group(1)))
    return found


# ===========================================================================
# Scenario 1 — Final module of a track
# ===========================================================================


class TestFinalModuleOfTrackCompletionFlow:
    """The final module of a track gets the full artifact set via the flow.

    Models boundary detection being shadowed at track end: every module is in
    ``modules_completed`` but the final module's artifacts were never produced.
    Running the planner-driven flow must backfill the recap section, journal
    entry, and certificate for the final module, and the validator must pass.

    Validates: Requirements 2.1, 2.4, 2.5, 2.6
    """

    def _run_flow(self, tmp_path: Path, capsys, completed: list[int], final: int) -> None:
        """Build a state missing the final module's artifacts and backfill it."""
        recap_path = tmp_path / "docs" / "bootcamp_recap.md"
        journal_path = tmp_path / "docs" / "bootcamp_journal.md"
        progress_dir = tmp_path / "docs" / "progress"
        progress_path = tmp_path / "config" / "bootcamp_progress.json"

        step_history = _ascending_step_history(completed)
        _write_progress(progress_path, completed, step_history)

        # Pre-fill artifacts for every module EXCEPT the final one (shadowed).
        present = [m for m in completed if m != final]
        full_plan = planner.plan_backfill(
            planner.ProgressState(completed, step_history, STARTED_AT),
            planner.ArtifactInventory(),
        )
        _write_initial_artifacts(
            recap_path=recap_path,
            journal_path=journal_path,
            progress_dir=progress_dir,
            step_history=step_history,
            present_modules=present,
            durations=full_plan.module_durations,
            total_duration=full_plan.total_duration,
        )

        # Pre-conditions: final module's artifacts are absent; the bug is detected.
        assert f"## Module {final}:" not in recap_path.read_text(encoding="utf-8")
        assert final not in _discover_certificates(progress_dir)
        assert _check_via_cli(
            progress_path=progress_path,
            recap_path=recap_path,
            journal_path=journal_path,
            progress_dir=progress_dir,
        ) == 1, "Bug condition (missing final-module artifacts) must be detected."

        # Run the planner-driven flow and apply the backfill.
        payload = _plan_via_cli(
            progress_path=progress_path,
            recap_path=recap_path,
            journal_path=journal_path,
            progress_dir=progress_dir,
            capsys=capsys,
        )
        assert final in payload["recap_modules"]
        assert final in payload["journal_modules"]
        assert final in payload["certificate_modules"]

        plan = planner.plan_backfill(
            planner.ProgressState(completed, step_history, STARTED_AT),
            planner.ArtifactInventory(
                recap_sections=set(present),
                journal_entries=set(present),
                certificates=set(present),
            ),
        )
        _apply_plan(
            plan,
            recap_path=recap_path,
            journal_path=journal_path,
            progress_dir=progress_dir,
            step_history=step_history,
        )

        # Post-conditions: all three artifacts for the final module now appear.
        recap_content = recap_path.read_text(encoding="utf-8")
        journal_content = journal_path.read_text(encoding="utf-8")
        assert f"## Module {final}:" in recap_content
        assert validator.count_recap_sections(recap_content) == sorted(completed)
        journal_doc = validator.parse_journal(journal_content)
        assert sorted(e.module_number for e in journal_doc.entries) == sorted(completed)
        assert final in _discover_certificates(progress_dir)
        assert _discover_certificates(progress_dir) == set(completed)

        # The structural validator passes, and the bug condition is cleared.
        assert _validate(progress_path, journal_path, recap_path) == 0
        assert _check_via_cli(
            progress_path=progress_path,
            recap_path=recap_path,
            journal_path=journal_path,
            progress_dir=progress_dir,
        ) == 0

    def test_core_track_final_module_7(self, tmp_path: Path, capsys) -> None:
        """Module 7 (final Core module) gets recap + journal + certificate."""
        self._run_flow(tmp_path, capsys, completed=[1, 2, 3, 4, 5, 6, 7], final=7)

    def test_advanced_track_final_module_11(self, tmp_path: Path, capsys) -> None:
        """Module 11 (final Advanced module) gets recap + journal + certificate."""
        self._run_flow(
            tmp_path,
            capsys,
            completed=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            final=11,
        )


# ===========================================================================
# Scenario 2 — Backfill on the reported defect state
# ===========================================================================


class TestBackfillReportedState:
    """Backfill completes a project mirroring the reported partial state.

    Reported: modules_completed [1..7], recap [1-6], journal [3,6,7],
    certificates [6,7], placeholder Durations. After the planner-driven backfill
    the per-module artifact set must be complete and consistent.

    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
    """

    def test_reported_state_is_complete_and_consistent_after_backfill(
        self, tmp_path: Path, capsys
    ) -> None:
        """The full flow fills every gap and the validator passes afterward."""
        completed = [1, 2, 3, 4, 5, 6, 7]
        recap_present = [1, 2, 3, 4, 5, 6]
        journal_present = [3, 6, 7]
        cert_present = [6, 7]

        recap_path = tmp_path / "docs" / "bootcamp_recap.md"
        journal_path = tmp_path / "docs" / "bootcamp_journal.md"
        progress_dir = tmp_path / "docs" / "progress"
        progress_path = tmp_path / "config" / "bootcamp_progress.json"

        step_history = _ascending_step_history(completed)
        _write_progress(progress_path, completed, step_history)

        # Build the partial state with placeholder Durations (the reported defect).
        recap_path.parent.mkdir(parents=True, exist_ok=True)
        progress_dir.mkdir(parents=True, exist_ok=True)
        recap = _recap_header("Module N session")  # placeholder total
        for m in recap_present:
            recap += _recap_section(m, _date_for(step_history, m), f"Module {m} session")
        recap_path.write_text(recap, encoding="utf-8")

        journal = validator.format_journal_header(BOOTCAMPER, START_DATE)
        for m in journal_present:
            journal += validator.format_journal_entry(
                module_number=m,
                module_name=MODULE_NAMES[m],
                date=_date_for(step_history, m),
                summary=f"Completed Module {m}",
                artifacts=[f"docs/module_{m}.md"],
                why_it_matters=f"Module {m} matters",
                takeaway="N/A",
            )
        journal_path.write_text(journal, encoding="utf-8")
        for m in cert_present:
            (progress_dir / f"MODULE_{m}_COMPLETE.md").write_text(
                f"# Module {m} Complete\n", encoding="utf-8"
            )

        # The reported state is a bug condition (coverage gaps + placeholders).
        assert _check_via_cli(
            progress_path=progress_path,
            recap_path=recap_path,
            journal_path=journal_path,
            progress_dir=progress_dir,
        ) == 1

        # Plan via the CLI mirrors the exact set differences.
        payload = _plan_via_cli(
            progress_path=progress_path,
            recap_path=recap_path,
            journal_path=journal_path,
            progress_dir=progress_dir,
            capsys=capsys,
        )
        assert payload["recap_modules"] == [7]
        assert payload["journal_modules"] == [1, 2, 4, 5]
        assert payload["certificate_modules"] == [1, 2, 3, 4, 5]
        assert _looks_like_duration(payload["total_duration"])

        # Apply the backfill. Note: placeholder Duration lines for modules 1-6
        # remain on disk; the workflow refreshes them from the plan's real values.
        plan = planner.plan_backfill(
            planner.ProgressState(completed, step_history, STARTED_AT),
            planner.ArtifactInventory(
                recap_sections=set(recap_present),
                journal_entries=set(journal_present),
                certificates=set(cert_present),
            ),
        )
        _apply_plan(
            plan,
            recap_path=recap_path,
            journal_path=journal_path,
            progress_dir=progress_dir,
            step_history=step_history,
        )

        # Complete and consistent: every module has all three artifacts.
        recap_content = recap_path.read_text(encoding="utf-8")
        journal_doc = validator.parse_journal(journal_path.read_text(encoding="utf-8"))
        assert validator.count_recap_sections(recap_content) == completed
        assert sorted(e.module_number for e in journal_doc.entries) == completed
        assert _discover_certificates(progress_dir) == set(completed)

        # Header Total Duration is a real cumulative time, not a placeholder.
        header = validator.parse_recap_header(recap_content)
        assert _looks_like_duration(header.total_duration)
        assert not _is_placeholder(header.total_duration)

        # Structural validator passes.
        assert _validate(progress_path, journal_path, recap_path) == 0

    def test_backfill_is_idempotent_on_complete_set(self, tmp_path: Path, capsys) -> None:
        """Re-running the flow on a complete, consistent set is a no-op."""
        completed = [1, 2, 3, 4, 5, 6, 7]
        recap_path = tmp_path / "docs" / "bootcamp_recap.md"
        journal_path = tmp_path / "docs" / "bootcamp_journal.md"
        progress_dir = tmp_path / "docs" / "progress"
        progress_path = tmp_path / "config" / "bootcamp_progress.json"

        step_history = _ascending_step_history(completed)
        _write_progress(progress_path, completed, step_history)

        full_plan = planner.plan_backfill(
            planner.ProgressState(completed, step_history, STARTED_AT),
            planner.ArtifactInventory(),
        )
        _write_initial_artifacts(
            recap_path=recap_path,
            journal_path=journal_path,
            progress_dir=progress_dir,
            step_history=step_history,
            present_modules=completed,
            durations=full_plan.module_durations,
            total_duration=full_plan.total_duration,
        )

        recap_before = recap_path.read_text(encoding="utf-8")
        journal_before = journal_path.read_text(encoding="utf-8")

        # No bug condition, validator passes.
        assert _check_via_cli(
            progress_path=progress_path,
            recap_path=recap_path,
            journal_path=journal_path,
            progress_dir=progress_dir,
        ) == 0
        assert _validate(progress_path, journal_path, recap_path) == 0

        # The plan is empty -> applying it changes nothing (byte-for-byte).
        payload = _plan_via_cli(
            progress_path=progress_path,
            recap_path=recap_path,
            journal_path=journal_path,
            progress_dir=progress_dir,
            capsys=capsys,
        )
        assert payload["recap_modules"] == []
        assert payload["journal_modules"] == []
        assert payload["certificate_modules"] == []

        plan = planner.plan_backfill(
            planner.ProgressState(completed, step_history, STARTED_AT),
            planner.ArtifactInventory(
                recap_sections=set(completed),
                journal_entries=set(completed),
                certificates=set(completed),
            ),
        )
        _apply_plan(
            plan,
            recap_path=recap_path,
            journal_path=journal_path,
            progress_dir=progress_dir,
            step_history=step_history,
        )
        assert recap_path.read_text(encoding="utf-8") == recap_before
        assert journal_path.read_text(encoding="utf-8") == journal_before


# ===========================================================================
# Scenario 3 — Context switching across modules then completing
# ===========================================================================


class TestContextSwitchingDurations:
    """Per-module Durations and a monotonic Total Duration, omitting when unreliable.

    Models a bootcamper switching context across modules. Each module that has
    reliable bounding timestamps gets a computed elapsed time; a module lacking a
    reliable timestamp is omitted (no placeholder). The cumulative Total Duration
    is monotonically non-decreasing as modules are added.

    Validates: Requirements 2.2, 2.3
    """

    def _seconds(self, text: str | None) -> float:
        """Parse a formatted elapsed string back into seconds (0 for None)."""
        if text is None:
            return 0.0
        units = {"d": 86_400, "h": 3_600, "m": 60, "s": 1}
        total = 0.0
        for token in text.split():
            total += int(token[:-1]) * units[token[-1]]
        return total

    def test_per_module_durations_computed_with_omission(self, tmp_path: Path) -> None:
        """Reliable modules get computed Durations; an unreliable module is omitted."""
        completed = [1, 2, 3, 4, 5, 6]
        # Module 4 has no reliable timestamp (absent from step_history).
        step_history = _ascending_step_history([1, 2, 3, 5, 6])
        progress = planner.ProgressState(completed, step_history, STARTED_AT)

        plan = planner.plan_backfill(progress, planner.ArtifactInventory())

        # Reliable modules are present with real elapsed times.
        for m in (1, 2, 3, 5, 6):
            assert m in plan.module_durations, f"Module {m} should have a Duration."
            assert _looks_like_duration(plan.module_durations[m])
            assert not _is_placeholder(plan.module_durations[m])

        # Module 4 (unreliable) is omitted rather than placeholdered.
        assert 4 not in plan.module_durations
        assert planner.compute_module_duration(step_history, STARTED_AT, 4, None) is None

        # The Total Duration is a real cumulative value.
        assert plan.total_duration is not None
        assert _looks_like_duration(plan.total_duration)

    def test_total_duration_is_monotonic_non_decreasing(self, tmp_path: Path) -> None:
        """Total Duration never decreases as more completed modules are added."""
        completed = [1, 2, 3, 4, 5, 6]
        step_history = _ascending_step_history([1, 2, 3, 5, 6])

        prev = -1.0
        for upto in range(1, len(completed) + 1):
            subset = completed[:upto]
            total = planner.compute_total_duration(step_history, STARTED_AT, subset)
            current = self._seconds(total)
            assert current >= prev, (
                f"Total Duration decreased at modules {subset}: "
                f"{current}s < {prev}s"
            )
            prev = current
        assert prev > 0, "Some reliable timing must accumulate."

    def test_omitted_duration_module_still_gets_all_artifacts(
        self, tmp_path: Path, capsys
    ) -> None:
        """A module with omitted Duration still receives recap/journal/certificate."""
        completed = [1, 2, 3, 4, 5, 6]
        step_history = _ascending_step_history([1, 2, 3, 5, 6])  # module 4 unreliable

        recap_path = tmp_path / "docs" / "bootcamp_recap.md"
        journal_path = tmp_path / "docs" / "bootcamp_journal.md"
        progress_dir = tmp_path / "docs" / "progress"
        progress_path = tmp_path / "config" / "bootcamp_progress.json"

        _write_progress(progress_path, completed, step_history)

        # Seed every module EXCEPT 4 with the full artifact set, then backfill 4.
        # Because certificates already exist for the others, the uniform-certificate
        # rule requires one for module 4 too — even though its Duration is omitted.
        present = [1, 2, 3, 5, 6]
        full_plan = planner.plan_backfill(
            planner.ProgressState(completed, step_history, STARTED_AT),
            planner.ArtifactInventory(),
        )
        _write_initial_artifacts(
            recap_path=recap_path,
            journal_path=journal_path,
            progress_dir=progress_dir,
            step_history=step_history,
            present_modules=present,
            durations=full_plan.module_durations,
            total_duration=full_plan.total_duration,
        )

        plan = planner.plan_backfill(
            planner.ProgressState(completed, step_history, STARTED_AT),
            planner.ArtifactInventory(
                recap_sections=set(present),
                journal_entries=set(present),
                certificates=set(present),
            ),
        )
        # Module 4 is the only gap across all three artifact types.
        assert plan.recap_modules == [4]
        assert plan.journal_modules == [4]
        assert plan.certificate_modules == [4]

        _apply_plan(
            plan,
            recap_path=recap_path,
            journal_path=journal_path,
            progress_dir=progress_dir,
            step_history=step_history,
        )

        recap_content = recap_path.read_text(encoding="utf-8")
        # All modules present in recap/journal/certificates.
        assert validator.count_recap_sections(recap_content) == completed
        journal_doc = validator.parse_journal(journal_path.read_text(encoding="utf-8"))
        assert sorted(e.module_number for e in journal_doc.entries) == completed
        assert _discover_certificates(progress_dir) == set(completed)

        # Module 4's section exists but omits the ### Duration field.
        section_4 = recap_content.split("## Module 4:", 1)[1].split("## Module 5:", 1)[0]
        assert "### Duration" not in section_4

        # The validator passes for the fully backfilled set.
        assert _validate(progress_path, journal_path, recap_path) == 0
