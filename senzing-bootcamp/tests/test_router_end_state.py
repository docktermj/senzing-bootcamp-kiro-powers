"""End-state verification tests for the thin Router_Root convention.

Feature: module-router-standardization

These are example/integration tests (not property-based) that assert the
post-remediation end-state directly on the REAL repository files:
``senzing-bootcamp/steering/steering-index.yaml`` and the steering ``.md``
files on disk. They codify the design's "End-state verification (asserted on
the real repo files)" Testing-Strategy section.

Covered concerns:

- Compliant roots (Requirements 2.4, 1.2): every in-scope root's measured token
  count is at or below the Router_Ceiling (1000).
- Distinct roots (Requirements 2.5, 4.3): every in-scope module's ``root``
  differs from all of its phase files.
- Phase manifest presence (Requirements 3.5, 7.1): each in-scope router file on
  disk contains a Phase_Manifest that references every phase file recorded for
  that module in the index.
- Index completeness (Requirements 4.2, 7.5): every steering ``.md`` file on
  disk has a ``file_metadata`` entry.
- Clean lint (Requirement 6.5): ``check_router_convention`` over the real parsed
  index returns no violations and a full ``run_all_checks`` exits 0 while
  emitting no router-related violation.
"""

import sys
from pathlib import Path

import pytest

# Make scripts importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from lint_steering import (  # noqa: E402
    check_router_convention,
    get_router_ceiling,
    parse_module_phase_files,
    parse_steering_index,
    run_all_checks,
)

# ---------------------------------------------------------------------------
# Real repository paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STEERING_DIR = REPO_ROOT / "senzing-bootcamp" / "steering"
HOOKS_DIR = REPO_ROOT / "senzing-bootcamp" / "hooks"
INDEX_PATH = STEERING_DIR / "steering-index.yaml"


def _router_info() -> dict:
    """Parse the real index into per-module router information."""
    return parse_module_phase_files(INDEX_PATH)


def _in_scope_modules() -> dict:
    """Return only the in-scope modules (a phase file distinct from the root)."""
    return {num: info for num, info in _router_info().items() if info.in_scope}


# Substrings that identify a router-convention violation message so the full
# lint run can be filtered for router-specific findings.
_ROUTER_MARKERS = ("Router_Root", "Router_Ceiling", "root-doubles-as-phase")


def _is_router_violation(message: str) -> bool:
    """True when a lint message is a router-convention violation."""
    return any(marker in message for marker in _ROUTER_MARKERS)


class TestRealIndexFixturesExist:
    """Sanity checks that the real corpus is present and has in-scope modules."""

    def test_index_and_steering_dir_exist(self):
        """The real steering index and directory are present."""
        assert INDEX_PATH.is_file(), f"missing steering index: {INDEX_PATH}"
        assert STEERING_DIR.is_dir(), f"missing steering dir: {STEERING_DIR}"

    def test_has_in_scope_modules(self):
        """The remediated corpus has the expected in-scope modules."""
        in_scope = _in_scope_modules()
        # Modules 1,3,5,6,7,8,9,10,11 are in scope; 2 and 4 are excluded
        # (single phase whose file equals the root).
        assert set(in_scope) == {1, 3, 5, 6, 7, 8, 9, 10, 11}, (
            f"unexpected in-scope module set: {sorted(in_scope)}"
        )


class TestCompliantRoots:
    """Every in-scope root's measured token count <= ceiling (Req 2.4, 1.2)."""

    def test_every_in_scope_root_at_or_below_ceiling(self):
        """All in-scope router roots are at or below the Router_Ceiling."""
        ceiling = get_router_ceiling(INDEX_PATH)
        assert ceiling == 1000, f"expected ceiling 1000, got {ceiling}"

        file_metadata = parse_steering_index(INDEX_PATH).get("file_metadata", {})
        offenders = []
        for num, info in sorted(_in_scope_modules().items()):
            token_count = file_metadata.get(info.root, {}).get("token_count")
            assert isinstance(token_count, int), (
                f"Module {num} root '{info.root}' has no measured token_count"
            )
            if token_count > ceiling:
                offenders.append((num, info.root, token_count))
        assert not offenders, (
            f"roots exceeding the {ceiling}-token ceiling: {offenders}"
        )


class TestDistinctRoots:
    """Every in-scope root differs from all its phase files (Req 2.5, 4.3)."""

    def test_root_distinct_from_all_phase_files(self):
        """No in-scope module reuses its root filename as a phase file."""
        offenders = []
        for num, info in sorted(_in_scope_modules().items()):
            if info.root in info.phase_files:
                offenders.append((num, info.root))
            assert not info.doubles_as_phase, (
                f"Module {num} root '{info.root}' doubles as a phase file"
            )
        assert not offenders, f"root-doubles-as-phase modules: {offenders}"


class TestPhaseManifestPresence:
    """Each in-scope router references every phase file (Req 3.5, 7.1)."""

    def test_router_lists_every_phase_file(self):
        """Each router file on disk names every phase file in its index entry."""
        for num, info in sorted(_in_scope_modules().items()):
            router_path = STEERING_DIR / info.root
            assert router_path.is_file(), (
                f"Module {num} router file missing on disk: {router_path}"
            )
            content = router_path.read_text(encoding="utf-8")
            missing = [pf for pf in info.phase_files if pf not in content]
            assert not missing, (
                f"Module {num} router '{info.root}' is missing Phase_Manifest "
                f"references to: {missing}"
            )


class TestIndexCompleteness:
    """Every steering .md on disk has a file_metadata entry (Req 4.2, 7.5)."""

    def test_every_steering_md_has_metadata(self):
        """Each ``.md`` under steering/ has a ``file_metadata`` entry."""
        file_metadata = parse_steering_index(INDEX_PATH).get("file_metadata", {})
        on_disk = {p.name for p in STEERING_DIR.glob("*.md")}
        missing = sorted(name for name in on_disk if name not in file_metadata)
        assert not missing, (
            f"steering .md files lacking a file_metadata entry: {missing}"
        )


class TestCleanLint:
    """No router violation and a clean exit on the real corpus (Req 6.5)."""

    def test_check_router_convention_returns_no_violations(self):
        """The router rule finds no violation over the real parsed index."""
        file_metadata = parse_steering_index(INDEX_PATH).get("file_metadata", {})
        ceiling = get_router_ceiling(INDEX_PATH)
        violations = check_router_convention(_router_info(), file_metadata, ceiling)
        assert violations == [], (
            f"router violations on the real corpus: "
            f"{[v.message for v in violations]}"
        )

    def test_full_lint_emits_no_router_violation_and_exits_zero(self):
        """A full lint run emits no router violation and exits 0."""
        violations, exit_code = run_all_checks(
            STEERING_DIR, HOOKS_DIR, INDEX_PATH
        )
        router_violations = [
            v for v in violations if _is_router_violation(v.message)
        ]
        assert not router_violations, (
            f"router-related violations: "
            f"{[v.format() for v in router_violations]}"
        )
        assert exit_code == 0, (
            f"linter exited {exit_code}; errors: "
            f"{[v.format() for v in violations if v.level == 'ERROR']}"
        )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
