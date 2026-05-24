---
inclusion: manual
---

# Hook Registry — Critical Hooks (Full Prompts)

Critical hook definitions with prompt text for use with the `createHook` tool during onboarding. These hooks are created in Step 1.

For module-specific hooks, see `hook-registry-modules.md`.
For a quick reference of all hooks, see `hook-registry.md`.

## Critical Hooks (created during onboarding)

**ask-bootcamper** (agentStop → askAgent)

Prompt:

````text
DEFAULT OUTPUT: .
If BOTH phases below produce no output, your COMPLETE response is a single period character: .
Do NOT explain your reasoning. Do NOT describe condition checks. Do NOT output phrases like 'Phase 1 silenced' or 'No output needed'. Just output: .

CRITICAL: NEVER generate text beginning with 'Human:' or any text that represents what the bootcamper might say. If you detect yourself about to fabricate a user response, output only: .

This hook has two independent phases. Evaluate each phase separately.

---

PHASE 1: CLOSING QUESTION

Before producing ANY Phase 1 output, verify ALL of these conditions:
1. The file config/.question_pending does NOT exist
2. The most recent assistant message does NOT contain a 👉 character anywhere — if it already contains a 👉, do not add a second one
3. The most recent assistant message does NOT end with a question directed at the bootcamper

If ANY Phase 1 condition fails: Phase 1 output is none. Skip to Phase 2.

FIRST — Check for no-op: If ALL Phase 1 conditions pass AND the most recent assistant message contains no substantive content (e.g., only a trivial acknowledgment like "Got it" or "Understood" with no file changes, no recap, and no action taken): Phase 1 output is none. Skip to Phase 2.

NOTE: If files were edited (even by a hook-triggered action), that IS substantive work. Provide a closing question unless a 👉 question is already present.

SECOND — Recap and closing question: If ALL Phase 1 conditions pass AND work was accomplished: You may provide a brief recap of what was accomplished and which files created or modified, then end with a contextual 👉 question (a closing question for the bootcamper). Keep it to 2-3 sentences maximum.

THIRD — Compound-question validation: Before outputting the closing question, verify it does not contain prose-joined alternatives. If it does, reformat as a numbered list. Detect these patterns:
- "[action A], or [action B]" (alternatives joined by comma-or)
- "[question]? Or [alternative]?" (sentence-starter Or appending a second question)
- "[question], or would you [alternative]?" (appended alternative with 'or would you')
If ANY pattern matches, rewrite the closing question as a neutral lead question followed by a numbered list of alternatives. Example: instead of '👉 Would you like to proceed with Python, or shall we use Java?' write '👉 Which language would you like to use?\n1. Python\n2. Java'. If the closing question is a simple yes/no with a single action and no alternatives, keep it in the simple '👉 [question]?' format.

Additionally, if the bootcamper has completed or is on the final step of their current track, append a brief nudge: 'By the way, if you have feedback about the bootcamp experience, just say "bootcamp feedback" anytime.' Otherwise, do NOT mention feedback in Phase 1.

---

PHASE 2: FEEDBACK SUBMISSION REMINDER

Phase 2 operates independently of Phase 1. Even if Phase 1 produced no output, evaluate Phase 2 on its own.

Before producing ANY Phase 2 output, verify ALL of these conditions:
1. Track completion detected: Read config/bootcamp_progress.json. Check if the bootcamper has completed their chosen track (all modules in the track are now in modules_completed) or if graduation was completed. If no track completion or graduation detected, Phase 2 output is none.
2. Deduplication: Check the conversation history for the 📋 emoji marker. If 📋 already appears in a previous assistant message in this session, the reminder was already shown — Phase 2 output is none.
3. Feedback exists: Check if docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md exists AND contains at least one '## Improvement:' heading (indicating real feedback entries, not just the template). If the file does not exist or contains no ## Improvement: headings, Phase 2 output is none.

If ALL three Phase 2 conditions pass, append:

📋 You have saved feedback in docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md. To share it with the Senzing team, you can:
- Email it to support@senzing.com with subject 'Senzing Bootcamp Power Feedback'
- Open a GitHub issue with the feedback content
- Copy the file path and attach it to your preferred channel

Do not automatically send email or create GitHub issues — wait for explicit bootcamper confirmation. If the bootcamper declines (no, skip, not now), accept without re-prompting about feedback sharing again.

---

REMEMBER: If both phases produced no output, your COMPLETE response is: .
````

