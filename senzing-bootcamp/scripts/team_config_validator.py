#!/usr/bin/env python3
"""Senzing Bootcamp - Team Configuration Validator.

Provides team config parsing, validation, and path resolution for
multi-user bootcamp sessions.  Depends only on the Python standard
library and is cross-platform (Linux, macOS, Windows).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath


# ── Data classes ──────────────────────────────────────────────────────────


@dataclass
class TeamMember:
    """A single team member entry from team.yaml."""

    id: str
    name: str
    repo_path: str | None = None


@dataclass
class TeamConfig:
    """Parsed and validated team configuration."""

    team_name: str
    members: list[TeamMember]
    mode: str  # "colocated" | "distributed"
    shared_data_sources: list[str] = field(default_factory=list)


class TeamConfigError(Exception):
    """Raised when team.yaml validation fails."""


# ── Minimal YAML parser ──────────────────────────────────────────────────


def parse_team_yaml(content: str) -> dict:
    """Parse the restricted YAML subset used by team.yaml.

    Supports:
      - Top-level string scalars (``key: value``)
      - Top-level lists of strings (``- item``)
      - Top-level lists of dicts with string values (``- key: value``)

    Does NOT support anchors, aliases, multi-line strings, nested
    structures beyond one level, or any other advanced YAML features.
    """
    result: dict = {}
    lines = content.splitlines()
    idx = 0

    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        # Skip blank lines and comments
        if not stripped or stripped.startswith("#"):
            idx += 1
            continue

        # Top-level key: value
        match = re.match(r"^(\w[\w_]*):\s*(.*)", line)
        if not match:
            idx += 1
            continue

        key = match.group(1)
        value_part = match.group(2).strip()

        if value_part and not value_part.startswith("#"):
            # Scalar value — strip optional quotes
            result[key] = _unquote(value_part)
            idx += 1
            continue

        # Value is on subsequent indented lines (list)
        idx += 1
        items: list = []
        while idx < len(lines):
            child = lines[idx]
            child_stripped = child.strip()

            if not child_stripped or child_stripped.startswith("#"):
                idx += 1
                continue

            # Must be indented list item
            child_match = re.match(r"^(\s+)-\s+(.*)", child)
            if not child_match:
                break  # no longer part of this list

            item_value = child_match.group(2).strip()

            # Check if this is a dict entry (key: value)
            kv_match = re.match(r"^(\w[\w_]*):\s*(.*)", item_value)
            if kv_match:
                # Start of a dict item — collect all key: value pairs
                dict_item: dict[str, str] = {}
                dict_item[kv_match.group(1)] = _unquote(
                    kv_match.group(2).strip()
                )
                idx += 1
                # Collect continuation lines (indented key: value without -)
                while idx < len(lines):
                    cont = lines[idx]
                    cont_stripped = cont.strip()
                    if not cont_stripped or cont_stripped.startswith("#"):
                        idx += 1
                        continue
                    # Another "- " at same or lesser indent means new item
                    cont_list_match = re.match(r"^(\s+)-\s+", cont)
                    if cont_list_match:
                        break
                    # Non-indented line means end of list
                    if not cont.startswith(" ") and not cont.startswith("\t"):
                        break
                    # Indented key: value continuation
                    cont_kv = re.match(r"^\s+(\w[\w_]*):\s*(.*)", cont)
                    if cont_kv:
                        dict_item[cont_kv.group(1)] = _unquote(
                            cont_kv.group(2).strip()
                        )
                        idx += 1
                    else:
                        break
                items.append(dict_item)
            else:
                # Simple string list item
                items.append(_unquote(item_value))
                idx += 1

        result[key] = items

    return result


def _unquote(s: str) -> str:
    """Remove surrounding quotes from a YAML scalar value."""
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


# ── Validation ────────────────────────────────────────────────────────────

VALID_MODES = ("colocated", "distributed")


def validate_team_config(raw: dict) -> list[str]:
    """Validate a raw parsed team config dict.

    Returns a list of human-readable error strings.  An empty list
    means the config is valid.
    """
    errors: list[str] = []

    # team_name
    tn = raw.get("team_name")
    if not isinstance(tn, str) or not tn.strip():
        errors.append("'team_name' is missing or not a non-empty string")

    # mode
    mode = raw.get("mode")
    if not isinstance(mode, str) or mode not in VALID_MODES:
        errors.append(
            f"'mode' must be one of {VALID_MODES}, got {mode!r}"
        )

    # members
    members = raw.get("members")
    if not isinstance(members, list):
        errors.append("'members' is missing or not a list")
        return errors  # can't validate further

    if len(members) < 2:
        errors.append("'members' must contain at least 2 entries")

    seen_ids: set[str] = set()
    for i, m in enumerate(members):
        if not isinstance(m, dict):
            errors.append(f"members[{i}] is not a dict")
            continue

        mid = m.get("id")
        if not isinstance(mid, str) or not mid.strip():
            errors.append(f"members[{i}] has missing or empty 'id'")
        else:
            if mid in seen_ids:
                errors.append(f"duplicate member id: {mid!r}")
            seen_ids.add(mid)

        mname = m.get("name")
        if not isinstance(mname, str) or not mname.strip():
            errors.append(f"members[{i}] has missing or empty 'name'")

        # distributed mode requires repo_path
        if isinstance(mode, str) and mode == "distributed":
            rp = m.get("repo_path")
            if not isinstance(rp, str) or not rp.strip():
                errors.append(
                    f"members[{i}] (id={mid!r}) missing 'repo_path' "
                    f"(required in distributed mode)"
                )

    return errors


# ── Load & validate ──────────────────────────────────────────────────────


def load_and_validate(path: str = "config/team.yaml") -> TeamConfig:
    """Read, parse, validate, and return a TeamConfig.

    Raises TeamConfigError if the file cannot be read or validation
    fails.
    """
    from pathlib import Path

    p = Path(path)
    try:
        content = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise TeamConfigError(f"Cannot read {path}: {exc}") from exc

    raw = parse_team_yaml(content)
    errors = validate_team_config(raw)
    if errors:
        msg = "Team config validation failed:\n" + "\n".join(
            f"  - {e}" for e in errors
        )
        raise TeamConfigError(msg)

    members = [
        TeamMember(
            id=m["id"],
            name=m["name"],
            repo_path=m.get("repo_path") or None,
        )
        for m in raw["members"]
    ]

    return TeamConfig(
        team_name=raw["team_name"],
        members=members,
        mode=raw["mode"],
        shared_data_sources=raw.get("shared_data_sources", []),
    )


# ── Path resolver ─────────────────────────────────────────────────────────


class PathResolver:
    """Resolve per-member file paths based on team mode."""

    def __init__(self, config: TeamConfig) -> None:
        self._config = config

    def progress_path(self, member: TeamMember) -> PurePosixPath:
        """Return the path to a member's progress JSON."""
        if self._config.mode == "colocated":
            return PurePosixPath(f"config/progress_{member.id}.json")
        return PurePosixPath(
            f"{member.repo_path}/config/bootcamp_progress.json"
        )

    def feedback_path(self, member: TeamMember) -> PurePosixPath:
        """Return the path to a member's feedback markdown."""
        if self._config.mode == "colocated":
            return PurePosixPath(
                f"docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK_{member.id}.md"
            )
        return PurePosixPath(
            f"{member.repo_path}/docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md"
        )

    def preferences_path(self, member: TeamMember) -> PurePosixPath:
        """Return the path to a member's preferences YAML."""
        if self._config.mode == "colocated":
            return PurePosixPath(f"config/preferences_{member.id}.yaml")
        return PurePosixPath(
            f"{member.repo_path}/config/bootcamp_preferences.yaml"
        )

    def journal_path(self, member: TeamMember) -> PurePosixPath:
        """Return the path to a member's bootcamp journal."""
        if self._config.mode == "colocated":
            return PurePosixPath(f"docs/bootcamp_journal_{member.id}.md")
        return PurePosixPath(
            f"{member.repo_path}/docs/bootcamp_journal.md"
        )
