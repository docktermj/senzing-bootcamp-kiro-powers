# Design Document: Workflow Improvements

## Overview

This design addresses three behavioral issues in the senzing-bootcamp power's steering files where the AI agent does not follow through on expected behavior:

1. **Auto-start web server** — The agent tells the bootcamper to manually start the web server instead of starting it automatically as a background process using `controlBashProcess`.
2. **License step never skippable** — The agent skips the license configuration step (Step 5) in Module 2 when the SDK is already installed, because the skip-ahead logic doesn't explicitly require it.
3. **Module transitions execute immediately** — The agent fails to start the next module after the bootcamper confirms they want to proceed, instead saving progress or pausing.

All three fixes are steering-file-only changes — editing markdown files in `senzing-bootcamp/steering/` to correct agent instructions. No application code, no new files, no infrastructure changes.

## Architecture

The senzing-bootcamp power uses a steering file architecture where:

- **Steering files** (markdown with YAML frontmatter) contain instructions that guide the Kiro AI agent's behavior during bootcamp sessions.
- **Inclusion modes** (`auto`, `always`, `manual`) determine when files are loaded into agent context.
- **Agent behavior** is entirely determined by the instructions in these files — if the instructions are wrong or ambiguous, the agent behaves incorrectly.

The architecture remains unchanged. This design modifies the *content* of existing steering files to correct agent behavior.

### Files to Modify

| File | Inclusion | Change Summary |
|------|-----------|----------------|
| `senzing-bootcamp/steering/visualization-web-service.md` | manual | Replace prohibition against background process with auto-start instruction |
| `senzing-bootcamp/steering/visualization-guide.md` | manual | Update Web Service Delivery Sequence to include auto-start step |
| `senzing-bootcamp/steering/module-02-sdk-setup.md` | manual | Make Step 5 (License) mandatory even when SDK already installed |
| `senzing-bootcamp/steering/conversation-protocol.md` | auto | Add explicit prohibition against saving/pausing after affirmative transition response |
| `senzing-bootcamp/steering/module-transitions.md` | always | Add "Transition Integrity" rule |
| `senzing-bootcamp/steering/module-completion.md` | manual | Reinforce immediate execution on affirmative response |

## Components and Interfaces

### Component 1: Web Server Auto-Start (visualization-web-service.md)

**Current behavior:** The file contains `⚠️ IMPORTANT: The agent SHALL NOT start the server as a background process within the IDE.` This explicitly prohibits the desired behavior.

**Target behavior:** The agent starts the web server as a background process using `controlBashProcess`, verifies it's running by reading process output, then presents the URL along with manual start/stop commands for reference.

**Changes:**

1. **Replace the prohibition** in the Lifecycle Management section with an auto-start instruction:
   - Use `controlBashProcess` with action `start` and the language-appropriate start command
   - Read process output to confirm the server started (look for "running on" or similar)
   - If startup fails (port conflict, missing deps, SDK error), fall back to manual instructions with troubleshooting guidance

2. **Add a "Server Auto-Start" subsection** to Lifecycle Management that specifies:
   - The exact `controlBashProcess` invocation pattern
   - How to verify the server is running (read process output, check for success message)
   - What to present to the bootcamper after successful start (URL + manual restart command + stop instructions)
   - Fallback behavior on failure

### Component 2: Web Service Delivery Sequence Update (visualization-guide.md)

**Current behavior:** The Web Service Delivery Sequence has 4 steps: present start command → describe expected output → present URL → provide stop instructions. This assumes manual start.

**Target behavior:** The sequence becomes: auto-start server → verify running → present URL with manual restart command → provide stop instructions.

**Changes:**

1. **Rewrite the Web Service Delivery Sequence** to reflect auto-start:
   - Step 1: Start the server as a background process using `controlBashProcess`
   - Step 2: Verify the server is running by reading process output
   - Step 3: Present the URL, the manual restart command (for reference), and stop instructions
   - Step 4: If auto-start failed, fall back to manual instructions

2. **Update the introductory note** to say the server is started automatically (not "must be started first").

### Component 3: License Step Mandatory Gate (module-02-sdk-setup.md)

**Current behavior:** Step 1's skip-ahead logic says "Skip Steps 2 and 3 entirely" and "Jump to Step 4 (verify installation) to confirm it works with the chosen language. If Step 4 passes, jump to Step 5 (license) then Step 7 (database)". While Step 5 is mentioned, the phrasing "jump to Step 5 then Step 7" is ambiguous — the agent sometimes interprets this as optional.

**Target behavior:** Step 5 is explicitly marked as a mandatory gate that is never skipped, with clear language that removes any ambiguity.

**Changes:**

1. **Add a mandatory gate marker to Step 5** — prefix with `⛔ MANDATORY GATE — Never skip this step, even if the SDK is already installed.`

2. **Strengthen Step 1's skip-ahead logic** — change the bullet from a casual mention to an explicit requirement:
   - Replace: "If Step 4 passes, jump to Step 5 (license) then Step 7 (database) — only configure what's not already configured"
   - With: "If Step 4 passes, proceed to Step 5 (Configure License) — this step is MANDATORY and must always be executed regardless of SDK installation status. After Step 5, proceed to Step 7 (database)."

