"""Property-based tests for record_export.py using Hypothesis.

Feature: bootcamp-record-export
"""

from __future__ import annotations

import dataclasses
import re
import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from record_export import (
    DecisionCollector,
    DecisionManifest,
    ManifestWriter,
    PreferencesData,
    ProgressData,
    SecuritySanitizer,
)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Path segment: alphanumeric + underscores, non-empty
_PATH_SEGMENT = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
    min_size=1,
    max_size=15,
)


@st.composite
def st_unix_absolute_path(draw) -> str:
    """Generate a Unix absolute path like /home/user/project/file.txt."""
    segments = draw(st.lists(_PATH_SEGMENT, min_size=1, max_size=5))
    return "/" + "/".join(segments)


@st.composite
def st_windows_absolute_path(draw) -> str:
    """Generate a Windows absolute path like C:\\Users\\project\\file.txt."""
    drive_letter = draw(st.sampled_from("CDEFGHIJKLMNOPQRSTUVWXYZ"))
    segments = draw(st.lists(_PATH_SEGMENT, min_size=1, max_size=5))
    separator = draw(st.sampled_from(["\\", "/"]))
    return f"{drive_letter}:{separator}" + separator.join(segments)


@st.composite
def st_absolute_path(draw) -> str:
    """Generate either a Unix or Windows absolute path."""
    return draw(st.one_of(st_unix_absolute_path(), st_windows_absolute_path()))


# Windows drive letter pattern: single alpha char followed by :\  or :/
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[/\\]")


# ---------------------------------------------------------------------------
# Property Tests: SecuritySanitizer
# ---------------------------------------------------------------------------


class TestSecuritySanitizer:
    """Property-based tests for SecuritySanitizer.

    **Validates: Requirement 11.3**
    """

    @given(path=st_absolute_path())
    @settings(max_examples=20)
    def test_relativize_path_removes_absolute_prefix(self, path: str) -> None:
        """Property 1: Sanitizer removes all absolute paths.

        For any string containing an absolute path (starting with `/` or a
        Windows drive letter like `C:\\`), `SecuritySanitizer.relativize_path()`
        SHALL return a string that does not start with `/` or a drive letter.
        The relative portion of the path SHALL be preserved.

        **Validates: Requirement 11.3**
        """
        sanitizer = SecuritySanitizer()
        project_root = "/home/user/project"

        result = sanitizer.relativize_path(path, project_root)

        # Result must NOT start with /
        assert not result.startswith("/"), (
            f"relativize_path({path!r}) returned {result!r} which still starts with '/'"
        )
        # Result must NOT start with a Windows drive letter pattern
        assert not _WINDOWS_DRIVE_RE.match(result), (
            f"relativize_path({path!r}) returned {result!r} which still has a drive letter"
        )
        # Result must not be empty (preserves some path content)
        assert len(result) > 0, (
            f"relativize_path({path!r}) returned empty string"
        )

    @given(path=st_absolute_path())
    @settings(max_examples=20)
    def test_sanitize_removes_absolute_paths_from_manifest(self, path: str) -> None:
        """Property 1 (extended): sanitize() removes absolute paths from manifest fields.

        The full `sanitize()` method SHALL ensure no absolute paths remain in
        manifest string fields that represent file paths.

        **Validates: Requirement 11.3**
        """
        sanitizer = SecuritySanitizer()
        project_root = "/home/user/project"

        # Build a minimal manifest with the absolute path in data_sources
        manifest = DecisionManifest(
            metadata={"schema_version": "1.0", "generated_at": "2026-01-01T00:00:00Z",
                      "power_version": "1.0.0"},
            track_progress={"track_name": "Core Bootcamp", "modules_completed": []},
            business_problem=None,
            sdk_setup=None,
            data_sources=[{"name": "test", "file_path": path, "file_format": "csv",
                           "record_count": 100, "module": 4}],
            mapping_decisions=[],
            loading_config={"strategy": "single_source", "script_files": [path],
                            "redo_processing": False, "redo_reason": None, "module": 6},
            query_programs=[{"filename": path, "query_type": "search_by_attributes",
                             "description": "test query", "module": 7}],
            performance_tuning=None,
            security_hardening=None,
            monitoring_config=None,
            deployment=None,
            replay_notes=[],
        )

        sanitized, warnings = sanitizer.sanitize(manifest, project_root)

        # Check data_sources file_path
        for ds in sanitized.data_sources:
            fp = ds["file_path"]
            assert not fp.startswith("/"), (
                f"data_sources file_path still absolute: {fp!r}"
            )
            assert not _WINDOWS_DRIVE_RE.match(fp), (
                f"data_sources file_path still has drive letter: {fp!r}"
            )

        # Check loading_config script_files
        if sanitized.loading_config:
            for sf in sanitized.loading_config["script_files"]:
                assert not sf.startswith("/"), (
                    f"loading_config script_file still absolute: {sf!r}"
                )
                assert not _WINDOWS_DRIVE_RE.match(sf), (
                    f"loading_config script_file still has drive letter: {sf!r}"
                )

        # Check query_programs filename
        for qp in sanitized.query_programs:
            fn = qp["filename"]
            assert not fn.startswith("/"), (
                f"query_programs filename still absolute: {fn!r}"
            )
            assert not _WINDOWS_DRIVE_RE.match(fn), (
                f"query_programs filename still has drive letter: {fn!r}"
            )

    # ------------------------------------------------------------------
    # Property 2: Sanitizer detects secret patterns
    # ------------------------------------------------------------------

    @given(secret=st.one_of(
        # Connection strings
        st.builds(
            lambda proto, user, pw, host, db: f"{proto}://{user}:{pw}@{host}/{db}",
            proto=st.sampled_from(["postgres", "mysql", "sqlite", "mongodb"]),
            user=st.from_regex(r"[a-z]{3,8}", fullmatch=True),
            pw=st.from_regex(r"[a-zA-Z0-9]{4,12}", fullmatch=True),
            host=st.from_regex(r"[a-z]{3,10}\.[a-z]{2,4}", fullmatch=True),
            db=st.from_regex(r"[a-z_]{3,10}", fullmatch=True),
        ),
        # AWS-style access key IDs
        st.builds(
            lambda suffix: f"AKIA{suffix}",
            suffix=st.from_regex(r"[0-9A-Z]{16}", fullmatch=True),
        ),
        # Token/key/secret assignments
        st.builds(
            lambda keyword, sep, val: f"{keyword}{sep}{val}",
            keyword=st.sampled_from(["token", "key", "secret", "password", "credential"]),
            sep=st.sampled_from([" = ", " : ", "=", ": "]),
            val=st.from_regex(r"[a-zA-Z0-9_]{8,20}", fullmatch=True),
        ),
        # Long hex strings (40+ chars)
        st.from_regex(r"[0-9a-f]{40,60}", fullmatch=True),
    ))
    @settings(max_examples=20)
    def test_check_value_detects_secrets(self, secret: str) -> None:
        """Property 2: check_value() detects secret patterns.

        For any string matching one of the defined secret patterns (connection
        string, AWS key, token assignment, long hex), check_value() SHALL
        return True.

        **Validates: Requirement 11.4**
        """
        sanitizer = SecuritySanitizer()
        assert sanitizer.check_value(secret) is True, (
            f"check_value({secret!r}) returned False but should detect this as a secret"
        )

    @given(normal=st.sampled_from([
        "python", "java", "csharp", "rust", "typescript",
        "sqlite", "postgresql", "mysql_type",
        "src/load/main.py", "src/query/search.py", "data/raw/customers.csv",
        "core_bootcamp", "advanced_topics",
        "csv", "json", "jsonl", "xml", "tsv",
        "PERSON", "ORGANIZATION", "VEHICLE",
        "single_source", "multi_source",
        "hello", "world", "test", "module",
        "NAME_FULL", "EMAIL_ADDRESS", "PHONE_NUMBER",
    ]))
    @settings(max_examples=20)
    def test_check_value_allows_normal_values(self, normal: str) -> None:
        """Property 2: check_value() allows normal configuration values.

        For strings that are normal configuration values (language names,
        database types, file paths, module names), check_value() SHALL
        return False.

        **Validates: Requirement 11.4**
        """
        sanitizer = SecuritySanitizer()
        assert sanitizer.check_value(normal) is False, (
            f"check_value({normal!r}) returned True but this is a normal config value"
        )


# ---------------------------------------------------------------------------
# Unit Tests: DecisionCollector.collect_preferences
# ---------------------------------------------------------------------------


