---
inclusion: manual
---

# Feedback Workflow

This steering file provides the complete feedback collection workflow for the Senzing Bootcamp.

## Trigger Phrases

When user says any of these, the feedback workflow starts automatically via the `capture-feedback` hook:

- "bootcamp feedback"
- "power feedback"
- "submit feedback"
- "provide feedback"
- "I have feedback"
- "report an issue"

## Feedback Workflow Steps

### Step 0: Automatic Context Capture

Before asking the bootcamper anything, capture their current context:

1. Read `config/bootcamp_progress.json` for the current module number and completed modules. If the file does not exist, record module as "Unknown".
2. Capture recent conversation context — summarize what the bootcamper was doing immediately before triggering feedback.
3. Identify which files are currently open in the editor.
4. Pre-fill these into the context fields below. Present the captured context to the bootcamper for confirmation: "I've captured your current context — does this look right?" Do NOT ask them to re-explain what they were doing.

### Step 1: Check for Feedback File

Check if `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` exists in the project. If not:

1. Create the `docs/feedback/` directory if it does not exist.
2. Copy from the power distribution: `senzing-bootcamp/docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md` → `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`
3. Replace the placeholder `[Date when you started using the power]` with today's date (YYYY-MM-DD).

### Step 2: Gather Feedback (One Question at a Time)

1. "What would you like to provide feedback about?" (present categories)
2. "Which module is this related to?" (0-12, or general) — pre-fill from captured context
3. "What happened or what issue did you encounter?"
4. "Why is this a problem? What was the impact?"
5. "Do you have a suggested fix or improvement?"
6. "What priority would you assign?" (High/Medium/Low)

### Step 3: Format Feedback Entry

```markdown
## Improvement: [Brief title based on user's description]

**Date**: YYYY-MM-DD
**Module**: [Module number or "General"]
**Priority**: [High/Medium/Low]
**Category**: [Documentation/Workflow/Tools/UX/Bug/Performance/Security]

### What Happened
[User's description of the issue]

### Why It's a Problem
[User's explanation of impact]

### Suggested Fix
[User's suggestion, or "None provided"]

### Workaround Used
[If user found a workaround, or "None"]

### Context When Reported
- **Current Module**: [From bootcamp_progress.json, or "Unknown"]
- **What You Were Doing**: [Summary from recent conversation]
- **Open Files**: [List of files open in editor]
```

### Step 4: Append to Feedback File

- Add the formatted entry to the "Your Feedback" section.
- Preserve any existing feedback entries.

### Step 5: Confirm and Guide

- "I've saved your feedback to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`."
- "You can review or edit it anytime."
- "Would you like to add more feedback, or continue with the bootcamp?"

**IMPORTANT:** Do NOT submit feedback to the Senzing MCP server. Feedback is saved locally only. Only submit if the user explicitly asks.

### Step 6: Remind About Submission

- "When you complete the bootcamp, please share your feedback file with the power author."
- "You can add more feedback anytime by saying 'power feedback'."

### Step 7: Return to Previous Activity

- "Would you like to continue where you left off?"
- Resume the bootcamper's previous activity using the context captured in Step 0. Do NOT require them to re-navigate or re-explain what they were doing.

## Feedback Categories

- **Documentation**: Clarity, accuracy, completeness
- **Workflow**: Step ordering, prerequisites, transitions
- **Tools**: Missing utilities, template improvements
- **UX**: Confusion points, navigation issues
- **Bugs**: Incorrect behavior, errors
- **Performance**: Slow operations, optimization opportunities
- **Security**: Security concerns, compliance issues

## Agent Reminders

- At the start of Module 1, inform users about the feedback mechanism
- When user triggers feedback, follow this workflow immediately
- At the end of Module 11, remind users to share their feedback file
