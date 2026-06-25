"""Config/integration checks for the steering-budget-headroom refactor.

# Feature: steering-budget-headroom

Concrete (non-``@given``) config tests that guard two invariants introduced by
the slicing refactor:

- Requirement 5.6: every keyword route target in ``steering-index.yaml`` names a
  steering file that exists on disk in the corpus.
- Requirements 8.4, 8.5: every new steering slice/root produced by this refactor
  ships under ``senzing-bootcamp/steering/`` and contains no external URL with an
  ``http`` scheme. (A ``<support@senzing.com>`` mailto-style email is allowed;
  only ``http`` scheme URLs are prohibited.)

The refactored corpus is a single fixed input, so these are example/config
tests rather than Hypothesis properties. Stdlib-only, with an optional PyYAML
fast path and a minimal stdlib fallback parser for the ``keywords`` block.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Test pattern: scripts aren't packages, so expose senzing-bootcamp/scripts on
# sys.path for parity with peer tests (shared convention).
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# The test file lives at ``<repo>/senzing-bootcamp/tests/``, so ``parents[2]``
# is the repo root and the steering corpus is two levels down.
_STEERING_DIR = Path(__file__).resolve().parents[2] / "senzing-bootcamp" / "steering"
_INDEX_PATH = _STEERING_DIR / "steering-index.yaml"

# Matches a real external URL (http or https scheme). The character class for the
# rest of the URL excludes whitespace and a few markdown delimiters so a bare
# scheme without a host is not treated as a URL. Assembled from parts so the
# literal scheme text does not appear verbatim in the source.
_SCHEME = "http" + "s?" + ":" + "/" + "/"
_URL_RE = re.compile(_SCHEME + r"[^\s)>\]\"']+")


def _new_steering_files() -> list[str]:
    """Return the steering files introduced or rewritten by this refactor.

    Includes the generated summary/critical/per-module slices and the
    hand-authored module-completion Root plus its concern slices. The numbered
    ``hook-registry-module-NN.md`` slices are discovered from disk so a new
    module slice is automatically covered.
    """
    module_slices = sorted(
        p.name for p in _STEERING_DIR.glob("hook-registry-module-*.md")
    )
    fixed = [
        "hook-registry.md",
        "hook-registry-critical.md",
        "module-completion.md",
        "module-completion-artifacts.md",
        "module-completion-error-handling.md",
        "module-completion-next-steps.md",
        "module-completion-track.md",
    ]
    return fixed + module_slices


def _load_keyword_routes() -> dict[str, str]:
    """Return the ``keywords`` map from ``steering-index.yaml``.

    Uses PyYAML when available, otherwise falls back to a minimal stdlib parser
    that reads the simple ``key: value.md`` lines under the top-level
    ``keywords:`` key (stopping at the next top-level key).

    Returns:
        Mapping of keyword to the steering filename it routes to.
    """
    content = _INDEX_PATH.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        index = yaml.safe_load(content)
        routes = index.get("keywords", {})
        return {str(k): str(v) for k, v in routes.items()}
    except Exception:
        return _parse_keywords_block(content)


def _parse_keywords_block(content: str) -> dict[str, str]:
    """Parse the ``keywords:`` block from raw YAML text (stdlib fallback).

    The keywords section is a flat map of ``key: value.md`` lines indented under
    the top-level ``keywords:`` key. Parsing stops at the next top-level key
    (a non-indented, non-blank line).

    Args:
        content: Full text of ``steering-index.yaml``.

    Returns:
        Mapping of keyword to routed filename.
    """
    routes: dict[str, str] = {}
    in_block = False
    for raw_line in content.splitlines():
        if not in_block:
            if re.match(r"^keywords:\s*$", raw_line):
                in_block = True
            continue
        # A non-indented, non-blank line ends the keywords block.
        if raw_line.strip() and not raw_line.startswith((" ", "\t")):
            break
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        match = re.match(r"^\s+(.+?):\s*(\S.*?)\s*$", raw_line)
        if match:
            key = match.group(1).strip().strip("'\"")
            value = match.group(2).strip().strip("'\"")
            routes[key] = value
    return routes


class TestKeywordRoutesResolve:
    """Every keyword route target names a file that exists in the corpus.

    **Validates: Requirements 5.6**
    """

    def test_keyword_block_is_non_empty(self) -> None:
        """Sanity check that the keywords map parsed to a non-empty mapping."""
        routes = _load_keyword_routes()
        assert routes, "no keyword routes parsed from steering-index.yaml"

    def test_every_keyword_target_exists_on_disk(self) -> None:
        """Each ``keywords`` route resolves to an existing ``.md`` file (Req 5.6)."""
        routes = _load_keyword_routes()
        missing = {
            keyword: target
            for keyword, target in routes.items()
            if not (_STEERING_DIR / target).is_file()
        }
        assert not missing, f"keyword routes point to missing files: {missing}"

    def test_new_slice_routes_are_present(self) -> None:
        """The completion-concern routes added by this refactor resolve on disk."""
        routes = _load_keyword_routes()
        expected = {
            "recap": "module-completion-artifacts.md",
            "journal": "module-completion-artifacts.md",
            "certificate": "module-completion-artifacts.md",
            "completion error": "module-completion-error-handling.md",
            "next step": "module-completion-next-steps.md",
            "track complete": "module-completion-track.md",
            "path completion": "module-completion-track.md",
            "celebration": "module-completion-track.md",
        }
        for keyword, target in expected.items():
            assert routes.get(keyword) == target, (
                f"keyword '{keyword}' should route to {target}, got {routes.get(keyword)}"
            )
            assert (_STEERING_DIR / target).is_file(), f"missing route target {target}"


class TestNewSlicesHaveNoExternalUrls:
    """No new steering slice/root contains an external (http-scheme) URL.

    **Validates: Requirements 8.4, 8.5**
    """

    def test_new_files_exist_in_corpus(self) -> None:
        """Each refactor file ships under the steering corpus (Requirement 8.5)."""
        for filename in _new_steering_files():
            assert (_STEERING_DIR / filename).is_file(), (
                f"expected refactor file {filename} under {_STEERING_DIR}"
            )

    def test_per_module_slices_are_discovered(self) -> None:
        """The numbered per-module slices plus the ``any`` slice are present."""
        module_slices = {
            p.name for p in _STEERING_DIR.glob("hook-registry-module-*.md")
        }
        assert "hook-registry-module-any.md" in module_slices
        # At least the numbered slices for modules that have hooks must exist.
        numbered = {
            n for n in module_slices
            if re.fullmatch(r"hook-registry-module-\d{2}\.md", n)
        }
        assert numbered, "no numbered hook-registry-module-NN.md slices found"

    def test_no_external_urls_in_new_files(self) -> None:
        """No new slice/root contains an external (http-scheme) URL (Req 8.4)."""
        offenders: dict[str, list[str]] = {}
        for filename in _new_steering_files():
            content = (_STEERING_DIR / filename).read_text(encoding="utf-8")
            found = _URL_RE.findall(content)
            if found:
                offenders[filename] = found
        assert not offenders, f"external URLs found in new steering files: {offenders}"