class TestCollectPreferences:
    """Unit tests for DecisionCollector.collect_preferences().

    **Validates: Requirement 12.2**
    """

    def test_returns_preferences_from_valid_yaml(self) -> None:
        """collect_preferences returns PreferencesData from valid YAML."""
        yaml_content = (
            "# Bootcamp preferences\n"
            "language: python\n"
            "track: core_bootcamp\n"
            "database_type: sqlite\n"
            "deployment_target: aws\n"
            "cloud_provider: aws\n"
            "verbosity: normal\n"
        )

        def reader(path: str) -> str | None:
            if "bootcamp_preferences.yaml" in path:
                return yaml_content
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_preferences()

        assert result is not None
        assert result.language == "python"
        assert result.track == "core_bootcamp"
        assert result.database_type == "sqlite"
        assert result.deployment_target == "aws"
        assert result.cloud_provider == "aws"
        assert result.verbosity == "normal"

    def test_returns_none_when_file_missing(self) -> None:
        """collect_preferences returns None when preferences file doesn't exist."""
        collector = DecisionCollector("/project", file_reader=lambda p: None)
        result = collector.collect_preferences()
        assert result is None

    def test_handles_null_values(self) -> None:
        """collect_preferences handles null/None YAML values correctly."""
        yaml_content = (
            "language: python\n"
            "track: core_bootcamp\n"
            "database_type: sqlite\n"
            "deployment_target: null\n"
            "cloud_provider: ~\n"
            "verbosity: None\n"
        )

        def reader(path: str) -> str | None:
            if "bootcamp_preferences.yaml" in path:
                return yaml_content
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_preferences()

        assert result is not None
        assert result.language == "python"
        assert result.deployment_target is None
        assert result.cloud_provider is None
        assert result.verbosity is None

    def test_handles_quoted_values(self) -> None:
        """collect_preferences strips quotes from YAML values."""
        yaml_content = (
            'language: "python"\n'
            "track: 'core_bootcamp'\n"
            "database_type: sqlite\n"
            "deployment_target: null\n"
            "cloud_provider: null\n"
            "verbosity: null\n"
        )

        def reader(path: str) -> str | None:
            if "bootcamp_preferences.yaml" in path:
                return yaml_content
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_preferences()

        assert result is not None
        assert result.language == "python"
        assert result.track == "core_bootcamp"

    def test_handles_missing_keys(self) -> None:
        """collect_preferences sets missing keys to None."""
        yaml_content = "language: python\n"

        def reader(path: str) -> str | None:
            if "bootcamp_preferences.yaml" in path:
                return yaml_content
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_preferences()

        assert result is not None
        assert result.language == "python"
        assert result.track is None
        assert result.database_type is None
        assert result.deployment_target is None
        assert result.cloud_provider is None
        assert result.verbosity is None

    def test_uses_correct_file_path(self) -> None:
        """collect_preferences reads from config/bootcamp_preferences.yaml relative to root."""
        requested_paths: list[str] = []

        def reader(path: str) -> str | None:
            requested_paths.append(path)
            return "language: python\ntrack: core_bootcamp\ndatabase_type: sqlite\n"

        collector = DecisionCollector("/my/project", file_reader=reader)
        collector.collect_preferences()

        assert len(requested_paths) == 1
        assert requested_paths[0].endswith("config/bootcamp_preferences.yaml")
        assert requested_paths[0].startswith("/my/project")


# ---------------------------------------------------------------------------
# Unit Tests: DecisionCollector.collect_progress
# ---------------------------------------------------------------------------


class TestCollectProgress:
    """Unit tests for DecisionCollector.collect_progress().

    **Validates: Requirement 12.1**
    """

    def test_returns_progress_from_valid_json(self) -> None:
        """collect_progress returns ProgressData from valid JSON."""
        json_content = (
            '{"modules_completed": [1, 2, 3], '
            '"current_module": 4, '
            '"step_history": {"1": {"completed": true}}}'
        )

        def reader(path: str) -> str | None:
            if "bootcamp_progress.json" in path:
                return json_content
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_progress()

        assert result is not None
        assert result.modules_completed == [1, 2, 3]
        assert result.current_module == 4
        assert result.step_history == {"1": {"completed": True}}

    def test_returns_none_when_file_missing(self) -> None:
        """collect_progress returns None when progress file doesn't exist."""
        collector = DecisionCollector("/project", file_reader=lambda p: None)
        result = collector.collect_progress()
        assert result is None

    def test_returns_none_for_invalid_json(self) -> None:
        """collect_progress returns None when JSON is invalid."""
        def reader(path: str) -> str | None:
            if "bootcamp_progress.json" in path:
                return "not valid json {{{["
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_progress()
        assert result is None

    def test_handles_missing_fields_with_defaults(self) -> None:
        """collect_progress uses defaults for missing fields."""
        json_content = "{}"

        def reader(path: str) -> str | None:
            if "bootcamp_progress.json" in path:
                return json_content
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_progress()

        assert result is not None
        assert result.modules_completed == []
        assert result.current_module is None
        assert result.step_history is None

    def test_handles_null_current_module(self) -> None:
        """collect_progress handles null current_module correctly."""
        json_content = '{"modules_completed": [1, 2], "current_module": null}'

        def reader(path: str) -> str | None:
            if "bootcamp_progress.json" in path:
                return json_content
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_progress()

        assert result is not None
        assert result.modules_completed == [1, 2]
        assert result.current_module is None

    def test_handles_invalid_modules_completed_type(self) -> None:
        """collect_progress defaults to empty list if modules_completed is not a list."""
        json_content = '{"modules_completed": "not a list"}'

        def reader(path: str) -> str | None:
            if "bootcamp_progress.json" in path:
                return json_content
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_progress()

        assert result is not None
        assert result.modules_completed == []

    def test_handles_invalid_current_module_type(self) -> None:
        """collect_progress defaults to None if current_module is not an int."""
        json_content = '{"modules_completed": [1], "current_module": "four"}'

        def reader(path: str) -> str | None:
            if "bootcamp_progress.json" in path:
                return json_content
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_progress()

        assert result is not None
        assert result.current_module is None

    def test_handles_invalid_step_history_type(self) -> None:
        """collect_progress defaults to None if step_history is not a dict."""
        json_content = '{"modules_completed": [], "step_history": [1, 2, 3]}'

        def reader(path: str) -> str | None:
            if "bootcamp_progress.json" in path:
                return json_content
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_progress()

        assert result is not None
        assert result.step_history is None

    def test_returns_none_for_non_dict_json(self) -> None:
        """collect_progress returns None if JSON root is not a dict."""
        json_content = "[1, 2, 3]"

        def reader(path: str) -> str | None:
            if "bootcamp_progress.json" in path:
                return json_content
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_progress()
        assert result is None

    def test_uses_correct_file_path(self) -> None:
        """collect_progress reads from config/bootcamp_progress.json relative to root."""
        requested_paths: list[str] = []

        def reader(path: str) -> str | None:
            requested_paths.append(path)
            return '{"modules_completed": [1]}'

        collector = DecisionCollector("/my/project", file_reader=reader)
        collector.collect_progress()

        assert len(requested_paths) == 1
        assert requested_paths[0].endswith("config/bootcamp_progress.json")
        assert requested_paths[0].startswith("/my/project")

# ---------------------------------------------------------------------------
# Unit Tests: DecisionCollector.collect_mappings
# ---------------------------------------------------------------------------

from record_export import MappingDecision


class TestCollectMappings:
    """Unit tests for DecisionCollector.collect_mappings().

    **Validates: Requirement 6.1, 6.2, 6.3, 6.4, 12.3**
    """

    def test_parses_full_mapping_file(self) -> None:
        """collect_mappings parses a complete mapping YAML file."""
        yaml_content = (
            "source_name: crm_customers\n"
            "entity_type: PERSON\n"
            "field_mappings:\n"
            "  full_name: NAME_FULL\n"
            "  email: EMAIL_ADDRESS\n"
            "  phone: PHONE_NUMBER\n"
            "transformations:\n"
            "  - Split full_name into first/last\n"
            "  - Normalize phone format\n"
        )

        def reader(path: str) -> str | None:
            if "crm_mapping.yaml" in path:
                return yaml_content
            return None

        def lister(path: str) -> list[str]:
            if path.endswith("config"):
                return ["crm_mapping.yaml", "bootcamp_preferences.yaml"]
            return []

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_mappings()

        assert len(result) == 1
        m = result[0]
        assert m.source_name == "crm_customers"
        assert m.entity_type == "PERSON"
        assert m.field_mappings == {
            "full_name": "NAME_FULL",
            "email": "EMAIL_ADDRESS",
            "phone": "PHONE_NUMBER",
        }
        assert m.transformations == [
            "Split full_name into first/last",
            "Normalize phone format",
        ]
        assert m.module == 5

    def test_infers_source_name_from_filename(self) -> None:
        """collect_mappings infers source_name from filename when not in content."""
        yaml_content = (
            "entity_type: ORGANIZATION\n"
            "field_mappings:\n"
            "  company: NAME_ORG\n"
        )

        def reader(path: str) -> str | None:
            if "mapping_billing.yaml" in path:
                return yaml_content
            return None

        def lister(path: str) -> list[str]:
            if path.endswith("config"):
                return ["mapping_billing.yaml"]
            return []

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_mappings()

        assert len(result) == 1
        assert result[0].source_name == "billing"
        assert result[0].entity_type == "ORGANIZATION"
        assert result[0].field_mappings == {"company": "NAME_ORG"}

    def test_handles_multiple_mapping_files(self) -> None:
        """collect_mappings processes multiple mapping files."""
        files = {
            "/project/config/crm_mapping.yaml": (
                "source_name: crm\n"
                "entity_type: PERSON\n"
                "field_mappings:\n"
                "  name: NAME_FULL\n"
            ),
            "/project/config/billing_mapping.yml": (
                "source_name: billing\n"
                "entity_type: ORGANIZATION\n"
                "field_mappings:\n"
                "  company: NAME_ORG\n"
            ),
        }

        def reader(path: str) -> str | None:
            return files.get(path)

        def lister(path: str) -> list[str]:
            if path.endswith("config"):
                return ["crm_mapping.yaml", "billing_mapping.yml", "other.yaml"]
            return []

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_mappings()

        assert len(result) == 2
        names = [m.source_name for m in result]
        assert "billing" in names
        assert "crm" in names

    def test_fallback_to_data_transformed(self) -> None:
        """collect_mappings falls back to data/transformed/ when no mapping files in config."""

        def reader(path: str) -> str | None:
            return None

        def lister(path: str) -> list[str]:
            if path.endswith("config"):
                return ["bootcamp_preferences.yaml"]  # no mapping files
            if path.endswith("transformed"):
                return ["transform_crm.py", "convert_billing.py"]
            return []

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_mappings()

        assert len(result) == 2
        # Sorted alphabetically: convert_billing.py, transform_crm.py
        assert result[0].source_name == "billing"
        assert result[0].transformations == ["Transformation script: convert_billing.py"]
        assert result[0].entity_type == ""
        assert result[0].field_mappings == {}
        assert result[1].source_name == "crm"
        assert result[1].transformations == ["Transformation script: transform_crm.py"]

    def test_returns_empty_list_when_no_mapping_info(self) -> None:
        """collect_mappings returns empty list when no mapping info found anywhere."""

        def reader(path: str) -> str | None:
            return None

        def lister(path: str) -> list[str]:
            if path.endswith("config"):
                return ["bootcamp_preferences.yaml"]
            if path.endswith("transformed"):
                return []
            return []

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_mappings()
        assert result == []

    def test_skips_non_yaml_files_with_mapping_in_name(self) -> None:
        """collect_mappings only processes .yaml/.yml files."""

        def reader(path: str) -> str | None:
            return None

        def lister(path: str) -> list[str]:
            if path.endswith("config"):
                return ["mapping_notes.txt", "mapping_backup.json"]
            return []

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_mappings()
        # No yaml/yml files with "mapping" → falls through to transformed dir
        assert result == []

    def test_handles_empty_field_mappings(self) -> None:
        """collect_mappings handles mapping file with no field_mappings section."""
        yaml_content = (
            "source_name: test_source\n"
            "entity_type: PERSON\n"
        )

        def reader(path: str) -> str | None:
            if "test_mapping.yaml" in path:
                return yaml_content
            return None

        def lister(path: str) -> list[str]:
            if path.endswith("config"):
                return ["test_mapping.yaml"]
            return []

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_mappings()

        assert len(result) == 1
        assert result[0].source_name == "test_source"
        assert result[0].field_mappings == {}
        assert result[0].transformations == []

    def test_skips_hidden_files_in_transformed_fallback(self) -> None:
        """collect_mappings skips hidden files when scanning data/transformed/."""

        def reader(path: str) -> str | None:
            return None

        def lister(path: str) -> list[str]:
            if path.endswith("config"):
                return []  # no files at all
            if path.endswith("transformed"):
                return [".hidden", "transform_crm.py"]
            return []

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_mappings()

        assert len(result) == 1
        assert result[0].source_name == "crm"

    def test_handles_comments_in_mapping_yaml(self) -> None:
        """collect_mappings correctly ignores comments in YAML."""
        yaml_content = (
            "# Mapping for CRM data\n"
            "source_name: crm\n"
            "# Entity type\n"
            "entity_type: PERSON\n"
            "field_mappings:\n"
            "  # Name field\n"
            "  name: NAME_FULL\n"
            "transformations:\n"
            "  # First transformation\n"
            "  - Split name\n"
        )

        def reader(path: str) -> str | None:
            if "crm_mapping.yaml" in path:
                return yaml_content
            return None

        def lister(path: str) -> list[str]:
            if path.endswith("config"):
                return ["crm_mapping.yaml"]
            return []

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_mappings()

        assert len(result) == 1
        assert result[0].source_name == "crm"
        assert result[0].field_mappings == {"name": "NAME_FULL"}
        assert result[0].transformations == ["Split name"]

    def test_dir_lister_defaults_to_os_listdir(self) -> None:
        """DecisionCollector uses os.listdir by default for dir_lister."""
        collector = DecisionCollector("/nonexistent/path", file_reader=lambda p: None)
        # Should not raise - returns empty list for nonexistent dir
        result = collector._list_dir("/nonexistent/path/config")
        assert result == []


