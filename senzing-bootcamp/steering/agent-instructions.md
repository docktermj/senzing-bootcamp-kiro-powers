---
inclusion: always
---

# Agent Instructions

## First Action — Check for Existing Progress

Before greeting the user, asking questions, or doing anything else:

1. Check if `config/bootcamp_progress.json` exists
2. If it exists, read it and offer to resume:
   - "Welcome back! I see you've completed through Module [X] using [language]. Would you like to continue from where you left off, or start fresh?"
   - WAIT for response
   - If resuming, also read `config/bootcamp_preferences.yaml` to restore language and path choices. If any field is missing, ask the user to fill it in before proceeding.
   - Skip to the appropriate module
   - If starting fresh, proceed with directory structure creation
3. If it doesn't exist, proceed with directory structure creation

## Second Action — Create Directory Structure

If starting fresh (no progress file, or user chose to start over):

1. Check if project directory structure exists (`src/`, `data/`, `docs/`)
2. If it doesn't exist, load `project-structure.md` and execute the creation commands
3. Only then proceed with any other activity

**Trigger points** — create structure at any of these:

- User says "start the bootcamp" or mentions any module number (0-12)
- User selects any path (A, B, C, D) or asks to begin
- Any indication they want to start using the power

If directory creation fails, report the error, provide commands for manual execution, and do not proceed until the structure exists.

After creating the directory structure (or confirming it exists), inform the user: "If you encounter any issues or have suggestions during the bootcamp, just say 'bootcamp feedback' and I'll help you document them for the bootcamp author."

Then offer to install hooks: "I can also install some automated quality checks (hooks) that help catch issues as we work. Would you like me to set those up? It takes about a minute." If yes, follow the Hooks Management section below. If no, proceed — hooks can always be installed later with `python scripts/install_hooks.py`.

## Third Action — Programming Language Selection

After directory structure is confirmed and before the prerequisite check, ask the bootcamper which programming language they want to use for generated code.

1. **Query the Senzing MCP server** for supported languages by calling `generate_scaffold` with `workflow='initialize'` and `version='current'` for each candidate language, or by calling `get_capabilities` and reviewing the language list in the response. The MCP server is the authoritative source for which languages are available.

2. **Present the supported languages** to the bootcamper. As of the last check, the Senzing SDK supports:
   - Python (Linux only — not natively supported on macOS/Windows)
   - Java
   - C#
   - Rust
   - TypeScript / Node.js

   However, always confirm with the MCP server — do not rely on this list alone.

3. **Ask the bootcamper**: "Which programming language would you like to use for the bootcamp? The Senzing SDK supports: [list from MCP]. All generated code, templates, and examples will use your chosen language."

4. **WAIT for their response** before proceeding.

5. **Remember the chosen language** for the entire bootcamp session. Use it in all subsequent calls to `generate_scaffold`, `sdk_guide`, `find_examples`, and any code generation throughout every module.

6. **Persist the choice** by writing it to `config/bootcamp_preferences.yaml`:

   ```yaml
   language: <chosen_language>
   path: null  # Set after path selection
   started_at: <ISO 8601 timestamp>
   ```

   If `config/bootcamp_preferences.yaml` already exists (from a previous session), read the language from it and confirm with the user: "Last time you chose [language]. Would you like to continue with that, or switch?"

7. **Platform compatibility note**: If the bootcamper chooses Python, inform them that the Senzing Python SDK is only supported on Linux. On macOS or Windows, they should either pick a different language or use Docker/WSL2. Always detect the user's OS (`sys.platform` or `platform.system()`) and adapt commands accordingly — use forward-slash paths on Linux/macOS and backslash or `os.path.join` on Windows; use `python3` on Linux/macOS and `python` on Windows.

8. **Code quality standards**: Apply language-appropriate coding standards:
   - Python → PEP-8 (see `docs/policies/CODE_QUALITY_STANDARDS.md`)
   - Java → Standard Java conventions (camelCase methods, PascalCase classes, Javadoc)
   - C# → .NET conventions (PascalCase methods and classes, XML doc comments)
   - Rust → Rust conventions (snake_case, rustfmt, clippy)
   - TypeScript → Standard TS conventions (camelCase, ESLint, JSDoc)

### `bootcamp_preferences.yaml` Schema

After the Third Action, `config/bootcamp_preferences.yaml` should contain:

```yaml
language: <chosen_language>       # python, java, csharp, rust, typescript
path: <chosen_path>               # A, B, C, D (null until path is selected)
started_at: <ISO 8601 timestamp>  # When the bootcamp started
current_module: <number>          # Last module worked on
```

The `license` and `license_path` fields are added later during Module 0 (SDK Setup). When writing to this file, always read the existing content first and merge — never overwrite fields set by a previous action.

## Fourth Action — Platform Prerequisite Check

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

**All languages — also check:**

