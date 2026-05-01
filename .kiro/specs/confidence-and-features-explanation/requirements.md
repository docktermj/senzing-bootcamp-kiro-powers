# Requirements Document

## Introduction

Modules 3 and 7 of the bootcamp present entity resolution results that include confidence scores, match keys, and feature comparisons — but never explain what these terms mean. Bootcampers see output like `+NAME+ADDRESS+PHONE` and confidence values without understanding how to interpret them. This feature adds a "How Senzing Matches Records" section to Module 3 (the first time the bootcamper sees results) that explains features, confidence scores, and cross-source connections in the context of the demo results they just produced. Module 7 then references this explanation when presenting query results, reinforcing the concepts without repeating them. All Senzing-specific claims must come from the Senzing MCP server (`search_docs`) rather than training data. Relevant terms are added to the bootcamp glossary at `docs/guides/GLOSSARY.md`.

## Glossary

- **Module_3_Steering**: The `senzing-bootcamp/steering/module-03-quick-demo.md` steering file that guides the agent through the quick demo workflow
- **Module_7_Steering**: The `senzing-bootcamp/steering/module-07-query-validation.md` steering file that guides the agent through query and visualization workflows
- **Matching_Explanation_Section**: The new "How Senzing Matches Records" section added to Module_3_Steering, presented after the demo results
- **Feature**: A category of identifying information used during entity resolution (e.g., NAME, ADDRESS, PHONE, EMAIL, DOB, SSN), each containing one or more attributes with its own matching behavior
- **Confidence_Score**: A numeric value produced by Senzing that indicates the strength of a match between records, reflecting how much evidence supports the conclusion that records refer to the same entity
- **Match_Key**: A string like `+NAME+ADDRESS+PHONE` that shows which features contributed to a match decision between records
- **Cross_Source_Connection**: A match discovered between records originating from different data sources, indicating the same real-world entity appears in multiple systems
- **Bootcamper**: A developer working through the Senzing bootcamp
- **MCP_Server**: The Senzing MCP server at `mcp.senzing.com` that provides authoritative Senzing documentation and tools via `search_docs`
- **Steering_Index**: The `senzing-bootcamp/steering/steering-index.yaml` file that maps steering files to their metadata including token counts and step ranges
- **Glossary_File**: The `senzing-bootcamp/docs/guides/GLOSSARY.md` file containing definitions of Senzing entity resolution terms used throughout the bootcamp

## Requirements

### Requirement 1: Add a "How Senzing Matches Records" Section to Module 3

**User Story:** As a bootcamper, I want to understand how Senzing matched the demo records I just saw, so that the results are meaningful rather than opaque.

#### Acceptance Criteria

1. THE Module_3_Steering SHALL include a Matching_Explanation_Section positioned in Phase 2 after step 3 (Display results) and before step 4 (Explain results), so the bootcamper has context before the agent walks through a specific entity
2. THE Matching_Explanation_Section SHALL be presented as part of the agent's natural explanation flow, not as a separate gated step that requires bootcamper interaction to proceed
3. THE Matching_Explanation_Section SHALL cover three topics in order: what features are, what confidence scores mean, and what cross-source connections are
4. THE Matching_Explanation_Section SHALL tie its explanations to the bootcamper's actual demo results rather than presenting abstract definitions

### Requirement 2: Explain Features and How Senzing Uses Them

**User Story:** As a bootcamper, I want to understand what features are and how Senzing compares them, so that I can interpret match keys like `+NAME+ADDRESS+PHONE` in the demo output.

#### Acceptance Criteria

1. THE Matching_Explanation_Section SHALL explain that features are categories of identifying information (NAME, ADDRESS, PHONE, EMAIL, DOB, SSN) that Senzing extracts from each record and uses for comparison
2. THE Matching_Explanation_Section SHALL explain that each feature type has its own matching behavior — for example, NAME matching handles nicknames and abbreviations, while ADDRESS matching normalizes street formats
3. THE Matching_Explanation_Section SHALL explain how to read a match key string (e.g., `+NAME+ADDRESS+PHONE` means all three feature types contributed to the match decision)
4. THE Matching_Explanation_Section SHALL reference at least three feature types from the bootcamper's demo data when illustrating how features work, using the actual values from the loaded records
5. WHEN presenting feature explanations, THE Agent SHALL retrieve authoritative content about Senzing feature types from the MCP_Server using `search_docs` rather than relying on training data

### Requirement 3: Explain Confidence Scores and How to Interpret Them

**User Story:** As a bootcamper, I want to understand what confidence scores mean and how to interpret their values, so that I can assess the quality of matches in my results.

#### Acceptance Criteria

1. THE Matching_Explanation_Section SHALL explain that confidence scores reflect the strength of evidence supporting a match — higher scores indicate more features agreeing across records
2. THE Matching_Explanation_Section SHALL explain how to interpret score ranges in practical terms: which scores indicate strong matches with multiple corroborating features, which indicate moderate matches worth reviewing, and which indicate weak matches based on limited evidence
3. THE Matching_Explanation_Section SHALL use at least one concrete example from the bootcamper's demo results, showing the score alongside the features that produced it
4. THE Matching_Explanation_Section SHALL explain that scores are relative indicators of match strength rather than absolute probabilities, so bootcampers do not misinterpret them as percentage likelihoods
5. WHEN presenting confidence score explanations, THE Agent SHALL retrieve authoritative content about Senzing scoring from the MCP_Server using `search_docs` rather than relying on training data

