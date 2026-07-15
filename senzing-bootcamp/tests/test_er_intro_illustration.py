"""Steering-content tests for the er-intro-interactive-illustration feature.

Validates the correctness properties defined in
``.kiro/specs/er-intro-interactive-illustration/{requirements,design}.md``
against the Target_File
(``senzing-bootcamp/steering/entity-resolution-intro.md``) after Tasks 1-4
added the optional two-record match / non-match illustration.

These are example (not property) tests: there is a single fixed input file,
so Hypothesis-style property-based testing would add noise without coverage —
matching the rationale in the peer suites ``test_entity_resolution_intro_structure.py``
and ``test_preface_banners.py``. The 👉 leading-question count reuses the
canonical, deterministic counting rule from
``senzing-bootcamp/scripts/count_leading_questions.py`` (imported via the
``sys.path`` shim) rather than re-implementing it here.

Properties covered (design.md §Correctness properties / §Testing notes):

- P6 / Req 1.1, 2.3: exactly ONE non-compound 👉 offer, and it is about
  viewing a two-record match / non-match example.
- Req 1.2: the ER_Illustration directs rendering of BOTH a match pair AND a
  non-match / possible-match pair, with reasoning tied to false negative /
  false positive (name variation, address-over-time).
- P4 / Req 1.4: MCP-first sourcing (``find_examples`` / ``search_docs``) with a
  clearly-labeled generic fallback.
- P5 / Req 3.1, 3.2: no server / graph rendering instructions in the
  illustration, and it points forward to the Module 3 visualization.
- P3 / Req 1.3: self-contained — no SDK, database, loaded data, or code
  execution required.
- P2 / Req 2.2: the ⛔ MANDATORY GATE wording and the once-only
  ER_Concepts_Banner behavior are preserved.
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
    """Read the Target_File's full text.

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
        text: The full Target_File text.

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


def _illustration_block(text: str) -> str:
    """Return the ER_ILLUSTRATION agent-instruction block.

    Slices from the ``ER_ILLUSTRATION`` marker to the end of the enclosing
    HTML comment (``-->``) so content assertions are scoped to the illustration
    rather than accidentally satisfied by unrelated prose elsewhere.

    Args:
        text: The full Target_File text.

    Returns:
        The text of the ER_ILLUSTRATION block (marker inclusive, closing
        ``-->`` exclusive).

    Raises:
        AssertionError: If the ER_ILLUSTRATION block cannot be located.
    """
    start = text.find("ER_ILLUSTRATION")
    assert start != -1, (
        f"Expected an ER_ILLUSTRATION agent-instruction block in "
        f"{TARGET_FILE.name}; none found."
    )
    end = text.find("-->", start)
    assert end != -1, (
        "Expected the ER_ILLUSTRATION block to be a closed HTML comment "
        f"(missing '-->') in {TARGET_FILE.name}."
    )
    return text[start:end]


# ---------------------------------------------------------------------------
# P6 / Req 1.1, 2.3 — exactly one non-compound 👉 offer
# ---------------------------------------------------------------------------


