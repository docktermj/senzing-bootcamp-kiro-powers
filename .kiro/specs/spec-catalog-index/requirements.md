# Requirements Document

## Introduction

The senzing-bootcamp repository contains a large, fast-growing collection of spec
directories under `.kiro/specs/` (currently 221 directories). Each spec typically
holds `requirements.md`, `design.md`, `tasks.md`, and a `.config.kiro` metadata
file. At this volume the catalog is itself a navigation problem: maintainers
cannot easily discover prior art before opening a new spec, cannot see at a glance
whether a spec shipped or was abandoned, and cannot trace supersession chains where
later specs replace earlier ones (for example `self-answering-questions-fix` →
`self-answering-prevention-v2` → `self-answering-reinforcement`, and pairs such as
`module-recap-document` → `module-recap-document-fix`).

This feature provides a generated, regenerable index of the spec catalog. A
stdlib-only Python generator (consistent with `generate_docs_index.py` conventions)
scans `.kiro/specs/`, derives each spec's status from existing signals, resolves
curated supersession and related-spec relationships, and produces a human-readable
Markdown index plus an optional machine-readable summary. A `--check` drift mode
keeps the committed index in sync with the actual spec directories, matching the
repository's existing drift-prevention gates in CI.

The feature only reads and indexes spec directories; it never modifies or deletes
existing specs. Status is derived primarily from signals already present in each
spec directory, with a small curated metadata file supplying only the editorial
facts (supersession, abandonment) that cannot be derived.

## Glossary

- **Spec_Catalog_Generator**: The stdlib-only Python CLI script that scans the spec
  catalog and produces the index and summary outputs. Lives at
  `senzing-bootcamp/scripts/generate_spec_catalog.py`.
- **Specs_Root**: The directory scanned for specs. Defaults to `.kiro/specs/`.
- **Spec_Directory**: A single immediate subdirectory of the Specs_Root that
  represents one spec (for example `.kiro/specs/adaptive-pacing/`). Its name is the
  spec's identifier.
- **Spec_Document**: One of the recognized files within a Spec_Directory:
  `requirements.md`, `design.md`, or `tasks.md`.
- **Config_File**: The `.config.kiro` file inside a Spec_Directory. It is
  JSON-formatted with keys `specId`, `workflowType`, and `specType`.
- **Task_Checkbox**: A Markdown checklist item line in `tasks.md` matching the
  committed format `- [ ]` (incomplete) or `- [x]` (complete).
- **Status_Value**: One of the enumerated spec lifecycle states:
  `in-progress`, `implemented`, `superseded`, `abandoned`, or `unknown`.
- **Catalog_Metadata_File**: A curated configuration file (YAML) supplying
  editorial facts the generator cannot derive — supersession relationships, related
  specs, and explicit status overrides. It is living configuration (analogous to
  `module-dependencies.yaml`), not hand-maintained history.
- **Supersession_Relationship**: A recorded directional link stating that one
  Spec_Directory replaces another (`superseded_by` / `supersedes`).
- **Related_Relationship**: A recorded non-directional link associating two
  Spec_Directories that address related concerns without superseding each other.
- **Spec_Index**: The generated human-readable Markdown index of the catalog.
- **Catalog_Summary**: The generated machine-readable JSON representation of the
  catalog.
- **Drift_Check_Mode**: The generator's `--check` mode, which reports whether the
  committed Spec_Index matches freshly generated output without writing.

## Requirements

### Requirement 1: Discover the spec catalog

**User Story:** As a bootcamp maintainer, I want the generator to discover every
spec directory under the specs root, so that the index reflects the complete
catalog without manual enumeration.

#### Acceptance Criteria

