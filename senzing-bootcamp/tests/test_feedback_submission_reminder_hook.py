"""Unit tests for the feedback-submission-reminder hook.

Validates the hook's JSON structure, metadata, event types, and prompt
content against the behavioral requirements from the design document.

Correctness Properties (from design.md / requirements.md):
  1. Hook File Valid JSON with Required Keys (Example)
  2. Hook Event and Action Types (Example)
  3. Prompt Contains Feedback File Path (Example)
  4. Prompt Contains Track Completion Detection (Example)
  5. Prompt Contains Deduplication Check (Example)
  6. Prompt Contains Improvement Heading Pattern (Example)
  7. Prompt Contains No-Output Conditions (Example)
  8. Hook Name and Description Match Expected Values (Example)
"""

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers — locate and parse source-of-truth files
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent  # senzing-bootcamp/

HOOK_FILE = _REPO_ROOT / "hooks" / "feedback-submission-reminder.kiro.hook"


def _read_hook_json() -> dict:
    """Return the full parsed JSON from the hook file."""
    return json.loads(HOOK_FILE.read_text(encoding="utf-8"))


def _read_hook_prompt() -> str:
    """Return the ``then.prompt`` value from the hook JSON file."""
    return _read_hook_json()["then"]["prompt"]


# ---------------------------------------------------------------------------
# Property 1: Hook File Valid JSON with Required Keys (Example-based)
# Validates: Requirements 5.1, 5.2, 5.3
# ---------------------------------------------------------------------------


class TestHookFileStructure:
    """Property 1 — Hook file must be valid JSON with all required keys.

    **Validates: Requirements 5.1, 5.2, 5.3**
    """

    def test_hook_file_is_valid_json(self):
        """Hook file must parse as valid JSON without errors.

        **Validates: Requirements 5.1**
        """
        text = HOOK_FILE.read_text(encoding="utf-8")
        data = json.loads(text)
        assert isinstance(data, dict), "Hook file root must be a JSON object"

    def test_hook_file_has_required_keys(self):
        """Hook file must contain name, version, description, when, and then.

        **Validates: Requirements 5.1, 5.3**
        """
        data = _read_hook_json()
        required_keys = {"name", "version", "description", "when", "then"}
        missing = required_keys - set(data.keys())
        assert not missing, f"Hook JSON missing required keys: {missing}"


# ---------------------------------------------------------------------------
# Property 2: Hook Event and Action Types (Example-based)
# Validates: Requirements 5.1, 5.2
# ---------------------------------------------------------------------------


class TestHookEventAndActionTypes:
    """Property 2 — when.type must be agentStop and then.type must be askAgent.

    **Validates: Requirements 5.1, 5.2**
    """

    def test_when_type_is_agent_stop(self):
        """when.type must be 'agentStop'.

        **Validates: Requirements 5.1**
        """
        data = _read_hook_json()
        assert data["when"]["type"] == "agentStop", (
            f"Expected when.type='agentStop', got {data['when']['type']!r}"
        )

    def test_then_type_is_ask_agent(self):
        """then.type must be 'askAgent'.

        **Validates: Requirements 5.2**
        """
        data = _read_hook_json()
        assert data["then"]["type"] == "askAgent", (
            f"Expected then.type='askAgent', got {data['then']['type']!r}"
        )


# ---------------------------------------------------------------------------
# Property 3: Prompt Contains Feedback File Path (Example-based)
# Validates: Requirement 5.3
# ---------------------------------------------------------------------------


class TestPromptFeedbackFilePath:
    """Property 3 — Prompt must reference the feedback file path.

    **Validates: Requirement 5.3**
    """

    def test_prompt_contains_feedback_file_path(self):
        """Prompt must mention docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md.

        **Validates: Requirement 5.3**
        """
        prompt = _read_hook_prompt()
        assert "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md" in prompt, (
            "Prompt does not contain the feedback file path "
            "'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md'"
        )


# ---------------------------------------------------------------------------
# Property 4: Prompt Contains Track Completion Detection (Example-based)
# Validates: Requirement 5.2
# ---------------------------------------------------------------------------


class TestPromptTrackCompletionDetection:
    """Property 4 — Prompt must instruct scanning for track completion evidence.

    **Validates: Requirement 5.2**
    """

    def test_prompt_contains_track_completion_detection(self):
        """Prompt must contain instructions to detect track completion.

        **Validates: Requirement 5.2**
        """
        prompt = _read_hook_prompt()
        prompt_lower = prompt.lower()

        has_track_completion = any(
            term in prompt_lower
            for term in [
                "track completion",
                "path completion",
                "graduation completion",
            ]
        )
        assert has_track_completion, (
            "Prompt lacks track completion detection instructions.\n"
            f"Prompt: {prompt!r}"
        )


