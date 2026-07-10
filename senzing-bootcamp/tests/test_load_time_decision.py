"""Unit tests for the Module 4 Load_Time_Warning decision marker.

Covers the shared ``sqlite_volume_prompt`` decision-marker schema extension
(module4-sqlite-load-time-warning spec):

- Task 7.2: schema unit tests for both marker shapes
  - The Module 4 shape (``source: module4_load_time``, ``choice`` in
    {proceed, sample, switch_db}, ``load_identity``) validates.
  - The unchanged Module 6 shape (``source: module6_volume``, ``tier``,
    ``raw_value``, ``choice`` in {proceed, migrate}) validates.
  - Unknown sub-keys and out-of-enum ``source``/``choice`` values are rejected.

Later tasks (8.2, 8.4) add decision round-trip and Module 6 scoping tests to
this same file/class.
"""

from __future__ import annotations

import random
import sys
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from data_sources import Registry, RegistryEntry  # noqa: E402
from load_time_warning import (  # noqa: E402
    LOAD_MARKER_SOURCE,
    compute_load_identity,
    module4_decision_applies,
    read_load_decision,
    write_load_decision,
)
from preferences_utils import validate_preferences_schema  # noqa: E402

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# The three Module 4 Load_Time_Warning options (Requirement 6.1). "migrate" is a
# Module 6-only choice and is deliberately excluded here.
_MODULE4_CHOICES: tuple[str, ...] = ("proceed", "sample", "switch_db")

# A safe alphabet for the general load-identity branch: letters, digits, and a
# few punctuation marks that all round-trip through the minimal preferences YAML
# serializer/parser (a ":" forces quoting on write and is unquoted on read; no
# newlines or leading/trailing whitespace are generated so nothing is lost).
_IDENTITY_ALPHABET: str = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:_.-"
)


@st.composite
def st_choice(draw) -> str:
    """Draw a Module 4 Load_Time_Warning choice (proceed, sample, switch_db)."""
    return draw(st.sampled_from(_MODULE4_CHOICES))


@st.composite
def st_load_identity(draw) -> str:
    """Draw a non-empty load-identity string that round-trips through preferences.

    Covers the real ``compute_load_identity`` shape (``"sha256:"`` + hex) plus
    arbitrary non-empty identifiers over a safe alphabet, so the round-trip is
    exercised across a wide identity space without tripping the minimal YAML
    serializer on newlines or surrounding whitespace.
    """
    return draw(
        st.one_of(
            st.builds(
                lambda hexdigest: f"sha256:{hexdigest}",
                st.text(alphabet="0123456789abcdef", min_size=1, max_size=64),
            ),
            st.text(alphabet=_IDENTITY_ALPHABET, min_size=1, max_size=40),
        )
    )


# ---------------------------------------------------------------------------
# Registry / db_type strategies for the load-identity + Module 6 scoping property
# ---------------------------------------------------------------------------
#
# compute_load_identity reads only each source's (data_source, record_count), so
# these registries are built in memory with synthetic, PII-free filler for the
# remaining RegistryEntry fields — no fixture files are needed.


