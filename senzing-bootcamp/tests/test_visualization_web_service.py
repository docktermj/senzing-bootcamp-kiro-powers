"""Structural validation tests for the visualization-web-service feature.

These tests verify that the steering file updates for the Visualization Prompt,
expanded Web Server Guidance, framework selection, lifecycle management, and
feature parity contain the expected content.

Feature: visualization-web-service
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_POWER_ROOT = Path(__file__).resolve().parent.parent  # senzing-bootcamp/

_VIZ_GUIDE = _POWER_ROOT / "steering" / "visualization-guide.md"
_VIZ_WEB_SERVICE = _POWER_ROOT / "steering" / "visualization-web-service.md"
_MODULE_03 = _POWER_ROOT / "steering" / "module-03-quick-demo.md"
_MODULE_07 = _POWER_ROOT / "steering" / "module-07-query-validation.md"


def _read(path: Path) -> str:
    """Read a file and return its content as a string."""
    return path.read_text(encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════════
# 4.1 — visualization-guide.md Visualization Prompt and branching
# Validates: Requirements 1.1, 1.2, 1.3, 1.4, 5.1, 5.4
# ═══════════════════════════════════════════════════════════════════════════


class TestVizGuidePromptAndBranching:
    """Verify visualization-guide.md contains the Visualization Prompt as step 1."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = _read(_VIZ_GUIDE)

    def test_prompt_is_first_workflow_step(self):
        """Visualization Prompt appears as the first step in Agent Workflow."""
        # The prompt step should come before any other numbered step
        workflow_start = self.content.index("## Agent Workflow")
        prompt_pos = self.content.index("Visualization Prompt", workflow_start)
        # Step 2 (Gather requirements) should come after the prompt
        step2_pos = self.content.index("Gather requirements", workflow_start)
        assert prompt_pos < step2_pos

    def test_prompt_offers_static_html(self):
        """Prompt offers Static HTML file option."""
        assert "Static HTML file" in self.content

    def test_prompt_offers_web_service(self):
        """Prompt offers Web service option."""
        assert "Web service" in self.content

    def test_wait_instruction_after_prompt(self):
        """WAIT instruction follows the Visualization Prompt."""
        prompt_pos = self.content.index("Visualization Prompt")
        # Find the next WAIT after the prompt
        wait_pos = self.content.index("WAIT", prompt_pos)
        # The WAIT should be reasonably close to the prompt (within the same step)
        assert wait_pos - prompt_pos < 800

    def test_branching_static_html_path(self):
        """Branching logic exists for Static HTML path."""
        lower = self.content.lower()
        assert "static html" in lower
        # Should mention continuing with existing workflow
        assert "static html file" in lower

    def test_branching_web_service_path(self):
        """Branching logic directs to Web Server Guidance for web service."""
        assert "Web Server Guidance" in self.content
        # Should mention following the web server guidance section
        lower = self.content.lower()
        assert "web server guidance" in lower


# ═══════════════════════════════════════════════════════════════════════════
# 4.2 — visualization-guide.md Web Server Guidance endpoints
# Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.3, 3.4
# ═══════════════════════════════════════════════════════════════════════════


