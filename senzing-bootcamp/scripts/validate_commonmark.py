#!/usr/bin/env python3
"""Validate CommonMark compliance for all markdown files in the power.

Cross-platform: works on Linux, macOS, and Windows.
Requires: npm install -g markdownlint-cli
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def color_supported():
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


def main():
    print("🔍 Validating CommonMark compliance...")

    # Check for markdownlint
    ml_cmd = "markdownlint"
    if sys.platform == "win32":
        ml_cmd = "markdownlint.cmd" if shutil.which("markdownlint.cmd") else "markdownlint"

    if not shutil.which(ml_cmd):
        print(yellow("⚠️  markdownlint-cli not found"))
        print("Installing markdownlint-cli...")
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        try:
            subprocess.run([npm_cmd, "install", "-g", "markdownlint-cli"],
                           capture_output=True, timeout=120)
        except Exception:
            pass
        if not shutil.which(ml_cmd):
            print(red("❌ Failed to install markdownlint-cli"))
            print("Please install manually: npm install -g markdownlint-cli")
            sys.exit(1)

    # Create config if missing
    config_file = Path(".markdownlint.json")
    if not config_file.is_file():
        config = {
            "default": True,
            "MD013": False,
            "MD033": False,
            "MD041": False,
            "line-length": False,
        }
        config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
        print("✅ Created .markdownlint.json configuration")

    # Count markdown files
    md_files = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".history", ".git")]
        for f in files:
            if f.endswith(".md"):
                md_files.append(os.path.join(root, f))

    print(f"📄 Found {len(md_files)} markdown files")
    print()
    print("Running markdownlint...")

    result = subprocess.run(
        [ml_cmd, "**/*.md", "--ignore", "node_modules", "--ignore", ".history"],
        capture_output=True, text=True,
    )

    if result.returncode == 0:
        print(green("✅ All markdown files are CommonMark compliant!"))
    else:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(red("❌ CommonMark compliance issues found"))
        print()
        print("Common issues and fixes:")
        print("  MD022: Headings need blank lines before/after")
        print("  MD032: Lists need blank lines before/after")
        print("  MD040: Code blocks need language specified")
        print()
        print("To fix automatically, run:")
        print('  markdownlint --fix "**/*.md" --ignore node_modules --ignore .history')
        sys.exit(1)


if __name__ == "__main__":
    main()
