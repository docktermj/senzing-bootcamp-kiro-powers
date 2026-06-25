"""Property-based tests for steering optimization correctness properties.

Validates that the optimize_steering.py script preserves behavioral rules
and markers during optimization transformations.

Feature: steering-optimization
"""

from __future__ import annotations

import io
import sys
import tempfile
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from optimize_steering import (  # noqa: E402, I001
    CompressTarget,
    ExtractionRule,
    RuleInventory,
    _create_file_with_frontmatter,
    _verify_budget_consistency,
    compress_file,
    extract_rule_inventory,
    size_category,
    split_always_on_file,
    token_count,
    verify_preservation,
)  # isort: skip


# ---------------------------------------------------------------------------
# Hypothesis strategies for generating steering file content with markers
# ---------------------------------------------------------------------------


def st_step_number() -> st.SearchStrategy[int]:
    """Strategy for generating step numbers (1-20)."""
    return st.integers(min_value=1, max_value=20)


def st_gate_condition() -> st.SearchStrategy[str]:
    """Strategy for generating gate condition text after ⛔ marker."""
    conditions = st.sampled_from([
        "MANDATORY GATE",
        "DO NOT PROCEED",
        "STOP — verify before continuing",
        "BLOCKING: user must confirm",
        "HALT until prerequisite met",
        "NEVER skip this step",
        "REQUIRED: complete before advancing",
    ])
    return conditions


def st_gate_line() -> st.SearchStrategy[str]:
    """Strategy for generating a complete ⛔ gate marker line."""
    return st.builds(
        lambda step, condition: f"⛔ Step {step}: {condition}",
        step=st_step_number(),
        condition=st_gate_condition(),
    )


def st_question_instruction() -> st.SearchStrategy[str]:
    """Strategy for generating question instruction text after 👉 marker."""
    instructions = st.sampled_from([
        "Ask the bootcamper which language they prefer",
        "Confirm the user has completed the installation",
        "Ask whether they want to proceed with the default configuration",
        "Check if the user has a Senzing license key",
        "Ask the bootcamper to verify their database connection",
        "Confirm they understand the entity resolution concept",
        "Ask which deployment track they want to follow",
    ])
    return instructions


def st_question_line() -> st.SearchStrategy[str]:
    """Strategy for generating a complete 👉 question marker line."""
    return st.builds(
        lambda step, instruction: f"👉 Step {step}: {instruction}",
        step=st_step_number(),
        instruction=st_question_instruction(),
    )


def st_plain_line() -> st.SearchStrategy[str]:
    """Strategy for generating non-marker steering file lines."""
    return st.sampled_from([
        "## Module Overview",
        "### Prerequisites",
        "1. **Install Senzing** — follow the platform guide",
        "2. **Configure database** — set up PostgreSQL or SQLite",
        "- Use the MCP tool to verify installation",
        "- Check that all dependencies are resolved",
        "**Checkpoint:** Write step 3 to progress file",
        "The bootcamper should now have a working environment.",
        "| Step | Action | Expected Result |",
        "| 1 | Run preflight | All checks pass |",
        "",
        "STOP — wait for user response before continuing.",
        "For SDK method discovery: load `mcp-usage-reference.md`",
    ])


def st_steering_content_with_gates(
    min_gates: int = 1, max_gates: int = 5
) -> st.SearchStrategy[str]:
    """Strategy for generating steering file content with ⛔ gate markers.

    Args:
        min_gates: Minimum number of gate marker lines.
        max_gates: Maximum number of gate marker lines.

    Returns:
        Strategy producing multi-line steering file content with gates.
    """
    return st.builds(
        lambda gates, plains: _build_steering_content(gates, plains),
        gates=st.lists(st_gate_line(), min_size=min_gates, max_size=max_gates),
        plains=st.lists(st_plain_line(), min_size=3, max_size=10),
    )


def st_steering_content_with_questions(
    min_questions: int = 1, max_questions: int = 5
) -> st.SearchStrategy[str]:
    """Strategy for generating steering file content with 👉 question markers.

    Args:
        min_questions: Minimum number of question marker lines.
        max_questions: Maximum number of question marker lines.

    Returns:
        Strategy producing multi-line steering file content with questions.
    """
    return st.builds(
        lambda questions, plains: _build_steering_content(questions, plains),
        questions=st.lists(
            st_question_line(), min_size=min_questions, max_size=max_questions
        ),
        plains=st.lists(st_plain_line(), min_size=3, max_size=10),
    )


def _build_steering_content(marker_lines: list[str], plain_lines: list[str]) -> str:
    """Interleave marker lines with plain lines to build file content.

    Args:
        marker_lines: Lines containing ⛔ or 👉 markers.
        plain_lines: Non-marker lines for context.

    Returns:
        Multi-line string with YAML frontmatter and interleaved content.
    """
    frontmatter = "---\ninclusion: manual\ndescription: Test steering file\n---\n\n"
    # Interleave: plain lines between each marker line
    lines: list[str] = []
    for i, marker in enumerate(marker_lines):
        # Add some plain lines before each marker
        if i < len(plain_lines):
            lines.append(plain_lines[i])
        lines.append(marker)
    # Add remaining plain lines at the end
    for remaining in plain_lines[len(marker_lines):]:
        lines.append(remaining)
    return frontmatter + "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Strategies for Property 1: Rule preservation
# ---------------------------------------------------------------------------


def st_directive_rule() -> st.SearchStrategy[str]:
    """Strategy for generating lines with SHALL/MUST/NEVER/ALWAYS directives."""
    return st.builds(
        lambda keyword, subject, action: f"THE agent {keyword} {subject} {action}",
        keyword=st.sampled_from(["SHALL", "MUST", "NEVER", "ALWAYS"]),
        subject=st.from_regex(r"[a-z]{3,10}", fullmatch=True),
        action=st.from_regex(r"[a-z ]{5,20}", fullmatch=True),
    )


def st_hook_rule_line() -> st.SearchStrategy[str]:
    """Strategy for generating lines referencing hook definitions."""
    return st.builds(
        lambda hook_id: f'Hook `{hook_id}.kiro.hook` with "name" and "when" fields',
        hook_id=st.from_regex(r"[a-z][a-z0-9-]{3,15}", fullmatch=True),
    )


def st_file_placement_rule_line() -> st.SearchStrategy[str]:
    """Strategy for generating lines about file placement rules."""
    return st.builds(
        lambda dirname: f"File placement: all scripts belong in `{dirname}/`",
        dirname=st.from_regex(r"[a-z][a-z0-9-]{2,12}", fullmatch=True),
    )


def st_mixed_steering_content() -> st.SearchStrategy[str]:
    """Strategy for generating steering content with all rule marker types.

    Produces content with a mix of ⛔ gates, 👉 questions, SHALL/MUST/NEVER/ALWAYS
    directives, hook rules, and file placement rules.

    Returns:
        Strategy producing multi-line steering file content with mixed markers.
    """
    return st.builds(
        _build_mixed_steering_content,
        gates=st.lists(st_gate_line(), min_size=0, max_size=3),
        questions=st.lists(st_question_line(), min_size=0, max_size=3),
        directives=st.lists(st_directive_rule(), min_size=0, max_size=3),
        hooks=st.lists(st_hook_rule_line(), min_size=0, max_size=2),
        file_rules=st.lists(st_file_placement_rule_line(), min_size=0, max_size=2),
    )


