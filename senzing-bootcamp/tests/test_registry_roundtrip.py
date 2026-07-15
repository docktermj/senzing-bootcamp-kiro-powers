#!/usr/bin/env python3
"""Property test for registry generation round-trip and id consistency (Property 8).

Feature: kiro-1-0-migration, Property 8: Registry generation round-trip and
identifier consistency

Exercises the Kiro 1.0 registry generator (``scripts/sync_hook_registry.py``)
end-to-end as a stable fixed point. For any valid set of ``v1`` hook definitions,
running the generator in ``--write`` mode and then ``--verify`` mode against the
generated output must succeed, the generated lockfile must record each hook id
with its 1.0 trigger (``event_type``), and the set of hook ids parsed from the
generated critical registry and per-module slices must equal the set of shipped
``v1`` hook ids.

The test builds a synthetic set of ``v1`` hook files (varying trigger, matcher,
and action) plus a matching ``hook-categories.yaml`` inside a throwaway temp
directory, runs generation to that temp output, then verifies the generated
output. Because the generator hard-codes a few real-repo paths as module globals
(``HOOKS_DIR`` for the lockfile version read, ``LOCKFILE_PATH`` for the lockfile,
and ``DEPRECATED_REGISTRY_PATHS`` for the orphan set), those are redirected into
the per-example temp directory so no real repo file is ever touched and
``--write`` is safe.

Matchers are drawn to match the trigger's ``hook_renames`` classification: file
triggers (``PostFileSave`` / ``PostFileCreate`` / ``PostFileDelete``) carry a
file-path regex, tool triggers (``PreToolUse`` / ``PostToolUse``) carry a
tool-name regex, and unscoped triggers (``Stop`` / ``UserPromptSubmit`` /
``PostTaskExec``) carry no matcher.

Validates: Requirements 7.1, 7.2, 7.4, 7.5, 14.4
"""

from __future__ import annotations

import contextlib
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st
from hypothesis.strategies import composite

# ---------------------------------------------------------------------------
# Import the scripts under test via sys.path (scripts are not a package).
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import sync_hook_registry as _shr  # noqa: E402
from hook_renames import (  # noqa: E402
    MATCHER_KIND_FILE_PATH,
    MATCHER_KIND_TOOL_NAME,
    VALID_V1_TRIGGERS,
    matcher_kind,
)
from sync_hook_registry import main as _sync_main  # noqa: E402

# ---------------------------------------------------------------------------
# Strategy inputs (local to this file, per the migration test-task convention
# that parallel property tests never share or clobber generators).
# ---------------------------------------------------------------------------

#: The 1.0 triggers, in a deterministic order, so hooks vary across the full set.
_TRIGGERS: tuple[str, ...] = tuple(sorted(VALID_V1_TRIGGERS))

#: Representative file-path matchers (anchored, workspace-relative regexes) for
#: file triggers — the shape the Matcher_Translator emits for ``when.patterns``.
_FILE_MATCHERS: tuple[str, ...] = (
    r"^(?:src/(?:.*/)?[^/]*\.py)$",
    r"^(?:src/load/[^/]*\.[^/]*)$",
    r"^(?:config/[^/]*credentials[^/]*)$",
    r"^(?:\.env[^/]*)$",
    r"^(?:data/transformed/[^/]*\.jsonl)$",
)

#: Representative tool-name matchers for tool triggers — the ``write`` category
#: regex and the shell/command tool name.
_TOOL_MATCHERS: tuple[str, ...] = (
    "fs_write|str_replace|fs_append",
    "execute_bash",
)

#: Numbered module buckets a hook may be assigned to.
_MODULE_NUMBERS: tuple[int, ...] = (1, 2, 3, 5, 6, 8, 11, 12)


@dataclass(frozen=True)
class HookSpec:
    """A synthetic ``v1`` hook plus its category assignment.

    Attributes:
        hook_id: Unique hook id (the ``<id>.json`` filename stem).
        name: The hook ``name`` label.
        trigger: The 1.0 trigger name.
        matcher: The 1.0 matcher regex, or ``None`` for an unscoped trigger.
        action_type: The 1.0 action type (``agent`` or ``command``).
        payload: The verbatim prompt (agent) or command (command) text.
        category: The category assignment — ``("critical",)``, ``("module", n)``,
            ``("any",)``, or ``("unmapped",)`` (omitted from the categories file).
    """

    hook_id: str
    name: str
    trigger: str
    matcher: str | None
    action_type: str
    payload: str
    category: tuple


# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions), local to this file.
# ---------------------------------------------------------------------------


