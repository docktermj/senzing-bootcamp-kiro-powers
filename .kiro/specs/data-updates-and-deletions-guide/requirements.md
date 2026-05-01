# Requirements Document

## Introduction

The bootcamp teaches record loading in Module 6 — add data sources, process redo records, validate entity resolution results. But real-world data is not static. Customers move, phone numbers change, businesses close, and records get removed from source systems. Bootcampers finishing Module 6 have no guidance on what happens when source data changes after initial loading: how to update an existing record, how to delete a record that no longer exists in the source, how entity resolution re-evaluates after those changes, or what redo processing implications arise from updates and deletions.

This feature adds a dedicated guide at `docs/guides/DATA_UPDATES_AND_DELETIONS.md` covering record updates and deletions in Senzing: replacing records when source data changes, deleting records when they are removed from source systems, understanding how entity resolution re-evaluates after each operation, and the redo processing implications of both. The guide uses `generate_scaffold` and `get_sdk_reference` for code examples and SDK method signatures. Module 6 references the guide as advanced reading after the main loading workflow.

## Glossary

- **Data_Updates_Guide**: The Markdown document at `docs/guides/DATA_UPDATES_AND_DELETIONS.md` that explains how to update and delete records in Senzing and the entity resolution implications of each operation.
- **Record_Update**: The process of replacing an existing record in Senzing by loading a new version with the same DATA_SOURCE and RECORD_ID combination, causing Senzing to replace the old record data with the new data.
- **Record_Deletion**: The process of removing a record from Senzing by specifying its DATA_SOURCE and RECORD_ID, causing Senzing to remove the record and re-evaluate any entities that included it.
- **Redo_Record**: A record that Senzing flags for reprocessing when data changes (adds, updates, or deletes) affect how previously loaded records should resolve. Redo records must be processed to keep entity resolution results current.
- **Entity_Re-evaluation**: The process by which Senzing recalculates entity composition after a record is updated or deleted, potentially splitting, merging, or restructuring entities.
- **Module_6_Steering**: The steering file at `senzing-bootcamp/steering/module-06-load-data.md` that defines the Module 6 workflow for loading data.
- **Guide_Directory**: The directory at `senzing-bootcamp/docs/guides/` containing user-facing reference documentation for the bootcamp.
- **Guides_README**: The file at `senzing-bootcamp/docs/guides/README.md` that indexes all available guides with descriptions and links.

## Requirements

### Requirement 1: Data Updates and Deletions Guide Creation

**User Story:** As a bootcamper, I want a dedicated guide on updating and deleting records in Senzing, so that I understand how to handle source data changes after initial loading.

#### Acceptance Criteria for Requirement 1

1. THE Data_Updates_Guide SHALL be located at `docs/guides/DATA_UPDATES_AND_DELETIONS.md`
2. THE Data_Updates_Guide SHALL open with an introduction explaining why record updates and deletions matter in production entity resolution systems where source data changes over time
3. THE Data_Updates_Guide SHALL use a level-1 heading with the guide title, followed by an introductory paragraph, consistent with the heading and layout conventions in the Guide_Directory

### Requirement 2: Record Updates

**User Story:** As a bootcamper, I want to understand how to update existing records when source data changes, so that I can keep entity resolution accurate when a customer moves, changes their name, or corrects their information.

#### Acceptance Criteria for Requirement 2

1. THE Data_Updates_Guide SHALL include a section explaining how to update an existing record in Senzing by loading a replacement record with the same DATA_SOURCE and RECORD_ID
2. THE Data_Updates_Guide SHALL explain that Senzing treats a Record_Update as a replace operation: the old record data is fully replaced by the new record data, not merged with it
3. THE Data_Updates_Guide SHALL explain what happens to entity resolution after a Record_Update: Senzing re-evaluates the updated record against all other records, which may cause entities to merge, split, or change composition
4. THE Data_Updates_Guide SHALL include a concrete scenario illustrating a Record_Update, such as a customer changing their address, showing the before and after record data
5. THE Data_Updates_Guide SHALL include a code example for updating a record, generated using `generate_scaffold` with the appropriate workflow in the bootcamper's chosen language

### Requirement 3: Record Deletions

**User Story:** As a bootcamper, I want to understand how to delete records when they are removed from source systems, so that stale records do not pollute entity resolution results.

#### Acceptance Criteria for Requirement 3

1. THE Data_Updates_Guide SHALL include a section explaining how to delete a record from Senzing by specifying its DATA_SOURCE and RECORD_ID
2. THE Data_Updates_Guide SHALL explain what happens to entity resolution after a Record_Deletion: Senzing removes the record from its entity and re-evaluates the remaining records, which may cause an entity to shrink, split into multiple entities, or be removed entirely if it contained only that record
3. THE Data_Updates_Guide SHALL include a concrete scenario illustrating a Record_Deletion, such as a customer account being closed in the source system, showing the entity composition before and after deletion
4. THE Data_Updates_Guide SHALL include a code example for deleting a record, generated using `generate_scaffold` or `get_sdk_reference` for the delete method signature in the bootcamper's chosen language

### Requirement 4: Entity Re-evaluation After Changes

