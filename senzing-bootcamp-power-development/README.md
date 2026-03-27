# Senzing Boot Camp - Development Documentation

Internal development documentation for the Senzing Boot Camp Kiro Power. These files are not distributed with the power.

## Purpose

This repository tracks design decisions, improvement history, and preserves files removed from the power distribution for reference.

## Contents

### `development/` — Design Decisions and History

Architecture docs, design decisions, and improvement records:

- `ALL_IMPROVEMENTS_COMPLETE.md` — Comprehensive record of all development phases
- `IMPROVEMENTS.md` / `IMPROVEMENTS_V3.md` — Improvement trackers
- `NEW_MODULE_STRUCTURE.md` — Documents the 13-module architecture
- `NEW_WORKFLOWS_PHASE5.md` — Detailed Module 7-12 workflows (referenced by steering.md)
- `DIRECTORY_STRUCTURE_FIRST.md` / `DIRECTORY_STRUCTURE_GUARANTEE.md` — Why directory creation is mandatory
- `PEP8_ENFORCEMENT_SUMMARY.md` — PEP-8 decision rationale
- `SQLITE_DATABASE_LOCATION_UPDATE.md` — Database location policy rationale
- `POWER_BUILDER_IMPROVEMENTS_2026-03-27.md` — Power builder alignment record
- `AUDIT_2026-03-24.md` — Documentation audit reference
- `V3_IMPLEMENTATION_STATUS.md` — v3 implementation status

### `feedback/` — Development Feedback Records

Improvement notes and implementation details from user feedback.

### `guides/` — Removed Guide Files

Guide files removed from power distribution (duplicated MCP server functionality or were internal docs).

### `hooks/` — Removed Hook Files

Generic hooks removed from power distribution. Preserved for users who want them.

### `quickstart_demo/` — Removed Demo Scripts

Static demo scripts replaced by MCP-generated code.

### `steering/` — Removed Steering Files

Generic best-practices steering files removed from power distribution. MCP server provides this information dynamically.

## Root Files

- `README.md` — This file
- `TESTING.md` — How to test the power locally before distribution

## For Maintainers

- Add new development notes to `development/`, not the root
- Reference `TESTING.md` for testing procedures
- Check `development/ALL_IMPROVEMENTS_COMPLETE.md` for full history
