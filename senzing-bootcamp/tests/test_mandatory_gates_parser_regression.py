"""Regression test for the vacuous mandatory-gate validator (Group B).

This test invokes the validator's OWN parser (`parse_mandatory_gates`) against the
real shipped steering corpus and asserts it finds the non-empty set of gates that
actually ship. It encodes the EXPECTED (fixed) behavior:

    parse_mandatory_gates(steering/) returns a non-empty set of gates that includes
    Module 2 Step 5 (Configure License) and Module 3 Step 9 (Web Service + Visualization).

On the UNFIXED tree this test is EXPECTED TO FAIL: `_parse_gates_from_file`'s
`step_pattern = r"^###\\s+Step\\s+(\\d+):"` matches only H3 `### Step N:` headings,
while the shipped gates live under H2 `## Step N:` headings — Module 2 Step 5
(`module-02-sdk-setup.md`) and Module 3 Step 9 (`module-03-phase2-visualization.md`,
whose `> ⛔ **MANDATORY GATE` marker sits in a `## ⚠️ DO NOT SKIP` preamble ABOVE the
`## Step 9:` heading). The parser therefore returns zero gates and the CLI exits 0
vacuously (`No mandatory gates found in steering files.`).

The SAME test is reused to validate the fix once `validate_mandatory_gates.py` is
broadened to recognize H2 (and H3) `Step N:` headings plus the bold-blockquote marker
form. It must NOT pass on the unfixed tree.

Property 11: Bug Condition — B Non-Vacuous Gate Parsing

**Validates: Requirements 2.1, 2.2, 2.3**
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_mandatory_gates import MandatoryGate, parse_mandatory_gates  # noqa: E402

# ---------------------------------------------------------------------------
# Paths — the REAL shipped steering corpus
# ---------------------------------------------------------------------------

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"


class TestParserSeesShippedGates:
    """The validator's parser must see the gates that actually ship.

    These assertions encode the fixed behavior; on the unfixed (H3-only) parser
    they fail because it returns zero gates against the real corpus.
    """

    def test_steering_dir_exists(self) -> None:
        """The real steering directory ships with module files to scan."""
        assert _STEERING_DIR.is_dir(), f"Steering dir not found: {_STEERING_DIR}"
        assert list(_STEERING_DIR.glob("module-*.md")), "No module steering files found"

    def test_parser_finds_at_least_two_shipped_gates(self) -> None:
        """`parse_mandatory_gates` must find the non-empty shipped gate set.

        EXPECTED TO FAIL on the unfixed tree: the H3-only `step_pattern` matches
        neither H2-hosted shipped gate, so the parser returns an empty list.
        """
        gates = parse_mandatory_gates(_STEERING_DIR)
        assert len(gates) >= 2, (
            f"Expected at least 2 shipped mandatory gates, found {len(gates)}: "
            f"{[(g.module, g.step, g.source_file) for g in gates]}"
        )

    def test_module2_step5_gate_is_found(self) -> None:
        """Module 2 Step 5 (Configure License) is a shipped H2 mandatory gate.

        `module-02-sdk-setup.md` has `## Step 5: Configure License` immediately
        followed by `⛔ MANDATORY GATE — Never skip this step...`.
        """
        gates = parse_mandatory_gates(_STEERING_DIR)
        membership = {(g.module, g.step) for g in gates}
        assert (2, 5) in membership, (
            "Module 2 Step 5 (Configure License) mandatory gate not found; "
            f"parsed gates: {sorted(membership)}"
        )

    def test_module3_step9_gate_is_found(self) -> None:
        """Module 3 Step 9 (Web Service + Visualization) is a shipped H2 gate.

        `module-03-phase2-visualization.md` has `## Step 9: Web Service +
        Visualization Page`; its `> ⛔ **MANDATORY GATE` marker lives in the
        `## ⚠️ DO NOT SKIP` preamble above the Step 9 heading.
        """
        gates = parse_mandatory_gates(_STEERING_DIR)
        membership = {(g.module, g.step) for g in gates}
        assert (3, 9) in membership, (
            "Module 3 Step 9 (Web Service + Visualization) mandatory gate not found; "
            f"parsed gates: {sorted(membership)}"
        )

    def test_found_gates_are_mandatory_gate_instances(self) -> None:
        """Every parsed gate is a `MandatoryGate` carrying its source file."""
        gates = parse_mandatory_gates(_STEERING_DIR)
        for gate in gates:
            assert isinstance(gate, MandatoryGate)
            assert gate.source_file, "Gate is missing its source_file attribution"