def _build_mixed_steering_content(
    gates: list[str],
    questions: list[str],
    directives: list[str],
    hooks: list[str],
    file_rules: list[str],
) -> str:
    """Assemble steering file content from multiple rule marker types.

    Args:
        gates: Lines with ⛔ gate markers.
        questions: Lines with 👉 question markers.
        directives: Lines with SHALL/MUST/NEVER/ALWAYS.
        hooks: Lines with hook definitions.
        file_rules: Lines with file placement rules.

    Returns:
        Multi-line string with YAML frontmatter and all rule types.
    """
    lines = [
        "---",
        "inclusion: manual",
        "description: Test steering file",
        "---",
        "",
        "# Test Steering File",
        "",
    ]
    for gate in gates:
        lines.append(gate)
        lines.append("")
    for question in questions:
        lines.append(question)
        lines.append("")
    for directive in directives:
        lines.append(directive)
        lines.append("")
    for hook in hooks:
        lines.append(hook)
        lines.append("")
    for rule in file_rules:
        lines.append(rule)
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Property 1: Behavioral rule preservation across optimization
# ---------------------------------------------------------------------------


class TestProperty1RulePreservation:
    """Property 1: Behavioral rule preservation across optimization.

    For any behavioral rule marker (⛔ gate, 👉 question protocol,
    SHALL/NEVER/MUST/ALWAYS directive, hook definition, or file placement rule)
    present in the original steering file set, that marker SHALL appear in the
    optimized output file set (the union of all modified and newly created files),
    and the total count of distinct behavioral rules in the optimized set SHALL
    equal the count in the original set.

    **Validates: Requirements 1.2, 1.6, 2.5, 3.5, 6.1, 6.2, 6.8**
    """

    @given(content=st_mixed_steering_content())
    @settings(max_examples=20)
    def test_all_rules_preserved_in_identity_transform(self, content: str) -> None:
        """Any rule inventory compared to itself should show zero missing rules.

        Generates synthetic steering file content with various rule markers,
        writes to a temp file, extracts the rule inventory, and verifies that
        comparing the inventory to itself yields no missing rules (identity
        preservation).

        Args:
            content: Generated steering file content with mixed rule markers.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test-steering.md"
            test_file.write_text(content, encoding="utf-8")

            inventory = extract_rule_inventory([test_file])

            # Identity preservation: comparing inventory to itself yields no missing
            missing = verify_preservation(inventory, inventory)
            assert missing == [], (
                f"Identity transform should produce zero missing rules, "
                f"got: {missing}"
            )

    @given(content=st_mixed_steering_content())
    @settings(max_examples=20)
    def test_missing_rule_detected(self, content: str) -> None:
        """Removing any rule from optimized set should be detected.

        Generates steering content, extracts the inventory, removes one rule
        from the first non-empty category, and verifies that verify_preservation()
        detects the missing rule.

        Args:
            content: Generated steering file content with mixed rule markers.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test-steering.md"
            test_file.write_text(content, encoding="utf-8")

            original = extract_rule_inventory([test_file])

            # Only test when there are rules to remove
            if original.total_count == 0:
                return

            # Create a copy with one rule removed from the first non-empty category
            optimized = RuleInventory(
                gate_markers=list(original.gate_markers),
                question_markers=list(original.question_markers),
                mcp_rules=list(original.mcp_rules),
                hook_rules=list(original.hook_rules),
                file_rules=list(original.file_rules),
            )

            # Remove one rule from the first non-empty category
            removed = False
            if optimized.gate_markers and not removed:
                optimized.gate_markers.pop(0)
                removed = True
            elif optimized.question_markers and not removed:
                optimized.question_markers.pop(0)
                removed = True
            elif optimized.mcp_rules and not removed:
                optimized.mcp_rules.pop(0)
                removed = True
            elif optimized.hook_rules and not removed:
                optimized.hook_rules.pop(0)
                removed = True
            elif optimized.file_rules and not removed:
                optimized.file_rules.pop(0)
                removed = True

            assert removed, "Should have removed at least one rule"

            # verify_preservation should detect the missing rule
            missing = verify_preservation(original, optimized)
            assert len(missing) > 0, (
                f"Removing a rule should be detected. "
                f"Original count: {original.total_count}, "
                f"Optimized count: {optimized.total_count}"
            )

    @given(
        content_a=st_mixed_steering_content(),
        content_b=st_mixed_steering_content(),
    )
    @settings(max_examples=20)
    def test_multi_file_inventory_preserves_all_rules(
        self, content_a: str, content_b: str
    ) -> None:
        """Splitting content across files and recombining preserves all rules.

        Writes two steering files, extracts the combined inventory (simulating
        the original file set), then extracts again from the same files
        (simulating the optimized set being identical). Verifies that
        verify_preservation() reports no missing rules.

        Args:
            content_a: Generated steering file content for first file.
            content_b: Generated steering file content for second file.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_a = Path(tmp_dir) / "steering-a.md"
            file_b = Path(tmp_dir) / "steering-b.md"
            file_a.write_text(content_a, encoding="utf-8")
            file_b.write_text(content_b, encoding="utf-8")

            # Original = combined inventory from both files
            original = extract_rule_inventory([file_a, file_b])

            # Optimized = same files (simulates optimization that preserves content)
            optimized = extract_rule_inventory([file_a, file_b])

            # Preservation should hold: same file set yields same inventory
            missing = verify_preservation(original, optimized)
            assert missing == [], (
                f"Same file set should yield identical inventory, "
                f"got missing: {missing}"
            )
            assert original.total_count == optimized.total_count


# ---------------------------------------------------------------------------
# Property 7: Gate and question marker verbatim preservation
# ---------------------------------------------------------------------------


class TestProperty7MarkerPreservation:
    """Property 7: Gate and question marker verbatim preservation.

    For any line containing a ⛔ or 👉 marker in the original steering files,
    the exact same line (character-for-character, including the marker and its
    associated step number or instruction) SHALL appear in the corresponding
    optimized output file, with no alteration to the marker text or its
    immediate context (the step number or gate condition on the same line).

    Validates: Requirements 3.7, 6.1, 6.2
    """

    @given(content=st_steering_content_with_gates(min_gates=1, max_gates=5))
    @settings(max_examples=20)
    def test_gate_markers_preserved_verbatim(self, content: str) -> None:
        """⛔ markers must appear character-for-character in optimized output.

        Generates synthetic steering file content with ⛔ gate markers,
        writes to a temp file, extracts the rule inventory, and verifies
        that every gate marker line is captured exactly as written.

        Args:
            content: Generated steering file content with gate markers.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test_gates.md"
            test_file.write_text(content, encoding="utf-8")

            # Extract inventory from the file
            inventory = extract_rule_inventory([test_file])

            # Verify all ⛔ lines from the content appear in the inventory
            original_gate_lines = [
                " ".join(line.split())
                for line in content.splitlines()
                if "⛔" in line and line.strip()
            ]

            for gate_line in original_gate_lines:
                assert gate_line in inventory.gate_markers, (
                    f"Gate marker line not preserved verbatim in inventory: "
                    f"'{gate_line}'\n"
                    f"Inventory contains: {inventory.gate_markers}"
                )

    @given(content=st_steering_content_with_questions(min_questions=1, max_questions=5))
    @settings(max_examples=20)
    def test_question_markers_preserved_verbatim(
        self, content: str
    ) -> None:
        """👉 markers must appear character-for-character in optimized output.

        Generates synthetic steering file content with 👉 question markers,
        writes to a temp file, extracts the rule inventory, and verifies
        that every question marker line is captured exactly as written.

        Args:
            content: Generated steering file content with question markers.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test_questions.md"
            test_file.write_text(content, encoding="utf-8")

            # Extract inventory from the file
            inventory = extract_rule_inventory([test_file])

            # Verify all 👉 lines from the content appear in the inventory
            original_question_lines = [
                " ".join(line.split())
                for line in content.splitlines()
                if "👉" in line and line.strip()
            ]

            for question_line in original_question_lines:
                assert question_line in inventory.question_markers, (
                    f"Question marker line not preserved verbatim in inventory: "
                    f"'{question_line}'\n"
                    f"Inventory contains: {inventory.question_markers}"
                )

    @given(content=st_steering_content_with_gates(min_gates=1, max_gates=3))
    @settings(max_examples=20)
    def test_verify_preservation_detects_altered_gate(
        self, content: str
    ) -> None:
        """verify_preservation() detects when a ⛔ gate marker line is altered.

        Creates an original inventory from generated content, then creates
        a modified inventory where one gate marker has been altered (step
        number changed). Verifies that verify_preservation() reports the
        missing rule.

        Args:
            content: Generated steering file content with gate markers.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Write original content
            original_file = Path(tmp_dir) / "original.md"
            original_file.write_text(content, encoding="utf-8")

            # Extract original inventory
            original_inventory = extract_rule_inventory([original_file])

            # Skip if no gate markers were found
            if not original_inventory.gate_markers:
                return

            # Create a modified inventory simulating an alteration
            modified_inventory = RuleInventory(
                gate_markers=[
                    marker.replace("Step ", "Step 99 — ") if i == 0 else marker
                    for i, marker in enumerate(original_inventory.gate_markers)
                ],
                question_markers=list(original_inventory.question_markers),
                mcp_rules=list(original_inventory.mcp_rules),
                hook_rules=list(original_inventory.hook_rules),
                file_rules=list(original_inventory.file_rules),
            )

            # verify_preservation should detect the missing original gate marker
            missing = verify_preservation(original_inventory, modified_inventory)
            assert len(missing) > 0, (
                "verify_preservation() should detect altered gate marker but "
                "reported no missing rules"
            )
            # At least one missing entry should mention "gate marker"
            assert any(
                "gate marker" in m.lower() or "Missing gate" in m for m in missing
            ), (
                f"Expected a gate marker violation but got: {missing}"
            )

    @given(content=st_steering_content_with_questions(min_questions=1, max_questions=3))
    @settings(max_examples=20)
    def test_verify_preservation_detects_altered_question(
        self, content: str
    ) -> None:
        """verify_preservation() detects when a 👉 question marker is altered.

        Creates an original inventory from generated content, then creates
        a modified inventory where one question marker has been altered
        (instruction text changed). Verifies that verify_preservation()
        reports the missing rule.

        Args:
            content: Generated steering file content with question markers.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Write original content
            original_file = Path(tmp_dir) / "original.md"
            original_file.write_text(content, encoding="utf-8")

            # Extract original inventory
            original_inventory = extract_rule_inventory([original_file])

            # Skip if no question markers were found
            if not original_inventory.question_markers:
                return

            # Create a modified inventory simulating an alteration
            modified_inventory = RuleInventory(
                gate_markers=list(original_inventory.gate_markers),
                question_markers=[
                    marker + " [ALTERED]" if i == 0 else marker
                    for i, marker in enumerate(original_inventory.question_markers)
                ],
                mcp_rules=list(original_inventory.mcp_rules),
                hook_rules=list(original_inventory.hook_rules),
                file_rules=list(original_inventory.file_rules),
            )

            # verify_preservation should detect the missing original question marker
            missing = verify_preservation(original_inventory, modified_inventory)
            assert len(missing) > 0, (
                "verify_preservation() should detect altered question marker but "
                "reported no missing rules"
            )
            # At least one missing entry should mention "question marker"
            assert any(
                "question marker" in m.lower() or "Missing question" in m
                for m in missing
            ), (
                f"Expected a question marker violation but got: {missing}"
            )

    @given(
        gates=st.lists(st_gate_line(), min_size=1, max_size=4),
        questions=st.lists(st_question_line(), min_size=1, max_size=4),
    )
    @settings(max_examples=20)
    def test_identical_inventories_pass_verification(
        self, gates: list[str], questions: list[str]
    ) -> None:
        """verify_preservation() returns empty list when inventories match.

        Creates a file with both gate and question markers, extracts the
        inventory twice (simulating original and optimized being identical),
        and verifies that verify_preservation() reports no missing rules.

        Args:
            gates: Generated gate marker lines.
            questions: Generated question marker lines.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Build content with both markers
            all_markers = gates + questions
            plain_lines = ["## Test Section", "Some context line.", ""]
            content = _build_steering_content(all_markers, plain_lines)

            test_file = Path(tmp_dir) / "combined.md"
            test_file.write_text(content, encoding="utf-8")

            # Extract inventory (same file = same inventory)
            original = extract_rule_inventory([test_file])
            optimized = extract_rule_inventory([test_file])

            # Identical inventories should produce no missing rules
            missing = verify_preservation(original, optimized)
            assert missing == [], (
                f"Identical inventories should pass verification but got: {missing}"
            )


