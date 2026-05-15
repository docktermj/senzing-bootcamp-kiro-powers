---
inclusion: manual
---

# Module 2: SDK Installation and Configuration

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_2_SDK_SETUP.md`.

Install and configure the Senzing SDK natively on your machine. This is the first step of the bootcamp — once the SDK is installed, all subsequent modules use it directly.

**Before/After:** You have a project directory but no Senzing SDK. After this module, the SDK is installed, configured, and verified — ready to load data and resolve entities.

**Prerequisites:** None (this is the first module)

**Language:** Use the bootcamper's chosen programming language from the language selection step in agent-instructions. All code generation, scaffold calls, and examples in this module must use that language.

## Step 1: Check for Existing Installation — MUST DO FIRST

**Before doing anything else in this module**, check if the Senzing SDK is already installed and working. There is no reason to re-install it.

Run a language-appropriate import/version check for the bootcamper's chosen language. Use `sdk_guide(topic='install', platform='<user_platform>', language='<chosen_language>', version='current')` to get the correct verification command.

**Filesystem fallback — if the import check fails:** When the language import check does not succeed (e.g., `PYTHONPATH` is not configured or the package manager query finds nothing), check for the following sentinel files on the filesystem before concluding the SDK is not installed:

- `/opt/senzing/er/lib/libSz.so` (native shared library)
- `/opt/senzing/er/szBuildVersion.json` (build version metadata)

Both sentinel files must be present to conclude the SDK is installed via filesystem detection. If both files exist, read the version from `/opt/senzing/er/szBuildVersion.json`, report the SDK as installed, Skip Steps 2 and 3 entirely, and proceed to Step 4 verification. If only one file or neither is found, proceed with the "SDK not found" path (Step 2).

**If the SDK is found and version is V4.0+:**

Tell the user: "Senzing SDK is already installed (version [X]). No need to reinstall — skipping straight to configuration verification."

- Skip Steps 2 and 3 entirely
- Jump to Step 4 (verify installation) to confirm it works with the chosen language
- If Step 4 passes, proceed to Step 5 (Configure License) — this step is MANDATORY and must always be executed regardless of SDK installation status. After Step 5, proceed to Step 7 (database).
- Mark Module 2 as complete once verification passes

> **Required Stops:** The following steps are NEVER skipped, even when the SDK is already installed:
>
> - **Step 4** (Verify Installation) — confirms the SDK works with the chosen language
> - **Step 5** (Configure License) — license configuration is always required

**If the SDK is found but version is incompatible (<V4.0):**

Tell the user: "Senzing SDK found but it's version [X] — the bootcamp requires V4.0+. We'll need to upgrade."

- Proceed with Steps 2-3 for upgrade

**If the SDK is NOT found:**

Tell the user: "Senzing SDK is not installed yet. Let's set it up — this is a one-time process."

- Proceed with Step 2

**Checkpoint:** Write step 1 to `config/bootcamp_progress.json`.

## Step 2: Determine Platform

Ask: "What platform are you using? Linux, macOS, or Windows?"

Use `sdk_guide` with `topic='install'` and the user's platform to get current installation commands. Pass the bootcamper's chosen language as the `language` parameter. The MCP server always has the latest instructions.

**Platform options for `sdk_guide`:**

- `platform='linux_apt'` — Ubuntu/Debian
- `platform='linux_yum'` — RHEL/CentOS/Fedora
- `platform='macos_arm'` — macOS (Apple Silicon)
- `platform='windows'` — Windows

**Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.

## Step 3: Install Senzing SDK

Follow the platform-specific instructions from `sdk_guide`. The installation has three phases:

**Before recommending any approach**, call `search_docs` with `category='anti_patterns'` to check for known pitfalls on the user's platform.

**Phase 1 — Install the SDK package (execute without stopping):**

1. Add the Senzing package repository
2. Install the Senzing SDK package

**Phase 2 — EULA acceptance (requires bootcamper input):**

The Senzing SDK requires EULA acceptance before use. Present the EULA question:

👉 "Do you accept the Senzing End User License Agreement (EULA)? You can review it at <https://senzing.com/end-user-license-agreement/>. Please respond yes or no."

**STOP and wait for the bootcamper's response.** Do not proceed until the bootcamper answers.

Once the bootcamper responds, act on their answer:

- **If the bootcamper accepts the EULA:** Proceed to Phase 3 below to install language-specific SDK bindings.
- **If the bootcamper declines the EULA:** Stop the installation process. Explain to the bootcamper: "The Senzing SDK cannot be used without EULA acceptance. The remaining installation steps and subsequent bootcamp modules require the SDK." Do not install language bindings and do not write the checkpoint. Stop here.

**Phase 3 — Install language bindings (only after EULA acceptance):**

3. Install the language-specific SDK bindings (e.g., `pip install senzing` for Python, or the equivalent for your chosen language)

**TypeScript/Node.js warning:** The TypeScript SDK (`sz-napi`) may require building from source if prebuilt binaries are not available for the user's platform. This involves installing the Rust toolchain, cloning `sz-rust-sdk` and `sz-rust-sdk-configtool` as Cargo dependencies, and building the native addon with `napi-rs`. Warn the user upfront: "The TypeScript SDK setup is more involved than other languages — it may require building native bindings from source, which needs the Rust toolchain. If you'd prefer a faster setup, Java or C# typically have simpler install paths." If they proceed with TypeScript, guide them through the full build sequence in one go rather than letting them discover steps through trial and error.

**Windows-specific:** Building the TypeScript SDK from source on Windows requires Visual Studio Build Tools (not the full IDE) with the "Desktop development with C++" workload. Install via `winget install Microsoft.VisualStudio.2022.BuildTools` or download from visualstudio.microsoft.com. The Rust toolchain installer (`rustup-init.exe`) will detect the build tools automatically.

**🚨 NEVER modify the user's global shell configuration** (`~/.zshrc`, `~/.bashrc`, `~/.profile`, etc.) to set Senzing environment variables. Instead, create a project-local environment script at `scripts/senzing-env.sh` (or `.bat` for Windows) that sets `SENZING_ROOT`, library paths, and any other Senzing-specific variables. The agent should source this script before running bootcamp tasks. This keeps the bootcamp self-contained and avoids side effects on the user's system.

**Checkpoint:** Write step 3 to `config/bootcamp_progress.json`.

## Step 4: Verify Installation

Generate a verification script in the bootcamper's chosen language using `generate_scaffold(language='<chosen_language>', workflow='initialize', version='current')`. The script should initialize the Senzing engine and print the version to confirm the SDK is working.

If verification fails, use `explain_error_code` for any SENZ error codes and `search_docs` for troubleshooting.

**Checkpoint:** Write step 4 to `config/bootcamp_progress.json`.

## Step 5: Configure License

⛔ MANDATORY GATE — Never skip this step, even if the SDK is already installed.

> **License check order:** Senzing checks for licenses in this order: project-local `licenses/g2.lic` → `SENZING_LICENSE_PATH` env var → system CONFIGPATH → built-in evaluation (500 records).

### 5a. Explain the built-in evaluation license

Before checking for license files or asking the bootcamper anything, proactively present this information:

"Here's what you need to know about Senzing licensing before we continue. Senzing includes a **built-in evaluation license limited to 500 records**. No license file is needed — the SDK uses this automatically when no custom license is present. This is enough for the bootcamp's demo modules and small datasets.

If you load more than 500 records, the SDK returns a **SENZ9000 error at record 501**. For larger datasets, you need a custom license file placed at `licenses/g2.lic`."

### 5b. Ask about the bootcamper's license situation

👉 Ask: **"Do you have a Senzing license file (.lic) or a Base64-encoded license key?"**

**STOP and wait for the bootcamper's response.** Do not proceed until the bootcamper answers.

### 5c. Handle the response

**IF the bootcamper has a Base64-encoded license string:**

**🚨 NEVER ask the user to paste a license key into chat.** Direct them to decode the string to `licenses/g2.lic` using the command for their platform:

**Linux / macOS:**

```bash
echo '<BASE64_STRING>' | base64 --decode > licenses/g2.lic
```

**Windows (PowerShell):**

```powershell
[System.Convert]::FromBase64String('<BASE64_STRING>') |
  Set-Content -Path licenses\g2.lic -AsByteStream
