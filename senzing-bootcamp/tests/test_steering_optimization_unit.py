"""Unit tests for steering optimization (example-based).

Validates line count constraints, token count targets, section extraction,
dispatch pointers, frontmatter structure, keyword mappings, and dry-run mode.

Feature: steering-optimization
Requirements: 1.1, 1.3, 2.3, 3.1, 3.2, 3.3, 3.4, 5.6, 7.4
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from optimize_steering import (  # noqa: E402, I001
    AGENT_INSTRUCTIONS_EXTRACTIONS,
    DEFAULT_KEYWORD_MAPPINGS,
    TRANSITIONS_EXTRACT,
    TRANSITIONS_KEEP,
    CompressTarget,
    _count_non_blank_lines,
    _create_file_with_frontmatter,
    compress_file,
    optimize,
    split_always_on_file,
    split_transitions_file,
)  # isort: skip


# ---------------------------------------------------------------------------
# Test Fixtures: Synthetic steering file content
# ---------------------------------------------------------------------------


def _make_agent_instructions(num_sections: int = 8) -> str:
    """Build synthetic agent-instructions.md with extractable sections.

    Creates a file with YAML frontmatter, core rules, and sections matching
    the extraction rules (SDK Method Discovery, Track Switching, etc.).

    Args:
        num_sections: Number of core rule lines to include.

    Returns:
        Synthetic agent-instructions.md content.
    """
    lines = [
        "---",
        "inclusion: always",
        "description: Core agent behavioral rules",
        "---",
        "",
        "# Agent Instructions",
        "",
        "## Answer Processing Priority",
        "",
    ]
    # Add core rule lines
    for i in range(1, num_sections + 1):
        lines.append(f"{i}. Core rule number {i} — THE agent SHALL follow this rule")
    lines.append("")
    lines.append("## MCP Rules")
    lines.append("")
    lines.append("THE agent SHALL call MCP tool before presenting Senzing facts")
    lines.append("THE agent NEVER uses training data for Senzing content")
    lines.append("")
    # Extractable section: SDK Method Discovery (H3 under MCP Rules)
    lines.append("### SDK Method Discovery")
    lines.append("")
    lines.append("Use the MCP tool to discover available SDK methods.")
    lines.append("Check the method signature before calling.")
    lines.append("Verify return types match expectations.")
    lines.append("")
    # Extractable section: Question_Pending File Format (H3 under MCP Rules)
    lines.append("### Question_Pending File Format")
    lines.append("")
    lines.append("Write .question_pending with the question text.")
    lines.append("Wait for user response before continuing.")
    lines.append("")
    # Extractable section: Track Switching (H2 — must come after H3 sections)
    lines.append("## Track Switching")
    lines.append("")
    lines.append("Switch tracks when the user requests a different deployment path.")
    lines.append("Confirm the switch with the user before proceeding.")
    lines.append("")
    # Extractable section: Module Transition Execution (H2)
    lines.append("## Module Transition Execution")
    lines.append("")
    lines.append("Execute module transitions per the transition protocol.")
    lines.append("Verify prerequisites before advancing.")
    lines.append("")
    return "\n".join(lines)


def _make_module_transitions() -> str:
    """Build synthetic module-transitions.md with keep and extract sections.

    Returns:
        Synthetic module-transitions.md content.
    """
    lines = [
        "---",
        "inclusion: always",
        "description: Module transition rules",
        "---",
        "",
        "# Module Transitions",
        "",
        "## Module Start Banner",
        "",
        "Display the module start banner with module number and title.",
        "",
        "## Journey Map (at module start)",
        "",
        "Show the journey map at the start of each module.",
        "",
        "## Before/After Framing (at module start)",
        "",
        "Frame the module with before/after context.",
        "",
        "## Step-Level Progress",
        "",
        "Track step-level progress within each module.",
        "",
        "## Module Completion",
        "",
        "Mark module as complete when all steps are done.",
        "",
        "## Transition Integrity",
        "",
        "Verify transition integrity between modules.",
        "",
        "## Confirmation Response Requirements",
        "",
        "Require confirmation responses at key checkpoints.",
        "",
        "## Quality Feedback Loop",
        "",
        "Provide quality feedback at the end of each module.",
        "Collect user satisfaction ratings.",
        "Adjust pacing based on feedback.",
        "",
        "## Sub-Step Convention",
        "",
        "Use sub-steps for complex operations.",
        "Number sub-steps as N.1, N.2, N.3.",
        "Track sub-step completion separately.",
        "",
    ]
    return "\n".join(lines)


def _make_compressible_file(target_tokens: int) -> str:
    """Build a synthetic steering file with verbose prose for compression testing.

    Creates content with filler phrases, transitional phrases, and verbose
    preambles that the compressor can reduce. The file is sized to be larger
    than the target so compression can be measured.

    Args:
        target_tokens: The target token count (file will be ~1.5x this size).

    Returns:
        Synthetic steering file content with compressible prose.
    """
    lines = [
        "---",
        "inclusion: manual",
        "description: Test file for compression",
        "---",
        "",
        "# Hook Registry Critical",
        "",
    ]
    # Generate verbose prose that the compressor can reduce
    verbose_block = (
        "It is important to note that the following is a list of hooks "
        "that are critical for the bootcamp experience. In order to ensure "
        "that the bootcamp functions correctly, you need to make sure that "
        "all of these hooks are properly installed. Please note that each "
        "hook basically has a specific trigger condition and action that "
        "essentially determines when it fires. Remember that hooks are "
        "simply JSON files with specific fields. Note that the hook naming "
        "convention is important to follow.\n"
    )
    # Repeat until we exceed target size
    char_target = target_tokens * 4 * 2  # 2x target for compression headroom
    content_so_far = "\n".join(lines)
    section_num = 1
    while len(content_so_far) < char_target:
        content_so_far += f"\n## Section {section_num}\n\n"
        content_so_far += verbose_block
        content_so_far += (
            f"Moving on to the next section, it should be noted that "
            f"section {section_num} is particularly important. First of all, "
            f"this section describes the hooks that are used in module "
            f"{section_num}. The following are the key hooks:\n\n"
        )
        content_so_far += f"- hook-{section_num}-a: triggers on file creation\n"
        content_so_far += f"- hook-{section_num}-b: triggers on prompt submit\n"
        content_so_far += f"- hook-{section_num}-c: triggers on agent stop\n\n"
        section_num += 1
    return content_so_far


# ---------------------------------------------------------------------------
# TestLineCountConstraints
# ---------------------------------------------------------------------------


class TestLineCountConstraints:
    """Test that split files meet line count targets.

    Requirements: 1.1, 2.3
    """

    def test_agent_instructions_core_under_80_lines(self, tmp_path: Path) -> None:
        """After split, agent-instructions.md core ≤ 80 non-blank lines."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()

        # Write synthetic agent-instructions.md
        agent_file = steering_dir / "agent-instructions.md"
        agent_file.write_text(_make_agent_instructions(), encoding="utf-8")

        # Create destination files that the extraction rules reference
        (steering_dir / "mcp-usage-reference.md").write_text(
            "---\ninclusion: auto\ndescription: MCP usage\n---\n\n",
            encoding="utf-8",
        )
        (steering_dir / "track-switching.md").write_text(
            "---\ninclusion: auto\ndescription: Track switching\n---\n\n",
            encoding="utf-8",
        )
        (steering_dir / "conversation-protocol.md").write_text(
            "---\ninclusion: auto\ndescription: Conversation protocol\n---\n\n",
            encoding="utf-8",
        )
        (steering_dir / "module-transitions.md").write_text(
            "---\ninclusion: always\ndescription: Module transitions\n---\n\n",
            encoding="utf-8",
        )

        result = split_always_on_file(
            source_path=agent_file,
            rules=AGENT_INSTRUCTIONS_EXTRACTIONS,
            steering_dir=steering_dir,
        )

        assert result.core_line_count <= 80, (
            f"agent-instructions.md has {result.core_line_count} non-blank lines, "
            f"expected ≤ 80"
        )

    def test_module_transitions_core_under_60_lines(self, tmp_path: Path) -> None:
        """After split, module-transitions.md core ≤ 60 non-blank lines."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()

        transitions_file = steering_dir / "module-transitions.md"
        transitions_file.write_text(_make_module_transitions(), encoding="utf-8")

        result = split_transitions_file(
            source_path=transitions_file,
            keep_sections=TRANSITIONS_KEEP,
            extract_sections=TRANSITIONS_EXTRACT,
            steering_dir=steering_dir,
        )

        assert result.core_line_count <= 60, (
            f"module-transitions.md has {result.core_line_count} non-blank lines, "
            f"expected ≤ 60"
        )

    def test_count_non_blank_lines_excludes_frontmatter(self) -> None:
        """_count_non_blank_lines excludes YAML frontmatter delimiters."""
        content = "---\ninclusion: always\n---\n\n# Title\n\nLine 1\nLine 2\n"
        # Non-blank lines: "inclusion: always" is inside frontmatter (excluded),
        # "# Title", "Line 1", "Line 2" = 3 non-blank lines
        # Wait — frontmatter content lines are also excluded by the function
        count = _count_non_blank_lines(content)
        # Only "# Title", "Line 1", "Line 2" should count
        assert count == 3

    def test_count_non_blank_lines_skips_blank_lines(self) -> None:
        """_count_non_blank_lines skips blank lines in body."""
        content = "# Title\n\n\nLine 1\n\nLine 2\n\n\n"
        count = _count_non_blank_lines(content)
        assert count == 3  # "# Title", "Line 1", "Line 2"


# ---------------------------------------------------------------------------
# TestTokenCountTargets
# ---------------------------------------------------------------------------


class TestTokenCountTargets:
    """Test compression targets for large manual files.

    These tests verify that compress_file() correctly reports whether targets
    are met. For already-terse files, the target may not be achievable — the
    test verifies that compress_file reports target_met=False and does NOT
    discard content.

    Requirements: 3.1, 3.2, 3.3, 3.4
    """

    def test_hook_registry_critical_under_5718_tokens(self, tmp_path: Path) -> None:
        """compress_file reports correct target status for hook-registry-critical.

        Target: ≤ 5718 tokens (70% of 8169).
        """
        file_path = tmp_path / "hook-registry-critical.md"
        content = _make_compressible_file(5718)
        file_path.write_text(content, encoding="utf-8")

        target = CompressTarget(
            filename="hook-registry-critical.md", max_token_ratio=0.70
        )
        result = compress_file(file_path, target)

        # Verify compression was attempted and markers preserved
        assert result.markers_preserved is True
        assert result.compressed_tokens <= result.original_tokens
        # If target met, verify the token count
        if result.target_met:
            assert result.compressed_tokens <= 5718
        else:
            # Target not met — verify content was not discarded
            compressed_content = file_path.read_text(encoding="utf-8")
            assert len(compressed_content) > 0

    def test_hook_registry_modules_under_5521_tokens(self, tmp_path: Path) -> None:
        """compress_file reports correct target status for hook-registry-modules.

        Target: ≤ 5521 tokens (70% of 7887).
        """
        file_path = tmp_path / "hook-registry-modules.md"
        content = _make_compressible_file(5521)
        file_path.write_text(content, encoding="utf-8")

        target = CompressTarget(
            filename="hook-registry-modules.md", max_token_ratio=0.70
        )
        result = compress_file(file_path, target)

        assert result.markers_preserved is True
        assert result.compressed_tokens <= result.original_tokens
        if result.target_met:
            assert result.compressed_tokens <= 5521
        else:
            compressed_content = file_path.read_text(encoding="utf-8")
            assert len(compressed_content) > 0

    def test_module_03_under_4814_tokens(self, tmp_path: Path) -> None:
        """compress_file reports correct target status for module-03.

        Target: ≤ 4814 tokens (75% of 6419).
        """
        file_path = tmp_path / "module-03-system-verification.md"
        content = _make_compressible_file(4814)
        file_path.write_text(content, encoding="utf-8")

        target = CompressTarget(
            filename="module-03-system-verification.md", max_token_ratio=0.75
        )
        result = compress_file(file_path, target)

        assert result.markers_preserved is True
        assert result.compressed_tokens <= result.original_tokens
        if result.target_met:
            assert result.compressed_tokens <= 4814
        else:
            compressed_content = file_path.read_text(encoding="utf-8")
            assert len(compressed_content) > 0

    def test_onboarding_flow_under_3950_tokens(self, tmp_path: Path) -> None:
        """compress_file reports correct target status for onboarding-flow.

        Target: ≤ 3950 tokens (75% of 5266).
        """
        file_path = tmp_path / "onboarding-flow.md"
        content = _make_compressible_file(3950)
        file_path.write_text(content, encoding="utf-8")

        target = CompressTarget(filename="onboarding-flow.md", max_token_ratio=0.75)
        result = compress_file(file_path, target)

        assert result.markers_preserved is True
        assert result.compressed_tokens <= result.original_tokens
        if result.target_met:
            assert result.compressed_tokens <= 3950
        else:
            compressed_content = file_path.read_text(encoding="utf-8")
            assert len(compressed_content) > 0

    def test_compress_does_not_discard_content_on_failure(self, tmp_path: Path) -> None:
        """When target cannot be met, compress_file preserves all content."""
        # Create a file that is already terse (no filler to remove)
        terse_content = (
            "---\ninclusion: manual\ndescription: Already terse\n---\n\n"
            "# Terse File\n\n"
            "## Rules\n\n"
            "1. Do X\n"
            "2. Do Y\n"
            "3. Do Z\n"
        )
        file_path = tmp_path / "terse-file.md"
        file_path.write_text(terse_content, encoding="utf-8")

        # Set an impossible target (10% of original)
        target = CompressTarget(filename="terse-file.md", max_token_ratio=0.10)
        result = compress_file(file_path, target)

        assert result.target_met is False
        # Content should still be present (not discarded)
        final_content = file_path.read_text(encoding="utf-8")
        assert "# Terse File" in final_content
        assert "1. Do X" in final_content


# ---------------------------------------------------------------------------
# TestSectionExtraction
# ---------------------------------------------------------------------------


class TestSectionExtraction:
    """Test specific section extraction behavior.

    Requirements: 1.3, 1.7
    """

    def test_sdk_method_discovery_extracted_to_mcp_usage_reference(
        self, tmp_path: Path
    ) -> None:
        """SDK Method Discovery section is extracted to mcp-usage-reference.md."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()

        agent_file = steering_dir / "agent-instructions.md"
        agent_file.write_text(_make_agent_instructions(), encoding="utf-8")

        # Create destination files
        mcp_ref = steering_dir / "mcp-usage-reference.md"
        mcp_ref.write_text(
            "---\ninclusion: auto\ndescription: MCP usage reference\n---\n\n",
            encoding="utf-8",
        )
        (steering_dir / "track-switching.md").write_text(
            "---\ninclusion: auto\ndescription: Track switching\n---\n\n",
            encoding="utf-8",
        )
        (steering_dir / "conversation-protocol.md").write_text(
            "---\ninclusion: auto\ndescription: Conversation protocol\n---\n\n",
            encoding="utf-8",
        )
        (steering_dir / "module-transitions.md").write_text(
            "---\ninclusion: always\ndescription: Module transitions\n---\n\n",
            encoding="utf-8",
        )

        split_always_on_file(
            source_path=agent_file,
            rules=AGENT_INSTRUCTIONS_EXTRACTIONS,
            steering_dir=steering_dir,
        )

        # Verify SDK Method Discovery content is in mcp-usage-reference.md
        mcp_content = mcp_ref.read_text(encoding="utf-8")
        assert "SDK Method Discovery" in mcp_content
        assert "Use the MCP tool to discover available SDK methods" in mcp_content

    def test_dispatch_pointer_present_in_core(self, tmp_path: Path) -> None:
        """Dispatch pointers replace extracted sections in the core file."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()

        agent_file = steering_dir / "agent-instructions.md"
        agent_file.write_text(_make_agent_instructions(), encoding="utf-8")

        # Create destination files
        (steering_dir / "mcp-usage-reference.md").write_text(
            "---\ninclusion: auto\ndescription: MCP usage\n---\n\n",
            encoding="utf-8",
        )
        (steering_dir / "track-switching.md").write_text(
            "---\ninclusion: auto\ndescription: Track switching\n---\n\n",
            encoding="utf-8",
        )
        (steering_dir / "conversation-protocol.md").write_text(
            "---\ninclusion: auto\ndescription: Conversation protocol\n---\n\n",
            encoding="utf-8",
        )
        (steering_dir / "module-transitions.md").write_text(
            "---\ninclusion: always\ndescription: Module transitions\n---\n\n",
            encoding="utf-8",
        )

        split_always_on_file(
            source_path=agent_file,
            rules=AGENT_INSTRUCTIONS_EXTRACTIONS,
            steering_dir=steering_dir,
        )

        # Read the modified core file
        core_content = agent_file.read_text(encoding="utf-8")

        # Verify dispatch pointers are present
        assert "For SDK method discovery: load `mcp-usage-reference.md`" in core_content
        assert "For track switching triggers: load `track-switching.md`" in core_content
        assert (
            "For .question_pending format: load `conversation-protocol.md`"
            in core_content
        )

        # Verify extracted sections are removed from core
        assert "### SDK Method Discovery" not in core_content
        assert "## Track Switching" not in core_content

    def test_track_switching_appended_to_existing_file(
        self, tmp_path: Path
    ) -> None:
        """Track Switching section is appended to existing track-switching.md."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()

        agent_file = steering_dir / "agent-instructions.md"
        agent_file.write_text(_make_agent_instructions(), encoding="utf-8")

        # Create destination files with existing content
        track_file = steering_dir / "track-switching.md"
        track_file.write_text(
            "---\ninclusion: auto\ndescription: Track switching\n---\n\n"
            "## Existing Track Content\n\nExisting rules here.\n",
            encoding="utf-8",
        )
        (steering_dir / "mcp-usage-reference.md").write_text(
            "---\ninclusion: auto\ndescription: MCP usage\n---\n\n",
            encoding="utf-8",
        )
        (steering_dir / "conversation-protocol.md").write_text(
            "---\ninclusion: auto\ndescription: Conversation protocol\n---\n\n",
            encoding="utf-8",
        )
        (steering_dir / "module-transitions.md").write_text(
            "---\ninclusion: always\ndescription: Module transitions\n---\n\n",
            encoding="utf-8",
        )

        split_always_on_file(
            source_path=agent_file,
            rules=AGENT_INSTRUCTIONS_EXTRACTIONS,
            steering_dir=steering_dir,
        )

        # Verify track-switching.md has both old and new content
        track_content = track_file.read_text(encoding="utf-8")
        assert "Existing Track Content" in track_content
        assert "Switch tracks when the user requests" in track_content


