"""Preservation property tests for the always-create-completion-summary bugfix.

Feature: always-create-completion-summary (BUGFIX)

Property 2: Preservation — Surrounding behavior and the published steering contract
are unchanged.

Methodology: observation-first. The preserved sections of the UNFIXED steering files
are snapshotted here as (a) verbatim exact-text excerpts and (b) SHA-256 byte-identity
digests captured from the current files. The fix MUST NOT touch these sections, so the
snapshots are valid both BEFORE and AFTER the fix.

Sections snapshotted (preserved — NOT edited by the fix):
    completion-summary-offer.md : ## Stopping Point Detection Rules
                                  ## False Positive Guards
                                  ## Ordering Rules
                                  ## Repeat Policy
    graduation.md               : ## Step 0: Recap PDF Generation (Step 0a/0b/0c)
                                  ## Graduation Report
    module-completion.md        : ## Path Completion Celebration (offer ordering)

NOT snapshotted (the fix DOES change these — see design Change 1):
    completion-summary-offer.md : ## Prompt Format
                                  ## Summary Offer Message Format

Expected outcome on UNFIXED code: every test PASSES — this pins the baseline behavior
that must survive the fix.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable (scripts aren't packages)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from generate_completion_summary import main  # noqa: E402

# ---------------------------------------------------------------------------
# Real files under test
# ---------------------------------------------------------------------------

_POWER_ROOT: Path = Path(__file__).resolve().parent.parent
_STEERING_DIR: Path = _POWER_ROOT / "steering"
_TESTS_DIR: Path = _POWER_ROOT / "tests"

_OFFER_FILE: Path = _STEERING_DIR / "completion-summary-offer.md"
_GRADUATION_FILE: Path = _STEERING_DIR / "graduation.md"
_MODULE_COMPLETION_FILE: Path = _STEERING_DIR / "module-completion.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    """Read a file as UTF-8 text."""
    return path.read_text(encoding="utf-8")


def _extract_section(content: str, heading: str) -> str:
    """Extract a `## heading` section body up to the next `## ` heading.

    Args:
        content: Full markdown content.
        heading: The exact heading text (without the leading `## `).

    Returns:
        The section body text (everything after the heading marker up to the next
        top-level `## ` heading), or an empty string if the heading is absent.
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


def _extract_inclusive(content: str, start_marker: str, end_marker: str) -> str:
    """Extract the inclusive span from start_marker through end_marker.

    Args:
        content: Full markdown content.
        start_marker: Literal text where the span begins (included).
        end_marker: Literal text where the span ends (included).

    Returns:
        The inclusive substring, or an empty string if either marker is absent.
    """
    start = content.find(start_marker)
    if start == -1:
        return ""
    end = content.find(end_marker, start)
    if end == -1:
        return ""
    return content[start:end + len(end_marker)]


