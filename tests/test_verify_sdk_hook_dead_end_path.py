"""Bug condition exploration test for the SDK-verify hook dead-end path.

Spec: .kiro/specs/sdk-verify-hook-dead-end-path

The Module 2 verification hook ``senzing-bootcamp/hooks/verify-sdk-setup.json``
recommends ``python3 senzing-bootcamp/scripts/preflight.py`` as a remediation
command when verification fails. That power-relative path does not resolve in the
bootcamper's installed project workspace, producing a "No such file or directory"
dead end.

This module encodes the EXPECTED (fixed) behavior. On the UNFIXED hook it MUST
FAIL — the failure surfaces the counterexample and confirms the bug exists. After
the fix repoints the remediation command to ``python3 src/scripts/verify_sdk.py``,
these assertions pass.
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# Make the tests directory importable so hook_test_helpers resolves when pytest
# collects from the repo root.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

import hook_test_helpers

HOOK_PATH = Path("senzing-bootcamp/hooks/verify-sdk-setup.json")

# The power-relative remediation path that does NOT resolve in the bootcamper
# workspace (the bug), and the workspace-relative path that does (the fix).
DEAD_END_PATH = "senzing-bootcamp/scripts/preflight.py"
DEAD_END_DIR = "senzing-bootcamp/scripts/"
WORKSPACE_PATH = "src/scripts/verify_sdk.py"


def _then_prompt() -> str:
    """Load the real hook and return its v1 ``action.prompt`` string."""
    hook = hook_test_helpers.load_hook(HOOK_PATH)
    return hook["action"]["prompt"]


class TestVerifySdkRemediationPath:
    """Property 1: Bug Condition - Remediation Path Resolves In Workspace.

    **Validates: Requirements 1.1, 1.2, 2.1, 2.2**
    """

    def test_no_power_relative_remediation_path(self):
        """then.prompt must NOT recommend the unresolvable power-relative path.

        Fails on the unfixed hook (counterexample: the prompt contains
        ``python3 senzing-bootcamp/scripts/preflight.py``).
        """
        prompt = _then_prompt()
        assert DEAD_END_PATH not in prompt, (
            "then.prompt recommends the power-relative remediation path "
            f"{DEAD_END_PATH!r}, which does not resolve in the bootcamper workspace "
            "(produces 'No such file or directory')."
        )

    def test_workspace_resolvable_remediation_path_present(self):
        """then.prompt must recommend the workspace-resolvable script path.

        Fails on the unfixed hook (the prompt does not yet reference
        ``src/scripts/verify_sdk.py``).
        """
        prompt = _then_prompt()
        assert WORKSPACE_PATH in prompt, (
            f"then.prompt does not recommend the workspace-resolvable path "
            f"{WORKSPACE_PATH!r}."
        )

    def test_no_power_relative_scripts_dir_anywhere(self):
        """Edge case: no ``senzing-bootcamp/scripts/`` substring may remain.

        Catches any power-relative scripts path, not just preflight.py.
        """
        prompt = _then_prompt()
        assert DEAD_END_DIR not in prompt, (
            f"then.prompt still contains a power-relative scripts path "
            f"({DEAD_END_DIR!r}), which does not resolve in the bootcamper workspace."
        )

    @given(
        suffix=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz_./",
            min_size=0,
            max_size=40,
        )
    )
    @settings(max_examples=20)
    def test_recommended_path_never_power_relative_form(self, suffix: str):
        """Generated path-resolution check: the recommended remediation path
        must never match the power-relative ``senzing-bootcamp/scripts/...`` form.

        For any generated script suffix, the prompt's recommended command must
        not point at ``senzing-bootcamp/scripts/<suffix>`` because such a path
        does not resolve in the bootcamper workspace.
        """
        prompt = _then_prompt()
        power_relative_candidate = f"{DEAD_END_DIR}{suffix}"
        assert power_relative_candidate not in prompt, (
            "then.prompt recommends a power-relative path "
            f"{power_relative_candidate!r}, which does not resolve in the "
            "bootcamper workspace."
        )


# ---------------------------------------------------------------------------
# Preservation baseline (observed on the UNFIXED hook)
# ---------------------------------------------------------------------------

# The legacy ``when.patterns`` globs collapsed into the single 1.0 matcher regex;
# the scoping intent (config/senzing_config.*, config/bootcamp_preferences.yaml,
# database/*.*) must be preserved as fragments of that matcher.
EXPECTED_MATCHER_FRAGMENTS = [
    "senzing_config",
    "bootcamp_preferences",
    "database/",
]
EXPECTED_TRIGGER = "PostFileSave"
EXPECTED_ACTION_TYPE = "agent"

# Module 2 gating phrases (Req 3.3).
GATING_IN_MODULE_2 = "If the bootcamper is in Module 2 (SDK Setup)"
GATING_NOT_IN_MODULE_2 = "If not in Module 2, produce no output"

# Verification check phrases (Req 3.1).
CHECK_DATABASE = "database/G2C.db exists and is accessible"
CHECK_ENGINE_INIT = "the Senzing engine can initialize with the current config"

# Genuine-failure reporting phrase (Req 3.2).
FAILURE_REPORTING = "If verification fails, present the error"

# Phrases that must be invariant across any module context (Req 3.1, 3.2, 3.3).
INVARIANT_PHRASES = [
    GATING_IN_MODULE_2,
    GATING_NOT_IN_MODULE_2,
    CHECK_DATABASE,
    CHECK_ENGINE_INIT,
    FAILURE_REPORTING,
]


def st_module_context() -> st.SearchStrategy[str]:
    """Strategy generating module-context descriptions ("in Module 2" / not).

    These represent the runtime context the hook prompt is gated on. The
    gating and verification phrases must remain present and invariant
    regardless of which context the bootcamper is in.
    """
    return st.sampled_from(
        [
            "in Module 2",
            "in Module 2 (SDK Setup)",
            "not in Module 2",
            "in Module 1",
            "in Module 5",
            "between modules",
        ]
    )


class TestVerifySdkPreservation:
    """Property 2: Preservation - Verification, Gating, and Trigger Behavior Unchanged.

    Observation-first: these assertions encode behavior observed on the UNFIXED
    hook. They MUST PASS on the unfixed hook, establishing the baseline that the
    remediation-path fix must preserve byte-for-byte (except the single
    remediation substring covered by Property 1).

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """

    def test_matcher_preserves_scoping_fragments(self):
        """The 1.0 matcher preserves the original file-scoping fragments (Req 3.4)."""
        hook = hook_test_helpers.load_hook(HOOK_PATH)
        matcher = hook.get("matcher", "")
        assert isinstance(matcher, str) and matcher, "hook must carry a matcher"
        for fragment in EXPECTED_MATCHER_FRAGMENTS:
            assert fragment in matcher, (
                f"matcher {matcher!r} lost scoping fragment {fragment!r}"
            )

    def test_trigger_is_post_file_save(self):
        """trigger is PostFileSave (1.0 rename of fileEdited) (Req 3.4)."""
        hook = hook_test_helpers.load_hook(HOOK_PATH)
        assert hook["trigger"] == EXPECTED_TRIGGER

    def test_module_2_gating_preserved(self):
        """then.prompt retains the Module 2 gating and no-output branch (Req 3.3)."""
        prompt = _then_prompt()
        assert GATING_IN_MODULE_2 in prompt
        assert GATING_NOT_IN_MODULE_2 in prompt

    def test_verification_checks_preserved(self):
        """then.prompt retains the database and engine-init checks (Req 3.1)."""
        prompt = _then_prompt()
        assert CHECK_DATABASE in prompt
        assert CHECK_ENGINE_INIT in prompt

    def test_genuine_failure_reporting_preserved(self):
        """then.prompt retains the failure-reporting instruction (Req 3.2)."""
        prompt = _then_prompt()
        assert FAILURE_REPORTING in prompt

    def test_schema_integrity_preserved(self):
        """Hook retains required v1 fields and well-formed schema (Req 3.1-3.4)."""
        hook = hook_test_helpers.load_hook(HOOK_PATH)
        for field in ("name", "trigger", "action"):
            assert field in hook, f"missing required field {field!r}"
        assert hook["action"]["type"] == EXPECTED_ACTION_TYPE
        prompt = hook["action"]["prompt"]
        assert isinstance(prompt, str)
        assert prompt.strip(), "action.prompt must be a non-empty string"

    def test_hook_file_parses_as_valid_json(self):
        """The hook file on disk parses as a valid v1 wrapper (Req 3.1-3.4)."""
        import json

        parsed = json.loads(HOOK_PATH.read_text(encoding="utf-8"))
        assert isinstance(parsed, dict)
        assert parsed.get("version") == "v1"
        assert isinstance(parsed.get("hooks"), list) and parsed["hooks"]

    @given(context=st_module_context())
    @settings(max_examples=20)
    def test_gating_and_verification_phrases_invariant(self, context: str):
        """For any module context, the gating/verification phrases remain present.

        The hook prompt's instructions are gated on whether the bootcamper is in
        Module 2, but the phrasing itself is static in then.prompt. For every
        generated context ("in Module 2" / "not in Module 2"), all invariant
        phrases must be present and unchanged.
        """
        prompt = _then_prompt()
        for phrase in INVARIANT_PHRASES:
            assert phrase in prompt, (
                f"invariant phrase {phrase!r} missing from then.prompt for "
                f"context {context!r}"
            )
