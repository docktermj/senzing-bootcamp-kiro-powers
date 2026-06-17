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
If ALL phases below produce no output, your COMPLETE response is a single period character: .
Do NOT explain your reasoning. Do NOT describe condition checks. Do NOT output phrases like 'Phase 1 silenced' or 'No output needed'. Just output: .

CRITICAL: NEVER generate text beginning with 'Human:' or any text that represents what the bootcamper might say. If you detect yourself about to fabricate a user response, output only: .

This hook has four phases. Phase 2 contains three sub-phases (2A: Sequential Step Enforcement, 2B: Answer Processing Retry, 2C: Not-Waiting Detection). Evaluate each phase in order. If Phase 2 or Phase 3 detects a violation, that takes priority over Phase 1's closing question. Phase 4 operates on the output that would be shown to the bootcamper, so it runs last.

════════════════════════════════════════════════════════════════════════════════
PHASE 1: CLOSING QUESTION (Closing_Question_Phase)
════════════════════════════════════════════════════════════════════════════════

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

FEEDBACK SUBMISSION REMINDER (sub-phase of Phase 1):

This sub-phase operates independently. Even if the main Phase 1 produced no output, evaluate this on its own.

Before producing ANY feedback reminder output, verify ALL of these conditions:
1. Track completion detected: Read config/bootcamp_progress.json. Check if the bootcamper has completed their chosen track (all modules in the track are now in modules_completed) or if graduation was completed. If no track completion or graduation detected, feedback reminder output is none.
2. Deduplication: Check the conversation history for the 📋 emoji marker. If 📋 already appears in a previous assistant message in this session, the reminder was already shown — feedback reminder output is none.
3. Feedback exists: Check if docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md exists AND contains at least one '## Improvement:' heading (indicating real feedback entries, not just the template). If the file does not exist or contains no ## Improvement: headings, feedback reminder output is none.

If ALL three feedback reminder conditions pass, append:

📋 You have saved feedback in docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md. To share it with the Senzing team, you can:
- Email it to support@senzing.com with subject 'Senzing Bootcamp Power Feedback'
- Open a GitHub issue with the feedback content
- Copy the file path and attach it to your preferred channel

Do not automatically send email or create GitHub issues — wait for explicit bootcamper confirmation. If the bootcamper declines (no, skip, not now), accept without re-prompting about feedback sharing again.

════════════════════════════════════════════════════════════════════════════════
PHASE 2: STEP SEQUENCING (Step_Sequencing_Phase)
════════════════════════════════════════════════════════════════════════════════

SUB-PHASE 2A: SEQUENTIAL STEP ENFORCEMENT

Read `config/bootcamp_progress.json` and check if `config/.question_pending` exists. Evaluate:

1. Extract `current_module`, `current_step`, and `step_history[<current_module>].last_completed_step`.

2. If `current_step` is null OR `step_history` has no entry for the current module: Sub-phase 2A output is none. Skip to Sub-phase 2B.

3. Parse the parent step number from both `current_step` and `last_completed_step`:
   - Integer steps: use the value directly (e.g., 5 → 5)
   - Dotted sub-steps: use the part before the dot (e.g., "5.3" → 5)
   - Lettered sub-steps: use the numeric prefix (e.g., "7a" → 7)

4. Calculate the gap: current_parent - last_parent.

5. If the gap is greater than 1: Output exactly:
   ⚠️ SEQUENTIAL STEP VIOLATION DETECTED: The agent advanced from step [last] to step [current] in Module [N], skipping step(s) [list]. Every numbered step with a 👉 question must be executed individually in order. This rule has the same absolute precedence as ⛔ mandatory gates. Go back and execute the skipped step(s) NOW before proceeding.

6. If `config/.question_pending` exists AND current_step has advanced beyond last_completed_step: Output exactly:
   ⚠️ QUESTION PENDING VIOLATION DETECTED: current_step advanced to [current] while a 👉 question is still pending (file config/.question_pending exists). The agent must not advance past a step until the bootcamper responds. Wait for the bootcamper's response before proceeding.

7. Otherwise: Sub-phase 2A output is none. Continue to Sub-phase 2B.

SUB-PHASE 2B: ANSWER PROCESSING RETRY

STEP 1: Check activation conditions.

