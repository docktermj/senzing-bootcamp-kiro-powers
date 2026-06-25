"""Property 2 tests for the write-gate-momentum-preservation feature.

Outcome B extends the ``write-policy-gate`` INTERNAL-FILE PASS-THROUGH set with
two new exact-match entries (``config/data_sources.yaml`` and
``config/visualization_tracker.json``). This module guards against *regression*:
every path that was already in the pass-through set before the extension must
still pass silently with no intercept/retry cycle.

The pre-existing pass-through members are:

- the exact paths ``config/bootcamp_progress.json`` and
  ``config/bootcamp_preferences.yaml``
- any member-scoped ``config/progress_{id}.json`` instance
  (regex ``^config/progress_[A-Za-z0-9_-]+\\.json$``)
- any member-scoped ``config/preferences_{id}.yaml`` instance
  (regex ``^config/preferences_[A-Za-z0-9_-]+\\.yaml$``)
- any power-written ``docs/progress/MODULE_*_COMPLETE.md`` recap log
  (regex ``^docs/progress/MODULE_[^/]*_COMPLETE\\.md$``)

For NOT-guard-clean content across every write tool (``fs_write``,
``fs_append``, ``str_replace``), the gate decision must remain ``PASS_SILENT``
with ``intercepted = False`` — the extension regresses no previously silent
path.

**Validates: Requirements 4.3**
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from hypothesis import example, given, settings
from hypothesis import strategies as st

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from gate_decision_model import (  # noqa: E402
    PASS_SILENT,
    GateDecision,
    WriteOperation,
    contains_senzing_sql,
    gate,
    load_gate_prompt,
)

# ---------------------------------------------------------------------------
# Pre-existing pass-through members (exact + member-scoped regex instances).
# These mirror the design's pass-through set MINUS the two Outcome B additions.
# ---------------------------------------------------------------------------

_EXISTING_EXACT_PATHS: tuple[str, str] = (
    "config/bootcamp_progress.json",
    "config/bootcamp_preferences.yaml",
)

_MEMBER_PROGRESS_RE: re.Pattern[str] = re.compile(
    r"^config/progress_[A-Za-z0-9_-]+\.json$"
)
_MEMBER_PREFERENCES_RE: re.Pattern[str] = re.compile(
    r"^config/preferences_[A-Za-z0-9_-]+\.yaml$"
)
_RECAP_LOG_RE: re.Pattern[str] = re.compile(
    r"^docs/progress/MODULE_[^/]*_COMPLETE\.md$"
)

_WRITE_TOOLS: tuple[str, str, str] = ("fs_write", "fs_append", "str_replace")


# ---------------------------------------------------------------------------
# Hypothesis strategies — smart generators constrained to the input space.
# ---------------------------------------------------------------------------

def st_member_id() -> st.SearchStrategy[str]:
    """Strategy for member identifiers matching ``[A-Za-z0-9_-]+``."""
    return st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
        min_size=1,
        max_size=24,
    )


def st_recap_middle() -> st.SearchStrategy[str]:
    """Strategy for the ``MODULE_<middle>_COMPLETE.md`` middle segment.

    The recap regex allows any non-slash run (including empty) between the
    ``MODULE_`` prefix and the ``_COMPLETE.md`` suffix.
    """
    return st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
        min_size=0,
        max_size=24,
    )


def st_existing_passthrough_path() -> st.SearchStrategy[str]:
    """Strategy over every path that was a pass-through member pre-extension."""
    return st.one_of(
        st.sampled_from(_EXISTING_EXACT_PATHS),
        st_member_id().map(lambda i: f"config/progress_{i}.json"),
        st_member_id().map(lambda i: f"config/preferences_{i}.yaml"),
        st_recap_middle().map(lambda m: f"docs/progress/MODULE_{m}_COMPLETE.md"),
    )


def st_clean_content() -> st.SearchStrategy[str]:
    """Strategy for NOT-guard-clean write content (no Senzing SQL).

    Combines realistic config/recap samples with free-form text, then filters
    out any value that would trip the Senzing-SQL NOT-guard so the pass-through
    precondition (clean content) always holds.
    """
    samples = st.sampled_from(
        [
            "",
            "{}",
            '{"module": 3, "status": "complete"}',
            "module: 3\nstatus: complete\n",
            "# Module 3 Complete\n\nGreat work finishing the module.\n",
            '{"members": {"alice": {"progress": 0.5}}}',
            "preferences:\n  track: python\n  pace: steady\n",
            "completed_steps:\n  - intro\n  - first-demo\n",
        ]
    )
    free_form = st.text(max_size=200)
    return st.one_of(samples, free_form).filter(
        lambda c: not contains_senzing_sql(c)
    )


def _assert_pass_through(path: str, content: str, tool: str) -> None:
    """Assert a write to an existing pass-through path stays silent.

    Args:
        path: The pre-existing pass-through target path.
        content: NOT-guard-clean write content.
        tool: One of ``fs_write``, ``fs_append``, ``str_replace``.
    """
    prompt = load_gate_prompt()
    op = WriteOperation(path=path, content=content, tool=tool)
    decision: GateDecision = gate(op, prompt)
    assert decision.outcome == PASS_SILENT, (
        f"existing pass-through path {path!r} via {tool} regressed: "
        f"expected {PASS_SILENT}, got {decision.outcome} "
        f"(category={decision.category})"
    )
    assert decision.intercepted is False, (
        f"existing pass-through path {path!r} via {tool} was intercepted; "
        f"the extension must not regress a previously silent path"
    )


# ===========================================================================
# Property 2: Existing pass-through entries still pass silently
# ===========================================================================
# Feature: write-gate-momentum-preservation, Property 2: For any write whose
# target path was already in the pass-through set before this change — the
# exact paths config/bootcamp_progress.json and config/bootcamp_preferences.yaml,
# any member-scoped config/progress_{id}.json or config/preferences_{id}.yaml
# instance, and any power-written docs/progress/MODULE_*_COMPLETE.md recap log —
# with NOT-guard-clean content and any write tool, the gate decision remains
# PASS_SILENT with intercepted = False. The extension regresses no previously
# silent path.

class TestExistingPassThroughEntriesStillPassSilently:
    """Pre-existing pass-through entries remain silent (no regression).

    **Validates: Requirements 4.3**
    """

    @given(
        path=st_existing_passthrough_path(),
        content=st_clean_content(),
        tool=st.sampled_from(_WRITE_TOOLS),
    )
    @settings(max_examples=200)
    @example(
        path="config/bootcamp_progress.json", content="{}", tool="fs_write"
    )
    @example(
        path="config/bootcamp_progress.json", content="{}", tool="fs_append"
    )
    @example(
        path="config/bootcamp_progress.json", content="{}", tool="str_replace"
    )
    @example(
        path="config/bootcamp_preferences.yaml",
        content="track: python\n",
        tool="fs_write",
    )
    @example(
        path="config/progress_alice.json",
        content='{"progress": 0.5}',
        tool="fs_append",
    )
    @example(
        path="config/preferences_team-1.yaml",
        content="pace: steady\n",
        tool="str_replace",
    )
    @example(
        path="docs/progress/MODULE_3_COMPLETE.md",
        content="# Module 3 Complete\n",
        tool="fs_write",
    )
    def test_existing_entries_pass_silently(
        self, path: str, content: str, tool: str
    ):
        """An existing pass-through write stays PASS_SILENT / intercepted=False.

        Drives the live hook prompt through the pure gate decision model over
        every pre-existing pass-through path category and all three write tools,
        with NOT-guard-clean content.

        **Validates: Requirements 4.3**
        """
        _assert_pass_through(path, content, tool)