# ---------------------------------------------------------------------------
# Unit Tests: DecisionCollector.collect_loading_config
# ---------------------------------------------------------------------------

from record_export import LoadingConfig


class TestCollectLoadingConfig:
    """Unit tests for DecisionCollector.collect_loading_config().

    **Validates: Requirement 7.1, 7.2, 12.4**
    """

    def test_returns_none_when_no_scripts_found(self) -> None:
        """collect_loading_config returns None when src/load/ has no script files."""

        def lister(path: str) -> list[str]:
            if "src/load" in path or path.endswith("load"):
                return ["README.md", "notes.txt"]
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_loading_config()
        assert result is None

    def test_returns_none_when_directory_empty(self) -> None:
        """collect_loading_config returns None when src/load/ is empty."""

        def lister(path: str) -> list[str]:
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_loading_config()
        assert result is None

    def test_single_source_strategy_with_one_script(self) -> None:
        """collect_loading_config returns single_source when only 1 script exists."""

        def lister(path: str) -> list[str]:
            if "src/load" in path or path.endswith("load"):
                return ["load_crm.py"]
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_loading_config()

        assert result is not None
        assert result.strategy == "single_source"
        assert result.script_files == ["src/load/load_crm.py"]
        assert result.module == 6

    def test_multi_source_strategy_with_multiple_scripts(self) -> None:
        """collect_loading_config returns multi_source when 2+ scripts exist."""

        def lister(path: str) -> list[str]:
            if "src/load" in path or path.endswith("load"):
                return ["load_crm.py", "load_billing.py"]
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_loading_config()

        assert result is not None
        assert result.strategy == "multi_source"
        assert result.script_files == ["src/load/load_billing.py", "src/load/load_crm.py"]
        assert result.module == 6

    def test_detects_redo_in_filename(self) -> None:
        """collect_loading_config detects redo processing from filename."""

        def lister(path: str) -> list[str]:
            if "src/load" in path or path.endswith("load"):
                return ["load_crm.py", "redo_processor.py"]
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_loading_config()

        assert result is not None
        assert result.redo_processing is True

    def test_detects_redo_in_file_content(self) -> None:
        """collect_loading_config detects redo processing from file content."""

        def lister(path: str) -> list[str]:
            if "src/load" in path or path.endswith("load"):
                return ["load_crm.py"]
            return []

        def reader(path: str) -> str | None:
            if "load_crm.py" in path:
                return "# Load CRM data\nprocess_redo_records()\n"
            return None

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_loading_config()

        assert result is not None
        assert result.redo_processing is True

    def test_redo_processing_none_when_not_found(self) -> None:
        """collect_loading_config sets redo_processing to None when not detected."""

        def lister(path: str) -> list[str]:
            if "src/load" in path or path.endswith("load"):
                return ["load_crm.py"]
            return []

        def reader(path: str) -> str | None:
            if "load_crm.py" in path:
                return "# Load CRM data\nimport senzing\n"
            return None

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_loading_config()

        assert result is not None
        assert result.redo_processing is None

    def test_filters_only_recognized_extensions(self) -> None:
        """collect_loading_config only includes .py, .java, .cs, .rs, .ts files."""

        def lister(path: str) -> list[str]:
            if "src/load" in path or path.endswith("load"):
                return [
                    "load_crm.py",
                    "LoadBilling.java",
                    "Loader.cs",
                    "loader.rs",
                    "loader.ts",
                    "README.md",
                    "config.yaml",
                    "notes.txt",
                ]
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_loading_config()

        assert result is not None
        assert result.strategy == "multi_source"
        assert len(result.script_files) == 5
        assert "src/load/README.md" not in result.script_files
        assert "src/load/config.yaml" not in result.script_files
        assert "src/load/notes.txt" not in result.script_files

    def test_script_files_are_sorted(self) -> None:
        """collect_loading_config returns script_files in sorted order."""

        def lister(path: str) -> list[str]:
            if "src/load" in path or path.endswith("load"):
                return ["z_loader.py", "a_loader.py", "m_loader.py"]
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_loading_config()

        assert result is not None
        assert result.script_files == [
            "src/load/a_loader.py",
            "src/load/m_loader.py",
            "src/load/z_loader.py",
        ]

    def test_redo_reason_is_always_none(self) -> None:
        """collect_loading_config always sets redo_reason to None."""

        def lister(path: str) -> list[str]:
            if "src/load" in path or path.endswith("load"):
                return ["load_redo.py"]
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_loading_config()

        assert result is not None
        assert result.redo_reason is None

    def test_handles_unreadable_file_content(self) -> None:
        """collect_loading_config handles None from file reader gracefully."""

        def lister(path: str) -> list[str]:
            if "src/load" in path or path.endswith("load"):
                return ["load_crm.py", "load_billing.py"]
            return []

        # Reader returns None for all files (unreadable)
        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_loading_config()

        assert result is not None
        assert result.strategy == "multi_source"
        # No redo detected since files are unreadable and filenames don't contain "redo"
        assert result.redo_processing is None


# ---------------------------------------------------------------------------
# Unit Tests: DecisionCollector.collect_query_programs
# ---------------------------------------------------------------------------

from record_export import QueryProgram


