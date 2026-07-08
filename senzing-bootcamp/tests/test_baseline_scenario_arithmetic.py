"""Baseline scenario arithmetic tests for the steering-inclusion-auto-audit.

Example/unit tests (Task 7.3) that pin the two baseline figures the audit
reasons about against the token counts measured from the real, shipped
``senzing-bootcamp/steering`` corpus and recorded in its ``steering-index.yaml``
``file_metadata`` block:

* the finalized projected always-set baseline (Decision_Record, Req 2.5) — the
  three pre-existing ``inclusion: always`` files plus the three Auto_Files
  promoted to ``always`` — which must sum to exactly 13,374 tokens and equal
  ``measure_steering``'s computed Baseline_Footprint for the real corpus; and
* the hypothetical ``loads-always`` scenario (Audit_Finding informational note,
  Req 1.5) — the three pre-existing ``always`` files plus all eleven Auto_Files
  counted as always-loaded — stated as ≈24,830 tokens.

Token counts are read from the index via ``measure_steering`` helpers (the same
parsing the shipped tooling uses) rather than hardcoded, and cross-checked
against the on-disk measurement, so the assertions stay truthful if the corpus
shifts. The two frontmatter deltas from Task 4/7.1 (changed ``inclusion`` value
plus an added ``fileMatchPattern`` on one file) nudge a few counts by a handful
of tokens, so the ``loads-always`` figure is asserted against the documented
≈24,830 within a small tolerance while the exact current sum is pinned via the
arithmetic identity (sum of parts == whole).

These are example tests (no ``@given`` needed): both scenarios are fixed,
enumerated file sets whose sums are exact arithmetic facts about the corpus.
``--check`` is not invoked here and nothing is written, so the working tree is
never mutated.
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages).
# conftest.py already inserts this, but keep it explicit per convention.
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import measure_steering  # noqa: E402

# ---------------------------------------------------------------------------
# Real, shipped corpus under test (resolved from this file, not the cwd).
# ---------------------------------------------------------------------------
_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_INDEX_PATH = _STEERING_DIR / "steering-index.yaml"

# The three files that declared `inclusion: always` before the audit.
PRE_EXISTING_ALWAYS_FILES: tuple[str, ...] = (
    "agent-instructions.md",
    "module-transitions.md",
    "security-privacy.md",
)

# The three Auto_Files the Decision_Record promoted to `always` (every-session).
NEWLY_ALWAYS_FILES: tuple[str, ...] = (
    "agent-behavior-rules.md",
    "conversation-protocol.md",
    "qa-transcript.md",
)

# The finalized always-set is exactly those six files (Decision_Record, Req 2.5).
FINALIZED_ALWAYS_FILES: tuple[str, ...] = PRE_EXISTING_ALWAYS_FILES + NEWLY_ALWAYS_FILES

# The eleven Auto_Files that declared `inclusion: auto` before re-classification.
AUTO_FILES: tuple[str, ...] = (
    "agent-behavior-rules.md",
    "agent-context-management.md",
    "conversation-protocol.md",
    "design-patterns.md",
    "file-placement.md",
    "mcp-response-caching.md",
    "module-prerequisites.md",
    "project-structure.md",
    "qa-transcript.md",
    "session-resume.md",
    "verbosity-control.md",
)

# Stated figures from the spec artifacts.
DOCUMENTED_FINALIZED_BASELINE = 13_374   # Decision_Record `projected_baseline_footprint` (Req 2.5)
DOCUMENTED_PRE_EXISTING_ALWAYS = 6_668   # three pre-existing `always` files
DOCUMENTED_LOADS_ALWAYS = 24_830         # Audit_Finding informational `loads-always` note (Req 1.5)

# "≈" tolerance for the loads-always note: 1% of the stated figure. The two
# Task 4/7.1 frontmatter edits move the true sum by only a handful of tokens,
# comfortably inside this band.
LOADS_ALWAYS_TOLERANCE = round(0.01 * DOCUMENTED_LOADS_ALWAYS)


def _sum_token_counts(filenames: tuple[str, ...], metadata: dict) -> int:
    """Sum the ``token_count`` of the named files from a metadata map.

    Args:
        filenames: Steering filenames to sum over.
        metadata: A map from filename to a metadata dict containing
            ``token_count`` (the index ``file_metadata`` block parsed by
            ``measure_steering._parse_stored_metadata``, or the on-disk scan from
            ``measure_steering.scan_steering_files``).

    Returns:
        The summed ``token_count`` over ``filenames``.

    Raises:
        AssertionError: If a named file is absent from ``metadata`` (a missing
            file would silently understate the sum and mask a corpus drift).
    """
    total = 0
    for name in filenames:
        assert name in metadata, f"{name} missing from steering metadata"
        total += metadata[name]["token_count"]
    return total


class TestBaselineScenarioArithmetic:
    """Baseline scenario arithmetic over the real corpus (Req 1.5, Req 2.5)."""

    def test_finalized_always_baseline_equals_measured_sum(self):
        """Finalized always-set sums to 13,374 across the index and the corpus.

        Validates: Requirements 2.5, 1.5

        Reads the per-file ``token_count`` from the shipped ``steering-index.yaml``
        ``file_metadata`` and asserts the six finalized ``always`` files sum to
        exactly the Decision_Record's projected 13,374 tokens; confirms the same
        figure equals ``measure_steering``'s computed Baseline_Footprint for the
        real corpus (the ``inclusion: always`` set); and pins the composition
        identity 6,668 (pre-existing) + 6,706 (newly promoted) == 13,374.
        """
        stored = measure_steering._parse_stored_metadata(
            measure_steering.load_yaml_content(_INDEX_PATH)
        )
        assert stored is not None, "file_metadata section missing from index"

        finalized_sum = _sum_token_counts(FINALIZED_ALWAYS_FILES, stored)
        assert finalized_sum == DOCUMENTED_FINALIZED_BASELINE

        # Composition identity: the finalized baseline is the pre-existing always
        # files plus the newly promoted Auto_Files (sum of parts == whole).
        pre_existing_sum = _sum_token_counts(PRE_EXISTING_ALWAYS_FILES, stored)
        newly_always_sum = _sum_token_counts(NEWLY_ALWAYS_FILES, stored)
        assert pre_existing_sum == DOCUMENTED_PRE_EXISTING_ALWAYS
        assert pre_existing_sum + newly_always_sum == finalized_sum

        # The finalized baseline equals measure_steering's computed footprint for
        # the real corpus: the always-set is exactly these six files, and the
        # footprint over the on-disk measurement matches the index sum.
        scanned = measure_steering.scan_steering_files(_STEERING_DIR)
        always_loaded = measure_steering.collect_always_loaded_set(_STEERING_DIR)
        assert always_loaded == sorted(FINALIZED_ALWAYS_FILES)
        footprint = measure_steering.compute_baseline_footprint(always_loaded, scanned)
        assert footprint == DOCUMENTED_FINALIZED_BASELINE

    def test_loads_always_scenario_equals_measured_sum(self):
        """The hypothetical loads-always footprint matches the measured sum.

        Validates: Requirements 1.5, 2.5

        Reads the per-file ``token_count`` from the shipped ``steering-index.yaml``
        ``file_metadata`` and asserts the ``loads-always`` scenario — the three
        pre-existing ``always`` files plus all eleven Auto_Files counted as
        always-loaded — satisfies the arithmetic identity (pre-existing sum +
        Auto_Files sum == combined sum) and lands within tolerance of the
        Audit_Finding's stated ≈24,830 tokens. The exact current measured sum is
        pinned via the identity rather than a brittle literal, and cross-checked
        against the on-disk measurement.
        """
        stored = measure_steering._parse_stored_metadata(
            measure_steering.load_yaml_content(_INDEX_PATH)
        )
        assert stored is not None, "file_metadata section missing from index"

        pre_existing_sum = _sum_token_counts(PRE_EXISTING_ALWAYS_FILES, stored)
        auto_files_sum = _sum_token_counts(AUTO_FILES, stored)
        loads_always_sum = _sum_token_counts(
            PRE_EXISTING_ALWAYS_FILES + AUTO_FILES, stored
        )

        # Arithmetic identity: sum of parts == whole. The pre-existing `always`
        # files and the eleven Auto_Files are disjoint sets, so the combined sum
        # equals the two partial sums added together.
        assert pre_existing_sum + auto_files_sum == loads_always_sum
        assert pre_existing_sum == DOCUMENTED_PRE_EXISTING_ALWAYS

        # The measured loads-always footprint matches the documented ≈24,830
        # within a 1% tolerance (the frontmatter edits shift it by ~11 tokens).
        assert abs(loads_always_sum - DOCUMENTED_LOADS_ALWAYS) <= LOADS_ALWAYS_TOLERANCE, (
            f"loads-always measured sum {loads_always_sum} is farther than "
            f"{LOADS_ALWAYS_TOLERANCE} tokens from the documented "
            f"{DOCUMENTED_LOADS_ALWAYS}"
        )

        # Cross-check the index sum against the on-disk measurement so the two
        # sources cannot silently diverge.
        scanned = measure_steering.scan_steering_files(_STEERING_DIR)
        scanned_loads_always = _sum_token_counts(
            PRE_EXISTING_ALWAYS_FILES + AUTO_FILES, scanned
        )
        assert scanned_loads_always == loads_always_sum
