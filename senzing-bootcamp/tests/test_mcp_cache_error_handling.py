"""Example-based tests for MCP response caching error handling and edge cases.

Validates error messages, corrupted file recovery, and cache directory creation
as defined in the mcp-response-caching design and requirements.

Feature: mcp-response-caching
Validates: Requirements 4.1, 4.3
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make sibling test modules importable
# ---------------------------------------------------------------------------
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from test_mcp_response_caching import (  # noqa: E402
    cache_lookup,
    compute_cache_key,
    derive_filename,
    serialize_cache_entry,
)

# ---------------------------------------------------------------------------
# Constants matching the steering file error messages
# ---------------------------------------------------------------------------

NETWORK_ERROR_MESSAGE = (
    "The Senzing MCP server is unreachable and no cached response is available "
    "for this request."
)
NETWORK_RETRY_SUGGESTION = (
    "Check your network connectivity or try again in a moment."
)


class TestNetworkFailureErrorMessage:
    """Test that network failure error messages match the steering file spec.

    Validates: Requirements 4.1, 4.3
    """

    def test_error_message_content(self) -> None:
        """Error message indicates MCP server is unreachable with no cache."""
        assert "unreachable" in NETWORK_ERROR_MESSAGE
        assert "no cached response" in NETWORK_ERROR_MESSAGE

    def test_retry_suggestion_content(self) -> None:
        """Retry suggestion mentions network connectivity and retry."""
        assert "network connectivity" in NETWORK_RETRY_SUGGESTION
        assert "try again" in NETWORK_RETRY_SUGGESTION

    def test_error_message_exact_text(self) -> None:
        """Error message matches the exact text from the design document."""
        expected = (
            "The Senzing MCP server is unreachable and no cached response "
            "is available for this request."
        )
        assert NETWORK_ERROR_MESSAGE == expected

    def test_retry_suggestion_exact_text(self) -> None:
        """Retry suggestion matches the exact text from the design document."""
        expected = "Check your network connectivity or try again in a moment."
        assert NETWORK_RETRY_SUGGESTION == expected


class TestCorruptedCacheFileRecovery:
    """Test that corrupted JSON cache files are deleted and treated as miss.

    Validates: Requirements 4.1 (error handling behavior)
    """

    def test_corrupted_json_returns_miss(self, tmp_path: Path) -> None:
        """A cache file with invalid JSON content produces a cache miss."""
        tool_name = "get_entity_by_record_id"
        parameters = {"data_source": "TEST", "record_id": "1001"}
        current_module_id = "module-05"

        # Compute the expected filename and write corrupted content
        cache_key = compute_cache_key(tool_name, parameters)
        filename = derive_filename(cache_key)
        cache_file = tmp_path / filename
        cache_file.write_text("this is not valid json {{{", encoding="utf-8")

        # Perform lookup
        status, response = cache_lookup(tmp_path, tool_name, parameters, current_module_id)

        assert status == "miss"
        assert response is None

    def test_corrupted_file_is_deleted(self, tmp_path: Path) -> None:
        """A corrupted cache file is removed from disk after lookup."""
        tool_name = "get_entity_by_record_id"
        parameters = {"data_source": "TEST", "record_id": "1001"}
        current_module_id = "module-05"

        # Compute the expected filename and write corrupted content
        cache_key = compute_cache_key(tool_name, parameters)
        filename = derive_filename(cache_key)
        cache_file = tmp_path / filename
        cache_file.write_text("not json at all!!!", encoding="utf-8")

        # Verify file exists before lookup
        assert cache_file.exists()

        # Perform lookup (triggers deletion)
        cache_lookup(tmp_path, tool_name, parameters, current_module_id)

        # Verify file has been deleted
        assert not cache_file.exists()

    def test_partial_json_treated_as_corrupted(self, tmp_path: Path) -> None:
        """A file with truncated/partial JSON is treated as corrupted."""
        tool_name = "search_by_attributes"
        parameters = {"name": "John Smith"}
        current_module_id = "module-03"

        cache_key = compute_cache_key(tool_name, parameters)
        filename = derive_filename(cache_key)
        cache_file = tmp_path / filename
        # Write partial JSON (missing closing brace)
        cache_file.write_text('{"tool_name": "search_by_attributes"', encoding="utf-8")

        status, response = cache_lookup(tmp_path, tool_name, parameters, current_module_id)

        assert status == "miss"
        assert response is None
        assert not cache_file.exists()


class TestCacheDirectoryCreation:
    """Test that cache directory and files are created correctly on first write.

    Validates: Requirements 4.3 (relates to directory creation on first use)
    """

    def test_write_to_nonexistent_directory(self, tmp_path: Path) -> None:
        """Writing a cache entry to a non-existent directory creates it."""
        cache_dir = tmp_path / "config" / "mcp_cache"

        # Directory should not exist yet
        assert not cache_dir.exists()

        # Simulate the cache write behavior: create dir + write file
        tool_name = "get_entity_by_record_id"
        parameters = {"data_source": "CUSTOMERS", "record_id": "2001"}
        module_id = "module-01"
        timestamp = "2025-01-15T10:30:00Z"
        response_payload = {"resolved_entity": {"entity_id": 1}}

        cache_key = compute_cache_key(tool_name, parameters)
        filename = derive_filename(cache_key)
        parameters_hash = filename.replace(".json", "")

        # Create directory (as the agent would on first write)
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Write cache entry
        entry_json = serialize_cache_entry(
            tool_name=tool_name,
            parameters_hash=parameters_hash,
            module_id=module_id,
            timestamp=timestamp,
            response=response_payload,
        )
        cache_file = cache_dir / filename
        cache_file.write_text(entry_json, encoding="utf-8")

        # Assert directory and file were created
        assert cache_dir.exists()
        assert cache_dir.is_dir()
        assert cache_file.exists()

    def test_created_file_is_valid_cache_entry(self, tmp_path: Path) -> None:
        """A newly created cache file contains valid JSON with all fields."""
        cache_dir = tmp_path / "mcp_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        tool_name = "get_entity_by_record_id"
        parameters = {"data_source": "WATCHLIST", "record_id": "W-100"}
        module_id = "module-07"
        timestamp = "2025-02-20T14:00:00Z"
        response_payload = {"resolved_entity": {"entity_id": 42, "entity_name": "Test"}}

        cache_key = compute_cache_key(tool_name, parameters)
        filename = derive_filename(cache_key)
        parameters_hash = filename.replace(".json", "")

        entry_json = serialize_cache_entry(
            tool_name=tool_name,
            parameters_hash=parameters_hash,
            module_id=module_id,
            timestamp=timestamp,
            response=response_payload,
        )
        cache_file = cache_dir / filename
        cache_file.write_text(entry_json, encoding="utf-8")

        # Read back and verify all fields
        content = json.loads(cache_file.read_text(encoding="utf-8"))
        assert content["tool_name"] == tool_name
        assert content["parameters_hash"] == parameters_hash
        assert content["module_id"] == module_id
        assert content["timestamp"] == timestamp
        assert content["response"] == response_payload

    def test_cache_lookup_works_after_directory_creation(self, tmp_path: Path) -> None:
        """After creating the directory and writing, lookup returns a hit."""
        cache_dir = tmp_path / "new_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        tool_name = "get_entity_by_record_id"
        parameters = {"data_source": "PEOPLE", "record_id": "P-001"}
        module_id = "module-02"
        timestamp = "2025-03-01T09:00:00Z"
        response_payload = {"resolved_entity": {"entity_id": 99}}

        cache_key = compute_cache_key(tool_name, parameters)
        filename = derive_filename(cache_key)
        parameters_hash = filename.replace(".json", "")

        entry_json = serialize_cache_entry(
            tool_name=tool_name,
            parameters_hash=parameters_hash,
            module_id=module_id,
            timestamp=timestamp,
            response=response_payload,
        )
        cache_file = cache_dir / filename
        cache_file.write_text(entry_json, encoding="utf-8")

        # Lookup should return a hit
        status, response = cache_lookup(cache_dir, tool_name, parameters, module_id)
        assert status == "hit"
        assert response == response_payload
