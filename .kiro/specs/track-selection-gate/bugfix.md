# Bugfix Requirements Document

## Introduction

During onboarding Step 5 (Track Selection), the agent presents track options (A/B/C/D) but does not stop to wait for the bootcamper's response. Instead, it fabricates a "Human: A" message in its own output and proceeds to start Module 2 (SDK Setup) immediately — choosing Track A on the bootcamper's behalf without receiving actual input. This undermines the interactive nature of the bootcamp and removes the bootcamper's ability to choose their own learning path.

The root cause is a conflict between the onboarding flow's general note ("Do NOT include inline closing questions or WAIT instructions at the end of steps") and the fact that track selection is a mandatory gate requiring user input. The agent treats Steps 4 (Introduction) and 5 (Track Selection) as continuous flow, never stopping between them. The `ask-bootcamper` hook (which fires on `agentStop`) never gets a chance to fire because the agent doesn't stop. Additionally, no rule explicitly prohibits the agent from fabricating user responses.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent presents the track selection options (A/B/C/D) in Step 5 of onboarding THEN the system continues executing without stopping, treating Steps 4 and 5 as a single continuous turn

1.2 WHEN the agent reaches a point where user input is required for track selection THEN the system fabricates a user response (e.g., "Human: A") in its own output and acts on it as if the bootcamper chose Track A

1.3 WHEN the agent fabricates a track selection response THEN the system proceeds to start Module 2 (SDK Setup) immediately, bypassing the bootcamper's actual choice

1.4 WHEN the agent proceeds past track selection without real user input THEN the `ask-bootcamper` hook never fires for the track selection step because the agent does not stop between presenting tracks and proceeding

### Expected Behavior (Correct)

2.1 WHEN the agent presents the track selection options (A/B/C/D) in Step 5 of onboarding THEN the system SHALL stop after presenting the options and wait for the bootcamper's actual response before proceeding

2.2 WHEN the agent reaches a point where user input is required for track selection THEN the system SHALL never fabricate, simulate, or role-play a user response — it must receive genuine input from the bootcamper

2.3 WHEN the bootcamper provides their track selection response THEN the system SHALL use that actual response to determine which module to start next, following the track-to-module mapping (A→Module 3, B→Module 5, C→Module 1, D→Module 1)

2.4 WHEN the agent stops after presenting track selection THEN the `ask-bootcamper` hook SHALL fire normally, generating a contextual closing question to prompt the bootcamper for their choice

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent is executing setup steps (Steps 0-1) that do not require user input THEN the system SHALL CONTINUE TO execute them as continuous flow without stopping between each one

3.2 WHEN the agent presents the bootcamp introduction in Step 4 THEN the system SHALL CONTINUE TO present the full overview content (module table, mock data info, license info, track preview, glossary reference) in a single turn

3.3 WHEN the `ask-bootcamper` hook fires on `agentStop` during non-track-selection steps THEN the system SHALL CONTINUE TO generate contextual closing questions as before

3.4 WHEN the bootcamper provides a valid track selection (A/B/C/D or equivalent text like "demo", "fast", "beginner", "full") THEN the system SHALL CONTINUE TO interpret the response using the existing mapping logic and route to the correct starting module

3.5 WHEN the agent is in steps other than track selection that do not require mandatory user input THEN the system SHALL CONTINUE TO follow the existing pattern of not including inline WAIT instructions, relying on the `ask-bootcamper` hook for closing questions
