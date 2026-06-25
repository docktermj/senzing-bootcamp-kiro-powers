# Requirements Document

## Introduction

The `senzing-bootcamp` Kiro Power ships a `POWER.md` file whose volatile sections (MCP tool list, hook list and hook count, steering file table, and module overview table) repeatedly drift away from the machine-readable sources of truth in the repository. The CHANGELOG history is dominated by drift-correction releases: stale hook names, lingering "Module 12" references after it was collapsed into Module 11, stale line counts (e.g. "~79 lines" corrected to "~101 lines"), stale steering token counts, and MCP tool inventory drift.

The team has already proven a pattern that prevents this class of bug: a machine-readable single source of truth, a deterministic generator that emits a documentation section, and a CI `--verify` gate that fails the build when the committed documentation no longer matches what the generator would produce. This pattern exists today for the MCP tool inventory (`mcp_tool_inventory.py` + `check_mcp_tool_inventory()` in `validate_power.py`) and the hook registry (`sync_hook_registry.py --verify`).

This feature generalizes that proven pattern to ALL volatile sections of `POWER.md`. The volatile sections will be delimited by marker comments so hand-written prose around them is preserved, regenerated from existing sources of truth by a documentation generator, and protected by a CI verification gate that fails on drift without modifying any files. The solution must remain Python 3.11+ standard-library-only (PyYAML permitted only where YAML is parsed, consistent with `validate_dependencies.py`), produce CommonMark-compliant output that passes `validate_commonmark.py`, remain compatible with Kiro's `#[[file:...]]` include syntax, and integrate into the existing CI gate sequence in `.github/workflows/validate-power.yml`.

## Glossary

- **Power_Doc_Generator**: The system component (a script or documented set of scripts under `senzing-bootcamp/scripts/`) that regenerates the volatile sections of `POWER.md` from machine-readable sources of truth.
- **Verify_Mode**: The operating mode of the Power_Doc_Generator that compares generated content against the committed `POWER.md` and reports drift without modifying files.
- **Write_Mode**: The operating mode of the Power_Doc_Generator that regenerates and writes the volatile sections into `POWER.md` on disk.
- **POWER.md**: The power configuration and documentation file at `senzing-bootcamp/POWER.md` that ships to users.
- **Volatile_Section**: A region of `POWER.md` whose content is derived from a machine-readable source and is therefore subject to drift. In scope: the MCP tool list, the hook list and hook count, the steering file table, and the module overview table.
- **Generated_Region**: A delimited region inside `POWER.md`, bounded by marker comments, whose content is fully owned and overwritten by the Power_Doc_Generator.
- **Marker_Comment**: A CommonMark-compatible HTML comment that delimits the start or end of a Generated_Region (e.g. a begin marker and an end marker carrying a region identifier).
- **Source_Of_Truth**: A machine-readable file that authoritatively defines the data for a Volatile_Section. Existing sources include `scripts/mcp_tool_inventory.py` (MCP tools), `hooks/*.kiro.hook` plus `hooks/hook-categories.yaml` (hooks), `steering/steering-index.yaml` (steering files), and `config/module-dependencies.yaml` (modules).
- **MCP_Tool_Inventory**: The canonical 13-tool inventory defined by `ALL_TOOLS` and `TOTAL_COUNT` in `scripts/mcp_tool_inventory.py`.
- **Hook_Source**: The set of `hooks/*.kiro.hook` files and `hooks/hook-categories.yaml` that defines the hook list and hook count.
- **Steering_Index**: The machine-readable `steering/steering-index.yaml` file describing steering files, token counts, size categories, and keyword routing.
- **Module_Source**: The machine-readable file (`config/module-dependencies.yaml`) describing the bootcamp modules and their order.
- **CI_Pipeline**: The GitHub Actions workflow at `.github/workflows/validate-power.yml`.
- **Drift**: A state in which a Volatile_Section in the committed `POWER.md` differs from the content the Power_Doc_Generator produces from the current Source_Of_Truth.
- **Developer**: A maintainer of the `senzing-bootcamp` power who edits sources of truth and runs the generator.

## Requirements

### Requirement 1: Regenerate volatile sections from sources of truth

**User Story:** As a Developer, I want `POWER.md` volatile sections regenerated from machine-readable sources of truth, so that documentation cannot drift from the actual power contents.

