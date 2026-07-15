---
inclusion: manual
---

# Onboarding Phase 2 — Track Setup

Loaded after the Detail Level step (Step 4a, verbosity) in phase 1b. Covers track selection, programming language selection, the comprehension check, the advanced track knowledge check, switching tracks, language changes, validation gates, and the hook registry.

> **Note on file name (historical):** The name `track-setup` is retained for stability, but this file now also owns programming language selection and the comprehension check (both moved here from phase 1b).

## 5. Track Selection

> **Authoritative source:** Track definitions are derived from
> `config/module-dependencies.yaml`. To update tracks, edit the dependency graph
> first, then run `python3 scripts/validate_dependencies.py` to verify consistency.

👉 **Present tracks — not mutually exclusive, all completed modules carry forward:**

- **Core Bootcamp** *(recommended)* — Modules 1, 2, 3, 4, 5, 6, 7. Recommended foundation covering problem definition through query/visualize.
- **Advanced Topics** *(not recommended for bootcamp)* — Modules 1–11. Adds production-readiness topics (performance, security hardening, monitoring, and packaging/deployment) as advanced add-ons layered on top of the core bootcamp.

Interpreting responses: "core"/"core_bootcamp"→start at Module 1, "advanced"/"advanced_topics"→start at Module 1. Bare number→clarify track vs module.

> ⛔ **MANDATORY GATE — STOP HERE.** After presenting the track options above, you MUST stop. Do NOT proceed to any module. Do NOT fabricate a user response. Do NOT assume a track choice. Do NOT generate text like "I'll go with Core Bootcamp for you." The bootcamper MUST provide their own choice. The `ask-bootcamper` hook will fire and prompt them. Wait for their real response before continuing.
>
> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not say "I'll go with X." Do not proceed to the next step. Wait for the bootcamper's real input.

## 5a. Programming Language Selection

Detect the user's platform (`platform.system()`), then call `get_capabilities` or `sdk_guide` on the Senzing MCP server for the supported languages on that platform. The hard gate in Step 0b guarantees MCP is available — call the tool directly and present the returned programming language list to the bootcamper.

When presenting this question, always use the phrase "programming language" — never the bare word "language" alone — to avoid ambiguity with natural/spoken languages.

The agent MUST use the phrase "programming language" (not just "language") when presenting the selection question to the bootcamper.

👉 **Present the MCP-returned programming language list. If the MCP server flags any language as discouraged, unsupported, or limited on the user's platform (e.g., Python on macOS), relay that warning clearly and suggest alternatives. For example: "The Senzing MCP server indicates Python is not recommended on macOS — [reason from MCP]. I'd suggest Java, C#, Rust, or TypeScript instead. Would you like to pick one of those?"**

*Internal directive (not shown to the bootcamper): end your turn on the question above and wait for the bootcamper's programming language choice before proceeding.*

> **Note:** All listed languages produce working code via the MCP server's
> `generate_scaffold` tool. However, the depth of supplementary examples
> (via `find_examples`) may vary — Python and Java currently have the most
> extensive example coverage. This does not affect the bootcamp workflow.

> Tip: If you plan to use these bootcamp artifacts in production, consider choosing the language your team already uses — the code we generate here is designed to be your starting point for real-world use.

Persist the selection to `config/bootcamp_preferences.yaml`.

Load language steering file immediately after confirmation (`lang-python.md`, `lang-java.md`, etc.).

> **Internal directive — not shown to the bootcamper.** Treat programming language selection as a ⛔ gate step: it requires the bootcamper's actual choice. Do NOT assume or fabricate a programming language preference, and do NOT say "I'll go with X."
>
> This is a MANDATORY GATE — you MUST stop and wait for the bootcamper's real input (🛑 STOP — end your response here). End your turn on the question above; do not answer it and do not proceed to the next step until the bootcamper responds.

### 5b. Comprehension Check

Before moving on, give the bootcamper a moment to absorb everything from the overview and their track and programming language selections. Present a warm, conversational check-in — this is an invitation, not a quiz.

Output format: your output MUST begin with 👉 followed by the comprehension check question. Compose it as a single, non-compound question on the first attempt. Example:

```text
👉 That was a lot of ground to cover — does everything so far make sense?
```

If you paraphrase or reformulate the question, keep it a single question and the 👉 prefix is still mandatory.

🛑 STOP — Wait for the bootcamper's Real_Answer before proceeding to Module 1 (or, on the Advanced track, to the Advanced Track Knowledge Check).

**Acknowledgment handling:** If the bootcamper responds with an acknowledgment — phrases like "looks good," "makes sense," "no questions," "let's go," "ready," "all clear," or "got it" — that acknowledgment is a Real_Answer, so proceed directly to Module 1 (or, on the Advanced track, to the Advanced Track Knowledge Check). Do not ask follow-up questions about the overview.

**Clarification handling:** If the bootcamper asks a clarification question, that too is a Real_Answer: answer it using the bootcamper's current verbosity settings from the preferences file, then re-present this comprehension check. Repeat this cycle — answer, then re-present the check-in and check for additional questions — until the bootcamper signals they are ready to move on.

