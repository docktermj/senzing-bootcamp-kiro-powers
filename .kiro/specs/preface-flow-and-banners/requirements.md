# Requirements Document

## Introduction

A verification of the Senzing Bootcamp power against its stated outcomes found three false items in the guided experience, all concerning presentation and sequence:

1. **No "ENTITY RESOLUTION CONCEPTS" banner.** The entity-resolution introduction (`steering/entity-resolution-intro.md`) is presented under a plain heading ("What Is Entity Resolution?") with no visually prominent banner, unlike the welcome banner and per-module banners.
2. **No "GRADUATION" banner.** The track-completion / graduation flow uses a `🎓` emoji, a certificate, an offer, and a report, but never presents a prominent "GRADUATION" banner comparable to the welcome and module-start banners.
3. **Preface order is wrong.** Programming-language selection is presented *before* the welcome banner (`onboarding-phase1b-intro-language.md` Step 4), and track selection is presented *last* (after the welcome banner, overview, verbosity, and comprehension check). The intended order is: welcome banner → overview → detail level → **track → language** → any questions.

This feature makes the preface follow the intended sequence, adds the two missing banners, and standardizes all three onboarding/graduation banners on the existing bordered-text-with-emoji pattern established by `module-transitions.md`.

## Glossary

- **Banner_Block**: A plain-text block of exactly three lines — a top border line, an emoji-decorated centered title line, and a bottom border line — using the box-drawing character `━` for borders, matching the pattern in `steering/module-transitions.md`.
- **ER_Concepts_Banner**: The Banner_Block whose title line reads `ENTITY RESOLUTION CONCEPTS`, presented at the start of the entity-resolution introduction.
- **Graduation_Banner**: The Banner_Block whose title line reads `GRADUATION`, presented at the start of the graduation / track-completion celebration.
- **Welcome_Banner**: The existing Banner_Block (`WELCOME TO THE SENZING BOOTCAMP!`) defined in `steering/onboarding-phase1b-intro-language.md`.
- **Preface**: The onboarding sequence the bootcamper experiences before Module 1 begins, spanning `steering/onboarding-flow.md`, `steering/onboarding-phase1b-intro-language.md`, and `steering/onboarding-phase2-track-setup.md`.
- **ER_Introduction**: The entity-resolution introduction content in `steering/entity-resolution-intro.md`, presented as Step 3 of the Preface, including its mandatory exploration gate.
- **Language_Selection**: The Preface step where the bootcamper chooses a programming language, currently Step 4 of `onboarding-phase1b-intro-language.md`.
- **Track_Selection**: The Preface step where the bootcamper chooses a track (Core / Advanced), currently Step 5 of `onboarding-phase2-track-setup.md`.
- **Detail_Level_Step**: The verbosity-preference step (currently Step 5a) where the bootcamper picks a verbosity preset.
- **Any_Questions_Step**: The comprehension check (currently Step 5b) that invites the bootcamper to raise questions before Module 1.
- **Advanced_Knowledge_Check**: The Advanced-track-only gut-check (currently Step 5c) presented just before Module 1.

## Requirements

### Requirement 1: Present an ENTITY RESOLUTION CONCEPTS Banner

**User Story:** As a bootcamper, I want a prominent "ENTITY RESOLUTION CONCEPTS" banner when the entity-resolution introduction begins, so that the concepts phase is as clearly signposted as the welcome and module transitions.

#### Acceptance Criteria

1. WHEN the ER_Introduction is presented, THE agent SHALL display the ER_Concepts_Banner as the first output of that step, before any descriptive prose.
2. THE ER_Concepts_Banner title line SHALL read `ENTITY RESOLUTION CONCEPTS`.
3. THE ER_Concepts_Banner SHALL follow the Banner_Block structure defined in Requirement 4.
4. THE ER_Concepts_Banner SHALL be presented exactly once per Preface run, and SHALL NOT be re-displayed when the agent answers a follow-up question and re-presents the exploration gate.

### Requirement 2: Present a GRADUATION Banner

**User Story:** As a bootcamper, I want a prominent "GRADUATION" banner when I reach the end of my track, so that graduation is as clearly celebrated and signposted as the start of the bootcamp.

#### Acceptance Criteria

