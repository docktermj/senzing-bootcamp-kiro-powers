# Design: Guided Rollback with Diff Preview

## Overview

The `rollback_module.py` script gains a `--preview` mode that shows what would change before executing. The agent uses this to present rollback consequences conversationally, building confidence in using rollback as a learning tool.

## Preview Output Format

```
$ python rollback_module.py --preview 6

Rollback Preview: Module 6 (Loading Data)
══════════════════════════════════════════

Files to be deleted:
  src/load/load.py                    (2.1 KB)
  src/load/redo_processor.py          (1.4 KB)
  logs/load_2026-05-01.log            (0.8 KB)

Files to be reverted (backup available):
  config/data_sources.yaml            → backup from 2026-04-30 14:22

Progress entries to be cleared:
  bootcamp_progress.json: current_module 6→5, step_history["6"] removed

Data source registry changes:
  config/data_sources.yaml: load_status reset to "not_loaded" for all sources

⚠️  Irreversible actions (no backup):
  src/load/load.py — will be permanently deleted

Safety Assessment:
  Backed up: 1 of 4 files (25%)
  Fully reversible: No

Downstream impact:
  ⚠️  Module 7 artifacts depend on Module 6 outputs
  Files at risk: src/query/query.py (from Module 7)

No changes made. Use --yes to execute, or run without --preview for interactive mode.
```

## Implementation Changes to rollback_module.py

### New Arguments
```python
parser.add_argument("--preview", "--dry-run", action="store_true",
                    help="Show what would change without making modifications")
parser.add_argument("--yes", "-y", action="store_true",
                    help="Skip confirmation prompt (for non-interactive use)")
```

### Execution Flow

```
rollback_module.py <module_number>
    │
    ├─ Compute rollback plan (always)
    │   ├─ Files to delete (from module's output directories)
    │   ├─ Files to revert (if backup exists)
    │   ├─ Progress entries to clear
    │   ├─ Registry entries to update
    │   └─ Downstream impact analysis
    │
    ├─ --preview? → Display plan, exit 0
    │
    ├─ --yes? → Execute immediately
    │
    └─ Interactive? → Display plan, ask confirmation, execute or abort
```

### Rollback Plan Data Structure

```python
@dataclass
class RollbackPlan:
    module: int
    files_to_delete: list[tuple[str, int]]  # (path, size_bytes)
    files_to_revert: list[tuple[str, str]]  # (path, backup_timestamp)
    progress_changes: list[str]              # human-readable descriptions
    registry_changes: list[str]             # human-readable descriptions
    irreversible: list[str]                 # paths with no backup
    downstream_impact: list[str]            # warnings about dependent modules
    backup_path: str | None                 # path to most recent backup if exists
    backup_timestamp: str | None            # ISO 8601 of backup
```

### Downstream Impact Detection

Read `config/module-dependencies.yaml` (or `module-artifacts.yaml` if available) to identify modules that depend on the one being rolled back. Check if those modules have artifacts on disk.

## Agent Integration

The `module-completion.md` steering file instructs the agent:

```markdown
### Rollback Offer

When the bootcamper asks to redo or rollback a module:
1. Run `rollback_module.py --preview <N>` to get the impact summary
2. Present the results conversationally:
   - "Rolling back Module 6 would remove 3 files and reset your loading progress."
   - "One file has no backup and would be permanently deleted."
   - "Module 7 artifacts also depend on Module 6 outputs."
3. Ask: 👉 "Want me to proceed with the rollback, or would you prefer to keep your current progress?"
4. If confirmed, run `rollback_module.py --yes <N>`
```

## Files Modified

- `senzing-bootcamp/scripts/rollback_module.py` — add --preview, --yes flags and plan computation
- `senzing-bootcamp/steering/module-completion.md` — update rollback offer instructions

## Testing

- Unit test: --preview flag accepted by argparse
- Unit test: --yes flag accepted by argparse
- Unit test: --preview always exits with code 0
- Unit test: preview output contains "No changes made" footer
- Unit test: downstream impact detection finds dependent modules
- Property test: rollback plan for any valid module number produces a valid plan structure
- Integration test: --preview followed by --yes produces same file list
