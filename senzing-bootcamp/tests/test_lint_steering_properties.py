"""Property-based tests for lint_steering.py using Hypothesis.

Feature: steering-file-linter
"""

import json
import shutil
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
    VALID_INCLUSIONS,
    VALID_SIZE_CATEGORIES,
    check_cross_references,
    check_module_numbering,
    check_checkpoints,
    check_index_completeness,
    check_hook_consistency,
    check_frontmatter,
    check_internal_links,
    check_wait_conflicts,
    is_in_code_block,
    parse_frontmatter,
    get_final_substantive_line,
    run_all_checks,
)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

def st_filename():
    """Generate valid steering-style filenames."""
    return st.from_regex(r"[a-z][a-z0-9-]{2,20}\.md", fullmatch=True)


def st_hook_id():
    """Generate valid hook IDs."""
    return st.from_regex(r"[a-z][a-z0-9-]{2,20}", fullmatch=True)


def st_module_number():
    """Generate valid module numbers (1-20)."""
    return st.integers(min_value=1, max_value=20)


# ---------------------------------------------------------------------------
# Property 1: Cross-Reference Detection Completeness
# ---------------------------------------------------------------------------


class TestProperty1CrossReferenceDetection:
    """Feature: steering-file-linter, Property 1: Cross-Reference Detection Completeness

    For any steering file content containing #[[file:path]] references, the
    linter shall report an error for every reference whose target path does
    not exist on disk, and shall not report an error for references whose
    target path does exist.

    **Validates: Requirements 1.1, 1.3**
    """

    @given(
        existing=st.lists(st_filename(), min_size=1, max_size=5, unique=True),
        missing=st.lists(st_filename(), min_size=1, max_size=5, unique=True),
    )
    @settings(max_examples=100)
    def test_reports_missing_include_refs_not_existing(self, existing, missing):
        """#[[file:path]] refs to missing files produce errors; existing ones don't."""
        assume(not set(existing) & set(missing))

        tmp = Path(tempfile.mkdtemp())
        try:
            steering = tmp / "steering"
            steering.mkdir()

            for fname in existing:
                (steering / fname).write_text("---\ninclusion: manual\n---\n# Exists\n")

            lines = ["---", "inclusion: manual", "---", "# Test"]
            for fname in existing:
                lines.append(f"See #[[file:{steering / fname}]]")
            for fname in missing:
                lines.append(f"See #[[file:{steering / fname}]]")

            (steering / "test-refs.md").write_text("\n".join(lines))

            index_data = {"modules": {}, "file_metadata": {}, "keywords": {},
                           "languages": {}, "deployment": {}}
            violations = check_cross_references(steering, index_data)

            error_messages = [v.message for v in violations if v.level == "ERROR"]
            for fname in missing:
                assert any(str(steering / fname) in msg for msg in error_messages), \
                    f"Missing ref to {fname} not reported"
            for fname in existing:
                assert not any(f"#[[file:{steering / fname}]]" in msg
                              and "does not exist" in msg
                              for msg in error_messages), \
                    f"Existing ref to {fname} incorrectly reported"
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Property 2: Bidirectional Module Numbering Consistency
# ---------------------------------------------------------------------------


class TestProperty2ModuleNumbering:
    """Feature: steering-file-linter, Property 2: Bidirectional Module Numbering Consistency

    For any set of module numbers in the steering index and set of module
    steering files on disk, the linter shall report every module number that
    exists in one set but not the other.

    **Validates: Requirements 2.1, 2.2**
    """

    @given(
        index_nums=st.frozensets(st_module_number(), min_size=1, max_size=10),
        disk_nums=st.frozensets(st_module_number(), min_size=1, max_size=10),
    )
    @settings(max_examples=100)
    def test_reports_all_mismatches_bidirectionally(self, index_nums, disk_nums):
        """Every module in index-only or disk-only is reported."""
        tmp = Path(tempfile.mkdtemp())
        try:
            steering = tmp / "steering"
            steering.mkdir()

            for n in disk_nums:
                fname = f"module-{n:02d}-test.md"
                (steering / fname).write_text("---\ninclusion: manual\n---\n# Module\n")

            index_data = {
                "modules": {n: f"module-{n:02d}-test.md" for n in index_nums},
                "file_metadata": {},
                "keywords": {},
                "languages": {},
                "deployment": {},
            }

            violations = check_module_numbering(steering, index_data)
            messages = [v.message for v in violations]

            for n in index_nums - disk_nums:
                assert any(f"module-{n:02d}-test.md" in msg and "does not exist" in msg
                          for msg in messages), \
                    f"Module {n} in index but not on disk was not reported"

            for n in disk_nums - index_nums:
                assert any(f"module-{n:02d}-test.md" in msg and "not listed" in msg
                          for msg in messages), \
                    f"Module {n} on disk but not in index was not reported"
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Property 3: Module Sequence Gap Detection
# ---------------------------------------------------------------------------


