---
inclusion: manual
---

## Path Completion Detection

After each module, check if the user finished their track's last module:

| Track | Complete after |
|-------|----------------|
| Core Bootcamp    | Module 7  |
| Advanced Topics  | Module 11 |

## Path Completion Celebration

> **Note:** The per-module artifacts (consolidated recap section including its `### Journal` subsection, completion certificate) for the final module of a track are produced by the Shared Boundary-Detection Trigger BEFORE this celebration runs. Track completion adds the celebration and next-step guidance below — it never replaces or suppresses the final module's per-module artifacts.

> **Note:** The completion-summary document (`docs/completion_summary.md`) is always created at track completion; the completion-summary offer in its existing position (between the celebration and the export option) governs only the shareable PDF/share, not the document's creation.

### Graduation Banner

<!-- AGENT INSTRUCTION — not shown to the bootcamper.
Display the GRADUATION banner below VERBATIM as the FIRST output of the
track-completion celebration, before the reconciliation passes, the shareable
deliverable renders, and the "🎉 You've completed…" summary below. It bookends
the bootcamp: the welcome banner signposts the start, this banner signposts
the finish.

Show the banner exactly ONCE per track completion. The track-completion
celebration ALWAYS runs at track completion — before the graduation offer — so
every bootcamper who completes a track sees the banner here, INCLUDING one who
later declines graduation or has `skip_graduation` set. When the bootcamper
ACCEPTS graduation, the graduation workflow (graduation.md) coordinates with
this note: because the celebration already displayed the banner for this
completion, graduation.md does NOT display it again, keeping it to at most once
per track completion.

This banner is display-only: it introduces no new question or gate, and it
does NOT change the artifact guarantees, the recap/transcript rendering order,
or the mandatory closing question defined later in this file.
-->

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎓🎓🎓  GRADUATION  🎓🎓🎓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Recap Reconciliation & Backfill (Path A final safety net)

Before presenting the celebration, reconcile the recap deliverable against the recorded progress so the final per-module recap is complete. Each module's section is appended-and-verified synchronously at module completion (see `module-completion-artifacts.md`); this pass is the **final safety net** that catches any section still missing at track completion — a write lost across a session boundary or a final-module hook miss.

1. Reconcile `docs/bootcamp_recap.md` against `config/bootcamp_progress.json` `modules_completed` and backfill any missing per-module `## Module N:` section:

   ```bash
   python senzing-bootcamp/scripts/completion_artifacts.py --progress config/bootcamp_progress.json --recap docs/bootcamp_recap.md --progress-dir docs/progress --backfill
   ```

   The applier uses a pure set difference, so it appends only the sections that are missing — existing sections are preserved byte-for-byte (Req 3.1) and a re-run on an already-consistent recap makes no changes (Req 3.2). It exits non-zero naming any module whose section it could not produce, so a silent gap is never reported as complete.

2. This step is **non-blocking**: if the applier cannot run or reports a remaining gap, log a warning (naming the still-missing modules) and continue the celebration. It runs silently when nothing needs backfilling.

3. **Ordering relative to the recap PDF:** this reconciliation runs *before* the recap PDF is rendered. The recap PDF (and the Q&A transcript) are produced **here at track completion** — by the `### Shareable Deliverables: Recap PDF & Q&A Transcript` subsection below, after this recap reconciliation and the transcript reconciliation pass — so every completed module has a `## Module N:` section in the rendered deliverable. Graduation is not required for these deliverables: `graduation.md` Step 0a/0b re-runs the same reconcile-then-render as an **idempotent safety net** (reconciliation is a no-op on a consistent recap/log and the renderers overwrite in place), refreshing rather than duplicating them.

### Q&A Transcript Reconciliation (Path A final safety net)

After the recap reconciliation above and **before** rendering the shareable deliverables below, reconcile the Q&A transcript source so the rendered transcript is as complete as the recap's captured Q&A content. This mirrors graduation Step 0b.4's reconcile-before-render ordering.

The logged Q&A events are emitted voluntarily by the agent (per `qa-transcript.md`) and are **not** backed by a write-tool hook, so they can silently under-represent the session. Reconcile the session log against the enforced recap source before the transcript is rendered.

1. Reconcile the session log against the recap's `### Questions & Responses` pairs by running the transcript reconciliation pass:

   ```bash
   python scripts/reconcile_transcript.py
   ```

   With no arguments the script uses the canonical paths (`docs/bootcamp_recap.md` and `config/session_log.jsonl`). It counts logged `question` events against the recap's Q&R pairs per module and, on a material shortfall, backfills the missing pairs into `config/session_log.jsonl` (reusing the existing `session_logger` completion-event schema) so the subsequent render is complete. The pass is **idempotent** (a no-op when the counts already agree, or when the recap has no Q&R content) and **non-blocking**: it never adds a per-write hook or per-write process spawn, and runs only here at track completion / stopping points.

