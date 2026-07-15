# Requirements Document

## Introduction

In Module 4 (Data Collection) a bootcamper can collect a large dataset (for example, all five
London CORD sources at 123,911 records) and carry the full dataset forward. Today the only
SQLite-volume heads-up fires later, in Module 6 Phase A, and it is driven by the *stated production
tier* (Medium/Large) rather than by the *actual collected dataset*. As a result, a bootcamper who
collects a large dataset that will run on SQLite gets no warning **at data-collection time** that
the Module 6 load will be slow. In the reported session the load throughput started high and
degraded as the database grew, and the initial load plus the entity-resolution redo phase took
about an hour — a long, mostly-idle wait that can look like the process has stalled, and that is
disproportionate for a learning exercise.

This feature adds an earlier, time/performance-based heads-up in Module 4. When the bootcamper has
collected more than 75,000 records in total AND the active database is SQLite, the bootcamp warns —
at collection time — that the Module 6 load will take significant time, sourcing the specific timing
figures from the Senzing MCP server (and omitting any figure the server does not return). It then
offers the bootcamper a choice: load all records, sample down to a smaller record count, or switch
to an alternative database such as PostgreSQL. When the bootcamper chooses to sample, the bootcamp
asks which sampling strategy to use. The decision is recorded so the existing Module 6 SQLite
heads-up does not redundantly re-ask for the same load.

This warning is a **time/performance** concern and is deliberately kept **independent of and
distinct from** the existing license-capacity sampling framing already present in Module 4 (which
governs how many records the effective license permits). This warning applies even when the license
imposes no record cap. Like the existing Module 6 heads-up, this warning is **non-blocking**: the
bootcamper may always proceed on SQLite with the full dataset.

This feature complements — and must not duplicate or conflict with — the existing
`module6-sqlite-volume-hard-prompt` (the Module 6 Phase A stop-and-confirm heads-up), and reuses the
existing record-count computation (`record_count_backfill` / `data_sources` registry), volume
helpers (`volume_utils`), preferences machinery (`preferences_utils`), and the
`database-migration-guide`, rather than introducing parallel logic.

## Glossary

- **Load_Time_Warning**: The new Module 4 heads-up that warns, at data-collection time, about the
  time cost of a Module 6 SQLite load and offers proceed/sample/alternative-database options. This
  is the primary system named in the requirements below.
- **Module_4_Steering**: The steering file at `senzing-bootcamp/steering/module-04-data-collection.md`
  that guides the agent through Module 4 (Data Collection).
- **Module_6_SQLite_Prompt**: The existing Module 6 Phase A stop-and-confirm heads-up defined by the
  `module6-sqlite-volume-hard-prompt` spec, which fires on the Medium/Large production tier before
  the Phase B load and records a `sqlite_volume_prompt` decision marker.
- **Data_Sources_Registry**: The YAML file at `config/data_sources.yaml` that tracks each collected
  source's metadata, including `record_count`, `file_path`, and `format`.
- **Collected_Record_Total**: The total number of records across all collected sources, inferred
  from the Data_Sources_Registry record-count metadata (with a row-count fallback for sources that
  lack a stated count).
- **Warning_Threshold**: The record-count boundary that, when strictly exceeded, arms the warning.
  Its value is 75,000 records.
- **SQLite_Active**: The condition that the bootcamper's active Senzing database (`database_type` in
  Bootcamp_Preferences) normalizes to SQLite.
- **MCP_Server**: The Senzing MCP server (referred to by name only), the sole authoritative source
  for Senzing facts, including SQLite load-timing figures.
- **Timing_Guidance**: The SQLite load-timing figures (expected throughput, throughput degradation,
  expected load duration, and redo-phase duration) retrieved from the MCP_Server at request time.
- **Redo_Phase**: The Senzing entity-resolution deferred-processing phase that runs after the
  initial load and requires additional time.
- **Sampling_Strategy**: The method used to reduce the dataset to a target record count — one of:
  first-N records, random-N records, N records selected to best demonstrate entity resolution
  (preserving cross-source overlaps / known match clusters), or another bootcamper-described
  strategy.
- **Load_Decision_Marker**: The persisted record of the bootcamper's response to the Load_Time_Warning,
  written to Bootcamp_Preferences and read by the Module_6_SQLite_Prompt to avoid a redundant
  re-prompt for the same load.
- **Bootcamp_Preferences**: The YAML file at `config/bootcamp_preferences.yaml` that stores
  bootcamper choices, including `database_type` and the `sqlite_volume_prompt` decision marker.
- **Effective_License_Limit**: The active record cap (`license_record_limit` in
  `config/bootcamp_progress.json`), where 0 means no cap; used only to establish that the
  Load_Time_Warning is independent of license capacity.
- **Database_Migration_Guide**: The existing guide at `docs/guides/DATABASE_MIGRATION.md`
  (`database-migration-guide` spec) that covers switching from SQLite to PostgreSQL.

