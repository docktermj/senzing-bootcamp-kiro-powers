# Design Document: Module Dependency Graph

## Overview

Module prerequisite relationships are currently scattered across three files (`module-prerequisites.md`, `onboarding-flow.md`, and individual module steering files), creating drift risk when prerequisites change. This design introduces a single machine-readable YAML dependency graph (`config/module-dependencies.yaml`) as the authoritative source, a validation script (`scripts/validate_dependencies.py`) that checks the graph for internal consistency and cross-references it against the steering files, and reference notes in the three existing files directing maintainers to the graph.

### Key Design Decisions

1. **YAML as the source of truth** — YAML is human-readable, diff-friendly, and parseable with PyYAML (already available) or `yaml.safe_load`. The graph encodes modules, prerequisites, tracks, gates, and metadata in a single file.
2. **Validation script, not code generation** — rather than generating the steering files from the graph (which would require complex markdown templating), the script validates that the graph and steering files agree. This preserves the human-authored prose in steering files while catching drift.
3. **Topological sort for cycle detection** — Kahn's algorithm detects cycles and produces a topological ordering in O(V+E), sufficient for 11 modules.
4. **PyYAML as the only external dependency** — the validation script uses only the Python standard library plus PyYAML, consistent with other project scripts.
5. **Error vs. warning severity** — structural problems (cycles, dangling references, schema violations) are errors. Missing steering files for graph modules are errors. Informational discrepancies are warnings.

## Architecture

```mermaid
flowchart TD
    YAML[config/module-dependencies.yaml] --> VS[validate_dependencies.py]
    MP[module-prerequisites.md] --> VS
    OF[onboarding-flow.md] --> VS
    SF[module-NN-*.md files] --> VS
    VS --> CR[Cross-Reference Checks]
    VS --> SC[Structural Checks]
    VS --> SchV[Schema Validation]
    CR --> V[Violation List]
    SC --> V
    SchV --> V
    V --> Fmt[Formatter]
    Fmt --> Stdout[stdout: {level}: {description}]
    V --> Exit[Exit Code: 0 or 1]
```

## Components and Interfaces

### 1. Dependency Graph Schema (`config/module-dependencies.yaml`)

```yaml
metadata:
  version: "1.0.0"
  last_updated: "2025-01-15"

modules:
  1:
    name: "Business Problem"
    requires: []
    skip_if: null
  2:
    name: "SDK Setup"
    requires: []
    skip_if: "SDK already installed and configured"
  3:
    name: "Quick Demo"
    requires: [2]
    skip_if: null
  # ... modules 4-11

tracks:
  quick_demo:
    name: "Quick Demo"
    description: "Fastest path to see Senzing in action"
    modules: [1, 2, 3]
  fast_track:
    name: "Fast Track"
    description: "Skip to loading and querying data"
    modules: [1, 2, 6, 7]
  complete_beginner:
    name: "Complete Beginner"
    description: "Full guided path through all modules"
    modules: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
  full_production:
    name: "Full Production"
    description: "Complete path including deployment"
    modules: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

gates:
  "1->2":
    requires: ["Module 1 checkpoint complete"]
  "2->3":
    requires: ["SDK installed and verified"]
  # ... gates 3->4 through 10->11
```

### 2. Validation Script Data Structures

```python
@dataclass
class Violation:
    level: str       # "ERROR" or "WARNING"
    description: str # Human-readable description

    def format(self) -> str:
        return f"{self.level}: {self.description}"
```

### 3. Validation Functions

```python
def load_dependency_graph(path: Path) -> dict:
    """Load and parse the YAML dependency graph.
    
    Raises:
        SystemExit: If file is missing or unparseable.
    """

def validate_schema(graph: dict) -> list[Violation]:
    """Verify the graph has all required sections and fields with correct types.
    
    Checks: metadata (version, last_updated), modules (name, requires, skip_if),
    tracks (name, description, modules), gates (requires).
    """

def validate_no_cycles(graph: dict) -> list[Violation]:
    """Verify the modules section forms a DAG using topological sort (Kahn's algorithm).
    
    Reports ERROR with cycle participants if a cycle is detected.
    """

def validate_references(graph: dict) -> list[Violation]:
    """Verify all module numbers in requires, tracks, and gates exist in modules section.
    
    Reports ERROR for each dangling reference.
    """

def validate_topological_order(graph: dict) -> list[Violation]:
    """Verify each track lists modules in an order consistent with prerequisites.
    
    Reports ERROR if a track lists a module before its prerequisites.
    """

def validate_steering_files(graph: dict, steering_dir: Path) -> list[Violation]:
    """Verify every module in the graph has a corresponding module-NN-*.md file.
    
    Reports ERROR for missing steering files.
    """

def validate_prerequisites_file(graph: dict, prereqs_path: Path) -> list[Violation]:
    """Parse module-prerequisites.md and verify its table matches the graph's requires fields.
    
    Reports ERROR for each discrepancy.
    """

def validate_onboarding_flow(graph: dict, onboarding_path: Path) -> list[Violation]:
    """Parse onboarding-flow.md and verify track definitions and gate conditions match the graph.
    
    Reports ERROR for each discrepancy.
    """

def run_all_checks(graph_path: Path, steering_dir: Path) -> tuple[list[Violation], int]:
    """Run all validation checks and return (violations, exit_code)."""

def main() -> None:
    """CLI entry point. Loads graph, runs checks, prints output, exits."""
```

