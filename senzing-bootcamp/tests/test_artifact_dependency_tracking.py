#!/usr/bin/env python3
"""Tests for cross-module artifact dependency tracking.

Feature: artifact-dependency-tracking

Validates:
- module-artifacts.yaml schema integrity (property tests)
- validate_module.py --artifacts flag (unit tests)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = str(_PROJECT_ROOT / "scripts")
_CONFIG_DIR = _PROJECT_ROOT / "config"
_MANIFEST_PATH = _CONFIG_DIR / "module-artifacts.yaml"

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_module import (
    VALID_ARTIFACT_TYPES,
    check_artifact_on_disk,
    parse_module_artifacts_yaml,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_manifest() -> dict:
    """Load the real module-artifacts.yaml manifest."""
    return parse_module_artifacts_yaml(str(_MANIFEST_PATH))


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestManifestModuleNumbers:
    """Property: all modules in manifest have valid numbers (1-11).

    Validates that the manifest only contains module numbers within the
    valid bootcamp range.
    """

    @given(data=st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_all_module_numbers_valid(self, data: st.DataObject) -> None:
        """Every module key in the manifest must be between 1 and 11."""
        manifest = load_manifest()
        assert manifest, "Manifest could not be loaded"
        modules = manifest.get("modules", {})
        assert len(modules) > 0, "Manifest has no modules"

        # Pick a random module from the manifest
        module_num = data.draw(st.sampled_from(list(modules.keys())))
        assert 1 <= module_num <= 11, (
            f"Module number {module_num} is outside valid range 1-11"
        )


class TestRequiresFromReferencesLowerModules:
    """Property: requires_from only references modules with lower numbers.

    Validates no circular dependencies — a module can only depend on
    artifacts from modules that come before it.
    """

    @given(data=st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_requires_from_references_lower_modules(self, data: st.DataObject) -> None:
        """requires_from keys must be strictly less than the module number."""
        manifest = load_manifest()
        assert manifest, "Manifest could not be loaded"
        modules = manifest.get("modules", {})

        # Filter to modules that have requires_from
        modules_with_deps = {
            k: v for k, v in modules.items() if v.get("requires_from")
        }
        if not modules_with_deps:
            pytest.skip("No modules with requires_from")

        module_num = data.draw(st.sampled_from(list(modules_with_deps.keys())))
        requires_from = modules_with_deps[module_num]["requires_from"]

        for source_module in requires_from:
            assert source_module < module_num, (
                f"Module {module_num} requires_from Module {source_module} "
                f"which is not a lower-numbered module"
            )


class TestProducesPathsAreRelative:
    """Property: all produces paths are relative (no leading /).

    Validates that artifact paths don't use absolute paths.
    """

    @given(data=st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_produces_paths_are_relative(self, data: st.DataObject) -> None:
        """No produces path should start with /."""
        manifest = load_manifest()
        assert manifest, "Manifest could not be loaded"
        modules = manifest.get("modules", {})

        # Collect all produces entries
        all_produces: list[tuple[int, dict]] = []
        for mod_num, mod_data in modules.items():
            for artifact in mod_data.get("produces", []):
                all_produces.append((mod_num, artifact))

        assert len(all_produces) > 0, "No produces entries found"

        idx = data.draw(st.integers(min_value=0, max_value=len(all_produces) - 1))
        mod_num, artifact = all_produces[idx]
        path = artifact["path"]

        assert not path.startswith("/"), (
            f"Module {mod_num} produces path '{path}' is absolute (starts with /)"
        )


class TestArtifactTypeValidationExhaustiveness:
    """Property: artifact type validation is exhaustive.

    For any string value used as an artifact type, the validation logic
    accepts it if and only if it is one of "file", "directory", or "sentinel".
    All other strings are rejected.

    **Validates: Requirements 4.1, 4.3, 6.1, 6.2**
    """

    @given(artifact_type=st.text())
    @settings(max_examples=20)
    def test_valid_artifact_types_constant_is_exact(self, artifact_type: str) -> None:
        """VALID_ARTIFACT_TYPES accepts exactly 'file', 'directory', 'sentinel'."""
        expected_valid = {"file", "directory", "sentinel"}
        # The constant must match the expected set exactly
        assert VALID_ARTIFACT_TYPES == expected_valid, (
            f"VALID_ARTIFACT_TYPES is {VALID_ARTIFACT_TYPES}, expected {expected_valid}"
        )
        # For any random string, membership matches expected behavior
        if artifact_type in expected_valid:
            assert artifact_type in VALID_ARTIFACT_TYPES, (
                f"'{artifact_type}' should be accepted but is not in VALID_ARTIFACT_TYPES"
            )
        else:
            assert artifact_type not in VALID_ARTIFACT_TYPES, (
                f"'{artifact_type}' should be rejected but is in VALID_ARTIFACT_TYPES"
            )


class TestSentinelDiskCheckBypass:
    """Property 2: Sentinel artifacts bypass filesystem validation.

    For any artifact entry with type "sentinel", the disk-checking logic
    SHALL report the artifact as present without performing any filesystem
    I/O. The path field is treated as a logical identifier.

    **Validates: Requirements 4.2**
    """

    @given(path=st.text(min_size=1))
    @settings(max_examples=20)
    def test_sentinel_always_returns_present(self, path: str) -> None:
        """check_artifact_on_disk returns (True, False) for any sentinel path."""
        result = check_artifact_on_disk(path, "sentinel")
        assert result == (True, False), (
            f"Sentinel artifact with path '{path}' returned {result}, "
            f"expected (True, False)"
        )


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------


class TestValidateModuleArtifactsFlag:
    """Unit tests for the --artifacts flag in validate_module.py."""

    def test_artifacts_flag_accepted(self) -> None:
        """validate_module.py accepts --artifacts flag without error."""
        result = subprocess.run(
            [sys.executable, str(_PROJECT_ROOT / "scripts" / "validate_module.py"),
             "--artifacts", "4"],
            capture_output=True,
            text=True,
            cwd=str(_PROJECT_ROOT),
        )
        # Exit code 0 or 1 are both valid (depends on whether artifacts exist)
        # but NOT 2 (argparse error)
        assert result.returncode in (0, 1), (
            f"--artifacts flag rejected by argparse: {result.stderr}"
        )

    def test_artifacts_flag_invalid_module(self) -> None:
        """validate_module.py rejects --artifacts with invalid module number."""
        result = subprocess.run(
            [sys.executable, str(_PROJECT_ROOT / "scripts" / "validate_module.py"),
             "--artifacts", "99"],
            capture_output=True,
            text=True,
            cwd=str(_PROJECT_ROOT),
        )
        # argparse should reject 99 as out of range
        assert result.returncode == 2


class TestNonRootModuleDependencyInvariant:
    """Property: non-root modules have upstream dependencies.

    For any module in the manifest with a module number greater than 2,
    the module SHALL have at least one entry in its requires_from mapping.
    Only Modules 1 and 2 are permitted to have empty requires_from.

    Validates: Requirements 7.2
    """

    @given(data=st.data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_non_root_modules_have_requires_from(self, data: st.DataObject) -> None:
        """Modules with number > 2 must have non-empty requires_from."""
        manifest = load_manifest()
        modules = manifest.get("modules", {})

        # Filter to non-root modules (number > 2)
        non_root_modules = [k for k in modules.keys() if k > 2]
        assert len(non_root_modules) > 0, "No non-root modules found in manifest"

        module_num = data.draw(st.sampled_from(non_root_modules))
        mod_data = modules[module_num]
        requires_from = mod_data.get("requires_from", {})

        assert requires_from, (
            f"Module {module_num} has empty requires_from — "
            f"only Modules 1 and 2 are permitted to have no upstream dependencies"
        )


class TestManifestFileValidity:
    """Unit tests for module-artifacts.yaml existence and validity."""

    def test_manifest_exists(self) -> None:
        """module-artifacts.yaml exists on disk."""
        assert _MANIFEST_PATH.exists(), (
            f"module-artifacts.yaml not found at {_MANIFEST_PATH}"
        )

    def test_manifest_has_version(self) -> None:
        """module-artifacts.yaml has a version field."""
        manifest = load_manifest()
        assert manifest.get("version"), "Manifest missing version field"

    def test_manifest_has_modules(self) -> None:
        """module-artifacts.yaml has a modules section with entries."""
        manifest = load_manifest()
        modules = manifest.get("modules", {})
        assert len(modules) > 0, "Manifest has no module entries"

    def test_manifest_produces_have_required_fields(self) -> None:
        """Every produces entry has path, type, description, and required."""
        manifest = load_manifest()
        modules = manifest.get("modules", {})
        for mod_num, mod_data in modules.items():
            for artifact in mod_data.get("produces", []):
                assert "path" in artifact, (
                    f"Module {mod_num}: produces entry missing 'path'"
                )
                assert "type" in artifact, (
                    f"Module {mod_num}: produces entry missing 'type'"
                )
                assert artifact["type"] in ("file", "directory", "sentinel"), (
                    f"Module {mod_num}: invalid type '{artifact['type']}'"
                )
                assert "description" in artifact, (
                    f"Module {mod_num}: produces entry missing 'description'"
                )
                assert "required" in artifact, (
                    f"Module {mod_num}: produces entry missing 'required'"
                )
