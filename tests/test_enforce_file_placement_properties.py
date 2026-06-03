"""Property-based tests for root file placement enforcement (CHECK 4).

Uses Hypothesis to verify universal properties of the hook prompt structure,
steering file content, and placement logic across generated inputs.

Requirements validated: 1.1–1.6, 2.1–2.7, 3.1–3.9, 4.5, 5.5, 5.6
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# sys.path manipulation to import from sibling test file
# ---------------------------------------------------------------------------

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from test_enforce_file_placement import (
    BLOCKED_EXTENSIONS,
    REPO_ROOT,
    ROOT_WHITELIST_EXACT,
    ROOT_WHITELIST_PATTERNS,
    has_blocked_extension,
    is_whitelisted,
)

# ---------------------------------------------------------------------------
# Load hook prompt and steering files once (module-level)
# ---------------------------------------------------------------------------

_HOOK_PATH = REPO_ROOT / "senzing-bootcamp" / "hooks" / "write-policy-gate.kiro.hook"
with open(_HOOK_PATH, encoding="utf-8") as _f:
    _HOOK_DATA = json.load(_f)
HOOK_PROMPT: str = _HOOK_DATA["then"]["prompt"]

_AGENT_INSTRUCTIONS_PATH = REPO_ROOT / "senzing-bootcamp" / "steering" / "agent-instructions.md"
AGENT_INSTRUCTIONS: str = _AGENT_INSTRUCTIONS_PATH.read_text(encoding="utf-8")

_PROJECT_STRUCTURE_PATH = REPO_ROOT / "senzing-bootcamp" / "steering" / "project-structure.md"
PROJECT_STRUCTURE: str = _PROJECT_STRUCTURE_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_filename_stem() -> st.SearchStrategy[str]:
    """Generate valid filename stems (alphanumeric + underscore, 1-20 chars)."""
    return st.from_regex(r"[a-z][a-z0-9_]{0,19}", fullmatch=True)


def st_blocked_filename() -> st.SearchStrategy[str]:
    """Generate filenames with blocked extensions that are NOT on the whitelist."""
    def make_blocked(stem: str, ext: str) -> str:
        return f"{stem}{ext}"

    return st.builds(
        make_blocked,
        stem=st_filename_stem(),
        ext=st.sampled_from(sorted(BLOCKED_EXTENSIONS)),
    ).filter(lambda f: not is_whitelisted(f))


def st_whitelisted_filename() -> st.SearchStrategy[str]:
    """Generate filenames from the whitelist (exact entries + random .csproj variants)."""
    exact = st.sampled_from(sorted(ROOT_WHITELIST_EXACT))
    csproj = st.builds(lambda stem: f"{stem}.csproj", stem=st_filename_stem())
    return st.one_of(exact, csproj)


# ---------------------------------------------------------------------------
# Routing destinations per extension (from design doc)
# ---------------------------------------------------------------------------

ROUTING_DESTINATIONS: dict[str, list[str]] = {
    ".py": ["src/transform/", "src/load/", "src/query/", "scripts/"],
    ".md": ["docs/"],
    ".jsonl": ["data/raw/", "data/transformed/", "data/samples/", "data/temp/"],
    ".csv": ["data/raw/", "data/transformed/", "data/samples/", "data/temp/"],
    ".json": ["data/raw/", "data/transformed/", "config/"],
}


# ===========================================================================
# Property 1: Blocked extensions are rejected in root
# Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5
# ===========================================================================


class TestPropertyBlockedExtensionsRejected:
    """Property 1: Blocked extensions are rejected in root.

    For any filename with a blocked extension that is not on the Root Whitelist,
    the hook prompt SHALL contain blocking logic with a STOP directive and
    corrective routing output for that extension.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
    """

    @given(filename=st_blocked_filename())
    @settings(max_examples=20)
    def test_blocked_file_has_stop_directive(self, filename: str) -> None:
        """Hook prompt contains STOP directive for each blocked extension."""
        assert has_blocked_extension(filename)
        assert not is_whitelisted(filename)
        # The hook prompt must contain a STOP directive
        assert "STOP. Do not proceed with the write." in HOOK_PROMPT

    @given(filename=st_blocked_filename())
    @settings(max_examples=20)
    def test_blocked_file_has_corrective_routing(self, filename: str) -> None:
        """Hook prompt contains corrective routing for the blocked extension."""
        ext = "." + filename.rsplit(".", 1)[1]
        # The hook prompt must reference the extension's section
        assert f"{ext} files" in HOOK_PROMPT or f"{ext} files:" in HOOK_PROMPT

    @given(filename=st_blocked_filename())
    @settings(max_examples=20)
    def test_blocked_file_has_root_placement_blocked(self, filename: str) -> None:
        """Hook prompt contains ROOT PLACEMENT BLOCKED message for blocked extensions."""
        assert "ROOT PLACEMENT BLOCKED" in HOOK_PROMPT

    @given(filename=st_blocked_filename())
    @settings(max_examples=20)
    def test_blocked_file_has_rewrite_instruction(self, filename: str) -> None:
        """Hook prompt instructs rewriting the path for blocked files."""
        assert "Rewrite the path and retry" in HOOK_PROMPT


# ===========================================================================
# Property 2: Whitelisted files are permitted
# Validates: Requirements 1.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9
# ===========================================================================


class TestPropertyWhitelistedFilesPermitted:
    """Property 2: Whitelisted files are permitted.

    For any filename on the Root Whitelist (including pattern-matched .csproj files),
    the hook prompt SHALL contain whitelist logic that permits the file silently.

    **Validates: Requirements 1.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9**
    """

    @given(filename=st_whitelisted_filename())
    @settings(max_examples=20)
    def test_whitelisted_file_is_recognized(self, filename: str) -> None:
        """Every generated whitelisted filename passes the is_whitelisted check."""
        assert is_whitelisted(filename)

    @given(filename=st_whitelisted_filename())
    @settings(max_examples=20)
    def test_hook_contains_whitelist_section(self, filename: str) -> None:
        """Hook prompt contains ROOT WHITELIST section for permitting files."""
        assert "ROOT WHITELIST" in HOOK_PROMPT

    @given(filename=st_whitelisted_filename())
    @settings(max_examples=20)
    def test_hook_permits_whitelisted_silently(self, filename: str) -> None:
        """Hook prompt instructs silent pass for whitelisted files."""
        assert "matches any entry on the ROOT WHITELIST" in HOOK_PROMPT

    @given(filename=st.sampled_from(sorted(ROOT_WHITELIST_EXACT)))
    @settings(max_examples=20)
    def test_exact_whitelist_entry_in_hook(self, filename: str) -> None:
        """Each exact whitelist entry appears in the hook prompt."""
        assert filename in HOOK_PROMPT

    @given(filename=st.builds(lambda s: f"{s}.csproj", s=st_filename_stem()))
    @settings(max_examples=20)
    def test_csproj_pattern_covered_in_hook(self, filename: str) -> None:
        """The .csproj pattern is covered in the hook prompt whitelist."""
        assert is_whitelisted(filename)
        assert ".csproj" in HOOK_PROMPT


# ===========================================================================
# Property 3: Corrective routing maps blocked extensions to valid destinations
# Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7
# ===========================================================================


class TestPropertyCorrectiveRouting:
    """Property 3: Corrective routing maps blocked extensions to valid destinations.

    For any blocked file extension, the hook prompt SHALL contain corrective routing
    that directs the agent to valid project subdirectories.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**
    """

    @given(filename=st_blocked_filename())
    @settings(max_examples=20)
    def test_routing_references_valid_destination(self, filename: str) -> None:
        """Hook prompt contains at least one valid routing destination for the extension."""
        ext = "." + filename.rsplit(".", 1)[1]
        destinations = ROUTING_DESTINATIONS[ext]
        found = any(dest in HOOK_PROMPT for dest in destinations)
        assert found, (
            f"No valid routing destination found in hook prompt for {ext}. "
            f"Expected one of: {destinations}"
        )

    @given(ext=st.sampled_from(sorted(BLOCKED_EXTENSIONS)))
    @settings(max_examples=20)
    def test_each_extension_has_all_destinations(self, ext: str) -> None:
        """Hook prompt contains all routing destinations for each blocked extension."""
        destinations = ROUTING_DESTINATIONS[ext]
        for dest in destinations:
            assert dest in HOOK_PROMPT, (
                f"Routing destination '{dest}' not found in hook prompt for {ext}"
            )

    @given(filename=st_blocked_filename())
    @settings(max_examples=20)
    def test_routing_output_has_corrective_prefix(self, filename: str) -> None:
        """Hook prompt corrective routing uses the ⚠️ prefix marker."""
        assert "⚠️" in HOOK_PROMPT


# ===========================================================================
# Property 4: Steering files enumerate all whitelist entries
# Validates: Requirements 4.5, 5.6
# ===========================================================================


class TestPropertySteeringWhitelistEntries:
    """Property 4: Steering files enumerate all whitelist entries.

    For each file on the Root Whitelist, both agent-instructions.md and
    project-structure.md SHALL contain that filename or pattern.

    **Validates: Requirements 4.5, 5.6**
    """

    @given(filename=st.sampled_from(sorted(ROOT_WHITELIST_EXACT)))
    @settings(max_examples=20)
    def test_agent_instructions_contains_whitelist_entry(self, filename: str) -> None:
        """agent-instructions.md contains each exact whitelist entry."""
        # Steering files use backtick-wrapped filenames
        assert filename in AGENT_INSTRUCTIONS or f"`{filename}`" in AGENT_INSTRUCTIONS

    @given(filename=st.sampled_from(sorted(ROOT_WHITELIST_EXACT)))
    @settings(max_examples=20)
    def test_project_structure_contains_whitelist_entry(self, filename: str) -> None:
        """project-structure.md contains each exact whitelist entry."""
        assert filename in PROJECT_STRUCTURE or f"`{filename}`" in PROJECT_STRUCTURE

    @given(pattern=st.sampled_from(ROOT_WHITELIST_PATTERNS))
    @settings(max_examples=20)
    def test_agent_instructions_contains_whitelist_pattern(self, pattern: str) -> None:
        """agent-instructions.md contains each whitelist pattern."""
        assert pattern in AGENT_INSTRUCTIONS or f"`{pattern}`" in AGENT_INSTRUCTIONS

    @given(pattern=st.sampled_from(ROOT_WHITELIST_PATTERNS))
    @settings(max_examples=20)
    def test_project_structure_contains_whitelist_pattern(self, pattern: str) -> None:
        """project-structure.md contains each whitelist pattern."""
        assert pattern in PROJECT_STRUCTURE or f"`{pattern}`" in PROJECT_STRUCTURE


# ===========================================================================
# Property 5: Steering files enumerate all routing destinations
# Validates: Requirements 5.5
# ===========================================================================


class TestPropertySteeringRoutingDestinations:
    """Property 5: Steering files enumerate all routing destinations.

    For each blocked extension, project-structure.md SHALL contain the
    corrective routing destination(s) for that extension.

    **Validates: Requirements 5.5**
    """

    @given(ext=st.sampled_from(sorted(BLOCKED_EXTENSIONS)))
    @settings(max_examples=20)
    def test_project_structure_contains_routing_for_extension(self, ext: str) -> None:
        """project-structure.md contains routing destinations for each blocked extension."""
        destinations = ROUTING_DESTINATIONS[ext]
        for dest in destinations:
            assert dest in PROJECT_STRUCTURE, (
                f"Routing destination '{dest}' for {ext} not found in project-structure.md"
            )

    @given(ext=st.sampled_from(sorted(BLOCKED_EXTENSIONS)))
    @settings(max_examples=20)
    def test_project_structure_mentions_blocked_extension(self, ext: str) -> None:
        """project-structure.md mentions each blocked extension."""
        assert f"`{ext}`" in PROJECT_STRUCTURE, (
            f"Blocked extension {ext} not mentioned in project-structure.md"
        )


# ===========================================================================
# Property 6: Existing hook checks are preserved
# Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
# ===========================================================================


# Reference strings that must be present in each CHECK section
CHECK_REFERENCE_STRINGS: dict[str, list[str]] = {
    "CHECK 1": [
        "CHECK 1: SENZING SQL BLOCKING",
        "SQL PATTERNS TO DETECT",
        "SENZING DATABASE INDICATORS",
    ],
    "CHECK 2": [
        "CHECK 2: SINGLE-QUESTION ENFORCEMENT",
        "EXACTLY ONE QUESTION",
        "COMPOUND QUESTION DETECTED",
    ],
    "CHECK 3": [
        "CHECK 3: FILE PATH POLICIES",
        "QUICK CHECK",
        "CONTENT CHECK",
    ],
}


class TestPropertyExistingChecksPreserved:
    """Property 6: Existing hook checks are preserved.

    The CHECK 1, CHECK 2, and CHECK 3 section headers and key content
    SHALL remain present and unmodified after CHECK 4 is added.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6**
    """

    @given(
        check_name=st.sampled_from(sorted(CHECK_REFERENCE_STRINGS.keys())),
    )
    @settings(max_examples=20)
    def test_check_header_present(self, check_name: str) -> None:
        """Each existing CHECK section header is present in the hook prompt."""
        header = CHECK_REFERENCE_STRINGS[check_name][0]
        assert header in HOOK_PROMPT, (
            f"CHECK header '{header}' not found in hook prompt"
        )

    @given(
        check_name=st.sampled_from(sorted(CHECK_REFERENCE_STRINGS.keys())),
    )
    @settings(max_examples=20)
    def test_check_key_content_present(self, check_name: str) -> None:
        """Each existing CHECK section contains its key reference strings."""
        for ref_string in CHECK_REFERENCE_STRINGS[check_name]:
            assert ref_string in HOOK_PROMPT, (
                f"Reference string '{ref_string}' for {check_name} "
                f"not found in hook prompt"
            )

    @given(
        ref_pair=st.sampled_from([
            (check, ref)
            for check, refs in CHECK_REFERENCE_STRINGS.items()
            for ref in refs
        ]),
    )
    @settings(max_examples=20)
    def test_individual_reference_string_present(
        self, ref_pair: tuple[str, str]
    ) -> None:
        """Each individual reference string is present in the hook prompt."""
        check_name, ref_string = ref_pair
        assert ref_string in HOOK_PROMPT, (
            f"Reference string '{ref_string}' for {check_name} "
            f"not found in hook prompt"
        )