class TestCollectQueryPrograms:
    """Unit tests for DecisionCollector.collect_query_programs().

    **Validates: Requirement 8.1, 8.2, 12.5**
    """

    def test_returns_empty_list_when_no_scripts_found(self) -> None:
        """collect_query_programs returns empty list when directory has no scripts."""

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return ["README.md", "notes.txt"]
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_query_programs()
        assert result == []

    def test_returns_empty_list_when_directory_missing(self) -> None:
        """collect_query_programs returns empty list when src/query/ doesn't exist."""

        def lister(path: str) -> list[str]:
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_query_programs()
        assert result == []

    def test_infers_search_type_from_filename(self) -> None:
        """collect_query_programs infers search_by_attributes from 'search' in filename."""

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return ["search_by_name.py"]
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_query_programs()

        assert len(result) == 1
        assert result[0].query_type == "search_by_attributes"
        assert result[0].filename == "src/query/search_by_name.py"
        assert result[0].module == 7

    def test_infers_get_entity_type(self) -> None:
        """collect_query_programs infers get_entity from 'get_entity' or 'entity'."""

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return ["get_entity_details.py", "entity_lookup.ts"]
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_query_programs()

        assert len(result) == 2
        assert all(p.query_type == "get_entity" for p in result)

    def test_infers_find_relationships_type(self) -> None:
        """collect_query_programs infers find_relationships from 'relationship' or 'network'."""

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return ["find_relationships.java", "network_explorer.rs"]
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_query_programs()

        assert len(result) == 2
        assert all(p.query_type == "find_relationships" for p in result)

    def test_infers_how_entity_type(self) -> None:
        """collect_query_programs infers how_entity from 'how' in filename."""

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return ["how_resolved.py"]
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_query_programs()

        assert len(result) == 1
        assert result[0].query_type == "how_entity"

    def test_infers_why_entity_type(self) -> None:
        """collect_query_programs infers why_entity from 'why' in filename."""

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return ["why_entities.cs"]
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_query_programs()

        assert len(result) == 1
        assert result[0].query_type == "why_entity"

    def test_infers_unknown_type_for_unrecognized_filename(self) -> None:
        """collect_query_programs returns 'unknown' for unrecognized filenames."""

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return ["custom_query.py"]
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_query_programs()

        assert len(result) == 1
        assert result[0].query_type == "unknown"

    def test_extracts_description_from_python_docstring(self) -> None:
        """collect_query_programs extracts description from Python triple-quote docstring."""
        py_content = '"""Search for entities by name and address."""\nimport senzing\n'

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return ["search_by_name.py"]
            return []

        def reader(path: str) -> str | None:
            if "search_by_name.py" in path:
                return py_content
            return None

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_query_programs()

        assert len(result) == 1
        assert result[0].description == "Search for entities by name and address."

    def test_extracts_description_from_python_hash_comment(self) -> None:
        """collect_query_programs extracts description from Python # comment."""
        py_content = "# Retrieve full entity record\nimport senzing\n"

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return ["get_entity.py"]
            return []

        def reader(path: str) -> str | None:
            if "get_entity.py" in path:
                return py_content
            return None

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_query_programs()

        assert len(result) == 1
        assert result[0].description == "Retrieve full entity record"

    def test_extracts_description_from_double_slash_comment(self) -> None:
        """collect_query_programs extracts description from // comment in non-Python files."""
        ts_content = "// Find relationships between entities\nimport { Senzing } from 'senzing';\n"

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return ["find_relationships.ts"]
            return []

        def reader(path: str) -> str | None:
            if "find_relationships.ts" in path:
                return ts_content
            return None

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_query_programs()

        assert len(result) == 1
        assert result[0].description == "Find relationships between entities"

    def test_extracts_description_from_block_comment(self) -> None:
        """collect_query_programs extracts description from /* */ block comment."""
        java_content = "/* How entity was resolved */\npublic class HowResolved {}\n"

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return ["how_resolved.java"]
            return []

        def reader(path: str) -> str | None:
            if "how_resolved.java" in path:
                return java_content
            return None

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_query_programs()

        assert len(result) == 1
        assert result[0].description == "How entity was resolved"

    def test_default_description_when_no_comment(self) -> None:
        """collect_query_programs uses default description when no comment found."""
        rs_content = "fn main() {}\n"

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return ["why_entities.rs"]
            return []

        def reader(path: str) -> str | None:
            if "why_entities.rs" in path:
                return rs_content
            return None

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_query_programs()

        assert len(result) == 1
        assert result[0].description == "Query program"

    def test_default_description_when_file_unreadable(self) -> None:
        """collect_query_programs uses default description when file can't be read."""

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return ["search_by_name.py"]
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_query_programs()

        assert len(result) == 1
        assert result[0].description == "Query program"

    def test_results_are_sorted_by_filename(self) -> None:
        """collect_query_programs returns results sorted by filename."""

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return ["z_query.py", "a_search.py", "m_entity.ts"]
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_query_programs()

        assert len(result) == 3
        assert result[0].filename == "src/query/a_search.py"
        assert result[1].filename == "src/query/m_entity.ts"
        assert result[2].filename == "src/query/z_query.py"

    def test_filters_only_recognized_extensions(self) -> None:
        """collect_query_programs only includes .py, .java, .cs, .rs, .ts files."""

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return [
                    "search.py", "search.java", "search.cs",
                    "search.rs", "search.ts",
                    "search.js", "search.go", "README.md", "notes.txt",
                ]
            return []

        collector = DecisionCollector(
            "/project", file_reader=lambda p: None, dir_lister=lister
        )
        result = collector.collect_query_programs()

        assert len(result) == 5
        extensions = [p.filename.split(".")[-1] for p in result]
        assert sorted(extensions) == ["cs", "java", "py", "rs", "ts"]

    def test_skips_shebang_in_python_description(self) -> None:
        """collect_query_programs skips shebang line when extracting Python description."""
        py_content = "#!/usr/bin/env python3\n# Search entities by attributes\nimport senzing\n"

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return ["search.py"]
            return []

        def reader(path: str) -> str | None:
            if "search.py" in path:
                return py_content
            return None

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_query_programs()

        assert len(result) == 1
        assert result[0].description == "Search entities by attributes"

    def test_multiline_python_docstring(self) -> None:
        """collect_query_programs extracts first line from multi-line Python docstring."""
        py_content = '"""\nSearch for entities by name.\n\nDetailed description here.\n"""\n'

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return ["search.py"]
            return []

        def reader(path: str) -> str | None:
            if "search.py" in path:
                return py_content
            return None

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_query_programs()

        assert len(result) == 1
        assert result[0].description == "Search for entities by name."

    def test_multiline_block_comment(self) -> None:
        """collect_query_programs extracts first line from multi-line /* */ comment."""
        java_content = "/*\n * Find entity relationships\n * More details\n */\npublic class X {}\n"

        def lister(path: str) -> list[str]:
            if "src/query" in path or path.endswith("query"):
                return ["find_relationships.java"]
            return []

        def reader(path: str) -> str | None:
            if "find_relationships.java" in path:
                return java_content
            return None

        collector = DecisionCollector("/project", file_reader=reader, dir_lister=lister)
        result = collector.collect_query_programs()

        assert len(result) == 1
        assert result[0].description == "Find entity relationships"

# ---------------------------------------------------------------------------
# Unit Tests: DecisionCollector.collect_business_problem
# ---------------------------------------------------------------------------

from record_export import BusinessProblem


class TestCollectBusinessProblem:
    """Unit tests for DecisionCollector.collect_business_problem().

    **Validates: Requirement 3.1, 3.2, 12.4**
    """

    def test_returns_none_when_journal_missing(self) -> None:
        """collect_business_problem returns None when journal file doesn't exist."""
        collector = DecisionCollector("/project", file_reader=lambda p: None)
        result = collector.collect_business_problem()
        assert result is None

    def test_returns_none_when_no_module1_section(self) -> None:
        """collect_business_problem returns None when journal has no Module 1."""
        journal = "# Bootcamp Journal\n\n## Module 2: SDK Setup\n\nSome content.\n"

        def reader(path: str) -> str | None:
            if "bootcamp_journal.md" in path:
                return journal
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_business_problem()
        assert result is None

    def test_parses_full_module1_with_all_subsections(self) -> None:
        """collect_business_problem extracts all subsections from Module 1."""
        journal = (
            "# Bootcamp Journal\n\n"
            "## Module 1: Business Problem\n\n"
            "### Problem Statement\n\n"
            "Deduplicate customer records across CRM and billing systems.\n\n"
            "### Data Sources\n\n"
            "- CRM export\n"
            "- Billing database dump\n\n"
            "### Success Criteria\n\n"
            "- Identify duplicate customers across systems\n"
            "- Achieve >90% precision on known duplicates\n\n"
            "## Module 2: SDK Setup\n\n"
            "Some other content.\n"
        )

        def reader(path: str) -> str | None:
            if "bootcamp_journal.md" in path:
                return journal
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_business_problem()

        assert result is not None
        assert result.module == 1
        assert result.problem_statement == (
            "Deduplicate customer records across CRM and billing systems."
        )
        assert result.identified_sources == ["CRM export", "Billing database dump"]
        assert result.success_criteria == [
            "Identify duplicate customers across systems",
            "Achieve >90% precision on known duplicates",
        ]

    def test_fallback_to_first_paragraph_when_no_problem_heading(self) -> None:
        """collect_business_problem uses first paragraph as problem statement."""
        journal = (
            "# Journal\n\n"
            "## Module 1\n\n"
            "We want to match customer records from multiple systems.\n\n"
            "## Module 2\n"
        )

        def reader(path: str) -> str | None:
            if "bootcamp_journal.md" in path:
                return journal
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_business_problem()

        assert result is not None
        assert result.module == 1
        assert result.problem_statement == (
            "We want to match customer records from multiple systems."
        )
        assert result.identified_sources == []
        assert result.success_criteria == []

    def test_handles_identified_sources_heading_variant(self) -> None:
        """collect_business_problem recognizes '### Identified Sources' heading."""
        journal = (
            "## Module 1: Business Problem\n\n"
            "### Problem Statement\n\n"
            "Match records.\n\n"
            "### Identified Sources\n\n"
            "* Source A\n"
            "* Source B\n\n"
            "## Module 2\n"
        )

        def reader(path: str) -> str | None:
            if "bootcamp_journal.md" in path:
                return journal
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_business_problem()

        assert result is not None
        assert result.identified_sources == ["Source A", "Source B"]

    def test_module1_at_end_of_file(self) -> None:
        """collect_business_problem works when Module 1 is the last section."""
        journal = (
            "# Journal\n\n"
            "## Module 1: Business Problem\n\n"
            "### Problem Statement\n\n"
            "Final module content.\n\n"
            "### Success Criteria\n\n"
            "- Done\n"
        )

        def reader(path: str) -> str | None:
            if "bootcamp_journal.md" in path:
                return journal
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_business_problem()

        assert result is not None
        assert result.problem_statement == "Final module content."
        assert result.success_criteria == ["Done"]

    def test_empty_subsections_return_empty_lists(self) -> None:
        """collect_business_problem returns empty lists for missing subsections."""
        journal = (
            "## Module 1: Business Problem\n\n"
            "### Problem Statement\n\n"
            "Some problem.\n\n"
            "## Module 2\n"
        )

        def reader(path: str) -> str | None:
            if "bootcamp_journal.md" in path:
                return journal
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_business_problem()

        assert result is not None
        assert result.problem_statement == "Some problem."
        assert result.identified_sources == []
        assert result.success_criteria == []

    def test_uses_correct_file_path(self) -> None:
        """collect_business_problem reads from docs/bootcamp_journal.md."""
        requested_paths: list[str] = []

        def reader(path: str) -> str | None:
            requested_paths.append(path)
            return None

        collector = DecisionCollector("/my/project", file_reader=reader)
        collector.collect_business_problem()

        assert len(requested_paths) == 1
        assert requested_paths[0].endswith("docs/bootcamp_journal.md")
        assert requested_paths[0].startswith("/my/project")

    def test_module1_heading_case_insensitive(self) -> None:
        """collect_business_problem matches Module 1 heading case-insensitively."""
        journal = (
            "## module 1: business problem\n\n"
            "### Problem Statement\n\n"
            "Case insensitive match.\n\n"
            "## Module 2\n"
        )

        def reader(path: str) -> str | None:
            if "bootcamp_journal.md" in path:
                return journal
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_business_problem()

        assert result is not None
        assert result.problem_statement == "Case insensitive match."

    def test_multiline_problem_statement(self) -> None:
        """collect_business_problem captures multi-line problem statement."""
        journal = (
            "## Module 1: Business Problem\n\n"
            "### Problem Statement\n\n"
            "Line one of the problem.\n"
            "Line two of the problem.\n\n"
            "### Data Sources\n\n"
            "- Source 1\n\n"
            "## Module 2\n"
        )

        def reader(path: str) -> str | None:
            if "bootcamp_journal.md" in path:
                return journal
            return None

        collector = DecisionCollector("/project", file_reader=reader)
        result = collector.collect_business_problem()

        assert result is not None
        assert "Line one" in result.problem_statement
        assert "Line two" in result.problem_statement
        assert result.identified_sources == ["Source 1"]


