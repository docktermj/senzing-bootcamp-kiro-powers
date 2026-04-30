"""Property-based tests for merge_feedback.py.

Uses Hypothesis for PBT.  Tests Property 4 from the team-bootcamp
design document.
"""

from __future__ import annotations

import string

from hypothesis import given, settings
from hypothesis import strategies as st

from merge_feedback import FeedbackEntry, compute_feedback_stats


# ═══════════════════════════════════════════════════════════════════════════
# Hypothesis strategies
# ═══════════════════════════════════════════════════════════════════════════

priority_st = st.sampled_from(["High", "Medium", "Low"])
category_st = st.sampled_from([
    "Documentation", "Workflow", "Tools", "UX",
    "Bug", "Performance", "Security",
])

_ID_CHARS = string.ascii_lowercase + string.digits + "_"

feedback_entry_st = st.builds(
    FeedbackEntry,
    member_id=st.text(alphabet=_ID_CHARS, min_size=1, max_size=10),
    member_name=st.text(
        alphabet=string.ascii_letters + " ", min_size=1, max_size=20
    ),
    title=st.text(
        alphabet=string.ascii_letters + " ", min_size=1, max_size=30
    ),
    date=st.from_regex(r"20[0-9]{2}-[01][0-9]-[0-3][0-9]", fullmatch=True),
    module=st.from_regex(r"[1-9]|1[0-2]", fullmatch=True),
    priority=priority_st,
    category=category_st,
    body=st.text(max_size=100),
)


# ═══════════════════════════════════════════════════════════════════════════
# Property 4: Feedback report statistics match input data
# Feature: team-bootcamp, Property 4: Feedback report statistics match
# input data
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty4FeedbackStats:
    """**Validates: Requirements 3.8, 3.9, 3.10**"""

    @given(entries=st.lists(feedback_entry_st, min_size=0, max_size=30))
    @settings(max_examples=100)
    def test_total_equals_entry_count(self, entries):
        """Total count in stats equals the number of entries."""
        stats = compute_feedback_stats(entries)
        assert stats["total"] == len(entries)

    @given(entries=st.lists(feedback_entry_st, min_size=0, max_size=30))
    @settings(max_examples=100)
    def test_priority_sum_equals_total(self, entries):
        """Sum of all priority counts equals total entry count."""
        stats = compute_feedback_stats(entries)
        pri_sum = sum(stats["by_priority"].values())
        assert pri_sum == stats["total"]

    @given(entries=st.lists(feedback_entry_st, min_size=0, max_size=30))
    @settings(max_examples=100)
    def test_category_sum_equals_total(self, entries):
        """Sum of all category counts equals total entry count."""
        stats = compute_feedback_stats(entries)
        cat_sum = sum(stats["by_category"].values())
        assert cat_sum == stats["total"]

    @given(entries=st.lists(feedback_entry_st, min_size=1, max_size=30))
    @settings(max_examples=100)
    def test_individual_priority_counts_match(self, entries):
        """Each priority count matches actual entries with that priority."""
        stats = compute_feedback_stats(entries)
        for pri, count in stats["by_priority"].items():
            actual = sum(1 for e in entries if e.priority == pri)
            assert count == actual, f"Priority {pri}: expected {actual}, got {count}"

    @given(entries=st.lists(feedback_entry_st, min_size=1, max_size=30))
    @settings(max_examples=100)
    def test_individual_category_counts_match(self, entries):
        """Each category count matches actual entries with that category."""
        stats = compute_feedback_stats(entries)
        for cat, count in stats["by_category"].items():
            actual = sum(1 for e in entries if e.category == cat)
            assert count == actual, f"Category {cat}: expected {actual}, got {count}"
