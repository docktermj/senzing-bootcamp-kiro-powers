"""Integration tests for the end-to-end TruthSet fallback acquisition flow.

Exercises the two layers of the ``truthset-fallback-source`` feature together,
with all network I/O mocked:

* the fetcher **script** ``scripts/fetch_fallback_truthset.py`` — real fetch ->
  normalize -> validate -> derive, driven through ``run_acquisition`` with
  ``urllib.request.urlopen`` patched, and
* the agent **decision logic** — modeled by the pure reference model
  ``tests/truthset_fallback_model.py`` (``classify_availability``,
  ``select_acquisition``, ``derive_module_status``).

A tiny orchestration helper (:func:`_orchestrate_step2`) mirrors Module 3 Step 2:
it classifies the ``get_sample_data`` response and, only when the primary is
unavailable, runs the fallback fetcher. Each of the four end-to-end scenarios
from the design's Testing Strategy gets its own integration test.

Feature: truthset-fallback-source
"""

from __future__ import annotations

import json
import sys
import urllib.error
from pathlib import Path
from unittest import mock

# ---------------------------------------------------------------------------
# Make scripts importable (scripts aren't packages)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from fetch_fallback_truthset import (  # noqa: E402
    OUTPUT_FILENAME,
    SourceConfig,
    run_acquisition,
)

# ---------------------------------------------------------------------------
# Make the co-located reference model importable
# ---------------------------------------------------------------------------

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from truthset_fallback_model import (  # noqa: E402
    AVAILABLE,
    BLOCKED,
    CORD_SUBSTITUTE,
    GITHUB_FALLBACK,
    INCOMPLETE,
    MCP_PRIMARY,
    NON_DETERMINISTIC,
    classify_availability,
    derive_module_status,
    select_acquisition,
)

# ---------------------------------------------------------------------------
# Fixtures / constants
# ---------------------------------------------------------------------------

# Placeholder base URL used only under a mocked ``urlopen`` — it is never
# actually contacted, and it is deliberately NOT the real sanctioned fallback
# URL (which lives solely in config/fallback_sources.yaml per the URL-governance
# rule), consistent with the properties test.
_BASE_URL = "https://fallback.example/truthsets/demo"

_RECORD_FILES = ["customers.jsonl", "watchlist.jsonl", "reference.jsonl"]
_TRUTH_KEY = "actual_truthset_key.csv"

# Small, deterministic inline fixtures for the success case. Records intentionally
# omit ``DATA_SOURCE`` so the normalizer derives it from the filename stem.
_CUSTOMERS_JSONL = "\n".join(
    [
        json.dumps({"RECORD_ID": "1001", "NAME_FULL": "Robert Smith"}),
        json.dumps({"RECORD_ID": "1002", "NAME_FULL": "Bob Smith"}),
        json.dumps({"RECORD_ID": "1003", "NAME_FULL": "Alice Jones"}),
        json.dumps({"RECORD_ID": "1004", "NAME_FULL": "Al Jones"}),
    ]
)
_WATCHLIST_JSONL = "\n".join(
    [
        json.dumps({"RECORD_ID": "2001", "NAME_FULL": "Robert Smith"}),
        json.dumps({"RECORD_ID": "2002", "NAME_FULL": "Carol White"}),
    ]
)
_REFERENCE_JSONL = "\n".join(
    [
        json.dumps({"RECORD_ID": "3001", "NAME_FULL": "Alice Jones"}),
        json.dumps({"RECORD_ID": "3002", "NAME_FULL": "Carol White"}),
    ]
)

# Ground-truth key with four distinct clusters, three of which own 2+ records so
# ``derive_expected_results`` yields >= 3 known matches (Req 5.2). Total records
# across the three record files (8) matches the rows here.
_TRUTH_KEY_CSV = "\n".join(
    [
        "CLUSTER_ID,RECORD_ID,DATA_SOURCE",
        "1,1001,CUSTOMERS",
        "1,2001,WATCHLIST",
        "2,1003,CUSTOMERS",
        "2,1004,CUSTOMERS",
        "2,3001,REFERENCE",
        "3,2002,WATCHLIST",
        "3,3002,REFERENCE",
        "4,1002,CUSTOMERS",
    ]
)

