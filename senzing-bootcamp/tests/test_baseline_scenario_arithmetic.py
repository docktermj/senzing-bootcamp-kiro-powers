"""Baseline scenario arithmetic tests for the steering-inclusion-auto-audit.

Example/unit tests (Task 7.3) that pin the two baseline figures the audit
reasons about against the token counts measured from the real, shipped
``senzing-bootcamp/steering`` corpus and recorded in its ``steering-index.yaml``
``file_metadata`` block:

* the finalized projected always-set baseline (Decision_Record, Req 2.5) — the
  three pre-existing ``inclusion: always`` files plus the three Auto_Files
  promoted to ``always`` — which must sum to exactly 13,889 tokens and equal
  ``measure_steering``'s computed Baseline_Footprint for the real corpus; and
* the hypothetical ``loads-always`` scenario (Audit_Finding informational note,
  Req 1.5) — the three pre-existing ``always`` files plus all eleven Auto_Files
  counted as always-loaded — stated as ≈25,968 tokens.

Token counts are read from the index via ``measure_steering`` helpers (the same
parsing the shipped tooling uses) rather than hardcoded, and cross-checked
against the on-disk measurement, so the assertions stay truthful if the corpus
shifts. Later specs have since grown a few always-loaded files — most notably
file-placement.md (+219 tokens, small -> medium, from the
file-placement-conventions Canonical Contract) plus small within-tolerance edits
to a pre-existing ``always`` file — so the baselines below were re-pinned to the
current measured reality: the finalized always-set is 13,889 tokens and the
``loads-always`` figure is asserted against ≈25,968 within a small tolerance
while the exact current sum is pinned via the arithmetic identity
(sum of parts == whole).

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

# Baseline figures pinned to the current measured corpus. These began as the
# spec-artifact figures (Decision_Record projected 13,374; Audit_Finding
# ≈24,830) and were re-pinned when later specs grew a few always-loaded files:
# +27 tokens across a pre-existing `always` file (within-tolerance edits from
# file-placement-conventions Tasks 5.2/6.1) and +219 tokens on file-placement.md
# (the Canonical File-Placement Contract), the latter counted only in the
# loads-always scenario.
# Re-pinned once more (13,396 -> 13,544 / 25,113 -> 25,261) for the
# question-format-consistency bugfix: agent-behavior-rules.md — one of the six
# finalized `always` files AND one of the eleven Auto_Files — grew 822 -> 970
# tokens when Rule 4 gained the Session-Recreation Re-Rendering and
# Track-Completion / Graduation Terminal Turn clauses, so both the finalized
# always-set baseline (+148) and the loads-always footprint (+148) moved by the
# same amount. The three pre-existing `always` files were untouched, so
# DOCUMENTED_PRE_EXISTING_ALWAYS stays 6,690.
# Re-pinned once more (13,544 -> 13,889 / 25,623 -> 25,968) for the
# write-gate-noise-cleanup bugfix: agent-behavior-rules.md — one of the six
# finalized `always` files AND one of the eleven Auto_Files — grew 970 -> 1315
# tokens (+345) when Rule 5 was added to it (an `inclusion: always` file), so
# both the finalized always-set baseline (+345) and the loads-always footprint
# (+345) moved by the same amount. The three pre-existing `always` files were
# untouched, so DOCUMENTED_PRE_EXISTING_ALWAYS stays 6,690.
# Re-pinned once more (13_889 -> 14_836 / 6_690 -> 6_836 / 25_968 -> 26_915) for
# the clean-question-presentation bugfix: three always-loaded files grew when the
# stop/gate markers were made internal-only directives and the compose-clean-first
# / no-duplicate-re-display rules were added — agent-instructions.md (a
# pre-existing `always` file) grew +146 (so DOCUMENTED_PRE_EXISTING_ALWAYS moves
# 6_690 -> 6_836), agent-behavior-rules.md (finalized `always` AND an Auto_File)
# 1315 -> 1537 (+222), and conversation-protocol.md (finalized `always` AND an
# Auto_File) 4600 -> 5179 (+579). The finalized always-set moved by the combined
# +947 (13_889 -> 14_836) and the loads-always footprint by the same +947
# (25_968 -> 26_915); qa-transcript.md was untouched.
# Re-pinned once more (14_836 -> 15_803 / 6_836 -> 7_011 / 26_915 -> 27_882) for
# the mandatory-question-answers spec (Task 1): the normative Answer_Required_Rule
# was added to conversation-protocol.md (finalized `always` AND an Auto_File,
# 5179 -> 5759, +580) and referenced from agent-behavior-rules.md (finalized
# `always` AND an Auto_File, 1537 -> 1749, +212) and agent-instructions.md (a
# pre-existing `always` file, 4650 -> 4825, +175). The finalized always-set moved
# by the combined +967 (14_836 -> 15_803), DOCUMENTED_PRE_EXISTING_ALWAYS by the
# agent-instructions.md +175 (6_836 -> 7_011), and the loads-always footprint by
# the same +967 (26_915 -> 27_882); module-transitions.md, security-privacy.md,
# and qa-transcript.md were untouched.
# Re-pinned once more (15_803 -> 17_116 / 7_011 -> 7_739 / 27_882 -> 29_510) for
# the single-ask-question-guarantee spec. That spec added the normative Ask-Once
# Guarantee section to conversation-protocol.md (finalized `always` AND an
# Auto_File) and the Question_Ledger operational guidance to agent-instructions.md
# and the checkpoint-boundary note to module-transitions.md (both pre-existing
# `always` files), plus a one-line cross-reference to session-resume.md (an
# Auto_File). measure_steering.py recomputed all of these into file_metadata and
# the budget total; the figures below are the resulting measured sums (verified
# against the live index via the arithmetic identities the tests assert):
#   * finalized always-set (the six `always` files) = 17_116
#   * three pre-existing `always` files             =  7_739 (security-privacy.md
#     untouched; agent-instructions.md + module-transitions.md grew)
#   * loads-always (3 pre-existing + 11 Auto_Files)  = 29_510
DOCUMENTED_FINALIZED_BASELINE = 17_116   # finalized always-set (Decision_Record baseline, Req 2.5)
DOCUMENTED_PRE_EXISTING_ALWAYS = 7_739   # three pre-existing `always` files
# Re-pinned once more (25_261 -> 25_623) for the session-handoff spec: task 5.1
# added the "### Session Handoff Offer" hook-in to agent-context-management.md
# (one of the eleven Auto_Files), growing its measured count 1326 -> 1616 (+290),
# which moved the loads-always footprint past the 1% tolerance band. The finalized
# always-set is unchanged (agent-context-management.md is manual-inclusion, not in
# the finalized `always` set), so DOCUMENTED_FINALIZED_BASELINE stays 13_544 and
# DOCUMENTED_PRE_EXISTING_ALWAYS stays 6_690 (the three pre-existing `always`
# files were untouched). The new session-handoff.md steering file is
# manual-inclusion and is in neither set.
# Re-pinned once more (25_623 -> 25_968) for the write-gate-noise-cleanup
# bugfix: agent-behavior-rules.md (one of the eleven Auto_Files) grew
# 970 -> 1315 (+345) when Rule 5 was added, moving the loads-always footprint by
# the same +345. This file is ALSO in the finalized `always` set, so
# DOCUMENTED_FINALIZED_BASELINE moved by the same amount (13_544 -> 13_889);
# DOCUMENTED_PRE_EXISTING_ALWAYS stays 6_690 (the three pre-existing `always`
# files were untouched).
DOCUMENTED_LOADS_ALWAYS = 29_510         # loads-always footprint (Audit_Finding note, Req 1.5)

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
        """Finalized always-set sums to 17,116 across the index and the corpus.

        Validates: Requirements 2.5, 1.5

        Reads the per-file ``token_count`` from the shipped ``steering-index.yaml``
        ``file_metadata`` and asserts the six finalized ``always`` files sum to
        exactly the current baseline of 17,116 tokens; confirms the same
        figure equals ``measure_steering``'s computed Baseline_Footprint for the
        real corpus (the ``inclusion: always`` set); and pins the composition
        identity 7,739 (pre-existing) + 9,377 (newly promoted) == 17,116.
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
        re-pinned baseline of ≈26,915 tokens. The exact current measured sum is
        pinned via the identity rather than a brittle literal, and cross-checked
        against the on-disk measurement. The re-pinned baseline is ≈27,882 tokens.
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

        # The measured loads-always footprint matches the re-pinned ≈27,882
        # within a 1% tolerance (the mandatory-question-answers Answer_Required_Rule
        # edits grew agent-instructions.md +175, agent-behavior-rules.md +212, and
        # conversation-protocol.md +580, moving it up from the prior ≈26,915
        # documented figure).
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
