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

Before starting the bootcamp, verify that the Senzing MCP server is reachable. The MCP server is required for the bootcamp — it generates SDK code in your chosen language, looks up Senzing facts and configuration details, and provides working examples on demand.

### Probe

Attempt a lightweight MCP tool call with a 10-second timeout:

```text
search_docs(query="health check", version="current")
```

### Success Path

If the call returns any response (even empty results) within 10 seconds:

1. Proceed silently — do not display anything to the bootcamper.

### Failure Path

If the call times out or errors after 10 seconds:

1. Display the following blocking error:

```text
⛔ The Senzing MCP server is unreachable.

The MCP server is required for the bootcamp — it generates SDK code,
looks up Senzing facts, and provides working examples. The bootcamp
cannot proceed without it.

**Troubleshooting steps:**
1. Verify internet connectivity (can you load any website?)
2. Test the endpoint: curl -s -o /dev/null -w "%{http_code}" https://mcp.senzing.com:443
3. If behind a corporate proxy, allowlist mcp.senzing.com:443
4. Restart the MCP connection in the Kiro Powers panel
5. Verify DNS: nslookup mcp.senzing.com

After fixing the connection, say "retry" to try again.
```

2. 🛑 STOP — Do NOT proceed to any subsequent step. Wait for the
   bootcamper to fix the connection and request a retry.

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

   **Verify hooks:** Check that each Critical Hook exists in `.kiro/hooks/`. If any are missing, retry creation once using `createHook`. Record the hook installation status (list of installed hook names and timestamp) in `config/bootcamp_preferences.yaml` under a `hooks_installed` key.

3. Generate foundational steering files (`product.md`, `tech.md`, `structure.md`) at `.kiro/steering/`. Each MUST include `inclusion` and `description` in the YAML frontmatter. Use `auto` for `structure.md`, `always` for the others.

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

Detect the user's platform (`platform.system()`), then call `get_capabilities` or `sdk_guide` on the Senzing MCP server for the supported languages on that platform. The hard gate in Step 0b guarantees MCP is available — call the tool directly and present the returned language list to the bootcamper.

👉 Present the MCP-returned language list. If the MCP server flags any language as discouraged, unsupported, or limited on the user's platform (e.g., Python on macOS), relay that warning clearly and suggest alternatives. For example: "The Senzing MCP server indicates Python is not recommended on macOS — [reason from MCP]. I'd suggest Java, C#, Rust, or TypeScript instead. Would you like to pick one of those?"

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

### 3a. Windows Prerequisite Installation Offers

**Condition:** The bootcamper's platform is Windows AND the preflight report contains a "Package Manager" check with status "warn" (Scoop not found).

If this condition is met, present the following offer to the bootcamper:

---

**Scoop is not installed.** Scoop is a command-line installer for Windows that the bootcamp uses to install prerequisites like Java, .NET SDK, Rust, Node.js, and the Senzing SDK. Without it, you'll need to install these tools manually later in Module 2.

👉 Would you like to install Scoop now?

- **Install Scoop now** — I'll run the official installer and verify it works.
- **Skip for later** — Module 2 will walk you through installation when needed.

---

⛔ **MUST NOT install without explicit bootcamper confirmation.** Wait for a clear acceptance before executing any installation command.

**If the bootcamper accepts ("Install Scoop now"):**

1. Execute the official Scoop installation command in PowerShell:

   ```powershell
   irm get.scoop.sh | iex
   ```

2. After the command completes, verify the installation:

   ```powershell
   scoop --version
   ```

3. **If verification succeeds:** Report the installed version to the bootcamper (e.g., "✅ Scoop installed successfully — version X.Y.Z"). Proceed to check whether the chosen runtime also needs installation (see Step 3b if applicable).

4. **If verification fails or the installation command returns an error:**
   - Display the error output to the bootcamper.
   - Suggest manual installation steps:

     ```text
     ⚠️ Scoop installation failed. You can try installing manually:
     1. Open PowerShell as your normal user (not Admin)
     2. Run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
     3. Run: irm get.scoop.sh | iex
     4. Restart your terminal and verify with: scoop --version

     If issues persist, see https://scoop.sh for troubleshooting.
     ```

   - Proceed with the existing WARN behavior — do NOT block onboarding. Note that Module 2 will handle Scoop installation.

