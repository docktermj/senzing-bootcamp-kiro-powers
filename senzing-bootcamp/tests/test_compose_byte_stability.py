"""Property-based test for the Module 3 gate-hook composer byte-stability.

Feature: kiro-1-0-migration.

This test implements **Property 9: Prompt composer byte-stability round-trip**.
The v1 gate hooks (``gate-module3-visualization``, ``enforce-mandatory-gate``,
``enforce-gate-on-stop``) are composed from the shared fragments in
``hook_prompt_fragments.py`` by ``compose_hook_prompts.py``. Because the composer
is a pure function of (per-hook template, fragment mapping, on-disk static
fields), composition must be deterministic: repeated composition yields
byte-identical output and equals the committed on-disk v1 gate files, so a
``--write`` followed by ``--verify`` reports no drift.

The test composes in memory against a read-only view of the committed files and
also drives the real ``--write``/``--verify`` CLI against a throwaway temp copy,
so it never mutates the committed gate files.
"""

from __future__ import annotations

import contextlib
import io
import shutil
import sys
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import compose_hook_prompts  # noqa: E402
from compose_hook_prompts import (  # noqa: E402
    HOOK_TEMPLATES,
    compose_hook,
    load_fragments,
    serialize_hook,
)

# The committed v1 gate hooks and the authoritative fragment source. Both are
# read-only inputs here; the composer's --write path runs against a temp copy.
_REAL_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
_FRAGMENTS_PATH = Path(_SCRIPTS_DIR) / "hook_prompt_fragments.py"

# The three Module 3 gate hook ids the composer owns (exactly HOOK_TEMPLATES).
_GATE_HOOK_IDS = sorted(HOOK_TEMPLATES)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


def st_gate_hook_order() -> st.SearchStrategy[list[str]]:
    """Draw a processing order (a full permutation) of the gate hook ids.

    Varying the order exercises the property that composition is invariant to
    the order in which hooks are processed; every permutation contains all three
    gate ids, so the CLI ``--write`` path (which composes every id in
    ``HOOK_TEMPLATES``) always has all its inputs present.
    """
    return st.permutations(_GATE_HOOK_IDS)


def st_repeat_count() -> st.SearchStrategy[int]:
    """Draw how many times to repeat composition (>= 2 to exercise determinism)."""
    return st.integers(min_value=2, max_value=4)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_main_silently(argv: list[str]) -> tuple[int, str, str]:
    """Invoke ``compose_hook_prompts.main(argv)`` capturing stdout/stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = compose_hook_prompts.main(argv)
    return code, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# Property 9 — Prompt composer byte-stability round-trip
# ---------------------------------------------------------------------------


class TestComposeByteStabilityRoundTrip:
    """Property 9: composing the Module 3 gate hooks is deterministic —
    ``--write`` produces byte-identical output on repeat and equals the
    committed v1 gate files, so ``--verify`` reports no drift.

    **Validates: Requirements 8.2, 8.3, 8.4**
    """

    # Feature: kiro-1-0-migration, Property 9: Prompt composer byte-stability round-trip
    @given(order=st_gate_hook_order(), repeats=st_repeat_count())
    def test_compose_byte_stability_round_trip(
        self, order: list[str], repeats: int
    ) -> None:
        fragments = load_fragments(_FRAGMENTS_PATH)

        # (1) In-memory: repeated composition is byte-identical across repeats and
        #     equals the committed on-disk v1 gate file bytes (Req 8.2, 8.3).
        for hook_id in order:
            committed = (_REAL_HOOKS_DIR / f"{hook_id}.json").read_text(
                encoding="utf-8"
            )
            renders = [
                serialize_hook(
                    compose_hook(hook_id, fragments, hooks_dir=_REAL_HOOKS_DIR)
                )
                for _ in range(repeats)
            ]
            assert all(render == renders[0] for render in renders), (
                f"composition of '{hook_id}' is not deterministic across repeats"
            )
            assert renders[0] == committed, (
                f"composed '{hook_id}' differs from committed v1 gate file"
            )

        # (2) CLI round trip against a throwaway copy: repeated --write is
        #     idempotent, reproduces the committed bytes, and --verify then
        #     reports no drift (Req 8.3, 8.4). The committed files are never
        #     touched — only the temp copy is written/verified.
        td = tempfile.mkdtemp()
        try:
            hooks_dir = Path(td) / "hooks"
            hooks_dir.mkdir()
            for hook_id in order:
                shutil.copy(
                    _REAL_HOOKS_DIR / f"{hook_id}.json",
                    hooks_dir / f"{hook_id}.json",
                )

            common = [
                "--hooks-dir",
                str(hooks_dir),
                "--fragments",
                str(_FRAGMENTS_PATH),
            ]

            for _ in range(repeats):
                code, _out, err = _run_main_silently(["--write", *common])
                assert code == 0, f"--write failed: {err}"

            for hook_id in order:
                written = (hooks_dir / f"{hook_id}.json").read_text(encoding="utf-8")
                committed = (_REAL_HOOKS_DIR / f"{hook_id}.json").read_text(
                    encoding="utf-8"
                )
                assert written == committed, (
                    f"--write output for '{hook_id}' drifted from committed file"
                )

            code, _out, err = _run_main_silently(["--verify", *common])
            assert code == 0, f"--verify reported drift after --write: {err}"
        finally:
            shutil.rmtree(td, ignore_errors=True)
