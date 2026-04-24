---
inclusion: manual
---

# Onboarding Flow

Load when starting a fresh bootcamp. Sequence: directory creation → language selection → prerequisites → introduction → path selection.

**🚨 STRICT RULE: One question at a time.** Each numbered section below ends with a question and WAIT. Do NOT combine language selection, introduction, and path selection into one message. Present one question, wait for the response, then move to the next section. This is the most common onboarding complaint — do not skip the WAITs.

## 0. Setup Preamble

Before doing any setup work, tell the user:

"I'm going to do some quick administrative setup — creating your project directory, installing hooks, and checking your environment. You'll see me working for a moment. When I'm done, you'll see a big **WELCOME TO THE SENZING BOOTCAMP** banner — that's when the bootcamp officially starts and I'll begin asking you questions."

## 1. Directory Structure

Execute these setup actions in order. Do not narrate the details to the user.

1. Check if `src/`, `data/`, `docs/` exist. If not, load `project-structure.md` and create.
2. **Create Critical Hooks:** For each hook in the Hook Registry's "Critical Hooks" section below, call the `createHook` tool with the specified parameters. Create `.kiro/hooks/` directory first if needed. If a createHook call fails, log the failure and continue with remaining hooks. After all attempts, report any failures to the bootcamper with affected functionality. Record installed hooks in `config/bootcamp_preferences.yaml` under `hooks_installed` with timestamp.
3. **Copy glossary:** copy `senzing-bootcamp/docs/guides/GLOSSARY.md` to `docs/guides/GLOSSARY.md`. This MUST happen before Step 4 (Introduction) references it.
4. Generate foundational steering files (`product.md`, `tech.md`, `structure.md`) at `.kiro/steering/`. Each MUST include `inclusion` and `description` in the YAML frontmatter. Use `auto` for `structure.md`, `always` for the others.

## 2. Language Selection

**Detect the user's platform first** (`platform.system()`), then query the Senzing MCP server (`get_capabilities` or `sdk_guide`) for which languages are supported on that platform. The MCP server is the authoritative source — do not hardcode language/platform assumptions.

Present the MCP-returned language list to the bootcamper. **If the MCP server flags any language as discouraged, unsupported, or limited on the user's platform (e.g., Python on macOS), relay that warning clearly to the bootcamper** and suggest alternatives. For example, if MCP discourages Python on macOS, tell them: "The Senzing MCP server indicates Python is not recommended on macOS — [reason from MCP]. I'd suggest Java, C#, Rust, or TypeScript instead. Would you like to pick one of those?"

Ask: "👉 Which language would you like to use?" WAIT for response.

Persist to `config/bootcamp_preferences.yaml`. If file exists from previous session, confirm: "Last time you chose [language]. Continue or switch?"

Load language steering file immediately after confirmation (`lang-python.md`, `lang-java.md`, etc.).

## 3. Prerequisite Check

Detect platform (`platform.system()`). Check language runtime with `shutil.which()` — cross-platform, not `command -v`. Check for Senzing SDK import. Present results only if something is missing. Surface all missing deps here — don't discover them one at a time later.

**If the Senzing SDK is already installed and working (V4.0+):** Tell the user: "Senzing SDK is already installed." When Module 0 is reached (either explicitly or auto-inserted), the module's Step 1 check will detect this and skip installation. Do not re-install.

## 4. Bootcamp Introduction

**Display the welcome banner — make it impossible to miss:**

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎓🎓🎓  WELCOME TO THE SENZING BOOTCAMP!  🎓🎓🎓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

This signals to the user that setup is done and the bootcamp is starting. Everything before this was administrative.

Present the overview before path selection. Cover all points naturally:

- This bootcamp is a **guided discovery** of how to use Senzing. It's not a race — feel free to take it slow, read what the bootcamp is telling you, and ask questions at any point to help with your understanding. Be curious. The bootcamp is here to help you learn, not just to produce code.
- Goal: comfortable generating Senzing SDK code. Finish with running code as foundation for real use.
- Module overview table (0-12): what each does and why it matters
- Mock data available anytime. Three sample datasets: Las Vegas, London, Moscow
- Built-in 500-record eval license; bring your own for more
- Paths let you skip to what matters
- If you encounter unfamiliar terms (like SGES, DATA_SOURCE, entity resolution), there's a glossary at `docs/guides/GLOSSARY.md` — and you can always ask me to explain anything

Ask: "👉 Does this outline make sense? Any questions before we choose a path? Feel free to ask about anything — that's what the bootcamp is for." WAIT for response.

## 5. Path Selection

