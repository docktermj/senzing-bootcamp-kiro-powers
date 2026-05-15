#!/usr/bin/env python3
"""Senzing Bootcamp — Database Health Check.

Runs basic health checks against a SQLite database: file exists, can connect,
integrity check passes, entity count > 0.  Supports ``--repair`` for automatic
recovery (WAL checkpoint, vacuum) and ``--json`` for programmatic output.

Usage:
    python scripts/check_database.py
    python scripts/check_database.py --db-path database/G2C.db --repair
    python scripts/check_database.py --json

Stdlib only — no third-party deps.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sqlite3
import sys


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class DatabaseCheckResult:
    """Result of a single database health check."""

    name: str
    status: str          # "pass" | "warn" | "fail"
    message: str
    fix: str | None = None
    fixed: bool = False


@dataclasses.dataclass
class DatabaseHealthReport:
    """Collection of all database check results."""

    checks: list[DatabaseCheckResult]
    db_path: str

    @property
    def verdict(self) -> str:
        """'FAIL' if any fail, 'WARN' if any warn, else 'PASS'."""
        if any(c.status == "fail" for c in self.checks):
            return "FAIL"
        if any(c.status == "warn" for c in self.checks):
            return "WARN"
        return "PASS"

    @property
    def pass_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "pass")

    @property
    def warn_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "warn")

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "fail")


# ---------------------------------------------------------------------------
# Health checker
# ---------------------------------------------------------------------------


class DatabaseHealthChecker:
    """Runs health checks against a SQLite database."""

    def __init__(self, db_path: str, repair: bool = False) -> None:
        self.db_path = db_path
        self.repair = repair

    def check_file_exists(self) -> DatabaseCheckResult:
        """Check that the database file exists on disk."""
        if os.path.isfile(self.db_path):
            return DatabaseCheckResult(
                name="File exists",
                status="pass",
                message=f"Database file found: {self.db_path}",
            )
        return DatabaseCheckResult(
            name="File exists",
            status="fail",
            message=f"Database file not found: {self.db_path}",
            fix="Re-run the loading program to create the database.",
        )

    def check_connection(self) -> DatabaseCheckResult:
        """Attempt to connect to the database and catch common errors."""
        try:
            conn = sqlite3.connect(self.db_path)
            # Query sqlite_master to force SQLite to read the file header
            conn.execute("SELECT name FROM sqlite_master LIMIT 1")
            conn.close()
            return DatabaseCheckResult(
                name="Connection",
                status="pass",
                message="Successfully connected to database",
            )
        except sqlite3.DatabaseError as exc:
            msg = str(exc).lower()
            if "not a database" in msg or "file is not a database" in msg:
                return DatabaseCheckResult(
                    name="Connection",
                    status="fail",
                    message=f"Not a valid SQLite database: {exc}",
                    fix="Database file is corrupted. Rebuild from scratch using the loading program.",
                )
            if "locked" in msg:
                return DatabaseCheckResult(
                    name="Connection",
                    status="fail",
                    message=f"Database is locked: {exc}",
                    fix="Close other processes accessing the database and retry.",
                )
            return DatabaseCheckResult(
                name="Connection",
                status="fail",
                message=f"Connection failed: {exc}",
                fix="Check file permissions and database integrity.",
            )
        except PermissionError as exc:
            return DatabaseCheckResult(
                name="Connection",
                status="fail",
                message=f"Permission denied: {exc}",
                fix="Check file permissions (chmod/chown) on the database file.",
            )
        except Exception as exc:
            return DatabaseCheckResult(
                name="Connection",
                status="fail",
                message=f"Unexpected connection error: {exc}",
                fix="Check file permissions and database integrity.",
            )

    def check_integrity(self) -> DatabaseCheckResult:
        """Run PRAGMA integrity_check and report the result."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            conn.close()
            if result == "ok":
                return DatabaseCheckResult(
                    name="Integrity check",
                    status="pass",
                    message="PRAGMA integrity_check: ok",
                )
            return DatabaseCheckResult(
                name="Integrity check",
                status="fail",
                message=f"PRAGMA integrity_check: {result}",
                fix="Run with --repair to attempt WAL checkpoint and vacuum, or rebuild the database.",
            )
        except Exception as exc:
            return DatabaseCheckResult(
                name="Integrity check",
                status="fail",
                message=f"Integrity check failed: {exc}",
                fix="Database may be corrupted. Try --repair or rebuild from scratch.",
            )

    def check_entity_count(self) -> DatabaseCheckResult:
        """Query entity count from RES_ENT_OKEY table."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM RES_ENT_OKEY")
            count = cursor.fetchone()[0]
            conn.close()
            if count > 0:
                return DatabaseCheckResult(
                    name="Entity count",
                    status="pass",
                    message=f"Entity count: {count}",
                )
            return DatabaseCheckResult(
                name="Entity count",
                status="warn",
                message="Entity count is 0 — data may not have loaded",
                fix="Re-run the loading program to populate the database.",
            )
        except sqlite3.OperationalError as exc:
            msg = str(exc).lower()
            if "no such table" in msg:
                return DatabaseCheckResult(
                    name="Entity count",
                    status="warn",
                    message="Table RES_ENT_OKEY does not exist (database may be freshly initialized)",
                    fix="Run the loading program to create Senzing tables and load data.",
                )
            return DatabaseCheckResult(
                name="Entity count",
                status="warn",
                message=f"Entity count query failed: {exc}",
                fix="Check database schema — expected Senzing tables may be missing.",
            )
        except Exception as exc:
            return DatabaseCheckResult(
                name="Entity count",
                status="warn",
                message=f"Entity count query failed: {exc}",
                fix="Check database schema and connectivity.",
            )

    def attempt_repair(self) -> list[DatabaseCheckResult]:
        """Attempt WAL checkpoint and vacuum, then re-check failing checks."""
        repair_results: list[DatabaseCheckResult] = []
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.execute("VACUUM")
            conn.close()
        except Exception as exc:
            repair_results.append(DatabaseCheckResult(
                name="Repair",
                status="fail",
                message=f"Repair failed: {exc}",
                fix="Manual intervention required. Free disk space or rebuild the database.",
            ))
            return repair_results

        # Re-run checks that can benefit from repair
        recheck_integrity = self.check_integrity()
        if recheck_integrity.status == "pass":
            recheck_integrity = DatabaseCheckResult(
                name=recheck_integrity.name,
                status="pass",
                message=recheck_integrity.message,
                fix=recheck_integrity.fix,
                fixed=True,
            )
        repair_results.append(recheck_integrity)

        recheck_entity = self.check_entity_count()
        if recheck_entity.status == "pass":
            recheck_entity = DatabaseCheckResult(
                name=recheck_entity.name,
                status="pass",
                message=recheck_entity.message,
                fix=recheck_entity.fix,
                fixed=True,
            )
        repair_results.append(recheck_entity)

        return repair_results

    def run_all(self) -> DatabaseHealthReport:
        """Execute all checks in sequence. Attempt repair if enabled and failures exist."""
        checks: list[DatabaseCheckResult] = []

        # 1. File exists
        file_check = self.check_file_exists()
        checks.append(file_check)
        if file_check.status == "fail":
            return DatabaseHealthReport(checks=checks, db_path=self.db_path)

        # 2. Connection
        conn_check = self.check_connection()
        checks.append(conn_check)
        if conn_check.status == "fail":
            return DatabaseHealthReport(checks=checks, db_path=self.db_path)

        # 3. Integrity
        integrity_check = self.check_integrity()
        checks.append(integrity_check)

        # 4. Entity count
        entity_check = self.check_entity_count()
        checks.append(entity_check)

        # Attempt repair if enabled and there are failures
        if self.repair and any(c.status == "fail" for c in checks):
            repair_results = self.attempt_repair()
            # Replace failing checks with repair results where applicable
            for repair_result in repair_results:
                if repair_result.name == "Repair":
                    checks.append(repair_result)
                else:
                    # Replace the original check with the post-repair result
                    for i, c in enumerate(checks):
                        if c.name == repair_result.name and c.status == "fail":
                            checks[i] = repair_result
                            break

        return DatabaseHealthReport(checks=checks, db_path=self.db_path)


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

_STATUS_ICON = {"pass": "✅", "warn": "⚠", "fail": "❌"}


def _color_supported() -> bool:
    """Return True if the terminal likely supports ANSI colors."""
    if os.environ.get("NO_COLOR"):
        return False
    if sys.platform == "win32":
        return bool(
            os.environ.get("WT_SESSION")
            or os.environ.get("TERM_PROGRAM")
            or "ANSICON" in os.environ
        )
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


_USE_COLOR = _color_supported()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def _green(t: str) -> str:
    return _c("0;32", t)


def _red(t: str) -> str:
    return _c("0;31", t)


def _yellow(t: str) -> str:
    return _c("1;33", t)


def _blue(t: str) -> str:
    return _c("0;34", t)


def _format_human(report: DatabaseHealthReport) -> str:
    """Render a human-readable report matching preflight.py style."""
    lines: list[str] = []

    lines.append("")
    lines.append(_blue("═" * 60))
    lines.append(_blue("  Senzing Bootcamp — Database Health Check"))
    lines.append(_blue("═" * 60))
    lines.append("")
    lines.append(f"  Database: {report.db_path}")
    lines.append("")

    for cr in report.checks:
        icon = _STATUS_ICON.get(cr.status, "?")
        lines.append(f"    {icon}  {cr.name}: {cr.message}")
        if cr.fixed:
            lines.append(f"        ↳ Fixed by --repair")
        elif cr.status in ("warn", "fail") and cr.fix:
            lines.append(f"        ↳ {cr.fix}")

    lines.append("")
    lines.append(_blue("─" * 60))
    lines.append(
        f"  {_green('Pass:')} {report.pass_count}  "
        f"{_yellow('Warn:')} {report.warn_count}  "
        f"{_red('Fail:')} {report.fail_count}"
    )

    verdict = report.verdict
    if verdict == "PASS":
        lines.append(_green(f"  Verdict: {verdict}"))
    elif verdict == "WARN":
        lines.append(_yellow(f"  Verdict: {verdict}"))
    else:
        lines.append(_red(f"  Verdict: {verdict}"))
    lines.append("")

    return "\n".join(lines)


def _format_json(report: DatabaseHealthReport) -> str:
    """Serialize a DatabaseHealthReport to JSON."""
    payload = dataclasses.asdict(report)
    payload["summary"] = {
        "pass_count": report.pass_count,
        "warn_count": report.warn_count,
        "fail_count": report.fail_count,
        "verdict": report.verdict,
    }
    return json.dumps(payload, indent=2)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Parse args, run database health checks, format output, return exit code."""
    parser = argparse.ArgumentParser(
        description="Senzing Bootcamp — Database Health Check",
    )
    parser.add_argument(
        "--db-path",
        default="database/G2C.db",
        help="Path to the SQLite database (default: database/G2C.db)",
    )
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Attempt automatic recovery (WAL checkpoint, vacuum) before reporting",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output report as JSON instead of human-readable text",
    )
    args = parser.parse_args(argv)

    checker = DatabaseHealthChecker(db_path=args.db_path, repair=args.repair)
    report = checker.run_all()

    if args.json_output:
        print(_format_json(report))
    else:
        print(_format_human(report))

    return 1 if report.verdict == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
