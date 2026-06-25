"""Unit / CLI example tests for the compose_hook_prompts.py composer.

Feature: hook-architecture-improvements (Theme B — hook-prompt deduplication).

These are *script-behavior* example/unit tests exercised over temporary hook
directories (never the real ``senzing-bootcamp/hooks``), so per ``structure.md``
they live in ``senzing-bootcamp/tests/`` rather than the repo-root ``tests/``.

Property-based coverage of the composer logic lives in
``test_compose_hook_prompts_properties.py`` (task 3.5); the no-op refactor /
drift properties against the *real* on-disk hooks live in
``tests/test_compose_no_op_refactor.py`` (task 3.7). This file covers the
concrete CLI/example contract (Hypothesis not required):

- ``--write`` into a temp dir produces files byte-identical to the originals
  (Req 6.3).
- ``main(argv=None)`` + argparse + the exit 0/1 contract (Req 6.4).
- ``--verify`` clean-copy passes and reports the drifted hook id after a
  mutation (Req 7.1).
- The fragment-source contract: ``FRAGMENTS`` shape, the four expected
  fragments, the composer's marker references, stdlib-only import, and the
  single-source (each fragment text defined once) invariant
  (Req 5.1, 5.2, 5.4, 5.5).
"""

from __future__ import annotations

import ast
import json
import shutil
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
import hook_prompt_fragments  # noqa: E402

# ---------------------------------------------------------------------------
# Real-repo paths
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_HOOKS_DIR = _REPO_ROOT / "senzing-bootcamp" / "hooks"
_FRAGMENTS_PATH = _REPO_ROOT / "senzing-bootcamp" / "scripts" / "hook_prompt_fragments.py"
_FRAGMENTS_SOURCE_PATH = Path(hook_prompt_fragments.__file__).resolve()

# The three Module 3 gate hooks the composer owns.
GATE_HOOK_IDS = tuple(compose_hook_prompts.HOOK_TEMPLATES.keys())

