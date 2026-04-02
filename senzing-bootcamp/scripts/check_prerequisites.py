#!/usr/bin/env python3
"""Senzing Boot Camp - Prerequisites Checker.

Validates environment before starting modules (language-agnostic).
Cross-platform: works on Linux, macOS, and Windows.
"""

import os
import shutil
import subprocess
import sys

PASSED = 0
FAILED = 0
WARNINGS = 0


def color_supported():
    """Return True if the terminal likely supports ANSI colors."""
    if os.environ.get("NO_COLOR"):
        return False
    if sys.platform == "win32":
        return os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM") or "ANSICON" in os.environ
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


USE_COLOR = color_supported()


def c(code, text):
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def green(t): return c("0;32", t)
def red(t): return c("0;31", t)
def yellow(t): return c("1;33", t)
def blue(t): return c("0;34", t)
def cyan(t): return c("0;36", t)


def get_version(cmd, args=None):
    """Run a command to get its version string."""
    if args is None:
        args = ["--version"]
    try:
        r = subprocess.run([cmd] + args, capture_output=True, text=True, timeout=10)
        output = r.stdout.strip() or r.stderr.strip()
        return output.splitlines()[0] if output else "unknown"
    except Exception:
        return None


def check_command(cmd, name, required, install_hint):
    global PASSED, FAILED, WARNINGS
    if shutil.which(cmd):
        ver = get_version(cmd) or "unknown"
        print(f"  {green('✓')} {name}: {green('installed')} ({ver})")
        PASSED += 1
        return True
    else:
        if required:
            print(f"  {red('✗')} {name}: {red('NOT FOUND')} (required)")
            print(f"    {yellow('Install:')} {install_hint}")
            FAILED += 1
        else:
            print(f"  {yellow('⚠')} {name}: {yellow('NOT FOUND')} (optional)")
            print(f"    {yellow('Install:')} {install_hint}")
            WARNINGS += 1
        return False



def main():
    global PASSED, FAILED, WARNINGS

    print(blue("╔════════════════════════════════════════════════════════════╗"))
    print(blue("║") + "  Senzing Boot Camp - Prerequisites Check                  " + blue("║"))
    print(blue("╚════════════════════════════════════════════════════════════╝"))
    print()

    # --- Core Requirements ---
    print(blue("Core Requirements:"))
    print()

    check_command("git", "Git", True,
                  "https://git-scm.com/downloads")
    check_command("curl", "curl", True,
                  "https://curl.se/download.html (included on most systems)")

    # zip/unzip are not standard on Windows; Python zipfile is used by our scripts instead
    if sys.platform != "win32":
        check_command("zip", "zip", True,
                      "sudo apt install zip (Ubuntu) or brew install zip (macOS)")
        check_command("unzip", "unzip", True,
                      "sudo apt install unzip (Ubuntu) or brew install unzip (macOS)")

    # --- Language Runtimes ---
    print()
    print(blue("Language Runtimes (at least one required):"))
    print()

    lang_count = 0

    # Python
    py_cmd = "python3" if shutil.which("python3") else ("python" if shutil.which("python") else None)
    if py_cmd:
        ver = get_version(py_cmd) or "unknown"
        print(f"  {green('✓')} Python: {green('installed')} ({ver})")
        PASSED += 1
        lang_count += 1
        pip_cmd = "pip3" if shutil.which("pip3") else ("pip" if shutil.which("pip") else None)
        if pip_cmd:
            print(f"  {green('✓')}   pip: {green('installed')}")
            PASSED += 1
        else:
            print(f"  {yellow('⚠')}   pip: {yellow('NOT FOUND')} (needed for Python SDK)")
            WARNINGS += 1
    else:
        print(f"  {yellow('○')} Python: not installed")

    # Java
    if shutil.which("java"):
        ver = get_version("java") or "unknown"
        print(f"  {green('✓')} Java: {green('installed')} ({ver})")
        PASSED += 1
        lang_count += 1
    else:
        print(f"  {yellow('○')} Java: not installed")

    # .NET
    if shutil.which("dotnet"):
        ver = get_version("dotnet") or "unknown"
        print(f"  {green('✓')} .NET SDK: {green('installed')} ({ver})")
        PASSED += 1
        lang_count += 1
    else:
        print(f"  {yellow('○')} .NET SDK: not installed")

    # Rust
    if shutil.which("rustc"):
        ver = get_version("rustc") or "unknown"
        print(f"  {green('✓')} Rust: {green('installed')} ({ver})")
        PASSED += 1
        lang_count += 1
    else:
        print(f"  {yellow('○')} Rust: not installed")

    # Node.js
    if shutil.which("node"):
        ver = get_version("node") or "unknown"
        print(f"  {green('✓')} Node.js: {green('installed')} ({ver})")
        PASSED += 1
        lang_count += 1
    else:
        print(f"  {yellow('○')} Node.js: not installed")

    if lang_count == 0:
        print()
        print(f"  {red('✗')} No supported language runtime found")
        print(f"    {yellow('Install one of:')} Python 3.10+, Java 17+, .NET SDK, Rust, or Node.js")
        FAILED += 1

    # --- Optional Tools ---
    print()
    print(blue("Optional Tools:"))
    print()

    check_command("psql", "PostgreSQL client", False,
                  "https://www.postgresql.org/download/")
    check_command("jq", "jq (JSON processor)", False,
                  "https://jqlang.github.io/jq/download/")

    # --- Directory Structure ---
    print()
    print(blue("Directory Structure:"))
    print()

    dirs = [
        os.path.join("data", "raw"),
        os.path.join("data", "transformed"),
        "database", "src", "scripts", "docs", "backups", "licenses",
    ]
    for d in dirs:
        if os.path.isdir(d):
            print(f"  {green('✓')} Directory '{d}': {green('exists')}")
            PASSED += 1
        else:
            print(f"  {yellow('⚠')} Directory '{d}': {yellow('missing')}")
            WARNINGS += 1

    # --- Configuration Files ---
    print()
    print(blue("Configuration Files:"))
    print()

    for fname in [".gitignore", ".env.example", "README.md"]:
        if os.path.isfile(fname):
            print(f"  {green('✓')} {fname}: {green('exists')}")
            PASSED += 1
        else:
            print(f"  {yellow('⚠')} {fname}: {yellow('missing')}")
            WARNINGS += 1

    # --- Summary ---
    print()
    print(blue("═══════════════════════════════════════════════════════════"))
    print()
    print(f"  {green('Passed:')} {PASSED}")
    print(f"  {yellow('Warnings:')} {WARNINGS}")
    print(f"  {red('Failed:')} {FAILED}")
    print()

    if FAILED == 0:
        if WARNINGS == 0:
            print(green("✓ All prerequisites met! Ready to start the boot camp."))
        else:
            print(yellow("⚠ Some optional prerequisites missing, but you can proceed."))
    else:
        print(red("✗ Missing required prerequisites. Please install them before starting."))
        sys.exit(1)


if __name__ == "__main__":
    main()
