# Bugfix Requirements Document

## Introduction

When using SDK methods like `how_entity`, `why_record_in_entity`, `get_entity`, and `search_by_attributes`, the agent never explains or considers the flags that control the level of detail in the response. Flags such as `SZ_INCLUDE_FEATURE_SCORES`, `SZ_INCLUDE_MATCH_KEY_DETAILS`, and `SZ_HOW_ENTITY_DEFAULT_FLAGS` determine what data comes back from the SDK. The agent passes `None` (default flags) without discussing the implications, missing a core teaching opportunity about the flag system and potentially returning insufficient or excessive data for the bootcamper's actual needs.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent selects an SDK method that accepts flags (e.g., `how_entity`, `why_record_in_entity`, `get_entity`, `search_by_attributes`) THEN the agent passes `None` or default flags without looking up available flags via `get_sdk_reference(topic='flags', filter='<method_name>')`

1.2 WHEN the agent uses an SDK method with flags THEN the agent does not explain to the bootcamper which flags are being used or why, missing the teaching opportunity about the flag system

1.3 WHEN the bootcamper's request implies a specific level of detail (e.g., "show me the scoring details" or "give me a high-level overview") THEN the agent does not match flag selection to the bootcamper's intent, using default flags regardless of what information is actually needed

1.4 WHEN the agent uses `how_entity` without `SZ_INCLUDE_MATCH_KEY_DETAILS` or `SZ_INCLUDE_FEATURE_SCORES` THEN the response lacks the detailed scoring information that would make visualizations and explanations much more informative

### Expected Behavior (Correct)

2.1 WHEN the agent selects an SDK method that accepts flags THEN the agent SHALL look up available flags for that method via `get_sdk_reference` to understand what detail levels are available before choosing which flags to pass

2.2 WHEN the agent uses an SDK method with flags THEN the agent SHALL explain the flag choices to the bootcamper (e.g., "I'm using `SZ_INCLUDE_FEATURE_SCORES` so we can see the confidence scores for each feature comparison")

2.3 WHEN the bootcamper's request implies a specific level of detail THEN the agent SHALL match flag selection to the bootcamper's intent — default flags for high-level overviews, feature score flags for detailed scoring, match key detail flags for match key breakdowns

2.4 WHEN the agent uses `how_entity` or `why_record_in_entity` for visualization or detailed explanation purposes THEN the agent SHALL include `SZ_INCLUDE_FEATURE_SCORES` and/or `SZ_INCLUDE_MATCH_KEY_DETAILS` to provide the scoring information needed for informative output

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the bootcamper explicitly specifies which flags to use (e.g., "use default flags" or "just use SZ_HOW_ENTITY_DEFAULT_FLAGS") THEN the agent SHALL CONTINUE TO respect the bootcamper's explicit flag choice without overriding it

3.2 WHEN the agent calls `get_sdk_reference` for method signatures (not flag lookup) THEN the agent SHALL CONTINUE TO use it in the same way as before — this fix adds a flag-lookup step, not changes to existing signature lookups

3.3 WHEN the agent has already looked up and explained flags for a method within the current module session THEN the agent SHALL CONTINUE TO reuse that knowledge without re-querying `get_sdk_reference` for the same method's flags

3.4 WHEN the bootcamper's request is a simple entity lookup where default flags are appropriate and no special detail is needed THEN the agent SHALL CONTINUE TO use default flags but SHALL now briefly note that defaults are being used and that more detailed flags are available if needed
