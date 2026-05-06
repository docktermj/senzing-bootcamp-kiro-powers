# Requirements: "Where Am I?" Quick Status Command

## Overview

The `status.py` script exists but requires leaving the conversation to run a command. This feature adds keyword-triggered inline status so the bootcamper can ask "where am I?" or "status" and get a compact progress summary without breaking conversational flow.

## Requirements

1. The agent recognizes status-trigger phrases: "where am I", "status", "what step am I on", "show progress", "how far along am I"
2. When a status trigger is detected, the agent reads `config/bootcamp_progress.json` and `config/data_sources.yaml` (if exists) and responds with a compact inline summary
3. The inline summary includes: current module name and number, current step within the module, percentage of current track completed, data sources registered (count and names), next milestone (what completing the current step unlocks)
4. The summary is formatted as a compact block (no more than 8 lines) that doesn't interrupt the teaching flow
5. After displaying the summary, the agent asks a single 👉 question: "Ready to continue with [current step description]?" or offers to switch context
6. The status trigger phrases are added to `steering-index.yaml` keywords section, mapping to a new `inline-status.md` steering file
7. The `inline-status.md` steering file contains the response format template and instructions for computing track completion percentage
8. Track completion percentage is calculated as: (completed modules in current track / total modules in current track) × 100, with partial credit for in-progress modules based on step completion
9. If `bootcamp_progress.json` doesn't exist (brand new session), the agent responds with "You haven't started yet — would you like to begin onboarding?"
10. The inline status does not reset or modify any state — it's purely read-only
11. The `review-bootcamper-input` hook is updated to detect status trigger phrases and route to the inline status behavior (similar to how it detects feedback triggers)

## Non-Requirements

- This does not replace `status.py` (that script provides more detailed output for CLI users)
- This does not provide historical analytics (that's `analyze_sessions.py`)
- This does not show other team members' progress (that's `team_dashboard.py`)
