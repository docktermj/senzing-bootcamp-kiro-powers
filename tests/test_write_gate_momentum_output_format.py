"""OUTPUT FORMAT integrity example tests for write-gate-momentum-preservation.

These are deterministic example/unit tests (NOT property-based) covering the
OUTPUT FORMAT integrity facet of Requirement 6.5: the live ``write-policy-gate``
prompt's "OUTPUT FORMAT (STRICT)" section must forbid extra content and
explicitly enumerate the forbidden narration strings, and a single policy
violation must yield exactly one corrective instruction and nothing else.

Two independent surfaces are asserted:

1. **Prompt text (static).** The OUTPUT FORMAT section is the final
   rule-delimited section of the live prompt. It must enumerate every forbidden
   narration string and must forbid extra output (the "Output ONLY the
   corrective instruction" / "FORBIDDEN" wording).
2. **Gate behavior (modeled).** Driving the pure ``gate`` decision model with a
   single-NOT-guard violation produces ``INTERCEPT_CORRECTIVE`` with exactly one
   corrective ``category`` — one corrective and nothing else.

The module reuses (and does not modify) the public contracts of
``tests/write_gate_momentum_baseline.py`` and ``tests/gate_decision_model.py``.

**Validates: Requirements 6.5**
"""

from __future__ import annotations

import sys
from pathlib import Path

# Tests are not packaged; make the sibling helper modules importable.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from gate_decision_model import (  # noqa: E402
    INTERCEPT_CORRECTIVE,
    WriteOperation,
    gate,
    load_gate_prompt,
)
from write_gate_momentum_baseline import sections  # noqa: E402

# ---------------------------------------------------------------------------
# Expectations
# ---------------------------------------------------------------------------

# The forbidden narration strings the OUTPUT FORMAT section must enumerate.
FORBIDDEN_NARRATION_STRINGS: tuple[str, ...] = (
    "Fast path passes",
    "Proceeding",
    "All checks pass",
    "This is a JSON configuration file",
    "Not SQL",
    "The file is inside the working directory",
)

# Phrases proving the section forbids any output beyond the single corrective.
FORBID_EXTRA_CONTENT_MARKERS: tuple[str, ...] = (
    "Output ONLY the corrective instruction",
    "FORBIDDEN",
)


def _output_format_section() -> str:
    """Return the live prompt's OUTPUT FORMAT section.

    The OUTPUT FORMAT section is the final rule-delimited section of the prompt
    (after splitting on the ``\\n\\n---\\n\\n`` separator).

    Returns:
        The OUTPUT FORMAT section text.
    """
    return sections()[-1]


class TestOutputFormatIntegrity:
    """The OUTPUT FORMAT section forbids extra content and a single violation
    yields exactly one corrective and nothing else.

    **Validates: Requirements 6.5**
    """

    def test_section_is_the_output_format_section(self):
        """The final rule-delimited section is the OUTPUT FORMAT section.

        **Validates: Requirements 6.5**
        """
        section = _output_format_section()
        assert section.startswith("OUTPUT FORMAT (STRICT):"), (
            "the final prompt section must be the OUTPUT FORMAT (STRICT) block; "
            f"got: {section[:60]!r}"
        )

    def test_section_lists_all_forbidden_narration_strings(self):
        """Every forbidden narration string is enumerated in the section.

        **Validates: Requirements 6.5**
        """
        section = _output_format_section()
        missing = [s for s in FORBIDDEN_NARRATION_STRINGS if s not in section]
        assert not missing, (
            f"OUTPUT FORMAT section is missing forbidden narration strings: {missing}"
        )

    def test_section_forbids_extra_content(self):
        """The section forbids any output beyond the single corrective.

        **Validates: Requirements 6.5**
        """
        section = _output_format_section()
        missing = [m for m in FORBID_EXTRA_CONTENT_MARKERS if m not in section]
        assert not missing, (
            "OUTPUT FORMAT section must forbid extra content via "
            f"{FORBID_EXTRA_CONTENT_MARKERS}; missing: {missing}"
        )

    def test_section_forbids_narrating_the_evaluation(self):
        """The section forbids any text narrating/summarizing the evaluation.

        **Validates: Requirements 6.5**
        """
        section = _output_format_section()
        assert "describing, summarizing, or narrating" in section, (
            "OUTPUT FORMAT section must forbid narrating/summarizing the "
            "evaluation process"
        )

    def test_single_violation_yields_exactly_one_corrective(self):
        """A single-NOT-guard violation emits exactly one corrective, nothing else.

        A root-blocked ``.py`` file at the project root trips exactly one guard
        (Check 4 root placement). The modeled gate must return
        ``INTERCEPT_CORRECTIVE`` with exactly one corrective ``category`` — i.e.
        a single corrective and no additional output.

        **Validates: Requirements 6.5**
        """
        prompt = load_gate_prompt()
        op = WriteOperation(path="rogue_script.py", content="print('hello')")
        decision = gate(op, prompt)

        assert decision.outcome == INTERCEPT_CORRECTIVE, (
            f"a single-NOT-guard violation must intercept with a corrective; "
            f"got outcome={decision.outcome!r}"
        )
        # The model carries the corrective as a single scalar category — exactly
        # one corrective, never a list of several.
        assert isinstance(decision.category, str), (
            "a single violation must produce exactly one corrective category "
            f"(a single string); got {decision.category!r}"
        )
        assert decision.category == "root_placement", (
            f"expected the single root-placement corrective; got "
            f"{decision.category!r}"
        )

    def test_feedback_overwrite_violation_yields_exactly_one_corrective(self):
        """A feedback-file overwrite trips exactly one guard and one corrective.

        Confirms the "exactly one corrective and nothing else" outcome holds for
        a second, independent single-NOT-guard violation.

        **Validates: Requirements 6.5**
        """
        prompt = load_gate_prompt()
        op = WriteOperation(
            path="docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md",
            content="# Feedback\n",
            tool="fs_write",
        )
        decision = gate(op, prompt)

        assert decision.outcome == INTERCEPT_CORRECTIVE, (
            f"a feedback overwrite must intercept with a corrective; got "
            f"outcome={decision.outcome!r}"
        )
        assert isinstance(decision.category, str), (
            "a single violation must produce exactly one corrective category "
            f"(a single string); got {decision.category!r}"
        )
        assert decision.category == "feedback_append_only", (
            f"expected the single feedback-append-only corrective; got "
            f"{decision.category!r}"
        )
