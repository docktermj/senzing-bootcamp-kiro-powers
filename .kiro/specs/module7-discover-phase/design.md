# Design Document

## Overview

This design adds a "Discover" phase to Module 7 (Query, Visualize & Discover) that introduces bootcampers to advanced Senzing capabilities — why analysis, how analysis, relationship networks, and data-specific visualizations — using concrete examples from their own loaded data.

The Discover phase is inserted as step 4 (with sub-steps 4a–4e) after the existing visualization checkpoints (steps 3c/3d) and before the Query Completeness Gate. It is opt-in: the bootcamper can decline or exit early at any point. Each sub-step has its own checkpoint for session resumption.

## Architecture

### Module 7 Step Flow (Updated)

```
Step 1:  Define query requirements
Step 2:  Create query programs
Step 3a: Present query results and matching concepts
Step 3b: Quality evaluation
Step 3c: Entity graph visualization checkpoint
Step 3d: Results dashboard visualization checkpoint
Step 4:  Discover Phase (NEW)
  4a: Data pattern analysis
  4b: Why analysis introduction
  4c: How analysis introduction
  4d: Relationship network exploration
  4e: Data-specific visualization suggestions
Query Completeness Gate (updated to include Discover phase status)
```

### Steering File Strategy

The existing `module-07-query-visualize-discover.md` is currently 2,971 tokens — well under the 5,000-token split threshold. Adding the Discover phase will push it significantly over that threshold. Following the pattern used by modules 3, 5, 6, 8, 9, 10, and 11, the Discover phase will be extracted into a separate phase file:

- **Root file:** `module-07-query-visualize-discover.md` — retains steps 1–3d, adds a brief step 4 entry that references the phase file, updates the Query Completeness Gate and Success Criteria
- **Phase file:** `module-07-phase2-discover.md` — contains the full Discover phase implementation (steps 4a–4e)

This keeps the root file under the split threshold and allows the agent to load the Discover phase only when needed.

### Steering Index Update

The `steering-index.yaml` entry for module 7 changes from a simple string reference to a phased structure:

```yaml
7:
  root: module-07-query-visualize-discover.md
  phases:
    phase1-query-visualize:
      file: module-07-query-visualize-discover.md
      token_count: <measured>
      size_category: large
      step_range: [1, "3d"]
    phase2-discover:
      file: module-07-phase2-discover.md
      token_count: <measured>
      size_category: large
      step_range: ["4a", "4e"]
```

## Components

### 1. New Phase File: `module-07-phase2-discover.md`

**Location:** `senzing-bootcamp/steering/module-07-phase2-discover.md`

This file contains the full Discover phase implementation with the following structure:

```markdown
---
inclusion: manual
---

# Module 7 — Phase 2: Discover

> **Phase file:** This file implements Step 4 (Discover Phase) of Module 7.
> Load when the agent reaches step 4 in `module-07-query-visualize-discover.md`.
> When complete, return to the root file for the Query Completeness Gate.

## Step 4: Discover Phase — Advanced Senzing Capabilities

### Introduction and Opt-in

[Present brief intro, ask bootcamper if they want to proceed]

### Step 4a: Data Pattern Analysis

[Analyze loaded data, identify interesting entities for demonstrations]
[Checkpoint: write step 4a to bootcamp_progress.json]

### Step 4b: Why Analysis Introduction

[Demonstrate why_entities/why_records with concrete cross-source entity]
[Use SZ_INCLUDE_FEATURE_SCORES + SZ_INCLUDE_MATCH_KEY_DETAILS flags]
[Explain output in plain language: features, scores, matching principles]
[Checkpoint: write step 4b to bootcamp_progress.json]

### Step 4c: How Analysis Introduction

[Demonstrate how_entity with multi-record entity (3+ records)]
[Use SZ_INCLUDE_FEATURE_SCORES flag]
[Present as chronological narrative of entity construction]
[Explain difference between why and how analysis]
[Checkpoint: write step 4c to bootcamp_progress.json]

### Step 4d: Relationship Network Exploration

[Demonstrate find_network and find_path with related entities]
[Explain network structure, shared attributes, degrees of separation]
[Graceful fallback if no relationships exist in data]
[Checkpoint: write step 4d to bootcamp_progress.json]

### Step 4e: Data-Specific Visualization Suggestions

[Suggest 2+ visualizations tailored to bootcamper's data]
[Catalog: cross-source heatmap, entity size distribution, network graph,
 match key frequency, feature score distribution]
[Generate if bootcamper selects one, using visualization-guide.md]
[Checkpoint: write step 4e to bootcamp_progress.json]
```

### 2. Root File Updates: `module-07-query-visualize-discover.md`

Add the following after step 3d and before the Query Completeness Gate:

```markdown
4. **Discover Phase — Advanced Senzing Capabilities**:

   > **Phase file:** Load `module-07-phase2-discover.md` for the full Discover
   > phase — data pattern analysis, why/how analysis, relationship networks,
   > and data-specific visualization suggestions.

   The Discover phase introduces advanced Senzing capabilities using concrete
   examples from the bootcamper's loaded data. It is opt-in — the bootcamper
   can decline or exit early at any demonstration point.

   **Checkpoint:** Steps 4a–4e each write individually to
   `config/bootcamp_progress.json`.
```

Update the Success Criteria to add:
```markdown
- ✅ Discover phase completed or explicitly skipped
```

