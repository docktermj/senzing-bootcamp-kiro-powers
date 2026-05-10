"""Shared helper module for hook test coverage.

Provides constants, file loading utilities, validation functions,
a minimal YAML parser, and Hypothesis strategies for property-based testing.
"""

from __future__ import annotations

import json
import re
import string
from fnmatch import fnmatch
from pathlib import Path

from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOKS_DIR: Path = Path("senzing-bootcamp/hooks")
CATEGORIES_PATH: Path = HOOKS_DIR / "hook-categories.yaml"

VALID_EVENT_TYPES: set[str] = {
    "promptSubmit",
    "preToolUse",
    "postToolUse",
    "fileEdited",
    "fileCreated",
    "fileDeleted",
    "agentStop",
    "userTriggered",
    "postTaskExecution",
    "preTaskExecution",
}

REQUIRED_FIELDS: list[str] = [
    "name",
    "version",
    "description",
    "when.type",
    "then.type",
    "then.prompt",
]

FILE_EVENT_TYPES: set[str] = {"fileEdited", "fileCreated", "fileDeleted"}
TOOL_EVENT_TYPES: set[str] = {"preToolUse", "postToolUse"}

CRITICAL_HOOKS: list[str] = [
    "ask-bootcamper",
    "review-bootcamper-input",
    "code-style-check",
    "commonmark-validation",
    "enforce-feedback-path",
    "enforce-working-directory",
    "verify-senzing-facts",
]

SEMVER_PATTERN: re.Pattern[str] = re.compile(
    r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)$"
)

# Silent-processing detection patterns
SILENT_PROCESSING_PATTERNS: list[str] = [
    r"produce no output at all",
    r"do nothing",
    r"do not acknowledge.*do not explain.*do not print",
]


# ---------------------------------------------------------------------------
# Hook file loading utilities
# ---------------------------------------------------------------------------

def get_hook_files() -> list[Path]:
    """Return all .kiro.hook file paths in the hooks directory, sorted."""
    assert HOOKS_DIR.is_dir(), f"Hooks directory not found at {HOOKS_DIR}"
    return sorted(HOOKS_DIR.glob("*.kiro.hook"))


def load_hook(path: Path) -> dict:
    """Load and parse a single .kiro.hook JSON file.

    Args:
        path: Path to the hook file.

    Returns:
        Parsed JSON dict.

    Raises:
        json.JSONDecodeError: If the file is not valid JSON.
    """
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_all_hooks() -> list[tuple[str, dict]]:
    """Load all .kiro.hook files from the hooks directory.

    Returns:
        List of (hook_id, parsed_json_dict) tuples where hook_id is the
        filename without the .kiro.hook extension.
    """
    results = []
    for path in get_hook_files():
        hook_id = path.name.replace(".kiro.hook", "")
        data = load_hook(path)
        results.append((hook_id, data))
    return results


# ---------------------------------------------------------------------------
# Minimal YAML parser for hook-categories.yaml
# ---------------------------------------------------------------------------

