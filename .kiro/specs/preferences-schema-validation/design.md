# Design Document

## Overview

This feature adds schema validation for `config/bootcamp_preferences.yaml`, mirroring the existing `progress_utils.py` + `validate_progress_ci.py` pattern. It provides a canonical schema definition, a custom minimal YAML parser (stdlib-only), and a strict validator that rejects undefined keys. A companion CI script catches schema violations before merge.

## Architecture

This feature adds two Python scripts mirroring the existing `progress_utils.py` + `validate_progress_ci.py` pattern:

1. **`preferences_utils.py`** — A utility module containing the canonical preferences schema (dataclass), a custom minimal YAML parser, and a strict validator function.
2. **`validate_preferences_ci.py`** — A CI script that imports from `preferences_utils.py`, performs self-consistency checks, and validates a preferences YAML file.

Both scripts use only Python standard library imports and follow the project's established script pattern (shebang, docstring, `from __future__ import annotations`, dataclass schema, argparse CLI, `main(argv=None)` entry point).

## Components and Interfaces

### 1. `preferences_utils.py`

**Location:** `senzing-bootcamp/scripts/preferences_utils.py`

#### 1.1 Schema Constants

```python
KNOWN_TOP_LEVEL_KEYS: set[str] = {
    "language", "track", "deployment_target", "cloud_provider",
    "database_type", "verbosity", "conversation_style",
    "mapping_verbosity", "hooks_installed", "pacing_overrides",
    "license", "license_guidance_deferred", "skip_graduation",
    "team_member_id", "scoop_installed_during_onboarding",
    "runtimes_installed_during_onboarding",
    "prerequisite_installation_deferred", "detail_level",
    "hardware_target", "production_specs",
}

CONVERSATION_STYLE_KEYS: set[str] = {
    "verbosity_preset", "question_framing", "tone", "pacing",
}

PRODUCTION_SPECS_KEYS: set[str] = {
    "cpu_cores", "ram_gb", "storage_type", "database",
}

VALID_MAPPING_VERBOSITY: tuple[str, ...] = ("verbose", "concise")
VALID_HARDWARE_TARGET: tuple[str, ...] = ("current_machine", "different_server")
VALID_VERBOSITY_PRESET: tuple[str, ...] = ("concise", "standard", "detailed", "custom")
VALID_QUESTION_FRAMING: tuple[str, ...] = ("minimal", "moderate", "full")
VALID_TONE: tuple[str, ...] = ("concise", "conversational", "detailed")
VALID_PACING: tuple[str, ...] = ("one_concept_per_turn", "grouped_concepts")
```

#### 1.2 PreferencesSchema Dataclass

```python
@dataclass
class PreferencesSchema:
    """Canonical schema for bootcamp_preferences.yaml.

    Defines the expected structure and types for all fields in the preferences
    file. Only database_type is required; all other fields are optional.
    """

    database_type: str
    language: str | None = None
    track: str | None = None
    deployment_target: str | None = None
    cloud_provider: str | None = None
    verbosity: str | None = None
    conversation_style: str | dict | None = None
    mapping_verbosity: str | None = None
    hooks_installed: list[str] | None = None
    pacing_overrides: str | None = None
    license: str | None = None
    license_guidance_deferred: bool | None = None
    skip_graduation: bool | None = None
    team_member_id: str | None = None
    scoop_installed_during_onboarding: bool | None = None
    runtimes_installed_during_onboarding: list[dict] | None = None
    prerequisite_installation_deferred: bool | None = None
    detail_level: str | None = None
    hardware_target: str | None = None
    production_specs: dict | None = None
```

#### 1.3 Minimal YAML Parser

```python
def parse_yaml(text: str) -> dict:
    """Parse a minimal YAML subset into a Python dict.

    Handles:
    - Scalar values: strings (quoted/unquoted), integers, booleans, null
    - Flat key-value pairs
    - Nested dicts (indented key-value pairs)
    - Lists (- prefix items)
    - Lists of dicts (list items with nested key-value pairs)
    - Comment lines (# prefix) and blank lines (ignored)

    Args:
        text: YAML content as a string.

    Returns:
        Parsed dict.

    Raises:
        ValueError: If content cannot be parsed, with line number and description.
    """
```

The parser processes lines sequentially, tracking indentation level to determine nesting. It uses a state machine approach:
- **Top-level state**: Reads `key: value` pairs
- **Nested dict state**: Reads indented `key: value` pairs under a parent key
- **List state**: Reads `- item` lines, detecting whether items are scalars or dicts

