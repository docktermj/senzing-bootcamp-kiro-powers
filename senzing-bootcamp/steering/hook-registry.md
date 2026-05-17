---
inclusion: manual
---

# Hook Registry

27 bootcamp hooks organized by category. Load `hook-registry-detail.md` for full prompt text when creating hooks.

## Critical Hooks (created during onboarding)

| Hook ID | Event Type | Description |
|---------|-----------|-------------|
| ask-bootcamper | agentStop → askAgent | Silence-first agentStop hook with dual responsibility: (1) Phase 1 produces a recap + closing question only when no question is already pending, with a near-completion feedback nudge; (2) Phase 2 independently reminds the bootcamper to share saved feedback after track completion. |
| code-style-check | fileEdited → askAgent | Automatically checks source code files for language-appropriate coding standards when edited. For Python: PEP-8. For Java: standard conventions. For C#: .NET conventions. For Rust: rustfmt/clippy. For TypeScript: ESLint conventions. |
| commonmark-validation | fileEdited → askAgent | Validates that all Markdown files conform to CommonMark standards when edited |
| enforce-file-path-policies | preToolUse → askAgent | Before any write operation, enforces two path policies: (1) feedback content must go to docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md, and (2) no files may be written outside the working directory. Uses a fast path for project-relative non-feedback writes (proceeds silently) and a slow path for violations (outputs corrective instructions). |
| enforce-single-question | preToolUse → askAgent | Validates that any 👉 question being written to .question_pending contains exactly one question with no compound constructions, conjunctions, or appended alternatives. Fires on write operations targeting the question_pending file. |
| review-bootcamper-input | promptSubmit → askAgent | Reviews each message submission for feedback trigger phrases and initiates the feedback workflow with automatic context capture. |

## Module Hooks (created when module starts)

| Hook ID | Module | Event Type | Description |
|---------|--------|-----------|-------------|
| validate-business-problem | 1 | postTaskExecution → askAgent | After Module 1 tasks complete, validates that the bootcamper has identified data sources, defined matching criteria, and documented success metrics before proceeding to Module 2. |
| verify-sdk-setup | 2 | fileEdited → askAgent | After config or environment files change during Module 2, re-verifies that the Senzing SDK setup is still valid. |
| enforce-mandatory-gate | 3 | preToolUse → askAgent | Blocks step advancement past a ⛔ mandatory gate step in bootcamp_progress.json when the corresponding checkpoint is missing and no skipped_steps entry exists. This is a proactive guard that fires BEFORE the agent advances past a mandatory gate, unlike the module-completion hook which fires at the end. |
| enforce-visualization-offers | 3,5,7,8 | agentStop → askAgent | When the agent stops during a visualization-capable module (3, 5, 7, 8), checks the visualization tracker to verify all required offers were made. Prompts for missed offers. |
| gate-module3-visualization | 3 | preToolUse → askAgent | Prevents Module 3 from being marked complete unless Step 9 (Web Service + Visualization) checkpoints are present in bootcamp_progress.json, or the step was explicitly skipped via the skip-step protocol. |
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
| module-completion-celebration | any | postTaskExecution → askAgent | Detects module completion boundaries and displays a brief celebration with next-step guidance. |

## Hook Creation

To create hooks, load `hook-registry-detail.md` for the full prompt text and `createHook` parameters.
