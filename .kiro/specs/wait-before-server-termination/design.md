# Wait Before Server Termination Bugfix Design

## Overview

After the agent presents the web visualization URL (`http://localhost:8080/`) in Module 3 Step 9, it immediately proceeds to Step 11 (Cleanup) and terminates the web server. The bootcamper never gets a chance to open and explore the visualization — the "wow moment" is destroyed. The fix adds explicit STOP-and-wait instructions at the presentation point and a user confirmation gate before cleanup, ensuring the server stays alive until the bootcamper confirms they are done exploring.

This is a steering-file-only fix. No application code changes are required. Three Markdown agent instruction files need targeted additions to insert a "wait for user" gate into the web service lifecycle.

## Glossary

- **Bug_Condition (C)**: The agent reaches the point after presenting the visualization URL and before the bootcamper has confirmed they are finished exploring — the transition from Step 9 presentation to Step 11 cleanup occurs without user input
- **Property (P)**: The agent SHALL stop after presenting the URL and wait for explicit bootcamper confirmation before proceeding to any cleanup or server termination
- **Preservation**: All existing behaviors — endpoint verification, checkpoint writing, server start sequence, cleanup logic, database purge, and module completion — remain unchanged once the bootcamper confirms they are done
- **Web Service Delivery Sequence**: The 4-step sequence in `visualization-guide.md` (start → verify → present → fallback) that governs how web services are presented to the bootcamper
- **STOP instruction**: A `🛑 STOP` directive in steering files that forces the agent to end its response and wait for bootcamper input before continuing
- **Step 9.4**: The "Start and Verify Web Service" subsection in `module-03-phase2-visualization.md`
- **Step 11**: The "Cleanup" step in `module-03-system-verification.md` that terminates the web service and purges TruthSet data

## Bug Details

### Bug Condition

The bug manifests when the agent completes Step 9.4 (presenting the visualization URL) and proceeds directly to writing the checkpoint and then to Step 11 cleanup without pausing for the bootcamper to interact with the visualization. The Web Service Delivery Sequence in `visualization-guide.md` has no "wait for user" step, and neither the phase2 file nor the main module file includes a STOP instruction between URL presentation and cleanup.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type AgentExecutionState
  OUTPUT: boolean
  
  RETURN input.step = "post_url_presentation"
         AND input.webServerRunning = true
         AND input.bootcamperConfirmedDone = false
         AND input.agentProceeding = true
