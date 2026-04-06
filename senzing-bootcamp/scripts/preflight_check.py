#!/usr/bin/env python3
"""Senzing Bootcamp Pre-flight Check.

Checks core system requirements (language-agnostic).
Cross-platform: works on Linux, macOS, and Windows.
"""

import os
import shutil
import subprocess
import sys
import tempfile

ERRORS = 0
WARNINGS = 0


def get_version(cmd, args=None):
    if args is None:
        args = ["--version"]
    try:
        r = subprocess.run([cmd] + args, capture_output=True, text=True, timeout=10)
        out = r.stdout.strip() or r.stderr.strip()
        return out.splitlines()[0] if out else "unknown"
    except Exception:
        return None


def main():
    global ERRORS, WARNINGS

    print("==================================")
    print("SENZING BOOTCAMP PRE-FLIGHT CHECK")
    print("==================================")
    print()

    # --- Language runtimes ---
    print("Checking language runtimes...")
    lang_found = 0

    py_cmd = "python3" if shutil.which("python3") else ("python" if shutil.which("python") else None)
    if py_cmd:
        ver = get_version(py_cmd) or "unknown"
        print(f"  ✅ Python {ver}")
        lang_found += 1
    if shutil.which("java"):
        print(f"  ✅ Java {get_version('java') or 'unknown'}")
        lang_found += 1
    if shutil.which("dotnet"):
        print(f"  ✅ .NET {get_version('dotnet') or 'unknown'}")
        lang_found += 1
    if shutil.which("rustc"):
        print(f"  ✅ Rust {get_version('rustc') or 'unknown'}")
        lang_found += 1
    if shutil.which("node"):
        print(f"  ✅ Node.js {get_version('node') or 'unknown'}")
        lang_found += 1

    if lang_found == 0:
        print("  ❌ No supported language runtime found")
        print("     Install one of: Python 3.10+, Java 17+, .NET SDK, Rust, or Node.js")
        ERRORS += 1
    print()

    # --- Disk space ---
    print("Checking disk space...")
    try:
        usage = shutil.disk_usage(os.getcwd())
        avail_gb = usage.free / (1024 ** 3)
        if avail_gb >= 10:
            print(f"  ✅ {avail_gb:.0f}GB available (10GB+ required)")
        else:
            print(f"  ⚠️  {avail_gb:.1f}GB available (10GB+ recommended)")
            WARNINGS += 1
    except Exception:
        print("  ⚠️  Could not verify disk space (10GB+ recommended)")
        WARNINGS += 1
    print()

    # --- Memory ---
    print("Checking memory...")
    total_gb = _get_total_memory_gb()
    if total_gb is not None:
        if total_gb >= 4:
            print(f"  ✅ {total_gb:.0f}GB RAM (4GB+ required)")
        else:
            print(f"  ⚠️  {total_gb:.0f}GB RAM (4GB+ recommended)")
            WARNINGS += 1
    else:
        print("  ⚠️  Cannot determine total memory")
        WARNINGS += 1
    print()

    # --- Git ---
    print("Checking Git...")
    if shutil.which("git"):
        print("  ✅ Git installed")
    else:
        print("  ⚠️  Git not found (recommended)")
        WARNINGS += 1
    print()

    # --- PostgreSQL ---
    print("Checking PostgreSQL...")
    if shutil.which("psql"):
        print("  ✅ PostgreSQL client installed")
    else:
        print("  ℹ️  PostgreSQL not found (optional — SQLite works for evaluation)")
    print()

    # --- Write permissions ---
    print("Checking permissions...")
    test_dir = os.path.join(os.getcwd(), "_preflight_test")
    try:
        os.makedirs(test_dir, exist_ok=True)
        os.rmdir(test_dir)
        print("  ✅ Write permissions OK")
    except OSError:
        print("  ❌ Cannot write to current directory")
        ERRORS += 1
    print()

    # --- Summary ---
    print("==================================")
    print("SUMMARY")
    print("==================================")
    print(f"  Errors:   {ERRORS}")
    print(f"  Warnings: {WARNINGS}")
    print()

    if ERRORS == 0:
        print("✅ PRE-FLIGHT CHECK PASSED!")
        print("You're ready to start the Senzing Bootcamp.")
        print("The agent will ask which language you'd like to use.")
    else:
        print("❌ PRE-FLIGHT CHECK FAILED")
        print("Please fix the errors above before starting.")
        sys.exit(1)


def _get_total_memory_gb():
    """Return total physical memory in GB, or None if unavailable."""
    # Linux
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return kb / (1024 * 1024)
        except Exception:
            pass
    # macOS
    if sys.platform == "darwin":
        try:
            r = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5)
            return int(r.stdout.strip()) / (1024 ** 3)
        except Exception:
            pass
    # Windows
    if sys.platform == "win32":
        try:
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            return stat.ullTotalPhys / (1024 ** 3)
        except Exception:
            pass
    return None


if __name__ == "__main__":
    main()
