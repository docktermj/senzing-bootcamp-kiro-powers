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

Parallel-safety (test-suite-parallelization, Tasks 5.2/5.3)
-----------------------------------------------------------
Originally the ``--write`` tests composed directly into the *shared* repo hooks
dir (``senzing-bootcamp/hooks``). Under ``pytest-xdist`` that is unsafe: many
reader tests in both roots load those hook files, and a concurrent worker could
observe a transient/partial file mid-write. The ``--write`` tests are therefore
**isolated to a per-test ``tmp_path`` hooks dir** (worker-unique under xdist):
each copies the real gate-hook files into ``tmp_path`` and composes there, so
the shared repo hooks dir is never written and workers cannot collide
(Requirements 5.1, 5.2, 6.2). Because ``compose --write`` is a proven
byte-identical no-op refactor (task 3.3 / Property 6), composing into ``tmp_path``
yields the same result as composing into the real dir while touching no shared
state.

The ``sync_hook_registry.py --verify`` step (and the canonical-repo baseline
test) cannot be isolated the same way: ``sync_hook_registry.main()`` writes its
mirror docs + lockfile to repo-root-relative default paths and reads the whole
shared repo tree, so it operates on shared repo state by construction. Those
residual portions are pinned to a serial scheduling group via the class-level
``serial`` + ``xdist_group("serial")`` markers below (Requirement 6.3).

_Requirements: 8.5_
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

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


def _make_isolated_hooks_dir(tmp_path: Path) -> Path:
    """Build a per-test hooks dir seeded with the real gate-hook files.

    ``compose_hook`` reads each gate hook's static fields (``name``, ``version``,
    ``when`` …) from the on-disk file and only recomposes ``then.prompt``, so the
    real files must be present in the target directory. Copying them into a
    ``tmp_path`` subdirectory (worker-unique under xdist) lets ``compose --write``
    run with byte-identical results while never touching the shared repo hooks
    dir.

    Args:
        tmp_path: The per-test temporary directory provided by pytest.

    Returns:
        Path to the isolated hooks directory containing the gate-hook copies.
    """
    tmp_hooks = tmp_path / "hooks"
    tmp_hooks.mkdir(parents=True, exist_ok=True)
    for hook_id in GATE_HOOK_IDS:
        src = _HOOKS_DIR / f"{hook_id}.kiro.hook"
        (tmp_hooks / f"{hook_id}.kiro.hook").write_bytes(src.read_bytes())
    return tmp_hooks


def _snapshot_hooks(hooks_dir: Path) -> dict[str, bytes]:
    """Return the current on-disk bytes of every gate-hook file in *hooks_dir*."""
    return {
        hook_id: (hooks_dir / f"{hook_id}.kiro.hook").read_bytes()
        for hook_id in GATE_HOOK_IDS
    }


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