## Data Models

### Dependency Graph Schema

| Section | Field | Type | Required | Description |
|---------|-------|------|----------|-------------|
| `metadata` | `version` | string (semver) | Yes | Schema version |
| `metadata` | `last_updated` | string (ISO 8601) | Yes | Last modification date |
| `modules.N` | `name` | string | Yes | Human-readable module title |
| `modules.N` | `requires` | list[int] | Yes | Prerequisite module numbers |
| `modules.N` | `skip_if` | string or null | Yes | Skip condition or null |
| `tracks.key` | `name` | string | Yes | Track display name |
| `tracks.key` | `description` | string | Yes | Track description |
| `tracks.key` | `modules` | list[int] | Yes | Ordered module sequence |
| `gates.N->M` | `requires` | list[string] | Yes | Gate conditions |

### Violation Object

| Field | Type | Description |
|-------|------|-------------|
| `level` | `str` | `"ERROR"` or `"WARNING"` |
| `description` | `str` | Human-readable violation description |

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Cycle Detection Correctness

*For any* directed graph of module prerequisites, the validation script shall report an error if and only if the graph contains a cycle. When a cycle exists, the error shall identify the modules involved.

**Validates: Requirements 3.1, 6.1, 6.2**

### Property 2: Dangling Reference Detection

*For any* dependency graph, the validation script shall report an error for every module number referenced in `requires`, `tracks`, or `gates` that does not exist in the `modules` section, and shall not report an error for references that do exist.

**Validates: Requirements 3.2, 6.3, 6.4**

### Property 3: Topological Order Validation

*For any* dependency graph and track definition, the validation script shall report an error if and only if the track's module list contains a module that appears before one of its prerequisites.

**Validates: Requirements 3.3**

### Property 4: Schema Validation Completeness

*For any* YAML structure presented as a dependency graph, the validation script shall report an error for every missing required field and every field with an incorrect type, and shall not report errors for valid structures.

**Validates: Requirements 6.5, 6.6**

### Property 5: Exit Code Correctness

*For any* set of validation violations, the exit code shall be 0 if and only if there are zero error-level violations. Otherwise the exit code shall be 1.

**Validates: Requirements 4.3, 4.4**

### Property 6: Violation Output Format

*For any* `Violation` object, the formatted output string shall match the pattern `{ERROR|WARNING}: {description}`.

**Validates: Requirements 4.5**

## Error Handling

| Scenario | Handling |
|----------|----------|
| YAML file missing | Script prints `ERROR: Dependency graph not found: {path}` and exits with code 1 |
| YAML parse error | Script prints `ERROR: Cannot parse dependency graph: {reason}` and exits with code 1 |
| Steering directory missing | Script prints `ERROR: Steering directory not found: {path}` and exits with code 1 |
| Module prerequisites file missing | Script prints `WARNING: module-prerequisites.md not found, skipping cross-reference check` |
| Onboarding flow file missing | Script prints `WARNING: onboarding-flow.md not found, skipping cross-reference check` |
| Individual steering file unreadable | Validation reports `WARNING: Could not read {file}: {reason}` and continues |

## Testing Strategy

### Property-Based Tests (Hypothesis)

The validation functions are pure functions that take graph dicts and return violation lists, making them well-suited for property-based testing.

**Library:** Hypothesis (Python) — already used in the project.

**Configuration:** Minimum 100 iterations per property test (`@settings(max_examples=100)`).

**Tag format:** `Feature: module-dependency-graph, Property {N}: {title}`

| Property | Test Strategy |
|----------|---------------|
| P1: Cycle detection | Generate random directed graphs (some with cycles, some without), verify detection matches actual cyclicity |
| P2: Dangling references | Generate random graphs with references to existing and non-existing modules, verify all dangling references reported |
| P3: Topological order | Generate random graphs with tracks, verify error iff track violates prerequisite ordering |
| P4: Schema validation | Generate random YAML structures with missing/invalid fields, verify all issues reported |
| P5: Exit code | Generate random violation sets, verify exit code is 0 iff zero errors |
| P6: Violation format | Generate random Violation objects, verify formatted string matches pattern |

### Example-Based Unit Tests

| Test | What it verifies |
|------|-----------------|
| Real dependency graph parses without error | Req 3.4 |
| Real graph has all 11 modules | Req 2.1 |
| Real graph has all 4 tracks | Req 2.2 |
| Real graph has all 10 gates | Req 2.3 |
| Real graph has no cycles | Req 3.1 |
| Real graph has no dangling references | Req 3.2 |
| Steering file reference notes exist in module-prerequisites.md | Req 7.1 |
| Steering file reference notes exist in onboarding-flow.md | Req 7.2, 7.3 |

### Integration Tests

| Test | What it verifies |
|------|-----------------|
| Full validation run on real graph + steering files exits 0 | End-to-end consistency |
| Script runs with only stdlib + PyYAML | Dependency constraint (Req 4.2) |
| Summary line shows correct counts | Output format (Req 4.6) |
