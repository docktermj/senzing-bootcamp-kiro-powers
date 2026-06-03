"""Property-based tests for visualization enhancements steering files.

Validates that both steering files (module-03-phase2-visualization.md and
visualization-guide.md) contain all required Critical Lessons constraints,
Entity Graph UX features, API endpoints, tabs, and modal fields as specified
in the visualization enhancements requirements.

Feature: visualization-enhancements
"""

from __future__ import annotations

from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths and file loading
# ---------------------------------------------------------------------------

MODULE03_PATH: Path = (
    Path(__file__).resolve().parent.parent
    / "steering"
    / "module-03-phase2-visualization.md"
)

VIZ_GUIDE_PATH: Path = (
    Path(__file__).resolve().parent.parent
    / "steering"
    / "visualization-guide.md"
)

MODULE03_CONTENT: str = MODULE03_PATH.read_text(encoding="utf-8")
VIZ_GUIDE_CONTENT: str = VIZ_GUIDE_PATH.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# Constants: Required constraints, features, endpoints, tabs, modal fields
# ---------------------------------------------------------------------------

# 7 mandatory constraint keywords/phrases for the Critical Lessons section
CRITICAL_LESSONS_CONSTRAINTS: list[str] = [
    "Python generator script",
    "fs_write",
    "node --check",
    "data-*",
    "Quote discipline",
    "function(){}",
    "width",
]

# 6 required Entity Graph UX features
REQUIRED_ENTITY_GRAPH_FEATURES: list[str] = [
    "Node labels",
    "Edge labels",
    "Click-to-detail modal",
    "Zoom/pan",
    "Color legend",
    "Responsive resize",
]

# 5 required click-to-detail modal fields
REQUIRED_MODAL_FIELDS: list[str] = [
    "entity ID",
    "primary name",
    "data sources",
    "record count",
    "constituent records",
]

# 4 required API endpoints
REQUIRED_API_ENDPOINTS: list[str] = [
    "/api/stats",
    "/api/graph",
    "/api/merges",
    "search",
]

# 4 required tabs
REQUIRED_TABS: list[str] = [
    "Entity_Graph",
    "Record_Merges_View",
    "Merge_Statistics",
    "Probe_Panel",
]


# ---------------------------------------------------------------------------
# Property 1: Critical Lessons section completeness across steering files
# ---------------------------------------------------------------------------


class TestCriticalLessonsCompleteness:
    """Feature: visualization-enhancements, Property 1: Critical Lessons section completeness"""

    @given(constraint=st.sampled_from(CRITICAL_LESSONS_CONSTRAINTS))
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_constraint_present_in_both_steering_files(
        self, constraint: str
    ) -> None:
        """Each mandatory constraint appears in both steering files' Critical Lessons sections.

        **Validates: Requirements 2.3, 2.4, 2.5, 2.6, 6.1, 6.2, 6.3**

        Args:
            constraint: A mandatory constraint keyword/phrase drawn from
                CRITICAL_LESSONS_CONSTRAINTS.
        """
        module03_lower = MODULE03_CONTENT.lower()
        viz_guide_lower = VIZ_GUIDE_CONTENT.lower()
        constraint_lower = constraint.lower()

        violations: list[str] = []

        if constraint_lower not in module03_lower:
            violations.append(
                f"Constraint '{constraint}' not found in "
                f"module-03-phase2-visualization.md"
            )

        if constraint_lower not in viz_guide_lower:
            violations.append(
                f"Constraint '{constraint}' not found in "
                f"visualization-guide.md"
            )

        assert violations == [], (
            f"Critical Lessons completeness violations: {violations}"
        )


# ---------------------------------------------------------------------------
# Property 2: Feature Guidance contains all required Entity Graph features
# ---------------------------------------------------------------------------


class TestFeatureGuidanceCompleteness:
    """Feature: visualization-enhancements, Property 2: Feature Guidance contains all required features"""

    @given(feature=st.sampled_from(REQUIRED_ENTITY_GRAPH_FEATURES))
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_feature_referenced_in_viz_guide(self, feature: str) -> None:
        """Each required Entity Graph feature appears in the Visualization Guide's Feature Guidance.

        **Validates: Requirements 3.4, 4.4**

        Args:
            feature: A required Entity Graph UX feature drawn from
                REQUIRED_ENTITY_GRAPH_FEATURES.
        """
        viz_guide_lower = VIZ_GUIDE_CONTENT.lower()
        feature_lower = feature.lower()

        assert feature_lower in viz_guide_lower, (
            f"Required Entity Graph feature '{feature}' not found in "
            f"visualization-guide.md Feature Guidance section. "
            f"All features in {REQUIRED_ENTITY_GRAPH_FEATURES} must be referenced."
        )


# ---------------------------------------------------------------------------
# Property 3: Click-to-detail modal specifies all required fields
# ---------------------------------------------------------------------------


