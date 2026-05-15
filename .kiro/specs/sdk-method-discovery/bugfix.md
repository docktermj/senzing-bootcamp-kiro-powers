# Bugfix Requirements Document

## Introduction

When a bootcamper's request could map to multiple SDK methods (e.g., "explain why entity 74 resolved"), the agent immediately picks one method without first discovering all available methods in that category via `get_sdk_reference` and without asking the bootcamper which level of detail they want. This violates the existing rule "Never guess SDK method signatures — use get_sdk_reference" and misses teaching opportunities about the SDK's method taxonomy (how vs. why methods, different granularity levels).

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the bootcamper requests an SDK operation that could map to multiple methods (e.g., "explain why entity 74 resolved") THEN the agent immediately selects and uses a single SDK method without first calling `get_sdk_reference` to discover all available methods in that category

1.2 WHEN the bootcamper's request is ambiguous about which SDK method to use (e.g., the request could be answered by `how_entity`, `why_entities`, `why_records`, or `why_record_in_entity`) THEN the agent proceeds without asking a clarifying question to determine the bootcamper's intent or desired level of detail

1.3 WHEN the agent picks the wrong method due to skipping discovery THEN the bootcamper must prompt the agent multiple times to discover alternative methods, wasting time and teaching incorrect SDK usage patterns

### Expected Behavior (Correct)

2.1 WHEN the bootcamper requests an SDK operation that could map to multiple methods THEN the agent SHALL call `get_sdk_reference` (or check the relevant traits/category) to discover ALL available methods in that category BEFORE selecting one

2.2 WHEN the bootcamper's request is ambiguous about which SDK method to use (i.e., multiple discovered methods could satisfy the request) THEN the agent SHALL ask a single 👉 clarifying question presenting the available methods as a numbered choice list with brief descriptions of what each method provides

2.3 WHEN the agent discovers available methods and the bootcamper's request unambiguously maps to exactly one method THEN the agent SHALL proceed with that method without asking an unnecessary clarifying question, noting the other available methods for the bootcamper's awareness

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the bootcamper explicitly names a specific SDK method (e.g., "use how_entity on entity 74") THEN the agent SHALL CONTINUE TO use that method directly without requiring a discovery step or clarifying question

3.2 WHEN the agent has already discovered available methods for a category within the current module session THEN the agent SHALL CONTINUE TO reuse that knowledge without re-querying `get_sdk_reference` for the same category

3.3 WHEN the bootcamper's request maps to a single unambiguous SDK method with no alternatives in that category THEN the agent SHALL CONTINUE TO proceed directly without asking unnecessary clarifying questions

3.4 WHEN the agent uses `get_sdk_reference` for looking up method signatures and flags for a known method THEN the agent SHALL CONTINUE TO use it in the same way as before (this fix adds a new discovery use case, not changes to existing usage)