Both conditions must be true for Sub-phase 2B to activate:
  A) The file `config/.question_pending` exists
  B) The agent's most recent output is Minimal_Output

The output is Minimal_Output if ANY of these are true:
  - Output is exactly "."
  - Output is empty or whitespace-only
  - Output length is fewer than 50 characters
  - Output is a single-word acknowledgment (e.g., "OK", "Sure", "Got it", "Understood", "Great")

If EITHER condition fails (file does not exist OR output is not minimal):
  → Sub-phase 2B output is none.

STEP 2: Extract the question type from `config/.question_pending`.

Read the first line of the file. If the first line matches one of the known types (track_selection, module_transition, step_question, confirmation, choice), use that as the question type. Otherwise, use "unknown" as the question type.

STEP 3: Issue type-specific retry instructions based on the question type.

The agent failed to process the bootcamper's answer to a pending 👉 question. This is a protocol violation. Based on the question type, issue the appropriate retry instructions:

If type is "track_selection":
  Read the bootcamper's track choice from their most recent message. Update config/bootcamp_progress.json with the selected track. Save preferences to config/bootcamp_preferences.yaml. Begin Module 1.

If type is "module_transition":
  Display the module start banner (━━━ header with 🚀🚀🚀 MODULE N: NAME 🚀🚀🚀 format). Display the journey map table. Display the before/after framing. Begin Step 1.

If type is "step_question":
  Read the bootcamper's answer from their most recent message. Incorporate the answer into the current step's workflow. Update progress. Present the next action or question.

If type is "confirmation":
  Treat the bootcamper's response as a confirmation. Proceed with the confirmed action.

If type is "choice":
  Read the bootcamper's selection from the numbered choice list. Acknowledge the choice. Proceed with the selected option.

If type is "unknown" (fallback):
  Re-read the bootcamper's most recent message. Treat it as an answer to the pending question. Produce a substantive response.

Do NOT output just a period or acknowledgment. Process the bootcamper's answer NOW and produce substantive output.

SUB-PHASE 2C: NOT-WAITING DETECTION

STEP 1: Check activation conditions.

ALL of the following conditions must be true for Sub-phase 2C to activate:
  A) The file `config/.question_pending` exists
  B) The agent's most recent output is NOT Minimal_Output (it is substantive)
  C) The agent's most recent output contains workflow-advancing content: step headers (e.g., '## Step N', '**Step N**'), module banners (e.g., '━━━', '🚀🚀🚀 MODULE'), or new 👉 questions
  D) The file `config/.question_pending` was NOT deleted during this turn (it still exists)

If ANY condition fails:
  → Sub-phase 2C output is none.

STEP 2: Issue not-waiting violation recovery instructions.

The agent advanced the workflow while a question is still pending. This is a not-waiting violation.

⚠️ NOT-WAITING VIOLATION DETECTED: The agent produced workflow-advancing output (step content, module content, or new questions) while config/.question_pending still exists. The agent must not advance past a pending 👉 question without the bootcamper's response.

REQUIRED ACTION:
1. Discard the premature output — do NOT show it to the bootcamper.
2. Acknowledge that a question is still pending and awaiting the bootcamper's response.
3. Wait for the bootcamper's response before producing any further workflow content.

════════════════════════════════════════════════════════════════════════════════
PHASE 3: MCP-FIRST COMPLIANCE (MCP_First_Phase)
════════════════════════════════════════════════════════════════════════════════

SUB-PHASE 3A — SENZING CONTENT DETECTION

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

If NONE of the above indicators are present in your most recent response: Phase 3 output is none.

SUB-PHASE 3B — MCP TOOL CALL VERIFICATION

If Senzing content WAS detected in Sub-phase 3A, check whether ANY of the following MCP tools were called during this same turn:

search_docs, get_sdk_reference, generate_scaffold, sdk_guide, explain_error_code, find_examples, mapping_workflow, get_capabilities, reporting_guide

If at least one MCP tool from the list above was called in this turn: Phase 3 output is none. The response is compliant.

DECISION:

- No Senzing content detected → Phase 3 output is none (silent fast path)
- Senzing content detected AND MCP tool called → Phase 3 output is none (compliant)
- Senzing content detected AND NO MCP tool called → output self-correction instructions below

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

