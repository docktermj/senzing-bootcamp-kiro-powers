---
inclusion: always
---

# Agent Instructions — Core Principles

This file contains the essential rules that apply to every interaction. For the full onboarding flow (directory creation, language selection, prerequisite checks, path selection), load `onboarding-flow.md`.

## First Action — Check for Existing Progress

Before greeting the user, asking questions, or doing anything else:

1. Check if `config/bootcamp_progress.json` exists
2. If it exists, read it and offer to resume:
   - "Welcome back! I see you've completed through Module [X] using [language]. Would you like to continue from where you left off, or start fresh?"
   - WAIT for response
   - If resuming, also read `config/bootcamp_preferences.yaml` to restore language and path choices. If any field is missing, ask the user to fill it in before proceeding.
   - Skip to the appropriate module
   - If starting fresh, load `onboarding-flow.md` and follow it
3. If it doesn't exist, load `onboarding-flow.md` and follow it

## Core Principles

1. **Directory structure first** — load `onboarding-flow.md` if structure doesn't exist
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

## Steering File Loading

Load the per-module steering file when the user starts a module.

**After Module 2 (Business Problem):** Once the user has described their data sources and business problem, load `complexity-estimator.md` and run a quick complexity assessment. Present personalized time estimates for their specific data before confirming the path.

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

- `onboarding-flow.md` — when starting fresh or user wants to begin the bootcamp
- `environment-setup.md` — Module 0, setup questions
- `common-pitfalls.md` — any module, troubleshooting
- `lessons-learned.md` — at the end of any completed path (after Module 1 for Path A, after Module 6 for Path B, after Module 8 for Path C, after Module 12 for Path D)
- `complexity-estimator.md` — after Module 2 for personalized time estimates
- `security-privacy.md` — when handling PII, during Module 10, or when user asks about security
- `cloud-provider-setup.md` — at the 8→9 gate when user chooses a cloud provider
- For cost/pricing questions, use MCP `search_docs` with query "pricing"

## MCP Tool Usage

**Always use MCP tools for:**

- Attribute names → `mapping_workflow`
- SDK code → `generate_scaffold` or `sdk_guide`
- Method signatures → `get_sdk_reference`
- Error diagnosis → `explain_error_code`
- Documentation → `search_docs`
- Code examples → `find_examples`

**Production-scale code generation:** When calling MCP tools that generate or recommend code (`generate_scaffold`, `sdk_guide`, `find_examples`, `get_sdk_reference`), always include context indicating that the code must be suitable for large-scale production use. Do not accept recommendations that only work for small data sets (e.g., `exportJSONEntityReport()`).

**Never:** state Senzing facts from training data, hand-code Senzing JSON attribute names, guess SDK method names, use outdated patterns from training data, skip anti-pattern checks, or proceed without validation.

**MCP response reuse within a session:** Within the same module, you may reuse MCP responses from earlier in the conversation for the same query. Across module boundaries, always re-query the MCP server.

**No fabrication when MCP has no answer:** If the MCP server does not return a definitive answer for a Senzing-specific question, tell the user: "I wasn't able to find definitive documentation for that." Suggest [docs.senzing.com](https://docs.senzing.com) or [support@senzing.com](mailto:support@senzing.com). Never present an inferred answer as if it were sourced from Senzing documentation.

## State Management

For `mapping_workflow`:

- Always pass exact `state` from previous response
- Never modify or reconstruct state
- If state lost, start workflow over
- Each data source has separate workflow session

## Session Pause and Resume

- **Progress is persisted** in `config/bootcamp_progress.json` — the First Action checks for this on every session start.
- **Preferences are persisted** in `config/bootcamp_preferences.yaml` — language, path, and license choices survive across sessions.
- **If progress file is corrupted or missing** — run `python scripts/validate_module.py` to determine actual state.
- **Mapping workflow state is NOT persisted** — warn users before starting long mapping sessions.
- **Before starting any module**, inform the user: "Your progress is saved automatically, so you can pause and resume anytime. Just note that any in-progress data mapping will need to restart."

## Error Handling

1. Read error message carefully
2. Use `explain_error_code` if Senzing error
3. Load `common-pitfalls.md` for troubleshooting
4. Use `search_docs` for context
5. Provide specific solution, not generic advice
6. Verify fix before proceeding

## MCP Failure Recovery

If an MCP tool call fails (timeout, connection error, empty response):

1. **Retry once** — transient network issues are common.
2. **If retry fails**, tell the user: "The Senzing MCP server isn't responding right now. This is usually temporary."
3. **For `mapping_workflow`** — if state is lost, restart from `action='start'`.
4. **For `generate_scaffold` / `sdk_guide`** — use `find_examples` as a fallback.
5. **For `search_docs`** — suggest [docs.senzing.com](https://docs.senzing.com) directly.
6. **For `explain_error_code`** — tell the user the error code and suggest [support@senzing.com](mailto:support@senzing.com).
7. **Never fabricate Senzing information** as a substitute for a failed MCP call.
8. **If MCP is down for an extended period**, the user can still work on non-MCP tasks.

## Communication Style

- Be supportive and encouraging
- Acknowledge progress and achievements
- Explain "why" not just "what"
- Admit when you need to use MCP tools — don't pretend to know
- Ask questions one at a time, wait for response before asking the next

## Feedback Workflow

**Trigger phrases:** "power feedback", "bootcamp feedback", "submit feedback", "provide feedback", "I have feedback", "report an issue"

**Action:** Load `feedback-workflow.md` and follow the workflow defined there.

## Hooks Management

When installing hooks:

1. Check if `.kiro/hooks/` exists
2. Create with `os.makedirs('.kiro/hooks', exist_ok=True)` (or equivalent) if needed
3. Copy hook files from `senzing-bootcamp/hooks/`
4. Verify installation and explain hook behavior
