# Requirements Document

## Introduction

Remove the "Quick Demo" / "System Verification" track (`quick_demo`) from the Senzing Bootcamp. The bootcamp currently offers three tracks; after this change it will offer exactly two: Core Bootcamp and Advanced Topics. Module 3 itself remains unchanged — it is already included in both remaining tracks — but the standalone verification-only track is eliminated from all definitions, onboarding flows, scripts, tests, and documentation.

## Glossary

- **Track_Registry**: The `tracks:` section in `senzing-bootcamp/config/module-dependencies.yaml` that defines available bootcamp tracks and their module lists.
- **Onboarding_Flow**: The steering file at `senzing-bootcamp/steering/onboarding-flow.md` that guides new bootcampers through setup and track selection.
- **Progress_Utils**: The utility module at `senzing-bootcamp/scripts/progress_utils.py` that defines valid track identifiers and progress data structures.
- **Track_Switcher**: The script at `senzing-bootcamp/scripts/track_switcher.py` that computes the effect of switching between tracks.
- **Validate_Dependencies**: The script at `senzing-bootcamp/scripts/validate_dependencies.py` that verifies consistency between the dependency graph and onboarding flow.
- **POWER_MD**: The `senzing-bootcamp/POWER.md` file that serves as the user-facing overview of the bootcamp power.
- **Test_Suite**: The collection of property-based and unit tests in `senzing-bootcamp/tests/` that validate track definitions and onboarding behavior.

## Requirements

### Requirement 1: Remove quick_demo from Track Registry

**User Story:** As a bootcamp maintainer, I want the `quick_demo` track removed from the dependency configuration, so that only two tracks (Core Bootcamp and Advanced Topics) are defined.

#### Acceptance Criteria

1. THE Track_Registry SHALL contain exactly two track entries: `core_bootcamp` and `advanced_topics`
2. WHEN `module-dependencies.yaml` is parsed, THE Track_Registry SHALL NOT contain a `quick_demo` key or any of its associated properties (name, description, modules, recommendation)
3. THE Track_Registry SHALL preserve all existing properties (name, description, modules, recommendation) of the `core_bootcamp` and `advanced_topics` tracks with values identical to their pre-edit state
4. WHEN `module-dependencies.yaml` is parsed after the removal, THE Track_Registry SHALL remain valid YAML and all non-track sections (metadata, modules, gates) SHALL be unchanged

### Requirement 2: Update Onboarding Flow Track Selection

**User Story:** As a bootcamper, I want the track selection step to present only Core Bootcamp and Advanced Topics, so that I am not offered a track that no longer exists.

#### Acceptance Criteria

1. WHEN Step 5 of the Onboarding_Flow is presented, THE Onboarding_Flow SHALL display exactly two track options: Core Bootcamp and Advanced Topics
2. THE Onboarding_Flow SHALL remove the "System Verification" bullet and its description from Step 5
3. THE Onboarding_Flow SHALL remove the `"verify"/"system_verification"→start at Module 2` mapping from the interpreting-responses guidance
4. THE Onboarding_Flow SHALL retain the `"core"/"core_bootcamp"→start at Module 1` and `"advanced"/"advanced_topics"→start at Module 1` response mappings

### Requirement 3: Update Progress Utilities

**User Story:** As a bootcamp maintainer, I want the valid track identifiers updated to exclude `quick_demo`, so that progress validation rejects the removed track.

#### Acceptance Criteria

1. THE Progress_Utils SHALL define valid tracks as exactly `("core_bootcamp", "advanced_topics")`
2. WHEN a progress record contains `track: "quick_demo"`, THE Progress_Utils SHALL append a validation error to the errors list indicating the track value is not among the valid tracks
3. IF a progress record contains a `track` value that is not in the valid tracks tuple, THEN THE Progress_Utils SHALL append a validation error to the errors list identifying the invalid value and listing the accepted tracks

### Requirement 4: Update Track Switcher

**User Story:** As a bootcamp maintainer, I want the track switcher to operate only on the two remaining tracks, so that switching to or from `quick_demo` is no longer possible.

#### Acceptance Criteria

1. THE Track_Switcher SHALL support switching only between `core_bootcamp` and `advanced_topics`
2. WHEN `quick_demo` is provided as a source or target track, THE Track_Switcher SHALL exit with code 1 and print an error message to stderr indicating the track name is invalid
3. IF `quick_demo` is provided as a source or target track, THEN THE Track_Switcher SHALL NOT modify the progress file
4. THE Track_Switcher SHALL NOT reference `quick_demo` in its module docstring, usage examples, or CLI help text

### Requirement 5: Update Validate Dependencies Script

**User Story:** As a bootcamp maintainer, I want the dependency validation script to expect exactly two tracks, so that CI passes after the track removal.

#### Acceptance Criteria

