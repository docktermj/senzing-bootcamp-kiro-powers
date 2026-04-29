---
inclusion: manual
description: "Step-by-step workflow for adding a new Python script to the power"
---

# Workflow: Add a New Script

1. Create `senzing-bootcamp/scripts/<script_name>.py` following the script pattern in `python-conventions.md`.
2. Create `senzing-bootcamp/tests/test_<script_name>_properties.py` with Hypothesis PBT tests.
3. Create `senzing-bootcamp/tests/test_<script_name>_unit.py` with example-based tests and integration tests.
4. Run `python -m pytest senzing-bootcamp/tests/test_<script_name>_properties.py senzing-bootcamp/tests/test_<script_name>_unit.py -v`.
5. Update `steering-index.yaml` if the script produces or modifies steering files — run `python senzing-bootcamp/scripts/measure_steering.py` to refresh token counts.
6. If the script is user-facing, add it to the "Useful Commands" section in `POWER.md`.
7. Add a CHANGELOG entry under the current version.
