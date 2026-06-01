# Implementation Plan

## Overview

Fix Rule 6 violation in the three license-insufficient steering paths so each contains a
defined, enforced `search_docs` MCP consultation step (not prose-only) for
temporary/larger evaluation license guidance. The fix is steering-markdown only across two
files:

- `senzing-bootcamp/steering/module-01-business-problem.md` — Step 6d ("does not have
  license" branch).
- `senzing-bootcamp/steering/module-02-sdk-setup.md` — Step 5a (built-in evaluation license
  explanation) and Step 5c "no license" branch.

Two new property-based test files (pytest + Hypothesis, stdlib + Hypothesis only) validate
the fix: an exploration suite (Property 1 — Fix Checking) authored to FAIL on the unfixed
files, and a preservation suite (Property 2 — Preservation Checking) authored to PASS on
the unfixed files. No MCP server URL is hardcoded in steering files or tests, and the
referenced tool name (`search_docs`) is validated against `mcp-tool-decision-tree.md`.

## Tasks

- [x] 1. Write bug condition exploration test (Fix Checking)
  - **Property 1: Bug Condition** - Enforced MCP Consultation on Insufficient License
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists in the current steering files
  - **Scoped PBT Approach**: Scope the property to the three license-insufficient sections — Module 1 Step 6d, Module 2 Step 5a, and Module 2 Step 5c "no license" branch
  - Create `senzing-bootcamp/tests/test_mcp_temporary_license_consultation_exploration.py`
  - Use `from __future__ import annotations`, class-based organization, type hints (`X | None`, `list[str]`), `st_`-prefixed strategies, and `@settings(max_examples=20)` per `python-conventions.md`
  - Define `LicenseSituation` dataclass `{ total_record_count: int, has_sufficient_license: bool, error_code: str | None }` and `is_bug_condition(x) -> bool` returning `(x.total_record_count > 500 or x.error_code == "SENZ9000") and not x.has_sufficient_license`
  - Add `st_license_situation()` composite strategy drawing `total_record_count` (0–10_000_000), `has_sufficient_license` (booleans), and `error_code` (`None`, `"SENZ9000"`, `"SENZ0002"`)
  - Implement section extraction helpers: `_extract_6d(content)` (slice Module 1 between `**6d.` and `**6e.`), `_extract_5a(content)` (slice Module 2 between `### 5a` and `### 5b`), and `_extract_5c_no_license(content)` (slice between `### 5c` and `### 5d`, then isolate the "IF the bootcamper has no license" block)
  - Implement content predicates: `_has_enforced_mcp_step(section)` (true only if `search_docs` appears AND an imperative directive such as `call`/`consult` is present), `_is_prose_only(section)` (true if it mentions the MCP server but names no MCP tool), `_tool_name_is_confirmed(name)` (parse the tool set from `mcp-tool-decision-tree.md` and confirm `name` resolves there), and `_no_mcp_url(section)` (assert no MCP server URL and no `http`/`https` URL is present)
  - Property test (map each bug-condition `LicenseSituation` to its steering path): assert `_has_enforced_mcp_step(path)` AND `_tool_name_is_confirmed("search_docs")` AND NOT `_is_prose_only(path)` AND `_no_mcp_url(path)`
  - Example-based tests covering each path explicitly: Module 1 Step 6d names `search_docs` in a directive; Module 2 Step 5a names `search_docs` in a directive; Module 2 Step 5c "no license" names `search_docs` in a directive; SENZ9000-capacity routing reaches a `search_docs` consultation
  - **DO NOT** hardcode any MCP server URL in the test (security hook blocks it); validate the tool name by parsing `mcp-tool-decision-tree.md`
  - Run test on UNFIXED code with `pytest senzing-bootcamp/tests/test_mcp_temporary_license_consultation_exploration.py`
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - 6d has no MCP mention at all; 5a and 5c are prose-only "MCP server can guide you…" with no tool named)
  - Document counterexamples found (e.g., "Module 1 Step 6d contains no MCP tool reference"; "Module 2 Step 5a mentions MCP server but names no tool → prose-only")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Sufficient-License Paths and Structural Invariants Unchanged
  - **IMPORTANT**: Follow observation-first methodology — observe behavior on UNFIXED files, then assert it is preserved
  - **IMPORTANT**: Write these tests BEFORE implementing the fix
  - Create `senzing-bootcamp/tests/test_mcp_temporary_license_consultation_preservation.py`
  - Use `from __future__ import annotations`, class-based organization, type hints, `st_`-prefixed strategies, and `@settings(max_examples=20)` per `python-conventions.md`
  - Observe on UNFIXED files and snapshot via SHA-256: Module 2 Steps 1–4 and 6–9 (non-license sections), Module 1 Step 6a/6b/6c/6e sections, and the Module 2 Step 5c "has license" branches (Base64 decode → `licenses/g2.lic`, "NEVER paste license key" warning, `PIPELINE.LICENSEFILE` JSON, `license: custom` / `license: evaluation` recording)
  - Store observed hashes as a `_BASELINE_HASHES` constant (mirroring the `_STEP_HASHES` snapshot pattern) and assert post-fix content matches
  - Reuse `LicenseSituation`, `is_bug_condition`, and `st_license_situation()` (import or redefine) and add a preservation property: for all `NOT is_bug_condition(x)` situations (records ≤ 500 or sufficient license), the sufficient-license paths and snapshotted invariants are byte-identical to baseline
  - Example-based preservation assertions: Module 1 Step 6a still skips 6b–6e and proceeds to Step 7 for ≤ 500 records; Module 1 sub-steps 6b and 6d retain exactly their existing 👉 questions and 🛑 STOP markers (no new 👉/🛑 added)
  - Module 2 Step 5 invariants: exactly one 👉 (the 5b question) and exactly one `\bSTOP\b` in Step 5; the "⛔ MANDATORY GATE — Never skip this step…" marker and the license-check order callout are unchanged
  - License mechanics + contacts preserved: `support@senzing.com` and `sales@senzing.com` present where they currently appear, `licenses/README.md` reference present, and the Step 5 / Step 6d checkpoints unchanged
  - Frontmatter preserved: both files retain `inclusion: manual`
  - Security preservation: assert no MCP server URL and no new `http`/`https` URL appears in the edited sections
  - **DO NOT** hardcode any MCP server URL in the test (security hook blocks it)
  - Run tests on UNFIXED code with `pytest senzing-bootcamp/tests/test_mcp_temporary_license_consultation_preservation.py`
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 3. Fix for prose-only MCP licensing guidance on insufficient-license paths

  - [x] 3.1 Add enforced MCP consultation to Module 1 Step 6d
    - Edit `senzing-bootcamp/steering/module-01-business-problem.md`, Step 6d ("does not have license" branch)
    - Add an enforced MCP consultation directive (imperative, not a 👉 question) that instructs the agent to call `search_docs` with a concrete query for a temporary/larger evaluation license (records exceed the 500-record limit), placed alongside the existing email path; present the returned guidance, then continue with the email path
    - Preserve the existing email guidance (`support@senzing.com`, what to provide, turnaround), the 👉 deferral question, its 🛑 STOP marker, the wait/defer→6e/received→6c branch routing, and the `**Checkpoint:** Write step 6d` instruction
    - Do NOT add a new 👉 question or a new 🛑 STOP to 6d; reference the MCP capability by tool name only — no URL
    - _Bug_Condition: isBugCondition(X) where X.totalRecordCount > 500 AND NOT X.hasSufficientLicense (Module 1 Step 6d path)_
    - _Expected_Behavior: path defines an enforced search_docs consultation for temporary/larger license guidance (Property 1)_
    - _Preservation: email contacts, 👉 deferral question, 🛑 STOP, branch routing, and 6d checkpoint unchanged (Preservation Requirements)_
    - _Requirements: 2.1, 2.4, 2.5_

  - [x] 3.2 Replace prose-only MCP mention with enforced consultation in Module 2 Step 5a
    - Edit `senzing-bootcamp/steering/module-02-sdk-setup.md`, Step 5a ("Explain the built-in evaluation license")
    - Replace the prose-only line "You can also request a larger evaluation license directly through the Senzing MCP server…" with an enforced directive to call `search_docs` with a concrete query for a larger/temporary evaluation license, positioned AFTER the 500-record / SENZ9000 explanation; present the returned guidance
    - Preserve the "500 records", "SENZ9000", and "`licenses/g2.lic`" content in 5a (ordering: MCP directive appears after the SENZ9000/500-record content)
    - Reference the MCP capability by tool name only — no URL
    - _Bug_Condition: isBugCondition(X) where X.totalRecordCount > 500 OR X.errorCode = "SENZ9000" (Module 2 Step 5a path)_
    - _Expected_Behavior: path defines an enforced search_docs consultation rather than passive prose (Property 1)_
    - _Preservation: 500/SENZ9000/licenses/g2.lic content and its ordering unchanged (Preservation Requirements)_
    - _Requirements: 2.2, 2.4, 2.5_

  - [x] 3.3 Replace prose-only MCP mention with enforced consultation in Module 2 Step 5c "no license" branch
    - Edit `senzing-bootcamp/steering/module-02-sdk-setup.md`, Step 5c "IF the bootcamper has no license" branch
    - Replace the prose-only line "Alternatively, the Senzing MCP server can guide you through requesting a larger evaluation license interactively." with an enforced directive to call `search_docs` with a concrete query for a larger evaluation license, kept alongside the existing `support@senzing.com` / `sales@senzing.com` contacts and the `licenses/README.md` reference
    - Preserve the "built-in 500-record evaluation license is active" confirmation, both email contacts, the `licenses/README.md` reference, and the `license: evaluation` preference recording
    - Maintain exactly one 👉 question (5b) and exactly one STOP in Step 5 — the MCP consultation is an imperative directive, never a 👉 question or a STOP; reference the MCP capability by tool name only — no URL
    - _Bug_Condition: isBugCondition(X) where NOT X.hasSufficientLicense (Module 2 Step 5c "no license" path)_
    - _Expected_Behavior: path defines an enforced search_docs consultation alongside email contacts (Property 1)_
    - _Preservation: confirmation, email contacts, licenses/README.md, license: evaluation recording, single 👉 + single STOP in Step 5 unchanged (Preservation Requirements)_
    - _Requirements: 2.3, 2.4, 2.5_

  - [x] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Enforced MCP Consultation on Insufficient License
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior; when it passes, the enforced `search_docs` consultation is confirmed present in all three paths
    - Run `pytest senzing-bootcamp/tests/test_mcp_temporary_license_consultation_exploration.py`
    - **EXPECTED OUTCOME**: Test PASSES (confirms the bug is fixed in Module 1 Step 6d, Module 2 Step 5a, and Module 2 Step 5c "no license")
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Sufficient-License Paths and Structural Invariants Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run `pytest senzing-bootcamp/tests/test_mcp_temporary_license_consultation_preservation.py`
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — sufficient-license paths, ⛔ gate, single 👉 + single STOP in Step 5, license mechanics, email contacts, README reference, and `inclusion: manual` frontmatter all unchanged)
    - Confirm all tests still pass after the fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run the new suites: `pytest senzing-bootcamp/tests/test_mcp_temporary_license_consultation_exploration.py senzing-bootcamp/tests/test_mcp_temporary_license_consultation_preservation.py`
  - Run the existing regression suite for the two edited files: `pytest senzing-bootcamp/tests/test_licensing_guidance.py senzing-bootcamp/tests/test_license_step_mandatory.py senzing-bootcamp/tests/test_module2_license_question.py`
  - Run CI structural validators on the edited files: `python senzing-bootcamp/scripts/validate_commonmark.py` and `python senzing-bootcamp/scripts/measure_steering.py --check` (token budgets in `steering-index.yaml` remain within limits)
  - Confirm no MCP server URL was introduced into either steering file
  - Ensure all tests pass, ask the user if questions arise.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1", "2"] },
    { "id": 1, "tasks": ["3.1", "3.2", "3.3"] },
    { "id": 2, "tasks": ["3.4", "3.5"] },
    { "id": 3, "tasks": ["4"] }
  ]
}
```

## Notes

- Tests use pytest + Hypothesis (property-based testing), stdlib + Hypothesis only, in `senzing-bootcamp/tests/` per `tech.md` and `python-conventions.md`
- The exploration test (task 1) is expected to FAIL on unfixed code — this confirms the bug exists across all three license-insufficient paths
- The preservation test (task 2) is expected to PASS on unfixed code — this captures baseline behavior to preserve
- After the fix (tasks 3.1–3.3), both suites should PASS
- The fix is steering-markdown only across two files; no Python/runtime code is involved
- `search_docs` is the file-confirmed tool (validated against `mcp-tool-decision-tree.md`); no MCP server URL is hardcoded in steering files or tests (security hook blocks it)
