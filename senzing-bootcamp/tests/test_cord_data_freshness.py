"""Tests for cord_metadata.py - CORD Data Freshness Indicator.

Feature: cord-data-freshness
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from cord_metadata import CordMetadata, SourceMetadata, parse_metadata, serialize_metadata


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_sha256_hash() -> st.SearchStrategy[str]:
    """Generate valid SHA-256 hex strings (64 lowercase hex characters)."""
    return st.text(
        alphabet="0123456789abcdef",
        min_size=64,
        max_size=64,
    )


def st_iso8601_date() -> st.SearchStrategy[str]:
    """Generate valid ISO 8601 date strings with timezone."""
    return st.datetimes().map(lambda dt: dt.isoformat() + "+00:00")


def st_nonempty_text() -> st.SearchStrategy[str]:
    """Generate non-empty strings suitable for names and paths.

    Avoids characters that would break YAML parsing (newlines, colons,
    quotes that nest badly, etc.).
    """
    safe_chars = st.characters(
        whitelist_categories=("L", "N"),
        whitelist_characters="-_./",
    )
    return st.text(alphabet=safe_chars, min_size=1, max_size=50).filter(
        lambda s: s.strip() == s and len(s.strip()) > 0
    )


@st.composite
def st_source_metadata(draw: st.DrawFn) -> SourceMetadata:
    """Generate a random SourceMetadata object."""
    name = draw(st_nonempty_text())
    file_path = draw(st_nonempty_text())
    record_count = draw(st.integers(min_value=0, max_value=10_000_000))
    file_size_bytes = draw(st.integers(min_value=0, max_value=10_000_000_000))
    return SourceMetadata(
        name=name,
        file_path=file_path,
        record_count=record_count,
        file_size_bytes=file_size_bytes,
    )


@st.composite
def st_cord_metadata(draw: st.DrawFn) -> CordMetadata:
    """Generate a random CordMetadata object with 1+ sources."""
    dataset_name = draw(st_nonempty_text())
    sources = draw(st.lists(st_source_metadata(), min_size=1, max_size=5))
    download_date = draw(st_iso8601_date())
    content_hash = draw(st_sha256_hash())
    return CordMetadata(
        dataset_name=dataset_name,
        sources=sources,
        download_date=download_date,
        content_hash=content_hash,
        schema_version="1",
    )


# ---------------------------------------------------------------------------
# Property 1: Metadata serialization round-trip
# ---------------------------------------------------------------------------


class TestMetadataRoundTrip:
    """Property test: serialize -> parse round-trip preserves all fields.

    **Validates: Requirements 1, 2**

    For any valid CordMetadata object, serializing to YAML and parsing back
    must produce an equivalent object with all fields preserved.
    """

    @given(metadata=st_cord_metadata())
    @settings(max_examples=100)
    def test_round_trip_preserves_all_fields(self, metadata: CordMetadata) -> None:
        """parse_metadata(serialize_metadata(m)) == m for all generated inputs."""
        yaml_str = serialize_metadata(metadata)
        restored = parse_metadata(yaml_str)

        assert restored.dataset_name == metadata.dataset_name
        assert restored.download_date == metadata.download_date
        assert restored.content_hash == metadata.content_hash
        assert restored.schema_version == metadata.schema_version
        assert len(restored.sources) == len(metadata.sources)

        for original, parsed in zip(metadata.sources, restored.sources):
            assert parsed.name == original.name
            assert parsed.file_path == original.file_path
            assert parsed.record_count == original.record_count
            assert parsed.file_size_bytes == original.file_size_bytes


class TestSerializationEdgeCases:
    """Unit tests for serialization edge cases.

    Requirements: 2
    """

    def test_single_source_round_trip(self) -> None:
        """Single source metadata serializes and parses back correctly."""
        metadata = CordMetadata(
            dataset_name="cord-las-vegas",
            sources=[
                SourceMetadata(
                    name="CORD_LAS_VEGAS",
                    file_path="data/raw/cord-las-vegas.jsonl",
                    record_count=8421,
                    file_size_bytes=4523891,
                ),
            ],
            download_date="2025-07-15T14:30:00+00:00",
            content_hash="a3f2b8c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
        )
        yaml_str = serialize_metadata(metadata)
        parsed = parse_metadata(yaml_str)

        assert parsed.dataset_name == metadata.dataset_name
        assert parsed.download_date == metadata.download_date
        assert parsed.content_hash == metadata.content_hash
        assert parsed.schema_version == metadata.schema_version
        assert len(parsed.sources) == 1
        assert parsed.sources[0].name == "CORD_LAS_VEGAS"
        assert parsed.sources[0].file_path == "data/raw/cord-las-vegas.jsonl"
        assert parsed.sources[0].record_count == 8421
        assert parsed.sources[0].file_size_bytes == 4523891

    def test_multiple_sources_round_trip(self) -> None:
        """Multiple sources metadata serializes and parses back correctly."""
        metadata = CordMetadata(
            dataset_name="cord-multi-region",
            sources=[
                SourceMetadata(
                    name="CORD_LAS_VEGAS",
                    file_path="data/raw/cord-las-vegas.jsonl",
                    record_count=8421,
                    file_size_bytes=4523891,
                ),
                SourceMetadata(
                    name="CORD_NEW_YORK",
                    file_path="data/raw/cord-new-york.jsonl",
                    record_count=12500,
                    file_size_bytes=7891234,
                ),
                SourceMetadata(
                    name="CORD_CHICAGO",
                    file_path="data/raw/cord-chicago.jsonl",
                    record_count=5000,
                    file_size_bytes=2345678,
                ),
            ],
            download_date="2025-08-01T09:00:00+00:00",
            content_hash="b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5",
        )
        yaml_str = serialize_metadata(metadata)
        parsed = parse_metadata(yaml_str)

        assert parsed.dataset_name == metadata.dataset_name
        assert len(parsed.sources) == 3
        assert parsed.sources[0].name == "CORD_LAS_VEGAS"
        assert parsed.sources[1].name == "CORD_NEW_YORK"
        assert parsed.sources[2].name == "CORD_CHICAGO"
        assert parsed.sources[1].record_count == 12500
        assert parsed.sources[2].file_size_bytes == 2345678

    def test_special_characters_in_dataset_name(self) -> None:
        """Dataset names with colons, quotes, spaces, and unicode round-trip."""
        metadata = CordMetadata(
            dataset_name='cord: "las vegas" données',
            sources=[
                SourceMetadata(
                    name="SOURCE_ONE",
                    file_path="data/raw/source.jsonl",
                    record_count=100,
                    file_size_bytes=5000,
                ),
            ],
            download_date="2025-07-15T14:30:00+00:00",
            content_hash="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        )
        yaml_str = serialize_metadata(metadata)
        parsed = parse_metadata(yaml_str)

        assert parsed.dataset_name == metadata.dataset_name

    def test_empty_string_fields(self) -> None:
        """Empty string fields serialize and parse back correctly."""
        metadata = CordMetadata(
            dataset_name="",
            sources=[
                SourceMetadata(
                    name="",
                    file_path="",
                    record_count=0,
                    file_size_bytes=0,
                ),
            ],
            download_date="",
            content_hash="",
        )
        yaml_str = serialize_metadata(metadata)
        parsed = parse_metadata(yaml_str)

        assert parsed.dataset_name == metadata.dataset_name
        assert parsed.sources[0].name == ""
        assert parsed.sources[0].file_path == ""
        assert parsed.sources[0].record_count == 0
        assert parsed.sources[0].file_size_bytes == 0
        assert parsed.download_date == ""
        assert parsed.content_hash == ""

    def test_large_record_counts(self) -> None:
        """Large record counts serialize and parse back correctly."""
        metadata = CordMetadata(
            dataset_name="cord-massive",
            sources=[
                SourceMetadata(
                    name="BIG_SOURCE",
                    file_path="data/raw/big.jsonl",
                    record_count=999999999,
                    file_size_bytes=9876543210,
                ),
            ],
            download_date="2025-12-31T23:59:59+00:00",
            content_hash="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        )
        yaml_str = serialize_metadata(metadata)
        parsed = parse_metadata(yaml_str)

        assert parsed.sources[0].record_count == 999999999
        assert parsed.sources[0].file_size_bytes == 9876543210

    def test_long_file_paths(self) -> None:
        """Deeply nested file paths serialize and parse back correctly."""
        long_path = "data/raw/very/deeply/nested/directory/structure/that/goes/on/file.jsonl"
        metadata = CordMetadata(
            dataset_name="cord-nested",
            sources=[
                SourceMetadata(
                    name="NESTED_SOURCE",
                    file_path=long_path,
                    record_count=42,
                    file_size_bytes=1024,
                ),
            ],
            download_date="2025-06-01T12:00:00+00:00",
            content_hash="deadbeefcafebabe1234567890abcdef1234567890abcdef1234567890abcdef",
        )
        yaml_str = serialize_metadata(metadata)
        parsed = parse_metadata(yaml_str)

        assert parsed.sources[0].file_path == long_path


# ---------------------------------------------------------------------------
# Unit tests for capture_metadata (Task 2.2)
# ---------------------------------------------------------------------------

from cord_metadata import capture_metadata, compute_content_hash


class TestCaptureMetadata:
    """Unit tests for capture_metadata function.

    Requirements: 1, 2, 9
    """

    def test_capture_creates_metadata_file(self, tmp_path: Path) -> None:
        """Capture with valid JSONL files creates metadata YAML with correct content."""
        # Create temp JSONL files
        file1 = tmp_path / "cord-las-vegas.jsonl"
        file1.write_text('{"RECORD_ID": "1", "NAME": "Alice"}\n'
                         '{"RECORD_ID": "2", "NAME": "Bob"}\n'
                         '{"RECORD_ID": "3", "NAME": "Charlie"}\n')

        file2 = tmp_path / "cord-new-york.jsonl"
        file2.write_text('{"RECORD_ID": "1", "NAME": "Dave"}\n'
                         '{"RECORD_ID": "2", "NAME": "Eve"}\n')

        output_path = str(tmp_path / "config" / "cord_metadata.yaml")

        result = capture_metadata(
            dataset_name="cord-test",
            source_files=[str(file1), str(file2)],
            output_path=output_path,
        )

        # Verify return value
        assert result is not None
        assert result.dataset_name == "cord-test"
        assert len(result.sources) == 2

        # Verify first source
        assert result.sources[0].name == "CORD_LAS_VEGAS"
        assert result.sources[0].file_path == str(file1)
        assert result.sources[0].record_count == 3
        assert result.sources[0].file_size_bytes == file1.stat().st_size

        # Verify second source
        assert result.sources[1].name == "CORD_NEW_YORK"
        assert result.sources[1].file_path == str(file2)
        assert result.sources[1].record_count == 2
        assert result.sources[1].file_size_bytes == file2.stat().st_size

        # Verify content hash is a valid SHA-256 hex string
        assert len(result.content_hash) == 64
        assert all(c in "0123456789abcdef" for c in result.content_hash)

        # Verify download_date is an ISO 8601 string
        assert "T" in result.download_date

        # Verify the output file was written
        assert Path(output_path).exists()

        # Verify the file content can be parsed back
        yaml_content = Path(output_path).read_text(encoding="utf-8")
        parsed = parse_metadata(yaml_content)
        assert parsed.dataset_name == "cord-test"
        assert len(parsed.sources) == 2

    def test_capture_missing_source_file(self, tmp_path: Path, capsys) -> None:
        """Missing source file is skipped with a warning; other valid files still captured."""
        # Create one valid file
        valid_file = tmp_path / "valid.jsonl"
        valid_file.write_text('{"RECORD_ID": "1"}\n{"RECORD_ID": "2"}\n')

        # Non-existent file path
        missing_file = str(tmp_path / "nonexistent.jsonl")

        output_path = str(tmp_path / "metadata.yaml")

        result = capture_metadata(
            dataset_name="cord-partial",
            source_files=[missing_file, str(valid_file)],
            output_path=output_path,
        )

        # Valid file should still be captured
        assert result is not None
        assert len(result.sources) == 1
        assert result.sources[0].file_path == str(valid_file)
        assert result.sources[0].record_count == 2

        # Warning should be printed to stderr
        captured = capsys.readouterr()
        assert "Warning" in captured.err
        assert "nonexistent.jsonl" in captured.err

    def test_capture_no_valid_files(self, tmp_path: Path) -> None:
        """Capture with only non-existent files returns None."""
        missing1 = str(tmp_path / "missing1.jsonl")
        missing2 = str(tmp_path / "missing2.jsonl")

        output_path = str(tmp_path / "metadata.yaml")

        result = capture_metadata(
            dataset_name="cord-empty",
            source_files=[missing1, missing2],
            output_path=output_path,
        )

        assert result is None
        # Output file should not be created
        assert not Path(output_path).exists()

    def test_content_hash_fewer_than_100_records(self, tmp_path: Path) -> None:
        """Content hash for file with < 100 lines uses all lines."""
        import hashlib

        # Create a file with 10 lines
        lines = [f'{{"RECORD_ID": "{i}"}}\n' for i in range(10)]
        data_file = tmp_path / "small.jsonl"
        data_file.write_text("".join(lines))

        result = compute_content_hash(str(data_file), max_records=100)

        # Compute expected hash from all 10 lines
        expected_hasher = hashlib.sha256()
        for line in lines:
            expected_hasher.update(line.encode("utf-8"))
        expected = expected_hasher.hexdigest()

        assert result == expected
        assert len(result) == 64

    def test_content_hash_more_than_100_records(self, tmp_path: Path) -> None:
        """Content hash for file with > 100 lines uses only first 100 lines."""
        import hashlib

        # Create a file with 150 lines
        lines = [f'{{"RECORD_ID": "{i}"}}\n' for i in range(150)]
        data_file = tmp_path / "large.jsonl"
        data_file.write_text("".join(lines))

        result = compute_content_hash(str(data_file), max_records=100)

        # Compute expected hash from only first 100 lines
        expected_hasher = hashlib.sha256()
        for line in lines[:100]:
            expected_hasher.update(line.encode("utf-8"))
        expected = expected_hasher.hexdigest()

        assert result == expected

        # Verify it's different from hashing all 150 lines
        full_hasher = hashlib.sha256()
        for line in lines:
            full_hasher.update(line.encode("utf-8"))
        full_hash = full_hasher.hexdigest()

        assert result != full_hash


# ---------------------------------------------------------------------------
# Property 2: Freshness check correctly detects mismatches
# ---------------------------------------------------------------------------

import tempfile

from cord_metadata import check_freshness


class TestFreshnessDetection:
    """Property test: check_freshness correctly detects mismatches.

    **Validates: Requirements 3, 4**

    For any stored metadata and current file state where at least one source
    file has a different size or record count than recorded, check_freshness
    SHALL return status "stale" with a non-empty mismatches list. Conversely,
    when all files match their stored metadata exactly, it SHALL return status
    "fresh" with an empty mismatches list.
    """

    @given(
        lines_per_source=st.lists(
            st.lists(
                st.text(
                    alphabet=st.characters(
                        whitelist_categories=("L", "N"),
                        whitelist_characters=' -_,.:',
                    ),
                    min_size=1,
                    max_size=80,
                ),
                min_size=1,
                max_size=20,
            ),
            min_size=1,
            max_size=4,
        ),
        mismatch_index=st.integers(min_value=0, max_value=3),
    )
    @settings(max_examples=100)
    def test_detects_mismatches_when_files_differ(
        self,
        lines_per_source: list[list[str]],
        mismatch_index: int,
    ) -> None:
        """When at least one file has different size or record count, status is stale."""
        if not lines_per_source:
            lines_per_source = [["record1"]]

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create source files and capture their metadata
            source_files: list[str] = []
            for i, lines in enumerate(lines_per_source):
                file_path = tmp_path / f"source_{i}.jsonl"
                content = "\n".join(lines) + "\n"
                file_path.write_text(content, encoding="utf-8")
                source_files.append(str(file_path))

            # Capture metadata from the current state
            metadata = capture_metadata(
                dataset_name="test-dataset",
                source_files=source_files,
                output_path=str(tmp_path / "metadata.yaml"),
            )
            assert metadata is not None

            # Now modify at least one file to create a mismatch
            target_idx = mismatch_index % len(lines_per_source)
            target_file = Path(source_files[target_idx])
            # Add an extra line to change both size and record count
            with open(target_file, "a", encoding="utf-8") as f:
                f.write("extra_record_to_cause_mismatch\n")

            # Run freshness check
            result = check_freshness(str(tmp_path / "metadata.yaml"))

            assert result.status == "stale"
            assert len(result.mismatches) > 0

    @given(
        lines_per_source=st.lists(
            st.lists(
                st.text(
                    alphabet=st.characters(
                        whitelist_categories=("L", "N"),
                        whitelist_characters=' -_,.:',
                    ),
                    min_size=1,
                    max_size=80,
                ),
                min_size=1,
                max_size=20,
            ),
            min_size=1,
            max_size=4,
        ),
    )
    @settings(max_examples=100)
    def test_reports_fresh_when_all_match(
        self,
        lines_per_source: list[list[str]],
    ) -> None:
        """When all files match their stored metadata exactly, status is fresh."""
        if not lines_per_source:
            lines_per_source = [["record1"]]

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create source files
            source_files: list[str] = []
            for i, lines in enumerate(lines_per_source):
                file_path = tmp_path / f"source_{i}.jsonl"
                content = "\n".join(lines) + "\n"
                file_path.write_text(content, encoding="utf-8")
                source_files.append(str(file_path))

            # Capture metadata from the current state
            metadata = capture_metadata(
                dataset_name="test-dataset",
                source_files=source_files,
                output_path=str(tmp_path / "metadata.yaml"),
            )
            assert metadata is not None

            # Do NOT modify any files - they should all match

            # Run freshness check
            result = check_freshness(str(tmp_path / "metadata.yaml"))

            assert result.status == "fresh"
            assert result.mismatches == []


# ---------------------------------------------------------------------------
# Property 3: Non-blocking advisory behavior
# ---------------------------------------------------------------------------

import tempfile

from cord_metadata import check_freshness, FreshnessResult


class TestNonBlockingBehavior:
    """Property test: check_freshness never raises an exception.

    **Validates: Requirements 5, 8**

    For any input state — missing files, corrupt YAML, empty metadata,
    non-CORD data — check_freshness completes without raising and returns
    a FreshnessResult with status in {"fresh", "stale", "skipped"}.
    """

    VALID_STATUSES = {"fresh", "stale", "skipped"}

    @given(content=st.binary(min_size=0, max_size=500))
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_never_raises_with_adversarial_yaml(
        self, content: bytes, tmp_path: Path
    ) -> None:
        """Random/corrupt YAML content never causes an exception."""
        metadata_file = tmp_path / "cord_metadata.yaml"
        metadata_file.write_bytes(content)

        result = check_freshness(str(metadata_file))

        assert isinstance(result, FreshnessResult)
        assert result.status in self.VALID_STATUSES

    @given(path_suffix=st.text(
        alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_/"),
        min_size=1,
        max_size=100,
    ))
    @settings(max_examples=100)
    def test_never_raises_with_missing_metadata(self, path_suffix: str) -> None:
        """Random non-existent file paths never cause an exception."""
        fake_path = f"/tmp/nonexistent_cord_test/{path_suffix}/cord_metadata.yaml"

        result = check_freshness(fake_path)

        assert isinstance(result, FreshnessResult)
        assert result.status in self.VALID_STATUSES

    @given(whitespace=st.text(
        alphabet=st.sampled_from([" ", "\t", "\n", "\r"]),
        min_size=0,
        max_size=50,
    ))
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_never_raises_with_empty_content(
        self, whitespace: str, tmp_path: Path
    ) -> None:
        """Empty files or files with just whitespace never cause an exception."""
        metadata_file = tmp_path / "cord_metadata.yaml"
        metadata_file.write_text(whitespace)

        result = check_freshness(str(metadata_file))

        assert isinstance(result, FreshnessResult)
        assert result.status in self.VALID_STATUSES


# ---------------------------------------------------------------------------
# Unit tests for check_freshness scenarios (Task 3.4)
# ---------------------------------------------------------------------------


class TestCheckFreshnessScenarios:
    """Unit tests for check_freshness specific scenarios.

    Requirements: 3, 4, 5, 8, 9
    """

    def test_freshness_check_pass(self, tmp_path: Path) -> None:
        """Metadata matches files exactly → status "fresh".

        Validates: Requirement 9
        """
        # Create a JSONL data file
        data_file = tmp_path / "cord-las-vegas.jsonl"
        data_file.write_text(
            '{"RECORD_ID": "1", "NAME": "Alice"}\n'
            '{"RECORD_ID": "2", "NAME": "Bob"}\n'
            '{"RECORD_ID": "3", "NAME": "Charlie"}\n'
        )

        # Capture metadata (creates YAML matching current file state)
        metadata_path = str(tmp_path / "cord_metadata.yaml")
        result = capture_metadata(
            dataset_name="cord-las-vegas",
            source_files=[str(data_file)],
            output_path=metadata_path,
        )
        assert result is not None

        # Check freshness — files haven't changed, should be fresh
        freshness = check_freshness(metadata_path)

        assert freshness.status == "fresh"
        assert freshness.mismatches == []
        assert "fresh" in freshness.message.lower() or "match" in freshness.message.lower()

    def test_freshness_check_fail_size_mismatch(self, tmp_path: Path) -> None:
        """File size changed after metadata capture → status "stale" with mismatch details.

        Validates: Requirement 9
        """
        # Create a JSONL data file
        data_file = tmp_path / "cord-las-vegas.jsonl"
        data_file.write_text(
            '{"RECORD_ID": "1", "NAME": "Alice"}\n'
            '{"RECORD_ID": "2", "NAME": "Bob"}\n'
        )

        # Capture metadata
        metadata_path = str(tmp_path / "cord_metadata.yaml")
        result = capture_metadata(
            dataset_name="cord-las-vegas",
            source_files=[str(data_file)],
            output_path=metadata_path,
        )
        assert result is not None

        # Modify the file to change its size (append extra content to existing line)
        # We keep the same number of lines but change the content to alter size
        data_file.write_text(
            '{"RECORD_ID": "1", "NAME": "Alice", "EXTRA": "padding data here"}\n'
            '{"RECORD_ID": "2", "NAME": "Bob", "EXTRA": "more padding data here too"}\n'
        )

        # Check freshness — file size changed, should be stale
        freshness = check_freshness(metadata_path)

        assert freshness.status == "stale"
        assert len(freshness.mismatches) > 0
        # At least one mismatch should reference file_size_bytes
        size_mismatches = [m for m in freshness.mismatches if m["field"] == "file_size_bytes"]
        assert len(size_mismatches) > 0

    def test_freshness_check_fail_record_count_mismatch(self, tmp_path: Path) -> None:
        """Record count changed after metadata capture → status "stale".

        Validates: Requirement 9
        """
        # Create a JSONL data file with 3 records
        data_file = tmp_path / "cord-data.jsonl"
        data_file.write_text(
            '{"RECORD_ID": "1"}\n'
            '{"RECORD_ID": "2"}\n'
            '{"RECORD_ID": "3"}\n'
        )

        # Capture metadata
        metadata_path = str(tmp_path / "cord_metadata.yaml")
        result = capture_metadata(
            dataset_name="cord-test",
            source_files=[str(data_file)],
            output_path=metadata_path,
        )
        assert result is not None

        # Add extra records (changes both size and record count)
        data_file.write_text(
            '{"RECORD_ID": "1"}\n'
            '{"RECORD_ID": "2"}\n'
            '{"RECORD_ID": "3"}\n'
            '{"RECORD_ID": "4"}\n'
            '{"RECORD_ID": "5"}\n'
        )

        # Check freshness — record count changed, should be stale
        freshness = check_freshness(metadata_path)

        assert freshness.status == "stale"
        assert len(freshness.mismatches) > 0
        # Should have a record_count mismatch
        count_mismatches = [m for m in freshness.mismatches if m["field"] == "record_count"]
        assert len(count_mismatches) > 0

    def test_missing_metadata_file(self, tmp_path: Path) -> None:
        """Non-existent metadata path → status "skipped".

        Validates: Requirement 9
        """
        non_existent_path = str(tmp_path / "does_not_exist" / "cord_metadata.yaml")

        freshness = check_freshness(non_existent_path)

        assert freshness.status == "skipped"
        assert freshness.message  # Should have an explanatory message

    def test_corrupt_metadata_file(self, tmp_path: Path) -> None:
        """Garbage content in metadata file → status "skipped".

        Validates: Requirement 5
        """
        metadata_file = tmp_path / "cord_metadata.yaml"
        metadata_file.write_text(
            "!!!not valid yaml at all {{{\n"
            "random garbage content 12345\n"
            "@@@ more nonsense $$$\n"
        )

        freshness = check_freshness(str(metadata_file))

        assert freshness.status == "skipped"
        assert freshness.message  # Should explain the issue

    def test_non_cord_data_skipped(self, tmp_path: Path) -> None:
        """No metadata file exists (simulating non-CORD data) → status "skipped".

        Validates: Requirement 8
        """
        # Point to a directory that exists but has no metadata file
        metadata_path = str(tmp_path / "cord_metadata.yaml")
        # Don't create the file — simulates non-CORD data scenario

        freshness = check_freshness(metadata_path)

        assert freshness.status == "skipped"
        assert freshness.message  # Should indicate no metadata found

    def test_missing_data_file_is_stale(self, tmp_path: Path) -> None:
        """Metadata references a file that doesn't exist on disk → status "stale".

        Validates: Requirements 3, 4
        """
        # Create metadata YAML that references a non-existent data file
        metadata = CordMetadata(
            dataset_name="cord-missing",
            sources=[
                SourceMetadata(
                    name="CORD_MISSING",
                    file_path=str(tmp_path / "nonexistent_data.jsonl"),
                    record_count=100,
                    file_size_bytes=5000,
                ),
            ],
            download_date="2025-07-15T14:30:00+00:00",
            content_hash="a" * 64,
        )

        metadata_path = tmp_path / "cord_metadata.yaml"
        metadata_path.write_text(serialize_metadata(metadata), encoding="utf-8")

        # Check freshness — data file is missing, should be stale
        freshness = check_freshness(str(metadata_path))

        assert freshness.status == "stale"
        assert len(freshness.mismatches) > 0
        # The mismatch should indicate the file is missing
        assert any(
            m.get("actual") == "FILE_MISSING" for m in freshness.mismatches
        )


# ---------------------------------------------------------------------------
# Unit tests for CLI subcommands (Task 5.2)
# ---------------------------------------------------------------------------

from cord_metadata import main


class TestCLISubcommands:
    """Unit tests for CLI capture/check subcommands end-to-end.

    Requirements: 4, 5, 9
    """

    def test_capture_subcommand_end_to_end(self, tmp_path: Path, capsys) -> None:
        """Capture subcommand creates metadata file and exits 0.

        Validates: Requirements 5, 9
        """
        # Create a temp JSONL file
        data_file = tmp_path / "cord-test.jsonl"
        data_file.write_text(
            '{"RECORD_ID": "1", "NAME": "Alice"}\n'
            '{"RECORD_ID": "2", "NAME": "Bob"}\n'
            '{"RECORD_ID": "3", "NAME": "Charlie"}\n'
        )

        output_file = tmp_path / "output" / "cord_metadata.yaml"

        exit_code = main([
            "capture",
            "--dataset", "test-dataset",
            "--files", str(data_file),
            "--output", str(output_file),
        ])

        assert exit_code == 0
        assert output_file.exists()

        # Verify output contains expected content
        captured = capsys.readouterr()
        assert "test-dataset" in captured.out
        assert "1 source(s)" in captured.out

    def test_check_subcommand_fresh(self, tmp_path: Path, capsys) -> None:
        """Check subcommand reports fresh when files match metadata.

        Validates: Requirements 5, 9
        """
        # Create a data file
        data_file = tmp_path / "cord-data.jsonl"
        data_file.write_text(
            '{"RECORD_ID": "1", "NAME": "Alice"}\n'
            '{"RECORD_ID": "2", "NAME": "Bob"}\n'
        )

        # Capture metadata first
        metadata_path = tmp_path / "cord_metadata.yaml"
        capture_exit = main([
            "capture",
            "--dataset", "cord-fresh-test",
            "--files", str(data_file),
            "--output", str(metadata_path),
        ])
        assert capture_exit == 0

        # Clear captured output from capture step
        capsys.readouterr()

        # Now check freshness — files haven't changed
        check_exit = main(["check", "--metadata", str(metadata_path)])

        assert check_exit == 0
        captured = capsys.readouterr()
        assert "fresh" in captured.out.lower() or "match" in captured.out.lower()

    def test_check_subcommand_stale(self, tmp_path: Path, capsys) -> None:
        """Check subcommand reports stale warning when files mismatch.

        Validates: Requirements 4, 5, 9
        """
        # Create a data file
        data_file = tmp_path / "cord-data.jsonl"
        data_file.write_text(
            '{"RECORD_ID": "1", "NAME": "Alice"}\n'
            '{"RECORD_ID": "2", "NAME": "Bob"}\n'
        )

        # Capture metadata
        metadata_path = tmp_path / "cord_metadata.yaml"
        capture_exit = main([
            "capture",
            "--dataset", "cord-stale-test",
            "--files", str(data_file),
            "--output", str(metadata_path),
        ])
        assert capture_exit == 0

        # Modify the data file to create a mismatch
        data_file.write_text(
            '{"RECORD_ID": "1", "NAME": "Alice"}\n'
            '{"RECORD_ID": "2", "NAME": "Bob"}\n'
            '{"RECORD_ID": "3", "NAME": "Charlie"}\n'
            '{"RECORD_ID": "4", "NAME": "Dave"}\n'
        )

        # Clear captured output from capture step
        capsys.readouterr()

        # Check freshness — file has changed
        check_exit = main(["check", "--metadata", str(metadata_path)])

        # Exit code must be 0 (advisory only per Requirement 5)
        assert check_exit == 0

        captured = capsys.readouterr()
        # Warning message must contain Requirement 4 text
        assert "Your CORD data files may have changed since download" in captured.out
        assert "re-download fresh data" in captured.out
        assert "proceed with current files" in captured.out
        assert "check what changed" in captured.out

    def test_check_subcommand_skipped(self, tmp_path: Path, capsys) -> None:
        """Check subcommand exits 0 when metadata file does not exist.

        Validates: Requirements 5, 8
        """
        non_existent = tmp_path / "does_not_exist" / "cord_metadata.yaml"

        check_exit = main(["check", "--metadata", str(non_existent)])

        # Exit code must be 0 (advisory only, never block)
        assert check_exit == 0

        captured = capsys.readouterr()
        # Should print a skip message (not crash)
        assert captured.out.strip()  # Some output was produced

    def test_warning_message_format(self, tmp_path: Path, capsys) -> None:
        """Stale warning includes all required phrases from Requirement 4.

        Validates: Requirement 4
        """
        # Create a data file
        data_file = tmp_path / "cord-data.jsonl"
        data_file.write_text('{"RECORD_ID": "1"}\n')

        # Capture metadata
        metadata_path = tmp_path / "cord_metadata.yaml"
        main([
            "capture",
            "--dataset", "cord-format-test",
            "--files", str(data_file),
            "--output", str(metadata_path),
        ])

        # Modify file to trigger stale
        data_file.write_text(
            '{"RECORD_ID": "1"}\n'
            '{"RECORD_ID": "2"}\n'
        )

        # Clear captured output
        capsys.readouterr()

        # Check freshness
        exit_code = main(["check", "--metadata", str(metadata_path)])
        assert exit_code == 0

        captured = capsys.readouterr()
        output = captured.out

        # Verify all required phrases from Requirement 4 are present
        assert "Your CORD data files may have changed since download" in output
        assert "re-download fresh data" in output
        assert "proceed with current files" in output
        assert "check what changed" in output
