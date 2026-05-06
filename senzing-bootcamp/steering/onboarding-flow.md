---
inclusion: manual
---

# Onboarding Flow

Load when starting a fresh bootcamp. Sequence: directory creation → language selection → prerequisites → introduction → track selection.

**Note:** The `ask-bootcamper` hook fires on every `agentStop` and generates a contextual 👉 closing question. Do NOT include inline closing questions or WAIT instructions at the end of steps — present the information and stop. **Exception — Mandatory gates:** Steps marked with ⛔ are mandatory gates where the agent MUST stop and MUST NOT proceed without real user input. These are the only steps where an explicit stop instruction overrides the general rule.

## 0. Setup Preamble

Before doing any setup work, tell the user:

"I'm going to do some quick administrative setup — creating your project directory, installing hooks, and checking your environment. You'll see me working for a moment. When I'm done, you'll see a big **WELCOME TO THE SENZING BOOTCAMP** banner — that's when the bootcamp officially starts and I'll begin asking you questions."

## 0b. MCP Health Check

Before starting the bootcamp, verify that the Senzing MCP server is reachable. The MCP server powers the bootcamp's interactive features — it generates SDK code in your chosen language, looks up Senzing facts and configuration details, and provides working examples on demand. Without it, the bootcamp can still function in a limited offline mode.

### Probe

Attempt a lightweight MCP tool call with a 10-second timeout:

```text
search_docs(query="health check", version="current")
```

### Success Path

If the call returns any response (even empty results) within 10 seconds:

1. Proceed silently — do not display anything to the bootcamper.
2. Write `config/.mcp_status` with:

```json
{"last_check": "<ISO 8601 timestamp>", "status": "healthy", "error_message": null}
```

### Failure Path

If the call times out or errors after 10 seconds:

1. Write `config/.mcp_status` with:

```json
{"last_check": "<ISO 8601 timestamp>", "status": "unreachable", "error_message": "<error details>"}
```

2. Display the following warning to the bootcamper:

```text
⚠️ The Senzing MCP server is currently unreachable.

The MCP server is what lets me generate working Senzing code, look up accurate
SDK details, and pull real examples for you. Without it, some features are limited.

**What's unavailable**: Code generation, fact lookup, example search
**What you can still do**: Review existing artifacts, work on documentation, plan next steps

For detailed offline capabilities, see docs/guides/OFFLINE_MODE.md
```

3. Ask:

```text
👉 Would you like to continue in offline mode, or try again later?
```

### Mid-Session Recovery

Before any step that requires MCP tools, check `config/.mcp_status`. If `status` is `"unreachable"`:

1. Re-attempt the `search_docs(query="health check", version="current")` probe with a 10-second timeout.
2. If successful, update `config/.mcp_status` to `"healthy"` and display: "✅ MCP server is back online — full functionality restored."
3. If still unreachable, inform the bootcamper that MCP remains unavailable and offer alternatives.

## 1. Directory Structure

Execute these setup actions in order. Do not narrate the details to the user.

1. Check if `src/`, `data/`, `docs/` exist. If not, load `project-structure.md` and create.
2. **Install Critical Hooks:** For each hook in the Hook Registry's "Critical Hooks" section below, call the `createHook` tool with the specified parameters. Create `.kiro/hooks/` directory first if needed. If a `createHook` call fails, log the failure and continue with the remaining hooks. After all attempts, report any failures to the bootcamper with the affected functionality using the impact messages below. If all Critical Hook creations fail, warn the bootcamper that hooks are unavailable and suggest restarting onboarding.

   **Failure impact messages** — when a critical hook fails, report the corresponding message:

   | Hook | Impact Message |
   | ---- | -------------- |
   | ask-bootcamper | "Session summaries, closing questions, and post-completion feedback reminders will not be automatically generated when the agent stops." |
   | code-style-check | "Code style will not be automatically checked on save." |
   | commonmark-validation | "Markdown files will not be automatically checked for CommonMark compliance." |
   | enforce-feedback-path | "Feedback may be written to incorrect file locations." |
   | enforce-working-directory | "File writes to /tmp or external paths will not be automatically blocked." |
   | review-bootcamper-input | "Feedback trigger phrases will not be automatically detected on message submission." |
   | verify-senzing-facts | "Senzing facts will not be automatically verified against MCP tools before writing." |

   **Verify hooks:** Check that each Critical Hook exists in `.kiro/hooks/`. If any are missing, retry creation once using `createHook`. Record the hook installation status (list of installed hook names and timestamp) in `config/bootcamp_preferences.yaml` under a `hooks_installed` key.

