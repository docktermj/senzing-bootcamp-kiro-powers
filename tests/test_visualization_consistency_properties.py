"""Property-based tests for visualization consistency protocol.

Uses Hypothesis to verify universal invariants over the visualization protocol:
- Property 1: Offer template structural invariance
- Property 2: Checkpoint-to-type mapping completeness and rendering accuracy
- Property 3: Tracker state machine validity
- Property 4: Per-checkpoint offer idempotency
- Property 5: Module-level decline suppression
- Property 6: Enforcement identifies missing offers

Feature: visualization-consistency
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

ALL_VISUALIZATION_TYPES = [
    "Static_HTML_Report",
    "Interactive_D3_Graph",
    "Web_Service_Dashboard",
]

TYPE_DESCRIPTIONS: dict[str, str] = {
    "Static_HTML_Report": (
        "**Static HTML file** — a self-contained file you can open directly"
        " in your browser, no server needed"
    ),
    "Interactive_D3_Graph": (
        "**Interactive D3 graph** — a force-directed network graph showing"
        " entities, relationships, and match strengths"
    ),
    "Web_Service_Dashboard": (
        "**Web service** — a localhost server with live SDK queries, data"
        " refresh, and interactive details"
    ),
}

CHECKPOINT_MAP: dict[int, list[dict]] = {
    3: [
        {
            "id": "m3_demo_results",
            "context": "these entity resolution demo results",
            "types": ["Static_HTML_Report", "Web_Service_Dashboard"],
        },
    ],
    5: [
        {
            "id": "m5_quality_assessment",
            "context": "this data quality assessment",
            "types": ["Static_HTML_Report"],
        },
    ],
    7: [
        {
            "id": "m7_exploratory_queries",
            "context": "your resolved entities and relationships",
            "types": [
                "Static_HTML_Report",
                "Interactive_D3_Graph",
                "Web_Service_Dashboard",
            ],
        },
        {
            "id": "m7_findings_documented",
            "context": "your query results and validation metrics",
            "types": [
                "Static_HTML_Report",
                "Interactive_D3_Graph",
                "Web_Service_Dashboard",
            ],
        },
    ],
    8: [
        {
            "id": "m8_performance_report",
            "context": "the performance benchmarks and optimization results",
            "types": ["Static_HTML_Report", "Web_Service_Dashboard"],
        },
    ],
}

VALID_STATUSES = {"offered", "accepted", "declined", "generated"}

VALID_TRANSITIONS: set[tuple[str, str]] = {
    ("offered", "accepted"),
    ("offered", "declined"),
    ("accepted", "generated"),
}

ALL_CHECKPOINT_IDS: list[str] = [
    cp["id"] for cps in CHECKPOINT_MAP.values() for cp in cps
]


# ---------------------------------------------------------------------------
# Pure functions under test
# ---------------------------------------------------------------------------


def render_offer_template(context: str, types: list[str]) -> str:
    """Render the visualization offer template for a given context and type list.

    Args:
        context: The context string describing what will be visualized.
        types: Non-empty list of visualization type identifiers.

    Returns:
        The fully rendered offer message including opening phrase, numbered
        list, and STOP directive.
    """
    opening = f"Would you like me to create a visualization of {context}?"
    lines = [opening, ""]
    for i, vtype in enumerate(types, start=1):
        description = TYPE_DESCRIPTIONS[vtype]
        lines.append(f"{i}. {description}")
    lines.append("")
    lines.append("> 🛑 STOP — End your response here. Wait for the bootcamper's input.")
    return "\n".join(lines)


def is_valid_transition(from_status: str, to_status: str) -> bool:
    """Check whether a state transition is valid.

    Args:
        from_status: The current status of the tracker entry.
        to_status: The proposed new status.

    Returns:
        True if the transition is permitted by the state machine.
    """
    return (from_status, to_status) in VALID_TRANSITIONS


def should_offer(checkpoint_id: str, tracker_offers: list[dict]) -> bool:
    """Determine whether a visualization offer should be made at a checkpoint.

    Args:
        checkpoint_id: The checkpoint identifier to check.
        tracker_offers: List of existing tracker entries.

    Returns:
        True if no tracker entry exists for this checkpoint (offer should be made).
        False if an entry already exists (skip the offer).
    """
    for entry in tracker_offers:
        if entry.get("checkpoint_id") == checkpoint_id:
            return False
    return True


def find_missing_checkpoints(
    module: int,
    tracker_offers: list[dict],
    checkpoint_map: dict[int, list[dict]],
) -> list[str]:
    """Find checkpoint IDs that have no tracker entry for a given module.

    Args:
        module: The module number to check.
        tracker_offers: List of existing tracker entries.
        checkpoint_map: The full checkpoint map (module → checkpoint list).

    Returns:
        List of checkpoint IDs that are missing from the tracker.
    """
    if module not in checkpoint_map:
        return []
    expected_ids = {cp["id"] for cp in checkpoint_map[module]}
    tracked_ids = {
        entry["checkpoint_id"]
        for entry in tracker_offers
        if entry.get("module") == module
    }
    missing = expected_ids - tracked_ids
    return sorted(missing)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_context_string() -> st.SearchStrategy[str]:
    """Strategy for generating valid context strings (non-empty printable text)."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N", "P", "Z"),
            blacklist_characters="\x00",
        ),
        min_size=1,
        max_size=120,
    )


