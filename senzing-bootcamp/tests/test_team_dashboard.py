"""Property-based tests for team_dashboard.py.

Uses Hypothesis for PBT.  Tests Properties 3, 5, and 6 from the
team-bootcamp design document.
"""

from __future__ import annotations

import string

from hypothesis import given, settings, assume
from hypothesis import strategies as st

from team_config_validator import TeamConfig, TeamMember
from team_dashboard import (
    compute_team_stats,
    render_dashboard_html,
    _best_er_rate,
    _best_cross_source,
    TOTAL_MODULES,
)


# ═══════════════════════════════════════════════════════════════════════════
# Hypothesis strategies
# ═══════════════════════════════════════════════════════════════════════════

_ID_CHARS = string.ascii_lowercase + string.digits + "_"

member_id_st = st.text(alphabet=_ID_CHARS, min_size=1, max_size=12).filter(
    lambda s: s.strip() == s and len(s.strip()) > 0
)
member_name_st = st.text(
    alphabet=string.ascii_letters + " ", min_size=1, max_size=30
).filter(lambda s: len(s.strip()) > 0)

modules_completed_st = st.lists(
    st.integers(min_value=1, max_value=12), unique=True, max_size=12
)


def member_progress_st():
    """Strategy for a single member progress dict."""
    @st.composite
    def _build(draw):
        mid = draw(member_id_st)
        name = draw(member_name_st)
        completed = draw(modules_completed_st)
        current = draw(st.integers(min_value=1, max_value=12))
        pct = len(completed) / TOTAL_MODULES * 100
        return {
            "member_id": mid,
            "member_name": name,
            "status": "ok",
            "modules_completed": completed,
            "current_module": current,
            "completion_pct": pct,
            "language": draw(st.sampled_from(["python", "java", "go", ""])),
            "data_sources": [],
            "er_stats": None,
        }
    return _build()


def team_config_st():
    """Strategy for a TeamConfig with matching member data."""
    @st.composite
    def _build(draw):
        n = draw(st.integers(min_value=2, max_value=5))
        ids = draw(st.lists(member_id_st, min_size=n, max_size=n, unique=True))
        members = []
        member_data = []
        for mid in ids:
            name = draw(member_name_st)
            members.append(TeamMember(id=mid, name=name))
            completed = draw(modules_completed_st)
            current = draw(st.integers(min_value=1, max_value=12))
            pct = len(completed) / TOTAL_MODULES * 100
            member_data.append({
                "member_id": mid,
                "member_name": name,
                "status": "ok",
                "modules_completed": completed,
                "current_module": current,
                "completion_pct": pct,
                "language": draw(st.sampled_from(["python", "java", ""])),
                "data_sources": [],
                "er_stats": None,
            })
        team_name = draw(
            st.text(alphabet=string.ascii_letters + " ", min_size=1, max_size=20)
            .filter(lambda s: len(s.strip()) > 0)
        )
        config = TeamConfig(
            team_name=team_name,
            members=members,
            mode="colocated",
        )
        return config, member_data
    return _build()


def er_stats_st():
    """Strategy for a list of ER stat dicts with positive values."""
    @st.composite
    def _build(draw):
        n = draw(st.integers(min_value=1, max_value=5))
        ids = draw(st.lists(member_id_st, min_size=n, max_size=n, unique=True))
        entries = []
        for mid in ids:
            name = draw(member_name_st)
            rl = draw(st.integers(min_value=1, max_value=10000))
            er = draw(st.integers(min_value=0, max_value=rl))
            cs = draw(st.integers(min_value=0, max_value=rl))
            entries.append({
                "member_id": mid,
                "member_name": name,
                "status": "ok",
                "records_loaded": rl,
                "entities_resolved": er,
                "duplicate_count": draw(st.integers(min_value=0, max_value=rl)),
                "cross_source_matches": cs,
                "data_sources": ["customers"],
            })
        return entries
    return _build()