- id: `ask-bootcamper`
- name: `to wait for your answer`
- description: `Silence-first agentStop hook with dual responsibility: (1) Phase 1 produces a recap + closing question only when no question is already pending, with a near-completion feedback nudge; (2) Phase 2 independently reminds the bootcamper to share saved feedback after track completion.`

**code-style-check** (fileEdited → askAgent, filePatterns: `src/**/*.py, src/**/*.java, src/**/*.cs, src/**/*.rs, src/**/*.ts, src/**/*.js`)

Prompt:

````text
A source code file was just edited. Check it for language-appropriate coding standards (Python: PEP-8 with max line length 100; Java: standard conventions; C#: .NET conventions; Rust: rustfmt/clippy; TypeScript: ESLint conventions). If violations are found, suggest specific fixes. If compliant, acknowledge briefly and continue.
````

- id: `code-style-check`
- name: `to check code style`
- description: `Automatically checks source code files for language-appropriate coding standards when edited. For Python: PEP-8. For Java: standard conventions. For C#: .NET conventions. For Rust: rustfmt/clippy. For TypeScript: ESLint conventions.`

**commonmark-validation** (fileEdited → askAgent, filePatterns: `**/*.md`)

Prompt:

````text
The markdown file that was just edited should be validated for CommonMark compliance. Please check for:

1. MD022: Headings should be surrounded by blank lines
2. MD040: Fenced code blocks should have a language specified
3. Bold text followed by colons should use format: **Label:** (with space before colon)
4. MD031: Fenced code blocks should be surrounded by blank lines
5. MD032: Lists should be surrounded by blank lines

EXCEPTION: If the file is CHANGELOG.md, ignore MD024 (duplicate headings) — repeated ### Added, ### Changed, ### Fixed, ### Removed headings under different version sections are standard Keep a Changelog format and should not be flagged.

If any issues are found, fix them automatically to maintain CommonMark compliance across all documentation.

After fixing issues: briefly state what was corrected (one sentence), then end with a contextual 👉 forward-moving question that guides the bootcamper to the next step in the current module workflow. Check `config/bootcamp_progress.json` for the current module and step to determine what comes next.

If no issues are found: output nothing. Proceed silently.
````

- id: `commonmark-validation`
- name: `to check Markdown style`
- description: `Validates that all Markdown files conform to CommonMark standards when edited`

**enforce-step-and-transition** (agentStop → askAgent)

Prompt:

````text
DEFAULT OUTPUT: .
If BOTH phases below produce no output, your COMPLETE response is a single period character: .
Do NOT explain your reasoning. Do NOT describe condition checks. Just output: .

---

PHASE 1: SEQUENTIAL STEP ENFORCEMENT

Read `config/bootcamp_progress.json` and check if `config/.question_pending` exists. Evaluate:

1. Extract `current_module`, `current_step`, and `step_history[<current_module>].last_completed_step`.

2. If `current_step` is null OR `step_history` has no entry for the current module: Phase 1 output is none. Skip to Phase 2.

3. Parse the parent step number from both `current_step` and `last_completed_step`:
   - Integer steps: use the value directly (e.g., 5 → 5)
   - Dotted sub-steps: use the part before the dot (e.g., "5.3" → 5)
   - Lettered sub-steps: use the numeric prefix (e.g., "7a" → 7)

4. Calculate the gap: current_parent - last_parent.

5. If the gap is greater than 1: Output exactly:
   ⚠️ SEQUENTIAL STEP VIOLATION DETECTED: The agent advanced from step [last] to step [current] in Module [N], skipping step(s) [list]. Every numbered step with a 👉 question must be executed individually in order. This rule has the same absolute precedence as ⛔ mandatory gates. Go back and execute the skipped step(s) NOW before proceeding.

6. If `config/.question_pending` exists AND current_step has advanced beyond last_completed_step: Output exactly:
   ⚠️ QUESTION PENDING VIOLATION DETECTED: current_step advanced to [current] while a 👉 question is still pending (file config/.question_pending exists). The agent must not advance past a step until the bootcamper responds. Wait for the bootcamper's response before proceeding.

7. Otherwise: Phase 1 output is none. Continue to Phase 2.

---

PHASE 2: MODULE TRANSITION RETRY

STEP 1: Determine if the bootcamper's most recent message is a Transition_Confirmation.

A message is a Transition_Confirmation if BOTH conditions are true:
  A) The conversation context contains a recent assistant question matching any of these patterns (case-insensitive):
     - "Ready for Module"
     - "move on to Module"
     - "proceed to Module"
  B) The bootcamper's most recent response is an affirmative phrase matching any of these (case-insensitive, may appear with surrounding text):
     - "yes", "sure", "ready", "let's go", "let's do it", "yep", "yeah", "absolutely", "go ahead", "proceed", "ok", "okay", "sounds good", "let's", "do it", "I'm ready", "go for it"