## Requirements

### Requirement 1: Trigger the warning on a large collected dataset running on SQLite

**User Story:** As a bootcamper collecting a large dataset in Module 4, I want to be warned at
collection time that a SQLite load will be slow, so that I understand the time cost before I commit
to carrying the full dataset into Module 6.

#### Acceptance Criteria

1. WHEN Module 4 data collection is complete AND the Collected_Record_Total exceeds the
   Warning_Threshold AND SQLite_Active is true, THE Load_Time_Warning SHALL present the warning
   before the transition to Module 5.
2. WHEN the Collected_Record_Total is at or below the Warning_Threshold, THE Load_Time_Warning SHALL
   continue the Module 4 flow without presenting the warning.
3. WHERE the active database normalizes to a non-SQLite engine, THE Load_Time_Warning SHALL continue
   the Module 4 flow without presenting the warning.
4. IF the active database type or the Collected_Record_Total is indeterminate, THEN THE
   Load_Time_Warning SHALL continue the Module 4 flow without presenting the warning.

### Requirement 2: Compute the collected record total independent of stated production tier

**User Story:** As a bootcamper, I want the warning to judge the time cost from my actual collected
data, so that the heads-up reflects what I will really load rather than a stated production estimate.

#### Acceptance Criteria

1. THE Load_Time_Warning SHALL compute the Collected_Record_Total from the Data_Sources_Registry
   `record_count` metadata.
2. WHERE a collected source lacks a stated `record_count`, THE Load_Time_Warning SHALL resolve the
   count from the collected file's row count when the format is countable, and otherwise SHALL treat
   that source's contribution as unknown rather than as zero.
3. WHEN the resolved Collected_Record_Total strictly exceeds the Warning_Threshold, THE
   Load_Time_Warning SHALL treat the trigger condition as met even when some sources remain unknown,
   since unknown sources can only increase the total.
4. IF the Collected_Record_Total cannot be computed from the Data_Sources_Registry, THEN THE
   Load_Time_Warning SHALL continue the Module 4 flow without presenting the warning.
5. THE Load_Time_Warning SHALL derive the trigger from the Collected_Record_Total and the active
   database type only, independent of the production tier recorded by the Module_6_SQLite_Prompt.

### Requirement 3: Present MCP-sourced timing guidance with graceful omission

**User Story:** As a bootcamper, I want realistic, authoritative timing expectations for the SQLite
load, so that I can decide whether the wait is acceptable and recognize that a slow load is expected
rather than stuck.

#### Acceptance Criteria

1. WHEN the Load_Time_Warning presents the warning, THE Load_Time_Warning SHALL state that loading
   the Collected_Record_Total on SQLite in Module 6 is expected to be slow and SHALL name the
   Collected_Record_Total driving the warning.
2. WHEN the Load_Time_Warning presents timing expectations, THE Load_Time_Warning SHALL retrieve the
   Timing_Guidance from the MCP_Server at request time.
3. THE Load_Time_Warning SHALL present a timing figure only when that figure is returned by the
   MCP_Server at request time.
4. IF the MCP_Server does not return a Timing_Guidance figure or cannot be reached, THEN THE
   Load_Time_Warning SHALL omit that figure and state that the value is currently unavailable from
   the MCP_Server.
5. THE Load_Time_Warning SHALL state that SQLite load throughput is expected to degrade as the
   database grows.
6. THE Load_Time_Warning SHALL state that the entity-resolution Redo_Phase requires additional time
   beyond the initial load.
7. THE Load_Time_Warning SHALL state that a slow, mostly-idle load is expected for a dataset of this
   size and indicates continued progress rather than a stalled process.

### Requirement 4: Offer proceed, sample, and alternative-database options

**User Story:** As a bootcamper, I want clear choices after the warning, so that I can proceed
knowingly, reduce the dataset, or switch databases.

#### Acceptance Criteria

1. WHEN the Load_Time_Warning presents the warning, THE Load_Time_Warning SHALL offer an option to
   load all collected records on SQLite.
2. WHEN the Load_Time_Warning presents the warning, THE Load_Time_Warning SHALL offer an option to
   sample the dataset down to a bootcamper-specified target record count.
3. WHEN the Load_Time_Warning presents the warning, THE Load_Time_Warning SHALL offer an option to
   switch to an alternative database and SHALL route the bootcamper to the Database_Migration_Guide
   rather than duplicating migration steps.
4. WHEN the bootcamper chooses to load all collected records, THE Load_Time_Warning SHALL obtain an
   explicit confirmation that the bootcamper accepts the expected load time before continuing the
   Module 4 flow with the full dataset.
5. THE Load_Time_Warning SHALL allow the bootcamper to proceed on SQLite with the full dataset, and
   SHALL present the warning as a heads-up rather than as a mandatory gate.

