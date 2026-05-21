# License Guidance Workflow Bugfix Design

## Overview

When a bootcamper's stated record count exceeds 500 during Module 1 (Business Problem) Step 6, the system currently mentions the 500-record evaluation limit and links to the license request page but provides no interactive guidance. It fails to ask whether the bootcamper already has a license, and it does not walk them through the license configuration process. This fix adds a branching license guidance workflow triggered by record count > 500 that asks about existing license status and provides step-by-step configuration guidance for both the "already has a license" and "needs a license" paths.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — when a bootcamper's total record count across data sources exceeds 500 during Module 1 discovery (Step 6 inference), the system provides inadequate license guidance
- **Property (P)**: The desired behavior — the system asks whether the bootcamper already has a license and provides step-by-step configuration guidance appropriate to their answer
- **Preservation**: Existing Module 1 discovery flow behavior for record counts ≤ 500, Module 2 Step 5 mandatory license gate, and Step 6 data inference logic must remain unchanged
- **module-01-business-problem.md**: The steering file at `senzing-bootcamp/steering/module-01-business-problem.md` that defines Module 1 Phase 1 workflow steps
- **module-01-phase2-document-confirm.md**: The steering file at `senzing-bootcamp/steering/module-01-phase2-document-confirm.md` that defines Module 1 Phase 2 (Steps 10–18)
- **module-02-sdk-setup.md**: The steering file at `senzing-bootcamp/steering/module-02-sdk-setup.md` that defines Module 2 including Step 5 (Configure License)
- **Record count**: The total number of records across all data sources inferred from the bootcamper's response in Step 6
- **LICENSESTRINGBASE64**: A Base64-encoded Senzing license string that decodes to a binary `.lic` file

## Bug Details

### Bug Condition

The bug manifests when a bootcamper describes data sources with a combined record count exceeding 500 during Module 1 Step 6 (Infer details from response). The `module-01-business-problem.md` steering file parses record counts from the bootcamper's response but has no conditional logic to trigger license guidance when the total exceeds the built-in evaluation limit.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type Module1Step6Response (bootcamper's data source description)
  OUTPUT: boolean
  
  totalRecords := sumRecordCounts(input.dataSources)
  RETURN totalRecords > 500
         AND currentModule = "Module 1"
         AND currentStep IN [6, 7a, 7b, 7c, 7d]
         AND licenseGuidanceNotProvided(input)
