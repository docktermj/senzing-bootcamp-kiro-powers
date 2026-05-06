# Design: Fix Hook Consolidation Checkbox

## Overview

This is a bookkeeping fix — task 6.4 in the hook-consolidation spec has an unchecked parent checkbox despite all 7 subtasks being complete and the deliverable file existing.

## Approach

Single-line edit to `.kiro/specs/hook-consolidation/tasks.md` changing `- [ ] 6.4` to `- [x] 6.4`.

## Verification

After the fix, `grep -c "^\- \[ \]" .kiro/specs/hook-consolidation/tasks.md` should return 0.
