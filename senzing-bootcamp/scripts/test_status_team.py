"""Example-based unit tests for status.py team mode behavior.

Tests team detection, --member argument handling, and team summary display.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from team_config_validator import TeamConfig, TeamMember, PathResolver


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════


def _make_team_config(members=None, mode="colocated"):
    """Create a TeamConfig for testing."""
    if members is None:
        members = [
            TeamMember(id="alice", name="Alice"),
            TeamMember(id="bob", name="Bob"),
        ]
    return TeamConfig(
        team_name="Test Team",
        members=members,
        mode=mode,
    )


def _make_progress_file(tmp_path, member_id, completed, current=1):
    """Write a co-located progress JSON for a member."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    data = {
        "modules_completed": completed,
        "current_module": current,
        "language": "python",
    }
    (config_dir / f"progress_{member_id}.json").write_text(
        json.dumps(data), encoding="utf-8"
    )


# ═══════════════════════════════════════════════════════════════════════════
# Team detection tests
# ═══════════════════════════════════════════════════════════════════════════


class TestTeamDetection:
    """Tests for _detect_team_mode in status.py."""

    def test_no_team_yaml_returns_none(self, tmp_path):
        """When config/team.yaml doesn't exist, returns (None, None)."""
        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            import importlib
            import status
            importlib.reload(status)
            config, resolver = status._detect_team_mode()
            assert config is None
            assert resolver is None
        finally:
            os.chdir(orig_cwd)

    def test_valid_team_yaml_returns_config(self, tmp_path):
        """When config/team.yaml exists and is valid, returns config + resolver."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "team.yaml").write_text(
            "team_name: Test Team\nmode: colocated\nmembers:\n"
            "  - id: alice\n    name: Alice\n"
            "  - id: bob\n    name: Bob\n",
            encoding="utf-8",
        )
        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            import importlib
            import status
            importlib.reload(status)
            config, resolver = status._detect_team_mode()
            assert config is not None
            assert config.team_name == "Test Team"
            assert resolver is not None
        finally:
            os.chdir(orig_cwd)

    def test_invalid_team_yaml_returns_none(self, tmp_path):
        """When config/team.yaml is invalid, returns (None, None)."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "team.yaml").write_text("bad: content\n", encoding="utf-8")
        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            import importlib
            import status
            importlib.reload(status)
            config, resolver = status._detect_team_mode()
            assert config is None
        finally:
            os.chdir(orig_cwd)


# ═══════════════════════════════════════════════════════════════════════════
# _show_member_status tests
# ═══════════════════════════════════════════════════════════════════════════


class TestShowMemberStatus:
    """Tests for _show_member_status helper."""

    def test_with_data(self, capsys):
        """Shows member name and progress when data exists."""
        import importlib
        import status
        importlib.reload(status)
        member = TeamMember(id="alice", name="Alice")
        data = {
            "modules_completed": [1, 2, 3],
            "current_module": 4,
            "language": "python",
            "current_step": 2,
        }
        status._show_member_status(member, data)
        out = capsys.readouterr().out
        assert "Alice" in out
        assert "alice" in out
        assert "3/12" in out

    def test_with_no_data(self, capsys):
        """Shows warning when no data available."""
        import importlib
        import status
        importlib.reload(status)
        member = TeamMember(id="alice", name="Alice")
        status._show_member_status(member, None)
        out = capsys.readouterr().out
        assert "No progress data" in out or "alice" in out


# ═══════════════════════════════════════════════════════════════════════════
# _show_team_summary tests
# ═══════════════════════════════════════════════════════════════════════════


