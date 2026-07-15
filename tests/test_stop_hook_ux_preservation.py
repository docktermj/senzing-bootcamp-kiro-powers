"""Preservation property tests for the stop-hook-ux bugfix.

These tests encode design **Property 2 (Preservation)**:

    FOR ALL X WHERE NOT isBugCondition(X):
        F'(X) == F(X)

They follow the **observation-first methodology**: every assertion captures a
behavior that is TRUE on the CURRENT (unfixed) code, so the whole suite is GREEN
before the fix and establishes the baseline the fix must not regress.

Consolidating the recap logic into ``ask-bootcamper`` Phase 0 and deleting the
standalone ``module-recap-append.json`` hook must NOT change any of:

1. **Relative precedence** of the surviving agentStop hooks — ``ask-bootcamper``
   first, then celebration before gate-on-stop, gate-on-stop before
   visualization-offers, visualization-offers before critical-artifacts
   (Req 3.4, 3.7).
2. **Recap constraints** — boundary detection, ``config/.question_pending``
   deferral, ISO 8601 timestamps, no secrets, planner-only durations, and
   backfill verification remain present in whichever prompt currently owns the
   recap logic (Req 3.1, 3.2, 3.3).
3. **The four original ``ask-bootcamper`` phases** — Closing Question, Step
   Sequencing, MCP-First, Question Format — remain present and unaltered
   (Req 3.3).
4. **Registry mutual consistency** — the set of ``Stop``-trigger hooks in
   ``hooks.lock.yaml`` equals the set of ids in ``agentstop_order`` (Req 3.7).
5. **The ``preToolUse`` write gates** — ``enforce-mandatory-gate``,
   ``gate-module3-visualization``, ``write-policy-gate`` — are byte-for-byte
   unaltered (Req 3.5, 3.6).

**Observation-first design notes** (why these pass on UNFIXED code):

* Property 1 asserts only the RELATIVE order of the five SURVIVING hooks; it
  never pins ``module-recap-append``'s position, so removing it cannot break the
  invariant. The relative order of the five holds both before and after.
* Property 2 reads the recap constraints from :func:`recap_logic_text`, which
  returns ``module-recap-append.json``'s prompt while that file exists and falls
  back to ``ask-bootcamper``'s prompt (Phase 0) once the fix deletes it — so the
  constraints are checked in whichever location currently owns them.
* Property 4 asserts MUTUAL CONSISTENCY (lock ``Stop`` set == ``agentstop_order``
  set), which holds with six entries today and five after the fix. The stronger
  "``module-recap-append`` absent from the lock" claim is a POST-FIX assertion
  (Task 3.5 / 3.7 re-run), deliberately NOT asserted here so the baseline stays
  green.

Feature: stop-hook-ux

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**
"""

from __future__ import annotations

import hashlib
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
LOCKFILE_PATH: Path = HOOKS_DIR / "hooks.lock.yaml"
ASK_BOOTCAMPER_PATH: Path = HOOKS_DIR / "ask-bootcamper.json"
MODULE_RECAP_APPEND_PATH: Path = HOOKS_DIR / "module-recap-append.json"

# The agentStop event trigger value recorded in the v1 hook files and the lock.
STOP_TRIGGER: str = "Stop"

# ---------------------------------------------------------------------------
# Property 1 — relative precedence of the SURVIVING agentStop hooks
# ---------------------------------------------------------------------------
# Deliberately EXCLUDES ``module-recap-append`` (removed by the fix). The
# relative order of these five holds on the unfixed registry (where
# ``module-recap-append`` sits at order 2, between #1 and #2 here) AND after the
# fix (where it is gone and these five renumber 1..5).
EXPECTED_RELATIVE_ORDER: tuple[str, ...] = (
    "ask-bootcamper",
    "module-completion-celebration",
    "enforce-gate-on-stop",
    "enforce-visualization-offers",
    "enforce-critical-artifacts",
)

# ---------------------------------------------------------------------------
# Property 2 — recap constraints that must survive consolidation into Phase 0.
# Each maps a human-readable constraint name to distinctive substrings that
# appear in the prompt currently owning the recap logic.
# ---------------------------------------------------------------------------
RECAP_CONSTRAINTS: dict[str, tuple[str, ...]] = {
    "boundary detection": ("BOUNDARY DETECTION",),
    "question_pending deferral": ("config/.question_pending",),
    "ISO 8601 timestamps": ("ISO 8601",),
    "no secrets in recap": ("secrets",),
    "planner-only durations": ("completion_artifacts.py",),
    "backfill verification": ("--backfill",),
}

