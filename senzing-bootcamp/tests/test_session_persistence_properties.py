"""Property-based tests for session persistence.

Feature: session-persistence
Covers correctness properties from the design document.
"""

import sys
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from preferences_utils import (
    KNOWN_TOP_LEVEL_KEYS,
    LANGUAGE_STEERING_MAP,
    VALID_MAPPING_VERBOSITY,
    format_context_reset,
    format_resume_summary,
    load_preferences,
    resolve_language_steering,
    validate_preferences_schema,
    write_preference,
)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Supported languages for the preference schema
_SUPPORTED_LANGUAGES: list[str] = ["python", "java", "csharp", "rust", "typescript"]

# Tracks used in the bootcamp
_TRACKS: list[str] = ["core_bootcamp", "advanced", "quick_start"]

# Verbosity levels
_VERBOSITY_LEVELS: list[str] = ["standard", "detailed", "concise"]

# Conversation style string values
_CONVERSATION_STYLES: list[str] = ["standard", "detailed", "concise", "custom"]

# Deployment targets
_DEPLOYMENT_TARGETS: list[str] = ["local", "cloud", "hybrid"]

# Cloud providers
_CLOUD_PROVIDERS: list[str] = ["aws", "azure", "gcp"]

# Database types
_DATABASE_TYPES: list[str] = ["sqlite", "postgresql", "mysql"]


def _st_safe_str():
    """Generate a safe non-empty string for preference values.

    Produces alphanumeric strings with underscores that won't cause
    YAML parsing issues.
    """
    return st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(
            whitelist_categories=("L", "N"),
            whitelist_characters="_-",
        ),
    )


@st.composite
def st_preference_key_value(draw):
    """Generate a random valid preference key-value pair from the schema.

    Returns a tuple of (key, value) where key is from the preference schema
    fields defined in Requirement 6.1 and value is an appropriate type for
    that key.

    **Validates: Requirements 6.1**
    """
    key = draw(st.sampled_from([
        "language",
        "track",
        "verbosity",
        "conversation_style",
        "deployment_target",
        "cloud_provider",
        "database_type",
        "mapping_verbosity",
        "hooks_installed",
        "pacing_overrides",
    ]))

    if key == "language":
        value = draw(st.sampled_from(_SUPPORTED_LANGUAGES))
    elif key == "track":
        value = draw(st.sampled_from(_TRACKS))
    elif key == "verbosity":
        value = draw(st.sampled_from(_VERBOSITY_LEVELS))
    elif key == "conversation_style":
        # Can be a string or a dict
        choice = draw(st.sampled_from(["string", "dict"]))
        if choice == "string":
            value = draw(st.sampled_from(_CONVERSATION_STYLES))
        else:
            # Dict with valid conversation_style sub-keys
            value = {}
            if draw(st.booleans()):
                value["verbosity_preset"] = draw(
                    st.sampled_from(["concise", "standard", "detailed", "custom"])
                )
            if draw(st.booleans()):
                value["question_framing"] = draw(
                    st.sampled_from(["minimal", "moderate", "full"])
                )
            if draw(st.booleans()):
                value["tone"] = draw(
                    st.sampled_from(["concise", "conversational", "detailed"])
                )
            if draw(st.booleans()):
                value["pacing"] = draw(
                    st.sampled_from(["one_concept_per_turn", "grouped_concepts"])
                )
            # Ensure at least one key is present
            if not value:
                value["tone"] = "conversational"
    elif key == "deployment_target":
        value = draw(st.sampled_from(_DEPLOYMENT_TARGETS))
    elif key == "cloud_provider":
        value = draw(st.sampled_from(_CLOUD_PROVIDERS))
    elif key == "database_type":
        value = draw(st.sampled_from(_DATABASE_TYPES))
    elif key == "mapping_verbosity":
        value = draw(st.sampled_from(list(VALID_MAPPING_VERBOSITY)))
    elif key == "hooks_installed":
        value = draw(
            st.lists(_st_safe_str(), min_size=1, max_size=5)
        )
    elif key == "pacing_overrides":
        # Dict of string keys to string or bool values
        keys = draw(
            st.lists(_st_safe_str(), min_size=1, max_size=3, unique=True)
        )
        value = {}
        for k in keys:
            value[k] = draw(st.one_of(_st_safe_str(), st.booleans()))
    else:
        value = draw(_st_safe_str())

    return (key, value)


