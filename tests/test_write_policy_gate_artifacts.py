"""Unit tests for the write-policy-gate decision model and artifact integrity.

These tests validate the *fixed* artifacts produced by the write-policy-gate UX
bugfix (design Changes A and B):

- The fixed hook prompt
  (``senzing-bootcamp/hooks/write-policy-gate.kiro.hook``) contains the
  INTERNAL-FILE PASS-THROUGH clause and its explicit NOT-guards.
- The hook JSON remains schema-valid and still declares a ``preToolUse`` write
  hook (``toolTypes: ["write"]``), per the security steering — the write hook is
  never removed or weakened.
- Each routine power-managed internal file in the defined set maps to
  ``PASS_SILENT`` in the decision model, while ``config/.question_pending`` does
  NOT (the exclusion must not shadow a governed file).
- The onboarding documentation
  (``senzing-bootcamp/steering/onboarding-flow.md``) explains the intercept-retry
  cycle (Property 3).

Unlike the Property 1/2 property-based suites, these are concrete example-based
unit tests asserting the integrity of the shipped artifacts after the fix.

**Validates: Requirements 2.1, 2.2, 2.3, 3.2, 3.6**
"""

from __future__ import annotations

import json
from pathlib import Path

from gate_decision_model import (
    FEEDBACK_FILE,
    HOOK_PATH,
    PASS_SILENT,
    WriteOperation,
    gate,
    is_bug_condition,
    is_power_managed_internal_file,
    load_gate_prompt,
    prompt_has_internal_pass_through,
)

# ---------------------------------------------------------------------------
# Artifact paths
# ---------------------------------------------------------------------------

ONBOARDING_DOC: Path = Path("senzing-bootcamp/steering/onboarding-flow.md")

# The concrete internal-file set defined in the design (Fix Implementation).
INTERNAL_FILE_SET: tuple[str, ...] = (
    "config/bootcamp_progress.json",
    "config/bootcamp_preferences.yaml",
    "config/progress_alice.json",
    "config/preferences_alice.yaml",
    "docs/progress/MODULE_3_COMPLETE.md",
)


def _clean_content_for(path: str) -> str:
    """Return clean (non-Senzing-SQL) content appropriate for the path.

    Args:
        path: The target file path.

    Returns:
        Content that contains no SQL pattern or Senzing indicator.
    """
    if path.endswith(".json"):
        return '{"step": 3, "status": "done", "completed": true}'
    if path.endswith(".yaml"):
        return "language: python\nverbosity: medium\n"
    return "# Module complete\n\nNice work.\n"


# ===========================================================================
# Hook prompt clause integrity (design Change A)
# ===========================================================================

class TestFixedHookPromptClause:
    """The fixed hook prompt carries the pass-through clause and NOT-guards.

    **Validates: Requirements 2.1, 2.2**
    """

    def test_prompt_contains_internal_file_pass_through_clause(self) -> None:
        """The prompt declares an INTERNAL-FILE PASS-THROUGH clause.

        **Validates: Requirements 2.1, 2.2**
        """
        prompt = load_gate_prompt()
        assert prompt_has_internal_pass_through(prompt), (
            "fixed gate prompt is missing the INTERNAL-FILE PASS-THROUGH clause"
        )

    def test_prompt_declares_not_guards(self) -> None:
        """The pass-through is guarded by the four explicit NOT clauses.

        The clause must apply ONLY when the path is NOT
        ``config/.question_pending``, NOT the feedback file, NOT a root-blocked
        placement, and the content contains NO Senzing SQL.

        **Validates: Requirements 2.1, 2.2**
        """
        prompt = load_gate_prompt()
        lowered = prompt.lower()

        # NOT-guard: .question_pending
        assert ".question_pending" in prompt
        # NOT-guard: feedback file
        assert FEEDBACK_FILE in prompt
        # NOT-guard: root-blocked placement
        assert "root-blocked placement" in lowered
        # NOT-guard: no Senzing SQL
        assert "no senzing sql" in lowered

    def test_prompt_evaluates_pass_through_before_fast_path(self) -> None:
        """The pass-through clause is positioned before the FAST PATH GATE.

        **Validates: Requirements 2.1, 2.2**
        """
        prompt = load_gate_prompt()
        pass_through_idx = prompt.find("INTERNAL-FILE PASS-THROUGH")
        fast_path_idx = prompt.find("FAST PATH GATE")
        assert pass_through_idx != -1, "pass-through clause not found"
        assert fast_path_idx != -1, "FAST PATH GATE not found"
        assert pass_through_idx < fast_path_idx, (
            "INTERNAL-FILE PASS-THROUGH must be evaluated before the FAST PATH GATE"
        )

    def test_prompt_enumerates_internal_file_set(self) -> None:
        """The prompt enumerates the exact internal-file set (no over-match).

        **Validates: Requirements 2.1, 2.2**
        """
        prompt = load_gate_prompt()
        assert "config/bootcamp_progress.json" in prompt
        assert "config/bootcamp_preferences.yaml" in prompt
        assert "config/progress_{id}.json" in prompt
        assert "config/preferences_{id}.yaml" in prompt
        assert "docs/progress/MODULE_*_COMPLETE.md" in prompt


# ===========================================================================
# Hook JSON schema integrity (security steering)
# ===========================================================================

