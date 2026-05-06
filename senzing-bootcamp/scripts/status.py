#!/usr/bin/env python3
"""Senzing Bootcamp - Status Command.

Shows current module, progress, and next steps.
Cross-platform: works on Linux, macOS, and Windows.
"""

import argparse
import dataclasses
import json
import os
import re
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

# Team mode imports (optional — only used when config/team.yaml exists)
_TEAM_AVAILABLE = False
try:
    from team_config_validator import (
        load_and_validate as _load_team_config,
        PathResolver as _PathResolver,
        TeamConfigError as _TeamConfigError,
    )
    _TEAM_AVAILABLE = True
except ImportError:
    pass


def color_supported():
    if os.environ.get("NO_COLOR"):
        return False
    if sys.platform == "win32":
        return os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM") or "ANSICON" in os.environ
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


USE_COLOR = color_supported()


def c(code, text):
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def green(t): return c("0;32", t)
def yellow(t): return c("1;33", t)
def blue(t): return c("0;34", t)
def cyan(t): return c("0;36", t)


MODULE_NAMES = {
    1: "Business Problem", 2: "SDK Setup", 3: "Quick Demo",
    4: "Data Collection", 5: "Data Quality & Mapping",
    6: "Load Data", 7: "Query & Visualize",
    8: "Performance Testing", 9: "Security Hardening",
    10: "Monitoring", 11: "Deployment",
    12: "Production Readiness",
}

NEXT_STEPS = {
    1:  ("Start Module 1: Business Problem", "Define your problem and identify data sources"),
    2:  ("Start Module 2: SDK Setup", "Install and configure Senzing SDK"),
    3:  ("Start Module 3: Quick Demo", "See entity resolution in action with sample data"),
    4:  ("Start Module 4: Data Collection", "Upload or link to data source files"),
    5:  ("Start Module 5: Data Quality & Mapping", "Evaluate data quality and create transformation programs"),
    6:  ("Start Module 6: Load Data", "Load your data sources and validate results"),
    7:  ("Start Module 7: Query & Visualize", "Create query programs and visualize results"),
    8:  ("Start Module 8: Performance Testing", "Benchmark and optimize performance"),
    9:  ("Start Module 9: Security Hardening", "Implement security best practices"),
    10: ("Start Module 10: Monitoring", "Set up monitoring and observability"),
    11: ("Start Module 11: Deployment", "Package and deploy to production"),
}


# ---------------------------------------------------------------------------
# Task 1: Data models
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class QualityScoreData:
    """Quality score for a single data source."""
    source_name: str
    overall: float  # 0-100
    completeness: float = None
    consistency: float = None
    format_compliance: float = None
    uniqueness: float = None

    @property
    def band(self) -> str:
        """'green' if >=80, 'yellow' if >=70, 'red' if <70."""
        if self.overall >= 80:
            return "green"
        if self.overall >= 70:
            return "yellow"
        return "red"


@dataclasses.dataclass
class PerformanceData:
    """Performance metrics from loading and querying."""
    loading_throughput_rps: float = None
    query_avg_ms: float = None
    query_p95_ms: float = None
    database_type: str = None
    wall_clock_seconds: float = None


@dataclasses.dataclass
class EntityStatsData:
    """Entity resolution statistics."""
    total_records: int = None
    total_entities: int = None
    match_count: int = None
    duplicate_count: int = None
    cross_source_matches: int = None


@dataclasses.dataclass
class HealthCheckItem:
    """A single project health check."""
    label: str
    path: str
    exists: bool


@dataclasses.dataclass
class DashboardData:
    """All data needed to render the HTML dashboard."""
    modules_completed: list
    current_module: int
    status: str
    language: str
    completion_pct: int
    completion_timestamps: dict
    quality_scores: list
    performance: PerformanceData
    entity_stats: EntityStatsData
    health_checks: list
    health_score: int
    health_total: int
    generated_at: str
    has_progress_data: bool


# ---------------------------------------------------------------------------
# Task 2: DashboardDataCollector
# ---------------------------------------------------------------------------

