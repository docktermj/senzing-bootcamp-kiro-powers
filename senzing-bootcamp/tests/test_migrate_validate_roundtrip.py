#!/usr/bin/env python3
"""Property test for the migrate -> validate round trip (Property 7).

Feature: kiro-1-0-migration, Property 7: Migration produces schema-valid V1
hooks (migrate -> validate round trip)

Wires together the two halves of the migration end-to-end: the one-time
transform in ``scripts/migrate_hooks.py`` (``migrate_hook``) that emits a
``{"version": "v1", "hooks": [...]}`` wrapper, and the updated validator in
``scripts/test_hooks.py`` (``validate_hook`` / ``_validate_v1_entry``) that
enforces the Kiro 1.0 hook schema against a shipped ``<id>.json`` file.

For any non-manual legacy hook, migrating it and writing the serialized wrapper
to a temporary ``.json`` file must produce a file the validator accepts: the
file wraps ``{"version": "v1", "hooks": [...]}``, each entry carries
``name``/``trigger``/``action``, a ``matcher`` is present when the trigger
requires scoping (and absent when it does not), and any present matcher compiles
as a regular expression. Round-tripping through a written file (rather than only
inspecting the in-memory wrapper) exercises the same discovery/parse path the
validator uses on the committed hook files, most faithfully covering Req 6.1.

``st_migratable_legacy_hook()`` is kept local to this file (as in the sibling
migration property tests ``test_migrate_rename_totality.py`` /
``test_migrate_preservation.py``) so the parallel test tasks never share or
clobber generators. It synthesizes migratable non-manual legacy hooks across
every trigger/action variant: file triggers carry valid ``when.patterns`` globs,
tool triggers carry valid ``when.toolTypes`` categories, and unscoped triggers
carry neither, so ``migrate_hook`` always produces (or omits) the matcher the
1.0 trigger requires. ``name`` and the action payload are drawn as non-blank
text (with surrounding/embedded whitespace and unicode) so the validator's
non-empty-string checks are satisfied while still exercising verbatim carry-over
through JSON serialization.

Validates: Requirements 1.2, 1.3, 6.1, 6.2, 6.5
"""

from __future__ import annotations

import sys
import tempfile
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

import hook_renames  # noqa: E402
from hook_renames import (  # noqa: E402
    MATCHER_KIND_FILE_PATH,
    MATCHER_KIND_TOOL_NAME,
    MATCHER_KIND_UNSCOPED,
    matcher_kind,
)
from migrate_hooks import LegacyHook, migrate_hook  # noqa: E402
from test_hooks import validate_hook  # noqa: E402

# ---------------------------------------------------------------------------
# Strategy inputs (local to this file).
# ---------------------------------------------------------------------------

#: Valid, translator-accepted file globs for scoping file triggers. Every entry
#: translates cleanly, so a hook scoped by any subset migrates without a
#: translation error (glob correctness is covered by the Matcher_Translator
#: properties, not this round-trip).
_SAFE_GLOBS: tuple[str, ...] = (
    "src/**/*.py",
    "src/load/*.*",
    "config/*credentials*",
    ".env*",
    "data/transformed/*.jsonl",
    "**/*.java",
    "docs/**/*.md",
)

#: Valid, translator-accepted toolTypes lists for scoping tool triggers.
_TOOLTYPE_VOCABULARY: tuple[tuple[str, ...], ...] = (
    ("write",),
    ("shell",),
    ("write", "shell"),
)

#: Payload field carried verbatim per legacy action type.
_ACTION_PAYLOAD_FIELD: dict[str, str] = {
    "askAgent": "prompt",
    "runCommand": "command",
}

#: Visible (non-whitespace) characters, including JSON-sensitive characters
#: (quote, backslash) and a few unicode letters, so serialization escaping is
#: exercised. Drawing at least one of these guarantees a non-blank string.
_VISIBLE_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    ".,:;/(){}[]!?-_\"'\\éñ中"
)

