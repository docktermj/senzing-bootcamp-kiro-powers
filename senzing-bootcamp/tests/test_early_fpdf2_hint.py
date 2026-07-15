"""Tests for the early-fpdf2-hint feature.

Feature: early-fpdf2-hint

Covers the two suggested test areas for the optional-tests task:

1. Steering-content assertions on Module 1 Phase 2 step 17a
   (``module-01-phase2-document-confirm.md``): the step invokes
   ``fpdf2_preflight.py`` at a natural, non-interrupting point (the
   module-completion recap), frames installing ``fpdf2`` as an *upgrade* and
   never a requirement, guards on the ``fpdf2_hint_shown`` flag, sets the flag
   only after surfacing the hint, and adds no ``👉`` question / ``🛑`` gate.
2. A preference-flag round-trip for ``fpdf2_hint_shown`` via
   ``preferences_utils`` (unset -> write True -> reload True -> schema
   validates), plus a property that any boolean value round-trips and
   validates.

The steering tests read the actual steering file (like
``test_fpdf2_preflight_note.py``) and assert on its contents with string-index
comparisons using anchors present in the file. The round-trip tests use the
canonical ``write_preference`` / ``load_preferences`` / ``validate_preferences_schema``
helpers with a throwaway preferences file per example.
"""

from __future__ import annotations

import dataclasses
import sys
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# Make scripts importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from preferences_utils import (
    _BOOL_OR_NONE_KEYS,
    KNOWN_TOP_LEVEL_KEYS,
    PreferencesSchema,
    load_preferences,
    validate_preferences_schema,
    write_preference,
)

# ---------------------------------------------------------------------------
# Steering file location + step-17a extraction
# ---------------------------------------------------------------------------

_STEERING_PATH = Path(__file__).resolve().parent.parent / "steering"
_MODULE1_PHASE2_PATH = _STEERING_PATH / "module-01-phase2-document-confirm.md"

# Anchors that bound step 17a within the Module 1 Phase 2 steering file.
_STEP_17A_HEADER = "17a. **fpdf2 early hint**"
_STEP_18_HEADER = "18. **Transition to Module 4**"
_STEP_17_HEADER = "17. **Offer stakeholder summary**"
_PREFLIGHT_INVOCATION = "python3 senzing-bootcamp/scripts/fpdf2_preflight.py"
_SET_FLAG_CALL = 'write_preference("fpdf2_hint_shown", True)'


def _phase2_content() -> str:
    """Read the Module 1 Phase 2 steering file.

    Returns:
        The full text of ``module-01-phase2-document-confirm.md``.
    """
    return _MODULE1_PHASE2_PATH.read_text(encoding="utf-8")


def _step_17a_section() -> str:
    """Extract the step-17a section text (from its header up to step 18).

    Returns:
        The substring of the steering file covering step 17a only, so the
        gates/questions of the neighbouring steps (16 and 17) cannot leak into
        the "no question / no gate" assertions.
    """
    content = _phase2_content()
    start = content.find(_STEP_17A_HEADER)
    end = content.find(_STEP_18_HEADER)
    assert start != -1, "step 17a header not found in the Phase 2 steering file"
    assert end != -1, "step 18 header not found in the Phase 2 steering file"
    assert end > start, "step 18 must come after step 17a"
    return content[start:end]


# ---------------------------------------------------------------------------
# Steering-content assertions for step 17a
# ---------------------------------------------------------------------------


