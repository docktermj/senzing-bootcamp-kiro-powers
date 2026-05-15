# Bugfix Requirements Document

## Introduction

During Module 1 Step 12, after the `commonmark-validation` hook fires and the agent fixes CommonMark issues in `docs/business_problem.md`, the agent stops without asking a forward-moving question to guide the bootcamper to the next step. The conversation dead-ends, leaving the bootcamper with no clear path forward.

The root cause has two parts:

1. The `commonmark-validation.kiro.hook` prompt instructs the agent to "fix them automatically" but does not instruct the agent to conclude with a forward-moving question after the fix is applied. The agent treats the hook-triggered work as complete once the markdown is fixed and stops.
2. The `ask-bootcamper` agentStop safety-net hook has conditions that may prevent it from firing a closing question (e.g., if it detects a question already pending, or if it determines no "substantive work" was done). When the commonmark fix is the only work in the turn, the safety net may classify it as trivial and suppress its closing question.

Additionally, when the agent does ask questions that present compound choices (using "or"), they are formatted as inline prose rather than numbered option lists, making it harder for the bootcamper to parse and select from the available choices.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the `commonmark-validation` hook fires and the agent fixes markdown issues THEN the system completes the fix and stops without asking a forward-moving question to guide the bootcamper to the next step.

1.2 WHEN the `ask-bootcamper` agentStop hook evaluates whether to add a closing question after hook-triggered markdown fixes THEN the hook may classify the work as not substantive and suppress the closing question, resulting in a dead-end response.

1.3 WHEN the agent presents a question with compound choices joined by "or" (e.g., "Would you like to do X or Y or Z?") THEN the system formats the choices as inline prose rather than a numbered option list, making it harder for the bootcamper to scan and select.

### Expected Behavior (Correct)

2.1 WHEN the `commonmark-validation` hook fires and the agent fixes markdown issues THEN the system SHALL conclude its response with a brief recap of what was fixed and a contextual 👉 forward-moving question that guides the bootcamper to the next step in the current module workflow.

2.2 WHEN the `ask-bootcamper` agentStop hook evaluates whether to add a closing question after any hook-triggered work (including markdown fixes) THEN the hook SHALL treat hook-triggered file edits as substantive work and provide a closing question if no 👉 question is already present in the response.

2.3 WHEN the agent presents a question with multiple options or compound choices (containing "or" between distinct alternatives) THEN the system SHALL format the choices as a numbered list so the bootcamper can easily identify and select an option.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the `commonmark-validation` hook fires and finds no issues to fix THEN the system SHALL CONTINUE TO produce no visible output (silent pass).

3.2 WHEN the agent asks a simple yes/no question or a question with a single choice THEN the system SHALL CONTINUE TO format it as inline prose without a numbered list.

3.3 WHEN the agent is already at a 👉 question stop point in the module workflow THEN the system SHALL CONTINUE TO stop after that question without adding a second question.

3.4 WHEN the `ask-bootcamper` hook detects that a 👉 question is already pending (via `config/.question_pending`) THEN the hook SHALL CONTINUE TO suppress additional output and not add a duplicate closing question.

3.5 WHEN the agent completes non-hook-triggered work that already ends with a 👉 question THEN the system SHALL CONTINUE TO follow the existing end-of-turn protocol without modification.
