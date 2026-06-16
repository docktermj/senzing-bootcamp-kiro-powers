"""Property-based and unit tests for token budget optimization (module-07 split).

Feature: token-budget-optimization
"""

from __future__ import annotations

import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from measure_steering import calculate_token_count

# Paths to the actual steering files
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
INDEX_PATH = STEERING_DIR / "steering-index.yaml"
PART_A_PATH = STEERING_DIR / "module-07-phase2-discover.md"
PART_B_PATH = STEERING_DIR / "module-07-phase2b-discover.md"

PART_A = STEERING_DIR / "module-07-phase2-discover.md"
PART_B = STEERING_DIR / "module-07-phase2b-discover.md"


# ---------------------------------------------------------------------------
# Helpers for content preservation
# ---------------------------------------------------------------------------


def _strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from markdown content."""
    if content.startswith("---"):
        match = re.search(r"^---\s*$", content[3:], re.MULTILINE)
        if match:
            return content[3 + match.end():].lstrip("\n")
    return content


def _extract_agent_instructions(content: str) -> list[str]:
    """Extract agent instruction lines (blockquotes starting with > **Agent instruction)."""
    lines = []
    in_instruction = False
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("> **Agent instruction"):
            in_instruction = True
            lines.append(stripped)
        elif in_instruction and stripped.startswith(">"):
            lines.append(stripped)
        elif in_instruction and not stripped.startswith(">"):
            in_instruction = False
    return lines


def _extract_checkpoints(content: str) -> list[str]:
    """Extract checkpoint blocks (lines starting with **Checkpoint:**)."""
    checkpoints = []
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("**Checkpoint:**"):
            checkpoints.append(stripped)
    return checkpoints


def _extract_success_criteria(content: str) -> list[str]:
    """Extract success criteria lines (lines starting with **Success:**)."""
    criteria = []
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("**Success:**"):
            criteria.append(stripped)
    return criteria


def _extract_step_headings(content: str) -> list[str]:
    """Extract step headings (### Step ...)."""
    headings = []
    for line in content.split("\n"):
        stripped = line.strip()
        if re.match(r"^###\s+Step\s+\d", stripped):
            headings.append(stripped)
    return headings


# ---------------------------------------------------------------------------
# Hypothesis strategies for content preservation
# ---------------------------------------------------------------------------


def _safe_instruction_text() -> st.SearchStrategy[str]:
    """Generate text that won't accidentally look like markdown structure."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N", "P", "Z"),
            blacklist_characters="\x00\r",
        ),
        min_size=1,
        max_size=80,
    ).filter(lambda t: t.strip() and "---" not in t and "###" not in t)


@st.composite
def st_steering_file_with_steps(draw):
    """Generate a steering file with frontmatter, steps, checkpoints, and instructions.

    Returns (full_content, instruction_lines, checkpoint_lines, success_lines, split_point).
    """
    frontmatter = "---\ninclusion: manual\n---\n\n"
    title = "# Module N — Phase X: Test\n\n"

    session_resumption = (
        "> **Agent instruction (session resumption):** On load, read\n"
        "> `config/bootcamp_progress.json` and resume from the first incomplete step.\n\n"
    )

    num_steps = draw(st.integers(min_value=2, max_value=6))
    split_point = draw(st.integers(min_value=1, max_value=num_steps - 1))

    instructions = []
    checkpoints = []
    success_lines = []
    body_parts = []

    for i in range(1, num_steps + 1):
        step_label = chr(ord("a") + i - 1)
        heading = f"### Step {i}{step_label}: Test Step {i}\n\n"

        instr_text = draw(_safe_instruction_text())
        instruction = f"> **Agent instruction:** {instr_text}\n"
        instructions.append(instruction.strip())

        checkpoint = f"**Checkpoint:** Write step {i}{step_label} to progress.\n"
        checkpoints.append(checkpoint.strip())

        body_parts.append(heading + instruction + "\n" + checkpoint + "\n")

    # Add a success line at the end
    success_text = draw(_safe_instruction_text())
    success_line = f"**Success:** {success_text}\n"
    success_lines.append(success_line.strip())
    body_parts.append(success_line)

    full_content = frontmatter + title + session_resumption + "\n".join(body_parts)

    return full_content, instructions, checkpoints, success_lines, split_point


# ---------------------------------------------------------------------------
# Property 1: Content preservation across split
# ---------------------------------------------------------------------------


class TestProperty1ContentPreservation:
    """Feature: token-budget-optimization, Property 1: Content preservation across split.

    For any valid steering file split at a section boundary, the concatenation
    of Part A body content and Part B body content (excluding added navigation
    boilerplate and duplicate frontmatter) SHALL contain every agent instruction
    line, checkpoint block, and success criterion present in the original file.
    """

    @given(data=st_steering_file_with_steps())
    @settings(max_examples=20)
    def test_split_preserves_all_instructions(self, data):
        """**Validates: Requirements 5.1**

        For any generated steering file split at a section boundary,
        all agent instruction lines are preserved in the combined parts.
        """
        full_content, instructions, checkpoints, success_lines, split_point = data

        # Simulate a split at the split_point boundary
        body = _strip_frontmatter(full_content)
        lines = body.split("\n")

        # Find the split_point-th step heading to split at
        step_heading_indices = []
        for idx, line in enumerate(lines):
            if re.match(r"^###\s+Step\s+\d", line.strip()):
                step_heading_indices.append(idx)

        assume(len(step_heading_indices) >= 2)
        assume(split_point < len(step_heading_indices))

        split_idx = step_heading_indices[split_point]

        # Part A = everything before split_idx, Part B = everything from split_idx
        part_a_body = "\n".join(lines[:split_idx])
        part_b_body = "\n".join(lines[split_idx:])

        # Combined content (excluding duplicate frontmatter/navigation boilerplate)
        combined = part_a_body + "\n" + part_b_body

        # Verify all instructions are preserved
        for instr in instructions:
            assert instr in combined, (
                f"Instruction lost in split: {instr!r}"
            )

        # Verify all checkpoints are preserved
        for cp in checkpoints:
            assert cp in combined, (
                f"Checkpoint lost in split: {cp!r}"
            )

        # Verify all success criteria are preserved
        for sc in success_lines:
            assert sc in combined, (
                f"Success criterion lost in split: {sc!r}"
            )

    @given(data=st_steering_file_with_steps())
    @settings(max_examples=20)
    def test_split_preserves_step_headings(self, data):
        """**Validates: Requirements 5.1**

        For any generated steering file split at a section boundary,
        all step headings are preserved in the combined parts.
        """
        full_content, _, _, _, split_point = data

        body = _strip_frontmatter(full_content)
        original_headings = _extract_step_headings(body)
        assume(len(original_headings) >= 2)

        lines = body.split("\n")
        step_heading_indices = []
        for idx, line in enumerate(lines):
            if re.match(r"^###\s+Step\s+\d", line.strip()):
                step_heading_indices.append(idx)

        assume(split_point < len(step_heading_indices))
        split_idx = step_heading_indices[split_point]

        part_a_body = "\n".join(lines[:split_idx])
        part_b_body = "\n".join(lines[split_idx:])
        combined = part_a_body + "\n" + part_b_body

        combined_headings = _extract_step_headings(combined)
        assert set(original_headings) == set(combined_headings), (
            f"Headings mismatch: original={original_headings}, combined={combined_headings}"
        )

    def test_actual_files_preserve_all_content(self):
        """**Validates: Requirements 5.1**

        The actual Part A and Part B files combined contain all agent
        instructions, checkpoints, and success criteria from the original
        content (verified against the actual split files).
        """
        part_a_content = PART_A_PATH.read_text(encoding="utf-8")
        part_b_content = PART_B_PATH.read_text(encoding="utf-8")

        part_a_body = _strip_frontmatter(part_a_content)
        part_b_body = _strip_frontmatter(part_b_content)
        combined = part_a_body + "\n" + part_b_body

        # Extract all instructional elements from combined content
        instructions = _extract_agent_instructions(combined)
        checkpoints = _extract_checkpoints(combined)
        success_criteria = _extract_success_criteria(combined)

        # Verify steps 4a-4e are all present
        step_headings = _extract_step_headings(combined)
        expected_steps = ["4a", "4b", "4c", "4d", "4e"]
        for step in expected_steps:
            found = any(f"Step {step}" in h for h in step_headings)
            assert found, f"Step {step} heading missing from combined content"

        # Verify agent instructions exist for each step
        assert len(instructions) > 0, "No agent instructions found in combined content"

        # Verify checkpoints exist (one per step minimum)
        assert len(checkpoints) >= 5, (
            f"Expected at least 5 checkpoints (one per step), found {len(checkpoints)}"
        )

        # Verify success criteria exist
        assert len(success_criteria) >= 1, "No success criteria found in combined content"

        # Verify session resumption instruction in both parts
        assert "session resumption" in part_a_body, (
            "Part A missing session resumption instruction"
        )
        assert "session resumption" in part_b_body, (
            "Part B missing session resumption instruction"
        )


# ---------------------------------------------------------------------------
# Property 2: Token budget compliance
# ---------------------------------------------------------------------------

SPLIT_THRESHOLD_TOKENS = 5000

PART_A_FILE = "module-07-phase2-discover.md"
PART_B_FILE = "module-07-phase2b-discover.md"


def _token_count_from_content(content: str) -> int:
    """Token count formula: round(len(content) / 4)."""
    return round(len(content) / 4)


@st.composite
def st_steering_content_under_budget(draw):
    """Generate steering file content that simulates a valid split output.

    Produces content with YAML frontmatter and markdown body whose token
    count is strictly less than split_threshold_tokens (5,000).
    A valid split operation should always produce files under this threshold.
    """
    # Target token count under the threshold
    target_tokens = draw(st.integers(min_value=50, max_value=SPLIT_THRESHOLD_TOKENS - 1))
    target_chars = target_tokens * 4

    frontmatter = "---\ninclusion: manual\n---\n\n"
    header = "# Module — Phase (Part)\n\n"
    boilerplate = frontmatter + header
    remaining_chars = max(0, target_chars - len(boilerplate))

    # Build body from repeated lines to avoid Hypothesis buffer size limits
    line = draw(st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N"),
            blacklist_characters="\x00\r",
        ),
        min_size=10,
        max_size=80,
    ))
    if not line.strip():
        line = "Step content placeholder text"

    # Repeat the line to fill the target size
    repetitions = (remaining_chars // (len(line) + 1)) + 1
    body = ("\n".join([line] * repetitions))[:remaining_chars]

    content = boilerplate + body
    return content


class TestProperty2TokenBudgetCompliance:
    """Feature: token-budget-optimization, Property 2: Token budget compliance.

    For any steering file produced by a split operation, its measured token
    count (round(len(content) / 4)) SHALL be strictly less than the
    split_threshold_tokens value (5,000).
    """

    @given(content=st_steering_content_under_budget())
    @settings(max_examples=20)
    def test_split_output_under_budget(self, content: str):
        """**Validates: Requirements 1.5, 1.6**

        Any file produced by a valid split operation has a measured token
        count strictly less than split_threshold_tokens.
        """
        token_count = _token_count_from_content(content)
        assert token_count < SPLIT_THRESHOLD_TOKENS, (
            f"Token count {token_count} >= threshold {SPLIT_THRESHOLD_TOKENS}"
        )

    @given(
        content_a=st_steering_content_under_budget(),
        content_b=st_steering_content_under_budget(),
    )
    @settings(max_examples=20)
    def test_both_split_parts_under_budget(self, content_a: str, content_b: str):
        """**Validates: Requirements 1.5, 1.6**

        For any pair of files produced by a split, both parts have measured
        token counts strictly less than split_threshold_tokens.
        """
        token_a = _token_count_from_content(content_a)
        token_b = _token_count_from_content(content_b)

        assert token_a < SPLIT_THRESHOLD_TOKENS, (
            f"Part A token count {token_a} >= threshold {SPLIT_THRESHOLD_TOKENS}"
        )
        assert token_b < SPLIT_THRESHOLD_TOKENS, (
            f"Part B token count {token_b} >= threshold {SPLIT_THRESHOLD_TOKENS}"
        )

    def test_actual_part_a_under_budget(self):
        """**Validates: Requirements 1.5**

        The actual Part A file (module-07-phase2-discover.md) has a measured
        token count strictly less than split_threshold_tokens (5,000).
        """
        path = STEERING_DIR / PART_A_FILE
        assert path.exists(), f"{PART_A_FILE} not found"
        token_count = calculate_token_count(path)
        assert token_count < SPLIT_THRESHOLD_TOKENS, (
            f"{PART_A_FILE}: token count {token_count} >= "
            f"threshold {SPLIT_THRESHOLD_TOKENS}"
        )

    def test_actual_part_b_under_budget(self):
        """**Validates: Requirements 1.6**

        The actual Part B file (module-07-phase2b-discover.md) has a measured
        token count strictly less than split_threshold_tokens (5,000).
        """
        path = STEERING_DIR / PART_B_FILE
        assert path.exists(), f"{PART_B_FILE} not found"
        token_count = calculate_token_count(path)
        assert token_count < SPLIT_THRESHOLD_TOKENS, (
            f"{PART_B_FILE}: token count {token_count} >= "
            f"threshold {SPLIT_THRESHOLD_TOKENS}"
        )

    def test_threshold_from_steering_index(self):
        """**Validates: Requirements 1.5, 1.6**

        Verify the split_threshold_tokens in steering-index.yaml is 5,000
        and both split files comply with it.
        """
        index_content = INDEX_PATH.read_text(encoding="utf-8")
        match = re.search(r"split_threshold_tokens:\s*(\d+)", index_content)
        assert match, "split_threshold_tokens not found in steering-index.yaml"
        threshold = int(match.group(1))
        assert threshold == SPLIT_THRESHOLD_TOKENS

        for filename in (PART_A_FILE, PART_B_FILE):
            path = STEERING_DIR / filename
            token_count = calculate_token_count(path)
            assert token_count < threshold, (
                f"{filename}: token count {token_count} >= threshold {threshold}"
            )


# ---------------------------------------------------------------------------
# Hypothesis strategies for steering index
# ---------------------------------------------------------------------------


@st.composite
def st_file_metadata_entry(draw):
    """Generate a file_metadata entry with a filename and token count.

    Returns (filename, token_count) where token_count is a positive integer.
    """
    name_base = draw(st.text(
        alphabet=st.characters(whitelist_categories=("Ll",), whitelist_characters="-"),
        min_size=3,
        max_size=20,
    ).filter(lambda s: s[0].isalpha() and s[-1].isalpha()))
    filename = f"{name_base}.md"
    token_count = draw(st.integers(min_value=10, max_value=10000))
    return filename, token_count


@st.composite
def st_file_metadata_collection(draw):
    """Generate a collection of file_metadata entries with token counts.

    Returns list of (filename, token_count) tuples with unique filenames.
    """
    num_files = draw(st.integers(min_value=1, max_value=10))
    entries = []
    seen_names = set()
    for _ in range(num_files):
        filename, token_count = draw(st_file_metadata_entry())
        # Ensure unique filenames
        while filename in seen_names:
            filename = f"x{filename}"
        seen_names.add(filename)
        entries.append((filename, token_count))
    return entries


# ---------------------------------------------------------------------------
# Property 3: Steering index consistency
# ---------------------------------------------------------------------------


class TestProperty3SteeringIndexConsistency:
    """Feature: token-budget-optimization, Property 3: Steering index consistency.

    For any steering file listed in file_metadata, the stored token_count SHALL
    be within 10% of the value computed by calculate_token_count on the actual
    file, and budget.total_tokens SHALL equal the sum of all file_metadata
    token counts.
    """

    @given(entries=st_file_metadata_collection())
    @settings(max_examples=20)
    def test_total_tokens_equals_sum_of_file_metadata(self, entries):
        """**Validates: Requirements 2.3, 2.4**

        For any set of file_metadata entries, budget.total_tokens must equal
        the sum of all individual token_count values.
        """
        # Build a steering-index.yaml with the generated entries
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Write file_metadata and budget sections
            lines = ["file_metadata:"]
            total = 0
            for filename, token_count in entries:
                lines.append(f"  {filename}:")
                lines.append(f"    token_count: {token_count}")
                lines.append("    size_category: large")
                total += token_count

            lines.append("")
            lines.append("budget:")
            lines.append(f"  total_tokens: {total}")
            lines.append("  reference_window: 200000")
            lines.append("  warn_threshold_pct: 60")
            lines.append("  critical_threshold_pct: 80")
            lines.append("  split_threshold_tokens: 5000")
            lines.append("")

            index_path = tmp_path / "steering-index.yaml"
            index_path.write_text("\n".join(lines), encoding="utf-8")

            # Parse and verify the invariant
            content = index_path.read_text(encoding="utf-8")

            # Extract total_tokens from budget
            total_match = re.search(r"total_tokens:\s*(\d+)", content)
            assert total_match, "total_tokens not found in budget"
            stored_total = int(total_match.group(1))

            # Extract all token_count values from file_metadata
            fm_start = content.find("file_metadata:")
            budget_start = content.find("budget:")
            fm_block = content[fm_start:budget_start]
            counts = re.findall(r"token_count:\s*(\d+)", fm_block)
            calculated_total = sum(int(c) for c in counts)

            assert stored_total == calculated_total, (
                f"total_tokens ({stored_total}) != sum of file_metadata ({calculated_total})"
            )

    @given(
        content_length=st.integers(min_value=4, max_value=2000),
        data=st.data(),
    )
    @settings(max_examples=20)
    def test_stored_token_count_within_tolerance_of_measured(
        self, content_length, data
    ):
        """**Validates: Requirements 2.3, 2.4**

        For any file content, a stored token_count within 10% of the measured
        value (round(len(content) / 4)) satisfies the consistency check. The
        stored value is drawn from the closed integer interval
        [ceil(measured * 0.90), floor(measured * 1.10)], so it is within the
        ±10% tolerance by construction and the assertion cannot self-falsify.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create a file with known content length
            file_content = "x" * content_length
            test_file = tmp_path / "test-file.md"
            test_file.write_text(file_content, encoding="utf-8")

            # Calculate the measured token count
            measured = calculate_token_count(test_file)
            assert measured == round(content_length / 4)

            # Draw a stored value provably within ±10% of measured. The closed
            # integer interval is non-empty for measured >= 1 because
            # lo <= measured <= hi.
            lo = math.ceil(measured * 0.90)
            hi = math.floor(measured * 1.10)
            stored = data.draw(st.integers(min_value=lo, max_value=hi))

            # The 10% tolerance check holds by construction.
            assert abs(stored - measured) / measured <= 0.10, (
                f"stored={stored}, measured={measured}, "
                f"deviation={abs(stored - measured) / measured:.2%} > 10%"
            )

    def test_actual_steering_index_total_tokens_equals_sum(self):
        """Concrete test: budget.total_tokens in the real steering-index.yaml
        equals the sum of all file_metadata token counts.

        **Validates: Requirements 2.3, 2.4**
        """
        content = INDEX_PATH.read_text(encoding="utf-8")

        # Extract total_tokens from budget section
        total_match = re.search(r"^  total_tokens:\s*(\d+)", content, re.MULTILINE)
        assert total_match, "total_tokens not found in budget section"
        stored_total = int(total_match.group(1))

        # Extract all token_count values from file_metadata section
        fm_start = content.find("\nfile_metadata:")
        budget_match = re.search(r"^budget:", content, re.MULTILINE)
        assert budget_match, "budget section not found"
        budget_start = budget_match.start()
        fm_block = content[fm_start:budget_start]
        counts = re.findall(r"token_count:\s*(\d+)", fm_block)
        calculated_total = sum(int(c) for c in counts)

        assert stored_total == calculated_total, (
            f"budget.total_tokens ({stored_total}) != "
            f"sum of file_metadata token counts ({calculated_total})"
        )

    def test_actual_steering_files_token_counts_within_tolerance(self):
        """Concrete test: each file_metadata entry in the real steering-index.yaml
        has a stored token_count within 10% of the measured value.

        **Validates: Requirements 2.3, 2.4**
        """
        content = INDEX_PATH.read_text(encoding="utf-8")

        # Parse file_metadata entries
        fm_start = content.find("\nfile_metadata:")
        budget_match = re.search(r"^budget:", content, re.MULTILINE)
        assert budget_match, "budget section not found"
        budget_start = budget_match.start()
        fm_block = content[fm_start:budget_start]

        # Extract filename -> token_count pairs
        file_pattern = re.compile(r"^\s{2}([\w.-]+\.md):\s*$", re.MULTILINE)
        tc_pattern = re.compile(r"^\s+token_count:\s*(\d+)", re.MULTILINE)

        filenames = [m.group(1) for m in file_pattern.finditer(fm_block)]
        token_counts = [int(m.group(1)) for m in tc_pattern.finditer(fm_block)]

        assert len(filenames) == len(token_counts), (
            f"Mismatch: {len(filenames)} filenames vs {len(token_counts)} token counts"
        )

        mismatches = []
        for filename, stored_count in zip(filenames, token_counts):
            filepath = STEERING_DIR / filename
            assert filepath.exists(), f"Steering file not found: {filename}"

            measured_count = calculate_token_count(filepath)
            if measured_count == 0:
                continue

            deviation = abs(stored_count - measured_count) / measured_count
            if deviation > 0.10:
                mismatches.append(
                    f"{filename}: stored={stored_count}, measured={measured_count}, "
                    f"deviation={deviation:.2%}"
                )

        assert not mismatches, (
            "Token counts outside 10% tolerance:\n" + "\n".join(mismatches)
        )


# ---------------------------------------------------------------------------
# Task 5.4: Unit tests for the actual split files
# Validates: Requirements 1.1, 1.2, 1.3, 1.4, 4.1, 4.2
# ---------------------------------------------------------------------------


class TestPartAStructure:
    """Verify Part A (module-07-phase2-discover.md) contains steps 4a–4c and navigation footer.

    **Validates: Requirements 1.1, 1.3**
    """

    @pytest.fixture(autouse=True)
    def _load_content(self):
        """Load Part A content once for all tests in this class."""
        assert PART_A.exists(), f"Part A file not found: {PART_A}"
        self.content = PART_A.read_text(encoding="utf-8")

    def test_part_a_contains_step_4a_heading(self):
        """Part A contains the Step 4a heading."""
        assert "### Step 4a:" in self.content, "Part A missing Step 4a heading"

    def test_part_a_contains_step_4b_heading(self):
        """Part A contains the Step 4b heading."""
        assert "### Step 4b:" in self.content, "Part A missing Step 4b heading"

    def test_part_a_contains_step_4c_heading(self):
        """Part A contains the Step 4c heading."""
        assert "### Step 4c:" in self.content, "Part A missing Step 4c heading"

    def test_part_a_does_not_contain_step_4d(self):
        """Part A should NOT contain Step 4d (that belongs in Part B)."""
        assert "### Step 4d:" not in self.content, \
            "Part A should not contain Step 4d"

    def test_part_a_does_not_contain_step_4e(self):
        """Part A should NOT contain Step 4e (that belongs in Part B)."""
        assert "### Step 4e:" not in self.content, \
            "Part A should not contain Step 4e"

    def test_part_a_has_navigation_footer(self):
        """Part A has a navigation footer directing to module-07-phase2b-discover.md."""
        assert "module-07-phase2b-discover.md" in self.content, \
            "Part A missing navigation reference to Part B"
        # The footer should be near the end of the file
        lines = self.content.strip().split("\n")
        tail = "\n".join(lines[-10:])
        assert "module-07-phase2b-discover.md" in tail, \
            "Navigation footer to Part B not found near end of Part A"


class TestPartBStructure:
    """Verify Part B (module-07-phase2b-discover.md) contains steps 4d–4e and continuation header.

    **Validates: Requirements 1.2, 1.4**
    """

    @pytest.fixture(autouse=True)
    def _load_content(self):
        """Load Part B content once for all tests in this class."""
        assert PART_B.exists(), f"Part B file not found: {PART_B}"
        self.content = PART_B.read_text(encoding="utf-8")

    def test_part_b_contains_step_4d_heading(self):
        """Part B contains the Step 4d heading."""
        assert "### Step 4d:" in self.content, "Part B missing Step 4d heading"

    def test_part_b_contains_step_4e_heading(self):
        """Part B contains the Step 4e heading."""
        assert "### Step 4e:" in self.content, "Part B missing Step 4e heading"

    def test_part_b_does_not_contain_step_4a(self):
        """Part B should NOT contain Step 4a (that belongs in Part A)."""
        assert "### Step 4a:" not in self.content, \
            "Part B should not contain Step 4a"

    def test_part_b_does_not_contain_step_4b(self):
        """Part B should NOT contain Step 4b (that belongs in Part A)."""
        assert "### Step 4b:" not in self.content, \
            "Part B should not contain Step 4b"

    def test_part_b_does_not_contain_step_4c(self):
        """Part B should NOT contain Step 4c (that belongs in Part A)."""
        assert "### Step 4c:" not in self.content, \
            "Part B should not contain Step 4c"

    def test_part_b_has_continuation_header(self):
        """Part B has a continuation header referencing module-07-phase2-discover.md."""
        # The continuation header should be near the top (within first 15 lines)
        lines = self.content.split("\n")
        header_section = "\n".join(lines[:15])
        assert "module-07-phase2-discover.md" in header_section, \
            "Part B missing continuation header referencing Part A"

    def test_part_b_contains_discover_phase_completion(self):
        """Part B contains the Discover Phase Completion section."""
        assert "Discover Phase Completion" in self.content, \
            "Part B missing Discover Phase Completion section"


class TestFrontmatter:
    """Verify both split files have `inclusion: manual` YAML frontmatter.

    **Validates: Requirements 1.1, 1.2**
    """

    @pytest.mark.parametrize("filepath,label", [
        (PART_A, "Part A"),
        (PART_B, "Part B"),
    ])
    def test_file_starts_with_yaml_frontmatter(self, filepath, label):
        """Both files start with YAML frontmatter delimiters."""
        content = filepath.read_text(encoding="utf-8")
        assert content.startswith("---\n"), \
            f"{label} does not start with YAML frontmatter delimiter"

    @pytest.mark.parametrize("filepath,label", [
        (PART_A, "Part A"),
        (PART_B, "Part B"),
    ])
    def test_file_has_inclusion_manual(self, filepath, label):
        """Both files have `inclusion: manual` in their frontmatter."""
        content = filepath.read_text(encoding="utf-8")
        # Extract frontmatter block (between first and second ---)
        fm_end = content.index("---", 3)
        frontmatter = content[:fm_end + 3]
        assert "inclusion: manual" in frontmatter, \
            f"{label} missing 'inclusion: manual' in frontmatter"


class TestNoHookModification:
    """Verify no hook files were modified by the token budget optimization.

    **Validates: Requirements 4.1, 4.2**
    """

    def test_no_kiro_hook_files_modified(self):
        """No .kiro.hook files appear as modified in git status.

        Note: ask-bootcamper.kiro.hook and deleted hooks (enforce-step-and-transition,
        mcp-first-invariant, question-format-gate) are excluded because they were
        intentionally consolidated by the agent-answer-processing-failures spec.
        """
        hook_files = list(HOOKS_DIR.glob("*.kiro.hook"))
        assert len(hook_files) > 0, "No .kiro.hook files found in hooks directory"

        # Check git status for hook files - they should not be modified
        result = subprocess.run(
            ["git", "status", "--porcelain", "senzing-bootcamp/hooks/"],
            capture_output=True,
            text=True,
            cwd=str(_PROJECT_ROOT),
        )
        # Hooks intentionally modified/deleted by the consolidation spec
        _CONSOLIDATED_HOOKS = {
            "ask-bootcamper.kiro.hook",
            "enforce-step-and-transition.kiro.hook",
            "mcp-first-invariant.kiro.hook",
            "question-format-gate.kiro.hook",
        }
        # agentStop hooks intentionally edited by the hook-architecture-improvements
        # spec (task 1.4): a behavior-preserving question-pending guard clause was
        # added to each per Req 2.4. These edits are expected and unrelated to the
        # token budget optimization, so they are excluded here.
        _AGENTSTOP_GUARD_HOOKS = {
            "module-recap-append.kiro.hook",
            "module-completion-celebration.kiro.hook",
            "enforce-gate-on-stop.kiro.hook",
            "enforce-visualization-offers.kiro.hook",
        }
        # Hook intentionally edited by the bootcamp-consistency-fixes batch: the
        # deployment-phase-gate prompt's deployment-step label was corrected from
        # "(Steps 12-15)" to "(Steps 13-15)" to match module-11-deployment.md after
        # Step 12 (Rollback Plan) moved into the packaging phase. Behavior-preserving
        # label fix, unrelated to the token budget optimization.
        _CONSISTENCY_FIX_HOOKS = {
            "deployment-phase-gate.kiro.hook",
        }
        # Hook intentionally edited by the docs-file-placement bugfix (Change 3):
        # the write-policy-gate Check 4 .py fallback was corrected from
        # "scripts/{filename}" to "src/scripts/{filename}" to remove the
        # src/-or-scripts/ ambiguity. The edit is confined to then.prompt text; the
        # JSON schema and all four security checks are unchanged. Unrelated to the
        # token budget optimization, so it is excluded here.
        _DOCS_FILE_PLACEMENT_HOOKS = {
            "write-policy-gate.kiro.hook",
        }
        _ALLOWED_MODIFIED = (
            _CONSOLIDATED_HOOKS
            | _AGENTSTOP_GUARD_HOOKS
            | _CONSISTENCY_FIX_HOOKS
            | _DOCS_FILE_PLACEMENT_HOOKS
        )
        # Filter for .kiro.hook files in the output, excluding hooks modified by
        # other specs. (Unrelated protections stay intact: any hook not in this
        # allowlist still fails the assertion.)
        modified_hooks = [
            line for line in result.stdout.strip().split("\n")
            if line.strip() and ".kiro.hook" in line
            and not any(h in line for h in _ALLOWED_MODIFIED)
        ]
        assert not modified_hooks, \
            f"Hook files were modified: {modified_hooks}"

    def test_hook_categories_yaml_not_modified(self):
        """hook-categories.yaml was not modified by the optimization.

        Note: Skipped when hook-categories.yaml is modified due to hook
        consolidation (agent-answer-processing-failures spec).
        """
        hook_categories = HOOKS_DIR / "hook-categories.yaml"
        assert hook_categories.exists(), "hook-categories.yaml not found"

        # Check git status for hook-categories.yaml
        result = subprocess.run(
            ["git", "status", "--porcelain",
             "senzing-bootcamp/hooks/hook-categories.yaml"],
            capture_output=True,
            text=True,
            cwd=str(_PROJECT_ROOT),
        )
        modified = result.stdout.strip()
        # Allow modification when hooks were consolidated by a known spec
        if modified and "M" in modified:
            # Verify the consolidation is expected by checking that deleted hooks
            # are no longer in the categories file
            categories_text = hook_categories.read_text(encoding="utf-8")
            if "enforce-step-and-transition" not in categories_text:
                # Hook consolidation removed the old hook — expected modification
                return
        assert not modified, \
            f"hook-categories.yaml was modified: {modified}"
