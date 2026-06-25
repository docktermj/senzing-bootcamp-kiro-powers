"""Integration tests for the write-policy-gate UX bugfix.

These tests exercise end-to-end *flows* over the live (fixed) gate prompt and
onboarding artifacts, rather than single-write decisions. They tie together
design Change A (the INTERNAL-FILE PASS-THROUGH clause) and design Change B
(the onboarding intercept-retry explanation) the way a bootcamper actually
encounters them:

1. A **step-checkpoint flow** that writes ``config/bootcamp_progress.json``
   repeatedly across a simulated module run — asserting NO corrective output
   and no "Rejected" message is produced for any checkpoint write.
2. A **mixed session** that interleaves routine internal-file writes with the
   governed writes the gate must still intercept (a Senzing-SQL write, a
   compound ``config/.question_pending`` write, and a feedback overwrite) —
   asserting internal writes pass silently while EVERY governed write is still
   intercepted with the correct corrective category.
3. The **onboarding flow placement** of the intercept-retry explanation —
   asserting it renders early (before the later onboarding sections) where a
   bootcamper would encounter it, not merely that the text exists.

The decision model reads the live hook prompt on every call, so these tests
validate the actually-shipped fixed artifacts.

**Validates: Requirements 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
"""

from __future__ import annotations

from pathlib import Path

from gate_decision_model import (
    FEEDBACK_FILE,
    INTERCEPT_CORRECTIVE,
    PASS_SILENT,
    GateDecision,
    WriteOperation,
    gate,
    is_bug_condition,
    load_gate_prompt,
    produces_rejected_message,
)

# ---------------------------------------------------------------------------
# Artifact paths
# ---------------------------------------------------------------------------

ONBOARDING_DOC: Path = Path("senzing-bootcamp/steering/onboarding-flow.md")


def _run_flow(ops: list[WriteOperation]) -> list[GateDecision]:
    """Run a sequence of writes through the live gate prompt.

    Args:
        ops: The ordered write operations issued during the simulated flow.

    Returns:
        The gate decision for each write, in order.
    """
    prompt = load_gate_prompt()
    return [gate(op, prompt) for op in ops]


# ===========================================================================
# Flow 1 — step-checkpoint progress writes produce no corrective noise
# ===========================================================================

class TestCheckpointFlowProducesNoNoise:
    """A repeated progress-checkpoint flow is completely silent.

    Simulates ``progress_utils.checkpoint`` writing
    ``config/bootcamp_progress.json`` at every step of a module run. Every
    write must complete silently (``PASS_SILENT``), be excluded from
    interception, and produce no "Rejected creation of ..." message.

    **Validates: Requirements 2.1, 2.2, 3.1, 3.6**
    """

    def _checkpoint_writes(self, steps: int = 25) -> list[WriteOperation]:
        """Build a run of progress checkpoint writes.

        Args:
            steps: Number of checkpoint writes to simulate.

        Returns:
            The ordered list of progress-file writes.
        """
        statuses = ["started", "in_progress", "done"]
        ops: list[WriteOperation] = []
        for step in range(1, steps + 1):
            status = statuses[step % len(statuses)]
            content = (
                '{"module": 3, "step": %d, "status": "%s", "completed": %s}'
                % (step, status, "true" if status == "done" else "false")
            )
            ops.append(
                WriteOperation(
                    path="config/bootcamp_progress.json",
                    content=content,
                    tool="fs_write",
                )
            )
        return ops

    def test_repeated_progress_checkpoints_are_silent(self) -> None:
        """No checkpoint write across the run produces corrective output.

        **Validates: Requirements 2.1, 2.2, 3.1**
        """
        ops = self._checkpoint_writes(steps=25)
        decisions = _run_flow(ops)

        # Every write is a genuine bug-condition (internal) write.
        for op in ops:
            assert is_bug_condition(op), (
                f"checkpoint write to '{op.path}' should be a bug-condition input"
            )

        # No corrective output is produced anywhere in the run.
        corrective = [d for d in decisions if d.outcome != PASS_SILENT]
        assert not corrective, (
            f"checkpoint flow produced corrective output on "
            f"{len(corrective)} of {len(decisions)} writes: "
            f"{[d.category for d in corrective]}"
        )

    def test_no_rejected_message_across_the_run(self) -> None:
        """No checkpoint write is intercepted, so no "Rejected" message shows.

        **Validates: Requirements 2.1, 2.2, 3.6**
        """
        decisions = _run_flow(self._checkpoint_writes(steps=25))
        rejected = [d for d in decisions if produces_rejected_message(d)]
        assert not rejected, (
            f"{len(rejected)} of {len(decisions)} checkpoint writes were held "
            f"(intercepted), producing the noisy 'Rejected' -> 'Accepted' pair"
        )
        # All writes are explicitly excluded from interception.
        assert all(d.intercepted is False for d in decisions)

    def test_member_scoped_checkpoint_flow_is_silent(self) -> None:
        """A colocated team-mode member checkpoint flow is equally silent.

        **Validates: Requirements 2.1, 2.2, 3.1**
        """
        ops = [
            WriteOperation(
                path="config/progress_alice.json",
                content='{"module": 2, "step": %d, "status": "done"}' % step,
                tool="fs_write",
            )
            for step in range(1, 16)
        ]
        decisions = _run_flow(ops)
        assert all(d.outcome == PASS_SILENT for d in decisions)
        assert not any(produces_rejected_message(d) for d in decisions)


