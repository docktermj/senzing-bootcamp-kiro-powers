# Bugfix Requirements Document

## Introduction

At track selection (`senzing-bootcamp/steering/onboarding-phase2-track-setup.md`, Section
"5. Track Selection"), the agent presents this line between the track options and the mandatory
stop gate:

> Module 2 is automatically inserted before any module that needs the SDK.

This is too much detail for this stage. The bootcamper is only trying to pick a track; the
mechanics of when Module 2 gets inserted are noise at this point and add cognitive load to a
simple decision. The auto-insertion is already explained later, at the moment it actually
happens — `onboarding-flow.md` Step (SDK check) states "When Module 2 is reached (either
explicitly or auto-inserted), the module's Step 1 check will detect this and skip installation."

This bugfix removes the auto-insertion note from the track-selection prompt so the decision stays
clean, while leaving the auto-insertion behavior itself and its later explanation unchanged.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent presents track selection from `onboarding-phase2-track-setup.md` Section 5,
THE prompt includes the sentence "Module 2 is automatically inserted before any module that needs
the SDK." as a standalone line between the track options and the mandatory stop gate.

1.2 WHEN the bootcamper is choosing between Core Bootcamp and Advanced Topics, THE presence of the
Module 2 auto-insertion mechanics adds cognitive load to a decision that does not require that
detail.

### Expected Behavior (Correct)

2.1 WHEN the agent presents track selection from `onboarding-phase2-track-setup.md` Section 5,
THE prompt SHALL NOT include the "Module 2 is automatically inserted before any module that needs
the SDK." line (the standalone auto-insertion note is removed from the track-selection step).

2.2 WHEN the first SDK-dependent module is reached, THE auto-insertion of Module 2 SHALL CONTINUE
to be explained at that point (the existing `onboarding-flow.md` explanation is retained), so the
information is delivered when it is actually relevant rather than during track selection.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the bootcamp determines module sequencing, THE Module 2 auto-insertion behavior itself
(driven by `config/module-dependencies.yaml`) SHALL CONTINUE TO work exactly as before — only the
track-selection prose note is removed, not the behavior.

3.2 WHEN the agent presents track selection, THE track options (Core Bootcamp, Advanced Topics),
the "Authoritative source" note, the response-interpretation guidance, and the ⛔ mandatory stop
gate SHALL CONTINUE TO be present and unchanged.

3.3 WHEN `onboarding-flow.md` reaches the SDK check, THE existing explanation that Module 2 may be
"explicitly or auto-inserted" SHALL CONTINUE TO be present and unchanged.

3.4 WHEN any steering file, hook, script, or config other than the single removed line in
`onboarding-phase2-track-setup.md` is considered, THE content SHALL CONTINUE TO be untouched.

---

### Bug Condition

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type SteeringContent (file_path, body)
  OUTPUT: boolean

  // Returns true when the track-selection step still carries the
  // standalone Module 2 auto-insertion note
  RETURN X.file_path = "senzing-bootcamp/steering/onboarding-phase2-track-setup.md"
         AND containsLine(X.body, "Module 2 is automatically inserted before any module that needs the SDK.")
END FUNCTION
```

### Fix Checking Property

```pascal
// Property: Fix Checking — track-selection step no longer carries the note
FOR ALL X WHERE isBugCondition(X) DO
  body' ← applyFix(X.body)
  ASSERT NOT containsLine(body', "Module 2 is automatically inserted before any module that needs the SDK.")
END FOR
```

### Preservation Property

```pascal
// Property: Preservation — everything else in track setup unchanged
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT applyFix(X.body) = X.body
END FOR
// And within the edited file, the track options, authoritative-source note,
// response-interpretation guidance, and ⛔ mandatory stop gate are preserved.
```

## Reference

- Source: `SENZING_BOOTCAMP_POWER_FEEDBACK.md` — "Drop the 'Module 2 auto-inserted' note at track selection"
- Module: 0 (onboarding — track selection) | Priority: Low | Category: UX
