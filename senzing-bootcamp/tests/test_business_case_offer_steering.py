"""Steering-content example tests for the Module 1 Business Case Offer feature.

These are example (not property) tests. They parse the Module 1 discovery and
document-confirm steering files and assert that the Business_Case_Offer behavior is
surfaced as designed: the third selectable path in discovery, the offer text covering
both the "no case" and "won't/can't share" situations, realistic multi-source
generation, the Step 4 reference, the pre-generation 🛑 STOP marker, and the
decline / generation-failure / write-failure / downstream-missing-artifact /
CORD-unavailable branches.

Requirements validated: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.4, 2.5, 4.5, 5.4, 6.4
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths and file loading
# ---------------------------------------------------------------------------

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_PHASE1_PATH = _STEERING_DIR / "module-01-phase1-discovery.md"
_PHASE2_PATH = _STEERING_DIR / "module-01-phase2-document-confirm.md"


def _load(path: Path) -> str:
    """Read a steering file's full text.

    Args:
        path: Absolute path to the steering Markdown file.

    Returns:
        The file contents as a string.
    """
    return path.read_text(encoding="utf-8")


def _section(text: str, start_marker: str, end_marker: str) -> str:
    """Return the slice of ``text`` between two markers (case-insensitive search).

    Args:
        text: The full document text.
        start_marker: Substring marking the start of the section.
        end_marker: Substring marking the end of the section.

    Returns:
        The text between the markers (start inclusive, end exclusive). Falls back to
        the remainder of the document when the end marker is absent.
    """
    low = text.lower()
    start = low.find(start_marker.lower())
    assert start != -1, f"start marker not found: {start_marker!r}"
    rest = low.find(end_marker.lower(), start + len(start_marker))
    if rest == -1:
        return text[start:]
    return text[start:rest]


# ---------------------------------------------------------------------------
# TestDiscoverySteeringOffer — Step 4 / Step 5 offer presentation (1.1–1.6)
# ---------------------------------------------------------------------------


class TestDiscoverySteeringOffer:
    """Phase 1 discovery steering surfaces the Business_Case_Offer correctly."""

    def test_step5_presents_three_selectable_paths_including_offer(self) -> None:
        """Step 5 presents three selectable paths, one of which is the offer.

        Validates: Requirements 1.1, 1.5
        """
        step5 = _section(
            _load(_PHASE1_PATH),
            "5. **Discovery prompt**",
            "5a.",
        ).lower()

        # Three separately selectable paths are framed up front.
        assert "three" in step5
        assert "selectable" in step5

        # Path 1: describe a real business case.
        assert "describe a real business case" in step5
        # Path 2: adopt a design pattern.
        assert "adopt a design pattern" in step5
        # Path 3: the Business_Case_Offer itself.
        assert "business_case_offer" in step5

    def test_offer_text_covers_no_case_and_wont_share(self) -> None:
        """The offer text applies to both 'no case' and 'won't/can't share' situations.

        Validates: Requirements 1.2
        """
        step5 = _section(
            _load(_PHASE1_PATH),
            "5. **Discovery prompt**",
            "5a.",
        ).lower()

        # "no business case" situation.
        assert "no business case" in step5
        # "won't / can't share" situation (tolerant of either wording).
        assert ("won't share" in step5) or ("can't or won't share" in step5) or (
            "rather not share" in step5
        )

    def test_offer_describes_realistic_multi_source_generation(self) -> None:
        """The offer describes realistic, multi-source scenario generation.

        Validates: Requirements 1.3
        """
        step5 = _section(
            _load(_PHASE1_PATH),
            "5. **Discovery prompt**",
            "5a.",
        ).lower()

        assert "realistic" in step5
        assert "multi-source" in step5
        # The offer promises completion of the full bootcamp without inventing a case.
        assert "without supplying or inventing" in step5

    def test_step4_references_the_offer(self) -> None:
        """Step 4 (design pattern gallery) references the Business_Case_Offer path.

        Validates: Requirements 1.4
        """
        step4 = _section(
            _load(_PHASE1_PATH),
            "4. **If user wants to see patterns**",
            "5. **Discovery prompt**",
        ).lower()

        assert "business_case_offer" in step4
        # It is framed as a selectable path available in Step 5.
        assert "step 5" in step4

    def test_stop_marker_precedes_generation_in_step5(self) -> None:
        """A 🛑 STOP marker appears in Step 5 before any scenario is produced.

        Validates: Requirements 1.6
        """
        text = _load(_PHASE1_PATH)
        low = text.lower()

        step5_start = low.find("5. **discovery prompt**")
        assert step5_start != -1
        # The generation/acceptance handling lives in Step 5a.
        gen_start = low.find("5a.", step5_start)
        assert gen_start != -1

        # The STOP marker exists within Step 5, before the 5a generation branch.
        stop_idx = text.find("🛑 STOP", step5_start)
        assert stop_idx != -1, "🛑 STOP marker not found in Step 5"
        assert stop_idx < gen_start, "🛑 STOP must precede the generation branch"

        # The STOP explicitly forbids generating before explicit acceptance.
        step5 = text[step5_start:gen_start].lower()
        assert "do not generate a generated_scenario before" in step5


# ---------------------------------------------------------------------------
# TestDiscoverySteeringBranches — decline / failure / CORD branches (2.4, 2.5, 6.4)
# ---------------------------------------------------------------------------


class TestDiscoverySteeringBranches:
    """Phase 1 acceptance-handling branches behave as specified."""

    def test_decline_branch_continues_without_generated_doc(self) -> None:
        """Declining continues with the bootcamper's own description, no generated doc.

        Validates: Requirements 2.4
        """
        branch = _section(
            _load(_PHASE1_PATH),
            "**On decline**",
            "**On generation failure**",
        ).lower()

        # Continues with the bootcamper's own description.
        assert "own description" in branch
        # Does not produce a scenario and does not write a generated doc.
        assert "not" in branch and "generated_scenario" in branch
        assert "do **not** write a generated" in branch
        assert "business_problem.md" in branch

    def test_generation_failure_branch_informs_and_falls_back(self) -> None:
        """Generation failure informs the bootcamper and falls back without writing.

        Validates: Requirements 2.5
        """
        branch = _section(
            _load(_PHASE1_PATH),
            "**On generation failure**",
            "**Checkpoint:** Write step 5a",
        ).lower()

        # Informs the bootcamper a complete scenario could not be generated.
        assert "could not generate a complete scenario" in branch
        # Falls back to the bootcamper's own description.
        assert "fall back to the bootcamper's own description" in branch
        # Without writing a generated business_problem.md.
        assert "without" in branch
        assert "business_problem.md" in branch

    def test_cord_unavailable_message_present(self) -> None:
        """A CORD-unavailable-from-MCP message is present in the CORD-sourcing branch.

        Validates: Requirements 6.4
        """
        branch = _section(
            _load(_PHASE1_PATH),
            "5b.",
            "6. **Infer details from response**",
        ).lower()

        # Text indicating CORD details are unavailable from the MCP server.
        assert "cord details are unavailable from the mcp server" in branch


# ---------------------------------------------------------------------------
# TestRecordingSteering — Phase 2 Step 12 recording branches (4.5, 5.4)
# ---------------------------------------------------------------------------


class TestRecordingSteering:
    """Phase 2 Step 12 recording handles generated scenarios and failure modes."""

    def test_generated_marker_present(self) -> None:
        """Step 12 writes an observable bootcamp-generated marker.

        Validates: Requirements 1.6 (generated-scenario recording context)
        """
        step12 = _section(
            _load(_PHASE2_PATH),
            "12. **Create problem statement document**",
            "13. **Update README.md**",
        )

        assert "🤖 Bootcamp-generated business case" in step12

    def test_write_failure_branch_informs_which_artifact_failed(self) -> None:
        """The write-failure branch informs which artifact failed.

        Validates: Requirements 4.5
        """
        step12 = _section(
            _load(_PHASE2_PATH),
            "12. **Create problem statement document**",
            "13. **Update README.md**",
        ).lower()

        # Names both possible artifacts and indicates which one failed.
        assert "if writing an artifact fails" in step12
        assert "which" in step12 and "artifact failed" in step12
        assert "business_problem.md" in step12
        assert "data_sources.yaml" in step12
        # Does not proceed silently / informs the bootcamper.
        assert "inform the bootcamper" in step12

    def test_downstream_missing_artifact_branch_allows_real_data(self) -> None:
        """The downstream-missing-artifact branch informs and allows real data.

        Validates: Requirements 5.4
        """
        step12 = _section(
            _load(_PHASE2_PATH),
            "12. **Create problem statement document**",
            "13. **Update README.md**",
        ).lower()

        assert "missing or unreadable" in step12
        # Informs the bootcamper the generated data is unavailable.
        assert "generated_scenario data is unavailable" in step12
        # Allows supplying real data to proceed.
        assert "supply real data" in step12
