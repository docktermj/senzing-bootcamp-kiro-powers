# Design Document

## Overview

The `progress_dashboard.py` script is a standalone Python CLI tool that reads bootcamp progress, preferences, and module dependency data to generate a self-contained HTML dashboard at `docs/progress/dashboard.html`. It follows a pipeline architecture: parse inputs → compute state → render HTML. The script uses Python 3.11+ stdlib only, has no imports from other project scripts, and produces a single HTML file with inline CSS that works offline in any browser.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  CLI Layer  │────▶│   Parsers    │────▶│  Computation    │────▶│   Renderer   │
│  (argparse) │     │ JSON + YAML  │     │  (statuses,     │     │  (HTML gen)  │
│             │     │              │     │   next steps,   │     │              │
└─────────────┘     └──────────────┘     │   artifacts)    │     └──────┬───────┘
                                         └─────────────────┘            │
                                                                        ▼
                                                               ┌────────────────┐
                                                               │  HTML Output   │
                                                               │  (self-cont.)  │
                                                               └────────────────┘
```

**Data flow:**
1. `main()` parses CLI args, resolves defaults relative to script's parent directory
2. Validates all input files exist (exit 1 if missing)
3. Parsers produce typed dataclass instances from JSON/YAML
4. Computation layer derives module statuses, next steps, and artifacts
5. Renderer produces a complete self-contained HTML5 string
6. Output directory is created if needed, HTML is written, exit 0

## Components and Interfaces

### 1. CLI Layer (`main` function)

```python
def main(argv: list[str] | None = None) -> None:
    """Entry point with argparse CLI.

    Args:
        argv: Command-line arguments (None for sys.argv).
    """
```

**CLI Interface:**
```
usage: progress_dashboard.py [-h] [--progress PATH] [--preferences PATH]
                             [--dependencies PATH] [--output PATH]

Generate a self-contained HTML progress dashboard.

optional arguments:
  --progress PATH      Path to bootcamp_progress.json
                       (default: config/bootcamp_progress.json)
  --preferences PATH   Path to bootcamp_preferences.yaml
                       (default: config/bootcamp_preferences.yaml)
  --dependencies PATH  Path to module-dependencies.yaml
                       (default: config/module-dependencies.yaml)
  --output PATH        Output path for dashboard HTML
                       (default: docs/progress/dashboard.html)
```

### 2. Minimal YAML Parser

```python
def parse_yaml(text: str) -> dict:
    """Parse a minimal YAML subset into a nested dict.

    Supports:
    - Scalar key: value pairs (strings, integers, null)
    - Lists with '- item' syntax
    - Nested mappings via indentation
    - Comments (lines starting with #)
    - Quoted strings and bare values
    - null keyword → None

    Args:
        text: YAML content as a string.

    Returns:
        Parsed dictionary.

    Raises:
        ValueError: If YAML structure is unparseable.
    """
```

### 3. Parser Functions

```python
def parse_progress(path: Path) -> ProgressData:
    """Parse the progress JSON file.

    Args:
        path: Path to bootcamp_progress.json.

    Returns:
        ProgressData with extracted fields.

    Raises:
        SystemExit: If JSON is invalid (exits with code 1).
    """


def parse_preferences(path: Path) -> PreferencesData:
    """Parse the preferences YAML file using the minimal parser.

    Args:
        path: Path to bootcamp_preferences.yaml.

    Returns:
        PreferencesData with extracted fields (None for missing/null values).
    """


def parse_dependencies(path: Path) -> DependencyData:
    """Parse the module dependencies YAML file.

    Args:
        path: Path to module-dependencies.yaml.

    Returns:
        DependencyData with modules and gates extracted.
    """
```

### 4. Computation Functions

```python
def compute_module_statuses(
    dependency_data: DependencyData,
    progress: ProgressData,
) -> dict[int, str]:
    """Compute status for each module: 'completed', 'in-progress', or 'not-started'.

    Args:
        dependency_data: Parsed dependency graph.
        progress: Parsed progress data.

    Returns:
        Dict mapping module number to status string.
    """


