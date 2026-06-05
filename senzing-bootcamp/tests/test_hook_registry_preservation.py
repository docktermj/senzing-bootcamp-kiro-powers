"""BUG 3 preservation baselines for the hook registry (Task 6, Phase B).

Property 6: Preservation — Registry Contents and sync_hook_registry Unchanged.

These tests are the preservation companion to the BUG 3 bug-condition exploration
(Property 5). They observe the *currently shipped* hook-registry steering files and
the ``sync_hook_registry.py --verify`` result on the UNFIXED tree and lock them down
so the BUG 3 fix can prove it touches ONLY ``lint_steering.py``'s hook-consistency
source selection (Rule 6): the three registry ``.md`` files MUST stay byte-identical,
``sync_hook_registry.py --verify`` MUST still pass (exit 0), and every linter rule
other than hook-consistency source selection MUST behave identically.

Observation-first methodology: every SHA-256 digest below was read from the live
shipped files on the UNFIXED tree before being asserted here. The digests and the
``--verify`` result are also persisted to
``.kiro/specs/bootcamp-consistency-fixes/bug3_preservation_baselines.txt`` so Task 9.5
can re-verify byte-stability after the fix.

Backward-compat note: the synthetic Property-7 test in
``test_lint_steering_properties.py`` builds its registry fixture on
``hook-registry-critical.md`` ONLY. The Task 9 union-source logic must therefore stay
backward-compatible — a hook documented in ANY recognized source counts as documented.

EXPECTED OUTCOME on the UNFIXED tree: every test in this file PASSES (baseline
confirmed). After the BUG 3 fix (linter-source-only), these same tests MUST still pass.

**Validates: Requirements 3.8, 3.9**
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SYNC_SCRIPT = _SCRIPTS_DIR / "sync_hook_registry.py"

# SHA-256 byte-level baselines observed on the UNFIXED tree (Task 6).
# Source of truth mirrored in
# .kiro/specs/bootcamp-consistency-fixes/bug3_preservation_baselines.txt
_REGISTRY_BASELINES: dict[str, str] = {
    "hook-registry.md":
        "388cffe18e522b64b04dc716378a1fae7b463f5cd300bc63ef4d1fca33a138bd",
    "hook-registry-critical.md":
        "71b8f11b051831998b8a248f81bf29d09df5e36a6b93b121de45c2c40502d08f",
    "hook-registry-modules.md":
        "f17c10437454954fb594e0a0464515991b5dcf304405b99626f2fb17712b9a7f",
}

# sync_hook_registry --verify success marker observed on the UNFIXED tree.
_VERIFY_OK_MARKER = "All registry files are up to date."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sha256_bytes(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's raw bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_verify() -> subprocess.CompletedProcess[str]:
    """Run ``sync_hook_registry.py --verify`` from the repo root."""
    return subprocess.run(
        [sys.executable, str(_SYNC_SCRIPT), "--verify"],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )


# ---------------------------------------------------------------------------
# Preservation — registry files byte-identical (Requirement 3.8)
# ---------------------------------------------------------------------------


class TestRegistryFilesByteIdentical:
    """The three hook-registry files match their observed SHA-256 baselines.

    These are the digests Task 9.5 re-checks to prove the BUG 3 fix corrects the
    LINTER's source, not the registry contents."""

    @pytest.mark.parametrize("filename", sorted(_REGISTRY_BASELINES))
    def test_registry_file_matches_sha256_baseline(self, filename: str) -> None:
        """**Validates: Requirements 3.8**

        Each registry file is byte-identical to the Task 6 baseline."""
        expected = _REGISTRY_BASELINES[filename]
        actual = _sha256_bytes(_STEERING_DIR / filename)
        assert actual == expected, (
            f"{filename} content changed — the BUG 3 fix must NOT edit the "
            "registry (it corrects the linter's source).\n"
            f"Expected: {expected}\n"
            f"Actual:   {actual}"
        )

    @given(filename=st.sampled_from(sorted(_REGISTRY_BASELINES)))
    @settings(max_examples=20)
    def test_all_registry_digests_unchanged(self, filename: str) -> None:
        """**Validates: Requirements 3.8**

        Property: for all hook-registry files, the on-disk SHA-256 digest equals
        the observed baseline. This is the preservation companion to Property 5 —
        it pins the registry contents so a fix that mutates any registry file is
        caught regardless of which file the linter-source change targets."""
        expected = _REGISTRY_BASELINES[filename]
        actual = _sha256_bytes(_STEERING_DIR / filename)
        assert actual == expected, (
            f"Registry digest drift for {filename}: "
            f"expected {expected}, got {actual}"
        )


# ---------------------------------------------------------------------------
# Preservation — sync_hook_registry --verify still passes (Requirement 3.9)
# ---------------------------------------------------------------------------


class TestSyncHookRegistryVerifyPasses:
    """sync_hook_registry.py --verify passes with its current behavior."""

    def test_verify_exits_zero(self) -> None:
        """**Validates: Requirements 3.9**

        ``sync_hook_registry.py --verify`` exits 0 on the registry baseline."""
        result = _run_verify()
        assert result.returncode == 0, (
            "sync_hook_registry.py --verify must continue to pass (exit 0).\n"
            f"Exit code: {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_verify_reports_up_to_date(self) -> None:
        """**Validates: Requirements 3.9**

        ``--verify`` reports the registry files are in sync with the source."""
        result = _run_verify()
        assert _VERIFY_OK_MARKER in result.stdout, (
            "sync_hook_registry.py --verify lost its up-to-date confirmation.\n"
            f"Expected to find: {_VERIFY_OK_MARKER!r}\n"
            f"stdout: {result.stdout}"
        )