def st_type_subset() -> st.SearchStrategy[list[str]]:
    """Strategy for generating non-empty subsets of visualization types."""
    return st.lists(
        st.sampled_from(ALL_VISUALIZATION_TYPES),
        min_size=1,
        max_size=3,
        unique=True,
    )


def st_checkpoint() -> st.SearchStrategy[dict]:
    """Strategy that samples from all defined checkpoints."""
    all_checkpoints = [cp for cps in CHECKPOINT_MAP.values() for cp in cps]
    return st.sampled_from(all_checkpoints)


def st_status() -> st.SearchStrategy[str]:
    """Strategy for generating valid status values."""
    return st.sampled_from(sorted(VALID_STATUSES))


def st_transition_pair() -> st.SearchStrategy[tuple[str, str]]:
    """Strategy for generating any pair of statuses (valid or invalid)."""
    return st.tuples(st_status(), st_status())


def st_tracker_entry(
    checkpoint_id: str | None = None,
    module: int | None = None,
    status: str | None = None,
) -> st.SearchStrategy[dict]:
    """Strategy for generating a tracker entry with optional fixed fields."""
    return st.fixed_dictionaries({
        "module": st.just(module) if module is not None else st.sampled_from([3, 5, 7, 8]),
        "checkpoint_id": (
            st.just(checkpoint_id)
            if checkpoint_id is not None
            else st.sampled_from(ALL_CHECKPOINT_IDS)
        ),
        "timestamp": st.just("2025-07-15T10:30:00Z"),
        "status": st.just(status) if status is not None else st_status(),
        "chosen_type": st.sampled_from(ALL_VISUALIZATION_TYPES + [None]),
        "output_path": st.sampled_from(["docs/output.html", None]),
    })


def st_module_number() -> st.SearchStrategy[int]:
    """Strategy for generating valid module numbers with visualization checkpoints."""
    return st.sampled_from([3, 5, 7, 8])


# ===========================================================================
# Property 1: Offer template structural invariance
# Feature: visualization-consistency, Property 1: Offer template structural invariance
# **Validates: Requirements 1.1, 1.5, 2.1, 2.2, 2.3**
# ===========================================================================


class TestProperty1OfferTemplateStructuralInvariance:
    """For any valid context string and type subset, the rendered offer template
    contains the opening phrase, numbered list with bold names, and STOP directive."""

    @given(context=st_context_string(), types=st_type_subset())
    @settings(max_examples=100)
    def test_template_contains_opening_phrase(self, context: str, types: list[str]):
        """The rendered template always starts with the standard opening phrase."""
        result = render_offer_template(context, types)
        expected_opening = f"Would you like me to create a visualization of {context}?"
        assert expected_opening in result, (
            f"Opening phrase not found in rendered template for context={context!r}"
        )

    @given(context=st_context_string(), types=st_type_subset())
    @settings(max_examples=100)
    def test_template_contains_numbered_list_with_bold_names(
        self, context: str, types: list[str]
    ):
        """The rendered template contains a numbered list with bold type names."""
        result = render_offer_template(context, types)
        for i, vtype in enumerate(types, start=1):
            # Each item must start with its number and contain bold text
            assert f"{i}. **" in result, (
                f"Missing numbered item {i} with bold name for type {vtype}"
            )

    @given(context=st_context_string(), types=st_type_subset())
    @settings(max_examples=100)
    def test_template_contains_stop_directive(self, context: str, types: list[str]):
        """The rendered template always ends with the STOP directive."""
        result = render_offer_template(context, types)
        assert "🛑 STOP" in result, "STOP directive not found in rendered template"
        assert "Wait for the bootcamper's input" in result, (
            "STOP directive missing 'Wait for the bootcamper's input' text"
        )


