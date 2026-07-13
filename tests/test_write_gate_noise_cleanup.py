"""Bug-condition EXPLORATION tests for the write-gate-noise-cleanup bugfix.

Property 1: Bug Condition — No Stale/Unwanted Write-Gate Output.

This bugfix consolidates two residual visible-noise defects tied to the
``write-policy-gate`` hook:

- **Defect 1 (stale onboarding note).** ``onboarding-flow.md`` still carries the
  section ``## 0a. Why You May See "Rejected"/"Accepted" Messages`` describing an
  intercept-then-retry write cycle that no longer occurs.
- **Defect 2 (steering gap).** ``agent-behavior-rules.md`` contains no rule that
  explicitly prohibits the agent from narrating (emitting visible tokens) when it
  re-invokes a write after the ``write-policy-gate`` INTERNAL-FILE PASS-THROUGH
  applies.

**IMPORTANT — inverted convention for this spec.** Unlike the standard bugfix
exploration test (which encodes the *fixed* behavior and fails on unfixed code),
this test encodes the *defective* state:

- On the CURRENT (unfixed) code these assertions **PASS** — the pass confirms
  both defects exist (section 0a is present; no anti-narration rule exists).
- After the fix (section 0a removed + Rule 5 added), these same assertions
  **FAIL** — the failure confirms the stale content was removed and the new
  steering rule was added.

Do NOT "fix" this test when it later fails; the failure is the success signal
for the fix. See ``design.md`` — Exploratory Bug Condition Checking.

Bug condition (from ``design.md``)::

    FUNCTION isBugCondition(input)
      staleOnboardingNote :=
            input.kind = "onboarding_preamble" AND input.note_present = TRUE
      narratedSilentReinvoke :=
            input.kind = "write_gate_passthrough"
        AND input.is_passthrough = TRUE
        AND input.target_path IS a routine power-managed internal file
        AND input.not_guards_hold = TRUE
        AND input.emitted_tokens != EMPTY
      RETURN staleOnboardingNote OR narratedSilentReinvoke

Feature: write-gate-noise-cleanup

**Validates: Requirements 1.1, 1.2**
"""

from __future__ import annotations

import hashlib
import re
import string
from dataclasses import dataclass
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — the REAL power steering files whose content encodes the two defects.
# ---------------------------------------------------------------------------

_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
_STEERING_DIR: Path = _PROJECT_ROOT / "senzing-bootcamp" / "steering"
_ONBOARDING_FLOW: Path = _STEERING_DIR / "onboarding-flow.md"
_AGENT_BEHAVIOR_RULES: Path = _STEERING_DIR / "agent-behavior-rules.md"

# The exact stale section heading (Defect 1).
_STALE_SECTION_HEADING: str = (
    '## 0a. Why You May See "Rejected"/"Accepted" Messages'
)

# A representative narration line the agent leaks on pass-through today (Defect 2).
_SAMPLE_NARRATION: str = "Internal progress file — re-invoking silently."

# Signals used to detect an explicit anti-narration pass-through rule (Defect 2).
_PASSTHROUGH_PATTERN = re.compile(r"pass[\s\-]?through", re.IGNORECASE)
_SILENCE_PROHIBITION_MARKERS: tuple[str, ...] = (
    "zero token",
    "zero visible token",
    "no visible token",
    "no narration",
    "without narration",
    "must not narrate",
    "must not emit",
    "emit no",
    "emits no",
    "produce no",
    "no tokens",
    "silent",
)


# ---------------------------------------------------------------------------
# Bug-condition model (mirrors design.md isBugCondition over WriteGateOutputEvent)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WriteGateOutputEvent:
    """A visible write-gate-related output event the bootcamper may observe.

    Attributes:
        kind: Either ``"onboarding_preamble"`` or ``"write_gate_passthrough"``.
        note_present: True when the stale "Rejected/Accepted" onboarding note
            is present in onboarding content.
        is_passthrough: True when the write-policy-gate INTERNAL-FILE
            PASS-THROUGH applied to this write.
        target_path: The write target path.
        not_guards_hold: True when all INTERNAL-FILE PASS-THROUGH NOT-guards
            hold (routine internal file, no Senzing SQL, etc.).
        emitted_tokens: Visible tokens the agent emitted on re-invoke;
            ``""`` means EMPTY (no narration).
    """

    kind: str
    note_present: bool
    is_passthrough: bool
    target_path: str
    not_guards_hold: bool
    emitted_tokens: str


