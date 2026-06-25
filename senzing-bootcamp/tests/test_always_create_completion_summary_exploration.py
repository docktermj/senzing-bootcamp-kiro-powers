"""Bug condition exploration suite for the always-create-completion-summary bugfix.

Feature: always-create-completion-summary (BUGFIX)

Property 1: Bug Condition — Completion-summary creation is gated behind the yes/no answer.

This suite encodes the *fixed* contract. It is EXPECTED TO FAIL on the unfixed
steering files: the failures are the success criterion — they surface counterexamples
proving that `completion-summary-offer.md` gates artifact creation on the bootcamper's
answer (root cause lives in the steering contract, not the script).

Bug Condition (from design):
    isBugCondition(X) = X.stoppingPointDetected AND X.offerAnswer != "yes"

Expected outcome on UNFIXED files:
    - Test 1 (decline does not gate creation, steering)        -> FAILS  (gate present)
    - Test 2 (unconditional generation step present, steering) -> FAILS  (step absent)
    - Test 3 (offer re-scoped to PDF/share, steering)          -> FAILS  (still gates file)
    - Test 4 (markdown always written, script)                 -> PASSES (root cause is steering)
    - PBT  (bug condition enumeration)                         -> PASSES (models input space)
"""

from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable (scripts aren't packages)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from generate_completion_summary import main  # noqa: E402

# ---------------------------------------------------------------------------
# Real steering file under test
# ---------------------------------------------------------------------------

_POWER_ROOT: Path = Path(__file__).resolve().parent.parent
_STEERING_FILE: Path = _POWER_ROOT / "steering" / "completion-summary-offer.md"

# The gating clause that encodes the bug: declining suppresses file creation.
_GATING_CLAUSE = "without generating any summary file"


# ---------------------------------------------------------------------------
# Bug condition model (from design)
# ---------------------------------------------------------------------------


@dataclass
class GraduationSituation:
    """A graduation/stopping-point situation characterizing the bug condition."""

    stopping_point_detected: bool
    offer_answer: str
    session_log_available: bool
    stopping_point_type: str


def is_bug_condition(situation: GraduationSituation) -> bool:
    """Return whether the bug manifests for the given situation.

    The bug manifests at any stopping point where the bootcamper does NOT accept
    the offer, because the mandated completion-summary artifact is then skipped.

    Args:
        situation: The graduation/stopping-point situation to evaluate.

    Returns:
        True when a stopping point is detected and the offer answer is not "yes".
    """
    return situation.stopping_point_detected and situation.offer_answer != "yes"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_steering() -> str:
    """Read the completion-summary-offer steering file contents."""
    return _STEERING_FILE.read_text(encoding="utf-8")


def _extract_section(content: str, heading: str) -> str:
    """Extract the text of a `## heading` section up to the next `## ` heading.

    Args:
        content: Full markdown content.
        heading: The exact heading text (without the leading `## `).

    Returns:
        The section body text, or an empty string if the heading is absent.
    """
    marker = f"## {heading}"
    start = content.find(marker)
    if start == -1:
        return ""
    rest = content[start + len(marker):]
    next_idx = rest.find("\n## ")
    if next_idx == -1:
        return rest
    return rest[:next_idx]


def _write_valid_session_log(log_path: Path) -> None:
    """Write a small, valid multi-module session log to the given path."""
    entries = [
        {
            "event_type": "question",
            "module": 1,
            "timestamp": "2025-01-10T09:00:00Z",
            "data": {"text": "What problem are we solving?", "question_id": "q001"},
        },
        {
            "event_type": "answer",
            "module": 1,
            "timestamp": "2025-01-10T09:05:00Z",
            "data": {"text": "Deduplicate customer records.", "question_id": "q001"},
        },
        {
            "event_type": "action",
            "module": 2,
            "timestamp": "2025-01-11T10:00:00Z",
            "data": {
                "action_type": "file_create",
                "description": "Created SDK setup script",
                "file_path": "scripts/setup_sdk.py",
            },
        },
        {
            "event_type": "artifact",
            "module": 2,
            "timestamp": "2025-01-11T10:30:00Z",
            "data": {
                "file_path": "scripts/setup_sdk.py",
                "artifact_type": "script",
                "description": "SDK initialization script",
            },
        },
    ]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, separators=(",", ":")) + "\n")


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


@st.composite
def st_offer_answer(draw) -> str:
    """Draw a non-"yes" offer answer ("no" and other non-acceptance strings).

    Enumerates the bug-condition input space: `offerAnswer != "yes"`.
    """
    answer = draw(
        st.one_of(
            st.sampled_from(["no", "n", "decline", "not now", "later", "skip", ""]),
            st.text(max_size=20),
        )
    )
    assume(answer != "yes")
    return answer


def st_stopping_point_type() -> st.SearchStrategy[str]:
    """Draw a detected stopping-point type."""
    return st.sampled_from(
        [
            "module_7_completion",
            "module_11_completion",
            "explicit_stop",
            "track_switch",
        ]
    )


# ---------------------------------------------------------------------------
# Steering-content assertions (Tests 1-3) — FAIL on unfixed files
# ---------------------------------------------------------------------------