1. WHEN the Spec_Catalog_Generator runs, THE Spec_Catalog_Generator SHALL identify every immediate subdirectory of the Specs_Root as a Spec_Directory.
2. THE Spec_Catalog_Generator SHALL record, for each Spec_Directory, the spec identifier as the directory name.
3. THE Spec_Catalog_Generator SHALL record, for each Spec_Directory, the presence or absence of `requirements.md`, `design.md`, and `tasks.md`.
4. WHEN a Config_File is present in a Spec_Directory, THE Spec_Catalog_Generator SHALL read the `workflowType` and `specType` values from the Config_File.
5. IF a Spec_Directory contains no Spec_Document and no Config_File, THEN THE Spec_Catalog_Generator SHALL include the Spec_Directory in the catalog with a `Status_Value` of `unknown`.
6. THE Spec_Catalog_Generator SHALL process Spec_Directories in case-insensitive ascending order of spec identifier.

### Requirement 2: Determine spec status from existing signals

**User Story:** As a bootcamp maintainer, I want each spec's status derived from
signals already present in the spec directory, so that status reflects reality with
minimal manual bookkeeping.

#### Acceptance Criteria

1. THE Spec_Catalog_Generator SHALL assign each Spec_Directory exactly one Status_Value from the set {`in-progress`, `implemented`, `superseded`, `abandoned`, `unknown`}.
2. WHERE the Catalog_Metadata_File records an explicit status override for a Spec_Directory, THE Spec_Catalog_Generator SHALL assign that recorded Status_Value and SHALL derive no status from other signals.
3. WHERE the Catalog_Metadata_File records that a Spec_Directory is superseded by another Spec_Directory, THE Spec_Catalog_Generator SHALL assign the Status_Value `superseded`.
4. WHEN no override applies, `tasks.md` is present, and every Task_Checkbox in `tasks.md` is complete, THE Spec_Catalog_Generator SHALL assign the Status_Value `implemented`.
5. WHEN no override applies, `tasks.md` is present, and at least one Task_Checkbox in `tasks.md` is incomplete, THE Spec_Catalog_Generator SHALL assign the Status_Value `in-progress`.
6. WHEN no override applies, `tasks.md` is present, and `tasks.md` contains no Task_Checkbox, THE Spec_Catalog_Generator SHALL assign the Status_Value `unknown`.
7. WHEN no override applies, `tasks.md` is absent, and at least one of `requirements.md` or `design.md` is present, THE Spec_Catalog_Generator SHALL assign the Status_Value `in-progress`.
8. THE Spec_Catalog_Generator SHALL apply status resolution in the following precedence order: explicit status override, recorded supersession, Task_Checkbox completion state, Spec_Document presence.

### Requirement 3: Record and resolve spec relationships

**User Story:** As a bootcamp maintainer, I want supersession and related-spec
relationships recorded in a single curated file and surfaced in the index, so that
I can trace why a spec was replaced before creating a new one.

#### Acceptance Criteria

1. THE Spec_Catalog_Generator SHALL read Supersession_Relationship and Related_Relationship entries from the Catalog_Metadata_File.
2. THE Catalog_Metadata_File SHALL record each Supersession_Relationship as a directional link from a superseding Spec_Directory to the superseded Spec_Directory.
3. WHEN a Supersession_Relationship names a superseding Spec_Directory, THE Spec_Catalog_Generator SHALL present the reciprocal `supersedes` and `superseded_by` links for both Spec_Directories in the Spec_Index.
4. WHEN a Spec_Directory participates in a Related_Relationship, THE Spec_Catalog_Generator SHALL list the associated spec identifiers in that Spec_Directory's Spec_Index entry.
5. IF the Catalog_Metadata_File references a spec identifier that matches no discovered Spec_Directory, THEN THE Spec_Catalog_Generator SHALL report the unresolved identifier to standard error and SHALL exit with status code 1.
6. IF the Catalog_Metadata_File is absent, THEN THE Spec_Catalog_Generator SHALL generate the catalog using derived signals only and SHALL record no relationships.

### Requirement 4: Generate the human-readable Markdown index

