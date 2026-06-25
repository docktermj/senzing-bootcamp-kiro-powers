# Design Document

## Overview

This feature applies three targeted fixes to the Module 3 Phase 2 visualization steering file (`senzing-bootcamp/steering/module-03-phase2-visualization.md`). All changes are markdown content edits and CSS specification changes within that single file. No new files are created; no code logic changes.

The fixes address:

1. **Phase 2 skip prevention** — Add an enforcement block before Step 9 that explicitly prohibits the agent from skipping Phase 2.
2. **Entity Graph viewport height** — Replace the fixed 600px graph container height with `calc(100vh - 120px)` for full viewport utilization.
3. **Post-launch guided tour** — Add instructions for the agent to deliver a structured text-based walkthrough after the visualization launches.

## Architecture

### Single-File Edit Strategy

All three fixes modify `senzing-bootcamp/steering/module-03-phase2-visualization.md`. The changes are additive (new sections) or substitutive (replacing a CSS value). No structural reorganization of the file is needed.

```text
module-03-phase2-visualization.md
├── YAML frontmatter (unchanged)
├── # Module 3 Phase 2 heading (unchanged)
├── Purpose / Prerequisites / Pattern sources (unchanged)
├── Implementation constraints (unchanged)
├── CRITICAL LESSONS section (unchanged)
├── ⚠️ ENFORCEMENT BLOCK (NEW — Fix 1)
├── ## Step 9: Web Service + Visualization Page
│   ├── 9.1 Generate Web Service (unchanged)
│   ├── 9.2 API Endpoints (unchanged)
│   ├── 9.3 Visualization Page Components
│   │   └── Entity_Graph section → height: calc(100vh - 120px) (Fix 2)
│   └── 9.4 Start and Verify Web Service
│       ├── ... verification steps (unchanged)
│       ├── Present to bootcamper (unchanged)
│       ├── 🗺️ GUIDED TOUR (NEW — Fix 3)
│       └── 🛑 STOP block (unchanged)
└── Checkpoint (unchanged)
```

## Components and Interfaces

### Component 1: Enforcement Block

**Location:** Inserted after the "CRITICAL LESSONS FOR VISUALIZATION GENERATION" section and before "## Step 9".

**Format:**

```markdown
---

## ⚠️ DO NOT SKIP — Phase 2 Execution Is Mandatory

> **🚨 This phase is MANDATORY. It is NOT optional.**
>
> Phase 2 visualization generation MUST be executed in full.
> DO NOT SKIP this phase. DO NOT transition to Module 4 until
> Phase 2 is complete and the bootcamper has confirmed they
> have explored the visualization.
>
> Skipping Phase 2 deprives the bootcamper of their first
> "wow moment" with entity resolution results.

---
```

**Design rationale:**

- The `## ⚠️` heading with emoji provides a visual marker (Req 1.4)
- "DO NOT SKIP" appears in uppercase (Req 1.1)
- "MANDATORY" and "NOT optional" language (Req 1.2, 1.5)
- Explicit Module 4 transition prohibition (Req 1.3)
- Blockquote formatting draws visual attention
- Horizontal rules above and below isolate the block

### Component 2: Graph Container Height Fix

**Location:** Within section 9.3, the Entity_Graph tab description where the graph container height is specified.

**Change:** Replace any fixed pixel height specification for the graph container with viewport-relative sizing.

**Before (current implicit 600px in the generated HTML):**

```css
#graph-container {
  height: 600px;
}
```

**After:**

```css
#graph-container {
  height: calc(100vh - 120px);
}
```

The steering file must specify this CSS value in the Entity_Graph section so the agent generates the correct height. The 120px offset accounts for:

- Fixed header: ~50px
- Summary banner: ~40px
- Tab navigation: ~30px

**Design rationale:**

- `calc(100vh - 120px)` fills the remaining viewport (Req 2.1)
- The 120px breakdown is documented for maintainability (Req 2.2)
- No fixed pixel height remains for the graph container (Req 2.3)

### Component 3: Post-Launch Guided Tour

**Location:** Within section 9.4, inserted after the URL presentation ("Your visualization is running...") and before the "🛑 STOP" block.

**Format:**

