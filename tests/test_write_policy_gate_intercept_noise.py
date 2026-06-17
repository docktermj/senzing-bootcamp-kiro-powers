"""Bug condition exploration test for write-policy-gate intercept noise.

Property 1: Bug Condition — Power-Managed Internal Files Bypass Intercept Noise.

This test encodes the EXPECTED (fixed) behavior: for any write where the bug
condition holds — a routine power-managed internal file that is NOT
`.question_pending`, NOT the feedback file, contains NO Senzing SQL, and is NOT
a root-blocked placement — the gate SHALL exclude the write from intercept-retry
processing so it completes (``PASS_SILENT``) and NO "Rejected creation of ..."
message is produced.

It is designed to FAIL on the *unfixed* gate prompt (which has no INTERNAL-FILE
PASS-THROUGH clause and therefore still intercepts these writes, producing the
noisy "Rejected" -> "Accepted" pair). The failure confirms the bug exists. When
re-run against the fixed prompt (design Change A), this same test PASSES,
validating the fix.

**Validates: Requirements 1.1, 1.2, 2.1, 2.2**
"""

from __future__ import annotations

import string

from hypothesis import example, given, settings
from hypothesis import strategies as st

from gate_decision_model import (
    PASS_SILENT,
    WriteOperation,
    gate,
    is_bug_condition,
    load_gate_prompt,
    produces_rejected_message,
)

# ---------------------------------------------------------------------------
# Clean (non-SQL, non-Senzing) content generators
# ---------------------------------------------------------------------------

# Safe alphabet for keys/values — avoids SQL keywords and Senzing indicators.
_SAFE_TEXT = st.text(
    alphabet=string.ascii_lowercase + string.digits + " _-.",
    min_size=1,
    max_size=20,
)


def _st_clean_json() -> st.SearchStrategy[str]:
    """Clean JSON content with no Senzing SQL."""
    return st.builds(
        lambda step, status: (
            '{"step": %d, "status": "%s", "completed": true}' % (step, status)
        ),
        step=st.integers(min_value=1, max_value=60),
        status=st.sampled_from(["done", "in_progress", "pending", "started"]),
    )


def _st_clean_yaml() -> st.SearchStrategy[str]:
    """Clean YAML content with no Senzing SQL."""
    return st.builds(
        lambda name, level: (
            "language: %s\nverbosity: %s\nnotifications: enabled\n" % (name, level)
        ),
        name=st.sampled_from(["python", "java", "rust", "typescript", "csharp"]),
        level=st.sampled_from(["low", "medium", "high"]),
    )


def _st_clean_markdown() -> st.SearchStrategy[str]:
    """Clean Markdown log content with no Senzing SQL."""
    return st.builds(
        lambda title, body: "# %s\n\n%s\n" % (title, body),
        title=_SAFE_TEXT,
        body=_SAFE_TEXT,
    )


def _st_member_id() -> st.SearchStrategy[str]:
    """Member identifier for colocated team-mode files."""
    return st.text(
        alphabet=string.ascii_lowercase + string.digits + "_-",
        min_size=1,
        max_size=12,
    )


@st.composite
def st_internal_file_write(draw) -> WriteOperation:
    """Generate a power-managed internal-file write with clean content.

    Covers every member of the internal-file set: the two fixed config files,
    member-scoped progress/preference files, and power-written session/recap
    log files.
    """
    tool = draw(st.sampled_from(["fs_write", "fs_append", "str_replace"]))
    kind = draw(
        st.sampled_from(
            [
                "progress",
                "preferences",
                "member_progress",
                "member_preferences",
                "power_log",
            ]
        )
    )
    if kind == "progress":
        path = "config/bootcamp_progress.json"
        content = draw(_st_clean_json())
    elif kind == "preferences":
        path = "config/bootcamp_preferences.yaml"
        content = draw(_st_clean_yaml())
    elif kind == "member_progress":
        path = "config/progress_%s.json" % draw(_st_member_id())
        content = draw(_st_clean_json())
    elif kind == "member_preferences":
        path = "config/preferences_%s.yaml" % draw(_st_member_id())
        content = draw(_st_clean_yaml())
    else:  # power_log
        module = draw(st.integers(min_value=1, max_value=11))
        path = "docs/progress/MODULE_%d_COMPLETE.md" % module
        content = draw(_st_clean_markdown())
    return WriteOperation(path=path, content=content, tool=tool)


# ---------------------------------------------------------------------------
# Property 1: Bug Condition
# ---------------------------------------------------------------------------

class TestBugConditionInternalFilePassThrough:
    """Property 1 — power-managed internal files bypass intercept noise.

    **Validates: Requirements 1.1, 1.2, 2.1, 2.2**

    For all W where ``isBugCondition(W)`` holds, the gate SHALL return
    ``PASS_SILENT`` and produce NO "Rejected"/corrective message.

    On the UNFIXED prompt this FAILS (no internal-file pass-through clause, so
    the write is still intercepted). On the FIXED prompt it PASSES.
    """

    @given(op=st_internal_file_write())
    @settings(max_examples=200)
    # Anchor concrete failing cases for reproducibility.
    @example(
        op=WriteOperation(
            "config/bootcamp_progress.json", '{"step": 1, "status": "done"}'
        )
    )
    @example(
        op=WriteOperation(
            "config/bootcamp_preferences.yaml", "language: python\n"
        )
    )
    @example(
        op=WriteOperation(
            "config/progress_alice.json", '{"step": 3, "status": "done"}'
        )
    )
    @example(
        op=WriteOperation(
            "config/preferences_alice.yaml", "language: java\n"
        )
    )
    @example(
        op=WriteOperation(
            "docs/progress/MODULE_3_COMPLETE.md", "# Module 3 complete\n"
        )
    )
    def test_internal_file_write_passes_without_rejected_message(
        self, op: WriteOperation
    ):
        """Bug-condition internal-file writes complete silently with no
        "Rejected" message.

        **Validates: Requirements 1.1, 1.2, 2.1, 2.2**
        """
        # Sanity: the generated write is genuinely a bug-condition input.
        assert is_bug_condition(op), (
            f"generator produced a non-bug-condition write: {op.path}"
        )

        prompt = load_gate_prompt()
        decision = gate(op, prompt)

        # Expected (fixed) behavior: silent pass with no intercept-retry noise.
        assert decision.outcome == PASS_SILENT, (
            f"Property 1 FAILED: internal-file write to '{op.path}' did not "
            f"PASS_SILENT (got {decision.outcome}, category={decision.category})."
        )
        assert not produces_rejected_message(decision), (
            f"Property 1 FAILED: internal-file write to '{op.path}' is still "
            f"processed through normal interception (held write), producing the "
            f"noisy 'Rejected creation of ...' -> 'Accepted edits to ...' pair. "
            f"The gate has no INTERNAL-FILE PASS-THROUGH clause excluding "
            f"power-managed internal files. "
            f"(tool={op.tool}, content={op.content!r})"
        )