**User Story:** As a bootcamp maintainer, I want a readable Markdown index of all
specs with their status and relationships, so that I can browse prior art at a
glance.

#### Acceptance Criteria

1. WHEN the Spec_Catalog_Generator runs outside Drift_Check_Mode, THE Spec_Catalog_Generator SHALL write the Spec_Index to the configured output path.
2. THE Spec_Index SHALL list one entry per discovered Spec_Directory, showing the spec identifier, the Status_Value, the `specType`, and the `workflowType`.
3. WHERE a Spec_Directory has a Supersession_Relationship or Related_Relationship, THE Spec_Index SHALL display the related spec identifiers within that spec's entry.
4. THE Spec_Index SHALL include a count of Spec_Directories grouped by Status_Value.
5. THE Spec_Index SHALL render a link from each spec entry to its Spec_Directory.
6. THE Spec_Index SHALL begin with generated-artifact provenance text stating that the file is generated by the Spec_Catalog_Generator and is to be regenerated rather than edited by hand.

### Requirement 5: Generate an optional machine-readable summary

**User Story:** As a maintainer building further tooling, I want an optional
machine-readable summary of the catalog, so that other scripts can consume spec
status and relationships programmatically.

#### Acceptance Criteria

1. WHERE the machine-readable summary option is requested, THE Spec_Catalog_Generator SHALL write the Catalog_Summary as JSON to the configured summary path.
2. THE Catalog_Summary SHALL contain, for each Spec_Directory, the spec identifier, the Status_Value, the `specType`, the `workflowType`, the presence flags for each Spec_Document, and the recorded relationships.
3. WHERE the machine-readable summary option is not requested, THE Spec_Catalog_Generator SHALL write only the Spec_Index.
4. THE Catalog_Summary SHALL serialize Spec_Directory entries in case-insensitive ascending order of spec identifier.
5. IF any field required for the Catalog_Summary cannot be collected for a Spec_Directory, THEN THE Spec_Catalog_Generator SHALL skip writing the Catalog_Summary and SHALL exit with status code 1.

### Requirement 6: Verify index synchronization (drift check)

**User Story:** As a maintainer, I want a check mode that fails when the committed
index no longer matches the spec directories, so that CI can prevent the index from
going stale.

#### Acceptance Criteria

1. WHEN the Spec_Catalog_Generator runs in Drift_Check_Mode, THE Spec_Catalog_Generator SHALL compare the committed Spec_Index against freshly generated output without writing any file.
2. WHEN the committed Spec_Index matches the freshly generated output in Drift_Check_Mode, THE Spec_Catalog_Generator SHALL exit with status code 0.
3. IF the committed Spec_Index differs from the freshly generated output in Drift_Check_Mode, THEN THE Spec_Catalog_Generator SHALL report the difference to standard error and SHALL exit with status code 1.
4. IF the Spec_Index file is absent in Drift_Check_Mode, THEN THE Spec_Catalog_Generator SHALL report the missing index to standard error and SHALL exit with status code 1.
5. WHEN a Spec_Directory is added to or removed from the Specs_Root after the Spec_Index was committed, THE Spec_Catalog_Generator in Drift_Check_Mode SHALL report the index as out of sync.

### Requirement 7: Deterministic and non-destructive operation

**User Story:** As a maintainer, I want generation to be deterministic and strictly
read-only over the spec catalog, so that the index is reproducible in CI and no
existing spec is ever altered.

#### Acceptance Criteria

1. WHEN the Spec_Catalog_Generator runs twice over an unchanged Specs_Root and Catalog_Metadata_File, THE Spec_Catalog_Generator SHALL produce byte-identical Spec_Index output.
2. THE Spec_Catalog_Generator SHALL write only to the configured Spec_Index path and, where requested, the configured Catalog_Summary path within the spec catalog, and MAY create temporary files and logs outside the Spec_Directories.
3. THE Spec_Catalog_Generator SHALL treat every Spec_Directory and Spec_Document as read-only.
4. WHEN the Spec_Catalog_Generator completes, THE Spec_Catalog_Generator SHALL leave every Spec_Directory and Spec_Document byte-identical to its pre-run content.