Present paths — not mutually exclusive, all completed modules carry forward:

- **A) Quick Demo** — 0→1. Verify technology works. One session.
- **B) Fast Track** — 5→6→8. Have SGES data. Straight to loading/querying.
- **C) Complete Beginner** — 2→3→4→5→6→8. From scratch with raw data.
- **D) Full Production** — All 0-12. Building for production.

Module 0 inserted automatically before any module needing SDK.

Interpreting responses: "A"/"demo"→Module 1, "B"/"fast"→Module 5, "C"/"beginner"→Module 2, "D"/"full"→Module 0. Bare number→clarify letter vs module.

Present paths with: "👉 Which path sounds right for you?"

## Switching Paths

All completed modules carry forward. Read `bootcamp_progress.json`, show new path requirements vs. done, update preferences, resume from first incomplete module.

## Changing Language

Update preferences. Warn: existing code in `src/` must be regenerated. Data/docs/config unaffected. Don't mix languages.

## Validation Gates

Run `validate_module.py --module N` before proceeding. Update `bootcamp_progress.json` and `bootcamp_preferences.yaml`. Every 3 modules: progress bar.

Gate checks:

| Gate  | Requires                                                                           |
|-------|------------------------------------------------------------------------------------|
| 0→1   | SDK installed, DB configured, test passes                                          |
| 1→2   | Demo completed or skipped                                                          |
| 2→3   | Problem documented, sources identified, criteria defined                           |
| 3→4   | Sources collected, files in `data/raw/`                                            |
| 4→5   | Sources evaluated, SGES compliance determined                                      |
| 5→6   | Sources mapped, programs tested, quality >70%                                      |
| 6→7   | Sources loaded, no critical errors                                                 |
| 7→8   | All sources orchestrated (or single source)                                        |
| 8→9   | Queries answer business problem, results validated. Load `cloud-provider-setup.md` |
| 9→10  | Baselines captured, bottlenecks documented                                         |
| 10→11 | Security checklist complete, no critical vulns                                     |
| 11→12 | Monitoring configured, health checks passing                                       |

## Hook Registry

All 18 bootcamp hooks are defined below. The agent reads these definitions and calls the `createHook` tool with the specified parameters. Critical Hooks are created during onboarding (Step 1). Module Hooks are created when the bootcamper starts the associated module.

### Critical Hooks (created during onboarding)

**capture-feedback-hook** (promptSubmit → askAgent)

Prompt: "Check if the bootcamper's message contains any of these feedback trigger phrases (case-insensitive): "bootcamp feedback", "power feedback", "submit feedback", "provide feedback", "I have feedback", "report an issue". If NONE of these phrases appear in the message, do nothing — let the conversation continue normally. If a trigger phrase IS found, immediately do the following: (1) Read config/bootcamp_progress.json to get the current module number and completed modules. If the file doesn't exist, record module as "Unknown". (2) Note what the bootcamper was doing in the recent conversation. (3) Note which files are open in the editor. (4) Load steering file feedback-workflow.md and follow its complete workflow, pre-filling the context fields with what you just captured. Do NOT ask the bootcamper to re-explain their context — you already have it."

- id: `capture-feedback-hook`
- name: `Capture Bootcamp Feedback`
- description: `Fires on every message submission. Checks for feedback trigger phrases and initiates the feedback workflow with automatic context capture.`

**enforce-feedback-path** (preToolUse → askAgent, toolTypes: write)

Prompt: "Check if you are currently in the feedback collection workflow (i.e., the bootcamper said 'bootcamp feedback', 'power feedback', or similar, and you are writing a feedback entry). If you are NOT in the feedback workflow, do nothing — let the write proceed normally. If you ARE writing feedback content (an improvement entry with Date, Module, Priority, Category, What Happened, Why It's a Problem sections), verify the target file path is exactly 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md'. If the path is different, STOP and redirect the write to 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md' instead. Do NOT write feedback to any other file. Do NOT submit feedback to any external service."

- id: `enforce-feedback-path`
- name: `Enforce Feedback File Path`
- description: `Before any write operation, checks if the agent is writing feedback content. If so, ensures it goes to docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md and nowhere else.`

**enforce-working-dir** (preToolUse → askAgent, toolTypes: write)

Prompt: "Before writing this file, verify: Does the file path or any path in the file content reference /tmp/, %TEMP%, ~/Downloads, or any location outside the working directory? If so, replace those paths with project-relative equivalents (database/G2C.db for databases, data/temp/ for temporary files, src/ for source code). Do NOT proceed with the write if it would place files outside the working directory."

