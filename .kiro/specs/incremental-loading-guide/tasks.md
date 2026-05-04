# Implementation Plan: Incremental Loading Guide

## Overview

This plan creates a new guide at `docs/guides/INCREMENTAL_LOADING.md` covering incremental loading patterns for Senzing entity resolution, adds a cross-reference from Module 6's steering file, and updates the guides README index. All changes are pure Markdown documentation — no new scripts, no new steering workflows, no code templates. The guide uses agent instruction blocks to call MCP tools at runtime for code examples.

## Tasks

- [x] 1. Create the incremental loading guide
  - [x] 1.1 Create `senzing-bootcamp/docs/guides/INCREMENTAL_LOADING.md` with introduction and Adding New Records section
    - Start with a level-1 heading `# Incremental Loading` followed by an introductory paragraph explaining the difference between batch loading (Module 6) and incremental loading, and when each approach applies
    - Follow the heading and layout conventions from existing guides (see `DATA_UPDATES_AND_DELETIONS.md` for format reference)
    - Add an "Adding New Records" section (level-2 heading) that explains: how `add_record` with a new `RECORD_ID` adds to an existing database, deduplication behavior (same DATA_SOURCE + RECORD_ID = replace, new RECORD_ID = additive), and how to structure incremental input files (only new/changed records, not the entire source)
    - Include an agent instruction block calling `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')` for the code example
    - Include an agent instruction block calling `search_docs(query="incremental loading add records", version="current")` for authoritative context
    - Reference the bootcamper's existing Module 6 loading program as the starting point
    - Present file-watching and scheduling as conceptual approaches with pseudocode, not framework-specific implementations
    - Do not introduce third-party tools or libraries beyond what the bootcamp already uses
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 5.1, 5.2, 8.1, 8.2, 8.3, 8.4_

  - [x] 1.2 Add Redo Processing for Incremental Loads section to `INCREMENTAL_LOADING.md`
    - Add a "Redo Processing for Incremental Loads" section (level-2 heading)
    - Explain why redo records are generated after incremental loads and why processing them is necessary for accurate entity resolution
    - Explain the relationship between incremental load volume and redo queue growth (larger loads produce more redo records)
    - Describe a scheduling pattern: after each incremental load completes, check the redo queue, process all pending records, verify the queue is drained before the next load
    - Explain how to check whether the redo queue is empty
    - Include an agent instruction block calling `generate_scaffold(language='<chosen_language>', workflow='redo', version='current')` for the redo processing code example
    - Include an agent instruction block calling `search_docs(query="redo processing incremental", version="current")` for authoritative context
    - Use the same redo processing functions taught in Module 6
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 5.1, 5.2, 8.1_

  - [x] 1.3 Add Monitoring Incremental Load Health section to `INCREMENTAL_LOADING.md`
    - Add a "Monitoring Incremental Load Health" section (level-2 heading)
    - Describe at least four health indicators: records loaded per interval (throughput), error count and error rate, redo queue depth over time, entity count trend after each incremental load
    - Describe warning signs of an unhealthy pipeline: growing redo queue that never drains, declining throughput, increasing error rate, entity count not changing despite new records
    - Include an agent instruction block for a code example that queries Senzing for current entity and record counts (using `generate_scaffold` or `search_docs`)
    - Include an agent instruction block calling `find_examples(query="monitoring entity count record count", version="current")` for working code references
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3_

  - [x] 1.4 Add Further Reading section to `INCREMENTAL_LOADING.md`
    - Add a "Further Reading" section (level-2 heading)
    - Direct bootcampers to use `search_docs(query="incremental loading")` for the latest guidance
    - Direct bootcampers to use `find_examples(query="incremental loading")` for working code from indexed Senzing repositories
    - Reference `DATA_UPDATES_AND_DELETIONS.md` as a complementary guide for record update and deletion patterns
    - _Requirements: 5.4_

- [x] 2. Update Module 6 steering with cross-reference
  - [x] 2.1 Add incremental loading guide reference to the Advanced Reading section in `senzing-bootcamp/steering/module-06-load-data.md`
    - Add a new blockquote paragraph after the existing `DATA_UPDATES_AND_DELETIONS.md` reference in the Advanced Reading section
    - The reference should read: `> For production systems that receive ongoing data, see docs/guides/INCREMENTAL_LOADING.md for incremental loading patterns — adding new records to an existing database, processing redo records after incremental loads, and monitoring pipeline health over time.`
    - The reference must be presented as optional further reading, not a required step
    - Do not modify any other part of the Module 6 steering file
    - _Requirements: 6.1, 6.2, 6.3_