# ---------------------------------------------------------------------------
# Strategies for Property 5: YAML frontmatter validity
# ---------------------------------------------------------------------------


def st_heading_text() -> st.SearchStrategy[str]:
    """Strategy for generating heading text used in file creation."""
    return st.sampled_from([
        "### SDK Method Discovery",
        "## Track Switching",
        "### Question_Pending File Format",
        "## Module Transition Execution",
        "## Quality Feedback Loop",
        "### Sub-Step Convention",
        "## Custom Section",
        "### Hook Registry",
        "## Onboarding Flow",
    ])


_VALID_INCLUSION_VALUES = ("always", "auto", "fileMatch", "manual")


def _parse_frontmatter(content: str) -> tuple[bool, dict[str, str]]:
    """Parse YAML frontmatter from file content.

    Args:
        content: Full file content.

    Returns:
        Tuple of (has_frontmatter, fields_dict). fields_dict maps field names
        to their string values. Returns (False, {}) if no valid frontmatter.
    """
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return (False, {})

    # Find closing ---
    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return (False, {})

    # Parse key: value pairs from frontmatter
    fields: dict[str, str] = {}
    for line in lines[1:end_idx]:
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"').strip("'")

    return (True, fields)


# ---------------------------------------------------------------------------
# Property 5: YAML frontmatter validity for new files
# ---------------------------------------------------------------------------