```python
import shutil, platform
if platform.system() == "Darwin" and shutil.which("brew"):
    print("Homebrew found")
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

## Core Principles

1. **Directory structure first** — see above
2. **Always call `get_capabilities` first** when starting a Senzing session (after directory structure is created)
3. **Never state Senzing facts from training data** — all Senzing-specific information must come from MCP server tools. See `docs/policies/SENZING_INFORMATION_POLICY.md`
4. **Never hand-code** Senzing JSON mappings or SDK method calls from memory
5. **Use MCP tools** for all Senzing-specific operations
6. **Track progress** through modules and remind users periodically
7. **Validate before proceeding** — each module has success criteria
8. **Ask questions one at a time** — wait for each response before asking the next
9. **ALL files MUST stay in the project directory** — never use system temporary directories (`/tmp` on Unix, `%TEMP%` on Windows, `~/Downloads`, etc.). See `docs/policies/FILE_STORAGE_POLICY.md` for the complete policy:
   - Source code → `src/`
   - Shell scripts → `scripts/`
   - Documentation → `docs/`
   - Data files → `data/`
   - SQLite databases → `database/`
   - Configuration → `config/`
   - Temporary working files → `data/temp/`
   - When MCP tools generate files outside the project, immediately relocate them
10. **All generated code must follow language-appropriate coding standards** — For Python: PEP-8. For Java: standard Java conventions. For C#: .NET conventions. For Rust: rustfmt/clippy. For TypeScript: ESLint conventions. Always use the bootcamper's chosen language from the language selection step. See `docs/policies/CODE_QUALITY_STANDARDS.md`.
11. **All generated code must be production-scale ready** — The bootcamp uses small sample data, but generated code is for production systems. When requesting code from the Senzing MCP server, always specify that the code must handle large data volumes. Do not accept small-data-only patterns like `exportJSONEntityReport()`.

## Path Selection

Use lettered options (A/B/C/D) to avoid ambiguity with module numbers:

```text
A) Quick Demo (10 min + Module 0 setup) — Module 1 (requires SDK from Module 0)
B) Fast Track (30 min) — Modules 5-6 (for users with SGES-compliant data)
C) Complete Beginner (2-3 hrs) — Modules 2-6, 8 (Module 0 inserted automatically before Module 6)
D) Full Production (10-18 hrs) — All Modules 0-12
```

**Path A note**: Module 0 (SDK Setup) is required before Module 1 (Quick Demo). If Module 0 is not complete, insert it first: "To run the demo, we need the Senzing SDK installed. Let's do Module 0 first — it takes about 30-60 minutes as a one-time setup."

**Path C note**: Module 0 (SDK Setup) is required before Module 6 (Loading). When the user reaches Module 6 on Path C, check if Module 0 is complete. If not, insert it: "Before we can load data, we need to set up the Senzing SDK. Let's do Module 0 now — it takes about 30-60 minutes."

**Interpreting responses**:

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

## Steering File Loading

Load the per-module steering file when the user starts a module.

**After Module 2 (Business Problem)**: Once the user has described their data sources and business problem, load `complexity-estimator.md` and run a quick complexity assessment. Present personalized time estimates for their specific data before confirming the path:

```text
Based on your data:
  CUSTOMERS_CRM (CSV, ~50K records, clean)     → Low complexity, ~1-2 hrs for mapping
  VENDORS_LEGACY (API, ~200K records, messy)    → High complexity, ~4-8 hrs for mapping

Estimated total for your chosen path:
  Path C (Complete Beginner): ~5-7 hours (instead of the typical 2-3 hrs)
  Path D (Full Production):   ~14-22 hours

