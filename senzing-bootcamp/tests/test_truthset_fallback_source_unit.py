"""Example-based unit tests for the TruthSet fallback source acquisition script.

Covers the specific edge cases that complement the property-based suite in
``test_truthset_fallback_source_properties.py``. These tests exercise concrete
examples against ``scripts/fetch_fallback_truthset.py`` (registry parsing, HTTP
error codes, timeouts, empty bodies, and truth-key thresholds), plus structural
assertions on the shipped steering files and the documented progress-file schema.

Feature: truthset-fallback-source

Requirements exercised: 3.4, 3.5, 5.2, 5.4, 6.1, 6.2

Note: the raw fallback URL is deliberately never written as a literal in this
file. Doing so would violate the single-source-of-truth governance rule
(Requirement 6.1 / Property 7): the URL is declared only in
``config/fallback_sources.yaml``. Any URL needed at runtime is read from the
registry, and URL assertions check structure without embedding the host.
"""

from __future__ import annotations

import socket
import sys
import urllib.error
from pathlib import Path
from unittest import mock

import pytest

# ---------------------------------------------------------------------------
# Make scripts importable (scripts aren't packages) and the tests directory
# importable (for the co-located URL-governance helper).
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from fetch_fallback_truthset import (  # noqa: E402
    ExpectedResultsError,
    FetchError,
    FetchedContent,
    SourceConfig,
    derive_expected_results,
    fetch_file,
    load_source_config,
    normalize_records,
    parse_registry,
    validate_jsonl,
)
from truthset_fallback_url_governance import (  # noqa: E402
    default_power_root,
    find_raw_url_violations,
)

# ---------------------------------------------------------------------------
# Shared paths and constants
# ---------------------------------------------------------------------------

_POWER_ROOT = Path(__file__).resolve().parent.parent
_REGISTRY_PATH = _POWER_ROOT / "config" / "fallback_sources.yaml"
_STEERING_DIR = _POWER_ROOT / "steering"
_PHASE1_STEERING = _STEERING_DIR / "module-03-phase1-verification.md"
_SYSTEM_STEERING = _STEERING_DIR / "module-03-system-verification.md"

# The sanctioned fallback source is referenced everywhere by this registry
# identifier, never by its raw URL (Requirement 6.1). The identifier is safe to
# embed; the URL is not.
_SOURCE_ID = "senzing_truthset_demo"

# The provenance labels documented in the design "Progress File Extensions".
_VALID_PROVENANCE = {"mcp_primary", "github_fallback", "cord_substitute"}

# Placeholder base URL used only to drive ``fetch_file`` under a mocked
# ``urlopen``. It is never contacted and is deliberately not the real sanctioned
# URL (which lives solely in the registry).
_PLACEHOLDER_BASE_URL = "https://fallback.example/truthsets/demo"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_truth_key_csv(rows: list[tuple[str, str, str]]) -> str:
    """Build truth-key CSV text from ``(cluster_id, record_id, data_source)`` rows.

    Args:
        rows: The data rows, each a ``(CLUSTER_ID, RECORD_ID, DATA_SOURCE)`` tuple.

    Returns:
        CSV text with the required header row followed by one line per row.
    """
    lines = ["CLUSTER_ID,RECORD_ID,DATA_SOURCE"]
    lines.extend(f"{cluster},{record},{source}" for cluster, record, source in rows)
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Registry YAML parsing (Requirements 6.1, 6.2)
# ---------------------------------------------------------------------------


class TestRegistryYamlParsing:
    """Unit tests for registry YAML parsing and source resolution.

    Validates that the real ``config/fallback_sources.yaml`` resolves to the
    expected ``SourceConfig`` (Requirements 6.1, 6.2) and that ``parse_registry``
    handles the minimal YAML subset (nested mappings and scalar list blocks).
    """

    def test_real_registry_resolves_expected_source_config(self) -> None:
        """The shipped registry resolves to the documented fallback source."""
        config = load_source_config(_REGISTRY_PATH, _SOURCE_ID)

        assert isinstance(config, SourceConfig)
        assert config.source_id == _SOURCE_ID
        assert config.record_files == ["customers.jsonl", "watchlist.jsonl", "reference.jsonl"]
        assert config.truth_key == "actual_truthset_key.csv"
        assert config.timeout_seconds == 30
        assert isinstance(config.timeout_seconds, int)

        # Assert URL structure without embedding the host literal (governance).
        assert config.base_url.startswith("https://")
        assert config.base_url.endswith("truthsets/demo")
        assert "truth-sets" in config.base_url

    def test_parse_registry_scalar_mapping(self) -> None:
        """A flat mapping of scalar values parses into a plain dict."""
        text = 'version: "1"\nname: demo\ntimeout_seconds: 30\n'

        result = parse_registry(text)

        assert result == {"version": "1", "name": "demo", "timeout_seconds": "30"}

    def test_parse_registry_nested_mapping_with_list_block(self) -> None:
        """A nested mapping containing a scalar list block parses structurally."""
        text = (
            "files:\n"
            "  records:\n"
            "    - customers.jsonl\n"
            "    - watchlist.jsonl\n"
            "  truth_key: actual_truthset_key.csv\n"
        )

        result = parse_registry(text)

        assert result == {
            "files": {
                "records": ["customers.jsonl", "watchlist.jsonl"],
                "truth_key": "actual_truthset_key.csv",
            }
        }

    def test_parse_registry_ignores_comments_and_blank_lines(self) -> None:
        """Comment lines, blank lines, and inline comments are discarded."""
        text = "# leading comment\n\nversion: 1  # inline comment\nname: demo\n"

        result = parse_registry(text)

        assert result == {"version": "1", "name": "demo"}


