# Bugfix Requirements Document

## Introduction

This bugfix consolidates two related, low-priority defects reported in `SENZING_BOOTCAMP_POWER_FEEDBACK.md` (both dated 2026-07-10). Both are cases where `write-policy-gate`-related content produces stale or unwanted **visible** output to the bootcamper — the two remaining visible-noise/staleness gaps left after the related specs listed below.

- **Defect 1 (Documentation) — stale onboarding note.** During onboarding, the agent presents a reassurance note (`onboarding-flow.md` section "0a. Why You May See 'Rejected'/'Accepted' Messages") that describes an intercept-then-retry write cycle where the `write-policy-gate` briefly holds a write (surfacing as "Rejected") before the agent re-issues it (surfacing as "Accepted"). The bootcamper reports this behavior no longer occurs, so the note is inaccurate and adds noise to the onboarding preamble, warning bootcampers about messages they will never see.
- **Defect 2 (UX) — narration on silent re-invoke.** When the `write-policy-gate` PreToolUse hook intercepts a write to a routine power-managed internal file (e.g., `config/bootcamp_progress.json`) and the INTERNAL-FILE PASS-THROUGH applies, the agent occasionally emits a visible line such as "Internal progress file — re-invoking silently." before re-issuing the write. The hook's INTERNAL-FILE PASS-THROUGH rule and the agent silence rule both require **zero visible tokens** on a routine internal-file pass-through, so this narration is noise that leaks internal bookkeeping and contradicts the documented silence behavior.

**Relationship to existing specs.** This bugfix builds on, and does not duplicate, prior related work: `write-policy-gate-ux`, `suppress-policy-pass-output` (suppressed the older "policy: pass" output), `hook-visual-noise-reduction`, `hook-silent-fast-path`, `silent-hook-architecture`, `write-gate-momentum-preservation` (leading-question guarantee + extended the internal-file pass-through set), `onboarding-flow`, and `split-onboarding-flow`. Those specs reduced hook noise and guaranteed a closing question, but did not remove the stale onboarding note (Defect 1) nor eliminate the specific narration line emitted on internal-file pass-through (Defect 2). This bugfix targets exactly those two residual gaps.

**Security constraint.** Defect 2 concerns suppressing agent **narration only**. The `write-policy-gate` PreToolUse hook, its `preToolUse` trigger, and its write-type `toolTypes` (`fs_write|str_replace|fs_append`) MUST NOT be removed or weakened. The INTERNAL-FILE PASS-THROUGH rule already mandates zero tokens; the fix reinforces that agent-side behavior (in `agent-instructions.md` and/or the relevant steering) rather than changing the gate's security behavior.

## Bug Analysis

### Current Behavior (Defect)

What currently happens: the bootcamper sees stale or unwanted `write-policy-gate`-related output.

1.1 WHEN the agent presents the onboarding preamble (`onboarding-flow.md` section "0a. Why You May See 'Rejected'/'Accepted' Messages") THEN the system displays a reassurance note describing a `write-policy-gate` intercept-then-retry ("Rejected" → "Accepted") write cycle that no longer occurs, presenting inaccurate information and adding noise to onboarding.

1.2 WHEN the `write-policy-gate` PreToolUse hook intercepts a write to a routine power-managed internal file (e.g., `config/bootcamp_progress.json`) and all INTERNAL-FILE PASS-THROUGH NOT-guards hold THEN the agent emits a visible narration line (e.g., "Internal progress file — re-invoking silently.") before re-issuing the write, instead of producing zero visible tokens.

### Expected Behavior (Correct)

What should happen instead: no stale or unwanted `write-policy-gate`-related output reaches the bootcamper.

2.1 WHEN the agent presents the onboarding preamble THEN the system SHALL NOT display the stale "Rejected/Accepted" reassurance note — the note SHALL be removed (or revised to match current behavior) so onboarding contains no description of an intercept-then-retry write cycle that no longer occurs.

2.2 WHEN the `write-policy-gate` PreToolUse hook intercepts a write to a routine power-managed internal file and all INTERNAL-FILE PASS-THROUGH NOT-guards hold THEN the agent SHALL produce zero visible tokens and re-invoke the write silently, emitting no narration line.

### Unchanged Behavior (Regression Prevention)

Existing behavior that must be preserved:

3.1 WHEN a write contains Senzing SQL, a compound or ambiguous `config/.question_pending` question, a feedback-file overwrite or in-place modification, an external path, or a root-blocked placement THEN the `write-policy-gate` SHALL CONTINUE TO block the write and produce its documented visible corrective output.

3.2 WHEN a write targets `config/.question_pending` (a non-internal-file path where a NOT-guard fails) THEN the `write-policy-gate` SHALL CONTINUE TO fall through and apply single-question validation as documented.

3.3 WHEN the `write-policy-gate` PreToolUse hook evaluates any write THEN the system SHALL CONTINUE TO use the existing `preToolUse` trigger and write-type `toolTypes` (`fs_write|str_replace|fs_append`), with the gate's security behavior and INTERNAL-FILE PASS-THROUGH set unchanged.

3.4 WHEN the agent presents onboarding content other than the "Rejected/Accepted" note (setup preamble, MCP health check, version display, directory structure, team detection, prerequisite checks) THEN the system SHALL CONTINUE TO present that content unchanged.

---

### Bug Condition

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type WriteGateOutputEvent
         (kind, onboarding_text, note_present, is_passthrough,
          target_path, not_guards_hold, emitted_tokens)
  OUTPUT: boolean

  // Defect 1: stale onboarding "Rejected/Accepted" reassurance note is shown
  staleOnboardingNote ←
        X.kind = "onboarding_preamble"
    AND X.note_present = TRUE   // describes intercept-then-retry that no longer occurs

  // Defect 2: agent narrates instead of staying silent on internal-file pass-through
  narratedSilentReinvoke ←
        X.kind = "write_gate_passthrough"
    AND X.is_passthrough = TRUE
    AND X.target_path IS a routine power-managed internal file
    AND X.not_guards_hold = TRUE
    AND X.emitted_tokens != EMPTY

  // Bootcamper sees stale/unwanted write-gate-related output
  RETURN staleOnboardingNote OR narratedSilentReinvoke
END FUNCTION
```

### Fix Checking Property

```pascal
// Property: Fix Checking — no stale/unwanted write-gate-related output reaches the bootcamper
FOR ALL X WHERE isBugCondition(X) DO
  result ← F'(X)

  IF X.kind = "onboarding_preamble" THEN
    // The stale note is gone (or revised to match current behavior)
    ASSERT result.note_present = FALSE
  ELSE IF X.kind = "write_gate_passthrough" THEN
    // Internal-file pass-through emits zero visible tokens
    ASSERT result.emitted_tokens = EMPTY
    ASSERT result.write_operation_proceeds = TRUE
  END IF
END FOR
```

### Preservation Property

```pascal
// Property: Preservation Checking — everything else behaves identically to before the fix
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
//
// In particular this preserves:
//   - legitimate write-gate rejections (Senzing SQL, compound .question_pending
//     questions, feedback append-only guard, external paths, root placement) still
//     produce their documented visible corrective output;
//   - non-internal-file question validation on config/.question_pending is unchanged;
//   - the preToolUse trigger and write-type toolTypes of the gate are unchanged;
//   - all other onboarding content is presented unchanged.
```
