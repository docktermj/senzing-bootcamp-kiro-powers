---
inclusion: manual
---

# Onboarding Flow

This steering file contains the full onboarding sequence: directory creation, language selection, prerequisite checks, path selection, and validation gates. Load this when starting a fresh bootcamp or when the user wants to begin.

## Create Directory Structure

1. Check if project directory structure exists (`src/`, `data/`, `docs/`)
2. If it doesn't exist, load `project-structure.md` and execute the creation commands
3. Only then proceed with any other activity

**Trigger points** — create structure at any of these:

- User says "start the bootcamp" or mentions any module number (0-12)
- User selects any path (A, B, C, D) or asks to begin
- Any indication they want to start using the power

If directory creation fails, report the error, provide commands for manual execution, and do not proceed until the structure exists.

After creating the directory structure (or confirming it exists), inform the user: "If you encounter any issues or have suggestions during the bootcamp, just say 'bootcamp feedback' and I'll help you document them for the bootcamp author."

Then offer to install hooks: "I can also install some automated quality checks (hooks) that help catch issues as we work. Would you like me to set those up? It takes about a minute." If yes, follow the Hooks Management section in `agent-instructions.md`. If no, proceed — hooks can always be installed later with `python scripts/install_hooks.py`.

## Programming Language Selection

After directory structure is confirmed and before the prerequisite check, ask the bootcamper which programming language they want to use for generated code.

1. **Query the Senzing MCP server** for supported languages by calling `generate_scaffold` with `workflow='initialize'` and `version='current'` for each candidate language, or by calling `get_capabilities` and reviewing the language list in the response. The MCP server is the authoritative source for which languages are available.

2. **Present the supported languages** to the bootcamper. As of the last check, the Senzing SDK supports:
   - Python (Linux only — not natively supported on macOS/Windows)
   - Java
   - C#
   - Rust
   - TypeScript / Node.js

   However, always confirm with the MCP server — do not rely on this list alone.

3. **Ask the bootcamper:** "Which programming language would you like to use for the bootcamp? The Senzing SDK supports: [list from MCP]. All generated code, templates, and examples will use your chosen language."

4. **WAIT for their response** before proceeding.

5. **Remember the chosen language** for the entire bootcamp session. Use it in all subsequent calls to `generate_scaffold`, `sdk_guide`, `find_examples`, and any code generation throughout every module.

6. **Persist the choice** by writing it to `config/bootcamp_preferences.yaml`:

   ```yaml
   language: <chosen_language>
   path: null  # Set after path selection
   started_at: <ISO 8601 timestamp>
   ```

   If `config/bootcamp_preferences.yaml` already exists (from a previous session), read the language from it and confirm with the user: "Last time you chose [language]. Would you like to continue with that, or switch?"

7. **Platform compatibility note:** If the bootcamper chooses Python, inform them that the Senzing Python SDK is only supported on Linux. On macOS or Windows, they should either pick a different language or use Docker/WSL2.

8. **Code quality standards:** Apply language-appropriate coding standards:
   - Python → PEP-8 (see `docs/policies/CODE_QUALITY_STANDARDS.md`)
   - Java → Standard Java conventions (camelCase methods, PascalCase classes, Javadoc)
   - C# → .NET conventions (PascalCase methods and classes, XML doc comments)
   - Rust → Rust conventions (snake_case, rustfmt, clippy)
   - TypeScript → Standard TS conventions (camelCase, ESLint, JSDoc)

### `bootcamp_preferences.yaml` Schema

```yaml
language: <chosen_language>       # python, java, csharp, rust, typescript
path: <chosen_path>               # A, B, C, D (null until path is selected)
started_at: <ISO 8601 timestamp>  # When the bootcamp started
current_module: <number>          # Last module worked on
```

The `license` and `license_path` fields are added later during Module 0 (SDK Setup). The `cloud_provider` field is added at the Module 8→9 gate (e.g., `aws`, `azure`, `gcp`, `on-premises`, or `local`). When writing to this file, always read the existing content first and merge — never overwrite fields set by a previous action.

## Platform Prerequisite Check

After language selection is confirmed and before presenting path options, run a quick prerequisite check to surface missing dependencies up front.

**Detect the user's platform first** using a cross-platform approach:

```python
import platform
print(f"OS: {platform.system()} ({platform.machine()})")
```

Then adapt the checks based on the chosen language. Use `shutil.which()` in Python or equivalent cross-platform checks — do NOT use `command -v` or `uname -s` which are Unix-only.

**For Python:**

```python
import shutil, subprocess
py = shutil.which("python3") or shutil.which("python")
if py:
    subprocess.run([py, "--version"])
    subprocess.run([py, "-c", "import senzing; print('Senzing SDK:', senzing.__version__)"])
```

**For Java:**

```python
import shutil, subprocess
if shutil.which("java"):
    subprocess.run(["java", "--version"])
```

**For C#:**

```python
import shutil, subprocess
if shutil.which("dotnet"):
    subprocess.run(["dotnet", "--version"])
```

**For Rust:**

```python
import shutil, subprocess
if shutil.which("rustc"):
    subprocess.run(["rustc", "--version"])
    subprocess.run(["cargo", "--version"])
```

**For TypeScript / Node.js:**

```python
import shutil, subprocess
if shutil.which("node"):
    subprocess.run(["node", "--version"])
    subprocess.run(["npm", "--version"])
```

