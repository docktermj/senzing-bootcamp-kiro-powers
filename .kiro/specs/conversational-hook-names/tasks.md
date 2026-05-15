# Tasks: Conversational Hook Names (Bugfix)

## Phase 1: Bug Condition Exploration Test

- [x] 1.1 Write property-based test asserting all 24 hook `name` fields start with "to " followed by a lowercase verb (Property P1: Pattern Compliance). This test MUST FAIL on unfixed code, confirming the bug exists.
  - Test file: `senzing-bootcamp/tests/test_conversational_hook_names.py`
  - Requirements: 1.1, 1.2, 1.3, 1.4 (Current Behavior — Defect)
  - Validates: P1 (Conversational Pattern Compliance)
  - Bug_Condition: hook `name` fields use Title Case labels, first-person phrasing, or inconsistent patterns instead of "to {verb phrase}"
  - Expected_Behavior: every hook `name` matches `/^to [a-z]/` so UI reads "Ask Kiro Hook to {action}"

- [x] 1.2 Run the bug condition test and confirm it FAILS (proving the bug exists in unfixed code)
  - Requirements: 1.1, 1.2, 1.3, 1.4

## Phase 2: Preservation Property Tests

- [x] 2.1 Write property-based tests capturing baseline values of `version`, `description`, `when`, `then` for all 24 hooks (Properties P3, P4, P5, P6, P7). These tests MUST PASS on unfixed code, establishing the preservation baseline.
  - Test file: `senzing-bootcamp/tests/test_conversational_hook_names.py`
  - Requirements: 3.1, 3.2, 3.3, 3.4, 3.5 (Unchanged Behavior — Regression Prevention)
  - Validates: P3 (Structural Preservation), P4 (JSON Validity), P5 (Registry Consistency), P6 (No ID Mutation), P7 (CI Validation Passes)
  - Preservation: hook IDs, versions, descriptions, event types, prompts, file patterns, JSON validity, and CI validation must remain unchanged

- [x] 2.2 Run the preservation tests and confirm they PASS on unfixed code (establishing the baseline)
  - Requirements: 3.1, 3.2, 3.3, 3.4, 3.5

## Phase 3: Implementation

- [x] 3.1 Update all 24 `.kiro.hook` files — change only the `name` field per the mapping table in design.md §7.1
  - Requirements: 2.1, 2.2, 2.3, 2.4
  - Bug_Condition: `name` fields are jargony implementation labels
  - Expected_Behavior: `name` fields follow "to {verb phrase}" pattern
  - Preservation: `version`, `description`, `when`, `then` fields unchanged
  - Changes:
    1. ask-bootcamper: "Ask Bootcamper" → "to wait for your answer"
    2. review-bootcamper-input: "Review Bootcamper Input" → "to review what you said"
    3. code-style-check: "Code Style Check" → "to check code style"
    4. commonmark-validation: "CommonMark Validation" → "to check Markdown style"
    5. enforce-file-path-policies: "I will make sure the file is in the project directory" → "to make sure the file is in the project directory"
    6. validate-business-problem: "Validate Business Problem" → "to validate your business problem"
    7. verify-sdk-setup: "Verify SDK Setup" → "to verify SDK setup"
    8. verify-demo-results: "Verify Demo Results" → "to verify demo results"
    9. validate-data-files: "Validate Data Files" → "to validate data files"
    10. data-quality-check: "Senzing Data Quality Check" → "to check data quality"
    11. analyze-after-mapping: "Analyze After Mapping" → "to analyze mapped data"
    12. enforce-mapping-spec: "Enforce Mapping Specification" → "to enforce the mapping specification"
    13. backup-before-load: "Backup Database Before Loading" → "to remind you to back up before loading"
    14. run-tests-after-change: "Run Tests After Code Change" → "to remind you to run tests"
    15. verify-generated-code: "Verify Generated Code Runs" → "to verify generated code"
    16. enforce-visualization-offers: "Enforce Visualization Offers" → "to offer visualizations"
    17. validate-benchmark-results: "Validate Benchmark Results" → "to validate benchmark results"
    18. security-scan-on-save: "Security Scan on Save" → "to run a security scan"
    19. validate-alert-config: "Validate Alert Configuration" → "to validate alert configuration"
    20. deployment-phase-gate: "Deployment Phase Gate" → "to check the deployment phase gate"
    21. backup-project-on-request: "Backup Project on Request" → "to back up your project"
    22. error-recovery-context: "Auto-Load Error Recovery Context" → "to help recover from errors"
    23. git-commit-reminder: "Git Commit Reminder" → "to remind you to commit"
    24. module-completion-celebration: "Module Completion Celebration" → "to celebrate module completion"

- [x] 3.2 Update `senzing-bootcamp/steering/hook-registry.md` — change all `name:` lines to match new names
  - Requirements: 2.5, 3.4
  - Bug_Condition: registry `name:` lines use old jargony labels
  - Expected_Behavior: registry `name:` lines match new "to {verb phrase}" names in hook files
  - Preservation: `id`, `description`, and `Prompt` sections unchanged

- [x] 3.3 Add style guide section to `senzing-bootcamp/hooks/README.md` documenting the "to {verb phrase}" naming convention
  - Requirements: 2.5
  - Expected_Behavior: contributors have a documented style guide for the `name` field

- [x] 3.4 Verify `senzing-bootcamp/steering/onboarding-flow.md` references hooks by `id` (not by `name`) — confirm no changes needed
  - Requirements: 3.3
  - Preservation: onboarding flow continues to install the same set of hooks with the same event types

- [x] 3.5 Re-run bug condition test (Phase 1) — should now PASS
  - Requirements: 2.1, 2.2, 2.3, 2.4
  - Expected_Behavior: all 24 hook names now match the "to {verb phrase}" pattern

- [x] 3.6 Re-run preservation tests (Phase 2) — should still PASS
  - Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
  - Preservation: no regressions introduced by the name changes

## Phase 4: Checkpoint

- [x] 4.1 Run full test suite (`pytest senzing-bootcamp/tests/test_conversational_hook_names.py -v`)
  - Requirements: 2.1–2.5, 3.1–3.5
  - All property tests pass: P1 (pattern compliance), P3 (structural preservation), P4 (JSON validity), P5 (registry consistency), P6 (no ID mutation)

- [x] 4.2 Run CI validation (`python senzing-bootcamp/scripts/sync_hook_registry.py --verify`)
  - Requirements: 3.4
  - Validates: P7 (CI Validation Passes) — registry and hook files remain in sync after name changes