def _is_internal_file(path: str) -> bool:
    """Return True when *path* is a routine power-managed internal file.

    Args:
        path: The write target path.

    Returns:
        True for the progress/preference config files (fixed and member-scoped)
        and power-written module-complete log files.
    """
    if path in ("config/bootcamp_progress.json", "config/bootcamp_preferences.yaml"):
        return True
    if re.fullmatch(r"config/progress_[A-Za-z0-9_\-]+\.json", path):
        return True
    if re.fullmatch(r"config/preferences_[A-Za-z0-9_\-]+\.yaml", path):
        return True
    if re.fullmatch(r"docs/progress/MODULE_\d+_COMPLETE\.md", path):
        return True
    return False


def is_bug_condition(event: WriteGateOutputEvent) -> bool:
    """Evaluate design.md ``isBugCondition`` for *event*.

    Args:
        event: The write-gate output event to classify.

    Returns:
        True when the event represents stale/unwanted write-gate output — either
        the stale onboarding note is shown, or the agent narrates on an
        internal-file pass-through re-invoke.
    """
    stale_onboarding_note = (
        event.kind == "onboarding_preamble" and event.note_present is True
    )
    narrated_silent_reinvoke = (
        event.kind == "write_gate_passthrough"
        and event.is_passthrough is True
        and _is_internal_file(event.target_path)
        and event.not_guards_hold is True
        and event.emitted_tokens != ""
    )
    return stale_onboarding_note or narrated_silent_reinvoke


# ---------------------------------------------------------------------------
# Parsers — derive the two defect signals from the REAL steering files.
# ---------------------------------------------------------------------------


def _onboarding_text() -> str:
    """Return the full text of onboarding-flow.md."""
    return _ONBOARDING_FLOW.read_text(encoding="utf-8")


def _stale_note_present() -> bool:
    """Return True when the stale section-0a heading is in onboarding-flow.md."""
    return _STALE_SECTION_HEADING in _onboarding_text()


def _stale_note_line_number() -> int | None:
    """Return the 1-based line number of the stale section-0a heading, if any.

    Returns:
        The line number where the stale heading appears, or ``None`` when the
        heading is absent.
    """
    for idx, line in enumerate(_onboarding_text().splitlines(), start=1):
        if line.strip() == _STALE_SECTION_HEADING:
            return idx
    return None


def _split_rule_sections(text: str) -> list[str]:
    """Split a steering file into ``##``-delimited sections.

    Args:
        text: The full steering file text.

    Returns:
        A list of section strings, each beginning at a ``## `` heading.
    """
    # Prefix a newline so a leading heading is still captured by the lookahead.
    parts = re.split(r"(?m)^(?=## )", "\n" + text)
    return [p for p in parts if p.strip()]


def _passthrough_narration_rule_present() -> bool:
    """Return True when a rule explicitly prohibits pass-through narration.

    A qualifying rule is a ``##`` section that references an internal-file
    pass-through AND mandates the absence of visible tokens (silence / zero
    tokens / no narration). The current Rule 4 references an intercept/retry
    *cycle* but neither "pass-through" nor a zero-token mandate, so it does not
    qualify.

    Returns:
        True when at least one section prohibits narration on pass-through
        re-invoke; False otherwise (the Defect 2 steering gap).
    """
    for section in _split_rule_sections(_AGENT_BEHAVIOR_RULES.read_text(encoding="utf-8")):
        if not _PASSTHROUGH_PATTERN.search(section):
            continue
        lowered = section.lower()
        if any(marker in lowered for marker in _SILENCE_PROHIBITION_MARKERS):
            return True
    return False


def _passthrough_emitted_tokens() -> str:
    """Return the tokens the agent emits on internal-file pass-through today.

    When no anti-narration rule exists (the Defect 2 gap), the agent leaks a
    narration line; model that as a non-empty token string. When the rule
    exists (post-fix), model zero tokens.

    Returns:
        A sample narration string when the steering gap is present, else ``""``.
    """
    return "" if _passthrough_narration_rule_present() else _SAMPLE_NARRATION


