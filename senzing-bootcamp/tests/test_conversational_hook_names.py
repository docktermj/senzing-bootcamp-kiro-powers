"""Property-based tests for conversational hook name compliance.

Validates that all .kiro.hook files in senzing-bootcamp/hooks/ follow the
conversational naming pattern: "to {verb phrase}" so the Kiro UI renders
naturally as "Ask Kiro Hook to {action}".

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Discover all 24 .kiro.hook files
# ---------------------------------------------------------------------------

_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
ALL_HOOK_FILES = sorted(_HOOKS_DIR.glob("*.kiro.hook"))

assert len(ALL_HOOK_FILES) == 24, (
    f"Expected 24 .kiro.hook files, found {len(ALL_HOOK_FILES)}"
)


# ---------------------------------------------------------------------------
# Property P1: Conversational Pattern Compliance
# ---------------------------------------------------------------------------


class TestConversationalPatternCompliance:
    """P1: Every hook name starts with 'to ' followed by a lowercase verb.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

    Bug_Condition: hook `name` fields use Title Case labels, first-person
    phrasing, or inconsistent patterns instead of "to {verb phrase}".

    Expected_Behavior: every hook `name` matches /^to [a-z]/ so the UI reads
    "Ask Kiro Hook to {action}".
    """

    @given(hook_file=st.sampled_from(ALL_HOOK_FILES))
    @settings(max_examples=100)
    def test_name_starts_with_to_lowercase_verb(self, hook_file: Path) -> None:
        """Every hook name must start with 'to ' followed by a lowercase letter.

        This ensures the Kiro UI renders as a natural sentence:
        "Ask Kiro Hook to {verb phrase}"
        """
        data = json.loads(hook_file.read_text(encoding="utf-8"))
        name = data["name"]

        assert name.startswith("to "), (
            f"{hook_file.name}: name {name!r} must start with 'to ' "
            f"(UI renders as 'Ask Kiro Hook {name}')"
        )

        rest = name[3:]
        assert len(rest) > 0, (
            f"{hook_file.name}: name must have a verb phrase after 'to '"
        )
        assert rest[0].islower(), (
            f"{hook_file.name}: verb after 'to ' must be lowercase, "
            f"got {rest[0]!r} in name {name!r}"
        )

# ---------------------------------------------------------------------------
# Shared: Baseline data captured at module load time
# ---------------------------------------------------------------------------

import re
import subprocess

_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "steering" / "hook-registry.md"
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

# Capture baseline values of version, description, when, then for all 24 hooks.
# This dict is populated ONCE at module load time so the tests pass on current
# (unfixed) code and will catch regressions after the fix is applied.
BASELINE_DATA: dict[str, dict] = {}
for _hf in ALL_HOOK_FILES:
    _data = json.loads(_hf.read_text(encoding="utf-8"))
    BASELINE_DATA[_hf.name] = {
        "version": _data.get("version"),
        "description": _data.get("description"),
        "when": _data.get("when"),
        "then": _data.get("then"),
    }

# Expected set of all 24 hook filenames (captured at module load)
EXPECTED_HOOK_FILENAMES: set[str] = {hf.name for hf in ALL_HOOK_FILES}


# ---------------------------------------------------------------------------
# Property P4: JSON Validity
# ---------------------------------------------------------------------------


class TestJSONValidity:
    """P4: Every .kiro.hook file is valid JSON.

    **Validates: Requirements 3.5**

    Preservation: hook files must remain parseable JSON after any changes.
    """

    @given(hook_file=st.sampled_from(ALL_HOOK_FILES))
    @settings(max_examples=100)
    def test_hook_file_is_valid_json(self, hook_file: Path) -> None:
        """Every .kiro.hook file must parse as valid JSON without errors."""
        content = hook_file.read_text(encoding="utf-8")
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AssertionError(
                f"{hook_file.name}: invalid JSON — {exc}"
            ) from exc
        # Must be a dict at the top level
        assert isinstance(data, dict), (
            f"{hook_file.name}: top-level JSON must be an object, got {type(data).__name__}"
        )


# ---------------------------------------------------------------------------
# Property P3: Structural Preservation
# ---------------------------------------------------------------------------


class TestStructuralPreservation:
    """P3: Only the name field may change; version, description, when, then are preserved.

    **Validates: Requirements 3.1, 3.2**

    Preservation: version, description, when, then fields must remain identical
    to the baseline captured at module load time.
    """

    @given(hook_file=st.sampled_from(ALL_HOOK_FILES))
    @settings(max_examples=100)
    def test_version_unchanged(self, hook_file: Path) -> None:
        """The version field must match the baseline."""
        data = json.loads(hook_file.read_text(encoding="utf-8"))
        baseline = BASELINE_DATA[hook_file.name]
        assert data.get("version") == baseline["version"], (
            f"{hook_file.name}: version was mutated — "
            f"expected {baseline['version']!r}, got {data.get('version')!r}"
        )

    @given(hook_file=st.sampled_from(ALL_HOOK_FILES))
    @settings(max_examples=100)
    def test_description_unchanged(self, hook_file: Path) -> None:
        """The description field must match the baseline."""
        data = json.loads(hook_file.read_text(encoding="utf-8"))
        baseline = BASELINE_DATA[hook_file.name]
        assert data.get("description") == baseline["description"], (
            f"{hook_file.name}: description was mutated"
        )

    @given(hook_file=st.sampled_from(ALL_HOOK_FILES))
    @settings(max_examples=100)
    def test_when_unchanged(self, hook_file: Path) -> None:
        """The when block must match the baseline."""
        data = json.loads(hook_file.read_text(encoding="utf-8"))
        baseline = BASELINE_DATA[hook_file.name]
        assert data.get("when") == baseline["when"], (
            f"{hook_file.name}: when block was mutated"
        )

    @given(hook_file=st.sampled_from(ALL_HOOK_FILES))
    @settings(max_examples=100)
    def test_then_unchanged(self, hook_file: Path) -> None:
        """The then block must match the baseline."""
        data = json.loads(hook_file.read_text(encoding="utf-8"))
        baseline = BASELINE_DATA[hook_file.name]
        assert data.get("then") == baseline["then"], (
            f"{hook_file.name}: then block was mutated"
        )


# ---------------------------------------------------------------------------
# Property P5: Registry Consistency
# ---------------------------------------------------------------------------


class TestRegistryConsistency:
    """P5: Registry name: lines match the name field in corresponding hook files.

    **Validates: Requirements 3.4**

    Preservation: the hook-registry.md name entries must stay in sync with
    the .kiro.hook file name fields.
    """

    @given(hook_file=st.sampled_from(ALL_HOOK_FILES))
    @settings(max_examples=100)
    def test_registry_name_matches_hook_file(self, hook_file: Path) -> None:
        """The name: line in hook-registry.md must match the hook file's name field."""
        data = json.loads(hook_file.read_text(encoding="utf-8"))
        hook_name = data["name"]

        # Derive hook_id from filename: "ask-bootcamper.kiro.hook" → "ask-bootcamper"
        hook_id = hook_file.name
        if hook_id.endswith(".kiro.hook"):
            hook_id = hook_id[: -len(".kiro.hook")]

        # Parse registry to find the name: line for this hook_id
        registry_text = _REGISTRY_PATH.read_text(encoding="utf-8")

        # Look for pattern: "- id: `{hook_id}`" followed by "- name: `{name}`"
        # The registry format is:
        #   - id: `hook-id`
        #   - name: `Hook Name`
        #   - description: `...`
        id_pattern = re.compile(
            rf"- id: `{re.escape(hook_id)}`\n- name: `([^`]+)`"
        )
        match = id_pattern.search(registry_text)
        assert match is not None, (
            f"{hook_file.name}: hook_id {hook_id!r} not found in registry"
        )
        registry_name = match.group(1)
        assert registry_name == hook_name, (
            f"{hook_file.name}: registry name {registry_name!r} does not match "
            f"hook file name {hook_name!r}"
        )


