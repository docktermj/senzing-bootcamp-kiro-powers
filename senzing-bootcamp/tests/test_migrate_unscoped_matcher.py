"""Property test: unscoped-trigger hooks migrate without a matcher.

Feature: kiro-1-0-migration

Validates the unscoped-trigger branch of the migration transform in
``scripts/migrate_hooks.py`` (``migrate_hook``) which consumes
``scripts/hook_matcher.py`` (``translate_scope``): a legacy hook whose ``when``
block carries neither ``patterns`` nor ``toolTypes`` (the ``agentStop``,
``promptSubmit``, and ``postTaskExecution`` triggers, which rename to the 1.0
``Stop``/``UserPromptSubmit``/``PostTaskExec`` triggers) migrates to a V1 hook
that omits the ``matcher`` key entirely.

``translate_scope`` returns ``None`` for such an unscoped ``when`` block, and
``migrate_hook`` reflects that by never adding a ``matcher`` key to the emitted
v1 entry (it also cross-checks that an unscoped 1.0 trigger produced no
matcher). This property asserts the emitted entry has no ``matcher`` key at all,
which is how the 1.0 schema represents an unscoped trigger for this Power.

Validated requirements:

- Requirement 3.4: a legacy hook trigger with neither ``when.patterns`` nor
  ``when.toolTypes`` (for example ``agentStop``, ``promptSubmit``,
  ``postTaskExecution``) omits the Matcher (or sets it to the empty value the
  1.0 schema requires for unscoped triggers).
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

from hook_renames import TRIGGER_RENAMES, UNSCOPED_TRIGGERS
from migrate_hooks import LegacyHook, migrate_hook

# The three legacy triggers that carry no scoping and therefore migrate to an
# unscoped 1.0 trigger with no matcher (Requirement 3.4).
_UNSCOPED_LEGACY_TRIGGERS = ("agentStop", "promptSubmit", "postTaskExecution")

# Sanity guard: every legacy trigger in the strategy renames to a 1.0 trigger
# that the rename tables classify as unscoped. If the rename tables ever change,
# this assertion fails at import time rather than producing a misleading pass.
assert {TRIGGER_RENAMES[t] for t in _UNSCOPED_LEGACY_TRIGGERS} <= UNSCOPED_TRIGGERS

_HOOK_ID_ALPHABET = "abcdefghijklmnopqrstuvwxyz-"


@composite
def st_unscoped_legacy_hook(draw) -> LegacyHook:
    """Draw a legacy hook whose trigger is unscoped (no patterns/toolTypes).

    The drawn hook uses one of the three unscoped legacy triggers, a ``when``
    block that carries neither ``patterns`` nor ``toolTypes``, an arbitrary
    ``name``, and either an ``askAgent`` action (with an arbitrary ``prompt``)
    or a ``runCommand`` action (with an arbitrary ``command`` and, sometimes, a
    legacy ``timeout``). This mirrors the shape of the real unscoped hooks
    (``Stop``/``UserPromptSubmit``/``PostTaskExec``) the migration must handle.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A :class:`migrate_hooks.LegacyHook` with an unscoped ``when`` block.
    """
    hook_id = draw(
        st.text(alphabet=_HOOK_ID_ALPHABET, min_size=1, max_size=12)
    ).strip("-")
    # Fall back to a valid stem if stripping emptied the id.
    hook_id = hook_id or "hook"

    trigger = draw(st.sampled_from(_UNSCOPED_LEGACY_TRIGGERS))
    name = draw(st.text(min_size=1, max_size=40))

    # Both legacy action variants are valid for an unscoped trigger.
    if draw(st.sampled_from(("askAgent", "runCommand"))) == "askAgent":
        then: dict = {"type": "askAgent", "prompt": draw(st.text(min_size=1, max_size=80))}
    else:
        then = {"type": "runCommand", "command": draw(st.text(min_size=1, max_size=80))}
        # A legacy command timeout is a hook-level field, never a matcher, so it
        # must not affect matcher omission; include it sometimes to prove that.
        if draw(st.booleans()):
            then["timeout"] = draw(st.integers(min_value=1, max_value=120))

    # An unscoped ``when`` block: only the trigger type, no patterns/toolTypes.
    data = {"name": name, "when": {"type": trigger}, "then": then}
    return LegacyHook(
        hook_id=hook_id, path=Path(f"{hook_id}.kiro.hook"), data=data
    )


class TestUnscopedTriggerMatcherOmission:
    """Property 4: Unscoped triggers omit the matcher.

    Validates: Requirements 3.4
    """

    # Feature: kiro-1-0-migration, Property 4: Unscoped triggers omit the matcher
    @given(legacy=st_unscoped_legacy_hook())
    def test_unscoped_trigger_omits_matcher(self, legacy: LegacyHook) -> None:
        """Migrating an unscoped-trigger hook emits a v1 entry with no matcher.

        Args:
            legacy: A legacy hook whose ``when`` block carries neither
                ``patterns`` nor ``toolTypes``.
        """
        result = migrate_hook(legacy)

        # The translated scope is None for an unscoped trigger.
        assert result.matcher is None

        # The migrated 1.0 trigger is one of the unscoped triggers.
        assert result.trigger in UNSCOPED_TRIGGERS

        # The emitted v1 entry omits the matcher key entirely.
        entry = result.wrapper["hooks"][0]
        assert "matcher" not in entry