# ---------------------------------------------------------------------------
# HTTP error codes (Requirement 3.4)
# ---------------------------------------------------------------------------


class TestHttpErrorCodes:
    """Unit tests for specific HTTP error-code classification.

    Validates that a non-200 status delivered as an ``HTTPError`` from
    ``urlopen`` is normalized into a ``FetchError`` whose message records the
    specific status code (Requirement 3.4).
    """

    @pytest.mark.parametrize("status_code", [404, 500, 503])
    def test_http_error_code_raises_fetch_error_recording_code(
        self, status_code: int
    ) -> None:
        """A 404, 500, or 503 becomes a ``FetchError`` naming the status code.

        Args:
            status_code: The HTTP error status returned by the mocked ``urlopen``.
        """
        http_error = urllib.error.HTTPError(
            url=f"{_PLACEHOLDER_BASE_URL}/customers.jsonl",
            code=status_code,
            msg="error",
            hdrs=None,
            fp=None,
        )
        with mock.patch(
            "fetch_fallback_truthset.urllib.request.urlopen",
            side_effect=http_error,
        ):
            with pytest.raises(FetchError) as exc_info:
                fetch_file(_PLACEHOLDER_BASE_URL, "customers.jsonl", timeout=30)

        assert str(status_code) in exc_info.value.message
        assert "customers.jsonl" in exc_info.value.message


# ---------------------------------------------------------------------------
# Timeout simulation (Requirement 3.5)
# ---------------------------------------------------------------------------


class TestTimeoutSimulation:
    """Unit tests for fetch timeout handling.

    Validates that a request that times out is terminated and surfaced as a
    ``FetchError`` whose message identifies the timeout and its duration
    (Requirement 3.5).
    """

    @pytest.mark.parametrize(
        "timeout_exc",
        [socket.timeout("timed out"), TimeoutError("timed out")],
        ids=["socket_timeout", "timeout_error"],
    )
    def test_timeout_raises_fetch_error_with_timeout_message(
        self, timeout_exc: BaseException
    ) -> None:
        """A timeout exception from ``urlopen`` becomes a timeout ``FetchError``.

        Args:
            timeout_exc: The timeout exception raised by the mocked ``urlopen``.
        """
        with mock.patch(
            "fetch_fallback_truthset.urllib.request.urlopen",
            side_effect=timeout_exc,
        ):
            with pytest.raises(FetchError) as exc_info:
                fetch_file(_PLACEHOLDER_BASE_URL, "customers.jsonl", timeout=30)

        assert "Timeout" in exc_info.value.message
        assert "30" in exc_info.value.message

    def test_urlerror_wrapping_timeout_is_classified_as_timeout(self) -> None:
        """A ``URLError`` whose reason is a timeout is reported as a timeout."""
        url_error = urllib.error.URLError(reason=socket.timeout("timed out"))
        with mock.patch(
            "fetch_fallback_truthset.urllib.request.urlopen",
            side_effect=url_error,
        ):
            with pytest.raises(FetchError) as exc_info:
                fetch_file(_PLACEHOLDER_BASE_URL, "customers.jsonl", timeout=30)

        assert "Timeout" in exc_info.value.message


# ---------------------------------------------------------------------------
# Empty response handling
# ---------------------------------------------------------------------------


