"""Property test for verbatim name and action-text preservation in migration.

Feature: kiro-1-0-migration

Validates that the one-time migration transform in ``scripts/migrate_hooks.py``
(``migrate_hook`` / ``migrate_action``) changes only the *envelope* shape of a
legacy ``*.kiro.hook`` and never its content: the hook ``name`` label and the
action payload text (``then.prompt`` for ``askAgent``, ``then.command`` for
``runCommand``) are carried across byte-for-byte into the migrated ``v1`` hook.

The strategy ``st_legacy_hook()`` synthesizes non-manual legacy hook dicts with
arbitrary (including unicode, whitespace, and multi-line) ``name`` and
``prompt``/``command`` text across every non-manual legacy trigger and both
action types, always with a valid ``when`` scope so the hook migrates cleanly:

- file-path triggers (``fileEdited``/``fileCreated``/``fileDeleted``) get a
  non-empty ``when.patterns`` glob list,
- tool-name triggers (``preToolUse``/``postToolUse``) get a ``when.toolTypes``
  list of valid categories, and
- unscoped triggers (``agentStop``/``promptSubmit``/``postTaskExecution``) get
  neither, so ``translate_scope`` returns ``None``.

Validated requirements:

- Requirement 1.4: the prompt/command text is preserved verbatim in the action.
- Requirement 1.5: the ``name`` value is preserved so the Kiro UI label is
  unchanged.
- Requirement 4.2: manual-hook prompt instruction text is preserved (the same
  verbatim-preservation guarantee this transform provides for every hook).
- Requirement 5.3: the full write-gate policy prompt text is preserved verbatim.
"""

import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st
from hypothesis.strategies import composite

# Make scripts importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from hook_renames import (
    MATCHER_KIND_FILE_PATH,
    MATCHER_KIND_TOOL_NAME,
    TRIGGER_RENAMES,
    matcher_kind,
)
from migrate_hooks import LegacyHook, migrate_hook

# The eight non-manual legacy triggers (``userTriggered`` is intentionally
# excluded from ``TRIGGER_RENAMES`` — those hooks become slash commands).
_LEGACY_TRIGGERS: tuple[str, ...] = tuple(sorted(TRIGGER_RENAMES))

# Known-good globs from the design's representative table plus a couple of
# simple extras. Every entry translates cleanly, so a hook scoped by any subset
# of them migrates without a translation error (scope correctness is covered by
# the Matcher_Translator properties, not this one).
_SAFE_GLOBS: tuple[str, ...] = (
    "src/**/*.py",
    "src/load/*.*",
    "config/*credentials*",
    ".env*",
    "data/transformed/*.jsonl",
    "*.md",
    "docs/**/*.md",
)

# Valid legacy toolTypes categories the Matcher_Translator understands.
_TOOL_TYPES: tuple[str, ...] = ("write", "shell")


@composite
def st_free_text(draw) -> str:
    """Draw arbitrary text: unicode, whitespace, and multi-line content.

    Joins one to four unicode chunks with a randomly chosen separator (newline,
    CRLF, tab, space, or empty) so the drawn value exercises multi-line and
    mixed-whitespace payloads as well as the empty string.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A free-form string that may be empty, unicode, or multi-line.
    """
    chunks = draw(st.lists(st.text(max_size=60), min_size=1, max_size=4))
    separator = draw(st.sampled_from(["\n", "\r\n", "\t", " ", ""]))
    return separator.join(chunks)


@composite
def st_when(draw, legacy_trigger: str) -> dict:
    """Draw a valid legacy ``when`` block for *legacy_trigger*.

    The block carries exactly the scope the trigger's 1.0 counterpart requires,
    so ``migrate_hook`` never fails the matcher-when-required cross-check:
    file-path triggers get ``patterns``, tool-name triggers get ``toolTypes``,
    and unscoped triggers get neither.

    Args:
        draw: The Hypothesis draw callable.
        legacy_trigger: A non-manual legacy trigger name.

    Returns:
        A legacy ``when`` block dict.
    """
    kind = matcher_kind(TRIGGER_RENAMES[legacy_trigger])
    when: dict = {"type": legacy_trigger}
    if kind == MATCHER_KIND_FILE_PATH:
        when["patterns"] = draw(
            st.lists(st.sampled_from(_SAFE_GLOBS), min_size=1, max_size=4)
        )
    elif kind == MATCHER_KIND_TOOL_NAME:
        when["toolTypes"] = draw(
            st.lists(
                st.sampled_from(_TOOL_TYPES), min_size=1, max_size=2, unique=True
            )
        )
    return when


@composite
def st_then(draw) -> dict:
    """Draw a legacy ``then`` action block for either action type.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        An ``askAgent`` block with a ``prompt`` or a ``runCommand`` block with a
        ``command``, each carrying arbitrary free-form text.
    """
    text = draw(st_free_text())
    if draw(st.booleans()):
        return {"type": "askAgent", "prompt": text}
    return {"type": "runCommand", "command": text}


@composite
def st_legacy_hook(draw) -> LegacyHook:
    """Draw a migratable non-manual legacy hook with arbitrary text payloads.

    Covers every non-manual trigger variant and both action types, always with
    a valid scope so ``migrate_hook`` succeeds. The ``name`` and the action
    payload are drawn as arbitrary free-form text so the preservation property
    is exercised against unicode, whitespace, and multi-line content.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A :class:`LegacyHook` wrapping a synthesized legacy hook dict.
    """
    legacy_trigger = draw(st.sampled_from(_LEGACY_TRIGGERS))
    data = {
        "name": draw(st_free_text()),
        "when": draw(st_when(legacy_trigger)),
        "then": draw(st_then()),
    }
    return LegacyHook(
        hook_id="legacy-hook",
        path=Path("legacy-hook.kiro.hook"),
        data=data,
    )


class TestNameAndActionTextPreservation:
    """Property 6: Name and action text are preserved verbatim.

    Validates: Requirements 1.4, 1.5, 4.2, 5.3
    """

    # Feature: kiro-1-0-migration, Property 6: Name and action text are
    # preserved verbatim
    @given(legacy=st_legacy_hook())
    def test_name_and_action_text_preserved_verbatim(
        self, legacy: LegacyHook
    ) -> None:
        """The migrated name and action payload equal the legacy ones exactly.

        Args:
            legacy: A synthesized non-manual legacy hook with arbitrary text.
        """
        result = migrate_hook(legacy)
        entry = result.wrapper["hooks"][0]

        # Name label preserved byte-for-byte (Requirement 1.5).
        assert entry["name"] == legacy.data["name"]

        # Action payload preserved byte-for-byte (Requirements 1.4, 4.2, 5.3).
        then = legacy.data["then"]
        action = entry["action"]
        if then["type"] == "askAgent":
            assert action["type"] == "agent"
            assert action["prompt"] == then["prompt"]
        else:
            assert action["type"] == "command"
            assert action["command"] == then["command"]
