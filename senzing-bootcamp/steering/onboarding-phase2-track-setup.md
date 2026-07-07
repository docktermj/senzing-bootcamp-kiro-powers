---
inclusion: manual
---

# Onboarding Phase 2 — Track Setup

Loaded after Step 4c (Comprehension Check) completes. Covers track selection, switching, language changes, validation gates, and the hook registry.

## 5. Track Selection

> **Authoritative source:** Track definitions are derived from
> `config/module-dependencies.yaml`. To update tracks, edit the dependency graph
> first, then run `python3 scripts/validate_dependencies.py` to verify consistency.

👉 Present tracks — not mutually exclusive, all completed modules carry forward:

- **Core Bootcamp** *(recommended)* — Modules 1, 2, 3, 4, 5, 6, 7. Recommended foundation covering problem definition through query/visualize.
- **Advanced Topics** *(not recommended for bootcamp)* — Modules 1–11. Adds production-readiness topics (performance, security hardening, monitoring, and packaging/deployment) as advanced add-ons layered on top of the core bootcamp.

Interpreting responses: "core"/"core_bootcamp"→start at Module 1, "advanced"/"advanced_topics"→start at Module 1. Bare number→clarify track vs module.

> ⛔ **MANDATORY GATE — STOP HERE.** After presenting the track options above, you MUST stop. Do NOT proceed to any module. Do NOT fabricate a user response. Do NOT assume a track choice. Do NOT generate text like "I'll go with Core Bootcamp for you." The bootcamper MUST provide their own choice. The `ask-bootcamper` hook will fire and prompt them. Wait for their real response before continuing.
>
> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not say "I'll go with X." Do not proceed to the next step. Wait for the bootcamper's real input.

## 5c. Advanced Track Knowledge Check

This step comes right after track selection and just before Module 1 begins. It gives Advanced-track bootcampers a light gut-check that the core entity-resolution idea landed before the deeper modules build on it.

**Advanced-only guard.** Run this step only when the persisted `track` in the preferences file is the Advanced track (`advanced_topics`). Skip it entirely for the Core track (`core_bootcamp`) and for any missing or unknown `track` value — those cases proceed straight to Module 1, and Core onboarding is unchanged. Do not present the question to anyone who is not on the Advanced track.

When the guard passes, present a single, warm, conversational question — this is a friendly gut-check, not a quiz or an exam. Draw it from a core ER concept the bootcamper just saw in the entity resolution introduction: that entity resolution decides whether different records refer to the *same real-world entity*.

Output format: your output MUST begin with 👉 followed by the one comprehension question, then stop. Example:

```text
👉 Quick gut-check before we dive in: in your own words, what is entity resolution deciding when it looks at two records?
```

If you paraphrase or reformulate the question, keep it to a single question and keep the 👉 prefix — it is still mandatory.

**Correct / understanding answer:** If the bootcamper answers correctly or clearly shows they understand that ER decides whether records point at the same real-world entity, affirm briefly and proceed to Module 1.

**Incorrect / unsure answer:** If the bootcamper answers incorrectly or signals they are unsure ("not sure," "I don't know"), offer a brief, plain-language Re_Explanation of the concept, then proceed to Module 1. Apply the bootcamper's current verbosity settings from the preferences file when giving the Re_Explanation.

**Note:** This step is NOT a gate — it is not mandatory, and it never prevents the bootcamper from continuing regardless of their answer. The `ask-bootcamper` hook handles the closing question on `agentStop`, so do not include inline closing questions here.

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