# ---------------------------------------------------------------------------
# Property 3 — the four original ask-bootcamper phases (header + internal tag).
# The fix only PREPENDS Phase 0; these four keep their numbers and content, so
# each fragment is present before AND after.
# ---------------------------------------------------------------------------
ASK_BOOTCAMPER_PHASES: dict[str, tuple[str, ...]] = {
    "Phase 1 - Closing Question": (
        "PHASE 1: CLOSING QUESTION",
        "Closing_Question_Phase",
    ),
    "Phase 2 - Step Sequencing": (
        "PHASE 2: STEP SEQUENCING",
        "Step_Sequencing_Phase",
    ),
    "Phase 3 - MCP-First": (
        "PHASE 3: MCP-FIRST COMPLIANCE",
        "MCP_First_Phase",
    ),
    "Phase 4 - Question Format": (
        "PHASE 4: QUESTION FORMAT",
        "Question_Format_Phase",
    ),
}

# ---------------------------------------------------------------------------
# Property 5 — the preToolUse write gates, pinned byte-for-byte. The fix touches
# ask-bootcamper.json / module-recap-append.json / hook-categories.yaml /
# hooks.lock.yaml only, so these three files stay unaltered. The SHA-256 pin is
# the strongest "completely unaltered" guarantee; matcher/trigger/fragment
# checks provide readable diagnostics when a regression is introduced.
# ---------------------------------------------------------------------------
PRETOOLUSE_MATCHER: str = "fs_write|str_replace|fs_append"

PRETOOLUSE_HOOKS: dict[str, dict[str, object]] = {
    "enforce-mandatory-gate": {
        "sha256": "7ffe25dc38f8365870047c526d610dd0c739c0c57261e11e0fef80b52f2dfc27",
        "fragments": ("\u26d4 BLOCKED", "mandatory gate"),
    },
    "gate-module3-visualization": {
        "sha256": "01dcd17eae7b64d53fb8a13e433ea6f8e4923d543da2f49c0fe6d703affc79db",
        "fragments": ("\u26d4 BLOCKED", "Module 3 cannot be marked complete"),
    },
    "write-policy-gate": {
        # Re-baselined for the mandatory-question-answers spec (Task 5.1 / 6.2):
        # the write-policy-gate prompt legitimately gained CHECK 5
        # (ANSWER-REQUIRED — no silent completion of a question-owning step),
        # so the gate file's bytes changed by design. This preservation pin is
        # re-frozen to the new digest (271a6fbe...364a4b -> 9caa3745...184372);
        # the stop-hook-ux fix itself still does not touch this gate, and the
        # SENZING SQL / write-momentum protections remain enforced.
        "sha256": "9caa3745ad6071190624a6922d59ded9301bb4e8c5cb59dbbdb455f7cb184372",
        "fragments": ("WRITE POLICY GATE", "SENZING SQL BLOCKING"),
    },
}


# ---------------------------------------------------------------------------
# Parsing helpers (minimal stdlib scanners, no PyYAML — repo convention)
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
    key. Surrounding quotes on the id value are stripped. The declared order is
    the precedence order (it mirrors the ``order:`` scalars).

    Args:
        path: Path to the YAML file. Defaults to ``CATEGORIES_PATH``.

    Returns:
        List of hook ids in declared (precedence) order.
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


def parse_lock_stop_hook_ids(path: Path | None = None) -> set[str]:
    """Return the set of hook ids in ``hooks.lock.yaml`` whose event is ``Stop``.

    Minimal stdlib scanner (no PyYAML): walks the top-level ``hooks:`` block,
    tracking the current ``- id:`` entry and its indented ``event_type:`` scalar,
    and collects ids whose ``event_type`` equals ``Stop``.

    Args:
        path: Path to the lockfile. Defaults to ``LOCKFILE_PATH``.

    Returns:
        Set of hook ids triggered on the agentStop event.
    """
    if path is None:
        path = LOCKFILE_PATH

    stop_ids: set[str] = set()
    current_id: str | None = None
    in_hooks_block = False
    id_item = re.compile(r"^-\s*id:\s*(.+?)\s*$")
    kv = re.compile(r"^([A-Za-z_]+):\s*(.+?)\s*$")

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "hooks:" and not raw_line.startswith(" "):
            in_hooks_block = True
            continue
        if not in_hooks_block:
            continue

        item_match = id_item.match(stripped)
        if item_match:
            current_id = _strip_scalar(item_match.group(1))
            continue

        kv_match = kv.match(stripped)
        if kv_match and current_id is not None:
            key, value = kv_match.group(1), _strip_scalar(kv_match.group(2))
            if key == "event_type" and value == STOP_TRIGGER:
                stop_ids.add(current_id)

    return stop_ids


