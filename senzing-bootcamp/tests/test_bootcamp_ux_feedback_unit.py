"""Unit tests for bootcamp UX feedback onboarding bullet order.

Verifies that the Step 4 overview bullets in onboarding-flow.md are in the
correct order after the reorder: Tracks → License → Test data, with the
guided-discovery preamble first and glossary reference last.

Feature: bootcamp-ux-feedback
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"
_ONBOARDING_FLOW: Path = _STEERING_DIR / "onboarding-flow.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# The expected bullet substrings in order for the three reordered bullets.
_TRACKS_BULLET = "Tracks let you skip to what matters"
_LICENSE_BULLET = "Built-in 500-record eval license; bring your own for more"
_TEST_DATA_BULLET = (
    "Test data available anytime. Three sample datasets: Las Vegas, London, Moscow"
)

# Preamble and glossary markers
_PREAMBLE_MARKER = "guided discovery"
_GLOSSARY_MARKER = "glossary"


def _get_step4_bullets() -> list[str]:
    """Extract the bullet list from Step 4 overview section.

    Returns the bullet lines between the 'Present the overview' instruction
    and the next heading (### 4a).
    """
    content = _ONBOARDING_FLOW.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Find the start of the bullet list (after "Present the overview")
    bullet_start: int | None = None
    bullet_end: int | None = None

    for idx, line in enumerate(lines):
        if "Present the overview" in line and "Cover all points" in line:
            bullet_start = idx + 1
        elif bullet_start is not None and re.match(r"^###\s+4a", line):
            bullet_end = idx
            break

    assert bullet_start is not None, (
        "Could not find 'Present the overview' instruction in Step 4"
    )
    assert bullet_end is not None, (
        "Could not find '### 4a' heading after Step 4 bullets"
    )

    # Extract only lines that start with '- ' (bullet points)
    bullets = [
        line.strip()
        for line in lines[bullet_start:bullet_end]
        if line.strip().startswith("- ")
    ]
    return bullets


class TestOnboardingBulletOrder:
    """Unit tests for onboarding Step 4 bullet reorder.

    Validates: Requirements 1.1, 1.2, 1.3
    """

    def test_reordered_bullets_in_correct_sequence(self) -> None:
        """Verify the three reordered bullets appear as Tracks → License → Test data.

        Validates: Requirement 1.1
        """
        bullets = _get_step4_bullets()
        bullet_text = "\n".join(bullets)

        tracks_idx = bullet_text.find(_TRACKS_BULLET)
        license_idx = bullet_text.find(_LICENSE_BULLET)
        test_data_idx = bullet_text.find(_TEST_DATA_BULLET)

        assert tracks_idx != -1, (
            f"Tracks bullet not found in Step 4. Bullets:\n{bullet_text}"
        )
        assert license_idx != -1, (
            f"License bullet not found in Step 4. Bullets:\n{bullet_text}"
        )
        assert test_data_idx != -1, (
            f"Test data bullet not found in Step 4. Bullets:\n{bullet_text}"
        )

        assert tracks_idx < license_idx, (
            "Tracks bullet must appear before License bullet"
        )
        assert license_idx < test_data_idx, (
            "License bullet must appear before Test data bullet"
        )

    def test_all_original_bullets_present(self) -> None:
        """Verify all original bullet points are present with unaltered text.

        Validates: Requirement 1.2
        """
        bullets = _get_step4_bullets()
        bullet_text = "\n".join(bullets)

        expected_fragments = [
            "guided discovery",
            "Goal: comfortable generating Senzing SDK code",
            "Module overview table (1-11)",
            _TRACKS_BULLET,
            _LICENSE_BULLET,
            _TEST_DATA_BULLET,
            "glossary at `docs/guides/GLOSSARY.md`",
        ]

        for fragment in expected_fragments:
            assert fragment in bullet_text, (
                f"Expected bullet fragment not found: '{fragment}'\n"
                f"Bullets:\n{bullet_text}"
            )

    def test_preamble_is_first_bullet(self) -> None:
        """Verify guided-discovery preamble is the first bullet.

        Validates: Requirement 1.3
        """
        bullets = _get_step4_bullets()
        assert len(bullets) > 0, "No bullets found in Step 4"
        assert _PREAMBLE_MARKER in bullets[0].lower(), (
            f"First bullet must be the guided-discovery preamble.\n"
            f"Got: {bullets[0]}"
        )

    def test_glossary_reference_is_last_bullet(self) -> None:
        """Verify glossary reference is the last bullet.

        Validates: Requirement 1.3
        """
        bullets = _get_step4_bullets()
        assert len(bullets) > 0, "No bullets found in Step 4"
        assert _GLOSSARY_MARKER in bullets[-1].lower(), (
            f"Last bullet must be the glossary reference.\n"
            f"Got: {bullets[-1]}"
        )


# ---------------------------------------------------------------------------
# Delivery-Mode Section Tests
# ---------------------------------------------------------------------------

_VISUALIZATION_PROTOCOL: Path = _STEERING_DIR / "visualization-protocol.md"


def _get_protocol_content() -> str:
    """Read the full content of visualization-protocol.md.

    Returns:
        The file content as a string.
    """
    return _VISUALIZATION_PROTOCOL.read_text(encoding="utf-8")


def _get_section_content(heading: str) -> str:
    """Extract the content of a specific ## section from visualization-protocol.md.

    Args:
        heading: The exact heading text (without the ## prefix).

    Returns:
        The section content from the heading line to the next ## heading.
    """
    content = _get_protocol_content()
    lines = content.splitlines()

    start: int | None = None
    end: int | None = None

    for idx, line in enumerate(lines):
        if line.strip() == f"## {heading}":
            start = idx
        elif start is not None and re.match(r"^## ", line):
            end = idx
            break

    assert start is not None, f"Section '## {heading}' not found in visualization-protocol.md"

    if end is None:
        end = len(lines)

    return "\n".join(lines[start:end])


class TestDeliveryModeSection:
    """Unit tests for delivery-mode section in visualization-protocol.md.

    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.7
    """

    def test_delivery_mode_question_with_both_options(self) -> None:
        """Verify visualization-protocol.md contains the delivery-mode question with both options.

        Validates: Requirement 2.1
        """
        section = _get_section_content("Delivery-Mode Selection")

        # Check that both delivery-mode options are present
        assert "Static HTML" in section, (
            "Delivery-mode section must include 'Static HTML' option"
        )
        assert "Web service + HTML" in section, (
            "Delivery-mode section must include 'Web service + HTML' option"
        )

        # Verify the numbered list format with descriptions
        assert "Self-contained file" in section or "data baked in" in section, (
            "Static HTML option must include description about self-contained/baked-in data"
        )
        assert "localhost HTTP service" in section or "live SDK queries" in section, (
            "Web service option must include description about live queries"
        )

    def test_section_ordering_after_type_selection_before_dispatch(self) -> None:
        """Verify delivery-mode section appears after type selection and before dispatch rules.

        Validates: Requirement 2.2
        """
        content = _get_protocol_content()

        # Find positions of the three relevant sections
        offer_pos = content.find("## Offer Template")
        delivery_pos = content.find("## Delivery-Mode Selection")
        dispatch_pos = content.find("## Dispatch Rules")

        assert offer_pos != -1, "Offer Template section not found"
        assert delivery_pos != -1, "Delivery-Mode Selection section not found"
        assert dispatch_pos != -1, "Dispatch Rules section not found"

        assert offer_pos < delivery_pos, (
            "Delivery-Mode Selection must appear after Offer Template (type selection)"
        )
        assert delivery_pos < dispatch_pos, (
            "Delivery-Mode Selection must appear before Dispatch Rules"
        )

    def test_dispatch_rules_reference_web_service_file(self) -> None:
        """Verify dispatch rules reference visualization-web-service.md for web service mode.

        Validates: Requirement 2.3
        """
        section = _get_section_content("Dispatch Rules")

        assert "visualization-web-service.md" in section, (
            "Dispatch Rules must reference 'visualization-web-service.md' for web service mode"
        )

        # Verify it's associated with web service delivery mode
        assert "Web service delivery mode" in section or "web service" in section.lower(), (
            "Dispatch Rules must associate visualization-web-service.md with web service mode"
        )

    def test_static_path_does_not_load_web_service_file(self) -> None:
        """Verify static delivery path does NOT load visualization-web-service.md.

        Validates: Requirement 2.4
        """
        section = _get_section_content("Dispatch Rules")

        # Find the static HTML delivery mode rule text
        # It should explicitly state NOT to load visualization-web-service.md
        static_rules = [
            line
            for line in section.splitlines()
            if "Static HTML delivery mode" in line or "static" in line.lower()
        ]

        static_text = "\n".join(static_rules)
        assert "Do NOT load" in static_text or "NOT load" in static_text, (
            "Static delivery path must explicitly state NOT to load "
            "visualization-web-service.md"
        )

    def test_delivery_mode_section_ends_with_stop_directive(self) -> None:
        """Verify delivery-mode section ends with a STOP directive.

        Validates: Requirement 2.7
        """
        section = _get_section_content("Delivery-Mode Selection")

        # The STOP directive should be at the end of the section
        # Look for the 🛑 STOP pattern
        assert "STOP" in section, (
            "Delivery-mode section must contain a STOP directive"
        )

        # Verify the STOP is near the end of the section (last non-empty lines)
        lines = [line for line in section.splitlines() if line.strip()]
        # Find the last line containing STOP
        stop_lines = [
            idx for idx, line in enumerate(lines) if "STOP" in line
        ]
        assert stop_lines, "No STOP directive found in delivery-mode section"

        last_stop_idx = stop_lines[-1]
        # STOP should be in the last few lines of the section
        assert last_stop_idx >= len(lines) - 3, (
            f"STOP directive should be near the end of the section. "
            f"Found at line {last_stop_idx + 1} of {len(lines)} non-empty lines."
        )


# ---------------------------------------------------------------------------
# Tracker Schema Tests
# ---------------------------------------------------------------------------


class TestTrackerSchema:
    """Unit tests for tracker schema version and delivery_mode field.

    Validates: Requirements 3.4, 3.1
    """

    def test_schema_version_is_1_1_0(self) -> None:
        """Verify the JSON schema example in visualization-protocol.md contains version 1.1.0.

        Validates: Requirement 3.4
        """
        content = _get_protocol_content()

        # The schema is in a JSON code block; look for the version field
        assert '"version": "1.1.0"' in content, (
            "Tracker schema version must be '1.1.0' in visualization-protocol.md"
        )

    def test_delivery_mode_field_documented(self) -> None:
        """Verify delivery_mode appears in the field documentation table.

        Validates: Requirement 3.1
        """
        content = _get_protocol_content()

        # The field documentation is a markdown table with | Field | Type | Description |
        # Find lines that are part of the table and contain delivery_mode
        table_lines = [
            line
            for line in content.splitlines()
            if line.strip().startswith("|") and "delivery_mode" in line
        ]

        assert len(table_lines) > 0, (
            "delivery_mode must be documented in the schema field table "
            "in visualization-protocol.md"
        )

        # Verify the table row contains type and description info
        table_row = table_lines[0]
        assert "string" in table_row.lower() or "null" in table_row.lower(), (
            f"delivery_mode table row must document its type. Got: {table_row}"
        )
