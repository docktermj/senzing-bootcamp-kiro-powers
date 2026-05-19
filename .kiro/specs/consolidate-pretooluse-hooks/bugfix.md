# Bugfix Requirements Document

## Introduction

Three separate `preToolUse` hooks (`block-direct-sql`, `enforce-single-question`, `enforce-file-path-policies`) each fire independently on every write operation, producing three visible "Ask Kiro Hook to..." interception messages plus three reasoning paragraphs (e.g., "Fast path" or "All hooks pass") per file write. This creates significant visual noise on nearly every agent turn, cluttering the bootcamp conversation and degrading the learning experience. The fix consolidates these three hooks into a single unified hook that performs all three checks in one interception, reducing visible noise from 3 messages to 1.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a write operation is triggered THEN the system displays three separate "Ask Kiro Hook to..." interception messages (one for each of the three preToolUse write hooks: block-direct-sql, enforce-single-question, enforce-file-path-policies)

1.2 WHEN a write operation passes all three hook checks (fast path) THEN the system displays three separate reasoning paragraphs (e.g., "Fast path", "All hooks pass") that are internal processing noise with no value to the bootcamper

1.3 WHEN a single config file update or routine write occurs THEN the system produces up to 6 visible items (3 interception messages + 3 reasoning outputs) before the actual content, making it harder to follow bootcamp material

### Expected Behavior (Correct)

2.1 WHEN a write operation is triggered THEN the system SHALL display only one "Ask Kiro Hook to..." interception message from a single consolidated preToolUse hook that performs all three checks (SQL blocking, single-question enforcement, file path policies)

2.2 WHEN a write operation passes all consolidated checks (fast path) THEN the system SHALL produce no visible reasoning output — the hook SHALL proceed silently without printing "Fast path", "All hooks pass", or any other internal processing text

2.3 WHEN a single config file update or routine write occurs THEN the system SHALL produce at most 1 visible interception item, reducing visual noise by approximately 83% (from 6 items to 1)

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a write operation contains direct SQL targeting the Senzing database (G2C.db, internal tables) THEN the system SHALL CONTINUE TO block the write and instruct the agent to rewrite using SDK methods via MCP tools

3.2 WHEN a write operation targets a `.question_pending` file with compound questions (multiple question marks, conjunctions joining questions, appended alternatives) THEN the system SHALL CONTINUE TO block the write and require the agent to rewrite as a single unambiguous question

3.3 WHEN a write operation targets a path outside the working directory THEN the system SHALL CONTINUE TO block the write and require project-relative equivalents

3.4 WHEN a write operation contains feedback content being routed to a file other than `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` THEN the system SHALL CONTINUE TO redirect the write to the correct feedback file

3.5 WHEN a write operation is a normal project-relative file that does not contain Senzing SQL, is not a question_pending file with compound questions, and is inside the working directory THEN the system SHALL CONTINUE TO allow the write to proceed without interference

3.6 WHEN a write operation triggers a violation in any of the three policy areas THEN the system SHALL CONTINUE TO provide the same corrective guidance (SQL rewrite instructions, question rewrite instructions, or path correction instructions) as the individual hooks currently provide