class DashboardDataCollector:
    """Gathers data from project artifacts to populate DashboardData."""

    _HEALTH_PATHS = [
        (os.path.join("data", "raw"), "Data directory"),
        ("database", "Database directory"),
        ("src", "Source directory"),
        ("scripts", "Scripts directory"),
        (".gitignore", ".gitignore"),
        (".env.example", ".env.example"),
        ("README.md", "README.md"),
        ("backups", "Backups directory"),
    ]

    def __init__(self, project_root: str):
        self.root = Path(project_root)

    # -- 2.1 collect orchestrator ------------------------------------------

    def collect(self) -> DashboardData:
        """Gather all data sources and return a populated DashboardData."""
        completed, current, status, language, current_step, raw_data = self._load_progress()
        has_progress = len(completed) > 0 or status != "Not Started"
        completion_pct = len(completed) * 100 // 12
        timestamps = self._load_completion_timestamps(raw_data)
        quality = self._scan_quality_scores()
        perf = self._scan_performance_metrics()
        entity = self._scan_entity_stats()
        checks, h_score, h_total = self._check_health()
        return DashboardData(
            modules_completed=sorted(completed),
            current_module=current,
            status=status,
            language=language,
            completion_pct=completion_pct,
            completion_timestamps=timestamps,
            quality_scores=quality,
            performance=perf,
            entity_stats=entity,
            health_checks=checks,
            health_score=h_score,
            health_total=h_total,
            generated_at=datetime.now(timezone.utc).isoformat(),
            has_progress_data=has_progress,
        )

    # -- 2.2 _load_progress ------------------------------------------------

    def _load_progress(self):
        """Load module progress. Returns (completed, current, status, language, step, raw_dict)."""
        progress_json = self.root / "config" / "bootcamp_progress.json"
        progress_md = self.root / "docs" / "guides" / "PROGRESS_TRACKER.md"

        completed = []
        current = 1
        status = "Not Started"
        language = None
        current_step = None
        raw_data = {}

        if progress_json.is_file():
            try:
                raw_data = json.loads(progress_json.read_text(encoding="utf-8"))
                completed = raw_data.get("modules_completed", [])
                current = raw_data.get("current_module", 1)
                language = raw_data.get("language")
                current_step = raw_data.get("current_step")
                if completed:
                    last = max(completed)
                    if current > last:
                        status = "Ready to Start"
                    elif current in completed:
                        status = "Complete" if last >= 11 else "Ready to Start"
                    else:
                        status = "In Progress"
            except (json.JSONDecodeError, KeyError):
                print("Warning: invalid JSON in bootcamp_progress.json, skipping", file=sys.stderr)
        elif progress_md.is_file():
            checked_re = re.compile(r"\[x\].*Module\s+(\d+)", re.IGNORECASE)
            unchecked_re = re.compile(r"\[\s\].*Module\s+(\d+)", re.IGNORECASE)
            in_progress = None
            try:
                for line in progress_md.read_text(encoding="utf-8").splitlines():
                    m = checked_re.search(line)
                    if m:
                        completed.append(int(m.group(1)))
                        continue
                    m = unchecked_re.search(line)
                    if m and in_progress is None:
                        in_progress = int(m.group(1))
            except OSError:
                pass
            if not completed:
                current = 1
                status = "Not Started"
            elif in_progress is not None:
                current = in_progress
                status = "In Progress"
            else:
                last = max(completed)
                current = min(last + 1, 11)
                status = "Complete" if last >= 11 else "Ready to Start"

        return completed, current, status, language, current_step, raw_data

    # -- 2.3 _load_completion_timestamps -----------------------------------

    def _load_completion_timestamps(self, progress_data: dict) -> dict:
        """Extract module completion timestamps from step_history."""
        timestamps = {}
        try:
            step_history = progress_data.get("step_history", {})
            for key, entry in step_history.items():
                try:
                    mod_num = int(str(key).split(".")[0].split("_")[-1])
                except (ValueError, IndexError):
                    # Try parsing "module_N" or just "N"
                    m = re.search(r"(\d+)", str(key))
                    if m:
                        mod_num = int(m.group(1))
                    else:
                        continue
                if 1 <= mod_num <= 12:
                    ts = None
                    if isinstance(entry, dict):
                        ts = entry.get("updated_at") or entry.get("completed_at") or entry.get("timestamp")
                    elif isinstance(entry, str):
                        ts = entry
                    if ts and mod_num not in timestamps:
                        timestamps[mod_num] = str(ts)
        except Exception:
            pass
        return timestamps

    # -- 2.4 _scan_quality_scores ------------------------------------------

    def _scan_quality_scores(self) -> list:
        """Scan docs artifacts for quality score data."""
        scores = []
        docs_dir = self.root / "docs"
        if not docs_dir.is_dir():
            return scores
        patterns = list(docs_dir.glob("*quality*")) + list(docs_dir.glob("*data_source_evaluation*"))
        overall_re = re.compile(r"overall[^:]*:\s*([\d.]+)", re.IGNORECASE)
        source_re = re.compile(r"(?:source|data\s*source)[^:]*:\s*(.+)", re.IGNORECASE)
        completeness_re = re.compile(r"completeness[^:]*:\s*([\d.]+)", re.IGNORECASE)
        consistency_re = re.compile(r"consistency[^:]*:\s*([\d.]+)", re.IGNORECASE)
        format_re = re.compile(r"format[_ ]?compliance[^:]*:\s*([\d.]+)", re.IGNORECASE)
        uniqueness_re = re.compile(r"uniqueness[^:]*:\s*([\d.]+)", re.IGNORECASE)

        for fpath in patterns:
            if not fpath.is_file():
                continue
            try:
                text = fpath.read_text(encoding="utf-8")
            except OSError:
                continue
            m_overall = overall_re.search(text)
            if not m_overall:
                continue
            overall = float(m_overall.group(1))
            m_source = source_re.search(text)
            source_name = m_source.group(1).strip() if m_source else fpath.stem

            def _extract(pat):
                m = pat.search(text)
                return float(m.group(1)) if m else None

            scores.append(QualityScoreData(
                source_name=source_name,
                overall=overall,
                completeness=_extract(completeness_re),
                consistency=_extract(consistency_re),
                format_compliance=_extract(format_re),
                uniqueness=_extract(uniqueness_re),
            ))
        return scores

    # -- 2.5 _scan_performance_metrics -------------------------------------

    def _scan_performance_metrics(self) -> PerformanceData:
        """Scan project artifacts for performance metrics."""
        docs_dir = self.root / "docs"
        if not docs_dir.is_dir():
            return None
        patterns = list(docs_dir.glob("*performance*")) + list(docs_dir.glob("*benchmark*"))
        throughput_re = re.compile(r"(?:throughput|records?\s*/?\s*s(?:ec(?:ond)?)?)[^:]*:\s*([\d,.]+)", re.IGNORECASE)
        avg_re = re.compile(r"(?:average|avg)\s*(?:query)?\s*(?:response)?\s*(?:time)?[^:]*:\s*([\d,.]+)\s*ms", re.IGNORECASE)
        p95_re = re.compile(r"p95[^:]*:\s*([\d,.]+)\s*ms", re.IGNORECASE)
        db_re = re.compile(r"database[_ ]?type[^:]*:\s*(\w+)", re.IGNORECASE)
        wall_re = re.compile(r"wall[_ ]?clock[^:]*:\s*([\d,.]+)\s*s", re.IGNORECASE)

        throughput = None
        avg_ms = None
        p95_ms = None
        db_type = None
        wall_s = None

        for fpath in patterns:
            if not fpath.is_file():
                continue
            try:
                text = fpath.read_text(encoding="utf-8")
            except OSError:
                continue

            def _first_float(pat, txt):
                m = pat.search(txt)
                return float(m.group(1).replace(",", "")) if m else None

            if throughput is None:
                throughput = _first_float(throughput_re, text)
            if avg_ms is None:
                avg_ms = _first_float(avg_re, text)
            if p95_ms is None:
                p95_ms = _first_float(p95_re, text)
            if db_type is None:
                m = db_re.search(text)
                if m:
                    db_type = m.group(1).lower()
            if wall_s is None:
                wall_s = _first_float(wall_re, text)

        if any(v is not None for v in (throughput, avg_ms, p95_ms, db_type, wall_s)):
            return PerformanceData(
                loading_throughput_rps=throughput,
                query_avg_ms=avg_ms,
                query_p95_ms=p95_ms,
                database_type=db_type,
                wall_clock_seconds=wall_s,
            )
        return None

    # -- 2.6 _scan_entity_stats --------------------------------------------

    def _scan_entity_stats(self) -> EntityStatsData:
        """Scan project artifacts for entity resolution statistics."""
        docs_dir = self.root / "docs"
        if not docs_dir.is_dir():
            return None
        patterns = list(docs_dir.glob("*entity*")) + list(docs_dir.glob("*resolution*")) + list(docs_dir.glob("*results*"))
        records_re = re.compile(r"total\s*records?[^:]*:\s*([\d,]+)", re.IGNORECASE)
        entities_re = re.compile(r"total\s*entit(?:y|ies)[^:]*:\s*([\d,]+)", re.IGNORECASE)
        match_re = re.compile(r"match(?:es)?\s*(?:count)?[^:]*:\s*([\d,]+)", re.IGNORECASE)
        dup_re = re.compile(r"duplicate(?:s)?\s*(?:count)?[^:]*:\s*([\d,]+)", re.IGNORECASE)
        cross_re = re.compile(r"cross[_ ]?source[^:]*:\s*([\d,]+)", re.IGNORECASE)

        total_records = None
        total_entities = None
        match_count = None
        dup_count = None
        cross_matches = None

        for fpath in patterns:
            if not fpath.is_file():
                continue
            try:
                text = fpath.read_text(encoding="utf-8")
            except OSError:
                continue

            def _first_int(pat, txt):
                m = pat.search(txt)
                return int(m.group(1).replace(",", "")) if m else None

            if total_records is None:
                total_records = _first_int(records_re, text)
            if total_entities is None:
                total_entities = _first_int(entities_re, text)
            if match_count is None:
                match_count = _first_int(match_re, text)
            if dup_count is None:
                dup_count = _first_int(dup_re, text)
            if cross_matches is None:
                cross_matches = _first_int(cross_re, text)

        if any(v is not None for v in (total_records, total_entities, match_count, dup_count, cross_matches)):
            return EntityStatsData(
                total_records=total_records,
                total_entities=total_entities,
                match_count=match_count,
                duplicate_count=dup_count,
                cross_source_matches=cross_matches,
            )
        return None

    # -- 2.7 _check_health ------------------------------------------------

    def _check_health(self):
        """Check 8 project health paths. Returns (items, score, total)."""
        items = []
        score = 0
        for rel_path, label in self._HEALTH_PATHS:
            exists = (self.root / rel_path).exists()
            items.append(HealthCheckItem(label=label, path=rel_path, exists=exists))
            if exists:
                score += 1
        return items, score, len(self._HEALTH_PATHS)