class TestEmptyResponseHandling:
    """Unit tests for empty and blank record-file bodies.

    Validates that an empty (or whitespace-only) fetched body normalizes to zero
    records and that validating a zero-record output against an expected count of
    zero succeeds, so an empty body is handled without spurious failure.
    """

    def test_empty_body_normalizes_to_zero_records(self, tmp_path: Path) -> None:
        """An empty record body writes zero records and validates against zero.

        Args:
            tmp_path: Pytest-provided temporary directory for the output file.
        """
        fetched = FetchedContent(records={"customers.jsonl": ""})
        output_path = tmp_path / "truthset_data.jsonl"

        count = normalize_records(fetched, output_path)

        assert count == 0
        assert output_path.exists()
        assert output_path.read_text(encoding="utf-8") == ""
        # Zero records validated against a zero expectation must not raise.
        validate_jsonl(output_path, 0)

    def test_blank_lines_only_body_normalizes_to_zero_records(
        self, tmp_path: Path
    ) -> None:
        """A whitespace-only body is treated as zero records.

        Args:
            tmp_path: Pytest-provided temporary directory for the output file.
        """
        fetched = FetchedContent(records={"customers.jsonl": "\n   \n\t\n"})
        output_path = tmp_path / "truthset_data.jsonl"

        count = normalize_records(fetched, output_path)

        assert count == 0
        validate_jsonl(output_path, 0)


# ---------------------------------------------------------------------------
# Truth key thresholds (Requirements 5.2, 5.4)
# ---------------------------------------------------------------------------


class TestTruthKeyThresholds:
    """Unit tests for expected-results derivation at the known-match boundary.

    Validates the minimum (exactly three multi-record clusters succeed,
    Requirement 5.2) and failure (fewer than three multi-record clusters raise,
    Requirement 5.4) behaviors of ``derive_expected_results``.
    """

    def test_exactly_three_multi_record_clusters_succeed(self) -> None:
        """Three multi-record clusters (plus singletons) yield >= 3 known matches."""
        csv_text = _make_truth_key_csv(
            [
                ("C1", "1001", "CUSTOMERS"),
                ("C1", "1002", "CUSTOMERS"),
                ("C2", "1003", "CUSTOMERS"),
                ("C2", "2001", "WATCHLIST"),
                ("C3", "3001", "REFERENCE"),
                ("C3", "1004", "CUSTOMERS"),
                ("C4", "1005", "CUSTOMERS"),  # singleton
                ("C5", "2002", "WATCHLIST"),  # singleton
            ]
        )

        expected = derive_expected_results(csv_text)

        # Distinct CLUSTER_ID count includes the singletons (Req 5.2).
        assert expected["expected_entity_count"] == 5
        # Only multi-record clusters become known matches; exactly three here.
        assert len(expected["known_matches"]) >= 3
        assert len(expected["known_matches"]) == 3
        for entry in expected["known_matches"]:
            assert len(entry["records"]) >= 2
        assert expected["tolerance_percent"] == 5
        assert expected["source"] == "github_fallback"

    @pytest.mark.parametrize(
        "rows",
        [
            # Zero multi-record clusters (all singletons) -> failure case (Req 5.4).
            [
                ("C1", "1001", "CUSTOMERS"),
                ("C2", "1002", "CUSTOMERS"),
                ("C3", "1003", "WATCHLIST"),
            ],
            # Two multi-record clusters (below the minimum of three) -> failure.
            [
                ("C1", "1001", "CUSTOMERS"),
                ("C1", "1002", "CUSTOMERS"),
                ("C2", "2001", "WATCHLIST"),
                ("C2", "2002", "WATCHLIST"),
                ("C3", "3001", "REFERENCE"),  # singleton
            ],
        ],
        ids=["zero_multi_record_clusters", "two_multi_record_clusters"],
    )
    def test_insufficient_multi_record_clusters_raise(
        self, rows: list[tuple[str, str, str]]
    ) -> None:
        """Fewer than three multi-record clusters raise ``ExpectedResultsError``.

        Args:
            rows: The truth-key rows producing fewer than three known matches.
        """
        csv_text = _make_truth_key_csv(rows)

        with pytest.raises(ExpectedResultsError):
            derive_expected_results(csv_text)


# ---------------------------------------------------------------------------
# Steering file content assertions (Requirement 6.1)
# ---------------------------------------------------------------------------


