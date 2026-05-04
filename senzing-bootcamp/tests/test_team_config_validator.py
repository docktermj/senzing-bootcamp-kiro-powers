"""Property-based and unit tests for team_config_validator.py.

Uses Hypothesis for PBT and pytest for example-based tests.
"""

from __future__ import annotations

import string
import tempfile
from pathlib import Path, PurePosixPath

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from team_config_validator import (
    PathResolver,
    TeamConfig,
    TeamConfigError,
    TeamMember,
    parse_team_yaml,
    validate_team_config,
    load_and_validate,
)


# ═══════════════════════════════════════════════════════════════════════════
# Hypothesis strategies
# ═══════════════════════════════════════════════════════════════════════════

# Safe identifier characters (no whitespace, no quotes, no colons)
_ID_CHARS = string.ascii_lowercase + string.digits + "_"

member_id_strategy = st.text(
    alphabet=_ID_CHARS, min_size=1, max_size=20
).filter(lambda s: s.strip() == s and len(s.strip()) > 0)

member_name_strategy = st.text(
    alphabet=string.ascii_letters + " ", min_size=1, max_size=40
).filter(lambda s: len(s.strip()) > 0)

repo_path_strategy = st.text(
    alphabet=string.ascii_lowercase + string.digits + "/_-",
    min_size=1,
    max_size=50,
).filter(lambda s: len(s.strip()) > 0 and "//" not in s)

mode_strategy = st.sampled_from(["colocated", "distributed"])


def valid_member_dict_strategy(with_repo_path: bool = False):
    """Strategy producing a valid member dict."""
    if with_repo_path:
        return st.fixed_dictionaries({
            "id": member_id_strategy,
            "name": member_name_strategy,
            "repo_path": repo_path_strategy,
        })
    return st.fixed_dictionaries({
        "id": member_id_strategy,
        "name": member_name_strategy,
    })


def valid_config_strategy():
    """Strategy producing a valid raw config dict."""
    @st.composite
    def _build(draw):
        mode = draw(mode_strategy)
        n = draw(st.integers(min_value=2, max_value=6))
        ids = draw(
            st.lists(
                member_id_strategy,
                min_size=n,
                max_size=n,
                unique=True,
            )
        )
        members = []
        for mid in ids:
            name = draw(member_name_strategy)
            m = {"id": mid, "name": name}
            if mode == "distributed":
                m["repo_path"] = draw(repo_path_strategy)
            members.append(m)
        team_name = draw(
            st.text(
                alphabet=string.ascii_letters + " ",
                min_size=1,
                max_size=30,
            ).filter(lambda s: len(s.strip()) > 0)
        )
        sources = draw(
            st.lists(
                st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=10),
                max_size=4,
            )
        )
        return {
            "team_name": team_name,
            "mode": mode,
            "members": members,
            "shared_data_sources": sources,
        }
    return _build()