# ---------------------------------------------------------------------------
# Task 3: DashboardRenderer
# ---------------------------------------------------------------------------

class DashboardRenderer:
    """Renders DashboardData into a self-contained HTML string."""

    _BAND_COLORS = {"green": "#2d8a4e", "yellow": "#b08800", "red": "#cf222e"}

    # -- 3.1 _render_head --------------------------------------------------

    def _render_head(self) -> str:
        return """<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Senzing Bootcamp Dashboard</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  background:#f6f8fa;color:#24292f;line-height:1.5;padding:0 16px 40px}
header{background:linear-gradient(135deg,#0969da,#1f6feb);color:#fff;padding:24px 32px;
  border-radius:0 0 12px 12px;margin-bottom:24px;text-align:center}
header h1{font-size:1.6rem;margin-bottom:4px}
.status-badge{display:inline-block;padding:2px 12px;border-radius:12px;font-size:.85rem;
  background:rgba(255,255,255,.25);margin-top:6px}
main{max-width:960px;margin:0 auto}
section{background:#fff;border:1px solid #d0d7de;border-radius:8px;padding:20px 24px;margin-bottom:20px}
section h2{font-size:1.15rem;margin-bottom:12px;color:#24292f}
.progress-bar-outer{background:#d0d7de;border-radius:6px;height:22px;overflow:hidden;position:relative}
.progress-bar-inner{background:#2da44e;height:100%;border-radius:6px;transition:width .3s}
.progress-label{text-align:center;margin-top:6px;font-size:.9rem;color:#57606a}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px}
.card{border:1px solid #d0d7de;border-radius:8px;padding:14px;text-align:center;font-size:.9rem}
.card .num{font-weight:600;font-size:1rem}
.card.completed{border-color:#2da44e;background:#dafbe1}
.card.in-progress{border-color:#bf8700;background:#fff8c5}
.card.not-started{border-color:#d0d7de;background:#f6f8fa;color:#8b949e}
.card .indicator{font-size:1.3rem;margin-bottom:4px}
.metric-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px}
.metric-item{text-align:center;padding:10px;border:1px solid #d0d7de;border-radius:8px}
.metric-item .value{font-size:1.3rem;font-weight:700;color:#0969da}
.metric-item .label{font-size:.8rem;color:#57606a}
.quality-item{margin-bottom:14px;padding:10px;border:1px solid #d0d7de;border-radius:8px}
.quality-item .header-row{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.quality-item .source{font-weight:600}
.quality-item .score-badge{padding:2px 10px;border-radius:10px;color:#fff;font-weight:600;font-size:.85rem}
.sub-scores{display:flex;gap:12px;flex-wrap:wrap;font-size:.82rem;color:#57606a}
.timeline-list{list-style:none;border-left:3px solid #0969da;padding-left:20px}
.timeline-list li{margin-bottom:12px;position:relative}
.timeline-list li::before{content:'';position:absolute;left:-26px;top:6px;width:10px;height:10px;
  background:#0969da;border-radius:50%}
.timeline-list .date{font-size:.8rem;color:#57606a}
.health-item{display:flex;align-items:center;gap:8px;padding:4px 0;font-size:.9rem}
.health-item .icon{font-size:1.1rem}
.health-score{margin-top:10px;font-weight:600;font-size:.95rem}
footer{text-align:center;color:#57606a;font-size:.8rem;padding:16px 0;margin-top:8px}
.notice{background:#fff8c5;border:1px solid #bf8700;border-radius:8px;padding:14px;text-align:center;
  margin-bottom:20px;color:#6a5300}
@media print{body{background:#fff;padding:0}header{background:#0969da;-webkit-print-color-adjust:exact;
  print-color-adjust:exact}section{break-inside:avoid}}
@media(max-width:600px){.cards{grid-template-columns:repeat(auto-fill,minmax(140px,1fr))}
  .metric-grid{grid-template-columns:1fr 1fr}}
</style>
</head>"""

    # -- 3.2 _render_header ------------------------------------------------

    def _render_header(self, data: DashboardData) -> str:
        lang_line = f"<div style='font-size:.9rem;margin-top:4px'>Language: {_esc(data.language)}</div>" if data.language else ""
        return f"""<header>
<h1>Senzing Bootcamp Dashboard</h1>
<div class="status-badge">{_esc(data.status)}</div>
<div style="font-size:.95rem;margin-top:6px">{len(data.modules_completed)} / 12 modules</div>
{lang_line}
</header>"""

    # -- 3.3 _render_progress_bar ------------------------------------------

    def _render_progress_bar(self, data: DashboardData) -> str:
        pct = data.completion_pct
        return f"""<section id="progress">
<h2>Overall Progress</h2>
<div class="progress-bar-outer"><div class="progress-bar-inner" style="width:{pct}%"></div></div>
<div class="progress-label">{pct}% complete &mdash; {len(data.modules_completed)} / 12 modules</div>
</section>"""

    # -- 3.4 _render_module_cards ------------------------------------------

    def _render_module_cards(self, data: DashboardData) -> str:
        cards = []
        for num in range(1, 13):
            name = MODULE_NAMES.get(num, "?")
            if num in data.modules_completed:
                cls = "completed"
                indicator = "&#x2705;"  # ✅
            elif num == data.current_module and num not in data.modules_completed:
                cls = "in-progress"
                indicator = "&#x1F504;"  # 🔄
            else:
                cls = "not-started"
                indicator = "&#x2B1C;"  # ⬜
            cards.append(
                f'<div class="card {cls}">'
                f'<div class="indicator">{indicator}</div>'
                f'<div class="num">Module {num}</div>'
                f'<div>{_esc(name)}</div></div>'
            )
        return f'<section id="modules"><h2>Modules</h2><div class="cards">{"".join(cards)}</div></section>'

    # -- 3.5 _render_quality_section ---------------------------------------

    def _render_quality_section(self, scores: list) -> str:
        if not scores:
            return ""
        items = []
        for qs in scores:
            bg = self._BAND_COLORS.get(qs.band, "#57606a")
            subs = []
            for label, val in [("Completeness", qs.completeness), ("Consistency", qs.consistency),
                               ("Format", qs.format_compliance), ("Uniqueness", qs.uniqueness)]:
                if val is not None:
                    subs.append(f"<span>{label}: {val:.1f}</span>")
            sub_html = f'<div class="sub-scores">{" ".join(subs)}</div>' if subs else ""
            items.append(
                f'<div class="quality-item">'
                f'<div class="header-row"><span class="source">{_esc(qs.source_name)}</span>'
                f'<span class="score-badge" style="background:{bg}">{qs.overall:.1f}</span></div>'
                f'{sub_html}</div>'
            )
        return f'<section id="quality"><h2>Data Quality Scores</h2>{"".join(items)}</section>'

    # -- 3.6 _render_performance_section -----------------------------------

    def _render_performance_section(self, perf) -> str:
        if perf is None:
            return ""
        items = []
        if perf.loading_throughput_rps is not None:
            items.append(f'<div class="metric-item"><div class="value">{perf.loading_throughput_rps:,.1f}</div><div class="label">Records / sec</div></div>')
        if perf.query_avg_ms is not None:
            items.append(f'<div class="metric-item"><div class="value">{perf.query_avg_ms:,.1f}</div><div class="label">Avg Query (ms)</div></div>')
        if perf.query_p95_ms is not None:
            items.append(f'<div class="metric-item"><div class="value">{perf.query_p95_ms:,.1f}</div><div class="label">P95 Query (ms)</div></div>')
        if perf.database_type is not None:
            items.append(f'<div class="metric-item"><div class="value">{_esc(perf.database_type)}</div><div class="label">Database Type</div></div>')
        if perf.wall_clock_seconds is not None:
            items.append(f'<div class="metric-item"><div class="value">{perf.wall_clock_seconds:,.1f}</div><div class="label">Wall Clock (s)</div></div>')
        if not items:
            return ""
        return f'<section id="performance"><h2>Performance Metrics</h2><div class="metric-grid">{"".join(items)}</div></section>'

    # -- 3.7 _render_entity_section ----------------------------------------

    def _render_entity_section(self, stats) -> str:
        if stats is None:
            return ""
        items = []
        for label, val in [("Total Records", stats.total_records), ("Total Entities", stats.total_entities),
                           ("Matches", stats.match_count), ("Duplicates", stats.duplicate_count),
                           ("Cross-Source", stats.cross_source_matches)]:
            if val is not None:
                items.append(f'<div class="metric-item"><div class="value">{val:,}</div><div class="label">{label}</div></div>')
        if not items:
            return ""
        return f'<section id="entities"><h2>Entity Resolution Statistics</h2><div class="metric-grid">{"".join(items)}</div></section>'

    # -- 3.8 _render_timeline ----------------------------------------------

    def _render_timeline(self, data: DashboardData) -> str:
        if not data.completion_timestamps:
            return ""
        # Sort by timestamp value chronologically
        sorted_entries = sorted(data.completion_timestamps.items(), key=lambda kv: kv[1])
        items = []
        for mod_num, ts in sorted_entries:
            name = MODULE_NAMES.get(mod_num, "?")
            # Show just the date portion if it's an ISO timestamp
            display_date = ts[:10] if len(ts) >= 10 else ts
            items.append(f'<li><strong>Module {mod_num}: {_esc(name)}</strong><div class="date">{_esc(display_date)}</div></li>')
        return f'<section id="timeline"><h2>Completion Timeline</h2><ul class="timeline-list">{"".join(items)}</ul></section>'

    # -- 3.9 _render_health_section ----------------------------------------

    def _render_health_section(self, data: DashboardData) -> str:
        items = []
        for chk in data.health_checks:
            icon = "&#x2705;" if chk.exists else "&#x274C;"
            status_text = "exists" if chk.exists else "missing"
            items.append(f'<div class="health-item"><span class="icon">{icon}</span>{_esc(chk.label)} — {status_text}</div>')
        pct = data.health_score * 100 // data.health_total if data.health_total else 0
        score_line = f'<div class="health-score">Health Score: {data.health_score}/{data.health_total} ({pct}%)</div>'
        return f'<section id="health"><h2>Project Health</h2>{"".join(items)}{score_line}</section>'

    # -- 3.10 _render_footer + render orchestrator -------------------------

    def _render_footer(self, data: DashboardData) -> str:
        return f'<footer>Generated at {_esc(data.generated_at)}</footer>'

    def render(self, data: DashboardData) -> str:
        """Generate complete self-contained HTML dashboard string."""
        notice = ""
        if not data.has_progress_data:
            notice = '<div class="notice">No progress data found. Start the bootcamp to begin tracking progress.</div>'

        sections = [
            self._render_progress_bar(data),
            self._render_module_cards(data),
            self._render_quality_section(data.quality_scores),
            self._render_performance_section(data.performance),
            self._render_entity_section(data.entity_stats),
            self._render_timeline(data),
            self._render_health_section(data),
        ]
        body_content = "\n".join(s for s in sections if s)

        return (
            "<!DOCTYPE html>\n<html lang=\"en\">\n"
            + self._render_head() + "\n<body>\n"
            + self._render_header(data) + "\n"
            + "<main>\n" + notice + "\n" + body_content + "\n</main>\n"
            + self._render_footer(data) + "\n"
            + "<script>/* dashboard ready */</script>\n"
            + "</body>\n</html>"
        )


