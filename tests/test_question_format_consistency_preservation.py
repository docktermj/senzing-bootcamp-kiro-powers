"""Preservation property tests for the question-format-consistency bugfix.

These tests encode design **Property 2 (Preservation)** — "Non-Target Steering
Files and Paths Unchanged":

    FOR ALL input WHERE NOT isBugCondition(input):
        fixedSteering(input) == originalSteering(input)

The fix (tasks 3.1-3.4) touches guidance at exactly two paths, living in four
target steering files:

    - session-resume-phase2-state-repair.md  (relocated pending-question re-rendering)
    - module-completion-track.md      (bootcamp-completion closing question)
    - agent-behavior-rules.md         (Rule 4 two new clauses)
    - graduation.md                   (Mandatory Closing Step terminal question)

    (session-resume.md itself is UNCHANGED: its Step 3 edit was reverted and the
    re-rendering guidance relocated to the phase-2 state-repair companion, so it
    is now a snapshot-protected non-target file.)

Everything else must be completely unaffected. Following the observation-first
methodology, these tests capture the CURRENT (unfixed) baseline and assert
invariants that hold now AND must still hold after the fix — so they PASS on
unfixed code and meaningfully guard against regressions post-fix.

Chosen preservation approach (two complementary mechanisms)
-----------------------------------------------------------
1. **Byte-identical snapshot of every non-target steering file.** A committed
   SHA-256 baseline (``question_format_consistency_preservation_baseline.json``)
   is captured from the current pre-fix files. Because the fix edits only the
   four target files, all 110 non-target ``*.md`` files must remain byte-for-byte
   identical: their SHA-256 must equal the frozen baseline both before and after
   the fix. This is the strongest possible regression guard for non-target files.

   A whole-file hash cannot be used for the four target files (their bytes WILL
   change), so those are guarded by mechanism 2 instead. The steering-index YAML
   is excluded because the fix may legitimately re-budget the target files there.

2. **Structural content anchors inside the target files.** For each of the four
   target files, the specific non-target sections/content that the fix must NOT
   disturb are asserted present verbatim (existing rules, existing steps,
   existing celebration offers, existing graduation steps, and the existing
   in-session welcome-back question). These anchors hold today and must survive
   the additive fix.

Plus a structural assertion (task item 3) that the ``config/.question_pending``
lifecycle rules — ``write-policy-gate`` validation, the Treat-as-answer rule,
and the Delete-and-process rule — remain referenced in the steering files.

Rationale for the snapshot mechanism: a committed, frozen SHA-256 baseline (in
the spirit of ``write_gate_momentum_baseline.py``) is captured once on unfixed
code and read read-only by the tests, so the post-fix run performs a real
comparison against the pre-fix bytes rather than a self-fulfilling recompute. If
the baseline file is ever missing it is bootstrapped from the current files (and
must then be committed), so the suite is self-contained.

Feature: question-format-consistency (bugfix)

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from hypothesis import assume, given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT: Path = Path(__file__).resolve().parent.parent
STEERING_DIR: Path = _REPO_ROOT / "senzing-bootcamp" / "steering"
BASELINE_PATH: Path = (
    Path(__file__).resolve().parent
    / "question_format_consistency_preservation_baseline.json"
)

# The four steering files the fix ultimately changes. Their bytes DIFFER from
# the pre-fix corpus, so they are EXCLUDED from the byte-identical snapshot and
# guarded by structural content anchors instead. NOTE: as remediated, the
# session-resume.md Step 3 edit was reverted and its pending-question
# re-rendering guidance was relocated into the phase-2 companion
# ``session-resume-phase2-state-repair.md`` (out of Step 3's single-👉 closing
# zone). So session-resume.md is now UNCHANGED (a non-target, snapshot-protected
# below) and the state-repair file takes its place in the target set.
TARGET_FILES: frozenset[str] = frozenset(
    {
        "session-resume-phase2-state-repair.md",
        "module-completion-track.md",
        "agent-behavior-rules.md",
        "graduation.md",
    }
)

# The two non-target steering files that carry the `.question_pending` lifecycle
# rules the fix must leave referenced and unchanged (they are also snapshot-
# protected as non-target files; asserted explicitly per task item 3).
CONVERSATION_PROTOCOL: str = "conversation-protocol.md"
AGENT_INSTRUCTIONS: str = "agent-instructions.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_bytes(name: str) -> bytes:
    """Return the raw bytes of a steering file.

    Args:
        name: The steering file name (e.g. ``session-resume.md``).

    Returns:
        The file's bytes.
    """
    return (STEERING_DIR / name).read_bytes()


def _read_text(name: str) -> str:
    """Return the UTF-8 text of a steering file.

    Args:
        name: The steering file name (e.g. ``graduation.md``).

    Returns:
        The file's decoded text.
    """
    return (STEERING_DIR / name).read_text(encoding="utf-8")


def _sha256(name: str) -> str:
    """Return the SHA-256 hex digest of a steering file's bytes.

    Args:
        name: The steering file name.

    Returns:
        The lowercase hex SHA-256 digest of the file's bytes.
    """
    return hashlib.sha256(_read_bytes(name)).hexdigest()


def all_md_files() -> list[str]:
    """Return every top-level ``*.md`` steering file name, sorted.

    Returns:
        Sorted list of Markdown steering file names in ``STEERING_DIR``.
    """
    return sorted(p.name for p in STEERING_DIR.glob("*.md"))


def non_target_md_files() -> list[str]:
    """Return every non-target ``*.md`` steering file name, sorted.

    Returns:
        Sorted list of Markdown steering file names excluding ``TARGET_FILES``.
    """
    return [name for name in all_md_files() if name not in TARGET_FILES]


def _compute_snapshot() -> dict[str, str]:
    """Compute the SHA-256 snapshot of every current non-target steering file.

    Returns:
        Mapping of non-target file name to its SHA-256 hex digest.
    """
    return {name: _sha256(name) for name in non_target_md_files()}


def _regenerate_baseline() -> dict[str, str]:
    """Write the committed baseline from the current non-target files.

    The baseline is a frozen pre-fix reference. It is written once (on unfixed
    code) and must be committed; the tests then read it read-only.

    Returns:
        The freshly written ``name -> sha256`` snapshot mapping.
    """
    snapshot = _compute_snapshot()
    payload = {
        "description": (
            "Frozen SHA-256 baseline of every non-target steering file for the "
            "question-format-consistency bugfix. Captured on pre-fix code; the "
            "fix edits only the four target files, so every file listed here "
            "must remain byte-identical."
        ),
        "algorithm": "sha256",
        "target_files_excluded": sorted(TARGET_FILES),
        "files": snapshot,
    }
    BASELINE_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return snapshot


def load_baseline() -> dict[str, str]:
    """Load the committed non-target snapshot, bootstrapping it if absent.

    On a normal run the frozen baseline exists and is returned as-is (a real
    comparison against pre-fix bytes). If the file is missing it is bootstrapped
    from the current files and must then be committed.

    Returns:
        Mapping of non-target file name to its baseline SHA-256 hex digest.
    """
    if not BASELINE_PATH.exists():
        return _regenerate_baseline()
    payload = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    return dict(payload["files"])


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


def st_non_target_md_file() -> st.SearchStrategy[str]:
    """Generate a real non-target steering file name.

    Returns:
        A Hypothesis strategy sampling from the non-target ``*.md`` file set.
    """
    return st.sampled_from(non_target_md_files())


def st_any_md_file() -> st.SearchStrategy[str]:
    """Generate any real steering ``*.md`` file name (target or non-target).

    Returns:
        A Hypothesis strategy sampling from every steering ``*.md`` file.
    """
    return st.sampled_from(all_md_files())


# ---------------------------------------------------------------------------
# Property 2 — non-target files are byte-identical to the frozen baseline
# ---------------------------------------------------------------------------


class TestNonTargetFilesByteIdentical:
    """Every non-target steering file is byte-identical to the pre-fix baseline.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

    Observation-first: the SHA-256 of each non-target ``*.md`` file is captured
    now (unfixed) into a frozen committed baseline. Because the fix edits only
    the four target files, these hashes must stay identical — the tests PASS on
    unfixed code and fail if the fix disturbs any non-target file.
    """

    def test_baseline_covers_exactly_the_current_non_target_set(self) -> None:
        """The frozen baseline lists exactly today's non-target ``*.md`` files.

        Guards against the fix adding, removing, or renaming a steering file
        outside the four intended targets.
        """
        assert set(load_baseline()) == set(non_target_md_files()), (
            "The non-target steering file set drifted from the frozen baseline. "
            "The fix must only edit the four target files; it must not add, "
            "remove, or rename any other steering file."
        )

    @given(name=st_non_target_md_file())
    def test_sampled_non_target_file_matches_baseline(self, name: str) -> None:
        """For any sampled non-target file, its SHA-256 equals the baseline.

        **Validates: Requirements 3.1, 3.4**
        """
        baseline = load_baseline()
        assert _sha256(name) == baseline[name], (
            f"Non-target steering file {name!r} changed relative to the frozen "
            "pre-fix baseline — the fix must leave it byte-identical."
        )

    @given(name=st_any_md_file())
    def test_only_target_files_may_differ(self, name: str) -> None:
        """No formatting change appears outside the two target paths.

        For any steering ``*.md`` file, if it is not one of the four target
        files it must be byte-identical to the frozen baseline. This encodes
        "no changes outside the two target paths (session-recreation
        re-presentation and graduation/track-completion closing)".

        **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**
        """
        assume(name not in TARGET_FILES)
        baseline = load_baseline()
        assert _sha256(name) == baseline[name], (
            f"Steering file {name!r} is outside the target set but changed "
            "relative to the frozen baseline — the fix introduced a formatting "
            "change outside the two intended target paths."
        )

    def test_every_non_target_file_matches_baseline(self) -> None:
        """Deterministic full-coverage check across all non-target files.

        Complements the sampled property tests by verifying every one of the
        non-target files (not just a Hypothesis sample) is unchanged.
        """
        baseline = load_baseline()
        changed = [name for name in non_target_md_files() if _sha256(name) != baseline[name]]
        assert not changed, (
            "These non-target steering files changed relative to the frozen "
            f"pre-fix baseline (they must remain byte-identical): {changed}"
        )


# ---------------------------------------------------------------------------
# Property 2 — target files: non-target content anchors preserved
# ---------------------------------------------------------------------------


class TestTargetFileNonTargetSectionsPreserved:
    """The fix's four target files keep all their non-target content intact.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.7**

    A whole-file hash cannot guard the target files (their bytes change), so the
    specific sections/content the additive fix must not disturb are asserted
    present verbatim. These anchors hold on unfixed code and must survive.
    """

    def test_target_file_set_is_exactly_the_four_documented_targets(self) -> None:
        """The target set matches the four files named in the design.

        Guards the definition the whole test file depends on.
        """
        assert TARGET_FILES == {
            "session-resume-phase2-state-repair.md",
            "module-completion-track.md",
            "agent-behavior-rules.md",
            "graduation.md",
        }
        for name in TARGET_FILES:
            assert (STEERING_DIR / name).exists(), f"missing target file {name!r}"

    def test_state_repair_non_target_sections_preserved(self) -> None:
        """state-repair.md keeps its pre-fix sections; only the re-render section is added.

        The relocated "Pending Question Re-Rendering" guidance is ADDED to
        ``session-resume-phase2-state-repair.md``; the file's existing state-repair
        content (guard condition, progress reconstruction, stale-state handling,
        and the Step 3 handoff) must survive the additive edit unchanged.

        **Validates: Requirements 3.2**
        """
        content = _read_text("session-resume-phase2-state-repair.md")
        for anchor in (
            "# State Repair: Stale or Corrupted Progress",
            "## Guard Condition",
            "## Progress Reconstruction from Artifacts",
            "## Handling Stale or Corrupted State",
            "### Discrepancy Examples",
            "After corrections are applied, return to the Phase-1 flow at Step 3 "
            "(Summarize and Confirm) with the corrected state.",
        ):
            assert anchor in content, (
                f"session-resume-phase2-state-repair.md lost preserved non-target "
                f"content: {anchor!r}"
            )
        # The relocated re-rendering guidance is the ONLY intended addition to
        # this file; confirm it landed here (Path A now lives in this phase-2 file).
        assert "## Pending Question Re-Rendering" in content
        assert ".question_pending" in content
        assert "👉 **{stored question text}**" in content

    def test_session_resume_unchanged_and_still_correctly_formatted(self) -> None:
        """session-resume.md is now UNCHANGED and keeps its correct in-session question.

        Its Step 3 edit was reverted (the re-rendering guidance was relocated to
        the phase-2 state-repair companion), so session-resume.md is a non-target
        file (byte-snapshot-protected above). This asserts the existing correctly
        formatted in-session welcome-back question and the `.question_pending`
        write instruction remain intact (Req 3.1, 3.2, 3.5), and that the reverted
        Step 3 carries no relocated re-rendering subsection.

        **Validates: Requirements 3.1, 3.2, 3.5**
        """
        content = _read_text("session-resume.md")
        for anchor in (
            "# Session Resume Workflow",
            "## Step 3: Summarize and Confirm",
            # The existing in-session welcome-back question (Req 3.1) — already
            # correctly 👉 + bold — must remain unchanged.
            "🎓 Welcome back to the Senzing Bootcamp!",
            "👉 **Ready to continue with Module [N], or would you like to do something else?**",
            # The existing `.question_pending` write instruction (Req 3.2/3.5).
            "Write `config/.question_pending` with the question text above.",
        ):
            assert anchor in content, (
                f"session-resume.md lost preserved content: {anchor!r}"
            )
        # The relocated subsection must NOT be inline in session-resume.md Step 3
        # (that is what broke the single-👉 Step 3 closing invariant before the
        # remediation relocated it to the phase-2 state-repair companion).
        assert "## Pending Question Re-Rendering" not in content
        assert "### Pending Question Re-Rendering" not in content

    def test_agent_behavior_rules_existing_clauses_preserved(self) -> None:
        """agent-behavior-rules.md Rule 4 existing clauses and Rules 1-3 survive.

        **Validates: Requirements 3.3**
        """
        content = _read_text("agent-behavior-rules.md")
        for anchor in (
            "## Rule 1: Honor Explicit Continuation Requests",
            "## Rule 2: Acknowledge Bootcamper Responses Before Proceeding",
            "## Rule 3: Eliminate Ambiguous Yes/No Questions",
            "## Rule 4: Consistent Pointer Indicator",
            "Prefix every input-requiring prompt with 👉 at the start of the line.",
            "**Leading-question guarantee.**",
            "A `write-policy-gate` intercept/retry cycle does not relieve you of this obligation.",
        ):
            assert anchor in content, (
                f"agent-behavior-rules.md lost preserved existing content: {anchor!r}"
            )

    def test_module_completion_track_celebration_offers_preserved(self) -> None:
        """module-completion-track.md celebration offers/sections survive.

        **Validates: Requirements 3.7**
        """
        content = _read_text("module-completion-track.md")
        for anchor in (
            "## Path Completion Detection",
            "## Path Completion Celebration",
            "Would you like to export a shareable report of your bootcamp results?",
            "Graduation offer (after the certificate generation, before the feedback reminder):",
            "Feedback Submission Reminder (after the graduation offer sequence, "
            "before the retrospective):",
            "Load `lessons-learned.md` and offer the retrospective.",
        ):
            assert anchor in content, (
                f"module-completion-track.md lost preserved celebration content: {anchor!r}"
            )

    def test_graduation_non_closing_sections_preserved(self) -> None:
        """graduation.md sections other than the Mandatory Closing Step survive.

        **Validates: Requirements 3.7**
        """
        content = _read_text("graduation.md")
        for anchor in (
            "# Graduation Workflow",
            "## Step 1: Production Project Structure",
            "## Step 5: Git Repository Initialization (Optional)",
            "## Graduation Report",
            "## Mandatory Closing Step: Guaranteed Recap & Post-Graduation Announcement",
            "python scripts/ensure_graduation_artifacts.py",
            # The recap announcement example was reworded by the guaranteed-recap-pdf
            # notification work to emphasize the PDF's keepsake value; the closing
            # announcement itself is preserved.
            "🏆 **Here's your bootcamp trophy.**",
        ):
            assert anchor in content, (
                f"graduation.md lost preserved non-closing content: {anchor!r}"
            )


# ---------------------------------------------------------------------------
# Structural assertion — .question_pending lifecycle rules remain referenced
# ---------------------------------------------------------------------------


class TestQuestionPendingLifecyclePreserved:
    """The ``config/.question_pending`` lifecycle rules stay referenced (task item 3).

    **Validates: Requirements 3.5, 3.6**

    The write-policy-gate validation, the Treat-as-answer rule, and the
    Delete-and-process rule govern how a pending question is written, treated,
    and deleted. The fix re-renders a pending question's *presentation* but must
    not alter this lifecycle. These rules live in non-target files (also
    snapshot-protected); asserted explicitly here for clarity.
    """

    def test_treat_as_answer_rule_referenced(self) -> None:
        """conversation-protocol.md still defines the Treat-as-answer rule."""
        content = _read_text(CONVERSATION_PROTOCOL)
        assert "**Treat-as-answer rule:**" in content, (
            "conversation-protocol.md must keep the Treat-as-answer rule."
        )
        assert "`config/.question_pending`" in content

    def test_delete_and_process_rule_referenced(self) -> None:
        """agent-instructions.md still defines the Delete-and-process rule."""
        content = _read_text(AGENT_INSTRUCTIONS)
        assert "**Delete-and-process rule:**" in content, (
            "agent-instructions.md must keep the Delete-and-process rule."
        )

    def test_write_policy_gate_validation_referenced(self) -> None:
        """conversation-protocol.md still routes writes through write-policy-gate."""
        content = _read_text(CONVERSATION_PROTOCOL)
        assert (
            "The `write-policy-gate` hook validates every question written to "
            "`config/.question_pending`" in content
        ), "conversation-protocol.md must keep the write-policy-gate validation rule."

    def test_structured_write_and_delete_lifecycle_referenced(self) -> None:
        """The write-then-delete structured lifecycle stays documented."""
        content = _read_text(CONVERSATION_PROTOCOL)
        assert (
            "Write the file `config/.question_pending` using the structured format:"
            in content
        ), "conversation-protocol.md must keep the structured write format."
        assert "Delete `config/.question_pending` before doing anything else" in content, (
            "conversation-protocol.md must keep the delete-before-processing rule."
        )


# ---------------------------------------------------------------------------
# Baseline (re)generation entry point — captures the frozen pre-fix reference.
# ---------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    snapshot = _regenerate_baseline()
    print(f"Wrote baseline for {len(snapshot)} non-target steering files -> {BASELINE_PATH}")