class TestShowTeamSummary:
    """Tests for _show_team_summary helper."""

    def test_shows_all_members(self, tmp_path, capsys):
        """Team summary lists all members."""
        config = _make_team_config()
        _make_progress_file(tmp_path, "alice", [1, 2], current=3)
        _make_progress_file(tmp_path, "bob", [1], current=2)
        resolver = PathResolver(config)

        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            import importlib
            import status
            importlib.reload(status)
            status._show_team_summary(config, resolver)
        finally:
            os.chdir(orig_cwd)

        out = capsys.readouterr().out
        assert "Alice" in out
        assert "Bob" in out
        assert "Test Team" in out

    def test_shows_stats(self, tmp_path, capsys):
        """Team summary includes team statistics."""
        config = _make_team_config()
        _make_progress_file(tmp_path, "alice", [1, 2, 3], current=4)
        _make_progress_file(tmp_path, "bob", [1], current=2)
        resolver = PathResolver(config)

        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            import importlib
            import status
            importlib.reload(status)
            status._show_team_summary(config, resolver)
        finally:
            os.chdir(orig_cwd)

        out = capsys.readouterr().out
        assert "Team Statistics" in out
        assert "Total modules completed" in out

    def test_missing_member_data(self, tmp_path, capsys):
        """Team summary handles missing member progress gracefully."""
        config = _make_team_config()
        _make_progress_file(tmp_path, "alice", [1, 2], current=3)
        # bob has no progress file
        resolver = PathResolver(config)

        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            import importlib
            import status
            importlib.reload(status)
            status._show_team_summary(config, resolver)
        finally:
            os.chdir(orig_cwd)

        out = capsys.readouterr().out
        assert "No data available" in out
        assert "Alice" in out
        assert "Bob" in out


# ═══════════════════════════════════════════════════════════════════════════
# main() integration tests with team mode
# ═══════════════════════════════════════════════════════════════════════════


class TestMainTeamMode:
    """Integration tests for main() with team mode active."""

    def test_main_team_summary(self, tmp_path, capsys):
        """main() shows team summary when team.yaml exists and no --member."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "team.yaml").write_text(
            "team_name: Test Team\nmode: colocated\nmembers:\n"
            "  - id: alice\n    name: Alice\n"
            "  - id: bob\n    name: Bob\n",
            encoding="utf-8",
        )
        _make_progress_file(tmp_path, "alice", [1, 2], current=3)
        _make_progress_file(tmp_path, "bob", [1], current=2)

        # We need to make main() chdir to tmp_path.
        # status.py computes project_root from __file__.parent.parent
        # We'll patch _detect_team_mode to return our config.
        config = _make_team_config()
        resolver = PathResolver(config)

        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            import importlib
            import status
            importlib.reload(status)
            with patch.object(status, "_detect_team_mode", return_value=(config, resolver)):
                with patch.object(sys, "argv", ["status.py"]):
                    status.main()
        finally:
            os.chdir(orig_cwd)

        out = capsys.readouterr().out
        assert "Test Team" in out
        assert "Alice" in out

    def test_main_member_flag(self, tmp_path, capsys):
        """main() shows individual member when --member is provided."""
        _make_progress_file(tmp_path, "alice", [1, 2, 3], current=4)

        config = _make_team_config()
        resolver = PathResolver(config)

        # Mock _read_member_progress to return data from our tmp_path
        progress_data = {
            "modules_completed": [1, 2, 3],
            "current_module": 4,
            "language": "python",
        }

        import importlib
        import status
        importlib.reload(status)
        with patch.object(status, "_detect_team_mode", return_value=(config, resolver)):
            with patch.object(status, "_read_member_progress", return_value=progress_data):
                with patch.object(sys, "argv", ["status.py", "--member", "alice"]):
                    status.main()

        out = capsys.readouterr().out
        assert "Alice" in out
        assert "alice" in out

    def test_main_member_not_found(self, tmp_path):
        """main() exits with code 1 when --member ID is unknown."""
        config = _make_team_config()
        resolver = PathResolver(config)

        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            import importlib
            import status
            importlib.reload(status)
            with patch.object(status, "_detect_team_mode", return_value=(config, resolver)):
                with patch.object(sys, "argv", ["status.py", "--member", "unknown"]):
                    with pytest.raises(SystemExit) as exc_info:
                        status.main()
                    assert exc_info.value.code == 1
        finally:
            os.chdir(orig_cwd)
