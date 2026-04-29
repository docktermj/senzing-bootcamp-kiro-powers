# Tasks

## Task 1: Add `VerificationResult` dataclass and `verify_rollback` function

- [x] 1.1 Add `VerificationResult` dataclass to `senzing-bootcamp/scripts/rollback_module.py` with fields `status: str | None` (`"passed"`, `"failed"`, or `None`) and `leftover_checks: list[str]`
- [x] 1.2 Implement `verify_rollback(module)` that imports `VALIDATORS` from `validate_module.py`, calls the validator for the given module number, inspects each `(ok, description, detail)` tuple, and returns a `VerificationResult`: status `"passed"` if all `ok` are `False`, status `"failed"` with leftover descriptions if any `ok` is `True`, or status `None` with empty leftover_checks if the validator raises an exception or the module has no validator
  _Requirements: 1.1, 1.2, 1.3, 1.4_

## Task 2: Update `RollbackLogEntry` and `build_log_entry` with verification fields

- [x] 2.1 Add `verification: str | None` and `leftover_checks: list` fields to the `RollbackLogEntry` dataclass, and update `build_log_entry` to accept optional `verification` (default `None`) and `leftover_checks` (default empty list) parameters, passing them through to the dataclass constructor
  _Requirements: 3.1, 3.2, 3.3_

## Task 3: Integrate verification into `main` flow

- [x] 3.1 In the `main` function, after artifact removal and progress update (and before log entry creation), add the verification step: if `--dry-run` is active, set `verification=None` and `leftover_checks=[]` without calling the validator; otherwise call `verify_rollback(module)` and use the result
  _Requirements: 1.1, 2.1, 2.2_
- [x] 3.2 Add stdout messages based on `VerificationResult.status`: print a green success message when status is `"passed"`, print a yellow warning listing each leftover check description when status is `"failed"`, and print a yellow warning about incomplete verification when status is `None` (non-dry-run case only)
  _Requirements: 1.2, 1.3, 1.4_
- [x] 3.3 Pass `verification` and `leftover_checks` from the `VerificationResult` to `build_log_entry` so the log entry records the verification outcome
  _Requirements: 3.1, 3.2, 3.3_

## Task 4: Property-based tests (Hypothesis)

- [x] 4.1 Create `senzing-bootcamp/tests/test_rollback_verification.py` with Hypothesis strategies for generating random module numbers (1–11), random lists of `(ok, description, detail)` validator check tuples (with ok as bool, description and detail as text strings), and random mixes of all-false and some-true check lists
- [x] 4.2 PBT: Property 1 — Validator Invocation with Correct Module: for any module number in [1, 11], verify_rollback calls the validator for exactly that module number (mock VALIDATORS to track calls) (Req 1.1)
- [x] 4.3 PBT: Property 2 — Verification Passed Output and Log: for any list of check tuples where all ok=False, verify_rollback returns status="passed" with empty leftover_checks, and the resulting log entry contains "verification": "passed" (Req 1.2, 3.1)
- [x] 4.4 PBT: Property 3 — Verification Failed Output and Log: for any list of check tuples with at least one ok=True, verify_rollback returns status="failed" with leftover_checks containing exactly the descriptions of ok=True checks, and the resulting log entry contains "verification": "failed" with the correct leftover_checks (Req 1.3, 3.2)
- [x] 4.5 PBT: Property 4 — Dry-Run Skips Verification: for any module number, when dry-run is active, the validator is not called and the log entry contains "verification": null (Req 2.1, 2.2, 3.3)

## Task 5: Example-based unit tests

- [x] 5.1 Unit test: `verify_rollback` with all checks returning ok=False returns status="passed" and empty leftover_checks
- [x] 5.2 Unit test: `verify_rollback` with mixed checks (some ok=True) returns status="failed" and correct leftover_checks list
- [x] 5.3 Unit test: `verify_rollback` when validator raises RuntimeError returns status=None and empty leftover_checks (Req 1.4)
- [x] 5.4 Unit test: `verify_rollback` when validator returns empty list returns status="passed"
- [x] 5.5 Unit test: `build_log_entry` with verification="passed" produces log entry with verification field
- [x] 5.6 Unit test: `build_log_entry` with verification="failed" and leftover_checks produces log entry with both fields
- [x] 5.7 Unit test: `build_log_entry` with verification=None produces log entry with null verification
- [x] 5.8 Unit test: `serialize_log_entry` round-trip preserves verification and leftover_checks fields
- [x] 5.9 Unit test: dry-run output does not mention verification results

## Task 6: Integration tests

- [x] 6.1 Integration test: full rollback of a module with artifacts present — artifacts removed, verification passes, log entry has verification="passed"
- [x] 6.2 Integration test: rollback with simulated leftover artifact — verification warns, log entry has verification="failed" and correct leftover_checks
- [x] 6.3 Integration test: dry-run rollback — no verification performed, log entry has verification=null
- [x] 6.4 Integration test: rollback with mocked validator exception — warning printed, rollback completes, log entry has verification=null