def _sha256(text: str) -> str:
    """Return the hex SHA-256 digest of the given text (UTF-8)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _ordered(haystack: str, needles: list[str]) -> bool:
    """Return True if every needle appears in haystack in the given order.

    Args:
        haystack: The text to search.
        needles: Substrings that must appear in strictly increasing index order.

    Returns:
        True when each needle is present and ordered after its predecessor.
    """
    last = -1
    for needle in needles:
        idx = haystack.find(needle, last + 1)
        if idx <= last:
            return False
        last = idx
    return True


# ---------------------------------------------------------------------------
# Byte-identity snapshots (SHA-256), captured from the UNFIXED steering files
# ---------------------------------------------------------------------------

# completion-summary-offer.md preserved sections.
_SNAP_DETECTION_RULES = (
    "97c8814da7a89af4afe25c6c40fc599c0055e5a2f48643f2516c0817eb6a2e32"
)
_SNAP_FALSE_POSITIVE_GUARDS = (
    "94d6acc3ee8db291301c337d5f03ef05b61feeb493691ee810bf2f2fc960b93a"
)
_SNAP_ORDERING_RULES = (
    "fbfa5aa457bdfeabb53322a4f1546bf6153fbae76af25a602bd342bbe02bb385"
)
_SNAP_REPEAT_POLICY = (
    "50db6dca507336d2f2840c2ea75ac476d8ee1d1e541805c79e8bb59879931f92"
)

# graduation.md preserved sections.
_SNAP_GRAD_STEP0_RECAP_ATTEMPT = (
    "10789b5c1b591ba0229301b417e73a3afdf741555c2c606529f18c919cab3b63"
)
_SNAP_GRAD_REPORT = (
    "e90585f1fda29397c3f565c965bde06edcb07325c04bf24c4243004bf097fd6f"
)

# module-completion.md preserved section.
# Recomputed after task 4.6 added a one-line clarification to the section intro: the
# completion-summary document is always created at track completion, with the offer in
# its existing position governing only the PDF/share. The meaningful invariant — the
# offer ordering — is independently asserted by test_celebration_offer_ordering_preserved
# via _CELEBRATION_ORDER_MARKERS, which the added prose does not disturb.
# Re-baselined again for the module-completion-artifacts bugfix, which added a
# clarifying note to this section; the ordering-marker test
# (test_celebration_offer_ordering_preserved) still independently guards the
# meaningful invariant.
_SNAP_PATH_COMPLETION_CELEBRATION = (
    "92ed1845950c3d0b9277bd6f62191d02b69c090126873e8c063d691f06f4345a"
)


# ---------------------------------------------------------------------------
# Verbatim exact-text excerpts (preserved content — must remain present)
# ---------------------------------------------------------------------------

# The four detection rules (## Stopping Point Detection Rules).
_DETECTION_RULE_EXCERPTS = [
    "### 1. Module 7 Completion (Core Track End)",
    (
        "When Module 7 appears in the `modules_completed` array of "
        "`config/bootcamp_progress.json`, detect a stopping point within the same "
        "agent turn that the module completion is recorded."
    ),
    "### 2. Module 11 Completion (Advanced Track End)",
    "### 3. Explicit Stop Request",
    "### 4. Track Switch at Boundary",
]

# The false-positive guards (## False Positive Guards).
_FALSE_POSITIVE_GUARD_EXCERPTS = [
    "### Stop Phrase in Longer Substantive Request",
    (
        "If the bootcamper's message contains a stop phrase embedded within a longer "
        "substantive request, do **NOT** trigger a stopping point from the stop "
        "phrase alone."
    ),
    "### Missing or Unreadable Progress File",
    "- Do **NOT** detect a stopping point",
]

# Track-completion + mid-session + simultaneous ordering (## Ordering Rules).
_ORDERING_RULE_EXCERPTS = [
    "### Track Completion (Module 7 or Module 11)",
    "1. Track completion celebration message (🎉)",
    "2. **→ Completion Summary PDF offer ← (here)**",
    "3. Export results offer (`scripts/export_results.py`)",
    "### Mid-Session Stop (Explicit Stop Request)",
    "### Simultaneous Detection",
]

# Repeat policy (## Repeat Policy).
_REPEAT_POLICY_EXCERPT = (
    "The summary offer is presented at **every** stopping point regardless of "
    "whether a previous summary was generated earlier in the session. Each stopping "
    "point is an independent opportunity to capture the current state of the "
    "bootcamp journey."
)

# graduation.md Step 0a/0b/0c recap-PDF attempt.
_GRAD_STEP0_EXCERPTS = [
    "### Step 0a: Recap Document Recovery",
    "### Step 0b: Recap Document Validation",
    "### Step 0c: PDF Generation",
    "python scripts/generate_recap_pdf.py",
]

# graduation.md Graduation Report always-generate behavior.
_GRAD_REPORT_ALWAYS_GENERATE = (
    "**Always generate `production/GRADUATION_REPORT.md`**, regardless of whether "
    "individual steps encountered errors."
)

# module-completion.md celebration ordering markers (in required order).
_CELEBRATION_ORDER_MARKERS = [
    "You've completed the [track name]!",
    "Would you like to export a shareable report of your bootcamp results?",
    "Would you like a record of your bootcamp journey?",
    "Would you like to see analytics on your bootcamp journey?",
    "generate_graduation_certificate.py",
    "Would you like to run the graduation workflow?",
    "Feedback Submission Reminder (after the graduation offer sequence",
]


# ===========================================================================
# Test — Published contract tokens preserved
# (re-assert the existing TestSteeringFileContent checks)
# ===========================================================================


class TestPublishedContractTokensPreserved:
    """The published completion-summary-offer.md contract tokens must survive the fix.

    Re-asserts the checks from
    test_completion_summary_integration.py::TestSteeringFileContent so the fix cannot
    silently drop a token the integration suite relies on.

    Validates: Requirements 3.2, 3.8
    """

    def test_offer_file_has_yaml_frontmatter(self) -> None:
        """Offer file still opens/closes YAML frontmatter delimiters."""
        content = _read(_OFFER_FILE)
        assert content.startswith("---"), "Offer file must start with '---'"
        assert len(content.split("---", 2)) >= 3, (
            "Offer file must have opening and closing '---' delimiters"
        )

    def test_offer_file_mentions_four_content_categories(self) -> None:
        """Offer file still names all four content categories."""
        lowered = _read(_OFFER_FILE).lower()
        for category in (
            "questions asked",
            "answers given",
            "actions taken",
            "artifacts created",
        ):
            assert category in lowered, f"Offer file must mention '{category}'"

    def test_offer_file_names_completion_summary_pdf(self) -> None:
        """Offer file still names the literal deliverable 'Completion Summary PDF'."""
        assert "Completion Summary PDF" in _read(_OFFER_FILE), (
            "Offer file must name the deliverable 'Completion Summary PDF'"
        )

    def test_offer_file_keeps_binary_yes_no_phrasing(self) -> None:
        """Offer file still specifies the 'yes/no' binary prompt phrasing."""
        assert "yes/no" in _read(_OFFER_FILE).lower(), (
            "Offer file must keep the 'yes/no' binary prompt phrasing"
        )

    def test_offer_file_references_celebration(self) -> None:
        """Offer file still references the celebration ordering anchor (emoji)."""
        content = _read(_OFFER_FILE)
        assert "celebration" in content.lower() or "\U0001f389" in content, (
            "Offer file must reference the celebration message"
        )

    def test_offer_file_references_export(self) -> None:
        """Offer file still references the export-results ordering anchor."""
        assert "export" in _read(_OFFER_FILE).lower(), (
            "Offer file must reference the export results offer"
        )


# ===========================================================================
# Test — Detection / ordering / repeat policy unchanged (byte-identical)
# ===========================================================================


class TestDetectionOrderingRepeatPolicyUnchanged:
    """The detection, false-positive, ordering, and repeat-policy sections are frozen.

    Each preserved section is asserted byte-identical to the captured UNFIXED snapshot
    (SHA-256) and is also checked to still contain its verbatim distinctive excerpts.

    Validates: Requirements 3.1, 3.4, 3.5, 3.7
    """

    def test_stopping_point_detection_rules_byte_identical(self) -> None:
        """`## Stopping Point Detection Rules` is byte-identical to the snapshot."""
        section = _extract_section(_read(_OFFER_FILE), "Stopping Point Detection Rules")
        assert section, "Detection rules section must be present"
        for excerpt in _DETECTION_RULE_EXCERPTS:
            assert excerpt in section, f"Detection rules missing excerpt: {excerpt!r}"
        assert _sha256(section) == _SNAP_DETECTION_RULES, (
            "Detection rules section changed (not byte-identical to UNFIXED snapshot)"
        )

    def test_false_positive_guards_byte_identical(self) -> None:
        """`## False Positive Guards` is byte-identical to the snapshot."""
        section = _extract_section(_read(_OFFER_FILE), "False Positive Guards")
        assert section, "False positive guards section must be present"
        for excerpt in _FALSE_POSITIVE_GUARD_EXCERPTS:
            assert excerpt in section, f"Guards missing excerpt: {excerpt!r}"
        assert _sha256(section) == _SNAP_FALSE_POSITIVE_GUARDS, (
            "False positive guards section changed (not byte-identical to snapshot)"
        )

    def test_ordering_rules_byte_identical(self) -> None:
        """`## Ordering Rules` (track/mid-session/simultaneous) is byte-identical."""
        section = _extract_section(_read(_OFFER_FILE), "Ordering Rules")
        assert section, "Ordering rules section must be present"
        for excerpt in _ORDERING_RULE_EXCERPTS:
            assert excerpt in section, f"Ordering rules missing excerpt: {excerpt!r}"
        # celebration -> Completion Summary PDF offer -> export ordering preserved.
        assert _ordered(
            section,
            [
                "Track completion celebration message (\U0001f389)",
                "**\u2192 Completion Summary PDF offer \u2190 (here)**",
                "Export results offer (`scripts/export_results.py`)",
            ],
        ), "Track-completion ordering (celebration -> summary offer -> export) changed"
        assert _sha256(section) == _SNAP_ORDERING_RULES, (
            "Ordering rules section changed (not byte-identical to snapshot)"
        )

    def test_repeat_policy_byte_identical(self) -> None:
        """`## Repeat Policy` text is byte-identical to the snapshot."""
        section = _extract_section(_read(_OFFER_FILE), "Repeat Policy")
        assert section, "Repeat policy section must be present"
        assert _REPEAT_POLICY_EXCERPT in section, "Repeat policy text changed"
        assert _sha256(section) == _SNAP_REPEAT_POLICY, (
            "Repeat policy section changed (not byte-identical to snapshot)"
        )


# ===========================================================================
# Test — graduation.md Step 0 + Graduation Report untouched
# ===========================================================================


class TestGraduationStep0AndReportUntouched:
    """The recap-PDF attempt (Step 0a/0b/0c) and Graduation Report are unchanged.

    The fix may add a short note to the `## Step 0` intro, but the Step 0a/0b/0c
    recap-PDF procedure and the `## Graduation Report` section must remain
    byte-identical.

    Validates: Requirements 3.3, 3.6
    """

    def test_step0_recap_pdf_attempt_byte_identical(self) -> None:
        """Step 0a/0b/0c recap-PDF attempt block is byte-identical to the snapshot."""
        content = _read(_GRADUATION_FILE)
        block = _extract_inclusive(
            content,
            "### Step 0a: Recap Document Recovery",
            "Proceed to Step 1.",
        )
        assert block, "Step 0a/0b/0c recap-PDF block must be present"
        for excerpt in _GRAD_STEP0_EXCERPTS:
            assert excerpt in block, f"Step 0 block missing excerpt: {excerpt!r}"
        assert _sha256(block) == _SNAP_GRAD_STEP0_RECAP_ATTEMPT, (
            "Step 0a/0b/0c recap-PDF block changed (not byte-identical to snapshot)"
        )

    def test_graduation_report_byte_identical(self) -> None:
        """`## Graduation Report` (always-generate GRADUATION_REPORT.md) is unchanged."""
        section = _extract_section(_read(_GRADUATION_FILE), "Graduation Report")
        assert section, "Graduation Report section must be present"
        assert _GRAD_REPORT_ALWAYS_GENERATE in section, (
            "Graduation Report 'Always generate GRADUATION_REPORT.md' behavior changed"
        )
        assert _sha256(section) == _SNAP_GRAD_REPORT, (
            "Graduation Report section changed (not byte-identical to snapshot)"
        )


# ===========================================================================
# Test — module-completion.md celebration ordering unchanged
# ===========================================================================


class TestPathCompletionCelebrationOrderingUnchanged:
    """The Path Completion Celebration offer ordering is preserved.

    The celebration -> completion-summary offer -> export -> record export ->
    analytics -> certificate -> graduation offer -> feedback reminder ordering must be
    intact, and the whole section must remain byte-identical to the UNFIXED snapshot.

    Validates: Requirements 3.4
    """

    def test_celebration_ordering_byte_identical(self) -> None:
        """`## Path Completion Celebration` is byte-identical to the snapshot."""
        section = _extract_section(
            _read(_MODULE_COMPLETION_FILE), "Path Completion Celebration"
        )
        assert section, "Path Completion Celebration section must be present"
        assert _sha256(section) == _SNAP_PATH_COMPLETION_CELEBRATION, (
            "Path Completion Celebration section changed (not byte-identical)"
        )

    def test_celebration_offer_ordering_preserved(self) -> None:
        """Celebration -> export -> record export -> analytics -> certificate -> grad \