# The four fragments the fragment source must define (Req 5.1, 5.2).
EXPECTED_FRAGMENT_NAMES = frozenset(
    {
        "module3_condition_a",
        "module3_gate_on_stop_violation",
        "module3_block_completion",
        "module3_block_advancement",
    }
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _copy_real_gate_hooks(dest: Path) -> Path:
    """Copy the three real gate-hook files into *dest* and return *dest*.

    The composer reads each hook's static fields (``name``/``version``/
    ``description``/``when``) from the on-disk file, so a clean copy of the
    canonical files must exist in the temp hooks dir before write/verify.
    """
    dest.mkdir(parents=True, exist_ok=True)
    for hook_id in GATE_HOOK_IDS:
        src = _HOOKS_DIR / f"{hook_id}.kiro.hook"
        shutil.copy2(src, dest / f"{hook_id}.kiro.hook")
    return dest


def _write_fragments_module(path: Path, fragments: dict[str, str]) -> Path:
    """Write a stdlib-only fragment-source module exposing *fragments*."""
    body = "from __future__ import annotations\n\n"
    body += f"FRAGMENTS: dict[str, str] = {fragments!r}\n"
    path.write_text(body, encoding="utf-8")
    return path


# ===========================================================================
# --write into a temp dir (Req 6.3)
# ===========================================================================


class TestWriteMode:
    """``--write`` composes the gate hooks into a temp dir byte-identically.

    **Validates: Requirements 6.3**
    """

    def test_write_creates_gate_hook_files_and_exits_zero(
        self, tmp_path: Path
    ) -> None:
        hooks_dir = _copy_real_gate_hooks(tmp_path / "hooks")

        code = compose_hook_prompts.main(
            [
                "--write",
                "--hooks-dir",
                str(hooks_dir),
                "--fragments",
                str(_FRAGMENTS_PATH),
            ]
        )

        assert code == 0
        for hook_id in GATE_HOOK_IDS:
            assert (hooks_dir / f"{hook_id}.kiro.hook").is_file()

    def test_written_files_are_byte_identical_to_originals(
        self, tmp_path: Path
    ) -> None:
        hooks_dir = _copy_real_gate_hooks(tmp_path / "hooks")

        code = compose_hook_prompts.main(
            [
                "--write",
                "--hooks-dir",
                str(hooks_dir),
                "--fragments",
                str(_FRAGMENTS_PATH),
            ]
        )

        assert code == 0
        for hook_id in GATE_HOOK_IDS:
            composed = (hooks_dir / f"{hook_id}.kiro.hook").read_bytes()
            original = (_HOOKS_DIR / f"{hook_id}.kiro.hook").read_bytes()
            assert composed == original, f"{hook_id} write was not byte-identical"

    def test_write_is_default_mode_when_no_flag(self, tmp_path: Path) -> None:
        # Mutate a copied hook, then run with NO mode flag; --write is the
        # default so the file is recomposed back to the canonical bytes.
        hooks_dir = _copy_real_gate_hooks(tmp_path / "hooks")
        target = hooks_dir / f"{GATE_HOOK_IDS[0]}.kiro.hook"
        data = json.loads(target.read_text(encoding="utf-8"))
        data["then"]["prompt"] = data["then"]["prompt"] + "\n\nDRIFT"
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")

        code = compose_hook_prompts.main(
            ["--hooks-dir", str(hooks_dir), "--fragments", str(_FRAGMENTS_PATH)]
        )

        assert code == 0
        original = (_HOOKS_DIR / f"{GATE_HOOK_IDS[0]}.kiro.hook").read_bytes()
        assert target.read_bytes() == original


# ===========================================================================
# main(argv=None) + argparse + exit 0/1 contract (Req 6.4)
# ===========================================================================


class TestCliContract:
    """``main(argv)`` returns 0 on success and 1 on error.

    **Validates: Requirements 6.4**
    """

    def test_main_returns_zero_on_verify_of_clean_copy(self, tmp_path: Path) -> None:
        hooks_dir = _copy_real_gate_hooks(tmp_path / "hooks")

        code = compose_hook_prompts.main(
            ["--verify", "--hooks-dir", str(hooks_dir), "--fragments", str(_FRAGMENTS_PATH)]
        )

        assert code == 0

    def test_main_returns_one_for_nonexistent_hooks_dir(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        missing = tmp_path / "does-not-exist"

        code = compose_hook_prompts.main(
            ["--verify", "--hooks-dir", str(missing), "--fragments", str(_FRAGMENTS_PATH)]
        )

        assert code == 1
        err = capsys.readouterr().err
        assert "hooks directory not found" in err
        assert str(missing) in err

    def test_main_returns_one_for_unknown_fragment(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # A fragment source that omits ``module3_condition_a`` (referenced by
        # every gate-hook template) forces an unknown-fragment failure.
        hooks_dir = _copy_real_gate_hooks(tmp_path / "hooks")
        broken_fragments = {
            "module3_gate_on_stop_violation": "x",
            "module3_block_completion": "x",
            "module3_block_advancement": "x",
        }
        frag_path = _write_fragments_module(
            tmp_path / "broken_fragments.py", broken_fragments
        )

        code = compose_hook_prompts.main(
            ["--write", "--hooks-dir", str(hooks_dir), "--fragments", str(frag_path)]
        )

        assert code == 1
        err = capsys.readouterr().err
        assert "unknown fragment" in err
        assert "module3_condition_a" in err

    def test_main_argv_none_uses_sys_argv(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # main(argv=None) must fall back to sys.argv; drive it through a clean
        # temp copy in --verify mode and assert the success contract.
        hooks_dir = _copy_real_gate_hooks(tmp_path / "hooks")
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "compose_hook_prompts.py",
                "--verify",
                "--hooks-dir",
                str(hooks_dir),
                "--fragments",
                str(_FRAGMENTS_PATH),
            ],
        )

        code = compose_hook_prompts.main()

        assert code == 0

    def test_write_and_verify_are_mutually_exclusive(self, tmp_path: Path) -> None:
        hooks_dir = _copy_real_gate_hooks(tmp_path / "hooks")

        with pytest.raises(SystemExit) as excinfo:
            compose_hook_prompts.main(
                [
                    "--write",
                    "--verify",
                    "--hooks-dir",
                    str(hooks_dir),
                    "--fragments",
                    str(_FRAGMENTS_PATH),
                ]
            )

        # argparse reports the conflict with a non-zero exit code.
        assert excinfo.value.code != 0


# ===========================================================================
# --verify compare path (Req 7.1)
# ===========================================================================


class TestVerifyMode:
    """``--verify`` passes on a clean copy and reports a drifted hook id.

    **Validates: Requirements 7.1**
    """

    def test_verify_clean_copy_exits_zero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        hooks_dir = _copy_real_gate_hooks(tmp_path / "hooks")

        code = compose_hook_prompts.main(
            ["--verify", "--hooks-dir", str(hooks_dir), "--fragments", str(_FRAGMENTS_PATH)]
        )

        assert code == 0
        out = capsys.readouterr().out
        assert "up to date" in out

    def test_verify_detects_drift_and_reports_hook_id(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        hooks_dir = _copy_real_gate_hooks(tmp_path / "hooks")
        drifted_id = "enforce-gate-on-stop"

        # Mutate one on-disk gate-hook prompt in the temp copy.
        target = hooks_dir / f"{drifted_id}.kiro.hook"
        data = json.loads(target.read_text(encoding="utf-8"))
        data["then"]["prompt"] = data["then"]["prompt"] + "\n\nUNAUTHORIZED EDIT"
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")

        code = compose_hook_prompts.main(
            ["--verify", "--hooks-dir", str(hooks_dir), "--fragments", str(_FRAGMENTS_PATH)]
        )

        assert code == 1
        err = capsys.readouterr().err
        assert drifted_id in err
        assert "drifted" in err.lower()

    def test_verify_clean_hooks_not_reported_as_drifted(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        hooks_dir = _copy_real_gate_hooks(tmp_path / "hooks")
        drifted_id = "enforce-gate-on-stop"
        clean_ids = [h for h in GATE_HOOK_IDS if h != drifted_id]

        target = hooks_dir / f"{drifted_id}.kiro.hook"
        data = json.loads(target.read_text(encoding="utf-8"))
        data["then"]["prompt"] = "totally different prompt"
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")

        code = compose_hook_prompts.main(
            ["--verify", "--hooks-dir", str(hooks_dir), "--fragments", str(_FRAGMENTS_PATH)]
        )

        assert code == 1
        captured = capsys.readouterr()
        summary_line = [
            line for line in captured.err.splitlines() if "drifted:" in line.lower()
        ]
        assert summary_line, "expected a 'drifted:' summary line"
        # Only the mutated hook is named on the summary line.
        for clean_id in clean_ids:
            assert clean_id not in summary_line[0]


# ===========================================================================
# Fragment-source contract (Req 5.1, 5.2, 5.4, 5.5)
# ===========================================================================


class TestFragmentSourceContract:
    """The fragment source is a stdlib-only single source of named fragments.

    **Validates: Requirements 5.1, 5.2, 5.4, 5.5**
    """

    def test_fragments_is_dict_of_str_to_str(self) -> None:
        fragments = hook_prompt_fragments.FRAGMENTS
        assert isinstance(fragments, dict)
        assert fragments, "FRAGMENTS must not be empty"
        for key, value in fragments.items():
            assert isinstance(key, str) and key
            assert isinstance(value, str) and value.strip()

    def test_four_expected_fragments_present(self) -> None:
        # CONDITION A checkpoint check (Req 5.1) + the three block output strings
        # (Req 5.2) are all named fragments.
        assert EXPECTED_FRAGMENT_NAMES <= set(hook_prompt_fragments.FRAGMENTS)

    def test_condition_a_fragment_holds_checkpoint_check(self) -> None:
        condition_a = hook_prompt_fragments.FRAGMENTS["module3_condition_a"]
        assert "web_service.status" in condition_a
        assert "web_page.status" in condition_a

    def test_each_block_fragment_is_a_gate_violation_string(self) -> None:
        for name in (
            "module3_gate_on_stop_violation",
            "module3_block_completion",
            "module3_block_advancement",
        ):
            assert "\u26d4" in hook_prompt_fragments.FRAGMENTS[name]

    def test_composer_templates_reference_fragment_markers(self) -> None:
        # Every gate-hook template references at least one {{fragment:NAME}}
        # marker (Req 5.4 — hooks reference fragments by name).
        for hook_id, template in compose_hook_prompts.HOOK_TEMPLATES.items():
            markers = compose_hook_prompts._MARKER_RE.findall(template)
            assert markers, f"{hook_id} template references no fragment markers"
            # Every referenced marker resolves to a defined fragment.
            for name in markers:
                assert name in hook_prompt_fragments.FRAGMENTS

    def test_all_expected_fragments_are_referenced_by_some_template(self) -> None:
        referenced: set[str] = set()
        for template in compose_hook_prompts.HOOK_TEMPLATES.values():
            referenced.update(compose_hook_prompts._MARKER_RE.findall(template))
        assert EXPECTED_FRAGMENT_NAMES <= referenced

    def test_fragment_source_imports_stdlib_only(self) -> None:
        # Req 5.5: stdlib-only, no third-party import. The module only needs
        # ``from __future__ import annotations``.
        source = _FRAGMENTS_SOURCE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        stdlib_top_levels = {"__future__"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    assert top in stdlib_top_levels, f"non-stdlib import: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0]
                    assert top in stdlib_top_levels, (
                        f"non-stdlib import: from {node.module}"
                    )

    def test_single_source_each_fragment_text_defined_once(self) -> None:
        # Req 5.3 single-source spirit: no fragment text is duplicated across
        # two names; each shared text is defined exactly once in FRAGMENTS.
        values = list(hook_prompt_fragments.FRAGMENTS.values())
        assert len(values) == len(set(values)), "duplicate fragment text detected"