3. **Copy glossary:** copy `senzing-bootcamp/docs/guides/GLOSSARY.md` to `docs/guides/GLOSSARY.md`. This MUST happen before Step 4 (Introduction) references it.
4. Generate foundational steering files (`product.md`, `tech.md`, `structure.md`) at `.kiro/steering/`. Each MUST include `inclusion` and `description` in the YAML frontmatter. Use `auto` for `structure.md`, `always` for the others.

## 1b. Team Detection

After directory setup, check whether this is a team bootcamp:

1. Check if `config/team.yaml` exists in the project root.
2. **If found**, read and validate it using the `team_config_validator` module (`senzing-bootcamp/scripts/team_config_validator.py`):
   - If validation fails, print the validation errors and proceed with standard single-user onboarding. Do NOT block onboarding on a broken team config.
   - If validation succeeds, activate **team mode** for the rest of onboarding.
3. **If not found**, proceed with standard single-user onboarding (skip the rest of this section).

**When team mode is active:**

Present the member list so the bootcamper can identify themselves.

Display the list of members from the config:

```text
Team: {team_name} ({member_count} members)

  1. {member_id} — {member_name}
  2. {member_id} — {member_name}
  ...
```

**After the bootcamper selects a member:**

- Validate the selection matches a member `id` in the config. If it does not match, ask them to choose from the available IDs or add themselves to `config/team.yaml`.
- In **co-located** mode: create or update the member-specific progress file at `config/progress_{member_id}.json` (using the same JSON schema as `bootcamp_progress.json`).
- In **distributed** mode: create or update `config/bootcamp_progress.json` in the member's own repo (standard single-user path).
- Persist the selected member ID to `config/bootcamp_preferences.yaml` (or `config/preferences_{member_id}.yaml` in co-located mode) under a `team_member_id` key.
- Store the team mode state so subsequent steps (welcome banner, progress tracking) use team-aware paths.

## 2. Language Selection

**Detect the user's platform first** (`platform.system()`), then query the Senzing MCP server (`get_capabilities` or `sdk_guide`) for which languages are supported on that platform. The MCP server is the authoritative source — do not hardcode language/platform assumptions.

👉 Present the MCP-returned language list to the bootcamper. **If the MCP server flags any language as discouraged, unsupported, or limited on the user's platform (e.g., Python on macOS), relay that warning clearly to the bootcamper** and suggest alternatives. For example, if MCP discourages Python on macOS, tell them: "The Senzing MCP server indicates Python is not recommended on macOS — [reason from MCP]. I'd suggest Java, C#, Rust, or TypeScript instead. Would you like to pick one of those?"

Persist the selection to `config/bootcamp_preferences.yaml`.

Load language steering file immediately after confirmation (`lang-python.md`, `lang-java.md`, etc.).

> ⛔ **MANDATORY GATE** — Language selection requires the bootcamper's actual choice. Do NOT assume or fabricate a language preference. MUST stop and wait for real input.
>
> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not say "I'll go with X." Do not proceed to the next step. Wait for the bootcamper's real input.

## 3. Prerequisite Check (Mandatory Gate)

Run the consolidated preflight script to verify the environment before proceeding:

```bash
python3 senzing-bootcamp/scripts/preflight.py
```

Present the full report to the bootcamper. Then act on the verdict:

- **FAIL:** Present the fix instructions from the report and ask the bootcamper to resolve the issues before proceeding. Do NOT continue to language selection until the verdict is no longer FAIL. Re-run the script after the bootcamper reports fixes are applied.
- **WARN:** Present the warnings to the bootcamper and allow them to proceed. Note any items that may need attention later (e.g., Senzing SDK not installed — Module 2 will cover it).
- **PASS:** Proceed silently to the next step without additional prompts.

**If the Senzing SDK is already installed and working (V4.0+):** Tell the user: "Senzing SDK is already installed." When Module 2 is reached (either explicitly or auto-inserted), the module's Step 1 check will detect this and skip installation. Do not re-install.

**Note:** This step replaces the previous inline `shutil.which()` checks. All environment verification is now handled by `preflight.py`.

## 4. Bootcamp Introduction

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
- Mock data available anytime. Three sample datasets: Las Vegas, London, Moscow
- Built-in 500-record eval license; bring your own for more
- Tracks let you skip to what matters
- If you encounter unfamiliar terms (like Senzing Entity Specification, DATA_SOURCE, entity resolution), there's a glossary at `docs/guides/GLOSSARY.md` — and you can always ask me to explain anything

### 4a. What Is Entity Resolution?

# [[file:senzing-bootcamp/steering/entity-resolution-intro.md]]

### 4b. Verbosity Preference

