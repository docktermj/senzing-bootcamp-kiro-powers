# Requirements: Self-Answering Reinforcement

## Overview

Despite existing mitigations (`self-answering-prevention-v2`, `track-selection-gate`, conversation-protocol rules, question-pending sentinel file), bootcamper feedback reports the agent still fabricates responses ("Human: Python", "Human: Yes, that's right.") and continues past 👉 questions without stopping. This occurs during onboarding and Module 1.

The existing architectural defenses (silence-first hook, sentinel file, steering rules) are correct but insufficient — the model still violates them under certain conditions. This spec adds additional reinforcement layers.

## Requirements

1. The agent SHALL never generate text that begins with "Human:" or any variation that simulates a user message
2. The `onboarding-flow.md` SHALL include explicit 🛑 STOP markers after EVERY 👉 question (not just gates) — including verbosity preference, language selection, and comprehension check
3. The `module-01-business-problem.md` SHALL include explicit 🛑 STOP markers after confirmation questions (e.g., "Does that sound right?")
4. The `ask-bootcamper` hook prompt SHALL include an explicit anti-fabrication instruction: "NEVER generate text beginning with 'Human:' or any text that represents what the bootcamper might say"
5. The `agent-instructions.md` Communication section SHALL explicitly list "Human:" as a forbidden output pattern
6. A new preToolUse hook SHALL detect and block write operations that contain "Human:" fabrication patterns in the content being written

## Non-Requirements

- This does not change the fundamental architecture of the question-pending mechanism
- This does not guarantee 100% compliance (model behavior is probabilistic)
- This does not address the silent-hook issue (that's a separate spec)
