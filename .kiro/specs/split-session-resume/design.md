# Design Document: Split Session Resume

## Overview

This feature restructures the monolithic `session-resume.md` steering file (~4,661 tokens) into a phase-1 root file and three concern-specific phase-2 files. The restructuring reduces context window consumption on the happy path by loading only the phase-1 file (~2,000 tokens) and conditionally loading phase-2 files only when their specific recovery scenarios are detected.

## Architecture

The architecture follows the existing phase-splitting pattern established by modules 1, 3, 5, 6, 8, 9, 10, and 11 in `steering-index.yaml`.

The key architectural decision is **conditional loading via routing logic**: the phase-1 file contains inline logic that evaluates session state and determines which (if any) phase-2 files to load. This differs from module phase-splitting (which uses step ranges) because session-resume phases are triggered by detected conditions rather than sequential progress.

### File Structure

```
senzing-bootcamp/steering/
├── session-resume.md                      # Phase-1 root (~2,000 tokens)
├── session-resume-phase2-mapping.md       # Mapping recovery (~900 tokens)
├── session-resume-phase2-state-repair.md  # State repair (~700 tokens)
└── session-resume-phase2-setup-recovery.md # Setup recovery (~650 tokens)
```

## Components and Interfaces

### Component 1: Phase-1 Root File (`session-resume.md`)

**Responsibility:** Fast-path evaluation, happy-path inline flow, routing logic, and non-recovery steps.

**Content allocation:**

| Section | Source (Original) | Rationale |
|---------|-------------------|-----------|
| YAML frontmatter (`inclusion: manual`) | Preserved | Required for agent file selection |
| Fast Path Check (5 boolean conditions + skip logic) | Fast Path Check section | Core routing decision — always needed |
| Step 1: Read All State Files | Step 1 (excluding hook check detail) | State loading is always needed on non-fast-path |
| Step 2: Load Language Steering | Step 2 | Always needed on non-fast-path |
| Step 2b: Behavioral Rules Reload | Step 2b | Inline on both fast-path and full path |
| Step 2c: Restore Conversation Style | Step 2c | Inline on both fast-path and full path |
| Step 3: Summarize and Confirm | Step 3 (excluding mapping checkpoint detail) | Always needed — the welcome-back banner |
| Step 4: Load the Right Module Steering | Step 4 (excluding mapping checkpoint validation) | Module loading is always needed |
| Step 5: Re-establish MCP Context | Step 5 | Always needed |
| Routing Logic block | New section | Evaluates conditions and directs phase-2 loading |

**Excluded from Phase-1 (moved to phase-2 files):**
- Mapping checkpoint validation procedure (→ Phase_2_Mapping)
- Mapping resume options and fast-track logic (→ Phase_2_Mapping)
- Hook installation logic detail (→ Phase_2_Setup_Recovery)
- MCP Health Check probe/failure path (→ Phase_2_Setup_Recovery)
- What's New Notification logic (→ Phase_2_Setup_Recovery)
- Handling Stale or Corrupted State procedure (→ Phase_2_State_Repair)

### Component 2: Phase-2 Mapping File (`session-resume-phase2-mapping.md`)

**Responsibility:** All mapping checkpoint recovery logic.

**Content allocation:**

| Section | Source (Original) | Rationale |
|---------|-------------------|-----------|
| Guard condition | New | Skip if loaded unnecessarily |
| Checkpoint validation procedure | Step 4 (mapping checkpoint subsection) | JSON parsing, field checks, MCP status call |
| Resume options presentation | Step 3 (mapping checkpoint subsection) | Resume/Restart/Skip options |
| Fast-track-through-completed-steps | Step 4 (mapping fast-track subsection) | Valid checkpoint resume logic |
| Corrupted checkpoint handling | Step 4 (cases 4 and 5) | Invalid/corrupted checkpoint restart offer |

### Component 3: Phase-2 State Repair File (`session-resume-phase2-state-repair.md`)

**Responsibility:** Stale or corrupted progress state handling.

**Content allocation:**

| Section | Source (Original) | Rationale |
|---------|-------------------|-----------|
| Guard condition | New | Skip if loaded unnecessarily |
| Handling Stale or Corrupted State | "Handling Stale or Corrupted State" section | Artifact scanning, discrepancy reporting, correction |
| Progress reconstruction from artifacts | Step 1 fallback paragraph | Missing/corrupted progress file recovery |

### Component 4: Phase-2 Setup Recovery File (`session-resume-phase2-setup-recovery.md`)

**Responsibility:** Hook installation, MCP health check, and What's New notification.

**Content allocation:**

| Section | Source (Original) | Rationale |
|---------|-------------------|-----------|
| Guard condition | New | Skip if loaded unnecessarily |
| Hook installation logic | Step 1, item 2b (hook check subsection) | Hook Registry reading, createHook calls, failure handling |
| Step 2d: MCP Health Check | Step 2d | Probe call, success/failure paths, troubleshooting |
| Step 2e: What's New Notification | Step 2e | CHANGELOG parsing, display logic |