def _esc(text) -> str:
    """HTML-escape a string."""
    if text is None:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ---------------------------------------------------------------------------
# Task 4: CLI integration and file output
# ---------------------------------------------------------------------------

def generate_dashboard(output_path, no_open):
    """Orchestrate dashboard generation: collect data, render, write, open."""
    project_root = Path(__file__).resolve().parent.parent
    collector = DashboardDataCollector(str(project_root))
    try:
        data = collector.collect()
    except Exception as exc:
        print(f"Error collecting dashboard data: {exc}", file=sys.stderr)
        sys.exit(1)

    renderer = DashboardRenderer()
    html = renderer.render(data)

    out = Path(output_path) if output_path else project_root / "docs" / "dashboard.html"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
    except OSError as exc:
        print(f"Error writing dashboard: {exc}", file=sys.stderr)
        sys.exit(1)

    size_kb = out.stat().st_size / 1024
    print(f"Dashboard written to {out} ({size_kb:.1f} KB)")

    if not no_open:
        try:
            webbrowser.open(out.as_uri())
        except Exception:
            print(f"Could not open browser. Open manually: {out}")


def sync_progress_tracker(completed, current, language, current_step=None):
    """Generate PROGRESS_TRACKER.md from bootcamp_progress.json."""
    tracker_path = Path("docs") / "guides" / "PROGRESS_TRACKER.md"
    lines = ["# Senzing Bootcamp Progress Tracker\n"]
    lines.append("")
    lines.append("Auto-generated by `python scripts/status.py --sync`.")
    lines.append("Source of truth: `config/bootcamp_progress.json`.")
    lines.append("")

    total = 11
    pct = len(completed) * 100 // total
    bar_w = 26
    filled = pct * bar_w // 100
    bar = "█" * filled + "░" * (bar_w - filled)
    lines.append(f"Progress: [{bar}] {len(completed)}/{total}")
    lines.append("")

    for m in range(1, 12):
        name = MODULE_NAMES.get(m, "?")
        if m in completed:
            icon = "✅"
        elif m == current:
            icon = "🔄"
        else:
            icon = "⬜"
        line = f"- {icon} Module {m}: {name}"
        if m == current and m not in completed and isinstance(current_step, int) and current_step > 0:
            line += f" (Step {current_step})"
        lines.append(line)

    lines.append("")
    if language:
        lines.append(f"Language: {language}")
        lines.append("")

    tracker_path.parent.mkdir(parents=True, exist_ok=True)
    tracker_path.write_text("\n".join(lines), encoding="utf-8")
    print(green(f"✓ Synced progress to {tracker_path}"))