```

After decoding, verify the file is binary (not leftover text):

```bash
file licenses/g2.lic
```

The output should indicate a binary/data file, not ASCII text. If it shows text, the Base64 string may have been copied incorrectly.

Confirm: "License decoded and saved to `licenses/g2.lic`."

**IF the bootcamper has a `.lic` file directly:**

Guide them to copy it into the project:

```bash
cp /path/to/g2.lic licenses/g2.lic
```

Confirm: "License file placed at `licenses/g2.lic`."

**IF the bootcamper has no license:**

Confirm: "No problem — the built-in 500-record evaluation license is active automatically. That's enough for the bootcamp demo modules."

Mention: "If you need a free evaluation license for larger datasets later, contact <support@senzing.com> (typically 1–2 business days, 30–90 day validity). For production licenses, contact <sales@senzing.com>. See `licenses/README.md` for details."

Record in `config/bootcamp_preferences.yaml`: `license: evaluation`.

### 5d. Configure LICENSEFILE in engine config

When a project-local license exists at `licenses/g2.lic`, add `LICENSEFILE` to the engine config PIPELINE section:

```json
"PIPELINE": { "LICENSEFILE": "licenses/g2.lic" }
```

Record in `config/bootcamp_preferences.yaml`: `license: custom`.

If no custom license was placed, skip this — the SDK uses the built-in evaluation license automatically.

**Checkpoint:** Write step 5 to `config/bootcamp_progress.json`.

## Step 6: Create Project Directory Structure

Follow the directory creation commands from the agent-instructions steering file. This creates the organized project layout (`data/`, `database/`, `src/`, `docs/`, etc.) that all subsequent modules use.

After creation, inform the user: "I've set up the project directory structure. All files will be organized properly throughout the bootcamp."

**Checkpoint:** Write step 6 to `config/bootcamp_progress.json`.

## Step 7: Configure Database

Ask: "Which database would you like to use? SQLite is recommended for learning and evaluation. PostgreSQL is better for production."

**For SQLite** (recommended for bootcamp):

- Create the database directory: `mkdir -p database` (Linux/macOS) or `New-Item -ItemType Directory -Force -Path database` (PowerShell)
- Database path: `database/G2C.db`
- No additional setup needed — SQLite is built in
- **IMPORTANT:** Never use `/tmp/` or in-memory databases. If `generate_scaffold` or `ExampleEnvironment` defaults to `/tmp/`, override the path to `database/G2C.db`.

**For PostgreSQL** (production):

- User needs PostgreSQL installed and running
- Create a database for Senzing
- Use `sdk_guide` with `topic='configure'` for PostgreSQL setup

**Checkpoint:** Write step 7 to `config/bootcamp_progress.json`.

## Step 8: Create Engine Configuration

**🚨 NEVER construct `SENZING_ENGINE_CONFIGURATION_JSON` manually.** Always use the exact JSON returned by `sdk_guide(topic='configure', platform='<user_platform>', language='<chosen_language>', version='current')`. Do not guess paths for CONFIGPATH, RESOURCEPATH, or SUPPORTPATH based on directory patterns — the correct paths vary by platform and installation method, and guessing causes engine initialization failures (e.g., SENZ2027 when SUPPORTPATH is wrong).

Use `sdk_guide` with `topic='configure'` to generate the correct engine configuration JSON for the user's platform and database choice. Save the MCP-returned JSON directly to `config/engine_config.json` — do not modify the paths.

**On Windows — verify SUPPORTPATH exists before saving the configuration:**

After receiving the MCP-returned JSON, check that the SUPPORTPATH directory actually exists on the filesystem. This is a targeted path verification, not manual JSON construction — the MCP-returned JSON remains the starting point.

1. Extract the SUPPORTPATH value from the MCP-returned configuration JSON
2. Use `Test-Path` in PowerShell to confirm the SUPPORTPATH directory exists:

   ```powershell
   Test-Path -Path "$SENZING_DIR\data"
   ```

3. If `$SENZING_DIR\data` does not exist, check `$SENZING_DIR\..\data` (one level up from the `er` directory):

   ```powershell
   Test-Path -Path "$SENZING_DIR\..\data"
   ```

4. If the parent-level path exists, update SUPPORTPATH in the configuration JSON to use `$SENZING_DIR\..\data` before saving to `config/engine_config.json`
5. If neither path exists, report the error clearly to the bootcamper: "SUPPORTPATH directory not found at either `$SENZING_DIR\data` or `$SENZING_DIR\..\data`. Please verify your Senzing installation."

> **Why the Scoop layout differs:** The unofficial Windows Scoop package places `SENZING_DIR` at the `er` subdirectory within the Scoop app folder (e.g., `C:\Users\<user>\scoop\apps\senzing\current\er`). The `data` directory containing `g2SifterRules.ibm` and other GNR support files is at the Scoop app version root — one level above `er` — rather than inside it. This is why the fallback to `$SENZING_DIR\..\data` is needed for Scoop installs.

This SUPPORTPATH verification applies to Windows only. On Linux and macOS, use the MCP-returned paths without modification.

**Checkpoint:** Write step 8 to `config/bootcamp_progress.json`.

## Step 9: Test Database Connection

> **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='initialize', version='current')`
> to get the current V4 initialization and connection test pattern.