# ---------------------------------------------------------------------------
# Hypothesis strategies (bug-condition input domain)
# ---------------------------------------------------------------------------


def _st_member_id() -> st.SearchStrategy[str]:
    """Member identifier for co-located team-mode internal files."""
    return st.text(
        alphabet=string.ascii_lowercase + string.digits + "_-",
        min_size=1,
        max_size=12,
    )


@st.composite
def st_internal_file_path(draw) -> str:
    """Draw a routine power-managed internal-file path.

    Covers every member of the internal-file set: the two fixed config files,
    member-scoped progress/preference files, and power-written module logs.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        An internal-file path for which ``_is_internal_file`` holds.
    """
    kind = draw(
        st.sampled_from(
            ["progress", "preferences", "member_progress", "member_preferences", "log"]
        )
    )
    if kind == "progress":
        return "config/bootcamp_progress.json"
    if kind == "preferences":
        return "config/bootcamp_preferences.yaml"
    if kind == "member_progress":
        return "config/progress_%s.json" % draw(_st_member_id())
    if kind == "member_preferences":
        return "config/preferences_%s.yaml" % draw(_st_member_id())
    return "docs/progress/MODULE_%d_COMPLETE.md" % draw(
        st.integers(min_value=1, max_value=11)
    )


@st.composite
def st_onboarding_event(draw) -> WriteGateOutputEvent:
    """Draw an onboarding-preamble event bound to the REAL onboarding content.

    ``note_present`` reflects the actual parsed state of onboarding-flow.md so
    the event faithfully represents Defect 1 on the current code. Other fields
    are varied to span the (irrelevant-for-this-kind) input space.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``kind="onboarding_preamble"`` event.
    """
    return WriteGateOutputEvent(
        kind="onboarding_preamble",
        note_present=_stale_note_present(),
        is_passthrough=draw(st.booleans()),
        target_path=draw(st.sampled_from(["", "config/bootcamp_progress.json"])),
        not_guards_hold=draw(st.booleans()),
        emitted_tokens=draw(st.sampled_from(["", "some text"])),
    )


@st.composite
def st_passthrough_event(draw) -> WriteGateOutputEvent:
    """Draw an internal-file pass-through event bound to the REAL steering gap.

    ``emitted_tokens`` reflects whether an anti-narration rule exists in
    agent-behavior-rules.md: absent rule => non-empty tokens (Defect 2 present).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``kind="write_gate_passthrough"`` event over an internal-file path.
    """
    return WriteGateOutputEvent(
        kind="write_gate_passthrough",
        note_present=draw(st.booleans()),
        is_passthrough=True,
        target_path=draw(st_internal_file_path()),
        not_guards_hold=True,
        emitted_tokens=_passthrough_emitted_tokens(),
    )


# ---------------------------------------------------------------------------
# Property 1: Bug Condition — No Stale/Unwanted Write-Gate Output
# ---------------------------------------------------------------------------


