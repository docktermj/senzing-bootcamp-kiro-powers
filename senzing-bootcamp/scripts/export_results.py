#!/usr/bin/env python3
"""Senzing Bootcamp - Export Results.

Bundles bootcamp artifacts into a self-contained HTML report or ZIP archive.
Cross-platform: works on Linux, macOS, and Windows.
Depends only on the Python standard library.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import fnmatch
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_ARTIFACT_TYPES = frozenset({
    "journal", "progress", "quality_report", "performance_report",
    "entity_stats", "visualization", "source_code",
    "transformed_data", "raw_data", "documentation",
})

MODULE_NAMES = {
    1: "Business Problem", 2: "SDK Setup", 3: "Quick Demo",
    4: "Data Collection", 5: "Data Quality & Mapping",
    6: "Single Source Loading", 7: "Multi-Source Orchestration",
    8: "Query, Visualize & Validate", 9: "Performance Testing",
    10: "Security Hardening", 11: "Monitoring", 12: "Deployment",
}

LANG_EXTENSIONS: dict[str, list[str]] = {
    "python": [".py"], "java": [".java"], "csharp": [".cs"],
    "rust": [".rs"], "typescript": [".ts"], "javascript": [".js"],
}

SUBDIR_MODULE: dict[str, int] = {
    "quickstart_demo": 3, "transform": 5, "load": 6, "query": 8,
    "performance": 9, "security": 10, "monitoring": 11, "deploy": 12,
}

VIZ_MARKERS = re.compile(r"\b(d3|force|graph|dashboard|entity|svg)\b", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Data Models  (Tasks 1.1 – 1.3)
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class ArtifactEntry:
    """A single discovered artifact."""
    path: str
    artifact_type: str
    module: int | None
    file_size: int
    description: str


@dataclasses.dataclass
class ArtifactManifest:
    """Catalog of all discovered artifacts."""
    artifacts: list[ArtifactEntry]
    scan_timestamp: str  # ISO 8601 UTC

    def by_type(self, artifact_type: str) -> list[ArtifactEntry]:
        return [a for a in self.artifacts if a.artifact_type == artifact_type]

    def by_module(self, module: int) -> list[ArtifactEntry]:
        return [a for a in self.artifacts if a.module == module]

    def total_size(self) -> int:
        return sum(a.file_size for a in self.artifacts)

    def type_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for a in self.artifacts:
            counts[a.artifact_type] = counts.get(a.artifact_type, 0) + 1
        return counts

    def is_empty(self) -> bool:
        return len(self.artifacts) == 0


@dataclasses.dataclass
class QualityScore:
    """Data quality score for a single source."""
    source_name: str
    overall: float  # 0-100
    completeness: float | None = None
    consistency: float | None = None
    format_compliance: float | None = None
    uniqueness: float | None = None

    @property
    def band(self) -> str:
        if self.overall >= 80:
            return "green"
        if self.overall >= 70:
            return "yellow"
        return "red"


@dataclasses.dataclass
class PerformanceMetrics:
    loading_throughput_rps: float | None = None
    query_response_ms: float | None = None
    database_type: str | None = None


@dataclasses.dataclass
class EntityStatistics:
    total_records: int | None = None
    total_entities: int | None = None
    match_count: int | None = None
    cross_source_matches: int | None = None
    duplicate_count: int | None = None


@dataclasses.dataclass
class ExportMetrics:
    quality_scores: list[QualityScore]
    performance: PerformanceMetrics | None = None
    entity_stats: EntityStatistics | None = None


@dataclasses.dataclass
class ProgressData:
    modules_completed: list[int]
    current_module: int | None = None
    language: str | None = None
    data_sources: list[str] = dataclasses.field(default_factory=list)
    track: str | None = None


# ---------------------------------------------------------------------------
# Module Filter  (Task 1.4)
# ---------------------------------------------------------------------------

class ModuleFilter:
    @staticmethod
    def validate_modules(modules: list[int]) -> tuple[list[int], list[int]]:
        """Partition *modules* into (valid, invalid). Valid means 1–12."""
        valid = [m for m in modules if 1 <= m <= 12]
        invalid = [m for m in modules if not (1 <= m <= 12)]
        return valid, invalid

    @staticmethod
    def filter(manifest: ArtifactManifest, modules: list[int] | None) -> ArtifactManifest:
        """Return manifest restricted to *modules*. module=None artifacts always kept."""
        if modules is None:
            return manifest
        keep = set(modules)
        filtered = [a for a in manifest.artifacts if a.module is None or a.module in keep]
        return ArtifactManifest(artifacts=filtered, scan_timestamp=manifest.scan_timestamp)


# ---------------------------------------------------------------------------
# Artifact Discovery  (Tasks 2.1 – 2.6)
# ---------------------------------------------------------------------------

class ArtifactDiscovery:
    def __init__(self, project_root: str):
        self.root = Path(project_root)

    def scan(self) -> ArtifactManifest:
        """Scan project directory and return manifest of all discovered artifacts."""
        entries: list[ArtifactEntry] = []
        journal = self._scan_journal()
        if journal:
            entries.append(journal)
        progress = self._scan_progress()
        if progress:
            entries.append(progress)
        entries.extend(self._scan_data_files())
        entries.extend(self._scan_visualizations())
        # Determine language from progress data
        lang = self._read_language()
        entries.extend(self._scan_source_code(lang))
        entries.extend(self._scan_docs())
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return ArtifactManifest(artifacts=entries, scan_timestamp=ts)

    # -- helpers --

    def _safe_size(self, p: Path) -> int:
        try:
            return p.stat().st_size
        except OSError:
            return 0

    def _read_language(self) -> str | None:
        pf = self.root / "config" / "bootcamp_progress.json"
        if pf.is_file():
            try:
                data = json.loads(pf.read_text(encoding="utf-8"))
                return data.get("language")
            except (json.JSONDecodeError, OSError):
                pass
        return None

    # -- scanners --

    def _scan_journal(self) -> ArtifactEntry | None:
        p = self.root / "docs" / "bootcamp_journal.md"
        if p.is_file():
            return ArtifactEntry(
                path=str(p.relative_to(self.root)),
                artifact_type="journal", module=None,
                file_size=self._safe_size(p),
                description="Bootcamp journal with per-module entries",
            )
        return None

    def _scan_progress(self) -> ArtifactEntry | None:
        p = self.root / "config" / "bootcamp_progress.json"
        if p.is_file():
            return ArtifactEntry(
                path=str(p.relative_to(self.root)),
                artifact_type="progress", module=None,
                file_size=self._safe_size(p),
                description="Bootcamp progress tracking data",
            )
        return None

    def _scan_data_files(self) -> list[ArtifactEntry]:
        entries: list[ArtifactEntry] = []
        transformed = self.root / "data" / "transformed"
        if transformed.is_dir():
            for f in sorted(transformed.iterdir()):
                if f.is_file() and f.suffix == ".jsonl":
                    entries.append(ArtifactEntry(
                        path=str(f.relative_to(self.root)),
                        artifact_type="transformed_data", module=5,
                        file_size=self._safe_size(f),
                        description=f"Transformed data file: {f.name}",
                    ))
        raw = self.root / "data" / "raw"
        if raw.is_dir():
            for f in sorted(raw.iterdir()):
                if f.is_file():
                    entries.append(ArtifactEntry(
                        path=str(f.relative_to(self.root)),
                        artifact_type="raw_data", module=4,
                        file_size=self._safe_size(f),
                        description=f"Raw data file: {f.name}",
                    ))
        return entries

    def _scan_visualizations(self) -> list[ArtifactEntry]:
        entries: list[ArtifactEntry] = []
        for dirpath, _dirs, files in os.walk(self.root):
            dp = Path(dirpath)
            # Skip hidden dirs and common noise
            rel = dp.relative_to(self.root)
            parts = rel.parts
            if any(p.startswith(".") or p in ("node_modules", "__pycache__", "database") for p in parts):
                continue
            for fname in sorted(files):
                if not fname.lower().endswith(".html"):
                    continue
                fp = dp / fname
                try:
                    content = fp.read_text(encoding="utf-8", errors="ignore")[:8192]
                except OSError:
                    continue
                if VIZ_MARKERS.search(content):
                    entries.append(ArtifactEntry(
                        path=str(fp.relative_to(self.root)),
                        artifact_type="visualization", module=8,
                        file_size=self._safe_size(fp),
                        description=f"Visualization: {fname}",
                    ))
        return entries

    def _scan_source_code(self, language: str | None) -> list[ArtifactEntry]:
        entries: list[ArtifactEntry] = []
        src = self.root / "src"
        if not src.is_dir():
            return entries
        exts = set()
        if language and language.lower() in LANG_EXTENSIONS:
            exts = set(LANG_EXTENSIONS[language.lower()])
        else:
            for ext_list in LANG_EXTENSIONS.values():
                exts.update(ext_list)
        for dirpath, _dirs, files in os.walk(src):
            dp = Path(dirpath)
            rel_to_src = dp.relative_to(src)
            first_dir = rel_to_src.parts[0] if rel_to_src.parts else None
            mod = SUBDIR_MODULE.get(first_dir) if first_dir else None
            for fname in sorted(files):
                fp = dp / fname
                if fp.suffix in exts and fp.is_file():
                    entries.append(ArtifactEntry(
                        path=str(fp.relative_to(self.root)),
                        artifact_type="source_code", module=mod,
                        file_size=self._safe_size(fp),
                        description=f"Source code: {fname}",
                    ))
        # Also check tests/performance for module 9
        perf_dir = self.root / "tests" / "performance"
        if perf_dir.is_dir():
            for dirpath, _dirs, files in os.walk(perf_dir):
                dp = Path(dirpath)
                for fname in sorted(files):
                    fp = dp / fname
                    if fp.suffix in exts and fp.is_file():
                        entries.append(ArtifactEntry(
                            path=str(fp.relative_to(self.root)),
                            artifact_type="source_code", module=9,
                            file_size=self._safe_size(fp),
                            description=f"Source code: {fname}",
                        ))
        return entries

    def _scan_docs(self) -> list[ArtifactEntry]:
        entries: list[ArtifactEntry] = []
        docs = self.root / "docs"
        if not docs.is_dir():
            return entries
        for f in sorted(docs.iterdir()):
            if not f.is_file() or f.suffix != ".md":
                continue
            name_lower = f.name.lower()
            # Skip journal — handled separately
            if name_lower == "bootcamp_journal.md":
                continue
            if "quality" in name_lower or name_lower == "data_source_evaluation.md":
                atype, mod = "quality_report", 5
            elif "performance" in name_lower:
                atype, mod = "performance_report", 9
            elif "entity" in name_lower or "resolution" in name_lower or "results_validation" in name_lower:
                atype, mod = "entity_stats", 8
            else:
                atype, mod = "documentation", None
            entries.append(ArtifactEntry(
                path=str(f.relative_to(self.root)),
                artifact_type=atype, module=mod,
                file_size=self._safe_size(f),
                description=f"Documentation: {f.name}",
            ))
        return entries


# ---------------------------------------------------------------------------
# Metrics Extraction  (Tasks 3.1 – 3.3)
# ---------------------------------------------------------------------------

class MetricsExtractor:
    _NUM = re.compile(r"[\d,]+\.?\d*")

    @staticmethod
    def _first_number(text: str) -> float | None:
        m = MetricsExtractor._NUM.search(text)
        if m:
            try:
                return float(m.group().replace(",", ""))
            except ValueError:
                pass
        return None

    @staticmethod
    def extract_quality_scores(
        doc_artifacts: list[ArtifactEntry],
        file_reader: Callable[[str], str],
    ) -> list[QualityScore]:
        scores: list[QualityScore] = []
        for art in doc_artifacts:
            if art.artifact_type != "quality_report":
                continue
            try:
                content = file_reader(art.path)
            except (OSError, IOError):
                continue
            overall = None
            completeness = consistency = fmt = uniqueness = None
            source_name = Path(art.path).stem.replace("_", " ").title()
            for line in content.splitlines():
                ll = line.lower()
                val = MetricsExtractor._first_number(line)
                if val is None:
                    continue
                if "overall" in ll or "total score" in ll or "quality score" in ll:
                    overall = val
                elif "completeness" in ll:
                    completeness = val
                elif "consistency" in ll:
                    consistency = val
                elif "format" in ll and "compliance" in ll:
                    fmt = val
                elif "uniqueness" in ll:
                    uniqueness = val
            if overall is not None:
                scores.append(QualityScore(
                    source_name=source_name, overall=overall,
                    completeness=completeness, consistency=consistency,
                    format_compliance=fmt, uniqueness=uniqueness,
                ))
        return scores

    @staticmethod
    def extract_performance(
        artifacts: list[ArtifactEntry],
        file_reader: Callable[[str], str],
    ) -> PerformanceMetrics | None:
        throughput = query_ms = db_type = None
        for art in artifacts:
            if art.artifact_type != "performance_report":
                continue
            try:
                content = file_reader(art.path)
            except (OSError, IOError):
                continue
            for line in content.splitlines():
                ll = line.lower()
                val = MetricsExtractor._first_number(line)
                if "throughput" in ll or "records per second" in ll or "rps" in ll:
                    if val is not None:
                        throughput = val
                elif "query" in ll and ("response" in ll or "time" in ll or "ms" in ll):
                    if val is not None:
                        query_ms = val
                elif "database" in ll or "db type" in ll:
                    if "sqlite" in ll:
                        db_type = "sqlite"
                    elif "postgresql" in ll or "postgres" in ll:
                        db_type = "postgresql"
        if throughput is not None or query_ms is not None or db_type is not None:
            return PerformanceMetrics(throughput, query_ms, db_type)
        return None

    @staticmethod
    def extract_entity_stats(
        artifacts: list[ArtifactEntry],
        file_reader: Callable[[str], str],
    ) -> EntityStatistics | None:
        total_records = total_entities = match_count = None
        cross_source = duplicate_count = None
        for art in artifacts:
            if art.artifact_type != "entity_stats":
                continue
            try:
                content = file_reader(art.path)
            except (OSError, IOError):
                continue
            for line in content.splitlines():
                ll = line.lower()
                val = MetricsExtractor._first_number(line)
                if val is None:
                    continue
                ival = int(val)
                if "total record" in ll:
                    total_records = ival
                elif "total entit" in ll:
                    total_entities = ival
                elif "cross" in ll and "source" in ll:
                    cross_source = ival
                elif "match" in ll and "cross" not in ll:
                    match_count = ival
                elif "duplicate" in ll:
                    duplicate_count = ival
        if any(v is not None for v in (total_records, total_entities, match_count, cross_source, duplicate_count)):
            return EntityStatistics(total_records, total_entities, match_count, cross_source, duplicate_count)
        return None


# ---------------------------------------------------------------------------
# Summary Generator  (Task 4.3)
# ---------------------------------------------------------------------------

class SummaryGenerator:
    @staticmethod
    def generate(progress: ProgressData, metrics: ExportMetrics, manifest: ArtifactManifest) -> str:
        parts: list[str] = []
        # Track and module count
        n = len(progress.modules_completed)
        track_str = f"Track {progress.track}" if progress.track else "the bootcamp"
        parts.append(f"This report summarises work completed during {track_str}.")
        parts.append(f"{n} of 12 modules have been completed.")
        # Quality bands
        for qs in metrics.quality_scores:
            band_word = {"green": "high", "yellow": "moderate", "red": "low"}.get(qs.band, qs.band)
            parts.append(
                f"Data quality for <em>{qs.source_name}</em> is rated "
                f"<strong>{band_word}</strong> (score&nbsp;{qs.overall:.0f}/100)."
            )
        # Entity stats
        if metrics.entity_stats:
            es = metrics.entity_stats
            if es.total_records is not None and es.total_entities is not None:
                parts.append(
                    f"{es.total_records:,} records were processed and resolved into "
                    f"{es.total_entities:,} unique entities (groups of records that refer "
                    f"to the same real-world object)."
                )
        # Artifact summary
        tc = manifest.type_counts()
        if tc:
            items = ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in sorted(tc.items()))
            parts.append(f"Key artifacts produced: {items}.")
        return "<p>" + "</p>\n<p>".join(parts) + "</p>"


# ---------------------------------------------------------------------------
# HTML Renderer  (Tasks 4.1 – 4.7)
# ---------------------------------------------------------------------------

BAND_COLORS = {"green": "#2d8a4e", "yellow": "#b08800", "red": "#cf222e"}


class HTMLRenderer:
    VERSION = "1.0.0"

    def render(
        self,
        progress: ProgressData,
        metrics: ExportMetrics,
        manifest: ArtifactManifest,
        journal_html: str | None,
        modules_filter: list[int] | None,
    ) -> str:
        sections: list[tuple[str, str, str]] = []  # (id, title, html)
        # Executive summary — always present
        summary_html = SummaryGenerator.generate(progress, metrics, manifest)
        sections.append(("executive-summary", "Executive Summary", summary_html))
        # Module table — always present
        sections.append(("module-completion", "Module Completion", self._render_module_table(progress)))
        # Conditional sections
        if metrics.quality_scores:
            sections.append(("quality-scores", "Quality Scores", self._render_quality_section(metrics.quality_scores)))
        if metrics.performance:
            sections.append(("performance", "Performance Metrics", self._render_performance_section(metrics.performance)))
        if metrics.entity_stats:
            sections.append(("entity-stats", "Entity Resolution Statistics", self._render_entity_stats_section(metrics.entity_stats)))
        if journal_html:
            sections.append(("journal", "Bootcamp Journal", self._render_journal_section(journal_html)))
        # Achievements (module completion certificates)
        achievements_html = self._render_achievements_section()
        if achievements_html:
            sections.append(("achievements", "Achievements", achievements_html))
        viz = manifest.by_type("visualization")
        if viz:
            sections.append(("visualizations", "Visualizations", self._render_visualizations_section(viz)))

        head = self._render_head()
        toc = self._render_toc([(sid, title) for sid, title, _ in sections])
        filter_note = ""
        if modules_filter:
            filter_note = f'<p class="filter-note">Filtered to modules: {", ".join(str(m) for m in sorted(modules_filter))}</p>'
        body_parts = [f'<section id="{sid}"><h2>{title}</h2>\n{html}\n</section>' for sid, title, html in sections]
        footer = self._render_footer()
        return (
            "<!DOCTYPE html>\n<html lang=\"en\">\n" + head
            + "<body>\n<header><h1>Senzing Bootcamp Report</h1>\n" + filter_note + "</header>\n"
            + "<nav>\n" + toc + "\n</nav>\n"
            + "<main>\n" + "\n".join(body_parts) + "\n</main>\n"
            + footer
            + "\n</body>\n</html>"
        )

    # -- section helpers --

    def _render_head(self) -> str:
        return (
            "<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            "<title>Senzing Bootcamp Report</title>\n"
            "<style>\n"
            "body{font-family:system-ui,sans-serif;max-width:960px;margin:0 auto;padding:1rem;color:#24292f;line-height:1.6}\n"
            "h1{border-bottom:2px solid #d0d7de;padding-bottom:.3em}\n"
            "h2{border-bottom:1px solid #d0d7de;padding-bottom:.2em}\n"
            "table{border-collapse:collapse;width:100%}\n"
            "th,td{border:1px solid #d0d7de;padding:.4em .8em;text-align:left}\n"
            "th{background:#f6f8fa}\n"
            "nav{background:#f6f8fa;padding:.8em;border-radius:6px;margin-bottom:1.5em}\n"
            "nav ul{list-style:none;padding:0;margin:0}\n"
            "nav li{display:inline;margin-right:1em}\n"
            "a{color:#0969da;text-decoration:none}\n"
            "a:hover{text-decoration:underline}\n"
            ".band-green{color:#2d8a4e}.band-yellow{color:#b08800}.band-red{color:#cf222e}\n"
            ".filter-note{background:#fff8c5;padding:.5em;border-radius:4px}\n"
            "footer{margin-top:2em;padding-top:1em;border-top:1px solid #d0d7de;font-size:.85em;color:#656d76}\n"
            "@media print{nav{display:none}body{max-width:100%}}\n"
            "</style>\n</head>\n"
        )

    def _render_toc(self, sections: list[tuple[str, str]]) -> str:
        items = "".join(f'<li><a href="#{sid}">{title}</a></li>' for sid, title in sections)
        return f"<ul>{items}</ul>"

    def _render_module_table(self, progress: ProgressData) -> str:
        n = len(progress.modules_completed)
        pct = n * 100 / 12 if True else 0
        rows = ""
        for m in range(1, 13):
            name = MODULE_NAMES.get(m, f"Module {m}")
            if m in progress.modules_completed:
                status = "✅ Completed"
            elif m == progress.current_module and m not in progress.modules_completed:
                status = "🔄 In Progress"
            else:
                status = "⬜ Not Started"
            rows += f"<tr><td>{m}</td><td>{name}</td><td>{status}</td></tr>\n"
        lang_row = f"<p>Language: <strong>{progress.language}</strong></p>" if progress.language else ""
        return (
            f"<p>Progress: <strong>{n}/12 ({pct:.0f}%)</strong></p>\n"
            + lang_row
            + "<table><thead><tr><th>#</th><th>Module</th><th>Status</th></tr></thead>\n<tbody>\n"
            + rows + "</tbody></table>"
        )

    def _render_quality_section(self, scores: list[QualityScore]) -> str:
        rows = ""
        for qs in scores:
            color = BAND_COLORS.get(qs.band, "#24292f")
            rows += (
                f"<tr><td>{qs.source_name}</td>"
                f"<td style=\"color:{color};font-weight:bold\">{qs.overall:.0f}</td>"
                f"<td>{qs.completeness if qs.completeness is not None else '—'}</td>"
                f"<td>{qs.consistency if qs.consistency is not None else '—'}</td>"
                f"<td>{qs.format_compliance if qs.format_compliance is not None else '—'}</td>"
                f"<td>{qs.uniqueness if qs.uniqueness is not None else '—'}</td></tr>\n"
            )
        return (
            "<table><thead><tr><th>Source</th><th>Overall</th><th>Completeness</th>"
            "<th>Consistency</th><th>Format</th><th>Uniqueness</th></tr></thead>\n<tbody>\n"
            + rows + "</tbody></table>"
        )

    def _render_performance_section(self, perf: PerformanceMetrics) -> str:
        items: list[str] = []
        if perf.loading_throughput_rps is not None:
            items.append(f"<li>Loading throughput: <strong>{perf.loading_throughput_rps:,.1f}</strong> records/sec</li>")
        if perf.query_response_ms is not None:
            items.append(f"<li>Avg query response: <strong>{perf.query_response_ms:,.1f}</strong> ms</li>")
        if perf.database_type:
            items.append(f"<li>Database: <strong>{perf.database_type}</strong></li>")
        return "<ul>\n" + "\n".join(items) + "\n</ul>"

    def _render_entity_stats_section(self, stats: EntityStatistics) -> str:
        items: list[str] = []
        if stats.total_records is not None:
            items.append(f"<li>Total records loaded: <strong>{stats.total_records:,}</strong></li>")
        if stats.total_entities is not None:
            items.append(f"<li>Total entities resolved: <strong>{stats.total_entities:,}</strong></li>")
        if stats.match_count is not None:
            items.append(f"<li>Match count: <strong>{stats.match_count:,}</strong></li>")
        if stats.cross_source_matches is not None:
            items.append(f"<li>Cross-source matches: <strong>{stats.cross_source_matches:,}</strong></li>")
        if stats.duplicate_count is not None:
            items.append(f"<li>Duplicates: <strong>{stats.duplicate_count:,}</strong></li>")
        return "<ul>\n" + "\n".join(items) + "\n</ul>"

    def _render_journal_section(self, journal_html: str) -> str:
        return f"<div class=\"journal\">{journal_html}</div>"

    def _render_achievements_section(self) -> str | None:
        """Render module completion certificates if docs/progress/ exists."""
        progress_dir = Path("docs/progress")
        if not progress_dir.is_dir():
            return None
        certs = sorted(progress_dir.glob("MODULE_*_COMPLETE.md"))
        if not certs:
            return None
        items: list[str] = []
        for cert in certs:
            try:
                content = cert.read_text(encoding="utf-8")
                # Extract the first heading as the title
                first_line = content.strip().splitlines()[0] if content.strip() else cert.name
                title = first_line.lstrip("# ").strip()
                items.append(f"<li><strong>{title}</strong></li>")
            except OSError:
                continue
        if not items:
            return None
        return "<ul>\n" + "\n".join(items) + "\n</ul>"

    def _render_visualizations_section(self, viz_artifacts: list[ArtifactEntry]) -> str:
        items = "".join(
            f"<li><strong>{Path(a.path).name}</strong> — {a.description}</li>" for a in viz_artifacts
        )
        return f"<ul>{items}</ul>"

    def _render_footer(self) -> str:
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        return f"<footer>Generated on {ts} by export_results.py v{self.VERSION}</footer>"


# ---------------------------------------------------------------------------
# ZIP Assembly  (Tasks 5.1 – 5.3)
# ---------------------------------------------------------------------------

class ZIPAssembler:
    EXCLUDE_PATTERNS = ["__pycache__", "*.pyc", ".env", ".git", "node_modules", "database/"]

    TYPE_TO_DIR: dict[str, str] = {
        "visualization": "artifacts/visualizations",
        "transformed_data": "artifacts/data",
        "raw_data": "artifacts/data",
        "source_code": "artifacts/source",
        "documentation": "artifacts/docs",
        "quality_report": "artifacts/docs",
        "performance_report": "artifacts/docs",
        "entity_stats": "artifacts/docs",
        "journal": "artifacts/docs",
        "progress": "artifacts/docs",
    }

    @staticmethod
    def should_exclude(path: str) -> bool:
        """Check if *path* matches any exclusion pattern."""
        parts = Path(path).parts
        for part in parts:
            if part == "__pycache__" or part == ".git" or part == "node_modules" or part == ".env":
                return True
            if part.startswith("database"):
                return True
            if fnmatch.fnmatch(part, "*.pyc"):
                return True
        return False

    @staticmethod
    def build_manifest_json(manifest: ArtifactManifest) -> str:
        """Serialize manifest to JSON for inclusion in ZIP."""
        entries = []
        for a in manifest.artifacts:
            dest_dir = ZIPAssembler.TYPE_TO_DIR.get(a.artifact_type, "artifacts/other")
            entries.append({
                "path": dest_dir + "/" + Path(a.path).name,
                "original_path": a.path,
                "artifact_type": a.artifact_type,
                "module": a.module,
                "file_size": a.file_size,
            })
        obj = {
            "generated_at": manifest.scan_timestamp,
            "version": HTMLRenderer.VERSION,
            "artifact_count": len(entries),
            "total_size_bytes": manifest.total_size(),
            "artifacts": entries,
        }
        return json.dumps(obj, indent=2)

    def assemble(
        self,
        html_content: str,
        manifest: ArtifactManifest,
        output_path: str,
        file_reader: Callable[[str], bytes],
    ) -> int:
        """Create ZIP archive. Returns total archive size in bytes."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("bootcamp_report.html", html_content)
            zf.writestr("manifest.json", self.build_manifest_json(manifest))
            for art in manifest.artifacts:
                if self.should_exclude(art.path):
                    continue
                dest_dir = self.TYPE_TO_DIR.get(art.artifact_type, "artifacts/other")
                arc_name = dest_dir + "/" + Path(art.path).name
                try:
                    data = file_reader(art.path)
                    zf.writestr(arc_name, data)
                except (OSError, IOError):
                    continue
            # Include module completion certificates if they exist
            progress_dir = Path("docs/progress")
            if progress_dir.is_dir():
                for cert_file in sorted(progress_dir.glob("*.md")):
                    try:
                        data = cert_file.read_bytes()
                        zf.writestr(
                            f"artifacts/progress/{cert_file.name}", data
                        )
                    except (OSError, IOError):
                        continue
        archive_bytes = buf.getvalue()
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(archive_bytes)
        return len(archive_bytes)