```markdown
**Guided Tour — deliver the following as a single structured chat message
(no interactive pauses):**

Present this guided tour to the bootcamper immediately after confirming
the URL is accessible:

---

🗺️ **What You're Looking At — A Quick Tour**

**Entity Graph tab (default view):**
- **Cross-source matches:** Nodes with multiple colors represent entities
  resolved across data sources (e.g., a CUSTOMERS record matched to a
  REFERENCE record). These are Senzing's highest-value findings.
- **Name variations:** Senzing resolves name variants automatically —
  look for entities like "Robert Smith" that merged records originally
  entered as "Bob Smith" or "R. Smith".
- **Relationship edges:** Lines between nodes show relationships.
  The labels (e.g., +NAME+ADDRESS, +PHONE) are match keys — they tell
  you which features Senzing used to link those entities.

**Merge Statistics tab:**
- The **records-per-entity histogram** shows how many records collapsed
  into each entity. A tall "1" bar means many unique entities; bars at
  "2", "3", "4+" show where Senzing found duplicates across sources.

---
```

**Design rationale:**

- Delivered as a single structured message, no pauses (Req 3.6)
- Describes cross-source matches (Req 3.2)
- Describes name variations with examples (Req 3.3)
- Describes relationship edges and match key labels (Req 3.4)
- Describes the records-per-entity histogram (Req 3.5)
- Positioned after URL presentation, before STOP block (Req 3.7)
- Instructed to present after verification passes (Req 3.1)

### Interfaces

No programmatic interfaces are introduced. All changes are markdown content that instructs the agent's behavior. The steering file's existing YAML frontmatter (`inclusion: manual`) remains unchanged.

## Data Models

No data models are introduced. The steering file is a static markdown document.

## Error Handling

No runtime error handling applies. The steering file is consumed by the agent at execution time. If the enforcement block is ignored by the agent, that is a behavioral issue outside the scope of this file edit — the enforcement block uses the strongest available language patterns to minimize that risk.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Enforcement block completeness

*For any* enforcement block extracted from the steering file (the section between the CRITICAL LESSONS section and Step 9), it SHALL contain all of the following elements: (a) the phrase "DO NOT SKIP" in uppercase, (b) the word "MANDATORY" in uppercase, (c) language prohibiting transition to Module 4, (d) at least one visual marker (emoji character or bold markdown formatting), and (e) language stating Phase 2 is not optional.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

### Property 2: Graph container uses viewport-relative height

*For any* CSS height specification associated with the graph container in the steering file, the value SHALL be a viewport-relative expression (containing `vh`) and SHALL NOT be a fixed pixel value matching the pattern `\d+px`.

**Validates: Requirements 2.1, 2.3**

### Property 3: Guided tour content completeness

*For any* guided tour section in the steering file (the structured tour block between URL presentation and the STOP block), it SHALL contain references to all four required topics: (a) cross-source matches, (b) name variations, (c) relationship edges with match key labels, and (d) the records-per-entity histogram in the Merge Statistics tab.

**Validates: Requirements 3.2, 3.3, 3.4, 3.5**

### Property 4: Guided tour structural ordering

*For any* valid state of the steering file, the guided tour section SHALL appear after the URL presentation text (containing "localhost" or "running") and before the STOP block (containing "🛑 STOP"), and SHALL specify single-message delivery with no interactive pauses.

**Validates: Requirements 3.6, 3.7**

## Testing Strategy

### Property-Based Tests (Hypothesis)

Tests parse the actual steering file content and verify structural/content properties hold. The strategies generate indices into extracted sections (similar to the existing `test_visualization_enforcement_properties.py` pattern in this project).

**Test file:** `senzing-bootcamp/tests/test_module3_visualization_fixes_properties.py`

Key approach:
- Parse the steering file at module load time
- Extract the enforcement block, graph container section, and guided tour section
- Use `st.sampled_from()` strategies over extracted sections
- Each property test class validates one design property with `@settings(max_examples=100)`

### Example-Based Tests (pytest)

**Test file:** `senzing-bootcamp/tests/test_module3_visualization_fixes_unit.py`

Covers:
- Exact `calc(100vh - 120px)` string presence (Req 2.1)
- 120px offset explanation mentions header, banner, tab navigation (Req 2.2)
- Guided tour appears after verification step (Req 3.1)
- No `600px` string in graph container context (Req 2.3)
