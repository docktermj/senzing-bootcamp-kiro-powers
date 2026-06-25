"""No-op refactor property tests against the REAL on-disk gate hooks.

Feature: hook-architecture-improvements (Theme B — hook-prompt deduplication).

These tests compare the composer's output against the *real* ``.kiro.hook``
files in ``senzing-bootcamp/hooks``. Per ``structure.md``, tests that validate
real hook files live in the repo-root ``tests/`` directory (script-behavior
tests over generated/temp inputs live in ``senzing-bootcamp/tests/``).

Properties covered:

- **Property 4** — Shared fragments expand byte-identically across hooks. For
  any fragment referenced by two or more gate-hook templates, the text inlined
  for that fragment is byte-identical in every hook's composed ``then.prompt``.
  **Validates: Requirements 7.5**
- **Property 6** — Composition is a byte-identical no-op refactor. For each of
  the three Module 3 gate hooks, the composer's generated file content equals
  the current on-disk ``.kiro.hook`` content byte-for-byte; therefore
  ``compose_hook_prompts.py --verify`` exits 0 on the canonical repository.
  **Validates: Requirements 8.1, 7.2**
- **Property 7** — Any drift from the composed source is detected and reported.
  For any modification applied to a composed gate-hook's on-disk
  ``then.prompt`` (in a temp copy), running ``--verify`` exits 1 and reports the
  drifted hook id. **Validates: Requirements 7.3**

The fragment source and composer are imported via the repository ``sys.path``
script-import pattern; the real hooks directory is resolved relative to this
test file (repo root -> ``senzing-bootcamp/hooks``). The real hooks directory is
NEVER written to: Property 6 only reads + runs ``--verify`` (which does not
write), and Property 7 mutates a temp copy.
"""

from __future__ import annotations

