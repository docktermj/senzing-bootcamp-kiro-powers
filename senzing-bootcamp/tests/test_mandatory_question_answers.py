"""Rule-presence and corpus-sweep tests for the mandatory-question-answers spec.

This module encodes the Requirement 6.3 content guarantees for the
mandatory-question-answers feature:

1. **Rule presence.** ``conversation-protocol.md`` states the single normative
   ``Answer_Required_Rule`` — every ``👉`` question requires a Real_Answer
   before the flow advances, the agent never supplies an Assumed_Answer / silent
   default, the only two exits are a Real_Answer or the question staying
   outstanding, and optionality is expressed as an Explicit_Default_Choice — and
   ``agent-behavior-rules.md`` and ``agent-instructions.md`` reference it.
2. **Corpus sweep.** No steering file authorizes advancing an *unanswered*
   ``👉`` question via an Assumed_Answer / silent-default idiom, EXCEPT the one
   allowlisted load-time preference fallback in ``verbosity-control.md`` (which
   is a *stored-preference-absent-at-load* fallback, not an unanswered-question
   path). The sweep is meaningful: it fails if a silent-default authorization is
   re-introduced anywhere else, and the same pattern demonstrably flags the
   allowlisted line when the allowlist is removed.
3. **Enforcement hook.** ``write-policy-gate.json`` carries the new CHECK 5
   answer-required check, and the ``hook-registry-critical.md`` mirror embeds
   the same CHECK 5 text.

Feature: mandatory-question-answers

**Validates: Requirements 6.3**
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths (resolved relative to this test file: senzing-bootcamp/{steering,hooks})
# ---------------------------------------------------------------------------

_POWER_ROOT: Path = Path(__file__).resolve().parent.parent
_STEERING_DIR: Path = _POWER_ROOT / "steering"
_HOOKS_DIR: Path = _POWER_ROOT / "hooks"

_CONVERSATION_PROTOCOL: Path = _STEERING_DIR / "conversation-protocol.md"
_AGENT_BEHAVIOR_RULES: Path = _STEERING_DIR / "agent-behavior-rules.md"
_AGENT_INSTRUCTIONS: Path = _STEERING_DIR / "agent-instructions.md"
_VERBOSITY_CONTROL: Path = _STEERING_DIR / "verbosity-control.md"
_WRITE_POLICY_GATE: Path = _HOOKS_DIR / "write-policy-gate.json"
_HOOK_REGISTRY_CRITICAL: Path = _STEERING_DIR / "hook-registry-critical.md"
# Prior-spec steering the Answer_Required_Rule must stay consistent with
# (Requirement 5.1 / 5.2 cross-spec invariants).
_SKIP_STEP_PROTOCOL: Path = _STEERING_DIR / "skip-step-protocol.md"
_SESSION_RESUME: Path = _STEERING_DIR / "session-resume.md"

# The pointing-hand glyph that marks a bootcamper-directed question.
_POINTER: str = "\U0001f449"  # 👉


# ---------------------------------------------------------------------------
# Corpus-sweep model
# ---------------------------------------------------------------------------
# Each pattern captures an Assumed_Answer / silent-default idiom that, if used
# affirmatively, would authorize advancing past an UNANSWERED 👉 question. A
# match is a violation UNLESS (a) it is the single allowlisted load-time
# preference fallback in verbosity-control.md, or (b) it appears inside a
# prohibition ("do NOT ...", "never ...", "... is forbidden"). The onboarding /
# module-05 texts mention these idioms only to FORBID them, so they are not
# violations.

_SILENT_DEFAULT_PATTERNS: dict[str, re.Pattern[str]] = {
    # The exact tell-tale of the removed verbosity silent default:
    # "if the bootcamper skips without answering, apply the `standard` preset ...".
    "skip-without-answering": re.compile(r"skips?\s+without\s+answering", re.IGNORECASE),
    # Affirmative "apply <preset> as the default" — the removed silent-default
    # idiom. The legitimate onboarding/module-05 prohibitions use the distinct
    # "as a silent default" wording, so they do not match this pattern.
    "apply-preset-as-default": re.compile(
        r"appl(?:y|ies)\s+(?:the\s+)?[`'\"]?\w+[`'\"]?\s+(?:preset\s+)?as\s+the\s+default",
        re.IGNORECASE,
    ),
    # Advancing with no bootcamper answer to a 👉 question.
    "proceed-without-answer": re.compile(
        r"proceed(?:ing|s)?\s+without\s+(?:an?\s+)?(?:real[\s_-]*)?(?:answer|response)",
        re.IGNORECASE,
    ),
    # "if the bootcamper skips ... default" spanning a clause.
    "if-skips-then-default": re.compile(
        r"if\s+the\s+bootcamper\s+skips.{0,80}default", re.IGNORECASE
    ),
    # "not a gate ... skip" — treating a 👉 step as freely skippable.
    "not-a-gate-skip": re.compile(
        r"not\s+a\s+gate.{0,60}(?:skip|can\s+skip)", re.IGNORECASE
    ),
}

# Prohibition markers: when a matched line contains one of these, the idiom is
# being FORBIDDEN, not authorized, so it is not a violation.
_PROHIBITION_MARKERS: tuple[str, ...] = (
    "do not",
    "don't",
    "never",
    "must not",
    "shall not",
    "cannot",
    "can't",
    "forbidden",
    "assumed_answer",
    "no silent default",
    "not authorize",
    "prohibited",
    "is forbidden",
)

# The single allowlisted load-time preference fallback in verbosity-control.md.
# It is a *stored-preference-absent-at-load* fallback (the `verbosity` key is
# absent), NOT the resolution of an outstanding 👉 question, and is explicitly
# annotated as such in the file.
_ALLOWLIST_FILE: str = "verbosity-control.md"
_ALLOWLIST_MARKER: str = "If the key does not exist"


def _steering_markdown_files() -> list[Path]:
    """Return every top-level ``*.md`` steering file, sorted by name.

    Returns:
        Sorted list of steering Markdown file paths.
    """
    return sorted(_STEERING_DIR.glob("*.md"))


def _line_is_prohibition(line: str) -> bool:
    """Return True if *line* forbids (rather than authorizes) the idiom.

    Args:
        line: The matched source line.

    Returns:
        True when the line contains any prohibition marker.
    """
    low = line.lower()
    return any(marker in low for marker in _PROHIBITION_MARKERS)


def _line_is_allowlisted(filename: str, line: str) -> bool:
    """Return True for the one allowlisted load-time fallback line.

    Args:
        filename: The steering file's base name.
        line: The matched source line.

    Returns:
        True only for the ``verbosity-control.md`` load-time fallback line.
    """
    return filename == _ALLOWLIST_FILE and _ALLOWLIST_MARKER in line


def sweep_silent_default_violations(
    *, apply_allowlist: bool = True
) -> list[tuple[str, int, str, str]]:
    """Scan the steering corpus for un-allowlisted silent-default authorizations.

    A line is a violation when it matches a silent-default pattern, is NOT a
    prohibition, and (when *apply_allowlist* is True) is NOT the allowlisted
    load-time fallback.

    Args:
        apply_allowlist: When True, exclude the allowlisted load-time fallback
            line in ``verbosity-control.md``. When False, the allowlisted line
            is reported as a violation (used to prove the pattern is live).

    Returns:
        A list of ``(filename, line_number, pattern_label, line_text)`` tuples.
    """
    violations: list[tuple[str, int, str, str]] = []
    for md_path in _steering_markdown_files():
        filename = md_path.name
        for lineno, line in enumerate(
            md_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            for label, pattern in _SILENT_DEFAULT_PATTERNS.items():
                if not pattern.search(line):
                    continue
                if _line_is_allowlisted(filename, line):
                    if apply_allowlist:
                        continue
                    violations.append((filename, lineno, label, line.strip()))
                    continue
                if _line_is_prohibition(line):
                    continue
                violations.append((filename, lineno, label, line.strip()))
    return violations


# ---------------------------------------------------------------------------
# Hypothesis strategies (st_-prefixed per python-conventions)
# ---------------------------------------------------------------------------


def st_steering_file() -> st.SearchStrategy[Path]:
    """Draw a real steering ``*.md`` file path from the shipped corpus."""
    return st.sampled_from(_steering_markdown_files())


def st_silent_default_label() -> st.SearchStrategy[str]:
    """Draw a silent-default pattern label."""
    return st.sampled_from(sorted(_SILENT_DEFAULT_PATTERNS))


# ---------------------------------------------------------------------------
# Group 1 — the normative Answer_Required_Rule is present and referenced
# ---------------------------------------------------------------------------


class TestAnswerRequiredRulePresence:
    """conversation-protocol.md states the Answer_Required_Rule; the two rule
    files reference it.

    **Validates: Requirements 6.3**
    """

    def test_conversation_protocol_has_rule_heading(self) -> None:
        """conversation-protocol.md contains the Answer_Required_Rule heading."""
        text = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
        assert "## The Answer_Required_Rule" in text, (
            "conversation-protocol.md must define the Answer_Required_Rule under "
            "its own heading"
        )

    def test_conversation_protocol_states_real_answer_requirement(self) -> None:
        """The rule requires a Real_Answer before advancing past a 👉 question."""
        text = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
        assert (
            f"Every {_POINTER} question requires a Real_Answer before the flow "
            "advances past it." in text
        ), "the normative Real_Answer requirement must be stated verbatim"

    def test_conversation_protocol_defines_the_three_terms(self) -> None:
        """Question, Real_Answer, and Assumed_Answer are all defined."""
        text = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
        for term in ("*Question*", "*Real_Answer*", "*Assumed_Answer*"):
            assert term in text, f"the rule must define {term}"

    def test_conversation_protocol_forbids_assumed_answer(self) -> None:
        """The rule forbids supplying an Assumed_Answer / silent default."""
        text = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
        assert "Never supply an Assumed_Answer." in text
        assert "silent default" in text

    def test_conversation_protocol_states_only_two_exits(self) -> None:
        """The rule states the only two exits (Real_Answer or stays outstanding)."""
        text = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
        assert "Only two exits." in text, "the two-exits clause must be present"
        assert (
            f"A {_POINTER} question has exactly two exits: (1) a Real_Answer, or "
            "(2) the question stays outstanding." in text
        )
        # The outstanding path is anchored to the pending-question marker.
        assert "config/.question_pending" in text

    def test_conversation_protocol_frames_optionality_as_explicit_choice(self) -> None:
        """Optionality is expressed as an Explicit_Default_Choice, not silence."""
        text = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
        assert "Optionality is an Explicit_Default_Choice." in text
        assert "Explicit_Default_Choice" in text

    def test_conversation_protocol_names_the_referencing_files(self) -> None:
        """The rule states it is referenced from the two rule files."""
        text = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
        assert "agent-behavior-rules.md" in text
        assert "agent-instructions.md" in text

    def test_agent_behavior_rules_references_the_rule(self) -> None:
        """agent-behavior-rules.md references the Answer_Required_Rule."""
        text = _AGENT_BEHAVIOR_RULES.read_text(encoding="utf-8")
        assert "Answer_Required_Rule (see `conversation-protocol.md`)" in text, (
            "agent-behavior-rules.md must reference the Answer_Required_Rule and "
            "point back to conversation-protocol.md"
        )
        # The reference carries the normative substance, not just a pointer.
        assert "Real_Answer" in text
        assert "Assumed_Answer" in text

    def test_agent_instructions_references_the_rule(self) -> None:
        """agent-instructions.md references the Answer_Required_Rule."""
        text = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        assert "**Answer_Required_Rule.**" in text, (
            "agent-instructions.md must carry the Answer_Required_Rule reference"
        )
        assert (
            "single normative rule defined in `conversation-protocol.md`" in text
        ), "the reference must point back to the canonical definition"


# ---------------------------------------------------------------------------
# Group 2 — corpus sweep: no un-allowlisted silent-default authorizations
# ---------------------------------------------------------------------------


class TestCorpusSweepNoSilentDefault:
    """No steering file authorizes advancing an unanswered 👉 question, save the
    one allowlisted load-time fallback.

    **Validates: Requirements 6.3**
    """

    def test_no_unallowlisted_silent_default_across_corpus(self) -> None:
        """The whole steering corpus has zero un-allowlisted silent defaults."""
        violations = sweep_silent_default_violations(apply_allowlist=True)
        assert violations == [], (
            "steering files must not authorize advancing an unanswered 👉 "
            "question via a silent default (only the annotated load-time "
            f"fallback in {_ALLOWLIST_FILE} is permitted); found: {violations}"
        )

    def test_removed_skip_without_answering_idiom_is_absent(self) -> None:
        """The removed 'skips without answering' silent-default trigger is gone."""
        pattern = _SILENT_DEFAULT_PATTERNS["skip-without-answering"]
        offenders = [
            md.name
            for md in _steering_markdown_files()
            if pattern.search(md.read_text(encoding="utf-8"))
        ]
        assert offenders == [], (
            "the removed verbosity silent-default trigger ('skips without "
            f"answering') must not reappear in the corpus; found in: {offenders}"
        )

    def test_sweep_detects_loadtime_fallback_without_allowlist(self) -> None:
        """Without the allowlist, the sweep flags exactly the load-time fallback.

        This proves the sweep is live: the same pattern that passes the corpus
        today would fire on a re-introduced silent default. Removing the
        allowlist must surface the single ``verbosity-control.md`` load-time
        fallback line and nothing else.
        """
        violations = sweep_silent_default_violations(apply_allowlist=False)
        assert len(violations) == 1, (
            "without the allowlist the sweep must flag exactly the one load-time "
            f"fallback; found: {violations}"
        )
        filename, _lineno, label, _line = violations[0]
        assert filename == _ALLOWLIST_FILE
        assert label == "apply-preset-as-default"

    def test_allowlisted_loadtime_fallback_is_annotated(self) -> None:
        """The allowlisted fallback is annotated as a load-time (not question) path."""
        text = _VERBOSITY_CONTROL.read_text(encoding="utf-8")
        assert _ALLOWLIST_MARKER in text, (
            "the load-time fallback line must exist so the allowlist has a real "
            "target"
        )
        # It is explicitly framed as a load-time fallback, not an answer path.
        assert "not an unanswered-question path" in text.lower() or (
            "not** the resolution of an outstanding" in text
        )

    @given(md_path=st_steering_file())
    def test_property_sampled_file_has_no_unallowlisted_silent_default(
        self, md_path: Path
    ) -> None:
        """For any sampled steering file, no line is an un-allowlisted violation.

        **Validates: Requirements 6.3**
        """
        filename = md_path.name
        for line in md_path.read_text(encoding="utf-8").splitlines():
            for pattern in _SILENT_DEFAULT_PATTERNS.values():
                if not pattern.search(line):
                    continue
                if _line_is_allowlisted(filename, line):
                    continue
                assert _line_is_prohibition(line), (
                    f"{filename}: line authorizes a silent default for an "
                    f"unanswered 👉 question: {line.strip()!r}"
                )


# ---------------------------------------------------------------------------
# Group 3 — the write-policy-gate CHECK 5 answer-required enforcement
# ---------------------------------------------------------------------------


def _write_policy_gate_prompt() -> str:
    """Return the ``action.prompt`` of the write-policy-gate v1 hook entry.

    Returns:
        The gate prompt text.
    """
    data = json.loads(_WRITE_POLICY_GATE.read_text(encoding="utf-8"))
    return data["hooks"][0]["action"]["prompt"]


class TestWritePolicyGateCheck5:
    """write-policy-gate.json carries CHECK 5, and the registry mirror embeds it.

    **Validates: Requirements 6.3**
    """

    def test_prompt_has_check5_header(self) -> None:
        """The prompt contains the CHECK 5 answer-required section header."""
        prompt = _write_policy_gate_prompt()
        assert (
            "CHECK 5: ANSWER-REQUIRED - NO SILENT COMPLETION OF A "
            "QUESTION-OWNING STEP" in prompt
        ), "write-policy-gate.json must define the CHECK 5 answer-required check"

    def test_prompt_check5_has_distinctive_phrases(self) -> None:
        """CHECK 5 carries its distinctive answer-required corrective phrasing."""
        prompt = _write_policy_gate_prompt()
        assert "NO SILENT COMPLETION" in prompt
        assert "ANSWER REQUIRED - QUESTION-OWNING STEP NOT ANSWERED" in prompt
        assert "Real_Answer" in prompt

    def test_prompt_check5_lists_question_owning_fields(self) -> None:
        """CHECK 5 enumerates the question-owning fields it guards."""
        prompt = _write_policy_gate_prompt()
        for field in ("'verbosity'", "'track'", "'mapping_verbosity'"):
            assert field in prompt, f"CHECK 5 must list the {field} field"
        assert "comprehension-check completion marker" in prompt

    def test_prompt_header_reflects_five_checks(self) -> None:
        """The gate header advertises five checks in one pass."""
        prompt = _write_policy_gate_prompt()
        assert "Five checks in one pass" in prompt

    def test_registry_mirror_embeds_check5(self) -> None:
        """hook-registry-critical.md mirrors the CHECK 5 text."""
        text = _HOOK_REGISTRY_CRITICAL.read_text(encoding="utf-8")
        assert (
            "CHECK 5: ANSWER-REQUIRED - NO SILENT COMPLETION OF A "
            "QUESTION-OWNING STEP" in text
        ), "the hook-registry-critical.md mirror must embed CHECK 5"
        assert "Five checks in one pass" in text


# ---------------------------------------------------------------------------
# Group 4 — cross-spec consistency (Requirements 5.1, 5.2)
# ---------------------------------------------------------------------------
# These assertions encode the key invariants that must hold between the new
# Answer_Required_Rule and the landed prior specs it interacts with:
#   * self-answering-prevention-v2  — the rule GENERALIZES "no self-answering"
#     (fabrication) to also forbid silent defaults; it must never weaken it.
#   * mandatory-gate-enforcement    — a 👉 step carries ⛔-gate precedence and
#     rejects the same prohibited justifications; an explicit bootcamper
#     decline is a Real_Answer but never re-opens the agent's ability to
#     self-initiate a ⛔ skip.
#   * eula-answer-skipped / agent-skips-git-question / skip-reflection-questions
#     are prior "don't skip an answer" fixes; the single-ask guarantee
#     (a recorded Real_Answer is not re-asked and is never resolved by an
#     Assumed_Answer) must stay consistent with them.
# If a future edit re-introduces a contradiction (drops the self-answering tie,
# weakens the ⛔ no-self-skip guarantee, or lets a recorded answer be resolved by
# an Assumed_Answer), one of these assertions fails.


def _answer_required_rule_section() -> str:
    """Return the text of the ``## The Answer_Required_Rule`` section only.

    Scoping the tie/consistency assertions to the rule's own section makes them
    meaningful: a regression that strips the cross-spec tie *from the rule*
    fails even if the phrase survives elsewhere in the file.

    Returns:
        The section text from its ``##`` heading up to the next ``##`` heading.
    """
    text = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
    lines = text.splitlines()
    start = next(
        i for i, line in enumerate(lines) if line.strip() == "## The Answer_Required_Rule"
    )
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    return "\n".join(lines[start:end])


class TestCrossSpecConsistencySelfAnswering:
    """Req 5.1 — the rule generalizes (never weakens) self-answering-prevention.

    **Validates: Requirements 5.1**
    """

    def test_rule_ties_to_self_answering_prevention(self) -> None:
        """The rule explicitly generalizes the no-self-answering stance."""
        section = _answer_required_rule_section()
        assert "generalizes the existing no-self-answering stance" in section, (
            "the Answer_Required_Rule must state it GENERALIZES no-self-answering "
            "(so it cannot be read as replacing/weakening it)"
        )
        assert "`self-answering-prevention`" in section, (
            "the rule must name the self-answering-prevention rules it builds on"
        )

    def test_rule_forbids_fabrication_and_silent_default(self) -> None:
        """The generalization keeps forbidding fabrication AND adds silent defaults."""
        section = _answer_required_rule_section()
        assert "Never supply an Assumed_Answer." in section
        # Fabrication (the self-answering-prevention concern) stays forbidden ...
        assert "fabricate a choice" in section
        # ... and the new dimension (silent default) is added on top.
        assert "silent default" in section

    def test_self_answering_example_still_forbids_answering_own_question(self) -> None:
        """The Self-Answering (WRONG) example is intact — no wording permits it."""
        text = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
        assert "### Self-Answering (WRONG)" in text, (
            "the Self-Answering (WRONG) counter-example must remain — the new "
            "rule reinforces it, never removes it"
        )
        assert "never answer it yourself" in text


class TestCrossSpecConsistencyMandatoryGate:
    """Req 5.1 — a 👉 step carries ⛔-gate precedence and the ⛔ no-self-skip
    guarantee is not re-opened by "explicit decline is a Real_Answer".

    **Validates: Requirements 5.1**
    """

    def test_pointer_step_has_gate_precedence(self) -> None:
        """A 👉 numbered step is bound to ⛔ mandatory-gate precedence."""
        text = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
        assert "the same absolute precedence as ⛔ mandatory gates" in text
        assert "Violation of this rule is equivalent to a ⛔ mandatory gate violation." in text

    def test_pointer_step_rejects_same_prohibited_justifications(self) -> None:
        """The 👉-step boundary rejects the gate spec's prohibited justifications."""
        text = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
        # mandatory-gate-enforcement forbids skipping for context budget, session
        # length, and perceived redundancy — the 👉-step boundary names the same.
        for justification in ("context budget", "session length", "redundancy"):
            assert justification in text, (
                f"the 👉-step boundary must reject the '{justification}' "
                "justification, matching mandatory-gate-enforcement"
            )

    def test_explicit_decline_does_not_reopen_agent_self_skip_of_gate(self) -> None:
        """An explicit decline (a Real_Answer) never lets the agent skip a ⛔ gate.

        The Answer_Required_Rule treats an explicit decline/skip as a Real_Answer,
        but the skip-step protocol must still forbid the agent self-initiating a
        ⛔ skip and still refuse a bootcamper's ⛔ skip — otherwise the new rule
        would contradict mandatory-gate-enforcement.
        """
        protocol = _SKIP_STEP_PROTOCOL.read_text(encoding="utf-8")
        assert "Mandatory gates (⛔) cannot be skipped." in protocol
        assert (
            "The agent can NEVER self-initiate a skip of a ⛔ mandatory gate step."
            in protocol
        )


