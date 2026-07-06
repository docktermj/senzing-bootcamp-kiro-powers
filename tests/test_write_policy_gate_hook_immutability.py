"""Hook-immutability test for the auto-approve-write-policy-gate feature.

The auto-approve-write-policy-gate feature is implemented entirely as steering
content and a preference key — it introduces no runtime scripts and, critically,
does NOT modify the ``write-policy-gate.kiro.hook`` file. Requirement 3.2
requires the hook file to be byte-for-byte identical before and after the
feature is applied.

Following the observation-first pattern in
``test_steering_index_token_count_sync_preservation.py``, this test snapshots
the SHA-256 of the live hook file and pins it as ``_BASELINE_HASH``. Any edit to
the hook (even a single byte) changes the digest and fails this test, guarding
the byte-for-byte-stability invariant.

Per the ``structure.md`` steering rule ("Hook tests validating real hook files
go in repo-root ``tests/``, not ``senzing-bootcamp/tests/``"), this test lives in
the repo-root ``tests/`` directory.

**Validates: Requirements 3.2**
"""

from __future__ import annotations

import hashlib
from pathlib import Path

# ---------------------------------------------------------------------------
# Locate the live hook file relative to the project root.
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_HOOK_PATH = _PROJECT_ROOT / "senzing-bootcamp" / "hooks" / "write-policy-gate.kiro.hook"

# SHA-256 of the live ``write-policy-gate.kiro.hook`` bytes, snapshotted while
# authoring the auto-approve-write-policy-gate feature. The feature must leave
# the hook file byte-for-byte unchanged, so this digest must never change as a
# result of the feature.
_BASELINE_HASH = "6828e48ef75b57f7287bf7cc6029ae8386e77e1feea59e64a59d8f3aca156e12"


def _sha256_bytes(data: bytes) -> str:
    """Return the hex SHA-256 digest of *data*."""
    return hashlib.sha256(data).hexdigest()


class TestWritePolicyGateHookImmutability:
    """The ``write-policy-gate.kiro.hook`` file is byte-for-byte unchanged.

    **Validates: Requirements 3.2**
    """

    def test_hook_file_exists(self) -> None:
        """The live hook file is present at its expected path.

        **Validates: Requirements 3.2**
        """
        assert _HOOK_PATH.is_file(), f"hook file not found: {_HOOK_PATH}"

    def test_hook_sha256_matches_pinned_baseline(self) -> None:
        """The hook's SHA-256 matches the pinned baseline (byte-for-byte stable).

        A mismatch means the ``write-policy-gate.kiro.hook`` file was modified,
        violating Requirement 3.2 (the auto-approve feature must not touch it).

        **Validates: Requirements 3.2**
        """
        actual = _sha256_bytes(_HOOK_PATH.read_bytes())
        assert actual == _BASELINE_HASH, (
            "write-policy-gate.kiro.hook has changed: its SHA-256 no longer "
            f"matches the pinned baseline.\n  expected: {_BASELINE_HASH}\n"
            f"  actual:   {actual}\n"
            "The auto-approve-write-policy-gate feature must leave this hook "
            "file byte-for-byte unchanged (Requirement 3.2). If the change was "
            "intentional and approved, re-pin _BASELINE_HASH."
        )