END FUNCTION
```

### Examples

- **Example 1**: Agent presents "Your visualization is running — open http://localhost:8080 in your browser", writes checkpoint, immediately proceeds to Step 11, terminates the server. Bootcamper sees the URL but by the time they click it, the server is already dead. **Expected**: Agent stops after presenting the URL and waits for bootcamper to say they're done.
- **Example 2**: Agent completes all endpoint verifications, presents the URL with restart/stop instructions, then in the same response begins "Now let's clean up..." and kills the process. **Expected**: Agent ends its response after presenting the URL with a STOP instruction.
- **Example 3**: Bootcamper is a slow reader, takes 30 seconds to copy the URL into their browser. Agent has already moved to cleanup. **Expected**: Server remains running indefinitely until bootcamper explicitly confirms.
- **Edge case**: Bootcamper used the skip-step protocol to skip Step 9 entirely — no server was started. **Expected**: No confirmation prompt needed; cleanup proceeds normally (no server to terminate).

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- The Web Service Delivery Sequence steps 1–3 (start, verify, present) and step 4 (fallback) continue to work exactly as before
- Endpoint verification with 10-second timeouts per endpoint remains unchanged
- Checkpoint writing to `config/bootcamp_progress.json` after verification continues as defined
- Step 11 cleanup logic (5-second termination timeout, force-stop, database purge) remains unchanged once triggered
- Step 10 (Verification Report Generation) continues to execute between Step 9 and Step 11
- The skip-step protocol continues to bypass visualization without a confirmation prompt
- Module completion, journal entry, and transition to Module 4 remain unchanged

**Scope:**
All agent behavior that does NOT involve the transition from URL presentation to cleanup should be completely unaffected by this fix. This includes:
- Server startup and endpoint verification
- Checkpoint persistence
- Report generation
- Database purge mechanics
- Module transition logic
- All other modules' visualization flows (Modules 5, 7, 8)

## Hypothesized Root Cause

Based on the bug description, the root cause is a missing control-flow gate in the steering files:

1. **Missing STOP in Web Service Delivery Sequence**: The `visualization-guide.md` "Web Service Delivery Sequence" defines 4 steps (start → verify → present → fallback) but includes no "wait for user confirmation" step between presenting the URL and any subsequent agent action. Since this sequence is the authoritative reference, downstream files inherit the gap.

2. **Missing STOP in phase2 file (Step 9.4 section 3)**: The `module-03-phase2-visualization.md` file's "Present to bootcamper" section provides the URL, restart command, and stop instructions but does not include a `🛑 STOP` directive. The agent treats this as informational output and continues to the checkpoint write and beyond.

3. **Missing confirmation gate in Step 11**: The `module-03-system-verification.md` Step 11 begins immediately with "Terminate the web service" — there is no preceding instruction to ask the bootcamper if they are done exploring. Even if the agent paused after Step 9, Step 11 has no safety net.

All three gaps must be addressed to create a robust fix. The primary fix is the STOP in the phase2 file (prevents the agent from continuing past presentation). The secondary fix is the confirmation prompt in Step 11 (defense-in-depth in case the agent somehow reaches cleanup without having paused). The tertiary fix is updating the Web Service Delivery Sequence (keeps the authoritative reference accurate for all modules).

## Correctness Properties

Property 1: Bug Condition - Agent Stops After URL Presentation

_For any_ execution where the agent has presented the visualization URL to the bootcamper and the web server is running, the agent SHALL end its response with a STOP instruction and wait for explicit bootcamper confirmation before proceeding to any subsequent step (checkpoint write, report generation, or cleanup).

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Cleanup Proceeds Normally After Confirmation

_For any_ execution where the bootcamper has confirmed they are finished exploring (or where no server was started due to skip-step protocol), the agent SHALL proceed with the existing cleanup logic unchanged — terminating the web service within 5 seconds, purging TruthSet data, and completing the module transition exactly as currently defined.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/visualization-guide.md`

**Section**: Web Service Delivery Sequence

**Specific Changes**:
1. **Add step 4 (wait for user)**: Insert a new step between the current step 3 (present) and step 4 (fallback) that instructs the agent to end its response with a STOP directive and wait for the bootcamper to confirm they have finished exploring. Renumber the current step 4 (fallback) to step 5.

---

**File**: `senzing-bootcamp/steering/module-03-phase2-visualization.md`

**Section**: Step 9.4, item 3 ("Present to bootcamper")

**Specific Changes**:
2. **Add STOP instruction after presentation**: After the bullet points presenting the URL, restart command, and stop instructions, add a `🛑 STOP` block that forces the agent to end its response and wait for the bootcamper to confirm they are done exploring before proceeding.
3. **Add confirmation prompt text**: Include a prompt like "👉 Take your time exploring the visualization. Let me know when you're ready and I'll continue with cleanup."

---

**File**: `senzing-bootcamp/steering/module-03-system-verification.md`

**Section**: Step 11 (Cleanup), before item 1

**Specific Changes**:
4. **Add user confirmation gate**: Insert a pre-cleanup instruction at the beginning of Step 11 that requires the agent to ask the bootcamper if they have finished exploring the visualization before proceeding with termination.
5. **Add skip condition**: If the bootcamper skipped Step 9 (no server was started), the confirmation prompt is skipped and cleanup proceeds directly.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed steering files, then verify the fix works correctly and preserves existing behavior. Since this is a steering-file fix (Markdown instructions, not executable code), testing is performed via structural analysis of the steering file content rather than runtime execution.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis by examining the current steering file content.

**Test Plan**: Parse the three steering files and verify the absence of STOP instructions and confirmation prompts at the critical transition points. Run these checks on the UNFIXED files to confirm the gap exists.

