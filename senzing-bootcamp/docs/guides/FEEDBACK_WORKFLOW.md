# Power Feedback Workflow

**Purpose**: Guide users through providing structured feedback about the Senzing Boot Camp power.  
**Trigger**: User says "power feedback", "submit feedback", "provide feedback", "I have feedback", or "report an issue"  
**Last Updated**: 2026-03-17

---

## Quick Reference

When user requests feedback:
1. ✅ Check/create feedback file from template
2. ✅ Ask what type of feedback (one question at a time)
3. ✅ Gather details (module, issue, impact, suggestion, priority)
4. ✅ Format and append to feedback file
5. ✅ Confirm and offer to add more
6. ✅ Remind about submission at end

---

## Trigger Phrases

The agent should activate the feedback workflow when user says:
- "power feedback"
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

### Step 5: Confirm and Offer Next Steps

Agent says:
```
✅ I've added your feedback to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`

You can review or edit it anytime. Would you like to:
- Add more feedback
- Continue with the boot camp
- Review the feedback file
```

### Step 6: Remind About Submission

Agent says:
```
When you complete the boot camp, please share this file with the 
power author to help improve the experience for future users.

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
6. **Make it easy**: Offer to add more feedback
7. **Remind about value**: Explain how feedback helps improve the power

---

## Integration Points

### Module 1 Start
Agent says: "If you encounter any issues or have suggestions during the boot camp, just say 'power feedback' and I'll help you document them."

### During Any Module
User can say "power feedback" at any time to document issues as they occur.

### Module 12 Completion
Agent says: "🎉 Congratulations on completing the Senzing Boot Camp! If you have any feedback about your experience, say 'power feedback' and I'll help you document it. If you've already documented feedback, please share `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` with the power author."

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

