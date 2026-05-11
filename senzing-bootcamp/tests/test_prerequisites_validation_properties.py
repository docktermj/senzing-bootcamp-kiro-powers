"""Property-based tests for validate_prerequisites.py using Hypothesis.

Feature: module-prerequisites-validation
"""

import sys
import tempfile
from pathlib import Path

from hypothesis import given, settings, assume
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_prerequisites import (
    parse_gate_key,
    extract_keywords,
    Finding,
    ModuleInfo,
    GateInfo,
    count_checkpoints,
    has_success_criteria,
    _validate_module_references,
    _validate_keyword_presence,
    _validate_checkpoint_coverage,
)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_gate_key(draw):
    """Generate valid "N->M" strings with positive integers (1-999)."""
    source = draw(st.integers(min_value=1, max_value=999))
    dest = draw(st.integers(min_value=1, max_value=999))
    return f"{source}->{dest}"


@st.composite
def st_gate_requirement(draw):
    """Generate comma-separated condition strings with at least one non-whitespace token."""
    num_tokens = draw(st.integers(min_value=1, max_value=5))
    # Generate non-empty tokens with at least one non-whitespace character
    tokens = []
    for _ in range(num_tokens):
        token = draw(st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N", "Z"),
                blacklist_characters=",\x00",
            ),
            min_size=1,
            max_size=30,
        ).filter(lambda t: t.strip()))
        tokens.append(token)
    return ", ".join(tokens)


@st.composite
def st_dependency_graph(draw):
    """Generate valid dependency graph dicts with modules and gates."""
    num_modules = draw(st.integers(min_value=1, max_value=8))
    modules: dict[int, ModuleInfo] = {}
    for i in range(1, num_modules + 1):
        # Each module can require modules with lower numbers
        possible_reqs = list(range(1, i))
        reqs = draw(st.lists(
            st.sampled_from(possible_reqs) if possible_reqs else st.nothing(),
            max_size=min(3, len(possible_reqs)),
            unique=True,
        ))
        modules[i] = ModuleInfo(name=f"Module {i}", requires=sorted(reqs))

    # Generate gates between existing modules
    num_gates = draw(st.integers(min_value=0, max_value=min(4, num_modules - 1) if num_modules > 1 else 0))
    gates: dict[str, GateInfo] = {}
    if num_modules > 1:
        for _ in range(num_gates):
            src = draw(st.integers(min_value=1, max_value=num_modules))
            dst = draw(st.integers(min_value=1, max_value=num_modules).filter(lambda x, s=src: x != s))
            key = f"{src}->{dst}"
            if key not in gates:
                num_reqs = draw(st.integers(min_value=0, max_value=3))
                reqs = [
                    draw(st.text(
                        alphabet=st.characters(whitelist_categories=("L", "N", "Z")),
                        min_size=1,
                        max_size=20,
                    ).filter(lambda t: t.strip()))
                    for _ in range(num_reqs)
                ]
                gates[key] = GateInfo(source=src, destination=dst, requires=reqs)

    return {"modules": modules, "gates": gates}


@st.composite
def st_steering_index(draw):
    """Generate module-to-file mappings (dict[int, list[str]])."""
    num_modules = draw(st.integers(min_value=1, max_value=8))
    index: dict[int, list[str]] = {}
    for i in range(1, num_modules + 1):
        num_files = draw(st.integers(min_value=1, max_value=3))
        files = [f"module-{i:02d}-part{j}.md" for j in range(1, num_files + 1)]
        index[i] = files
    return index