#### Acceptance Criteria

1. WHEN the Power_Doc_Generator runs in Write_Mode, THE Power_Doc_Generator SHALL regenerate the MCP tool list Generated_Region from the MCP_Tool_Inventory.
2. WHEN the Power_Doc_Generator runs in Write_Mode, THE Power_Doc_Generator SHALL regenerate the hook list and hook count Generated_Region from the Hook_Source.
3. WHEN the Power_Doc_Generator runs in Write_Mode, THE Power_Doc_Generator SHALL regenerate the steering file table Generated_Region from the Steering_Index.
4. WHEN the Power_Doc_Generator runs in Write_Mode, THE Power_Doc_Generator SHALL regenerate the module overview table Generated_Region from the Module_Source.
5. IF a Source_Of_Truth file cannot be read or cannot be parsed, THEN THE Power_Doc_Generator SHALL report an error identifying the affected file path and the failure cause AND SHALL exit with a non-zero status.
6. IF a Source_Of_Truth file cannot be read or cannot be parsed during Write_Mode, THEN THE Power_Doc_Generator SHALL leave POWER.md byte-for-byte unchanged.

### Requirement 2: Preserve hand-written prose around generated regions

**User Story:** As a Developer, I want hand-written prose outside generated regions preserved, so that I can edit narrative content without it being overwritten by the generator.

#### Acceptance Criteria

1. THE Power_Doc_Generator SHALL delimit each Generated_Region with a begin Marker_Comment and an end Marker_Comment that carry a region identifier that is unique among all Generated_Regions in POWER.md.
2. WHEN the Power_Doc_Generator runs in Write_Mode, THE Power_Doc_Generator SHALL replace only the content between the begin Marker_Comment and the end Marker_Comment of each Generated_Region.
3. WHEN the Power_Doc_Generator runs in Write_Mode, THE Power_Doc_Generator SHALL leave all content outside every Generated_Region byte-for-byte unchanged.
4. IF an expected Generated_Region's begin or end Marker_Comment is missing from POWER.md, THEN THE Power_Doc_Generator SHALL report which region identifier is missing, SHALL leave POWER.md byte-for-byte unchanged, and SHALL exit with a non-zero status.
5. IF a begin Marker_Comment appears without a matching end Marker_Comment for the same region identifier, THEN THE Power_Doc_Generator SHALL report the mismatched region identifier, SHALL leave POWER.md byte-for-byte unchanged, and SHALL exit with a non-zero status.
6. IF an end Marker_Comment for a region identifier appears before its matching begin Marker_Comment for the same region identifier in POWER.md, THEN THE Power_Doc_Generator SHALL report the affected region identifier, SHALL leave POWER.md byte-for-byte unchanged, and SHALL exit with a non-zero status.
7. IF more than one begin Marker_Comment carries the same region identifier in POWER.md, THEN THE Power_Doc_Generator SHALL report the duplicated region identifier, SHALL leave POWER.md byte-for-byte unchanged, and SHALL exit with a non-zero status.

### Requirement 3: Verify mode detects drift without modifying files

**User Story:** As a Developer, I want a verify mode that reports drift without changing files, so that CI can gate merges and I can check status locally.

#### Acceptance Criteria

1. WHEN the Power_Doc_Generator runs in Verify_Mode, THE Power_Doc_Generator SHALL perform a byte-for-byte comparison of the content it produces for each Generated_Region against the corresponding region in the committed POWER.md.
2. IF one or more Generated_Region entries in the committed POWER.md differ from the generated content, THEN THE Power_Doc_Generator SHALL report, in its output, the identifier of every drifted region and the total count of drifted regions, AND SHALL terminate with exit status 1.
3. WHEN every Generated_Region matches the generated content exactly, THE Power_Doc_Generator SHALL report a success indication in its output AND SHALL terminate with exit status 0.
4. WHILE running in Verify_Mode, THE Power_Doc_Generator SHALL NOT create, modify, or delete POWER.md or any other file on disk.
5. IF Drift is detected in Verify_Mode, THEN THE Power_Doc_Generator SHALL include in its output the exact, runnable command that regenerates the affected sections.
6. IF the committed POWER.md does not exist or cannot be read when running in Verify_Mode, THEN THE Power_Doc_Generator SHALL report an error indicating that POWER.md is missing or unreadable AND SHALL terminate with a non-zero exit status without modifying any file.
7. IF a Generated_Region that the generator produces is absent from the committed POWER.md, THEN THE Power_Doc_Generator SHALL treat the region as drifted, report the missing region identifier, AND SHALL terminate with exit status 1.

