"""Pure reference model of the Module 3 TruthSet availability classification rule.

This is a **test-only** helper co-located with the property tests for the
``truthset-fallback-source`` feature. It is *not* shipped as a power script under
``senzing-bootcamp/scripts/`` and performs **no** filesystem or network I/O — it is
a pure, deterministic encoding of the *agent logic that lives in steering* so the
property tests can quantify over it.

The classification rule mirrored here is the Step 2 "Availability Classifier"
described in ``senzing-bootcamp/steering/module-03-phase1-verification.md`` (Step 2,
"Classify Primary_TruthSet availability") and in the feature design document
(``design.md`` §2 "Availability Classifier"):

* **available** — the ``get_sample_data`` response contains a named TruthSet
  reference (a dataset whose ``name`` matches "TruthSet" case-insensitively, or whose
  ``type`` indicates ``truthset``) WITH retrievable records.
* **unavailable** — the response contains only CORD collection entries
  (Las Vegas, London, Moscow) and no TruthSet entry.

The single entry point for this task is :func:`classify_availability`. The model is
intentionally minimal — later property tasks for this feature (path selection /
provenance, degraded-status propagation) will append their own pure functions to
this module and reuse the vocabulary declared here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = [
    "AVAILABLE",
    "UNAVAILABLE",
    "CORD_COLLECTION_NAMES",
    "TRUTHSET_NAME_TOKEN",
    "RESPONSE_CONTAINER_KEYS",
    "classify_availability",
    "MCP_PRIMARY",
    "GITHUB_FALLBACK",
    "CORD_SUBSTITUTE",
    "NON_DETERMINISTIC",
    "BLOCKED",
    "FALLBACK_SUCCESS",
    "FALLBACK_FAILURE_STATUSES",
    "AcquisitionDecision",
    "select_acquisition",
    "DETERMINISTIC_PASSED",
    "DETERMINISTIC_FAILED",
    "DEGRADED_VERIFICATION_STATES",
    "INCOMPLETE",
    "COMPLETE",
    "derive_module_status",
    "VALID_PROVENANCE",
    "build_progress_and_report",
]

# The two classification outcomes the Availability Classifier can emit.
AVAILABLE = "available"
UNAVAILABLE = "unavailable"

# The CORD sample collections ``get_sample_data`` may expose, lowercased for
# case-insensitive matching. A response carrying only these (and no TruthSet)
# classifies as ``unavailable``.
CORD_COLLECTION_NAMES: frozenset[str] = frozenset({"las vegas", "london", "moscow"})

# The token a dataset ``name`` (space-insensitive) or ``type`` must carry, matched
# case-insensitively, to count as a named TruthSet reference.
TRUTHSET_NAME_TOKEN = "truthset"

# Keys under which a ``get_sample_data`` response may carry its list of dataset
# entries. The classifier also accepts a bare list. The first key whose value is a
# list wins, mirroring an agent scanning the response for the collection of
# datasets regardless of the exact envelope key the MCP server used.
RESPONSE_CONTAINER_KEYS: tuple[str, ...] = (
    "datasets",
    "collections",
    "sample_data",
    "data",
    "entries",
)


def _extract_entries(mcp_response: Any) -> list[dict[str, Any]]:
    """Extract the list of dataset entries from a ``get_sample_data`` response.

    Accepts either a bare list of entries or a mapping carrying the entries under
    one of :data:`RESPONSE_CONTAINER_KEYS`. Non-dict elements are ignored so a
    malformed entry can never masquerade as a dataset.

    Args:
        mcp_response: The parsed ``get_sample_data`` response (mapping or list).

    Returns:
        The dataset entries as dicts, or an empty list when none can be located.
    """
    if isinstance(mcp_response, list):
        return [entry for entry in mcp_response if isinstance(entry, dict)]
    if isinstance(mcp_response, dict):
        for key in RESPONSE_CONTAINER_KEYS:
            value = mcp_response.get(key)
            if isinstance(value, list):
                return [entry for entry in value if isinstance(entry, dict)]
    return []


def _normalize(text: Any) -> str:
    """Lowercase and strip a value for case-insensitive comparison.

    Args:
        text: A candidate string value (any other type yields an empty string).

    Returns:
        The trimmed, lowercased string, or ``""`` when ``text`` is not a string.
    """
    return text.strip().lower() if isinstance(text, str) else ""


def _is_truthset_entry(entry: dict[str, Any]) -> bool:
    """Report whether ``entry`` is a named TruthSet reference.

    An entry is a TruthSet reference when its ``name`` contains the ``truthset``
    token (matched case-insensitively and ignoring internal spaces, so both
    ``"TruthSet"`` and ``"Truth Set"`` qualify), or when its ``type`` is exactly
    ``truthset`` (case-insensitive).

    Args:
        entry: One dataset entry from the response.

    Returns:
        ``True`` if the entry names or types itself as a TruthSet.
    """
    name = _normalize(entry.get("name"))
    if TRUTHSET_NAME_TOKEN in name or TRUTHSET_NAME_TOKEN in name.replace(" ", ""):
        return True
    return _normalize(entry.get("type")) == TRUTHSET_NAME_TOKEN


def _has_retrievable_records(entry: dict[str, Any]) -> bool:
    """Report whether ``entry`` exposes retrievable record content.

    Retrievability is satisfied by a non-empty ``records`` list or a positive
    integer ``record_count`` (``bool`` is rejected despite subclassing ``int``).

    Args:
        entry: One dataset entry from the response.

    Returns:
        ``True`` if the entry carries at least one retrievable record.
    """
    records = entry.get("records")
    if isinstance(records, list) and len(records) > 0:
        return True
    count = entry.get("record_count")
    return isinstance(count, int) and not isinstance(count, bool) and count > 0


def classify_availability(mcp_response: Any) -> str:
    """Classify Primary_TruthSet availability from a ``get_sample_data`` response.

    Mirrors the Step 2 Availability Classifier: returns :data:`AVAILABLE` if and
    only if the response contains a named TruthSet reference with retrievable
    records; otherwise returns :data:`UNAVAILABLE` (the canonical case being a
    CORD-only response with no TruthSet entry).

    Args:
        mcp_response: The parsed ``get_sample_data`` response (mapping or list).

    Returns:
        :data:`AVAILABLE` or :data:`UNAVAILABLE`.
    """
    for entry in _extract_entries(mcp_response):
        if _is_truthset_entry(entry) and _has_retrievable_records(entry):
            return AVAILABLE
    return UNAVAILABLE


# ---------------------------------------------------------------------------
# Step 2 / Step 2a: acquisition path selection + provenance (Property 2)
# ---------------------------------------------------------------------------
#
# The following encodes the acquisition-path decision the agent performs in
# ``module-03-phase1-verification.md`` Step 2 ("Primary path" / "Fallback path")
# and Step 2a ("Graceful Degradation"), together with the ``design.md`` High-Level
# Flow diagram and Property 2 ("Path Selection and Provenance Consistency"). It
# maps an availability state (and, when the primary is unavailable, the fallback
# outcome and the bootcamper's CORD decision) to exactly one provenance label and
# the source Step 7 must use for Expected_Results.

# Provenance labels recorded as ``source_provenance`` (design "Progress File
# Extensions"; Reqs 2.2, 3.3, 7.3). These are the only non-null provenance values.
MCP_PRIMARY = "mcp_primary"
GITHUB_FALLBACK = "github_fallback"
CORD_SUBSTITUTE = "cord_substitute"

# Expected-results routing values that are NOT themselves provenance labels.
# ``NON_DETERMINISTIC`` marks the accepted CORD substitute path, which has no
# known-good Expected_Results (Step 2a / Req 7.3). ``BLOCKED`` marks the
# declined-CORD path, where no dataset is loaded at all (Step 2a / Req 7.4).
NON_DETERMINISTIC = "non_deterministic"
BLOCKED = "blocked"

# The fetcher stdout ``status`` meaning the fallback path produced a usable
# TruthSet (design "Fallback Fetcher Script" interface contract; Step 2 item 5.2).
FALLBACK_SUCCESS = "success"

# The fetcher stdout statuses meaning the fallback path did NOT succeed, so
# graceful degradation (Step 2a) applies (Step 2 item 5.3).
FALLBACK_FAILURE_STATUSES: frozenset[str] = frozenset(
    {"fetch_failed", "validation_failed", "expected_results_failed"}
)


@dataclass(frozen=True)
class AcquisitionDecision:
    """The outcome of acquisition-path selection for one verification run.

    Attributes:
        provenance: The ``source_provenance`` label to record — one of
            :data:`MCP_PRIMARY`, :data:`GITHUB_FALLBACK`, or :data:`CORD_SUBSTITUTE`,
            or ``None`` when the bootcamper declined the CORD substitute (blocked).
        expected_results_source: The source Step 7 must use for Expected_Results —
            :data:`MCP_PRIMARY` (from the MCP server), :data:`GITHUB_FALLBACK` (from
            the sanctioned fallback source), :data:`NON_DETERMINISTIC` (the CORD
            substitute has no known-good results), or :data:`BLOCKED` (no dataset
            loaded).
        deterministic: Whether Step 7 can run deterministic verification against
            known-good Expected_Results (``True`` for the primary and fallback
            paths, ``False`` for the CORD-substitute and blocked outcomes).
    """

    provenance: str | None
    expected_results_source: str
    deterministic: bool


def select_acquisition(
    availability: str,
    fallback_outcome: str | None = None,
    cord_accepted: bool | None = None,
) -> AcquisitionDecision:
    """Select the acquisition path, provenance label, and expected-results source.

    Mirrors ``module-03-phase1-verification.md`` Step 2 / Step 2a and the
    ``design.md`` High-Level Flow diagram (Property 2). The primary MCP path takes
    precedence: whenever the Primary_TruthSet is available the decision is
    ``mcp_primary`` regardless of any fallback/CORD inputs (Req 2.1, 2.2), and Step
    7 uses the MCP Expected_Results (Req 2.3). When the primary is unavailable, a
    successful fallback fetch yields ``github_fallback`` with fallback
    Expected_Results (Reqs 3.1, 3.3, 5.3); otherwise graceful degradation applies
    and an accepted CORD substitute yields ``cord_substitute`` routed to
    non-deterministic verification with no known-good results (Req 7.3), while a
    declined substitute is blocked with no provenance (Req 7.4).

    Args:
        availability: The Availability Classifier output — :data:`AVAILABLE` or
            :data:`UNAVAILABLE`.
        fallback_outcome: The fallback fetcher ``status`` when the fallback path
            runs (:data:`FALLBACK_SUCCESS`, or a value in
            :data:`FALLBACK_FAILURE_STATUSES`); ``None`` when the primary path is
            taken and the fallback never runs.
        cord_accepted: The bootcamper's CORD-substitute decision when both sources
            fail — ``True`` (accepted), ``False`` (declined), or ``None`` (not
            reached).

    Returns:
        The :class:`AcquisitionDecision` for the run.
    """
    if availability == AVAILABLE:
        return AcquisitionDecision(
            provenance=MCP_PRIMARY,
            expected_results_source=MCP_PRIMARY,
            deterministic=True,
        )
    if fallback_outcome == FALLBACK_SUCCESS:
        return AcquisitionDecision(
            provenance=GITHUB_FALLBACK,
            expected_results_source=GITHUB_FALLBACK,
            deterministic=True,
        )
    if cord_accepted:
        return AcquisitionDecision(
            provenance=CORD_SUBSTITUTE,
            expected_results_source=NON_DETERMINISTIC,
            deterministic=False,
        )
    return AcquisitionDecision(
        provenance=None,
        expected_results_source=BLOCKED,
        deterministic=False,
    )


# ---------------------------------------------------------------------------
# Step 2a: degraded-status propagation (Property 8)
# ---------------------------------------------------------------------------
#
# The following encodes the overall-module-status derivation the agent performs
# in ``module-03-phase1-verification.md`` Step 2a item 5 ("Either outcome (Req
# 7.5): when the check is ``non_deterministic`` or ``blocked``, set the overall
# Module 3 status to ``incomplete``"), together with the ``design.md`` "Progress
# File Extensions" degraded example (``"status": "incomplete"``) and Property 8
# ("Degraded Status Propagation").

# Deterministic_Verification check states recorded in the Verification_Report for
# a *deterministic* run — the run had known-good Expected_Results and Step 7 was
# able to compare against them. Neither of these forces the module incomplete.
DETERMINISTIC_PASSED = "passed"
DETERMINISTIC_FAILED = "failed"

# The Deterministic_Verification check states that trip the degradation rule: an
# accepted CORD substitute (``non_deterministic``) or a declined one (``blocked``).
# Recording either forces the overall Module 3 status to ``incomplete`` (Req 7.5).
DEGRADED_VERIFICATION_STATES: frozenset[str] = frozenset({NON_DETERMINISTIC, BLOCKED})

# Overall Module 3 verification status values relevant to Property 8. ``INCOMPLETE``
# is the status a degraded run is forced to; ``COMPLETE`` is the normal status a
# deterministic run keeps (it is never forced to ``incomplete``).
INCOMPLETE = "incomplete"
COMPLETE = "complete"


def derive_module_status(deterministic_verification: str) -> str:
    """Derive the overall Module 3 status from the Deterministic_Verification state.

    Mirrors ``module-03-phase1-verification.md`` Step 2a item 5 and the
    ``design.md`` "Progress File Extensions" degraded example (Property 8): when
    the Deterministic_Verification check is recorded as :data:`NON_DETERMINISTIC`
    or :data:`BLOCKED`, the overall Module 3 verification status is forced to
    :data:`INCOMPLETE` (Req 7.5). Any deterministic-run state — e.g.
    :data:`DETERMINISTIC_PASSED` or :data:`DETERMINISTIC_FAILED` — leaves the
    module status at the normal :data:`COMPLETE` value and is never forced to
    ``incomplete``.

    Args:
        deterministic_verification: The recorded Deterministic_Verification check
            state — one of :data:`DETERMINISTIC_PASSED`,
            :data:`DETERMINISTIC_FAILED`, :data:`NON_DETERMINISTIC`, or
            :data:`BLOCKED`.

    Returns:
        :data:`INCOMPLETE` when the check state is a degraded state (in
        :data:`DEGRADED_VERIFICATION_STATES`); otherwise :data:`COMPLETE`.
    """
    if deterministic_verification in DEGRADED_VERIFICATION_STATES:
        return INCOMPLETE
    return COMPLETE


# ---------------------------------------------------------------------------
# Step 2/2a persistence + Step 10 report mirroring (Property 9)
# ---------------------------------------------------------------------------
#
# The following encodes the provenance-persistence path the agent performs in
# ``module-03-phase1-verification.md`` Step 2/2a (the ``truthset_acquisition``
# checkpoint written to ``config/bootcamp_progress.json`` with a
# ``source_provenance`` field) together with ``module-03-phase3-report-close.md``
# Step 10 (the Verification Report, which mirrors the provenance Step 2/2a wrote —
# "Do NOT re-derive it; carry the acquisition result forward" — at both the
# ``module_3_verification`` level and on the ``truthset_acquisition`` check). This
# mirrors the ``design.md`` "Progress File Extensions" / "Expected Results
# Structure" ``source`` shape and Property 9 ("Provenance Persistence
# Completeness"), covering Reqs 8.1 and 8.3.

# The provenance labels a *completed* acquisition can persist. These are the only
# values ``source_provenance`` may carry in both the progress file and the
# Verification Report (Req 8.1, 8.3). The declined/blocked path has provenance
# ``None`` and is NOT a completed acquisition with a provenance value, so it is
# outside the scope of Property 9.
VALID_PROVENANCE: frozenset[str] = frozenset({MCP_PRIMARY, GITHUB_FALLBACK, CORD_SUBSTITUTE})


def build_progress_and_report(
    decision: AcquisitionDecision,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the persisted progress entry and Verification Report for an acquisition.

    Mirrors the Step 2/2a checkpoint (which persists ``source_provenance`` to
    ``config/bootcamp_progress.json`` alongside the ``truthset_acquisition`` check)
    and the Step 10 Verification Report (which carries the SAME provenance forward
    — at both the ``module_3_verification`` level and on the ``truthset_acquisition``
    check — rather than re-deriving it). The report's provenance is therefore read
    back from the persisted progress entry, so the two structures can never diverge
    (Property 9; Reqs 8.1, 8.3).

    Args:
        decision: A completed :class:`AcquisitionDecision` whose ``provenance`` is a
            label in :data:`VALID_PROVENANCE` (``mcp_primary``, ``github_fallback``,
            or ``cord_substitute``). The declined/blocked outcome (provenance
            ``None``) is not a completed acquisition and is rejected.

    Returns:
        A ``(progress, report)`` tuple. ``progress`` is the
        ``bootcamp_progress.json``-shaped ``module_3_verification.checks.
        truthset_acquisition`` entry including ``source_provenance``; ``report`` is
        the Verification Report structure including ``source_provenance`` at both the
        ``module_3_verification`` level and on the ``truthset_acquisition`` check.

    Raises:
        ValueError: If ``decision.provenance`` is not a label in
            :data:`VALID_PROVENANCE` (e.g. the ``None`` blocked path).
    """
    provenance = decision.provenance
    if provenance not in VALID_PROVENANCE:
        raise ValueError(
            "build_progress_and_report requires a completed acquisition whose "
            f"provenance is in {sorted(VALID_PROVENANCE)}, got {provenance!r}"
        )

    # Step 2/2a: persist the acquisition check, including source_provenance.
    progress: dict[str, Any] = {
        "module_3_verification": {
            "checks": {
                "truthset_acquisition": {
                    "status": "passed",
                    "source_provenance": provenance,
                }
            }
        }
    }

    # Step 10: mirror what Step 2/2a persisted — read it back, never re-derive.
    persisted = progress["module_3_verification"]["checks"]["truthset_acquisition"][
        "source_provenance"
    ]
    report: dict[str, Any] = {
        "module_3_verification": {
            "source_provenance": persisted,
            "checks": {
                "truthset_acquisition": {
                    "status": "passed",
                    "source_provenance": persisted,
                }
            },
        }
    }
    return progress, report
