"""Property and unit tests for the capture-hook completion safeguard.

Feature: capture-hook-completion-safeguard.

These are *script-behavior* tests for
``senzing-bootcamp/scripts/capture_hook_safeguard.py``, exercised over temporary
``.kiro/hooks`` directories (never the real one), so per ``structure.md`` they
live in ``senzing-bootcamp/tests/`` rather than the repo-root ``tests/``.

Properties covered:

- **Property 1** — Detection names exactly the missing capture-critical hooks
  and the outputs they feed. Validates: Requirements 1.1, 1.2
- **Property 2** — All hooks present is a silent no-op. Validates:
  Requirements 1.3

Later tasks append additional property/unit classes to this module; it is
structured (shared strategies + helpers up top, one class per property) so those
additions drop in cleanly.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import capture_hook_safeguard as chs  # noqa: E402

# The three capture-critical ids, as a sorted tuple for deterministic drawing.
_CAPTURE_CRITICAL_IDS: tuple[str, ...] = tuple(sorted(chs.CAPTURE_CRITICAL))

# The only outputs a capture-critical hook may feed (Requirement 1.2).
_VALID_OUTPUTS: frozenset[str] = frozenset({"recap", "transcript", "completion summary"})


# ---------------------------------------------------------------------------
# Strategies + materializer
# ---------------------------------------------------------------------------
#
# Following the established pattern in this suite (see conftest's WorldSpec /
# materialize_world), the strategy draws a *pure* description of a hooks-dir
# state and a helper materializes it into a fresh temp ``.kiro/hooks`` directory
# per example. Keeping the draw side-effect-free lets Hypothesis shrink freely;
# the test owns the temp directory lifecycle and cleans it up.


@dataclass(frozen=True)
class HooksDirState:
    """A pure description of a synthetic ``.kiro/hooks`` directory state.

    Attributes:
        present_ids: The subset of capture-critical ids whose
            ``<id>.kiro.hook`` file exists.
        unrelated_filenames: Extra ``*.kiro.hook`` filenames for non
            capture-critical hooks (must never affect detection).
    """

    present_ids: tuple[str, ...]
    unrelated_filenames: tuple[str, ...]


def _st_unrelated_filename() -> st.SearchStrategy[str]:
    """Draw an unrelated ``<hook-id>.kiro.hook`` filename.

    The hook id is a lowercase, hyphen-separated identifier that is never one of
    the three capture-critical ids, so these files exercise the "unrelated hooks
    never affect the result" guarantee.
    """
    return (
        st.from_regex(r"[a-z][a-z0-9]{0,7}(-[a-z0-9]{1,7}){0,3}", fullmatch=True)
        .filter(lambda hook_id: hook_id not in chs.CAPTURE_CRITICAL)
        .map(lambda hook_id: f"{hook_id}.kiro.hook")
    )


@st.composite
def st_hooks_dir_state(draw) -> HooksDirState:
    """Draw a synthetic ``.kiro/hooks`` state: a subset of capture-critical
    hooks present plus arbitrary unrelated ``*.kiro.hook`` files.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A :class:`HooksDirState` describing which capture-critical ids are
        present and which unrelated hook files sit alongside them. Materialize
        it with :func:`materialize_hooks_dir` to get real empty files in a temp
        ``.kiro/hooks`` directory.
    """
    present_ids = draw(
        st.lists(
            st.sampled_from(_CAPTURE_CRITICAL_IDS),
            min_size=0,
            max_size=len(_CAPTURE_CRITICAL_IDS),
            unique=True,
        )
    )
    unrelated = draw(
        st.lists(_st_unrelated_filename(), min_size=0, max_size=5, unique=True)
    )
    return HooksDirState(
        present_ids=tuple(sorted(present_ids)),
        unrelated_filenames=tuple(sorted(unrelated)),
    )


def materialize_hooks_dir(state: HooksDirState, base_dir: Path) -> Path:
    """Materialize ``state`` as empty files in a ``.kiro/hooks`` dir under ``base_dir``.

    Writes one empty ``<id>.kiro.hook`` file per present capture-critical id plus
    one empty file per unrelated filename. Files are synthetic and PII-free.

    Args:
        state: The hooks-dir description to write.
        base_dir: A fresh directory to build ``.kiro/hooks`` beneath.

    Returns:
        The path to the materialized ``.kiro/hooks`` directory.
    """
    hooks_dir = base_dir / ".kiro" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for hook_id in state.present_ids:
        (hooks_dir / f"{hook_id}.kiro.hook").write_text("", encoding="utf-8")
    for filename in state.unrelated_filenames:
        (hooks_dir / filename).write_text("", encoding="utf-8")
    return hooks_dir


# ---------------------------------------------------------------------------
# Property 1 — Detection names exactly the missing capture-critical hooks
# ---------------------------------------------------------------------------


class TestDetectionNaming:
    """Property 1: detection names exactly the missing capture-critical hooks.

    **Validates: Requirements 1.1, 1.2**
    """

    # Feature: capture-hook-completion-safeguard, Property 1: Detection names
    # exactly the missing capture-critical hooks and the outputs they feed
    @given(state=st_hooks_dir_state())
    def test_detection_names_exactly_missing_hooks_and_outputs(
        self, state: HooksDirState
    ) -> None:
        base_dir = Path(tempfile.mkdtemp())
        try:
            hooks_dir = materialize_hooks_dir(state, base_dir)

            missing = chs.detect_missing_capture_hooks(hooks_dir)

            expected_missing = sorted(
                set(_CAPTURE_CRITICAL_IDS) - set(state.present_ids)
            )
            # Detection returns exactly the absent capture-critical ids, sorted,
            # unaffected by any unrelated *.kiro.hook files (Req 1.1).
            assert missing == expected_missing

            plan = chs.build_reminder(missing)

            # The reminder reports exactly those missing ids (Req 1.2).
            reported_ids = [hook.hook_id for hook in plan.missing]
            assert reported_ids == expected_missing

            # Each reported hook names a non-empty output list drawn only from
            # {recap, transcript, completion summary} (Req 1.2).
            for hook in plan.missing:
                assert hook.outputs, f"{hook.hook_id} reported no outputs"
                assert set(hook.outputs) <= _VALID_OUTPUTS
                assert hook.outputs == chs.outputs_for_hook(hook.hook_id)
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 2 — All hooks present is a silent no-op
# ---------------------------------------------------------------------------
#
# Reuses HooksDirState / materialize_hooks_dir and the unrelated-filename
# strategy above; the only new piece is a strategy that always marks all three
# capture-critical ids present while still scattering arbitrary unrelated
# *.kiro.hook files alongside them.


@st.composite
def st_all_present_hooks_dir_state(draw) -> HooksDirState:
    """Draw a ``.kiro/hooks`` state with all three capture-critical hooks present.

    Every drawn state marks all three capture-critical ids present and adds an
    arbitrary set of unrelated ``*.kiro.hook`` files, exercising the guarantee
    that a fully-populated directory (regardless of unrelated files) is a silent
    no-op.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A :class:`HooksDirState` with ``present_ids`` equal to all three
        capture-critical ids plus arbitrary unrelated hook filenames.
    """
    unrelated = draw(
        st.lists(_st_unrelated_filename(), min_size=0, max_size=5, unique=True)
    )
    return HooksDirState(
        present_ids=_CAPTURE_CRITICAL_IDS,
        unrelated_filenames=tuple(sorted(unrelated)),
    )


class TestAllPresentNoop:
    """Property 2: all hooks present is a silent no-op.

    **Validates: Requirements 1.3**
    """

    # Feature: capture-hook-completion-safeguard, Property 2: All hooks present
    # is a silent no-op
    @given(state=st_all_present_hooks_dir_state())
    def test_all_present_is_silent_noop(self, state: HooksDirState) -> None:
        base_dir = Path(tempfile.mkdtemp())
        try:
            hooks_dir = materialize_hooks_dir(state, base_dir)

            missing = chs.detect_missing_capture_hooks(hooks_dir)

            # All three present -> nothing is missing, unaffected by any
            # unrelated *.kiro.hook files (Req 1.3).
            assert missing == []

            plan = chs.build_reminder(missing)

            # A no-op plan: silent, never a Soft_Block, with no missing entries
            # (Req 1.3).
            assert plan.is_noop is True
            assert plan.is_soft_block is False
            assert plan.missing == []
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 3 — A missing hook always yields an overridable Soft_Block
# ---------------------------------------------------------------------------
#
# Reuses _CAPTURE_CRITICAL_IDS and chs.INSTALL_OPTIONS; the only new piece is a
# strategy that draws a non-empty subset of the three capture-critical ids to
# stand in for the detected "missing" set.


@st.composite
def st_missing_set(draw) -> list[str]:
    """Draw a non-empty subset of the three capture-critical ids.

    Represents an arbitrary detected "missing" set fed to
    :func:`build_reminder`, covering every non-empty combination of the three
    capture-critical hooks.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A sorted, non-empty list of distinct capture-critical ids.
    """
    missing = draw(
        st.lists(
            st.sampled_from(_CAPTURE_CRITICAL_IDS),
            min_size=1,
            max_size=len(_CAPTURE_CRITICAL_IDS),
            unique=True,
        )
    )
    return sorted(missing)


class TestOverridableSoftBlock:
    """Property 3: a missing hook always yields an overridable Soft_Block.

    **Validates: Requirements 2.1, 2.4**
    """

    # Feature: capture-hook-completion-safeguard, Property 3: A missing hook
    # always yields an overridable Soft_Block with both install options
    @given(missing_ids=st_missing_set())
    def test_missing_yields_overridable_soft_block(
        self, missing_ids: list[str]
    ) -> None:
        plan = chs.build_reminder(missing_ids)

        # A non-empty missing set is always an overridable Soft_Block, never a
        # silent no-op and never a Mandatory_Gate (Req 2.4). There is no
        # hard-gate field; is_soft_block=True is the design's representation of
        # the overridable stop-and-confirm.
        assert plan.is_soft_block is True
        assert plan.is_noop is False

        # The Soft_Block carries exactly the two canonical install options
        # (re-create via createHook, or install_hooks.py --essential) (Req 2.1).
        assert plan.install_options == chs.INSTALL_OPTIONS
        assert len(plan.install_options) == 2


# ---------------------------------------------------------------------------
# Property 5 — The reminder recurs at every boundary while a hook stays missing
# ---------------------------------------------------------------------------
#
# Reuses st_missing_set() above for the non-empty missing set. The only new
# piece is st_progress_mapping(): well-formed progress dicts optionally
# pre-seeded with a prior acknowledgment history (including repeated
# acknowledgments of the same ids across many boundaries), used to prove that
# should_reprompt never consults that history to suppress the reminder.


def _st_simple_json_value() -> st.SearchStrategy[object]:
    """Draw a simple JSON-ish scalar/collection for arbitrary progress values.

    Covers the kinds of values a real ``config/bootcamp_progress.json`` mapping
    holds (booleans, ints, strings, and shallow lists/dicts thereof) so the
    generated progress dicts are well-formed and JSON-serializable.
    """
    scalars = st.one_of(
        st.booleans(),
        st.integers(min_value=-1000, max_value=1000),
        st.text(max_size=20),
    )
    return st.recursive(
        scalars,
        lambda children: st.one_of(
            st.lists(children, max_size=4),
            st.dictionaries(st.text(max_size=10), children, max_size=4),
        ),
        max_leaves=8,
    )


@st.composite
def st_progress_mapping(draw) -> dict:
    """Draw a well-formed progress dict, optionally pre-seeded with prior acks.

    Builds an arbitrary ``config/bootcamp_progress.json``-style mapping (arbitrary
    string keys mapped to simple JSON-ish values) and, with some probability,
    pre-seeds a ``capture_hook_safeguard.acknowledgments`` list of prior entries.
    Each entry has the recorded shape ``{"module": int, "acknowledged": [ids],
    "timestamp": str}``. The acknowledgment list may repeat acknowledgments of
    the same ids across many simulated boundaries, so a passing property proves
    that no amount of prior acknowledgment suppresses the reminder.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A well-formed progress mapping, sometimes carrying a prior
        ``capture_hook_safeguard.acknowledgments`` history.
    """
    progress: dict = draw(
        st.dictionaries(
            st.text(max_size=12).filter(
                lambda key: key != "capture_hook_safeguard"
            ),
            _st_simple_json_value(),
            max_size=5,
        )
    )

    def _st_acknowledgment() -> st.SearchStrategy[dict]:
        return st.fixed_dictionaries(
            {
                "module": st.integers(min_value=0, max_value=11),
                "acknowledged": st.lists(
                    st.sampled_from(_CAPTURE_CRITICAL_IDS),
                    min_size=1,
                    max_size=len(_CAPTURE_CRITICAL_IDS),
                    unique=True,
                ).map(sorted),
                "timestamp": st.text(max_size=25),
            }
        )

    if draw(st.booleans()):
        # Pre-seed a prior acknowledgment history. min_size=0 keeps the empty
        # history in play; larger lists exercise repeated acks of the same ids.
        acknowledgments = draw(
            st.lists(_st_acknowledgment(), min_size=0, max_size=6)
        )
        progress["capture_hook_safeguard"] = {"acknowledgments": acknowledgments}

    return progress


class TestRecurringReprompt:
    """Property 5: the reminder recurs at every boundary and is never suppressed.

    **Validates: Requirements 2.3, 2.4**
    """

    # Feature: capture-hook-completion-safeguard, Property 5: The reminder
    # recurs at every boundary while a hook stays missing and is never
    # suppressed
    @given(missing_ids=st_missing_set(), progress=st_progress_mapping())
    def test_reprompt_recurs_regardless_of_acknowledgments(
        self, missing_ids: list[str], progress: dict
    ) -> None:
        # For any non-empty missing set and any prior acknowledgment history
        # (including repeated acks of the same ids), the reminder re-presents:
        # should_reprompt returns True and an acknowledgment never suppresses a
        # future reminder (Req 2.3, 2.4).
        assert chs.should_reprompt(missing_ids, progress) is True


# ---------------------------------------------------------------------------
# Property 4 — An explicit override records an acknowledgment and permits the
# transition
# ---------------------------------------------------------------------------
#
# Reuses st_missing_set() (a non-empty detected missing set) and
# st_progress_mapping() (a well-formed progress dict, optionally pre-seeded with
# a prior capture_hook_safeguard.acknowledgments history). Each example writes
# the drawn progress mapping to a temp JSON file, invokes record_acknowledgment
# on it, and asserts exactly one entry is appended, the pre-existing keys are
# preserved byte-for-byte, and the returned mapping matches what is persisted.


class TestAcknowledgmentRecording:
    """Property 4: an explicit override records an acknowledgment and permits
    the transition.

    **Validates: Requirements 2.2**
    """

    # Feature: capture-hook-completion-safeguard, Property 4: An explicit
    # override records an acknowledgment and permits the transition
    @given(
        progress=st_progress_mapping(),
        module=st.integers(min_value=0, max_value=11),
        missing_ids=st_missing_set(),
    )
    def test_override_records_acknowledgment_and_permits_transition(
        self, progress: dict, module: int, missing_ids: list[str]
    ) -> None:
        import json

        base_dir = Path(tempfile.mkdtemp())
        try:
            progress_path = base_dir / "config" / "bootcamp_progress.json"
            progress_path.parent.mkdir(parents=True, exist_ok=True)
            with progress_path.open("w", encoding="utf-8") as handle:
                json.dump(progress, handle, indent=2)
                handle.write("\n")

            # The mapping as it round-trips through JSON on disk — the true
            # pre-state record_acknowledgment reads from.
            with progress_path.open(encoding="utf-8") as handle:
                before = json.load(handle)

            def _acks(mapping: dict) -> list:
                safeguard = mapping.get("capture_hook_safeguard")
                if isinstance(safeguard, dict):
                    acks = safeguard.get("acknowledgments")
                    if isinstance(acks, list):
                        return acks
                return []

            before_count = len(_acks(before))

            updated = chs.record_acknowledgment(progress_path, module, missing_ids)

            after_acks = _acks(updated)

            # Exactly one new acknowledgment entry was appended (Req 2.2).
            assert len(after_acks) == before_count + 1
            if before_count == 0:
                assert len(after_acks) == 1

            # The prior acknowledgment history (if any) is preserved verbatim,
            # with the new entry appended at the end.
            assert after_acks[:before_count] == _acks(before)

            # The new entry names the module, the sorted acknowledged ids, and a
            # non-empty timestamp string (Req 2.2).
            entry = after_acks[-1]
            assert entry["module"] == module
            assert entry["acknowledged"] == sorted(missing_ids)
            assert isinstance(entry["timestamp"], str)
            assert entry["timestamp"] != ""

            # Every pre-existing progress key (other than the safeguard
            # bookkeeping) is preserved byte-for-byte in value (Req 2.2).
            for key, value in before.items():
                if key == "capture_hook_safeguard":
                    continue
                assert key in updated
                assert updated[key] == value

            # The returned mapping equals exactly what is persisted to disk —
            # the recorded acknowledgment is what permits the transition to
            # proceed (Req 2.2).
            with progress_path.open(encoding="utf-8") as handle:
                persisted = json.load(handle)
            assert updated == persisted
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Unit / example tests — detection, no-op, recurrence, and override
# ---------------------------------------------------------------------------
#
# Concrete example tests (no @given) complementing the property classes above.
# Each reuses HooksDirState / materialize_hooks_dir / _CAPTURE_CRITICAL_IDS and
# the chs module handle; none redefine or modify the existing helpers.


class TestSafeguardExamples:
    """Example tests for detection, no-op, recurrence, and override paths.

    Concrete (non-property) examples covering: detection of each individual
    missing capture-critical hook and the outputs it feeds, the all-present
    silent no-op, the recurring re-prompt across multiple boundaries, and the
    explicit-override continue path.

    **Validates: Requirements 4.1, 4.2**
    """

    def test_detection_of_each_individual_missing_hook(self) -> None:
        """Each capture-critical hook, when singly absent, is named with its outputs.

        For every capture-critical id, build a directory with the *other two*
        present, then assert detection reports exactly that one id and
        ``build_reminder`` names it together with the concrete outputs it feeds.
        """
        for missing_id in _CAPTURE_CRITICAL_IDS:
            present_ids = tuple(
                sorted(hook_id for hook_id in _CAPTURE_CRITICAL_IDS if hook_id != missing_id)
            )
            state = HooksDirState(present_ids=present_ids, unrelated_filenames=())
            base_dir = Path(tempfile.mkdtemp())
            try:
                hooks_dir = materialize_hooks_dir(state, base_dir)

                missing = chs.detect_missing_capture_hooks(hooks_dir)

                # Exactly the one absent capture-critical id is detected (Req 4.1).
                assert missing == [missing_id]

                plan = chs.build_reminder(missing)

                # The reminder is an overridable Soft_Block naming that one hook.
                assert plan.is_noop is False
                assert plan.is_soft_block is True
                assert [hook.hook_id for hook in plan.missing] == [missing_id]

                # The hook is named with the concrete, non-empty outputs it feeds.
                only = plan.missing[0]
                assert only.outputs, f"{missing_id} reported no outputs"
                assert only.outputs == chs.outputs_for_hook(missing_id)
                assert set(only.outputs) <= _VALID_OUTPUTS
            finally:
                shutil.rmtree(base_dir, ignore_errors=True)

    def test_all_present_is_silent_noop(self) -> None:
        """A directory with all three capture-critical hooks is a silent no-op.

        Detection returns nothing missing and ``build_reminder`` yields a no-op
        plan (silent, never a Soft_Block, no missing entries), so the safeguard
        emits no output.
        """
        state = HooksDirState(present_ids=_CAPTURE_CRITICAL_IDS, unrelated_filenames=())
        base_dir = Path(tempfile.mkdtemp())
        try:
            hooks_dir = materialize_hooks_dir(state, base_dir)

            missing = chs.detect_missing_capture_hooks(hooks_dir)

            # All three present -> nothing missing (Req 4.1).
            assert missing == []

            plan = chs.build_reminder(missing)

            # A silent no-op plan: no output, never a Soft_Block, no entries.
            assert plan.is_noop is True
            assert plan.is_soft_block is False
            assert plan.missing == []
            assert chs.render_plan(plan) == ""
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)

    def test_recurring_reprompt_across_multiple_boundaries(self) -> None:
        """A still-missing hook re-prompts at each of three successive boundaries.

        Simulate three module-completion boundaries with the same hook missing,
        recording an acknowledgment between boundaries; assert
        ``should_reprompt`` returns True at every boundary regardless of the
        accumulating acknowledgment history.
        """
        missing_ids = ["session-log-events"]
        base_dir = Path(tempfile.mkdtemp())
        try:
            progress_path = base_dir / "config" / "bootcamp_progress.json"
            progress_path.parent.mkdir(parents=True, exist_ok=True)

            for boundary_module in (4, 5, 6):
                # The reminder recurs at this boundary despite prior acks (Req 4.1).
                assert chs.should_reprompt(missing_ids, {}) is True

                # Record the explicit-override acknowledgment before moving on.
                updated = chs.record_acknowledgment(
                    progress_path, boundary_module, missing_ids
                )
                acks = updated["capture_hook_safeguard"]["acknowledgments"]
                # An acknowledgment accumulates but never suppresses future prompts.
                assert len(acks) == boundary_module - 3

            # After three acknowledged boundaries the reminder still fires.
            assert chs.should_reprompt(missing_ids, updated) is True
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)

    def test_explicit_override_continue_path(self) -> None:
        """An explicit override records the acknowledgment and permits the transition.

        Call ``record_acknowledgment`` on a fresh progress file and assert the
        entry lands in ``capture_hook_safeguard.acknowledgments`` with the module,
        acknowledged ids, and a timestamp, and that it is persisted to disk (the
        transition is permitted to proceed).
        """
        import json

        missing_ids = ["ask-bootcamper", "module-recap-append"]
        module = 7
        base_dir = Path(tempfile.mkdtemp())
        try:
            progress_path = base_dir / "config" / "bootcamp_progress.json"

            updated = chs.record_acknowledgment(progress_path, module, missing_ids)

            acks = updated["capture_hook_safeguard"]["acknowledgments"]
            # Exactly one acknowledgment entry was recorded (Req 4.1).
            assert len(acks) == 1

            entry = acks[0]
            assert entry["module"] == module
            assert entry["acknowledged"] == sorted(missing_ids)
            assert isinstance(entry["timestamp"], str)
            assert entry["timestamp"] != ""

            # The acknowledgment is persisted to disk, so the transition proceeds.
            assert progress_path.is_file()
            with progress_path.open(encoding="utf-8") as handle:
                persisted = json.load(handle)
            assert persisted == updated
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Consistency (single source of truth) — Requirement 3.2
# ---------------------------------------------------------------------------
#
# ``install_hooks`` is already on sys.path (the safeguard module imports it via
# the same scripts directory inserted above), so it imports directly here.

import install_hooks  # noqa: E402


class TestSingleSourceOfTruth:
    """Consistency: the safeguard reuses a single source of truth.

    Assert the safeguard's capture-critical set is exactly
    ``install_hooks.CAPTURE_CRITICAL`` (never redefined) and that its two
    presented install options match the two canonical options offered by the
    session-start Warn_On_Absence_Check (re-create via createHook from the
    registry, or ``install_hooks.py --essential``), so the module-completion
    safeguard and the session-start check can never drift apart.

    **Validates: Requirements 3.2**
    """

    def test_capture_critical_set_is_the_installer_single_source(self) -> None:
        """The safeguard reuses ``install_hooks.CAPTURE_CRITICAL`` verbatim.

        It must not redefine the capture-critical set: ``chs.CAPTURE_CRITICAL``
        is the very object exposed by the installer, keeping the two checks in
        sync.
        """
        # Same value and same object — the safeguard did not redefine the set.
        assert chs.CAPTURE_CRITICAL == install_hooks.CAPTURE_CRITICAL
        assert chs.CAPTURE_CRITICAL is install_hooks.CAPTURE_CRITICAL

    def test_install_options_match_the_two_canonical_options(self) -> None:
        """The presented options are the two canonical Warn_On_Absence options.

        The session-start Warn_On_Absence_Check offers exactly two install
        paths: re-create via ``createHook`` from the hook registry, or run
        ``install_hooks.py --essential``. Assert the safeguard presents a
        2-tuple whose first option references createHook/registry and whose
        second references ``install_hooks.py --essential`` (checked by key
        substrings, not brittle full-string equality against prose).
        """
        options = chs.INSTALL_OPTIONS

        # Exactly two canonical install options are presented (Req 3.2).
        assert isinstance(options, tuple)
        assert len(options) == 2

        recreate_option, installer_option = options

        # First option: re-create via createHook from the hook registry.
        assert "createHook" in recreate_option
        assert "registry" in recreate_option.lower()

        # Second option: the file-copy installer's --essential set.
        assert "install_hooks.py" in installer_option
        assert "--essential" in installer_option