### Requirement 4: Idempotent and deterministic generation

**User Story:** As a Developer, I want generation to be idempotent and deterministic, so that repeated runs produce stable output and verify mode is reliable.

#### Acceptance Criteria

1. WHEN the Power_Doc_Generator runs in Write_Mode twice in succession against byte-for-byte identical Source_Of_Truth content, THE Power_Doc_Generator SHALL produce POWER.md content after the second run that is byte-for-byte identical to the content produced after the first run.
2. WHEN the Power_Doc_Generator runs in Write_Mode immediately followed by Verify_Mode against Source_Of_Truth content that is byte-for-byte unchanged between the two runs, THE Power_Doc_Generator SHALL report success in Verify_Mode and exit with status code zero.
3. IF the Power_Doc_Generator runs in Verify_Mode and detects that the existing POWER.md content within any Generated_Region differs by one or more bytes from the content Write_Mode would produce for the current Source_Of_Truth, THEN THE Power_Doc_Generator SHALL report failure indicating the differing Generated_Region, exit with a non-zero status code, and leave POWER.md unmodified.
4. THE Power_Doc_Generator SHALL order entries within each Generated_Region by a total ordering derived solely from Source_Of_Truth content, applying a deterministic tie-breaking key so that entries with otherwise equal sort values always appear in the same relative order across runs.
5. THE Power_Doc_Generator SHALL exclude environment-dependent values (including current timestamps, locale-specific formatting, and filesystem enumeration order) from Generated_Region content, such that output depends only on Source_Of_Truth content.

### Requirement 5: CommonMark-compliant and Kiro-compatible output

**User Story:** As a Developer, I want generated output to pass existing markdown validation and remain Kiro-compatible, so that the power continues to ship valid documentation.

#### Acceptance Criteria

1. WHEN the Power_Doc_Generator runs in Write_Mode, THE Power_Doc_Generator SHALL produce POWER.md content that passes `validate_commonmark.py`.
2. THE Marker_Comment SHALL be expressed as a CommonMark HTML comment so that rendered POWER.md hides the marker text and so that the Power_Doc_Generator can re-locate every Generated_Region by its Marker_Comment on subsequent runs.
3. WHERE a Generated_Region contains a reference to a repository file, THE Power_Doc_Generator SHALL emit references compatible with Kiro's `#[[file:...]]` include syntax using a path relative to the repository root.
4. IF a Generated_Region would reference a repository file that does not exist, THEN THE Power_Doc_Generator SHALL report the missing referenced file path AND SHALL exit with a non-zero status.
5. WHEN the Power_Doc_Generator runs in Write_Mode, THE Power_Doc_Generator SHALL terminate POWER.md with exactly one trailing line-feed newline.
6. WHEN the Power_Doc_Generator runs in Write_Mode, THE Power_Doc_Generator SHALL write POWER.md with Unix line endings, containing no carriage-return line terminators.
7. IF the content the Power_Doc_Generator would write fails `validate_commonmark.py` validation, THEN THE Power_Doc_Generator SHALL leave POWER.md unchanged, perform no partial write, report the validation failure, and exit with a non-zero status.

### Requirement 6: Standard-library-only implementation under the power distribution model

**User Story:** As a Developer, I want the generator implemented with stdlib-only Python under `senzing-bootcamp/`, so that it complies with the power's distribution and dependency constraints.

#### Acceptance Criteria

1. THE Power_Doc_Generator SHALL reside as a `snake_case.py` module under `senzing-bootcamp/scripts/`.
2. THE Power_Doc_Generator SHALL import only Python standard-library modules at module top level, except that PyYAML MAY be imported where YAML files are parsed, consistent with `validate_dependencies.py`.
3. WHEN the Power_Doc_Generator is executed under CPython 3.11, 3.12, or 3.13, THE Power_Doc_Generator SHALL complete without raising an unhandled exception and without an `ImportError` for any non-standard-library module other than the permitted PyYAML import.
4. THE tests for the Power_Doc_Generator SHALL reside as `test_*.py` modules under `senzing-bootcamp/tests/`.
5. THE Power_Doc_Generator SHALL expose a `main(argv=None)` entry point with an `argparse` command-line interface.
6. WHEN `main(argv=None)` completes the requested operation successfully, THE Power_Doc_Generator SHALL return process exit status 0.
7. IF `main(argv=None)` receives invalid command-line arguments or encounters an operation failure, THEN THE Power_Doc_Generator SHALL terminate with a non-zero process exit status and emit an error message to standard error indicating the cause of failure, without writing partial or corrupted output files.