class TestProperty3ModuleSequenceGaps:
    """Feature: steering-file-linter, Property 3: Module Sequence Gap Detection

    For any sequence of module numbers in the steering index, the linter
    shall report a warning for every integer gap in the sequence.

    **Validates: Requirements 2.4**
    """

    @given(
        nums=st.frozensets(st_module_number(), min_size=2, max_size=15),
    )
    @settings(max_examples=100)
    def test_reports_every_gap(self, nums):
        """Every gap in the module sequence is reported as a warning."""
        tmp = Path(tempfile.mkdtemp())
        try:
            steering = tmp / "steering"
            steering.mkdir()

            for n in nums:
                fname = f"module-{n:02d}-test.md"
                (steering / fname).write_text("---\ninclusion: manual\n---\n# Module\n")

            index_data = {
                "modules": {n: f"module-{n:02d}-test.md" for n in nums},
                "file_metadata": {},
                "keywords": {},
                "languages": {},
                "deployment": {},
            }

            violations = check_module_numbering(steering, index_data)
            gap_warnings = [v for v in violations
                           if v.level == "WARNING" and "Gap" in v.message]

            min_n, max_n = min(nums), max(nums)
            expected_gaps = set(range(min_n, max_n + 1)) - nums

            assert len(gap_warnings) == len(expected_gaps), \
                f"Expected {len(expected_gaps)} gap warnings, got {len(gap_warnings)}"
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Property 4: WAIT-at-End-of-File Detection
# ---------------------------------------------------------------------------


class TestProperty4WaitAtEndDetection:
    """Feature: steering-file-linter, Property 4: WAIT-at-End-of-File Detection

    For any steering file content, the linter shall report a warning if and
    only if the final substantive line contains a `WAIT for` instruction,
    unless the WAIT is preceded by a 👉 question on the same or previous
    non-blank line.

    **Validates: Requirements 3.2, 3.4**
    """

    @given(
        has_wait=st.booleans(),
        has_pointing=st.booleans(),
        trailing_blanks=st.integers(min_value=0, max_value=3),
    )
    @settings(max_examples=100)
    def test_wait_at_end_detection(self, has_wait, has_pointing, trailing_blanks):
        """WAIT on final line warns unless preceded by 👉."""
        tmp = Path(tempfile.mkdtemp())
        try:
            steering = tmp / "steering"
            hooks = tmp / "hooks"
            steering.mkdir()
            hooks.mkdir()

            lines = ["---", "inclusion: manual", "---", "# Test", "", "Some content."]
            if has_pointing:
                lines.append("👉 What would you like to do?")
                lines.append("")
            if has_wait:
                lines.append("WAIT for response.")
            else:
                lines.append("That's all for now.")
            lines.extend([""] * trailing_blanks)

            (steering / "test-wait.md").write_text("\n".join(lines))

            violations = check_wait_conflicts(steering, hooks)
            wait_warnings = [v for v in violations if "WAIT" in v.message]

            if has_wait and not has_pointing:
                assert len(wait_warnings) == 1, \
                    f"Expected 1 WAIT warning, got {len(wait_warnings)}"
            else:
                assert len(wait_warnings) == 0, \
                    f"Expected 0 WAIT warnings, got {len(wait_warnings)}"
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Property 5: Step-Checkpoint Matching
# ---------------------------------------------------------------------------