# ---------------------------------------------------------------------------
# Property P6: No ID Mutation
# ---------------------------------------------------------------------------


class TestNoIDMutation:
    """P6: The set of .kiro.hook filenames must not change (all 24 expected files exist).

    **Validates: Requirements 3.1**

    Preservation: no hook files may be renamed, added, or deleted.
    """

    @given(hook_file=st.sampled_from(ALL_HOOK_FILES))
    @settings(max_examples=100)
    def test_hook_file_exists_in_expected_set(self, hook_file: Path) -> None:
        """Every hook file must be in the expected set of 24 filenames."""
        assert hook_file.name in EXPECTED_HOOK_FILENAMES, (
            f"{hook_file.name}: unexpected hook file not in baseline set"
        )

    def test_all_expected_hook_files_exist(self) -> None:
        """All 24 expected hook files must still exist on disk."""
        current_files = {f.name for f in _HOOKS_DIR.glob("*.kiro.hook")}
        missing = EXPECTED_HOOK_FILENAMES - current_files
        assert not missing, (
            f"Missing hook files: {sorted(missing)}"
        )
        extra = current_files - EXPECTED_HOOK_FILENAMES
        assert not extra, (
            f"Unexpected hook files: {sorted(extra)}"
        )


# ---------------------------------------------------------------------------
# Property P7: CI Validation Passes
# ---------------------------------------------------------------------------


class TestCIValidation:
    """P7: sync_hook_registry.py --verify must exit with code 0.

    **Validates: Requirements 3.4**

    Preservation: the CI validation script must continue to pass after changes.
    """

    def test_sync_hook_registry_verify_passes(self) -> None:
        """Running sync_hook_registry.py --verify must exit with code 0."""
        # Run from the repo root (parent of senzing-bootcamp/)
        repo_root = Path(__file__).resolve().parent.parent.parent
        script = _SCRIPTS_DIR / "sync_hook_registry.py"
        result = subprocess.run(
            ["python3", str(script), "--verify"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
        )
        assert result.returncode == 0, (
            f"sync_hook_registry.py --verify failed (exit code {result.returncode}).\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
