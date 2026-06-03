"""Property-based tests for progress_dashboard.py parsers using Hypothesis.

Feature: individual-progress-dashboard
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from progress_dashboard import (
    DependencyData,
    GateInfo,
    ModuleInfo,
    PreferencesData,
    ProgressData,
    parse_dependencies,
    parse_preferences,
    parse_progress,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_progress_data(draw):
    """Generate random valid progress JSON data.

    Produces a dict with:
    - current_module: random int or None
    - modules_completed: list of random ints
    - current_step: random string like "N.M" or None
    - language: random string or None
    - step_history: dict with step keys like "N.M" and values containing
      optional "artifact" key
    """
    current_module = draw(st.one_of(st.none(), st.integers(min_value=1, max_value=20)))
    modules_completed = draw(
        st.lists(st.integers(min_value=1, max_value=20), min_size=0, max_size=10, unique=True)
    )
    current_step = draw(st.one_of(
        st.none(),
        st.builds(lambda a, b: f"{a}.{b}", st.integers(1, 20), st.integers(1, 10)),
    ))
    language = draw(st.one_of(st.none(), st.sampled_from(["python", "java", "csharp", "rust"])))

    # Generate step_history with optional artifact references
    num_steps = draw(st.integers(min_value=0, max_value=5))
    step_history: dict = {}
    for _ in range(num_steps):
        mod_num = draw(st.integers(min_value=1, max_value=20))
        step_num = draw(st.integers(min_value=1, max_value=10))
        step_key = f"{mod_num}.{step_num}"
        has_artifact = draw(st.booleans())
        entry: dict = {"status": "complete"}
        if has_artifact:
            artifact_name = draw(st.from_regex(r"[a-z_]+\.[a-z]+", fullmatch=True))
            entry["artifact"] = f"docs/{artifact_name}"
        step_history[step_key] = entry

    return {
        "current_module": current_module,
        "modules_completed": modules_completed,
        "current_step": current_step,
        "language": language,
        "step_history": step_history,
    }


@st.composite
def st_preferences_data(draw):
    """Generate random valid preferences data.

    Produces a dict with:
    - language, track, database_type, deployment_target: each either a string or None
    """
    language = draw(st.one_of(
        st.none(),
        st.sampled_from(["python", "java", "csharp", "rust", "typescript"]),
    ))
    track = draw(st.one_of(
        st.none(),
        st.sampled_from(["core_bootcamp", "advanced_topics"]),
    ))
    database_type = draw(st.one_of(
        st.none(),
        st.sampled_from(["sqlite", "postgresql", "mysql"]),
    ))
    deployment_target = draw(st.one_of(
        st.none(),
        st.sampled_from(["docker", "kubernetes", "bare_metal"]),
    ))
    return {
        "language": language,
        "track": track,
        "database_type": database_type,
        "deployment_target": deployment_target,
    }


@st.composite
def st_dependency_data(draw):
    """Generate random dependency graphs.

    Produces a dict with:
    - modules: dict of number -> {name, requires} (DAG structure)
    - gates: dict of "from->to" -> {requires: [...]}
    """
    n = draw(st.integers(min_value=1, max_value=8))
    modules: dict = {}
    for i in range(1, n + 1):
        name = draw(st.from_regex(r"[A-Z][a-z]+ [A-Z][a-z]+", fullmatch=True))
        # Only require modules with lower numbers to ensure DAG
        possible_reqs = list(range(1, i))
        requires = draw(
            st.lists(
                st.sampled_from(possible_reqs) if possible_reqs else st.nothing(),
                max_size=min(3, len(possible_reqs)),
                unique=True,
            )
        )
        modules[i] = {"name": name, "requires": sorted(requires)}

    # Generate gates between consecutive modules
    num_gates = draw(st.integers(min_value=0, max_value=min(n - 1, 4)))
    gates: dict = {}
    if n > 1 and num_gates > 0:
        gate_pairs = draw(
            st.lists(
                st.tuples(
                    st.integers(min_value=1, max_value=n - 1),
                    st.integers(min_value=2, max_value=n),
                ).filter(lambda t: t[0] < t[1]),
                min_size=num_gates,
                max_size=num_gates,
                unique=True,
            )
        )
        for from_mod, to_mod in gate_pairs:
            req_text = draw(st.from_regex(r"[A-Za-z ]+", fullmatch=True).filter(
                lambda s: len(s.strip()) > 0
            ))
            gates[f"{from_mod}->{to_mod}"] = {"requires": [req_text]}

    return {"modules": modules, "gates": gates}


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestProgressDataParsingPreservation:
    """Property 2 — Progress Data Parsing Preservation.

    **Validates: Requirements 2.1, 2.2, 2.3**

    For any valid progress JSON, all `modules_completed` entries and artifact
    references are preserved after parsing.
    """

    @given(data=st_progress_data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_modules_completed_preserved(self, data):
        """All modules_completed entries are preserved after parsing."""
        json_text = json.dumps(data)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write(json_text)
            f.flush()
            path = Path(f.name)

        try:
            result = parse_progress(path)
            assert isinstance(result, ProgressData)
            assert sorted(result.modules_completed) == sorted(data["modules_completed"])
        finally:
            path.unlink()

    @given(data=st_progress_data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_artifact_references_preserved(self, data):
        """All artifact references in step_history are preserved after parsing."""
        json_text = json.dumps(data)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write(json_text)
            f.flush()
            path = Path(f.name)

        try:
            result = parse_progress(path)
            # Every artifact in source step_history should be in parsed result
            for step_key, entry in data["step_history"].items():
                assert step_key in result.step_history
                if "artifact" in entry:
                    assert result.step_history[step_key]["artifact"] == entry["artifact"]
        finally:
            path.unlink()

    @given(data=st_progress_data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_current_module_preserved(self, data):
        """current_module value is preserved after parsing."""
        json_text = json.dumps(data)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write(json_text)
            f.flush()
            path = Path(f.name)

        try:
            result = parse_progress(path)
            assert result.current_module == data["current_module"]
            assert result.language == data["language"]
            assert result.current_step == data["current_step"]
        finally:
            path.unlink()


class TestYAMLPreferencesParsingRoundTrip:
    """Property 3 — YAML Preferences Parsing Round-Trip.

    **Validates: Requirements 3.1, 3.2, 3.3**

    For any valid preferences YAML, parsed values match originals
    (None for null/absent).
    """

    @given(data=st_preferences_data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_preferences_round_trip(self, data):
        """Parsed preference values match the original data."""
        # Serialize to YAML text
        lines = []
        for key in ("language", "track", "database_type", "deployment_target"):
            value = data[key]
            if value is None:
                lines.append(f"{key}: null")
            else:
                lines.append(f"{key}: {value}")
        yaml_text = "\n".join(lines) + "\n"

        # Write to temp file and parse
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_text)
            f.flush()
            path = Path(f.name)

        try:
            result = parse_preferences(path)
            assert isinstance(result, PreferencesData)
            assert result.language == data["language"]
            assert result.track == data["track"]
            assert result.database_type == data["database_type"]
            assert result.deployment_target == data["deployment_target"]
        finally:
            path.unlink()

    @given(data=st_preferences_data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_absent_fields_parsed_as_none(self, data):
        """Absent fields are parsed as None."""
        # Only include non-None fields in the YAML
        lines = []
        for key in ("language", "track", "database_type", "deployment_target"):
            value = data[key]
            if value is not None:
                lines.append(f"{key}: {value}")
            # Absent fields are simply not written
        yaml_text = "\n".join(lines) + "\n" if lines else "\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_text)
            f.flush()
            path = Path(f.name)

        try:
            result = parse_preferences(path)
            assert isinstance(result, PreferencesData)
            for key in ("language", "track", "database_type", "deployment_target"):
                parsed_val = getattr(result, key)
                if data[key] is not None:
                    assert parsed_val == data[key]
                else:
                    # Absent fields should be None
                    assert parsed_val is None
        finally:
            path.unlink()


class TestDependencyGraphParsingCompleteness:
    """Property 4 — Dependency Graph Parsing Completeness.

    **Validates: Requirements 4.1, 4.2, 4.3**

    For any valid dependencies YAML, all module numbers, names, requires lists,
    and gates are captured.
    """

    @given(data=st_dependency_data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_all_modules_captured(self, data):
        """All module numbers and names are captured after parsing."""
        # Serialize to YAML text matching the format parse_dependencies expects
        yaml_lines = ["modules:"]
        for num, mod_data in sorted(data["modules"].items()):
            yaml_lines.append(f"  {num}:")
            yaml_lines.append(f'    name: "{mod_data["name"]}"')
            requires = mod_data["requires"]
            if requires:
                req_str = ", ".join(str(r) for r in requires)
                yaml_lines.append(f"    requires: [{req_str}]")
            else:
                yaml_lines.append("    requires: []")

        yaml_lines.append("gates:")
        for gate_key, gate_data in data["gates"].items():
            yaml_lines.append(f'  "{gate_key}":')
            yaml_lines.append("    requires:")
            for req in gate_data["requires"]:
                yaml_lines.append(f'      - "{req}"')

        yaml_text = "\n".join(yaml_lines) + "\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_text)
            f.flush()
            path = Path(f.name)

        try:
            result = parse_dependencies(path)
            assert isinstance(result, DependencyData)

            # All module numbers are captured
            parsed_numbers = {m.number for m in result.modules}
            expected_numbers = set(data["modules"].keys())
            assert parsed_numbers == expected_numbers

            # All module names are captured
            for mod in result.modules:
                expected_name = data["modules"][mod.number]["name"]
                assert mod.name == expected_name

            # All requires lists are captured
            for mod in result.modules:
                expected_requires = sorted(data["modules"][mod.number]["requires"])
                assert sorted(mod.requires) == expected_requires
        finally:
            path.unlink()

    @given(data=st_dependency_data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_all_gates_captured(self, data):
        """All gate transitions are captured after parsing."""
        # Serialize to YAML text
        yaml_lines = ["modules:"]
        for num, mod_data in sorted(data["modules"].items()):
            yaml_lines.append(f"  {num}:")
            yaml_lines.append(f'    name: "{mod_data["name"]}"')
            requires = mod_data["requires"]
            if requires:
                req_str = ", ".join(str(r) for r in requires)
                yaml_lines.append(f"    requires: [{req_str}]")
            else:
                yaml_lines.append("    requires: []")

        yaml_lines.append("gates:")
        for gate_key, gate_data in data["gates"].items():
            yaml_lines.append(f'  "{gate_key}":')
            yaml_lines.append("    requires:")
            for req in gate_data["requires"]:
                yaml_lines.append(f'      - "{req}"')

        yaml_text = "\n".join(yaml_lines) + "\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_text)
            f.flush()
            path = Path(f.name)

        try:
            result = parse_dependencies(path)

            # All gates are captured
            parsed_gates = {
                (g.from_module, g.to_module): g.requirements for g in result.gates
            }
            for gate_key, gate_data in data["gates"].items():
                parts = gate_key.split("->")
                from_mod = int(parts[0])
                to_mod = int(parts[1])
                assert (from_mod, to_mod) in parsed_gates
                assert parsed_gates[(from_mod, to_mod)] == gate_data["requires"]
        finally:
            path.unlink()


# Additional imports for computation tests
from progress_dashboard import (
    compute_module_statuses,
    compute_next_steps,
)

# ---------------------------------------------------------------------------
# Strategies for computation tests (generate dataclass instances directly)
# ---------------------------------------------------------------------------


@st.composite
def st_dependency_graph(draw):
    """Generate a random DependencyData with a valid DAG of modules.

    Produces a DependencyData dataclass instance with:
    - modules: list of ModuleInfo with DAG-valid requires (only lower-numbered modules)
    - gates: list of GateInfo between module pairs
    """
    n = draw(st.integers(min_value=1, max_value=8))
    modules: list[ModuleInfo] = []
    for i in range(1, n + 1):
        name = f"Module {i}"
        possible_reqs = list(range(1, i))
        requires = draw(
            st.lists(
                st.sampled_from(possible_reqs) if possible_reqs else st.nothing(),
                max_size=min(3, len(possible_reqs)),
                unique=True,
            )
        )
        modules.append(ModuleInfo(number=i, name=name, requires=sorted(requires)))

    # Generate gates
    num_gates = draw(st.integers(min_value=0, max_value=min(n - 1, 3)))
    gates: list[GateInfo] = []
    if n > 1 and num_gates > 0:
        gate_pairs = draw(
            st.lists(
                st.tuples(
                    st.integers(min_value=1, max_value=n - 1),
                    st.integers(min_value=2, max_value=n),
                ).filter(lambda t: t[0] < t[1]),
                min_size=num_gates,
                max_size=num_gates,
                unique=True,
            )
        )
        for from_mod, to_mod in gate_pairs:
            gates.append(GateInfo(
                from_module=from_mod,
                to_module=to_mod,
                requirements=[f"Gate requirement {from_mod}->{to_mod}"],
            ))

    return DependencyData(modules=modules, gates=gates)


@st.composite
def st_completion_state(draw, dependency_data: DependencyData):
    """Generate a random completion state for a given dependency graph.

    Produces a ProgressData dataclass instance with:
    - modules_completed: random subset of module numbers
    - current_module: one of the module numbers (or None), not in completed
    """
    all_numbers = [m.number for m in dependency_data.modules]
    completed = draw(
        st.lists(
            st.sampled_from(all_numbers) if all_numbers else st.nothing(),
            max_size=len(all_numbers),
            unique=True,
        )
    )
    remaining = [n for n in all_numbers if n not in completed]
    current_module = draw(
        st.sampled_from(remaining) if remaining else st.none()
    )
    return ProgressData(
        current_module=current_module,
        modules_completed=completed,
        current_step=None,
        language=None,
        step_history={},
    )


# ---------------------------------------------------------------------------
# Property 5: Module Status Classification Correctness
# ---------------------------------------------------------------------------


class TestModuleStatusClassificationCorrectness:
    """Property 5 — Module Status Classification Correctness.

    **Validates: Requirements 5.1, 5.2, 5.3**

    For any dependency graph and progress state, every module is classified as
    exactly one of: "completed", "in-progress", or "not-started", matching its
    state in the progress data.
    """

    @given(data=st.data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_every_module_has_exactly_one_status(self, data):
        """Every module is classified as exactly one status."""
        dep_data = data.draw(st_dependency_graph())
        progress = data.draw(st_completion_state(dep_data))

        statuses = compute_module_statuses(dep_data, progress)

        # Every module in the graph has a status
        for module in dep_data.modules:
            assert module.number in statuses
            assert statuses[module.number] in ("completed", "in-progress", "not-started")

    @given(data=st.data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_completed_modules_classified_correctly(self, data):
        """Modules in modules_completed are classified as 'completed'."""
        dep_data = data.draw(st_dependency_graph())
        progress = data.draw(st_completion_state(dep_data))

        statuses = compute_module_statuses(dep_data, progress)

        for module in dep_data.modules:
            if module.number in progress.modules_completed:
                assert statuses[module.number] == "completed"

    @given(data=st.data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_current_module_classified_as_in_progress(self, data):
        """current_module (if not completed) is classified as 'in-progress'."""
        dep_data = data.draw(st_dependency_graph())
        progress = data.draw(st_completion_state(dep_data))

        statuses = compute_module_statuses(dep_data, progress)

        if (
            progress.current_module is not None
            and progress.current_module not in progress.modules_completed
        ):
            # Only check if current_module is actually in the graph
            module_numbers = {m.number for m in dep_data.modules}
            if progress.current_module in module_numbers:
                assert statuses[progress.current_module] == "in-progress"

    @given(data=st.data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_remaining_modules_classified_as_not_started(self, data):
        """Modules not completed and not current are classified as 'not-started'."""
        dep_data = data.draw(st_dependency_graph())
        progress = data.draw(st_completion_state(dep_data))

        statuses = compute_module_statuses(dep_data, progress)

        for module in dep_data.modules:
            if (
                module.number not in progress.modules_completed
                and module.number != progress.current_module
            ):
                assert statuses[module.number] == "not-started"


# ---------------------------------------------------------------------------
# Property 6: Next Steps Computation Correctness
# ---------------------------------------------------------------------------


class TestNextStepsComputationCorrectness:
    """Property 6 — Next Steps Computation Correctness.

    **Validates: Requirements 7.1, 7.2**

    For any dependency graph and set of completed modules, the computed next
    steps are exactly the set of modules where:
    (a) all requires are in modules_completed
    (b) the module is not in modules_completed
    (c) the module is not the current_module
    """

    @given(data=st.data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_next_steps_have_all_requires_met(self, data):
        """Every returned next step has all its requires in modules_completed."""
        dep_data = data.draw(st_dependency_graph())
        progress = data.draw(st_completion_state(dep_data))

        next_steps = compute_next_steps(dep_data, progress)
        completed_set = set(progress.modules_completed)

        for step in next_steps:
            for req in step.module.requires:
                assert req in completed_set

    @given(data=st.data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_next_steps_exclude_completed(self, data):
        """No returned next step is in modules_completed."""
        dep_data = data.draw(st_dependency_graph())
        progress = data.draw(st_completion_state(dep_data))

        next_steps = compute_next_steps(dep_data, progress)
        completed_set = set(progress.modules_completed)

        for step in next_steps:
            assert step.module.number not in completed_set

    @given(data=st.data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_next_steps_exclude_current_module(self, data):
        """No returned next step is the current_module."""
        dep_data = data.draw(st_dependency_graph())
        progress = data.draw(st_completion_state(dep_data))

        next_steps = compute_next_steps(dep_data, progress)

        for step in next_steps:
            assert step.module.number != progress.current_module

    @given(data=st.data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_next_steps_completeness(self, data):
        """Every module satisfying all three conditions IS in the result."""
        dep_data = data.draw(st_dependency_graph())
        progress = data.draw(st_completion_state(dep_data))

        next_steps = compute_next_steps(dep_data, progress)
        next_step_numbers = {step.module.number for step in next_steps}
        completed_set = set(progress.modules_completed)

        for module in dep_data.modules:
            # Check if module satisfies all three conditions
            all_requires_met = all(req in completed_set for req in module.requires)
            not_completed = module.number not in completed_set
            not_current = module.number != progress.current_module

            if all_requires_met and not_completed and not_current:
                assert module.number in next_step_numbers, (
                    f"Module {module.number} satisfies all conditions but is not "
                    f"in next_steps. requires={module.requires}, "
                    f"completed={progress.modules_completed}, "
                    f"current={progress.current_module}"
                )


# Additional imports for renderer tests
from progress_dashboard import (
    extract_artifacts,
    render_dashboard,
)

# ---------------------------------------------------------------------------
# Property 7: Preferences Card Rendering Completeness
# ---------------------------------------------------------------------------


class TestPreferencesCardRenderingCompleteness:
    """Property 7 — Preferences Card Rendering Completeness.

    **Validates: Requirements 3.3, 8.1, 8.2, 8.3, 8.4, 8.5**

    For any preferences data (with values being non-null strings or None),
    the rendered HTML preferences card contains each of the four fields
    with either the actual value or the text "Not set" for None/absent values.
    """

    @given(data=st_preferences_data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_all_preference_fields_present(self, data):
        """Rendered HTML contains all four preference fields with value or 'Not set'."""
        preferences = PreferencesData(
            language=data["language"],
            track=data["track"],
            database_type=data["database_type"],
            deployment_target=data["deployment_target"],
        )

        # Minimal valid inputs for render_dashboard
        progress = ProgressData(
            current_module=None,
            modules_completed=[],
            current_step=None,
            language=None,
            step_history={},
        )
        dep_data = DependencyData(
            modules=[ModuleInfo(number=1, name="Test Module", requires=[])],
            gates=[],
        )
        module_statuses = {1: "not-started"}
        next_steps = []
        artifacts = []

        html = render_dashboard(
            progress, preferences, dep_data, module_statuses, next_steps, artifacts
        )

        # Each field should appear with its value or "Not set"
        for field_name in ("language", "track", "database_type", "deployment_target"):
            value = data[field_name]
            if value is not None:
                assert value in html, (
                    f"Expected preference value '{value}' for field '{field_name}' "
                    f"to appear in rendered HTML"
                )
            else:
                # "Not set" must appear (at least once for this field)
                assert "Not set" in html, (
                    f"Expected 'Not set' for None field '{field_name}' "
                    f"to appear in rendered HTML"
                )


# ---------------------------------------------------------------------------
# Property 8: Self-Contained HTML Output
# ---------------------------------------------------------------------------


class TestSelfContainedHTMLOutput:
    """Property 8 — Self-Contained HTML Output.

    **Validates: Requirements 9.1, 9.2, 9.3**

    For any valid set of inputs, the rendered HTML output contains a
    <!DOCTYPE html> declaration, a <style> element with CSS, and does NOT
    contain any external resource references.
    """

    @given(data=st.data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_html_is_self_contained(self, data):
        """Output has DOCTYPE, <style>, and no external resource references."""
        dep_data = data.draw(st_dependency_graph())
        progress = data.draw(st_completion_state(dep_data))
        prefs_raw = data.draw(st_preferences_data())

        preferences = PreferencesData(
            language=prefs_raw["language"],
            track=prefs_raw["track"],
            database_type=prefs_raw["database_type"],
            deployment_target=prefs_raw["deployment_target"],
        )

        module_statuses = compute_module_statuses(dep_data, progress)
        next_steps = compute_next_steps(dep_data, progress)
        artifacts = extract_artifacts(progress)

        html = render_dashboard(
            progress, preferences, dep_data, module_statuses, next_steps, artifacts
        )

        # Must contain DOCTYPE declaration
        assert "<!DOCTYPE html>" in html, "HTML output must contain <!DOCTYPE html>"

        # Must contain a <style> element
        assert "<style>" in html, "HTML output must contain a <style> element"
        assert "</style>" in html, "HTML output must contain closing </style>"

        # Must NOT contain external stylesheet links
        assert '<link rel="stylesheet"' not in html.lower(), (
            "HTML output must not contain external stylesheet links"
        )

        # Must NOT contain external script references
        assert '<script src="http' not in html.lower(), (
            "HTML output must not contain external script references"
        )


# ---------------------------------------------------------------------------
# Property 9: Artifact Display Correctness
# ---------------------------------------------------------------------------


@st.composite
def st_progress_with_artifacts(draw):
    """Generate ProgressData with guaranteed artifact references in step_history.

    Produces a ProgressData dataclass instance with:
    - step_history containing entries with artifact references
    - module numbers derived from step keys
    """
    num_artifacts = draw(st.integers(min_value=1, max_value=5))
    step_history: dict = {}
    for _ in range(num_artifacts):
        mod_num = draw(st.integers(min_value=1, max_value=10))
        step_num = draw(st.integers(min_value=1, max_value=10))
        step_key = f"{mod_num}.{step_num}"
        artifact_name = draw(
            st.from_regex(r"[a-z][a-z_]{2,10}\.[a-z]{2,4}", fullmatch=True)
        )
        step_history[step_key] = {
            "status": "complete",
            "artifact": f"docs/{artifact_name}",
        }

    current_module = draw(st.one_of(st.none(), st.integers(min_value=1, max_value=10)))
    modules_completed = draw(
        st.lists(st.integers(min_value=1, max_value=10), min_size=0, max_size=5, unique=True)
    )

    return ProgressData(
        current_module=current_module,
        modules_completed=modules_completed,
        current_step=None,
        language=None,
        step_history=step_history,
    )


class TestArtifactDisplayCorrectness:
    """Property 9 — Artifact Display Correctness.

    **Validates: Requirements 6.1**

    For any progress data with a non-empty step_history containing artifact
    references, every artifact reference present in the source data appears
    in the rendered HTML output.
    """

    @given(progress=st_progress_with_artifacts())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_all_artifacts_appear_in_html(self, progress):
        """Every artifact reference in source data appears in rendered HTML."""
        # Extract artifacts from the progress data
        artifacts = extract_artifacts(progress)
        assume(len(artifacts) > 0)

        # Build minimal valid inputs for render_dashboard
        # Ensure we have modules covering all artifact module numbers
        artifact_modules = {a.module_number for a in artifacts}
        modules = [
            ModuleInfo(number=n, name=f"Module {n}", requires=[])
            for n in sorted(artifact_modules)
        ]
        if not modules:
            modules = [ModuleInfo(number=1, name="Default", requires=[])]

        dep_data = DependencyData(modules=modules, gates=[])
        module_statuses = {m.number: "not-started" for m in modules}
        # Mark completed modules
        for num in progress.modules_completed:
            if num in module_statuses:
                module_statuses[num] = "completed"

        preferences = PreferencesData(
            language=None, track=None, database_type=None, deployment_target=None
        )
        next_steps = []

        html = render_dashboard(
            progress, preferences, dep_data, module_statuses, next_steps, artifacts
        )

        # Every artifact reference must appear in the HTML
        for artifact in artifacts:
            assert artifact.reference in html, (
                f"Artifact reference '{artifact.reference}' from step "
                f"'{artifact.step_key}' not found in rendered HTML"
            )


# ---------------------------------------------------------------------------
# Additional imports for exit code tests
# ---------------------------------------------------------------------------

from progress_dashboard import main

# ---------------------------------------------------------------------------
# Strategies for exit code tests
# ---------------------------------------------------------------------------


@st.composite
def st_valid_file_set(draw):
    """Generate a valid set of input files (progress JSON, preferences YAML, deps YAML).

    Returns a dict with keys 'progress', 'preferences', 'dependencies' containing
    valid file content strings.
    """
    # Valid progress JSON
    progress_data = draw(st_progress_data())
    progress_json = json.dumps(progress_data)

    # Valid preferences YAML
    prefs_data = draw(st_preferences_data())
    pref_lines = []
    for key in ("language", "track", "database_type", "deployment_target"):
        value = prefs_data[key]
        if value is None:
            pref_lines.append(f"{key}: null")
        else:
            pref_lines.append(f"{key}: {value}")
    preferences_yaml = "\n".join(pref_lines) + "\n"

    # Valid dependencies YAML (minimal valid structure)
    dep_data = draw(st_dependency_data())
    yaml_lines = ["modules:"]
    for num, mod_data in sorted(dep_data["modules"].items()):
        yaml_lines.append(f"  {num}:")
        yaml_lines.append(f'    name: "{mod_data["name"]}"')
        requires = mod_data["requires"]
        if requires:
            req_str = ", ".join(str(r) for r in requires)
            yaml_lines.append(f"    requires: [{req_str}]")
        else:
            yaml_lines.append("    requires: []")
    yaml_lines.append("gates:")
    for gate_key, gate_data in dep_data["gates"].items():
        yaml_lines.append(f'  "{gate_key}":')
        yaml_lines.append("    requires:")
        for req in gate_data["requires"]:
            yaml_lines.append(f'      - "{req}"')
    dependencies_yaml = "\n".join(yaml_lines) + "\n"

    return {
        "progress": progress_json,
        "preferences": preferences_yaml,
        "dependencies": dependencies_yaml,
    }


# ---------------------------------------------------------------------------
# Property 1: Exit Code Correctness
# ---------------------------------------------------------------------------


class TestExitCodeCorrectness:
    """Property 1 — Exit Code Correctness.

    **Validates: Requirements 1.6, 1.7, 2.4**

    For any set of input file paths, the script exits with code 0 if and only
    if all required input files exist and contain parseable content; exits with
    code 1 otherwise.
    """

    @given(file_set=st_valid_file_set())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_exits_0_when_all_files_valid(self, file_set):
        """Script exits 0 when all input files exist and are parseable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Write valid files
            progress_path = tmp_path / "progress.json"
            progress_path.write_text(file_set["progress"])

            prefs_path = tmp_path / "preferences.yaml"
            prefs_path.write_text(file_set["preferences"])

            deps_path = tmp_path / "dependencies.yaml"
            deps_path.write_text(file_set["dependencies"])

            output_path = tmp_path / "output" / "dashboard.html"

            # Call main() and expect exit code 0 (no SystemExit raised)
            try:
                main(argv=[
                    "--progress", str(progress_path),
                    "--preferences", str(prefs_path),
                    "--dependencies", str(deps_path),
                    "--output", str(output_path),
                ])
            except SystemExit as e:
                assert e.code == 0 or e.code is None, (
                    f"Expected exit code 0 for valid inputs, got {e.code}"
                )

            # Output file should have been created
            assert output_path.exists(), "Dashboard HTML should be written on success"

    @given(
        file_set=st_valid_file_set(),
        missing_file=st.sampled_from(["progress", "preferences", "dependencies"]),
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_exits_1_when_file_missing(self, file_set, missing_file):
        """Script exits 1 when one or more input files are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Write all files except the missing one
            paths = {}
            for name in ("progress", "preferences", "dependencies"):
                if name == "progress":
                    file_path = tmp_path / "progress.json"
                elif name == "preferences":
                    file_path = tmp_path / "preferences.yaml"
                else:
                    file_path = tmp_path / "dependencies.yaml"

                if name != missing_file:
                    file_path.write_text(file_set[name])
                paths[name] = file_path

            output_path = tmp_path / "output" / "dashboard.html"

            # Call main() and expect exit code 1
            with pytest.raises(SystemExit) as exc_info:
                main(argv=[
                    "--progress", str(paths["progress"]),
                    "--preferences", str(paths["preferences"]),
                    "--dependencies", str(paths["dependencies"]),
                    "--output", str(output_path),
                ])

            assert exc_info.value.code == 1, (
                f"Expected exit code 1 for missing {missing_file}, "
                f"got {exc_info.value.code}"
            )

    @given(file_set=st_valid_file_set())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_exits_1_when_progress_has_invalid_json(self, file_set):
        """Script exits 1 when progress file contains invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Write invalid JSON for progress
            progress_path = tmp_path / "progress.json"
            progress_path.write_text("{invalid json content!!!")

            prefs_path = tmp_path / "preferences.yaml"
            prefs_path.write_text(file_set["preferences"])

            deps_path = tmp_path / "dependencies.yaml"
            deps_path.write_text(file_set["dependencies"])

            output_path = tmp_path / "output" / "dashboard.html"

            # Call main() and expect exit code 1
            with pytest.raises(SystemExit) as exc_info:
                main(argv=[
                    "--progress", str(progress_path),
                    "--preferences", str(prefs_path),
                    "--dependencies", str(deps_path),
                    "--output", str(output_path),
                ])

            assert exc_info.value.code == 1, (
                f"Expected exit code 1 for invalid JSON, got {exc_info.value.code}"
            )


# ---------------------------------------------------------------------------
# Unit Tests: CLI Defaults and Edge Cases
# ---------------------------------------------------------------------------

import os


class TestCLIEdgeCases:
    """Unit tests for CLI defaults and edge cases.

    **Validates: Requirements 1.5, 1.7, 5.4, 7.5, 10.1**
    """

    def test_help_exits_with_code_0(self):
        """--help flag displays usage and exits with code 0.

        Validates: Requirement 1.5
        """
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_missing_file_produces_error_and_exit_code_1(self):
        """Missing input file prints error message and exits with code 1.

        Validates: Requirement 1.7
        """
        with pytest.raises(SystemExit) as exc_info:
            main(["--progress", "/nonexistent/path.json"])
        assert exc_info.value.code == 1

    def test_empty_modules_completed_renders_zero_progress(self):
        """Empty modules_completed renders 0 / N modules completed.

        Validates: Requirement 5.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create progress file with empty modules_completed
            progress_path = os.path.join(tmpdir, "progress.json")
            with open(progress_path, "w") as f:
                json.dump({
                    "current_module": None,
                    "modules_completed": [],
                    "current_step": None,
                    "language": None,
                    "step_history": {},
                }, f)

            # Create preferences file
            prefs_path = os.path.join(tmpdir, "preferences.yaml")
            with open(prefs_path, "w") as f:
                f.write("language: python\ntrack: core_bootcamp\n")
                f.write("database_type: sqlite\ndeployment_target: docker\n")

            # Create dependencies file with 3 modules
            deps_path = os.path.join(tmpdir, "dependencies.yaml")
            with open(deps_path, "w") as f:
                f.write("modules:\n")
                f.write('  1:\n    name: "Module One"\n    requires: []\n')
                f.write('  2:\n    name: "Module Two"\n    requires: [1]\n')
                f.write('  3:\n    name: "Module Three"\n    requires: [1, 2]\n')
                f.write("gates:\n")

            # Output path
            output_path = os.path.join(tmpdir, "output", "dashboard.html")

            main([
                "--progress", progress_path,
                "--preferences", prefs_path,
                "--dependencies", deps_path,
                "--output", output_path,
            ])

            html = Path(output_path).read_text()
            assert "0 / 3 modules completed" in html

    def test_all_modules_completed_renders_congratulatory_message(self):
        """All modules completed renders congratulatory completion message.

        Validates: Requirement 7.5
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create progress file with all modules completed
            progress_path = os.path.join(tmpdir, "progress.json")
            with open(progress_path, "w") as f:
                json.dump({
                    "current_module": None,
                    "modules_completed": [1, 2, 3],
                    "current_step": None,
                    "language": "python",
                    "step_history": {},
                }, f)

            # Create preferences file
            prefs_path = os.path.join(tmpdir, "preferences.yaml")
            with open(prefs_path, "w") as f:
                f.write("language: python\ntrack: core_bootcamp\n")
                f.write("database_type: sqlite\ndeployment_target: docker\n")

            # Create dependencies file with 3 modules (all completed)
            deps_path = os.path.join(tmpdir, "dependencies.yaml")
            with open(deps_path, "w") as f:
                f.write("modules:\n")
                f.write('  1:\n    name: "Module One"\n    requires: []\n')
                f.write('  2:\n    name: "Module Two"\n    requires: [1]\n')
                f.write('  3:\n    name: "Module Three"\n    requires: [1, 2]\n')
                f.write("gates:\n")

            # Output path
            output_path = os.path.join(tmpdir, "output", "dashboard.html")

            main([
                "--progress", progress_path,
                "--preferences", prefs_path,
                "--dependencies", deps_path,
                "--output", output_path,
            ])

            html = Path(output_path).read_text()
            assert "Congratulations" in html

    def test_no_imports_from_status_or_other_scripts(self):
        """Script has no imports from status.py or other scripts in the directory.

        Validates: Requirement 10.1
        """
        import ast

        script_path = Path(__file__).resolve().parent.parent / "scripts" / "progress_dashboard.py"
        source = script_path.read_text()
        tree = ast.parse(source)

        # Collect all imported module names from the AST
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module.split(".")[0])

        # Must not import from status module
        assert "status" not in imported_modules, (
            "progress_dashboard.py must not import from status module"
        )

        # Must not import from any other script in the scripts directory
        scripts_dir = script_path.parent
        other_scripts = [
            f.stem for f in scripts_dir.iterdir()
            if f.suffix == ".py" and f.name != "progress_dashboard.py"
            and f.name != "__init__.py"
        ]
        for script_name in other_scripts:
            assert script_name not in imported_modules, (
                f"progress_dashboard.py must not import from {script_name}"
            )