class TestHookJsonSchema:
    """The hook JSON stays schema-valid and keeps the preToolUse write hook.

    **Validates: Requirements 3.6**
    """

    def _load_hook(self) -> dict:
        """Load and parse the live hook JSON.

        Returns:
            The parsed hook object.
        """
        with open(HOOK_PATH, encoding="utf-8") as f:
            return json.load(f)

    def test_hook_json_is_valid_json(self) -> None:
        """The hook file parses as JSON.

        **Validates: Requirements 3.6**
        """
        hook = self._load_hook()
        assert isinstance(hook, dict)

    def test_hook_has_required_schema_fields(self) -> None:
        """The hook declares ``name``, ``version``, ``when``, and ``then``.

        **Validates: Requirements 3.6**
        """
        hook = self._load_hook()
        for field in ("name", "version", "when", "then"):
            assert field in hook, f"hook JSON missing required field: {field}"

    def test_hook_declares_pretooluse_write(self) -> None:
        """The hook still declares ``preToolUse`` with ``toolTypes: ["write"]``.

        The security steering forbids removing or weakening the write hook.

        **Validates: Requirements 3.6**
        """
        hook = self._load_hook()
        when = hook["when"]
        assert when.get("type") == "preToolUse", (
            "hook must remain a preToolUse hook"
        )
        assert when.get("toolTypes") == ["write"], (
            'hook must retain toolTypes: ["write"]'
        )

    def test_hook_then_has_prompt(self) -> None:
        """The ``then`` block carries the gate prompt.

        **Validates: Requirements 3.6**
        """
        hook = self._load_hook()
        then = hook["then"]
        assert "prompt" in then
        assert isinstance(then["prompt"], str)
        assert then["prompt"].strip() != ""


# ===========================================================================
# Decision model on the internal-file set (design Change A behavior)
# ===========================================================================

class TestInternalFileSetPassesSilent:
    """Each defined internal-file path maps to PASS_SILENT under the fix.

    **Validates: Requirements 2.1, 2.2**
    """

    def test_each_internal_file_passes_silent(self) -> None:
        """Every path in the internal-file set is excluded (PASS_SILENT, no
        "Rejected" message) under the fixed prompt.

        **Validates: Requirements 2.1, 2.2**
        """
        prompt = load_gate_prompt()
        for path in INTERNAL_FILE_SET:
            op = WriteOperation(path=path, content=_clean_content_for(path))
            assert is_power_managed_internal_file(path), (
                f"{path} should be recognized as a power-managed internal file"
            )
            assert is_bug_condition(op), (
                f"{path} with clean content should be a bug-condition input"
            )
            decision = gate(op, prompt)
            assert decision.outcome == PASS_SILENT, (
                f"internal file '{path}' did not PASS_SILENT "
                f"(got {decision.outcome}, category={decision.category})"
            )
            assert decision.intercepted is False, (
                f"internal file '{path}' should be excluded from interception "
                f"(no 'Rejected' message)"
            )


class TestQuestionPendingNotExcluded:
    """``config/.question_pending`` must NOT be excluded by the pass-through.

    **Validates: Requirements 3.2**
    """

    def test_question_pending_does_not_pass_silent_when_compound(self) -> None:
        """A compound-question ``config/.question_pending`` write stays governed
        (INTERCEPT_CORRECTIVE) — the exclusion does not shadow it.

        **Validates: Requirements 3.2**
        """
        op = WriteOperation(
            path="config/.question_pending",
            content="Which language, and should I enable notifications?",
            tool="fs_write",
        )
        assert not is_bug_condition(op), (
            "config/.question_pending must never be a bug-condition input"
        )
        decision = gate(op, load_gate_prompt())
        assert decision.outcome != PASS_SILENT, (
            "compound config/.question_pending must remain intercepted"
        )
        assert decision.intercepted is True

    def test_question_pending_is_not_power_managed_internal(self) -> None:
        """``config/.question_pending`` is not classified as an internal file.

        **Validates: Requirements 3.2**
        """
        assert not is_power_managed_internal_file("config/.question_pending")


# ===========================================================================
# Onboarding documentation integrity (design Change B / Property 3)
# ===========================================================================

class TestOnboardingDocumentation:
    """Onboarding explains the intercept-retry cycle is expected and harmless.

    **Validates: Requirements 2.3**
    """

    def _load_doc(self) -> str:
        """Load the onboarding documentation text.

        Returns:
            The onboarding-flow.md file contents.
        """
        with open(ONBOARDING_DOC, encoding="utf-8") as f:
            return f.read()

    def test_onboarding_explains_rejected_accepted_cycle(self) -> None:
        """The onboarding doc references both "Rejected" and "Accepted edits".

        **Validates: Requirements 2.3**
        """
        doc = self._load_doc()
        assert "Rejected" in doc
        assert "Accepted edits" in doc

    def test_onboarding_names_the_write_policy_gate(self) -> None:
        """The explanation attributes the cycle to the write-policy-gate check.

        **Validates: Requirements 2.3**
        """
        doc = self._load_doc()
        assert "write-policy-gate" in doc

    def test_onboarding_reassures_no_data_loss_on_retry(self) -> None:
        """The explanation states writes succeed on retry and no data is lost.

        **Validates: Requirements 2.3**
        """
        lowered = self._load_doc().lower()
        assert "succeed on retry" in lowered
        assert "no data is lost" in lowered
        assert "expected and harmless" in lowered