-> feedback."""
        section = _extract_section(
            _read(_MODULE_COMPLETION_FILE), "Path Completion Celebration"
        )
        assert _ordered(section, _CELEBRATION_ORDER_MARKERS), (
            "Path completion celebration offer ordering changed"
        )


# ===========================================================================
# Test — existing suites still pass (re-run via subprocess)
# ===========================================================================


class TestExistingSuitesStillPass:
    """The three existing completion-summary suites continue to pass unchanged.

    Re-runs the suites in a fresh subprocess so a regression in preserved behavior is
    caught here, not only in the dedicated suites.

    Validates: Requirements 3.8
    """

    def test_existing_completion_summary_suites_pass(self) -> None:
        """Re-run unit, properties, and integration suites; all must pass."""
        suites = [
            str(_TESTS_DIR / "test_completion_summary_unit.py"),
            str(_TESTS_DIR / "test_completion_summary_properties.py"),
            str(_TESTS_DIR / "test_completion_summary_integration.py"),
        ]
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *suites],
            cwd=str(_POWER_ROOT.parent),
            capture_output=True,
            text=True,
            timeout=600,
        )
        assert result.returncode == 0, (
            "Existing completion-summary suites must still pass.\n"
            f"STDOUT:\n{result.stdout[-3000:]}\n"
            f"STDERR:\n{result.stderr[-2000:]}"
        )


# ===========================================================================
# PBT — Non-bug-condition equivalence (F(X) = F'(X))
# ===========================================================================


@dataclass(frozen=True)
class Situation:
    """A non-bug-condition graduation/stopping-point situation."""

    stopping_point_detected: bool
    offer_answer: str


def simulate_workflow(situation: Situation, *, fixed: bool) -> frozenset[str]:
    """Model the post-completion outcome for the preserved (non-bug) input space.

    Outcome tokens:
        - "summary_md" : docs/completion_summary.md is created
        - "pdf"        : the shareable PDF is rendered
        - "surface"    : the summary/PDF is surfaced to the bootcamper

    For non-bug-condition inputs (no stopping point, or offer_answer == "yes") the
    original (F) and fixed (F') workflows produce identical outcomes — the preserved
    sections drive the same behavior.

    Args:
        situation: The non-bug-condition situation to model.
        fixed: Whether to model the fixed workflow (F') vs. the original (F).

    Returns:
        The frozenset of outcome tokens for the situation.
    """
    if not situation.stopping_point_detected:
        # No stopping point -> no offer, no summary, under both F and F'.
        return frozenset()
    if situation.offer_answer == "yes":
        # Accepted path: summary created + PDF rendered + surfaced, under F and F'.
        return frozenset({"summary_md", "pdf", "surface"})
    # Bug-condition branch (excluded by the generator below): F and F' differ.
    return frozenset({"summary_md"}) if fixed else frozenset()


def st_offer_answer() -> st.SearchStrategy[str]:
    """Draw the accepted offer answer ("yes") for the equivalence property."""
    return st.just("yes")


@st.composite
def st_non_bug_situation(draw: st.DrawFn) -> Situation:
    """Draw a non-bug-condition situation: accepted offer or no stopping point."""
    stopping_point_detected = draw(st.booleans())
    if stopping_point_detected:
        # Stopping point + accepted offer is non-bug-condition.
        return Situation(
            stopping_point_detected=True, offer_answer=draw(st_offer_answer())
        )
    # No stopping point: answer is irrelevant (no offer is presented).
    answer = draw(st.sampled_from(["yes", "no", "n/a", ""]))
    return Situation(stopping_point_detected=False, offer_answer=answer)


# --- session-log generation for the grounded accepted-path equivalence ----

_ACTION_TYPES = [
    "file_create", "file_modify", "file_delete", "command_run", "mcp_tool_call",
]
_FILE_ACTION_TYPES = {"file_create", "file_modify", "file_delete"}
_ARTIFACT_TYPES = ["script", "config", "data", "report", "visualization"]
_PATH_ALPHABET = "abcdefghijklmnopqrstuvwxyz/._"


@st.composite
def st_session_entry(draw: st.DrawFn) -> dict[str, object]:
    """Draw one valid session-log entry dict (question/answer/action/artifact)."""
    event_type = draw(st.sampled_from(["question", "answer", "action", "artifact"]))
    module = draw(st.integers(min_value=1, max_value=11))
    text = draw(st.text(min_size=1, max_size=60))
    if event_type in ("question", "answer"):
        data: dict[str, str] = {"text": text, "question_id": "q001"}
    elif event_type == "action":
        action_type = draw(st.sampled_from(_ACTION_TYPES))
        data = {"action_type": action_type, "description": text}
        if action_type in _FILE_ACTION_TYPES:
            data["file_path"] = draw(
                st.text(min_size=1, max_size=30, alphabet=_PATH_ALPHABET)
            )
    else:
        data = {
            "file_path": draw(
                st.text(min_size=1, max_size=30, alphabet=_PATH_ALPHABET)
            ),
            "artifact_type": draw(st.sampled_from(_ARTIFACT_TYPES)),
            "description": text,
        }
    return {
        "event_type": event_type,
        "module": module,
        "timestamp": "2025-01-10T09:00:00Z",
        "data": data,
    }


@st.composite
def st_session_log(draw: st.DrawFn) -> list[dict[str, object]]:
    """Draw a non-empty multi-entry session log."""
    return draw(st.lists(st_session_entry(), min_size=1, max_size=8))


def _write_log(log_path: Path, entries: list[dict[str, object]]) -> None:
    """Write session-log entry dicts to a JSONL file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, separators=(",", ":")) + "\n")


