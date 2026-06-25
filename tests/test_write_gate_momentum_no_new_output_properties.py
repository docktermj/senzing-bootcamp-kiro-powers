"""Property 5 tests for the write-gate-momentum-preservation feature.

Outcome B extends the ``write-policy-gate`` INTERNAL-FILE PASS-THROUGH set with
two routine power-managed config files. The extension must reuse the existing
zero-token silent outcome and add *no new output strings*: the FAST PATH GATE
and CHECK 1-4 rule-delimited sections must stay byte-for-byte identical to the
captured baseline, the pass-through block must introduce no new corrective/STOP
marker of its own, and any clean write the gate holds (a non-pass-through write
that passes all four checks) must still resolve to the silent outcome.

This file is DEDICATED to Property 5 only, kept separate from the sibling
passthrough property modules to avoid file collisions.

The baseline is the single source of truth captured in
``tests/write_gate_momentum_baseline.py`` (task 1.1): ``BASELINE_SECTIONS`` maps
each section label to its ``(split-index, byte-for-byte text)`` snapshot, which
this module compares against the live prompt loaded on every call.

**Validates: Requirements 4.5, 6.4**
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import example, given, settings
from hypothesis import strategies as st

# Tests are not packaged; make the sibling test modules importable.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from gate_decision_model import (  # noqa: E402
    PASS_SILENT,
    WriteOperation,
    contains_senzing_sql,
    gate,
    load_gate_prompt,
)
from write_gate_momentum_baseline import (  # noqa: E402
    BASELINE_SECTION_LABELS,
    BASELINE_SECTIONS,
    NEW_PASSTHROUGH_PATHS,
    passthrough_block,
    sections,
)

# ---------------------------------------------------------------------------
# Inputs.
# ---------------------------------------------------------------------------

# The three write tools the gate inspects.
_WRITE_TOOLS: tuple[str, str, str] = ("fs_write", "fs_append", "str_replace")

# Corrective markers that, in this hook prompt, signal a STOP/redirect output.
# The pass-through block must introduce none of these beyond what the captured
# baseline (pre-extension) already carried — its only edit is two enumeration
# lines, which carry no markers of their own.
_CORRECTIVE_MARKERS: tuple[str, str] = ("\u26a0\ufe0f", "STOP")


def st_baseline_label() -> st.SearchStrategy[str]:
    """Strategy over the captured baseline section labels (FAST PATH, CHECK 1-4)."""
    return st.sampled_from(list(BASELINE_SECTION_LABELS))


def st_write_tool() -> st.SearchStrategy[str]:
    """Strategy over the three write tools (fs_write, fs_append, str_replace)."""
    return st.sampled_from(_WRITE_TOOLS)


def st_clean_nonpassthrough_path() -> st.SearchStrategy[str]:
    """Strategy generating a clean, held, non-pass-through project path.

    The generated path lives under a ``src/`` subdirectory, so it is never a
    routine power-managed internal file (no pass-through), never a root-blocked
    placement (it has a subdirectory), never ``config/.question_pending``, never
    the feedback file, and never an external path. Such a write is therefore
    *held* by the gate and resolves through the four checks to the silent
    outcome.

    Returns:
        A strategy of ``src/<dir>/<name>.<ext>`` style project-relative paths.
    """
    segment = st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-",
        min_size=1,
        max_size=12,
    )
    extension = st.sampled_from(
        ["py", "ts", "java", "rs", "cs", "json", "yaml", "csv", "jsonl", "md"]
    )
    return st.builds(
        lambda subdir, name, ext: f"src/{subdir}/{name}.{ext}",
        subdir=segment,
        name=segment,
        ext=extension,
    )


def st_clean_content() -> st.SearchStrategy[str]:
    """Strategy generating NOT-guard-clean write content (no Senzing SQL).

    Returns:
        A strategy of content strings that never trip the Senzing SQL guard.
    """
    return st.text(max_size=400).filter(lambda c: not contains_senzing_sql(c))


def _reconstruct_baseline_block(live_block: str) -> str:
    """Reconstruct the pre-extension pass-through block from the live block.

    Outcome B's only edit to the pass-through block is the two added
    enumeration lines (``NEW_PASSTHROUGH_PATHS``). Removing them yields the
    block as it stood in the captured baseline, so a marker-count comparison
    proves the extension introduced no new corrective/STOP output.

    Args:
        live_block: The live INTERNAL-FILE PASS-THROUGH section text.

    Returns:
        The reconstructed pre-extension pass-through block text.
    """
    baseline_block = live_block
    for path in NEW_PASSTHROUGH_PATHS:
        baseline_block = baseline_block.replace(f"\n- {path}", "")
    return baseline_block


# ===========================================================================
# Property 5: The pass-through extension introduces no new output strings and
# preserves the silent outcome
# ===========================================================================
# Feature: write-gate-momentum-preservation, Property 5: For any of the
# established baseline sections (FAST PATH GATE and CHECK 1-4), the
# corresponding section in the live prompt is byte-for-byte identical to the
# captured baseline, and the INTERNAL-FILE PASS-THROUGH block adds no new
# corrective/STOP marker of its own; consequently any clean write that is held
# by the gate (a non-pass-through write passing all four checks) results in
# PASS_SILENT with intercepted=True and category=None, the same silent outcome
# the pass-through reuses.

class TestExtensionIntroducesNoNewOutputStrings:
    """The pass-through extension preserves the baseline safety surface
    byte-for-byte and reuses the silent held-write outcome.

    **Validates: Requirements 4.5, 6.4**
    """

    @given(
        label=st_baseline_label(),
        path=st_clean_nonpassthrough_path(),
        content=st_clean_content(),
        tool=st_write_tool(),
    )
    @settings(max_examples=200)
    @example(
        label="FAST PATH GATE",
        path="src/transform/mapper.py",
        content="def map_records(rows):\n    return [dict(r) for r in rows]\n",
        tool="fs_write",
    )
    @example(
        label="CHECK 1",
        path="src/transform/mapper.py",
        content="# clean transform logic, no Senzing SQL",
        tool="fs_append",
    )
    @example(
        label="CHECK 4",
        path="src/load/loader.py",
        content="rows = []",
        tool="str_replace",
    )
    def test_baseline_preserved_and_held_write_stays_silent(
        self, label: str, path: str, content: str, tool: str
    ):
        """Baseline sections are byte-identical and a clean held write is silent.

        Three invariants are asserted together for Property 5:

        1. The live prompt's ``label`` section is byte-for-byte identical to the
           captured baseline snapshot (FAST PATH GATE, CHECK 1-4 unchanged).
        2. The INTERNAL-FILE PASS-THROUGH block introduces no new corrective/
           STOP marker of its own relative to the reconstructed baseline block.
        3. A clean, non-pass-through write that passes all four checks resolves
           to ``PASS_SILENT`` with ``intercepted=True`` and ``category=None``.

        **Validates: Requirements 4.5, 6.4**
        """
        # 1. Baseline section is byte-for-byte identical to the captured snapshot.
        live_sections = sections()
        idx, baseline_text = BASELINE_SECTIONS[label]
        assert live_sections[idx] == baseline_text, (
            f"live section {label!r} (index {idx}) drifted from the captured "
            f"baseline — the safety surface must stay byte-for-byte identical"
        )

        # 2. Pass-through block adds no new corrective/STOP marker of its own.
        live_block = passthrough_block()
        assert "STOP" not in live_block, (
            "the INTERNAL-FILE PASS-THROUGH block must emit no STOP corrective "
            "of its own — it reuses the silent outcome"
        )
        baseline_block = _reconstruct_baseline_block(live_block)
        for marker in _CORRECTIVE_MARKERS:
            assert live_block.count(marker) == baseline_block.count(marker), (
                f"the pass-through extension introduced a new {marker!r} marker; "
                f"it must add no new output strings beyond the baseline"
            )

        # 3. A clean held (non-pass-through) write reuses the silent outcome.
        prompt = load_gate_prompt()
        op = WriteOperation(path=path, content=content, tool=tool)
        decision = gate(op, prompt)
        assert decision.outcome == PASS_SILENT, (
            f"expected PASS_SILENT for clean held write {path!r} via {tool}, "
            f"got {decision.outcome!r}"
        )
        assert decision.intercepted is True, (
            f"expected the gate to hold the non-pass-through write {path!r} "
            f"(intercepted=True), but it was excluded via pass-through"
        )
        assert decision.category is None, (
            f"expected no corrective category for clean held write {path!r}, "
            f"got {decision.category!r}"
        )
