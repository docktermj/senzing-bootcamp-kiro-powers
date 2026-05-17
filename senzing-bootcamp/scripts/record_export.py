#!/usr/bin/env python3
"""Senzing Bootcamp - Record Export.

Generates a structured YAML decision manifest capturing every meaningful choice
a bootcamper made during their journey. The manifest is designed to be both
human-readable and machine-parseable for theoretical replay.

Usage:
    python3 scripts/record_export.py
    python3 scripts/record_export.py --output path/to/output.yaml
    python3 scripts/record_export.py --dry-run
    python3 scripts/record_export.py --overwrite
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
import os
import re
from collections.abc import Callable


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "1.0"
POWER_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class PreferencesData:
    """Bootcamper preferences from config/bootcamp_preferences.yaml."""

    language: str | None
    track: str | None
    database_type: str | None
    deployment_target: str | None
    cloud_provider: str | None
    verbosity: str | None


@dataclasses.dataclass
class ProgressData:
    """Module completion state from config/bootcamp_progress.json."""

    modules_completed: list[int]
    current_module: int | None
    step_history: dict[str, dict] | None


@dataclasses.dataclass
class DataSourceEntry:
    """A registered data source from config/data_sources.yaml."""

    name: str
    file_path: str
    file_format: str
    record_count: int | None
    module: int = 4


@dataclasses.dataclass
class MappingDecision:
    """Field mapping configuration for a data source (Module 5)."""

    source_name: str
    entity_type: str
    field_mappings: dict[str, str]
    transformations: list[str]
    module: int = 5


@dataclasses.dataclass
class LoadingConfig:
    """Loading strategy decisions from Module 6."""

    strategy: str
    redo_processing: bool | None
    redo_reason: str | None
    script_files: list[str]
    module: int = 6


@dataclasses.dataclass
class QueryProgram:
    """A query script created during Module 7."""

    filename: str
    query_type: str
    description: str
    module: int = 7


@dataclasses.dataclass
class BusinessProblem:
    """Business problem definition from Module 1."""

    problem_statement: str | None
    identified_sources: list[str]
    success_criteria: list[str]
    module: int = 1


@dataclasses.dataclass
class PerformanceTuning:
    """Performance tuning decisions from Module 8."""

    tuning_decisions: list[str]
    baseline_metrics: dict[str, str] | None
    optimizations_applied: list[str]
    module: int = 8


@dataclasses.dataclass
class SecurityHardening:
    """Security hardening decisions from Module 9."""

    choices: list[str]
    checklist_items_completed: int | None
    checklist_items_total: int | None
    module: int = 9


@dataclasses.dataclass
class MonitoringConfig:
    """Monitoring configuration from Module 10."""

    tools_chosen: list[str]
    alert_configurations: list[str]
    module: int = 10


@dataclasses.dataclass
class DeploymentDecision:
    """Deployment decisions from Module 11."""

    target: str
    infrastructure_choices: list[str]
    deployment_method: str | None
    module: int = 11


@dataclasses.dataclass
class CollectedDecisions:
    """All decisions collected from project files."""

    preferences: PreferencesData | None
    progress: ProgressData | None
    business_problem: BusinessProblem | None
    data_sources: list[DataSourceEntry]
    mappings: list[MappingDecision]
    loading_config: LoadingConfig | None
    query_programs: list[QueryProgram]
    performance_tuning: PerformanceTuning | None
    security_hardening: SecurityHardening | None
    monitoring_config: MonitoringConfig | None
    deployment: DeploymentDecision | None
    warnings: list[str]


@dataclasses.dataclass
class DecisionManifest:
    """The final structured manifest written to YAML."""

    metadata: dict
    track_progress: dict
    business_problem: dict | None
    sdk_setup: dict | None
    data_sources: list[dict]
    mapping_decisions: list[dict]
    loading_config: dict | None
    query_programs: list[dict]
    performance_tuning: dict | None
    security_hardening: dict | None
    monitoring_config: dict | None
    deployment: dict | None
    replay_notes: list[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def generate_metadata() -> dict:
    """Generate manifest metadata section.

    Returns:
        Dict with schema_version, generated_at (ISO 8601 UTC), and power_version.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "power_version": POWER_VERSION,
    }


# ---------------------------------------------------------------------------
# Security Sanitizer
# ---------------------------------------------------------------------------


