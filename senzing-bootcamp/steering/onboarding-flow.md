---
inclusion: manual
---

# Onboarding Flow

This steering file contains the full onboarding sequence: directory creation, language selection, prerequisite checks, path selection, and validation gates. Load this when starting a fresh bootcamp or when the user wants to begin.

## Create Directory Structure

1. Check if project directory structure exists (`src/`, `data/`, `docs/`)
2. If it doesn't exist, load `project-structure.md` and execute the creation commands.
3. Only then proceed with any other activity

**Trigger points** — create structure at any of these:

- User says "start the bootcamp" or mentions any module number (0-12)
- User selects any path (A, B, C, D) or asks to begin
- Any indication they want to start using the power

If directory creation fails, report the error, provide commands for manual execution, and do not proceed until the structure exists.

After creating the directory structure (or confirming it exists), install the bootcamp hooks automatically by copying all `.kiro.hook` files from `senzing-bootcamp/hooks/` to `.kiro/hooks/` (create the directory if needed). Do not ask — just install them silently.

**Do not narrate setup steps to the user.** Directory creation, hook installation, and steering file generation should happen without explanation. The user doesn't need to know about the internal setup — just move to the first question (language selection).

## Generate Foundational Steering Files

After directory creation, generate project-specific steering files for the user's workspace at `.kiro/steering/`:

1. **product.md** — project purpose, target users, business objectives (based on what the user describes in Module 2, or a placeholder if starting with Module 0/1)
2. **tech.md** — chosen language, Senzing SDK, database choice, key dependencies
3. **structure.md** — project directory layout, naming conventions, import patterns

Use Kiro's built-in "Generate Steering Docs" if available, or create minimal versions that get refined as the bootcamp progresses. These help Kiro understand the project context beyond what the bootcamp steering files provide. Do not mention this step to the user — it's internal agent setup.

**Frontmatter for generated steering files:** Each file MUST include explicit `inclusion` frontmatter so Kiro knows when to load them:

```yaml
# product.md — always relevant for project context
---
inclusion: always
---

# tech.md — always relevant for code generation
---
inclusion: always
---

# structure.md — load when editing source files
---
inclusion: fileMatch
fileMatchPattern: "src/**/*"
---
```

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

3. **Ask the bootcamper:** "Which language? [list from MCP]"

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

   **Windows/WSL2 setup** (for Python or if the SDK has Linux dependencies for other languages):

   If the bootcamper is on Windows and needs a Linux environment:

   1. Install WSL2 (requires Windows 10 version 2004+ or Windows 11):

      ```powershell
      wsl --install
      ```

      This installs Ubuntu by default. Restart when prompted.

   2. Open the Ubuntu terminal and set up the development environment inside WSL2:

      ```bash
      sudo apt update && sudo apt upgrade -y
      sudo apt install -y python3 python3-pip python3-venv git
      ```

   3. The bootcamp project directory should live inside the WSL2 filesystem (e.g., `~/my-senzing-project`), not on the Windows filesystem (`/mnt/c/...`), for better performance.

   4. Kiro can connect to WSL2 — open the project from within the WSL2 filesystem.

   5. All subsequent bootcamp commands should be run inside the WSL2 terminal.

   If the bootcamper prefers not to use WSL2, recommend they choose Java, C#, Rust, or TypeScript instead, as these have broader platform support.

8. **Code quality standards:** Apply language-appropriate coding standards:
   - Python → PEP-8 (see `docs/policies/CODE_QUALITY_STANDARDS.md`)
   - Java → Standard Java conventions (camelCase methods, PascalCase classes, Javadoc)
   - C# → .NET conventions (PascalCase methods and classes, XML doc comments)
   - Rust → Rust conventions (snake_case, rustfmt, clippy)
   - TypeScript → Standard TS conventions (camelCase, ESLint, JSDoc)

9. **Load language steering file immediately:** After the language is confirmed, load the corresponding language steering file so conventions are in context for all subsequent code generation — don't wait for a matching file to be edited:
   - Python → `lang-python.md`
   - Java → `lang-java.md`
   - C# → `lang-csharp.md`
   - Rust → `lang-rust.md`
   - TypeScript → `lang-typescript.md`

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

Present results only if something is missing. If everything passes, proceed silently to path selection.

