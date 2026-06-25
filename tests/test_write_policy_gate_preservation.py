"""Preservation property tests for the write-policy-gate UX bugfix.

Property 2: Preservation — Governed Writes Behave Identically.

For any write where the bug condition does NOT hold
(``is_bug_condition(W)`` is False), the fixed gate SHALL produce exactly the
same outcome as the original gate, preserving every genuine policy enforcement
(Senzing SQL blocking, single-question rule, feedback append-only guard, root
file placement, external-path redirect) and the ``preToolUse`` held-write /
re-issue-of-identical-write semantics for every governed file.

Observation-first methodology
-----------------------------
The gate decision model reads the *live* hook prompt on every call. The only
behavioral difference the fix introduces (design Change A) is an INTERNAL-FILE
PASS-THROUGH clause that fires *only* when ``is_bug_condition(W)`` is True.
Therefore, for every ``NOT is_bug_condition(W)`` input the decision must be
**independent of whether the pass-through clause is present**.

These tests capture that invariant directly and robustly:

1. They observe the UNFIXED prompt's decision for governed/clean inputs and
   assert the concrete expected outcome per preservation case (the baseline to
   preserve).
2. They build a *simulated fixed prompt* (the live prompt with the pass-through
   clause text injected) and assert ``gate(op, unfixed) == gate(op, fixed)``
   for every non-bug-condition input.

Because (2) compares the decision across the exact change the fix will make,
the assertions hold on the unfixed prompt now AND continue to hold after the
real pass-through clause is added (the clause only changes bug-condition
inputs). Running on UNFIXED code, all tests PASS — confirming the baseline.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
"""

from __future__ import annotations

import string

from hypothesis import assume, example, given, settings
from hypothesis import strategies as st

from gate_decision_model import (
    FEEDBACK_FILE,
    INTERCEPT_CORRECTIVE,
    PASS_SILENT,
    GateDecision,
    WriteOperation,
    contains_senzing_sql,
    gate,
    is_bug_condition,
    is_root_blocked_placement,
    load_gate_prompt,
    produces_rejected_message,
    prompt_has_internal_pass_through,
)

# ---------------------------------------------------------------------------
# Prompt fixtures: the live (unfixed) prompt and a simulated fixed prompt
# ---------------------------------------------------------------------------

# Minimal text that makes ``prompt_has_internal_pass_through`` report True,
# simulating design Change A without yet editing the live hook file. The fix
# only changes behavior for bug-condition inputs, so injecting the clause must
# NOT alter any NOT-bug-condition decision.
_SIMULATED_PASS_THROUGH_CLAUSE = (
    "\n\n## INTERNAL-FILE PASS-THROUGH\n"
    "If the target path is a routine power-managed internal file (and NOT "
    "config/.question_pending, NOT the feedback file, NOT a root-blocked "
    "placement, and the content contains NO Senzing SQL), produce ZERO tokens "
    "and re-invoke the tool silently.\n"
)


def _unfixed_prompt() -> str:
    """Load the live (currently unfixed) gate prompt."""
    return load_gate_prompt()


def _simulated_fixed_prompt() -> str:
    """Live prompt with the pass-through clause injected (simulated fix)."""
    return _unfixed_prompt() + _SIMULATED_PASS_THROUGH_CLAUSE


def _assert_preserved(op: WriteOperation) -> GateDecision:
    """Assert the decision is identical with and without the pass-through clause.

    This is the core preservation invariant: for a NOT-bug-condition write, the
    presence of the INTERNAL-FILE PASS-THROUGH clause must not change anything.

    Returns:
        The (identical) decision under the unfixed prompt, for callers that
        also want to assert a concrete expected outcome.
    """
    assert not is_bug_condition(op), (
        f"test setup error: {op.path!r} is a bug-condition input; preservation "
        f"tests must only cover NOT-bug-condition writes"
    )

    unfixed = gate(op, _unfixed_prompt())
    fixed = gate(op, _simulated_fixed_prompt())

    assert fixed == unfixed, (
        f"Preservation FAILED: decision changed for non-bug-condition write to "
        f"'{op.path}' (tool={op.tool}). unfixed={unfixed}, fixed={fixed}. The "
        f"INTERNAL-FILE PASS-THROUGH clause must never affect a governed/clean "
        f"write."
    )
    # Sanity: the simulated clause really is present in the fixed prompt and
    # absent from the unfixed one, so the comparison above is meaningful.
    assert prompt_has_internal_pass_through(_simulated_fixed_prompt())
    return unfixed


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_SAFE_TEXT = st.text(
    alphabet=string.ascii_lowercase + string.digits + " _-./",
    min_size=0,
    max_size=24,
)