class TestVizGuideEndpoints:
    """Verify Web Server Guidance documents all endpoints and schemas."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = _read(_VIZ_WEB_SERVICE)

    def test_get_root_endpoint(self):
        """GET / endpoint is documented."""
        assert "GET" in self.content
        assert "`/`" in self.content

    def test_get_health_endpoint(self):
        """GET /health endpoint is documented."""
        assert "/health" in self.content

    def test_post_refresh_endpoint(self):
        """POST /refresh endpoint is documented."""
        assert "POST" in self.content
        assert "/refresh" in self.content

    def test_get_entity_endpoint(self):
        """GET /entity/{entityId} endpoint is documented."""
        assert "/entity/{entityId}" in self.content

    def test_get_search_endpoint(self):
        """GET /search endpoint is documented."""
        assert "/search" in self.content

    def test_health_response_status_field(self):
        """Health check response schema includes 'status' field."""
        assert '"status"' in self.content
        assert '"ok"' in self.content

    def test_health_response_last_refresh_field(self):
        """Health check response schema includes 'lastRefresh' field."""
        assert '"lastRefresh"' in self.content

    def test_error_response_error_field(self):
        """Error response schema includes 'error' field."""
        assert '"error"' in self.content

    def test_error_response_code_field(self):
        """Error response schema includes 'code' field."""
        assert '"code"' in self.content

    def test_error_response_detail_field(self):
        """Error response schema includes 'detail' field."""
        assert '"detail"' in self.content

    def test_localhost_binding_with_port_8080(self):
        """Localhost binding with configurable port and 8080 default."""
        assert "localhost" in self.content.lower()
        assert "8080" in self.content

    def test_port_conflict_handling(self):
        """Port conflict error handling is documented."""
        lower = self.content.lower()
        assert "port" in lower
        assert "conflict" in lower or "already in use" in lower

    def test_search_query_parameters(self):
        """Search endpoint documents query parameters."""
        lower = self.content.lower()
        assert "name" in lower
        assert "address" in lower
        assert "phone" in lower
        assert "email" in lower


# ═══════════════════════════════════════════════════════════════════════════
# 4.3 — visualization-guide.md code generation and lifecycle
# Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 6.1, 6.2, 6.3, 6.4, 6.5
# ═══════════════════════════════════════════════════════════════════════════


class TestVizGuideCodeGenAndLifecycle:
    """Verify framework selection, code gen instructions, and lifecycle management."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = _read(_VIZ_WEB_SERVICE)

    def test_framework_python_flask(self):
        """Framework table maps Python to Flask."""
        assert "Python" in self.content
        assert "Flask" in self.content

    def test_framework_typescript_express(self):
        """Framework table maps TypeScript to Express."""
        assert "TypeScript" in self.content
        assert "Express" in self.content

    def test_framework_java_javalin(self):
        """Framework table maps Java to Javalin."""
        assert "Java" in self.content
        assert "Javalin" in self.content

    def test_framework_rust_actix(self):
        """Framework table maps Rust to Actix-web."""
        assert "Rust" in self.content
        assert "Actix-web" in self.content

    def test_framework_csharp_aspnet(self):
        """Framework table maps C# to ASP.NET Minimal APIs."""
        assert "C#" in self.content
        assert "ASP.NET" in self.content

    def test_output_directory_src_server(self):
        """src/server/ is specified as the output directory."""
        assert "src/server/" in self.content

    def test_dependency_file_generation(self):
        """Dependency file generation is documented with per-language examples."""
        assert "requirements.txt" in self.content
        assert "package.json" in self.content
        assert "pom.xml" in self.content
        assert "Cargo.toml" in self.content
        assert ".csproj" in self.content

    def test_inline_code_comments_requirement(self):
        """Inline code comments requirement is documented."""
        lower = self.content.lower()
        assert "inline code comments" in lower

    def test_start_command_instructions(self):
        """Start command instructions are provided."""
        lower = self.content.lower()
        assert "start command" in lower or "starting the server" in lower
        # Should have actual commands
        assert "python src/server/server.py" in self.content

    def test_browser_url_instruction(self):
        """Browser URL instruction is included."""
        assert "http://localhost:8080" in self.content

    def test_stop_instructions_ctrl_c(self):
        """Stop instructions (Ctrl+C) are included."""
        assert "Ctrl+C" in self.content

    def test_troubleshooting_guidance(self):
        """Troubleshooting guidance for startup failures exists."""
        lower = self.content.lower()
        assert "troubleshooting" in lower or "problem" in lower

    def test_no_background_process_prohibition(self):
        """Explicit prohibition against starting server as background process."""
        lower = self.content.lower()
        assert "shall not start the server as a background process" in lower


# ═══════════════════════════════════════════════════════════════════════════
# 4.4 — visualization-guide.md feature parity
# Validates: Requirements 7.1, 7.2, 7.3
# ═══════════════════════════════════════════════════════════════════════════