def parse_categories_yaml(path: Path | None = None) -> dict[str, list[str]]:
    """Parse hook-categories.yaml into a flat category -> hook_ids mapping.

    Handles the specific structure of hook-categories.yaml:
    - Top-level keys: 'critical', 'modules'
    - Under 'modules': numbered keys (1, 2, ...) and 'any'
    - Each leaf is a list of hook identifier strings

    Returns a flat dict mapping category names to lists of hook identifiers:
    - "critical" -> [7 hook ids]
    - "module-1" -> [hook ids for module 1]
    - "module-any" -> [hook ids for 'any' module]

    Args:
        path: Path to the YAML file. Defaults to CATEGORIES_PATH.

    Returns:
        Dict mapping category name to list of hook identifiers.

    Raises:
        ValueError: If the YAML structure is malformed.
    """
    if path is None:
        path = CATEGORIES_PATH

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    categories: dict[str, list[str]] = {}
    current_top_key: str | None = None
    current_module_key: str | None = None

    for line_num, line in enumerate(lines, start=1):
        # Skip comments and blank lines
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            continue

        # Detect indentation level
        indent = len(line) - len(line.lstrip())

        # Top-level key (no indentation): "critical:" or "modules:"
        if indent == 0 and stripped.endswith(":"):
            current_top_key = stripped[:-1].strip()
            current_module_key = None
            if current_top_key == "critical":
                categories["critical"] = []
            continue

        # Module sub-key (2-space indent): "  1:" or "  any:"
        if indent == 2 and stripped.endswith(":") and current_top_key == "modules":
            key_name = stripped.strip()[:-1]
            current_module_key = f"module-{key_name}"
            categories[current_module_key] = []
            continue

        # List item (various indent levels): "  - hook-name" or "    - hook-name"
        item_match = re.match(r"^\s+-\s+(.+)$", stripped)
        if item_match:
            hook_id = item_match.group(1).strip()
            if current_top_key == "critical" and current_module_key is None:
                categories.setdefault("critical", []).append(hook_id)
            elif current_module_key is not None:
                categories.setdefault(current_module_key, []).append(hook_id)
            else:
                raise ValueError(
                    f"Line {line_num}: list item '{hook_id}' outside a known category"
                )
            continue

    return categories


# ---------------------------------------------------------------------------
# Validation functions
# ---------------------------------------------------------------------------

def validate_required_fields(hook_data: dict) -> list[str]:
    """Check that all REQUIRED_FIELDS are present using dot-notation traversal.

    Args:
        hook_data: Parsed hook JSON dict.

    Returns:
        List of missing field names (empty if all present).
    """
    missing = []
    for field in REQUIRED_FIELDS:
        parts = field.split(".")
        obj = hook_data
        found = True
        for part in parts:
            if isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                found = False
                break
        if not found:
            missing.append(field)
    return missing


def validate_conditional_fields(hook_data: dict) -> list[str]:
    """Check conditional fields based on event type.

    File events require non-empty when.patterns.
    Tool events require non-empty when.toolTypes.

    Args:
        hook_data: Parsed hook JSON dict.

    Returns:
        List of validation error messages (empty if all valid).
    """
    errors = []
    when = hook_data.get("when", {})
    event_type = when.get("type", "")

    if event_type in FILE_EVENT_TYPES:
        patterns = when.get("patterns")
        if not patterns or not isinstance(patterns, list) or len(patterns) == 0:
            errors.append(
                f'event type "{event_type}" requires non-empty when.patterns'
            )

    if event_type in TOOL_EVENT_TYPES:
        tool_types = when.get("toolTypes")
        if not tool_types or not isinstance(tool_types, list) or len(tool_types) == 0:
            errors.append(
                f'event type "{event_type}" requires non-empty when.toolTypes'
            )

    return errors


def validate_event_type(event_type: str) -> bool:
    """Return True if event_type is a valid hook event type.

    Args:
        event_type: String to validate.

    Returns:
        True if valid, False otherwise.
    """
    return event_type in VALID_EVENT_TYPES


def validate_version(version: str) -> bool:
    """Return True if version matches semver format with no leading zeros.

    Valid format: <major>.<minor>.<patch> where each component is a
    non-negative integer without leading zeros.

    Args:
        version: String to validate.

    Returns:
        True if valid semver, False otherwise.
    """
    return SEMVER_PATTERN.match(version) is not None


# ---------------------------------------------------------------------------
# Prompt analysis helpers
# ---------------------------------------------------------------------------

def has_silent_processing(prompt: str) -> bool:
    """Return True if the prompt contains a silent-processing instruction.

    Args:
        prompt: Hook prompt text to check.

    Returns:
        True if any silent-processing pattern matches.
    """
    for pattern in SILENT_PROCESSING_PATTERNS:
        if re.search(pattern, prompt, re.IGNORECASE):
            return True
    return False


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

def st_valid_semver() -> st.SearchStrategy[str]:
    """Strategy generating valid semantic version strings (no leading zeros)."""
    return st.builds(
        lambda major, minor, patch: f"{major}.{minor}.{patch}",
        major=st.integers(min_value=0, max_value=99),
        minor=st.integers(min_value=0, max_value=99),
        patch=st.integers(min_value=0, max_value=99),
    )


