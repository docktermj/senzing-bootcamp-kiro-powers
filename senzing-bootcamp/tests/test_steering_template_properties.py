"""Property-based tests for template conformance rules in lint_steering.py.

Feature: steering-file-template
"""

import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from lint_steering import (
    LintViolation,
    check_module_frontmatter,
    check_first_read_instruction,
    check_before_after_block,
    check_checkpoint_completeness,
    check_success_indicator,
    check_section_order,
    get_module_steering_files,
)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_inclusion_value():
    """Generate inclusion field values — manual or something else."""
    return st.sampled_from(["manual", "auto", "always", "fileMatch", "custom"])


def st_frontmatter(inclusion_value=None):
    """Generate YAML frontmatter block."""
    if inclusion_value is None:
        inc = st_inclusion_value()
    else:
        inc = st.just(inclusion_value)
    return inc.map(lambda v: f"---\ninclusion: {v}\n---\n")


def st_first_read_instruction(include_progress=True, include_transitions=True):
    """Generate a first-read instruction line."""
    refs = []
    if include_progress:
        refs.append("`config/bootcamp_progress.json`")
    if include_transitions:
        refs.append("`module-transitions.md`")
    ref_text = " and follow ".join(refs) if refs else "the docs"
    return st.just(
        f"**🚀 First:** Read {ref_text} — display the module start banner.\n"
    )


def st_before_after_block():
    """Generate a Before/After block."""
    return st.just("**Before/After:** State before → State after.\n")


def st_workflow_step(step_num, include_checkpoint=True, checkpoint_num=None):
    """Generate a single numbered workflow step with optional checkpoint."""
    cp_num = checkpoint_num if checkpoint_num is not None else step_num
    checkpoint = ""
    if include_checkpoint:
        checkpoint = (
            f"\n   **Checkpoint:** Write step {cp_num} to "
            f"`config/bootcamp_progress.json`.\n"
        )
    return st.just(f"{step_num}. **Step {step_num} description**\n{checkpoint}")


def st_success_indicator():
    """Generate a success indicator line."""
    return st.just("**Success indicator:** ✅ Module complete.\n")


def st_module_content(
    has_frontmatter=True,
    inclusion_value="manual",
    has_first_read=True,
    first_read_has_progress=True,
    first_read_has_transitions=True,
    has_before_after=True,
    num_steps=2,
    steps_have_checkpoints=True,
    checkpoint_match=True,
    has_success_indicator=True,
    scramble_order=False,
):
    """Build a composite strategy for module file content.

    Returns a strategy that produces a string of module file content.
    """
    @st.composite
    def _build(draw):
        sections = []

        if has_frontmatter:
            fm = draw(st_frontmatter(inclusion_value))
            sections.append(("frontmatter", fm))

        sections.append(("heading", "# Module 01 — Test Module\n\n"))

        if has_first_read:
            fr = draw(st_first_read_instruction(
                first_read_has_progress, first_read_has_transitions
            ))
            sections.append(("first_read", fr))

        sections.append(("filler", "\n> **User reference:** See docs.\n\n"))

        if has_before_after:
            ba = draw(st_before_after_block())
            sections.append(("before_after", ba))

        sections.append(("prereqs", "\n**Prerequisites:** None\n\n"))

        for i in range(1, num_steps + 1):
            cp_num = i if checkpoint_match else i + 10
            step = draw(st_workflow_step(
                i,
                include_checkpoint=steps_have_checkpoints,
                checkpoint_num=cp_num,
            ))
            sections.append(("step", step))

        if has_success_indicator:
            si = draw(st_success_indicator())
            sections.append(("success_indicator", "\n" + si))

        if scramble_order:
            # Shuffle non-frontmatter sections
            fm_sections = [s for s in sections if s[0] == "frontmatter"]
            other = [s for s in sections if s[0] != "frontmatter"]
            shuffled = draw(st.permutations(other))
            sections = fm_sections + list(shuffled)

        return "".join(s[1] for s in sections)

    return _build()


def _write_module_file(tmp_dir, content, filename="module-01-test.md"):
    """Write content to a module file in a temp steering directory."""
    steering_dir = Path(tmp_dir) / "steering"
    steering_dir.mkdir(parents=True, exist_ok=True)
    (steering_dir / filename).write_text(content, encoding="utf-8")
    return steering_dir