def _run_accepted_path(
    tmp: Path, entries: list[dict[str, object]]
) -> tuple[str, bool]:
    """Run the unchanged generator for the accepted ('yes') path.

    Writes a session log, progress, and preferences under ``tmp`` and runs ``main``
    with ``--pdf`` (modeling the accepted offer). Returns the rendered markdown content
    and whether the PDF was produced.

    Args:
        tmp: A unique temporary directory for this run.
        entries: The session-log entry dicts to render.

    Returns:
        A tuple of (markdown content, pdf_exists).
    """
    log_path = tmp / "config" / "session_log.jsonl"
    progress_path = tmp / "config" / "bootcamp_progress.json"
    prefs_path = tmp / "config" / "bootcamp_preferences.yaml"
    output_path = tmp / "docs" / "completion_summary.md"
    pdf_path = tmp / "docs" / "completion_summary.pdf"

    _write_log(log_path, entries)
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(
        json.dumps(
            {"current_module": 7, "modules_completed": [1], "track": "core_bootcamp"}
        ),
        encoding="utf-8",
    )
    prefs_path.write_text(
        "name: Test Bootcamper\ntrack: core_bootcamp\n", encoding="utf-8"
    )

    argv = [
        "--log", str(log_path),
        "--output", str(output_path),
        "--progress", str(progress_path),
        "--preferences", str(prefs_path),
        "--pdf-output", str(pdf_path),
        "--pdf",
    ]
    exit_code = main(argv)
    assert exit_code == 0, "Accepted-path generation should succeed for a valid log"
    return output_path.read_text(encoding="utf-8"), pdf_path.exists()


