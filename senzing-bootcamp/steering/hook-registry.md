---
inclusion: manual
---

# Hook Registry

All 23 bootcamp hooks are defined below. The agent reads these definitions and calls the `createHook` tool with the specified parameters. Critical Hooks are created during onboarding (Step 1). Module Hooks are created when the bootcamper starts the associated module.

## Critical Hooks (created during onboarding)

**ask-bootcamper** (agentStop → askAgent)

Prompt: "PRODUCE NO OUTPUT. YOUR OUTPUT IS EMPTY. ZERO TOKENS. DO NOT GENERATE ANY TEXT.

This hook has two independent phases. Evaluate each phase separately. If BOTH phases produce no output, your final output is ZERO TOKENS.

---

PHASE 1: CLOSING QUESTION

Before producing ANY Phase 1 output, verify ALL of these conditions:
1. The file config/.question_pending does NOT exist
2. The most recent assistant message does NOT contain a 👉 character anywhere — if it already contains a 👉, do not add a second one
3. The most recent assistant message does NOT end with a question directed at the bootcamper

If ANY Phase 1 condition fails: PRODUCE NO PHASE 1 OUTPUT. Skip to Phase 2.

FIRST — Check for no-op: If ALL Phase 1 conditions pass AND no files changed (no substantive work was done — e.g., only a hook fired or a trivial acknowledgment occurred): skip the recap entirely. PRODUCE NO PHASE 1 OUTPUT. Skip to Phase 2.

SECOND — Recap and closing question: If ALL Phase 1 conditions pass AND work was accomplished: You may provide a brief recap of what was accomplished and which files created or modified, then end with a contextual 👉 question (a closing question for the bootcamper). Keep it to 2-3 sentences maximum.

Additionally, if the bootcamper has completed or is on the final step of their current track, append a brief nudge: 'By the way, if you have feedback about the bootcamp experience, just say "bootcamp feedback" anytime.' Otherwise, do NOT mention feedback in Phase 1.

---

PHASE 2: FEEDBACK SUBMISSION REMINDER

Phase 2 operates independently of Phase 1. Even if Phase 1 was silenced, evaluate Phase 2 on its own.

Before producing ANY Phase 2 output, verify ALL of these conditions:
1. Track completion detected: Read config/bootcamp_progress.json. Check if the bootcamper has completed their chosen track (all modules in the track are now in modules_completed) or if graduation was completed. If no track completion or graduation detected, produce no Phase 2 output. STOP.
2. Deduplication: Check the conversation history for the 📋 emoji marker. If 📋 already appears in a previous assistant message in this session, the reminder was already shown — produce no Phase 2 output. STOP.
3. Feedback exists: Check if docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md exists AND contains at least one '## Improvement:' heading (indicating real feedback entries, not just the template). If the file does not exist or contains no ## Improvement: headings, produce no Phase 2 output. STOP.

If ALL three Phase 2 conditions pass, append:

📋 You have saved feedback in docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md. To share it with the Senzing team, you can:
- Email it to support@senzing.com with subject 'Senzing Bootcamp Power Feedback'
- Open a GitHub issue with the feedback content
- Copy the file path and attach it to your preferred channel

Do not automatically send email or create GitHub issues — wait for explicit bootcamper confirmation. If the bootcamper declines (no, skip, not now), accept without re-prompting about feedback sharing again.

---

CRITICAL: If you are uncertain about ANY condition in either phase, default to SILENCE for that phase. Silence is always safe. Do not fabricate user responses or assume a choice on the bootcamper's behalf."

- id: `ask-bootcamper`
- name: `Ask Bootcamper`
- description: `Silence-first agentStop hook with dual responsibility: (1) Phase 1 produces a recap + closing question only when no question is already pending, with a near-completion feedback nudge; (2) Phase 2 independently reminds the bootcamper to share saved feedback after track completion.`

**code-style-check** (fileEdited → askAgent, filePatterns: `src/**/*.py, src/**/*.java, src/**/*.cs, src/**/*.rs, src/**/*.ts, src/**/*.js`)

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

Prompt: "Check if you are currently in the feedback collection workflow (i.e., the bootcamper said 'bootcamp feedback', 'power feedback', or similar, and you are writing a feedback entry). If you are NOT in the feedback workflow, produce no output at all — do not acknowledge, do not explain, do not print anything. STOP immediately and return nothing. Your response must be completely empty — zero tokens, zero characters. If you ARE writing feedback content (an improvement entry with Date, Module, Priority, Category, What Happened, Why It's a Problem sections), verify the target file path is exactly 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md'. If the path is different, STOP and redirect the write to 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md' instead. Do NOT write feedback to any other file. Do NOT submit feedback to any external service."

- id: `enforce-feedback-path`
- name: `Enforce Feedback File Path`
- description: `Before any write operation, checks if the agent is writing feedback content. If so, ensures it goes to docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md and nowhere else.`

**enforce-working-directory** (preToolUse → askAgent, toolTypes: write)

