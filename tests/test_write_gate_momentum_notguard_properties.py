"""Property 4 tests for the write-gate-momentum-preservation feature.

Outcome B extends the ``write-policy-gate`` INTERNAL-FILE PASS-THROUGH set with
two routine power-managed config files. This module guards that the extension
never weakens the four security checks: whenever a write to a candidate
pass-through path violates exactly one NOT-guard, the gate declines the silent
pass-through, holds the write (``intercepted=True``), and returns exactly one
corrective whose ``category`` matches the violated guard — with no extra
content.

This file is DEDICATED to Property 4 only. Sibling property modules cover the
other passthrough properties to avoid collisions. It drives the *live* hook
prompt through the pure ``gate_decision_model.gate`` decision model.

The four NOT-guard violations and their expected corrective categories are:

- Senzing SQL content (on a pass-through path) -> ``senzing_sql``
- A compound question written to ``config/.question_pending`` -> ``single_question``
- An ``fs_write``/``str_replace`` overwrite of the feedback file ->
  ``feedback_append_only``
- A blocked file type placed in the project root -> ``root_placement``

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 6.5**
"""

from __future__ import annotations

import string
import sys
from pathlib import Path

from hypothesis import example, given, settings
from hypothesis import strategies as st

# Tests are not packaged; make the sibling test modules importable.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from gate_decision_model import (  # noqa: E402
    FEEDBACK_FILE,
    INTERCEPT_CORRECTIVE,
    WriteOperation,
    gate,
    load_gate_prompt,
)

# ---------------------------------------------------------------------------
# Candidate pass-through paths (the set the gate may silently pass).
# ---------------------------------------------------------------------------

# Exact-match pass-through entries, including the two added by this feature.
_EXACT_PASS_THROUGH: tuple[str, ...] = (
    "config/data_sources.yaml",
    "config/visualization_tracker.json",
    "config/bootcamp_progress.json",
    "config/bootcamp_preferences.yaml",
)

# Benign filler content — lowercase letters and spaces only, so it can never
# carry a Senzing DB indicator (all indicators contain an uppercase letter,
# digit, period, or underscore) and therefore never trips the Senzing SQL
# guard. This keeps each scenario at exactly one NOT-guard violation.
_SAFE_TEXT: st.SearchStrategy[str] = st.text(
    alphabet=string.ascii_lowercase + " ",
    min_size=0,
    max_size=40,
)


def st_member_id() -> st.SearchStrategy[str]:
    """Strategy: a member id usable in colocated-team config paths.

    Returns:
        A non-empty token of ``[A-Za-z0-9_-]`` characters.
    """
    return st.text(
        alphabet=string.ascii_letters + string.digits + "_-",
        min_size=1,
        max_size=12,
    )


def st_pass_through_path() -> st.SearchStrategy[str]:
    """Strategy: any candidate pass-through path (exact, member, or log).

    Returns:
        A path string that belongs to (or matches the regex shape of) the
        INTERNAL-FILE PASS-THROUGH set.
    """
    exact = st.sampled_from(_EXACT_PASS_THROUGH)
    member_progress = st_member_id().map(lambda mid: f"config/progress_{mid}.json")
    member_prefs = st_member_id().map(lambda mid: f"config/preferences_{mid}.yaml")
    power_log = st_member_id().map(
        lambda mid: f"docs/progress/MODULE_{mid}_COMPLETE.md"
    )
    return st.one_of(exact, member_progress, member_prefs, power_log)


# ---------------------------------------------------------------------------
# NOT-guard violation content generators.
# ---------------------------------------------------------------------------

def st_senzing_sql_content() -> st.SearchStrategy[str]:
    """Strategy: content with an SQL pattern AND a Senzing DB indicator.

    Returns:
        A string that ``contains_senzing_sql`` classifies as Senzing SQL.
    """
    sql_keyword = st.sampled_from(
        ["SELECT * FROM", "INSERT INTO", "UPDATE", "DELETE FROM", "CREATE TABLE"]
    )
    indicator = st.sampled_from(
        ["RES_ENT", "OBS_ENT", "DSRC_RECORD", "LIB_FEAT", "database/G2C.db"]
    )
    return st.builds(
        lambda kw, ind: f"{kw} {ind} WHERE id = 1;",
        sql_keyword,
        indicator,
    )


def st_compound_question_content() -> st.SearchStrategy[str]:
    """Strategy: ``.question_pending`` content that is a compound question.

    Returns:
        A string with two question marks, which ``is_compound_question``
        rejects as compound. Both fragments use the safe alphabet so the
        Senzing SQL guard is never co-triggered.
    """
    return st.builds(
        lambda a, b: f"step_question\ndo you want {a}? or maybe {b}?",
        _SAFE_TEXT,
        _SAFE_TEXT,
    )


# ---------------------------------------------------------------------------
# Violation-scenario strategies: (WriteOperation, expected_category) pairs.
# Each scenario is constructed so it violates EXACTLY ONE NOT-guard.
# ---------------------------------------------------------------------------

def st_senzing_sql_violation() -> st.SearchStrategy[tuple[WriteOperation, str]]:
    """Strategy: a pass-through path carrying Senzing SQL content.

    The path is a genuine pass-through entry (not ``.question_pending``, not the
    feedback file, not a root placement), so the Senzing SQL guard is the only
    NOT-guard that fails.

    Returns:
        A ``(WriteOperation, "senzing_sql")`` pair.
    """
    return st.builds(
        lambda path, content, tool: (
            WriteOperation(path=path, content=content, tool=tool),
            "senzing_sql",
        ),
        st_pass_through_path(),
        st_senzing_sql_content(),
        st.sampled_from(["fs_write", "fs_append", "str_replace"]),
    )