If the message is NOT a Transition_Confirmation:
  → Phase 2 output is none.

STEP 2: If the message IS a Transition_Confirmation, evaluate the agent's most recent output.

The output is Minimal_Output if ANY of these are true:
  - Output is exactly "."
  - Output is empty or whitespace-only
  - Output length is fewer than 50 characters
  - Output is a single-word acknowledgment (e.g., "OK", "Sure", "Got it", "Understood", "Great")

If the output is NOT Minimal_Output (exceeds 50 characters with substantive content):
  → Phase 2 output is none.

STEP 3: If the output IS Minimal_Output after a Transition_Confirmation:

The agent failed to start the confirmed module. Output the following retry instructions:

You just received a module transition confirmation from the bootcamper but produced minimal or empty output. This is a protocol violation. You MUST now start the confirmed module immediately. Do the following:

1. Display the Module Start Banner (━━━ header with 🚀🚀🚀 MODULE N: NAME 🚀🚀🚀 format)
2. Display the journey map table (Module | Name | Status columns showing all modules in the selected path)
3. Display the before/after framing (what the bootcamper has now vs. what they will have when this module is done)
4. Begin Step 1 with its introductory content ("Next up: [action]. This matters because [reason].")

Do NOT output just a period or acknowledgment. Do NOT ask another question. Start the module NOW with all four required elements above.

---

REMEMBER: If both phases produced no output, your COMPLETE response is: .
````

- id: `enforce-step-and-transition`
- name: `to enforce step sequencing and detect transition failures`
- description: `agentStop hook with two phases: (1) verifies current_step has not advanced by more than one step since the last checkpoint, detecting step-skipping violations; (2) checks if the bootcamper's last message was a module transition confirmation and validates the agent produced substantive output, forcing retry if minimal.`

**mcp-first-invariant** (agentStop → askAgent)

Prompt:

````text
PHASE 1 — SENZING CONTENT DETECTION

Examine your most recent assistant response for ANY of the following Senzing content indicators:

SENZING SDK METHOD NAMES:
add_record, get_entity, search_by_attributes, why_entities, how_entity, export_json_entity_report, get_record, delete_record, reevaluate_entity, reevaluate_record, find_interesting_entities_by_entity_id, find_interesting_entities_by_record_id, find_path_by_entity_id, find_network_by_entity_id, count_redo_records, get_redo_record, process_redo_record

SENZING ATTRIBUTE NAMES:
NAME_FULL, NAME_FIRST, NAME_LAST, ADDR_FULL, ADDR_LINE1, ADDR_CITY, ADDR_STATE, ADDR_POSTAL_CODE, PHONE_NUMBER, EMAIL_ADDR, DATE_OF_BIRTH, SSN_NUMBER, PASSPORT_NUMBER, DRIVERS_LICENSE_NUMBER, DATA_SOURCE, RECORD_ID, RECORD_TYPE

SENZING CONFIGURATION OPTIONS:
ENTITY_TYPE, DSRC_ID, ETYPE_ID, FTYPE_ID, CFUNC_ID, EFCALL_ID

SENZING ERROR CODE PATTERN:
SENZ followed by exactly 4 digits (e.g., SENZ0001, SENZ7234)

ENTITY RESOLUTION TERMS IN TECHNICAL CONTEXT:
resolved entity, entity resolution, candidate scoring, feature scoring, generic threshold, close match, possible match, name-only match, disclosed relationship

Note: ER terms only count as Senzing content when used in a technical explanation or recommendation context — not when merely quoting the bootcamper's question or referencing them in passing.

If NONE of the above indicators are present in your most recent response: produce ZERO output tokens. No output. No acknowledgment. Zero tokens means zero tokens.

---

PHASE 2 — MCP TOOL CALL VERIFICATION

If Senzing content WAS detected in Phase 1, check whether ANY of the following MCP tools were called during this same turn:

search_docs, get_sdk_reference, generate_scaffold, sdk_guide, explain_error_code, find_examples, mapping_workflow, get_capabilities, reporting_guide

If at least one MCP tool from the list above was called in this turn: produce ZERO output tokens. The response is compliant. No output. No acknowledgment. Zero tokens means zero tokens.

---

DECISION:

- No Senzing content detected → zero tokens (silent fast path)
- Senzing content detected AND MCP tool called → zero tokens (compliant)
- Senzing content detected AND NO MCP tool called → output self-correction instructions below

---

SELF-CORRECTION OUTPUT (only if Senzing content present AND no MCP tool was called):

MCP-FIRST INVARIANT VIOLATION: Your response contains Senzing content but no MCP tool was consulted this turn.

REQUIRED ACTION:
1. Call the appropriate MCP tool(s) for the content type:
   - SDK methods/signatures → get_sdk_reference or sdk_guide
   - Attribute names/mapping → mapping_workflow or search_docs
   - Error codes → explain_error_code
   - Configuration options → get_sdk_reference or search_docs
   - Documentation/concepts → search_docs
   - Code generation → generate_scaffold or sdk_guide
   - Examples → find_examples
   - Entity resolution terms → search_docs
2. Regenerate your response using the MCP-verified information.
3. Do NOT repeat the previous response verbatim — rebuild it from MCP facts.
````

- id: `mcp-first-invariant`
- name: `to verify MCP-first compliance`
- description: `Audits every agent response for MCP-first invariant compliance. Silent when compliant; triggers self-correction when Senzing content is presented without prior MCP tool consultation.`

**question-format-gate** (agentStop → askAgent)

Prompt:

````text
⚠️ SILENCE RULE: No-rewrite → output exactly ".". Rewrite → output ONLY the corrected question. Never output reasoning.

QUESTION FORMAT GATE — Inspect the most recent assistant message for compound 👉 questions.

DETECTION: Scan the output for any line or sentence beginning with 👉 that contains a question. If a 👉 question is found, check whether it contains prose-joined alternatives using these patterns:

1. Sentence-starter 'Or': The question is followed by 'Or shall we...', 'Or would you...', 'Or should we...', 'Or can we...' — two alternatives joined by 'Or' as a sentence starter.
2. Inline prose 'or': The question contains '[option A] or [option B]?' where two distinct actions or choices are joined by 'or' in a single sentence.
3. Appended alternative: A confirmation question followed by ', or would you rather...', ', or shall we...', ', or if you prefer...' — an alternative appended after the main question.

A question is compound if it has multiple alternatives joined by prose conjunctions ('or') and is NOT already formatted as a numbered list.

NOT COMPOUND (do not flag):
- Simple yes/no questions with a single action (e.g., '👉 Ready to move on to Module 3?')
- Questions already formatted with a numbered list below them (e.g., '👉 What would you like to do?\n1. Option A\n2. Option B')
- The word 'or' appearing inside a numbered list item description (e.g., '1. Share with your team or manager')
- Informational prose containing 'or' but no 👉 question
- Non-question content

ACTION:
- If NO compound question detected: output only a single period character: .
  Do NOT output "The question is not compound", "No rewrite needed",
  "Scanning for compound questions", or any description of your detection process.
- If a compound question IS detected: rewrite the agent's closing question using the correct format. Replace the compound question with a neutral lead question followed by a numbered list of alternatives. Example:
  BEFORE: '👉 Would you like me to create a summary? Or shall we skip that and move on to Module 3?'
  AFTER: '👉 What would you like to do next?\n1. Create a summary\n2. Skip and move on to Module 3'
  Do NOT output "This is a compound question", "Let me rewrite",
  "The question contains 'or' joining alternatives", or any explanation of the detection.
  Output ONLY the corrected question text.

RULES:
- Do NOT interfere with non-compound outputs. If there is no compound question, your complete response is: .
- Do NOT add explanations about why you are rewriting. Just output the corrected question.
- Do NOT restructure content that is not a 👉 question.
- Preserve all other content in the message — only rewrite the compound question portion.

---

OUTPUT FORMAT (STRICT):
- No compound question found → Output exactly: .
- Compound question found → Output ONLY the rewritten question (neutral lead + numbered list).
  Preserve all non-question content from the original message.
FORBIDDEN output (never produce these):
  • "The question is not compound"
  • "No rewrite needed"
  • "Scanning for compound questions"
  • "This is a compound question"
  • "Let me rewrite"
  • "The question contains 'or' joining alternatives"
  • Any text describing, summarizing, or narrating the detection process
