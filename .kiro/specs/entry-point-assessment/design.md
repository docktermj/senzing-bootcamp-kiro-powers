# Design Document

## Overview

The Entry Point Assessment script (`senzing-bootcamp/scripts/assess_entry_point.py`) is a single-file Python 3.11+ CLI tool that determines where a bootcamper should begin (or resume) the Senzing Bootcamp. It reads the `module-artifacts.yaml` manifest, scans the bootcamper's filesystem for produced artifacts, checks Senzing SDK importability via subprocess, and outputs a per-module checklist with a final recommendation of the first incomplete module.

The script follows the project's established conventions: stdlib-only, argparse CLI with `main(argv=None)`, dataclasses for structured data, and a custom YAML parser (no PyYAML dependency).

## Architecture

The Entry Point Assessment script (`senzing-bootcamp/scripts/assess_entry_point.py`) is a single-file Python CLI tool that follows the project's established script pattern. It uses a layered architecture with clear separation between parsing, scanning, logic, and output concerns.

```
┌─────────────────────────────────────────────────────┐
│                    CLI Layer (argparse)              │
│  main(argv=None) → parse args → orchestrate        │
├─────────────────────────────────────────────────────┤
│              Orchestrator (AssessmentRunner)         │
│  Coordinates parsing, scanning, logic, output       │
├──────────┬──────────┬───────────┬───────────────────┤
│  Manifest│ Artifact │    SDK    │  Recommendation   │
│  Parser  │ Scanner  │  Checker  │     Engine        │
├──────────┴──────────┴───────────┴───────────────────┤
│              Output Formatter                        │
│  Renders per-module checklist + recommendation      │
└─────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Custom YAML Parser (`parse_manifest`)

A minimal YAML parser that handles the subset of YAML used in `module-artifacts.yaml`. It does not attempt full YAML spec compliance — only the indentation-based structure with string scalars, sequences, and mappings needed for the manifest format.

```python
@dataclass
class Artifact:
    """A single artifact expected by a module."""
    path: str
    type: str  # "file" or "directory"
    description: str
    required: bool


@dataclass
class ModuleManifest:
    """Parsed representation of a single module's manifest entry."""
    number: int
    produces: list[Artifact]
    requires_from: dict[int, list[str]]  # source_module -> [artifact_paths]


def parse_manifest(text: str) -> list[ModuleManifest]:
    """Parse module-artifacts.yaml content into structured data.

    Args:
        text: Raw YAML text content of the manifest file.

    Returns:
        List of ModuleManifest entries in module-number order.

    Raises:
        ValueError: If the YAML structure is malformed or missing required fields.
    """
```

The parser operates line-by-line using indentation depth to determine nesting. It recognizes:
- Top-level `modules:` key
- Numeric module keys (e.g., `4:`, `5:`)
- `produces:` sequences with `- path:`, `type:`, `description:`, `required:` fields
- `requires_from:` mappings with numeric keys and list values

### 2. Artifact Scanner (`scan_artifacts`)

Checks artifact presence against the filesystem using `pathlib.Path`.

```python
@dataclass
class ArtifactStatus:
    """Result of checking a single artifact's presence."""
    artifact: Artifact
    present: bool


def scan_artifacts(
    artifacts: list[Artifact],
    project_dir: Path,
) -> list[ArtifactStatus]:
    """Check each artifact's presence in the project directory.

    Args:
        artifacts: List of artifacts to check.
        project_dir: Root directory to resolve artifact paths against.

    Returns:
        List of ArtifactStatus results, one per input artifact.
    """
```

Presence rules:
- **Directory**: `path.is_dir()` and `any(path.iterdir())` (exists and non-empty)
- **File**: `path.is_file()` and `path.stat().st_size > 0` (exists and non-zero size)

Path normalization uses `PurePosixPath` for manifest paths and converts to platform-native paths via `Path()` for filesystem checks, ensuring both `/` and `\` separators work.

### 3. SDK Checker (`check_sdk`)

Runs a subprocess to test Senzing SDK importability.

```python
@dataclass
class SdkStatus:
    """Result of the SDK importability check."""
    available: bool | None  # None = unknown (no Python found)
    version: str | None
    note: str | None  # timeout or diagnostic message


def check_sdk() -> SdkStatus:
    """Check whether the Senzing Python SDK is importable.

    Uses shutil.which to find a Python interpreter, then runs a subprocess
    that attempts `import senzing` with a 15-second timeout.

    Returns:
        SdkStatus with availability, version, and optional diagnostic note.
    """
```

Implementation:
1. `shutil.which("python3")` or `shutil.which("python")` to find interpreter
2. If no interpreter found → `SdkStatus(available=None, version=None, note="...")`
3. Run `subprocess.run([python, "-c", "import senzing; print(senzing.__version__)"], timeout=15)`
4. Exit code 0 → `SdkStatus(available=True, version=stdout.strip(), note=None)`
5. Non-zero exit → `SdkStatus(available=False, version=None, note=None)`
6. `subprocess.TimeoutExpired` → `SdkStatus(available=False, version=None, note="timeout")`

### 4. Module Completeness Logic (`determine_completeness`)

```python
@dataclass
class ModuleStatus:
    """Completeness state of a single module."""
    number: int
    complete: bool
    artifact_statuses: list[ArtifactStatus]