# ===========================================================================
# Flow 2 — mixed session: internal writes silent, governed writes intercepted
# ===========================================================================

class TestMixedSessionFlow:
    """A realistic session mixing internal and governed writes.

    Internal bookkeeping writes are interleaved with the three governed write
    classes the gate must still intercept: a Senzing-SQL write, a compound
    ``config/.question_pending`` write, and a feedback-file overwrite. Internal
    writes must pass silently; every governed write must still be intercepted
    with the correct corrective category.

    **Validates: Requirements 2.1, 2.2, 3.1, 3.2, 3.3, 3.6**
    """

    def _session(
        self,
    ) -> list[tuple[str, WriteOperation, str, str | None]]:
        """Build the interleaved mixed-session timeline.

        Returns:
            A list of (label, op, expected_outcome, expected_category) tuples
            in the order they occur during the session.
        """
        return [
            (
                "internal_progress",
                WriteOperation(
                    "config/bootcamp_progress.json",
                    '{"module": 4, "step": 1, "status": "started"}',
                    "fs_write",
                ),
                PASS_SILENT,
                None,
            ),
            (
                "governed_sql",
                WriteOperation(
                    "src/query/run.py",
                    "SELECT * FROM RES_ENT WHERE ENTITY_ID > 0;",
                    "fs_write",
                ),
                INTERCEPT_CORRECTIVE,
                "senzing_sql",
            ),
            (
                "internal_preferences",
                WriteOperation(
                    "config/bootcamp_preferences.yaml",
                    "language: python\nverbosity: medium\n",
                    "fs_write",
                ),
                PASS_SILENT,
                None,
            ),
            (
                "governed_question",
                WriteOperation(
                    "config/.question_pending",
                    "Which language do you want, and should I enable hints?",
                    "fs_write",
                ),
                INTERCEPT_CORRECTIVE,
                "single_question",
            ),
            (
                "internal_member_progress",
                WriteOperation(
                    "config/progress_bob.json",
                    '{"module": 4, "step": 2, "status": "in_progress"}',
                    "fs_write",
                ),
                PASS_SILENT,
                None,
            ),
            (
                "governed_feedback_overwrite",
                WriteOperation(
                    FEEDBACK_FILE,
                    "completely rewritten feedback body",
                    "fs_write",
                ),
                INTERCEPT_CORRECTIVE,
                "feedback_append_only",
            ),
            (
                "internal_power_log",
                WriteOperation(
                    "docs/progress/MODULE_4_COMPLETE.md",
                    "# Module 4 complete\n\nGreat progress.\n",
                    "fs_write",
                ),
                PASS_SILENT,
                None,
            ),
        ]

    def test_each_write_matches_expected_outcome(self) -> None:
        """Every write in the session yields its expected outcome/category.

        **Validates: Requirements 2.1, 2.2, 3.1, 3.2, 3.3**
        """
        prompt = load_gate_prompt()
        for label, op, expected_outcome, expected_category in self._session():
            decision = gate(op, prompt)
            assert decision.outcome == expected_outcome, (
                f"[{label}] '{op.path}' expected {expected_outcome}, got "
                f"{decision.outcome} (category={decision.category})"
            )
            assert decision.category == expected_category, (
                f"[{label}] '{op.path}' expected category {expected_category}, "
                f"got {decision.category}"
            )

    def test_internal_writes_pass_silently(self) -> None:
        """All internal-file writes in the session pass silently, no "Rejected".

        **Validates: Requirements 2.1, 2.2**
        """
        prompt = load_gate_prompt()
        internal = [
            (label, op)
            for label, op, _, _ in self._session()
            if label.startswith("internal")
        ]
        assert internal, "session must contain internal-file writes"
        for label, op in internal:
            assert is_bug_condition(op), f"[{label}] should be a bug-condition write"
            decision = gate(op, prompt)
            assert decision.outcome == PASS_SILENT, (
                f"[{label}] internal write to '{op.path}' was not silent"
            )
            assert not produces_rejected_message(decision), (
                f"[{label}] internal write to '{op.path}' produced a 'Rejected' "
                f"message"
            )

    def test_every_governed_write_still_intercepted(self) -> None:
        """All governed writes remain intercepted with a corrective message.

        **Validates: Requirements 3.1, 3.2, 3.3, 3.6**
        """
        prompt = load_gate_prompt()
        governed = [
            (label, op, category)
            for label, op, _, category in self._session()
            if label.startswith("governed")
        ]
        assert governed, "session must contain governed writes"
        for label, op, category in governed:
            assert not is_bug_condition(op), (
                f"[{label}] governed write must never be a bug-condition input"
            )
            decision = gate(op, prompt)
            assert decision.outcome == INTERCEPT_CORRECTIVE, (
                f"[{label}] governed write to '{op.path}' was not intercepted"
            )
            assert decision.category == category, (
                f"[{label}] governed write expected category {category}, got "
                f"{decision.category}"
            )
            assert produces_rejected_message(decision), (
                f"[{label}] governed write should still be held (intercepted)"
            )

    def test_internal_and_governed_writes_are_partitioned(self) -> None:
        """Across the whole session, silent writes are exactly the internal
        writes and intercepted writes are exactly the governed writes.

        **Validates: Requirements 2.1, 2.2, 3.1, 3.6**
        """
        prompt = load_gate_prompt()
        silent: list[str] = []
        intercepted: list[str] = []
        for label, op, _, _ in self._session():
            decision = gate(op, prompt)
            if produces_rejected_message(decision):
                intercepted.append(label)
            else:
                silent.append(label)

        assert all(lbl.startswith("internal") for lbl in silent), (
            f"non-internal write passed without interception: {silent}"
        )
        assert all(lbl.startswith("governed") for lbl in intercepted), (
            f"internal write was intercepted: {intercepted}"
        )


