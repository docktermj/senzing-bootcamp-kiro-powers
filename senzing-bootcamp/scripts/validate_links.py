#!/usr/bin/env python3
"""Validate external URLs referenced in markdown files.

Checks that all https:// URLs in shipped markdown files return HTTP 2xx or 3xx.
Skips mailto: links and relative file references.

Usage:
    python senzing-bootcamp/scripts/validate_links.py
    python senzing-bootcamp/scripts/validate_links.py --timeout 10
    python senzing-bootcamp/scripts/validate_links.py --dry-run
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


POWER_DIR = Path(__file__).resolve().parent.parent
URL_PATTERN = re.compile(r"https?://[^\s\)>\]\"'`]+")

# URLs that are expected to be unreachable in CI (e.g., localhost examples)
SKIP_PATTERNS = [
    "localhost",
    "127.0.0.1",
    "example.com",
    "your-",
    "<your-",
    "placeholder",
]


def color(code: str, text: str) -> str:
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text


def green(t: str) -> str:
    return color("0;32", t)


def red(t: str) -> str:
    return color("0;31", t)


def yellow(t: str) -> str:
    return color("1;33", t)


def find_markdown_files() -> list[Path]:
    """Find all .md files in the power directory."""
    return sorted(POWER_DIR.rglob("*.md"))


def extract_urls(path: Path) -> list[tuple[int, str]]:
    """Extract all external URLs from a markdown file with line numbers."""
    results: list[tuple[int, str]] = []
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return results

    for line_num, line in enumerate(content.splitlines(), start=1):
        for match in URL_PATTERN.finditer(line):
            url = match.group(0).rstrip(".,;:!?)")
            # Skip non-http URLs and patterns we know won't resolve
            if any(skip in url for skip in SKIP_PATTERNS):
                continue
            results.append((line_num, url))
    return results


def check_url(url: str, timeout: int = 5) -> tuple[bool, str]:
    """Check if a URL is reachable. Returns (ok, status_message)."""
    try:
        req = urllib.request.Request(
            url,
            method="HEAD",
            headers={"User-Agent": "senzing-bootcamp-link-checker/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
            if code and 200 <= code < 400:
                return True, f"{code}"
            return False, f"{code}"
    except urllib.error.HTTPError as e:
        # Some servers reject HEAD, try GET
        if e.code == 405:
            try:
                req = urllib.request.Request(
                    url,
                    method="GET",
                    headers={"User-Agent": "senzing-bootcamp-link-checker/1.0"},
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    code = resp.getcode()
                    if code and 200 <= code < 400:
                        return True, f"{code}"
                    return False, f"{code}"
            except Exception as e2:
                return False, str(e2)[:60]
        return False, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return False, f"URLError: {e.reason}"[:60]
    except Exception as e:
        return False, str(e)[:60]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Validate external URLs in markdown files")
    parser.add_argument("--timeout", type=int, default=5, help="Request timeout in seconds")
    parser.add_argument("--dry-run", action="store_true", help="List URLs without checking")
    args = parser.parse_args(argv)

    md_files = find_markdown_files()
    print(f"Scanning {len(md_files)} markdown files in {POWER_DIR}...")

    # Deduplicate URLs across files
    url_locations: dict[str, list[str]] = {}
    for path in md_files:
        urls = extract_urls(path)
        rel_path = path.relative_to(POWER_DIR)
        for line_num, url in urls:
            if url not in url_locations:
                url_locations[url] = []
            url_locations[url].append(f"{rel_path}:{line_num}")

    print(f"Found {len(url_locations)} unique URLs\n")

    if args.dry_run:
        for url, locations in sorted(url_locations.items()):
            print(f"  {url}")
            for loc in locations[:3]:
                print(f"    └─ {loc}")
            if len(locations) > 3:
                print(f"    └─ ... and {len(locations) - 3} more")
        return

    failures: list[tuple[str, str, list[str]]] = []
    checked = 0

    for url, locations in sorted(url_locations.items()):
        ok, status = check_url(url, timeout=args.timeout)
        checked += 1
        if ok:
            print(f"  {green('✓')} {url} [{status}]")
        else:
            print(f"  {red('✗')} {url} [{status}]")
            for loc in locations[:3]:
                print(f"    └─ {loc}")
            failures.append((url, status, locations))

    print(f"\n{'=' * 50}")
    print(f"Checked: {checked} URLs")
    if failures:
        print(red(f"FAILED: {len(failures)} broken link(s)"))
        sys.exit(1)
    else:
        print(green("PASSED: All links valid"))


if __name__ == "__main__":
    main()
