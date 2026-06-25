"""Doc-prose example tests for the hook-architecture steering document.

Validates that the real ``senzing-bootcamp/steering/hook-architecture.md``
steering file records the Theme A precedence/ordering decisions and the
Theme C capture-critical coverage statements specified by the design.

Requirements validated: 1.1, 1.2, 1.3, 2.2, 2.3, 3.1, 3.2, 3.3, 4.2, 8.6,
10.1, 10.5, 10.6

These are prose/example assertions (not property-based), so they use robust
case-insensitive substring checks against the rendered document rather than
brittle exact-line matches.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path to the steering document under test (resolved relative to this file).
# ---------------------------------------------------------------------------

_DOC_PATH: Path = (
    Path(__file__).resolve().parent.parent
    / "senzing-bootcamp"
    / "steering"
    / "hook-architecture.md"
)

# The exactly-five agentStop hook ids, highest precedence first.
_AGENTSTOP_HOOKS: tuple[str, ...] = (
    "ask-bootcamper",
    "module-recap-append",
    "module-completion-celebration",
    "enforce-gate-on-stop",
    "enforce-visualization-offers",
)

# The three capture-critical hooks.
_CAPTURE_CRITICAL: tuple[str, ...] = (
    "session-log-events",
    "module-recap-append",
    "ask-bootcamper",
)


def _read_doc() -> str:
    """Read the steering document once.

    Returns:
        The full text of hook-architecture.md.
    """
    assert _DOC_PATH.exists(), f"Steering file not found: {_DOC_PATH}"
    return _DOC_PATH.read_text(encoding="utf-8")


# Module-level read: the document is static during a test run.
_DOC: str = _read_doc()
_DOC_LOWER: str = _DOC.lower()


# ---------------------------------------------------------------------------
# TestHookArchitectureDoc
# ---------------------------------------------------------------------------


class TestHookArchitectureDoc:
    """Validate the hook-architecture.md steering document prose.

    **Validates: Requirements 1.1, 1.2, 1.3, 2.2, 2.3, 3.1, 3.2, 3.3, 4.2,
    8.6, 10.1, 10.5, 10.6**
    """

    @pytest.fixture(autouse=True)
    def _load_content(self) -> None:
        """Expose document content to every test in this class."""
        self.content: str = _DOC
        self.lower: str = _DOC_LOWER

    # -- Requirement 1.1 / 1.2: precedence list and semantics ---------------

    def test_records_all_five_agentstop_hook_ids(self) -> None:
        """Doc must name exactly the five agentStop hooks (Req 1.1)."""
        for hook_id in _AGENTSTOP_HOOKS:
            assert hook_id in self.content, (
                f"hook-architecture.md must record agentStop hook '{hook_id}' "
                "in its precedence list"
            )

    def test_records_precedence_order(self) -> None:
        """Doc must record the hooks in the intended precedence order (Req 1.1, 1.2).

        The five ids must appear in the document in their precedence order,
        highest first, so the ordered list is unambiguous.
        """
        positions = [self.content.find(hook_id) for hook_id in _AGENTSTOP_HOOKS]
        assert all(pos >= 0 for pos in positions), (
            "all five agentStop hook ids must appear in the document"
        )
        assert positions == sorted(positions), (
            "hook-architecture.md must list the agentStop hooks in precedence "
            f"order: {' > '.join(_AGENTSTOP_HOOKS)}"
        )

    def test_records_precedence_semantics(self) -> None:
        """Doc must describe the precedence semantics by role (Req 1.2)."""
        for phrase in (
            "answer-processing",
            "closing-question",
            "capture",
            "celebration",
            "gate enforcement",
            "visualization-offer enforcement",
        ):
            assert phrase.lower() in self.lower, (
                f"hook-architecture.md must describe precedence semantics "
                f"including '{phrase}'"
            )

    def test_references_machine_readable_agentstop_order(self) -> None:
        """Doc must point to the agentstop_order machine-readable source (Req 1.2/1.4)."""
        assert "agentstop_order" in self.content, (
            "hook-architecture.md must reference the 'agentstop_order' mapping"
        )
        assert "hook-categories.yaml" in self.content, (
            "hook-architecture.md must reference hook-categories.yaml as the "
            "machine-readable source"
        )

    # -- Requirement 1.3: per-hook rationale --------------------------------

    def test_records_per_hook_rationale_section(self) -> None:
        """Doc must contain a per-hook rationale section (Req 1.3)."""
        assert "rationale" in self.lower, (
            "hook-architecture.md must record a written rationale for hook "
            "precedence positions"
        )

    def test_records_rationale_for_each_hook(self) -> None:
        """Doc must justify each hook's position individually (Req 1.3).

        Each of the five hook ids should appear in the rationale section that
        follows the '## Per-Hook Rationale' heading.
        """
        marker = "per-hook rationale"
        idx = self.lower.find(marker)
        assert idx >= 0, "hook-architecture.md must have a Per-Hook Rationale section"
        rationale_section = self.content[idx:]
        for hook_id in _AGENTSTOP_HOOKS:
            assert hook_id in rationale_section, (
                f"Per-Hook Rationale section must justify the position of "
                f"'{hook_id}'"
            )

    # -- Requirement 2.2 / 2.3: closing-question ownership ------------------

    def test_records_closing_question_ownership(self) -> None:
        """Doc must name ask-bootcamper as closing-question owner (Req 2.2)."""
        assert "closing-question owner" in self.lower or (
            "ask-bootcamper" in self.content and "closing question" in self.lower
        ), (
            "hook-architecture.md must state ask-bootcamper is the "
            "closing-question owner"
        )
        assert "defer" in self.lower, (
            "hook-architecture.md must state other agentStop hooks defer "
            "closing-question emission to ask-bootcamper"
        )

    def test_records_conflict_resolution_favors_ask_bootcamper(self) -> None:
        """Doc must resolve precedence/ownership conflicts toward ask-bootcamper (Req 2.3)."""
        assert "conflict" in self.lower, (
            "hook-architecture.md must address conflict resolution"
        )
        assert "in favor of" in self.lower and "ask-bootcamper" in self.content, (
            "hook-architecture.md must resolve conflicts in favor of "
            "ask-bootcamper owning closing questions"
        )

    # -- Requirement 2.x: question-pending silence guard --------------------

    def test_records_question_pending_silence_rule(self) -> None:
        """Doc must state the question-pending silence rule."""
        assert "config/.question_pending" in self.content, (
            "hook-architecture.md must reference config/.question_pending"
        )
        assert "zero output" in self.lower or "no output" in self.lower, (
            "hook-architecture.md must state agentStop hooks emit no output "
            "while a question is pending"
        )

    # -- Requirement 3.1 / 3.2: single-winner precedence + example ----------

    def test_records_single_winner_precedence_rule(self) -> None:
        """Doc must define a single-winner precedence rule (Req 3.1).

        When more than one hook would emit, exactly one output takes precedence.
        """
        assert "takes precedence" in self.lower, (
            "hook-architecture.md must define which single hook's output takes "
            "precedence when multiple would emit"
        )
        assert "more than one" in self.lower or "multiple" in self.lower, (
            "hook-architecture.md must describe the multiple-emitters case"
        )

    def test_records_gate_violation_outranks_celebration(self) -> None:
        """Doc must record the gate-violation > celebration example (Req 3.2).

        enforce-gate-on-stop must be documented as outranking
        module-completion-celebration in the same turn.
        """
        gate_idx = self.content.find("enforce-gate-on-stop")
        celebration_idx = self.content.find("module-completion-celebration")
        assert gate_idx >= 0 and celebration_idx >= 0, (
            "both enforce-gate-on-stop and module-completion-celebration must "
            "appear in the document"
        )
        assert "gate-violation" in self.lower or "gate violation" in self.lower, (
            "hook-architecture.md must record the gate-violation example"
        )
        # The required example must mention both hooks together with precedence.
        assert (
            "enforce-gate-on-stop" in self.content
            and "module-completion-celebration" in self.content
            and ("outranks" in self.lower or "takes precedence" in self.lower)
        ), (
            "hook-architecture.md must state enforce-gate-on-stop outranks / "
            "takes precedence over module-completion-celebration"
        )

    # -- Requirement 3.3: no-stacking rule ----------------------------------

    def test_records_no_stacking_rule(self) -> None:
        """Doc must record the no-stacking rule (Req 3.3)."""
        assert "stack" in self.lower, (
            "hook-architecture.md must state hooks do not stack two separate "
            "end-of-turn messages"
        )
        assert "at most one" in self.lower, (
            "hook-architecture.md must state the turn carries at most one "
            "primary end-of-turn message"
        )

    # -- Requirement 4.2: cannot-control-order assumption -------------------

    def test_records_cannot_control_ide_order_assumption(self) -> None:
        """Doc must state the cannot-control-firing-order assumption (Req 4.2)."""
        assert "firing order" in self.lower, (
            "hook-architecture.md must state the power cannot control IDE-level "
            "firing order"
        )
        assert "cannot control" in self.lower, (
            "hook-architecture.md must state the power cannot control the IDE "
            "dispatch order"
        )

    def test_records_determinism_via_guards_and_precedence(self) -> None:
        """Doc must state determinism comes from guards + documented precedence (Req 4.2)."""
        assert "guard" in self.lower, (
            "hook-architecture.md must attribute determinism to per-hook guards"
        )
        assert "precedence" in self.lower, (
            "hook-architecture.md must attribute determinism to the documented "
            "precedence rule"
        )
        assert (
            "does not modify" in self.lower
            or "not modify" in self.lower
            or "no attempt" in self.lower
        ), (
            "hook-architecture.md must state it does not modify the IDE "
            "hook-execution engine"
        )

    # -- Requirement 8.6: sibling-script decision ---------------------------

    def test_records_sibling_script_decision(self) -> None:
        """Doc must record the sibling-script composer decision (Req 8.6)."""
        assert "compose_hook_prompts.py" in self.content, (
            "hook-architecture.md must name the compose_hook_prompts.py composer"
        )
        assert "sibling" in self.lower, (
            "hook-architecture.md must record the decision to implement "
            "composition as a sibling script"
        )
        assert "sync_hook_registry.py" in self.content, (
            "hook-architecture.md must contrast with sync_hook_registry.py"
        )

    def test_records_ci_verifiable_roundtrip_requirement(self) -> None:
        """Doc must require the CI-verifiable round-trip regardless of structure (Req 8.6)."""
        assert "--verify" in self.content, (
            "hook-architecture.md must reference the --verify CI round-trip"
        )

    # -- Requirement 10.1: capture-critical designation ---------------------

    def test_records_capture_critical_designation(self) -> None:
        """Doc must designate the three capture-critical hooks (Req 10.1)."""
        assert "capture-critical" in self.lower, (
            "hook-architecture.md must use the 'capture-critical' designation"
        )
        for hook_id in _CAPTURE_CRITICAL:
            assert hook_id in self.content, (
                f"hook-architecture.md must designate '{hook_id}' as "
                "capture-critical"
            )

    # -- Requirement 10.5: both-paths coverage ------------------------------

    def test_records_both_paths_coverage(self) -> None:
        """Doc must state capture-critical coverage on both install paths (Req 10.5)."""
        assert "both" in self.lower, (
            "hook-architecture.md must state coverage is required on both "
            "install paths"
        )
        assert "createhook" in self.lower, (
            "hook-architecture.md must mention the createHook-from-registry path"
        )
        assert "install_hooks.py" in self.content, (
            "hook-architecture.md must mention the install_hooks.py file-copy path"
        )

    # -- Requirement 10.6: warn-on-absence at session start -----------------

    def test_records_warn_on_absence_at_session_start(self) -> None:
        """Doc must state the session-start warn-on-absence behavior (Req 10.6)."""
        assert "session start" in self.lower or "session-start" in self.lower, (
            "hook-architecture.md must reference the session-start check"
        )
        assert "warn" in self.lower and "missing" in self.lower, (
            "hook-architecture.md must state the session-start check warns which "
            "capture-critical hooks are missing"
        )