- [x] 3. Update guides README with index entry
  - [x] 3.1 Add `INCREMENTAL_LOADING.md` entry to the Reference Documentation section in `senzing-bootcamp/docs/guides/README.md`
    - Add the entry after the `DATA_UPDATES_AND_DELETIONS.md` entry (topically related)
    - Format: bold Markdown link `**[INCREMENTAL_LOADING.md](INCREMENTAL_LOADING.md)**` followed by a bulleted description covering incremental record loading, redo processing after incremental loads, and pipeline health monitoring
    - _Requirements: 7.1, 7.2_

  - [x] 3.2 Add `INCREMENTAL_LOADING.md` to the Documentation Structure tree in `senzing-bootcamp/docs/guides/README.md`
    - Add `│   ├── INCREMENTAL_LOADING.md` to the `guides/` directory listing in alphabetical order
    - _Requirements: 7.3_

- [x] 4. Write tests for the incremental loading guide
  - [x] 4.1 Create `senzing-bootcamp/tests/test_incremental_loading_guide.py` with guide structure tests
    - Verify `docs/guides/INCREMENTAL_LOADING.md` exists
    - Verify the file starts with a level-1 heading (`# Incremental Loading`)
    - Verify the file contains required section headings: a section on adding new records, a section on redo processing, a section on monitoring, and a "Further Reading" section
    - Verify the file contains at least three agent instruction blocks (one per code example section)
    - Verify agent instruction blocks reference MCP tools: `generate_scaffold`, `search_docs`, `find_examples`
    - _Requirements: 1.1, 1.2, 1.3, 2.4, 3.4, 4.4, 5.1, 5.2, 5.3_

  - [x] 4.2 Add content validation tests to `test_incremental_loading_guide.py`
    - Verify the introduction explains the difference between batch and incremental loading
    - Verify the adding records section mentions `DATA_SOURCE`, `RECORD_ID`, and deduplication/replace behavior
    - Verify the redo processing section mentions redo queue, scheduling, and drain verification
    - Verify the monitoring section mentions at least four health indicators (throughput, error rate, redo queue depth, entity count)
    - Verify the further reading section references `search_docs` and `find_examples`
    - Verify the guide references the Module 6 loading program as a starting point
    - Verify the guide does not introduce third-party tools or libraries (no mentions of cron, Airflow, Celery, etc. as requirements)
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 5.4, 8.1, 8.2, 8.3, 8.4_

  - [x] 4.3 Add cross-reference and README integration tests to `test_incremental_loading_guide.py`
    - Verify `steering/module-06-load-data.md` contains a reference to `INCREMENTAL_LOADING.md` in the Advanced Reading section
    - Verify the Module 6 reference describes the guide as covering incremental loading patterns for production systems
    - Verify `docs/guides/README.md` contains an entry for `INCREMENTAL_LOADING.md` in the Reference Documentation section
    - Verify the README entry includes a Markdown link to the file
    - Verify the README entry description mentions incremental loading, redo processing, and pipeline health monitoring
    - Verify `INCREMENTAL_LOADING.md` appears in the Documentation Structure tree
    - _Requirements: 6.1, 6.2, 6.3, 7.1, 7.2, 7.3_

- [x] 5. Final validation
  - [x] 5.1 Run all tests and CI checks
    - Run `pytest senzing-bootcamp/tests/test_incremental_loading_guide.py -v` to validate all new tests pass
    - Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` to validate Markdown compliance for the new guide
    - Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to validate token counts for the modified steering file
    - Verify no existing tests are broken by the changes
    - _Requirements: all_

## Notes

- This feature is pure documentation — no new Python scripts, no new steering workflows, no code templates
- Property-based testing does not apply; tests focus on structural validation and content verification
- All Senzing facts in the guide come from MCP tools at runtime (via agent instruction blocks), never from training data
- The guide follows the same conventions as `DATA_UPDATES_AND_DELETIONS.md`: prose explanations, concrete scenarios, agent instruction blocks for code examples
- The existing CI pipeline validates all new and modified files automatically