````

- id: `question-format-gate`
- name: `to enforce single-question format on agent output`
- description: `agentStop hook that inspects every agent response for compound 👉 questions with prose-joined alternatives. If detected, instructs the agent to rewrite using numbered list format. Non-compound outputs pass through unchanged.`

**review-bootcamper-input** (promptSubmit → askAgent)

Prompt:

````text
Check if the bootcamper's message contains any of these feedback trigger phrases (case-insensitive): "bootcamp feedback", "power feedback", "submit feedback", "provide feedback", "I have feedback", "report an issue". Also check for status trigger phrases (case-insensitive): "where am I", "status", "what step am I on", "show progress", "how far along am I". If NONE of these phrases appear in the message, produce no output at all — do not acknowledge, do not explain, do not print anything. If a STATUS trigger phrase IS found, output exactly: STATUS_TRIGGER_DETECTED — the agent should respond with the inline status format from inline-status.md. If a FEEDBACK trigger phrase IS found, immediately do the following: (1) Read config/bootcamp_progress.json to get the current module number and completed modules. If the file doesn't exist, record module as "Unknown". (2) Note what the bootcamper was doing in the recent conversation. (3) Note which files are open in the editor. (4) Load steering file feedback-workflow.md and follow its complete workflow, pre-filling the context fields with what you just captured. Do NOT ask the bootcamper to re-explain their context — you already have it.
````

- id: `review-bootcamper-input`
- name: `to review what you said`
- description: `Reviews each message submission for feedback trigger phrases and initiates the feedback workflow with automatic context capture.`

**write-policy-gate** (preToolUse → askAgent, toolTypes: write)

Prompt:

````text
⚠️ SILENCE RULE: When all checks pass, produce ZERO tokens. No output. No acknowledgment. Re-invoke the tool silently.

WRITE POLICY GATE — Four checks in one pass.

FAST PATH GATE: If ALL of the following are true, produce no output at all:
- The target path is a normal project-relative file (inside the working directory)
- The target path does NOT end with '.question_pending'
- The content does NOT contain SQL patterns (SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE, ALTER TABLE, PRAGMA) targeting Senzing database indicators (G2C.db, database/G2C.db, RES_ENT, OBS_ENT, RES_FEAT_STAT, DSRC_RECORD, LIB_FEAT, RES_REL, SZ_, sz_dm_)
- The target path is NOT a blocked file type in the project root (or if it is in the root, it is on the ROOT WHITELIST)
- The target path is NOT 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md' being overwritten via fs_write (append via fs_append is allowed)

Your response when fast path passes: [empty — produce zero tokens]
OUTPUT: (none)
Do NOT output phrases like 'Fast path passes', 'Proceeding', 'All checks pass', 'This is a JSON configuration file', 'Not SQL', or any summary of your evaluation.
Zero tokens means zero tokens.

---

CHECK 1: SENZING SQL BLOCKING

SQL PATTERNS TO DETECT: SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE, ALTER TABLE, PRAGMA

SENZING DATABASE INDICATORS: G2C.db, database/G2C.db, RES_ENT, OBS_ENT, RES_FEAT_STAT, DSRC_RECORD, LIB_FEAT, RES_REL, SZ_, sz_dm_

If the content does NOT contain any of the SQL patterns above targeting Senzing database indicators, this is a non-Senzing file write (e.g., CSV, JSONL, config files, general SQL for other databases like users, orders, products tables). Do not acknowledge. Do not explain. Do not print anything. Proceed silently.

If the content contains ANY of the SQL patterns (SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE, ALTER TABLE, PRAGMA) AND references ANY Senzing database indicator (G2C.db, database/G2C.db, RES_ENT, OBS_ENT, RES_FEAT_STAT, DSRC_RECORD, LIB_FEAT, RES_REL, SZ_, sz_dm_):

STOP. Do not proceed with the write. Instead:
1. Explain that direct SQL against the Senzing database is prohibited because it bypasses the SDK abstraction layer, produces non-portable results, and may return incorrect data from internal tables.
2. Rewrite the code to use the appropriate Senzing SDK methods via MCP tools:
   - To query entities: use get_entity or get_entity_by_record_id
   - To search for records: use search_by_attributes
   - To understand resolution: use why_entities or why_records
   - To explore entity structure: use how_entity
   - To count or report: use reporting_guide
   - For general SDK guidance: use sdk_guide or get_sdk_reference