END FUNCTION
```

### Examples

- **Example 1**: Bootcamper says "I have 3,000 customer records from our CRM" → System mentions 500-record limit and links to license page, but does NOT ask "Do you already have a Senzing license?" (Bug: no branching question)
- **Example 2**: Bootcamper says "We have two sources: 2,000 records from billing and 1,500 from support" → System notes the limit but does NOT guide through license configuration steps (Bug: no step-by-step guidance)
- **Example 3**: Enterprise user says "I have 10,000 records and already have a Senzing license from my organization" → System still directs them to request a new license instead of asking for their existing key (Bug: assumes no license)
- **Edge case**: Bootcamper says "about 500 records" (exactly 500) → Should NOT trigger license guidance (evaluation license is sufficient for ≤ 500)

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Module 1 Step 6 data inference logic (parsing record types, source count, problem category, matching criteria, desired outcome) must continue to work without interruption from license guidance
- Bootcampers with record counts ≤ 500 must proceed through Module 1 without any license-related mentions
- Module 2 Step 5 (Configure License) mandatory gate must continue to execute regardless of what happened in Module 1
- The one-question-per-turn pattern in Module 1 gap-filling (Steps 7a–7d) must be preserved
- The deferral option must allow bootcampers to continue Module 1 without completing license configuration

**Scope:**
All inputs where the total record count is ≤ 500 should be completely unaffected by this fix. This includes:
- Bootcampers who describe small datasets (≤ 500 records total)
- All Module 1 steps unrelated to record count (Steps 1–5, 8–9, Phase 2)
- Module 2 Step 5 license configuration (independent mandatory gate)
- All other modules (3–11)

## Hypothesized Root Cause

Based on the bug description and analysis of the steering files, the root cause is:

1. **Missing conditional logic in Step 6**: The `module-01-business-problem.md` file's Step 6 (Infer details from response) parses record counts under "SOURCE COUNT AND NAMES" but has no conditional branch that checks whether the total exceeds 500. The step simply records the count and moves on.

2. **No license guidance workflow exists**: There is no sub-workflow or additional step between Steps 6 and 7 (or within Step 7) that triggers license guidance when record count > 500. The steering file has no awareness of the 500-record evaluation limit.

3. **POWER.md mentions the limit passively**: The `POWER.md` file states "Senzing includes a built-in evaluation license that allows 500 records" but this is informational text, not an actionable workflow trigger. The onboarding flow (`onboarding-flow.md`) also mentions it passively.

4. **No branching question for existing license holders**: Even if the system were to detect the > 500 condition, there is no "Do you already have a license?" question defined anywhere in Module 1. The only license interaction is in Module 2 Step 5, which is a separate mandatory gate.

## Correctness Properties

Property 1: Bug Condition - License Guidance Triggered for Large Datasets

_For any_ Module 1 Step 6 response where the total record count across all described data sources exceeds 500, the system SHALL ask "Do you already have a Senzing license?" and then provide appropriate step-by-step guidance based on the bootcamper's answer (configuration guidance for existing license holders, or request-and-configure guidance for those without a license).

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation - No License Guidance for Small Datasets

_For any_ Module 1 Step 6 response where the total record count across all described data sources is 500 or fewer, the system SHALL produce the same behavior as the original (unfixed) system — proceeding through Module 1 without mentioning license requirements, preserving the existing discovery flow, data inference logic, and gap-filling question sequence.

**Validates: Requirements 3.1, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/module-01-business-problem.md`

**Location**: After Step 6 (Infer details from response), before Step 7 (Confirm inferred details)

**Specific Changes**:

1. **Add record count threshold detection in Step 6**: After parsing source count and names, add logic to sum all record counts mentioned. If the total exceeds 500, set a flag to trigger the license guidance sub-workflow.

2. **Add new Step 6b — License Guidance Workflow** (inserted between Step 6 and Step 7): A conditional step that only executes when total records > 500. This step:
   - Explains the 500-record evaluation limit
   - Asks: "Do you already have a Senzing license?"
   - Includes a STOP marker to wait for the bootcamper's response
   - Branches based on the answer

3. **Add Step 6c — "Already has license" branch**: When the bootcamper confirms they have a license:
   - Ask them to provide the Base64-encoded license string or file path
   - Guide through decoding to `licenses/g2.lic`
   - Guide through adding `LICENSEFILE` to engine config PIPELINE section
   - Record `license: custom` in `config/bootcamp_preferences.yaml`

4. **Add Step 6d — "Does not have license" branch**: When the bootcamper confirms they do not have a license:
   - Explain where to request (support@senzing.com)
   - Explain what information to provide (mention bootcamp use case)
   - Set expectations (1–2 business day turnaround, 30–90 day validity)
   - Explain how to configure once received (decode Base64 → `licenses/g2.lic`, add LICENSEFILE to engine config)
   - Offer to defer: "Would you like to continue with Module 1 now and configure the license later in Module 2?"

5. **Add Step 6e — Deferral handling**: When the bootcamper chooses to defer:
   - Record `license_guidance_deferred: true` in `config/bootcamp_preferences.yaml`
   - Note that Module 2 Step 5 will handle license configuration
   - Proceed to Step 7 normally