class TestCrossSpecConsistencySingleAsk:
    """Req 5.2 — consistency with the single-ask guarantee: a recorded
    Real_Answer is not re-asked and is never resolved by an Assumed_Answer.

    **Validates: Requirements 5.2**
    """

    def test_rule_two_exits_never_assumed(self) -> None:
        """An outstanding question is re-presented, never closed by an Assumed_Answer."""
        section = _answer_required_rule_section()
        assert "Only two exits." in section
        assert "config/.question_pending" in section, (
            "the outstanding-question exit must anchor to the pending marker so a "
            "later turn re-presents it"
        )
        assert "never resolved by an Assumed_Answer" in section

    def test_recorded_real_answer_satisfies_completion(self) -> None:
        """A recorded Real_Answer (incl. mark-answered) completes the step as-is.

        The write-policy-gate CHECK 5 accepts a recorded Real_Answer / ledger
        ``mark-answered`` signal for a question-owning step and persists ONLY the
        bootcamper-selected value — so a question that already has a recorded
        answer is completed with that answer, never re-defaulted by the agent.
        """
        prompt = _write_policy_gate_prompt()
        assert (
            "A Question_Ledger 'mark-answered' signal for that step, if present, "
            "also counts as a recorded Real_Answer." in prompt
        )
        assert (
            "NOT a value the agent chose or silently defaulted on the "
            "bootcamper's behalf" in prompt
        )

    def test_already_answered_field_is_not_re_asked(self) -> None:
        """Session resume does not re-ask fields that already have a Real_Answer.

        This is the single-ask guarantee's "not re-asked" half; it coexists with
        the Answer_Required_Rule (which only re-presents *outstanding* questions),
        so the two rules are complementary rather than contradictory.
        """
        resume = _SESSION_RESUME.read_text(encoding="utf-8")
        assert "do not re-ask for fields that are already present" in resume
