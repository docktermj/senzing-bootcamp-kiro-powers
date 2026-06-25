# Always-Create Completion Summary Bugfix Design

## Overview

Governing rule 16 requires that, after all modules, in the graduation, the bootcamp
**ALWAYS** creates the completion-summary — the module-by-module collection of questions
posed, bootcamper responses, actions taken, and artifacts generated. The dedicated
completion-summary artifact is `docs/completion_summary.md` (with an optional shareable
`docs/completion_summary.pdf`), produced by `senzing-bootcamp/scripts/generate_completion_summary.py`
from `config/session_log.jsonl`.

Today that artifact is **gated behind a binary yes/no opt-in**. `senzing-bootcamp/steering/completion-summary-offer.md`
instructs the agent: *"If the bootcamper declines ('no'): proceed to the next post-completion
step without generating any summary file."* So when the bootcamper declines, no
completion-summary artifact is created, breaching rule 16. This is the only graduation
artifact whose creation is opt-in — graduation always generates `production/GRADUATION_REPORT.md`
and always attempts `docs/bootcamp_recap.pdf`.

The fix is realized **entirely in the steering contracts** (and is anchored into the
graduation flow), not in the script. The contract is reshaped so that during any stopping
point / graduation:

1. `docs/completion_summary.md` is generated **unconditionally** by running
   `generate_completion_summary.py` (markdown), exactly like `GRADUATION_REPORT.md` is
   always generated and the recap PDF is always attempted.
2. The binary yes/no answer is **re-scoped** to govern only the *secondary presentation
   concerns*: whether the shareable PDF (`--pdf` → `docs/completion_summary.pdf`) is
   rendered and whether the summary is surfaced/shared with the bootcamper.
3. Generation is **non-blocking**: any failure (missing/empty session log, file-system
   error, non-zero script exit) logs a warning and continues, mirroring the existing
   recap-PDF and graduation-report patterns.

`generate_completion_summary.py` already supports unconditional markdown generation
(`main()` always calls `write_narrative()`; the PDF branch is the only `--pdf`-gated work),
so **no change to the script's internals is required** for the happy path. The single
residual is the missing/unreadable session-log path, which is handled non-blockingly by
the steering wrapper rather than by changing the script.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — a stopping point is detected
  and the bootcamper's offer answer is not `"yes"`, so the mandated completion-summary
  document is skipped entirely. `C(X) = X.stoppingPointDetected AND X.offerAnswer != "yes"`.
- **Property (P)**: The desired behavior — `docs/completion_summary.md` is always created at
  graduation/stopping points regardless of the yes/no answer; the answer governs only PDF
  rendering and surfacing/sharing.
- **Preservation**: All behavior outside the always-create change must remain unchanged —
  stopping-point detection, offer ordering/repeat policy, the per-module recap
  (`docs/bootcamp_recap.md`), graduation Step 0 recap PDF, `GRADUATION_REPORT.md`, the
  journal/certificate steps, and every existing behavior of `generate_completion_summary.py`.
- **F** (original): The unfixed workflow, where the completion-summary document is created
  only on an accepted (`"yes"`) offer.
- **F'** (fixed): The fixed workflow, where the completion-summary document is always created
  and the yes/no answer governs only PDF rendering / sharing.
- **the completion-summary artifact**: `docs/completion_summary.md` produced by
  `generate_completion_summary.py`. Distinct from `docs/bootcamp_recap.md` /
  `docs/bootcamp_recap.pdf` (the per-module recap, which is not the bug site).
- **completion-summary-offer.md**: `senzing-bootcamp/steering/completion-summary-offer.md` —
  the steering contract that detects stopping points and presents the offer. **Primary bug
  site.**
- **graduation.md**: `senzing-bootcamp/steering/graduation.md` — the graduation workflow that
  always generates `GRADUATION_REPORT.md` (see `## Graduation Report`) and always attempts
  the recap PDF (see `## Step 0: Recap PDF Generation`). The always-create pattern is modeled
  on these.
