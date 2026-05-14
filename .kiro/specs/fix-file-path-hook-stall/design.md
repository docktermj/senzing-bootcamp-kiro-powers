# Fix File Path Hook Stall — Bugfix Design

## Overview

The `enforce-file-path-policies` preToolUse hook intercepts every write operation (`fs_write`, `fs_append`, `str_replace`) to check two path policies. When no policy is violated, the hook's prompt instructs the agent to "produce no output at all — zero tokens, zero characters." The agent must then infer from the hook silence rule in `agent-instructions.md` that it should retry the original tool call. Under load (rapid multi-file edits), this inferential step fails — the agent emits a no-op acknowledgment and stops, causing a silent stall visible to the bootcamper.

The fix makes the hook discriminating (only intercepts when there's a real signal of concern) and adds an explicit pass signal when it does intercept but finds no violation, eliminating the inferential gap that causes stalls.

## Glossary

- **Bug_Condition (C)**: The agent drops the thread after a no-op hook intercept during a multi-file edit because the zero-output convention requires an inferential retry step that fails under cumulative attention load
- **Property (P)**: The hook either does not intercept at all (common case: project-relative path, no suspicious content) or produces an explicit "policy: pass" signal that unambiguously tells the agent to retry
- **Preservation**: Existing violation detection (external paths, feedback path enforcement, content path references) continues to intercept and block with corrective messages
- **Hook Prompt**: The `then.prompt` field in `enforce-file-path-policies.kiro.hook` — the instructions the agent evaluates on each write intercept
- **Agent Instructions**: `senzing-bootcamp/steering/agent-instructions.md` — the always-loaded steering file containing the hook silence rule
- **Discriminating Intercept**: A hook that only fires when pre-screening detects a signal of concern, rather than intercepting unconditionally

## Bug Details

### Bug Condition

The bug manifests when the agent performs a multi-file edit (e.g., building a web service with server.py, index.html, graph.js) and the hook intercepts each write in rapid succession. Each intercept is a no-op (project-relative path, no external references), but the cumulative attention cost of evaluating the hook prompt and remembering the zero-output retry contract causes the agent to drop the thread.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type WriteInterceptContext
  OUTPUT: boolean

  RETURN input.hookId == "enforce-file-path-policies"
         AND input.targetPath IS project-relative
         AND input.content DOES NOT CONTAIN external_path_references
         AND input.isNotFeedbackContent
         AND input.interceptCount >= 3  -- cumulative load threshold
         AND input.hookOutput == ""     -- zero output (no violation)
         AND agent.nextAction == NONE   -- agent stopped instead of retrying
END FUNCTION
```

### Examples

- **Multi-file build, 5th write**: Agent writes `src/web_service/server.py`, hook intercepts, no violation, zero output. Agent writes `src/web_service/static/index.html`, hook intercepts, no violation, zero output. By the 5th file, agent emits "I'll continue" but never retries. **Expected**: Hook doesn't intercept at all for project-relative paths with no suspicious content.
- **Single write, project-relative**: Agent writes `src/transform/mapper.py`, hook intercepts, no violation, zero output. Agent retries successfully. **Expected**: Hook doesn't intercept (common case optimization).
- **Write to /tmp/**: Agent writes `/tmp/test.py`, hook intercepts, detects violation, produces corrective output. Agent follows correction. **Expected**: Same behavior (preserved).
- **Feedback to wrong path**: Agent writes feedback to `notes.md`, hook intercepts, detects feedback-path violation, redirects. **Expected**: Same behavior (preserved).

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Writes targeting paths outside the working directory (`/tmp/`, `%TEMP%`, `~/Downloads`) are intercepted and blocked with a corrective message
- Feedback content written to any path other than `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` is intercepted and redirected
- File content referencing external paths is intercepted and requires replacement with project-relative equivalents
- When the hook identifies a violation and produces corrective output, the agent follows the correction rather than retrying
- The hook's `id`, `version`, `when` configuration (preToolUse, write toolTypes), and `description` remain unchanged

**Scope:**
The fix changes only:
1. The hook's `then.prompt` field — to add pre-screening logic and an explicit pass signal
2. The `agent-instructions.md` hook silence rule — to reinforce the retry-on-no-violation contract

## Hypothesized Root Cause

Three contributing factors combine to produce the stall:

1. **Unconditional interception**: The hook fires on every single write regardless of whether the path or content is suspicious. In a multi-file build, this means 5–10 intercepts in a row where the hook evaluates its full prompt, determines no violation, and produces zero output. Each intercept consumes an agent decision cycle.

2. **Zero-output success convention**: The current prompt says "If neither policy is violated, produce no output at all — zero tokens, zero characters." The agent must then remember from `agent-instructions.md` that "When a hook check passes with no action needed, produce zero output" and infer that it should retry the original tool call. This is an inferential step that works in isolation but fails under cumulative load.

3. **Missing explicit retry mandate**: The hook silence rule in `agent-instructions.md` says to "produce zero output" but does not explicitly say "then immediately retry the original tool call with the same parameters." The agent must connect the dots: zero output → no violation → retry. Under load, this connection breaks.

## Correctness Properties

### P1: Discriminating Intercept (Bug Condition Fix)

_For any_ write operation where the target path is project-relative AND the content contains no external path references (`/tmp/`, `%TEMP%`, `~/Downloads`) AND the write is not feedback content directed to a non-canonical path, the hook prompt SHALL instruct the agent to immediately output "policy: pass" without evaluating the full policy check, providing an unambiguous retry signal.

**Validates: Requirements 2.1, 2.2**

### P2: Explicit Pass Signal

_For any_ hook intercept where the agent evaluates the full policy check and determines no violation exists, the hook output SHALL be exactly "policy: pass" (not zero output), providing an explicit signal that the agent should retry the original tool call immediately.

**Validates: Requirements 2.2, 2.3**

### P3: Violation Detection Preserved

_For any_ write operation where the target path is outside the working directory, OR the content references external paths, OR feedback content targets a non-canonical path, the hook SHALL continue to produce actionable corrective output describing the violation and required fix.

**Validates: Requirements 2.4, 3.1, 3.2, 3.3, 3.5**

### P4: Retry Contract Reinforced

_For any_ preToolUse hook intercept that does not explicitly deny access or produce corrective output, the agent-instructions.md SHALL explicitly mandate immediate retry of the original tool call with the same parameters.

**Validates: Requirements 2.3**

## Fix Implementation

### Changes Required

**File 1**: `senzing-bootcamp/hooks/enforce-file-path-policies.kiro.hook`

**Change**: Rewrite the `then.prompt` field to add pre-screening logic and an explicit pass signal.

**New prompt structure:**
```
QUICK CHECK — answer these two questions about the file being written:

Q1: Is the target path inside the working directory? (Not /tmp/, not %TEMP%, not ~/Downloads, not any absolute path outside the project)
Q2: Is this feedback content (has Date/Module/Priority/Category/What Happened sections) being written to a path OTHER than 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md'?

FAST PATH: If Q1 is YES (path is inside working directory) AND Q2 is NO (not misrouted feedback), output exactly:
policy: pass

Do not check file content for path references in the fast path. Do not explain. Do not acknowledge. Just output: policy: pass

SLOW PATH: If Q1 is NO (path is outside working directory) OR Q2 is YES (feedback going to wrong file):
- For external paths: STOP. Tell the agent to use project-relative equivalents (database/G2C.db for databases, data/temp/ for temporary files, src/ for source code).
- For misrouted feedback: STOP. Redirect to docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md.

CONTENT CHECK (only if fast path passed): Does the file content reference /tmp/, %TEMP%, ~/Downloads, or any location outside the working directory? If YES: STOP and require replacement with project-relative equivalents. If NO: output was already "policy: pass" — do not add anything.
```

**Rationale**: The fast path handles the common case (project-relative path, not feedback) with a single "policy: pass" output. The slow path handles violations. The content check is a secondary gate that only fires when the path itself is fine but content might reference external locations.

---

**File 2**: `senzing-bootcamp/steering/agent-instructions.md`

**Section**: `## Hooks` → `🔇 Hook silence rule`

**Change**: Add an explicit retry mandate after the silence rule.

**Updated text:**
```markdown
**🔇 Hook silence rule:** When a hook check passes with no action needed, produce zero output — no acknowledgment, no reasoning, no status. Only produce output when the hook identifies a problem. Applies to ALL hook types. The `ask-bootcamper` hook owns all closing questions — never end your turn with a closing question yourself; the hook handles it.

**🔄 preToolUse retry rule:** When a preToolUse hook produces "policy: pass" or produces no output (zero tokens), you MUST immediately retry the original tool call with exactly the same parameters. Do not emit any acknowledgment, do not explain, do not pause — retry instantly. Only when a preToolUse hook explicitly denies access or produces corrective instructions should you NOT retry.
```

---

**File 3**: `senzing-bootcamp/hooks/enforce-file-path-policies.kiro.hook` — `description` field

**Change**: Update the description to mention the fast-path behavior.

**New description:**
```
Before any write operation, enforces two path policies: (1) feedback content must go to docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md, and (2) no files may be written outside the working directory. Uses a fast path for project-relative non-feedback writes (outputs 'policy: pass' immediately) and a slow path for violations (outputs corrective instructions).
```

## Testing Strategy

### Exploratory Bug Condition Checking

**Goal**: Confirm the bug exists by demonstrating that the current hook prompt produces zero output for compliant writes, with no explicit retry signal.

**Test Cases**:
1. Parse the hook prompt and verify it contains "produce no output at all" (the zero-output instruction that causes the stall)
2. Verify `agent-instructions.md` does NOT contain an explicit "retry the original tool call" mandate for preToolUse hooks
3. Simulate the hook evaluation for a project-relative path with no violations — confirm the expected output is empty (not "policy: pass")

### Fix Checking

**Goal**: Verify the fix eliminates the bug condition.

**Test Cases**:
1. Parse the updated hook prompt and verify it contains "policy: pass" as the fast-path output
2. Parse the updated hook prompt and verify the fast-path condition matches: path inside working directory AND not misrouted feedback
3. Verify `agent-instructions.md` contains the explicit "🔄 preToolUse retry rule" with "immediately retry the original tool call"
4. Simulate the hook evaluation for a project-relative path — confirm expected output is "policy: pass"

### Preservation Checking

**Goal**: Verify violation detection is unchanged.

**Test Cases**:
1. Parse the updated hook prompt and verify it still contains instructions to STOP for external paths
2. Parse the updated hook prompt and verify it still contains instructions to redirect misrouted feedback
3. Parse the updated hook prompt and verify it still contains instructions to check content for external path references
4. Verify the hook's `when` configuration (preToolUse, write toolTypes) is unchanged
5. Verify the hook's `version` field is updated (since behavior changed)

### Property-Based Tests

- Generate random project-relative paths and verify the fast-path condition evaluates to "policy: pass"
- Generate random external paths (`/tmp/X`, `~/Downloads/Y`, `%TEMP%/Z`) and verify the slow-path condition triggers
- Generate random feedback content with various target paths and verify the feedback-path check triggers correctly
- Generate random file content with and without external path references and verify the content check behaves correctly

### Unit Tests

- `test_hook_prompt_contains_fast_path`: Verify "policy: pass" appears in the prompt
- `test_hook_prompt_contains_slow_path_for_external`: Verify STOP instruction for external paths
- `test_hook_prompt_contains_feedback_redirect`: Verify feedback path enforcement
- `test_agent_instructions_contains_retry_rule`: Verify the preToolUse retry rule exists
- `test_hook_when_config_unchanged`: Verify preToolUse + write toolTypes preserved
- `test_hook_description_updated`: Verify description mentions fast path