# ===========================================================================
# Flow 3 — onboarding renders the intercept-retry explanation early
# ===========================================================================

class TestOnboardingExplanationPlacement:
    """The intercept-retry explanation renders early in the onboarding flow.

    Verifies not just presence but *placement/ordering*: a bootcamper meets the
    explanation near the start of onboarding (right after the setup preamble)
    and before the later onboarding sections (MCP health check, directory
    setup, prerequisites, language selection).

    **Validates: Requirements 2.3**
    """

    def _load_doc(self) -> str:
        """Load the onboarding documentation text.

        Returns:
            The onboarding-flow.md file contents.
        """
        with open(ONBOARDING_DOC, encoding="utf-8") as f:
            return f.read()

    def test_explanation_section_exists(self) -> None:
        """An explicit "Rejected"/"Accepted" explanation section is present.

        **Validates: Requirements 2.3**
        """
        doc = self._load_doc()
        idx = doc.find('Why You May See "Rejected"/"Accepted" Messages')
        assert idx != -1, (
            "onboarding-flow.md is missing the intercept-retry explanation "
            "section"
        )

    def test_explanation_appears_before_later_sections(self) -> None:
        """The explanation precedes MCP health check, directory setup, and
        prerequisites.

        **Validates: Requirements 2.3**
        """
        doc = self._load_doc()
        explanation_idx = doc.find(
            'Why You May See "Rejected"/"Accepted" Messages'
        )
        assert explanation_idx != -1, "explanation section not found"

        for later_marker in (
            "## 0b. MCP Health Check",
            "## 1. Directory Structure",
            "## 2. Prerequisite Check",
        ):
            later_idx = doc.find(later_marker)
            assert later_idx != -1, (
                f"expected onboarding section missing: {later_marker}"
            )
            assert explanation_idx < later_idx, (
                f"intercept-retry explanation must appear before "
                f"'{later_marker}' (explanation@{explanation_idx}, "
                f"section@{later_idx})"
            )

    def test_explanation_is_near_the_start(self) -> None:
        """The explanation sits in the first portion of the onboarding flow.

        A bootcamper encounters it early — within the opening setup phase,
        before the bulk of the onboarding content.

        **Validates: Requirements 2.3**
        """
        doc = self._load_doc()
        explanation_idx = doc.find(
            'Why You May See "Rejected"/"Accepted" Messages'
        )
        assert explanation_idx != -1, "explanation section not found"
        # It appears within the first third of the document — i.e., during the
        # opening setup phase rather than buried among later steps.
        assert explanation_idx < len(doc) // 3, (
            f"intercept-retry explanation is not early enough "
            f"(at char {explanation_idx} of {len(doc)})"
        )

    def test_explanation_follows_setup_preamble(self) -> None:
        """The explanation comes right after the setup preamble (Section 0).

        **Validates: Requirements 2.3**
        """
        doc = self._load_doc()
        preamble_idx = doc.find("## 0. Setup Preamble")
        explanation_idx = doc.find(
            'Why You May See "Rejected"/"Accepted" Messages'
        )
        assert preamble_idx != -1, "setup preamble section not found"
        assert explanation_idx != -1, "explanation section not found"
        assert preamble_idx < explanation_idx, (
            "intercept-retry explanation should follow the setup preamble"
        )

    def test_explanation_content_reassures_bootcamper(self) -> None:
        """The early explanation conveys the cycle is expected and harmless.

        **Validates: Requirements 2.3**
        """
        doc = self._load_doc()
        # Scope the assertions to the explanation section body.
        start = doc.find('Why You May See "Rejected"/"Accepted" Messages')
        end = doc.find("## 0b. MCP Health Check", start)
        section = doc[start:end].lower()
        assert "write-policy-gate" in section
        assert "succeed on retry" in section
        assert "no data is lost" in section
        assert "expected and harmless" in section