# ---------------------------------------------------------------------------
# Property Tests: DecisionCollector.collect_all — missing files produce warnings
# ---------------------------------------------------------------------------

from record_export import CollectedDecisions


# The required source files that collect_all() checks for
_REQUIRED_FILES = ["preferences", "progress", "data_sources", "journal"]


@st.composite
def st_missing_files_subset(draw) -> set[str]:
    """Generate a random non-empty subset of required source files to be missing."""
    subset = draw(
        st.lists(
            st.sampled_from(_REQUIRED_FILES),
            min_size=1,
            max_size=len(_REQUIRED_FILES),
            unique=True,
        )
    )
    return set(subset)


class TestCollectAllMissingFiles:
    """Property-based tests for DecisionCollector.collect_all() with missing files.

    **Validates: Requirement 12.7**
    """

    @given(missing=st_missing_files_subset())
    @settings(max_examples=20)
    def test_missing_source_files_produce_warnings_not_failures(
        self, missing: set[str]
    ) -> None:
        """Property 10: Missing source files produce warnings, not failures.

        For any subset of source files that are missing (preferences, progress,
        data_sources, journal), `DecisionCollector.collect_all()` SHALL return a
        `CollectedDecisions` with the corresponding fields set to `None` or empty
        lists, and the `warnings` list SHALL contain one entry per missing file.
        The collector SHALL NOT raise an exception.

        **Validates: Requirement 12.7**
        """
        # Build file content for "present" files only
        file_contents: dict[str, str] = {}

        if "preferences" not in missing:
            file_contents["bootcamp_preferences.yaml"] = (
                "language: python\n"
                "track: core_bootcamp\n"
                "database_type: sqlite\n"
                "deployment_target: null\n"
                "cloud_provider: null\n"
                "verbosity: normal\n"
            )

        if "progress" not in missing:
            file_contents["bootcamp_progress.json"] = (
                '{"modules_completed": [1, 2, 3], "current_module": 4}'
            )

        if "data_sources" not in missing:
            file_contents["data_sources.yaml"] = (
                "- name: test_source\n"
                "  file_path: data/raw/test.csv\n"
                "  file_format: csv\n"
                "  record_count: 100\n"
            )

        if "journal" not in missing:
            file_contents["bootcamp_journal.md"] = (
                "## Module 1: Business Problem\n\n"
                "### Problem Statement\n\n"
                "Test problem statement.\n\n"
                "### Data Sources\n\n"
                "- Source A\n\n"
                "### Success Criteria\n\n"
                "- Criterion 1\n\n"
                "## Module 2\n"
            )

        def mock_file_reader(path: str) -> str | None:
            """Return content for present files, None for missing ones."""
            for filename, content in file_contents.items():
                if filename in path:
                    return content
            return None

        def mock_dir_lister(path: str) -> list[str]:
            """Return empty lists — simulates missing directories."""
            return []

        collector = DecisionCollector(
            "/project", file_reader=mock_file_reader, dir_lister=mock_dir_lister
        )

        # collect_all() SHALL NOT raise an exception
        result = collector.collect_all()

        # Result must be a CollectedDecisions instance
        assert isinstance(result, CollectedDecisions)

        # For each missing required file, verify the corresponding field is None/empty
        # and there's a corresponding warning
        if "preferences" in missing:
            assert result.preferences is None
        if "progress" in missing:
            assert result.progress is None
        if "data_sources" in missing:
            assert result.data_sources == []
        if "journal" in missing:
            assert result.business_problem is None

        # The warnings list SHALL contain at least one entry per missing required file
        assert len(result.warnings) >= len(missing), (
            f"Expected at least {len(missing)} warnings for missing files "
            f"{missing}, but got {len(result.warnings)}: {result.warnings}"
        )


# ---------------------------------------------------------------------------
# Property Tests: ManifestAssembler
# ---------------------------------------------------------------------------

from record_export import (
    DeploymentDecision,
    ManifestAssembler,
    MonitoringConfig,
    PerformanceTuning,
    SecurityHardening,
)



@st.composite
def st_collected_decisions(draw) -> CollectedDecisions:
    """Generate a CollectedDecisions with random combinations of None/populated fields."""
    # Mostly None values with optional populated preferences/progress
    preferences = draw(st.one_of(
        st.none(),
        st.builds(
            PreferencesData,
            language=st.sampled_from(["python", "java", "csharp", "rust", "typescript", None]),
            track=st.sampled_from(["core_bootcamp", "advanced_topics", None]),
            database_type=st.sampled_from(["sqlite", "postgresql", None]),
            deployment_target=st.sampled_from(["aws", "azure", "gcp", None]),
            cloud_provider=st.sampled_from(["aws", "azure", "gcp", None]),
            verbosity=st.sampled_from(["normal", "verbose", "quiet", None]),
        ),
    ))

    progress = draw(st.one_of(
        st.none(),
        st.builds(
            ProgressData,
            modules_completed=st.lists(
                st.integers(min_value=1, max_value=11), max_size=11, unique=True
            ),
            current_module=st.one_of(st.none(), st.integers(min_value=1, max_value=11)),
            step_history=st.none(),
        ),
    ))

    return CollectedDecisions(
        preferences=preferences,
        progress=progress,
        business_problem=None,
        data_sources=[],
        mappings=[],
        loading_config=None,
        query_programs=[],
        performance_tuning=None,
        security_hardening=None,
        monitoring_config=None,
        deployment=None,
        warnings=[],
    )


