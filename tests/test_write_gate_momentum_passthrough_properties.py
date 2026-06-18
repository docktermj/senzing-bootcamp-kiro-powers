"""Property 1 tests for the write-gate-momentum-preservation feature.

Outcome B extends the ``write-policy-gate`` INTERNAL-FILE PASS-THROUGH set with
two routine power-managed config files so they pass silently on the first
attempt instead of churning through an intercept/retry cycle. This module
guards that behavior against drift by driving the *live* hook prompt through
the pure ``gate_decision_model.gate`` decision model.

This file is DEDICATED to Property 1 only. Sibling property modules cover the
other passthrough properties to avoid collisions.

**Validates: Requirements 4.1, 4.2**
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

# ---------------------------------------------------------------------------
# Inputs: the two new exact pass-through paths × the three write tools.
# ---------------------------------------------------------------------------

# The two routine power-managed files added to the pass-through set (Req 4.1,
# 4.2). Each must pass silently on the first attempt across every write tool.
_NEW_PASSTHROUGH_PATHS: tuple[str, str] = (
    "config/data_sources.yaml",
    "config/visualization_tracker.json",
)

# The write tools the gate inspects.
_WRITE_TOOLS: tuple[str, str, str] = ("fs_write", "fs_append", "str_replace")


def st_new_path() -> st.SearchStrategy[str]:
    """Strategy over the two new exact pass-through paths."""
    return st.sampled_from(_NEW_PASSTHROUGH_PATHS)


def st_write_tool() -> st.SearchStrategy[str]:
    """Strategy over the three write tools (fs_write, fs_append, str_replace)."""
    return st.sampled_from(_WRITE_TOOLS)


def st_clean_content() -> st.SearchStrategy[str]:
    """Strategy generating NOT-guard-clean write content.

    The only content-based NOT-guard for these paths is the Senzing SQL guard
    (the paths are not ``.question_pending``, not the feedback file, and not a
    root placement). Generated text is filtered so it never trips that guard,
    keeping the pass-through preconditions satisfied across all inputs.

    Returns:
        A strategy of content strings that contain no Senzing SQL.
    """
    return st.text(max_size=400).filter(lambda c: not contains_senzing_sql(c))


# ===========================================================================
# Property 1: New routine config files pass through silently on first attempt
# ===========================================================================
# Feature: write-gate-momentum-preservation, Property 1: For any write whose
# target path is exactly config/data_sources.yaml or config/visualization_
# tracker.json, with NOT-guard-clean content and across any write tool
# (fs_write, fs_append, str_replace), the gate decision is PASS_SILENT with
# intercepted=False, and the literal path appears in the INTERNAL-FILE
# PASS-THROUGH enumeration of then.prompt.

class TestNewRoutineConfigFilesPassThroughSilently:
    """The two new routine config files pass through silently on the first
    attempt across every write tool.

    **Validates: Requirements 4.1, 4.2**
    """

    @given(path=st_new_path(), tool=st_write_tool(), content=st_clean_content())
    @settings(max_examples=200)
    @example(path="config/data_sources.yaml", tool="fs_write", content="sources: []")
    @example(
        path="config/visualization_tracker.json",
        tool="fs_write",
        content='{"views": []}',
    )
    @example(path="config/data_sources.yaml", tool="fs_append", content="- new_source")
    @example(
        path="config/visualization_tracker.json",
        tool="str_replace",
        content='{"views": ["graph"]}',
    )
    def test_new_paths_pass_silently_and_are_enumerated(
        self, path: str, tool: str, content: str
    ):
        """A clean write to a new path passes silently and the path is listed.

        Drives the live hook prompt through the gate decision model and asserts
        the silent first-attempt outcome (PASS_SILENT, intercepted=False) and
        that the literal path appears in the INTERNAL-FILE PASS-THROUGH
        enumeration of ``then.prompt``.

        **Validates: Requirements 4.1, 4.2**
        """
        prompt = load_gate_prompt()
        op = WriteOperation(path=path, content=content, tool=tool)
        decision = gate(op, prompt)

        assert decision.outcome == PASS_SILENT, (
            f"expected PASS_SILENT for {path!r} via {tool}, got {decision.outcome!r}"
        )
        assert decision.intercepted is False, (
            f"expected no intercept (silent first attempt) for {path!r} via "
            f"{tool}, but the write was held"
        )
        assert decision.category is None, (
            f"expected no corrective category for clean {path!r}, got "
            f"{decision.category!r}"
        )
        assert path in prompt, (
            f"literal path {path!r} is not present in the INTERNAL-FILE "
            f"PASS-THROUGH enumeration of then.prompt"
        )
