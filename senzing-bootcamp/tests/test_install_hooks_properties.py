"""Property-based tests for the install_hooks.py installer logic.

Feature: hook-architecture-improvements (Theme C — capture-hook install
reliability).

These are *script-behavior* property tests exercised over temporary hook
directories (never the real ``.kiro/hooks``), so per ``structure.md`` they live
in ``senzing-bootcamp/tests/`` rather than the repo-root ``tests/``.

Properties covered:

- **Property 9** — Installer discovered set equals the hook-file set.
  Validates: Requirements 9.3, 12.1
- **Property 13** — Non-interactive ``--all`` / ``--essential`` modes never read
  stdin and exit 0. Validates: Requirements 11.3, 11.4, 12.4
- **Property 14** — A missing hooks directory under a non-interactive flag fails
  cleanly (exit 1 + reported path). Validates: Requirements 11.5
"""

from __future__ import annotations

import builtins
import contextlib
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import install_hooks  # noqa: E402


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


def st_hook_id() -> st.SearchStrategy[str]:
    """Generate valid hook ids (lowercase, hyphen-separated segments)."""
    return st.from_regex(r"[a-z][a-z0-9]{0,7}(-[a-z0-9]{1,7}){0,3}", fullmatch=True)


def st_hook_filename() -> st.SearchStrategy[str]:
    """Generate ``<hook-id>.kiro.hook`` filenames."""
    return st_hook_id().map(lambda hook_id: f"{hook_id}.kiro.hook")


