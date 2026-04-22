# Tasks

## Task 1: Onboarding Sequence Steering File

- [x] 1.1 Create `senzing-bootcamp/steering/onboarding-flow.md` with the full 6-step sequence: setup preamble, directory creation, language selection, prerequisite checks, welcome banner + introduction, path selection
- [x] 1.2 Add setup preamble (Step 0) telling the user administrative setup is happening and a WELCOME banner will signal the start
- [x] 1.3 Define directory creation (Step 1): project structure creation, hook installation, glossary copy, foundational steering file generation (product.md, tech.md, structure.md)
- [x] 1.4 Define language selection (Step 2) with MCP-driven platform detection, supported language query, platform warnings, and persistence to `config/bootcamp_preferences.yaml`
- [x] 1.5 Define prerequisite check (Step 3) using `shutil.which()` for runtime detection and Senzing SDK import check, reporting only missing items
- [x] 1.6 Define welcome banner (Step 4) with 🎓 emojis, bootcamp overview, module table, and mock data/licensing info
- [x] 1.7 Define path selection (Step 5) with four paths (A: Quick Demo, B: Fast Track, C: Complete Beginner, D: Full Production) and auto-insertion of Module 0

## Task 2: Communication Rules in Agent Instructions

- [x] 2.1 Add one-question-at-a-time rule with WAIT markers to `senzing-bootcamp/steering/agent-instructions.md` Communication section
- [x] 2.2 Add 👉 input-required marker rule for all questions requiring user response
- [x] 2.3 Add Goldilocks detail check rule: ask after modules 3, 6, and 9, persist `detail_level` to `config/bootcamp_preferences.yaml`
- [x] 2.4 Add first-term explanation rule: define Senzing terms inline on first use, reference `docs/guides/GLOSSARY.md`, do not re-explain

## Task 3: Validation Gates and State Management

- [x] 3.1 Define validation gate table in `onboarding-flow.md` with gate criteria for all module transitions (0→1 through 11→12)
- [x] 3.2 Define gate execution: run `validate_module.py --module N` before progression, update `bootcamp_progress.json`
- [x] 3.3 Define path switching logic: completed modules carry forward, resume from first incomplete module
- [x] 3.4 Define session entry logic in `agent-instructions.md`: check `bootcamp_progress.json` existence to decide between `onboarding-flow.md` and `session-resume.md`

## Task 4: Foundational Steering File Generation

- [x] 4.1 Define generation of `product.md` (inclusion: always) during onboarding Step 1
- [x] 4.2 Define generation of `tech.md` (inclusion: always) during onboarding Step 1
- [x] 4.3 Define generation of `structure.md` (inclusion: auto) during onboarding Step 1
- [x] 4.4 Ensure glossary copy (`GLOSSARY.md` → `docs/guides/`) happens before Step 4 references it