class TestSteeringFileContent:
    """Unit tests asserting the shipped Module 3 steering documents the fallback.

    Validates that both steering files document the fallback path and reference
    the sanctioned source by its registry identifier, and that neither embeds the
    raw fallback URL (Requirement 6.1).
    """

    def test_steering_documents_fallback_path_by_registry_id(self) -> None:
        """Both steering files document the fallback path and cite the registry id."""
        phase1 = _PHASE1_STEERING.read_text(encoding="utf-8")
        system = _SYSTEM_STEERING.read_text(encoding="utf-8")

        # Registry identifier is used to reference the sanctioned source.
        assert _SOURCE_ID in phase1
        assert _SOURCE_ID in system

        # The fallback path is documented in both files.
        assert "fallback" in phase1.lower()
        assert "fallback" in system.lower()

        # The registry file is referenced by name (not the raw URL).
        assert "fallback_sources.yaml" in phase1
        assert "fallback_sources.yaml" in system

        # The system-verification file carries the dedicated section.
        assert "TruthSet Fallback Source" in system

    def test_steering_files_contain_no_raw_fallback_url(self) -> None:
        """Neither steering file embeds the raw fallback URL (single source)."""
        base_url = load_source_config(_REGISTRY_PATH, _SOURCE_ID).base_url

        phase1 = _PHASE1_STEERING.read_text(encoding="utf-8")
        system = _SYSTEM_STEERING.read_text(encoding="utf-8")
        assert base_url not in phase1
        assert base_url not in system

        # Cross-check with the governance scanner: neither file is a violator.
        violators = {path.resolve() for path in find_raw_url_violations(default_power_root())}
        assert _PHASE1_STEERING.resolve() not in violators
        assert _SYSTEM_STEERING.resolve() not in violators


# ---------------------------------------------------------------------------
# Progress file schema after each provenance path
# ---------------------------------------------------------------------------


def _acquisition_check(checkpoint: dict) -> dict:
    """Extract the ``truthset_acquisition`` check from a checkpoint dict.

    Args:
        checkpoint: A ``config/bootcamp_progress.json``-shaped checkpoint dict.

    Returns:
        The nested ``truthset_acquisition`` check mapping.
    """
    return checkpoint["module_3_verification"]["checks"]["truthset_acquisition"]


def _assert_acquisition_schema(checkpoint: dict) -> None:
    """Assert a checkpoint carries the required acquisition-schema fields.

    Args:
        checkpoint: A ``config/bootcamp_progress.json``-shaped checkpoint dict.
    """
    check = _acquisition_check(checkpoint)
    assert "status" in check
    assert "source_provenance" in check
    assert check["source_provenance"] in _VALID_PROVENANCE


class TestProgressFileSchema:
    """Schema/shape assertions on the documented progress-file checkpoints.

    Validates that the ``truthset_acquisition`` checkpoint documented for each
    provenance path (``mcp_primary``, ``github_fallback``, ``cord_substitute``)
    carries the required keys and values from the design "Progress File
    Extensions" and the Step 2 / Step 2a checkpoints in the steering.
    """

    def test_mcp_primary_checkpoint_schema(self) -> None:
        """The primary-path checkpoint records ``mcp_primary`` with no fallback."""
        checkpoint = {
            "module_3_verification": {
                "checks": {
                    "truthset_acquisition": {
                        "status": "passed",
                        "records": 48,
                        "source_provenance": "mcp_primary",
                        "primary_available": True,
                        "classification_reason": "truthset_found",
                        "fallback_attempted": False,
                        "fallback_error": None,
                    }
                }
            }
        }

        _assert_acquisition_schema(checkpoint)
        check = _acquisition_check(checkpoint)
        assert check["source_provenance"] == "mcp_primary"
        assert check["primary_available"] is True
        assert check["classification_reason"] == "truthset_found"
        assert check["fallback_attempted"] is False
        assert check["status"] == "passed"

    def test_github_fallback_checkpoint_schema(self) -> None:
        """The fallback-path checkpoint records ``github_fallback`` after fallback."""
        checkpoint = {
            "module_3_verification": {
                "checks": {
                    "truthset_acquisition": {
                        "status": "passed",
                        "records": 48,
                        "source_provenance": "github_fallback",
                        "primary_available": False,
                        "classification_reason": "cord_only",
                        "fallback_attempted": True,
                        "fallback_error": None,
                    }
                }
            }
        }

        _assert_acquisition_schema(checkpoint)
        check = _acquisition_check(checkpoint)
        assert check["source_provenance"] == "github_fallback"
        assert check["primary_available"] is False
        assert check["classification_reason"] == "cord_only"
        assert check["fallback_attempted"] is True
        assert check["status"] == "passed"

    def test_cord_substitute_degraded_checkpoint_schema(self) -> None:
        """The degraded checkpoint records ``cord_substitute`` and incomplete module."""
        checkpoint = {
            "module_3_verification": {
                "checks": {
                    "truthset_acquisition": {
                        "status": "non_deterministic",
                        "source_provenance": "cord_substitute",
                        "deterministic_verification": "non_deterministic",
                    }
                },
                "status": "incomplete",
            }
        }

        _assert_acquisition_schema(checkpoint)
        check = _acquisition_check(checkpoint)
        assert check["source_provenance"] == "cord_substitute"
        assert check["deterministic_verification"] == "non_deterministic"
        assert checkpoint["module_3_verification"]["status"] == "incomplete"