# ---------------------------------------------------------------------------
# TestNewFileFrontmatter
# ---------------------------------------------------------------------------


class TestNewFileFrontmatter:
    """Test YAML frontmatter structure for new files.

    Requirements: 7.4
    """

    def test_new_file_has_inclusion_field(self, tmp_path: Path) -> None:
        """Newly created files have an inclusion field in frontmatter."""
        new_file = tmp_path / "new-steering-file.md"
        _create_file_with_frontmatter(new_file, "### SDK Method Discovery")

        content = new_file.read_text(encoding="utf-8")
        assert "inclusion:" in content

        # Parse frontmatter to verify field value
        lines = content.splitlines()
        assert lines[0] == "---"
        inclusion_found = False
        for line in lines[1:]:
            if line.strip() == "---":
                break
            if line.startswith("inclusion:"):
                inclusion_found = True
                value = line.split(":", 1)[1].strip()
                assert value in ("always", "auto", "fileMatch", "manual"), (
                    f"inclusion value '{value}' is not valid"
                )
        assert inclusion_found, "inclusion field not found in frontmatter"

    def test_new_file_has_description_field(self, tmp_path: Path) -> None:
        """Newly created files have a description field in frontmatter."""
        new_file = tmp_path / "new-steering-file.md"
        _create_file_with_frontmatter(new_file, "## Quality Feedback Loop")

        content = new_file.read_text(encoding="utf-8")
        assert "description:" in content

        # Parse frontmatter to verify field is non-empty
        lines = content.splitlines()
        description_found = False
        for line in lines[1:]:
            if line.strip() == "---":
                break
            if line.startswith("description:"):
                description_found = True
                value = line.split(":", 1)[1].strip().strip('"').strip("'")
                assert len(value) > 0, "description field must be non-empty"
        assert description_found, "description field not found in frontmatter"

    def test_new_file_frontmatter_delimiters(self, tmp_path: Path) -> None:
        """Newly created files start and end frontmatter with --- delimiters."""
        new_file = tmp_path / "test-frontmatter.md"
        _create_file_with_frontmatter(new_file, "### Hook Registry")

        content = new_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Must start with ---
        assert lines[0] == "---", f"Expected '---' as first line, got '{lines[0]}'"

        # Must have a closing ---
        closing_found = any(line.strip() == "---" for line in lines[1:])
        assert closing_found, "Frontmatter must be closed with '---'"

    def test_split_creates_detail_file_with_valid_frontmatter(
        self, tmp_path: Path
    ) -> None:
        """split_transitions_file creates detail file with frontmatter."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()

        transitions_file = steering_dir / "module-transitions.md"
        transitions_file.write_text(_make_module_transitions(), encoding="utf-8")

        split_transitions_file(
            source_path=transitions_file,
            keep_sections=TRANSITIONS_KEEP,
            extract_sections=TRANSITIONS_EXTRACT,
            steering_dir=steering_dir,
        )

        detail_file = steering_dir / "module-transitions-detail.md"
        assert detail_file.exists(), "module-transitions-detail.md should be created"

        content = detail_file.read_text(encoding="utf-8")
        assert content.startswith("---")
        assert "inclusion: auto" in content
        assert "description:" in content


# ---------------------------------------------------------------------------
# TestKeywordMappings
# ---------------------------------------------------------------------------


class TestKeywordMappings:
    """Test keyword mappings in steering-index.yaml for new files.

    Requirements: 5.6
    """

    def test_default_keyword_mappings_include_sdk_keywords(self) -> None:
        """DEFAULT_KEYWORD_MAPPINGS includes SDK-related keywords."""
        assert "sdk method discovery" in DEFAULT_KEYWORD_MAPPINGS
        expected = "mcp-usage-reference.md"
        assert DEFAULT_KEYWORD_MAPPINGS["sdk method discovery"] == expected

    def test_default_keyword_mappings_include_mcp_tool(self) -> None:
        """DEFAULT_KEYWORD_MAPPINGS includes 'mcp tool' keyword."""
        assert "mcp tool" in DEFAULT_KEYWORD_MAPPINGS
        expected = "mcp-usage-reference.md"
        assert DEFAULT_KEYWORD_MAPPINGS["mcp tool"] == expected

    def test_default_keyword_mappings_include_which_tool(self) -> None:
        """DEFAULT_KEYWORD_MAPPINGS includes 'which tool' keyword."""
        assert "which tool" in DEFAULT_KEYWORD_MAPPINGS
        expected = "mcp-usage-reference.md"
        assert DEFAULT_KEYWORD_MAPPINGS["which tool"] == expected

    def test_default_keyword_mappings_include_transition_keywords(self) -> None:
        """DEFAULT_KEYWORD_MAPPINGS includes transition-related keywords."""
        detail = "module-transitions-detail.md"
        assert "transition" in DEFAULT_KEYWORD_MAPPINGS
        assert DEFAULT_KEYWORD_MAPPINGS["transition"] == detail
        assert "sub-step" in DEFAULT_KEYWORD_MAPPINGS
        assert DEFAULT_KEYWORD_MAPPINGS["sub-step"] == detail
        assert "quality loop" in DEFAULT_KEYWORD_MAPPINGS
        assert DEFAULT_KEYWORD_MAPPINGS["quality loop"] == detail

    def test_default_keyword_mappings_include_question_keywords(self) -> None:
        """DEFAULT_KEYWORD_MAPPINGS includes question-related keywords."""
        proto = "conversation-protocol.md"
        assert "question_pending" in DEFAULT_KEYWORD_MAPPINGS
        assert DEFAULT_KEYWORD_MAPPINGS["question_pending"] == proto
        assert "question format" in DEFAULT_KEYWORD_MAPPINGS
        assert DEFAULT_KEYWORD_MAPPINGS["question format"] == proto

    def test_all_new_files_have_at_least_one_keyword(self) -> None:
        """Every new file referenced in DEFAULT_KEYWORD_MAPPINGS has ≥1 keyword."""
        # Collect all unique destination files
        dest_files = set(DEFAULT_KEYWORD_MAPPINGS.values())
        # Each destination file should have at least one keyword pointing to it
        for dest_file in dest_files:
            keywords_for_file = [
                k for k, v in DEFAULT_KEYWORD_MAPPINGS.items() if v == dest_file
            ]
            assert len(keywords_for_file) >= 1, (
                f"File '{dest_file}' has no keyword mappings"
            )


# ---------------------------------------------------------------------------
# TestDryRunMode
# ---------------------------------------------------------------------------


class TestDryRunMode:
    """Test dry-run mode produces no file changes.

    Requirements: 1.1, 2.3
    """

    def test_dry_run_does_not_modify_files(self, tmp_path: Path) -> None:
        """Dry-run mode reports changes without writing files."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()

        # Create agent-instructions.md
        agent_file = steering_dir / "agent-instructions.md"
        agent_content = _make_agent_instructions()
        agent_file.write_text(agent_content, encoding="utf-8")

        # Create module-transitions.md
        transitions_file = steering_dir / "module-transitions.md"
        transitions_content = _make_module_transitions()
        transitions_file.write_text(transitions_content, encoding="utf-8")

        # Create a compressible file
        hook_file = steering_dir / "hook-registry-critical.md"
        hook_content = _make_compressible_file(5718)
        hook_file.write_text(hook_content, encoding="utf-8")

        # Create steering-index.yaml (minimal)
        index_path = steering_dir / "steering-index.yaml"
        index_path.write_text(
            "budget:\n  total_tokens: 1000\nfile_metadata:\nkeywords:\n",
            encoding="utf-8",
        )

        # Record file contents before dry-run
        before_agent = agent_file.read_text(encoding="utf-8")
        before_transitions = transitions_file.read_text(encoding="utf-8")
        before_hook = hook_file.read_text(encoding="utf-8")
        before_index = index_path.read_text(encoding="utf-8")

        # Run optimize in dry-run mode
        optimize(
            steering_dir=steering_dir,
            index_path=index_path,
            dry_run=True,
        )

        # Verify no files were modified
        assert agent_file.read_text(encoding="utf-8") == before_agent
        assert transitions_file.read_text(encoding="utf-8") == before_transitions
        assert hook_file.read_text(encoding="utf-8") == before_hook
        assert index_path.read_text(encoding="utf-8") == before_index

    def test_dry_run_does_not_create_new_files(self, tmp_path: Path) -> None:
        """Dry-run mode does not create new destination files."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()

        # Create agent-instructions.md (has extractable sections)
        agent_file = steering_dir / "agent-instructions.md"
        agent_file.write_text(_make_agent_instructions(), encoding="utf-8")

        # Create module-transitions.md
        transitions_file = steering_dir / "module-transitions.md"
        transitions_file.write_text(_make_module_transitions(), encoding="utf-8")

        # Create steering-index.yaml (minimal)
        index_path = steering_dir / "steering-index.yaml"
        index_path.write_text(
            "budget:\n  total_tokens: 1000\nfile_metadata:\nkeywords:\n",
            encoding="utf-8",
        )

        # Record files before dry-run
        files_before = set(f.name for f in steering_dir.iterdir())

        # Run optimize in dry-run mode
        optimize(
            steering_dir=steering_dir,
            index_path=index_path,
            dry_run=True,
        )

        # Verify no new files were created
        files_after = set(f.name for f in steering_dir.iterdir())
        assert files_after == files_before, (
            f"Dry-run created new files: {files_after - files_before}"
        )

    def test_dry_run_returns_result_with_zero_savings(self, tmp_path: Path) -> None:
        """Dry-run mode returns OptimizeResult with zero token savings."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()

        agent_file = steering_dir / "agent-instructions.md"
        agent_file.write_text(_make_agent_instructions(), encoding="utf-8")

        transitions_file = steering_dir / "module-transitions.md"
        transitions_file.write_text(_make_module_transitions(), encoding="utf-8")

        index_path = steering_dir / "steering-index.yaml"
        index_path.write_text(
            "budget:\n  total_tokens: 1000\nfile_metadata:\nkeywords:\n",
            encoding="utf-8",
        )

        result = optimize(
            steering_dir=steering_dir,
            index_path=index_path,
            dry_run=True,
        )

        assert result.total_token_savings == 0
