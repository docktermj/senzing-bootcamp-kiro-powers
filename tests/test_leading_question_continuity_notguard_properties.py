"""Property test: NOT-guard failures decline pass-through and route to checks.

This module exercises the *live* ``write-policy-gate`` prompt through the
gate decision model (``tests/gate_decision_model.py``). It verifies that the
INTERNAL-FILE PASS-THROUGH extension never weakens the four security checks:
whenever any NOT-guard fails for a candidate pass-through path, the gate
declines the silent pass-through and routes the write to the security checks,
producing the corrective outcome whose category matches the failing guard.

The four NOT-guard violations and their expected corrective categories are:

- Senzing SQL content (on any path, including a pass-through path) -> ``senzing_sql``
- The append-only feedback file overwritten/edited -> ``feedback_append_only``
- The ``config/.question_pending`` file with a compound question -> ``single_question``
- A blocked file type placed in the project root -> ``root_placement``

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
"""

from __future__ import annotations

import string

from hypothesis import given, settings
from hypothesis import strategies as st

from gate_decision_model import (
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

# Safe alphabet for benign filler content — no SQL keywords, no Senzing tokens.
_SAFE_TEXT = st.text(
    alphabet=string.ascii_lowercase + string.digits + " _-.",
    min_size=1,
    max_size=24,
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
        ["SELECT * FROM", "INSERT INTO", "UPDATE", "DELETE FROM"]
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
        A string with two question marks or a choice-joining conjunction, which
        ``is_compound_question`` rejects as compound.
    """
    two_marks = st.builds(
        lambda a, b: f"step_question\nDo you want {a}? Or maybe {b}?",
        _SAFE_TEXT,
        _SAFE_TEXT,
    )
    joiner = st.builds(
        lambda a, b: f"step_question\nShould we use {a} or {b}?",
        _SAFE_TEXT,
        _SAFE_TEXT,
    )
    return st.one_of(two_marks, joiner)


# ---------------------------------------------------------------------------
# Violation-scenario strategy: (WriteOperation, expected_category) pairs.
# ---------------------------------------------------------------------------

def st_senzing_sql_violation() -> st.SearchStrategy[tuple[WriteOperation, str]]:
    """Strategy: a pass-through path carrying Senzing SQL content.

    Pairs each candidate pass-through path with injected Senzing SQL so the
    block applies regardless of the target path.

    Returns:
        A ``(WriteOperation, "senzing_sql")`` pair.
    """
    return st.builds(
        lambda path, content: (
            WriteOperation(path=path, content=content),
            "senzing_sql",
        ),
        st_pass_through_path(),
        st_senzing_sql_content(),
    )


def st_feedback_violation() -> st.SearchStrategy[tuple[WriteOperation, str]]:
    """Strategy: a full-overwrite/in-place edit of the append-only feedback file.

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


def st_single_question_violation() -> st.SearchStrategy[tuple[WriteOperation, str]]:
    """Strategy: a compound question written to ``config/.question_pending``.

    Returns:
        A ``(WriteOperation, "single_question")`` pair.
    """
    return st.builds(
        lambda content: (
            WriteOperation(path="config/.question_pending", content=content),
            "single_question",
        ),
        st_compound_question_content(),
    )


def st_root_placement_violation() -> st.SearchStrategy[tuple[WriteOperation, str]]:
    """Strategy: a blocked file type placed in the project root.

    Returns:
        A ``(WriteOperation, "root_placement")`` pair.
    """
    return st.builds(
        lambda stem, ext, content: (
            WriteOperation(path=f"{stem}{ext}", content=content),
            "root_placement",
        ),
        st.text(
            alphabet=string.ascii_lowercase + string.digits + "_-",
            min_size=1,
            max_size=16,
        ).filter(lambda s: s not in ("README", "requirements")),
        st.sampled_from([".py", ".md", ".jsonl", ".csv", ".json"]),
        _SAFE_TEXT,
    )


def st_notguard_violation() -> st.SearchStrategy[tuple[WriteOperation, str]]:
    """Strategy: any one of the four NOT-guard violations with its category.

    Returns:
        A ``(WriteOperation, expected_category)`` pair covering Senzing SQL,
        feedback append-only, single-question, and root-placement violations.
    """
    return st.one_of(
        st_senzing_sql_violation(),
        st_feedback_violation(),
        st_single_question_violation(),
        st_root_placement_violation(),
    )


# Feature: leading-question-continuity, Property 6: Any NOT-guard failure
# declines pass-through and routes to the security checks.
class TestNotGuardFailureRoutesToChecks:
    """Property 6 — NOT-guard failures decline pass-through, route to checks.

    **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
    """

    @settings(max_examples=200)
    @given(scenario=st_notguard_violation())
    def test_notguard_failure_routes_to_matching_corrective(
        self, scenario: tuple[WriteOperation, str]
    ) -> None:
        """A failed NOT-guard yields ``INTERCEPT_CORRECTIVE`` with its category.

        Args:
            scenario: A ``(WriteOperation, expected_category)`` pair where the
                write violates exactly one NOT-guard.
        """
        op, expected_category = scenario
        prompt = load_gate_prompt()

        decision = gate(op, prompt)

        assert decision.outcome == INTERCEPT_CORRECTIVE
        assert decision.category == expected_category
        # The silent pass-through must have been declined: a corrective outcome
        # means the write was held (intercepted) and evaluated against checks.
        assert decision.intercepted is True