def st_hook_id() -> st.SearchStrategy[str]:
    """Draw a short, filename-safe hook id (lowercase letters/digits/hyphens)."""
    return st.from_regex(r"[a-z][a-z0-9]{1,7}(?:-[a-z0-9]{1,5})?", fullmatch=True)


def st_text() -> st.SearchStrategy[str]:
    """Draw non-empty single-line text with no backticks (safe for id parsing).

    Backticks are excluded so a generated ``name`` / prompt / command can never
    forge a ``- id: `<x>` `` bullet line that the id-consistency parser reads.
    """
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N", "P", "Z"),
            blacklist_characters="`\x00",
        ),
        min_size=1,
        max_size=40,
    )


@composite
def st_v1_hook_set(draw) -> list[HookSpec]:
    """Draw a set of synthetic ``v1`` hooks with unique ids.

    Triggers vary across the full 1.0 set and each hook's matcher is drawn to
    match the trigger's ``matcher_kind`` classification (file-path regex for file
    triggers, tool-name regex for tool triggers, none for unscoped triggers). The
    action is ``agent`` (with a prompt) or ``command`` (with a command), and each
    hook is assigned to a category bucket (critical, a numbered module, the
    ``any`` group, or left unmapped so ``categorize_hooks`` files it under
    ``any``).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A non-empty list of :class:`HookSpec` with unique ``hook_id`` values.
    """
    ids = draw(st.lists(st_hook_id(), min_size=1, max_size=6, unique=True))

    specs: list[HookSpec] = []
    for hook_id in ids:
        trigger = draw(st.sampled_from(_TRIGGERS))
        kind = matcher_kind(trigger)
        if kind == MATCHER_KIND_FILE_PATH:
            matcher = draw(st.sampled_from(_FILE_MATCHERS))
        elif kind == MATCHER_KIND_TOOL_NAME:
            matcher = draw(st.sampled_from(_TOOL_MATCHERS))
        else:
            matcher = None

        action_type = draw(st.sampled_from(("agent", "command")))
        assignment = draw(st.sampled_from(("critical", "module", "any", "unmapped")))
        if assignment == "module":
            category: tuple = ("module", draw(st.sampled_from(_MODULE_NUMBERS)))
        else:
            category = (assignment,)

        specs.append(
            HookSpec(
                hook_id=hook_id,
                name=draw(st_text()),
                trigger=trigger,
                matcher=matcher,
                action_type=action_type,
                payload=draw(st_text()),
                category=category,
            )
        )
    return specs


# ---------------------------------------------------------------------------
# Materializers: write the synthetic v1 corpus + categories file to disk.
# ---------------------------------------------------------------------------


def _hook_wrapper(spec: HookSpec) -> dict:
    """Build the ``{"version": "v1", "hooks": [entry]}`` wrapper for *spec*."""
    action: dict = {"type": spec.action_type}
    if spec.action_type == "command":
        action["command"] = spec.payload
    else:
        action["prompt"] = spec.payload

    entry: dict = {"name": spec.name, "trigger": spec.trigger}
    if spec.matcher is not None:
        entry["matcher"] = spec.matcher
    entry["action"] = action

    return {"version": "v1", "hooks": [entry]}


def _write_hook_files(specs: list[HookSpec], hooks_dir: Path) -> None:
    """Write each spec as ``<hooks_dir>/<id>.json``."""
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for spec in specs:
        (hooks_dir / f"{spec.hook_id}.json").write_text(
            json.dumps(_hook_wrapper(spec), indent=2), encoding="utf-8"
        )