class TestClickToDetailModalFields:
    """Feature: visualization-enhancements, Property 3: Click-to-detail modal fields"""

    @given(field=st.sampled_from(REQUIRED_MODAL_FIELDS))
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_modal_field_specified_in_module03(self, field: str) -> None:
        """Each required modal field is mentioned in Module 03 Phase 2 Entity Graph specification.

        **Validates: Requirements 3.3**

        Args:
            field: A required click-to-detail modal field drawn from
                REQUIRED_MODAL_FIELDS.
        """
        module03_lower = MODULE03_CONTENT.lower()
        field_lower = field.lower()

        assert field_lower in module03_lower, (
            f"Required click-to-detail modal field '{field}' not found in "
            f"module-03-phase2-visualization.md Entity Graph specification. "
            f"All fields in {REQUIRED_MODAL_FIELDS} must be specified."
        )


# ---------------------------------------------------------------------------
# Property 4: All required API endpoints are specified
# ---------------------------------------------------------------------------


class TestApiEndpointsSpecified:
    """Feature: visualization-enhancements, Property 4: All API endpoints specified"""

    @given(endpoint=st.sampled_from(REQUIRED_API_ENDPOINTS))
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_endpoint_specified_in_module03(self, endpoint: str) -> None:
        """Each required API endpoint is specified in Module 03 Phase 2 steering.

        **Validates: Requirements 5.2, 7.1**

        Args:
            endpoint: A required API endpoint drawn from
                REQUIRED_API_ENDPOINTS.
        """
        module03_lower = MODULE03_CONTENT.lower()
        endpoint_lower = endpoint.lower()

        assert endpoint_lower in module03_lower, (
            f"Required API endpoint '{endpoint}' not found in "
            f"module-03-phase2-visualization.md. "
            f"All endpoints in {REQUIRED_API_ENDPOINTS} must be specified."
        )


# ---------------------------------------------------------------------------
# Property 5: All required tabs are specified
# ---------------------------------------------------------------------------


class TestTabsSpecified:
    """Feature: visualization-enhancements, Property 5: All tabs specified"""

    @given(tab=st.sampled_from(REQUIRED_TABS))
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_tab_referenced_in_module03(self, tab: str) -> None:
        """Each required tab is referenced in Module 03 Phase 2 steering.

        **Validates: Requirements 7.2**

        Args:
            tab: A required tab name drawn from REQUIRED_TABS.
        """
        assert tab in MODULE03_CONTENT, (
            f"Required tab '{tab}' not found in "
            f"module-03-phase2-visualization.md. "
            f"All tabs in {REQUIRED_TABS} must be referenced "
            f"(case-sensitive match)."
        )


# ---------------------------------------------------------------------------
# Unit tests: Scaffold removal and Python generator presence
# ---------------------------------------------------------------------------


class TestScaffoldRemovalAndGenerator:
    """Unit tests for scaffold removal and Python generator presence"""

    def test_no_generate_scaffold_reference(self) -> None:
        """Verify generate_scaffold(workflow='web_service') is absent from Module 03.

        **Validates: Requirements 1.1, 1.2**
        """
        assert "generate_scaffold(workflow='web_service')" not in MODULE03_CONTENT, (
            "Module 03 Phase 2 steering still contains "
            "'generate_scaffold(workflow='web_service')' which should have been "
            "removed in favor of the Python generator approach."
        )

    def test_write_html_py_in_required_files(self) -> None:
        """Verify write_html.py is mentioned as a generator in Module 03.

        **Validates: Requirements 1.1, 1.2**
        """
        assert "write_html.py" in MODULE03_CONTENT, (
            "Module 03 Phase 2 steering does not mention 'write_html.py' as "
            "the Python generator script. It should be listed in the required "
            "files and referenced as the generation mechanism."
        )

    def test_critical_lessons_heading_in_module03(self) -> None:
        """Verify CRITICAL LESSONS FOR VISUALIZATION GENERATION heading exists in Module 03.

        **Validates: Requirements 2.1**
        """
        assert "CRITICAL LESSONS FOR VISUALIZATION GENERATION" in MODULE03_CONTENT, (
            "Module 03 Phase 2 steering is missing the section heading "
            "'CRITICAL LESSONS FOR VISUALIZATION GENERATION'."
        )

    def test_critical_lessons_heading_in_viz_guide(self) -> None:
        """Verify CRITICAL LESSONS FOR VISUALIZATION GENERATION heading exists in Visualization Guide.

        **Validates: Requirements 2.2**
        """
        assert "CRITICAL LESSONS FOR VISUALIZATION GENERATION" in VIZ_GUIDE_CONTENT, (
            "Visualization Guide is missing the section heading "
            "'CRITICAL LESSONS FOR VISUALIZATION GENERATION'."
        )