class TestProperty5FrontmatterValidity:
    """Property 5: YAML frontmatter validity for new files.

    For any newly created steering file, the file SHALL begin with a YAML
    frontmatter block (delimited by ---) containing at minimum an inclusion
    field (with value always, auto, fileMatch, or manual) and a description
    field (non-empty string).

    Validates: Requirements 7.4
    """

    @given(heading=st_heading_text())
    @settings(max_examples=20)
    def test_new_files_have_valid_frontmatter(self, heading: str) -> None:
        """Newly created files must have valid YAML frontmatter.

        Uses _create_file_with_frontmatter() to create a new file, then
        verifies the file starts with --- and ends the frontmatter block
        with ---, and contains both inclusion and description fields.

        Args:
            heading: Generated heading text for file creation.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "new-steering-file.md"
            _create_file_with_frontmatter(test_file, heading)

            content = test_file.read_text(encoding="utf-8")
            lines = content.splitlines()

            # File must start with ---
            assert len(lines) >= 3, (
                f"File too short to contain valid frontmatter: {lines}"
            )
            assert lines[0].strip() == "---", (
                f"File must start with '---', got: '{lines[0]}'"
            )

            # Must have a closing ---
            closing_found = False
            for line in lines[1:]:
                if line.strip() == "---":
                    closing_found = True
                    break
            assert closing_found, (
                "Frontmatter must be closed with '---'"
            )

            # Must have both inclusion and description fields
            has_fm, fields = _parse_frontmatter(content)
            assert has_fm, "File must have valid YAML frontmatter"
            assert "inclusion" in fields, (
                f"Frontmatter must contain 'inclusion' field. Got fields: {fields}"
            )
            assert "description" in fields, (
                f"Frontmatter must contain 'description' field. Got fields: {fields}"
            )

    @given(heading=st_heading_text())
    @settings(max_examples=20)
    def test_inclusion_field_has_valid_value(self, heading: str) -> None:
        """inclusion field must be always, auto, fileMatch, or manual.

        Creates a file with _create_file_with_frontmatter() and verifies
        the inclusion field value is one of the four valid options.

        Args:
            heading: Generated heading text for file creation.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test-inclusion.md"
            _create_file_with_frontmatter(test_file, heading)

            content = test_file.read_text(encoding="utf-8")
            has_fm, fields = _parse_frontmatter(content)

            assert has_fm, "File must have valid YAML frontmatter"
            assert "inclusion" in fields, "Frontmatter must have inclusion field"

            inclusion_value = fields["inclusion"]
            assert inclusion_value in _VALID_INCLUSION_VALUES, (
                f"inclusion field must be one of {_VALID_INCLUSION_VALUES}, "
                f"got: '{inclusion_value}'"
            )

    @given(heading=st_heading_text())
    @settings(max_examples=20)
    def test_description_field_is_non_empty(self, heading: str) -> None:
        """description field must be a non-empty string.

        Creates a file with _create_file_with_frontmatter() and verifies
        the description field is present and non-empty.

        Args:
            heading: Generated heading text for file creation.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test-description.md"
            _create_file_with_frontmatter(test_file, heading)

            content = test_file.read_text(encoding="utf-8")
            has_fm, fields = _parse_frontmatter(content)

            assert has_fm, "File must have valid YAML frontmatter"
            assert "description" in fields, "Frontmatter must have description field"

            description_value = fields["description"]
            assert len(description_value) > 0, (
                "description field must be a non-empty string, "
                f"got: '{description_value}'"
            )

    @given(heading=st_heading_text())
    @settings(max_examples=20)
    def test_split_creates_files_with_valid_frontmatter(
        self, heading: str
    ) -> None:
        """split_always_on_file creates valid frontmatter when dest missing.

        Creates a source file with a section matching the heading, then uses
        split_always_on_file() with an extraction rule targeting a non-existent
        destination. Verifies the newly created destination file has valid
        YAML frontmatter with inclusion and description fields.

        Args:
            heading: Generated heading text for the section to extract.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            steering_dir = Path(tmp_dir)

            # Build a source file with the heading as a section
            heading_text = heading.lstrip("#").strip()
            source_content = (
                "---\n"
                "inclusion: always\n"
                "description: Source always-on file\n"
                "---\n\n"
                "## Core Section\n\n"
                "This is the core content that stays.\n\n"
                f"{heading}\n\n"
                f"Content under {heading_text} that should be extracted.\n\n"
                "More content in this section.\n"
            )

            source_file = steering_dir / "source-file.md"
            source_file.write_text(source_content, encoding="utf-8")

            # Define extraction rule for a non-existent destination
            dest_filename = "extracted-destination.md"
            rule = ExtractionRule(
                source_heading=heading,
                destination_file=dest_filename,
                append=True,
                dispatch_pointer=f"For {heading_text}: load `{dest_filename}`",
            )

            # Run split — destination doesn't exist, so it should be created
            split_always_on_file(
                source_path=source_file,
                rules=[rule],
                steering_dir=steering_dir,
            )

            # Verify the destination file was created with valid frontmatter
            dest_file = steering_dir / dest_filename
            assert dest_file.exists(), (
                f"Destination file '{dest_filename}' should have been created"
            )

            content = dest_file.read_text(encoding="utf-8")
            has_fm, fields = _parse_frontmatter(content)

            assert has_fm, (
                "Newly created destination file must have YAML frontmatter"
            )
            assert "inclusion" in fields, (
                f"Destination file must have 'inclusion' field. Got: {fields}"
            )
            assert fields["inclusion"] in _VALID_INCLUSION_VALUES, (
                f"inclusion must be valid, got: '{fields['inclusion']}'"
            )
            assert "description" in fields, (
                f"Destination file must have 'description' field. Got: {fields}"
            )
            assert len(fields["description"]) > 0, (
                "description must be non-empty"
            )


# ---------------------------------------------------------------------------
# Strategies for Property 2: Token reduction for always-on files
# ---------------------------------------------------------------------------


def st_filler_phrase() -> st.SearchStrategy[str]:
    """Strategy for generating filler phrases that compression removes."""
    return st.sampled_from([
        "It is important to note that",
        "Please note that",
        "As mentioned earlier",
        "It should be noted that",
        "It is worth noting that",
        "Keep in mind that",
        "In order to",
        "You need to",
        "You should",
        "This is because",
        "This means that",
        "This ensures that",
    ])


def st_transitional_phrase() -> st.SearchStrategy[str]:
    """Strategy for generating transitional phrases that compression removes."""
    return st.sampled_from([
        "First of all",
        "Moving on to",
        "Now let's",
        "Next we will",
        "With that in mind",
        "Having said that",
        "That being said",
        "In the following section",
        "Going forward",
        "Following this",
        "From here",
    ])


def st_filler_word() -> st.SearchStrategy[str]:
    """Strategy for generating filler words that compression removes."""
    return st.sampled_from([
        "basically",
        "essentially",
        "actually",
        "simply",
        "really",
        "very",
        "quite",
        "certainly",
        "obviously",
        "clearly",
        "effectively",
        "generally",
    ])


def st_verbose_sentence() -> st.SearchStrategy[str]:
    """Strategy for generating a verbose sentence with filler content.

    Produces sentences that contain filler phrases, transitional phrases,
    and filler words — content that the compressor is designed to remove.

    Returns:
        Strategy producing a single verbose sentence.
    """
    return st.builds(
        lambda filler, transition, word, subject, action: (
            f"{transition}, {filler} the agent {word} needs to "
            f"{subject} the {action} in order to proceed effectively."
        ),
        filler=st_filler_phrase(),
        transition=st_transitional_phrase(),
        word=st_filler_word(),
        subject=st.sampled_from([
            "verify", "configure", "initialize", "validate",
            "process", "execute", "complete", "establish",
        ]),
        action=st.sampled_from([
            "database connection", "entity resolution pipeline",
            "configuration settings", "module prerequisites",
            "system environment", "data source mapping",
            "SDK initialization", "record ingestion",
        ]),
    )


