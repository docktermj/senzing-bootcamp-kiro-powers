#!/usr/bin/env python3
"""Senzing Bootcamp — Consolidated Environment Verification.

Performs all environment checks (language runtimes, disk space, network
connectivity, Senzing SDK availability, write permissions, required tools,
project structure) and produces a structured pass/warn/fail report.

Supports ``--json`` for programmatic consumption and ``--fix`` for
auto-remediation of simple issues (e.g. missing directories).

Cross-platform: Linux, macOS, Windows.  Stdlib only — no third-party deps.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import shutil
import socket
import subprocess
import sys
from typing import List, Optional


# ---------------------------------------------------------------------------
# Color helpers (matches existing NO_COLOR convention)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Data model  (Task 1.1)
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class CheckResult:
    """A single verification outcome."""

    name: str
    category: str
    status: str          # "pass" | "warn" | "fail"
    message: str
    fix: Optional[str] = None
    fixed: bool = False


@dataclasses.dataclass
class PreflightReport:
    """Ordered collection of all check results."""

    checks: List[CheckResult] = dataclasses.field(default_factory=list)

    @property
    def pass_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "pass")

    @property
    def warn_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "warn")

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "fail")

    @property
    def verdict(self) -> str:
        """'FAIL' if any fail, 'WARN' if any warn, else 'PASS'."""
        if any(c.status == "fail" for c in self.checks):
            return "FAIL"
        if any(c.status == "warn" for c in self.checks):
            return "WARN"
        return "PASS"


# ---------------------------------------------------------------------------
# Output formatting  (Tasks 1.2, 1.3)
# ---------------------------------------------------------------------------

class OutputFormatter:
    """Renders a PreflightReport as human-readable text or JSON."""

    # -- Task 1.2 ----------------------------------------------------------
    @staticmethod
    def to_json(report: PreflightReport) -> str:
        """Serialize *report* to a JSON string."""
        payload = {
            "checks": [
                {
                    "name": cr.name,
                    "category": cr.category,
                    "status": cr.status,
                    "message": cr.message,
                    "fix": cr.fix,
                    "fixed": cr.fixed,
                }
                for cr in report.checks
            ],
            "summary": {
                "pass_count": report.pass_count,
                "warn_count": report.warn_count,
                "fail_count": report.fail_count,
                "verdict": report.verdict,
            },
        }
        return json.dumps(payload, indent=2)

    # -- Task 1.3 ----------------------------------------------------------
    @staticmethod
    def to_human(report: PreflightReport) -> str:
        """Render a grouped, colored, human-readable report."""
        lines: list[str] = []

        # Banner
        lines.append("")
        lines.append(_blue("═" * 60))
        lines.append(
            _blue("  Senzing Bootcamp \u2014 Environment Verification")
        )
        lines.append(_blue("═" * 60))
        lines.append("")

        # Group checks by category, preserving insertion order
        categories: dict[str, list[CheckResult]] = {}
        for cr in report.checks:
            categories.setdefault(cr.category, []).append(cr)

        _STATUS_ICON = {"pass": "✅", "warn": "⚠", "fail": "❌"}

        for cat, results in categories.items():
            lines.append(_blue(f"  {cat}"))
            lines.append("")
            for cr in results:
                icon = _STATUS_ICON.get(cr.status, "?")
                lines.append(f"    {icon}  {cr.name}: {cr.message}")
                if cr.status in ("warn", "fail") and cr.fix:
                    lines.append(f"        ↳ {cr.fix}")
            lines.append("")

        # Summary
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


# ---------------------------------------------------------------------------
# Version helper
# ---------------------------------------------------------------------------

def _get_version(cmd: str, args: Optional[list[str]] = None) -> str:
    """Run *cmd* with version args and return the first line of output."""
    if args is None:
        args = ["--version"]
    try:
        r = subprocess.run(
            [cmd] + args,
            capture_output=True,
            text=True,
            timeout=10,
        )
        out = (r.stdout.strip() or r.stderr.strip())
        return out.splitlines()[0] if out else "unknown"
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Check functions  (Task 2)
# ---------------------------------------------------------------------------

# -- Task 2.1 --------------------------------------------------------------

def check_language_runtimes() -> list[CheckResult]:
    """Detect Python, Java, .NET, Rust, Node.js runtimes."""
    results: list[CheckResult] = []
    cat = "Language Runtimes"

    runtimes = {
        "Python": ["python3", "python"],
        "Java": ["java"],
        ".NET SDK": ["dotnet"],
        "Rust": ["rustc"],
        "Node.js": ["node"],
    }

    found_count = 0
    python_found = False

    for name, candidates in runtimes.items():
        cmd = None
        for c in candidates:
            if shutil.which(c):
                cmd = c
                break
        if cmd:
            ver = _get_version(cmd)
            results.append(CheckResult(
                name=f"{name} runtime",
                category=cat,
                status="pass",
                message=f"{name} {ver}",
            ))
            found_count += 1
            if name == "Python":
                python_found = True
        # If not found, we don't emit a result per runtime — only fail if *none* found

    if found_count == 0:
        results.append(CheckResult(
            name="Language runtimes",
            category=cat,
            status="fail",
            message="No supported language runtime found",
            fix=(
                "Install at least one: "
                "Python (https://python.org), "
                "Java (https://adoptium.net), "
                ".NET SDK (https://dot.net), "
                "Rust (https://rustup.rs), "
                "Node.js (https://nodejs.org)"
            ),
        ))

    # pip check when Python is present
    if python_found:
        pip_cmd = None
        for c in ["pip3", "pip"]:
            if shutil.which(c):
                pip_cmd = c
                break
        if pip_cmd:
            results.append(CheckResult(
                name="pip",
                category=cat,
                status="pass",
                message="pip available",
            ))
        else:
            results.append(CheckResult(
                name="pip",
                category=cat,
                status="warn",
                message="pip not found (needed for Python SDK installation)",
                fix="Install pip: https://pip.pypa.io/en/stable/installation/",
            ))

    # npm check when Node.js is present
    if shutil.which("node"):
        npm_candidates = ["npm.cmd", "npm"] if sys.platform == "win32" else ["npm"]
        npm_cmd = None
        for c in npm_candidates:
            if shutil.which(c):
                npm_cmd = c
                break
        if npm_cmd:
            results.append(CheckResult(
                name="npm",
                category=cat,
                status="pass",
                message="npm available",
            ))
        else:
            results.append(CheckResult(
                name="npm",
                category=cat,
                status="warn",
                message="npm not found (needed for TypeScript/Node.js projects)",
                fix="npm is bundled with Node.js — reinstall Node.js from https://nodejs.org",
            ))

    return results


# -- Task 2.2 --------------------------------------------------------------

def check_disk_space() -> list[CheckResult]:
    """Check available disk space (≥10 GB recommended)."""
    cat = "Disk Space"
    try:
        usage = shutil.disk_usage(os.getcwd())
        avail_gb = usage.free / (1024 ** 3)
        if avail_gb >= 10:
            return [CheckResult(
                name="Disk space",
                category=cat,
                status="pass",
                message=f"{avail_gb:.1f} GB available",
            )]
        else:
            return [CheckResult(
                name="Disk space",
                category=cat,
                status="warn",
                message=f"{avail_gb:.1f} GB available (10 GB+ recommended)",
                fix="Free up disk space to have at least 10 GB available.",
            )]
    except Exception:
        return [CheckResult(
            name="Disk space",
            category=cat,
            status="warn",
            message="Could not determine available disk space",
            fix="Ensure at least 10 GB of free disk space.",
        )]


# -- Task 2.3 --------------------------------------------------------------

def check_network() -> list[CheckResult]:
    """Check connectivity to mcp.senzing.com:443."""
    cat = "Network"
    host = "mcp.senzing.com"
    port = 443
    timeout = 5
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return [CheckResult(
            name="MCP connectivity",
            category=cat,
            status="pass",
            message=f"Connected to {host}:{port}",
        )]
    except (OSError, socket.timeout):
        return [CheckResult(
            name="MCP connectivity",
            category=cat,
            status="warn",
            message=f"Cannot reach {host}:{port}",
            fix=(
                f"Check internet connectivity and firewall rules for {host}:{port}. "
                "See docs/guides/OFFLINE_MODE.md for offline usage."
            ),
        )]


# -- Task 2.4 --------------------------------------------------------------

def check_senzing_sdk() -> list[CheckResult]:
    """Check Senzing SDK importability and version."""
    cat = "Senzing SDK"

    # Find a Python interpreter first
    py_cmd = None
    for c in ["python3", "python"]:
        if shutil.which(c):
            py_cmd = c
            break

    if py_cmd is None:
        return [CheckResult(
            name="Senzing SDK",
            category=cat,
            status="warn",
            message="SDK detection requires Python (no Python runtime found)",
            fix="Install Python to enable Senzing SDK detection.",
        )]

    # Try importing senzing in a subprocess
    code = (
        "import senzing; "
        "v = getattr(senzing, '__version__', getattr(senzing, 'VERSION', 'unknown')); "
        "print(v)"
    )
    try:
        r = subprocess.run(
            [py_cmd, "-c", code],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode != 0:
            return [CheckResult(
                name="Senzing SDK",
                category=cat,
                status="warn",
                message="Senzing SDK is not installed",
                fix="Module 2 will cover SDK installation. Or: pip install senzing",
            )]

        version_str = r.stdout.strip()
        if not version_str or version_str == "unknown":
            return [CheckResult(
                name="Senzing SDK",
                category=cat,
                status="warn",
                message="Senzing SDK installed but version could not be determined",
                fix="Consider upgrading: pip install --upgrade senzing",
            )]

        # Parse major.minor
        try:
            parts = version_str.split(".")
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            version_tuple = (major, minor)
        except (ValueError, IndexError):
            version_tuple = (0, 0)

        if version_tuple >= (4, 0):
            return [CheckResult(
                name="Senzing SDK",
                category=cat,
                status="pass",
                message=f"Senzing SDK {version_str}",
            )]
        else:
            return [CheckResult(
                name="Senzing SDK",
                category=cat,
                status="warn",
                message=f"Senzing SDK {version_str} (version 4.0+ recommended)",
                fix="Upgrade: pip install --upgrade senzing",
            )]

    except Exception:
        return [CheckResult(
            name="Senzing SDK",
            category=cat,
            status="warn",
            message="Could not check Senzing SDK",
            fix="Module 2 will cover SDK installation.",
        )]


# -- Task 2.5 --------------------------------------------------------------

def check_write_permissions() -> list[CheckResult]:
    """Verify write permissions in the current working directory."""
    cat = "Permissions"
    test_dir = os.path.join(os.getcwd(), "_preflight_write_test")
    try:
        os.makedirs(test_dir, exist_ok=True)
        os.rmdir(test_dir)
        return [CheckResult(
            name="Write permissions",
            category=cat,
            status="pass",
            message="Write permissions OK in current directory",
        )]
    except OSError as exc:
        return [CheckResult(
            name="Write permissions",
            category=cat,
            status="fail",
            message=f"Cannot write to current directory: {exc}",
            fix="Check directory ownership and permissions (chmod / chown).",
        )]


# -- Task 2.6 --------------------------------------------------------------

def check_required_tools() -> list[CheckResult]:
    """Check for required CLI tools (git, curl, zip/unzip)."""
    cat = "Core Tools"
    results: list[CheckResult] = []

    tools = {
        "git": "https://git-scm.com/downloads",
        "curl": "https://curl.se/download.html",
    }

    # zip/unzip only required on non-Windows
    if sys.platform != "win32":
        tools["zip"] = "sudo apt install zip (Ubuntu) or brew install zip (macOS)"
        tools["unzip"] = "sudo apt install unzip (Ubuntu) or brew install unzip (macOS)"

    for tool, install_url in tools.items():
        if shutil.which(tool):
            ver = _get_version(tool)
            results.append(CheckResult(
                name=tool,
                category=cat,
                status="pass",
                message=f"{tool} {ver}",
            ))
        else:
            results.append(CheckResult(
                name=tool,
                category=cat,
                status="fail",
                message=f"{tool} not found",
                fix=f"Install {tool}: {install_url}",
            ))

    # Windows: check for Visual Studio Build Tools (needed for TypeScript native addons)
    if sys.platform == "win32":
        vswhere = os.path.join(
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
            "Microsoft Visual Studio", "Installer", "vswhere.exe",
        )
        if os.path.isfile(vswhere):
            try:
                proc = subprocess.run(
                    [vswhere, "-products", "*", "-requires",
                     "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                     "-property", "installationPath"],
                    capture_output=True, text=True, timeout=10,
                )
                if proc.stdout.strip():
                    results.append(CheckResult(
                        name="VS Build Tools",
                        category=cat,
                        status="pass",
                        message="Visual Studio Build Tools found",
                    ))
                else:
                    results.append(CheckResult(
                        name="VS Build Tools",
                        category=cat,
                        status="warn",
                        message="Visual Studio Build Tools not found (needed for TypeScript native addons)",
                        fix='Install: winget install Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools"',
                    ))
            except Exception:
                results.append(CheckResult(
                    name="VS Build Tools",
                    category=cat,
                    status="warn",
                    message="Could not check for Visual Studio Build Tools",
                    fix='Install: winget install Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools"',
                ))
        else:
            results.append(CheckResult(
                name="VS Build Tools",
                category=cat,
                status="warn",
                message="vswhere not found — cannot verify Visual Studio Build Tools",
                fix='Install: winget install Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools"',
            ))

    return results


# -- Task 2.7 --------------------------------------------------------------

EXPECTED_DIRS = [
    os.path.join("data", "raw"),
    os.path.join("data", "transformed"),
    "database",
    "src",
    "scripts",
    "docs",
    "backups",
    "licenses",
]


def check_directories() -> list[CheckResult]:
    """Verify expected project directories exist."""
    cat = "Project Structure"
    results: list[CheckResult] = []

    for d in EXPECTED_DIRS:
        if os.path.isdir(d):
            results.append(CheckResult(
                name=f"Directory '{d}'",
                category=cat,
                status="pass",
                message=f"'{d}' exists",
            ))
        else:
            results.append(CheckResult(
                name=f"Directory '{d}'",
                category=cat,
                status="warn",
                message=f"'{d}' is missing",
                fix=f"Create it: mkdir -p {d}",
            ))

    return results


# ---------------------------------------------------------------------------
# AutoFixer  (Task 3.2)
# ---------------------------------------------------------------------------

class AutoFixer:
    """Attempts safe, idempotent fixes for failing checks."""

    FIXABLE_DIRS = EXPECTED_DIRS

    @staticmethod
    def try_fix(result: CheckResult) -> Optional[CheckResult]:
        """Attempt to fix *result*.  Returns an updated CheckResult or None."""
        # Only directory-creation fixes are supported
        if result.category != "Project Structure":
            return None
        if result.status not in ("warn", "fail"):
            return None

        # Extract the directory path from the check name
        # Name format: "Directory 'some/path'"
        dir_path: Optional[str] = None
        for d in AutoFixer.FIXABLE_DIRS:
            if d in result.name:
                dir_path = d
                break

        if dir_path is None:
            return None

        try:
            os.makedirs(dir_path, exist_ok=True)
            return CheckResult(
                name=result.name,
                category=result.category,
                status="pass",
                message=f"'{dir_path}' created",
                fix=result.fix,
                fixed=True,
            )
        except OSError as exc:
            # Retain original status, append failure reason
            return CheckResult(
                name=result.name,
                category=result.category,
                status=result.status,
                message=result.message,
                fix=f"{result.fix or ''} (auto-fix failed: {exc})",
                fixed=False,
            )


# ---------------------------------------------------------------------------
# CheckRunner  (Tasks 3.1, 3.3)
# ---------------------------------------------------------------------------

class CheckRunner:
    """Orchestrates all checks in category order."""

    # Ordered list of (category_label, check_function) — determines report order
    CHECK_SEQUENCE = [
        ("Core Tools", check_required_tools),
        ("Language Runtimes", check_language_runtimes),
        ("Disk Space", check_disk_space),
        ("Network", check_network),
        ("Senzing SDK", check_senzing_sdk),
        ("Permissions", check_write_permissions),
        ("Project Structure", check_directories),
    ]

    def run(self, fix: bool = False) -> PreflightReport:
        """Execute all checks.  If *fix* is True, attempt auto-fix then re-check."""
        all_results: list[CheckResult] = []

        for _cat, check_fn in self.CHECK_SEQUENCE:
            results = check_fn()
            all_results.extend(results)

        # -- Task 3.3: wire --fix into runner --
        if fix:
            fixer = AutoFixer()
            fixed_results: list[CheckResult] = []
            for cr in all_results:
                if cr.status in ("warn", "fail"):
                    fixed = fixer.try_fix(cr)
                    if fixed is not None:
                        fixed_results.append(fixed)
                    else:
                        fixed_results.append(cr)
                else:
                    fixed_results.append(cr)
            all_results = fixed_results

        return PreflightReport(checks=all_results)


# ---------------------------------------------------------------------------
# CLI entry point  (Task 1.4)
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    """Parse args, run checks, format output, return exit code."""
    parser = argparse.ArgumentParser(
        description="Senzing Bootcamp — Environment Verification",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output report as JSON instead of human-readable text",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt auto-fix for simple issues (e.g. missing directories)",
    )
    args = parser.parse_args(argv)

    runner = CheckRunner()
    report = runner.run(fix=args.fix)

    if args.json_output:
        print(OutputFormatter.to_json(report))
    else:
        print(OutputFormatter.to_human(report))

    return 1 if report.verdict == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
