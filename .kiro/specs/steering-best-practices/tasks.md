# Tasks

## Task 1: Change `security-privacy.md` inclusion mode

- [x] 1.1 Change `inclusion: auto` to `inclusion: always` in the YAML frontmatter of `senzing-bootcamp/steering/security-privacy.md`
- [x] 1.2 Run `python senzing-bootcamp/scripts/validate_power.py` and confirm it passes without errors related to `security-privacy.md`

## Task 2: Trim `agent-instructions.md` to under 80 lines

- [x] 2.1 Replace the detailed `## Hooks` section in `senzing-bootcamp/steering/agent-instructions.md` with a brief reference to `hook-registry.md` (e.g., "Create hooks using the `createHook` tool with definitions from `hook-registry.md`. Critical hooks during onboarding, module hooks when the relevant module starts.")
- [x] 2.2 Tighten any other verbose sections to bring the total line count under 80
- [x] 2.3 Verify all critical rules are preserved: session start, file placement table, MCP rules, MCP failure handling, module steering loading, state & progress, communication rules, context budget management
- [x] 2.4 Run `python senzing-bootcamp/scripts/validate_power.py` and confirm it passes

## Task 3: Extract Hook Registry into `hook-registry.md`

- [x] 3.1 Create `senzing-bootcamp/steering/hook-registry.md` with `inclusion: manual` frontmatter containing all 18 hook definitions (7 critical + 11 module hooks) extracted from `onboarding-flow.md`
- [x] 3.2 Replace the inline Hook Registry section in `senzing-bootcamp/steering/onboarding-flow.md` with a `#[[file:senzing-bootcamp/steering/hook-registry.md]]` reference directive
- [x] 3.3 Verify `onboarding-flow.md` line count is reduced (target: ~190 lines)
- [x] 3.4 Run `python senzing-bootcamp/scripts/validate_power.py` and confirm it passes

## Task 4: Split `graduation.md` into main workflow and reference

- [x] 4.1 Create `senzing-bootcamp/steering/graduation-reference.md` with `inclusion: manual` frontmatter containing the extracted reference material: file copy/exclude tables, configuration file templates (`.env.production`, `.env.example`, `docker-compose.yml`, CI/CD, `.gitignore`), conditional checklist logic, and graduation report template
- [x] 4.2 Replace the extracted inline content in `senzing-bootcamp/steering/graduation.md` with `#[[file:senzing-bootcamp/steering/graduation-reference.md]]` reference directives and condensed step descriptions
- [x] 4.3 Verify `graduation.md` is under 200 lines and the workflow still covers pre-checks and Steps 1–5
- [x] 4.4 Run `python senzing-bootcamp/scripts/validate_power.py` and confirm it passes

## Task 5: Trim `module-12-deployment.md` to under 250 lines

- [x] 5.1 Condense repeated "If Azure / GCP / On-Premises / Kubernetes" blocks in Steps 3, 5, 6, 7, and 10 into single-line references to the corresponding platform steering files
- [x] 5.2 Add a `#[[file:senzing-bootcamp/templates/stakeholder_summary.md]]` reference in the stakeholder summary section of Step 15
- [x] 5.3 Verify all 15 step definitions and the phase gate are preserved
- [x] 5.4 Verify line count is under 250
- [x] 5.5 Run `python senzing-bootcamp/scripts/validate_power.py` and confirm it passes

## Task 6: Trim `module-07-multi-source.md` to under 250 lines

- [x] 6.1 Move the Common Issues section to `senzing-bootcamp/steering/module-07-reference.md` (append if not already there)
- [x] 6.2 Condense verbose step descriptions and the stakeholder summary workflow, using a `#[[file:]]` reference to the stakeholder summary template where appropriate
- [x] 6.3 Verify all 16 step definitions and the decision gate are preserved
- [x] 6.4 Verify line count is under 250
- [x] 6.5 Run `python senzing-bootcamp/scripts/validate_power.py` and confirm it passes

## Task 7: Trim `common-pitfalls.md` to under 180 lines

- [x] 7.1 Condense the Modules 9–12 section, Recovery Quick Reference, and Pre-Module Checklist into more compact formats
- [x] 7.2 Preserve the guided troubleshooting flow and all module-specific pitfall tables
- [x] 7.3 Verify line count is under 180
- [x] 7.4 Run `python senzing-bootcamp/scripts/validate_power.py` and confirm it passes

## Task 8: Trim `troubleshooting-decision-tree.md` to under 200 lines

- [x] 8.1 Condense ASCII flowcharts by removing redundant whitespace and merging closely related branches
- [x] 8.2 Preserve the visual flowchart format and all six diagnostic sections (A–F)
- [x] 8.3 Verify line count is under 200
- [x] 8.4 Run `python senzing-bootcamp/scripts/validate_power.py` and confirm it passes

## Task 9: Verify file reference count

- [x] 9.1 Count all `#[[file:]]` directives across `senzing-bootcamp/steering/*.md` and confirm the total is at least 8
- [x] 9.2 Verify each `#[[file:]]` target path points to an existing file

## Task 10: Update steering index and validate context budget

- [x] 10.1 Run `python senzing-bootcamp/scripts/measure_steering.py` to recalculate token counts for all steering files (including new `graduation-reference.md` and `hook-registry.md`)
- [x] 10.2 Verify `steering-index.yaml` has entries for all steering files including the two new ones
- [x] 10.3 Verify the always-on context budget (sum of token counts for `agent-instructions.md` + `security-privacy.md`) is under 3,000 tokens
- [x] 10.4 Run `python senzing-bootcamp/scripts/measure_steering.py --check` and confirm it passes

## Task 11: Full power validation

- [x] 11.1 Run `python senzing-bootcamp/scripts/validate_power.py` and confirm zero errors
- [x] 11.2 Run `python senzing-bootcamp/scripts/measure_steering.py --check` and confirm all token counts are within 10% of actual
- [x] 11.3 Verify `steering-index.yaml` lists every `.md` file in `senzing-bootcamp/steering/` with no missing or phantom entries
