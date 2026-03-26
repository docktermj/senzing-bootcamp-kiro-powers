# Power Feedback Workflow

**Purpose**: Guide users through providing structured feedback about the Senzing Boot Camp power.
**Trigger**: User says "power feedback", "bootcamp feedback", "submit feedback", "provide feedback", "I have feedback", or "report an issue"
**Last Updated**: 2026-03-24

**CRITICAL**: Feedback must be submitted to TWO locations:

1. **Local file**: `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` (user's copy)
2. **Senzing MCP server**: For centralized tracking and power improvement

---

## Quick Reference

When user requests feedback:

1. ✅ Check/create feedback file from template
2. ✅ Ask what type of feedback (one question at a time)
3. ✅ Gather details (module, issue, impact, suggestion, priority)
4. ✅ Format and append to feedback file
5. ✅ Submit to Senzing MCP server (if available)
6. ✅ Confirm and offer to add more
7. ✅ Remind about dual submission at end

**IMPORTANT**: Feedback must go to TWO places:

1. User's `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` (local copy)
2. Senzing MCP server (for power improvement tracking)

---

## Trigger Phrases

The agent should activate the feedback workflow when user says:

- "power feedback"
- "bootcamp feedback"
- "submit feedback"
- "provide feedback"
- "I have feedback"
- "report an issue"
- "I found a problem"
- "suggestion for improvement"

---

## Workflow Steps

### Step 1: Check/Create Feedback File

```bash
# Check if feedback file exists
if [ ! -f "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md" ]; then
    # Create from template
    cp docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md \
       docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md

    # Update header with current date
    sed -i "s/\[Date when you started using the power\]/$(date +%Y-%m-%d)/" \
       docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md

    echo "Created feedback file from template"
fi
```

### Step 2: Gather Feedback (One Question at a Time)

**Question 1**: "What would you like to provide feedback about?"

- Present categories: Documentation, Workflow, Tools, UX, Bug, Performance, Security

**Question 2**: "Which module is this related to?"

- Options: 0-12, or "General" if not module-specific

**Question 3**: "What happened or what issue did you encounter?"

- Let user describe in their own words

**Question 4**: "Why is this a problem? What was the impact?"

- Understanding the impact helps prioritize

**Question 5**: "Do you have a suggested fix or improvement?"

- Optional - user may not have a solution

**Question 6**: "What priority would you assign to this?"

- Options: High, Medium, Low

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
- Maintain proper markdown formatting
- Save to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`

### Step 5: Submit to Senzing MCP Server

**IMPORTANT**: After saving to local file, submit to MCP server for tracking.

Check if Senzing MCP server has a feedback submission tool:

```bash
# Check available MCP tools
# Look for: submit_feedback, report_issue, or similar
```

If available, submit the feedback:

```json
{
  "tool": "submit_feedback",
  "parameters": {
    "source": "senzing-bootcamp",
    "module": "[module number or 'General']",
    "category": "[category]",
    "priority": "[High/Medium/Low]",
    "title": "[brief title]",
    "description": "[what happened]",
    "impact": "[why it's a problem]",
    "suggestion": "[suggested fix]",
    "date": "[YYYY-MM-DD]"
  }
}
```

**If MCP tool not available**: Note in the feedback file that it should be submitted manually.

### Step 6: Confirm and Offer Next Steps

Agent says:

```text
✅ I've added your feedback to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`
✅ Submitted to Senzing MCP server for tracking

You can review or edit it anytime. Would you like to:
- Add more feedback
- Continue with the boot camp
- Review the feedback file
```

If MCP submission failed or unavailable:

```text
✅ I've added your feedback to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`
⚠️  Could not submit to Senzing MCP server (will be submitted when you share the file)

You can review or edit it anytime. Would you like to:
- Add more feedback
- Continue with the boot camp
- Review the feedback file
```

### Step 7: Remind About Dual Submission

Agent says:

```text
Your feedback has been saved in two places:
1. ✅ Local file: `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`
2. ✅ Senzing MCP server: Submitted for tracking

When you complete the boot camp, please also share your local feedback
file with the power author for additional context.

You can add more feedback anytime by saying "power feedback".
```

---

## Example Interaction

**User**: "power feedback"

**Agent**: "I'll help you document your feedback. What would you like to provide feedback about?

- Documentation (clarity, accuracy, completeness)
- Workflow (step ordering, prerequisites, transitions)
- Tools (missing utilities, template improvements)
- UX (confusion points, navigation issues)
- Bug (incorrect behavior, errors)
- Performance (slow operations, optimization)
- Security (security concerns, compliance)"

**User**: "Documentation"

**Agent**: "Which module is this related to? (0-12, or 'General' if not module-specific)"

**User**: "Module 4"

**Agent**: "What happened or what issue did you encounter?"

**User**: "The mapping workflow instructions were unclear about how to handle nested JSON"

**Agent**: "Why is this a problem? What was the impact?"

**User**: "I spent 30 minutes trying different approaches before figuring it out"

**Agent**: "Do you have a suggested fix or improvement?"

**User**: "Add an example showing nested JSON mapping"

**Agent**: "What priority would you assign to this? (High/Medium/Low)"

**User**: "Medium"

**Agent**: "✅ I've added your feedback to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`
✅ Submitted to Senzing MCP server for tracking

You can review or edit it anytime. Would you like to:

- Add more feedback
- Continue with the boot camp
- Review the feedback file"

---

## Feedback Categories

### Documentation

- Unclear instructions
- Missing information
- Incorrect information
- Outdated content
- Poor examples

### Workflow

- Step ordering issues
- Missing prerequisites
- Unclear transitions
- Redundant steps
- Confusing flow

### Tools

- Missing utilities
- Template improvements
- Tool usability issues
- Integration problems

### UX

- Confusion points
- Navigation problems
- Repeated questions
- Onboarding issues
- Unclear error messages

### Bug

- Incorrect behavior
- Errors
- Edge cases
- Data issues
- Compatibility problems

### Performance

- Slow operations
- Resource usage
- Optimization opportunities
- Scalability issues

### Security

- Security concerns
- PII handling
- Access control
- Compliance issues
- Vulnerability risks

---

## Priority Guidelines

### High Priority

- Blocks user progress
- Causes data loss or corruption
- Security vulnerabilities
- Affects majority of users
- Quick fix with high impact

### Medium Priority

- Causes confusion but has workaround
- Affects some users
- Moderate effort to fix
- Improves efficiency

### Low Priority

- Minor inconvenience
- Affects few users
- Nice-to-have feature
- High effort, low impact

---

## Agent Best Practices

1. **Be supportive**: Thank user for providing feedback
2. **Ask one at a time**: Don't overwhelm with multiple questions
3. **Be patient**: Let user explain in their own words
4. **Clarify if needed**: Ask follow-up questions for clarity
5. **Confirm understanding**: Summarize before adding to file
6. **Submit to both locations**: Local file AND MCP server
7. **Handle MCP failures gracefully**: If MCP submission fails, note it and continue
8. **Make it easy**: Offer to add more feedback
9. **Remind about value**: Explain how feedback helps improve the power

---

## MCP Server Integration

### Checking for MCP Feedback Tool

Before submitting feedback, check if the Senzing MCP server has a feedback submission tool:

```bash
# List available MCP tools
# Look for: submit_feedback, report_issue, send_feedback, or similar
```

### Submitting to MCP Server

If a feedback tool is available, submit with these parameters:

**Required fields**:

- `source`: "senzing-bootcamp"
- `module`: Module number (0-12) or "General"
- `category`: Documentation/Workflow/Tools/UX/Bug/Performance/Security
- `priority`: High/Medium/Low
- `title`: Brief description
- `description`: What happened
- `date`: YYYY-MM-DD

**Optional fields**:

- `impact`: Why it's a problem
- `suggestion`: Suggested fix
- `workaround`: Workaround used
- `user_context`: Additional context

### Handling MCP Submission Failures

If MCP submission fails:

1. ✅ Still save to local file
2. ⚠️  Note the failure in agent response
3. 📝 Add a note in the feedback file that it needs manual submission
4. 🔄 Offer to retry later

**Example failure message**:

```text
✅ I've added your feedback to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`
⚠️  Could not submit to Senzing MCP server (connection issue)

Your feedback is saved locally and will be submitted when you share the file.
```

### MCP Server Not Available

If the MCP server doesn't have a feedback tool:

1. ✅ Save to local file as normal
2. 📝 Note in the feedback file header that it should be shared with power author
3. 💡 Remind user at Module 12 completion to share the file

---

## Integration Points

### Module 1 Start

Agent says: "If you encounter any issues or have suggestions during the boot camp, just say 'power feedback' or 'bootcamp feedback' and I'll help you document them."

### During Any Module

User can say "power feedback" or "bootcamp feedback" at any time to document issues as they occur.

### Module 12 Completion

Agent says: "🎉 Congratulations on completing the Senzing Boot Camp!

Your feedback has been:
✅ Saved locally: `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`
✅ Submitted to Senzing MCP server throughout the boot camp

If you have any additional feedback, say 'power feedback' or 'bootcamp feedback' and I'll help you document it. You can also share your local feedback file with the power author for additional context."

---

## Troubleshooting

### Feedback File Not Created

- Check if `docs/feedback/` directory exists
- Create directory if needed: `mkdir -p docs/feedback`
- Copy template manually if automated copy fails

### User Doesn't Know What to Say

- Prompt with specific questions
- Give examples of common feedback
- Suggest reviewing recent modules for issues

### Multiple Feedback Entries

- Each entry should be separate
- Use clear numbering or titles
- Maintain chronological order

---

**Document Owner**: Senzing Boot Camp Team
**Maintained By**: Agent during power usage
**Review Frequency**: After each feedback submission