# ---------------------------------------------------------------------------
# Property 5: Prompt Contains Deduplication Check (Example-based)
# Validates: Requirement 5.5
# ---------------------------------------------------------------------------


class TestPromptDeduplicationCheck:
    """Property 5 — Prompt must check for the 📋 marker to avoid duplicates.

    **Validates: Requirement 5.5**
    """

    def test_prompt_contains_clipboard_emoji_marker(self):
        """Prompt must reference the 📋 emoji for deduplication.

        **Validates: Requirement 5.5**
        """
        prompt = _read_hook_prompt()
        assert "📋" in prompt, (
            "Prompt does not contain the 📋 deduplication marker"
        )

    def test_prompt_contains_deduplication_logic(self):
        """Prompt must instruct skipping if reminder was already shown.

        **Validates: Requirement 5.5**
        """
        prompt = _read_hook_prompt()
        prompt_lower = prompt.lower()

        has_dedup = any(
            term in prompt_lower
            for term in [
                "already presented",
                "already shown",
                "produce no output",
            ]
        )
        assert has_dedup, (
            "Prompt lacks deduplication logic instructions.\n"
            f"Prompt: {prompt!r}"
        )


# ---------------------------------------------------------------------------
# Property 6: Prompt Contains Improvement Heading Pattern (Example-based)
# Validates: Requirement 5.3
# ---------------------------------------------------------------------------


class TestPromptImprovementHeadingPattern:
    """Property 6 — Prompt must check for ## Improvement: headings.

    **Validates: Requirement 5.3**
    """

    def test_prompt_contains_improvement_heading(self):
        """Prompt must reference the '## Improvement:' heading pattern.

        **Validates: Requirement 5.3**
        """
        prompt = _read_hook_prompt()
        assert "## Improvement:" in prompt, (
            "Prompt does not contain the '## Improvement:' heading pattern"
        )


# ---------------------------------------------------------------------------
# Property 7: Prompt Contains No-Output Conditions (Example-based)
# Validates: Requirements 5.4, 5.5
# ---------------------------------------------------------------------------


class TestPromptNoOutputConditions:
    """Property 7 — Prompt must describe conditions that produce no output.

    **Validates: Requirements 5.4, 5.5**
    """

    def test_prompt_contains_no_output_instruction(self):
        """Prompt must instruct producing no output under certain conditions.

        **Validates: Requirements 5.4**
        """
        prompt = _read_hook_prompt()
        prompt_lower = prompt.lower()

        assert "produce no output" in prompt_lower, (
            "Prompt does not contain 'produce no output' instruction"
        )

    def test_prompt_has_multiple_no_output_conditions(self):
        """Prompt must have at least three no-output conditions.

        The three conditions are: (1) no track completion detected,
        (2) reminder already shown (deduplication), (3) no feedback file
        or no entries.

        **Validates: Requirements 5.4, 5.5**
        """
        prompt = _read_hook_prompt()
        no_output_count = prompt.lower().count("produce no output")
        assert no_output_count >= 3, (
            f"Expected at least 3 'produce no output' conditions, "
            f"found {no_output_count}"
        )


# ---------------------------------------------------------------------------
# Property 8: Hook Name and Description Match Expected Values (Example-based)
# Validates: Requirements 5.1, 5.3
# ---------------------------------------------------------------------------


class TestHookNameAndDescription:
    """Property 8 — Hook name and description must match expected values.

    **Validates: Requirements 5.1, 5.3**
    """

    def test_hook_name_matches(self):
        """name must be 'Feedback Submission Reminder'.

        **Validates: Requirement 5.1**
        """
        data = _read_hook_json()
        assert data["name"] == "Feedback Submission Reminder", (
            f"Expected name='Feedback Submission Reminder', got {data['name']!r}"
        )

    def test_hook_description_matches(self):
        """description must match the expected value from the design.

        **Validates: Requirement 5.3**
        """
        data = _read_hook_json()
        expected = (
            "After track completion or graduation, checks for saved feedback "
            "and reminds the bootcamper to share it with the power author."
        )
        assert data["description"] == expected, (
            f"Expected description={expected!r}, got {data['description']!r}"
        )


# ---------------------------------------------------------------------------
# Module-Completion Integration Tests
# ---------------------------------------------------------------------------

MODULE_COMPLETION_FILE = _REPO_ROOT / "steering" / "module-completion.md"


