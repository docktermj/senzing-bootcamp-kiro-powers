# Implementation Plan: Workflow Improvements

## Overview

Three targeted steering-file edits to fix agent behavioral issues: auto-starting the web server as a background process, making the license step mandatory, and ensuring module transitions execute immediately on confirmation. All changes are to existing markdown files in `senzing-bootcamp/steering/`. Tests use pytest with simple text-pattern assertions.

## Tasks

- [x] 1. Implement web server auto-start in visualization steering files
  - [x] 1.1 Update `visualization-web-service.md` to replace background-process prohibition with auto-start instruction
    - Remove the `⚠️ IMPORTANT: The agent SHALL NOT start the server as a background process within the IDE.` prohibition
    - Add a "Server Auto-Start" subsection to Lifecycle Management specifying:
      - Use `controlBashProcess` with action `start` and the language-appropriate start command
      - Read process output to confirm server started (look for "running on" or similar)
      - Present URL + manual restart command + stop instructions to bootcamper
      - Fallback behavior on failure (port conflict, missing deps, SDK error)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [x] 1.2 Update `visualization-guide.md` Web Service Delivery Sequence to include auto-start step
    - Rewrite the delivery sequence to:
      - Step 1: Start server as background process using `controlBashProcess`
      - Step 2: Verify server is running by reading process output
      - Step 3: Present URL, manual restart command (for reference), and stop instructions
      - Step 4: If auto-start failed, fall back to manual instructions
    - Update introductory note to say server is started automatically
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.7_

  - [x] 1.3 Write pytest tests for web server auto-start steering changes
    - Verify `visualization-web-service.md` contains `controlBashProcess` instruction
    - Verify `visualization-web-service.md` does NOT contain the old prohibition text
    - Verify `visualization-guide.md` delivery sequence includes auto-start step
    - Verify both files retain valid YAML frontmatter and unchanged `inclusion` mode
    - _Requirements: 1.6, 1.7_

- [x] 2. Make license step mandatory in Module 2 steering file
  - [x] 2.1 Add mandatory gate marker to Step 5 in `module-02-sdk-setup.md`
    - Prefix Step 5 with `⛔ MANDATORY GATE — Never skip this step, even if the SDK is already installed.`
    - Retain existing 👉 question and 🛑 STOP marker
    - _Requirements: 2.1, 2.4_

  - [x] 2.2 Strengthen Step 1 skip-ahead logic in `module-02-sdk-setup.md`
    - Replace ambiguous "jump to Step 5 (license) then Step 7" phrasing
    - New text: "proceed to Step 5 (Configure License) — this step is MANDATORY and must always be executed regardless of SDK installation status. After Step 5, proceed to Step 7 (database)."
    - Add a "Required Stops" callout listing steps that are never skipped: Step 4 (verify), Step 5 (license)
    - _Requirements: 2.2, 2.3_

  - [x] 2.3 Write pytest tests for license step mandatory gate
    - Verify `module-02-sdk-setup.md` Step 5 contains mandatory gate marker
    - Verify Step 1 skip-ahead logic explicitly requires Step 5 as mandatory
    - Verify file retains valid YAML frontmatter and unchanged `inclusion` mode
    - _Requirements: 2.1, 2.2, 2.3_

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement module transition integrity across three steering files
  - [x] 4.1 Expand Module Transition Protocol in `conversation-protocol.md`
    - Add explicit prohibition: "Saving progress and ending the session is PROHIBITED as a response to an affirmative answer to a module transition question."
    - Add commitment rule: "Once a 'Ready for Module X?' question has been asked, the only valid response to an affirmative answer is to start Module X — never to save progress, pause, or end the session."
    - Add context-limit guidance: "If context limits are a concern, address them BEFORE asking the transition question, not after receiving the affirmative response."
    - _Requirements: 3.2, 3.4, 3.5_

  - [x] 4.2 Add "Transition Integrity" section to `module-transitions.md`
    - Add rule: "Module transition questions are commitments: asking the question means the agent is prepared to execute the transition if confirmed."
    - Add rule: "If context limits may prevent completing the next module, do NOT ask the transition question. Instead, transparently inform the bootcamper about the limitation and offer to save progress."
    - _Requirements: 3.4, 3.6_

  - [x] 4.3 Strengthen immediate execution in `module-completion.md`
    - Reinforce that upon receiving an affirmative response to "Ready to move on to Module [N]?", the agent must immediately execute the next module's startup sequence (banner, journey map, Step 1)
    - Explicitly prohibit intermediate acknowledgment, progress-saving, or session-ending behavior between the affirmative response and module startup
    - _Requirements: 3.1, 3.3_

  - [x] 4.4 Write pytest tests for module transition integrity
    - Verify `conversation-protocol.md` contains prohibition against saving after affirmative response
    - Verify `module-transitions.md` contains "Transition Integrity" section
    - Verify `module-completion.md` reinforces immediate execution on affirmative response
    - Verify all three files retain valid YAML frontmatter and unchanged `inclusion` modes
    - Verify cross-file consistency (transition rules are non-contradictory)
    - _Requirements: 3.1, 3.2, 3.3, 3.5, 3.6_

- [x] 5. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- All changes are to existing markdown steering files — no new files, no application code
- Tests use pytest with simple string/regex assertions on file content
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation after each logical group of changes
