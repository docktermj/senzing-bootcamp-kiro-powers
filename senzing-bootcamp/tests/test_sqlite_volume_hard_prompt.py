"""Tests for the Module 6 SQLite volume Hard_Prompt trigger and wording.

Feature: module6-sqlite-volume-hard-prompt
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from volume_utils import (  # noqa: E402
    TIER_LARGE,
    TIER_MEDIUM,
    TIER_SMALL,
    VALID_TIERS,
    build_hard_prompt,
    should_prompt,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Junk strings that are neither valid tiers nor "sqlite" — used to exercise the
# indeterminate/unrecognized branches of the predicate.
_JUNK_STRINGS = ["", "  ", "SQLITE_DB", "mysql", "postgres", "unknown", "xyz", "123"]


@st.composite
def st_tier(draw) -> str | None:
    """Draw a volume tier: a valid tier, None, or an unrecognized junk string."""
    return draw(
        st.one_of(
            st.sampled_from(VALID_TIERS),
            st.none(),
            st.sampled_from(_JUNK_STRINGS),
            st.text(max_size=12),
        )
    )


@st.composite
def st_db_type(draw) -> str | None:
    """Draw a database type.

    Covers ``sqlite`` in mixed case and with surrounding whitespace (all of which
    normalize to SQLite), ``postgresql``, the empty string, ``None``, and junk.
    """
    sqlite_variants = ["sqlite", "SQLite", "SQLITE", " sqlite ", "  SqLiTe\t", "sqlite\n"]
    return draw(
        st.one_of(
            st.sampled_from(sqlite_variants),
            st.just("postgresql"),
            st.just(""),
            st.none(),
            st.sampled_from(_JUNK_STRINGS),
            st.text(max_size=12),
        )
    )


@st.composite
def st_record_count(draw) -> int | None:
    """Draw a record count: a non-negative integer or ``None`` (unavailable)."""
    return draw(st.one_of(st.integers(min_value=0), st.none()))


class TestSqliteVolumeHardPrompt:
    """Property and example tests for ``should_prompt`` / ``build_hard_prompt``.

    Validates: Requirements 1.1, 1.2, 1.3, 2.4, 3.3
    """

    # Feature: module6-sqlite-volume-hard-prompt, Property 1: Trigger fires
    # exactly on Medium/Large-on-SQLite (comprehensive truth table) — for any
    # tier, any db_type, and any already_decided, should_prompt returns True iff
    # tier in {TIER_MEDIUM, TIER_LARGE} AND normalized db_type == "sqlite" AND
    # already_decided is False, and never raises.
    # Validates: Requirements 1.1, 1.2, 1.3, 2.4, 3.3
    @given(tier=st_tier(), db_type=st_db_type(), already_decided=st.booleans())
    def test_trigger_truth_table(
        self, tier: str | None, db_type: str | None, already_decided: bool
    ) -> None:
        result = should_prompt(tier, db_type, already_decided)

        normalized_sqlite = isinstance(db_type, str) and db_type.strip().lower() == "sqlite"
        expected = (
            tier in (TIER_MEDIUM, TIER_LARGE)
            and normalized_sqlite
            and already_decided is False
        )

        assert result is expected

    # Feature: module6-sqlite-volume-hard-prompt, Property 2: Prompt names the
    # tier, record count, and expected slowdown — for any tier in
    # {TIER_MEDIUM, TIER_LARGE} and any record count (non-negative int or None),
    # build_hard_prompt returns text that names the tier, states the expected
    # slowdown on SQLite, includes the record count when present, omits it
    # gracefully when None, and never raises.
    # Validates: Requirements 2.1
    @given(
        tier=st.sampled_from([TIER_MEDIUM, TIER_LARGE]),
        record_count=st_record_count(),
    )
    def test_prompt_names_tier_count_and_slowdown(
        self, tier: str, record_count: int | None
    ) -> None:
        prompt = build_hard_prompt(tier, record_count)

        # Never raises and always returns text.
        assert isinstance(prompt, str)
        assert prompt.strip() != ""

        # Names the tier driving the warning.
        assert tier in prompt

        # States the expected slowdown on SQLite.
        assert "slow" in prompt.lower()
        assert "sqlite" in prompt.lower()

        if record_count is not None:
            # Includes the record count when present.
            assert str(record_count) in prompt
        else:
            # Omits the figure gracefully when None — no stray "None" leaks in.
            assert "None" not in prompt

    # Feature: module6-sqlite-volume-hard-prompt, Property 3: Prompt always
    # offers migration and proceed, and is never a mandatory gate — for any tier
    # in {TIER_MEDIUM, TIER_LARGE} and any record count, build_hard_prompt output
    # always contains a Migration_Alternative option naming the existing guide
    # (database-migration-guide / DATABASE_MIGRATION.md) AND a proceed-on-SQLite
    # option, and never contains the Mandatory_Gate marker (⛔).
    # Validates: Requirements 2.2, 3.1
    @given(
        tier=st.sampled_from([TIER_MEDIUM, TIER_LARGE]),
        record_count=st_record_count(),
    )
    def test_prompt_offers_migration_and_proceed_non_blocking(
        self, tier: str, record_count: int | None
    ) -> None:
        prompt = build_hard_prompt(tier, record_count)

        # Always offers the Migration_Alternative, naming the existing guide.
        assert "database-migration-guide" in prompt
        assert "DATABASE_MIGRATION.md" in prompt

        # Always offers a proceed-on-SQLite option.
        assert "Proceed on SQLite" in prompt

        # Never a Mandatory_Gate — the ⛔ marker must not appear.
        assert "\u26d4" not in prompt

    # -----------------------------------------------------------------------
    # Explicit truth-table cell examples (Task 4.1)
    #
    # The four corner cases of the {Demo, Small, Medium, Large} × {SQLite,
    # non-SQLite} trigger truth table, asserted as concrete examples that
    # complement the exhaustive Property 1 above.
    # Validates: Requirements 1.1, 1.2, 1.3, 4.1, 4.2
    # -----------------------------------------------------------------------

    def test_medium_on_sqlite_fires(self) -> None:
        """(medium, sqlite) → True — the risky combination fires the prompt."""
        assert should_prompt(TIER_MEDIUM, "sqlite") is True

    def test_large_on_sqlite_fires(self) -> None:
        """(large, sqlite) → True — the risky combination fires the prompt."""
        assert should_prompt(TIER_LARGE, "sqlite") is True

    def test_small_on_sqlite_does_not_fire(self) -> None:
        """(small, sqlite) → False — small volume never fires (Req 1.2)."""
        assert should_prompt(TIER_SMALL, "sqlite") is False

    def test_medium_on_postgresql_does_not_fire(self) -> None:
        """(medium, postgresql) → False — non-SQLite never fires (Req 1.3)."""
        assert should_prompt(TIER_MEDIUM, "postgresql") is False

    # -----------------------------------------------------------------------
    # Indeterminate-fallback and no-reprompt examples (Task 4.2)
    #
    # When the tier or db_type cannot be determined, the predicate falls back to
    # the existing advisory behavior (no prompt); once a choice has been recorded
    # for the current load, the predicate does not re-prompt.
    # Validates: Requirements 2.4, 3.3, 4.1
    # -----------------------------------------------------------------------

    def test_indeterminate_tier_does_not_fire(self) -> None:
        """(None, sqlite) → False — indeterminate tier falls back (Req 3.3)."""
        assert should_prompt(None, "sqlite") is False

    def test_indeterminate_db_type_does_not_fire(self) -> None:
        """(medium, None) → False — indeterminate db_type falls back (Req 3.3)."""
        assert should_prompt(TIER_MEDIUM, None) is False

    def test_already_decided_does_not_reprompt(self) -> None:
        """(medium, sqlite, already_decided=True) → False — no re-prompt (Req 2.4)."""
        assert should_prompt(TIER_MEDIUM, "sqlite", already_decided=True) is False

    # -----------------------------------------------------------------------
    # Migration-routing / reuse guardrail examples (Task 4.3)
    #
    # The prompt must ROUTE to the existing database-migration-guide rather than
    # duplicating the procedure, and both pure functions must live in
    # volume_utils.py and reuse the existing tier constants rather than
    # re-deriving tiers from raw record counts.
    # Validates: Requirements 2.3, 3.2, 4.1
    # -----------------------------------------------------------------------

    def test_prompt_routes_to_migration_guide(self) -> None:
        """Prompt names the existing guide by id and repo-relative path (Req 2.3)."""
        prompt = build_hard_prompt(TIER_MEDIUM, 750_000)

        # Points at the existing guide rather than duplicating it.
        assert "database-migration-guide" in prompt
        assert "DATABASE_MIGRATION.md" in prompt

    def test_prompt_does_not_inline_migration_procedure(self) -> None:
        """Prompt points to the guide but inlines no step-by-step procedure (Req 2.3, 3.2)."""
        # Build across both firing tiers, with and without a record count, so the
        # guardrail holds for every prompt the builder can emit.
        prompts = [
            build_hard_prompt(TIER_MEDIUM),
            build_hard_prompt(TIER_MEDIUM, 750_000),
            build_hard_prompt(TIER_LARGE),
            build_hard_prompt(TIER_LARGE, 25_000_000),
        ]

        # Concrete procedure keywords that only appear when the migration steps
        # are copied inline (they live in DATABASE_MIGRATION.md, not the prompt).
        procedure_markers = [
            "CREATE USER",
            "CREATE DATABASE",
            "GRANT ALL PRIVILEGES",
            "DROP DATABASE",
            "psql",
            "pg_hba",
            "postgresql://",
            "Step 1:",
            "Step 2:",
            "Step 3:",
            "Step 4:",
            "sdk_guide",
            "search_docs",
            "Initialize Senzing Schema",
        ]

        for prompt in prompts:
            for marker in procedure_markers:
                assert marker not in prompt, (
                    f"prompt should route to the guide, not inline the procedure "
                    f"(found inlined step marker: {marker!r})"
                )

    def test_functions_defined_in_volume_utils(self) -> None:
        """should_prompt / build_hard_prompt are defined in volume_utils.py (Req 3.2)."""
        for func in (should_prompt, build_hard_prompt):
            assert func.__module__ == "volume_utils"
            source_file = inspect.getsourcefile(func)
            assert source_file is not None
            assert Path(source_file).name == "volume_utils.py"

    def test_should_prompt_reuses_tier_constants_not_record_counts(self) -> None:
        """should_prompt relies on the tier constants, not raw record-count thresholds (Req 3.2)."""
        source = inspect.getsource(should_prompt)

        # Reuses the existing tier vocabulary rather than parallel logic.
        assert "TIER_MEDIUM" in source
        assert "TIER_LARGE" in source

        # Does not re-derive tiers from raw record counts: it neither takes a
        # record count nor re-runs / restates the classification thresholds.
        assert "record_count" not in source
        assert "classify_tier" not in source
        assert "TIER_BOUNDARIES" not in source
        for boundary in ("500_000", "500000", "10_000_000", "10000000"):
            assert boundary not in source


# ---------------------------------------------------------------------------
# Steering-structure test (Task 5.2)
# ---------------------------------------------------------------------------

_STEERING_FILE = (
    Path(__file__).resolve().parent.parent
    / "steering"
    / "module-06-phaseA-build-loading.md"
)

# Heading of the pre-load block wired into Phase A steering.
_HARD_PROMPT_HEADING = "## SQLite Volume Hard_Prompt (pre-load check)"


def _read_steering() -> str:
    """Return the full Module 6 Phase A steering markdown."""
    return _STEERING_FILE.read_text(encoding="utf-8")


def _hard_prompt_section(text: str) -> str:
    """Extract the 'SQLite Volume Hard_Prompt (pre-load check)' section body.

    Returns the text from the section heading up to the next top-level ('## ')
    heading (or end of file). Falls back to the full document if the heading is
    absent so the assertions surface a clear failure.
    """
    start = text.find(_HARD_PROMPT_HEADING)
    if start == -1:
        return text
    rest = text[start + len(_HARD_PROMPT_HEADING):]
    next_heading = rest.find("\n## ")
    if next_heading == -1:
        return _HARD_PROMPT_HEADING + rest
    return _HARD_PROMPT_HEADING + rest[:next_heading]


class TestSqliteVolumeHardPromptSteering:
    """Structure tests for the Module 6 Phase A Hard_Prompt steering block.

    Assert the wired-in ``module-06-phaseA-build-loading.md`` block calls
    ``should_prompt`` before the Phase B load, presents ``build_hard_prompt`` on
    the trigger, routes the migrate choice to the existing
    ``database-migration-guide``, records the choice via the decision marker,
    inlines no migration steps, contains no Mandatory_Gate marker, and
    references no external URLs.

    Validates: Requirements 2.3, 3.1, 3.2, 4.2
    """

    def test_steering_file_exists(self) -> None:
        """The Phase A steering file is present at the expected repo-relative path."""
        assert _STEERING_FILE.is_file()

    def test_hard_prompt_section_present(self) -> None:
        """The 'SQLite Volume Hard_Prompt (pre-load check)' section exists."""
        text = _read_steering()
        assert _HARD_PROMPT_HEADING in text

    def test_calls_should_prompt_before_phase_b_load(self) -> None:
        """The block calls should_prompt, positioned before the Phase B load (Req 4.2)."""
        section = _hard_prompt_section(_read_steering())

        # The predicate is invoked in the block.
        assert "should_prompt" in section

        # The block is explicitly scoped to run before the Phase B load begins.
        assert "before the Phase B load" in section

        # should_prompt is called before build_hard_prompt is presented.
        assert section.index("should_prompt") < section.index("build_hard_prompt")

    def test_presents_build_hard_prompt_on_trigger(self) -> None:
        """On a True trigger the block presents build_hard_prompt output (Req 4.2)."""
        section = _hard_prompt_section(_read_steering())
        assert "build_hard_prompt" in section

    def test_routes_migrate_to_existing_migration_guide(self) -> None:
        """The migrate choice routes to the existing database-migration-guide (Req 2.3)."""
        section = _hard_prompt_section(_read_steering())
        assert "database-migration-guide" in section
        assert "docs/guides/DATABASE_MIGRATION.md" in section

    def test_records_choice_via_decision_marker(self) -> None:
        """Proceed/migrate choices are recorded via the decision marker (Req 2.4)."""
        section = _hard_prompt_section(_read_steering())

        # The load-scoped decision marker key and the persistence writer.
        assert "sqlite_volume_prompt" in section
        assert "write_preference" in section

        # Both choices are recorded.
        assert '"choice": "migrate"' in section
        assert '"choice": "proceed"' in section

    def test_inlines_no_migration_steps(self) -> None:
        """The block routes to the guide and inlines no migration procedure (Req 3.2)."""
        section = _hard_prompt_section(_read_steering())

        procedure_markers = [
            "CREATE USER",
            "CREATE DATABASE",
            "GRANT ALL PRIVILEGES",
            "DROP DATABASE",
            "psql",
            "pg_hba",
            "Initialize Senzing Schema",
        ]
        for marker in procedure_markers:
            assert marker not in section, (
                f"steering should route to the guide, not inline the procedure "
                f"(found inlined step marker: {marker!r})"
            )

    def test_no_mandatory_gate_marker(self) -> None:
        """The block is a stop-and-confirm, never an active Mandatory_Gate (Req 3.1).

        The block declares itself non-blocking. Per the established codebase idiom
        (cf. onboarding-phase1b-intro-language.md: "This is NOT a mandatory gate
        (marker)"), the only allowed gate glyph is inside the explicit negation
        "there is no <glyph>". The glyph must never be used as an *active* gate
        marker (e.g. "<glyph> MANDATORY GATE", "## <glyph> PHASE GATE").
        """
        section = _hard_prompt_section(_read_steering())
        gate = "\u26d4"

        # The block explicitly labels itself as NOT a Mandatory_Gate.
        assert "NOT a Mandatory_Gate" in section

        # Strip the sanctioned negation declaration; no gate glyph may remain, so
        # the glyph is never used as an active gate marker.
        residual = section.replace(f"there is no {gate}", "")
        assert gate not in residual

    def test_no_external_urls(self) -> None:
        """The block references no external URLs — migration guide by path only."""
        section = _hard_prompt_section(_read_steering())
        assert "http" + "://" not in section
        assert "https" + "://" not in section
