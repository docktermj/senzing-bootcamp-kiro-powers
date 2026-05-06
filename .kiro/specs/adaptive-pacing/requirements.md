# Requirements: Adaptive Pacing Based on Session Analytics

## Overview

The bootcamp already collects per-module session analytics (turn counts, corrections, time spent) via `session_logger.py` and `analyze_sessions.py`. This feature closes the feedback loop by having the agent read session analytics at module start and adapt its teaching pace accordingly — slower for areas where the bootcamper previously struggled, faster for areas they breezed through.

## Requirements

1. At module start, the agent reads `config/session_log.jsonl` and computes per-module metrics (turns, corrections, total time, correction density) for the bootcamper's history
2. The agent classifies each completed module into pacing categories: "struggled" (correction density > 0.3 or time > 2x median), "comfortable" (density < 0.1 and time < median), or "normal" (everything else)
3. When starting a module whose prerequisites were classified as "struggled", the agent increases explanation depth: fuller context before each step, more "why" framing, proactive offer of alternative explanations
4. When starting a module whose prerequisites were classified as "comfortable", the agent reduces preamble: shorter lead-ins, skip "why" framing unless asked, move faster through familiar patterns
5. The pacing adjustment is stored in `config/bootcamp_preferences.yaml` under a `pacing_overrides` key mapping module numbers to pacing categories
6. The bootcamper can override adaptive pacing at any time by saying "slow down" or "speed up", which updates the `pacing_overrides` for the current module
7. Adaptive pacing integrates with the existing verbosity-control system — it adjusts the baseline but does not override explicit verbosity preferences
8. If no session analytics exist (first session, or log file missing), the agent uses "normal" pacing for all modules
9. The pacing classification logic lives in a new function in `analyze_sessions.py` (stdlib only, no new dependencies)
10. Steering instructions for adaptive pacing are added to `agent-instructions.md` in the Module Steering section
11. The `session-resume.md` Step 1 (Read All State Files) is updated to include reading session analytics for pacing context

## Non-Requirements

- This does not change the module content or step structure
- This does not require real-time analytics during a module (only reads at module start)
- This does not affect hook behavior or hook timing