class TestIllustrationOffer:
    """The Illustration_Offer is a single, non-compound 👉 about a match/non-match.

    Validates: Requirements 1.1, 2.3 (Property P6).
    """

    def test_exactly_one_leading_question(self) -> None:
        """Exactly one 👉 leading question exists in the file (Req 2.3, P6).

        Reuses the deterministic counting rule, which excludes the 👉 that
        appear mid-line inside the agent-instruction comments — only the
        rendered Illustration_Offer line counts.
        """
        count = count_leading_questions(_load())
        assert count == 1, (
            f"Expected exactly one 👉 leading question (the Illustration_Offer) "
            f"in {TARGET_FILE.name} per the One Question Rule (Req 2.3, P6); "
            f"found {count}."
        )

    def test_offer_is_non_compound(self) -> None:
        """The offer asks a single, non-compound question (Req 2.3, P6).

        A non-compound offer poses one question, so the 👉 line carries exactly
        one question mark (a compound offer would chain two asks / two '?').
        """
        offer = _pointer_line(_load())
        question_marks = offer.count("?")
        assert question_marks == 1, (
            "Expected the Illustration_Offer to be a single non-compound "
            f"question (exactly one '?') in {TARGET_FILE.name} (Req 2.3, P6); "
            f"found {question_marks} in: {offer!r}"
        )

    def test_offer_is_about_two_record_match_and_non_match(self) -> None:
        """The offer proposes viewing a two-record match / non-match example (Req 1.1).

        The 👉 line frames the ER_Illustration as an optional preview of a
        concrete two-record match and non-match pair.
        """
        offer = _norm(_pointer_line(_load()))
        assert "two-record example of a match and a non-match" in offer, (
            "Expected the Illustration_Offer to offer a two-record match / "
            f"non-match example in {TARGET_FILE.name} (Req 1.1); got: {offer!r}"
        )

    def test_offer_instruction_marks_it_single_and_non_compound(self) -> None:
        """The agent instruction labels the offer a single, non-compound 👉 (Req 2.3).

        Guards the ILLUSTRATION_OFFER directive so a future edit cannot drop the
        One-Question framing that keeps the offer gate-safe.
        """
        block = _norm(_load())
        assert "the single 👉".lower() in block, (
            "Expected the ILLUSTRATION_OFFER instruction to describe 'the single "
            f"👉' in {TARGET_FILE.name} (Req 2.3, P6)."
        )
        assert "non-compound" in block, (
            "Expected the ILLUSTRATION_OFFER instruction to label the offer "
            f"'non-compound' in {TARGET_FILE.name} (Req 2.3, P6)."
        )
        assert "optional" in block, (
            "Expected the ILLUSTRATION_OFFER instruction to mark the offer "
            f"'optional' in {TARGET_FILE.name} (Req 2.1, 2.3)."
        )


# ---------------------------------------------------------------------------
# Req 1.2 — a match pair AND a non-match / possible-match pair with reasoning
# ---------------------------------------------------------------------------


class TestIllustrationContent:
    """The ER_Illustration renders both a match and a non-match/possible-match pair.

    Validates: Requirement 1.2 (concrete two-record pairs tied to the intro's
    false-negative / false-positive concepts).
    """

    def test_match_pair_present(self) -> None:
        """A clear MATCH pair is directed in the illustration (Req 1.2)."""
        block = _norm(_illustration_block(_load()))
        assert "- match:" in block, (
            "Expected a MATCH pair bullet in the ER_ILLUSTRATION block of "
            f"{TARGET_FILE.name} (Req 1.2)."
        )

    def test_non_match_or_possible_match_pair_present(self) -> None:
        """A clear NON-MATCH / POSSIBLE MATCH pair is directed (Req 1.2)."""
        block = _norm(_illustration_block(_load()))
        assert "non-match / possible match:" in block, (
            "Expected a NON-MATCH / POSSIBLE MATCH pair bullet in the "
            f"ER_ILLUSTRATION block of {TARGET_FILE.name} (Req 1.2)."
        )

    def test_reasoning_tied_to_false_negative_and_false_positive(self) -> None:
        """Reasoning ties the pairs to false negative and false positive (Req 1.2).

        The match pair's risk is a missed match (false negative); the
        non-match pair's risk is an over-merge (false positive).
        """
        block = _norm(_illustration_block(_load()))
        assert "false negative" in block, (
            "Expected the MATCH pair reasoning to reference a 'false negative' "
            f"in the ER_ILLUSTRATION block of {TARGET_FILE.name} (Req 1.2)."
        )
        assert "false positive" in block, (
            "Expected the NON-MATCH pair reasoning to reference a 'false "
            f"positive' in the ER_ILLUSTRATION block of {TARGET_FILE.name} "
            "(Req 1.2)."
        )

    def test_reasoning_references_name_variation_and_prior_address(self) -> None:
        """The match reasoning ties to name variation + address-over-time (Req 1.2).

        These are the same surface-difference concepts the intro's "why matching
        is hard" section names, so the illustration grounds them concretely.
        """
        block = _norm(_illustration_block(_load()))
        assert "name" in block and "variation" in block, (
            "Expected the illustration reasoning to reference name variation in "
            f"the ER_ILLUSTRATION block of {TARGET_FILE.name} (Req 1.2)."
        )
        assert "prior address" in block, (
            "Expected the illustration reasoning to reference a prior/over-time "
            f"address in the ER_ILLUSTRATION block of {TARGET_FILE.name} "
            "(Req 1.2)."
        )