class TestManifestAssembler:
    """Property-based tests for ManifestAssembler.

    **Validates: Requirement 2.3, 13.1**
    """

    @given(decisions=st_collected_decisions())
    @settings(max_examples=20)
    def test_metadata_always_present_and_valid(self, decisions: CollectedDecisions) -> None:
        """Property 3: Manifest schema version is always present and valid.

        For any CollectedDecisions input (including all-None fields),
        ManifestAssembler.assemble() SHALL produce a DecisionManifest whose
        metadata dict contains schema_version equal to "1.0", a generated_at
        string in ISO 8601 format, and a non-empty power_version string.

        **Validates: Requirement 2.3, 13.1**
        """
        manifest = ManifestAssembler().assemble(decisions)

        # metadata must be present
        assert manifest.metadata is not None
        assert isinstance(manifest.metadata, dict)

        # schema_version must be "1.0"
        assert manifest.metadata["schema_version"] == "1.0"

        # generated_at must match ISO 8601 pattern
        iso_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"
        assert re.match(iso_pattern, manifest.metadata["generated_at"]), (
            f"generated_at {manifest.metadata['generated_at']!r} does not match ISO 8601 pattern"
        )

        # power_version must be a non-empty string
        assert isinstance(manifest.metadata["power_version"], str)
        assert len(manifest.metadata["power_version"]) > 0

    @given(data=st.data())
    @settings(max_examples=20)
    def test_optional_sections_appear_only_for_completed_modules(
        self, data: st.DataObject
    ) -> None:
        """Property 4: Optional sections appear only for completed modules.

        For any CollectedDecisions with random presence/absence of optional
        module data, the assembled manifest SHALL include performance_tuning
        if and only if the performance_tuning field is not None,
        security_hardening if and only if security_hardening is not None,
        monitoring_config if and only if monitoring_config is not None,
        and deployment if and only if deployment is not None.

        **Validates: Requirement 9.1, 9.2, 9.3, 9.4, 9.5**
        """
        # Generate random presence/absence of each optional module
        perf = data.draw(st.one_of(
            st.none(),
            st.just(PerformanceTuning(
                tuning_decisions=["test"],
                baseline_metrics=None,
                optimizations_applied=[],
                module=8,
            )),
        ))
        security = data.draw(st.one_of(
            st.none(),
            st.just(SecurityHardening(
                choices=["test"],
                checklist_items_completed=1,
                checklist_items_total=5,
                module=9,
            )),
        ))
        monitoring = data.draw(st.one_of(
            st.none(),
            st.just(MonitoringConfig(
                tools_chosen=["test"],
                alert_configurations=[],
                module=10,
            )),
        ))
        deployment = data.draw(st.one_of(
            st.none(),
            st.just(DeploymentDecision(
                target="aws",
                infrastructure_choices=["test"],
                deployment_method=None,
                module=11,
            )),
        ))

        decisions = CollectedDecisions(
            preferences=None,
            progress=None,
            business_problem=None,
            data_sources=[],
            mappings=[],
            loading_config=None,
            query_programs=[],
            performance_tuning=perf,
            security_hardening=security,
            monitoring_config=monitoring,
            deployment=deployment,
            warnings=[],
        )

        manifest = ManifestAssembler().assemble(decisions)

        # performance_tuning present iff decisions.performance_tuning is not None
        assert (manifest.performance_tuning is not None) == (perf is not None), (
            f"manifest.performance_tuning={manifest.performance_tuning!r} "
            f"but decisions.performance_tuning={'set' if perf else 'None'}"
        )
        # security_hardening present iff decisions.security_hardening is not None
        assert (manifest.security_hardening is not None) == (security is not None), (
            f"manifest.security_hardening={manifest.security_hardening!r} "
            f"but decisions.security_hardening={'set' if security else 'None'}"
        )
        # monitoring_config present iff decisions.monitoring_config is not None
        assert (manifest.monitoring_config is not None) == (monitoring is not None), (
            f"manifest.monitoring_config={manifest.monitoring_config!r} "
            f"but decisions.monitoring_config={'set' if monitoring else 'None'}"
        )
        # deployment present iff decisions.deployment is not None
        assert (manifest.deployment is not None) == (deployment is not None), (
            f"manifest.deployment={manifest.deployment!r} "
            f"but decisions.deployment={'set' if deployment else 'None'}"
        )

    @given(
        modules_completed=st.lists(
            st.integers(min_value=1, max_value=11), min_size=0, max_size=11, unique=True
        ),
        track=st.sampled_from(["core_bootcamp", "advanced_topics"]),
    )
    @settings(max_examples=20)
    def test_track_progress_reflects_actual_completion_state(
        self, modules_completed: list[int], track: str
    ) -> None:
        """Property 8: Track progress reflects actual completion state.

        For any ProgressData with modules_completed as a subset of 1–11 and a
        track from {core_bootcamp, advanced_topics}, the assembled track_progress
        section SHALL list exactly the modules in modules_completed, the
        total_modules_in_track SHALL match the track definition (7 for core,
        11 for advanced), and no module outside modules_completed SHALL appear
        in the completed list.

        **Validates: Requirement 10.1, 10.2**
        """
        progress = ProgressData(
            modules_completed=modules_completed,
            current_module=None,
            step_history=None,
        )
        preferences = PreferencesData(
            language=None,
            track=track,
            database_type=None,
            deployment_target=None,
            cloud_provider=None,
            verbosity=None,
        )
        decisions = CollectedDecisions(
            preferences=preferences,
            progress=progress,
            business_problem=None,
            data_sources=[],
            mappings=[],
            loading_config=None,
            query_programs=[],
            performance_tuning=None,
            security_hardening=None,
            monitoring_config=None,
            deployment=None,
            warnings=[],
        )

        manifest = ManifestAssembler().assemble(decisions)
        track_progress = manifest.track_progress

        # total_modules_in_track matches track definition
        expected_total = 7 if track == "core_bootcamp" else 11
        assert track_progress["total_modules_in_track"] == expected_total, (
            f"total_modules_in_track={track_progress['total_modules_in_track']!r} "
            f"but expected {expected_total} for track {track!r}"
        )

        # The set of module numbers in track_progress["modules_completed"]
        # must equal the set of progress.modules_completed
        completed_module_numbers = {
            entry["module"] for entry in track_progress["modules_completed"]
        }
        assert completed_module_numbers == set(modules_completed), (
            f"modules in track_progress={completed_module_numbers!r} "
            f"but expected {set(modules_completed)!r}"
        )

        # No module outside modules_completed appears in the completed list
        for entry in track_progress["modules_completed"]:
            assert entry["module"] in modules_completed, (
                f"module {entry['module']} in completed list but not in "
                f"modules_completed={modules_completed!r}"
            )

        # track_name matches the track
        expected_name = "Core Bootcamp" if track == "core_bootcamp" else "Advanced Topics"
        assert track_progress["track_name"] == expected_name, (
            f"track_name={track_progress['track_name']!r} "
            f"but expected {expected_name!r} for track {track!r}"
        )

# ---------------------------------------------------------------------------
# Property Tests: ManifestWriter
# ---------------------------------------------------------------------------

import yaml


@st.composite
def st_decision_manifest(draw) -> DecisionManifest:
    """Generate a DecisionManifest with various content for round-trip testing."""
    decisions = draw(st_collected_decisions())
    manifest = ManifestAssembler().assemble(decisions)
    return manifest


def _collect_all_keys(obj: object) -> list[str]:
    """Recursively collect all dict keys from nested dicts and lists of dicts.

    Args:
        obj: The object to walk (dict, list, or scalar).

    Returns:
        A list of all string keys found at every nesting level.
    """
    keys: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            keys.append(key)
            keys.extend(_collect_all_keys(value))
    elif isinstance(obj, list):
        for item in obj:
            keys.extend(_collect_all_keys(item))
    return keys


class TestManifestWriter:
    """Property-based tests for ManifestWriter.

    **Validates: Requirement 2.4, 13.2**
    """

    @given(manifest=st_decision_manifest())
    @settings(max_examples=20)
    def test_yaml_round_trip_serialize_parse_compare(
        self, manifest: DecisionManifest
    ) -> None:
        """Property 7: Manifest YAML is valid and parseable.

        For any DecisionManifest, ManifestWriter.to_yaml() SHALL produce a
        string that, when parsed by a YAML parser, produces a dict with the
        same logical content as the original manifest.

        **Validates: Requirement 2.4, 13.2**
        """
        writer = ManifestWriter()
        yaml_str = writer.to_yaml(manifest)

        # Parse the YAML output
        parsed = yaml.safe_load(yaml_str)
        assert isinstance(parsed, dict), (
            f"Parsed YAML is not a dict: {type(parsed)}"
        )

        # Verify top-level keys that are present (None values are skipped)
        manifest_dict = dataclasses.asdict(manifest)

        # The writer skips None values, so only compare keys present in both
        for key, value in manifest_dict.items():
            if value is None:
                # None values are omitted from YAML output
                assert key not in parsed, (
                    f"Key {key!r} has None value but appeared in YAML output"
                )
            else:
                assert key in parsed, (
                    f"Key {key!r} has non-None value but missing from YAML output"
                )

        # Verify metadata section round-trips correctly
        assert "metadata" in parsed
        assert parsed["metadata"]["schema_version"] == manifest.metadata["schema_version"]
        assert parsed["metadata"]["generated_at"] == manifest.metadata["generated_at"]
        assert parsed["metadata"]["power_version"] == manifest.metadata["power_version"]

        # Verify track_progress section round-trips correctly
        assert "track_progress" in parsed
        tp_parsed = parsed["track_progress"]
        tp_orig = manifest.track_progress

        # Compare non-None fields in track_progress
        for key, value in tp_orig.items():
            if value is None:
                continue
            assert key in tp_parsed, (
                f"track_progress.{key} missing from parsed YAML"
            )
            assert tp_parsed[key] == value, (
                f"track_progress.{key}: parsed={tp_parsed[key]!r} != original={value!r}"
            )

        # Verify data_sources round-trips (comparing non-None fields)
        if manifest.data_sources:
            assert "data_sources" in parsed
            assert len(parsed["data_sources"]) == len(manifest.data_sources)

        # Verify replay_notes round-trips
        if manifest.replay_notes:
            assert "replay_notes" in parsed
            assert parsed["replay_notes"] == manifest.replay_notes

    # ------------------------------------------------------------------
    # Property 9: Consistent snake_case key naming
    # ------------------------------------------------------------------

    @given(manifest=st_decision_manifest())
    @settings(max_examples=20)
    def test_all_keys_are_snake_case(self, manifest: DecisionManifest) -> None:
        """Property 9: Consistent snake_case key naming.

        For any DecisionManifest serialized to YAML, every key at every
        nesting level SHALL match the pattern [a-z][a-z0-9_]* (snake_case).
        No camelCase, PascalCase, or kebab-case keys SHALL appear.

        **Validates: Requirement 13.2**
        """
        writer = ManifestWriter()
        yaml_str = writer.to_yaml(manifest)

        parsed = yaml.safe_load(yaml_str)
        assert isinstance(parsed, dict), (
            f"Parsed YAML is not a dict: {type(parsed)}"
        )

        all_keys = _collect_all_keys(parsed)
        snake_case_re = re.compile(r"^[a-z][a-z0-9_]*$")

        for key in all_keys:
            assert snake_case_re.match(key), (
                f"Key {key!r} does not match snake_case pattern [a-z][a-z0-9_]*"
            )