class TestSteeringContractGate:
    """The steering contract must not gate completion-summary creation on the answer.

    These assertions encode the FIXED contract and are EXPECTED TO FAIL on the
    unfixed steering files — proving the creation gate exists.

    Validates: Requirements 1.1, 1.2, 1.3, 1.4
    """

    def test_decline_does_not_gate_creation(self) -> None:
        """Test 1: the gating clause that suppresses file creation must be absent."""
        content = _read_steering()
        assert _GATING_CLAUSE not in content, (
            "Steering file still contains the creation-gating clause "
            f"{_GATING_CLAUSE!r}; declining the offer suppresses file creation "
            "(bug present)."
        )

    def test_unconditional_generation_step_present(self) -> None:
        """Test 2: an unconditional markdown-generation step must exist.

        The file must contain an "always generate" step that runs
        generate_completion_summary.py (markdown, no --pdf) before/independent of
        the yes/no answer.
        """
        content = _read_steering()
        heading = "Always Generate the Summary Document"
        assert f"## {heading}" in content, (
            "Steering file is missing an unconditional "
            f"'## {heading}' generation step; the summary is only generated on "
            "an accepted offer (bug present)."
        )
        section = _extract_section(content, heading)
        assert "generate_completion_summary.py" in section, (
            "The unconditional generation step must reference running "
            "generate_completion_summary.py."
        )
        # The unconditional step generates markdown only (no --pdf gating).
        assert "--pdf" not in section, (
            "The unconditional generation step must run the markdown generator "
            "without --pdf (the PDF is gated by the yes/no answer elsewhere)."
        )

    def test_offer_rescoped_to_pdf_share(self) -> None:
        """Test 3: the Prompt Format must scope yes/no to PDF/share, not file creation.

        "yes" -> render the shareable PDF (--pdf) / surface it.
        "no"  -> skip ONLY the PDF render and surfacing (the markdown stays created).
        """
        content = _read_steering()
        section = _extract_section(content, "Prompt Format")
        assert section, "Steering file is missing a '## Prompt Format' section."
        # "yes" must be tied to rendering the shareable PDF via --pdf.
        assert "--pdf" in section, (
            "The Prompt Format section must tie 'yes' to rendering the shareable "
            "PDF via --pdf; it currently gates summary-file creation on the answer "
            "(bug present)."
        )
        # The decline branch must not suppress the summary file itself.
        assert _GATING_CLAUSE not in section, (
            "The Prompt Format decline branch still suppresses file creation "
            f"({_GATING_CLAUSE!r}); it must skip only PDF rendering/sharing "
            "(bug present)."
        )


# ---------------------------------------------------------------------------
# Script-behavior assertion (Test 4) — PASSES on unfixed code
# ---------------------------------------------------------------------------


class TestScriptWritesMarkdownUnconditionally:
    """generate_completion_summary.py writes markdown without --pdf.

    This PASSES on the unfixed script, confirming the root cause is the steering
    contract (not the script): main() already writes docs/completion_summary.md
    unconditionally and gates only the PDF behind --pdf.

    Validates: Requirements 1.3, 1.4
    """

    def test_markdown_always_written_without_pdf_flag(self) -> None:
        """Test 4: main([...]) with no --pdf creates the markdown summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            log_path = tmp / "config" / "session_log.jsonl"
            progress_path = tmp / "config" / "bootcamp_progress.json"
            prefs_path = tmp / "config" / "bootcamp_preferences.yaml"
            output_path = tmp / "docs" / "completion_summary.md"

            _write_valid_session_log(log_path)
            progress_path.parent.mkdir(parents=True, exist_ok=True)
            progress_path.write_text(
                json.dumps(
                    {
                        "current_module": 2,
                        "modules_completed": [1, 2],
                        "track": "core_bootcamp",
                    }
                ),
                encoding="utf-8",
            )
            prefs_path.write_text(
                "name: Test Bootcamper\ntrack: core_bootcamp\n",
                encoding="utf-8",
            )

            exit_code = main(
                [
                    "--log",
                    str(log_path),
                    "--output",
                    str(output_path),
                    "--progress",
                    str(progress_path),
                    "--preferences",
                    str(prefs_path),
                ]
            )

            assert exit_code == 0, "main() should succeed for a valid session log"
            assert output_path.exists(), (
                "docs/completion_summary.md must be created with no --pdf flag; "
                "the script writes markdown unconditionally (root cause is the "
                "steering contract, not the script)."
            )
            rendered = output_path.read_text(encoding="utf-8")
            assert "## Module 1:" in rendered
            assert "## Module 2:" in rendered


# ---------------------------------------------------------------------------
# PBT — Bug condition enumeration — PASSES (models the bug input space)
# ---------------------------------------------------------------------------


class TestBugConditionEnumeration:
    """Enumerate the bug-condition input space (`offerAnswer != "yes"`).

    For every non-"yes" answer at a detected stopping point, isBugCondition holds —
    modeling the situations where the unfixed workflow skips the mandated artifact.

    Validates: Requirements 1.1, 1.2
    """

    @given(answer=st_offer_answer(), stopping_point=st_stopping_point_type())
    @settings(max_examples=20)
    def test_bug_condition_holds_for_non_yes_answers(
        self, answer: str, stopping_point: str
    ) -> None:
        """Any detected stopping point with offerAnswer != 'yes' is a bug condition."""
        situation = GraduationSituation(
            stopping_point_detected=True,
            offer_answer=answer,
            session_log_available=True,
            stopping_point_type=stopping_point,
        )
        assert is_bug_condition(situation), (
            f"Expected bug condition for offer_answer={answer!r} at "
            f"stopping point {stopping_point!r}"
        )

    @given(stopping_point=st_stopping_point_type())
    @settings(max_examples=20)
    def test_accepted_offer_is_not_bug_condition(self, stopping_point: str) -> None:
        """An accepted ('yes') offer at a stopping point is NOT a bug condition."""
        situation = GraduationSituation(
            stopping_point_detected=True,
            offer_answer="yes",
            session_log_available=True,
            stopping_point_type=stopping_point,
        )
        assert not is_bug_condition(situation), (
            "Accepting the offer must not be a bug condition (summary is created)."
        )
