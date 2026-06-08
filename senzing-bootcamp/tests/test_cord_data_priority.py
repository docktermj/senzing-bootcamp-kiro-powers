"""Property-based and unit tests for CORD data priority hierarchy.

These tests verify that the senzing-bootcamp power consistently presents
CORD data before synthesized test data across all user-facing touchpoints,
and that the CORD reference URL is present wherever CORD is recommended.

Feature: cord-data-priority
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Regex patterns for detecting CORD and synthesized test data mentions
# ---------------------------------------------------------------------------

# Pattern to detect CORD mentions (case-insensitive).
# Matches: CORD, Collections Of Relatable Data, CORD datasets, CORD data,
# sample datasets (in context of CORD).
CORD_PATTERN = re.compile(
    r"\bCORD\b|Collections\s+Of\s+Relatable\s+Data|\bCORD\s+data(?:sets)?",
    re.IGNORECASE,
)

# Pattern to detect synthesized/generated test data mentions (case-insensitive).
# Matches: synthesized test data, generated test data, test data can be generated,
# generate test data, test data generation.
SYNTHESIZED_DATA_PATTERN = re.compile(
    r"synthesized\s+(?:test\s+)?data"
    r"|generated?\s+(?:test\s+)?data"
    r"|test\s+data\s+(?:can\s+(?:also\s+)?be\s+)?generat(?:ed|ion)"
    r"|data\s+(?:can\s+(?:also\s+)?be\s+)?generat(?:ed|ion)",
    re.IGNORECASE,
)

# CORD reference URL
CORD_URL = "https://senzing.com/senzing-ready-data-collections-cord/"

# Pattern to detect get_sample_data MCP tool reference
GET_SAMPLE_DATA_PATTERN = re.compile(r"get_sample_data", re.IGNORECASE)

# Pattern to detect on-demand CORD lookup language.
#
# The workspace security rule (.kiro/steering/security.md) forbids steering
# files from referencing external URLs ("Steering file referencing external
# URLs | MEDIUM | Use MCP tools or #[[file:]] references"). During the
# onboarding split, the CORD reference URL was intentionally removed from
# steering/onboarding-phase1b-intro-language.md and replaced with on-demand
# lookup language ("Ask me and I'll look up the current CORD details from the
# Senzing documentation on demand"). This pattern recognizes that intentional,
# security-rule-driven substitution so a steering file that directs the
# bootcamper to look up CORD details on demand is still considered compliant
# (the URL itself must NOT be re-added to the steering file).
ON_DEMAND_CORD_PATTERN = re.compile(
    r"look up the current CORD details[^.]*on demand"
    r"|ask me[^.]*CORD[^.]*on demand",
    re.IGNORECASE,
)

# Pattern verifying the on-demand substitution names an authoritative,
# security-compliant lookup source (the Senzing documentation / MCP server)
# in place of the removed external URL. Used as an independent content
# assertion so the relaxation is precise rather than a blanket pass.
ON_DEMAND_LOOKUP_SOURCE_PATTERN = re.compile(
    r"Senzing documentation|Senzing MCP|MCP server",
    re.IGNORECASE,
)

# Pattern to detect a CORD mention that is a PROHIBITION rather than a
# recommendation. Mirrors the prohibition-context logic in
# test_system_verification_properties.py. For example,
# steering/module-03-system-verification.md forbids CORD with the line
# "Do not use CORD, Las Vegas, London, Moscow, or any other dataset" — a
# forbidding mention must NOT be classified as a recommendation.
CORD_PROHIBITION_PATTERN = re.compile(
    r"do not use|shall not|must not|never use|no dataset choice|don.t use",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# File collection helpers
# ---------------------------------------------------------------------------


def collect_markdown_files() -> list[Path]:
    """Collect all Markdown files under the senzing-bootcamp/ directory.

    Excludes CHANGELOG.md since it is a historical record of past changes,
    not user-facing content that recommends data sources.

    Returns:
        Sorted list of Path objects for all .md files, excluding
        __pycache__, .pytest_cache, .hypothesis, and CHANGELOG.md.
    """
    files = list(_BOOTCAMP_DIR.rglob("*.md"))
    files = [
        f for f in files
        if "__pycache__" not in str(f)
        and ".pytest_cache" not in str(f)
        and ".hypothesis" not in str(f)
        and f.name != "CHANGELOG.md"
    ]
    return sorted(files)


def collect_files_mentioning_both(
    cord_pattern: re.Pattern[str] = CORD_PATTERN,
    synth_pattern: re.Pattern[str] = SYNTHESIZED_DATA_PATTERN,
) -> list[Path]:
    """Collect Markdown files that mention both CORD and synthesized test data.

    Args:
        cord_pattern: Compiled regex for CORD mentions.
        synth_pattern: Compiled regex for synthesized test data mentions.

    Returns:
        Sorted list of Path objects for files containing both patterns.
    """
    result: list[Path] = []
    for md_file in collect_markdown_files():
        content = md_file.read_text(encoding="utf-8")
        if cord_pattern.search(content) and synth_pattern.search(content):
            result.append(md_file)
    return sorted(result)


def collect_files_recommending_cord(
    cord_pattern: re.Pattern[str] = CORD_PATTERN,
) -> list[Path]:
    """Collect Markdown files that recommend CORD data to a bootcamper.

    A file is considered to *recommend* CORD only if it contains at least one
    CORD mention that is NOT in a prohibition/negative context. Files whose
    ONLY CORD mention forbids the dataset (e.g.
    steering/module-03-system-verification.md, which says "Do not use CORD,
    Las Vegas, London, Moscow, or any other dataset") are excluded — a
    forbidding mention is not a recommendation. This mirrors the
    prohibition-context logic in test_system_verification_properties.py.

    Args:
        cord_pattern: Compiled regex for CORD mentions.

    Returns:
        Sorted list of Path objects for files that recommend CORD.
    """
    result: list[Path] = []
    for md_file in collect_markdown_files():
        content = md_file.read_text(encoding="utf-8")
        if _has_cord_recommendation(content, cord_pattern):
            result.append(md_file)
    return sorted(result)


def _has_cord_recommendation(
    content: str,
    cord_pattern: re.Pattern[str] = CORD_PATTERN,
) -> bool:
    """Return True if content mentions CORD as a recommendation (not a prohibition).

    A CORD mention counts as a recommendation when it appears on a line that is
    not in a prohibition/negative context. If every CORD-bearing line forbids
    the dataset, the file is not recommending CORD.

    Args:
        content: The file content to inspect.
        cord_pattern: Compiled regex for CORD mentions.

    Returns:
        True if at least one non-prohibition CORD mention exists.
    """
    for line in content.splitlines():
        if cord_pattern.search(line) and not CORD_PROHIBITION_PATTERN.search(line):
            return True
    return False


def first_match_line(content: str, pattern: re.Pattern[str]) -> int | None:
    """Find the line number (1-indexed) of the first match for a pattern.

    Args:
        content: The file content to search.
        pattern: Compiled regex pattern to search for.

    Returns:
        1-indexed line number of the first match, or None if not found.
    """
    for i, line in enumerate(content.splitlines(), start=1):
        if pattern.search(line):
            return i
    return None


# ---------------------------------------------------------------------------
# Precomputed file lists for Hypothesis strategies
# ---------------------------------------------------------------------------

_FILES_WITH_BOTH = collect_files_mentioning_both()
_FILES_RECOMMENDING_CORD = collect_files_recommending_cord()


# ---------------------------------------------------------------------------
# Property-based test class
# ---------------------------------------------------------------------------


class TestCordDataPriorityProperties:
    """Property-based tests for cross-file CORD data priority consistency.

    Validates that the data recommendation hierarchy (own data > CORD >
    synthesized test data) is maintained across all Markdown files in the
    senzing-bootcamp power.
    """

    # Feature: cord-data-priority, Property 1: CORD precedes synthesized test data
    @pytest.mark.skipif(
        not _FILES_WITH_BOTH,
        reason="No Markdown files found mentioning both CORD and synthesized data",
    )
    @given(md_file=st.sampled_from(_FILES_WITH_BOTH or [Path(".")]))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_cord_precedes_synthesized_data(self, md_file: Path) -> None:
        """CORD mention appears before synthesized test data mention in every file.

        For any Markdown file under senzing-bootcamp/ that mentions both CORD
        and synthesized test data, the first CORD mention must appear at a
        lower line number than the first synthesized test data mention.
        When both appear on the same line, CORD must appear first (lower
        character offset).

        **Validates: Requirements 1.1, 1.2, 7.1, 7.2**
        """
        content = md_file.read_text(encoding="utf-8")

        cord_line = first_match_line(content, CORD_PATTERN)
        synth_line = first_match_line(content, SYNTHESIZED_DATA_PATTERN)

        assert cord_line is not None, (
            f"Expected CORD mention in {md_file.relative_to(_BOOTCAMP_DIR)}"
        )
        assert synth_line is not None, (
            f"Expected synthesized data mention in {md_file.relative_to(_BOOTCAMP_DIR)}"
        )

        if cord_line == synth_line:
            # Same line — verify CORD appears first by character position
            line_text = content.splitlines()[cord_line - 1]
            cord_pos = CORD_PATTERN.search(line_text)
            synth_pos = SYNTHESIZED_DATA_PATTERN.search(line_text)
            assert cord_pos is not None and synth_pos is not None
            assert cord_pos.start() < synth_pos.start(), (
                f"In {md_file.relative_to(_BOOTCAMP_DIR)} line {cord_line}: "
                f"CORD appears at position {cord_pos.start()} but synthesized "
                f"test data appears at position {synth_pos.start()}. "
                f"CORD must precede synthesized test data."
            )
        else:
            assert cord_line < synth_line, (
                f"In {md_file.relative_to(_BOOTCAMP_DIR)}: "
                f"CORD first appears at line {cord_line} but synthesized test data "
                f"first appears at line {synth_line}. "
                f"CORD must precede synthesized test data."
            )

    # Feature: cord-data-priority, Property 2: CORD reference URL present wherever
    # CORD is recommended
    @pytest.mark.skipif(
        not _FILES_RECOMMENDING_CORD,
        reason="No Markdown files found recommending CORD data",
    )
    @given(md_file=st.sampled_from(_FILES_RECOMMENDING_CORD or [Path(".")]))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_cord_url_present_where_cord_recommended(self, md_file: Path) -> None:
        """Files recommending CORD reference the URL, get_sample_data, or on-demand lookup.

        For any Markdown file under senzing-bootcamp/ that recommends CORD data,
        the file must contain ONE of:
          - the CORD reference URL, OR
          - a reference to the get_sample_data MCP tool, OR
          - on-demand CORD lookup language.

        The on-demand branch reflects an intentional, security-rule-driven
        change: .kiro/steering/security.md forbids steering files from
        referencing external URLs, so during the onboarding split the CORD URL
        was removed from steering/onboarding-phase1b-intro-language.md and
        replaced with "Ask me and I'll look up the current CORD details from
        the Senzing documentation on demand". To keep the relaxation precise
        (not a blanket pass), the on-demand branch additionally requires the
        text to name an authoritative lookup source (the Senzing documentation
        / MCP server) in place of the removed URL.

        **Validates: Requirements 2.3, 2.4, 2.6, 2.9, 3.2, 4.3, 5.3**
        """
        content = md_file.read_text(encoding="utf-8")
        has_cord_url = CORD_URL in content
        has_get_sample_data = GET_SAMPLE_DATA_PATTERN.search(content) is not None
        has_on_demand_lookup = (
            ON_DEMAND_CORD_PATTERN.search(content) is not None
            and ON_DEMAND_LOOKUP_SOURCE_PATTERN.search(content) is not None
        )
        assert has_cord_url or has_get_sample_data or has_on_demand_lookup, (
            f"File {md_file.relative_to(_BOOTCAMP_DIR)} recommends CORD data but "
            f"contains none of: the CORD URL ({CORD_URL}), a reference to "
            f"get_sample_data, or on-demand CORD lookup language that names the "
            f"Senzing documentation / MCP server as the source"
        )


# ---------------------------------------------------------------------------
# Example-based unit test class
# ---------------------------------------------------------------------------


class TestCordDataPriorityExamples:
    """Example-based tests for specific file requirements.

    Validates individual acceptance criteria on specific files to ensure
    each touchpoint correctly implements the CORD data priority hierarchy.
    """

    def test_onboarding_flow_cord_in_step4(self) -> None:
        """Bootcamp Introduction step mentions CORD with description, before synthesized data.

        The Bootcamp Introduction (which carries the CORD overview bullet) was
        moved out of onboarding-flow.md into onboarding-phase1b-intro-language.md
        (shipped Step 5).

        Validates: Requirements 2.1, 2.2, 2.4
        """
        path = _BOOTCAMP_DIR / "steering" / "onboarding-phase1b-intro-language.md"
        content = path.read_text(encoding="utf-8")

        # Requirement 2.1: CORD is mentioned in the Bootcamp Introduction section
        step4_marker = content.find("## 5. Bootcamp Introduction")
        assert step4_marker != -1, (
            "Bootcamp Introduction section not found in "
            "onboarding-phase1b-intro-language.md"
        )
        step4_content = content[step4_marker:]

        assert CORD_PATTERN.search(step4_content), (
            "CORD is not mentioned in the Bootcamp Introduction step of "
            "onboarding-phase1b-intro-language.md"
        )

        # Requirement 2.2: CORD description (curated/entity resolution evaluation)
        assert re.search(
            r"curated.*entity resolution|entity resolution.*evaluation",
            step4_content,
            re.IGNORECASE,
        ), (
            "CORD description (curated/entity resolution evaluation) "
            "not found in the Bootcamp Introduction step of "
            "onboarding-phase1b-intro-language.md"
        )

        # Requirement 2.4: CORD appears before synthesized test data
        cord_match = CORD_PATTERN.search(step4_content)
        synth_match = SYNTHESIZED_DATA_PATTERN.search(step4_content)
        assert cord_match is not None, (
            "CORD mention not found in the Bootcamp Introduction step of "
            "onboarding-phase1b-intro-language.md"
        )
        assert synth_match is not None, (
            "Synthesized test data mention not found in the Bootcamp "
            "Introduction step of onboarding-phase1b-intro-language.md"
        )
        assert cord_match.start() < synth_match.start(), (
            f"CORD (pos {cord_match.start()}) does not appear before synthesized "
            f"test data (pos {synth_match.start()}) in the Bootcamp Introduction "
            f"step of onboarding-phase1b-intro-language.md"
        )

    def test_power_md_cord_primary(self) -> None:
        """POWER.md leads with CORD, retains get_sample_data.

        Validates: Requirements 3.1, 3.3, 3.4
        """
        path = _BOOTCAMP_DIR / "POWER.md"
        content = path.read_text(encoding="utf-8")

        # Requirement 3.1: CORD is mentioned before synthesized test data
        cord_match = CORD_PATTERN.search(content)
        synth_match = SYNTHESIZED_DATA_PATTERN.search(content)
        assert cord_match is not None, "CORD mention not found in POWER.md"
        assert synth_match is not None, (
            "Synthesized test data mention not found in POWER.md"
        )
        assert cord_match.start() < synth_match.start(), (
            f"CORD (pos {cord_match.start()}) does not appear before synthesized "
            f"test data (pos {synth_match.start()}) in POWER.md"
        )

        # Requirement 3.4: get_sample_data tool reference is present
        assert GET_SAMPLE_DATA_PATTERN.search(content), (
            "get_sample_data tool reference not found in POWER.md"
        )

        # Requirement 3.3 (implicit): CORD URL is present
        assert CORD_URL in content, (
            f"CORD URL ({CORD_URL}) not found in POWER.md"
        )

    def test_quick_start_cord_first(self) -> None:
        """QUICK_START.md recommends CORD before synthesized.

        Validates: Requirements 4.1, 4.2
        """
        path = _BOOTCAMP_DIR / "docs" / "guides" / "QUICK_START.md"
        content = path.read_text(encoding="utf-8")

        # Requirement 4.1: CORD is mentioned before synthesized test data
        cord_match = CORD_PATTERN.search(content)
        synth_match = SYNTHESIZED_DATA_PATTERN.search(content)
        assert cord_match is not None, "CORD mention not found in QUICK_START.md"
        assert synth_match is not None, (
            "Synthesized test data mention not found in QUICK_START.md"
        )
        assert cord_match.start() < synth_match.start(), (
            f"CORD (pos {cord_match.start()}) does not appear before synthesized "
            f"test data (pos {synth_match.start()}) in QUICK_START.md"
        )

        # Requirement 4.2: get_sample_data or CORD URL is referenced
        has_tool = GET_SAMPLE_DATA_PATTERN.search(content)
        has_url = CORD_URL in content
        assert has_tool or has_url, (
            "Neither get_sample_data tool nor CORD URL found in QUICK_START.md"
        )

    def test_module04_cord_hierarchy(self) -> None:
        """Module 4 steering recommends CORD first, synthesized as fallback.

        Validates: Requirements 5.1, 5.2
        """
        path = _BOOTCAMP_DIR / "steering" / "module-04-data-collection.md"
        content = path.read_text(encoding="utf-8")

        # Requirement 5.1: CORD is recommended before synthesized test data
        cord_line = first_match_line(content, CORD_PATTERN)
        synth_line = first_match_line(content, SYNTHESIZED_DATA_PATTERN)
        assert cord_line is not None, (
            "CORD mention not found in module-04-data-collection.md"
        )
        assert synth_line is not None, (
            "Synthesized test data mention not found in module-04-data-collection.md"
        )
        assert cord_line < synth_line, (
            f"CORD (line {cord_line}) does not appear before synthesized test data "
            f"(line {synth_line}) in module-04-data-collection.md"
        )

        # Requirement 5.2: CORD URL is present
        assert CORD_URL in content, (
            f"CORD URL ({CORD_URL}) not found in module-04-data-collection.md"
        )

    def test_onboarding_checklist_cord(self) -> None:
        """Checklist mentions CORD as primary, synthesized as fallback.

        Validates: Requirements 6.1, 6.2
        """
        path = _BOOTCAMP_DIR / "docs" / "guides" / "ONBOARDING_CHECKLIST.md"
        content = path.read_text(encoding="utf-8")

        # Requirement 6.1: CORD is mentioned as primary sample data option
        assert CORD_PATTERN.search(content), (
            "CORD mention not found in ONBOARDING_CHECKLIST.md"
        )

        # Requirement 6.2: Synthesized test data is positioned as fallback (after CORD)
        cord_match = CORD_PATTERN.search(content)
        synth_match = SYNTHESIZED_DATA_PATTERN.search(content)
        assert cord_match is not None, (
            "CORD mention not found in ONBOARDING_CHECKLIST.md"
        )
        assert synth_match is not None, (
            "Synthesized test data mention not found in ONBOARDING_CHECKLIST.md"
        )
        assert cord_match.start() < synth_match.start(), (
            f"CORD (pos {cord_match.start()}) does not appear before synthesized "
            f"test data (pos {synth_match.start()}) in ONBOARDING_CHECKLIST.md"
        )