_SUCCESS_BODIES = {
    "customers.jsonl": _CUSTOMERS_JSONL,
    "watchlist.jsonl": _WATCHLIST_JSONL,
    "reference.jsonl": _REFERENCE_JSONL,
    _TRUTH_KEY: _TRUTH_KEY_CSV,
}

# get_sample_data-style responses the classifier reads (design §2 Classifier).
_PRIMARY_AVAILABLE_RESPONSE = {
    "datasets": [
        {
            "name": "Senzing TruthSet",
            "type": "truthset",
            "records": [{"RECORD_ID": "1001", "NAME_FULL": "Robert Smith"}],
        }
    ]
}
_CORD_ONLY_RESPONSE = {
    "datasets": [
        {"name": "Las Vegas", "type": "cord"},
        {"name": "London", "type": "cord"},
        {"name": "Moscow", "type": "cord"},
    ]
}


def _make_config() -> SourceConfig:
    """Build a ``SourceConfig`` pointing at the mocked placeholder base URL.

    Returns:
        A ``SourceConfig`` with the demo record files and truth key, mirroring
        the sanctioned registry entry but using a placeholder base URL.
    """
    return SourceConfig(
        source_id="senzing_truthset_demo",
        base_url=_BASE_URL,
        record_files=list(_RECORD_FILES),
        truth_key=_TRUTH_KEY,
        timeout_seconds=30,
    )


def _ok_response(body: str) -> mock.MagicMock:
    """Build a context-manager mock that emulates an HTTP 200 response.

    Args:
        body: The response body text; returned as UTF-8 bytes by ``read()``.

    Returns:
        A ``MagicMock`` whose ``getcode()`` returns 200 and ``read()`` returns
        ``body`` encoded as UTF-8, usable as a ``with`` context manager.
    """
    response = mock.MagicMock()
    response.getcode.return_value = 200
    response.read.return_value = body.encode("utf-8")
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


def _urlopen_side_effect(
    bodies: dict[str, str],
    errors: dict[str, Exception] | None = None,
):
    """Build a ``urlopen`` side-effect keyed on the requested filename.

    The returned callable inspects the ``urllib.request.Request`` passed to
    ``urlopen``, extracts the trailing filename from its URL, and either raises a
    configured error for that file or returns a 200 response carrying its body.

    Args:
        bodies: Mapping of filename to the 200-response body to serve.
        errors: Optional mapping of filename to an exception to raise instead of
            serving a body (e.g. an ``HTTPError`` or ``URLError``).

    Returns:
        A callable suitable for ``mock.patch(..., side_effect=...)``.
    """
    errors = errors or {}

    def _side_effect(request: urllib.request.Request, timeout: int | None = None):
        filename = request.full_url.rsplit("/", 1)[-1]
        if filename in errors:
            raise errors[filename]
        return _ok_response(bodies[filename])

    return _side_effect


def _orchestrate_step2(
    mcp_response: object,
    config: SourceConfig,
    output_dir: Path,
    *,
    cord_accepted: bool | None = None,
):
    """Mirror Module 3 Step 2: classify, then take the primary or fallback path.

    On the primary path (Primary_TruthSet available) the fetcher is never run,
    proving "fallback not attempted". Otherwise the fallback fetcher script runs
    and its status feeds the acquisition decision.

    Args:
        mcp_response: The parsed ``get_sample_data`` response to classify.
        config: The resolved fallback source configuration.
        output_dir: Directory the fetcher writes ``truthset_data.jsonl`` into.
        cord_accepted: The bootcamper's CORD-substitute decision, forwarded to
            the decision model when the fallback path fails.

    Returns:
        A ``(decision, fetch_status)`` tuple where ``fetch_status`` is ``None`` on
        the primary path and the fetcher's status dict on the fallback path.
    """
    availability = classify_availability(mcp_response)
    if availability == AVAILABLE:
        return select_acquisition(availability), None
    fetch_status = run_acquisition(config, output_dir)
    decision = select_acquisition(
        availability,
        fallback_outcome=fetch_status["status"],
        cord_accepted=cord_accepted,
    )
    return decision, fetch_status


