"""Property 3 tests for the write-gate-momentum-preservation feature.

Outcome B extends the ``write-policy-gate`` INTERNAL-FILE PASS-THROUGH set with
two routine power-managed config files. The pass-through is exact-match only: a
broadened set must never silently pass an unintended path. This module guards
that exact-match contract against drift by driving the *live* hook prompt
through the pure ``gate_decision_model.gate`` decision model with adversarial
near-miss mutations of the exact entries.

A near-miss path that is NOT an exact pass-through entry is NOT granted the
internal-file silent pass-through (``intercepted=False``). Instead the
``preToolUse`` hook holds it (``intercepted=True``) and routes it to the four
security checks. A clean near-miss may still ultimately pass via the FAST PATH
GATE — but only with ``intercepted=True`` (the hook held it, the pass-through
did not grant it). The key assertion is therefore ``intercepted is True``.

This file is DEDICATED to Property 3 only. Sibling property modules cover the
other passthrough properties to avoid collisions.

**Validates: Requirements 4.6**
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import assume, example, given, settings
from hypothesis import strategies as st

# Tests are not packaged; make the sibling test modules importable.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from gate_decision_model import (  # noqa: E402
    WriteOperation,
    contains_senzing_sql,
    gate,
    is_power_managed_internal_file,
    load_gate_prompt,
)

# ---------------------------------------------------------------------------
# Exact pass-through entries to mutate into adversarial near-misses.
# ---------------------------------------------------------------------------

# The exact-match members of the INTERNAL-FILE PASS-THROUGH set (the two
# pre-existing entries plus the two Outcome B additions). Property 3 mutates
# each into a path that is NOT an exact entry and asserts the silent
# pass-through is declined.
_EXACT_ENTRIES: tuple[str, ...] = (
    "config/bootcamp_progress.json",
    "config/bootcamp_preferences.yaml",
    "config/data_sources.yaml",
    "config/visualization_tracker.json",
)

# The write tools the gate inspects.
_WRITE_TOOLS: tuple[str, str, str] = ("fs_write", "fs_append", "str_replace")

# Replacement extensions for the changed-extension mutation.
_NEAR_MISS_EXTENSIONS: tuple[str, ...] = (
    ".yml",
    ".json5",
    ".jsonc",
    ".txt",
    ".cfg",
    ".ini",
    ".toml",
)

# Suffixes appended after the original (full) filename.
_NEAR_MISS_SUFFIXES: tuple[str, ...] = (".bak", ".tmp", ".orig", ".old", ".save", "~")

# Extra parent directory segments prepended to the path.
_NEAR_MISS_PARENTS: tuple[str, ...] = ("sub", "nested", "a", "deep/dir", "team")


def _strip_extension(path: str) -> str:
    """Return ``path`` with its final extension removed.

    Args:
        path: The original path.

    Returns:
        The path without its trailing ``.<ext>`` component.
    """
    return path.rsplit(".", 1)[0]


def _change_extension(path: str, new_ext: str) -> str:
    """Mutate ``path`` by replacing its extension with ``new_ext``.

    Args:
        path: The exact-entry path being mutated.
        new_ext: The replacement extension (leading dot included).

    Returns:
        The path with a changed extension (e.g. ``config/data_sources.yml``).
    """
    return _strip_extension(path) + new_ext


def _add_suffix(path: str, suffix: str) -> str:
    """Mutate ``path`` by appending ``suffix`` after the full filename.

    Args:
        path: The exact-entry path being mutated.
        suffix: The suffix to append (e.g. ``.bak``).

    Returns:
        The path with an added suffix (e.g. ``config/data_sources.yaml.bak``).
    """
    return path + suffix


def _add_parent(path: str, parent: str) -> str:
    """Mutate ``path`` by prepending an extra parent directory segment.

    Args:
        path: The exact-entry path being mutated.
        parent: The parent directory segment to prepend.

    Returns:
        The path with an extra parent dir (e.g. ``sub/config/data_sources.yaml``).
    """
    return f"{parent}/{path}"


def _change_case(path: str) -> str:
    """Mutate ``path`` by upper-casing its filename component.

    Path membership is case-sensitive, so upper-casing the filename yields a
    distinct, non-member path (e.g. ``config/DATA_SOURCES.yaml``).

    Args:
        path: The exact-entry path being mutated.

    Returns:
        The path with an upper-cased filename component.
    """
    head, _, tail = path.rpartition("/")
    stem, dot, ext = tail.partition(".")
    mutated_tail = stem.upper() + dot + ext
    return f"{head}/{mutated_tail}" if head else mutated_tail


def st_near_miss_path() -> st.SearchStrategy[str]:
    """Strategy producing adversarial near-miss mutations of the exact entries.

    Covers the four near-miss kinds called out by Property 3: a changed
    extension, an added suffix, an extra parent directory, and a case change.
    Every produced path is guaranteed to differ from its source entry; an
    ``assume`` in the test additionally rejects the rare mutation that happens
    to land on any pass-through member.

    Returns:
        A strategy of near-miss path strings.
    """
    base = st.sampled_from(_EXACT_ENTRIES)
    changed_ext = st.builds(
        _change_extension, base, st.sampled_from(_NEAR_MISS_EXTENSIONS)
    )
    added_suffix = st.builds(_add_suffix, base, st.sampled_from(_NEAR_MISS_SUFFIXES))
    extra_parent = st.builds(_add_parent, base, st.sampled_from(_NEAR_MISS_PARENTS))
    case_change = st.builds(_change_case, base)
    return st.one_of(changed_ext, added_suffix, extra_parent, case_change)


def st_write_tool() -> st.SearchStrategy[str]:
    """Strategy over the three write tools (fs_write, fs_append, str_replace)."""
    return st.sampled_from(_WRITE_TOOLS)


def st_clean_content() -> st.SearchStrategy[str]:
    """Strategy generating NOT-guard-clean write content.

    Content is filtered so it never trips the Senzing SQL guard. This keeps the
    test focused on membership: any hold (``intercepted=True``) is due to the
    near-miss path not being an exact pass-through member, not to a content
    NOT-guard firing.

    Returns:
        A strategy of content strings that contain no Senzing SQL.
    """
    return st.text(max_size=400).filter(lambda c: not contains_senzing_sql(c))


# ===========================================================================
# Property 3: Pass-through membership is exact-match only
# ===========================================================================
# Feature: write-gate-momentum-preservation, Property 3: For any path that is
# not exactly equal to a pass-through set entry — including adversarial
# near-misses such as a changed extension (config/data_sources.yml), an added
# suffix (config/data_sources.yaml.bak), an extra parent directory
# (sub/config/data_sources.yaml), or a case change (config/DATA_SOURCES.yaml) —
# the gate does NOT grant the silent pass-through; the write is held
# (intercepted=True) and routed to the four security checks.

class TestPassThroughMembershipIsExactMatchOnly:
    """Near-miss paths never receive the internal-file silent pass-through;
    they are held and routed to the four security checks.

    **Validates: Requirements 4.6**
    """

    @given(
        path=st_near_miss_path(),
        tool=st_write_tool(),
        content=st_clean_content(),
    )
    @settings(max_examples=200)
    @example(path="config/data_sources.yml", tool="fs_write", content="sources: []")
    @example(
        path="config/data_sources.yaml.bak", tool="fs_write", content="sources: []"
    )
    @example(
        path="sub/config/data_sources.yaml", tool="fs_write", content="sources: []"
    )
    @example(path="config/DATA_SOURCES.yaml", tool="fs_write", content="sources: []")
    def test_near_miss_paths_are_not_granted_silent_passthrough(
        self, path: str, tool: str, content: str
    ):
        """A near-miss path is held (intercepted) rather than passed silently.

        Drives the live hook prompt through the gate decision model and asserts
        the write was NOT granted the internal-file silent pass-through: the
        hook held it (``intercepted=True``) and routed it to the four checks.

        **Validates: Requirements 4.6**
        """
        # A near-miss must not coincide with any pass-through member (exact or
        # member-scoped regex). Reject the rare mutation that lands on one.
        assume(not is_power_managed_internal_file(path))

        prompt = load_gate_prompt()
        op = WriteOperation(path=path, content=content, tool=tool)
        decision = gate(op, prompt)

        assert decision.intercepted is True, (
            f"near-miss path {path!r} via {tool} was granted the silent "
            f"internal-file pass-through (intercepted=False); pass-through "
            f"membership must be exact-match only"
        )
