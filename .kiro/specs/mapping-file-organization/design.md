# Design Document: Mapping File Organization

## Overview

This feature adds a single Python CLI script (`organize_mapping_files.py`) and two steering file edits. The script routes files from a flat source directory into project subdirectories based on file extension. The steering file edits instruct the bootcamp agent to invoke the script after mapping workflow steps produce output.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  mapping_workflow (MCP tool)                            │
│  Generates: .py, .md, .jsonl, .json files              │
│  Output: workspace_dir (flat)                          │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  organize_mapping_files.py                             │
│  --source <workspace_dir> --project-root <project>     │
│                                                        │
│  Routing Table:                                        │
│    .py   → scripts/                                    │
│    .md   → docs/                                       │
│    .jsonl → data/                                      │
│    .json → config/                                     │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Project Directory                                     │
│  ├── scripts/   (*.py)                                 │
│  ├── docs/      (*.md)                                 │
│  ├── data/      (*.jsonl)                              │
│  └── config/    (*.json)                               │
└─────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Organizer Script (`senzing-bootcamp/scripts/organize_mapping_files.py`)

A standalone Python CLI tool following the project's script conventions: shebang, module docstring, `from __future__ import annotations`, stdlib-only imports, argparse CLI with `main(argv=None)` signature, exit code 0/1.

### 2. Steering File Edits

Two existing steering files receive new agent instruction blocks:
- `senzing-bootcamp/steering/module-05-phase2-data-mapping.md`
- `senzing-bootcamp/steering/module-05-phase3-test-load.md`

## Interfaces

### CLI Interface

```
usage: organize_mapping_files.py [-h] [--source SOURCE] [--project-root PROJECT_ROOT] [--dry-run]

Organize mapping workflow output files into project subdirectories.

options:
  -h, --help            show this help message and exit
  --source SOURCE       Source directory to scan (default: cwd)
  --project-root PROJECT_ROOT
                        Project root for target directory resolution (default: cwd)
  --dry-run             Print planned moves without modifying the file system
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0    | Success (files moved, no files to move, or dry-run) |
| 1    | Fatal error (source directory does not exist, I/O failure) |

### Output Streams

| Stream | Content |
|--------|---------|
| stdout | Summary of moves (or "no files" message); dry-run planned moves |
| stderr | Warnings for unrouted files; notices for skipped conflicts; fatal errors |

## Data Models

### Routing Table

```python
ROUTING_RULES: dict[str, str] = {
    ".py": "scripts",
    ".md": "docs",
    ".jsonl": "data",
    ".json": "config",
}
```

The routing table is a module-level constant. Each key is a file extension (lowercase, with dot). Each value is the target subdirectory name relative to the project root.

### MoveResult Dataclass

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MoveResult:
    """Result of attempting to move a single file.

    Attributes:
        source: Original file path.
        destination: Target file path (where it would be or was moved).
        status: One of "moved", "skipped", "unrouted".
        reason: Human-readable explanation (empty for "moved").
    """

    source: Path
    destination: Path | None
    status: str
    reason: str
```

## Core Logic

### `scan_source(source_dir: Path) -> list[Path]`

Returns all regular files in `source_dir` (non-recursive, excludes directories and hidden files starting with `.`).

### `plan_moves(files: list[Path], project_root: Path) -> list[MoveResult]`

For each file:
1. Extract the extension (lowercase).
2. Look up in `ROUTING_RULES`.
3. If found: compute `destination = project_root / target_subdir / file.name`.
   - If destination already exists: status="skipped", reason="file already exists at destination".
   - Otherwise: status="moved", destination set.
4. If not found: status="unrouted", destination=None, reason="no routing rule for extension".

### `execute_moves(plan: list[MoveResult]) -> None`

For each result with status="moved":
1. Create `destination.parent` with `mkdir(parents=True, exist_ok=True)`.
2. Move the file with `shutil.move(str(source), str(destination))`.

### `print_summary(plan: list[MoveResult], dry_run: bool) -> None`

- If `dry_run`: print each planned move as `"Would move: {source.name} → {destination}"`.
- If any moves executed: print each as `"Moved: {source.name} → {destination}"`.
- If no moves and no dry-run: print `"No files required organization."`.
- For skipped files: print notice to stderr.
- For unrouted files: print warning to stderr.

### `main(argv: list[str] | None = None) -> int`

1. Parse arguments with argparse.
2. Resolve `source` and `project_root` to absolute paths.
3. Validate `source` exists and is a directory; if not, print error to stderr, return 1.
4. Call `scan_source`.
5. Call `plan_moves`.
6. If not `dry_run`: call `execute_moves`.
7. Call `print_summary`.
8. Return 0.

