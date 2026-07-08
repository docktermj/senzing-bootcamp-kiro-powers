"""Example-based unit tests for sync_hook_registry.py.

Feature: hook-registry-source-of-truth

These tests exercise the Kiro 1.0 ``v1`` hook model: hooks ship as ``*.json``
files wrapping ``{"version": "v1", "hooks": [{name, trigger, matcher, action}]}``.
There is no legacy ``file_patterns`` / ``tool_types`` split — a hook carries a
single ``matcher`` regex (or ``None``) — and the schema has no ``description``
field, so ``HookEntry.description`` falls back to the hook ``name``.
"""

import ast
import json
import sys
import tempfile
from pathlib import Path

import pytest

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from sync_hook_registry import (
    categorize_hooks,
    discover_hook_files,
    generate_registry_summary,
    load_category_mapping,
    parse_all_hooks,
    parse_hook_file,
    verify_registry,
)

# Paths relative to the repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_HOOKS_DIR = _REPO_ROOT / "senzing-bootcamp" / "hooks"
_CATEGORIES_PATH = _HOOKS_DIR / "hook-categories.yaml"
_REGISTRY_PATH = _REPO_ROOT / "senzing-bootcamp" / "steering" / "hook-registry.md"
_SCRIPT_PATH = _REPO_ROOT / "senzing-bootcamp" / "scripts" / "sync_hook_registry.py"


# ---------------------------------------------------------------------------
# 8.1 Parse real ask-bootcamper.json v1 hook file (Req 1.2)
# ---------------------------------------------------------------------------


class TestParseRealHookFile:
    """Validates: Requirement 1.2"""

    def test_parse_ask_bootcamper(self):
        hook_path = _HOOKS_DIR / "ask-bootcamper.json"
        entry = parse_hook_file(hook_path)

        assert entry.hook_id == "ask-bootcamper"
        assert entry.name == "to wait for your answer"
        # The v1 schema has no description field, so description falls back to
        # the hook name.
        assert entry.description == entry.name
        # 1.0 trigger + action type (replaces legacy agentStop / askAgent).
        assert entry.event_type == "Stop"
        assert entry.action_type == "agent"
        assert entry.prompt is not None
        assert "recap" in entry.prompt.lower()
        # ask-bootcamper is an unscoped Stop trigger — no single matcher.
        assert entry.matcher is None


# ---------------------------------------------------------------------------
# 8.2 Parse all real v1 hook files without errors (Req 1.1)
# ---------------------------------------------------------------------------


class TestParseAllRealHooks:
    """Validates: Requirement 1.1"""

    def test_all_hooks_parse_without_errors(self):
        entries, errors = parse_all_hooks(_HOOKS_DIR)
        assert len(errors) == 0, f"Parse errors: {errors}"
        # Count should match the number of v1 ``*.json`` hook files on disk.
        expected = len(discover_hook_files(_HOOKS_DIR))
        assert len(entries) == expected, f"Expected {expected} hooks, got {len(entries)}"


# ---------------------------------------------------------------------------
# 8.3 Invalid JSON file is skipped with error message (Req 1.6)
# ---------------------------------------------------------------------------


