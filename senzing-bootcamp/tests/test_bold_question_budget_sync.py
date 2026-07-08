"""Deterministic budget-sync tests for the question-visibility feature.

Task 6.1 re-synced ``steering-index.yaml`` with ``measure_steering.py`` after the
bold-question edits. This module locks that in: it asserts that
``measure_steering.py --check`` passes on the current synced index and pins the
three properties the check enforces after the sync —

- per-file ``token_count`` values match their measured values (R9.1),
- ``budget.total_tokens`` equals the sum of the per-file counts (R9.3), and
- the always-loaded baseline footprint stays under the configured ceiling (R9.2).

Mirrors the deterministic patterns already used in ``test_measure_steering.py``
(``TestIntegrationRealSteering``) and ``test_steering_index_token_count_sync_*``:
it reads the fixed on-disk steering content and runs the check both via the
module function API and via a subprocess exactly as CI invokes it. All tests are
deterministic — no randomness, no wall-clock time, no network, no external state.

Feature: question-visibility

Validates: Requirements R9.1, R9.2, R9.3
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages).
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import measure_steering  # noqa: E402

_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"
_INDEX_PATH: Path = _STEERING_DIR / "steering-index.yaml"
_SCRIPT_PATH: Path = Path(_SCRIPTS_DIR) / "measure_steering.py"


class TestBoldQuestionBudgetSync:
    """``--check`` passes on the synced steering-index.yaml after the bold edits.

    Validates: Requirements R9.1, R9.2, R9.3
    """

    def test_check_cli_exits_zero_on_synced_index(self) -> None:
        """``measure_steering.py --check`` exits 0 on the live synced index.

        Runs the script exactly as the CI pipeline does (subprocess against the
        real steering directory and index) and asserts a clean pass.

        Validates: Requirements R9.1, R9.2, R9.3
        """
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPT_PATH),
                "--check",
                "--steering-dir",
                str(_STEERING_DIR),
                "--index-path",
                str(_INDEX_PATH),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"--check exited {result.returncode} on the synced index:\n"
            f"{result.stdout}\n{result.stderr}"
        )
        assert "All token counts are within 10% tolerance." in result.stdout, (
            f"expected the success line in --check output:\n{result.stdout}"
        )

    def test_per_file_counts_match_measured(self) -> None:
        """Each stored file_metadata token_count exactly equals its measured value.

        The sync writes measured counts verbatim, so every measured file must be
        recorded with an exactly-equal count and ``check_counts`` must report no
        per-file drift.

        Validates: Requirement R9.1
        """
        content = measure_steering.load_yaml_content(_INDEX_PATH)
        stored = measure_steering._parse_stored_metadata(content)
        assert stored, "file_metadata section missing from the synced index"

        measured = measure_steering.scan_steering_files(_STEERING_DIR)

        for filename, meta in measured.items():
            assert filename in stored, f"{filename} missing from file_metadata"
            assert stored[filename].get("token_count") == meta["token_count"], (
                f"{filename}: stored token_count "
                f"{stored[filename].get('token_count')} != measured "
                f"{meta['token_count']}"
            )

        # And the CLI-level per-file drift check reports nothing.
        assert measure_steering.check_counts(_INDEX_PATH, measured) == []

    def test_budget_total_equals_sum_of_per_file_counts(self) -> None:
        """``budget.total_tokens`` equals the sum of the per-file token counts.

        Validates: Requirement R9.3
        """
        content = measure_steering.load_yaml_content(_INDEX_PATH)
        declared_total = measure_steering.parse_budget_total(content)
        stored = measure_steering._parse_stored_metadata(content) or {}
        expected_total = sum(m.get("token_count", 0) for m in stored.values())
        assert declared_total == expected_total, (
            f"budget.total_tokens {declared_total} != sum(file_metadata) "
            f"{expected_total}"
        )

    def test_always_loaded_footprint_under_ceiling(self) -> None:
        """The always-loaded baseline footprint stays under the configured ceiling.

        Also confirms ``agent-instructions.md`` (the always-loaded file this
        feature grows) individually stays within the ceiling.

        Validates: Requirement R9.2
        """
        measured = measure_steering.scan_steering_files(_STEERING_DIR)
        result = measure_steering.check_always_loaded_budget(
            _INDEX_PATH, _STEERING_DIR, measured
        )
        assert result.over_budget is False, (
            f"always-loaded footprint {result.footprint_tokens} exceeds ceiling "
            f"{result.ceiling_tokens}"
        )
        assert result.footprint_tokens <= result.ceiling_tokens

        ai_tokens = measured.get("agent-instructions.md", {}).get("token_count")
        assert ai_tokens is not None, "agent-instructions.md must be measured"
        assert ai_tokens <= result.ceiling_tokens, (
            f"agent-instructions.md token_count {ai_tokens} exceeds the "
            f"always-loaded ceiling {result.ceiling_tokens}"
        )
