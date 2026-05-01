"""Verification tests for the Module 11 rename: Packaging and Deployment.

These tests assert that every reference to Module 11 uses the new name
"Packaging and Deployment" (not "Deployment and Packaging") and that the
module doc file has been renamed accordingly.

Tests are EXPECTED TO FAIL before the rename is applied — that confirms
the old name is still present. After the rename, all tests should pass.

Feature: rename-module11-packaging-deployment
Requirements: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths — relative to the senzing-bootcamp/ directory
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent

_STEERING_FILE = _BOOTCAMP_DIR / "steering" / "module-11-deployment.md"
_MODULE_DOC_NEW = _BOOTCAMP_DIR / "docs" / "modules" / "MODULE_11_PACKAGING_DEPLOYMENT.md"
_MODULE_DOC_OLD = _BOOTCAMP_DIR / "docs" / "modules" / "MODULE_11_DEPLOYMENT_PACKAGING.md"
_MODULES_README = _BOOTCAMP_DIR / "docs" / "modules" / "README.md"
_DOCS_README = _BOOTCAMP_DIR / "docs" / "README.md"
_STAKEHOLDER = _BOOTCAMP_DIR / "templates" / "stakeholder_summary.md"
_GRADUATION_REF = _BOOTCAMP_DIR / "steering" / "graduation-reference.md"
_PREREQUISITES = _BOOTCAMP_DIR / "docs" / "diagrams" / "module-prerequisites.md"
_POWER_MD = _BOOTCAMP_DIR / "POWER.md"
_STEERING_INDEX = _BOOTCAMP_DIR / "steering" / "steering-index.yaml"


class TestRenameModule11:
    """Verify all Module 11 references use 'Packaging and Deployment'."""

    # -----------------------------------------------------------------------
    # Requirement 2: Module doc file rename
    # -----------------------------------------------------------------------

    def test_new_module_doc_exists(self) -> None:
        """MODULE_11_PACKAGING_DEPLOYMENT.md must exist."""
        assert _MODULE_DOC_NEW.exists(), (
            f"Expected renamed file at {_MODULE_DOC_NEW} but it does not exist"
        )

    def test_old_module_doc_absent(self) -> None:
        """MODULE_11_DEPLOYMENT_PACKAGING.md must NOT exist."""
        assert not _MODULE_DOC_OLD.exists(), (
            f"Old file {_MODULE_DOC_OLD} still exists — it should have been renamed"
        )

    # -----------------------------------------------------------------------
    # Requirement 1: Steering file heading and Module_Doc reference
    # -----------------------------------------------------------------------

    def test_steering_heading(self) -> None:
        """Steering heading must be '# Module 11: Packaging and Deployment'."""
        content = _STEERING_FILE.read_text(encoding="utf-8")
        assert "# Module 11: Packaging and Deployment" in content, (
            "Steering file does not contain the heading "
            "'# Module 11: Packaging and Deployment'"
        )

    def test_steering_module_doc_reference(self) -> None:
        """Steering Module_Doc reference must use MODULE_11_PACKAGING_DEPLOYMENT.md."""
        content = _STEERING_FILE.read_text(encoding="utf-8")
        assert "MODULE_11_PACKAGING_DEPLOYMENT.md" in content, (
            "Steering file does not reference MODULE_11_PACKAGING_DEPLOYMENT.md"
        )

    # -----------------------------------------------------------------------
    # Requirement 3: Module documentation index
    # -----------------------------------------------------------------------

    def test_modules_readme_links_new_filename(self) -> None:
        """docs/modules/README.md must link to MODULE_11_PACKAGING_DEPLOYMENT.md."""
        content = _MODULES_README.read_text(encoding="utf-8")
        assert "MODULE_11_PACKAGING_DEPLOYMENT.md" in content, (
            "docs/modules/README.md does not link to MODULE_11_PACKAGING_DEPLOYMENT.md"
        )

    # -----------------------------------------------------------------------
    # Requirement 4: Docs README file listing
    # -----------------------------------------------------------------------

    def test_docs_readme_references_new_filename(self) -> None:
        """docs/README.md must reference MODULE_11_PACKAGING_DEPLOYMENT.md."""
        content = _DOCS_README.read_text(encoding="utf-8")
        assert "MODULE_11_PACKAGING_DEPLOYMENT.md" in content, (
            "docs/README.md does not reference MODULE_11_PACKAGING_DEPLOYMENT.md"
        )

    def test_docs_readme_description(self) -> None:
        """docs/README.md must describe Module 11 as 'Packaging and deployment'."""
        content = _DOCS_README.read_text(encoding="utf-8")
        assert "Packaging and deployment" in content, (
            "docs/README.md does not contain the description 'Packaging and deployment'"
        )

    # -----------------------------------------------------------------------
    # Requirement 5: Stakeholder summary — Module 11 section
    # -----------------------------------------------------------------------

    def test_stakeholder_section_header(self) -> None:
        """Stakeholder summary Module 11 header must say 'Packaging and Deployment'."""
        content = _STAKEHOLDER.read_text(encoding="utf-8")
        assert "MODULE 11 — Packaging and Deployment" in content, (
            "stakeholder_summary.md does not contain "
            "'MODULE 11 — Packaging and Deployment'"
        )

    def test_stakeholder_module_name_placeholder(self) -> None:
        """Stakeholder summary [module_name] placeholder must say 'Packaging and Deployment'."""
        content = _STAKEHOLDER.read_text(encoding="utf-8")
        # The placeholder line: [module_name]   → "Packaging and Deployment"
        assert '"Packaging and Deployment"' in content, (
            "stakeholder_summary.md does not contain "
            "'\"Packaging and Deployment\"' in the [module_name] placeholder"
        )

    # -----------------------------------------------------------------------
    # Requirement 9: Stakeholder summary — Module 10 next-steps
    # -----------------------------------------------------------------------

    def test_stakeholder_module10_next_steps(self) -> None:
        """Module 10 next-steps must say 'packaging and deployment (Module 11)'."""
        content = _STAKEHOLDER.read_text(encoding="utf-8")
        assert "packaging and deployment (Module 11)" in content, (
            "stakeholder_summary.md does not contain "
            "'packaging and deployment (Module 11)' in Module 10 next-steps"
        )

    # -----------------------------------------------------------------------
    # Requirement 6: Graduation reference
    # -----------------------------------------------------------------------

    def test_graduation_ref_review_line(self) -> None:
        """Graduation reference must say 'Review packaging and deployment from Module 11'."""
        content = _GRADUATION_REF.read_text(encoding="utf-8")
        assert "Review packaging and deployment from Module 11" in content, (
            "graduation-reference.md does not contain "
            "'Review packaging and deployment from Module 11'"
        )

    def test_graduation_ref_not_covered_line(self) -> None:
        """Graduation reference must say 'Packaging and deployment was not covered'."""
        content = _GRADUATION_REF.read_text(encoding="utf-8")
        assert "Packaging and deployment was not covered" in content, (
            "graduation-reference.md does not contain "
            "'Packaging and deployment was not covered'"
        )

    # -----------------------------------------------------------------------
    # Requirement 7: Module prerequisites diagram
    # -----------------------------------------------------------------------

    def test_prerequisites_diagram_label(self) -> None:
        """Mermaid diagram label must be 'Module 11: Package & Deploy' (no 'Monitoring')."""
        content = _PREREQUISITES.read_text(encoding="utf-8")
        assert "Module 11: Package & Deploy" in content, (
            "module-prerequisites.md does not contain "
            "'Module 11: Package & Deploy'"
        )
        assert "Module 11: Monitoring" not in content, (
            "module-prerequisites.md still contains 'Module 11: Monitoring' — "
            "Monitoring is Module 10, not Module 11"
        )

    # -----------------------------------------------------------------------
    # Requirement 10: Preserved files — must NOT be modified
    # -----------------------------------------------------------------------

    def test_power_md_unchanged(self) -> None:
        """POWER.md must still contain 'Package & Deploy' (already correct order)."""
        content = _POWER_MD.read_text(encoding="utf-8")
        assert "Package & Deploy" in content, (
            "POWER.md no longer contains 'Package & Deploy' — it should be unchanged"
        )
        assert "Package and Deploy" in content, (
            "POWER.md no longer contains 'Package and Deploy' — it should be unchanged"
        )

    def test_steering_index_unchanged(self) -> None:
        """steering-index.yaml must still reference module-11-deployment.md."""
        content = _STEERING_INDEX.read_text(encoding="utf-8")
        assert "module-11-deployment.md" in content, (
            "steering-index.yaml no longer references module-11-deployment.md — "
            "it should be unchanged"
        )

    def test_steering_filename_preserved(self) -> None:
        """The steering filename module-11-deployment.md must still exist."""
        assert _STEERING_FILE.exists(), (
            "Steering file module-11-deployment.md no longer exists — "
            "the filename should be preserved"
        )
