# Implementation Plan: Bootcamp UX Feedback Fixes

## Overview

Five targeted text edits to existing steering files and hook definitions in the Senzing Bootcamp Kiro Power. All changes are Markdown or JSON edits — no executable code is modified or created. Each task is independent and can be applied in any order. Verification uses the existing CI pipeline scripts.

## Tasks

- [x] 1. Fix Module 1 Step 7 to ask one question per turn
  - [x] 1.1 Edit `senzing-bootcamp/steering/module-01-business-problem.md` Step 7
    - In the paragraph after "After confirmation, ask ONLY about items marked 'not yet determined':", find the line: "Ask these as a single grouped question, not one at a time. Do NOT ask about items the user already covered."
    - Replace with: "Ask about only one undetermined item per turn. After the bootcamper responds, ask about the next undetermined item in a subsequent turn. Do NOT ask about items the user already covered. Queue remaining questions for subsequent turns."
    - Verify the surrounding context (confirmation summary, list of possible follow-up questions) is unchanged
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Strengthen hook silence rule in agent-instructions.md
  - [x] 2.1 Edit the Hooks paragraph in `senzing-bootcamp/steering/agent-instructions.md`
    - Find the existing paragraph starting with "When a hook check passes with no action needed, produce no output."
    - Replace the entire paragraph with the strengthened version that includes the 🔇 emoji marker, "zero tokens, zero characters" language, prohibition on narrating evaluation, and explicit "applies to ALL hooks" scope
    - New text: `**🔇 Hook silence rule:** When a hook check passes with no action needed, produce absolutely no output — zero tokens, zero characters. Do not acknowledge the check, do not explain your reasoning, do not print any status message, do not narrate your evaluation, do not explain why no action is needed. Your response must be completely empty. Only produce output when the hook identifies a problem requiring corrective action. This applies to ALL hooks — preToolUse, agentStop, fileEdited, fileCreated, and any other hook type.`
    - _Requirements: 2.1, 2.2, 2.3_

- [x] 3. Fix Module 5 mapper path from scripts/ to docs/
  - [x] 3.1 Edit Step 1 agent instruction box in `senzing-bootcamp/steering/module-05-phase2-data-mapping.md`
    - Change `scripts/{source_name}_mapper.md` to `docs/{source_name}_mapper.md` in the per-source mapping requirement block
    - _Requirements: 3.2, 3.3_
  - [x] 3.2 Edit Step 11 per-source mapping specification in `senzing-bootcamp/steering/module-05-phase2-data-mapping.md`
    - Change `scripts/{source_name}_mapper.md` to `docs/{source_name}_mapper.md` in both the paragraph text and the "Save a mapping specification markdown to" instruction
    - _Requirements: 3.1, 3.2, 3.3_
  - [x] 3.3 Edit Step 12 per-source completion checkpoint in `senzing-bootcamp/steering/module-05-phase2-data-mapping.md`
    - Change both occurrences of `scripts/{source_name}_mapper.md` to `docs/{source_name}_mapper.md` in the verification paragraph
    - _Requirements: 3.2, 3.3, 3.4_

- [x] 4. Checkpoint — Verify mapper path fix completeness
  - Grep all steering files for any remaining `scripts/.*_mapper\.md` references — should return zero results
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Add Markdown directory enforcement rules
  - [x] 5.1 Add docs/ rule to `senzing-bootcamp/steering/project-structure.md`
    - Add a new rule in the Rules section: "All Markdown documentation files (`*.md`) belong in `docs/` or a subdirectory of `docs/`. The `scripts/` directory is reserved for executable code only — no `.md` files."
    - _Requirements: 4.1, 4.2_
  - [x] 5.2 Add Markdown docs row to the File Placement table in `senzing-bootcamp/steering/agent-instructions.md`
    - Add a new row: `Markdown docs` | `docs/`
    - _Requirements: 4.3_
  - [x] 5.3 Add redirect rule to `senzing-bootcamp/steering/agent-instructions.md`
    - Add a rule near the file placement table: "If about to write a `.md` file to `scripts/`, redirect to `docs/` instead."
    - _Requirements: 4.4_

- [x] 6. Verify hook registry consistency
  - [x] 6.1 Compare hook-registry.md prompts against .kiro.hook JSON files
    - For each of the three preToolUse hooks (enforce-working-directory, verify-senzing-facts, enforce-feedback-path), confirm the `prompt` field in the `.kiro.hook` JSON file matches the corresponding prompt text in `senzing-bootcamp/steering/hook-registry.md`
    - If any mismatch is found, update hook-registry.md to match the `.kiro.hook` file (the JSON file is the source of truth)
    - _Requirements: 5.1, 5.2_

- [x] 7. Final checkpoint — Run CI validation
  - Run `python senzing-bootcamp/scripts/sync_hook_registry.py --verify` to confirm hook registry consistency
  - Run `python senzing-bootcamp/scripts/validate_commonmark.py` to confirm all Markdown files remain CommonMark-compliant
  - Run `python senzing-bootcamp/scripts/validate_power.py` to confirm power structure integrity
  - Grep for stale `scripts/.*_mapper\.md` references and the removed "single grouped question" phrase — both should return zero results
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All changes are text edits to existing Markdown steering files and JSON hook definitions — no executable code is modified
- Each task references specific requirements from the requirements document for traceability
- The existing CI pipeline (validate_power.py, validate_commonmark.py, sync_hook_registry.py --verify) provides automated verification
- Property-based testing does not apply — there are no functions, parsers, or data transformations to test
