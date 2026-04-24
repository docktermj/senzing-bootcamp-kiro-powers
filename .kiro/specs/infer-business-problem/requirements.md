# Requirements: Infer Business Problem Details

## Introduction

Replace the sequential direct questions about record types and source count in Module 2 with a single open-ended question, inferring details from the user's free-form response.

## What Happened

Module 2 asked two direct questions in sequence: (1) record types (people/organizations/both) and (2) number of source systems. These felt like an interrogation rather than a natural conversation.

## Why It's a Problem

Both answers would naturally emerge from a free-form business problem description. Isolated direct questions feel mechanical and front-load details that aren't relevant until the user has described what they're trying to solve.

## Acceptance Criteria

1. `module-02-business-problem.md` uses a single open-ended question (e.g., "Tell me about the problem you're trying to solve — what data do you have, where does it come from, and what would success look like?")
2. Record types and source count are inferred from the user's response rather than asked directly
3. Follow-up questions are only asked for information gaps not covered in the initial response
4. The inferred details are confirmed with the user before proceeding

## Reference

- Source: `tmpe/SENZING_BOOTCAMP_POWER_FEEDBACK.md` — "Infer record types and source count from business problem description"
- Module: 2 | Priority: Medium | Category: UX
