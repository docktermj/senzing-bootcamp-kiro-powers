"""Property-based tests for the leading-question-continuity pass-through extension.

Outcome B of the leading-question-continuity feature extends the
``write-policy-gate`` hook's INTERNAL-FILE PASS-THROUGH set with two additional
routine power-managed config files — ``config/data_sources.yaml`` and
``config/visualization_tracker.json`` — so they pass silently on the first
attempt without triggering the intercept/retry cycle.

These tests drive the live hook prompt through the gate decision model in
``tests/gate_decision_model.py`` (which reads the prompt from the on-disk hook
file on every call), so they exercise the *actual* prompt text rather than a
copy.
"""

from __future__ import annotations

import string

from hypothesis import assume, example, given, settings
from hypothesis import strategies as st

from gate_decision_model import (
    PASS_SILENT,
    WriteOperation,
    gate,
    is_bug_condition,
    is_power_managed_internal_file,
    load_gate_prompt,
)

# ---------------------------------------------------------------------------
# The two new exact pass-through paths under test (Requirements 3.1, 3.2).
# ---------------------------------------------------------------------------

NEW_PASS_THROUGH_PATHS: tuple[str, ...] = (
    "config/data_sources.yaml",
    "config/visualization_tracker.json",
)

# Safe alphabet for keys/values — avoids SQL keywords and Senzing indicators so
# generated content never trips a NOT-guard.
_SAFE_TEXT = st.text(
    alphabet=string.ascii_lowercase + string.digits + " _-.",
    min_size=1,
    max_size=20,
)


def _st_clean_yaml() -> st.SearchStrategy[str]:
    """NOT-guard-clean YAML content (no Senzing SQL, no secrets/URLs)."""
    return st.builds(
        lambda name, count: (
            "source: %s\nrecords: %d\nenabled: true\n" % (name, count)
        ),
        name=st.sampled_from(["customers", "vendors", "watchlist", "people"]),
        count=st.integers(min_value=0, max_value=100000),
    )


def _st_clean_json() -> st.SearchStrategy[str]:
    """NOT-guard-clean JSON content (no Senzing SQL, no secrets/URLs)."""
    return st.builds(
        lambda nodes, status: (
            '{"nodes": %d, "status": "%s", "rendered": true}' % (nodes, status)
        ),
        nodes=st.integers(min_value=0, max_value=5000),
        status=st.sampled_from(["ready", "pending", "rendered", "stale"]),
    )


@st.composite
def st_new_pass_through_write(draw) -> WriteOperation:
    """Generate a NOT-guard-clean write to one of the two new exact paths.

    ``config/data_sources.yaml`` gets clean YAML content and
    ``config/visualization_tracker.json`` gets clean JSON content. The tool is
    varied across the write tools the gate inspects.
    """
    tool = draw(st.sampled_from(["fs_write", "fs_append", "str_replace"]))
    path = draw(st.sampled_from(NEW_PASS_THROUGH_PATHS))
    if path.endswith(".yaml"):
        content = draw(_st_clean_yaml())
    else:
        content = draw(_st_clean_json())
    return WriteOperation(path=path, content=content, tool=tool)


# Feature: leading-question-continuity, Property 3: New routine config files
# pass through silently on first attempt.
class TestNewConfigFilesPassThroughSilently:
    """Property 3 — new routine config files pass through silently.

    **Validates: Requirements 3.1, 3.2, 3.4**

    For any write whose target path is exactly ``config/data_sources.yaml`` or
    exactly ``config/visualization_tracker.json``, with NOT-guard-clean
    content, the gate decision is ``PASS_SILENT`` with ``intercepted = False``
    (zero output tokens, no intercept/retry), and the literal path appears in
    the INTERNAL-FILE PASS-THROUGH enumeration of ``then.prompt``.
    """

    @given(op=st_new_pass_through_write())
    @settings(max_examples=200)
    @example(
        op=WriteOperation(
            "config/data_sources.yaml", "source: customers\nrecords: 10\n"
        )
    )
    @example(
        op=WriteOperation(
            "config/visualization_tracker.json", '{"nodes": 5, "status": "ready"}'
        )
    )
    def test_new_config_file_passes_silently_without_intercept(
        self, op: WriteOperation
    ):
        """New exact-path config writes pass silently with no interception.

        **Validates: Requirements 3.1, 3.2, 3.4**
        """
        # Sanity: the generated write is genuinely a bug-condition (clean,
        # power-managed internal) input for one of the two new exact paths.
        assert is_bug_condition(op), (
            f"generator produced a non-bug-condition write: {op.path}"
        )

        prompt = load_gate_prompt()
        decision = gate(op, prompt)

        # Requirements 3.1 / 3.2: silent first-attempt pass-through.
        assert decision.outcome == PASS_SILENT, (
            f"Property 3 FAILED: write to '{op.path}' did not PASS_SILENT "
            f"(got {decision.outcome}, category={decision.category})."
        )
        # Requirement 3.4: zero output tokens — modeled as no interception
        # (no "Rejected"/retry pair, no corrective message).
        assert decision.intercepted is False, (
            f"Property 3 FAILED: write to '{op.path}' was intercepted; it must "
            f"pass through silently with zero output tokens "
            f"(tool={op.tool}, content={op.content!r})."
        )

        # The literal path must appear in the pass-through enumeration of the
        # live prompt (otherwise the silent pass-through is not anchored in the
        # actual hook text).
        assert op.path in prompt, (
            f"Property 3 FAILED: literal path '{op.path}' is absent from the "
            f"INTERNAL-FILE PASS-THROUGH enumeration in then.prompt."
        )


