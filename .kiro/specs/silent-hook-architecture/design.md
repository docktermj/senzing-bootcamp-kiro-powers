# Design: Silent Hook Architecture Fix

## Overview

The `ask-bootcamper` hook uses `askAgent` which requires the model to generate a response. When conditions aren't met, the model interprets "PRODUCE NO OUTPUT" as a reasoning constraint and still generates visible text explaining its silence. The fix uses a minimal-token response approach (Option A from requirements).

## Chosen Approach: Minimal-Token Response

Instead of instructing "PRODUCE NO OUTPUT" (which the model interprets as "explain why you're producing no output"), instruct the model to respond with a single specific token that's effectively invisible:

**New instruction:** "If ALL conditions fail, respond with exactly one period character (.) and nothing else — no reasoning, no explanation, no condition checks."

### Why This Works

1. The model has a concrete, unambiguous output to produce — no interpretation needed
2. A single `.` is functionally invisible in chat (minimal visual noise)
3. It satisfies the `askAgent` requirement that the model must produce *something*
4. It's testable — we can verify the output is exactly `.` when conditions fail

### Why Not Zero-Width Space

Zero-width spaces (U+200B) are unreliable across different model versions and tokenizers. A period is universally understood and consistently produced.

## Changes to ask-bootcamper Hook

Replace the opening instruction block:

**Before:**
```
PRODUCE NO OUTPUT. YOUR OUTPUT IS EMPTY. ZERO TOKENS. DO NOT GENERATE ANY TEXT.
```

**After:**
```
DEFAULT OUTPUT: .
If BOTH phases below produce no output, your COMPLETE response is a single period character: .
Do NOT explain your reasoning. Do NOT describe condition checks. Just output: .
```

The rest of the prompt (Phase 1 and Phase 2 logic) remains unchanged.

## Changes to Other Silence-First Hooks

Audit all hooks for "PRODUCE NO OUTPUT" or "zero output" instructions and apply the same pattern. Currently only `ask-bootcamper` uses the silence-first pattern.

## Hook Registry Update

Update the `ask-bootcamper` entry in `hook-registry.md` to reflect the new prompt opening.

## Testing

- Unit test: ask-bootcamper hook prompt starts with "DEFAULT OUTPUT: ." instruction
- Unit test: hook prompt does NOT contain "PRODUCE NO OUTPUT" or "ZERO TOKENS"
- Steering structure test: hook-registry.md matches actual hook file

## Files Modified

- `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` — replace silence instruction
- `senzing-bootcamp/steering/hook-registry.md` — regenerate via `sync_hook_registry.py --write`