Prompt: "Before writing this file, verify: Does the file path or any path in the file content reference /tmp/, %TEMP%, ~/Downloads, or any location outside the working directory? If all paths are within the working directory, produce no output at all — do not acknowledge, do not explain, do not print anything. STOP immediately and return nothing. Your response must be completely empty — zero tokens, zero characters. If so, replace those paths with project-relative equivalents (database/G2C.db for databases, data/temp/ for temporary files, src/ for source code). Do NOT proceed with the write if it would place files outside the working directory."

- id: `enforce-working-directory`
- name: `Enforce Working Directory Paths`
- description: `Checks that file write operations do not use /tmp, %TEMP%, or any path outside the working directory. Enforces the file storage policy automatically.`

**review-bootcamper-input** (promptSubmit → askAgent)

Prompt: "Check if the bootcamper's message contains any of these feedback trigger phrases (case-insensitive): "bootcamp feedback", "power feedback", "submit feedback", "provide feedback", "I have feedback", "report an issue". Also check for status trigger phrases (case-insensitive): "where am I", "status", "what step am I on", "show progress", "how far along am I". If NONE of these phrases appear in the message, produce no output at all — do not acknowledge, do not explain, do not print anything. If a STATUS trigger phrase IS found, output exactly: STATUS_TRIGGER_DETECTED — the agent should respond with the inline status format from inline-status.md. If a FEEDBACK trigger phrase IS found, immediately do the following: (1) Read config/bootcamp_progress.json to get the current module number and completed modules. If the file doesn't exist, record module as "Unknown". (2) Note what the bootcamper was doing in the recent conversation. (3) Note which files are open in the editor. (4) Load steering file feedback-workflow.md and follow its complete workflow, pre-filling the context fields with what you just captured. Do NOT ask the bootcamper to re-explain their context — you already have it."

- id: `review-bootcamper-input`
- name: `Review Bootcamper Input`
- description: `Reviews each message submission for feedback trigger phrases and initiates the feedback workflow with automatic context capture.`

**verify-senzing-facts** (preToolUse → askAgent, toolTypes: write)

Prompt: "If the file contains no Senzing-specific content, or all Senzing content was already verified via MCP tools, produce no output at all — do not acknowledge, do not explain, do not print anything. STOP immediately and return nothing. Your response must be completely empty — zero tokens, zero characters. Before writing this file, verify that any Senzing-specific content (attribute names, SDK method signatures, configuration values, error code explanations) was retrieved from the Senzing MCP server tools (mapping_workflow, generate_scaffold, get_sdk_reference, search_docs, explain_error_code, sdk_guide) and not stated from training data. Per SENZING_INFORMATION_POLICY.md, all Senzing facts must come from MCP tools."

- id: `verify-senzing-facts`
- name: `Verify Senzing Facts Before Writing`
- description: `Reminds the agent to verify Senzing-specific facts via MCP tools before writing code or documentation that contains Senzing attribute names, SDK method calls, or configuration values.`

## Module Hooks (created when module starts)

**verify-sdk-setup** — Module 2 (fileEdited → askAgent, filePatterns: `config/senzing_config.*, config/bootcamp_preferences.yaml, database/*.*`)

Prompt: "A configuration or database file was modified. If the bootcamper is in Module 2 (SDK Setup), run a quick verification: check that database/G2C.db exists and is accessible, and that the Senzing engine can initialize with the current config. If not in Module 2, produce no output. If verification fails, present the error and suggest running: python3 senzing-bootcamp/scripts/preflight.py"

- id: `verify-sdk-setup`
- name: `Verify SDK Setup`
- description: `After config or environment files change during Module 2, re-verifies that the Senzing SDK setup is still valid.`

**validate-data-files** — Module 4 (fileCreated → askAgent, filePatterns: `data/raw/*.*`)

Prompt: "A new data file was added to data/raw/. Before proceeding, do a quick sanity check: (1) Can the file be read without encoding errors? Try reading the first 10 lines. (2) Is the format recognizable (CSV, JSON, JSONL, XML, TSV)? (3) Does it contain at least a few records? (4) Are there obvious issues like binary content, empty file, or corrupted data? Report what you find to the bootcamper. If the file looks good, say so briefly. If there are issues, explain what's wrong and suggest how to fix it."

- id: `validate-data-files`
- name: `Validate Data Files`
- description: `When new data files are added to data/raw/, checks file format, encoding, and basic readability to catch issues early.`

**analyze-after-mapping** — Module 5 (fileCreated → askAgent, filePatterns: `data/transformed/*.jsonl, data/transformed/*.json`)

Prompt: "A new Senzing JSON file was created in data/transformed/. Before proceeding to loading (Module 6), use the analyze_record MCP tool to validate a sample of records from this file. Check feature distribution, attribute coverage, and data quality. Quality score should be >70% before loading. Also verify that records conform to the Senzing Generic Entity Specification.