#: Full text alphabet: visible characters plus whitespace/newline/tab so the
#: drawn text also exercises multi-line and mixed-whitespace payloads.
_TEXT_ALPHABET = _VISIBLE_CHARS + " \t\n"

_HOOK_ID_ALPHABET = "abcdefghijklmnopqrstuvwxyz-"


# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions), local to this file.
# ---------------------------------------------------------------------------


@composite
def st_nonblank_text(draw) -> str:
    """Draw text that is non-empty after ``.strip()``.

    Anchors a single guaranteed-visible character between optional
    whitespace/unicode/multi-line runs, so the value satisfies the validator's
    non-empty-string checks for ``name`` and the action payload while still
    exercising surrounding whitespace and JSON-sensitive characters.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A string whose ``.strip()`` is non-empty.
    """
    lead = draw(st.text(alphabet=_TEXT_ALPHABET, max_size=30))
    anchor = draw(st.sampled_from(_VISIBLE_CHARS))
    trail = draw(st.text(alphabet=_TEXT_ALPHABET, max_size=30))
    return lead + anchor + trail


@composite
def st_migratable_legacy_hook(draw) -> LegacyHook:
    """Draw a migratable non-manual legacy hook across all trigger/action variants.

    The drawn hook is always representable as a schema-valid V1 hook: file
    triggers (``fileEdited``/``fileCreated``/``fileDeleted``) carry a non-empty
    ``when.patterns`` glob list, tool triggers (``preToolUse``/``postToolUse``)
    carry a non-empty ``when.toolTypes`` category list, and unscoped triggers
    (``agentStop``/``promptSubmit``/``postTaskExecution``) carry neither — so
    ``migrate_hook`` produces (or omits) the matcher the 1.0 trigger requires.
    The action is either ``askAgent`` + ``prompt`` or ``runCommand`` +
    ``command`` with non-blank payload text; a ``runCommand`` hook sometimes
    carries a legacy ``timeout`` (preserved as a hook-level integer).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A :class:`migrate_hooks.LegacyHook` ready to feed ``migrate_hook``.
    """
    legacy_trigger = draw(st.sampled_from(sorted(hook_renames.LEGACY_TRIGGERS)))
    kind = matcher_kind(hook_renames.TRIGGER_RENAMES[legacy_trigger])

    when: dict = {"type": legacy_trigger}
    if kind == MATCHER_KIND_FILE_PATH:
        when["patterns"] = draw(
            st.lists(st.sampled_from(_SAFE_GLOBS), min_size=1, max_size=4)
        )
    elif kind == MATCHER_KIND_TOOL_NAME:
        when["toolTypes"] = list(draw(st.sampled_from(_TOOLTYPE_VOCABULARY)))
    # Unscoped triggers carry neither patterns nor toolTypes.

    legacy_action = draw(st.sampled_from(sorted(hook_renames.LEGACY_ACTION_TYPES)))
    payload_field = _ACTION_PAYLOAD_FIELD[legacy_action]
    then: dict = {"type": legacy_action, payload_field: draw(st_nonblank_text())}
    if legacy_action == "runCommand" and draw(st.booleans()):
        then["timeout"] = draw(st.integers(min_value=1, max_value=120))

    hook_id = (
        draw(st.text(alphabet=_HOOK_ID_ALPHABET, min_size=1, max_size=12)).strip("-")
        or "hook"
    )
    data = {"name": draw(st_nonblank_text()), "when": when, "then": then}
    return LegacyHook(
        hook_id=hook_id,
        path=Path(f"{hook_id}.kiro.hook"),
        data=data,
    )


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------