def _st_senzing_sql_content() -> st.SearchStrategy[str]:
    """Content containing an SQL pattern targeting a Senzing DB indicator."""
    return st.builds(
        lambda verb, indicator: f"{verb} * FROM {indicator} WHERE id > 0;",
        verb=st.sampled_from(
            [
                "SELECT",
                "INSERT INTO",
                "UPDATE",
                "DELETE FROM",
                "CREATE TABLE",
                "DROP TABLE",
                "ALTER TABLE",
                "PRAGMA",
            ]
        ),
        indicator=st.sampled_from(
            [
                "RES_ENT",
                "OBS_ENT",
                "RES_FEAT_STAT",
                "DSRC_RECORD",
                "LIB_FEAT",
                "RES_REL",
                "SZ_ENTITY",
                "sz_dm_record",
                "G2C.db",
                "database/G2C.db",
            ]
        ),
    )


def _st_any_path() -> st.SearchStrategy[str]:
    """Arbitrary-ish destination paths (used with SQL content, any path)."""
    return st.sampled_from(
        [
            "src/load_data.py",
            "src/query/run.py",
            "scripts/migrate.py",
            "notebooks/explore.md",
            "config/bootcamp_progress.json",  # internal name, but SQL content
            "docs/notes.md",
            "data/export.sql",
            "main.py",
        ]
    )


@st.composite
def st_senzing_sql_write(draw) -> WriteOperation:
    """A write whose content contains Senzing SQL (governed on any path)."""
    tool = draw(st.sampled_from(["fs_write", "fs_append", "str_replace"]))
    return WriteOperation(
        path=draw(_st_any_path()),
        content=draw(_st_senzing_sql_content()),
        tool=tool,
    )


def _st_compound_question() -> st.SearchStrategy[str]:
    """Compound / ambiguous `.question_pending` content."""
    return st.sampled_from(
        [
            "Which language do you prefer, and should I enable notifications?",
            "Do you want Python? Or Java?",
            "Ready to start? Also, what is your name?",
            "Shall I proceed or alternatively pick defaults?",
            "Continue? And do you want verbose output?",
        ]
    )


@st.composite
def st_question_pending_compound_write(draw) -> WriteOperation:
    """A `.question_pending` write with a compound question (governed)."""
    base = draw(st.sampled_from(["config/.question_pending", ".question_pending"]))
    return WriteOperation(
        path=base,
        content=draw(_st_compound_question()),
        tool=draw(st.sampled_from(["fs_write", "str_replace"])),
    )


@st.composite
def st_feedback_overwrite_write(draw) -> WriteOperation:
    """A feedback-file overwrite/edit (governed: append-only guard)."""
    return WriteOperation(
        path=FEEDBACK_FILE,
        content=draw(_SAFE_TEXT),
        tool=draw(st.sampled_from(["fs_write", "str_replace"])),
    )


@st.composite
def st_feedback_append_write(draw) -> WriteOperation:
    """A feedback-file append (allowed: passes the append-only guard)."""
    return WriteOperation(
        path=FEEDBACK_FILE,
        content=draw(_SAFE_TEXT),
        tool="fs_append",
    )


