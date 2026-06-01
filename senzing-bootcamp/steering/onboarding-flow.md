---
inclusion: manual
---

# Onboarding Flow

Load when starting a fresh bootcamp. Sequence: directory creation → prerequisites → entity resolution → language selection → introduction → track selection.

**Note:** The `ask-bootcamper` hook fires on every `agentStop` and generates a contextual 👉 closing question. Do NOT include inline closing questions or WAIT instructions at the end of steps — present the information and stop. **Exception — Mandatory gates:** Steps marked with ⛔ are mandatory gates where the agent MUST stop and MUST NOT proceed without real user input. These are the only steps where an explicit stop instruction overrides the general rule.

## Phase Sub-Files

- **Phase 1b — Entity Resolution Intro & Language Selection** (steps 3–5b): `onboarding-phase1b-intro-language.md`

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

## 0c. Version Display

Extract the power version from the POWER.md frontmatter `version` field (received during power activation) and display it to the bootcamper:

```text
Senzing Bootcamp Power vX.Y.Z
```

This is automatic — no user interaction is required. Display the version as the first onboarding output before proceeding.

If the version field is not present in the POWER.md frontmatter or cannot be parsed, display:

```text
⚠️ Could not determine power version.
```

Then continue with the onboarding sequence — do NOT block on version errors.

## 1. Directory Structure

Execute these setup actions in order. Do not narrate the details to the user.

1. Check if `src/`, `data/`, `docs/` exist. If not, load `project-structure.md` and create.
2. **Install Critical Hooks:** Load `hook-registry-critical.md` and create each Critical Hook using the `createHook` tool. For each hook entry, use EXACTLY the `id`, `name`, `description`, event type, file patterns, tool types, and prompt text specified in the registry. **CRITICAL: The `name` parameter passed to `createHook` MUST be the exact string from the `- name:` line in `hook-registry-critical.md` (e.g., `to wait for your answer`, NOT `Ask Bootcamper`).** The `name` field is user-facing — the Kiro UI renders it as "Ask Kiro Hook {name}", so it must follow the "to {verb phrase}" pattern. Create `.kiro/hooks/` directory first if needed. If a `createHook` call fails, log the failure and continue with the remaining hooks. After all attempts, report any failures to the bootcamper with the affected functionality using the impact messages below. If all Critical Hook creations fail, warn the bootcamper that hooks are unavailable and suggest restarting onboarding.

   **Failure impact messages** — when a critical hook fails, report the corresponding message:

   | Hook | Impact Message |
   | ---- | -------------- |
   | ask-bootcamper | "Session summaries, closing questions, and post-completion feedback reminders will not be automatically generated when the agent stops." |
   | code-style-check | "Code style will not be automatically checked on save." |
   | commonmark-validation | "Markdown files will not be automatically checked for CommonMark compliance." |
   | review-bootcamper-input | "Feedback trigger phrases will not be automatically detected on message submission." |
   | write-policy-gate | "Write policy violations (direct SQL, compound questions, external paths) will not be automatically detected and blocked." |

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

## 2. Prerequisite Check (Mandatory Gate)

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

### 2a. Windows Prerequisite Installation Offers

**Condition:** The bootcamper's platform is Windows AND the preflight report contains a "Package Manager" check with status "warn" (Scoop not found).

If this condition is met, present the following offer to the bootcamper:

---

**Scoop is not installed.** Scoop is a command-line installer for Windows that the bootcamp uses to install prerequisites like Java, .NET SDK, Rust, Node.js, and the Senzing SDK. Without it, you'll need to install these tools manually later in Module 2.

👉 Would you like to install Scoop now?

- **Install Scoop now** — I'll run the official installer and verify it works.
- **Skip for later** — Module 2 will walk you through installation when needed.

---

⛔ **MUST NOT install without explicit bootcamper confirmation.** Wait for a clear acceptance before executing any installation command.

**If accepted:** Run `irm get.scoop.sh | iex` in PowerShell, then verify with `scoop --version`. On success, report the version and proceed to Step 2b. On failure, display the error, suggest manual install from the official Scoop site (scoop.sh), and proceed without blocking.

**If declined:** Inform the bootcamper Module 2 will handle it. Proceed with WARN behavior.

🛑 STOP — Wait for the bootcamper's response before proceeding to runtime installation.

### 2b. Windows Runtime Installation via Scoop

**Condition:** The bootcamper's platform is Windows AND Scoop is available (either already installed or just installed in Step 2a) AND the bootcamper's chosen language runtime check has status "warn" (runtime not found).

**If Scoop is NOT available** (bootcamper declined Scoop installation in Step 2a): Skip this section entirely. Defer runtime installation to Module 2.

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

**If accepted:**

1. **For Java only** — First add the required Scoop bucket: `scoop bucket add java`. If it fails, suggest adoptium.net as alternative and proceed without blocking.
2. Execute the appropriate Scoop install command for the chosen runtime (from the table above).
3. Verify the installation using the runtime's verify command (from the table above).
4. **If verification succeeds:** Report the installed version (e.g., "✅ [Runtime] installed — version X.Y.Z"). Record in preferences (see Step 2d).
5. **If verification fails:** Display the error, suggest alternative downloads (Adoptium for Java, dotnet.microsoft.com for .NET, rustup.rs for Rust, nodejs.org for Node.js), and proceed with WARN behavior.

**If declined:** Inform the bootcamper Module 2 will handle it. Proceed with WARN behavior.

### 2c. Re-run Preflight After Installation

**After any successful installation** (Scoop in Step 2a or runtime in Step 2b), re-run `python3 senzing-bootcamp/scripts/preflight.py` and present the updated report before proceeding to Step 3.

### 2d. Record Installation Preferences

After completing Steps 2a–2c, record the installation outcomes in `config/bootcamp_preferences.yaml`. Do NOT overwrite existing content — append or merge new keys.

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

---

After Step 2d, load `onboarding-phase1b-intro-language.md` to continue with the entity resolution introduction and programming language selection.