def st_single_question_violation() -> st.SearchStrategy[tuple[WriteOperation, str]]:
    """Strategy: a compound question written to ``config/.question_pending``.

    Returns:
        A ``(WriteOperation, "single_question")`` pair.
    """
    return st.builds(
        lambda content, tool: (
            WriteOperation(path="config/.question_pending", content=content, tool=tool),
            "single_question",
        ),
        st_compound_question_content(),
        st.sampled_from(["fs_write", "fs_append", "str_replace"]),
    )


def st_feedback_violation() -> st.SearchStrategy[tuple[WriteOperation, str]]:
    """Strategy: a full-overwrite/in-place edit of the append-only feedback file.

    Only ``fs_write`` and ``str_replace`` violate the append-only guard;
    ``fs_append`` is the sanctioned tool and is excluded here.

    Returns:
        A ``(WriteOperation, "feedback_append_only")`` pair.
    """
    return st.builds(
        lambda content, tool: (
            WriteOperation(path=FEEDBACK_FILE, content=content, tool=tool),
            "feedback_append_only",
        ),
        _SAFE_TEXT,
        st.sampled_from(["fs_write", "str_replace"]),
    )


def st_root_placement_violation() -> st.SearchStrategy[tuple[WriteOperation, str]]:
    """Strategy: a blocked file type placed in the project root.

    The stem excludes whitelisted root stems so the path is genuinely blocked
    and only the root-placement guard fails.

    Returns:
        A ``(WriteOperation, "root_placement")`` pair.
    """
    return st.builds(
        lambda stem, ext, content, tool: (
            WriteOperation(path=f"{stem}{ext}", content=content, tool=tool),
            "root_placement",
        ),
        st.text(
            alphabet=string.ascii_lowercase + string.digits + "_-",
            min_size=1,
            max_size=16,
        ).filter(lambda s: s not in ("readme", "package", "requirements")),
        st.sampled_from([".py", ".md", ".jsonl", ".csv", ".json"]),
        _SAFE_TEXT,
        st.sampled_from(["fs_write", "fs_append", "str_replace"]),
    )


def st_notguard_violation() -> st.SearchStrategy[tuple[WriteOperation, str]]:
    """Strategy: any one of the four NOT-guard violations with its category.

    Returns:
        A ``(WriteOperation, expected_category)`` pair covering Senzing SQL,
        single-question, feedback append-only, and root-placement violations.
    """
    return st.one_of(
        st_senzing_sql_violation(),
        st_single_question_violation(),
        st_feedback_violation(),
        st_root_placement_violation(),
    )


# Feature: write-gate-momentum-preservation, Property 4: Any NOT-guard failure
# declines pass-through and yields exactly one matching corrective. For any
# write to a candidate pass-through path that violates exactly one NOT-guard,
# the gate declines the silent pass-through, holds the write (intercepted=True),
# and returns INTERCEPT_CORRECTIVE with exactly one category matching the
# violated guard and no additional content.
class TestNotGuardFailureYieldsOneMatchingCorrective:
    """NOT-guard failures decline pass-through and yield one matching corrective.

    **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 6.5**
    """

    @given(scenario=st_notguard_violation())
    @settings(max_examples=200)
    @example(
        scenario=(
            WriteOperation(
                path="config/data_sources.yaml",
                content="SELECT * FROM RES_ENT WHERE id = 1;",
                tool="fs_write",
            ),
            "senzing_sql",
        )
    )
    @example(
        scenario=(
            WriteOperation(
                path="config/.question_pending",
                content="step_question\ndo you want a? or b?",
                tool="fs_write",
            ),
            "single_question",
        )
    )
    @example(
        scenario=(
            WriteOperation(path=FEEDBACK_FILE, content="overwrite", tool="fs_write"),
            "feedback_append_only",
        )
    )
    @example(
        scenario=(
            WriteOperation(path=FEEDBACK_FILE, content="edit", tool="str_replace"),
            "feedback_append_only",
        )
    )
    @example(
        scenario=(
            WriteOperation(path="notes.md", content="scratch", tool="fs_write"),
            "root_placement",
        )
    )
    def test_notguard_failure_yields_one_matching_corrective(
        self, scenario: tuple[WriteOperation, str]
    ) -> None:
        """A single failed NOT-guard yields one matching corrective category.

        Drives the live hook prompt through the gate decision model and asserts
        the write is held and routed to the four security checks, producing
        exactly one corrective whose category matches the violated guard.

        Args:
            scenario: A ``(WriteOperation, expected_category)`` pair where the
                write violates exactly one NOT-guard.
        """
        op, expected_category = scenario
        prompt = load_gate_prompt()

        decision = gate(op, prompt)

        # The silent pass-through was declined: the write is held and evaluated.
        assert decision.intercepted is True, (
            f"expected the write to {op.path!r} via {op.tool} to be held, but "
            f"the gate passed it through silently"
        )
        # A single corrective outcome is produced.
        assert decision.outcome == INTERCEPT_CORRECTIVE, (
            f"expected INTERCEPT_CORRECTIVE for {op.path!r} via {op.tool}, got "
            f"{decision.outcome!r}"
        )
        # Exactly one category, matching the violated guard.
        assert decision.category == expected_category, (
            f"expected category {expected_category!r} for {op.path!r} via "
            f"{op.tool}, got {decision.category!r}"
        )