👉 After presenting the overview, ask the bootcamper how much detail they want in the bootcamp output. Present the three presets:

- **concise** — Minimal explanations, no code walkthroughs, brief recaps. Best for experienced developers.
- **standard** *(recommended)* — Balanced "what and why" explanations, block-level code summaries, before/after framing. Good for most learners.
- **detailed** — Full explanations with workflow connections, line-by-line code walkthroughs, SDK internals. Best for deep learners.

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

### 4c. Comprehension Check

Before moving on to track selection, give the bootcamper a moment to absorb everything from the overview. Present a warm, conversational check-in — this is an invitation, not a quiz:

👉 "That was a lot of ground to cover. Does everything so far makes sense? Do you have any questions about the modules, the data, licensing, or anything else before we move on to choosing a track?"

**Acknowledgment handling:** If the bootcamper responds with an acknowledgment — phrases like "looks good," "makes sense," "no questions," "let's go," "ready," "all clear," or "got it" — proceed directly to Step 5 (Track Selection). Do not ask follow-up questions about the overview.

**Clarification handling:** If the bootcamper asks a clarification question, answer it using the bootcamper's current verbosity settings from the preferences file. After answering, check whether the bootcamper has any more questions before proceeding to Step 5. Repeat this cycle — answer, then check for additional questions — until the bootcamper signals they are ready to move on.

**Note:** This step is NOT a gate — it is not mandatory, and the bootcamper can skip it or acknowledge quickly. The `ask-bootcamper` hook handles the closing question on `agentStop`, so do not include inline closing questions here.

## 5. Track Selection

> **Authoritative source:** Track definitions are derived from
> `config/module-dependencies.yaml`. To update tracks, edit the dependency graph
> first, then run `python3 scripts/validate_dependencies.py` to verify consistency.

👉 Present tracks — not mutually exclusive, all completed modules carry forward:

- **A) Quick Demo** — 1→2→3. Verify technology works. One session.
- **B) Fast Track** — 5→6→7. Have Entity Specification data. Straight to loading/querying.
- **C) Complete Beginner** — 1→4→5→6→7. From scratch with raw data.
- **D) Full Production** — All 1-11. Building for production.

Module 2 inserted automatically before any module needing SDK.

Interpreting responses: "A"/"demo"→Module 1, "B"/"fast"→Module 5, "C"/"beginner"→Module 1, "D"/"full"→Module 1. Bare number→clarify letter vs module.

> ⛔ **MANDATORY GATE — STOP HERE.** After presenting the track options above, you MUST stop. Do NOT proceed to any module. Do NOT fabricate a user response. Do NOT assume a track choice. Do NOT generate text like "Human: A" or "I'll go with Track A for you." The bootcamper MUST provide their own choice. The `ask-bootcamper` hook will fire and prompt them. Wait for their real response before continuing.
>
> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not say "I'll go with X." Do not proceed to the next step. Wait for the bootcamper's real input.

## Switching Tracks

All completed modules carry forward. Read the appropriate progress file — in team mode, use the member-specific progress file (`config/progress_{member_id}.json` in co-located mode, or `{repo_path}/config/bootcamp_progress.json` in distributed mode); in single-user mode, use `bootcamp_progress.json`. Show new track requirements vs. done, update preferences, resume from first incomplete module.

## Changing Language

Update preferences. Warn: existing code in `src/` must be regenerated. Data/docs/config unaffected. Don't mix languages.

## Validation Gates

> **Authoritative source:** Gate conditions are derived from
> `config/module-dependencies.yaml`. To update gate conditions, edit the
> dependency graph first, then run `python3 scripts/validate_dependencies.py` to
> verify consistency.

Run `validate_module.py --module N` before proceeding. Update `bootcamp_progress.json` and `bootcamp_preferences.yaml`. Every 3 modules: progress bar.

Gate checks:

| Gate   | Requires                                                                           |
|--------|------------------------------------------------------------------------------------|
| 1→2    | Problem documented, sources identified, criteria defined                           |
| 2→3    | SDK installed, DB configured, test passes                                          |
| 3→4    | Demo completed or skipped                                                          |
| 4→5    | Sources collected, files in `data/raw/`                                            |
| 5→6    | Sources evaluated, mapped, programs tested, quality >70%                           |
| 6→7    | Sources loaded, no critical errors                                                 |
| 7→8    | Queries answer business problem. Load `cloud-provider-setup.md`                    |
| 8→9    | Baselines captured, bottlenecks documented                                         |
| 9→10   | Security checklist complete, no critical vulns                                     |
| 10→11  | Monitoring configured, health checks passing                                       |

## Hook Registry

# [[file:senzing-bootcamp/steering/hook-registry.md]]
