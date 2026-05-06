# Tasks: Module Completion Certificates

## Task 1: Update module-completion.md with certificate generation step

- [x] 1.1 Read the current `senzing-bootcamp/steering/module-completion.md` to understand the completion workflow
- [x] 1.2 Add a certificate generation step after the completion celebration: instruct the agent to generate `docs/progress/MODULE_N_COMPLETE.md`
- [x] 1.3 Add instructions for the certificate content: read module steering file for concepts, scan file system for artifacts, check session analytics for stats
- [x] 1.4 Add instructions to create/update `docs/progress/README.md` summary index after each certificate
- [x] 1.5 Document that certificate generation should not block the completion flow — if it fails, log a warning and continue

## Task 2: Define certificate template in steering

- [x] 2.1 Add the certificate template format to `module-completion.md` showing all sections: title, date, time, language, concepts, artifacts, what this enables, session stats
- [x] 2.2 Document content derivation rules: concepts from steering file, artifacts from file system, capabilities from module-dependencies.yaml
- [x] 2.3 Document the language-aware description rule: use the bootcamper's chosen language in artifact descriptions
- [x] 2.4 Document that "Session Stats" section is only included when session analytics are available

## Task 3: Update export_results.py to include certificates

- [x] 3.1 Read the current `senzing-bootcamp/scripts/export_results.py` to understand its export structure
- [x] 3.2 Add logic to check for `docs/progress/` directory existence
- [x] 3.3 For HTML export: add an "Achievements" section containing certificate content
- [x] 3.4 For ZIP export: include `docs/progress/` contents under `artifacts/progress/`
- [x] 3.5 Handle gracefully when no certificates exist (skip the section, don't error)

## Task 4: Write tests

- [x] 4.1 Create `senzing-bootcamp/tests/test_module_completion_certificates.py`
- [x] 4.2 Unit test: module-completion.md contains certificate generation instruction
- [x] 4.3 Unit test: module-completion.md contains README.md index update instruction
- [x] 4.4 Unit test: certificate template in module-completion.md contains all required sections (Key Concepts, Artifacts Produced, What This Enables)
- [x] 4.5 Property test: certificate filename pattern MODULE_N_COMPLETE.md is valid for all module numbers 1-11
- [x] 4.6 Unit test: export_results.py handles missing docs/progress/ directory without error
- [x] 4.7 Unit test: module-completion.md specifies language-aware artifact descriptions

## Task 5: Validate

- [x] 5.1 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` on modified files
- [x] 5.2 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check`
- [x] 5.3 Run `pytest senzing-bootcamp/tests/test_module_completion_certificates.py -v`
- [x] 5.4 Run existing export_results tests to confirm no regressions
