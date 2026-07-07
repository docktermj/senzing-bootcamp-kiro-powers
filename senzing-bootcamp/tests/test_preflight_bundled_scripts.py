"""Unit tests for the bundled-scripts preflight check and self-repair.

Covers the task 3.1 fix part: ``check_bundled_scripts`` warns (never fails)
when the bundled ``senzing-bootcamp/scripts/`` directory or a required script is
absent, and ``AutoFixer`` materializes/restores the directory under ``--fix``
idempotently without clobbering already-present valid files.
"""

import importlib
from pathlib import Path


def _load_preflight():
    """Import / reload the preflight module, resetting globals."""
    import preflight
    importlib.reload(preflight)
    return preflight


def _make_source_dir(tmp_path: Path, mod) -> Path:
    """Create a fake bundled-scripts source dir with all required scripts."""
    source = tmp_path / "power_source"
    source.mkdir()
    for name in mod.REQUIRED_BUNDLED_SCRIPTS:
        (source / name).write_text(f"# {name}\n", encoding="utf-8")
    # A non-file entry should be skipped by the materializer.
    (source / "__pycache__").mkdir()
    return source


class TestCheckBundledScripts:
    """Bundled-scripts presence check warns when absent, passes when present."""

    def test_missing_directory_warns(self, project_root):
        mod = _load_preflight()
        results = mod.check_bundled_scripts()
        assert len(results) == 1
        assert results[0].status == "warn"
        assert results[0].fix  # remediation hint present
        assert "preflight.py --fix" in results[0].fix

    def test_missing_required_script_warns(self, project_root):
        mod = _load_preflight()
        scripts_dir = project_root / "senzing-bootcamp" / "scripts"
        scripts_dir.mkdir(parents=True)
        # Create all but one required script.
        for name in mod.REQUIRED_BUNDLED_SCRIPTS[:-1]:
            (scripts_dir / name).write_text("x\n", encoding="utf-8")
        results = mod.check_bundled_scripts()
        assert results[0].status == "warn"
        missing_name = mod.REQUIRED_BUNDLED_SCRIPTS[-1]
        assert missing_name in results[0].message

    def test_all_present_passes(self, project_root):
        mod = _load_preflight()
        scripts_dir = project_root / "senzing-bootcamp" / "scripts"
        scripts_dir.mkdir(parents=True)
        for name in mod.REQUIRED_BUNDLED_SCRIPTS:
            (scripts_dir / name).write_text("x\n", encoding="utf-8")
        results = mod.check_bundled_scripts()
        assert results[0].status == "pass"

    def test_check_never_fails(self, project_root):
        """The check warns but must never emit a ``fail`` status."""
        mod = _load_preflight()
        results = mod.check_bundled_scripts()
        assert all(r.status != "fail" for r in results)


class TestAutoFixBundledScripts:
    """AutoFixer materializes/restores the directory idempotently, no clobber."""

    def test_materializes_missing_directory(self, project_root, monkeypatch):
        mod = _load_preflight()
        source = _make_source_dir(project_root, mod)
        monkeypatch.setattr(mod, "BUNDLED_SCRIPTS_SOURCE", str(source))

        warn = mod.check_bundled_scripts()[0]
        fixed = mod.AutoFixer.try_fix(warn)

        assert fixed is not None
        assert fixed.status == "pass"
        assert fixed.fixed is True
        scripts_dir = project_root / "senzing-bootcamp" / "scripts"
        for name in mod.REQUIRED_BUNDLED_SCRIPTS:
            assert (scripts_dir / name).is_file()
        # The non-file source entry must not be copied as a file.
        assert not (scripts_dir / "__pycache__").is_file()

    def test_no_clobber_of_existing_file(self, project_root, monkeypatch):
        mod = _load_preflight()
        source = _make_source_dir(project_root, mod)
        monkeypatch.setattr(mod, "BUNDLED_SCRIPTS_SOURCE", str(source))

        scripts_dir = project_root / "senzing-bootcamp" / "scripts"
        scripts_dir.mkdir(parents=True)
        preserved = scripts_dir / mod.REQUIRED_BUNDLED_SCRIPTS[0]
        preserved.write_text("CUSTOM-DO-NOT-OVERWRITE\n", encoding="utf-8")

        warn = mod.check_bundled_scripts()[0]
        mod.AutoFixer.try_fix(warn)

        # Already-present file left byte-for-byte unchanged.
        assert preserved.read_text(encoding="utf-8") == "CUSTOM-DO-NOT-OVERWRITE\n"
        # Other required scripts still materialized.
        for name in mod.REQUIRED_BUNDLED_SCRIPTS[1:]:
            assert (scripts_dir / name).is_file()

    def test_idempotent_repeated_fix(self, project_root, monkeypatch):
        mod = _load_preflight()
        source = _make_source_dir(project_root, mod)
        monkeypatch.setattr(mod, "BUNDLED_SCRIPTS_SOURCE", str(source))

        warn = mod.check_bundled_scripts()[0]
        first = mod.AutoFixer.try_fix(warn)
        scripts_dir = project_root / "senzing-bootcamp" / "scripts"
        snapshot = {
            name: (scripts_dir / name).read_text(encoding="utf-8")
            for name in mod.REQUIRED_BUNDLED_SCRIPTS
        }

        # Re-applying the same fix operation changes nothing and still succeeds.
        second = mod.AutoFixer.try_fix(warn)
        assert first.status == "pass"
        assert second.status == "pass"
        for name, content in snapshot.items():
            assert (scripts_dir / name).read_text(encoding="utf-8") == content

        # And once everything is present, the check reports pass with nothing to fix.
        assert mod.check_bundled_scripts()[0].status == "pass"

    def test_runner_fix_repairs_and_rechecks(self, project_root, monkeypatch):
        """End-to-end: ``CheckRunner.run(fix=True)`` repairs the warn to pass."""
        mod = _load_preflight()
        source = _make_source_dir(project_root, mod)
        monkeypatch.setattr(mod, "BUNDLED_SCRIPTS_SOURCE", str(source))

        report = mod.CheckRunner().run(fix=True)
        bundled = [c for c in report.checks if c.category == "Bundled Scripts"]
        assert bundled
        assert bundled[0].status == "pass"
        assert bundled[0].fixed is True
