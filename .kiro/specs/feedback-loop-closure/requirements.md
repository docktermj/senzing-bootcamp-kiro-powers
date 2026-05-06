# Requirements: Feedback Loop Closure

## Overview

The feedback system collects input but there's no mechanism to show bootcampers that their feedback led to changes. This feature adds a "What's New Since Your Last Session" notification that compares the bootcamper's last session timestamp against CHANGELOG entries, demonstrating responsiveness and encouraging continued feedback.

## Requirements

1. At session resume, after the welcome-back message and before the "Ready to continue?" question, the agent checks whether there are CHANGELOG entries newer than the bootcamper's last session
2. The last session timestamp is read from the most recent entry in `config/session_log.jsonl` (the `timestamp` field of the last line)
3. If new CHANGELOG entries exist since the last session, the agent presents a brief "What's New" summary: 1-3 bullet points covering the most relevant changes (prioritizing changes that affect the bootcamper's current module or track)
4. The summary is kept to 3 lines maximum — it's a notification, not a changelog review
5. If no new changes exist, nothing is shown (no "nothing new" message)
6. The CHANGELOG is parsed by looking for version headers (`## [vX.Y.Z]`) and their dates, comparing against the last session timestamp
7. Changes are prioritized by relevance: (a) changes mentioning the bootcamper's current module, (b) changes mentioning their language, (c) bug fixes, (d) new features
8. The "What's New" notification includes a note: "These improvements were informed by bootcamper feedback — yours included if you've submitted any."
9. A new steering file `whats-new.md` contains the format template and relevance-scoring instructions for the agent
10. The `steering-index.yaml` keywords section maps "what's new", "changelog", "updates" to the `whats-new.md` file
11. The bootcamper can say "don't show updates" to suppress the notification for future sessions (stored in `config/bootcamp_preferences.yaml` as `show_whats_new: false`)
12. If the bootcamper has never had a session (no session log), the notification is skipped entirely

## Non-Requirements

- This does not parse git history — only the CHANGELOG.md file
- This does not attribute specific changes to specific feedback submissions
- This does not modify the CHANGELOG format
- This does not show changes from before the bootcamper's first session