# The class as a whole touches shared repo state: the ``sync --verify`` step and
# the canonical-repo baseline test invoke ``sync_hook_registry.py`` as a
# subprocess with ``cwd`` pinned to the repo root, and that script writes its
# mirror docs + lockfile to repo-root-relative *default* output paths while
# reading the whole shared hooks dir + registry. There is no CLI knob to
# redirect those default outputs into a tmp dir, so the sync-verify portion
# cannot be isolated per-worker the way the composer ``--write`` step is. Pin the
# whole class to a single serial scheduling group so it never runs concurrently
# with a colliding peer under ``--dist loadgroup`` (Requirement 6.3). The
# ``--write`` tests are *additionally* isolated to ``tmp_path`` (Task 5.2), so
# even within the serial group the shared hooks dir is never mutated.
@pytest.mark.serial
@pytest.mark.xdist_group("serial")
class TestComposeSyncIntegration:
    """compose ``--write`` then sync ``--verify`` exits 0 (Req 8.5).

    Validates the composer-before-sync ordering: writing the composed gate-hook
    JSON keeps the registry mirrors in sync, so the downstream sync verify gate
    passes.
    """

    def test_compose_write_then_sync_verify_exits_zero(self, tmp_path: Path) -> None:
        tmp_hooks = _make_isolated_hooks_dir(tmp_path)
        # Isolation guard (Req 5.2): snapshot the *shared* repo hooks dir bytes
        # before the write. The compose --write below targets the per-test
        # tmp_path hooks dir, so the shared dir must be byte-identical
        # afterwards — proving the write landed only under the temp dir and no
        # concurrent xdist worker can observe a mutated shared file.
        shared_before = _snapshot_hooks(_HOOKS_DIR)
        # Step 1: composer writes the self-contained gate-hook JSON into an
        # isolated per-test hooks dir (never the shared repo hooks dir), so
        # concurrent xdist workers cannot observe a transient/partial file.
        compose_code = compose_hook_prompts.main(
            [
                "--write",
                "--hooks-dir",
                str(tmp_hooks),
                "--fragments",
                str(_FRAGMENTS_PATH),
            ]
        )
        assert compose_code == 0, "compose --write must succeed (exit 0)"

        # Isolation guard (Req 5.2): the write landed under tmp_path — each
        # gate-hook output file exists in the isolated dir — and the shared repo
        # hooks dir is byte-for-byte unchanged (the write touched only tmp_path).
        for hook_id in GATE_HOOK_IDS:
            assert (tmp_hooks / f"{hook_id}.kiro.hook").exists(), (
                f"compose --write must produce {hook_id} under the isolated "
                f"tmp_path hooks dir: {tmp_hooks}"
            )
        shared_after = _snapshot_hooks(_HOOKS_DIR)
        assert shared_after == shared_before, (
            "compose --write must not touch the shared repo hooks dir "
            f"({_HOOKS_DIR}); writes must land only under tmp_path"
        )

        # Step 2: the downstream sync verify gate passes against the canonical
        # repo — composer-before-sync ordering holds. Because compose --write is
        # a byte-identical no-op, composing into tmp_path leaves the canonical
        # hooks unchanged, so this still exercises the ordering invariant.
        result = _run_sync_verify()
        assert result.returncode == 0, (
            "sync --verify must exit 0 after compose --write.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_compose_write_leaves_gate_hooks_byte_identical(self, tmp_path: Path) -> None:
        # The compose --write is a byte-identical no-op refactor: running it
        # against an isolated copy of the gate hooks must not mutate any
        # gate-hook bytes, which is precisely why the subsequent sync --verify
        # stays green. Operating on a tmp_path copy keeps the shared repo hooks
        # dir untouched under concurrent workers.
        tmp_hooks = _make_isolated_hooks_dir(tmp_path)
        before = _snapshot_hooks(tmp_hooks)
        # Isolation guard (Req 5.2): snapshot the *shared* repo hooks dir too, so
        # we can prove the write below never escapes tmp_path into shared state.
        shared_before = _snapshot_hooks(_HOOKS_DIR)
        compose_code = compose_hook_prompts.main(
            [
                "--write",
                "--hooks-dir",
                str(tmp_hooks),
                "--fragments",
                str(_FRAGMENTS_PATH),
            ]
        )
        assert compose_code == 0
        after = _snapshot_hooks(tmp_hooks)
        assert after == before, "compose --write must not change gate-hook bytes"
        # Isolation guard (Req 5.2): every written file lives under tmp_path and
        # the shared repo hooks dir is byte-for-byte unchanged.
        for hook_id in GATE_HOOK_IDS:
            assert (tmp_hooks / f"{hook_id}.kiro.hook").exists(), (
                f"compose --write must produce {hook_id} under the isolated "
                f"tmp_path hooks dir: {tmp_hooks}"
            )
        shared_after = _snapshot_hooks(_HOOKS_DIR)
        assert shared_after == shared_before, (
            "compose --write must not touch the shared repo hooks dir "
            f"({_HOOKS_DIR}); writes must land only under tmp_path"
        )

    def test_sync_verify_passes_on_canonical_repo(self) -> None:
        # Sanity baseline: sync --verify is green on the canonical repo before
        # any composition, so a post-compose pass demonstrably reflects the
        # ordering invariant rather than a pre-existing failure being masked.
        # This is read-only against the repo tree but still reads shared state,
        # hence the class-level serial pin documented above.
        result = _run_sync_verify()
        assert result.returncode == 0, (
            "sync --verify must exit 0 on the canonical repo.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