### Requirement 7: CI verification gate integration

**User Story:** As a Developer, I want the verify gate wired into CI, so that any drift fails the build before merge.

#### Acceptance Criteria

1. THE CI_Pipeline SHALL run the Power_Doc_Generator in Verify_Mode as a step within the `validate` job of `.github/workflows/validate-power.yml`, sequenced before the test-execution step.
2. IF the Power_Doc_Generator reports Drift in Verify_Mode during a CI run, THEN THE CI_Pipeline SHALL terminate the affected matrix job with a non-success (failed) status and SHALL prevent the workflow from reporting overall success.
3. WHEN the Power_Doc_Generator reports no Drift in Verify_Mode during a CI run, THE CI_Pipeline SHALL complete the Verify_Mode step with a success status and proceed to the subsequent step.
4. WHEN the Power_Doc_Generator Verify_Mode step fails in CI, THE CI_Pipeline SHALL emit the exact regeneration command as an error-level message in the job log output.
5. THE Power_Doc_Generator Verify_Mode step SHALL execute independently on each Python version in the existing CI matrix (3.11, 3.12, 3.13), and each matrix job SHALL report its Verify_Mode result regardless of the outcome of other matrix jobs.

### Requirement 8: Developer ergonomics

**User Story:** As a Developer, I want one command to regenerate and one command to verify, so that the workflow is simple and discoverable.

#### Acceptance Criteria

1. WHEN the Power_Doc_Generator is invoked in Write_Mode, THE Power_Doc_Generator SHALL regenerate all in-scope Generated_Regions (the MCP tool list, the hook list and hook count, the steering file table, and the module overview table) in POWER.md within a single invocation, without requiring a separate invocation per region.
2. WHEN the Power_Doc_Generator is invoked in Verify_Mode, THE Power_Doc_Generator SHALL verify all in-scope Generated_Regions (the MCP tool list, the hook list and hook count, the steering file table, and the module overview table) in POWER.md within a single invocation, without requiring a separate invocation per region.
3. WHERE the Power_Doc_Generator is invoked without an explicit mode argument, THE Power_Doc_Generator SHALL default to Write_Mode, consistent with the existing `sync_hook_registry.py` convention.
4. WHEN the Power_Doc_Generator is invoked with an explicit Verify_Mode argument, THE Power_Doc_Generator SHALL operate in Verify_Mode instead of the default Write_Mode.
5. THE Power_Doc_Generator SHALL document both its Write_Mode (regenerate) command invocation and its Verify_Mode (verify) command invocation in `senzing-bootcamp/scripts/README.md`.
6. IF the Power_Doc_Generator is invoked with an unrecognized mode argument, THEN THE Power_Doc_Generator SHALL report an error identifying the invalid argument and SHALL exit with a non-zero status.

### Requirement 9: MCP tool list region content

**User Story:** As a Developer, I want the MCP tool list region to reflect the canonical inventory exactly, so that the existing tool-inventory gate and the new generator agree.

#### Acceptance Criteria

1. WHEN the Power_Doc_Generator regenerates the MCP tool list Generated_Region, THE Power_Doc_Generator SHALL list each tool name defined in `ALL_TOOLS` from the MCP_Tool_Inventory exactly once, with no tool from `ALL_TOOLS` omitted and no listed entry that is not a member of `ALL_TOOLS`.
2. WHEN the Power_Doc_Generator regenerates the MCP tool list Generated_Region, THE Power_Doc_Generator SHALL order the listed tools by a deterministic key derived from `ALL_TOOLS` such that two successive regenerations against unchanged MCP_Tool_Inventory content produce identical ordering.
3. WHEN the Power_Doc_Generator regenerates the MCP tool list Generated_Region, THE Power_Doc_Generator SHALL produce content for which `check_mcp_tool_inventory()` in `validate_power.py` reports success.
4. IF the MCP_Tool_Inventory `TOTAL_COUNT` differs from the number of tools in `ALL_TOOLS`, THEN THE Power_Doc_Generator SHALL report an error identifying both the `TOTAL_COUNT` value and the counted number of tools in `ALL_TOOLS`, SHALL leave POWER.md unchanged, and SHALL exit with a non-zero status.