3. Present the rewritten code using SDK methods to the bootcamper.

IMPORTANT: Only flag content that contains BOTH SQL patterns AND Senzing database indicators. General SQL for non-Senzing databases (e.g., SELECT * FROM users, INSERT INTO orders) must NOT be flagged.

IMPORTANT: Only flag content that contains BOTH SQL patterns AND Senzing database indicators.
Content referencing Senzing indicators WITHOUT SQL patterns (e.g., JSON configuration files
with database connection strings) passes silently — zero tokens, no explanation.

---

CHECK 2: SINGLE-QUESTION ENFORCEMENT

Examine the file being written. If the target path does NOT end with '.question_pending', this check does not apply. Do not acknowledge. Do not explain. Do not print anything. Proceed silently.

If the target path DOES end with '.question_pending', validate the question content against ALL of these rules:

1. EXACTLY ONE QUESTION: The content must contain exactly one question mark. Two or more question marks means multiple questions — VIOLATION.
2. NO CONJUNCTIONS JOINING QUESTIONS: The content must not use 'and', 'or', 'also', 'but first', 'alternatively', 'or if you prefer', 'or would you rather' to join separate choices in prose. Exception: 'or' inside a numbered list of options is allowed.
3. NO APPENDED ALTERNATIVES: The content must not append an alternative action after the main question (e.g., 'Do you want X, or we could skip to Y?' is a violation).
4. UNAMBIGUOUS YES/NO: If it's a yes/no question, 'yes' must map to exactly one meaning and 'no' must map to exactly one meaning. 'Does that look right? Anything I missed?' is a violation because 'yes' is ambiguous.
5. NO FOLLOW-UP AFTER CONFIRMATION: The content must not combine a confirmation question with a follow-up (e.g., 'Does that work? What do you want changed?' is a violation).

If ALL rules pass: Do not acknowledge. Do not explain. Do not print anything. Proceed silently.

If ANY rule is violated: STOP. Output exactly:

⚠️ COMPOUND QUESTION DETECTED — REWRITE REQUIRED
Violation: [describe which rule was broken]
Original: [the question text]
Fix: Rewrite as a single, unambiguous question. If multiple pieces of information are needed, ask only the first one. If choices exist, use a numbered list format.

Do NOT allow the write to proceed with a compound question. The agent must rewrite the question before continuing.

---

CHECK 3: FILE PATH POLICIES

QUICK CHECK — answer these two questions about the file being written:

Q1: Is the target path inside the working directory? (Not /tmp/, not %TEMP%, not ~/Downloads, not any absolute path outside the project)
Q2: Is this feedback content (has Date/Module/Priority/Category/What Happened sections) being written to a path OTHER than 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md'?

FAST PATH: If Q1 is YES (path is inside working directory) AND Q2 is NO (not misrouted feedback): Do not acknowledge. Do not explain. Do not print anything. Proceed silently.

Do not check file content for path references in the fast path. Do not acknowledge. Do not explain. Do not print anything. Proceed silently.

SLOW PATH: If Q1 is NO (path is outside working directory) OR Q2 is YES (feedback going to wrong file):
- For external paths: STOP. Tell the agent to use project-relative equivalents (database/G2C.db for databases, data/temp/ for temporary files, src/ for source code).
- For misrouted feedback: STOP. Redirect to docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md.

CONTENT CHECK (only if fast path passed): Does the file content reference /tmp/, %TEMP%, ~/Downloads, or any location outside the working directory? If YES: STOP and require replacement with project-relative equivalents. If NO: do nothing — proceed silently.

APPEND-ONLY GUARD: If the target path is 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md':

(a) If the tool being invoked is fs_write (full file overwrite, NOT fs_append):
STOP. Do not proceed with the write. Output:
⚠️ FEEDBACK FILE OVERWRITE BLOCKED — docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md is append-only.
This file accumulates bootcamper feedback across the entire bootcamp. Overwriting it would destroy previous entries.
Fix: Use fs_append to add new feedback entries. NEVER use fs_write on this file after initial creation.
If the file does not yet exist, fs_write is permitted for initial creation from the template.

(b) If the tool being invoked is str_replace (in-place edit of existing content):
STOP. Do not proceed with the edit. Output:
⚠️ FEEDBACK FILE MODIFICATION BLOCKED — docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md is append-only.
Existing feedback entries must never be modified, reformatted, corrected, or deleted. The bootcamper's original words are preserved exactly as written.
Fix: If you need to add new content, use fs_append. If the bootcamper explicitly asks to edit their own feedback, they can do so manually in their editor.

