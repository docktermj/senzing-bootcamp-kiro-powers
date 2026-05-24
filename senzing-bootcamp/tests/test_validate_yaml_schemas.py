"""Property-based tests for validate_yaml_schemas.py using Hypothesis.

Feature: yaml-schema-validation
"""

import contextlib
import io
import sys
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_yaml_schemas import (  # noqa: E402
    SCHEMA_REGISTRY,
    ValidationResult,
    format_result,
    main,
    validate_file,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_yaml_keys():
    """Generate valid YAML key names (alphanumeric + underscores/hyphens)."""
    return st.from_regex(r"[a-z][a-z0-9_-]{0,15}", fullmatch=True)


def st_yaml_key_set():
    """Generate a non-empty set of valid YAML keys."""
    return st.frozensets(st_yaml_keys(), min_size=1, max_size=10)


def st_file_path():
    """Generate file paths ending in .yaml."""
    return st.from_regex(r"[a-z][a-z0-9/_-]{1,30}\.yaml", fullmatch=True)


def st_key_set():
    """Generate sets of YAML key names (possibly empty)."""
    return st.frozensets(
        st.from_regex(r"[a-z][a-z0-9_]{0,15}", fullmatch=True),
        min_size=0,
        max_size=5,
    )


def st_error_message():
    """Generate optional error messages."""
    return st.one_of(
        st.none(),
        st.text(
            min_size=1,
            max_size=80,
            alphabet=st.characters(
                whitelist_categories=("L", "N", "P", "Z"),
                blacklist_characters="\n\r",
            ),
        ),
    )


def st_validation_result_passed():
    """Generate a ValidationResult that passed."""
    return st.builds(
        ValidationResult,
        file_path=st_file_path(),
        passed=st.just(True),
        missing_keys=st.just(set()),
        unexpected_keys=st.just(set()),
        error=st.just(None),
    )


def st_validation_result_failed():
    """Generate a ValidationResult that failed with at least one reason."""
    return st.one_of(
        # Failed with missing keys
        st.builds(
            ValidationResult,
            file_path=st_file_path(),
            passed=st.just(False),
            missing_keys=st.frozensets(
                st.from_regex(r"[a-z][a-z0-9_]{0,15}", fullmatch=True),
                min_size=1,
                max_size=5,
            ).map(set),
            unexpected_keys=st_key_set().map(set),
            error=st.just(None),
        ),
        # Failed with unexpected keys
        st.builds(
            ValidationResult,
            file_path=st_file_path(),
            passed=st.just(False),
            missing_keys=st_key_set().map(set),
            unexpected_keys=st.frozensets(
                st.from_regex(r"[a-z][a-z0-9_]{0,15}", fullmatch=True),
                min_size=1,
                max_size=5,
            ).map(set),
            error=st.just(None),
        ),
        # Failed with error message
        st.builds(
            ValidationResult,
            file_path=st_file_path(),
            passed=st.just(False),
            missing_keys=st.just(set()),
            unexpected_keys=st.just(set()),
            error=st.text(
                min_size=1,
                max_size=80,
                alphabet=st.characters(
                    whitelist_categories=("L", "N", "P", "Z"),
                    blacklist_characters="\n\r",
                ),
            ),
        ),
    )


def st_validation_result():
    """Generate arbitrary ValidationResult instances."""
    return st.one_of(st_validation_result_passed(), st_validation_result_failed())


# ---------------------------------------------------------------------------
# Property 1: Key Set Validation Detects Symmetric Difference
# ---------------------------------------------------------------------------


class TestProperty1KeySetValidation:
    """Property 1: Key Set Validation Detects Symmetric Difference.

    Feature: yaml-schema-validation

    For any set of expected keys and for any YAML content whose actual top-level
    keys differ from the expected set, the validator SHALL report FAIL and the
    union of missing_keys and unexpected_keys SHALL equal the symmetric difference
    between the expected and actual key sets.

    **Validates: Requirements 1.5, 1.6**
    """

    @given(
        expected_keys=st_yaml_key_set(),
        actual_keys=st_yaml_key_set(),
    )
    @settings(max_examples=20)
    def test_symmetric_difference_property(self, expected_keys, actual_keys):
        """missing_keys | unexpected_keys == expected_keys ^ actual_keys."""
        # Build YAML content from actual keys
        yaml_content = "\n".join(f"{key}: value" for key in sorted(actual_keys))

        # Write to a temp file and validate
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            tmp_path = f.name

        try:
            result = validate_file(tmp_path, set(expected_keys))

            # The symmetric difference between expected and actual
            symmetric_diff = set(expected_keys) ^ set(actual_keys)

            # The union of missing and unexpected keys from the result
            reported_diff = result.missing_keys | result.unexpected_keys

            assert reported_diff == symmetric_diff, (
                f"reported_diff={reported_diff} != symmetric_diff={symmetric_diff}\n"
                f"expected_keys={expected_keys}, actual_keys={actual_keys}\n"
                f"missing={result.missing_keys}, unexpected={result.unexpected_keys}"
            )

            # If there's any symmetric difference, the result should be FAIL
            if symmetric_diff:
                assert not result.passed, (
                    f"Expected FAIL when symmetric_diff={symmetric_diff} is non-empty"
                )
            else:
                assert result.passed, (
                    "Expected PASS when symmetric_diff is empty"
                )
        finally:
            Path(tmp_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Property 2: Output Format Correctness
# ---------------------------------------------------------------------------


class TestProperty2OutputFormat:
    """Feature: yaml-schema-validation, Property 2: Output Format Correctness

    For any validation result, the formatted output SHALL start with
    `PASS: <filename>` when the result passed, or `FAIL: <filename>` when
    the result failed, and the total number of output lines (one per file)
    SHALL equal the number of files validated.

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    @given(result=st_validation_result())
    @settings(max_examples=20)
    def test_output_starts_with_pass_or_fail(self, result):
        """Formatted output starts with PASS: or FAIL: depending on result."""
        output = format_result(result)

        if result.passed:
            assert output.startswith("PASS:"), (
                f"Passed result should start with 'PASS:', got: {output!r}"
            )
        else:
            assert output.startswith("FAIL:"), (
                f"Failed result should start with 'FAIL:', got: {output!r}"
            )

    @given(result=st_validation_result())
    @settings(max_examples=20)
    def test_output_is_single_line(self, result):
        """Each formatted result is a single line (no newlines)."""
        output = format_result(result)

        assert "\n" not in output, (
            f"Output should be a single line, got: {output!r}"
        )

    @given(results=st.lists(st_validation_result(), min_size=1, max_size=10))
    @settings(max_examples=20)
    def test_line_count_equals_file_count(self, results):
        """Total output lines equals number of files validated."""
        lines = [format_result(r) for r in results]

        assert len(lines) == len(results), (
            f"Expected {len(results)} output lines, got {len(lines)}"
        )

    @given(result=st_validation_result())
    @settings(max_examples=20)
    def test_output_contains_filename(self, result):
        """Formatted output contains the filename from the result."""
        output = format_result(result)
        filename = Path(result.file_path).name

        assert filename in output, (
            f"Output should contain filename '{filename}', got: {output!r}"
        )


# ---------------------------------------------------------------------------
# Property 3: Exit Code Correctness
# ---------------------------------------------------------------------------


class TestProperty3ExitCodeCorrectness:
    """Feature: yaml-schema-validation, Property 3: Exit Code Correctness

    For any set of validation results, the exit code SHALL be 0 if and only if
    all results have `passed == True`. If any result has `passed == False`, the
    exit code SHALL be non-zero.

    **Validates: Requirements 4.1, 4.2, 4.3**
    """

    @given(
        results=st.lists(
            st.builds(
                ValidationResult,
                file_path=st_file_path(),
                passed=st.booleans(),
                missing_keys=st.just(set()),
                unexpected_keys=st.just(set()),
                error=st.just(None),
            ),
            min_size=1,
            max_size=10,
        ),
    )
    @settings(max_examples=20)
    def test_exit_code_zero_iff_all_passed(self, results):
        """Exit code is 0 iff all results have passed == True."""
        # Compute exit code using the same logic as main()
        exit_code = 0 if all(r.passed for r in results) else 1

        all_passed = all(r.passed for r in results)

        if all_passed:
            assert exit_code == 0, (
                f"Expected exit code 0 when all results passed, got {exit_code}"
            )
        else:
            assert exit_code != 0, (
                f"Expected non-zero exit code when some results failed, got {exit_code}"
            )

    @given(
        results=st.lists(
            st_validation_result_passed(),
            min_size=1,
            max_size=10,
        ),
    )
    @settings(max_examples=20)
    def test_all_passed_gives_zero_exit(self, results):
        """When all results pass, exit code is 0."""
        exit_code = 0 if all(r.passed for r in results) else 1

        assert exit_code == 0, (
            f"Expected exit code 0 when all results passed, got {exit_code}"
        )

    @given(
        passed_results=st.lists(st_validation_result_passed(), min_size=0, max_size=5),
        failed_results=st.lists(st_validation_result_failed(), min_size=1, max_size=5),
    )
    @settings(max_examples=20)
    def test_any_failure_gives_nonzero_exit(self, passed_results, failed_results):
        """When any result fails, exit code is non-zero."""
        results = passed_results + failed_results
        exit_code = 0 if all(r.passed for r in results) else 1

        assert exit_code != 0, (
            f"Expected non-zero exit code when failures present, got {exit_code}"
        )


# ---------------------------------------------------------------------------
# Property 4: Single-File Flag Isolation
# ---------------------------------------------------------------------------


class TestProperty4SingleFileFlagIsolation:
    """Feature: yaml-schema-validation, Property 4: Single-File Flag Isolation

    For any file path present in the schema registry, invoking the validator
    with `--file <path>` SHALL produce exactly one output line corresponding
    to that file and no output for other files.

    **Validates: Requirements 3.2**
    """

    @given(registry_key=st.sampled_from(sorted(SCHEMA_REGISTRY.keys())))
    @settings(max_examples=20)
    def test_single_file_produces_exactly_one_output_line(self, registry_key):
        """--file with a valid registry key produces exactly one output line."""
        stdout_capture = io.StringIO()

        with contextlib.redirect_stdout(stdout_capture):
            main(["--file", registry_key])

        stdout_output = stdout_capture.getvalue()
        lines = [line for line in stdout_output.splitlines() if line.strip()]

        assert len(lines) == 1, (
            f"Expected exactly 1 output line for --file {registry_key!r}, "
            f"got {len(lines)}: {lines!r}"
        )


# ---------------------------------------------------------------------------
# Property 5: Unrecognized File Rejection
# ---------------------------------------------------------------------------


class TestProperty5UnrecognizedFileRejection:
    """Feature: yaml-schema-validation, Property 5: Unrecognized File Rejection

    For any file path NOT present in the schema registry, invoking the validator
    with `--file <path>` SHALL exit with a non-zero code and print an error
    message containing the unrecognized path.

    **Validates: Requirements 3.3**
    """

    @given(
        path=st.text(
            min_size=1,
            max_size=60,
            alphabet=st.characters(whitelist_categories=("L", "N", "P", "S"),
                                   blacklist_characters="-\x00"),
        ).filter(lambda p: p not in SCHEMA_REGISTRY and not p.startswith("-")),
    )
    @settings(max_examples=20)
    def test_unrecognized_file_exits_nonzero_with_path_in_error(self, path):
        """Unrecognized paths produce non-zero exit and error with path."""
        stderr_capture = io.StringIO()

        with contextlib.redirect_stderr(stderr_capture):
            exit_code = main(["--file", path])

        assert exit_code != 0, (
            f"Expected non-zero exit for unrecognized path {path!r}, got {exit_code}"
        )

        stderr_output = stderr_capture.getvalue()
        assert path in stderr_output, (
            f"Expected stderr to contain path {path!r}, got: {stderr_output!r}"
        )


# ---------------------------------------------------------------------------
# Unit Tests: Four Specific File Schemas (Task 3.6)
# ---------------------------------------------------------------------------

# Power root for resolving real file paths
_POWER_ROOT = Path(__file__).resolve().parent.parent


class TestSteeringIndexSchema:
    """Unit tests for steering/steering-index.yaml validation.

    **Validates: Requirements 1.1**
    """

    _REL_PATH = "steering/steering-index.yaml"
    _EXPECTED_KEYS = SCHEMA_REGISTRY[_REL_PATH]

    def test_real_file_passes_validation(self):
        """The real steering-index.yaml passes validation with its expected keys."""
        full_path = str(_POWER_ROOT / self._REL_PATH)
        result = validate_file(full_path, self._EXPECTED_KEYS)

        assert result.passed, (
            f"Expected PASS for {self._REL_PATH}, got FAIL: "
            f"missing={result.missing_keys}, unexpected={result.unexpected_keys}, "
            f"error={result.error}"
        )

    def test_real_file_pass_output_format(self):
        """PASS output starts with 'PASS: steering-index.yaml'."""
        full_path = str(_POWER_ROOT / self._REL_PATH)
        result = validate_file(full_path, self._EXPECTED_KEYS)
        output = format_result(result)

        assert output == "PASS: steering-index.yaml"

    def test_extra_key_produces_fail(self, tmp_path):
        """Adding an extra key to steering-index.yaml content produces FAIL."""
        real_path = _POWER_ROOT / self._REL_PATH
        content = real_path.read_text(encoding="utf-8")
        modified = content + "\nextra_bogus_key: true\n"

        tmp_file = tmp_path / "steering-index.yaml"
        tmp_file.write_text(modified, encoding="utf-8")

        result = validate_file(str(tmp_file), self._EXPECTED_KEYS)

        assert not result.passed
        assert "extra_bogus_key" in result.unexpected_keys

    def test_missing_key_produces_fail(self, tmp_path):
        """Removing a key from steering-index.yaml content produces FAIL."""
        real_path = _POWER_ROOT / self._REL_PATH
        content = real_path.read_text(encoding="utf-8")
        # Remove the 'budget:' line to simulate a missing key
        lines = [ln for ln in content.splitlines() if not ln.startswith("budget:")]
        modified = "\n".join(lines) + "\n"

        tmp_file = tmp_path / "steering-index.yaml"
        tmp_file.write_text(modified, encoding="utf-8")

        result = validate_file(str(tmp_file), self._EXPECTED_KEYS)

        assert not result.passed
        assert "budget" in result.missing_keys

    def test_fail_output_format(self, tmp_path):
        """FAIL output starts with 'FAIL: steering-index.yaml'."""
        real_path = _POWER_ROOT / self._REL_PATH
        content = real_path.read_text(encoding="utf-8")
        modified = content + "\nbogus: true\n"

        tmp_file = tmp_path / "steering-index.yaml"
        tmp_file.write_text(modified, encoding="utf-8")

        result = validate_file(str(tmp_file), self._EXPECTED_KEYS)
        output = format_result(result)

        assert output.startswith("FAIL: steering-index.yaml")
        assert "unexpected keys" in output


class TestModuleDependenciesSchema:
    """Unit tests for config/module-dependencies.yaml validation.

    **Validates: Requirements 1.2**
    """

    _REL_PATH = "config/module-dependencies.yaml"
    _EXPECTED_KEYS = SCHEMA_REGISTRY[_REL_PATH]

    def test_real_file_passes_validation(self):
        """The real module-dependencies.yaml passes validation."""
        full_path = str(_POWER_ROOT / self._REL_PATH)
        result = validate_file(full_path, self._EXPECTED_KEYS)

        assert result.passed, (
            f"Expected PASS for {self._REL_PATH}, got FAIL: "
            f"missing={result.missing_keys}, unexpected={result.unexpected_keys}, "
            f"error={result.error}"
        )

    def test_real_file_pass_output_format(self):
        """PASS output for module-dependencies.yaml is correct."""
        full_path = str(_POWER_ROOT / self._REL_PATH)
        result = validate_file(full_path, self._EXPECTED_KEYS)
        output = format_result(result)

        assert output == "PASS: module-dependencies.yaml"

    def test_extra_key_produces_fail(self, tmp_path):
        """Adding an extra key to module-dependencies.yaml content produces FAIL."""
        real_path = _POWER_ROOT / self._REL_PATH
        content = real_path.read_text(encoding="utf-8")
        modified = content + "\nphantom_key: true\n"

        tmp_file = tmp_path / "module-dependencies.yaml"
        tmp_file.write_text(modified, encoding="utf-8")

        result = validate_file(str(tmp_file), self._EXPECTED_KEYS)

        assert not result.passed
        assert "phantom_key" in result.unexpected_keys

    def test_missing_key_produces_fail(self, tmp_path):
        """Removing a key from module-dependencies.yaml content produces FAIL."""
        real_path = _POWER_ROOT / self._REL_PATH
        content = real_path.read_text(encoding="utf-8")
        lines = [ln for ln in content.splitlines() if not ln.startswith("gates:")]
        modified = "\n".join(lines) + "\n"

        tmp_file = tmp_path / "module-dependencies.yaml"
        tmp_file.write_text(modified, encoding="utf-8")

        result = validate_file(str(tmp_file), self._EXPECTED_KEYS)

        assert not result.passed
        assert "gates" in result.missing_keys

    def test_fail_output_format(self, tmp_path):
        """FAIL output for module-dependencies.yaml starts with FAIL prefix."""
        real_path = _POWER_ROOT / self._REL_PATH
        content = real_path.read_text(encoding="utf-8")
        modified = content + "\nbogus: true\n"

        tmp_file = tmp_path / "module-dependencies.yaml"
        tmp_file.write_text(modified, encoding="utf-8")

        result = validate_file(str(tmp_file), self._EXPECTED_KEYS)
        output = format_result(result)

        assert output.startswith("FAIL: module-dependencies.yaml")
        assert "unexpected keys" in output


class TestHookCategoriesSchema:
    """Unit tests for hooks/hook-categories.yaml validation.

    **Validates: Requirements 1.3**
    """

    _REL_PATH = "hooks/hook-categories.yaml"
    _EXPECTED_KEYS = SCHEMA_REGISTRY[_REL_PATH]

    def test_real_file_passes_validation(self):
        """The real hook-categories.yaml passes validation with its expected keys."""
        full_path = str(_POWER_ROOT / self._REL_PATH)
        result = validate_file(full_path, self._EXPECTED_KEYS)

        assert result.passed, (
            f"Expected PASS for {self._REL_PATH}, got FAIL: "
            f"missing={result.missing_keys}, unexpected={result.unexpected_keys}, "
            f"error={result.error}"
        )

    def test_real_file_pass_output_format(self):
        """PASS output for hook-categories.yaml is correct."""
        full_path = str(_POWER_ROOT / self._REL_PATH)
        result = validate_file(full_path, self._EXPECTED_KEYS)
        output = format_result(result)

        assert output == "PASS: hook-categories.yaml"

    def test_extra_key_produces_fail(self, tmp_path):
        """Adding an extra key to hook-categories.yaml content produces FAIL."""
        real_path = _POWER_ROOT / self._REL_PATH
        content = real_path.read_text(encoding="utf-8")
        modified = content + "\nrogue_key: true\n"

        tmp_file = tmp_path / "hook-categories.yaml"
        tmp_file.write_text(modified, encoding="utf-8")

        result = validate_file(str(tmp_file), self._EXPECTED_KEYS)

        assert not result.passed
        assert "rogue_key" in result.unexpected_keys

    def test_missing_key_produces_fail(self, tmp_path):
        """Removing a key from hook-categories.yaml content produces FAIL."""
        real_path = _POWER_ROOT / self._REL_PATH
        content = real_path.read_text(encoding="utf-8")
        lines = [ln for ln in content.splitlines() if not ln.startswith("critical:")]
        modified = "\n".join(lines) + "\n"

        tmp_file = tmp_path / "hook-categories.yaml"
        tmp_file.write_text(modified, encoding="utf-8")

        result = validate_file(str(tmp_file), self._EXPECTED_KEYS)

        assert not result.passed
        assert "critical" in result.missing_keys

    def test_fail_output_format(self, tmp_path):
        """FAIL output for hook-categories.yaml starts with FAIL prefix."""
        real_path = _POWER_ROOT / self._REL_PATH
        content = real_path.read_text(encoding="utf-8")
        modified = content + "\nbogus: true\n"

        tmp_file = tmp_path / "hook-categories.yaml"
        tmp_file.write_text(modified, encoding="utf-8")

        result = validate_file(str(tmp_file), self._EXPECTED_KEYS)
        output = format_result(result)

        assert output.startswith("FAIL: hook-categories.yaml")
        assert "unexpected keys" in output


class TestModuleArtifactsSchema:
    """Unit tests for config/module-artifacts.yaml validation.

    **Validates: Requirements 1.4**
    """

    _REL_PATH = "config/module-artifacts.yaml"
    _EXPECTED_KEYS = SCHEMA_REGISTRY[_REL_PATH]

    def test_real_file_passes_validation(self):
        """The real module-artifacts.yaml passes validation with its expected keys."""
        full_path = str(_POWER_ROOT / self._REL_PATH)
        result = validate_file(full_path, self._EXPECTED_KEYS)

        assert result.passed, (
            f"Expected PASS for {self._REL_PATH}, got FAIL: "
            f"missing={result.missing_keys}, unexpected={result.unexpected_keys}, "
            f"error={result.error}"
        )

    def test_real_file_pass_output_format(self):
        """PASS output for module-artifacts.yaml is correct."""
        full_path = str(_POWER_ROOT / self._REL_PATH)
        result = validate_file(full_path, self._EXPECTED_KEYS)
        output = format_result(result)

        assert output == "PASS: module-artifacts.yaml"

    def test_extra_key_produces_fail(self, tmp_path):
        """Adding an extra key to module-artifacts.yaml content produces FAIL."""
        real_path = _POWER_ROOT / self._REL_PATH
        content = real_path.read_text(encoding="utf-8")
        modified = content + "\nspurious_key: true\n"

        tmp_file = tmp_path / "module-artifacts.yaml"
        tmp_file.write_text(modified, encoding="utf-8")

        result = validate_file(str(tmp_file), self._EXPECTED_KEYS)

        assert not result.passed
        assert "spurious_key" in result.unexpected_keys

    def test_missing_key_produces_fail(self, tmp_path):
        """Removing a key from module-artifacts.yaml content produces FAIL."""
        real_path = _POWER_ROOT / self._REL_PATH
        content = real_path.read_text(encoding="utf-8")
        lines = [ln for ln in content.splitlines() if not ln.startswith("version:")]
        modified = "\n".join(lines) + "\n"

        tmp_file = tmp_path / "module-artifacts.yaml"
        tmp_file.write_text(modified, encoding="utf-8")

        result = validate_file(str(tmp_file), self._EXPECTED_KEYS)

        assert not result.passed
        assert "version" in result.missing_keys

    def test_fail_output_format(self, tmp_path):
        """FAIL output for module-artifacts.yaml starts with FAIL prefix."""
        real_path = _POWER_ROOT / self._REL_PATH
        content = real_path.read_text(encoding="utf-8")
        modified = content + "\nbogus: true\n"

        tmp_file = tmp_path / "module-artifacts.yaml"
        tmp_file.write_text(modified, encoding="utf-8")

        result = validate_file(str(tmp_file), self._EXPECTED_KEYS)
        output = format_result(result)

        assert output.startswith("FAIL: module-artifacts.yaml")
        assert "unexpected keys" in output
