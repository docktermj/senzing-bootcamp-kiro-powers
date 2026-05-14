"""Property-based tests for structural invariants across module steering files.

Validates that every module steering file referenced in steering-index.yaml
satisfies six structural rules: before/after framing, step-checkpoint
correspondence, pointing-question-followed-by-STOP, single question per step,
prerequisites listed, and YAML frontmatter with ``inclusion: manual``.

Feature: steering-structural-validation
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# ---------------------------------------------------------------------------
# Regex constants used by structural validators
# ---------------------------------------------------------------------------

# Numbered step: "1. **Step title**" or "1. **Check for...**"
RE_NUMBERED_STEP = re.compile(r"^(\d+)\.\s+\*\*")

# Checkpoint instruction: "**Checkpoint:** Write step N to ..." or
# "**Checkpoint:** Write to config/bootcamp_progress.json:" (no step number)
RE_CHECKPOINT = re.compile(r"\*\*Checkpoint:\*\*", re.IGNORECASE)

# Pointing question: line containing 👉 followed by quoted text
RE_POINTING_QUESTION = re.compile(r"👉")

# Stop/Wait instruction: line containing STOP or WAIT as a directive
RE_STOP_INSTRUCTION = re.compile(r"\b(STOP|WAIT)\b")

# Before/After framing: "**Before/After**" or "**Before/After:**"
RE_BEFORE_AFTER = re.compile(r"\*\*Before/After:?\*\*")

# Prerequisites section: "Prerequisites" followed by colon (may be bold)
RE_PREREQUISITES = re.compile(r"Prerequisites\*{0,2}\s*:", re.IGNORECASE)

# YAML frontmatter delimiters
RE_FRONTMATTER_START = re.compile(r"^---\s*$")


# ---------------------------------------------------------------------------
# Data model and index parser
# ---------------------------------------------------------------------------


@dataclass
class ModuleFiles:
    """Resolved file paths for a single module.

    Attributes:
        module_number: Integer module identifier (1–11).
        root_file: Path to the root steering file for this module.
        phase_files: Paths to phase sub-files (empty for simple modules).
    """

    module_number: int
    root_file: Path
    phase_files: list[Path]

    @property
    def all_files(self) -> list[Path]:
        """Return root file plus all phase files."""
        return [self.root_file] + self.phase_files


def parse_steering_index(index_path: Path) -> dict[int, ModuleFiles]:
    """Parse steering-index.yaml and resolve module file paths.

    Reads the steering index, handles both simple string entries and phased
    object entries, and resolves all file paths relative to the index file's
    parent directory.

    Args:
        index_path: Path to steering-index.yaml.

    Returns:
        Mapping of module number to ModuleFiles.

    Raises:
        FileNotFoundError: If index_path does not exist.
        ValueError: If a file listed in the index does not exist on disk.
    """
    if not index_path.exists():
        raise FileNotFoundError(
            f"Steering index not found: {index_path}"
        )

    steering_dir = index_path.parent
    data = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    modules_raw: dict = data["modules"]
    result: dict[int, ModuleFiles] = {}

    for mod_num, entry in modules_raw.items():
        mod_num = int(mod_num)

        if isinstance(entry, str):
            # Simple entry: "2: module-02-sdk-setup.md"
            root = steering_dir / entry
            phase_files: list[Path] = []
        else:
            # Phased entry with root + phases map
            root = steering_dir / entry["root"]
            phase_files = [
                steering_dir / phase_info["file"]
                for phase_info in entry.get("phases", {}).values()
            ]

        # Validate all referenced files exist on disk
        for fpath in [root] + phase_files:
            if not fpath.exists():
                raise ValueError(
                    f"Module {mod_num}: referenced file does not exist: "
                    f"{fpath}"
                )

        result[mod_num] = ModuleFiles(
            module_number=mod_num,
            root_file=root,
            phase_files=phase_files,
        )

    return result


# ---------------------------------------------------------------------------
# Module-level index (parsed once, reused by fixture and Hypothesis strategy)
# ---------------------------------------------------------------------------

_STEERING_INDEX_PATH: Path = (
    Path(__file__).resolve().parent.parent / "steering" / "steering-index.yaml"
)

_INDEX: dict[int, ModuleFiles] = parse_steering_index(_STEERING_INDEX_PATH)


# ---------------------------------------------------------------------------
# Pytest fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def steering_index() -> dict[int, ModuleFiles]:
    """Session-scoped fixture providing the parsed steering index.

    Returns:
        Mapping of module number to ModuleFiles, parsed from
        ``steering-index.yaml``.
    """
    return _INDEX


# ---------------------------------------------------------------------------
# Hypothesis strategy
# ---------------------------------------------------------------------------


def st_module_number() -> st.SearchStrategy[int]:
    """Hypothesis strategy that draws from available module numbers.

    Returns:
        A strategy producing integer module numbers present in the
        steering index.
    """
    return st.sampled_from(sorted(_INDEX.keys()))


# ---------------------------------------------------------------------------
# Structural validators
# ---------------------------------------------------------------------------


def check_before_after_framing(content: str, file_path: Path) -> list[str]:
    """Check that a steering file contains a Before/After framing section.

    Searches the file content for a line matching the ``**Before/After**``
    pattern. If no match is found, a violation is returned identifying the
    file path.

    Args:
        content: The full text content of a steering file.
        file_path: Path to the file (for error messages).

    Returns:
        List of violation descriptions. Empty list means the check passed.
    """
    if RE_BEFORE_AFTER.search(content):
        return []
    return [f"{file_path}: missing **Before/After** framing section"]


def check_step_checkpoint_correspondence(
    content: str, file_path: Path
) -> list[str]:
    """Check that every numbered step has a corresponding checkpoint.

    Walks through the file line by line, recording each numbered step and
    each checkpoint instruction. For every numbered step, verifies that a
    checkpoint instruction appears between that step's line and the next
    step's line (or end of the step region).

    Steering files use two different formats for workflow steps:

    * **Heading format** — ``## Step N: Title`` (used by modules 8–11).
      When this format is detected, only heading-level steps are collected
      and inline numbered items (``1. **Bold**``) are ignored.
    * **Inline format** — ``N. **Title**`` at the start of a line (used
      by modules 1–7 and phase sub-files).  Numbered items inside
      non-step sections (Error Handling, Recovery, etc.) are excluded by
      tracking the current ``##`` heading context.

    Checkpoint numbers may differ from local step numbers (per-phase
    numbering restarts at 1 while checkpoints use global numbers), so
    this validator checks for the *presence* of any checkpoint between
    consecutive steps rather than requiring matching numbers.

    Args:
        content: The full text content of a steering file.
        file_path: Path to the file (for error messages).

    Returns:
        List of violation descriptions. Empty list means the check passed.
    """
    lines = content.splitlines()

    # Detect whether the file uses ``## Step N:`` or ``### Step N:`` headings
    re_heading_step = re.compile(r"^#{2,}\s+Step\s+(\d+)\s*(?::|$)")
    uses_heading_steps = any(
        re_heading_step.match(line) for line in lines
    )

    # Headings that contain numbered items which are NOT workflow steps.
    _NON_STEP_HEADINGS = re.compile(
        r"^##\s+"
        r"(Error Handling|Recovery|Reference|Success Criteria"
        r"|Agent Rules|Integration Patterns|Advanced Reading"
        r"|Phase Sub-Files|Completeness Gate"
        r"|Query Completeness Gate|Iterate"
        r"|Stakeholder|Common Blockers"
        r"|Agent Behavior|Quick Reference)",
        re.IGNORECASE,
    )

    # Track whether we are inside a non-step section
    in_non_step_section = False

    # Collect line indices for each numbered step
    steps: list[tuple[int, str]] = []
    # Collect line indices for each checkpoint
    checkpoint_lines: list[int] = []

    for idx, line in enumerate(lines):
        # Detect ## headings to toggle step-collection context
        if line.startswith("## "):
            in_non_step_section = bool(_NON_STEP_HEADINGS.match(line))

            # In heading-step mode, ## Step N headings are the steps
            if uses_heading_steps:
                heading_match = re_heading_step.match(line)
                if heading_match:
                    steps.append((idx, heading_match.group(1)))
                continue
            continue

        # H3 (and deeper) step headings — system-verification uses
        # `### Step N:` nested under `## Phase N` headings.
        if uses_heading_steps and line.startswith("### "):
            heading_match = re_heading_step.match(line)
            if heading_match:
                steps.append((idx, heading_match.group(1)))
            continue

        if in_non_step_section:
            continue

        # In inline-step mode, collect N. **Bold** items as steps
        if not uses_heading_steps:
            step_match = RE_NUMBERED_STEP.match(line)
            if step_match:
                steps.append((idx, step_match.group(1)))

        if RE_CHECKPOINT.search(line):
            checkpoint_lines.append(idx)

    if not steps:
        return []

    violations: list[str] = []

    for i, (step_line, step_num) in enumerate(steps):
        # Region ends at the next step's line or EOF
        if i + 1 < len(steps):
            next_step_line = steps[i + 1][0]
        else:
            next_step_line = len(lines)

        # Check for any checkpoint instruction in the region
        has_checkpoint = any(
            step_line < ckpt_line < next_step_line
            for ckpt_line in checkpoint_lines
        )

        if not has_checkpoint:
            violations.append(
                f"{file_path}: step {step_num} (line {step_line + 1})"
                f" has no corresponding checkpoint"
            )

    return violations


def check_pointing_question_stop(
    content: str, file_path: Path
) -> list[str]:
    """Check that every pointing question is followed by a STOP/WAIT.

    For each line containing 👉, searches subsequent non-blank lines
    (up to 5 lines or the next numbered step, whichever comes first)
    for a STOP or WAIT instruction.

    Args:
        content: The full text content of a steering file.
        file_path: Path to the file (for error messages).

    Returns:
        List of violation descriptions. Empty list means the check
        passed.
    """
    lines = content.splitlines()
    violations: list[str] = []

    for idx, line in enumerate(lines):
        if not RE_POINTING_QUESTION.search(line):
            continue

        # Scan up to 5 non-blank lines after the 👉 line
        found_stop = False
        non_blank_seen = 0

        for scan_idx in range(idx + 1, len(lines)):
            scan_line = lines[scan_idx]

            # Skip blank lines (they don't count toward the 5-line
            # window)
            if not scan_line.strip():
                continue

            # Stop at the next numbered step boundary
            if RE_NUMBERED_STEP.match(scan_line):
                break

            non_blank_seen += 1

            if RE_STOP_INSTRUCTION.search(scan_line):
                found_stop = True
                break

            if non_blank_seen >= 5:
                break

        if not found_stop:
            violations.append(
                f"{file_path}: pointing question at line"
                f" {idx + 1} has no STOP/WAIT instruction"
            )

    return violations


def check_single_question_per_step(
    content: str, file_path: Path
) -> list[str]:
    """Check that each numbered step contains at most one pointing question.

    Groups pointing questions by the numbered step or sub-step they belong
    to. A pointing question belongs to the most recent preceding step or
    sub-step. Sub-steps use the format ``Na. **Title**`` (e.g., ``5a.``,
    ``5b.``) and are treated as separate interaction boundaries.

    Args:
        content: The full text content of a steering file.
        file_path: Path to the file (for error messages).

    Returns:
        List of violation descriptions. Empty list means the check
        passed.
    """
    # Sub-step pattern: "5a. **Title**" or "5b. **Title**:"
    re_sub_step = re.compile(r"^(\d+[a-z])\.\s+\*\*")

    lines = content.splitlines()
    current_step: str | None = None
    questions_per_step: dict[str, int] = {}

    for line in lines:
        # Check sub-steps first (more specific pattern)
        sub_match = re_sub_step.match(line)
        if sub_match:
            current_step = sub_match.group(1)
            questions_per_step.setdefault(current_step, 0)
            continue

        step_match = RE_NUMBERED_STEP.match(line)
        if step_match:
            current_step = step_match.group(1)
            questions_per_step.setdefault(current_step, 0)
            continue

        if RE_POINTING_QUESTION.search(line) and current_step is not None:
            questions_per_step[current_step] = (
                questions_per_step.get(current_step, 0) + 1
            )

    violations: list[str] = []
    for step_num, count in questions_per_step.items():
        if count > 1:
            violations.append(
                f"{file_path}: step {step_num} has {count}"
                f" pointing questions (expected at most 1)"
            )

    return violations


def check_prerequisites_listed(
    content: str, file_path: Path
) -> list[str]:
    """Check that a steering file contains a prerequisites section.

    Searches for a line containing ``Prerequisites`` followed by a colon.

    Args:
        content: The full text content of a steering file.
        file_path: Path to the file (for error messages).

    Returns:
        List of violation descriptions. Empty list means the check
        passed.
    """
    if RE_PREREQUISITES.search(content):
        return []
    return [f"{file_path}: missing Prerequisites section"]


def check_yaml_frontmatter(content: str, file_path: Path) -> list[str]:
    """Check that a steering file has YAML frontmatter with inclusion: manual.

    Verifies that the file starts with a ``---`` delimiter, extracts the
    frontmatter block (up to the closing ``---``), and checks for an
    ``inclusion`` key with the value ``manual``.

    Args:
        content: The full text content of a steering file.
        file_path: Path to the file (for error messages).

    Returns:
        List of violation descriptions. Empty list means the check passed.
    """
    lines = content.splitlines()

    # Check that the file starts with the opening --- delimiter
    if not lines or not RE_FRONTMATTER_START.match(lines[0]):
        return [f"{file_path}: missing YAML frontmatter"]

    # Find the closing --- delimiter (second occurrence)
    closing_idx: int | None = None
    for idx in range(1, len(lines)):
        if RE_FRONTMATTER_START.match(lines[idx]):
            closing_idx = idx
            break

    if closing_idx is None:
        return [f"{file_path}: missing YAML frontmatter"]

    # Extract and parse the frontmatter block between the delimiters
    frontmatter_text = "\n".join(lines[1:closing_idx])
    frontmatter = yaml.safe_load(frontmatter_text)

    # Handle empty frontmatter (safe_load returns None for empty string)
    if not isinstance(frontmatter, dict):
        return [
            f"{file_path}: frontmatter missing 'inclusion' key"
        ]

    if "inclusion" not in frontmatter:
        return [
            f"{file_path}: frontmatter missing 'inclusion' key"
        ]

    value = frontmatter["inclusion"]
    if value != "manual":
        return [
            f"{file_path}: frontmatter has inclusion:"
            f" {value}, expected 'manual'"
        ]

    return []


# ---------------------------------------------------------------------------
# Property-based test classes
# ---------------------------------------------------------------------------


class TestProperty1BeforeAfterFraming:
    """Feature: steering-structural-validation, Property 1: Before/After Framing Presence

    For any module number in the steering index, every associated module
    steering file shall either contain a **Before/After** section, or be a
    phase sub-file whose root module file contains the section.

    Validates: Requirements 1.1, 1.2, 1.3
    """

    @given(module_num=st_module_number())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_before_after_framing_present(self, module_num: int) -> None:
        """Every module file has before/after framing (or delegates to root).

        Args:
            module_num: Module number drawn from the steering index.
        """
        mod = _INDEX[module_num]
        root_content = mod.root_file.read_text(encoding="utf-8")
        root_has_framing = not check_before_after_framing(
            root_content, mod.root_file
        )

        violations: list[str] = []

        # Check root file
        if not root_has_framing:
            violations.extend(
                check_before_after_framing(root_content, mod.root_file)
            )

        # Check each phase file; phase sub-files may delegate to root
        for phase_file in mod.phase_files:
            phase_content = phase_file.read_text(encoding="utf-8")
            phase_violations = check_before_after_framing(
                phase_content, phase_file
            )
            if phase_violations and not root_has_framing:
                violations.extend(phase_violations)

        assert violations == [], (
            f"Module {module_num} before/after framing violations: "
            f"{violations}"
        )


class TestProperty2StepCheckpointCorrespondence:
    """Feature: steering-structural-validation, Property 2: Step-Checkpoint Correspondence

    For any module number in the steering index, and for every module steering
    file that contains numbered steps, every numbered step shall have a
    corresponding checkpoint instruction with a matching step number appearing
    between that step and the next step (or end of file).

    Validates: Requirements 2.1, 2.2, 2.3, 2.4
    """

    @given(module_num=st_module_number())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_step_checkpoint_correspondence(self, module_num: int) -> None:
        """Every numbered step has a corresponding checkpoint instruction.

        Args:
            module_num: Module number drawn from the steering index.
        """
        mod = _INDEX[module_num]
        violations: list[str] = []

        for file_path in mod.all_files:
            content = file_path.read_text(encoding="utf-8")
            violations.extend(
                check_step_checkpoint_correspondence(content, file_path)
            )

        assert violations == [], (
            f"Module {module_num} step-checkpoint correspondence "
            f"violations: {violations}"
        )


class TestProperty3PointingQuestionStop:
    """Feature: steering-structural-validation, Property 3: Pointing Question Followed by STOP

    For any module number in the steering index, and for every module steering
    file, every pointing question shall be followed by a STOP or WAIT
    instruction within the next 5 non-blank lines or before the next numbered
    step.

    Validates: Requirements 3.1, 3.2, 3.3, 3.4
    """

    @given(module_num=st_module_number())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_pointing_question_followed_by_stop(
        self, module_num: int
    ) -> None:
        """Every pointing question is followed by a STOP/WAIT instruction.

        Args:
            module_num: Module number drawn from the steering index.
        """
        mod = _INDEX[module_num]
        violations: list[str] = []

        for file_path in mod.all_files:
            content = file_path.read_text(encoding="utf-8")
            violations.extend(
                check_pointing_question_stop(content, file_path)
            )

        assert violations == [], (
            f"Module {module_num} pointing-question-stop "
            f"violations: {violations}"
        )


class TestProperty4SingleQuestionPerStep:
    """Feature: steering-structural-validation, Property 4: Single Question Per Step

    For any module number in the steering index, and for every module steering
    file that contains numbered steps, each numbered step shall contain at most
    one pointing question.

    Validates: Requirements 4.3, 7.3, 7.4
    """

    @given(module_num=st_module_number())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_single_question_per_step(self, module_num: int) -> None:
        """Each numbered step has at most one pointing question.

        Args:
            module_num: Module number drawn from the steering index.
        """
        mod = _INDEX[module_num]
        violations: list[str] = []

        for file_path in mod.all_files:
            content = file_path.read_text(encoding="utf-8")
            violations.extend(
                check_single_question_per_step(content, file_path)
            )

        assert violations == [], (
            f"Module {module_num} single-question-per-step "
            f"violations: {violations}"
        )


class TestProperty5PrerequisitesListed:
    """Feature: steering-structural-validation, Property 5: Prerequisites Listed

    For any module number in the steering index, the root module steering
    file shall contain a prerequisites section (a line matching
    ``Prerequisites`` followed by a colon).

    Validates: Requirements 5.1, 5.2, 5.3
    """

    @given(module_num=st_module_number())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_prerequisites_listed(self, module_num: int) -> None:
        """Root module file contains a prerequisites section.

        Args:
            module_num: Module number drawn from the steering index.
        """
        mod = _INDEX[module_num]
        content = mod.root_file.read_text(encoding="utf-8")
        violations = check_prerequisites_listed(content, mod.root_file)

        assert violations == [], (
            f"Module {module_num} prerequisites-listed "
            f"violations: {violations}"
        )


class TestProperty6YamlFrontmatter:
    """Feature: steering-structural-validation, Property 6: YAML Frontmatter

    For any module number in the steering index, every associated module
    steering file (root and phase sub-files) shall begin with a YAML
    frontmatter block containing inclusion: manual.

    Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5
    """

    @given(module_num=st_module_number())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_yaml_frontmatter_present(self, module_num: int) -> None:
        """Every module file has YAML frontmatter with inclusion: manual.

        Args:
            module_num: Module number drawn from the steering index.
        """
        mod = _INDEX[module_num]
        violations: list[str] = []

        for file_path in mod.all_files:
            content = file_path.read_text(encoding="utf-8")
            violations.extend(
                check_yaml_frontmatter(content, file_path)
            )

        assert violations == [], (
            f"Module {module_num} yaml-frontmatter "
            f"violations: {violations}"
        )


class TestProperty7IndexFileExistence:
    """Feature: steering-structural-validation, Property 7: Index File Existence

    For any module number in the steering index, every file path referenced
    by that module entry (root file and all phase sub-files) shall exist on
    disk.

    Validates: Requirements 8.1, 8.4
    """

    @given(module_num=st_module_number())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_index_files_exist(self, module_num: int) -> None:
        """All files referenced by a module entry exist on disk.

        Args:
            module_num: Module number drawn from the steering index.
        """
        mod = _INDEX[module_num]
        missing: list[str] = [
            str(file_path)
            for file_path in mod.all_files
            if not file_path.exists()
        ]

        assert missing == [], (
            f"Module {module_num} references files that do not"
            f" exist on disk: {missing}"
        )


# ---------------------------------------------------------------------------
# Example-based test classes
# ---------------------------------------------------------------------------


class TestIndexResolution:
    """Feature: steering-structural-validation, Example-based index tests.

    Validates: Requirements 8.2, 8.3, 8.4
    """

    def test_simple_entry_resolves_to_single_file(self) -> None:
        """Module 4 (simple string entry) resolves to one root file.

        Verifies that a simple string entry in the steering index
        produces a ModuleFiles with the correct root file, no phase
        files, and exactly one file in all_files.
        """
        mod = _INDEX[4]
        assert mod.module_number == 4
        assert mod.root_file.name == "module-04-data-collection.md"
        assert mod.phase_files == []
        assert len(mod.all_files) == 1

    def test_phased_entry_resolves_to_root_plus_phases(self) -> None:
        """Module 5 (phased entry) resolves to root + 3 phase files.

        Verifies that a phased object entry in the steering index
        produces a ModuleFiles with the correct root file, three
        phase sub-files, and four total files in all_files.
        """
        mod = _INDEX[5]
        assert mod.module_number == 5
        assert mod.root_file.name == (
            "module-05-data-quality-mapping.md"
        )
        assert len(mod.phase_files) == 3
        assert len(mod.all_files) == 4
        phase_names = sorted(f.name for f in mod.phase_files)
        assert "module-05-phase1-quality-assessment.md" in phase_names
        assert "module-05-phase2-data-mapping.md" in phase_names
        assert "module-05-phase3-test-load.md" in phase_names

    def test_missing_file_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        """Index referencing non-existent file raises ValueError.

        Creates a temporary steering index YAML file that references
        a file that does not exist on disk, then verifies that
        parse_steering_index raises ValueError with a descriptive
        message.
        """
        index_content = "modules:\n  99: nonexistent-module.md\n"
        index_file = tmp_path / "steering-index.yaml"
        index_file.write_text(index_content, encoding="utf-8")
        with pytest.raises(ValueError, match="does not exist"):
            parse_steering_index(index_file)