@st.composite
def st_root_blocked_write(draw) -> WriteOperation:
    """A blocked-extension file placed in the project root (governed)."""
    name = draw(
        st.sampled_from(
            [
                "main.py",
                "data.jsonl",
                "records.csv",
                "notes.md",
                "results.json",  # non-whitelisted .json
                "progress.json",
                "analysis.py",
            ]
        )
    )
    return WriteOperation(
        path=name,
        content=draw(_SAFE_TEXT),
        tool=draw(st.sampled_from(["fs_write", "str_replace", "fs_append"])),
    )


@st.composite
def st_external_path_write(draw) -> WriteOperation:
    """A write to a path outside the working directory (governed: redirect)."""
    prefix = draw(st.sampled_from(["/tmp/", "%TEMP%", "~/Downloads", "/var/", "C:\\"]))
    leaf = draw(st.sampled_from(["out.json", "scratch.py", "notes.md", "data.csv"]))
    sep = "" if prefix.endswith(("/", "\\")) else "/"
    return WriteOperation(
        path=f"{prefix}{sep}{leaf}",
        content=draw(_SAFE_TEXT),
        tool=draw(st.sampled_from(["fs_write", "str_replace", "fs_append"])),
    )


@st.composite
def st_clean_ordinary_write(draw) -> WriteOperation:
    """An ordinary project-relative clean write (fast path: PASS_SILENT)."""
    path = draw(
        st.sampled_from(
            [
                "src/load.py",
                "src/query/run.py",
                "src/models/entity.py",
                "scripts/helper.py",
                "docs/notes.md",
                "tests/test_thing.py",
            ]
        )
    )
    return WriteOperation(
        path=path,
        content=draw(_SAFE_TEXT.filter(lambda s: not contains_senzing_sql(s))),
        tool=draw(st.sampled_from(["fs_write", "fs_append", "str_replace"])),
    )


@st.composite
def st_near_miss_write(draw) -> WriteOperation:
    """Near-misses to the internal-file set that must NOT be excluded.

    - ``config/.question_pending`` (governed by the single-question rule)
    - ``config/notes.py`` (a bootcamper file living under config/)
    - root ``progress.json`` (a root-blocked placement that *looks* internal)
    """
    kind = draw(st.sampled_from(["question_pending", "config_py", "root_progress"]))
    if kind == "question_pending":
        # Non-compound content so it is not caught by Check 2 — the point is
        # that it still must NOT be treated as an excludable internal file.
        return WriteOperation(
            path="config/.question_pending",
            content=draw(st.sampled_from(["Ready to start?", "Pick a language?"])),
            tool=draw(st.sampled_from(["fs_write", "str_replace"])),
        )
    if kind == "config_py":
        return WriteOperation(
            path="config/notes.py",
            content=draw(_SAFE_TEXT.filter(lambda s: not contains_senzing_sql(s))),
            tool=draw(st.sampled_from(["fs_write", "fs_append", "str_replace"])),
        )
    return WriteOperation(
        path="progress.json",
        content=draw(_SAFE_TEXT.filter(lambda s: not contains_senzing_sql(s))),
        tool=draw(st.sampled_from(["fs_write", "str_replace"])),
    )


@st.composite
def st_non_bug_condition_write(draw) -> WriteOperation:
    """Union generator over the whole NOT-bug-condition input domain."""
    op = draw(
        st.one_of(
            st_senzing_sql_write(),
            st_question_pending_compound_write(),
            st_feedback_overwrite_write(),
            st_feedback_append_write(),
            st_root_blocked_write(),
            st_external_path_write(),
            st_clean_ordinary_write(),
            st_near_miss_write(),
        )
    )
    # Guard the domain: these tests only cover NOT-bug-condition writes.
    assume(not is_bug_condition(op))
    return op


# ===========================================================================
# Property 2: Preservation — per-case baseline observation + invariant
# ===========================================================================

