"""Tests for the write_policy_gate_auto_approve preferences template key.

Validates that the schema template (bootcamp_preferences.yaml.example) declares
the write_policy_gate_auto_approve key defaulting to null, so onboarding can
record the auto-approve offer decision under a dedicated key. The .example file
is the authoritative schema definition; the runtime file is user-state and
gitignored.

Requirements: 4.1, 4.2
"""

from __future__ import annotations

from pathlib import Path


class TestWritePolicyGatePreferenceTemplate:
    """Tests for the write_policy_gate_auto_approve key in the template.

    **Validates: Requirements 4.1, 4.2**
    """

    @staticmethod
    def _power_root() -> Path:
        """Return the senzing-bootcamp/ directory path."""
        return Path(__file__).resolve().parent.parent

    def _read_preferences_file(self) -> str:
        """Read and return the bootcamp_preferences.yaml.example content."""
        path = self._power_root() / "config" / "bootcamp_preferences.yaml.example"
        return path.read_text(encoding="utf-8")

    def test_preferences_file_exists(self):
        """bootcamp_preferences.yaml.example exists at the expected path."""
        path = self._power_root() / "config" / "bootcamp_preferences.yaml.example"
        assert path.is_file(), f"Missing: {path}"

    def test_write_policy_gate_auto_approve_key_present(self):
        """Preferences template contains the write_policy_gate_auto_approve key."""
        content = self._read_preferences_file()
        assert "write_policy_gate_auto_approve:" in content

    def test_write_policy_gate_auto_approve_default_is_null(self):
        """write_policy_gate_auto_approve defaults to null (not yet offered)."""
        content = self._read_preferences_file()
        assert "write_policy_gate_auto_approve: null" in content