Scalar parsing logic:
- `null`, `~`, empty value → `None`
- `true`/`false` (case-insensitive) → `bool`
- Numeric strings → `int`
- Quoted strings (`"..."` or `'...'`) → `str` with quotes stripped
- Everything else → `str`

#### 1.4 Preferences Validator

```python
def validate_preferences_schema(data: dict) -> list[str]:
    """Validate a preferences dict against the full schema.

    Performs strict validation:
    1. Rejects unknown top-level keys
    2. Validates types for all known keys
    3. Validates enum constraints for restricted fields
    4. Validates nested dict structures (conversation_style, production_specs)
    5. Validates list element structures (hooks_installed, runtimes_installed_during_onboarding)
    6. Requires database_type (only required field)

    Never short-circuits — collects all errors and returns the complete list.

    Args:
        data: Parsed preferences dict.

    Returns:
        Empty list when valid, or list of human-readable error strings.
    """
```

Validation order:
1. Check for unknown top-level keys
2. Check required key (`database_type`) is present
3. For each known key present in data:
   - Validate base type
   - Validate enum constraints (mapping_verbosity, hardware_target)
   - Validate nested structure (conversation_style, production_specs, runtimes_installed_during_onboarding, hooks_installed)

Error message format: `"{key}: expected {expected_type}, got {actual_type}"` for type errors, `"{key}: unrecognized key"` for unknown keys, `"{key}: value must be one of {allowed}, got {actual!r}"` for enum violations.

### 2. `validate_preferences_ci.py`

**Location:** `senzing-bootcamp/scripts/validate_preferences_ci.py`

```python
def main(argv: list[str] | None = None) -> None:
    """Run preferences schema CI validation.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).
    """
```

#### Flow:
1. Parse CLI args (optional path, default `config/bootcamp_preferences.yaml`)
2. Run schema self-consistency check:
   - Verify `KNOWN_TOP_LEVEL_KEYS` is non-empty
   - Verify built-in minimal sample passes validation
3. If file exists: parse with `parse_yaml()`, validate with `validate_preferences_schema()`
4. If file does not exist: validate built-in minimal sample only
5. Print results: "Schema validation passed" (exit 0) or errors to stderr (exit 1)

#### Built-in Minimal Sample:

```python
_SAMPLE_PREFERENCES: dict = {
    "database_type": "sqlite",
}
```

## Data Models

### Input: `bootcamp_preferences.yaml`

A YAML file with flat and nested key-value pairs. Only `database_type` is required. All other keys are optional. The file may contain comments and blank lines.

### Output: Validation Errors

A `list[str]` where each string is a human-readable error message. Empty list means validation passed.

### Error Categories:
| Category | Format |
|----------|--------|
| Unknown key | `"Unknown top-level key: '{key}'"` |
| Unknown nested key | `"conversation_style: unknown key '{key}'"` |
| Type mismatch | `"{key}: expected {expected}, got {actual}"` |
| Enum violation | `"{key}: must be one of {allowed}, got '{value}'"` |
| Missing required | `"Missing required key: 'database_type'"` |
| Invalid list element | `"{key}[{index}]: expected {expected}, got {actual}"` |

## Interfaces

### Public API (`preferences_utils.py`)

| Function | Signature | Description |
|----------|-----------|-------------|
| `parse_yaml` | `(text: str) -> dict` | Parse minimal YAML subset |
| `validate_preferences_schema` | `(data: dict) -> list[str]` | Validate preferences dict |

### Public Constants (`preferences_utils.py`)

| Constant | Type | Description |
|----------|------|-------------|
| `KNOWN_TOP_LEVEL_KEYS` | `set[str]` | All valid top-level keys |
| `CONVERSATION_STYLE_KEYS` | `set[str]` | Valid conversation_style sub-keys |
| `PRODUCTION_SPECS_KEYS` | `set[str]` | Valid production_specs sub-keys |
| `VALID_MAPPING_VERBOSITY` | `tuple[str, ...]` | Allowed mapping_verbosity values |
| `VALID_HARDWARE_TARGET` | `tuple[str, ...]` | Allowed hardware_target values |
| `VALID_VERBOSITY_PRESET` | `tuple[str, ...]` | Allowed verbosity_preset values |
| `VALID_QUESTION_FRAMING` | `tuple[str, ...]` | Allowed question_framing values |
| `VALID_TONE` | `tuple[str, ...]` | Allowed tone values |
| `VALID_PACING` | `tuple[str, ...]` | Allowed pacing values |
| `PreferencesSchema` | `dataclass` | Canonical schema definition |

