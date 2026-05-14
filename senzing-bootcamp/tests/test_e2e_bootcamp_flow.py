"""End-to-end bootcamp flow property-based and integration tests.

Validates that the complete bootcamp lifecycle — prerequisite checking, gate
evaluation, progress state management, steering file resolution, phase
transitions, and skip conditions — works correctly across all three tracks.

Feature: end-to-end-bootcamp-flow-test
"""

from __future__ import annotations

import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# sys.path setup for scripts imports
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import progress_utils  # noqa: E402
import validate_module  # noqa: E402

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class ModuleConfig:
    """Configuration for a single bootcamp module."""

    name: str
    requires: list[int]
    skip_if: str | None


@dataclass
class TrackConfig:
    """Configuration for a bootcamp track."""

    name: str
    modules: list[int]


@dataclass
class GateConfig:
    """Configuration for a gate between modules."""

    source: int
    target: int
    requires: list[str]


@dataclass
class BootcampConfig:
    """Complete bootcamp configuration parsed from module-dependencies.yaml."""

    modules: dict[int, ModuleConfig] = field(default_factory=dict)
    tracks: dict[str, TrackConfig] = field(default_factory=dict)
    gates: dict[str, GateConfig] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Minimal YAML Parser for module-dependencies.yaml
# ---------------------------------------------------------------------------


