"""Property-based and unit tests for record_count_backfill.py.

Uses Hypothesis to verify the correctness properties of the Module 4
record-count license back-fill helper across randomly generated registries.
Fixtures are synthetic and PII-free (Requirement 4.2 and the power-distribution
safety rule): only source names, counts, and fixed guidance text are exercised.
"""

from __future__ import annotations

import ast
import contextlib
import inspect
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from hypothesis import assume, given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts are not a package).
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import preferences_utils  # noqa: E402  (path manipulated above)
import record_count_backfill as rcb  # noqa: E402  (path manipulated above)
import volume_utils  # noqa: E402  (path manipulated above)
from data_sources import (  # noqa: E402  (path manipulated above)
    VALID_FORMATS,
    Registry,
    RegistryEntry,
    _dict_to_registry,
    _registry_to_dict,
    apply_migrations,
    parse_registry_yaml,
    serialize_registry_yaml,
    validate_registry,
)

# ═══════════════════════════════════════════════════════════════════════════
# Hypothesis strategies (st_ prefix per python-conventions)
# ═══════════════════════════════════════════════════════════════════════════


def _st_data_source_keys():
    """Strategy producing valid DATA_SOURCE key strings: ^[A-Z][A-Z0-9_]*$."""
    first = st.sampled_from(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    rest = st.text(
        alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_", min_size=0, max_size=12
    )
    return st.tuples(first, rest).map(lambda t: t[0] + t[1])


def _st_safe_name():
    """Strategy producing PII-free source names that round-trip through YAML."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters=" _",
        ),
        min_size=1,
        max_size=24,
    ).filter(lambda s: s.strip() != "")


def _st_record_count():
    """Strategy: a non-negative integer count OR ``None`` (unknown)."""
    return st.one_of(st.none(), st.integers(min_value=0, max_value=1_000_000))


def _st_registry_entry(key):
    """Strategy producing a valid RegistryEntry for a fixed DATA_SOURCE key."""
    return st.builds(
        RegistryEntry,
        data_source=st.just(key),
        name=_st_safe_name(),
        file_path=st.builds(
            lambda n: f"data/raw/{n}.csv",
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=10),
        ),
        format=st.sampled_from(sorted(VALID_FORMATS)),
        record_count=_st_record_count(),
        file_size_bytes=st.none(),
        quality_score=st.one_of(st.none(), st.integers(min_value=0, max_value=100)),
        mapping_status=st.just("pending"),
        load_status=st.just("not_loaded"),
        added_at=st.just("2025-01-01T00:00:00Z"),
        updated_at=st.just("2025-01-01T00:00:00Z"),
        test_load_status=st.none(),
        test_entity_count=st.none(),
        issues=st.none(),
    )


@st.composite
def st_registry(draw, min_sources=0, max_sources=8):
    """Draw a registry, render it to the restricted YAML, and round-trip it.

    Generates a set of synthetic, PII-free sources — each with a non-negative
    integer or ``null`` ``record_count`` and a valid format — serializes them to
    the restricted registry YAML, then parses them back through the real
    ``parse_registry_yaml`` + ``apply_migrations`` + ``_dict_to_registry`` chain
    (mirroring how ``main`` wires the reader). Returning the *parsed* registry
    guarantees the round-trip is valid and that expectations are derived from
    exactly what the helper sees.

    Args:
        draw: The Hypothesis draw callable.
        min_sources: Minimum number of sources to generate.
        max_sources: Maximum number of sources to generate.

    Returns:
        A parsed :class:`Registry` ready to feed ``compute_collected_count``.
    """
    keys = draw(
        st.lists(
            _st_data_source_keys(),
            min_size=min_sources,
            max_size=max_sources,
            unique=True,
        )
    )
    entries = [draw(_st_registry_entry(key)) for key in keys]
    registry = Registry(version="2", sources=entries)

    yaml_text = serialize_registry_yaml(_registry_to_dict(registry))
    raw = apply_migrations(parse_registry_yaml(yaml_text))
    # The generated sources are always schema-valid; mirror main's validation
    # step so the round-trip matches the real reader flow.
    assume(not validate_registry(raw))
    return _dict_to_registry(raw)


def st_module1_state():
    """Strategy over the three Module-1 license states.

    Returns:
        A strategy sampling ``DELIVERED``, ``DEFERRED``, and ``SKIPPED``.
    """
    return st.sampled_from(list(rcb.Module1GuidanceState))


@st.composite
def st_collected_count(draw):
    """Draw a synthetic, PII-free ``CollectedCount`` for a pure decision test.

    The ``known_total`` is chosen to span the interesting decision regions —
    below 500, exactly 500, and above 500 — so the exact-limit boundary is
    exercised. An optional non-empty ``unknown_sources`` list is attached so the
    indeterminate branch (count at or below the limit with unknowns remaining)
    is also covered. The per-source breakdown carries only source names and
    counts (never row content or PII); it is kept broadly consistent with
    ``known_total`` where cheap, but ``decide_backfill`` reads only
    ``known_total`` and ``unknown_sources`` (via ``is_complete`` /
    ``compare_to_limit``).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A :class:`record_count_backfill.CollectedCount` instance.
    """
    limit = rcb.EVALUATION_LIMIT
    known_total = draw(
        st.one_of(
            st.integers(min_value=0, max_value=limit - 1),  # below the limit
            st.just(limit),                                  # exactly the limit
            st.integers(min_value=limit + 1, max_value=limit + 5_000),  # above
        )
    )

    # Optionally attach one or more unknown sources (drives is_complete).
    unknown_sources = draw(
        st.lists(
            _st_safe_name(),
            min_size=0,
            max_size=3,
            unique=True,
        )
    )

    sources = []
    if known_total > 0:
        sources.append(
            rcb.SourceCount(name="KNOWN_SOURCE", count=known_total, counted_from="metadata")
        )
    for name in unknown_sources:
        sources.append(rcb.SourceCount(name=name, count=None, counted_from="unknown"))

    return rcb.CollectedCount(
        known_total=known_total,
        sources=sources,
        unknown_sources=unknown_sources,
    )


@st.composite
def st_framing_context(draw):
    """Draw a synthetic, PII-free ``LicenseFramingContext`` for Property 3.

    Spans the framing helper's input space: an optional non-negative capacity,
    an optional short safe validity string, and the in-flow / existing-license /
    downsizing booleans. Values are deliberately kept generic (no PII) since the
    render-equivalence property only cares that ``render_backfill_guidance``
    forwards the context verbatim to ``volume_utils.build_license_framing``.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A :class:`volume_utils.LicenseFramingContext` instance.
    """
    capacity = draw(st.one_of(st.none(), st.integers(min_value=0, max_value=10_000_000)))
    validity = draw(
        st.one_of(
            st.none(),
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("L", "N"),
                    whitelist_characters=" ",
                ),
                min_size=0,
                max_size=16,
            ),
        )
    )
    return volume_utils.LicenseFramingContext(
        capacity=capacity,
        validity=validity,
        submit_feedback_available=draw(st.booleans()),
        has_existing_license=draw(st.booleans()),
        mention_downsizing=draw(st.booleans()),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Property 1 — Collected_Count summing and unknown-tracking
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty1CollectedCount:
    """Feature: module4-record-count-license-backfill, Property 1.

    Collected_Count sums known counts and tracks unknowns without zeroing: for
    any registry of sources with non-negative-integer or ``null`` record counts,
    ``compute_collected_count`` returns a ``known_total`` equal to the sum of
    exactly the non-null counts and an ``unknown_sources`` list equal to exactly
    the null-count source names; no unknown source contributes to
    ``known_total``, and enabling row-count only ever moves a source from
    unknown to counted, never changing an already-known count.

    **Validates: Requirements 1.1, 1.2**
    """

    # Feature: module4-record-count-license-backfill, Property 1: Collected_Count
    # sums known counts and tracks unknowns without zeroing.
    @given(registry=st_registry())
    def test_sums_known_and_tracks_unknowns(self, registry):
        """known_total sums exactly the non-null counts; unknowns are tracked."""
        collected = rcb.compute_collected_count(registry)

        expected_known = sum(
            e.record_count for e in registry.sources if e.record_count is not None
        )
        expected_unknown = [
            e.name for e in registry.sources if e.record_count is None
        ]

        # known_total is exactly the sum of the non-null counts.
        assert collected.known_total == expected_known
        # unknown_sources is exactly the null-count source names (order-preserved).
        assert collected.unknown_sources == expected_unknown
        # No unknown source contributes to known_total: it is the sum over
        # only the resolved (non-None) per-source counts.
        resolved_sum = sum(
            sc.count for sc in collected.sources if sc.count is not None
        )
        assert collected.known_total == resolved_sum
        # Every unknown source is carried with count None and never zeroed.
        for sc in collected.sources:
            if sc.counted_from == "unknown":
                assert sc.count is None
                assert sc.name in collected.unknown_sources
            else:
                assert sc.counted_from == "metadata"
                assert sc.count is not None

    # Feature: module4-record-count-license-backfill, Property 1: Collected_Count
    # sums known counts and tracks unknowns without zeroing.
    @given(registry=st_registry())
    def test_row_count_only_moves_unknowns_never_changes_known(self, registry):
        """Enabling row-count never changes an already-known count.

        Row-count resolution may or may not resolve unknowns depending on
        whether the collected files exist (here they do not, since fixtures are
        synthetic), but it must never alter a source already counted from
        metadata, and the known total can only stay equal or grow.
        """
        default = rcb.compute_collected_count(registry)
        with_rows = rcb.compute_collected_count(registry, row_count=True)

        # Same sources, same order — compare position by position.
        assert len(default.sources) == len(with_rows.sources)

        for base, rowed in zip(default.sources, with_rows.sources):
            assert base.name == rowed.name
            if base.counted_from == "metadata":
                # An already-known count is never changed by row-counting.
                assert rowed.counted_from == "metadata"
                assert rowed.count == base.count
            else:
                # An unknown source either stays unknown or moves to counted;
                # it never regresses to metadata or a different name.
                assert base.counted_from == "unknown"
                assert rowed.counted_from in ("unknown", "row_count")
                if rowed.counted_from == "unknown":
                    assert rowed.count is None
                else:
                    assert rowed.count is not None and rowed.count >= 0

        # Row-counting can only leave unknowns the same or resolve them.
        assert set(with_rows.unknown_sources).issubset(set(default.unknown_sources))
        # The known total is monotonic under row-count resolution.
        assert with_rows.known_total >= default.known_total


# ═══════════════════════════════════════════════════════════════════════════
# Property 2 — present/suppress decision truth table
# ═══════════════════════════════════════════════════════════════════════════


class TestProperty2Decision:
    """Feature: module4-record-count-license-backfill, Property 2.

    The present/suppress decision matches the exact truth table: for any
    Collected_Count and any Module-1 license state, ``decide_backfill`` sets
    ``present_guidance`` true iff the count *certainly* exceeds the 500-record
    limit and the state is ``SKIPPED`` or ``DEFERRED``; it is false whenever the
    state is ``DELIVERED`` (already guided) and whenever the certain count is at
    or below the limit (including exactly 500).

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    # Feature: module4-record-count-license-backfill, Property 2: The present/
    # suppress decision matches the exact truth table.
    @given(collected=st_collected_count(), state=st_module1_state())
    def test_decision_matches_truth_table(self, collected, state):
        """present_guidance matches the independently-computed truth value."""
        limit = rcb.EVALUATION_LIMIT

        # Independently recompute the expected verdict from first principles.
        over_limit = collected.known_total > limit
        # Certain when already over (unknowns can only add) or no unknowns remain.
        certain = over_limit or (not collected.unknown_sources)
        expected_present = (
            over_limit
            and certain
            and state in (rcb.Module1GuidanceState.SKIPPED, rcb.Module1GuidanceState.DEFERRED)
        )

        decision = rcb.decide_backfill(collected, state)

        # Core truth-table equivalence (computable defaults to True).
        assert decision.present_guidance == expected_present
        # already_guided is exactly the DELIVERED state (Req 2.2).
        assert decision.already_guided == (state is rcb.Module1GuidanceState.DELIVERED)
        # Never present when Module 1 already delivered guidance (Req 2.2).
        if state is rcb.Module1GuidanceState.DELIVERED:
            assert decision.present_guidance is False
        # Never present at or below the limit, including exactly 500 (Req 2.3).
        if collected.known_total <= limit:
            assert decision.present_guidance is False

    # ---- Explicit boundary / example tests (not property-based) ----

    @staticmethod
    def _collected(known_total, unknown_sources=None):
        """Build a PII-free CollectedCount for the example tests."""
        unknown_sources = unknown_sources or []
        sources = []
        if known_total > 0:
            sources.append(
                rcb.SourceCount(name="KNOWN_SOURCE", count=known_total, counted_from="metadata")
            )
        for name in unknown_sources:
            sources.append(rcb.SourceCount(name=name, count=None, counted_from="unknown"))
        return rcb.CollectedCount(
            known_total=known_total,
            sources=sources,
            unknown_sources=unknown_sources,
        )

    def test_exactly_at_limit_is_not_present(self):
        """Exactly 500 records is at the limit, not over it -> suppress (Req 2.3)."""
        collected = self._collected(rcb.EVALUATION_LIMIT)
        decision = rcb.decide_backfill(collected, rcb.Module1GuidanceState.SKIPPED)
        assert decision.over_limit is False
        assert decision.present_guidance is False

    def test_over_limit_and_skipped_is_present(self):
        """501 records with SKIPPED state -> present the existing guidance (Req 2.1)."""
        collected = self._collected(rcb.EVALUATION_LIMIT + 1)
        decision = rcb.decide_backfill(collected, rcb.Module1GuidanceState.SKIPPED)
        assert decision.over_limit is True
        assert decision.certain is True
        assert decision.present_guidance is True

    def test_over_limit_but_delivered_short_circuits(self):
        """501 records with DELIVERED state -> suppressed and already_guided (Req 2.2)."""
        collected = self._collected(rcb.EVALUATION_LIMIT + 1)
        decision = rcb.decide_backfill(collected, rcb.Module1GuidanceState.DELIVERED)
        assert decision.already_guided is True
        assert decision.present_guidance is False

    def test_below_limit_with_unknowns_is_indeterminate(self):
        """Below 500 with unknown sources is indeterminate -> suppress (Req 2.1, 2.3)."""
        collected = self._collected(100, unknown_sources=["PENDING_SOURCE"])
        decision = rcb.decide_backfill(collected, rcb.Module1GuidanceState.SKIPPED)
        assert decision.over_limit is False
        assert decision.certain is False
        assert decision.present_guidance is False


# ═══════════════════════════════════════════════════════════════════════════
# Property 3 — rendered guidance is exactly the reused canonical framing
# ═══════════════════════════════════════════════════════════════════════════


def _present_decision():
    """Build a real present-guidance decision via decide_backfill.

    An over-limit collected count (501, fully known) combined with the SKIPPED
    Module-1 state yields ``present_guidance=True`` through the real decision
    logic (no hand-set BackfillDecision), keeping the test faithful to how the
    helper is actually driven.

    Returns:
        A :class:`record_count_backfill.BackfillDecision` with
        ``present_guidance`` True.
    """
    collected = rcb.CollectedCount(
        known_total=rcb.EVALUATION_LIMIT + 1,
        sources=[
            rcb.SourceCount(
                name="KNOWN_SOURCE",
                count=rcb.EVALUATION_LIMIT + 1,
                counted_from="metadata",
            )
        ],
        unknown_sources=[],
    )
    decision = rcb.decide_backfill(collected, rcb.Module1GuidanceState.SKIPPED)
    assert decision.present_guidance is True
    return decision


def _suppressed_decision():
    """Build a real suppress-guidance decision via decide_backfill.

    An under-limit collected count with the SKIPPED state yields
    ``present_guidance=False`` through the real decision logic.

    Returns:
        A :class:`record_count_backfill.BackfillDecision` with
        ``present_guidance`` False.
    """
    collected = rcb.CollectedCount(
        known_total=rcb.EVALUATION_LIMIT - 1,
        sources=[
            rcb.SourceCount(
                name="KNOWN_SOURCE",
                count=rcb.EVALUATION_LIMIT - 1,
                counted_from="metadata",
            )
        ],
        unknown_sources=[],
    )
    decision = rcb.decide_backfill(collected, rcb.Module1GuidanceState.SKIPPED)
    assert decision.present_guidance is False
    return decision


class TestProperty3RenderEquivalence:
    """Feature: module4-record-count-license-backfill, Property 3.

    Rendered guidance is exactly the reused canonical framing: for any
    ``LicenseFramingContext`` and a decision with ``present_guidance`` true,
    ``render_backfill_guidance`` returns a string identical to
    ``volume_utils.build_license_framing`` called with the same context, and
    returns ``None`` when ``present_guidance`` is false — so the Module 4
    guidance text is the existing Steps 6b-6e framing verbatim, never a parallel
    re-authored flow.

    **Validates: Requirements 3.1, 3.2**
    """

    # Feature: module4-record-count-license-backfill, Property 3: Rendered
    # guidance is exactly the reused canonical framing.
    @given(ctx=st_framing_context())
    def test_present_guidance_renders_canonical_framing_verbatim(self, ctx):
        """A present decision renders exactly build_license_framing(ctx)."""
        decision = _present_decision()

        rendered = rcb.render_backfill_guidance(decision, ctx)
        expected = volume_utils.build_license_framing(
            capacity=ctx.capacity,
            validity=ctx.validity,
            submit_feedback_available=ctx.submit_feedback_available,
            has_existing_license=ctx.has_existing_license,
            mention_downsizing=ctx.mention_downsizing,
        )

        # The rendered guidance is the canonical framing verbatim — no new text.
        assert rendered == expected

    # Feature: module4-record-count-license-backfill, Property 3: Rendered
    # guidance is exactly the reused canonical framing.
    @given(ctx=st_framing_context())
    def test_suppressed_guidance_returns_none(self, ctx):
        """A suppress decision renders no guidance regardless of context."""
        decision = _suppressed_decision()
        assert rcb.render_backfill_guidance(decision, ctx) is None


# ═══════════════════════════════════════════════════════════════════════════
# Property 4 — marker updates are idempotent and use the Module 1 markers
# ═══════════════════════════════════════════════════════════════════════════


@st.composite
def st_preferences_state(draw):
    """Draw a synthetic, PII-free, schema-valid starting preferences dict.

    Always includes the only required key (``database_type``) and optionally
    seeds other valid known keys plus, with some probability, the existing
    ``license_guidance_deferred`` and ``license`` license markers — so the
    idempotence property is exercised both when the deferral marker is present
    (and must be cleared) and when it is absent (and must stay absent). Values
    are generic and PII-free; only known top-level keys are ever produced so
    the seeded file is schema-valid.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A preferences dict whose keys are a subset of
        ``preferences_utils.KNOWN_TOP_LEVEL_KEYS``.
    """
    prefs: dict = {
        "database_type": draw(st.sampled_from(["sqlite", "postgresql", "custom_db"]))
    }
    if draw(st.booleans()):
        prefs["language"] = draw(
            st.sampled_from(["python", "java", "rust", "typescript", "csharp"])
        )
    if draw(st.booleans()):
        prefs["track"] = draw(st.sampled_from(["core_bootcamp", "advanced_topics"]))
    if draw(st.booleans()):
        prefs["verbosity"] = draw(st.sampled_from(["concise", "standard", "detailed"]))
    if draw(st.booleans()):
        # The existing Module 1 deferral marker -> must be cleared by the helper.
        prefs["license_guidance_deferred"] = True
    if draw(st.booleans()):
        # An already-applied license marker -> must be left untouched.
        prefs["license"] = draw(st.sampled_from(["custom", "standard"]))
    return prefs


@st.composite
def st_present_decision(draw):
    """Draw a real present-guidance ``BackfillDecision`` via ``decide_backfill``.

    An over-limit, fully-known Collected_Count combined with a ``SKIPPED`` or
    ``DEFERRED`` Module-1 state yields ``present_guidance=True`` through the real
    decision logic (never a hand-built decision), so ``apply_guidance_markers``
    is driven exactly as it is in production. The per-source breakdown carries
    only a synthetic source name and its count (no PII).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A :class:`record_count_backfill.BackfillDecision` with
        ``present_guidance`` True.
    """
    known_total = draw(
        st.integers(
            min_value=rcb.EVALUATION_LIMIT + 1,
            max_value=rcb.EVALUATION_LIMIT + 5_000,
        )
    )
    state = draw(
        st.sampled_from(
            [rcb.Module1GuidanceState.SKIPPED, rcb.Module1GuidanceState.DEFERRED]
        )
    )
    collected = rcb.CollectedCount(
        known_total=known_total,
        sources=[
            rcb.SourceCount(
                name="KNOWN_SOURCE", count=known_total, counted_from="metadata"
            )
        ],
        unknown_sources=[],
    )
    decision = rcb.decide_backfill(collected, state)
    return decision


def _seed_progress_file(progress_path: str, database_type: str) -> None:
    """Write a minimal, schema-valid starting ``bootcamp_progress.json``.

    Args:
        progress_path: Where to write the seeded progress file.
        database_type: A synthetic database type value for the seed.
    """
    seed = {
        "current_module": 4,
        "modules_completed": [1, 2, 3],
        "data_sources": [],
        "database_type": database_type,
    }
    Path(progress_path).write_text(json.dumps(seed, indent=2) + "\n", encoding="utf-8")


class TestProperty4MarkerIdempotence:
    """Feature: module4-record-count-license-backfill, Property 4.

    Marker updates are idempotent and use the Module 1 markers: for any starting
    ``bootcamp_preferences.yaml`` state and a present-guidance decision, running
    ``apply_guidance_markers`` twice leaves the preferences and progress files
    byte-identical to their post-first-run state and sets only the existing
    ``license`` / ``license_guidance_deferred`` markers the Module 1 flow uses
    (introducing no new marker key), so downstream modules observe a consistent
    state.

    **Validates: Requirements 3.3**
    """

    # Feature: module4-record-count-license-backfill, Property 4: Marker updates
    # are idempotent and use the Module 1 markers.
    @given(
        prefs=st_preferences_state(),
        decision=st_present_decision(),
        seed_progress=st.booleans(),
    )
    def test_marker_updates_are_idempotent(self, prefs, decision, seed_progress):
        """A second apply_guidance_markers leaves both files byte-identical.

        Each generated example runs inside its own fresh temp workspace so
        Hypothesis examples never bleed state into one another. The starting
        preferences file is seeded through the canonical
        ``preferences_utils.write_preference`` writer; the progress file is
        optionally seeded. After the first apply the files are snapshotted, and
        after the second apply they must be byte-for-byte identical — and the
        resulting preferences must reference only the two Module 1 license
        markers, with the deferral marker cleared.
        """
        # Sanity: the decision genuinely presents guidance (setup precondition).
        assert decision.present_guidance is True

        with tempfile.TemporaryDirectory() as tmp:
            prefs_path = os.path.join(tmp, "bootcamp_preferences.yaml")
            progress_path = os.path.join(tmp, "bootcamp_progress.json")

            # Seed the starting preferences via the canonical writer.
            for key, value in prefs.items():
                result = preferences_utils.write_preference(
                    key, value, preferences_path=prefs_path
                )
                assert result.success, result.error

            if seed_progress:
                _seed_progress_file(progress_path, prefs["database_type"])

            # ---- First run: capture the post-first-run byte snapshots. ----
            rcb.apply_guidance_markers(
                decision,
                preferences_path=prefs_path,
                progress_path=progress_path,
                step_number=8,
            )
            prefs_after_first = Path(prefs_path).read_bytes()
            progress_after_first = Path(progress_path).read_bytes()

            # ---- Second run: must be a byte-identical no-op. ----
            rcb.apply_guidance_markers(
                decision,
                preferences_path=prefs_path,
                progress_path=progress_path,
                step_number=8,
            )
            prefs_after_second = Path(prefs_path).read_bytes()
            progress_after_second = Path(progress_path).read_bytes()

            # Idempotence: both files are unchanged by the second call.
            assert prefs_after_second == prefs_after_first
            assert progress_after_second == progress_after_first

            # The resulting preferences reference only known top-level keys —
            # no bespoke/new marker key was introduced.
            parsed = preferences_utils.parse_yaml(
                prefs_after_first.decode("utf-8")
            )
            assert set(parsed.keys()) <= set(preferences_utils.KNOWN_TOP_LEVEL_KEYS)

            # The only license-related markers touched are the two Module 1
            # markers; the deferral marker is cleared (absent) after guidance.
            license_markers = set(parsed.keys()) & {
                "license",
                "license_guidance_deferred",
            }
            assert license_markers <= {"license", "license_guidance_deferred"}
            assert "license_guidance_deferred" not in parsed

            # A checkpoint for the Module 4 back-fill step was recorded.
            progress = json.loads(progress_after_first.decode("utf-8"))
            assert progress.get("current_step") == "8a"


# ═══════════════════════════════════════════════════════════════════════════
# Structural guardrails (example/source-inspection tests, NOT property-based)
# ═══════════════════════════════════════════════════════════════════════════

# Paths to the artifacts under structural inspection.
_BACKFILL_SCRIPT_PATH = Path(_SCRIPTS_DIR) / "record_count_backfill.py"
_MODULE4_STEERING_PATH = (
    Path(__file__).resolve().parent.parent / "steering" / "module-04-data-collection.md"
)

# The only license-related preference markers Module 1 uses. The back-fill must
# reuse these and introduce no new bespoke preference key (Requirement 3.1, 3.3).
_ALLOWED_LICENSE_MARKERS = {"license", "license_guidance_deferred"}


def _string_literals(source: str) -> set[str]:
    """Return every string-constant literal in a Python source string.

    Parses the source with :mod:`ast` and collects the values of all string
    constants, so assertions can reason about exactly which key names the
    module references (rather than substring-matching prose).

    Args:
        source: Python source text to parse.

    Returns:
        The set of distinct string-constant values found in the source.
    """
    tree = ast.parse(source)
    literals: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            literals.add(node.value)
    return literals


class TestStructuralGuardrails:
    """Structural guardrails for the reuse contract (example tests, not PBT).

    These assert the back-fill reuses the *existing* license plumbing rather
    than defining a parallel flow: it introduces no new preference key beyond
    the Module 1 ``license`` / ``license_guidance_deferred`` markers, it renders
    guidance through the canonical ``volume_utils.build_license_framing`` (no
    duplicated license text), and the Module 4 steering wires Step 8a to invoke
    ``record_count_backfill.py`` after collection and before the Module 5
    transition.

    **Validates: Requirements 3.1, 3.3**
    """

    def test_introduces_no_new_preference_key(self):
        """The helper references only the two Module 1 license markers (Req 3.1, 3.3).

        Reads the back-fill source, extracts every string literal, and asserts
        that the only literals which name a *known preference key* are the two
        markers Module 1 already uses — so no bespoke preference key is written
        to preferences. Also asserts against the authoritative
        ``preferences_utils.KNOWN_TOP_LEVEL_KEYS`` set.
        """
        source = _BACKFILL_SCRIPT_PATH.read_text(encoding="utf-8")
        literals = _string_literals(source)

        # The helper must reference the two markers it reuses.
        assert "license" in literals
        assert "license_guidance_deferred" in literals

        # Any literal that names a known preference key must be one of the two
        # allowed license markers — no other preference key is touched.
        known_keys = set(preferences_utils.KNOWN_TOP_LEVEL_KEYS)
        preference_key_literals = literals & known_keys
        assert preference_key_literals <= _ALLOWED_LICENSE_MARKERS, (
            "record_count_backfill.py references preference keys beyond the two "
            "Module 1 license markers: "
            f"{sorted(preference_key_literals - _ALLOWED_LICENSE_MARKERS)}"
        )

        # Guard against a new bespoke deferral/guidance marker key: any literal
        # that looks like a license/guidance marker key must be an allowed one.
        marker_like = {
            lit
            for lit in literals
            if re.fullmatch(r"[a-z][a-z0-9_]*", lit)
            and ("guidance_deferred" in lit or lit.startswith("license"))
        }
        assert marker_like <= _ALLOWED_LICENSE_MARKERS, (
            "record_count_backfill.py defines a new license/guidance marker key: "
            f"{sorted(marker_like - _ALLOWED_LICENSE_MARKERS)}"
        )

    def test_renders_through_build_license_framing_no_duplicated_text(self):
        """Guidance is rendered through the canonical framing, not re-authored (Req 3.1, 3.2).

        Structural guardrail via source inspection (robust regardless of task
        ordering): the back-fill delegates the *wording* to
        ``volume_utils.build_license_framing`` and does not embed a duplicated
        copy of the canonical license framing text. When
        ``render_backfill_guidance`` exists (implemented by task 6.1), its own
        source is asserted to call the canonical builder; until then, the module
        must at minimum import the framing plumbing it delegates to.
        """
        source = _BACKFILL_SCRIPT_PATH.read_text(encoding="utf-8")

        # The plumbing it delegates to must be wired in (imported), never a
        # parallel re-implementation.
        assert "volume_utils" in source

        # The canonical framing text must NOT be duplicated (hardcoded) here.
        # Sample the real builder output and assert its distinctive phrases do
        # not appear verbatim in the back-fill source.
        canonical = volume_utils.build_license_framing()
        distinctive_phrases = [
            "built-in evaluation license that you already have by default",
            "you have options to process more records",
            "just one choice alongside the",
        ]
        for phrase in distinctive_phrases:
            assert phrase in canonical, (
                f"test fixture phrase drifted from build_license_framing: {phrase!r}"
            )
            assert phrase not in source, (
                "record_count_backfill.py duplicates canonical license framing "
                f"text instead of delegating to build_license_framing: {phrase!r}"
            )

        # Once render_backfill_guidance lands (task 6.1), it must delegate to
        # the canonical builder rather than re-author the wording.
        render = getattr(rcb, "render_backfill_guidance", None)
        if render is not None:
            render_source = inspect.getsource(render)
            assert "build_license_framing" in render_source, (
                "render_backfill_guidance must delegate to "
                "volume_utils.build_license_framing"
            )
            for phrase in distinctive_phrases:
                assert phrase not in render_source, (
                    "render_backfill_guidance embeds duplicated license framing "
                    f"text instead of delegating: {phrase!r}"
                )

    def test_step_8a_wires_backfill_after_step8_before_module5(self):
        """Module 4 Step 8a invokes the back-fill after collection, before Module 5 (Req 3.3).

        Reads ``module-04-data-collection.md`` and asserts a Step 8a exists that
        invokes ``record_count_backfill.py``, positioned after the Step 8
        data-source-tracking content and before the Step 9 transition to
        Module 5. Ordering is verified by string index.
        """
        doc = _MODULE4_STEERING_PATH.read_text(encoding="utf-8")

        # A Step 8a exists and invokes the back-fill script.
        assert "8a." in doc
        assert "record_count_backfill.py" in doc

        step8_idx = doc.find("8. **Update data source tracking**")
        backfill_idx = doc.find("record_count_backfill.py")
        step9_idx = doc.find("9. **Transition to Module 5**")

        # All three anchors are present.
        assert step8_idx != -1, "Step 8 (Update data source tracking) not found"
        assert backfill_idx != -1, "record_count_backfill.py invocation not found"
        assert step9_idx != -1, "Step 9 (Transition to Module 5) not found"

        # The back-fill invocation sits strictly between Step 8 and Step 9.
        assert step8_idx < backfill_idx < step9_idx, (
            "Step 8a record_count_backfill.py invocation must appear after Step 8 "
            "and before the Step 9 Module 5 transition"
        )


# ═══════════════════════════════════════════════════════════════════════════
# Property 5 — non-blocking fallback on missing/unreadable/malformed input
# ═══════════════════════════════════════════════════════════════════════════


@st.composite
def st_malformed_input(draw):
    """Draw a scenario describing a bad registry input for the fallback property.

    Each scenario is a ``(registry_content, description)`` tuple where
    ``registry_content`` is either ``None`` — meaning *do not create the
    registry file* so ``--registry`` points at a non-existent path (absent) — or
    a string to write verbatim to the registry file. Three non-overlapping
    families of bad input are covered so ``main`` must fall back on every one:

    1. **Absent file**: ``None`` — the registry path does not exist (unreadable).
    2. **Invalid YAML**: garbage / non-structured text that does not yield a
       valid registry (no ``version`` + ``sources`` structure), so the
       parse/validate chain rejects it.
    3. **Schema-invalid registry**: text that *parses* as the restricted YAML
       subset but violates the registry schema — a wrong ``version``, a missing
       required top-level field, an invalid (lower-case) DATA_SOURCE key, or an
       entry missing its required fields — so it reaches the
       ``validate_registry`` error path inside ``_compute_decision``.

    All content is synthetic and PII-free (only fixed keywords and generic
    tokens are emitted).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(registry_content_or_None, description)`` tuple.
    """
    kind = draw(st.sampled_from(["absent", "invalid_yaml", "schema_invalid"]))

    if kind == "absent":
        return (None, "absent registry file")

    if kind == "invalid_yaml":
        # Non-structured garbage: punctuation-led tokens that never form the
        # required version+sources registry structure, so the parse/validate
        # chain rejects the input.
        garbage = draw(
            st.lists(
                st.text(
                    alphabet="!@#%^&*()<>?/\\|~`.,;[]{}=+- \tabcXYZ0129",
                    min_size=1,
                    max_size=30,
                ),
                min_size=1,
                max_size=5,
            ).map(lambda parts: "\n".join(parts))
        )
        # Guard against the astronomically unlikely case of garbage that happens
        # to declare the registry structure; keep the input firmly invalid.
        assume("version" not in garbage and "sources" not in garbage)
        return (garbage, "invalid YAML content")

    # schema_invalid — parses as the restricted YAML subset but fails
    # validate_registry, so it reaches the validation error path.
    content = draw(
        st.sampled_from(
            [
                # Missing required top-level 'version'.
                "sources:\n  CUSTOMER:\n    name: Customer\n",
                # Wrong schema version.
                'version: "99"\nsources:\n  CUSTOMER:\n    name: Customer\n',
                # Missing required top-level 'sources'.
                'version: "2"\n',
                # Invalid (lower-case) DATA_SOURCE key.
                'version: "2"\nsources:\n  lowercasekey:\n    name: Customer\n',
                # Valid key but entry missing its required fields.
                'version: "2"\nsources:\n  CUSTOMER:\n    name: Customer\n',
            ]
        )
    )
    return (content, "schema-invalid registry")


class TestProperty5NonBlockingFallback:
    """Feature: module4-record-count-license-backfill, Property 5.

    Uncomputable or malformed input warns and continues (non-blocking): for any
    missing, unreadable, or malformed registry or preferences input (absent
    files, invalid YAML, schema-invalid registries), ``record_count_backfill.main``
    never raises, returns exit code 0, and emits a decision with ``computable``
    false — so Module 4 falls back to the existing Prose_Count behavior rather
    than blocking.

    **Validates: Requirements 4.1**
    """

    # Feature: module4-record-count-license-backfill, Property 5: Uncomputable or
    # malformed input warns and continues (non-blocking).
    @given(scenario=st_malformed_input(), write_prefs=st.sampled_from(["none", "garbage"]))
    def test_bad_input_never_raises_and_emits_computable_false(self, scenario, write_prefs):
        """main() returns 0, never raises, and emits computable=false.

        Each example is materialized in its own fresh temp workspace so
        Hypothesis examples never bleed state. When the scenario provides
        registry content it is written to the registry path; otherwise the path
        is left non-existent (absent). Preferences are independently omitted or
        seeded with garbage — neither of which may make ``main`` raise — and
        because the registry is always bad, the decision is always
        ``computable=false`` regardless of the preferences input.
        """
        registry_content, _description = scenario

        with tempfile.TemporaryDirectory() as tmp:
            registry_path = os.path.join(tmp, "data_sources.yaml")
            prefs_path = os.path.join(tmp, "bootcamp_preferences.yaml")

            # Materialize the registry scenario: write it, or leave the path
            # non-existent for the absent case.
            if registry_content is not None:
                Path(registry_path).write_text(registry_content, encoding="utf-8")

            # Independently vary the preferences input; neither variant is
            # allowed to make main() raise.
            if write_prefs == "garbage":
                Path(prefs_path).write_text(":\n\t- not: [valid", encoding="utf-8")
            # else: leave prefs_path non-existent (omitted).

            stdout = io.StringIO()
            try:
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(
                    io.StringIO()
                ):
                    exit_code = rcb.main(
                        ["--registry", registry_path, "--preferences", prefs_path]
                    )
            except Exception as exc:  # noqa: BLE001 - the property is "never raises"
                raise AssertionError(
                    f"main() raised on bad input ({_description}): {exc!r}"
                ) from exc

            # Non-blocking contract: exit code is always 0.
            assert exit_code == 0

            # The emitted stdout is valid JSON with computable=false.
            payload = json.loads(stdout.getvalue())
            assert payload["computable"] is False


# ═══════════════════════════════════════════════════════════════════════════
# Property 6 — only counts and source names leave the helper (no PII)
# ═══════════════════════════════════════════════════════════════════════════

# Distinctive sentinel integers seeded into numeric fields the helper never
# surfaces. They are far larger than any generated record_count (<= 5_000) or
# their sum, so their string forms cannot collide with an emitted count/total.
_SENTINEL_FILE_SIZE_BYTES = 900_000_001
_SENTINEL_QUALITY_SCORE = 900_000_002


def _st_sentinel_token():
    """Strategy producing a distinctive, PII-simulating sentinel string.

    The token is prefixed with ``SENTINEL-PII-`` and suffixed with random hex.
    The literal ``-`` guarantees the token can never be a substring of a
    generated source name (names draw only from letters/underscore/space), of
    the fixed guidance/reason text, of the ``counted_from`` tokens, or of any
    emitted number — so if it ever appears in the output, that is a genuine leak.

    Returns:
        A strategy over sentinel strings like ``SENTINEL-PII-a1b2c3d4``.
    """
    return st.text(alphabet="0123456789abcdef", min_size=8, max_size=16).map(
        lambda suffix: f"SENTINEL-PII-{suffix}"
    )


def _st_letters_only_name():
    """Strategy producing PII-free source names with no digits and no hyphens.

    Names are legitimately surfaced by the helper, so they must never collide
    with a sentinel value. Restricting the alphabet to letters (plus space and
    underscore) — no digits, no ``-`` — makes it impossible for a surfaced name
    to contain either the all-digit integer sentinels or the hyphenated string
    sentinel, keeping the leak assertions free of false positives.

    Returns:
        A strategy over safe, digit-free, hyphen-free source names.
    """
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L",),
            whitelist_characters=" _",
        ),
        min_size=1,
        max_size=24,
    ).filter(lambda s: s.strip() != "")


