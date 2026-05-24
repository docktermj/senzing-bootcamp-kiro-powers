# Bugfix Requirements Document

## Introduction

The agent asks compound questions using "or" to join alternatives in prose form, forcing bootcampers to parse multiple options embedded in a single sentence. Despite existing rules in `conversation-protocol.md` and enforcement in the `write-policy-gate` hook for `.question_pending` writes, the agent still produces compound questions in its general conversational output. This degrades the bootcamper experience by creating ambiguous prompts where "yes" or "no" cannot map to a single clear meaning.

Example violation: "Would you like me to create a one-page executive summary you can share with your team or manager? It covers the problem, approach, data sources, and expected outcomes. Or shall we skip that and move on to Module 3 (System Verification)?"

This bug applies across all modules and all question contexts — not just those written to `.question_pending`.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent presents two or more alternatives to the bootcamper THEN the system joins them with "or" in prose form (e.g., "Would you like X, or shall we Y?")

1.2 WHEN the agent asks a question with multiple embedded options THEN the system produces a single compound sentence where "yes" cannot map to exactly one meaning

1.3 WHEN the agent offers to skip a step or choose between actions THEN the system appends the alternative after the main question using "Or" as a sentence starter (e.g., "Or shall we skip that and move on to Module 3?")

1.4 WHEN the agent asks a confirmation question THEN the system sometimes appends a follow-up alternative in the same turn (e.g., "Does that look right? Or would you like me to adjust it?")

### Expected Behavior (Correct)

2.1 WHEN the agent presents two or more alternatives to the bootcamper THEN the system SHALL format them as a numbered list preceded by a single neutral question (e.g., "👉 What would you like to do next?\n1. Create executive summary\n2. Skip and move to Module 3")

2.2 WHEN the agent asks a question with a single action THEN the system SHALL ask exactly one yes/no question with no appended alternatives (e.g., "👉 Would you like me to create a one-page executive summary for your team?")

2.3 WHEN the agent needs to offer a skip option alongside a primary action THEN the system SHALL present both as numbered choices rather than joining them with "Or" in prose

2.4 WHEN the agent asks a confirmation question THEN the system SHALL ask only the confirmation with no follow-up alternative appended — corrections are handled in the next turn if the answer is "no"

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent asks a simple yes/no question with a single clear action THEN the system SHALL CONTINUE TO present it as inline prose without a numbered list (e.g., "👉 Ready to move on to Module 3?")

3.2 WHEN the agent provides informational content without asking a question THEN the system SHALL CONTINUE TO present prose normally without restructuring into lists

3.3 WHEN the agent uses "or" within a numbered list option description THEN the system SHALL CONTINUE TO allow "or" inside list items (e.g., "1. Share with your team or manager")

3.4 WHEN the `write-policy-gate` hook validates `.question_pending` writes THEN the system SHALL CONTINUE TO enforce the existing single-question rules at write time

3.5 WHEN the agent presents a single-option confirmation (no alternatives) THEN the system SHALL CONTINUE TO use the simple "👉 [question]?" format without a numbered list
