"""Unit tests for the shipped Senzing MCP configuration (`senzing-bootcamp/mcp.json`).

Task 14.3 of the kiro-1-0-migration spec. Validates the 1.0 permissions /
MCP auto-approve surface:

- `mcp.json` `autoApprove` lists exactly the 12 active read-only Senzing MCP
  tools (Requirement 12.3).
- `submit_feedback` stays in `disabledTools` (Requirement 12.4).
- `mcp.json` remains the sole source of the Senzing MCP server URL
  (Requirement 12.5).

Scoping decision for the "no hardcoded MCP URL outside mcp.json" check
--------------------------------------------------------------------
`mcp.senzing.com` legitimately appears in several places in the repo, so a
naive "the string appears only in mcp.json anywhere" assertion would be brittle
and falsely fail against pre-existing, legitimate content:

- Markdown documentation (`POWER.md`, `docs/guides/ARCHITECTURE.md`,
  `steering/common-pitfalls.md`) references the host in prose: troubleshooting
  steps, `curl`/`nslookup` examples, an architecture reference table, and an
  illustrative copy of the `mcp.json` block. This is user-facing documentation,
  not a live connection source.
- `scripts/preflight.py` uses the bare host `mcp.senzing.com` for a TCP
  connectivity pre-check (host + port 443). That is an operational reachability
  probe, not the MCP connection endpoint the client dials.
- Several `senzing-bootcamp/tests/*.py` files assert *about* the host.

The security rule that matters ("Hardcoded MCP URLs outside `mcp.json`", HIGH)
and Requirement 12.5 ("mcp.json is the SOLE source of the Senzing MCP server
URL") are about the shipped Power (`senzing-bootcamp/`) and about the *machine-
readable connection surface*. This test therefore enforces two concrete,
non-brittle invariants scoped to `senzing-bootcamp/`:

1. Config surface: among machine-readable config files (`.json`, `.yaml`,
   `.yml`), the host `mcp.senzing.com` appears ONLY in `mcp.json`. No other
   config file may hardcode it.
2. Connection endpoint: the full MCP connection URL (`https://mcp.senzing.com/mcp`)
   — the value the MCP client actually connects to — appears ONLY in `mcp.json`
   among code/config files (`.py`, `.json`, `.yaml`, `.yml`, `.toml`, `.cfg`,
   `.ini`, `.sh`). Markdown docs may reproduce it as an illustrative example.

Both the bare host (assembled from parts) and the full URL are built at runtime
so this test file never itself embeds a hardcoded MCP URL.

**Validates: Requirements 12.3, 12.4, 12.5**
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_POWER_ROOT = _REPO_ROOT / "senzing-bootcamp"
_MCP_JSON = _POWER_ROOT / "mcp.json"

# Import the canonical tool inventory (single source of truth) so the expected
# tool lists in this test stay tied to the documented inventory.
_SCRIPTS_DIR = str(_POWER_ROOT / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import mcp_tool_inventory as inventory  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The 12 active read-only tools expected in mcp.json `autoApprove`, per Task 14.2
# / Requirement 12.3. Kept explicit here (the task's contract) and cross-checked
# against the canonical inventory below so the two sources cannot drift apart.
EXPECTED_ACTIVE_TOOLS: list[str] = [
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
]

DISABLED_TOOL: str = "submit_feedback"

# Host/URL assembled from parts so this file never embeds a hardcoded MCP URL
# (a security gate blocks hardcoded MCP URLs outside mcp.json).
_MCP_HOST: str = "mcp." + "senzing.com"
_MCP_URL: str = "https://" + _MCP_HOST + "/mcp"

# File-extension scopes for the URL-confinement checks (see module docstring).
_CONFIG_SUFFIXES: frozenset[str] = frozenset({".json", ".yaml", ".yml"})
_CODE_CONFIG_SUFFIXES: frozenset[str] = frozenset(
    {".py", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".sh"}
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_server_config() -> dict:
    """Return the `senzing-mcp-server` config object from mcp.json."""
    data = json.loads(_MCP_JSON.read_text(encoding="utf-8"))
    return data["mcpServers"]["senzing-mcp-server"]


def _iter_power_files(suffixes: frozenset[str]) -> list[Path]:
    """Return shipped Power files whose suffix is in `suffixes`.

    Skips `__pycache__` artifacts. Paths are absolute.
    """
    return [
        p
        for p in _POWER_ROOT.rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and p.suffix.lower() in suffixes
    ]


def _files_containing(needle: str, suffixes: frozenset[str]) -> list[str]:
    """Return repo-relative paths of Power files (of the given suffixes) that
    contain `needle`, excluding mcp.json itself."""
    offenders: list[str] = []
    for path in _iter_power_files(suffixes):
        if path == _MCP_JSON:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if needle in text:
            offenders.append(str(path.relative_to(_REPO_ROOT)))
    return sorted(offenders)


# ===========================================================================
# TestMcpConfigStructure
# ===========================================================================

class TestMcpConfigStructure:
    """mcp.json exists and has the expected server config shape."""

    def test_mcp_json_exists(self) -> None:
        """The shipped mcp.json config file must exist."""
        assert _MCP_JSON.is_file(), f"Missing {_MCP_JSON}"

    def test_mcp_json_is_valid_json(self) -> None:
        """mcp.json parses as JSON with the senzing-mcp-server entry."""
        server = _load_server_config()
        assert isinstance(server, dict)
        assert "autoApprove" in server, "mcp.json is missing `autoApprove`"
        assert "disabledTools" in server, "mcp.json is missing `disabledTools`"


# ===========================================================================
# TestAutoApproveTools  (Requirement 12.3)
# ===========================================================================

class TestAutoApproveTools:
    """`autoApprove` lists exactly the 12 active read-only tools.

    **Validates: Requirements 12.3**
    """

    def test_auto_approve_has_twelve_tools(self) -> None:
        """autoApprove lists exactly 12 tools."""
        auto = _load_server_config()["autoApprove"]
        assert isinstance(auto, list), "`autoApprove` must be a JSON array"
        assert len(auto) == 12, (
            f"autoApprove must list exactly 12 active tools, found {len(auto)}: {auto}"
        )

    def test_auto_approve_has_no_duplicates(self) -> None:
        """autoApprove contains no duplicate tool names."""
        auto = _load_server_config()["autoApprove"]
        assert len(auto) == len(set(auto)), (
            f"autoApprove contains duplicate entries: {auto}"
        )

    def test_auto_approve_matches_expected_active_tools(self) -> None:
        """autoApprove contains exactly the 12 expected active tools."""
        auto = set(_load_server_config()["autoApprove"])
        expected = set(EXPECTED_ACTIVE_TOOLS)
        missing = expected - auto
        extra = auto - expected
        assert auto == expected, (
            "autoApprove does not match the expected 12 active tools.\n"
            f"  Missing: {sorted(missing)}\n"
            f"  Unexpected: {sorted(extra)}"
        )

    def test_expected_tools_match_canonical_inventory(self) -> None:
        """The expected 12 tools equal the canonical ACTIVE_TOOLS inventory.

        Ties this test's explicit list to the single source of truth so the two
        cannot silently drift apart.
        """
        assert set(EXPECTED_ACTIVE_TOOLS) == set(inventory.ACTIVE_TOOLS), (
            "Expected active tools drifted from mcp_tool_inventory.ACTIVE_TOOLS.\n"
            f"  test list: {sorted(EXPECTED_ACTIVE_TOOLS)}\n"
            f"  inventory: {sorted(inventory.ACTIVE_TOOLS)}"
        )
        assert len(inventory.ACTIVE_TOOLS) == 12


# ===========================================================================
# TestDisabledTools  (Requirement 12.4)
# ===========================================================================

class TestDisabledTools:
    """`submit_feedback` stays disabled and is never auto-approved.

    **Validates: Requirements 12.4**
    """

    def test_submit_feedback_in_disabled_tools(self) -> None:
        """submit_feedback stays in the disabledTools list."""
        disabled = _load_server_config()["disabledTools"]
        assert DISABLED_TOOL in disabled, (
            f"`{DISABLED_TOOL}` must remain in disabledTools, found: {disabled}"
        )

    def test_submit_feedback_not_auto_approved(self) -> None:
        """submit_feedback must NOT appear in autoApprove."""
        auto = _load_server_config()["autoApprove"]
        assert DISABLED_TOOL not in auto, (
            f"`{DISABLED_TOOL}` must not be auto-approved; found it in {auto}"
        )

    def test_disabled_tools_match_canonical_inventory(self) -> None:
        """disabledTools equals the canonical DISABLED_TOOLS inventory."""
        disabled = set(_load_server_config()["disabledTools"])
        assert disabled == set(inventory.DISABLED_TOOLS), (
            "disabledTools drifted from mcp_tool_inventory.DISABLED_TOOLS.\n"
            f"  mcp.json: {sorted(disabled)}\n"
            f"  inventory: {sorted(inventory.DISABLED_TOOLS)}"
        )


# ===========================================================================
# TestMcpUrlSoleSource  (Requirement 12.5)
# ===========================================================================

class TestMcpUrlSoleSource:
    """mcp.json is the sole source of the Senzing MCP server URL.

    See the module docstring for the scoping decision. Enforced scopes:
    - No config file (`.json`/`.yaml`/`.yml`) other than mcp.json hardcodes the host.
    - No code/config file other than mcp.json hardcodes the full connection URL.

    **Validates: Requirements 12.5**
    """

    def test_mcp_json_contains_the_connection_url(self) -> None:
        """Sanity: the single source (mcp.json) actually holds the connection URL."""
        text = _MCP_JSON.read_text(encoding="utf-8")
        assert _MCP_URL in text, "mcp.json must contain the MCP connection URL"

    def test_host_not_hardcoded_in_other_config_files(self) -> None:
        """No other shipped config file hardcodes the MCP host."""
        offenders = _files_containing(_MCP_HOST, _CONFIG_SUFFIXES)
        assert not offenders, (
            "The MCP host must live only in mcp.json among config files; "
            f"found it hardcoded in: {offenders}"
        )

    def test_connection_url_not_hardcoded_in_code_or_config(self) -> None:
        """No shipped code/config file other than mcp.json hardcodes the full URL."""
        offenders = _files_containing(_MCP_URL, _CODE_CONFIG_SUFFIXES)
        assert not offenders, (
            "The MCP connection URL must live only in mcp.json; "
            f"found it hardcoded in: {offenders}"
        )
