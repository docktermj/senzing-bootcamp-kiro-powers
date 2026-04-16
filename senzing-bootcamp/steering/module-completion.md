---
inclusion: manual
---

# Module Completion Workflow

Load this after completing any module. Handles journal entries, reflection, and path completion.

## Bootcamp Journal

Append to `docs/bootcamp_journal.md` (create if needed):

```markdown
## Module N: [Name] — Completed [date]
**What we did:** [1-2 sentences]
**What was produced:** [files/artifacts]
**Why it matters:** [enables next step]
**Bootcamper's takeaway:** [response to reflection question]
```

## Reflection Question

After the factual journal entry, ask: "What's your main takeaway from this module — anything that surprised you, or something you want to remember?"

Append response under "Bootcamper's takeaway." If they decline, write "No additional notes." Don't push.

## Next-Step Options

After the journal entry and reflection, present 3-4 concrete options based on the module just completed. Don't just say "proceed to Module N" — give the user choices:

- **Proceed:** "Ready to move on to Module [N] ([name])?"
- **Iterate:** "Would you like to improve anything from this module first? (e.g., better quality scores, additional data sources, more test cases)"
- **Explore:** "Would you like to dig deeper into what we just did? (e.g., examine specific entities, try different queries, review match explanations)"
- **Share:** "Would you like to prepare a summary of these results to share with your team or stakeholders?"

WAIT for response. Let the user choose their pace.

## Path Completion Detection

After each module, check if the user finished their path's last module:

| Path | Complete after |
|------|----------------|
| A    | Module 1       |
| B    | Module 8       |
| C    | Module 8       |
| D    | Module 12      |

## Path Completion Celebration

When path is complete, present:

- 🎉 "You've completed Path [letter]!"
- Summary of all artifacts built (code, data, docs)
- Where everything lives (src/, data/transformed/, docs/, config/, database/)
- Reference to `docs/bootcamp_journal.md`
- Next options: switch to longer path (modules carry forward), harden for production, or start using the code
- Remind: "Say 'bootcamp feedback' to share your experience"

Load `lessons-learned.md` and offer the retrospective.