ADDITIONALLY: Verify that docs/{source_name}_mapper.md exists (extract source name from the transformed filename, e.g., "customers" from "customers.jsonl"). If it does not exist, state: 'The per-source mapping specification is missing. Create docs/{source_name}_mapper.md before proceeding to the next source or to loading.'"

- id: `analyze-after-mapping`
- name: `Analyze After Mapping`
- description: `After completing a mapping task, validates the transformation output using analyze_record for quality metrics and Senzing Generic Entity Specification conformance before proceeding to loading.`

**data-quality-check** — Module 5 (fileEdited → askAgent, filePatterns: `src/transform/*.*`)

Prompt: "The transformation program was just updated. Please review the changes and suggest running data quality validation tests to ensure the output still meets quality standards (>70% attribute coverage)."

- id: `data-quality-check`
- name: `Senzing Data Quality Check`
- description: `Automatically check data quality when transformation programs are saved`

**enforce-mapping-spec** — Module 5 (fileCreated → askAgent, filePatterns: `data/transformed/*.jsonl, data/transformed/*.json`)

Prompt: "A transformed data file was just created in data/transformed/.

REQUIRED CHECK: Extract the source name from the filename (e.g., "customers" from "customers.jsonl"). Check if the file docs/{source_name}_mapper.md exists.

If docs/{source_name}_mapper.md ALREADY EXISTS:
  Produce no output. STOP. Zero tokens. The mapping spec is in place.

If docs/{source_name}_mapper.md DOES NOT EXIST:
  You MUST create it NOW before doing any other work. Do not proceed to the next data source. Do not proceed to quality validation. Do not proceed to Module 6.

  Create docs/{source_name}_mapper.md with this structure:

  # Mapping Specification: {SOURCE_NAME}

  **Source file:** data/raw/{source_file}
  **Data source name:** {DATA_SOURCE}
  **Entity type:** Person / Organization / Both
  **Generated by:** mapping_workflow

  ## Field Mappings

  | Source Field | Senzing Attribute | Transformation | Notes |
  |---|---|---|---|
  | (fill from the mapping workflow results) |

  ## Mapping Decisions

  - (key decisions made during mapping)

  ## Quality Notes

  - (quality observations specific to this source)

  Fill in the actual field mappings from the mapping workflow you just completed. This file must be self-contained — a developer reading only this file should be able to recreate the transformation program in any language.

  Do not proceed to the next data source or any other work until this file is created."

- id: `enforce-mapping-spec`
- name: `Enforce Mapping Specification`
- description: `When transformed data is created, verifies that a per-source mapping specification markdown exists in docs/. Blocks progression until the mapping spec is created.`

**backup-before-load** — Module 6 (fileEdited → askAgent, filePatterns: `src/load/*.*`)

Prompt: "A loading program was modified. Before running this in production, remind the user to backup the database using: python3 scripts/backup_project.py (on Linux/macOS) or python scripts/backup_project.py (on Windows)"

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

**validate-benchmark-results** — Module 8 (fileEdited → askAgent, filePatterns: `tests/performance/*.*`)

Prompt: "A benchmark script in tests/performance/ was just modified. Before recording results, verify: (1) The script runs without errors on a small sample. (2) Output includes required metrics: records/sec for loading benchmarks, or p50/p95/p99 latency for query benchmarks. (3) Results are written to a structured format (JSON or markdown table) that can be compared across runs. If the script fails or produces unparseable output, suggest fixes before the bootcamper records baselines."

- id: `validate-benchmark-results`
- name: `Validate Benchmark Results`
- description: `When benchmark scripts are created or modified in tests/performance/, validates that they produce parseable output with required metrics (records/sec, latency percentiles).`

**security-scan-on-save** — Module 9 (fileEdited → askAgent, filePatterns: `src/security/*.*, config/*credentials*, config/*secret*, .env*`)

Prompt: "A security-related file was just modified. If the bootcamper is in Module 9 (Security Hardening), remind them to re-run the appropriate vulnerability scanner for their language (Python: bandit; Java: spotbugs; C#: dotnet list package --vulnerable; Rust: cargo audit; TypeScript: npm audit) to verify no new vulnerabilities were introduced. If not in Module 9, produce no output."

- id: `security-scan-on-save`
- name: `Security Scan on Save`
- description: `When security-related files are modified during Module 9, reminds the agent to re-run vulnerability scanning to catch regressions.`

**validate-alert-config** — Module 10 (fileCreated → askAgent, filePatterns: `monitoring/alerts/*.*, monitoring/dashboards/*.*`)

Prompt: "A monitoring configuration file was just created. Validate: (1) Alert rules have required fields: name, condition, severity, and action. (2) Severity levels are one of: Critical, Warning, Info. (3) Thresholds are numeric and reasonable (e.g., error rate percentages between 0-100, latency in milliseconds). (4) Dashboard configs reference metrics that are actually collected by the metrics_collector. Report any issues to the bootcamper with suggested fixes."

- id: `validate-alert-config`
- name: `Validate Alert Configuration`
- description: `When monitoring configuration files are created or modified during Module 10, validates alert rule syntax and completeness.`

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