## Routing Logic Design

The routing logic is a new section in the Phase-1 file that evaluates conditions and directs phase-2 file loading. It sits between the Fast Path Check and Step 1.

### Evaluation Model

```
┌─────────────────────────────────────────────────┐
│           Phase-1 File Loaded                    │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │  Fast Path Check                          │   │
│  │  All 5 conditions met? ──YES──→ Step 2b/2c/3│ │
│  │         │ NO                              │   │
│  └─────────┼────────────────────────────────┘   │
│            ▼                                     │
│  ┌──────────────────────────────────────────┐   │
│  │  Routing Logic (evaluate ALL conditions)  │   │
│  │                                           │   │
│  │  1. State repair condition?               │   │
│  │     - progress.json invalid JSON          │   │
│  │     - current_module inconsistent         │   │
│  │     → Load session-resume-phase2-         │   │
│  │       state-repair.md                     │   │
│  │                                           │   │
│  │  2. Setup recovery condition?             │   │
│  │     - hooks_installed missing/empty       │   │
│  │     - preferences missing/corrupted       │   │
│  │     - MCP health check fails             │   │
│  │     - show_whats_new + session_log        │   │
│  │     → Load session-resume-phase2-         │   │
│  │       setup-recovery.md                   │   │
│  │                                           │   │
│  │  3. Mapping condition?                    │   │
│  │     - mapping_state_*.json exists         │   │
│  │     → Load session-resume-phase2-         │   │
│  │       mapping.md                          │   │
│  │                                           │   │
│  │  (All conditions evaluated independently) │   │
│  └──────────────────────────────────────────┘   │
│            ▼                                     │
│  Step 1 → Step 2 → [Phase-2 content] →          │
│  Step 2b → Step 2c → Step 3 → Step 4 → Step 5   │
└─────────────────────────────────────────────────┘
```

### Evaluation Order

Conditions are evaluated in this fixed order:
1. **State repair** — checked first because corrupted state affects all other evaluations
2. **Setup recovery** — checked second because missing hooks/MCP affect the session
3. **Mapping** — checked third because it's the most specific recovery scenario

### Independent Evaluation

All three conditions are evaluated regardless of whether earlier conditions triggered. This enables compound recovery (e.g., corrupted state AND missing hooks are both detected and both phase-2 files are loaded).

### Guard Conditions in Phase-2 Files

Each phase-2 file begins with a guard condition block:

```markdown
## Guard Condition

If this file was loaded but none of the following conditions are true,
skip all content below and return to the Phase-1 flow:
- [specific conditions for this file]
```

This ensures that if a phase-2 file is loaded unnecessarily (e.g., due to a race condition or stale evaluation), the agent skips its content without executing instructions.

## Steering Index Registration

The `steering-index.yaml` registration follows the existing `onboarding` pattern (non-module entries with `root` and `phases`):

```yaml
session-resume:
  root: session-resume.md
  phases:
    phase1-fast-path:
      file: session-resume.md
      token_count: 2000  # measured after implementation
      size_category: large
    phase2-mapping:
      file: session-resume-phase2-mapping.md
      token_count: 900   # measured after implementation
      size_category: medium
    phase2-state-repair:
      file: session-resume-phase2-state-repair.md
      token_count: 700   # measured after implementation
      size_category: medium
    phase2-setup-recovery:
      file: session-resume-phase2-setup-recovery.md
      token_count: 650   # measured after implementation
      size_category: medium
```

The `file_metadata` section gets three new entries and the existing `session-resume.md` entry gets its `token_count` updated to reflect the reduced size.

The `keywords` section remains unchanged — `resume` continues to map to `session-resume.md` (the Phase-1 root).

## Token Budget Analysis

| File | Estimated Tokens | Budget Category |
|------|-----------------|-----------------|
| Phase-1 (session-resume.md) | ~2,000 | large |
| Phase-2 Mapping | ~900 | medium |
| Phase-2 State Repair | ~700 | medium |
| Phase-2 Setup Recovery | ~650 | medium |
| **Total (all loaded)** | **~4,250** | — |
| **Original monolithic** | **4,661** | large |

The total across all files is slightly less than the original because:
- Redundant context-setting prose is consolidated
- Guard conditions add minimal overhead (~20 tokens each)
- The routing logic block replaces implicit ordering with explicit conditions

**Happy-path savings:** On the fast path (all conditions clean), only ~2,000 tokens are consumed instead of 4,661 — a ~57% reduction.

## Content Migration Rules

