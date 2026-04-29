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

**If the SDK is found and version is V4.0+:**

Tell the user: "Senzing SDK is already installed (version [X]). No need to reinstall — skipping straight to configuration verification."

- Skip Steps 2 and 3 entirely
- Jump to Step 4 (verify installation) to confirm it works with the chosen language
- If Step 4 passes, jump to Step 5 (license) then Step 7 (database) — only configure what's not already configured
- Mark Module 2 as complete once verification passes

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

Follow the platform-specific instructions from `sdk_guide`. The typical flow:

1. Add the Senzing package repository
2. Install the Senzing SDK package
3. Accept the EULA
4. Install the language-specific SDK bindings (e.g., `pip install senzing` for Python, or the equivalent for your chosen language)

**Before recommending any approach**, call `search_docs` with `category='anti_patterns'` to check for known pitfalls on the user's platform.

**TypeScript/Node.js warning:** The TypeScript SDK (`sz-napi`) may require building from source if prebuilt binaries are not available for the user's platform. This involves installing the Rust toolchain, cloning `sz-rust-sdk` and `sz-rust-sdk-configtool` as Cargo dependencies, and building the native addon with `napi-rs`. Warn the user upfront: "The TypeScript SDK setup is more involved than other languages — it may require building native bindings from source, which needs the Rust toolchain. If you'd prefer a faster setup, Java or C# typically have simpler install paths." If they proceed with TypeScript, guide them through the full build sequence in one go rather than letting them discover steps through trial and error.

**🚨 NEVER modify the user's global shell configuration** (`~/.zshrc`, `~/.bashrc`, `~/.profile`, etc.) to set Senzing environment variables. Instead, create a project-local environment script at `scripts/senzing-env.sh` (or `.bat` for Windows) that sets `SENZING_ROOT`, library paths, and any other Senzing-specific variables. The agent should source this script before running bootcamp tasks. This keeps the bootcamp self-contained and avoids side effects on the user's system.

**Checkpoint:** Write step 3 to `config/bootcamp_progress.json`.

## Step 4: Verify Installation

Generate a verification script in the bootcamper's chosen language using `generate_scaffold(language='<chosen_language>', workflow='initialize', version='current')`. The script should initialize the Senzing engine and print the version to confirm the SDK is working.

If verification fails, use `explain_error_code` for any SENZ error codes and `search_docs` for troubleshooting.

**Checkpoint:** Write step 4 to `config/bootcamp_progress.json`.

## Step 5: Configure License

Senzing checks for licenses in this order: project-local `licenses/g2.lic` → `SENZING_LICENSE_PATH` env var → system CONFIGPATH → built-in evaluation (500 records).

Check all three locations. Then always present the following license information as content:

**If a license was found**, tell the bootcamper where it was found and what it means (e.g., "Found a license at `licenses/g2.lic`" or "Found a license via `SENZING_LICENSE_PATH`").

**If no license was found**, tell the bootcamper that no license file was detected in any of the checked locations.

**Regardless of the check results**, always present these license options as informational content:

- **Evaluation license:** The SDK works with a built-in evaluation license limited to 500 records. No license file is needed — the SDK uses this automatically when no custom license is present.
- **Custom license:** To use a custom license, place a license file at `licenses/g2.lic` or decode a BASE64 key to that location (see command below). The bootcamper may already have a license file or BASE64 key from Senzing.
- **License acquisition:** To obtain an evaluation license, contact support@senzing.com (typically 1-2 days, 30-90 day validity). For a production license, contact sales@senzing.com. See `licenses/README.md` for details.

Present this information and stop — the `ask-bootcamper` hook will generate the contextual closing question about the bootcamper's license choice.

**🚨 NEVER ask the user to paste a license key into chat.** Direct them to decode to `licenses/g2.lic`:

```bash
echo 'YOUR_BASE64_KEY' | base64 --decode > licenses/g2.lic
```

When a project-local license exists, add `LICENSEFILE` to the engine config PIPELINE section:

```json
"PIPELINE": { "LICENSEFILE": "licenses/g2.lic" }
```

Record in `config/bootcamp_preferences.yaml`: `license: custom` or `license: evaluation`.

For license acquisition: evaluation → support@senzing.com (1-2 days, 30-90 day validity); production → sales@senzing.com. See `licenses/README.md` for details.

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

**Checkpoint:** Write step 8 to `config/bootcamp_progress.json`.

## Step 9: Test Database Connection

> **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='initialize', version='current')`
> to get the current V4 initialization and connection test pattern.

Use the MCP-generated initialization code to verify the database connection works.

**Checkpoint:** Write step 9 to `config/bootcamp_progress.json`.

## Success Criteria

- ✅ Senzing SDK installed natively
- ✅ SDK imports/references work in the chosen language
- ✅ Engine initializes without errors
- ✅ Database connection works
- ✅ Project directory structure created

## Transition

Once the SDK is installed and verified, proceed to:

- **Module 3** (Quick Demo) — see the SDK in action with sample data
- **Module 1** (Business Problem) — start working with your own data

## Troubleshooting

- Installation fails? Use `explain_error_code` for SENZ errors
- Platform not supported? Use `search_docs` for alternative installation methods
- Database errors? Check `docs/policies/FILE_STORAGE_POLICY.md` for path requirements
- Permission issues? Ensure you have admin/sudo access for installation
- Missing dependencies? Run `python senzing-bootcamp/scripts/preflight.py`

## Agent Behavior

- Always check for existing installation first — if SDK is present and V4.0+, do NOT reinstall. Skip to verification.
- Do NOT offer alternatives — install the SDK natively
- Use `sdk_guide` MCP tool for current platform-specific instructions
- Use `search_docs` with `category='anti_patterns'` before recommending approaches
- **NEVER construct engine configuration JSON manually** — always use the exact JSON from `sdk_guide(topic='configure')`. Do not guess CONFIGPATH, RESOURCEPATH, or SUPPORTPATH.
- Recommend SQLite for evaluation, PostgreSQL for production
- Always use `database/G2C.db` for SQLite (never `/tmp/sqlite`)
- Verify installation before proceeding to Module 3
