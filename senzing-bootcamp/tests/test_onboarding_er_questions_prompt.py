"""Steering-content tests for the onboarding-er-questions-prompt feature.

Validates the seven correctness properties defined in
``.kiro/specs/onboarding-er-questions-prompt/{requirements,design}.md`` against
the steering file
(``senzing-bootcamp/steering/entity-resolution-intro.md``) after the
Exploration_Gate's closing calls-to-action were reordered so the rendered
closing 👉 is the Open_Questions_Prompt ("Do you have any questions about
Entity Resolution?") and the Illustration_Offer is deferred to a subsequent
(Phase B) turn.

These are example (not property) tests: the implementation surface is a single
fixed steering markdown file, so there is no input space to randomize over and
Hypothesis-style property-based testing would add noise without coverage. This
matches the rationale documented in the design's "PBT applicability" note and
in the peer suites ``test_er_intro_illustration.py`` and
``test_entity_resolution_intro_structure.py``. The 👉 leading-question count
reuses the canonical, deterministic counting rule from
``senzing-bootcamp/scripts/count_leading_questions.py`` (imported via the
``sys.path`` shim) rather than re-implementing it here.

Properties covered (design.md §Correctness Properties):

- P1 / Req 1.1, 1.2, 1.3: the closing call-to-action is the Open_Questions_Prompt
  only (exactly one non-compound 👉; Illustration_Offer is not a rendered 👉).
- P2 / Req 1.5, 1.6, 3.1: the open prompt precedes and gates the illustration
  offer.
- P3 / Req 2.1, 2.2: gate wait semantics are preserved (🛑 STOP follows the
  open prompt; no fabricate/proceed).
- P4 / Req 2.3, 2.4, 2.5: MCP-first answering and re-presentation are preserved.
- P5 / Req 2.6, 3.6: the ER_Concepts_Banner is shown once per Preface run.
- P6 / Req 3.2, 3.3, 3.4, 3.5, 3.7: Illustration_Offer regression invariants hold.
- P7 / Req 4.1, 4.2, 4.3, 4.4: the illustration remains a conceptual preview.
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts importable so we can reuse the canonical
# 👉 leading-question counting rule (scripts aren't packages).
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from count_leading_questions import (  # noqa: E402
    HARD_GATE_MARKER,
    POINTER_INDICATOR,
    STOP_MARKER,
    count_leading_questions,
    is_leading_question_line,
)

# ---------------------------------------------------------------------------
# Module-level path constants (resolved relative to this test file).
# ---------------------------------------------------------------------------
#: Repository root — parent of the ``senzing-bootcamp/`` power directory.
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

#: The entity-resolution introduction steering file under test.
TARGET_FILE: Path = (
    REPO_ROOT / "senzing-bootcamp" / "steering" / "entity-resolution-intro.md"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load() -> str:
    """Read the steering file's full text.

    Returns:
        The contents of ``entity-resolution-intro.md`` as a UTF-8 string.
    """
    return TARGET_FILE.read_text(encoding="utf-8")


def _norm(text: str) -> str:
    """Collapse whitespace and lowercase for whitespace-tolerant matching.

    Steering-file phrasing frequently wraps across lines, so assertions on
    multi-word phrases must not depend on where a line break falls.

    Args:
        text: The raw text to normalize.

    Returns:
        ``text`` lowercased with every run of whitespace collapsed to a single
        space.
    """
    return " ".join(text.split()).lower()


def _pointer_line(text: str) -> str:
    """Return the single 👉 leading-question line (raw), or raise if not exactly one.

    Uses the canonical :func:`is_leading_question_line` rule so the definition
    of "a 👉 leading question" matches the rest of the bootcamp tooling.

    Args:
        text: The full steering file text.

    Returns:
        The raw line whose first content is the 👉 pointer.

    Raises:
        AssertionError: If the file does not contain exactly one such line.
    """
    lines = [line for line in text.splitlines() if is_leading_question_line(line)]
    assert len(lines) == 1, (
        f"Expected exactly one 👉 leading-question line in {TARGET_FILE.name}; "
        f"found {len(lines)}: {lines!r}"
    )
    return lines[0]


def _directive_block(text: str, marker: str) -> str:
    """Return the AGENT INSTRUCTION comment block that begins at ``marker``.

    Slices from the first occurrence of ``marker`` to the end of the enclosing
    HTML comment (``-->``) so content assertions are scoped to a single
    directive rather than accidentally satisfied by unrelated prose or a
    neighbouring directive.

    Args:
        text: The full steering file text.
        marker: A distinctive substring at the start of the directive (for
            example ``"ILLUSTRATION_OFFER (Req"``).

    Returns:
        The directive block text (``marker`` inclusive, closing ``-->``
        exclusive).

    Raises:
        AssertionError: If the marker or its closing ``-->`` cannot be located.
    """
    start = text.find(marker)
    assert start != -1, (
        f"Expected a directive beginning with {marker!r} in {TARGET_FILE.name}; "
        "none found."
    )
    end = text.find("-->", start)
    assert end != -1, (
        f"Expected the {marker!r} directive to be a closed HTML comment "
        f"(missing '-->') in {TARGET_FILE.name}."
    )
    return text[start:end]


# ---------------------------------------------------------------------------
# P1 / Req 1.1, 1.2, 1.3 — closing call-to-action is the Open_Questions_Prompt only
# ---------------------------------------------------------------------------


class TestClosingCallToActionIsOpenQuestionsPrompt:
    """The single rendered 👉 is the Open_Questions_Prompt, and it alone.

    Validates: Requirements 1.1, 1.2, 1.3 (Property 1).
    """

    def test_exactly_one_rendered_leading_question(self) -> None:
        """Exactly one 👉 leading question is rendered (One_Question_Rule; Req 1.1, 1.3).

        Reuses the canonical counting rule, which excludes 👉 that appear
        mid-line inside AGENT INSTRUCTION comments — only the rendered closing
        👉 counts.
        """
        count = count_leading_questions(_load())
        assert count == 1, (
            f"Expected exactly one rendered 👉 leading question in "
            f"{TARGET_FILE.name} per the One Question Rule (Req 1.1, 1.3); "
            f"found {count}."
        )

    def test_rendered_prompt_is_the_open_questions_prompt(self) -> None:
        """The single rendered 👉 is the Open_Questions_Prompt (Req 1.1, 1.2)."""
        prompt = _norm(_pointer_line(_load()))
        assert "do you have any questions about entity resolution?" in prompt, (
            "Expected the single rendered 👉 to be the Open_Questions_Prompt "
            "('Do you have any questions about Entity Resolution?') in "
            f"{TARGET_FILE.name} (Req 1.1, 1.2); got: {prompt!r}"
        )

    def test_rendered_prompt_is_non_compound(self) -> None:
        """The rendered prompt poses a single, non-compound question (Req 1.3).

        A non-compound prompt carries exactly one question mark; a compound
        prompt would chain two asks / two '?'.
        """
        prompt = _pointer_line(_load())
        question_marks = prompt.count("?")
        assert question_marks == 1, (
            "Expected the Open_Questions_Prompt to be a single non-compound "
            f"question (exactly one '?') in {TARGET_FILE.name} (Req 1.3); "
            f"found {question_marks} in: {prompt!r}"
        )

    def test_illustration_offer_is_not_a_rendered_leading_question(self) -> None:
        """The Illustration_Offer text is NOT the rendered closing 👉 (Req 1.2).

        The two-record match/non-match offer wording may appear only inside the
        ILLUSTRATION_OFFER agent-instruction comment, never as the rendered
        leading question that ends the gate turn.
        """
        prompt = _norm(_pointer_line(_load()))
        assert "two-record example of a match and a non-match" not in prompt, (
            "Expected the Illustration_Offer wording NOT to be the rendered "
            f"closing 👉 in {TARGET_FILE.name} (Req 1.2); got: {prompt!r}"
        )


# ---------------------------------------------------------------------------
# P2 / Req 1.5, 1.6, 3.1 — open prompt precedes and gates the illustration offer
# ---------------------------------------------------------------------------


class TestOpenPromptPrecedesAndGatesOffer:
    """The Open_Questions_Prompt is ordered before, and gates, the offer.

    Validates: Requirements 1.5, 1.6, 3.1 (Property 2).
    """

    def test_open_prompt_directive_precedes_illustration_offer_directive(self) -> None:
        """The OPEN_QUESTIONS_PROMPT directive precedes the ILLUSTRATION_OFFER one (Req 3.1)."""
        text = _load()
        open_index = text.find("OPEN_QUESTIONS_PROMPT (Req")
        offer_index = text.find("ILLUSTRATION_OFFER (Req")
        assert open_index != -1, (
            "Expected an OPEN_QUESTIONS_PROMPT directive in "
            f"{TARGET_FILE.name} (Req 1.5, 3.1)."
        )
        assert offer_index != -1, (
            "Expected an ILLUSTRATION_OFFER directive in "
            f"{TARGET_FILE.name} (Req 3.1)."
        )
        assert open_index < offer_index, (
            "Expected the OPEN_QUESTIONS_PROMPT directive to precede the "
            f"ILLUSTRATION_OFFER directive in {TARGET_FILE.name} (Req 3.1); "
            f"got open={open_index}, offer={offer_index}."
        )

    def test_offer_is_gated_on_open_prompt_being_handled(self) -> None:
        """The offer is presented only after the open prompt is handled (Req 1.5, 3.1).

        The ILLUSTRATION_OFFER directive must state it fires only after the
        bootcamper signalled readiness / "no questions" (the open prompt being
        handled), on a later turn.
        """
        block = _norm(_directive_block(_load(), "ILLUSTRATION_OFFER (Req"))
        assert "only after the open_questions_prompt has been handled" in block, (
            "Expected the ILLUSTRATION_OFFER directive to gate presentation on "
            "the Open_Questions_Prompt being handled in "
            f"{TARGET_FILE.name} (Req 3.1)."
        )
        assert "readiness" in block and "no questions" in block, (
            "Expected the ILLUSTRATION_OFFER directive to condition on a "
            "readiness / 'no questions' signal in "
            f"{TARGET_FILE.name} (Req 1.5, 3.1)."
        )

    def test_asked_question_answered_before_offer(self) -> None:
        """Any asked question is answered before the offer is presented (Req 1.6).

        The OPEN_QUESTIONS_PROMPT directive must state that a question the
        bootcamper asks is answered before the Illustration_Offer is presented.
        """
        block = _norm(_directive_block(_load(), "OPEN_QUESTIONS_PROMPT (Req"))
        assert "answered before the illustration_offer is" in block, (
            "Expected the OPEN_QUESTIONS_PROMPT directive to require answering "
            "any asked question BEFORE presenting the ILLUSTRATION_OFFER in "
            f"{TARGET_FILE.name} (Req 1.6)."
        )
        assert "next turn" in block, (
            "Expected the OPEN_QUESTIONS_PROMPT directive to defer the "
            f"ILLUSTRATION_OFFER to the NEXT turn in {TARGET_FILE.name} "
            "(Req 1.5)."
        )


# ---------------------------------------------------------------------------
# P3 / Req 2.1, 2.2 — gate wait semantics preserved
# ---------------------------------------------------------------------------


class TestGateWaitSemanticsPreserved:
    """A 🛑 STOP follows the open prompt and no fabricate/proceed is allowed.

    Validates: Requirements 2.1, 2.2 (Property 3).
    """

    def test_stop_marker_follows_the_open_questions_prompt(self) -> None:
        """A 🛑 STOP line follows the Open_Questions_Prompt 👉 (Req 2.1).

        The rendered closing 👉 (the Open_Questions_Prompt) must be followed by
        the 🛑 STOP marker so the agent still waits for real input.
        """
        text = _load()
        prompt_index = text.find(
            f"{POINTER_INDICATOR} **Do you have any questions about Entity Resolution?**"
        )
        assert prompt_index != -1, (
            "Expected the Open_Questions_Prompt 👉 line in "
            f"{TARGET_FILE.name} (Req 2.1)."
        )
        stop_index = text.find(f"{STOP_MARKER} **STOP", prompt_index)
        assert stop_index != -1, (
            "Expected a 🛑 STOP marker after the Open_Questions_Prompt in "
            f"{TARGET_FILE.name} (Req 2.1); the gate must still wait for input."
        )

    def test_directive_forbids_fabricating_or_assuming_a_response(self) -> None:
        """The gate forbids assuming a response and proceeding (Req 2.2).

        The rendered 🛑 STOP instruction must forbid proceeding and forbid
        assuming a response, and require waiting for the bootcamper's real
        input.
        """
        text = _norm(_load())
        assert "do not proceed." in text, (
            "Expected the 🛑 STOP line to forbid proceeding past the gate in "
            f"{TARGET_FILE.name} (Req 2.2)."
        )
        assert "do not assume a response." in text, (
            "Expected the 🛑 STOP line to forbid assuming a bootcamper response "
            f"in {TARGET_FILE.name} (Req 2.2)."
        )
        assert "wait for the bootcamper's real input" in text, (
            "Expected the 🛑 STOP line to require waiting for the bootcamper's "
            f"real input in {TARGET_FILE.name} (Req 2.2)."
        )


# ---------------------------------------------------------------------------
# P4 / Req 2.3, 2.4, 2.5 — MCP-first answering and re-presentation preserved
# ---------------------------------------------------------------------------


class TestMcpFirstAnsweringPreserved:
    """The gate answers follow-ups MCP-first and re-presents the gate.

    Validates: Requirements 2.3, 2.4, 2.5 (Property 4).
    """

    def _gate_directive(self) -> str:
        """Return the normalized gate wait/answer directive block."""
        return _norm(_directive_block(_load(), "Mandatory gate — the agent MUST"))

    def test_follow_up_answered_via_search_docs(self) -> None:
        """Follow-up questions are answered MCP-first via ``search_docs`` (Req 2.3)."""
        block = self._gate_directive()
        assert "search_docs" in block, (
            "Expected the gate directive to answer follow-ups via 'search_docs' "
            f"(Senzing MCP) in {TARGET_FILE.name} (Req 2.3)."
        )
        assert "follow-up question" in block, (
            "Expected the gate directive to name the follow-up question case in "
            f"{TARGET_FILE.name} (Req 2.3)."
        )

    def test_ambiguous_response_handling(self) -> None:
        """Ambiguous responses are treated as follow-up questions (Req 2.4)."""
        block = self._gate_directive()
        assert "ambiguous response" in block, (
            "Expected the gate directive to handle an 'ambiguous response' in "
            f"{TARGET_FILE.name} (Req 2.4)."
        )

    def test_search_docs_failure_handling(self) -> None:
        """A ``search_docs`` no-results/failure path is defined (Req 2.5)."""
        block = self._gate_directive()
        assert "no relevant results or fails" in block, (
            "Expected the gate directive to handle 'search_docs returns no "
            f"relevant results or fails' in {TARGET_FILE.name} (Req 2.5)."
        )
        assert "suggest a rephrase" in block, (
            "Expected the gate directive to suggest a rephrase on MCP failure "
            f"in {TARGET_FILE.name} (Req 2.5)."
        )

    def test_gate_is_re_presented(self) -> None:
        """Each answer/failure path re-presents the gate (Req 2.3, 2.4, 2.5)."""
        block = self._gate_directive()
        assert "re-present" in block, (
            "Expected the gate directive to 're-present' the gate after "
            f"answering / on failure in {TARGET_FILE.name} (Req 2.3-2.5)."
        )


# ---------------------------------------------------------------------------
# P5 / Req 2.6, 3.6 — concepts banner shown once per Preface run
# ---------------------------------------------------------------------------


class TestConceptsBannerShownOnce:
    """The ER_Concepts_Banner is shown once and never re-displayed on re-present.

    Validates: Requirements 2.6, 3.6 (Property 5).
    """

    def test_once_only_banner_directive_preserved(self) -> None:
        """The banner directive keeps its once-only rule (Req 2.6)."""
        text = _norm(_load())
        assert "show it once per preface run" in text, (
            "Expected the ER_Concepts_Banner directive to keep its once-per-"
            f"Preface-run rule in {TARGET_FILE.name} (Req 2.6)."
        )

    def test_banner_not_re_displayed_on_re_presentation(self) -> None:
        """Re-presenting the gate never re-displays the banner (Req 2.6, 3.6)."""
        text = _norm(_load())
        assert "do not re-display when re-presenting the gate" in text, (
            "Expected the ER_Concepts_Banner directive to forbid re-displaying "
            f"the banner when re-presenting the gate in {TARGET_FILE.name} "
            "(Req 2.6, 3.6)."
        )


# ---------------------------------------------------------------------------
# P6 / Req 3.2, 3.3, 3.4, 3.5, 3.7 — Illustration_Offer regression invariants
# ---------------------------------------------------------------------------


class TestIllustrationOfferInvariants:
    """The ILLUSTRATION_OFFER directive keeps its gate-safe invariants.

    Validates: Requirements 3.2, 3.3, 3.4, 3.5, 3.7 (Property 6).
    """

    def _offer_directive(self) -> str:
        """Return the normalized ILLUSTRATION_OFFER directive block."""
        return _norm(_directive_block(_load(), "ILLUSTRATION_OFFER (Req"))

    def test_offer_is_single_and_non_compound_and_verbosity_aware(self) -> None:
        """The offer is the single, non-compound, verbosity-aware 👉 (Req 3.2)."""
        block = self._offer_directive()
        assert "single 👉" in block, (
            "Expected the ILLUSTRATION_OFFER directive to mark the offer 'the "
            f"single 👉' in {TARGET_FILE.name} (Req 3.2)."
        )
        assert "non-compound" in block, (
            "Expected the ILLUSTRATION_OFFER directive to label the offer "
            f"'non-compound' in {TARGET_FILE.name} (Req 3.2)."
        )
        assert "verbosity-aware" in block, (
            "Expected the ILLUSTRATION_OFFER directive to mark the offer "
            f"'verbosity-aware' in {TARGET_FILE.name} (Req 3.2)."
        )

    def test_offer_is_optional(self) -> None:
        """The offer is optional; decline/readiness proceeds past the gate (Req 3.3, 3.4)."""
        block = self._offer_directive()
        assert "optional" in block, (
            "Expected the ILLUSTRATION_OFFER directive to mark the offer "
            f"'optional' in {TARGET_FILE.name} (Req 3.3)."
        )
        assert "proceed past the gate" in block, (
            "Expected the ILLUSTRATION_OFFER directive to proceed past the gate "
            f"on decline/readiness in {TARGET_FILE.name} (Req 3.4)."
        )

    def test_offer_is_ask_once(self) -> None:
        """The offer is ask-once — never re-offered once answered (Req 3.5)."""
        block = self._offer_directive()
        assert "ask-once" in block, (
            "Expected the ILLUSTRATION_OFFER directive to mark the offer "
            f"'ask-once' in {TARGET_FILE.name} (Req 3.5)."
        )
        assert "do not offer it again" in block, (
            "Expected the ILLUSTRATION_OFFER directive to state the offer is not "
            f"offered again once answered in {TARGET_FILE.name} (Req 3.5)."
        )

    def test_offer_has_clarify_once_path(self) -> None:
        """An unrecognized response re-presents the offer once, no proceed (Req 3.7)."""
        block = self._offer_directive()
        assert "unrecognized response" in block, (
            "Expected the ILLUSTRATION_OFFER directive to handle an "
            f"'unrecognized response' in {TARGET_FILE.name} (Req 3.7)."
        )
        assert "re-present" in block and "once" in block, (
            "Expected the ILLUSTRATION_OFFER directive to re-present the offer "
            f"once on an unrecognized response in {TARGET_FILE.name} (Req 3.7)."
        )
        assert "do not proceed past the gate" in block, (
            "Expected the ILLUSTRATION_OFFER directive not to proceed until a "
            f"recognized response is received in {TARGET_FILE.name} (Req 3.7)."
        )


# ---------------------------------------------------------------------------
# P7 / Req 4.1, 4.2, 4.3, 4.4 — the illustration remains a conceptual preview
# ---------------------------------------------------------------------------


class TestIllustrationRemainsConceptualPreview:
    """The ER_ILLUSTRATION directive keeps the illustration a conceptual preview.

    Validates: Requirements 4.1, 4.2, 4.3, 4.4 (Property 7).
    """

    def _illustration_directive(self) -> str:
        """Return the normalized ER_ILLUSTRATION directive block."""
        return _norm(_directive_block(_load(), "ER_ILLUSTRATION (Req"))

    def test_conceptual_only_with_line_limit(self) -> None:
        """The illustration is conceptual-only and capped at ≤25 lines (Req 4.1)."""
        block = self._illustration_directive()
        assert "conceptual teaser only" in block, (
            "Expected the ER_ILLUSTRATION directive to constrain the teaser to "
            f"'conceptual teaser only' in {TARGET_FILE.name} (Req 4.1)."
        )
        assert "no more than 25 lines" in block, (
            "Expected the ER_ILLUSTRATION directive to cap the illustration at "
            f"no more than 25 lines in {TARGET_FILE.name} (Req 4.1)."
        )

    def test_no_graph_and_no_server(self) -> None:
        """The illustration renders no graph and starts no server (Req 4.1, 4.2)."""
        block = self._illustration_directive()
        assert "no sdk, data, code, server, or graph" in block, (
            "Expected the ER_ILLUSTRATION directive to forbid server/graph "
            f"rendering in {TARGET_FILE.name} (Req 4.1, 4.2)."
        )
        assert 'do not reproduce the module 3 "wow" visualization' in block, (
            "Expected the ER_ILLUSTRATION directive to forbid reproducing the "
            f"Module 3 'wow' visualization in {TARGET_FILE.name} (Req 4.2)."
        )

    def test_module_3_forward_reference(self) -> None:
        """The illustration points forward to the Module 3 visualization (Req 4.3)."""
        block = self._illustration_directive()
        assert "preview" in block, (
            "Expected the ER_ILLUSTRATION directive to frame the illustration "
            f"as a 'preview' in {TARGET_FILE.name} (Req 4.3)."
        )
        assert "module 3 visualization" in block, (
            "Expected the ER_ILLUSTRATION directive to point forward to the "
            f"Module 3 visualization on the bootcamper's own data in "
            f"{TARGET_FILE.name} (Req 4.3)."
        )
        assert "their own data" in block, (
            "Expected the ER_ILLUSTRATION directive to reference the "
            f"bootcamper's own data in {TARGET_FILE.name} (Req 4.3)."
        )

    def test_decline_and_redirect_for_full_graph_request(self) -> None:
        """A full-graph request is declined and redirected to Module 3 (Req 4.4).

        If the bootcamper asks for the interactive entity graph / full
        visualization while the illustration is displayed, the directive must
        decline, leave the preview unchanged, and direct them to Module 3.
        """
        block = self._illustration_directive()
        assert "interactive entity graph or full visualization" in block, (
            "Expected the ER_ILLUSTRATION directive to handle a request for the "
            "interactive entity graph / full visualization in "
            f"{TARGET_FILE.name} (Req 4.4)."
        )
        assert "decline to render it" in block, (
            "Expected the ER_ILLUSTRATION directive to decline rendering the "
            f"full graph in {TARGET_FILE.name} (Req 4.4)."
        )
        assert "leave the conceptual preview unchanged" in block, (
            "Expected the ER_ILLUSTRATION directive to leave the conceptual "
            f"preview unchanged in {TARGET_FILE.name} (Req 4.4)."
        )
        assert "direct them to the module 3" in block, (
            "Expected the ER_ILLUSTRATION directive to direct the bootcamper to "
            f"the Module 3 hands-on visualization in {TARGET_FILE.name} "
            "(Req 4.4)."
        )
