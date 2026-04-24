# Requirements: Refocus Module 8 on Query & Visualize

## Introduction

Rename Module 8 from "Query, Visualize & Validate" to "Query & Visualize" and move validation steps into the data mapping/loading module where they naturally belong.

## What Happened

Module 8 bundles validation (confirming match accuracy) with querying (building custom query programs). Validation is really the final check after mapping and loading, not a querying activity.

## Why It's a Problem

Combining validation with querying conflates two different concerns. Validation belongs with mapping/loading as its natural conclusion. Querying is a separate skill. Bundling them makes Module 8 unfocused and leaves the mapping/loading modules feeling incomplete.

## Acceptance Criteria

1. Module 8 is renamed to "Query & Visualize" and focused entirely on building query programs, overlap reports, search programs, and visualizations
2. Validation steps (checking match accuracy, reviewing cross-source results, confirming success criteria) are moved to the data mapping/loading module as its final phase
3. All references to Module 8's name and scope are updated across POWER.md, steering files, and documentation
4. The mapping → loading → validation flow is continuous within a single module

## Reference

- Source: `tmpe/SENZING_BOOTCAMP_POWER_FEEDBACK.md` — "Rename Module 8 and move validation into the data mapping module"
- Module: 8 | Priority: High | Category: Workflow