# ---------------------------------------------------------------------------
# Journal Markdown → HTML (minimal converter)
# ---------------------------------------------------------------------------

def _md_to_html(md: str) -> str:
    """Very basic markdown-to-HTML for journal content."""
    lines = md.splitlines()
    out: list[str] = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        # Headings
        hm = re.match(r"^(#{1,6})\s+(.*)", stripped)
        if hm:
            if in_list:
                out.append("</ul>")
                in_list = False
            level = len(hm.group(1))
            out.append(f"<h{level}>{hm.group(2)}</h{level}>")
            continue
        # List items
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{stripped[2:]}</li>")
            continue
        # Close list if needed
        if in_list and not stripped:
            out.append("</ul>")
            in_list = False
        # Bold / italic
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", stripped)
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        if text:
            out.append(f"<p>{text}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI Entry Point  (Tasks 6.1 – 6.3)
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export Senzing Bootcamp results as HTML report or ZIP archive.",
    )
    parser.add_argument(
        "--format", choices=["html", "zip"], default="html",
        help="Output format (default: html)",
    )
    parser.add_argument(
        "--modules", type=str, default=None,
        help="Comma-separated module numbers to include (e.g. 1,2,3)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output file path (default: exports/bootcamp_report_{timestamp}.{ext})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Parse args, discover artifacts, generate report, return exit code."""
    args = _parse_args(argv)

    # Determine project root (parent of scripts/)
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    # Parse --modules
    modules_filter: list[int] | None = None
    if args.modules:
        try:
            raw = [int(x.strip()) for x in args.modules.split(",") if x.strip()]
        except ValueError:
            print("Error: --modules must be comma-separated integers.", file=sys.stderr)
            return 1
        valid, invalid = ModuleFilter.validate_modules(raw)
        for inv in invalid:
            print(f"Warning: ignoring invalid module number {inv} (must be 1-12).", file=sys.stderr)
        if valid:
            modules_filter = valid
        else:
            print("Warning: no valid module numbers provided, including all modules.", file=sys.stderr)

    # Discover artifacts
    print("Scanning for bootcamp artifacts...")
    discovery = ArtifactDiscovery(str(project_root))
    manifest = discovery.scan()

    tc = manifest.type_counts()
    for atype, count in sorted(tc.items()):
        print(f"  Found {count} {atype.replace('_', ' ')} file(s)")

    if manifest.is_empty():
        print("Warning: no artifacts found. Nothing to export.", file=sys.stderr)
        return 1

    # Apply module filter
    manifest = ModuleFilter.filter(manifest, modules_filter)

    # Read progress data
    progress = _load_progress(project_root)

    # Build file reader
    def file_reader_text(path: str) -> str:
        return (project_root / path).read_text(encoding="utf-8")

    def file_reader_bytes(path: str) -> bytes:
        return (project_root / path).read_bytes()

    # Extract metrics
    metrics = ExportMetrics(
        quality_scores=MetricsExtractor.extract_quality_scores(manifest.artifacts, file_reader_text),
        performance=MetricsExtractor.extract_performance(manifest.artifacts, file_reader_text),
        entity_stats=MetricsExtractor.extract_entity_stats(manifest.artifacts, file_reader_text),
    )

    # Read journal
    journal_html: str | None = None
    journal_arts = manifest.by_type("journal")
    if journal_arts:
        try:
            raw_md = file_reader_text(journal_arts[0].path)
            journal_html = _md_to_html(raw_md)
        except (OSError, IOError):
            journal_html = None

    # Render HTML
    print("Generating report...")
    renderer = HTMLRenderer()
    html = renderer.render(progress, metrics, manifest, journal_html, modules_filter)

    # Determine output path
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    ext = args.format
    if args.output:
        output_path = args.output
    else:
        output_path = f"exports/bootcamp_report_{ts}.{ext}"

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        if args.format == "zip":
            assembler = ZIPAssembler()
            size = assembler.assemble(html, manifest, output_path, file_reader_bytes)
            print(f"ZIP archive created: {output_path} ({size:,} bytes, {len(manifest.artifacts)} artifacts)")
        else:
            out.write_text(html, encoding="utf-8")
            size = out.stat().st_size
            print(f"HTML report created: {output_path} ({size:,} bytes, {len(manifest.artifacts)} artifacts)")
    except OSError as exc:
        print(f"Error writing output: {exc}", file=sys.stderr)
        return 1

    return 0


def _load_progress(project_root: Path) -> ProgressData:
    """Load progress data from config/bootcamp_progress.json."""
    pf = project_root / "config" / "bootcamp_progress.json"
    if not pf.is_file():
        print("Warning: no progress data found at config/bootcamp_progress.json.", file=sys.stderr)
        return ProgressData(modules_completed=[])
    try:
        data = json.loads(pf.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Warning: could not read progress data: {exc}", file=sys.stderr)
        return ProgressData(modules_completed=[])
    return ProgressData(
        modules_completed=data.get("modules_completed", []),
        current_module=data.get("current_module"),
        language=data.get("language"),
        data_sources=data.get("data_sources", []),
        track=data.get("track"),
    )


if __name__ == "__main__":
    sys.exit(main())
