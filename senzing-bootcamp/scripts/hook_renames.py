#!/usr/bin/env python3
"""Single-source trigger and action rename tables for the Kiro 1.0 migration.

This module is the authoritative, machine-readable record of how legacy
``*.kiro.hook`` triggers and actions map onto the Kiro 1.0 ``v1`` hook schema.
Both the one-time migration transform (``migrate_hooks.py``) and the hook
validator accept-list (``validate_power.py`` / ``test_hooks.py``) import these
tables so the rename has exactly one definition and cannot drift between the
code that *produces* v1 hooks and the code that *validates* them.

The tables cover the eight automatic legacy triggers. The manual
``userTriggered`` trigger is intentionally absent: Kiro 1.0 removes it, so its
three hooks become manual-invocation slash-command steering files rather than
v1 hooks (see the Manual-Hook Conversion design section).

Derived, for the validator's benefit:

- ``VALID_V1_TRIGGERS`` — the set of accepted 1.0 Trigger names.
- ``VALID_V1_ACTION_TYPES`` — the set of accepted 1.0 Action types
  (``agent``, ``command``).
- ``LEGACY_TRIGGERS`` / ``LEGACY_ACTION_TYPES`` — the legacy names the migration
  accepts as input.
- ``FILE_PATH_TRIGGERS`` / ``TOOL_NAME_TRIGGERS`` / ``UNSCOPED_TRIGGERS`` — the
  matcher-requirement classification of every 1.0 Trigger (file-path Matcher,
  tool-name Matcher, or no Matcher).

Only Python standard-library features are used; importing this module yields the
tables directly with no parsing layer.

Usage:
    import hook_renames as renames

    renames.TRIGGER_RENAMES["fileEdited"]         # -> "PostFileSave"
    renames.ACTION_RENAMES["askAgent"].v1_type    # -> "agent"
    "PostFileSave" in renames.VALID_V1_TRIGGERS   # -> True
    renames.matcher_kind("PreToolUse")            # -> "tool-name"
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Trigger rename table (Requirements 2.1-2.8)
# ---------------------------------------------------------------------------

#: Legacy trigger name -> Kiro 1.0 Trigger name.
#:
#: ``userTriggered`` is deliberately excluded — 1.0 has no manual trigger, so
#: those hooks are converted to slash-command steering files instead.
TRIGGER_RENAMES: dict[str, str] = {
    "fileEdited": "PostFileSave",
    "fileCreated": "PostFileCreate",
    "fileDeleted": "PostFileDelete",
    "agentStop": "Stop",
    "promptSubmit": "UserPromptSubmit",
    "postTaskExecution": "PostTaskExec",
    "preToolUse": "PreToolUse",
    "postToolUse": "PostToolUse",
}


# ---------------------------------------------------------------------------
# Action rename table (Requirements 2.9-2.10)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActionRename:
    """How one legacy action type maps onto a 1.0 Action object.

    Attributes:
        legacy_type: The legacy ``then.type`` value (``askAgent``/``runCommand``).
        v1_type: The 1.0 ``action.type`` value (``agent``/``command``).
        payload_field: The key carrying the verbatim payload text — identical in
            the legacy ``then`` block and the 1.0 ``action`` object (``prompt``
            for agent actions, ``command`` for command actions).
    """

    legacy_type: str
    v1_type: str
    payload_field: str


#: Legacy action type -> its 1.0 rename (target type + payload field).
#:
#: ``askAgent`` + ``prompt``   -> ``{"type": "agent", "prompt": <original>}``
#: ``runCommand`` + ``command`` -> ``{"type": "command", "command": <original>}``
ACTION_RENAMES: dict[str, ActionRename] = {
    "askAgent": ActionRename("askAgent", "agent", "prompt"),
    "runCommand": ActionRename("runCommand", "command", "command"),
}


# ---------------------------------------------------------------------------
# Derived accept-lists (for the Hook_Validator)
# ---------------------------------------------------------------------------

#: Legacy trigger names accepted as migration input (excludes ``userTriggered``).
LEGACY_TRIGGERS: frozenset[str] = frozenset(TRIGGER_RENAMES)

#: Legacy action types accepted as migration input.
LEGACY_ACTION_TYPES: frozenset[str] = frozenset(ACTION_RENAMES)

#: The set of valid 1.0 Trigger names (the right column of the rename table).
VALID_V1_TRIGGERS: frozenset[str] = frozenset(TRIGGER_RENAMES.values())

#: The set of valid 1.0 Action types.
VALID_V1_ACTION_TYPES: frozenset[str] = frozenset(
    rename.v1_type for rename in ACTION_RENAMES.values()
)


# ---------------------------------------------------------------------------
# Matcher-requirement classification of the 1.0 triggers
# ---------------------------------------------------------------------------

#: 1.0 triggers that require a file-path Matcher (translated from when.patterns).
FILE_PATH_TRIGGERS: frozenset[str] = frozenset(
    {"PostFileSave", "PostFileCreate", "PostFileDelete"}
)

#: 1.0 triggers that require a tool-name Matcher (translated from when.toolTypes).
TOOL_NAME_TRIGGERS: frozenset[str] = frozenset({"PreToolUse", "PostToolUse"})

#: 1.0 triggers that carry no Matcher (unscoped).
UNSCOPED_TRIGGERS: frozenset[str] = frozenset(
    {"Stop", "UserPromptSubmit", "PostTaskExec"}
)

#: Matcher-kind labels returned by :func:`matcher_kind`.
MATCHER_KIND_FILE_PATH: str = "file-path"
MATCHER_KIND_TOOL_NAME: str = "tool-name"
MATCHER_KIND_UNSCOPED: str = "unscoped"


def matcher_kind(trigger: str) -> str:
    """Classify a 1.0 Trigger by the kind of Matcher it requires.

    Args:
        trigger: A 1.0 Trigger name (a member of ``VALID_V1_TRIGGERS``).

    Returns:
        ``"file-path"`` if the trigger requires a file-path Matcher,
        ``"tool-name"`` if it requires a tool-name Matcher, or ``"unscoped"``
        if it carries no Matcher.

    Raises:
        KeyError: If ``trigger`` is not a recognized 1.0 Trigger name.
    """
    if trigger in FILE_PATH_TRIGGERS:
        return MATCHER_KIND_FILE_PATH
    if trigger in TOOL_NAME_TRIGGERS:
        return MATCHER_KIND_TOOL_NAME
    if trigger in UNSCOPED_TRIGGERS:
        return MATCHER_KIND_UNSCOPED
    raise KeyError(f"Unknown 1.0 trigger: {trigger!r}")
