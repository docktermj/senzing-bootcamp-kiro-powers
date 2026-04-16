---
inclusion: manual
---

# Module 0: SDK Installation and Configuration

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_0_SDK_SETUP.md`.

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
- Mark Module 0 as complete once verification passes

**If the SDK is found but version is incompatible (<V4.0):**

Tell the user: "Senzing SDK found but it's version [X] — the bootcamp requires V4.0+. We'll need to upgrade."

- Proceed with Steps 2-3 for upgrade

**If the SDK is NOT found:**

Tell the user: "Senzing SDK is not installed yet. Let's set it up — this is a one-time process."

- Proceed with Step 2

## Step 2: Determine Platform

Ask: "What platform are you using? Linux, macOS, or Windows?"

WAIT for response before proceeding.

Use `sdk_guide` with `topic='install'` and the user's platform to get current installation commands. Pass the bootcamper's chosen language as the `language` parameter. The MCP server always has the latest instructions.

**Platform options for `sdk_guide`:**

- `platform='linux_apt'` — Ubuntu/Debian
- `platform='linux_yum'` — RHEL/CentOS/Fedora
- `platform='macos_arm'` — macOS (Apple Silicon)
- `platform='windows'` — Windows

## Step 3: Install Senzing SDK

Follow the platform-specific instructions from `sdk_guide`. The typical flow:

1. Add the Senzing package repository
2. Install the Senzing SDK package
3. Accept the EULA
4. Install the language-specific SDK bindings (e.g., `pip install senzing` for Python, or the equivalent for your chosen language)

**Before recommending any approach**, call `search_docs` with `category='anti_patterns'` to check for known pitfalls on the user's platform.

**TypeScript/Node.js warning:** The TypeScript SDK (`sz-napi`) may require building from source if prebuilt binaries are not available for the user's platform. This involves installing the Rust toolchain, cloning `sz-rust-sdk` and `sz-rust-sdk-configtool` as Cargo dependencies, and building the native addon with `napi-rs`. Warn the user upfront: "The TypeScript SDK setup is more involved than other languages — it may require building native bindings from source, which needs the Rust toolchain. If you'd prefer a faster setup, Java or C# typically have simpler install paths." If they proceed with TypeScript, guide them through the full build sequence in one go rather than letting them discover steps through trial and error.

**🚨 NEVER modify the user's global shell configuration** (`~/.zshrc`, `~/.bashrc`, `~/.profile`, etc.) to set Senzing environment variables. Instead, create a project-local environment script at `scripts/senzing-env.sh` (or `.bat` for Windows) that sets `SENZING_ROOT`, library paths, and any other Senzing-specific variables. The agent should source this script before running bootcamp tasks. This keeps the bootcamp self-contained and avoids side effects on the user's system.

## Step 4: Verify Installation

Generate a verification script in the bootcamper's chosen language using `generate_scaffold(language='<chosen_language>', workflow='initialize', version='current')`. The script should initialize the Senzing engine and print the version to confirm the SDK is working.

If verification fails, use `explain_error_code` for any SENZ error codes and `search_docs` for troubleshooting.

## Step 5: Configure License (Optional)

Ask: "Do you have a Senzing license file (`g2.lic`) or a BASE64 license key? If not, no worries — the SDK works with its built-in evaluation limits (500 records)."

WAIT for response.

**🚨 NEVER ask the user to paste a license key or BASE64 string into the chat.** Chat prompt history may be retained, and license keys are sensitive. Always direct the user to save the key to a file instead.

**If they have a license key (BASE64 string):**

Tell them: "Please save your license key to the file `licenses/g2.lic` — don't paste it into the chat, since chat history may be kept. The license file is binary, so you'll need to decode the BASE64 string first:"

```bash
# Linux / macOS
echo 'YOUR_BASE64_KEY' | base64 --decode > licenses/g2.lic
```

```powershell
# Windows (PowerShell)
[IO.File]::WriteAllBytes("licenses\g2.lic", [Convert]::FromBase64String("YOUR_BASE64_KEY"))
```

- Verify the file exists after they confirm
- Record in `config/bootcamp_preferences.yaml`:

  ```yaml
  license: custom
  license_path: licenses/g2.lic
  ```

**If they have a license file:**

- Ask them to place it at `licenses/g2.lic`
- Verify the file exists
- Inform them: "Your license is configured. Senzing will use it automatically."
- Record in `config/bootcamp_preferences.yaml`:

  ```yaml
  license: custom
  license_path: licenses/g2.lic
  ```

**If they don't have a license:**

- Inform them: "No problem. The SDK includes built-in evaluation limits (500 records) that are fine for the bootcamp. If you'd like a full evaluation license later, you can email <support@senzing.com>."
- Record in `config/bootcamp_preferences.yaml`:

  ```yaml
  license: evaluation
  license_path: null
  ```

**If they're unsure:** Evaluation (built-in) works out of the box with a 500-record limit. A custom license removes limits. They can always add one later by saving it to `licenses/g2.lic`.

## Step 6: Create Project Directory Structure

Follow the directory creation commands from the agent-instructions steering file. This creates the organized project layout (`data/`, `database/`, `src/`, `docs/`, etc.) that all subsequent modules use.

After creation, inform the user: "I've set up the project directory structure. All files will be organized properly throughout the bootcamp."

## Step 7: Configure Database

Ask: "Which database would you like to use? SQLite is recommended for learning and evaluation. PostgreSQL is better for production."

WAIT for response.

**For SQLite** (recommended for bootcamp):

- Create the database directory: `mkdir -p database` (Linux/macOS) or `New-Item -ItemType Directory -Force -Path database` (PowerShell)
- Database path: `database/G2C.db`
- No additional setup needed — SQLite is built in
- **IMPORTANT:** Never use `/tmp/` or in-memory databases. If `generate_scaffold` or `ExampleEnvironment` defaults to `/tmp/`, override the path to `database/G2C.db`.

**For PostgreSQL** (production):

- User needs PostgreSQL installed and running
- Create a database for Senzing
- Use `sdk_guide` with `topic='configure'` for PostgreSQL setup

## Step 8: Create Engine Configuration

> **Agent instruction:** Do not use the example JSON below. Use
> `sdk_guide(topic='configure', platform='<user_platform>', language='<chosen_language>', version='current')`
> to get the correct engine configuration for the user's platform. The MCP server provides
> correct paths and catches anti-patterns.

Use `sdk_guide` with `topic='configure'` to generate the correct engine configuration JSON for the user's platform and database choice. Save it to `config/engine_config.json`.

## Step 9: Test Database Connection

> **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='initialize', version='current')`
> to get the current V4 initialization and connection test pattern.

