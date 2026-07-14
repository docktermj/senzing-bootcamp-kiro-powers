---
inclusion: manual
---
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

## 4. Programming Language Selection

Detect the user's platform (`platform.system()`), then call `get_capabilities` or `sdk_guide` on the Senzing MCP server for the supported languages on that platform. The hard gate in Step 0b guarantees MCP is available — call the tool directly and present the returned programming language list to the bootcamper.

When presenting this question, always use the phrase "programming language" — never the bare word "language" alone — to avoid ambiguity with natural/spoken languages.

The agent MUST use the phrase "programming language" (not just "language") when presenting the selection question to the bootcamper.

👉 **Present the MCP-returned programming language list. If the MCP server flags any language as discouraged, unsupported, or limited on the user's platform (e.g., Python on macOS), relay that warning clearly and suggest alternatives. For example: "The Senzing MCP server indicates Python is not recommended on macOS — [reason from MCP]. I'd suggest Java, C#, Rust, or TypeScript instead. Would you like to pick one of those?"**

*Internal directive (not shown to the bootcamper): end your turn on the question above and wait for the bootcamper's programming language choice before proceeding.*

> **Note:** All listed languages produce working code via the MCP server's
> `generate_scaffold` tool. However, the depth of supplementary examples
> (via `find_examples`) may vary — Python and Java currently have the most
> extensive example coverage. This does not affect the bootcamp workflow.

> Tip: If you plan to use these bootcamp artifacts in production, consider choosing the language your team already uses — the code we generate here is designed to be your starting point for real-world use.

Persist the selection to `config/bootcamp_preferences.yaml`.

Load language steering file immediately after confirmation (`lang-python.md`, `lang-java.md`, etc.).

> **Internal directive — not shown to the bootcamper.** Treat programming language selection as a ⛔ gate step: it requires the bootcamper's actual choice. Do NOT assume or fabricate a programming language preference, and do NOT say "I'll go with X."
>
> This is a MANDATORY GATE — you MUST stop and wait for the bootcamper's real input (🛑 STOP — end your response here). End your turn on the question above; do not answer it and do not proceed to the next step until the bootcamper responds.

## 5. Bootcamp Introduction

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

### 5a. Verbosity Preference

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

### 5b. Comprehension Check

Before moving on to track selection, give the bootcamper a moment to absorb everything from the overview. Present a warm, conversational check-in — this is an invitation, not a quiz.

Output format: your output MUST begin with 👉 followed by the comprehension check question. Compose it as a single, non-compound question on the first attempt. Example:

```text
👉 That was a lot of ground to cover — does everything so far make sense?
```

If you paraphrase or reformulate the question, keep it a single question and the 👉 prefix is still mandatory.

🛑 STOP — Wait for the bootcamper's Real_Answer before proceeding to track selection.

**Acknowledgment handling:** If the bootcamper responds with an acknowledgment — phrases like "looks good," "makes sense," "no questions," "let's go," "ready," "all clear," or "got it" — that acknowledgment is a Real_Answer, so proceed directly to track selection (load `onboarding-phase2-track-setup.md`). Do not ask follow-up questions about the overview.

**Clarification handling:** If the bootcamper asks a clarification question, that too is a Real_Answer: answer it using the bootcamper's current verbosity settings from the preferences file, then re-present this comprehension check. Repeat this cycle — answer, then re-present the check-in and check for additional questions — until the bootcamper signals they are ready to move on.

> **Internal directive — not shown to the bootcamper.** This comprehension check is governed by the Answer_Required_Rule (see `conversation-protocol.md`): it requires the bootcamper's Real_Answer before you proceed to track selection. A Real_Answer is either a readiness acknowledgment ("makes sense," "no questions," "ready," etc.) or a clarification question — answer the latter, then re-present this check-in, looping until the bootcamper signals readiness. Do NOT proceed as if the bootcamper acknowledged when they said nothing; treating silence as readiness is an Assumed_Answer and is forbidden. The `ask-bootcamper` hook owns the closing question on `Stop`, so do not include inline closing questions here.

---

After Step 5b, load `onboarding-phase2-track-setup.md` for track selection.