6. **Preserve Step 6 inference logic**: The record type, source count, problem category, matching criteria, and desired outcome inference must execute completely before the license guidance sub-workflow triggers. License guidance must not interrupt the five-category parsing.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed steering content, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that parse the current `module-01-business-problem.md` steering file and verify whether it contains conditional logic for record counts > 500. Simulate agent behavior by checking for the presence of license guidance keywords and branching questions in the Step 6 output path.

**Test Cases**:
1. **Missing threshold check**: Verify that Step 6 in the current steering file has no conditional logic checking record count > 500 (will confirm bug on unfixed code)
2. **Missing license question**: Verify that no step between 6 and 7 asks "Do you already have a Senzing license?" (will confirm bug on unfixed code)
3. **Missing configuration guidance**: Verify that no step in Module 1 contains LICENSESTRINGBASE64 decode instructions (will confirm bug on unfixed code)
4. **Missing branching logic**: Verify that no step handles the "already has license" vs "needs license" fork (will confirm bug on unfixed code)

**Expected Counterexamples**:
- Step 6 parses record counts but has no > 500 conditional branch
- No license question exists between Steps 6 and 7
- Possible causes: the steering file was written assuming all bootcampers would use ≤ 500 records, with license handling deferred entirely to Module 2

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (record count > 500), the fixed steering file produces the expected license guidance workflow.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  steeringContent := parseSteeringFile("module-01-business-problem.md")
  result := simulateAgentBehavior(steeringContent, input)
  ASSERT result.asksLicenseQuestion = true
  ASSERT result.providesBranchingGuidance = true
  ASSERT result.handlesExistingLicense = true
  ASSERT result.handlesNoLicense = true
  ASSERT result.allowsDeferral = true
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold (record count ≤ 500), the fixed steering file produces the same behavior as the original.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT simulateAgentBehavior(fixedSteering, input) = simulateAgentBehavior(originalSteering, input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many record count values ≤ 500 to verify no license guidance is triggered
- It catches edge cases (exactly 500, 0 records, ambiguous counts) that manual tests might miss
- It provides strong guarantees that the discovery flow is unchanged for small datasets

**Test Plan**: Parse the fixed steering file and verify that for any simulated bootcamper response with total records ≤ 500, the Step 6 output does not include license guidance content. Also verify that Step 6's five-category inference (record types, source count, problem category, matching criteria, desired outcome) produces identical results regardless of whether the license guidance workflow was added.

**Test Cases**:
1. **Small dataset preservation**: Verify that a response mentioning "200 records" triggers no license guidance and proceeds directly to Step 7
2. **Boundary preservation**: Verify that exactly 500 records triggers no license guidance
3. **Inference logic preservation**: Verify that the five-category parsing in Step 6 produces identical results for any input, whether or not the license workflow exists
4. **Module 2 Step 5 independence**: Verify that Module 2 Step 5 (Configure License) remains unchanged and mandatory regardless of Module 1 license guidance

### Unit Tests

- Test record count extraction from various bootcamper response formats ("3,000 records", "about 2k", "500 from CRM and 1000 from billing")
- Test threshold detection (> 500 triggers, ≤ 500 does not)
- Test branching logic ("yes I have a license" → configuration path, "no" → request path)
- Test deferral handling (bootcamper chooses to continue without configuring)
- Test edge cases (ambiguous counts, no count mentioned, multiple sources summing to > 500)

### Property-Based Tests

- Generate random record count values (1–100,000) and verify the threshold triggers correctly at > 500
- Generate random bootcamper responses with varying data source descriptions and verify the five-category inference is unaffected by the license guidance addition
- Generate random combinations of "has license" / "no license" / "defer" responses and verify each branch produces the correct guidance content

### Integration Tests

- Test full Module 1 flow with record count > 500 and "already has license" response
- Test full Module 1 flow with record count > 500 and "no license" response with deferral
- Test that Module 2 Step 5 still executes after Module 1 license guidance was provided
- Test that `config/bootcamp_preferences.yaml` is correctly updated with license status
