"""CI-step presence test for the composer --verify gate.

Validates that the real ``.github/workflows/validate-power.yml`` wires the
composer drift gate (``compose_hook_prompts.py --verify``) as a required step
*before* the existing hook-registry sync gate
(``sync_hook_registry.py --verify``), matching the composer-before-sync
ordering from the design.

Requirements validated: 7.4

This is an example test (not property-based). Assertions search for the script
invocation substrings rather than brittle exact-line matches, and confirm the
composer-verify occurrence precedes the sync-verify occurrence by position in
the workflow text.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path to the CI workflow under test (resolved relative to this file:
# repo root -> .github/workflows/validate-power.yml).
# ---------------------------------------------------------------------------

_WORKFLOW_PATH: Path = (
    Path(__file__).resolve().parent.parent
    / ".github"
    / "workflows"
    / "validate-power.yml"
)

# Substrings identifying the two verify invocations. Searching for the script
# invocation substrings keeps the assertions robust against step renames,
# reformatting, or indentation changes.
_COMPOSE_VERIFY: str = "compose_hook_prompts.py --verify"
_SYNC_VERIFY: str = "sync_hook_registry.py --verify"


def _read_workflow() -> str:
    """Read the CI workflow file as text.

    Returns:
        The full text of validate-power.yml.
    """
    assert _WORKFLOW_PATH.exists(), f"CI workflow not found: {_WORKFLOW_PATH}"
    return _WORKFLOW_PATH.read_text(encoding="utf-8")


# Module-level read: the workflow is static during a test run.
_WORKFLOW: str = _read_workflow()


# ---------------------------------------------------------------------------
# TestCiComposeVerify
# ---------------------------------------------------------------------------


class TestCiComposeVerify:
    """Validate the composer --verify CI step presence and ordering.

    **Validates: Requirements 7.4**
    """

    @pytest.fixture(autouse=True)
    def _load_content(self) -> None:
        """Expose workflow content to every test in this class."""
        self.content: str = _WORKFLOW

    def test_compose_verify_step_present(self) -> None:
        """Workflow must invoke compose_hook_prompts.py --verify (Req 7.4)."""
        assert _COMPOSE_VERIFY in self.content, (
            "validate-power.yml must run "
            f"'{_COMPOSE_VERIFY}' as a required CI step"
        )

    def test_sync_verify_step_present(self) -> None:
        """Workflow must still invoke sync_hook_registry.py --verify (Req 7.4)."""
        assert _SYNC_VERIFY in self.content, (
            "validate-power.yml must run "
            f"'{_SYNC_VERIFY}' as a required CI step"
        )

    def test_compose_verify_ordered_before_sync_verify(self) -> None:
        """Composer verify must appear before sync verify (Req 7.4).

        The byte/line index of the composer-verify invocation must be strictly
        less than that of the sync-verify invocation so the composer-before-sync
        ordering holds.
        """
        compose_idx = self.content.find(_COMPOSE_VERIFY)
        sync_idx = self.content.find(_SYNC_VERIFY)
        assert compose_idx >= 0, (
            f"'{_COMPOSE_VERIFY}' must appear in validate-power.yml"
        )
        assert sync_idx >= 0, (
            f"'{_SYNC_VERIFY}' must appear in validate-power.yml"
        )
        assert compose_idx < sync_idx, (
            "validate-power.yml must run the composer verify "
            f"('{_COMPOSE_VERIFY}') before the registry sync verify "
            f"('{_SYNC_VERIFY}'): composer index {compose_idx} must be < "
            f"sync index {sync_idx}"
        )