def _write_categories(specs: list[HookSpec], cat_path: Path) -> None:
    """Write a ``hook-categories.yaml`` describing the specs' category buckets.

    Critical hooks go under ``critical:``; numbered-module and ``any`` hooks go
    under ``modules:``; ``unmapped`` hooks are deliberately omitted so
    ``categorize_hooks`` files them under the ``any`` bucket.
    """
    critical = [s.hook_id for s in specs if s.category[0] == "critical"]
    modules: dict[int, list[str]] = {}
    any_ids: list[str] = []
    for spec in specs:
        if spec.category[0] == "module":
            modules.setdefault(spec.category[1], []).append(spec.hook_id)
        elif spec.category[0] == "any":
            any_ids.append(spec.hook_id)

    lines: list[str] = ["critical:"]
    lines.extend(f"  - {hook_id}" for hook_id in critical)
    lines.append("modules:")
    for mod in sorted(modules):
        lines.append(f"  {mod}:")
        lines.extend(f"    - {hook_id}" for hook_id in modules[mod])
    if any_ids:
        lines.append("  any:")
        lines.extend(f"    - {hook_id}" for hook_id in any_ids)

    cat_path.parent.mkdir(parents=True, exist_ok=True)
    cat_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# In-process CLI driver with the module-level real-repo paths redirected.
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def _patched_module_paths(
    hooks_dir: Path, lockfile_path: Path, deprecated_paths: tuple[Path, ...]
):
    """Temporarily redirect the generator's hard-coded real-repo paths.

    ``sync_hook_registry`` hard-codes ``HOOKS_DIR`` (read by ``generate_lockfile``
    for each hook's schema version), ``LOCKFILE_PATH`` (written on ``--write`` and
    read on ``--verify``), and ``DEPRECATED_REGISTRY_PATHS`` (the orphan set) as
    module globals pointing at the real repo. This test drives ``main()`` in
    process, so those are redirected into the per-example temp directory to keep
    the real repo files untouched. Originals are restored on exit.
    """
    saved = (_shr.HOOKS_DIR, _shr.LOCKFILE_PATH, _shr.DEPRECATED_REGISTRY_PATHS)
    _shr.HOOKS_DIR = hooks_dir
    _shr.LOCKFILE_PATH = lockfile_path
    _shr.DEPRECATED_REGISTRY_PATHS = deprecated_paths
    try:
        yield
    finally:
        (_shr.HOOKS_DIR, _shr.LOCKFILE_PATH, _shr.DEPRECATED_REGISTRY_PATHS) = saved


def _run_cli(argv: list[str]) -> int:
    """Invoke ``sync_hook_registry.main()`` in process with *argv*.

    ``main`` reads ``parse_args()`` with no argv parameter, so ``sys.argv`` is
    monkeypatched for the call. ``--write`` returns normally on success (treated
    as ``0``); ``--verify`` raises ``SystemExit`` with ``0`` (all match) or ``1``.
    """
    old_argv = sys.argv
    sys.argv = ["sync_hook_registry.py", *argv]
    try:
        _sync_main()
        return 0
    except SystemExit as exc:
        code = exc.code
        return 0 if code is None else int(code)
    finally:
        sys.argv = old_argv


# ---------------------------------------------------------------------------
# Parsers for the generated lockfile and registry id bullets.
# ---------------------------------------------------------------------------

#: Matches a ``- id: `<hook-id>` `` bullet emitted by ``format_hook_entry``.
_ID_BULLET = re.compile(r"^- id: `([^`]+)`", re.MULTILINE)


def _lockfile_triggers(lockfile_text: str) -> dict[str, str]:
    """Map each hook id in the lockfile to its recorded ``event_type`` (trigger)."""
    triggers: dict[str, str] = {}
    current_id: str | None = None
    for line in lockfile_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- id:"):
            current_id = stripped[len("- id:"):].strip()
        elif stripped.startswith("event_type:") and current_id is not None:
            triggers[current_id] = stripped[len("event_type:"):].strip()
            current_id = None
    return triggers


def _registry_ids(*contents: str) -> set[str]:
    """Return the set of hook ids whose ``- id:`` bullet appears in *contents*."""
    ids: set[str] = set()
    for content in contents:
        ids.update(_ID_BULLET.findall(content))
    return ids