@st.composite
def st_valid_preferences(draw):
    """Generate a complete valid preferences dict.

    Produces a dict with all or a subset of valid preference fields from
    the schema. Each field has an appropriate type and value.

    **Validates: Requirements 6.1**
    """
    result: dict = {}

    # Always include at least one field
    if draw(st.booleans()):
        result["language"] = draw(st.sampled_from(_SUPPORTED_LANGUAGES))
    if draw(st.booleans()):
        result["track"] = draw(st.sampled_from(_TRACKS))
    if draw(st.booleans()):
        result["verbosity"] = draw(st.sampled_from(_VERBOSITY_LEVELS))
    if draw(st.booleans()):
        choice = draw(st.sampled_from(["string", "dict"]))
        if choice == "string":
            result["conversation_style"] = draw(
                st.sampled_from(_CONVERSATION_STYLES)
            )
        else:
            style_dict: dict = {}
            if draw(st.booleans()):
                style_dict["verbosity_preset"] = draw(
                    st.sampled_from(["concise", "standard", "detailed", "custom"])
                )
            if draw(st.booleans()):
                style_dict["question_framing"] = draw(
                    st.sampled_from(["minimal", "moderate", "full"])
                )
            if draw(st.booleans()):
                style_dict["tone"] = draw(
                    st.sampled_from(["concise", "conversational", "detailed"])
                )
            if draw(st.booleans()):
                style_dict["pacing"] = draw(
                    st.sampled_from(["one_concept_per_turn", "grouped_concepts"])
                )
            if style_dict:
                result["conversation_style"] = style_dict
    if draw(st.booleans()):
        result["deployment_target"] = draw(st.sampled_from(_DEPLOYMENT_TARGETS))
    if draw(st.booleans()):
        result["cloud_provider"] = draw(st.sampled_from(_CLOUD_PROVIDERS))
    if draw(st.booleans()):
        result["database_type"] = draw(st.sampled_from(_DATABASE_TYPES))
    if draw(st.booleans()):
        result["mapping_verbosity"] = draw(
            st.sampled_from(list(VALID_MAPPING_VERBOSITY))
        )
    if draw(st.booleans()):
        result["hooks_installed"] = draw(
            st.lists(_st_safe_str(), min_size=0, max_size=5)
        )
    if draw(st.booleans()):
        keys = draw(
            st.lists(_st_safe_str(), min_size=1, max_size=3, unique=True)
        )
        result["pacing_overrides"] = {
            k: draw(st.one_of(_st_safe_str(), st.booleans())) for k in keys
        }

    # Ensure at least one field is present
    if not result:
        result["language"] = draw(st.sampled_from(_SUPPORTED_LANGUAGES))

    return result


@st.composite
def st_progress_state(draw):
    """Generate a valid progress state dict.

    Produces a dict with:
    - current_module: int from 1 to 11
    - current_step: str, int, or None

    **Validates: Requirements 4.1, 5.3**
    """
    module = draw(st.integers(min_value=1, max_value=11))
    step = draw(st.one_of(
        st.none(),
        st.integers(min_value=1, max_value=20),
        st.sampled_from([
            "introduction",
            "setup",
            "exercise",
            "review",
            "checkpoint",
            "summary",
        ]),
    ))
    return {"current_module": module, "current_step": step}


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestPropertyWriteRoundTrip:
    """Property 1: Preference Write Round-Trip.

    For any valid preference key-value pair, writing then reading back
    produces identical value.

    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 3.5, 6.5**
    """

    @given(kv=st_preference_key_value())
    @settings(max_examples=20)
    def test_write_then_read_produces_identical_value(self, kv):
        key, value = kv
        with tempfile.TemporaryDirectory() as tmp_dir:
            prefs_file = str(Path(tmp_dir) / "prefs.yaml")
            result = write_preference(key, value, preferences_path=prefs_file)
            assert result.success, f"Write failed: {result.error}"
            loaded = load_preferences(preferences_path=prefs_file)
            assert loaded.preferences is not None, f"Load failed: {loaded.error}"
            assert key in loaded.preferences, f"Key '{key}' not found after write"
            assert loaded.preferences[key] == value, (
                f"Round-trip mismatch for key '{key}': "
                f"wrote {value!r}, got {loaded.preferences[key]!r}"
            )


