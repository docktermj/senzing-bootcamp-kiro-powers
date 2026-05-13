#!/usr/bin/env python3
"""Lint steering files for structural consistency.

Scans steering files, hooks, and the steering index for:
- Orphaned cross-references
- Module numbering inconsistencies
- WAIT instruction / hook ownership conflicts
- Missing checkpoint instructions
- Steering index completeness
- Hook registry / hook file consistency
- Frontmatter validation
- Internal link validation

Usage:
    python senzing-bootcamp/scripts/lint_steering.py
    python senzing-bootcamp/scripts/lint_steering.py --warnings-as-errors
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STEERING_DIR = Path("senzing-bootcamp/steering")
HOOKS_DIR = Path("senzing-bootcamp/hooks")
INDEX_PATH = Path("senzing-bootcamp/steering/steering-index.yaml")

VALID_INCLUSIONS = {"always", "auto", "fileMatch", "manual"}
VALID_SIZE_CATEGORIES = {"small", "medium", "large"}

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Rule 1: Cross-references
RE_INCLUDE_REF = re.compile(r"#\[\[file:(.*?)\]\]")
RE_BACKTICK_MD = re.compile(r"`([a-zA-Z0-9_-]+\.md)`")

# Rule 2: Module filenames
RE_MODULE_FILENAME = re.compile(r"^module-(\d{2})-.+\.md$")

# Rule 3: WAIT instructions
RE_WAIT = re.compile(r"WAIT for")
RE_POINTING_QUESTION = re.compile(r"👉")

# Rule 4: Numbered steps and checkpoints
RE_NUMBERED_STEP = re.compile(r"^(\d+)\.\s+\*\*")
# Step headings: ## Step N or ### Step N (but not sub-steps like ### Step 1a)
RE_HEADING_STEP = re.compile(r"^#{2,}\s+Step\s+(\d+)\s*(?::|$)")
RE_CHECKPOINT = re.compile(
    r"\*\*Checkpoint:\*\*.*(?:step|Step)\s+(\d+)"
)
RE_CHECKPOINT_ANY = re.compile(r"\*\*Checkpoint:\*\*")

# Rule 7: Frontmatter
RE_FRONTMATTER_DELIM = re.compile(r"^---\s*$")
RE_INCLUSION_FIELD = re.compile(r"^inclusion:\s*(.+)$", re.MULTILINE)
RE_FILE_MATCH_PATTERN = re.compile(r"^fileMatchPattern:\s*(.+)$", re.MULTILINE)

# Rule 9: Internal links (prose references)
RE_PROSE_REF = re.compile(r"(?:load|follow|see)\s+`([^`]+\.md)`")

# Fenced code block delimiter
RE_CODE_FENCE = re.compile(r"^```")

# Hook registry patterns
RE_HOOK_ID = re.compile(r"^- id:\s*`([^`]+)`", re.MULTILINE)
RE_HOOK_EVENT_TYPE = re.compile(
    r"\*\*([a-zA-Z0-9_-]+)\*\*.*?\((\w+)\s*→\s*(\w+)"
)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class LintViolation:
    """A single lint violation found by the linter."""

    level: str   # "ERROR" or "WARNING"
    file: str    # relative path to the file
    line: int    # line number (0 when not applicable)
    message: str  # human-readable description

    def format(self) -> str:
        """Format the violation for output."""
        return f"{self.level}: {self.file}:{self.line}: {self.message}"


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def parse_frontmatter(content: str) -> tuple:
    """Parse YAML frontmatter from file content.

    Returns:
        Tuple of (frontmatter_dict_or_None, end_line_number).
        Returns (None, 0) if no frontmatter block found.
        Line numbers are 1-based.
    """
    lines = content.splitlines()
    if not lines or not RE_FRONTMATTER_DELIM.match(lines[0]):
        return (None, 0)

    # Find closing ---
    for i in range(1, len(lines)):
        if RE_FRONTMATTER_DELIM.match(lines[i]):
            # Parse the frontmatter block (simple key: value YAML)
            fm = {}
            for line in lines[1:i]:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    key, _, value = line.partition(":")
                    fm[key.strip()] = value.strip()
            return (fm, i + 1)  # 1-based end line

    return (None, 0)


def is_in_code_block(lines: list, line_index: int) -> bool:
    """Check if a given line index falls inside a fenced code block.

    Args:
        lines: List of file lines.
        line_index: 0-based index of the line to check.

    Returns:
        True if the line is inside a fenced code block.
    """
    in_block = False
    for i in range(line_index):
        if RE_CODE_FENCE.match(lines[i].strip()):
            in_block = not in_block
    return in_block


def parse_steering_index(index_path: Path) -> dict:
    """Parse steering-index.yaml and return structured data.

    Uses simple line-by-line parsing (no PyYAML dependency).

    Returns:
        dict with keys: modules, file_metadata, keywords, languages, deployment.
    """
    result = {
        "modules": {},
        "file_metadata": {},
        "keywords": {},
        "languages": {},
        "deployment": {},
    }

    if not index_path.exists():
        return result

    content = index_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    current_section = None
    current_file = None
    current_module_num = None
    in_phases = False
    in_phase = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip comments and blank lines
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        # Detect top-level sections (no indentation)
        if not line[0].isspace() and stripped.endswith(":"):
            section_name = stripped[:-1]
            if section_name in result:
                current_section = section_name
            else:
                current_section = None
            current_file = None
            current_module_num = None
            in_phases = False
            in_phase = False
            i += 1
            continue

        if not line[0].isspace() and ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if key in result:
                current_section = key
                current_file = None
                current_module_num = None
                in_phases = False
                in_phase = False
                if val:
                    # Inline value — not expected for our sections
                    pass
            i += 1
            continue

        # Process section content
        if current_section == "modules":
            # Module entries: "  1: module-01-business-problem.md" or "  5:" (complex)
            indent = len(line) - len(line.lstrip())
            if indent == 2 and ":" in stripped:
                key, _, val = stripped.partition(":")
                val = val.strip()
                try:
                    mod_num = int(key.strip())
                    if val:
                        # Simple module: "1: module-01-business-problem.md"
                        result["modules"][mod_num] = val
                        current_module_num = None
                        in_phases = False
                    else:
                        # Complex module with phases
                        current_module_num = mod_num
                        in_phases = False
                except ValueError:
                    pass
            elif indent == 4 and current_module_num is not None:
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip()
                if key == "root" and val:
                    result["modules"][current_module_num] = val
                elif key == "phases":
                    in_phases = True
                    in_phase = False
                elif key == "file" and val and in_phases:
                    # Phase file — also track as part of the module
                    pass
            elif indent == 6 and in_phases:
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip()
                if not val:
                    # Phase name
                    in_phase = True
                elif key == "file" and val:
                    # Phase file reference — these are sub-files of the module
                    pass

        elif current_section == "file_metadata":
            indent = len(line) - len(line.lstrip())
            if indent == 2 and stripped.endswith(":"):
                current_file = stripped[:-1].strip()
                result["file_metadata"][current_file] = {}
            elif indent == 4 and current_file and ":" in stripped:
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip()
                if key == "token_count":
                    try:
                        result["file_metadata"][current_file]["token_count"] = int(val)
                    except ValueError:
                        result["file_metadata"][current_file]["token_count"] = val
                elif key == "size_category":
                    result["file_metadata"][current_file]["size_category"] = val

        elif current_section in ("keywords", "languages", "deployment"):
            indent = len(line) - len(line.lstrip())
            if indent == 2 and ":" in stripped:
                key, _, val = stripped.partition(":")
                val = val.strip()
                if val:
                    result[current_section][key.strip()] = val

        i += 1

    return result


def get_final_substantive_line(lines: list) -> tuple:
    """Return the index and content of the last non-blank, non-comment line.

    Args:
        lines: List of file lines.

    Returns:
        Tuple of (0-based index, line content). Returns (-1, "") if no
        substantive line found.
    """
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].strip()
        if stripped and not stripped.startswith("<!--") and not stripped.startswith("//"):
            return (i, stripped)
    return (-1, "")


# ---------------------------------------------------------------------------
# Rule functions
# ---------------------------------------------------------------------------


def check_cross_references(steering_dir: Path, index_data: dict) -> list:
    """Rule 1: Detect orphaned cross-references.

    Scans steering files for #[[file:path]] includes and backtick-quoted .md
    filenames, verifies each exists. Also checks steering index references.
    """
    violations = []
    steering_path = Path(steering_dir)
    md_files = sorted(steering_path.glob("*.md"))

    # Known steering file names for backtick reference matching
    known_steering_names = {f.name for f in md_files}

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
        except (PermissionError, OSError) as exc:
            violations.append(LintViolation(
                "WARNING", str(md_file), 0, f"Could not read file: {exc}"
            ))
            continue

        lines = content.splitlines()
        for line_idx, line in enumerate(lines):
            if is_in_code_block(lines, line_idx):
                continue

            # Check #[[file:path]] references
            for match in RE_INCLUDE_REF.finditer(line):
                ref_path = match.group(1)
                if not Path(ref_path).exists():
                    violations.append(LintViolation(
                        "ERROR", str(md_file), line_idx + 1,
                        f"Orphaned include reference: #[[file:{ref_path}]] — "
                        f"target does not exist"
                    ))

            # Check backtick-quoted .md filenames
            for match in RE_BACKTICK_MD.finditer(line):
                ref_name = match.group(1)
                # Only flag if it looks like a steering file name
                if ref_name in known_steering_names:
                    # It exists, no violation
                    continue
                # Check if it matches a steering file naming pattern
                if (ref_name.startswith("module-") or
                        ref_name.startswith("lang-") or
                        ref_name.startswith("deployment-") or
                        ref_name.endswith("-flow.md") or
                        ref_name.endswith("-registry.md") or
                        ref_name.endswith("-instructions.md") or
                        ref_name.endswith("-resume.md") or
                        ref_name.endswith("-completion.md") or
                        ref_name.endswith("-transitions.md") or
                        ref_name.endswith("-prerequisites.md") or
                        ref_name in known_steering_names):
                    pass  # Already checked above
                # Only flag references that look like they should be steering files
                # by checking if the name matches known patterns
                if (ref_name.startswith(("module-", "lang-", "deployment-",
                                         "cloud-", "common-", "complexity-",
                                         "data-", "design-", "environment-",
                                         "feedback-", "graduation", "hook-",
                                         "mcp-", "onboarding-", "project-",
                                         "security-", "session-", "steering-",
                                         "troubleshooting-", "uat-",
                                         "visualization-", "agent-",
                                         "lessons-")) or
                        ref_name in known_steering_names):
                    if ref_name not in known_steering_names:
                        violations.append(LintViolation(
                            "ERROR", str(md_file), line_idx + 1,
                            f"Orphaned backtick reference: `{ref_name}` — "
                            f"file not found in {steering_dir}"
                        ))

    # Check steering index references
    for section_name in ("modules", "keywords", "languages", "deployment"):
        section = index_data.get(section_name, {})
        for key, value in section.items():
            if isinstance(value, str) and value.endswith(".md"):
                if not (steering_path / value).exists():
                    violations.append(LintViolation(
                        "ERROR", str(steering_path / "steering-index.yaml"), 0,
                        f"Steering index [{section_name}] key '{key}' references "
                        f"'{value}' which does not exist"
                    ))

    return violations


def check_module_numbering(steering_dir: Path, index_data: dict) -> list:
    """Rule 2: Verify module numbering consistency."""
    violations = []
    steering_path = Path(steering_dir)
    index_path_str = str(steering_path / "steering-index.yaml")

    modules_in_index = index_data.get("modules", {})
    if not modules_in_index:
        violations.append(LintViolation(
            "ERROR", index_path_str, 0, "Missing modules section"
        ))
        return violations

    # Find all module files on disk
    module_files_on_disk = {}
    for f in sorted(steering_path.glob("module-*.md")):
        m = RE_MODULE_FILENAME.match(f.name)
        if m:
            num = int(m.group(1))
            module_files_on_disk[num] = f.name

    # (a) Every module in index should have a file on disk
    for mod_num, filename in modules_in_index.items():
        if isinstance(filename, str):
            expected_prefix = f"module-{int(mod_num):02d}-"
            if not filename.startswith(expected_prefix):
                violations.append(LintViolation(
                    "ERROR", index_path_str, 0,
                    f"Module {mod_num} filename '{filename}' does not match "
                    f"expected pattern '{expected_prefix}*.md'"
                ))
            if not (steering_path / filename).exists():
                violations.append(LintViolation(
                    "ERROR", index_path_str, 0,
                    f"Module {mod_num} references '{filename}' which does not exist"
                ))

    # (b) Module files on disk not in index
    index_nums = set(int(k) for k in modules_in_index.keys())
    for num, fname in module_files_on_disk.items():
        if num not in index_nums:
            # Check if it's a phase file (e.g., module-05-phase1-...)
            # Phase files are sub-files and don't need their own index entry
            if "-phase" in fname.lower():
                continue
            violations.append(LintViolation(
                "WARNING", str(steering_path / fname), 0,
                f"Module file '{fname}' exists on disk but is not listed "
                f"in the steering index modules mapping"
            ))

    # (d) Detect gaps in module number sequence
    if index_nums:
        min_num = min(index_nums)
        max_num = max(index_nums)
        for n in range(min_num, max_num + 1):
            if n not in index_nums:
                violations.append(LintViolation(
                    "WARNING", index_path_str, 0,
                    f"Gap in module sequence: module {n} is missing "
                    f"(modules {min_num}-{max_num} expected)"
                ))

    return violations


def check_wait_conflicts(steering_dir: Path, hooks_dir: Path) -> list:
    """Rule 3: Flag WAIT instructions conflicting with closing-question ownership."""
    violations = []
    steering_path = Path(steering_dir)

    for md_file in sorted(steering_path.glob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
        except (PermissionError, OSError):
            continue

        lines = content.splitlines()
        if not lines:
            continue

        final_idx, final_content = get_final_substantive_line(lines)
        if final_idx < 0:
            continue

        # Check if the final substantive line has a WAIT instruction
        if RE_WAIT.search(final_content):
            # Check if preceded by a 👉 question
            has_pointing = False
            # Check same line
            if RE_POINTING_QUESTION.search(final_content):
                has_pointing = True
            # Check previous non-blank lines
            if not has_pointing:
                for j in range(final_idx - 1, max(final_idx - 5, -1), -1):
                    if j < 0:
                        break
                    prev = lines[j].strip()
                    if not prev:
                        continue
                    if RE_POINTING_QUESTION.search(prev):
                        has_pointing = True
                    break  # Only check the immediately preceding non-blank line

            if not has_pointing:
                violations.append(LintViolation(
                    "WARNING", str(md_file), final_idx + 1,
                    "WAIT instruction on final substantive line may conflict "
                    "with closing-question ownership rule (ask-bootcamper hook)"
                ))

    return violations


def _find_workflow_end(lines: list, frontmatter_end: int) -> int:
    """Find the end of the main workflow section.

    The main workflow section ends at the first top-level `---` horizontal
    rule after frontmatter (not indented), or at a success criteria/indicator
    section, or at end of file if no separator is found.
    """
    for i in range(frontmatter_end, len(lines)):
        line = lines[i]
        stripped = line.strip()
        # Top-level --- separator (not indented)
        if stripped == "---" and (not line or not line[0].isspace()):
            return i
        # Success criteria/indicator marks end of workflow steps
        if stripped.startswith("**Success indicator") or stripped.startswith("**Success Criteria"):
            return i
    return len(lines)


def _is_in_non_workflow_section(lines: list, line_idx: int) -> bool:
    """Check if a line falls inside a non-workflow section.

    Non-workflow sections are headed by ## headings like "Error Handling",
    "Troubleshooting", "Success Criteria", or "Agent Rules" that contain
    numbered lists which are NOT workflow steps.

    Args:
        lines: List of file lines.
        line_idx: 0-based index of the line to check.

    Returns:
        True if the line is inside a non-workflow section.
    """
    non_workflow_headings = {
        "error handling", "troubleshooting", "success criteria",
        "agent rules", "references", "appendix", "agent behavior",
        "transition", "query completeness gate", "completeness gate",
    }
    # Walk backwards to find the nearest ## heading
    for i in range(line_idx, -1, -1):
        stripped = lines[i].strip()
        if stripped.startswith("## "):
            heading_text = stripped[3:].strip().lower()
            return heading_text in non_workflow_headings
        # If we hit an H1 heading before any H2, the line is in the
        # intro section — but only if the file also has ## Step headings
        # elsewhere (indicating the numbered items are intro, not workflow)
        if stripped.startswith("# ") and not stripped.startswith("## "):
            # Check if there are any ## Step headings in the file
            has_step_headings = any(
                l.strip().startswith("## Step ")
                or l.strip().startswith("## Phase ")
                for l in lines
            )
            return has_step_headings
    return False


def check_checkpoints(steering_dir: Path) -> list:
    """Rule 4: Detect numbered steps missing checkpoint instructions."""
    violations = []
    steering_path = Path(steering_dir)

    for md_file in sorted(steering_path.glob("module-*.md")):
        m = RE_MODULE_FILENAME.match(md_file.name)
        if not m:
            continue

        # Phase files use module-global step numbering — checkpoint step
        # numbers intentionally differ from file-local step position.
        is_phase_file = "phase" in md_file.name

        try:
            content = md_file.read_text(encoding="utf-8")
        except (PermissionError, OSError):
            continue

        lines = content.splitlines()

        # Determine where frontmatter ends
        _, fm_end = parse_frontmatter(content)

        # Detect step patterns across the entire file
        heading_steps = []
        numbered_steps = []
        for line_idx in range(fm_end, len(lines)):
            line = lines[line_idx]
            if is_in_code_block(lines, line_idx):
                continue
            hm = RE_HEADING_STEP.match(line)
            if hm:
                heading_steps.append((line_idx, int(hm.group(1))))
            nm = RE_NUMBERED_STEP.match(line)
            if nm:
                # Skip numbered items inside non-workflow sections
                if not _is_in_non_workflow_section(lines, line_idx):
                    numbered_steps.append((line_idx, int(nm.group(1))))

        # Use heading steps if available (scan entire file for these)
        # For numbered steps, restrict to the main workflow section to
        # avoid false positives from numbered lists in reference sections
        if heading_steps:
            steps = heading_steps
        elif numbered_steps:
            # Filter numbered steps to only those in the main workflow
            workflow_end = _find_workflow_end(lines, fm_end)
            steps = [(idx, num) for idx, num in numbered_steps
                     if idx < workflow_end]
        else:
            continue  # Skip files with zero steps

        if not steps:
            continue

        # For each step, check for a checkpoint before the next step or EOF
        for i, (step_line, step_num) in enumerate(steps):
            if i + 1 < len(steps):
                end_line = steps[i + 1][0]
            else:
                end_line = len(lines)

            # Search for checkpoint in the range [step_line, end_line)
            found_checkpoint = False
            checkpoint_step = None
            for j in range(step_line, end_line):
                cp_match = RE_CHECKPOINT.search(lines[j])
                if cp_match:
                    found_checkpoint = True
                    checkpoint_step = int(cp_match.group(1))
                    break
                # Accept checkpoint without explicit "step N" wording
                # (used in files where each Step has its own checkpoint JSON)
                if RE_CHECKPOINT_ANY.search(lines[j]):
                    found_checkpoint = True
                    checkpoint_step = step_num
                    break

            if not found_checkpoint:
                violations.append(LintViolation(
                    "ERROR", str(md_file), step_line + 1,
                    f"Step {step_num} has no checkpoint instruction"
                ))
            elif checkpoint_step != step_num:
                # Module files commonly use module-global checkpoint numbers
                # even when file-local step numbering restarts in each phase
                # section. Only flag if the checkpoint number is LESS than the
                # step number (which would indicate a genuine error, not
                # module-global numbering).
                if checkpoint_step < step_num:
                    violations.append(LintViolation(
                        "ERROR", str(md_file), step_line + 1,
                        f"Checkpoint references step {checkpoint_step} "
                        f"but follows step {step_num}"
                    ))

    return violations


def check_index_completeness(steering_dir: Path, index_data: dict) -> list:
    """Rule 5: Verify every .md file has file_metadata with valid fields."""
    violations = []
    steering_path = Path(steering_dir)
    index_path_str = str(steering_path / "steering-index.yaml")

    file_metadata = index_data.get("file_metadata", {})
    if file_metadata is None:
        violations.append(LintViolation(
            "ERROR", index_path_str, 0, "Missing file_metadata section"
        ))
        return violations

    # Check every .md file on disk has a metadata entry
    md_files = sorted(steering_path.glob("*.md"))
    for md_file in md_files:
        fname = md_file.name
        if fname not in file_metadata:
            violations.append(LintViolation(
                "ERROR", index_path_str, 0,
                f"File '{fname}' exists on disk but has no file_metadata entry"
            ))

    # Validate each metadata entry
    for fname, meta in file_metadata.items():
        # Check token_count
        tc = meta.get("token_count")
        if tc is None:
            violations.append(LintViolation(
                "ERROR", index_path_str, 0,
                f"file_metadata['{fname}'] is missing 'token_count'"
            ))
        elif not isinstance(tc, int) or tc <= 0:
            violations.append(LintViolation(
                "ERROR", index_path_str, 0,
                f"file_metadata['{fname}'] has invalid token_count: {tc}"
            ))

        # Check size_category
        sc = meta.get("size_category")
        if sc is None:
            violations.append(LintViolation(
                "ERROR", index_path_str, 0,
                f"file_metadata['{fname}'] is missing 'size_category'"
            ))
        elif sc not in VALID_SIZE_CATEGORIES:
            violations.append(LintViolation(
                "ERROR", index_path_str, 0,
                f"file_metadata['{fname}'] has invalid size_category: '{sc}'"
            ))

    return violations


def check_hook_consistency(steering_dir: Path, hooks_dir: Path) -> list:
    """Rule 6: Verify hook registry and hook file bidirectional consistency."""
    violations = []
    steering_path = Path(steering_dir)
    hooks_path = Path(hooks_dir)
    registry_path = steering_path / "hook-registry.md"

    if not registry_path.exists():
        violations.append(LintViolation(
            "ERROR", str(registry_path), 0, "Hook registry file not found"
        ))
        return violations

    registry_content = registry_path.read_text(encoding="utf-8")

    # Extract hook IDs from registry
    registry_ids = set()
    for match in RE_HOOK_ID.finditer(registry_content):
        registry_ids.add(match.group(1))

    # Extract event types from registry (hook_id -> event_type mapping)
    registry_event_types = {}
    lines = registry_content.splitlines()
    current_hook_id = None
    for line in lines:
        # Look for hook header pattern: **hook-id** (eventType → actionType)
        event_match = RE_HOOK_EVENT_TYPE.search(line)
        if event_match:
            current_hook_id = event_match.group(1)
            event_type = event_match.group(2)
            registry_event_types[current_hook_id] = event_type

    # Find all .kiro.hook files on disk
    hook_files_on_disk = {}
    if hooks_path.exists():
        for hf in sorted(hooks_path.glob("*.kiro.hook")):
            hook_id = hf.name.replace(".kiro.hook", "")
            hook_files_on_disk[hook_id] = hf

    # (b) Registry IDs without corresponding hook files
    for hook_id in registry_ids:
        if hook_id not in hook_files_on_disk:
            violations.append(LintViolation(
                "ERROR", str(registry_path), 0,
                f"Hook '{hook_id}' is in the registry but has no "
                f"corresponding .kiro.hook file in {hooks_dir}"
            ))

    # (c) Hook files not in registry
    for hook_id, hf in hook_files_on_disk.items():
        if hook_id not in registry_ids:
            violations.append(LintViolation(
                "WARNING", str(hf), 0,
                f"Hook file '{hf.name}' exists but is not documented "
                f"in the hook registry"
            ))

    # (d) Event type mismatches
    for hook_id in registry_ids & set(hook_files_on_disk.keys()):
        hf = hook_files_on_disk[hook_id]
        try:
            hook_data = json.loads(hf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            violations.append(LintViolation(
                "ERROR", str(hf), 0, "Invalid JSON in hook file"
            ))
            continue

        file_event_type = hook_data.get("when", {}).get("type", "")
        registry_event = registry_event_types.get(hook_id, "")

        if registry_event and file_event_type and registry_event != file_event_type:
            violations.append(LintViolation(
                "ERROR", str(hf), 0,
                f"Hook '{hook_id}' event type mismatch: registry says "
                f"'{registry_event}', hook file says '{file_event_type}'"
            ))

    return violations


def check_frontmatter(steering_dir: Path) -> list:
    """Rule 7: Validate YAML frontmatter presence and inclusion field."""
    violations = []
    steering_path = Path(steering_dir)

    for md_file in sorted(steering_path.glob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
        except (PermissionError, OSError):
            continue

        fm, end_line = parse_frontmatter(content)

        if fm is None:
            violations.append(LintViolation(
                "ERROR", str(md_file), 1,
                "File lacks YAML frontmatter block (must start with ---)"
            ))
            continue

        inclusion = fm.get("inclusion")
        if inclusion is None:
            violations.append(LintViolation(
                "ERROR", str(md_file), 1,
                "Frontmatter missing 'inclusion' field"
            ))
        elif inclusion not in VALID_INCLUSIONS:
            violations.append(LintViolation(
                "ERROR", str(md_file), 1,
                f"Frontmatter has unrecognized inclusion value: '{inclusion}'"
            ))
        elif inclusion == "fileMatch":
            pattern = fm.get("fileMatchPattern", "").strip()
            if not pattern:
                violations.append(LintViolation(
                    "ERROR", str(md_file), 1,
                    "Frontmatter has inclusion 'fileMatch' but missing or "
                    "empty 'fileMatchPattern' field"
                ))

    return violations


# ---------------------------------------------------------------------------
# Template conformance regex patterns
# ---------------------------------------------------------------------------

RE_FIRST_READ = re.compile(r"\*\*🚀 First:\*\*")
RE_BEFORE_AFTER = re.compile(r"\*\*Before/After\b", re.IGNORECASE)
RE_SUCCESS_INDICATOR = re.compile(r"\*\*Success indicator\b", re.IGNORECASE)
RE_TOP_LEVEL_STEP = re.compile(r"^(\d+)\.\s+\*\*")
RE_CHECKPOINT_TEMPLATE = re.compile(
    r"\*\*Checkpoint:\*\*.*(?:step|Step)\s+(\d+)"
)

SECTION_ORDER = [
    "frontmatter",
    "first_read",
    "before_after",
    "workflow_steps",
    "success_indicator",
]


# ---------------------------------------------------------------------------
# Template conformance utility
# ---------------------------------------------------------------------------


def get_module_steering_files(steering_dir: Path) -> list:
    """Return all module-NN-*.md files in the steering directory.

    Only returns root module files (module-01-..., module-02-..., etc.),
    not phase files (module-05-phase1-..., module-06-phaseA-...).
    """
    steering_path = Path(steering_dir)
    result = []
    for f in sorted(steering_path.glob("module-*.md")):
        if RE_MODULE_FILENAME.match(f.name) and "phase" not in f.name:
            result.append(f)
    return result


# ---------------------------------------------------------------------------
# Template conformance rule functions
# ---------------------------------------------------------------------------


def check_module_frontmatter(steering_dir: Path) -> list:
    """Validate frontmatter in all module steering files.

    Checks:
    - File begins with --- delimited YAML frontmatter
    - Frontmatter contains inclusion: manual

    Returns errors for missing frontmatter, warnings for non-manual inclusion.
    """
    violations = []
    for md_file in get_module_steering_files(steering_dir):
        try:
            content = md_file.read_text(encoding="utf-8")
        except (PermissionError, OSError):
            violations.append(LintViolation(
                "WARNING", str(md_file), 0, "Could not read file"
            ))
            continue

        fm, end_line = parse_frontmatter(content)

        if fm is None:
            violations.append(LintViolation(
                "ERROR", str(md_file), 1,
                "Module file missing YAML frontmatter (must start with ---)"
            ))
            continue

        inclusion = fm.get("inclusion")
        if inclusion is None:
            violations.append(LintViolation(
                "ERROR", str(md_file), 1,
                "Module frontmatter missing 'inclusion' field"
            ))
        elif inclusion != "manual":
            violations.append(LintViolation(
                "WARNING", str(md_file), 1,
                f"Module frontmatter has inclusion '{inclusion}', expected 'manual'"
            ))

    return violations


def check_first_read_instruction(steering_dir: Path) -> list:
    """Validate first-read instruction in all module steering files.

    Checks:
    - File contains **🚀 First:** within first 10 non-blank lines after frontmatter
    - Instruction references config/bootcamp_progress.json and module-transitions.md

    Returns errors for missing instruction, warnings for missing references.
    """
    violations = []
    for md_file in get_module_steering_files(steering_dir):
        try:
            content = md_file.read_text(encoding="utf-8")
        except (PermissionError, OSError):
            violations.append(LintViolation(
                "WARNING", str(md_file), 0, "Could not read file"
            ))
            continue

        lines = content.splitlines()
        _, fm_end = parse_frontmatter(content)

        # Scan first 10 non-blank lines after frontmatter
        found_line = None
        found_line_num = None
        non_blank_count = 0
        for i in range(fm_end, len(lines)):
            stripped = lines[i].strip()
            if not stripped:
                continue
            non_blank_count += 1
            if RE_FIRST_READ.search(stripped):
                found_line = stripped
                found_line_num = i + 1  # 1-based
                break
            if non_blank_count >= 10:
                break

        if found_line is None:
            violations.append(LintViolation(
                "ERROR", str(md_file), 1,
                "Module file missing first-read instruction "
                "(**🚀 First:**) in first 10 non-blank lines after frontmatter"
            ))
            continue

        # Check references
        # Look at the found line and the next few lines for the full instruction
        instruction_text = found_line
        for j in range(found_line_num, min(found_line_num + 3, len(lines))):
            instruction_text += " " + lines[j].strip()

        has_progress = "config/bootcamp_progress.json" in instruction_text
        has_transitions = "module-transitions.md" in instruction_text

        if not has_progress:
            violations.append(LintViolation(
                "WARNING", str(md_file), found_line_num,
                "First-read instruction does not reference "
                "config/bootcamp_progress.json"
            ))
        if not has_transitions:
            violations.append(LintViolation(
                "WARNING", str(md_file), found_line_num,
                "First-read instruction does not reference "
                "module-transitions.md"
            ))

    return violations


def check_before_after_block(steering_dir: Path) -> list:
    """Validate before/after block in all module steering files.

    Checks:
    - File contains a line with **Before/After** (case-insensitive)
    - Block appears before the first workflow step

    Returns warnings for missing or misplaced blocks.
    """
    violations = []
    for md_file in get_module_steering_files(steering_dir):
        try:
            content = md_file.read_text(encoding="utf-8")
        except (PermissionError, OSError):
            violations.append(LintViolation(
                "WARNING", str(md_file), 0, "Could not read file"
            ))
            continue

        lines = content.splitlines()

        ba_line = None
        first_step_line = None

        for i, line in enumerate(lines):
            stripped = line.strip()
            if ba_line is None and RE_BEFORE_AFTER.search(stripped):
                ba_line = i
            if first_step_line is None and RE_TOP_LEVEL_STEP.match(line):
                first_step_line = i

        if ba_line is None:
            violations.append(LintViolation(
                "WARNING", str(md_file), 0,
                "Module file missing Before/After block"
            ))
        elif first_step_line is not None and ba_line > first_step_line:
            violations.append(LintViolation(
                "WARNING", str(md_file), ba_line + 1,
                "Before/After block appears after the first workflow step"
            ))

    return violations


def check_checkpoint_completeness(steering_dir: Path) -> list:
    """Validate checkpoint instructions for all workflow steps.

    Checks:
    - Every top-level numbered step has a checkpoint instruction
    - Checkpoint step numbers match their parent step
    - Files with zero steps are skipped
    - Steps in non-workflow sections (Error Handling, etc.) are skipped

    Returns errors for missing or mismatched checkpoints.
    """
    violations = []
    for md_file in get_module_steering_files(steering_dir):
        try:
            content = md_file.read_text(encoding="utf-8")
        except (PermissionError, OSError):
            violations.append(LintViolation(
                "WARNING", str(md_file), 0, "Could not read file"
            ))
            continue

        lines = content.splitlines()
        _, fm_end = parse_frontmatter(content)

        # Find the workflow end (success indicator or end of file)
        workflow_end = len(lines)
        for i in range(fm_end, len(lines)):
            if RE_SUCCESS_INDICATOR.search(lines[i].strip()):
                workflow_end = i
                break

        # Find all top-level numbered steps and heading steps, excluding
        # non-workflow sections. Prefer heading steps when present.
        heading_steps = []
        numbered_steps = []
        for i in range(fm_end, workflow_end):
            hm = RE_HEADING_STEP.match(lines[i])
            if hm:
                heading_steps.append((i, int(hm.group(1))))
                continue
            m = RE_TOP_LEVEL_STEP.match(lines[i])
            if m and not _is_in_non_workflow_section(lines, i):
                numbered_steps.append((i, int(m.group(1))))

        steps = heading_steps if heading_steps else numbered_steps

        if not steps:
            continue  # Skip files with zero steps

        # For each step, check for a checkpoint before the next step or workflow end
        for idx, (step_line, step_num) in enumerate(steps):
            if idx + 1 < len(steps):
                end_line = steps[idx + 1][0]
            else:
                end_line = workflow_end

            found_checkpoint = False
            checkpoint_step = None
            for j in range(step_line, end_line):
                cp_match = RE_CHECKPOINT_TEMPLATE.search(lines[j])
                if cp_match:
                    found_checkpoint = True
                    checkpoint_step = int(cp_match.group(1))
                    break
                # Accept a generic **Checkpoint:** anywhere in the step body
                if RE_CHECKPOINT_ANY.search(lines[j]):
                    found_checkpoint = True
                    checkpoint_step = step_num
                    break

            if not found_checkpoint:
                violations.append(LintViolation(
                    "ERROR", str(md_file), step_line + 1,
                    f"Step {step_num} has no checkpoint instruction"
                ))
            elif checkpoint_step != step_num:
                # Module files commonly use module-global checkpoint numbers
                # even when file-local step numbering restarts in each phase
                # section. Only flag if the checkpoint number is LESS than the
                # step number (which would indicate a genuine error, not
                # module-global numbering).
                if checkpoint_step < step_num:
                    violations.append(LintViolation(
                        "ERROR", str(md_file), step_line + 1,
                        f"Checkpoint references step {checkpoint_step} "
                        f"but belongs to step {step_num}"
                    ))

    return violations


def check_success_indicator(steering_dir: Path) -> list:
    """Validate success indicator in all module steering files.

    Checks:
    - File contains **Success indicator:** line (case-insensitive)
    - Success indicator appears after all workflow steps

    Returns warnings for missing indicator, errors for out-of-order placement.
    """
    violations = []
    for md_file in get_module_steering_files(steering_dir):
        try:
            content = md_file.read_text(encoding="utf-8")
        except (PermissionError, OSError):
            violations.append(LintViolation(
                "WARNING", str(md_file), 0, "Could not read file"
            ))
            continue

        lines = content.splitlines()

        si_line = None
        last_step_line = None

        for i, line in enumerate(lines):
            stripped = line.strip()
            if RE_SUCCESS_INDICATOR.search(stripped):
                si_line = i
            if RE_TOP_LEVEL_STEP.match(line):
                if not _is_in_non_workflow_section(lines, i):
                    last_step_line = i

        if si_line is None:
            violations.append(LintViolation(
                "WARNING", str(md_file), 0,
                "Module file missing success indicator "
                "(**Success indicator:**)"
            ))
        elif last_step_line is not None and si_line < last_step_line:
            violations.append(LintViolation(
                "ERROR", str(md_file), si_line + 1,
                "Success indicator appears before a workflow step"
            ))

    return violations


def check_section_order(steering_dir: Path) -> list:
    """Validate section ordering in all module steering files.

    Required order (for present sections only):
    frontmatter → first-read → before/after → workflow steps → success indicator

    Returns warnings for out-of-order sections.
    """
    violations = []
    for md_file in get_module_steering_files(steering_dir):
        try:
            content = md_file.read_text(encoding="utf-8")
        except (PermissionError, OSError):
            violations.append(LintViolation(
                "WARNING", str(md_file), 0, "Could not read file"
            ))
            continue

        lines = content.splitlines()
        fm, fm_end = parse_frontmatter(content)

        # Detect section positions (first occurrence line number)
        section_positions = {}

        if fm is not None:
            section_positions["frontmatter"] = 0  # line 0 (0-based)

        first_read_found = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not first_read_found and RE_FIRST_READ.search(stripped):
                section_positions["first_read"] = i
                first_read_found = True
            if "before_after" not in section_positions and RE_BEFORE_AFTER.search(stripped):
                section_positions["before_after"] = i
            if "workflow_steps" not in section_positions and RE_TOP_LEVEL_STEP.match(line):
                if not _is_in_non_workflow_section(lines, i):
                    section_positions["workflow_steps"] = i
            if "success_indicator" not in section_positions and RE_SUCCESS_INDICATOR.search(stripped):
                section_positions["success_indicator"] = i

        # Check ordering for present sections
        present_sections = [
            (name, pos) for name, pos in section_positions.items()
            if name in SECTION_ORDER
        ]
        # Sort by the required order
        present_ordered = sorted(
            present_sections,
            key=lambda x: SECTION_ORDER.index(x[0])
        )

        for idx in range(len(present_ordered) - 1):
            name_a, pos_a = present_ordered[idx]
            name_b, pos_b = present_ordered[idx + 1]
            if pos_a > pos_b:
                violations.append(LintViolation(
                    "WARNING", str(md_file), pos_b + 1,
                    f"Section '{name_b}' appears before '{name_a}' "
                    f"but should come after it"
                ))

    return violations


def check_internal_links(steering_dir: Path) -> list:
    """Rule 9: Validate prose references (load/follow/see `filename.md`)."""
    violations = []
    steering_path = Path(steering_dir)

    for md_file in sorted(steering_path.glob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
        except (PermissionError, OSError):
            continue

        lines = content.splitlines()
        for line_idx, line in enumerate(lines):
            if is_in_code_block(lines, line_idx):
                continue

            for match in RE_PROSE_REF.finditer(line):
                ref_name = match.group(1)
                # Only check plain filenames (no path separators)
                # References like `docs/modules/FOO.md` are repo-relative,
                # not steering file references
                if "/" in ref_name or "\\" in ref_name:
                    continue
                if not (steering_path / ref_name).exists():
                    violations.append(LintViolation(
                        "ERROR", str(md_file), line_idx + 1,
                        f"Prose reference to `{ref_name}` — file not found "
                        f"in {steering_dir}"
                    ))

    return violations


# ---------------------------------------------------------------------------
# Runner and CLI
# ---------------------------------------------------------------------------


def run_all_checks(
    steering_dir: Path,
    hooks_dir: Path,
    index_path: Path,
    warnings_as_errors: bool = False,
    skip_template: bool = False,
) -> tuple:
    """Run all lint rules and return (violations, exit_code).

    Args:
        steering_dir: Path to senzing-bootcamp/steering/
        hooks_dir: Path to senzing-bootcamp/hooks/
        index_path: Path to steering-index.yaml
        warnings_as_errors: If True, treat WARNING as ERROR for exit code.
        skip_template: If True, skip all template conformance checks.

    Returns:
        Tuple of (all_violations, exit_code).
    """
    steering_dir = Path(steering_dir)
    hooks_dir = Path(hooks_dir)
    index_path = Path(index_path)

    # Validate directories exist
    if not steering_dir.is_dir():
        return (
            [LintViolation("ERROR", str(steering_dir), 0,
                           f"Steering directory not found: {steering_dir}")],
            1,
        )

    if not hooks_dir.is_dir():
        return (
            [LintViolation("ERROR", str(hooks_dir), 0,
                           f"Hooks directory not found: {hooks_dir}")],
            1,
        )

    # Parse steering index
    if not index_path.exists():
        return (
            [LintViolation("ERROR", str(index_path), 0,
                           f"Cannot parse steering-index.yaml: file not found")],
            1,
        )

    try:
        index_data = parse_steering_index(index_path)
    except Exception as exc:
        return (
            [LintViolation("ERROR", str(index_path), 0,
                           f"Cannot parse steering-index.yaml: {exc}")],
            1,
        )

    # Run all rules
    violations = []
    violations.extend(check_cross_references(steering_dir, index_data))
    violations.extend(check_module_numbering(steering_dir, index_data))
    violations.extend(check_wait_conflicts(steering_dir, hooks_dir))
    violations.extend(check_checkpoints(steering_dir))
    violations.extend(check_index_completeness(steering_dir, index_data))
    violations.extend(check_hook_consistency(steering_dir, hooks_dir))
    violations.extend(check_frontmatter(steering_dir))
    violations.extend(check_internal_links(steering_dir))

    # Template conformance rules (unless skipped)
    if not skip_template:
        violations.extend(check_module_frontmatter(steering_dir))
        violations.extend(check_first_read_instruction(steering_dir))
        violations.extend(check_before_after_block(steering_dir))
        violations.extend(check_checkpoint_completeness(steering_dir))
        violations.extend(check_success_indicator(steering_dir))
        violations.extend(check_section_order(steering_dir))

    # Determine exit code
    if warnings_as_errors:
        has_issues = any(True for v in violations)
    else:
        has_issues = any(v.level == "ERROR" for v in violations)

    exit_code = 1 if has_issues else 0
    return (violations, exit_code)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Lint steering files for structural consistency"
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Treat warnings as errors for exit code determination",
    )
    parser.add_argument(
        "--steering-dir",
        type=Path,
        default=STEERING_DIR,
        help=f"Path to steering directory (default: {STEERING_DIR})",
    )
    parser.add_argument(
        "--hooks-dir",
        type=Path,
        default=HOOKS_DIR,
        help=f"Path to hooks directory (default: {HOOKS_DIR})",
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=INDEX_PATH,
        help=f"Path to steering-index.yaml (default: {INDEX_PATH})",
    )
    parser.add_argument(
        "--skip-template",
        action="store_true",
        help="Skip all template conformance checks for module steering files",
    )
    args = parser.parse_args()

    violations, exit_code = run_all_checks(
        args.steering_dir,
        args.hooks_dir,
        args.index_path,
        args.warnings_as_errors,
        args.skip_template,
    )

    # Print violations
    for v in violations:
        print(v.format())

    # Print summary
    error_count = sum(1 for v in violations if v.level == "ERROR")
    warning_count = sum(1 for v in violations if v.level == "WARNING")
    print(f"\n{error_count} error(s), {warning_count} warning(s)")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
