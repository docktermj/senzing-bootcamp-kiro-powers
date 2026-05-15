# Requirements: Entity Resolution Quality Evaluation Loop

## Overview

Add a structured quality evaluation step in Module 7 that uses `reporting_guide(topic='quality')` to help bootcampers assess whether their entity resolution results are acceptable or need mapping refinements, creating a feedback loop back to Module 5.

## Requirements

1. Add a quality evaluation step to `module-07-query-validation.md` after the initial query results are reviewed
2. The evaluation step must call `reporting_guide(topic='quality', language='<chosen_language>', version='current')` to get precision/recall/F1 guidance
3. Present quality indicators to the bootcamper: entity count vs record count ratio, possible match count, split/merge detection signals
4. Define quality thresholds: acceptable (proceed), marginal (review specific entities), poor (return to Module 5 for mapping refinement)
5. When quality is marginal or poor, provide a guided path back to Module 5 with specific recommendations (which data sources need remapping, which features are causing splits/merges)
6. The return-to-Module-5 path must preserve Module 6/7 progress so the bootcamper can reload and re-evaluate without losing work
7. Add an agent instruction block calling `reporting_guide(topic='quality')` for the evaluation methodology
8. Add an agent instruction block calling `search_docs(query='entity resolution quality evaluation', version='current')` for authoritative context
9. Update `module-transitions.md` to document the Module 7→5 feedback loop as a valid backward transition
10. Write tests verifying the quality evaluation step exists in Module 7 steering and references the reporting_guide MCP tool
