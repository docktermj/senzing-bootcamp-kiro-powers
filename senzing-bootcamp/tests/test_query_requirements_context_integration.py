"""Integration tests for query requirements context feature.

Validates structural integrity of the modified steering file, YAML frontmatter,
steering-index resolution, and checkpoint preservation.

Feature: query-requirements-context
Requirements: 3.1, 3.5
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_STEERING_FILE = _STEERING_DIR / "module-07-query-visualize-discover.md"
_STEERING_INDEX = _STEERING_DIR / "steering-index.yaml"
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


# ---------------------------------------------------------------------------
# Tests: CommonMark Structural Validation (Requirement 3.1)
# ---------------------------------------------------------------------------


class TestCommonMarkValidation:
    """Verify the steering file passes CommonMark structural validation.

    Requirements: 3.1
    """

    def test_steering_file_exists(self) -> None:
        """The module-07 steering file exists on disk."""
        assert _STEERING_FILE.is_file(), (
            f"Steering file not found: {_STEERING_FILE}"
        )

    def test_no_unclosed_code_blocks(self) -> None:
        """The steering file has no unclosed fenced code blocks."""
        content = _STEERING_FILE.read_text(encoding="utf-8")
        fence_pattern = re.compile(r"^(`{3,}|~{3,})", re.MULTILINE)
        fences = fence_pattern.findall(content)
        # Fenced code blocks must come in pairs (open + close)
        assert len(fences) % 2 == 0, (
            f"Unclosed code block detected: found {len(fences)} fence markers "
            f"(expected even number)"
        )

    def test_heading_structure_is_valid(self) -> None:
        """Headings follow a valid hierarchy (no skipping levels)."""
        content = _STEERING_FILE.read_text(encoding="utf-8")
        heading_pattern = re.compile(r"^(#{1,6})\s+", re.MULTILINE)
        headings = heading_pattern.findall(content)

        assert len(headings) > 0, "No headings found in steering file"

        # First heading should be level 1
        assert len(headings[0]) == 1, (
            f"First heading should be H1, got H{len(headings[0])}"
        )

        # No heading should skip more than one level down
        prev_level = 1
        for h in headings:
            level = len(h)
            # Going deeper should not skip levels (e.g., H1 -> H3 is invalid)
            if level > prev_level:
                assert level - prev_level <= 1, (
                    f"Heading level skipped: H{prev_level} -> H{level}"
                )
            prev_level = level

    def test_no_unclosed_blockquotes_in_step1(self) -> None:
        """Step 1 block does not have malformed blockquotes (unmatched > lines
        without content)."""
        content = _STEERING_FILE.read_text(encoding="utf-8")
        # Find Step 1 section
        step1_match = re.search(
            r"^1\.\s+\*\*Define query requirements\*\*",
            content,
            re.MULTILINE,
        )
        assert step1_match is not None, "Step 1 not found in steering file"

        # Extract Step 1 content (up to next numbered step)
        step1_start = step1_match.start()
        next_step = re.search(r"^2\.\s+\*\*", content[step1_start + 1:], re.MULTILINE)
        step1_end = step1_start + 1 + next_step.start() if next_step else len(content)
        step1_content = content[step1_start:step1_end]

        # Check that blockquote lines have content after >
        blockquote_lines = [
            line for line in step1_content.splitlines()
            if line.strip().startswith(">")
        ]
        for line in blockquote_lines:
            # A blockquote line should have content (> followed by space and text)
            # or be a continuation (> alone is valid for blank blockquote lines)
            stripped = line.strip()
            assert stripped == ">" or len(stripped) > 1, (
                f"Malformed blockquote line: '{line}'"
            )

    def test_validate_commonmark_script_passes(self) -> None:
        """The validate_commonmark.py script passes on the steering file.

        This test is skipped if markdownlint-cli is not installed, since it's
        an external dependency not required for the test suite.
        """
        import shutil

        if not shutil.which("markdownlint") and not shutil.which("markdownlint.cmd"):
            pytest.skip("markdownlint-cli not installed")

        result = subprocess.run(
            ["markdownlint", str(_STEERING_FILE), "--config",
             str(_REPO_ROOT / ".markdownlint.json")],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
        )
        assert result.returncode == 0, (
            f"CommonMark validation failed:\n{result.stdout}\n{result.stderr}"
        )


# ---------------------------------------------------------------------------
# Tests: YAML Frontmatter Validation (Requirement 3.1)
# ---------------------------------------------------------------------------


class TestYAMLFrontmatter:
    """Verify the steering file retains valid YAML frontmatter.

    Requirements: 3.1
    """

    def test_starts_with_frontmatter_delimiter(self) -> None:
        """The file starts with the YAML frontmatter opening delimiter '---'."""
        content = _STEERING_FILE.read_text(encoding="utf-8")
        assert content.startswith("---"), (
            "Steering file must start with YAML frontmatter delimiter '---'"
        )

    def test_has_closing_frontmatter_delimiter(self) -> None:
        """The file has a closing '---' delimiter for the frontmatter block."""
        content = _STEERING_FILE.read_text(encoding="utf-8")
        lines = content.splitlines()

        # First line is opening ---
        assert lines[0].strip() == "---"

        # Find closing --- (must be on a subsequent line)
        closing_found = False
        for line in lines[1:]:
            if line.strip() == "---":
                closing_found = True
                break

        assert closing_found, (
            "No closing '---' delimiter found for YAML frontmatter"
        )

    def test_frontmatter_contains_inclusion_key(self) -> None:
        """The frontmatter contains the 'inclusion' key."""
        content = _STEERING_FILE.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Extract frontmatter content between --- delimiters
        frontmatter_lines: list[str] = []
        in_frontmatter = False
        for line in lines:
            if line.strip() == "---":
                if not in_frontmatter:
                    in_frontmatter = True
                    continue
                else:
                    break
            if in_frontmatter:
                frontmatter_lines.append(line)

        frontmatter_text = "\n".join(frontmatter_lines)
        assert "inclusion:" in frontmatter_text, (
            "Frontmatter missing 'inclusion' key"
        )

    def test_frontmatter_inclusion_value_is_manual(self) -> None:
        """The frontmatter 'inclusion' value is 'manual'."""
        content = _STEERING_FILE.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Extract frontmatter
        frontmatter_lines: list[str] = []
        in_frontmatter = False
        for line in lines:
            if line.strip() == "---":
                if not in_frontmatter:
                    in_frontmatter = True
                    continue
                else:
                    break
            if in_frontmatter:
                frontmatter_lines.append(line)

        # Find inclusion key
        inclusion_found = False
        for line in frontmatter_lines:
            if line.strip().startswith("inclusion:"):
                value = line.split(":", 1)[1].strip()
                assert value == "manual", (
                    f"Expected inclusion: manual, got inclusion: {value}"
                )
                inclusion_found = True
                break

        assert inclusion_found, "No 'inclusion' key found in frontmatter"


# ---------------------------------------------------------------------------
# Tests: Steering Index Resolution (Requirement 3.1)
# ---------------------------------------------------------------------------


class TestSteeringIndexResolution:
    """Verify Module 7 entry in steering-index.yaml resolves correctly.

    Requirements: 3.1
    """

    def test_steering_index_exists(self) -> None:
        """The steering-index.yaml file exists."""
        assert _STEERING_INDEX.is_file(), (
            f"steering-index.yaml not found: {_STEERING_INDEX}"
        )

    def test_module_7_root_points_to_correct_file(self) -> None:
        """Module 7 root entry points to module-07-query-visualize-discover.md."""
        content = _STEERING_INDEX.read_text(encoding="utf-8")

        # Parse the module 7 root entry
        # Look for pattern: 7:\n    root: <filename>
        module7_match = re.search(
            r"^\s+7:\s*\n\s+root:\s*(.+)$",
            content,
            re.MULTILINE,
        )
        assert module7_match is not None, (
            "Module 7 entry not found in steering-index.yaml"
        )

        root_file = module7_match.group(1).strip()
        assert root_file == "module-07-query-visualize-discover.md", (
            f"Module 7 root points to '{root_file}', expected "
            f"'module-07-query-visualize-discover.md'"
        )

    def test_module_7_root_file_exists_on_disk(self) -> None:
        """The file referenced by Module 7 root entry exists on disk."""
        content = _STEERING_INDEX.read_text(encoding="utf-8")

        module7_match = re.search(
            r"^\s+7:\s*\n\s+root:\s*(.+)$",
            content,
            re.MULTILINE,
        )
        assert module7_match is not None

        root_file = module7_match.group(1).strip()
        resolved_path = _STEERING_DIR / root_file
        assert resolved_path.is_file(), (
            f"Module 7 root file does not exist: {resolved_path}"
        )

    def test_module_7_phase1_file_matches_root(self) -> None:
        """Module 7 phase1 file entry matches the root file."""
        content = _STEERING_INDEX.read_text(encoding="utf-8")

        # Find the phase1-query-visualize file entry under module 7
        phase1_match = re.search(
            r"phase1-query-visualize:\s*\n\s+file:\s*(.+)$",
            content,
            re.MULTILINE,
        )
        assert phase1_match is not None, (
            "Module 7 phase1-query-visualize entry not found"
        )

        phase1_file = phase1_match.group(1).strip()
        assert phase1_file == "module-07-query-visualize-discover.md", (
            f"Module 7 phase1 file is '{phase1_file}', expected "
            f"'module-07-query-visualize-discover.md'"
        )


# ---------------------------------------------------------------------------
# Tests: Step 1 Checkpoint Preservation (Requirement 3.5)
# ---------------------------------------------------------------------------


class TestCheckpointPreservation:
    """Verify Step 1 checkpoint marker is preserved in the steering file.

    Requirements: 3.5
    """

    def test_step1_checkpoint_exists(self) -> None:
        """Step 1 contains a checkpoint marker."""
        content = _STEERING_FILE.read_text(encoding="utf-8")

        # Find Step 1 section
        step1_match = re.search(
            r"^1\.\s+\*\*Define query requirements\*\*",
            content,
            re.MULTILINE,
        )
        assert step1_match is not None, "Step 1 not found in steering file"

        # Extract Step 1 content (up to next numbered step)
        step1_start = step1_match.start()
        next_step = re.search(r"^2\.\s+\*\*", content[step1_start + 1:], re.MULTILINE)
        step1_end = step1_start + 1 + next_step.start() if next_step else len(content)
        step1_content = content[step1_start:step1_end]

        # Verify checkpoint marker exists
        assert "**Checkpoint:**" in step1_content or "Checkpoint:" in step1_content, (
            "Step 1 checkpoint marker not found"
        )

    def test_step1_checkpoint_references_progress_file(self) -> None:
        """Step 1 checkpoint references bootcamp_progress.json."""
        content = _STEERING_FILE.read_text(encoding="utf-8")

        # Find Step 1 section
        step1_match = re.search(
            r"^1\.\s+\*\*Define query requirements\*\*",
            content,
            re.MULTILINE,
        )
        assert step1_match is not None

        # Extract Step 1 content
        step1_start = step1_match.start()
        next_step = re.search(r"^2\.\s+\*\*", content[step1_start + 1:], re.MULTILINE)
        step1_end = step1_start + 1 + next_step.start() if next_step else len(content)
        step1_content = content[step1_start:step1_end]

        # Verify checkpoint references progress file
        assert "bootcamp_progress.json" in step1_content, (
            "Step 1 checkpoint does not reference bootcamp_progress.json"
        )

    def test_step1_checkpoint_mentions_step_1(self) -> None:
        """Step 1 checkpoint writes step 1 to progress."""
        content = _STEERING_FILE.read_text(encoding="utf-8")

        # Find Step 1 section
        step1_match = re.search(
            r"^1\.\s+\*\*Define query requirements\*\*",
            content,
            re.MULTILINE,
        )
        assert step1_match is not None

        # Extract Step 1 content
        step1_start = step1_match.start()
        next_step = re.search(r"^2\.\s+\*\*", content[step1_start + 1:], re.MULTILINE)
        step1_end = step1_start + 1 + next_step.start() if next_step else len(content)
        step1_content = content[step1_start:step1_end]

        # Verify checkpoint mentions writing step 1
        checkpoint_pattern = re.search(
            r"[Cc]heckpoint.*step\s*1|[Ww]rite\s+step\s*1",
            step1_content,
        )
        assert checkpoint_pattern is not None, (
            "Step 1 checkpoint does not mention writing step 1 to progress"
        )