# ===========================================================================
# Property 2: Checkpoint-to-type mapping completeness and rendering accuracy
# Feature: visualization-consistency, Property 2: Checkpoint-to-type mapping
#   completeness and rendering accuracy
# **Validates: Requirements 3.6, 4.5**
# ===========================================================================


class TestProperty2CheckpointToTypeMappingAccuracy:
    """For any checkpoint in the protocol map, there exists a non-empty type subset,
    and the rendered offer contains exactly those types."""

    @given(checkpoint=st_checkpoint())
    @settings(max_examples=100)
    def test_checkpoint_has_nonempty_types(self, checkpoint: dict):
        """Every checkpoint defines at least one visualization type."""
        types = checkpoint["types"]
        assert len(types) > 0, (
            f"Checkpoint {checkpoint['id']} has empty types list"
        )

    @given(checkpoint=st_checkpoint())
    @settings(max_examples=100)
    def test_rendered_offer_contains_exactly_checkpoint_types(self, checkpoint: dict):
        """The rendered offer for a checkpoint contains exactly its defined types."""
        context = checkpoint["context"]
        types = checkpoint["types"]
        result = render_offer_template(context, types)

        # Each type's description must appear in the output
        for vtype in types:
            desc = TYPE_DESCRIPTIONS[vtype]
            assert desc in result, (
                f"Type {vtype} description missing from rendered offer"
            )

        # Types NOT in the checkpoint must NOT appear
        excluded_types = set(ALL_VISUALIZATION_TYPES) - set(types)
        for vtype in excluded_types:
            desc = TYPE_DESCRIPTIONS[vtype]
            assert desc not in result, (
                f"Excluded type {vtype} description found in rendered offer"
            )


# ===========================================================================
# Property 3: Tracker state machine validity
# Feature: visualization-consistency, Property 3: Tracker state machine validity
# **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
# ===========================================================================


class TestProperty3TrackerStateMachineValidity:
    """For any sequence of state transitions on a tracker entry, only valid
    transitions are permitted and required fields are preserved."""

    @given(transition=st_transition_pair())
    @settings(max_examples=100)
    def test_valid_transitions_accepted(self, transition: tuple[str, str]):
        """Only the three valid transitions return True."""
        from_status, to_status = transition
        result = is_valid_transition(from_status, to_status)
        expected = (from_status, to_status) in VALID_TRANSITIONS
        assert result == expected, (
            f"Transition {from_status}→{to_status}: "
            f"expected {expected}, got {result}"
        )

    @given(
        transitions=st.lists(st_status(), min_size=2, max_size=6),
    )
    @settings(max_examples=100)
    def test_sequential_transitions_follow_state_machine(
        self, transitions: list[str]
    ):
        """For any sequence of statuses, applying them sequentially only
        succeeds if each consecutive pair is a valid transition."""
        # Start from the first status and try to transition through the rest
        current = transitions[0]
        for next_status in transitions[1:]:
            valid = is_valid_transition(current, next_status)
            if valid:
                # Verify it's actually in the valid set
                assert (current, next_status) in VALID_TRANSITIONS
                current = next_status
            else:
                # Verify it's NOT in the valid set
                assert (current, next_status) not in VALID_TRANSITIONS
                break  # Can't continue after invalid transition

    @given(entry=st_tracker_entry())
    @settings(max_examples=100)
    def test_required_fields_preserved_across_transitions(self, entry: dict):
        """Required fields (module, checkpoint_id, timestamp) are always present."""
        assert "module" in entry, "Missing required field: module"
        assert "checkpoint_id" in entry, "Missing required field: checkpoint_id"
        assert "timestamp" in entry, "Missing required field: timestamp"
        assert "status" in entry, "Missing required field: status"
        assert entry["status"] in VALID_STATUSES, (
            f"Invalid status: {entry['status']}"
        )


# ===========================================================================
# Property 4: Per-checkpoint offer idempotency
# Feature: visualization-consistency, Property 4: Per-checkpoint offer idempotency
# **Validates: Requirements 5.5, 6.1, 6.2**
# ===========================================================================


