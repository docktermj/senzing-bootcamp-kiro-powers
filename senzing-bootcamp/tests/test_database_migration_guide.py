"""Structural validation tests for the DATABASE_MIGRATION.md guide.

Validates that the database migration guide meets all requirements defined in
``.kiro/specs/database-migration-guide/requirements.md``:

- Req 1: Guide file exists at expected path
- Req 2: All required sections present
- Req 3: SQLite limitations and PostgreSQL advantages explained
- Req 4: sdk_guide MCP tool reference with configure topic
- Req 5: search_docs MCP tool reference with PostgreSQL query
- Req 6: Cross-reference from Module 8 Phase C steering
- Req 7: Entry in docs/guides/README.md
- Req 8: No re-mapping instructions; re-loading from JSON mentioned
- Req 9: Rollback section with SQLite preservation
- Req 10: database_type preference field documented with valid values

Tests use stdlib only (pathlib, re) with pytest as the test runner.
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Module-level path constants
# ---------------------------------------------------------------------------

#: The senzing-bootcamp power root directory.
_BOOTCAMP_DIR: Path = Path(__file__).resolve().parent.parent

#: The database migration guide under test.
_GUIDE_PATH: Path = _BOOTCAMP_DIR / "docs" / "guides" / "DATABASE_MIGRATION.md"

#: Module 8 Phase C steering file (cross-reference source).
_MODULE8_PHASE_C_PATH: Path = _BOOTCAMP_DIR / "steering" / "module-08-phaseC-optimization.md"

#: The guides README that indexes all guides.
_GUIDES_README_PATH: Path = _BOOTCAMP_DIR / "docs" / "guides" / "README.md"


class TestDatabaseMigrationGuide:
    """Structural validation for docs/guides/DATABASE_MIGRATION.md.

    Each test method validates one or more requirements from the spec.
    """

    def test_guide_file_exists(self) -> None:
        """Validates: Requirement 1.

        The guide file must exist at docs/guides/DATABASE_MIGRATION.md.
        """
        assert _GUIDE_PATH.exists(), (
            f"Expected guide file at {_GUIDE_PATH.relative_to(_BOOTCAMP_DIR)} "
            "but it does not exist (Req 1)"
        )

    def test_required_sections_present(self) -> None:
        """Validates: Requirement 2.

        The guide must include sections for: prerequisites, database creation,
        schema initialization, data re-loading, verification, and rollback.
        """
        text = _GUIDE_PATH.read_text(encoding="utf-8")
        headings = [
            match.group(1).strip().lower()
            for match in re.finditer(r"^## (.+)$", text, re.MULTILINE)
        ]

        required_sections = [
            ("prerequisites", lambda h: "prerequisite" in h),
            ("database creation", lambda h: "create" in h and "database" in h),
            ("schema initialization", lambda h: "schema" in h or "initialize" in h),
            ("re-load data", lambda h: "load" in h and "data" in h),
            ("verification", lambda h: "verify" in h or "verification" in h),
            ("rollback", lambda h: "rollback" in h),
        ]

        for section_name, predicate in required_sections:
            assert any(predicate(h) for h in headings), (
                f"No '## ' heading covers required section '{section_name}' (Req 2). "
                f"Headings found: {headings}"
            )

    def test_sqlite_limitations_explained(self) -> None:
        """Validates: Requirement 3 (SQLite limitations).

        The guide must explain SQLite limitations including single-writer
        constraint, no network access, and performance ceiling at ~100K records.
        """
        text = _GUIDE_PATH.read_text(encoding="utf-8").lower()

        assert "single-writer" in text or "single writer" in text, (
            "Guide must mention SQLite single-writer limitation (Req 3)"
        )
        assert "network" in text, (
            "Guide must mention SQLite lack of network access (Req 3)"
        )
        assert "100k" in text or "100,000" in text, (
            "Guide must mention performance ceiling at ~100K records (Req 3)"
        )

    def test_postgresql_advantages_explained(self) -> None:
        """Validates: Requirement 3 (PostgreSQL advantages).

        The guide must explain PostgreSQL advantages including concurrent access,
        production-grade reliability, and multi-process loading support.
        """
        text = _GUIDE_PATH.read_text(encoding="utf-8").lower()

        assert "concurrent" in text, (
            "Guide must mention PostgreSQL concurrent access (Req 3)"
        )
        assert "production" in text, (
            "Guide must mention PostgreSQL production-grade capability (Req 3)"
        )
        assert "multi-process" in text or "multi-threaded" in text, (
            "Guide must mention multi-process or multi-threaded loading (Req 3)"
        )

    def test_sdk_guide_mcp_reference(self) -> None:
        """Validates: Requirement 4.

        The guide must include an agent instruction block calling
        sdk_guide with topic='configure' for PostgreSQL engine configuration.
        """
        text = _GUIDE_PATH.read_text(encoding="utf-8")

        assert "sdk_guide" in text, (
            "Guide must reference the sdk_guide MCP tool (Req 4)"
        )
        assert re.search(r"sdk_guide.*configure", text, re.DOTALL), (
            "Guide must call sdk_guide with topic='configure' (Req 4)"
        )

    def test_search_docs_mcp_reference(self) -> None:
        """Validates: Requirement 5.

        The guide must include an agent instruction block calling
        search_docs with a PostgreSQL-related query.
        """
        text = _GUIDE_PATH.read_text(encoding="utf-8")

        assert "search_docs" in text, (
            "Guide must reference the search_docs MCP tool (Req 5)"
        )
        assert re.search(r"search_docs.*postgresql", text, re.IGNORECASE), (
            "Guide must call search_docs with a PostgreSQL-related query (Req 5)"
        )

    def test_module8_cross_reference(self) -> None:
        """Validates: Requirement 6.

        Module 8 Phase C steering file must contain a cross-reference
        to DATABASE_MIGRATION.md.
        """
        assert _MODULE8_PHASE_C_PATH.exists(), (
            f"Module 8 Phase C file not found at "
            f"{_MODULE8_PHASE_C_PATH.relative_to(_BOOTCAMP_DIR)} (Req 6)"
        )
        text = _MODULE8_PHASE_C_PATH.read_text(encoding="utf-8")

        assert "DATABASE_MIGRATION" in text, (
            "Module 8 Phase C steering must reference DATABASE_MIGRATION guide (Req 6)"
        )

    def test_guides_readme_entry(self) -> None:
        """Validates: Requirement 7.

        The guides README.md must contain an entry for DATABASE_MIGRATION.md.
        """
        assert _GUIDES_README_PATH.exists(), (
            f"Guides README not found at "
            f"{_GUIDES_README_PATH.relative_to(_BOOTCAMP_DIR)} (Req 7)"
        )
        text = _GUIDES_README_PATH.read_text(encoding="utf-8")

        assert "DATABASE_MIGRATION" in text, (
            "docs/guides/README.md must list DATABASE_MIGRATION.md (Req 7)"
        )

    def test_no_remapping_instructions(self) -> None:
        """Validates: Requirement 8.

        The guide must NOT instruct users to re-map data. It MUST mention
        re-loading from existing JSON files. The guide may mention re-mapping
        only in a negative context (e.g., "you do not need to re-map").
        """
        text = _GUIDE_PATH.read_text(encoding="utf-8")
        lower_text = text.lower()

        # Negative check: guide must not positively instruct re-mapping.
        # Phrases like "re-map your data" are acceptable only when preceded
        # by a negation (e.g., "not need to re-map", "not a re-mapping").
        # Check for affirmative re-mapping instructions (imperative form).
        affirmative_remap_patterns = [
            r"(?<!not need to )re-map your (?:raw |source )?data(?! —)",
            r"you (?:should|must|need to) re-?map",
            r"map your raw data again",
            r"repeat the mapping",
        ]
        for pattern in affirmative_remap_patterns:
            assert not re.search(pattern, lower_text), (
                f"Guide must NOT instruct re-mapping (matched: '{pattern}') (Req 8)"
            )

        # Positive check: mentions re-loading from JSON files
        assert "re-load" in lower_text or "reload" in lower_text, (
            "Guide must mention re-loading data (Req 8)"
        )
        assert "json" in lower_text, (
            "Guide must mention loading from JSON files (Req 8)"
        )

    def test_rollback_section_present(self) -> None:
        """Validates: Requirement 9.

        The guide must have a rollback section that mentions the SQLite
        database remaining intact.
        """
        text = _GUIDE_PATH.read_text(encoding="utf-8")

        # Verify rollback heading exists
        assert re.search(r"^## Rollback", text, re.MULTILINE), (
            "Guide must have a '## Rollback' section (Req 9)"
        )

        # Extract rollback section content (from ## Rollback to next ## or end)
        rollback_match = re.search(
            r"^## Rollback\s*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
        )
        assert rollback_match, (
            "Could not extract rollback section content (Req 9)"
        )
        rollback_text = rollback_match.group(1).lower()

        assert "sqlite" in rollback_text, (
            "Rollback section must mention SQLite (Req 9)"
        )
        assert "intact" in rollback_text or "never modified" in rollback_text, (
            "Rollback section must mention SQLite database remains intact (Req 9)"
        )

    def test_database_type_preference_documented(self) -> None:
        """Validates: Requirement 10.

        The guide must document the database_type preference field
        with valid values (sqlite, postgresql).
        """
        text = _GUIDE_PATH.read_text(encoding="utf-8")
        lower_text = text.lower()

        assert "database_type" in text, (
            "Guide must mention the database_type preference field (Req 10)"
        )
        assert "sqlite" in lower_text, (
            "Guide must document 'sqlite' as a valid database_type value (Req 10)"
        )
        assert "postgresql" in lower_text, (
            "Guide must document 'postgresql' as a valid database_type value (Req 10)"
        )
