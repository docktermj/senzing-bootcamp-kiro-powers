---
inclusion: manual
---

# Feedback Workflow

This steering file provides the complete feedback collection workflow for the Senzing Boot Camp.

## Trigger Phrases

When user says any of these, immediately start the feedback workflow:

- "power feedback"
- "bootcamp feedback"
- "submit feedback"
- "provide feedback"
- "I have feedback"
- "report an issue"

## Feedback Workflow Steps

### Step 1: Check for Feedback File

```bash
if [ ! -f "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md" ]; then
    cp docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md \
       docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md
    sed -i "s/\[Date when you started using the power\]/$(date +%Y-%m-%d)/" \
       docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md
fi
```

### Step 2: Gather Feedback (One Question at a Time)

1. "What would you like to provide feedback about?" (present categories)
2. "Which module is this related to?" (0-12, or general)
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
```

### Step 4: Append to Feedback File

- Add the formatted entry to the "Your Feedback" section
- Preserve any existing feedback entries

### Step 5: Confirm and Guide

- "I've saved your feedback to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`."
- "You can review or edit it anytime."
- "Would you like to add more feedback, or continue with the boot camp?"

**IMPORTANT**: Do NOT submit feedback to the Senzing MCP server. Feedback is saved locally only. Only submit to the MCP server if the user explicitly asks to do so.

### Step 6: Remind About Submission

- "When you complete the boot camp, please share your feedback file with the power author."
- "You can add more feedback anytime by saying 'power feedback'."

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
- At the end of Module 12, remind users to share their feedback file
