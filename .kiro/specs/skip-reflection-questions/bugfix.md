# Bugfix Requirements Document

## Introduction

At module completion, the agent presents a "reflection question" (e.g., "which verification step gave you the most confidence?") before offering next-step options. This question originates from the `module-completion.md` steering file's "Reflection Question" section and from module-specific steering files (e.g., `module-03-system-verification.md` step 12). The reflection question adds friction at module transitions — the bootcamper wants to move forward, not engage with a pedagogical prompt that doesn't advance the project.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a module completes and the agent follows the `module-completion.md` workflow THEN the system presents a reflection question asking for the bootcamper's "main takeaway" before offering next-step options

1.2 WHEN Module 3 completes (step 12) THEN the system presents a reflection question such as "which verification step gave you the most confidence?" and blocks transition until the bootcamper responds

1.3 WHEN the agent evaluates Module 3 success criteria THEN the system requires "The bootcamper has answered the reflection question" as a completion condition

1.4 WHEN the bootcamper's takeaway field in the journal entry template is populated THEN the system waits for a reflection response (or explicit decline) before proceeding to next-step options

### Expected Behavior (Correct)

2.1 WHEN a module completes and the agent follows the `module-completion.md` workflow THEN the system SHALL skip the reflection question and proceed directly to the module completion certificate and next-step options

2.2 WHEN Module 3 completes (step 12) THEN the system SHALL transition directly to the Module 4 offer without presenting a reflection question

2.3 WHEN the agent evaluates Module 3 success criteria THEN the system SHALL NOT require a reflection question response as a completion condition

2.4 WHEN the journal entry is written THEN the system SHALL omit the "Bootcamper's takeaway" field or auto-fill it with "N/A" without prompting the bootcamper

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a module completes THEN the system SHALL CONTINUE TO append a structured journal entry to `docs/bootcamp_journal.md` containing module name, completion date, what was done, what was produced, and why it matters

3.2 WHEN a module completes THEN the system SHALL CONTINUE TO generate a module completion certificate in `docs/progress/MODULE_N_COMPLETE.md`

3.3 WHEN a module completes THEN the system SHALL CONTINUE TO present next-step options (Proceed, Iterate, Explore, Undo, Share)

3.4 WHEN the bootcamper says "yes" to the proceed option THEN the system SHALL CONTINUE TO immediately execute the next module's startup sequence with zero intermediate steps

3.5 WHEN a path is completed THEN the system SHALL CONTINUE TO present the path completion celebration, export option, graduation offer, and feedback reminder

3.6 WHEN the celebration hook fires THEN the system SHALL CONTINUE TO provide a brief celebration and next-step offer without performing journal entries or certificates
