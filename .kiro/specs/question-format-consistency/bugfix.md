# Bugfix Requirements Document

## Introduction

The bootcamp's standard question convention — defined in `senzing-bootcamp/steering/agent-behavior-rules.md` (Rule 4: Consistent Pointer Indicator) and reinforced in `conversation-protocol.md` and `agent-instructions.md` — requires that every input-requiring question is prefixed with 👉 at the start of the line and has its question text wrapped in bold (`**...**`), with the 👉 outside the bold span. The "leading-question guarantee" further requires that every yielding turn ends with exactly one 👉 leading question.

This bugfix consolidates three related question-formatting defects (all reported 2026-07-10) where that convention is not upheld. All three are gaps at two specific paths that other question-formatting specs did not cover:

- **The session-recreation re-presentation path** — when a pending question stored in `config/.question_pending` is surfaced again after a new session is created, the re-presentation path echoes the raw stored text (which carries no presentation formatting) instead of re-rendering through the standard question renderer, so the 👉 prefix and bold styling are lost.
- **The graduation / track-completion path** — the closing messages at bootcamp completion are plain statements rather than a clearly marked question, and the bootcamp-completion question (when present) omits the standard 👉 icon even though it carries a celebratory emoji and bold text.

**Relationship to existing specs.** This bugfix builds on, rather than duplicates, the existing question-formatting work:

- `question-visibility` establishes the additive bold-question convention across all question-bearing steering files; this bugfix ensures that convention survives the two paths above.
- `missing-pointer-marker` and `missing-pointing-prefix` fix the 👉 prefix in the onboarding flow; this bugfix addresses the graduation-completion question and the session-recreation re-presentation path, which those specs did not cover.
- `single-question-format` eliminates compound questions; this bugfix preserves that single-question guarantee for the newly-marked completion question.
- `leading-question-continuity` and `leading-question-enforcement` guarantee a closing 👉 question on every yielding turn (including hook-intercept and gap-filling turns); this bugfix extends that guarantee to the terminal graduation-completion turn.
- `session-resume` documents the welcome-back resume flow (which already renders its "Ready to continue" question with 👉 + bold); this bugfix targets the distinct case where a *pending* question is re-presented across session recreation without going through that renderer.

The scope of this fix is the agent guidance in the Markdown steering files (and any paired hook-prompt guidance / repo-level hook-prompt test) that governs these two paths. Everything under `senzing-bootcamp/` ships to bootcampers as a distributed Kiro Power.

## Bug Analysis

### Current Behavior (Defect)

Defect 1 — Pending question loses 👉/bold formatting across a new session (session-recreation re-presentation path):

1.1 WHEN a pending question stored in `config/.question_pending` (for example, the Module 3 → 4 transition question "Ready to move on to Module 4 (Data Collection)?") is re-presented to the bootcamper after a new session is created THEN the system presents the question text without the leading 👉 prefix.

1.2 WHEN that same pending question is re-presented after a new session is created THEN the system presents the question text without bold styling, so it reads as ordinary prose rather than a marked question.

1.3 WHEN the re-presentation path surfaces a stored pending question in a newly created session THEN the system echoes the raw stored question text instead of re-rendering it through the standard question renderer, which is why the 👉 prefix and bold styling are lost.

Defect 2 — No clearly marked completion question at the end of the bootcamp (graduation/track-completion path):

1.4 WHEN the track or graduation workflow completes THEN the system ends the turn with plain closing statements rather than a clearly marked question that uses an emoji and bold text.

1.5 WHEN the bootcamp is complete THEN the system provides no explicit, unambiguous prompt confirming finality and inviting any final discussion.

Defect 3 — Bootcamp-completion question omits the 👉 icon (graduation/track-completion path):

1.6 WHEN the bootcamp-completion question is presented (for example, "The Senzing Bootcamp is complete...") THEN the system marks it with a graduation/celebratory emoji and bold text but does NOT preface it with the standard 👉 icon that prefaces every other decision-point question.

### Expected Behavior (Correct)

2.1 WHEN a pending question stored in `config/.question_pending` is re-presented to the bootcamper after a new session is created THEN the system SHALL present the question with the leading 👉 prefix at the start of the line, matching the standard format used elsewhere in the bootcamp.

2.2 WHEN that same pending question is re-presented after a new session is created THEN the system SHALL present the question text wrapped in bold (`**...**`), with the 👉 outside the bold span.

2.3 WHEN the re-presentation path surfaces a stored pending question in a newly created session THEN the system SHALL re-render the question through the standard question renderer (persisting enough presentation metadata, or re-rendering from a canonical format) rather than echoing the raw stored text, so the re-presented question is formatted identically to when it was originally asked.

2.4 WHEN the track or graduation workflow completes THEN the system SHALL end the turn with exactly one clearly marked question that uses an emoji and bold text (for example, "[emoji] **The bootcamp has completed. Do you have anything else you would like to discuss?**").

2.5 WHEN the bootcamp is complete THEN the system SHALL present a single, unambiguous prompt that signals finality and invites any final discussion.

2.6 WHEN the bootcamp-completion question is presented THEN the system SHALL preface it with the 👉 icon at the start of the line (in addition to any celebratory emoji) and keep it a single, unambiguous question (for example, "👉 **The Senzing Bootcamp is complete. Do you have anything else you would like to discuss?**").

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent presents any well-formed 👉 question outside the session-recreation re-presentation path and the graduation-completion path (onboarding, module steps, module transitions, feedback, and the in-session resume welcome-back question) THEN the system SHALL CONTINUE TO render it with the 👉 prefix and bold question text as it does today.

3.2 WHEN a pending question is presented within the same session in which it was written (no session recreation) THEN the system SHALL CONTINUE TO render it with the 👉 prefix and bold styling.

3.3 WHEN the agent ends any yielding turn THEN the system SHALL CONTINUE TO enforce the One Question Rule — exactly one 👉 leading question per yielding turn.

3.4 WHEN the agent presents informational content that does not require bootcamper input (banners, journey maps, summaries, recap/announcement lines, status updates) THEN the system SHALL CONTINUE TO omit the 👉 prefix from that content.

3.5 WHEN a question is written to `config/.question_pending` THEN the system SHALL CONTINUE TO validate it through the `write-policy-gate` hook and apply the single-question enforcement check unchanged.

3.6 WHEN a bootcamper responds to a pending question THEN the system SHALL CONTINUE TO apply the Treat-as-answer and Delete-and-process rules — deleting `config/.question_pending` and processing the answer as the first action of the turn — regardless of how the question was rendered.

3.7 WHEN the graduation / track-completion workflow produces its other artifacts and announcements (recap, recap PDF, transcript, certificate, indexes, graduation report) THEN the system SHALL CONTINUE TO generate and announce them as it does today, unaffected by the closing-question formatting change.
