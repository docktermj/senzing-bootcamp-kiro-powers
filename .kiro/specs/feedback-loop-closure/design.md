# Design: Feedback Loop Closure

## Overview

At session resume, the agent checks whether CHANGELOG entries are newer than the bootcamper's last session. If so, it presents a brief "What's New" notification showing relevant changes, demonstrating that feedback leads to improvements.

## Notification Format

```
📢 **What's New** (since your last session on May 1):
- Module 6 loading now includes automatic redo processing verification
- Fixed: session resume no longer asks duplicate questions
- New: "where am I?" command shows inline progress summary

These improvements were informed by bootcamper feedback — yours included if you've submitted any.
```

### Format Rules
- Maximum 3 bullet points (most relevant changes only)
- One-line summary per change (no details)
- Always includes the attribution note
- Shown only once per session (not repeated if bootcamper asks again)

## CHANGELOG Parsing

The CHANGELOG follows Keep a Changelog format:

```markdown
## [v0.10.0] - 2026-04-22

### Added
- Data source registry with quality scoring
- Team bootcamp mode

### Fixed
- Session resume duplicate question bug
```

### Parsing Logic

```python
def parse_changelog(content: str) -> list[dict]:
    """Parse CHANGELOG into version entries with dates."""
    entries = []
    for match in re.finditer(r'## \[v([\d.]+)\] - (\d{4}-\d{2}-\d{2})', content):
        version = match.group(1)
        date = match.group(2)
        # Extract section content until next ## header
        section_content = extract_until_next_header(content, match.end())
        entries.append({
            "version": version,
            "date": date,
            "changes": extract_bullet_points(section_content)
        })
    return entries

def get_changes_since(entries, last_session_date):
    """Filter to entries newer than last session."""
    return [e for e in entries if e["date"] > last_session_date]
```

## Relevance Scoring

Changes are scored for relevance to the current bootcamper:

| Priority | Criterion | Score |
|----------|-----------|-------|
| 1 | Mentions current module number | +3 |
| 2 | Mentions bootcamper's language | +2 |
| 3 | Is a bug fix (under "### Fixed") | +1 |
| 4 | Is a new feature (under "### Added") | +1 |
| 5 | Everything else | 0 |

Top 3 changes by score are shown. Ties broken by recency.

## Last Session Timestamp

Read from the last line of `config/session_log.jsonl`:

```python
def get_last_session_date(log_path="config/session_log.jsonl"):
    """Get the date of the most recent session log entry."""
    try:
        with open(log_path) as f:
            lines = f.readlines()
        if not lines:
            return None
        last_entry = json.loads(lines[-1])
        return last_entry["timestamp"][:10]  # YYYY-MM-DD
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None
```

## Suppression

If the bootcamper says "don't show updates" (or similar):
- Set `show_whats_new: false` in `config/bootcamp_preferences.yaml`
- Agent checks this preference before showing the notification
- Can be re-enabled by saying "show updates again"

## Steering File: whats-new.md

```markdown
---
inclusion: manual
---

# What's New Notification

## When to Show

Show the "What's New" notification during session resume when ALL conditions are met:
1. `config/session_log.jsonl` exists with at least one entry
2. `CHANGELOG.md` has entries newer than the last session date
3. `config/bootcamp_preferences.yaml` does NOT have `show_whats_new: false`

## How to Generate

1. Read last session date from session log
2. Parse CHANGELOG.md for version entries with dates
3. Filter to entries newer than last session
4. Score changes by relevance (current module > language > bug fix > feature)
5. Select top 3 changes
6. Format using the notification template

## Suppression

If bootcamper says "don't show updates" or "stop showing what's new":
- Set `show_whats_new: false` in preferences
- Acknowledge: "Got it — I won't show update notifications. Say 'show updates' if you change your mind."
```

## Integration with session-resume.md

Insert after the welcome-back message and before the "Ready to continue?" question:

```
Step 2e: What's New Notification
- Check conditions (session log exists, new CHANGELOG entries, not suppressed)
- If conditions met: show notification (max 3 bullets + attribution)
- If conditions not met: skip silently
- Continue to Step 3 (Ready to continue?)
```

## Files Created/Modified

- `senzing-bootcamp/steering/whats-new.md` — new steering file (manual inclusion)
- `senzing-bootcamp/steering/session-resume.md` — add Step 2e
- `senzing-bootcamp/steering/steering-index.yaml` — add keywords and file_metadata

## Testing

- Unit test: whats-new.md exists with correct frontmatter
- Unit test: session-resume.md contains "What's New" step
- Unit test: steering-index.yaml has keyword entries for "what's new", "changelog", "updates"
- Property test: relevance scoring always produces 0-3 results
- Property test: changes newer than last session are always a subset of all changes
- Unit test: suppression preference is respected
