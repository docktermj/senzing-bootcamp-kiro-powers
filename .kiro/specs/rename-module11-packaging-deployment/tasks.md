# Implementation Plan: Rename Module 11 — Packaging and Deployment

## Overview

Coordinated search-and-replace across 8 files plus one file rename to change Module 11's display name from "Deployment and Packaging" to "Packaging and Deployment". No new files created, no new dependencies. Tests are example-based (deterministic replacements — PBT does not apply).

## Tasks

- [x] 1. Write verification tests for the rename
  - [x] 1.1 Add a test class `TestRenameModule11` in `senzing-bootcamp/tests/test_module_closing_question_ownership.py` (or a new test file `senzing-bootcamp/tests/test_rename_module11.py`)
    - Assert `MODULE_11_PACKAGING_DEPLOYMENT.md` exists and `MODULE_11_DEPLOYMENT_PACKAGING.md` does not
    - Assert steering heading is `# Module 11: Packaging and Deployment`
    - Assert steering Module_Doc reference uses `MODULE_11_PACKAGING_DEPLOYMENT.md`
    - Assert `docs/modules/README.md` links to `MODULE_11_PACKAGING_DEPLOYMENT.md`
    - Assert `docs/README.md` references `MODULE_11_PACKAGING_DEPLOYMENT.md` with description "Packaging and deployment"
    - Assert `templates/stakeholder_summary.md` uses "Packaging and Deployment" in section header and placeholder
    - Assert `templates/stakeholder_summary.md` Module 10 next-steps says "packaging and deployment (Module 11)"
    - Assert `steering/graduation-reference.md` uses "packaging and deployment" in both checklist lines
    - Assert `docs/diagrams/module-prerequisites.md` label is `Module 11: Package & Deploy` (no "Monitoring")
    - Assert preserved files (`POWER.md`, `steering-index.yaml`, steering filename) are unchanged
    - _Requirements: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10_

- [x] 2. Rename the module documentation file
  - [x] 2.1 Rename `senzing-bootcamp/docs/modules/MODULE_11_DEPLOYMENT_PACKAGING.md` to `senzing-bootcamp/docs/modules/MODULE_11_PACKAGING_DEPLOYMENT.md`
    - File content stays unchanged — the internal heading `# Module 11: Package and Deploy` and banner already use the correct order
    - _Requirements: 2.1, 2.2_

- [x] 3. Update text references across all files
  - [x] 3.1 Update steering file heading and Module_Doc reference in `senzing-bootcamp/steering/module-11-deployment.md`
    - Change heading from `# Module 11: Deployment and Packaging` to `# Module 11: Packaging and Deployment`
    - Change Module_Doc reference from `MODULE_11_DEPLOYMENT_PACKAGING.md` to `MODULE_11_PACKAGING_DEPLOYMENT.md`
    - Preserve the user message text `"Module 11 has two phases. First we'll package your code."` unchanged
    - _Requirements: 1.1, 1.2, 2.3_

  - [x] 3.2 Update module documentation index in `senzing-bootcamp/docs/modules/README.md`
    - Change file link from `MODULE_11_DEPLOYMENT_PACKAGING.md` to `MODULE_11_PACKAGING_DEPLOYMENT.md`
    - _Requirements: 3.1_

  - [x] 3.3 Update docs README file listing in `senzing-bootcamp/docs/README.md`
    - Change filename from `MODULE_11_DEPLOYMENT_PACKAGING.md` to `MODULE_11_PACKAGING_DEPLOYMENT.md`
    - Change description from "Deployment packaging" to "Packaging and deployment"
    - _Requirements: 4.1, 4.2_

  - [x] 3.4 Update stakeholder summary template in `senzing-bootcamp/templates/stakeholder_summary.md`
    - Change Module 11 section header from `MODULE 11 — Deployment and Packaging` to `MODULE 11 — Packaging and Deployment`
    - Change `[module_name]` placeholder value from `"Deployment and Packaging"` to `"Packaging and Deployment"`
    - Change Module 10 next-steps from `Proceed to deployment packaging (Module 11)` to `Proceed to packaging and deployment (Module 11)`
    - _Requirements: 5.1, 9.1_

  - [x] 3.5 Update graduation reference in `senzing-bootcamp/steering/graduation-reference.md`
    - Change first checklist line from `Review deployment packaging from Module 11` to `Review packaging and deployment from Module 11`
    - Change second checklist line from `Deployment packaging was not covered` to `Packaging and deployment was not covered`
    - _Requirements: 6.1_

  - [x] 3.6 Fix module prerequisites diagram in `senzing-bootcamp/docs/diagrams/module-prerequisites.md`
    - Change Mermaid label from `Module 11: Monitoring, Package & Deploy` to `Module 11: Package & Deploy`
    - _Requirements: 7.1_

- [x] 4. Update test heading constant
  - [x] 4.1 Update `_HEADINGS_MODULE_11` in `senzing-bootcamp/tests/test_module_closing_question_ownership.py`
    - Change first entry from `"# Module 11: Deployment and Packaging"` to `"# Module 11: Packaging and Deployment"`
    - _Requirements: 8.1_

- [x] 5. Checkpoint — Run full test suite
  - Ensure all tests pass with `pytest senzing-bootcamp/tests/ -v`, ask the user if questions arise.
  - Verify zero failures related to Module 11 heading or filename references
  - _Requirements: 11.1_

## Notes

- No property-based tests — this is deterministic search-and-replace with no input space to vary
- Preserved files: `POWER.md`, `steering-index.yaml`, and the steering filename `module-11-deployment.md` must NOT be modified
- The module doc's internal heading (`# Module 11: Package and Deploy`) and banner (`MODULE 11: PACKAGE AND DEPLOY`) already use the correct order and must not change
- Python 3.11+, stdlib only, pytest for tests