def st_invalid_semver() -> st.SearchStrategy[str]:
    """Strategy generating strings that are NOT valid semver."""
    return st.one_of(
        # Leading zeros
        st.builds(
            lambda minor, patch: f"01.{minor}.{patch}",
            minor=st.integers(min_value=0, max_value=9),
            patch=st.integers(min_value=0, max_value=9),
        ),
        # Missing components
        st.builds(
            lambda major, minor: f"{major}.{minor}",
            major=st.integers(min_value=0, max_value=9),
            minor=st.integers(min_value=0, max_value=9),
        ),
        # Extra components
        st.builds(
            lambda a, b, c, d: f"{a}.{b}.{c}.{d}",
            a=st.integers(min_value=0, max_value=9),
            b=st.integers(min_value=0, max_value=9),
            c=st.integers(min_value=0, max_value=9),
            d=st.integers(min_value=0, max_value=9),
        ),
        # Non-numeric
        st.text(
            alphabet=string.ascii_letters + "-_",
            min_size=1,
            max_size=10,
        ),
        # Empty string
        st.just(""),
        # Negative numbers
        st.builds(
            lambda major, minor, patch: f"-{major}.{minor}.{patch}",
            major=st.integers(min_value=1, max_value=9),
            minor=st.integers(min_value=0, max_value=9),
            patch=st.integers(min_value=0, max_value=9),
        ),
    )


def st_valid_hook() -> st.SearchStrategy[dict]:
    """Strategy generating valid hook dicts that pass structural validation."""
    return st.builds(
        _build_valid_hook,
        event_type=st.sampled_from(sorted(VALID_EVENT_TYPES)),
        name=st.text(
            alphabet=string.ascii_letters + " -",
            min_size=3,
            max_size=40,
        ),
        version=st_valid_semver(),
        description=st.text(
            alphabet=string.ascii_letters + " .,",
            min_size=10,
            max_size=80,
        ),
        prompt=st.text(
            alphabet=string.ascii_letters + " .,!?",
            min_size=25,
            max_size=100,
        ),
    )


def _build_valid_hook(
    event_type: str,
    name: str,
    version: str,
    description: str,
    prompt: str,
) -> dict:
    """Build a valid hook dict with appropriate conditional fields."""
    hook: dict = {
        "name": name,
        "version": version,
        "description": description,
        "when": {"type": event_type},
        "then": {"type": "askAgent", "prompt": prompt},
    }
    if event_type in FILE_EVENT_TYPES:
        hook["when"]["patterns"] = ["*.py"]
    if event_type in TOOL_EVENT_TYPES:
        hook["when"]["toolTypes"] = ["write"]
    return hook


def st_markdown_path() -> st.SearchStrategy[str]:
    """Strategy generating file paths ending in .md."""
    return st.builds(
        lambda parts, name: "/".join(parts + [name + ".md"]),
        parts=st.lists(
            st.text(
                alphabet=string.ascii_lowercase + string.digits + "-_",
                min_size=1,
                max_size=12,
            ),
            min_size=0,
            max_size=3,
        ),
        name=st.text(
            alphabet=string.ascii_lowercase + string.digits + "-_",
            min_size=1,
            max_size=15,
        ),
    )


def st_non_markdown_path() -> st.SearchStrategy[str]:
    """Strategy generating file paths NOT ending in .md."""
    non_md_extensions = [".py", ".js", ".ts", ".json", ".yaml", ".txt", ".rs", ".java"]
    return st.builds(
        lambda parts, name, ext: "/".join(parts + [name + ext]),
        parts=st.lists(
            st.text(
                alphabet=string.ascii_lowercase + string.digits + "-_",
                min_size=1,
                max_size=12,
            ),
            min_size=0,
            max_size=3,
        ),
        name=st.text(
            alphabet=string.ascii_lowercase + string.digits + "-_",
            min_size=1,
            max_size=15,
        ),
        ext=st.sampled_from(non_md_extensions),
    )
