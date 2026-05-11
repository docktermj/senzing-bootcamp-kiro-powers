# Tasks

## Task 1: Create the hook file

- [x] 1.1 Create `senzing-bootcamp/hooks/module-completion-celebration.kiro.hook` with valid JSON containing `name`, `version` (1.0.0), `description`, `when.type` = `postTaskExecution`, and `then.type` = `askAgent`
- [x] 1.2 Write the `then.prompt` field with silent-exit instruction: if `modules_completed` in `config/bootcamp_progress.json` has not changed, produce no output
- [x] 1.3 Add boundary detection logic to the prompt: read `config/bootcamp_progress.json`, identify newly completed module number from `modules_completed`
- [x] 1.4 Add celebration message instructions to the prompt: display congratulatory banner with module number and name (derived from `config/module-dependencies.yaml`), provide one-sentence summary of accomplishments
- [x] 1.5 Add next-module logic to the prompt: read `config/bootcamp_preferences.yaml` for track, determine next module from `config/module-dependencies.yaml` track definitions, offer to begin next module or display graduation acknowledgment if track is complete
- [x] 1.6 Add coexistence instructions to the prompt: mention "completion" or "journal" trigger words for the full workflow, do NOT reference `module-completion.md` for loading, do NOT include journal/certificate/reflection steps
- [x] 1.7 Add lightweight execution constraints to the prompt: no file writes, no script execution, no file-system scans, limit reads to the three allowed config files

## Task 2: Register hook in categories file

- [x] 2.1 Add `module-completion-celebration` to the `any` list in `senzing-bootcamp/hooks/hook-categories.yaml`
- [x] 2.2 Verify the identifier appears in exactly one category (no duplicates)

## Task 3: Create example-based tests

- [x] 3.1 Create `tests/test_module_completion_celebration.py` with `TestHookFileStructure` class — verify file exists, parses as valid JSON, contains all required fields, correct `when.type` and `then.type` values, valid semver version (Req 1)
- [x] 3.2 Add `TestPromptBoundaryDetection` class — verify prompt references `bootcamp_progress.json`, `modules_completed`, and contains silent-exit instruction language (Req 2)
- [x] 3.3 Add `TestPromptCelebrationMessage` class — verify prompt contains banner/congratulatory instructions, summary instructions, and references `module-dependencies.yaml` (Req 3)
- [x] 3.4 Add `TestPromptNextModule` class — verify prompt contains next-module display, offer-to-begin, graduation handling, and references both `bootcamp_preferences.yaml` and `module-dependencies.yaml` (Req 4)
- [x] 3.5 Add `TestPromptLightweightExecution` class — verify prompt does NOT contain file-writing, script-running, or scanning instructions; verify only three config files referenced (Req 5)
- [x] 3.6 Add `TestCategoriesRegistration` class — verify `module-completion-celebration` appears in `any` category and in exactly one category (Req 6)
- [x] 3.7 Add `TestPromptCoexistence` class — verify prompt does NOT load `module-completion.md`, contains "completion" and "journal" trigger words, does NOT contain journal/certificate/reflection instructions (Req 7)

## Task 4: Create property-based tests

- [x] 4.1 Add `TestRequiredFieldsValidation` class — Property 1: for any subset of required fields, validator reports exactly the missing fields (`@settings(max_examples=100)`)
- [x] 4.2 Add `TestSemverFormatValidation` class — Property 2: for any random string, version validator accepts iff it matches valid semver format (`@settings(max_examples=100)`)
- [x] 4.3 Add `TestSilentProcessingDetection` class — Property 3: for any prompt string, detector returns true iff a silent-processing phrase is present (`@settings(max_examples=100)`)
- [x] 4.4 Add `TestCategoryUniqueness` class — Property 4: for any category mapping, uniqueness checker correctly identifies duplicate hook identifiers (`@settings(max_examples=100)`)

## Task 5: Run tests and verify

- [x] 5.1 Run `pytest tests/test_module_completion_celebration.py` and verify all example-based tests pass
- [x] 5.2 Run `pytest tests/test_module_completion_celebration.py` and verify all property-based tests pass with 100+ iterations
- [x] 5.3 Run `pytest tests/` and verify the full test suite passes without regressions