**User Story:** As a bootcamper, I want to understand how Senzing re-evaluates entities after updates and deletions, so that I can predict and verify the impact of data changes on my resolved entities.

#### Acceptance Criteria for Requirement 4

1. THE Data_Updates_Guide SHALL include a section explaining Entity_Re-evaluation: how Senzing automatically recalculates entity composition when records are updated or deleted
2. THE Data_Updates_Guide SHALL explain the difference between re-evaluation triggered by a Record_Update versus a Record_Deletion: updates may shift which entity a record belongs to, while deletions may cause entities to split or disappear
3. THE Data_Updates_Guide SHALL explain how to verify entity changes after an update or deletion, such as querying the affected entity to confirm the new composition
4. THE Data_Updates_Guide SHALL include a code example for querying an entity after a change to verify the re-evaluation result, using `generate_scaffold` or `get_sdk_reference` for the appropriate query method

### Requirement 5: Redo Processing Implications

**User Story:** As a bootcamper, I want to understand how redo processing relates to record updates and deletions, so that I can ensure entity resolution remains fully accurate after data changes.

#### Acceptance Criteria for Requirement 5

1. THE Data_Updates_Guide SHALL include a section explaining why updates and deletions generate Redo_Records and why processing them is necessary for complete entity resolution accuracy
2. THE Data_Updates_Guide SHALL explain that a single Record_Update or Record_Deletion can generate multiple Redo_Records affecting other records that shared an entity with the changed record
3. THE Data_Updates_Guide SHALL describe the recommended pattern for processing redo records after a batch of updates or deletions: check the redo queue, process all pending redo records, and verify the queue is drained
4. THE Data_Updates_Guide SHALL include a code example for checking and processing the redo queue after updates or deletions, generated using `generate_scaffold` with the redo processing workflow

### Requirement 6: MCP Tool Usage for Authoritative Content

**User Story:** As a bootcamper, I want the guide to use authoritative Senzing content, so that the examples and explanations reflect current SDK behavior.

#### Acceptance Criteria for Requirement 6

1. WHEN generating code examples for the Data_Updates_Guide, THE guide author SHALL use `generate_scaffold` from the Senzing MCP server to produce SDK code rather than hand-writing Senzing API calls
2. WHEN documenting SDK method signatures for update and delete operations, THE guide author SHALL use `get_sdk_reference` to retrieve current method signatures rather than relying on training data
3. WHEN explaining Senzing concepts such as entity re-evaluation or redo processing, THE guide author SHALL use `search_docs` to retrieve current documentation rather than relying on training data
4. THE Data_Updates_Guide SHALL include a "Further Reading" section that directs bootcampers to use `search_docs` and `get_sdk_reference` for the latest guidance on record management

### Requirement 7: Module 6 Cross-Reference

**User Story:** As a bootcamper finishing Module 6, I want to be pointed toward the data updates and deletions guide, so that I know where to learn about handling source data changes after completing the loading workflow.

#### Acceptance Criteria for Requirement 7

1. THE Module_6_Steering SHALL include a reference to the Data_Updates_Guide as advanced reading, placed after the Phase D validation section
2. WHEN referencing the Data_Updates_Guide from Module_6_Steering, THE reference SHALL describe the guide as covering record updates, deletions, entity re-evaluation, and redo processing implications for production systems where source data changes
3. THE reference in Module_6_Steering SHALL not add the Data_Updates_Guide as a required step — it SHALL be presented as optional advanced reading for bootcampers interested in managing data changes after initial loading

### Requirement 8: Guides README Integration

**User Story:** As a bootcamper, I want the data updates and deletions guide listed in the guides README, so that I can discover it from the central documentation index.

#### Acceptance Criteria for Requirement 8

1. WHEN the Data_Updates_Guide is created, THE Guides_README SHALL include an entry for `DATA_UPDATES_AND_DELETIONS.md` in the appropriate section
2. WHEN listing the Data_Updates_Guide in the Guides_README, THE entry SHALL include the filename as a Markdown link, a bold title, and a description covering record updates, record deletions, entity re-evaluation, and redo processing implications
3. THE Guides_README SHALL list `DATA_UPDATES_AND_DELETIONS.md` in the Documentation Structure tree under the `guides/` directory

### Requirement 9: Practical Focus and SDK Consistency

**User Story:** As a bootcamper, I want the guide to build on the SDK patterns I already learned in Module 6, so that I can apply update and deletion patterns without learning a new toolset.

#### Acceptance Criteria for Requirement 9

1. THE Data_Updates_Guide SHALL use the same SDK functions and patterns taught in Module 6 (e.g., `add_record` for updates, redo processing functions) rather than introducing new APIs the bootcamper has not encountered
2. THE Data_Updates_Guide SHALL reference the bootcamper's existing loading program from Module 6 as the starting point, explaining what modifications or additions are needed to support updates and deletions
3. THE Data_Updates_Guide SHALL avoid recommending third-party tools or libraries beyond what the bootcamp has already introduced, keeping the focus on patterns implementable with the Senzing SDK
4. IF the Data_Updates_Guide includes patterns for detecting source data changes (such as change data capture or file diffing), THEN THE Data_Updates_Guide SHALL present them as conceptual approaches with pseudocode rather than requiring specific frameworks
