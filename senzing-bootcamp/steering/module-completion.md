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

After the factual journal entry, ask the bootcamper about their main takeaway from the module — anything that surprised them, or something they want to remember.

Append response under "Bootcamper's takeaway." If they decline, write "No additional notes." Don't push.

## Next-Step Options

After the journal entry and reflection, present 3-4 concrete options based on the module just completed. Don't just say "proceed to Module N" — give the user choices:

- **Proceed:** "Ready to move on to Module [N] ([name])?"
- **Iterate:** "Would you like to improve anything from this module first?"
- **Explore:** "Would you like to explore further — visualize entities, examine match explanations, or search by attributes? (For other modules: dig deeper into what we just produced.)"
- **Undo:** "Roll back this module's work with `python scripts/rollback_module.py --module N`"
- **Share:** "Would you like to prepare a summary to share with your team?"

Present these as a single list for the bootcamper to choose from.

**Module 3 special case:** The visualization offer (web page with interactive features) should already have been presented before reaching this workflow. If the user declined, the Explore option above gives them another chance.

## Path Completion Detection

After each module, check if the user finished their path's last module:

| Path | Complete after |
|------|----------------|
| A    | Module 3       |
| B    | Module 7       |
| C    | Module 7       |
| D    | Module 11      |

## Path Completion Celebration

When path is complete, present:

- 🎉 "You've completed Path [letter]!"
- Summary of all artifacts built (code, data, docs)
- Where everything lives (src/, data/transformed/, docs/, config/, database/)
- Reference to `docs/bootcamp_journal.md`
- Next options: switch to longer path (modules carry forward), harden for production, or start using the code
- Export option: "Would you like to export a shareable report of your bootcamp results?" — when accepted, run `python scripts/export_results.py` and present the output path to the bootcamper. This option appears only at track completion, not after every module.
- Graduation offer (after the export offer, before the feedback reminder):
  1. Read `skip_graduation` from `config/bootcamp_preferences.yaml`. If `skip_graduation` is `true`, skip the graduation offer entirely.
  2. If not skipped, present: "🎓 Would you like to run the graduation workflow? It will help you turn your bootcamp project into a production-ready codebase — clean structure, production configs, CI/CD pipeline, and a migration checklist."
  3. If accepted: load `steering/graduation.md` and begin the workflow.
  4. If declined: ask "Would you like me to remember this choice so I don't ask again?" If the bootcamper confirms, set `skip_graduation: true` in `config/bootcamp_preferences.yaml`. Then continue with the remaining post-completion options.
- Remind: "Say 'bootcamp feedback' to share your experience"

Load `lessons-learned.md` and offer the retrospective.