def compute_next_steps(
    dependency_data: DependencyData,
    progress: ProgressData,
) -> list[NextStep]:
    """Compute dependency-aware next steps.

    A module is a valid next step if:
    1. All entries in its `requires` array are in `modules_completed`
    2. It is not in `modules_completed`
    3. It is not the `current_module`

    Args:
        dependency_data: Parsed dependency graph.
        progress: Parsed progress data.

    Returns:
        List of NextStep recommendations with gate requirements.
    """


def extract_artifacts(progress: ProgressData) -> list[Artifact]:
    """Extract artifact references from step_history.

    Scans step_history entries for values that reference file paths
    or output artifacts, grouping them by module number.

    Args:
        progress: Parsed progress data.

    Returns:
        List of Artifact objects sorted by module number.
    """
```

### 5. HTML Renderer

```python
def render_dashboard(
    progress: ProgressData,
    preferences: PreferencesData,
    dependency_data: DependencyData,
    module_statuses: dict[int, str],
    next_steps: list[NextStep],
    artifacts: list[Artifact],
) -> str:
    """Render the complete self-contained HTML dashboard.

    Produces valid HTML5 with all CSS inline in a <style> element.
    No external resources are referenced.

    Args:
        progress: Parsed progress data.
        preferences: Parsed preferences data.
        dependency_data: Parsed dependency graph.
        module_statuses: Module number → status mapping.
        next_steps: Computed next step recommendations.
        artifacts: Extracted artifacts list.

    Returns:
        Complete HTML string ready to write to file.
    """
```

## Data Models

```python
@dataclass
class ProgressData:
    """Parsed progress file data."""
    current_module: int | None
    modules_completed: list[int]
    current_step: str | None
    language: str | None
    step_history: dict[str, dict]


@dataclass
class PreferencesData:
    """Parsed preferences file data."""
    language: str | None
    track: str | None
    database_type: str | None
    deployment_target: str | None


@dataclass
class ModuleInfo:
    """A single module from the dependency graph."""
    number: int
    name: str
    requires: list[int]


@dataclass
class GateInfo:
    """A gate transition requirement."""
    from_module: int
    to_module: int
    requirements: list[str]


@dataclass
class DependencyData:
    """Parsed dependency graph data."""
    modules: list[ModuleInfo]
    gates: list[GateInfo]


@dataclass
class Artifact:
    """An artifact produced during a module step."""
    module_number: int
    step_key: str
    reference: str


@dataclass
class NextStep:
    """A recommended next module with gate info."""
    module: ModuleInfo
    gate_requirements: list[str]
```

### Input File Formats

**Progress File (JSON):**
```json
{
  "current_module": 4,
  "modules_completed": [1, 2, 3],
  "current_step": "4.2",
  "language": "python",
  "step_history": {
    "1.1": {"status": "complete", "artifact": "docs/problem_statement.md"},
    "2.1": {"status": "complete", "artifact": "src/senzing_config.py"}
  }
}
```

**Preferences File (YAML):**
```yaml
language: python
track: core_bootcamp
database_type: sqlite
deployment_target: null
```

**Dependencies File (YAML):**
```yaml
modules:
  1:
    name: "Business Problem"
    requires: []
  2:
    name: "SDK Setup"
    requires: []
  3:
    name: "System Verification"
    requires: [2]

gates:
  "1->2":
    requires:
      - "Problem documented, sources identified"
