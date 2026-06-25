"""Integration test: composer-before-sync ordering (Theme B).

Feature: hook-architecture-improvements (Theme B — hook-prompt deduplication).

This is a *script-behavior / integration* test that drives the two real scripts
against the real hooks directory, so per ``structure.md`` it lives in
``senzing-bootcamp/tests/`` (script-behavior) rather than the repo-root
``tests/``.

It proves the design's "Composer-before-sync ordering" invariant: the composer
*writes* the self-contained gate-hook JSON and ``sync_hook_registry.py`` *reads*
that JSON to regenerate the mirror docs + lockfile, so the pipeline is
``compose --write`` → ``sync --verify``. After the composer writes the gate
hooks, ``sync_hook_registry.py --verify`` must still exit 0 because the mirrors
are consistent with the (byte-identical) composed hook JSON (Req 8.5).

Because the composer's ``--write`` is a proven byte-identical no-op refactor
(task 3.3 / Property 6), running it against the real hooks dir changes no bytes.
The test snapshots the three gate-hook files before composing and restores them
afterward so the working tree is guaranteed unchanged regardless of outcome.

_Requirements: 8.5_
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import compose_hook_prompts  # noqa: E402

# ---------------------------------------------------------------------------
# Real-repo paths
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_HOOKS_DIR = _REPO_ROOT / "senzing-bootcamp" / "hooks"
_FRAGMENTS_PATH = _REPO_ROOT / "senzing-bootcamp" / "scripts" / "hook_prompt_fragments.py"
_COMPOSE_SCRIPT = _REPO_ROOT / "senzing-bootcamp" / "scripts" / "compose_hook_prompts.py"
_SYNC_SCRIPT = _REPO_ROOT / "senzing-bootcamp" / "scripts" / "sync_hook_registry.py"

# The three Module 3 gate hooks the composer owns and writes.
GATE_HOOK_IDS = tuple(compose_hook_prompts.HOOK_TEMPLATES.keys())


def _snapshot_gate_hooks() -> dict[str, bytes]:
    """Return the current on-disk bytes of every gate-hook file."""
    return {
        hook_id: (_HOOKS_DIR / f"{hook_id}.kiro.hook").read_bytes()
        for hook_id in GATE_HOOK_IDS
    }


def _restore_gate_hooks(snapshot: dict[str, bytes]) -> None:
    """Restore gate-hook files from a *snapshot* (defensive no-op safety net)."""
    for hook_id, original in snapshot.items():
        path = _HOOKS_DIR / f"{hook_id}.kiro.hook"
        if path.read_bytes() != original:
            path.write_bytes(original)


def _run_sync_verify() -> subprocess.CompletedProcess[str]:
    """Run ``sync_hook_registry.py --verify`` from the repo root.

    ``sync_hook_registry.main()`` takes no argv and calls ``sys.exit()`` and its
    default output paths are repo-root relative, so it is invoked as a
    subprocess with ``cwd`` pinned to the repository root (matching the existing
    sync integration test convention).
    """
    return subprocess.run(
        [sys.executable, str(_SYNC_SCRIPT), "--verify"],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )


class TestComposeSyncIntegration:
    """compose ``--write`` then sync ``--verify`` exits 0 (Req 8.5).

    Validates the composer-before-sync ordering: writing the composed gate-hook
    JSON keeps the registry mirrors in sync, so the downstream sync verify gate
    passes.
    """

    def test_compose_write_then_sync_verify_exits_zero(self) -> None:
        snapshot = _snapshot_gate_hooks()
        try:
            # Step 1: composer writes the self-contained gate-hook JSON.
            compose_code = compose_hook_prompts.main(
                [
                    "--write",
                    "--hooks-dir",
                    str(_HOOKS_DIR),
                    "--fragments",
                    str(_FRAGMENTS_PATH),
                ]
            )
            assert compose_code == 0, "compose --write must succeed (exit 0)"

            # Step 2: the downstream sync verify gate passes against the freshly
            # composed hook JSON — composer-before-sync ordering holds.
            result = _run_sync_verify()
            assert result.returncode == 0, (
                "sync --verify must exit 0 after compose --write.\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )
        finally:
            _restore_gate_hooks(snapshot)

    def test_compose_write_leaves_gate_hooks_byte_identical(self) -> None:
        # The compose --write is a byte-identical no-op refactor: running it
        # against the real hooks dir must not mutate any gate-hook bytes, which
        # is precisely why the subsequent sync --verify stays green.
        before = _snapshot_gate_hooks()
        try:
            compose_code = compose_hook_prompts.main(
                [
                    "--write",
                    "--hooks-dir",
                    str(_HOOKS_DIR),
                    "--fragments",
                    str(_FRAGMENTS_PATH),
                ]
            )
            assert compose_code == 0
            after = _snapshot_gate_hooks()
            assert after == before, "compose --write must not change gate-hook bytes"
        finally:
            _restore_gate_hooks(before)

    def test_sync_verify_passes_on_canonical_repo(self) -> None:
        # Sanity baseline: sync --verify is green on the canonical repo before
        # any composition, so a post-compose pass demonstrably reflects the
        # ordering invariant rather than a pre-existing failure being masked.
        result = _run_sync_verify()
        assert result.returncode == 0, (
            "sync --verify must exit 0 on the canonical repo.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
