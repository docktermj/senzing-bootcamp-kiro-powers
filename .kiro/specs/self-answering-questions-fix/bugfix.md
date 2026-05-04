# Bugfix Requirements Document

## Introduction

The senzing-bootcamp Power's agent asks questions to the bootcamper during interactive modules (particularly Module 1 gap-filling in Step 7, onboarding gates, and deployment target questions) but then answers those questions itself in the same turn instead of stopping and waiting for the bootcamper's actual response. This defeats the interactive, guided nature of the bootcamp and can lead to fabricated business details, skipped decision points, and a confusing experience where the bootcamper's real input is never collected.

The bug persists despite existing safeguards in `agent-instructions.md` (soft rules like "wait for response"), the `ask-bootcamper` agentStop hook (which fires too late — after the agent has already self-answered), and inline "STOP and wait" instructions in module steering files. The root cause is that these instructions are not structurally strong enough to override the model's tendency to continue generating after posing a question.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent asks a gap-filling question in Module 1 Step 7 (e.g., "Are you working with people records, organization records, or both?") THEN the system continues generating in the same turn, answering the question on the bootcamper's behalf with fabricated details instead of stopping and yielding control to the bootcamper.

1.2 WHEN the agent asks a question marked with 👉 or containing "STOP and wait for the bootcamper's response" THEN the system sometimes ignores the stop instruction and proceeds to the next step or provides its own answer to the question within the same response.

1.3 WHEN the agent reaches a mandatory gate (⛔) that requires real bootcamper input (e.g., language selection, track selection, deployment target) THEN the system occasionally fabricates a response (e.g., "I'll go with Python" or "Let's do Track C") and continues past the gate without actual bootcamper input.

1.4 WHEN the ask-bootcamper agentStop hook fires after the agent has already self-answered a question THEN the hook's suppression logic cannot undo the self-answered content because the damage (fabricated answer and continued execution) already occurred in the preceding turn.

### Expected Behavior (Correct)

2.1 WHEN the agent asks a gap-filling question in Module 1 Step 7 THEN the system SHALL end its response immediately after the question, producing no further content, and SHALL wait for the bootcamper to provide their own answer before continuing.

2.2 WHEN the agent asks any question marked with 👉 or any question at a point where "STOP and wait" is instructed THEN the system SHALL terminate its output immediately after the question text and SHALL NOT generate any answer, assumption, continuation, or next-step content in the same response.

2.3 WHEN the agent reaches a mandatory gate (⛔) requiring bootcamper input THEN the system SHALL stop completely after presenting the gate's question or options, SHALL NOT fabricate or simulate a bootcamper response, and SHALL NOT proceed past the gate until the bootcamper provides real input in a subsequent turn.

2.4 WHEN the agent's steering instructions contain a stop-and-wait directive at a question point THEN the system SHALL treat that directive as an absolute hard stop — equivalent to an end-of-turn boundary — rather than a soft suggestion that can be overridden by conversational momentum.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent performs non-interactive work (e.g., creating directories, writing checkpoint files, running scripts, generating code) that does not involve asking the bootcamper a question THEN the system SHALL CONTINUE TO complete that work fully in a single turn without unnecessary interruptions.

3.2 WHEN the agent presents informational content that does not require a response (e.g., data privacy reminder in Step 2, solution approach explanation in Step 14) THEN the system SHALL CONTINUE TO present the full informational content before moving on, without inserting unnecessary stop points.

3.3 WHEN the ask-bootcamper agentStop hook fires and no question is pending THEN the system SHALL CONTINUE TO provide a recap of work done and a contextual 👉 closing question, as it does today.

3.4 WHEN the agent is in the middle of multi-step non-interactive work (e.g., parsing user input in Step 6, creating the problem statement document in Step 12) THEN the system SHALL CONTINUE TO complete all sub-steps of that work without stopping, since no bootcamper input is needed.

3.5 WHEN the hook silence rule applies (hook check passes with no action needed) THEN the system SHALL CONTINUE TO produce zero output for that hook invocation, as it does today.
