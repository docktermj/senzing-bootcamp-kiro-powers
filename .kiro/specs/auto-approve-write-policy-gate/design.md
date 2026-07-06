# Design Document

## Overview

This feature adds a proactive, opt-in offer during Senzing Bootcamp onboarding to auto-approve the `write-policy-gate` hook, silencing the visible "Rejected"/"Accepted" intercept cycle while preserving all four of the hook's safety checks.

The feature is implemented entirely as **steering content and agent behavior** — it introduces no new runtime scripts or hook logic. Auto-approving a hook is a Kiro IDE user action performed in the Agent Hooks panel; the power cannot and should not silently modify the user's IDE auto-approve settings. Therefore the design's job is to (1) instruct the `Bootcamp_Agent` to surface the offer at the right moment, (2) give the bootcamper the exact steps to auto-approve via the Agent Hooks panel when they accept, and (3) record the bootcamper's decision in `config/bootcamp_preferences.yaml` so the offer is not repeated and downstream guidance stays consistent.

This keeps the change aligned with the power's constraints: stdlib-only, no new external endpoints, MCP URL untouched, and the `write-policy-gate.kiro.hook` file byte-for-byte unchanged.

### Goals

- Present a one-time opt-in offer after `write-policy-gate` is installed during onboarding.
- Preserve every safety check regardless of the bootcamper's choice.
- Persist the decision durably and idempotently in existing preferences infrastructure.
- Align the existing Section 0a explanation of the intercept cycle with the new offer.

### Non-Goals