1. WHEN a track-completion / graduation stopping point is reached, THE agent SHALL display the Graduation_Banner at the start of the graduation celebration output.
2. THE Graduation_Banner title line SHALL read `GRADUATION`.
3. THE Graduation_Banner SHALL follow the Banner_Block structure defined in Requirement 4.
4. THE Graduation_Banner SHALL be presented for both the graduation workflow (when accepted) and the track-completion celebration (when graduation is declined or `skip_graduation` is set), so that every bootcamper who completes a track sees it.
5. THE Graduation_Banner SHALL be presented at most once per track completion.

### Requirement 3: Reorder the Preface So Track Comes Before Language

**User Story:** As a bootcamper, I want the preface to introduce the bootcamp, then let me pick a track, then pick a programming language, so that the flow matches the documented outcome and I choose scope before I choose tooling.

#### Acceptance Criteria

1. THE Preface SHALL present its interactive steps in this order: ER_Introduction (with the exploration gate) → Welcome_Banner → bootcamp overview → Detail_Level_Step → Track_Selection → Language_Selection → Any_Questions_Step → (Advanced_Knowledge_Check when applicable) → Module 1.
2. THE Language_Selection SHALL be presented AFTER the Welcome_Banner.
3. THE Track_Selection SHALL be presented BEFORE the Language_Selection.
4. THE Any_Questions_Step SHALL be presented AFTER the Language_Selection.
5. WHEN the bootcamper is on the Advanced track, THE Advanced_Knowledge_Check SHALL be the final Preface step immediately before Module 1 begins.
6. THE ER_Introduction SHALL remain BEFORE the Welcome_Banner, so the bootcamper has domain context before any selection.
7. THE reorder SHALL preserve every existing gate semantic: Language_Selection and Track_Selection remain mandatory gates (⛔) that require the bootcamper's real input, and the ER_Introduction exploration gate is unchanged.

### Requirement 4: Banners Follow the Established Bordered Pattern

**User Story:** As a bootcamp maintainer, I want the new banners to match the existing banner style, so that the bootcamp has one consistent visual language.

#### Acceptance Criteria

1. THE Banner_Block SHALL consist of exactly three lines: a top border line, a title line, and a bottom border line.
2. THE top and bottom border lines SHALL each be 56 `━` (box-drawing heavy horizontal) characters, matching `module-transitions.md`.
3. THE title line SHALL use a three-emoji prefix and suffix group around the title text, separated from the title by two spaces on each side (e.g., `🧩🧩🧩  ENTITY RESOLUTION CONCEPTS  🧩🧩🧩`, `🎓🎓🎓  GRADUATION  🎓🎓🎓`).
4. WHEN a Banner_Block appears inside a steering file as a display template, THE Banner_Block SHALL be wrapped in a fenced code block with the `text` language identifier.
5. THE Banner_Block SHALL contain only plain text, box-drawing characters, spaces, and emoji — no markdown formatting inside the block.

### Requirement 5: Preserve Existing Preface and Graduation Behavior

**User Story:** As a bootcamp maintainer, I want the reorder and banner additions to preserve all other documented behavior, so that no workflow, persistence, or hook interaction regresses.

#### Acceptance Criteria

1. THE reorder SHALL preserve persistence of each selection to `config/bootcamp_preferences.yaml` (language, track, verbosity) exactly as before.
2. THE reorder SHALL preserve loading of the language steering file (`lang-python.md`, etc.) immediately after Language_Selection is confirmed.
3. THE reorder SHALL preserve the `ask-bootcamper` Stop-hook closing-question ownership — no inline closing questions are introduced by this change.
4. THE Graduation_Banner addition SHALL NOT alter the graduation artifact guarantees, the recap/transcript rendering order, or the mandatory closing question defined in `steering/graduation.md` and `steering/module-completion-track.md`.
5. WHEN the Preface is resumed mid-flow via session resume, THE resumed flow SHALL honor the reordered sequence.

### Requirement 6: Update Tests to Match the New Order and Banners

**User Story:** As a bootcamp maintainer, I want the existing onboarding and banner tests updated, so that the suite reflects and protects the corrected behavior.

#### Acceptance Criteria

1. THE existing onboarding sequence/ownership tests SHALL be updated to assert the reordered step sequence (Track_Selection before Language_Selection; Language_Selection after the Welcome_Banner).
2. THE test suite SHALL assert that the ER_Concepts_Banner text appears at the start of the ER_Introduction content.
3. THE test suite SHALL assert that the Graduation_Banner text appears in the graduation / track-completion flow.
4. WHEN the full test suite is run, THE suite SHALL pass with the updated assertions.