class TestPropertyFieldPreservation:
    """Property 2: Field Preservation on Update.

    For any valid preferences file with N fields, writing one field
    preserves all others unchanged.

    **Validates: Requirements 1.6, 6.3**
    """

    @given(prefs=st_valid_preferences(), kv=st_preference_key_value())
    @settings(max_examples=20)
    def test_writing_one_field_preserves_others(self, prefs, kv):
        with tempfile.TemporaryDirectory() as tmp_dir:
            prefs_file = str(Path(tmp_dir) / "prefs.yaml")

            # Write all initial preferences one by one
            for k, v in prefs.items():
                result = write_preference(k, v, preferences_path=prefs_file)
                assert result.success, f"Initial write of '{k}' failed: {result.error}"

            # Now write the new key-value pair
            new_key, new_value = kv
            result = write_preference(new_key, new_value, preferences_path=prefs_file)
            assert result.success, f"Update write failed: {result.error}"

            # Load and verify all original fields (except the updated one) are preserved
            loaded = load_preferences(preferences_path=prefs_file)
            assert loaded.preferences is not None, f"Load failed: {loaded.error}"

            for k, v in prefs.items():
                if k == new_key:
                    # This field was overwritten — should have the new value
                    assert loaded.preferences[k] == new_value
                else:
                    # This field should be preserved unchanged
                    assert loaded.preferences[k] == v, (
                        f"Field '{k}' was modified: expected {v!r}, "
                        f"got {loaded.preferences.get(k)!r}"
                    )


class TestPropertyNoNullFieldsWritten:
    """Property 3: No Null Fields Written.

    Writing None removes the key; writing non-None produces only
    non-None keys in file.

    **Validates: Requirements 6.2**
    """

    @given(kv=st_preference_key_value())
    @settings(max_examples=20)
    def test_writing_none_removes_key(self, kv):
        key, value = kv
        with tempfile.TemporaryDirectory() as tmp_dir:
            prefs_file = str(Path(tmp_dir) / "prefs.yaml")

            # First write a non-None value
            result = write_preference(key, value, preferences_path=prefs_file)
            assert result.success, f"Initial write failed: {result.error}"

            # Now write None to remove the key
            result = write_preference(key, None, preferences_path=prefs_file)
            assert result.success, f"None write failed: {result.error}"

            # Load and verify the key is absent
            loaded = load_preferences(preferences_path=prefs_file)
            if loaded.preferences is not None:
                assert key not in loaded.preferences, (
                    f"Key '{key}' still present after writing None"
                )

    @given(kv=st_preference_key_value())
    @settings(max_examples=20)
    def test_writing_non_none_produces_no_none_values(self, kv):
        key, value = kv
        with tempfile.TemporaryDirectory() as tmp_dir:
            prefs_file = str(Path(tmp_dir) / "prefs.yaml")

            result = write_preference(key, value, preferences_path=prefs_file)
            assert result.success, f"Write failed: {result.error}"

            loaded = load_preferences(preferences_path=prefs_file)
            assert loaded.preferences is not None, f"Load failed: {loaded.error}"

            # All values in the file should be non-None
            for k, v in loaded.preferences.items():
                assert v is not None, (
                    f"Key '{k}' has None value in file after writing non-None"
                )