- Automating the IDE-level auto-approve toggle (out of the power's control; guided manually).
- Modifying the `write-policy-gate` hook's checks or prompt.
- Changing how any other hook is installed or approved.

## Architecture

### Component Map

```text
onboarding-flow.md (steering)
├── §0a  Intercept-cycle explanation  ──── updated to reference the Auto_Approve_Offer (Req 5)
└── §1   Directory Structure
    ├── 1.2  Install Critical Hooks (write-policy-gate created here)
    └── 1.2a NEW: Auto-Approve Offer  ──── presents offer, records decision (Req 1,2,3,4)
                     │
                     ├── reads/writes ─► config/bootcamp_preferences.yaml
                     │                    (new key: write_policy_gate_auto_approve)
                     └── references ────► write-policy-gate.kiro.hook (unchanged)
```

The offer lives as a new sub-step (`1.2a`) immediately after the hook-installation step (`1.2`), because `1.2` is where `write-policy-gate` is created and verified. Placing the offer there satisfies the "after Write_Policy_Gate has been installed" precondition (Req 1.1) and lets the offer be skipped when installation failed (Req 1.5).

### Why steering, not a script

The `Bootcamp_Agent` executes onboarding by reading steering files. The offer is conversational (present choices, wait for explicit response, branch on the answer), which is agent behavior, not a deterministic CLI task. The only durable state is the recorded decision, and the power already persists onboarding choices to `config/bootcamp_preferences.yaml` using a documented "merge, don't clobber" convention (see Steps 1.2, 1b, 2d). We reuse that convention rather than introducing a new store.

### Preferences write is intercept-free

`config/bootcamp_preferences.yaml` is already on the `write-policy-gate` **INTERNAL-FILE PASS-THROUGH** allowlist (verified in `write-policy-gate.kiro.hook`). Recording the decision therefore does not itself produce a visible intercept cycle — consistent with the feature's intent.

## Components and Interfaces

### 1. Onboarding Step 1.2a — Auto-Approve Offer (new)

Added to `senzing-bootcamp/steering/onboarding-flow.md` directly after Step 1.2.

**Preconditions (Req 1.1, 1.5):**
- Reached only after the Critical Hooks step completes.
- Present the offer only if `write-policy-gate` is confirmed installed (it appears in the `hooks_installed` verification from Step 1.2). If `write-policy-gate` failed to install, skip 1.2a entirely (the failure-impact message from Step 1.2 already covers that case).

**Idempotency guard (Req 4.4):**
- Before presenting, read `config/bootcamp_preferences.yaml`. If the `write_policy_gate_auto_approve` key already holds a decision, do NOT present the offer again this onboarding.

**Offer content (Req 1.2, 1.3, 1.4, 3.1, 3.3):** a fixed block, e.g.:

```text
👉 The write-policy-gate safety check briefly intercepts each file write, which
shows up as a "Rejected ..." → "Accepted edits ..." message pair. You can silence
these messages by auto-approving the hook.

Auto-approving keeps ALL four safety checks fully active:
  1. Senzing SQL blocking
  2. Single-question enforcement
  3. File-path policy
  4. Root-placement policy
Any violation is still detected and blocked — only the visible intercept goes away.

  1. Auto-approve write-policy-gate — I'll show you how to enable it in the Agent Hooks panel.
  2. Keep the messages — leave things as they are.
```

The block is authored to satisfy each observable-content criterion (removes visible cycle; four checks named exactly; violations still blocked; exactly two selectable choices). Note: this is a ⛔ mandatory-gate style step — the agent stops and waits for explicit input rather than relying on the `ask-bootcamper` closing-question hook.

**Branching:**

| Bootcamper response | Agent behavior | Requirement |
|---|---|---|
| Accepts | Provide ordered Agent Hooks panel steps to add `write-policy-gate` to the auto-approve list; record `accepted`. | 2.2, 4.1 |
| Declines | Continue onboarding unchanged; tell bootcamper it can be enabled later from the Agent Hooks panel; record `declined`. | 2.3, 2.4, 4.2 |
| Unrecognized | Re-present the offer; keep waiting; make no auto-approve or preferences change. | 2.5, 1.6 |
| Awaiting (no selection) | Stay on the step; intercept cycle stays active; no auto-approve list change. | 1.6, 2.1 |

**Agent Hooks panel steps (accept path, Req 2.2):** ordered, IDE-accurate instructions — open the Agent Hooks panel (Kiro feature panel → Agent Hooks), locate the `write-policy-gate` hook (displayed as "Ask Kiro Hook to process your response"), and enable auto-approve for it. These steps are guidance only; the bootcamper performs the toggle.

### 2. Preferences key (new)

Add to `config/bootcamp_preferences.yaml.example` and write at runtime under a dedicated key:

```yaml
# Write-policy-gate auto-approve offer decision (set during onboarding Step 1.2a)
# Values: accepted, declined, or null (not yet offered)
write_policy_gate_auto_approve: null
```

**Write semantics (Req 4):**
- Accept → set value `accepted`; Decline → set value `declined` (distinct values, same key).
- Merge only this key; preserve all other keys/values byte-wise (Req 4.3), matching the file's existing merge convention.
- File missing → create it with just this key (Req 4.5).
- Write failure → leave existing content intact and tell the bootcamper the decision could not be saved (Req 4.6).
- Unparseable YAML → do not overwrite; tell the bootcamper the decision could not be saved (Req 4.7).

### 3. Section 0a alignment (edit)

Update the existing `## 0a. Why You May See "Rejected"/"Accepted" Messages` section in `onboarding-flow.md` to:
- Reference the `Auto_Approve_Offer` by that exact term, stating that accepting it removes the visible "Rejected"/"Accepted" messages for all subsequent `write-policy-gate` operations during onboarding (Req 5.1, 5.4).
- Frame the intercept cycle conditionally: describe it as suppressed for the remainder of onboarding when the offer was accepted, and as ongoing expected behavior when it was not (Req 5.2, 5.3).

Because 0a is read before Step 1.2a runs, the wording points forward to the upcoming offer ("you'll be offered the option to silence these in a moment") and the post-decision framing is realized by the agent's runtime knowledge of the recorded preference.

### 4. `write-policy-gate.kiro.hook` (unchanged)

No edit. Req 3.2 requires byte-for-byte stability; a test asserts the file hash is unchanged by this feature.

## Data Models

### `write_policy_gate_auto_approve` (preferences key)

| Aspect | Value |
|---|---|
| Location | `config/bootcamp_preferences.yaml` |
| Type | string enum |
| Domain | `accepted` \| `declined` \| `null` (unset) |
| Written by | `Bootcamp_Agent` at Step 1.2a |
| Read by | Step 1.2a (idempotency), Section 0a framing, future steps honoring the choice |

## Error Handling

| Condition | Handling | Req |
|---|---|---|
| `write-policy-gate` not installed | Skip Step 1.2a; no offer | 1.5 |
| Decision already recorded | Skip offer; proceed | 4.4 |
| Unrecognized response | Re-present offer; no state change | 2.5 |
| No selection yet | Stay on step; no auto-approve change | 1.6, 2.1 |
| Preferences file absent | Create with only the new key | 4.5 |
| Preferences write fails | Preserve existing content; inform bootcamper | 4.6 |
| Preferences unparseable | Do not overwrite; inform bootcamper | 4.7 |

## Correctness Properties

These invariants hold for any onboarding run and are the basis for the property-based tests below.

### Property 1: Preference preservation

For any pre-existing valid `bootcamp_preferences.yaml`, recording a decision changes only the `write_policy_gate_auto_approve` key; every other key and its value are byte-preserved.

**Validates: Requirements 4.3**

### Property 2: Decision totality and distinctness

After a resolved offer, `write_policy_gate_auto_approve` is exactly one of `accepted` or `declined`, and the two are never equal.

**Validates: Requirements 4.1, 4.2**

### Property 3: Offer idempotency

If `write_policy_gate_auto_approve` already holds a decision, no offer is presented and the value is unchanged for the remainder of that onboarding.

**Validates: Requirements 4.4**

### Property 4: Non-destructive failure

If the preferences file is missing, unwritable, or unparseable, existing content is never destroyed: missing → created with only the new key; unwritable/unparseable → original bytes untouched.

**Validates: Requirements 4.5, 4.6, 4.7**

### Property 5: Hook immutability

The byte content of `write-policy-gate.kiro.hook` is identical before and after the feature is applied, regardless of the bootcamper's choice.

**Validates: Requirements 3.2**

### Property 6: Safety-check invariance

For any write that violates a safety check, the outcome (detected and blocked) is identical whether or not the offer was accepted.

**Validates: Requirements 3.3, 3.4**

### Property 7: Two-choice exclusivity

The presented offer always exposes exactly two selectable choices — one accept, one decline — and no others.

**Validates: Requirements 1.4**

## Testing Strategy

Tests live in `senzing-bootcamp/tests/` (pytest + Hypothesis), consistent with existing onboarding-structure tests.

1. **Onboarding structure** — extend `test_onboarding_question_ownership.py` (which already enumerates expected headings including "0a. Why You May See..."): assert the new Step 1.2a heading exists in `onboarding-flow.md` and that it names all four safety checks and presents exactly two choices.
2. **Section 0a alignment** — assert `onboarding-flow.md` §0a contains the exact string `Auto_Approve_Offer` and references removal of the visible messages (Req 5.1, 5.4).
3. **Hook immutability** — assert the SHA-256 of `write-policy-gate.kiro.hook` matches a pinned baseline (Req 3.2), following the pattern in `test_steering_index_token_count_sync_preservation.py`.
4. **Preferences template** — assert `bootcamp_preferences.yaml.example` contains the `write_policy_gate_auto_approve` key defaulting to `null`.
5. **Preferences merge (property-based)** — Hypothesis test over arbitrary pre-existing valid YAML preference maps: applying the documented merge (set only `write_policy_gate_auto_approve`) preserves all other keys/values and sets exactly the target value (Req 4.3). Include cases for missing file (create) and malformed YAML (no clobber) to cover Req 4.5/4.7.

## Cross-Cutting Concerns

### Steering token budget (CI gate)

Editing `onboarding-flow.md` changes its token count. CI runs `measure_steering.py --check` against `steering/steering-index.yaml`. After the steering edits, re-run `python3 senzing-bootcamp/scripts/measure_steering.py` (update mode) so `steering-index.yaml` `file_metadata` and `budget.total_tokens` are re-synced; otherwise the `--check` gate fails. Keep the added content concise to limit budget impact.

### Hook registry / governance

The offer is authored so the `write-policy-gate` hook file and its registry entries (`hook-registry-critical.md`, `hook-registry.md`) are untouched, so `sync_hook_registry.py --verify` and the `governance-rules.yaml` assertions remain green. No new hook is introduced.

### CommonMark

New/edited Markdown must pass `validate_commonmark.py` (CI gate). Author the offer block and 0a edits as valid CommonMark.

## Requirements Traceability

| Requirement | Design element |
|---|---|
| 1.1–1.6 Present offer | Step 1.2a preconditions, offer block, awaiting/skip handling |
| 2.1–2.5 Opt-in choice | Step 1.2a branching table |
| 3.1–3.4 Preserve checks | Offer block enumerates 4 checks; hook file unchanged; violations still blocked by unmodified hook |
| 4.1–4.7 Record decision | `write_policy_gate_auto_approve` key + merge/create/failure/parse semantics |
| 5.1–5.4 Align 0a | Section 0a edit referencing `Auto_Approve_Offer`, conditional framing |
