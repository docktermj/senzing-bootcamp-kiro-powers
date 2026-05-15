---
inclusion: manual
---

# Hook Registry — Full Prompts

Complete hook definitions with prompt text for use with the `createHook` tool. Load this file when actively creating hooks during onboarding or module start.

For a quick reference of all hooks, see `hook-registry.md`.

## Critical Hooks (created during onboarding)

**ask-bootcamper** (agentStop → askAgent)

Prompt:

````text
DEFAULT OUTPUT: .
If BOTH phases below produce no output, your COMPLETE response is a single period character: .
Do NOT explain your reasoning. Do NOT describe condition checks. Do NOT output phrases like 'Phase 1 silenced' or 'No output needed'. Just output: .

CRITICAL: NEVER generate text beginning with 'Human:' or any text that represents what the bootcamper might say. If you detect yourself about to fabricate a user response, output only: .

This hook has two independent phases. Evaluate each phase separately.

---

PHASE 1: CLOSING QUESTION

Before producing ANY Phase 1 output, verify ALL of these conditions:
1. The file config/.question_pending does NOT exist
2. The most recent assistant message does NOT contain a 👉 character anywhere — if it already contains a 👉, do not add a second one
3. The most recent assistant message does NOT end with a question directed at the bootcamper

If ANY Phase 1 condition fails: Phase 1 output is none. Skip to Phase 2.

FIRST — Check for no-op: If ALL Phase 1 conditions pass AND the most recent assistant message contains no substantive content (e.g., only a trivial acknowledgment like "Got it" or "Understood" with no file changes, no recap, and no action taken): Phase 1 output is none. Skip to Phase 2.

NOTE: If files were edited (even by a hook-triggered action), that IS substantive work. Provide a closing question unless a 👉 question is already present.

SECOND — Recap and closing question: If ALL Phase 1 conditions pass AND work was accomplished: You may provide a brief recap of what was accomplished and which files created or modified, then end with a contextual 👉 question (a closing question for the bootcamper). Keep it to 2-3 sentences maximum.

Additionally, if the bootcamper has completed or is on the final step of their current track, append a brief nudge: 'By the way, if you have feedback about the bootcamp experience, just say "bootcamp feedback" anytime.' Otherwise, do NOT mention feedback in Phase 1.

---

PHASE 2: FEEDBACK SUBMISSION REMINDER

Phase 2 operates independently of Phase 1. Even if Phase 1 produced no output, evaluate Phase 2 on its own.

Before producing ANY Phase 2 output, verify ALL of these conditions:
1. Track completion detected: Read config/bootcamp_progress.json. Check if the bootcamper has completed their chosen track (all modules in the track are now in modules_completed) or if graduation was completed. If no track completion or graduation detected, Phase 2 output is none.
2. Deduplication: Check the conversation history for the 📋 emoji marker. If 📋 already appears in a previous assistant message in this session, the reminder was already shown — Phase 2 output is none.
3. Feedback exists: Check if docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md exists AND contains at least one '## Improvement:' heading (indicating real feedback entries, not just the template). If the file does not exist or contains no ## Improvement: headings, Phase 2 output is none.

If ALL three Phase 2 conditions pass, append:

📋 You have saved feedback in docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md. To share it with the Senzing team, you can:
- Email it to support@senzing.com with subject 'Senzing Bootcamp Power Feedback'
- Open a GitHub issue with the feedback content
- Copy the file path and attach it to your preferred channel

Do not automatically send email or create GitHub issues — wait for explicit bootcamper confirmation. If the bootcamper declines (no, skip, not now), accept without re-prompting about feedback sharing again.

---

REMEMBER: If both phases produced no output, your COMPLETE response is: .
````

- id: `ask-bootcamper`
- name: `to wait for your answer`
- description: `Silence-first agentStop hook with dual responsibility: (1) Phase 1 produces a recap + closing question only when no question is already pending, with a near-completion feedback nudge; (2) Phase 2 independently reminds the bootcamper to share saved feedback after track completion.`

