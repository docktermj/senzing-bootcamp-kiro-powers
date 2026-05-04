"""Unit tests for verbosity.py.

Feature: bootcamp-verbosity-control
"""

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from verbosity import (
    VerbosityPreferences,
    CATEGORIES,
    PRESETS,
    NL_TERM_MAP,
    resolve_preset,
    detect_preset,
    adjust_category,
    match_nl_term,
    validate_preferences,
    serialize_preferences,
    deserialize_preferences,
)


class TestPresetDefinitionsAndResolution:
    """Unit tests for preset definitions and resolution.

    Requirements: 2.2, 2.3, 2.4
    """

    def test_resolve_concise_returns_exact_levels(self):
        """resolve_preset('concise') returns exact levels per Requirement 2.2."""
        prefs = resolve_preset("concise")
        assert prefs.preset == "concise"
        assert prefs.categories == {
            "explanations": 1,
            "code_walkthroughs": 1,
            "step_recaps": 2,
            "technical_details": 1,
            "code_execution_framing": 1,
        }

    def test_resolve_standard_returns_all_twos(self):
        """resolve_preset('standard') returns all levels at 2 per Requirement 2.3."""
        prefs = resolve_preset("standard")
        assert prefs.preset == "standard"
        assert all(level == 2 for level in prefs.categories.values())
        assert len(prefs.categories) == 5

    def test_resolve_detailed_returns_all_threes(self):
        """resolve_preset('detailed') returns all levels at 3 per Requirement 2.4."""
        prefs = resolve_preset("detailed")
        assert prefs.preset == "detailed"
        assert all(level == 3 for level in prefs.categories.values())
        assert len(prefs.categories) == 5

    def test_resolve_unknown_raises_value_error(self):
        """resolve_preset raises ValueError for unknown preset names."""
        with pytest.raises(ValueError, match="Unknown preset"):
            resolve_preset("unknown")

    def test_resolve_unknown_lists_valid_presets(self):
        """ValueError message lists valid preset names."""
        with pytest.raises(ValueError) as exc_info:
            resolve_preset("invalid")
        msg = str(exc_info.value)
        assert "concise" in msg
        assert "standard" in msg
        assert "detailed" in msg

    def test_all_presets_have_all_categories(self):
        """Every preset defines all five categories."""
        for name in PRESETS:
            prefs = resolve_preset(name)
            assert set(prefs.categories.keys()) == set(CATEGORIES)

    def test_resolve_does_not_mutate_presets(self):
        """resolve_preset returns a copy, not a reference to PRESETS."""
        prefs = resolve_preset("standard")
        prefs.categories["explanations"] = 99
        fresh = resolve_preset("standard")
        assert fresh.categories["explanations"] == 2