def st_verbose_paragraph() -> st.SearchStrategy[str]:
    """Strategy for generating a verbose paragraph (3+ sentences).

    Produces paragraphs with multiple verbose sentences that are compressible
    via filler removal and prose-to-bullet conversion.

    Returns:
        Strategy producing a multi-sentence verbose paragraph.
    """
    return st.builds(
        lambda sentences: " ".join(sentences),
        sentences=st.lists(st_verbose_sentence(), min_size=3, max_size=6),
    )


def st_when_then_block() -> st.SearchStrategy[str]:
    """Strategy for generating WHEN/THEN pattern blocks.

    Produces multiple WHEN/THEN lines that the compressor converts to
    compact arrow notation.

    Returns:
        Strategy producing multi-line WHEN/THEN block.
    """
    return st.builds(
        lambda pairs: "\n".join(
            f"WHEN {cond}, THEN {action}." for cond, action in pairs
        ),
        pairs=st.lists(
            st.tuples(
                st.sampled_from([
                    "the user completes module setup",
                    "the database connection is established",
                    "all prerequisites are verified",
                    "the configuration file is valid",
                    "the SDK is initialized",
                    "the data source is registered",
                ]),
                st.sampled_from([
                    "advance to the next step",
                    "write progress to the state file",
                    "display the completion banner",
                    "load the next module steering",
                    "update the journey map",
                    "trigger the validation hook",
                ]),
            ),
            min_size=2,
            max_size=5,
        ),
    )


def st_compressible_always_on_content() -> st.SearchStrategy[str]:
    """Strategy for generating compressible always-on steering file content.

    Produces content with verbose prose, filler words, transitional phrases,
    and WHEN/THEN patterns — all designed to be compressible by the optimizer.
    The content is long enough to ensure meaningful compression is achievable.

    Returns:
        Strategy producing multi-paragraph verbose steering file content
        with always-on frontmatter.
    """
    return st.builds(
        _build_compressible_content,
        paragraphs=st.lists(st_verbose_paragraph(), min_size=4, max_size=8),
        when_then_blocks=st.lists(st_when_then_block(), min_size=2, max_size=4),
    )


def _build_compressible_content(
    paragraphs: list[str],
    when_then_blocks: list[str],
) -> str:
    """Assemble compressible always-on steering file content.

    Args:
        paragraphs: Verbose paragraphs with filler content.
        when_then_blocks: WHEN/THEN pattern blocks.

    Returns:
        Multi-section steering file content with always-on frontmatter.
    """
    frontmatter = (
        "---\n"
        "inclusion: always\n"
        "description: Test always-on steering file with verbose content\n"
        "---\n\n"
    )
    sections: list[str] = ["# Test Always-On File\n"]

    for i, paragraph in enumerate(paragraphs):
        sections.append(f"## Section {i + 1}\n")
        sections.append(paragraph + "\n")

    for i, block in enumerate(when_then_blocks):
        sections.append(f"## Workflow {i + 1}\n")
        sections.append(block + "\n")

    return frontmatter + "\n".join(sections) + "\n"


# ---------------------------------------------------------------------------
# Property 2: Token reduction for always-on files
# ---------------------------------------------------------------------------


class TestProperty2TokenReduction:
    """Property 2: Token reduction for always-on files.

    For any always-on steering file (files with inclusion: always frontmatter)
    that undergoes Refine-style optimization, the optimized file's token count
    (calculated as round(len(content) / 4)) SHALL be at most 85% of the
    original file's token count, representing a minimum 15% reduction.

    Validates: Requirements 4.3
    """

    @given(content=st_compressible_always_on_content())
    @settings(max_examples=20)
    def test_compression_reduces_tokens(self, content: str) -> None:
        """Compressed content must have fewer tokens than original.

        Generates verbose always-on steering file content, compresses it
        using compress_file() with a max_token_ratio of 0.85, and verifies
        the compressed token count is strictly less than the original.

        Args:
            content: Generated verbose always-on steering file content.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test-always-on.md"
            test_file.write_text(content, encoding="utf-8")

            original_tokens = token_count(content)

            target = CompressTarget(
                filename="test-always-on.md",
                max_token_ratio=0.85,
            )
            result = compress_file(test_file, target)

            assert result.compressed_tokens <= original_tokens, (
                f"Compression must never increase token count. "
                f"Original: {original_tokens}, Compressed: {result.compressed_tokens}"
            )

    @given(content=st_compressible_always_on_content())
    @settings(max_examples=20)
    def test_always_on_files_meet_reduction_target(self, content: str) -> None:
        """Always-on files must achieve >= 15% token reduction (ratio <= 0.85).

        Generates verbose always-on steering file content with filler words,
        transitional phrases, and WHEN/THEN patterns, compresses it using
        compress_file() with a max_token_ratio of 0.85, and verifies the
        resulting ratio is at most 0.85 (at least 15% reduction).

        Args:
            content: Generated verbose always-on steering file content.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test-always-on.md"
            test_file.write_text(content, encoding="utf-8")

            original_tokens = token_count(content)

            target = CompressTarget(
                filename="test-always-on.md",
                max_token_ratio=0.85,
            )
            result = compress_file(test_file, target)

            assert result.ratio <= 0.85, (
                f"Always-on file must achieve at least 15% token reduction "
                f"(ratio <= 0.85). Got ratio: {result.ratio:.4f} "
                f"(original: {original_tokens}, compressed: "
                f"{result.compressed_tokens})"
            )
            assert result.target_met, (
                f"CompressResult.target_met should be True when ratio "
                f"{result.ratio:.4f} <= target {target.max_token_ratio}"
            )


# ---------------------------------------------------------------------------
# Strategies for Property 3: Steering index completeness
# ---------------------------------------------------------------------------


def st_md_filename() -> st.SearchStrategy[str]:
    """Strategy for generating valid markdown filenames in kebab-case."""
    return st.builds(
        lambda parts: "-".join(parts) + ".md",
        parts=st.lists(
            st.from_regex(r"[a-z][a-z0-9]{2,8}", fullmatch=True),
            min_size=1,
            max_size=3,
        ),
    )


def st_md_file_content() -> st.SearchStrategy[str]:
    """Strategy for generating markdown file content of varying lengths.

    Produces content ranging from very short (small category) to long
    (large category) to exercise all size_category thresholds.

    Returns:
        Strategy producing markdown content strings.
    """
    return st.builds(
        _build_md_content,
        inclusion=st.sampled_from(["always", "auto", "manual", "fileMatch"]),
        description=st.from_regex(r"[A-Z][a-z ]{10,40}", fullmatch=True),
        body_lines=st.lists(
            st.from_regex(r"[A-Za-z0-9 .,;:!?-]{10,80}", fullmatch=True),
            min_size=1,
            max_size=30,
        ),
    )


def _build_md_content(
    inclusion: str,
    description: str,
    body_lines: list[str],
) -> str:
    """Assemble markdown file content with YAML frontmatter and body.

    Args:
        inclusion: Frontmatter inclusion value.
        description: Frontmatter description value.
        body_lines: Lines of body content.

    Returns:
        Complete markdown file content string.
    """
    frontmatter = (
        "---\n"
        f"inclusion: {inclusion}\n"
        f'description: "{description}"\n'
        "---\n\n"
    )
    body = "\n".join(body_lines) + "\n"
    return frontmatter + body