def _strip_scalar(value: str) -> str:
    """Strip surrounding quotes and whitespace from a YAML scalar.

    Args:
        value: Raw scalar text.

    Returns:
        The unquoted, stripped scalar value.
    """
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def ask_bootcamper_prompt() -> str:
    """Return the ``action.prompt`` text of the ``ask-bootcamper`` Stop hook."""
    return _load_hook_entry(ASK_BOOTCAMPER_PATH)["action"]["prompt"]


def recap_logic_text() -> str:
    """Return the prompt text that CURRENTLY owns the recap-append logic.

    Observation-first: on UNFIXED code the recap logic lives in the standalone
    ``module-recap-append.json`` hook; after the fix it is folded into
    ``ask-bootcamper.json`` as Phase 0 and the standalone file is deleted. This
    returns whichever location currently holds the logic so the recap-constraint
    checks pass before AND after the fix.

    Returns:
        The recap-owning prompt text.
    """
    if MODULE_RECAP_APPEND_PATH.exists():
        return _load_hook_entry(MODULE_RECAP_APPEND_PATH)["action"]["prompt"]
    return ask_bootcamper_prompt()


def sha256_of(path: Path) -> str:
    """Return the hex SHA-256 digest of a file's raw bytes.

    Args:
        path: Path to the file to hash.

    Returns:
        The lowercase hex digest string.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Module-level data (computed once from the real files)
# ---------------------------------------------------------------------------

AGENTSTOP_ORDER_IDS: list[str] = parse_agentstop_order_ids()
LOCK_STOP_HOOK_IDS: set[str] = parse_lock_stop_hook_ids()
_REGISTRY_UNION: list[str] = sorted(set(AGENTSTOP_ORDER_IDS) | LOCK_STOP_HOOK_IDS)


# ---------------------------------------------------------------------------
# Strategies (st_-prefixed, per repo convention)
# ---------------------------------------------------------------------------


@st.composite
def st_precedence_pair(draw) -> tuple[str, str]:
    """Draw an ordered pair of surviving hooks that must keep their precedence.

    Draws indices ``i < j`` into :data:`EXPECTED_RELATIVE_ORDER` and returns the
    corresponding ``(earlier, later)`` hook ids. The invariant under test is that
    ``earlier`` outranks ``later`` in the real ``agentstop_order``.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(earlier_id, later_id)`` tuple with a fixed expected precedence.
    """
    last = len(EXPECTED_RELATIVE_ORDER) - 1
    i = draw(st.integers(min_value=0, max_value=last - 1))
    j = draw(st.integers(min_value=i + 1, max_value=last))
    return (EXPECTED_RELATIVE_ORDER[i], EXPECTED_RELATIVE_ORDER[j])


def st_recap_constraint() -> st.SearchStrategy[str]:
    """Strategy sampling over the recap-constraint names that must be preserved."""
    return st.sampled_from(sorted(RECAP_CONSTRAINTS))


def st_ask_phase() -> st.SearchStrategy[str]:
    """Strategy sampling over the four original ask-bootcamper phase names."""
    return st.sampled_from(sorted(ASK_BOOTCAMPER_PHASES))


def st_registry_hook_id() -> st.SearchStrategy[str]:
    """Strategy sampling over the union of agentstop_order and lock Stop ids."""
    return st.sampled_from(_REGISTRY_UNION)


def st_pretooluse_hook_id() -> st.SearchStrategy[str]:
    """Strategy sampling over the three preToolUse write-gate hook ids."""
    return st.sampled_from(sorted(PRETOOLUSE_HOOKS))


# ---------------------------------------------------------------------------
# Property 1 — relative precedence preserved
# ---------------------------------------------------------------------------


class TestPrecedencePreservation:
    """Relative precedence of the surviving agentStop hooks is preserved.

    **Validates: Requirements 3.4, 3.7**

    Observation-first: asserts only the relative order of the five surviving
    hooks (``module-recap-append`` intentionally excluded), which holds on the
    unfixed registry and after the fix.
    """

    @given(pair=st_precedence_pair())
    def test_relative_precedence_is_monotonic(self, pair: tuple[str, str]) -> None:
        """For any surviving pair, the earlier hook outranks the later hook."""
        earlier, later = pair
        assert earlier in AGENTSTOP_ORDER_IDS, (
            f"expected surviving hook '{earlier}' present in agentstop_order "
            f"{AGENTSTOP_ORDER_IDS}"
        )
        assert later in AGENTSTOP_ORDER_IDS, (
            f"expected surviving hook '{later}' present in agentstop_order "
            f"{AGENTSTOP_ORDER_IDS}"
        )
        rank_earlier = AGENTSTOP_ORDER_IDS.index(earlier)
        rank_later = AGENTSTOP_ORDER_IDS.index(later)
        assert rank_earlier < rank_later, (
            f"precedence regression: '{earlier}' (rank {rank_earlier}) must "
            f"come before '{later}' (rank {rank_later}) in agentstop_order "
            f"{AGENTSTOP_ORDER_IDS}"
        )

    def test_ask_bootcamper_has_absolute_precedence(self) -> None:
        """``ask-bootcamper`` is the first entry in ``agentstop_order``.

        **Validates: Requirements 3.4**
        """
        assert AGENTSTOP_ORDER_IDS, "agentstop_order is empty"
        assert AGENTSTOP_ORDER_IDS[0] == "ask-bootcamper", (
            "ask-bootcamper must retain absolute precedence (order 1); "
            f"first entry is '{AGENTSTOP_ORDER_IDS[0]}'"
        )

    def test_surviving_hooks_appear_in_expected_relative_order(self) -> None:
        """Filtering ``agentstop_order`` to the survivors yields the expected order.

        **Validates: Requirements 3.4, 3.7**
        """
        filtered = [hid for hid in AGENTSTOP_ORDER_IDS if hid in EXPECTED_RELATIVE_ORDER]
        assert filtered == list(EXPECTED_RELATIVE_ORDER), (
            "surviving agentStop hooks are out of order.\n"
            f"  expected: {list(EXPECTED_RELATIVE_ORDER)}\n"
            f"  actual:   {filtered}"
        )


# ---------------------------------------------------------------------------
# Property 2 — recap constraints preserved wherever the recap logic lives
# ---------------------------------------------------------------------------


class TestRecapConstraintPreservation:
    """Recap constraints survive in whichever prompt owns the recap logic.

    **Validates: Requirements 3.1, 3.2, 3.3**

    Observation-first: :func:`recap_logic_text` returns
    ``module-recap-append.json``'s prompt today and ``ask-bootcamper`` Phase 0
    after the fix, so each constraint is verified in its current location.
    """

    @given(constraint=st_recap_constraint())
    def test_recap_constraint_present(self, constraint: str) -> None:
        """For any required recap constraint, its markers are present."""
        text = recap_logic_text()
        for marker in RECAP_CONSTRAINTS[constraint]:
            assert marker in text, (
                f"recap constraint '{constraint}' lost its marker {marker!r}; "
                "the recap logic must preserve boundary detection, "
                "question_pending deferral, ISO 8601 timestamps, no-secrets, "
                "planner-only durations, and backfill verification."
            )

    def test_all_recap_constraints_present(self) -> None:
        """All recap constraints are present in the recap-owning prompt.

        **Validates: Requirements 3.1, 3.2**
        """
        text = recap_logic_text()
        missing = [
            name
            for name, markers in RECAP_CONSTRAINTS.items()
            if any(marker not in text for marker in markers)
        ]
        assert not missing, f"recap-owning prompt is missing constraints: {missing}"


# ---------------------------------------------------------------------------
# Property 3 — the four original ask-bootcamper phases remain present
# ---------------------------------------------------------------------------


class TestAskBootcamperPhasePreservation:
    """The four original ``ask-bootcamper`` phases remain present and unaltered.

    **Validates: Requirements 3.3**

    The fix only prepends a new Phase 0; Phases 1-4 keep their numbers and
    content, so each phase header and internal tag is present before and after.
    """

    @given(phase=st_ask_phase())
    def test_phase_fragments_present(self, phase: str) -> None:
        """For any of the four original phases, its header and tag are present."""
        prompt = ask_bootcamper_prompt()
        for fragment in ASK_BOOTCAMPER_PHASES[phase]:
            assert fragment in prompt, (
                f"{phase} is missing expected fragment {fragment!r}; the four "
                "original ask-bootcamper phases must remain present and unaltered."
            )

    def test_all_four_phases_present(self) -> None:
        """All four original phase headers are present in the prompt.

        **Validates: Requirements 3.3**
        """
        prompt = ask_bootcamper_prompt()
        missing = [
            name
            for name, fragments in ASK_BOOTCAMPER_PHASES.items()
            if any(fragment not in prompt for fragment in fragments)
        ]
        assert not missing, f"ask-bootcamper is missing phases: {missing}"


# ---------------------------------------------------------------------------
# Property 4 — registry mutual consistency (lock Stop set == agentstop_order set)
# ---------------------------------------------------------------------------


class TestRegistryConsistencyPreservation:
    """``hooks.lock.yaml`` Stop hooks and ``agentstop_order`` stay consistent.

    **Validates: Requirements 3.7**

    Observation-first: asserts the MUTUAL CONSISTENCY invariant (the two id sets
    are equal), which holds with six entries today and five after the fix. The
    stronger "``module-recap-append`` absent from the lock" claim is a post-fix
    assertion handled by Task 3.5 / 3.7 re-verification, not this baseline.
    """

    @given(hook_id=st_registry_hook_id())
    def test_lock_and_order_membership_biconditional(self, hook_id: str) -> None:
        """For any registry id, it is in the lock Stop set IFF it is in the order."""
        in_order = hook_id in set(AGENTSTOP_ORDER_IDS)
        in_lock = hook_id in LOCK_STOP_HOOK_IDS
        assert in_order == in_lock, (
            f"registry inconsistency for '{hook_id}': "
            f"agentstop_order={in_order}, lock Stop hooks={in_lock}. Every "
            "agentStop hook in the lock must have an agentstop_order entry and "
            "vice versa."
        )

    def test_lock_stop_set_equals_order_set(self) -> None:
        """The lock's Stop-hook set equals the ``agentstop_order`` id set.

        **Validates: Requirements 3.7**
        """
        order_set = set(AGENTSTOP_ORDER_IDS)
        assert LOCK_STOP_HOOK_IDS == order_set, (
            "hooks.lock.yaml Stop hooks must match agentstop_order exactly.\n"
            f"  in lock only:  {sorted(LOCK_STOP_HOOK_IDS - order_set)}\n"
            f"  in order only: {sorted(order_set - LOCK_STOP_HOOK_IDS)}"
        )

    def test_agentstop_order_has_no_duplicates(self) -> None:
        """``agentstop_order`` lists each hook id at most once."""
        assert len(AGENTSTOP_ORDER_IDS) == len(set(AGENTSTOP_ORDER_IDS)), (
            f"agentstop_order contains duplicate ids: {AGENTSTOP_ORDER_IDS}"
        )


# ---------------------------------------------------------------------------
# Property 5 — preToolUse write gates are byte-for-byte unaltered
# ---------------------------------------------------------------------------


class TestPreToolUseGatePreservation:
    """The three ``preToolUse`` write gates are completely unaltered.

    **Validates: Requirements 3.5, 3.6**

    The fix touches only the Stop-hook registry and prompts; these
    write-momentum gates must stay byte-for-byte identical. The SHA-256 pin is
    the byte-for-byte guarantee; trigger/matcher/fragment checks give readable
    diagnostics.
    """

    @given(hook_id=st_pretooluse_hook_id())
    def test_pretooluse_gate_unaltered(self, hook_id: str) -> None:
        """For any preToolUse gate, its bytes, trigger, matcher, and text hold."""
        path = HOOKS_DIR / f"{hook_id}.json"
        spec = PRETOOLUSE_HOOKS[hook_id]

        assert path.exists(), (
            f"preToolUse write gate '{hook_id}.json' must not be removed"
        )
        assert sha256_of(path) == spec["sha256"], (
            f"preToolUse write gate '{hook_id}.json' was altered "
            "(SHA-256 mismatch); it must remain byte-for-byte unchanged."
        )

        entry = _load_hook_entry(path)
        assert entry.get("trigger") == "PreToolUse", (
            f"'{hook_id}' must keep its PreToolUse trigger, got "
            f"{entry.get('trigger')!r}"
        )
        assert entry.get("matcher") == PRETOOLUSE_MATCHER, (
            f"'{hook_id}' must keep its write matcher {PRETOOLUSE_MATCHER!r}, "
            f"got {entry.get('matcher')!r}"
        )

        prompt = entry["action"]["prompt"]
        for fragment in spec["fragments"]:  # type: ignore[union-attr]
            assert fragment in prompt, (
                f"'{hook_id}' prompt lost expected fragment {fragment!r}"
            )

    def test_all_pretooluse_gates_present(self) -> None:
        """All three preToolUse write gates exist as hook files.

        **Validates: Requirements 3.5, 3.6**
        """
        for hook_id in PRETOOLUSE_HOOKS:
            assert (HOOKS_DIR / f"{hook_id}.json").exists(), (
                f"preToolUse write gate '{hook_id}.json' is missing"
            )
