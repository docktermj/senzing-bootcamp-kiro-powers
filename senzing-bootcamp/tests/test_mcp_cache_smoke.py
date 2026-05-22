"""Smoke tests for MCP response caching static configuration.

Validates that the steering file, steering index registration, and
.gitignore exclusion are correctly configured for the MCP response
caching feature.

Validates: Requirements 1.1, 1.2, 6.1, 6.2, 6.3, 7.1, 7.2
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Module-level path constants
# ---------------------------------------------------------------------------
#: Repository root — parent of the ``senzing-bootcamp/`` power directory.
REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent

#: The MCP response caching steering file.
STEERING_FILE: Path = (
    REPO_ROOT / "senzing-bootcamp" / "steering" / "mcp-response-caching.md"
)

#: The steering index that registers all steering files.
STEERING_INDEX: Path = (
    REPO_ROOT / "senzing-bootcamp" / "steering" / "steering-index.yaml"
)

#: The repository .gitignore file.
GITIGNORE_FILE: Path = REPO_ROOT / ".gitignore"


class TestSteeringFileConfiguration:
    """Verify the MCP response caching steering file exists with correct frontmatter.

    Validates: Requirements 1.1, 1.2
    """

    def test_steering_file_exists(self) -> None:
        """The steering file SHALL reside at the expected path (Req 1.1)."""
        assert STEERING_FILE.exists(), (
            f"Expected steering file at {STEERING_FILE.relative_to(REPO_ROOT)}; "
            "file not found."
        )

    def test_steering_file_has_yaml_frontmatter(self) -> None:
        """The steering file SHALL contain YAML frontmatter delimiters (Req 1.2)."""
        content = STEERING_FILE.read_text(encoding="utf-8")
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert frontmatter_match is not None, (
            f"Expected YAML frontmatter delimited by '---' lines in "
            f"{STEERING_FILE.relative_to(REPO_ROOT)}; none found."
        )

    def test_steering_file_inclusion_auto(self) -> None:
        """The steering file SHALL have inclusion: auto in frontmatter (Req 1.2)."""
        content = STEERING_FILE.read_text(encoding="utf-8")
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert frontmatter_match is not None
        frontmatter = frontmatter_match.group(1)
        assert re.search(r"^inclusion:\s*auto\s*$", frontmatter, re.MULTILINE), (
            f"Expected 'inclusion: auto' in YAML frontmatter of "
            f"{STEERING_FILE.relative_to(REPO_ROOT)}; found frontmatter:\n"
            f"{frontmatter}"
        )


class TestSteeringIndexRegistration:
    """Verify the steering index contains keyword mappings and file_metadata.

    Validates: Requirements 6.1, 6.2, 6.3
    """

    def test_keyword_cache_mapping(self) -> None:
        """The steering index SHALL map 'cache' to mcp-response-caching.md (Req 6.1)."""
        index_data = yaml.safe_load(STEERING_INDEX.read_text(encoding="utf-8"))
        keywords = index_data.get("keywords", {})
        assert keywords.get("cache") == "mcp-response-caching.md", (
            "Expected keywords.cache == 'mcp-response-caching.md' in "
            f"{STEERING_INDEX.relative_to(REPO_ROOT)}; "
            f"got {keywords.get('cache')!r}."
        )

    def test_keyword_mcp_cache_mapping(self) -> None:
        """The steering index SHALL map 'mcp cache' to mcp-response-caching.md (Req 6.2)."""
        index_data = yaml.safe_load(STEERING_INDEX.read_text(encoding="utf-8"))
        keywords = index_data.get("keywords", {})
        assert keywords.get("mcp cache") == "mcp-response-caching.md", (
            "Expected keywords['mcp cache'] == 'mcp-response-caching.md' in "
            f"{STEERING_INDEX.relative_to(REPO_ROOT)}; "
            f"got {keywords.get('mcp cache')!r}."
        )

    def test_file_metadata_entry_exists(self) -> None:
        """The steering index SHALL have a file_metadata entry for the file (Req 6.3)."""
        index_data = yaml.safe_load(STEERING_INDEX.read_text(encoding="utf-8"))
        file_metadata = index_data.get("file_metadata", {})
        entry = file_metadata.get("mcp-response-caching.md")
        assert entry is not None, (
            "Expected file_metadata entry for 'mcp-response-caching.md' in "
            f"{STEERING_INDEX.relative_to(REPO_ROOT)}; not found."
        )

    def test_file_metadata_has_token_count(self) -> None:
        """The file_metadata entry SHALL include a token_count value (Req 6.3)."""
        index_data = yaml.safe_load(STEERING_INDEX.read_text(encoding="utf-8"))
        entry = index_data["file_metadata"]["mcp-response-caching.md"]
        assert "token_count" in entry, (
            "Expected 'token_count' key in file_metadata for "
            "'mcp-response-caching.md'; not found."
        )
        assert isinstance(entry["token_count"], int) and entry["token_count"] > 0, (
            f"Expected positive integer token_count; got {entry['token_count']!r}."
        )

    def test_file_metadata_has_size_category(self) -> None:
        """The file_metadata entry SHALL include a size_category value (Req 6.3)."""
        index_data = yaml.safe_load(STEERING_INDEX.read_text(encoding="utf-8"))
        entry = index_data["file_metadata"]["mcp-response-caching.md"]
        assert "size_category" in entry, (
            "Expected 'size_category' key in file_metadata for "
            "'mcp-response-caching.md'; not found."
        )
        valid_categories = {"small", "medium", "large"}
        assert entry["size_category"] in valid_categories, (
            f"Expected size_category in {valid_categories}; "
            f"got {entry['size_category']!r}."
        )


class TestGitignoreConfiguration:
    """Verify .gitignore contains the cache directory exclusion with comment.

    Validates: Requirements 7.1, 7.2
    """

    def test_gitignore_contains_cache_pattern(self) -> None:
        """The .gitignore SHALL exclude senzing-bootcamp/config/mcp_cache/ (Req 7.1)."""
        content = GITIGNORE_FILE.read_text(encoding="utf-8")
        assert "senzing-bootcamp/config/mcp_cache/" in content, (
            "Expected pattern 'senzing-bootcamp/config/mcp_cache/' in "
            f"{GITIGNORE_FILE.relative_to(REPO_ROOT)}; not found."
        )

    def test_gitignore_contains_cache_comment(self) -> None:
        """The .gitignore SHALL include a comment for the cache entry (Req 7.2)."""
        content = GITIGNORE_FILE.read_text(encoding="utf-8")
        assert "# MCP response cache runtime state" in content, (
            "Expected comment '# MCP response cache runtime state' in "
            f"{GITIGNORE_FILE.relative_to(REPO_ROOT)}; not found."
        )

    def test_gitignore_comment_precedes_pattern(self) -> None:
        """The comment SHALL appear before the exclusion pattern (Req 7.2)."""
        content = GITIGNORE_FILE.read_text(encoding="utf-8")
        comment_pos = content.find("# MCP response cache runtime state")
        pattern_pos = content.find("senzing-bootcamp/config/mcp_cache/")
        assert comment_pos >= 0 and pattern_pos >= 0, (
            "Both comment and pattern must exist in .gitignore."
        )
        assert comment_pos < pattern_pos, (
            "Expected comment '# MCP response cache runtime state' to appear "
            "before the exclusion pattern 'senzing-bootcamp/config/mcp_cache/' "
            f"in {GITIGNORE_FILE.relative_to(REPO_ROOT)}."
        )