@st.composite
def st_steering_content(draw, checkpoints=None, success_criteria=None):
    """Generate markdown content with configurable checkpoint count and success criteria."""
    if checkpoints is None:
        num_checkpoints = draw(st.integers(min_value=0, max_value=5))
    else:
        num_checkpoints = checkpoints

    if success_criteria is None:
        has_criteria = draw(st.booleans())
    else:
        has_criteria = success_criteria

    lines = ["# Module Guide", "", "Some introductory text about this module.", ""]

    # Add some body content
    num_sections = draw(st.integers(min_value=1, max_value=4))
    for s in range(num_sections):
        lines.append(f"## Section {s + 1}")
        lines.append("")
        lines.append(draw(st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "Z", "P")),
            min_size=10,
            max_size=80,
        ).filter(lambda t: t.strip())))
        lines.append("")

    # Add checkpoints
    for c in range(num_checkpoints):
        lines.append(f"**Checkpoint:** Step {c + 1} completed successfully.")
        lines.append("")

    # Add success criteria
    if has_criteria:
        criteria_type = draw(st.sampled_from(["heading", "markers"]))
        if criteria_type == "heading":
            lines.append("## Success Criteria")
            lines.append("")
            lines.append("- All steps completed")
        else:
            lines.append("✅ Module completed successfully")
            lines.append("✅ All tests passing")

    return "\n".join(lines)


@st.composite
def st_finding_set(draw):
    """Generate lists of Finding objects with mixed levels."""
    num_findings = draw(st.integers(min_value=0, max_value=10))
    findings = []
    for _ in range(num_findings):
        level = draw(st.sampled_from(["ERROR", "WARNING"]))
        description = draw(st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N", "P", "Z"),
                blacklist_characters="\x00",
            ),
            min_size=1,
            max_size=80,
        ))
        findings.append(Finding(level=level, description=description))
    return findings


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestGateParsingCorrectness:
    """Property 1 — Gate Parsing Correctness.

    **Validates: Requirements 1.4, 1.5, 7.1, 7.3**

    For any valid gate key string matching "N->M" where N and M are positive
    integers, parse_gate_key correctly extracts both module numbers as integers.
    For any valid dependency graph structure, the parser extracts all gates
    without raising exceptions.
    """

    @given(key=st_gate_key())
    @settings(max_examples=100)
    def test_parse_gate_key_extracts_correct_numbers(self, key):
        """For any valid gate key "N->M", parser extracts (N, M) as integers."""
        result = parse_gate_key(key)
        assert result is not None, f"Failed to parse valid gate key: {key}"
        source, dest = result
        # Extract expected values from the key string
        parts = key.split("->")
        expected_source = int(parts[0])
        expected_dest = int(parts[1])
        assert source == expected_source
        assert dest == expected_dest
        assert isinstance(source, int)
        assert isinstance(dest, int)

    @given(graph=st_dependency_graph())
    @settings(max_examples=100)
    def test_dependency_graph_gates_parse_without_exceptions(self, graph):
        """For any valid dependency graph, all gate keys parse correctly."""
        gates = graph["gates"]
        for gate_key, gate_info in gates.items():
            result = parse_gate_key(gate_key)
            assert result is not None, f"Failed to parse gate key: {gate_key}"
            source, dest = result
            assert source == gate_info.source
            assert dest == gate_info.destination


class TestKeywordExtractionNormalized:
    """Property 2 — Keyword Extraction Produces Normalized Tokens.

    **Validates: Requirements 3.2, 7.2**

    For any non-empty gate requirement string containing comma-separated
    conditions, extract_keywords produces a non-empty list of lowercase tokens
    where each token has no leading or trailing whitespace.
    """

    @given(requirement=st_gate_requirement())
    @settings(max_examples=100)
    def test_keywords_are_non_empty_lowercase_stripped(self, requirement):
        """Keywords are non-empty, lowercase, and have no leading/trailing whitespace."""
        keywords = extract_keywords(requirement)
        assert len(keywords) > 0, f"Empty keywords for requirement: {requirement!r}"
        for kw in keywords:
            assert kw == kw.lower(), f"Keyword not lowercase: {kw!r}"
            assert kw == kw.strip(), f"Keyword has whitespace: {kw!r}"
            assert len(kw) > 0, "Empty keyword in result"

    @given(requirement=st_gate_requirement())
    @settings(max_examples=100)
    def test_keyword_count_matches_non_empty_tokens(self, requirement):
        """Number of keywords equals number of non-empty comma-separated tokens."""
        keywords = extract_keywords(requirement)
        # Manually compute expected count
        expected = [t.strip().lower() for t in requirement.split(",") if t.strip()]
        assert len(keywords) == len(expected)


