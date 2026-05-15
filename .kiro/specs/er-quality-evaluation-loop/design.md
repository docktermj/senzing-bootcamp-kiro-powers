# Design: Entity Resolution Quality Evaluation Loop

## Overview

Add a structured quality evaluation step to Module 7 (`module-07-query-validation.md`) that uses the MCP `reporting_guide(topic='quality')` tool to help bootcampers assess entity resolution quality. When quality is marginal or poor, provide a guided feedback loop back to Module 5 for mapping refinement — preserving Module 6/7 progress so the bootcamper can reload and re-evaluate without losing work.

## Architecture

### Quality Evaluation Flow

```text
Module 7: Query & Visualize
    │
    ├─ Step 3a: Run exploratory queries (existing)
    │
    ├─ NEW Step 3d: Quality Evaluation
    │   │
    │   ├─ Call reporting_guide(topic='quality') for methodology
    │   ├─ Call search_docs(query='entity resolution quality evaluation')
    │   ├─ Present quality indicators to bootcamper
    │   │
    │   ├─ ACCEPTABLE → proceed to visualizations (step 3b)
    │   ├─ MARGINAL → review specific entities, then decide
    │   └─ POOR → guided path back to Module 5
    │       │
    │       ├─ Preserve Module 6/7 progress
    │       ├─ Identify which sources/features need remapping
    │       └─ Return to Module 5 Phase 2 (data mapping)
    │
    └─ Step 3b/3c: Visualizations (existing, renumbered if needed)
```

### Insertion Point

The quality evaluation step is inserted **after Step 3a** (exploratory queries + matching concepts) and **before Step 3b** (entity graph visualization). This is the natural point where the bootcamper has seen their results and can assess quality before investing in visualizations.

The new step will be **Step 3d** (placed between 3a and the existing 3b) to avoid renumbering existing steps. The ordering becomes: 3a → 3d → 3b → 3c.

Wait — that's confusing. Better approach: insert as a new numbered step. Looking at the current structure:

- Step 3a: Present query results and matching concepts
- Step 3b: Entity graph visualization checkpoint
- Step 3c: Results dashboard visualization checkpoint

The quality evaluation should go between 3a and 3b. We'll insert it as **Step 3b** and renumber the existing 3b→3c and 3c→3d. This keeps the logical flow: results → evaluate quality → visualize.

**Final step ordering:**
- Step 3a: Present query results and matching concepts (existing)
- Step 3b: Quality evaluation (NEW)
- Step 3c: Entity graph visualization checkpoint (was 3b)
- Step 3d: Results dashboard visualization checkpoint (was 3c)

## Quality Indicators

The evaluation step presents these indicators to the bootcamper:

| Indicator | What It Means | How to Compute |
|-----------|---------------|----------------|
| Entity-to-record ratio | How much deduplication occurred | entity_count / record_count (closer to 1.0 = less matching) |
| Possible match count | Entities that might be the same but need review | Query for possible matches via SDK |
| Cross-source match rate | How many entities span multiple sources | Entities with records from 2+ sources / total entities |
| Split signals | Same real entity split into multiple Senzing entities | Look for entities with very similar features but different IDs |
| Merge signals | Different real entities incorrectly merged | Look for entities with conflicting features (e.g., different DOBs) |

The agent uses `reporting_guide(topic='quality')` to get the authoritative methodology for computing these indicators, then presents them in a summary table.

## Quality Thresholds

| Assessment | Criteria | Action |
|------------|----------|--------|
| **Acceptable** | Entity-to-record ratio is reasonable for the data, possible matches < 5% of entities, no obvious split/merge signals | Proceed to visualizations |
| **Marginal** | Possible matches 5-15% of entities, OR some split/merge signals detected | Review specific entities with the bootcamper, then decide |
| **Poor** | Possible matches > 15% of entities, OR clear split/merge patterns, OR entity-to-record ratio is unexpectedly close to 1.0 (no matching happening) | Guided path back to Module 5 |

These thresholds are advisory — the bootcamper always has the final say on whether to proceed or iterate.

## Module 7→5 Feedback Loop

### Preserving Progress

When the bootcamper returns to Module 5 for remapping:

1. **Module 6/7 progress is NOT rolled back** — `config/bootcamp_progress.json` retains the completed status for Modules 6 and 7
2. **The database is NOT deleted** — the loaded data stays in place
3. **Module 5 is re-entered at Phase 2** (data mapping) — not Phase 1 (quality assessment), since the issue is mapping, not raw data quality
4. **After remapping**, the bootcamper returns to Module 6 to reload the affected source(s), then back to Module 7 to re-evaluate

### Specific Recommendations

When quality is poor, the agent provides specific guidance:

- **Which data sources** need remapping (based on which sources contribute to problematic entities)
- **Which features** are causing issues (e.g., "NAME_FULL is not being matched because records use different name formats — consider mapping to NAME_FIRST + NAME_LAST instead")
- **What to look for** in the remapping (e.g., "The split pattern suggests addresses aren't being compared — check if ADDRESS fields are mapped")

These recommendations come from analyzing the query results and calling `search_docs(query='split merge detection')` for authoritative guidance.

## Changes Required

### 1. `module-07-query-validation.md` — New Step 3b

