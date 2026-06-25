"""Pass-through ordering and enumeration-diff example tests (task 3.2).

These are deterministic, input-invariant example/unit tests for Outcome B of the
write-gate-momentum-preservation feature. They guard two structural properties
of the live ``write-policy-gate`` hook prompt:

- **Ordering (Requirement 4.4):** the INTERNAL-FILE PASS-THROUGH block is
  evaluated *before* the FAST PATH GATE section.
- **Enumeration diff (Requirements 4.1, 5.3):** the pass-through enumeration
  gained exactly the two new exact-match lines
  (``- config/data_sources.yaml`` and ``- config/visualization_tracker.json``)
  relative to the reconstructed pre-extension baseline, with every prior entry
  preserved.

Both tests drive the *live* on-disk hook prompt through the shared baseline
helpers in :mod:`write_gate_momentum_baseline`, so any drift fails the build.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Tests are not packaged; make the sibling baseline module importable.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from write_gate_momentum_baseline import (  # noqa: E402
    NEW_PASSTHROUGH_PATHS,
    PASSTHROUGH_SECTION_INDEX,
    SECTION_SEPARATOR,
    live_enumeration_lines,
    load_prompt,
    passthrough_block,
    reconstruct_baseline_enumeration,
    sections,
)

# The FAST PATH GATE section begins with this label.
_FAST_PATH_GATE_LABEL: str = "FAST PATH GATE"

# The header that introduces the INTERNAL-FILE PASS-THROUGH block.
_PASSTHROUGH_LABEL: str = "INTERNAL-FILE PASS-THROUGH"

# The two new exact-match enumeration lines (bullet-prefixed).
_NEW_ENUMERATION_LINES: tuple[str, ...] = tuple(
    f"- {path}" for path in NEW_PASSTHROUGH_PATHS
)


class TestPassThroughOrdering:
    """The INTERNAL-FILE PASS-THROUGH block precedes the FAST PATH GATE section.

    **Validates: Requirements 4.4**
    """

    def test_passthrough_block_is_first_section(self) -> None:
        """The pass-through block occupies section index 0, before FAST PATH GATE.

        Splits the live prompt on ``SECTION_SEPARATOR`` and asserts the
        pass-through block lives at ``PASSTHROUGH_SECTION_INDEX`` while the
        FAST PATH GATE label appears in a later section.

        **Validates: Requirements 4.4**
        """
        prompt_sections = sections()

        passthrough = prompt_sections[PASSTHROUGH_SECTION_INDEX]
        assert _PASSTHROUGH_LABEL in passthrough, (
            f"expected {_PASSTHROUGH_LABEL!r} in section "
            f"{PASSTHROUGH_SECTION_INDEX}, got: {passthrough[:80]!r}"
        )
        assert passthrough == passthrough_block(), (
            "passthrough_block() must return the section at "
            "PASSTHROUGH_SECTION_INDEX"
        )

        # The pass-through block (section 0) references "the FAST PATH GATE"
        # in prose, so identify the *actual* gate section by the section that
        # begins with the label, not one that merely mentions it.
        fast_path_indices = [
            i for i, sec in enumerate(prompt_sections)
            if sec.lstrip().startswith(_FAST_PATH_GATE_LABEL)
        ]
        assert fast_path_indices, (
            f"expected a section beginning with {_FAST_PATH_GATE_LABEL!r}"
        )
        assert PASSTHROUGH_SECTION_INDEX < fast_path_indices[0], (
            "INTERNAL-FILE PASS-THROUGH block must precede the FAST PATH GATE "
            f"section (passthrough at {PASSTHROUGH_SECTION_INDEX}, FAST PATH "
            f"GATE at {fast_path_indices[0]})"
        )

    def test_passthrough_text_precedes_fast_path_gate_text(self) -> None:
        """The pass-through label appears before FAST PATH GATE in the raw prompt.

        A direct character-offset check independent of the section split:
        ``prompt.index('INTERNAL-FILE PASS-THROUGH')`` must come before
        ``prompt.index('FAST PATH GATE')``.

        **Validates: Requirements 4.4**
        """
        prompt = load_prompt()
        assert prompt.index(_PASSTHROUGH_LABEL) < prompt.index(
            _FAST_PATH_GATE_LABEL
        ), (
            "INTERNAL-FILE PASS-THROUGH must appear before FAST PATH GATE in "
            "the prompt text"
        )

    def test_section_separator_splits_distinct_blocks(self) -> None:
        """The separator yields distinct pass-through and FAST PATH GATE blocks.

        Confirms the two structural blocks land in different sections so the
        ordering assertion is meaningful (not both inside one section). The
        pass-through block references "the FAST PATH GATE" in prose, so the
        gate *section* is identified by the section that begins with the label.

        **Validates: Requirements 4.4**
        """
        prompt = load_prompt()
        assert SECTION_SEPARATOR in prompt, (
            f"expected section separator {SECTION_SEPARATOR!r} in the prompt"
        )

        prompt_sections = sections()
        gate_section_indices = [
            i for i, sec in enumerate(prompt_sections)
            if sec.lstrip().startswith(_FAST_PATH_GATE_LABEL)
        ]
        assert gate_section_indices, (
            f"expected a distinct section beginning with {_FAST_PATH_GATE_LABEL!r}"
        )
        assert PASSTHROUGH_SECTION_INDEX not in gate_section_indices, (
            "FAST PATH GATE must live in a separate section from the "
            "INTERNAL-FILE PASS-THROUGH block"
        )


class TestEnumerationDiff:
    """The enumeration gained exactly the two new lines, preserving all priors.

    **Validates: Requirements 4.1, 5.3**
    """

    def test_live_enumeration_added_exactly_the_two_new_lines(self) -> None:
        """Live minus reconstructed baseline equals exactly the two new lines.

        Compares the live enumeration against the reconstructed pre-extension
        baseline and asserts the set difference is exactly the two new
        exact-match lines ``- config/data_sources.yaml`` and
        ``- config/visualization_tracker.json``.

        **Validates: Requirements 4.1, 5.3**
        """
        live = live_enumeration_lines()
        baseline = reconstruct_baseline_enumeration(live)

        added = set(live) - set(baseline)
        assert added == set(_NEW_ENUMERATION_LINES), (
            f"expected exactly the two new lines added, got {sorted(added)!r}"
        )

    def test_two_new_lines_present_in_live_enumeration(self) -> None:
        """Both new exact-match lines are present in the live enumeration.

        **Validates: Requirements 4.1**
        """
        live = live_enumeration_lines()
        for line in _NEW_ENUMERATION_LINES:
            assert line in live, (
                f"expected new enumeration line {line!r} in live enumeration"
            )

    def test_every_baseline_entry_preserved(self) -> None:
        """Every reconstructed baseline entry survives in the live enumeration.

        Guards Requirement 5.3 (existing pass-through entries retained): no
        prior enumeration entry was dropped when the two new lines were added.

        **Validates: Requirements 5.3**
        """
        live = live_enumeration_lines()
        baseline = reconstruct_baseline_enumeration(live)

        assert baseline, "reconstructed baseline enumeration must be non-empty"
        for entry in baseline:
            assert entry in live, (
                f"baseline enumeration entry {entry!r} was not preserved in "
                f"the live enumeration"
            )

    def test_live_count_is_baseline_plus_two(self) -> None:
        """The live enumeration has exactly two more lines than the baseline.

        A net-count guard reinforcing that the extension added exactly two
        lines and removed none.

        **Validates: Requirements 4.1, 5.3**
        """
        live = live_enumeration_lines()
        baseline = reconstruct_baseline_enumeration(live)
        assert len(live) == len(baseline) + 2, (
            f"expected live enumeration to have baseline+2 lines, got "
            f"live={len(live)} baseline={len(baseline)}"
        )
