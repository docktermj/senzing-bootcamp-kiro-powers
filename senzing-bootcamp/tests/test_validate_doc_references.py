"""Tests for senzing-bootcamp/scripts/validate_doc_references.py.

Covers the doc-reference validator that guards against the class of drift where
a shipped script, steering file, or hook prompt points at a power-owned
documentation file that has been renamed or removed (the OFFLINE_MODE.md bug).

- ``TestShippedCorpus`` — the real shipped corpus has zero broken references and
  the matcher actually resolves a meaningful, non-vacuous set (script strings,
  hook-JSON prompts, and markdown links all get scanned).
- ``TestDetection`` — synthetic power trees exercise flag/allow behavior across
  scanned file types, excluded dirs, out-of-scope prefixes, globs, placeholders,
  and the documented allowlist.
- ``TestNormalization`` / ``TestPlaceholder`` — reference normalization and the
  placeholder heuristic.
- ``TestReferenceProperties`` — property-based: a reference resolves iff its
  target file exists under the power root.
- ``TestCli`` — the CLI entry point returns the right exit code.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import validate_doc_references as vdr  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(root: Path, rel: str, text: str) -> Path:
    """Create ``root/rel`` (with parents) containing ``text`` and return it."""
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _all_targets(power_dir: Path) -> set[str]:
    """Return the set of every reference target extracted from ``power_dir``."""
    targets: set[str] = set()
    for path in vdr.find_scanned_files(power_dir):
        for ref in vdr.extract_references(path, power_dir):
            targets.add(ref.target)
    return targets


# A filename segment that never trips the placeholder heuristic (lowercase only)
# and never collides with an allowlisted path.
_SAFE_NAME = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
    min_size=1,
    max_size=12,
).filter(lambda s: s.strip("-") != "")


# ===========================================================================
# TestShippedCorpus
# ===========================================================================


class TestShippedCorpus:
    """The real shipped power passes and is scanned non-vacuously."""

    def test_no_broken_references_in_shipped_power(self) -> None:
        """Every power-owned doc reference in the shipped tree resolves."""
        broken = vdr.find_broken_references(vdr.POWER_DIR)
        assert broken == [], (
            "Shipped power has references to missing doc files:\n"
            + "\n".join(f"  {b.source}:{b.line} -> {b.target}" for b in broken)
        )

    def test_scan_is_not_vacuous(self) -> None:
        """A meaningful number of references is actually checked."""
        targets = _all_targets(vdr.POWER_DIR)
        assert len(targets) > 25, (
            f"Expected the matcher to resolve many references, found {len(targets)}"
        )

    def test_scans_script_string_references(self) -> None:
        """A script-string reference (the OFFLINE_MODE bug class) is scanned."""
        assert "docs/guides/PERFORMANCE_BASELINES.md" in _all_targets(vdr.POWER_DIR)

    def test_scans_hook_json_prompt_references(self) -> None:
        """A steering reference embedded in a hook JSON prompt is scanned."""
        assert "steering/common-pitfalls.md" in _all_targets(vdr.POWER_DIR)


# ===========================================================================
# TestDetection
# ===========================================================================


class TestDetection:
    """Synthetic power trees exercise the flag/allow decisions."""

    def test_missing_reference_is_flagged(self, tmp_path: Path) -> None:
        """A reference to a nonexistent power doc is reported."""
        _write(tmp_path, "scripts/foo.py", 'x = "see docs/guides/GONE.md"\n')
        broken = vdr.find_broken_references(tmp_path)
        assert [b.target for b in broken] == ["docs/guides/GONE.md"]

    def test_existing_reference_passes(self, tmp_path: Path) -> None:
        """A reference to a real power doc is not reported."""
        _write(tmp_path, "docs/guides/REAL.md", "real\n")
        _write(tmp_path, "scripts/foo.py", 'x = "docs/guides/REAL.md"\n')
        assert vdr.find_broken_references(tmp_path) == []

    def test_markdown_and_json_sources_are_scanned(self, tmp_path: Path) -> None:
        """Broken references are caught in .md and .json files too."""
        _write(tmp_path, "steering/a.md", "See `docs/policies/MISSING.md`.\n")
        _write(tmp_path, "hooks/h.json", '{"prompt": "read steering/missing.md"}\n')
        targets = {b.target for b in vdr.find_broken_references(tmp_path)}
        assert targets == {"docs/policies/MISSING.md", "steering/missing.md"}

    def test_tests_dir_is_excluded(self, tmp_path: Path) -> None:
        """References inside the tests/ tree are ignored."""
        _write(tmp_path, "tests/test_x.py", 'x = "docs/guides/GONE.md"\n')
        assert vdr.find_broken_references(tmp_path) == []

    def test_changelog_is_excluded(self, tmp_path: Path) -> None:
        """The changelog (historical record) is ignored."""
        _write(tmp_path, "CHANGELOG.md", "removed `docs/guides/OLD.md`\n")
        assert vdr.find_broken_references(tmp_path) == []

    def test_bare_docs_path_is_out_of_scope(self, tmp_path: Path) -> None:
        """A bootcamper runtime path under bare docs/ is not treated as broken."""
        _write(tmp_path, "steering/a.md", "Create `docs/business_problem.md`.\n")
        assert vdr.find_broken_references(tmp_path) == []

    def test_docs_feedback_is_out_of_scope(self, tmp_path: Path) -> None:
        """docs/feedback/ (runtime outputs) is not treated as broken."""
        _write(tmp_path, "scripts/f.py", 'o = "docs/feedback/TEAM_FEEDBACK_REPORT.md"\n')
        assert vdr.find_broken_references(tmp_path) == []

    def test_glob_reference_is_skipped(self, tmp_path: Path) -> None:
        """A glob pattern like steering/module-*.md is not a concrete reference."""
        _write(tmp_path, "docs/guides/a.md", "Load `steering/module-*.md`.\n")
        assert vdr.find_broken_references(tmp_path) == []

    def test_module_number_placeholder_is_skipped(self, tmp_path: Path) -> None:
        """An NN module-number placeholder is not treated as a real reference."""
        _write(tmp_path, "docs/guides/a.md", "See `steering/hook-registry-module-NN.md`.\n")
        assert vdr.find_broken_references(tmp_path) == []

    def test_allowlisted_missing_reference_is_skipped(self, tmp_path: Path) -> None:
        """Documented intentional-missing references are exempt."""
        for target in vdr.ALLOWED_MISSING:
            _write(tmp_path, "scripts/f.py", f'x = "{target}"\n')
            assert vdr.find_broken_references(tmp_path) == [], target

    def test_yaml_example_reference_resolves(self, tmp_path: Path) -> None:
        """A templates/*.yaml.example reference is captured and resolved."""
        _write(tmp_path, "templates/team.yaml.example", "team: []\n")
        _write(tmp_path, "docs/guides/a.md", "Copy `templates/team.yaml.example`.\n")
        assert vdr.find_broken_references(tmp_path) == []


# ===========================================================================
# TestNormalization
# ===========================================================================


class TestNormalization:
    """Reference prefixes normalize to power-root-relative targets."""

    def test_relative_link_prefix_is_normalized(self, tmp_path: Path) -> None:
        """A ../../ markdown-link prefix resolves against the power root."""
        _write(tmp_path, "docs/modules/m.md", "[x](../../steering/gone.md)\n")
        assert [b.target for b in vdr.find_broken_references(tmp_path)] == [
            "steering/gone.md"
        ]

    def test_power_prefix_is_normalized(self, tmp_path: Path) -> None:
        """A senzing-bootcamp/ prefix resolves against the power root."""
        _write(tmp_path, "docs/guides/g.md", "See `senzing-bootcamp/steering/gone.md`.\n")
        assert [b.target for b in vdr.find_broken_references(tmp_path)] == [
            "steering/gone.md"
        ]

    def test_word_boundary_avoids_false_anchor(self, tmp_path: Path) -> None:
        """A word ending in an anchor name (e.g. mytemplates/) is not matched."""
        _write(tmp_path, "docs/guides/g.md", "path `mytemplates/foo.md` is unrelated\n")
        assert vdr.find_broken_references(tmp_path) == []


# ===========================================================================
# TestPlaceholder
# ===========================================================================


class TestPlaceholder:
    """The module-number placeholder heuristic."""

    def test_nn_token_is_placeholder(self) -> None:
        """An NN run delimited by separators is a placeholder."""
        assert vdr.is_placeholder("steering/hook-registry-module-NN.md")

    def test_single_n_token_is_placeholder(self) -> None:
        """A lone uppercase N segment is a placeholder."""
        assert vdr.is_placeholder("docs/modules/MODULE_N.md")

    def test_real_names_are_not_placeholders(self) -> None:
        """Concrete file names are not misread as placeholders."""
        for target in (
            "docs/guides/PERFORMANCE_BASELINES.md",
            "steering/module-07-query-visualize-discover.md",
            "docs/modules/MODULE_11_PACKAGING_DEPLOYMENT.md",
        ):
            assert not vdr.is_placeholder(target), target


# ===========================================================================
# TestReferenceProperties
# ===========================================================================


class TestReferenceProperties:
    """Property: a reference resolves iff its target file exists."""

    @given(anchor=st.sampled_from(vdr.ANCHOR_DIRS), name=_SAFE_NAME)
    def test_missing_target_always_flagged(self, anchor: str, name: str) -> None:
        """Any concrete reference to an absent file under an anchor is flagged."""
        target = f"{anchor}/{name}.md"
        if target in vdr.ALLOWED_MISSING:
            return
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "scripts/probe.py", f'x = "{target}"\n')
            broken = vdr.find_broken_references(root)
            assert [b.target for b in broken] == [target]

    @given(anchor=st.sampled_from(vdr.ANCHOR_DIRS), name=_SAFE_NAME)
    def test_present_target_never_flagged(self, anchor: str, name: str) -> None:
        """A reference to an existing file under an anchor is never flagged."""
        target = f"{anchor}/{name}.md"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, target, "content\n")
            _write(root, "scripts/probe.py", f'x = "{target}"\n')
            assert vdr.find_broken_references(root) == []


# ===========================================================================
# TestCli
# ===========================================================================


class TestCli:
    """The CLI entry point maps results to exit codes."""

    def test_main_passes_on_shipped_power(self) -> None:
        """main() returns 0 against the clean shipped corpus."""
        assert vdr.main([]) == 0

    def test_main_list_mode_passes(self) -> None:
        """--list still returns 0 when nothing is broken."""
        assert vdr.main(["--list"]) == 0