### Requirement 4: Explain Cross-Source Connections and Their Business Value

**User Story:** As a bootcamper, I want to understand what cross-source connections are and why they matter, so that I can see the business value of entity resolution beyond simple deduplication.

#### Acceptance Criteria

1. THE Matching_Explanation_Section SHALL explain that a cross-source connection occurs when records from different data sources resolve to the same entity, revealing that the same person or organization exists in multiple systems
2. THE Matching_Explanation_Section SHALL distinguish cross-source connections from within-source deduplication, explaining that deduplication finds duplicates inside one system while cross-source matching links records across systems
3. THE Matching_Explanation_Section SHALL explain the business value of cross-source connections using at least one concrete scenario (e.g., discovering that a customer in the CRM is the same person as a support ticket contact, enabling a unified view)
4. WHEN the bootcamper's demo data contains records from multiple data sources, THE Agent SHALL point out specific cross-source connections in the demo results to illustrate the concept with real examples

### Requirement 5: Reference the Matching Explanation from Module 7

**User Story:** As a bootcamper, I want Module 7 to remind me how to interpret features, scores, and cross-source connections when I see query results, so that I can apply what I learned in Module 3 to my own data.

#### Acceptance Criteria

1. THE Module_7_Steering SHALL include a brief reference to the Matching_Explanation_Section from Module 3 when the agent presents query results in step 3 (Run exploratory queries)
2. THE Module_7_Steering reference SHALL remind the bootcamper of the key interpretation concepts (features, confidence scores, cross-source connections) without repeating the full explanation from Module 3
3. THE Module_7_Steering reference SHALL direct the bootcamper to ask the agent for a refresher on matching concepts if they need more detail
4. THE Module_7_Steering reference SHALL adapt to the bootcamper's own data context rather than referring back to the Module 3 sample data

### Requirement 6: Source All Senzing-Specific Content from the MCP Server

**User Story:** As a maintainer, I want all Senzing-specific claims about features and scoring sourced from the MCP server, so that the content stays accurate as Senzing evolves.

#### Acceptance Criteria

1. THE Module_3_Steering SHALL include an instruction for the agent to call `search_docs` from the MCP_Server to retrieve authoritative content about Senzing features and their matching behavior before presenting the Matching_Explanation_Section
2. THE Module_3_Steering SHALL include an instruction for the agent to call `search_docs` from the MCP_Server to retrieve authoritative content about Senzing confidence scoring and match levels
3. IF the MCP_Server is unavailable, THEN THE Agent SHALL present the Matching_Explanation_Section using the static guidance embedded in the steering file and note to the bootcamper that it will verify details when the server is available
4. THE Module_3_Steering SHALL NOT hardcode specific score thresholds, feature matching algorithms, or version-specific scoring behavior — these must come from the MCP_Server at runtime

### Requirement 7: Add Relevant Terms to the Bootcamp Glossary

**User Story:** As a bootcamper, I want confidence scores, match keys, and cross-source connections defined in the glossary, so that I can look up these terms when I encounter them later in the bootcamp.

#### Acceptance Criteria

1. THE Glossary_File SHALL include a definition for "Confidence score" that explains it as a numeric indicator of match strength based on the features that agree between records
2. THE Glossary_File SHALL include a definition for "Cross-source match" if one does not already exist, or THE existing definition SHALL be verified as consistent with the Matching_Explanation_Section content
3. THE Glossary_File SHALL include a definition for "Match key" if one does not already exist, or THE existing definition SHALL be verified as consistent with the Matching_Explanation_Section content
4. WHEN adding or updating glossary entries, THE entries SHALL follow the existing format and alphabetical ordering used in the Glossary_File
5. THE Glossary_File SHALL include a definition for "Match level" if one does not already exist, covering the distinction between resolved, possibly same, possibly related, and name-only match levels

### Requirement 8: Keep the Explanation Concise and Tied to Demo Results

**User Story:** As a bootcamper, I want the matching explanation to be brief and grounded in what I just saw, so that it builds understanding without interrupting the demo flow.

#### Acceptance Criteria

1. THE Matching_Explanation_Section SHALL be concise enough to present in under two minutes of reading, using short paragraphs or bullet points rather than long prose blocks
2. THE Matching_Explanation_Section SHALL reference the bootcamper's actual demo output (specific entities, match keys, and scores from the run) rather than using only hypothetical examples
3. THE Matching_Explanation_Section SHALL avoid deep technical detail about Senzing internals — the goal is practical interpretation, not algorithmic understanding
4. THE Matching_Explanation_Section SHALL use plain language and define or explain any term not already in the Glossary_File before using it
5. THE modified Module_3_Steering and Module_7_Steering SHALL pass `validate_commonmark.py` and `validate_power.py` without errors
