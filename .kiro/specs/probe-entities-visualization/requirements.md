# Requirements Document

## Introduction

The Probe Entities tab in the Module 3 visualization currently displays only basic entity information (entity name, record count, data sources) when a bootcamper searches for or selects an entity. This makes it a simple lookup tool rather than an educational demonstration of how Senzing entity resolution works. This feature enhances the Probe tab to show resolution reasoning by default — including match keys, feature scores, and per-record resolution rules — so bootcampers can understand *why* records were resolved into an entity, not just *that* they were.

## Glossary

- **Probe_Tab**: The fourth tab ("Probe Entities") in the Module 3 visualization web service, providing interactive entity search and exploration
- **Search_Builder**: The Python module (`search_builder.py`) that handles search requests for the Probe tab by calling Senzing SDK methods
- **Match_Key**: A string indicating which features linked records together during entity resolution (e.g., `+NAME+DOB+PHONE` means name, date of birth, and phone matched)
- **Feature_Score**: A numeric similarity score with a classification label showing how closely two feature values matched (e.g., `NAME: 97% CLOSE`)
- **Resolution_Rule**: The named rule Senzing applied to decide that records belong to the same entity (e.g., `CNAME_CFF_CEXCL`)
- **Entity_Detail**: The full entity record returned by `get_entity_by_entity_id`, containing record-level match keys, feature scores, and resolution rules not available from `search_by_attributes` alone
- **Visualization_Server**: The Python stdlib HTTP server (`server.py`) that serves the visualization page and API endpoints on localhost:8080
- **SDK**: The Senzing SDK accessed via MCP tools, providing entity resolution operations

## Requirements

### Requirement 1: Enrich Search Results with Entity Detail

**User Story:** As a bootcamper, I want the Probe tab search results to include full resolution reasoning, so that I can understand how Senzing decided which records belong together.

#### Acceptance Criteria

1. WHEN a search returns matching entities, THE Search_Builder SHALL call `get_entity_by_entity_id` for each matched entity, up to a maximum of 10 entities, to retrieve full resolution detail
2. WHEN entity detail is retrieved, THE Search_Builder SHALL extract the entity-level match key string and per-record match keys that linked records within the entity
3. WHEN entity detail is retrieved, THE Search_Builder SHALL extract the feature scores from the search match comparison, including feature name, numeric percentage, and classification label for each scored feature
4. WHEN entity detail is retrieved, THE Search_Builder SHALL extract the per-record resolution rules that determined record membership, preserving the rule name associated with each constituent record
5. IF `get_entity_by_entity_id` raises any exception for a specific entity, THEN THE Search_Builder SHALL return the basic search result for that entity with null values for match keys, feature scores, and resolution rules, plus an `enrichment_error` field containing the exception type and message
6. IF a search returns more than 10 matching entities, THEN THE Search_Builder SHALL enrich only the first 10 entities and return the remaining entities as basic search results without resolution detail

### Requirement 2: Display Match Keys in Probe Results

**User Story:** As a bootcamper, I want to see which features linked records together, so that I can understand the evidence behind entity resolution decisions.

#### Acceptance Criteria

1. WHEN probe results are displayed, THE Probe_Tab SHALL show the entity-level match key string for each resolved entity (e.g., `+NAME+DOB+PHONE`)
2. IF a resolved entity contains multiple records, THEN THE Probe_Tab SHALL show per-record match keys indicating which features linked each record into the entity
3. IF a resolved entity contains only one record, THEN THE Probe_Tab SHALL omit the per-record match key section for that entity
4. THE Probe_Tab SHALL present each individual feature indicator within a match key (e.g., `+NAME`, `+DOB`) as a separate inline element with a visible boundary distinguishing it from adjacent indicators and surrounding text
5. IF an entity has no match key data available, THEN THE Probe_Tab SHALL display a placeholder label indicating that no match key information is available for that entity

### Requirement 3: Display Feature Scores in Probe Results

**User Story:** As a bootcamper, I want to see how closely features matched between records, so that I can understand the confidence level of each resolution decision.

#### Acceptance Criteria

1. WHEN probe results are displayed, THE Probe_Tab SHALL show feature scores for the search match comparison
2. THE Probe_Tab SHALL display each feature score as a feature name, numeric percentage, and classification label (e.g., `NAME: 97% CLOSE`)
3. WHEN multiple features were compared, THE Probe_Tab SHALL list all scored features in a structured format

### Requirement 4: Display Resolution Rules in Probe Results

**User Story:** As a bootcamper, I want to see which resolution rules Senzing applied, so that I can understand the logic that determined record membership in an entity.

#### Acceptance Criteria

1. WHEN probe results are displayed, THE Probe_Tab SHALL show the resolution rule applied to each record within the entity (e.g., `CNAME_CFF_CEXCL`)
2. WHEN an entity contains multiple records, THE Probe_Tab SHALL show the resolution rule next to each constituent record
3. THE Probe_Tab SHALL present resolution rules using a monospace or code-style format to distinguish them from natural language text

### Requirement 5: Update Search API Response Schema

**User Story:** As a developer maintaining the visualization, I want the `/api/search` endpoint to return resolution reasoning data, so that the frontend can display it without additional API calls.

#### Acceptance Criteria

1. WHEN a search result is returned, THE Visualization_Server SHALL include a `match_keys` field containing an entity-level match key string and a list of per-record match key strings, one per constituent record
2. WHEN a search result is returned, THE Visualization_Server SHALL include a `feature_scores` field containing a list of scored comparisons, where each entry provides the feature name, numeric percentage (0-100), and classification label
3. WHEN a search result is returned, THE Visualization_Server SHALL include a `resolution_rules` field containing a list of per-record entries, where each entry provides the record's data source, record ID, and the resolution rule string applied to that record
4. IF enrichment fails for an entity, THEN THE Visualization_Server SHALL include the entity in results with null values for `match_keys`, `feature_scores`, and `resolution_rules`, plus a non-empty `enrichment_error` string describing the failure
5. IF a matched entity contains only one record, THEN THE Visualization_Server SHALL return an empty list for per-record match keys and an empty list for `resolution_rules`, with the entity-level match key and `feature_scores` populated from the search comparison

### Requirement 6: Update Steering File Specification

**User Story:** As a power author, I want the Module 3 Phase 2 steering file to specify resolution reasoning in the Probe tab, so that every future bootcamper receives the enriched visualization.

#### Acceptance Criteria

1. THE Module_03_Phase2_Steering SHALL specify that the Probe_Panel displays match keys, feature scores, and resolution rules for each search result
2. THE Module_03_Phase2_Steering SHALL specify that `search_builder.py` calls `get_entity_by_entity_id` after `search_by_attributes` to retrieve full resolution detail
3. THE Module_03_Phase2_Steering SHALL specify the enriched `/api/search` response schema including `match_keys`, `feature_scores`, and `resolution_rules` fields