class SecuritySanitizer:
    """Scans manifest content for sensitive data and redacts.

    Detects secrets, credentials, absolute paths, and PII patterns in
    manifest values. Redacts matches and returns warnings for each finding.
    """

    PII_PATTERNS: list[re.Pattern] = [
        # Email addresses
        re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
        # US phone numbers: 555-123-4567, 555.123.4567, 555 123 4567
        re.compile(r"\d{3}[-.\s]?\d{3}[-.\s]?\d{4}"),
        # US phone numbers with parens: (555) 123-4567, (555)123-4567
        re.compile(r"\(\d{3}\)\s?\d{3}[-.\s]?\d{4}"),
        # Social Security Numbers: 123-45-6789
        re.compile(r"\d{3}-\d{2}-\d{4}"),
    ]

    SECRET_PATTERNS: list[re.Pattern] = [
        # Connection strings (database URIs)
        re.compile(r"(postgres|mysql|sqlite|mongodb)://[^\s]+"),
        # AWS-style access key IDs
        re.compile(r"AKIA[0-9A-Z]{16}"),
        # Generic token/key/secret/password/credential assignments
        re.compile(
            r"(token|key|secret|password|credential)\s*[:=]\s*\S+", re.IGNORECASE
        ),
        # Long hex strings (40+ chars) that look like API keys or hashes
        re.compile(r"[0-9a-fA-F]{40,}"),
        # Base64-like long strings (40+ chars of alphanumeric plus +/)
        re.compile(r"[A-Za-z0-9+/]{40,}"),
    ]

    def check_value(self, value: str) -> bool:
        """Check whether a string appears to contain sensitive content.

        Args:
            value: The string to inspect.

        Returns:
            True if the value matches any secret pattern.
        """
        for pattern in self.SECRET_PATTERNS:
            if pattern.search(value):
                return True
        return False

    def relativize_path(self, path: str, project_root: str) -> str:
        """Convert an absolute path to a relative path.

        Args:
            path: The file path to process.
            project_root: The project root directory for relativization.

        Returns:
            A relative path string. Returns as-is if already relative.
        """
        if not path:
            return path

        # Check if already relative: doesn't start with / and doesn't match
        # a Windows drive letter pattern like C:\ or C:/
        is_absolute = path.startswith("/") or (
            len(path) >= 3 and path[0].isalpha() and path[1] == ":"
            and path[2] in ("/", "\\")
        )
        if not is_absolute:
            return path

        # Normalize separators for consistent comparison
        norm_path = path.replace("\\", "/")
        norm_root = project_root.replace("\\", "/").rstrip("/")

        # If path starts with project_root, strip it and return relative portion
        if norm_root and norm_path.startswith(norm_root):
            relative = norm_path[len(norm_root):]
            # Remove leading separator
            relative = relative.lstrip("/")
            return relative if relative else path

        # Absolute path that doesn't start with project_root: strip leading
        # / or drive letter prefix (best effort)
        if norm_path.startswith("/"):
            return norm_path[1:]

        # Windows drive letter: strip "X:/" prefix
        if (
            len(norm_path) >= 3
            and norm_path[0].isalpha()
            and norm_path[1] == ":"
            and norm_path[2] == "/"
        ):
            return norm_path[3:]

        return path

    def scan_for_pii(self, text: str) -> bool:
        """Heuristic check for personally identifiable information.

        Checks for email addresses, phone numbers, and SSN patterns.

        Args:
            text: The text to scan for PII.

        Returns:
            True if potential PII is detected.
        """
        if not text:
            return False
        for pattern in self.PII_PATTERNS:
            if pattern.search(text):
                return True
        return False

    def _walk_and_sanitize(
        self, obj: object, project_root: str, warnings: list[str], field_name: str = ""
    ) -> object:
        """Recursively walk a structure and sanitize all string values.

        Args:
            obj: The object to process (dict, list, or scalar).
            project_root: The project root for path relativization.
            warnings: Accumulator list for sanitization warnings.
            field_name: Current field name for warning messages.

        Returns:
            The sanitized object with secrets redacted and paths relativized.
        """
        if isinstance(obj, dict):
            return {
                k: self._walk_and_sanitize(v, project_root, warnings, field_name=k)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [
                self._walk_and_sanitize(item, project_root, warnings, field_name=field_name)
                for item in obj
            ]
        if isinstance(obj, str):
            # Check secrets first
            if self.check_value(obj):
                warnings.append(f"Redacted secret in field '{field_name}'")
                return "[REDACTED]"
            # Check absolute paths
            is_absolute = obj.startswith("/") or (
                len(obj) >= 3 and obj[0].isalpha() and obj[1] == ":"
                and obj[2] in ("/", "\\")
            )
            if is_absolute:
                obj = self.relativize_path(obj, project_root)
            # Check PII
            if self.scan_for_pii(obj):
                warnings.append(f"Detected PII in field '{field_name}'")
                return "[PII REDACTED]"
            return obj
        return obj

    def sanitize(
        self, manifest: DecisionManifest, project_root: str = ""
    ) -> tuple[DecisionManifest, list[str]]:
        """Sanitize a manifest by redacting secrets and relativizing paths.

        Walks all string values in the manifest, redacts detected secrets,
        converts absolute paths to relative, and collects warnings.

        Args:
            manifest: The decision manifest to sanitize.
            project_root: The project root directory for path relativization.

        Returns:
            A tuple of (cleaned_manifest, warnings) where warnings lists
            each redaction or path conversion performed.
        """
        warnings: list[str] = []
        manifest_dict = dataclasses.asdict(manifest)
        sanitized_dict = self._walk_and_sanitize(manifest_dict, project_root, warnings)
        sanitized_manifest = DecisionManifest(**sanitized_dict)
        return (sanitized_manifest, warnings)


# ---------------------------------------------------------------------------
# Decision Collector
# ---------------------------------------------------------------------------


class DecisionCollector:
    """Reads project files and extracts bootcamp decisions.

    Collects structured decision data from config files, source directories,
    and documentation within the project.
    """

    def __init__(
        self,
        project_root: str,
        file_reader: Callable[[str], str | None] = None,
        dir_lister: Callable[[str], list[str]] | None = None,
    ) -> None:
        """Initialize with project root and optional file reader.

        Args:
            project_root: Absolute path to the project root directory.
            file_reader: Optional callable that takes a file path and returns
                its content as a string, or None if the file doesn't exist.
                If not provided, uses a default that reads from disk.
            dir_lister: Optional callable that takes a directory path and returns
                a list of filenames in that directory. If not provided, uses
                os.listdir. Allows testing without real filesystem access.
        """
        self.project_root = project_root
        if file_reader is not None:
            self._read_file = file_reader
        else:
            self._read_file = self._default_file_reader
        if dir_lister is not None:
            self._list_dir = dir_lister
        else:
            self._list_dir = self._default_dir_lister

    @staticmethod
    def _default_file_reader(path: str) -> str | None:
        """Read a file from disk, returning None if it doesn't exist.

        Args:
            path: Absolute path to the file.

        Returns:
            File content as a string, or None if the file doesn't exist.
        """
        try:
            with open(path, encoding="utf-8") as f:
                return f.read()
        except (FileNotFoundError, PermissionError, OSError):
            return None

    @staticmethod
    def _default_dir_lister(path: str) -> list[str]:
        """List files in a directory, returning empty list on error.

        Args:
            path: Absolute path to the directory.

        Returns:
            List of filenames in the directory, or empty list if not accessible.
        """
        try:
            return os.listdir(path)
        except (FileNotFoundError, PermissionError, OSError):
            return []

    def _parse_simple_yaml(self, content: str) -> dict[str, str | None]:
        """Parse simple key-value YAML content without external dependencies.

        Handles:
        - key: value lines
        - Comments (lines starting with #)
        - Empty lines
        - String values (with or without quotes)
        - null/None values

        Args:
            content: Raw YAML string with simple key-value pairs.

        Returns:
            Dict mapping keys to string values (or None for null values).
        """
        result: dict[str, str | None] = {}
        for line in content.splitlines():
            stripped = line.strip()
            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue
            # Split on first colon
            if ":" not in stripped:
                continue
            key, _, raw_value = stripped.partition(":")
            key = key.strip()
            if not key:
                continue
            value = raw_value.strip()
            # Handle null/None values
            if value.lower() in ("null", "none", "~", ""):
                result[key] = None
                continue
            # Strip surrounding quotes (single or double)
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            result[key] = value
        return result

    def collect_preferences(self) -> PreferencesData | None:
        """Read config/bootcamp_preferences.yaml and return PreferencesData.

        Returns:
            A PreferencesData instance with values from the YAML file,
            or None if the file doesn't exist.
        """
        path = os.path.join(self.project_root, "config", "bootcamp_preferences.yaml")
        content = self._read_file(path)
        if content is None:
            return None
        data = self._parse_simple_yaml(content)
        return PreferencesData(
            language=data.get("language"),
            track=data.get("track"),
            database_type=data.get("database_type"),
            deployment_target=data.get("deployment_target"),
            cloud_provider=data.get("cloud_provider"),
            verbosity=data.get("verbosity"),
        )

    def collect_progress(self) -> ProgressData | None:
        """Read config/bootcamp_progress.json and return ProgressData.

        Returns:
            A ProgressData instance with module completion state,
            or None if the file doesn't exist or JSON parsing fails.
        """
        path = os.path.join(self.project_root, "config", "bootcamp_progress.json")
        content = self._read_file(path)
        if content is None:
            return None
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return None
        if not isinstance(data, dict):
            return None
        modules_completed = data.get("modules_completed", [])
        if not isinstance(modules_completed, list):
            modules_completed = []
        current_module = data.get("current_module")
        if current_module is not None and not isinstance(current_module, int):
            current_module = None
        step_history = data.get("step_history")
        if step_history is not None and not isinstance(step_history, dict):
            step_history = None
        return ProgressData(
            modules_completed=modules_completed,
            current_module=current_module,
            step_history=step_history,
        )

    def _parse_data_sources_yaml(self, content: str) -> list[dict]:
        """Parse a YAML list of data source entries without external dependencies.

        Handles list-based YAML format where each item starts with ``- `` and
        subsequent indented lines provide key-value pairs for that item.

        Args:
            content: Raw YAML string containing a list of data source entries.

        Returns:
            List of dicts, each with keys like name, file_path, file_format,
            record_count parsed from the YAML content.
        """
        entries: list[dict] = []
        current: dict | None = None

        for line in content.splitlines():
            stripped = line.strip()
            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue

            if stripped.startswith("- "):
                # New list item — save previous if exists
                if current is not None:
                    entries.append(current)
                current = {}
                # The rest of the line after "- " may contain a key: value
                remainder = stripped[2:].strip()
                if remainder and ":" in remainder:
                    key, _, raw_value = remainder.partition(":")
                    key = key.strip()
                    value = raw_value.strip()
                    if key:
                        current[key] = self._parse_yaml_scalar(value)
            elif current is not None and ":" in stripped:
                # Indented key: value belonging to current item
                key, _, raw_value = stripped.partition(":")
                key = key.strip()
                value = raw_value.strip()
                if key:
                    current[key] = self._parse_yaml_scalar(value)

        # Don't forget the last item
        if current is not None:
            entries.append(current)

        return entries

    @staticmethod
    def _parse_yaml_scalar(value: str) -> str | int | None:
        """Parse a single YAML scalar value to a Python type.

        Args:
            value: The raw string value from a YAML key-value pair.

        Returns:
            None for null/empty values, int for numeric strings, or the
            string value with surrounding quotes stripped.
        """
        if not value or value.lower() in ("null", "none", "~"):
            return None
        # Strip surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        # Try integer conversion
        try:
            return int(value)
        except ValueError:
            return value

    def collect_data_sources(self) -> list[DataSourceEntry]:
        """Read config/data_sources.yaml or scan data/raw/ as fallback.

        First attempts to read and parse config/data_sources.yaml. If that
        file doesn't exist, falls back to scanning the data/raw/ directory
        for files and inferring metadata from filenames.

        Returns:
            List of DataSourceEntry instances. Returns empty list if neither
            source is available.
        """
        # Try config/data_sources.yaml first
        yaml_path = os.path.join(self.project_root, "config", "data_sources.yaml")
        content = self._read_file(yaml_path)
        if content is not None:
            parsed = self._parse_data_sources_yaml(content)
            entries: list[DataSourceEntry] = []
            for item in parsed:
                name = item.get("name")
                if not name:
                    continue
                file_path = item.get("file_path", "")
                file_format = item.get("file_format", "")
                record_count = item.get("record_count")
                if record_count is not None:
                    try:
                        record_count = int(record_count)
                    except (ValueError, TypeError):
                        record_count = None
                entries.append(DataSourceEntry(
                    name=str(name),
                    file_path=str(file_path) if file_path else "",
                    file_format=str(file_format) if file_format else "",
                    record_count=record_count,
                    module=4,
                ))
            return entries

        # Fallback: scan data/raw/ directory
        raw_dir = os.path.join(self.project_root, "data", "raw")
        try:
            filenames = os.listdir(raw_dir)
        except (FileNotFoundError, PermissionError, OSError):
            return []

        entries = []
        for filename in sorted(filenames):
            # Skip hidden files and directories
            if filename.startswith("."):
                continue
            full_path = os.path.join(raw_dir, filename)
            if not os.path.isfile(full_path):
                continue
            name_without_ext, ext = os.path.splitext(filename)
            file_format = ext.lstrip(".").lower() if ext else ""
            entries.append(DataSourceEntry(
                name=name_without_ext,
                file_path=f"data/raw/{filename}",
                file_format=file_format,
                record_count=None,
                module=4,
            ))
        return entries

    def _parse_mapping_yaml(self, content: str) -> dict:
        """Parse a mapping YAML file with one level of nesting and lists.

        Handles:
        - Top-level key: value pairs (source_name, entity_type)
        - One-level nested dicts (field_mappings with key: value children)
        - Simple lists (transformations with ``- item`` children)
        - Comments and empty lines

        Args:
            content: Raw YAML string from a mapping spec file.

        Returns:
            Dict with top-level keys mapped to scalars, nested dicts, or lists.
        """
        result: dict = {}
        current_key: str | None = None
        current_type: str | None = None  # "dict", "list", or None

        for line in content.splitlines():
            # Skip empty lines and comments
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Determine indentation level
            indent = len(line) - len(line.lstrip())

            if indent == 0 and ":" in stripped:
                # Top-level key
                key, _, raw_value = stripped.partition(":")
                key = key.strip()
                if not key:
                    continue
                value = raw_value.strip()
                if value:
                    # Scalar value on same line
                    scalar = self._parse_yaml_scalar(value)
                    result[key] = scalar if scalar is not None else value
                    current_key = None
                    current_type = None
                else:
                    # Value will be on subsequent indented lines (dict or list)
                    current_key = key
                    current_type = None
                    result[key] = None  # placeholder
            elif current_key is not None and indent > 0:
                # Indented content belonging to current_key
                if stripped.startswith("- "):
                    # List item
                    if current_type is None:
                        current_type = "list"
                        result[current_key] = []
                    item_value = stripped[2:].strip()
                    # Strip quotes from list items
                    if (
                        len(item_value) >= 2
                        and item_value[0] == item_value[-1]
                        and item_value[0] in ("'", '"')
                    ):
                        item_value = item_value[1:-1]
                    result[current_key].append(item_value)
                elif ":" in stripped:
                    # Nested key: value (one level of nesting)
                    if current_type is None:
                        current_type = "dict"
                        result[current_key] = {}
                    nested_key, _, nested_raw = stripped.partition(":")
                    nested_key = nested_key.strip()
                    nested_value = nested_raw.strip()
                    if not nested_key:
                        continue
                    # Strip quotes from nested values
                    if (
                        len(nested_value) >= 2
                        and nested_value[0] == nested_value[-1]
                        and nested_value[0] in ("'", '"')
                    ):
                        nested_value = nested_value[1:-1]
                    if nested_value.lower() in ("null", "none", "~", ""):
                        nested_value = ""
                    result[current_key][nested_key] = nested_value

        return result

    def collect_mappings(self) -> list[MappingDecision]:
        """Read mapping specs from config/ and data/transformed/.

        Looks for files containing "mapping" in their filename within the
        config/ directory. Parses each as YAML to extract source_name,
        entity_type, field_mappings, and transformations. Falls back to
        checking data/transformed/ for transformation scripts if no mapping
        files are found in config/.

        Returns:
            List of MappingDecision instances (module=5). Returns empty list
            if no mapping information is found.
        """
        mappings: list[MappingDecision] = []

        # Look for mapping files in config/
        config_dir = os.path.join(self.project_root, "config")
        config_files = self._list_dir(config_dir)

        mapping_files = [
            f for f in config_files
            if "mapping" in f.lower() and (f.endswith(".yaml") or f.endswith(".yml"))
        ]

        for filename in sorted(mapping_files):
            file_path = os.path.join(config_dir, filename)
            content = self._read_file(file_path)
            if content is None:
                continue

            data = self._parse_mapping_yaml(content)

            # Extract source_name: from file content or infer from filename
            source_name = data.get("source_name")
            if not source_name or not isinstance(source_name, str):
                # Infer from filename: strip "mapping" and extension
                name_without_ext = os.path.splitext(filename)[0]
                # Remove "mapping" prefix/suffix and underscores/hyphens
                inferred = name_without_ext.replace("mapping", "").strip("_- ")
                source_name = inferred if inferred else name_without_ext

            # Extract entity_type
            entity_type = data.get("entity_type", "")
            if not isinstance(entity_type, str):
                entity_type = str(entity_type) if entity_type else ""

            # Extract field_mappings (nested dict)
            field_mappings_raw = data.get("field_mappings")
            field_mappings: dict[str, str] = {}
            if isinstance(field_mappings_raw, dict):
                for k, v in field_mappings_raw.items():
                    field_mappings[str(k)] = str(v) if v else ""

            # Extract transformations (list)
            transformations_raw = data.get("transformations")
            transformations: list[str] = []
            if isinstance(transformations_raw, list):
                transformations = [str(t) for t in transformations_raw if t]

            mappings.append(MappingDecision(
                source_name=source_name,
                entity_type=entity_type,
                field_mappings=field_mappings,
                transformations=transformations,
                module=5,
            ))

        if mappings:
            return mappings

        # Fallback: check data/transformed/ for transformation scripts
        transformed_dir = os.path.join(self.project_root, "data", "transformed")
        transformed_files = self._list_dir(transformed_dir)

        for filename in sorted(transformed_files):
            # Skip hidden files
            if filename.startswith("."):
                continue
            # Try to extract mapping intent from filename
            name_without_ext = os.path.splitext(filename)[0]
            # Infer source name from filename (e.g., "transform_crm" -> "crm")
            source_name = name_without_ext
            for prefix in ("transform_", "map_", "convert_"):
                if source_name.lower().startswith(prefix):
                    source_name = source_name[len(prefix):]
                    break

            mappings.append(MappingDecision(
                source_name=source_name,
                entity_type="",
                field_mappings={},
                transformations=[f"Transformation script: {filename}"],
                module=5,
            ))

        return mappings

    def collect_loading_config(self) -> LoadingConfig | None:
        """Infer loading strategy from src/load/ scripts.

        Scans the src/load/ directory for script files and determines:
        - Strategy: single_source (1 script) or multi_source (2+ scripts)
        - Redo processing: detected by "redo" in filenames or file content

        Returns:
            A LoadingConfig instance with inferred strategy and script list,
            or None if no loading scripts are found.
        """
        load_dir = os.path.join(self.project_root, "src", "load")
        all_files = self._list_dir(load_dir)

        # Filter to recognized script extensions
        script_extensions = (".py", ".java", ".cs", ".rs", ".ts")
        scripts = [
            f for f in all_files
            if any(f.endswith(ext) for ext in script_extensions)
        ]

        if not scripts:
            return None

        # Determine strategy based on script count
        strategy = "single_source" if len(scripts) == 1 else "multi_source"

        # Check for redo processing
        redo_processing: bool | None = None
        for filename in scripts:
            # Check filename for "redo"
            if "redo" in filename.lower():
                redo_processing = True
                break
            # Check file content for "redo" (if readable)
            file_path = os.path.join(load_dir, filename)
            content = self._read_file(file_path)
            if content is not None and "redo" in content.lower():
                redo_processing = True
                break

        # Collect script filenames as relative paths
        script_files = [f"src/load/{f}" for f in sorted(scripts)]

        return LoadingConfig(
            strategy=strategy,
            redo_processing=redo_processing,
            redo_reason=None,
            script_files=script_files,
            module=6,
        )

    def collect_query_programs(self) -> list[QueryProgram]:
        """Scan src/query/ for scripts and extract metadata.

        Scans the src/query/ directory for script files and extracts:
        - query_type: inferred from filename keywords
        - description: extracted from the first comment/docstring in the file

        Returns:
            Sorted list of QueryProgram instances (module=7). Returns empty
            list if no query scripts are found.
        """
        query_dir = os.path.join(self.project_root, "src", "query")
        all_files = self._list_dir(query_dir)

        # Filter to recognized script extensions
        script_extensions = (".py", ".java", ".cs", ".rs", ".ts")
        scripts = [
            f for f in all_files
            if any(f.endswith(ext) for ext in script_extensions)
        ]

        if not scripts:
            return []

        programs: list[QueryProgram] = []
        for filename in scripts:
            query_type = self._infer_query_type(filename)
            file_path = os.path.join(query_dir, filename)
            description = self._extract_description(file_path, filename)
            programs.append(QueryProgram(
                filename=f"src/query/{filename}",
                query_type=query_type,
                description=description,
                module=7,
            ))

        return sorted(programs, key=lambda p: p.filename)

    @staticmethod
    def _infer_query_type(filename: str) -> str:
        """Infer the query type from a script filename.

        Args:
            filename: The script filename (e.g., "search_by_name.py").

        Returns:
            A query type string based on keyword matching in the filename.
        """
        name_lower = filename.lower()
        if "search" in name_lower:
            return "search_by_attributes"
        if "get_entity" in name_lower or "entity" in name_lower:
            return "get_entity"
        if "relationship" in name_lower or "network" in name_lower:
            return "find_relationships"
        if "how" in name_lower:
            return "how_entity"
        if "why" in name_lower:
            return "why_entity"
        return "unknown"

    def _extract_description(self, file_path: str, filename: str) -> str:
        """Extract description from the first comment or docstring in a file.

        For Python files: looks for the first module docstring (triple quotes)
        or first # comment line.
        For other languages: looks for the first // comment or first line of
        a /* */ block comment.

        Args:
            file_path: Absolute path to the script file.
            filename: The filename used to determine language.

        Returns:
            The extracted description string, or "Query program" as default.
        """
        content = self._read_file(file_path)
        if content is None:
            return "Query program"

        if filename.endswith(".py"):
            return self._extract_python_description(content)
        return self._extract_other_description(content)

    @staticmethod
    def _extract_python_description(content: str) -> str:
        """Extract description from a Python file's docstring or comment.

        Args:
            content: The full file content.

        Returns:
            First meaningful line from docstring or # comment, or default.
        """
        for line in content.splitlines():
            stripped = line.strip()
            # Skip empty lines and shebang
            if not stripped or stripped.startswith("#!"):
                continue
            # Check for triple-quote docstring
            if stripped.startswith('"""') or stripped.startswith("'''"):
                quote = stripped[:3]
                # Single-line docstring: """text"""
                if stripped.count(quote) >= 2 and len(stripped) > 6:
                    return stripped[3:stripped.index(quote, 3)].strip()
                # Multi-line docstring: first content line
                rest = stripped[3:].strip()
                if rest:
                    return rest
                # Look at subsequent lines for content
                lines = content.splitlines()
                start_idx = lines.index(line) + 1
                for subsequent in lines[start_idx:]:
                    sub_stripped = subsequent.strip()
                    if sub_stripped and not sub_stripped.startswith(quote):
                        return sub_stripped
                    if sub_stripped.startswith(quote) or sub_stripped.endswith(quote):
                        break
                return "Query program"
            # Check for # comment
            if stripped.startswith("#"):
                comment_text = stripped.lstrip("#").strip()
                if comment_text:
                    return comment_text
                continue
            # Non-comment, non-docstring line reached — stop looking
            break
        return "Query program"

    @staticmethod
    def _extract_other_description(content: str) -> str:
        """Extract description from a non-Python file's comments.

        Looks for // single-line comments or /* */ block comments.

        Args:
            content: The full file content.

        Returns:
            First meaningful comment text, or "Query program" as default.
        """
        for line in content.splitlines():
            stripped = line.strip()
            # Skip empty lines
            if not stripped:
                continue
            # Check for // comment
            if stripped.startswith("//"):
                comment_text = stripped[2:].strip()
                if comment_text:
                    return comment_text
                continue
            # Check for /* block comment
            if stripped.startswith("/*"):
                # Extract text after /*
                rest = stripped[2:].strip()
                # Remove trailing */ if on same line
                if rest.endswith("*/"):
                    rest = rest[:-2].strip()
                if rest:
                    return rest
                # Multi-line block: look at next lines
                lines = content.splitlines()
                start_idx = lines.index(line) + 1
                for subsequent in lines[start_idx:]:
                    sub_stripped = subsequent.strip()
                    # Strip leading * from block comment continuation
                    if sub_stripped.startswith("*"):
                        sub_stripped = sub_stripped[1:].strip()
                    if sub_stripped.endswith("*/"):
                        sub_stripped = sub_stripped[:-2].strip()
                    if sub_stripped:
                        return sub_stripped
                    if "*/" in subsequent:
                        break
                return "Query program"
            # Non-comment line reached — stop looking
            break
        return "Query program"

    def collect_business_problem(self) -> BusinessProblem | None:
        """Extract Module 1 data from docs/bootcamp_journal.md.

        Reads the bootcamp journal and parses the Module 1 section to extract:
        - Problem statement: text after a ### Problem Statement heading or
          the first paragraph of Module 1 content
        - Identified sources: list items after ### Data Sources or
          ### Identified Sources
        - Success criteria: list items after ### Success Criteria

        Returns:
            A BusinessProblem instance with module=1, or None if the journal
            doesn't exist or has no Module 1 section.
        """
        path = os.path.join(self.project_root, "docs", "bootcamp_journal.md")
        content = self._read_file(path)
        if content is None:
            return None

        # Extract Module 1 content between its heading and the next ## Module heading
        module1_content = self._extract_module1_section(content)
        if module1_content is None:
            return None

        # Parse subsections from Module 1 content
        problem_statement = self._extract_problem_statement(module1_content)
        identified_sources = self._extract_list_section(
            module1_content, ("data sources", "identified sources")
        )
        success_criteria = self._extract_list_section(
            module1_content, ("success criteria",)
        )

        return BusinessProblem(
            problem_statement=problem_statement,
            identified_sources=identified_sources,
            success_criteria=success_criteria,
            module=1,
        )

    @staticmethod
    def _extract_module1_section(content: str) -> str | None:
        """Extract the Module 1 section content from the journal.

        Looks for a heading like '## Module 1: Business Problem' or
        '## Module 1' and captures everything until the next '## Module'
        heading.

        Args:
            content: Full journal markdown content.

        Returns:
            The text content of the Module 1 section, or None if not found.
        """
        lines = content.splitlines()
        start_idx: int | None = None
        end_idx: int | None = None

        # Pattern: ## Module 1 (optionally followed by : and description)
        module1_pattern = re.compile(r"^##\s+Module\s+1\b", re.IGNORECASE)
        # Pattern: ## Module N (any module heading after Module 1)
        next_module_pattern = re.compile(r"^##\s+Module\s+\d", re.IGNORECASE)

        for i, line in enumerate(lines):
            if start_idx is None:
                if module1_pattern.match(line.strip()):
                    start_idx = i + 1
            else:
                if next_module_pattern.match(line.strip()):
                    end_idx = i
                    break

        if start_idx is None:
            return None

        if end_idx is None:
            end_idx = len(lines)

        section = "\n".join(lines[start_idx:end_idx]).strip()
        return section if section else None

    @staticmethod
    def _extract_problem_statement(module1_content: str) -> str | None:
        """Extract the problem statement from Module 1 content.

        Looks for a ### Problem Statement heading and takes the text after it.
        If no such heading exists, uses the first non-empty paragraph.

        Args:
            module1_content: The extracted Module 1 section text.

        Returns:
            The problem statement text, or None if no content found.
        """
        lines = module1_content.splitlines()

        # Look for ### Problem Statement heading
        problem_heading_pattern = re.compile(
            r"^###\s+Problem\s+Statement", re.IGNORECASE
        )
        for i, line in enumerate(lines):
            if problem_heading_pattern.match(line.strip()):
                # Collect text after this heading until next ### or end
                text_lines: list[str] = []
                for subsequent in lines[i + 1:]:
                    if subsequent.strip().startswith("###"):
                        break
                    text_lines.append(subsequent)
                # Join and strip to get the paragraph
                text = "\n".join(text_lines).strip()
                return text if text else None

        # Fallback: use the first non-empty paragraph (before any ### heading)
        paragraph_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("###"):
                break
            if stripped:
                paragraph_lines.append(stripped)
            elif paragraph_lines:
                # End of first paragraph (hit empty line after content)
                break

        if paragraph_lines:
            return " ".join(paragraph_lines)
        return None

    @staticmethod
    def _extract_list_section(
        module1_content: str, heading_keywords: tuple[str, ...]
    ) -> list[str]:
        """Extract list items from a subsection matching given heading keywords.

        Looks for a ### heading containing one of the keywords, then collects
        markdown list items (lines starting with '- ' or '* ') until the next
        ### heading or end of content.

        Args:
            module1_content: The extracted Module 1 section text.
            heading_keywords: Tuple of lowercase keywords to match in headings.

        Returns:
            List of extracted item strings. Empty list if section not found.
        """
        lines = module1_content.splitlines()
        section_start: int | None = None

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("###"):
                heading_text = stripped.lstrip("#").strip().lower()
                if any(kw in heading_text for kw in heading_keywords):
                    section_start = i + 1
                    break

        if section_start is None:
            return []

        items: list[str] = []
        for line in lines[section_start:]:
            stripped = line.strip()
            if stripped.startswith("###"):
                break
            if stripped.startswith("- ") or stripped.startswith("* "):
                item_text = stripped[2:].strip()
                if item_text:
                    items.append(item_text)

        return items

    def collect_performance_tuning(self) -> PerformanceTuning | None:
        """Extract Module 8 performance tuning decisions if completed.

        Looks for evidence of performance work:
        - Files in tests/performance/ directory
        - Module 8 entries in docs/bootcamp_journal.md

        Returns:
            A PerformanceTuning instance with module=8, or None if no
            performance tuning evidence is found.
        """
        tuning_decisions: list[str] = []
        optimizations_applied: list[str] = []
        baseline_metrics: dict[str, str] | None = None

        # Check tests/performance/ directory for performance test files
        perf_dir = os.path.join(self.project_root, "tests", "performance")
        perf_files = self._list_dir(perf_dir)
        perf_scripts = [f for f in perf_files if not f.startswith(".")]

        if perf_scripts:
            tuning_decisions.append(
                f"Performance test files created: {', '.join(sorted(perf_scripts))}"
            )

        # Check journal for Module 8 entries
        journal_path = os.path.join(self.project_root, "docs", "bootcamp_journal.md")
        journal_content = self._read_file(journal_path)
        if journal_content is not None:
            module8_content = self._extract_module_section(journal_content, 8)
            if module8_content is not None:
                # Extract list items as tuning decisions/optimizations
                for line in module8_content.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("- ") or stripped.startswith("* "):
                        item = stripped[2:].strip()
                        if item:
                            # Categorize: items mentioning "baseline" or "metric"
                            # go to metrics, others to optimizations
                            item_lower = item.lower()
                            if "baseline" in item_lower or "metric" in item_lower:
                                if baseline_metrics is None:
                                    baseline_metrics = {}
                                baseline_metrics[f"metric_{len(baseline_metrics) + 1}"] = item
                            elif "optimiz" in item_lower or "improv" in item_lower:
                                optimizations_applied.append(item)
                            else:
                                tuning_decisions.append(item)

        # Return None if no evidence found
        if not tuning_decisions and not optimizations_applied and baseline_metrics is None:
            return None

        return PerformanceTuning(
            tuning_decisions=tuning_decisions,
            baseline_metrics=baseline_metrics,
            optimizations_applied=optimizations_applied,
            module=8,
        )

    def collect_security_hardening(self) -> SecurityHardening | None:
        """Extract Module 9 security hardening decisions if completed.

        Looks for docs/security_checklist.md and counts checklist items
        (lines with ``- [x]`` or ``- [ ]``). Extracts security choices
        from checked items.

        Returns:
            A SecurityHardening instance with module=9, or None if no
            security checklist is found.
        """
        checklist_path = os.path.join(
            self.project_root, "docs", "security_checklist.md"
        )
        content = self._read_file(checklist_path)
        if content is None:
            return None

        choices: list[str] = []
        items_completed = 0
        items_total = 0

        for line in content.splitlines():
            stripped = line.strip()
            # Match checked items: - [x] or - [X]
            if re.match(r"^-\s*\[[xX]\]", stripped):
                items_total += 1
                items_completed += 1
                # Extract the text after the checkbox
                item_text = re.sub(r"^-\s*\[[xX]\]\s*", "", stripped).strip()
                if item_text:
                    choices.append(item_text)
            # Match unchecked items: - [ ]
            elif re.match(r"^-\s*\[\s\]", stripped):
                items_total += 1

        # Return None if no checklist items found at all
        if items_total == 0:
            return None

        return SecurityHardening(
            choices=choices,
            checklist_items_completed=items_completed,
            checklist_items_total=items_total,
            module=9,
        )

    def collect_monitoring_config(self) -> MonitoringConfig | None:
        """Extract Module 10 monitoring configuration if completed.

        Looks for monitoring evidence in:
        - Module 10 entries in docs/bootcamp_journal.md
        - Config files with "monitor" in the name

        Returns:
            A MonitoringConfig instance with module=10, or None if no
            monitoring evidence is found.
        """
        tools_chosen: list[str] = []
        alert_configurations: list[str] = []

        # Check journal for Module 10 entries
        journal_path = os.path.join(self.project_root, "docs", "bootcamp_journal.md")
        journal_content = self._read_file(journal_path)
        if journal_content is not None:
            module10_content = self._extract_module_section(journal_content, 10)
            if module10_content is not None:
                for line in module10_content.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("- ") or stripped.startswith("* "):
                        item = stripped[2:].strip()
                        if item:
                            item_lower = item.lower()
                            if "alert" in item_lower or "notify" in item_lower:
                                alert_configurations.append(item)
                            else:
                                tools_chosen.append(item)

        # Check for monitoring config files in config/
        config_dir = os.path.join(self.project_root, "config")
        config_files = self._list_dir(config_dir)
        monitor_files = [
            f for f in config_files
            if "monitor" in f.lower() and (f.endswith(".yaml") or f.endswith(".yml"))
        ]

        for filename in sorted(monitor_files):
            file_path = os.path.join(config_dir, filename)
            content = self._read_file(file_path)
            if content is None:
                continue
            data = self._parse_simple_yaml(content)
            # Extract tool and alert info from config
            for key, value in data.items():
                if value is None:
                    continue
                key_lower = key.lower()
                if "tool" in key_lower:
                    tools_chosen.append(value)
                elif "alert" in key_lower:
                    alert_configurations.append(value)

        # Return None if no evidence found
        if not tools_chosen and not alert_configurations:
            return None

        return MonitoringConfig(
            tools_chosen=tools_chosen,
            alert_configurations=alert_configurations,
            module=10,
        )

    def collect_deployment(self) -> DeploymentDecision | None:
        """Extract Module 11 deployment decisions if completed.

        Looks for docs/deployment_plan.md or deployment-related config files.
        Extracts target, infrastructure choices, and deployment method.

        Returns:
            A DeploymentDecision instance with module=11, or None if no
            deployment evidence is found.
        """
        # Check docs/deployment_plan.md first
        deploy_path = os.path.join(
            self.project_root, "docs", "deployment_plan.md"
        )
        content = self._read_file(deploy_path)
        if content is not None:
            return self._parse_deployment_plan(content)

        # Fallback: check for deployment config files
        config_dir = os.path.join(self.project_root, "config")
        config_files = self._list_dir(config_dir)
        deploy_files = [
            f for f in config_files
            if "deploy" in f.lower() and (f.endswith(".yaml") or f.endswith(".yml"))
        ]

        for filename in sorted(deploy_files):
            file_path = os.path.join(config_dir, filename)
            file_content = self._read_file(file_path)
            if file_content is None:
                continue
            data = self._parse_simple_yaml(file_content)
            target = data.get("target", data.get("platform", ""))
            if not target:
                continue
            infrastructure: list[str] = []
            method: str | None = None
            for key, value in data.items():
                if value is None:
                    continue
                key_lower = key.lower()
                if "method" in key_lower or "strategy" in key_lower:
                    method = value
                elif key_lower not in ("target", "platform"):
                    infrastructure.append(f"{key}: {value}")
            return DeploymentDecision(
                target=target,
                infrastructure_choices=infrastructure,
                deployment_method=method,
                module=11,
            )

        return None

    def _parse_deployment_plan(self, content: str) -> DeploymentDecision | None:
        """Parse a deployment plan markdown file for deployment decisions.

        Extracts target platform, infrastructure choices, and deployment method
        from the markdown content using heading-based sections and list items.

        Args:
            content: The full content of docs/deployment_plan.md.

        Returns:
            A DeploymentDecision instance, or None if no meaningful data found.
        """
        target: str = ""
        infrastructure_choices: list[str] = []
        deployment_method: str | None = None

        lines = content.splitlines()
        current_section: str = ""

        for line in lines:
            stripped = line.strip()
            # Track section headings
            if stripped.startswith("#"):
                heading_text = stripped.lstrip("#").strip().lower()
                current_section = heading_text
                continue

            # Extract list items based on current section
            if stripped.startswith("- ") or stripped.startswith("* "):
                item = stripped[2:].strip()
                if not item:
                    continue
                section_lower = current_section.lower()
                if "target" in section_lower or "platform" in section_lower:
                    if not target:
                        target = item
                    else:
                        infrastructure_choices.append(item)
                elif "infrastructure" in section_lower:
                    infrastructure_choices.append(item)
                elif "method" in section_lower or "strategy" in section_lower:
                    if deployment_method is None:
                        deployment_method = item
                else:
                    # General items — try to categorize
                    item_lower = item.lower()
                    if not target and any(
                        kw in item_lower
                        for kw in ("aws", "azure", "gcp", "kubernetes", "on-prem")
                    ):
                        target = item
                    else:
                        infrastructure_choices.append(item)
            # Check for key: value patterns in non-list lines
            elif ":" in stripped and not stripped.startswith("#"):
                key, _, value = stripped.partition(":")
                key = key.strip().lower()
                value = value.strip()
                if not value:
                    continue
                if key in ("target", "platform"):
                    if not target:
                        target = value
                elif key in ("method", "deployment_method", "strategy"):
                    if deployment_method is None:
                        deployment_method = value

        # Return None if no meaningful data extracted
        if not target and not infrastructure_choices and deployment_method is None:
            return None

        # Default target if we have other data but no explicit target
        if not target:
            target = "unknown"

        return DeploymentDecision(
            target=target,
            infrastructure_choices=infrastructure_choices,
            deployment_method=deployment_method,
            module=11,
        )

    def collect_all(self) -> CollectedDecisions:
        """Collect all decisions from available sources.

        Orchestrates all individual collector methods in sequence, populating
        warnings for missing files. Never raises an exception — any unexpected
        error from an individual collector is caught and added as a warning.

        Returns:
            A CollectedDecisions instance with all collected data and warnings.
        """
        warnings: list[str] = []

        # collect_preferences
        preferences: PreferencesData | None = None
        try:
            preferences = self.collect_preferences()
            if preferences is None:
                warnings.append(
                    "config/bootcamp_preferences.yaml not found"
                )
        except Exception as exc:
            warnings.append(f"Error collecting preferences: {exc}")

        # collect_progress
        progress: ProgressData | None = None
        try:
            progress = self.collect_progress()
            if progress is None:
                warnings.append(
                    "config/bootcamp_progress.json not found"
                )
        except Exception as exc:
            warnings.append(f"Error collecting progress: {exc}")

        # collect_data_sources
        data_sources: list[DataSourceEntry] = []
        try:
            data_sources = self.collect_data_sources()
            if not data_sources:
                warnings.append("No data sources found")
        except Exception as exc:
            warnings.append(f"Error collecting data_sources: {exc}")

        # collect_mappings
        mappings: list[MappingDecision] = []
        try:
            mappings = self.collect_mappings()
            if not mappings:
                warnings.append("No mapping specifications found")
        except Exception as exc:
            warnings.append(f"Error collecting mappings: {exc}")

        # collect_loading_config
        loading_config: LoadingConfig | None = None
        try:
            loading_config = self.collect_loading_config()
            if loading_config is None:
                warnings.append("No loading scripts found in src/load/")
        except Exception as exc:
            warnings.append(f"Error collecting loading_config: {exc}")

        # collect_query_programs
        query_programs: list[QueryProgram] = []
        try:
            query_programs = self.collect_query_programs()
            if not query_programs:
                warnings.append(
                    "No query programs found in src/query/"
                )
        except Exception as exc:
            warnings.append(f"Error collecting query_programs: {exc}")

        # collect_business_problem
        business_problem: BusinessProblem | None = None
        try:
            business_problem = self.collect_business_problem()
            if business_problem is None:
                warnings.append(
                    "docs/bootcamp_journal.md not found or no Module 1 section"
                )
        except Exception as exc:
            warnings.append(f"Error collecting business_problem: {exc}")

        # collect_performance_tuning (optional — no warning if None)
        performance_tuning: PerformanceTuning | None = None
        try:
            performance_tuning = self.collect_performance_tuning()
        except Exception as exc:
            warnings.append(f"Error collecting performance_tuning: {exc}")

        # collect_security_hardening (optional — no warning if None)
        security_hardening: SecurityHardening | None = None
        try:
            security_hardening = self.collect_security_hardening()
        except Exception as exc:
            warnings.append(f"Error collecting security_hardening: {exc}")

        # collect_monitoring_config (optional — no warning if None)
        monitoring_config: MonitoringConfig | None = None
        try:
            monitoring_config = self.collect_monitoring_config()
        except Exception as exc:
            warnings.append(f"Error collecting monitoring_config: {exc}")

        # collect_deployment (optional — no warning if None)
        deployment: DeploymentDecision | None = None
        try:
            deployment = self.collect_deployment()
        except Exception as exc:
            warnings.append(f"Error collecting deployment: {exc}")

        return CollectedDecisions(
            preferences=preferences,
            progress=progress,
            business_problem=business_problem,
            data_sources=data_sources,
            mappings=mappings,
            loading_config=loading_config,
            query_programs=query_programs,
            performance_tuning=performance_tuning,
            security_hardening=security_hardening,
            monitoring_config=monitoring_config,
            deployment=deployment,
            warnings=warnings,
        )

    @staticmethod
    def _extract_module_section(content: str, module_number: int) -> str | None:
        """Extract a specific module section from the bootcamp journal.

        Looks for a heading like '## Module N' and captures everything until
        the next '## Module' heading or end of content.

        Args:
            content: Full journal markdown content.
            module_number: The module number to extract (e.g., 8, 10).

        Returns:
            The text content of the module section, or None if not found.
        """
        lines = content.splitlines()
        start_idx: int | None = None
        end_idx: int | None = None

        module_pattern = re.compile(
            rf"^##\s+Module\s+{module_number}\b", re.IGNORECASE
        )
        next_module_pattern = re.compile(r"^##\s+Module\s+\d", re.IGNORECASE)

        for i, line in enumerate(lines):
            if start_idx is None:
                if module_pattern.match(line.strip()):
                    start_idx = i + 1
            else:
                if next_module_pattern.match(line.strip()):
                    end_idx = i
                    break

        if start_idx is None:
            return None

        if end_idx is None:
            end_idx = len(lines)

        section = "\n".join(lines[start_idx:end_idx]).strip()
        return section if section else None


# ---------------------------------------------------------------------------
# Manifest Assembler
# ---------------------------------------------------------------------------


class ManifestAssembler:
    """Builds the Decision Manifest from collected data.

    Combines all collected decisions into a structured DecisionManifest
    ready for sanitization and serialization.
    """

    SCHEMA_VERSION = SCHEMA_VERSION
    POWER_VERSION = POWER_VERSION

    def assemble(self, decisions: CollectedDecisions) -> DecisionManifest:
        """Assemble full manifest from collected decisions.

        Args:
            decisions: The collected decisions from all project sources.

        Returns:
            A DecisionManifest instance with all sections populated.
        """
        metadata = self._build_metadata()
        track_progress = self._build_track_progress(
            decisions.progress, decisions.preferences
        )

        # Build sdk_setup from preferences
        sdk_setup: dict | None = None
        if decisions.preferences is not None:
            sdk_setup = {
                "module": 2,
                "language": decisions.preferences.language,
                "database_type": decisions.preferences.database_type,
                "deployment_target": decisions.preferences.deployment_target,
                "cloud_provider": decisions.preferences.cloud_provider,
            }

        # Convert data_sources list to list of dicts
        data_sources = [dataclasses.asdict(ds) for ds in decisions.data_sources]

        # Convert mappings list to list of dicts
        mapping_decisions = [dataclasses.asdict(m) for m in decisions.mappings]

        # Convert loading_config to dict if not None
        loading_config: dict | None = None
        if decisions.loading_config is not None:
            loading_config = dataclasses.asdict(decisions.loading_config)

        # Convert query_programs list to list of dicts
        query_programs = [dataclasses.asdict(qp) for qp in decisions.query_programs]

        # Convert business_problem to dict if not None
        business_problem: dict | None = None
        if decisions.business_problem is not None:
            business_problem = dataclasses.asdict(decisions.business_problem)

        # Build optional sections (modules 8-11)
        optional = self._build_optional_sections(decisions)

        # Build replay notes
        replay_notes = self._build_replay_notes(decisions)

        return DecisionManifest(
            metadata=metadata,
            track_progress=track_progress,
            business_problem=business_problem,
            sdk_setup=sdk_setup,
            data_sources=data_sources,
            mapping_decisions=mapping_decisions,
            loading_config=loading_config,
            query_programs=query_programs,
            performance_tuning=optional.get("performance_tuning"),
            security_hardening=optional.get("security_hardening"),
            monitoring_config=optional.get("monitoring_config"),
            deployment=optional.get("deployment"),
            replay_notes=replay_notes,
        )

    def _build_metadata(self) -> dict:
        """Generate metadata section with timestamp, versions.

        Returns:
            Dict with schema_version, generated_at (ISO 8601 UTC),
            and power_version.
        """
        return generate_metadata()

    def _build_track_progress(
        self,
        progress: ProgressData | None,
        preferences: PreferencesData | None,
    ) -> dict:
        """Build track_progress section.

        Args:
            progress: Module completion state, or None if unavailable.
            preferences: Bootcamper preferences, or None if unavailable.

        Returns:
            Dict with track_name, track_id, total_modules_in_track,
            modules_completed, modules_skipped, and elapsed_time.
        """
        # Track name mapping
        track_names: dict[str, str] = {
            "core_bootcamp": "Core Bootcamp",
            "advanced_topics": "Advanced Topics",
        }
        # Total modules per track
        track_module_counts: dict[str, int] = {
            "core_bootcamp": 7,
            "advanced_topics": 11,
        }

        # Derive track info from preferences
        track_id: str | None = None
        track_name = "Unknown"
        total_modules: int | None = None

        if preferences is not None and preferences.track is not None:
            track_id = preferences.track
            track_name = track_names.get(preferences.track, "Unknown")
            total_modules = track_module_counts.get(preferences.track)

        # Build modules_completed list
        modules_completed: list[dict] = []
        if progress is not None:
            for module_num in progress.modules_completed:
                entry: dict = {"module": module_num}
                # Check step_history for completed_at timestamp
                if progress.step_history is not None:
                    module_key = str(module_num)
                    step_data = progress.step_history.get(module_key)
                    if isinstance(step_data, dict) and "completed_at" in step_data:
                        entry["completed_at"] = step_data["completed_at"]
                modules_completed.append(entry)

        return {
            "track_name": track_name,
            "track_id": track_id,
            "total_modules_in_track": total_modules,
            "modules_completed": modules_completed,
            "modules_skipped": [],
            "elapsed_time": None,
        }

    def _build_optional_sections(self, decisions: CollectedDecisions) -> dict:
        """Build sections for modules 8-11 only if completed.

        Checks each optional module's data in decisions and includes it
        only when the corresponding dataclass is not None. Omits sections
        entirely when the module was not completed.

        Args:
            decisions: The collected decisions containing optional module data.

        Returns:
            Dict with keys for each optional section that has data.
            Keys are only present when the corresponding module was completed.
        """
        result: dict = {}

        if decisions.performance_tuning is not None:
            result["performance_tuning"] = dataclasses.asdict(decisions.performance_tuning)

        if decisions.security_hardening is not None:
            result["security_hardening"] = dataclasses.asdict(decisions.security_hardening)

        if decisions.monitoring_config is not None:
            result["monitoring_config"] = dataclasses.asdict(decisions.monitoring_config)

        if decisions.deployment is not None:
            result["deployment"] = dataclasses.asdict(decisions.deployment)

        return result

    def _build_replay_notes(self, decisions: CollectedDecisions) -> list[str]:
        """Identify decisions that need manual input on replay.

        Analyzes collected decisions and identifies which ones would need
        manual input during a theoretical replay.

        Args:
            decisions: The collected decisions to analyze for replay notes.

        Returns:
            List of replay note strings describing items needing manual input.
        """
        notes: list[str] = []

        # 1. Business problem extracted from journal prose
        if (
            decisions.business_problem is not None
            and decisions.business_problem.problem_statement
        ):
            notes.append(
                "Business problem statement was extracted from journal prose"
                " — verify accuracy before replay"
            )

        # 2. Mapping transformations in natural language
        if decisions.mappings:
            has_transformations = any(
                mapping.transformations for mapping in decisions.mappings
            )
            if has_transformations:
                notes.append(
                    "Mapping transformations described in natural language"
                    " — may need manual translation to code"
                )

        # 3. Preferences file missing
        if decisions.preferences is None:
            notes.append(
                "Preferences file was not found"
                " — language and track choices will need manual input on replay"
            )

        # 4. Progress file missing
        if decisions.progress is None:
            notes.append(
                "Progress file was not found"
                " — module completion state will need manual verification on replay"
            )

        # 5. Warnings mentioning "not found"
        for warning in decisions.warnings:
            if "not found" in warning:
                notes.append(warning)

        return notes


# ---------------------------------------------------------------------------
# Manifest Writer
# ---------------------------------------------------------------------------


class ManifestWriter:
    """Writes the Decision Manifest to YAML.

    Serializes a DecisionManifest to human-readable YAML format using a
    custom serializer (no PyYAML dependency). Handles writing to disk with
    overwrite protection.
    """

    HEADER_COMMENT = (
        "# Bootcamp Decision Record\n"
        "# Generated by Senzing Bootcamp Power\n"
        "# This file captures all decisions made during the bootcamp.\n"
        "# It can be shared with colleagues or used to replay the same setup.\n"
    )

    # Characters that require quoting a YAML string value
    _SPECIAL_CHARS = set(':#{}[],&*?|-<>=!%@\n')

    def to_yaml(self, manifest: DecisionManifest) -> str:
        """Serialize manifest to YAML string with header comments.

        Converts the manifest to a dict via dataclasses.asdict() and
        serializes to YAML format with a custom serializer.

        Args:
            manifest: The decision manifest to serialize.

        Returns:
            A YAML string with header comments and 2-space indentation.
        """
        manifest_dict = dataclasses.asdict(manifest)
        lines: list[str] = [self.HEADER_COMMENT]
        self._serialize_dict(manifest_dict, lines, indent=0, top_level=True)
        return "\n".join(lines) + "\n"

    def _serialize_dict(
        self, data: dict, lines: list[str], indent: int, top_level: bool = False
    ) -> None:
        """Serialize a dict to YAML lines.

        Args:
            data: The dictionary to serialize.
            lines: Accumulator list of output lines.
            indent: Current indentation level (number of spaces).
            top_level: Whether this is the root-level dict (adds blank lines
                between sections).
        """
        prefix = " " * indent
        first = True
        for key, value in data.items():
            # Skip None values entirely (don't output the key)
            if value is None:
                continue
            # Add blank line between top-level sections for readability
            if top_level and not first:
                lines.append("")
            first = False
            if isinstance(value, dict):
                if not value:
                    lines.append(f"{prefix}{key}: {{}}")
                else:
                    lines.append(f"{prefix}{key}:")
                    self._serialize_dict(value, lines, indent + 2)
            elif isinstance(value, list):
                if not value:
                    lines.append(f"{prefix}{key}: []")
                else:
                    lines.append(f"{prefix}{key}:")
                    self._serialize_list(value, lines, indent + 2)
            else:
                formatted = self._format_scalar(value)
                lines.append(f"{prefix}{key}: {formatted}")

    def _serialize_list(
        self, data: list, lines: list[str], indent: int
    ) -> None:
        """Serialize a list to YAML lines.

        Args:
            data: The list to serialize.
            lines: Accumulator list of output lines.
            indent: Current indentation level (number of spaces).
        """
        prefix = " " * indent
        for item in data:
            if isinstance(item, dict):
                if not item:
                    lines.append(f"{prefix}- {{}}")
                else:
                    # First key on same line as dash, rest indented
                    items_iter = iter(item.items())
                    first_key, first_value = next(items_iter)
                    # Skip None values in list dicts too
                    while first_value is None:
                        try:
                            first_key, first_value = next(items_iter)
                        except StopIteration:
                            # All values are None — emit empty dict
                            lines.append(f"{prefix}- {{}}")
                            break
                    else:
                        if isinstance(first_value, dict):
                            if not first_value:
                                lines.append(f"{prefix}- {first_key}: {{}}")
                            else:
                                lines.append(f"{prefix}- {first_key}:")
                                self._serialize_dict(
                                    first_value, lines, indent + 4
                                )
                        elif isinstance(first_value, list):
                            if not first_value:
                                lines.append(f"{prefix}- {first_key}: []")
                            else:
                                lines.append(f"{prefix}- {first_key}:")
                                self._serialize_list(
                                    first_value, lines, indent + 4
                                )
                        else:
                            formatted = self._format_scalar(first_value)
                            lines.append(
                                f"{prefix}- {first_key}: {formatted}"
                            )
                        # Remaining keys at indent + 2
                        remaining_prefix = " " * (indent + 2)
                        for k, v in items_iter:
                            if v is None:
                                continue
                            if isinstance(v, dict):
                                if not v:
                                    lines.append(
                                        f"{remaining_prefix}{k}: {{}}"
                                    )
                                else:
                                    lines.append(f"{remaining_prefix}{k}:")
                                    self._serialize_dict(
                                        v, lines, indent + 4
                                    )
                            elif isinstance(v, list):
                                if not v:
                                    lines.append(
                                        f"{remaining_prefix}{k}: []"
                                    )
                                else:
                                    lines.append(f"{remaining_prefix}{k}:")
                                    self._serialize_list(
                                        v, lines, indent + 4
                                    )
                            else:
                                formatted = self._format_scalar(v)
                                lines.append(
                                    f"{remaining_prefix}{k}: {formatted}"
                                )
            elif isinstance(item, list):
                # Nested list (rare but handle it)
                if not item:
                    lines.append(f"{prefix}- []")
                else:
                    # Serialize nested list items with extra indent
                    lines.append(f"{prefix}-")
                    self._serialize_list(item, lines, indent + 2)
            else:
                formatted = self._format_scalar(item)
                lines.append(f"{prefix}- {formatted}")

    def _format_scalar(self, value: object) -> str:
        """Format a scalar value for YAML output.

        Args:
            value: The value to format (str, int, float, bool, or None).

        Returns:
            A YAML-formatted string representation of the value.
        """
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return str(value)
        # String handling
        s = str(value)
        if self._needs_quoting(s):
            # Use double quotes with escaped internal double quotes
            escaped = s.replace("\\", "\\\\").replace('"', '\\"')
            escaped = escaped.replace("\n", "\\n")
            return f'"{escaped}"'
        return s

    def _needs_quoting(self, value: str) -> bool:
        """Determine if a string value needs quoting in YAML.

        Args:
            value: The string to check.

        Returns:
            True if the string contains special characters requiring quotes.
        """
        if not value:
            # Empty string needs quoting
            return True
        # Check for special characters
        for ch in value:
            if ch in self._SPECIAL_CHARS:
                return True
        # Check for values that look like YAML keywords
        lower = value.lower()
        if lower in ("true", "false", "yes", "no", "on", "off", "null", "~"):
            return True
        # Check if it looks like a number (would be parsed as int/float)
        try:
            float(value)
            return True
        except ValueError:
            pass
        return False

    def write(
        self, manifest: DecisionManifest, output_path: str, overwrite: bool = False
    ) -> str:
        """Write manifest to file with overwrite protection.

        Serializes the manifest to YAML and writes it to the specified path.
        Creates parent directories if they don't exist.

        Args:
            manifest: The decision manifest to write.
            output_path: File path to write the YAML output to.
            overwrite: If True, overwrite existing file. If False, raise
                FileExistsError when the file already exists.

        Returns:
            The output_path string.

        Raises:
            FileExistsError: If output_path exists and overwrite is False.
            PermissionError: If the file cannot be written (propagated).
        """
        # Check if file already exists
        if os.path.exists(output_path) and not overwrite:
            raise FileExistsError(
                f"Output file already exists: {output_path}. Use --overwrite to replace."
            )

        # Create parent directories if needed
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        # Serialize and write
        yaml_content = self.to_yaml(manifest)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        return output_path


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Parse args, collect decisions, assemble manifest, write output.

    Args:
        argv: Command-line arguments. Uses sys.argv if None.

    Returns:
        0 on success, 1 on error.
    """
    parser = argparse.ArgumentParser(
        description="Generate a structured YAML decision manifest from bootcamp project files."
    )
    parser.add_argument(
        "--output",
        "-o",
        default="docs/bootcamp_record.yaml",
        help="Output file path for the decision manifest (default: docs/bootcamp_record.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print manifest to stdout without writing to disk",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output file without prompting",
    )
    args = parser.parse_args(argv)

    try:
        # 1. Determine project root
        project_root = os.getcwd()

        # 2. Collect decisions
        collector = DecisionCollector(project_root)
        decisions = collector.collect_all()

        # 3. Assemble manifest
        assembler = ManifestAssembler()
        manifest = assembler.assemble(decisions)

        # 4. Sanitize
        sanitizer = SecuritySanitizer()
        manifest, sanitize_warnings = sanitizer.sanitize(manifest, project_root)

        # 4b. Print progress
        source_files_read = sum(1 for x in [
            decisions.preferences,
            decisions.progress,
            decisions.business_problem,
            decisions.loading_config,
        ] if x is not None) + sum(len(x) for x in [
            decisions.data_sources,
            decisions.mappings,
            decisions.query_programs,
        ])

        sections_generated = sum(1 for x in [
            manifest.business_problem,
            manifest.sdk_setup,
            manifest.loading_config,
            manifest.performance_tuning,
            manifest.security_hardening,
            manifest.monitoring_config,
            manifest.deployment,
        ] if x is not None) + sum(1 for x in [
            manifest.data_sources,
            manifest.mapping_decisions,
            manifest.query_programs,
        ] if x)

        all_warnings = decisions.warnings + sanitize_warnings

        print(f"Collected from {source_files_read} source files")
        print(f"Generated {sections_generated} manifest sections")
        print(f"{len(all_warnings)} warnings encountered")
        if all_warnings:
            for warning in all_warnings:
                print(f"  - {warning}")

        # 5. Handle dry-run
        if args.dry_run:
            writer = ManifestWriter()
            print(writer.to_yaml(manifest))
            return 0

        # 6. Handle overwrite check
        if os.path.exists(args.output) and not args.overwrite:
            print(f"Error: Output file already exists: {args.output}")
            print("Use --overwrite to replace the existing file.")
            return 1

        # 7. Write manifest
        writer = ManifestWriter()
        writer.write(manifest, args.output, overwrite=args.overwrite)

        # 8. Print success message
        print(f"Decision manifest written to: {args.output}")
        return 0

    except FileExistsError as exc:
        print(f"Error: {exc}")
        return 1
    except Exception as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
