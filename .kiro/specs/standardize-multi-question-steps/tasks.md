# Tasks: Standardize Multi-Question Steps

## Task 1: Audit steering files for multi-question steps

- [x] 1.1 Scan all module steering files (`module-*.md`) and count 👉 markers and question prompts per numbered step
- [x] 1.2 Identify steps with multiple independent questions that should be asked one at a time (e.g., module-01 step 7 conditional gap-filling, module-08 step 1 performance questions, module-09 step 1 compliance + stakeholders, module-10 step 1 tools + channels, module-11 step 1 target + method)
- [x] 1.3 Identify steps with multiple 👉 markers (e.g., module-07 step 3 has two visualization offer 👉 questions)
- [x] 1.4 Identify steps that say "ask one at a time" but structurally list multiple questions (e.g., module-01 step 7 "ask about only one undetermined item per turn", module-08 step 1 "Ask ONE AT A TIME")
- [x] 1.5 Document the audit results as comments in this task file listing each affected file, step number, question count, and classification (multi-question, conditional-independent, structural-violation)

<!-- AUDIT RESULTS — Task 1 Output

Files scanned: 20 module steering files (module-*.md including phase sub-files)
Total 👉 markers found: 5 (across 4 files)
Non-compliant steps found: 7

=== FILES WITH 👉 MARKERS (per step) ===

| File | Step | 👉 Count | Questions | Classification |
|------|------|----------|-----------|----------------|
| module-01-business-problem.md | 1 | 1 | 1 (conditional on git repo check) | COMPLIANT |
| module-02-sdk-setup.md | 3 | 1 | 1 (EULA acceptance) | COMPLIANT |
| module-03-quick-demo.md | 10 (Phase 2 step 5) | 1 | 2 (viz format + conditional interactive features follow-up) | MULTI-QUESTION |
| module-07-query-validation.md | 3 | 2 | 2 (entity graph viz offer + results dashboard viz offer) | MULTI-QUESTION |

=== NON-COMPLIANT STEPS ===

1. module-01-business-problem.md — Step 7
   - 👉 markers: 0
   - Questions: 4 (1 confirmation + 3 conditional: record types, source count, desired outcome)
   - Classification: STRUCTURAL-VIOLATION
   - Evidence: Says "Ask about only one undetermined item per turn" but lists 3 conditional questions in one step
   - Action: Split into 7a (summary + confirmation), 7b (record types), 7c (source count), 7d (desired outcome)

2. module-03-quick-demo.md — Step 10 (Phase 2 step 5)
   - 👉 markers: 1
   - Questions: 2 (viz format 👉 question + conditional follow-up about interactive features if static HTML chosen)
   - Classification: MULTI-QUESTION
   - Evidence: 1 👉 for viz format, then conditional "Would you like any interactive features?" follow-up
   - Action: Split into 5a (viz format question), 5b (interactive features follow-up)

3. module-07-query-validation.md — Step 3
   - 👉 markers: 2
   - Questions: 2 (entity graph viz offer + results dashboard viz offer)
   - Classification: MULTI-QUESTION
   - Evidence: Two ⛔ MANDATORY VISUALIZATION OFFER blocks, each with its own 👉 and 🛑 STOP
   - Action: Split into 3a (run queries + matching concepts), 3b (entity graph viz offer), 3c (results dashboard viz offer)

4. module-08-performance.md — Step 1
   - 👉 markers: 0
   - Questions: 5 (loading throughput, query latency, concurrent users, data volume/growth, database choice)
   - Classification: STRUCTURAL-VIOLATION
   - Evidence: Says "Ask ONE AT A TIME" but lists all 5 questions in one step
   - Action: Split into 1a-1e, one question per sub-step

5. module-09-security.md — Step 1
   - 👉 markers: 0
   - Questions: 2 (compliance requirements + security stakeholders)
   - Classification: CONDITIONAL-INDEPENDENT
   - Evidence: Two independent questions in one step, no "ask one at a time" instruction
   - Action: Split into 1a (compliance), 1b (stakeholders)

6. module-10-monitoring.md — Step 1
   - 👉 markers: 0
   - Questions: 2 (monitoring tools + alerting channels)
   - Classification: CONDITIONAL-INDEPENDENT
   - Evidence: Two independent questions in one step ("What monitoring tools?" + "What alerting channels?")
   - Action: Split into 1a (tools), 1b (channels)

7. module-11-deployment.md — Step 1
   - 👉 markers: 0
   - Questions: 2 (deployment target + deployment method)
   - Classification: STRUCTURAL-VIOLATION
   - Evidence: Says "ask (one at a time)" but lists both questions in one step
   - Action: Split into 1a (target), 1b (method)

=== COMPLIANT FILES (no multi-question steps) ===

- module-01-phase2-document-confirm.md — all steps have 0 or 1 question
- module-02-sdk-setup.md — step 3 has 1 👉 (EULA), all others 0 or 1
- module-04-data-collection.md — all steps have 0 or 1 question
- module-05-data-quality-mapping.md — root file, delegates to phases
- module-05-phase1-quality-assessment.md — all steps have 0 questions
- module-05-phase2-data-mapping.md — all steps have 0 or 1 question
- module-05-phase3-test-load.md — all steps have 0 or 1 question
- module-06-load-data.md — root file, delegates to phases
- module-06-phaseA-build-loading.md — all steps have 0 questions
- module-06-phaseB-load-first-source.md — all steps have 0 or 1 question
- module-06-phaseC-multi-source.md — all steps have 0 or 1 question
- module-06-phaseD-validation.md — all steps have 0 or 1 question
- module-11-phase2-deploy.md — all steps have 0 or 1 question

