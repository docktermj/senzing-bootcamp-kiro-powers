"""Regression guard for the What's New sections in POWER.md.

This read-only module guards the ``senzing-bootcamp/POWER.md`` What's New
structure against the confirmed Retention_Policy so the per-version notes
cannot silently accumulate again (Requirement 7). It reads the shipped
``POWER.md`` and ``CHANGELOG.md`` from disk and exposes no production API;
its helpers are stdlib-only and mirror (rather than import) the existing
``version.read_version_from_frontmatter`` behavior so the guard stays
self-contained.

The example-based assertions below cover Requirements 7.1, 7.2, 7.3, 1.1,
1.2, 2.1, and 3.1. The property-based tests (Feature: power-whats-new-cleanup,
Properties 1-3) are appended to this same module by later tasks (2.2, 2.3,
2.4); the helpers and constants here are shared by those tests.

Feature: power-whats-new-cleanup
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants — shipped file locations and the confirmed Retention_Policy
# ---------------------------------------------------------------------------

_POWER_MD_PATH = Path(__file__).resolve().parent.parent / "POWER.md"
_CHANGELOG_PATH = Path(__file__).resolve().parent.parent / "CHANGELOG.md"

# The exact CHANGELOG_Pointer sentence the retained section must end with.
_CHANGELOG_POINTER = "See the CHANGELOG for the full release history."

# Older_Whats_New_Sections the cleanup removed (used by the Property 3 guard
# added in a later task; kept here so the policy lives in one place).
_REMOVED_VERSIONS: list[str] = ["0.1.3", "1.0.0", "0.12.1", "0.12.0"]

# A Whats_New_Section heading: anchored ``## What's New in X.Y.Z``.
_WHATS_NEW_HEADING_RE = re.compile(r"^## What's New in (\d+\.\d+\.\d+)$")

# A Point_In_Time_Metric_Claim: a numeric value paired (in either order and
# within a short span on one line) with a metric keyword such as a passing- or
# failing-test count or a lint-violation count (e.g. "4,830 passed").
_METRIC_CLAIM_RE = re.compile(
    r"\d[\d,]*[^\n]{0,40}\b(?:passed|failed|violations)\b"
    r"|\b(?:passed|failed|violations)\b[^\n]{0,40}\d[\d,]*",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Pure helpers (stdlib-only, no production API)
# ---------------------------------------------------------------------------


def whats_new_versions(text: str) -> list[str]:
    """Return the ordered versions with a What's New heading in ``text``.

    Scans ``text`` line by line for headings matching the anchored pattern
    ``## What's New in X.Y.Z`` and returns the captured ``X.Y.Z`` versions in
    document order (no version missed, none spurious).

    Args:
        text: The Markdown document to scan.

    Returns:
        The versions, in order of appearance, that head a Whats_New_Section.
    """
    versions: list[str] = []
    for line in text.splitlines():
        match = _WHATS_NEW_HEADING_RE.match(line)
        if match:
            versions.append(match.group(1))
    return versions


def frontmatter_version(text: str) -> str:
    """Return the ``version`` field from the leading YAML frontmatter of ``text``.

    Mirrors the behavior of ``version.read_version_from_frontmatter``: locates
    the leading ``---``-delimited frontmatter block and returns the value of its
    ``version`` field with surrounding quotes and whitespace stripped.

    Args:
        text: The full text of a POWER.md-style document.

    Returns:
        The frontmatter ``version`` value (e.g. ``"0.2.0"``).

    Raises:
        ValueError: If no YAML frontmatter is present, the ``version`` field is
            missing, or the ``version`` field is empty — the message names the
            missing element so the guard fails loudly.
    """
    parts = text.split("---")
    if len(parts) < 3:
        raise ValueError(
            "POWER.md has no YAML frontmatter (missing '---' delimiters); "
            "cannot determine the frontmatter 'version' field."
        )

    frontmatter_block = parts[1]
    for line in frontmatter_block.splitlines():
        stripped = line.strip()
        if ":" not in stripped:
            continue
        key, _, raw_value = stripped.partition(":")
        if key.strip() == "version":
            value = raw_value.strip().strip('"').strip("'")
            if not value:
                raise ValueError(
                    "POWER.md frontmatter 'version' field is present but empty."
                )
            return value

    raise ValueError("POWER.md frontmatter has no 'version' field.")


def retained_section_body(text: str) -> str:
    """Return the body of the sole retained Whats_New_Section in ``text``.

    The body runs from the line after the first ``## What's New in X.Y.Z``
    heading up to (but excluding) the next level-2 ``## `` heading, or the end
    of the document.

    Args:
        text: The full text of a POWER.md-style document.

    Returns:
        The heading-exclusive body text of the retained section.

    Raises:
        ValueError: If ``text`` contains no What's New heading — the message
            names the missing element so the guard fails loudly.
    """
    lines = text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if _WHATS_NEW_HEADING_RE.match(line):
            start = index
            break

    if start is None:
        raise ValueError(
            "POWER.md contains no \"## What's New in X.Y.Z\" heading; "
            "cannot locate the retained What's New section."
        )

    body_lines: list[str] = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        body_lines.append(line)
    return "\n".join(body_lines)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def _read_power_md() -> str:
    """Return the shipped ``POWER.md`` text.

    Returns:
        The full UTF-8 contents of ``senzing-bootcamp/POWER.md``.
    """
    return _POWER_MD_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Example-based regression guard (Requirements 7.1, 7.2, 7.3, 1.1, 1.2, 2.1, 3.1)
# ---------------------------------------------------------------------------


class TestWhatsNewSectionsGuard:
    """Example-based guard over the real POWER.md What's New structure.

    Validates: Requirements 7.1, 7.2, 7.3, 1.1, 1.2, 2.1, 3.1
    """

    def test_exactly_one_section_and_it_is_the_frontmatter_version(self) -> None:
        """POWER.md has exactly one What's New section, the frontmatter version.

        Validates: Requirements 1.1, 1.2, 7.2
        """
        power_md = _read_power_md()
        current = frontmatter_version(power_md)
        found = whats_new_versions(power_md)
        assert found == [current], (
            f"Expected exactly one What's New section for the frontmatter "
            f"version {current!r}, but found {found!r}."
        )

    def test_no_disallowed_version_has_a_section(self) -> None:
        """No version other than the frontmatter version has a What's New section.

        Validates: Requirements 1.2, 1.3, 7.2
        """
        power_md = _read_power_md()
        current = frontmatter_version(power_md)
        disallowed = [v for v in whats_new_versions(power_md) if v != current]
        assert disallowed == [], (
            f"POWER.md contains What's New section(s) for disallowed "
            f"version(s) {disallowed!r}; only {current!r} is permitted."
        )

    def test_retained_section_ends_with_changelog_pointer(self) -> None:
        """The retained section's final non-empty line is the CHANGELOG pointer.

        Validates: Requirements 2.1, 7.3
        """
        power_md = _read_power_md()
        body = retained_section_body(power_md)
        non_empty = [line.strip() for line in body.splitlines() if line.strip()]
        assert non_empty, "The retained What's New section body is empty."
        assert non_empty[-1] == _CHANGELOG_POINTER, (
            f"Expected the retained section to end with {_CHANGELOG_POINTER!r}, "
            f"but its final non-empty line is {non_empty[-1]!r}."
        )

    def test_retained_section_has_no_point_in_time_metric_claim(self) -> None:
        """The retained section states no frozen point-in-time metric claim.

        Validates: Requirement 3.1
        """
        power_md = _read_power_md()
        body = retained_section_body(power_md)
        match = _METRIC_CLAIM_RE.search(body)
        assert match is None, (
            f"The retained What's New section contains a Point_In_Time_Metric_Claim: "
            f"{match.group(0)!r}."
        )

    def test_frontmatter_version_is_present(self) -> None:
        """POWER.md exposes a frontmatter version (fails loudly if missing).

        Validates: Requirement 1.2
        """
        power_md = _read_power_md()
        version = frontmatter_version(power_md)
        assert version, "POWER.md frontmatter 'version' field is missing or empty."

    def test_whats_new_heading_is_present(self) -> None:
        """POWER.md contains at least one What's New heading (fails loudly if none).

        Validates: Requirements 1.1, 7.1
        """
        power_md = _read_power_md()
        assert whats_new_versions(power_md), (
            "POWER.md contains no \"## What's New in X.Y.Z\" heading."
        )


# ---------------------------------------------------------------------------
# Strategies for the property-based tests (prefixed ``st_`` per conventions)
# ---------------------------------------------------------------------------


@st.composite
def st_semver(draw: st.DrawFn) -> str:
    """Draw a semantic-version string ``X.Y.Z`` with non-negative integer parts.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A version string of the form ``"<major>.<minor>.<patch>"`` that matches
        the anchored What's New heading pattern.
    """
    major = draw(st.integers(min_value=0, max_value=999))
    minor = draw(st.integers(min_value=0, max_value=999))
    patch = draw(st.integers(min_value=0, max_value=999))
    return f"{major}.{minor}.{patch}"


@st.composite
def st_section_body(draw: st.DrawFn) -> str:
    """Draw arbitrary section-body text containing no What's New heading line.

    Generates zero or more newline-free lines of arbitrary printable text, then
    drops any line that would itself match ``## What's New in X.Y.Z`` so the
    synthesized body can never introduce a spurious version into the document.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        The joined body text (possibly empty, possibly multi-line).
    """
    line_text = st.text(
        alphabet=st.characters(min_codepoint=32, max_codepoint=126),
        max_size=60,
    )
    lines = draw(st.lists(line_text, max_size=5))
    safe = [line for line in lines if not _WHATS_NEW_HEADING_RE.match(line)]
    return "\n".join(safe)


@st.composite
def st_whats_new_document(draw: st.DrawFn) -> tuple[list[str], str]:
    """Draw a distinct semver set and a Markdown document that heads each one.

    For each distinct version, synthesizes a ``## What's New in X.Y.Z`` heading
    followed by an arbitrary (heading-free) body, joined into a single document.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(versions, document)`` pair where ``versions`` is the list of
        distinct versions synthesized (document order) and ``document`` is the
        rendered Markdown text.
    """
    versions = draw(st.lists(st_semver(), unique=True, max_size=8))
    blocks: list[str] = []
    for version in versions:
        body = draw(st_section_body())
        block = f"## What's New in {version}"
        if body:
            block = f"{block}\n{body}"
        blocks.append(block)
    document = "\n\n".join(blocks)
    return versions, document


# ---------------------------------------------------------------------------
# Property 1 — What's New version detection round-trips
# ---------------------------------------------------------------------------


class TestWhatsNewVersionDetectionRoundTrips:
    """Round-trip guarantee for the ``whats_new_versions`` detection helper.

    Validates: Requirements 1.1, 1.3, 7.2
    """

    # Feature: power-whats-new-cleanup, Property 1: What's New version detection round-trips
    @given(case=st_whats_new_document())
    def test_version_detection_round_trips(self, case: tuple[list[str], str]) -> None:
        """``whats_new_versions`` recovers exactly the synthesized version set.

        For any set of distinct semver strings rendered as What's New headings
        with arbitrary bodies, the helper returns exactly that set — no version
        missed and no spurious version introduced.

        Validates: Requirements 1.1, 1.3, 7.2
        """
        versions, document = case
        found = whats_new_versions(document)

        assert set(found) == set(versions), (
            f"whats_new_versions did not round-trip: expected version set "
            f"{sorted(set(versions))!r}, got {sorted(set(found))!r}."
        )
        assert len(found) == len(versions), (
            f"whats_new_versions introduced duplicate/spurious versions: "
            f"expected {len(versions)} version(s), got {found!r}."
        )

# ---------------------------------------------------------------------------
# Property 2 — Only the current version has a What's New section
# ---------------------------------------------------------------------------

# The Current_Version recorded in the shipped POWER.md frontmatter, computed
# once so the Property 2 strategy can exclude it from the generated versions.
_CURRENT_VERSION = frontmatter_version(_read_power_md())


class TestOnlyCurrentVersionHasWhatsNewSection:
    """Only the frontmatter Current_Version heads a What's New section.

    Validates: Requirements 1.2, 1.3, 7.2
    """

    # Feature: power-whats-new-cleanup, Property 2: Only the current version has a What's New section
    @given(version=st_semver().filter(lambda v: v != _CURRENT_VERSION))
    def test_no_non_current_version_has_a_section(self, version: str) -> None:
        """The real POWER.md heads no What's New section for a non-current version.

        For any semver string that differs from the Current_Version recorded in
        the POWER.md frontmatter, POWER.md contains no ``## What's New in v``
        heading for that version.

        Validates: Requirements 1.2, 1.3, 7.2
        """
        power_md = _read_power_md()
        found = whats_new_versions(power_md)
        assert version not in found, (
            f"POWER.md unexpectedly contains a What's New section for "
            f"non-current version {version!r}; only {_CURRENT_VERSION!r} is permitted."
        )

# ---------------------------------------------------------------------------
# Property 3 — No release information is lost
# ---------------------------------------------------------------------------


def _read_changelog() -> str:
    """Return the shipped ``CHANGELOG.md`` text.

    Returns:
        The full UTF-8 contents of ``senzing-bootcamp/CHANGELOG.md``.
    """
    return _CHANGELOG_PATH.read_text(encoding="utf-8")


def _changelog_has_release_entry(changelog_text: str, version: str) -> bool:
    """Return whether ``changelog_text`` has a ``## [version]`` release entry.

    Matches the Keep a Changelog release heading for ``version`` — a level-2
    heading whose text opens with the literal bracketed version (e.g.
    ``## [1.0.0] - 2026-06-24``). The version's dots are escaped so ``0.1.3``
    cannot spuriously match ``0X1X3``.

    Args:
        changelog_text: The full text of CHANGELOG.md.
        version: The ``X.Y.Z`` version to look for.

    Returns:
        ``True`` if a ``## [version]`` release heading is present, else ``False``.
    """
    heading = re.compile(rf"^## \[{re.escape(version)}\]", re.MULTILINE)
    return heading.search(changelog_text) is not None


class TestNoReleaseInformationIsLost:
    """Every removed What's New version retains a CHANGELOG release entry.

    Validates: Requirements 2.3
    """

    # Feature: power-whats-new-cleanup, Property 3: No release information is lost
    def test_every_removed_version_has_a_changelog_release_entry(self) -> None:
        """Each removed version has a matching ``## [version]`` entry in CHANGELOG.md.

        For every version whose Older_Whats_New_Section the cleanup removed, the
        authoritative CHANGELOG retains a ``## [version]`` release entry, so the
        pruned per-version notes remain discoverable and no release information
        is lost.

        Validates: Requirements 2.3
        """
        changelog = _read_changelog()
        missing = [
            version
            for version in _REMOVED_VERSIONS
            if not _changelog_has_release_entry(changelog, version)
        ]
        assert missing == [], (
            f"CHANGELOG.md is missing a '## [version]' release entry for removed "
            f"version(s) {missing!r}; removing their What's New section from POWER.md "
            f"would lose release information."
        )