# ---------------------------------------------------------------------------
# Unit Tests: CLI argument parsing and main flow
# ---------------------------------------------------------------------------

import os
import tempfile

import yaml

from record_export import main


class TestCLI:
    """Unit tests for CLI argument parsing and main() function.

    **Validates: Requirements 2.1, 2.5**
    """

    def test_default_output_path(self) -> None:
        """main(["--dry-run"]) returns 0 (dry-run doesn't write)."""
        result = main(["--dry-run"])
        assert result == 0

    def test_custom_output_path(self) -> None:
        """main(["--output", path, "--dry-run"]) returns 0."""
        result = main(["--output", "/tmp/test_record.yaml", "--dry-run"])
        assert result == 0

    def test_overwrite_flag_accepted(self) -> None:
        """--overwrite flag is accepted without error."""
        result = main(["--dry-run", "--overwrite"])
        assert result == 0

    def test_dry_run_prints_yaml(self, capsys) -> None:
        """main(["--dry-run"]) prints YAML content to stdout."""
        result = main(["--dry-run"])
        assert result == 0
        captured = capsys.readouterr()
        assert "metadata:" in captured.out
        assert "track_progress:" in captured.out

    def test_overwrite_check_blocks_existing_file(self, tmp_path) -> None:
        """Existing file without --overwrite returns 1."""
        temp_file = tmp_path / "existing_record.yaml"
        temp_file.write_text("existing content")
        result = main(["--output", str(temp_file)])
        assert result == 1

    def test_overwrite_check_allows_with_flag(self, tmp_path) -> None:
        """Existing file with --overwrite returns 0."""
        temp_file = tmp_path / "existing_record.yaml"
        temp_file.write_text("existing content")
        result = main(["--output", str(temp_file), "--overwrite"])
        assert result == 0

    def test_writes_file_to_output_path(self, tmp_path) -> None:
        """main writes a valid YAML file to the specified output path."""
        output_file = tmp_path / "output_record.yaml"
        result = main(["--output", str(output_file)])
        assert result == 0
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        assert isinstance(parsed, dict)
        assert "metadata" in parsed
        assert "track_progress" in parsed


# ---------------------------------------------------------------------------
# Property Tests: DataSourceEntry contains no actual record data
# ---------------------------------------------------------------------------

from record_export import DataSourceEntry


# Known file formats that data_sources.yaml entries should use
_KNOWN_FORMATS = {"csv", "json", "jsonl", "xml", "tsv", "txt", "parquet", "avro", "xlsx"}

# Patterns that indicate actual record data (not metadata)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_FULL_ADDRESS_RE = re.compile(r"\d+\s+\w+\s+(st|street|ave|avenue|rd|road|blvd|dr|lane|ln)",
                              re.IGNORECASE)


@st.composite
def st_data_source_yaml(draw) -> str:
    """Generate mock data_sources.yaml content with various source entries."""
    num_entries = draw(st.integers(min_value=1, max_value=5))
    lines: list[str] = []

    for _ in range(num_entries):
        name = draw(st.from_regex(r"[a-z][a-z0-9_]{2,15}", fullmatch=True))
        file_format = draw(st.sampled_from(["csv", "json", "jsonl", "xml", "tsv"]))
        # Generate a plausible relative file path
        subdir = draw(st.sampled_from(["data/raw", "data/input", "data"]))
        filename = f"{name}.{file_format}"
        file_path = f"{subdir}/{filename}"
        # record_count: either a number or null
        record_count = draw(st.one_of(
            st.just("null"),
            st.integers(min_value=0, max_value=1000000).map(str),
        ))
        module = draw(st.just("4"))

        lines.append(f"- name: {name}")
        lines.append(f"  file_path: {file_path}")
        lines.append(f"  file_format: {file_format}")
        lines.append(f"  record_count: {record_count}")
        lines.append(f"  module: {module}")

    return "\n".join(lines)


class TestDataSourceProperty:
    """Property-based tests for DataSourceEntry containing no actual record data.

    **Validates: Requirement 5.4, 11.1**
    """

    @given(yaml_content=st_data_source_yaml())
    @settings(max_examples=20)
    def test_data_source_entries_contain_no_actual_record_data(
        self, yaml_content: str
    ) -> None:
        """Property 5: Data source entries contain no actual record data.

        For any DataSourceEntry produced by DecisionCollector.collect_data_sources(),
        the entry SHALL contain only name, file_path, file_format, record_count,
        and module fields. No field SHALL contain data that could be a record value
        (content from the actual data file).

        **Validates: Requirement 5.4, 11.1**
        """

        def mock_reader(path: str) -> str | None:
            if "data_sources.yaml" in path:
                return yaml_content
            return None

        collector = DecisionCollector("/project", file_reader=mock_reader)
        entries = collector.collect_data_sources()

        # Expected fields for DataSourceEntry
        expected_fields = {"name", "file_path", "file_format", "record_count", "module"}

        for entry in entries:
            # Verify entry only has the expected fields
            actual_fields = set(dataclasses.fields(entry).__class__.__name__
                                for _ in [None])  # dummy
            entry_fields = {f.name for f in dataclasses.fields(entry)}
            assert entry_fields == expected_fields, (
                f"DataSourceEntry has unexpected fields: "
                f"{entry_fields - expected_fields}"
            )

            # name field is a short identifier (not a full record)
            assert len(entry.name) <= 100, (
                f"name field too long to be an identifier: {entry.name!r}"
            )
            assert "\n" not in entry.name, (
                f"name field contains newline (looks like record data): {entry.name!r}"
            )
            # name should not look like an email address
            assert not _EMAIL_RE.fullmatch(entry.name), (
                f"name field looks like an email address: {entry.name!r}"
            )

            # file_path field looks like a file path (contains / or .)
            if entry.file_path:
                assert "/" in entry.file_path or "." in entry.file_path, (
                    f"file_path doesn't look like a path: {entry.file_path!r}"
                )
                # file_path should not contain actual data patterns
                assert not _EMAIL_RE.search(entry.file_path), (
                    f"file_path contains email-like data: {entry.file_path!r}"
                )
                assert not _FULL_ADDRESS_RE.search(entry.file_path), (
                    f"file_path contains address-like data: {entry.file_path!r}"
                )

            # file_format field is a known format string
            if entry.file_format:
                assert entry.file_format.lower() in _KNOWN_FORMATS, (
                    f"file_format is not a known format: {entry.file_format!r}"
                )

            # record_count is either None or a non-negative integer
            if entry.record_count is not None:
                assert isinstance(entry.record_count, int), (
                    f"record_count is not an int: {type(entry.record_count)}"
                )
                assert entry.record_count >= 0, (
                    f"record_count is negative: {entry.record_count}"
                )

            # No field contains what looks like actual data
            # Check all string fields for PII-like patterns
            for field_name in ("name", "file_path", "file_format"):
                value = getattr(entry, field_name)
                if value:
                    # Should not contain email addresses
                    assert not _EMAIL_RE.search(value), (
                        f"Field '{field_name}' contains email-like data: {value!r}"
                    )
                    # Should not contain full street addresses
                    assert not _FULL_ADDRESS_RE.search(value), (
                        f"Field '{field_name}' contains address-like data: {value!r}"
                    )


# ---------------------------------------------------------------------------
# Property Tests: All paths in manifest are relative after sanitization
# ---------------------------------------------------------------------------


class TestPathSanitization:
    """Property-based tests for full pipeline path sanitization.

    **Validates: Requirement 11.3**
    """

    @given(
        ds_path=st_absolute_path(),
        script_path=st_absolute_path(),
        query_path=st_absolute_path(),
    )
    @settings(max_examples=20)
    def test_all_paths_relative_after_sanitization(
        self, ds_path: str, script_path: str, query_path: str
    ) -> None:
        """Property 6: All paths in manifest are relative after sanitization.

        For any DecisionManifest produced after sanitization, every string value
        that represents a file path (in data_sources[].file_path,
        loading_config.script_files[], query_programs[].filename) SHALL NOT
        start with `/` or a Windows drive letter.

        **Validates: Requirement 11.3**
        """
        # Build a manifest with absolute paths in all path fields
        manifest = DecisionManifest(
            metadata={
                "schema_version": "1.0",
                "generated_at": "2026-01-01T00:00:00Z",
                "power_version": "1.0.0",
            },
            track_progress={"track_name": "Core Bootcamp", "modules_completed": []},
            business_problem=None,
            sdk_setup=None,
            data_sources=[
                {
                    "name": "test_source",
                    "file_path": ds_path,
                    "file_format": "csv",
                    "record_count": 100,
                    "module": 4,
                }
            ],
            mapping_decisions=[],
            loading_config={
                "strategy": "single_source",
                "script_files": [script_path],
                "redo_processing": False,
                "redo_reason": None,
                "module": 6,
            },
            query_programs=[
                {
                    "filename": query_path,
                    "query_type": "search_by_attributes",
                    "description": "test query",
                    "module": 7,
                }
            ],
            performance_tuning=None,
            security_hardening=None,
            monitoring_config=None,
            deployment=None,
            replay_notes=[],
        )

        # Run through sanitizer (full pipeline: sanitize walks all fields)
        sanitizer = SecuritySanitizer()
        project_root = "/home/user/project"
        sanitized, warnings = sanitizer.sanitize(manifest, project_root)

        # Verify data_sources file_path is relative
        for ds in sanitized.data_sources:
            fp = ds["file_path"]
            assert not fp.startswith("/"), (
                f"data_sources file_path still absolute after sanitization: {fp!r}"
            )
            assert not _WINDOWS_DRIVE_RE.match(fp), (
                f"data_sources file_path still has drive letter: {fp!r}"
            )

        # Verify loading_config script_files are relative
        if sanitized.loading_config:
            for sf in sanitized.loading_config["script_files"]:
                assert not sf.startswith("/"), (
                    f"loading_config script_file still absolute: {sf!r}"
                )
                assert not _WINDOWS_DRIVE_RE.match(sf), (
                    f"loading_config script_file still has drive letter: {sf!r}"
                )

        # Verify query_programs filename is relative
        for qp in sanitized.query_programs:
            fn = qp["filename"]
            assert not fn.startswith("/"), (
                f"query_programs filename still absolute: {fn!r}"
            )
            assert not _WINDOWS_DRIVE_RE.match(fn), (
                f"query_programs filename still has drive letter: {fn!r}"
            )