### Requirement 8: Command-line interface and error handling

**User Story:** As a maintainer, I want the generator to follow the repository's
script conventions and report errors clearly, so that it is consistent with
existing tooling and safe to run in CI.

#### Acceptance Criteria

1. THE Spec_Catalog_Generator SHALL accept a `--specs-root` argument that overrides the default Specs_Root of `.kiro/specs/`.
2. THE Spec_Catalog_Generator SHALL accept a `--check` argument that activates Drift_Check_Mode.
3. THE Spec_Catalog_Generator SHALL accept an argument that selects the optional Catalog_Summary output.
4. WHEN the Spec_Catalog_Generator completes with no detected errors, THE Spec_Catalog_Generator SHALL exit with status code 0.
5. IF the Spec_Catalog_Generator detects any error during processing, THEN THE Spec_Catalog_Generator SHALL exit with status code 1 even when processing reaches completion.
6. IF the Specs_Root does not exist or is not a directory, THEN THE Spec_Catalog_Generator SHALL report the error to standard error and SHALL exit with status code 1.
7. IF a Config_File contains content that is not valid JSON, THEN THE Spec_Catalog_Generator SHALL report the offending Spec_Directory to standard error and SHALL exit with status code 1.
8. IF the Catalog_Metadata_File is present and cannot be parsed, THEN THE Spec_Catalog_Generator SHALL report the parse error to standard error and SHALL exit with status code 1.
9. THE Spec_Catalog_Generator SHALL depend only on the Python 3.11+ standard library.

### Requirement 9: Output location and distribution boundary

**User Story:** As a maintainer, I want a clear decision on where the generated
index lives and whether it ships to users, so that the index does not pollute the
distributed power and remains consistent with the repository's structure rules.

#### Acceptance Criteria

1. THE Spec_Catalog_Generator SHALL write the Spec_Index to a default path under `.kiro/` so that the index of workspace-only development artifacts does not ship in the distributed power under `senzing-bootcamp/`.
2. THE Spec_Catalog_Generator SHALL accept an argument that overrides the Spec_Index output path.
3. THE Spec_Index SHALL be CommonMark-compliant as validated by `validate_commonmark.py` regardless of the configured output path.
4. THE Drift_Check_Mode SHALL be invocable as a CI gate consistent with the existing `--check` and `--verify` drift gates in `.github/workflows/validate-power.yml`.

## Decision Points

The following items are recorded for resolution during design. Defaults are stated
so the generator has a coherent starting behavior.

1. **Index location (default chosen):** The Spec_Index defaults to a path under
   `.kiro/` (the index describes `.kiro/specs/`, which is workspace tooling and is
   not part of the distributed power). Shipping it under `senzing-bootcamp/docs/`
   would expose internal development artifacts to bootcamp users and is therefore
   not the default. Requirement 9 keeps the path overridable and requires the
   Spec_Index to be CommonMark-compliant at every output location.
2. **Relationship storage (default chosen):** Supersession and related-spec links
   are stored in a single curated Catalog_Metadata_File rather than as new fields
   inside each `.config.kiro`. The `.config.kiro` files are tool-managed JSON
   (`specId`, `workflowType`, `specType`); adding editorial fields there risks
   being overwritten and scatters relationship data across 221 files. Design will
   confirm the metadata file location and exact schema.
3. **Config format note:** `.config.kiro` is JSON in practice (confirmed across the
   existing catalog), not YAML. The Catalog_Metadata_File uses YAML for consistency
   with other curated configs (`module-dependencies.yaml`, `steering-index.yaml`);
   design will confirm whether a minimal stdlib YAML parser suffices or whether the
   metadata file should also be JSON to keep the generator strictly stdlib-only.
