"""
Preservation property tests for bootcamp UX steering files.

These tests capture the baseline content of UNFIXED steering files.
They MUST pass on both unfixed and fixed code — any failure after the fix
indicates a regression in content that should have been preserved.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
"""

import os
import pytest

STEERING_DIR = os.path.join(
    os.path.dirname(__file__), "..", "senzing-bootcamp", "steering"
)


def _read(filename: str) -> str:
    path = os.path.join(STEERING_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# module-01-quick-demo.md — Preservation of module close & Module 2 transition
# ---------------------------------------------------------------------------

class TestModule01Preservation:
    """Preserve module close statement and Module 2 transition questions."""

    @pytest.fixture(autouse=True)
    def load_content(self):
        self.content = _read("module-01-quick-demo.md")

    def test_explicit_module_close_statement(self):
        """Module close text 'That's Module 1 complete!' must survive the fix."""
        assert "That's Module 1 complete!" in self.content

    def test_purpose_summary(self):
        """Purpose summary about verifying end-to-end system must survive."""
        assert (
            "The purpose of this demo was to verify that your entire system works end-to-end"
            in self.content
        )

    def test_module_completion_reference(self):
        """Reference to module-completion.md workflow must survive."""
        assert "module-completion.md" in self.content


    def test_module2_transition_contrast(self):
        """Module 2 transition contrast statement must survive."""
        assert (
            "Starting with Module 2, we shift to YOUR use case"
            in self.content
        )

    def test_discovery_question_record_types(self):
        """Use-case discovery question about record types must survive."""
        assert (
            "What kind of records do you work with"
            in self.content
        )

    def test_discovery_question_source_systems(self):
        """Use-case discovery question about source systems must survive."""
        assert (
            "How many distinct source systems or feeds will you be ingesting from?"
            in self.content
        )

    def test_discovery_question_duplicates(self):
        """Use-case discovery question about duplicates must survive."""
        assert (
            "What does a 'duplicate' look like in your world?"
            in self.content
        )


# ---------------------------------------------------------------------------
# module-transitions.md — Preservation of Step-Level Progress & Module Completion
# ---------------------------------------------------------------------------

class TestModuleTransitionsPreservation:
    """Preserve Step-Level Progress and Module Completion sections."""

    @pytest.fixture(autouse=True)
    def load_content(self):
        self.content = _read("module-transitions.md")

    def test_step_level_progress_section_exists(self):
        """Step-Level Progress section header must survive."""
        assert "## Step-Level Progress" in self.content

    def test_before_item(self):
        """Before item with 'Next up: [action]' must survive."""
        assert '**Before:** "Next up: [action]. This matters because [reason]."' in self.content

    def test_during_item(self):
        """During item with status update example must survive."""
        assert "**During:** Status updates describing what" in self.content

    def test_after_item(self):
        """After item about what changed must survive."""
        assert "**After:** What changed, what was produced, file paths." in self.content

    def test_module_completion_section_exists(self):
        """Module Completion section header must survive."""
        assert "## Module Completion" in self.content

    def test_module_completion_references_completion_file(self):
        """Module Completion section must reference module-completion.md."""
        assert "module-completion.md" in self.content


# ---------------------------------------------------------------------------
# module-completion.md — Preservation of journal, reflection, options, path
# ---------------------------------------------------------------------------

class TestModuleCompletionPreservation:
    """Preserve journal template, reflection, options, and path completion."""

    @pytest.fixture(autouse=True)
    def load_content(self):
        self.content = _read("module-completion.md")

    # Journal template fields
    def test_journal_field_what_we_did(self):
        """Journal template 'What we did' field must survive."""
        assert "**What we did:**" in self.content

    def test_journal_field_what_was_produced(self):
        """Journal template 'What was produced' field must survive."""
        assert "**What was produced:**" in self.content

    def test_journal_field_why_it_matters(self):
        """Journal template 'Why it matters' field must survive."""
        assert "**Why it matters:**" in self.content

    def test_journal_field_bootcamper_takeaway(self):
        """Journal template 'Bootcamper's takeaway' field must survive."""
        assert "**Bootcamper's takeaway:**" in self.content

    # Reflection question
    def test_reflection_question_emoji(self):
        """Reflection question must retain 👉 emoji."""
        assert "👉" in self.content

    def test_reflection_question_text(self):
        """Reflection question text must survive."""
        assert (
            "What's your main takeaway from this module"
            in self.content
        )

    # Next-step options: Proceed, Iterate, Share must survive
    # (Explore will be enhanced but not removed)
    def test_proceed_option(self):
        """Proceed option must survive."""
        assert "**Proceed:**" in self.content

    def test_iterate_option(self):
        """Iterate option must survive."""
        assert "**Iterate:**" in self.content

    def test_share_option(self):
        """Share option must survive."""
        assert "**Share:**" in self.content

    def test_explore_option_present(self):
        """Explore option must still be present (enhanced, not removed)."""
        assert "**Explore:**" in self.content

    # Path Completion Detection table
    def test_path_completion_detection_section(self):
        """Path Completion Detection section must survive."""
        assert "## Path Completion Detection" in self.content

    def test_path_a_in_table(self):
        """Path A row must survive in the table."""
        assert "| A" in self.content

    def test_path_b_in_table(self):
        """Path B row must survive in the table."""
        assert "| B" in self.content

    def test_path_c_in_table(self):
        """Path C row must survive in the table."""
        assert "| C" in self.content

    def test_path_d_in_table(self):
        """Path D row must survive in the table."""
        assert "| D" in self.content

    # Path Completion Celebration
    def test_celebration_section(self):
        """Path Completion Celebration section must survive."""
        assert "## Path Completion Celebration" in self.content

    def test_celebration_emoji(self):
        """Celebration 🎉 emoji must survive."""
        assert "🎉" in self.content


# ---------------------------------------------------------------------------
# onboarding-flow.md — Welcome banner must be untouched
# ---------------------------------------------------------------------------

class TestOnboardingFlowPreservation:
    """The 🎓 welcome banner must remain exactly as-is."""

    @pytest.fixture(autouse=True)
    def load_content(self):
        self.content = _read("onboarding-flow.md")

    def test_welcome_banner_text(self):
        """Welcome banner with 🎓 emojis must be untouched."""
        assert (
            "🎓🎓🎓  WELCOME TO THE SENZING BOOTCAMP!  🎓🎓🎓"
            in self.content
        )
