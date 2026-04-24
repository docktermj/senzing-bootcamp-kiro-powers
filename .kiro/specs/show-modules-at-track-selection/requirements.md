# Requirements: Show Modules at Track Selection

## Introduction

Display a condensed module overview table alongside the track selection prompt so users can make an informed choice without scrolling back.

## What Happened

When the bootcamp asks the user to choose a track (A–D), it lists tracks with module numbers (e.g., "Modules 2→3→4→5→6→8") but doesn't re-display the module table. Users must scroll back to remember what each module number covers.

## Why It's a Problem

Track descriptions reference module numbers but the user may not remember what Module 4 or Module 8 covers. This forces scrolling, breaking the decision flow.

## Acceptance Criteria

1. `onboarding-flow.md` Step 5 re-displays a condensed module table (module number + title) immediately before the track selection question
2. The condensed table includes all modules referenced by the four tracks
3. The track selection question and module table are visible together without scrolling
4. The condensed table does not duplicate the full detailed module descriptions from earlier in the flow

## Reference

- Source: `tmpe/SENZING_BOOTCAMP_POWER_FEEDBACK.md` — "Show module list alongside track selection"
- Module: General | Priority: Medium | Category: UX
