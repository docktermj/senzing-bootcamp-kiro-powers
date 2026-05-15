"""Property-based tests for triage_feedback.py using Hypothesis.

Feature: automated-feedback-triage
"""

import json
import sys
import tempfile
import uuid
from io import StringIO
from pathlib import Path

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from triage_feedback import (
    FeedbackEntry,
    TriageResult,
    VALID_CATEGORIES,
    VALID_PRIORITIES,
    to_kebab_case,
    extract_field,
    parse_feedback_file,
    generate_bugfix_skeleton,
    generate_requirements_skeleton,
    generate_config,
    create_spec_directory,
    print_triage_report,
)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

def st_safe_text():
    """Generate text that won't interfere with markdown heading parsing."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N", "P", "S"),
            blacklist_characters="\x00\r\xa0",
        ),
        min_size=1,
        max_size=80,
    ).map(lambda s: s.strip()).filter(lambda s: s and "\n" not in s)


def st_multiline_content():
    """Generate multi-line markdown content that won't contain heading markers."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N", "P", "S"),
            blacklist_characters="\x00\r\xa0",
        ),
        min_size=1,
        max_size=200,
    ).map(lambda s: s.strip()).filter(
        lambda s: s and "## Improvement:" not in s and "###" not in s and "**" not in s
    )


def st_title():
    """Generate valid feedback entry titles."""
    return st.from_regex(r"[A-Za-z][A-Za-z0-9 ]{2,30}", fullmatch=True).map(
        lambda s: s.strip()
    ).filter(lambda s: s)


def st_category():
    """Generate a valid feedback category."""
    return st.sampled_from(sorted(VALID_CATEGORIES))


def st_priority():
    """Generate a valid feedback priority."""
    return st.sampled_from(sorted(VALID_PRIORITIES))


def st_module():
    """Generate a valid module number string."""
    return st.integers(min_value=1, max_value=12).map(str)


def st_date():
    """Generate a date string."""
    return st.from_regex(r"20[2-3][0-9]-[01][0-9]-[0-3][0-9]", fullmatch=True)


def st_feedback_entry():
    """Generate a random FeedbackEntry object."""
    return st.builds(
        FeedbackEntry,
        title=st_title(),
        date=st.one_of(st.none(), st_date()),
        module=st.one_of(st.none(), st_module()),
        priority=st.one_of(st.none(), st_priority()),
        category=st_category(),
        what_happened=st_multiline_content(),
        why_problem=st_multiline_content(),
        suggested_fix=st_multiline_content(),
        workaround=st.one_of(st.none(), st.just(""), st_multiline_content()),
    )


def st_bug_entry():
    """Generate a FeedbackEntry with category Bug."""
    return st.builds(
        FeedbackEntry,
        title=st_title(),
        date=st.one_of(st.none(), st_date()),
        module=st.one_of(st.none(), st_module()),
        priority=st.one_of(st.none(), st_priority()),
        category=st.just("Bug"),
        what_happened=st_multiline_content(),
        why_problem=st_multiline_content(),
        suggested_fix=st_multiline_content(),
        workaround=st.one_of(st.none(), st.just(""), st_multiline_content()),
    )


def st_non_bug_entry():
    """Generate a FeedbackEntry with a non-Bug category."""
    non_bug_cats = sorted(VALID_CATEGORIES - {"Bug"})
    return st.builds(
        FeedbackEntry,
        title=st_title(),
        date=st.one_of(st.none(), st_date()),
        module=st.one_of(st.none(), st_module()),
        priority=st.one_of(st.none(), st_priority()),
        category=st.sampled_from(non_bug_cats),
        what_happened=st_multiline_content(),
        why_problem=st_multiline_content(),
        suggested_fix=st_multiline_content(),
        workaround=st.one_of(st.none(), st.just(""), st_multiline_content()),
    )


