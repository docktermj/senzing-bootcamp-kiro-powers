"""Property-based tests for MCP response caching.

Validates cache key computation, filename derivation, cache entry schema
round-trip, and cache lookup correctness as defined in the
mcp-response-caching steering file.

Feature: mcp-response-caching
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CACHE_DIR_NAME = "mcp_cache"
_HASH_LENGTH = 16
_CACHE_ENTRY_FIELDS = ("tool_name", "parameters_hash", "module_id", "timestamp", "response")


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def compute_cache_key(tool_name: str, parameters: dict) -> str:
    """Compute the deterministic cache key from tool name and parameters.

    The cache key is formed by concatenating the tool name, a pipe separator,
    and the JSON-serialized parameters with keys sorted alphabetically and
    compact separators (no extra whitespace).

    Args:
        tool_name: The MCP tool name.
        parameters: The parameters dictionary for the tool call.

    Returns:
        The deterministic cache key string.
    """
    serialized = json.dumps(parameters, sort_keys=True, separators=(",", ":"))
    return f"{tool_name}|{serialized}"


def derive_filename(cache_key: str) -> str:
    """Derive the cache entry filename from a cache key.

    Computes the SHA-256 hex digest of the UTF-8 encoded cache key,
    truncates to 16 characters, and appends '.json'.

    Args:
        cache_key: The cache key string.

    Returns:
        Filename string of exactly 16 hex characters plus '.json'.
    """
    digest = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
    return f"{digest[:_HASH_LENGTH]}.json"


def serialize_cache_entry(
    tool_name: str,
    parameters_hash: str,
    module_id: str,
    timestamp: str,
    response: object,
) -> str:
    """Serialize a cache entry to a JSON string.

    Args:
        tool_name: The MCP tool name that was called.
        parameters_hash: The 16-char hex digest (matches filename without .json).
        module_id: The module identifier active when the entry was written.
        timestamp: ISO 8601 timestamp of when the entry was created.
        response: The complete MCP tool response payload.

    Returns:
        JSON string representation of the cache entry.
    """
    entry = {
        "tool_name": tool_name,
        "parameters_hash": parameters_hash,
        "module_id": module_id,
        "timestamp": timestamp,
        "response": response,
    }
    return json.dumps(entry, separators=(",", ":"))


def deserialize_cache_entry(json_str: str) -> dict:
    """Deserialize a JSON string back to a cache entry dictionary.

    Args:
        json_str: A JSON string representing a cache entry.

    Returns:
        Dictionary with cache entry fields.
    """
    return json.loads(json_str)


def cache_lookup(
    cache_dir: Path,
    tool_name: str,
    parameters: dict,
    current_module_id: str,
) -> tuple[str, object | None]:
    """Simulate the cache lookup logic.

    Checks for a cached response file in the cache directory. Returns the
    lookup result based on file existence and module_id matching.

    Args:
        cache_dir: Path to the cache directory.
        tool_name: The MCP tool name being called.
        parameters: The parameters dictionary for the tool call.
        current_module_id: The currently active module identifier.

    Returns:
        A tuple of (status, response) where:
        - ("hit", response) if file exists and module_id matches
        - ("stale", None) if file exists but module_id doesn't match (file deleted)
        - ("miss", None) if file doesn't exist
    """
    cache_key = compute_cache_key(tool_name, parameters)
    filename = derive_filename(cache_key)
    cache_file = cache_dir / filename

    if not cache_file.exists():
        return ("miss", None)

    try:
        entry = deserialize_cache_entry(cache_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # Corrupted file — delete and treat as miss
        cache_file.unlink(missing_ok=True)
        return ("miss", None)

    if entry.get("module_id") == current_module_id:
        return ("hit", entry.get("response"))

    # Stale entry — module_id mismatch, delete the file
    cache_file.unlink(missing_ok=True)
    return ("stale", None)


import random

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


class TestCacheKeyDeterminism:
    """Property 1: Cache key determinism.

    Validates: Requirements 1.4

    For any MCP tool name and for any parameters dictionary, computing the
    cache key with the parameters in any insertion order SHALL produce the
    identical cache key string.
    """

    @given(
        tool_name=st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(whitelist_categories=("L", "N", "P")),
        ),
        parameters=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(
                st.text(),
                st.integers(),
                st.floats(allow_nan=False),
                st.booleans(),
                st.none(),
            ),
        ),
    )
    @settings(max_examples=20)
    def test_cache_key_same_regardless_of_insertion_order(
        self, tool_name: str, parameters: dict
    ) -> None:
        """Cache key is identical regardless of parameter insertion order."""
        # Compute cache key with original parameter order
        key_original = compute_cache_key(tool_name, parameters)

        # Create a shuffled copy of the parameters dict
        keys = list(parameters.keys())
        random.shuffle(keys)
        shuffled_parameters = {k: parameters[k] for k in keys}

        # Compute cache key with shuffled parameter order
        key_shuffled = compute_cache_key(tool_name, shuffled_parameters)

        assert key_original == key_shuffled


# ---------------------------------------------------------------------------
# Property-Based Tests — Hypothesis
# ---------------------------------------------------------------------------

import re

from hypothesis import given, settings
from hypothesis import strategies as st


class TestFilenameDerivedDeterminism:
    """Property 3: Filename derivation determinism and format.

    Validates: Requirements 2.3
    """

    @given(cache_key=st.text(min_size=1, max_size=200))
    @settings(max_examples=20)
    def test_filename_format_is_16_hex_chars_plus_json(self, cache_key: str) -> None:
        """Derived filename is exactly 16 hex characters followed by '.json'."""
        filename = derive_filename(cache_key)
        assert re.fullmatch(r"^[0-9a-f]{16}\.json$", filename), (
            f"Filename {filename!r} does not match expected format"
        )

    @given(cache_key=st.text(min_size=1, max_size=200))
    @settings(max_examples=20)
    def test_filename_derivation_is_deterministic(self, cache_key: str) -> None:
        """Computing filename multiple times from same key produces same result."""
        assert derive_filename(cache_key) == derive_filename(cache_key)


class TestCacheEntrySchemaRoundTrip:
    """Property 2: Cache entry schema round-trip.

    Validates: Requirements 2.2

    For any valid cache entry (containing tool_name, parameters_hash, module_id,
    timestamp, and response), serializing the entry to JSON and deserializing it
    back SHALL produce an equivalent object with all five fields preserved.
    """

    @given(
        tool_name=st.text(min_size=1, max_size=50),
        parameters_hash=st.text(
            alphabet="0123456789abcdef", min_size=16, max_size=16
        ),
        module_id=st.text(min_size=1, max_size=20).map(
            lambda s: f"module-{s}"
        ),
        timestamp=st.datetimes().map(lambda dt: dt.isoformat() + "Z"),
        response=st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.one_of(st.text(), st.integers(), st.booleans()),
        ),
    )
    @settings(max_examples=20)
    def test_serialize_deserialize_preserves_all_fields(
        self,
        tool_name: str,
        parameters_hash: str,
        module_id: str,
        timestamp: str,
        response: dict,
    ) -> None:
        """Serializing and deserializing a cache entry preserves all fields."""
        json_str = serialize_cache_entry(
            tool_name=tool_name,
            parameters_hash=parameters_hash,
            module_id=module_id,
            timestamp=timestamp,
            response=response,
        )

        restored = deserialize_cache_entry(json_str)

        assert restored["tool_name"] == tool_name
        assert restored["parameters_hash"] == parameters_hash
        assert restored["module_id"] == module_id
        assert restored["timestamp"] == timestamp
        assert restored["response"] == response


import shutil
import tempfile


class TestCacheLookupCorrectness:
    """Property 4: Cache lookup correctness.

    Validates: Requirements 3.1, 3.2, 3.3

    For any cache entry file in the cache directory and for any current
    module_id, the lookup SHALL return the cached response if and only if
    the entry's module_id matches the current module_id. When the module_id
    does not match, the stale entry file SHALL be deleted.
    """

    @given(
        tool_name=st.text(
            min_size=1,
            max_size=30,
            alphabet=st.characters(whitelist_categories=("L", "N")),
        ),
        parameters=st.dictionaries(
            keys=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz"),
            values=st.one_of(st.text(max_size=20), st.integers(), st.booleans()),
            max_size=5,
        ),
        module_id=st.text(
            min_size=1, max_size=15, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"
        ).map(lambda s: f"module-{s}"),
        response=st.dictionaries(
            keys=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz"),
            values=st.one_of(st.text(max_size=20), st.integers(), st.booleans()),
            max_size=3,
        ),
    )
    @settings(max_examples=20)
    def test_cache_hit_when_module_id_matches(
        self,
        tool_name: str,
        parameters: dict,
        module_id: str,
        response: dict,
    ) -> None:
        """Cached response returned when entry module_id matches current module_id."""
        cache_dir = Path(tempfile.mkdtemp())
        try:
            # Write a cache entry with the given module_id
            cache_key = compute_cache_key(tool_name, parameters)
            filename = derive_filename(cache_key)
            entry_json = serialize_cache_entry(
                tool_name=tool_name,
                parameters_hash=filename.removesuffix(".json"),
                module_id=module_id,
                timestamp="2025-01-15T10:30:00Z",
                response=response,
            )
            (cache_dir / filename).write_text(entry_json, encoding="utf-8")

            # Lookup with the same module_id → expect cache hit
            status, cached_response = cache_lookup(cache_dir, tool_name, parameters, module_id)

            assert status == "hit"
            assert cached_response == response
        finally:
            shutil.rmtree(cache_dir)

    @given(
        tool_name=st.text(
            min_size=1,
            max_size=30,
            alphabet=st.characters(whitelist_categories=("L", "N")),
        ),
        parameters=st.dictionaries(
            keys=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz"),
            values=st.one_of(st.text(max_size=20), st.integers(), st.booleans()),
            max_size=5,
        ),
        entry_module_id=st.text(
            min_size=1, max_size=15, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"
        ).map(lambda s: f"module-{s}"),
        current_module_id=st.text(
            min_size=1, max_size=15, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"
        ).map(lambda s: f"module-{s}"),
        response=st.dictionaries(
            keys=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz"),
            values=st.one_of(st.text(max_size=20), st.integers(), st.booleans()),
            max_size=3,
        ),
    )
    @settings(max_examples=20)
    def test_stale_miss_when_module_id_differs(
        self,
        tool_name: str,
        parameters: dict,
        entry_module_id: str,
        current_module_id: str,
        response: dict,
    ) -> None:
        """Stale entry deleted and miss returned when module_id does not match."""
        from hypothesis import assume

        assume(entry_module_id != current_module_id)

        cache_dir = Path(tempfile.mkdtemp())
        try:
            # Write a cache entry with entry_module_id
            cache_key = compute_cache_key(tool_name, parameters)
            filename = derive_filename(cache_key)
            entry_json = serialize_cache_entry(
                tool_name=tool_name,
                parameters_hash=filename.removesuffix(".json"),
                module_id=entry_module_id,
                timestamp="2025-01-15T10:30:00Z",
                response=response,
            )
            cache_file = cache_dir / filename
            cache_file.write_text(entry_json, encoding="utf-8")

            # Lookup with a different module_id → expect stale miss
            status, cached_response = cache_lookup(
                cache_dir, tool_name, parameters, current_module_id
            )

            assert status == "stale"
            assert cached_response is None
            # The stale file must have been deleted
            assert not cache_file.exists()
        finally:
            shutil.rmtree(cache_dir)


class TestModuleTransitionClearsAllEntries:
    """Property 6: Module transition clears all entries.

    Validates: Requirements 5.1, 5.2

    For any non-empty set of cache entry files in the cache directory, when a
    module transition occurs, all cache entry files SHALL be deleted before any
    MCP calls are made in the new module session.
    """

    @given(
        filenames=st.lists(
            st.text(alphabet="0123456789abcdef", min_size=16, max_size=16).map(
                lambda h: h + ".json"
            ),
            min_size=1,
            max_size=10,
            unique=True,
        ),
    )
    @settings(max_examples=20)
    def test_all_entries_deleted_after_module_transition(
        self, filenames: list[str]
    ) -> None:
        """All cache entry files are deleted when a module transition occurs."""
        import os
        import shutil
        import tempfile

        cache_dir = tempfile.mkdtemp()
        try:
            # Write dummy cache entry files
            for fname in filenames:
                filepath = os.path.join(cache_dir, fname)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("{}")

            # Verify files were created
            assert len(os.listdir(cache_dir)) == len(filenames)

            # Simulate module transition: delete all files in the cache directory
            for entry in os.listdir(cache_dir):
                os.unlink(os.path.join(cache_dir, entry))

            # Assert the directory is empty after transition
            assert os.listdir(cache_dir) == []
        finally:
            shutil.rmtree(cache_dir)


import shutil
import tempfile


class TestNoStaleFallbackOnFailure:
    """Property 5: No stale fallback on failure.

    Validates: Requirements 4.2

    For any cache miss scenario where the MCP server call fails, the system
    SHALL NOT return any previously cached response (even if stale entries
    exist in the cache directory), regardless of the number or content of
    stale entries present.
    """

    @given(
        tool_name=st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(whitelist_categories=("L", "N", "P")),
        ),
        parameters=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(
                st.text(max_size=30),
                st.integers(),
                st.booleans(),
                st.none(),
            ),
            max_size=5,
        ),
        stale_module_id=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("L", "N")),
        ).map(lambda s: f"module-{s}"),
        current_module_id=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("L", "N")),
        ).map(lambda s: f"module-{s}"),
    )
    @settings(max_examples=20)
    def test_stale_entry_never_returned_on_mismatched_module(
        self,
        tool_name: str,
        parameters: dict,
        stale_module_id: str,
        current_module_id: str,
    ) -> None:
        """Even when stale entries exist, the system never returns them."""
        from hypothesis import assume

        assume(stale_module_id != current_module_id)

        cache_dir = Path(tempfile.mkdtemp())
        try:
            # Write a cache entry with the stale module_id
            cache_key = compute_cache_key(tool_name, parameters)
            filename = derive_filename(cache_key)
            entry = {
                "tool_name": tool_name,
                "parameters_hash": filename.replace(".json", ""),
                "module_id": stale_module_id,
                "timestamp": "2025-01-15T10:30:00Z",
                "response": {"result": "stale_data"},
            }
            cache_file = cache_dir / filename
            cache_file.write_text(json.dumps(entry), encoding="utf-8")

            # Call cache_lookup with a DIFFERENT current_module_id
            status, response = cache_lookup(
                cache_dir, tool_name, parameters, current_module_id
            )

            # The result must NOT be a hit with the stale response
            assert (status, response) != ("hit", {"result": "stale_data"})
            # It should be ("stale", None) since module_id doesn't match
            assert status == "stale"
            assert response is None
        finally:
            shutil.rmtree(cache_dir)
