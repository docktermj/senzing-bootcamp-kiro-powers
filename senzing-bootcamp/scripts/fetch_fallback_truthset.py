#!/usr/bin/env python3
"""Fetch the sanctioned fallback TruthSet for Module 3 system verification.

This script is the fallback TruthSet acquisition path used by Module 3 when the
MCP server's ``get_sample_data`` tool does not expose a named TruthSet. It reads
the Sanctioned_Source_Registry (``config/fallback_sources.yaml``) to obtain the
approved fallback location by identifier, fetches the demo TruthSet record files
and ground-truth key over HTTPS, and (in subsequent pipeline stages) normalizes,
validates, and derives expected results before Step 7 deterministic verification.

The script writes a single JSON status object to stdout for the agent to consume:

    {
      "status": "success|fetch_failed|validation_failed|expected_results_failed",
      "records_written": <int>,
      "file_path": "<path to truthset_data.jsonl>",
      "expected_results": {...} | null,
      "error": null | "<message>"
    }

Usage:
    python fetch_fallback_truthset.py \\
        --config config/fallback_sources.yaml \\
        --output-dir src/system_verification
    python fetch_fallback_truthset.py \\
        --config config/fallback_sources.yaml \\
        --output-dir src/system_verification \\
        --source-id senzing_truthset_demo

Python 3.11+ standard library only (no third-party dependencies). The YAML
registry is read with a minimal in-house parser, consistent with the project
convention that only ``validate_dependencies.py`` uses PyYAML.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_SOURCE_ID = "senzing_truthset_demo"
OUTPUT_FILENAME = "truthset_data.jsonl"
USER_AGENT = "senzing-bootcamp-truthset-fetcher/1.0"

# Expected-results derivation (task 2.4).
TOLERANCE_PERCENT = 5
FALLBACK_SOURCE_LABEL = "github_fallback"
MIN_KNOWN_MATCHES = 3
TRUTH_KEY_COLUMNS = ("CLUSTER_ID", "RECORD_ID", "DATA_SOURCE")


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SourceConfig:
    """Resolved fallback source configuration from the registry.

    Attributes:
        source_id: Registry identifier used to look up the source.
        base_url: Base URL the record and truth-key files are fetched from.
        record_files: Ordered list of JSONL record filenames to fetch.
        truth_key: Filename of the ground-truth key (CSV).
        timeout_seconds: Per-request HTTP timeout in seconds.
    """

    source_id: str
    base_url: str
    record_files: list[str]
    truth_key: str
    timeout_seconds: int


@dataclass
class FetchedContent:
    """Raw content fetched from the sanctioned fallback source.

    Attributes:
        records: Mapping of record filename to its raw text content, in the
            order the files were declared in the registry.
        truth_key_name: Filename of the fetched ground-truth key.
        truth_key_text: Raw text content of the ground-truth key file.
    """

    records: dict[str, str] = field(default_factory=dict)
    truth_key_name: str = ""
    truth_key_text: str = ""


class FetchError(Exception):
    """Raised when a fallback source file cannot be fetched.

    The ``message`` attribute carries the specific, human-readable reason
    (HTTP status, timeout, or network error) recorded in the stdout status.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(Exception):
    """Raised when the normalized JSONL output file fails validation.

    The ``message`` attribute carries the specific, human-readable reason
    identifying which validation check failed (an invalid-JSON line or a
    line-count mismatch), recorded in the stdout status ``error`` field.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ExpectedResultsError(Exception):
    """Raised when Fallback_Expected_Results cannot be derived from the key.

    Signals that the ground-truth key is missing, incomplete, or does not yield
    enough known matches for deterministic verification (fewer than three
    multi-record clusters). The ``message`` attribute carries the specific,
    human-readable reason recorded in the stdout status ``error`` field, and the
    pipeline converts it into an ``expected_results_failed`` status.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


