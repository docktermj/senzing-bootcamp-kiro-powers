# License-Aware Sampling Bugfix Design

## Overview

The senzing-bootcamp Kiro Power hardcodes the built-in ~500-record evaluation license limit at every sampling and capacity decision point. When a custom license is configured (in Module 2), the agent never calls `SzProduct.get_license()` to read the active license's real `recordLimit`. This causes unnecessary downsampling recommendations, incorrect capacity claims ("SENZ9000 at record 501"), and an under-loaded entity resolution graph — degrading the core fraud/due-diligence deliverable.

The fix introduces a license-detection step after Module 2 license setup, persists the detected `recordLimit` to `config/bootcamp_progress.json`, and makes every downstream capacity/sampling decision read from that persisted value (or call `get_license()` afresh when needed). The hardcoded 500 figure remains the default only when no custom license is present. A small stdlib-only helper script validates and persists the detected license limit. All Senzing SDK facts continue to come from the Senzing MCP server.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — a custom Senzing license is configured AND a sampling/capacity decision point is reached, yet the agent uses the hardcoded 500 figure instead of querying the active license.
- **Property (P)**: The desired behavior when the bug condition holds — the agent reads the active license's `recordLimit` via `SzProduct.get_license()` and drives the decision from that value (0 means no cap).
- **Preservation**: Existing evaluation-license behavior, non-license uses of the number 500 (volume tiers, SQLite performance guidance, visualization entity cap), mouse/keyboard flows, and the MCP-sourced-facts rule must remain unchanged.
- **`get_license()`**: The `SzProduct.get_license()` SDK call that returns a JSON blob including `recordLimit`, license type, and expiry date. SDK facts about this call come from the Senzing MCP server.
- **`recordLimit`**: The integer field in the license JSON. A value of `0` means no record cap; a positive integer means the cap is that many records.
- **`config/bootcamp_progress.json`**: The per-session progress file; the fix adds a `license_record_limit` field to persist the detected limit for cross-module reuse.
- **Steering files**: The Markdown files in `senzing-bootcamp/steering/` that control agent behavior at each module step.

## Bug Details

### Bug Condition

The bug manifests when a custom Senzing license has been configured in Module 2 AND the agent reaches any sampling or capacity decision point (Module 1 Step 6a, Module 4 Step 6, Module 6 loading, Module 8 performance). The agent compares the dataset total against the hardcoded 500 figure rather than the active license's `recordLimit`.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type CapacityDecisionContext
         {customLicenseConfigured: boolean,
          decisionPoint: string,
          comparisonLimit: integer}
  OUTPUT: boolean
  
  RETURN input.customLicenseConfigured == true
         AND input.decisionPoint IN ['module1_step6a', 'module4_step6',
                                      'module6_loading', 'module8_performance']
         AND input.comparisonLimit == 500
         AND NOT licenseQueried(input.decisionPoint)
