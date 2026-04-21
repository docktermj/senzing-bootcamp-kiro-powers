# Bugfix Requirements Document

## Introduction

Three related UX bugs in the Senzing Bootcamp Power's steering files degrade the bootcamp experience. After Module 1 completes, the agent skips the visualization/exploration prompt that the module-01-quick-demo.md steering file describes. Additionally, individual module starts lack the bold, prominent announcement banners that the onboarding flow uses for the welcome message, making module transitions feel flat. Finally, the journey map shown at module start (per module-transitions.md) is not enforced as a tabular format, resulting in inconsistent and less scannable progress displays.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN Module 1 completes and the agent follows the module-completion.md workflow THEN the system skips the visualization offer ("Would you like me to create a web page showing these results?") and the exploration options described in module-01-quick-demo.md Phase 2 Step 4, jumping straight to the journal/reflection/next-step flow without surfacing the visualization and deeper-exploration prompts

1.2 WHEN Module 1 completes and the agent presents next-step options from module-completion.md THEN the "Explore" option ("Would you like to dig deeper into what we just did?") does not explicitly mention visualization or interactive result exploration as concrete choices, making it too vague for the user to know these are available

1.3 WHEN any module begins (e.g., Module 2, Module 3, etc.) THEN the system presents the module name and description in plain text without a prominent visual banner, unlike the bold welcome banner used during onboarding

1.4 WHEN any module begins and the agent shows the journey map per module-transitions.md THEN the system renders the journey map in a freeform text format (e.g., bullet list or inline text) rather than a structured table with Module number, Name, and Status columns

### Expected Behavior (Correct)

2.1 WHEN Module 1 completes THEN the system SHALL offer visualization before entering the module-completion.md workflow, asking "Would you like me to create a web page showing these results?" and presenting interactive feature options (how-entity explanations, why-match analysis, attribute search, path finding, or static summary) as described in module-01-quick-demo.md Phase 2 Step 4

2.2 WHEN Module 1 completes and the agent presents next-step options from module-completion.md THEN the "Explore" option SHALL explicitly mention visualization and interactive result exploration (e.g., "Would you like to explore the results further — visualize entities, examine match explanations, or search by attributes?")

2.3 WHEN any module begins THEN the system SHALL display a prominent visual banner in the same style as the onboarding welcome banner, using the format:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀🚀🚀  MODULE N: [MODULE NAME IN CAPS]  🚀🚀🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

2.4 WHEN any module begins and the agent shows the journey map THEN the system SHALL render it as a markdown table with columns for Module number, Name, and Status, using ✅ for completed modules, 🔄 (with → prefix on the module number) for the current module, and ⬜ for upcoming modules

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the onboarding flow runs THEN the system SHALL CONTINUE TO display the existing welcome banner in its current format with 🎓 emojis and "WELCOME TO THE SENZING BOOTCAMP!" text

3.2 WHEN any module completes THEN the system SHALL CONTINUE TO follow the module-completion.md workflow for journal entries, reflection questions, and next-step options

3.3 WHEN step-level progress is communicated within a module THEN the system SHALL CONTINUE TO show Before/During/After status updates as specified in module-transitions.md

3.4 WHEN Module 1 completes and transitions to Module 2 THEN the system SHALL CONTINUE TO close Module 1 explicitly, state its purpose, and then introduce Module 2 with use-case discovery questions as specified in module-01-quick-demo.md Phase 2 Steps 5-6

3.5 WHEN modules other than Module 1 complete THEN the system SHALL CONTINUE TO present the standard next-step options (Proceed, Iterate, Explore, Share) without Module-1-specific visualization prompts


---

## Bug Condition Derivation

### Bug 1: Missing Post-Module 1 Visualization Prompt

```pascal
FUNCTION isBugCondition_Viz(X)
  INPUT: X of type ModuleCompletionEvent
  OUTPUT: boolean

  // Bug triggers when Module 1 completes and the agent transitions
  // to module-completion.md without first offering visualization
  RETURN X.module = 1 AND X.phase = "completion"
END FUNCTION

// Property: Fix Checking - Visualization Offer
FOR ALL X WHERE isBugCondition_Viz(X) DO
  result ← handleModuleCompletion'(X)
  ASSERT result.offeredVisualization = true
    AND result.visualizationPromptBeforeJournal = true
END FOR

// Property: Preservation Checking
FOR ALL X WHERE NOT isBugCondition_Viz(X) DO
  ASSERT handleModuleCompletion(X) = handleModuleCompletion'(X)
END FOR
```

### Bug 2: Missing Bold Module Announcements

```pascal
FUNCTION isBugCondition_Banner(X)
  INPUT: X of type ModuleStartEvent
  OUTPUT: boolean

  // Bug triggers when any module starts (module transitions)
  // The onboarding welcome banner is NOT affected (separate flow)
  RETURN X.event = "module_start"
END FUNCTION

// Property: Fix Checking - Bold Banner Display
FOR ALL X WHERE isBugCondition_Banner(X) DO
  result ← displayModuleStart'(X)
  ASSERT result.hasBoldBanner = true
    AND result.bannerFormat MATCHES "━━━.*🚀🚀🚀.*MODULE.*🚀🚀🚀.*━━━"
END FOR

// Property: Preservation Checking
FOR ALL X WHERE NOT isBugCondition_Banner(X) DO
  ASSERT displayModuleStart(X) = displayModuleStart'(X)
END FOR
```

### Bug 3: Journey Map Not in Tabular Format

```pascal
FUNCTION isBugCondition_Table(X)
  INPUT: X of type ModuleStartEvent
  OUTPUT: boolean

  // Bug triggers when the journey map is displayed at module start
  RETURN X.event = "module_start" AND X.showsJourneyMap = true
END FUNCTION

// Property: Fix Checking - Tabular Journey Map
FOR ALL X WHERE isBugCondition_Table(X) DO
  result ← renderJourneyMap'(X)
  ASSERT result.format = "markdown_table"
    AND result.columns = ["Module", "Name", "Status"]
    AND result.statusIcons CONTAINS {"completed": "✅", "current": "🔄", "upcoming": "⬜"}
    AND result.currentModulePrefix = "→"
END FOR

// Property: Preservation Checking
FOR ALL X WHERE NOT isBugCondition_Table(X) DO
  ASSERT renderJourneyMap(X).content = renderJourneyMap'(X).content
END FOR
```