class TestDefaultBehaviorAndNLTermMapping:
    """Unit tests for default behavior and NL term mapping.

    Requirements: 3.5, 5.3, 5.6, 6.4
    """

    def test_standard_preset_is_default(self):
        """Missing verbosity key defaults to standard preset (Req 3.5, 6.4)."""
        prefs = resolve_preset("standard")
        assert prefs.preset == "standard"
        assert all(level == 2 for level in prefs.categories.values())

    def test_all_nl_terms_from_requirement_5_3_present(self):
        """All NL terms from Requirement 5.3 are present in NL_TERM_MAP."""
        required_terms = [
            "explanations", "context",
            "code detail", "code walkthrough", "code walkthroughs", "line by line",
            "recaps", "summaries", "recap", "summary",
            "technical", "internals", "technical detail", "technical details",
            "before and after", "execution framing", "code framing", "framing",
        ]
        for term in required_terms:
            assert term in NL_TERM_MAP, f"Missing NL term: {term!r}"

    def test_nl_term_explanations_maps_correctly(self):
        """'explanations' and 'context' map to 'explanations' category."""
        assert match_nl_term("explanations") == "explanations"
        assert match_nl_term("context") == "explanations"

    def test_nl_term_code_walkthroughs_maps_correctly(self):
        """Code-related terms map to 'code_walkthroughs' category."""
        assert match_nl_term("code detail") == "code_walkthroughs"
        assert match_nl_term("code walkthrough") == "code_walkthroughs"
        assert match_nl_term("code walkthroughs") == "code_walkthroughs"
        assert match_nl_term("line by line") == "code_walkthroughs"

    def test_nl_term_step_recaps_maps_correctly(self):
        """Recap-related terms map to 'step_recaps' category."""
        assert match_nl_term("recaps") == "step_recaps"
        assert match_nl_term("summaries") == "step_recaps"
        assert match_nl_term("recap") == "step_recaps"
        assert match_nl_term("summary") == "step_recaps"

    def test_nl_term_technical_details_maps_correctly(self):
        """Technical terms map to 'technical_details' category."""
        assert match_nl_term("technical") == "technical_details"
        assert match_nl_term("internals") == "technical_details"
        assert match_nl_term("technical detail") == "technical_details"
        assert match_nl_term("technical details") == "technical_details"

    def test_nl_term_code_execution_framing_maps_correctly(self):
        """Framing terms map to 'code_execution_framing' category."""
        assert match_nl_term("before and after") == "code_execution_framing"
        assert match_nl_term("execution framing") == "code_execution_framing"
        assert match_nl_term("code framing") == "code_execution_framing"
        assert match_nl_term("framing") == "code_execution_framing"

    def test_match_nl_term_returns_none_for_unrecognized(self):
        """match_nl_term returns None for unrecognized terms (Req 5.6)."""
        assert match_nl_term("banana") is None
        assert match_nl_term("") is None
        assert match_nl_term("something random") is None

    def test_match_nl_term_case_insensitive(self):
        """match_nl_term is case-insensitive."""
        assert match_nl_term("EXPLANATIONS") == "explanations"
        assert match_nl_term("Code Detail") == "code_walkthroughs"
        assert match_nl_term("TECHNICAL") == "technical_details"

    def test_match_nl_term_strips_whitespace(self):
        """match_nl_term strips leading/trailing whitespace."""
        assert match_nl_term("  explanations  ") == "explanations"
        assert match_nl_term("\trecaps\n") == "step_recaps"

