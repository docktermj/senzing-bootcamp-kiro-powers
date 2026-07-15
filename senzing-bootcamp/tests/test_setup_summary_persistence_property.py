"""Property-based tests for setup_summary persistence.

Feature: setup-summary-persistence

Covers Task 5 (optional tests) — the design's five correctness properties for
persisting and replaying the ``setup_summary`` block in the Progress_File:

- **P1 (fidelity):** each persisted field equals the corresponding real
  onboarding outcome; no field is fabricated.
- **P2 (additive):** writing ``setup_summary`` preserves every other
  Progress_File key byte-for-byte except the added block.
- **P3 (secret-free):** the block never contains secrets/tokens/connection
  strings.
- **P4 (backward compatible):** resume works whether or not ``setup_summary``
  exists; absence is never an error.
- **P5 (non-blocking):** a write or read failure never blocks onboarding or
  resume.

Design reality — no dedicated Python function exists
----------------------------------------------------
The write path (onboarding §4.0) and the replay path (``session-resume.md``) are
implemented as *steering instructions* (agent behavior in Markdown), not as new
Python functions. The design says onboarding reuses the existing progress
read-modify-write discipline already in ``progress_utils.py`` (the same pattern
``write_checkpoint`` uses). These tests therefore exercise the real code seams
that back that behavior:

- ``_read_progress`` / ``_write_progress`` — the read-modify-write primitives the
  steering directive reuses. ``_merge_setup_summary`` below is a faithful,
  minimal model of the §4.0 write (mirroring ``write_checkpoint``'s
  read-modify-write), used to demonstrate P1/P2.
- ``validate_progress_schema`` — the light ``setup_summary`` validation added in
  Task 4, used for the P3 secret-free rule and P4 (an absent block is valid).

P5's "non-blocking" guarantee is, at its outer edge, a steering-level behavior
(the agent must catch a write/read error and continue). It is modeled here by the
thin ``_safe_write_setup_summary`` / ``_safe_read_setup_summary`` wrappers, which
represent exactly what the steering prescribes and let us assert the contract at
the code-level seam that exists: a failure is caught (never propagated) and
existing progress state is never corrupted.

Example counts come from the active Hypothesis profile baseline (see repo-root
``hypothesis_profiles.py`` / ``conftest.py``); no per-test ``@settings`` override
is used.

Requirements: 1.2, 1.3, 1.5, 2.3, 2.4, 3.1, 3.2
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ and sibling test modules importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from progress_utils import (  # noqa: E402
    _SECRET_LIKE_KEY_SUBSTRINGS,
    VALID_PREFLIGHT_VERDICTS,
    _read_progress,
    _write_progress,
    validate_progress_schema,
)

# Reuse the existing, well-tested valid-progress strategy rather than
# reinventing it. It never emits a ``setup_summary`` key, which is exactly the
# "existing Progress_File" precondition P2/P4 need.
from test_progress_schema_validation_properties import st_progress_file  # noqa: E402

# ═══════════════════════════════════════════════════════════════════════════
# Models of the steering-prescribed write / replay behavior
# ═══════════════════════════════════════════════════════════════════════════


def _merge_setup_summary(progress_path: str, setup_summary: dict) -> None:
    """Additively merge ``setup_summary`` into the Progress_File.

    Faithful model of the onboarding §4.0 write directive: a read-modify-write
    that mirrors ``progress_utils.write_checkpoint`` — read the whole file,
    set exactly one key, write the whole file back. Every other key is left
    untouched.

    Args:
        progress_path: Path to the progress JSON file.
        setup_summary: The block to persist under the ``setup_summary`` key.
    """
    data = _read_progress(progress_path)
    data["setup_summary"] = setup_summary
    _write_progress(progress_path, data)


def _safe_write_setup_summary(
    progress_path: str,
    setup_summary: dict,
    *,
    writer: Callable[[str, dict], None] = _write_progress,
) -> bool:
    """Non-blocking additive write (model of the §4.0 "if the merge fails" rule).

    Wraps the read-modify-write so that an I/O failure is caught and reported
    rather than propagated — onboarding continues and the summary stays a
    presentation-only artifact for the session. Because the write is the final
    step, a failing ``writer`` leaves the existing on-disk state untouched.

    Args:
        progress_path: Path to the progress JSON file.
        setup_summary: The block to persist.
        writer: The write primitive; injectable so a failure can be simulated.

    Returns:
        ``True`` when the block was persisted, ``False`` when the write failed
        (in which case no exception escapes and existing state is preserved).
    """
    try:
        data = _read_progress(progress_path)
        data["setup_summary"] = setup_summary
        writer(progress_path, data)
        return True
    except OSError:
        return False


def _safe_read_setup_summary(
    progress_path: str,
    *,
    reader: Callable[[str], dict] = _read_progress,
) -> dict | None:
    """Non-blocking replay read (model of the ``session-resume.md`` directive).

    Reads the persisted ``setup_summary`` for replay. A missing block yields
    ``None`` (backward compatible), and a read failure (missing/corrupt file)
    is caught and also yields ``None`` so resume proceeds unchanged.

    Args:
        progress_path: Path to the progress JSON file.
        reader: The read primitive; injectable so a failure can be simulated.

    Returns:
        The persisted ``setup_summary`` dict, or ``None`` when it is absent or
        cannot be read.
    """
    try:
        data = reader(progress_path)
    except (OSError, ValueError):
        # ValueError covers json.JSONDecodeError from a corrupt progress file.
        return None
    summary = data.get("setup_summary")
    return summary if isinstance(summary, dict) else None


def _raising_writer(progress_path: str, data: dict) -> None:
    """A write primitive that always fails, simulating an I/O error.

    Args:
        progress_path: Ignored.
        data: Ignored.

    Raises:
        OSError: Always, to model an unwritable target (disk full, permission
            denied, read-only filesystem, ...).
    """
    raise OSError("simulated write failure")


@contextmanager
def _temp_dir() -> Iterator[Path]:
    """Yield a fresh temporary directory, removed on exit.

    Used instead of the function-scoped ``tmp_path`` fixture because these are
    ``@given`` property tests: each example needs its own throwaway directory,
    matching the ``tempfile`` pattern already used elsewhere in this suite.

    Yields:
        The path to a new temporary directory.
    """
    directory = tempfile.mkdtemp()
    try:
        yield Path(directory)
    finally:
        shutil.rmtree(directory, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════════════
# Strategies
# ═══════════════════════════════════════════════════════════════════════════

_TOKEN = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P")),
    min_size=1,
    max_size=24,
)
_STRING_LIST = st.lists(_TOKEN, max_size=5)


@st.composite
def st_setup_summary(draw) -> dict:
    """Draw a well-formed, secret-free ``setup_summary`` block.

    Every field is optional (validation is "light"), so a random subset is
    included on each draw — from an empty block up to the full documented shape.
    All values honor the schema: booleans for flags, a verdict from
    :data:`VALID_PREFLIGHT_VERDICTS`, arrays of strings, and a non-negative int
    hook ``count``. No key resembles a secret, token, or connection string.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A schema-valid ``setup_summary`` dict.
    """
    summary: dict = {}

    if draw(st.booleans()):
        summary["captured_at"] = draw(st.datetimes()).isoformat()
    if draw(st.booleans()):
        summary["power_version"] = draw(_TOKEN)
    if draw(st.booleans()):
        summary["mcp_reachable"] = draw(st.booleans())
    if draw(st.booleans()):
        summary["directories_created"] = draw(st.booleans())
    if draw(st.booleans()):
        summary["hooks_installed"] = {
            "count": draw(st.integers(min_value=0, max_value=50)),
            "names": draw(_STRING_LIST),
        }
    if draw(st.booleans()):
        summary["steering_generated"] = draw(_STRING_LIST)
    if draw(st.booleans()):
        summary["preflight_verdict"] = draw(st.sampled_from(VALID_PREFLIGHT_VERDICTS))
    if draw(st.booleans()):
        summary["preflight_warnings"] = draw(_STRING_LIST)
    if draw(st.booleans()):
        summary["deferrals"] = draw(_STRING_LIST)

    return summary


@st.composite
def st_progress_without_summary(draw) -> dict:
    """Draw a valid Progress_File dict that has no ``setup_summary`` key.

    Thin wrapper over the shared :func:`st_progress_file` strategy documenting
    the precondition the additive/backward-compatibility properties rely on:
    the existing file predates (or simply lacks) the block.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A valid progress dict without a ``setup_summary`` key.
    """
    progress = draw(st_progress_file())
    progress.pop("setup_summary", None)
    return progress


@st.composite
def st_secret_key(draw) -> str:
    """Draw a key name guaranteed to trip the secret-free rule.

    Embeds one of the forbidden substrings (secret, token, password, api_key,
    connection, ...) inside optional lowercase padding, so the resulting key is
    always flagged by ``validate_progress_schema`` regardless of surrounding
    characters or case.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A key name containing a secret-like substring.
    """
    substring = draw(st.sampled_from(_SECRET_LIKE_KEY_SUBSTRINGS))
    pad = st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", max_size=6)
    prefix = draw(pad)
    suffix = draw(pad)
    casing = draw(st.sampled_from(["lower", "upper", "title"]))
    core = substring
    if casing == "upper":
        core = substring.upper()
    elif casing == "title":
        core = substring.capitalize()
    return f"{prefix}{core}{suffix}"


# ═══════════════════════════════════════════════════════════════════════════
# P1 — Fidelity
# ═══════════════════════════════════════════════════════════════════════════


class TestSetupSummaryFidelity:
    """P1: persisted fields equal the real outcomes; nothing is fabricated.

    Validates: Requirements 1.2, 3.2
    """

    @given(progress=st_progress_without_summary(), summary=st_setup_summary())
    def test_persisted_block_equals_source_outcomes(self, progress, summary):
        """Reading the block back reproduces the source outcomes exactly.

        The persisted ``setup_summary`` equals the object assembled from the
        onboarding outcomes field-for-field — no field is added, dropped, or
        altered through the write/read round-trip.

        **Validates: Requirements 1.2**
        """
        with _temp_dir() as directory:
            path = str(directory / "bootcamp_progress.json")
            _write_progress(path, progress)
            _merge_setup_summary(path, summary)

            reloaded = _read_progress(path)
            assert reloaded["setup_summary"] == summary
            assert set(reloaded["setup_summary"]) == set(summary)

    @given(progress=st_progress_without_summary(), summary=st_setup_summary())
    def test_persisted_block_is_schema_valid(self, progress, summary):
        """A block built only from legitimate outcomes validates cleanly.

        Because the block carries only real onboarding fields (no fabricated,
        secret-like keys), the merged Progress_File passes schema validation.

        **Validates: Requirements 1.2, 3.2**
        """
        merged = dict(progress)
        merged["setup_summary"] = summary
        assert validate_progress_schema(merged) == []


# ═══════════════════════════════════════════════════════════════════════════
# P2 — Additive
# ═══════════════════════════════════════════════════════════════════════════


class TestSetupSummaryAdditive:
    """P2: writing the block preserves every other key byte-for-byte.

    Validates: Requirements 1.3
    """

    @given(progress=st_progress_without_summary(), summary=st_setup_summary())
    def test_other_keys_preserved_byte_for_byte(self, progress, summary):
        """Only ``setup_summary`` is added; all other keys are byte-identical.

        Serializing the post-write file with the added block stripped yields the
        exact bytes of the original file, and the only new key is
        ``setup_summary`` (appended last, so prior key order is preserved).

        **Validates: Requirements 1.3**
        """
        with _temp_dir() as directory:
            path = str(directory / "bootcamp_progress.json")
            _write_progress(path, progress)
            original_bytes = Path(path).read_bytes()

            _merge_setup_summary(path, summary)
            reloaded = _read_progress(path)

            # Exactly one key was added.
            assert set(reloaded) - set(progress) == {"setup_summary"}
            assert set(progress) - set(reloaded) == set()
            assert reloaded["setup_summary"] == summary

            # Every other key is unchanged in value and order.
            without_block = {k: v for k, v in reloaded.items() if k != "setup_summary"}
            assert without_block == progress
            assert list(without_block.keys()) == list(progress.keys())

            # Byte-for-byte: re-serializing the surviving keys with the same
            # writer reproduces the original file exactly.
            other_path = str(directory / "other.json")
            _write_progress(other_path, without_block)
            assert Path(other_path).read_bytes() == original_bytes


# ═══════════════════════════════════════════════════════════════════════════
# P3 — Secret-free
# ═══════════════════════════════════════════════════════════════════════════


class TestSetupSummarySecretFree:
    """P3: the block never contains secrets/tokens/connection strings.

    Validates: Requirements 3.2
    """

    @given(summary=st_setup_summary())
    def test_wellformed_block_has_no_secret_error(self, summary):
        """A well-formed block (names/counts/versions/verdicts) is never flagged.

        **Validates: Requirements 3.2**
        """
        errors = validate_progress_schema({"setup_summary": summary})
        assert errors == []
        assert not any("secret-like field" in e for e in errors)

    @given(summary=st_setup_summary(), secret_key=st_secret_key(), value=_TOKEN)
    def test_injected_secret_key_is_rejected(self, summary, secret_key, value):
        """Any key resembling a secret/token/connection string is rejected.

        Generalizes the example-based secret-field unit tests across the full
        forbidden-substring vocabulary and arbitrary surrounding characters.

        **Validates: Requirements 3.2**
        """
        tainted = dict(summary)
        tainted[secret_key] = value
        errors = validate_progress_schema({"setup_summary": tainted})
        assert any("secret-like field" in e for e in errors)


# ═══════════════════════════════════════════════════════════════════════════
# P4 — Backward compatible
# ═══════════════════════════════════════════════════════════════════════════


class TestSetupSummaryBackwardCompatible:
    """P4: resume works with or without the block; absence is never an error.

    Validates: Requirements 2.3, 3.1
    """

    @given(progress=st_progress_without_summary())
    def test_absent_block_validates_and_reads_as_none(self, progress):
        """A Progress_File without the block validates and replays as ``None``.

        The validator raises no error for the missing block, and the replay read
        returns ``None`` without raising — resume proceeds unchanged.

        **Validates: Requirements 2.3, 3.1**
        """
        assert validate_progress_schema(progress) == []
        assert "setup_summary" not in progress

        with _temp_dir() as directory:
            path = str(directory / "bootcamp_progress.json")
            _write_progress(path, progress)
            assert _safe_read_setup_summary(path) is None

    @given(progress=st_progress_without_summary(), summary=st_setup_summary())
    def test_present_block_is_replayed(self, progress, summary):
        """When the block exists, the replay read returns it intact.

        Together with the absent-block case, this shows resume works whether or
        not ``setup_summary`` is present.

        **Validates: Requirements 2.3**
        """
        with _temp_dir() as directory:
            path = str(directory / "bootcamp_progress.json")
            _write_progress(path, progress)
            _merge_setup_summary(path, summary)
            assert _safe_read_setup_summary(path) == summary


# ═══════════════════════════════════════════════════════════════════════════
# P5 — Non-blocking
# ═══════════════════════════════════════════════════════════════════════════


class TestSetupSummaryNonBlocking:
    """P5: a write or read failure never blocks onboarding or resume.

    The outer "catch and continue" is a steering-level contract; these tests
    model it with the ``_safe_*`` wrappers and assert it at the code-level seam.

    Validates: Requirements 1.5, 2.3, 2.4
    """

    @given(progress=st_progress_without_summary(), summary=st_setup_summary())
    def test_write_failure_is_non_blocking_and_preserves_state(self, progress, summary):
        """A failed write is swallowed and leaves existing progress intact.

        Onboarding continues (no exception escapes, the wrapper returns
        ``False``) and the on-disk Progress_File is byte-for-byte unchanged — a
        failed persist never corrupts prior state.

        **Validates: Requirements 1.5**
        """
        with _temp_dir() as directory:
            path = str(directory / "bootcamp_progress.json")
            _write_progress(path, progress)
            before = Path(path).read_bytes()

            persisted = _safe_write_setup_summary(path, summary, writer=_raising_writer)

            assert persisted is False
            assert Path(path).read_bytes() == before
            assert _read_progress(path) == progress

    @given(garbage=st.text(max_size=40))
    def test_read_failure_is_non_blocking(self, garbage):
        """A corrupt/unreadable Progress_File replays as ``None`` without raising.

        Resume proceeds unchanged when the persisted block cannot be read.

        **Validates: Requirements 2.3, 2.4**
        """
        with _temp_dir() as directory:
            corrupt_path = directory / "bootcamp_progress.json"
            # Prepend a brace so the payload is almost-JSON but still invalid,
            # forcing a decode error through the real ``_read_progress`` seam.
            corrupt_path.write_text("{" + garbage, encoding="utf-8")
            assert _safe_read_setup_summary(str(corrupt_path)) is None

        # A path that does not exist reads as an empty dict -> block is None.
        with _temp_dir() as directory:
            missing_path = str(directory / "does_not_exist.json")
            assert _safe_read_setup_summary(missing_path) is None
