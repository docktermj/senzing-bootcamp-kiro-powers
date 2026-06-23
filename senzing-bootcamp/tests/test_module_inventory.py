"""Tests pinning the bootcamp module inventory (drift + preservation guards).

`config/module-dependencies.yaml` is the single source of truth for the module
roster (number → name). These tests pin the canonical 11-module roster and fail
if any documented or coded module map drifts from it:

  * a module renamed without updating the YAML,
  * a wrong name assigned to a number (e.g. labelling Module 7 with the old
    "Multi-Source Orchestration" content), or
  * a stale "Module 12" reintroduced after the 0.11.0 collapse of Module 12
    into Module 11.

The expectations are sourced from the YAML (via track_switcher.load_module_names)
and cross-checked against an explicit pinned roster, every script that hard-codes
a module-name map, and POWER.md's generated module table.
"""

from __future__ import annotations

import sys
from pathlib import Path

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = str(_BOOTCAMP_DIR / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import importlib

import track_switcher
import validate_power

_YAML = _BOOTCAMP_DIR / "config" / "module-dependencies.yaml"
_POWER_MD = _BOOTCAMP_DIR / "POWER.md"

# The canonical 11-module roster (pinned). Must match module-dependencies.yaml.
_EXPECTED_ROSTER = {
    1: "Business Problem",
    2: "SDK Setup",
    3: "System Verification",
    4: "Data Collection",
    5: "Data Quality & Mapping",
    6: "Data Processing",
    7: "Query, Visualize, and Discover",
    8: "Performance Testing & Benchmarking",
    9: "Security Hardening",
    10: "Monitoring & Observability",
    11: "Package & Deploy",
}

# Scripts that hard-code a module number → name map and must stay in sync.
_SCRIPTS_WITH_MODULE_MAPS = (
    "status",
    "export_results",
    "repair_progress",
    "team_dashboard",
    "rollback_module",
    "assess_entry_point",
    "generate_graduation_certificate",
    "validate_module",
)


def _canonical() -> dict[int, str]:
    return track_switcher.load_module_names(_YAML)


class TestCanonicalRoster:
    """The YAML roster is the pinned 11-module inventory."""

    def test_yaml_matches_pinned_roster(self) -> None:
        """module-dependencies.yaml defines exactly the pinned 11-module roster."""
        assert _canonical() == _EXPECTED_ROSTER

    def test_roster_has_no_module_12(self) -> None:
        """No Module 12 — it was collapsed into Module 11 in 0.11.0."""
        assert 12 not in _canonical()

    def test_roster_is_contiguous_from_one(self) -> None:
        """Module numbers are a contiguous 1..N range."""
        roster = _canonical()
        assert set(roster) == set(range(1, len(roster) + 1))


class TestScriptMapsMatchRoster:
    """Every script's hard-coded module-name map matches the canonical roster."""

    def test_each_script_map_matches(self) -> None:
        """For each registered script, every module-name map equals the roster."""
        canonical = _canonical()
        for name in _SCRIPTS_WITH_MODULE_MAPS:
            module = importlib.import_module(name)
            maps = validate_power._find_module_name_maps(module)
            assert maps, f"{name}.py defines no module number→name map"
            for mod_map in maps:
                assert mod_map == canonical, (
                    f"{name}.py module-name map diverged from the canonical roster.\n"
                    f"  script:    {mod_map}\n  canonical: {canonical}"
                )

    def test_no_script_map_defines_module_12(self) -> None:
        """No script module-name map carries a stale Module 12 entry."""
        for name in _SCRIPTS_WITH_MODULE_MAPS:
            module = importlib.import_module(name)
            for mod_map in validate_power._find_module_name_maps(module):
                assert 12 not in mod_map, f"{name}.py still defines a Module 12"


class TestPowerMdModuleTable:
    """POWER.md's generated module table matches the canonical roster."""

    def test_power_md_table_matches_roster(self) -> None:
        """The POWER.md modules table lists exactly the canonical roster."""
        table = validate_power._power_md_module_table(
            _POWER_MD.read_text(encoding="utf-8")
        )
        assert table == _canonical()


class TestValidatePowerGate:
    """The validate_power.py module-inventory gate runs clean on the shipped tree."""

    def test_gate_records_no_errors(self) -> None:
        """check_module_inventory() adds no errors to the validator's error list."""
        validate_power.errors.clear()
        validate_power.warnings.clear()
        validate_power.check_module_inventory()
        assert validate_power.errors == []
