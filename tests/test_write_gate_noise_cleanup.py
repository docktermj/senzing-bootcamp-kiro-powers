"""Preservation property tests for the write-gate-noise-cleanup bugfix.

This bugfix consolidated two residual visible-noise defects tied to the
``write-policy-gate`` hook:

- **Defect 1 (stale onboarding note).** ``onboarding-flow.md`` carried a section
  ``## 0a. Why You May See "Rejected"/"Accepted" Messages`` describing an
  intercept-then-retry write cycle that no longer occurs. The fix removed it.
- **Defect 2 (steering gap).** ``agent-behavior-rules.md`` had no rule
  prohibiting the agent from narrating (emitting visible tokens) when it
  re-invokes a write after the ``write-policy-gate`` INTERNAL-FILE PASS-THROUGH
  applies. The fix appended a new Rule 5.

The transient bug-condition EXPLORATION tests that reproduced the *defective*
state have been removed now that the fix has landed — their job (confirming the
defects existed) is captured in git history for commit ``write-gate-noise-cleanup``.
What remains here is the durable PRESERVATION suite: it pins the content the fix
must leave untouched, so a future regression that alters the preserved
onboarding sections, Rules 1-4, or the write-policy-gate hook file is caught.

Feature: write-gate-noise-cleanup

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — the REAL power files whose preserved content the fix must not change.
# ---------------------------------------------------------------------------

_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
_STEERING_DIR: Path = _PROJECT_ROOT / "senzing-bootcamp" / "steering"
_ONBOARDING_FLOW: Path = _STEERING_DIR / "onboarding-flow.md"
_AGENT_BEHAVIOR_RULES: Path = _STEERING_DIR / "agent-behavior-rules.md"
_HOOKS_DIR: Path = _PROJECT_ROOT / "senzing-bootcamp" / "hooks"
_WRITE_POLICY_GATE: Path = _HOOKS_DIR / "write-policy-gate.json"

# The exact stale section heading that the fix removed (Defect 1). Retained here
# only so the preservation suite can assert it is not among the pinned sections.
_STALE_SECTION_HEADING: str = (
    '## 0a. Why You May See "Rejected"/"Accepted" Messages'
)

# The onboarding ``##`` sections that MUST be preserved verbatim (0a excluded).
_PRESERVED_ONBOARDING_HEADINGS: tuple[str, ...] = (
    "## 0. Setup Preamble",
    "## 0b. MCP Health Check",
    "## 0c. Version Display",
    "## 1. Directory Structure",
    "## 1b. Team Detection",
    "## 2. Prerequisite Check (Mandatory Gate)",
)

# The agent-behavior-rules ``##`` sections that MUST be preserved verbatim. The
# fix appends a new Rule 5, so ONLY Rules 1-4 are pinned (not the whole file).
_PRESERVED_RULE_HEADINGS: tuple[str, ...] = (
    "## Rule 1: Honor Explicit Continuation Requests",
    "## Rule 2: Acknowledge Bootcamper Responses Before Proceeding",
    "## Rule 3: Eliminate Ambiguous Yes/No Questions",
    "## Rule 4: Consistent Pointer Indicator",
)


# ---------------------------------------------------------------------------
# Preservation helpers (shared by the frozen-baseline capture and the tests).
# ---------------------------------------------------------------------------


def _onboarding_text() -> str:
    """Return the full text of onboarding-flow.md."""
    return _ONBOARDING_FLOW.read_text(encoding="utf-8")


def _sha256(text: str) -> str:
    """Return the hex SHA-256 digest of *text* (UTF-8 encoded).

    Args:
        text: The content to digest.

    Returns:
        The 64-character lowercase hex digest.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _agent_behavior_rules_text() -> str:
    """Return the full text of agent-behavior-rules.md."""
    return _AGENT_BEHAVIOR_RULES.read_text(encoding="utf-8")


def _write_policy_gate_text() -> str:
    """Return the full text of the write-policy-gate hook file."""
    return _WRITE_POLICY_GATE.read_text(encoding="utf-8")


def _extract_h2_section(text: str, heading: str) -> str:
    """Return the ``##`` section named *heading*, body-scoped and normalized.

    The section spans from its heading line through the line before the next
    ``## `` heading (so nested ``###`` subsections are included), joined with
    ``\\n`` and ``rstrip``-normalized. Normalization makes the digest immune to
    trailing-whitespace shifts caused by removing an adjacent section (0a) or
    appending a later one (Rule 5).

    Args:
        text: The full markdown text to search.
        heading: The exact heading line to locate (e.g. ``"## 0. Setup Preamble"``).

    Returns:
        The normalized section text, heading included.

    Raises:
        AssertionError: When *heading* is not present in *text*.
    """
    lines = text.splitlines()
    start_idx: int | None = None
    for i, line in enumerate(lines):
        if line.strip() == heading:
            start_idx = i
            break
    assert start_idx is not None, f"section heading not found: {heading!r}"
    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        if lines[j].startswith("## "):
            end_idx = j
            break
    return "\n".join(lines[start_idx:end_idx]).rstrip()