- **module-completion.md**: `senzing-bootcamp/steering/module-completion.md` — defines the
  Path Completion Celebration ordering of post-completion offers and the per-module recap append.
- **offerAnswer**: The bootcamper's response to the offer (`"yes"`, `"no"`, or any
  non-acceptance). After the fix this governs only the PDF/surface secondary concern.

## Bug Details

### Bug Condition

The bug manifests at any stopping point (Module 7 completion, Module 11 completion, explicit
stop request, track switch at boundary) where the bootcamper does **not** accept the offer.
`completion-summary-offer.md` (section `## Prompt Format`) currently gates artifact creation
on the answer: it generates the summary only on `"yes"` and, on `"no"`, *"proceed to the next
post-completion step without generating any summary file."* The mandated completion-summary
artifact is therefore skipped whenever the bootcamper declines.

**Formal Specification:**

```
FUNCTION isBugCondition(X)
  INPUT: X of type GraduationSituation
         (fields: stoppingPointDetected: bool,
                  offerAnswer: "yes" | "no" | <other>,
                  sessionLogAvailable: bool,
                  stoppingPointType: string)
  OUTPUT: boolean

  // The bug manifests at any stopping point where the bootcamper does NOT
  // accept the offer, because the mandated completion-summary artifact is
  // then skipped entirely (no docs/completion_summary.md is created).
  RETURN X.stoppingPointDetected
         AND X.offerAnswer <> "yes"
END FUNCTION
```

### Examples

- **Track completion at Module 7, bootcamper declines** — `isBugCondition = true`. Under **F**,
  the workflow "proceeds without generating any summary file"; `docs/completion_summary.md` is
  never created → rule 16 violated. Under **F'**, `docs/completion_summary.md` IS created; only
  the PDF render / sharing is skipped.
- **Advanced track completion at Module 11, bootcamper declines** — `isBugCondition = true`.
  Same outcome: no summary under F; summary created (PDF/share skipped) under F'.
- **Mid-session explicit stop ("stop here"), bootcamper declines the offer** — `isBugCondition = true`.
  No summary under F; summary created under F'.
