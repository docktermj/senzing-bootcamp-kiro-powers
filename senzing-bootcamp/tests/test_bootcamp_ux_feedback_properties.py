"""Property-based tests for bootcamp UX feedback correctness properties.

Validates correctness properties for the visualization tracker schema,
specifically the delivery_mode field constraints defined in the design document.

Feature: bootcamp-ux-feedback
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Domain logic under test
# ---------------------------------------------------------------------------

_VALID_DELIVERY_MODES: set[str | None] = {"static", "web_service", None}


def validate_delivery_mode(value: str | None) -> bool:
    """Validate that a delivery_mode value is one of the accepted values.

    The visualization tracker schema allows only three valid values for the
    delivery_mode field: "static", "web_service", or None (null in JSON).

    Args:
        value: The delivery_mode value to validate.

    Returns:
        True if the value is valid, False otherwise.
    """
    return value in _VALID_DELIVERY_MODES


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_valid_delivery_mode() -> st.SearchStrategy[str | None]:
    """Strategy that produces only valid delivery_mode values.

    Returns:
        A strategy producing "static", "web_service", or None.
    """
    return st.sampled_from(["static", "web_service", None])


def st_arbitrary_delivery_mode() -> st.SearchStrategy[str | None]:
    """Strategy that produces arbitrary values including invalid ones.

    Generates a mix of valid delivery_mode values, random strings, empty
    strings, integers coerced to strings, and other edge cases to ensure
    the validator rejects everything except the three valid values.

    Returns:
        A strategy producing arbitrary string or None values.
    """
    return st.one_of(
        st.text(min_size=0, max_size=50),
        st.none(),
        st.sampled_from([
            "static", "web_service",  # valid
            "Static", "WEB_SERVICE", "STATIC", "Web_Service",  # wrong case
            "web-service", "webservice", "web service",  # wrong format
            " static", "static ", " web_service ",  # whitespace
            "", "null", "none", "undefined",  # common invalid
        ]),
    )


# ---------------------------------------------------------------------------
# Property-based test classes
# ---------------------------------------------------------------------------


class TestTrackerDeliveryModeValidity:
    """Feature: bootcamp-ux-feedback, Property 1: Tracker delivery_mode field validity

    For any visualization tracker entry, the delivery_mode field SHALL be one
    of: "static", "web_service", or null — no other values are valid.

    **Validates: Requirements 3.1**
    """

    @given(value=st_valid_delivery_mode())
    @settings(max_examples=100)
    def test_valid_delivery_modes_always_accepted(self, value: str | None) -> None:
        """All three valid delivery_mode values pass validation.

        Args:
            value: A valid delivery_mode drawn from the strategy.
        """
        assert validate_delivery_mode(value) is True, (
            f"Valid delivery_mode {value!r} was rejected"
        )

    @given(value=st.text(min_size=1, max_size=100).filter(
        lambda v: v not in ("static", "web_service")
    ))
    @settings(max_examples=100)
    def test_arbitrary_strings_rejected_unless_valid(self, value: str) -> None:
        """Any non-empty string that is not "static" or "web_service" is rejected.

        Args:
            value: An arbitrary non-empty string that is not a valid mode.
        """
        assert validate_delivery_mode(value) is False, (
            f"Invalid delivery_mode {value!r} was incorrectly accepted"
        )

    @given(value=st_arbitrary_delivery_mode())
    @settings(max_examples=100)
    def test_only_exact_valid_values_accepted(self, value: str | None) -> None:
        """Only the exact valid values pass; all others are rejected.

        Args:
            value: An arbitrary value drawn from a mixed strategy.
        """
        expected = value in _VALID_DELIVERY_MODES
        result = validate_delivery_mode(value)
        assert result == expected, (
            f"delivery_mode={value!r}: expected {expected}, got {result}"
        )


# ---------------------------------------------------------------------------
# Domain logic under test — offer creation
# ---------------------------------------------------------------------------

_VALID_MODULES: list[int] = [3, 5, 7, 8]


def create_offer_entry(module: int, checkpoint_id: str, timestamp: str) -> dict:
    """Create a new tracker entry with status "offered" and delivery_mode=None.

    When a visualization checkpoint is reached, a new offer entry is created
    in the tracker. At this point no delivery mode has been selected yet, so
    the field must be null.

    Args:
        module: The module number (3, 5, 7, or 8).
        checkpoint_id: The checkpoint identifier string.
        timestamp: ISO 8601 timestamp of when the offer was made.

    Returns:
        A dictionary representing the new tracker entry.
    """
    return {
        "module": module,
        "checkpoint_id": checkpoint_id,
        "timestamp": timestamp,
        "status": "offered",
        "chosen_type": None,
        "delivery_mode": None,
        "output_path": None,
    }


# ---------------------------------------------------------------------------
# Hypothesis strategies — offer creation
# ---------------------------------------------------------------------------


def st_module_number() -> st.SearchStrategy[int]:
    """Strategy that produces valid module numbers.

    Returns:
        A strategy producing one of 3, 5, 7, or 8.
    """
    return st.sampled_from(_VALID_MODULES)


def st_checkpoint_id() -> st.SearchStrategy[str]:
    """Strategy that produces random checkpoint_id strings.

    Generates identifiers resembling real checkpoint IDs (e.g.,
    "m7_exploratory_queries") using lowercase letters, digits, and
    underscores.

    Returns:
        A strategy producing non-empty checkpoint identifier strings.
    """
    return st.from_regex(r"m[0-9]_[a-z][a-z0-9_]{2,30}", fullmatch=True)


def st_iso8601_timestamp() -> st.SearchStrategy[str]:
    """Strategy that produces random ISO 8601 timestamp strings.

    Generates timestamps in the format "YYYY-MM-DDTHH:MM:SSZ" with
    realistic date/time ranges.

    Returns:
        A strategy producing ISO 8601 formatted timestamp strings.
    """
    return st.builds(
        lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        st.datetimes(
            min_value=__import__("datetime").datetime(2020, 1, 1),
            max_value=__import__("datetime").datetime(2030, 12, 31),
        ),
    )


# ---------------------------------------------------------------------------
# Property 2 test class
# ---------------------------------------------------------------------------


class TestNewOfferDeliveryModeNull:
    """Feature: bootcamp-ux-feedback, Property 2: New offer entries have null delivery_mode

    For any newly created tracker entry with status "offered", the
    delivery_mode field SHALL be null.

    **Validates: Requirements 3.2**
    """

    @given(
        module=st_module_number(),
        checkpoint_id=st_checkpoint_id(),
        timestamp=st_iso8601_timestamp(),
    )
    @settings(max_examples=100)
    def test_new_offer_entry_has_null_delivery_mode(
        self, module: int, checkpoint_id: str, timestamp: str
    ) -> None:
        """Every newly created offer entry must have delivery_mode=None.

        Args:
            module: A valid module number drawn from the strategy.
            checkpoint_id: A random checkpoint identifier.
            timestamp: A random ISO 8601 timestamp.
        """
        entry = create_offer_entry(module, checkpoint_id, timestamp)
        assert entry["delivery_mode"] is None, (
            f"New offer entry for module={module}, checkpoint={checkpoint_id!r} "
            f"has delivery_mode={entry['delivery_mode']!r} instead of None"
        )

    @given(
        module=st_module_number(),
        checkpoint_id=st_checkpoint_id(),
        timestamp=st_iso8601_timestamp(),
    )
    @settings(max_examples=100)
    def test_new_offer_entry_has_offered_status(
        self, module: int, checkpoint_id: str, timestamp: str
    ) -> None:
        """Every newly created offer entry must have status="offered".

        Args:
            module: A valid module number drawn from the strategy.
            checkpoint_id: A random checkpoint identifier.
            timestamp: A random ISO 8601 timestamp.
        """
        entry = create_offer_entry(module, checkpoint_id, timestamp)
        assert entry["status"] == "offered", (
            f"New offer entry has status={entry['status']!r} instead of 'offered'"
        )

    @given(
        module=st_module_number(),
        checkpoint_id=st_checkpoint_id(),
        timestamp=st_iso8601_timestamp(),
    )
    @settings(max_examples=100)
    def test_new_offer_entry_has_null_chosen_type(
        self, module: int, checkpoint_id: str, timestamp: str
    ) -> None:
        """Every newly created offer entry must have chosen_type=None.

        Args:
            module: A valid module number drawn from the strategy.
            checkpoint_id: A random checkpoint identifier.
            timestamp: A random ISO 8601 timestamp.
        """
        entry = create_offer_entry(module, checkpoint_id, timestamp)
        assert entry["chosen_type"] is None, (
            f"New offer entry has chosen_type={entry['chosen_type']!r} instead of None"
        )


# ---------------------------------------------------------------------------
# Domain logic under test — offer acceptance
# ---------------------------------------------------------------------------

_VALID_CHOSEN_TYPES: list[str] = [
    "Static_HTML_Report",
    "Interactive_D3_Graph",
    "Web_Service_Dashboard",
]

_VALID_NON_NULL_DELIVERY_MODES: list[str] = ["static", "web_service"]


def accept_offer(entry: dict, chosen_type: str, delivery_mode: str) -> dict:
    """Transition an offered entry to accepted, setting chosen_type and delivery_mode.

    When a bootcamper accepts a visualization offer, the tracker entry is
    updated with their chosen visualization type and delivery mode. The
    delivery_mode must be non-null after acceptance.

    Args:
        entry: A tracker entry dict with status "offered".
        chosen_type: The visualization type selected by the bootcamper.
        delivery_mode: The delivery mode selected ("static" or "web_service").

    Returns:
        The updated entry dict with status "accepted" and fields set.
    """
    entry["status"] = "accepted"
    entry["chosen_type"] = chosen_type
    entry["delivery_mode"] = delivery_mode
    return entry


# ---------------------------------------------------------------------------
# Hypothesis strategies — acceptance
# ---------------------------------------------------------------------------


def st_chosen_type() -> st.SearchStrategy[str]:
    """Strategy that produces valid chosen_type values.

    Returns:
        A strategy producing one of the three valid visualization types.
    """
    return st.sampled_from(_VALID_CHOSEN_TYPES)


def st_non_null_delivery_mode() -> st.SearchStrategy[str]:
    """Strategy that produces valid non-null delivery_mode values.

    Returns:
        A strategy producing "static" or "web_service".
    """
    return st.sampled_from(_VALID_NON_NULL_DELIVERY_MODES)


# ---------------------------------------------------------------------------
# Property 3 test class
# ---------------------------------------------------------------------------


class TestAcceptanceSetsDeliveryMode:
    """Feature: bootcamp-ux-feedback, Property 3: Acceptance sets delivery_mode

    For any tracker state transition from "offered" to "accepted", the
    resulting entry SHALL have delivery_mode set to the bootcamper's selected
    value ("static" or "web_service") — it SHALL NOT remain null.

    **Validates: Requirements 2.5, 3.3**
    """

    @given(
        module=st_module_number(),
        checkpoint_id=st_checkpoint_id(),
        timestamp=st_iso8601_timestamp(),
        chosen_type=st_chosen_type(),
        delivery_mode=st_non_null_delivery_mode(),
    )
    @settings(max_examples=100)
    def test_acceptance_sets_delivery_mode_to_input(
        self,
        module: int,
        checkpoint_id: str,
        timestamp: str,
        chosen_type: str,
        delivery_mode: str,
    ) -> None:
        """After acceptance, delivery_mode matches the selected value.

        Args:
            module: A valid module number drawn from the strategy.
            checkpoint_id: A random checkpoint identifier.
            timestamp: A random ISO 8601 timestamp.
            chosen_type: A random valid visualization type.
            delivery_mode: A random valid non-null delivery mode.
        """
        entry = create_offer_entry(module, checkpoint_id, timestamp)
        accepted = accept_offer(entry, chosen_type, delivery_mode)
        assert accepted["delivery_mode"] == delivery_mode, (
            f"Expected delivery_mode={delivery_mode!r}, "
            f"got {accepted['delivery_mode']!r}"
        )

    @given(
        module=st_module_number(),
        checkpoint_id=st_checkpoint_id(),
        timestamp=st_iso8601_timestamp(),
        chosen_type=st_chosen_type(),
        delivery_mode=st_non_null_delivery_mode(),
    )
    @settings(max_examples=100)
    def test_acceptance_delivery_mode_is_not_null(
        self,
        module: int,
        checkpoint_id: str,
        timestamp: str,
        chosen_type: str,
        delivery_mode: str,
    ) -> None:
        """After acceptance, delivery_mode is never null.

        Args:
            module: A valid module number drawn from the strategy.
            checkpoint_id: A random checkpoint identifier.
            timestamp: A random ISO 8601 timestamp.
            chosen_type: A random valid visualization type.
            delivery_mode: A random valid non-null delivery mode.
        """
        entry = create_offer_entry(module, checkpoint_id, timestamp)
        accepted = accept_offer(entry, chosen_type, delivery_mode)
        assert accepted["delivery_mode"] is not None, (
            f"delivery_mode is None after acceptance for "
            f"module={module}, checkpoint={checkpoint_id!r}"
        )

    @given(
        module=st_module_number(),
        checkpoint_id=st_checkpoint_id(),
        timestamp=st_iso8601_timestamp(),
        chosen_type=st_chosen_type(),
        delivery_mode=st_non_null_delivery_mode(),
    )
    @settings(max_examples=100)
    def test_acceptance_sets_status_to_accepted(
        self,
        module: int,
        checkpoint_id: str,
        timestamp: str,
        chosen_type: str,
        delivery_mode: str,
    ) -> None:
        """After acceptance, status transitions to "accepted".

        Args:
            module: A valid module number drawn from the strategy.
            checkpoint_id: A random checkpoint identifier.
            timestamp: A random ISO 8601 timestamp.
            chosen_type: A random valid visualization type.
            delivery_mode: A random valid non-null delivery mode.
        """
        entry = create_offer_entry(module, checkpoint_id, timestamp)
        accepted = accept_offer(entry, chosen_type, delivery_mode)
        assert accepted["status"] == "accepted", (
            f"Expected status='accepted', got {accepted['status']!r}"
        )


# ---------------------------------------------------------------------------
# Domain logic under test — delivery-mode skip logic
# ---------------------------------------------------------------------------


def resolve_delivery_mode(checkpoint_types: list[str]) -> str | None:
    """Resolve the delivery mode based on a checkpoint's available types.

    If the checkpoint only offers Static_HTML_Report, the delivery mode is
    automatically set to "static" without presenting the question to the
    bootcamper. Otherwise, returns None indicating the question should be asked.

    Args:
        checkpoint_types: List of visualization types available at the checkpoint.

    Returns:
        "static" if the checkpoint is static-only, None otherwise.
    """
    if checkpoint_types == ["Static_HTML_Report"]:
        return "static"
    return None


# ---------------------------------------------------------------------------
# Hypothesis strategies — checkpoint configuration
# ---------------------------------------------------------------------------


def st_checkpoint_types() -> st.SearchStrategy[list[str]]:
    """Strategy that produces random checkpoint type configurations.

    Generates lists of visualization types drawn from the valid set,
    including edge cases like single-element lists, multi-element lists,
    and empty lists.

    Returns:
        A strategy producing lists of valid visualization type strings.
    """
    return st.lists(
        st.sampled_from(_VALID_CHOSEN_TYPES),
        min_size=0,
        max_size=len(_VALID_CHOSEN_TYPES),
    )


def st_static_only_types() -> st.SearchStrategy[list[str]]:
    """Strategy that always produces the static-only configuration.

    Returns:
        A strategy producing ["Static_HTML_Report"].
    """
    return st.just(["Static_HTML_Report"])


# ---------------------------------------------------------------------------
# Property 4 test class
# ---------------------------------------------------------------------------


class TestStaticOnlyCheckpointDefault:
    """Feature: bootcamp-ux-feedback, Property 4: Static-only checkpoints default to static

    For any checkpoint whose available types list contains only
    Static_HTML_Report, the delivery_mode SHALL be set to "static" without
    presenting the delivery-mode question to the bootcamper.

    **Validates: Requirements 2.6**
    """

    @given(types=st_static_only_types())
    @settings(max_examples=100)
    def test_static_only_checkpoint_resolves_to_static(
        self, types: list[str]
    ) -> None:
        """When types == ["Static_HTML_Report"], delivery_mode is "static".

        Args:
            types: A checkpoint types list containing only Static_HTML_Report.
        """
        result = resolve_delivery_mode(types)
        assert result == "static", (
            f"Expected 'static' for types={types!r}, got {result!r}"
        )

    @given(types=st_checkpoint_types())
    @settings(max_examples=100)
    def test_any_config_with_only_static_defaults_to_static(
        self, types: list[str]
    ) -> None:
        """For any random config, if types == ["Static_HTML_Report"] then mode is "static".

        Args:
            types: A random list of visualization types.
        """
        result = resolve_delivery_mode(types)
        if types == ["Static_HTML_Report"]:
            assert result == "static", (
                f"Static-only checkpoint should resolve to 'static', got {result!r}"
            )
        else:
            assert result is None, (
                f"Non-static-only checkpoint types={types!r} should resolve to None, "
                f"got {result!r}"
            )

    @given(
        types=st.lists(
            st.sampled_from(_VALID_CHOSEN_TYPES),
            min_size=2,
            max_size=3,
        )
    )
    @settings(max_examples=100)
    def test_multi_type_checkpoint_does_not_default(
        self, types: list[str]
    ) -> None:
        """Checkpoints with multiple types never auto-default to static.

        Args:
            types: A list with at least 2 visualization types.
        """
        result = resolve_delivery_mode(types)
        assert result is None, (
            f"Multi-type checkpoint types={types!r} should not auto-default, "
            f"got {result!r}"
        )
