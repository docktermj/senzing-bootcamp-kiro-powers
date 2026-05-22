# Requirements Document

## Introduction

Schema validation for `config/bootcamp_preferences.yaml`. This feature adds a `preferences_utils.py` module defining the canonical schema for all known preference keys, a custom minimal YAML parser (no PyYAML), and a strict validator that rejects undefined keys. A companion `validate_preferences_ci.py` script runs in CI to catch schema violations before merge. The architecture mirrors the existing `progress_utils.py` + `validate_progress_ci.py` pattern.

## Glossary

- **Preferences_File**: The YAML file at `config/bootcamp_preferences.yaml` storing bootcamper choices persisted during onboarding and ongoing sessions.
- **Preferences_Schema**: A Python dataclass in `preferences_utils.py` defining all valid keys, their expected types, and default values.
- **Preferences_Validator**: The `validate_preferences_schema()` function in `preferences_utils.py` that checks a parsed preferences dict against the Preferences_Schema.
- **Minimal_YAML_Parser**: A custom stdlib-only YAML parser in `preferences_utils.py` capable of parsing the subset of YAML used by the Preferences_File (scalars, lists, nested dicts).
- **CI_Script**: The `validate_preferences_ci.py` script that runs schema self-consistency checks and validates a Preferences_File, exiting 0 on success and 1 on failure.
- **Strict_Mode**: The validation mode where any key not defined in the Preferences_Schema causes a validation error.
- **Known_Keys**: The complete set of keys recognized by the Preferences_Schema (see Requirement 2 for the full list).

## Requirements

### Requirement 1: Strict Schema Validation

**User Story:** As a bootcamp developer, I want the preferences validator to reject any key not defined in the schema, so that typos and undocumented keys are caught before they reach users.

#### Acceptance Criteria

1. WHEN the Preferences_Validator encounters a top-level key not present in the Known_Keys set, THE Preferences_Validator SHALL return an error identifying the unrecognized key.
2. WHEN the Preferences_Validator encounters a nested key within `conversation_style` not present in the defined sub-keys (`verbosity_preset`, `question_framing`, `tone`, `pacing`), THE Preferences_Validator SHALL return an error identifying the unrecognized nested key.
3. WHEN the Preferences_Validator encounters a nested key within `production_specs` not present in the defined sub-keys (`cpu_cores`, `ram_gb`, `storage_type`, `database`), THE Preferences_Validator SHALL return an error identifying the unrecognized nested key.
4. THE Preferences_Validator SHALL collect all errors without short-circuiting and return the complete list of violations.

### Requirement 2: Known Keys and Type Definitions

**User Story:** As a bootcamp developer, I want a single authoritative schema defining all valid preference keys and their types, so that validation is consistent and discoverable.

#### Acceptance Criteria

1. THE Preferences_Schema SHALL define the following top-level keys with their expected types:
   - `language`: `str | None`
   - `track`: `str | None`
   - `deployment_target`: `str | None`
   - `cloud_provider`: `str | None`
   - `database_type`: `str`
   - `verbosity`: `str | None`
   - `conversation_style`: `str | dict | None`
   - `mapping_verbosity`: `str | None`
   - `hooks_installed`: `list[str]`
   - `pacing_overrides`: `str | None`
   - `license`: `str | None`
   - `license_guidance_deferred`: `bool | None`
   - `skip_graduation`: `bool | None`
   - `team_member_id`: `str | None`
   - `scoop_installed_during_onboarding`: `bool | None`
   - `runtimes_installed_during_onboarding`: `list[dict] | None`
   - `prerequisite_installation_deferred`: `bool | None`
   - `detail_level`: `str | None`
   - `hardware_target`: `str | None`
   - `production_specs`: `dict | None`
2. WHEN `conversation_style` is a dict, THE Preferences_Validator SHALL validate that the dict contains only the sub-keys `verbosity_preset`, `question_framing`, `tone`, and `pacing`, each of type `str`.
3. WHEN `runtimes_installed_during_onboarding` is a list, THE Preferences_Validator SHALL validate that each element is a dict containing `name` (str) and `version` (str).
4. WHEN `production_specs` is a dict, THE Preferences_Validator SHALL validate that the dict contains only the sub-keys `cpu_cores` (int), `ram_gb` (int), `storage_type` (str), and `database` (str).
5. WHEN `hooks_installed` is present, THE Preferences_Validator SHALL validate that the value is a list where each element is a string.

### Requirement 3: Type Validation

**User Story:** As a bootcamp developer, I want type mismatches to produce clear error messages, so that I can quickly identify and fix corrupted preferences.

#### Acceptance Criteria