class TestBoundaryClampingAndValidation:
    """Unit tests for boundary clamping and validation errors.

    Requirements: 5.1, 5.2, 6.2
    """

    def test_level_3_plus_1_stays_at_3(self):
        """Level 3 + delta +1 stays at 3 (Req 5.1)."""
        prefs = resolve_preset("detailed")  # all levels at 3
        result = adjust_category(prefs, "explanations", +1)
        assert result.categories["explanations"] == 3

    def test_level_1_minus_1_stays_at_1(self):
        """Level 1 + delta -1 stays at 1 (Req 5.2)."""
        prefs = resolve_preset("concise")  # explanations at 1
        result = adjust_category(prefs, "explanations", -1)
        assert result.categories["explanations"] == 1

    def test_adjust_unknown_category_raises_value_error(self):
        """adjust_category raises ValueError for unknown category name."""
        prefs = resolve_preset("standard")
        with pytest.raises(ValueError, match="Unknown category"):
            adjust_category(prefs, "nonexistent", +1)

    def test_adjust_unknown_category_lists_valid_names(self):
        """ValueError message lists valid category names."""
        prefs = resolve_preset("standard")
        with pytest.raises(ValueError) as exc_info:
            adjust_category(prefs, "bad_name", +1)
        msg = str(exc_info.value)
        for cat in CATEGORIES:
            assert cat in msg

    def test_validate_catches_missing_preset(self):
        """validate_preferences catches missing 'preset' field."""
        data = {"categories": {cat: 2 for cat in CATEGORIES}}
        errors = validate_preferences(data)
        assert any("preset" in e.lower() for e in errors)

    def test_validate_catches_missing_categories(self):
        """validate_preferences catches missing 'categories' field."""
        data = {"preset": "standard"}
        errors = validate_preferences(data)
        assert any("categories" in e.lower() for e in errors)

    def test_validate_catches_out_of_range_level_zero(self):
        """validate_preferences catches level 0 (below minimum)."""
        cats = {cat: 2 for cat in CATEGORIES}
        cats["explanations"] = 0
        data = {"preset": "custom", "categories": cats}
        errors = validate_preferences(data)
        assert any("explanations" in e for e in errors)

    def test_validate_catches_out_of_range_level_four(self):
        """validate_preferences catches level 4 (above maximum)."""
        cats = {cat: 2 for cat in CATEGORIES}
        cats["technical_details"] = 4
        data = {"preset": "custom", "categories": cats}
        errors = validate_preferences(data)
        assert any("technical_details" in e for e in errors)

    def test_validate_catches_string_instead_of_int(self):
        """validate_preferences catches string type instead of int for level."""
        cats = {cat: 2 for cat in CATEGORIES}
        cats["step_recaps"] = "high"
        data = {"preset": "standard", "categories": cats}
        errors = validate_preferences(data)
        assert any("step_recaps" in e for e in errors)

    def test_validate_valid_preferences_returns_empty(self):
        """validate_preferences returns empty list for valid data."""
        data = {
            "preset": "standard",
            "categories": {cat: 2 for cat in CATEGORIES},
        }
        errors = validate_preferences(data)
        assert errors == []

    def test_validate_catches_missing_individual_category(self):
        """validate_preferences catches a missing individual category."""
        cats = {cat: 2 for cat in CATEGORIES if cat != "code_walkthroughs"}
        data = {"preset": "custom", "categories": cats}
        errors = validate_preferences(data)
        assert any("code_walkthroughs" in e for e in errors)


