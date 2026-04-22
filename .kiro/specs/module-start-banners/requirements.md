# Requirements Document

## Introduction

The Senzing Bootcamp power uses visual banners to signal transitions and orient users. The onboarding flow displays a welcome banner, and the `module-transitions.md` steering file defines a module start banner template for agents to display at runtime. However, the 13 module documentation files (`MODULE_0` through `MODULE_12`) in `senzing-bootcamp/docs/modules/` currently begin with a plain markdown heading and no banner. This feature adds a consistent, visually prominent banner block to the top of every module documentation file, matching the existing bordered-text-with-emoji style established by the welcome and module-start banners.

## Glossary

- **Module_Documentation_File**: One of the 13 markdown files in `senzing-bootcamp/docs/modules/` named `MODULE_0_SDK_SETUP.md` through `MODULE_12_DEPLOYMENT_PACKAGING.md`
- **Banner_Block**: A text block consisting of a top border line, a centered emoji-decorated title line, and a bottom border line, using the box-drawing character `━` for borders
- **Module_Heading**: The existing first-line markdown heading in each Module_Documentation_File (e.g., `# Module 0: Set Up SDK`)
- **Banner_Template**: The module start banner pattern defined in `senzing-bootcamp/steering/module-transitions.md`

## Requirements

### Requirement 1: Add a Banner Block to Every Module Documentation File

**User Story:** As a bootcamp user, I want every module documentation file to begin with a visually prominent banner, so that I can immediately identify which module I am reading and feel the same guided experience established by the welcome banner.

#### Acceptance Criteria

1. THE Banner_Block SHALL appear as the very first content in each Module_Documentation_File, before the Module_Heading.
2. WHEN a Module_Documentation_File is opened, THE Banner_Block SHALL be the first visible text element a reader encounters.
3. THE Banner_Block SHALL exist in all 13 Module_Documentation_Files (MODULE_0 through MODULE_12).

### Requirement 2: Banner Block Structure Matches Established Pattern

**User Story:** As a bootcamp maintainer, I want the module banners to follow the same visual structure as the existing welcome and module-start banners, so that the bootcamp has a consistent look and feel.

#### Acceptance Criteria

1. THE Banner_Block SHALL consist of exactly three lines: a top border line, a title line, and a bottom border line.
2. THE Banner_Block top border line SHALL be a row of `━` (box-drawing heavy horizontal) characters matching the width used in the Banner_Template.
3. THE Banner_Block bottom border line SHALL be identical to the top border line.
4. THE Banner_Block title line SHALL use the 🚀 emoji as a prefix and suffix group, matching the Banner_Template style (e.g., `🚀🚀🚀  MODULE N: [TITLE IN CAPS]  🚀🚀🚀`).
5. THE Banner_Block title line SHALL contain the module number and the module name in uppercase, derived from the Module_Heading of that file.

### Requirement 3: Banner Content Matches Each Module's Identity

**User Story:** As a bootcamp user, I want each banner to display the correct module number and name, so that the banner accurately identifies the module I am viewing.

#### Acceptance Criteria

1. WHEN the Module_Heading reads `# Module N: <Title>`, THE Banner_Block title line SHALL display `MODULE N: <TITLE IN UPPERCASE>`.
2. THE Banner_Block for MODULE_0 SHALL display `MODULE 0: SET UP SDK` as the title text.
3. THE Banner_Block for MODULE_1 SHALL display `MODULE 1: QUICK DEMO` as the title text.
4. THE Banner_Block for MODULE_2 SHALL display `MODULE 2: UNDERSTAND BUSINESS PROBLEM` as the title text.
5. THE Banner_Block for MODULE_3 SHALL display `MODULE 3: DATA COLLECTION POLICY` as the title text.
6. THE Banner_Block for MODULE_4 SHALL display `MODULE 4: EVALUATE DATA QUALITY WITH AUTOMATED SCORING` as the title text.
7. THE Banner_Block for MODULE_5 SHALL display `MODULE 5: MAP YOUR DATA` as the title text.
8. THE Banner_Block for MODULE_6 SHALL display `MODULE 6: LOAD SINGLE DATA SOURCE` as the title text.
9. THE Banner_Block for MODULE_7 SHALL display `MODULE 7: MULTI-SOURCE ORCHESTRATION` as the title text.
10. THE Banner_Block for MODULE_8 SHALL display `MODULE 8: QUERY AND VALIDATE RESULTS` as the title text.
11. THE Banner_Block for MODULE_9 SHALL display `MODULE 9: PERFORMANCE TESTING AND BENCHMARKING` as the title text.
12. THE Banner_Block for MODULE_10 SHALL display `MODULE 10: SECURITY HARDENING` as the title text.
13. THE Banner_Block for MODULE_11 SHALL display `MODULE 11: MONITORING AND OBSERVABILITY` as the title text.
14. THE Banner_Block for MODULE_12 SHALL display `MODULE 12: PACKAGE AND DEPLOY` as the title text.

### Requirement 4: Preserve Existing Module Content

**User Story:** As a bootcamp maintainer, I want the banner addition to leave all existing module content intact, so that no documentation or agent workflow references are lost.

#### Acceptance Criteria

1. WHEN a Banner_Block is added, THE Module_Documentation_File SHALL retain the original Module_Heading unchanged.
2. WHEN a Banner_Block is added, THE Module_Documentation_File SHALL retain all content that followed the original Module_Heading, in the same order and without modification.
3. THE Banner_Block SHALL be separated from the Module_Heading by exactly one blank line.

### Requirement 5: Banner Uses Plain Text Format

**User Story:** As a bootcamp maintainer, I want the banners to be plain text blocks rather than markdown-rendered elements, so that they display consistently across all markdown renderers and terminal outputs.

#### Acceptance Criteria

1. THE Banner_Block SHALL be wrapped in a markdown fenced code block (triple backticks) with the `text` language identifier.
2. THE Banner_Block SHALL contain only plain text characters, box-drawing characters, and emoji — no markdown formatting syntax within the block.