# ---------------------------------------------------------------------------
# Integration Tests: Full pipeline with fixture data
# ---------------------------------------------------------------------------


class TestIntegration:
    """Integration test: full pipeline with fixture data produces valid YAML.

    Tests the complete flow: collect_all → assemble → sanitize → write.
    """

    def test_full_pipeline_produces_valid_yaml_with_expected_sections(self) -> None:
        """Full pipeline with fixture data produces valid YAML with expected sections."""
        # Fixture data
        preferences_yaml = (
            "language: python\n"
            "track: core_bootcamp\n"
            "database_type: sqlite\n"
            "deployment_target: null\n"
            "cloud_provider: null\n"
            "verbosity: normal\n"
        )
        progress_json = (
            '{"modules_completed": [1, 2, 3, 4, 5, 6, 7], "current_module": null}'
        )
        data_sources_yaml = (
            "- name: crm_customers\n"
            "  file_path: data/raw/crm_customers.csv\n"
            "  file_format: csv\n"
            "  record_count: 10000\n"
            "- name: billing_records\n"
            "  file_path: data/raw/billing_records.jsonl\n"
            "  file_format: jsonl\n"
            "  record_count: 8500\n"
        )
        journal_md = (
            "# Bootcamp Journal\n\n"
            "## Module 1: Business Problem\n\n"
            "### Problem Statement\n\n"
            "Deduplicate customer records across CRM and billing systems.\n\n"
            "### Data Sources\n\n"
            "- CRM export\n"
            "- Billing database dump\n\n"
            "### Success Criteria\n\n"
            "- Identify duplicate customers across systems\n"
            "- Achieve >90% precision on known duplicates\n\n"
            "## Module 2: SDK Setup\n\n"
            "Set up Python SDK with SQLite.\n"
        )

        # Injectable file_reader that provides fixture data
        def file_reader(path: str) -> str | None:
            if "bootcamp_preferences.yaml" in path:
                return preferences_yaml
            if "bootcamp_progress.json" in path:
                return progress_json
            if "data_sources.yaml" in path:
                return data_sources_yaml
            if "bootcamp_journal.md" in path:
                return journal_md
            return None

        # Injectable dir_lister that returns empty lists (no scripts)
        def dir_lister(path: str) -> list[str]:
            return []

        # Run the full pipeline
        collector = DecisionCollector(
            "/project", file_reader=file_reader, dir_lister=dir_lister
        )
        decisions = collector.collect_all()
        manifest = ManifestAssembler().assemble(decisions)
        sanitized, _warnings = SecuritySanitizer().sanitize(manifest, "/project")
        yaml_output = ManifestWriter().to_yaml(sanitized)

        # Parse the YAML output
        parsed = yaml.safe_load(yaml_output)

        # 1. Output is valid YAML (parseable)
        assert isinstance(parsed, dict)

        # 2. Contains metadata section with schema_version "1.0"
        assert "metadata" in parsed
        assert parsed["metadata"]["schema_version"] == "1.0"

        # 3. Contains track_progress section with correct track name
        assert "track_progress" in parsed
        assert parsed["track_progress"]["track_name"] == "Core Bootcamp"

        # 4. Contains sdk_setup section with language from preferences
        assert "sdk_setup" in parsed
        assert parsed["sdk_setup"]["language"] == "python"

        # 5. Contains data_sources section with 2 entries
        assert "data_sources" in parsed
        assert len(parsed["data_sources"]) == 2

        # 6. Contains business_problem section with problem statement
        assert "business_problem" in parsed
        assert "Deduplicate" in parsed["business_problem"]["problem_statement"]

        # 7. Contains replay_notes section
        assert "replay_notes" in parsed

        # 8. Does NOT contain None-valued optional sections
        assert "performance_tuning" not in parsed
        assert "security_hardening" not in parsed
        assert "monitoring_config" not in parsed
        assert "deployment" not in parsed

    def test_empty_project_produces_minimal_manifest_with_warnings(self) -> None:
        """Empty project (no config files, no source files) produces minimal manifest."""
        # file_reader always returns None (no files exist)
        def file_reader(path: str) -> str | None:
            return None

        # dir_lister always returns empty list (no directories)
        def dir_lister(path: str) -> list[str]:
            return []

        # Run the full pipeline
        collector = DecisionCollector(
            "/empty_project", file_reader=file_reader, dir_lister=dir_lister
        )
        decisions = collector.collect_all()
        manifest = ManifestAssembler().assemble(decisions)
        sanitized, _warnings = SecuritySanitizer().sanitize(manifest, "/empty_project")
        yaml_output = ManifestWriter().to_yaml(sanitized)

        # Parse the YAML output
        parsed = yaml.safe_load(yaml_output)

        # 1. Output is valid YAML
        assert isinstance(parsed, dict)

        # 2. Contains metadata section (always present)
        assert "metadata" in parsed
        assert parsed["metadata"]["schema_version"] == "1.0"
        assert "generated_at" in parsed["metadata"]
        assert "power_version" in parsed["metadata"]

        # 3. Contains track_progress section (always present, with "Unknown" track)
        assert "track_progress" in parsed
        assert parsed["track_progress"]["track_name"] == "Unknown"

        # 4. Does NOT contain sdk_setup (preferences were None)
        assert "sdk_setup" not in parsed

        # 5. Does NOT contain business_problem (journal was None)
        assert "business_problem" not in parsed

        # 6. data_sources is empty list
        assert parsed["data_sources"] == []

        # 7. mapping_decisions is empty list
        assert parsed["mapping_decisions"] == []

        # 8. query_programs is empty list
        assert parsed["query_programs"] == []

        # 9. Does NOT contain optional sections
        assert "performance_tuning" not in parsed
        assert "security_hardening" not in parsed
        assert "monitoring_config" not in parsed
        assert "deployment" not in parsed

        # 10. Contains replay_notes with entries about missing files
        assert "replay_notes" in parsed
        assert len(parsed["replay_notes"]) > 0

        # 11. The decisions.warnings list has multiple entries (one per missing file)
        assert len(decisions.warnings) > 1
        # Verify warnings mention missing required files
        warning_text = " ".join(decisions.warnings)
        assert "not found" in warning_text or "No " in warning_text


# ---------------------------------------------------------------------------
# Unit Tests: ManifestWriter overwrite protection
# ---------------------------------------------------------------------------


class TestOverwriteProtection:
    """Unit tests for ManifestWriter.write() overwrite protection behavior.

    **Validates: Requirement 2.5**
    """

    @staticmethod
    def _minimal_manifest() -> DecisionManifest:
        """Create a minimal DecisionManifest for testing."""
        return DecisionManifest(
            metadata={
                "schema_version": "1.0",
                "generated_at": "2026-01-01T00:00:00Z",
                "power_version": "1.0.0",
            },
            track_progress={
                "track_name": "Core Bootcamp",
                "modules_completed": [],
            },
            business_problem=None,
            sdk_setup=None,
            data_sources=[],
            mapping_decisions=[],
            loading_config=None,
            query_programs=[],
            performance_tuning=None,
            security_hardening=None,
            monitoring_config=None,
            deployment=None,
            replay_notes=[],
        )

    def test_write_raises_file_exists_error_without_overwrite(self, tmp_path) -> None:
        """write() raises FileExistsError when file exists and overwrite=False."""
        manifest = self._minimal_manifest()
        output_file = tmp_path / "existing.yaml"
        output_file.write_text("old content")

        writer = ManifestWriter()
        import pytest

        with pytest.raises(FileExistsError) as exc_info:
            writer.write(manifest, str(output_file), overwrite=False)

        # Error message should contain the file path
        assert str(output_file) in str(exc_info.value)

    def test_write_succeeds_with_overwrite_flag(self, tmp_path) -> None:
        """write() overwrites existing file when overwrite=True."""
        manifest = self._minimal_manifest()
        output_file = tmp_path / "existing.yaml"
        output_file.write_text("old content")

        writer = ManifestWriter()
        result = writer.write(manifest, str(output_file), overwrite=True)

        assert result == str(output_file)
        new_content = output_file.read_text()
        assert "old content" not in new_content
        assert "schema_version" in new_content

    def test_write_creates_new_file_without_overwrite(self, tmp_path) -> None:
        """write() creates a new file successfully when overwrite=False and file doesn't exist."""
        manifest = self._minimal_manifest()
        output_file = tmp_path / "new_output.yaml"

        writer = ManifestWriter()
        result = writer.write(manifest, str(output_file), overwrite=False)

        assert result == str(output_file)
        assert output_file.exists()
        content = output_file.read_text()
        assert "schema_version" in content

    def test_write_creates_parent_directories(self, tmp_path) -> None:
        """write() creates parent directories if they don't exist."""
        manifest = self._minimal_manifest()
        output_file = tmp_path / "nested" / "deep" / "dir" / "output.yaml"

        writer = ManifestWriter()
        result = writer.write(manifest, str(output_file), overwrite=False)

        assert result == str(output_file)
        assert output_file.exists()
        content = output_file.read_text()
        assert "schema_version" in content