# ---------------------------------------------------------------------------
# The pre-existing Pass_Through_Set entries under test (Requirement 3.3).
# ---------------------------------------------------------------------------

EXISTING_EXACT_PASS_THROUGH_PATHS: tuple[str, ...] = (
    "config/bootcamp_progress.json",
    "config/bootcamp_preferences.yaml",
)

# Member-id alphabet matching the gate's regexes ([A-Za-z0-9_-]+).
_st_member_id = st.text(
    alphabet=string.ascii_letters + string.digits + "_-",
    min_size=1,
    max_size=15,
)

# Module token for docs/progress/MODULE_<token>_COMPLETE.md — the gate matches
# `[^/]*` for the token, so any non-slash text (including empty) is valid. Keep
# it NOT-guard-clean (no SQL/Senzing indicators) by construction.
_st_module_token = st.text(
    alphabet=string.ascii_uppercase + string.digits + "_",
    min_size=0,
    max_size=12,
)


def _st_clean_markdown() -> st.SearchStrategy[str]:
    """NOT-guard-clean Markdown recap content (no Senzing SQL, no secrets)."""
    return st.builds(
        lambda module, items: (
            "# %s recap\n\n- completed %d steps\n- status: done\n"
            % (module, items)
        ),
        module=st.sampled_from(["module one", "module two", "module three"]),
        items=st.integers(min_value=0, max_value=50),
    )


@st.composite
def st_existing_pass_through_write(draw) -> WriteOperation:
    """Generate a NOT-guard-clean write to a pre-existing pass-through path.

    Covers the full pre-existing Pass_Through_Set: the two exact paths, the
    member-scoped ``config/progress_{id}.json`` and
    ``config/preferences_{id}.yaml`` regex instances, and the power-written
    ``docs/progress/MODULE_*_COMPLETE.md`` session/recap logs. Content is
    generated to match each path's file type and never trips a NOT-guard.
    """
    kind = draw(
        st.sampled_from(
            ["exact_json", "exact_yaml", "progress", "preferences", "module_log"]
        )
    )
    tool = draw(st.sampled_from(["fs_write", "fs_append", "str_replace"]))

    if kind == "exact_json":
        path = "config/bootcamp_progress.json"
        content = draw(_st_clean_json())
    elif kind == "exact_yaml":
        path = "config/bootcamp_preferences.yaml"
        content = draw(_st_clean_yaml())
    elif kind == "progress":
        path = f"config/progress_{draw(_st_member_id)}.json"
        content = draw(_st_clean_json())
    elif kind == "preferences":
        path = f"config/preferences_{draw(_st_member_id)}.yaml"
        content = draw(_st_clean_yaml())
    else:  # module_log
        path = f"docs/progress/MODULE_{draw(_st_module_token)}_COMPLETE.md"
        content = draw(_st_clean_markdown())

    return WriteOperation(path=path, content=content, tool=tool)


