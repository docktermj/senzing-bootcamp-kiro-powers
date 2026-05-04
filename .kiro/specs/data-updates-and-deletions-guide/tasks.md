# Tasks

## Task 1: Create the Data Updates and Deletions Guide

- [x] 1.1 Create `senzing-bootcamp/docs/guides/DATA_UPDATES_AND_DELETIONS.md` with a level-1 heading and introductory paragraph explaining why record updates and deletions matter in production entity resolution systems where source data changes over time
- [x] 1.2 Add the "Updating Records" section explaining replace semantics (same DATA_SOURCE + RECORD_ID replaces old data), a concrete scenario (e.g., customer address change with before/after record data), entity re-evaluation impact, and an agent instruction block to call `generate_scaffold` for the update code example
- [x] 1.3 Add the "Deleting Records" section explaining deletion by DATA_SOURCE + RECORD_ID, entity impact (shrink, split, or removal), a concrete scenario (e.g., account closure with before/after entity composition), and an agent instruction block to call `get_sdk_reference` for the delete method signature
- [x] 1.4 Add the "Entity Re-evaluation After Changes" section explaining automatic re-evaluation, the difference between update-triggered and deletion-triggered re-evaluation, how to verify entity changes, and an agent instruction block to call `generate_scaffold` or `get_sdk_reference` for the query method
- [x] 1.5 Add the "Redo Processing Implications" section explaining why updates and deletions generate redo records, cascading redo effects, the recommended check-process-drain pattern, and an agent instruction block to call `generate_scaffold` with the redo processing workflow
- [x] 1.6 Add the "Further Reading" section directing bootcampers to use `search_docs` and `get_sdk_reference` for the latest guidance on record management

## Task 2: Add Module 6 Cross-Reference

- [x] 2.1 Add an "Advanced Reading" section to `senzing-bootcamp/steering/module-06-load-data.md` after the Phase Sub-Files section, referencing `docs/guides/DATA_UPDATES_AND_DELETIONS.md` as optional advanced reading covering record updates, deletions, entity re-evaluation, and redo processing implications

## Task 3: Update Guides README

- [x] 3.1 Add an entry for `DATA_UPDATES_AND_DELETIONS.md` in the "Reference Documentation" section of `senzing-bootcamp/docs/guides/README.md` with a bold Markdown link, title, and description covering record updates, deletions, entity re-evaluation, and redo processing
- [x] 3.2 Add `DATA_UPDATES_AND_DELETIONS.md` to the Documentation Structure tree in `senzing-bootcamp/docs/guides/README.md` under the `guides/` directory listing
