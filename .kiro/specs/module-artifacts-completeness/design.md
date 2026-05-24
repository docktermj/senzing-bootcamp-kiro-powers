# Design Document

## Overview

This feature completes the `config/module-artifacts.yaml` manifest by adding Modules 1–3, introduces a "sentinel" artifact type for non-file outcomes, aligns the `requires_from` dependency graph with `module-dependencies.yaml`, and updates existing test suites to accept the new type.

The changes are confined to:
1. The YAML manifest (`config/module-artifacts.yaml`)
2. The validation script (`scripts/validate_module.py`)
3. Two test files (`tests/test_artifact_chain_integration.py`, `tests/test_artifact_dependency_tracking.py`)

## Architecture

### Component Interaction

```
module-artifacts.yaml  ──parsed by──▶  validate_module.py (parse_module_artifacts_yaml)
         │                                        │
         │                                        ▼
         │                              run_artifact_check() ──skips disk check──▶ sentinel artifacts
         │
         ├──parsed by──▶  test_artifact_chain_integration.py (_parse_artifacts_yaml)
         │                        │
         │                        ▼
         │              TestArtifactChainConsistency (type validation, graph checks)
         │              TestSteeringReferencesArtifacts (parametrized modules)
         │              TestArtifactChainContinuity (connectivity, orphan checks)
         │
         └──parsed by──▶  test_artifact_dependency_tracking.py (parse_module_artifacts_yaml)
                                  │
                                  ▼
                        TestManifestModuleNumbers (range 1-11)
                        TestManifestFileValidity (type validation)
```

### Data Flow

Module 1 and Module 2 are root nodes (no `requires_from`). Module 3 depends on Module 2. Module 4 gains a new dependency on Module 1 in addition to its existing dependencies. Module 6 gains a new dependency on Module 2. The full graph flows:

```
Module 1 ──▶ Module 4 ──▶ Module 5 ──▶ Module 6 ──▶ Module 7 ──▶ ... ──▶ Module 11
Module 2 ──▶ Module 3                       ▲
Module 2 ───────────────────────────────────┘
```

## Components and Interfaces

### 1. Module-Artifacts YAML Manifest

**File:** `senzing-bootcamp/config/module-artifacts.yaml`

Add three new module entries (1, 2, 3) before the existing Module 4 entry. Update Module 4 and Module 6 `requires_from` to include new upstream dependencies.

```yaml
modules:
  1:
    produces:
      - path: "docs/business_problem.md"
        type: file
        description: "Business problem definition document"
        required: true
      - path: "config/data_sources.yaml"
        type: file
        description: "Data source registry identifying sources to resolve"
        required: true
    requires_from: {}

  2:
    produces:
      - path: "database/G2C.db"
        type: file
        description: "SQLite database for Senzing engine"
        required: true
      - path: "config/engine_config.json"
        type: file
        description: "Senzing engine configuration"
        required: true
      - path: "config/bootcamp_preferences.yaml"
        type: file
        description: "Bootcamp user preferences (language, style)"
        required: true
      - path: "sdk_installed"
        type: sentinel
        description: "Senzing SDK installed and importable"
        required: true
    requires_from: {}

  3:
    produces:
      - path: "src/system_verification/"
        type: directory
        description: "System verification scripts and outputs"
        required: true
      - path: "docs/progress/MODULE_3_COMPLETE.md"
        type: file
        description: "Module 3 completion marker"
        required: true
    requires_from:
      2: ["database/G2C.db"]

  4:
    produces:
      # ... existing entries unchanged ...
    requires_from:
      1: ["config/data_sources.yaml"]
      # Note: existing requires_from entries for Module 4 are preserved

  6:
    produces:
      # ... existing entries unchanged ...
    requires_from:
      2: ["database/G2C.db"]
      5: ["data/transformed/"]
```

### 2. Validation Script Update

**File:** `senzing-bootcamp/scripts/validate_module.py`

#### Type Validation

The `parse_module_artifacts_yaml` function already parses the `type` field. The `run_artifact_check` function needs to skip disk-existence checks for sentinel artifacts.