def _read_module_completion() -> str:
    """Return the full text of module-completion.md."""
    return MODULE_COMPLETION_FILE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Integration: Feedback Existence Check in Path Completion Celebration
# Validates: Requirements 1.4, 6.1
# ---------------------------------------------------------------------------


class TestModuleCompletionFeedbackExistenceCheck:
    """module-completion.md must contain the feedback existence check
    instructions inside the Path Completion Celebration section.

    **Validates: Requirements 1.4, 6.1**
    """

    def test_path_completion_section_contains_feedback_file_check(self):
        """The Path Completion Celebration section must instruct checking
        for docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md.

        **Validates: Requirement 6.1**
        """
        text = _read_module_completion()
        # Isolate the Path Completion Celebration section
        assert "## Path Completion Celebration" in text, (
            "module-completion.md is missing the '## Path Completion Celebration' section"
        )
        celebration_start = text.index("## Path Completion Celebration")
        celebration_section = text[celebration_start:]

        assert "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md" in celebration_section, (
            "Path Completion Celebration section does not reference the feedback file path"
        )

    def test_path_completion_section_contains_improvement_heading_check(self):
        """The section must instruct checking for '## Improvement:' headings
        to determine whether real feedback entries exist.

        **Validates: Requirement 6.1**
        """
        text = _read_module_completion()
        celebration_start = text.index("## Path Completion Celebration")
        celebration_section = text[celebration_start:]

        assert "## Improvement:" in celebration_section, (
            "Path Completion Celebration section does not reference "
            "the '## Improvement:' heading pattern for feedback detection"
        )

    def test_path_completion_section_contains_clipboard_reminder(self):
        """The section must contain the 📋 reminder prompt when feedback exists.

        **Validates: Requirement 6.1**
        """
        text = _read_module_completion()
        celebration_start = text.index("## Path Completion Celebration")
        celebration_section = text[celebration_start:]

        assert "📋" in celebration_section, (
            "Path Completion Celebration section does not contain the 📋 feedback reminder"
        )


# ---------------------------------------------------------------------------
# Integration: Feedback Reminder Ordering (after graduation, before lessons)
# Validates: Requirements 1.4, 6.3
# ---------------------------------------------------------------------------


class TestModuleCompletionFeedbackReminderOrdering:
    """The feedback reminder must appear after the graduation offer and
    before the lessons-learned retrospective load.

    **Validates: Requirements 1.4, 6.3**
    """

    def test_feedback_reminder_appears_after_graduation_offer(self):
        """The Feedback Submission Reminder block must come after the
        graduation offer sequence in the Path Completion Celebration section.

        **Validates: Requirement 1.4**
        """
        text = _read_module_completion()
        celebration_start = text.index("## Path Completion Celebration")
        celebration_section = text[celebration_start:]

        graduation_pos = celebration_section.find("Graduation offer")
        if graduation_pos == -1:
            graduation_pos = celebration_section.find("graduation offer")
        if graduation_pos == -1:
            graduation_pos = celebration_section.lower().find("skip_graduation")

        feedback_pos = celebration_section.find("Feedback Submission Reminder")

        assert graduation_pos != -1, (
            "Path Completion Celebration section does not contain a graduation offer"
        )
        assert feedback_pos != -1, (
            "Path Completion Celebration section does not contain "
            "'Feedback Submission Reminder'"
        )
        assert graduation_pos < feedback_pos, (
            "Feedback Submission Reminder must appear after the graduation offer, "
            f"but graduation offer is at position {graduation_pos} and "
            f"Feedback Submission Reminder is at position {feedback_pos}"
        )

    def test_feedback_reminder_appears_before_lessons_learned(self):
        """The feedback reminder must come before the lessons-learned
        retrospective load instruction.

        **Validates: Requirement 6.3**
        """
        text = _read_module_completion()
        celebration_start = text.index("## Path Completion Celebration")
        celebration_section = text[celebration_start:]

        feedback_pos = celebration_section.find("Feedback Submission Reminder")
        lessons_pos = celebration_section.find("lessons-learned")

        assert feedback_pos != -1, (
            "Path Completion Celebration section does not contain "
            "'Feedback Submission Reminder'"
        )
        assert lessons_pos != -1, (
            "Path Completion Celebration section does not reference lessons-learned"
        )
        assert feedback_pos < lessons_pos, (
            "Feedback Submission Reminder must appear before the lessons-learned load, "
            f"but Feedback Submission Reminder is at position {feedback_pos} and "
            f"lessons-learned is at position {lessons_pos}"
        )


