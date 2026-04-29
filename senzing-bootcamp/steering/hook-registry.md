---
inclusion: manual
---

# Hook Registry

All 18 bootcamp hooks are defined below. The agent reads these definitions and calls the `createHook` tool with the specified parameters. Critical Hooks are created during onboarding (Step 1). Module Hooks are created when the bootcamper starts the associated module.

## Critical Hooks (created during onboarding)

**ask-bootcamper** (agentStop → askAgent)

Prompt: "If your previous output already ends with a 👉 question, do nothing. Otherwise, if no files changed and no substantive work was done, skip the recap and just ask a contextual 👉 question about what the bootcamper wants to do next. Otherwise, recap: (1) what you accomplished, (2) files created or modified (with paths). Then end with a contextual 👉 question asking the bootcamper what to do next. Keep it concise."

- id: `ask-bootcamper`
- name: `Ask Bootcamper`
- description: `Recaps what was accomplished and which files changed, then asks the bootcamper what to do next with a contextual 👉 question.`

**capture-feedback** (promptSubmit → askAgent)

Prompt: "Check if the bootcamper's message contains any of these feedback trigger phrases (case-insensitive): "bootcamp feedback", "power feedback", "submit feedback", "provide feedback", "I have feedback", "report an issue". If NONE of these phrases appear in the message, produce no output at all — do not acknowledge, do not explain, do not print anything. If a trigger phrase IS found, immediately do the following: (1) Read config/bootcamp_progress.json to get the current module number and completed modules. If the file doesn't exist, record module as "Unknown". (2) Note what the bootcamper was doing in the recent conversation. (3) Note which files are open in the editor. (4) Load steering file feedback-workflow.md and follow its complete workflow, pre-filling the context fields with what you just captured. Do NOT ask the bootcamper to re-explain their context — you already have it."

- id: `capture-feedback`
- name: `Capture Bootcamp Feedback`
- description: `Fires on every message submission. Checks for feedback trigger phrases and initiates the feedback workflow with automatic context capture.`

**code-style-check** (fileEdited → askAgent, filePatterns: `*.py, *.java, *.cs, *.rs, *.ts, *.js`)

Prompt: "A source code file was just edited. Check it for language-appropriate coding standards (Python: PEP-8 with max line length 100; Java: standard conventions; C#: .NET conventions; Rust: rustfmt/clippy; TypeScript: ESLint conventions). If violations are found, suggest specific fixes. If compliant, acknowledge briefly and continue."

- id: `code-style-check`
- name: `Code Style Check`
- description: `Automatically checks source code files for language-appropriate coding standards when edited. For Python: PEP-8. For Java: standard conventions. For C#: .NET conventions. For Rust: rustfmt/clippy. For TypeScript: ESLint conventions.`

**commonmark-validation** (fileEdited → askAgent, filePatterns: `**/*.md`)

Prompt: "The markdown file that was just edited should be validated for CommonMark compliance. Please check for:

1. MD022: Headings should be surrounded by blank lines
2. MD040: Fenced code blocks should have a language specified
3. Bold text followed by colons should use format: **Label:** (with space before colon)
4. MD031: Fenced code blocks should be surrounded by blank lines
5. MD032: Lists should be surrounded by blank lines

EXCEPTION: If the file is CHANGELOG.md, ignore MD024 (duplicate headings) — repeated ### Added, ### Changed, ### Fixed, ### Removed headings under different version sections are standard Keep a Changelog format and should not be flagged.

If any issues are found, fix them automatically to maintain CommonMark compliance across all documentation."

- id: `commonmark-validation`
- name: `CommonMark Validation`
- description: `Validates that all Markdown files conform to CommonMark standards when edited`

**enforce-feedback-path** (preToolUse → askAgent, toolTypes: write)

Prompt: "Check if you are currently in the feedback collection workflow (i.e., the bootcamper said 'bootcamp feedback', 'power feedback', or similar, and you are writing a feedback entry). If you are NOT in the feedback workflow, produce no output at all — do not acknowledge, do not explain, do not print anything. If you ARE writing feedback content (an improvement entry with Date, Module, Priority, Category, What Happened, Why It's a Problem sections), verify the target file path is exactly 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md'. If the path is different, STOP and redirect the write to 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md' instead. Do NOT write feedback to any other file. Do NOT submit feedback to any external service."

- id: `enforce-feedback-path`
- name: `Enforce Feedback File Path`
- description: `Before any write operation, checks if the agent is writing feedback content. If so, ensures it goes to docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md and nowhere else.`

