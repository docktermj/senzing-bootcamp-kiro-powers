"""Property-based tests for silent self-correction regeneration and suppression.

Property 5: Silent self-correction instructs regeneration and suppression.

Verifies that the Phase 4 section of the consolidated ask-bootcamper.kiro.hook
contains both a regeneration instruction and a suppression instruction.

**Validates: Requirements 2.1, 2.2**
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOK_PATH = Path("senzing-bootcamp/hooks/ask-bootcamper.kiro.hook")

# Regeneration instruction phrases that must appear in Phase 4.
# These verify Requirement 2.1: the hook instructs the agent to regenerate
# its entire last response with the corrected question inline.
REGENERATION_PHRASES: list[str] = [
    "REGENERATE your entire last response",
    "Replace the compound",
    "Rebuild the full response inline",
]

# Suppression instruction phrases that must appear in Phase 4.
# These verify Requirement 2.2: the hook instructs the agent to suppress
# the original compound question from the bootcamper's view.
SUPPRESSION_PHRASES: list[str] = [
    "suppress the original compound question",
    "bootcamper must only see the clean version",
    "Do NOT output the rewrite as a separate message",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_hook_prompt() -> str:
    """Load and return the then.prompt field from the consolidated hook file."""
    with open(HOOK_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["then"]["prompt"]


def extract_phase4_section(prompt: str) -> str:
    """Extract the Phase 4 section from the consolidated hook prompt.

    Returns the text from the PHASE 4 header line through to the next
    major section boundary (═══ line after the header's closing ═══ line)
    or end of prompt.
    """
    phase4_start = prompt.find("PHASE 4:")
    if phase4_start < 0:
        return ""

    after_header = prompt[phase4_start:]
    lines = after_header.split("\n")

    # The structure is: PHASE 4 line, ═══ closing line, then content,
    # then ═══ line starting the next section.
    header_close_found = False
    for i, line in enumerate(lines):
        if i == 0:
            continue  # skip the PHASE 4 line itself
        if "════" in line and not header_close_found:
            header_close_found = True
            continue
        if "════" in line and header_close_found:
            # This is the next section boundary
            return "\n".join(lines[:i])

    # No next section found — Phase 4 extends to end of prompt
    return after_header


# ---------------------------------------------------------------------------
# Property 5: Silent self-correction instructs regeneration and suppression
# ---------------------------------------------------------------------------


class TestSilentSelfCorrectionRegenerationAndSuppression:
    """For the Phase 4 section, both regeneration and suppression instructions exist.

    **Validates: Requirements 2.1, 2.2**

    Property 5: For any valid Ask_Bootcamper_Hook prompt, the
    Question_Format_Phase section SHALL contain both (a) an instruction to
    regenerate the entire last response with the corrected question inline,
    and (b) an instruction to suppress the original compound question from
    the bootcamper's view.
    """

    @given(phrase=st.sampled_from(REGENERATION_PHRASES))
    @settings(max_examples=20)
    def test_phase4_contains_regeneration_instruction(self, phrase: str):
        """For any regeneration phrase, Phase 4 SHALL contain it."""
        prompt = load_hook_prompt()
        phase4 = extract_phase4_section(prompt)
        assert phase4, "Phase 4 section not found in consolidated hook prompt"
        assert phrase in phase4, (
            f"Phase 4 section does not contain regeneration instruction "
            f"'{phrase}'"
        )

    @given(phrase=st.sampled_from(SUPPRESSION_PHRASES))
    @settings(max_examples=20)
    def test_phase4_contains_suppression_instruction(self, phrase: str):
        """For any suppression phrase, Phase 4 SHALL contain it."""
        prompt = load_hook_prompt()
        phase4 = extract_phase4_section(prompt)
        assert phase4, "Phase 4 section not found in consolidated hook prompt"
        assert phrase in phase4, (
            f"Phase 4 section does not contain suppression instruction "
            f"'{phrase}'"
        )

    @given(
        regen_phrase=st.sampled_from(REGENERATION_PHRASES),
        suppress_phrase=st.sampled_from(SUPPRESSION_PHRASES),
    )
    @settings(max_examples=20)
    def test_phase4_has_both_regeneration_and_suppression(
        self, regen_phrase: str, suppress_phrase: str
    ):
        """For any pair of regeneration and suppression phrases, both SHALL
        be present in Phase 4 (co-existence property)."""
        prompt = load_hook_prompt()
        phase4 = extract_phase4_section(prompt)
        assert phase4, "Phase 4 section not found in consolidated hook prompt"

        has_regen = regen_phrase in phase4
        has_suppress = suppress_phrase in phase4

        assert has_regen and has_suppress, (
            f"Phase 4 must contain both regeneration and suppression "
            f"instructions. Regeneration '{regen_phrase}' found: {has_regen}, "
            f"Suppression '{suppress_phrase}' found: {has_suppress}"
        )
