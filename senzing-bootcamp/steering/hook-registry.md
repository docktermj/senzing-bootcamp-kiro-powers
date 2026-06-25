---
inclusion: manual
---

# Hook Registry

29 bootcamp hooks organized by category. Load `hook-registry-critical.md` for full prompt text when creating hooks.

## Critical Hooks (created during onboarding)

| Hook ID | Event Type | Description |
|---------|-----------|-------------|
| ask-bootcamper | agentStop → askAgent | Consolidated agentStop hook with four phases: (1) closing question with feedback nudge, (2) step sequencing enforcement with answer processing retry (all question types) and not-waiting detection, (3) MCP-first compliance audit, (4) compound question detection with silent self-correction. |
| code-style-check | fileEdited → askAgent | Automatically checks source code files for language-appropriate coding standards when edited. For Python: PEP-8. For Java: standard conventions. For C#: .NET conventions. For Rust: rustfmt/clippy. For TypeScript: ESLint conventions. |
| commonmark-validation | userTriggered → askAgent | Validates that all Markdown files conform to CommonMark standards in a single pass. Triggered manually via the Agent Hooks panel button or as part of the graduation normalization step — no longer fires on every Markdown save. |
| review-bootcamper-input | promptSubmit → askAgent | Reviews each message submission for feedback trigger phrases and initiates the feedback workflow with automatic context capture. |
| write-policy-gate | preToolUse → askAgent | Consolidated preToolUse write hook that performs four policy checks in a single interception: (1) blocks direct SQL against the Senzing database, (2) enforces single-question rule for .question_pending writes, (3) validates file path policies including append-only guard for the feedback file, (4) enforces root file placement rules. Uses a fast path for normal writes (proceeds silently) and slow paths for violations (outputs corrective instructions). |

## Module Hooks (created when module starts)

| Hook ID | Module | Event Type | Description |
|---------|--------|-----------|-------------|
| validate-business-problem | 1 | postTaskExecution → askAgent | After Module 1 tasks complete, validates that the bootcamper has identified data sources, defined matching criteria, and documented success metrics before proceeding to Module 2. |
| verify-sdk-setup | 2 | fileEdited → askAgent | After config or environment files change during Module 2, re-verifies that the Senzing SDK setup is still valid. |
| enforce-gate-on-stop | 3 | agentStop → askAgent | After each agent turn during Module 3, verifies that Step 9 (⛔ mandatory gate) has been executed if the agent has reached or passed it. Forces immediate execution if the gate checkpoint is missing. |
| enforce-mandatory-gate | 3 | preToolUse → askAgent | Blocks step advancement past a ⛔ mandatory gate step in bootcamp_progress.json when the corresponding checkpoint is missing. Step 9 is unconditional and cannot be satisfied by a skip. This is a proactive guard that fires BEFORE the agent advances past a mandatory gate, unlike the module-completion hook which fires at the end. |
| enforce-visualization-offers | 3,5,7,8 | agentStop → askAgent | When the agent stops during a visualization-capable module (3, 5, 7, 8), checks the visualization tracker to verify all required offers were made. Prompts for missed offers. |
| gate-module3-visualization | 3 | preToolUse → askAgent | Prevents Module 3 from being marked complete unless Step 9 (Web Service + Visualization) checkpoints are present in bootcamp_progress.json. Step 9 is an unconditional ⛔ mandatory gate and cannot be skipped. |
| verify-demo-results | 3 | postTaskExecution → askAgent | After Module 3 tasks complete, verifies that system verification produced entity resolution results matching the Senzing TruthSet expected output before marking the module complete. |
| validate-data-files | 4 | fileCreated → askAgent | When new data files are added to data/raw/, checks file format, encoding, and basic readability to catch issues early. |
| analyze-after-mapping | 5 | fileCreated → askAgent | After completing a mapping task, validates the transformation output using analyze_record for quality metrics and Senzing Generic Entity Specification conformance before proceeding to loading. |
| data-quality-check | 5 | fileEdited → askAgent | Automatically check data quality when transformation programs are saved |
| enforce-mapping-spec | 5 | fileCreated → askAgent | When transformed data is created, verifies that a per-source mapping specification markdown exists in docs/. Blocks progression until the mapping spec is created. |
| backup-before-load | 6 | fileEdited → askAgent | Remind to backup database before running loading programs |
| run-tests-after-change | 6 | fileEdited → askAgent | Reminds the agent to run the test suite after source code changes in loading, query, or transformation programs. |
| verify-generated-code | 6 | fileCreated → askAgent | When bootcamp source code is created, prompts the agent to run it on sample data and report results before moving on. |
| validate-benchmark-results | 8 | fileEdited → askAgent | When benchmark scripts are created or modified in tests/performance/, validates that they produce parseable output with required metrics (records/sec, latency percentiles). |
| security-scan-on-save | 9 | fileEdited → askAgent | When security-related files are modified during Module 9, reminds the agent to re-run vulnerability scanning to catch regressions. |
| validate-alert-config | 10 | fileCreated → askAgent | When monitoring configuration files are created or modified during Module 10, validates alert rule syntax and completeness. |
| deployment-phase-gate | 11 | postTaskExecution → askAgent | After packaging tasks complete in Module 11, displays a phase gate prompt asking the bootcamper whether to proceed to deployment or stop. Checks config/bootcamp_progress.json to confirm the current module is 11 before acting. |
| backup-project-on-request | any | userTriggered → askAgent | Run project backup when user clicks the hook button. Avoids firing on every prompt — use the manual trigger button in the Agent Hooks panel instead. |
| error-recovery-context | any | postToolUse → askAgent | Detects shell command failures and consults common-pitfalls.md and recovery-from-mistakes.md to provide targeted error recovery guidance during bootcamp modules. |
| git-commit-reminder | any | userTriggered → askAgent | Reminds the user to commit their work after completing a module. Triggered manually via button click. |
| module-completion-celebration | any | agentStop → askAgent | Detects module completion boundaries and displays a brief celebration with next-step guidance. |
| module-recap-append | any | agentStop → askAgent | Appends a structured recap section to docs/bootcamp_recap.md when a module is completed. |
| session-log-events | any | postToolUse → runCommand | Logs a session event after write operations complete. The IDE appends the log line directly via a runCommand (no agent round-trip), invoking senzing-bootcamp/scripts/log_write_event.py, which records a generic write action (timestamp + current module) to config/session_log.jsonl for the completion summary. |

## Hook Creation

To create hooks, load `hook-registry-critical.md` for the full critical hook prompts and `createHook` parameters.

For module hook prompts, resolve `current_module` from `config/bootcamp_progress.json` and load the matching per-module slice `hook-registry-module-<NN>.md` (zero-padded two-digit module number, e.g. `hook-registry-module-03.md`) or `hook-registry-module-any.md` for hooks that apply to any module. Each slice holds the full prompt text and `createHook` parameters for that module's hooks.

If the expected per-module slice is missing at its path, fall back to this summary and report that the per-module slice is unavailable. The tables above list every hook by ID, event flow, module label, and description.
