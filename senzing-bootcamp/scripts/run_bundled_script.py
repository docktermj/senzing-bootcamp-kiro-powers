#!/usr/bin/env python3
"""Guarded runner for bundled ``senzing-bootcamp/scripts/<name>.py`` helpers.

Bootcamp, onboarding, and graduation steps shell out to bundled scripts under
``senzing-bootcamp/scripts/`` (for example ``install_hooks.py``,
``completion_artifacts.py``, ``status.py``, ``backup_project.py``, and
``generate_docs_index.py``). Those scripts are not guaranteed to be materialized
in a bootcamper's workspace. Invoking ``python3 senzing-bootcamp/scripts/<name>.py``
directly when the file is absent surfaces a raw interpreter error
(``No such file or directory``, exit 2) and silently drops the step's effect.

This wrapper applies the generic-step degradation pattern so a missing bundled
script never produces a raw file-not-found interpreter error:

1. **Existence check first** — resolve the bundled script at the workspace path
   the steps use (``<cwd>/senzing-bootcamp/scripts/<name>``) and check it exists
   before shelling out.
2. **Self-repair once** — when it is absent, run the onboarding self-repair
   (``preflight.py --fix``) a single time to materialize/restore the bundled
   scripts directory, then re-check.
3. **Inline/no-op fallback** — when the script is still absent after self-repair,
   degrade gracefully: print a one-line notice and exit 0 (a clean skip), never a
   file-not-found error.

When the bundled script IS present it is executed unchanged and its own exit code
is propagated, so present-script behavior is preserved exactly.

Usage:
    python3 senzing-bootcamp/scripts/run_bundled_script.py <name> [args...]
    python3 senzing-bootcamp/scripts/run_bundled_script.py --no-repair <name> [args...]
    python3 senzing-bootcamp/scripts/run_bundled_script.py --quiet <name> [args...]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Workspace-relative bundled scripts directory the documented steps reference,
# mirroring ``preflight.py``'s ``BUNDLED_SCRIPTS_REL`` convention.
BUNDLED_SCRIPTS_REL = os.path.join("senzing-bootcamp", "scripts")

# The onboarding self-repair entry point that materializes the bundled scripts
# directory under ``--fix`` (see ``preflight.check_bundled_scripts`` /
# ``AutoFixer._fix_bundled_scripts``).
PREFLIGHT_SCRIPT = "preflight.py"

# The installed power's own scripts directory (this file's location) is always
# present and is the authoritative source for the self-repair entry point.
INSTALLED_SCRIPTS_DIR = Path(__file__).resolve().parent


def workspace_scripts_dir() -> Path:
    """Return the workspace-relative bundled scripts directory.

    Returns:
        The ``<cwd>/senzing-bootcamp/scripts`` path the documented steps use.
    """
    return Path.cwd() / BUNDLED_SCRIPTS_REL


def resolve_script(name: str, scripts_dir: Path | None = None) -> Path:
    """Resolve a bundled script's path within the workspace scripts directory.

    Args:
        name: Bundled script filename (e.g. ``generate_docs_index.py``).
        scripts_dir: Override for the scripts directory (defaults to the
            workspace scripts directory).

    Returns:
        The path the script would occupy under the workspace scripts directory.
    """
    base = scripts_dir if scripts_dir is not None else workspace_scripts_dir()
    return base / name


def script_exists(name: str, scripts_dir: Path | None = None) -> bool:
    """Return whether a bundled script exists in the workspace scripts directory.

    Args:
        name: Bundled script filename.
        scripts_dir: Override for the scripts directory.

    Returns:
        True when the resolved script is a regular file.
    """
    return resolve_script(name, scripts_dir).is_file()


def _preflight_entry_point(scripts_dir: Path) -> Path | None:
    """Return a runnable ``preflight.py``, preferring the workspace copy.

    Falls back to the installed power's ``preflight.py`` (always present) when
    the workspace copy is absent, so self-repair can run even when the workspace
    scripts directory has not been materialized yet.

    Args:
        scripts_dir: The workspace scripts directory.

    Returns:
        A path to a runnable ``preflight.py``, or None when none can be found.
    """
    workspace_preflight = scripts_dir / PREFLIGHT_SCRIPT
    if workspace_preflight.is_file():
        return workspace_preflight
    installed_preflight = INSTALLED_SCRIPTS_DIR / PREFLIGHT_SCRIPT
    if installed_preflight.is_file():
        return installed_preflight
    return None


def attempt_self_repair(scripts_dir: Path | None = None) -> bool:
    """Run ``preflight.py --fix`` once to materialize the bundled scripts dir.

    The self-repair is idempotent and never clobbers already-present scripts
    (see ``preflight.AutoFixer._fix_bundled_scripts``). Any preflight failure is
    swallowed — the caller falls back to the inline no-op path.

    Args:
        scripts_dir: Override for the scripts directory.

    Returns:
        True when the self-repair command ran to completion (regardless of its
        verdict), False when no ``preflight.py`` could be found or it could not
        be executed.
    """
    base = scripts_dir if scripts_dir is not None else workspace_scripts_dir()
    preflight = _preflight_entry_point(base)
    if preflight is None:
        return False
    try:
        subprocess.run(
            [sys.executable, str(preflight), "--fix", "--json"],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return True


def run_bundled_script(
    name: str,
    args: list[str] | None = None,
    *,
    allow_repair: bool = True,
    quiet: bool = False,
    scripts_dir: Path | None = None,
) -> int:
    """Run a bundled script with graceful degradation when it is absent.

    Applies the generic-step degradation pattern: existence check, one-shot
    self-repair, then an inline no-op fallback. A missing bundled script never
    surfaces a raw file-not-found interpreter error.

    Args:
        name: Bundled script filename to run (e.g. ``generate_docs_index.py``).
        args: Passthrough arguments forwarded to the bundled script.
        allow_repair: When True, attempt ``preflight.py --fix`` self-repair once
            before falling back to the no-op path.
        quiet: When True, suppress the one-line skip notice on the no-op path.
        scripts_dir: Override for the scripts directory (used in tests).

    Returns:
        The bundled script's exit code when it is present and executed, or 0 for
        the graceful no-op fallback when it cannot be found or restored.
    """
    args = list(args or [])

    if not script_exists(name, scripts_dir) and allow_repair:
        attempt_self_repair(scripts_dir)

    target = resolve_script(name, scripts_dir)
    if not target.is_file():
        if not quiet:
            print(
                f"[run_bundled_script] Skipped optional bundled script "
                f"'{name}': not present and could not be restored — continuing "
                f"(graceful no-op).",
                file=sys.stderr,
            )
        return 0

    try:
        completed = subprocess.run(
            [sys.executable, str(target), *args],
            cwd=os.getcwd(),
        )
    except OSError as exc:
        # Defensive: the file existed at the check above but could not be
        # executed. Degrade gracefully rather than propagating a raw OSError.
        if not quiet:
            print(
                f"[run_bundled_script] Could not execute '{name}': {exc} — "
                f"continuing (graceful no-op).",
                file=sys.stderr,
            )
        return 0
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run the requested bundled script with degradation.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]`` when None).

    Returns:
        The bundled script's exit code, or 0 for the graceful no-op fallback.
    """
    parser = argparse.ArgumentParser(
        prog="run_bundled_script.py",
        description=(
            "Run a bundled senzing-bootcamp/scripts/<name>.py helper with an "
            "existence guard, one-shot preflight --fix self-repair, and an "
            "inline no-op fallback so a missing script never errors."
        ),
    )
    parser.add_argument(
        "name",
        help="Bundled script filename to run (e.g. generate_docs_index.py).",
    )
    parser.add_argument(
        "--no-repair",
        action="store_true",
        help="Do not attempt preflight --fix self-repair when the script is absent.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the one-line skip notice on the no-op fallback path.",
    )
    parser.add_argument(
        "script_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded verbatim to the bundled script.",
    )
    args = parser.parse_args(argv)

    return run_bundled_script(
        args.name,
        args.script_args,
        allow_repair=not args.no_repair,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    sys.exit(main())
