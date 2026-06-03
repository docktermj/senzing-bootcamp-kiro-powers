"""Property-based tests for question format detection patterns with silent self-correction.

Property 4: Question format detection patterns preserved with silent self-correction.

Verifies that all compound-question detection pattern descriptions appear in the
consolidated ask-bootcamper.kiro.hook prompt AND silent self-correction language
(regeneration instruction) is present.

**Validates: Requirements 1.6, 2.4**
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOK_PATH = Path("senzing-bootcamp/hooks/ask-bootcamper.kiro.hook")

# Detection pattern descriptions that must appear in the prompt.
# These correspond to the three compound-question detection patterns from
# the original question-format-gate.kiro.hook, now in Phase 4.
DETECTION_PATTERN_DESCRIPTIONS: list[str] = [
    "Sentence-starter 'Or'",
    "Inline prose 'or'",
    "Appended alternative",
]

# Key phrases from each detection pattern that must appear in the prompt.
DETECTION_PATTERN_PHRASES: list[str] = [
    "Or shall we",
    "Or would you",
    "Or should we",
    "or would you rather",
    "or shall we",
]

# Silent self-correction language that must be present in the prompt.
SILENT_SELF_CORRECTION_PHRASES: list[str] = [
    "REGENERATE",
    "suppress the original compound question",
    "Do NOT output the rewrite as a separate message",
    "Rebuild the full response inline",
    "bootcamper must only see the clean version",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_hook_prompt() -> str:
    """Load and return the then.prompt field from the consolidated hook file."""
    with open(HOOK_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["then"]["prompt"]


# ---------------------------------------------------------------------------
# Property 4: Question Format Detection Patterns Preserved with Silent
#              Self-Correction
# ---------------------------------------------------------------------------


class TestQuestionFormatDetectionPatterns:
    """For any detection pattern description, the consolidated hook prompt contains it.

    **Validates: Requirements 1.6, 2.4**

    Property 4: For any compound-question detection pattern from the original
    question-format-gate.kiro.hook (sentence-starter Or, inline prose or,
    appended alternative), that pattern description SHALL appear in the
    consolidated Ask_Bootcamper_Hook prompt, AND the prompt SHALL contain
    silent self-correction language instructing response regeneration rather
    than separate-message output.
    """

    @given(pattern_desc=st.sampled_from(DETECTION_PATTERN_DESCRIPTIONS))
    @settings(max_examples=20)
    def test_detection_pattern_description_present(self, pattern_desc: str):
        """For any detection pattern description, the prompt SHALL contain it."""
        prompt = load_hook_prompt()
        assert pattern_desc in prompt, (
            f"Consolidated hook prompt does not contain detection pattern "
            f"description '{pattern_desc}'"
        )

    @given(phrase=st.sampled_from(DETECTION_PATTERN_PHRASES))
    @settings(max_examples=20)
    def test_detection_pattern_example_phrases_present(self, phrase: str):
        """For any detection pattern example phrase, the prompt SHALL contain it."""
        prompt = load_hook_prompt()
        assert phrase in prompt, (
            f"Consolidated hook prompt does not contain detection pattern "
            f"example phrase '{phrase}'"
        )

    @given(phrase=st.sampled_from(SILENT_SELF_CORRECTION_PHRASES))
    @settings(max_examples=20)
    def test_silent_self_correction_language_present(self, phrase: str):
        """For any silent self-correction phrase, the prompt SHALL contain it."""
        prompt = load_hook_prompt()
        assert phrase in prompt, (
            f"Consolidated hook prompt does not contain silent self-correction "
            f"language '{phrase}'"
        )

    @given(pattern_desc=st.sampled_from(DETECTION_PATTERN_DESCRIPTIONS))
    @settings(max_examples=20)
    def test_detection_patterns_coexist_with_regeneration(self, pattern_desc: str):
        """For any detection pattern, both the pattern AND regeneration instruction
        SHALL be present in the same prompt (co-existence property)."""
        prompt = load_hook_prompt()
        has_pattern = pattern_desc in prompt
        has_regeneration = "REGENERATE" in prompt

        assert has_pattern and has_regeneration, (
            f"Detection pattern '{pattern_desc}' and regeneration instruction "
            f"must both be present. Pattern found: {has_pattern}, "
            f"Regeneration found: {has_regeneration}"
        )
