"""Example/unit tests for the business_case_offer.py CLI and category set.

Feature: module1-business-case-offer

These are plain example tests (Hypothesis not required) covering the
machine-verifiable surface of the helper that is NOT exercised by the
property-based suite:

- the ``RECOGNIZED_CATEGORIES`` set equals exactly the 10 Module 1 categories;
- the ``validate`` CLI subcommand exits non-zero for an invalid artifact pair,
  exits zero for a valid pair, and degrades gracefully (no exception, non-zero
  exit) when an artifact file is missing;
- the shipped script embeds no CORD dataset names or record counts — the only
  allowed source of CORD facts is the MCP server at runtime.

Validates: Requirements 4.5, 5.4, 6.2
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make senzing-bootcamp/scripts/ importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from business_case_offer import (  # noqa: E402  (path manipulated above)
    RECOGNIZED_CATEGORIES,
    GeneratedScenario,
    ScenarioDataSource,
    main,
    record_data_sources,
    render_business_problem,
)

# The exact 10 use-case categories recognized by Module 1 (design Research Notes).
_EXPECTED_CATEGORIES = {
    "Customer 360",
    "Fraud Detection",
    "Data Migration",
    "Compliance",
    "Marketing",
    "Healthcare",
    "Supply Chain",
    "KYC",
    "Insurance",
    "Vendor MDM",
}


def _valid_scenario() -> GeneratedScenario:
    """Build a structurally valid, multi-source Generated_Scenario.

    Returns:
        A GeneratedScenario with two distinctly named sources, each carrying at
        least one record, a recognized category, and non-empty descriptions.
    """
    return GeneratedScenario(
        problem_description="Duplicate customers across CRM and billing systems.",
        use_case_category="Customer 360",
        success_definition="A single resolved customer view with no duplicates.",
        data_sources=[
            ScenarioDataSource(
                name="crm_export",
                fields=["full_name", "phone"],
                records=[{"full_name": "Ada Lovelace", "phone": "555-1234"}],
            ),
            ScenarioDataSource(
                name="billing_export",
                fields=["first_name", "last_name", "telephone"],
                records=[
                    {
                        "first_name": "Ada",
                        "last_name": "Lovelace",
                        "telephone": "5551234",
                    }
                ],
            ),
        ],
        provenance="generated",
        selected_pattern_category=None,
    )


class TestRecognizedCategories:
    """The recognized-category set pins exactly the 10 Module 1 categories."""

    def test_recognized_categories_set_equality(self) -> None:
        """RECOGNIZED_CATEGORIES equals exactly the 10 Module 1 categories.

        Validates: Requirements 2.2 (category set used by the CLI/validation).
        """
        assert set(RECOGNIZED_CATEGORIES) == _EXPECTED_CATEGORIES

    def test_recognized_categories_count(self) -> None:
        """There are exactly 10 recognized categories (no extras, no omissions)."""
        assert len(RECOGNIZED_CATEGORIES) == 10


class TestValidateCLI:
    """The `validate` subcommand reports invariants and exits accordingly."""

    def test_valid_pair_exits_zero(self, tmp_path: Path) -> None:
        """A valid business_problem.md + data_sources.yaml pair exits zero.

        Validates: Requirements 4.5, 5.4
        """
        scenario = _valid_scenario()
        business_problem = tmp_path / "business_problem.md"
        data_sources = tmp_path / "data_sources.yaml"
        business_problem.write_text(
            render_business_problem(scenario), encoding="utf-8"
        )
        data_sources.write_text(record_data_sources(scenario), encoding="utf-8")

        exit_code = main(
            [
                "validate",
                "--business-problem",
                str(business_problem),
                "--data-sources",
                str(data_sources),
            ]
        )
        assert exit_code == 0

    def test_invalid_pair_exits_nonzero(self, tmp_path: Path) -> None:
        """An invalid pair (no marker/sections, single source) exits non-zero.

        The business_problem.md is missing the generated marker and the required
        sections, and the registry records only a single source — violating the
        multi-source invariant.

        Validates: Requirements 4.5, 5.4
        """
        business_problem = tmp_path / "business_problem.md"
        data_sources = tmp_path / "data_sources.yaml"
        business_problem.write_text(
            "# Some unrelated document\n\nNothing useful here.\n", encoding="utf-8"
        )
        # Single-source scenario -> serialized registry has only one entry.
        single_source = GeneratedScenario(
            problem_description="x",
            use_case_category="Customer 360",
            success_definition="y",
            data_sources=[
                ScenarioDataSource(
                    name="only_source",
                    fields=["name"],
                    records=[{"name": "solo"}],
                )
            ],
            provenance="generated",
            selected_pattern_category=None,
        )
        data_sources.write_text(
            record_data_sources(single_source), encoding="utf-8"
        )

        exit_code = main(
            [
                "validate",
                "--business-problem",
                str(business_problem),
                "--data-sources",
                str(data_sources),
            ]
        )
        assert exit_code != 0

    def test_missing_files_exit_nonzero_gracefully(self, tmp_path: Path) -> None:
        """Missing artifacts are reported with a non-zero exit, no exception.

        Validates: Requirements 4.5, 5.4
        """
        missing_business = tmp_path / "does_not_exist.md"
        missing_sources = tmp_path / "missing.yaml"

        # Must not raise; degrades gracefully to a non-zero exit code.
        exit_code = main(
            [
                "validate",
                "--business-problem",
                str(missing_business),
                "--data-sources",
                str(missing_sources),
            ]
        )
        assert exit_code != 0


class TestNoCordFacts:
    """The shipped helper embeds no CORD dataset names or record counts."""

    def test_no_cord_dataset_names_in_source(self) -> None:
        """Known CORD dataset proper names do not appear in business_case_offer.py.

        CORD facts (dataset names, contents, counts) must come from the MCP
        server at runtime, never from training data baked into a shipped file.

        Validates: Requirements 6.2
        """
        source_path = (
            Path(__file__).resolve().parent.parent / "scripts" / "business_case_offer.py"
        )
        source_text = source_path.read_text(encoding="utf-8")

        forbidden = ["Las Vegas", "London", "Moscow"]
        present = [name for name in forbidden if name in source_text]
        assert not present, (
            f"CORD dataset names must not appear in business_case_offer.py; "
            f"found: {present}"
        )
