# Design Document: Graduation Certificate

## Overview

Auto-generate a graduation certificate in Markdown and HTML formats when a bootcamper completes their track. The feature consists of:

1. **Python CLI script** (`senzing-bootcamp/scripts/generate_graduation_certificate.py`) — reads progress, preferences, and journal data to produce certificate files in `docs/graduation/`.
2. **Steering file edit** (`senzing-bootcamp/steering/module-completion.md`) — adds a non-interactive certificate generation step in the "Path Completion Celebration" section.

The script follows project conventions: stdlib-only, argparse CLI, `main(argv=None)` entry point, dataclass models, and exit code 0/1.

## Architecture

```
config/bootcamp_progress.json ──┐
config/bootcamp_preferences.yaml ──┤──▶ load ──▶ assemble ──▶ render ──▶ write
docs/bootcamp_journal.md ──────────┘                              │
                                                                  ▼
                                                    docs/graduation/graduation_certificate.md
                                                    docs/graduation/graduation_certificate.html
```

The script is a single-file CLI tool with no module dependencies beyond stdlib. It uses a pipeline architecture:

1. **Load** — Parse each input file with graceful degradation (only progress is required)
2. **Assemble** — Combine parsed data into a unified `CertificateData` model
3. **Render** — Produce Markdown and HTML strings from the model
4. **Write** — Create output directory if needed and write both files

The steering file invokes the script non-interactively during path completion. Failures are logged as warnings without blocking the completion flow.

## Components and Interfaces

### Data Loaders

```python
def load_progress(path: Path) -> ProgressData:
    """Load and parse bootcamp_progress.json.

    Args:
        path: Path to the progress JSON file.

    Returns:
        ProgressData with modules_completed and module metadata.

    Raises:
        SystemExit: If the file does not exist (required input).
    """
    ...

def load_preferences(path: Path) -> PreferencesData:
    """Load and parse bootcamp_preferences.yaml using minimal YAML parser.

    Args:
        path: Path to the preferences YAML file.

    Returns:
        PreferencesData with track and language. Uses defaults if file missing.
    """
    ...

def load_journal(path: Path) -> JournalData:
    """Load and parse bootcamp_journal.md for outcomes and ER metrics.

    Args:
        path: Path to the journal markdown file.

    Returns:
        JournalData with per-module outcomes and ER metrics. Empty if file missing.
    """
    ...
```

### Content Assembly

```python
def assemble_certificate(
    progress: ProgressData,
    preferences: PreferencesData,
    journal: JournalData,
    project_name: str,
) -> CertificateData:
    """Combine all data sources into a unified certificate model.

    Args:
        progress: Parsed progress data.
        preferences: Parsed preferences data.
        journal: Parsed journal data.
        project_name: Workspace directory name.

    Returns:
        CertificateData ready for rendering.
    """
    ...
```

### Skills Mapping

A static mapping from module numbers to skill categories:

```python
MODULE_SKILLS: dict[int, list[str]] = {
    1: ["Business Problem Definition", "Use Case Analysis"],
    2: ["SDK Installation", "Environment Configuration"],
    3: ["System Verification", "Database Setup"],
    4: ["Data Collection", "Source Identification"],
    5: ["Data Quality Assessment", "Entity Mapping"],
    6: ["Data Loading", "Multi-Source Integration"],
    7: ["Entity Querying", "Result Visualization"],
    8: ["Performance Tuning", "Benchmarking"],
    9: ["Security Hardening", "Access Control"],
    10: ["Monitoring", "Operational Alerting"],
    11: ["Production Deployment", "CI/CD Integration"],
}
```

### Next-Steps Logic

```python
def derive_next_steps(track: str) -> list[str]:
    """Derive next-step recommendations based on completed track.

    Args:
        track: The completed track name.

    Returns:
        List of recommendation strings.
    """
    ...
```

- Core Bootcamp → recommends performance, security, monitoring, deployment (advanced topics)
- Advanced Topics → recommends production deployment and ongoing operations
- Unknown → provides generic next steps

