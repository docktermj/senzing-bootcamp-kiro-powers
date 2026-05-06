---
inclusion: manual
---

# What's New Notification

Show a brief "What's New" notification during session resume when relevant changes have been made since the bootcamper's last session.

## When to Show

Show the notification when ALL of these conditions are met:

1. `config/session_log.jsonl` exists with at least one entry
2. `CHANGELOG.md` has version entries newer than the last session date
3. `config/bootcamp_preferences.yaml` does NOT have `show_whats_new: false`

If any condition is not met, skip silently — do not show "nothing new" or any acknowledgment.

## How to Generate

1. Read the last session date from the final line of `config/session_log.jsonl` (the `timestamp` field, truncated to YYYY-MM-DD)
2. Parse `CHANGELOG.md` for version entries with dates (format: `## [vX.Y.Z] - YYYY-MM-DD`)
3. Filter to entries newer than the last session date
4. Score each change bullet by relevance (see scoring below)
5. Select the top 3 changes by score (ties broken by recency)
6. Format using the notification template

## Relevance Scoring

| Priority | Criterion | Score |
|----------|-----------|-------|
| 1 | Mentions the bootcamper's current module number | +3 |
| 2 | Mentions the bootcamper's chosen language | +2 |
| 3 | Is a bug fix (under "### Fixed" section) | +1 |
| 4 | Is a new feature (under "### Added" section) | +1 |
| 5 | Everything else | 0 |

## Notification Template

```text
📢 **What's New** (since your last session on [date]):
- [Most relevant change — one line]
- [Second most relevant change — one line]
- [Third most relevant change — one line]

These improvements were informed by bootcamper feedback — yours included if you've submitted any.
```

## Format Rules

- Maximum 3 bullet points (never more)
- One-line summary per change (no details or sub-bullets)
- Always include the attribution note at the end
- Show only once per session (do not repeat if bootcamper asks again — direct them to CHANGELOG.md)

## Suppression

If the bootcamper says "don't show updates", "stop showing what's new", or similar:
- Set `show_whats_new: false` in `config/bootcamp_preferences.yaml`
- Acknowledge: "Got it — I won't show update notifications. Say 'show updates' if you change your mind."

If the bootcamper says "show updates" or "show what's new again":
- Remove the `show_whats_new: false` entry (or set to `true`)
- Acknowledge: "Update notifications re-enabled."