### Requirement 5: Ask which sampling strategy to use when the bootcamper samples

**User Story:** As a bootcamper who chooses to sample, I want to pick how the sample is selected, so
that the reduced dataset still serves my learning goals.

#### Acceptance Criteria

1. WHEN the bootcamper chooses to sample the dataset, THE Load_Time_Warning SHALL ask which
   Sampling_Strategy to use before creating the sample.
2. WHEN the Load_Time_Warning asks which Sampling_Strategy to use, THE Load_Time_Warning SHALL offer
   the first-N-records strategy, the random-N-records strategy, and the entity-resolution-demonstrating
   strategy that preserves cross-source overlaps and known match clusters.
3. WHERE the bootcamper describes an alternative sampling approach, THE Load_Time_Warning SHALL
   accept that bootcamper-described Sampling_Strategy.
4. WHEN a Sampling_Strategy and target record count are chosen, THE Load_Time_Warning SHALL create
   the sample using the chosen strategy, save it under `data/samples/`, and document the strategy and
   target count.
5. THE Load_Time_Warning SHALL require the sampling target record count to be a positive integer that
   is less than the Collected_Record_Total.
6. IF the requested sampling target record count is not a positive integer or is not less than the
   Collected_Record_Total, THEN THE Load_Time_Warning SHALL re-ask for a valid target record count
   before creating the sample.
7. WHEN the bootcamper chooses the entity-resolution-demonstrating strategy, THE Load_Time_Warning
   SHALL select records that preserve cross-source overlaps and known match clusters.

### Requirement 6: Persist the decision to avoid a redundant Module 6 re-prompt

**User Story:** As a bootcamper who already decided about the SQLite load in Module 4, I want that
decision remembered, so that Module 6 does not ask me the same thing again for the same load.

#### Acceptance Criteria

1. WHEN the bootcamper responds to the Load_Time_Warning, THE Load_Time_Warning SHALL record the
   Load_Decision_Marker to Bootcamp_Preferences, capturing the chosen option and the identity of the
   load the decision applies to.
2. THE Load_Time_Warning SHALL persist the Load_Decision_Marker using the existing Bootcamp_Preferences
   decision-marker mechanism shared with the Module_6_SQLite_Prompt rather than a parallel store.
3. WHEN a Load_Decision_Marker has been recorded for the current load and the active database remains
   SQLite, THE Module_6_SQLite_Prompt SHALL treat the SQLite volume concern as already decided and
   continue without re-presenting its heads-up for that same load.
4. IF the load identity recorded in the Load_Decision_Marker differs from the current load, THEN THE
   Module_6_SQLite_Prompt SHALL evaluate its own condition as if no Module 4 decision applied.

### Requirement 7: Keep the warning non-blocking and distinct from license-capacity framing

**User Story:** As a maintainer, I want the time/performance warning to stay separate from the
license-capacity framing and to never block the flow, so that the two concerns remain consistent and
the bootcamper is never stuck.

#### Acceptance Criteria

1. THE Load_Time_Warning SHALL evaluate its trigger from the Collected_Record_Total and the active
   database type independent of the Effective_License_Limit.
2. WHERE the Effective_License_Limit imposes no record cap, THE Load_Time_Warning SHALL still present
   the warning when the Warning_Threshold and SQLite_Active conditions are met.
3. THE Load_Time_Warning SHALL present the time/performance concern as distinct from the
   license-capacity sampling framing already defined in Module_4_Steering, while keeping sampling
   available as one option among proceeding and switching databases.
4. THE Load_Time_Warning SHALL reuse the existing record-count computation, volume helpers,
   preferences machinery, and Database_Migration_Guide rather than adding parallel logic.
5. IF any step of the Load_Time_Warning fails or an input is indeterminate, THEN THE Load_Time_Warning
   SHALL continue the Module 4 flow without blocking.

### Requirement 8: Test coverage

**User Story:** As a maintainer, I want tests so the trigger condition, MCP omission, options,
sampling sub-choice, and persistence do not regress.

#### Acceptance Criteria

1. THE feature SHALL include tests covering the trigger truth table: Collected_Record_Total above,
   at, and below the Warning_Threshold, crossed with SQLite and non-SQLite database types, asserting
   the warning fires only above the threshold on SQLite.
2. THE feature SHALL include tests covering the MCP-unavailable case, asserting that a missing
   Timing_Guidance figure is omitted and reported as currently unavailable rather than substituted.
3. THE feature SHALL include tests covering the proceed, sample, and alternative-database options,
   the Sampling_Strategy sub-choice, the Load_Decision_Marker persistence, the Module_6_SQLite_Prompt
   no-reprompt behavior, and the non-blocking fallback when the Collected_Record_Total is uncomputable.
4. Tests SHALL follow the project pattern (pytest + Hypothesis, class-based, `sys.path` import of
   `scripts/`) in `senzing-bootcamp/tests/`.