2. This step is **non-blocking regardless of the reconcile script's exit code** — whether it succeeds, no-ops, or exits non-zero after an internally handled error, always proceed to the render below. On a non-zero exit or any warning, log the reason and continue; the render falls back to the existing session-log content.

**Ordering invariant:** reconcile the transcript log (this step) **then** render the transcript (the subsection below). The transcript is never rendered from an unreconciled log.

### Shareable Deliverables: Recap PDF & Q&A Transcript

After **both** reconciliation passes above (recap Markdown, then transcript log) and **before** the graduation offer, always render the two shareable derived deliverables from their now-reconciled sources: the recap PDF (`docs/bootcamp_recap.pdf`) from the reconciled recap, and the Q&A transcript (`docs/bootcamp_transcript.md`) from the reconciled session log.

This subsection **always** runs at track completion. It runs **independent of whether the bootcamper accepts graduation** — a bootcamper who declines graduation still receives both deliverables — and it runs **regardless of `skip_graduation`**: the `skip_graduation` preference gates only the graduation *workflow* (the offer and `graduation.md`), never these deliverables. Graduation, when it runs, re-executes the same reconcile-then-render as an idempotent safety net that overwrites in place rather than producing conflicting duplicates.

**Ordering invariant:** reconcile the recap **then** render the PDF; reconcile the transcript log **then** render the transcript. Both renders here run only after the two reconciliation passes above.

1. Render the recap PDF from the reconciled recap:

   ```bash
   python scripts/generate_recap_pdf.py
   ```

   This reads the reconciled `docs/bootcamp_recap.md` and overwrites `docs/bootcamp_recap.pdf`. On success, inform the bootcamper: "📄 Recap PDF generated at `docs/bootcamp_recap.pdf`."

2. Render the Q&A transcript from the reconciled session log:

   ```bash
   python scripts/generate_transcript.py
   ```

   This reads the reconciled `config/session_log.jsonl` and overwrites `docs/bootcamp_transcript.md`, an ordered Q&A record grouped by module. On success, inform the bootcamper: "📝 Q&A transcript generated at `docs/bootcamp_transcript.md`."

3. This subsection is **non-blocking**, and the recap PDF is **guaranteed**: `generate_recap_pdf.py` routes through the tiered strategy — the rich `fpdf2` renderer when available, a best-effort auto-install of `fpdf2` otherwise, and a stdlib-only PDF writer as the final tier — so a valid `docs/bootcamp_recap.pdf` is produced even when `fpdf2` is absent (a plainer PDF, not "Markdown only"). Installing `fpdf2` (`pip install fpdf2`) simply upgrades the result to the professionally designed PDF. Should a genuine, unexpected render error still occur, log a warning, point the bootcamper to the existing `docs/bootcamp_recap.md` as the content backstop, and continue — a generation failure never blocks the celebration, the remaining offers, or the graduation offer. When the transcript renderer reports no Q&A events, no transcript is written; inform the bootcamper and continue.

> **Note (enforced guarantee):** The always-run renders above are the *best-effort* pass; they stay non-blocking so a render failure never holds up the celebration. The recap PDF / transcript / recap Markdown are additionally **guaranteed** at every stopping point by the `enforce-critical-artifacts` `Stop` hook, which runs `python senzing-bootcamp/scripts/ensure_graduation_artifacts.py` and blocks "done" until each artifact exists and is non-empty. That orchestrator preserves the reconcile-then-render ordering used here (reconcile the source, then render) and guarantees a valid `docs/bootcamp_recap.pdf` via the tiered strategy (the best-effort `fpdf2` auto-install may run; otherwise the stdlib-only PDF writer is used), so a rendered PDF always exists. Any `docs/bootcamp_recap.html` is only a supplementary extra, never the artifact that satisfies the rendered-recap guarantee. The enforcement gate is what makes these deliverables guaranteed; it does not change the non-blocking behavior of this celebration pass.

### fpdf2 Preflight Note (before the completion-summary PDF / export offer)

At track completion, before the completion-summary PDF offer and the export option below, run the preflight helper so the bootcamper learns up front which recap PDF they'll get — the professionally designed one when `fpdf2` is available, or a plainer but still valid PDF otherwise (a PDF is produced either way):

```bash
python3 senzing-bootcamp/scripts/fpdf2_preflight.py
```

