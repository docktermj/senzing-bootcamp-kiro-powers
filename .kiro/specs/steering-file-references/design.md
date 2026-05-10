# Design Document

## Overview

This enhancement adds `#[[file:]]` references to two manual steering workflow files (`add-new-module.md` and `add-new-script.md`) so that the Kiro agent automatically receives critical context files when those workflows are activated. The third workflow file (`validation-suite.md`) remains unchanged because it already contains all necessary information inline.

The change is purely additive — inserting reference lines into existing Markdown files. No executable logic, no new files, no configuration changes.

## Architecture

No architectural changes. The existing Kiro file-reference mechanism (`#[[file:path]]`) handles context injection at activation time. This design simply identifies which files should be referenced from which steering files, applying context-budget guardrails to avoid bloating the agent's token window.

### Decision: Which files to reference

The decision framework for each candidate file:

| Question | Yes → | No → |
|----------|-------|------|
| Does the agent need to **read** the file's content to execute the workflow? | Reference it | Don't reference |
| Is the file under 200 lines? | Safe to reference | Only reference if full content is essential |
| Does the agent only **run** the file (not read/modify)? | Don't reference | — |

Applied to the candidate files:

| File | Lines | Agent needs content? | Decision |
|------|-------|---------------------|----------|
| `senzing-bootcamp/config/module-dependencies.yaml` | ~95 | Yes — find next module number, understand prerequisites | **Reference** from `add-new-module.md` |
| `senzing-bootcamp/steering/module-prerequisites.md` | ~75 | Yes — update the prerequisites table | **Reference** from `add-new-module.md` |
| `.kiro/steering/python-conventions.md` | ~50 | Yes — write conforming scripts | **Reference** from `add-new-script.md` |
| `senzing-bootcamp/steering/steering-index.yaml` | ~300 | No — agent only appends an entry | **Exclude** (too large, partial read suffices) |
| `senzing-bootcamp/scripts/lint_steering.py` | ~1000+ | No — agent only runs it | **Exclude** (execute-only, too large) |
| `senzing-bootcamp/scripts/measure_steering.py` | ~500+ | No — agent only runs it | **Exclude** (execute-only) |

## Components and Interfaces

### Component: `add-new-module.md` (modified)

**Current state:** References `module-dependencies.yaml` and `module-prerequisites.md` by path in prose but does not use `#[[file:]]` syntax.

**Target state:** Two `#[[file:]]` lines inserted after frontmatter, before the first heading:

```markdown
---
inclusion: manual
description: "Step-by-step workflow for adding a new bootcamp module"
---

#[[file:senzing-bootcamp/config/module-dependencies.yaml]]
#[[file:senzing-bootcamp/steering/module-prerequisites.md]]

# Workflow: Add a New Bootcamp Module
```

**Rationale:** The agent needs the full dependency graph to determine the next available module number and understand prerequisite chains. It needs the prerequisites table to add the new module's row.

### Component: `add-new-script.md` (modified)

**Current state:** References `python-conventions.md` by name in step 1 but does not use `#[[file:]]` syntax.

**Target state:** One `#[[file:]]` line inserted after frontmatter, before the first heading:

```markdown
---
inclusion: manual
description: "Step-by-step workflow for adding a new Python script to the power"
---

#[[file:.kiro/steering/python-conventions.md]]

# Workflow: Add a New Script
```

**Rationale:** The agent needs the full conventions document to generate scripts that conform to project patterns (shebang, imports, argparse structure, test patterns, style rules).

### Component: `validation-suite.md` (unchanged)

**Rationale:** This workflow only runs scripts via shell commands. The agent doesn't need to read any script implementations — it just executes them and interprets output. All commands and fix instructions are already inline.

## Data Models

No data models. This enhancement modifies Markdown content only.

## Error Handling

No runtime error handling applies. Potential failure modes during implementation:

| Failure | Mitigation |
|---------|-----------|
| Referenced file path is wrong | Use workspace-root-relative paths; validate with `validate_power.py` which checks cross-references |
| Referenced file grows beyond budget | Context budget guardrails in requirements prevent referencing files >200 lines without justification; current referenced files are well under limit |
| Frontmatter parsing breaks | Place references on their own lines after the closing `---`, separated by a blank line from the heading |

## Testing Strategy

**PBT does not apply.** This is a documentation enhancement — no executable logic is introduced or modified. There are no functions, no data transformations, no algorithms to test with property-based testing.

**Validation approach:**

1. **Power integrity check** — Run `python senzing-bootcamp/scripts/validate_power.py` to verify that all `#[[file:]]` references point to files that exist in the workspace.

2. **Steering lint** — Run `python senzing-bootcamp/scripts/lint_steering.py` to verify structural conformance of the modified steering files (frontmatter present, valid Markdown).

3. **Manual review** — Confirm that activating each workflow in Kiro loads the expected referenced file content into context.

4. **Token budget check** — Run `python senzing-bootcamp/scripts/measure_steering.py --check` to verify that the modified files remain within their token budgets (the references themselves are small; the referenced content is loaded separately by Kiro at activation time and does not count toward the steering file's own token measurement).