Use the MCP-generated initialization code to verify the database connection works.

**Checkpoint:** Write step 9 to `config/bootcamp_progress.json`.

**Success indicator**: ✅ SDK installed + DB configured + test passes + engine initializes and connects without errors

## Success Criteria

- ✅ Senzing SDK installed natively
- ✅ SDK imports/references work in the chosen language
- ✅ Engine initializes without errors
- ✅ Database connection works
- ✅ Project directory structure created

## Transition

Once the SDK is installed and verified, proceed to:

- **Module 3** (System Verification) — verify the full setup end-to-end using the Senzing TruthSet
- **Module 1** (Business Problem) — start working with your own data

## Troubleshooting

- Installation fails? Use `explain_error_code` for SENZ errors
- Platform not supported? Use `search_docs` for alternative installation methods
- Database errors? Check `docs/policies/FILE_STORAGE_POLICY.md` for path requirements
- Permission issues? Ensure you have admin/sudo access for installation
- Missing dependencies? Run `python3 senzing-bootcamp/scripts/preflight.py`

## Error Handling

When the bootcamper encounters an error during this module:

1. **Check for SENZ error code** — if the error message contains a code matching `SENZ` followed by digits (e.g., `SENZ2027`):
   - Call `explain_error_code(error_code="<code>", version="current")`
   - Present the explanation and recommended fix to the bootcamper
   - If `explain_error_code` returns no result, continue to step 2
2. **Load `common-pitfalls.md`** — navigate to this module's section and present only the matching pitfall and fix
3. **Check cross-module resources** — if no match in the module section, check the Troubleshooting by Symptom table and General Pitfalls section

## Agent Behavior

- Always check for existing installation first — if SDK is present and V4.0+, do NOT reinstall. Skip to verification.
- Do NOT offer alternatives — install the SDK natively
- Use `sdk_guide` MCP tool for current platform-specific instructions
- Use `search_docs` with `category='anti_patterns'` before recommending approaches
- **NEVER construct engine configuration JSON manually** — always use the exact JSON from `sdk_guide(topic='configure')`. Do not guess CONFIGPATH, RESOURCEPATH, or SUPPORTPATH.
- Recommend SQLite for evaluation, PostgreSQL for production
- Always use `database/G2C.db` for SQLite (never `/tmp/sqlite`)
- Verify installation before proceeding to Module 3