# ---------------------------------------------------------------------------
# Minimal YAML registry parser (stdlib only; no PyYAML)
# ---------------------------------------------------------------------------


def _tokenize_yaml(text: str) -> list[tuple[int, str]]:
    """Split YAML text into ``(indent, stripped_text)`` entries.

    Blank lines and ``#`` comment lines are discarded.

    Args:
        text: Raw YAML document text.

    Returns:
        A list of ``(indent, text)`` tuples in document order.
    """
    entries: list[tuple[int, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        entries.append((indent, stripped))
    return entries


def _strip_inline_comment(value: str) -> str:
    """Remove a trailing ``  # comment`` from an unquoted scalar.

    A ``#`` inside a quoted string is preserved.

    Args:
        value: The raw scalar text following the ``key:`` separator.

    Returns:
        The scalar text with any trailing inline comment removed.
    """
    if value.startswith('"') or value.startswith("'"):
        return value
    idx = value.find(" #")
    if idx != -1:
        return value[:idx].strip()
    return value


def _parse_scalar(value: str) -> str | None:
    """Parse a single YAML scalar into a Python value.

    Quoted strings have their surrounding quotes removed; the YAML null tokens
    (``null``, ``~``) and the empty string map to ``None``. All other values are
    returned as plain strings.

    Args:
        value: The raw scalar text.

    Returns:
        The parsed string, or ``None`` for null/empty scalars.
    """
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    if value in ("", "null", "~"):
        return None
    return value


def _parse_yaml_list(
    entries: list[tuple[int, str]], i: int, indent: int
) -> tuple[list, int]:
    """Parse a block of ``- item`` list entries at a fixed indentation.

    Only scalar list items are supported (sufficient for the registry schema).

    Args:
        entries: The ``(indent, text)`` entries of the document.
        i: Index of the first list entry.
        indent: The indentation level shared by the list items.

    Returns:
        A ``(list, next_index)`` tuple.
    """
    items: list = []
    while i < len(entries):
        cur_indent, text = entries[i]
        if cur_indent != indent or not text.startswith("- "):
            break
        items.append(_parse_scalar(_strip_inline_comment(text[2:].strip())))
        i += 1
    return items, i


def _parse_yaml_block(
    entries: list[tuple[int, str]], i: int, indent: int
) -> tuple[object, int]:
    """Dispatch to the list or mapping parser based on the first entry.

    Args:
        entries: The ``(indent, text)`` entries of the document.
        i: Index of the first entry of the block.
        indent: The indentation level of the block.

    Returns:
        A ``(value, next_index)`` tuple where ``value`` is a list or dict.
    """
    if entries[i][1].startswith("- "):
        return _parse_yaml_list(entries, i, indent)
    return _parse_yaml_mapping(entries, i, indent)


def _parse_yaml_mapping(
    entries: list[tuple[int, str]], i: int, indent: int
) -> tuple[dict, int]:
    """Parse a YAML mapping at a fixed indentation level.

    Args:
        entries: The ``(indent, text)`` entries of the document.
        i: Index of the first entry of the mapping.
        indent: The indentation level shared by the mapping's keys.

    Returns:
        A ``(mapping, next_index)`` tuple.

    Raises:
        ValueError: When an entry at this level is neither a ``key: value`` pair
            nor a recognized nested block.
    """
    result: dict = {}
    while i < len(entries):
        cur_indent, text = entries[i]
        if cur_indent < indent or text.startswith("- "):
            break
        if cur_indent > indent:
            raise ValueError(f"unexpected indentation: {text!r}")
        colon = text.find(":")
        if colon == -1:
            raise ValueError(f"expected 'key: value', got: {text!r}")
        key = text[:colon].strip().strip("\"'")
        rest = _strip_inline_comment(text[colon + 1:].strip())
        if rest:
            result[key] = _parse_scalar(rest)
            i += 1
            continue
        i += 1
        if i < len(entries) and entries[i][0] > indent:
            child, i = _parse_yaml_block(entries, i, entries[i][0])
            result[key] = child
        else:
            result[key] = None
    return result, i


def parse_registry(text: str) -> dict:
    """Parse the minimal YAML subset used by the fallback source registry.

    Supports nested mappings, scalar ``key: value`` pairs, and blocks of scalar
    ``- item`` list entries. Blank lines and ``#`` comment lines are ignored.

    Args:
        text: Raw YAML text of the registry file.

    Returns:
        A nested dict mirroring the document's top-level mapping.

    Raises:
        ValueError: When the text is not a well-formed instance of the supported
            YAML subset.
    """
    entries = _tokenize_yaml(text)
    if not entries:
        return {}
    if entries[0][0] != 0:
        raise ValueError("top-level content must not be indented")
    if entries[0][1].startswith("- "):
        raise ValueError("top-level content must be a mapping, not a list")
    result, index = _parse_yaml_mapping(entries, 0, 0)
    if index != len(entries):
        raise ValueError("unexpected trailing content")
    return result


def load_source_config(config_path: str | Path, source_id: str) -> SourceConfig:
    """Read the registry and resolve one source into a ``SourceConfig``.

    Args:
        config_path: Path to ``fallback_sources.yaml``.
        source_id: Registry identifier of the source to resolve.

    Returns:
        The resolved ``SourceConfig``.

    Raises:
        OSError: When the registry file cannot be read.
        ValueError: When the registry is malformed or a required field is
            missing or invalid.
        KeyError: When ``source_id`` is not present in the registry.
    """
    text = Path(config_path).read_text(encoding="utf-8")
    registry = parse_registry(text)

    sources = registry.get("sources")
    if not isinstance(sources, dict):
        raise ValueError("registry has no 'sources' mapping")
    if source_id not in sources:
        raise KeyError(f"source_id '{source_id}' not found in {config_path}")

    source = sources[source_id] or {}
    base_url = source.get("base_url")
    if not base_url:
        raise ValueError(f"source '{source_id}' is missing 'base_url'")

    files = source.get("files") or {}
    records = files.get("records") or []
    if isinstance(records, str):
        records = [records]
    if not records:
        raise ValueError(f"source '{source_id}' declares no record files")
    truth_key = files.get("truth_key")
    if not truth_key:
        raise ValueError(f"source '{source_id}' is missing 'files.truth_key'")

    raw_timeout = source.get("timeout_seconds")
    if raw_timeout is None:
        raise ValueError(f"source '{source_id}' is missing 'timeout_seconds'")
    try:
        timeout_seconds = int(raw_timeout)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"source '{source_id}' has non-integer timeout_seconds: {raw_timeout!r}"
        ) from exc

    return SourceConfig(
        source_id=source_id,
        base_url=str(base_url),
        record_files=[str(name) for name in records],
        truth_key=str(truth_key),
        timeout_seconds=timeout_seconds,
    )


# ---------------------------------------------------------------------------
# HTTP fetcher
# ---------------------------------------------------------------------------


def _build_url(base_url: str, filename: str) -> str:
    """Join a base URL and filename with exactly one separating slash.

    Args:
        base_url: The registry base URL.
        filename: The file to append.

    Returns:
        The full URL.
    """
    return f"{base_url.rstrip('/')}/{filename}"


def fetch_file(base_url: str, filename: str, timeout: int) -> str:
    """Fetch a single file from the fallback source over HTTP(S).

    A non-200 response, a timeout, or any network error is normalized into a
    ``FetchError`` whose message records the specific reason.

    Args:
        base_url: Base URL of the fallback source.
        filename: File to fetch, relative to ``base_url``.
        timeout: Per-request timeout in seconds.

    Returns:
        The decoded UTF-8 body of the response.

    Raises:
        FetchError: On any non-200 status, timeout, or network failure.
    """
    url = _build_url(base_url, filename)
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.getcode()
            if status != 200:
                raise FetchError(f"HTTP {status} for {filename}")
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise FetchError(f"HTTP {exc.code} for {filename}") from exc
    except socket.timeout as exc:  # alias of TimeoutError on 3.10+
        raise FetchError(f"Timeout after {timeout}s for {filename}") from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, (socket.timeout, TimeoutError)):
            raise FetchError(f"Timeout after {timeout}s for {filename}") from exc
        raise FetchError(f"Network error for {filename}: {exc.reason}") from exc
    except TimeoutError as exc:
        raise FetchError(f"Timeout after {timeout}s for {filename}") from exc


