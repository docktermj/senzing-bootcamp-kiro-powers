# Requirements: SQLite to PostgreSQL Database Migration Guide

## Overview

Add a guided database migration step (SQLite → PostgreSQL) as an optional mini-module or guided step in Module 8, since production Senzing deployments require PostgreSQL but the bootcamp defaults to SQLite for simplicity.

## Requirements

1. Create `docs/guides/DATABASE_MIGRATION.md` covering the full SQLite → PostgreSQL migration path for Senzing
2. The guide must include: prerequisites (PostgreSQL installed and running), database creation, Senzing schema initialization, data re-loading strategy (re-run loading program against PostgreSQL), and verification
3. Explain why migration is needed: SQLite limitations (single-writer, no network access, performance ceiling at ~100K records), PostgreSQL advantages (concurrent access, production-grade, required for multi-process loading)
4. Include agent instruction blocks calling `sdk_guide(topic='configure', language='<chosen_language>')` for PostgreSQL-specific engine configuration
5. Include agent instruction blocks calling `search_docs(query='PostgreSQL database setup', version='current')` for authoritative guidance
6. Add a cross-reference from Module 8 steering (`module-08-performance.md`) to the migration guide as an optional step when performance testing reveals SQLite bottlenecks
7. Add the guide to `docs/guides/README.md` in the Reference Documentation section
8. The guide must not require re-mapping data — only re-loading from existing Senzing JSON files
9. Include a rollback path: if PostgreSQL migration fails, the SQLite database is still intact
10. Update `config/bootcamp_preferences.yaml` schema to track `database_type` changes (sqlite → postgresql)
11. Write tests verifying guide structure, required sections, MCP tool references, and cross-references from Module 8
