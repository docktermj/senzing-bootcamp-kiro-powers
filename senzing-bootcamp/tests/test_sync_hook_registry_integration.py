"""Integration tests for sync_hook_registry.py.

Feature: hook-registry-source-of-truth

These tests exercise the full pipeline: discover → parse → categorize →
generate → write/verify, using the real hook files on disk.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from sync_hook_registry import (
    parse_all_hooks,
    load_category_mapping,
    categorize_hooks,
    generate_registry_summary,
    generate_registry_detail,
    write_registry,
    verify_registry,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_HOOKS_DIR = _REPO_ROOT / "senzing-bootcamp" / "hooks"
_CATEGORIES_PATH = _HOOKS_DIR / "hook-categories.yaml"
_REGISTRY_PATH = _REPO_ROOT / "senzing-bootcamp" / "steering" / "hook-registry.md"
_SCRIPT_PATH = _REPO_ROOT / "senzing-bootcamp" / "scripts" / "sync_hook_registry.py"


# ---------------------------------------------------------------------------
# 9.1 End-to-end: generate from real hooks, verify matches existing registry
# ---------------------------------------------------------------------------


class TestEndToEndGenerate:
    def test_generated_matches_existing_registry(self):
        """Generate registry from real hooks and verify it matches the
        existing hook-registry.md on disk."""
        entries, errors = parse_all_hooks(_HOOKS_DIR)
        assert len(errors) == 0, f"Parse errors: {errors}"

        mapping = load_category_mapping(_CATEGORIES_PATH)
        critical, modules = categorize_hooks(entries, mapping)
        content = generate_registry_summary(
            critical, modules, len(entries), categories_path=_CATEGORIES_PATH
        )

        matches, msg = verify_registry(content, _REGISTRY_PATH)
        assert matches, f"Generated registry does not match existing: {msg}"


# ---------------------------------------------------------------------------
# 9.2 CLI: python scripts/sync_hook_registry.py --verify exits 0
# ---------------------------------------------------------------------------


class TestCLIVerify:
    def test_verify_exits_zero(self):
        """Run the script in --verify mode and confirm exit code 0."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPT_PATH), "--verify"],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
        )
        assert result.returncode == 0, (
            f"--verify exited with code {result.returncode}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


# ---------------------------------------------------------------------------
# 9.3 Regenerate twice from real hooks, compare byte-for-byte (Req 6.1)
# ---------------------------------------------------------------------------


class TestRegenerateTwice:
    def test_two_generations_byte_identical(self):
        """Generate the registry twice and confirm byte-identical output."""
        entries, errors = parse_all_hooks(_HOOKS_DIR)
        assert len(errors) == 0
        mapping = load_category_mapping(_CATEGORIES_PATH)

        critical1, modules1 = categorize_hooks(entries, mapping)
        content1 = generate_registry_summary(critical1, modules1, len(entries))

        # Write to temp, re-read, compare
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8", newline=""
        ) as f:
            f.write(content1)
            tmp_path = Path(f.name)

        try:
            critical2, modules2 = categorize_hooks(entries, mapping)
            content2 = generate_registry_summary(critical2, modules2, len(entries))

            assert content1 == content2, "Two generations must be byte-identical"

            # Also verify the written file matches
            on_disk = tmp_path.read_text(encoding="utf-8")
            assert on_disk == content1, "Written file must match generated content"
        finally:
            tmp_path.unlink(missing_ok=True)