# ═══════════════════════════════════════════════════════════════════════════
# Property 3: Dashboard HTML contains all required member data
# Feature: team-bootcamp, Property 3: Dashboard HTML contains all required
# member data
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty3DashboardContent:
    """**Validates: Requirements 2.8, 2.9, 2.10, 10.5**"""

    @given(data=team_config_st())
    @settings(max_examples=10)
    def test_dashboard_contains_team_name(self, data):
        """Dashboard HTML contains the team name."""
        config, member_data = data
        stats = compute_team_stats(member_data)
        er_data = [
            {"member_id": m["member_id"], "member_name": m["member_name"],
             "status": "Not yet available"}
            for m in member_data
        ]
        html = render_dashboard_html(config, member_data, stats, er_data)
        # Team name should appear in the HTML (escaped)
        escaped_name = (
            config.team_name
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        assert escaped_name in html

    @given(data=team_config_st())
    @settings(max_examples=10)
    def test_dashboard_contains_member_count(self, data):
        """Dashboard HTML contains the total member count."""
        config, member_data = data
        stats = compute_team_stats(member_data)
        er_data = [
            {"member_id": m["member_id"], "member_name": m["member_name"],
             "status": "Not yet available"}
            for m in member_data
        ]
        html = render_dashboard_html(config, member_data, stats, er_data)
        assert str(len(config.members)) in html

    @given(data=team_config_st())
    @settings(max_examples=10)
    def test_dashboard_contains_each_member_name(self, data):
        """Dashboard HTML contains each member's display name."""
        config, member_data = data
        stats = compute_team_stats(member_data)
        er_data = [
            {"member_id": m["member_id"], "member_name": m["member_name"],
             "status": "Not yet available"}
            for m in member_data
        ]
        html = render_dashboard_html(config, member_data, stats, er_data)
        for m in member_data:
            escaped = (
                m["member_name"]
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            assert escaped in html, f"Member name '{m['member_name']}' not in HTML"

    @given(data=team_config_st())
    @settings(max_examples=10)
    def test_dashboard_contains_completion_pct(self, data):
        """Dashboard HTML contains the overall completion percentage."""
        config, member_data = data
        stats = compute_team_stats(member_data)
        er_data = [
            {"member_id": m["member_id"], "member_name": m["member_name"],
             "status": "Not yet available"}
            for m in member_data
        ]
        html = render_dashboard_html(config, member_data, stats, er_data)
        avg_str = f"{stats['average_completion']:.1f}%"
        assert avg_str in html


# ═══════════════════════════════════════════════════════════════════════════
# Property 5: Team statistics are correctly computed from member progress
# Feature: team-bootcamp, Property 5: Team statistics are correctly
# computed from member progress
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty5TeamStats:
    """**Validates: Requirements 4.5**"""

    @given(
        member_data=st.lists(member_progress_st(), min_size=1, max_size=6)
    )
    @settings(max_examples=10)
    def test_average_completion(self, member_data):
        """Average completion equals mean of individual completion percentages."""
        stats = compute_team_stats(member_data)
        expected_avg = sum(
            len(m["modules_completed"]) / TOTAL_MODULES * 100
            for m in member_data
        ) / len(member_data)
        assert abs(stats["average_completion"] - expected_avg) < 0.01

    @given(
        member_data=st.lists(member_progress_st(), min_size=1, max_size=6)
    )
    @settings(max_examples=10)
    def test_total_modules_completed(self, member_data):
        """Total modules completed equals sum of all members' completed counts."""
        stats = compute_team_stats(member_data)
        expected = sum(len(m["modules_completed"]) for m in member_data)
        assert stats["total_modules_completed"] == expected

    @given(
        member_data=st.lists(member_progress_st(), min_size=1, max_size=6)
    )
    @settings(max_examples=10)
    def test_fully_completed_count(self, member_data):
        """Fully completed count equals members with all 12 modules done."""
        stats = compute_team_stats(member_data)
        expected = sum(
            1 for m in member_data
            if len(m["modules_completed"]) >= TOTAL_MODULES
        )
        assert stats["fully_completed_count"] == expected


# ═══════════════════════════════════════════════════════════════════════════
# Property 6: ER comparison correctly identifies top-performing members
# Feature: team-bootcamp, Property 6: ER comparison correctly identifies
# top-performing members
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty6ERComparison:
    """**Validates: Requirements 5.2, 5.5**"""

    @given(er_data=er_stats_st())
    @settings(max_examples=10)
    def test_best_er_rate_is_correct(self, er_data):
        """The member with highest entities_resolved/records_loaded is identified."""
        best_id = _best_er_rate(er_data)
        # Compute expected
        best_rate = -1.0
        expected_id = None
        for e in er_data:
            if e.get("status") != "ok" or e.get("records_loaded", 0) <= 0:
                continue
            rate = e["entities_resolved"] / e["records_loaded"]
            if rate > best_rate:
                best_rate = rate
                expected_id = e["member_id"]
        assert best_id == expected_id

    @given(er_data=er_stats_st())
    @settings(max_examples=10)
    def test_best_cross_source_is_correct(self, er_data):
        """The member with highest cross_source_matches is identified."""
        best_id = _best_cross_source(er_data)
        best_val = -1
        expected_id = None
        for e in er_data:
            if e.get("status") != "ok":
                continue
            cs = e.get("cross_source_matches", 0)
            if cs > best_val:
                best_val = cs
                expected_id = e["member_id"]
        assert best_id == expected_id