- **Track completion, bootcamper accepts ("yes")** — `isBugCondition = false`. Under both F and
  F', `docs/completion_summary.md` is created; F' additionally renders the PDF and surfaces it
  (unchanged from F's accepted-path behavior). Preserved.
- **No stopping point detected (mid-module work)** — `isBugCondition = false`. No offer, no
  summary, under both F and F'. Preserved.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- **Stopping-point detection** (`completion-summary-offer.md` → `## Stopping Point Detection Rules`):
  Module 7 completion, Module 11 completion, explicit stop request, and track switch at boundary
  must continue to be detected exactly as before, including the `## False Positive Guards`
  (stop phrase embedded in a longer substantive request does not trigger; missing/unreadable
  `config/bootcamp_progress.json` does not trigger).
- **Offer ordering** (`completion-summary-offer.md` → `## Ordering Rules`): track-completion
  sequence (celebration 🎉 → completion-summary offer → export results), mid-session sequence
  (acknowledge stop → completion-summary offer with no intervening prompts), and simultaneous-detection
  rule (follow track-completion sequence).
- **Repeat policy** (`completion-summary-offer.md` → `## Repeat Policy`): the offer/summary
  opportunity occurs at every stopping point; the same stopping point is not re-prompted after a decline.
- **Per-module recap** (`module-completion.md` → `## Recap Append`): `docs/bootcamp_recap.md` is
  still appended on every module completion via the `module-recap-append` hook, preserving all
  prior bytes. This file is **not** the bug site.
- **Graduation Step 0** (`graduation.md` → `## Step 0: Recap PDF Generation`): still attempts
  `docs/bootcamp_recap.pdf` with its Step 0a recovery / Step 0b validation / reconstruction
  fallbacks.
- **Graduation report** (`graduation.md` → `## Graduation Report`): `production/GRADUATION_REPORT.md`
  is still always generated, and Steps 1–5 are unchanged.
- **Journal & certificate** (`module-completion.md` → `## Bootcamp Journal`,
  `## Module Completion Certificate`): fixed-order execution with existing non-blocking error
  handling, unchanged.
- **Script behavior** (`generate_completion_summary.py`): session-log parsing, secret filtering,
  append-only JSONL integrity, module-ascending section ordering, four subsections per module,
  metadata completeness, size truncation, PDF fallback messages, and the separation of
  `docs/completion_summary.*` paths from `docs/bootcamp_recap.*` paths — all unchanged and still
  covered by the existing tests.
- **Steering-content tokens** relied on by integration tests: the offer file must still contain
  `yes/no`, `Completion Summary PDF`, the four content categories, the `celebration`/🎉 reference,
  and the `export` reference (see `test_completion_summary_integration.py` → `TestSteeringFileContent`).

**Scope:**

All situations where the bug condition does NOT hold must be completely unaffected by this fix.
This includes:

- The accepted path (`offerAnswer == "yes"`) — already creates the summary and renders/surfaces
  the PDF; F' behaves identically.
- Non-stopping-point situations (mid-module work) — no offer and no summary under both F and F'.
- All non-summary post-completion steps (recap, journal, certificate, export, record export,
  analytics, graduation offer, feedback reminder).

**Note:** The actual expected correct behavior for the bug condition is defined in the
Correctness Properties section (Property 1). This section focuses on what must NOT change.

## Hypothesized Root Cause

Based on the bug description and file investigation, the root cause is **a steering-contract
gating decision**, not a code defect:

1. **Creation gated on the yes/no answer (primary root cause)**: `completion-summary-offer.md`
   → `## Prompt Format` conflates two concerns into one binary choice:
   - *"If the bootcamper accepts ('yes'): invoke the narrative formatter followed by the PDF generator"*
   - *"If the bootcamper declines ('no'): proceed to the next post-completion step **without
     generating any summary file** ..."*
   The decline branch suppresses the **primary artifact** (the markdown document) together with
   the **secondary concern** (PDF rendering / sharing). Rule 16 requires the primary artifact to
   always exist.

2. **No unconditional generation step anchored in the flow**: Unlike `GRADUATION_REPORT.md`
   ("Always generate ...") and the recap PDF ("This step is **non-blocking** — graduation
   continues regardless of the outcome"), there is no "always create the completion summary"
   step. The summary's only trigger is the accepted offer.

3. **Not a script defect**: `generate_completion_summary.py` already writes the markdown
   unconditionally — `main()` calls `parse_session_log()` → `build_narrative()` →
   `render_markdown()` → `write_narrative(args.output, ...)` and only runs the PDF branch when
   `--pdf` is supplied. The script does **not** require the bootcamper's answer. The defect lives
   wholly in the steering contract that decides *whether* to run it.

4. **Residual failure mode (edge)**: When `config/session_log.jsonl` is missing or unreadable,
   `parse_session_log()` raises `FileNotFoundError`/`ValueError`; `main()` prints `ERROR` and
   returns exit code 1 **before** writing markdown. An empty-but-present log instead yields a
   valid markdown file with per-module "Session log was unavailable for this module." rendering.
   The always-create step must therefore wrap script invocation with non-blocking error handling
   (warn-and-continue) so a missing log degrades gracefully rather than blocking graduation —
   consistent with the recap-PDF "skip and inform" behavior. No script change is needed for this;
   it is handled in the steering contract.

## Correctness Properties

Property 1: Bug Condition (Fix) — Completion Summary Always Created

_For any_ graduation/stopping-point situation where the bug condition holds (`isBugCondition`
returns true — a stopping point is detected and `offerAnswer != "yes"`), the fixed workflow F'
SHALL generate `docs/completion_summary.md` by running `generate_completion_summary.py`
(markdown) regardless of the yes/no answer, and the document SHALL contain the module-by-module
collection of questions posed, bootcamper responses, actions taken, and artifacts generated
(as built from `config/session_log.jsonl`).

**Validates: Requirements 2.1, 2.2, 2.4**

Property 2: Bug Condition (Fix) — Yes/No Governs Only Secondary Concerns

_For any_ situation where a stopping point is detected, the yes/no answer SHALL govern **only**
the secondary presentation concerns: on `"yes"` the workflow additionally renders the shareable
PDF (`--pdf` → `docs/completion_summary.pdf`) and surfaces it; on `"no"` the workflow skips
**only** PDF rendering and surfacing/sharing. In both cases `docs/completion_summary.md` exists.
The markdown document's existence SHALL be independent of `offerAnswer`.

**Validates: Requirements 2.2, 2.3, 2.6**

Property 3: Bug Condition (Fix) — Non-Blocking Degradation

_For any_ situation where completion-summary generation fails (missing or empty session log,
file-system error, non-zero script exit), the fixed workflow SHALL handle it non-blockingly —
log a warning and continue the post-completion/graduation flow — and SHALL NOT halt or block
subsequent steps, consistent with the existing recap-PDF and graduation-report patterns.

**Validates: Requirements 2.5, 3.9**

Property 4: Preservation — Script Behavior Unchanged

_For any_ valid session log, progress file, and preferences file, `generate_completion_summary.py`
SHALL produce exactly the same result as before the fix: session-log parsing, secret filtering,
append-only JSONL integrity, module-ascending section ordering, four subsections per module,
metadata completeness, size truncation, PDF fallback messages, and the separation of
`docs/completion_summary.*` from `docs/bootcamp_recap.*`.

**Validates: Requirements 3.8, 3.9**

Property 5: Preservation — Detection, Ordering, and Repeat Policy Unchanged

_For any_ input where the bug condition does NOT hold (`offerAnswer == "yes"`, or no stopping
point detected), the fixed workflow SHALL behave identically to the original (`F(X) = F'(X)`),
preserving stopping-point detection, the false-positive guards, offer ordering (track-completion,
mid-session, simultaneous), and the repeat policy.

**Validates: Requirements 3.1, 3.4, 3.5, 3.7**

Property 6: Preservation — Per-Module Recap, Graduation Step 0, and Graduation Report Unchanged

_For any_ module completion or graduation run, the fixed workflow SHALL CONTINUE TO append the
per-module recap to `docs/bootcamp_recap.md` (preserving prior bytes), attempt the recap PDF in
graduation Step 0 with its fallbacks, always generate `production/GRADUATION_REPORT.md`, and run
the journal/certificate steps in their fixed order with existing non-blocking error handling.

**Validates: Requirements 3.2, 3.3, 3.6**

## Fix Implementation

### Design decision: keep the offer as a yes/no, but re-scope it to the PDF/share concern

Three options were considered for the offer:

1. **Remove the offer entirely** — always create both markdown and PDF. Rejected: it discards
   the bootcamper's control over the PDF render (which can `pip install fpdf2`) and breaks the
   integration tests that assert the file still presents a `yes/no` prompt and names the
   "Completion Summary PDF".
2. **Make the offer informational only** — always generate everything and just tell the user.
   Rejected for the same fpdf2/sharing-control reason and the same test breakage.
3. **Keep the binary yes/no, but re-scope it to the secondary concern (chosen)** — always
   generate the markdown unconditionally (modeled on `GRADUATION_REPORT.md`), and let the
   yes/no answer decide only whether the shareable PDF is rendered and the summary is surfaced/shared.

Option 3 is chosen because it (a) satisfies rule 16 (markdown always exists), (b) matches the
existing "always generate / non-blocking" patterns already in `graduation.md`, (c) keeps the
bootcamper's `--pdf` control, and (d) preserves the `yes/no` + "Completion Summary PDF" + four-category
+ celebration + export tokens that the existing integration tests assert on. The offer prompt's
**meaning** changes (it now governs PDF/share, not file creation), while its **shape** (binary
yes/no naming the Completion Summary PDF) is preserved.

### Change 1 — `completion-summary-offer.md`: remove the creation gate; make markdown unconditional

**File**: `senzing-bootcamp/steering/completion-summary-offer.md`

1. **Add an unconditional generation step** (new subsection, e.g. `## Always Generate the Summary Document`,
   placed before `## Summary Offer Message Format`). Specify that when a stopping point is detected,
   the agent runs the markdown generation **before** presenting the offer:

   ```bash
   python3 senzing-bootcamp/scripts/generate_completion_summary.py
   ```

   This always writes `docs/completion_summary.md`. State that this step is **non-blocking**:
   if the script exits non-zero or raises (e.g., `config/session_log.jsonl` missing/unreadable →
   `parse_session_log` raises and `main()` returns exit code 1), log a warning
   (`⚠️ Completion summary generation skipped: <reason>. Continuing.`) and continue the
   post-completion flow. Note that an empty-but-present session log still produces a valid
   markdown file with per-module "Session log was unavailable for this module." rendering, so it
   is not an error path.

2. **Rewrite `## Prompt Format`** so the binary choice governs only the secondary concern. Replace
   the current text:

   > - If the bootcamper accepts ("yes"): invoke the narrative formatter followed by the PDF generator
   > - If the bootcamper declines ("no"): proceed to the next post-completion step without generating any summary file and without re-prompting for the same stopping point

   with wording such as:

   > The completion summary document (`docs/completion_summary.md`) has already been created (see
   > "Always Generate the Summary Document"). The binary yes/no prompt governs only the shareable
   > **Completion Summary PDF** and surfacing:
   >
   > - If the bootcamper accepts ("yes"): render the shareable PDF by running
   >   `python3 senzing-bootcamp/scripts/generate_completion_summary.py --pdf` and surface the
   >   output path(s) to the bootcamper.
   > - If the bootcamper declines ("no"): skip **only** the PDF rendering and surfacing/sharing,
   >   then proceed to the next post-completion step without re-prompting for the same stopping
   >   point. `docs/completion_summary.md` remains created either way.

   Keep the `yes/no` phrasing intact (required by `test_steering_file_binary_prompt`).

3. **Reframe `## Summary Offer Message Format`** (Requirement 2.6) so the offer message makes
   clear the summary is already captured and the choice is about the shareable PDF. Preserve the
   literal string `Completion Summary PDF` and all four content categories (questions asked,
   answers given, actions taken, artifacts created) and the "organized by module" statement —
   these are asserted by `test_steering_file_names_deliverable` and
   `test_steering_file_mentions_four_categories`. Example reframed message:

   > 📄 **Completion Summary PDF**
   >
   > I've captured your bootcamp journey in a Completion Summary — organized by module, it
   > includes **Questions asked**, **Answers given**, **Actions taken**, and **Artifacts created**.
   > It's saved at `docs/completion_summary.md`. Would you like me to also render a shareable PDF? (yes/no)

4. **Leave unchanged**: `## Stopping Point Detection Rules`, `## False Positive Guards`,
   `## Ordering Rules`, and `## Repeat Policy`. The frontmatter (`inclusion: manual`, triggers,
   priority) is unchanged.

### Change 2 — `graduation.md`: anchor the always-create step

**File**: `senzing-bootcamp/steering/graduation.md`

1. Add a short note in `## Step 0: Recap PDF Generation` (or a sibling note near the top of the
   workflow steps list) stating that, independent of the recap PDF, the completion-summary
   document (`docs/completion_summary.md`) is **always** generated during the post-completion/graduation
   flow via `generate_completion_summary.py`, non-blocking, in the same spirit as the recap PDF and
   `GRADUATION_REPORT.md`. This anchors the contract in the graduation document so it is discoverable
   from the graduation workflow even though the generation is triggered by `completion-summary-offer.md`.
2. Do **not** alter Step 0a/0b/0c, Steps 1–5, or `## Graduation Report`. The recap PDF and
   `GRADUATION_REPORT.md` behavior is preserved verbatim.

### Change 3 — `module-completion.md`: align the celebration ordering note

**File**: `senzing-bootcamp/steering/module-completion.md`

1. In `## Path Completion Celebration`, add a one-line clarification that the completion-summary
   document is always created at track completion (with the offer in its existing position governing
   only the PDF/share), so the celebration ordering text stays consistent with the re-scoped offer.
   The existing ordering (celebration → completion-summary offer → export results → record export →
   analytics → certificate → graduation offer → feedback reminder) is unchanged.

### Change 4 — `generate_completion_summary.py`: confirm NO behavioral change needed

**File**: `senzing-bootcamp/scripts/generate_completion_summary.py`

**Verified**: `main()` always parses the log, builds the narrative, renders markdown, and calls
`write_narrative(args.output, ...)` to write `docs/completion_summary.md`; the PDF is produced only
when `--pdf` is passed (the `if args.pdf:` branch). So:

- Running the script with no flags satisfies "always create markdown".
- Running with `--pdf` satisfies the accept path (markdown + PDF).

Therefore **no change to the script's internals is required**. The one hard-failure path
(missing/unreadable `config/session_log.jsonl` → `FileNotFoundError`/`ValueError` →
`print("ERROR", ...)` → `return 1`, no markdown written) is handled at the **steering** layer by
the non-blocking wrapper described in Change 1 (warn and continue). If a future decision wanted
the script itself to emit a minimal placeholder markdown on a missing log, that would be a separate
enhancement; it is intentionally **out of scope** here to keep the fix minimal and to avoid
disturbing the existing unit/property/integration tests that exercise `parse_session_log`'s
`FileNotFoundError` contract.

### Token-budget housekeeping

The edited steering files change size, so after editing run
`python3 senzing-bootcamp/scripts/measure_steering.py` to refresh `token_count`/`size_category`
in `steering/steering-index.yaml` (CI runs `measure_steering.py --check`). `completion-summary-offer.md`
is currently 1341 tokens (`medium`); the reframing is roughly size-neutral and should stay `medium`.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate
the bug on the unfixed steering contract, then verify the fix creates the summary unconditionally
and preserves all surrounding behavior. Because the bug lives in a steering contract (markdown
text), the tests assert on the **contract content** of `completion-summary-offer.md` /
`graduation.md` (the source of the gating decision) and on the **script behavior** that the
contract relies on. Tests use pytest + Hypothesis with `@settings(max_examples=20)` and `st_`-prefixed
strategies, and live in `senzing-bootcamp/tests/`.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or
refute the root-cause analysis (creation gated on the yes/no answer in `completion-summary-offer.md`).
If refuted, re-hypothesize.

**Test Plan**: Add content assertions against `senzing-bootcamp/steering/completion-summary-offer.md`
that encode the fixed contract, and a behavioral assertion against `generate_completion_summary.py`
run with no flags. Run on the UNFIXED files to observe failures.

**Test Cases**:

1. **Decline-does-not-gate-creation (steering)**: Assert the offer file does **not** contain the
   phrase "without generating any summary file" (the gating clause). Will fail on unfixed code.
2. **Unconditional-generation-step present (steering)**: Assert the offer file instructs running
   `generate_completion_summary.py` unconditionally (markdown) before/independent of the yes/no
   answer. Will fail on unfixed code.
3. **Offer re-scoped to PDF/share (steering)**: Assert the `## Prompt Format` section ties "yes"
   to `--pdf`/surfacing and "no" to skipping only PDF/share (not file creation). Will fail on unfixed code.
4. **Markdown-always-written (script, edge)**: Run `main([])` against a temp dir with a valid
   `session_log.jsonl` and assert `docs/completion_summary.md` exists without `--pdf`. (Passes on
   current script — confirms Change 4's "no script change" claim and pins the behavior the contract
   depends on.)

**Expected Counterexamples**:

- The unfixed `completion-summary-offer.md` still contains "without generating any summary file"
  and ties creation to "yes" → tests 1–3 fail, demonstrating the gate.
- Root cause confirmed: the creation decision is in the steering contract, not the script (test 4
  passes on the unfixed script).

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed workflow produces the
expected behavior (the summary document is always created; only PDF/share is gated).

**Pseudocode:**

```
FOR ALL X WHERE isBugCondition(X) DO          // stoppingPointDetected AND offerAnswer != "yes"
  workflow := F'(X)
  ASSERT createsFile(workflow, "docs/completion_summary.md")
     AND summaryHasModuleByModuleContent(workflow)
     AND (X.offerAnswer = "no" IMPLIES skipsOnly(workflow, {render_pdf, surface_or_share}))
     AND nonBlockingOnFailure(workflow)
END FOR
```

Realized as: (a) steering-content assertions that the always-generate step exists and is
unconditional; and (b) a script-level property test that, for any generated session log, running
`main([])` (no `--pdf`) creates `docs/completion_summary.md` with the four per-module subsections,
while `main(["--pdf"])` additionally creates the PDF — modeling that the answer governs only the PDF.

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed workflow
produces the same result as the original.

**Pseudocode:**

```
FOR ALL X WHERE NOT isBugCondition(X) DO       // offerAnswer = "yes", or no stopping point
  ASSERT F(X) = F'(X)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation because it generates
many inputs across the domain (session logs, module sets, names, tracks) and catches edge cases that
fixed unit tests miss. The existing suites (`test_completion_summary_unit.py`,
`test_completion_summary_properties.py`, `test_completion_summary_integration.py`) already provide
strong preservation coverage for the script; they must continue to pass unchanged.

### Unit Tests

- Assert the new `## Always Generate the Summary Document` step exists in
  `completion-summary-offer.md` and references `generate_completion_summary.py` without `--pdf`.
- Assert the gating clause "without generating any summary file" is absent.
- Assert `## Prompt Format` ties "yes" to `--pdf`/surfacing and "no" to skipping only PDF/share.
- Assert `graduation.md` mentions the always-created completion summary as non-blocking.
- Confirm `generate_completion_summary.py` writes markdown with no flags (no behavioral change).

### Property-Based Tests

New test file: `senzing-bootcamp/tests/test_always_create_completion_summary_properties.py`
(pytest + Hypothesis, `@settings(max_examples=20)`, `st_`-prefixed strategies). Properties:

- **Markdown always created regardless of "answer"**: With `st_session_log()` generating varied
  multi-module logs, running `main([...])` without `--pdf` always creates `docs/completion_summary.md`
  containing the per-module sections — modeling Property 1 (the markdown does not depend on the
  yes/no answer). (Validates 2.1, 2.2, 2.4.)
- **Answer governs only the PDF**: For the same generated logs, `main([... , "--pdf"])` creates both
  the markdown and the PDF, while `main([...])` creates only the markdown — modeling that the
  secondary concern (PDF/share) is the only thing the yes/no toggles. (Validates 2.2, 2.3.)
- **Preservation of script invariants**: Reuse the existing `st_completion_entry` /
  `st_completion_entry_inputs` strategies to re-assert ordering, four-subsection presence, and
  metadata completeness are unchanged. (Validates 3.8.)
- **Graceful degradation**: With a generated empty/whitespace log, markdown is still produced with
  the "Session log was unavailable" rendering and no crash. (Validates 2.5, 3.9.)

### Integration Tests

- Extend `test_completion_summary_integration.py` (or add a sibling) to assert the end-to-end
  contract: after a simulated stopping point, `docs/completion_summary.md` exists for both the
  "yes" and "no" branches, and the PDF exists only for "yes" (using the existing
  `_create_sample_session_log` helper and the full `parse_session_log → build_narrative →
  render_markdown → write_narrative` pipeline, plus `render_completion_pdf` for the yes branch).
- Assert the reframed steering text in `completion-summary-offer.md` still satisfies all existing
  `TestSteeringFileContent` checks (frontmatter, four categories, "Completion Summary PDF", "yes/no",
  celebration, export) so the reframing does not regress the published contract.
- Assert `graduation.md` Step 0 / `## Graduation Report` behavior is untouched (recap PDF attempt and
  `GRADUATION_REPORT.md` always generated).