Update the Query Completeness Gate to add:
```markdown
3. **Discover phase status?** — The Discover phase was either completed
   (all steps 4a–4e checkpointed) or explicitly skipped by the bootcamper.
```

### 3. Checkpoint Schema

Each Discover phase step writes to `config/bootcamp_progress.json` under the module 7 section:

```json
{
  "module_7_query": {
    "steps": {
      "4a": {"status": "completed", "patterns_found": {"multi_record": 5, "cross_source": 3, "relationships": 2}},
      "4b": {"status": "completed", "entity_demonstrated": 1234},
      "4c": {"status": "completed", "entity_demonstrated": 5678},
      "4d": {"status": "completed|skipped", "reason": "no_relationships"},
      "4e": {"status": "completed|skipped", "visualizations_offered": 2}
    },
    "discover_phase": "completed|skipped|in_progress"
  }
}
```

### 4. Session Resumption

The phase file includes a session resumption instruction at the top:

```markdown
> **Agent instruction (session resumption):** On load, read
> `config/bootcamp_progress.json` and check which step 4x sub-steps are
> already completed. Resume from the first incomplete step. Do not re-run
> completed demonstrations.
```

### 5. Early Exit Flow

At the end of each demonstration (4b, 4c, 4d, 4e), the agent asks:

```text
Would you like to continue to the next demonstration, or proceed to module completion?
```

If the bootcamper chooses to exit:
1. Write `discover_phase: "skipped"` (or partial completion status) to progress
2. Return to root file for the Query Completeness Gate
3. The gate accepts both "completed" and "skipped" as valid states

### 6. Data Pattern Analysis Strategy (Step 4a)

The agent uses these SDK calls to find demonstration candidates:

1. **Multi-record entities:** Iterate over loaded records using `get_entity_by_record_id`, collect entities with `record_count >= 3`
2. **Cross-source entities:** From the multi-record entities, filter for those with records from 2+ data sources
3. **Relationship clusters:** From entities found, check for disclosed relationships using relationship flags

If insufficient data patterns exist (fewer than 2 multi-record entities), the agent adapts:
- Uses whatever entities are available
- Explains limitations to the bootcamper
- Skips demonstrations that require unavailable patterns (e.g., skip relationship networks if no relationships exist)

### 7. SDK Flag Usage

| Method | Required Flags | Purpose |
|--------|---------------|---------|
| `why_entities` | `SZ_INCLUDE_FEATURE_SCORES`, `SZ_INCLUDE_MATCH_KEY_DETAILS` | Full scoring detail for why analysis |
| `why_records` | `SZ_INCLUDE_FEATURE_SCORES`, `SZ_INCLUDE_MATCH_KEY_DETAILS` | Full scoring detail for why analysis |
| `how_entity` | `SZ_INCLUDE_FEATURE_SCORES` | Scoring at each construction step |
| `find_network` | Look up via `get_sdk_reference(method='find_network', topic='flags')` | Relationship exploration |
| `find_path` | Look up via `get_sdk_reference(method='find_path', topic='flags')` | Path finding |

The agent explains each flag choice to the bootcamper: "I'm using [flag] so we can see [what it provides]."

### 8. Visualization Suggestions Catalog

Step 4e draws from this catalog, selecting suggestions relevant to the bootcamper's data:

| Visualization | When to Suggest | What It Reveals |
|---------------|-----------------|-----------------|
| Cross-source overlap heatmap | 2+ data sources loaded | Which sources share the most entities |
| Entity size distribution chart | Any data | Distribution of records per entity (singletons vs. large merges) |
| Relationship network graph | Relationships exist | How entities connect through shared attributes |
| Match key frequency analysis | Multi-record entities exist | Which feature combinations drive most resolutions |
| Feature score distribution | Multi-record entities exist | How closely features match across resolved records |

If the bootcamper selects a visualization, the agent generates it using `visualization-guide.md` patterns and the bootcamper's chosen language.

## Unchanged Components

- Steps 1–3d in the root steering file — unchanged except for minor formatting to accommodate the new step 4 reference
- `visualization-guide.md` — unchanged, referenced by step 4e for generation
- `visualization-web-service.md` — unchanged
- Existing hooks (`enforce-visualization-offers`) — unchanged, already covers module 7
- `hook-categories.yaml` — no new hooks needed (existing `enforce-visualization-offers` covers the Discover phase visualization offers)
- Other module steering files — unchanged

## Testing Strategy

1. **CommonMark validation:** Both the updated root file and new phase file must pass `validate_commonmark.py`
2. **Power structure validation:** `validate_power.py` must pass with the new file
3. **Steering index accuracy:** `measure_steering.py --check` must pass after token count updates
4. **Hook registry sync:** `sync_hook_registry.py --verify` must pass (no new hooks, but registry must still be in sync)
5. **Existing tests:** `pytest` must pass — no existing tests should break from adding a new steering file

## Token Budget Considerations

The current module 7 file is 2,971 tokens. The root file update (adding step 4 reference + gate updates) will add approximately 200–300 tokens, keeping it well under the 5,000-token split threshold.

The new phase file (`module-07-phase2-discover.md`) will be approximately 3,000–4,000 tokens based on the detail required for 5 sub-steps with agent instructions, SDK flag guidance, and checkpoint definitions. This is within the "large" size category but under the split threshold.