class TestSqlBlockingPreservation:
    """Senzing-SQL content stays INTERCEPT_CORRECTIVE on any path.

    **Validates: Requirements 3.1**
    """

    @given(op=st_senzing_sql_write())
    @settings(max_examples=150)
    @example(
        op=WriteOperation("src/load.py", "SELECT * FROM RES_ENT;", "fs_write")
    )
    @example(
        op=WriteOperation(
            "config/bootcamp_progress.json",
            "DROP TABLE OBS_ENT;",
            "fs_write",
        )
    )
    def test_senzing_sql_still_blocked(self, op: WriteOperation):
        """SQL content is intercepted with the SDK-redirect category, and the
        outcome is unchanged by the pass-through clause.

        **Validates: Requirements 3.1**
        """
        assert contains_senzing_sql(op.content)
        decision = _assert_preserved(op)
        assert decision.outcome == INTERCEPT_CORRECTIVE
        assert decision.category == "senzing_sql"
        assert produces_rejected_message(decision)


class TestSingleQuestionPreservation:
    """`.question_pending` compound questions stay governed (not shadowed).

    **Validates: Requirements 3.2**
    """

    @given(op=st_question_pending_compound_write())
    @settings(max_examples=100)
    @example(
        op=WriteOperation(
            "config/.question_pending",
            "Which language, and enable notifications?",
            "fs_write",
        )
    )
    def test_compound_question_still_intercepted(self, op: WriteOperation):
        """Compound `.question_pending` writes remain INTERCEPT_CORRECTIVE; the
        internal-file exclusion does NOT shadow `config/.question_pending`.

        **Validates: Requirements 3.2**
        """
        decision = _assert_preserved(op)
        assert decision.outcome == INTERCEPT_CORRECTIVE
        assert decision.category == "single_question"
        assert produces_rejected_message(decision)


class TestFeedbackAppendOnlyPreservation:
    """Feedback overwrite/edit blocked; append passes — unchanged by the fix.

    **Validates: Requirements 3.3**
    """

    @given(op=st_feedback_overwrite_write())
    @settings(max_examples=80)
    @example(op=WriteOperation(FEEDBACK_FILE, "rewritten", "fs_write"))
    @example(op=WriteOperation(FEEDBACK_FILE, "edited", "str_replace"))
    def test_feedback_overwrite_still_blocked(self, op: WriteOperation):
        """`fs_write`/`str_replace` on the feedback file stays blocked.

        **Validates: Requirements 3.3**
        """
        decision = _assert_preserved(op)
        assert decision.outcome == INTERCEPT_CORRECTIVE
        assert decision.category == "feedback_append_only"
        assert produces_rejected_message(decision)

    @given(op=st_feedback_append_write())
    @settings(max_examples=80)
    @example(op=WriteOperation(FEEDBACK_FILE, "new entry", "fs_append"))
    def test_feedback_append_still_passes(self, op: WriteOperation):
        """`fs_append` to the feedback file continues to pass the guard.

        **Validates: Requirements 3.3**
        """
        decision = _assert_preserved(op)
        assert decision.outcome == PASS_SILENT


class TestRootPlacementPreservation:
    """Root-blocked placements stay INTERCEPT_CORRECTIVE (routed).

    **Validates: Requirements 3.4**
    """

    @given(op=st_root_blocked_write())
    @settings(max_examples=120)
    @example(op=WriteOperation("main.py", "print('hi')", "fs_write"))
    @example(op=WriteOperation("data.jsonl", '{"a": 1}', "fs_write"))
    @example(op=WriteOperation("results.json", "{}", "fs_write"))
    def test_root_blocked_still_routed(self, op: WriteOperation):
        """Blocked-extension root files remain intercepted for routing.

        **Validates: Requirements 3.4**
        """
        assert is_root_blocked_placement(op.path)
        decision = _assert_preserved(op)
        assert decision.outcome == INTERCEPT_CORRECTIVE
        assert decision.category == "root_placement"
        assert produces_rejected_message(decision)


