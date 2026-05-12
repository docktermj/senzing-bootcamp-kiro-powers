# Implementation Plan: Require MCP Server

## Overview

Make the Senzing MCP server a hard requirement for the bootcamp. Remove all offline/fallback infrastructure, delete static Senzing knowledge files replaceable by MCP, simplify steering files, and remove the verify-senzing-facts hook. Organized into 10 phases to manage dependencies.

## Tasks

- [x] 1. Delete offline mode and fallback files
  - [x] 1.1 Delete `senzing-bootcamp/docs/guides/OFFLINE_MODE.md`
    - _Requirements: 1_
  - [x] 1.2 Delete `senzing-bootcamp/steering/mcp-offline-fallback.md`
    - _Requirements: 1_
  - [x] 1.3 Delete `senzing-bootcamp/docs/guides/GLOSSARY.md`
    - _Requirements: 8_
  - [x] 1.4 Delete `senzing-bootcamp/docs/guides/DATA_UPDATES_AND_DELETIONS.md`
    - _Requirements: 9_
  - [x] 1.5 Delete `senzing-bootcamp/docs/guides/DESIGN_PATTERNS.md`
    - _Requirements: 9_
  - [x] 1.6 Delete `senzing-bootcamp/docs/guides/INCREMENTAL_LOADING.md`
    - _Requirements: 9_
  - [x] 1.7 Delete `senzing-bootcamp/docs/guides/MULTI_LANGUAGE_DATA.md`
    - _Requirements: 9_
  - [x] 1.8 Delete `senzing-bootcamp/docs/guides/STREAMING_INTEGRATION.md`
    - _Requirements: 9_
  - [x] 1.9 Delete `senzing-bootcamp/hooks/verify-senzing-facts.kiro.hook`
    - _Requirements: 12_

- [x] 2. Convert MCP health check to hard gate
  - [x] 2.1 Rewrite Step 0b in `senzing-bootcamp/steering/onboarding-flow.md`: keep the probe, replace failure path with blocking error + troubleshooting steps, remove `.mcp_status` writes, remove "Mid-Session Recovery" section
    - _Requirements: 2, 3, 14_
  - [x] 2.2 Rewrite Step 2d in `senzing-bootcamp/steering/session-resume.md`: same hard gate pattern, remove `.mcp_status` read/write, remove mid-session recovery logic
    - _Requirements: 2, 3, 14, 16_

- [x] 3. Remove fallback logic from module steering files
  - [x] 3.1 Remove "If MCP unavailable" comment block from `senzing-bootcamp/steering/entity-resolution-intro.md`
    - _Requirements: 4, 11_
  - [x] 3.2 Remove inline 5-record fallback dataset and MCP-unavailable conditional from `senzing-bootcamp/steering/module-03-quick-demo.md`
    - _Requirements: 4, 19_
  - [x] 3.3 Remove "Agent guidance — MCP unavailable" note from `senzing-bootcamp/steering/visualization-guide.md`
    - _Requirements: 4_
  - [x] 3.4 Simplify MCP Failure section in `senzing-bootcamp/steering/agent-instructions.md` to: "Retry once. If still failing, block and tell bootcamper to fix connection. Never fabricate Senzing facts. All Senzing facts must come from MCP tools."
    - _Requirements: 4, 12_
  - [x] 3.5 Reduce "MCP Server Unavailable" section in `senzing-bootcamp/steering/common-pitfalls.md` to connectivity troubleshooting only (proxy, DNS, firewall, IDE restart)
    - _Requirements: 4, 10, 18_

- [x] 4. Update steering index and hook registry
  - [x] 4.1 Remove `offline: mcp-offline-fallback.md` keyword entry and `mcp-offline-fallback.md` metadata from `senzing-bootcamp/steering/steering-index.yaml`
    - _Requirements: 5_
  - [x] 4.2 Remove metadata entries for all deleted guide files from `senzing-bootcamp/steering/steering-index.yaml` (if present)
    - _Requirements: 9_
  - [x] 4.3 Remove `verify-senzing-facts` from `senzing-bootcamp/hooks/hook-categories.yaml` critical hooks list
    - _Requirements: 12_
  - [x] 4.4 Remove `verify-senzing-facts` entry from `senzing-bootcamp/steering/hook-registry.md` and decrement hook count
    - _Requirements: 12_

- [x] 5. Update onboarding flow
  - [x] 5.1 Remove "Copy glossary" substep from Step 1 in `senzing-bootcamp/steering/onboarding-flow.md`
    - _Requirements: 8_
  - [x] 5.2 Remove `verify-senzing-facts` from hook failure impact table in Step 1
    - _Requirements: 12_
  - [x] 5.3 Simplify Step 2 (Language Selection) to remove any MCP-unavailable conditional paths
    - _Requirements: 13_
  - [x] 5.4 Replace `GLOSSARY.md` reference in Step 4 with "ask the agent to explain any unfamiliar term"
    - _Requirements: 8_

- [x] 6. Simplify error-recovery-context hook
  - [x] 6.1 Update `error-recovery-context` hook prompt in `senzing-bootcamp/steering/hook-registry.md` to remove `.mcp_status` checks and MCP-unavailable fallback instructions; call `explain_error_code` directly for SENZ errors
    - _Requirements: 15_
  - [x] 6.2 Update `senzing-bootcamp/hooks/error-recovery-context.kiro.hook` file to match the simplified prompt (if the hook file contains the prompt directly)
    - _Requirements: 15_

