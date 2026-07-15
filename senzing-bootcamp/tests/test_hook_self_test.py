"""Unit and property tests for the v1 hook self-test (``test_hooks.py``).

Feature: kiro-1-0-migration (hook-self-test)

``test_hooks.py`` structurally validates every shipped ``hooks/*.json`` file
against the Kiro 1.0 ``v1`` schema (``{"version": "v1", "hooks": [{name,
trigger, matcher, action}]}``). This suite exercises ``test_hooks.py``'s own
public functions against that v1 model:

- ``validate_hook`` — a well-formed v1 hook passes; malformed shapes that are
  *not* about legacy-schema rejection (invalid JSON, missing/blank name, empty
  payload, empty/absent ``hooks`` array, wrong ``version``) fail with a clear
  message.
- ``discover_hooks`` / ``hook_id_from_path`` — discovery globs ``*.json`` and
  ignores legacy ``*.kiro.hook`` files; the id is the filename stem.
- ``parse_categories_yaml`` / ``parse_registry_hook_ids`` — the minimal parsers
  return the expected id sets.
- ``check_registry_consistency`` — orphaned hooks and stale registry entries
  are both reported, and a matching pair is clean.
- ``main`` — the ``--hook`` / ``--categories`` / ``--verbose`` CLI flags are
  accepted and the shipped v1 hook set validates.

The dedicated *legacy-schema rejection* cases (legacy trigger names, legacy
askAgent/runCommand action types, residual when/then shapes, scoped-trigger
matcher rules) live in ``test_validator_rejections.py`` and are intentionally
not duplicated here.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# Make senzing-bootcamp/scripts/ importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import hook_renames as renames  # noqa: E402
from test_hooks import (  # noqa: E402
    HOOKS_DIR,
    check_registry_consistency,
    discover_hooks,
    hook_id_from_path,
    main,
    parse_categories_yaml,
    parse_registry_hook_ids,
    validate_hook,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_hook(tmp_dir: Path, hook_id: str, data: object) -> Path:
    """Write ``data`` as ``<hook_id>.json`` under ``tmp_dir`` and return it.

    Args:
        tmp_dir: Directory to write into.
        hook_id: Hook id / filename stem.
        data: JSON-serializable object to write.

    Returns:
        Path to the written ``.json`` file.
    """
    path = tmp_dir / f"{hook_id}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _entry(**overrides: object) -> dict:
    """Build a schema-valid v1 hook entry, applying any field overrides.

    The baseline uses the unscoped ``Stop`` trigger (no matcher required) plus a
    valid ``agent`` action, so a single overridden field is the sole reason a
    negative test fails.

    Args:
        **overrides: Fields to replace on the baseline entry.

    Returns:
        A v1 hook entry dict.
    """
    entry: dict = {
        "name": "Test Hook",
        "trigger": "Stop",
        "action": {"type": "agent", "prompt": "Do something"},
    }
    entry.update(overrides)
    return entry


def _wrapper(*entries: dict) -> dict:
    """Wrap entries in the ``{"version": "v1", "hooks": [...]}`` shape.

    Args:
        *entries: The v1 hook entries to include.

    Returns:
        A v1 wrapper dict.
    """
    return {"version": "v1", "hooks": list(entries)}


# ---------------------------------------------------------------------------
# validate_hook: valid v1 hooks pass
# ---------------------------------------------------------------------------


class TestValidHookPasses:
    """A well-formed v1 hook passes all structural checks."""

    def test_valid_unscoped_agent_hook(self, tmp_path: Path) -> None:
        """A ``Stop`` + ``agent`` hook (no matcher required) passes."""
        path = _write_hook(tmp_path, "unscoped-hook", _wrapper(_entry()))
        result = validate_hook(path)
        assert result.passed, f"Failures: {result.failures}"
        assert result.hook_id == "unscoped-hook"
        assert result.trigger == "Stop"
        assert result.action_type == "agent"

    def test_valid_file_path_hook(self, tmp_path: Path) -> None:
        """A ``PostFileSave`` hook with a compiling file-path matcher passes."""
        data = _wrapper(_entry(trigger="PostFileSave", matcher=r".*\.py$"))
        path = _write_hook(tmp_path, "file-hook", data)
        result = validate_hook(path)
        assert result.passed, f"Failures: {result.failures}"

    def test_valid_tool_name_hook(self, tmp_path: Path) -> None:
        """A ``PreToolUse`` hook with a compiling tool-name matcher passes."""
        data = _wrapper(_entry(trigger="PreToolUse", matcher=r"fsWrite|fsAppend"))
        path = _write_hook(tmp_path, "tool-hook", data)
        result = validate_hook(path)
        assert result.passed, f"Failures: {result.failures}"

    def test_valid_command_action_hook(self, tmp_path: Path) -> None:
        """A ``command`` action carrying a command passes."""
        data = _wrapper(
            _entry(action={"type": "command", "command": "python -m pytest"})
        )
        path = _write_hook(tmp_path, "cmd-hook", data)
        result = validate_hook(path)
        assert result.passed, f"Failures: {result.failures}"
        assert result.action_type == "command"

    def test_optional_integer_timeout_is_accepted(self, tmp_path: Path) -> None:
        """An optional integer ``timeout`` on an entry does not fail validation."""
        data = _wrapper(_entry(timeout=10))
        path = _write_hook(tmp_path, "timeout-hook", data)
        result = validate_hook(path)
        assert result.passed, f"Failures: {result.failures}"


# ---------------------------------------------------------------------------
# validate_hook: malformed (non-legacy) shapes fail
# ---------------------------------------------------------------------------


class TestMalformedHookFails:
    """Structurally malformed v1 files fail with a clear message.

    These cases exercise ``validate_hook``'s own checks and deliberately avoid
    the legacy-schema rejection paths covered by ``test_validator_rejections``.
    """

    def test_invalid_json_fails(self, tmp_path: Path) -> None:
        """A file that is not valid JSON is reported, not raised."""
        path = tmp_path / "broken.json"
        path.write_text("{ not valid json ", encoding="utf-8")
        result = validate_hook(path)
        assert not result.passed
        assert any("Invalid JSON" in f for f in result.failures)

    def test_missing_version_fails(self, tmp_path: Path) -> None:
        """A wrapper whose ``version`` is not ``v1`` fails."""
        data = {"hooks": [_entry()]}
        path = _write_hook(tmp_path, "no-version", data)
        result = validate_hook(path)
        assert not result.passed
        assert any("version must be 'v1'" in f for f in result.failures)

    def test_missing_hooks_array_fails(self, tmp_path: Path) -> None:
        """A wrapper with no ``hooks`` array fails."""
        data = {"version": "v1"}
        path = _write_hook(tmp_path, "no-hooks", data)
        result = validate_hook(path)
        assert not result.passed
        assert any("hooks (array)" in f for f in result.failures)

    def test_empty_hooks_array_fails(self, tmp_path: Path) -> None:
        """A wrapper whose ``hooks`` array is empty fails."""
        data = _wrapper()  # zero entries
        path = _write_hook(tmp_path, "empty-hooks", data)
        result = validate_hook(path)
        assert not result.passed
        assert any("hooks array is empty" in f for f in result.failures)

    def test_missing_name_fails(self, tmp_path: Path) -> None:
        """An entry with a blank ``name`` fails."""
        data = _wrapper(_entry(name="   "))
        path = _write_hook(tmp_path, "no-name", data)
        result = validate_hook(path)
        assert not result.passed
        assert any("required field: name" in f for f in result.failures)

    def test_empty_prompt_fails(self, tmp_path: Path) -> None:
        """An ``agent`` action with a blank prompt fails."""
        data = _wrapper(_entry(action={"type": "agent", "prompt": "   "}))
        path = _write_hook(tmp_path, "empty-prompt", data)
        result = validate_hook(path)
        assert not result.passed
        assert any("empty prompt" in f for f in result.failures)

    def test_non_integer_timeout_fails(self, tmp_path: Path) -> None:
        """A non-integer ``timeout`` is rejected."""
        data = _wrapper(_entry(timeout="soon"))
        path = _write_hook(tmp_path, "bad-timeout", data)
        result = validate_hook(path)
        assert not result.passed
        assert any("timeout" in f for f in result.failures)


# ---------------------------------------------------------------------------
# discover_hooks / hook_id_from_path
# ---------------------------------------------------------------------------


class TestDiscovery:
    """``discover_hooks`` globs ``*.json`` and ignores legacy ``*.kiro.hook``."""

    def test_discovers_json_ignores_legacy(self, tmp_path: Path) -> None:
        """Only ``*.json`` files are discovered; ``*.kiro.hook`` are skipped."""
        _write_hook(tmp_path, "alpha", _wrapper(_entry()))
        _write_hook(tmp_path, "beta", _wrapper(_entry()))
        # A legacy file that must NOT be discovered.
        (tmp_path / "legacy.kiro.hook").write_text("{}", encoding="utf-8")

        ids = {hook_id_from_path(p) for p in discover_hooks(tmp_path)}
        assert ids == {"alpha", "beta"}

    def test_discover_missing_dir_returns_empty(self) -> None:
        """Discovery of a non-existent directory returns an empty list."""
        assert discover_hooks(Path("/no/such/hooks/dir")) == []

    def test_hook_id_from_path_is_stem(self) -> None:
        """The hook id is the filename stem (``<id>.json`` -> ``<id>``)."""
        assert hook_id_from_path(Path("hooks/ask-bootcamper.json")) == "ask-bootcamper"

    def test_shipped_hooks_ids_match_files(self) -> None:
        """The shipped hooks directory yields ids equal to the ``*.json`` stems."""
        files = discover_hooks(HOOKS_DIR)
        assert files, f"No hook files discovered in {HOOKS_DIR}"
        ids = {hook_id_from_path(f) for f in files}
        assert ids == {f.stem for f in files}


# ---------------------------------------------------------------------------
# parse_categories_yaml / parse_registry_hook_ids
# ---------------------------------------------------------------------------


class TestParsers:
    """The minimal YAML / registry parsers return the expected id sets."""

    def test_parse_categories_yaml_flattens_modules(self, tmp_path: Path) -> None:
        """Nested module sub-keys are flattened into their top-level category."""
        path = tmp_path / "hook-categories.yaml"
        path.write_text(
            "critical:\n"
            "  - ask-bootcamper\n"
            "  - code-style-check\n"
            "modules:\n"
            "  1:\n"
            "    - verify-sdk-setup\n"
            "  any:\n"
            "    - session-log-events\n",
            encoding="utf-8",
        )
        categories = parse_categories_yaml(path)
        assert categories["critical"] == ["ask-bootcamper", "code-style-check"]
        assert categories["modules"] == ["verify-sdk-setup", "session-log-events"]

    def test_parse_categories_missing_file_returns_empty(self) -> None:
        """A missing categories file yields an empty mapping."""
        assert parse_categories_yaml(Path("/no/such/hook-categories.yaml")) == {}

    def test_parse_registry_hook_ids_extracts_bold_ids(self, tmp_path: Path) -> None:
        """Bold ``**hook-id**`` entries at line start are extracted."""
        path = tmp_path / "hook-registry-critical.md"
        path.write_text(
            "# Registry\n"
            "\n"
            "**ask-bootcamper** — the greeter\n"
            "**code-style-check** — the linter\n"
            "not-**bold-at-start** should be ignored\n",
            encoding="utf-8",
        )
        ids = parse_registry_hook_ids(path)
        assert ids == {"ask-bootcamper", "code-style-check"}

    def test_parse_registry_missing_file_returns_empty(self) -> None:
        """A missing registry file yields an empty set."""
        assert parse_registry_hook_ids(Path("/no/such/registry.md")) == set()


# ---------------------------------------------------------------------------
# check_registry_consistency
# ---------------------------------------------------------------------------


class TestRegistryConsistency:
    """Orphaned hooks and stale registry entries are both reported."""

    def _write_registry(self, tmp_dir: Path, *hook_ids: str) -> Path:
        """Write a critical registry file documenting ``hook_ids``."""
        path = tmp_dir / "hook-registry-critical.md"
        body = "\n".join(f"**{hid}** — doc" for hid in hook_ids)
        path.write_text(f"# Registry\n\n{body}\n", encoding="utf-8")
        return path

    def test_consistent_when_ids_match(self, tmp_path: Path) -> None:
        """No mismatch is reported when files and registry agree."""
        registry = self._write_registry(tmp_path, "alpha", "beta")
        result = check_registry_consistency({"alpha", "beta"}, registry)
        assert result.passed
        assert not result.orphaned_hooks
        assert not result.stale_entries

    def test_orphaned_hook_is_reported(self, tmp_path: Path) -> None:
        """A hook file with no registry entry is flagged as orphaned."""
        registry = self._write_registry(tmp_path, "alpha")
        result = check_registry_consistency({"alpha", "beta"}, registry)
        assert not result.passed
        assert result.orphaned_hooks == ["beta"]

    def test_stale_registry_entry_is_reported(self, tmp_path: Path) -> None:
        """A registry entry with no hook file is flagged as stale."""
        registry = self._write_registry(tmp_path, "alpha", "gamma")
        result = check_registry_consistency({"alpha"}, registry)
        assert not result.passed
        assert result.stale_entries == ["gamma"]


# ---------------------------------------------------------------------------
# main() CLI flags
# ---------------------------------------------------------------------------


class TestCLIFlags:
    """The CLI accepts --hook, --categories, --verbose and validates the ship set."""

    def test_hook_flag_accepted(self) -> None:
        """--hook filters to a single known hook and exits 0."""
        assert main(["--hook", "ask-bootcamper"]) == 0

    def test_categories_flag_accepted(self) -> None:
        """--categories filters to a known category and exits 0."""
        assert main(["--categories", "critical"]) == 0

    def test_verbose_flag_accepted(self) -> None:
        """--verbose runs the full self-test and exits 0."""
        assert main(["--verbose"]) == 0

    def test_flags_combined(self) -> None:
        """--hook and --verbose can be combined."""
        assert main(["--hook", "ask-bootcamper", "--verbose"]) == 0


# ---------------------------------------------------------------------------
# Property test: any well-formed v1 hook passes validate_hook
# ---------------------------------------------------------------------------

# A curated set of matchers that always compile as regular expressions, split by
# the matcher kind their trigger requires. Keeping them realistic-but-valid
# constrains the generator to the true input space (a matcher must compile).
_FILE_PATH_MATCHERS = [r".*\.py$", r"src/.*", r".*\.(ts|js)$", r"data/.*\.csv$"]
_TOOL_NAME_MATCHERS = [r"fsWrite", r"fsWrite|fsAppend", r".*sql.*", r"executeBash"]

st_trigger = st.sampled_from(sorted(renames.VALID_V1_TRIGGERS))
st_action_type = st.sampled_from(sorted(renames.VALID_V1_ACTION_TYPES))
st_non_empty_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "S", "Z")),
    min_size=1,
    max_size=50,
).filter(lambda s: s.strip())


@st.composite
def st_valid_v1_hook(draw: st.DrawFn) -> dict:
    """Draw a structurally valid v1 hook wrapper.

    The generator respects every ``validate_hook`` invariant: a 1.0 trigger, a
    1.0 action type with its matching payload field, and a compiling matcher of
    the correct kind whenever the trigger is scoped.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``{"version": "v1", "hooks": [entry]}`` dict expected to pass.
    """
    trigger = draw(st_trigger)
    action_type = draw(st_action_type)
    payload = draw(st_non_empty_text)

    action: dict = {"type": action_type}
    if action_type == "agent":
        action["prompt"] = payload
    else:
        action["command"] = payload

    entry: dict = {
        "name": draw(st_non_empty_text),
        "trigger": trigger,
        "action": action,
    }

    kind = renames.matcher_kind(trigger)
    if kind == renames.MATCHER_KIND_FILE_PATH:
        entry["matcher"] = draw(st.sampled_from(_FILE_PATH_MATCHERS))
    elif kind == renames.MATCHER_KIND_TOOL_NAME:
        entry["matcher"] = draw(st.sampled_from(_TOOL_NAME_MATCHERS))

    return {"version": "v1", "hooks": [entry]}


class TestPropertyValidHookPasses:
    """Property: any well-formed v1 hook passes ``validate_hook``.

    Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5
    """

    @given(hook_data=st_valid_v1_hook())
    def test_valid_v1_hook_always_passes(self, hook_data: dict) -> None:
        """A generated well-formed v1 hook passes all structural checks."""
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_hook(Path(tmp), "prop-hook", hook_data)
            result = validate_hook(path)
            assert result.passed, (
                f"Valid hook failed: {result.failures}\nData: {hook_data}"
            )