- id: `enforce-working-dir`
- name: `Enforce Working Directory Paths`
- description: `Checks that file write operations do not use /tmp, %TEMP%, or any path outside the working directory. Enforces the file storage policy automatically.`

**verify-senzing-facts** (preToolUse → askAgent, toolTypes: write)

Prompt: "Before writing this file, verify that any Senzing-specific content (attribute names, SDK method signatures, configuration values, error code explanations) was retrieved from the Senzing MCP server tools (mapping_workflow, generate_scaffold, get_sdk_reference, search_docs, explain_error_code, sdk_guide) and not stated from training data. Per SENZING_INFORMATION_POLICY.md, all Senzing facts must come from MCP tools."

- id: `verify-senzing-facts`
- name: `Verify Senzing Facts Before Writing`
- description: `Reminds the agent to verify Senzing-specific facts via MCP tools before writing code or documentation that contains Senzing attribute names, SDK method calls, or configuration values.`

**code-style-check** (fileEdited → askAgent, filePatterns: `*.py, *.java, *.cs, *.rs, *.ts, *.js`)

Prompt: "A source code file was just edited. Check it for language-appropriate coding standards (Python: PEP-8 with max line length 100; Java: standard conventions; C#: .NET conventions; Rust: rustfmt/clippy; TypeScript: ESLint conventions). If violations are found, suggest specific fixes. If compliant, acknowledge briefly and continue."

- id: `code-style-check`
- name: `Code Style Check`
- description: `Automatically checks source code files for language-appropriate coding standards when edited.`

**summarize-on-stop** (agentStop → askAgent)

Prompt: "Before finishing, provide a brief summary for the bootcamper: (1) What did you just accomplish in this interaction? (2) Which files were created or modified — list the specific file paths. (3) What is the next step the bootcamper should expect when they continue? Keep it concise — a few sentences, not a wall of text."

- id: `summarize-on-stop`
- name: `Summarize Progress on Stop`
- description: `When the agent finishes working, it summarizes what was accomplished, which files changed, and what the next step is.`

**commonmark-validation** (fileEdited → askAgent, filePatterns: `**/*.md`)

Prompt: "The markdown file that was just edited should be validated for CommonMark compliance. Please check for: 1. MD022: Headings should be surrounded by blank lines. 2. MD040: Fenced code blocks should have a language specified. 3. Bold text followed by colons should use format: **Label:** (with space before colon). 4. MD031: Fenced code blocks should be surrounded by blank lines. 5. MD032: Lists should be surrounded by blank lines. EXCEPTION: If the file is CHANGELOG.md, ignore MD024 (duplicate headings). If any issues are found, fix them automatically."

- id: `commonmark-validation`
- name: `CommonMark Validation`
- description: `Validates that all Markdown files conform to CommonMark standards when edited.`

### Module Hooks (created when module starts)

**data-quality-check** — Module 5 (fileEdited → askAgent, filePatterns: `src/transform/*.*`)

Prompt: "The transformation program was just updated. Please review the changes and suggest running data quality validation tests to ensure the output still meets quality standards (>70% attribute coverage)."

- id: `data-quality-check`
- name: `Senzing Data Quality Check`
- description: `Automatically check data quality when transformation programs are saved.`

**validate-senzing-json** — Module 5 (fileEdited → askAgent, filePatterns: `data/transformed/*.jsonl, data/transformed/*.json`)

Prompt: "Senzing JSON output was modified. Please use the analyze_record MCP tool to validate a sample of records from this file to ensure they conform to the Senzing Generic Entity Specification."

- id: `validate-senzing-json`
- name: `Validate Senzing JSON Output`
- description: `Validate Senzing JSON format when transformation output files are created or modified.`

**analyze-after-mapping** — Module 5 (fileCreated → askAgent, filePatterns: `data/transformed/*.jsonl, data/transformed/*.json`)

Prompt: "A new Senzing JSON file was created in data/transformed/. Before proceeding to loading (Module 6), use the analyze_record MCP tool to validate a sample of records from this file. Check feature distribution, attribute coverage, and data quality. Quality score should be >70% before loading."

- id: `analyze-after-mapping`
- name: `Analyze After Mapping`
- description: `After completing a mapping task, reminds the agent to validate the transformation output using analyze_record before proceeding to loading.`

**backup-before-load** — Module 6 (fileEdited → askAgent, filePatterns: `src/load/*.*`)

Prompt: "A loading program was modified. Before running this in production, remind the user to backup the database using: python scripts/backup_project.py"