1. WHEN a key has a value whose type does not match the expected type defined in the Preferences_Schema, THE Preferences_Validator SHALL return an error stating the key name, expected type, and actual type.
2. WHEN `database_type` is present, THE Preferences_Validator SHALL validate that the value is a non-empty string.
3. WHEN `mapping_verbosity` is a string, THE Preferences_Validator SHALL validate that the value is one of `verbose`, `concise`, or `null`.
4. WHEN `hardware_target` is a string, THE Preferences_Validator SHALL validate that the value is one of `current_machine` or `different_server`.
5. WHEN `conversation_style` is a dict and `verbosity_preset` is present, THE Preferences_Validator SHALL validate that the value is one of `concise`, `standard`, `detailed`, or `custom`.
6. WHEN `conversation_style` is a dict and `question_framing` is present, THE Preferences_Validator SHALL validate that the value is one of `minimal`, `moderate`, or `full`.
7. WHEN `conversation_style` is a dict and `tone` is present, THE Preferences_Validator SHALL validate that the value is one of `concise`, `conversational`, or `detailed`.
8. WHEN `conversation_style` is a dict and `pacing` is present, THE Preferences_Validator SHALL validate that the value is one of `one_concept_per_turn` or `grouped_concepts`.

### Requirement 4: Custom Minimal YAML Parser

**User Story:** As a bootcamp developer, I want a stdlib-only YAML parser that handles the preferences file format, so that the validation toolchain has no third-party dependencies.

#### Acceptance Criteria

1. THE Minimal_YAML_Parser SHALL parse scalar values: strings (quoted and unquoted), integers, booleans (`true`/`false`), and `null`.
2. THE Minimal_YAML_Parser SHALL parse flat key-value pairs at the top level.
3. THE Minimal_YAML_Parser SHALL parse nested dicts (indented key-value pairs under a parent key).
4. THE Minimal_YAML_Parser SHALL parse lists denoted by `- ` prefix items.
5. THE Minimal_YAML_Parser SHALL parse lists of dicts (list items containing nested key-value pairs).
6. THE Minimal_YAML_Parser SHALL ignore comment lines (lines starting with `#` after optional whitespace).
7. THE Minimal_YAML_Parser SHALL ignore blank lines.
8. IF the Minimal_YAML_Parser encounters content it cannot parse, THEN THE Minimal_YAML_Parser SHALL raise a `ValueError` with the line number and a description of the problem.

### Requirement 5: CI Validation Script

**User Story:** As a bootcamp developer, I want a CI script that validates the preferences file on every PR, so that schema violations are caught automatically.

#### Acceptance Criteria

1. THE CI_Script SHALL accept an optional positional argument for the path to a preferences YAML file, defaulting to `config/bootcamp_preferences.yaml`.
2. WHEN the specified file exists, THE CI_Script SHALL parse the file using the Minimal_YAML_Parser and validate the result using the Preferences_Validator.
3. WHEN the specified file does not exist, THE CI_Script SHALL validate a built-in minimal sample to confirm the schema and parser are self-consistent.
4. THE CI_Script SHALL perform a schema self-consistency check verifying that the Known_Keys set is non-empty and the built-in sample passes validation.
5. WHEN validation passes, THE CI_Script SHALL print "Schema validation passed" and exit with code 0.
6. WHEN validation fails, THE CI_Script SHALL print all errors to stderr and exit with code 1.
7. THE CI_Script SHALL use `argparse` for CLI argument handling with a `main(argv=None)` signature.

### Requirement 6: Backward Compatibility

**User Story:** As a bootcamp developer, I want the validator to accept legacy preferences files that lack newer keys, so that existing bootcamper files remain valid.

#### Acceptance Criteria

1. THE Preferences_Validator SHALL treat all keys as optional except `database_type`.
2. WHEN a key defined in the Preferences_Schema is absent from the preferences dict, THE Preferences_Validator SHALL not report an error for that key.
3. WHEN `database_type` is absent from the preferences dict, THE Preferences_Validator SHALL report an error indicating the required key is missing.

### Requirement 7: Module Architecture

**User Story:** As a bootcamp developer, I want the preferences validation code organized as a utils module plus a CI script, so that the architecture mirrors the existing progress validation pattern.

#### Acceptance Criteria

1. THE Preferences_Schema, Minimal_YAML_Parser, and Preferences_Validator SHALL reside in `senzing-bootcamp/scripts/preferences_utils.py`.
2. THE CI_Script SHALL reside in `senzing-bootcamp/scripts/validate_preferences_ci.py`.
3. THE CI_Script SHALL import from `preferences_utils.py` using the same `sys.path` pattern used by `validate_progress_ci.py`.
4. THE `preferences_utils.py` module SHALL use only Python standard library imports (no third-party dependencies).
5. THE `validate_preferences_ci.py` script SHALL use only Python standard library imports (no third-party dependencies).
6. THE `preferences_utils.py` module SHALL follow the project script pattern: shebang, module docstring, `from __future__ import annotations`, stdlib imports, dataclass schema, argparse CLI with `main(argv=None)`, and `if __name__ == "__main__": main()` entry point.
