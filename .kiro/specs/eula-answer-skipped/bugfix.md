# Bugfix Requirements Document

## Introduction

During Module 2 Step 3 (Install Senzing SDK), the agent asks the bootcamper to accept the Senzing EULA but does not wait for the bootcamper's explicit response before continuing with the remaining installation steps. The EULA is a legal agreement — the agent cannot assume acceptance. Additionally, because the EULA question lacks the 👉 marker, the `ask-bootcamper` agentStop hook does not detect it as a pending question, which can cause the hook to fire and produce a second question in the same interaction. The bootcamper only gets one chance to respond, so one question goes unanswered.

The root cause has two parts:

1. The Module 2 steering file (`module-02-sdk-setup.md`) Step 3 lists EULA acceptance as item 3 in a continuous numbered list of installation sub-steps ("1. Add repo, 2. Install package, 3. Accept EULA, 4. Install bindings") with no explicit instruction to STOP and wait for the bootcamper's response after the EULA question.
2. The EULA question does not use the 👉 marker that the `ask-bootcamper` agentStop hook scans for to detect pending questions and suppress further output.

This is the same pattern as the `agent-skips-git-question` bug — the steering file says to do something that requires user input but does not explicitly instruct the agent to stop and wait, and does not use the 👉 marker.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent reaches Module 2 Step 3 and presents the EULA acceptance question THEN the system asks the EULA question but immediately continues with the remaining installation sub-steps (language-specific SDK bindings) without waiting for the bootcamper's explicit acceptance or rejection.

1.2 WHEN the ask-bootcamper agentStop hook fires after the agent asks the EULA question THEN the hook does not detect the question as pending because the question text lacks the 👉 marker, so the hook may produce additional output or a second question instead of suppressing output.

1.3 WHEN the hook produces a second question in the same interaction as the EULA question THEN the bootcamper only has one chance to respond, so one of the two questions goes unanswered and the agent cannot determine which question the bootcamper answered.

1.4 WHEN the agent proceeds past the EULA question without waiting THEN the system continues installing language-specific SDK bindings and writes the Step 3 checkpoint regardless of whether the bootcamper accepted or declined the EULA.

### Expected Behavior (Correct)

2.1 WHEN the agent reaches Module 2 Step 3 and the EULA needs to be accepted THEN the system SHALL present the EULA acceptance question using the 👉 marker and STOP, waiting for the bootcamper's explicit response before proceeding with any subsequent installation sub-steps.

2.2 WHEN the ask-bootcamper agentStop hook fires after the agent asks the 👉-prefixed EULA question THEN the hook SHALL detect the pending question and suppress all additional output, preserving the one-question-at-a-time flow.

2.3 WHEN the bootcamper explicitly accepts the EULA THEN the system SHALL proceed with the remaining installation sub-steps (language-specific SDK bindings) and write the Step 3 checkpoint.

2.4 WHEN the bootcamper declines the EULA THEN the system SHALL stop the installation process and explain that the Senzing SDK cannot be used without EULA acceptance, without proceeding to install language-specific bindings or writing the Step 3 checkpoint as complete.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent executes Module 2 Step 3 sub-steps that do not require user input (adding the package repository, installing the SDK package) THEN the system SHALL CONTINUE TO execute those sub-steps in sequence without stopping.

3.2 WHEN the agent asks other 👉-prefixed questions in any module THEN the ask-bootcamper hook SHALL CONTINUE TO detect those questions as pending and suppress additional output.

3.3 WHEN Module 2 Steps 1, 2, and 4 through 9 execute THEN the system SHALL CONTINUE TO follow their existing flow, checkpoint logic, and question-asking behavior unchanged.

3.4 WHEN the bootcamper has already accepted the EULA in a previous session or the EULA was previously accepted on the system THEN the system SHALL CONTINUE TO skip the EULA question and proceed with the remaining installation sub-steps without stopping.
