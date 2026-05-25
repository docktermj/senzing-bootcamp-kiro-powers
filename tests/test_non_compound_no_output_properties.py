"""Property-based tests for non-compound case producing no phase output.

Property 6: Non-compound case produces no phase output.

Verifies that the Phase 4 section of the consolidated ask-bootcamper.kiro.hook
contains an explicit directive that when no compound question is detected, that
phase produces no output.

**Validates: Requirements 2.3**
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOK_PATH = Path("senzing-bootcamp/hooks/ask-bootcamper.kiro.hook")

# Phrases that express the "no compound question → no output" directive.
# At least one of these must appear in the Phase 4 section to satisfy the
# requirement that the phase explicitly states it produces no output when
# no compound question is detected.
NO_OUTPUT_DIRECTIVE_PHRASES: list[str] = [
    "Phase 4 output is none",
    "NO compound question detected",
]

# Contextual phrases that must co-exist with the no-output directive to
# confirm the directive is properly scoped to the non-compound case.
NO_COMPOUND_CONTEXT_PHRASES: list[str] = [
    "If NO compound question detected",
    "NOT COMPOUND",
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

    Returns the content text between the PHASE 4 header block and the next
    ════ separator line (or end of prompt). The header block consists of:
      ════...════
      PHASE 4: QUESTION FORMAT (Question_Format_Phase — Silent_Self_Correction)
      ════...════
    Content starts after the second ════ line.
    """
    phase4_idx = prompt.find("PHASE 4:")
    if phase4_idx < 0:
        return ""

    after_header = prompt[phase4_idx:]
    lines = after_header.split("\n")

    # Line 0: PHASE 4: ...
    # Line 1: ════...════ (closing bar of header block)
    # Line 2+: content until next ════ line
    content_end = None
    for i, line in enumerate(lines):
        if i <= 1:
            continue
        if re.match(r"^═{4,}", line):
            content_end = i
            break

    if content_end:
        return "\n".join(lines[2:content_end])
    return "\n".join(lines[2:])


# ---------------------------------------------------------------------------
# Property 6: Non-compound case produces no phase output
# ---------------------------------------------------------------------------


class TestNonCompoundNoPhaseOutput:
    """For the Phase 4 section, an explicit no-output directive exists for non-compound case.

    **Validates: Requirements 2.3**

    Property 6: For any valid Ask_Bootcamper_Hook prompt, the
    Question_Format_Phase section SHALL contain an explicit directive that
    when no compound question is detected, that phase produces no output
    (contributing to the default "." response).
    """

    @given(phrase=st.sampled_from(NO_OUTPUT_DIRECTIVE_PHRASES))
    @settings(max_examples=20)
    def test_phase4_contains_no_output_directive(self, phrase: str):
        """For any no-output directive phrase, Phase 4 SHALL contain it."""
        prompt = load_hook_prompt()
        phase4 = extract_phase4_section(prompt)
        assert phase4, "Phase 4 section not found in consolidated hook prompt"
        assert phrase in phase4, (
            f"Phase 4 section does not contain no-output directive "
            f"'{phrase}'. The phase must explicitly state that no compound "
            f"question results in no output."
        )

    @given(phrase=st.sampled_from(NO_COMPOUND_CONTEXT_PHRASES))
    @settings(max_examples=20)
    def test_phase4_contains_non_compound_context(self, phrase: str):
        """For any non-compound context phrase, Phase 4 SHALL contain it."""
        prompt = load_hook_prompt()
        phase4 = extract_phase4_section(prompt)
        assert phase4, "Phase 4 section not found in consolidated hook prompt"
        assert phrase in phase4, (
            f"Phase 4 section does not contain non-compound context phrase "
            f"'{phrase}'. The phase must explicitly describe the non-compound "
            f"case and its no-output behavior."
        )

    @given(
        directive=st.sampled_from(NO_OUTPUT_DIRECTIVE_PHRASES),
        context=st.sampled_from(NO_COMPOUND_CONTEXT_PHRASES),
    )
    @settings(max_examples=20)
    def test_phase4_no_output_directive_coexists_with_context(
        self, directive: str, context: str
    ):
        """For any pair of directive and context phrases, both SHALL be present
        in Phase 4 (co-existence property)."""
        prompt = load_hook_prompt()
        phase4 = extract_phase4_section(prompt)
        assert phase4, "Phase 4 section not found in consolidated hook prompt"

        has_directive = directive in phase4
        has_context = context in phase4

        assert has_directive and has_context, (
            f"Phase 4 must contain both the no-output directive and "
            f"non-compound context. Directive '{directive}' found: "
            f"{has_directive}, Context '{context}' found: {has_context}"
        )
