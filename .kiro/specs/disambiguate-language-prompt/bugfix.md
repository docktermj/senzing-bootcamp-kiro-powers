# Bugfix Requirements Document

## Introduction

The onboarding language-selection step (Step 2 in `onboarding-flow.md`) uses the word "language" without the qualifier "programming." This is ambiguous — a bootcamper could interpret it as asking about a natural/spoken language rather than a programming language. Since the onboarding flow offers Python, Java, C#, Rust, and TypeScript as choices, the prompt must explicitly say "programming language" to eliminate confusion at this first real decision point.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent presents the language-selection question at onboarding Step 2 THEN the system uses the word "language" without the qualifier "programming," producing an ambiguous prompt (e.g., "Which language would you like to use?")

1.2 WHEN a bootcamper reads the language-selection prompt without seeing the listed options THEN the system provides no disambiguation between natural/spoken language and programming language

### Expected Behavior (Correct)

2.1 WHEN the agent presents the language-selection question at onboarding Step 2 THEN the system SHALL use the phrase "programming language" in the prompt (e.g., "Which programming language would you like to use?")

2.2 WHEN a bootcamper reads the language-selection prompt THEN the system SHALL make it unambiguous that the question refers to a programming language, regardless of whether the option list is visible

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent presents the language-selection step THEN the system SHALL CONTINUE TO display the MCP-returned list of supported languages for the bootcamper's platform

3.2 WHEN the agent detects a discouraged or unsupported language for the bootcamper's platform THEN the system SHALL CONTINUE TO relay the MCP server's warning and suggest alternatives

3.3 WHEN the bootcamper selects a programming language THEN the system SHALL CONTINUE TO persist the selection to `config/bootcamp_preferences.yaml` and load the corresponding language steering file

3.4 WHEN the bootcamper has not yet provided input at the language-selection mandatory gate THEN the system SHALL CONTINUE TO stop and wait for real input without assuming or fabricating a choice