### Renderers

```python
def render_markdown(data: CertificateData) -> str:
    """Render certificate data as a Markdown document.

    Args:
        data: Assembled certificate content.

    Returns:
        Complete Markdown string.
    """
    ...

def render_html(data: CertificateData) -> str:
    """Render certificate data as an HTML5 document with inline CSS.

    Uses html.escape() for all user-provided content.

    Args:
        data: Assembled certificate content.

    Returns:
        Complete HTML5 string with DOCTYPE, head, body, and inline styles.
    """
    ...
```

### YAML Parsing

```python
def parse_simple_yaml(content: str) -> dict[str, str]:
    """Parse a flat YAML file with simple key: value pairs.

    Handles string values (quoted or unquoted) and boolean literals.
    Ignores comments and blank lines.

    Args:
        content: Raw YAML file content.

    Returns:
        Dict mapping keys to string values.
    """
    ...
```

Since the project convention is stdlib-only (no PyYAML), the preferences file uses a minimal line-by-line parser. The preferences structure is flat (`track`, `language`, `skip_graduation`), so a full YAML parser is unnecessary.

### Journal Parsing

The journal file is Markdown with a known structure:

```python
_MODULE_HEADING_RE = re.compile(r"^##\s+Module\s+(\d+):\s+(.+?)\s+—", re.MULTILINE)
_WHAT_WE_DID_RE = re.compile(r"\*\*What we did:\*\*\s*(.+)")
_ER_ENTITY_COUNT_RE = re.compile(r"entit(?:y count|ies):\s*(\d[\d,]*)", re.IGNORECASE)
_ER_MATCH_RATE_RE = re.compile(r"match(?:\s+rate)?:\s*([\d.]+%?)", re.IGNORECASE)
_ER_DATA_SOURCES_RE = re.compile(r"(?:data\s+)?sources?\s+loaded:\s*(\d+)", re.IGNORECASE)
```

ER metrics are extracted by scanning the full journal for patterns matching entity counts, match rates, and data sources loaded.

### CLI Entry Point

```python
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Arguments:
        --progress-file: Path to progress JSON (default: config/bootcamp_progress.json)
        --preferences-file: Path to preferences YAML (default: config/bootcamp_preferences.yaml)
        --journal-file: Path to journal markdown (default: docs/bootcamp_journal.md)
        --output-dir: Output directory (default: docs/graduation/)

    Returns:
        Namespace with all argument values.
    """
    ...

def main(argv: list[str] | None = None) -> int:
    """Entry point for graduation certificate generation.

    Returns:
        Exit code: 0 for success, 1 for error.
    """
    ...
```

## Data Models

```python
@dataclass
class ProgressData:
    """Parsed progress file content."""
    modules_completed: list[int]
    module_names: dict[int, str]  # module_number -> name

@dataclass
class PreferencesData:
    """Parsed preferences file content."""
    track: str  # "Core Bootcamp" | "Advanced Topics" | "Unknown"
    language: str  # e.g. "Python", "Java", or "Unknown"

@dataclass
class JournalEntry:
    """A single module journal entry."""
    module_number: int
    outcome: str

@dataclass
class ERMetrics:
    """Entity resolution metrics extracted from journal."""
    entity_count: str | None
    match_rate: str | None
    data_sources_loaded: str | None

@dataclass
class JournalData:
    """Parsed journal file content."""
    entries: dict[int, JournalEntry]  # module_number -> entry
    er_metrics: ERMetrics | None

@dataclass
class ModuleRecord:
    """A single module entry for the certificate."""
    number: int
    name: str
    outcome: str  # empty string if no journal entry

@dataclass
class CertificateData:
    """Assembled certificate content ready for rendering."""
    project_name: str
    completion_date: str  # ISO 8601 YYYY-MM-DD
    track: str
    modules: list[ModuleRecord]
    er_metrics: ERMetrics | None
    skills: list[str]
    next_steps: list[str]
```

## Error Handling