END FUNCTION
```

### Examples

- **Module 1 Step 6a**: Bootcamper describes 5,726 records across two sources. A custom license with `recordLimit: 0` (unlimited) is configured. The agent compares 5,726 > 500 and triggers the license-guidance branch — incorrectly, since the active license has no cap.
- **Module 4 Step 6**: Dataset contains 2,000 records. Custom license allows 50,000 records. The agent recommends downsampling to ≤500 records for "license reasons" when the limit is actually 50,000.
- **Module 6 loading**: The agent warns "SENZ9000 error at record 501" before loading begins, even though the active license permits unlimited records.
- **Module 8 performance**: The agent caps benchmark sample sizes at 500 citing "the evaluation license" when a production license is active.
- **Edge case — no custom license**: Only the built-in evaluation license is active. The agent correctly uses the evaluation capacity (confirmed via MCP) — this is NOT a bug condition.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- When no custom license is configured, the agent continues to explain the built-in evaluation license and its capacity (confirmed via MCP) in Module 2 Step 5a.
- The number 500 used for non-license purposes (Module 6 Phase A volume tiers: "fewer than 500 — demo/evaluation"; SQLite ≤1,000-record performance advice; visualization entity cap) remains unchanged.
- Mouse clicks, button interactions, EULA acceptance flow, and all non-capacity-decision agent behavior is unaffected.
- The MCP-sourced-facts rule is preserved: all Senzing SDK facts (including `get_license()` semantics, `recordLimit` meaning, and the evaluation capacity) come from the Senzing MCP server, never training data.
- When the dataset genuinely exceeds the effective record limit, the agent continues to present the Module 1 licensing paths (apply existing, external request, in-flow MCP) as choices rather than forcing downsampling.
- Sampling for non-license reasons (very large file, faster iteration) remains available as an option independent of the license limit.

**Scope:**
All inputs where `customLicenseConfigured == false` or the decision point does not involve a license-capacity comparison should be completely unaffected by this fix. This includes:
- Sessions using only the built-in evaluation license
- Volume tier classification in Module 6 Phase A (demo/small/medium/large boundaries)
- SQLite single-threaded performance advice (≤1,000 records)
- Visualization entity caps in Module 7

## Hypothesized Root Cause

Based on the bug description and steering file analysis, the root causes are:

1. **Module 1 Step 6a — hardcoded threshold**: The steering text uses a literal `500` in the condition `If the total record count exceeds 500` without checking whether a custom license with a different `recordLimit` is active. The comparison should be against the effective license limit.

2. **Module 2 Step 5 — no license introspection after setup**: After the license is configured (Step 5c/5d), the module never calls `SzProduct.get_license()` to read and persist the active `recordLimit`. The only persistence is `license: custom` in `bootcamp_preferences.yaml` — no numeric limit is stored.

3. **Module 4 Step 6 — defers to hardcoded figure**: The "canonical framing" agent instruction references "the built-in evaluation license" and "a documented record count" but never instructs the agent to read the effective limit from `config/bootcamp_progress.json` or call `get_license()` when a custom license is present. It falls back to the 500 assumption.

4. **Module 6 loading — no conditional on license type**: The loading decision references "SENZ9000" and the evaluation capacity without conditioning on whether a custom license is active.

5. **Module 8 performance — inherited assumption**: Performance benchmarks inherit the capacity assumption from earlier modules without re-checking the license.

6. **No persistence contract**: `config/bootcamp_progress.json` has no field for the detected license limit, so there is no mechanism for later modules to reuse a once-detected limit without re-querying the SDK.

## Correctness Properties

Property 1: Bug Condition - License Limit Used at Capacity Decisions

_For any_ capacity-decision context where a custom license is configured (isBugCondition returns true), the fixed steering SHALL direct the agent to read the active license's `recordLimit` (via `SzProduct.get_license()` or from the persisted `license_record_limit` in `config/bootcamp_progress.json`) and compare the dataset total against that effective limit — never against the hardcoded 500.

**Validates: Requirements 2.1, 2.2, 2.5**

Property 2: Preservation - Evaluation License and Non-License Figures Unchanged

_For any_ context where no custom license is configured (isBugCondition returns false) OR the decision point does not involve a license-capacity comparison, the fixed steering SHALL produce the same agent behavior as the original steering, preserving the built-in evaluation explanation, the volume tier boundaries (500 in Module 6 Phase A), and MCP-sourced-facts rule.

**Validates: Requirements 3.1, 3.2, 3.5, 3.6**

Property 3: Persistence - Detected Limit Stored for Cross-Module Reuse

_For any_ session where a custom license is configured in Module 2, the fixed flow SHALL persist the detected `recordLimit` to `config/bootcamp_progress.json` under a `license_record_limit` key so that Modules 4, 6, and 8 can read it without re-querying the SDK.

**Validates: Requirements 2.4**

Property 4: No Hardcoded Claim - Custom License Messaging

_For any_ context where a custom license is present, the fixed steering SHALL NOT present the hardcoded 500-record figure or the "SENZ9000 at record 501" claim as the authoritative limit; it SHALL present the detected `recordLimit` instead.

**Validates: Requirements 2.3**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/scripts/detect_license_limit.py` (new)

**Purpose**: A stdlib-only helper that the agent is instructed to run after license configuration in Module 2 (and optionally re-run before any downstream capacity decision). It:
1. Instructs the agent to call `SzProduct.get_license()` via the MCP server or generated scaffold.
2. Parses the returned JSON for `recordLimit`.
3. Persists `license_record_limit` (integer, 0 means unlimited) to `config/bootcamp_progress.json`.
4. Outputs the detected limit to stdout for the agent to use.

**Specific Changes**:

1. **New script `detect_license_limit.py`**: Creates a Python script following project conventions (shebang, stdlib only, argparse, `main()` entry point). Reads the license JSON (passed as stdin or a file argument), extracts `recordLimit`, writes it to `config/bootcamp_progress.json`, and prints the result.

2. **`config/bootcamp_progress.json` schema update**: Add an optional `license_record_limit` field (integer | null). `null` means not yet detected; `0` means unlimited; positive integer means that many records.

3. **Steering: `module-02-sdk-setup.md` — add Step 5e (Detect License Limit)**: After Step 5d (configure LICENSEFILE), add a new step that instructs the agent to:
   - Generate a script using `generate_scaffold` that calls `SzProduct.get_license()` and prints the JSON.
   - Parse the `recordLimit` from the output.
   - Run `detect_license_limit.py` to persist it to `config/bootcamp_progress.json`.
   - Report the detected limit to the bootcamper.

4. **Steering: `module-01-phase1-discovery.md` — Step 6a conditional**: Change the threshold comparison from `exceeds 500` to: "Read `license_record_limit` from `config/bootcamp_progress.json`. If present and > 0, compare against that limit. If present and == 0, skip license guidance (no cap). If absent or null, compare against the evaluation capacity (confirmed via MCP)."

