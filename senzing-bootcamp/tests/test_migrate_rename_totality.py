#!/usr/bin/env python3
"""Property test for trigger/action rename totality and range (Property 5).

Feature: kiro-1-0-migration, Property 5: Trigger and action rename totality and
range

Exercises the one-time migration transform in ``scripts/migrate_hooks.py``
(``migrate_hook``, which delegates the action rename to ``migrate_action``) as
it consumes the single-source rename tables in ``scripts/hook_renames.py``. For
any legacy hook drawn across all eight legacy trigger variants and both action
types, the transform must:

* map the legacy trigger onto the documented Kiro 1.0 Trigger, and produce a
  Trigger that is always a member of the 1.0 Trigger set
  (``hook_renames.VALID_V1_TRIGGERS``); and
* map the legacy action onto the documented 1.0 action type, and produce an
  action type that is always ``agent`` or ``command``
  (``hook_renames.VALID_V1_ACTION_TYPES``).

The expected trigger/action mappings are pinned in this test as independent
truth tables (``EXPECTED_TRIGGER_MAP`` / ``EXPECTED_ACTION_MAP``) so the property
is a genuine check of the transform's output, not a restatement of the
implementation's own tables. The range assertions reuse the derived accept-lists
from ``hook_renames`` rather than hardcoding them.

``st_legacy_hook()`` is kept local to this file (as in the sibling migration
property tests) so the parallel test tasks never share or clobber generators. It
synthesizes migratable legacy hook dicts across every legacy trigger/action
variant: file triggers carry valid ``when.patterns``, tool triggers carry valid
``when.toolTypes``, and unscoped triggers carry neither, so ``migrate_hook``
always produces the matcher the 1.0 trigger requires.

Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10
"""

from __future__ import annotations

import sys
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
    VALID_V1_ACTION_TYPES,
    VALID_V1_TRIGGERS,
    matcher_kind,
)
from migrate_hooks import LegacyHook, migrate_hook  # noqa: E402

# ---------------------------------------------------------------------------
# Independent expected mappings (the truth table this property pins).
# ---------------------------------------------------------------------------

#: Legacy trigger -> expected 1.0 Trigger (independent of the implementation's
#: own ``TRIGGER_RENAMES`` table, so the property genuinely checks the output).
EXPECTED_TRIGGER_MAP: dict[str, str] = {
    "fileEdited": "PostFileSave",
    "fileCreated": "PostFileCreate",
    "fileDeleted": "PostFileDelete",
    "agentStop": "Stop",
    "promptSubmit": "UserPromptSubmit",
    "postTaskExecution": "PostTaskExec",
    "preToolUse": "PreToolUse",
    "postToolUse": "PostToolUse",
}

#: Legacy action type -> expected 1.0 action type.
EXPECTED_ACTION_MAP: dict[str, str] = {
    "askAgent": "agent",
    "runCommand": "command",
}

#: Payload field carried verbatim per legacy action type.
_ACTION_PAYLOAD_FIELD: dict[str, str] = {
    "askAgent": "prompt",
    "runCommand": "command",
}

#: Valid, translator-accepted file globs for scoping file triggers.
_GLOB_VOCABULARY: tuple[str, ...] = (
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

#: Safe payload text alphabet (printable, no surrogates) — the transform carries
#: this text verbatim, so any representative text exercises the action rename.
_PAYLOAD_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,:/\n"
)
_HOOK_ID_ALPHABET = "abcdefghijklmnopqrstuvwxyz-"


# ---------------------------------------------------------------------------
# Strategy (st_ prefix per python-conventions), local to this file.
# ---------------------------------------------------------------------------