class TestStep17aSteeringContent:
    """Step 17a surfaces the fpdf2 hint early, one-time, and non-blocking.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 3.2**

    Asserts on the actual ``module-01-phase2-document-confirm.md`` step-17a
    text: it invokes ``fpdf2_preflight.py`` at the module-completion recap (a
    non-interrupting point), frames installing ``fpdf2`` as an upgrade (never a
    requirement, with a valid PDF produced either way), guards on the
    ``fpdf2_hint_shown`` flag before running, sets the flag only after
    surfacing, stays silent when ``fpdf2`` is present, does not auto-install,
    and adds no ``👉`` question or ``🛑`` gate.
    """

    def test_step_17a_invokes_preflight(self) -> None:
        """Step 17a runs ``fpdf2_preflight.py``.

        **Validates: Requirements 1.1**
        """
        section = _step_17a_section()
        assert _PREFLIGHT_INVOCATION in section, (
            "step 17a must invoke python3 senzing-bootcamp/scripts/fpdf2_preflight.py"
        )

    def test_step_17a_fires_at_non_interrupting_point(self) -> None:
        """Step 17a sits at the module-completion recap, a non-interrupting point.

        The step header labels the placement, and step 17a lands after the
        stakeholder-summary offer (step 17) and before the Module 4 transition
        (step 18) — i.e. at the completion recap, not mid-question.

        **Validates: Requirements 1.1**
        """
        content = _phase2_content()
        section = _step_17a_section()

        assert "non-interrupting" in section.lower(), (
            "step 17a should label its placement as a non-interrupting point"
        )

        step_17_idx = content.find(_STEP_17_HEADER)
        step_17a_idx = content.find(_STEP_17A_HEADER)
        step_18_idx = content.find(_STEP_18_HEADER)
        assert step_17_idx != -1
        assert step_17a_idx != -1
        assert step_18_idx != -1
        assert step_17_idx < step_17a_idx < step_18_idx, (
            "step 17a must fall between step 17 and step 18 (the completion recap)"
        )

    def test_step_17a_frames_hint_as_upgrade_not_requirement(self) -> None:
        """Step 17a frames the hint as an upgrade, with a valid PDF either way.

        **Validates: Requirements 1.2, 1.4**
        """
        lowered = _step_17a_section().lower()
        assert "upgrade" in lowered, (
            "step 17a must frame installing fpdf2 as an upgrade"
        )
        assert "never a requirement" in lowered, (
            "step 17a must state the hint is never a requirement"
        )
        assert "either way" in lowered, (
            "step 17a must state a valid recap PDF is produced either way"
        )
        assert "pip install fpdf2" in lowered, (
            "step 17a must mention the exact install command"
        )

    def test_step_17a_guards_on_flag_before_running(self) -> None:
        """Step 17a checks ``fpdf2_hint_shown`` and skips before running preflight.

        **Validates: Requirements 2.2**
        """
        section = _step_17a_section()
        lowered = section.lower()

        assert "fpdf2_hint_shown" in section, (
            "step 17a must reference the fpdf2_hint_shown flag"
        )

        guard_idx = lowered.find("guard first")
        invocation_idx = section.find(_PREFLIGHT_INVOCATION)
        assert guard_idx != -1, "step 17a must guard first (skip if already shown)"
        assert invocation_idx != -1
        assert guard_idx < invocation_idx, (
            "the flag guard must precede the preflight invocation (skip if set)"
        )
        assert "do nothing" in lowered, (
            "step 17a must do nothing when the flag is already set"
        )

    def test_step_17a_sets_flag_after_surfacing(self) -> None:
        """Step 17a sets ``fpdf2_hint_shown`` only after surfacing the hint.

        **Validates: Requirements 2.2**
        """
        section = _step_17a_section()
        lowered = section.lower()

        set_idx = section.find(_SET_FLAG_CALL)
        assert set_idx != -1, (
            "step 17a must set the flag via "
            'write_preference("fpdf2_hint_shown", True)'
        )

        after_idx = lowered.find("after surfacing")
        assert after_idx != -1, (
            "step 17a must record the flag after surfacing the hint"
        )
        assert after_idx < set_idx, (
            "the flag must be set after (not before) surfacing the hint"
        )

    def test_step_17a_silent_when_fpdf2_present(self) -> None:
        """Step 17a stays silent (and writes no flag) when ``fpdf2`` is present.

        **Validates: Requirements 1.3, 2.2**
        """
        lowered = _step_17a_section().lower()
        assert "stay silent" in lowered, (
            "step 17a must stay silent when fpdf2 is present"
        )
        assert "no** flag" in lowered or "no flag" in lowered, (
            "step 17a must write no flag when fpdf2 is present"
        )

    def test_step_17a_adds_no_question_or_gate(self) -> None:
        """Step 17a adds no ``👉`` question prompt and no ``🛑`` STOP gate.

        The bootcamp presents required questions as ``👉 **"..."``  and gates
        with a ``> **🛑 STOP ...`` blockquote (see steps 16 and 17). Step 17a
        must contain neither construct. A purely descriptive mention of the
        word "question" (e.g. "it never adds a 👉 question") is fine — only an
        actual bold-quoted pointer prompt is forbidden.

        **Validates: Requirements 2.1**
        """
        section = _step_17a_section()

        assert "🛑" not in section, (
            "step 17a must not add a 🛑 STOP gate"
        )
        assert '👉 **"' not in section, (
            "step 17a must not present a 👉 bold-quoted question prompt"
        )

        lowered = section.lower()
        assert "non-blocking and orientation-only" in lowered, (
            "step 17a must state it is non-blocking and orientation-only"
        )
        assert "never gates progress" in lowered, (
            "step 17a must state it never gates progress"
        )

    def test_step_17a_does_not_auto_install(self) -> None:
        """Step 17a never auto-installs ``fpdf2`` during Module 1.

        **Validates: Requirements 3.2**
        """
        lowered = _step_17a_section().lower()
        assert "does not auto-install" in lowered, (
            "step 17a must state it does not auto-install fpdf2"
        )


