"""Steering-structure and non-blocking-fallback tests for the Load_Time_Warning.

Feature: module4-sqlite-load-time-warning

This module holds the example/structural tests for the Module 4 SQLite
Load_Time_Warning that are not universal properties:

- ``TestNonBlockingFallback`` (task 12.4) - the ``load_time_warning.main`` CLI
  diagnostic is non-blocking: an uncomputable/unreadable registry drives the
  collected total to ``None`` so the trigger is ``False``, and ``main`` reports
  "continue" and returns 0 without raising (Requirements 7.5, 8.3).

Later tasks (12.2, 12.3) add a ``TestSteeringStructure`` class to this same
file covering the Module 4 / Module 6 steering-block wiring; the imports and
``sys.path`` setup below are shared, so that class can simply be appended.
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts are not a package)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import load_time_warning  # noqa: E402  (path manipulated above)

# The exact "continue" wording main emits on every non-warning path
# (see load_time_warning._print_continue_report).
_CONTINUE_TEXT = "No load-time warning -- continue"


class TestNonBlockingFallback:
    """The CLI diagnostic never blocks when the registry is uncomputable.

    Validates: Requirements 7.5, 8.3
    """

    def test_missing_registry_and_preferences_report_continue(self, tmp_path, capsys):
        """A nonexistent registry + preferences -> total None -> "continue", exit 0.

        With no registry to parse, the collected total is indeterminate
        (``None``), so ``should_warn_load_time`` is ``False`` and ``main`` prints
        the non-blocking "continue" report and returns 0 without raising
        (Requirements 7.5, 8.3).
        """
        missing_registry = tmp_path / "no_such_registry.yaml"
        missing_preferences = tmp_path / "no_such_preferences.yaml"

        exit_code = load_time_warning.main(
            [
                "--registry",
                str(missing_registry),
                "--preferences",
                str(missing_preferences),
            ]
        )

        assert exit_code == 0
        out = capsys.readouterr().out
        assert _CONTINUE_TEXT in out
        # The indeterminate total must be surfaced, never a fabricated number.
        assert "Collected total: indeterminate" in out

    def test_malformed_registry_reports_continue(self, tmp_path, capsys):
        """A garbage registry file still yields "continue" and exit 0 (no raise).

        A malformed/unparseable registry cannot produce a determinate total, so
        the trigger stays ``False`` and the flow continues non-blocking
        (Requirements 7.5, 8.3).
        """
        garbage_registry = tmp_path / "garbage_registry.yaml"
        garbage_registry.write_text(
            "\x00 not: [valid: yaml : : :\n\tgarbage ]]]{{{\n",
            encoding="utf-8",
        )
        missing_preferences = tmp_path / "no_such_preferences.yaml"

        exit_code = load_time_warning.main(
            [
                "--registry",
                str(garbage_registry),
                "--preferences",
                str(missing_preferences),
            ]
        )

        assert exit_code == 0
        assert _CONTINUE_TEXT in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Shared paths for the steering-structure tests (tasks 12.2, 12.3)
# ---------------------------------------------------------------------------
_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_MODULE_04_STEERING = _STEERING_DIR / "module-04-data-collection.md"
_MODULE_06_STEERING = _STEERING_DIR / "module-06-phaseA-build-loading.md"
_LOAD_TIME_WARNING_SCRIPT = Path(_SCRIPTS_DIR) / "load_time_warning.py"

# The no-entry glyph used across the steering files to mark a Mandatory_Gate.
_GATE_MARKER = "\u26d4"  # ⛔


class TestSteeringStructure:
    """Structural tests over the Module 4 SQLite Load_Time_Warning wiring.

    These read the steering markdown and the ``load_time_warning`` source and
    assert on their content: the "8b. SQLite Load-Time Warning" block sits
    between Step 8a (record-count back-fill) and the Step 9 transition, asks the
    sampling sub-choice before creating a sample, obtains an explicit
    confirmation on the load-all path, frames the concern distinctly from the
    license-capacity sampling framing (while still listing sampling as one
    option), stays a heads-up rather than a Mandatory_Gate, and reuses the
    sibling helpers rather than re-deriving record counts or tiers.

    Validates: Requirements 4.4, 5.1, 5.3, 7.3, 7.4
    """

    # -- helpers ------------------------------------------------------------

    def _module4_text(self) -> str:
        """Return the Module 4 steering file text."""
        return _MODULE_04_STEERING.read_text(encoding="utf-8")

    def _load_time_block(self, content: str) -> str:
        """Return the "8b" block: from its heading up to the Step 9 transition."""
        start = content.index("SQLite Load-Time Warning")
        end = content.index("Transition to Module 5")
        assert start < end, "Step 9 transition must follow the 8b heading"
        return content[start:end]

    def _module6_text(self) -> str:
        """Return the Module 6 Phase A steering file text."""
        return _MODULE_06_STEERING.read_text(encoding="utf-8")

    def _already_decided_step(self, content: str) -> str:
        """Return the Module 6 pre-load ``already_decided`` computation (step 2).

        Slices from the "Compute ``already_decided``" heading up to the step 3
        "Call the predicate" heading so the assertions see the whole
        marker-derivation step and nothing after it.
        """
        start = content.index("Compute `already_decided`")
        end = content.index("Call the predicate", start)
        assert start < end, "step 3 (call the predicate) must follow the already_decided step"
        return content[start:end]

    # -- tests --------------------------------------------------------------

    def test_block_appears_after_step_8a_and_before_step_9(self):
        """The 8b block sits after Step 8a back-fill and before the Step 9 move.

        Compares string indices so the collection-time heads-up is evaluated
        once the record-count back-fill has run and before the transition to
        Module 5 (design: "placed after Step 8a and before the Step 9
        transition").
        """
        content = self._module4_text()
        idx_step_8a = content.index("Record-count license back-fill")
        idx_step_8b = content.index("SQLite Load-Time Warning")
        idx_step_9 = content.index("Transition to Module 5")
        assert idx_step_8a < idx_step_8b < idx_step_9

    def test_asks_sampling_subchoice_before_creating_the_sample(self):
        """The Sampling_Strategy ask precedes validating/writing the sample.

        Requirement 5.1: ask which Sampling_Strategy to use before creating the
        sample. The strategy ask must appear before the target validation and
        before the sample is written under ``data/samples/``. Requirements 5.2 /
        5.3: the named first-N / random-N / ER-demonstrating strategies are
        offered and a bootcamper-described strategy is accepted.
        """
        block = self._load_time_block(self._module4_text())

        ask_idx = block.index("Sampling_Strategy")
        # Ask the sub-choice before validating the target and before writing.
        assert ask_idx < block.index("validate_sample_target")
        assert ask_idx < block.index("write_sample")
        assert ask_idx < block.index("data/samples/")

        # The three named strategies are offered (Req 5.2) ...
        assert "first-N records" in block
        assert "random-N records" in block
        assert "entity-resolution-demonstrating" in block
        # ... and a bootcamper-described strategy is accepted (Req 5.3).
        assert "bootcamper-described strategy" in block

    def test_load_all_path_obtains_explicit_confirmation(self):
        """The load-all path confirms the accepted load time first (Req 4.4)."""
        block = self._load_time_block(self._module4_text())
        assert "explicit confirmation" in block
        assert "accepts the expected load time" in block

    def test_concern_is_distinct_from_license_capacity_framing(self):
        """The heads-up is framed distinctly from license-capacity sampling.

        Requirement 7.3: present the time/performance concern as distinct from
        the license-capacity sampling framing already in the module, while
        keeping sampling available as one option among proceeding and switching
        databases.
        """
        block = self._load_time_block(self._module4_text())
        assert "distinct" in block
        assert "license-capacity sampling framing" in block
        # Sampling is still listed as one option, not the only path.
        assert "one option" in block

    def test_block_is_a_heads_up_not_a_mandatory_gate(self):
        """The block is a heads-up, never a Mandatory_Gate (Req 4.5).

        It explicitly disclaims the gate marker rather than using it to block
        the flow: the only ⛔ occurrence is the "there is no ⛔" statement.
        """
        block = self._load_time_block(self._module4_text())
        assert "NOT a Mandatory_Gate" in block
        assert "heads-up" in block
        # The single gate glyph present is the explicit disclaimer, never a gate.
        assert block.count(_GATE_MARKER) == 1
        assert f"there is no {_GATE_MARKER}" in block

    def test_load_time_warning_reuses_sibling_helpers(self):
        """``load_time_warning.py`` imports its four siblings (Req 7.4).

        Reuse -- not parallel record-count/tier logic: the module imports
        ``volume_utils``, ``preferences_utils``, ``record_count_backfill``, and
        ``data_sources`` rather than re-deriving their behavior.
        """
        source = _LOAD_TIME_WARNING_SCRIPT.read_text(encoding="utf-8")
        for module in (
            "volume_utils",
            "preferences_utils",
            "record_count_backfill",
            "data_sources",
        ):
            assert f"import {module}" in source, (
                f"expected 'import {module}' in load_time_warning.py (reuse, "
                f"no parallel logic)"
            )

    def test_module6_already_decided_ors_in_module4_decision(self):
        """Module 6 ORs a Module 4 decision into ``already_decided`` (Req 6.3).

        The Module 6 Phase A pre-load check must *additively* OR
        ``module4_decision_applies`` alongside its existing tier/raw_value
        match: a Module 4 Load-Time-Warning decision recorded for the current
        load on SQLite suppresses the redundant Module 6 re-prompt, while the
        two branches remain an either/or relationship rather than one replacing
        the other. Asserting on the ``already_decided`` step (Requirement 6.3).
        """
        step = self._already_decided_step(self._module6_text())

        # The Module 4 honor-decision predicate is referenced ...
        assert "module4_decision_applies" in step
        assert "compute_load_identity" in step

        # ... additively alongside the *existing* Module 6 tier/raw_value match:
        # both named branches are present, so neither replaces the other.
        assert "tier" in step
        assert "raw_value" in step
        assert "match" in step
        assert "Existing Module 6 match" in step
        assert "Applicable Module 4 decision" in step

        # ... and the text conveys an OR / either-branch (additive) relationship.
        assert "OR" in step or "either" in step
