# Bugfix Requirements Document

## Introduction

During the bootcamp onboarding flow in `senzing-bootcamp/steering/onboarding-flow.md`, the full module list (Modules 1–12) is displayed twice to the bootcamper. Step 4 ("Bootcamp Introduction") instructs the agent to present a "Module overview table (1-12): what each does and why it matters" as part of the welcome overview. Step 5 ("Track Selection") then displays a separate "quick-reference module table" with the same 12 modules listed again before presenting the track options. This redundancy makes the welcome message unnecessarily long and cluttered.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent executes Step 5 (Track Selection) of the onboarding flow THEN the system displays a duplicate plain module number/title table that repeats the same module list already shown in Step 4's overview

1.2 WHEN a bootcamper reads the full onboarding welcome message THEN the system presents the module list twice — once as a descriptive overview table in Step 4 and again as a plain quick-reference table in Step 5 — creating unnecessary length and redundancy

### Expected Behavior (Correct)

2.1 WHEN the agent executes Step 5 (Track Selection) of the onboarding flow THEN the system SHALL present only the track descriptions (A through D) without repeating the module table, since the Step 4 overview already provides all module information needed

2.2 WHEN a bootcamper reads the full onboarding welcome message THEN the system SHALL present the module list exactly once — in the Step 4 overview table — keeping the welcome message concise and non-repetitive

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent executes Step 4 (Bootcamp Introduction) THEN the system SHALL CONTINUE TO present the module overview table (1-12) with descriptions of what each module does and why it matters

3.2 WHEN the agent executes Step 5 (Track Selection) THEN the system SHALL CONTINUE TO present the four track options (A: Quick Demo, B: Fast Track, C: Complete Beginner, D: Full Production) with their module sequences

3.3 WHEN the agent executes Step 5 (Track Selection) THEN the system SHALL CONTINUE TO include the Module 2 auto-insertion note and the response interpretation rules

3.4 WHEN a bootcamper selects a track THEN the system SHALL CONTINUE TO correctly map the selection to the appropriate starting module