def _detect_team_mode():
    """Check for config/team.yaml and return (config, resolver) or (None, None)."""
    if not _TEAM_AVAILABLE:
        return None, None
    team_yaml = Path("config") / "team.yaml"
    if not team_yaml.is_file():
        return None, None
    try:
        config = _load_team_config(str(team_yaml))
        resolver = _PathResolver(config)
        return config, resolver
    except _TeamConfigError:
        return None, None


def _read_member_progress(progress_path):
    """Read a single member's progress JSON. Returns dict or None."""
    p = Path(str(progress_path))
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _show_member_status(member, data):
    """Display a single member's progress (used with --member)."""
    if data is None:
        print(yellow(f"⚠ No progress data for member '{member.id}'"))
        return
    completed = data.get("modules_completed", [])
    current = data.get("current_module", 1)
    language = data.get("language")
    current_step = data.get("current_step")
    total_modules = 11
    pct = len(completed) * 100 // total_modules

    module_display = f"Module {current}"
    if isinstance(current_step, int) and current_step > 0 and current not in completed:
        module_display += f", Step {current_step}"

    print(f"  {green('Member:')} {member.name} ({member.id})")
    print(f"  {green('Current Module:')} {module_display}")
    if language:
        print(f"  {green('Language:')} {language}")
    print(f"  {green('Progress:')} {len(completed)}/{total_modules} modules ({pct}%)")
    print()

    if completed:
        print(green("✓ Completed Modules:"))
        for m in sorted(completed):
            print(f"    ✓ Module {m}: {MODULE_NAMES.get(m, '?')}")
        print()


