# Bugfix Requirements Document

## Introduction

The bootcamp agent may generate direct SQL queries against the Senzing SQLite database (`database/G2C.db`) when helping users explore entity resolution results. Direct SQL bypasses the Senzing SDK's abstraction layer, may produce incorrect or unsupported results, and teaches users a non-portable access pattern. All data access must go through Senzing SDK methods provided by the MCP server (e.g., `get_entity`, `get_entity_by_record_id`, `search_by_attributes`, `why_entities`, `how_entity`).

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent is asked to explore or query entity resolution results THEN the system may generate direct SQL queries (SELECT, INSERT, UPDATE, DELETE) against the Senzing SQLite database

1.2 WHEN the agent is asked to count entities, find duplicates, or retrieve statistics THEN the system may write SQL statements targeting Senzing internal tables (e.g., `RES_ENT`, `OBS_ENT`, `RES_FEAT_STAT`) rather than using SDK methods

1.3 WHEN the agent is asked to visualize or export resolved entity data THEN the system may open a direct database connection to `database/G2C.db` and execute raw SQL to extract data

### Expected Behavior (Correct)

2.1 WHEN the agent is asked to explore or query entity resolution results THEN the system SHALL use only Senzing SDK methods (via MCP tools such as `get_entity`, `get_entity_by_record_id`, `search_by_attributes`, `why_entities`, `why_records`, `how_entity`) to access data

2.2 WHEN the agent is asked to count entities, find duplicates, or retrieve statistics THEN the system SHALL use SDK methods (e.g., `get_entity_by_record_id` iterated over loaded records, or appropriate reporting/search SDK calls) rather than direct SQL

2.3 WHEN the agent is asked to visualize or export resolved entity data THEN the system SHALL retrieve data exclusively through SDK method calls and never open a direct database connection to the Senzing database

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent generates code that reads or writes non-Senzing files (CSV, JSONL, config files, user data files) THEN the system SHALL CONTINUE TO use standard file I/O operations as before

3.2 WHEN the agent generates code that uses the Senzing SDK methods through the MCP server THEN the system SHALL CONTINUE TO call those SDK methods with correct parameters and flags

3.3 WHEN the agent is asked about SQL concepts in general (not targeting the Senzing database) THEN the system SHALL CONTINUE TO provide helpful SQL guidance for non-Senzing databases or educational contexts

3.4 WHEN the agent generates scaffold code via `generate_scaffold` MCP tool THEN the system SHALL CONTINUE TO use the MCP-generated code as-is (which already uses SDK methods)