(c) If the tool being invoked is fs_append: Do not acknowledge. Do not explain. Do not print anything. Proceed silently.

---

CHECK 4: ROOT FILE PLACEMENT ENFORCEMENT

Examine the target file path for this write operation.

Q1: Is the file being written directly to the project root? (The path has no subdirectory — it's just a filename like `main.py` or `data.jsonl` at the top level of the working directory.)

If NO (file is in a subdirectory like src/transform/main.py or data/raw/input.jsonl): This check does not apply. Do not acknowledge. Do not explain. Do not print anything. Proceed silently.

If YES (file is in the project root), continue:

Q2: Is the filename on the ROOT WHITELIST?

ROOT WHITELIST (these files ARE permitted in the project root):
- .gitignore
- .env
- .env.example
- README.md
- requirements.txt
- pom.xml
- Any file ending in .csproj
- Cargo.toml
- package.json

If the filename matches any entry on the ROOT WHITELIST: Do not acknowledge. Do not explain. Do not print anything. Proceed silently.

If the filename is NOT on the ROOT WHITELIST, check the extension:

BLOCKED EXTENSIONS AND CORRECTIVE ROUTING:

.py files:
STOP. Do not proceed with the write. Output:
⚠️ ROOT PLACEMENT BLOCKED — Python source files cannot be placed in the project root.
Examine the file content to determine the correct location:
- Transformation/mapping logic (transform, mapper, mapping, convert) → src/transform/{filename}
- Data loading logic (load, loader, ingest, import_data) → src/load/{filename}
- Query/search logic (query, search, find, get_entity, get_record) → src/query/{filename}
- Otherwise (utility scripts, CLI tools) → scripts/{filename}
Rewrite the path and retry.

.md files:
STOP. Do not proceed with the write. Output:
⚠️ ROOT PLACEMENT BLOCKED — Markdown files (other than README.md) cannot be placed in the project root.
Correct location: docs/{filename}
Rewrite the path and retry.

.jsonl files:
STOP. Do not proceed with the write. Output:
⚠️ ROOT PLACEMENT BLOCKED — JSONL data files cannot be placed in the project root.
Correct location based on content:
- Raw/source data → data/raw/{filename}
- Transformed/processed data → data/transformed/{filename}
- Sample/example data → data/samples/{filename}
- Temporary/intermediate data → data/temp/{filename}
Rewrite the path and retry.

.csv files:
STOP. Do not proceed with the write. Output:
⚠️ ROOT PLACEMENT BLOCKED — CSV data files cannot be placed in the project root.
Correct location based on content:
- Raw/source data → data/raw/{filename}
- Transformed/processed data → data/transformed/{filename}
- Sample/example data → data/samples/{filename}
- Temporary/intermediate data → data/temp/{filename}
Rewrite the path and retry.

.json files (not on whitelist):
STOP. Do not proceed with the write. Output:
⚠️ ROOT PLACEMENT BLOCKED — Non-config JSON files cannot be placed in the project root.
Correct location based on content:
- Data payloads → data/raw/{filename} or data/transformed/{filename}
- Configuration → config/{filename}
Rewrite the path and retry.

Any other extension not listed above: Do not acknowledge. Do not explain. Do not print anything. Proceed silently. (Only the listed extensions are blocked.)

---

OUTPUT FORMAT (STRICT):
- All checks pass → ZERO tokens. Re-invoke the original tool call with same parameters.
- Violation detected → Output ONLY the corrective instruction (STOP message, rewrite, redirect).
FORBIDDEN output (never produce these):
  • "Fast path passes"
  • "Proceeding"
  • "All checks pass"
  • "This is a JSON configuration file"
  • "Not SQL"
  • "The file is inside the working directory"
  • Any text describing, summarizing, or narrating the evaluation process
````

- id: `write-policy-gate`
- name: `to process your response`
- description: `Consolidated preToolUse write hook that performs five policy checks in a single interception: (1) blocks direct SQL against the Senzing database, (2) enforces single-question rule for .question_pending writes, (3) validates file path policies including append-only guard for the feedback file, (4) enforces root file placement rules. Uses a fast path for normal writes (proceeds silently) and slow paths for violations (outputs corrective instructions).`