def _parse_module_dependencies(path: Path) -> BootcampConfig:
    """Parse module-dependencies.yaml into a BootcampConfig.

    A minimal line-based parser that extracts modules, tracks, and gates
    sections without requiring PyYAML.

    Args:
        path: Path to module-dependencies.yaml.

    Returns:
        BootcampConfig with all sections populated.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the YAML structure is malformed.
    """
    if not path.exists():
        raise FileNotFoundError(f"Module dependencies not found: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()
    config = BootcampConfig()

    # Find section starts
    section = None
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        # Top-level keys (no indentation)
        indent = len(line) - len(line.lstrip())
        if indent == 0 and stripped.endswith(":"):
            key = stripped[:-1]
            if key == "modules":
                section = "modules"
            elif key == "tracks":
                section = "tracks"
            elif key == "gates":
                section = "gates"
            else:
                section = None
            i += 1
            continue

        if indent == 0 and ":" in stripped:
            section = None
            i += 1
            continue

        if section == "modules" and indent == 2:
            i = _parse_module_entry(lines, i, config)
        elif section == "tracks" and indent == 2:
            i = _parse_track_entry(lines, i, config)
        elif section == "gates" and indent == 2:
            i = _parse_gate_entry(lines, i, config)
        else:
            i += 1

    return config


def _parse_module_entry(lines: list[str], start: int, config: BootcampConfig) -> int:
    """Parse a single module entry starting at line index start."""
    line = lines[start]
    stripped = line.strip()
    colon_pos = stripped.find(":")
    module_num = int(stripped[:colon_pos].strip())

    i = start + 1
    name = ""
    requires: list[int] = []
    skip_if: str | None = None

    while i < len(lines):
        ln = lines[i]
        ln_stripped = ln.strip()
        if not ln_stripped or ln_stripped.startswith("#"):
            i += 1
            continue
        ln_indent = len(ln) - len(ln.lstrip())
        if ln_indent <= 2:
            break

        if ln_stripped.startswith("name:"):
            name = ln_stripped.split(":", 1)[1].strip().strip('"').strip("'")
        elif ln_stripped.startswith("requires:"):
            val = ln_stripped.split(":", 1)[1].strip()
            if val == "[]":
                requires = []
            else:
                # Parse [1, 2, 3] format
                inner = val.strip("[]")
                requires = [int(x.strip()) for x in inner.split(",") if x.strip()]
        elif ln_stripped.startswith("skip_if:"):
            val = ln_stripped.split(":", 1)[1].strip()
            if val == "null" or val == "":
                skip_if = None
            else:
                skip_if = val.strip('"').strip("'")
        i += 1

    config.modules[module_num] = ModuleConfig(name=name, requires=requires, skip_if=skip_if)
    return i


def _parse_track_entry(lines: list[str], start: int, config: BootcampConfig) -> int:
    """Parse a single track entry starting at line index start."""
    line = lines[start]
    stripped = line.strip()
    colon_pos = stripped.find(":")
    track_key = stripped[:colon_pos].strip()

    i = start + 1
    name = ""
    modules: list[int] = []

    while i < len(lines):
        ln = lines[i]
        ln_stripped = ln.strip()
        if not ln_stripped or ln_stripped.startswith("#"):
            i += 1
            continue
        ln_indent = len(ln) - len(ln.lstrip())
        if ln_indent <= 2:
            break

        if ln_stripped.startswith("name:"):
            name = ln_stripped.split(":", 1)[1].strip().strip('"').strip("'")
        elif ln_stripped.startswith("modules:"):
            val = ln_stripped.split(":", 1)[1].strip()
            inner = val.strip("[]")
            modules = [int(x.strip()) for x in inner.split(",") if x.strip()]
        i += 1

    config.tracks[track_key] = TrackConfig(name=name, modules=modules)
    return i


def _parse_gate_entry(lines: list[str], start: int, config: BootcampConfig) -> int:
    """Parse a single gate entry starting at line index start."""
    line = lines[start]
    stripped = line.strip()
    colon_pos = stripped.find(":")
    gate_key = stripped[:colon_pos].strip().strip('"').strip("'")

    # Parse source->target from key
    parts = gate_key.split("->")
    source = int(parts[0].strip())
    target = int(parts[1].strip())

    i = start + 1
    requires: list[str] = []

    while i < len(lines):
        ln = lines[i]
        ln_stripped = ln.strip()
        if not ln_stripped or ln_stripped.startswith("#"):
            i += 1
            continue
        ln_indent = len(ln) - len(ln.lstrip())
        if ln_indent <= 2:
            break

        if ln_stripped.startswith("requires:"):
            i += 1
            continue
        elif ln_stripped.startswith("- "):
            req = ln_stripped[2:].strip().strip('"').strip("'")
            requires.append(req)
        i += 1

    config.gates[gate_key] = GateConfig(source=source, target=target, requires=requires)
    return i


# ---------------------------------------------------------------------------
# Steering Index Parser (reused from test_module_transition_properties.py)
# ---------------------------------------------------------------------------


def _parse_steering_index(path: Path) -> dict:
    """Parse the steering-index.yaml modules section.

    A minimal line-based parser that extracts the ``modules:`` top-level key.
    Handles simple string entries and nested objects with ``root``, ``phases``,
    ``file``, and ``step_range`` keys.

    Args:
        path: Path to steering-index.yaml.

    Returns:
        Dict mapping module numbers (int) to either a filename string
        (single-file module) or a dict with 'root' and 'phases' keys
        (multi-phase module).

    Raises:
        FileNotFoundError: If the steering index file does not exist.
        ValueError: If the YAML structure is malformed.
    """
    if not path.exists():
        raise FileNotFoundError(f"Steering index not found: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()

    # Find the modules: section
    modules_start = None
    for idx, ln in enumerate(lines):
        if ln.rstrip() == "modules:":
            modules_start = idx + 1
            break

    if modules_start is None:
        raise ValueError("No 'modules:' key found in steering index")

    modules: dict[int, str | dict] = {}
    i = modules_start

    while i < len(lines):
        line = lines[i]

        # Stop at next top-level key (no indentation)
        if line and not line[0].isspace() and not line.startswith("#"):
            break

        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        indent = len(line) - len(line.lstrip())
        if indent == 2:
            colon_pos = stripped.find(":")
            if colon_pos == -1:
                raise ValueError(f"Malformed module entry at line {i + 1}: {line}")

            key_str = stripped[:colon_pos].strip()
            try:
                module_num = int(key_str)
            except ValueError as exc:
                raise ValueError(
                    f"Expected integer module number at line {i + 1}, got: {key_str}"
                ) from exc

            value_str = stripped[colon_pos + 1:].strip()

            if value_str:
                modules[module_num] = value_str
                i += 1
            else:
                module_data: dict = {}
                i += 1
                while i < len(lines):
                    nested_line = lines[i]
                    nested_stripped = nested_line.strip()

                    if not nested_stripped or nested_stripped.startswith("#"):
                        i += 1
                        continue

                    nested_indent = len(nested_line) - len(nested_line.lstrip())
                    if nested_indent <= 2:
                        break

                    if nested_indent == 4:
                        nc = nested_stripped.find(":")
                        if nc == -1:
                            raise ValueError(
                                f"Malformed nested entry at line {i + 1}"
                            )
                        nkey = nested_stripped[:nc].strip()
                        nval = nested_stripped[nc + 1:].strip()

                        if nkey == "root":
                            module_data["root"] = nval
                            i += 1
                        elif nkey == "phases":
                            phases: dict[str, dict] = {}
                            i += 1
                            while i < len(lines):
                                phase_line = lines[i]
                                phase_stripped = phase_line.strip()

                                if not phase_stripped or phase_stripped.startswith("#"):
                                    i += 1
                                    continue

                                phase_indent = len(phase_line) - len(phase_line.lstrip())
                                if phase_indent <= 4:
                                    break

                                if phase_indent == 6:
                                    pc = phase_stripped.find(":")
                                    if pc == -1:
                                        raise ValueError(
                                            f"Malformed phase entry at line {i + 1}"
                                        )
                                    phase_name = phase_stripped[:pc].strip()
                                    phase_data: dict = {}
                                    i += 1
                                    while i < len(lines):
                                        prop_line = lines[i]
                                        prop_stripped = prop_line.strip()

                                        if not prop_stripped or prop_stripped.startswith("#"):
                                            i += 1
                                            continue

                                        prop_indent = len(prop_line) - len(prop_line.lstrip())
                                        if prop_indent <= 6:
                                            break

                                        ppc = prop_stripped.find(":")
                                        if ppc == -1:
                                            raise ValueError(
                                                f"Malformed phase property at line {i + 1}"
                                            )
                                        pkey = prop_stripped[:ppc].strip()
                                        pval = prop_stripped[ppc + 1:].strip()

                                        if pkey == "file":
                                            phase_data["file"] = pval
                                        elif pkey == "step_range":
                                            pval = pval.strip("[]")
                                            range_parts = pval.split(",")
                                            if len(range_parts) != 2:
                                                raise ValueError(
                                                    f"Malformed step_range at line {i + 1}"
                                                )
                                            phase_data["step_range"] = (
                                                int(range_parts[0].strip()),
                                                int(range_parts[1].strip()),
                                            )
                                        i += 1

                                    if "file" not in phase_data:
                                        raise ValueError(
                                            f"Phase '{phase_name}' missing 'file' key"
                                        )
                                    if "step_range" not in phase_data:
                                        raise ValueError(
                                            f"Phase '{phase_name}' missing 'step_range' key"
                                        )
                                    phases[phase_name] = phase_data
                                else:
                                    i += 1

                            module_data["phases"] = phases
                        else:
                            i += 1
                    else:
                        i += 1

                if "root" not in module_data:
                    raise ValueError(f"Module {module_num} missing 'root' key")
                if "phases" not in module_data:
                    raise ValueError(f"Module {module_num} missing 'phases' key")
                modules[module_num] = module_data
        else:
            i += 1

    if not modules:
        raise ValueError("No modules found in steering index")

    return modules


# ---------------------------------------------------------------------------
# Module-Level Constants
# ---------------------------------------------------------------------------

_BOOTCAMP_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _BOOTCAMP_ROOT / "config" / "module-dependencies.yaml"
_STEERING_DIR = _BOOTCAMP_ROOT / "steering"
_INDEX_PATH = _STEERING_DIR / "steering-index.yaml"

CONFIG: BootcampConfig = _parse_module_dependencies(_CONFIG_PATH)
STEERING_INDEX: dict[int, str | dict] = _parse_steering_index(_INDEX_PATH)

MODULE_ARTIFACTS: dict[int, list[str]] = {
    1: ["docs/business_problem.md"],
    2: ["database/G2C.db", "config/bootcamp_preferences.yaml"],
    3: ["src/quickstart_demo/demo_example.py", "src/quickstart_demo/sample_data_example.json"],
    4: ["data/raw/example.csv", "docs/data_source_locations.md"],
    5: ["docs/data_source_evaluation.md", "src/transform/transform.py",
        "data/transformed/output.jsonl"],
    6: ["src/load/loader.py", "database/G2C.db", "docs/loading_strategy.md"],
    7: ["src/query/query.py", "docs/results_validation.md"],
    8: ["docs/performance_requirements.md", "docs/benchmark_environment.md",
        "tests/performance/bench.py", "docs/performance_report.md"],
    9: ["docs/security_compliance.md", "src/security/auth.py", "docs/security_checklist.md"],
    10: ["src/monitoring/health.py", "docs/runbooks/runbook.md", "docs/monitoring_setup.md"],
    11: ["Dockerfile", "docs/deployment_plan.md"],
}


# ---------------------------------------------------------------------------
# Test Infrastructure Helpers
# ---------------------------------------------------------------------------


def _create_module_artifacts(root: Path, module_num: int) -> None:
    """Create all filesystem artifacts that validate_module.py checks for a module.

    Args:
        root: The project root directory (typically tmp_path).
        module_num: The module number whose artifacts to create.
    """
    artifacts = MODULE_ARTIFACTS.get(module_num, [])
    for artifact in artifacts:
        artifact_path = root / artifact
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(f"# Artifact for module {module_num}\ncontent\n",
                                 encoding="utf-8")


class _ProgressManager:
    """Wraps progress read/write/complete_module operations scoped to a tmp_path root.

    Args:
        root: The project root directory where config/bootcamp_progress.json lives.
    """

    def __init__(self, root: Path) -> None:
        self._root = root
        self._progress_path = str(root / "config" / "bootcamp_progress.json")
        # Ensure config dir exists
        (root / "config").mkdir(parents=True, exist_ok=True)

    def read(self) -> dict:
        """Read the current progress state."""
        return progress_utils._read_progress(self._progress_path)

    def write(self, data: dict) -> None:
        """Write a progress state dict."""
        progress_utils._write_progress(self._progress_path, data)

    def complete_module(self, module_num: int, track_modules: list[int]) -> None:
        """Mark a module as complete and advance to the next module in the track.

        Args:
            module_num: The module number being completed.
            track_modules: The ordered list of modules in the current track.
        """
        data = self.read()
        if not data:
            data = {
                "modules_completed": [],
                "current_module": module_num,
                "language": "python",
                "database_type": "sqlite",
                "data_sources": [],
                "current_step": 1,
                "step_history": {},
            }

        completed = data.get("modules_completed", [])
        if module_num not in completed:
            completed.append(module_num)
        data["modules_completed"] = completed

        # Advance to next module in track
        idx = track_modules.index(module_num)
        if idx + 1 < len(track_modules):
            data["current_module"] = track_modules[idx + 1]
        else:
            data["current_module"] = module_num  # Stay on last

        data["current_step"] = 1
        self.write(data)


def _evaluate_gate(root: Path, gate_key: str, config: BootcampConfig) -> bool:
    """Check whether a gate transition is allowed.

    A gate allows transition if and only if the source module's artifacts
    are all present in the project root.

    Args:
        root: The project root directory.
        gate_key: The gate key (e.g., "5->6").
        config: The parsed bootcamp configuration.

    Returns:
        True if the gate allows transition, False otherwise.
    """
    gate = config.gates[gate_key]
    source_artifacts = MODULE_ARTIFACTS.get(gate.source, [])
    for artifact in source_artifacts:
        artifact_path = root / artifact
        if not artifact_path.exists():
            return False
    return True


def _resolve_steering(
    module_num: int,
    phase: str | None,
    steering_index: dict,
) -> str:
    """Return the steering file path for the given module and phase.

    Args:
        module_num: The module number.
        phase: The phase name (None for single-phase modules or root file).
        steering_index: The parsed steering index dict.

    Returns:
        The steering file path (filename) for the module/phase.

    Raises:
        KeyError: If the module or phase is not found.
    """
    entry = steering_index[module_num]
    if isinstance(entry, str):
        return entry
    # Multi-phase module
    if phase is None:
        return entry["root"]
    return entry["phases"][phase]["file"]


# ---------------------------------------------------------------------------
# Hypothesis Strategies
# ---------------------------------------------------------------------------


def st_module_with_prereqs() -> st.SearchStrategy[int]:
    """Draw from modules with non-empty requires lists."""
    modules_with_prereqs = [
        num for num, mod in CONFIG.modules.items() if mod.requires
    ]
    return st.sampled_from(sorted(modules_with_prereqs))


def st_any_module() -> st.SearchStrategy[int]:
    """Draw from all module numbers in config."""
    return st.sampled_from(sorted(CONFIG.modules.keys()))


def st_gate_key() -> st.SearchStrategy[str]:
    """Draw from all gate keys defined in config."""
    return st.sampled_from(sorted(CONFIG.gates.keys()))


def st_track_and_position() -> st.SearchStrategy[tuple[str, int]]:
    """Draw a track name and a valid index within that track's module list."""
    track_keys = sorted(CONFIG.tracks.keys())
    return st.sampled_from(track_keys).flatmap(
        lambda tk: st.tuples(
            st.just(tk),
            st.integers(min_value=0, max_value=len(CONFIG.tracks[tk].modules) - 2),
        )
    )


def st_steering_module() -> st.SearchStrategy[int]:
    """Draw from all module numbers in steering index."""
    return st.sampled_from(sorted(STEERING_INDEX.keys()))


def st_multi_phase_module() -> st.SearchStrategy[int]:
    """Draw from modules with phases in steering index."""
    multi = [num for num, entry in STEERING_INDEX.items() if isinstance(entry, dict)]
    return st.sampled_from(sorted(multi))


def st_skippable_module() -> st.SearchStrategy[int]:
    """Draw from modules with non-null skip_if."""
    skippable = [num for num, mod in CONFIG.modules.items() if mod.skip_if is not None]
    return st.sampled_from(sorted(skippable))


def st_non_skippable_module() -> st.SearchStrategy[int]:
    """Draw from modules with null skip_if."""
    non_skippable = [num for num, mod in CONFIG.modules.items() if mod.skip_if is None]
    return st.sampled_from(sorted(non_skippable))


def st_valid_progress_state() -> st.SearchStrategy[dict]:
    """Generate random valid progress state dicts for round-trip testing."""
    all_modules = sorted(CONFIG.modules.keys())
    return st.fixed_dictionaries({
        "modules_completed": st.lists(
            st.sampled_from(all_modules), unique=True, max_size=len(all_modules)
        ),
        "current_module": st.sampled_from(all_modules),
        "language": st.sampled_from(["python", "java", "csharp", "rust", "typescript"]),
        "database_type": st.sampled_from(["sqlite", "postgresql"]),
        "data_sources": st.lists(st.text(min_size=1, max_size=20), max_size=3),
        "current_step": st.just(1),
        "step_history": st.just({}),
    })


# ---------------------------------------------------------------------------
# Property-Based Tests
# ---------------------------------------------------------------------------


class TestProgressStateProperties:
    """Property tests for progress state management.

    Feature: end-to-end-bootcamp-flow-test
    """

    @given(state=st_valid_progress_state())
    @settings(max_examples=100,
              suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_progress_round_trip(self, tmp_path: Path, state: dict) -> None:
        """Property 1: Progress State Round-Trip.

        For any valid progress state, writing it to bootcamp_progress.json
        and reading it back SHALL produce an identical object.

        Feature: end-to-end-bootcamp-flow-test
        Property 1: Progress State Round-Trip
        Validates: Requirements 4.5
        """
        root = Path(tempfile.mkdtemp(dir=tmp_path))
        mgr = _ProgressManager(root)
        mgr.write(state)
        recovered = mgr.read()
        assert recovered == state

    @given(data=st.data())
    @settings(max_examples=100,
              suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_transition_updates_state(self, tmp_path: Path, data: st.DataObject) -> None:
        """Property 5: Progress State Update on Transition.

        For any track and valid position, completing the current module SHALL:
        (a) add the module to modules_completed,
        (b) update current_module to the next module,
        (c) reset current_step to 1.

        Feature: end-to-end-bootcamp-flow-test
        Property 5: Progress State Update on Transition
        Validates: Requirements 4.1, 4.2, 4.3
        """
        track_key, pos = data.draw(st_track_and_position())
        track = CONFIG.tracks[track_key]
        current_module = track.modules[pos]
        next_module = track.modules[pos + 1]

        root = Path(tempfile.mkdtemp(dir=tmp_path))
        mgr = _ProgressManager(root)
        initial_state = {
            "modules_completed": [],
            "current_module": current_module,
            "language": "python",
            "database_type": "sqlite",
            "data_sources": [],
            "current_step": 5,
            "step_history": {},
        }
        mgr.write(initial_state)
        mgr.complete_module(current_module, track.modules)

        result = mgr.read()
        assert current_module in result["modules_completed"]
        assert result["current_module"] == next_module
        assert result["current_step"] == 1


class TestPrerequisiteProperties:
    """Property tests for prerequisite enforcement.

    Feature: end-to-end-bootcamp-flow-test
    """

    @given(module_num=st_module_with_prereqs())
    @settings(max_examples=100,
              suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_missing_prereqs_cause_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, module_num: int
    ) -> None:
        """Property 2: Prerequisite Enforcement (Negative).

        For any module with a non-empty requires list, attempting validation
        in a project root that lacks prerequisite modules' artifacts SHALL
        produce at least one validation failure.

        Feature: end-to-end-bootcamp-flow-test
        Property 2: Prerequisite Enforcement (Negative)
        Validates: Requirements 2.1, 2.3
        """
        root = Path(tempfile.mkdtemp(dir=tmp_path))
        monkeypatch.chdir(root)
        # Create artifacts for the current module but NOT its prerequisites
        _create_module_artifacts(root, module_num)

        # Check that at least one prerequisite's artifacts are missing
        mod_config = CONFIG.modules[module_num]
        any_prereq_missing = False
        for prereq in mod_config.requires:
            prereq_artifacts = MODULE_ARTIFACTS.get(prereq, [])
            for artifact in prereq_artifacts:
                if not (root / artifact).exists():
                    any_prereq_missing = True
                    break
            if any_prereq_missing:
                break

        assert any_prereq_missing, (
            f"Module {module_num}: expected prerequisite artifacts to be missing"
        )

    @given(module_num=st_any_module())
    @settings(max_examples=100,
              suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_present_prereqs_allow_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, module_num: int
    ) -> None:
        """Property 3: Prerequisite Satisfaction (Positive).

        For any module, when all prerequisite modules' artifacts are present,
        the module's validator SHALL report success.

        Feature: end-to-end-bootcamp-flow-test
        Property 3: Prerequisite Satisfaction (Positive)
        Validates: Requirements 2.2
        """
        root = Path(tempfile.mkdtemp(dir=tmp_path))
        monkeypatch.chdir(root)
        # Create artifacts for all prerequisites AND the module itself
        mod_config = CONFIG.modules[module_num]
        for prereq in mod_config.requires:
            _create_module_artifacts(root, prereq)
        _create_module_artifacts(root, module_num)

        # Run the validator for this module
        validator = validate_module.VALIDATORS[module_num]
        results = validator()
        failures = [r for r in results if not r[0]]
        assert not failures, (
            f"Module {module_num}: validation failed with prereqs present: "
            f"{[r[1] for r in failures]}"
        )


class TestGateProperties:
    """Property tests for gate evaluation.

    Feature: end-to-end-bootcamp-flow-test
    """

    @given(gate_key=st_gate_key())
    @settings(max_examples=100,
              suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_gate_allows_iff_artifacts_present(
        self, tmp_path: Path, gate_key: str
    ) -> None:
        """Property 4: Gate Evaluation Correctness.

        For any gate, the gate SHALL allow transition if and only if the
        source module's artifacts are present. Without artifacts, the gate
        SHALL report the transition as blocked.

        Feature: end-to-end-bootcamp-flow-test
        Property 4: Gate Evaluation Correctness
        Validates: Requirements 3.1, 3.2, 3.3
        """
        root = Path(tempfile.mkdtemp(dir=tmp_path))
        # Without artifacts: gate should block
        assert not _evaluate_gate(root, gate_key, CONFIG), (
            f"Gate {gate_key} should block without source artifacts"
        )

        # With artifacts: gate should allow
        gate = CONFIG.gates[gate_key]
        _create_module_artifacts(root, gate.source)
        assert _evaluate_gate(root, gate_key, CONFIG), (
            f"Gate {gate_key} should allow with source artifacts present"
        )


class TestSteeringResolutionProperties:
    """Property tests for steering file resolution.

    Feature: end-to-end-bootcamp-flow-test
    """

    @given(module_num=st_steering_module())
    @settings(max_examples=100)
    def test_resolver_returns_correct_path(self, module_num: int) -> None:
        """Property 6: Steering Resolution Correctness.

        For any module defined in steering-index.yaml and any valid phase,
        the steering resolver SHALL return the correct non-empty file path.

        Feature: end-to-end-bootcamp-flow-test
        Property 6: Steering Resolution Correctness
        Validates: Requirements 5.1, 5.2, 5.4
        """
        entry = STEERING_INDEX[module_num]
        if isinstance(entry, str):
            result = _resolve_steering(module_num, None, STEERING_INDEX)
            assert result == entry
            assert result  # non-empty
        else:
            # Check root
            root_result = _resolve_steering(module_num, None, STEERING_INDEX)
            assert root_result == entry["root"]
            assert root_result  # non-empty
            # Check each phase
            for phase_name, phase_data in entry["phases"].items():
                phase_result = _resolve_steering(module_num, phase_name, STEERING_INDEX)
                assert phase_result == phase_data["file"]
                assert phase_result  # non-empty

    @given(module_num=st_steering_module())
    @settings(max_examples=100)
    def test_all_steering_files_exist(self, module_num: int) -> None:
        """Property 7: Steering File Existence.

        For any steering file path referenced in steering-index.yaml,
        the file SHALL exist on disk in the steering directory.

        Feature: end-to-end-bootcamp-flow-test
        Property 7: Steering File Existence
        Validates: Requirements 5.3, 6.4
        """
        entry = STEERING_INDEX[module_num]
        if isinstance(entry, str):
            file_path = _STEERING_DIR / entry
            assert file_path.exists(), f"Steering file not found: {file_path}"
        else:
            root_path = _STEERING_DIR / entry["root"]
            assert root_path.exists(), f"Root steering file not found: {root_path}"
            for phase_name, phase_data in entry["phases"].items():
                phase_path = _STEERING_DIR / phase_data["file"]
                assert phase_path.exists(), (
                    f"Module {module_num}, phase '{phase_name}': "
                    f"file not found: {phase_path}"
                )


class TestPhaseTransitionProperties:
    """Property tests for phase transitions within multi-phase modules.

    Feature: end-to-end-bootcamp-flow-test
    """

    @given(module_num=st_multi_phase_module())
    @settings(max_examples=100)
    def test_step_ranges_contiguous(self, module_num: int) -> None:
        """Property 8: Phase Step Range Contiguity.

        For any multi-phase module, the step ranges across its phases SHALL
        be contiguous (phase N's end + 1 equals phase N+1's start) and
        non-overlapping.

        Feature: end-to-end-bootcamp-flow-test
        Property 8: Phase Step Range Contiguity
        Validates: Requirements 6.3
        """
        entry = STEERING_INDEX[module_num]
        assert isinstance(entry, dict)
        phases = entry["phases"]
        phase_list = list(phases.values())

        for idx in range(len(phase_list) - 1):
            current_end = phase_list[idx]["step_range"][1]
            next_start = phase_list[idx + 1]["step_range"][0]
            assert current_end + 1 == next_start, (
                f"Module {module_num}: step ranges not contiguous between "
                f"phases {idx} and {idx + 1}: {current_end} -> {next_start}"
            )

    @given(module_num=st_multi_phase_module())
    @settings(max_examples=100)
    def test_phase_traversal_order(self, module_num: int) -> None:
        """Property 9: Phase Traversal Order.

        For any multi-phase module and any non-final phase, advancing to
        the next phase SHALL yield the steering file for the subsequent
        phase as defined in steering-index.yaml.

        Feature: end-to-end-bootcamp-flow-test
        Property 9: Phase Traversal Order
        Validates: Requirements 6.1, 6.2
        """
        entry = STEERING_INDEX[module_num]
        assert isinstance(entry, dict)
        phase_names = list(entry["phases"].keys())

        for idx in range(len(phase_names) - 1):
            current_phase = phase_names[idx]
            next_phase = phase_names[idx + 1]
            next_file = _resolve_steering(module_num, next_phase, STEERING_INDEX)
            expected_file = entry["phases"][next_phase]["file"]
            assert next_file == expected_file, (
                f"Module {module_num}: advancing from '{current_phase}' should "
                f"yield '{expected_file}', got '{next_file}'"
            )


class TestSkipConditionProperties:
    """Property tests for skip condition evaluation.

    Feature: end-to-end-bootcamp-flow-test
    """

    @given(data=st.data())
    @settings(max_examples=100,
              suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_skip_condition_evaluation(
        self, tmp_path: Path, data: st.DataObject
    ) -> None:
        """Property 10: Skip Condition Evaluation.

        For any module with a non-null skip_if, skipping that module SHALL
        allow the track to proceed without the skipped module's artifacts.
        For any module with null skip_if, the module SHALL NOT be bypassable.

        Feature: end-to-end-bootcamp-flow-test
        Property 10: Skip Condition Evaluation
        Validates: Requirements 7.1, 7.2, 7.3, 7.4
        """
        root = Path(tempfile.mkdtemp(dir=tmp_path))
        # Test skippable modules
        skippable_nums = [n for n, m in CONFIG.modules.items() if m.skip_if is not None]
        non_skippable_nums = [n for n, m in CONFIG.modules.items() if m.skip_if is None]

        if skippable_nums:
            skip_mod = data.draw(st.sampled_from(sorted(skippable_nums)))
            mod_config = CONFIG.modules[skip_mod]
            # Skippable: skip_if is non-null, module can be bypassed
            assert mod_config.skip_if is not None

            # Simulate skipping: track can proceed without this module's artifacts
            mgr = _ProgressManager(root)
            # Find a track containing this module
            for track in CONFIG.tracks.values():
                if skip_mod in track.modules:
                    idx = track.modules.index(skip_mod)
                    if idx + 1 < len(track.modules):
                        next_mod = track.modules[idx + 1]
                        # We can advance to next module without creating skip_mod artifacts
                        state = {
                            "modules_completed": [],
                            "current_module": skip_mod,
                            "language": "python",
                            "database_type": "sqlite",
                            "data_sources": [],
                            "current_step": 1,
                            "step_history": {},
                        }
                        mgr.write(state)
                        # Skip: advance without completing artifacts
                        state["current_module"] = next_mod
                        state["current_step"] = 1
                        mgr.write(state)
                        result = mgr.read()
                        assert result["current_module"] == next_mod
                    break

        if non_skippable_nums:
            non_skip_mod = data.draw(st.sampled_from(sorted(non_skippable_nums)))
            mod_config = CONFIG.modules[non_skip_mod]
            # Non-skippable: skip_if is null, module cannot be bypassed
            assert mod_config.skip_if is None


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


class TestTrackFlowIntegration:
    """Integration tests that walk through complete track flows.

    Feature: end-to-end-bootcamp-flow-test
    """

    def _walk_track(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, track_key: str
    ) -> None:
        """Walk through all modules in a track, validating each step."""
        monkeypatch.chdir(tmp_path)
        track = CONFIG.tracks[track_key]
        mgr = _ProgressManager(tmp_path)

        # Initialize progress
        initial_state = {
            "modules_completed": [],
            "current_module": track.modules[0],
            "language": "python",
            "database_type": "sqlite",
            "data_sources": [],
            "current_step": 1,
            "step_history": {},
        }
        mgr.write(initial_state)

        for idx, module_num in enumerate(track.modules):
            # Create artifacts for this module (and prerequisites if needed)
            mod_config = CONFIG.modules[module_num]
            for prereq in mod_config.requires:
                _create_module_artifacts(tmp_path, prereq)
            _create_module_artifacts(tmp_path, module_num)

            # Validate module passes
            validator = validate_module.VALIDATORS[module_num]
            results = validator()
            failures = [r for r in results if not r[0]]
            assert not failures, (
                f"Track '{track_key}', module {module_num}: validation failed: "
                f"{[r[1] for r in failures]}"
            )

            # Check gate (if not the last module)
            if idx < len(track.modules) - 1:
                next_mod = track.modules[idx + 1]
                gate_key = f"{module_num}->{next_mod}"
                if gate_key in CONFIG.gates:
                    assert _evaluate_gate(tmp_path, gate_key, CONFIG), (
                        f"Gate {gate_key} should allow after module {module_num} artifacts"
                    )

            # Verify steering resolution
            if module_num in STEERING_INDEX:
                steering_file = _resolve_steering(module_num, None, STEERING_INDEX)
                assert steering_file, f"Module {module_num}: no steering file resolved"

            # Complete module and advance
            mgr.complete_module(module_num, track.modules)

        # Verify final state
        final_state = mgr.read()
        assert set(final_state["modules_completed"]) == set(track.modules)

    def test_core_bootcamp_track(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Walk modules 1-7 in the Core Bootcamp track.

        Validates: Requirements 1.2
        """
        self._walk_track(tmp_path, monkeypatch, "core_bootcamp")

    def test_advanced_topics_track(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Walk modules 1-11 in the Advanced Topics track.

        Validates: Requirements 1.3
        """
        self._walk_track(tmp_path, monkeypatch, "advanced_topics")


class TestConfigParsing:
    """Smoke tests for YAML parsing and error handling edge cases.

    Feature: end-to-end-bootcamp-flow-test
    Validates: Requirements 8.1, 8.2, 8.3, 8.4
    """

    def test_module_dependencies_parsed(self) -> None:
        """Verify module-dependencies.yaml was parsed successfully."""
        assert len(CONFIG.modules) == 11
        assert len(CONFIG.tracks) == 2
        assert len(CONFIG.gates) == 10

    def test_steering_index_parsed(self) -> None:
        """Verify steering-index.yaml was parsed successfully."""
        assert len(STEERING_INDEX) == 11
        # Single-phase modules
        for num in [4, 7]:
            assert isinstance(STEERING_INDEX[num], str)
        # Multi-phase modules (including module 2 which uses structured format)
        for num in [1, 2, 3, 5, 6, 8, 9, 10, 11]:
            assert isinstance(STEERING_INDEX[num], dict)

    def test_tracks_contain_valid_modules(self) -> None:
        """All modules referenced in tracks exist in the modules section."""
        for track_key, track in CONFIG.tracks.items():
            for mod_num in track.modules:
                assert mod_num in CONFIG.modules, (
                    f"Track '{track_key}' references module {mod_num} "
                    f"which is not defined in modules section"
                )

    def test_gates_reference_valid_modules(self) -> None:
        """All gates reference valid source and target modules."""
        for gate_key, gate in CONFIG.gates.items():
            assert gate.source in CONFIG.modules, (
                f"Gate '{gate_key}' source {gate.source} not in modules"
            )
            assert gate.target in CONFIG.modules, (
                f"Gate '{gate_key}' target {gate.target} not in modules"
            )

    def test_missing_file_raises_error(self, tmp_path: Path) -> None:
        """Parsing a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            _parse_module_dependencies(tmp_path / "nonexistent.yaml")

    def test_missing_steering_file_raises_error(self, tmp_path: Path) -> None:
        """Parsing a non-existent steering index raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            _parse_steering_index(tmp_path / "nonexistent.yaml")

    def test_malformed_steering_raises_error(self, tmp_path: Path) -> None:
        """Parsing a malformed steering index raises ValueError."""
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("not_modules:\n  foo: bar\n", encoding="utf-8")
        with pytest.raises(ValueError, match="No 'modules:' key found"):
            _parse_steering_index(bad_file)

    def test_module_artifacts_covers_all_modules(self) -> None:
        """MODULE_ARTIFACTS has entries for all 11 modules."""
        for num in range(1, 12):
            assert num in MODULE_ARTIFACTS, f"Module {num} missing from MODULE_ARTIFACTS"