class TestBugConditionExploration:
    """Property 1 — confirm both write-gate noise defects exist on unfixed code.

    **Validates: Requirements 1.1, 1.2**

    These assertions encode the *defective* state and therefore PASS on the
    current (unfixed) code and FAIL once the fix removes section 0a and adds the
    anti-narration rule. A PASS here is the SUCCESS signal that both defects are
    present and reproduced.
    """

    # -- Defect 1: stale onboarding note present (Requirement 1.1) -----------

    def test_defect_1_stale_onboarding_note_present(self) -> None:
        """The stale section-0a heading is present in onboarding-flow.md.

        Encodes ``staleOnboardingNote`` (``note_present = TRUE``). PASS on
        unfixed code confirms Defect 1.

        **Validates: Requirements 1.1**
        """
        line_no = _stale_note_line_number()
        assert _stale_note_present(), (
            "Defect 1 NOT reproduced: the stale onboarding section "
            f"{_STALE_SECTION_HEADING!r} was not found in {_ONBOARDING_FLOW}. "
            "On unfixed code this section is expected to be present."
        )
        # Counterexample evidence captured in the assertion message.
        assert line_no is not None, (
            f"stale section heading present but line number not resolved in "
            f"{_ONBOARDING_FLOW}"
        )

    def test_defect_1_stale_note_describes_rejected_accepted_cycle(self) -> None:
        """The stale-note body describes the obsolete Rejected/Accepted cycle.

        Reinforces that ``note_present`` reflects real intercept-then-retry
        reassurance content, not merely a bare heading.

        **Validates: Requirements 1.1**
        """
        text = _onboarding_text()
        assert "Rejected" in text and "Accepted" in text, (
            "Defect 1 NOT reproduced: expected the obsolete "
            "'Rejected'/'Accepted' reassurance content in "
            f"{_ONBOARDING_FLOW}."
        )

    # -- Defect 2: no anti-narration pass-through rule (Requirement 1.2) -----

    def test_defect_2_no_passthrough_narration_rule(self) -> None:
        """No rule prohibits narration on internal-file pass-through re-invoke.

        Encodes the Defect 2 steering gap: with no such rule, the agent may
        emit ``emitted_tokens != EMPTY`` on pass-through. PASS on unfixed code
        confirms Defect 2.

        **Validates: Requirements 1.2**
        """
        assert not _passthrough_narration_rule_present(), (
            "Defect 2 NOT reproduced: a rule prohibiting narration on "
            "internal-file pass-through re-invoke already exists in "
            f"{_AGENT_BEHAVIOR_RULES}. On unfixed code no such rule is expected."
        )

    # -- Property-based coverage of the isBugCondition domain ----------------

    @given(event=st_onboarding_event())
    def test_property_onboarding_events_are_bug_condition(
        self, event: WriteGateOutputEvent
    ) -> None:
        """For all onboarding events, isBugCondition holds on unfixed code.

        Because ``note_present`` is bound to the real onboarding content (stale
        note present), every generated ``onboarding_preamble`` event satisfies
        ``staleOnboardingNote`` and therefore ``isBugCondition``.

        **Validates: Requirements 1.1**
        """
        assert event.note_present is True, (
            "expected the stale onboarding note to be present on unfixed code"
        )
        assert is_bug_condition(event), (
            "Defect 1 NOT reproduced: onboarding event did not satisfy "
            f"isBugCondition despite stale note present: {event!r}"
        )

    @given(event=st_passthrough_event())
    def test_property_passthrough_events_are_bug_condition(
        self, event: WriteGateOutputEvent
    ) -> None:
        """For all internal-file pass-through events, isBugCondition holds.

        Because ``emitted_tokens`` is bound to the real steering gap (no
        anti-narration rule => non-empty tokens), every generated internal-file
        pass-through event satisfies ``narratedSilentReinvoke`` and therefore
        ``isBugCondition``.

        **Validates: Requirements 1.2**
        """
        assert event.emitted_tokens != "", (
            "expected the agent to emit narration tokens on pass-through given "
            "the missing anti-narration steering rule on unfixed code"
        )
        assert _is_internal_file(event.target_path), (
            f"generator produced a non-internal-file path: {event.target_path}"
        )
        assert is_bug_condition(event), (
            "Defect 2 NOT reproduced: pass-through event did not satisfy "
            f"isBugCondition despite emitted narration tokens: {event!r}"
        )


# ===========================================================================
# Property 2: Preservation — Legitimate Gate Behavior & Other Onboarding Unchanged
# ===========================================================================
#
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
#
# Observation-first methodology: the FROZEN baselines below were captured from
# the CURRENT (unfixed) power files. They pin the exact content that the fix
# (Task 3) MUST leave untouched:
#
#   - every non-0a onboarding section (0, 0b, 0c, 1, 1b, 2),
#   - the write-policy-gate hook file (whole-file digest),
#   - Rules 1–4 of agent-behavior-rules.md (individual per-rule digests).
#
# Designed to survive the upcoming fix:
#   * We do NOT capture section 0a — it is being removed, so it is absent from
#     every baseline collection.
#   * We do NOT hash onboarding-flow.md or agent-behavior-rules.md as a whole —
#     both files change (0a removed / Rule 5 appended). Only INDIVIDUAL preserved
#     sections and INDIVIDUAL Rules 1–4 are digested.
#   * Section/rule extraction is body-scoped and ``rstrip``-normalized, so
#     removing 0a (which only shifts section 0's following heading from ``0a`` to
#     ``0b``) and appending Rule 5 (which only adds trailing content after Rule 4)
#     leave the preserved digests byte-identical.
#   * The hook file IS hashed whole — the security constraint forbids any change.