**enforce-working-directory** (preToolUse → askAgent, toolTypes: write)

Prompt: "Before writing this file, verify: Does the file path or any path in the file content reference /tmp/, %TEMP%, ~/Downloads, or any location outside the working directory? If all paths are within the working directory, produce no output at all — do not acknowledge, do not explain, do not print anything. If so, replace those paths with project-relative equivalents (database/G2C.db for databases, data/temp/ for temporary files, src/ for source code). Do NOT proceed with the write if it would place files outside the working directory."

- id: `enforce-working-directory`
- name: `Enforce Working Directory Paths`
- description: `Checks that file write operations do not use /tmp, %TEMP%, or any path outside the working directory. Enforces the file storage policy automatically.`

**verify-senzing-facts** (preToolUse → askAgent, toolTypes: write)

Prompt: "If the file contains no Senzing-specific content, or all Senzing content was already verified via MCP tools, produce no output at all — do not acknowledge, do not explain, do not print anything. Before writing this file, verify that any Senzing-specific content (attribute names, SDK method signatures, configuration values, error code explanations) was retrieved from the Senzing MCP server tools (mapping_workflow, generate_scaffold, get_sdk_reference, search_docs, explain_error_code, sdk_guide) and not stated from training data. Per SENZING_INFORMATION_POLICY.md, all Senzing facts must come from MCP tools."

- id: `verify-senzing-facts`
- name: `Verify Senzing Facts Before Writing`
- description: `Reminds the agent to verify Senzing-specific facts via MCP tools before writing code or documentation that contains Senzing attribute names, SDK method calls, or configuration values.`

## Module Hooks (created when module starts)

**analyze-after-mapping** — Module 5 (fileCreated → askAgent, filePatterns: `data/transformed/*.jsonl, data/transformed/*.json`)

Prompt: "A new Senzing JSON file was created in data/transformed/. Before proceeding to loading (Module 6), use the analyze_record MCP tool to validate a sample of records from this file. Check feature distribution, attribute coverage, and data quality. Quality score should be >70% before loading."

- id: `analyze-after-mapping`
- name: `Analyze After Mapping`
- description: `After completing a mapping task, reminds the agent to validate the transformation output using analyze_record before proceeding to loading.`

**data-quality-check** — Module 5 (fileEdited → askAgent, filePatterns: `src/transform/*.*`)

Prompt: "The transformation program was just updated. Please review the changes and suggest running data quality validation tests to ensure the output still meets quality standards (>70% attribute coverage)."

- id: `data-quality-check`
- name: `Senzing Data Quality Check`
- description: `Automatically check data quality when transformation programs are saved`

**validate-senzing-json** — Module 5 (fileEdited → askAgent, filePatterns: `data/transformed/*.jsonl, data/transformed/*.json`)

Prompt: "Senzing JSON output was modified. Please use the analyze_record MCP tool to validate a sample of records from this file to ensure they conform to the Senzing Generic Entity Specification."

- id: `validate-senzing-json`
- name: `Validate Senzing JSON Output`
- description: `Validate Senzing JSON format when transformation output files are created or modified`

**backup-before-load** — Module 6 (fileEdited → askAgent, filePatterns: `src/load/*.*`)

Prompt: "A loading program was modified. Before running this in production, remind the user to backup the database using: python scripts/backup_project.py"

- id: `backup-before-load`
- name: `Backup Database Before Loading`
- description: `Remind to backup database before running loading programs`

**run-tests-after-change** — Module 6 (fileEdited → askAgent, filePatterns: `src/load/*.*, src/query/*.*, src/transform/*.*`)

Prompt: "Source code was modified. If tests exist in the tests/ directory, remind the user to run them to verify the change didn't break anything. Suggest the appropriate test command for the chosen language."

- id: `run-tests-after-change`
- name: `Run Tests After Code Change`
- description: `Reminds the agent to run the test suite after source code changes in loading, query, or transformation programs.`

**verify-generated-code** — Module 6 (fileCreated → askAgent, filePatterns: `src/transform/*.*, src/load/*.*, src/query/*.*`)

Prompt: "A new bootcamp source file was created. Before moving to the next step, verify this code actually runs: (1) Execute it on a small sample (10-100 records from data/samples/ or data/raw/). (2) Check for errors or exceptions. (3) If it produces output, inspect the first few records. (4) Report the results to the bootcamper — did it work, and if not, what needs fixing? Do not skip this verification step."

