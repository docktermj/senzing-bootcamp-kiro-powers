#!/usr/bin/env python3
"""Senzing Bootcamp - Team Dashboard Generator.

Generates a self-contained HTML dashboard showing all team members'
bootcamp progress, module completion heatmap, and ER comparison.
Depends only on the Python standard library.  Cross-platform.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from team_config_validator import (
    TeamConfig,
    TeamConfigError,
    TeamMember,
    PathResolver,
    load_and_validate,
)

MODULE_NAMES = {
    1: "Business Problem",
    2: "SDK Setup",
    3: "System Verification",
    4: "Data Collection",
    5: "Data Quality & Mapping",
    6: "Single Source Loading",
    7: "Multi-Source Orchestration",
    8: "Query, Visualize & Validate",
    9: "Performance Testing",
    10: "Security Hardening",
    11: "Monitoring",
    12: "Deployment",
}

TOTAL_MODULES = 12


# ── Data collection ───────────────────────────────────────────────────────


def collect_member_progress(
    config: TeamConfig, resolver: PathResolver
) -> list[dict]:
    """Read each member's progress file via PathResolver.

    Returns a list of dicts, one per member, with keys:
      member_id, member_name, status, modules_completed, current_module,
      completion_pct, language, data_sources, er_stats
    Members with missing/unreadable files get status='No data available'.
    """
    results: list[dict] = []
    for member in config.members:
        p = Path(str(resolver.progress_path(member)))
        entry: dict = {
            "member_id": member.id,
            "member_name": member.name,
        }
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            completed = data.get("modules_completed", [])
            entry["status"] = "ok"
            entry["modules_completed"] = completed
            entry["current_module"] = data.get("current_module", 1)
            entry["completion_pct"] = (
                len(completed) / TOTAL_MODULES * 100 if TOTAL_MODULES else 0
            )
            entry["language"] = data.get("language", "")
            entry["data_sources"] = data.get("data_sources", [])
            entry["er_stats"] = data.get("er_stats")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"Warning: cannot read progress for {member.id}: {exc}", file=sys.stderr)
            entry["status"] = "No data available"
            entry["modules_completed"] = []
            entry["current_module"] = 0
            entry["completion_pct"] = 0.0
            entry["language"] = ""
            entry["data_sources"] = []
            entry["er_stats"] = None
        results.append(entry)
    return results


# ── Statistics ────────────────────────────────────────────────────────────


def compute_team_stats(member_data: list[dict]) -> dict:
    """Compute team-level statistics from member progress data.

    Returns dict with keys:
      average_completion, total_modules_completed,
      lowest_completion_module, fully_completed_count
    """
    if not member_data:
        return {
            "average_completion": 0.0,
            "total_modules_completed": 0,
            "lowest_completion_module": None,
            "fully_completed_count": 0,
        }

    # Average completion %
    pcts = [m.get("completion_pct", 0.0) for m in member_data]
    avg = sum(pcts) / len(pcts)

    # Total modules completed across all members
    total = sum(len(m.get("modules_completed", [])) for m in member_data)

    # Fully completed count (all 12 modules)
    fully = sum(
        1
        for m in member_data
        if len(m.get("modules_completed", [])) >= TOTAL_MODULES
    )

    # Lowest-completion module: the module number completed by fewest members
    module_counts: dict[int, int] = {}
    for mod in range(1, TOTAL_MODULES + 1):
        module_counts[mod] = sum(
            1
            for m in member_data
            if mod in m.get("modules_completed", [])
        )
    lowest_mod = min(module_counts, key=module_counts.get)  # type: ignore[arg-type]

    return {
        "average_completion": avg,
        "total_modules_completed": total,
        "lowest_completion_module": lowest_mod,
        "fully_completed_count": fully,
    }


# ── ER stats collection ──────────────────────────────────────────────────


def collect_er_stats(
    config: TeamConfig, resolver: PathResolver
) -> list[dict]:
    """Read ER statistics from progress for Module 6+ members.

    Returns a list of dicts with keys:
      member_id, member_name, status, records_loaded, entities_resolved,
      duplicate_count, cross_source_matches, data_sources
    Members who haven't reached Module 6 get status='Not yet available'.
    """
    results: list[dict] = []
    for member in config.members:
        p = Path(str(resolver.progress_path(member)))
        entry: dict = {
            "member_id": member.id,
            "member_name": member.name,
        }
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            completed = data.get("modules_completed", [])
            er = data.get("er_stats")
            if 6 in completed and isinstance(er, dict):
                entry["status"] = "ok"
                entry["records_loaded"] = er.get("records_loaded", 0)
                entry["entities_resolved"] = er.get("entities_resolved", 0)
                entry["duplicate_count"] = er.get("duplicate_count", 0)
                entry["cross_source_matches"] = er.get("cross_source_matches", 0)
                entry["data_sources"] = data.get("data_sources", [])
            else:
                entry["status"] = "Not yet available"
        except (OSError, json.JSONDecodeError, ValueError):
            entry["status"] = "Not yet available"
        results.append(entry)
    return results


# ── HTML rendering ────────────────────────────────────────────────────────


def render_dashboard_html(
    config: TeamConfig,
    member_data: list[dict],
    team_stats: dict,
    er_data: list[dict],
) -> str:
    """Generate a self-contained HTML dashboard string.

    Includes inline CSS, semantic HTML elements, team summary,
    per-member table, module heatmap, ER comparison, nav bar,
    and generation timestamp in footer.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    member_count = len(config.members)
    avg_pct = team_stats.get("average_completion", 0.0)
    total_mods = team_stats.get("total_modules_completed", 0)
    lowest_mod = team_stats.get("lowest_completion_module")
    fully_done = team_stats.get("fully_completed_count", 0)

    # ── Build member rows ──
    member_rows = ""
    for m in member_data:
        name = _esc(m["member_name"])
        mid = _esc(m["member_id"])
        if m["status"] == "No data available":
            member_rows += (
                f'<tr><td>{name} ({mid})</td>'
                f'<td colspan="4" class="no-data">No data available</td></tr>\n'
            )
        else:
            cur = m.get("current_module", 0)
            done = len(m.get("modules_completed", []))
            lang = _esc(m.get("language", ""))
            pct = m.get("completion_pct", 0.0)
            member_rows += (
                f"<tr><td>{name} ({mid})</td>"
                f"<td>{cur}</td><td>{done}</td>"
                f"<td>{lang}</td><td>{pct:.0f}%</td></tr>\n"
            )

    # ── Build heatmap rows ──
    heatmap_header = "".join(f"<th>M{i}</th>" for i in range(1, 13))
    heatmap_rows = ""
    for m in member_data:
        name = _esc(m["member_name"])
        completed = set(m.get("modules_completed", []))
        cur = m.get("current_module", 0)
        cells = ""
        for mod in range(1, 13):
            if mod in completed:
                cells += '<td class="mod-done">&#10003;</td>'
            elif mod == cur and m["status"] != "No data available":
                cells += '<td class="mod-progress">&#9679;</td>'
            else:
                cells += '<td class="mod-none">&mdash;</td>'
        heatmap_rows += f"<tr><td>{name}</td>{cells}</tr>\n"

    # ── Build ER comparison rows ──
    er_rows = ""
    # Find top performers for highlights
    best_rate_id = _best_er_rate(er_data)
    best_cross_id = _best_cross_source(er_data)

    for e in er_data:
        name = _esc(e["member_name"])
        if e["status"] == "Not yet available":
            er_rows += (
                f'<tr><td>{name}</td>'
                f'<td colspan="5" class="no-data">Not yet available</td></tr>\n'
            )
        else:
            rl = e.get("records_loaded", 0)
            er_val = e.get("entities_resolved", 0)
            dup = e.get("duplicate_count", 0)
            cs = e.get("cross_source_matches", 0)
            ds = ", ".join(e.get("data_sources", []))
            rate_cls = ' class="highlight"' if e["member_id"] == best_rate_id else ""
            cross_cls = ' class="highlight"' if e["member_id"] == best_cross_id else ""
            er_rows += (
                f"<tr><td>{name}</td>"
                f"<td>{rl}</td>"
                f"<td{rate_cls}>{er_val}</td>"
                f"<td>{dup}</td>"
                f"<td{cross_cls}>{cs}</td>"
                f"<td>{_esc(ds)}</td></tr>\n"
            )

    lowest_label = f"Module {lowest_mod}" if lowest_mod else "N/A"

    html = _HTML_TEMPLATE.format(
        team_name=_esc(config.team_name),
        member_count=member_count,
        avg_pct=f"{avg_pct:.1f}",
        total_mods=total_mods,
        lowest_mod=lowest_label,
        fully_done=fully_done,
        member_rows=member_rows,
        heatmap_header=heatmap_header,
        heatmap_rows=heatmap_rows,
        er_rows=er_rows,
        timestamp=now,
    )
    return html


