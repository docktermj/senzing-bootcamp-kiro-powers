# Requirements: Git Initialization Question Should Indicate It's Optional

## Introduction

In Module 1, Step 1, the agent asks "Would you like me to initialize a git repository for version control?" without indicating that this step is optional and can be skipped without any impact on the rest of the bootcamp.

## What Happened

The question does not indicate that this step is optional. The bootcamper may feel pressured to set up git even if they don't want or need it for the bootcamp. It's unclear whether skipping it will cause issues later.

## Why It's a Problem

Without the "optional" label, the bootcamper may feel pressured to set up git even if they don't want or need it. It's unclear whether skipping it will cause issues later in the bootcamp.

## Acceptance Criteria

1. The git initialization question in Module 1 Step 1 SHALL explicitly state that the step is optional
2. The question wording SHALL make clear that skipping git initialization will not affect the rest of the bootcamp (e.g., "This is optional, but would you like me to initialize a git repository for version control? You can skip this without affecting the bootcamp.")
3. The steering file `module-01-business-problem.md` Step 1 SHALL contain the updated question wording with the optional indicator
4. The existing behavior of actually initializing git when the bootcamper says "yes" SHALL be preserved unchanged
5. The existing behavior of skipping git initialization when the workspace is already a git repository SHALL be preserved unchanged

## Reference

- Source: `SENZING_BOOTCAMP_POWER_FEEDBACK.md` — "Git initialization question should indicate it's optional"
- Module: 1 (Business Problem) | Priority: High | Category: UX
