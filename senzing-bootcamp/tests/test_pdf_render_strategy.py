"""Behavioral + property tests for the three-tier PDF render strategy.

Feature: guaranteed-recap-pdf

These tests exercise ``pdf_render_strategy`` -- the central tier-selection logic
that guarantees a real ``docs/bootcamp_recap.pdf`` while keeping ``fpdf2`` an
optional, lazily imported dependency:

* **Tier 1 - rich:** ``fpdf2`` importable -> ``generate_recap_pdf.render_pdf``.
* **Tier 2 - autoinstalled:** ``fpdf2`` absent + autoinstall allowed -> a single
  guarded ``pip install fpdf2``; on success (and a successful re-probe) -> rich.
* **Tier 3 - stdlib:** ``fpdf2`` absent + autoinstall disabled/failed/timed out
  -> ``recap_pdf_minimal.render_minimal_pdf`` (the actual guarantee).

Every test monkeypatches the availability probe (``fpdf2_available``) and either
the autoinstall (``attempt_autoinstall``) or the ``subprocess`` call inside it,
so NO real network install is ever performed. The rich renderer is likewise
patched with a spy in selection tests, so these tests never require ``fpdf2`` to
be installed and never skip (except one optional real-rich smoke test that is
skipped when ``fpdf2`` genuinely is not present).

Properties / cases validated (design "Property-Based / Behavioral Tests"):

- Tier selection: present -> "rich"; absent+off -> "stdlib" (NO subprocess);
  absent+on+fail -> "stdlib"; absent+on+success -> "autoinstalled".
- Autoinstall is attempted at most once per invocation.
- The bounded timeout is passed through to the installer, and a simulated
  ``TimeoutExpired`` falls through to the stdlib writer.
- ``resolve_allow_autoinstall``: env var wins over preferences; recognized
  on/off tokens; default enabled when unset.

**Validates: Requirements 7.3, 7.4**
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

# Scripts are not packages; make them importable via the documented sys.path
# pattern (conftest also does this, kept here so the module imports standalone).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import pdf_render_strategy as strategy  # noqa: E402
from generate_recap_pdf import (  # noqa: E402
    QRPair,
    RecapDocument,
    RecapHeader,
    RecapSection,
)

# The autoinstall opt-out tokens the strategy documents as recognized. Restated
# here (rather than imported from the private frozensets) so the tests assert
# the intended vocabulary from Requirement 3.3 independently of the source.
_TRUE_TOKENS = ("1", "true", "yes", "on", "enable", "enabled")
_FALSE_TOKENS = ("0", "false", "no", "off", "disable", "disabled")

# A path guaranteed not to exist, used to force preferences resolution to fall
# through to the default without depending on the current working directory.
_MISSING_PREFS = "/nonexistent/senzing-bootcamp/config/bootcamp_preferences.yaml"


# ---------------------------------------------------------------------------
# Test doubles (spies) -- record calls without touching the network or fpdf2
# ---------------------------------------------------------------------------


class _ProbeSpy:
    """Stateful ``fpdf2_available`` stand-in returning a first/then value.

    The strategy probes availability once up front and, after a successful
    autoinstall, once more. This spy returns ``first`` on the first call and
    ``rest`` on every subsequent call so both the "already present" and
    "install flipped the probe" transitions can be simulated deterministically.
    """

    def __init__(self, first: bool, rest: bool | None = None) -> None:
        """Store the first and subsequent probe results.

        Args:
            first: Result for the first probe call.
            rest: Result for later probe calls (defaults to ``first``).
        """
        self.first = first
        self.rest = first if rest is None else rest
        self.calls = 0

    def __call__(self) -> bool:
        """Return the configured probe result and count the call."""
        self.calls += 1
        return self.first if self.calls == 1 else self.rest


class _AutoinstallSpy:
    """``attempt_autoinstall`` stand-in that never installs anything.

    Records how many times it was called (to assert the at-most-once guarantee)
    and the ``timeout_s`` it received (to assert the bound is threaded through),
    and returns a canned success/failure result.
    """

    def __init__(self, result: bool) -> None:
        """Store the canned install result.

        Args:
            result: The value to return for each call (install success/failure).
        """
        self.result = result
        self.calls = 0
        self.timeouts: list[int] = []

    def __call__(self, timeout_s: int) -> bool:
        """Record the call and requested timeout, returning the canned result."""
        self.calls += 1
        self.timeouts.append(timeout_s)
        return self.result


class _RenderSpy:
    """Renderer stand-in that records calls and writes a tiny valid PDF.

    Matches the ``(doc, out_path, body_text="")`` shape shared by both
    ``render_pdf`` (rich) and ``render_minimal_pdf`` (stdlib) so it can stand in
    for either. Writing minimal ``%PDF-`` bytes keeps any downstream file checks
    happy without depending on ``fpdf2`` or the real writers.
    """

    def __init__(self, *, raises: bool = False) -> None:
        """Configure the spy.

        Args:
            raises: When True, raise ``ImportError`` to simulate a rich-render
                failure so the caller falls through to the stdlib writer.
        """
        self.raises = raises
        self.calls = 0
        self.paths: list[str] = []

    def __call__(self, doc: object, out_path: str, body_text: str = "") -> None:
        """Record the call and (unless configured to raise) write a stub PDF."""
        self.calls += 1
        self.paths.append(str(out_path))
        if self.raises:
            raise ImportError("simulated fpdf2 absence at render time")
        Path(out_path).write_bytes(b"%PDF-1.4\n%%EOF\n")


class _SubprocessRunSpy:
    """``subprocess.run`` stand-in that records calls and never spawns a process.

    Records the argv and ``timeout`` kwarg of each call so the guarded installer
    can be asserted to pass the bounded timeout through, and returns a stub
    result whose ``returncode`` is configurable.
    """

    def __init__(self, returncode: int = 0) -> None:
        """Configure the stub return code.

        Args:
            returncode: The ``returncode`` for the returned stub result.
        """
        self.returncode = returncode
        self.calls = 0
        self.timeouts: list[object] = []
        self.argvs: list[object] = []

    def __call__(self, argv, *args, **kwargs):
        """Record the invocation and return a stub with the configured code."""
        self.calls += 1
        self.argvs.append(argv)
        self.timeouts.append(kwargs.get("timeout"))
        return _StubCompleted(self.returncode)


class _StubCompleted:
    """Minimal stand-in for ``subprocess.CompletedProcess`` (returncode only)."""

    def __init__(self, returncode: int) -> None:
        self.returncode = returncode


def _make_doc() -> RecapDocument:
    """Build a small, valid recap document for rendering through the strategy.

    Returns:
        A single-module ``RecapDocument`` with populated subsections.
    """
    return RecapDocument(
        header=RecapHeader(bootcamper="Ada", started="2025", total_duration="2h"),
        sections=[
            RecapSection(
                module_number=1,
                module_name="BusinessProblem",
                timestamp="2025-01-01",
                information_shared=["shared a dataset"],
                schema="paired",
                qr_pairs=[QRPair(question="why entities", response="because dupes")],
                actions_taken=["ran the demo"],
                duration="45m",
                generic_content=["a freeform note"],
            )
        ],
    )


# ---------------------------------------------------------------------------
# Tier selection (example-based decision table)
# ---------------------------------------------------------------------------


class TestTierSelection:
    """``ensure_recap_pdf`` picks the correct tier for each probe/install state.

    **Validates: Requirements 7.3, 7.4**

    Covers the four documented cases and the at-most-once autoinstall guarantee.
    The rich and stdlib renderers are spied so the assertions are about *which*
    path ran, never about fpdf2 being installed.
    """

    def test_present_returns_rich_and_invokes_rich_renderer(
        self, monkeypatch, tmp_path
    ) -> None:
        """fpdf2 present -> "rich"; rich renderer runs; no autoinstall/stdlib.

        **Validates: Requirements 7.3**
        """
        rich = _RenderSpy()
        stdlib = _RenderSpy()
        autoinstall = _AutoinstallSpy(result=True)
        monkeypatch.setattr(strategy, "fpdf2_available", _ProbeSpy(first=True))
        monkeypatch.setattr(strategy, "render_pdf", rich)
        monkeypatch.setattr(strategy, "render_minimal_pdf", stdlib)
        monkeypatch.setattr(strategy, "attempt_autoinstall", autoinstall)

        out = tmp_path / "recap.pdf"
        tier = strategy.ensure_recap_pdf(
            _make_doc(), out, allow_autoinstall=True, timeout_s=120
        )

        assert tier == strategy.TIER_RICH
        assert rich.calls == 1
        assert autoinstall.calls == 0, "autoinstall must not run when fpdf2 present"
        assert stdlib.calls == 0, "stdlib writer must not run when fpdf2 present"

    def test_absent_autoinstall_disabled_returns_stdlib_no_subprocess(
        self, monkeypatch, tmp_path
    ) -> None:
        """fpdf2 absent + autoinstall off -> "stdlib"; NO subprocess call.

        Uses the *real* ``attempt_autoinstall`` but patches the ``subprocess``
        call it would make, then asserts the short-circuit means the installer
        is never even reached (call count 0).

        **Validates: Requirements 7.4**
        """
        stdlib = _RenderSpy()
        rich = _RenderSpy()
        run_spy = _SubprocessRunSpy(returncode=0)
        monkeypatch.setattr(strategy, "fpdf2_available", _ProbeSpy(first=False))
        monkeypatch.setattr(strategy, "render_minimal_pdf", stdlib)
        monkeypatch.setattr(strategy, "render_pdf", rich)
        monkeypatch.setattr(strategy.subprocess, "run", run_spy)

        out = tmp_path / "recap.pdf"
        tier = strategy.ensure_recap_pdf(
            _make_doc(), out, allow_autoinstall=False, timeout_s=120
        )

        assert tier == strategy.TIER_STDLIB
        assert stdlib.calls == 1, "stdlib writer must produce the PDF"
        assert rich.calls == 0
        assert run_spy.calls == 0, "no pip subprocess when autoinstall is disabled"

    def test_absent_autoinstall_fails_returns_stdlib_attempted_once(
        self, monkeypatch, tmp_path
    ) -> None:
        """fpdf2 absent + autoinstall on + install fails -> "stdlib", tried once.

        **Validates: Requirements 7.4**
        """
        stdlib = _RenderSpy()
        rich = _RenderSpy()
        autoinstall = _AutoinstallSpy(result=False)
        # Probe stays False even after the (failed) install attempt.
        monkeypatch.setattr(strategy, "fpdf2_available", _ProbeSpy(first=False))
        monkeypatch.setattr(strategy, "attempt_autoinstall", autoinstall)
        monkeypatch.setattr(strategy, "render_minimal_pdf", stdlib)
        monkeypatch.setattr(strategy, "render_pdf", rich)

        out = tmp_path / "recap.pdf"
        tier = strategy.ensure_recap_pdf(
            _make_doc(), out, allow_autoinstall=True, timeout_s=120
        )

        assert tier == strategy.TIER_STDLIB
        assert autoinstall.calls == 1, "autoinstall must be attempted at most once"
        assert stdlib.calls == 1
        assert rich.calls == 0

    def test_absent_autoinstall_succeeds_returns_autoinstalled(
        self, monkeypatch, tmp_path
    ) -> None:
        """fpdf2 absent + install succeeds (probe flips) -> "autoinstalled".

        **Validates: Requirements 7.4**
        """
        rich = _RenderSpy()
        stdlib = _RenderSpy()
        autoinstall = _AutoinstallSpy(result=True)
        # Absent on first probe, present on the post-install re-probe.
        probe = _ProbeSpy(first=False, rest=True)
        monkeypatch.setattr(strategy, "fpdf2_available", probe)
        monkeypatch.setattr(strategy, "attempt_autoinstall", autoinstall)
        monkeypatch.setattr(strategy, "render_pdf", rich)
        monkeypatch.setattr(strategy, "render_minimal_pdf", stdlib)

        out = tmp_path / "recap.pdf"
        tier = strategy.ensure_recap_pdf(
            _make_doc(), out, allow_autoinstall=True, timeout_s=120
        )

        assert tier == strategy.TIER_AUTOINSTALLED
        assert autoinstall.calls == 1, "autoinstall must be attempted exactly once"
        assert rich.calls == 1, "rich renderer runs after a successful install"
        assert stdlib.calls == 0

    def test_stdlib_tier_produces_a_real_valid_pdf(
        self, monkeypatch, tmp_path
    ) -> None:
        """Absent + autoinstall off drives the *real* stdlib writer to a %PDF-.

        Exercises the genuine Tier 3 guarantee end to end (no renderer spies):
        with fpdf2 simulated absent and autoinstall disabled, the produced file
        is a structurally valid PDF. Confirms Requirement 7.4's guaranteed PDF.

        **Validates: Requirements 7.4**
        """
        monkeypatch.setattr(strategy, "fpdf2_available", lambda: False)

        out = tmp_path / "recap.pdf"
        tier = strategy.ensure_recap_pdf(
            _make_doc(), out, allow_autoinstall=False, timeout_s=120
        )

        assert tier == strategy.TIER_STDLIB
        data = out.read_bytes()
        assert data.startswith(b"%PDF-"), "stdlib tier must emit a valid PDF header"
        assert data.rstrip().endswith(b"%%EOF"), "stdlib tier PDF missing trailer"

    def test_present_tier_produces_a_real_valid_pdf_when_fpdf2_installed(
        self, tmp_path
    ) -> None:
        """When fpdf2 is genuinely installed, the rich tier yields a valid PDF.

        Skipped when fpdf2 is not importable so the suite never depends on the
        optional dependency; when present, confirms Tier 1 is selected and the
        real ``render_pdf`` produces a valid PDF (Requirement 7.3 unchanged).

        **Validates: Requirements 7.3**
        """
        if not strategy.fpdf2_available():
            pytest.skip("fpdf2 not installed; rich tier smoke test not applicable")

        out = tmp_path / "recap.pdf"
        tier = strategy.ensure_recap_pdf(
            _make_doc(), out, allow_autoinstall=False, timeout_s=120
        )

        assert tier == strategy.TIER_RICH
        assert out.read_bytes().startswith(b"%PDF-")


# ---------------------------------------------------------------------------
# Autoinstall timeout handling
# ---------------------------------------------------------------------------


class TestAutoinstallTimeout:
    """The bounded timeout is honored and a timeout falls through to stdlib.

    **Validates: Requirements 7.4**
    """

    def test_attempt_autoinstall_passes_timeout_to_subprocess(
        self, monkeypatch
    ) -> None:
        """``attempt_autoinstall`` forwards ``timeout_s`` to ``subprocess.run``.

        **Validates: Requirements 7.4**
        """
        run_spy = _SubprocessRunSpy(returncode=0)
        monkeypatch.setattr(strategy.subprocess, "run", run_spy)

        result = strategy.attempt_autoinstall(timeout_s=37)

        assert result is True, "returncode 0 must report install success"
        assert run_spy.calls == 1
        assert run_spy.timeouts == [37], "the bounded timeout must be passed through"

    def test_ensure_recap_pdf_threads_timeout_into_autoinstall(
        self, monkeypatch, tmp_path
    ) -> None:
        """``ensure_recap_pdf`` passes its ``timeout_s`` to the autoinstall.

        **Validates: Requirements 7.4**
        """
        autoinstall = _AutoinstallSpy(result=False)
        monkeypatch.setattr(strategy, "fpdf2_available", _ProbeSpy(first=False))
        monkeypatch.setattr(strategy, "attempt_autoinstall", autoinstall)
        monkeypatch.setattr(strategy, "render_minimal_pdf", _RenderSpy())

        strategy.ensure_recap_pdf(
            _make_doc(), tmp_path / "recap.pdf", allow_autoinstall=True, timeout_s=55
        )

        assert autoinstall.timeouts == [55], "timeout_s must reach attempt_autoinstall"

    def test_timeout_expired_falls_through_to_stdlib(
        self, monkeypatch, tmp_path
    ) -> None:
        """A simulated ``TimeoutExpired`` from pip lands on the stdlib tier.

        Uses the *real* ``attempt_autoinstall`` with ``subprocess.run`` patched to
        raise ``TimeoutExpired``; the guarded installer must swallow it, return
        False, and let the flow fall through to the stdlib writer (no raise).

        **Validates: Requirements 7.4**
        """

        def _raise_timeout(argv, *args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=argv, timeout=kwargs.get("timeout"))

        stdlib = _RenderSpy()
        rich = _RenderSpy()
        monkeypatch.setattr(strategy, "fpdf2_available", _ProbeSpy(first=False))
        monkeypatch.setattr(strategy.subprocess, "run", _raise_timeout)
        monkeypatch.setattr(strategy, "render_minimal_pdf", stdlib)
        monkeypatch.setattr(strategy, "render_pdf", rich)

        out = tmp_path / "recap.pdf"
        tier = strategy.ensure_recap_pdf(
            _make_doc(), out, allow_autoinstall=True, timeout_s=1
        )

        assert tier == strategy.TIER_STDLIB
        assert stdlib.calls == 1, "a pip timeout must fall through to the stdlib tier"
        assert rich.calls == 0


# ---------------------------------------------------------------------------
# resolve_allow_autoinstall (env var wins, tokens, default)
# ---------------------------------------------------------------------------


class TestResolveAllowAutoinstall:
    """Opt-out resolution: env var wins over preferences; tokens; default on.

    **Validates: Requirements 7.4**

    Requirement 3.3 (surfaced by Requirement 7.4's tiered-selection tests):
    resolution consults the ``SENZING_BOOTCAMP_PDF_AUTOINSTALL`` environment
    variable first, then the ``pdf_autoinstall`` preferences key, then defaults
    to enabled.
    """

    def _write_prefs(self, tmp_path: Path, value: str) -> str:
        """Write a preferences file with a ``pdf_autoinstall`` line.

        Args:
            tmp_path: The per-test temporary directory.
            value: The raw YAML value to place after ``pdf_autoinstall:``.

        Returns:
            The path to the written preferences file.
        """
        prefs = tmp_path / "bootcamp_preferences.yaml"
        prefs.write_text(
            f"database_type: sqlite\npdf_autoinstall: {value}\n", encoding="utf-8"
        )
        return str(prefs)

    def test_env_true_wins_over_preferences_false(self, tmp_path) -> None:
        """Env ``on`` overrides a preferences ``false`` -> enabled.

        **Validates: Requirements 7.4**
        """
        prefs_path = self._write_prefs(tmp_path, "false")
        result = strategy.resolve_allow_autoinstall(
            env={strategy.AUTOINSTALL_ENV_VAR: "on"}, preferences_path=prefs_path
        )
        assert result is True

    def test_env_false_wins_over_preferences_true(self, tmp_path) -> None:
        """Env ``off`` overrides a preferences ``true`` -> disabled.

        **Validates: Requirements 7.4**
        """
        prefs_path = self._write_prefs(tmp_path, "true")
        result = strategy.resolve_allow_autoinstall(
            env={strategy.AUTOINSTALL_ENV_VAR: "off"}, preferences_path=prefs_path
        )
        assert result is False

    def test_preferences_used_when_env_unset(self, tmp_path) -> None:
        """With the env var unset, the preferences key decides.

        **Validates: Requirements 7.4**
        """
        assert (
            strategy.resolve_allow_autoinstall(
                env={}, preferences_path=self._write_prefs(tmp_path, "false")
            )
            is False
        )
        assert (
            strategy.resolve_allow_autoinstall(
                env={}, preferences_path=self._write_prefs(tmp_path, "true")
            )
            is True
        )

    def test_default_enabled_when_env_and_preferences_absent(self) -> None:
        """Unset env + missing preferences file -> default enabled.

        **Validates: Requirements 7.4**
        """
        result = strategy.resolve_allow_autoinstall(
            env={}, preferences_path=_MISSING_PREFS
        )
        assert result is True

    def test_unrecognized_env_token_falls_through_to_default(self) -> None:
        """An unrecognized env token is ignored, leaving the default enabled.

        **Validates: Requirements 7.4**
        """
        result = strategy.resolve_allow_autoinstall(
            env={strategy.AUTOINSTALL_ENV_VAR: "maybe"}, preferences_path=_MISSING_PREFS
        )
        assert result is True

    @given(token=st.sampled_from(_TRUE_TOKENS), upper=st.booleans())
    def test_recognized_true_tokens_enable(self, token: str, upper: bool) -> None:
        """Every recognized on-token (any case) resolves to enabled.

        **Validates: Requirements 7.4**
        """
        value = token.upper() if upper else token
        result = strategy.resolve_allow_autoinstall(
            env={strategy.AUTOINSTALL_ENV_VAR: value}, preferences_path=_MISSING_PREFS
        )
        assert result is True

    @given(token=st.sampled_from(_FALSE_TOKENS), upper=st.booleans())
    def test_recognized_false_tokens_disable(self, token: str, upper: bool) -> None:
        """Every recognized off-token (any case) resolves to disabled.

        **Validates: Requirements 7.4**
        """
        value = token.upper() if upper else token
        result = strategy.resolve_allow_autoinstall(
            env={strategy.AUTOINSTALL_ENV_VAR: value}, preferences_path=_MISSING_PREFS
        )
        assert result is False


# ---------------------------------------------------------------------------
# Property: tier selection matches the decision table for all state combos
# ---------------------------------------------------------------------------


class TestTierSelectionProperties:
    """Across all probe/install/opt-out combinations the tier is well-defined.

    **Validates: Requirements 7.3, 7.4**

    For any combination of (fpdf2 initially present, autoinstall allowed, install
    success, probe result after install), ``ensure_recap_pdf`` returns exactly the
    tier the documented decision table prescribes and never attempts autoinstall
    more than once.
    """

    @given(
        present_initial=st.booleans(),
        allow_autoinstall=st.booleans(),
        install_success=st.booleans(),
        present_after=st.booleans(),
        timeout_s=st.integers(min_value=1, max_value=600),
    )
    def test_decision_table_holds(
        self,
        present_initial: bool,
        allow_autoinstall: bool,
        install_success: bool,
        present_after: bool,
        timeout_s: int,
    ) -> None:
        """The returned tier and autoinstall call count follow the table.

        **Validates: Requirements 7.3, 7.4**
        """
        rich = _RenderSpy()
        stdlib = _RenderSpy()
        autoinstall = _AutoinstallSpy(result=install_success)
        probe = _ProbeSpy(first=present_initial, rest=present_after)

        # A fresh temp dir per example (rather than the function-scoped tmp_path
        # fixture, which Hypothesis flags as not reset between inputs). The
        # module-level renderers are swapped with spies and restored in the
        # finally block so no state leaks between generated examples.
        saved = {
            "fpdf2_available": strategy.fpdf2_available,
            "attempt_autoinstall": strategy.attempt_autoinstall,
            "render_pdf": strategy.render_pdf,
            "render_minimal_pdf": strategy.render_minimal_pdf,
        }
        strategy.fpdf2_available = probe
        strategy.attempt_autoinstall = autoinstall
        strategy.render_pdf = rich
        strategy.render_minimal_pdf = stdlib
        try:
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "recap.pdf"
                tier = strategy.ensure_recap_pdf(
                    _make_doc(),
                    out,
                    allow_autoinstall=allow_autoinstall,
                    timeout_s=timeout_s,
                )
        finally:
            for name, value in saved.items():
                setattr(strategy, name, value)

        if present_initial:
            expected_tier = strategy.TIER_RICH
            expected_attempts = 0
        elif allow_autoinstall and install_success and present_after:
            expected_tier = strategy.TIER_AUTOINSTALLED
            expected_attempts = 1
        else:
            expected_tier = strategy.TIER_STDLIB
            expected_attempts = 1 if allow_autoinstall else 0

        assert tier == expected_tier
        assert autoinstall.calls == expected_attempts, (
            "autoinstall must run at most once and only when reached"
        )
        assert autoinstall.calls <= 1, "autoinstall must never retry"