- If everything passes → proceed to path selection without comment.
- If anything is missing → tell the user briefly what needs to be installed. Let them choose to install now or pick a path first (they can still do Module 2 — Business Problem — without the SDK).
- Do NOT discover missing dependencies one at a time during later modules. Surface them all here.

## Bootcamp Introduction (Scene-Setting)

Before path selection, present the bootcamp overview so the user has a clear mental model of what they're signing up for. This is critical — users who skip this step often feel lost later.

Present this introduction (adapt the wording naturally, but cover all points):

> "Here's what this bootcamp is about:
>
> The goal is to make you comfortable generating code — with my help — that uses the Senzing SDK for entity resolution. By the end, you'll have running code that serves as the foundation for your real-world use of Senzing.
>
> The bootcamp is a series of modules, each building on the last. Here's the full picture:
>
> | Module | What It Does | Why It Matters |
> |--------|-------------|----------------|
> | 0 — SDK Setup | Install and configure the Senzing SDK | Everything else depends on a working installation |
> | 1 — Quick Demo | Run entity resolution on sample data | Validates your setup end-to-end (the result is trivial on purpose — the point is proving the system works) |
> | 2 — Business Problem | Define what you're solving and which data sources matter | Focuses the rest of the bootcamp on your actual use case |
> | 3 — Data Collection | Get your data files into the project | Can't resolve entities without data |
> | 4 — Data Quality | Score your data for completeness and consistency | Catches issues before they cause bad matches |
> | 5 — Data Mapping | Transform your data into Senzing's JSON format | Senzing needs data in a specific format to work |
> | 6 — Single Source Loading | Load your first data source into Senzing | Your first real entity resolution run with your data |
> | 7 — Multi-Source | Load and coordinate multiple data sources | Cross-source matching is where ER really shines |
> | 8 — Query & Validation | Build query programs and validate results | Proves the system answers your business questions |
> | 9-12 — Production | Performance, security, monitoring, deployment | Gets your solution production-ready |
>
> A few things to know up front:
> - If you don't have data readily available, we can generate mock data at any point. Senzing also provides three ready-made sample datasets — Las Vegas (customer records), London (person records), and Moscow (organization records) — that you can use as stand-ins throughout the entire bootcamp, not just in the demo
> - Senzing includes a built-in evaluation license for 500 records (enough for the bootcamp), but you can bring your own license for more capacity
> - You don't have to do every module — there are paths that let you skip to what matters most to you
>
> You'll pick a path in a moment, but first — does this outline make sense? Any questions about what the bootcamp covers before we choose a path?"

**WAIT for the user's response.** Answer any questions they have about the bootcamp structure. Only proceed to path selection after they indicate they're ready.

## Path Selection

Present the paths with enough context for an informed choice. The bootcamp has 13 modules (0-12) and each path covers a different subset:

> "Now let's pick your path. These are not mutually exclusive — you can start with one and jump to another at any time. All completed modules carry forward.
>
> A) Quick Demo — Modules 0 → 1. See entity resolution in action with sample data. Done in one session. Choose this if you want to verify the technology works before investing more time.
> B) Fast Track — Modules 5 → 6 → 8. For people who already have Senzing-ready (SGES) data. Choose this if you've already mapped your data and want to get straight to loading and querying.
> C) Complete Beginner — Modules 2 → 3 → 4 → 5 → 6 → 8. Full learning path from defining the problem through validating results. Choose this if you're starting from scratch with raw data and want guided help through the entire process.
> D) Full Production — All modules 0-12, including performance testing, security, monitoring, and deployment. Choose this if you're building something that needs to run in production.
>
> Module 0 (SDK Setup) is inserted automatically before any module that needs it. Which path sounds right for you?"

**Path A note:** Module 0 (SDK Setup) is required before Module 1 (Quick Demo). If Module 0 is not complete, insert it first: "To run the demo, we need the Senzing SDK installed. Let's do Module 0 first — it takes about 30-60 minutes as a one-time setup."

**Path B note:** Module 0 (SDK Setup) is required before Module 6 (Loading). When the user reaches Module 6 on Path B, check if Module 0 is complete. If not, insert it: "Before we can load data, we need to set up the Senzing SDK. Let's do Module 0 first — it takes about 30-60 minutes as a one-time setup."

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
