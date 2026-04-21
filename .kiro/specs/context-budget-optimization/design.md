# Design Document

## Overview

This feature changes `senzing-bootcamp/steering/module-transitions.md` from `inclusion: auto` (loaded on every interaction) to `inclusion: fileMatch` with `fileMatchPattern: "config/bootcamp_progress.json"` (loaded only when the progress file is accessed). It also adds a `description` field to the frontmatter for discoverability, and updates `senzing-bootcamp/steering/agent-instructions.md` to reflect the conditional loading behavior.

## Architecture

### Approach

This is a frontmatter-only change to `module-transitions.md` and a minor text update to `agent-instructions.md`. No content body changes are needed in either file.

### Files Modified

1. `senzing-bootcamp/steering/module-transitions.md` — replace frontmatter
2. `senzing-bootcamp/steering/agent-instructions.md` — update module transitions reference

### Change Details

**module-transitions.md frontmatter change:**

Current:
```yaml
---
inclusion: auto
---
```

New:
```yaml
---
inclusion: fileMatch
fileMatchPattern: "config/bootcamp_progress.json"
description: "Module boundary guidance: start banners, journey maps, before/after framing, step-level progress, and completion summaries. Loaded when bootcamp progress is read or written."
---
```

The body content of `module-transitions.md` (everything after the closing `---`) remains exactly as-is.

**agent-instructions.md change:**

In the "Module Steering" or module transitions reference section, update the text that references `module-transitions.md` to note it is conditionally loaded when `config/bootcamp_progress.json` is accessed, not auto-included. The specific line to update is in the "Communication" section:

Current:
```text
- At module start/completion: follow `module-transitions.md` rules. After completing any module: load `module-completion.md` for journal and path-completion workflow.
```

New:
```text
- At module start/completion: follow `module-transitions.md` rules (conditionally loaded when `config/bootcamp_progress.json` is accessed, not auto-included). After completing any module: load `module-completion.md` for journal and path-completion workflow.
```

## Correctness Properties

Since these are markdown/YAML frontmatter changes (not code), correctness is verified by example-based content checks:

1. **Frontmatter inclusion type**: `module-transitions.md` contains `inclusion: fileMatch` in its frontmatter and does not contain `inclusion: auto`
2. **Frontmatter file match pattern**: `module-transitions.md` contains `fileMatchPattern: "config/bootcamp_progress.json"` in its frontmatter
3. **Frontmatter description present**: `module-transitions.md` contains a `description` field in its frontmatter
4. **Body content preserved**: The body of `module-transitions.md` (after frontmatter) contains all original sections: "Module Start Banner", "Journey Map", "Before/After Framing", "Step-Level Progress", "Module Completion"
5. **Agent instructions updated**: `agent-instructions.md` contains text indicating `module-transitions.md` is conditionally loaded when `config/bootcamp_progress.json` is accessed
6. **Agent instructions preserved**: `agent-instructions.md` retains all existing sections: "File Placement", "MCP Rules", "MCP Failure", "Module Steering", "State & Progress", "Communication", "Hooks"
