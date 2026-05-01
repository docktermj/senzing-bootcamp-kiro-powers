# Bugfix Requirements Document

## Introduction

During Module 1 Step 1, the agent asks "Would you like me to initialize a git repository for version control?" but does not wait for the bootcamper's response before continuing to Step 2. This bypasses the bootcamper's input, making the interaction feel scripted rather than conversational and undermining trust that the agent is listening.

The root cause has two parts:
1. The Module 1 steering file (`module-01-business-problem.md`) Step 1 says "ask" but does not explicitly instruct the agent to STOP and wait for the bootcamper's response before proceeding.
2. The git repo question does not use the 👉 marker that the `ask-bootcamper` agentStop hook scans for to detect pending questions and suppress further output.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent reaches Module 1 Step 1 and the workspace is not already a git repository THEN the system asks the git repo initialization question but immediately continues to Step 2 without waiting for the bootcamper's response.

1.2 WHEN the ask-bootcamper agentStop hook fires after the agent asks the git repo question THEN the hook does not detect the question as pending because the question text lacks the 👉 marker, so the hook may produce additional output or a second question instead of suppressing output.

1.3 WHEN the agent proceeds past the git repo question without waiting THEN the system writes the Step 1 checkpoint and begins Step 2 (data privacy reminder) regardless of whether the bootcamper wanted git initialized.

### Expected Behavior (Correct)

2.1 WHEN the agent reaches Module 1 Step 1 and the workspace is not already a git repository THEN the system SHALL ask the git repo initialization question using the 👉 marker and STOP, waiting for the bootcamper's explicit response before proceeding to any subsequent step.

2.2 WHEN the ask-bootcamper agentStop hook fires after the agent asks the 👉-prefixed git repo question THEN the hook SHALL detect the pending question and suppress all additional output, preserving the one-question-at-a-time flow.

2.3 WHEN the bootcamper responds to the git repo question THEN the system SHALL act on the response (initialize git if yes, skip if no) and only then proceed to Step 2 and write the Step 1 checkpoint.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the workspace is already a git repository at Module 1 Step 1 THEN the system SHALL CONTINUE TO skip the git repo question and proceed directly to Step 2 without prompting.

3.2 WHEN the agent asks other 👉-prefixed questions in any module THEN the ask-bootcamper hook SHALL CONTINUE TO detect those questions as pending and suppress additional output.

3.3 WHEN the bootcamper answers "no" to the git repo question THEN the system SHALL CONTINUE TO proceed to Step 2 without initializing a git repository.

3.4 WHEN Module 1 Steps 2 through 8 execute THEN the system SHALL CONTINUE TO follow their existing flow, checkpoint logic, and question-asking behavior unchanged.