def determine_completeness(
    manifest: ModuleManifest,
    artifact_statuses: list[ArtifactStatus],
) -> ModuleStatus:
    """Determine whether a module is complete based on required artifact presence.

    A module is complete if and only if ALL artifacts with required=True are present.
    Artifacts with required=False are reported but do not affect completeness.

    Args:
        manifest: The module's manifest entry.
        artifact_statuses: Scan results for the module's artifacts.

    Returns:
        ModuleStatus with completeness determination.
    """
```

### 5. Recommendation Engine (`recommend_entry_point`)

```python
@dataclass
class Recommendation:
    """The final entry point recommendation."""
    module_number: int | None  # None means graduation (all complete)
    module_name: str
    reason: str


def recommend_entry_point(
    module_statuses: list[ModuleStatus],
    sdk_status: SdkStatus,
) -> Recommendation:
    """Determine the recommended entry point module.

    Logic:
    1. If SDK is unavailable and module 2 is incomplete → recommend module 2
    2. Otherwise, recommend the first incomplete module in ascending order
    3. If all modules are complete → recommend graduation

    Args:
        module_statuses: Completeness states for modules 4-11.
        sdk_status: Result of the SDK importability check.

    Returns:
        Recommendation with module number, name, and reason.
    """
```

### 6. Output Formatter (`format_report`)

```python
@dataclass
class AssessmentReport:
    """Complete assessment result ready for formatting."""
    module_statuses: list[ModuleStatus]
    sdk_status: SdkStatus
    recommendation: Recommendation


def format_report(report: AssessmentReport) -> str:
    """Format the assessment report as a human-readable checklist.

    Output structure:
    - Per-module section with artifact checklist (path, type, required, status)
    - SDK check result (availability + version)
    - Summary recommendation line

    Args:
        report: The complete assessment result.

    Returns:
        Formatted string for terminal output.
    """
```

### 7. CLI Entry Point

```python
def main(argv: list[str] | None = None) -> None:
    """Entry point for the assess_entry_point script.

    Args:
        argv: Optional argument list (defaults to sys.argv[1:]).

    CLI options:
        --project-dir PATH  Project directory to scan (default: cwd)
        --manifest PATH     Path to module-artifacts.yaml
                           (default: config/module-artifacts.yaml relative to script dir)

    Exit codes:
        0: Assessment completed successfully
        1: Unrecoverable error (missing manifest, unreadable file)
    """
```

## Data Models

```python
from __future__ import annotations

import argparse
import os
import subprocess
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath


@dataclass
class Artifact:
    """A single artifact expected by a module."""
    path: str
    type: str  # "file" or "directory"
    description: str
    required: bool


@dataclass
class ModuleManifest:
    """Parsed representation of a single module's manifest entry."""
    number: int
    produces: list[Artifact] = field(default_factory=list)
    requires_from: dict[int, list[str]] = field(default_factory=dict)


@dataclass
class ArtifactStatus:
    """Result of checking a single artifact's presence."""
    artifact: Artifact
    present: bool


@dataclass
class ModuleStatus:
    """Completeness state of a single module."""
    number: int
    complete: bool
    artifact_statuses: list[ArtifactStatus] = field(default_factory=list)


@dataclass
class SdkStatus:
    """Result of the SDK importability check."""
    available: bool | None  # None = unknown (no Python found)
    version: str | None = None
    note: str | None = None


@dataclass
class Recommendation:
    """The final entry point recommendation."""
    module_number: int | None  # None means graduation
    module_name: str = ""
    reason: str = ""


@dataclass
class AssessmentReport:
    """Complete assessment result."""
    module_statuses: list[ModuleStatus] = field(default_factory=list)
    sdk_status: SdkStatus = field(default_factory=lambda: SdkStatus(available=None))
    recommendation: Recommendation = field(
        default_factory=lambda: Recommendation(module_number=None)
    )