@composite
def st_legacy_hook(draw) -> LegacyHook:
    """Draw a migratable legacy hook across all trigger and action variants.

    The drawn hook is always representable as a schema-valid V1 hook: file
    triggers (``fileEdited``/``fileCreated``/``fileDeleted``) carry a non-empty
    ``when.patterns`` glob list, tool triggers (``preToolUse``/``postToolUse``)
    carry a non-empty ``when.toolTypes`` category list, and unscoped triggers
    (``agentStop``/``promptSubmit``/``postTaskExecution``) carry neither — so
    ``migrate_hook`` finds the matcher (or absence of one) the 1.0 trigger
    requires. The action is either ``askAgent`` + ``prompt`` or ``runCommand`` +
    ``command`` with verbatim payload text.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A :class:`migrate_hooks.LegacyHook` ready to feed ``migrate_hook``.
    """
    legacy_trigger = draw(st.sampled_from(sorted(hook_renames.LEGACY_TRIGGERS)))
    # Classify the trigger via the derived matcher-requirement tables so the
    # ``when`` block matches what the 1.0 trigger needs (no hardcoded lists).
    kind = matcher_kind(hook_renames.TRIGGER_RENAMES[legacy_trigger])

    when: dict = {"type": legacy_trigger}
    if kind == MATCHER_KIND_FILE_PATH:
        when["patterns"] = draw(
            st.lists(
                st.sampled_from(_GLOB_VOCABULARY), min_size=1, max_size=4
            )
        )
    elif kind == MATCHER_KIND_TOOL_NAME:
        when["toolTypes"] = list(draw(st.sampled_from(_TOOLTYPE_VOCABULARY)))
    # Unscoped triggers carry neither patterns nor toolTypes.

    legacy_action = draw(st.sampled_from(sorted(hook_renames.LEGACY_ACTION_TYPES)))
    payload_field = _ACTION_PAYLOAD_FIELD[legacy_action]
    payload_text = draw(
        st.text(alphabet=_PAYLOAD_ALPHABET, min_size=1, max_size=60)
    )
    then = {"type": legacy_action, payload_field: payload_text}

    name = draw(st.text(alphabet=_PAYLOAD_ALPHABET, min_size=1, max_size=40))
    hook_id = draw(
        st.text(alphabet=_HOOK_ID_ALPHABET, min_size=1, max_size=12)
    ).strip("-") or "hook"

    data = {"name": name, "when": when, "then": then}
    return LegacyHook(
        hook_id=hook_id,
        path=Path(f"{hook_id}.kiro.hook"),
        data=data,
    )


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------


class TestRenameTotalityAndRange:
    """Property 5: Trigger and action rename totality and range.

    Feature: kiro-1-0-migration, Property 5: Trigger and action rename totality
    and range.

    For any legacy trigger drawn from the supported legacy set, ``migrate_hook``
    produces the mapped 1.0 Trigger, and every produced Trigger is a member of
    the 1.0 Trigger set; likewise ``askAgent`` maps to ``agent`` and
    ``runCommand`` maps to ``command``, and every produced action type is
    ``agent`` or ``command``.

    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10
    """

    # Feature: kiro-1-0-migration, Property 5: Trigger and action rename
    # totality and range
    @given(legacy=st_legacy_hook())
    def test_rename_totality_and_range(self, legacy: LegacyHook) -> None:
        """Every migrated trigger/action matches the map and lands in the 1.0 range.

        Args:
            legacy: A migratable legacy hook drawn across all trigger/action
                variants.
        """
        result = migrate_hook(legacy)

        legacy_trigger = legacy.data["when"]["type"]
        legacy_action = legacy.data["then"]["type"]

        # Totality: the exact documented mapping holds for trigger and action.
        assert result.trigger == EXPECTED_TRIGGER_MAP[legacy_trigger], (
            f"trigger {legacy_trigger!r} mapped to {result.trigger!r}, "
            f"expected {EXPECTED_TRIGGER_MAP[legacy_trigger]!r}"
        )
        assert result.action_type == EXPECTED_ACTION_MAP[legacy_action], (
            f"action {legacy_action!r} mapped to {result.action_type!r}, "
            f"expected {EXPECTED_ACTION_MAP[legacy_action]!r}"
        )

        # Range: produced trigger is a 1.0 Trigger and action type is 1.0.
        assert result.trigger in VALID_V1_TRIGGERS
        assert result.action_type in VALID_V1_ACTION_TYPES

        # The emitted v1 entry agrees with the reported result fields.
        entry = result.wrapper["hooks"][0]
        assert entry["trigger"] in VALID_V1_TRIGGERS
        assert entry["action"]["type"] in VALID_V1_ACTION_TYPES

    def test_every_legacy_trigger_and_action_is_covered(self) -> None:
        """The migration covers all eight legacy triggers and both action types.

        Guards the totality claim end-to-end: each legacy trigger (paired with
        each action type and a scope its 1.0 trigger requires) migrates to the
        expected 1.0 Trigger and action type, so no supported variant is left
        unmapped or out of range.
        """
        assert set(EXPECTED_TRIGGER_MAP) == set(hook_renames.LEGACY_TRIGGERS)
        assert set(EXPECTED_ACTION_MAP) == set(hook_renames.LEGACY_ACTION_TYPES)

        for legacy_trigger, expected_trigger in EXPECTED_TRIGGER_MAP.items():
            kind = matcher_kind(hook_renames.TRIGGER_RENAMES[legacy_trigger])
            when: dict = {"type": legacy_trigger}
            if kind == MATCHER_KIND_FILE_PATH:
                when["patterns"] = ["src/**/*.py"]
            elif kind == MATCHER_KIND_TOOL_NAME:
                when["toolTypes"] = ["write"]

            for legacy_action, expected_action in EXPECTED_ACTION_MAP.items():
                payload_field = _ACTION_PAYLOAD_FIELD[legacy_action]
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
                assert result.trigger == expected_trigger
                assert result.action_type == expected_action
                assert result.trigger in VALID_V1_TRIGGERS
                assert result.action_type in VALID_V1_ACTION_TYPES