def _st_registry_entry_with_sentinels(key, sentinel_token):
    """Strategy: a schema-valid RegistryEntry seeded with sentinels.

    Mirrors :func:`_st_registry_entry` but embeds sentinel values into fields
    the helper does *not* surface — ``file_path``, ``issues``, ``updated_at``
    (string sentinels), and ``file_size_bytes`` / ``quality_score`` (integer
    sentinels) — while keeping the surfaced fields sentinel-free: ``name`` is a
    legitimately surfaced, digit/hyphen-free safe name, and ``record_count`` is
    a small non-negative integer or ``null``. Every seeded value is schema-valid
    (``file_path`` is an arbitrary path-like string, ``issues`` is a list of
    strings, the numeric fields are unvalidated integers), so the entry
    round-trips cleanly through ``parse_registry_yaml`` / ``validate_registry``.

    Args:
        key: The fixed DATA_SOURCE key for this entry.
        sentinel_token: The string sentinel to embed into non-surfaced fields.

    Returns:
        A strategy producing a sentinel-seeded :class:`RegistryEntry`.
    """
    return st.builds(
        RegistryEntry,
        data_source=st.just(key),
        # Surfaced field — must stay sentinel-free (no digits, no hyphen).
        name=_st_letters_only_name(),
        # Non-surfaced: the row-content file path carries the sentinel.
        file_path=st.just(f"data/raw/{sentinel_token}.csv"),
        format=st.sampled_from(sorted(VALID_FORMATS)),
        # Surfaced field — a real, small count (or unknown), never a sentinel.
        record_count=st.one_of(st.none(), st.integers(min_value=0, max_value=5_000)),
        # Non-surfaced numeric field carrying a distinctive integer sentinel.
        file_size_bytes=st.just(_SENTINEL_FILE_SIZE_BYTES),
        # Non-surfaced numeric field carrying a distinctive integer sentinel.
        quality_score=st.just(_SENTINEL_QUALITY_SCORE),
        mapping_status=st.just("pending"),
        load_status=st.just("not_loaded"),
        added_at=st.just("2025-01-01T00:00:00Z"),
        # Non-surfaced timestamp string carrying the sentinel.
        updated_at=st.just(sentinel_token),
        test_load_status=st.none(),
        test_entity_count=st.none(),
        # Non-surfaced issues list carrying the sentinel.
        issues=st.just([sentinel_token]),
    )


