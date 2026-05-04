# Tasks

## Task 1: Add "How Senzing Matches Records" section to Module 3 steering

- [x] 1.1 Add MCP `search_docs` agent instructions before the new section in Phase 2, directing the agent to retrieve authoritative content about Senzing feature types and matching behavior, and about confidence scoring and match levels
- [x] 1.2 Insert the "How Senzing Matches Records" sub-section between step 3 (Display results) and step 4 (Explain results) in Phase 2, structured as agent instructions covering: features explanation, confidence scores explanation, and cross-source connections explanation
- [x] 1.3 Add MCP fallback guidance so the agent presents the explanation using static steering guidance and notifies the bootcamper when the MCP server is unavailable
- [x] 1.4 Ensure the new section instructs the agent to reference the bootcamper's actual demo results (specific entities, match keys, scores) rather than only hypothetical examples
- [x] 1.5 Ensure the new section does not hardcode specific score thresholds, feature matching algorithms, or version-specific scoring behavior

## Task 2: Add matching concepts back-reference to Module 7 steering

- [x] 2.1 Insert a brief matching concepts reminder in step 3 (Run exploratory queries) of Module 7, before the visualization offers, covering features, confidence scores, and cross-source connections
- [x] 2.2 Include an instruction for the agent to adapt the reminder to the bootcamper's own data context rather than referring back to Module 3 sample data
- [x] 2.3 Include an instruction directing the bootcamper to ask the agent for a refresher on matching concepts if they need more detail

## Task 3: Add glossary entries

- [x] 3.1 Add a "Confidence score" definition to `senzing-bootcamp/docs/guides/GLOSSARY.md` explaining it as a numeric indicator of match strength based on the features that agree between records
- [x] 3.2 Verify the existing "Cross-source match" definition is consistent with the new Matching Explanation Section content
- [x] 3.3 Verify the existing "Match key" definition is consistent with the new Matching Explanation Section content
- [x] 3.4 Verify the existing "Match level" definition is consistent with the new Matching Explanation Section content
- [x] 3.5 Ensure all glossary entries maintain alphabetical ordering

## Task 4: Update steering index token counts

- [x] 4.1 Run `measure_steering.py` to calculate new token counts for `module-03-quick-demo.md` and `module-07-query-validation.md`
- [x] 4.2 Update `steering-index.yaml` with the new token counts and size categories

## Task 5: Validate all changes

- [x] 5.1 Run `validate_commonmark.py` and confirm all modified markdown files pass without errors
- [x] 5.2 Run `validate_power.py` and confirm the power structure is valid
- [x] 5.3 Run `measure_steering.py --check` and confirm token counts match
