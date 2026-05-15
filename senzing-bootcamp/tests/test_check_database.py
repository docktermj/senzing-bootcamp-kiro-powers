"""Property-based tests for scripts/check_database.py.

Validates correctness properties of the DatabaseHealthChecker:
- Property 4: Repair then re-check behavior

Feature: database-corruption-recovery
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import check_database  # noqa: E402
from check_database import DatabaseCheckResult, DatabaseHealthChecker, main  # noqa: E402
from preflight import check_database as preflight_check_database  # noqa: E402


# ---------------------------------------------------------------------------
# Task 4.1 — Property 1: Corruption detection
# ---------------------------------------------------------------------------


class TestCorruptionDetection:
    """Property 1: Corruption detection.

    For any byte sequence written to a file that is not a valid SQLite database,
    the DatabaseHealthChecker SHALL report a failure status (either at the
    connection check or integrity check stage).

    **Validates: Requirements 5, 10**
    """

    @given(data=st.binary(min_size=1, max_size=1000))
    @settings(max_examples=5)
    def test_random_bytes_detected_as_corrupt(self, data: bytes) -> None:
        """Any random byte sequence that isn't a valid SQLite DB must be detected as corrupt.

        The checker must report a non-PASS verdict. For most random data, SQLite
        will reject the file at the connection stage ("not a database"). For very
        small files (e.g., a single null byte), SQLite may accept the connection
        but the integrity or entity count checks will still flag the issue.

        **Validates: Requirements 5, 10**
        """
        # Write random bytes to a temp file
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            f.write(data)
            db_file = f.name

        try:
            checker = DatabaseHealthChecker(db_path=db_file)
            report = checker.run_all()

            # The checker must NOT report PASS for random bytes — it must detect
            # that this is not a healthy database (FAIL or WARN)
            assert report.verdict != "PASS", (
                f"Expected non-PASS verdict for random bytes (len={len(data)}), "
                f"got {report.verdict}. Checks: "
                f"{[(c.name, c.status) for c in report.checks]}"
            )

            # At least one check must have a non-pass status at connection,
            # integrity, or entity count stage
            non_pass_checks = [c for c in report.checks if c.status != "pass"]
            assert len(non_pass_checks) > 0, (
                f"Expected at least one non-pass check for random bytes, "
                f"got: {[(c.name, c.status) for c in report.checks]}"
            )
        finally:
            os.unlink(db_file)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


@st.composite
def st_repair_scenario(draw):
    """Generate a repair scenario with initial check states and repair outcome.

    Produces a dict with:
    - integrity_fails: whether the initial integrity check fails
    - repair_succeeds: whether the repair (WAL checkpoint + vacuum) succeeds
    - post_repair_integrity_ok: whether integrity passes after repair
    """
    integrity_fails = draw(st.booleans())
    repair_succeeds = draw(st.booleans())
    # Post-repair integrity only matters if repair succeeds
    post_repair_integrity_ok = draw(st.booleans()) if repair_succeeds else False
    return {
        "integrity_fails": integrity_fails,
        "repair_succeeds": repair_succeeds,
        "post_repair_integrity_ok": post_repair_integrity_ok,
    }


# ---------------------------------------------------------------------------
# Property 4: Repair then re-check
# ---------------------------------------------------------------------------


class TestRepairThenRecheck:
    """Property 4: Repair then re-check.

    For any database state where the initial integrity check fails, when
    --repair is enabled the checker SHALL attempt WAL checkpoint and vacuum,
    then re-evaluate the failing checks. The final report SHALL reflect the
    post-repair status (pass if repair succeeded, fail if not).

    **Validates: Requirements 6**
    """

    @given(scenario=st_repair_scenario())
    @settings(max_examples=5)
    def test_final_report_reflects_post_repair_status(self, scenario: dict) -> None:
        """Final report reflects post-repair status, not initial failure state."""
        integrity_fails = scenario["integrity_fails"]
        repair_succeeds = scenario["repair_succeeds"]
        post_repair_integrity_ok = scenario["post_repair_integrity_ok"]

        # Track call count to distinguish initial check from post-repair recheck
        integrity_call_count = 0

        def mock_integrity_check(self_checker):
            """Simulate integrity check: fail initially, then reflect repair outcome."""
            nonlocal integrity_call_count
            integrity_call_count += 1

            if integrity_call_count == 1:
                # Initial check
                if integrity_fails:
                    return DatabaseCheckResult(
                        name="Integrity check",
                        status="fail",
                        message="PRAGMA integrity_check: corruption detected",
                        fix="Run with --repair to attempt WAL checkpoint and vacuum.",
                    )
                else:
                    return DatabaseCheckResult(
                        name="Integrity check",
                        status="pass",
                        message="PRAGMA integrity_check: ok",
                    )
            else:
                # Post-repair recheck
                if post_repair_integrity_ok:
                    return DatabaseCheckResult(
                        name="Integrity check",
                        status="pass",
                        message="PRAGMA integrity_check: ok",
                        fixed=True,
                    )
                else:
                    return DatabaseCheckResult(
                        name="Integrity check",
                        status="fail",
                        message="PRAGMA integrity_check: still corrupted",
                        fix="Manual intervention required.",
                    )

        def mock_file_exists(self_checker):
            return DatabaseCheckResult(
                name="File exists",
                status="pass",
                message="Database file found: test.db",
            )

        def mock_connection(self_checker):
            return DatabaseCheckResult(
                name="Connection",
                status="pass",
                message="Successfully connected to database",
            )

        def mock_entity_count(self_checker):
            return DatabaseCheckResult(
                name="Entity count",
                status="pass",
                message="Entity count: 100",
            )

        def mock_attempt_repair(self_checker):
            """Simulate repair attempt."""
            if not repair_succeeds:
                return [DatabaseCheckResult(
                    name="Repair",
                    status="fail",
                    message="Repair failed: disk full",
                    fix="Manual intervention required. Free disk space or rebuild.",
                )]

            # Repair succeeded — re-run checks
            recheck_integrity = mock_integrity_check(self_checker)
            if recheck_integrity.status == "pass":
                recheck_integrity = DatabaseCheckResult(
                    name=recheck_integrity.name,
                    status="pass",
                    message=recheck_integrity.message,
                    fix=recheck_integrity.fix,
                    fixed=True,
                )

            recheck_entity = DatabaseCheckResult(
                name="Entity count",
                status="pass",
                message="Entity count: 100",
                fixed=True,
            )
            return [recheck_integrity, recheck_entity]

        with patch.object(DatabaseHealthChecker, "check_file_exists", mock_file_exists), \
             patch.object(DatabaseHealthChecker, "check_connection", mock_connection), \
             patch.object(DatabaseHealthChecker, "check_integrity", mock_integrity_check), \
             patch.object(DatabaseHealthChecker, "check_entity_count", mock_entity_count), \
             patch.object(DatabaseHealthChecker, "attempt_repair", mock_attempt_repair):

            checker = DatabaseHealthChecker(db_path="test.db", repair=True)
            report = checker.run_all()

        # Assertions based on scenario
        if not integrity_fails:
            # No initial failure → repair not triggered → report should pass
            assert report.verdict == "PASS", (
                f"Expected PASS when integrity doesn't fail initially, got {report.verdict}"
            )
        elif not repair_succeeds:
            # Initial failure + repair fails → final report should still show failure
            # The original integrity fail remains, plus a Repair fail entry
            assert report.verdict == "FAIL", (
                f"Expected FAIL when repair doesn't succeed, got {report.verdict}"
            )
        elif post_repair_integrity_ok:
            # Initial failure + repair succeeds + post-repair integrity ok → PASS
            assert report.verdict == "PASS", (
                f"Expected PASS when repair succeeds and post-repair integrity is ok, "
                f"got {report.verdict}"
            )
        else:
            # Initial failure + repair succeeds but post-repair integrity still fails → FAIL
            assert report.verdict == "FAIL", (
                f"Expected FAIL when repair succeeds but post-repair integrity still fails, "
                f"got {report.verdict}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# Task 4.3 — Property 3: Entity count threshold
# ═══════════════════════════════════════════════════════════════════════════


class TestEntityCountThreshold:
    """Property 3: Entity count threshold.

    For any non-negative integer returned as the entity count from the database,
    if the count is greater than zero the entity count check SHALL report "pass";
    if the count equals zero it SHALL report "warn" or "fail".

    **Validates: Requirements 5**
    """

    @given(st.integers(min_value=0, max_value=10000))
    @settings(max_examples=5)
    def test_entity_count_threshold_property(self, count: int) -> None:
        """count > 0 → pass; count == 0 → warn or fail."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (count,)
        mock_conn.execute.return_value = mock_cursor

        with patch("check_database.os.path.isfile", return_value=True), \
             patch("check_database.sqlite3.connect", return_value=mock_conn):
            checker = DatabaseHealthChecker(db_path="fake.db")
            result = checker.check_entity_count()

        if count > 0:
            assert result.status == "pass", (
                f"Expected 'pass' for count={count}, got '{result.status}'"
            )
        else:
            assert result.status in ("warn", "fail"), (
                f"Expected 'warn' or 'fail' for count=0, got '{result.status}'"
            )