# ---------------------------------------------------------------------------
# Additional paths for preservation baselines.
# ---------------------------------------------------------------------------

_HOOKS_DIR: Path = _PROJECT_ROOT / "senzing-bootcamp" / "hooks"
_WRITE_POLICY_GATE: Path = _HOOKS_DIR / "write-policy-gate.json"

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
# fix appends a new Rule 5, so ONLY Rules 1–4 are pinned (not the whole file).
_PRESERVED_RULE_HEADINGS: tuple[str, ...] = (
    "## Rule 1: Honor Explicit Continuation Requests",
    "## Rule 2: Acknowledge Bootcamper Responses Before Proceeding",
    "## Rule 3: Eliminate Ambiguous Yes/No Questions",
    "## Rule 4: Consistent Pointer Indicator",
)


# ---------------------------------------------------------------------------
# Preservation helpers (shared by the frozen-baseline capture and the tests).
# ---------------------------------------------------------------------------


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


def _current_onboarding_digests() -> dict[str, str]:
    """Return current SHA-256 digests for each preserved onboarding section."""
    text = _onboarding_text()
    return {
        heading: _sha256(_extract_h2_section(text, heading))
        for heading in _PRESERVED_ONBOARDING_HEADINGS
    }


def _current_rule_digests() -> dict[str, str]:
    """Return current SHA-256 digests for each preserved Rule 1–4 section."""
    text = _agent_behavior_rules_text()
    return {
        heading: _sha256(_extract_h2_section(text, heading))
        for heading in _PRESERVED_RULE_HEADINGS
    }


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
    "## 2. Prerequisite Check (Mandatory Gate)": (
        "99e5de49bea96c3f1fc241486637d859cdbe3c9e9aefdf1554970232a77f2978"
    ),
}

_FROZEN_RULE_SHA256: dict[str, str] = {
    "## Rule 1: Honor Explicit Continuation Requests": (
        "36356379c3ccccfefbbcbd3a6de878dc0818ed8cc606ab685ee158d9af6485b1"
    ),
    "## Rule 2: Acknowledge Bootcamper Responses Before Proceeding": (
        "dbe37ffcc977be613215093d119ed8e755a9ed22dcd16f9897f58430592f42e5"
    ),
    "## Rule 3: Eliminate Ambiguous Yes/No Questions": (
        "b794e9f36d40ab14285a65dccc8dd61a649c7c602a105aefe3dafc937608e2d4"
    ),
    "## Rule 4: Consistent Pointer Indicator": (
        "e1c6014348618872dc7356b0bc0029acc232acebbae7656f09ffb0bcc9ea35af"
    ),
}

_FROZEN_HOOK_SHA256: str = (
    "271a6fbe6ad48666fa5967fe14b0555d9ebe2305f0a54200ca0990cb21364a4b"
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
    """Property 2 — legitimate gate behavior and non-0a onboarding unchanged.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

    EXPECTED OUTCOME on UNFIXED code: all tests PASS (confirms the baseline that
    the fix must preserve). These tests are designed to STILL PASS after the fix
    removes section 0a and appends Rule 5, because they pin only the individual
    preserved sections/rules (body-scoped, ``rstrip``-normalized) and the whole
    hook file — none of which the fix may change.
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
        """Rules 1–4 are present with unchanged content (Rule 5 may be added).

        Only per-rule digests are pinned, so appending a new Rule 5 later does
        not break this assertion.

        **Validates: Requirements 3.3**
        """
        text = _agent_behavior_rules_text()
        for heading in _PRESERVED_RULE_HEADINGS:
            section = _extract_h2_section(text, heading)
            assert _sha256(section) == _FROZEN_RULE_SHA256[heading], (
                f"agent behavior {heading!r} changed — Rules 1–4 must be "
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
        """For a random Rule 1–4 index, content matches its baseline.

        **Validates: Requirements 3.3**
        """
        heading = _PRESERVED_RULE_HEADINGS[index]
        section = _extract_h2_section(_agent_behavior_rules_text(), heading)
        assert section, f"preserved rule section is empty: {heading!r}"
        assert _sha256(section) == _FROZEN_RULE_SHA256[heading], (
            f"preserved rule section {heading!r} content changed"
        )