**If the bootcamper declines ("Skip for later"):**

Proceed with the existing WARN behavior. Inform the bootcamper: "No problem — Module 2 will guide you through Scoop installation when it's needed."

🛑 STOP — Wait for the bootcamper's response before proceeding to runtime installation.

### 3b. Windows Runtime Installation via Scoop

**Condition:** The bootcamper's platform is Windows AND Scoop is available (either already installed or just installed in Step 3a) AND the bootcamper's chosen language runtime check has status "warn" (runtime not found).

**If Scoop is NOT available** (bootcamper declined Scoop installation in Step 3a): Skip this section entirely. Defer runtime installation to Module 2.

If the condition is met, present the following offer to the bootcamper:

---

**Your chosen runtime is not installed.** I can install it now using Scoop so your environment is ready before we begin.

👉 Would you like to install the runtime now?

- **Install [runtime] now** — I'll run the Scoop installer and verify it works.
- **Skip for later** — Module 2 will walk you through installation when needed.

---

⛔ **MUST NOT install without explicit bootcamper confirmation.** Wait for a clear acceptance before executing any installation command.

**Installation commands** — Reference the `SCOOP_RUNTIME_COMMANDS` mapping in `senzing-bootcamp/scripts/preflight.py` for the correct commands per runtime:

| Runtime | Bucket Command          | Install Command                      | Verify Command    |
|---------|-------------------------|--------------------------------------|-------------------|
| Java    | `scoop bucket add java` | `scoop install java/temurin-lts-jdk` | `java --version`  |
| .NET    | *(none)*                | `scoop install dotnet-sdk`           | `dotnet --version`|
| Rust    | *(none)*                | `scoop install rustup`               | `rustc --version` |
| Node.js | *(none)*                | `scoop install nodejs-lts`           | `node --version`  |

**If the bootcamper accepts ("Install [runtime] now"):**

1. **For Java only** — First add the required Scoop bucket:

   ```powershell
   scoop bucket add java
   ```

   - If the bucket addition succeeds (or the bucket already exists), proceed to step 2.
   - If the bucket addition fails, display the error and suggest the Adoptium website as an alternative:

     ```text
     ⚠️ Could not add the Java bucket to Scoop. You can install Java manually from:
     https://adoptium.net

     Download and install Temurin JDK (LTS), then restart your terminal.
     ```

     Proceed without blocking — do NOT escalate to FAIL.

2. Execute the appropriate Scoop install command for the chosen runtime (from the table above).

3. After the command completes, verify the installation using the runtime's verify command (from the table above).

4. **If verification succeeds:** Report the installed version to the bootcamper (e.g., "✅ [Runtime] installed successfully — version X.Y.Z"). Record the installation in preferences (see Step 5).

5. **If verification fails or the installation command returns an error:**
   - Display the error output to the bootcamper.
   - Suggest alternative installation methods:

     ```text
     ⚠️ [Runtime] installation via Scoop failed. Alternative installation methods:
     - Java: Download from https://adoptium.net
     - .NET SDK: Download from https://dotnet.microsoft.com/download
     - Rust: Run `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
     - Node.js: Download from https://nodejs.org
     ```

   - Proceed with the existing WARN behavior — do NOT block onboarding. Note that Module 2 will handle runtime installation.

**If the bootcamper declines ("Skip for later"):**

Proceed with the existing WARN behavior. Inform the bootcamper: "No problem — Module 2 will guide you through runtime installation when it's needed."

### 3c. Re-run Preflight After Installation

**After any successful installation** (Scoop in Step 3a or runtime in Step 3b), re-run the preflight script to update the report:

```bash
python3 senzing-bootcamp/scripts/preflight.py
```

Present the updated report to the bootcamper before proceeding to Step 4. This confirms the installation was successful and shows the improved environment status.

### 3d. Record Installation Preferences

After completing Steps 3a–3c, record the installation outcomes in `config/bootcamp_preferences.yaml`. Do NOT overwrite existing content — append or merge new keys.

**After successful Scoop installation:**

```yaml
scoop_installed_during_onboarding: true
```

**After successful runtime installation:**

```yaml
runtimes_installed_during_onboarding:
  - name: java        # or dotnet, rust, nodejs
    version: "21.0.3" # actual version from verify command