# ---------------------------------------------------------------------------
# Scenario 1: Primary available -> fallback not attempted (Req 2.1)
# ---------------------------------------------------------------------------


class TestPrimaryAvailableFallbackNotAttempted:
    """Primary TruthSet available: the fallback fetcher is never invoked.

    Feature: truthset-fallback-source

    When ``get_sample_data`` exposes a named TruthSet with retrievable records,
    the classifier reports ``available``, acquisition provenance is
    ``mcp_primary``, and the fallback path (and therefore ``urlopen``) is never
    reached.

    **Validates: Requirements 2.1**
    """

    def test_primary_available_skips_fallback(self, tmp_path: Path) -> None:
        """The primary path uses MCP and never touches ``urlopen`` or the file.

        Args:
            tmp_path: Pytest-provided temporary directory for output isolation.
        """
        config = _make_config()
        with mock.patch(
            "fetch_fallback_truthset.urllib.request.urlopen"
        ) as urlopen:
            decision, fetch_status = _orchestrate_step2(
                _PRIMARY_AVAILABLE_RESPONSE, config, tmp_path
            )

        # Primary path chosen: provenance is mcp_primary and verification is
        # deterministic against MCP Expected_Results.
        assert decision.provenance == MCP_PRIMARY
        assert decision.expected_results_source == MCP_PRIMARY
        assert decision.deterministic is True

        # Fallback was not attempted at all.
        assert fetch_status is None
        urlopen.assert_not_called()
        assert not (tmp_path / OUTPUT_FILENAME).exists()


# ---------------------------------------------------------------------------
# Scenario 2: Primary unavailable -> fallback succeeds -> deterministic (Req 3.1)
# ---------------------------------------------------------------------------


