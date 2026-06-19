# Requirements Document

## Introduction

The senzing-bootcamp Kiro Power supports five languages (Python, Java, C#, Rust,
TypeScript/Node.js). Core code generation via the MCP server tools `generate_scaffold`
and `sdk_guide` produces equivalent results for every supported language. However, the
depth of *supplementary* example coverage available via the MCP `find_examples` tool
varies by language. Today this gap is only disclosed as static prose in `POWER.md` and
`onboarding-phase1b-intro-language.md` ("Python and Java currently have the most
extensive example coverage"). The gap is disclaimed but neither tracked nor demonstrably
shrinking.

This feature makes the cross-language example-coverage gap visible and trackable so it
can be deliberately reduced rather than merely disclaimed. It introduces a canonical,
machine-readable coverage record under `senzing-bootcamp/config/`, a stdlib-only report
script under `senzing-bootcamp/scripts/`, a mechanism that keeps the `POWER.md`
disclosure consistent with the tracked record, and CI validation. All Senzing example
facts originate from the MCP server (`find_examples`); the coverage record is a
maintainer-curated snapshot of known MCP results and never hardcodes Senzing knowledge
that belongs to the MCP server.

## Glossary

- **Coverage_Record**: The canonical machine-readable YAML config file
  (`senzing-bootcamp/config/example-coverage.yaml`) that stores, per supported language,
  which bootcamp workflows/topics have supplementary examples available via
  `find_examples`, plus snapshot provenance metadata.
- **Supported_Language**: One of the languages the bootcamp supports (Python, Java, C#,
  Rust, TypeScript/Node.js); the authoritative current list is obtained from the MCP
  server at session start.
- **Coverage_Topic**: A named bootcamp workflow or topic (for example `add_records`,
  `query`, `redo`, `container deployment`) for which supplementary example availability
  is tracked across languages.
- **Coverage_Entry**: A single tracked fact recording whether supplementary examples
  exist for a specific Coverage_Topic in a specific Supported_Language.
- **Coverage_Status**: The recorded availability value for a Coverage_Entry, one of
  `available`, `none`, or `unknown`.
- **Coverage_Report_Script**: The stdlib-only Python CLI script
  (`senzing-bootcamp/scripts/example_coverage_report.py`) that reads the Coverage_Record
  and produces a per-language coverage report highlighting gaps.
- **Coverage_Disclosure**: The human-readable prose statement(s) in `POWER.md` (and
  comparable onboarding steering text) describing relative example coverage across
  languages.
- **Coverage_Validator**: The validation logic (run in CI) that checks the
  Coverage_Record schema and verifies the Coverage_Disclosure is consistent with the
  Coverage_Record.
- **MCP_Server**: The Senzing MCP server, the sole source of Senzing example facts,
  queried via tools including `find_examples`.
- **Maintainer**: A person who updates the Coverage_Record from observed MCP
  `find_examples` results.
- **Snapshot_Metadata**: Provenance fields in the Coverage_Record recording when the
  coverage data was last observed from the MCP_Server and against which Senzing version.

## Requirements

### Requirement 1: Canonical Coverage Record

**User Story:** As a maintainer, I want a single machine-readable record of per-language
example coverage, so that the coverage gap is tracked in one authoritative location
instead of scattered prose.

#### Acceptance Criteria

1. THE Coverage_Record SHALL be stored as a YAML file at
   `senzing-bootcamp/config/example-coverage.yaml`.
2. THE Coverage_Record SHALL list each Supported_Language as a tracked language key.
3. THE Coverage_Record SHALL define a set of Coverage_Topic identifiers that represent
   the bootcamp workflows and topics whose example availability is tracked.
4. FOR each combination of Supported_Language and Coverage_Topic, THE Coverage_Record
   SHALL store exactly one Coverage_Entry with a Coverage_Status value.
5. THE Coverage_Record SHALL constrain each Coverage_Status to one of the values
   `available`, `none`, or `unknown`.
6. THE Coverage_Record SHALL include Snapshot_Metadata fields recording the date the
   coverage data was last observed and the Senzing version it was observed against.
7. WHERE the Coverage_Record uses a file extension, THE Coverage_Record SHALL use the
   `.yaml` extension with kebab-case or snake_case naming consistent with existing
   configs under `senzing-bootcamp/config/`.

### Requirement 2: Coverage Signal Definition

**User Story:** As a maintainer, I want a clearly defined coverage signal, so that
everyone interprets per-language coverage the same way.

#### Acceptance Criteria

1. THE Coverage_Record SHALL define the coverage signal as the availability of
   supplementary examples via the MCP_Server `find_examples` tool for a given
   Coverage_Topic and Supported_Language.
2. THE Coverage_Record SHALL document, in an embedded description field, that a
   Coverage_Status of `available` means at least one supplementary example was observed
   via `find_examples` for that Coverage_Topic and Supported_Language.
3. THE Coverage_Record SHALL document, in an embedded description field, that a
   Coverage_Status of `unknown` means the Coverage_Topic and Supported_Language
   combination has not yet been observed via the MCP_Server.
4. THE Coverage_Record SHALL record, for each Coverage_Topic, a human-readable label
   describing the bootcamp workflow or topic the identifier represents.

### Requirement 3: Coverage Report Generation

**User Story:** As a maintainer, I want to produce a coverage report from the record, so
that I can see per-language coverage and identify gaps at a glance.

#### Acceptance Criteria

1. THE Coverage_Report_Script SHALL be a Python script located at
   `senzing-bootcamp/scripts/example_coverage_report.py`.
2. THE Coverage_Report_Script SHALL depend only on the Python 3.11+ standard library,
   except for PyYAML used to parse the Coverage_Record.
3. THE Coverage_Report_Script SHALL provide an argparse-based command-line interface with
   a `main(argv=None)` entry point, consistent with existing scripts under
   `senzing-bootcamp/scripts/`.
4. WHEN the Coverage_Report_Script is run, THE Coverage_Report_Script SHALL output a
   per-language summary showing the count of Coverage_Topic identifiers at each
   Coverage_Status.
5. WHEN the Coverage_Report_Script is run, THE Coverage_Report_Script SHALL list the
   Coverage_Topic identifiers whose Coverage_Status is `none` or `unknown` for each
   Supported_Language, identifying the coverage gaps.
6. WHEN the Coverage_Report_Script completes without error, THE Coverage_Report_Script
   SHALL exit with code 0.
7. IF the Coverage_Record file is missing or cannot be parsed, THEN THE
   Coverage_Report_Script SHALL print a descriptive error message and exit with code 1.
8. THE Coverage_Report_Script SHALL display the Snapshot_Metadata in the report so that
   readers can see how current the coverage data is.

### Requirement 4: Disclosure Consistency With Tracked Data

**User Story:** As a maintainer, I want the POWER.md disclosure kept consistent with the
tracked coverage record, so that the prose disclaimer cannot silently drift from reality.

#### Acceptance Criteria

1. THE Coverage_Validator SHALL verify that the Coverage_Disclosure in `POWER.md` is
   consistent with the Supported_Language coverage ranking derived from the
   Coverage_Record.
2. IF the Coverage_Disclosure names languages with the most extensive coverage that do
   not match the ranking derived from the Coverage_Record, THEN THE Coverage_Validator
   SHALL report a drift error and exit with a non-zero code.
3. THE Coverage_Disclosure consistency mechanism SHALL use a marker-delimited or
   generated-region approach compatible with the existing generated-documentation
   drift-prevention convention used for other auto-maintained content.
4. WHERE a generated region is used in `POWER.md`, THE Coverage_Disclosure mechanism
   SHALL scope the generated content to the coverage disclosure only and SHALL leave all
   other `POWER.md` content unchanged.

### Requirement 5: MCP As Sole Source of Senzing Facts

**User Story:** As a maintainer, I want the coverage record to be a curated snapshot of
MCP results, so that the feature never hardcodes Senzing knowledge that belongs to the
MCP server.

#### Acceptance Criteria

1. THE Coverage_Record SHALL contain only maintainer-curated snapshots of example
   availability observed from the MCP_Server `find_examples` tool.
2. THE Coverage_Report_Script SHALL derive all coverage information solely from the
   Coverage_Record and SHALL NOT query the MCP_Server directly.
3. THE Coverage_Record SHALL NOT contain MCP server URLs; the MCP server URL SHALL remain
   only in `senzing-bootcamp/mcp.json`.
4. THE Coverage_Record SHALL document that Coverage_Entry values are updated by a
   Maintainer from observed `find_examples` results rather than from model training data.

### Requirement 6: Honest Limitation Statement

**User Story:** As a bootcamper, I want the coverage information to be honest about its
scope, so that I understand example coverage does not affect the quality of generated
code.

#### Acceptance Criteria

1. THE Coverage_Disclosure SHALL state that the tracked coverage signal reflects
   supplementary example availability only.
2. THE Coverage_Disclosure SHALL state that `generate_scaffold` and `sdk_guide` produce
   equivalent results for all Supported_Languages.
3. WHEN the Coverage_Report_Script outputs a report, THE Coverage_Report_Script SHALL
   include a statement that the report reflects supplementary example availability only
   and does not reflect `generate_scaffold` or `sdk_guide` output quality.

### Requirement 7: Validation and CI Integration

**User Story:** As a maintainer, I want the coverage record and disclosure validated in
CI, so that schema errors and disclosure drift are caught automatically.

#### Acceptance Criteria

1. THE Coverage_Validator SHALL verify that every Coverage_Entry in the Coverage_Record
   uses a Coverage_Status value of `available`, `none`, or `unknown`.
2. THE Coverage_Validator SHALL verify that the Coverage_Record includes a Coverage_Entry
   for every combination of tracked Supported_Language and Coverage_Topic.
3. THE Coverage_Validator SHALL verify that the Coverage_Record includes the required
   Snapshot_Metadata fields.
4. WHEN the Coverage_Validator detects a schema violation, THE Coverage_Validator SHALL
   print a descriptive error message and exit with a non-zero code.
5. THE Coverage_Validator SHALL run as a step in the
   `.github/workflows/validate-power.yml` CI pipeline.
6. THE coverage test suite SHALL reside under `senzing-bootcamp/tests/` and SHALL use
   pytest with Hypothesis for property-based tests.

### Requirement 8: Trackability Over Time

**User Story:** As a maintainer, I want to see whether coverage is improving over time,
so that the gap can be deliberately reduced rather than left static.

#### Acceptance Criteria

1. THE Coverage_Report_Script SHALL compute, per Supported_Language, the proportion of
   Coverage_Topic identifiers with a Coverage_Status of `available`.
2. WHERE a `--format` option requesting machine-readable output is provided, THE
   Coverage_Report_Script SHALL emit the per-language coverage proportions in a
   structured format suitable for comparison across snapshots.
3. WHEN the Coverage_Record Snapshot_Metadata is updated, THE Coverage_Record SHALL
   retain the most recent observation date and Senzing version so that successive
   snapshots are comparable.