### Requirement 10: Hook region content

**User Story:** As a Developer, I want the hook region to reflect the actual hook files, so that the hook count and hook names never go stale.

#### Acceptance Criteria

1. WHEN the Power_Doc_Generator regenerates the hook Generated_Region, THE Power_Doc_Generator SHALL list exactly one entry for each `hooks/*.kiro.hook` file discovered in the Hook_Source, ordered by a deterministic key derived from the Hook_Source.
2. WHEN the Power_Doc_Generator regenerates the hook Generated_Region, THE Power_Doc_Generator SHALL state a hook count equal to the number of `hooks/*.kiro.hook` files discovered in the Hook_Source.
3. WHERE a hook is categorized as critical in `hooks/hook-categories.yaml`, THE Power_Doc_Generator SHALL mark the corresponding hook entry as critical in the hook Generated_Region.
4. IF a hook name listed in `hooks/hook-categories.yaml` has no corresponding `hooks/*.kiro.hook` file in the Hook_Source, THEN THE Power_Doc_Generator SHALL report the inconsistency identifying the hook name and SHALL exit with a non-zero status.
5. IF a discovered `hooks/*.kiro.hook` file is absent from every category list in `hooks/hook-categories.yaml`, THEN THE Power_Doc_Generator SHALL report the inconsistency identifying the hook name and SHALL exit with a non-zero status.

### Requirement 11: Steering file table region content

**User Story:** As a Developer, I want the steering file table region to reflect the steering index, so that steering file listings and token counts never go stale.

#### Acceptance Criteria

1. WHEN the Power_Doc_Generator regenerates the steering file table Generated_Region, THE Power_Doc_Generator SHALL list exactly the steering files recorded in the Steering_Index, emitting one table entry per recorded steering file with no duplicate and no omitted entries.
2. WHEN the Power_Doc_Generator regenerates the steering file table Generated_Region, THE Power_Doc_Generator SHALL emit, for each listed steering file, the token-count value recorded for that steering file in the Steering_Index.
3. WHEN the Power_Doc_Generator regenerates the steering file table Generated_Region, THE Power_Doc_Generator SHALL emit, for each listed steering file, the size-category value recorded for that steering file in the Steering_Index.
4. WHERE the Steering_Index records a budget total, THE Power_Doc_Generator SHALL emit that budget total in the steering file table Generated_Region as the value recorded in the Steering_Index, unchanged.
5. IF a steering file recorded in the Steering_Index is missing its token-count or size-category value, THEN THE Power_Doc_Generator SHALL report the affected steering file and the missing value and SHALL exit with a non-zero status.

### Requirement 12: Module overview table region content

**User Story:** As a Developer, I want the module overview table region to reflect the module source, so that module numbers and names never go stale.

#### Acceptance Criteria

1. WHEN the Power_Doc_Generator regenerates the module overview table Generated_Region, THE Power_Doc_Generator SHALL emit exactly one table row for every module recorded in the Module_Source, omitting no recorded module and adding no module that is not recorded in the Module_Source.
2. WHEN the Power_Doc_Generator regenerates the module overview table Generated_Region, THE Power_Doc_Generator SHALL emit, for each listed module, the module number and the module name exactly as recorded in the Module_Source.
3. WHEN the Power_Doc_Generator regenerates the module overview table Generated_Region, THE Power_Doc_Generator SHALL order the module rows by module number in ascending numeric order from lowest to highest.
4. WHEN the Power_Doc_Generator regenerates the module overview table Generated_Region, THE Power_Doc_Generator SHALL emit a module count equal to the number of module rows listed, which SHALL equal the number of modules recorded in the Module_Source.
5. IF a module recorded in the Module_Source is missing its module number or its module name, THEN THE Power_Doc_Generator SHALL report an error identifying the offending module and the missing field, SHALL leave POWER.md unchanged, and SHALL exit with a non-zero status.