# ---------------------------------------------------------------------------
# P4 / Req 1.4 — MCP-first sourcing with a clearly-labeled generic fallback
# ---------------------------------------------------------------------------


class TestMcpFirstSourcing:
    """The illustration sources examples MCP-first with a labeled generic fallback.

    Validates: Requirement 1.4 (Property P4).
    """

    def test_references_mcp_example_tools(self) -> None:
        """The illustration prefers ``find_examples`` / ``search_docs`` (Req 1.4)."""
        block = _norm(_illustration_block(_load()))
        assert "find_examples" in block, (
            "Expected MCP-first sourcing via 'find_examples' in the "
            f"ER_ILLUSTRATION block of {TARGET_FILE.name} (Req 1.4, P4)."
        )
        assert "search_docs" in block, (
            "Expected MCP-first sourcing via 'search_docs' in the "
            f"ER_ILLUSTRATION block of {TARGET_FILE.name} (Req 1.4, P4)."
        )

    def test_generic_fallback_is_clearly_labeled(self) -> None:
        """A generic fallback is present and clearly marked as illustrative (Req 1.4).

        When MCP examples are unavailable the agent falls back to a pair that is
        explicitly labeled "illustrative, not Senzing data" so it is never
        mistaken for real MCP-sourced content.
        """
        block = _norm(_illustration_block(_load()))
        assert "generic fallback" in block, (
            "Expected a clearly-labeled generic fallback in the ER_ILLUSTRATION "
            f"block of {TARGET_FILE.name} (Req 1.4, P4)."
        )
        assert "illustrative, not senzing data" in block, (
            "Expected the generic fallback to be labeled 'illustrative, not "
            f"Senzing data' in the ER_ILLUSTRATION block of {TARGET_FILE.name} "
            "(Req 1.4, P4)."
        )


# ---------------------------------------------------------------------------
# P5 / Req 3.1, 3.2 — no server/graph rendering; points forward to Module 3
# ---------------------------------------------------------------------------


class TestNonDuplicationOfModule3:
    """The illustration is a lightweight teaser, not the Module 3 visualization.

    Validates: Requirements 3.1, 3.2 (Property P5).
    """

    def test_no_server_or_graph_rendering(self) -> None:
        """The illustration renders no interactive graph and starts no server (Req 3.1)."""
        block = _norm(_illustration_block(_load()))
        assert "no sdk, data, code, server, or graph" in block, (
            "Expected the ER_ILLUSTRATION block to forbid server/graph rendering "
            f"('no SDK, data, code, server, or graph') in {TARGET_FILE.name} "
            "(Req 3.1, P5)."
        )
        assert 'do not reproduce the module 3 "wow" visualization' in block, (
            "Expected the ER_ILLUSTRATION block to forbid reproducing the "
            f"Module 3 'wow' visualization in {TARGET_FILE.name} (Req 3.1, P5)."
        )

    def test_points_forward_to_module_3(self) -> None:
        """The illustration is framed as a preview pointing to Module 3 (Req 3.2)."""
        block = _norm(_illustration_block(_load()))
        assert "preview" in block, (
            "Expected the ER_ILLUSTRATION block to frame the illustration as a "
            f"'preview' in {TARGET_FILE.name} (Req 3.2, P5)."
        )
        assert "module 3 visualization" in block, (
            "Expected the ER_ILLUSTRATION block to point forward to the "
            f"Module 3 visualization in {TARGET_FILE.name} (Req 3.2, P5)."
        )


