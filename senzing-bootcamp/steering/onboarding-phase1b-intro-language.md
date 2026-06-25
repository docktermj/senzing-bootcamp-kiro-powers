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

## 4. Programming Language Selection

Detect the user's platform (`platform.system()`), then call `get_capabilities` or `sdk_guide` on the Senzing MCP server for the supported languages on that platform. The hard gate in Step 0b guarantees MCP is available — call the tool directly and present the returned programming language list to the bootcamper.

When presenting this question, always use the phrase "programming language" — never the bare word "language" alone — to avoid ambiguity with natural/spoken languages.

The agent MUST use the phrase "programming language" (not just "language") when presenting the selection question to the bootcamper.

👉 Present the MCP-returned programming language list. If the MCP server flags any language as discouraged, unsupported, or limited on the user's platform (e.g., Python on macOS), relay that warning clearly and suggest alternatives. For example: "The Senzing MCP server indicates Python is not recommended on macOS — [reason from MCP]. I'd suggest Java, C#, Rust, or TypeScript instead. Would you like to pick one of those?"

🛑 STOP — Wait for the bootcamper's programming language choice before proceeding.

> **Note:** All listed languages produce working code via the MCP server's
> `generate_scaffold` tool. However, the depth of supplementary examples
> (via `find_examples`) may vary — Python and Java currently have the most
> extensive example coverage. This does not affect the bootcamp workflow.

> Tip: If you plan to use these bootcamp artifacts in production, consider choosing the language your team already uses — the code we generate here is designed to be your starting point for real-world use.

Persist the selection to `config/bootcamp_preferences.yaml`.

Load language steering file immediately after confirmation (`lang-python.md`, `lang-java.md`, etc.).

> ⛔ **MANDATORY GATE** — Programming language selection requires the bootcamper's actual choice. Do NOT assume or fabricate a programming language preference. MUST stop and wait for real input.
>
> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not say "I'll go with X." Do not proceed to the next step. Wait for the bootcamper's real input.

## 5. Bootcamp Introduction

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
- If you noticed hook files (like `.kiro.hook` files) appearing in your editor panel during setup — those are automated quality checks that run in the background. They do not require your review. You can safely close them, but please do not delete them — they help maintain code quality throughout the bootcamp.

### 5a. Verbosity Preference

👉 After presenting the overview, ask the bootcamper how much detail they want in the bootcamp output. Present the three presets:

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

If the bootcamper skips without answering, apply the `standard` preset as the default and inform them: "I've set your verbosity to **standard** (balanced detail). You can change this anytime."

This is NOT a mandatory gate (⛔) — the bootcamper can skip it.

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

### 5b. Comprehension Check

Before moving on to track selection, give the bootcamper a moment to absorb everything from the overview. Present a warm, conversational check-in — this is an invitation, not a quiz.

Output format: your output MUST begin with 👉 followed by the comprehension check question. Example:

```text
👉 That was a lot of ground to cover — does everything so far make sense?
```

If you paraphrase or reformulate the question, the 👉 prefix is still mandatory.

🛑 STOP — Wait for bootcamper response.

**Acknowledgment handling:** If the bootcamper responds with an acknowledgment — phrases like "looks good," "makes sense," "no questions," "let's go," "ready," "all clear," or "got it" — proceed directly to track selection (load `onboarding-phase2-track-setup.md`). Do not ask follow-up questions about the overview.

**Clarification handling:** If the bootcamper asks a clarification question, answer it using the bootcamper's current verbosity settings from the preferences file. After answering, check whether the bootcamper has any more questions before proceeding to track selection. Repeat this cycle — answer, then check for additional questions — until the bootcamper signals they are ready to move on.

**Note:** This step is NOT a gate — it is not mandatory, and the bootcamper can skip it or acknowledge quickly. The `ask-bootcamper` hook handles the closing question on `agentStop`, so do not include inline closing questions here.

---

After Step 5b, load `onboarding-phase2-track-setup.md` for track selection.