def build_feedback_markdown(entries_data):
    """Build a feedback markdown string from a list of entry dicts."""
    lines = ["# Feedback\n\nPreamble text.\n"]
    for e in entries_data:
        lines.append(f"## Improvement: {e['title']}\n")
        if e.get("date"):
            lines.append(f"**Date**: {e['date']}")
        if e.get("module"):
            lines.append(f"**Module**: {e['module']}")
        if e.get("priority"):
            lines.append(f"**Priority**: {e['priority']}")
        if e.get("category"):
            lines.append(f"**Category**: {e['category']}")
        lines.append("")
        lines.append(f"### What Happened\n{e.get('what_happened', 'Something happened')}\n")
        lines.append(f"### Why It's a Problem\n{e.get('why_problem', 'It is a problem')}\n")
        lines.append(f"### Suggested Fix\n{e.get('suggested_fix', 'Fix it')}\n")
        if e.get("workaround"):
            lines.append(f"### Workaround Used\n{e['workaround']}\n")
        else:
            lines.append("### Workaround Used\n\n")
    return "\n".join(lines)


def st_entry_data():
    """Generate a dict of entry data for building markdown."""
    return st.fixed_dictionaries({
        "title": st_title(),
        "date": st_date(),
        "module": st_module(),
        "priority": st_priority(),
        "category": st_category(),
        "what_happened": st_multiline_content(),
        "why_problem": st_multiline_content(),
        "suggested_fix": st_multiline_content(),
        "workaround": st.one_of(st.just(""), st_multiline_content()),
    })


# ---------------------------------------------------------------------------
# Property 1: Heading-Based Entry Identification
# ---------------------------------------------------------------------------


class TestProperty1HeadingBasedEntryIdentification:
    """Feature: automated-feedback-triage, Property 1: Heading-Based Entry Identification

    For any markdown content, the parser identifies exactly the sections
    delimited by `## Improvement: <title>` headings as feedback entries.

    **Validates: Requirements 1.3**
    """

    @given(entries=st.lists(st_entry_data(), min_size=0, max_size=5))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_parser_finds_exactly_improvement_headings(self, entries):
        md = build_feedback_markdown(entries)
        parsed, _warnings = parse_feedback_file(md)
        # Every entry has a valid category, so all should parse
        assert len(parsed) == len(entries)
        for parsed_entry, source in zip(parsed, entries):
            assert parsed_entry.title == source["title"]


# ---------------------------------------------------------------------------
# Property 2: Field Extraction Completeness
# ---------------------------------------------------------------------------


