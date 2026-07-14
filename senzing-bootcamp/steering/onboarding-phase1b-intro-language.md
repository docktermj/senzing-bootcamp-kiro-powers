---
inclusion: manual
---

> **Note on file name (historical):** This file keeps `intro-language` in its name for stability, but `Language_Selection` has moved to phase 2 (`onboarding-phase2-track-setup.md`). This file now covers the entity resolution intro handoff, the welcome banner / bootcamp introduction, and the detail-level (verbosity) step.

## 3. Entity Resolution Introduction

<!-- This step introduces entity resolution concepts before the bootcamper
     chooses a programming language, so they have domain context for that decision. -->

#[[file:senzing-bootcamp/steering/entity-resolution-intro.md]]

<!-- The mandatory gate (⛔ MANDATORY GATE — Entity Resolution Exploration)
     within entity-resolution-intro.md serves as the gate for this step.
     The agent MUST NOT proceed past this step until the bootcamper signals
     readiness to continue. -->

### Gate Clearance — Advancing to Step 4

**When the bootcamper signals readiness to proceed at the entity-resolution-intro mandatory gate, immediately proceed to Step 4 below.** Do NOT re-present the entity-resolution-intro content or the gate question — the readiness signal clears the gate.

Recognize any of these readiness signals as gate-clearance that advances the flow directly to Step 4:

- **Acknowledgments:** "ready," "got it," "let's go," "continue," "next," "move on"
- **Affirmatives:** "yes," "sure," "yep"
- **Forward-looking statements:** "what's next," "let's keep going"

**Contrast — follow-up questions are NOT readiness signals.** If the bootcamper's message contains "?", asks for an explanation, or requests clarification about an entity resolution concept, do NOT treat it as a readiness signal and do NOT advance to Step 4. Instead, follow the answer-then-re-present-gate flow defined in `entity-resolution-intro.md`: answer the question using `search_docs`, then re-present the gate. Only a genuine readiness signal — not a follow-up question — routes directly to Step 4.

## 4. Bootcamp Introduction

Immediately before displaying the welcome banner, state that administrative setup is complete and the bootcamp is now starting — for example: "Administrative setup is complete. The bootcamp is starting."

**Display the welcome banner — make it impossible to miss.**

**Standard (single-user) banner:**

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎓🎓🎓  WELCOME TO THE SENZING BOOTCAMP!  🎓🎓🎓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Team mode banner** (when `config/team.yaml` was detected in Step 1b):

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎓🎓🎓  WELCOME TO THE SENZING BOOTCAMP!  🎓🎓🎓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👥 Team: {team_name}  •  {member_count} members
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

This signals to the user that setup is done and the bootcamp is starting. Everything before this was administrative.

Present the overview before track selection. Cover all points naturally:

- This bootcamp is a **guided discovery** of how to use Senzing. It's not a race — feel free to take it slow, read what the bootcamp is telling you, and ask questions at any point to help with your understanding. Be curious. The bootcamp is here to help you learn, not just to produce code.
- Goal: comfortable generating Senzing SDK code. Finish with running code as foundation for real use.
- Module overview table (1-11): what each does and why it matters
- Tracks let you skip to what matters
- Licensing: you already have a built-in 500-record evaluation license — plenty for the bootcamp's demos. If you need more capacity you have options: apply an existing license, or ask the Senzing MCP server to issue a temporary evaluation license for you. Module 1 walks through these options and checks which are available in your session.
- Senzing provides CORD (Collections Of Relatable Data) — curated data collections designed for entity resolution evaluation. Three CORD datasets are available: Las Vegas, London, Moscow. Ask me and I'll look up the current CORD details from the Senzing documentation on demand. If CORD data doesn't meet your specific needs, test data can also be generated.
- If you encounter unfamiliar terms (like Senzing Entity Specification, DATA_SOURCE, entity resolution), just ask me to explain — I'll look up the current definition from the Senzing documentation on demand
- If you noticed hook files (like `.json` files) appearing in your editor panel during setup — those are automated quality checks that run in the background. They do not require your review. You can safely close them, but please do not delete them — they help maintain code quality throughout the bootcamp.

### 4a. Verbosity Preference

👉 **After presenting the overview, ask the bootcamper how much detail they want in the bootcamp output. Present the three presets:**

- **concise** — Minimal explanations, no code walkthroughs, brief recaps. Best for experienced developers.
- **standard** *(recommended)* — Balanced "what and why" explanations, block-level code summaries, before/after framing. Good for most learners.
- **detailed** — Full explanations with workflow connections, line-by-line code walkthroughs, SDK internals. Best for deep learners.

🛑 STOP — Wait for bootcamper response before persisting the selection.

Persist the selection to the `verbosity` key in the preferences file (`config/bootcamp_preferences.yaml`, or `config/preferences_{member_id}.yaml` in team mode) using this format:

```yaml
verbosity:
  preset: standard
  categories:
    explanations: 2
    code_walkthroughs: 2
    step_recaps: 2
    technical_details: 2
    code_execution_framing: 2
```

After the bootcamper selects a preset, confirm the choice and tell them:

"You can change your verbosity level at any time by saying 'change verbosity' or by fine-tuning specific categories like 'I want more code walkthroughs'."

> **Internal directive — not shown to the bootcamper.** Treat verbosity selection as a ⛔ gate step governed by the Answer_Required_Rule (see `conversation-protocol.md`): it requires the bootcamper's Real_Answer. Do NOT assume or fabricate a verbosity preference, and do NOT apply the `standard` preset (or any preset) as a silent default when the bootcamper says nothing. "**standard** *(recommended)*" is an Explicit_Default_Choice — the bootcamper can pick it in one keystroke, and only then do you persist `standard` to `config/bootcamp_preferences.yaml` and proceed. Selecting the default is a Real_Answer; assuming it is an Assumed_Answer.
>
> This is a MANDATORY GATE — you MUST stop and wait for the bootcamper's real input (🛑 STOP — end your response here). End your turn on the question above; do not answer it, do not assume a response, and do not continue to the next step until the bootcamper responds.

---

After Step 4a, load `onboarding-phase2-track-setup.md` for track selection.
