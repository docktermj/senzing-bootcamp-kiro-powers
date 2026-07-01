"""Tests for the module-recap-append hook prompt Paired_Schema wording.

Validates that the `module-recap-append.kiro.hook` prompt instructs the agent to
author the recap using the Paired_Schema (a single `### Questions & Responses`
section with interspersed `- **Q:**` / `- **R:**` items, four-space response
indentation, a `- None` item when there are no substantive questions, and the
`(no response recorded)` placeholder) and no longer instructs writing the legacy
split `### Questions Asked` / `### Answers Given` sections.

The rewritten prompt still MENTIONS the legacy headings once, inside a prohibition
sentence telling the agent to NEVER emit them. The tests therefore do not assert
those strings are absent; they assert every occurrence sits in a prohibition
context rather than an authoring instruction.

**Validates: Requirements 1.1, 1.3, 1.4, 1.5, 1.6, 2.1**
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Locate the hook file relative to the repo root (this file lives in repo-root
# tests/, so the repo root is its parent's parent).
_REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = _REPO_ROOT / "senzing-bootcamp" / "hooks" / "module-recap-append.kiro.hook"

# Literal Paired_Schema tokens the prompt MUST describe.
REQUIRED_TOKENS: list[str] = [
    "### Questions & Responses",
    "- **Q:**",
    "- **R:**",
    "- None",
    "(no response recorded)",
]

# The legacy split-list headings that must only ever appear in a prohibition.
LEGACY_HEADINGS: list[str] = [
    "### Questions Asked",
    "### Answers Given",
]

# Words that signal a prohibition context around a legacy-heading mention.
PROHIBITION_MARKERS: list[str] = ["never", "not", "no longer", "don't", "do not"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_hook() -> dict:
    """Load and parse the hook JSON file."""
    with open(HOOK_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_prompt() -> str:
    """Return the then.prompt string from the hook."""
    return load_hook()["then"]["prompt"]


def _mention_is_prohibited(prompt: str, needle: str) -> bool:
    """Return True if every occurrence of ``needle`` sits in a prohibition context.

    A mention is considered prohibited when a prohibition marker (e.g. "NEVER")
    appears within the sentence-sized window of ~120 characters preceding the
    mention. Authoring instructions ("write a ### Questions Asked section") would
    lack such a marker and fail this check.

    Args:
        prompt: The full hook prompt text.
        needle: The legacy heading string to locate.

    Returns:
        True if all occurrences are in a prohibition context (or there are none).
    """
    lowered = prompt.lower()
    needle_lower = needle.lower()
    start = 0
    while True:
        idx = lowered.find(needle_lower, start)
        if idx == -1:
            return True
        window = lowered[max(0, idx - 120):idx]
        if not any(marker in window for marker in PROHIBITION_MARKERS):
            return False
        start = idx + len(needle_lower)


# ---------------------------------------------------------------------------
# Test Class
# ---------------------------------------------------------------------------


class TestModuleRecapAppendQRPrompt:
    """Verify the module-recap-append hook prompt describes the Paired_Schema.

    **Validates: Requirements 1.1, 1.3, 1.4, 1.5, 1.6, 2.1**
    """

    def test_hook_json_is_valid_and_well_formed(self) -> None:
        """The hook file SHALL be valid JSON with name, version, when, then."""
        data = load_hook()
        for field in ("name", "version", "when", "then"):
            assert field in data, f"Hook JSON missing required top-level field '{field}'"
        assert isinstance(data["then"], dict), "'then' must be an object"
        assert isinstance(data["then"].get("prompt"), str) and data["then"]["prompt"], (
            "'then.prompt' must be a non-empty string"
        )

    def test_prompt_describes_paired_schema_heading(self) -> None:
        """The prompt SHALL reference the single `### Questions & Responses` heading.

        **Validates: Requirements 1.1**
        """
        prompt = load_prompt()
        assert "### Questions & Responses" in prompt, (
            "Hook prompt does not describe the '### Questions & Responses' heading"
        )

    def test_prompt_describes_qr_prefixes(self) -> None:
        """The prompt SHALL describe the `- **Q:**` and `- **R:**` item prefixes.

        **Validates: Requirements 1.3**
        """
        prompt = load_prompt()
        assert "- **Q:**" in prompt, "Hook prompt does not describe the '- **Q:**' prefix"
        assert "- **R:**" in prompt, "Hook prompt does not describe the '- **R:**' prefix"

    def test_prompt_describes_none_placeholder_for_zero_questions(self) -> None:
        """The prompt SHALL describe emitting `- None` for zero substantive questions.

        **Validates: Requirements 1.5**
        """
        prompt = load_prompt()
        assert "- None" in prompt, (
            "Hook prompt does not describe the '- None' item for zero questions"
        )

    def test_prompt_describes_no_response_placeholder(self) -> None:
        """The prompt SHALL describe the `(no response recorded)` placeholder.

        **Validates: Requirements 1.6**
        """
        prompt = load_prompt()
        assert "(no response recorded)" in prompt, (
            "Hook prompt does not describe the '(no response recorded)' placeholder"
        )

    def test_prompt_describes_four_space_indentation(self) -> None:
        """The prompt SHALL describe four-space indentation of response items.

        **Validates: Requirements 2.1**
        """
        prompt = load_prompt()
        lowered = prompt.lower()
        assert (
            "four leading space" in lowered
            or "four-space" in lowered
            or "four spaces" in lowered
        ), (
            "Hook prompt does not describe four leading spaces / four-space "
            "indentation for the response item"
        )

    def test_all_required_tokens_present(self) -> None:
        """Every Paired_Schema token SHALL appear in the prompt.

        **Validates: Requirements 1.1, 1.3, 1.5, 1.6**
        """
        prompt = load_prompt()
        for token in REQUIRED_TOKENS:
            assert token in prompt, f"Hook prompt missing required token '{token}'"

    def test_legacy_headings_only_appear_in_prohibition(self) -> None:
        """Legacy split headings SHALL appear only in a prohibition, never as
        an authoring instruction to write them.

        **Validates: Requirements 1.4**
        """
        prompt = load_prompt()
        for heading in LEGACY_HEADINGS:
            assert _mention_is_prohibited(prompt, heading), (
                f"Hook prompt appears to INSTRUCT writing '{heading}' outside a "
                f"prohibition context — the Paired_Schema must not author the "
                f"legacy split-list sections"
            )

    def test_prompt_does_not_emit_legacy_headings_in_template(self) -> None:
        """The prompt SHALL NOT contain a template line that emits a legacy heading.

        A template emission would look like a heading on its own line (optionally
        after whitespace/escaped newline) that is not part of a prohibition
        sentence. We assert no legacy heading is immediately preceded by a newline
        marker used for the append template block.

        **Validates: Requirements 1.4**
        """
        prompt = load_prompt()
        for heading in LEGACY_HEADINGS:
            # A template block emits headings after an (escaped or literal) newline.
            pattern = re.compile(r"\n\s*" + re.escape(heading))
            assert not pattern.search(prompt), (
                f"Hook prompt contains a template emission of '{heading}' on its "
                f"own line — the Paired_Schema template must not write it"
            )
