"""Property-based tests for the Question_Ledger helper (``question_ledger.py``).

These tests exercise the durable "ask each question at most once" ledger helper:
idempotent record, answer-supersedes-asked, malformed-file tolerance, and the
record -> mark-answered -> query round-trip.

Validates: Requirements 6.1 (property-based tests for the ledger helper covering
idempotent record/answer/query operations and malformed-file tolerance).
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Repo Test Pattern: scripts/ is not a package, so import via sys.path.
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import question_ledger as ql  # noqa: E402  (import after sys.path manipulation)


# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------

# Segment characters for onboarding/global names: lowercase, digits, underscore.
_NAME_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789_"
# Step suffix characters for module keys (e.g. "7a", "12", "3b").
_STEP_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"

# A key that the generators below can never produce (too long / not a real
# scheme value), safe to use as a "definitely absent" sentinel.
_ABSENT_KEY = "global.__never_recorded_sentinel_key__"


@st.composite
def st_question_key(draw) -> str:
    """Draw a valid Question_Key following the design's key scheme.

    Produces one of the three stable key shapes defined in the design:
    ``onboarding.<step>``, ``module.<N>.<step>``, or ``global.<name>``. All are
    non-empty strings that survive a JSON round-trip.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A valid Question_Key string.
    """
    kind = draw(st.sampled_from(("onboarding", "module", "global")))
    if kind == "onboarding":
        step = draw(st.text(alphabet=_NAME_ALPHABET, min_size=1, max_size=16))
        return f"onboarding.{step}"
    if kind == "module":
        number = draw(st.integers(min_value=1, max_value=12))
        step = draw(st.text(alphabet=_STEP_ALPHABET, min_size=1, max_size=4))
        return f"module.{number}.{step}"
    name = draw(st.text(alphabet=_NAME_ALPHABET, min_size=1, max_size=16))
    return f"global.{name}"


# Arbitrary single-line junk for the malformed-tolerance property. Excludes
# newlines (so each drawn value is exactly one physical line) and surrogates.
_JUNK_LINE = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\n\r"),
    max_size=48,
)


# ---------------------------------------------------------------------------
# Per-example ledger path helper (tempfile, never touches real config/)
# ---------------------------------------------------------------------------


def _fresh_ledger() -> tuple[Path, Path]:
    """Create a throwaway directory and return ``(dir, ledger_path)``.

    Each property example gets its own directory so ledger state never leaks
    between examples and the real ``config/`` directory is never touched.

    Returns:
        A tuple of (temp directory path, ledger file path within it).
    """
    base = Path(tempfile.mkdtemp(prefix="qledger_test_"))
    return base, base / "question_ledger.jsonl"


def _nonempty_lines(path: Path) -> list[str]:
    """Return the non-blank physical lines of a ledger file."""
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------


class TestQuestionLedgerProperties:
    """Property-based coverage of the ledger helper.

    Validates: Requirements 6.1 (idempotent record/answer/query and
    malformed-file tolerance), supporting 5.3 (idempotency) and 5.4
    (malformed tolerance).
    """

    @given(key=st_question_key(), times=st.integers(min_value=1, max_value=6))
    def test_record_asked_is_idempotent(self, key: str, times: int) -> None:
        """Recording the same asked key N times yields exactly one asked entry.

        Querying is stable: repeated queries return the same result.

        Validates: Requirements 6.1, 5.3
        """
        base, ledger = _fresh_ledger()
        try:
            for _ in range(times):
                ql.record_asked(key, ledger)

            lines = _nonempty_lines(ledger)
            assert len(lines) == 1
            obj = json.loads(lines[0])
            assert obj["key"] == key
            assert obj["status"] == "asked"

            # Querying is stable across repeated calls.
            assert ql.is_answered(key, ledger) is False
            assert ql.is_answered(key, ledger) is False
            assert ql.get_pending(ledger) == [key]
            assert ql.get_pending(ledger) == [key]
        finally:
            shutil.rmtree(base, ignore_errors=True)

    @given(key=st_question_key(), pre_asks=st.integers(min_value=0, max_value=5))
    def test_answer_supersedes_asked(self, key: str, pre_asks: int) -> None:
        """After mark-answered, is-answered is True regardless of prior asks.

        A subsequent record-asked must never regress an answered key back to
        pending.

        Validates: Requirements 6.1, 5.3
        """
        base, ledger = _fresh_ledger()
        try:
            for _ in range(pre_asks):
                ql.record_asked(key, ledger)

            ql.mark_answered(key, ledger)
            assert ql.is_answered(key, ledger) is True

            # answered supersedes asked: re-recording does not regress it.
            ql.record_asked(key, ledger)
            assert ql.is_answered(key, ledger) is True
            assert ql.get_pending(ledger) == []
        finally:
            shutil.rmtree(base, ignore_errors=True)

    @given(junk=st.lists(_JUNK_LINE, min_size=1, max_size=10), key=st_question_key())
    def test_malformed_file_tolerated_then_rewritten_clean(
        self, junk: list[str], key: str
    ) -> None:
        """A junk-seeded ledger reads without raising; a write cleans it up.

        Reading a file full of malformed lines returns a (possibly empty)
        mapping without raising. A subsequent write recreates a valid JSONL
        file whose every line is a well-formed entry.

        Validates: Requirements 6.1, 5.4
        """
        base, ledger = _fresh_ledger()
        try:
            ledger.write_text("\n".join(junk) + "\n", encoding="utf-8")

            # Reading tolerates the junk without raising.
            state = ql.read_state(ledger)
            assert isinstance(state, dict)

            # A subsequent write produces a valid, parseable ledger file.
            ql.record_asked(key, ledger)
            for line in _nonempty_lines(ledger):
                obj = json.loads(line)  # must parse as JSON
                assert isinstance(obj, dict)
                assert {"key", "status", "ts"} <= set(obj)
                assert obj["status"] in ql.VALID_STATUSES
                assert isinstance(obj["key"], str) and obj["key"]

            # The recorded key is present after the clean rewrite.
            assert key in ql.read_state(ledger)
        finally:
            shutil.rmtree(base, ignore_errors=True)

    @given(keys=st.lists(st_question_key(), min_size=0, max_size=8, unique=True))
    def test_round_trip_record_answer_query(self, keys: list[str]) -> None:
        """record -> mark-answered -> is-answered holds for arbitrary key sets.

        Every recorded-and-answered key reports answered; a key that was never
        recorded reports not-answered; nothing remains pending.

        Validates: Requirements 6.1
        """
        base, ledger = _fresh_ledger()
        try:
            for key in keys:
                ql.record_asked(key, ledger)
            for key in keys:
                ql.mark_answered(key, ledger)

            for key in keys:
                assert ql.is_answered(key, ledger) is True

            # A never-recorded key is not answered.
            assert ql.is_answered(_ABSENT_KEY, ledger) is False
            # All keys are answered, so none remain pending.
            assert ql.get_pending(ledger) == []
        finally:
            shutil.rmtree(base, ignore_errors=True)


# ---------------------------------------------------------------------------
# Focused example-based unit tests (core functional logic + CLI exit codes)
# ---------------------------------------------------------------------------


class TestQuestionLedgerUnit:
    """Example-based checks for edge cases and the CLI contract.

    Validates: Requirements 5.4 (missing-file tolerance) and 5.1/5.2 (CLI
    operations and exit-code contract).
    """

    def test_missing_file_reads_as_empty(self, tmp_path):
        """Reading a nonexistent ledger yields an empty state without raising."""
        ledger = tmp_path / "does_not_exist.jsonl"
        assert ql.read_state(ledger) == {}
        assert ql.is_answered("onboarding.language_selection", ledger) is False
        assert ql.get_pending(ledger) == []

    def test_mark_answered_on_absent_key_creates_answered(self, tmp_path):
        """mark-answered on a never-asked key records it directly as answered."""
        ledger = tmp_path / "question_ledger.jsonl"
        ql.mark_answered("global.hardware_target", ledger)
        assert ql.is_answered("global.hardware_target", ledger) is True
        assert ql.get_pending(ledger) == []

    def test_cli_record_then_is_answered_exit_codes(self, tmp_path, monkeypatch):
        """CLI round-trip: record-asked (0), is-answered pending (1), answered (0)."""
        monkeypatch.chdir(tmp_path)  # ledger resolves under tmp_path/config/
        key = "onboarding.track_selection"

        assert ql.main(["record-asked", "--key", key]) == 0
        # Recorded but not answered -> exit 1.
        assert ql.main(["is-answered", "--key", key]) == 1

        assert ql.main(["mark-answered", "--key", key]) == 0
        # Now answered -> exit 0.
        assert ql.main(["is-answered", "--key", key]) == 0

        # The ledger was created under config/, not the real config directory.
        assert (tmp_path / "config" / "question_ledger.jsonl").exists()

    def test_cli_is_answered_unknown_key_exit_one(self, tmp_path, monkeypatch):
        """is-answered on an unknown key exits 1 (not answered)."""
        monkeypatch.chdir(tmp_path)
        assert ql.main(["is-answered", "--key", "module.9.9z"]) == 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