# ---------------------------------------------------------------------------
# Unit tests: Entity Graph UX features
# ---------------------------------------------------------------------------


class TestEntityGraphUXFeatures:
    """Unit tests for Entity Graph UX feature specifications"""

    def test_node_labels_specified(self) -> None:
        """Verify node labels with truncation are specified in Module 03.

        **Validates: Requirements 3.1**
        """
        module03_lower = MODULE03_CONTENT.lower()
        assert "node labels" in module03_lower, (
            "Module 03 Phase 2 steering does not specify 'node labels' for "
            "the Entity Graph. Node text labels must be specified."
        )
        assert "20 characters" in MODULE03_CONTENT, (
            "Module 03 Phase 2 steering does not specify '20 characters' "
            "truncation limit for node labels."
        )

    def test_edge_labels_specified(self) -> None:
        """Verify edge labels with match key are specified in Module 03.

        **Validates: Requirements 3.2**
        """
        module03_lower = MODULE03_CONTENT.lower()
        assert "edge labels" in module03_lower, (
            "Module 03 Phase 2 steering does not specify 'edge labels' for "
            "the Entity Graph. Edge text labels must be specified."
        )
        assert "match key" in module03_lower, (
            "Module 03 Phase 2 steering does not specify 'match key' for "
            "edge labels. Edge labels should show the match key string."
        )

    def test_zoom_pan_specified(self) -> None:
        """Verify D3.js zoom and pan behavior is specified in Module 03.

        **Validates: Requirements 4.1**
        """
        module03_lower = MODULE03_CONTENT.lower()
        assert "zoom" in module03_lower, (
            "Module 03 Phase 2 steering does not specify 'zoom' behavior "
            "for the Entity Graph."
        )
        assert "pan" in module03_lower, (
            "Module 03 Phase 2 steering does not specify 'pan' behavior "
            "for the Entity Graph."
        )

    def test_color_legend_specified(self) -> None:
        """Verify color legend is specified in Module 03.

        **Validates: Requirements 4.2**
        """
        module03_lower = MODULE03_CONTENT.lower()
        assert "color legend" in module03_lower, (
            "Module 03 Phase 2 steering does not specify a 'color legend' "
            "for the Entity Graph."
        )

    def test_responsive_resize_specified(self) -> None:
        """Verify responsive resize is specified in Module 03.

        **Validates: Requirements 4.3**
        """
        module03_lower = MODULE03_CONTENT.lower()
        assert "responsive resize" in module03_lower or "window resize" in module03_lower, (
            "Module 03 Phase 2 steering does not specify 'responsive resize' "
            "or 'window resize' for the Entity Graph."
        )


# ---------------------------------------------------------------------------
# Unit tests: Preservation of existing content and new architecture sections
# ---------------------------------------------------------------------------


class TestPreservationRequirements:
    """Unit tests for preservation of existing content and new architecture sections"""

    def test_python_generator_architecture_in_viz_guide(self) -> None:
        """Verify Python Generator Architecture section exists in Visualization Guide.

        **Validates: Requirements 5.3**
        """
        viz_guide_lower = VIZ_GUIDE_CONTENT.lower()
        assert (
            "python generator architecture" in viz_guide_lower
            or "mandated" in viz_guide_lower
        ), (
            "Visualization Guide does not contain 'Python Generator Architecture' "
            "section or 'mandated' keyword. The Python generator approach must be "
            "documented as the mandated method for all visualization generation."
        )

    def test_summary_banner_preserved(self) -> None:
        """Verify Summary_Banner with 5 stats is preserved in Module 03.

        **Validates: Requirements 7.3**
        """
        assert "Summary_Banner" in MODULE03_CONTENT or "Summary Banner" in MODULE03_CONTENT, (
            "Module 03 Phase 2 steering does not contain 'Summary_Banner' or "
            "'Summary Banner'. The Summary Banner specification must be preserved."
        )

        module03_lower = MODULE03_CONTENT.lower()
        stats_keywords = ["records", "entities", "multi-record", "cross-source", "relationships"]
        found = [kw for kw in stats_keywords if kw in module03_lower]

        assert len(found) >= 3, (
            f"Module 03 Phase 2 steering only references {len(found)} of 5 expected "
            f"Summary Banner statistics keywords ({stats_keywords}). "
            f"Found: {found}. At least 3 must be present."
        )

    def test_delivery_sequence_reference_preserved(self) -> None:
        """Verify Web Service Delivery Sequence reference is preserved in Module 03.

        **Validates: Requirements 7.4**
        """
        module03_lower = MODULE03_CONTENT.lower()
        assert "delivery sequence" in module03_lower, (
            "Module 03 Phase 2 steering does not contain 'Delivery Sequence' "
            "(case-insensitive). The Web Service Delivery Sequence reference "
            "must be preserved for server lifecycle management."
        )
