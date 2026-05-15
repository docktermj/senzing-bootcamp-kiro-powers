"""Bug condition exploration tests for file-path-hook-stall bugfix.

These tests verify the hook has an explicit fast-path with silent processing
instructions for compliant writes, preventing agent stalls during multi-file edits.

Feature: fix-file-path-hook-stall

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

Note: The original bug was that the hook had no explicit fast-path instruction,
requiring the agent to infer retry behavior from silence. The fix uses silent
processing ("Do not acknowledge. Do not explain. Do not print anything. Proceed
silently.") rather than an explicit "policy: pass" output signal. This achieves
the same goal — preventing stalls — without adding visible output noise.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_HOOK_FILE = _BOOTCAMP_DIR / "hooks" / "enforce-file-path-policies.kiro.hook"
_AGENT_INSTRUCTIONS = _BOOTCAMP_DIR / "steering" / "agent-instructions.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_hook() -> dict:
    """Parse the hook file as JSON and return the dict."""
    return json.loads(_HOOK_FILE.read_text(encoding="utf-8"))


def _read_hook_prompt() -> str:
    """Extract the then.prompt field from the hook file."""
    hook = _read_hook()
    return hook.get("then", {}).get("prompt", "")


def _read_agent_instructions() -> str:
    """Read the full content of agent-instructions.md."""
    return _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Regex patterns for expected (fixed) behavior
# ---------------------------------------------------------------------------

# The fix uses silent processing instead of "policy: pass" output.
# The fast-path must contain explicit silent-proceed instructions.
_SILENT_PROCESSING_PATTERN = re.compile(
    r"do\s+not\s+acknowledge.*do\s+not\s+explain.*do\s+not\s+print",
    re.IGNORECASE | re.DOTALL,
)

_FAST_PATH_PATTERN = re.compile(
    r"fast\s*path",
    re.IGNORECASE,
)

_RETRY_MANDATE_PATTERN = re.compile(
    r"(immediately\s+retry\s+the\s+original\s+tool\s+call|"
    r"MUST\s+immediately\s+retry\s+the\s+original\s+tool\s+call|"
    r"retry\s+the\s+original\s+tool\s+call\s+with\s+(exactly\s+)?the\s+same\s+parameters)",
    re.IGNORECASE,
)

_PRETOOLUSE_RETRY_RULE = re.compile(
    r"preToolUse\s+retry\s+rule",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Test 1 — Explicit Silent Processing in Hook Prompt
# ---------------------------------------------------------------------------


class TestMissingExplicitPassSignal:
    """Test 1 — Explicit Silent Processing Signal.

    **Validates: Requirements 1.2, 1.4**

    Parse the hook prompt and assert it contains explicit silent processing
    instructions on the fast path. The fix uses "Do not acknowledge. Do not
    explain. Do not print anything. Proceed silently." as the explicit
    instruction that prevents agent stalls (no inference required).
    """

    def test_hook_prompt_contains_policy_pass(self) -> None:
        """The hook prompt must contain explicit silent processing instructions."""
        prompt = _read_hook_prompt()
        assert _SILENT_PROCESSING_PATTERN.search(prompt), (
            "Bug condition: The hook prompt does NOT contain explicit silent "
            "processing instructions ('Do not acknowledge. Do not explain. "
            "Do not print anything.'). Without explicit instructions, the "
            "agent must infer behavior, leading to stalls. "
            f"Prompt excerpt: ...{prompt[-200:]}"
        )


# ---------------------------------------------------------------------------
# Test 2 — Fast-Path Condition Exists
# ---------------------------------------------------------------------------


class TestMissingFastPath:
    """Test 2 — Fast-Path Condition Exists.

    **Validates: Requirements 1.1, 1.2**

    Parse the hook prompt and assert it contains a FAST PATH section
    with explicit silent processing instructions for project-relative
    non-feedback writes.
    """

    def test_hook_prompt_contains_fast_path(self) -> None:
        """The hook prompt must contain a FAST PATH with silent processing."""
        prompt = _read_hook_prompt()
        assert _FAST_PATH_PATTERN.search(prompt), (
            "Bug condition: The hook prompt does NOT contain a "
            "FAST PATH section for project-relative non-feedback writes. "
            "Without a fast path, the hook evaluates the full policy check "
            "unconditionally on every write, creating cumulative attention "
            "cost during multi-file edits. "
            f"Prompt excerpt: {prompt[:300]}"
        )


# ---------------------------------------------------------------------------
# Test 3 — Missing Retry Mandate in Agent Instructions
# ---------------------------------------------------------------------------


class TestMissingRetryMandate:
    """Test 3 — Missing Retry Mandate in Agent Instructions.

    **Validates: Requirements 1.3, 1.4**

    Parse agent-instructions.md and assert it contains an explicit
    "retry the original tool call" mandate for preToolUse hooks.
    On unfixed code this will FAIL because only the silence rule exists
    (produce zero output) with no explicit retry mandate.
    """

    def test_agent_instructions_contains_retry_mandate(self) -> None:
        """Agent instructions must contain an explicit retry mandate."""
        content = _read_agent_instructions()
        assert _RETRY_MANDATE_PATTERN.search(content), (
            "Bug condition confirmed: agent-instructions.md does NOT contain "
            "an explicit 'retry the original tool call' mandate for preToolUse "
            "hooks. Only the silence rule exists ('produce zero output') which "
            "requires the agent to infer that it should retry. Under cumulative "
            "attention load, this inferential step fails and the agent stalls. "
            f"Hooks section excerpt: {content[content.find('## Hooks'):content.find('## Hooks') + 500]}"
        )

    def test_agent_instructions_contains_pretooluse_retry_rule(self) -> None:
        """Agent instructions must contain a named 'preToolUse retry rule'."""
        content = _read_agent_instructions()
        assert _PRETOOLUSE_RETRY_RULE.search(content), (
            "Bug condition confirmed: agent-instructions.md does NOT contain "
            "a named 'preToolUse retry rule' section. Without an explicit, "
            "named rule, the agent has no unambiguous directive to retry "
            "after a no-violation hook intercept."
        )


# ---------------------------------------------------------------------------
# PBT Test — Bug Condition: No Explicit Pass Signal for Compliant Writes
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Strategies for preservation tests
# ---------------------------------------------------------------------------

_EXTERNAL_PATHS = ["/tmp/", "%TEMP%", "~/Downloads"]

_EXTERNAL_PATH_EXAMPLES = [
    "/tmp/test.py",
    "/tmp/data/output.csv",
    "%TEMP%/scratch.txt",
    "%TEMP%/build/artifact.bin",
    "~/Downloads/report.pdf",
    "~/Downloads/data/input.json",
]

_FEEDBACK_PATH_VARIANTS = [
    "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md",
    "SENZING_BOOTCAMP_POWER_FEEDBACK.md",
]


# ---------------------------------------------------------------------------
# Strategies for bug condition tests
# ---------------------------------------------------------------------------


@st.composite
def st_project_relative_path(draw: st.DrawFn) -> str:
    """Generate random project-relative file paths (the common case)."""
    directories = [
        "src", "src/transform", "src/load", "src/query", "src/utils",
        "data", "data/raw", "data/transformed", "config", "scripts",
        "tests", "docs", "database", "logs",
    ]
    extensions = [".py", ".js", ".ts", ".html", ".css", ".json", ".yaml", ".md", ".sql"]
    filename = draw(st.from_regex(r"[a-z][a-z0-9_]{1,20}", fullmatch=True))
    directory = draw(st.sampled_from(directories))
    extension = draw(st.sampled_from(extensions))
    return f"{directory}/{filename}{extension}"


class TestNoExplicitPassSignalForCompliantWrites:
    """PBT Test — Explicit Fast-Path Instructions for Compliant Writes.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

    Use Hypothesis to generate random project-relative paths and assert
    the hook prompt contains an explicit fast-path with silent processing
    instructions for these common-case writes.

    The fix uses silent processing instructions ("Do not acknowledge. Do not
    explain. Do not print anything. Proceed silently.") which gives the agent
    an unambiguous directive — no inference required, preventing stalls.
    """

    @given(path=st_project_relative_path())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_hook_provides_explicit_pass_for_project_relative_paths(
        self, path: str
    ) -> None:
        """For any project-relative path, the hook prompt must provide an
        explicit fast-path with silent processing instructions rather than
        requiring the agent to infer behavior from silence.

        The fix ensures: targetPath is project-relative AND content has no
        external references AND write is not misrouted feedback → the hook
        fast-path explicitly instructs silent processing (no inference needed).
        """
        prompt = _read_hook_prompt()

        # The hook prompt MUST contain both:
        # 1. An explicit silent processing instruction
        has_silent_processing = bool(_SILENT_PROCESSING_PATTERN.search(prompt))
        # 2. A fast-path section for project-relative non-feedback writes
        has_fast_path = bool(_FAST_PATH_PATTERN.search(prompt))

        assert has_silent_processing and has_fast_path, (
            f"Bug condition for path '{path}': The hook prompt "
            f"does NOT provide an explicit fast-path with silent processing "
            f"instructions for project-relative non-feedback writes. "
            f"has_silent_processing={has_silent_processing}, has_fast_path={has_fast_path}. "
            f"Without explicit instructions, the agent must infer behavior, "
            f"which fails under cumulative load during multi-file edits."
        )


# ===========================================================================
# PRESERVATION PROPERTY TESTS — Verify existing behavior to preserve
# ===========================================================================
# These tests PASS on unfixed code. They establish a baseline of violation-
# detection behavior that must remain intact after the fix is applied.
# ===========================================================================


# ---------------------------------------------------------------------------
# Regex patterns for preservation checks
# ---------------------------------------------------------------------------

_STOP_EXTERNAL_PATH_PATTERN = re.compile(
    r"(STOP|stop|do\s+not\s+proceed).*("
    r"/tmp/|%TEMP%|~/Downloads|outside\s+the\s+working\s+directory"
    r")",
    re.IGNORECASE | re.DOTALL,
)

_FEEDBACK_REDIRECT_PATTERN = re.compile(
    r"(redirect|STOP|verify).*docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK\.md"
    r"|docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK\.md.*(redirect|STOP|verify)",
    re.IGNORECASE | re.DOTALL,
)

_CONTENT_PATH_CHECK_PATTERN = re.compile(
    r"(file\s+(path|content)|path\s+in\s+the\s+file\s+content|any\s+path\s+in\s+the\s+file"
    r"|content\s+reference).*(/tmp/|%TEMP%|~/Downloads|outside\s+the\s+working\s+directory)",
    re.IGNORECASE | re.DOTALL,
)


# ---------------------------------------------------------------------------
# Test Class: External Path Blocking Preserved
# ---------------------------------------------------------------------------


class TestExternalPathBlockingPreserved:
    """Preservation Test — External Path Blocking.

    **Validates: Requirements 3.1, 3.5**

    Verify the hook prompt contains instructions to STOP for paths outside
    the working directory. This behavior must be preserved after the fix.
    """

    @given(path=st.sampled_from(_EXTERNAL_PATH_EXAMPLES))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_hook_prompt_blocks_external_paths(self, path: str) -> None:
        """For any external path pattern, the hook prompt must contain
        instructions to STOP or not proceed.

        The hook prompt references /tmp/, %TEMP%, ~/Downloads and instructs
        the agent to not proceed if the file path targets these locations.
        """
        prompt = _read_hook_prompt()

        # The prompt must reference the external path prefix used in this example
        path_prefix = None
        for prefix in _EXTERNAL_PATHS:
            if path.startswith(prefix) or prefix in path:
                path_prefix = prefix
                break

        assert path_prefix is not None, f"Test setup error: {path} doesn't match any external prefix"
        assert path_prefix in prompt, (
            f"Hook prompt must reference external path prefix '{path_prefix}' "
            f"to block writes to paths like '{path}'. "
            f"Prompt: {prompt[:200]}"
        )

    def test_hook_prompt_contains_stop_for_external_paths(self) -> None:
        """The hook prompt must instruct the agent to STOP/not proceed for external paths."""
        prompt = _read_hook_prompt()
        assert _STOP_EXTERNAL_PATH_PATTERN.search(prompt), (
            "Preservation check: The hook prompt must contain instructions to "
            "STOP or 'Do NOT proceed' for paths outside the working directory. "
            f"Prompt: {prompt[:300]}"
        )


# ---------------------------------------------------------------------------
# Test Class: Feedback Path Enforcement Preserved
# ---------------------------------------------------------------------------


class TestFeedbackPathEnforcementPreserved:
    """Preservation Test — Feedback Path Enforcement.

    **Validates: Requirements 3.2, 3.5**

    Verify the hook prompt contains instructions to redirect feedback to
    docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md. This behavior must
    be preserved after the fix.
    """

    @given(path_variant=st.sampled_from(_FEEDBACK_PATH_VARIANTS))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_hook_prompt_enforces_feedback_path(self, path_variant: str) -> None:
        """The hook prompt must reference the canonical feedback path."""
        prompt = _read_hook_prompt()
        # The canonical path must appear in the prompt
        canonical = "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md"
        assert canonical in prompt, (
            f"Preservation check: The hook prompt must reference the canonical "
            f"feedback path '{canonical}' to enforce feedback routing. "
            f"Checking variant: '{path_variant}'. "
            f"Prompt: {prompt[:300]}"
        )

    def test_hook_prompt_contains_feedback_redirect_instruction(self) -> None:
        """The hook prompt must instruct the agent to redirect/STOP for misrouted feedback."""
        prompt = _read_hook_prompt()
        assert _FEEDBACK_REDIRECT_PATTERN.search(prompt), (
            "Preservation check: The hook prompt must contain instructions to "
            "redirect or STOP when feedback is written to the wrong path. "
            f"Prompt: {prompt[:300]}"
        )


# ---------------------------------------------------------------------------
# Test Class: Content Path Check Preserved
# ---------------------------------------------------------------------------


class TestContentPathCheckPreserved:
    """Preservation Test — Content Path Check.

    **Validates: Requirements 3.3, 3.5**

    Verify the hook prompt contains instructions to check file content for
    external path references. This behavior must be preserved after the fix.
    """

    @given(external_ref=st.sampled_from(_EXTERNAL_PATHS))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_hook_prompt_checks_content_for_external_refs(self, external_ref: str) -> None:
        """The hook prompt must check file content for external path references."""
        prompt = _read_hook_prompt()
        # The prompt must mention checking content/paths for external references
        assert external_ref in prompt, (
            f"Preservation check: The hook prompt must reference '{external_ref}' "
            f"to detect external path references in file content. "
            f"Prompt: {prompt[:300]}"
        )

    def test_hook_prompt_contains_content_path_check_instruction(self) -> None:
        """The hook prompt must instruct checking file content for external path references."""
        prompt = _read_hook_prompt()
        assert _CONTENT_PATH_CHECK_PATTERN.search(prompt), (
            "Preservation check: The hook prompt must contain instructions to "
            "check file content for external path references (/tmp/, %TEMP%, "
            "~/Downloads, or outside the working directory). "
            f"Prompt: {prompt[:300]}"
        )


# ---------------------------------------------------------------------------
# Test Class: Hook Event Config Preserved
# ---------------------------------------------------------------------------


class TestHookEventConfigPreserved:
    """Preservation Test — Hook Event Configuration.

    **Validates: Requirements 3.4, 3.5**

    Verify the hook's when.type is "preToolUse" and when.toolTypes contains
    "write". This configuration must be preserved after the fix.
    """

    def test_hook_when_type_is_pretooluse(self) -> None:
        """The hook's when.type must be 'preToolUse'."""
        hook = _read_hook()
        when = hook.get("when", {})
        assert when.get("type") == "preToolUse", (
            f"Preservation check: Hook when.type must be 'preToolUse', "
            f"got '{when.get('type')}'"
        )

    def test_hook_when_tooltypes_contains_write(self) -> None:
        """The hook's when.toolTypes must contain 'write'."""
        hook = _read_hook()
        when = hook.get("when", {})
        tool_types = when.get("toolTypes", [])
        assert "write" in tool_types, (
            f"Preservation check: Hook when.toolTypes must contain 'write', "
            f"got {tool_types}"
        )

    @given(field=st.sampled_from(["type", "toolTypes"]))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_hook_when_config_fields_exist(self, field: str) -> None:
        """The hook's when configuration must contain required fields."""
        hook = _read_hook()
        when = hook.get("when", {})
        assert field in when, (
            f"Preservation check: Hook 'when' config must contain field '{field}', "
            f"got keys: {list(when.keys())}"
        )


# ---------------------------------------------------------------------------
# Test Class: Hook JSON Validity
# ---------------------------------------------------------------------------


class TestHookJsonValidity:
    """Preservation Test — Hook JSON Validity.

    **Validates: Requirements 3.4**

    Verify the hook file parses as valid JSON and contains required fields.
    """

    def test_hook_file_is_valid_json(self) -> None:
        """The hook file must parse as valid JSON."""
        content = _HOOK_FILE.read_text(encoding="utf-8")
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise AssertionError(
                f"Preservation check: Hook file is not valid JSON: {e}"
            ) from e
        assert isinstance(data, dict), (
            f"Preservation check: Hook file must be a JSON object, got {type(data).__name__}"
        )

    @given(field=st.sampled_from(["name", "version", "description", "when", "then"]))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_hook_contains_required_fields(self, field: str) -> None:
        """The hook JSON must contain all required top-level fields."""
        hook = _read_hook()
        assert field in hook, (
            f"Preservation check: Hook JSON must contain field '{field}', "
            f"got keys: {list(hook.keys())}"
        )

    def test_hook_then_type_is_askagent(self) -> None:
        """The hook's then.type must be 'askAgent'."""
        hook = _read_hook()
        then = hook.get("then", {})
        assert then.get("type") == "askAgent", (
            f"Preservation check: Hook then.type must be 'askAgent', "
            f"got '{then.get('type')}'"
        )

    def test_hook_then_prompt_is_nonempty_string(self) -> None:
        """The hook's then.prompt must be a non-empty string."""
        hook = _read_hook()
        prompt = hook.get("then", {}).get("prompt", "")
        assert isinstance(prompt, str) and len(prompt) > 0, (
            "Preservation check: Hook then.prompt must be a non-empty string"
        )