def _show_team_summary(config, resolver):
    """Display team summary: each member's status + overall stats."""
    print(cyan(f"Team: {config.team_name}"))
    print(f"  Members: {len(config.members)}")
    print()

    all_completed_counts = []
    for member in config.members:
        p = resolver.progress_path(member)
        data = _read_member_progress(p)
        if data is None:
            print(f"  {member.name} ({member.id}): {yellow('No data available')}")
            all_completed_counts.append(0)
        else:
            completed = data.get("modules_completed", [])
            current = data.get("current_module", 1)
            pct = len(completed) * 100 // 11
            print(
                f"  {member.name} ({member.id}): "
                f"Module {current}, {len(completed)}/11 ({pct}%)"
            )
            all_completed_counts.append(len(completed))

    print()
    total = sum(all_completed_counts)
    avg = sum(c / 11 * 100 for c in all_completed_counts) / len(all_completed_counts) if all_completed_counts else 0
    fully = sum(1 for c in all_completed_counts if c >= 11)
    print(cyan("Team Statistics:"))
    print(f"  Total modules completed: {total}")
    print(f"  Average completion: {avg:.0f}%")
    print(f"  Fully completed members: {fully}")
    print()


def _show_terminal_status(args):
    """Original terminal output logic, extracted from main for clarity."""
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    print(blue("╔════════════════════════════════════════════════════════════╗"))
    print(blue("║") + "  " + cyan("Senzing Bootcamp - Project Status") + "                     " + blue("║"))
    print(blue("╚════════════════════════════════════════════════════════════╝"))
    print()

    # ── Team mode handling ──
    team_config, team_resolver = _detect_team_mode()
    if team_config is not None:
        member_arg = getattr(args, "member", None)
        if member_arg:
            member = None
            for m in team_config.members:
                if m.id == member_arg:
                    member = m
                    break
            if member is None:
                print(yellow(f"⚠ Member '{member_arg}' not found in team config"))
                ids = ", ".join(m.id for m in team_config.members)
                print(f"  Available members: {ids}")
                sys.exit(1)
            p = team_resolver.progress_path(member)
            data = _read_member_progress(p)
            _show_member_status(member, data)
            return
        else:
            _show_team_summary(team_config, team_resolver)
            return

    progress_json = Path("config") / "bootcamp_progress.json"
    progress_md = Path("docs") / "guides" / "PROGRESS_TRACKER.md"

    completed = []
    in_progress = None
    current = 1
    status = "Not Started"
    language = None
    current_step = None

    if progress_json.is_file():
        try:
            data = json.loads(progress_json.read_text(encoding="utf-8"))
            completed = data.get("modules_completed", [])
            current = data.get("current_module", 1)
            language = data.get("language")
            current_step = data.get("current_step")
            if completed:
                last = max(completed)
                if current > last:
                    status = "Ready to Start"
                elif current in completed:
                    status = "Complete" if last >= 11 else "Ready to Start"
                else:
                    status = "In Progress"
        except (json.JSONDecodeError, KeyError):
            pass
    elif progress_md.is_file():
        checked_re = re.compile(r"\[x\].*Module\s+(\d+)", re.IGNORECASE)
        unchecked_re = re.compile(r"\[\s\].*Module\s+(\d+)", re.IGNORECASE)
        for line in progress_md.read_text(encoding="utf-8").splitlines():
            m = checked_re.search(line)
            if m:
                completed.append(int(m.group(1)))
                continue
            m = unchecked_re.search(line)
            if m and in_progress is None:
                in_progress = int(m.group(1))
        if not completed:
            current = 1
            status = "Not Started"
        elif in_progress is not None:
            current = in_progress
            status = "In Progress"
        else:
            last = max(completed)
            current = min(last + 1, 11)
            status = "Complete" if last >= 11 else "Ready to Start"
    else:
        print(yellow("⚠ No progress data found"))
        print("Start the bootcamp to begin tracking progress.")
        print()

    total_modules = 11
    pct = len(completed) * 100 // total_modules

    module_display = f"Module {current}"
    if isinstance(current_step, int) and current_step > 0 and current not in completed:
        module_display += f", Step {current_step}"
    print(f"  {green('Current Module:')} {module_display}")
    print(f"  {green('Status:')} {status}")
    if language:
        print(f"  {green('Language:')} {language}")
    print(f"  {green('Progress:')} {len(completed)}/{total_modules} modules ({pct}%)")
    print()

    bar_w = 50
    filled = pct * bar_w // 100
    bar = "█" * filled + "░" * (bar_w - filled)
    print(f"  {green('[')}{bar}{green(']')} {pct}%")
    print()

    if completed:
        print(green("✓ Completed Modules:"))
        for m in sorted(completed):
            print(f"    ✓ Module {m}: {MODULE_NAMES.get(m, '?')}")
        print(f"  Tip: Use {yellow('python scripts/rollback_module.py --module N')} to undo a module")
        print()

    if current <= 11 and status != "Complete":
        print(cyan("→ Next Steps:"))
        step = NEXT_STEPS.get(current)
        if step:
            print(f"    1. {step[0]}")
            print(f"    2. {step[1]}")
            print(f"    3. Tell agent 'Start Module {current}'")
        print()
    else:
        print(green("🎉 Bootcamp Complete!"))
        print()

    print(cyan("Project Health:"))
    health = 0
    checks = [
        (os.path.join("data", "raw"), "Data directory"),
        ("database", "Database directory"),
        ("src", "Source directory"),
        ("scripts", "Scripts directory"),
        (".gitignore", ".gitignore"),
        (".env.example", ".env.example"),
        ("README.md", "README.md"),
        ("backups", "Backups directory"),
    ]
    for path, label in checks:
        exists = os.path.exists(path)
        mark = "✓" if exists else "✗"
        print(f"    {mark} {label} {'exists' if exists else 'missing'}")
        if exists:
            health += 1

    health_pct = health * 100 // len(checks)
    print()
    print(f"  {green('Health Score:')} {health}/{len(checks)} ({health_pct}%)")
    print()

    # ── Data Sources section (if registry exists) ──
    try:
        from data_sources import render_data_sources_section
    except ImportError:
        try:
            from scripts.data_sources import render_data_sources_section
        except ImportError:
            render_data_sources_section = None

    if render_data_sources_section is not None:
        ds_section = render_data_sources_section()
        if ds_section is not None:
            print(cyan(ds_section.splitlines()[0]))
            for line in ds_section.splitlines()[1:]:
                print(line)
            print()

    print(cyan("Quick Commands:"))
    print("    python scripts/status.py              # Show this status")
    print("    python scripts/status.py --html       # Generate HTML dashboard")
    print("    python scripts/status.py --sync       # Sync progress tracker")
    print("    python scripts/backup_project.py      # Backup project")
    print("    Tell agent 'resume bootcamp'           # Resume bootcamp")
    print()

    if args.sync:
        sync_progress_tracker(completed, current, language, current_step=current_step)