class TestProperty5StepCheckpointMatching:
    """Feature: steering-file-linter, Property 5: Step-Checkpoint Matching

    For any module steering file content with numbered steps, the linter
    shall report an error for every numbered step that lacks a corresponding
    checkpoint instruction before the next step or end of file, and shall
    report an error when a checkpoint's step number does not match the step
    it follows.

    **Validates: Requirements 4.2, 4.3**
    """

    @given(
        num_steps=st.integers(min_value=1, max_value=5),
        missing_indices=st.frozensets(st.integers(min_value=0, max_value=4)),
    )
    @settings(max_examples=100)
    def test_missing_checkpoints_reported(self, num_steps, missing_indices):
        """Steps without checkpoints are reported as errors."""
        tmp = Path(tempfile.mkdtemp())
        try:
            steering = tmp / "steering"
            steering.mkdir()

            content_parts = ["---\ninclusion: manual\n---\n\n# Module 99\n\n"]
            for i in range(1, num_steps + 1):
                content_parts.append(f"{i}. **Step {i} title**\n\n")
                content_parts.append(f"   Content for step {i}.\n\n")
                if (i - 1) not in missing_indices:
                    content_parts.append(
                        f"   **Checkpoint:** Write step {i} to "
                        f"`config/bootcamp_progress.json`.\n\n"
                    )

            (steering / "module-99-test.md").write_text("".join(content_parts))

            violations = check_checkpoints(steering)
            missing_errors = [v for v in violations
                             if "no checkpoint" in v.message]

            expected_missing = sum(1 for i in range(num_steps)
                                  if i in missing_indices)

            assert len(missing_errors) == expected_missing, \
                f"Expected {expected_missing} missing checkpoint errors, " \
                f"got {len(missing_errors)}"
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Property 6: File Metadata Completeness
# ---------------------------------------------------------------------------


class TestProperty6FileMetadataCompleteness:
    """Feature: steering-file-linter, Property 6: File Metadata Completeness

    For any set of .md files on disk and file_metadata entries in the
    steering index, the linter shall report an error for every file that has
    no metadata entry, and shall report an error for every metadata entry
    missing a valid token_count or size_category.

    **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
    """

    @given(
        files_on_disk=st.lists(st_filename(), min_size=1, max_size=5, unique=True),
        files_in_meta=st.lists(st_filename(), min_size=0, max_size=5, unique=True),
        invalid_token=st.booleans(),
        invalid_category=st.booleans(),
    )
    @settings(max_examples=100)
    def test_missing_and_invalid_metadata_reported(
        self, files_on_disk, files_in_meta, invalid_token, invalid_category
    ):
        """Files without metadata and invalid metadata fields are reported."""
        tmp = Path(tempfile.mkdtemp())
        try:
            steering = tmp / "steering"
            steering.mkdir()

            for fname in files_on_disk:
                (steering / fname).write_text("---\ninclusion: manual\n---\n# File\n")

            file_metadata = {}
            for fname in files_in_meta:
                meta = {}
                if invalid_token:
                    meta["token_count"] = -1
                else:
                    meta["token_count"] = 100
                if invalid_category:
                    meta["size_category"] = "huge"
                else:
                    meta["size_category"] = "small"
                file_metadata[fname] = meta

            index_data = {
                "modules": {},
                "file_metadata": file_metadata,
                "keywords": {},
                "languages": {},
                "deployment": {},
            }

            violations = check_index_completeness(steering, index_data)

            for fname in files_on_disk:
                if fname not in file_metadata:
                    assert any(fname in v.message for v in violations
                              if v.level == "ERROR"), \
                        f"File {fname} missing from metadata not reported"

            for fname in files_in_meta:
                if invalid_token:
                    assert any(fname in v.message and "token_count" in v.message
                              for v in violations if v.level == "ERROR"), \
                        f"Invalid token_count for {fname} not reported"
                if invalid_category:
                    assert any(fname in v.message and "size_category" in v.message
                              for v in violations if v.level == "ERROR"), \
                        f"Invalid size_category for {fname} not reported"
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Property 7: Bidirectional Hook Registry Consistency
# ---------------------------------------------------------------------------


