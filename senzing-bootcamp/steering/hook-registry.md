---
inclusion: manual
---

# Hook Registry

All 20 bootcamp hooks. The agent calls `createHook` with these parameters. Critical Hooks are created during onboarding (Step 1). Module Hooks are created when the bootcamper starts the associated module.

Full prompt text for each hook is in the corresponding `.kiro.hook` file under `senzing-bootcamp/hooks/`. Read the hook file to get the exact prompt when calling `createHook`.

## Critical Hooks (created during onboarding)

**ask-bootcamper** (agentStop → askAgent)

- id: `ask-bootcamper`
- name: `Ask Bootcamper`
- description: `Recaps what was accomplished and which files changed, then asks the bootcamper what to do next with a contextual 👉 question. Suppresses output entirely when a question is already pending.`

**capture-feedback** (promptSubmit → askAgent)

- id: `capture-feedback`
- name: `Capture Bootcamp Feedback`
- description: `Fires on every message submission. Instructs the agent to check for feedback trigger phrases and, if found, initiate the feedback workflow with automatic context capture.`

**code-style-check** (fileEdited → askAgent, filePatterns: `src/**/*.py, src/**/*.java, src/**/*.cs, src/**/*.rs, src/**/*.ts, src/**/*.js`)

- id: `code-style-check`
- name: `Code Style Check`
- description: `Automatically checks source code files for language-appropriate coding standards when edited.`

**commonmark-validation** (fileEdited → askAgent, filePatterns: `**/*.md`)

- id: `commonmark-validation`
- name: `CommonMark Validation`
- description: `Validates that all Markdown files conform to CommonMark standards when edited`

**enforce-feedback-path** (preToolUse → askAgent, toolTypes: write)

- id: `enforce-feedback-path`
- name: `Enforce Feedback File Path`
- description: `Before any write operation, checks if the agent is writing feedback content. If so, ensures it goes to docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md and nowhere else.`

**enforce-working-directory** (preToolUse → askAgent, toolTypes: write)

- id: `enforce-working-directory`
- name: `Enforce Working Directory Paths`
- description: `Checks that file write operations do not use /tmp, %TEMP%, or any path outside the working directory.`

**feedback-submission-reminder** (agentStop → askAgent)

- id: `feedback-submission-reminder`
- name: `Feedback Submission Reminder`
- description: `After track completion or graduation, checks for saved feedback and reminds the bootcamper to share it with the power author.`

**review-bootcamper-input** (promptSubmit → askAgent)

- id: `review-bootcamper-input`
- name: `Review Bootcamper Input`
- description: `Reviews each message submission for feedback trigger phrases and initiates the feedback workflow with automatic context capture.`

**verify-senzing-facts** (preToolUse → askAgent, toolTypes: write)

- id: `verify-senzing-facts`
- name: `Verify Senzing Facts Before Writing`
- description: `Reminds the agent to verify Senzing-specific facts via MCP tools before writing code or documentation that contains Senzing attribute names, SDK method calls, or configuration values.`

## Module Hooks (created when module starts)

**validate-data-files** — Module 4 (fileCreated → askAgent, filePatterns: `data/raw/*.*`)

- id: `validate-data-files`
- name: `Validate Data Files`
- description: `When new data files are added to data/raw/, checks file format, encoding, and basic readability to catch issues early.`

**analyze-after-mapping** — Module 5 (fileCreated → askAgent, filePatterns: `data/transformed/*.jsonl, data/transformed/*.json`)

- id: `analyze-after-mapping`
- name: `Analyze After Mapping`
- description: `After completing a mapping task, validates the transformation output using analyze_record for quality metrics and Senzing Generic Entity Specification conformance before proceeding to loading.`

**data-quality-check** — Module 5 (fileEdited → askAgent, filePatterns: `src/transform/*.*`)

- id: `data-quality-check`
- name: `Senzing Data Quality Check`
- description: `Automatically check data quality when transformation programs are saved`

**backup-before-load** — Module 6 (fileEdited → askAgent, filePatterns: `src/load/*.*`)

- id: `backup-before-load`
- name: `Backup Database Before Loading`
- description: `Remind to backup database before running loading programs`

**run-tests-after-change** — Module 6 (fileEdited → askAgent, filePatterns: `src/load/*.*, src/query/*.*, src/transform/*.*`)

- id: `run-tests-after-change`
- name: `Run Tests After Code Change`
- description: `Reminds the agent to run the test suite after source code changes in loading, query, or transformation programs.`

**verify-generated-code** — Module 6 (fileCreated → askAgent, filePatterns: `src/transform/*.*, src/load/*.*, src/query/*.*`)

- id: `verify-generated-code`
- name: `Verify Generated Code Runs`
- description: `When bootcamp source code is created, prompts the agent to run it on sample data and report results before moving on.`

**enforce-visualization-offers** — Module 7 (agentStop → askAgent)

- id: `enforce-visualization-offers`
- name: `Enforce Visualization Offers`
- description: `When the agent stops during Module 7, checks whether both visualization offers (entity graph and results dashboard) were made. If either was missed, prompts the agent to offer it before closing.`

**offer-visualization** — Module 7 (fileCreated → askAgent, filePatterns: `src/query/*`)

- id: `offer-visualization`
- name: `Offer Entity Graph Visualization`
- description: `After query programs are created in Module 7, prompts the agent to offer generating an interactive entity graph visualization.`

**deployment-phase-gate** — Module 11 (postTaskExecution → askAgent)

- id: `deployment-phase-gate`
- name: `Deployment Phase Gate`
- description: `After packaging tasks complete in Module 11, displays a phase gate prompt asking the bootcamper whether to proceed to deployment or stop. Checks config/bootcamp_progress.json to confirm the current module is 11 or 12 before acting.`

**backup-project-on-request** — any module (userTriggered → askAgent)

- id: `backup-project-on-request`
- name: `Backup Project on Request`
- description: `Run project backup when user clicks the hook button.`

**git-commit-reminder** — any module (userTriggered → askAgent)

- id: `git-commit-reminder`
- name: `Git Commit Reminder`
- description: `Reminds the user to commit their work after completing a module. Triggered manually via button click.`