# ---------------------------------------------------------------------------
# Integration: Sharing Instructions Include All Three Options
# Validates: Requirement 6.2
# ---------------------------------------------------------------------------


class TestModuleCompletionSharingInstructions:
    """The sharing instructions in module-completion.md must include all
    three options: email, GitHub issue, and copy path.

    **Validates: Requirement 6.2**
    """

    def test_sharing_instructions_include_email_option(self):
        """Sharing instructions must include the email option with
        support@senzing.com.

        **Validates: Requirement 6.2**
        """
        text = _read_module_completion()
        celebration_start = text.index("## Path Completion Celebration")
        celebration_section = text[celebration_start:]

        assert "support@senzing.com" in celebration_section, (
            "Sharing instructions do not include the email address support@senzing.com"
        )
        assert "Senzing Bootcamp Power Feedback" in celebration_section, (
            "Sharing instructions do not include the suggested email subject line"
        )

    def test_sharing_instructions_include_github_issue_option(self):
        """Sharing instructions must include the GitHub issue option.

        **Validates: Requirement 6.2**
        """
        text = _read_module_completion()
        celebration_start = text.index("## Path Completion Celebration")
        celebration_section = text[celebration_start:]

        assert "GitHub Issue" in celebration_section or "GitHub issue" in celebration_section, (
            "Sharing instructions do not include the GitHub issue option"
        )

    def test_sharing_instructions_include_copy_path_option(self):
        """Sharing instructions must include the copy-path option.

        **Validates: Requirement 6.2**
        """
        text = _read_module_completion()
        celebration_start = text.index("## Path Completion Celebration")
        celebration_section = text[celebration_start:]

        assert "Copy path" in celebration_section or "copy path" in celebration_section, (
            "Sharing instructions do not include the copy path option"
        )

    def test_no_automatic_external_actions(self):
        """Sharing instructions must explicitly prohibit automatic email
        sending or GitHub issue creation.

        **Validates: Requirement 6.2**
        """
        text = _read_module_completion()
        celebration_start = text.index("## Path Completion Celebration")
        celebration_section = text[celebration_start:].lower()

        has_no_auto = any(
            phrase in celebration_section
            for phrase in [
                "do not automatically send",
                "do not automatically create",
                "wait for explicit",
                "explicit bootcamper confirmation",
                "explicit confirmation",
            ]
        )
        assert has_no_auto, (
            "Sharing instructions do not explicitly prohibit automatic "
            "email sending or GitHub issue creation"
        )


# ---------------------------------------------------------------------------
# Integration: Non-Blocking Decline Behavior
# Validates: Requirements 6.1, 6.2
# ---------------------------------------------------------------------------


class TestModuleCompletionNonBlockingDecline:
    """The feedback reminder must describe non-blocking decline behavior:
    accept declining responses and do not re-prompt about feedback.

    **Validates: Requirements 6.1, 6.2**
    """

    def test_decline_responses_are_accepted(self):
        """The section must mention accepting decline responses such as
        'no', 'skip', or 'not now'.

        **Validates: Requirement 6.1**
        """
        text = _read_module_completion()
        celebration_start = text.index("## Path Completion Celebration")
        celebration_section = text[celebration_start:].lower()

        decline_terms_found = sum(
            1
            for term in ["no", "skip", "not now"]
            if term in celebration_section
        )
        assert decline_terms_found >= 2, (
            "The feedback reminder section does not describe accepting "
            "decline responses (expected at least 2 of: 'no', 'skip', 'not now')"
        )

    def test_no_re_prompting_after_decline(self):
        """The section must instruct not to re-prompt about feedback after
        the bootcamper declines.

        **Validates: Requirement 6.1**
        """
        text = _read_module_completion()
        celebration_start = text.index("## Path Completion Celebration")
        celebration_section = text[celebration_start:].lower()

        has_no_reprompt = any(
            phrase in celebration_section
            for phrase in [
                "without re-prompting",
                "do not ask about feedback sharing again",
                "don't ask about feedback again",
                "do not re-prompt",
            ]
        )
        assert has_no_reprompt, (
            "The feedback reminder section does not instruct against "
            "re-prompting about feedback after a decline"
        )


# ---------------------------------------------------------------------------
# Graduation Integration Tests
# ---------------------------------------------------------------------------

GRADUATION_FILE = _REPO_ROOT / "steering" / "graduation.md"


def _read_graduation() -> str:
    """Return the full text of graduation.md."""
    return GRADUATION_FILE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Integration: Feedback Existence Check in Graduation Report Section
# Validates: Requirements 4.1, 7.1
# ---------------------------------------------------------------------------


