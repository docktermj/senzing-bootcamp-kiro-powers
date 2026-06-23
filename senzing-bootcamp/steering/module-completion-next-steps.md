---
inclusion: manual
---

## Next-Step Options

After the journal entry, present 3-4 concrete options based on the module just completed. Don't just say "proceed to Module N" — give the user choices:

- **Proceed:** "Ready to move on to Module [N] ([name])?"
- **Iterate:** "Would you like to improve anything from this module first?"
- **Explore:** "Would you like to explore further — visualize entities, examine match explanations, or search by attributes? (For other modules: dig deeper into what we just produced.)"
- **Undo:** "Roll back this module's work with `python3 scripts/rollback_module.py --module N`"
- **Share:** "Would you like to prepare a summary to share with your team?"

When the bootcamper asks to roll back a module, always run `rollback_module.py --preview --module N` first and present the results conversationally (files affected, safety assessment, downstream impact) before asking whether they want to proceed. Only execute `rollback_module.py --yes --module N` after explicit confirmation.

Present these as a single list for the bootcamper to choose from.

### Final-Message Ordering

The forward 👉 "Ready to move on to Module [N]?" question must be the **final message** of this input-expecting turn (per the Final-Message Invariant in `conversation-protocol.md`). Run any per-module recap/confirmation BEFORE the forward transition question, or re-surface the forward 👉 "Ready for Module X?" question as the final message after any recap/confirmation, with `config/.question_pending` (re)written for it. A recap/confirmation line must never be the final message of this turn. This does not weaken the affirmative-transition commitment below.

### ⛔ Immediate Execution on Affirmative Response

**When the bootcamper says "yes" to "Ready to move on to Module [N]?", the agent MUST immediately execute the next module's startup sequence:**

1. Display the module banner
2. Show the journey map
3. Begin Step 1

**There are ZERO permitted steps between the affirmative response and the module startup sequence.**

⛔ **PROHIBITED between affirmative response and module startup:**

- Intermediate acknowledgment (e.g., "Great! Let's get started...", "Awesome, moving on...")
- Progress-saving behavior (e.g., "Let me save your progress first...", "Let me note where we left off...")
- Session-ending behavior (e.g., "We can pick this up next time...", "Let me wrap up this session...")
- Any text output that is not the module banner

The affirmative response IS the trigger. The module banner IS the next thing the bootcamper sees. Nothing else.

**Module 3 special case:** The visualization offer (web page with interactive features) should already have been presented before reaching this workflow. If the user declined, the Explore option above gives them another chance.
