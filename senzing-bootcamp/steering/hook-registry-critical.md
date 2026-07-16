---
inclusion: manual
---

# Hook Registry — Critical Hooks (Full Prompts)

Critical hook definitions with prompt text for use with the `createHook` tool during onboarding. These hooks are created in Step 1.

For module-specific hooks, see `hook-registry.md`, which routes to the per-module slice for your current module.
For a quick reference of all hooks, see `hook-registry.md`.

## Critical Hooks (created during onboarding)

**ask-bootcamper** (Stop → agent)

Prompt:

````text
DEFAULT OUTPUT: .
If ALL phases below produce no output, your COMPLETE response is a single period character: .
Do NOT explain your reasoning. Do NOT describe condition checks. Do NOT narrate which phases were evaluated. Do NOT output phrases like "My last message ends with..." or "No module was completed" or "Phase N silenced" or any variation. NEVER explain WHY you are outputting a period. Just output: .

NEGATIVE EXAMPLES (NEVER produce output like these):
✗ "My last message ends with a 👉 question, and no module was completed."
✗ "Phase 1 was silenced because a question is already pending."
✗ "No phases produced output, so responding with a period."
✗ "All conditions checked — no action needed."
The ONLY acceptable no-output response is the literal single character: .

CRITICAL: NEVER generate text beginning with 'Human:' or any text that represents what the bootcamper might say. If you detect yourself about to fabricate a user response, output only: .

Q&A CAPTURE (silent side effect — this does NOT count as visible output and does NOT change the DEFAULT OUTPUT period rule): Durable Q&A capture is now GUARANTEED deterministically by the command-backed hook `capture-qa-events.json`, which runs `log_qa_event.py record-question` at this same Stop cadence whether or not you act. The step below is therefore only a redundant, best-effort backstop — it is NOT the primary durability path and you are NOT relied upon to make the write durable. As a best-effort backstop, before evaluating the phases below, if the file config/.question_pending exists, you MAY run the command `python3 senzing-bootcamp/scripts/log_qa_event.py record-question` to redundantly record the outstanding 👉 question for the graduation recap and Q&A transcript. It is idempotent (a re-presented question is never double-logged, and it is safe to run even though the command hook also records it) and non-blocking, and it prints nothing to the bootcamper. Running it never changes your visible output — if all phases below produce no output, your response is still a single period. This hook has six phases: Phase 0, Phase 1, Phase 1.5, Phase 2, Phase 3, and Phase 4. Phase 0 (Module Recap Append) runs first: it captures a structured recap to docs/bootcamp_recap.md when a module was just completed, and defers to a pending 👉 question. Phase 1.5 (Leading-Question Count Audit) runs right after Phase 1: it is an advisory, non-blocking spot check of the exactly-one-👉 invariant, and it produces no output for non-yielding turns, silent internal-file pass-throughs, the DEFAULT-OUTPUT single period, or when a higher-precedence phase is already emitting a self-correction. Phase 2 contains three sub-phases (2A: Sequential Step Enforcement, 2B: Answer Processing Retry, 2C: Not-Waiting Detection). Evaluate each phase in order. If Phase 2 or Phase 3 detects a violation, that takes priority over Phase 1's closing question. Phase 4 operates on the output that would be shown to the bootcamper, so it runs last.

════════════════════════════════════════════════════════════════════════════════
PHASE 0: MODULE RECAP APPEND (Module_Recap_Phase)
════════════════════════════════════════════════════════════════════════════════

If `config/.question_pending` exists, Phase 0 produces no output at all — skip the recap append entirely and continue to Phase 1 (a pending 👉 question takes absolute precedence over recap capture).

This phase runs internally as part of this single Stop hook — it does NOT surface as a separate hook in the UI. In this phase you are checking whether the bootcamper just completed a module and, if so, appending a structured recap section to docs/bootcamp_recap.md. Follow these steps exactly:

1. BOUNDARY DETECTION: Read `config/bootcamp_progress.json` and examine the `modules_completed` array. If `modules_completed` has not changed (no new module number was added since the previous state), produce no output at all — do nothing, do not acknowledge, do not explain. Let the conversation continue normally. This boundary detection fires for EVERY new entry added to `modules_completed`, INCLUDING the final module of a track. Track completion (graduation or celebration) MUST NOT suppress the per-module recap section: if the newly completed module is the last module of the bootcamper's track, still append its recap section exactly as for any other module.

2. IDENTIFY COMPLETED MODULE: If a new module number appears in `modules_completed`, identify that module number. Read `config/module-dependencies.yaml` to find the module name corresponding to that number.

3. GATHER SESSION CONTENT: Review the current session context to collect:
   - Information Shared: key concepts, explanations, and reference material presented to the bootcamper during this module
   - Questions & Responses: an ORDERED LIST OF PAIRS, one pair per substantive question the agent posed to the bootcamper (exclude rhetorical or transitional prompts), each pair holding the question and the bootcamper's response to that question. Preserve the ascending sequence in which the questions were asked during the module. A substantive question is one whose text contains at least one non-whitespace character after leading and trailing whitespace is removed. Keep each question adjacent to its own response — do NOT collect questions and responses as two separate parallel lists.
   - Actions Taken: all file creations, modifications, code generation, configuration changes, and commands executed during the module
   - Journal Narrative: a concise narrative summary for the `### Journal` subsection made up of four fields — `**What we did:**` (what was accomplished this module), `**What was produced:**` (the artifact paths created or updated), `**Why it matters:**` (why this module's work matters to the bootcamper's goal), and `**Bootcamper's takeaway:**` (the bootcamper's own stated takeaway, or `N/A` when none was given)

4. COMPUTE DURATION (no placeholders): Obtain the per-module Duration and the cumulative Total Duration from the deterministic planner instead of from session context. Run:

   ```
   python senzing-bootcamp/scripts/completion_artifacts.py --progress config/bootcamp_progress.json --recap docs/bootcamp_recap.md --progress-dir docs/progress --plan
   ```

   Parse the emitted JSON. Use `module_durations["N"]` (where N is the completed module number) as that module's Duration, and `total_duration` as the cumulative Total Duration. These values are computed from the ISO 8601 timestamps stored in `step_history` and the top-level `started_at` in `config/bootcamp_progress.json`. If the planner does not return a value for this module (the key is absent or null), OMIT the `### Duration` field for this module entirely — do NOT write a placeholder such as "Module N session". If `total_duration` is null, OMIT the **Total Duration** value in the header rather than writing a placeholder. If the planner cannot be run (file-system error or timeout), log a warning and continue, omitting the Duration fields rather than fabricating a value.

5. GET BOOTCAMPER NAME: Read `config/bootcamp_preferences.yaml` and extract the bootcamper's name. If the file does not exist or the name field is missing, use "Bootcamper" as the default.

6. CREATE OR VERIFY FILE: Check if `docs/bootcamp_recap.md` exists.
   - If it does NOT exist, create it with this header (include the **Total Duration** line only when the planner returned a non-null `total_duration`; otherwise omit that line entirely):
     ```
     # Senzing Bootcamp Recap

     **Bootcamper:** [Name]
     **Started:** [ISO 8601 timestamp with timezone of current time]
     **Total Duration:** [total_duration from planner]

     ---
     ```
   - If it already exists, do NOT overwrite or modify any existing content.

7. APPEND RECAP SECTION: Append the following structured section to the end of `docs/bootcamp_recap.md`. Include the `### Duration` heading and value ONLY when the planner returned a value for this module; when no reliable duration was computed, omit the `### Duration` heading and its value entirely:
   ```

   ## Module N: [Module Name] — [ISO 8601 timestamp with timezone]

   ### Information Shared
   - [Concept or explanation presented]
   - [Reference material shared]

   ### Questions & Responses
   - **Q:** [Agent question to bootcamper]
       - **R:** [Bootcamper response to that question]
   - **Q:** [Next agent question to bootcamper]
       - **R:** [Bootcamper response to that question]

   ### Actions Taken
   - Created `[file path]`
   - Modified `[file path]`
   - Ran `[command]`

   ### Duration
   [module_durations["N"] from planner]

   ### Journal
   **What we did:** [summary of what was accomplished this module]
   **What was produced:** [artifact paths created or updated]
   **Why it matters:** [why this module's work matters]
   **Bootcamper's takeaway:** [bootcamper's stated takeaway, or N/A]

   ---
   ```

   QUESTIONS & RESPONSES FORMAT (follow exactly — this must match what `format_qr_section` produces):
   - Emit exactly ONE `### Questions & Responses` heading per module. NEVER emit a `### Questions Asked` heading or an `### Answers Given` heading.
   - For each pair, in ascending ask order, write the question on its own line beginning with the literal prefix `- **Q:**` (zero leading spaces), immediately followed on the next line by its response beginning with exactly four leading space characters (ASCII 0x20, no tabs) and the literal prefix `- **R:**`. The response line is nested four spaces beneath its question so the Response_Item Indent_Depth is exactly 4 and the Question_Item Indent_Depth is exactly 0.
   - Keep each response immediately after its own question — never group all questions then all responses.
   - If a question's response is absent or contains only whitespace, write the response line as `    - **R:** (no response recorded)`.
   - If a response spans more than one line, prefix every continuation line with at least four leading spaces so it stays nested beneath the question.
   - If the module has zero substantive questions, write the `### Questions & Responses` heading followed by exactly one list item consisting of the literal text `- None` and no question/response pairs.

   JOURNAL SUBSECTION FORMAT (follow exactly): After the `### Actions Taken` subsection — and after the `### Duration` subsection when one was written — emit exactly ONE `### Journal` heading, followed on separate lines by these four narrative fields in this exact order, each starting at zero indentation with its bold label followed by a single space and the field value:
   - `**What we did:**` — a concise summary of what was accomplished during this module.
   - `**What was produced:**` — the artifact paths created or updated during this module.
   - `**Why it matters:**` — why this module's work matters to the bootcamper's goal.
   - `**Bootcamper's takeaway:**` — the bootcamper's own stated takeaway. When the module produced no takeaway value, write `N/A` for this field.
   Every consolidated section MUST include the `### Journal` subsection with all four fields; when a field has no meaningful content, write `N/A` for that field rather than omitting it. The narrative journal content lives here in the Consolidated_Log — do NOT write a separate journal file.

8. UPDATE TOTAL DURATION: If the file header contains a **Total Duration** line and the planner returned a non-null `total_duration`, update it to that value. The total duration is rolled up from the real per-module elapsed times and must be monotonically non-decreasing. If the planner returned null for `total_duration`, leave the header without a Total Duration value rather than writing a placeholder.

9. VERIFY AND BACKFILL (synchronous, before reporting success): The append is not complete until you confirm it persisted. Re-read `docs/bootcamp_recap.md` and check for a `## Module N:` heading for the module you just completed. If the heading is present, proceed. If it is ABSENT (the write did not persist, this is the final module of a track, or the section was never written), do NOT report success: run the deterministic backfill applier, which appends a `## Module N:` section for every completed module missing one (append-around, preserving existing bytes; idempotent when nothing is missing):

   ```
   python senzing-bootcamp/scripts/completion_artifacts.py --progress config/bootcamp_progress.json --recap docs/bootcamp_recap.md --progress-dir docs/progress --backfill
   ```

   The applier exits non-zero and names any modules still missing if verification fails after the write. Re-read the file and confirm the `## Module N:` heading is now present before continuing. If the applier cannot be run (file-system error or timeout), log a warning and continue without blocking module completion — the track-completion reconciliation pass is the final safety net.

10. CONFIRMATION: Display a single brief line confirming the recap was updated, for example: "Recap updated for Module N: [Module Name]."

CONSTRAINTS:
- All timestamps MUST use ISO 8601 format with timezone offset (e.g., 2026-05-23T10:30:00-05:00).
- Preserve all existing file content byte-for-byte when appending.
- Duration and Total Duration values come ONLY from `completion_artifacts.py`; never derive them from session context and never write a placeholder such as "Module N session". When the planner omits a value, omit the corresponding field.
- If any section has no content (e.g., no actions were taken), include the subsection heading with a single item "None" or "N/A". This does NOT apply to the `### Duration` field, which is omitted entirely when the planner returns no value, and it does NOT apply to the `### Questions & Responses` section, which follows its own rule above (heading followed by exactly `- None` when there are zero substantive questions).
- If the file cannot be written due to a file system error, log a warning message and continue without blocking the module completion flow. Do NOT raise an error or halt execution.
- Do NOT alter the behavior of any other hooks (celebration, etc.).
- Keep the recap factual and concise — summarize rather than reproduce entire conversations.
- Do NOT include secrets, credentials, environment variable values, or connection strings in the recap content.
- Module sections must appear in chronological order of completion timestamps.

After Phase 0 completes, is skipped (a question is pending), or is a no-op (no new module was completed), continue to Phase 1. Phase 0's recap-append actions do not by themselves count as the hook's user-visible output.

════════════════════════════════════════════════════════════════════════════════
PHASE 1: CLOSING QUESTION (Closing_Question_Phase)
════════════════════════════════════════════════════════════════════════════════

Before producing ANY Phase 1 output, verify ALL of these conditions:
1. The file config/.question_pending does NOT exist
2. The most recent assistant message does NOT contain a 👉 character anywhere — if it already contains a 👉, do not add a second one
3. The most recent assistant message does NOT end with a question directed at the bootcamper

INLINE TRANSITION PROMPT RECOGNITION (module-completion transition turns): When the most recent assistant message is a module-completion transition turn, treat a forward module-transition prompt ("Ready to (start | move on to) Module N") as an already-present transition question EVEN WHEN it is phrased inline as prose without a leading 👉 (for example, as the "Proceed" next-step option). An inline transition prompt counts the same as a 👉 transition question for condition 2 above: do NOT add a second closing 👉 transition question when the transition question is already present inline. Recognize the already-present transition and leave exactly one closing 👉 transition question rather than a second copy.

If ANY Phase 1 condition fails: Phase 1 output is none. Skip to Phase 2.

FIRST — Check for no-op: If ALL Phase 1 conditions pass AND the most recent assistant message contains no substantive content (e.g., only a trivial acknowledgment like "Got it" or "Understood" with no file changes, no recap, and no action taken): Phase 1 output is none. Skip to Phase 2.

NOTE: If files were edited (even by a hook-triggered action), that IS substantive work. Provide a closing question unless a 👉 question is already present.

SECOND — Recap and closing question: GATE-AWARENESS CHECK (evaluate this FIRST, before composing any closing question): Determine whether a mandatory gate is currently active. A mandatory gate is active when the most recent assistant message contains "⛔ **MANDATORY GATE**" AND that same assistant message contains "🛑 **STOP" — this indicates the gate was just presented and is awaiting the bootcamper's input. When a mandatory gate is detected as active, your closing question MUST NOT name, preview, or reference specific content from any step beyond the current gate. Use generic forward-looking language only, such as 'we'll continue when you're ready' or 'we'll move on to the next setup step.' Do NOT mention programming language selection, track selection, or any other specific upcoming topic. This gate-awareness constraint applies ONLY when a mandatory gate is active; when no mandatory gate is detected, Phase 1 proceeds exactly as before with full session awareness and may reference upcoming content naturally.

LEDGER CONSULT (Ask-Once Guarantee — evaluate before composing the closing question): When the closing 👉 question you are about to emit is tied to a specific step's Question_Key, consult the Question_Ledger first so you never re-ask a question the bootcamper already answered. Run `python3 senzing-bootcamp/scripts/question_ledger.py is-answered --key <KEY>` for that step's Question_Key (add `--member <ID>` in team mode); exit code 0 means the question is already answered. If it is already answered, do NOT re-ask it — advance using the stored answer and select the next genuinely unanswered question instead. This enforces the Ask-Once Guarantee (see `conversation-protocol.md` → The Ask-Once Guarantee; the Question_Key scheme and ledger operations are documented in `agent-instructions.md` → State & Progress → Question_Ledger). This consult only narrows WHICH question to ask — it is NEVER a reason to emit no output when a genuinely new (unanswered) question is due. When the closing question is not tied to a specific step's Question_Key, or that Question_Key is not yet answered, proceed with the closing question as normal. If the ledger read fails, degrade safely: fall back to normal question selection and never block the bootcamper.

If ALL Phase 1 conditions pass AND work was accomplished: You may provide a brief recap of what was accomplished and which files created or modified, then end with a contextual 👉 question (a closing question for the bootcamper). Keep it to 2-3 sentences maximum.

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
PHASE 1.5: LEADING-QUESTION COUNT AUDIT (Leading_Question_Count_Audit_Phase)
════════════════════════════════════════════════════════════════════════════════

This phase is an advisory, non-blocking spot check that runs AFTER Phase 1 has had its chance to add a closing 👉 question. It verifies the One-Question Invariant: a genuine Yielding_Turn ends with EXACTLY ONE 👉 leading question — never zero, never two-plus. It is a Soft_Block at most; it NEVER becomes a ⛔ mandatory gate and NEVER permanently blocks progress. If it cannot be evaluated for any reason, it degrades to a silent no-op (produce no output).

FIRST — SKIP CONDITIONS (if ANY is true, this phase produces no output at all):
1. The most recent turn is NOT a genuine Yielding_Turn — it is a silent internal-file pass-through (per agent-behavior-rules.md Rule 5), a non-yielding continuation, or the DEFAULT-OUTPUT single-period response.
2. Phase 2 (Step Sequencing) or Phase 3 (MCP-First) is emitting a violation or self-correction this turn, or a mandatory gate is active — the visible output is a self-correction or gate rather than a bootcamper-facing closing question.
3. config/.question_pending indicates the turn is a wait or pass-through while a question already stands and no fresh bootcamper-facing content was produced.
4. CADENCE (optional sampling): the audit runs ONLY at this Stop boundary and the default cadence is every Yielding_Turn. If config/bootcamp_preferences.yaml sets `sampling_rate` to a value greater than 0.0 and less than 1.0, this Stop event MAY be sampled out (skipped) to stay lightweight; when `sampling_rate` is absent, null, or 1.0 (the default), NEVER skip on cadence grounds. Sampling only affects how often the audit runs — it never changes the self-correction behavior when the audit does run, and it never couples the audit to a file-write or PostToolUse event.

SECOND — COUNT the 👉 leading questions in the rendered turn using the precise, deterministic counting rule (authoritative source: senzing-bootcamp/scripts/count_leading_questions.py). A 👉 leading-question line is a line whose FIRST non-whitespace, non-blockquote, non-bold content begins with 👉. EXCLUDE: 👉 inside fenced code blocks (``` or ~~~) or inline code spans (backticks); 👉 on blockquoted (>) lines that quote a prior-turn example; and the internal control markers 🛑 (STOP) and ⛔ (mandatory gate), which are never 👉. Strip a single leading bold marker (**) so a bolded 👉 line still counts.

CROSS-CHECK: a well-formed Yielding_Turn records exactly one pending question in config/.question_pending. If the rendered 👉 count disagrees with that pending state (zero 👉 while a question is pending, or two-plus 👉 for a single pending question), treat it as the matching violation below.

THIRD — CLASSIFY and act on the 👉 count:
- EXACTLY ONE 👉: the invariant holds. Produce NO output (silent pass).
- ZERO 👉 on a Yielding_Turn that performed substantive work: missing-leading-question self-correction. Silently re-render the turn so it ends with exactly one 👉 question the bootcamper can answer; do not show the original dead-end version.
- TWO OR MORE 👉: multiple-leading-questions self-correction. The turn must end with EXACTLY ONE 👉. Silently re-render it down to a single lead 👉 question; when the extras are alternatives, fold them into one lead 👉 question followed by a numbered list of the options (reuse the compound-question rewrite / numbered-list pattern from Phase 1 and Phase 4). Preserve all non-question content; only collapse the stacked questions into one.
- DUPLICATE TRANSITION PROMPT (an inline prose copy paired with a single 👉 line): on a module-completion transition turn, when the forward module-transition prompt ("Ready to (start | move on to) Module N") appears BOTH inline as prose AND again as a single 👉 line, that is a duplicate transition — the 👉 count can read as one while the bootcamper still sees the transition question twice. Silently collapse it to exactly one 👉 transition question: keep the single closing 👉 transition question and drop the inline prose copy so no second copy of the transition remains. Reuse this same silent self-correction pattern and do not narrate the de-duplication.

OUTPUT CONSTRAINTS (the Self_Audit must never worsen the turn):
- The re-rendered turn MUST contain AT MOST ONE 👉 and MUST NOT be a compound question; present any alternatives as a numbered list rather than joining them with prose.
- Do NOT explain the audit, name this phase, or narrate the count (no 'this turn has N leading questions', no 'Phase 1.5 detected a violation'). Output ONLY the corrected turn.
- If evaluation is uncertain or an error occurs, produce no output (silent no-op) — never block the turn.

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
- trigger: `Stop`
- action: `agent`

**code-style-check** (PostFileSave → agent, matcher: `^(?:src/(?:.*/)?[^/]*\.py|src/(?:.*/)?[^/]*\.java|src/(?:.*/)?[^/]*\.cs|src/(?:.*/)?[^/]*\.rs|src/(?:.*/)?[^/]*\.ts|src/(?:.*/)?[^/]*\.js)$`)

Prompt:

````text
A source code file was just edited. Check it for language-appropriate coding standards (Python: PEP-8 with max line length 100; Java: standard conventions; C#: .NET conventions; Rust: rustfmt/clippy; TypeScript: ESLint conventions). If violations are found, suggest specific fixes. If compliant, acknowledge briefly and continue.
````

- id: `code-style-check`
- name: `to check code style`
- trigger: `PostFileSave`
- matcher: `^(?:src/(?:.*/)?[^/]*\.py|src/(?:.*/)?[^/]*\.java|src/(?:.*/)?[^/]*\.cs|src/(?:.*/)?[^/]*\.rs|src/(?:.*/)?[^/]*\.ts|src/(?:.*/)?[^/]*\.js)$`
- action: `agent`

**review-bootcamper-input** (UserPromptSubmit → agent)

Prompt:

````text
ANSWER CAPTURE (silent side effect — produces no output): Durable answer capture is now GUARANTEED deterministically by the command-backed hook `capture-qa-events.json`, which runs `log_qa_event.py record-answer` at this same UserPromptSubmit cadence whether or not you act. The step below is therefore only a redundant, best-effort backstop — it is NOT the primary durability path. As a best-effort backstop, if the file config/.question_pending exists, the bootcamper's message is the answer to that pending 👉 question — you MAY redundantly record it for the graduation recap and Q&A transcript by running `python3 senzing-bootcamp/scripts/log_qa_event.py record-answer` and passing the bootcamper's verbatim message on stdin (for example via a heredoc). It pairs the answer to the pending question's id, self-heals by logging the question first if it was not already recorded, and is non-blocking (and idempotent alongside the command hook, so the redundant write is safe). This runs regardless of the trigger-phrase checks and produces no visible output. Then continue with the checks below. Check if the bootcamper's message contains any of these feedback trigger phrases (case-insensitive): "bootcamp feedback", "power feedback", "submit feedback", "provide feedback", "I have feedback", "report an issue". Also check for status trigger phrases (case-insensitive): "where am I", "status", "what step am I on", "show progress", "how far along am I". Also check for Repeat_Request trigger phrases (case-insensitive) — the bootcamper asking to see the current question again: "repeat that", "repeat the question", "say that again", "what was the question", "ask me again", "come again". If NONE of these phrases appear in the message, produce no output at all — do not acknowledge, do not explain, do not print anything. If a REPEAT trigger phrase IS found, handle it as a Repeat_Request under the Ask-Once Guarantee (see conversation-protocol.md → The Ask-Once Guarantee): re-present the current Pending_Question verbatim and do nothing else. Read config/.question_pending — this marker holds the single currently-outstanding question (question type on line 1, full question text on lines 2+). If the file exists, re-present the question text from lines 2+ exactly as written, preserving the same 👉 text word-for-word; do NOT create a new Question_Ledger entry, do NOT run question_ledger.py record-asked, and do NOT change the question's answered status — a Repeat_Request re-presents an existing question, it is not a new question. If config/.question_pending does NOT exist, there is no Pending_Question: state plainly that there is no outstanding question right now rather than inventing or fabricating one. In either case, take no other action and do not advance the workflow. If a STATUS trigger phrase IS found, output exactly: STATUS_TRIGGER_DETECTED — the agent should respond with the inline status format from inline-status.md. If a FEEDBACK trigger phrase IS found, immediately do the following: (1) Read config/bootcamp_progress.json to get the current module number and completed modules. If the file doesn't exist, record module as "Unknown". (2) Note what the bootcamper was doing in the recent conversation. (3) Note which files are open in the editor. (4) Load steering file feedback-workflow.md and follow its complete workflow, pre-filling the context fields with what you just captured. Do NOT ask the bootcamper to re-explain their context — you already have it.
````

- id: `review-bootcamper-input`
- name: `to review what you said`
- trigger: `UserPromptSubmit`
- action: `agent`

**write-policy-gate** (PreToolUse → agent, matcher: `fs_write|str_replace|fs_append`)

Prompt:

````text
⚠️ SILENCE RULE: When all checks pass, produce ZERO tokens. No output. No acknowledgment. Re-invoke the tool silently.

WRITE POLICY GATE — Five checks in one pass.

INTERNAL-FILE PASS-THROUGH (evaluate FIRST, before the FAST PATH GATE): If the target path is a routine power-managed internal file, produce ZERO tokens and re-invoke the tool silently — the exact same silent outcome as the FAST PATH GATE. Introduce NO new output strings.

Routine power-managed internal files (the exact set — do not over-match):
- config/bootcamp_progress.json
- config/bootcamp_preferences.yaml
- config/data_sources.yaml
- config/visualization_tracker.json
- config/progress_{id}.json (member-scoped, colocated team mode — {id} is an alphanumeric member identifier)
- config/preferences_{id}.yaml (member-scoped, colocated team mode)
- power-written session/recap log files: docs/progress/MODULE_*_COMPLETE.md and recap/journal log files the power appends to during a session

This pass-through applies ONLY when ALL of these NOT-guards hold:
- the path is NOT 'config/.question_pending'
- the path is NOT the feedback file 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md'
- the path is NOT a root-blocked placement (a blocked file type in the project root that is not on the ROOT WHITELIST)
- the content contains NO Senzing SQL (no SQL pattern targeting a Senzing database indicator)
- the write does NOT complete a question-owning onboarding step (see CHECK 5): it does not set or finalize a question-owning field ('verbosity', a comprehension-check completion marker, 'track', or 'mapping_verbosity') in config/bootcamp_progress.json, config/bootcamp_preferences.yaml, or the member-scoped config/progress_{id}.json / config/preferences_{id}.yaml

If ANY NOT-guard fails, do NOT pass through — fall through to the checks below. Zero tokens means zero tokens.

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

If the target path DOES end with '.question_pending', FIRST strip bold markers, THEN validate. STRIP BOLD MARKERS (do this before evaluating any rule below): remove ALL '**' bold-emphasis markers from the question content, and perform every count and detection in the rules below — the question-mark count in rule 1 and the joining-conjunction detection in rule 2 — on that marker-stripped wording only. The '**' markers are presentational; they contain no question mark and no conjunction words and act as word boundaries, so they MUST NOT change the verdict. Then validate the marker-stripped question content against ALL of these rules:

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

CHECK 5: ANSWER-REQUIRED - NO SILENT COMPLETION OF A QUESTION-OWNING STEP

This check applies ONLY to writes that complete a question-owning onboarding step by setting or finalizing a question-owning field in one of these progress/preferences files:
- config/bootcamp_progress.json
- config/bootcamp_preferences.yaml
- config/progress_{id}.json (member-scoped, colocated team mode)
- config/preferences_{id}.yaml (member-scoped, colocated team mode)

QUESTION-OWNING FIELDS - each is owned by a 👉 question the bootcamper must answer:
- 'verbosity' (Detail_Level_Step)
- a comprehension-check completion marker (Any_Questions_Step - e.g. a field or flag recording the comprehension check as done/acknowledged)
- 'track' (track selection)
- 'mapping_verbosity'

If the target path is NOT one of the four progress/preferences files above, OR the write does NOT set/finalize any question-owning field (it is a routine bookkeeping update - step counters, timestamps, module progress, completed-module lists, etc.): this check does not apply. Do not acknowledge. Do not explain. Do not print anything. Proceed silently.

If the write DOES set or finalize a question-owning field, confirm a Real_Answer for that step exists in the CURRENT turn:
- A Real_Answer is a response the bootcamper actually gave this turn - including an explicit 'use the default / skip / no preference' (an Explicit_Default_Choice). A Question_Ledger 'mark-answered' signal for that step, if present, also counts as a recorded Real_Answer.
- The value being written must be the one the bootcamper selected, NOT a value the agent chose or silently defaulted on the bootcamper's behalf.

If a recorded Real_Answer (or Explicit_Default_Choice) for that step IS present in the turn: Do not acknowledge. Do not explain. Do not print anything. Proceed silently.

If there is NO recorded Real_Answer for that step (the agent would be completing the step with a value it chose or silently defaulted):

STOP. Do not proceed with the write. Output:
⚠️ ANSWER REQUIRED - QUESTION-OWNING STEP NOT ANSWERED
Violation: This write completes a question-owning step (name it: verbosity / comprehension check / track / mapping_verbosity), but the bootcamper has not provided a Real_Answer for it this turn - the value would be an agent-chosen or silent default.
Fix: Do not write an agent-supplied value. Present the step's 👉 question (offer the Explicit_Default_Choice, e.g. 'standard (recommended)' for verbosity), wait for the bootcamper's Real_Answer, and persist ONLY the value the bootcamper actually selects. An explicit 'use the default' from the bootcamper is itself a valid Real_Answer - record it and proceed.

Do NOT allow the write to proceed until the bootcamper has supplied a Real_Answer (or explicitly chosen the default) for the step.

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
- trigger: `PreToolUse`
- matcher: `fs_write|str_replace|fs_append`
- action: `agent`