# ---------------------------------------------------------------------------
# fpdf2_hint_shown preference registration + round-trip
# ---------------------------------------------------------------------------


class TestFpdf2HintShownRegistration:
    """The ``fpdf2_hint_shown`` flag is a recognized boolean preference.

    **Validates: Requirements 2.2, 3.1**

    The one-time guard depends on the flag being a first-class, schema-known
    boolean preference: present in ``KNOWN_TOP_LEVEL_KEYS`` (so
    ``write_preference`` accepts it and the validator does not reject it), in
    ``_BOOL_OR_NONE_KEYS`` (so it is type-checked as ``bool | None``), and a
    field on ``PreferencesSchema``.
    """

    def test_flag_is_a_known_top_level_key(self) -> None:
        """``fpdf2_hint_shown`` is a recognized top-level preference key.

        **Validates: Requirements 2.2**
        """
        assert "fpdf2_hint_shown" in KNOWN_TOP_LEVEL_KEYS

    def test_flag_is_validated_as_bool_or_none(self) -> None:
        """``fpdf2_hint_shown`` is type-checked as ``bool | None``.

        **Validates: Requirements 2.2**
        """
        assert "fpdf2_hint_shown" in _BOOL_OR_NONE_KEYS

    def test_flag_is_a_schema_field(self) -> None:
        """``PreferencesSchema`` declares an ``fpdf2_hint_shown`` field.

        **Validates: Requirements 3.1**
        """
        field_names = {f.name for f in dataclasses.fields(PreferencesSchema)}
        assert "fpdf2_hint_shown" in field_names


class TestFpdf2HintShownRoundTrip:
    """The ``fpdf2_hint_shown`` flag round-trips through the preferences file.

    **Validates: Requirements 2.2**

    Mirrors the one-time guard's persistence: from an unset flag, writing
    ``True`` and reloading yields ``True``, and the reloaded preferences pass
    strict schema validation.
    """

    def test_unset_write_true_reload_true_and_validates(self) -> None:
        """Unset -> write True -> reload True -> schema validates.

        **Validates: Requirements 2.2**
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            prefs_path = str(Path(tmp_dir) / "bootcamp_preferences.yaml")

            # Seed only the single required key so the schema can validate as
            # complete; the flag starts unset.
            seed = write_preference(
                "database_type", "sqlite", preferences_path=prefs_path
            )
            assert seed.success, seed.error

            before = load_preferences(preferences_path=prefs_path)
            assert before.preferences is not None
            assert before.preferences.get("fpdf2_hint_shown") is None, (
                "the flag must start unset"
            )

            # Write the flag as the guard would after surfacing the hint.
            result = write_preference(
                "fpdf2_hint_shown", True, preferences_path=prefs_path
            )
            assert result.success, result.error

            after = load_preferences(preferences_path=prefs_path)
            assert after.preferences is not None
            assert after.preferences.get("fpdf2_hint_shown") is True, (
                "the flag must reload as True after being written"
            )

            errors = validate_preferences_schema(after.preferences)
            assert errors == [], f"schema validation errors: {errors}"


def st_hint_flag_value() -> st.SearchStrategy[bool]:
    """Generate a boolean value for the ``fpdf2_hint_shown`` flag.

    Returns:
        A strategy yielding ``True`` or ``False`` — the two persisted states of
        the one-time hint flag.
    """
    return st.booleans()


class TestFpdf2HintShownRoundTripProperties:
    """Any boolean ``fpdf2_hint_shown`` value round-trips and validates.

    **Validates: Requirements 2.2**

    For either boolean value, writing the flag and reloading returns the same
    boolean, and the reloaded preferences pass strict schema validation — so
    the guard state persists faithfully regardless of which value is stored.
    """

    @given(value=st_hint_flag_value())
    def test_bool_flag_roundtrips_and_validates(self, value: bool) -> None:
        """A written boolean flag reloads unchanged and passes validation.

        **Validates: Requirements 2.2**
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            prefs_path = str(Path(tmp_dir) / "bootcamp_preferences.yaml")

            seed = write_preference(
                "database_type", "sqlite", preferences_path=prefs_path
            )
            assert seed.success, seed.error

            result = write_preference(
                "fpdf2_hint_shown", value, preferences_path=prefs_path
            )
            assert result.success, result.error

            loaded = load_preferences(preferences_path=prefs_path)
            assert loaded.preferences is not None
            assert loaded.preferences.get("fpdf2_hint_shown") is value, (
                f"the flag must reload as {value}"
            )

            errors = validate_preferences_schema(loaded.preferences)
            assert errors == [], f"schema validation errors: {errors}"