def fetch_all(config: SourceConfig) -> FetchedContent:
    """Fetch every record file and the truth-key file for a source.

    No partial acquisition is allowed: if any single fetch fails, the resulting
    ``FetchError`` propagates and the whole fallback is classified unreachable.

    Args:
        config: The resolved source configuration.

    Returns:
        A ``FetchedContent`` with the raw record contents and truth-key content.

    Raises:
        FetchError: If any record file or the truth key cannot be fetched.
    """
    records: dict[str, str] = {}
    for filename in config.record_files:
        records[filename] = fetch_file(config.base_url, filename, config.timeout_seconds)
    truth_key_text = fetch_file(config.base_url, config.truth_key, config.timeout_seconds)
    return FetchedContent(
        records=records,
        truth_key_name=config.truth_key,
        truth_key_text=truth_key_text,
    )


# ---------------------------------------------------------------------------
# Downstream pipeline hooks (implemented by later tasks)
#
# These stages extend this same script:
#   * normalize_records      -> task 2.2 (record normalizer)
#   * validate_jsonl         -> task 2.3 (JSONL validator)
#   * derive_expected_results-> task 2.4 (expected-results deriver)
# They are declared here so the fetch foundation and main() orchestration have
# stable seams to plug into.
# ---------------------------------------------------------------------------