class TestPropertySchemaValidationCorrectness:
    """Property 4: Schema Validation Correctness.

    Valid dicts produce zero errors; dicts with schema violations
    produce at least one error.

    **Validates: Requirements 6.1, 3.2, 6.4**
    """

    @given(prefs=st_valid_preferences())
    @settings(max_examples=20)
    def test_valid_dicts_produce_zero_errors(self, prefs):
        # Build a schema-valid dict: add required database_type and ensure
        # pacing_overrides is str (validator expects str, not dict)
        valid_prefs = dict(prefs)
        if "database_type" not in valid_prefs:
            valid_prefs["database_type"] = "sqlite"
        # The validator expects pacing_overrides to be str | None, but the
        # strategy generates dicts for write round-trip testing. Convert to
        # str for schema validation.
        if "pacing_overrides" in valid_prefs and isinstance(
            valid_prefs["pacing_overrides"], dict
        ):
            valid_prefs["pacing_overrides"] = "custom"
        errors = validate_preferences_schema(valid_prefs)
        assert errors == [], (
            f"Valid preferences produced errors: {errors}"
        )

    @given(prefs=st_valid_preferences())
    @settings(max_examples=20)
    def test_unknown_key_produces_error(self, prefs):
        # Add an unknown key to an otherwise valid dict
        invalid_prefs = dict(prefs)
        if "database_type" not in invalid_prefs:
            invalid_prefs["database_type"] = "sqlite"
        invalid_prefs["totally_unknown_key_xyz"] = "some_value"
        errors = validate_preferences_schema(invalid_prefs)
        assert len(errors) >= 1, (
            "Dict with unknown key should produce at least one error"
        )

    @given(prefs=st_valid_preferences())
    @settings(max_examples=20)
    def test_wrong_type_produces_error(self, prefs):
        # Set a string field to an invalid type (int where str expected)
        invalid_prefs = dict(prefs)
        if "database_type" not in invalid_prefs:
            invalid_prefs["database_type"] = "sqlite"
        # language must be str or None — set it to an int to violate schema
        invalid_prefs["language"] = 12345
        errors = validate_preferences_schema(invalid_prefs)
        assert len(errors) >= 1, (
            "Dict with wrong type should produce at least one error"
        )


# ---------------------------------------------------------------------------
# Property 5: Missing Required Field Detection
# ---------------------------------------------------------------------------


class TestMissingRequiredFieldDetection:
    """Property 5: Missing Required Field Detection.

    For any valid preferences dict with a random non-empty subset of required
    fields (language, track, verbosity) removed, the loader SHALL report exactly
    those removed fields as missing and preserve all other loaded values.

    **Validates: Requirements 3.3**
    """

    _REQUIRED_FIELDS = ("language", "track", "verbosity")

    @given(
        prefs=st_valid_preferences(),
        fields_to_remove=st.lists(
            st.sampled_from(["language", "track", "verbosity"]),
            min_size=1,
            max_size=3,
            unique=True,
        ),
    )
    @settings(max_examples=20)
    def test_missing_fields_detected(self, prefs, fields_to_remove):
        """Removing required fields reports exactly those fields as missing."""
        import os
        import tempfile

        # Ensure all required fields are present first
        prefs["language"] = "python"
        prefs["track"] = "core_bootcamp"
        prefs["verbosity"] = "standard"

        # Remove the selected subset
        for field in fields_to_remove:
            prefs.pop(field, None)

        # Write the remaining prefs to a temp file
        lines = []
        for key, value in prefs.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for sk, sv in value.items():
                    lines.append(f"  {sk}: {sv}")
            elif isinstance(value, list):
                if not value:
                    lines.append(f"{key}: []")
                else:
                    lines.append(f"{key}:")
                    for item in value:
                        lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: {value}")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write("\n".join(lines) + "\n")
            pref_path = f.name

        try:
            result = load_preferences(
                preferences_path=pref_path,
                required_fields=self._REQUIRED_FIELDS,
            )

            assert result.error is None
            assert set(result.missing_required) == set(fields_to_remove)
        finally:
            os.unlink(pref_path)


# ---------------------------------------------------------------------------
# Property 6: Language Steering Mapping
# ---------------------------------------------------------------------------


class TestLanguageSteeringMapping:
    """Property 6: Language Steering Mapping.

    Supported languages return non-None steering file; unsupported return None.

    **Validates: Requirements 2.4, 2.5**
    """

    @given(language=st.sampled_from(list(LANGUAGE_STEERING_MAP.keys())))
    @settings(max_examples=20)
    def test_supported_languages_return_steering_file(self, language):
        """Supported languages always return a non-None steering file name."""
        result = resolve_language_steering(language)
        assert result is not None
        assert result.endswith(".md")

    @given(
        language=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("L", "N")),
        ).filter(lambda s: s.lower() not in LANGUAGE_STEERING_MAP)
    )
    @settings(max_examples=20)
    def test_unsupported_languages_return_none(self, language):
        """Unsupported languages always return None."""
        result = resolve_language_steering(language)
        assert result is None


