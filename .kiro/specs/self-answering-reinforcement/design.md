# Design: Self-Answering Reinforcement

## Overview

Despite existing mitigations, the agent still fabricates "Human:" responses during onboarding and Module 1. This design adds explicit 🛑 STOP markers after every 👉 question in affected files and adds a "Human:" pattern to the forbidden output list.

## Root Cause Analysis

The existing defenses are:
1. `agent-instructions.md` — "Never fabricate user input"
2. `conversation-protocol.md` — Self-answering prohibition
3. `session-resume.md` — Self-Answering Prohibition subsection with examples
4. `ask-bootcamper` hook — silence-first with question-pending check
5. `config/.question_pending` — sentinel file mechanism

The gap: **onboarding-flow.md and module-01 don't have explicit 🛑 STOP markers after every 👉 question.** The agent sees the 👉 prefix but doesn't always recognize it as a hard stop boundary without the explicit marker. Adding 🛑 STOP after each question provides a redundant signal.

## Changes

### 1. Add "Human:" to forbidden patterns in agent-instructions.md

In the Communication section, add:

```markdown
- FORBIDDEN output patterns: never generate text beginning with "Human:", "User:", or any text that simulates a bootcamper response. This is a critical violation.
```

### 2. Add 🛑 STOP after every 👉 question in onboarding-flow.md

For each 👉 question in onboarding-flow.md that doesn't already have a 🛑 STOP within 2 lines, add:

```markdown
🛑 STOP — Wait for bootcamper response. Do not generate any additional content.
```

Affected questions:
- Step 0b: MCP offline mode question
- Step 2: Language selection
- Step 4b: Verbosity preference
- Step 4c: Comprehension check
- Step 5: Track selection

### 3. Add 🛑 STOP after confirmation questions in module-01

For questions like "Does that sound right?" in module-01-business-problem.md, add explicit STOP markers.

### 4. Add anti-fabrication to ask-bootcamper hook

Add to the hook prompt (after the DEFAULT OUTPUT instruction):

```
CRITICAL: NEVER generate text beginning with "Human:" or any text that represents what the bootcamper might say. If you detect yourself about to fabricate a user response, output only: .
```

## Files Modified

- `senzing-bootcamp/steering/agent-instructions.md` — add "Human:" to forbidden patterns
- `senzing-bootcamp/steering/onboarding-flow.md` — add 🛑 STOP after 👉 questions
- `senzing-bootcamp/steering/module-01-business-problem.md` — add 🛑 STOP after confirmation questions
- `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` — add anti-fabrication instruction
- `senzing-bootcamp/steering/hook-registry.md` — regenerate

## Testing

- Unit test: agent-instructions.md contains "Human:" in forbidden patterns
- Unit test: onboarding-flow.md has 🛑 STOP within 2 lines of every 👉 question
- Unit test: module-01 has 🛑 STOP after confirmation questions
- Unit test: ask-bootcamper hook contains anti-fabrication instruction
- Property test: no steering file has a 👉 question without a 🛑 STOP within 3 lines (excluding code blocks and examples)