# ═══════════════════════════════════════════════════════════════════════════
# Property 1: Valid configs accepted, invalid configs produce specific errors
# Feature: team-bootcamp, Property 1: Valid team configs are accepted,
# invalid configs produce specific errors
# Validates: Requirements 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 1.9, 9.2, 9.3,
#            9.4, 9.5, 9.6, 9.8
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty1ConfigValidation:
    """**Validates: Requirements 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 1.9,
    9.2, 9.3, 9.4, 9.5, 9.6, 9.8**"""

    @given(config=valid_config_strategy())
    @settings(max_examples=100)
    def test_valid_configs_accepted(self, config):
        """Valid configs produce no validation errors."""
        errors = validate_team_config(config)
        assert errors == [], f"Expected no errors for valid config, got: {errors}"

    @given(data=st.data())
    @settings(max_examples=100)
    def test_invalid_configs_produce_errors(self, data):
        """Configs with at least one violation produce non-empty error lists."""
        # Start with a valid config and break it in a random way
        base = data.draw(valid_config_strategy())
        mutation = data.draw(st.sampled_from([
            "remove_team_name",
            "empty_team_name",
            "remove_members",
            "empty_members",
            "one_member",
            "bad_mode",
            "empty_member_id",
            "empty_member_name",
            "distributed_no_repo",
        ]))

        if mutation == "remove_team_name":
            del base["team_name"]
        elif mutation == "empty_team_name":
            base["team_name"] = ""
        elif mutation == "remove_members":
            del base["members"]
        elif mutation == "empty_members":
            base["members"] = []
        elif mutation == "one_member":
            base["members"] = base["members"][:1]
        elif mutation == "bad_mode":
            base["mode"] = "invalid_mode"
        elif mutation == "empty_member_id":
            base["members"][0]["id"] = ""
        elif mutation == "empty_member_name":
            base["members"][0]["name"] = ""
        elif mutation == "distributed_no_repo":
            base["mode"] = "distributed"
            if "repo_path" in base["members"][0]:
                del base["members"][0]["repo_path"]

        errors = validate_team_config(base)
        assert len(errors) > 0, (
            f"Expected errors for mutation '{mutation}', got none"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Property 2: Path resolution produces correct mode-specific paths
# Feature: team-bootcamp, Property 2: Path resolution produces correct
# mode-specific paths for all file types
# Validates: Requirements 1.7, 2.6, 2.7, 3.5, 3.6, 4.6, 7.1, 7.2, 7.3,
#            7.4, 7.5, 8.3
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty2PathResolution:
    """**Validates: Requirements 1.7, 2.6, 2.7, 3.5, 3.6, 4.6, 7.1, 7.2,
    7.3, 7.4, 7.5, 8.3**"""

    @given(
        member_id=member_id_strategy,
        member_name=member_name_strategy,
        repo_path=repo_path_strategy,
    )
    @settings(max_examples=100)
    def test_colocated_paths_contain_member_id(
        self, member_id, member_name, repo_path
    ):
        """Co-located mode paths contain the member id as a suffix."""
        config = TeamConfig(
            team_name="Test",
            members=[],
            mode="colocated",
        )
        member = TeamMember(id=member_id, name=member_name, repo_path=repo_path)
        resolver = PathResolver(config)

        progress = resolver.progress_path(member)
        feedback = resolver.feedback_path(member)
        prefs = resolver.preferences_path(member)
        journal = resolver.journal_path(member)

        assert progress == PurePosixPath(f"config/progress_{member_id}.json")
        assert feedback == PurePosixPath(
            f"docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK_{member_id}.md"
        )
        assert prefs == PurePosixPath(f"config/preferences_{member_id}.yaml")
        assert journal == PurePosixPath(f"docs/bootcamp_journal_{member_id}.md")

        # All paths contain the member id
        for p in (progress, feedback, prefs, journal):
            assert member_id in str(p)

    @given(
        member_id=member_id_strategy,
        member_name=member_name_strategy,
        repo_path=repo_path_strategy,
    )
    @settings(max_examples=100)
    def test_distributed_paths_rooted_at_repo_path(
        self, member_id, member_name, repo_path
    ):
        """Distributed mode paths are rooted at the member's repo_path."""
        config = TeamConfig(
            team_name="Test",
            members=[],
            mode="distributed",
        )
        member = TeamMember(id=member_id, name=member_name, repo_path=repo_path)
        resolver = PathResolver(config)

        progress = resolver.progress_path(member)
        feedback = resolver.feedback_path(member)
        prefs = resolver.preferences_path(member)
        journal = resolver.journal_path(member)

        assert progress == PurePosixPath(
            f"{repo_path}/config/bootcamp_progress.json"
        )
        assert feedback == PurePosixPath(
            f"{repo_path}/docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md"
        )
        assert prefs == PurePosixPath(
            f"{repo_path}/config/bootcamp_preferences.yaml"
        )
        assert journal == PurePosixPath(
            f"{repo_path}/docs/bootcamp_journal.md"
        )

        # All paths start with repo_path
        for p in (progress, feedback, prefs, journal):
            assert str(p).startswith(repo_path)


# ═══════════════════════════════════════════════════════════════════════════
# Example-based unit tests
# ═══════════════════════════════════════════════════════════════════════════


class TestDuplicateIDs:
    """Duplicate member IDs produce a validation error."""

    def test_duplicate_ids_detected(self):
        raw = {
            "team_name": "Acme",
            "mode": "colocated",
            "members": [
                {"id": "alice", "name": "Alice"},
                {"id": "alice", "name": "Alice Clone"},
                {"id": "bob", "name": "Bob"},
            ],
        }
        errors = validate_team_config(raw)
        assert any("duplicate" in e.lower() for e in errors)
        assert any("alice" in e for e in errors)


class TestMissingRequiredFields:
    """Missing required fields produce specific errors."""

    def test_missing_team_name(self):
        raw = {
            "mode": "colocated",
            "members": [
                {"id": "a", "name": "A"},
                {"id": "b", "name": "B"},
            ],
        }
        errors = validate_team_config(raw)
        assert any("team_name" in e for e in errors)

    def test_missing_mode(self):
        raw = {
            "team_name": "T",
            "members": [
                {"id": "a", "name": "A"},
                {"id": "b", "name": "B"},
            ],
        }
        errors = validate_team_config(raw)
        assert any("mode" in e for e in errors)

    def test_missing_members(self):
        raw = {
            "team_name": "T",
            "mode": "colocated",
        }
        errors = validate_team_config(raw)
        assert any("members" in e for e in errors)

    def test_missing_member_id(self):
        raw = {
            "team_name": "T",
            "mode": "colocated",
            "members": [
                {"name": "A"},
                {"id": "b", "name": "B"},
            ],
        }
        errors = validate_team_config(raw)
        assert any("id" in e for e in errors)

    def test_missing_member_name(self):
        raw = {
            "team_name": "T",
            "mode": "colocated",
            "members": [
                {"id": "a"},
                {"id": "b", "name": "B"},
            ],
        }
        errors = validate_team_config(raw)
        assert any("name" in e for e in errors)


class TestInvalidMode:
    """Invalid mode values produce a validation error."""

    def test_invalid_mode(self):
        raw = {
            "team_name": "T",
            "mode": "hybrid",
            "members": [
                {"id": "a", "name": "A"},
                {"id": "b", "name": "B"},
            ],
        }
        errors = validate_team_config(raw)
        assert any("mode" in e for e in errors)


class TestDistributedWithoutRepoPath:
    """Distributed mode without repo_path produces errors."""

    def test_distributed_missing_repo_path(self):
        raw = {
            "team_name": "T",
            "mode": "distributed",
            "members": [
                {"id": "a", "name": "A"},
                {"id": "b", "name": "B", "repo_path": "/home/b/repo"},
            ],
        }
        errors = validate_team_config(raw)
        assert any("repo_path" in e for e in errors)
        # Only member 'a' should be flagged
        assert any("a" in e and "repo_path" in e for e in errors)

    def test_distributed_with_repo_path_valid(self):
        raw = {
            "team_name": "T",
            "mode": "distributed",
            "members": [
                {"id": "a", "name": "A", "repo_path": "/home/a/repo"},
                {"id": "b", "name": "B", "repo_path": "/home/b/repo"},
            ],
        }
        errors = validate_team_config(raw)
        assert errors == []


class TestParseTeamYaml:
    """Tests for the minimal YAML parser."""

    def test_parse_basic_config(self):
        content = """team_name: Acme ER Team
mode: colocated
shared_data_sources:
  - customers
  - vendors
members:
  - id: alice
    name: Alice Johnson
  - id: bob
    name: Bob Smith
"""
        result = parse_team_yaml(content)
        assert result["team_name"] == "Acme ER Team"
        assert result["mode"] == "colocated"
        assert result["shared_data_sources"] == ["customers", "vendors"]
        assert len(result["members"]) == 2
        assert result["members"][0]["id"] == "alice"
        assert result["members"][0]["name"] == "Alice Johnson"
        assert result["members"][1]["id"] == "bob"

    def test_parse_quoted_values(self):
        content = """team_name: "Quoted Team"
mode: 'colocated'
members:
  - id: "alice"
    name: 'Alice Johnson'
  - id: bob
    name: Bob
"""
        result = parse_team_yaml(content)
        assert result["team_name"] == "Quoted Team"
        assert result["mode"] == "colocated"
        assert result["members"][0]["id"] == "alice"
        assert result["members"][0]["name"] == "Alice Johnson"

    def test_parse_distributed_with_repo_path(self):
        content = """team_name: Distributed Team
mode: distributed
members:
  - id: alice
    name: Alice
    repo_path: /home/alice/repo
  - id: bob
    name: Bob
    repo_path: /home/bob/repo
"""
        result = parse_team_yaml(content)
        assert result["mode"] == "distributed"
        assert result["members"][0]["repo_path"] == "/home/alice/repo"
        assert result["members"][1]["repo_path"] == "/home/bob/repo"


class TestLoadAndValidate:
    """Tests for load_and_validate."""

    def test_load_valid_file(self, tmp_path):
        yaml_content = """team_name: Test Team
mode: colocated
members:
  - id: alice
    name: Alice
  - id: bob
    name: Bob
"""
        f = tmp_path / "team.yaml"
        f.write_text(yaml_content, encoding="utf-8")
        config = load_and_validate(str(f))
        assert config.team_name == "Test Team"
        assert config.mode == "colocated"
        assert len(config.members) == 2
        assert config.members[0].id == "alice"

    def test_load_missing_file(self):
        with pytest.raises(TeamConfigError, match="Cannot read"):
            load_and_validate("/nonexistent/team.yaml")

    def test_load_invalid_config(self, tmp_path):
        f = tmp_path / "team.yaml"
        f.write_text("team_name:\nmode: bad\n", encoding="utf-8")
        with pytest.raises(TeamConfigError, match="validation failed"):
            load_and_validate(str(f))
