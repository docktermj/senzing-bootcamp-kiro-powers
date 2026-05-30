# Design Document: Session Persistence

## Overview

This design addresses reliable preference persistence, session resume behavior, graceful recovery from corrupted state, and clear context-reset communication for the Senzing bootcamp power. The bootcamp spans 11 modules across multiple sessions; bootcampers must never re-answer preference questions, and context limitations must be communicated transparently.

The implementation builds on the existing `preferences_utils.py` (schema validation, custom YAML parser) and `progress_utils.py` (step checkpointing) scripts, extending them with a dedicated preference writer component and a context reset message formatter. The session resume steering file (`session-resume.md`) already handles preference loading; this design formalizes the contract and adds recovery logic.

**Key design decisions:**
- **Stdlib-only Python** for all scripts (no PyYAML dependency for the preference writer)
- **Custom minimal YAML parser** already exists in `preferences_utils.py` — reuse it for reading; write YAML using simple string formatting (the schema is flat/shallow enough)
- **Atomic writes** via write-to-temp-then-rename pattern for crash safety
- **Steering-driven behavior** for agent-facing rules (context reset phrasing, session resume flow)

## Architecture

```mermaid
graph TD
    subgraph "Agent Layer (Steering)"
        SR[session-resume.md]
        CRA[agent-context-management.md]
    end

    subgraph "Script Layer (Python)"
        PW[Preference Writer<br/>write_preference()]
        PR[Preference Reader<br/>load_preferences()]
        CRF[Context Reset Formatter<br/>format_context_reset()]
        PV[Preferences Validator<br/>validate_preferences_schema()]
    end

    subgraph "Data Layer (Files)"
        PREF[config/bootcamp_preferences.yaml]
        PROG[config/bootcamp_progress.json]
    end

    SR -->|reads| PR
    SR -->|writes via| PW
    CRA -->|generates message via| CRF
    CRF -->|reads| PROG
    PW -->|writes| PREF
    PR -->|reads| PREF
    PV -->|validates| PREF
    PW -->|validates before write| PV
```

The architecture separates concerns into three layers:
1. **Steering layer** — defines agent behavior rules (when to write, what to say)
2. **Script layer** — pure functions for file I/O, validation, and message formatting
3. **Data layer** — YAML/JSON files persisted in `config/`

## Components and Interfaces

### 1. Preference Writer (`write_preference`)

**Location:** `senzing-bootcamp/scripts/preferences_utils.py` (extend existing module)

```python
def write_preference(
    key: str,
    value: str | bool | dict | list,
    preferences_path: str = "config/bootcamp_preferences.yaml",
) -> WriteResult:
    """Write a single preference field atomically.

    Reads existing file (if any), merges the new key-value pair,
    validates the result, and writes atomically via temp file + rename.

    Args:
        key: The preference field name (must be in KNOWN_TOP_LEVEL_KEYS).
        value: The value to persist. None values are treated as deletion
               (the key is removed from the file rather than stored as null).
        preferences_path: Path to the preferences YAML file.

    Returns:
        WriteResult with success status and optional error message.
    """
```

```python
@dataclass
class WriteResult:
    success: bool
    error: str | None = None
```

**Behavior:**
- If `value` is `None`, remove the key from the file (requirement 6.2)
- Read existing file → merge → validate schema → write atomically
- On filesystem error, preserve original file and return error (requirement 6.6)
- File must remain valid YAML and under 10 KB (requirement 6.4)

### 2. Preference Reader (`load_preferences`)

**Location:** `senzing-bootcamp/scripts/preferences_utils.py` (extend existing module)

```python
@dataclass
class LoadResult:
    preferences: dict | None
    missing_required: list[str]
    error: str | None = None

def load_preferences(
    preferences_path: str = "config/bootcamp_preferences.yaml",
    required_fields: tuple[str, ...] = ("language", "track", "verbosity"),
) -> LoadResult:
    """Load and validate preferences from the YAML file.

    Args:
        preferences_path: Path to the preferences YAML file.
        required_fields: Fields that must be present for a complete session.

    Returns:
        LoadResult with parsed preferences, list of missing required fields,
        and optional error message if file is missing/corrupt.
    """
```

**Behavior:**
- File missing → `LoadResult(preferences=None, missing_required=[...], error="File not found")`
- Invalid YAML → `LoadResult(preferences=None, missing_required=[...], error="Invalid YAML: ...")`
- Valid but incomplete → `LoadResult(preferences={...}, missing_required=["track"], error=None)`
- Fully valid → `LoadResult(preferences={...}, missing_required=[], error=None)`

### 3. Context Reset Formatter (`format_context_reset`)

**Location:** `senzing-bootcamp/scripts/preferences_utils.py` (new function in same module)

