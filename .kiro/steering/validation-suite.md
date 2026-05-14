---
inclusion: auto
description: "Step-by-step workflow for running the full CI validation suite locally"
---

# Workflow: Run the Full Validation Suite

Run these in order. All must pass before merging to main.

```bash
# 1. Power integrity (cross-references, hooks, steering files)
python senzing-bootcamp/scripts/validate_power.py

# 2. Steering token counts match stored values (±10%)
python senzing-bootcamp/scripts/measure_steering.py --check

# 3. CommonMark compliance
python senzing-bootcamp/scripts/validate_commonmark.py

# 4. Hook registry generated from hook files matches on-disk registry
python senzing-bootcamp/scripts/sync_hook_registry.py --verify

# 5. Module dependency graph consistency
python senzing-bootcamp/scripts/validate_dependencies.py

# 6. Steering file linter (structural checks)
python senzing-bootcamp/scripts/lint_steering.py

# 7. All tests (power tests + repo-level hook tests)
python -m pytest senzing-bootcamp/tests/ tests/ -v --tb=short
```

If `measure_steering.py --check` fails, run `measure_steering.py` (no flag) to update counts.
If `sync_hook_registry.py --verify` fails, run `sync_hook_registry.py --write` to regenerate.