def _current_hook_digest() -> str:
    """Return the current whole-file SHA-256 digest of the hook file."""
    return _sha256(_write_policy_gate_text())


# ---------------------------------------------------------------------------
# FROZEN baselines — captured from the current (unfixed) power files.
# These literals must NOT be recomputed from the files; freezing them is what
# lets the preservation tests detect an accidental change after the fix.
# ---------------------------------------------------------------------------

_FROZEN_ONBOARDING_SHA256: dict[str, str] = {
    "## 0. Setup Preamble": (
        "b5b4d967d8a7dd9329ad05e682f4cd869ca81197be13322e77a3715f4615aa14"
    ),
    "## 0b. MCP Health Check": (
        "121cc01a8cb444bce76a8445446a12ff1c86f745cc2f3ccdd8137c6f5dba6393"
    ),
    "## 0c. Version Display": (
        "f00d1749ab91a4bc9813371d17ee3bfa3c6fe60916f361ac82f9edada730f751"
    ),
    "## 1. Directory Structure": (
        "3fb4e9f7416ca51946cb7c29ac0a7bbc20e31af66f63733164cb641c3b036c6e"
    ),
    "## 1b. Team Detection": (
        "3cbb0af39796296aefc3393fb090cc33d3826e4565abb48365dd73c72d819682"
    ),
    # Re-baselined for the preface-flow-and-banners spec (reorder): the trailing
    # hand-off paragraph in the "## 2. Prerequisite Check" section (which the
    # body-scoped extractor includes, since it runs to EOF) was updated to note
    # that programming language selection now happens later, in phase 2
    # (onboarding-phase2-track-setup.md), after track selection. That reorder edit
    # is unrelated to the write-gate-noise-cleanup fix this suite guards, so the
    # baseline is moved observation-first to the current section contents. Sections
    # 0/0b/0c/1/1b were verified byte-identical during the re-pin.
    "## 2. Prerequisite Check (Mandatory Gate)": (
        "e5cca88db42eb5fa81d9443d535c0206fe6af6d40d798911793b65f145ec3d2b"
    ),
}

# Re-pinned for the clean-question-presentation bugfix: that spec legitimately
# amended two of these four rule sections (design.md mandates editing
# agent-behavior-rules.md Rule 3 and Rule 4), so their body-scoped,
# rstrip-normalized SHA-256 baselines were re-frozen to the current measured
# reality:
#   * Rule 3 (Eliminate Ambiguous Yes/No Questions) — the compose-clean-first
#     clause was added (the FIRST composed question must already be single and
#     non-compound, not merely rewritten after the fact):
#       b794e9f3...608e2d4 -> 6cf4054e...d207ab4
#   * Rule 4 (Consistent Pointer Indicator) — the internal-only control-directive
#     clause was added (🛑 STOP / ⛔ MANDATORY GATE govern end-of-turn / gate
#     semantics but are NEVER rendered to the bootcamper; the rendered boundary
#     is the trailing 👉 question):
#       e1c60143...c9ea35af -> 8281cfde...c549b3db
# Rules 1 and 2 were NOT touched by this spec and remain byte-identical to their
# original frozen baselines (verified unchanged during the re-pin), so only the
# Rule 3 and Rule 4 literals moved. The test logic and _PRESERVED_RULE_HEADINGS
# are unchanged — this is a frozen-baseline re-pin, not a logic change.
_FROZEN_RULE_SHA256: dict[str, str] = {
    "## Rule 1: Honor Explicit Continuation Requests": (
        "36356379c3ccccfefbbcbd3a6de878dc0818ed8cc606ab685ee158d9af6485b1"
    ),
    "## Rule 2: Acknowledge Bootcamper Responses Before Proceeding": (
        "dbe37ffcc977be613215093d119ed8e755a9ed22dcd16f9897f58430592f42e5"
    ),
    "## Rule 3: Eliminate Ambiguous Yes/No Questions": (
        "6cf4054ea7296cb88dc63831bd8412140686c3745c4f72d4f2c1d976dd207ab4"
    ),
    "## Rule 4: Consistent Pointer Indicator": (
        "8281cfde5e46f4896c5b841166eab3e7cc680032db5c637b67e20113c549b3db"
    ),
}

# Re-baselined for the mandatory-question-answers spec (Task 5.1 / 6.2): that
# spec legitimately extended the write-policy-gate prompt with CHECK 5
# (ANSWER-REQUIRED — no silent completion of a question-owning step) and a
# matching NOT-guard in the INTERNAL-FILE PASS-THROUGH, and re-titled the header
# "Four checks" -> "Five checks in one pass". The gate file's bytes therefore
# changed by design, so the frozen whole-file digest is re-pinned to the new
# measured reality:
#   271a6fbe...364a4b -> 9caa3745...184372
# This is a mechanical re-baseline of a pinned derived snapshot, not a logic
# change: the test still guards the gate against any UNINTENDED future edit.
_FROZEN_HOOK_SHA256: str = (
    "9caa3745ad6071190624a6922d59ded9301bb4e8c5cb59dbbdb455f7cb184372"
)