- id: `verify-generated-code`
- name: `Verify Generated Code Runs`
- description: `When bootcamp source code is created, prompts the agent to run it on sample data and report results before moving on.`

**enforce-visualization-offers** — Module 7 (agentStop → askAgent)

Prompt: "First, read `config/bootcamp_progress.json` and check the `current_module` field. If the current module is NOT 7, do nothing — let the conversation end normally.

If the current module IS 7, review the conversation history and check whether you offered BOTH of these visualizations during this interaction:

1. **Entity graph visualization** — an interactive force-directed network graph of resolved entities (offered after exploratory queries in step 3)
2. **Results dashboard** — an HTML page showing query results and validation metrics (offered after documenting findings in step 7)

If BOTH were offered (regardless of whether the bootcamper accepted or declined), do nothing — the requirement is satisfied.

If EITHER visualization was NOT offered, display this message:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊  MODULE 7 VISUALIZATION CHECK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Then, for each visualization that was NOT offered, ask the bootcamper:

- If the entity graph was not offered: "Before we wrap up — would you like me to help you build an interactive entity graph? It shows resolved entities as a force-directed network with clustering, search, and detail panels."
- If the results dashboard was not offered: "Before we wrap up — would you like me to create a web page showing your query results and validation metrics?"

WAIT for the bootcamper's response before finishing. They may accept or decline — both are fine."

- id: `enforce-visualization-offers`
- name: `Enforce Visualization Offers`
- description: `When the agent stops during Module 7, checks whether both visualization offers (entity graph and results dashboard) were made. If either was missed, prompts the agent to offer it before closing.`

**offer-visualization** — Module 7 (fileCreated → askAgent, filePatterns: `src/query/*`)

Prompt: "A query program was just created. If the bootcamper is in Module 7 and hasn't been offered the entity graph visualization yet, offer it: 'Would you like me to help you build an interactive entity graph visualization? It shows resolved entities as a force-directed network graph with clustering, search, and detail panels. I can create a self-contained HTML file you can open in any browser.' If they accept, load steering file visualization-guide.md and follow its workflow."

- id: `offer-visualization`
- name: `Offer Entity Graph Visualization`
- description: `After query programs are created in Module 7, prompts the agent to offer generating an interactive entity graph visualization.`

**deployment-phase-gate** — Module 11 (postTaskExecution → askAgent)

Prompt: "First, read `config/bootcamp_progress.json` and check the `current_module` field. If the current module is NOT 11 and NOT 12, do nothing — let the conversation continue normally. If the current module IS 11 or 12, do the following:

Display a clear packaging-complete summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦  PACKAGING PHASE COMPLETE — PHASE GATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Everything from the packaging phase is done:
✅ Code containerized (Dockerfile + docker-compose.yml)
✅ Multi-environment config (dev/staging/prod)
✅ CI/CD pipeline configured
✅ Pre-deployment checklist verified
✅ Rollback plan documented

⚠️  Nothing has been deployed. No changes were made to any
    target environment. Everything so far was local
    preparation work. It is completely safe to stop here.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Then ask: "Ready to deploy now, or prefer to stop here and deploy later on your own?"

WAIT for the bootcamper's response. Do NOT proceed to any deployment steps (Steps 12–15) until the bootcamper explicitly says they want to deploy."

- id: `deployment-phase-gate`
- name: `Deployment Phase Gate`
- description: `After packaging tasks complete in Module 11, displays a phase gate prompt asking the bootcamper whether to proceed to deployment or stop. Checks config/bootcamp_progress.json to confirm the current module is 11 or 12 before acting.`

**backup-project-on-request** — any module (userTriggered → askAgent)

Prompt: "The user wants to back up their project. Run the backup script: python3 scripts/backup_project.py (on Linux/macOS) or python scripts/backup_project.py (on Windows). Create the backups/ directory first if it doesn't exist."

- id: `backup-project-on-request`
- name: `Backup Project on Request`
- description: `Run project backup when user clicks the hook button. Avoids firing on every prompt — use the manual trigger button in the Agent Hooks panel instead.`

**git-commit-reminder** — any module (userTriggered → askAgent)

Prompt: "The user wants to commit their bootcamp progress. Check config/bootcamp_progress.json for the current module number and list of completed modules. Then suggest a git commit with a descriptive message like: git add . && git commit -m "Complete Module [N]: [Module Name]". Show the user the command and ask if they'd like you to run it."

- id: `git-commit-reminder`
- name: `Git Commit Reminder`
- description: `Reminds the user to commit their work after completing a module. Triggered manually via button click.`