# ═══════════════════════════════════════════════════════════════════════════
# Task 4.2 — Property 2: Integrity check interpretation
# ═══════════════════════════════════════════════════════════════════════════


class TestIntegrityCheckInterpretation:
    """Property 2: Integrity check interpretation.

    For any string returned by PRAGMA integrity_check, if the string equals
    "ok" the integrity check SHALL report "pass"; for any other string value,
    it SHALL report "fail".

    **Validates: Requirements 5, 3**
    """

    @given(st.text(min_size=1, max_size=200))
    @settings(max_examples=5)
    def test_integrity_check_interpretation(self, pragma_response: str) -> None:
        """For any PRAGMA integrity_check response, "ok" → pass, anything else → fail."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (pragma_response,)

        mock_conn = MagicMock()
        mock_conn.execute.return_value = mock_cursor

        with patch("check_database.sqlite3.connect", return_value=mock_conn):
            checker = DatabaseHealthChecker(db_path="/fake/path.db", repair=False)
            result = checker.check_integrity()

        if pragma_response == "ok":
            assert result.status == "pass", (
                f"Expected 'pass' for PRAGMA response 'ok', got '{result.status}'"
            )
        else:
            assert result.status == "fail", (
                f"Expected 'fail' for PRAGMA response {pragma_response!r}, "
                f"got '{result.status}'"
            )


# ═══════════════════════════════════════════════════════════════════════════
# Task 4.5 — Unit tests for CLI behavior and preflight integration
# ═══════════════════════════════════════════════════════════════════════════


class TestCLIBehavior:
    """Unit tests for check_database.py CLI behavior.

    Validates: Requirements 7, 10
    """

    def test_missing_database_file_returns_fail(self, tmp_path: Path) -> None:
        """Missing database file → fail result with exit code 1."""
        nonexistent = str(tmp_path / "nonexistent.db")
        exit_code = main(argv=["--db-path", nonexistent])
        assert exit_code == 1

    def test_healthy_database_all_checks_pass(self, tmp_path: Path) -> None:
        """Healthy database → all checks pass with exit code 0."""
        db_file = tmp_path / "healthy.db"
        conn = sqlite3.connect(str(db_file))
        conn.execute("CREATE TABLE RES_ENT_OKEY (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO RES_ENT_OKEY (id) VALUES (1)")
        conn.execute("INSERT INTO RES_ENT_OKEY (id) VALUES (2)")
        conn.commit()
        conn.close()

        exit_code = main(argv=["--db-path", str(db_file)])
        assert exit_code == 0

    def test_repair_triggers_wal_checkpoint_and_vacuum(self, tmp_path: Path) -> None:
        """--repair triggers WAL checkpoint + vacuum."""
        db_file = tmp_path / "repair_test.db"
        conn = sqlite3.connect(str(db_file))
        conn.execute("CREATE TABLE RES_ENT_OKEY (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO RES_ENT_OKEY (id) VALUES (1)")
        conn.commit()
        conn.close()

        # Patch attempt_repair to verify it gets called
        with patch.object(DatabaseHealthChecker, "attempt_repair", wraps=None) as mock_repair:
            mock_repair.return_value = []
            # Force a failure so repair is triggered
            with patch.object(
                DatabaseHealthChecker, "check_integrity"
            ) as mock_integrity:
                from check_database import DatabaseCheckResult
                mock_integrity.return_value = DatabaseCheckResult(
                    name="Integrity check",
                    status="fail",
                    message="PRAGMA integrity_check: corruption",
                )
                exit_code = main(argv=["--db-path", str(db_file), "--repair"])
                mock_repair.assert_called_once()

    def test_json_produces_valid_json_output(self, tmp_path: Path, capsys) -> None:
        """--json produces valid JSON output."""
        db_file = tmp_path / "json_test.db"
        conn = sqlite3.connect(str(db_file))
        conn.execute("CREATE TABLE RES_ENT_OKEY (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO RES_ENT_OKEY (id) VALUES (1)")
        conn.commit()
        conn.close()

        exit_code = main(argv=["--db-path", str(db_file), "--json"])
        captured = capsys.readouterr()

        # Must be valid JSON
        data = json.loads(captured.out)
        assert "checks" in data
        assert "summary" in data
        assert data["summary"]["verdict"] in ("PASS", "WARN", "FAIL")
        assert exit_code == 0

    def test_db_path_overrides_default(self, tmp_path: Path) -> None:
        """--db-path overrides default path."""
        custom_db = tmp_path / "custom" / "my.db"
        custom_db.parent.mkdir(parents=True)
        conn = sqlite3.connect(str(custom_db))
        conn.execute("CREATE TABLE RES_ENT_OKEY (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO RES_ENT_OKEY (id) VALUES (1)")
        conn.commit()
        conn.close()

        exit_code = main(argv=["--db-path", str(custom_db)])
        assert exit_code == 0


class TestPreflightIntegration:
    """Unit tests for preflight.py database check integration.

    Validates: Requirements 7, 10
    """

    def test_file_exists_check_runs(self, tmp_path: Path, monkeypatch) -> None:
        """Preflight integration — file exists → check runs."""
        db_file = tmp_path / "database" / "G2C.db"
        db_file.parent.mkdir(parents=True)
        conn = sqlite3.connect(str(db_file))
        conn.execute("CREATE TABLE test_table (id INTEGER)")
        conn.commit()
        conn.close()

        # Monkeypatch os.path.isfile and sqlite3.connect to use our temp db
        monkeypatch.chdir(tmp_path)

        results = preflight_check_database()
        # When file exists, we should get at least one CheckResult
        assert len(results) > 0
        assert results[0].category == "Database"

    def test_file_absent_check_skipped(self, tmp_path: Path, monkeypatch) -> None:
        """Preflight integration — file absent → check skipped (empty list)."""
        # chdir to a temp directory with no database/G2C.db
        monkeypatch.chdir(tmp_path)

        results = preflight_check_database()
        # When file does not exist, returns empty list (skip silently)
        assert results == []
