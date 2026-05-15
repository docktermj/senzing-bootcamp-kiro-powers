"""Property-based tests for module transition validation.

Validates that all module steering files follow the banner → journey map →
before/after transition pattern defined in module-transitions.md.

Feature: module-transition-validation-tests
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_INDEX_PATH = _STEERING_DIR / "steering-index.yaml"


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class ModuleFiles:
    """Resolved file paths for a single module."""

    module_number: int
    root_file: Path
    last_phase_file: Path
    all_phase_files: list[Path]


# ---------------------------------------------------------------------------
# Minimal YAML Parser
# ---------------------------------------------------------------------------


def parse_steering_index(path: Path) -> dict:
    """Parse the steering-index.yaml modules section.

    A minimal line-based parser that extracts the ``modules:`` top-level key.
    Handles simple string entries and nested objects with ``root``, ``phases``,
    ``file``, and ``step_range`` keys.

    Args:
        path: Path to steering-index.yaml.

    Returns:
        Dict mapping module numbers (int) to either a filename string
        (single-file module) or a dict with 'root' and 'phases' keys
        (multi-phase module).

    Raises:
        FileNotFoundError: If the steering index file does not exist.
        ValueError: If the YAML structure is malformed.
    """
    if not path.exists():
        raise FileNotFoundError(f"Steering index not found: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()

    # Find the modules: section
    modules_start = None
    for i, line in enumerate(lines):
        if line.rstrip() == "modules:":
            modules_start = i + 1
            break

    if modules_start is None:
        raise ValueError("No 'modules:' key found in steering index")

    modules: dict[int, str | dict] = {}
    i = modules_start

    while i < len(lines):
        line = lines[i]

        # Stop at next top-level key (no indentation)
        if line and not line[0].isspace() and not line.startswith("#"):
            break

        # Skip blank lines and comments
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        # Module entry line: "  N: value" or "  N:"
        indent = len(line) - len(line.lstrip())
        if indent == 2:
            # Parse "N: value" or "N:"
            colon_pos = stripped.find(":")
            if colon_pos == -1:
                raise ValueError(f"Malformed module entry at line {i + 1}: {line}")

            key_str = stripped[:colon_pos].strip()
            try:
                module_num = int(key_str)
            except ValueError:
                raise ValueError(
                    f"Expected integer module number at line {i + 1}, got: {key_str}"
                )

            value_str = stripped[colon_pos + 1:].strip()

            if value_str:
                # Simple entry: "N: filename.md"
                modules[module_num] = value_str
                i += 1
            else:
                # Complex entry: parse nested root and phases
                module_data: dict = {}
                i += 1
                while i < len(lines):
                    nested_line = lines[i]
                    nested_stripped = nested_line.strip()

                    if not nested_stripped or nested_stripped.startswith("#"):
                        i += 1
                        continue

                    nested_indent = len(nested_line) - len(nested_line.lstrip())
                    if nested_indent <= 2:
                        break  # Back to module-level or top-level

                    if nested_indent == 4:
                        # Keys: root, phases
                        nc = nested_stripped.find(":")
                        if nc == -1:
                            raise ValueError(
                                f"Malformed nested entry at line {i + 1}: {nested_line}"
                            )
                        nkey = nested_stripped[:nc].strip()
                        nval = nested_stripped[nc + 1:].strip()

                        if nkey == "root":
                            module_data["root"] = nval
                            i += 1
                        elif nkey == "phases":
                            # Parse phases block
                            phases: dict[str, dict] = {}
                            i += 1
                            while i < len(lines):
                                phase_line = lines[i]
                                phase_stripped = phase_line.strip()

                                if not phase_stripped or phase_stripped.startswith("#"):
                                    i += 1
                                    continue

                                phase_indent = len(phase_line) - len(phase_line.lstrip())
                                if phase_indent <= 4:
                                    break  # Back to module keys level

                                if phase_indent == 6:
                                    # Phase name line: "      phase-name:"
                                    pc = phase_stripped.find(":")
                                    if pc == -1:
                                        raise ValueError(
                                            f"Malformed phase entry at line {i + 1}"
                                        )
                                    phase_name = phase_stripped[:pc].strip()
                                    phase_data: dict = {}
                                    i += 1
                                    while i < len(lines):
                                        prop_line = lines[i]
                                        prop_stripped = prop_line.strip()

                                        if (
                                            not prop_stripped
                                            or prop_stripped.startswith("#")
                                        ):
                                            i += 1
                                            continue

                                        prop_indent = len(prop_line) - len(
                                            prop_line.lstrip()
                                        )
                                        if prop_indent <= 6:
                                            break  # Back to phase-name level

                                        # Phase properties: file, step_range, etc.
                                        ppc = prop_stripped.find(":")
                                        if ppc == -1:
                                            raise ValueError(
                                                f"Malformed phase property at "
                                                f"line {i + 1}"
                                            )
                                        pkey = prop_stripped[:ppc].strip()
                                        pval = prop_stripped[ppc + 1:].strip()

                                        if pkey == "file":
                                            phase_data["file"] = pval
                                        elif pkey == "step_range":
                                            # Parse [N, M]
                                            pval = pval.strip("[]")
                                            parts = pval.split(",")
                                            if len(parts) != 2:
                                                raise ValueError(
                                                    f"Malformed step_range at "
                                                    f"line {i + 1}"
                                                )
                                            phase_data["step_range"] = (
                                                int(parts[0].strip()),
                                                int(parts[1].strip()),
                                            )
                                        # Skip token_count, size_category
                                        i += 1

                                    if "file" not in phase_data:
                                        raise ValueError(
                                            f"Phase '{phase_name}' missing 'file' key"
                                        )
                                    if "step_range" not in phase_data:
                                        raise ValueError(
                                            f"Phase '{phase_name}' missing "
                                            f"'step_range' key"
                                        )
                                    phases[phase_name] = phase_data
                                else:
                                    i += 1

                            module_data["phases"] = phases
                        else:
                            # Skip other keys at this level
                            i += 1
                    else:
                        i += 1

                if "root" not in module_data:
                    raise ValueError(
                        f"Module {module_num} missing 'root' key"
                    )
                if "phases" not in module_data:
                    raise ValueError(
                        f"Module {module_num} missing 'phases' key"
                    )
                modules[module_num] = module_data
        else:
            i += 1

    if not modules:
        raise ValueError("No modules found in steering index")

    return modules

# ---------------------------------------------------------------------------
# Module Resolver
# ---------------------------------------------------------------------------


def resolve_module_files(
    module_number: int,
    entry: str | dict,
    steering_dir: Path,
) -> ModuleFiles:
    """Resolve a steering index entry to concrete file paths.

    Args:
        module_number: The module number from the steering index.
        entry: The steering index value — a filename string or a dict
               with 'root' and 'phases' keys.
        steering_dir: Path to the steering directory.

    Returns:
        ModuleFiles with resolved paths.

    Raises:
        FileNotFoundError: If any referenced file does not exist on disk.
    """
    if isinstance(entry, str):
        file_path = steering_dir / entry
        if not file_path.exists():
            raise FileNotFoundError(
                f"Module {module_number}: file not found: {file_path}"
            )
        return ModuleFiles(
            module_number=module_number,
            root_file=file_path,
            last_phase_file=file_path,
            all_phase_files=[file_path],
        )

    # Complex entry with root and phases
    root_path = steering_dir / entry["root"]
    if not root_path.exists():
        raise FileNotFoundError(
            f"Module {module_number}: root file not found: {root_path}"
        )

    all_phase_files: list[Path] = []
    last_phase_file = root_path
    max_step_end = -1

    for phase_name, phase_data in entry["phases"].items():
        phase_path = steering_dir / phase_data["file"]
        if not phase_path.exists():
            raise FileNotFoundError(
                f"Module {module_number}, phase '{phase_name}': "
                f"file not found: {phase_path}"
            )
        all_phase_files.append(phase_path)

        step_end = phase_data["step_range"][1]
        if step_end > max_step_end:
            max_step_end = step_end
            last_phase_file = phase_path

    return ModuleFiles(
        module_number=module_number,
        root_file=root_path,
        last_phase_file=last_phase_file,
        all_phase_files=all_phase_files,
    )



# ---------------------------------------------------------------------------
# Content Checkers
# ---------------------------------------------------------------------------


def has_transition_reference(content: str) -> bool:
    """Check if file content contains a reference to module-transitions.md."""
    return "module-transitions.md" in content


def has_before_after_section(content: str) -> bool:
    """Check if file content contains a **Before/After** section.

    Matches both ``**Before/After**:`` and ``**Before/After:**`` variants.
    """
    return "**Before/After**" in content or "**Before/After:**" in content


def has_success_indicator(content: str) -> bool:
    """Check if file content contains **Success or ✅ emoji."""
    return "**Success" in content or "\u2705" in content



# ---------------------------------------------------------------------------
# Module-level parsing and Hypothesis strategy
# ---------------------------------------------------------------------------

_MODULES: dict[int, str | dict] = parse_steering_index(_INDEX_PATH)


def st_module_number() -> st.SearchStrategy[int]:
    """Hypothesis strategy that draws from the steering index module numbers."""
    return st.sampled_from(sorted(_MODULES.keys()))



# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestModuleTransitionProperties:
    """Property-based tests for module transition validation.

    Validates Requirements 1-5 from the module-transition-validation-tests spec.
    """

    @given(module_num=st_module_number())
    @settings(max_examples=10)
    def test_transition_reference_in_root_files(self, module_num: int) -> None:
        """Property 1: Transition Reference Invariant.

        For any module number drawn from the steering index, the root module
        file contains 'module-transitions.md'.

        Feature: module-transition-validation-tests
        Property 1: Transition Reference Invariant
        Validates: Requirements 1.1, 1.3
        """
        entry = _MODULES[module_num]
        module_files = resolve_module_files(module_num, entry, _STEERING_DIR)
        content = module_files.root_file.read_text(encoding="utf-8")
        assert has_transition_reference(content), (
            f"Module {module_num}: root file {module_files.root_file.name} "
            f"does not reference module-transitions.md"
        )


    @given(module_num=st_module_number())
    @settings(max_examples=10)
    def test_before_after_section_in_root_files(self, module_num: int) -> None:
        """Property 2: Before/After Section Invariant.

        For any module number drawn from the steering index, the root module
        file contains '**Before/After**'.

        Feature: module-transition-validation-tests
        Property 2: Before/After Section Invariant
        Validates: Requirements 2.1, 2.3
        """
        entry = _MODULES[module_num]
        module_files = resolve_module_files(module_num, entry, _STEERING_DIR)
        content = module_files.root_file.read_text(encoding="utf-8")
        assert has_before_after_section(content), (
            f"Module {module_num}: root file {module_files.root_file.name} "
            f"does not contain **Before/After** section"
        )


    @given(module_num=st_module_number())
    @settings(max_examples=10)
    def test_success_indicator_in_appropriate_file(self, module_num: int) -> None:
        """Property 3: Success Indicator Invariant.

        For any module number drawn from the steering index, the appropriate
        file (root for single-file, last phase sub-file for multi-phase)
        contains '**Success' or '✅'.

        Feature: module-transition-validation-tests
        Property 3: Success Indicator Invariant
        Validates: Requirements 3.1, 3.2, 3.4
        """
        entry = _MODULES[module_num]
        module_files = resolve_module_files(module_num, entry, _STEERING_DIR)
        content = module_files.last_phase_file.read_text(encoding="utf-8")
        assert has_success_indicator(content), (
            f"Module {module_num}: file {module_files.last_phase_file.name} "
            f"does not contain a success indicator (**Success or ✅)"
        )


    @given(module_num=st_module_number())
    @settings(max_examples=10)
    def test_all_referenced_files_exist(self, module_num: int) -> None:
        """Property 4: File Resolution Completeness.

        For any module number drawn from the steering index, all files
        referenced by that module entry exist on disk.

        Feature: module-transition-validation-tests
        Property 4: File Resolution Completeness
        Validates: Requirements 4.2, 5.2, 5.3, 5.4
        """
        entry = _MODULES[module_num]
        # resolve_module_files raises FileNotFoundError if any file is missing
        module_files = resolve_module_files(module_num, entry, _STEERING_DIR)
        # Explicitly verify all paths exist (belt-and-suspenders)
        assert module_files.root_file.exists(), (
            f"Module {module_num}: root file not found: {module_files.root_file}"
        )
        for phase_file in module_files.all_phase_files:
            assert phase_file.exists(), (
                f"Module {module_num}: phase file not found: {phase_file}"
            )