@st.composite
def st_registry_with_sentinels(draw, min_sources=1, max_sources=6):
    """Draw a sentinel-seeded registry variant of :func:`st_registry`.

    Builds a registry whose every entry embeds a batch of sentinel values in the
    fields the helper never reads (``file_path``, ``issues``, ``updated_at``,
    ``file_size_bytes``, ``quality_score``), serializes it to the restricted
    registry YAML, and round-trips it through the real
    ``parse_registry_yaml`` + ``apply_migrations`` + ``validate_registry`` +
    ``_dict_to_registry`` chain (mirroring how ``main`` reads it). At least one
    source is always present so a sentinel is always in play. Returns the parsed
    registry, the serialized YAML text (the exact bytes written for ``main`` to
    read), and the set of seeded sentinel values to assert absence of.

    Args:
        draw: The Hypothesis draw callable.
        min_sources: Minimum number of sources to generate (>= 1).
        max_sources: Maximum number of sources to generate.

    Returns:
        A ``(registry, yaml_text, sentinel_values)`` tuple.
    """
    sentinel_token = draw(_st_sentinel_token())

    keys = draw(
        st.lists(
            _st_data_source_keys(),
            min_size=max(1, min_sources),
            max_size=max_sources,
            unique=True,
        )
    )
    entries = [
        draw(_st_registry_entry_with_sentinels(key, sentinel_token)) for key in keys
    ]
    registry = Registry(version="2", sources=entries)

    yaml_text = serialize_registry_yaml(_registry_to_dict(registry))
    raw = apply_migrations(parse_registry_yaml(yaml_text))
    # The generated sources are always schema-valid; mirror main's validation
    # step so the round-trip matches the real reader flow.
    assume(not validate_registry(raw))
    parsed = _dict_to_registry(raw)

    sentinel_values = {
        sentinel_token,
        str(_SENTINEL_FILE_SIZE_BYTES),
        str(_SENTINEL_QUALITY_SCORE),
    }
    return parsed, yaml_text, sentinel_values


