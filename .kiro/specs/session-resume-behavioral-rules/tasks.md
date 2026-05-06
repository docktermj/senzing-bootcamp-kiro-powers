# Tasks

## Task 1: Expand Behavioral Rules Reload in session-resume.md

- [x] 1.1 Expand the existing Step 2b "Behavioral Rules Reload" section to include the authoritative source declaration: "conversation-protocol.md is the authoritative source for all turn-taking and question-handling rules. These rules apply without exception after session resume."
- [x] 1.2 Add enforcement mechanism descriptions for each of the five core rules: (a) one question per turn with STOP after each, (b) 👉 prefix on every bootcamper question, (c) STOP markers as absolute end-of-turn boundaries, (d) no self-answering under any circumstance, (e) no dead-end responses after bootcamper input
- [x] 1.3 Add equal priority statement: session resume does not reduce the authority of any behavioral rule; conversation-protocol rules have equal priority to agent-instructions rules
- [x] 1.4 Add instruction to confirm conversation-protocol.md is loaded (via its `inclusion: auto` setting) and its rules are active before proceeding

## Task 2: Add Self-Answering Prohibition subsection to session-resume.md

- [x] 2.1 Create a "Self-Answering Prohibition" subsection within the Behavioral Rules Reload section with the exact prohibition text: "After asking any 👉 question, produce zero additional tokens. Do not answer the question. Do not assume the bootcamper's response. Do not generate placeholder answers like 'just me' or 'I will go with X.'"
- [x] 2.2 Add concrete violation examples (WRONG patterns) showing what the agent must not do after resume (e.g., generating "just me", "I'll go with Python", answering its own Ready to continue? question)
- [x] 2.3 Add correct behavior examples (CORRECT patterns) paired with each violation example showing the agent stopping immediately after the 👉 question
- [x] 2.4 Add instruction that while `config/.question_pending` exists, the agent must not generate any response content until the bootcamper provides input

## Task 3: Add Conversation Style Restoration section to session-resume.md

- [x] 3.1 Add instruction in Step 1 (Read All State Files) to read the `conversation_style` key from `config/bootcamp_preferences.yaml`
- [x] 3.2 Add a new Step 2c "Restore Conversation Style" section after Step 2b with instructions to apply stored style parameters (verbosity_preset, question_framing, tone, pacing)
- [x] 3.3 Add fallback logic: if `conversation_style` key does not exist, apply defaults (standard preset, conversational tone, moderate framing, one_concept_per_turn pacing) derived from conversation-protocol and verbosity-control settings
- [x] 3.4 Add tone descriptor mapping table: concise → short lead-ins and minimal preamble; conversational → moderate lead-ins and friendly framing; detailed → full contextual framing and thorough explanations
- [x] 3.5 Add style drift detection instruction: agent must compare first post-resume response style against the profile and self-correct if divergent; re-read profile after loading new module steering files

## Task 4: Add Conversation Style Persistence to agent-instructions.md

- [x] 4.1 Add instruction in the State & Progress section of agent-instructions.md to write a `conversation_style` profile to `config/bootcamp_preferences.yaml` after onboarding completes and the first module interaction establishes a baseline style
- [x] 4.2 Document the conversation_style schema: verbosity_preset (string), question_framing (minimal|moderate|full), tone (concise|conversational|detailed), pacing (one_concept_per_turn|grouped_concepts)

## Task 5: Add Conversation Style Update to verbosity-control.md

- [x] 5.1 Add instruction in the Adjustment Instructions section of verbosity-control.md to update the `conversation_style` key in the preferences file when the bootcamper requests a style change
- [x] 5.2 Specify that verbosity preset changes update `conversation_style.verbosity_preset` and `conversation_style.category_levels`; tone/pacing feedback updates the corresponding fields

## Task 6: Ensure welcome-back question compliance in session-resume.md

- [x] 6.1 Verify Step 3 ends with exactly one 👉 question ("Ready to continue with Module [N], or would you like to do something else?") combining options into a single question
- [x] 6.2 Add explicit instruction to write `config/.question_pending` with the question text after the welcome-back 👉 question
- [x] 6.3 Add 🛑 STOP marker after the question_pending write instruction to enforce the turn boundary

## Task 7: Write property-based tests

- [x] 7.1 Create `senzing-bootcamp/tests/test_session_resume_behavioral_rules_properties.py` with Hypothesis strategies for conversation style profiles (`st_conversation_style_profile`, `st_tone_descriptor`, `st_verbosity_preset`, `st_pacing_preference`)
- [x] 7.2 Implement Property 1 test: Behavioral Rules Reload completeness — verify all five rules with enforcement mechanisms are present
- [x] 7.3 Implement Property 2 test: Document ordering — verify Behavioral Rules Reload appears after Step 1 and before Step 3
- [x] 7.4 Implement Property 3 test: Self-Answering Prohibition contains both WRONG and CORRECT examples
- [x] 7.5 Implement Property 4 test: Question pending instruction exists after welcome-back question in Step 3
- [x] 7.6 Implement Property 5 test: Conversation style profile YAML round-trip serialization preserves all fields
- [x] 7.7 Implement Property 6 test: Behavioral Rules Reload references conversation-protocol.md and is shorter than the full file
- [x] 7.8 Implement Property 7 test: Step 3 contains exactly one 👉 question with no content after it
- [x] 7.9 Implement Property 8 test: Step 1 includes instruction to read conversation_style from preferences
- [x] 7.10 Implement Property 9 test: Tone descriptor mapping covers all three values (concise, conversational, detailed)
- [x] 7.11 Implement Property 10 test: agent-instructions.md contains conversation_style persistence instruction

## Task 8: Write unit tests

- [x] 8.1 Create `senzing-bootcamp/tests/test_session_resume_behavioral_rules_unit.py` with unit tests for conversation style profile validation (valid profiles, missing fields, invalid values)
- [x] 8.2 Add unit tests for fallback behavior: missing preferences file, missing conversation_style key, malformed data
- [x] 8.3 Add unit tests verifying the Self-Answering Prohibition examples are correctly formatted (each WRONG has a paired CORRECT)
- [x] 8.4 Add unit test verifying session-resume.md Step 2b instruction to re-read conversation-protocol.md exists

## Task 9: Update steering-index.yaml

- [x] 9.1 Update `senzing-bootcamp/steering/steering-index.yaml` token counts for session-resume.md after modifications
- [x] 9.2 Update token counts for agent-instructions.md and verbosity-control.md if their sizes change significantly

## Task 10: Run tests and validate

- [x] 10.1 Run the full property-based test suite with `pytest senzing-bootcamp/tests/test_session_resume_behavioral_rules_properties.py -v`
- [x] 10.2 Run the unit test suite with `pytest senzing-bootcamp/tests/test_session_resume_behavioral_rules_unit.py -v`
- [x] 10.3 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` to verify all modified steering files remain valid CommonMark
- [x] 10.4 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to verify token budgets are not exceeded
