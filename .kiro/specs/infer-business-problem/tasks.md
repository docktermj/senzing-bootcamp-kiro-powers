# Implementation Plan: Infer Business Problem Details

## Overview

Replace sequential direct questions in Module 2 (Steps 5–6) and Module 1's transition (Step 7) with a single open-ended prompt and inference-based discovery. Two steering files are modified — no code changes.

## Tasks

- [x] 1. Rewrite Module 1 transition (Step 7)
  - [x] 1.1 Rewrite Step 7 in `senzing-bootcamp/steering/module-01-quick-demo.md`
    - Remove the three direct transition questions (record types, source count, duplicate definition)
    - Replace with a single conversational bridge that previews Module 2's open-ended approach
    - Include the contrast framing: "Starting with Module 2, we shift to YOUR use case"
    - Include the preview of Module 2's open-ended prompt style
    - Add the fallback path for users with no specific use case ("The bootcamp works great with sample data too")
    - Do NOT ask record-type, source-count, or duplicate-definition questions in this step
    - _Requirements: 1, 2, 3_

- [x] 2. Checkpoint — Verify Module 1 transition
  - Confirm Step 7 no longer asks direct record-type, source-count, or duplicate-definition questions. Ensure the conversational bridge cleanly sets up Module 2. Ask the user if questions arise.

- [x] 3. Rewrite Module 2 discovery flow (Steps 5–6)
  - [x] 3.1 Replace Steps 5–6 in `senzing-bootcamp/steering/module-02-business-problem.md` with three new steps
    - **New Step 5 — Open-ended discovery prompt:** Single open-ended question ("Tell me about the problem you're trying to solve — what data do you have, where does it come from, and what would success look like?"); adapt prompt if a design pattern was selected in Step 4; include WAIT instruction
    - **New Step 6 — Infer details from response:** Inference logic for all five categories (record types, source count/names, problem category, matching criteria, desired outcome); include signal lists and "not yet determined" defaults for each category
    - **New Step 7 — Confirm inferred details and fill gaps:** Present concise summary of inferred details; invite corrections; ask follow-up questions ONLY for items marked "not yet determined" as a single grouped question
    - Renumber any subsequent steps accordingly
    - _Requirements: 1, 2, 3, 4_

- [x] 4. Checkpoint — Cross-reference consistency and validation
  - Trace through the Module 1 → Module 2 transition to confirm: (1) Module 1 Step 7 does NOT ask direct questions, (2) Module 2 Step 5 asks a single open-ended question, (3) Module 2 Step 6 contains inference logic for all five categories, (4) Module 2 Step 7 presents a confirmation summary and only asks about gaps
  - Run `python senzing-bootcamp/scripts/validate_commonmark.py` on both modified steering files
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- No code changes — all tasks modify Markdown steering content
- Property-based testing is not applicable; validation is via cross-reference consistency and CommonMark checks
- Each task references specific acceptance criteria from the requirements document (numbered 1–4)