class TestGraduationFeedbackExistenceCheck:
    """graduation.md must contain the feedback existence check instructions
    after the graduation complete message.

    **Validates: Requirements 4.1, 7.1**
    """

    def test_graduation_contains_feedback_file_check(self):
        """The Graduation Report section must instruct checking for
        docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md.

        **Validates: Requirement 4.1**
        """
        text = _read_graduation()
        assert "## Graduation Report" in text, (
            "graduation.md is missing the '## Graduation Report' section"
        )
        report_start = text.index("## Graduation Report")
        report_section = text[report_start:]

        assert "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md" in report_section, (
            "Graduation Report section does not reference the feedback file path"
        )

    def test_graduation_contains_improvement_heading_check(self):
        """The section must instruct checking for '## Improvement:' headings
        to determine whether real feedback entries exist.

        **Validates: Requirement 4.1**
        """
        text = _read_graduation()
        report_start = text.index("## Graduation Report")
        report_section = text[report_start:]

        assert "## Improvement:" in report_section, (
            "Graduation Report section does not reference "
            "the '## Improvement:' heading pattern for feedback detection"
        )

    def test_graduation_contains_clipboard_reminder(self):
        """The section must contain the 📋 reminder prompt when feedback exists.

        **Validates: Requirement 7.1**
        """
        text = _read_graduation()
        report_start = text.index("## Graduation Report")
        report_section = text[report_start:]

        assert "📋" in report_section, (
            "Graduation Report section does not contain the 📋 feedback reminder"
        )


# ---------------------------------------------------------------------------
# Integration: Graduation Feedback Reminder Ordering
# Validates: Requirements 4.2, 7.2
# ---------------------------------------------------------------------------


class TestGraduationFeedbackReminderOrdering:
    """The feedback reminder must appear after the graduation complete
    message and before the existing 'Say "bootcamp feedback"' line.

    **Validates: Requirements 4.2, 7.2**
    """

    def test_feedback_reminder_appears_after_graduation_complete(self):
        """The Feedback Submission Reminder block must come after the
        '🎓 Graduation complete!' message.

        **Validates: Requirement 7.2**
        """
        text = _read_graduation()
        report_start = text.index("## Graduation Report")
        report_section = text[report_start:]

        graduation_complete_pos = report_section.find("Graduation complete!")
        feedback_reminder_pos = report_section.find("Feedback Submission Reminder")

        assert graduation_complete_pos != -1, (
            "Graduation Report section does not contain 'Graduation complete!' message"
        )
        assert feedback_reminder_pos != -1, (
            "Graduation Report section does not contain 'Feedback Submission Reminder'"
        )
        assert graduation_complete_pos < feedback_reminder_pos, (
            "Feedback Submission Reminder must appear after 'Graduation complete!', "
            f"but graduation complete is at position {graduation_complete_pos} and "
            f"Feedback Submission Reminder is at position {feedback_reminder_pos}"
        )

    def test_feedback_reminder_appears_before_say_bootcamp_feedback(self):
        """The feedback reminder must come before the existing
        'Say "bootcamp feedback"' fallback line.

        **Validates: Requirement 7.2**
        """
        text = _read_graduation()
        report_start = text.index("## Graduation Report")
        report_section = text[report_start:]

        feedback_reminder_pos = report_section.find("Feedback Submission Reminder")
        say_feedback_pos = report_section.find('Say "bootcamp feedback"')

        assert feedback_reminder_pos != -1, (
            "Graduation Report section does not contain 'Feedback Submission Reminder'"
        )
        assert say_feedback_pos != -1, (
            "Graduation Report section does not contain "
            "'Say \"bootcamp feedback\"' fallback line"
        )
        assert feedback_reminder_pos < say_feedback_pos, (
            "Feedback Submission Reminder must appear before 'Say \"bootcamp feedback\"', "
            f"but Feedback Submission Reminder is at position {feedback_reminder_pos} and "
            f"'Say \"bootcamp feedback\"' is at position {say_feedback_pos}"
        )

    def test_say_bootcamp_feedback_fallback_retained(self):
        """The existing 'Say "bootcamp feedback"' line must be retained
        as a fallback for bootcampers without saved feedback.

        **Validates: Requirement 7.3**
        """
        text = _read_graduation()
        assert 'Say "bootcamp feedback"' in text, (
            "graduation.md no longer contains the 'Say \"bootcamp feedback\"' "
            "fallback line — it must be retained per Requirement 7.3"
        )