# Feature: leading-question-continuity, Property 4: Existing pass-through
# entries still pass through silently (preservation).
class TestExistingPassThroughEntriesStillPassSilently:
    """Property 4 — pre-existing pass-through entries still pass silently.

    **Validates: Requirements 3.3**

    For any path already in the Pass_Through_Set before this change — the two
    exact paths (``config/bootcamp_progress.json``,
    ``config/bootcamp_preferences.yaml``), any member-scoped
    ``config/progress_{id}.json`` / ``config/preferences_{id}.yaml`` instance,
    and any power-written ``docs/progress/MODULE_*_COMPLETE.md`` session/recap
    log — with NOT-guard-clean content, the gate decision remains
    ``PASS_SILENT`` with ``intercepted = False``. The pass-through extension
    must not regress any previously silent path.
    """

    @given(op=st_existing_pass_through_write())
    @settings(max_examples=200)
    @example(
        op=WriteOperation(
            "config/bootcamp_progress.json", '{"nodes": 1, "status": "ready"}'
        )
    )
    @example(
        op=WriteOperation(
            "config/bootcamp_preferences.yaml", "source: people\nrecords: 3\n"
        )
    )
    @example(
        op=WriteOperation(
            "config/progress_alice.json", '{"nodes": 0, "status": "pending"}'
        )
    )
    @example(
        op=WriteOperation(
            "config/preferences_bob-1.yaml", "source: vendors\nrecords: 7\n"
        )
    )
    @example(
        op=WriteOperation(
            "docs/progress/MODULE_3_COMPLETE.md", "# module three recap\n\n- done\n"
        )
    )
    def test_existing_pass_through_path_still_passes_silently(
        self, op: WriteOperation
    ):
        """Pre-existing pass-through writes remain silent and un-intercepted.

        **Validates: Requirements 3.3**
        """
        # Sanity: the generated write is a genuine bug-condition (clean,
        # power-managed internal) input for a pre-existing pass-through path.
        assert is_bug_condition(op), (
            f"generator produced a non-bug-condition write: {op.path}"
        )

        prompt = load_gate_prompt()
        decision = gate(op, prompt)

        # Requirement 3.3: previously-silent paths still PASS_SILENT.
        assert decision.outcome == PASS_SILENT, (
            f"Property 4 FAILED: existing pass-through write to '{op.path}' did "
            f"not PASS_SILENT (got {decision.outcome}, "
            f"category={decision.category})."
        )
        # ...and are not intercepted (no "Rejected"/retry pair, zero tokens).
        assert decision.intercepted is False, (
            f"Property 4 FAILED: existing pass-through write to '{op.path}' was "
            f"intercepted; it must still pass through silently "
            f"(tool={op.tool}, content={op.content!r})."
        )


# ---------------------------------------------------------------------------
# Exact-match base paths from which near-miss mutations are derived
# (Requirements 4.1, 4.2, 4.3). These are genuine Pass_Through_Set entries;
# any mutation of them must NOT inherit the silent pass-through.
# ---------------------------------------------------------------------------

EXACT_PASS_THROUGH_BASES: tuple[str, ...] = (
    "config/data_sources.yaml",
    "config/visualization_tracker.json",
    "config/bootcamp_progress.json",
    "config/bootcamp_preferences.yaml",
)

# Alternate extensions per real extension — each differs from the original so
# the regex/exact match no longer applies.
_ALT_EXTENSIONS: dict[str, tuple[str, ...]] = {
    ".yaml": (".yml", ".yaml.txt", ".json", ".conf"),
    ".json": (".jsonc", ".json5", ".yaml", ".txt"),
}

# Suffixes appended after the full filename (backup/temp artifacts).
_NEAR_MISS_SUFFIXES: tuple[str, ...] = (".bak", ".tmp", ".orig", "~", ".swp")

# Extra parent directories prepended to the path.
_EXTRA_PARENTS: tuple[str, ...] = ("sub/", "backup/", "old/", "a/b/")


def _change_extension(path: str) -> str:
    """Return ``path`` with its extension swapped for a different one."""
    base, _, ext = path.rpartition(".")
    dot_ext = "." + ext
    alternates = _ALT_EXTENSIONS.get(dot_ext, (".txt",))
    return base + alternates[0]