class TestExternalPathPreservation:
    """External-path writes stay INTERCEPT_CORRECTIVE (redirected).

    **Validates: Requirements 3.5**
    """

    @given(op=st_external_path_write())
    @settings(max_examples=120)
    @example(op=WriteOperation("/tmp/out.json", "{}", "fs_write"))
    @example(op=WriteOperation("%TEMP%/scratch.py", "x = 1", "fs_write"))
    @example(op=WriteOperation("~/Downloads/data.csv", "a,b", "fs_write"))
    def test_external_path_still_redirected(self, op: WriteOperation):
        """Out-of-working-directory writes remain intercepted for redirect.

        **Validates: Requirements 3.5**
        """
        decision = _assert_preserved(op)
        assert decision.outcome == INTERCEPT_CORRECTIVE
        assert decision.category == "external_path"
        assert produces_rejected_message(decision)


class TestCleanWriteFastPathPreservation:
    """Ordinary clean writes stay PASS_SILENT and keep preToolUse semantics.

    **Validates: Requirements 3.6**
    """

    @given(op=st_clean_ordinary_write())
    @settings(max_examples=120)
    @example(op=WriteOperation("src/load.py", "import os", "fs_write"))
    def test_clean_write_still_passes_silent(self, op: WriteOperation):
        """A clean `src/...` write passes silently — but is still held by the
        preToolUse hook (held-write/re-issue semantics preserved).

        **Validates: Requirements 3.6**
        """
        decision = _assert_preserved(op)
        assert decision.outcome == PASS_SILENT
        # preToolUse held-write semantics: a non-excluded clean write is still
        # intercepted (this is exactly the cosmetic behavior the fix leaves
        # intact for non-internal files).
        assert decision.intercepted is True


class TestPreToolUseSemanticsPreservation:
    """Every governed write remains held (intercepted) by the preToolUse hook.

    **Validates: Requirements 3.6**
    """

    @given(
        op=st.one_of(
            st_senzing_sql_write(),
            st_question_pending_compound_write(),
            st_feedback_overwrite_write(),
            st_root_blocked_write(),
            st_external_path_write(),
        )
    )
    @settings(max_examples=150)
    def test_governed_writes_remain_intercepted(self, op: WriteOperation):
        """Held-write then re-issue-of-identical-write semantics are preserved
        for every governed file (the write is intercepted in both prompts).

        **Validates: Requirements 3.6**
        """
        assume(not is_bug_condition(op))
        decision = _assert_preserved(op)
        assert decision.intercepted is True
        assert produces_rejected_message(decision)


class TestNearMissNotExcluded:
    """Near-misses to the internal-file set are NOT excluded by the fix.

    **Validates: Requirements 3.2, 3.4, 3.6**
    """

    @given(op=st_near_miss_write())
    @settings(max_examples=120)
    @example(op=WriteOperation("config/.question_pending", "Ready?", "fs_write"))
    @example(op=WriteOperation("config/notes.py", "x = 1", "fs_write"))
    @example(op=WriteOperation("progress.json", "{}", "fs_write"))
    def test_near_miss_is_not_bug_condition_and_preserved(
        self, op: WriteOperation
    ):
        """`config/.question_pending`, `config/notes.py`, and root
        `progress.json` are NOT internal-file exclusions: they are not
        bug-condition inputs and their decisions are unchanged by the clause.

        **Validates: Requirements 3.2, 3.4, 3.6**
        """
        assert not is_bug_condition(op), (
            f"near-miss '{op.path}' must NOT be classified as a bug-condition "
            f"(excludable) internal file"
        )
        # And the decision is identical with/without the pass-through clause.
        _assert_preserved(op)


class TestPreservationAcrossInputDomain:
    """Global invariant: NO non-bug-condition decision changes under the fix.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
    """

    @given(op=st_non_bug_condition_write())
    @settings(max_examples=400)
    def test_decision_independent_of_pass_through_clause(
        self, op: WriteOperation
    ):
        """For every NOT-bug-condition write across the input domain, the gate
        decision is identical with and without the INTERNAL-FILE PASS-THROUGH
        clause — i.e., gate(op, fixed) == gate(op, unfixed).

        **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
        """
        _assert_preserved(op)
