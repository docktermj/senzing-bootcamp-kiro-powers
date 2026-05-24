# Design: Consolidate preToolUse Hooks

## Overview

Consolidate three separate `preToolUse` write hooks (`block-direct-sql`, `enforce-single-question`, `enforce-file-path-policies`) into a single unified hook (`write-policy-gate`) that performs all three checks in one interception. This reduces visible noise from 3 "Ask Kiro Hook to..." messages per write operation down to 1.

## Glossary

| Term | Definition |
|------|-----------|
| preToolUse hook | A hook that fires before a tool operation, allowing the agent to validate or block the operation |
| Fast path | The code path taken when no violations are detected — produces zero visible output |
| Slow path | The code path taken when a violation is detected — produces blocking instructions |
| Write-policy-gate | The new consolidated hook replacing the three individual hooks |

## Bug Details

Three separate `preToolUse` hooks each fire independently on every write operation:
1. `block-direct-sql` — checks for SQL targeting Senzing database
2. `enforce-single-question` — validates `.question_pending` writes
3. `enforce-file-path-policies` — validates file paths and feedback routing

Each produces a visible "Ask Kiro Hook to..." interception message plus reasoning output, resulting in up to 6 visible items per write operation. This clutters the bootcamp conversation on nearly every agent turn.

## Expected Behavior

- A single "Ask Kiro Hook to..." message per write operation (from one consolidated hook)
- Zero visible reasoning output when all checks pass (silent fast path)
- Identical violation detection and corrective guidance when checks fail
- All three policy areas (SQL blocking, single-question, file paths) continue to function

## Hypothesized Root Cause

The Kiro hook framework fires each registered `preToolUse` hook as a separate visible interception. There is no framework-level mechanism to suppress the "Ask Kiro Hook to..." message or to batch multiple hooks into a single interception. The only solution is to consolidate the three hooks into one hook file.

## Fix Implementation

### Architecture

```
BEFORE (3 hooks, 3 interceptions per write):
┌─────────────────────┐  ┌──────────────────────┐  ┌───────────────────────────┐
│ block-direct-sql    │  │ enforce-single-question│  │ enforce-file-path-policies│
└─────────────────────┘  └──────────────────────┘  └───────────────────────────┘

AFTER (1 hook, 1 interception per write):
┌─────────────────────────────────────────────────────────────────────────────┐
│ write-policy-gate                                                           │
│ ┌─────────────┐  ┌─────────────────────┐  ┌──────────────────────────────┐ │
│ │ Check 1: SQL│  │ Check 2: Single-Q   │  │ Check 3: File Path Policies  │ │
│ └─────────────┘  └─────────────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Consolidated Prompt Structure

1. **Fast path gate** — If the write is a normal project-relative file that doesn't target `.question_pending` and doesn't contain Senzing SQL patterns, proceed silently with zero output.
2. **Check 1: Senzing SQL** — If content contains SQL patterns AND Senzing database indicators, block and provide SDK rewrite guidance (verbatim from `block-direct-sql`).
3. **Check 2: Single question** — If target path ends with `.question_pending`, validate single-question rules (verbatim from `enforce-single-question`).
4. **Check 3: File path policies** — If target path is outside working directory OR feedback content is misrouted, block and redirect (verbatim from `enforce-file-path-policies`).

### New Files

| File | Purpose |
|------|---------|
| `senzing-bootcamp/hooks/write-policy-gate.kiro.hook` | Consolidated preToolUse write hook |

### Modified Files

| File | Change |
|------|--------|
| `senzing-bootcamp/hooks/hook-categories.yaml` | Replace 3 entries with `write-policy-gate` in `critical` list |
| `senzing-bootcamp/steering/hook-registry.md` | Remove 3 rows, add 1 row |
| `senzing-bootcamp/steering/hook-registry-detail.md` | Remove 3 sections, add 1 section |
| `senzing-bootcamp/steering/onboarding-flow.md` | Replace 3 hook table rows with 1 |
| `senzing-bootcamp/steering/agent-instructions.md` | Update hook reference |
| `senzing-bootcamp/steering/conversation-protocol.md` | Update hook reference |
| `senzing-bootcamp/steering/conversation-examples.md` | Update hook reference |
| `tests/test_hook_prompt_standards.py` | Update `EXPECTED_HOOK_COUNT` (29 → 27) |
| `tests/test_suppress_policy_pass_output.py` | Update `HOOK_PATH` |
| `tests/hook_test_helpers.py` | Update `CRITICAL_HOOKS` list |

### Deleted Files

| File | Reason |
|------|--------|
| `senzing-bootcamp/hooks/block-direct-sql.kiro.hook` | Replaced by consolidated hook |
| `senzing-bootcamp/hooks/enforce-single-question.kiro.hook` | Replaced by consolidated hook |
| `senzing-bootcamp/hooks/enforce-file-path-policies.kiro.hook` | Replaced by consolidated hook |

### Design Decisions

1. **Hook naming**: File ID `write-policy-gate`, display name "to process your response" (neutral, doesn't reveal internal mechanics to bootcamper).
2. **Check ordering**: SQL → Question → Path (most-specific to least-specific for early fast-path exit).
3. **Verbatim slow-path text**: Violation messages preserved word-for-word from originals (required by test baselines).
4. **Hook count**: Net -2 (remove 3, add 1), changing `EXPECTED_HOOK_COUNT` from 29 to 27.

## Correctness Properties

### Property 1: Single interception per write
Only one `.kiro.hook` file with `preToolUse` + `toolTypes: ["write"]` exists for these three policies, ensuring a single "Ask Kiro Hook to..." message per write.
**Validates: Requirements 2.1, 2.3**

### Property 2: Silent fast path
The consolidated prompt contains "Do not acknowledge. Do not explain. Do not print anything. Proceed silently." ensuring zero visible output when all checks pass.
**Validates: Requirements 2.2, 3.5**

### Property 3: SQL blocking preserved
The consolidated prompt contains all SQL patterns (SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE, ALTER TABLE, PRAGMA) and all Senzing database indicators (G2C.db, RES_ENT, OBS_ENT, etc.) from the original `block-direct-sql` hook.
**Validates: Requirements 3.1, 3.6**

### Property 4: Single-question enforcement preserved
The consolidated prompt contains all 5 validation rules from the original `enforce-single-question` hook (exactly one question mark, no conjunctions, no appended alternatives, unambiguous yes/no, no follow-up after confirmation).
**Validates: Requirements 3.2, 3.6**

### Property 5: File path policies preserved
The consolidated prompt contains SLOW PATH text identical to the `ORIGINAL_SLOW_PATH_TEXT` baseline in `test_suppress_policy_pass_output.py`.
**Validates: Requirements 3.3, 3.4, 3.6**

### Property 6: Registry sync
`sync_hook_registry.py --verify` passes after all changes are applied.
**Validates: Requirements 2.1**

## Testing Strategy

1. Run `pytest tests/test_suppress_policy_pass_output.py -v` — validates silent fast path and slow-path baseline
2. Run `pytest tests/test_hook_prompt_standards.py -v` — validates JSON structure, hook count, registry sync
3. Run `pytest tests/test_hook_prompt_logic.py -v` — validates prompt logic patterns
4. Run `python senzing-bootcamp/scripts/sync_hook_registry.py --verify` — validates registry consistency
5. Full suite: `pytest tests/ senzing-bootcamp/tests/ -v`