# ---------------------------------------------------------------------------
# Integration: Graduation Deduplication Check
# Validates: Requirements 4.3, 7.1
# ---------------------------------------------------------------------------


class TestGraduationDeduplicationCheck:
    """graduation.md must include a deduplication check to skip the feedback
    reminder if it was already shown during track completion.

    **Validates: Requirements 4.3, 7.1**
    """

    def test_deduplication_references_clipboard_marker(self):
        """The deduplication check must reference the 📋 marker to detect
        whether a reminder was already shown.

        **Validates: Requirement 4.3**
        """
        text = _read_graduation()
        report_start = text.index("## Graduation Report")
        report_section = text[report_start:]

        # The 📋 marker must appear in the context of deduplication
        assert "📋" in report_section, (
            "Graduation Report section does not reference the 📋 marker "
            "for deduplication"
        )

    def test_deduplication_instructs_skip_if_already_shown(self):
        """The section must instruct skipping the reminder if it was
        already shown during track completion.

        **Validates: Requirement 4.3**
        """
        text = _read_graduation()
        report_start = text.index("## Graduation Report")
        report_section = text[report_start:].lower()

        has_skip_logic = any(
            phrase in report_section
            for phrase in [
                "already appears",
                "already shown",
                "skip this reminder",
                "already presented",
            ]
        )
        assert has_skip_logic, (
            "Graduation Report section does not instruct skipping the "
            "feedback reminder if it was already shown during track completion"
        )

    def test_deduplication_references_conversation_history(self):
        """The deduplication check must reference conversation history
        as the source for detecting prior reminders.

        **Validates: Requirement 4.3**
        """
        text = _read_graduation()
        report_start = text.index("## Graduation Report")
        report_section = text[report_start:].lower()

        assert "conversation" in report_section, (
            "Graduation Report section does not reference conversation "
            "history for deduplication"
        )


# ---------------------------------------------------------------------------
# Integration: Graduation Sharing Instructions
# Validates: Requirements 4.4, 7.1
# ---------------------------------------------------------------------------


class TestGraduationSharingInstructions:
    """The sharing instructions in graduation.md must include all three
    options: email, GitHub issue, and copy path.

    **Validates: Requirements 4.4, 7.1**
    """

    def test_sharing_instructions_include_email_option(self):
        """Sharing instructions must include the email option with
        support@senzing.com.

        **Validates: Requirement 4.4**
        """
        text = _read_graduation()
        report_start = text.index("## Graduation Report")
        report_section = text[report_start:]

        assert "support@senzing.com" in report_section, (
            "Graduation sharing instructions do not include "
            "the email address support@senzing.com"
        )

    def test_sharing_instructions_include_github_issue_option(self):
        """Sharing instructions must include the GitHub issue option.

        **Validates: Requirement 4.4**
        """
        text = _read_graduation()
        report_start = text.index("## Graduation Report")
        report_section = text[report_start:]

        assert "GitHub Issue" in report_section or "GitHub issue" in report_section, (
            "Graduation sharing instructions do not include the GitHub issue option"
        )

    def test_sharing_instructions_include_copy_path_option(self):
        """Sharing instructions must include the copy-path option.

        **Validates: Requirement 4.4**
        """
        text = _read_graduation()
        report_start = text.index("## Graduation Report")
        report_section = text[report_start:]

        assert "Copy path" in report_section or "copy path" in report_section, (
            "Graduation sharing instructions do not include the copy path option"
        )

    def test_no_automatic_external_actions(self):
        """Sharing instructions must explicitly prohibit automatic email
        sending or GitHub issue creation.

        **Validates: Requirement 4.4**
        """
        text = _read_graduation()
        report_start = text.index("## Graduation Report")
        report_section = text[report_start:].lower()

        has_no_auto = any(
            phrase in report_section
            for phrase in [
                "do not automatically send",
                "do not automatically create",
                "wait for explicit",
                "explicit bootcamper confirmation",
                "explicit confirmation",
            ]
        )
        assert has_no_auto, (
            "Graduation sharing instructions do not explicitly prohibit "
            "automatic email sending or GitHub issue creation"
        )


# ---------------------------------------------------------------------------
# Integration: Graduation Non-Blocking Decline Behavior
# Validates: Requirements 4.3, 7.1
# ---------------------------------------------------------------------------


