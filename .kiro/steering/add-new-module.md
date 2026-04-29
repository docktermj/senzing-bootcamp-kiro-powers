---
inclusion: manual
---

# Workflow: Add a New Bootcamp Module

1. Choose the module number N (zero-padded: `NN`). Check `senzing-bootcamp/config/module-dependencies.yaml` for the next available number.

2. Create the steering file from the template:
   - Copy `senzing-bootcamp/templates/module-steering-template.md` to `senzing-bootcamp/steering/module-NN-description.md`
   - Replace `NN`, `[Module Title]`, and all placeholder values
   - Set `inclusion: manual` in frontmatter

3. Create the companion doc at `senzing-bootcamp/docs/modules/MODULE_N_TITLE.md`.

4. Update `senzing-bootcamp/config/module-dependencies.yaml`:
   - Add the module under `modules:` with `name`, `requires`, `skip_if`
   - Add the gate under `gates:` (e.g., `"N-1->N"`)
   - Update any tracks that should include this module
   - Run `python senzing-bootcamp/scripts/validate_dependencies.py` to verify

5. Update `senzing-bootcamp/steering/steering-index.yaml`:
   - Add the module under `modules:`
   - Run `python senzing-bootcamp/scripts/measure_steering.py` to add `file_metadata`

6. Update `senzing-bootcamp/steering/module-prerequisites.md` table.

7. Update `POWER.md` module table and steering file list.

8. Run `python senzing-bootcamp/scripts/lint_steering.py` to verify template conformance.

9. Add a CHANGELOG entry.