# ---------------------------------------------------------------------------
# P3 / Req 1.3 — self-contained (no SDK, database, loaded data, code execution)
# ---------------------------------------------------------------------------


class TestSelfContained:
    """The illustration requires no SDK, database, loaded data, or code execution.

    Validates: Requirement 1.3 (Property P3).
    """

    def test_no_sdk_data_or_code_required(self) -> None:
        """The illustration is conceptual and self-contained (Req 1.3, P3).

        The agent instruction constrains the teaser to require none of: SDK,
        data, or code (the "no SDK, data, code, server, or graph" clause).
        """
        block = _norm(_illustration_block(_load()))
        assert "conceptual teaser only" in block, (
            "Expected the ER_ILLUSTRATION block to constrain the teaser to be "
            f"'conceptual teaser only' in {TARGET_FILE.name} (Req 1.3, P3)."
        )
        for forbidden in ("sdk", "data", "code"):
            assert forbidden in block, (
                f"Expected the ER_ILLUSTRATION self-contained clause to name "
                f"'{forbidden}' as not required in {TARGET_FILE.name} "
                "(Req 1.3, P3)."
            )


# ---------------------------------------------------------------------------
# P2 / Req 2.2 — gate wording + once-only banner preserved
# ---------------------------------------------------------------------------


class TestGatePreservation:
    """The Exploration_Gate wording and once-only banner behavior are preserved.

    Validates: Requirement 2.2 (Property P2).
    """

    def test_mandatory_gate_wording_preserved(self) -> None:
        """The ⛔ MANDATORY GATE heading is preserved (Req 2.2, P2)."""
        text = _load()
        gate_title = f"{HARD_GATE_MARKER} **MANDATORY GATE**"
        assert gate_title in text, (
            "Expected the '⛔ **MANDATORY GATE**' heading to remain in "
            f"{TARGET_FILE.name} (Req 2.2, P2); the Illustration_Offer must not "
            "alter the gate wording."
        )

    def test_stop_marker_follows_the_offer(self) -> None:
        """A 🛑 STOP marker still terminates the gate turn after the offer (Req 2.2).

        The offer ends the gate turn; the 🛑 STOP line must come after the 👉 so
        the agent still waits for real input rather than proceeding.
        """
        text = _load()
        offer_index = text.find(POINTER_INDICATOR + " **Want to see")
        assert offer_index != -1, (
            f"Expected the Illustration_Offer 👉 line in {TARGET_FILE.name}."
        )
        stop_index = text.find(f"{STOP_MARKER} **STOP", offer_index)
        assert stop_index != -1, (
            "Expected a 🛑 STOP marker after the Illustration_Offer in "
            f"{TARGET_FILE.name} (Req 2.2, P2); the gate must still wait for "
            "input."
        )

    def test_once_only_banner_behavior_preserved(self) -> None:
        """The ER_Concepts_Banner is still shown exactly once per Preface run (Req 2.2).

        The banner directive must retain the once-only rule, and the
        illustration path must not re-display the banner when re-presenting the
        gate.
        """
        block = _norm(_load())
        assert (
            "show it once per preface run; do not re-display when re-presenting the gate"
            in block
        ), (
            "Expected the once-only ER_Concepts_Banner directive to be preserved "
            f"in {TARGET_FILE.name} (Req 2.2, P2)."
        )
        assert "never re-display the banner" in block, (
            "Expected the illustration/offer path to state it never re-displays "
            f"the banner in {TARGET_FILE.name} (Req 2.2, P2)."
        )