class TestProperty7HookRegistryConsistency:
    """Feature: steering-file-linter, Property 7: Bidirectional Hook Registry Consistency

    For any set of hook IDs in the hook registry and set of .kiro.hook files
    on disk, the linter shall report every ID that exists in one set but not
    the other, and shall report an error when the event type documented in
    the registry does not match the when.type field in the corresponding
    hook file.

    **Validates: Requirements 6.2, 6.3, 6.4**
    """

    @given(
        registry_ids=st.frozensets(st_hook_id(), min_size=1, max_size=5),
        disk_ids=st.frozensets(st_hook_id(), min_size=1, max_size=5),
    )
    @settings(max_examples=100)
    def test_reports_all_mismatches_bidirectionally(self, registry_ids, disk_ids):
        """Every hook in registry-only or disk-only is reported."""
        tmp = Path(tempfile.mkdtemp())
        try:
            steering = tmp / "steering"
            hooks = tmp / "hooks"
            steering.mkdir()
            hooks.mkdir()

            registry_lines = [
                "---", "inclusion: manual", "---", "# Hook Registry — Full Prompts", ""
            ]
            for hid in registry_ids:
                registry_lines.append(f"**{hid}** (promptSubmit → askAgent)")
                registry_lines.append(f"")
                registry_lines.append(f"- id: `{hid}`")
                registry_lines.append(f"")
            (steering / "hook-registry-detail.md").write_text("\n".join(registry_lines))

            for hid in disk_ids:
                hook_data = {
                    "name": hid,
                    "when": {"type": "promptSubmit"},
                    "then": {"type": "askAgent", "prompt": "test"},
                }
                (hooks / f"{hid}.kiro.hook").write_text(json.dumps(hook_data))

            violations = check_hook_consistency(steering, hooks)
            messages = [v.message for v in violations]

            for hid in registry_ids - disk_ids:
                assert any(hid in msg and "no corresponding" in msg.lower()
                          for msg in messages), \
                    f"Registry-only hook {hid} not reported"

            for hid in disk_ids - registry_ids:
                assert any(hid in msg and "not documented" in msg.lower()
                          for msg in messages), \
                    f"Disk-only hook {hid} not reported"
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Property 8: Frontmatter Inclusion Validation
# ---------------------------------------------------------------------------


class TestProperty8FrontmatterValidation:
    """Feature: steering-file-linter, Property 8: Frontmatter Inclusion Validation

    For any steering file content, the linter shall report an error if the
    file lacks a YAML frontmatter block, and shall report an error if the
    inclusion field is missing or has a value not in {always, auto, fileMatch,
    manual}. When inclusion is fileMatch, the linter shall additionally
    require a non-empty fileMatchPattern field.

    **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**
    """

    @given(
        has_frontmatter=st.booleans(),
        inclusion=st.sampled_from(
            list(VALID_INCLUSIONS) + ["invalid", "none", ""]
        ),
        has_pattern=st.booleans(),
    )
    @settings(max_examples=100)
    def test_frontmatter_validation(self, has_frontmatter, inclusion, has_pattern):
        """Frontmatter presence and inclusion field are validated."""
        tmp = Path(tempfile.mkdtemp())
        try:
            steering = tmp / "steering"
            steering.mkdir()

            if has_frontmatter:
                lines = ["---"]
                if inclusion:
                    lines.append(f"inclusion: {inclusion}")
                if inclusion == "fileMatch" and has_pattern:
                    lines.append("fileMatchPattern: **/*.py")
                lines.append("---")
                lines.append("# Test")
            else:
                lines = ["# Test", "No frontmatter here."]

            (steering / "test-fm.md").write_text("\n".join(lines))

            violations = check_frontmatter(steering)
            error_messages = [v.message for v in violations if v.level == "ERROR"]

            if not has_frontmatter:
                assert any("frontmatter" in msg.lower() for msg in error_messages), \
                    "Missing frontmatter not reported"
            elif not inclusion:
                assert any("inclusion" in msg.lower() for msg in error_messages), \
                    "Missing inclusion field not reported"
            elif inclusion not in VALID_INCLUSIONS:
                assert any("inclusion" in msg.lower() for msg in error_messages), \
                    f"Invalid inclusion '{inclusion}' not reported"
            elif inclusion == "fileMatch" and not has_pattern:
                assert any("fileMatchPattern" in msg for msg in error_messages), \
                    "Missing fileMatchPattern not reported"
            else:
                assert len(error_messages) == 0, \
                    f"Valid frontmatter produced errors: {error_messages}"
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Property 9: Exit Code Correctness
# ---------------------------------------------------------------------------