class TestMigrateValidateRoundTrip:
    """Property 7: Migration produces schema-valid V1 hooks (round trip).

    Feature: kiro-1-0-migration, Property 7: Migration produces schema-valid V1
    hooks (migrate -> validate round trip).

    For any non-manual legacy hook, the migrated V1_Hook is accepted by the
    Hook_Validator: the file wraps ``{"version": "v1", "hooks": [...]}``, each
    entry has ``name``, ``trigger``, and ``action``, a ``matcher`` is present
    when the trigger requires it, and any present Matcher compiles as a valid
    regular expression.

    Validates: Requirements 1.2, 1.3, 6.1, 6.2, 6.5
    """

    # Feature: kiro-1-0-migration, Property 7: Migration produces schema-valid
    # V1 hooks (migrate -> validate round trip)
    @given(legacy=st_migratable_legacy_hook())
    def test_migrated_hook_passes_validator(self, legacy: LegacyHook) -> None:
        """A migrated hook, written to a ``.json`` file, passes the validator.

        Args:
            legacy: A migratable non-manual legacy hook drawn across all
                trigger/action variants.
        """
        result = migrate_hook(legacy)

        # Wrapper shape (Req 1.2, 6.1) — asserted directly for a clear failure
        # message before the validator round trip.
        wrapper = result.wrapper
        assert wrapper["version"] == "v1"
        assert isinstance(wrapper["hooks"], list) and len(wrapper["hooks"]) == 1

        # Required fields and matcher-when-required (Req 1.3, 6.2).
        entry = wrapper["hooks"][0]
        assert {"name", "trigger", "action"} <= set(entry)
        kind = matcher_kind(entry["trigger"])
        if kind == MATCHER_KIND_UNSCOPED:
            assert "matcher" not in entry
        else:
            assert isinstance(entry.get("matcher"), str) and entry["matcher"]

        # Round trip through a written file, then validate (Req 6.1, 6.5). A
        # fresh temp dir per example keeps generated worlds from overlapping.
        with tempfile.TemporaryDirectory() as tmp:
            hook_path = Path(tmp) / f"{result.hook_id}.json"
            hook_path.write_text(result.serialized, encoding="utf-8", newline="")
            validation = validate_hook(hook_path)

        assert validation.passed, (
            f"validator rejected migrated hook {result.hook_id!r} "
            f"(trigger={entry['trigger']!r}): {validation.failures}"
        )
        assert validation.failures == []

    def test_all_trigger_action_variants_round_trip(self) -> None:
        """Every legacy trigger x action variant migrates to a validator-clean file.

        Guards Property 7 end-to-end over the full finite variant space: each of
        the eight legacy triggers (scoped as its 1.0 trigger requires) paired
        with each action type migrates to a ``.json`` file the validator
        accepts, so no supported variant produces a schema-invalid V1 hook.
        """
        for legacy_trigger in sorted(hook_renames.LEGACY_TRIGGERS):
            kind = matcher_kind(hook_renames.TRIGGER_RENAMES[legacy_trigger])
            when: dict = {"type": legacy_trigger}
            if kind == MATCHER_KIND_FILE_PATH:
                when["patterns"] = ["src/**/*.py"]
            elif kind == MATCHER_KIND_TOOL_NAME:
                when["toolTypes"] = ["write"]

            for legacy_action, payload_field in _ACTION_PAYLOAD_FIELD.items():
                legacy = LegacyHook(
                    hook_id=f"{legacy_trigger}-{legacy_action}",
                    path=Path("x.kiro.hook"),
                    data={
                        "name": "example hook",
                        "when": dict(when),
                        "then": {"type": legacy_action, payload_field: "text"},
                    },
                )
                result = migrate_hook(legacy)
                with tempfile.TemporaryDirectory() as tmp:
                    hook_path = Path(tmp) / f"{result.hook_id}.json"
                    hook_path.write_text(
                        result.serialized, encoding="utf-8", newline=""
                    )
                    validation = validate_hook(hook_path)
                assert validation.passed, (
                    f"{legacy_trigger}+{legacy_action} rejected: "
                    f"{validation.failures}"
                )