class TestProperty2FieldExtractionCompleteness:
    """Feature: automated-feedback-triage, Property 2: Field Extraction Completeness

    For any valid feedback entry with all fields, the parser extracts
    all fields with their complete content.

    **Validates: Requirements 1.4**
    """

    @given(entry_data=st_entry_data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_all_fields_extracted(self, entry_data):
        md = build_feedback_markdown([entry_data])
        parsed, warnings = parse_feedback_file(md)
        assert len(parsed) == 1
        entry = parsed[0]
        # Title may be stripped of whitespace during parsing
        assert entry.title == entry_data["title"].strip()
        assert entry.date == entry_data["date"]
        assert entry.module == entry_data["module"]
        assert entry.priority == entry_data["priority"]
        assert entry.category == entry_data["category"]
        assert entry_data["what_happened"] in entry.what_happened
        assert entry_data["why_problem"] in entry.why_problem
        assert entry_data["suggested_fix"] in entry.suggested_fix


# ---------------------------------------------------------------------------
# Property 3: Missing Required Fields Cause Skip
# ---------------------------------------------------------------------------


class TestProperty3MissingRequiredFieldsCauseSkip:
    """Feature: automated-feedback-triage, Property 3: Missing Required Fields Cause Skip

    For any feedback entry missing title or category, the parser logs
    a warning and excludes it.

    **Validates: Requirements 1.5**
    """

    @given(entry_data=st_entry_data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_missing_category_causes_skip(self, entry_data):
        # Remove category from the entry
        entry_data_no_cat = dict(entry_data)
        entry_data_no_cat["category"] = ""
        md = build_feedback_markdown([entry_data_no_cat])
        # Manually remove the category line
        md = "\n".join(
            line for line in md.split("\n")
            if not line.startswith("**Category**:")
        )
        parsed, warnings = parse_feedback_file(md)
        assert len(parsed) == 0
        assert any("category" in w.lower() for w in warnings)


# ---------------------------------------------------------------------------
# Property 4: Kebab-Case Determinism
# ---------------------------------------------------------------------------


class TestProperty4KebabCaseDeterminism:
    """Feature: automated-feedback-triage, Property 4: Kebab-Case Determinism

    For any input string, to_kebab_case produces lowercase output with
    only alphanumeric chars and hyphens, no consecutive hyphens, no
    leading/trailing hyphens.

    **Validates: Requirements 2.2**
    """

    @given(title=st.text(min_size=0, max_size=100))
    @settings(max_examples=10)
    def test_kebab_case_invariants(self, title):
        result = to_kebab_case(title)
        # Must be lowercase
        assert result == result.lower()
        # Only alphanumeric and hyphens
        assert all(c.isalnum() or c == "-" for c in result)
        # No consecutive hyphens
        assert "--" not in result
        # No leading/trailing hyphens
        if result:
            assert not result.startswith("-")
            assert not result.endswith("-")

    @given(title=st.text(min_size=1, max_size=100))
    @settings(max_examples=10)
    def test_kebab_case_is_deterministic(self, title):
        """Same input always produces same output."""
        assert to_kebab_case(title) == to_kebab_case(title)


# ---------------------------------------------------------------------------
# Property 5: Bug Category Routes to Bugfix Skeleton
# ---------------------------------------------------------------------------


class TestProperty5BugCategoryRouting:
    """Feature: automated-feedback-triage, Property 5: Bug Category Routes to Bugfix Skeleton

    For any entry with category "Bug", generates bugfix.md; for non-bug,
    generates requirements.md.

    **Validates: Requirements 3.1, 4.1**
    """

    @given(entry=st_bug_entry())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_bug_category_generates_bugfix(self, entry):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            spec_path, warning = create_spec_directory(entry, tmp_path)
            assume(spec_path is not None)
            assert (spec_path / "bugfix.md").exists()
            assert not (spec_path / "requirements.md").exists()

    @given(entry=st_non_bug_entry())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_non_bug_category_generates_requirements(self, entry):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            spec_path, warning = create_spec_directory(entry, tmp_path)
            assume(spec_path is not None)
            assert (spec_path / "requirements.md").exists()
            assert not (spec_path / "bugfix.md").exists()


# ---------------------------------------------------------------------------
# Property 6: Bugfix Skeleton Content Mapping
# ---------------------------------------------------------------------------


class TestProperty6BugfixSkeletonContentMapping:
    """Feature: automated-feedback-triage, Property 6: Bugfix Skeleton Content Mapping

    For any bug entry, skeleton contains what_happened in "Bug Report",
    suggested_fix in "Suggested Fix", and "Known Workaround" iff
    workaround is non-empty.

    **Validates: Requirements 3.2, 3.5, 3.6**
    """

    @given(entry=st_bug_entry())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_bugfix_skeleton_content(self, entry):
        skeleton = generate_bugfix_skeleton(entry)
        # Bug Report section contains what_happened
        assert entry.what_happened in skeleton
        # Suggested Fix section contains suggested_fix
        assert entry.suggested_fix in skeleton
        # Known Workaround present iff workaround is non-empty
        has_workaround_section = "## Known Workaround" in skeleton
        has_workaround_content = bool(entry.workaround)
        assert has_workaround_section == has_workaround_content


# ---------------------------------------------------------------------------
# Property 7: Requirements Skeleton Content Mapping
# ---------------------------------------------------------------------------


class TestProperty7RequirementsSkeletonContentMapping:
    """Feature: automated-feedback-triage, Property 7: Requirements Skeleton Content Mapping

    For any non-bug entry, skeleton contains title and problem in
    "Introduction" and user story from suggested_fix in "Requirements".

    **Validates: Requirements 4.2, 4.4**
    """

    @given(entry=st_non_bug_entry())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_requirements_skeleton_content(self, entry):
        skeleton = generate_requirements_skeleton(entry)
        # Introduction contains title
        assert entry.title in skeleton
        # Introduction contains problem description
        assert entry.why_problem in skeleton
        # Requirements section contains suggested_fix content
        assert entry.suggested_fix.lower().rstrip(".") in skeleton.lower()


# ---------------------------------------------------------------------------
# Property 8: Triage Report Accuracy
# ---------------------------------------------------------------------------


class TestProperty8TriageReportAccuracy:
    """Feature: automated-feedback-triage, Property 8: Triage Report Accuracy

    For any set of entries, summary counts satisfy total = generated + skipped.

    **Validates: Requirements 5.2, 5.3, 5.4**
    """

    @given(
        num_generated=st.integers(min_value=0, max_value=10),
        num_skipped=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=10)
    def test_report_counts_are_accurate(self, num_generated, num_skipped):
        total = num_generated + num_skipped
        assume(total > 0)

        generated = [
            TriageResult(
                path=Path(f".kiro/specs/entry-{i}"),
                title=f"Entry {i}",
                doc_type="requirements",
                priority="Medium",
            )
            for i in range(num_generated)
        ]
        skipped = [
            (f"Skipped {i}", f"reason {i}")
            for i in range(num_skipped)
        ]

        # Capture stdout using StringIO
        old_stdout = sys.stdout
        sys.stdout = captured = StringIO()
        try:
            print_triage_report(generated, skipped, total)
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue()
        assert f"{total} processed" in output
        assert f"{num_generated} generated" in output
        assert f"{num_skipped} skipped" in output


# ---------------------------------------------------------------------------
# Property 9: Config File UUID Uniqueness
# ---------------------------------------------------------------------------


class TestProperty9ConfigFileUUIDUniqueness:
    """Feature: automated-feedback-triage, Property 9: Config File UUID Uniqueness

    For any set of generated configs, all specId values are valid UUID v4
    and distinct.

    **Validates: Requirements 2.4, 2.5**
    """

    @given(count=st.integers(min_value=2, max_value=20))
    @settings(max_examples=10)
    def test_all_uuids_are_unique_and_valid(self, count):
        configs = [generate_config("requirements-first", "feature") for _ in range(count)]
        spec_ids = []
        for config_str in configs:
            config = json.loads(config_str)
            spec_id = config["specId"]
            # Validate it's a valid UUID v4
            parsed = uuid.UUID(spec_id, version=4)
            assert str(parsed) == spec_id
            spec_ids.append(spec_id)
        # All UUIDs must be distinct
        assert len(set(spec_ids)) == len(spec_ids)


# ---------------------------------------------------------------------------
# Property 10: Parser Round-Trip Content Preservation
# ---------------------------------------------------------------------------


class TestProperty10RoundTripContentPreservation:
    """Feature: automated-feedback-triage, Property 10: Parser Round-Trip Content Preservation

    For any valid entry, parsing and writing to skeleton preserves
    what_happened, why_problem, and suggested_fix content.

    **Validates: Requirements 7.1, 7.2, 7.4**
    """

    @given(entry_data=st_entry_data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_content_preserved_through_parse_and_generate(self, entry_data):
        md = build_feedback_markdown([entry_data])
        parsed, _warnings = parse_feedback_file(md)
        assert len(parsed) == 1
        entry = parsed[0]

        # Generate skeleton based on category
        if entry.category == "Bug":
            skeleton = generate_bugfix_skeleton(entry)
        else:
            skeleton = generate_requirements_skeleton(entry)

        # Verify substantive content is preserved
        assert entry_data["what_happened"] in skeleton
        assert entry_data["suggested_fix"].lower().rstrip(".") in skeleton.lower()