def _st_data_source_key():
    """Strategy producing valid DATA_SOURCE key strings: ``^[A-Z][A-Z0-9_]*$``."""
    first = st.sampled_from(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    rest = st.text(
        alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_", min_size=0, max_size=8
    )
    return st.tuples(first, rest).map(lambda t: t[0] + t[1])


def _entry(key: str, record_count: int | None) -> RegistryEntry:
    """Build a synthetic, PII-free :class:`RegistryEntry`.

    Mirrors the ``_entry`` helper in ``test_load_time_warning.py``.
    ``compute_load_identity`` reads only ``data_source`` and ``record_count``;
    the remaining fields carry synthetic filler so the entry is well-formed.

    Args:
        key: The DATA_SOURCE key (also used as the display name).
        record_count: The stated record count, or ``None`` when unknown.

    Returns:
        A fully-populated :class:`RegistryEntry`.
    """
    return RegistryEntry(
        data_source=key,
        name=key,
        file_path=f"data/raw/{key}.csv",
        format="csv",
        record_count=record_count,
        file_size_bytes=None,
        quality_score=None,
        mapping_status="pending",
        load_status="not_loaded",
        added_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
        test_load_status=None,
        test_entity_count=None,
        issues=None,
    )


@st.composite
def st_registry(draw) -> Registry:
    """Draw a :class:`Registry` with unique DATA_SOURCE keys and varied counts.

    Source keys are unique and match ``^[A-Z][A-Z0-9_]*$``; each source's
    ``record_count`` is a non-negative integer or ``None`` (unknown) so the
    identity signature exercises both the integer and ``"unknown"`` renderings.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A :class:`Registry` (possibly with zero sources).
    """
    keys = draw(st.lists(_st_data_source_key(), min_size=0, max_size=6, unique=True))
    entries = [
        _entry(
            key,
            draw(st.one_of(st.none(), st.integers(min_value=0, max_value=200_000))),
        )
        for key in keys
    ]
    return Registry(version="2", sources=entries)


@st.composite
def st_db_type(draw) -> str | None:
    """Draw an active database type.

    Covers ``sqlite`` in mixed case / with surrounding whitespace (all normalize
    to SQLite), ``postgresql``, the empty string, ``None``, and junk strings that
    never normalize to SQLite.
    """
    sqlite_variants = ["sqlite", "SQLite", "SQLITE", " sqlite ", "  SqLiTe\t", "sqlite\n"]
    return draw(
        st.one_of(
            st.sampled_from(sqlite_variants),
            st.just("postgresql"),
            st.just(""),
            st.none(),
            st.sampled_from(["mysql", "postgres", "unknown", "SQLITE_DB", "xyz"]),
            st.text(max_size=12),
        )
    )


# ═══════════════════════════════════════════════════════════════════════════
# Task 7.2 — Decision-marker schema, both shapes
# Requirements: 6.2
# ═══════════════════════════════════════════════════════════════════════════


class TestDecisionMarker:
    """Verify the shared sqlite_volume_prompt marker validates both shapes."""

    def test_module4_shape_is_accepted(self) -> None:
        """The Module 4 Load_Time_Warning marker shape validates.

        The Module 4 shape carries ``source: module4_load_time``, a
        ``load_identity``, and a ``choice`` drawn from the Module 4 options
        (proceed, sample, switch_db); ``tier``/``raw_value`` are absent.

        Validates: Req 6.2
        """
        for choice in ("proceed", "sample", "switch_db"):
            prefs = {
                "database_type": "sqlite",
                "sqlite_volume_prompt": {
                    "decided": True,
                    "choice": choice,
                    "source": "module4_load_time",
                    "load_identity": "sha256:abc123",
                },
            }
            errors = validate_preferences_schema(prefs)
            assert errors == [], (
                f"Module 4 marker with choice '{choice}' produced errors: {errors}"
            )

    def test_module6_shape_is_accepted(self) -> None:
        """The unchanged Module 6 Hard_Prompt marker shape validates.

        The Module 6 shape carries ``source: module6_volume``, ``tier``,
        ``raw_value``, and a ``choice`` drawn from the Module 6 options
        (proceed, migrate).

        Validates: Req 6.2
        """
        for choice in ("proceed", "migrate"):
            prefs = {
                "database_type": "sqlite",
                "sqlite_volume_prompt": {
                    "decided": True,
                    "choice": choice,
                    "source": "module6_volume",
                    "tier": "medium",
                    "raw_value": 123911,
                },
            }
            errors = validate_preferences_schema(prefs)
            assert errors == [], (
                f"Module 6 marker with choice '{choice}' produced errors: {errors}"
            )

    def test_legacy_module6_shape_without_source_is_accepted(self) -> None:
        """A pre-extension Module 6 marker (no ``source``) still validates.

        ``source`` is optional, so a marker written before the schema
        extension — carrying only ``tier``/``raw_value`` — remains valid for
        backward compatibility.

        Validates: Req 6.2
        """
        prefs = {
            "database_type": "sqlite",
            "sqlite_volume_prompt": {
                "decided": True,
                "choice": "migrate",
                "tier": "large",
                "raw_value": 50000000,
            },
        }
        assert validate_preferences_schema(prefs) == []

    def test_unknown_sub_key_is_rejected(self) -> None:
        """An unrecognized marker sub-key produces a schema error.

        Validates: Req 6.2
        """
        prefs = {
            "database_type": "sqlite",
            "sqlite_volume_prompt": {
                "decided": True,
                "choice": "proceed",
                "source": "module4_load_time",
                "load_identity": "sha256:abc123",
                "bogus_field": "value",
            },
        }
        errors = validate_preferences_schema(prefs)
        assert errors, "Expected an error for the unknown sub-key"
        assert any("sqlite_volume_prompt" in err for err in errors), (
            f"Expected a sqlite_volume_prompt error, got: {errors!r}"
        )

    def test_out_of_enum_source_is_rejected(self) -> None:
        """A ``source`` outside the allowed enum produces a schema error.

        Validates: Req 6.2
        """
        prefs = {
            "database_type": "sqlite",
            "sqlite_volume_prompt": {
                "decided": True,
                "choice": "proceed",
                "source": "module7_unknown",
                "load_identity": "sha256:abc123",
            },
        }
        errors = validate_preferences_schema(prefs)
        assert errors, "Expected an error for the out-of-enum source"
        assert any("source" in err for err in errors), (
            f"Expected a source enum error, got: {errors!r}"
        )

    def test_out_of_enum_choice_is_rejected(self) -> None:
        """A ``choice`` outside the allowed enum produces a schema error.

        Validates: Req 6.2
        """
        prefs = {
            "database_type": "sqlite",
            "sqlite_volume_prompt": {
                "decided": True,
                "choice": "abandon",
                "source": "module4_load_time",
                "load_identity": "sha256:abc123",
            },
        }
        errors = validate_preferences_schema(prefs)
        assert errors, "Expected an error for the out-of-enum choice"
        assert any("choice" in err for err in errors), (
            f"Expected a choice enum error, got: {errors!r}"
        )

    # ═══════════════════════════════════════════════════════════════════════
    # Task 8.2 — Decision-marker round-trip
    # ═══════════════════════════════════════════════════════════════════════

    # Feature: module4-sqlite-load-time-warning, Property 7: Decision-marker
    # round-trips choice and load identity through the shared marker — for any
    # choice drawn from {"proceed", "sample", "switch_db"} and any load_identity
    # string, writing the decision with write_load_decision(choice,
    # load_identity, preferences_path) and then reading it back with
    # read_load_decision(preferences_path) yields a marker under the shared
    # sqlite_volume_prompt key whose decided is True, whose choice equals the
    # written choice, whose source is "module4_load_time", and whose
    # load_identity equals the written load_identity.
    # Validates: Requirements 6.1, 6.2
    @given(choice=st_choice(), load_identity=st_load_identity())
    def test_decision_marker_round_trips_choice_and_identity(
        self, choice: str, load_identity: str
    ) -> None:
        # A fresh temp dir per example keeps each write/read isolated and avoids
        # the function-scoped-fixture health check that pytest's tmp_path would
        # trip under @given.
        with tempfile.TemporaryDirectory() as tmpdir:
            prefs_path = str(Path(tmpdir) / "bootcamp_preferences.yaml")

            write_result = write_load_decision(choice, load_identity, prefs_path)
            assert write_result.success is True, write_result.error

            marker = read_load_decision(prefs_path)

            # A decided Module 4 marker is round-tripped under the shared key.
            assert isinstance(marker, dict), f"Expected a marker dict, got {marker!r}"
            assert marker.get("decided") is True
            assert marker.get("choice") == choice
            assert marker.get("source") == LOAD_MARKER_SOURCE == "module4_load_time"
            assert marker.get("load_identity") == load_identity

    # ═══════════════════════════════════════════════════════════════════════
    # Task 8.4 — Identity determinism + Module 6 scoping
    # ═══════════════════════════════════════════════════════════════════════

    # Feature: module4-sqlite-load-time-warning, Property 8: Module 6 honors a
    # Module 4 decision only for the same load on SQLite — for any two registries
    # with identities id_a = compute_load_identity(reg_a) and id_b =
    # compute_load_identity(reg_b): compute_load_identity is deterministic and
    # independent of source ordering (recomputing on a reordering of the same
    # sources yields the same identity), and differing source/count sets yield
    # differing identities; and for a decided Module 4 marker recorded with
    # load_identity = id_a, module4_decision_applies(marker, current_identity,
    # db_type) returns True iff current_identity == id_a AND normalized db_type
    # == "sqlite", and returns False whenever the identity differs
    # (current_identity == id_b != id_a) or the marker is not a decided Module 4
    # marker. It never raises.
    # Validates: Requirements 6.3, 6.4
    @given(
        reg_a=st_registry(),
        reg_b=st_registry(),
        choice=st_choice(),
        db_type=st_db_type(),
        seed=st.integers(),
    )
    def test_identity_determinism_and_module6_scoping(
        self,
        reg_a: Registry,
        reg_b: Registry,
        choice: str,
        db_type: str | None,
        seed: int,
    ) -> None:
        id_a = compute_load_identity(reg_a)
        id_b = compute_load_identity(reg_b)

        # --- Identity shape: always "sha256:<hexdigest>" ---
        assert id_a.startswith("sha256:")
        assert id_b.startswith("sha256:")

        # --- Determinism: recomputing on the same registry yields the same id ---
        assert compute_load_identity(reg_a) == id_a

        # --- Order-independence: any reordering of the same sources is the same id.
        shuffled = list(reg_a.sources)
        random.Random(seed).shuffle(shuffled)
        assert compute_load_identity(Registry(version=reg_a.version, sources=shuffled)) == id_a
        assert (
            compute_load_identity(
                Registry(version=reg_a.version, sources=list(reversed(reg_a.sources)))
            )
            == id_a
        )

        # --- Differing (source, count) sets differ; equal sets match. Source keys
        # are unique within a registry, so the identity is a function of the set
        # of (data_source, record_count) pairs (modulo hash collision).
        def _source_count_set(reg: Registry) -> frozenset[tuple[str, int | None]]:
            return frozenset((e.data_source, e.record_count) for e in reg.sources)

        if _source_count_set(reg_a) == _source_count_set(reg_b):
            assert id_a == id_b
        else:
            assert id_a != id_b

        # --- Scoping: a decided Module 4 marker recorded for load id_a ---
        marker = {
            "decided": True,
            "choice": choice,
            "source": LOAD_MARKER_SOURCE,
            "load_identity": id_a,
        }
        normalized_sqlite = (
            isinstance(db_type, str) and db_type.strip().lower() == "sqlite"
        )

        # Same load (current_identity == id_a): applies iff the db is SQLite.
        assert module4_decision_applies(marker, id_a, db_type) is normalized_sqlite

        # Other load (current_identity == id_b): applies iff id_b == id_a AND SQLite.
        assert module4_decision_applies(marker, id_b, db_type) is (
            id_b == id_a and normalized_sqlite
        )

        # --- False for a non-decided or non-Module-4 marker, even on the same load ---
        undecided = {**marker, "decided": False}
        assert module4_decision_applies(undecided, id_a, db_type) is False

        module6_marker = {**marker, "source": "module6_volume"}
        assert module4_decision_applies(module6_marker, id_a, db_type) is False

        assert module4_decision_applies(None, id_a, db_type) is False