### CLI Interface (`validate_preferences_ci.py`)

```
usage: validate_preferences_ci.py [-h] [path]

positional arguments:
  path    Path to preferences YAML file (default: config/bootcamp_preferences.yaml)
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| YAML parse error | `parse_yaml()` raises `ValueError` with line number |
| File read error (CI script) | Adds error to list, continues to report |
| Multiple validation errors | All collected, never short-circuits |
| Missing file (CI script) | Falls back to built-in sample validation |
| Schema self-consistency failure | Reports error and exits 1 |

## Testing Strategy

**Unit tests** (`test_preferences_schema_validation_unit.py`):
- Verify schema dataclass has exactly the specified fields
- Verify CI script accepts optional path argument and produces correct exit codes
- Verify specific error messages for known edge cases (empty database_type, missing required key)
- Verify built-in sample passes self-consistency check

**Property-based tests** (`test_preferences_schema_validation_properties.py`):
- Hypothesis strategies generate random valid/invalid preferences dicts
- Minimum 100 iterations per property (configured via `@settings(max_examples=20)` per project convention)
- Cover all 10 correctness properties below
- Strategies: `st_preferences_file()`, `st_corrupted_preferences_file()`, `st_yaml_text()`, `st_preferences_yaml_text()`

**Integration tests**:
- CI script end-to-end with temp files (valid and invalid YAML)
- Import verification (sys.path pattern works)

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Valid preferences validate cleanly

*For any* preferences dict containing only keys from the Known_Keys set with correctly-typed values (including random subsets of optional keys), `validate_preferences_schema()` SHALL return an empty error list.

**Validates: Requirements 2.1, 6.1, 6.2**

### Property 2: Unknown top-level keys are rejected

*For any* string not present in the Known_Keys set, when that string appears as a top-level key in a preferences dict, `validate_preferences_schema()` SHALL return a non-empty error list containing the unrecognized key name.

**Validates: Requirements 1.1**

### Property 3: Unknown nested keys are rejected

*For any* string not present in the allowed sub-key set for `conversation_style` or `production_specs`, when that string appears as a nested key within the respective parent, `validate_preferences_schema()` SHALL return a non-empty error list identifying the unrecognized nested key.

**Validates: Requirements 1.2, 1.3**

### Property 4: Type mismatches produce descriptive errors

*For any* known key whose value has a type not matching the schema definition, `validate_preferences_schema()` SHALL return a non-empty error list where at least one error message contains the key name, the expected type, and the actual type.

**Validates: Requirements 3.1, 2.2, 2.3, 2.4, 2.5**

### Property 5: Enum constraint violations are rejected

*For any* field with an enum constraint (`mapping_verbosity`, `hardware_target`, `verbosity_preset`, `question_framing`, `tone`, `pacing`) and *for any* string value not in that field's allowed set, `validate_preferences_schema()` SHALL return a non-empty error list identifying the invalid value.

**Validates: Requirements 3.3, 3.4, 3.5, 3.6, 3.7, 3.8**

### Property 6: All errors collected without short-circuiting

*For any* preferences dict containing N distinct violations (unknown keys, type mismatches, enum violations), `validate_preferences_schema()` SHALL return an error list with at least N entries.

**Validates: Requirements 1.4**

### Property 7: Missing required key detected

*For any* valid preferences dict with the `database_type` key removed, `validate_preferences_schema()` SHALL return a non-empty error list indicating the required key is missing.

**Validates: Requirements 6.3, 3.2**

### Property 8: YAML round-trip parsing

*For any* valid preferences dict (containing scalars, nested dicts, and lists as used by the preferences file format), formatting the dict as YAML text and parsing it with `parse_yaml()` SHALL produce an equivalent dict.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

### Property 9: Comments and blank lines are transparent to parsing

*For any* valid YAML text that parses successfully, inserting comment lines (starting with `#`) or blank lines at arbitrary positions SHALL not change the parsed result.

**Validates: Requirements 4.6, 4.7**

### Property 10: Malformed YAML raises ValueError with line info

*For any* text input containing syntactically invalid YAML (e.g., inconsistent indentation, malformed key-value pairs), `parse_yaml()` SHALL raise a `ValueError` whose message contains a line number.

**Validates: Requirements 4.8**