class TestFallbackSuccessDeterministic:
    """Primary unavailable, fallback fetch succeeds, deterministic verification runs.

    Feature: truthset-fallback-source

    A CORD-only ``get_sample_data`` response classifies ``unavailable``; the
    fallback fetch returns HTTP 200 for every record file and a valid truth key,
    so acquisition succeeds, ``truthset_data.jsonl`` is written, expected results
    are derived, and provenance is ``github_fallback`` with deterministic
    verification enabled.

    **Validates: Requirements 3.1**
    """

    def test_fallback_success_writes_data_and_expected_results(
        self, tmp_path: Path
    ) -> None:
        """Fallback success yields a data file, expected results, and determinism.

        Args:
            tmp_path: Pytest-provided temporary directory for output isolation.
        """
        config = _make_config()
        with mock.patch(
            "fetch_fallback_truthset.urllib.request.urlopen",
            side_effect=_urlopen_side_effect(_SUCCESS_BODIES),
        ):
            decision, fetch_status = _orchestrate_step2(
                _CORD_ONLY_RESPONSE, config, tmp_path
            )

        # Fetcher-side outcome.
        assert fetch_status is not None
        assert fetch_status["status"] == "success"
        assert fetch_status["records_written"] == 8
        assert fetch_status["error"] is None

        # TruthSet_Data_File written with the expected records.
        output_path = tmp_path / OUTPUT_FILENAME
        assert output_path.exists()
        records = [
            json.loads(line)
            for line in output_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(records) == 8
        # DATA_SOURCE was derived from each source filename stem.
        assert {r["DATA_SOURCE"] for r in records} == {
            "CUSTOMERS",
            "WATCHLIST",
            "REFERENCE",
        }

        # Expected_Results present and structurally complete (>= 3 known matches).
        expected = fetch_status["expected_results"]
        assert expected is not None
        assert expected["expected_entity_count"] == 4
        assert expected["tolerance_percent"] == 5
        assert expected["source"] == "github_fallback"
        assert len(expected["known_matches"]) >= 3

        # Decision-side outcome: github_fallback with deterministic verification.
        assert decision.provenance == GITHUB_FALLBACK
        assert decision.expected_results_source == GITHUB_FALLBACK
        assert decision.deterministic is True


# ---------------------------------------------------------------------------
# Scenario 3: Primary unavailable -> fallback fails -> CORD offered (Req 7.1, 7.2)
# ---------------------------------------------------------------------------


class TestFallbackFailsCordOffered:
    """Primary unavailable and fallback unreachable: graceful degradation to CORD.

    Feature: truthset-fallback-source

    A CORD-only response classifies ``unavailable``; the fallback fetch fails
    (network error), so acquisition returns ``fetch_failed`` and the module
    offers the CORD substitute. Accepting yields ``cord_substitute`` +
    non-deterministic verification; declining is ``blocked``. Either degraded
    outcome forces the overall Module 3 status to ``incomplete``.

    **Validates: Requirements 7.1, 7.2**
    """

    def test_fallback_failure_routes_to_cord_and_incomplete(
        self, tmp_path: Path
    ) -> None:
        """Fetch failure leads to a CORD offer and an incomplete module status.

        Args:
            tmp_path: Pytest-provided temporary directory for output isolation.
        """
        config = _make_config()
        # The very first fetch fails with a network error -> whole fallback fails.
        errors = {"customers.jsonl": urllib.error.URLError("connection refused")}
        with mock.patch(
            "fetch_fallback_truthset.urllib.request.urlopen",
            side_effect=_urlopen_side_effect(_SUCCESS_BODIES, errors=errors),
        ):
            fetch_status = run_acquisition(config, tmp_path)

        # Fallback classified unreachable.
        assert fetch_status["status"] == "fetch_failed"
        assert not (tmp_path / OUTPUT_FILENAME).exists()

        # Bootcamper accepts the CORD substitute: non-deterministic, cord_substitute.
        accepted = select_acquisition(
            classify_availability(_CORD_ONLY_RESPONSE),
            fallback_outcome=fetch_status["status"],
            cord_accepted=True,
        )
        assert accepted.provenance == CORD_SUBSTITUTE
        assert accepted.expected_results_source == NON_DETERMINISTIC
        assert accepted.deterministic is False

        # Bootcamper declines the CORD substitute: blocked, no provenance.
        declined = select_acquisition(
            classify_availability(_CORD_ONLY_RESPONSE),
            fallback_outcome=fetch_status["status"],
            cord_accepted=False,
        )
        assert declined.provenance is None
        assert declined.expected_results_source == BLOCKED
        assert declined.deterministic is False

        # Both degraded outcomes force overall Module 3 status to incomplete.
        assert derive_module_status(NON_DETERMINISTIC) == INCOMPLETE
        assert derive_module_status(BLOCKED) == INCOMPLETE


# ---------------------------------------------------------------------------
# Scenario 4: Primary unavailable -> one file 404 -> classified unreachable (Req 3.4)
# ---------------------------------------------------------------------------


class TestFallbackPartialFailureUnreachable:
    """A single 404 among the fallback files makes the whole fallback unreachable.

    Feature: truthset-fallback-source

    When the first record file returns HTTP 200 but a later record file raises
    HTTP 404, no partial acquisition is allowed: ``run_acquisition`` returns
    ``fetch_failed`` with the 404 recorded and leaves no ``truthset_data.jsonl``
    success artifact behind.

    **Validates: Requirements 3.4**
    """

    def test_one_file_404_yields_fetch_failed_no_artifact(
        self, tmp_path: Path
    ) -> None:
        """A later-file 404 fails the whole fallback and writes no data file.

        Args:
            tmp_path: Pytest-provided temporary directory for output isolation.
        """
        config = _make_config()
        # First record file (customers.jsonl) succeeds; a later one (reference.jsonl)
        # 404s, so the whole fallback is unreachable (no partial acquisition).
        not_found = urllib.error.HTTPError(
            url=f"{_BASE_URL}/reference.jsonl",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )
        errors = {"reference.jsonl": not_found}
        with mock.patch(
            "fetch_fallback_truthset.urllib.request.urlopen",
            side_effect=_urlopen_side_effect(_SUCCESS_BODIES, errors=errors),
        ):
            fetch_status = run_acquisition(config, tmp_path)

        assert fetch_status["status"] == "fetch_failed"
        # The specific HTTP status code is recorded.
        assert "404" in fetch_status["error"]
        assert "reference.jsonl" in fetch_status["error"]
        # No partial/valid success artifact is left behind.
        assert not (tmp_path / OUTPUT_FILENAME).exists()