Present results as a checklist before path selection:

```text
Platform check:
  ✅ / ❌  [Language runtime/compiler]
  ✅ / ❌  Senzing SDK
  ✅ / ❌  Homebrew (macOS only)
```

- If everything passes → proceed to path selection normally.
- If anything is missing → tell the user exactly what needs to be installed manually before they can run code. Provide the install commands. Let them choose to install now or pick a path first (they can still do Module 2 — Business Problem — without the SDK).
- Do NOT discover missing dependencies one at a time during later modules. Surface them all here.

## Path Selection

Use lettered options (A/B/C/D) to avoid ambiguity with module numbers:

```text
A) Quick Demo — Module 1 (requires SDK from Module 0)
B) Fast Track — Modules 5-6 (for users with SGES-compliant data)
C) Complete Beginner — Modules 2-6, 8 (Module 0 inserted automatically before Module 6)
D) Full Production — All Modules 0-12
```

**Path A note:** Module 0 (SDK Setup) is required before Module 1 (Quick Demo). If Module 0 is not complete, insert it first: "To run the demo, we need the Senzing SDK installed. Let's do Module 0 first — it takes about 30-60 minutes as a one-time setup."

**Path C note:** Module 0 (SDK Setup) is required before Module 6 (Loading). When the user reaches Module 6 on Path C, check if Module 0 is complete. If not, insert it: "Before we can load data, we need to set up the Senzing SDK. Let's do Module 0 now — it takes about 30-60 minutes."

**Interpreting responses:**

- "A", "demo", "quick demo", "Module 1" → Start Module 1
- "B", "fast", "fast track" → Start Module 5
- "C", "complete", "beginner" → Start Module 2
- "D", "full", "production" → Start Module 0
- A bare number (1, 2, 3) → Ask for clarification: "Did you mean option [letter] or Module [number]?"

## Switching Paths Mid-Bootcamp

Users may want to change paths after starting. Handle this gracefully:

- **Upgrading** (e.g., A→C or C→D): All completed modules carry forward. Identify which modules the new path requires that haven't been done yet, and resume from the first missing one.
- **Downgrading** (e.g., D→C or C→A): All completed modules still count. The user simply stops at the new path's endpoint. No work is lost.
- **Switching** (e.g., A→B): Check which modules overlap. Completed modules carry forward; start the first module in the new path that hasn't been completed.

When a user asks to switch paths:

1. Read `config/bootcamp_progress.json` to see completed modules.
2. Show what the new path requires vs. what's already done.
3. Update `config/bootcamp_preferences.yaml` with the new path.
4. Resume from the first incomplete module in the new path.

## Changing Language Mid-Bootcamp

If a user wants to switch programming languages after generating code:

1. Update `config/bootcamp_preferences.yaml` with the new language.
2. **Previously generated code will not work** in the new language — it must be regenerated. Inform the user: "Switching languages means the code we've already generated (in `src/`) will need to be recreated in [new language]. Your data files, documentation, and configuration are unaffected."
3. For each module that produced code (Modules 1, 5, 6, 7, 8), regenerate using `generate_scaffold` with the new language.
4. **Do not mix languages** within the bootcamp project.

## Validation Gates

Before proceeding to next module, verify and update progress.

**Automated validation:** Run `python scripts/validate_module.py --module N` to check if module N's artifacts are in place. Use `python scripts/validate_module.py --next N` to check if the user is ready to start module N.

After each module's validation gate passes, update `config/bootcamp_progress.json`:

```json
{
  "current_module": 6,
  "language": "java",
  "path": "D",
  "modules_completed": [0, 1, 2, 3, 4, 5],
  "last_updated": "2026-04-01T14:30:00Z",
  "data_sources": ["CUSTOMERS_CRM", "CUSTOMERS_ECOMMERCE"],
  "database": "postgresql"
}
```

Also update `config/bootcamp_preferences.yaml` with the current module.

Every 3 modules, congratulate the user on their progress and show a visual progress bar:

```text
Bootcamp Progress:  [████████░░░░░░░░░░░░░░░░░░] 4/13 modules
Completed: 0, 1, 2, 3  |  Next: Module 4 (Data Quality)
Great work — you've completed 4 modules so far!
```

Gate checks:

- **0 → 1:** SDK installed, database configured, test script passes
- **1 → 2:** Demo completed or skipped
- **2 → 3:** Problem statement documented, data sources identified, success criteria defined
- **3 → 4:** All data sources collected, files in `data/raw/` or locations documented
- **4 → 5:** All sources evaluated, SGES compliance determined, sample data available
- **5 → 6:** All non-compliant sources mapped, transformation programs tested, quality >70%
- **6 → 7:** All sources loaded, no critical errors, loading statistics captured
- **7 → 8:** All sources orchestrated (or single source loaded)
- **8 → 9:** Query programs answer business problem, results validated, documentation complete. **Before starting Module 9**, load `cloud-provider-setup.md` and follow the cloud provider selection flow.
- **9 → 10:** Performance baselines captured, bottlenecks identified and documented, optimization recommendations recorded
- **10 → 11:** Security checklist complete, no critical vulnerabilities, secrets management configured, compliance documentation updated
- **11 → 12:** Monitoring dashboards configured, alerting rules defined, health checks passing, runbooks created