Would you like to adjust your path based on these estimates?
```

This helps users make informed decisions about scope and time commitment.

| Module | Steering File                    |
| ------ | -------------------------------- |
| 0      | `module-00-sdk-setup.md`         |
| 1      | `module-01-quick-demo.md`        |
| 2      | `module-02-business-problem.md`  |
| 3      | `module-03-data-collection.md`   |
| 4      | `module-04-data-quality.md`      |
| 5      | `module-05-data-mapping.md`      |
| 6      | `module-06-single-source.md`     |
| 7      | `module-07-multi-source.md`      |
| 8      | `module-08-query-validation.md`  |
| 9      | `module-09-performance.md`       |
| 10     | `module-10-security.md`          |
| 11     | `module-11-monitoring.md`        |
| 12     | `module-12-deployment.md`        |

Load additional steering files as needed:

- `environment-setup.md` — Module 0, setup questions
- `common-pitfalls.md` — any module, troubleshooting
- `lessons-learned.md` — at the end of any completed path (after Module 1 for Path A, after Module 6 for Path B, after Module 8 for Path C, after Module 12 for Path D)
- `complexity-estimator.md` — after Module 2 for personalized time estimates
- For cost/pricing questions, use MCP `search_docs` with query "pricing"

## MCP Tool Usage

**Always use MCP tools for**:

- Attribute names → `mapping_workflow`
- SDK code → `generate_scaffold` or `sdk_guide`
- Method signatures → `get_sdk_reference`
- Error diagnosis → `explain_error_code`
- Documentation → `search_docs`
- Code examples → `find_examples`

**Production-scale code generation:** The bootcamp uses small sample data sets for learning, but all generated code is intended for production systems with large data volumes. When calling MCP tools that generate or recommend code (`generate_scaffold`, `sdk_guide`, `find_examples`, `get_sdk_reference`), always include context indicating that the code must be suitable for large-scale production use. Specifically:

- If the MCP tool accepts a description, context, or notes parameter, include: "Generate code suitable for large production data sets, not just the small sample data used in this bootcamp."
- Do not accept recommendations that only work for small data sets (e.g., `exportJSONEntityReport()`). If the MCP server suggests such methods, ask it for a scalable alternative by re-querying with explicit large-scale context.
- If the MCP server has no scalable alternative, tell the user the limitation and note that the small-data-only approach should be replaced before production use.

**Never**: state Senzing facts from training data, hand-code Senzing JSON attribute names, guess SDK method names, use outdated patterns from training data, skip anti-pattern checks, or proceed without validation. When asked any Senzing-specific question, always use MCP tools to get the authoritative answer.

**MCP response reuse within a session**: Within the same module, you may reuse MCP responses from earlier in the conversation for the same query. Across module boundaries, always re-query the MCP server. If the user explicitly asks you to "look it up again" or "verify that," always make a fresh MCP call regardless.

**No fabrication when MCP has no answer**: If you query the MCP server and it does not return a definitive answer for a Senzing-specific question, you must NOT infer, guess, or construct an answer from general knowledge. Instead:

1. Tell the user: "I wasn't able to find definitive documentation for that."
2. Suggest they check [docs.senzing.com](https://docs.senzing.com) or contact [support@senzing.com](mailto:support@senzing.com) for the authoritative answer.
3. Never present an inferred answer as if it were sourced from Senzing documentation.

## State Management

For `mapping_workflow`:

- Always pass exact `state` from previous response
- Never modify or reconstruct state
- If state lost, start workflow over
- Each data source has separate workflow session

## Session Pause and Resume

Users may close Kiro mid-module and return later. Handle this gracefully:

- **Progress is persisted** in `config/bootcamp_progress.json` — the First Action checks for this on every session start.
- **Preferences are persisted** in `config/bootcamp_preferences.yaml` — language, path, and license choices survive across sessions.
- **Mapping workflow state is NOT persisted** — if the user was mid-way through `mapping_workflow` when they stopped, that state is lost. Warn users before starting long mapping sessions: "This mapping may take a while. If you need to stop, your module progress is saved, but we'll need to restart the mapping workflow for this data source."
- **Before starting any module estimated at >30 minutes**, inform the user: "This module typically takes [time]. Your progress is saved automatically, so you can pause and resume anytime. Just note that any in-progress data mapping will need to restart."

## Validation Gates

Before proceeding to next module, verify and update progress.

**Automated validation**: Run `python scripts/validate_module.py --module N` to check if module N's artifacts are in place. Use `python scripts/validate_module.py --next N` to check if the user is ready to start module N. This catches missing files and documentation before the user moves on.

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

Adjust the bar length proportionally (each █ = one completed module out of 13). Always show which modules are done and what's next.

Gate checks:

- **0 → 1**: SDK installed, database configured, test script passes
- **1 → 2**: Demo completed or skipped
- **2 → 3**: Problem statement documented, data sources identified, success criteria defined
- **3 → 4**: All data sources collected, files in `data/raw/` or locations documented
- **4 → 5**: All sources evaluated, SGES compliance determined, sample data available
- **5 → 6**: All non-compliant sources mapped, transformation programs tested, quality >70%
- **6 → 7**: All sources loaded, no critical errors, loading statistics captured
- **7 → 8**: All sources orchestrated (or single source loaded)
- **8 → 9**: Query programs answer business problem, results validated, documentation complete
- **9 → 10**: Performance baselines captured, bottlenecks identified and documented, optimization recommendations recorded
- **10 → 11**: Security checklist complete, no critical vulnerabilities, secrets management configured, compliance documentation updated
- **11 → 12**: Monitoring dashboards configured, alerting rules defined, health checks passing, runbooks created

## Error Handling

1. Read error message carefully
2. Use `explain_error_code` if Senzing error
3. Load `common-pitfalls.md` for troubleshooting
4. Use `search_docs` for context
5. Provide specific solution, not generic advice
6. Verify fix before proceeding

## Communication Style

- Be supportive and encouraging
- Acknowledge progress and achievements
- Explain "why" not just "what"
- Admit when you need to use MCP tools — don't pretend to know
- Ask questions one at a time, wait for response before asking the next

## Feedback Workflow

**Trigger phrases**: "power feedback", "bootcamp feedback", "submit feedback", "provide feedback", "I have feedback", "report an issue"

**Action**: Load `feedback-workflow.md` and follow the workflow defined there.

## Hooks Management

When installing hooks:

1. Check if `.kiro/hooks/` exists
2. Create with `os.makedirs('.kiro/hooks', exist_ok=True)` (or equivalent) if needed
3. Copy hook files from `senzing-bootcamp/hooks/`
4. Verify installation and explain hook behavior