Use the MCP-generated initialization code to verify the database connection works.

## Success Criteria

- ✅ Senzing SDK installed natively
- ✅ SDK imports/references work in the chosen language
- ✅ Engine initializes without errors
- ✅ Database connection works
- ✅ Project directory structure created

## Transition

Once the SDK is installed and verified, proceed to:

- **Module 1** (Quick Demo) — see the SDK in action with sample data
- **Module 2** (Business Problem) — start working with your own data

## Troubleshooting

- Installation fails? Use `explain_error_code` for SENZ errors
- Platform not supported? Use `search_docs` for alternative installation methods
- Database errors? Check `docs/policies/FILE_STORAGE_POLICY.md` for path requirements
- Permission issues? Ensure you have admin/sudo access for installation
- Missing dependencies? Run `python scripts/check_prerequisites.py`

## Agent Behavior

- Always check for existing installation first — if SDK is present and V4.0+, do NOT reinstall. Skip to verification.
- Do NOT offer alternatives — install the SDK natively
- Use `sdk_guide` MCP tool for current platform-specific instructions
- Use `search_docs` with `category='anti_patterns'` before recommending approaches
- Recommend SQLite for evaluation, PostgreSQL for production
- Always use `database/G2C.db` for SQLite (never `/tmp/sqlite`)
- Verify installation before proceeding to Module 1
