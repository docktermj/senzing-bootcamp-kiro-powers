# Technical Design: forward-moving-questions

## Overview

The agent dead-ends after hook-triggered CommonMark fixes because: (1) the `commonmark-validation` hook prompt ends at "fix them automatically" with no instruction to conclude with a forward-moving question, and (2) the `ask-bootcamper` safety-net hook's no-op check ("if no files changed / no substantive work") may suppress the closing question even though files were edited. Additionally, compound-choice questions lack numbered-list formatting, making them harder to parse.

## Root Cause

**Dead-end after hook fix:** The `commonmark-validation.kiro.hook` prompt is purely corrective — it tells the agent to check and fix, then implicitly signals "done." The agent treats the hook-triggered work as complete. The `ask-bootcamper` agentStop hook has a no-op clause: "if ALL Phase 1 conditions pass AND no files changed (no substantive work was done — e.g., only a hook fired or a trivial acknowledgment occurred): Phase 1 output is none." This clause is ambiguous — hook-triggered file edits DO change files, but the parenthetical "(e.g., only a hook fired)" suggests the hook classifies all hook-triggered work as non-substantive regardless of file changes.

**Compound-choice formatting:** The `conversation-protocol.md` has a "One Question Rule" that prohibits multi-question patterns, but has no rule requiring numbered-list formatting when a single question presents multiple distinct options. The agent defaults to inline prose.

## Design

### Approach: Hook Prompt Update + Steering Rule Addition

The fix uses three targeted changes:

1. **Update `commonmark-validation.kiro.hook` prompt** — Add a closing instruction that tells the agent to conclude with a brief recap and a contextual 👉 forward-moving question after applying fixes.
2. **Update `ask-bootcamper.kiro.hook` prompt** — Clarify the no-op condition to explicitly treat hook-triggered file edits as substantive work.
3. **Add question formatting rule to `conversation-protocol.md`** — Add a "Choice Formatting" section requiring numbered lists when a question presents 2+ distinct alternatives.

### Change 1: Update `commonmark-validation.kiro.hook`

**Current prompt ending:**
```
If any issues are found, fix them automatically to maintain CommonMark compliance across all documentation.
```

**New prompt ending:**
```
If any issues are found, fix them automatically to maintain CommonMark compliance across all documentation.

After fixing issues: briefly state what was corrected (one sentence), then end with a contextual 👉 forward-moving question that guides the bootcamper to the next step in the current module workflow. Check `config/bootcamp_progress.json` for the current module and step to determine what comes next.

If no issues are found: output nothing. Proceed silently.
```

**Rationale:** This makes the hook self-sufficient — it doesn't rely on the `ask-bootcamper` safety net for the forward-moving question. The "output nothing" clause preserves requirement 3.1 (silent pass when no issues found).

### Change 2: Update `ask-bootcamper.kiro.hook`

**Current no-op clause:**
```
FIRST — Check for no-op: If ALL Phase 1 conditions pass AND no files changed (no substantive work was done — e.g., only a hook fired or a trivial acknowledgment occurred): Phase 1 output is none. Skip to Phase 2.
```

**New no-op clause:**
```
FIRST — Check for no-op: If ALL Phase 1 conditions pass AND the most recent assistant message contains no substantive content (e.g., only a trivial acknowledgment like "Got it" or "Understood" with no file changes, no recap, and no action taken): Phase 1 output is none. Skip to Phase 2.

NOTE: If files were edited (even by a hook-triggered action), that IS substantive work. Provide a closing question unless a 👉 question is already present.
```

**Rationale:** This removes the ambiguity that allowed hook-triggered file edits to be classified as non-substantive. The safety net now correctly fires when the primary hook (commonmark-validation) fails to include a forward-moving question for any reason. This satisfies requirement 2.2.

### Change 3: Add "Choice Formatting" section to `conversation-protocol.md`

Insert a new section after "One Question Rule":

```markdown
## Choice Formatting

When a 👉 question presents 2 or more distinct alternatives (options the bootcamper can choose between), format them as a numbered list:

### Compound Choice (WRONG)

> 👉 Would you like to proceed with Python or Java or TypeScript?

### Compound Choice (CORRECT)

> 👉 Which language would you like to use?
>
> 1. Python
> 2. Java
> 3. TypeScript

Simple yes/no questions or questions with a single implied action remain as inline prose:

### Simple Question (CORRECT — no list needed)

> 👉 Ready to move on to Module 3?
```

**Rationale:** This provides clear formatting guidance with examples matching the existing violation/correct pattern in the protocol. It satisfies requirement 2.3 while preserving requirement 3.2 (simple yes/no stays inline).

## Files Changed

| File | Change |
|------|--------|
| `senzing-bootcamp/hooks/commonmark-validation.kiro.hook` | UPDATE prompt to include forward-moving question instruction after fixes |
| `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` | UPDATE no-op clause to treat hook-triggered file edits as substantive |
| `senzing-bootcamp/steering/conversation-protocol.md` | ADD "Choice Formatting" section with numbered-list rule and examples |

## Interaction with Existing Hooks and Steering

- **`ask-bootcamper` (agentStop):** Updated to be a more reliable safety net. The primary responsibility for forward-moving questions remains with the agent (per conversation-protocol.md: "This is YOUR responsibility — do not rely on hooks to provide the closing question"). The hook change ensures it catches cases where the agent fails to follow the protocol.
- **`commonmark-validation` (fileEdited):** Updated to be self-sufficient — it now instructs the agent to provide the forward-moving question directly, rather than relying on the safety net.
- **`conversation-protocol.md` (auto-included steering):** Extended with formatting guidance. The new section complements the existing "One Question Rule" without conflicting.
- **`config/.question_pending`:** No changes. The existing mechanism continues to prevent duplicate questions (requirement 3.4).

## Scope Boundaries

- Only the `commonmark-validation` hook is updated to include forward-moving question instructions. Other hooks that trigger file edits (e.g., `code-style-check`) are not modified — they have different completion semantics.
- The `ask-bootcamper` no-op clause change applies globally but only affects the safety-net behavior. It does not change the hook's Phase 2 (feedback reminder) logic.
- The choice formatting rule applies to all 👉 questions across all modules, not just Module 1.

## Testing Considerations

- Verify the updated `commonmark-validation` hook JSON is valid (required fields: name, version, when, then)
- Verify the `ask-bootcamper` hook JSON is valid after the prompt update
- Verify `conversation-protocol.md` maintains valid CommonMark after the new section is added
- Run `validate_power.py` to confirm power structure validity
- Run `sync_hook_registry.py --verify` to confirm hook registry consistency
- Run `pytest` to confirm no regressions