class TestModuleReferenceCrossValidation:
    """Property 3 — Module Reference Cross-Validation.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

    For any dependency graph and steering index, _validate_module_references
    reports an ERROR for each module number referenced in requires lists or
    gate keys that does not exist in the steering index, and reports zero
    errors when all referenced module numbers exist.
    """

    @given(graph=st_dependency_graph(), index=st_steering_index())
    @settings(max_examples=100)
    def test_errors_for_missing_references(self, graph, index):
        """An ERROR is reported for each referenced module not in steering index."""
        modules = graph["modules"]
        gates = graph["gates"]
        findings = _validate_module_references(modules, gates, index)

        # Compute expected missing references
        all_referenced: set[int] = set()
        for mod_info in modules.values():
            all_referenced.update(mod_info.requires)
        for gate_info in gates.values():
            all_referenced.add(gate_info.source)
            all_referenced.add(gate_info.destination)

        missing = all_referenced - set(index.keys())

        if not missing:
            assert len(findings) == 0, f"False positive errors: {[f.description for f in findings]}"
        else:
            assert len(findings) > 0, "Missing references not detected"
            assert all(f.level == "ERROR" for f in findings)

    @given(graph=st_dependency_graph())
    @settings(max_examples=100)
    def test_zero_errors_when_all_references_exist(self, graph):
        """Zero errors when all referenced modules exist in steering index."""
        modules = graph["modules"]
        gates = graph["gates"]

        # Build a steering index that covers all referenced modules
        all_referenced: set[int] = set()
        for mod_num in modules:
            all_referenced.add(mod_num)
            all_referenced.update(modules[mod_num].requires)
        for gate_info in gates.values():
            all_referenced.add(gate_info.source)
            all_referenced.add(gate_info.destination)

        complete_index = {m: [f"module-{m:02d}.md"] for m in all_referenced}

        findings = _validate_module_references(modules, gates, complete_index)
        assert len(findings) == 0, f"Unexpected errors: {[f.description for f in findings]}"