# ---------------------------------------------------------------------------
# Hypothesis strategies (preserved-content input domain)
# ---------------------------------------------------------------------------


def st_preserved_onboarding_index() -> st.SearchStrategy[int]:
    """Draw a random index into ``_PRESERVED_ONBOARDING_HEADINGS``."""
    return st.integers(min_value=0, max_value=len(_PRESERVED_ONBOARDING_HEADINGS) - 1)


def st_preserved_rule_index() -> st.SearchStrategy[int]:
    """Draw a random index into ``_PRESERVED_RULE_HEADINGS``."""
    return st.integers(min_value=0, max_value=len(_PRESERVED_RULE_HEADINGS) - 1)


# ---------------------------------------------------------------------------
# Property 2: Preservation
# ---------------------------------------------------------------------------


class TestPreservation:
    """Property 2 - legitimate gate behavior and non-0a onboarding unchanged.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

    These tests pin only the individual preserved sections/rules (body-scoped,
    ``rstrip``-normalized) and the whole hook file, so they PASS both before and
    after the fix (which removes section 0a and appends Rule 5) and catch any
    future regression that alters preserved content.
    """

    # -- Hook file integrity (Requirement 3.3) ------------------------------

    def test_hook_file_byte_for_byte_unchanged(self) -> None:
        """write-policy-gate.json matches its frozen whole-file digest.

        The hook's ``preToolUse`` trigger, write-type ``toolTypes``, and
        INTERNAL-FILE PASS-THROUGH set must remain unchanged; a whole-file
        digest is the strongest guard.

        **Validates: Requirements 3.3**
        """
        assert _WRITE_POLICY_GATE.is_file(), (
            f"hook file missing: {_WRITE_POLICY_GATE}"
        )
        assert _current_hook_digest() == _FROZEN_HOOK_SHA256, (
            "write-policy-gate.json changed — the hook file must be byte-for-byte "
            f"unchanged (security constraint). Expected {_FROZEN_HOOK_SHA256}, "
            f"got {_current_hook_digest()}."
        )

    # -- Onboarding section preservation (Requirements 3.4) -----------------

    def test_all_preserved_onboarding_sections_present_and_unchanged(self) -> None:
        """Every non-0a onboarding section is present with unchanged content.

        **Validates: Requirements 3.4**
        """
        text = _onboarding_text()
        for heading in _PRESERVED_ONBOARDING_HEADINGS:
            section = _extract_h2_section(text, heading)
            assert _sha256(section) == _FROZEN_ONBOARDING_SHA256[heading], (
                f"onboarding section {heading!r} changed — its content must be "
                "preserved verbatim by the fix (only section 0a is removed)."
            )

    def test_stale_section_0a_not_in_preserved_baselines(self) -> None:
        """Sanity: the removed 0a section is not among the preserved baselines.

        Guards the survival design — if 0a were pinned as "preserved", the test
        would wrongly fail once the fix removes it.

        **Validates: Requirements 3.4**
        """
        joined = "\n".join(_PRESERVED_ONBOARDING_HEADINGS)
        assert _STALE_SECTION_HEADING not in joined, (
            "section 0a must NOT be captured as a preserved section"
        )

    # -- Agent behavior rules additive-only (Requirements 3.3) --------------

    def test_rules_1_to_4_present_and_unchanged(self) -> None:
        """Rules 1-4 are present with unchanged content (Rule 5 may be added).

        Only per-rule digests are pinned, so appending a new Rule 5 later does
        not break this assertion.

        **Validates: Requirements 3.3**
        """
        text = _agent_behavior_rules_text()
        for heading in _PRESERVED_RULE_HEADINGS:
            section = _extract_h2_section(text, heading)
            assert _sha256(section) == _FROZEN_RULE_SHA256[heading], (
                f"agent behavior {heading!r} changed — Rules 1-4 must be "
                "preserved verbatim; the fix may only append a new Rule 5."
            )

    # -- Property-based coverage over the preserved-content domain ----------

    @given(index=st_preserved_onboarding_index())
    def test_property_random_onboarding_section_preserved(self, index: int) -> None:
        """For a random preserved-section index, content matches its baseline.

        **Validates: Requirements 3.1, 3.2, 3.4**
        """
        heading = _PRESERVED_ONBOARDING_HEADINGS[index]
        section = _extract_h2_section(_onboarding_text(), heading)
        assert section, f"preserved onboarding section is empty: {heading!r}"
        assert _sha256(section) == _FROZEN_ONBOARDING_SHA256[heading], (
            f"preserved onboarding section {heading!r} content changed"
        )

    @given(index=st_preserved_rule_index())
    def test_property_random_rule_preserved(self, index: int) -> None:
        """For a random Rule 1-4 index, content matches its baseline.

        **Validates: Requirements 3.3**
        """
        heading = _PRESERVED_RULE_HEADINGS[index]
        section = _extract_h2_section(_agent_behavior_rules_text(), heading)
        assert section, f"preserved rule section is empty: {heading!r}"
        assert _sha256(section) == _FROZEN_RULE_SHA256[heading], (
            f"preserved rule section {heading!r} content changed"
        )