**Test Cases**:
1. **Missing STOP in phase2 file**: Verify that `module-03-phase2-visualization.md` Step 9.4 section 3 does NOT contain a `🛑 STOP` directive after the URL presentation (will confirm bug on unfixed files)
2. **Missing confirmation in Step 11**: Verify that `module-03-system-verification.md` Step 11 does NOT contain a user confirmation prompt before termination (will confirm bug on unfixed files)
3. **Missing wait step in delivery sequence**: Verify that `visualization-guide.md` Web Service Delivery Sequence has only 4 steps with no "wait" step (will confirm bug on unfixed files)
4. **Sequence gap**: Verify that the delivery sequence goes directly from "Present" to "Fallback" with no intermediate user-wait step (will confirm bug on unfixed files)

**Expected Counterexamples**:
- Step 9.4 section 3 ends with stop instructions but no STOP directive — agent continues
- Step 11 begins with "Terminate the web service" — no confirmation gate
- Web Service Delivery Sequence step 3 is "Present" and step 4 is "Fallback" — no wait step

### Fix Checking

**Goal**: Verify that for all steering file states where the bug condition holds (agent at post-presentation point), the fixed files contain instructions that force the agent to stop and wait.

**Pseudocode:**
```
FOR ALL file_state WHERE isBugCondition(file_state) DO
  result := parse_steering_file(fixed_file)
  ASSERT contains_stop_instruction(result, after="url_presentation")
  ASSERT contains_confirmation_prompt(result, before="server_termination")
END FOR
```

### Preservation Checking

**Goal**: Verify that for all steering file content where the bug condition does NOT hold (all other instructions), the fixed files produce the same agent behavior as the original files.

**Pseudocode:**
```
FOR ALL instruction WHERE NOT isBugCondition(instruction) DO
  ASSERT original_file_content(instruction) = fixed_file_content(instruction)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It can generate many structural variations of the steering file content
- It catches unintended modifications to surrounding instructions
- It provides strong guarantees that non-fix content is unchanged

**Test Plan**: Compare the original and fixed file content line-by-line outside the specific insertion points to verify no unintended changes were introduced.

**Test Cases**:
1. **Delivery sequence steps 1-3 preserved**: Verify steps 1 (start), 2 (verify), and 3 (present) in `visualization-guide.md` are unchanged after fix
2. **Fallback step preserved**: Verify the fallback-on-failure logic is unchanged (only renumbered)
3. **Step 11 cleanup logic preserved**: Verify the termination, artifact message, purge, and retain steps in `module-03-system-verification.md` are unchanged after the new confirmation gate
4. **Endpoint verification preserved**: Verify Step 9.4 items 1 and 2 (start server, verify endpoints) in `module-03-phase2-visualization.md` are unchanged
5. **Checkpoint writing preserved**: Verify the checkpoint JSON structure at the end of Step 9.4 is unchanged

### Unit Tests

- Test that `visualization-guide.md` Web Service Delivery Sequence contains exactly 5 steps after fix
- Test that step 4 in the delivery sequence contains "STOP" and "wait" and "confirm" keywords
- Test that `module-03-phase2-visualization.md` Step 9.4 section 3 contains a `🛑 STOP` directive
- Test that `module-03-system-verification.md` Step 11 contains a confirmation prompt before termination logic
- Test that the skip condition is present (no confirmation when Step 9 was skipped)

### Property-Based Tests

- Generate random positions in the steering files and verify that only the designated insertion points have new content
- Generate random module execution states and verify the confirmation prompt appears only when a web server is running
- Test across all checkpoint IDs in `visualization-guide.md` to verify only `m3_demo_results` flow is affected

### Integration Tests

- Trace the full Module 3 execution flow through all three files and verify the STOP appears exactly once between URL presentation and cleanup
- Verify the Web Service Delivery Sequence referenced by `module-03-phase2-visualization.md` is consistent with the updated `visualization-guide.md`
- Verify that the confirmation prompt text in Step 11 matches the STOP prompt in Step 9.4 (consistent user experience)
