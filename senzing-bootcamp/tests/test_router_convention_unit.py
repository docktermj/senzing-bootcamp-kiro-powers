"""Example and edge-case unit tests for the thin Router_Root convention.

Feature: module-router-standardization

Covers the two example/edge concerns called out in the design's Testing Strategy
("Example and edge-case unit tests"):

- Ceiling boundary (Requirement 1.6): the default Router_Ceiling resolves to
  1000 and classifies the three known thin routers (689/571/568) as routers and
  the three known content roots (1583/1448/1359) as requiring remediation.
- Environment guard (Requirement 6.6): patching ``sys.version_info`` to
  ``(3, 10)`` makes ``require_runtime`` report an environment error and exit
  non-zero rather than reporting success.
"""

import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

# Make scripts importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from lint_steering import (
    MIN_PYTHON,
    REQUIRED_STDLIB_MODULES,
    ModuleRouterInfo,
    check_router_convention,
    get_router_ceiling,
    require_runtime,
)

# Known token counts from the steering index (Requirements 1.6, 2.6).
# Roots at or below the ceiling are thin routers; roots above it require
# remediation.
KNOWN_ROUTERS = {
    "module-05-data-quality-mapping.md": 689,
    "module-09-security.md": 571,
    "module-10-monitoring.md": 568,
}
KNOWN_CONTENT_ROOTS = {
    "module-06-data-processing.md": 1583,
    "module-03-system-verification.md": 1448,
    "module-08-performance.md": 1359,
}


def _in_scope_info(module_num: int, root: str, token_count: int) -> ModuleRouterInfo:
    """Build an in-scope ModuleRouterInfo with a phase file distinct from root.

    The single phase file differs from the root so ``in_scope`` is True and the
    root is not flagged as doubling-as-phase, isolating the ceiling behavior.

    Args:
        module_num: Module number for the entry.
        root: Router_Root filename.
        token_count: Measured token count attached to the root.

    Returns:
        An in-scope ``ModuleRouterInfo`` whose only concern is the ceiling.
    """
    phase_file = f"module-{module_num:02d}-phase1.md"
    return ModuleRouterInfo(
        module_num=module_num,
        root=root,
        phase_files=[phase_file],
        root_token_count=token_count,
    )


class TestRouterCeilingDefault:
    """The default Router_Ceiling resolves to 1000 (Requirement 1.6)."""

    def test_missing_key_defaults_to_1000(self):
        """An index without ``router_ceiling`` yields the 1000-token default."""
        with tempfile.TemporaryDirectory() as tmp:
            index_path = Path(tmp) / "steering-index.yaml"
            index_path.write_text(
                "budget:\n"
                "  total_tokens: 12345\n"
                "  split_threshold_tokens: 5000\n",
                encoding="utf-8",
            )
            assert get_router_ceiling(index_path) == 1000

    def test_missing_file_defaults_to_1000(self):
        """A nonexistent index path still yields the 1000-token default."""
        missing = Path(tempfile.gettempdir()) / "does-not-exist-steering-index.yaml"
        assert get_router_ceiling(missing) == 1000

    def test_explicit_value_is_read(self):
        """An explicit ``router_ceiling`` is read from the budget block."""
        with tempfile.TemporaryDirectory() as tmp:
            index_path = Path(tmp) / "steering-index.yaml"
            index_path.write_text(
                "budget:\n"
                "  router_ceiling: 1000\n",
                encoding="utf-8",
            )
            assert get_router_ceiling(index_path) == 1000


class TestCeilingClassification:
    """Default ceiling (1000) classification of the known roots (Req 1.6)."""

    def test_known_thin_routers_have_no_ceiling_violation(self):
        """689/571/568 are at/below 1000 and classify as routers."""
        ceiling = 1000
        for i, (root, count) in enumerate(KNOWN_ROUTERS.items(), start=1):
            info = _in_scope_info(i, root, count)
            violations = check_router_convention({i: info}, {}, ceiling)
            assert violations == [], (
                f"{root} ({count} tokens) should classify as a router, "
                f"got: {[v.message for v in violations]}"
            )

    def test_known_content_roots_require_remediation(self):
        """1583/1448/1359 exceed 1000 and produce a ceiling violation."""
        ceiling = 1000
        for i, (root, count) in enumerate(KNOWN_CONTENT_ROOTS.items(), start=1):
            info = _in_scope_info(i, root, count)
            violations = check_router_convention({i: info}, {}, ceiling)
            assert len(violations) == 1, (
                f"{root} ({count} tokens) should require remediation"
            )
            v = violations[0]
            assert v.level == "ERROR"
            # The message names the root, its token count, and the ceiling.
            assert root in v.message
            assert str(count) in v.message
            assert str(ceiling) in v.message

    def test_all_known_routers_together_produce_no_violations(self):
        """The three thin routers in one index yield zero violations."""
        index_data = {
            i: _in_scope_info(i, root, count)
            for i, (root, count) in enumerate(KNOWN_ROUTERS.items(), start=1)
        }
        assert check_router_convention(index_data, {}, 1000) == []

    def test_all_known_content_roots_together_each_flagged(self):
        """The three content roots in one index each yield a violation."""
        index_data = {
            i: _in_scope_info(i, root, count)
            for i, (root, count) in enumerate(KNOWN_CONTENT_ROOTS.items(), start=1)
        }
        violations = check_router_convention(index_data, {}, 1000)
        assert len(violations) == len(KNOWN_CONTENT_ROOTS)


class TestEnvironmentGuard:
    """The Python 3.11+ environment guard (Requirement 6.6)."""

    def test_python_3_10_exits_non_zero(self):
        """Patching ``sys.version_info`` to (3, 10) triggers a non-zero exit."""
        fake_version = (3, 10, 0, "final", 0)
        with mock.patch.object(sys, "version_info", fake_version):
            with pytest.raises(SystemExit) as exc_info:
                require_runtime(
                    min_python=MIN_PYTHON,
                    required_modules=REQUIRED_STDLIB_MODULES,
                )
        code = exc_info.value.code
        assert code is not None and code != 0

    def test_python_3_10_reports_environment_error_to_stderr(self, capsys):
        """The guard reports an environment error and does not report success."""
        fake_version = (3, 10, 0, "final", 0)
        with mock.patch.object(sys, "version_info", fake_version):
            with pytest.raises(SystemExit):
                require_runtime(
                    min_python=MIN_PYTHON,
                    required_modules=REQUIRED_STDLIB_MODULES,
                )
        captured = capsys.readouterr()
        assert "ERROR" in captured.err
        assert "Python" in captured.err
        # It must not falsely report success on an unsupported runtime.
        assert "success" not in (captured.out + captured.err).lower()

    def test_supported_runtime_passes(self):
        """The current (supported) interpreter passes the guard cleanly."""
        # No SystemExit expected on the real 3.11+ runtime running the suite.
        require_runtime(
            min_python=MIN_PYTHON,
            required_modules=REQUIRED_STDLIB_MODULES,
        )
