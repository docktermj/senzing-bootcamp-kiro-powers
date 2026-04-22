# Tasks

## Task 1: State Reconstruction and Language Loading

- [x] 1.1 Define Step 1 in `senzing-bootcamp/steering/session-resume.md`: read `config/bootcamp_progress.json`, `config/bootcamp_preferences.yaml`, `docs/bootcamp_journal.md`, and any `config/mapping_state_*.json` files
- [x] 1.2 Define Step 2: map the `language` field from preferences to the corresponding language steering file (`lang-python.md`, `lang-java.md`, `lang-csharp.md`, `lang-rust.md`, `lang-typescript.md`)
- [x] 1.3 Add corrupted/missing state handling: inform the Bootcamper and offer to reconstruct from project artifacts in `src/`, `data/`, `docs/`

## Task 2: Welcome-Back Summary and User Confirmation

- [x] 2.1 Define Step 3: display "🎓 Welcome back to the Senzing Bootcamp!" banner followed by a concise summary (path, language, completed modules, current module, database, data sources)
- [x] 2.2 Add mapping checkpoint mention: if `config/mapping_state_*.json` files exist, include in-progress data source and completed steps in the summary
- [x] 2.3 Add 👉 "Ready to continue with Module [N]?" prompt with WAIT marker for user response

## Task 3: Module Loading and MCP Re-establishment

- [x] 3.1 Define Step 4: load current module steering on confirmation, verify prerequisites on module switch, confirm and load `onboarding-flow.md` on start-over
- [x] 3.2 Define Step 5: call `get_capabilities` to re-establish MCP session context after module steering is loaded

## Task 4: Stale State Validation and Correction

- [x] 4.1 Add stale state detection: when `bootcamp_progress.json` claims completion but artifacts are missing, run `python scripts/validate_module.py`
- [x] 4.2 Display discrepancies to the Bootcamper and offer to correct `bootcamp_progress.json` based on actual artifact state
- [x] 4.3 Resume from the last verifiably complete module after corrections are accepted
