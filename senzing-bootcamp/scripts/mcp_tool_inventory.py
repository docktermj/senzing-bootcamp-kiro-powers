#!/usr/bin/env python3
"""Canonical Senzing MCP tool inventory — single source of truth.

This module is the authoritative, machine-readable record of the Senzing MCP
tool inventory used by the bootcamp power. Tests and validators import these
constants instead of hard-coding tool lists, so any drift in the documented
inventory (a real tool dropped, a phantom tool such as ``lint_record`` added,
or a stale 12/14-tool count reintroduced) fails CI against this single source.

The values below were confirmed against a live ``get_capabilities(version="current")``
call to the Senzing MCP server (``sz-mcp-coworker`` — first recorded against v1.24.0,
re-confirmed against v1.26.8 for the 1.0.0 release), which reported
``tool_count: 13`` with the 13 tool names listed in ``ALL_TOOLS`` and NO
``lint_record`` tool. ``analyze_record`` is the data-mapping validation tool.

These constants MUST be re-confirmed against a live ``get_capabilities(version="current")``
response before any change. If the MCP server is unreachable, BLOCK and surface the
MCP connection-troubleshooting steps in ``POWER.md`` — there is no offline fallback.

Usage:
    import mcp_tool_inventory as inventory

    assert inventory.TOTAL_COUNT == 13
    assert len(inventory.ALL_TOOLS) == 13
    assert inventory.VALIDATION_TOOL == "analyze_record"
"""

from __future__ import annotations

# The 12 routable (active) tools, in the order reported by the live server.
ACTIVE_TOOLS: tuple[str, ...] = (
    "get_capabilities",
    "mapping_workflow",
    "analyze_record",
    "download_resource",
    "explain_error_code",
    "search_docs",
    "find_examples",
    "generate_scaffold",
    "get_sample_data",
    "get_sdk_reference",
    "sdk_guide",
    "reporting_guide",
)

# Tools disabled by default via the ``disabledTools`` array in ``mcp.json``.
DISABLED_TOOLS: tuple[str, ...] = ("submit_feedback",)

# The full 13-tool live inventory, derived so it stays consistent with the parts.
ALL_TOOLS: tuple[str, ...] = ACTIVE_TOOLS + DISABLED_TOOLS

# Total number of tools exposed by the live server (``server_info.tool_count``).
TOTAL_COUNT: int = 13

# The tool that validates a mapped record against the Entity Specification.
VALIDATION_TOOL: str = "analyze_record"