5. **Steering: `module-04-data-collection.md` — canonical framing update**: Update the agent instruction at the top to read `license_record_limit` from progress and use it as the effective limit. When `license_record_limit` is 0 or >= dataset size, do not recommend sampling for license reasons.

6. **Steering: `module-06-phaseB-load-first-source.md` — Step 6 conditional**: Before warning about "SENZ9000 at record 501", check `license_record_limit`. If a custom license is active (limit is 0 or > dataset size), omit the warning.

7. **Steering: `module-08-phaseB-benchmarking.md` — benchmark cap removal**: When a custom license is active (limit is 0 or > dataset size), do not cap benchmark sample sizes at 500.

8. **Steering: `module-02-sdk-setup.md` — Step 5a messaging guard**: Add a conditional: "When a custom license has been configured, do NOT restate the 500-record figure as the authoritative limit. Instead, present the detected `recordLimit`."

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed steering, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write property-based tests that generate capacity-decision contexts with various `license_record_limit` values and verify that the `detect_license_limit.py` script correctly persists and reads the limit, and that the threshold logic respects it.

**Test Cases**:
1. **Module 1 threshold test**: Generate a progress file with `license_record_limit: 0` and a dataset total of 5,726. Assert that the threshold check (as implemented in the helper script) does NOT trigger license guidance. (Will fail on unfixed code — there is no `license_record_limit` field to read.)
2. **Module 4 sampling test**: Generate a progress file with `license_record_limit: 50000` and dataset of 2,000 records. Assert sampling is not recommended for license reasons. (Will fail on unfixed code — the 500 comparison fires.)
3. **Module 6 SENZ9000 claim test**: Generate a context with `license_record_limit: 0`. Assert the "SENZ9000 at record 501" warning is not emitted. (Will fail on unfixed code.)
4. **No custom license test**: Generate a progress file with no `license_record_limit` field. Assert the evaluation-limit comparison fires as before. (Should pass on both unfixed and fixed code.)

**Expected Counterexamples**:
- The threshold logic compares against 500 regardless of license state
- No `license_record_limit` field exists in `config/bootcamp_progress.json`

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  progress := readProgress("config/bootcamp_progress.json")
  effectiveLimit := progress.license_record_limit
  result := evaluateCapacityDecision(input.datasetTotal, effectiveLimit)
  ASSERT result.comparisonLimit == effectiveLimit
  ASSERT result.recommendSampling == (effectiveLimit > 0 AND input.datasetTotal > effectiveLimit)
  ASSERT result.hardcoded500NotUsed == true
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT evaluateCapacityDecision_original(input) == evaluateCapacityDecision_fixed(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many configurations (no license, evaluation license, various dataset sizes) automatically
- It catches edge cases: `recordLimit` of 0 vs. 1 vs. exactly equal to dataset size
- It provides strong guarantees that the volume tier boundaries (500 in Module 6 Phase A) are unaffected

**Test Plan**: Observe behavior on UNFIXED code first for sessions without a custom license, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Evaluation-only preservation**: Verify that sessions without `license_record_limit` in progress still compare against MCP-returned evaluation capacity.
2. **Volume tier preservation**: Verify that Module 6 Phase A volume tiers (demo: <500, small: 500-500K, medium: 500K-10M, large: 10M+) are unaffected by the fix.
3. **SQLite performance advice preservation**: Verify ≤1,000-record recommendation remains in Module 6 Phase B.
4. **MCP-sourced-facts preservation**: Verify that the fix still directs the agent to source all SDK facts from the MCP server.

### Unit Tests

- Test `detect_license_limit.py` with various license JSON inputs (recordLimit: 0, 500, 10000, missing field)
- Test `config/bootcamp_progress.json` read/write with and without `license_record_limit` field
- Test threshold comparison logic: `effectiveLimit == 0` means no cap; positive integer means compare
- Test edge cases: `recordLimit` exactly equal to dataset total, `recordLimit` of 1

### Property-Based Tests

- Generate random `recordLimit` values (0 to 10M) and dataset totals (1 to 10M); verify the capacity decision is correct for each combination
- Generate random progress files with/without `license_record_limit`; verify backward compatibility (missing field falls back to evaluation logic)
- Generate random license JSON blobs; verify `detect_license_limit.py` extracts `recordLimit` correctly or reports an error for malformed input

### Integration Tests

- Test full flow: configure license in Module 2 → detect limit → persist → Module 4 reads persisted limit and skips sampling
- Test session resume: progress file already has `license_record_limit` from a previous session; verify later modules use it
- Test upgrade path: progress file from before the fix (no `license_record_limit` field); verify graceful fallback to evaluation-limit behavior
