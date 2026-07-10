"""URL-governance validation helper for the ``truthset-fallback-source`` feature.

This is a **test-only** helper co-located with the property/unit tests for the
``truthset-fallback-source`` feature. Unlike the pure ``truthset_fallback_model``
module (which performs no I/O), this helper does clearly-bounded filesystem reads:
it walks the distributed power tree and reports every file that embeds the raw
fallback source URL.

It encodes the enforcement side of the "single source of truth" governance rule
described by Requirement 6.1 and design ``Property 7``:

* The fallback source location is declared in exactly one place — the
  Sanctioned_Source_Registry (``config/fallback_sources.yaml``).
* Every other file in the power must reference the fallback source by its
  registry *identifier* (e.g. ``senzing_truthset_demo``), never by embedding the
  raw URL.

The raw URL is **not** hardcoded here — that would defeat the governance rule.
Instead it is derived at runtime from the registry via the same parser the
fetcher script uses (``scripts/fetch_fallback_truthset.py``), so the check always
tracks whatever URL the registry currently declares.

The single entry point is :func:`find_raw_url_violations`. An empty returned list
means governance is satisfied (no leaks); a non-empty list names the offending
files. The Property 7 test (task 6.2) and the unit tests (task 6.4) exercise this
helper.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

# ---------------------------------------------------------------------------
# Make the power scripts importable (scripts aren't a package) so the raw
# fallback URL can be derived from the registry parser rather than re-parsed
# or hardcoded here.
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from fetch_fallback_truthset import parse_registry  # noqa: E402

__all__ = [
    "DEFAULT_REGISTRY_RELPATH",
    "SKIP_DIR_NAMES",
    "SKIP_FILE_SUFFIXES",
    "default_power_root",
    "registry_url_fragments",
    "find_raw_url_violations",
]

# Registry file, relative to the power root, that owns the raw URL and is the one
# file excluded from the scan.
DEFAULT_REGISTRY_RELPATH = "config/fallback_sources.yaml"

# Directory names pruned from the walk: version control, caches, and build/tool
# artifacts that are never authored power content and can hold huge file counts
# (e.g. the Hypothesis example database).
SKIP_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        "__pycache__",
        ".hypothesis",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "venv",
        "node_modules",
        ".idea",
        ".vscode",
    }
)

# File suffixes skipped as binary/irrelevant. Any binary file that slips past this
# list is still skipped by the UTF-8 decode guard in :func:`find_raw_url_violations`.
SKIP_FILE_SUFFIXES: frozenset[str] = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".ico",
        ".bmp",
        ".webp",
        ".pdf",
        ".pyc",
        ".pyo",
        ".so",
        ".dll",
        ".dylib",
        ".zip",
        ".gz",
        ".tar",
        ".tgz",
        ".bz2",
        ".xz",
        ".7z",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".otf",
        ".mp3",
        ".mp4",
        ".mov",
        ".avi",
        ".wav",
    }
)


def default_power_root() -> Path:
    """Return the distributed power root (the ``senzing-bootcamp/`` directory).

    Resolved relative to this file's location so callers do not depend on the
    current working directory.

    Returns:
        The absolute path to the ``senzing-bootcamp/`` directory.
    """
    return Path(__file__).resolve().parent.parent


def _url_variants(base_url: str) -> set[str]:
    """Derive the searchable fragments that identify one raw fallback URL.

    Returns the exact URL plus two progressively shorter fragments so a *partial*
    embedding is caught even when the scheme is dropped or only the repository is
    referenced:

    1. the exact ``base_url`` (e.g. ``https://host/owner/repo/main/dir``),
    2. the URL with its scheme removed (``host/owner/repo/main/dir``), and
    3. the host plus the first two path segments (``host/owner/repo``) when the
       path has at least two segments.

    All three are specific to the declared host and repository, so an unrelated
    placeholder URL (a different host and repo) is never matched.

    Args:
        base_url: The raw ``base_url`` declared for one registry source.

    Returns:
        The set of non-empty fragments to search files for (empty when
        ``base_url`` is blank).
    """
    base_url = base_url.strip()
    if not base_url:
        return set()

    variants = {base_url}
    split = urlsplit(base_url)
    netloc = split.netloc
    path = split.path
    if netloc:
        variants.add(f"{netloc}{path}")
        segments = [segment for segment in path.split("/") if segment]
        if len(segments) >= 2:
            variants.add(f"{netloc}/{segments[0]}/{segments[1]}")
    return {variant for variant in variants if variant}


def registry_url_fragments(registry_path: str | Path) -> set[str]:
    """Derive the raw-URL fragments to guard against, from the registry file.

    Reads the Sanctioned_Source_Registry, parses it with the same parser the
    fetcher script uses, and collects the URL variants (see :func:`_url_variants`)
    for every declared source's ``base_url``. This is the sole place the "raw URL"
    is obtained — it is never hardcoded in this module.

    Args:
        registry_path: Path to ``fallback_sources.yaml``.

    Returns:
        The set of URL fragments whose presence in any other file is a violation.

    Raises:
        OSError: When the registry file cannot be read.
        ValueError: When the registry is not well-formed YAML the parser accepts.
    """
    text = Path(registry_path).read_text(encoding="utf-8")
    registry = parse_registry(text)

    fragments: set[str] = set()
    sources = registry.get("sources")
    if isinstance(sources, dict):
        for source in sources.values():
            if not isinstance(source, dict):
                continue
            base_url = source.get("base_url")
            if isinstance(base_url, str):
                fragments |= _url_variants(base_url)
    return fragments


def find_raw_url_violations(
    power_root: str | Path,
    registry_relpath: str = DEFAULT_REGISTRY_RELPATH,
) -> list[Path]:
    """Find files in the distributed power that embed the raw fallback URL.

    Walks ``power_root`` and returns every text file that contains the raw
    fallback source URL (or an identifying fragment of it), **excluding** the
    registry file itself, which is the one sanctioned place the URL is declared.
    Directories in :data:`SKIP_DIR_NAMES`, files whose suffix is in
    :data:`SKIP_FILE_SUFFIXES`, and files that are not valid UTF-8 text are
    skipped. An empty result means the "single source of truth" governance rule
    (Requirement 6.1 / Property 7) holds.

    Args:
        power_root: Root of the distributed power tree (``senzing-bootcamp/``).
        registry_relpath: Path to the registry file relative to ``power_root``;
            this file is the sole exclusion from the scan.

    Returns:
        A sorted list of paths (rooted the same way as ``power_root``) that embed
        the raw URL. Empty when governance is satisfied.

    Raises:
        OSError: When the registry file cannot be read.
        ValueError: When the registry is not well-formed YAML the parser accepts.
    """
    power_root = Path(power_root)
    registry_path = power_root / registry_relpath
    fragments = registry_url_fragments(registry_path)
    if not fragments:
        return []

    registry_resolved = registry_path.resolve()
    violations: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(power_root):
        # Prune skipped directories in place so os.walk never descends into them.
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIR_NAMES]
        for filename in filenames:
            file_path = Path(dirpath) / filename
            if file_path.suffix.lower() in SKIP_FILE_SUFFIXES:
                continue
            if file_path.resolve() == registry_resolved:
                continue
            try:
                text = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                # Non-UTF-8 (binary) or unreadable files carry no text URL.
                continue
            if any(fragment in text for fragment in fragments):
                violations.append(file_path)

    return sorted(violations)
