# Requirements: Silent Hook Architecture Fix

## Overview

The `ask-bootcamper` hook (and potentially other `askAgent` hooks) cannot achieve true silence. When the hook's conditions aren't met and it should produce zero output, the agent instead displays its internal reasoning ("Phase 1: condition fails. Silenced. Phase 2: no track completion. Silenced."). This exposes implementation details to the bootcamper and clutters every conversation turn.

The root cause is architectural: `askAgent` hooks require the agent to generate a response. The agent interprets "PRODUCE NO OUTPUT" as a reasoning constraint but still generates visible text explaining why it's silent.

## Requirements

1. When the `ask-bootcamper` hook determines all conditions fail (no closing question needed, no feedback reminder needed), the bootcamper SHALL see absolutely zero visible output — no reasoning, no condition checks, no acknowledgment
2. The solution SHALL work reliably across different model versions and context states — it cannot depend on the model perfectly following "produce nothing" instructions
3. The solution SHALL preserve the hook's existing functionality: recap + closing question when conditions pass, feedback reminder on track completion
4. The solution SHALL not require the bootcamper to install additional tools or dependencies
5. The hook's silence behavior SHALL be testable — the test suite can verify that the hook produces no output under specific conditions
6. The solution SHALL apply to all hooks that need silence-first behavior, not just `ask-bootcamper`
7. If the chosen approach changes the hook type (e.g., from `askAgent` to `runCommand`), the hook registry, hook-categories.yaml, and all documentation SHALL be updated to match

## Proposed Approaches (for design phase)

### Option A: Minimal-token response instruction
Change the prompt from "PRODUCE NO OUTPUT" to "If conditions are not met, respond with exactly: ​" (a zero-width space). This gives the model a concrete minimal output that's invisible to the bootcamper.

### Option B: Stronger prompt engineering
Restructure the prompt to put the silence instruction in a format the model is more likely to follow literally — e.g., making the first line of output conditional on a check, so the model never enters "explanation mode."

### Option C: Accept the limitation and document it
Document that `askAgent` hooks may produce minimal reasoning output and that this is a known Kiro platform limitation. Focus mitigation on making the output as short as possible.

## Non-Requirements

- This does not change what the hook does when conditions ARE met (recap, closing question, feedback reminder)
- This does not add new hook types to the Kiro platform
- This does not require changes to the Kiro IDE itself
- This does not address the self-answering problem (that's covered by existing specs)
