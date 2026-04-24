# Requirements: Replace "SGES" with "Entity Specification"

## Introduction

Replace the undefined acronym "SGES" with the human-readable term "Entity Specification" in all user-facing bootcamp content shown before the term is formally defined.

## What Happened

The bootcamp introduction uses "SGES" (e.g., "If you encounter unfamiliar terms like SGES...") without defining it. New users have no context for this internal acronym during onboarding.

## Why It's a Problem

"SGES" is internal jargon (Senzing Generic Entity Specification) that creates unnecessary confusion at the exact moment clarity matters most. The glossary defines it, but users shouldn't need a lookup during the welcome message.

## Acceptance Criteria

1. All instances of "SGES" in `onboarding-flow.md`, `POWER.md`, and user-facing steering files are replaced with "Entity Specification" (or "Senzing Entity Specification" on first use)
2. The acronym "SGES" is only used in contexts where the full term has already been introduced
3. The glossary entry for SGES remains unchanged as a reference
4. No broken links or references result from the terminology change

## Reference

- Source: `tmpe/SENZING_BOOTCAMP_POWER_FEEDBACK.md` — "Replace SGES with Entity Specification in bootcamp overview"
- Module: General | Priority: Medium | Category: Documentation