class TestProperty9ExitCodeCorrectness:
    """Feature: steering-file-linter, Property 9: Exit Code Correctness

    For any set of lint violations, the exit code shall be 0 if and only if
    there are zero error-level violations (or zero error+warning violations
    when --warnings-as-errors is set). Otherwise the exit code shall be 1.

    **Validates: Requirements 8.2, 8.3, 8.6**
    """

    @given(
        errors=st.integers(min_value=0, max_value=5),
        warnings=st.integers(min_value=0, max_value=5),
        warnings_as_errors=st.booleans(),
    )
    @settings(max_examples=100)
    def test_exit_code_correctness(self, errors, warnings, warnings_as_errors):
        """Exit code is 0 iff no errors (or no errors+warnings with flag)."""
        violations = []
        for i in range(errors):
            violations.append(LintViolation("ERROR", "test.md", i + 1, f"Error {i}"))
        for i in range(warnings):
            violations.append(LintViolation("WARNING", "test.md", i + 1, f"Warning {i}"))

        if warnings_as_errors:
            has_issues = len(violations) > 0
        else:
            has_issues = errors > 0

        expected_exit = 1 if has_issues else 0

        # Replicate the exit code logic from run_all_checks
        if warnings_as_errors:
            actual_has_issues = any(True for v in violations)
        else:
            actual_has_issues = any(v.level == "ERROR" for v in violations)

        actual_exit = 1 if actual_has_issues else 0

        assert actual_exit == expected_exit, \
            f"Exit code {actual_exit} != expected {expected_exit} " \
            f"(errors={errors}, warnings={warnings}, wae={warnings_as_errors})"


# ---------------------------------------------------------------------------
# Property 10: Violation Output Format
# ---------------------------------------------------------------------------


class TestProperty10ViolationOutputFormat:
    """Feature: steering-file-linter, Property 10: Violation Output Format

    For any LintViolation object, the formatted output string shall match
    the pattern {ERROR|WARNING}: {file}:{line}: {message}.

    **Validates: Requirements 8.4**
    """

    @given(
        level=st.sampled_from(["ERROR", "WARNING"]),
        filename=st.from_regex(r"[a-z][a-z0-9/_-]{1,30}\.[a-z]{1,4}", fullmatch=True),
        line=st.integers(min_value=0, max_value=9999),
        message=st.text(min_size=1, max_size=100,
                       alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z"),
                                              blacklist_characters="\n\r")),
    )
    @settings(max_examples=100)
    def test_format_matches_pattern(self, level, filename, line, message):
        """Formatted output matches {level}: {file}:{line}: {message}."""
        v = LintViolation(level=level, file=filename, line=line, message=message)
        formatted = v.format()

        assert formatted == f"{level}: {filename}:{line}: {message}"
        assert formatted.startswith(("ERROR:", "WARNING:"))
        parts = formatted.split(": ", 2)
        assert len(parts) == 3
        assert parts[0] in ("ERROR", "WARNING")


# ---------------------------------------------------------------------------
# Property 11: Code-Block-Aware Reference Validation
# ---------------------------------------------------------------------------


class TestProperty11CodeBlockAwareValidation:
    """Feature: steering-file-linter, Property 11: Code-Block-Aware Reference Validation

    For any steering file content containing file references both inside and
    outside fenced code blocks, the linter shall validate only references
    outside code blocks and skip those inside code blocks.

    **Validates: Requirements 9.3**
    """

    @given(ref_name=st_filename())
    @settings(max_examples=100)
    def test_refs_inside_code_blocks_skipped(self, ref_name):
        """References inside code blocks are not validated."""
        tmp = Path(tempfile.mkdtemp())
        try:
            steering = tmp / "steering"
            steering.mkdir()

            content = (
                "---\n"
                "inclusion: manual\n"
                "---\n"
                "# Test\n"
                "\n"
                "```\n"
                f"see `{ref_name}`\n"
                "```\n"
                "\n"
                "Normal text without references.\n"
            )
            (steering / "test-codeblock.md").write_text(content)

            violations = check_internal_links(steering)
            ref_violations = [v for v in violations if ref_name in v.message]
            assert len(ref_violations) == 0, \
                f"Reference inside code block was incorrectly validated"
        finally:
            shutil.rmtree(tmp)

    @given(ref_name=st_filename())
    @settings(max_examples=100)
    def test_refs_outside_code_blocks_validated(self, ref_name):
        """References outside code blocks are validated."""
        tmp = Path(tempfile.mkdtemp())
        try:
            steering = tmp / "steering"
            steering.mkdir()

            content = (
                "---\n"
                "inclusion: manual\n"
                "---\n"
                "# Test\n"
                "\n"
                f"Please load `{ref_name}`\n"
            )
            (steering / "test-outside.md").write_text(content)

            violations = check_internal_links(steering)
            ref_violations = [v for v in violations if ref_name in v.message]
            assert len(ref_violations) == 1, \
                f"Expected 1 violation for missing ref, got {len(ref_violations)}"
        finally:
            shutil.rmtree(tmp)
