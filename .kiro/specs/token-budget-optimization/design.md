# Design Document

## Overview

Split `module-07-phase2-discover.md` at the step 4c/4d boundary into two files, update `steering-index.yaml` and the root module file, then validate with `measure_steering.py --check`.

This is a content-redistribution operation — no new logic, no new scripts, no behavioral changes. The design focuses on what content goes where and how references are updated.

## Architecture

### File Layout (after split)

```
senzing-bootcamp/steering/
├── module-07-query-visualize-discover.md   # Root file (updated reference)
├── module-07-phase2-discover.md            # Part A: steps 4a–4c
├── module-07-phase2b-discover.md           # Part B: steps 4d–4e (new file)
└── steering-index.yaml                     # Updated entries + token counts
```

### Split Boundary

The original file is split at the `---` separator between step 4c's checkpoint and step 4d's heading:

| File | Content |
|------|---------|
| Part A (`module-07-phase2-discover.md`) | Frontmatter, intro, opt-in, step 4a, step 4b, step 4c, navigation footer |
| Part B (`module-07-phase2b-discover.md`) | Frontmatter, continuation header, step 4d, step 4e, Discover Phase Completion |

## Components and Interfaces

### Part A File Structure

```markdown
---
inclusion: manual
---

# Module 7 — Phase 2: Discover (Part A)

> **Phase file:** ... Load when agent reaches step 4 ...
> When steps 4a–4c are complete, load `module-07-phase2b-discover.md` for steps 4d–4e.

> **Agent instruction (session resumption):** On load, read
> `config/bootcamp_progress.json` ...

## Step 4: Discover Phase — Advanced Senzing Capabilities
### Introduction and Opt-in
### Step 4a: Data Pattern Analysis
### Step 4b: Why Analysis Introduction
### Step 4c: How Analysis Introduction

---
**Next:** Load `module-07-phase2b-discover.md` for steps 4d–4e ...
```

### Part B File Structure

```markdown
---
inclusion: manual
---

# Module 7 — Phase 2: Discover (Part B)

> **Phase file:** ... Load after completing steps 4a–4c in `module-07-phase2-discover.md`.
> When complete, return to the root file for the Query Completeness Gate.

> **Agent instruction (session resumption):** On load, read
> `config/bootcamp_progress.json` ...

### Step 4d: Relationship Network Exploration
### Step 4e: Data-Specific Visualization Suggestions
### Discover Phase Completion
```

### Root File Reference Update

In `module-07-query-visualize-discover.md`, step 4's phase file instruction becomes:

```markdown
> **Phase files:** Load `module-07-phase2-discover.md` for steps 4a–4c
> (data pattern analysis, why analysis, how analysis). Then load
> `module-07-phase2b-discover.md` for steps 4d–4e (relationship networks,
> visualization suggestions, and Discover Phase Completion).
```

### Steering Index Changes

**Module 7 phases section** — replace single `phase2-discover` with two entries:

```yaml
  7:
    root: module-07-query-visualize-discover.md
    phases:
      phase1-query-visualize:
        file: module-07-query-visualize-discover.md
        token_count: 3183
        size_category: large
        step_range: [1, "3d"]
      phase2a-discover:
        file: module-07-phase2-discover.md
        token_count: <measured>
        size_category: large
        step_range: ["4a", "4c"]
      phase2b-discover:
        file: module-07-phase2b-discover.md
        token_count: <measured>
        size_category: large
        step_range: ["4d", "4e"]
```

**file_metadata section** — two entries replace one:

```yaml
  module-07-phase2-discover.md:
    token_count: <measured>
    size_category: large
  module-07-phase2b-discover.md:
    token_count: <measured>
    size_category: large
```

**budget.total_tokens** — recomputed by `measure_steering.py` (sum of all file token counts).

### Token Counting

Token count formula (from `measure_steering.py`):

```python
def calculate_token_count(filepath: Path) -> int:
    content = filepath.read_text(encoding="utf-8")
    return round(len(content) / 4)
```

Size classification:

```python
def classify_size(token_count: int) -> str:
    if token_count < 500:
        return "small"
    elif token_count <= 2000:
        return "medium"
    else:
        return "large"
```

### Validation Interface

```bash
python senzing-bootcamp/scripts/measure_steering.py --check
```

Exit code 0 = all stored token counts within 10% of measured values. Exit code 1 = mismatch detected.

## Data Models

No new data models. Existing structures:

- **Steering file**: Markdown with YAML frontmatter (`inclusion: manual`)
- **steering-index.yaml**: Module phases (file, token_count, size_category, step_range), file_metadata, budget
- **bootcamp_progress.json**: Checkpoint structure unchanged (steps 4a–4e write individually)

## Error Handling

| Scenario | Handling |
|----------|----------|
| Part A or Part B exceeds 5,000 tokens | Adjust split boundary (move content between files) |
| `measure_steering.py --check` fails | Run `measure_steering.py` (update mode) to refresh stored counts, then re-check |
| Root file reference doesn't match actual filenames | CI catches via steering-index validation |

## Testing Strategy

- **Property tests** (Hypothesis): Validate content preservation, token budget compliance, and index consistency using generated steering file content.
- **Example tests** (pytest): Verify the actual split files contain expected sections, frontmatter, navigation instructions, and cross-references.
- **Smoke test**: Run `measure_steering.py --check` to confirm end-to-end consistency between stored and measured token counts.

No hook files are modified — constraint 4.1/4.2 verified by asserting no `.kiro.hook` or `hook-categories.yaml` files appear in the changeset.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Content preservation across split

*For any* valid steering file split at a section boundary, the concatenation of Part A body content and Part B body content (excluding added navigation boilerplate and duplicate frontmatter) SHALL contain every agent instruction line, checkpoint block, and success criterion present in the original file.

**Validates: Requirements 5.1**

### Property 2: Token budget compliance

*For any* steering file produced by a split operation, its measured token count (round(len(content) / 4)) SHALL be strictly less than the `split_threshold_tokens` value (5,000).

**Validates: Requirements 1.5, 1.6**

### Property 3: Steering index consistency

*For any* steering file listed in `file_metadata`, the stored `token_count` SHALL be within 10% of the value computed by `calculate_token_count` on the actual file, and `budget.total_tokens` SHALL equal the sum of all `file_metadata` token counts.

**Validates: Requirements 2.3, 2.4**