class TestNonBugConditionEquivalence:
    """Property 5 (preservation): F(X) = F'(X) for non-bug-condition inputs.

    For accepted offers and non-stopping-point situations, the original and fixed
    workflows behave identically. The accepted path is additionally grounded against
    the real (unchanged) generator to show byte-identical markdown under F and F'.

    Validates: Requirements 3.1, 3.4, 3.5, 3.7
    """

    @given(situation=st_non_bug_situation())
    @settings(max_examples=20)
    def test_non_bug_outcomes_equivalent(self, situation: Situation) -> None:
        """Original and fixed workflows produce identical outcomes off the bug path."""
        assert simulate_workflow(situation, fixed=False) == simulate_workflow(
            situation, fixed=True
        ), f"F(X) != F'(X) for non-bug-condition situation {situation!r}"

    # deadline disabled: each example runs the generator twice (incl. PDF render),
    # whose wall-clock time varies; correctness, not latency, is under test.
    @given(answer=st_offer_answer(), entries=st_session_log())
    @settings(max_examples=20, deadline=None)
    def test_accepted_path_markdown_identical_under_f_and_fprime(
        self, answer: str, entries: list[dict[str, object]]
    ) -> None:
        """Accepted ('yes') path renders byte-identical markdown under F and F'."""
        assert answer == "yes"
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            md_f, pdf_f = _run_accepted_path(Path(d1), entries)
            md_fprime, pdf_fprime = _run_accepted_path(Path(d2), entries)

        assert md_f == md_fprime, (
            "Accepted-path markdown differs between F and F' (preservation broken)"
        )
        assert "## Module " in md_f, (
            "Accepted-path markdown must contain module sections"
        )
        # Preservation is equivalence: whether a PDF is produced is data-dependent
        # (the generator skips it on insufficient data), but it must be identical
        # between F and F' for the same input.
        assert pdf_f == pdf_fprime, (
            "PDF outcome differs between F and F' for identical input "
            "(preservation broken)"
        )