```

## Interfaces

### Public API

| Function | Input | Output | Side Effects |
|----------|-------|--------|--------------|
| `parse_manifest(text)` | `str` | `list[ModuleManifest]` | None (pure) |
| `scan_artifacts(artifacts, project_dir)` | `list[Artifact], Path` | `list[ArtifactStatus]` | Filesystem reads |
| `check_sdk()` | None | `SdkStatus` | Subprocess execution |
| `determine_completeness(manifest, statuses)` | `ModuleManifest, list[ArtifactStatus]` | `ModuleStatus` | None (pure) |
| `recommend_entry_point(statuses, sdk)` | `list[ModuleStatus], SdkStatus` | `Recommendation` | None (pure) |
| `format_report(report)` | `AssessmentReport` | `str` | None (pure) |
| `main(argv)` | `list[str] \| None` | `None` (exits) | I/O, subprocess, exit |

### Internal Helpers

| Function | Purpose |
|----------|---------|
| `_normalize_path(path_str)` | Convert manifest path to platform-native `Path` |
| `_is_dir_present(path)` | Check directory exists and is non-empty |
| `_is_file_present(path)` | Check file exists and has size > 0 |
| `_find_python()` | Locate Python interpreter via `shutil.which` |

## Error Handling

| Error Condition | Behavior |
|-----------------|----------|
| Manifest file not found | Print error to stderr with file path, exit code 1 |
| Manifest file unreadable (permissions) | Print error to stderr, exit code 1 |
| Manifest YAML malformed | Print parse error to stderr, exit code 1 |
| Project directory not found | Print error to stderr, exit code 1 |
| Artifact path permission denied | Mark artifact as missing, continue assessment |
| SDK subprocess timeout (15s) | Record SDK as unavailable with timeout note |
| No Python interpreter on PATH | Record SDK as unknown with diagnostic |
| Unexpected exception in scan | Log warning, mark affected artifact as missing |

## Cross-Platform Path Handling

The manifest stores paths with forward slashes (POSIX convention). The script normalizes these for the current platform:

```python
def _normalize_path(manifest_path: str) -> Path:
    """Convert a manifest path (always forward-slash) to a platform Path.

    Handles both 'data/raw/' and 'data\\raw\\' by normalizing through
    PurePosixPath then converting to native Path.
    """
    # Strip trailing slashes for consistent comparison
    cleaned = manifest_path.replace("\\", "/").rstrip("/")
    return Path(PurePosixPath(cleaned))
```

## Testing Strategy

The script's pure logic functions (`parse_manifest`, `determine_completeness`, `recommend_entry_point`, `format_report`, `_normalize_path`) are ideal candidates for property-based testing since they have clear input/output behavior and universal properties that hold across all valid inputs.

**Property-based tests** (Hypothesis, `@settings(max_examples=20)`):
- Manifest parsing round-trip
- Artifact presence detection (using `tmp_path` fixtures)
- Completeness logic (pure function, no I/O)
- Recommendation engine (pure function)
- Output report completeness
- Path separator normalization

**Example-based unit tests**:
- CLI argument parsing (--project-dir, --manifest, defaults)
- Error conditions (missing manifest, unreadable file → exit 1)
- SDK check result interpretation (mocked subprocess)
- Module evaluation order (4 through 11)

**Integration tests**:
- End-to-end `main()` with a real temp directory structure
- SDK subprocess execution (mocked at subprocess level)

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Manifest Parsing Round-Trip

*For any* valid manifest structure (containing module numbers 4–11, each with a list of artifacts having path/type/description/required fields, and optional requires_from mappings), serializing that structure to the expected YAML format and then parsing it with `parse_manifest` SHALL produce a list of `ModuleManifest` objects with identical module numbers, artifact paths, artifact types, required flags, and requires_from mappings.

**Validates: Requirements 1.1, 1.3, 1.4**

### Property 2: Artifact Presence Detection

*For any* artifact and filesystem state: (a) a directory-type artifact is present if and only if the directory exists and contains at least one entry, and (b) a file-type artifact is present if and only if the file exists and has size greater than zero bytes. The `scan_artifacts` function SHALL return presence=True only when these conditions hold.

**Validates: Requirements 2.2, 2.3**

### Property 3: Completeness Depends Only on Required Artifacts

*For any* module with a mix of required and optional artifacts, `determine_completeness` SHALL return complete=True if and only if all artifacts with required=True are present. The presence or absence of artifacts with required=False SHALL not change the completeness result.

**Validates: Requirements 2.4, 2.5, 4.1, 4.2**

### Property 4: Recommendation Is First Incomplete Module

*For any* list of module statuses (modules 4–11) where the SDK is available: if all modules are complete, the recommendation SHALL be graduation; otherwise, the recommendation SHALL be the module with the lowest number that has complete=False.

**Validates: Requirements 5.1, 5.2**

### Property 5: SDK Unavailable Overrides Recommendation

*For any* assessment state where the SDK status is unavailable and module 2 artifacts are incomplete, `recommend_entry_point` SHALL return module 2 as the recommendation, regardless of the completeness states of modules 4–11.

**Validates: Requirements 5.3, 5.4**

### Property 6: Output Report Completeness

*For any* `AssessmentReport` containing module statuses and an SDK status, `format_report` SHALL produce a string that contains: (a) for each module, every artifact's path, type, required flag, and presence status; and (b) the SDK availability status and version string (when available).

**Validates: Requirements 6.1, 6.2**

### Property 7: Path Separator Normalization

*For any* artifact path string containing forward slashes, backslashes, or a mix of both, `_normalize_path` SHALL produce a `Path` that resolves to the same filesystem location regardless of which separator style was used in the input.

**Validates: Requirements 8.3**

### Property 8: Successful Assessment Exits Zero

*For any* valid manifest file and accessible project directory (regardless of which artifacts are present or missing), `main()` SHALL complete without raising an unhandled exception and exit with code 0.

**Validates: Requirements 7.4**