**code-style-check** (fileEdited → askAgent, filePatterns: `src/**/*.py, src/**/*.java, src/**/*.cs, src/**/*.rs, src/**/*.ts, src/**/*.js`)

Prompt:

````text
A source code file was just edited. Check it for language-appropriate coding standards (Python: PEP-8 with max line length 100; Java: standard conventions; C#: .NET conventions; Rust: rustfmt/clippy; TypeScript: ESLint conventions). If violations are found, suggest specific fixes. If compliant, acknowledge briefly and continue.
````

- id: `code-style-check`
- name: `to check code style`
- description: `Automatically checks source code files for language-appropriate coding standards when edited. For Python: PEP-8. For Java: standard conventions. For C#: .NET conventions. For Rust: rustfmt/clippy. For TypeScript: ESLint conventions.`

**commonmark-validation** (fileEdited → askAgent, filePatterns: `**/*.md`)

Prompt:

````text
The markdown file that was just edited should be validated for CommonMark compliance. Please check for:

1. MD022: Headings should be surrounded by blank lines
2. MD040: Fenced code blocks should have a language specified
3. Bold text followed by colons should use format: **Label:** (with space before colon)
4. MD031: Fenced code blocks should be surrounded by blank lines
5. MD032: Lists should be surrounded by blank lines

EXCEPTION: If the file is CHANGELOG.md, ignore MD024 (duplicate headings) — repeated ### Added, ### Changed, ### Fixed, ### Removed headings under different version sections are standard Keep a Changelog format and should not be flagged.

If any issues are found, fix them automatically to maintain CommonMark compliance across all documentation.

After fixing issues: briefly state what was corrected (one sentence), then end with a contextual 👉 forward-moving question that guides the bootcamper to the next step in the current module workflow. Check `config/bootcamp_progress.json` for the current module and step to determine what comes next.

If no issues are found: output nothing. Proceed silently.
````

- id: `commonmark-validation`
- name: `to check Markdown style`
- description: `Validates that all Markdown files conform to CommonMark standards when edited`

**enforce-file-path-policies** (preToolUse → askAgent, toolTypes: write)

Prompt:

````text
QUICK CHECK — answer these two questions about the file being written:

Q1: Is the target path inside the working directory? (Not /tmp/, not %TEMP%, not ~/Downloads, not any absolute path outside the project)
Q2: Is this feedback content (has Date/Module/Priority/Category/What Happened sections) being written to a path OTHER than 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md'?

FAST PATH: If Q1 is YES (path is inside working directory) AND Q2 is NO (not misrouted feedback): Do not acknowledge. Do not explain. Do not print anything. Proceed silently.

Do not check file content for path references in the fast path. Do not acknowledge. Do not explain. Do not print anything. Proceed silently.

SLOW PATH: If Q1 is NO (path is outside working directory) OR Q2 is YES (feedback going to wrong file):
- For external paths: STOP. Tell the agent to use project-relative equivalents (database/G2C.db for databases, data/temp/ for temporary files, src/ for source code).
- For misrouted feedback: STOP. Redirect to docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md.

CONTENT CHECK (only if fast path passed): Does the file content reference /tmp/, %TEMP%, ~/Downloads, or any location outside the working directory? If YES: STOP and require replacement with project-relative equivalents. If NO: do nothing — proceed silently.
````

- id: `enforce-file-path-policies`
- name: `to make sure the file is in the project directory`
- description: `Before any write operation, enforces two path policies: (1) feedback content must go to docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md, and (2) no files may be written outside the working directory. Uses a fast path for project-relative non-feedback writes (proceeds silently) and a slow path for violations (outputs corrective instructions).`

**review-bootcamper-input** (promptSubmit → askAgent)

Prompt:

````text
Check if the bootcamper's message contains any of these feedback trigger phrases (case-insensitive): "bootcamp feedback", "power feedback", "submit feedback", "provide feedback", "I have feedback", "report an issue". Also check for status trigger phrases (case-insensitive): "where am I", "status", "what step am I on", "show progress", "how far along am I". If NONE of these phrases appear in the message, produce no output at all — do not acknowledge, do not explain, do not print anything. If a STATUS trigger phrase IS found, output exactly: STATUS_TRIGGER_DETECTED — the agent should respond with the inline status format from inline-status.md. If a FEEDBACK trigger phrase IS found, immediately do the following: (1) Read config/bootcamp_progress.json to get the current module number and completed modules. If the file doesn't exist, record module as "Unknown". (2) Note what the bootcamper was doing in the recent conversation. (3) Note which files are open in the editor. (4) Load steering file feedback-workflow.md and follow its complete workflow, pre-filling the context fields with what you just captured. Do NOT ask the bootcamper to re-explain their context — you already have it.
````

- id: `review-bootcamper-input`
- name: `to review what you said`
- description: `Reviews each message submission for feedback trigger phrases and initiates the feedback workflow with automatic context capture.`

## Module Hooks (created when module starts)

**validate-business-problem** — Module 1 (postTaskExecution → askAgent)

Prompt:

````text
Read `config/bootcamp_progress.json` and check the `current_module` field. If the current module is NOT 1, produce no output at all — do not acknowledge, do not explain, do not print anything. If the current module IS 1, validate the business problem definition by checking these three fields in the progress file:

1. **Data sources identified** — At least one data source must be listed (the records the bootcamper wants to resolve).
2. **Matching criteria defined** — The attributes to match on must be specified (e.g., name, address, date of birth).
3. **Success metrics documented** — The bootcamper must have described what successful entity resolution looks like for their use case.

If any of these fields are missing or empty, report which fields are incomplete and suggest the bootcamper address them before moving on. For example: "Your problem statement is missing matching criteria — please specify which attributes (name, address, etc.) you want Senzing to match on."

If all three fields are present and non-empty, confirm readiness: "Your business problem is fully defined. You have data sources identified, matching criteria set, and success metrics documented. Ready to proceed to Module 2."
````

- id: `validate-business-problem`
- name: `to validate your business problem`
- description: `After Module 1 tasks complete, validates that the bootcamper has identified data sources, defined matching criteria, and documented success metrics before proceeding to Module 2.`

**verify-sdk-setup** — Module 2 (fileEdited → askAgent, filePatterns: `config/senzing_config.*, config/bootcamp_preferences.yaml, database/*.*`)

Prompt:

````text
A configuration or database file was modified. If the bootcamper is in Module 2 (SDK Setup), run a quick verification: check that database/G2C.db exists and is accessible, and that the Senzing engine can initialize with the current config. If not in Module 2, produce no output. If verification fails, present the error and suggest running: python3 senzing-bootcamp/scripts/preflight.py
````

- id: `verify-sdk-setup`
- name: `to verify SDK setup`
- description: `After config or environment files change during Module 2, re-verifies that the Senzing SDK setup is still valid.`

**gate-module3-visualization** — Module 3 (preToolUse → askAgent, toolTypes: write)

Prompt:

````text
CHECK — Is this write updating `config/bootcamp_progress.json` to mark Module 3 as complete (adding 3 to modules_completed, or setting module_3_verification.status to 'passed')?

If NO (not a Module 3 completion write, or not writing to bootcamp_progress.json): produce no output at all. Do nothing.

If YES: Read the CURRENT contents of `config/bootcamp_progress.json` and check TWO conditions:

CONDITION A — Step 9 checkpoints exist:
- `module_3_verification.checks.web_service.status` equals `"passed"`
- `module_3_verification.checks.web_page.status` equals `"passed"`

CONDITION B — Step 9 was explicitly skipped:
- `skipped_steps` contains an entry with key `"3.9"`

If CONDITION A is true OR CONDITION B is true: produce no output at all. Do nothing.

If NEITHER condition is met: STOP. Do NOT allow this write. Output exactly:

⛔ BLOCKED: Module 3 cannot be marked complete — Step 9 (Web Service + Visualization) has not been executed. Load `module-03-phase2-visualization.md` and execute the full visualization step (generate web service, start server, verify 3 API endpoints, present URL to bootcamper). Only after web_service and web_page checkpoints show 'passed' can Module 3 be completed.

Do not proceed with the write operation.
````

- id: `gate-module3-visualization`
- name: `to gate Module 3 completion on visualization step`
- description: `Prevents Module 3 from being marked complete unless Step 9 (Web Service + Visualization) checkpoints are present in bootcamp_progress.json, or the step was explicitly skipped via the skip-step protocol.`

**verify-demo-results** — Module 3 (postTaskExecution → askAgent)

Prompt:

````text
Read `config/bootcamp_progress.json` and check the `current_module` field. If the current module is NOT 3, produce no output at all — do not acknowledge, do not explain, do not print anything. If the current module IS 3, verify the system verification results by checking:

1. **Entities were resolved** — Confirm that verification produced more than zero resolved entities from the loaded TruthSet records.
2. **Matches were found** — Confirm that at least two records were resolved to the same entity (i.e., the engine found genuine matches, not just singletons).
3. **TruthSet expectations met** — Compare the actual entity counts against the expected TruthSet results retrieved via MCP. Flag any deviation.

If verification produced only singletons (every record became its own entity with no matches), report this: "Verification ran but produced only singletons — no records were matched together. This indicates an engine or configuration problem, since the Senzing TruthSet contains records designed to match. Check the SDK configuration and database setup before proceeding."

If actual counts diverge from the TruthSet expectations, report the specific deltas: "Expected N resolved entities, got M. This deviation suggests a configuration issue. Review the TruthSet documentation via `search_docs` and check engine configuration before proceeding."

If the results match the TruthSet expectations, confirm success: "System verification passed — entity counts match the Senzing TruthSet expected output. Your setup is working correctly. Ready to proceed to Module 4."
````

- id: `verify-demo-results`
- name: `to verify demo results`
- description: `After Module 3 tasks complete, verifies that system verification produced entity resolution results matching the Senzing TruthSet expected output before marking the module complete.`

**validate-data-files** — Module 4 (fileCreated → askAgent, filePatterns: `data/raw/*.*`)

Prompt:

````text
A new data file was added to data/raw/. Before proceeding, do a quick sanity check: (1) Can the file be read without encoding errors? Try reading the first 10 lines. (2) Is the format recognizable (CSV, JSON, JSONL, XML, TSV)? (3) Does it contain at least a few records? (4) Are there obvious issues like binary content, empty file, or corrupted data? Report what you find to the bootcamper. If the file looks good, say so briefly. If there are issues, explain what's wrong and suggest how to fix it.
````

- id: `validate-data-files`
- name: `to validate data files`
- description: `When new data files are added to data/raw/, checks file format, encoding, and basic readability to catch issues early.`

**analyze-after-mapping** — Module 5 (fileCreated → askAgent, filePatterns: `data/transformed/*.jsonl, data/transformed/*.json`)

Prompt:

````text
A new Senzing JSON file was created in data/transformed/. Before proceeding to loading (Module 6), use the analyze_record MCP tool to validate a sample of records from this file. Check feature distribution, attribute coverage, and data quality. Quality score should be >70% before loading. Also verify that records conform to the Senzing Generic Entity Specification.

ADDITIONALLY: Verify that docs/{source_name}_mapper.md exists (extract source name from the transformed filename, e.g., "customers" from "customers.jsonl"). If it does not exist, state: 'The per-source mapping specification is missing. Create docs/{source_name}_mapper.md before proceeding to the next source or to loading.'
````

- id: `analyze-after-mapping`
- name: `to analyze mapped data`
- description: `After completing a mapping task, validates the transformation output using analyze_record for quality metrics and Senzing Generic Entity Specification conformance before proceeding to loading.`

**data-quality-check** — Module 5 (fileEdited → askAgent, filePatterns: `src/transform/*.*`)

Prompt:

````text
The transformation program was just updated. Please review the changes and suggest running data quality validation tests to ensure the output still meets quality standards (>70% attribute coverage).
````

- id: `data-quality-check`
- name: `to check data quality`
- description: `Automatically check data quality when transformation programs are saved`

**enforce-mapping-spec** — Module 5 (fileCreated → askAgent, filePatterns: `data/transformed/*.jsonl, data/transformed/*.json`)

Prompt:

````text
A transformed data file was just created in data/transformed/.

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

  Do not proceed to the next data source or any other work until this file is created.
````

- id: `enforce-mapping-spec`
- name: `to enforce the mapping specification`
- description: `When transformed data is created, verifies that a per-source mapping specification markdown exists in docs/. Blocks progression until the mapping spec is created.`

**backup-before-load** — Module 6 (fileEdited → askAgent, filePatterns: `src/load/*.*`)

Prompt:

````text
A loading program was modified. Before running this in production, remind the user to backup the database using: python3 scripts/backup_project.py (on Linux/macOS) or python scripts/backup_project.py (on Windows)
````

- id: `backup-before-load`
- name: `to remind you to back up before loading`
- description: `Remind to backup database before running loading programs`

**run-tests-after-change** — Module 6 (fileEdited → askAgent, filePatterns: `src/load/*.*, src/query/*.*, src/transform/*.*`)

Prompt:

````text
Source code was modified. If tests exist in the tests/ directory, remind the user to run them to verify the change didn't break anything. Suggest the appropriate test command for the chosen language.
````

- id: `run-tests-after-change`
- name: `to remind you to run tests`
- description: `Reminds the agent to run the test suite after source code changes in loading, query, or transformation programs.`

**verify-generated-code** — Module 6 (fileCreated → askAgent, filePatterns: `src/transform/*.*, src/load/*.*, src/query/*.*`)

Prompt:

````text
A new bootcamp source file was created. Before moving to the next step, verify this code actually runs: (1) Execute it on a small sample (10-100 records from data/samples/ or data/raw/). (2) Check for errors or exceptions. (3) If it produces output, inspect the first few records. (4) Report the results to the bootcamper — did it work, and if not, what needs fixing? Do not skip this verification step.
````

- id: `verify-generated-code`
- name: `to verify generated code`
- description: `When bootcamp source code is created, prompts the agent to run it on sample data and report results before moving on.`

**enforce-visualization-offers** — Module 8 (agentStop → askAgent)

Prompt:

````text
Read `config/bootcamp_progress.json` and check the `current_module` field. If the current module is NOT in {3, 5, 7, 8}, do nothing — let the conversation end normally.

If the current module IS in {3, 5, 7, 8}, load `visualization-protocol.md` and read the Checkpoint Map section. Identify all checkpoints defined for the current module.

Next, read `config/visualization_tracker.json`. For each checkpoint in the current module's checkpoint map, check whether a tracker entry with that `checkpoint_id` exists.

If ALL checkpoints for the current module have tracker entries (regardless of status — offered, accepted, declined, or generated), do nothing — all offers were made.

If ANY checkpoint is missing a tracker entry, offer the missed visualization(s) before the conversation ends. For each missing checkpoint, use the Visualization Protocol's offer template:

Would you like me to create a visualization of {context}?

Present only the types listed for that checkpoint in the checkpoint map, using the standard numbered list format with bold names and one-line descriptions. End with the STOP directive and wait for the bootcamper's response.

After the bootcamper responds (accept or decline), update `config/visualization_tracker.json` accordingly following the Tracker Instructions in the protocol.

Process missed checkpoints one at a time. Do not batch multiple offers into a single message.
````

- id: `enforce-visualization-offers`
- name: `to offer visualizations`
- description: `When the agent stops during a visualization-capable module (3, 5, 7, 8), checks the visualization tracker to verify all required offers were made. Prompts for missed offers.`

**validate-benchmark-results** — Module 8 (fileEdited → askAgent, filePatterns: `tests/performance/*.*`)

Prompt:

````text
A benchmark script in tests/performance/ was just modified. Before recording results, verify: (1) The script runs without errors on a small sample. (2) Output includes required metrics: records/sec for loading benchmarks, or p50/p95/p99 latency for query benchmarks. (3) Results are written to a structured format (JSON or markdown table) that can be compared across runs. If the script fails or produces unparseable output, suggest fixes before the bootcamper records baselines.
````

- id: `validate-benchmark-results`
- name: `to validate benchmark results`
- description: `When benchmark scripts are created or modified in tests/performance/, validates that they produce parseable output with required metrics (records/sec, latency percentiles).`

**security-scan-on-save** — Module 9 (fileEdited → askAgent, filePatterns: `src/security/*.*, config/*credentials*, config/*secret*, .env*`)

Prompt:

````text
A security-related file was just modified. If the bootcamper is in Module 9 (Security Hardening), remind them to re-run the appropriate vulnerability scanner for their language (Python: bandit; Java: spotbugs; C#: dotnet list package --vulnerable; Rust: cargo audit; TypeScript: npm audit) to verify no new vulnerabilities were introduced. If not in Module 9, produce no output.
````

- id: `security-scan-on-save`
- name: `to run a security scan`
- description: `When security-related files are modified during Module 9, reminds the agent to re-run vulnerability scanning to catch regressions.`

**validate-alert-config** — Module 10 (fileCreated → askAgent, filePatterns: `monitoring/alerts/*.*, monitoring/dashboards/*.*`)

Prompt:

````text
A monitoring configuration file was just created. Validate: (1) Alert rules have required fields: name, condition, severity, and action. (2) Severity levels are one of: Critical, Warning, Info. (3) Thresholds are numeric and reasonable (e.g., error rate percentages between 0-100, latency in milliseconds). (4) Dashboard configs reference metrics that are actually collected by the metrics_collector. Report any issues to the bootcamper with suggested fixes.
````

- id: `validate-alert-config`
- name: `to validate alert configuration`
- description: `When monitoring configuration files are created or modified during Module 10, validates alert rule syntax and completeness.`

**deployment-phase-gate** — Module 11 (postTaskExecution → askAgent)

Prompt:

````text
First, read `config/bootcamp_progress.json` and check the `current_module` field. If the current module is NOT 11, do nothing — let the conversation continue normally. If the current module IS 11, do the following:

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

WAIT for the bootcamper's response. Do NOT proceed to any deployment steps (Steps 12–15) until the bootcamper explicitly says they want to deploy.
````

- id: `deployment-phase-gate`
- name: `to check the deployment phase gate`
- description: `After packaging tasks complete in Module 11, displays a phase gate prompt asking the bootcamper whether to proceed to deployment or stop. Checks config/bootcamp_progress.json to confirm the current module is 11 before acting.`

**backup-project-on-request** — any module (userTriggered → askAgent)

Prompt:

````text
The user wants to back up their project. Run the backup script: python3 scripts/backup_project.py (on Linux/macOS) or python scripts/backup_project.py (on Windows). Create the backups/ directory first if it doesn't exist.
````

- id: `backup-project-on-request`
- name: `to back up your project`
- description: `Run project backup when user clicks the hook button. Avoids firing on every prompt — use the manual trigger button in the Agent Hooks panel instead.`

**error-recovery-context** — any module (postToolUse → askAgent, toolTypes: shell)

Prompt:

````text
If the shell command exited with code zero, produce no output at all — do not acknowledge, do not explain, do not print anything. STOP immediately and return nothing.

If the exit code is non-zero, check whether `config/bootcamp_progress.json` exists. If it does not exist, produce no output at all — STOP immediately and return nothing.

For non-zero exit codes with a valid bootcamp session:

1. Extract the error message, exit code, and command context from the tool execution result.

2. If the error message contains a SENZ error code prefix (e.g., SENZ0001, SENZ2034), call `explain_error_code` directly to get the official explanation and include it in your response.

3. For non-SENZ errors: Read `senzing-bootcamp/steering/common-pitfalls.md` and `senzing-bootcamp/steering/recovery-from-mistakes.md`. Read `config/bootcamp_progress.json` to determine the current module number. Scope your pitfall lookup to the current module section first. If no match is found in the module-specific section, fall back to the General Pitfalls section and the Troubleshooting by Symptom section.

4. When a known solution is found: present only the matching fix. Cite the source section (e.g., "From common-pitfalls.md § Module 3 — Docker Issues"). Include the specific command or action needed to resolve the issue. Do not dump the entire pitfalls file.

5. When multiple pitfalls could apply, present the most specific match based on the current module context. Prefer module-scoped matches over general matches.

6. When no known solution matches the error, fall back to normal troubleshooting. Do not claim a known solution exists when none was found in the pitfalls or recovery files.
````

- id: `error-recovery-context`
- name: `to help recover from errors`
- description: `Detects shell command failures and consults common-pitfalls.md and recovery-from-mistakes.md to provide targeted error recovery guidance during bootcamp modules.`

**git-commit-reminder** — any module (userTriggered → askAgent)

Prompt:

````text
The user wants to commit their bootcamp progress. Check config/bootcamp_progress.json for the current module number and list of completed modules. Then suggest a git commit with a descriptive message like: git add . && git commit -m "Complete Module [N]: [Module Name]". Show the user the command and ask if they'd like you to run it.
````

- id: `git-commit-reminder`
- name: `to remind you to commit`
- description: `Reminds the user to commit their work after completing a module. Triggered manually via button click.`

**module-completion-celebration** — any module (postTaskExecution → askAgent)

Prompt:

````text
You are checking whether the bootcamper just completed a module. Follow these steps exactly:

1. BOUNDARY DETECTION: Read `config/bootcamp_progress.json` and examine the `modules_completed` array. If `modules_completed` has not changed (no new module number was added since the previous state), produce no output at all — do nothing, do not acknowledge, do not explain, do not print any message. Let the conversation continue normally.

2. IDENTIFY COMPLETED MODULE: If a new module number appears in `modules_completed`, identify that module number. Read `config/module-dependencies.yaml` and find the module name corresponding to that number.

3. CELEBRATION MESSAGE: Display a congratulatory banner that includes the completed module number and name. Provide a one-sentence summary of what the bootcamper built or accomplished in that module.

4. NEXT MODULE: Read `config/bootcamp_preferences.yaml` to determine the bootcamper's selected track. Then consult `config/module-dependencies.yaml` for the track definition to find the next module in sequence. If more modules remain in the track, display the next module's number and name and offer to begin it immediately. If all modules in the track are complete, display a graduation acknowledgment congratulating the bootcamper on finishing the entire track.

5. FULL WORKFLOW MENTION: Let the bootcamper know they can say "completion" or "journal" to access the full completion workflow including journal entry, certificate, and reflection.

CONSTRAINTS:
- Do NOT write any files.
- Do NOT run any scripts or commands.
- Do NOT perform file-system scans or directory listings.
- ONLY read these three config files: `config/bootcamp_progress.json`, `config/module-dependencies.yaml`, and `config/bootcamp_preferences.yaml`.
- Keep the celebration concise: one banner line, one summary sentence, and the next-step information.
- Do NOT perform journal entries, generate certificates, or ask reflection questions — those belong to the full completion workflow.
````

- id: `module-completion-celebration`
- name: `to celebrate module completion`
- description: `Detects module completion boundaries and displays a brief celebration with next-step guidance.`