3. **Add a "Required Stops" callout** after the skip-ahead logic listing steps that are never skipped: Step 4 (verify), Step 5 (license).

### Component 4: Module Transition Integrity (conversation-protocol.md, module-transitions.md, module-completion.md)

**Current behavior:** The conversation-protocol.md has a "Module Transition Protocol" section that says to immediately begin the module, but it's brief and doesn't explicitly prohibit the failure mode (saving progress instead of starting). The module-completion.md has a note about immediate execution but doesn't prohibit intermediate actions.

**Target behavior:** Multiple steering files reinforce that once a "Ready for Module X?" question is asked and answered affirmatively, the *only* valid response is to start that module. Saving progress, pausing, or ending the session is explicitly prohibited.

**Changes:**

1. **conversation-protocol.md** — Expand the Module Transition Protocol section:
   - Add explicit prohibition: "Saving progress and ending the session is PROHIBITED as a response to an affirmative answer to a module transition question."
   - Add the commitment rule: "Once a 'Ready for Module X?' question has been asked, the only valid response to an affirmative answer is to start Module X — never to save progress, pause, or end the session."
   - Add context-limit guidance: "If context limits are a concern, address them BEFORE asking the transition question, not after receiving the affirmative response."

2. **module-transitions.md** — Add a "Transition Integrity" section:
   - Rule: "Module transition questions are commitments: asking the question means the agent is prepared to execute the transition if confirmed."
   - Rule: "If context limits may prevent completing the next module, do NOT ask the transition question. Instead, transparently inform the bootcamper about the limitation and offer to save progress."

3. **module-completion.md** — Strengthen the existing note:
   - Reinforce that upon receiving an affirmative response, the agent must immediately execute the startup sequence without any intermediate acknowledgment, progress-saving, or session-ending behavior.

## Data Models

No data model changes. The steering files are plain markdown with YAML frontmatter. The only "data" involved is the text content of the instructions.

## Error Handling

### Web Server Auto-Start Failures

The design includes explicit fallback behavior when the web server fails to start:

| Failure Mode | Detection | Fallback |
|--------------|-----------|----------|
| Port conflict | Process output contains "address already in use" or similar | Report conflict, suggest alternative port, provide manual command |
| Missing dependencies | Process output contains import/module errors | Guide bootcamper to install deps, provide manual command |
| SDK error | Process output contains SENZ error codes | Use `explain_error_code`, provide troubleshooting, provide manual command |
| Process crashes immediately | No "running on" message in output after reasonable wait | Report failure, provide manual command |

### License Step Edge Cases

| Scenario | Handling |
|----------|----------|
| SDK already installed, Step 5 previously completed | Still execute Step 5 — the bootcamper may have changed their license situation |
| Bootcamper tries to skip Step 5 | The ⛔ MANDATORY GATE marker and 🛑 STOP ensure the agent waits |

### Module Transition Edge Cases

| Scenario | Handling |
|----------|----------|
| Context limit reached before asking transition question | Agent informs bootcamper about limitation and offers to save progress BEFORE asking |
| Context limit reached after asking but before receiving response | Agent should not have asked — this is prevented by the Transition Integrity rule |
| Ambiguous response (not clearly affirmative or negative) | Existing conversation protocol handles this — ask for clarification |

## Testing Strategy

### Why Property-Based Testing Does Not Apply

This feature modifies markdown steering files — declarative instruction documents for an AI agent. There are no pure functions, no input/output transformations, no parsers, serializers, or algorithms to test. The "correctness" of these changes is determined by whether specific text patterns exist in the right files, which is a configuration validation problem.

**Appropriate testing approach:** Example-based validation tests that verify the steering files contain the required instructions and do not contain the prohibited instructions.

### Test Categories

**1. Content Presence Tests (unit tests)**

Verify that after applying changes, the steering files contain required text:

- `visualization-web-service.md` contains `controlBashProcess` instruction
- `visualization-web-service.md` does NOT contain the old prohibition ("SHALL NOT start the server as a background process")
- `visualization-guide.md` Web Service Delivery Sequence includes auto-start step
- `module-02-sdk-setup.md` Step 5 contains mandatory gate marker
- `module-02-sdk-setup.md` Step 1 skip-ahead logic explicitly requires Step 5
- `conversation-protocol.md` contains prohibition against saving after affirmative response
- `module-transitions.md` contains "Transition Integrity" section
- `module-completion.md` reinforces immediate execution

**2. Structural Integrity Tests (unit tests)**

Verify that modified files maintain valid structure:

- All modified files retain valid YAML frontmatter
- All modified files retain their `inclusion` mode unchanged
- No markdown structural issues introduced (headers, tables, code blocks)

**3. Consistency Tests (unit tests)**

Verify cross-file consistency:

- The auto-start instruction in `visualization-web-service.md` matches the delivery sequence in `visualization-guide.md`
- The transition rules in `conversation-protocol.md`, `module-transitions.md`, and `module-completion.md` are consistent and non-contradictory
- The mandatory gate in `module-02-sdk-setup.md` Step 5 is referenced in Step 1's skip logic

### Test Implementation

- **Framework:** pytest (per project conventions)
- **Location:** `senzing-bootcamp/tests/` (power tests directory)
- **Approach:** Read steering file content and assert on text patterns using simple string matching or regex
- **No mocking needed** — tests read static file content
