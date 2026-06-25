"""Example-based unit tests for the steering file template and conformance rules.

Feature: steering-file-template
"""

import re
import sys
import tempfile
from pathlib import Path

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from lint_steering import (
    SECTION_ORDER,
    check_before_after_block,
    check_checkpoint_completeness,
    check_first_read_instruction,
    check_module_frontmatter,
    check_section_order,
    check_success_indicator,
    get_module_steering_files,
    run_all_checks,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_PATH = REPO_ROOT / "senzing-bootcamp" / "templates" / "module-steering-template.md"
STEERING_DIR = REPO_ROOT / "senzing-bootcamp" / "steering"
HOOKS_DIR = REPO_ROOT / "senzing-bootcamp" / "hooks"
INDEX_PATH = STEERING_DIR / "steering-index.yaml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_module_file(tmp_dir, content, filename="module-01-test.md"):
    """Write content to a module file in a temp steering directory."""
    steering_dir = Path(tmp_dir) / "steering"
    steering_dir.mkdir(parents=True, exist_ok=True)
    (steering_dir / filename).write_text(content, encoding="utf-8")
    return steering_dir


VALID_MODULE_CONTENT = """\
---
inclusion: manual
---

# Module 01 — Test Module

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — \
display the module start banner.

> **User reference:** See docs.

**Before/After:** Before state → After state.

**Prerequisites:** None

1. **Step 1 description**

   **Checkpoint:** Write step 1 to `config/bootcamp_progress.json`.

2. **Step 2 description**

   **Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.

**Success indicator:** ✅ Module complete.
"""


# ---------------------------------------------------------------------------
# Task 11.1: Template file exists
# ---------------------------------------------------------------------------


class TestTemplateFileExists:
    """Validates: Requirement 1.1"""

    def test_template_file_exists(self):
        """Template file exists at the expected path."""
        assert TEMPLATE_PATH.exists(), (
            f"Template file not found at {TEMPLATE_PATH}"
        )

    def test_template_file_is_not_empty(self):
        """Template file has content."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        assert len(content.strip()) > 0


# ---------------------------------------------------------------------------
# Task 11.2: Template contains all required sections in correct order
# ---------------------------------------------------------------------------


class TestTemplateSections:
    """Validates: Requirement 1.2"""

    def test_template_has_frontmatter(self):
        """Template starts with YAML frontmatter."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        assert content.startswith("---\n")

    def test_template_has_inclusion_manual(self):
        """Template frontmatter has inclusion: manual."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        assert "inclusion: manual" in content

    def test_template_has_first_read(self):
        """Template has first-read instruction."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        assert "**🚀 First:**" in content

    def test_template_has_before_after(self):
        """Template has Before/After block."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        assert re.search(r"\*\*Before/After\b", content, re.IGNORECASE)

    def test_template_has_workflow_steps(self):
        """Template has numbered workflow steps."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        assert re.search(r"^\d+\.\s", content, re.MULTILINE)

    def test_template_has_checkpoint(self):
        """Template has checkpoint instructions."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        assert "**Checkpoint:**" in content

    def test_template_has_success_indicator(self):
        """Template has success indicator."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        assert re.search(r"\*\*Success indicator\b", content, re.IGNORECASE)

    def test_template_sections_in_correct_order(self):
        """Template sections appear in the required order."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        lines = content.splitlines()

        positions = {}
        for i, line in enumerate(lines):
            if line.strip() == "---" and i == 0:
                positions["frontmatter"] = i
            if "**🚀 First:**" in line and "first_read" not in positions:
                positions["first_read"] = i
            if (
                re.search(r"\*\*Before/After\b", line, re.IGNORECASE)
                and "before_after" not in positions
            ):
                positions["before_after"] = i
            if re.match(r"^\d+\.\s", line) and "workflow_steps" not in positions:
                positions["workflow_steps"] = i
            if (
                re.search(r"\*\*Success indicator\b", line, re.IGNORECASE)
                and "success_indicator" not in positions
            ):
                positions["success_indicator"] = i

        # Verify all sections found
        for section in SECTION_ORDER:
            assert section in positions, f"Section '{section}' not found in template"

        # Verify order
        for i in range(len(SECTION_ORDER) - 1):
            a = SECTION_ORDER[i]
            b = SECTION_ORDER[i + 1]
            assert positions[a] < positions[b], (
                f"Section '{a}' (line {positions[a]}) should come before "
                f"'{b}' (line {positions[b]})"
            )


# ---------------------------------------------------------------------------
# Task 11.3: Template contains HTML comments
# ---------------------------------------------------------------------------


class TestTemplateComments:
    """Validates: Requirement 1.3"""

    def test_template_has_html_comments(self):
        """Template contains HTML comments."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        comments = re.findall(r"<!--.*?-->", content, re.DOTALL)
        assert len(comments) >= 3, (
            f"Expected at least 3 HTML comments, found {len(comments)}"
        )


# ---------------------------------------------------------------------------
# Task 11.4: Template contains placeholder values
# ---------------------------------------------------------------------------


class TestTemplatePlaceholders:
    """Validates: Requirement 1.4"""

    def test_template_has_nn_placeholder(self):
        """Template contains NN placeholder for module number."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        assert "NN" in content

    def test_template_has_module_title_placeholder(self):
        """Template contains [Module Title] placeholder."""
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        assert "[Module Title]" in content


# ---------------------------------------------------------------------------
# Task 11.5: Real module files have valid frontmatter
# ---------------------------------------------------------------------------


class TestRealModuleFrontmatter:
    """Validates: Requirements 2.1, 2.2"""

    def test_real_modules_have_valid_frontmatter(self):
        """All real module files have frontmatter with inclusion: manual."""
        violations = check_module_frontmatter(STEERING_DIR)
        # Filter to only root module files (not phase files)
        root_modules = [
            f"module-{n:02d}-" for n in range(1, 12)
        ]
        root_violations = [
            v for v in violations
            if any(rm in v.file for rm in root_modules)
            and "-phase" not in v.file
        ]
        assert len(root_violations) == 0, (
            f"Root module frontmatter violations: "
            f"{[v.format() for v in root_violations]}"
        )


# ---------------------------------------------------------------------------
# Task 11.6: Real module files have first-read instruction
# ---------------------------------------------------------------------------


class TestRealModuleFirstRead:
    """Validates: Requirements 3.1, 3.2"""

    def test_real_root_modules_have_first_read(self):
        """All root *workflow* module files have a first-read instruction.

        The module-03 monolith was split into a dispatcher
        (module-03-system-verification.md) plus phase sub-files
        (module-03-phaseN-*.md) and an on-demand reference file
        (module-03-visualization-api-reference.md). Phase sub-files already
        carry "-phase" in their name and are excluded. The reference file is
        NOT a workflow module — it is pure reference material ("loaded on demand
        from module-03-phase2-visualization.md") with no first-read step, so it
        is classified out alongside the phase sub-files (same treatment the
        linter gives non-workflow sub-files). The dispatcher itself still
        carries the first-read instruction and is asserted to do so below.
        """
        violations = check_first_read_instruction(STEERING_DIR)

        def _is_workflow_module(file_path: str) -> bool:
            name = Path(file_path).name
            # Exclude phase sub-files and on-demand reference files — they are
            # not standalone workflow modules and have no first-read step.
            return "-phase" not in name and "-reference" not in name

        root_violations = [
            v for v in violations
            if _is_workflow_module(v.file)
            and v.level == "ERROR"
        ]
        assert len(root_violations) == 0, (
            f"Root module first-read violations: "
            f"{[v.format() for v in root_violations]}"
        )

        # Independent content assertion: every shipped root *workflow* module
        # (a module-NN-*.md that the linter treats as a module and is not an
        # on-demand reference file) actually contains the first-read marker.
        # `get_module_steering_files` already excludes phase sub-files and
        # non-module files (module-completion/-prerequisites/-transitions); we
        # additionally exclude the reference file. This guards the re-targeting
        # so that excluding the reference file can never mask a genuine missing
        # first-read on a real workflow module.
        workflow_modules = [
            f for f in get_module_steering_files(STEERING_DIR)
            if "-reference" not in f.name
        ]
        assert workflow_modules, "Expected to find root workflow module files"
        missing = [
            f.name for f in workflow_modules
            if "**\U0001f680 First:**" not in f.read_text(encoding="utf-8")
        ]
        assert not missing, (
            f"Root workflow modules missing first-read instruction: {missing}"
        )

        # Independent content assertion: the excluded reference file really is
        # on-demand reference material (relocation artifact of the split), not a
        # mis-classified workflow module.
        ref_file = STEERING_DIR / "module-03-visualization-api-reference.md"
        if ref_file.exists():
            ref_text = ref_file.read_text(encoding="utf-8")
            assert "reference" in ref_text.lower(), (
                "module-03-visualization-api-reference.md should describe itself "
                "as reference material"
            )


# ---------------------------------------------------------------------------
# Task 11.7: Real module files have checkpoints for all steps
# ---------------------------------------------------------------------------


class TestRealModuleCheckpoints:
    """Validates: Requirements 5.1, 5.2"""

    def test_real_root_modules_with_simple_steps_have_checkpoints(self):
        """Root module files with simple step numbering have checkpoints."""
        violations = check_checkpoint_completeness(STEERING_DIR)
        # Only check module-04 which has straightforward numbering.
        # Module-01 now uses sub-step checkpoints (7a, 7b, etc.) and has
        # an Error Handling section with numbered items that are not
        # workflow steps, so it is excluded from this simple check.
        simple_modules = ["module-04-"]
        simple_violations = [
            v for v in violations
            if any(sm in v.file for sm in simple_modules)
        ]
        assert len(simple_violations) == 0, (
            f"Simple module checkpoint violations: "
            f"{[v.format() for v in simple_violations]}"
        )


# ---------------------------------------------------------------------------
# Task 11.8: --skip-template flag suppresses template violations
# ---------------------------------------------------------------------------


class TestSkipTemplateFlag:
    """Validates: Requirement 8.3"""

    def test_skip_template_suppresses_template_violations(self):
        """Running with skip_template=True produces no template violations."""
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, "# No frontmatter at all\n\nJust text.\n")
            # Without skip_template, should find violations
            violations_with = check_module_frontmatter(sd)
            assert len(violations_with) > 0

            # With skip_template in run_all_checks, template checks are skipped
            # We test this by verifying the flag works in run_all_checks
            hooks_dir = Path(tmp) / "hooks"
            hooks_dir.mkdir()
            index_path = Path(tmp) / "steering" / "steering-index.yaml"
            index_path.write_text(
                "modules:\nfile_metadata:\nkeywords:\nlanguages:\ndeployment:\n",
                encoding="utf-8",
            )
            violations_skip, _ = run_all_checks(
                sd, hooks_dir, index_path, skip_template=True
            )
            template_violations = [
                v for v in violations_skip
                if "module file" in v.message.lower()
                or "first-read instruction" in v.message.lower()
                or "before/after block" in v.message.lower()
                or "success indicator" in v.message.lower()
                or "section '" in v.message.lower()
            ]
            assert len(template_violations) == 0


# ---------------------------------------------------------------------------
# Task 11.9: Template violations use standard format
# ---------------------------------------------------------------------------


class TestViolationFormat:
    """Validates: Requirement 8.2"""

    def test_template_violations_use_standard_format(self):
        """Template violations match {level}: {file}:{line}: {message}."""
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, "# No frontmatter\n")
            violations = check_module_frontmatter(sd)
            assert len(violations) > 0
            pattern = re.compile(r"^(ERROR|WARNING): .+:\d+: .+$")
            for v in violations:
                formatted = v.format()
                assert pattern.match(formatted), (
                    f"Violation format mismatch: {formatted!r}"
                )

    def test_all_template_rule_violations_use_standard_format(self):
        """All template rule violations use the standard format."""
        with tempfile.TemporaryDirectory() as tmp:
            # Create a file that triggers violations from multiple rules
            content = "# No frontmatter, no sections\n\n1. Step without checkpoint\n"
            sd = _write_module_file(tmp, content)

            all_violations = []
            all_violations.extend(check_module_frontmatter(sd))
            all_violations.extend(check_first_read_instruction(sd))
            all_violations.extend(check_before_after_block(sd))
            all_violations.extend(check_checkpoint_completeness(sd))
            all_violations.extend(check_success_indicator(sd))
            all_violations.extend(check_section_order(sd))

            assert len(all_violations) > 0
            pattern = re.compile(r"^(ERROR|WARNING): .+:\d+: .+$")
            for v in all_violations:
                formatted = v.format()
                assert pattern.match(formatted), (
                    f"Violation format mismatch: {formatted!r}"
                )