```

**When the bootcamper declines any installation offer:**

```yaml
prerequisite_installation_deferred: true
```

**Important:** If the preferences file does not exist yet, create it with only the new keys. If it already exists, merge the new keys without removing existing content.

**Module 2 integration:** When Module 2 begins, the agent SHOULD check `config/bootcamp_preferences.yaml` for `scoop_installed_during_onboarding` and `runtimes_installed_during_onboarding` keys. If these indicate that Scoop or a runtime was already installed during onboarding, Module 2 should skip re-installation of those items.

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
- Tracks let you skip to what matters
- Built-in 500-record eval license; bring your own for more
- Senzing provides CORD (Collections Of Relatable Data) — curated data collections designed for entity resolution evaluation. Three CORD datasets are available: Las Vegas, London, Moscow. Learn more: <https://senzing.com/senzing-ready-data-collections-cord/>. If CORD data doesn't meet your specific needs, test data can also be generated.
- If you encounter unfamiliar terms (like Senzing Entity Specification, DATA_SOURCE, entity resolution), just ask me to explain — I'll look up the current definition from the Senzing documentation on demand

### 4a. What Is Entity Resolution?

# [[file:senzing-bootcamp/steering/entity-resolution-intro.md]]

### 4b. Verbosity Preference

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

### 4c. Comprehension Check

Before moving on to track selection, give the bootcamper a moment to absorb everything from the overview. Present a warm, conversational check-in — this is an invitation, not a quiz:

👉 "That was a lot of ground to cover. Does everything so far makes sense? Do you have any questions about the modules, the data, licensing, or anything else before we move on to choosing a track?"

🛑 STOP — Wait for bootcamper response.

**Acknowledgment handling:** If the bootcamper responds with an acknowledgment — phrases like "looks good," "makes sense," "no questions," "let's go," "ready," "all clear," or "got it" — proceed directly to Step 5 (Track Selection). Do not ask follow-up questions about the overview.

**Clarification handling:** If the bootcamper asks a clarification question, answer it using the bootcamper's current verbosity settings from the preferences file. After answering, check whether the bootcamper has any more questions before proceeding to Step 5. Repeat this cycle — answer, then check for additional questions — until the bootcamper signals they are ready to move on.

**Note:** This step is NOT a gate — it is not mandatory, and the bootcamper can skip it or acknowledge quickly. The `ask-bootcamper` hook handles the closing question on `agentStop`, so do not include inline closing questions here.

## 5. Track Selection

> **Authoritative source:** Track definitions are derived from
> `config/module-dependencies.yaml`. To update tracks, edit the dependency graph
> first, then run `python3 scripts/validate_dependencies.py` to verify consistency.

👉 Present tracks — not mutually exclusive, all completed modules carry forward:

- **Core Bootcamp** *(recommended)* — Modules 1, 2, 3, 4, 5, 6, 7. Recommended foundation covering problem definition through query/visualize.
- **Advanced Topics** *(not recommended for bootcamp)* — Modules 1–11. Adds production-readiness topics (performance, security hardening, monitoring, and packaging/deployment) as advanced add-ons layered on top of the core bootcamp.

Module 2 is automatically inserted before any module that needs the SDK.

Interpreting responses: "core"/"core_bootcamp"→start at Module 1, "advanced"/"advanced_topics"→start at Module 1. Bare number→clarify track vs module.

> ⛔ **MANDATORY GATE — STOP HERE.** After presenting the track options above, you MUST stop. Do NOT proceed to any module. Do NOT fabricate a user response. Do NOT assume a track choice. Do NOT generate text like "I'll go with Core Bootcamp for you." The bootcamper MUST provide their own choice. The `ask-bootcamper` hook will fire and prompt them. Wait for their real response before continuing.
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
| 3→4    | System verification passed or skipped                                              |
| 4→5    | Sources collected, files in `data/raw/`                                            |
| 5→6    | Sources evaluated, mapped, programs tested, quality >70%                           |
| 6→7    | Sources loaded, no critical errors                                                 |
| 7→8    | Queries answer business problem. Load `cloud-provider-setup.md`                    |
| 8→9    | Baselines captured, bottlenecks documented                                         |
| 9→10   | Security checklist complete, no critical vulns                                     |
| 10→11  | Monitoring configured, health checks passing                                       |

## Hook Registry

# [[file:senzing-bootcamp/steering/hook-registry.md]]
