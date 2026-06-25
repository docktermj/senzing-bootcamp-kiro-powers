# Design Document

## Overview

This feature adds MCP server license guidance to Module 2 Step 5 of the `senzing-bootcamp/steering/module-02-sdk-setup.md` steering file. Two sub-steps are modified:

1. **Sub-step 5a** — A new paragraph is appended after the existing SENZ9000 explanation, informing bootcampers they can request a larger evaluation license through the Senzing MCP server.
2. **Sub-step 5c "no license" path** — A sentence is added alongside the existing email contacts, mentioning the MCP server as an additional resource for license guidance.

No other steps, sections, or structural elements of the file are modified.

## Architecture

This is a content-only change to a single markdown steering file. There are no new components, modules, or interfaces introduced.

### Change Scope

```
senzing-bootcamp/steering/module-02-sdk-setup.md
└── Step 5: Configure License
    ├── 5a. Explain the built-in evaluation license  ← ADD paragraph
    └── 5c. Handle the response
        └── "IF the bootcamper has no license:" path  ← ADD sentence
```

### Design Constraints

1. **No new URLs** — The MCP server (`mcp.senzing.com`) is already referenced elsewhere in the power. The added text references the MCP server capability generically without hardcoding tool names or new URLs.
2. **No new interaction points** — No new pointing questions (👉) or STOP instructions are introduced.
3. **Structural invariants preserved** — The file continues to satisfy all six structural properties validated by the existing test suite.

## Components

### Modified File

**File:** `senzing-bootcamp/steering/module-02-sdk-setup.md`

#### Sub-step 5a Addition

A new paragraph is inserted after the existing text about SENZ9000 and `licenses/g2.lic`. The paragraph informs bootcampers that the Senzing MCP server can provide guidance on requesting a larger evaluation license.

**Placement rule:** After the sentence ending with `placed at \`licenses/g2.lic\`.` and before sub-step 5b.

**Content guidance:**

```markdown
You can also request a larger evaluation license directly through the Senzing MCP server — it can guide you through the process without waiting for email responses.
```

#### Sub-step 5c "No License" Path Addition

A sentence is added to the existing "no license" response block, positioned alongside the email contact information. It mentions the MCP server as an alternative path for license requests.

**Placement rule:** After the `support@senzing.com` / `sales@senzing.com` mention, before the `licenses/README.md` reference.

**Content guidance:**

```markdown
Alternatively, the Senzing MCP server can guide you through requesting a larger evaluation license interactively.
```

## Data Model

No data model changes. The steering file is plain markdown with YAML frontmatter — no structured data is added or modified beyond prose content.

## Error Handling

Not applicable. This is a static content edit to a steering file. There are no runtime error paths introduced.

## Testing Strategy

### Existing Property-Based Tests (No Changes Needed)

The existing test suite at `senzing-bootcamp/tests/test_steering_structure_properties.py` validates six structural invariants across all module steering files. The modified file must continue passing all of these:

| Property | What It Validates | Requirement |
|----------|-------------------|-------------|
| Property 1: Before/After Framing | File contains `**Before/After**` section | 3.5 |
| Property 2: Step-Checkpoint | Every step has a checkpoint instruction | 3.4 |
| Property 3: Pointing Question → STOP | Every 👉 is followed by STOP/WAIT within 5 lines | 3.2 |
| Property 4: Single Question Per Step | At most one 👉 per step/sub-step | 3.3 |
| Property 5: Prerequisites Listed | File contains a Prerequisites section | 3.6 |
| Property 6: YAML Frontmatter | File starts with `inclusion: manual` frontmatter | 3.1 |

Running the existing test suite against the modified file is the primary validation mechanism for structural compliance.

### New Example-Based Tests

New example-based tests verify the content-specific requirements. These belong in a new test file `senzing-bootcamp/tests/test_licensing_guidance.py`:

1. **5a contains MCP guidance** — Assert Sub_Step_5a contains text about the MCP server and license requests (validates 1.1).
2. **5a MCP guidance positioned after SENZ9000** — Assert the MCP guidance line index is greater than the SENZ9000/500-record line index (validates 1.2).
3. **5a preserves existing content** — Assert Sub_Step_5a still contains "500 records", "SENZ9000", and "licenses/g2.lic" (validates 1.3).
4. **5c "no license" contains MCP guidance** — Assert the "no license" branch mentions the MCP server (validates 2.1).
5. **5c MCP guidance alongside email contacts** — Assert both MCP guidance and email contacts exist in the same section (validates 2.2).
6. **5c preserves existing content** — Assert the "no license" section still contains confirmation message, email contacts, `licenses/README.md`, and `bootcamp_preferences.yaml` (validates 2.3).
7. **Modifications scoped to Step 5** — Compare non-Step-5 content against baseline hash to ensure no changes (validates 4.1).
8. **No new URLs or tool names** — Scan added content for URL patterns not already present in the file (validates 4.2).
9. **No new pointing questions or STOPs in Step 5** — Count 👉 and STOP occurrences in Step 5, verify unchanged (validates 4.3).

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

The structural correctness of this change is fully covered by the existing property-based test suite. The six properties below are the existing properties that the modified file must continue satisfying. No new property-based tests are introduced because:

- There is no meaningful input variation (it's a single static file).
- The acceptance criteria are content-specific checks on known text.
- Running 100 iterations would not find more bugs than a single check.

### Property 1: YAML Frontmatter Presence

*For any* module number in the steering index, every associated steering file shall begin with YAML frontmatter containing `inclusion: manual`.

**Validates: Requirements 3.1**

### Property 2: Pointing Question Followed by STOP

*For any* module number in the steering index, and for every steering file, every pointing question (👉) shall be followed by a STOP or WAIT instruction within the next 5 non-blank lines.

**Validates: Requirements 3.2**

### Property 3: Single Question Per Sub-Step

*For any* module number in the steering index, and for every steering file, each numbered step or sub-step shall contain at most one pointing question.

**Validates: Requirements 3.3**

### Property 4: Step-Checkpoint Correspondence

*For any* module number in the steering index, and for every steering file containing numbered steps, every step shall have a corresponding checkpoint instruction.

**Validates: Requirements 3.4**

### Property 5: Before/After Framing Presence

*For any* module number in the steering index, the root steering file shall contain a `**Before/After**` framing section.

**Validates: Requirements 3.5**

### Property 6: Prerequisites Listed

*For any* module number in the steering index, the root steering file shall contain a Prerequisites section.

**Validates: Requirements 3.6**