END AUDIT RESULTS -->

## Task 2: Restructure module-01-business-problem.md step 7

- [x] 2.1 Split step 7 (confirm inferred details and fill gaps) into sub-steps: 7a for presenting the summary and asking for confirmation, 7b/7c/7d for each independent conditional question (record types, source count, desired outcome) — each sub-step gets one question and its own checkpoint
- [x] 2.2 Preserve all conditional logic ("If record types unknown", "If source count unknown", "If desired outcome unknown") and the "ask about only one undetermined item per turn" instruction within the appropriate sub-steps
- [x] 2.3 Preserve the 🛑 STOP instruction after each question sub-step
- [x] 2.4 Update checkpoint instructions to use sub-step identifiers (e.g., "Write step 7a to `config/bootcamp_progress.json`")

## Task 3: Restructure module-07-query-validation.md step 3

- [x] 3.1 Split step 3 (run exploratory queries) into sub-steps: 3a for running queries and presenting results with matching concepts reminder, 3b for the entity graph visualization offer (first 👉 question), 3c for the results dashboard visualization offer (second 👉 question)
- [x] 3.2 Preserve the ⛔ MANDATORY VISUALIZATION OFFER blocks and all conditional response handling (static HTML, web service, no, unsure)
- [x] 3.3 Preserve the 🛑 STOP instruction after each 👉 question sub-step
- [x] 3.4 Update checkpoint instructions — move the single step 3 checkpoint to step 3c (last sub-step) and add checkpoints for 3a and 3b

## Task 4: Restructure module-03-quick-demo.md step 10

- [x] 4.1 Split Phase 2 step 5 (offer visualization) into sub-steps: 5a for the visualization format 👉 question (static HTML vs web service), 5b for the follow-up question about interactive features (if static HTML chosen)
- [x] 4.2 Preserve the 🛑 STOP instruction after the 👉 question and the conditional response handling
- [x] 4.3 Update checkpoint instructions to use sub-step identifiers (e.g., "Write step 10a/10b to `config/bootcamp_progress.json`")

## Task 5: Restructure module-08-performance.md step 1

- [x] 5.1 Split step 1 (define performance requirements) into sub-steps for each question asked "ONE AT A TIME": 1a for loading throughput target, 1b for query latency target, 1c for concurrent users, 1d for data volume/growth, 1e for database choice (SQLite vs PostgreSQL)
- [x] 5.2 Preserve the instruction to direct users to `docs/guides/PERFORMANCE_BASELINES.md` before setting targets (place in preamble before 1a)
- [x] 5.3 Preserve the `search_docs` call and documentation instruction
- [x] 5.4 Add checkpoint instructions for each sub-step and remove the parent step checkpoint

## Task 6: Restructure module-09-security.md step 1

- [x] 6.1 Split step 1 (assess security requirements) into sub-steps: 1a for asking about compliance requirements, 1b for asking about security stakeholders
- [x] 6.2 Preserve the categorization logic (Minimal/Standard/Strict) and the "Tell the user what was assessed" output template
- [x] 6.3 Add checkpoint instructions for each sub-step and remove the parent step checkpoint

## Task 7: Restructure module-10-monitoring.md step 1

- [x] 7.1 Split step 1 (assess monitoring landscape) into sub-steps: 1a for asking about monitoring tools, 1b for asking about alerting channels
- [x] 7.2 Preserve the recommendation logic ("If none: recommend Prometheus + Grafana for local, CloudWatch for AWS")
- [x] 7.3 Add checkpoint instructions for each sub-step and remove the parent step checkpoint

## Task 8: Restructure module-11-deployment.md step 1

- [x] 8.1 Split step 1 (deployment target and method) into sub-steps: 1a for asking about deployment target ("Where do you plan to deploy?"), 1b for asking about deployment method per platform
- [x] 8.2 Preserve the conditional logic for checking existing `deployment_target` and `cloud_provider` preferences (place in preamble before 1a)
- [x] 8.3 Preserve the persistence instructions for `deployment_target` and `deployment_method`
- [x] 8.4 Add checkpoint instructions for each sub-step and remove the parent step checkpoint

## Task 9: Document the sub-step convention in agent-instructions.md

- [x] 9.1 Add a "Sub-Step Convention" subsection under the "State & Progress" section in `senzing-bootcamp/steering/agent-instructions.md`
- [x] 9.2 Document the rules: sub-steps use `{step_number}{letter}` format (e.g., 7a, 7b, 7c), each sub-step contains at most one 👉 question, each sub-step has its own checkpoint instruction, steps with no questions remain as single steps without sub-step splitting, mutually exclusive conditionals may share a sub-step

## Task 10: Update steering-index.yaml token counts

- [x] 10.1 Run `python senzing-bootcamp/scripts/measure_steering.py --update` to recalculate token counts for all modified steering files
- [x] 10.2 Verify step ranges in steering-index.yaml still encompass all steps (no format changes needed — sub-steps are within parent step ranges)
- [x] 10.3 Verify steering-index.yaml is valid YAML and `total_tokens` budget is updated

## Task 11: Validate restructured files pass CI

- [x] 11.1 Run `python senzing-bootcamp/scripts/validate_power.py` and fix any errors
- [x] 11.2 Run `python senzing-bootcamp/scripts/measure_steering.py --check` and fix any mismatches
- [x] 11.3 Run `python senzing-bootcamp/scripts/validate_commonmark.py` and fix any markdown errors
- [x] 11.4 Run `python -m pytest senzing-bootcamp/tests/ -v` and fix any test failures
