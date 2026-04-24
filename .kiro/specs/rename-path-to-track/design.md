# Design: Rename "path" to "track"

## Overview

This feature performs a targeted text replacement across four bootcamp files, changing the word "path" (when it refers to learning options A–D) to "track" or "learning track." The goal is to eliminate ambiguity with file system paths in a developer-facing context.

The change is purely textual — no code logic, data models, or runtime behavior is involved. The scope is limited to four files: `onboarding-flow.md`, `POWER.md`, `agent-instructions.md`, and `session-resume.md`.

## Architecture

No architectural changes. This is a documentation-only refactor. Each file is edited in place with find-and-replace operations, guided by semantic context to distinguish "path = learning option" from "path = file system location."

## Components and Interfaces

No new components or interfaces. The affected files are Markdown steering/documentation files consumed by AI agents and bootcamp users.

### Affected Files and Change Inventory

#### 1. `senzing-bootcamp/steering/onboarding-flow.md`

| Line context | Current text | Replacement | Type |
|---|---|---|---|
| Header description | `path selection` | `track selection` | learning |
| Strict rule note | `path selection` | `track selection` | learning |
| Overview bullet | `Paths let you skip` | `Tracks let you skip` | learning |
| Pre-selection prompt | `before we choose a path` | `before we choose a track` | learning |
| Section heading | `## 5. Path Selection` | `## 5. Track Selection` | learning |
| Presentation line | `Present paths` | `Present tracks` | learning |
| Selection prompt | `Which path sounds right` | `Which track sounds right` | learning |
| Section heading | `## Switching Paths` | `## Switching Tracks` | learning |
| Switching body | `show new path requirements` | `show new track requirements` | learning |
| **enforce-feedback-path** hook name/id | UNCHANGED | — | file system |
| **enforce-feedback-path** prompt text (`file path`, `the path is different`) | UNCHANGED | — | file system |
| **Enforce Feedback File Path** hook display name | UNCHANGED | — | file system |
| **enforce-working-dir** prompt (`file path`, `any path in the file content`) | UNCHANGED | — | file system |
| **Enforce Working Directory Paths** hook display name | UNCHANGED | — | file system |

#### 2. `senzing-bootcamp/POWER.md`

| Line context | Current text | Replacement | Type |
|---|---|---|---|
| YAML keywords | `learning-path` | `learning-track` | learning |
| Quick Start intro | `Choose your path` | `Choose your track` | learning |
| Option C description | `Full learning path` | `Full learning track` | learning |
| Paths paragraph | `Paths are not mutually exclusive` | `Tracks are not mutually exclusive` | learning |
| Paths paragraph | `start with Path A` / `switch to Path C` | `start with Track A` / `switch to Track C` | learning |
| Steering file description | `path selection` | `track selection` | learning |
| Module completion description | `path completion celebration` | `track completion celebration` | learning |

#### 3. `senzing-bootcamp/steering/agent-instructions.md`

| Line context | Current text | Replacement | Type |
|---|---|---|---|
| Module Steering section | `At path end` | `At track end` | learning |
| Module transitions line | `path-completion workflow` | `track-completion workflow` | learning |

#### 4. `senzing-bootcamp/steering/session-resume.md`

| Line context | Current text | Replacement | Type |
|---|---|---|---|
| State file description | `chosen language, path, cloud provider` | `chosen language, track, cloud provider` | learning |
| Summary template | `Path: [path letter]` | `Track: [track letter]` | learning |

### Unchanged References (file system "path")

These occurrences of "path" refer to file system paths and must NOT be changed:

- `enforce-feedback-path` hook id and name
- `Enforce Feedback File Path` display name
- `file path` references in hook prompts
- `Enforce Working Directory Paths` display name
- `any path in the file content` in enforce-working-dir prompt
- `MCP-generated paths` in agent-instructions.md
- `replace those paths with project-relative equivalents` in hook prompts

## Data Models

No data models are affected. The `bootcamp_preferences.yaml` field that stores the user's chosen option is named generically (not "path"), so no config schema changes are needed.

## Error Handling

No error handling changes. This is a static text replacement with no runtime behavior.

## Testing Strategy

Property-based testing is **not applicable** to this feature. This is a pure documentation/text refactor with no code logic, no functions, no input/output behavior, and no data transformations. There are no universal properties to test across generated inputs.

**Appropriate testing approach:**

- Manual review: verify each replacement was made correctly and no file system "path" references were altered
- Grep verification: run `grep -n "\bpath\b"` on each file after changes to confirm only file-system-path occurrences remain
- Contextual spot-check: read the changed lines in context to ensure grammatical correctness and consistent terminology