# ---------------------------------------------------------------------------
# Property 7: Session Resume Summary Format
# ---------------------------------------------------------------------------


class TestSessionResumeSummaryFormat:
    """Property 7: Session Resume Summary Format.

    For any language/track/verbosity, summary contains all three and is at
    most 2 sentences.

    **Validates: Requirements 2.2**
    """

    @given(
        language=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
        ),
        track=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
        ),
        verbosity=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
        ),
    )
    @settings(max_examples=20)
    def test_summary_contains_all_values_and_max_two_sentences(
        self, language, track, verbosity
    ):
        """Summary contains all three values and has at most 2 sentences."""
        summary = format_resume_summary(language, track, verbosity)

        # Must contain all three values
        assert language in summary
        assert track in summary
        assert verbosity in summary

        # At most 2 sentences (count sentence-ending periods)
        sentence_count = summary.count(". ") + (1 if summary.rstrip().endswith(".") else 0)
        assert sentence_count <= 2


# ---------------------------------------------------------------------------
# Property 8: Context Reset Message Completeness
# ---------------------------------------------------------------------------


class TestContextResetMessageCompleteness:
    """Property 8: Context Reset Message Completeness.

    For any valid progress state, message contains technical reason, immediacy,
    reassurance, continuation phrase, and module number.

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.7, 5.1, 5.2, 5.3**
    """

    @given(progress=st_progress_state())
    @settings(max_examples=20)
    def test_message_contains_all_required_elements(self, progress):
        """Context reset message contains all required elements."""
        import json
        import os
        import tempfile

        # Write progress state to a JSON file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(progress, f)
            progress_path = f.name

        try:
            # Generate the context reset message
            result = format_context_reset(progress_path=progress_path)
            msg = result.message

            # (a) Technical reason referencing conversation memory
            assert "memory" in msg.lower() or "conversation" in msg.lower()

            # (b) Immediacy statement
            assert "right now" in msg.lower() or "immediately" in msg.lower()

            # (c) Progress reassurance
            assert "saved" in msg.lower() or "progress" in msg.lower()

            # (d) Continuation phrase in quotation marks
            assert '"' in msg

            # (e) Module number present
            assert str(progress["current_module"]) in msg
        finally:
            os.unlink(progress_path)


# ---------------------------------------------------------------------------
# Property 9: Context Reset Message Constraints
# ---------------------------------------------------------------------------


class TestContextResetMessageConstraints:
    """Property 9: Context Reset Message Constraints.

    No forbidden temporal phrases, no question marks, at most 4 sentences.

    **Validates: Requirements 4.6, 5.2, 5.4**
    """

    @given(progress=st_progress_state())
    @settings(max_examples=20)
    def test_message_has_no_forbidden_phrases_no_questions_max_sentences(
        self, progress
    ):
        """Message has no forbidden phrases, no questions, max 4 sentences."""
        import json
        import os
        import tempfile

        # Write progress state to a JSON file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(progress, f)
            progress_path = f.name

        try:
            # Generate the context reset message
            result = format_context_reset(progress_path=progress_path)
            msg = result.message
            msg_lower = msg.lower()

            # No forbidden temporal phrases
            from preferences_utils import FORBIDDEN_TEMPORAL_PHRASES
            for phrase in FORBIDDEN_TEMPORAL_PHRASES:
                assert phrase not in msg_lower, (
                    f"Forbidden phrase '{phrase}' found in message"
                )

            # No question marks
            assert "?" not in msg, "Message must not contain question marks"

            # At most 4 sentences (split on '. ' and count terminal period)
            # Count sentences by splitting on period followed by space or end
            sentences = [s.strip() for s in msg.split(". ") if s.strip()]
            # The last segment may end with a period but not '. '
            assert len(sentences) <= 4, (
                f"Message has {len(sentences)} sentences, expected at most 4"
            )
        finally:
            os.unlink(progress_path)