> **Internal directive — not shown to the bootcamper.** This comprehension check is governed by the Answer_Required_Rule (see `conversation-protocol.md`): it requires the bootcamper's Real_Answer before you proceed to Module 1 (or, on the Advanced track, to the Advanced Track Knowledge Check). A Real_Answer is either a readiness acknowledgment ("makes sense," "no questions," "ready," etc.) or a clarification question — answer the latter, then re-present this check-in, looping until the bootcamper signals readiness. Do NOT proceed as if the bootcamper acknowledged when they said nothing; treating silence as readiness is an Assumed_Answer and is forbidden. The `ask-bootcamper` hook owns the closing question on `Stop`, so do not include inline closing questions here.

## 5c. Advanced Track Knowledge Check

This step comes right after the comprehension check and just before Module 1 begins. It gives Advanced-track bootcampers a light gut-check that the core entity-resolution idea landed before the deeper modules build on it.

**Advanced-only guard.** Run this step only when the persisted `track` in the preferences file is the Advanced track (`advanced_topics`). Skip it entirely for the Core track (`core_bootcamp`) and for any missing or unknown `track` value — those cases proceed straight to Module 1, and Core onboarding is unchanged. Do not present the question to anyone who is not on the Advanced track.

When the guard passes, present a single, warm, conversational question — this is a friendly gut-check, not a quiz or an exam. Draw it from a core ER concept the bootcamper just saw in the entity resolution introduction: that entity resolution decides whether different records refer to the *same real-world entity*.

Output format: your output MUST begin with 👉 followed by the one comprehension question, then stop. Example:

```text
👉 Quick gut-check before we dive in: in your own words, what is entity resolution deciding when it looks at two records?
```

If you paraphrase or reformulate the question, keep it to a single question and keep the 👉 prefix — it is still mandatory.

🛑 STOP — Wait for the bootcamper's Real_Answer before proceeding to Module 1. This 👉 question is governed by the Answer_Required_Rule (see `conversation-protocol.md`): it requires a Real_Answer, and you must never answer it for the bootcamper. End your turn on the question; do not assume a response, do not supply a Re_Explanation the bootcamper did not prompt, and do not proceed as if answered when they said nothing.

**Correct / understanding answer:** If the bootcamper answers correctly or clearly shows they understand that ER decides whether records point at the same real-world entity, affirm briefly and proceed to Module 1.

**Incorrect / unsure answer:** If the bootcamper answers incorrectly or signals they are unsure ("not sure," "I don't know"), offer a brief, plain-language Re_Explanation of the concept, then proceed to Module 1. Apply the bootcamper's current verbosity settings from the preferences file when giving the Re_Explanation.

**Explicit skip / decline:** If the bootcamper explicitly declines or asks to move on ("skip", "let's just start", "no comment"), that is a Real_Answer — record it and proceed to Module 1 without a Re_Explanation. An explicit skip is a choice the bootcamper makes; silence is not.

**Note:** Correctness never gates *progress* — the bootcamper continues to Module 1 whether their answer is right, wrong, or an explicit skip — but a Real_Answer is still required before advancing: never treat silence as an answer, and never supply one yourself (Answer_Required_Rule). The `ask-bootcamper` hook handles the closing question on the `Stop` trigger, so do not include inline closing questions here.

## Switching Tracks

All completed modules carry forward. Read the appropriate progress file — in team mode, use the member-specific progress file (`config/progress_{member_id}.json` in co-located mode, or `{repo_path}/config/bootcamp_progress.json` in distributed mode); in single-user mode, use `bootcamp_progress.json`. Show new track requirements vs. done, update preferences, resume from first incomplete module.

## Changing Language

Update preferences. Warn: existing code in `src/` must be regenerated. Data/docs/config unaffected. Don't mix languages.

## Validation Gates

> **Authoritative source:** Gate conditions are derived from
> `config/module-dependencies.yaml`. To update gate conditions, edit the
> dependency graph first, then run `python3 scripts/validate_dependencies.py` to
> verify consistency.

Run `validate_module.py --module N` before proceeding. Update `bootcamp_progress.json` and `bootcamp_preferences.yaml`. Every 3 modules: progress bar.

Gate checks:

| Gate   | Requires                                                                           |
|--------|------------------------------------------------------------------------------------|
| 1→2    | Problem documented, sources identified, criteria defined                           |
| 2→3    | SDK installed, DB configured, test passes                                          |
| 3→4    | System verification passed or skipped                                              |
| 4→5    | Sources collected, files in `data/raw/`                                            |
| 5→6    | Sources evaluated, mapped, programs tested, quality >70%                           |
| 6→7    | Sources loaded, no critical errors                                                 |
| 7→8    | Queries answer business problem. Load `cloud-provider-setup.md`                    |
| 8→9    | Baselines captured, bottlenecks documented                                         |
| 9→10   | Security checklist complete, no critical vulns                                     |
| 10→11  | Monitoring configured, health checks passing                                       |

## Hook Registry

#[[file:senzing-bootcamp/steering/hook-registry-critical.md]]