def _esc(s: str) -> str:
    """Minimal HTML escaping."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _best_er_rate(er_data: list[dict]) -> str | None:
    """Return member_id with highest entities_resolved/records_loaded."""
    best_id = None
    best_rate = -1.0
    for e in er_data:
        if e.get("status") != "ok":
            continue
        rl = e.get("records_loaded", 0)
        if rl <= 0:
            continue
        rate = e.get("entities_resolved", 0) / rl
        if rate > best_rate:
            best_rate = rate
            best_id = e["member_id"]
    return best_id


def _best_cross_source(er_data: list[dict]) -> str | None:
    """Return member_id with highest cross_source_matches."""
    best_id = None
    best_val = -1
    for e in er_data:
        if e.get("status") != "ok":
            continue
        cs = e.get("cross_source_matches", 0)
        if cs > best_val:
            best_val = cs
            best_id = e["member_id"]
    return best_id


_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{team_name} - Team Dashboard</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         color: #333; background: #f5f7fa; line-height: 1.6; }}
  header {{ background: #1a73e8; color: #fff; padding: 1.5rem 2rem; }}
  header h1 {{ font-size: 1.8rem; }}
  nav {{ background: #fff; border-bottom: 1px solid #ddd; padding: 0.5rem 2rem;
         display: flex; gap: 1.5rem; flex-wrap: wrap; }}
  nav a {{ color: #1a73e8; text-decoration: none; font-weight: 500; }}
  nav a:hover {{ text-decoration: underline; }}
  main {{ max-width: 1200px; margin: 1.5rem auto; padding: 0 1rem; }}
  section {{ background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 1.5rem; margin-bottom: 1.5rem; }}
  section h2 {{ margin-bottom: 1rem; color: #1a73e8; }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                 gap: 1rem; }}
  .stat-card {{ background: #f0f4ff; border-radius: 6px; padding: 1rem; text-align: center; }}
  .stat-card .value {{ font-size: 2rem; font-weight: 700; color: #1a73e8; }}
  .stat-card .label {{ font-size: 0.85rem; color: #666; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 0.5rem; }}
  th, td {{ padding: 0.6rem 0.8rem; text-align: left; border-bottom: 1px solid #eee; }}
  th {{ background: #f8f9fa; font-weight: 600; }}
  .no-data {{ color: #999; font-style: italic; }}
  .mod-done {{ background: #c8e6c9; color: #2e7d32; text-align: center; font-weight: 700; }}
  .mod-progress {{ background: #fff9c4; color: #f57f17; text-align: center; }}
  .mod-none {{ background: #f5f5f5; color: #bbb; text-align: center; }}
  .highlight {{ background: #e8f5e9; font-weight: 700; }}
  footer {{ text-align: center; padding: 1rem; color: #999; font-size: 0.85rem; }}
  @media (max-width: 768px) {{
    .stats-grid {{ grid-template-columns: 1fr 1fr; }}
    table {{ font-size: 0.85rem; }}
  }}
</style>
</head>
<body>
<header>
  <h1>{team_name} - Team Dashboard</h1>
</header>
<nav>
  <a href="#summary">Team Summary</a>
  <a href="#members">Member Progress</a>
  <a href="#heatmap">Module Heatmap</a>
  <a href="#er-comparison">ER Comparison</a>
</nav>
<main>
  <section id="summary">
    <h2>Team Summary</h2>
    <div class="stats-grid">
      <div class="stat-card"><div class="value">{member_count}</div><div class="label">Members</div></div>
      <div class="stat-card"><div class="value">{avg_pct}%</div><div class="label">Avg Completion</div></div>
      <div class="stat-card"><div class="value">{total_mods}</div><div class="label">Total Modules Done</div></div>
      <div class="stat-card"><div class="value">{lowest_mod}</div><div class="label">Lowest Completion Module</div></div>
      <div class="stat-card"><div class="value">{fully_done}</div><div class="label">Fully Completed</div></div>
    </div>
  </section>
  <section id="members">
    <h2>Member Progress</h2>
    <table>
      <thead><tr><th>Member</th><th>Current Module</th><th>Completed</th><th>Language</th><th>Completion</th></tr></thead>
      <tbody>
{member_rows}
      </tbody>
    </table>
  </section>
  <section id="heatmap">
    <h2>Module Heatmap</h2>
    <table>
      <thead><tr><th>Member</th>{heatmap_header}</tr></thead>
      <tbody>
{heatmap_rows}
      </tbody>
    </table>
  </section>
  <section id="er-comparison">
    <h2>ER Comparison</h2>
    <table>
      <thead><tr><th>Member</th><th>Records Loaded</th><th>Entities Resolved</th><th>Duplicates</th><th>Cross-Source</th><th>Data Sources</th></tr></thead>
      <tbody>
{er_rows}
      </tbody>
    </table>
  </section>
</main>
<footer>
  Generated: {timestamp}
</footer>
</body>
</html>
"""


# ── CLI / main ────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point: load config, collect data, render, write file."""
    parser = argparse.ArgumentParser(
        description="Generate team bootcamp dashboard",
        epilog="See Also: status.py (individual progress), analyze_sessions.py (historical analytics)",
    )
    parser.add_argument(
        "--output",
        default="exports/team_dashboard.html",
        help="Output HTML file path (default: exports/team_dashboard.html)",
    )
    args = parser.parse_args()

    try:
        config = load_and_validate()
    except TeamConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    resolver = PathResolver(config)
    member_data = collect_member_progress(config, resolver)
    team_stats = compute_team_stats(member_data)
    er_data = collect_er_stats(config, resolver)
    html = render_dashboard_html(config, member_data, team_stats, er_data)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Dashboard written to {out}")


if __name__ == "__main__":
    main()