## Steering File Integration

### Phase 2 Instruction (module-05-phase2-data-mapping.md)

Added as an agent instruction block after step 5 (Generate starter code), where `mapping_workflow` produces output files:

```markdown
> **Agent instruction — Organize mapping output files:**
>
> After `mapping_workflow` generates output files into the workspace directory,
> run the organizer script to sort them into the correct project subdirectories:
>
> ```bash
> python3 senzing-bootcamp/scripts/organize_mapping_files.py \
>   --source <workspace_dir> \
>   --project-root <bootcamper_project_root>
> ```
>
> Where `<workspace_dir>` is the directory passed to `mapping_workflow` as
> `workspace_dir` and `<bootcamper_project_root>` is the bootcamper's project
> root directory. Review the output summary to confirm files landed correctly.
```

### Phase 3 Instruction (module-05-phase3-test-load.md)

Added as an agent instruction block after step 24 (Entity resolution evaluation), where `mapping_workflow` steps 5–8 produce output files:

```markdown
> **Agent instruction — Organize mapping output files:**
>
> After `mapping_workflow` steps 5–8 generate output files into the workspace
> directory, run the organizer script to sort them into the correct project
> subdirectories:
>
> ```bash
> python3 senzing-bootcamp/scripts/organize_mapping_files.py \
>   --source <workspace_dir> \
>   --project-root <bootcamper_project_root>
> ```
>
> Where `<workspace_dir>` is the directory passed to `mapping_workflow` as
> `workspace_dir` and `<bootcamper_project_root>` is the bootcamper's project
> root directory. Review the output summary to confirm files landed correctly.
```

## Error Handling

| Condition | Behavior |
|-----------|----------|
| `--source` path does not exist | Print error to stderr, exit 1 |
| `--source` is a file, not a directory | Print error to stderr, exit 1 |
| Target directory cannot be created (permissions) | Print error to stderr, exit 1 |
| File move fails (I/O error) | Print error to stderr, exit 1 |
| File already exists at destination | Skip, print notice to stderr, continue |
| Unrecognized extension | Leave in place, print warning to stderr, continue |
| Source directory is empty | Print "no files" message, exit 0 |

## Testing Strategy

Tests live in `senzing-bootcamp/tests/test_organize_mapping_files.py`.

- **Property-based tests** (Hypothesis): Validate universal routing, idempotence, dry-run safety, and conflict handling across generated file sets.
- **Example-based tests** (pytest): Validate CLI argument defaults, specific error messages, and steering file content.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Extension-based routing correctness

*For any* set of files with recognized extensions (`.py`, `.md`, `.jsonl`, `.json`) placed in a source directory, after running the organizer script, each file SHALL reside in the target subdirectory dictated by the routing table (`scripts/`, `docs/`, `data/`, `config/` respectively) and no longer exist in the source directory.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 2: Unrecognized extensions remain in place

*For any* file with an extension not in the routing table (not `.py`, `.md`, `.jsonl`, or `.json`), after running the organizer script, the file SHALL still exist at its original location in the source directory and stderr SHALL contain a warning identifying the file.

**Validates: Requirements 1.5**

### Property 3: Conflict detection prevents overwrite

*For any* file in the source directory whose name already exists in the corresponding target directory, the organizer script SHALL leave both the source file and the existing target file unchanged, and stderr SHALL contain a notice about the skip.

**Validates: Requirements 2.1**

### Property 4: Idempotence

*For any* source directory and file set, running the organizer script twice in succession SHALL produce the same final file layout as running it once — the second invocation makes no additional file system changes.

**Validates: Requirements 2.3**

### Property 5: Non-existent source exits with error

*For any* path that does not exist on the file system, invoking the organizer script with `--source` set to that path SHALL exit with code 1 and print an error to stderr.

**Validates: Requirements 4.6**

### Property 6: Dry-run preserves file system

*For any* source directory and file set, running the organizer script with `--dry-run` SHALL leave all files in their original locations (no moves, no directory creation beyond what already exists), exit with code 0, and print the planned moves to stdout.

**Validates: Requirements 5.1, 5.2**

### Property 7: Summary reporting completeness

*For any* successful organizer run that moves at least one file, stdout SHALL contain a line for each moved file identifying the file name and its destination. *For any* successful run that moves zero files, stdout SHALL contain a message indicating no files required organization.

**Validates: Requirements 8.1, 8.2**