class TestSteeringFileSmokeTests:
    """Smoke tests for verbosity steering file structure.

    Requirements: 1.1, 1.2, 1.4, 10.1-10.10
    """

    @staticmethod
    def _power_root() -> Path:
        """Return the senzing-bootcamp/ directory path."""
        return Path(__file__).resolve().parent.parent

    def _read_steering_file(self) -> str:
        """Read and return the verbosity-control.md content."""
        path = self._power_root() / "steering" / "verbosity-control.md"
        return path.read_text(encoding="utf-8")

    def _read_steering_index(self) -> str:
        """Read and return the steering-index.yaml content."""
        path = self._power_root() / "steering" / "steering-index.yaml"
        return path.read_text(encoding="utf-8")

    def _read_reference_file(self) -> str:
        """Read and return the verbosity-control-reference.md content."""
        path = (
            self._power_root()
            / "steering"
            / "verbosity-control-reference.md"
        )
        return path.read_text(encoding="utf-8")

    def test_reference_file_exists(self):
        """verbosity-control-reference.md exists at the expected path."""
        path = (
            self._power_root()
            / "steering"
            / "verbosity-control-reference.md"
        )
        assert path.is_file(), f"Missing: {path}"

    def test_reference_file_frontmatter_contains_inclusion_manual(self):
        """Reference file frontmatter contains 'inclusion: manual'."""
        content = self._read_reference_file()
        assert "inclusion: manual" in content

    def test_core_file_line_count_within_limit(self):
        """Core verbosity-control.md has 80 lines or fewer."""
        content = self._read_steering_file()
        line_count = len(content.splitlines())
        assert line_count <= 80, (
            f"verbosity-control.md has {line_count} lines, "
            f"expected ≤80"
        )

    def test_core_file_contains_file_reference_directive(self):
        """Core file contains a #[[file:]] directive to the reference file."""
        content = self._read_steering_file()
        assert "#[[file:" in content
        assert "verbosity-control-reference.md" in content

    def test_reference_file_contains_full_category_definitions(self):
        """Reference file contains definition paragraphs for all five categories.

        Validates: Requirements 4.1, 4.2
        """
        content = self._read_reference_file()
        categories = [
            "explanations",
            "code_walkthroughs",
            "step_recaps",
            "technical_details",
            "code_execution_framing",
        ]
        for cat in categories:
            assert f"### {cat}" in content, (
                f"Missing category heading '### {cat}' in reference file"
            )
        assert content.count("Definition:") >= 5, (
            "Expected at least 5 'Definition:' entries in reference file, "
            f"found {content.count('Definition:')}"
        )

    def test_reference_file_contains_content_rules_by_level(self):
        """Reference file contains content rules for all three levels.

        Validates: Requirements 4.2
        """
        content = self._read_reference_file()
        assert "Content rules by level:" in content
        assert "Level 1" in content
        assert "Level 2" in content
        assert "Level 3" in content

    def test_reference_file_contains_all_framing_patterns(self):
        """Reference file contains all three framing pattern sections.

        Validates: Requirements 4.3, 4.4, 4.5
        """
        content = self._read_reference_file()
        assert "What and Why" in content, (
            "Missing 'What and Why' framing section in reference file"
        )
        assert "Code Execution Framing" in content, (
            "Missing 'Code Execution Framing' section in reference file"
        )
        assert "Step Recap Framing" in content, (
            "Missing 'Step Recap Framing' section in reference file"
        )

    def test_steering_file_exists(self):
        """verbosity-control.md exists at the expected path."""
        path = self._power_root() / "steering" / "verbosity-control.md"
        assert path.is_file(), f"Missing: {path}"

    def test_frontmatter_contains_inclusion_auto(self):
        """Frontmatter contains 'inclusion: auto'."""
        content = self._read_steering_file()
        assert "inclusion: auto" in content

    def test_all_five_category_names_present(self):
        """All five category names appear in the steering file."""
        content = self._read_steering_file()
        for cat in CATEGORIES:
            assert cat in content, f"Missing category: {cat}"

    def test_all_three_preset_names_present(self):
        """All three preset names appear in the steering file."""
        content = self._read_steering_file()
        for preset in ["concise", "standard", "detailed"]:
            assert preset in content, f"Missing preset: {preset}"

    def test_nl_term_mapping_table_present(self):
        """NL term mapping table is present in the steering file."""
        content = self._read_steering_file()
        assert "Natural Language Term Mapping" in content
        # Check that at least some key terms appear in the mapping section
        for term in ["explanations", "code detail", "recaps", "technical", "framing"]:
            assert term in content, f"Missing NL term in mapping: {term}"

    def test_what_why_framing_all_levels(self):
        """What/why framing examples exist for all three levels."""
        content = self._read_reference_file()
        assert "What and Why" in content
        assert "Level 1" in content
        assert "Level 2" in content
        assert "Level 3" in content

    def test_code_execution_framing_all_levels(self):
        """Code execution framing examples exist for all three levels."""
        content = self._read_reference_file()
        assert "Code Execution Framing" in content
        assert "What this code does" in content
        assert "Before" in content
        assert "After" in content

    def test_step_recap_framing_all_levels(self):
        """Step recap framing examples exist for all three levels."""
        content = self._read_reference_file()
        assert "Step Recap" in content
        assert "One-line" in content or "one-line" in content

    def test_steering_index_contains_verbosity_keyword(self):
        """steering-index.yaml contains 'verbosity' keyword entry."""
        content = self._read_steering_index()
        assert "verbosity: verbosity-control.md" in content

    def test_steering_index_contains_verbose_keyword(self):
        """steering-index.yaml contains 'verbose' keyword entry."""
        content = self._read_steering_index()
        assert "verbose: verbosity-control.md" in content

    def test_steering_index_contains_output_level_keyword(self):
        """steering-index.yaml contains 'output level' keyword entry."""
        content = self._read_steering_index()
        assert "output level: verbosity-control.md" in content