```python
@dataclass
class ContextResetMessage:
    message: str
    module_number: int
    step_identifier: str | int | None
    continuation_phrase: str

def format_context_reset(
    progress_path: str = "config/bootcamp_progress.json",
) -> ContextResetMessage:
    """Generate a context reset message from current progress state.

    Reads the progress file to determine current module and step,
    then formats a message containing:
    1. Technical reason (context memory full)
    2. Immediacy clarification (can start new chat right now)
    3. Progress reassurance (all work saved in project files)
    4. Continuation instruction with quoted phrase

    The message is at most 4 sentences, contains no temporal delay language,
    and includes no questions.

    Args:
        progress_path: Path to the progress JSON file.

    Returns:
        ContextResetMessage with the formatted message and metadata.
    """
```

**Forbidden phrases** (requirement 4.6):
```python
FORBIDDEN_TEMPORAL_PHRASES: tuple[str, ...] = (
    "come back later",
    "come back tomorrow",
    "take a break",
    "try again in a while",
    "when you're ready",
    "try again later",
    "wait a moment",
    "give it some time",
)
```

### 4. Language Steering Mapper

**Location:** `senzing-bootcamp/scripts/preferences_utils.py` (new function)

```python
LANGUAGE_STEERING_MAP: dict[str, str] = {
    "python": "lang-python.md",
    "java": "lang-java.md",
    "csharp": "lang-csharp.md",
    "c#": "lang-csharp.md",
    "rust": "lang-rust.md",
    "typescript": "lang-typescript.md",
}

def resolve_language_steering(language: str) -> str | None:
    """Map a language preference value to its steering file name.

    Args:
        language: The persisted language value (case-insensitive).

    Returns:
        Steering file name (e.g., "lang-python.md") or None if unrecognized.
    """
```

### 5. Session Resume Summary Formatter

**Location:** `senzing-bootcamp/scripts/preferences_utils.py` (new function)

```python
def format_resume_summary(
    language: str,
    track: str,
    verbosity: str,
) -> str:
    """Format a 1-2 sentence session resume confirmation.

    Args:
        language: Active programming language.
        track: Active bootcamp track.
        verbosity: Active verbosity level.

    Returns:
        Summary string of at most 2 sentences.
    """
```

## Data Models

### Preferences File Schema (`config/bootcamp_preferences.yaml`)

```yaml
# All fields optional — absent means "not yet set"
language: python              # string
track: core_bootcamp          # string
verbosity: standard           # string
conversation_style:           # string | dict
  verbosity_preset: standard
  question_framing: moderate
  tone: conversational
  pacing: one_concept_per_turn
deployment_target: local      # string
cloud_provider: aws           # string
database_type: sqlite         # string
mapping_verbosity: verbose    # string: "verbose" | "concise"
hooks_installed:              # list[str]
  - ask-bootcamper
  - code-style-check
pacing_overrides: null        # string (absent when not set)
```

**Constraints:**
- Maximum file size: 10 KB
- Format: valid YAML parseable by the custom `parse_yaml()` function
- No null-valued keys stored (absent = not set)
- Round-trip equivalence: `parse_yaml(write(prefs)) == prefs` for all valid inputs

### Progress File Schema (`config/bootcamp_progress.json`)

Already defined in `progress_utils.py`. The context reset formatter reads:
- `current_module: int` (1–11)
- `current_step: int | str | None`
- `modules_completed: list[int]`

### WriteResult / LoadResult / ContextResetMessage

Defined as `@dataclass` instances above. These are the return types for the public API functions.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Preference Write Round-Trip

*For any* valid preference key-value pair from the schema, writing it to the preferences file and then reading the file back SHALL produce a dict containing that key with an identical value (same type and content).

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 3.5, 6.5**

### Property 2: Field Preservation on Update

*For any* valid preferences file containing N fields, writing a single new or updated preference field SHALL preserve all other existing fields with their original values unchanged.

**Validates: Requirements 1.6, 6.3**

### Property 3: No Null Fields Written

*For any* write operation where the value is None, the resulting preferences file SHALL NOT contain that key. For any write operation where the value is non-None, the file SHALL contain only keys with non-None values.

**Validates: Requirements 6.2**

### Property 4: Schema Validation Correctness

*For any* dict conforming to the preferences schema (valid types, valid enum values, known keys only), the validator SHALL return zero errors. *For any* dict containing at least one schema violation (unknown key, wrong type, invalid enum value), the validator SHALL return at least one error.

**Validates: Requirements 6.1, 3.2, 6.4**

### Property 5: Missing Required Field Detection

*For any* valid preferences dict with a random non-empty subset of required fields (language, track, verbosity) removed, the loader SHALL report exactly those removed fields as missing and preserve all other loaded values.

**Validates: Requirements 3.3**

### Property 6: Language Steering Mapping

*For any* supported language string (case-insensitive), the mapping function SHALL return a non-None steering file name. *For any* string not in the supported language set, the mapping function SHALL return None.