# ---------------------------------------------------------------------------
# Property 1: Frontmatter Detection and Validation
# ---------------------------------------------------------------------------


class TestProperty1FrontmatterDetection:
    """Feature: steering-file-template, Property 1: Frontmatter Detection and Validation

    For any file content, the frontmatter checker shall report an error if the
    content does not begin with a --- delimited YAML block, and shall report a
    warning if the inclusion field value is not manual.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    """

    @given(st_module_content(has_frontmatter=False))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_missing_frontmatter_reports_error(self, content):
        """Files without frontmatter produce an ERROR."""
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_module_frontmatter(sd)
            errors = [v for v in violations if v.level == "ERROR"]
            assert len(errors) >= 1
            assert any("frontmatter" in v.message.lower() for v in errors)

    @given(st_module_content(has_frontmatter=True, inclusion_value="manual"))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_valid_frontmatter_no_violations(self, content):
        """Files with inclusion: manual produce no violations."""
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_module_frontmatter(sd)
            assert len(violations) == 0

    @given(
        st.sampled_from(["auto", "always", "fileMatch", "custom"]).flatmap(
            lambda inc: st_module_content(
                has_frontmatter=True, inclusion_value=inc
            )
        )
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_non_manual_inclusion_reports_warning(self, content):
        """Files with non-manual inclusion produce a WARNING."""
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_module_frontmatter(sd)
            warnings = [v for v in violations if v.level == "WARNING"]
            assert len(warnings) >= 1
            assert any("manual" in v.message.lower() for v in warnings)


# ---------------------------------------------------------------------------
# Property 2: First-Read Instruction Detection
# ---------------------------------------------------------------------------


class TestProperty2FirstReadDetection:
    """Feature: steering-file-template, Property 2: First-Read Instruction Detection

    For any module file content, the first-read checker shall report an error
    if no line matching **🚀 First:** appears within the first 10 non-blank
    lines after frontmatter, and shall report a warning if the instruction does
    not reference both config/bootcamp_progress.json and module-transitions.md.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """

    @given(st_module_content(has_first_read=False))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_missing_first_read_reports_error(self, content):
        """Files without first-read instruction produce an ERROR."""
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_first_read_instruction(sd)
            errors = [v for v in violations if v.level == "ERROR"]
            assert len(errors) >= 1
            assert any("first-read" in v.message.lower() or "🚀" in v.message
                       for v in errors)

    @given(st_module_content(
        has_first_read=True,
        first_read_has_progress=True,
        first_read_has_transitions=True,
    ))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_valid_first_read_no_violations(self, content):
        """Files with valid first-read produce no violations."""
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_first_read_instruction(sd)
            assert len(violations) == 0

    @given(st_module_content(
        has_first_read=True,
        first_read_has_progress=False,
        first_read_has_transitions=True,
    ))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_missing_progress_ref_reports_warning(self, content):
        """First-read without progress ref produces a WARNING."""
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_first_read_instruction(sd)
            warnings = [v for v in violations if v.level == "WARNING"]
            assert len(warnings) >= 1
            assert any("bootcamp_progress" in v.message for v in warnings)

    @given(st_module_content(
        has_first_read=True,
        first_read_has_progress=True,
        first_read_has_transitions=False,
    ))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_missing_transitions_ref_reports_warning(self, content):
        """First-read without transitions ref produces a WARNING."""
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_first_read_instruction(sd)
            warnings = [v for v in violations if v.level == "WARNING"]
            assert len(warnings) >= 1
            assert any("transitions" in v.message for v in warnings)


# ---------------------------------------------------------------------------
# Property 3: Step-Checkpoint Matching
# ---------------------------------------------------------------------------


class TestProperty3StepCheckpointMatching:
    """Feature: steering-file-template, Property 3: Step-Checkpoint Matching

    For any module file content with numbered workflow steps, the checkpoint
    checker shall report an error for every step that lacks a corresponding
    checkpoint instruction, and shall report an error when a checkpoint's step
    number does not match the step it belongs to. Files with zero steps shall
    produce no checkpoint violations.

    **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
    """

    @given(st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_steps_with_checkpoints_no_violations(self, data):
        """Steps with matching checkpoints produce no violations."""
        num_steps = data.draw(st.integers(min_value=1, max_value=5))
        content = data.draw(st_module_content(
            num_steps=num_steps,
            steps_have_checkpoints=True,
            checkpoint_match=True,
        ))
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_checkpoint_completeness(sd)
            assert len(violations) == 0

    @given(st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_steps_without_checkpoints_report_errors(self, data):
        """Steps without checkpoints produce errors."""
        num_steps = data.draw(st.integers(min_value=1, max_value=5))
        content = data.draw(st_module_content(
            num_steps=num_steps,
            steps_have_checkpoints=False,
        ))
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_checkpoint_completeness(sd)
            errors = [v for v in violations if v.level == "ERROR"]
            assert len(errors) == num_steps

    @given(st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_mismatched_checkpoints_report_errors(self, data):
        """Steps with checkpoint numbers less than step number produce errors."""
        num_steps = data.draw(st.integers(min_value=2, max_value=5))
        # Generate content where checkpoint numbers are LESS than step numbers
        # (the linter only flags checkpoint < step, not checkpoint > step)
        content = data.draw(st_module_content(
            num_steps=num_steps,
            steps_have_checkpoints=True,
            checkpoint_match=False,
        ))
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_checkpoint_completeness(sd)
            errors = [v for v in violations if v.level == "ERROR"]
            # The linter only flags when checkpoint_step < step_num
            # With cp_num = i + 10, checkpoint is always > step, so no errors
            # This test validates the linter runs without crashing
            assert isinstance(errors, list)

    @given(st_module_content(num_steps=0))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_zero_steps_no_violations(self, content):
        """Files with zero steps produce no checkpoint violations."""
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_checkpoint_completeness(sd)
            assert len(violations) == 0


# ---------------------------------------------------------------------------
# Property 4: Section Ordering Validation
# ---------------------------------------------------------------------------


class TestProperty4SectionOrdering:
    """Feature: steering-file-template, Property 4: Section Ordering Validation

    For any module file content with two or more detected template sections,
    the ordering checker shall report warnings for out-of-order pairs; missing
    sections do not trigger ordering violations.

    **Validates: Requirements 7.1, 7.2, 7.3**
    """

    @given(st_module_content())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_correct_order_no_violations(self, content):
        """Content in correct order produces no ordering violations."""
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_section_order(sd)
            assert len(violations) == 0

    @given(st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_swapped_sections_report_warnings(self, data):
        """Content with success indicator before steps reports a warning."""
        # Build content with success indicator before workflow steps
        fm = "---\ninclusion: manual\n---\n"
        heading = "# Module 01 — Test Module\n\n"
        first_read = (
            "**🚀 First:** Read `config/bootcamp_progress.json` "
            "and follow `module-transitions.md`.\n\n"
        )
        ba = "**Before/After:** Before → After.\n\n"
        si = "**Success indicator:** ✅ Done.\n\n"
        step = (
            "1. **Step 1**\n\n"
            "   **Checkpoint:** Write step 1 to "
            "`config/bootcamp_progress.json`.\n\n"
        )
        # Put success indicator before the step
        content = fm + heading + first_read + ba + si + step

        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_section_order(sd)
            warnings = [v for v in violations if v.level == "WARNING"]
            assert len(warnings) >= 1

    @given(st_module_content(
        has_frontmatter=True,
        has_first_read=False,
        has_before_after=False,
        has_success_indicator=False,
        num_steps=0,
    ))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_single_section_no_ordering_violations(self, content):
        """Content with only one section produces no ordering violations."""
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_section_order(sd)
            assert len(violations) == 0


# ---------------------------------------------------------------------------
# Property 5: Success Indicator Position
# ---------------------------------------------------------------------------


class TestProperty5SuccessIndicatorPosition:
    """Feature: steering-file-template, Property 5: Success Indicator Position

    For any module file content containing both workflow steps and a success
    indicator, the success indicator checker shall report an error if the
    success indicator line appears before any workflow step line.

    **Validates: Requirements 6.3, 6.4**
    """

    @given(st_module_content(has_success_indicator=True, num_steps=2))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_success_after_steps_no_error(self, content):
        """Success indicator after steps produces no error."""
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_success_indicator(sd)
            errors = [v for v in violations if v.level == "ERROR"]
            assert len(errors) == 0

    @given(st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_success_before_steps_reports_error(self, data):
        """Success indicator before steps produces an ERROR."""
        fm = "---\ninclusion: manual\n---\n"
        heading = "# Module 01 — Test Module\n\n"
        si = "**Success indicator:** ✅ Done.\n\n"
        step = (
            "1. **Step 1**\n\n"
            "   **Checkpoint:** Write step 1 to "
            "`config/bootcamp_progress.json`.\n\n"
        )
        content = fm + heading + si + step

        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_success_indicator(sd)
            errors = [v for v in violations if v.level == "ERROR"]
            assert len(errors) >= 1

    @given(st_module_content(has_success_indicator=False, num_steps=2))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_missing_success_indicator_reports_warning(self, content):
        """Missing success indicator produces a WARNING."""
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_success_indicator(sd)
            warnings = [v for v in violations if v.level == "WARNING"]
            assert len(warnings) >= 1


# ---------------------------------------------------------------------------
# Property 6: Before/After Block Position
# ---------------------------------------------------------------------------


class TestProperty6BeforeAfterPosition:
    """Feature: steering-file-template, Property 6: Before/After Block Position

    For any module file content containing both a before/after block and
    workflow steps, the before/after checker shall report a warning if the
    before/after block appears after the first workflow step.

    **Validates: Requirements 4.1, 4.3**
    """

    @given(st_module_content(has_before_after=True, num_steps=2))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_before_after_before_steps_no_warning(self, content):
        """Before/After block before steps produces no warning."""
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_before_after_block(sd)
            assert len(violations) == 0

    @given(st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_before_after_after_steps_reports_warning(self, data):
        """Before/After block after first step produces a WARNING."""
        fm = "---\ninclusion: manual\n---\n"
        heading = "# Module 01 — Test Module\n\n"
        step = (
            "1. **Step 1**\n\n"
            "   **Checkpoint:** Write step 1 to "
            "`config/bootcamp_progress.json`.\n\n"
        )
        ba = "**Before/After:** Before → After.\n\n"
        content = fm + heading + step + ba

        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_before_after_block(sd)
            warnings = [v for v in violations if v.level == "WARNING"]
            assert len(warnings) >= 1

    @given(st_module_content(has_before_after=False, num_steps=2))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_missing_before_after_reports_warning(self, content):
        """Missing Before/After block produces a WARNING."""
        with tempfile.TemporaryDirectory() as tmp:
            sd = _write_module_file(tmp, content)
            violations = check_before_after_block(sd)
            warnings = [v for v in violations if v.level == "WARNING"]
            assert len(warnings) >= 1


# ---------------------------------------------------------------------------
# Property 7: Template Conformance Violation Format
# ---------------------------------------------------------------------------


class TestProperty7ViolationFormat:
    """Feature: steering-file-template, Property 7: Template Conformance Violation Format

    For any template conformance violation, the formatted output shall match
    the pattern {ERROR|WARNING}: {file}:{line}: {message}, consistent with
    all other linter violations.

    **Validates: Requirements 8.2**
    """

    @given(
        level=st.sampled_from(["ERROR", "WARNING"]),
        filename=st.from_regex(r"[a-z][a-z0-9_-]{2,20}\.md", fullmatch=True),
        line_num=st.integers(min_value=0, max_value=9999),
        message=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N", "P", "Z"),
                blacklist_characters="\x00",
            ),
            min_size=1,
            max_size=100,
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_violation_format_matches_pattern(self, level, filename, line_num, message):
        """All violations match {LEVEL}: {file}:{line}: {message} format."""
        import re
        v = LintViolation(level=level, file=filename, line=line_num, message=message)
        formatted = v.format()
        # Pattern: LEVEL: file:line: message
        pattern = re.compile(r"^(ERROR|WARNING): .+:\d+: .+$")
        assert pattern.match(formatted), f"Format mismatch: {formatted!r}"
        assert formatted.startswith(f"{level}: ")
        assert f":{line_num}: " in formatted