```

## Error Handling

| Condition | Behavior |
|-----------|----------|
| Input file does not exist | Print `"Error: file not found: {path}"` to stderr, exit 1 |
| Progress file has invalid JSON | Print `"Error: invalid JSON in {path}: {detail}"` to stderr, exit 1 |
| Preferences/dependencies YAML parse error | Print `"Error: cannot parse {path}: {detail}"` to stderr, exit 1 |
| Output directory does not exist | Create it with `os.makedirs(exist_ok=True)` |
| Empty modules_completed | Render dashboard with 0% progress, all modules as not-started |
| Null/absent preference fields | Display "Not set" in the preferences card |
| No artifacts in step_history | Display "No artifacts produced yet" message |
| All modules completed | Display congratulatory completion message |
| No next steps available (blocked) | Display message about blocking prerequisites |

## Testing Strategy

**Dual approach:**
- **Property-based tests** (Hypothesis): Validate universal properties across generated inputs for parsing, computation, and rendering logic.
- **Example-based unit tests**: Verify CLI defaults, specific edge cases (empty inputs, all-complete state), and static analysis checks (no external imports, script pattern compliance).

Test file: `senzing-bootcamp/tests/test_progress_dashboard_properties.py`

Strategies will generate:
- Random valid progress JSON (`st_progress_data`)
- Random valid preferences YAML content (`st_preferences_data`)
- Random dependency graphs with modules and gates (`st_dependency_data`)
- Random completion states for a given graph (`st_completion_state`)

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Exit Code Correctness

*For any* set of input file paths, the script SHALL exit with code 0 if and only if all required input files exist and contain parseable content; otherwise it SHALL exit with code 1.

**Validates: Requirements 1.6, 1.7, 2.4**

### Property 2: Progress Data Parsing Preservation

*For any* valid progress JSON containing `current_module`, `modules_completed`, `current_step`, `language`, and `step_history` fields, parsing SHALL produce a ProgressData object where every integer in the source `modules_completed` array appears in the parsed result, and every artifact reference in `step_history` is extractable from the parsed result.

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 3: YAML Preferences Parsing Round-Trip

*For any* valid preferences YAML file containing `language`, `track`, `database_type`, and `deployment_target` scalar values (including `null`), the minimal YAML parser SHALL extract values such that for each field, the parsed value equals the original value (or None for `null`/absent fields).

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 4: Dependency Graph Parsing Completeness

*For any* valid dependencies YAML file containing a `modules` section with numbered entries (each having `name` and `requires`) and a `gates` section, parsing SHALL produce a DependencyData where every module number, name, and requires list from the source is present in the result, and every gate transition is captured.

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 5: Module Status Classification Correctness

*For any* dependency graph and progress state, every module SHALL be classified as exactly one of: "completed" (if its number is in `modules_completed`), "in-progress" (if it equals `current_module` and is not completed), or "not-started" (otherwise); and the rendered HTML SHALL contain a visual indicator for each module matching its classification.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

### Property 6: Next Steps Computation Correctness

*For any* dependency graph and set of completed modules, the computed next steps SHALL be exactly the set of modules where (a) all entries in the module's `requires` array are present in `modules_completed`, AND (b) the module is not in `modules_completed`, AND (c) the module is not the `current_module`.

**Validates: Requirements 7.1, 7.2**

### Property 7: Preferences Card Rendering Completeness

*For any* preferences data (with values being non-null strings or None), the rendered HTML preferences card SHALL contain each of the four fields (`language`, `track`, `database_type`, `deployment_target`) with either the actual value or the text "Not set" for None/absent values.

**Validates: Requirements 3.3, 8.1, 8.2, 8.3, 8.4, 8.5**

### Property 8: Self-Contained HTML Output

*For any* valid set of input files, the rendered HTML output SHALL contain a `<!DOCTYPE html>` declaration, a `<style>` element with CSS, and SHALL NOT contain any external resource references (no `<link rel="stylesheet">` with external `href`, no `<script src="http...">` tags).

**Validates: Requirements 9.1, 9.2, 9.3**

### Property 9: Artifact Display Correctness

*For any* progress data with a non-empty `step_history` containing artifact references, every artifact reference present in the source data SHALL appear in the rendered HTML output.

**Validates: Requirements 6.1**