- id: `backup-before-load`
- name: `Backup Database Before Loading`
- description: `Remind to backup database before running loading programs.`

**run-tests-on-change** — Module 6 (fileEdited → askAgent, filePatterns: `src/load/*.*, src/query/*.*, src/transform/*.*`)

Prompt: "Source code was modified. If tests exist in the tests/ directory, remind the user to run them to verify the change didn't break anything. Suggest the appropriate test command for the chosen language."

- id: `run-tests-on-change`
- name: `Run Tests After Code Change`
- description: `Reminds the agent to run the test suite after source code changes in loading, query, or transformation programs.`

**verify-generated-code** — Module 6 (fileCreated → askAgent, filePatterns: `src/transform/*.*, src/load/*.*, src/query/*.*`)

Prompt: "A new bootcamp source file was created. Before moving to the next step, verify this code actually runs: (1) Execute it on a small sample (10-100 records from data/samples/ or data/raw/). (2) Check for errors or exceptions. (3) If it produces output, inspect the first few records. (4) Report the results to the bootcamper — did it work, and if not, what needs fixing? Do not skip this verification step."

- id: `verify-generated-code`
- name: `Verify Generated Code Runs`
- description: `When bootcamp source code is created, prompts the agent to run it on sample data and report results before moving on.`

**offer-visualization** — Module 8 (fileCreated → askAgent, filePatterns: `src/query/*`)

Prompt: "A query program was just created. If the bootcamper is in Module 8 and hasn't been offered the entity graph visualization yet, offer it: 'Would you like me to help you build an interactive entity graph visualization? It shows resolved entities as a force-directed network graph with clustering, search, and detail panels. I can create a self-contained HTML file you can open in any browser.' If they accept, load steering file visualization-guide.md and follow its workflow."

- id: `offer-visualization`
- name: `Offer Entity Graph Visualization`
- description: `After query programs are created in Module 8, prompts the agent to offer generating an interactive entity graph visualization.`

**enforce-viz-offers** — Module 8 (agentStop → askAgent)

Prompt: "First, read config/bootcamp_progress.json and check the current_module field. If the current module is NOT 8, do nothing — let the conversation end normally. If the current module IS 8, review the conversation history and check whether you offered BOTH of these visualizations during this interaction: 1. Entity graph visualization — an interactive force-directed network graph of resolved entities (offered after exploratory queries in step 3). 2. Results dashboard — an HTML page showing query results and validation metrics (offered after documenting findings in step 7). If BOTH were offered (regardless of whether the bootcamper accepted or declined), do nothing. If EITHER was NOT offered, ask the bootcamper if they would like that visualization before wrapping up. WAIT for the bootcamper's response before finishing."

- id: `enforce-viz-offers`
- name: `Enforce Module 8 Visualization Offers`
- description: `When the agent stops during Module 8, checks whether both visualization offers were made. If either was missed, prompts the agent to offer it before closing.`

**module12-phase-gate** — Module 12 (postTaskExecution → askAgent)

Prompt: "First, read config/bootcamp_progress.json and check the current_module field. If the current module is NOT 12, do nothing. If the current module IS 12, display a packaging-complete summary showing all packaging steps are done (containerized, multi-env config, CI/CD, checklist, rollback plan) and note that nothing has been deployed yet — it is safe to stop here. Then ask: "Would you like to actually deploy this now, or would you prefer to stop here and deploy later on your own?" WAIT for the bootcamper's response. Do NOT proceed to deployment steps until the bootcamper explicitly says they want to deploy."

- id: `module12-phase-gate`
- name: `Module 12 Phase Gate`
- description: `After packaging tasks complete in Module 12, displays a phase gate prompt asking the bootcamper whether to proceed to deployment or stop.`

**backup-on-request** — any module (userTriggered → askAgent)

Prompt: "The user wants to back up their project. Run the backup script: python3 scripts/backup_project.py (on Linux/macOS) or python scripts/backup_project.py (on Windows). Create the backups/ directory first if it doesn't exist."

- id: `backup-on-request`
- name: `Backup Project on Request`
- description: `Run project backup when user clicks the hook button.`

**git-commit-reminder** — any module (userTriggered → askAgent)

Prompt: "The user wants to commit their bootcamp progress. Check config/bootcamp_progress.json for the current module number and list of completed modules. Then suggest a git commit with a descriptive message like: git add . && git commit -m "Complete Module [N]: [Module Name]". Show the user the command and ask if they'd like you to run it."

- id: `git-commit-reminder`
- name: `Git Commit Reminder`
- description: `Reminds the user to commit their work after completing a module. Triggered manually via button click.`