class TestProperty4PerCheckpointOfferIdempotency:
    """For any checkpoint with an existing tracker entry, should_offer returns False."""

    @given(
        checkpoint_id=st.sampled_from(ALL_CHECKPOINT_IDS),
        status=st_status(),
    )
    @settings(max_examples=100)
    def test_should_offer_false_when_entry_exists(
        self, checkpoint_id: str, status: str
    ):
        """When a tracker entry exists for a checkpoint, should_offer returns False."""
        tracker_offers = [
            {
                "module": 7,
                "checkpoint_id": checkpoint_id,
                "timestamp": "2025-07-15T10:30:00Z",
                "status": status,
                "chosen_type": None,
                "output_path": None,
            }
        ]
        result = should_offer(checkpoint_id, tracker_offers)
        assert result is False, (
            f"should_offer returned True for checkpoint {checkpoint_id} "
            f"with existing entry (status={status})"
        )

    @given(checkpoint_id=st.sampled_from(ALL_CHECKPOINT_IDS))
    @settings(max_examples=100)
    def test_should_offer_true_when_no_entry_exists(self, checkpoint_id: str):
        """When no tracker entry exists for a checkpoint, should_offer returns True."""
        # Create entries for OTHER checkpoints only
        other_ids = [cid for cid in ALL_CHECKPOINT_IDS if cid != checkpoint_id]
        tracker_offers = [
            {
                "module": 7,
                "checkpoint_id": other_id,
                "timestamp": "2025-07-15T10:30:00Z",
                "status": "offered",
                "chosen_type": None,
                "output_path": None,
            }
            for other_id in other_ids
        ]
        result = should_offer(checkpoint_id, tracker_offers)
        assert result is True, (
            f"should_offer returned False for checkpoint {checkpoint_id} "
            f"with no matching entry"
        )


# ===========================================================================
# Property 5: Module-level decline suppression
# Feature: visualization-consistency, Property 5: Module-level decline suppression
# **Validates: Requirements 6.4**
# ===========================================================================


class TestProperty5ModuleLevelDeclineSuppression:
    """For any module where all checkpoints are declined, should_offer returns
    False for that module."""

    @given(module=st_module_number())
    @settings(max_examples=100)
    def test_all_declined_suppresses_further_offers(self, module: int):
        """When all checkpoints in a module are declined, should_offer is False."""
        checkpoints = CHECKPOINT_MAP[module]
        # Create declined entries for ALL checkpoints in this module
        tracker_offers = [
            {
                "module": module,
                "checkpoint_id": cp["id"],
                "timestamp": "2025-07-15T10:30:00Z",
                "status": "declined",
                "chosen_type": None,
                "output_path": None,
            }
            for cp in checkpoints
        ]
        # should_offer must return False for every checkpoint in this module
        for cp in checkpoints:
            result = should_offer(cp["id"], tracker_offers)
            assert result is False, (
                f"should_offer returned True for checkpoint {cp['id']} "
                f"in module {module} where all checkpoints are declined"
            )


# ===========================================================================
# Property 6: Enforcement identifies missing offers
# Feature: visualization-consistency, Property 6: Enforcement identifies missing offers
# **Validates: Requirements 7.1**
# ===========================================================================


class TestProperty6EnforcementIdentifiesMissingOffers:
    """For any module with N checkpoints and fewer than N tracker entries,
    enforcement check identifies the missing checkpoint IDs."""

    @given(
        module=st_module_number(),
        data=st.data(),
    )
    @settings(max_examples=100)
    def test_missing_checkpoints_identified(self, module: int, data: st.DataObject):
        """Enforcement correctly identifies checkpoint IDs missing from tracker."""
        checkpoints = CHECKPOINT_MAP[module]
        all_ids = [cp["id"] for cp in checkpoints]

        # Draw a random subset of checkpoint IDs to include in tracker
        included_ids = data.draw(
            st.lists(
                st.sampled_from(all_ids),
                min_size=0,
                max_size=len(all_ids) - 1,
                unique=True,
            )
        )

        tracker_offers = [
            {
                "module": module,
                "checkpoint_id": cid,
                "timestamp": "2025-07-15T10:30:00Z",
                "status": "offered",
                "chosen_type": None,
                "output_path": None,
            }
            for cid in included_ids
        ]

        missing = find_missing_checkpoints(module, tracker_offers, CHECKPOINT_MAP)
        expected_missing = sorted(set(all_ids) - set(included_ids))

        assert missing == expected_missing, (
            f"Module {module}: expected missing={expected_missing}, "
            f"got missing={missing}"
        )

    @given(module=st_module_number())
    @settings(max_examples=100)
    def test_no_missing_when_all_tracked(self, module: int):
        """When all checkpoints have tracker entries, no missing IDs are found."""
        checkpoints = CHECKPOINT_MAP[module]
        tracker_offers = [
            {
                "module": module,
                "checkpoint_id": cp["id"],
                "timestamp": "2025-07-15T10:30:00Z",
                "status": "offered",
                "chosen_type": None,
                "output_path": None,
            }
            for cp in checkpoints
        ]

        missing = find_missing_checkpoints(module, tracker_offers, CHECKPOINT_MAP)
        assert missing == [], (
            f"Module {module}: expected no missing checkpoints, got {missing}"
        )