1. **No content duplication** — Each instruction from the original appears in exactly one split file
2. **Cross-references replace inline content** — Where the Phase-1 file previously contained recovery logic inline, it now contains a brief reference: "See session-resume-phase2-{concern}.md for [description]"
3. **Step numbering preserved** — Steps 1–5 retain their original numbers in the Phase-1 file for backward compatibility with `phase-loading-guide.md` references
4. **Frontmatter preserved** — Only the Phase-1 file has `inclusion: manual` frontmatter; phase-2 files have no frontmatter (they are loaded programmatically by the agent, not by the inclusion system)

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Phase-2 file missing from disk | Agent logs warning, continues with Phase-1 flow only. Recovery logic is skipped but session resumes. |
| Phase-2 file loaded but guard condition not met | Agent skips phase-2 content, returns to Phase-1 flow |
| Multiple phase-2 files triggered | All triggered files loaded in evaluation order (state repair → setup recovery → mapping) |
| Routing logic cannot evaluate a condition (e.g., file read error) | Treat condition as triggered (fail-open for recovery files) |

## Data Models

### Session State Model (Routing Input)

The routing logic evaluates a session state composed of these elements:

| Field | Source | Type | Used By |
|-------|--------|------|---------|
| `progress_json_valid` | `config/bootcamp_progress.json` parseable | boolean | State repair condition |
| `current_module_consistent` | `current_module` matches project artifacts | boolean | State repair condition |
| `preferences_valid` | `config/bootcamp_preferences.yaml` parseable | boolean | Setup recovery condition |
| `hooks_installed` | `hooks_installed` key in preferences | string[] or null | Setup recovery condition |
| `mcp_probe_result` | MCP `search_docs` call result | success/failure | Setup recovery condition |
| `show_whats_new` | `show_whats_new` in preferences | boolean | Setup recovery condition |
| `session_log_exists` | `config/session_log.jsonl` exists | boolean | Setup recovery condition |
| `mapping_state_files` | `config/mapping_state_*.json` glob | string[] | Mapping condition |

### Routing Output Model

```yaml
load_set:
  - file: session-resume-phase2-state-repair.md    # if state repair triggered
  - file: session-resume-phase2-setup-recovery.md  # if setup recovery triggered
  - file: session-resume-phase2-mapping.md         # if mapping triggered
```

### Steering Index Entry Model

```yaml
session-resume:
  root: session-resume.md
  phases:
    phase1-fast-path:
      file: string           # filename
      token_count: integer   # measured token count
      size_category: string  # small|medium|large
    phase2-mapping:
      file: string
      token_count: integer
      size_category: string
    phase2-state-repair:
      file: string
      token_count: integer
      size_category: string
    phase2-setup-recovery:
      file: string
      token_count: integer
      size_category: string
```

## Testing Strategy

### Unit Tests (Example-Based)

Content allocation and structural checks are verified with example-based tests:

- **Token budget compliance**: Measure each file's token count against its budget ceiling (2200, 1000, 800, 700)
- **Section presence**: Verify each file contains its required sections (fast-path check, Step 2b, routing logic, etc.)
- **Content exclusion**: Verify Phase-1 does NOT contain mapping checkpoint validation logic
- **Frontmatter preservation**: Verify `inclusion: manual` in Phase-1 only
- **Steering index structure**: Verify `session-resume` entry has correct shape with all four files
- **Keyword mapping**: Verify `resume` still maps to `session-resume.md`

### Property Tests

Property-based tests validate routing correctness and content completeness across generated session states (see Correctness Properties below).

### Integration Tests

- **MCP health check routing**: Mock MCP failure and verify setup recovery is triggered
- **Behavioral equivalence**: Load all four files simultaneously and verify the combined instruction set matches the original

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Routing Correctness

*For any* session state (defined by the existence and content of `config/bootcamp_progress.json`, `config/bootcamp_preferences.yaml`, `config/mapping_state_*.json`, and `config/session_log.jsonl`), the set of phase-2 files directed for loading by the routing logic SHALL equal exactly the set of phase-2 files whose trigger conditions are satisfied by that state. Specifically:
- If `mapping_state_*.json` files exist → mapping file is in the load set
- If `bootcamp_progress.json` is invalid JSON or has inconsistent `current_module` → state repair file is in the load set
- If `hooks_installed` is missing/empty, preferences are missing/corrupted, MCP probe fails, or `show_whats_new` conditions are met → setup recovery file is in the load set
- If none of the above → the load set is empty (only Phase-1 is used)

**Validates: Requirements 2.5, 3.3, 3.4, 4.4, 4.5, 4.7, 5.1, 5.2, 8.1**

### Property 2: Content Completeness (No Instruction Loss)

*For any* instruction block present in the original monolithic `session-resume.md`, that instruction block SHALL appear in exactly one of the four split files (Phase-1, Phase-2 Mapping, Phase-2 State Repair, or Phase-2 Setup Recovery). No instruction is duplicated across files and no instruction is omitted.

**Validates: Requirements 7.1, 7.3**

### Property 3: Routing Section Completeness

*For any* phase-2 file in the set {`session-resume-phase2-mapping.md`, `session-resume-phase2-state-repair.md`, `session-resume-phase2-setup-recovery.md`}, the routing logic section in the Phase-1 file SHALL contain at least one explicit loading condition that references that file by name.

**Validates: Requirements 1.5, 5.3**