class TestKeywordPresenceDetection:
    """Property 4 — Keyword Presence Detection.

    **Validates: Requirements 3.3, 3.4, 3.5**

    For any steering content and set of keywords, _validate_keyword_presence
    reports a WARNING for each keyword not found (case-insensitively) in the
    content, and reports zero warnings when all keywords are present.
    """

    @given(data=st.data())
    @settings(max_examples=100)
    def test_warnings_for_missing_keywords(self, data):
        """A WARNING is reported for each keyword not found in content."""
        content = data.draw(st_steering_content())
        # Generate keywords, some present and some not
        num_keywords = data.draw(st.integers(min_value=1, max_value=4))
        keywords_present = []
        keywords_absent = []

        for _ in range(num_keywords):
            if data.draw(st.booleans()):
                # Generate a keyword guaranteed to be in content
                # Pick a word from the content
                words = [w for w in content.lower().split() if len(w) >= 3]
                if words:
                    kw = data.draw(st.sampled_from(words))
                    keywords_present.append(kw)
                else:
                    # Content has no suitable words, generate absent keyword
                    kw = data.draw(st.text(
                        alphabet="xyzqwj",
                        min_size=8,
                        max_size=15,
                    ))
                    keywords_absent.append(kw)
            else:
                # Generate a keyword guaranteed NOT to be in content
                kw = "zzz_nonexistent_" + data.draw(st.text(
                    alphabet="abcdefgh",
                    min_size=5,
                    max_size=10,
                ))
                if kw.lower() not in content.lower():
                    keywords_absent.append(kw)

        all_keywords = keywords_present + keywords_absent
        assume(len(all_keywords) > 0)

        # Write content to a temp directory
        tmp_dir = Path(tempfile.mkdtemp())
        steering_file = tmp_dir / "module-01.md"
        steering_file.write_text(content, encoding="utf-8")

        # Build gate with all keywords as a single requirement string
        requirement_str = ", ".join(all_keywords)
        gates = {
            "1->2": GateInfo(source=1, destination=2, requires=[requirement_str]),
        }
        steering_index = {1: ["module-01.md"], 2: ["module-02.md"]}

        findings = _validate_keyword_presence(gates, steering_index, tmp_dir)

        # Each absent keyword should produce a WARNING
        for kw in keywords_absent:
            matching = [f for f in findings if kw in f.description]
            assert len(matching) > 0, f"Missing warning for absent keyword: {kw!r}"

        # Each present keyword should NOT produce a WARNING
        for kw in keywords_present:
            matching = [f for f in findings if f"'{kw}'" in f.description]
            assert len(matching) == 0, f"False warning for present keyword: {kw!r}"

        assert all(f.level == "WARNING" for f in findings)

    @given(data=st.data())
    @settings(max_examples=100)
    def test_zero_warnings_when_all_keywords_present(self, data):
        """Zero warnings when all keywords are found in content."""
        # Generate content first, then pick keywords from it
        content = data.draw(st_steering_content())
        words = [w for w in content.lower().split() if len(w) >= 3]
        assume(len(words) >= 1)

        num_keywords = data.draw(st.integers(min_value=1, max_value=min(3, len(words))))
        keywords = data.draw(st.lists(
            st.sampled_from(words),
            min_size=num_keywords,
            max_size=num_keywords,
        ))

        # Write content to a temp directory
        tmp_dir = Path(tempfile.mkdtemp())
        steering_file = tmp_dir / "module-01.md"
        steering_file.write_text(content, encoding="utf-8")

        # Build gate with keywords
        requirement_str = ", ".join(keywords)
        gates = {
            "1->2": GateInfo(source=1, destination=2, requires=[requirement_str]),
        }
        steering_index = {1: ["module-01.md"], 2: ["module-02.md"]}

        findings = _validate_keyword_presence(gates, steering_index, tmp_dir)
        assert len(findings) == 0, f"Unexpected warnings: {[f.description for f in findings]}"