```python
VALID_ARTIFACT_TYPES = {"file", "directory", "sentinel"}


def check_artifact_on_disk(artifact_path: str, artifact_type: str) -> tuple[bool, bool]:
    """Check if an artifact exists on disk.

    Sentinel artifacts are always considered present (they represent
    non-file system state like 'SDK installed').

    Args:
        artifact_path: Relative path to the artifact.
        artifact_type: The artifact type ("file", "directory", or "sentinel").

    Returns:
        Tuple of (exists, is_directory).
    """
    if artifact_type == "sentinel":
        return (True, False)

    p = Path(artifact_path)
    if artifact_path.endswith("/"):
        if not p.exists() or not p.is_dir():
            return (False, True)
        has_files = any(True for _ in p.iterdir())
        return (has_files, True)
    else:
        return (p.exists() and p.is_file(), False)
```

#### Updated `run_artifact_check`

The function must resolve the artifact type from the source module's `produces` list before calling `check_artifact_on_disk`:

```python
def run_artifact_check(module_num: int) -> bool:
    # ... existing setup ...
    for source_module, paths in sorted(requires_from.items()):
        source_data = modules.get(source_module, {})
        for artifact_path in paths:
            # Resolve artifact type from source module's produces
            artifact_type = "file"  # default
            for prod in source_data.get("produces", []):
                if prod["path"] == artifact_path:
                    artifact_type = prod.get("type", "file")
                    break

            exists, _is_dir = check_artifact_on_disk(artifact_path, artifact_type)
            # ... rest of reporting logic ...
```

### 3. Chain Integration Tests Update

**File:** `senzing-bootcamp/tests/test_artifact_chain_integration.py`

#### Type Validation Fix

Update `test_produces_items_have_valid_structure` to accept "sentinel":

```python
def test_produces_items_have_valid_structure(self):
    """Every produces entry must have path, type, and description."""
    modules = _parse_artifacts_yaml()
    errors = []

    for mod_num, info in modules.items():
        for i, item in enumerate(info["produces"]):
            if not item.get("path"):
                errors.append(f"Module {mod_num} produces[{i}]: missing path")
            if not item.get("type"):
                errors.append(f"Module {mod_num} produces[{i}]: missing type")
            if item.get("type") not in ("file", "directory", "sentinel"):
                errors.append(
                    f"Module {mod_num} produces[{i}]: type must be "
                    f"'file', 'directory', or 'sentinel', got '{item.get('type')}'"
                )

    assert not errors, "Invalid produces entries:\n" + "\n".join(errors)
```

#### Parametrization Update

Update `test_steering_mentions_required_input_paths` to cover modules 1–11:

```python
@pytest.mark.parametrize("module_num", list(range(1, 12)))
def test_steering_mentions_required_input_paths(self, module_num: int):
    # ... existing logic unchanged ...
```

#### Connectivity Update

Update `TestArtifactChainContinuity.test_chain_is_connected` to allow Module 1 and Module 2 as root nodes:

```python
def test_chain_is_connected(self):
    """Every module with requires_from connects back to a producing module."""
    modules = _parse_artifacts_yaml()
    root_modules = {1, 2}  # Modules with no dependencies
    for mod_num in sorted(modules.keys()):
        if mod_num in root_modules:
            continue
        info = modules[mod_num]
        assert info["requires_from"], (
            f"Module {mod_num} has no requires_from — "
            f"it's disconnected from the artifact chain"
        )
```

### 4. Dependency Tracking Tests Update

**File:** `senzing-bootcamp/tests/test_artifact_dependency_tracking.py`

#### Type Validation Fix

Update `test_manifest_produces_have_required_fields` to accept "sentinel":

```python
def test_manifest_produces_have_required_fields(self) -> None:
    """Every produces entry has path, type, description, and required."""
    manifest = load_manifest()
    modules = manifest.get("modules", {})
    for mod_num, mod_data in modules.items():
        for artifact in mod_data.get("produces", []):
            assert "path" in artifact, (
                f"Module {mod_num}: produces entry missing 'path'"
            )
            assert "type" in artifact, (
                f"Module {mod_num}: produces entry missing 'type'"
            )
            assert artifact["type"] in ("file", "directory", "sentinel"), (
                f"Module {mod_num}: invalid type '{artifact['type']}'"
            )
            assert "description" in artifact, (
                f"Module {mod_num}: produces entry missing 'description'"
            )
            assert "required" in artifact, (
                f"Module {mod_num}: produces entry missing 'required'"
            )
```

