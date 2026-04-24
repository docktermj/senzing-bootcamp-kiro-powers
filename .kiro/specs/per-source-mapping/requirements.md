# Requirements: Per-Source Mapping Workflow

## Introduction

Run the Senzing MCP `mapping_workflow` separately for each user-supplied data file, producing individual mapping specification markdown files per source.

## What Happened

During Module 5, the bootcamp ran the mapping workflow against only the first file and applied the same mapping to all sources via a single mapper program. Each source should go through its own mapping workflow run.

## Why It's a Problem

In real-world scenarios, each data source has different schemas, field names, and quality characteristics. Mapping through a single workflow assumes identical schemas. Separate mapping files per source provide clear documentation, easier per-source updates, and practice running the workflow multiple times.

## Acceptance Criteria

1. `module-05-data-mapping.md` explicitly requires a separate `mapping_workflow` run for each user-supplied source file
2. Each mapping workflow run produces its own mapping specification markdown (e.g., `scripts/toyworld_mapper.md`, `scripts/funtoys_mapper.md`)
3. Mapper code may be shared across sources if schemas are identical, but mapping documentation is always per-source
4. The module instructions guide the user through mapping the first source, then repeating for each additional source

## Reference

- Source: `tmpe/SENZING_BOOTCAMP_POWER_FEEDBACK.md` — "Map each user-supplied file separately with its own mapping markdown"
- Module: 5 | Priority: Medium | Category: Workflow
