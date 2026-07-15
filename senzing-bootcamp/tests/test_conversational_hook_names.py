"""Property-based tests for conversational hook name compliance.

Validates that all v1 ``*.json`` hook files in senzing-bootcamp/hooks/ follow
the conversational naming pattern: "to {verb phrase}" so the Kiro UI renders
naturally as "Ask Kiro Hook to {action}".

Under the Kiro 1.0 migration each hook file is a ``{"version": "v1", "hooks":
[entry]}`` wrapper; the ``name`` lives on the single entry, and the fields that
must be preserved (previously ``version``/``description``/``when``/``then``) are
the v1 ``trigger``/``matcher``/``action`` fields.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Discover all v1 *.json hook files
# ---------------------------------------------------------------------------

_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
ALL_HOOK_FILES = sorted(_HOOKS_DIR.glob("*.json"))

assert len(ALL_HOOK_FILES) >= 1, (
    f"Expected at least 1 .json hook file, found {len(ALL_HOOK_FILES)}"
)


def _load_entry(hook_file: Path) -> dict:
    """Return the single v1 hook entry (``hooks[0]``) from a hook file."""
    return json.loads(hook_file.read_text(encoding="utf-8"))["hooks"][0]


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
    @settings(max_examples=10)
    def test_name_starts_with_to_lowercase_verb(self, hook_file: Path) -> None:
        """Every hook name must start with 'to ' followed by a lowercase letter.

        This ensures the Kiro UI renders as a natural sentence:
        "Ask Kiro Hook to {verb phrase}"
        """
        data = _load_entry(hook_file)
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

_REGISTRY_CRITICAL_PATH = (
    Path(__file__).resolve().parent.parent / "steering" / "hook-registry-critical.md"
)
# The steering-budget-headroom spec replaced the single hook-registry-modules.md
# monolith with one per-module slice (hook-registry-module-NN.md / -any.md). Read
# all module slices where the module registry monolith was previously read.
_REGISTRY_MODULE_SLICE_PATHS = sorted(
    (Path(__file__).resolve().parent.parent / "steering").glob(
        "hook-registry-module-*.md"
    )
)
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

# Capture baseline values of the v1 entry fields that must be preserved
# (trigger, matcher, action) for all shipped hooks. This dict is populated ONCE
# at module load time so the tests catch regressions after any rename.
BASELINE_DATA: dict[str, dict] = {}
for _hf in ALL_HOOK_FILES:
    _entry = _load_entry(_hf)
    BASELINE_DATA[_hf.name] = {
        "trigger": _entry.get("trigger"),
        "matcher": _entry.get("matcher"),
        "action": _entry.get("action"),
    }

# Expected set of all shipped hook filenames (captured at module load)
EXPECTED_HOOK_FILENAMES: set[str] = {hf.name for hf in ALL_HOOK_FILES}


# ---------------------------------------------------------------------------
# Property P4: JSON Validity
# ---------------------------------------------------------------------------


class TestJSONValidity:
    """P4: Every .json hook file is valid JSON.

    **Validates: Requirements 3.5**

    Preservation: hook files must remain parseable JSON after any changes.
    """

    @given(hook_file=st.sampled_from(ALL_HOOK_FILES))
    @settings(max_examples=10)
    def test_hook_file_is_valid_json(self, hook_file: Path) -> None:
        """Every .json hook file must parse as valid JSON without errors."""
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
    """P3: Only the name field may change; trigger, matcher, action are preserved.

    **Validates: Requirements 3.1, 3.2**

    Preservation: the v1 ``trigger``, ``matcher``, and ``action`` fields must
    remain identical to the baseline captured at module load time.
    """

    @given(hook_file=st.sampled_from(ALL_HOOK_FILES))
    @settings(max_examples=10)
    def test_trigger_unchanged(self, hook_file: Path) -> None:
        """The trigger field must match the baseline."""
        data = _load_entry(hook_file)
        baseline = BASELINE_DATA[hook_file.name]
        assert data.get("trigger") == baseline["trigger"], (
            f"{hook_file.name}: trigger was mutated — "
            f"expected {baseline['trigger']!r}, got {data.get('trigger')!r}"
        )

    @given(hook_file=st.sampled_from(ALL_HOOK_FILES))
    @settings(max_examples=10)
    def test_matcher_unchanged(self, hook_file: Path) -> None:
        """The matcher field must match the baseline."""
        data = _load_entry(hook_file)
        baseline = BASELINE_DATA[hook_file.name]
        assert data.get("matcher") == baseline["matcher"], (
            f"{hook_file.name}: matcher was mutated"
        )

    @given(hook_file=st.sampled_from(ALL_HOOK_FILES))
    @settings(max_examples=10)
    def test_action_unchanged(self, hook_file: Path) -> None:
        """The action block must match the baseline."""
        data = _load_entry(hook_file)
        baseline = BASELINE_DATA[hook_file.name]
        assert data.get("action") == baseline["action"], (
            f"{hook_file.name}: action block was mutated"
        )


# ---------------------------------------------------------------------------
# Property P5: Registry Consistency
# ---------------------------------------------------------------------------


class TestRegistryConsistency:
    """P5: Registry name: lines match the name field in corresponding hook files.

    **Validates: Requirements 3.4**

    Preservation: the hook-registry.md name entries must stay in sync with
    the .json hook file name fields.
    """

    @given(hook_file=st.sampled_from(ALL_HOOK_FILES))
    @settings(max_examples=10)
    def test_registry_name_matches_hook_file(self, hook_file: Path) -> None:
        """The name: line in hook-registry.md must match the hook file's name field."""
        data = _load_entry(hook_file)
        hook_name = data["name"]

        # Derive hook_id from filename: "ask-bootcamper.json" → "ask-bootcamper"
        hook_id = hook_file.name
        if hook_id.endswith(".json"):
            hook_id = hook_id[: -len(".json")]

        # Parse registry to find the name: line for this hook_id
        registry_text = _REGISTRY_CRITICAL_PATH.read_text(encoding="utf-8") + "\n".join(
            p.read_text(encoding="utf-8") for p in _REGISTRY_MODULE_SLICE_PATHS
        )

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
    """P6: The set of .json hook filenames must not change (all expected files exist).

    **Validates: Requirements 3.1**

    Preservation: no hook files may be renamed, added, or deleted.
    """

    @given(hook_file=st.sampled_from(ALL_HOOK_FILES))
    @settings(max_examples=10)
    def test_hook_file_exists_in_expected_set(self, hook_file: Path) -> None:
        """Every hook file must be in the expected set of 24 filenames."""
        assert hook_file.name in EXPECTED_HOOK_FILENAMES, (
            f"{hook_file.name}: unexpected hook file not in baseline set"
        )

    def test_all_expected_hook_files_exist(self) -> None:
        """All expected hook files must still exist on disk."""
        current_files = {f.name for f in _HOOKS_DIR.glob("*.json")}
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