def _data_source_from_filename(filename: str) -> str:
    """Derive a ``DATA_SOURCE`` label from a record filename.

    The label is the filename stem upper-cased, e.g. ``customers.jsonl`` maps to
    ``CUSTOMERS`` and ``watchlist.jsonl`` maps to ``WATCHLIST``.

    Args:
        filename: The record filename declared in the registry.

    Returns:
        The derived ``DATA_SOURCE`` label.
    """
    return Path(filename).stem.upper()


def normalize_records(fetched: FetchedContent, output_path: Path) -> int:
    """Normalize fetched record files into a single JSONL output file.

    Concatenates the fetched record files, in registry order, into one
    ``truthset_data.jsonl`` at ``output_path`` with exactly one JSON object per
    line. Each line is parsed as JSON to validate its structure; when a record is
    a JSON object that has no ``DATA_SOURCE`` field, one is added, derived from
    the source filename (``customers.jsonl`` maps to ``CUSTOMERS``). Blank lines
    are ignored. Any existing file at ``output_path`` is overwritten.

    Normalization is idempotent: because an existing ``DATA_SOURCE`` is never
    overwritten, the file is always rewritten from scratch, and serialization is
    deterministic, running it again on the same content produces byte-identical
    output.

    Args:
        fetched: The raw content fetched from the fallback source.
        output_path: Destination path for the normalized JSONL file.

    Returns:
        The number of records written to the output file.

    Raises:
        json.JSONDecodeError: If a non-blank source line is not valid JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records_written = 0
    with output_path.open("w", encoding="utf-8") as out:
        for filename, content in fetched.records.items():
            data_source = _data_source_from_filename(filename)
            for line in content.splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                if isinstance(record, dict) and "DATA_SOURCE" not in record:
                    record["DATA_SOURCE"] = data_source
                out.write(json.dumps(record, ensure_ascii=False))
                out.write("\n")
                records_written += 1

    return records_written


def validate_jsonl(output_path: Path, expected_record_count: int) -> None:
    """Validate the normalized JSONL output file.

    Runs two checks and raises on the first failure, so validation blocks
    progression before the success status is built:

    1. **JSON validity**: every non-blank line parses as a valid JSON value.
    2. **Line count**: the number of non-blank (record) lines equals
       ``expected_record_count`` (the number of records fetched from the source).

    Args:
        output_path: Path to the normalized JSONL file.
        expected_record_count: Number of records fetched from the source.

    Raises:
        ValidationError: If a non-blank line is not valid JSON (identifying the
            offending line number) or the record line count does not match
            ``expected_record_count`` (identifying the mismatch).
        OSError: If the output file cannot be read.
    """
    record_count = 0
    with output_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue
            try:
                json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise ValidationError(
                    f"JSON validity check failed: line {line_number} is not "
                    f"valid JSON: {exc.msg}"
                ) from exc
            record_count += 1

    if record_count != expected_record_count:
        raise ValidationError(
            f"line count check failed: found {record_count} record line(s), "
            f"expected {expected_record_count}"
        )


def derive_expected_results(truth_key_text: str) -> dict:
    """Derive Fallback_Expected_Results from the ground-truth key CSV.

    Parses ``actual_truthset_key.csv`` (which declares at least the
    ``CLUSTER_ID``, ``RECORD_ID``, and ``DATA_SOURCE`` columns, in any order and
    possibly alongside extra columns) by column name, then computes:

    * ``expected_entity_count`` -- the number of distinct ``CLUSTER_ID`` values.
    * ``known_matches`` -- one entry per cluster that resolves 2+ distinct
      records. Each entry lists its member records as ``"DATA_SOURCE:RECORD_ID"``
      identifiers and carries an ``entity_label`` of ``"cluster_<CLUSTER_ID>"``.

    The result also fixes ``tolerance_percent`` at 5 and labels the ``source`` as
    ``github_fallback`` so Step 7 deterministic verification can run unchanged.

    Args:
        truth_key_text: Raw CSV content of the ground-truth key.

    Returns:
        The expected-results object with ``expected_entity_count``,
        ``tolerance_percent``, ``known_matches``, and ``source`` keys.

    Raises:
        ExpectedResultsError: If the key has no header, is missing a required
            column, contains no usable rows, or yields fewer than three
            multi-record clusters (incomplete truth definitions).
    """
    reader = csv.DictReader(io.StringIO(truth_key_text))
    if not reader.fieldnames:
        raise ExpectedResultsError("truth key is empty: no header row found")

    # Map each required column to its actual header, tolerating surrounding
    # whitespace, a BOM on the first header, and case differences.
    header_lookup = {
        (name or "").strip().lstrip("\ufeff").upper(): name
        for name in reader.fieldnames
    }
    missing = [column for column in TRUTH_KEY_COLUMNS if column not in header_lookup]
    if missing:
        raise ExpectedResultsError(
            f"truth key is missing required column(s): {', '.join(missing)}"
        )

    cluster_col = header_lookup["CLUSTER_ID"]
    record_col = header_lookup["RECORD_ID"]
    source_col = header_lookup["DATA_SOURCE"]

    # Preserve first-seen order of clusters and their member records so the
    # derived output is deterministic across runs.
    clusters: dict[str, list[str]] = {}
    for row in reader:
        cluster_id = (row.get(cluster_col) or "").strip()
        record_id = (row.get(record_col) or "").strip()
        data_source = (row.get(source_col) or "").strip()
        if not cluster_id or not record_id or not data_source:
            continue
        identifier = f"{data_source}:{record_id}"
        members = clusters.setdefault(cluster_id, [])
        if identifier not in members:
            members.append(identifier)

    if not clusters:
        raise ExpectedResultsError("truth key contains no usable cluster rows")

    known_matches = [
        {"records": members, "entity_label": f"cluster_{cluster_id}"}
        for cluster_id, members in clusters.items()
        if len(members) >= 2
    ]
    if len(known_matches) < MIN_KNOWN_MATCHES:
        raise ExpectedResultsError(
            f"truth key yields only {len(known_matches)} multi-record cluster(s); "
            f"at least {MIN_KNOWN_MATCHES} known matches are required"
        )

    return {
        "expected_entity_count": len(clusters),
        "tolerance_percent": TOLERANCE_PERCENT,
        "known_matches": known_matches,
        "source": FALLBACK_SOURCE_LABEL,
    }


# ---------------------------------------------------------------------------
# Status output + CLI
# ---------------------------------------------------------------------------


def build_status(
    status: str,
    file_path: str | Path,
    *,
    records_written: int = 0,
    expected_results: dict | None = None,
    error: str | None = None,
) -> dict:
    """Build the stdout status object described by the interface contract.

    Args:
        status: One of ``success``, ``fetch_failed``, ``validation_failed``,
            ``expected_results_failed``.
        file_path: Path to the target ``truthset_data.jsonl``.
        records_written: Number of records written to the output file.
        expected_results: Derived expected-results object, or ``None``.
        error: Specific failure message, or ``None`` on success.

    Returns:
        A dict ready to be serialized to stdout as JSON.
    """
    return {
        "status": status,
        "records_written": records_written,
        "file_path": str(file_path),
        "expected_results": expected_results,
        "error": error,
    }


def _emit(status: dict) -> None:
    """Write a status object to stdout as a single JSON line.

    Args:
        status: The status object to serialize.
    """
    print(json.dumps(status))


def run_acquisition(config: SourceConfig, output_dir: str | Path) -> dict:
    """Run the fallback acquisition pipeline and return a status object.

    Task 2.1 implements the fetch stage. The normalize/validate/derive stages
    are plugged in by tasks 2.2-2.4 via the hook functions above.

    Args:
        config: The resolved source configuration.
        output_dir: Directory the ``truthset_data.jsonl`` file is written to.

    Returns:
        A status object describing the outcome.
    """
    output_path = Path(output_dir) / OUTPUT_FILENAME

    try:
        fetched = fetch_all(config)
    except FetchError as exc:
        return build_status("fetch_failed", output_path, error=exc.message)

    # Downstream stages (tasks 2.2-2.4).
    records_written = normalize_records(fetched, output_path)
    try:
        validate_jsonl(output_path, records_written)
    except ValidationError as exc:
        return build_status(
            "validation_failed",
            output_path,
            records_written=records_written,
            error=exc.message,
        )
    try:
        expected_results = derive_expected_results(fetched.truth_key_text)
    except ExpectedResultsError as exc:
        return build_status(
            "expected_results_failed",
            output_path,
            records_written=records_written,
            error=exc.message,
        )
    return build_status(
        "success",
        output_path,
        records_written=records_written,
        expected_results=expected_results,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code: 0 on success, 1 on any failure status.
    """
    parser = argparse.ArgumentParser(
        description="Fetch the sanctioned fallback TruthSet for Module 3.",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the fallback source registry (fallback_sources.yaml).",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to write truthset_data.jsonl into.",
    )
    parser.add_argument(
        "--source-id",
        default=DEFAULT_SOURCE_ID,
        help=f"Registry identifier of the fallback source (default: {DEFAULT_SOURCE_ID}).",
    )
    args = parser.parse_args(argv)

    output_path = Path(args.output_dir) / OUTPUT_FILENAME

    try:
        config = load_source_config(args.config, args.source_id)
    except (OSError, ValueError, KeyError) as exc:
        _emit(build_status("fetch_failed", output_path, error=f"registry error: {exc}"))
        return 1

    status = run_acquisition(config, args.output_dir)
    _emit(status)
    return 0 if status["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