Insert after Step 3a, before the existing visualization checkpoints:

```markdown
3b. **Quality evaluation:**

   > **Agent instruction:** Call `reporting_guide(topic='quality', language='<chosen_language>', version='current')` to get the quality evaluation methodology. Then call `search_docs(query='entity resolution quality evaluation', version='current')` for additional context on interpreting results.

   Present a quality summary to the bootcamper:

   | Indicator | Value | Assessment |
   |-----------|-------|------------|
   | Entity-to-record ratio | [computed] | [interpretation] |
   | Possible matches | [count] ([%] of entities) | [interpretation] |
   | Cross-source match rate | [%] | [interpretation] |

   **Quality assessment:**

   - **Acceptable** (proceed): Ratio is reasonable, possible matches < 5%, no split/merge signals
   - **Marginal** (review): Possible matches 5-15% or some split/merge signals detected
   - **Poor** (iterate): Possible matches > 15%, clear split/merge patterns, or no matching occurring

   Based on the assessment:

   - **Acceptable:** "Your entity resolution quality looks good. Let's proceed to visualizations."
   - **Marginal:** "I see some potential issues. Let me show you a few specific entities to review." [Present examples, then ask if they want to proceed or iterate]
   - **Poor:** "The entity resolution results suggest mapping improvements would help. Here's what I recommend..." [Present specific recommendations and offer the Module 5 feedback loop]

   **Module 5 feedback loop (when quality is poor or bootcamper requests iteration):**

   👉 "Would you like to return to Module 5 to refine your data mapping? Your loaded data and query programs will be preserved — after remapping, you'll reload the affected sources and re-evaluate here."

   If accepted:
   1. Note which data sources need remapping in `config/bootcamp_progress.json` under a `quality_iteration` key
   2. Set `current_module` to 5 and `current_step` to the Phase 2 start step
   3. Load `module-05-data-quality-mapping.md` and begin at Phase 2

   **Checkpoint:** Write step 3b to `config/bootcamp_progress.json`.
```

### 2. Renumber Existing Steps

- Existing Step 3b (entity graph visualization) → Step 3c
- Existing Step 3c (results dashboard visualization) → Step 3d
- Update all checkpoint references accordingly

### 3. `module-transitions.md` — Backward Transition

Add a new section documenting the quality feedback loop:

```markdown
## Quality Feedback Loop (Module 7 → Module 5)

When entity resolution quality is assessed as marginal or poor in Module 7, the bootcamper may return to Module 5 for mapping refinement. This is a valid backward transition that preserves progress:

- Module 6/7 completion status is retained in `config/bootcamp_progress.json`
- The database and loaded data are NOT deleted
- Module 5 is re-entered at Phase 2 (data mapping), not Phase 1
- After remapping, the bootcamper reloads affected sources (Module 6) and re-evaluates (Module 7)
- The `quality_iteration` key in progress tracks which sources triggered the loop

This transition does NOT require track switching or rollback — it's an iterative refinement within the normal bootcamp flow.
```

### 4. Tests

Create `senzing-bootcamp/tests/test_er_quality_evaluation.py` verifying:

1. Module 7 steering contains a quality evaluation step
2. The step references `reporting_guide(topic='quality')`
3. The step references `search_docs` for authoritative context
4. Quality thresholds are defined (acceptable/marginal/poor)
5. Module 5 feedback loop instructions exist
6. Progress preservation is documented
7. `module-transitions.md` contains the backward transition documentation

## Integration Points

### Files to Modify

| File | Change |
|------|--------|
| `senzing-bootcamp/steering/module-07-query-validation.md` | Add Step 3b (quality evaluation), renumber 3b→3c and 3c→3d |
| `senzing-bootcamp/steering/module-transitions.md` | Add Quality Feedback Loop section |

### Files to Create

| File | Purpose |
|------|---------|
| `senzing-bootcamp/tests/test_er_quality_evaluation.py` | Unit tests verifying steering file content |

### Existing Files Referenced (No Changes)

| File | Relevance |
|------|-----------|
| `module-05-data-quality-mapping.md` | Target of the feedback loop (Phase 2 re-entry) |
| `module-06-load-data.md` | Reload step after remapping |
| `config/bootcamp_progress.json` | Stores quality_iteration tracking |

## Correctness Properties

1. **Non-destructive evaluation**: The quality evaluation step never modifies data, database, or progress — it only reads and presents.
2. **Bootcamper autonomy**: Thresholds are advisory. The bootcamper always decides whether to proceed or iterate.
3. **Progress preservation**: Returning to Module 5 never deletes Module 6/7 artifacts or progress.
4. **MCP-sourced methodology**: Quality evaluation methodology comes from `reporting_guide`, not training data.
5. **Deterministic step ordering**: The new step has a fixed position (after 3a, before visualizations) regardless of quality assessment outcome.

## Constraints

- No new Python scripts — this is purely steering file content
- Quality indicators are computed by the agent using SDK queries (via `generate_scaffold` or direct SDK calls), not by a standalone script
- The `reporting_guide(topic='quality')` MCP tool provides the methodology; the agent applies it to the bootcamper's data
- Token budget impact: the new step adds ~400-500 tokens to `module-07-query-validation.md` — well within the 5000-token split threshold (current file is 2,193 tokens)
