#!/usr/bin/env python3
"""Compose self-contained Module 3 gate-hook prompts from shared fragments.

The IDE reads each ``.kiro.hook`` file as-is: ``then.prompt`` must be a
self-contained string with no include/expansion mechanism at runtime. This
script is the **build-time** single-source mechanism for the shared Module 3
gate logic. It holds a per-hook prompt *template* containing
``{{fragment:NAME}}`` markers plus the per-hook literal text, and expands each
marker using the authoritative ``FRAGMENTS`` mapping in
``hook_prompt_fragments.py``.

The composer's ``--write`` output is **byte-identical** to the current on-disk
gate hooks, so introducing it is a pure no-op refactor that ``--verify`` proves
in CI (run *before* ``sync_hook_registry.py --verify``).

Modes
-----
--write   (default) Compose each gate hook and write it to the hooks directory.
--verify  Compose each gate hook in memory and compare against the on-disk
          bytes; exit 0 if every hook matches, else exit 1 listing each
          drifted hook id.

Usage
-----
    python3 senzing-bootcamp/scripts/compose_hook_prompts.py            # --write
    python3 senzing-bootcamp/scripts/compose_hook_prompts.py --verify
    python3 senzing-bootcamp/scripts/compose_hook_prompts.py --hooks-dir DIR
    python3 senzing-bootcamp/scripts/compose_hook_prompts.py --fragments FILE

Only Python standard-library modules are used.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Default paths (relative to the repository root)
# ---------------------------------------------------------------------------

HOOKS_DIR = Path("senzing-bootcamp/hooks")
FRAGMENTS_PATH = Path(__file__).resolve().with_name("hook_prompt_fragments.py")

# ---------------------------------------------------------------------------
# Marker syntax
#
# Markers use ``{{fragment:NAME}}`` where NAME matches [A-Za-z0-9_]+. This token
# does not occur in any current hook prompt, so it is unambiguous to scan for
# both expansion and the "no unexpanded markers remain" assertion (Req 6.2).
# ---------------------------------------------------------------------------

_MARKER_RE = re.compile(r"\{\{fragment:([A-Za-z0-9_]+)\}\}")
_RESIDUAL_MARKER_RE = re.compile(r"\{\{fragment:([^}]*)\}?\}?")
_RESIDUAL_TOKEN = "{{fragment:"


class UnknownFragmentError(Exception):
    """Raised when a template references a fragment absent from the source.

    Attributes:
        fragment_name: The undefined fragment name referenced by the marker.
    """

    def __init__(self, fragment_name: str) -> None:
        self.fragment_name = fragment_name
        super().__init__(f"unknown fragment '{fragment_name}'")


# ---------------------------------------------------------------------------
# Per-hook prompt templates
#
# Each template is the hook's full then.prompt with the shared regions replaced
# by {{fragment:NAME}} markers. All per-hook literal text (the CHECK clause, the
# question-pending guard in enforce-gate-on-stop, surrounding prose) stays
# verbatim so composition reproduces the original prompt byte-for-byte.
# ---------------------------------------------------------------------------

HOOK_TEMPLATES: dict[str, str] = {
    "gate-module3-visualization": (
        "CHECK — Is this write updating `config/bootcamp_progress.json` to mark "
        "Module 3 as complete (adding 3 to modules_completed, or setting "
        "module_3_verification.status to 'passed')?\n\n"
        "If NO (not a Module 3 completion write, or not writing to "
        "bootcamp_progress.json): produce no output at all. Do nothing.\n\n"
        "If YES: Read the CURRENT contents of `config/bootcamp_progress.json` and "
        "check this condition:\n\n"
        "{{fragment:module3_condition_a}}\n\n"
        "If CONDITION A is true: produce no output at all. Do nothing.\n\n"
        "If CONDITION A is not met: STOP. Do NOT allow this write. Output exactly:"
        "\n\n"
        "{{fragment:module3_block_completion}}\n\n"
        "Do not proceed with the write operation."
    ),
    "enforce-mandatory-gate": (
        "CHECK — Is this write updating `config/bootcamp_progress.json` to advance "
        "`current_step` past Step 9 (the ⛔ mandatory gate step for Web Service + "
        "Visualization)?\n\n"
        "If NO (not writing to `config/bootcamp_progress.json`, or not changing "
        "`current_step`, or `current_step` is not being set to a value greater than "
        "9): produce no output at all. Do nothing.\n\n"
        "If YES (the write sets `current_step` to 10 or higher, advancing past the "
        "⛔ mandatory gate Step 9): Read the CURRENT contents of "
        "`config/bootcamp_progress.json` and check TWO conditions:\n\n"
        "{{fragment:module3_condition_a}}\n\n"
        "If CONDITION A is true: produce no output at all. Do nothing. The "
        "mandatory gate has been satisfied.\n\n"
        "If CONDITION A is not met: STOP. Do NOT allow this write. Block the "
        "operation. Output exactly:\n\n"
        "{{fragment:module3_block_advancement}}\n\n"
        "Do not proceed with the write operation."
    ),
    "enforce-gate-on-stop": (
        "If `config/.question_pending` exists, produce no output at all — defer to "
        "`ask-bootcamper`.\n\n"
        "CHECK — Read `config/bootcamp_progress.json` and evaluate:\n\n"
        "1. Is `current_module` equal to 3?\n"
        "2. Is `current_step` greater than or equal to 9?\n\n"
        "If EITHER condition is false: produce no output. Do nothing.\n\n"
        "If BOTH are true: Check whether the ⛔ mandatory gate for Step 9 has been "
        "satisfied:\n\n"
        "{{fragment:module3_condition_a}}\n\n"
        "If CONDITION A is true: produce no output. The mandatory gate is "
        "satisfied.\n\n"
        "If CONDITION A is not met: The agent has reached or passed Step 9 without "
        "executing it. This is a ⛔ mandatory gate violation. Output exactly:\n\n"
        "{{fragment:module3_gate_on_stop_violation}}"
    ),
}


# ---------------------------------------------------------------------------
# Fragment source loading
# ---------------------------------------------------------------------------


def load_fragments(fragments_path: Path) -> dict[str, str]:
    """Import ``FRAGMENTS`` from the fragment-source module at *fragments_path*.

    Args:
        fragments_path: Path to the ``hook_prompt_fragments.py`` module file.

    Returns:
        The authoritative fragment-name -> text mapping.

    Raises:
        FileNotFoundError: If *fragments_path* does not exist.
        AttributeError: If the module does not define ``FRAGMENTS``.
    """
    if not fragments_path.is_file():
        raise FileNotFoundError(f"fragment source not found: {fragments_path}")
    spec = importlib.util.spec_from_file_location(
        "hook_prompt_fragments", fragments_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load fragment source: {fragments_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return dict(module.FRAGMENTS)


# ---------------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------------


def compose_prompt(template: str, fragments: dict[str, str]) -> str:
    """Expand all ``{{fragment:NAME}}`` markers in *template* using *fragments*.

    Each marker is replaced verbatim (byte-identical) with its fragment text.
    The result is a self-contained string with no remaining marker substring.

    Args:
        template: The hook prompt template containing fragment markers.
        fragments: The fragment-name -> text mapping to expand from.

    Returns:
        The fully expanded prompt string.

    Raises:
        UnknownFragmentError: If a marker references a name absent from
            *fragments*, or if a malformed ``{{fragment:`` substring remains.
    """

    def _replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in fragments:
            raise UnknownFragmentError(name)
        return fragments[name]

    result = _MARKER_RE.sub(_replace, template)

    # Any residual ``{{fragment:`` token means a malformed/unparsable marker
    # slipped through; treat it as an unknown-fragment error (Req 6.2).
    if _RESIDUAL_TOKEN in result:
        residual = _RESIDUAL_MARKER_RE.search(result)
        bad_name = residual.group(1) if residual else ""
        raise UnknownFragmentError(bad_name)

    return result


def compose_hook(
    hook_id: str,
    fragments: dict[str, str],
    hooks_dir: Path = HOOKS_DIR,
) -> dict:
    """Return the full hook JSON dict with ``then.prompt`` fully expanded.

    The static fields (``name``, ``version``, ``description``, ``when``) are read
    from the current on-disk file so the ``when`` block and other metadata are
    preserved unchanged; only ``then.prompt`` is (re)composed from the template.

    Args:
        hook_id: The gate-hook id (key in ``HOOK_TEMPLATES``).
        fragments: The fragment-name -> text mapping to expand from.
        hooks_dir: Directory containing the ``.kiro.hook`` files.

    Returns:
        The composed hook dict, preserving the original key order.

    Raises:
        KeyError: If *hook_id* has no registered template.
        FileNotFoundError: If the on-disk hook file is missing.
        UnknownFragmentError: Propagated from :func:`compose_prompt`.
    """
    if hook_id not in HOOK_TEMPLATES:
        raise KeyError(f"no template registered for hook '{hook_id}'")

    hook_path = hooks_dir / f"{hook_id}.kiro.hook"
    if not hook_path.is_file():
        raise FileNotFoundError(f"hook file not found: {hook_path}")

    data = json.loads(hook_path.read_text(encoding="utf-8"))

    composed_prompt = compose_prompt(HOOK_TEMPLATES[hook_id], fragments)

    # Rebuild preserving the original key order; only swap then.prompt.
    new_then = {
        key: (composed_prompt if key == "prompt" else value)
        for key, value in data["then"].items()
    }
    new_hook = {
        key: (new_then if key == "then" else value)
        for key, value in data.items()
    }
    return new_hook


# ---------------------------------------------------------------------------
# Byte-identical JSON serialization
#
# The on-disk hook files use 2-space indentation, ensure_ascii=False, and keep
# scalar-only arrays (e.g. ``"toolTypes": ["write"]``) inline. The stdlib
# ``json.dumps(indent=2)`` expands every array onto multiple lines, so a custom
# serializer is required to reproduce the canonical bytes exactly.
# ---------------------------------------------------------------------------


def _is_scalar(value: object) -> bool:
    """Return True if *value* is a JSON scalar (str/int/float/bool/None)."""
    return isinstance(value, (str, int, float, bool)) or value is None


def serialize_hook(hook: dict, indent: int = 2) -> str:
    """Serialize *hook* to JSON matching the on-disk ``.kiro.hook`` formatting.

    Uses 2-space indentation and ``ensure_ascii=False``, but keeps arrays whose
    elements are all scalars inline (matching the canonical files). A trailing
    newline is appended.

    Args:
        hook: The hook dict to serialize.
        indent: Number of spaces per indentation level.

    Returns:
        The serialized JSON text including a trailing newline.
    """

    def _dump(value: object, level: int) -> str:
        pad = " " * (indent * level)
        child_pad = " " * (indent * (level + 1))
        if isinstance(value, dict):
            if not value:
                return "{}"
            items = [
                f"{child_pad}{json.dumps(key, ensure_ascii=False)}: "
                f"{_dump(val, level + 1)}"
                for key, val in value.items()
            ]
            return "{\n" + ",\n".join(items) + "\n" + pad + "}"
        if isinstance(value, list):
            if all(_is_scalar(item) for item in value):
                inline = ", ".join(
                    json.dumps(item, ensure_ascii=False) for item in value
                )
                return "[" + inline + "]"
            items = [f"{child_pad}{_dump(item, level + 1)}" for item in value]
            return "[\n" + ",\n".join(items) + "\n" + pad + "]"
        return json.dumps(value, ensure_ascii=False)

    return _dump(hook, 0) + "\n"


# ---------------------------------------------------------------------------
# Write / Verify
# ---------------------------------------------------------------------------


def write_hook(hook_id: str, content: str, hooks_dir: Path) -> Path:
    """Write composed *content* to ``<hooks_dir>/<hook_id>.kiro.hook``."""
    hooks_dir.mkdir(parents=True, exist_ok=True)
    out_path = hooks_dir / f"{hook_id}.kiro.hook"
    out_path.write_text(content, encoding="utf-8", newline="")
    return out_path


def verify_hook(hook_id: str, content: str, hooks_dir: Path) -> tuple[bool, str]:
    """Compare composed *content* against the on-disk hook bytes.

    Returns:
        ``(matches, message)`` where *matches* is True only if the on-disk file
        exists and its bytes equal *content*.
    """
    hook_path = hooks_dir / f"{hook_id}.kiro.hook"
    if not hook_path.is_file():
        return False, f"hook file missing: {hook_path}"
    existing = hook_path.read_text(encoding="utf-8")
    if existing == content:
        return True, "up to date"
    return False, "composed prompt differs from on-disk file"


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry: ``--write`` (default) | ``--verify``. Returns 0 on success, 1 on error."""
    parser = argparse.ArgumentParser(
        description="Compose Module 3 gate-hook prompts from shared fragments."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write",
        action="store_true",
        default=True,
        help="Compose and write the gate-hook files to disk (default).",
    )
    mode.add_argument(
        "--verify",
        action="store_true",
        help="Compare composed output against on-disk files; exit 1 on drift.",
    )
    parser.add_argument(
        "--hooks-dir",
        type=Path,
        default=HOOKS_DIR,
        help=f"Path to hooks directory (default: {HOOKS_DIR}).",
    )
    parser.add_argument(
        "--fragments",
        type=Path,
        default=FRAGMENTS_PATH,
        help=f"Path to fragment-source module (default: {FRAGMENTS_PATH}).",
    )

    args = parser.parse_args(argv)

    if not args.hooks_dir.is_dir():
        print(f"ERROR: hooks directory not found: {args.hooks_dir}", file=sys.stderr)
        return 1

    try:
        fragments = load_fragments(args.fragments)
    except (FileNotFoundError, ImportError, AttributeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # Compose every gate hook, surfacing unknown-fragment errors with the hook id.
    composed: dict[str, str] = {}
    for hook_id in HOOK_TEMPLATES:
        try:
            hook = compose_hook(hook_id, fragments, hooks_dir=args.hooks_dir)
        except UnknownFragmentError as exc:
            print(
                f"ERROR: unknown fragment '{exc.fragment_name}' referenced by "
                f"hook '{hook_id}'",
                file=sys.stderr,
            )
            return 1
        except (FileNotFoundError, KeyError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        composed[hook_id] = serialize_hook(hook)

    if args.verify:
        drifted: list[str] = []
        for hook_id, content in composed.items():
            matches, message = verify_hook(hook_id, content, args.hooks_dir)
            if not matches:
                print(f"FAIL: {hook_id} — {message}", file=sys.stderr)
                drifted.append(hook_id)
        if drifted:
            print(
                "Composed hook prompts drifted: " + ", ".join(drifted),
                file=sys.stderr,
            )
            return 1
        print(f"All {len(composed)} composed hook prompts are up to date.")
        return 0

    for hook_id, content in composed.items():
        out_path = write_hook(hook_id, content, args.hooks_dir)
        print(f"Composed hook written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
