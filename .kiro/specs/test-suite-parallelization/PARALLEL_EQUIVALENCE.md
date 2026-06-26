# Test suite: parallel execution & equivalence

Developer/maintainer note for the senzing-bootcamp test suite. This is **not**
user-facing bootcamp content, so it lives in the spec directory rather than under
`senzing-bootcamp/`.

The suite runs serially by default locally and in parallel in CI. The two modes
**must** produce the same pass/fail outcome. This note describes how to verify that
equivalence and how divergence is handled.

## Background

- `pytest-xdist` is pinned in `requirements-dev.txt` (`pytest-xdist==3.7.0`).
- `-n` is intentionally **not** in `addopts` (`[tool.pytest.ini_options]` in
  `pyproject.toml`), so local runs are serial-by-default. This keeps clean
  tracebacks and `pdb` for debugging.
- Parallelism is opted into explicitly: CI runs `-n auto --dist loadgroup`. The
  green parallel CI matrix (Python 3.11/3.12/3.13) is the standing equivalence
  guard.

## Verifying parallel-vs-serial equivalence

Run both commands against the **same commit** and diff the passing/failing sets.

Serial baseline:

```bash
HYPOTHESIS_PROFILE=thorough python -m pytest senzing-bootcamp/tests/ tests/
```

Parallel:

```bash
HYPOTHESIS_PROFILE=thorough python -m pytest senzing-bootcamp/tests/ tests/ -n auto --dist loadgroup
```

Compare the set of passing and failing tests between the two runs. They must be
identical. A practical way to capture each set is to record the per-test results
(for example with `-rA` or by writing a report) and diff them.

## Verifying determinism

Run the parallel suite **twice on an unchanged commit** and confirm identical
results:

```bash
HYPOTHESIS_PROFILE=thorough python -m pytest senzing-bootcamp/tests/ tests/ -n auto --dist loadgroup
HYPOTHESIS_PROFILE=thorough python -m pytest senzing-bootcamp/tests/ tests/ -n auto --dist loadgroup
```

Both runs must report the same pass/fail result.

## Handling divergence

Any test whose outcome differs between parallel and serial (or between two parallel
runs) is treated as a `Non_Parallel_Safe_Test` and remediated under Task 5 of this
spec:

- Prefer per-test path isolation via `tmp_path` / `tmp_path_factory` (worker-unique
  under xdist) or `monkeypatch.chdir(tmp_path)`.
- If isolation is infeasible, pin the test to a single worker with
  `@pytest.mark.serial` plus `@pytest.mark.xdist_group("serial")`, which is honored
  under `--dist loadgroup`.

After remediation, re-run the parallel suite to confirm the divergence is resolved.