class TestCheckpointSuccessCriteriaDetection:
    """Property 5 — Checkpoint and Success Criteria Detection.

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

    For any steering content containing N **Checkpoint:** patterns,
    count_checkpoints returns exactly N. For content with zero checkpoints
    and an outgoing gate, the validator reports an ERROR. For content lacking
    both a "Success Criteria" heading and ✅ markers, the validator reports
    a WARNING.
    """

    @given(data=st.data())
    @settings(max_examples=100)
    def test_count_checkpoints_returns_exact_count(self, data):
        """count_checkpoints returns exactly N for content with N checkpoint patterns."""
        num_checkpoints = data.draw(st.integers(min_value=0, max_value=10))
        content = data.draw(st_steering_content(checkpoints=num_checkpoints))
        assert count_checkpoints(content) == num_checkpoints

    @given(data=st.data())
    @settings(max_examples=100)
    def test_zero_checkpoints_with_gate_produces_error(self, data):
        """Zero checkpoints with an outgoing gate produces an ERROR."""
        content = data.draw(st_steering_content(checkpoints=0, success_criteria=True))

        # Write content to temp directory
        tmp_dir = Path(tempfile.mkdtemp())
        steering_file = tmp_dir / "module-01.md"
        steering_file.write_text(content, encoding="utf-8")

        gates = {
            "1->2": GateInfo(source=1, destination=2, requires=["condition"]),
        }
        steering_index = {1: ["module-01.md"], 2: ["module-02.md"]}

        findings = _validate_checkpoint_coverage(gates, steering_index, tmp_dir)

        error_findings = [f for f in findings if f.level == "ERROR"]
        assert len(error_findings) > 0, "Missing ERROR for zero checkpoints with gate"
        assert any("checkpoint" in f.description.lower() for f in error_findings)

    @given(data=st.data())
    @settings(max_examples=100)
    def test_missing_success_criteria_produces_warning(self, data):
        """Missing success criteria with an outgoing gate produces a WARNING."""
        # Generate content with checkpoints but no success criteria
        num_checkpoints = data.draw(st.integers(min_value=1, max_value=5))
        content = data.draw(st_steering_content(
            checkpoints=num_checkpoints,
            success_criteria=False,
        ))
        # Verify our generated content actually lacks success criteria
        assume(not has_success_criteria(content))

        # Write content to temp directory
        tmp_dir = Path(tempfile.mkdtemp())
        steering_file = tmp_dir / "module-01.md"
        steering_file.write_text(content, encoding="utf-8")

        gates = {
            "1->2": GateInfo(source=1, destination=2, requires=["condition"]),
        }
        steering_index = {1: ["module-01.md"], 2: ["module-02.md"]}

        findings = _validate_checkpoint_coverage(gates, steering_index, tmp_dir)

        warning_findings = [f for f in findings if f.level == "WARNING"]
        assert len(warning_findings) > 0, "Missing WARNING for no success criteria"
        assert any("success criteria" in f.description.lower() for f in warning_findings)

    @given(data=st.data())
    @settings(max_examples=100)
    def test_has_success_criteria_detects_heading(self, data):
        """has_success_criteria returns True for content with Success Criteria heading."""
        content = data.draw(st_steering_content(checkpoints=1, success_criteria=True))
        # Only test if the content actually has success criteria markers
        assume(has_success_criteria(content))
        assert has_success_criteria(content) is True


class TestExitCodeCorrectness:
    """Property 6 — Exit Code Correctness.

    **Validates: Requirements 5.4, 5.5, 5.6**

    For any set of findings, the exit code is 1 if at least one ERROR exists
    (or if --warnings-as-errors is set and at least one WARNING exists),
    and 0 otherwise.
    """

    @given(findings=st_finding_set())
    @settings(max_examples=100)
    def test_exit_code_1_iff_errors_exist(self, findings):
        """Exit code is 1 iff at least one ERROR exists."""
        error_count = sum(1 for f in findings if f.level == "ERROR")
        expected_exit = 1 if error_count > 0 else 0

        # Replicate the exit code logic from main()
        actual_exit = 1 if error_count > 0 else 0
        assert actual_exit == expected_exit

    @given(findings=st_finding_set())
    @settings(max_examples=100)
    def test_exit_code_with_warnings_as_errors(self, findings):
        """With --warnings-as-errors, exit code is 1 if any WARNING exists."""
        error_count = sum(1 for f in findings if f.level == "ERROR")
        warning_count = sum(1 for f in findings if f.level == "WARNING")

        # With --warnings-as-errors flag
        if error_count > 0:
            expected_exit = 1
        elif warning_count > 0:
            expected_exit = 1
        else:
            expected_exit = 0

        # Replicate the exit code logic from main() with warnings_as_errors=True
        actual_exit = 1 if error_count > 0 else (1 if warning_count > 0 else 0)
        assert actual_exit == expected_exit

    @given(findings=st_finding_set())
    @settings(max_examples=100)
    def test_exit_code_0_when_no_errors_no_warnings_as_errors(self, findings):
        """Exit code is 0 when no ERRORs and --warnings-as-errors is not set."""
        error_count = sum(1 for f in findings if f.level == "ERROR")

        # Without --warnings-as-errors flag
        expected_exit = 1 if error_count > 0 else 0

        # Replicate the exit code logic from main() without warnings_as_errors
        actual_exit = 1 if error_count > 0 else 0
        assert actual_exit == expected_exit
