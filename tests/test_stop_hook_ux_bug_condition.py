"""Bug-condition EXPLORATION tests for the stop-hook-ux bugfix.

These tests encode the EXPECTED (fixed) behavior from design Property 1
("Single Stop Hook Visibility and Silent Turn") and are deliberately AUTHORED
TO FAIL on the current (unfixed) code. Their failure CONFIRMS the two defect
disjuncts of the bug condition exist:

    isBugCondition(X) :=
        countVisibleStopHooks(X.hookRegistry) > 1          # Defect 1 (dual UI labels)
        OR (ask_output.allPhasesNoOutput                   # Defect 2 (narration leak)
            AND ask_output.responseText != ".")

The fixed system must satisfy Property 1: exactly ONE "waiting for your answer"
Stop hook surfaces in the UI, and the ``ask-bootcamper`` OUTPUT RULES preamble
carries explicit negative examples so a no-output turn emits only ".".

Scoped-PBT approach — the property is scoped to the two concrete failing cases:

    1. Dual visibility: the ``agentstop_order`` registry surfaces more than one
       user-facing Stop label (``ask-bootcamper`` "to wait for your answer" AND
       ``module-recap-append`` "to append module recap on completion"), and the
       standalone ``module-recap-append.json`` file still exists.
    2. Narration leak: the ``ask-bootcamper`` OUTPUT RULES preamble lacks the
       explicit "✗" negative examples that prohibit narrating internal hook
       evaluation on a no-output turn.

**DO NOT "fix" these tests or the code when they fail here** — the failure is
the SUCCESS case for an exploration test. After the fix (recap folded into
``ask-bootcamper`` Phase 0, ``module-recap-append.json`` deleted, and the
OUTPUT RULES strengthened with negative examples) these same tests will pass.

Feature: stop-hook-ux

**Validates: Requirements 2.1, 2.3** (the fixed behavior these encode)
Explores defect Requirements 1.1, 1.2, 1.3.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths (resolved relative to this test file: repo root -> senzing-bootcamp/hooks)
# ---------------------------------------------------------------------------

_REPO_ROOT: Path = Path(__file__).resolve().parent.parent
HOOKS_DIR: Path = _REPO_ROOT / "senzing-bootcamp" / "hooks"
CATEGORIES_PATH: Path = HOOKS_DIR / "hook-categories.yaml"
ASK_BOOTCAMPER_PATH: Path = HOOKS_DIR / "ask-bootcamper.json"
MODULE_RECAP_APPEND_PATH: Path = HOOKS_DIR / "module-recap-append.json"

# A Stop hook surfaces a user-facing "waiting"/"appending" UI label when its
# ``name`` begins with one of these prefixes. Only ``ask-bootcamper`` should
# retain such a label after the fix.
SURFACING_LABEL_PREFIXES: tuple[str, ...] = ("to wait", "to append")

# Minimum number of "✗" negative-example lines the strengthened OUTPUT RULES
# preamble must carry (design task 3.2 lists four).
MIN_NEGATIVE_EXAMPLES: int = 3

# Distinctive fragments of the narration sentences the fixed OUTPUT RULES must
# explicitly prohibit as negative examples. Each fragment is absent from the
# unfixed prompt (so this domain fails today) and present after the fix.
KNOWN_NARRATION_LEAKS: tuple[str, ...] = (
    "My last message ends with",
    "silenced because a question is already pending",
    "responding with a period",
    "All conditions checked",
)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _load_hook_entry(path: Path) -> dict:
    """Load and return the single v1 hook entry (``hooks[0]``) from a hook file.

    Args:
        path: Path to the ``<id>.json`` hook file.

    Returns:
        The single v1 hook entry dict (keys ``name``, ``trigger``, ``action``).
    """
    return json.loads(path.read_text(encoding="utf-8"))["hooks"][0]


def parse_agentstop_order_ids(path: Path | None = None) -> list[str]:
    """Parse the ordered ``id`` values from the ``agentstop_order`` YAML block.

    Minimal stdlib scanner (no PyYAML, consistent with the repository's
    hook-config parsing convention): finds the top-level ``agentstop_order:``
    key, then collects each ``- id: <value>`` entry until the next top-level
    key. Surrounding quotes on the id value are stripped.

    Args:
        path: Path to the YAML file. Defaults to ``CATEGORIES_PATH``.

    Returns:
        List of hook ids in declared order.
    """
    if path is None:
        path = CATEGORIES_PATH

    ids: list[str] = []
    in_block = False
    id_pattern = re.compile(r"^\s*-\s*id:\s*(.+?)\s*$")

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())
        if indent == 0 and stripped.endswith(":"):
            in_block = stripped[:-1].strip() == "agentstop_order"
            continue

        if in_block:
            match = id_pattern.match(line)
            if match:
                ids.append(match.group(1).strip().strip('"').strip("'"))

    return ids


def hook_name(hook_id: str) -> str | None:
    """Return the ``name`` (user-facing label) of a Stop hook by id.

    Args:
        hook_id: The hook id (filename without the ``.json`` suffix).

    Returns:
        The hook's ``name`` string, or ``None`` when the hook file does not
        exist (e.g. after ``module-recap-append.json`` is deleted by the fix).
    """
    path = HOOKS_DIR / f"{hook_id}.json"
    if not path.exists():
        return None
    return _load_hook_entry(path).get("name")


def is_visible_waiting_label(hook_id: str) -> bool:
    """Return True if the hook surfaces a user-facing waiting/appending label.

    A Stop hook is user-facing when its ``name`` begins with one of
    :data:`SURFACING_LABEL_PREFIXES` ("to wait" / "to append"). A missing hook
    file surfaces nothing.

    Args:
        hook_id: The hook id to inspect.

    Returns:
        True when the hook's ``name`` starts with a surfacing prefix.
    """
    name = hook_name(hook_id)
    if name is None:
        return False
    return any(name.startswith(prefix) for prefix in SURFACING_LABEL_PREFIXES)


def visible_stop_hook_ids() -> list[str]:
    """Return the ``agentstop_order`` ids that surface a user-facing label.

    Returns:
        List of hook ids whose ``name`` starts with a surfacing prefix, i.e.
        ``countVisibleStopHooks`` of the design's bug condition.
    """
    return [hid for hid in parse_agentstop_order_ids() if is_visible_waiting_label(hid)]


def ask_bootcamper_prompt() -> str:
    """Return the ``action.prompt`` text of the ``ask-bootcamper`` Stop hook."""
    return _load_hook_entry(ASK_BOOTCAMPER_PATH)["action"]["prompt"]


def count_negative_example_lines(prompt: str) -> int:
    """Count OUTPUT RULES negative-example lines (lines beginning with "✗").

    Args:
        prompt: The full ``ask-bootcamper`` prompt text.

    Returns:
        Number of lines whose first non-whitespace character is "✗".
    """
    return sum(1 for line in prompt.splitlines() if line.strip().startswith("✗"))


# ---------------------------------------------------------------------------
# Module-level data (computed once from the real files)
# ---------------------------------------------------------------------------

AGENTSTOP_ORDER_IDS: list[str] = parse_agentstop_order_ids()


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


@st.composite
def st_agentstop_id_pair(draw) -> tuple[str, str]:
    """Draw two distinct hook ids from the ``agentstop_order`` registry.

    Scopes the dual-visibility disjunct: for any pair of distinct Stop hooks,
    at most one may surface a user-facing waiting label after the fix.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(id_a, id_b)`` tuple of two distinct ``agentstop_order`` ids.
    """
    first = draw(st.sampled_from(AGENTSTOP_ORDER_IDS))
    second = draw(st.sampled_from([hid for hid in AGENTSTOP_ORDER_IDS if hid != first]))
    return (first, second)


def st_narration_leak() -> st.SearchStrategy[str]:
    """Strategy sampling over the narration fragments the OUTPUT RULES must ban."""
    return st.sampled_from(KNOWN_NARRATION_LEAKS)


# ---------------------------------------------------------------------------
# Defect 1 — Dual Stop hook visibility
# ---------------------------------------------------------------------------


class TestDualStopHookVisibility:
    """Exactly one Stop hook may surface a user-facing waiting label.

    **Validates: Requirements 2.1** (explores defect Requirements 1.1, 1.2)

    Scoped to the ``countVisibleStopHooks(X.hookRegistry) > 1`` disjunct of the
    bug condition. AUTHORED TO FAIL on unfixed code, where both
    ``ask-bootcamper`` ("to wait for your answer") and ``module-recap-append``
    ("to append module recap on completion") surface labels.
    """

    @given(pair=st_agentstop_id_pair())
    def test_no_two_stop_hooks_both_surface_waiting_labels(
        self, pair: tuple[str, str]
    ) -> None:
        """For any pair of distinct Stop hooks, not both surface a waiting label."""
        id_a, id_b = pair
        both_visible = is_visible_waiting_label(id_a) and is_visible_waiting_label(id_b)
        assert not both_visible, (
            "Two Stop hooks surface user-facing waiting labels simultaneously "
            f"('{id_a}' -> {hook_name(id_a)!r}, '{id_b}' -> {hook_name(id_b)!r}); "
            "exactly one 'waiting for your answer' label must surface after "
            "consolidation."
        )

    def test_agentstop_order_has_exactly_one_visible_waiting_label(self) -> None:
        """``agentstop_order`` lists exactly one user-facing waiting-label hook.

        **Validates: Requirements 2.1**
        """
        visible = visible_stop_hook_ids()
        assert len(visible) == 1, (
            "Expected exactly one agentstop_order entry whose hook name starts "
            f"with {SURFACING_LABEL_PREFIXES}, found {len(visible)}: {visible}."
        )

    def test_module_recap_append_hook_file_absent(self) -> None:
        """No standalone ``module-recap-append.json`` Stop-trigger hook file exists.

        Its recap logic must live inside ``ask-bootcamper`` (Phase 0) so it no
        longer surfaces as a second UI label.

        **Validates: Requirements 2.1, 1.1, 1.2**
        """
        assert not MODULE_RECAP_APPEND_PATH.exists(), (
            "module-recap-append.json still exists as a standalone Stop hook "
            f"file at {MODULE_RECAP_APPEND_PATH}; it must be consolidated into "
            "ask-bootcamper.json so only one Stop label surfaces."
        )


# ---------------------------------------------------------------------------
# Defect 2 — Narration leak on a no-output turn
# ---------------------------------------------------------------------------


class TestNarrationLeakOutputRules:
    """OUTPUT RULES must carry explicit negative examples banning narration.

    **Validates: Requirements 2.3** (explores defect Requirement 1.3)

    Scoped to the ``allPhasesNoOutput AND responseText != "."`` disjunct of the
    bug condition. AUTHORED TO FAIL on unfixed code, whose OUTPUT RULES preamble
    carries no "✗" negative examples and does not prohibit the specific
    narration sentences the agent leaks on a no-output turn.
    """

    @given(fragment=st_narration_leak())
    def test_output_rules_prohibit_known_narration_leaks(self, fragment: str) -> None:
        """For any known narration fragment, the OUTPUT RULES must prohibit it."""
        prompt = ask_bootcamper_prompt()
        assert fragment in prompt, (
            "ask-bootcamper OUTPUT RULES do not explicitly prohibit the "
            f"narration leak {fragment!r}; a no-output turn must be forbidden "
            "from narrating internal hook evaluation."
        )

    def test_output_rules_have_at_least_three_negative_examples(self) -> None:
        """The OUTPUT RULES preamble carries at least three "✗" negative examples.

        **Validates: Requirements 2.3**
        """
        prompt = ask_bootcamper_prompt()
        count = count_negative_example_lines(prompt)
        assert count >= MIN_NEGATIVE_EXAMPLES, (
            f"ask-bootcamper OUTPUT RULES contain {count} '✗' negative-example "
            f"lines; at least {MIN_NEGATIVE_EXAMPLES} are required to prevent "
            "narration on a no-output turn."
        )
