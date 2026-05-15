# Requirements: Bootcamp Completion Analytics

## Overview

Provide a local-only analytics summary that reads session logs to identify where bootcampers get stuck, which modules take longest, and which steps have the highest skip rate — helping identify curriculum weak spots without sending data externally.

## Requirements

1. Create `scripts/bootcamp_analytics.py` that reads `config/session_log.jsonl` and produces a summary report
2. Report must include: time spent per module, average turns per module, steps skipped (from skip-step-protocol tracking), error frequency by module, feedback sentiment summary
3. Report must include a "Friction Points" section identifying: modules with above-average time, steps with multiple retries, steps that were skipped, MCP tool failures by module
4. Output format: human-readable text to stdout (default) or `--json` for machine-readable output
5. The script must handle missing or empty session logs gracefully (exit 0 with "No session data available")
6. No data leaves the local machine — this is purely local analysis
7. Add a `--compare` flag that compares the bootcamper's pace against the performance baselines in `PERFORMANCE_BASELINES.md` (time estimates per module)
8. Add the script to POWER.md "Useful Commands" section
9. The agent should offer to run analytics at track completion (add to `module-completion.md` Path Completion Celebration)
10. Write tests covering: empty log, single module log, multi-module log, skip detection, JSON output format
11. Use only Python stdlib (no third-party dependencies)