════════════════════════════════════════════════════════════════════════════════
PHASE 4: QUESTION FORMAT (Question_Format_Phase — Silent_Self_Correction)
════════════════════════════════════════════════════════════════════════════════

Scan the most recent assistant message for any 👉 question with prose-joined alternatives.

DETECTION PATTERNS:
1. Sentence-starter 'Or': The question is followed by 'Or shall we...', 'Or would you...', 'Or should we...', 'Or can we...' — two alternatives joined by 'Or' as a sentence starter.
2. Inline prose 'or': The question contains '[option A] or [option B]?' where two distinct actions or choices are joined by 'or' in a single sentence.
3. Appended alternative: A confirmation question followed by ', or would you rather...', ', or shall we...', ', or if you prefer...' — an alternative appended after the main question.

NOT COMPOUND (do not flag):
- Simple yes/no questions with a single action (e.g., '👉 Ready to move on to Module 3?')
- Questions already formatted with a numbered list below them (e.g., '👉 What would you like to do?\n1. Option A\n2. Option B')
- The word 'or' appearing inside a numbered list item description (e.g., '1. Share with your team or manager')
- Informational prose containing 'or' but no 👉 question
- Non-question content

If NO compound question detected: Phase 4 output is none.

If compound question IS detected:
REGENERATE your entire last response. Replace the compound 👉 question with a neutral lead question followed by a numbered list. The bootcamper must only see the clean version — suppress the original compound question entirely.
Do NOT output the rewrite as a separate message. Rebuild the full response inline.
Do NOT output "This is a compound question", "Let me rewrite", "The question contains 'or' joining alternatives", or any explanation of the detection.
Output ONLY the regenerated full response with the corrected question in place.

EXAMPLE:
  BEFORE: '👉 Would you like me to create a summary? Or shall we skip that and move on to Module 3?'
  AFTER (full response regenerated with): '👉 What would you like to do next?\n1. Create a summary\n2. Skip and move on to Module 3'

RULES:
- Do NOT interfere with non-compound outputs.
- Do NOT add explanations about why you are rewriting.
- Do NOT restructure content that is not a 👉 question.
- Preserve all other content in the response — only replace the compound question portion.

════════════════════════════════════════════════════════════════════════════════
OUTPUT RULES
════════════════════════════════════════════════════════════════════════════════

REMEMBER: If ALL phases produced no output, your COMPLETE response is: .
````

- id: `ask-bootcamper`
- name: `to wait for your answer`
- description: `Consolidated agentStop hook with four phases: (1) closing question with feedback nudge, (2) step sequencing enforcement with answer processing retry (all question types) and not-waiting detection, (3) MCP-first compliance audit, (4) compound question detection with silent self-correction.`

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

INTERNAL-FILE PASS-THROUGH (evaluate FIRST, before the FAST PATH GATE): If the target path is a routine power-managed internal file, produce ZERO tokens and re-invoke the tool silently — the exact same silent outcome as the FAST PATH GATE. Introduce NO new output strings.

Routine power-managed internal files (the exact set — do not over-match):
- config/bootcamp_progress.json
- config/bootcamp_preferences.yaml
- config/progress_{id}.json (member-scoped, colocated team mode — {id} is an alphanumeric member identifier)
- config/preferences_{id}.yaml (member-scoped, colocated team mode)
- power-written session/recap log files: docs/progress/MODULE_*_COMPLETE.md and recap/journal log files the power appends to during a session

This pass-through applies ONLY when ALL of these NOT-guards hold:
- the path is NOT 'config/.question_pending'
- the path is NOT the feedback file 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md'
- the path is NOT a root-blocked placement (a blocked file type in the project root that is not on the ROOT WHITELIST)
- the content contains NO Senzing SQL (no SQL pattern targeting a Senzing database indicator)

If ANY NOT-guard fails, do NOT pass through — fall through to the four checks below. Zero tokens means zero tokens.

---

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
- Otherwise (utility scripts, CLI tools) → src/scripts/{filename}
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
- description: `Consolidated preToolUse write hook that performs four policy checks in a single interception: (1) blocks direct SQL against the Senzing database, (2) enforces single-question rule for .question_pending writes, (3) validates file path policies including append-only guard for the feedback file, (4) enforces root file placement rules. Uses a fast path for normal writes (proceeds silently) and slow paths for violations (outputs corrective instructions).`