### 5. Interface Summary

#### `parse_module_artifacts_yaml(path: str) -> dict`

No signature change. The returned structure gains new module keys (1, 2, 3) and the `type` field can now be `"sentinel"` in addition to `"file"` and `"directory"`.

#### `check_artifact_on_disk(artifact_path: str, artifact_type: str) -> tuple[bool, bool]`

**Changed signature** — adds `artifact_type` parameter. When `artifact_type == "sentinel"`, returns `(True, False)` without touching the filesystem.

#### `VALID_ARTIFACT_TYPES`

New module-level constant: `{"file", "directory", "sentinel"}`.

## Data Models

### Artifact Entry (produces item)

```python
@dataclass
class ArtifactEntry:
    path: str          # Filesystem path (file/directory) or logical ID (sentinel)
    type: str          # One of: "file", "directory", "sentinel"
    description: str   # Human-readable description
    required: bool     # Whether this artifact is mandatory for downstream modules
```

### Module Entry

```python
@dataclass
class ModuleEntry:
    produces: list[ArtifactEntry]
    requires_from: dict[int, list[str]]  # source_module -> [artifact_paths]
```

### Valid Artifact Types

| Type | Path Semantics | Disk Check | Example |
|------|---------------|------------|---------|
| `file` | Relative filesystem path | Checks file exists | `docs/business_problem.md` |
| `directory` | Relative directory path (trailing `/`) | Checks dir exists and non-empty | `data/raw/` |
| `sentinel` | Logical identifier (no filesystem meaning) | Skipped — always "present" | `sdk_installed` |

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Unknown artifact type in YAML | Validation script rejects with error message listing valid types |
| Sentinel artifact in `requires_from` | `run_artifact_check` skips disk check, reports as "✅ present" |
| Module references non-existent source module | Existing `test_requires_from_sources_exist_in_graph` catches this |
| Circular dependency introduced | Existing `test_dependency_graph_is_acyclic` catches this |
| Module > 2 missing `requires_from` | New connectivity test fails with descriptive message |

## Testing Strategy

### Property-Based Tests (Hypothesis)

Property tests validate universal invariants across generated inputs:

1. **Type validation exhaustiveness** — Generate random strings and verify the validator accepts exactly the three valid types
2. **Sentinel disk-check bypass** — Generate random sentinel artifact entries and verify no filesystem I/O occurs
3. **Non-root module dependency invariant** — Sample modules from the manifest and verify modules > 2 always have requires_from

Configuration: `@settings(max_examples=100)` per property test.

### Example-Based Unit Tests

Unit tests verify specific structural assertions about the manifest:

- Module 1 produces exactly `docs/business_problem.md` and `config/data_sources.yaml`
- Module 2 produces the four expected artifacts including the sentinel
- Module 3 has correct produces and requires_from entries
- Module 4 requires_from includes Module 1
- Module 6 requires_from includes Module 2
- Chain integration tests pass with all 11 modules

### Integration Tests

- Run the full `test_artifact_chain_integration.py` suite to verify graph consistency
- Run `validate_module.py --artifacts N` for modules 1–6 to verify the script handles new entries

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Artifact type validation is exhaustive

*For any* string value used as an artifact type, the validation logic SHALL accept it if and only if it is one of "file", "directory", or "sentinel". All other strings SHALL be rejected.

**Validates: Requirements 4.1, 4.3, 6.1, 6.2**

### Property 2: Sentinel artifacts bypass filesystem validation

*For any* artifact entry with type "sentinel", the disk-checking logic SHALL report the artifact as present without performing any filesystem I/O. The path field is treated as a logical identifier.

**Validates: Requirements 4.2**

### Property 3: Non-root modules have upstream dependencies

*For any* module in the Artifact_Manifest with a module number greater than 2, the module SHALL have at least one entry in its `requires_from` mapping. Only Modules 1 and 2 are permitted to have empty `requires_from`.

**Validates: Requirements 7.2**
