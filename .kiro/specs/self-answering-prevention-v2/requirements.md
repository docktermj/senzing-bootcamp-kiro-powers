# Bugfix Requirements Document: Self-Answering Prevention v2

## Introduction

Despite the `self-answering-questions-fix` spec being fully implemented (hard-stop blocks at all question points, Question Stop Protocol in agent-instructions.md, strengthened ask-bootcamper hook prompt), the agent continues to answer its own 👉 questions. The issue occurred 5+ times across Modules 8, 9, and 10 in a single session.

The agent itself diagnosed the root cause: "The agentStop hooks fire after I finish a response. They inject instructions as a new turn in the conversation. When I see that new turn, I sometimes generate a response that starts with what looks like a user message followed by my reply to it. I'm essentially hallucinating your response and then acting on it — all in one output."

The previous fix attempted to solve this with stronger prompt language. That approach is insufficient — the model sometimes fails to follow "produce zero tokens" instructions regardless of how strongly worded they are. A structural change to the hook architecture is needed.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent asks a 👉 question and correctly stops THEN the `ask-bootcamper` agentStop hook fires, creating a new agent turn with its prompt injected into the conversation.

1.2 WHEN the agent receives the hook prompt as a new turn THEN it sometimes hallucinates a user response (e.g., "Human: 50 concurrent users") and acts on it — generating both the fabricated user message and its own response to it in a single output.

1.3 WHEN the agent hallucinates a user response THEN it proceeds through multiple steps, answering its own questions repeatedly, creating a monologue that bypasses the bootcamper entirely.

1.4 THE existing fix (stronger prompt language in the hook) is insufficient because the model's failure mode is not "misunderstanding the instruction" but rather "generating content before processing the instruction" — once token generation begins, the model commits to the fabricated flow.

### Expected Behavior (Correct)

2.1 WHEN the agent asks a 👉 question and stops THEN the system SHALL NOT create a new agent turn that could trigger hallucinated continuations.

2.2 WHEN a 👉 question is pending THEN the next agent output SHALL be in direct response to genuine bootcamper input only — no intermediate hook-triggered turns.

2.3 WHEN the agent completes non-question work (no 👉 pending) THEN the system SHALL still provide the recap + closing question behavior currently handled by the ask-bootcamper hook.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent completes work without asking a 👉 question THEN the recap + closing question behavior SHALL be preserved.

3.2 WHEN the bootcamper provides genuine input after a 👉 question THEN the agent SHALL respond normally to that input.

3.3 WHEN other hooks fire (preToolUse, fileEdited, etc.) THEN their behavior SHALL be unchanged.

## Root Cause Analysis

The root cause is **architectural, not prompt-based**:

1. The `ask-bootcamper` hook is `agentStop` → `askAgent`
2. `askAgent` creates a new agent turn — the model receives the hook prompt and must generate a response
3. The model is supposed to generate zero tokens when 👉 is pending, but this is asking the model to "do nothing" in a context where it's been explicitly prompted to generate
4. The model's failure mode: it starts generating, hallucinates a user message, and commits to the fabricated flow
5. Stronger prompt language cannot fix this because the failure happens at the generation-initiation level, not the instruction-following level

## Proposed Structural Fix

Replace the single `ask-bootcamper` agentStop → askAgent hook with a two-part approach:

**Part 1: Embed recap behavior in steering instructions** — Move the "recap + closing question" responsibility from the hook into `agent-instructions.md` as a mandatory end-of-turn behavior. The agent always ends non-question turns with a brief recap and 👉 closing question. This eliminates the need for the hook to fire on non-question turns.

**Part 2: Remove or neuter the agentStop hook** — Either delete the `ask-bootcamper` hook entirely (since its behavior is now in steering), or convert it to a `runCommand` hook that simply checks for a sentinel file (no agent turn created). If kept as `askAgent`, restructure the prompt so the DEFAULT is absolute silence with the recap being a narrowly gated exception.

## Acceptance Criteria

1. After the agent asks a 👉 question and stops, NO additional agent turn SHALL be created by hooks that could trigger hallucinated continuations
2. The recap + closing question behavior SHALL still occur after non-question agent turns (delivered either by the agent itself via steering instructions, or by a restructured hook that cannot trigger hallucinations)
3. The fix SHALL eliminate the structural opportunity for the agent to hallucinate user responses — not merely instruct it not to
4. The fix SHALL be validated by confirming that no `askAgent` hook fires between a 👉 question and the bootcamper's genuine response
5. All other hook behaviors (preToolUse, fileEdited, promptSubmit, etc.) SHALL remain unchanged

## Reference

- Source: `SENZING_BOOTCAMP_POWER_FEEDBACK.md` — "Agent answering its own questions is a systemic recurring issue"
- Modules: 8, 9, 10 (multiple) | Priority: Critical | Category: Bug
- Previous fix: `self-answering-questions-fix` spec (implemented but insufficient)
- Agent self-diagnosis: "I see the hook instruction as a new conversation turn. I sometimes interpret 'produce no output' incorrectly and instead generate a simulated continuation."