class TestProperty6NoPII:
    """Feature: module4-record-count-license-backfill, Property 6.

    Only counts and source names leave the helper (no PII): for any registry
    whose entries embed arbitrary sentinel values in fields the helper does not
    read (row-content / non-count / non-name fields), the emitted
    ``BackfillDecision`` JSON and the preference/progress markers contain only
    source names, counts, and fixed guidance text — never any sentinel value —
    confirming that no PII is surfaced or persisted.

    **Validates: Requirements 4.2**
    """

    # Feature: module4-record-count-license-backfill, Property 6: Only counts and
    # source names leave the helper (no PII).
    @given(seeded=st_registry_with_sentinels())
    def test_no_sentinel_in_emitted_json(self, seeded):
        """main()'s emitted JSON never contains a seeded sentinel value.

        Each example runs in its own fresh temp workspace. The sentinel-seeded
        registry YAML is written verbatim (so ``main`` reads exactly the bytes
        that carry the sentinels), ``main`` is run capturing stdout, and no
        seeded sentinel — the hyphenated string sentinel or either integer
        sentinel — may appear anywhere in the emitted JSON. The decision is
        genuinely ``computable`` (the registry is schema-valid), so real source
        names and counts are surfaced while the non-surfaced sentinels are not.
        """
        registry, yaml_text, sentinel_values = seeded

        # Sanity: the sentinels really are present in the registry input, so a
        # clean output is a genuine no-leak result rather than a vacuous pass.
        for sentinel in sentinel_values:
            assert sentinel in yaml_text, (
                f"test setup error: sentinel {sentinel!r} was not seeded into the "
                "registry YAML"
            )

        with tempfile.TemporaryDirectory() as tmp:
            registry_path = os.path.join(tmp, "data_sources.yaml")
            prefs_path = os.path.join(tmp, "bootcamp_preferences.yaml")
            Path(registry_path).write_text(yaml_text, encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(
                io.StringIO()
            ):
                exit_code = rcb.main(
                    ["--registry", registry_path, "--preferences", prefs_path]
                )

            assert exit_code == 0
            out = stdout.getvalue()

            # The registry is valid, so the helper computes a real decision and
            # surfaces real source names/counts (the meaningful, PII-free output).
            payload = json.loads(out)
            assert payload["computable"] is True

            # No seeded sentinel value leaks into the emitted JSON anywhere.
            for sentinel in sentinel_values:
                assert sentinel not in out, (
                    f"sentinel {sentinel!r} leaked into the emitted BackfillDecision "
                    f"JSON: {out!r}"
                )

    # Feature: module4-record-count-license-backfill, Property 6: Only counts and
    # source names leave the helper (no PII).
    @given(seeded=st_registry_with_sentinels(), seed_deferral=st.booleans())
    def test_no_sentinel_in_preference_and_progress_markers(self, seeded, seed_deferral):
        """apply_guidance_markers writes no seeded sentinel to the marker files.

        Drives the present-guidance marker path with a decision derived from the
        sentinel-seeded registry's Collected_Count (real source names/counts,
        pushed over the limit so guidance is presented), then reads the updated
        preferences and progress files back and asserts that neither contains a
        seeded sentinel — only the fixed Module 1 markers, the step checkpoint,
        and clean seeded values ever reach the tracked artifacts.
        """
        registry, _yaml_text, sentinel_values = seeded

        # Build a real present-guidance decision from the registry's collected
        # count, forced over the limit so decide_backfill presents guidance.
        base = rcb.compute_collected_count(registry)
        collected = rcb.CollectedCount(
            known_total=rcb.EVALUATION_LIMIT + 1 + base.known_total,
            sources=base.sources,
            unknown_sources=base.unknown_sources,
        )
        decision = rcb.decide_backfill(collected, rcb.Module1GuidanceState.SKIPPED)
        assert decision.present_guidance is True

        with tempfile.TemporaryDirectory() as tmp:
            prefs_path = os.path.join(tmp, "bootcamp_preferences.yaml")
            progress_path = os.path.join(tmp, "bootcamp_progress.json")

            # Seed clean, PII-free starting preferences via the canonical writer.
            result = preferences_utils.write_preference(
                "database_type", "sqlite", preferences_path=prefs_path
            )
            assert result.success, result.error
            if seed_deferral:
                result = preferences_utils.write_preference(
                    "license_guidance_deferred", True, preferences_path=prefs_path
                )
                assert result.success, result.error
            _seed_progress_file(progress_path, "sqlite")

            with contextlib.redirect_stderr(io.StringIO()):
                rcb.apply_guidance_markers(
                    decision,
                    preferences_path=prefs_path,
                    progress_path=progress_path,
                    step_number=8,
                )

            prefs_text = Path(prefs_path).read_text(encoding="utf-8")
            progress_text = Path(progress_path).read_text(encoding="utf-8")

            for sentinel in sentinel_values:
                assert sentinel not in prefs_text, (
                    f"sentinel {sentinel!r} leaked into the preferences markers: "
                    f"{prefs_text!r}"
                )
                assert sentinel not in progress_text, (
                    f"sentinel {sentinel!r} leaked into the progress markers: "
                    f"{progress_text!r}"
                )


# ═══════════════════════════════════════════════════════════════════════════
# Named scenario unit / example tests (Requirement 5.1) — NOT property-based
# ═══════════════════════════════════════════════════════════════════════════


def _named_entry(
    data_source: str,
    record_count: int | None,
    *,
    file_path: str | None = None,
    fmt: str = "csv",
    name: str | None = None,
) -> RegistryEntry:
    """Build a synthetic, PII-free RegistryEntry for the named-scenario tests.

    Args:
        data_source: The DATA_SOURCE key (upper-case identifier).
        record_count: The per-source record count, or ``None`` for unknown.
        file_path: Optional explicit file path (defaults to a synthetic path).
        fmt: The source format (defaults to ``csv``).
        name: Optional display name (defaults to a title-cased key).

    Returns:
        A fully-populated :class:`RegistryEntry`.
    """
    return RegistryEntry(
        data_source=data_source,
        name=name or data_source.replace("_", " ").title(),
        file_path=file_path or f"data/raw/{data_source.lower()}.csv",
        format=fmt,
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


def _write_named_registry(path: str, entries: list[RegistryEntry]) -> None:
    """Serialize a registry of entries to the restricted YAML at ``path``.

    Reuses the canonical ``_registry_to_dict`` + ``serialize_registry_yaml``
    helpers so the written file round-trips cleanly through the reader chain
    ``main`` uses.

    Args:
        path: Destination path for the ``data_sources.yaml`` file.
        entries: The registry entries to serialize.
    """
    registry = Registry(version="2", sources=entries)
    yaml_text = serialize_registry_yaml(_registry_to_dict(registry))
    Path(path).write_text(yaml_text, encoding="utf-8")


def _run_main(argv: list[str]) -> tuple[int, dict]:
    """Run ``rcb.main`` capturing stdout, returning the exit code and JSON.

    Stderr is swallowed (warnings are non-blocking and not under test here).

    Args:
        argv: The argument vector to pass to ``main``.

    Returns:
        A ``(exit_code, decision_json)`` tuple.
    """
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
        exit_code = rcb.main(argv)
    return exit_code, json.loads(stdout.getvalue())


class TestNamedScenarios:
    """The explicit scenarios Requirement 5.1 names (example tests, not PBT).

    Drives the back-fill end-to-end through ``main`` (and the pure functions
    directly where cleaner) across the five named scenarios: over-limit with
    Module 1 skipped presents guidance; under-limit and exactly-500 suppress it;
    guidance already delivered in Module 1 suppresses it and reports
    ``already_guided``; missing/unreadable metadata is non-blocking
    (``computable: false``, exit 0); and an unknown source is resolved by
    row-counting a small synthetic csv/jsonl fixture. All fixtures are synthetic
    and PII-free (Requirement 4.2 and the power-distribution safety rule).

    **Validates: Requirement 5.1**
    """

    # ---- Scenario 1: over-limit + Module 1 skipped -> present_guidance true ----

    def test_over_limit_and_module1_skipped_presents_guidance_via_main(self):
        """Over-limit registry with no license markers -> present_guidance true."""
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = os.path.join(tmp, "data_sources.yaml")
            prefs_path = os.path.join(tmp, "bootcamp_preferences.yaml")

            # Total 812 > 500; preferences omitted -> Module 1 state SKIPPED.
            _write_named_registry(
                registry_path,
                [
                    _named_entry("CUSTOMER_CRM", 500),
                    _named_entry("VENDOR_LIST", 312),
                ],
            )

            exit_code, payload = _run_main(
                ["--registry", registry_path, "--preferences", prefs_path]
            )

            assert exit_code == 0
            assert payload["computable"] is True
            assert payload["known_total"] == 812
            assert payload["over_limit"] is True
            assert payload["certain"] is True
            assert payload["module1_state"] == "skipped"
            assert payload["present_guidance"] is True
            assert payload["already_guided"] is False

    def test_over_limit_and_skipped_presents_guidance_via_decide_backfill(self):
        """Focused unit check of the same scenario through decide_backfill."""
        collected = rcb.CollectedCount(
            known_total=812,
            sources=[
                rcb.SourceCount(name="Customer Crm", count=812, counted_from="metadata")
            ],
            unknown_sources=[],
        )
        decision = rcb.decide_backfill(collected, rcb.Module1GuidanceState.SKIPPED)
        assert decision.present_guidance is True
        assert decision.already_guided is False

    # ---- Scenario 2: under-limit and exactly-500 -> present_guidance false ----

    def test_under_limit_suppresses_guidance_via_main(self):
        """A 499-record total is under the limit -> present_guidance false."""
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = os.path.join(tmp, "data_sources.yaml")
            prefs_path = os.path.join(tmp, "bootcamp_preferences.yaml")

            _write_named_registry(registry_path, [_named_entry("CUSTOMER_CRM", 499)])

            exit_code, payload = _run_main(
                ["--registry", registry_path, "--preferences", prefs_path]
            )

            assert exit_code == 0
            assert payload["computable"] is True
            assert payload["known_total"] == 499
            assert payload["over_limit"] is False
            assert payload["present_guidance"] is False

    def test_exactly_500_is_boundary_and_suppresses_guidance_via_main(self):
        """Exactly 500 records is at the limit, not over it -> suppressed."""
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = os.path.join(tmp, "data_sources.yaml")
            prefs_path = os.path.join(tmp, "bootcamp_preferences.yaml")

            _write_named_registry(registry_path, [_named_entry("CUSTOMER_CRM", 500)])

            exit_code, payload = _run_main(
                ["--registry", registry_path, "--preferences", prefs_path]
            )

            assert exit_code == 0
            assert payload["computable"] is True
            assert payload["known_total"] == 500
            assert payload["over_limit"] is False
            assert payload["present_guidance"] is False

    # ---- Scenario 3: guidance already delivered -> suppressed, already_guided ----

    def test_guidance_already_delivered_suppresses_and_flags_already_guided(self):
        """An over-limit registry with a license set -> suppressed, already_guided."""
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = os.path.join(tmp, "data_sources.yaml")
            prefs_path = os.path.join(tmp, "bootcamp_preferences.yaml")

            # Over-limit total (900 > 500) but Module 1 already applied a license.
            _write_named_registry(registry_path, [_named_entry("CUSTOMER_CRM", 900)])

            # Seed the preferences via the canonical writer: a license is set,
            # so classify_module1_state -> DELIVERED.
            result = preferences_utils.write_preference(
                "database_type", "sqlite", preferences_path=prefs_path
            )
            assert result.success, result.error
            result = preferences_utils.write_preference(
                "license", "custom", preferences_path=prefs_path
            )
            assert result.success, result.error

            exit_code, payload = _run_main(
                ["--registry", registry_path, "--preferences", prefs_path]
            )

            assert exit_code == 0
            assert payload["computable"] is True
            assert payload["over_limit"] is True
            assert payload["module1_state"] == "delivered"
            assert payload["already_guided"] is True
            assert payload["present_guidance"] is False

    # ---- Scenario 4: missing/unreadable metadata -> computable false, exit 0 ----

    def test_missing_registry_is_non_blocking_and_computable_false(self):
        """A non-existent registry path -> exit 0 with computable false."""
        with tempfile.TemporaryDirectory() as tmp:
            missing_registry = os.path.join(tmp, "does_not_exist.yaml")
            prefs_path = os.path.join(tmp, "bootcamp_preferences.yaml")

            exit_code, payload = _run_main(
                ["--registry", missing_registry, "--preferences", prefs_path]
            )

            assert exit_code == 0
            assert payload["computable"] is False
            assert payload["present_guidance"] is False

    # ---- Scenario 5: row-count resolution of an unknown source ----

    def test_row_count_resolves_unknown_csv_and_jsonl_sources(self):
        """An unknown source is resolved by row-counting a synthetic fixture."""
        with tempfile.TemporaryDirectory() as tmp:
            # Synthetic, PII-free CSV: header + 3 data rows -> count 3.
            csv_path = os.path.join(tmp, "customers.csv")
            Path(csv_path).write_text("col1,col2\na,b\nc,d\ne,f\n", encoding="utf-8")
            # Synthetic, PII-free JSONL: 4 lines -> count 4.
            jsonl_path = os.path.join(tmp, "vendors.jsonl")
            Path(jsonl_path).write_text(
                '{"col1": "a"}\n{"col1": "b"}\n{"col1": "c"}\n{"col1": "d"}\n',
                encoding="utf-8",
            )

            # count_file_rows directly: csv = lines - 1 (header), jsonl = lines.
            assert rcb.count_file_rows(csv_path, "csv") == 3
            assert rcb.count_file_rows(jsonl_path, "jsonl") == 4

            # Registry with two unknown (record_count null) sources whose
            # file_paths point (absolutely) at the fixtures.
            registry = Registry(
                version="2",
                sources=[
                    _named_entry("CSV_SOURCE", None, file_path=csv_path, fmt="csv"),
                    _named_entry("JSONL_SOURCE", None, file_path=jsonl_path, fmt="jsonl"),
                ],
            )

            # With row-count disabled the sources stay unknown (never zeroed).
            without = rcb.compute_collected_count(registry)
            assert (
                without.known_total == 0
            )  # brittle-allow: domain record count, not a suite test count
            assert set(without.unknown_sources) == {"Csv Source", "Jsonl Source"}
            assert all(sc.counted_from == "unknown" for sc in without.sources)

            # With row-count enabled the unknowns resolve via row counting.
            with_rows = rcb.compute_collected_count(registry, row_count=True)
            assert (
                with_rows.known_total == 7
            )  # brittle-allow: domain record count (3 csv + 4 jsonl)
            assert with_rows.unknown_sources == []
            counted = {sc.name: sc for sc in with_rows.sources}
            assert counted["Csv Source"].counted_from == "row_count"
            assert counted["Csv Source"].count == 3
            assert counted["Jsonl Source"].counted_from == "row_count"
            assert counted["Jsonl Source"].count == 4


# ═══════════════════════════════════════════════════════════════════════════
# End-to-end integration (Requirements 5.1, 5.2, 4.2) — NOT property-based
# ═══════════════════════════════════════════════════════════════════════════

# A distinctive, PII-simulating sentinel embedded only into a non-surfaced
# registry field (``file_path``). The literal ``-`` guarantees it can never be
# a substring of a surfaced source name (letters/underscore/space only), of any
# emitted count, or of the fixed guidance/reason text — so if it ever appears in
# the emitted JSON or the marker files, that is a genuine leak (Requirement 4.2).
_E2E_SENTINEL = "SENTINEL-PII-e2ecafebabe1234"


class TestEndToEndIntegration:
    """End-to-end integration across the real reader/decision/framing plumbing.

    Wires the real registry parser (``data_sources``), the real
    ``preferences_utils`` reader/writer, the real ``volume_utils.build_license_framing``
    framing builder, and the real back-fill script (``record_count_backfill``)
    against a fresh temp workspace laid out canonically
    (``<tmp>/config/data_sources.yaml`` + ``bootcamp_preferences.yaml`` +
    ``bootcamp_progress.json``). It seeds a registry whose collected counts
    exceed the 500-record evaluation limit (300 + 400 = 700) plus a
    deferred-state preferences file, runs ``main`` end-to-end, and asserts the
    emitted decision presents guidance, that the reused canonical framing is
    rendered verbatim, and that ``apply_guidance_markers`` updates the *same*
    Module 1 markers (clearing ``license_guidance_deferred`` and checkpointing
    Step 8a) — all with no fixture PII (a sentinel seeded into a non-surfaced
    field) appearing anywhere in the emitted JSON or the marker files. All
    fixtures are synthetic and PII-free (Requirement 4.2 and the
    power-distribution safety rule).

    **Validates: Requirements 5.1, 5.2, 4.2**
    """

    def test_backfill_end_to_end_presents_guidance_and_updates_module1_markers(self):
        """Full flow: over-limit + deferred -> guidance presented, markers updated.

        Exercises the real plumbing end-to-end in a canonical temp workspace:

        1. Seed ``config/data_sources.yaml`` with two synthetic PII-free sources
           totalling 700 records (> 500), with a PII sentinel embedded in the
           non-surfaced ``file_path`` field.
        2. Seed a deferred-state ``config/bootcamp_preferences.yaml`` via the
           canonical writer (``database_type`` + ``license_guidance_deferred``).
        3. Run ``main`` capturing stdout and assert exit 0 and the JSON decision
           (``computable``/``over_limit``/``present_guidance`` true,
           ``module1_state`` "deferred", ``known_total`` 700).
        4. Rebuild the decision from the real parsed registry and assert the
           rendered guidance equals ``volume_utils.build_license_framing`` for
           the same context (reused framing end-to-end — Req 5.2).
        5. Apply the markers and read the files back: the Module 1
           ``license_guidance_deferred`` marker is cleared, the Step 8a
           checkpoint is recorded, and the preferences keys stay a subset of the
           known top-level keys (no new key).
        6. Assert the seeded sentinel never appears in the emitted JSON or the
           marker files (Req 4.2).
        """
        with tempfile.TemporaryDirectory() as tmp:
            # ---- 1. Canonical workspace layout so main derives workspace_root. ----
            config_dir = os.path.join(tmp, "config")
            os.makedirs(config_dir)
            registry_path = os.path.join(config_dir, "data_sources.yaml")
            prefs_path = os.path.join(config_dir, "bootcamp_preferences.yaml")
            progress_path = os.path.join(config_dir, "bootcamp_progress.json")

            # ---- 2. Seed the registry: 300 + 400 = 700 (> 500), PII-free names,
            #         sentinel in the non-surfaced file_path field. ----
            _write_named_registry(
                registry_path,
                [
                    _named_entry(
                        "CUSTOMER_CRM",
                        300,
                        name="Customer CRM",
                        file_path=f"data/raw/{_E2E_SENTINEL}_a.csv",
                    ),
                    _named_entry(
                        "VENDOR_LIST",
                        400,
                        name="Vendor List",
                        file_path=f"data/raw/{_E2E_SENTINEL}_b.csv",
                    ),
                ],
            )

            # Sanity: the sentinel really is present in the registry input, so a
            # clean output is a genuine no-leak result rather than a vacuous pass.
            registry_text = Path(registry_path).read_text(encoding="utf-8")
            assert _E2E_SENTINEL in registry_text

            # ---- 3. Seed a deferred-state, schema-valid preferences file. ----
            result = preferences_utils.write_preference(
                "database_type", "sqlite", preferences_path=prefs_path
            )
            assert result.success, result.error
            result = preferences_utils.write_preference(
                "license_guidance_deferred", True, preferences_path=prefs_path
            )
            assert result.success, result.error

            # Seed a minimal, schema-valid starting progress file.
            _seed_progress_file(progress_path, "sqlite")

            # ---- 4. Run main end-to-end, capturing stdout. ----
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = rcb.main(
                    [
                        "--registry", registry_path,
                        "--preferences", prefs_path,
                        "--progress", progress_path,
                    ]
                )

            out = stdout.getvalue()
            assert exit_code == 0
            payload = json.loads(out)

            # The real reader/decision plumbing surfaces the over-limit,
            # deferred, present-guidance verdict from the collected 700 total.
            assert payload["computable"] is True
            assert payload["known_total"] == 700
            assert payload["over_limit"] is True
            assert payload["present_guidance"] is True
            assert payload["module1_state"] == "deferred"
            assert payload["certain"] is True
            assert payload["already_guided"] is False

            # No sentinel from the non-surfaced file_path leaks into the JSON.
            assert _E2E_SENTINEL not in out, (
                f"sentinel leaked into the emitted BackfillDecision JSON: {out!r}"
            )

            # ---- 5. Rebuild the decision from the REAL parsed registry and assert
            #         the rendered guidance is the reused canonical framing (Req 5.2). ----
            raw = apply_migrations(parse_registry_yaml(registry_text))
            assert not validate_registry(raw)
            registry = _dict_to_registry(raw)

            collected = rcb.compute_collected_count(registry)
            assert (
                collected.known_total == 700
            )  # brittle-allow: domain record count, not a suite test count

            load_result = preferences_utils.load_preferences(prefs_path)
            assert load_result.error is None
            module1_state = rcb.classify_module1_state(load_result.preferences)
            assert module1_state is rcb.Module1GuidanceState.DEFERRED

            decision = rcb.decide_backfill(collected, module1_state)
            assert decision.present_guidance is True

            # The rendered guidance is byte-for-byte the canonical framing.
            ctx = volume_utils.LicenseFramingContext(
                capacity=100_000,
                validity="1 year",
                submit_feedback_available=True,
                has_existing_license=False,
                mention_downsizing=False,
            )
            rendered = rcb.render_backfill_guidance(decision, ctx)
            expected = volume_utils.build_license_framing(
                capacity=ctx.capacity,
                validity=ctx.validity,
                submit_feedback_available=ctx.submit_feedback_available,
                has_existing_license=ctx.has_existing_license,
                mention_downsizing=ctx.mention_downsizing,
            )
            assert rendered == expected

            # ---- 6. Apply the markers and read the files back (Req 5.1, 3.3). ----
            with contextlib.redirect_stderr(io.StringIO()):
                rcb.apply_guidance_markers(
                    decision,
                    preferences_path=prefs_path,
                    progress_path=progress_path,
                    step_number=8,
                )

            prefs_text = Path(prefs_path).read_text(encoding="utf-8")
            progress_text = Path(progress_path).read_text(encoding="utf-8")

            # The SAME Module 1 marker was updated: the deferral is now cleared.
            parsed_prefs = preferences_utils.parse_yaml(prefs_text)
            assert "license_guidance_deferred" not in parsed_prefs
            # No new preference key was introduced (subset of the known keys).
            assert set(parsed_prefs.keys()) <= set(preferences_utils.KNOWN_TOP_LEVEL_KEYS)
            # The unrelated seeded preference is untouched.
            assert parsed_prefs.get("database_type") == "sqlite"

            # The Step 8a checkpoint was recorded in the progress file.
            progress = json.loads(progress_text)
            assert progress.get("current_step") == "8a"

            # ---- 7. No fixture sentinel/PII leaks into any marker file (Req 4.2). ----
            assert _E2E_SENTINEL not in prefs_text, (
                f"sentinel leaked into the preferences markers: {prefs_text!r}"
            )
            assert _E2E_SENTINEL not in progress_text, (
                f"sentinel leaked into the progress markers: {progress_text!r}"
            )