class TestVizGuideFeatureParity:
    """Verify feature parity section lists all required features."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = _read(_VIZ_WEB_SERVICE)

    def test_feature_parity_force_layout(self):
        """Feature parity lists force layout."""
        # Find the feature parity section
        lower = self.content.lower()
        assert "feature parity" in lower
        assert "force layout" in lower

    def test_feature_parity_detail_panel(self):
        """Feature parity lists detail panel."""
        lower = self.content.lower()
        assert "detail panel" in lower

    def test_feature_parity_cluster_highlighting(self):
        """Feature parity lists cluster highlighting."""
        lower = self.content.lower()
        assert "cluster highlighting" in lower

    def test_feature_parity_search_filter(self):
        """Feature parity lists search & filter."""
        lower = self.content.lower()
        assert "search" in lower and "filter" in lower

    def test_feature_parity_statistics(self):
        """Feature parity lists statistics."""
        lower = self.content.lower()
        assert "statistics" in lower

    def test_live_entity_detail_fetching(self):
        """Live entity detail fetching via /entity/{entityId} is documented."""
        assert "/entity/{entityId}" in self.content
        lower = self.content.lower()
        assert "live entity detail" in lower or "fetch('/entity/{entityid}')" in lower.replace(
            "{entityid}", "{entityId}"
        )

    def test_refresh_button_without_page_reload(self):
        """Refresh button calling /refresh without full page reload is documented."""
        lower = self.content.lower()
        assert "refresh button" in lower
        assert "/refresh" in self.content
        assert "without" in lower and "page reload" in lower


# ═══════════════════════════════════════════════════════════════════════════
# 4.5 — module-03-quick-demo.md Visualization Prompt
# Validates: Requirements 5.2
# ═══════════════════════════════════════════════════════════════════════════


class TestModule03VisualizationPrompt:
    """Verify module-03-quick-demo.md contains the Visualization Prompt in Phase 2 Step 5."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = _read(_MODULE_03)

    def test_prompt_in_phase2_step5(self):
        """Visualization Prompt appears in Phase 2 Step 5."""
        # Step 5 is the "Offer visualization" step
        step5_pos = self.content.index("Offer visualization")
        # The prompt should be within step 5 content
        static_pos = self.content.index("Static HTML file", step5_pos)
        assert static_pos > step5_pos

    def test_prompt_offers_static_html(self):
        """Prompt offers Static HTML file option."""
        assert "Static HTML file" in self.content

    def test_prompt_offers_web_service(self):
        """Prompt offers Web service option."""
        assert "Web service" in self.content

    def test_wait_instruction_after_prompt(self):
        """WAIT instruction follows the prompt."""
        prompt_pos = self.content.index("Static HTML file")
        wait_pos = self.content.index("WAIT", prompt_pos)
        assert wait_pos > prompt_pos


# ═══════════════════════════════════════════════════════════════════════════
# 4.6 — module-07-query-validation.md Visualization Prompt
# Validates: Requirements 5.3
# ═══════════════════════════════════════════════════════════════════════════


