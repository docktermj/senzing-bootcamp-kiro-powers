# Design: Git Initialization Question Should Indicate It's Optional

## Overview

This feature updates the Module 1 Step 1 steering file to reword the git initialization question so it explicitly states the step is optional and can be skipped without affecting the bootcamp. This is a single-line wording change in one steering file.

## Architecture

### Affected Files

| File | Change Type | Purpose |
|------|-------------|---------|
| `senzing-bootcamp/steering/module-01-business-problem.md` | Modify | Update the git init question wording in Step 1 to include "optional" indicator |

### Design Rationale

The fix is minimal — a wording change to the question text. The existing logic (check if workspace is already a git repo, ask if not, act on response) remains unchanged. Only the question phrasing changes to set expectations.

### Updated Question Wording

Current: "Would you like me to initialize a git repository for version control?"

New: "👉 This is optional, but would you like me to initialize a git repository for version control? You can skip this without affecting the bootcamp."

The 👉 marker is preserved (or added if missing) to ensure the ask-bootcamper hook correctly detects this as a pending question.

## Components and Interfaces

### Component 1: Step 1 Question Text Update

In `module-01-business-problem.md`, locate the Step 1 git initialization question and replace the question text with the updated wording that includes the "optional" indicator and the reassurance that skipping won't affect the bootcamp.

## Data Models

No data model changes.

## Error Handling

Not applicable — this is a wording change only.

## Testing Strategy

- Verify the updated question text contains the word "optional"
- Verify the updated question text contains reassurance about not affecting the bootcamp
- Verify the 👉 marker is present on the question
- Verify no other content in Step 1 is changed