class TestGraduationNonBlockingDecline:
    """The graduation feedback reminder must describe non-blocking decline
    behavior: accept declining responses and do not re-prompt.

    **Validates: Requirements 4.3, 7.1**
    """

    def test_decline_responses_are_accepted(self):
        """The section must mention accepting decline responses such as
        'no', 'skip', or 'not now'.

        **Validates: Requirement 4.3**
        """
        text = _read_graduation()
        report_start = text.index("## Graduation Report")
        report_section = text[report_start:].lower()

        decline_terms_found = sum(
            1
            for term in ["no", "skip", "not now"]
            if term in report_section
        )
        assert decline_terms_found >= 2, (
            "The graduation feedback reminder does not describe accepting "
            "decline responses (expected at least 2 of: 'no', 'skip', 'not now')"
        )

    def test_no_re_prompting_after_decline(self):
        """The section must instruct not to re-prompt about feedback after
        the bootcamper declines.

        **Validates: Requirement 4.3**
        """
        text = _read_graduation()
        report_start = text.index("## Graduation Report")
        report_section = text[report_start:].lower()

        has_no_reprompt = any(
            phrase in report_section
            for phrase in [
                "without re-prompting",
                "proceed without re-prompting",
                "do not re-prompt",
                "don't re-prompt",
            ]
        )
        assert has_no_reprompt, (
            "The graduation feedback reminder does not instruct against "
            "re-prompting about feedback after a decline"
        )


# ---------------------------------------------------------------------------
# Hook Registry Consistency Integration Tests
# ---------------------------------------------------------------------------

REGISTRY_FILE = _REPO_ROOT / "steering" / "hook-registry.md"
CATEGORIES_FILE = _REPO_ROOT / "hooks" / "hook-categories.yaml"
STEERING_INDEX_FILE = _REPO_ROOT / "steering" / "steering-index.yaml"


def _read_registry() -> str:
    """Return the full text of hook-registry.md."""
    return REGISTRY_FILE.read_text(encoding="utf-8")


def _read_categories() -> str:
    """Return the full text of hook-categories.yaml."""
    return CATEGORIES_FILE.read_text(encoding="utf-8")


def _read_steering_index() -> str:
    """Return the full text of steering-index.yaml."""
    return STEERING_INDEX_FILE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Integration: Hook Registry Contains feedback-submission-reminder
# Validates: Requirements 5.1, 5.2, 5.3
# ---------------------------------------------------------------------------


class TestHookRegistryEntry:
    """hook-registry.md must contain a feedback-submission-reminder entry
    under the Critical Hooks section.

    **Validates: Requirements 5.1, 5.2, 5.3**
    """

    def test_registry_contains_hook_id(self):
        """hook-registry.md must contain the feedback-submission-reminder id.

        **Validates: Requirement 5.1**
        """
        text = _read_registry()
        assert "feedback-submission-reminder" in text, (
            "hook-registry.md does not contain 'feedback-submission-reminder'"
        )

    def test_registry_entry_under_critical_hooks(self):
        """feedback-submission-reminder must appear under the Critical Hooks section.

        **Validates: Requirement 5.1**
        """
        text = _read_registry()
        critical_start = text.index("## Critical Hooks")
        # Find the Module Hooks section to bound the critical section
        module_start = text.index("## Module Hooks")
        critical_section = text[critical_start:module_start]

        assert "feedback-submission-reminder" in critical_section, (
            "feedback-submission-reminder is not listed under the "
            "'## Critical Hooks' section in hook-registry.md"
        )

    def test_registry_entry_has_id_field(self):
        """The registry entry must include '- id: `feedback-submission-reminder`'.

        **Validates: Requirement 5.1**
        """
        text = _read_registry()
        assert "- id: `feedback-submission-reminder`" in text, (
            "hook-registry.md lacks '- id: `feedback-submission-reminder`' field"
        )

    def test_registry_entry_has_agent_stop_type(self):
        """The registry entry must indicate agentStop → askAgent.

        **Validates: Requirement 5.2**
        """
        text = _read_registry()
        critical_start = text.index("## Critical Hooks")
        module_start = text.index("## Module Hooks")
        critical_section = text[critical_start:module_start]

        # Find the feedback-submission-reminder entry and check its type line
        hook_pos = critical_section.index("feedback-submission-reminder")
        hook_section = critical_section[hook_pos:]

        assert "agentStop" in hook_section, (
            "feedback-submission-reminder registry entry does not mention 'agentStop'"
        )
        assert "askAgent" in hook_section, (
            "feedback-submission-reminder registry entry does not mention 'askAgent'"
        )


# ---------------------------------------------------------------------------
# Integration: Hook Categories Contains feedback-submission-reminder
# Validates: Requirement 5.1
# ---------------------------------------------------------------------------