class TestModule07VisualizationPrompt:
    """Verify module-07-query-validation.md contains the Visualization Prompt."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = _read(_MODULE_07)

    def test_prompt_in_entity_graph_section(self):
        """Visualization Prompt appears in the entity graph offer section."""
        graph_pos = self.content.index("MANDATORY VISUALIZATION OFFER — ENTITY GRAPH")
        static_pos = self.content.index("Static HTML file", graph_pos)
        assert static_pos > graph_pos

    def test_prompt_in_results_dashboard_section(self):
        """Visualization Prompt appears in the results dashboard offer section."""
        dashboard_pos = self.content.index("MANDATORY VISUALIZATION OFFER — RESULTS DASHBOARD")
        static_pos = self.content.index("Static HTML file", dashboard_pos)
        assert static_pos > dashboard_pos

    def test_entity_graph_offers_both_options(self):
        """Entity graph prompt offers both static HTML and web service."""
        graph_pos = self.content.index("MANDATORY VISUALIZATION OFFER — ENTITY GRAPH")
        dashboard_pos = self.content.index("MANDATORY VISUALIZATION OFFER — RESULTS DASHBOARD")
        graph_section = self.content[graph_pos:dashboard_pos]
        assert "Static HTML file" in graph_section
        assert "Web service" in graph_section

    def test_results_dashboard_offers_both_options(self):
        """Results dashboard prompt offers both static HTML and web service."""
        dashboard_pos = self.content.index("MANDATORY VISUALIZATION OFFER — RESULTS DASHBOARD")
        dashboard_section = self.content[dashboard_pos:]
        assert "Static HTML file" in dashboard_section
        assert "Web service" in dashboard_section

    def test_entity_graph_wait_instruction(self):
        """WAIT instruction follows the entity graph prompt."""
        graph_pos = self.content.index("MANDATORY VISUALIZATION OFFER — ENTITY GRAPH")
        dashboard_pos = self.content.index("MANDATORY VISUALIZATION OFFER — RESULTS DASHBOARD")
        graph_section = self.content[graph_pos:dashboard_pos]
        assert "WAIT" in graph_section

    def test_results_dashboard_wait_instruction(self):
        """WAIT instruction follows the results dashboard prompt."""
        dashboard_pos = self.content.index("MANDATORY VISUALIZATION OFFER — RESULTS DASHBOARD")
        dashboard_section = self.content[dashboard_pos:]
        assert "WAIT" in dashboard_section


# ═══════════════════════════════════════════════════════════════════════════
# 4.7 — Preservation tests
# Validates: All (regression prevention)
# ═══════════════════════════════════════════════════════════════════════════


class TestPreservation:
    """Verify existing content is preserved across all modified files."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.viz_guide = _read(_VIZ_GUIDE)
        self.module_03 = _read(_MODULE_03)
        self.module_07 = _read(_MODULE_07)

    # --- visualization-guide.md preservation ---

    def test_graph_data_model_schema_preserved(self):
        """Existing Graph Data Model Schema is preserved."""
        assert "Graph Data Model Schema" in self.viz_guide
        assert "EntityNode" in self.viz_guide
        assert "RelationshipEdge" in self.viz_guide
        assert "entityId" in self.viz_guide
        assert "primaryName" in self.viz_guide

    def test_visualization_feature_guidance_preserved(self):
        """Existing Visualization Feature Guidance is preserved."""
        assert "Visualization Feature Guidance" in self.viz_guide
        assert "D3.js Force Layout" in self.viz_guide
        assert "Detail Panel" in self.viz_guide
        assert "Cluster Highlighting" in self.viz_guide
        assert "Search & Filter" in self.viz_guide
        assert "Statistics" in self.viz_guide

    def test_error_handling_guidance_preserved(self):
        """Existing Error Handling Guidance table is preserved."""
        assert "Error Handling Guidance" in self.viz_guide
        assert "SDK not initialized" in self.viz_guide
        assert "Empty database" in self.viz_guide
        assert "Entity count > 500" in self.viz_guide

    # --- module-03-quick-demo.md preservation ---

    def test_module03_phase1_preserved(self):
        """Module 3 Phase 1 content is unchanged."""
        assert "Phase 1: Setup" in self.module_03
        assert "Create project structure" in self.module_03
        assert "Verify SDK" in self.module_03
        assert "Choose sample dataset" in self.module_03
        assert "Generate demo script" in self.module_03

    def test_module03_phase2_other_steps_preserved(self):
        """Module 3 Phase 2 content (other than Step 5) is unchanged."""
        assert "Phase 2: Demo" in self.module_03
        assert "Show records BEFORE resolution" in self.module_03
        assert "Run the demo" in self.module_03
        assert "Display results" in self.module_03
        assert "Explain results" in self.module_03
        assert "Close Module 3 explicitly" in self.module_03
        assert "Transition to Module 1" in self.module_03

    # --- module-07-query-validation.md preservation ---

    def test_module07_query_requirements_preserved(self):
        """Module 7 query requirements content is preserved."""
        assert "Define query requirements" in self.module_07
        assert "Create query programs" in self.module_07
        assert "Run exploratory queries" in self.module_07

    def test_module07_integration_patterns_preserved(self):
        """Module 7 integration patterns are preserved."""
        assert "Integration Patterns" in self.module_07
        assert "Batch Report" in self.module_07
        assert "REST API" in self.module_07

    def test_module07_success_criteria_preserved(self):
        """Module 7 success criteria are preserved."""
        assert "Success Criteria" in self.module_07
        assert "Query programs created and tested" in self.module_07

    def test_module07_completeness_gate_preserved(self):
        """Module 7 Query Completeness Gate is preserved."""
        assert "Query Completeness Gate" in self.module_07