@st.composite
def st_near_miss_path(draw) -> str:
    """Generate an adversarial near-miss of an exact Pass_Through_Set entry.

    The mutation kinds mirror the design's Property 5 examples:

    * ``changed_extension`` — e.g. ``config/data_sources.yml``
    * ``added_suffix`` — e.g. ``config/data_sources.yaml.bak``
    * ``extra_parent`` — e.g. ``sub/config/data_sources.yaml``
    * ``case_change`` — e.g. ``config/DATA_SOURCES.yaml``

    The result is guaranteed (via :func:`hypothesis.assume`) to differ from the
    original and to not be recognized as a power-managed internal file, so it is
    a true near-miss rather than an accidental match.
    """
    base = draw(st.sampled_from(EXACT_PASS_THROUGH_BASES))
    kind = draw(
        st.sampled_from(
            ["changed_extension", "added_suffix", "extra_parent", "case_change"]
        )
    )

    if kind == "changed_extension":
        path = _change_extension(base)
    elif kind == "added_suffix":
        path = base + draw(st.sampled_from(_NEAR_MISS_SUFFIXES))
    elif kind == "extra_parent":
        path = draw(st.sampled_from(_EXTRA_PARENTS)) + base
    else:  # case_change — flip the basename to upper case
        directory, _, filename = base.rpartition("/")
        path = f"{directory}/{filename.upper()}"

    # A near-miss must genuinely differ from the original and must NOT be a
    # recognized pass-through path (exact set or any regex instance).
    assume(path != base)
    assume(not is_power_managed_internal_file(path))
    return path


def _st_near_miss_content() -> st.SearchStrategy[str]:
    """NOT-guard-clean content (no Senzing SQL, no secrets/URLs).

    Content is deliberately benign so the gate's outcome is driven solely by
    path membership, not by a security-check violation — isolating the
    exact-match behavior under test.
    """
    return st.one_of(_st_clean_yaml(), _st_clean_json())


@st.composite
def st_near_miss_write(draw) -> WriteOperation:
    """Generate a NOT-guard-clean write to a near-miss (non-member) path."""
    return WriteOperation(
        path=draw(st_near_miss_path()),
        content=draw(_st_near_miss_content()),
        tool=draw(st.sampled_from(["fs_write", "fs_append", "str_replace"])),
    )


# Feature: leading-question-continuity, Property 5: Pass-through membership is
# exact-match only.
class TestPassThroughMembershipIsExactMatchOnly:
    """Property 5 — pass-through membership is exact-match only.

    **Validates: Requirements 4.1, 4.2, 4.3**

    For any path that is not exactly equal to a Pass_Through_Set entry —
    including adversarial near-misses such as a changed extension
    (``config/data_sources.yml``), an added suffix
    (``config/data_sources.yaml.bak``), an extra parent directory
    (``sub/config/data_sources.yaml``), or a case change
    (``config/DATA_SOURCES.yaml``) — the gate does NOT grant the silent
    pass-through. Because the pass-through clause is the only code path that
    yields ``intercepted = False``, a near-miss is necessarily held
    (``intercepted = True``) and routed to the four security checks.
    """

    @given(op=st_near_miss_write())
    @settings(max_examples=200)
    @example(
        op=WriteOperation("config/data_sources.yml", "source: customers\nrecords: 1\n")
    )
    @example(
        op=WriteOperation(
            "config/data_sources.yaml.bak", "source: vendors\nrecords: 2\n"
        )
    )
    @example(
        op=WriteOperation(
            "sub/config/data_sources.yaml", "source: people\nrecords: 3\n"
        )
    )
    @example(
        op=WriteOperation("config/DATA_SOURCES.yaml", "source: watchlist\nrecords: 4\n")
    )
    @example(
        op=WriteOperation(
            "config/visualization_tracker.jsonc", '{"nodes": 1, "status": "ready"}'
        )
    )
    def test_near_miss_path_is_not_granted_silent_pass_through(
        self, op: WriteOperation
    ):
        """Near-miss paths are not pass-through and route to the checks.

        **Validates: Requirements 4.1, 4.2, 4.3**
        """
        # Requirement 4.3: a path that resembles but does not exactly match a
        # Pass_Through_Set entry is not recognized as a pass-through internal
        # file (no exact-set membership, no regex instance match).
        assert is_power_managed_internal_file(op.path) is False, (
            f"Property 5 FAILED: near-miss path '{op.path}' was wrongly "
            f"recognized as a power-managed internal pass-through file."
        )
        # ...so it is not a bug-condition (silent pass-through) input either.
        assert is_bug_condition(op) is False, (
            f"Property 5 FAILED: near-miss path '{op.path}' was wrongly "
            f"classified as a silent-pass-through bug-condition write."
        )

        prompt = load_gate_prompt()
        decision = gate(op, prompt)

        # Requirements 4.1 / 4.2: the silent pass-through (the only path that
        # produces intercepted=False) is NOT granted; the write is held and
        # evaluated against the four security checks.
        assert decision.intercepted is True, (
            f"Property 5 FAILED: near-miss write to '{op.path}' was granted the "
            f"silent pass-through (intercepted=False); only exact Pass_Through_Set "
            f"entries may pass through silently "
            f"(tool={op.tool}, content={op.content!r})."
        )
