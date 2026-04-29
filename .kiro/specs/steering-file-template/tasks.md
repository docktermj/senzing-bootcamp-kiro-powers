# Tasks

## Task 1: Create the canonical template file

- [x] 1.1 Create `senzing-bootcamp/templates/module-steering-template.md` with placeholder sections in the required Section_Order: Frontmatter_Block (`inclusion: manual`), First_Read_Instruction (`**🚀 First:**` referencing `config/bootcamp_progress.json` and `module-transitions.md`), user reference line, Before_After_Block (`**Before/After:**` with table), Prerequisites_Block, Workflow_Steps (at least two example numbered steps each with a Checkpoint_Instruction), and Success_Indicator (`**Success indicator:** ✅ ...`)
  _Requirements: 1.1, 1.2_
- [x] 1.2 Add HTML comments (`<!-- ... -->`) to each section explaining its purpose and expected content, and use placeholder values (`NN`, `[Module Title]`, `[description]`) to indicate customizable parts
  _Requirements: 1.3, 1.4_

## Task 2: Implement frontmatter validation rule

- [x] 2.1 Add `get_module_steering_files(steering_dir)` utility function to `scripts/lint_steering.py` that returns all `module-NN-*.md` file paths in the steering directory
- [x] 2.2 Implement `check_module_frontmatter(steering_dir)` that verifies every module steering file begins with a `---` delimited YAML frontmatter block containing `inclusion: manual`, reporting errors for missing frontmatter and warnings for non-manual inclusion values
  _Requirements: 2.1, 2.2, 2.3, 2.4_

## Task 3: Implement first-read instruction validation rule

- [x] 3.1 Implement `check_first_read_instruction(steering_dir)` that verifies every module steering file contains a line matching `**🚀 First:**` within the first 10 non-blank lines after frontmatter, reporting errors for missing instructions and warnings when the instruction doesn't reference both `config/bootcamp_progress.json` and `module-transitions.md`
  _Requirements: 3.1, 3.2, 3.3, 3.4_

## Task 4: Implement before/after block validation rule

- [x] 4.1 Implement `check_before_after_block(steering_dir)` that verifies every module steering file contains a Before_After_Block (line containing `**Before/After**`, case-insensitive), reports warnings for missing blocks, and verifies the block appears before the first workflow step
  _Requirements: 4.1, 4.2, 4.3_

## Task 5: Implement checkpoint completeness validation rule

- [x] 5.1 Implement `check_checkpoint_completeness(steering_dir)` that parses each module steering file to identify top-level numbered workflow steps (`1. `, `2. `, etc.), reports errors for steps without a corresponding `**Checkpoint:** Write step N` instruction before the next step or end of file, reports errors for mismatched step numbers in checkpoints, and skips files with zero workflow steps
  _Requirements: 5.1, 5.2, 5.3, 5.4_

## Task 6: Implement success indicator validation rule

- [x] 6.1 Implement `check_success_indicator(steering_dir)` that verifies every module steering file contains a `**Success indicator:**` line (case-insensitive), reports warnings for missing indicators, verifies the indicator appears after all workflow steps, and reports errors when the indicator appears before a workflow step
  _Requirements: 6.1, 6.2, 6.3, 6.4_

## Task 7: Implement section order validation rule

- [x] 7.1 Implement `check_section_order(steering_dir)` that detects the line numbers of all present template sections (frontmatter, first-read, before/after, workflow steps, success indicator) in each module steering file, verifies they appear in the required order, reports warnings for out-of-order pairs, and only validates ordering for sections that are present (missing sections do not trigger ordering violations)
  _Requirements: 7.1, 7.2, 7.3_

## Task 8: Integrate template rules into linter CLI

- [x] 8.1 Add `--skip-template` flag to the `argparse` configuration in `main()` and update `run_all_checks` to accept a `skip_template` parameter that skips all template conformance rule functions when True
  _Requirements: 8.3_