**Validates: Requirements 2.4, 2.5**

### Property 7: Session Resume Summary Format

*For any* combination of language, track, and verbosity strings, the formatted resume summary SHALL contain all three values and consist of at most 2 sentences.

**Validates: Requirements 2.2**

### Property 8: Context Reset Message Completeness

*For any* valid progress state (module 1–11, any valid step), the formatted context reset message SHALL contain: (a) a technical reason referencing conversation memory, (b) an immediacy statement, (c) a progress reassurance statement, (d) a quoted continuation phrase, and (e) the current module number.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.7, 5.1, 5.2, 5.3**

### Property 9: Context Reset Message Constraints

*For any* generated context reset message, the message SHALL NOT contain any forbidden temporal phrases AND SHALL NOT contain question marks or input requests. The message SHALL be at most 4 sentences.

**Validates: Requirements 4.6, 5.2, 5.4**

## Error Handling

| Scenario | Component | Behavior |
|----------|-----------|----------|
| Preferences file missing | Preference Reader | Return `LoadResult` with `error="File not found"`, all required fields listed as missing |
| Preferences file unreadable (permissions) | Preference Reader | Return `LoadResult` with `error="Permission denied: ..."` |
| Invalid YAML in preferences | Preference Reader | Return `LoadResult` with `error="Invalid YAML: <parse error>"`, all required fields missing |
| Write fails (disk full, permissions) | Preference Writer | Preserve original file unchanged, return `WriteResult(success=False, error="...")` |
| Write would exceed 10 KB | Preference Writer | Reject write, return `WriteResult(success=False, error="File would exceed 10 KB limit")` |
| Unknown preference key | Preference Writer | Reject write, return `WriteResult(success=False, error="Unknown key: ...")` |
| Progress file missing | Context Reset Formatter | Use fallback: module=1, step=None |
| Progress file corrupt JSON | Context Reset Formatter | Use fallback: module=1, step=None, note in message |

**Atomic write strategy:**
1. Write to `config/.bootcamp_preferences.yaml.tmp`
2. Validate the temp file is valid YAML and under 10 KB
3. Rename temp file to `config/bootcamp_preferences.yaml` (atomic on POSIX)
4. On Windows, use `os.replace()` which is atomic

**Error reporting:** All errors are returned as structured `WriteResult`/`LoadResult` objects. The steering layer translates these into bootcamper-facing messages.

## Testing Strategy

### Property-Based Tests (Hypothesis)

**Library:** Hypothesis (already in use across the project)
**Configuration:** `@settings(max_examples=100)` minimum per property test
**Location:** `senzing-bootcamp/tests/test_session_persistence_properties.py`

Each property from the Correctness Properties section maps to a single Hypothesis test:

| Property | Test Function | Strategy |
|----------|--------------|----------|
| 1: Write Round-Trip | `test_preference_write_round_trip` | Generate random valid key-value pairs from schema |
| 2: Field Preservation | `test_field_preservation_on_update` | Generate full preferences dict, pick random field to update |
| 3: No Null Fields | `test_no_null_fields_written` | Generate preferences with random None values |
| 4: Schema Validation | `test_schema_validation_correctness` | Generate valid and invalid dicts |
| 5: Missing Field Detection | `test_missing_required_field_detection` | Generate valid prefs, remove random required fields |
| 6: Language Mapping | `test_language_steering_mapping` | Generate supported and unsupported language strings |
| 7: Resume Summary Format | `test_resume_summary_format` | Generate random language/track/verbosity strings |
| 8: Message Completeness | `test_context_reset_message_completeness` | Generate random valid progress states |
| 9: Message Constraints | `test_context_reset_message_constraints` | Generate random valid progress states |

**Tag format:** Each test is annotated with:
```python
# Feature: session-persistence, Property N: <property text>
```

### Unit Tests (Example-Based)

**Location:** `senzing-bootcamp/tests/test_session_persistence_unit.py`

- File creation when preferences file does not exist (requirement 1.7)
- Filesystem error handling with mocked I/O (requirements 1.8, 6.6)
- Specific language mapping examples (Python to lang-python.md)
- Edge case: empty preferences file
- Edge case: preferences file with only comments

### Integration Tests

**Location:** `senzing-bootcamp/tests/test_session_persistence_integration.py`

- Full session resume flow: write preferences, simulate new session, load, verify
- Context reset message generation with real progress file
- Steering file content validation (forbidden phrases not present in templates)

### Hypothesis Strategies

```python
@st.composite
def st_preference_key_value(draw):
    """Generate a random valid preference key-value pair."""
    ...

@st.composite
def st_valid_preferences(draw):
    """Generate a complete valid preferences dict."""
    ...

@st.composite
def st_progress_state(draw):
    """Generate a valid progress state (module + step)."""
    ...
```