import contextlib
import io
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages).
# Resolve relative to this test file: repo root -> senzing-bootcamp/scripts.
# ---------------------------------------------------------------------------
_REPO_ROOT: Path = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = str(_REPO_ROOT / "senzing-bootcamp" / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from compose_hook_prompts import (  # noqa: E402
    _MARKER_RE,
    HOOK_TEMPLATES,
    compose_hook,
    main,
    serialize_hook,
)
from hook_prompt_fragments import FRAGMENTS  # noqa: E402

# ---------------------------------------------------------------------------
# Paths (resolved relative to this test file: repo root -> senzing-bootcamp/...)
# ---------------------------------------------------------------------------

_HOOKS_DIR: Path = _REPO_ROOT / "senzing-bootcamp" / "hooks"
_FRAGMENTS_PATH: Path = (
    _REPO_ROOT / "senzing-bootcamp" / "scripts" / "hook_prompt_fragments.py"
)

# The three Module 3 gate hooks the composer owns.
GATE_HOOK_IDS: tuple[str, ...] = tuple(HOOK_TEMPLATES)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _referenced_fragment_names(template: str) -> set[str]:
    """Return the set of fragment names referenced by *template*'s markers."""
    return set(_MARKER_RE.findall(template))


def _fragments_referenced_by_multiple_templates() -> list[str]:
    """Return fragment names referenced by two or more gate-hook templates."""
    counts: Counter[str] = Counter()
    for template in HOOK_TEMPLATES.values():
        for name in _referenced_fragment_names(template):
            counts[name] += 1
    return sorted(name for name, count in counts.items() if count >= 2)


def _templates_referencing(name: str) -> list[str]:
    """Return the gate-hook ids whose template references fragment *name*."""
    return sorted(
        hook_id
        for hook_id, template in HOOK_TEMPLATES.items()
        if name in _referenced_fragment_names(template)
    )


def _composed_prompt(hook_id: str) -> str:
    """Compose *hook_id*'s ``then.prompt`` from the REAL hooks dir (read-only)."""
    return compose_hook(hook_id, FRAGMENTS, hooks_dir=_HOOKS_DIR)["then"]["prompt"]


def _run_main_silently(argv: list[str]) -> tuple[int, str, str]:
    """Invoke ``compose_hook_prompts.main(argv)`` capturing stdout/stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


# Computed once: the shared fragment(s). ``module3_condition_a`` is shared by all
# three gate hooks; the three ⛔ strings are each referenced by exactly one hook.
SHARED_FRAGMENT_NAMES: list[str] = _fragments_referenced_by_multiple_templates()


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


def st_shared_fragment_names() -> st.SearchStrategy[str]:
    """Sample over fragment names referenced by two or more gate-hook templates."""
    return st.sampled_from(SHARED_FRAGMENT_NAMES)


def st_gate_hook_ids() -> st.SearchStrategy[str]:
    """Sample over the three Module 3 gate-hook ids."""
    return st.sampled_from(GATE_HOOK_IDS)


def st_mutation_suffix() -> st.SearchStrategy[str]:
    """Generate a non-empty suffix to append to an on-disk prompt (a drift).

    Surrogates / control chars are excluded so the mutation round-trips cleanly
    through JSON serialization.
    """
    return st.text(
        alphabet=st.characters(blacklist_categories=("Cs", "Cc")),
        min_size=1,
        max_size=30,
    )


# ===========================================================================
# Property 4 — Shared fragments expand byte-identically across hooks
# ===========================================================================


class TestSharedFragmentByteIdentical:
    """Property 4: a fragment shared by 2+ gate hooks inlines byte-identically.

    **Validates: Requirements 7.5**
    """

    def test_a_shared_fragment_exists(self) -> None:
        """Guard: at least one fragment is shared across two or more templates.

        ``module3_condition_a`` is the CONDITION A block shared verbatim by all
        three gate hooks; without it the byte-identity property below would be
        vacuous.
        """
        assert SHARED_FRAGMENT_NAMES, (
            "expected at least one fragment referenced by 2+ gate-hook templates"
        )
        assert "module3_condition_a" in SHARED_FRAGMENT_NAMES

    # Feature: hook-architecture-improvements, Property 4
    @given(name=st_shared_fragment_names())
    @settings(max_examples=20)
    def test_shared_fragment_inlined_identically_across_hooks(
        self, name: str
    ) -> None:
        """The shared fragment's inlined text is byte-identical in every hook.

        For the shared fragment, assert ``FRAGMENTS[name]`` is a substring of
        every composed prompt whose template references it, that the extracted
        occurrence equals ``FRAGMENTS[name]`` byte-for-byte, and that the
        occurrence is identical across all referencing hooks.

        **Validates: Requirements 7.5**
        """
        expected = FRAGMENTS[name]
        referencing = _templates_referencing(name)
        assert len(referencing) >= 2, (
            f"fragment '{name}' should be referenced by 2+ hooks"
        )

        extracted: list[str] = []
        for hook_id in referencing:
            prompt = _composed_prompt(hook_id)
            index = prompt.find(expected)
            assert index != -1, (
                f"fragment '{name}' not inlined in composed prompt of '{hook_id}'"
            )
            occurrence = prompt[index : index + len(expected)]
            # The inlined occurrence equals the source fragment byte-for-byte.
            assert occurrence == expected, (
                f"fragment '{name}' inlined non-identically in '{hook_id}'"
            )
            extracted.append(occurrence)

        # Every referencing hook inlined the exact same bytes.
        assert all(occurrence == extracted[0] for occurrence in extracted), (
            f"fragment '{name}' inlined differently across hooks: {referencing}"
        )


# ===========================================================================
# Property 6 — Composition is a byte-identical no-op refactor
# ===========================================================================


class TestNoOpRefactor:
    """Property 6: composed content equals the on-disk bytes; ``--verify`` exits 0.

    **Validates: Requirements 8.1, 7.2**
    """

    # Feature: hook-architecture-improvements, Property 6
    @given(hook_id=st_gate_hook_ids())
    @settings(max_examples=20)
    def test_composed_content_is_byte_identical_to_on_disk(
        self, hook_id: str
    ) -> None:
        """For each gate hook, composed-in-memory bytes equal the on-disk file.

        Composes from the REAL hooks dir (read-only) and compares against the
        real file's bytes — the on-disk files are never modified.

        **Validates: Requirements 8.1**
        """
        composed = serialize_hook(
            compose_hook(hook_id, FRAGMENTS, hooks_dir=_HOOKS_DIR)
        )
        on_disk = (_HOOKS_DIR / f"{hook_id}.kiro.hook").read_text(encoding="utf-8")
        assert composed == on_disk, (
            f"composer output for '{hook_id}' is not byte-identical to the "
            "on-disk .kiro.hook file"
        )

    def test_all_three_gate_hooks_compose_byte_identically(self) -> None:
        """Concrete check across all three gate hooks at once (no sampling)."""
        for hook_id in GATE_HOOK_IDS:
            composed = serialize_hook(
                compose_hook(hook_id, FRAGMENTS, hooks_dir=_HOOKS_DIR)
            )
            on_disk = (_HOOKS_DIR / f"{hook_id}.kiro.hook").read_text(
                encoding="utf-8"
            )
            assert composed == on_disk, f"{hook_id} drifted from composed source"

    def test_verify_exits_zero_on_canonical_repo(self) -> None:
        """``--verify`` against the real hooks dir exits 0 (does not write).

        **Validates: Requirements 7.2**
        """
        code, out, _err = _run_main_silently(
            [
                "--verify",
                "--hooks-dir",
                str(_HOOKS_DIR),
                "--fragments",
                str(_FRAGMENTS_PATH),
            ]
        )
        assert code == 0, (
            "compose_hook_prompts.py --verify must exit 0 on canonical repo"
        )
        assert "up to date" in out


# ===========================================================================
# Property 7 — Any drift from the composed source is detected and reported
# ===========================================================================


class TestDriftDetection:
    """Property 7: a mutated on-disk prompt makes ``--verify`` exit 1 + name it.

    **Validates: Requirements 7.3**
    """

    @staticmethod
    def _copy_real_gate_hooks(dest: Path) -> Path:
        """Copy the three real gate-hook files into *dest* and return *dest*."""
        dest.mkdir(parents=True, exist_ok=True)
        for hook_id in GATE_HOOK_IDS:
            shutil.copy2(
                _HOOKS_DIR / f"{hook_id}.kiro.hook",
                dest / f"{hook_id}.kiro.hook",
            )
        return dest

    # Feature: hook-architecture-improvements, Property 7
    @given(target_id=st_gate_hook_ids(), suffix=st_mutation_suffix())
    @settings(max_examples=20)
    def test_drift_in_one_hook_is_detected_and_reported(
        self, target_id: str, suffix: str
    ) -> None:
        """Mutating one gate hook's prompt drives ``--verify`` to exit 1 + id.

        Works on a temp COPY of the real gate hooks. The mutation isolates the
        drift to ``then.prompt`` (the static fields stay canonical), and only
        the mutated hook should be reported as drifted.

        **Validates: Requirements 7.3**
        """
        tmp_dir = tempfile.mkdtemp()
        try:
            hooks_dir = self._copy_real_gate_hooks(Path(tmp_dir) / "hooks")

            # Mutate the target hook's prompt, re-serializing with the canonical
            # formatter so only then.prompt differs from the composed source.
            target_path = hooks_dir / f"{target_id}.kiro.hook"
            hook = compose_hook(target_id, FRAGMENTS, hooks_dir=hooks_dir)
            hook["then"]["prompt"] = hook["then"]["prompt"] + suffix
            target_path.write_text(
                serialize_hook(hook), encoding="utf-8", newline=""
            )

            code, _out, err = _run_main_silently(
                [
                    "--verify",
                    "--hooks-dir",
                    str(hooks_dir),
                    "--fragments",
                    str(_FRAGMENTS_PATH),
                ]
            )

            assert code == 1, "drift must cause --verify to exit 1"
            assert target_id in err, (
                f"drifted hook id '{target_id}' not reported in stderr"
            )
            assert "drifted" in err.lower()

            # Only the mutated hook is named on the 'drifted:' summary line.
            summary = [
                line for line in err.splitlines() if "drifted:" in line.lower()
            ]
            assert summary, "expected a 'drifted:' summary line"
            for other_id in GATE_HOOK_IDS:
                if other_id != target_id:
                    assert other_id not in summary[0], (
                        f"unmutated hook '{other_id}' wrongly reported as drifted"
                    )
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