class TestHookCategoriesEntry:
    """hook-categories.yaml must list feedback-submission-reminder under critical.

    **Validates: Requirement 5.1**
    """

    def test_categories_contains_hook_under_critical(self):
        """feedback-submission-reminder must appear in the critical list.

        **Validates: Requirement 5.1**
        """
        text = _read_categories()
        # Find the critical section (between "critical:" and "modules:")
        critical_start = text.index("critical:")
        modules_start = text.index("modules:")
        critical_section = text[critical_start:modules_start]

        assert "feedback-submission-reminder" in critical_section, (
            "hook-categories.yaml does not list 'feedback-submission-reminder' "
            "under the 'critical' section"
        )


# ---------------------------------------------------------------------------
# Integration: Hook File Exists at Expected Path
# Validates: Requirement 5.1
# ---------------------------------------------------------------------------


class TestHookFileExists:
    """The hook file must exist at the expected path.

    **Validates: Requirement 5.1**
    """

    def test_hook_file_exists(self):
        """senzing-bootcamp/hooks/feedback-submission-reminder.kiro.hook must exist.

        **Validates: Requirement 5.1**
        """
        assert HOOK_FILE.exists(), (
            f"Hook file does not exist at {HOOK_FILE}"
        )

    def test_hook_file_is_valid_json_from_registry_path(self):
        """The hook file at the expected path must be valid JSON.

        **Validates: Requirement 5.1**
        """
        text = HOOK_FILE.read_text(encoding="utf-8")
        data = json.loads(text)
        assert isinstance(data, dict), "Hook file root must be a JSON object"


# ---------------------------------------------------------------------------
# Integration: Hook JSON Matches Registry Entry
# Validates: Requirements 5.1, 5.2, 5.3
# ---------------------------------------------------------------------------


class TestHookJsonMatchesRegistry:
    """The hook file's name, description, and when.type must match the
    corresponding values in hook-registry.md.

    **Validates: Requirements 5.1, 5.2, 5.3**
    """

    def test_hook_name_in_registry(self):
        """The hook's name must appear in hook-registry.md.

        **Validates: Requirement 5.1**
        """
        data = _read_hook_json()
        registry = _read_registry()
        assert data["name"] in registry, (
            f"Hook name {data['name']!r} not found in hook-registry.md"
        )

    def test_hook_name_matches_registry_name_field(self):
        """The registry entry's name field must match the hook JSON name.

        **Validates: Requirement 5.1**
        """
        data = _read_hook_json()
        registry = _read_registry()
        expected_name_field = f"- name: `{data['name']}`"
        assert expected_name_field in registry, (
            f"hook-registry.md lacks '{expected_name_field}'"
        )

    def test_hook_description_matches_registry(self):
        """The registry entry's description must match the hook JSON description.

        **Validates: Requirement 5.3**
        """
        data = _read_hook_json()
        registry = _read_registry()
        expected_desc_field = f"- description: `{data['description']}`"
        assert expected_desc_field in registry, (
            f"hook-registry.md lacks '{expected_desc_field}'"
        )

    def test_hook_when_type_matches_registry(self):
        """The registry entry must reflect the hook's when.type (agentStop).

        **Validates: Requirement 5.2**
        """
        data = _read_hook_json()
        registry = _read_registry()
        when_type = data["when"]["type"]

        # The registry format uses "(agentStop → askAgent)" in the header
        assert when_type in registry, (
            f"Hook when.type '{when_type}' not found in hook-registry.md"
        )


# ---------------------------------------------------------------------------
# Integration: Steering Index Contains 'share feedback' Keyword
# Validates: Requirement 5.1
# ---------------------------------------------------------------------------


class TestSteeringIndexKeyword:
    """steering-index.yaml must contain the 'share feedback' keyword mapping.

    **Validates: Requirement 5.1**
    """

    def test_share_feedback_keyword_exists(self):
        """The keywords section must include 'share feedback'.

        **Validates: Requirement 5.1**
        """
        text = _read_steering_index()
        assert "share feedback" in text, (
            "steering-index.yaml does not contain the 'share feedback' keyword"
        )

    def test_share_feedback_maps_to_feedback_workflow(self):
        """The 'share feedback' keyword must map to feedback-workflow.md.

        **Validates: Requirement 5.1**
        """
        text = _read_steering_index()
        # Find the line containing 'share feedback' and verify it maps correctly
        for line in text.splitlines():
            if "share feedback" in line:
                assert "feedback-workflow.md" in line, (
                    f"'share feedback' keyword does not map to feedback-workflow.md. "
                    f"Found line: {line!r}"
                )
                return
        assert False, (
            "steering-index.yaml does not contain a 'share feedback' keyword line"
        )
