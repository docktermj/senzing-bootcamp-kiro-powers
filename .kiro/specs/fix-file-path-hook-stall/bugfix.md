# Bugfix Requirements Document

## Introduction

The `enforce-file-path-policies` preToolUse hook intercepts every write operation (`fs_write`, `fs_append`, `str_replace`) to enforce path policies. When no policy is violated, the hook contract requires zero output and the agent must retry the original tool call. In practice, after several rapid no-op intercepts during a multi-file edit, the agent drops the thread and stops making progress. The bootcamper sees a silent stall with no error or explanation, requiring them to manually prompt the agent to continue.

The root causes are: (1) the hook intercepts unconditionally even when there is no signal of a policy concern, creating cumulative attention cost; (2) the zero-output success convention requires an inferential step that fails under load; and (3) the agent-instructions.md hook silence rule does not explicitly mandate retry after a no-violation intercept.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the hook intercepts a write to a project-relative path with no external path references AND multiple such intercepts occur in rapid succession THEN the agent emits a no-op acknowledgment and stops without retrying the original tool call

1.2 WHEN the hook intercepts a write to a project-relative path with no policy violation THEN the hook still fires and consumes an agent decision cycle even though no action is needed

1.3 WHEN the agent drops the thread after a no-op intercept THEN the bootcamper sees silence with no error message, no explanation, and no indication of what happened

1.4 WHEN the hook produces zero output after a compliant write THEN the agent has no explicit signal to retry and must infer the retry requirement from contract documentation

### Expected Behavior (Correct)

2.1 WHEN a write targets a project-relative path AND the content contains no external path references (`/tmp/`, `%TEMP%`, `~/Downloads`) AND the write is not feedback content directed to a non-canonical path THEN the hook SHALL NOT intercept at all (the write proceeds without triggering the hook)

2.2 WHEN the hook does intercept a write and determines no policy is violated THEN the hook output SHALL include an explicit pass signal (e.g., "policy: pass") confirming the agent should retry the original tool call immediately

2.3 WHEN the agent receives a hook intercept that does not explicitly deny access THEN the agent SHALL immediately retry the original tool call with the same parameters without emitting any acknowledgment or commentary

2.4 WHEN the hook intercepts and identifies a real policy violation THEN the hook SHALL produce actionable output describing the violation and the required correction (existing behavior, preserved)

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a write targets a path outside the working directory (e.g., `/tmp/foo.py`, `~/Downloads/bar.txt`) THEN the system SHALL CONTINUE TO intercept and block the write with a corrective message

3.2 WHEN feedback content is being written to a path other than `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` THEN the system SHALL CONTINUE TO intercept and redirect to the canonical feedback path

3.3 WHEN file content references external paths (`/tmp/`, `%TEMP%`, `~/Downloads`) THEN the system SHALL CONTINUE TO intercept and require replacement with project-relative equivalents

3.4 WHEN a write targets a project-relative path with no policy concerns AND the hook does not fire THEN the write SHALL CONTINUE TO succeed normally as if no hook existed

3.5 WHEN the hook identifies a violation and produces corrective output THEN the agent SHALL CONTINUE TO follow the corrective instructions rather than retrying the original call
