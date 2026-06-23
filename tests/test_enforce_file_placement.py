"""Example-based tests for root file placement enforcement (CHECK 4).

Verifies the hook prompt structure, steering file content, and placement
logic using deterministic example tests. Companion to the property-based
tests in test_enforce_file_placement_properties.py.

Requirements validated: 1.1–1.6, 2.1, 2.5–2.6, 3.1–3.9, 4.1–4.5, 5.1–5.6
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Repo root resolution
# ---------------------------------------------------------------------------

REPO_ROOT: Path = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Constants (mirrors design doc data model)
# ---------------------------------------------------------------------------

ROOT_WHITELIST_EXACT: set[str] = {
    ".gitignore",
    ".env",
    ".env.example",
    "README.md",
    "requirements.txt",
    "pom.xml",
    "Cargo.toml",
    "package.json",
}

ROOT_WHITELIST_PATTERNS: list[str] = [
    "*.csproj",  # Any .csproj file
]

BLOCKED_EXTENSIONS: set[str] = {".py", ".md", ".jsonl", ".csv", ".json"}


# ---------------------------------------------------------------------------
# Test helper functions
# ---------------------------------------------------------------------------


def is_root_path(path: str) -> bool:
    """True if path has no subdirectory (is just a filename).

    Args:
        path: File path to check.

    Returns:
        True if the path is a bare filename with no directory component.
    """
    return os.path.dirname(path) == "" or os.path.dirname(path) == "."


def is_whitelisted(filename: str) -> bool:
    """Check if filename is on the root whitelist (exact match or pattern).

    Args:
        filename: Bare filename to check (no directory).

    Returns:
        True if the file is permitted in the project root.
    """
    if filename in ROOT_WHITELIST_EXACT:
        return True
    for pattern in ROOT_WHITELIST_PATTERNS:
        # Pattern is "*.csproj" — check if filename ends with ".csproj"
        suffix = pattern.lstrip("*")
        if filename.endswith(suffix):
            return True
    return False


def has_blocked_extension(filename: str) -> bool:
    """Check if filename has a blocked extension.

    Args:
        filename: Bare filename to check.

    Returns:
        True if the file extension is in BLOCKED_EXTENSIONS.
    """
    _, ext = os.path.splitext(filename)
    return ext.lower() in BLOCKED_EXTENSIONS


def get_expected_routing(filename: str) -> str:
    """Return the expected corrective routing destination for a blocked file.

    Args:
        filename: Bare filename with a blocked extension.

    Returns:
        Target directory string (e.g., "scripts/", "docs/").
    """
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext == ".py":
        return "scripts/"
    elif ext == ".md":
        return "docs/"
    elif ext in (".jsonl", ".csv"):
        return "data/"
    elif ext == ".json":
        return "data/"
    return ""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def hook_prompt() -> str:
    """Load the write-policy-gate hook prompt text."""
    hook_path = REPO_ROOT / "senzing-bootcamp" / "hooks" / "write-policy-gate.kiro.hook"
    assert hook_path.exists(), f"Hook file not found: {hook_path}"
    with open(hook_path, encoding="utf-8") as f:
        data = json.load(f)
    return data["then"]["prompt"]


@pytest.fixture(scope="module")
def agent_instructions_content() -> str:
    """Load agent-instructions.md content."""
    path = REPO_ROOT / "senzing-bootcamp" / "steering" / "agent-instructions.md"
    assert path.exists(), f"Steering file not found: {path}"
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def file_placement_content() -> str:
    """Load file-placement.md content (root prohibitions + whitelist relocated here)."""
    path = REPO_ROOT / "senzing-bootcamp" / "steering" / "file-placement.md"
    assert path.exists(), f"Steering file not found: {path}"
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def project_structure_content() -> str:
    """Load project-structure.md content."""
    path = REPO_ROOT / "senzing-bootcamp" / "steering" / "project-structure.md"
    assert path.exists(), f"Steering file not found: {path}"
    return path.read_text(encoding="utf-8")


# ===========================================================================
# TestHelperFunctions — Validate test helper correctness
# ===========================================================================


class TestHelperFunctions:
    """Verify the test helper functions behave correctly."""

    def test_is_root_path_bare_filename(self):
        """Bare filename is a root path."""
        assert is_root_path("main.py") is True

    def test_is_root_path_with_subdirectory(self):
        """Path with subdirectory is not a root path."""
        assert is_root_path("src/main.py") is False

    def test_is_root_path_dot_prefix(self):
        """Path with ./ prefix is a root path."""
        assert is_root_path("./main.py") is True

    def test_is_root_path_nested(self):
        """Deeply nested path is not a root path."""
        assert is_root_path("src/transform/mapper.py") is False

    def test_is_whitelisted_exact_match(self):
        """Exact whitelist entries are recognized."""
        assert is_whitelisted(".gitignore") is True
        assert is_whitelisted("README.md") is True
        assert is_whitelisted("package.json") is True

    def test_is_whitelisted_pattern_match(self):
        """Pattern-matched .csproj files are recognized."""
        assert is_whitelisted("MyProject.csproj") is True
        assert is_whitelisted("senzing.csproj") is True

    def test_is_whitelisted_blocked_file(self):
        """Non-whitelisted files are rejected."""
        assert is_whitelisted("main.py") is False
        assert is_whitelisted("notes.md") is False
        assert is_whitelisted("data.jsonl") is False

    def test_has_blocked_extension_all_types(self):
        """All blocked extensions are detected."""
        assert has_blocked_extension("main.py") is True
        assert has_blocked_extension("notes.md") is True
        assert has_blocked_extension("data.jsonl") is True
        assert has_blocked_extension("records.csv") is True
        assert has_blocked_extension("config.json") is True

    def test_has_blocked_extension_allowed_types(self):
        """Non-blocked extensions pass through."""
        assert has_blocked_extension("Cargo.toml") is False
        assert has_blocked_extension(".gitignore") is False
        assert has_blocked_extension("app.rs") is False
        assert has_blocked_extension("index.html") is False

    def test_get_expected_routing_py(self):
        """Python files route to scripts/ by default."""
        assert get_expected_routing("main.py") == "scripts/"

    def test_get_expected_routing_md(self):
        """Markdown files route to docs/."""
        assert get_expected_routing("notes.md") == "docs/"

    def test_get_expected_routing_jsonl(self):
        """JSONL files route to data/."""
        assert get_expected_routing("records.jsonl") == "data/"

    def test_get_expected_routing_csv(self):
        """CSV files route to data/."""
        assert get_expected_routing("input.csv") == "data/"

    def test_get_expected_routing_json(self):
        """JSON files route to data/."""
        assert get_expected_routing("payload.json") == "data/"


# ===========================================================================
# TestBlockedExtensionsInRoot — Req 1.1, 1.2, 1.3, 1.4, 1.5
# ===========================================================================


class TestBlockedExtensionsInRoot:
    """Verify each blocked extension is rejected when placed in root."""

    def test_py_blocked_in_root(self, hook_prompt: str):
        """Hook blocks .py files in root (Req 1.1)."""
        assert ".py files:" in hook_prompt
        assert "ROOT PLACEMENT BLOCKED" in hook_prompt
        assert "Python source files cannot be placed in the project root" in hook_prompt

    def test_md_blocked_in_root(self, hook_prompt: str):
        """Hook blocks .md files (except README.md) in root (Req 1.2)."""
        assert ".md files:" in hook_prompt
        assert "Markdown files (other than README.md) cannot be placed" in hook_prompt

    def test_jsonl_blocked_in_root(self, hook_prompt: str):
        """Hook blocks .jsonl files in root (Req 1.3)."""
        assert ".jsonl files:" in hook_prompt
        assert "JSONL data files cannot be placed in the project root" in hook_prompt

    def test_csv_blocked_in_root(self, hook_prompt: str):
        """Hook blocks .csv files in root (Req 1.4)."""
        assert ".csv files:" in hook_prompt
        assert "CSV data files cannot be placed in the project root" in hook_prompt

    def test_json_blocked_in_root(self, hook_prompt: str):
        """Hook blocks non-whitelist .json files in root (Req 1.5)."""
        assert ".json files (not on whitelist):" in hook_prompt
        assert "Non-config JSON files cannot be placed in the project root" in hook_prompt

    def test_all_blocked_extensions_have_stop_directive(self, hook_prompt: str):
        """Each blocked extension section contains a STOP directive."""
        for ext in [".py", ".md", ".jsonl", ".csv", ".json"]:
            # Each extension section has "STOP. Do not proceed with the write."
            assert "STOP. Do not proceed with the write." in hook_prompt


# ===========================================================================
# TestWhitelistedFilesPermitted — Req 1.6, 3.1–3.9
# ===========================================================================


class TestWhitelistedFilesPermitted:
    """Verify each whitelisted file is permitted in the hook prompt."""

    @pytest.mark.parametrize("filename", sorted(ROOT_WHITELIST_EXACT))
    def test_whitelist_exact_entry_in_hook(self, hook_prompt: str, filename: str):
        """Each exact whitelist entry appears in the ROOT WHITELIST section."""
        assert filename in hook_prompt, (
            f"Whitelist entry '{filename}' not found in hook prompt"
        )

    def test_csproj_pattern_in_hook(self, hook_prompt: str):
        """The .csproj pattern is referenced in the hook prompt."""
        assert ".csproj" in hook_prompt

    def test_whitelist_section_exists(self, hook_prompt: str):
        """Hook prompt contains a ROOT WHITELIST section."""
        assert "ROOT WHITELIST" in hook_prompt

    def test_whitelist_permits_silently(self, hook_prompt: str):
        """Hook prompt instructs silent pass for whitelisted files."""
        # After the whitelist check, the hook says to proceed silently
        assert "matches any entry on the ROOT WHITELIST" in hook_prompt


# ===========================================================================
# TestCorrectiveRouting — Req 2.1, 2.5, 2.6
# ===========================================================================


class TestCorrectiveRouting:
    """Verify corrective routing destinations are present in hook prompt."""

    def test_py_routing_to_src_transform(self, hook_prompt: str):
        """Python files with transform logic route to src/transform/ (Req 2.1)."""
        assert "src/transform/" in hook_prompt

    def test_py_routing_to_src_load(self, hook_prompt: str):
        """Python files with load logic route to src/load/."""
        assert "src/load/" in hook_prompt

    def test_py_routing_to_src_query(self, hook_prompt: str):
        """Python files with query logic route to src/query/."""
        assert "src/query/" in hook_prompt

    def test_py_routing_to_scripts(self, hook_prompt: str):
        """Python files without specific signal route to scripts/."""
        assert "scripts/" in hook_prompt

    def test_md_routing_to_docs(self, hook_prompt: str):
        """Markdown files route to docs/ (Req 2.5)."""
        assert "docs/" in hook_prompt

    def test_jsonl_routing_to_data_subdirs(self, hook_prompt: str):
        """JSONL files route to data/ subdirectories (Req 2.6)."""
        assert "data/raw/" in hook_prompt
        assert "data/transformed/" in hook_prompt
        assert "data/samples/" in hook_prompt
        assert "data/temp/" in hook_prompt

    def test_csv_routing_to_data_subdirs(self, hook_prompt: str):
        """CSV files route to data/ subdirectories (Req 2.6)."""
        # CSV section references same data subdirectories
        prompt_csv_section = hook_prompt[hook_prompt.find(".csv files:"):]
        assert "data/raw/" in prompt_csv_section
        assert "data/transformed/" in prompt_csv_section

    def test_json_routing_to_data_or_config(self, hook_prompt: str):
        """JSON files route to data/ or config/ (Req 2.7)."""
        assert "config/" in hook_prompt

    def test_rewrite_path_instruction(self, hook_prompt: str):
        """Hook instructs agent to rewrite the path and retry."""
        assert "Rewrite the path and retry" in hook_prompt


# ===========================================================================
# TestCheck4PromptStructure — Req 1.1–1.6
# ===========================================================================


class TestCheck4PromptStructure:
    """Verify CHECK 4 text is present and properly structured in the hook."""

    def test_check4_header_present(self, hook_prompt: str):
        """CHECK 4 section header exists in hook prompt."""
        assert "CHECK 4: ROOT FILE PLACEMENT ENFORCEMENT" in hook_prompt

    def test_check4_q1_root_detection(self, hook_prompt: str):
        """CHECK 4 contains Q1 for root path detection."""
        assert "Q1:" in hook_prompt
        assert "project root" in hook_prompt

    def test_check4_q2_whitelist_check(self, hook_prompt: str):
        """CHECK 4 contains Q2 for whitelist verification."""
        # Find Q2 in the CHECK 4 section
        check4_start = hook_prompt.find("CHECK 4:")
        check4_section = hook_prompt[check4_start:]
        assert "Q2:" in check4_section
        assert "ROOT WHITELIST" in check4_section

    def test_check4_blocked_extensions_section(self, hook_prompt: str):
        """CHECK 4 contains BLOCKED EXTENSIONS AND CORRECTIVE ROUTING section."""
        assert "BLOCKED EXTENSIONS AND CORRECTIVE ROUTING" in hook_prompt

    def test_check4_silent_pass_for_non_root(self, hook_prompt: str):
        """CHECK 4 instructs silent pass for files not in root."""
        check4_start = hook_prompt.find("CHECK 4:")
        check4_section = hook_prompt[check4_start:]
        assert "This check does not apply" in check4_section

    def test_check4_silent_pass_for_unknown_extensions(self, hook_prompt: str):
        """CHECK 4 instructs silent pass for unknown extensions."""
        assert "Any other extension not listed above" in hook_prompt

    def test_fast_path_gate_includes_root_condition(self, hook_prompt: str):
        """FAST PATH GATE includes the root placement condition."""
        assert "The target path is NOT a blocked file type in the project root" in hook_prompt

    def test_four_checks_in_description(self):
        """Hook description mentions four policy checks."""
        hook_path = (
            REPO_ROOT / "senzing-bootcamp" / "hooks" / "write-policy-gate.kiro.hook"
        )
        with open(hook_path, encoding="utf-8") as f:
            data = json.load(f)
        assert "four policy checks" in data["description"]


# ===========================================================================
# TestSteeringFileProhibitions — Req 4.1–4.5, 5.1–5.6
# ===========================================================================


class TestSteeringFileProhibitions:
    """Verify steering files contain prohibition language."""

    # --- file-placement.md tests (Req 4.1–4.5; relocated from agent-instructions.md) ---

    def test_agent_instructions_blocks_py(self, file_placement_content: str):
        """Root prohibitions block .py files in root (Req 4.1)."""
        assert "`.py` files" in file_placement_content
        assert "src/" in file_placement_content or "scripts/" in file_placement_content

    def test_agent_instructions_blocks_md(self, file_placement_content: str):
        """Root prohibitions block .md files (except README.md) in root (Req 4.2)."""
        assert "`.md` files (except `README.md`)" in file_placement_content

    def test_agent_instructions_blocks_data_files(self, file_placement_content: str):
        """Root prohibitions block .jsonl and .csv files in root (Req 4.3)."""
        assert "`.jsonl` files" in file_placement_content
        assert "`.csv` files" in file_placement_content

    def test_agent_instructions_blocks_json(self, file_placement_content: str):
        """Root prohibitions block non-config .json files in root (Req 4.4)."""
        assert "`.json` files" in file_placement_content or \
               "Non-config `.json` files" in file_placement_content

    def test_agent_instructions_lists_whitelist(self, file_placement_content: str):
        """Root prohibitions list the root whitelist (Req 4.5)."""
        assert "`.gitignore`" in file_placement_content
        assert "`README.md`" in file_placement_content
        assert "`requirements.txt`" in file_placement_content
        assert "`package.json`" in file_placement_content
        assert "`Cargo.toml`" in file_placement_content
        assert "`pom.xml`" in file_placement_content
        assert "`*.csproj`" in file_placement_content

    def test_agent_instructions_has_root_prohibitions_section(
        self, file_placement_content: str
    ):
        """file-placement.md contains a Root Prohibitions section."""
        assert "## Root Prohibitions" in file_placement_content

    def test_agent_instructions_never_language(self, file_placement_content: str):
        """Root prohibitions use NEVER prohibition language."""
        assert "NEVER place these file types in the project root" in file_placement_content

    def test_agent_instructions_points_to_file_placement(
        self, agent_instructions_content: str
    ):
        """agent-instructions.md keeps a pointer to file-placement.md."""
        assert "file-placement.md" in agent_instructions_content

    # --- project-structure.md tests (Req 5.1–5.6) ---

    def test_project_structure_blocks_py(self, project_structure_content: str):
        """Project structure prohibits .py files in root (Req 5.1)."""
        assert "`.py`" in project_structure_content

    def test_project_structure_blocks_md(self, project_structure_content: str):
        """Project structure prohibits .md files (except README.md) in root (Req 5.2)."""
        assert "`.md`" in project_structure_content
        assert "README.md" in project_structure_content

    def test_project_structure_blocks_data_files(self, project_structure_content: str):
        """Project structure prohibits .jsonl and .csv files in root (Req 5.3)."""
        assert "`.jsonl`" in project_structure_content
        assert "`.csv`" in project_structure_content

    def test_project_structure_blocks_json(self, project_structure_content: str):
        """Project structure prohibits non-config .json files in root (Req 5.4)."""
        assert "`.json`" in project_structure_content

    def test_project_structure_lists_routing(self, project_structure_content: str):
        """Project structure lists corrective routing destinations (Req 5.5)."""
        assert "src/transform/" in project_structure_content
        assert "src/load/" in project_structure_content
        assert "src/query/" in project_structure_content
        assert "scripts/" in project_structure_content
        assert "docs/" in project_structure_content
        assert "data/" in project_structure_content

    def test_project_structure_lists_whitelist(self, project_structure_content: str):
        """Project structure lists the exhaustive root-permitted file list (Req 5.6)."""
        assert "`.gitignore`" in project_structure_content
        assert "`README.md`" in project_structure_content
        assert "`requirements.txt`" in project_structure_content
        assert "`package.json`" in project_structure_content
        assert "`Cargo.toml`" in project_structure_content
        assert "`pom.xml`" in project_structure_content
        assert "`*.csproj`" in project_structure_content

    def test_project_structure_has_enforcement_section(
        self, project_structure_content: str
    ):
        """Project structure contains Root File Placement Enforcement section."""
        assert "### Root File Placement Enforcement" in project_structure_content

    def test_project_structure_never_language(self, project_structure_content: str):
        """Project structure uses NEVER prohibition language."""
        assert "NEVER permitted in the project root" in project_structure_content

    def test_project_structure_mentions_hook_enforcement(
        self, project_structure_content: str
    ):
        """Project structure mentions write-policy-gate hook enforcement."""
        assert "write-policy-gate" in project_structure_content
        assert "enforces" in project_structure_content