- [x] 7. Replace static Senzing content with MCP instructions in steering files
  - [x] 7.1 Update `senzing-bootcamp/steering/entity-resolution-intro.md` to instruct agent to call `search_docs` dynamically instead of presenting static content
    - _Requirements: 11_
  - [x] 7.2 Update `senzing-bootcamp/steering/design-patterns.md` to instruct agent to use `search_docs` for current pattern descriptions instead of hardcoded details
    - _Requirements: 11_
  - [x] 7.3 Review language steering files (`lang-python.md`, `lang-java.md`, `lang-csharp.md`, `lang-rust.md`, `lang-typescript.md`) and replace any hardcoded SDK method names with instructions to call `get_sdk_reference`
    - _Requirements: 11_

- [x] 8. Trim documentation files
  - [x] 8.1 Update `senzing-bootcamp/POWER.md`: remove OFFLINE_MODE.md and mcp-offline-fallback.md references, add "MCP server is required" statement, replace offline troubleshooting with connection fix instructions
    - _Requirements: 6_
  - [x] 8.2 Trim `senzing-bootcamp/docs/guides/AFTER_BOOTCAMP.md`: keep maintenance cadence + adding data sources + MCP tool table; replace Scaling/Keeping Updated/Advanced Topics with MCP tool pointers
    - _Requirements: 17_
  - [x] 8.3 Trim `senzing-bootcamp/steering/common-pitfalls.md`: keep bootcamp-operational pitfalls and connectivity table; replace Senzing-specific pitfalls with "call MCP tool" instructions
    - _Requirements: 18_
  - [x] 8.4 Trim `senzing-bootcamp/docs/guides/COMMON_MISTAKES.md`: keep bootcamp-operational mistakes; replace Senzing-specific mistakes with "ask the agent" guidance
    - _Requirements: 20_
  - [x] 8.5 Trim `senzing-bootcamp/docs/guides/FAQ.md`: keep bootcamp-operational questions; replace Senzing-specific answers with "ask the agent" guidance; remove GLOSSARY.md and OFFLINE_MODE.md references
    - _Requirements: 20_

- [x] 9. Clean up cross-references
  - [x] 9.1 Update `senzing-bootcamp/docs/guides/README.md`: remove entries for all deleted files (OFFLINE_MODE, GLOSSARY, DATA_UPDATES_AND_DELETIONS, DESIGN_PATTERNS, INCREMENTAL_LOADING, MULTI_LANGUAGE_DATA, STREAMING_INTEGRATION)
    - _Requirements: 1, 8, 9_
  - [x] 9.2 Update `senzing-bootcamp/docs/README.md`: remove entries for deleted files
    - _Requirements: 1, 8, 9_
  - [x] 9.3 Update `senzing-bootcamp/docs/guides/GETTING_HELP.md`: remove GLOSSARY and OFFLINE_MODE rows from the guide table
    - _Requirements: 1, 8_
  - [x] 9.4 Update `senzing-bootcamp/docs/guides/ONBOARDING_CHECKLIST.md`: remove GLOSSARY.md reference
    - _Requirements: 8_
  - [x] 9.5 Update `senzing-bootcamp/docs/guides/PERFORMANCE_BASELINES.md`: remove "See also" links to deleted files (OFFLINE_MODE, etc.)
    - _Requirements: 1, 9_
  - [x] 9.6 Update `senzing-bootcamp/docs/guides/QUALITY_SCORING_METHODOLOGY.md`: remove "See also" link to OFFLINE_MODE
    - _Requirements: 1_
  - [x] 9.7 Update `senzing-bootcamp/docs/guides/ARCHITECTURE.md`: remove `.mcp_status` from config tables and data flow, replace "MCP Failure and Offline Fallback" section with brief "MCP is required" note, remove OFFLINE_MODE.md link
    - _Requirements: 14_
  - [x] 9.8 Update `senzing-bootcamp/steering/agent-instructions.md`: replace `GLOSSARY.md` reference with instruction to use `search_docs` for term definitions
    - _Requirements: 8_

- [x] 10. Validate changes
  - [x] 10.1 Run `python senzing-bootcamp/scripts/lint_steering.py` and confirm 0 errors
    - _Requirements: all_
  - [x] 10.2 Run `python senzing-bootcamp/scripts/sync_hook_registry.py --verify` and confirm registry is up to date
    - _Requirements: 12_
  - [x] 10.3 Run `python senzing-bootcamp/scripts/validate_power.py` and confirm no broken cross-references
    - _Requirements: 1, 8, 9_
  - [x] 10.4 Run `python senzing-bootcamp/scripts/measure_steering.py --check` and confirm token budgets pass
    - _Requirements: all_
  - [x] 10.5 Run `pytest senzing-bootcamp/tests/` and fix any test assertions that reference deleted files or removed content (GLOSSARY.md assertions, offline mode assertions, verify-senzing-facts assertions)
    - _Requirements: all_

## Notes

- PBT does not apply — this is a documentation/steering simplification with no executable logic changes
- Phase ordering matters: delete files first (Phase 1), then update references (Phases 2-9), then validate (Phase 10)
- Test fixes in 10.5 may require updating assertions in: `test_comprehension_check.py`, `test_track_selection_gate_preservation.py`, `test_onboarding_question_ownership.py`, `test_bootcamp_ux_feedback_unit.py`
- The hook count in hook-registry.md will decrease by 1 (verify-senzing-facts removal) — currently 25, will become 24