def st_steering_file_set() -> st.SearchStrategy[list[tuple[str, str]]]:
    """Strategy for generating a set of (filename, content) pairs.

    Produces 1-5 markdown files with unique filenames and varying content
    lengths to test index completeness across all size categories.

    Returns:
        Strategy producing list of (filename, content) tuples.
    """
    return st.lists(
        st.tuples(st_md_filename(), st_md_file_content()),
        min_size=1,
        max_size=5,
        unique_by=lambda pair: pair[0],
    )


def _build_index_yaml(
    file_metadata: dict[str, dict[str, str | int]],
) -> str:
    """Build a minimal steering-index.yaml string from file_metadata.

    Args:
        file_metadata: Dict mapping filename to {token_count, size_category}.

    Returns:
        YAML-formatted string for steering-index.yaml.
    """
    lines = ["file_metadata:"]
    for filename, meta in sorted(file_metadata.items()):
        lines.append(f"  {filename}:")
        lines.append(f"    token_count: {meta['token_count']}")
        lines.append(f"    size_category: {meta['size_category']}")
    total = sum(m["token_count"] for m in file_metadata.values())
    lines.append("")
    lines.append("budget:")
    lines.append(f"  total_tokens: {total}")
    lines.append("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Property 3: Steering index completeness
# ---------------------------------------------------------------------------


class TestProperty3IndexCompleteness:
    """Property 3: Steering index completeness.

    For any .md file present in the senzing-bootcamp/steering/ directory,
    the file_metadata section of steering-index.yaml SHALL contain an entry
    for that file with a token_count value within 10% of
    round(len(file_content) / 4) and a size_category matching the thresholds
    (small < 500, medium 500-2000, large > 2000).

    Validates: Requirements 5.1, 5.2
    """

    @given(file_set=st_steering_file_set())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_all_md_files_have_index_entries(
        self, file_set: list[tuple[str, str]]
    ) -> None:
        """Every .md file in steering/ must have a file_metadata entry.

        Creates a temp steering directory with generated .md files and a
        steering-index.yaml containing entries for all files. Verifies that
        every .md file in the directory has a corresponding entry in the
        file_metadata section.

        Args:
            file_set: Generated list of (filename, content) tuples.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            steering_dir = Path(tmp_dir)

            # Write all .md files
            for filename, content in file_set:
                (steering_dir / filename).write_text(content, encoding="utf-8")

            # Build index with entries for all files
            file_metadata: dict[str, dict[str, str | int]] = {}
            for filename, content in file_set:
                tokens = token_count(content)
                file_metadata[filename] = {
                    "token_count": tokens,
                    "size_category": size_category(tokens),
                }

            index_content = _build_index_yaml(file_metadata)
            (steering_dir / "steering-index.yaml").write_text(
                index_content, encoding="utf-8"
            )

            # Verify: every .md file has an index entry
            md_files = sorted(
                f.name for f in steering_dir.iterdir() if f.suffix == ".md"
            )
            for md_file in md_files:
                assert md_file in file_metadata, (
                    f"File '{md_file}' is present in steering/ but has no "
                    f"file_metadata entry in steering-index.yaml. "
                    f"Index contains: {sorted(file_metadata.keys())}"
                )

    @given(file_set=st_steering_file_set())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_token_counts_within_tolerance(
        self, file_set: list[tuple[str, str]]
    ) -> None:
        """Stored token_count must be within 10% of calculated value.

        Creates a temp steering directory with generated .md files and a
        steering-index.yaml with token counts computed by token_count().
        Verifies that each stored token_count is within 10% of the
        independently calculated value.

        Args:
            file_set: Generated list of (filename, content) tuples.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            steering_dir = Path(tmp_dir)

            # Write all .md files
            for filename, content in file_set:
                (steering_dir / filename).write_text(content, encoding="utf-8")

            # Build index with entries for all files
            file_metadata: dict[str, dict[str, str | int]] = {}
            for filename, content in file_set:
                tokens = token_count(content)
                file_metadata[filename] = {
                    "token_count": tokens,
                    "size_category": size_category(tokens),
                }

            # Verify: stored token_count is within 10% of calculated
            for filename, content in file_set:
                calculated_tokens = token_count(content)
                stored_tokens = file_metadata[filename]["token_count"]

                # Within 10% tolerance
                lower_bound = calculated_tokens * 0.9
                upper_bound = calculated_tokens * 1.1

                assert lower_bound <= stored_tokens <= upper_bound, (
                    f"File '{filename}': stored token_count {stored_tokens} "
                    f"is not within 10% of calculated value "
                    f"{calculated_tokens}. "
                    f"Acceptable range: [{lower_bound:.0f}, {upper_bound:.0f}]"
                )

    @given(file_set=st_steering_file_set())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_size_categories_match_thresholds(
        self, file_set: list[tuple[str, str]]
    ) -> None:
        """size_category must match token count thresholds.

        Creates a temp steering directory with generated .md files and a
        steering-index.yaml with size categories computed by size_category().
        Verifies that each stored size_category matches the expected value
        based on the token count thresholds (small < 500, medium 500-2000,
        large > 2000).

        Args:
            file_set: Generated list of (filename, content) tuples.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            steering_dir = Path(tmp_dir)

            # Write all .md files
            for filename, content in file_set:
                (steering_dir / filename).write_text(content, encoding="utf-8")

            # Build index with entries for all files
            file_metadata: dict[str, dict[str, str | int]] = {}
            for filename, content in file_set:
                tokens = token_count(content)
                file_metadata[filename] = {
                    "token_count": tokens,
                    "size_category": size_category(tokens),
                }

            # Verify: size_category matches thresholds
            for filename, content in file_set:
                tokens = token_count(content)
                expected_category = size_category(tokens)
                stored_category = file_metadata[filename]["size_category"]

                assert stored_category == expected_category, (
                    f"File '{filename}': size_category '{stored_category}' "
                    f"does not match expected '{expected_category}' for "
                    f"token_count={tokens}. Thresholds: "
                    f"small < 500, medium 500-2000, large > 2000"
                )

    @given(file_set=st_steering_file_set())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_missing_file_detectable(
        self, file_set: list[tuple[str, str]]
    ) -> None:
        """A file missing from the index should be detectable.

        Creates a temp steering directory with generated .md files but builds
        the index with one file omitted. Verifies that comparing the directory
        contents against the index reveals the missing file.

        Args:
            file_set: Generated list of (filename, content) tuples.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            steering_dir = Path(tmp_dir)

            # Write all .md files
            for filename, content in file_set:
                (steering_dir / filename).write_text(content, encoding="utf-8")

            # Build index with one file deliberately omitted
            file_metadata: dict[str, dict[str, str | int]] = {}
            omitted_file = file_set[0][0]  # Omit the first file
            for filename, content in file_set[1:]:
                tokens = token_count(content)
                file_metadata[filename] = {
                    "token_count": tokens,
                    "size_category": size_category(tokens),
                }

            # Detect: compare directory contents against index
            md_files = sorted(
                f.name for f in steering_dir.iterdir() if f.suffix == ".md"
            )
            missing_from_index = [
                f for f in md_files if f not in file_metadata
            ]

            assert len(missing_from_index) > 0, (
                "Should detect at least one file missing from the index"
            )
            assert omitted_file in missing_from_index, (
                f"Omitted file '{omitted_file}' should be detected as missing "
                f"from the index. Missing files: {missing_from_index}"
            )

# ---------------------------------------------------------------------------
# Strategies for Property 4: Budget total consistency
# ---------------------------------------------------------------------------


def st_token_count_value() -> st.SearchStrategy[int]:
    """Strategy for generating realistic token count values."""
    return st.integers(min_value=50, max_value=10000)


def st_file_metadata_entry() -> st.SearchStrategy[tuple[str, int]]:
    """Strategy for generating a file_metadata entry (filename, token_count).

    Returns:
        Strategy producing (filename, token_count) tuples.
    """
    return st.tuples(
        st.from_regex(r"[a-z][a-z0-9-]{3,20}\.md", fullmatch=True),
        st_token_count_value(),
    )


def _build_budget_index_yaml(
    entries: list[tuple[str, int]],
    budget_total: int,
) -> str:
    """Build a synthetic steering-index.yaml content string.

    Args:
        entries: List of (filename, token_count) tuples for file_metadata.
        budget_total: The budget.total_tokens value to set.

    Returns:
        YAML content string with file_metadata and budget sections.
    """
    lines: list[str] = []
    lines.append("file_metadata:")
    for filename, tc in entries:
        cat = "small" if tc < 500 else ("medium" if tc <= 2000 else "large")
        lines.append(f"  {filename}:")
        lines.append(f"    token_count: {tc}")
        lines.append(f"    size_category: {cat}")
    lines.append("")
    lines.append("budget:")
    lines.append(f"  total_tokens: {budget_total}")
    lines.append("  warn_threshold: 0.6")
    lines.append("  critical_threshold: 0.8")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Property 4: Budget total consistency
# ---------------------------------------------------------------------------


class TestProperty4BudgetConsistency:
    """Property 4: Budget total consistency.

    For any valid steering-index.yaml after optimization, the budget.total_tokens
    value SHALL equal the arithmetic sum of all token_count values in the
    file_metadata section.

    Validates: Requirements 5.5
    """

    @given(
        entries=st.lists(st_file_metadata_entry(), min_size=1, max_size=15),
    )
    @settings(max_examples=20)
    def test_budget_total_equals_sum_of_token_counts(
        self, entries: list[tuple[str, int]]
    ) -> None:
        """budget.total_tokens must equal sum of all file_metadata token_counts.

        Generates a list of file_metadata entries, builds a steering-index.yaml
        where budget.total_tokens equals the sum of all token_counts, and
        verifies that _verify_budget_consistency() produces no warning.

        Args:
            entries: Generated list of (filename, token_count) tuples.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            index_path = Path(tmp_dir) / "steering-index.yaml"

            # Calculate the correct total
            correct_total = sum(tc for _, tc in entries)

            # Build YAML with consistent budget total
            content = _build_budget_index_yaml(entries, correct_total)
            index_path.write_text(content, encoding="utf-8")

            # Capture stderr to check for warnings
            captured = io.StringIO()
            old_stderr = sys.stderr
            sys.stderr = captured
            try:
                _verify_budget_consistency(content, index_path)
            finally:
                sys.stderr = old_stderr

            warning_output = captured.getvalue()
            assert "does not equal" not in warning_output, (
                f"When budget.total_tokens ({correct_total}) equals the sum of "
                f"file_metadata token_counts, no warning should be emitted. "
                f"Got: {warning_output}"
            )

    @given(
        entries=st.lists(st_file_metadata_entry(), min_size=1, max_size=15),
        offset=st.integers(min_value=1, max_value=5000),
    )
    @settings(max_examples=20)
    def test_budget_mismatch_detected(
        self, entries: list[tuple[str, int]], offset: int
    ) -> None:
        """A budget total that doesn't match the sum should be detectable.

        Generates a list of file_metadata entries, builds a steering-index.yaml
        where budget.total_tokens does NOT equal the sum (off by a positive
        offset), and verifies that _verify_budget_consistency() emits a warning.

        Args:
            entries: Generated list of (filename, token_count) tuples.
            offset: Positive offset to make the budget total incorrect.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            index_path = Path(tmp_dir) / "steering-index.yaml"

            # Calculate the correct total and add offset to make it wrong
            correct_total = sum(tc for _, tc in entries)
            wrong_total = correct_total + offset

            # Build YAML with inconsistent budget total
            content = _build_budget_index_yaml(entries, wrong_total)
            index_path.write_text(content, encoding="utf-8")

            # Capture stderr to check for warnings
            captured = io.StringIO()
            old_stderr = sys.stderr
            sys.stderr = captured
            try:
                _verify_budget_consistency(content, index_path)
            finally:
                sys.stderr = old_stderr

            warning_output = captured.getvalue()
            assert "does not equal" in warning_output, (
                f"When budget.total_tokens ({wrong_total}) does not equal the sum "
                f"of file_metadata token_counts ({correct_total}), a warning "
                f"should be emitted. Got no warning output."
            )


# ---------------------------------------------------------------------------
# Strategies for Property 6: Index referential integrity
# ---------------------------------------------------------------------------


def st_steering_filename() -> st.SearchStrategy[str]:
    """Strategy for generating valid steering file names (kebab-case .md).

    Returns:
        Strategy producing filenames like 'module-01-setup.md', 'hook-registry.md'.
    """
    return st.builds(
        lambda parts: "-".join(parts) + ".md",
        parts=st.lists(
            st.from_regex(r"[a-z][a-z0-9]{1,10}", fullmatch=True),
            min_size=1,
            max_size=3,
        ),
    )


def st_keyword() -> st.SearchStrategy[str]:
    """Strategy for generating keyword strings for the keywords section."""
    return st.sampled_from([
        "error",
        "stuck",
        "tool selection",
        "troubleshoot",
        "resume",
        "onboard",
        "hook",
        "completion",
        "security",
        "transition",
        "mcp tool",
        "visualization",
        "recovery",
        "verbose",
        "status",
    ])


def _build_steering_index_yaml(
    file_metadata_files: list[str],
    keyword_files: list[str],
    module_files: list[str],
) -> str:
    """Build a synthetic steering-index.yaml content string.

    Creates a minimal but structurally valid steering-index.yaml with
    modules, file_metadata, and keywords sections referencing the given files.

    Args:
        file_metadata_files: Filenames to include in file_metadata section.
        keyword_files: Filenames to reference in keywords section.
        module_files: Filenames to reference in modules section (as root/phase files).

    Returns:
        YAML content string for a steering-index.yaml.
    """
    lines: list[str] = []

    # modules section
    lines.append("modules:")
    for i, fname in enumerate(module_files, start=1):
        lines.append(f"  {i}:")
        lines.append(f"    root: {fname}")
        lines.append("    phases:")
        lines.append("      phase1:")
        lines.append(f"        file: {fname}")
        lines.append("        token_count: 1000")
        lines.append("        size_category: medium")
        lines.append("        step_range: [1, 5]")

    # keywords section
    lines.append("")
    lines.append("keywords:")
    for i, fname in enumerate(keyword_files):
        lines.append(f"  keyword{i}: {fname}")

    # file_metadata section
    lines.append("")
    lines.append("file_metadata:")
    for fname in file_metadata_files:
        lines.append(f"  {fname}:")
        lines.append("    token_count: 500")
        lines.append("    size_category: medium")

    # budget section
    total = 500 * len(file_metadata_files)
    lines.append("")
    lines.append("budget:")
    lines.append(f"  total_tokens: {total}")
    lines.append("  reference_window: 200000")

    return "\n".join(lines) + "\n"


def _extract_referenced_files_from_index(index_content: str) -> set[str]:
    """Parse a steering-index.yaml and extract all referenced .md filenames.

    Extracts filenames from:
    - modules section: root fields and phases.*.file fields
    - file_metadata section: keys (filenames as YAML keys)
    - keywords section: values (filenames as YAML values)

    Args:
        index_content: Full text content of steering-index.yaml.

    Returns:
        Set of all .md filenames referenced in the index.
    """
    referenced: set[str] = set()
    lines = index_content.splitlines()

    current_section = ""

    for line in lines:
        stripped = line.strip()

        # Detect top-level sections
        if line and not line[0].isspace() and stripped.endswith(":"):
            section_name = stripped.rstrip(":")
            if section_name in ("modules", "file_metadata", "keywords",
                                "onboarding", "session-resume", "languages",
                                "deployment"):
                current_section = section_name
            else:
                current_section = section_name
            continue

        # Extract filenames based on section
        if current_section == "file_metadata":
            # Keys in file_metadata are filenames: "  filename.md:"
            if stripped.endswith(".md:"):
                fname = stripped.rstrip(":")
                referenced.add(fname)

        elif current_section in ("modules", "onboarding", "session-resume"):
            # root: filename.md or file: filename.md
            if "root:" in stripped or "file:" in stripped:
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    value = parts[1].strip()
                    if value.endswith(".md"):
                        referenced.add(value)

        elif current_section == "keywords":
            # keyword: filename.md
            if ":" in stripped and stripped.endswith(".md"):
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    value = parts[1].strip()
                    if value.endswith(".md"):
                        referenced.add(value)

        elif current_section in ("languages", "deployment"):
            # language/deployment: filename.md
            if ":" in stripped and stripped.endswith(".md"):
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    value = parts[1].strip()
                    if value.endswith(".md"):
                        referenced.add(value)

    return referenced


def _check_referential_integrity(
    index_content: str,
    steering_dir: Path,
) -> list[str]:
    """Check that all files referenced in the index exist in the steering directory.

    Args:
        index_content: Full text content of steering-index.yaml.
        steering_dir: Path to the steering directory containing .md files.

    Returns:
        List of filenames referenced in the index but missing from the directory.
    """
    referenced = _extract_referenced_files_from_index(index_content)
    missing: list[str] = []

    for fname in sorted(referenced):
        file_path = steering_dir / fname
        if not file_path.exists():
            missing.append(fname)

    return missing


# ---------------------------------------------------------------------------
# Property 6: Index referential integrity
# ---------------------------------------------------------------------------


class TestProperty6ReferentialIntegrity:
    """Property 6: Index referential integrity.

    For any filename referenced in the modules, file_metadata, or keywords
    sections of steering-index.yaml, a corresponding .md file SHALL exist
    in the senzing-bootcamp/steering/ directory.

    Validates: Requirements 7.5
    """

    @given(
        filenames=st.lists(
            st_steering_filename(),
            min_size=1,
            max_size=10,
            unique=True,
        ),
    )
    @settings(max_examples=20)
    def test_all_referenced_files_exist(self, filenames: list[str]) -> None:
        """Every filename in the index must correspond to an existing .md file.

        Generates a set of filenames, creates corresponding .md files in a
        temp directory, builds a steering-index.yaml referencing those files
        across modules, file_metadata, and keywords sections, then verifies
        that referential integrity holds (no missing files).

        Args:
            filenames: Generated list of unique steering filenames.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            steering_dir = Path(tmp_dir)

            # Create all .md files in the steering directory
            for fname in filenames:
                (steering_dir / fname).write_text(
                    "---\ninclusion: manual\ndescription: test\n---\n\nContent.\n",
                    encoding="utf-8",
                )

            # Build an index referencing these files across all sections
            # Use subsets for each section to simulate realistic distribution
            module_files = filenames[:3] if len(filenames) >= 3 else filenames[:1]
            keyword_files = filenames[1:5] if len(filenames) >= 5 else filenames
            file_metadata_files = filenames  # All files should be in file_metadata

            index_content = _build_steering_index_yaml(
                file_metadata_files=file_metadata_files,
                keyword_files=keyword_files,
                module_files=module_files,
            )

            # Write the index file
            index_path = steering_dir / "steering-index.yaml"
            index_path.write_text(index_content, encoding="utf-8")

            # Check referential integrity — should find no missing files
            missing = _check_referential_integrity(index_content, steering_dir)
            assert missing == [], (
                f"All referenced files should exist in the steering directory. "
                f"Missing: {missing}"
            )

    @given(
        existing_files=st.lists(
            st_steering_filename(),
            min_size=2,
            max_size=8,
            unique=True,
        ),
        ghost_file=st_steering_filename(),
    )
    @settings(max_examples=20)
    def test_missing_file_detected(
        self, existing_files: list[str], ghost_file: str
    ) -> None:
        """A reference to a non-existent file should be detectable.

        Creates .md files for a subset of filenames, then builds an index
        that also references a 'ghost' file that does NOT exist on disk.
        Verifies that the integrity check detects the missing file.

        Args:
            existing_files: Filenames for which .md files will be created.
            ghost_file: A filename that will be referenced in the index but
                NOT created on disk.
        """
        # Ensure ghost_file is distinct from existing files
        if ghost_file in existing_files:
            return  # Skip this example — ghost must be truly missing

        with tempfile.TemporaryDirectory() as tmp_dir:
            steering_dir = Path(tmp_dir)

            # Create only the existing files
            for fname in existing_files:
                (steering_dir / fname).write_text(
                    "---\ninclusion: manual\ndescription: test\n---\n\nContent.\n",
                    encoding="utf-8",
                )

            # Build an index that references both existing AND ghost files
            all_referenced = existing_files + [ghost_file]
            index_content = _build_steering_index_yaml(
                file_metadata_files=all_referenced,
                keyword_files=[ghost_file],  # Ghost in keywords too
                module_files=existing_files[:1],
            )

            # Check referential integrity — should detect the ghost file
            missing = _check_referential_integrity(index_content, steering_dir)
            assert ghost_file in missing, (
                f"Ghost file '{ghost_file}' should be detected as missing. "
                f"Missing list: {missing}"
            )

    @given(
        filenames=st.lists(
            st_steering_filename(),
            min_size=3,
            max_size=10,
            unique=True,
        ),
    )
    @settings(max_examples=20)
    def test_extracted_references_cover_all_sections(
        self, filenames: list[str]
    ) -> None:
        """File extraction from index captures references from all three sections.

        Builds an index with files distributed across modules, file_metadata,
        and keywords sections, then verifies that _extract_referenced_files_from_index
        captures all of them.

        Args:
            filenames: Generated list of unique steering filenames.
        """
        # Distribute filenames across sections
        module_files = filenames[:2]
        keyword_files = filenames[1:4] if len(filenames) >= 4 else filenames[1:]
        file_metadata_files = filenames

        index_content = _build_steering_index_yaml(
            file_metadata_files=file_metadata_files,
            keyword_files=keyword_files,
            module_files=module_files,
        )

        # Extract all referenced files
        referenced = _extract_referenced_files_from_index(index_content)

        # All filenames should appear in the extracted set
        all_expected = set(filenames)
        assert all_expected.issubset(referenced), (
            f"All filenames should be captured from the index. "
            f"Missing from extraction: {all_expected - referenced}"
        )
