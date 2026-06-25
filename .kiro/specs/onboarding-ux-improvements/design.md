# Design Document

## Overview

This design covers two targeted content changes to existing steering files in the senzing-bootcamp power: adding a hook files explanatory note to `onboarding-flow.md` and adding an exploration gate to `entity-resolution-intro.md`. No new files, scripts, or infrastructure are introduced — only markdown content edits.

## Architecture

Both changes are purely additive content insertions into existing steering files. The architecture is unchanged — the onboarding flow continues to load `entity-resolution-intro.md` via `#[[file:]]` reference during Step 4a, and the overall steering file structure remains intact.

### Affected Files

| File | Change Type | Location |
|------|-------------|----------|
| `senzing-bootcamp/steering/onboarding-flow.md` | Insert paragraph | Step 4 Overview_Bullets, after "unfamiliar terms" bullet |
| `senzing-bootcamp/steering/entity-resolution-intro.md` | Insert mandatory gate section | After "What entity resolution produces" section, before Sources comment |

## Components and Interfaces

### Component 1: Hook Files Note (onboarding-flow.md)

**Location:** Step 4 of `onboarding-flow.md`, as the last bullet in the overview list (after the "unfamiliar terms" bullet and before `### 4a`).

**Content structure:**

```markdown
- If you noticed hook files (like `.kiro.hook` files) appearing in your editor panel during setup — those are automated quality checks that run in the background. They do not require your review. You can safely close them, but please do not delete them — they help maintain code quality throughout the bootcamp.
```

**Design decisions:**

- The note is a standard list item (bullet point) to match the existing Overview_Bullets format.
- No mandatory gate (⛔) or stop instruction is included — the flow continues seamlessly to section 4a.
- The tone matches the existing conversational style of the overview bullets.
- The note uses "hook files" and ".kiro.hook files" to connect what the bootcamper sees in the editor panel to the concept.

### Component 2: Exploration Gate (entity-resolution-intro.md)

**Location:** After the "What entity resolution produces" section content and before the `## Sources` comment block.

**Content structure:**

```markdown
## Explore Further

<!-- AGENT INSTRUCTION — not shown to the bootcamper.
This is a mandatory gate. The agent MUST stop here and wait for the
bootcamper to either ask follow-up questions or signal readiness to proceed.

Handling rules:
- If the bootcamper asks a follow-up question: answer it using search_docs
  from the Senzing MCP server, then re-present this gate.
- If the bootcamper signals readiness to proceed (e.g., "ready", "let's go",
  "continue", "next"): allow the flow to continue to the next section.
- If the bootcamper provides an ambiguous response: treat it as a follow-up
  question, attempt to answer it using MCP tools, then re-present this gate.
-->

⛔ **MANDATORY GATE** — Entity Resolution Exploration

That covers the foundations of entity resolution. Before we move on, this is a good moment to dig deeper if anything sparked your curiosity.

Here are some questions other bootcampers have found useful:

- "How does Senzing match records without rules?"
- "What's the difference between matching and relating?"
- "What kinds of data does entity resolution work with?"

You can ask any question about entity resolution — not just these examples. When you're ready to move on, just say so.

🛑 **STOP — End your response here.** Do not proceed. Do not assume a response. Wait for the bootcamper's real input.
```

**Design decisions:**

- Uses the established `⛔ MANDATORY GATE` pattern consistent with other gates in `onboarding-flow.md` (e.g., programming language selection in Step 2).
- Agent instructions are wrapped in an HTML comment block (`<!-- -->`) following the existing convention in `entity-resolution-intro.md`.
- The gate explicitly handles three response types: follow-up question, readiness signal, and ambiguous response.
- MCP tool usage (`search_docs`) is specified for answering questions, consistent with the file's existing MCP-first approach.
- The gate re-presents itself after answering a question, creating a loop until the bootcamper explicitly exits.
- Example questions are chosen to cover different aspects: mechanism (how matching works), concepts (matching vs relating), and scope (data types).

### Steering File Conventions Used

| Convention | Application |
|------------|-------------|
| `⛔ MANDATORY GATE` | Marks the exploration gate as a hard stop requiring bootcamper input |
| `🛑 STOP` | Explicit stop instruction for the agent |
| `<!-- AGENT INSTRUCTION -->` | Hidden agent-only instructions not shown to bootcamper |
| `#[[file:]]` reference | Existing mechanism that loads entity-resolution-intro.md into onboarding-flow.md |
| Bullet list format | Hook files note matches existing Overview_Bullets style |

No programmatic interfaces or data models are introduced. Both changes are static markdown content consumed by the Kiro agent at steering-file load time.

## Data Models

No data models are introduced. The changes are static markdown content with no structured data, configuration files, or persistent state.

## Error Handling

### Component 1: Hook Files Note

No error handling needed — the note is informational content with no conditional logic or agent actions.

### Component 2: Exploration Gate

| Scenario | Handling |
|----------|----------|
| Bootcamper asks a question but MCP is unreachable | The MCP health check in Step 0b guarantees connectivity. If MCP fails mid-session, standard MCP error handling applies (outside this feature's scope). |
| Bootcamper provides ambiguous response | Treated as a follow-up question per requirement 2.6 — agent attempts to answer using MCP tools, then re-presents the gate. |
| Bootcamper wants to skip without engaging | Any readiness signal ("ready", "next", "continue", "let's go") exits the gate immediately. |

## Testing Strategy

All acceptance criteria for this feature are best verified with example-based tests rather than property-based tests. The changes are static markdown content edits — there is no input space to vary, no transformations to round-trip, and no universal properties that hold "for all inputs."

**Recommended tests (example-based):**

1. **Hook files note position** — Parse `onboarding-flow.md` and verify the hook files note appears after the "unfamiliar terms" bullet and before `### 4a`.
2. **Hook files note content** — Verify the note mentions automated quality checks, safe to close, and must not delete.
3. **No gate before 4a** — Verify no ⛔ or 🛑 markers exist between the hook files note and `### 4a`.
4. **Exploration gate position** — Parse `entity-resolution-intro.md` and verify the ⛔ gate exists after the last content section and before the Sources comment.
5. **Exploration gate content** — Verify the gate contains example questions, agent instructions for MCP usage, stop instruction, and ambiguous response handling.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

No property-based tests are appropriate for this feature. The changes are static markdown content edits to steering files — declarative configuration rather than functions with inputs and outputs. There is no input space to vary, no transformations to round-trip, and no universal properties that hold "for all inputs." All criteria are verified through example-based tests described in the Testing Strategy section above.