If it prints a line, surface that line to the bootcamper; if it prints nothing, continue silently. This step is **non-blocking regardless of exit code** — the completion-summary PDF and export offers always run afterward whether or not a note was shown. The note only distinguishes the rich vs. plainer PDF; a valid recap PDF is produced regardless, so it never implies the recap PDF might be skipped.

When track is complete, present:

- 🎉 "You've completed the [track name]!"
- Summary of all artifacts built (code, data, docs)
- Where everything lives (src/, data/transformed/, docs/, config/, database/)
- Reference to `docs/bootcamp_recap.md` (the consolidated per-module log, including each module's `### Journal` subsection)
- Next options: switch to longer track (modules carry forward), harden for production, or start using the code
- Export option: "Would you like to export a shareable report of your bootcamp results?" — when accepted, run `python3 scripts/export_results.py` and present the output path to the bootcamper. This option appears only at track completion, not after every module.
- Record export offer (after the export option, before the analytics offer): "📋 Would you like a record of your bootcamp journey? You can share it with your team or use it to replay the same setup on another project." — when accepted, run `python3 scripts/record_export.py` and present the output path (`docs/bootcamp_record.yaml`) to the bootcamper. When declined, proceed to the next step without generating any export file.
- Analytics offer (after the record export offer, before the certificate generation): "📊 Would you like to see analytics on your bootcamp journey? I can show you time distribution, friction points, and how your pace compares to baselines." — when accepted, run `python3 scripts/bootcamp_analytics.py` and present the output conversationally.
- Certificate generation (after the analytics offer, before the graduation offer):
  Run `python3 senzing-bootcamp/scripts/generate_graduation_certificate.py` silently
  (no confirmation prompt). If it succeeds, display:
  "🎓 Graduation certificate generated at docs/graduation/"
  If it fails, log a warning and continue without blocking subsequent steps.
- Graduation offer (after the certificate generation, before the feedback reminder):
  1. Read `skip_graduation` from `config/bootcamp_preferences.yaml`. If `skip_graduation` is `true`, skip the graduation offer entirely.
  2. If not skipped, present: "🎓 Would you like to run the graduation workflow? It will help you turn your bootcamp project into a production-ready codebase — clean structure, production configs, CI/CD pipeline, and a migration checklist."
  3. If accepted: load `steering/graduation.md` and begin the workflow.
  4. If declined: ask "Would you like me to remember this choice so I don't ask again?" If the bootcamper confirms, set `skip_graduation: true` in `config/bootcamp_preferences.yaml`. Then continue with the remaining post-completion options.
- Feedback Submission Reminder (after the graduation offer sequence, before the retrospective):
  1. Check if `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` exists.
  2. If it exists, read the file and check for at least one `## Improvement:` heading below the `## Your Feedback` section (headings outside fenced code blocks count as real entries; the template block inside a fenced code block does not).
  3. If feedback entries exist, display: "📋 You have feedback saved in `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`. Would you like to share it with the power author?"
  4. If the bootcamper accepts, present the sharing options:

     **How would you like to share your feedback?**

     1. **Email** — Send to <support@senzing.com> with subject "Senzing Bootcamp Power Feedback". I can format the content for easy copy-paste.
     2. **GitHub Issue** — Create an issue on the senzing-bootcamp power repository. I can format it as a markdown-ready issue body.
     3. **Copy path** — I'll show you the full file path so you can share it however you prefer.

     Do not automatically send emails or create GitHub issues — wait for explicit bootcamper confirmation before taking any external action.
  5. If the bootcamper declines (says "no", "skip", "not now", or any declining response), proceed to the next step without re-prompting about feedback. Do not ask about feedback sharing again during this track completion sequence.
  6. If the feedback file does not exist or contains no entries beyond the template header, display the fallback: "Say 'bootcamp feedback' to share your experience"

Load `lessons-learned.md` and offer the retrospective.

### Bootcamp-Completion Closing Question

Once every offer above is resolved — including the retrospective offered from `lessons-learned.md` — close the track-completion turn with exactly one clearly marked question. This closing question is **unconditional**: it is always presented at the end of the celebration, even when every offer was declined, so the bootcamper always receives an explicit signal that the bootcamp is complete and an invitation to raise anything else.

Present it through the standard question renderer — the 👉 pointer at the start of the line, **outside** the bold span, with the question text wrapped in CommonMark bold:

```text
👉 **The Senzing Bootcamp is complete. Do you have anything else you would like to discuss?**
```

A celebratory emoji (for example 🎉 or 🎓) MAY appear before or inside the bold span, but it does NOT replace the 👉 — the pointer always leads the line. This terminal turn carries the same One Question Rule as every other yielding turn: emit exactly one 👉 question, write it to `config/.question_pending`, and stop immediately after (🛑 STOP). Do not append any statement, offer, or follow-up after this question.