1. WHEN `validate_dependencies.py` parses the onboarding flow Step 5 track list, THE Validate_Dependencies SHALL expect exactly 2 track entries and report an ERROR if the count is not 2
2. WHEN `validate_dependencies.py` compares onboarding-flow.md tracks against `config/module-dependencies.yaml`, THE Validate_Dependencies SHALL validate that every track key defined in the `tracks` section of the dependency graph has a matching bullet entry in Step 5
3. IF the onboarding-flow.md contains a track name matching "Quick Demo", THEN THE Validate_Dependencies SHALL report an ERROR indicating a removed track is still referenced
4. THE Validate_Dependencies SHALL NOT include "Quick Demo" in any expected-track list, display-name mapping, or pattern used for validation

### Requirement 6: Update POWER.md and Documentation

**User Story:** As a bootcamper reading the power overview, I want to see only two track options, so that the documentation matches the actual available tracks.

#### Acceptance Criteria

1. THE POWER_MD SHALL list exactly two tracks in the "Quick Start" section under the "New users:" paragraph: Core Bootcamp and Advanced Topics
2. THE POWER_MD SHALL include Module 3 ("Quick Demo") in the Core Bootcamp track's module sequence (Modules 1, 2, 3, 4, 5, 6, 7)
3. WHEN any markdown file in the `senzing-bootcamp/` directory references available tracks by name, THE file SHALL list only Core Bootcamp and Advanced Topics as track options
4. THE POWER_MD SHALL retain Module 3 ("Quick Demo") in the Bootcamp Modules table and in the Available Steering Files module workflow list — only the standalone "Quick Demo" track bullet (Modules 2, 3) is removed from the track selection list

### Requirement 7: Update Test Suite

**User Story:** As a bootcamp maintainer, I want all tests updated to reflect two tracks, so that the test suite passes after the track removal.

#### Acceptance Criteria

1. WHEN tests validate track definitions, THE Test_Suite SHALL assert exactly two tracks exist: `core_bootcamp` and `advanced_topics`
2. WHEN tests validate onboarding flow content, THE Test_Suite SHALL NOT assert the presence of a "Quick Demo" track bullet or a "System Verification" track bullet that maps to the removed `quick_demo` track
3. WHEN tests generate random track values using Hypothesis strategies, THE Test_Suite SHALL sample only from `("core_bootcamp", "advanced_topics")`
4. WHEN a test class or test method exclusively tests `quick_demo` track switching scenarios with no assertions applicable to the remaining two tracks, THE Test_Suite SHALL remove that test class or method entirely
5. IF a test class tests `quick_demo` track switching alongside other tracks, THEN THE Test_Suite SHALL remove only the `quick_demo`-specific branches and retain assertions for `core_bootcamp` and `advanced_topics`
6. THE Test_Suite SHALL retain all tests for Module 3 content and functionality — only references to `quick_demo` as a track identifier or track-level routing through Module 3 are removed
7. WHEN tests define `TRACK_DEFINITIONS` or `_VALID_TRACK_IDS` constants, THE Test_Suite SHALL update these to contain exactly `{"core_bootcamp", "advanced_topics"}` with their corresponding module lists unchanged

### Requirement 8: Update Inline Status and Diagrams

**User Story:** As a bootcamper viewing progress or architecture diagrams, I want to see only two tracks listed, so that visual aids match the actual track options.

#### Acceptance Criteria

1. THE inline-status steering file SHALL list exactly two tracks in its "Track module lists" section: Core Bootcamp (Modules 1, 2, 3, 4, 5, 6, 7) and Advanced Topics (Modules 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11), with no Quick Demo entry
2. WHEN the module-prerequisites diagram displays its Learning Paths table, THE table SHALL contain exactly two rows: Core Bootcamp and Advanced Topics, with no Quick Demo row
3. THE module-flow diagram SHALL remove the "Quick Demo" subsection under "Learning Paths", retaining only the Core Bootcamp and Advanced Topics subsections
4. WHEN the module-prerequisites diagram mermaid graph is rendered, THE graph SHALL retain the M2 to M3 dependency edge because Module 3 remains part of both surviving tracks

### Requirement 9: Update Quick Start Guide

**User Story:** As a new bootcamper reading the quick start guide, I want the guide to reflect the current track options without referencing a removed "Quick Demo" path.

#### Acceptance Criteria

1. THE Quick_Start guide SHALL NOT contain the text "Quick Demo" as a path name, table row entry, or selectable option
2. THE Quick_Start guide SHALL present exactly two tracks by name: "Core Bootcamp" and "Advanced Topics", each listing their included module numbers matching the values defined in module-dependencies.yaml
3. WHEN a user says "Let's run the Senzing quick demo", THE Quick_Start guide SHALL map that command to Module 3 within the Core Bootcamp track and SHALL NOT reference a standalone Quick Demo path
4. THE Quick_Start guide SHALL NOT contain an "After A" section or any post-path guidance that references a Quick Demo path
