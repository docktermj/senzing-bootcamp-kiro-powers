"""Example test for versioning and back-compat (kiro-1-0-migration task 15.3).

Feature: kiro-1-0-migration

Validates the recorded back-compatibility decision and version bump for the
Kiro 1.0 migration against the *real shipped artifacts* under
``senzing-bootcamp/`` (a concrete example/edge test, not a Hypothesis property
test):

- No legacy ``*.kiro.hook`` files remain in ``senzing-bootcamp/hooks/`` so only
  v1 definitions ship (Req 13.1).
- ``POWER.md`` declares the Power requires Kiro 1.0 or later (Req 13.2).
- ``CHANGELOG.md`` records the migration under a new *released* version section
  (a ``## [x.y.z] - <date>`` heading, not ``[Unreleased]``) in Keep a Changelog
  format, with a version greater than the ``0.1.3`` baseline (Req 13.3).
- ``VERSION`` holds a new semantic version greater than ``0.1.3`` (Req 13.4).
- The ``POWER.md`` frontmatter version equals ``VERSION`` (Req 13.5).

The version parsing/validation reuses the shipped version-consistency helper
``senzing-bootcamp/scripts/version.py`` (``read_version``,
``read_version_from_frontmatter``, ``parse_version``) rather than re-parsing, so
this test and the Power stay tied to one definition of "valid semver".

**Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.5**
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (resolved absolutely so the test is cwd-independent)
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
_POWER_ROOT = _REPO_ROOT / "senzing-bootcamp"

HOOKS_DIR: Path = _POWER_ROOT / "hooks"
VERSION_FILE: Path = _POWER_ROOT / "VERSION"
POWER_MD: Path = _POWER_ROOT / "POWER.md"
CHANGELOG_MD: Path = _POWER_ROOT / "CHANGELOG.md"

# Reuse the shipped version-consistency helper (single definition of semver).
_SCRIPTS_DIR = str(_POWER_ROOT / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import version as version_helper  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The minimum bar: VERSION and the newest released CHANGELOG section must both
# exceed this. Compared as a (major, minor, patch) tuple (Req 13.4).
BASELINE_VERSION: tuple[int, int, int] = (0, 1, 3)

# Robust, case-insensitive ways POWER.md may state the Kiro 1.0 requirement.
# Any one match satisfies "the Power requires Kiro 1.0 or later" (Req 13.2).
_KIRO_REQUIREMENT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"requires?\s+kiro\s+1\.0", re.IGNORECASE),
    re.compile(r"kiro\s+1\.0\s+or\s+later", re.IGNORECASE),
)

# Keep a Changelog released-section heading: "## [x.y.z] - YYYY-MM-DD".
# The date requirement excludes the undated "## [Unreleased]" section.
_RELEASED_SECTION_RE: re.Pattern[str] = re.compile(
    r"^##\s+\[(?P<version>\d+\.\d+\.\d+)\]\s+-\s+(?P<date>\d{4}-\d{2}-\d{2})",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _released_versions(changelog_text: str) -> list[tuple[str, str]]:
    """Return ``(version, date)`` pairs for every released CHANGELOG section.

    A released section is a Keep a Changelog heading carrying a date, e.g.
    ``## [0.2.0] - 2026-07-07``. The undated ``## [Unreleased]`` heading is
    intentionally excluded.
    """
    return [
        (m.group("version"), m.group("date"))
        for m in _RELEASED_SECTION_RE.finditer(changelog_text)
    ]


def _version_tuple(version: str) -> tuple[int, int, int]:
    """Validate ``version`` as strict semver and return its integer tuple."""
    return version_helper.parse_version(version_helper.validate_version(version))


# ===========================================================================
# TestNoLegacyHookFiles  (Requirement 13.1)
# ===========================================================================


class TestNoLegacyHookFiles:
    """Only v1 definitions ship — no legacy ``*.kiro.hook`` files remain.

    Feature: kiro-1-0-migration
    **Validates: Requirements 13.1**
    """

    def test_hooks_dir_exists(self) -> None:
        """The shipped hooks directory exists."""
        assert HOOKS_DIR.is_dir(), f"Hooks directory not found at {HOOKS_DIR}"

    def test_no_kiro_hook_files_remain(self) -> None:
        """No ``*.kiro.hook`` file remains in ``senzing-bootcamp/hooks/``."""
        legacy = sorted(HOOKS_DIR.glob("*.kiro.hook"))
        assert not legacy, (
            "legacy *.kiro.hook files must be removed so only v1 definitions "
            f"ship; found {sorted(p.name for p in legacy)}"
        )


# ===========================================================================
# TestPowerRequiresKiro10  (Requirement 13.2)
# ===========================================================================


class TestPowerRequiresKiro10:
    """POWER.md declares the Power requires Kiro 1.0 or later.

    Feature: kiro-1-0-migration
    **Validates: Requirements 13.2**
    """

    def test_power_md_exists(self) -> None:
        """POWER.md exists."""
        assert POWER_MD.is_file(), f"POWER.md not found at {POWER_MD}"

    def test_power_md_declares_kiro_1_0_requirement(self) -> None:
        """POWER.md states the Power requires Kiro 1.0 or later."""
        text = POWER_MD.read_text(encoding="utf-8")
        matched = [p.pattern for p in _KIRO_REQUIREMENT_PATTERNS if p.search(text)]
        assert matched, (
            "POWER.md must declare that the Power requires Kiro 1.0 or later "
            "(expected a statement like 'requires Kiro 1.0 or later'); "
            "no matching statement found"
        )


# ===========================================================================
# TestChangelogReleasedSection  (Requirement 13.3)
# ===========================================================================


class TestChangelogReleasedSection:
    """CHANGELOG.md records the migration under a new released section.

    Feature: kiro-1-0-migration
    **Validates: Requirements 13.3**
    """

    def test_changelog_exists(self) -> None:
        """CHANGELOG.md exists."""
        assert CHANGELOG_MD.is_file(), f"CHANGELOG.md not found at {CHANGELOG_MD}"

    def test_changelog_has_a_released_section(self) -> None:
        """At least one dated Keep a Changelog released section exists."""
        released = _released_versions(CHANGELOG_MD.read_text(encoding="utf-8"))
        assert released, (
            "CHANGELOG.md must contain at least one released section in "
            "'## [x.y.z] - YYYY-MM-DD' (Keep a Changelog) format"
        )

    def test_changelog_has_new_released_section_above_baseline(self) -> None:
        """A released section with a version greater than the 0.1.3 baseline exists.

        This is the *new* released section recording the migration (e.g.
        ``## [0.2.0] - <date>``) — distinct from the undated ``[Unreleased]``
        heading, which is not counted.
        """
        released = _released_versions(CHANGELOG_MD.read_text(encoding="utf-8"))
        newer = [(v, d) for (v, d) in released if _version_tuple(v) > BASELINE_VERSION]
        assert newer, (
            "CHANGELOG.md must record a new released section with a version "
            f"greater than {'.'.join(map(str, BASELINE_VERSION))}; "
            f"released sections found: {released}"
        )

    def test_current_version_has_a_released_changelog_entry(self) -> None:
        """The current ``VERSION`` appears as a dated released CHANGELOG section.

        Ties the version bump (Req 13.4) to the changelog record (Req 13.3): the
        shipped version must have its own released section, not merely sit under
        ``[Unreleased]``.
        """
        current = version_helper.read_version(VERSION_FILE)
        released_versions = {
            v for (v, _d) in _released_versions(CHANGELOG_MD.read_text(encoding="utf-8"))
        }
        assert current in released_versions, (
            f"the current VERSION {current!r} must have a dated released section "
            f"in CHANGELOG.md; released versions found: {sorted(released_versions)}"
        )


# ===========================================================================
# TestVersionBump  (Requirement 13.4)
# ===========================================================================


class TestVersionBump:
    """VERSION holds a new semantic version greater than 0.1.3.

    Feature: kiro-1-0-migration
    **Validates: Requirements 13.4**
    """

    def test_version_file_exists(self) -> None:
        """The VERSION file exists."""
        assert VERSION_FILE.is_file(), f"VERSION file not found at {VERSION_FILE}"

    def test_version_is_valid_semver(self) -> None:
        """VERSION contains a strict MAJOR.MINOR.PATCH semantic version."""
        # read_version validates strict semver and raises on any deviation.
        version = version_helper.read_version(VERSION_FILE)
        assert isinstance(version, str) and version

    def test_version_greater_than_baseline(self) -> None:
        """VERSION parses to a semantic version greater than 0.1.3."""
        version = version_helper.read_version(VERSION_FILE)
        assert _version_tuple(version) > BASELINE_VERSION, (
            f"VERSION must be greater than {'.'.join(map(str, BASELINE_VERSION))}; "
            f"found {version!r}"
        )


# ===========================================================================
# TestFrontmatterVersionMatchesVersion  (Requirement 13.5)
# ===========================================================================


class TestFrontmatterVersionMatchesVersion:
    """The POWER.md frontmatter version equals the VERSION file value.

    Feature: kiro-1-0-migration
    **Validates: Requirements 13.5**
    """

    def test_frontmatter_version_equals_version_file(self) -> None:
        """POWER.md frontmatter ``version`` equals the VERSION file value."""
        file_version = version_helper.read_version(VERSION_FILE)
        frontmatter_version = version_helper.read_version_from_frontmatter(
            POWER_MD.read_text(encoding="utf-8")
        )
        assert frontmatter_version == file_version, (
            "POWER.md frontmatter version must equal the VERSION file value; "
            f"frontmatter={frontmatter_version!r}, VERSION={file_version!r}"
        )
