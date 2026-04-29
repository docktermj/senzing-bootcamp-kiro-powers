# Bugfix Requirements Document

## Introduction

During Module 2 Step 5 (Configure License), the agent checks the `licenses/` directory, finds no license file, and immediately assumes the evaluation license will be used — without presenting the bootcamper with their license options. Two separate feedback reports confirm this behavior. The module steering file (`senzing-bootcamp/steering/module-02-sdk-setup.md`) explicitly instructs the agent to ask about the bootcamper's license, but the current Step 5 wording uses an inline question with a WAIT instruction. Per the closing-question-ownership fix (`.kiro/specs/module-closing-question-ownership/`), the `ask-bootcamper` hook owns all closing questions, so Step 5 should present license information as content and let the hook generate the contextual 👉 question. The current instructions are ambiguous enough that the agent short-circuits the step by defaulting to evaluation mode.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent executes Module 2 Step 5 and finds no license file in any of the three checked locations THEN the system skips presenting the license options to the bootcamper and immediately defaults to evaluation mode, removing the bootcamper's choice to provide a custom license

1.2 WHEN the agent executes Module 2 Step 5 and the steering file instructs it to ask an inline question ("Do you have a Senzing license file or BASE64 key?") with a WAIT instruction THEN the step's structure conflicts with the `ask-bootcamper` hook's closing-question ownership — the agent either asks the question itself (violating hook ownership) or skips it entirely (the observed bug), because the inline question format is ambiguous about whether the agent or the hook should ask

1.3 WHEN the agent executes Module 2 Step 5 and finds an existing license file THEN the steering file instructs the agent to ask an inline confirmation question ("I found a license at [location]. Use this one?") with a WAIT instruction, which has the same hook-ownership conflict as the no-license-found path

### Expected Behavior (Correct)

2.1 WHEN the agent executes Module 2 Step 5 and finds no license file in any checked location THEN the system SHALL present the license options as informational content — explaining what the evaluation license provides (500 records), how to provide a custom license file or BASE64 key, and where to obtain licenses — and then stop, allowing the `ask-bootcamper` hook to generate the contextual 👉 question about the bootcamper's license choice

2.2 WHEN the agent executes Module 2 Step 5 THEN the steering file SHALL NOT contain inline closing questions or WAIT-for-response instructions; instead it SHALL describe the information to present (license search results, evaluation vs. custom license options, how to provide a license) as content the agent must always show, and the `ask-bootcamper` hook SHALL generate the closing question

2.3 WHEN the agent executes Module 2 Step 5 and finds an existing license file THEN the system SHALL present the finding as informational content (location found, license details) and stop, allowing the `ask-bootcamper` hook to generate the contextual 👉 question about whether to use the found license

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent executes Module 2 Step 5 THEN the system SHALL CONTINUE TO check for licenses in the documented priority order: project-local `licenses/g2.lic` → `SENZING_LICENSE_PATH` env var → system CONFIGPATH → built-in evaluation

3.2 WHEN the bootcamper provides a BASE64 license key THEN the system SHALL CONTINUE TO direct them to decode it to `licenses/g2.lic` using the documented command, and SHALL CONTINUE TO never ask the user to paste a license key into chat

3.3 WHEN a project-local license exists THEN the system SHALL CONTINUE TO add `LICENSEFILE` to the engine config PIPELINE section and record `license: custom` in `config/bootcamp_preferences.yaml`

3.4 WHEN the bootcamper chooses the evaluation license THEN the system SHALL CONTINUE TO record `license: evaluation` in `config/bootcamp_preferences.yaml` and proceed without requiring a license file

3.5 WHEN the `ask-bootcamper` hook fires after the agent completes Step 5 THEN the system SHALL CONTINUE TO generate a contextual 👉 question based on the license information the agent just presented

3.6 WHEN the agent executes other Module 2 steps (Steps 1-4, 6-9) THEN the system SHALL CONTINUE TO follow those steps unchanged — the fix is scoped to Step 5 only