- [x] 8.2 Wire the six template conformance rule functions (`check_module_frontmatter`, `check_first_read_instruction`, `check_before_after_block`, `check_checkpoint_completeness`, `check_success_indicator`, `check_section_order`) into `run_all_checks` so they execute as part of the standard linter run, reporting violations in the same `{level}: {file}:{line}: {message}` format
  _Requirements: 8.1, 8.2_
- [x] 8.3 Verify that all template conformance code uses only Python standard library imports
  _Requirements: 8.4_

## Task 9: Verify template rules on real module files

- [x] 9.1 Run `python senzing-bootcamp/scripts/lint_steering.py` on the real steering corpus and verify template conformance rules produce expected results for all 11 module steering files (module-01 through module-11)
- [x] 9.2 Run with `--skip-template` flag and verify no template conformance violations appear in output
- [x] 9.3 Fix any false positives or adjust regex patterns based on real module file variations

## Task 10: Property-based tests (Hypothesis)

- [x] 10.1 Create `senzing-bootcamp/tests/test_steering_template_properties.py` with Hypothesis strategies for generating random module steering file content (with optional frontmatter, first-read instructions, before/after blocks, numbered steps with optional checkpoints, and success indicators at various positions)
- [x] 10.2 PBT: Property 1 — Frontmatter Detection and Validation: for any file content, the checker reports an error if no `---` delimited YAML block exists, and a warning if inclusion is not `manual` (Req 2.1, 2.2, 2.3, 2.4)
- [x] 10.3 PBT: Property 2 — First-Read Instruction Detection: for any module content, the checker reports an error if `**🚀 First:**` is missing from the first 10 non-blank lines after frontmatter, and a warning if required references are missing (Req 3.1, 3.2, 3.3, 3.4)
- [x] 10.4 PBT: Property 3 — Step-Checkpoint Matching: for any module content with numbered steps, the checker reports errors for steps missing checkpoints and for mismatched step numbers; files with zero steps produce no violations (Req 5.1, 5.2, 5.3, 5.4)
- [x] 10.5 PBT: Property 4 — Section Ordering Validation: for any module content with two or more detected sections, the checker reports warnings for out-of-order pairs; missing sections do not trigger ordering violations (Req 7.1, 7.2, 7.3)
- [x] 10.6 PBT: Property 5 — Success Indicator Position: for any module content with steps and a success indicator, the checker reports an error if the indicator appears before any step (Req 6.3, 6.4)
- [x] 10.7 PBT: Property 6 — Before/After Block Position: for any module content with a before/after block and steps, the checker reports a warning if the block appears after the first step (Req 4.1, 4.3)
- [x] 10.8 PBT: Property 7 — Template Conformance Violation Format: for any template violation, formatted output matches `{ERROR|WARNING}: {file}:{line}: {message}` (Req 8.2)

## Task 11: Example-based unit tests

- [x] 11.1 Unit test: template file exists at `senzing-bootcamp/templates/module-steering-template.md` (Req 1.1)
- [x] 11.2 Unit test: template contains all required sections in the correct order (Req 1.2)
- [x] 11.3 Unit test: template contains HTML comments for each section (Req 1.3)
- [x] 11.4 Unit test: template contains placeholder values `NN`, `[Module Title]` (Req 1.4)
- [x] 11.5 Unit test: real module files have valid frontmatter with `inclusion: manual` (Req 2.1, 2.2)
- [x] 11.6 Unit test: real module files have first-read instruction referencing required files (Req 3.1, 3.2)
- [x] 11.7 Unit test: real module files have checkpoints for all numbered steps (Req 5.1, 5.2)
- [x] 11.8 Unit test: `--skip-template` flag suppresses all template conformance violations (Req 8.3)
- [x] 11.9 Unit test: template violations use standard `{level}: {file}:{line}: {message}` format (Req 8.2)

## Task 12: Integration tests

- [x] 12.1 Integration test: full linter run includes template conformance results in output
- [x] 12.2 Integration test: `--skip-template` suppresses all template-related output lines
- [x] 12.3 Integration test: linter with template checks uses only Python standard library (Req 8.4)