def st_hook_filenames(
    min_size: int = 1, max_size: int = 8
) -> st.SearchStrategy[list[str]]:
    """Generate a unique list of ``*.kiro.hook`` filenames."""
    return st.lists(
        st_hook_filename(), min_size=min_size, max_size=max_size, unique=True
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_hook_file(power_dir: Path, filename: str) -> None:
    """Write a minimal but schema-valid ``.kiro.hook`` JSON file."""
    hook_id = install_hooks._hook_id(filename)
    verb_phrase = hook_id.replace("-", " ")
    data = {
        "name": f"to {verb_phrase}",
        "version": "1.0.0",
        "when": {"type": "agentStop"},
        "then": {"type": "askAgent", "prompt": f"Do the {verb_phrase} thing."},
    }
    (power_dir / filename).write_text(json.dumps(data, indent=2), encoding="utf-8")


class _RaisingStdin:
    """A stand-in for ``sys.stdin`` that fails loudly if read from."""

    def read(self, *args: object, **kwargs: object) -> str:
        raise AssertionError("non-interactive mode read from sys.stdin.read()")

    def readline(self, *args: object, **kwargs: object) -> str:
        raise AssertionError("non-interactive mode read from sys.stdin.readline()")

    def __iter__(self) -> object:
        raise AssertionError("non-interactive mode iterated sys.stdin")


@contextlib.contextmanager
def _stdin_tripwire():
    """Make any ``input()`` call or ``sys.stdin`` read raise immediately."""

    def _no_input(*args: object, **kwargs: object) -> str:
        raise AssertionError("non-interactive mode called input()")

    saved_input = builtins.input
    saved_stdin = sys.stdin
    builtins.input = _no_input  # type: ignore[assignment]
    sys.stdin = _RaisingStdin()  # type: ignore[assignment]
    try:
        yield
    finally:
        builtins.input = saved_input  # type: ignore[assignment]
        sys.stdin = saved_stdin


def _run_main_silently(argv: list[str]) -> tuple[int, str, str]:
    """Invoke ``install_hooks.main(argv)`` capturing stdout/stderr.

    Returns:
        A ``(exit_code, stdout, stderr)`` tuple.
    """
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = install_hooks.main(argv)
    return code, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# Property 9 — Installer discovered set equals the hook-file set
# ---------------------------------------------------------------------------


class TestInstallerDiscovery:
    """Property 9: discover_hooks returns exactly the *.kiro.hook file set.

    **Validates: Requirements 9.3, 12.1**
    """

    # Feature: hook-architecture-improvements, Property 9
    @given(filenames=st_hook_filenames())
    @settings(max_examples=20)
    def test_discovered_set_equals_hook_file_set(self, filenames: list[str]) -> None:
        td = tempfile.mkdtemp()
        try:
            power_dir = Path(td) / "hooks"
            power_dir.mkdir()
            for filename in filenames:
                _write_hook_file(power_dir, filename)

            discovered = install_hooks.discover_hooks(power_dir)

            # Exactly one entry per file.
            assert len(discovered) == len(filenames)
            discovered_filenames = [entry[0] for entry in discovered]
            assert len(discovered_filenames) == len(set(discovered_filenames))

            # The discovered filename set equals the *.kiro.hook file set.
            assert set(discovered_filenames) == set(filenames)
        finally:
            shutil.rmtree(td, ignore_errors=True)

    # Feature: hook-architecture-improvements, Property 9
    @given(
        filenames=st_hook_filenames(),
        noise=st.lists(
            st.from_regex(r"[a-z0-9_-]{1,12}\.(md|yaml|json|txt)", fullmatch=True),
            max_size=4,
            unique=True,
        ),
    )
    @settings(max_examples=20)
    def test_only_kiro_hook_files_are_discovered(
        self, filenames: list[str], noise: list[str]
    ) -> None:
        td = tempfile.mkdtemp()
        try:
            power_dir = Path(td) / "hooks"
            power_dir.mkdir()
            for filename in filenames:
                _write_hook_file(power_dir, filename)
            # Non-hook files in the same directory must be ignored.
            for other in noise:
                (power_dir / other).write_text("noise", encoding="utf-8")

            discovered = install_hooks.discover_hooks(power_dir)
            discovered_filenames = {entry[0] for entry in discovered}

            assert discovered_filenames == set(filenames)
        finally:
            shutil.rmtree(td, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 13 — Non-interactive modes never read stdin and exit 0
# ---------------------------------------------------------------------------


class TestNonInteractiveModes:
    """Property 13: --all / --essential never read stdin and exit 0.

    **Validates: Requirements 11.3, 11.4, 12.4**
    """

    # Feature: hook-architecture-improvements, Property 13
    @given(filenames=st_hook_filenames(), flag=st.sampled_from(["--all", "--essential"]))
    @settings(max_examples=20)
    def test_non_interactive_flag_exits_zero_without_stdin(
        self, filenames: list[str], flag: str
    ) -> None:
        td = tempfile.mkdtemp()
        try:
            power_dir = Path(td) / "hooks"
            power_dir.mkdir()
            user_dir = Path(td) / "user_hooks"
            for filename in filenames:
                _write_hook_file(power_dir, filename)

            argv = [
                flag,
                "--power-dir",
                str(power_dir),
                "--user-dir",
                str(user_dir),
            ]

            with _stdin_tripwire():
                code, _out, _err = _run_main_silently(argv)

            assert code == 0
        finally:
            shutil.rmtree(td, ignore_errors=True)

    # Feature: hook-architecture-improvements, Property 13
    @given(filenames=st_hook_filenames())
    @settings(max_examples=20)
    def test_both_modes_install_into_empty_user_dir(
        self, filenames: list[str]
    ) -> None:
        td = tempfile.mkdtemp()
        try:
            power_dir = Path(td) / "hooks"
            power_dir.mkdir()
            for filename in filenames:
                _write_hook_file(power_dir, filename)

            for flag in ("--all", "--essential"):
                user_dir = Path(td) / f"user_{flag.strip('-')}"
                argv = [
                    flag,
                    "--power-dir",
                    str(power_dir),
                    "--user-dir",
                    str(user_dir),
                ]
                with _stdin_tripwire():
                    code, _out, _err = _run_main_silently(argv)
                assert code == 0
                # The destination dir is created even when nothing matches.
                assert user_dir.is_dir()
        finally:
            shutil.rmtree(td, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 14 — Missing hooks directory under a non-interactive flag fails cleanly
# ---------------------------------------------------------------------------


class TestMissingHooksDirectory:
    """Property 14: missing power-dir under --all/--essential exits 1 + reports path.

    **Validates: Requirements 11.5**
    """

    # Feature: hook-architecture-improvements, Property 14
    @given(
        missing_name=st.from_regex(r"[a-z0-9][a-z0-9_-]{0,15}", fullmatch=True),
        flag=st.sampled_from(["--all", "--essential"]),
    )
    @settings(max_examples=20)
    def test_missing_power_dir_exits_one_and_reports_path(
        self, missing_name: str, flag: str
    ) -> None:
        td = tempfile.mkdtemp()
        try:
            missing_dir = Path(td) / missing_name / "hooks"
            user_dir = Path(td) / "user_hooks"
            assert not missing_dir.exists()

            argv = [
                flag,
                "--power-dir",
                str(missing_dir),
                "--user-dir",
                str(user_dir),
            ]

            with _stdin_tripwire():
                code, out, err = _run_main_silently(argv)

            assert code == 1
            # The missing directory path must be reported to the user.
            combined = out + err
            assert str(missing_dir) in combined
        finally:
            shutil.rmtree(td, ignore_errors=True)