class TestInvalidJsonSkipped:
    """Validates: Requirement 1.6"""

    def test_invalid_json_raises_value_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_file = Path(tmp_dir) / "bad-hook.json"
            bad_file.write_text("{ not valid json }", encoding="utf-8")

            with pytest.raises(ValueError, match="bad-hook"):
                parse_hook_file(bad_file)

    def test_invalid_json_collected_in_parse_all(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create one valid v1 hook file and one invalid JSON file.
            valid = Path(tmp_dir) / "good.json"
            valid.write_text(json.dumps({
                "version": "v1",
                "hooks": [
                    {
                        "name": "Good Hook",
                        "trigger": "Stop",
                        "action": {"type": "agent", "prompt": "Do the good thing."},
                    }
                ],
            }), encoding="utf-8")

            bad = Path(tmp_dir) / "bad.json"
            bad.write_text("not json", encoding="utf-8")

            entries, errors = parse_all_hooks(Path(tmp_dir))
            assert len(entries) == 1
            assert len(errors) == 1
            assert "bad" in errors[0].lower()


# ---------------------------------------------------------------------------
# 8.4 Category mapping loads correctly from real hook-categories.yaml (Req 2.5)
# ---------------------------------------------------------------------------


class TestCategoryMappingLoads:
    """Validates: Requirement 2.5"""

    def test_load_real_categories(self):
        mapping = load_category_mapping(_CATEGORIES_PATH)

        # Should have all hooks mapped (count matches disk).
        expected = len(discover_hook_files(_HOOKS_DIR))
        assert len(mapping) == expected, f"Expected {expected} mappings, got {len(mapping)}"

        # Check some known critical hooks.
        assert mapping["ask-bootcamper"].category == "critical"
        assert mapping["review-bootcamper-input"].category == "critical"

        # Check some known module hooks.
        assert mapping["data-quality-check"].category == "module"
        assert mapping["data-quality-check"].module_number == 5

        assert mapping["backup-before-load"].category == "module"
        assert mapping["backup-before-load"].module_number == 6

        # Check "any module" hooks (module category, no specific module number).
        assert mapping["session-log-events"].category == "module"
        assert mapping["session-log-events"].module_number is None


# ---------------------------------------------------------------------------
# 8.5 --verify exits 0 when generated registry matches (Req 4.3)
# ---------------------------------------------------------------------------


class TestVerifyExitsZero:
    """Validates: Requirement 4.3"""

    def test_verify_matches_current_registry(self):
        # Generate content from real hooks.
        entries, errors = parse_all_hooks(_HOOKS_DIR)
        assert len(errors) == 0
        mapping = load_category_mapping(_CATEGORIES_PATH)
        critical, modules = categorize_hooks(entries, mapping, _CATEGORIES_PATH)
        content = generate_registry_summary(
            critical, modules, len(entries), categories_path=_CATEGORIES_PATH
        )

        matches, msg = verify_registry(content, _REGISTRY_PATH)
        assert matches, f"Registry should match: {msg}"


# ---------------------------------------------------------------------------
# 8.6 --verify exits 1 when registry file is missing (Req 4.5)
# ---------------------------------------------------------------------------


class TestVerifyMissingFile:
    """Validates: Requirement 4.5"""

    def test_verify_missing_file(self):
        matches, msg = verify_registry("some content", Path("/nonexistent/path.md"))
        assert not matches
        assert "missing" in msg.lower()


# ---------------------------------------------------------------------------
# 8.7 Script uses only Python standard library imports (Req 5.4)
# ---------------------------------------------------------------------------


class TestStdlibOnly:
    """Validates: Requirement 5.4"""

    def test_only_stdlib_imports(self):
        """Parse the script's AST and verify all imports are from stdlib."""
        source = _SCRIPT_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)

        # Known stdlib modules
        stdlib_modules = {
            "argparse", "json", "sys", "pathlib", "dataclasses",
            "typing", "re", "os", "io", "collections", "functools",
            "itertools", "textwrap", "string", "__future__", "datetime",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    assert top in stdlib_modules, (
                        f"Non-stdlib import: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0]
                    assert top in stdlib_modules, (
                        f"Non-stdlib import: from {node.module}"
                    )


# ---------------------------------------------------------------------------
# 8.8 Generated registry is byte-identical when regenerated (Req 6.1)
# ---------------------------------------------------------------------------


class TestDeterministicGeneration:
    """Validates: Requirement 6.1"""

    def test_regenerate_is_identical(self):
        entries, errors = parse_all_hooks(_HOOKS_DIR)
        assert len(errors) == 0
        mapping = load_category_mapping(_CATEGORIES_PATH)

        critical1, modules1 = categorize_hooks(entries, mapping)
        content1 = generate_registry_summary(critical1, modules1, len(entries))

        critical2, modules2 = categorize_hooks(entries, mapping)
        content2 = generate_registry_summary(critical2, modules2, len(entries))

        assert content1 == content2, "Regenerated registry must be byte-identical"