def _generate_and_verify(specs: list[HookSpec]) -> None:
    """Write *specs*, run ``--write`` then ``--verify``, and assert the property.

    Asserts the three facets of Property 8: ``--write`` then ``--verify`` succeeds
    (a stable, idempotent fixed point), the generated lockfile records each id
    with its 1.0 trigger, and the ids in the generated critical registry plus
    per-module slices equal the shipped hook ids.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        hooks_dir = tmp / "hooks"
        steering_dir = tmp / "steering"
        cat_path = hooks_dir / "hook-categories.yaml"
        summary_path = steering_dir / "hook-registry.md"
        critical_path = steering_dir / "hook-registry-critical.md"
        lockfile_path = tmp / "hooks.lock.yaml"
        deprecated_path = steering_dir / "hook-registry-modules.md"

        _write_hook_files(specs, hooks_dir)
        _write_categories(specs, cat_path)

        common = [
            "--hooks-dir", str(hooks_dir),
            "--output", str(summary_path),
            "--output-critical", str(critical_path),
            "--steering-dir", str(steering_dir),
            "--categories", str(cat_path),
        ]
        write_argv = ["--write", *common]
        verify_argv = ["--verify", *common]

        with _patched_module_paths(hooks_dir, lockfile_path, (deprecated_path,)):
            # Write, then verify: generation is a stable fixed point (Req 7.5).
            assert _run_cli(write_argv) == 0, "Initial --write must succeed"
            assert _run_cli(verify_argv) == 0, (
                "Freshly generated registry must verify clean (exit 0)"
            )
            # Idempotence: writing again and re-verifying stays a fixed point.
            assert _run_cli(write_argv) == 0, "Second --write must succeed"
            assert _run_cli(verify_argv) == 0, (
                "Re-generated registry must still verify clean (exit 0)"
            )

            lockfile_text = lockfile_path.read_text(encoding="utf-8")
            critical_text = critical_path.read_text(encoding="utf-8")
            slice_texts = [
                path.read_text(encoding="utf-8")
                for path in sorted(steering_dir.glob("hook-registry-module-*.md"))
            ]

    input_ids = {spec.hook_id for spec in specs}
    expected_triggers = {spec.hook_id: spec.trigger for spec in specs}

    # Lockfile records each id with its 1.0 trigger (Req 7.4).
    lock_triggers = _lockfile_triggers(lockfile_text)
    assert lock_triggers == expected_triggers, (
        "Lockfile must record every hook id with its 1.0 trigger"
    )

    # Registry ids (critical + per-module slices) equal shipped hook ids
    # (Req 7.1, 7.2, 14.4).
    registry_ids = _registry_ids(critical_text, *slice_texts)
    assert registry_ids == input_ids, (
        "Registry ids (critical + module slices) must equal the shipped hook ids"
    )


# ---------------------------------------------------------------------------
# Property + example tests
# ---------------------------------------------------------------------------


class TestRegistryRoundTripAndIdConsistency:
    """Property 8: Registry generation round-trip and identifier consistency.

    Feature: kiro-1-0-migration, Property 8: Registry generation round-trip and
    identifier consistency.

    For any valid set of ``v1`` hook definitions, running the Registry_Generator
    in ``--write`` then ``--verify`` succeeds (generation is a stable fixed
    point), the generated lockfile records each hook id with its 1.0 trigger, and
    the set of ids in the generated registry equals the set of shipped ``v1``
    hook ids.

    Validates: Requirements 7.1, 7.2, 7.4, 7.5, 14.4
    """

    # Feature: kiro-1-0-migration, Property 8: Registry generation round-trip and
    # identifier consistency
    @given(specs=st_v1_hook_set())
    def test_registry_roundtrip_and_id_consistency(self, specs: list[HookSpec]) -> None:
        """A generated registry is a stable fixed point with consistent ids.

        Args:
            specs: A synthetic set of ``v1`` hooks varying trigger, matcher,
                action, and category.
        """
        _generate_and_verify(specs)

    def test_fixed_hook_set_round_trips(self) -> None:
        """A concrete hook set spanning every trigger kind and category round-trips.

        A deterministic anchor for Property 8: file / tool / unscoped triggers,
        both action types, and critical / numbered-module / any / unmapped
        categories all generate a registry that verifies clean, with a lockfile
        recording each 1.0 trigger and registry ids equal to the shipped ids.
        """
        specs = [
            HookSpec(
                hook_id="code-style-check",
                name="to check code style",
                trigger="PostFileSave",
                matcher=r"^(?:src/(?:.*/)?[^/]*\.py)$",
                action_type="agent",
                payload="A source code file was just edited. Check its style.",
                category=("critical",),
            ),
            HookSpec(
                hook_id="write-policy-gate",
                name="to process your response",
                trigger="PreToolUse",
                matcher="fs_write|str_replace|fs_append",
                action_type="agent",
                payload="Write policy gate prompt.",
                category=("critical",),
            ),
            HookSpec(
                hook_id="ask-bootcamper",
                name="to wait for your answer",
                trigger="Stop",
                matcher=None,
                action_type="agent",
                payload="Closing question prompt.",
                category=("critical",),
            ),
            HookSpec(
                hook_id="verify-demo-results",
                name="to verify the demo",
                trigger="PostTaskExec",
                matcher=None,
                action_type="agent",
                payload="Verify the demo results.",
                category=("module", 3),
            ),
            HookSpec(
                hook_id="session-log-events",
                name="to log session events",
                trigger="PostToolUse",
                matcher="fs_write|str_replace|fs_append",
                action_type="command",
                payload="python3 scripts/log_write_event.py",
                category=("any",),
            ),
            HookSpec(
                hook_id="stray-hook",
                name="an unmapped hook",
                trigger="UserPromptSubmit",
                matcher=None,
                action_type="agent",
                payload="Unmapped hook prompt.",
                category=("unmapped",),
            ),
        ]
        _generate_and_verify(specs)
