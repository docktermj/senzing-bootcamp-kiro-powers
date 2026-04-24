# Requirements: Merge Data Quality and Data Mapping Modules

## Introduction

Combine Module 4 (Data Quality Scoring) and Module 5 (Data Mapping) into a single "Data Quality & Mapping" module to eliminate the redundant boundary between quality assessment and data profiling.

## What Happened

Module 4 assesses field completeness and format consistency, then Module 5's profiling step immediately re-examines the same data to understand its schema. Users experience these as redundant steps separated by an artificial module boundary.

## Why It's a Problem

The separation creates unnecessary bureaucracy — separate banners, journey maps, and transitions for what is naturally one continuous thought process. Module 4's quality gate ("is this data ready?") and Module 5's profiling ("what does this data look like?") belong together.

## Acceptance Criteria

1. Modules 4 and 5 are merged into a single steering file covering quality assessment followed by the mapping workflow (profile → plan → map → generate)
2. The quality gate (≥70% to proceed) is preserved within the merged module
3. Module numbering is updated across all references in POWER.md, steering files, and documentation
4. The merged module flows continuously from quality scoring into mapping without a module boundary

## Reference

- Source: `tmpe/SENZING_BOOTCAMP_POWER_FEEDBACK.md` — "Combine Module 4 and Module 5 into a unified step"
- Module: 4-5 | Priority: High | Category: Workflow