| Condition | Behavior |
|-----------|----------|
| Progress file missing | Print error to stderr, exit 1 |
| Progress file malformed JSON | Print error to stderr, exit 1 |
| Preferences file missing | Use defaults (track="Unknown", language="Unknown") |
| Preferences file malformed | Use defaults |
| Journal file missing | Generate without outcomes/ER metrics |
| Journal file malformed | Generate with whatever entries parse successfully |
| Output directory not writable | Print error to stderr, exit 1 |
| Any unexpected exception | Catch at top level, print to stderr, exit 1 |

## Steering File Integration

The `module-completion.md` steering file is updated to add a certificate generation step in the "Path Completion Celebration" section. The new bullet is inserted after the analytics offer and before the graduation offer:

```markdown
- Certificate generation (after the analytics offer, before the graduation offer):
  Run `python3 senzing-bootcamp/scripts/generate_graduation_certificate.py` silently
  (no confirmation prompt). If it succeeds, display:
  "🎓 Graduation certificate generated at docs/graduation/"
  If it fails, log a warning and continue without blocking subsequent steps.
```

## Testing Strategy

**Unit tests** cover:
- Argument parsing defaults and overrides
- Each loader with valid/missing/malformed files
- Skills mapping correctness for specific modules
- Next-steps logic for each track
- HTML escaping of special characters

**Property-based tests** (Hypothesis) cover:
- Round-trip and invariant properties across generated inputs
- Minimum 100 iterations per property (configured via `@settings(max_examples=100)`)
- Strategies generate random progress data, preferences, journal content

**Edge case tests** cover:
- Missing output directory creation
- Overwriting existing files
- Missing journal entries for some modules
- Missing ER metrics placeholder

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Successful generation produces both output files

*For any* valid progress file (with at least one completed module), valid or missing preferences file, and valid or missing journal file, invoking the Certificate_Generator SHALL produce both `graduation_certificate.md` and `graduation_certificate.html` in the output directory and exit with code 0.

**Validates: Requirements 2.7, 3.1, 3.2**

### Property 2: HTML output is valid HTML5 structure

*For any* valid input that produces a successful generation, the HTML output SHALL contain a `<!DOCTYPE html>` declaration, `<html>` root element, `<head>` section with `<style>` block, and `<body>` section with content.

**Validates: Requirements 3.5**

### Property 3: Certificate contains identity metadata

*For any* valid input, the generated certificate (both Markdown and HTML) SHALL contain the project name, a completion date in ISO 8601 format (YYYY-MM-DD), and the track name from the preferences file (or "Unknown" if preferences are missing).

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 4: All completed modules appear in certificate

*For any* valid progress file listing N completed modules, the generated certificate SHALL contain all N module numbers and their corresponding names.

**Validates: Requirements 5.1**

### Property 5: Journal outcomes appear for matching modules

*For any* journal file containing outcome entries for a subset of completed modules, the generated certificate SHALL include the outcome text for each module that has a matching journal entry.

**Validates: Requirements 5.2**

### Property 6: ER metrics from journal appear in certificate

*For any* journal file containing ER-related metrics (entity counts, match rates, data sources loaded), the generated certificate SHALL include those metrics in the ER results summary section. When no ER metrics are present, the certificate SHALL contain a placeholder statement.

**Validates: Requirements 6.1, 6.2**

### Property 7: Skills and next-steps derived from completed track and modules

*For any* set of completed modules and a valid track name, the certificate SHALL contain a skills section with at least one skill per completed module, and a next-steps section with recommendations appropriate to the track.

**Validates: Requirements 7.1, 7.2**

### Property 8: No unhandled exceptions for any input

*For any* combination of input files (including malformed JSON, invalid content, empty files, and binary data), the Certificate_Generator SHALL not raise an unhandled exception. It SHALL either produce a certificate or exit with a non-zero code and an error message to stderr.

**Validates: Requirements 9.4**

### Property 9: Idempotent output

*For any* valid input set, running the Certificate_Generator twice with identical inputs SHALL produce byte-identical output files.

**Validates: Requirements 10.2**
