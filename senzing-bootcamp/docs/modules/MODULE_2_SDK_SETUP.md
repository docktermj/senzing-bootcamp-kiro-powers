```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀🚀🚀  MODULE 2: SET UP SDK  🚀🚀🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

# Module 2: Set Up SDK

> **Agent workflow:** The agent follows `steering/module-02-sdk-setup.md` for this module's step-by-step workflow.

## Overview

Module 2 installs and configures the Senzing SDK natively on your machine. Once the SDK is installed, all subsequent modules use it directly.

**Prerequisites:** None
**Output:** Installed SDK, configured database, verified installation

## Learning Objectives

By the end of this module, you will:

- Install the Senzing SDK on your platform
- Configure a database (SQLite or PostgreSQL)
- Verify the installation works
- Create the project directory structure

## What You'll Do

1. Check if Senzing is already installed
2. Install Senzing SDK natively
3. Choose and configure database
4. Create project directory structure
5. Test the installation

## Installation Check

Before installing, the agent checks if the Senzing SDK is already present and working. There is no reason to re-install an existing SDK.

The agent will run a language-appropriate verification command for your chosen language. If the SDK is found and the version is V4.0+, installation is skipped entirely — the agent jumps straight to verifying the configuration and database setup.

If Senzing is found:

- Version V4.0+ → Skip installation, verify configuration only
- Version below V4.0 → Upgrade required
- Not found → Full installation

## Senzing License Requirements

Here's what you need to know about licensing before you start loading data.

The Senzing SDK includes a **built-in evaluation license limited to 500 records**. No license file is needed — the SDK uses this automatically when no custom license is present. This is enough for the bootcamp's demo modules and small datasets.

If you load more than 500 records, the SDK returns a **SENZ9000** error at record 501. For larger datasets, you need a custom license file placed at `licenses/g2.lic`.

> **Note:** The agent asks about your license during the bootcamp setup (before Module 2). If you've already configured your license, you can skip this section.

### Obtaining a License

**Evaluation License (Recommended for Bootcamp):**

- Email: <support@senzing.com>
- Mention: "Requesting evaluation license for Senzing Bootcamp"
- Response time: 1-2 business days
- Valid for 30-90 days

**Production License:**

- Email: <sales@senzing.com>
- Pricing based on data source records (DSRs)

### Installing a License File

If you have a `.lic` file, copy it into the project:

```bash
# Linux / macOS
cp /path/to/downloaded/g2.lic licenses/g2.lic
chmod 644 licenses/g2.lic
```

```powershell
# Windows (PowerShell)
Copy-Item C:\path\to\downloaded\g2.lic licenses\g2.lic
```

### Decoding a Base64-Encoded License

If you received a Base64-encoded license string (for example, pasted into an email body or copied from a licensing portal), decode it to a binary file before the SDK can use it.

Replace `<BASE64_STRING>` with the string you received:

```bash
# Linux / macOS
echo '<BASE64_STRING>' | base64 --decode > licenses/g2.lic
```

```powershell
# Windows (PowerShell)
[System.Convert]::FromBase64String('<BASE64_STRING>') |
  Set-Content -Path licenses\g2.lic -AsByteStream
```

Verify the decoded file is binary (not text):

```bash
file licenses/g2.lic
```

The output should show `data` or `binary`. If it shows `ASCII text`, the Base64 string may have been copied incorrectly.

### License Check Order

Senzing checks for licenses in this order: project-local `licenses/g2.lic` → `SENZING_LICENSE_PATH` env var → system `/etc/opt/senzing/g2.lic` → built-in evaluation (500 records).

See `licenses/README.md` for complete licensing information.

## Platform Installation

> **Agent instruction:** Do not use the example commands below. Always retrieve
> current, platform-specific installation commands from the MCP server:
> `sdk_guide(topic='install', platform='<user_platform>', version='current')`.
> Before recommending any approach, check for anti-patterns:
> `search_docs(query="installation", category="anti_patterns", version="current")`.
> The commands below are illustrative only and may be outdated.

Use the `sdk_guide` MCP tool with the user's platform for current installation commands.

Supported platforms:

- `linux_apt` — Ubuntu/Debian
- `linux_yum` — RHEL/CentOS/Fedora
- `macos_arm` — macOS (Apple Silicon)
- `windows` — Windows

After system installation, verify the SDK is accessible from your chosen language. The agent will run the correct verification command for your language.

## Database Configuration

> **Agent instruction:** Do not use the configuration JSON or commands below verbatim.
> Always retrieve current database configuration from the MCP server:
> `sdk_guide(topic='configure', platform='<user_platform>', language='<chosen_language>', version='current')`.
> The MCP server provides correct paths (CONFIGPATH, RESOURCEPATH, SUPPORTPATH) for
> each platform and catches common anti-patterns like wrong paths or missing schema creation.

### SQLite (Recommended for Bootcamp)

No setup required — SQLite is built in and file-based.

```bash
mkdir -p database
```

Use `sdk_guide(topic='configure')` for the correct engine configuration JSON for your platform.

### PostgreSQL (Production)

For production workloads, use `sdk_guide(topic='configure')` with your platform and database details. The MCP server will provide the correct connection string format and any required schema setup steps.

## Verify Installation

> **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='initialize', version='current')`
> to get the current V4 initialization pattern. The code below uses a legacy pattern that
> may not match the current SDK version.

Run a verification script generated by the MCP server to confirm the SDK is working. The `generate_scaffold` tool with `workflow='initialize'` provides the correct factory-based initialization pattern for V4.

## Success Criteria

- ✅ Senzing SDK installed natively
- ✅ SDK is accessible from the chosen programming language
- ✅ Database configured and tested
- ✅ Project directory structure created
- ✅ Verification script passes

## Common Issues

> **Agent instruction:** For any error codes encountered during setup, use
> `explain_error_code(error_code="<code>", version="current")` for diagnosis.
> Use `search_docs(query="<issue>", category="troubleshooting", version="current")`
> for general troubleshooting guidance.

- **Permission denied:** Use `sudo` for system installation
- **Database connection fails:** Verify database path exists (`mkdir -p database`)
- **Import/reference error:** Verify SDK is installed for your chosen language, check version requirements via MCP `search_docs`
- **Configuration not found:** Use `sdk_guide` to get correct paths for your platform

## Next Steps

- **Module 3** (System Verification) — Verify the full setup end-to-end using the Senzing TruthSet
- **Module 1** (Business Problem) — Start working with your own data

## Related Documentation

- `POWER.md` — Bootcamp overview
- `steering/module-02-sdk-setup.md` — Module 2 workflow
- `licenses/README.md` — Licensing details
- `docs/policies/FILE_STORAGE_POLICY.md` — Database path policy (see Database Files section)
- Use `sdk_guide` MCP tool for platform-specific instructions
- Use `find_examples(query="initialization")` for real-world SDK initialization patterns from GitHub