def main():
    parser = argparse.ArgumentParser(description="Senzing Bootcamp - Project Status",
                                     epilog="See Also: analyze_sessions.py (historical analytics),"
                                            " preflight.py (environment checks)")
    parser.add_argument("--html", action="store_true", help="Generate HTML dashboard")
    parser.add_argument("--output", type=str, default=None,
                        help="Dashboard output path (default: docs/dashboard.html)")
    parser.add_argument("--no-open", action="store_true",
                        help="Don't auto-open dashboard in browser")
    parser.add_argument("--sync", action="store_true", help="Sync progress tracker")
    parser.add_argument("--member", type=str, default=None,
                        help="Show specific team member status")
    parser.add_argument("--graph", action="store_true", help="Show module dependency graph")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    if args.html:
        generate_dashboard(args.output, args.no_open)
    elif args.graph:
        try:
            from visualize_dependencies import (
                load_modules, load_progress, load_tracks, load_preferences, render_text,
            )
        except ImportError:
            from scripts.visualize_dependencies import (
                load_modules, load_progress, load_tracks, load_preferences, render_text,
            )
        modules = load_modules()
        progress = load_progress()
        tracks = load_tracks()
        preferences = load_preferences()
        print(render_text(modules, progress, tracks, preferences))
    else:
        _show_terminal_status(args)


if __name__ == "__main__":
    main()
