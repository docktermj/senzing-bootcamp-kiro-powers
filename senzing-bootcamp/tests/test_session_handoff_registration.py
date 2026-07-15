"""Registration tests for ``session-handoff.md`` in ``steering-index.yaml``.

Feature: session-handoff

Deterministic example test (no randomness, no wall-clock, no network, stdlib
only) that asserts the Session_Handoff steering file is correctly registered in
the Steering_Index ``file_metadata`` block. It reuses ``measure_steering.py``'s
own measuring helpers -- imported via the ``sys.path`` shim per repo convention
-- so the recorded ``token_count`` / ``size_category`` stay in lockstep with
CI's ``measure_steering.py --check`` rather than re-implementing token counting.

Assertions:
- ``file_metadata`` contains an entry for ``session-handoff.md`` (Req 11.2).
- The entry carries an integer ``token_count`` and a valid ``size_category``.
- The recorded ``token_count`` equals the value the repo's measuring logic
  computes for the current file content (exact equality is the sync convention),
  and no per-file drift is reported by the CI ``--check`` tolerance rule.
- The recorded ``size_category`` matches what the measuring logic classifies for
  that count, and the file stays under the configured ``split_threshold_tokens``
  so it needs no ``split_allowlist`` exemption (consistent with the CI budget /
  ``validate_power.py`` expectations).

Validates: Requirements 11.2
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts are not a package) so the
# token-count / size-category logic comes straight from measure_steering.py.
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import measure_steering  # noqa: E402

# ---------------------------------------------------------------------------
# Paths and constants (resolved relative to this file so the suite is
# location-independent: <repo>/senzing-bootcamp/tests/ -> ../steering/).
# ---------------------------------------------------------------------------
_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"
_INDEX_PATH: Path = _STEERING_DIR / "steering-index.yaml"
_STEERING_FILE_NAME = "session-handoff.md"
_SESSION_HANDOFF: Path = _STEERING_DIR / _STEERING_FILE_NAME

# Size categories recognized by measure_steering.classify_size.
_VALID_SIZE_CATEGORIES = frozenset({"small", "medium", "large"})

# Default split threshold measure_steering falls back to when the budget key is
# absent (mirrors the documented Default_Threshold).
_DEFAULT_SPLIT_THRESHOLD = 5000


def _stored_entry() -> dict[str, object]:
    """Return the ``session-handoff.md`` file_metadata entry from the index.

    Reads the on-disk ``steering-index.yaml`` and parses its ``file_metadata``
    block with ``measure_steering._parse_stored_metadata`` (the same minimal
    stdlib parser the CI check uses), failing clearly if the file is not
    registered.

    Returns:
        The parsed ``{"token_count": int, "size_category": str}`` entry.
    """
    content = measure_steering.load_yaml_content(_INDEX_PATH)
    stored = measure_steering._parse_stored_metadata(content)
    assert stored is not None, "file_metadata section missing from steering-index.yaml"
    assert _STEERING_FILE_NAME in stored, (
        f"{_STEERING_FILE_NAME} is not registered in file_metadata"
    )
    return stored[_STEERING_FILE_NAME]


def _split_threshold() -> int:
    """Return the configured ``budget.split_threshold_tokens`` from the index.

    Parses the value with a localized regex (the repo's minimal-parser
    convention, mirroring ``measure_steering.parse_budget_total``), falling back
    to the documented default when the key is absent.

    Returns:
        The split threshold in tokens.
    """
    content = measure_steering.load_yaml_content(_INDEX_PATH)
    match = re.search(r"split_threshold_tokens:\s*(\d+)", content)
    return int(match.group(1)) if match else _DEFAULT_SPLIT_THRESHOLD


class TestSessionHandoffRegistration:
    """Registration conformance for ``session-handoff.md`` in the Steering_Index.

    Validates: Requirements 11.2
    """

    def test_index_and_steering_file_exist(self) -> None:
        """Both the steering index and the steering file are present on disk."""
        assert _INDEX_PATH.exists(), f"steering index not found: {_INDEX_PATH}"
        assert _SESSION_HANDOFF.exists(), f"steering file not found: {_SESSION_HANDOFF}"
        assert _SESSION_HANDOFF.is_file(), f"not a file: {_SESSION_HANDOFF}"

    def test_file_metadata_contains_session_handoff(self) -> None:
        """``file_metadata`` registers an entry for ``session-handoff.md`` (Req 11.2)."""
        content = measure_steering.load_yaml_content(_INDEX_PATH)
        stored = measure_steering._parse_stored_metadata(content)
        assert stored is not None, "file_metadata section missing from the index"
        assert _STEERING_FILE_NAME in stored, (
            f"{_STEERING_FILE_NAME} missing from file_metadata: registration required"
        )

    def test_entry_has_positive_integer_token_count(self) -> None:
        """The registered ``token_count`` is a positive integer (Req 11.2)."""
        token_count = _stored_entry().get("token_count")
        assert isinstance(token_count, int) and not isinstance(token_count, bool), (
            f"token_count must be an integer, got {token_count!r}"
        )
        assert token_count > 0, f"token_count must be positive, got {token_count}"

    def test_entry_has_valid_size_category(self) -> None:
        """The registered ``size_category`` is one of the recognized categories."""
        size_category = _stored_entry().get("size_category")
        assert size_category in _VALID_SIZE_CATEGORIES, (
            f"invalid size_category: {size_category!r}"
        )

    def test_token_count_matches_measuring_logic(self) -> None:
        """Recorded ``token_count`` equals measure_steering's computed value (Req 11.2).

        Exact equality is the sync convention (``measure_steering`` writes measured
        counts verbatim), keeping the registration in lockstep with the on-disk
        content.
        """
        measured = measure_steering.calculate_token_count(_SESSION_HANDOFF)
        recorded = _stored_entry()["token_count"]
        assert recorded == measured, (
            f"recorded token_count {recorded} != measured {measured}; "
            "re-run measure_steering.py to re-sync the index"
        )

    def test_token_count_within_ci_check_tolerance(self) -> None:
        """No per-file drift is reported for the entry by the CI ``--check`` rule.

        Runs the same ``check_counts`` comparison that ``measure_steering.py
        --check`` uses (10% tolerance) and asserts ``session-handoff.md`` is not
        among the reported mismatches, so this registration will not break CI.
        """
        measured = measure_steering.scan_steering_files(_STEERING_DIR)
        mismatches = measure_steering.check_counts(_INDEX_PATH, measured)
        offending = [m for m in mismatches if m[0] == _STEERING_FILE_NAME]
        assert offending == [], (
            f"session-handoff.md flagged by --check tolerance rule: {offending}"
        )

    def test_size_category_matches_measuring_logic(self) -> None:
        """Recorded ``size_category`` matches ``classify_size`` for the measured count."""
        measured = measure_steering.calculate_token_count(_SESSION_HANDOFF)
        expected_category = measure_steering.classify_size(measured)
        recorded = _stored_entry()["size_category"]
        assert recorded == expected_category, (
            f"recorded size_category {recorded!r} != classified "
            f"{expected_category!r} for token_count {measured}"
        )

    def test_token_count_under_split_threshold(self) -> None:
        """The file stays under ``split_threshold_tokens`` (no allowlist exemption).

        Keeping ``session-handoff.md`` a single cohesive file under the budget is
        the design's stated target and avoids needing a ``split_allowlist`` entry,
        consistent with the CI budget / ``validate_power.py`` expectations.
        """
        recorded = _stored_entry()["token_count"]
        threshold = _split_threshold()
        assert isinstance(recorded, int)
        assert recorded < threshold, (
            f"session-handoff.md token_count {recorded} is not under the split "
            f"threshold {threshold}; it would require a split_allowlist entry"
        )
