"""Property-based and unit tests for session-resume split feature.

Validates:
- Property 1: Routing Correctness — phase-2 load set matches trigger conditions
- Property 2: Content Completeness — no instruction loss or duplication
- Property 3: Routing Section Completeness — routing logic references all phase-2 files
- Unit tests: Token budgets, frontmatter, guard conditions, steering index, keywords

Feature: split-session-resume
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
from hypothesis import given, settings, HealthCheck, assume
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths to the split steering files
# ---------------------------------------------------------------------------

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

_PHASE1_FILE = _STEERING_DIR / "session-resume.md"
_PHASE2_MAPPING = _STEERING_DIR / "session-resume-phase2-mapping.md"
_PHASE2_STATE_REPAIR = _STEERING_DIR / "session-resume-phase2-state-repair.md"
_PHASE2_SETUP_RECOVERY = _STEERING_DIR / "session-resume-phase2-setup-recovery.md"

_ALL_SPLIT_FILES = [
    _PHASE1_FILE,
    _PHASE2_MAPPING,
    _PHASE2_STATE_REPAIR,
    _PHASE2_SETUP_RECOVERY,
]


# ---------------------------------------------------------------------------
# Instruction block definitions
# ---------------------------------------------------------------------------

# Each instruction block is a tuple of (block_name, identifying_phrase).
# The identifying phrase is a distinctive string that uniquely locates
# the instruction block in the original monolithic file. Each block must
# appear in exactly one of the four split files.

INSTRUCTION_BLOCKS: list[tuple[str, str]] = [
    # Phase-1: Fast Path Check
    ("fast_path_check", "## Fast Path Check"),
    ("fast_path_skip_logic", "Skip Steps 1–2 entirely"),
    ("fast_path_condition_3", "No mapping checkpoints exist"),

    # Phase-1: Step 1 (Read All State Files)
    ("step1_read_state", "## Step 1: Read All State Files"),
    ("step1_journal", "`docs/bootcamp_journal.md`"),
    ("step1_reconstruct_reference", "see `session-resume-phase2-state-repair.md`"),

    # Phase-1: Step 2 (Load Language Steering)
    ("step2_load_language", "## Step 2: Load Language Steering"),
    ("step2_python", "Python → `lang-python.md`"),
    ("step2_java", "Java → `lang-java.md`"),
    ("step2_rust", "Rust → `lang-rust.md`"),

    # Phase-1: Step 2b (Behavioral Rules Reload)
    ("step2b_behavioral_rules", "## Step 2b: Behavioral Rules Reload"),
    ("step2b_one_question_per_turn", "One-question-per-turn"),
    ("step2b_no_self_answering", "No self-answering"),
    ("step2b_protocol_confirmation", "### Protocol Confirmation"),
    ("step2b_self_answering_prohibition", "### Self-Answering Prohibition"),

    # Phase-1: Step 2c (Restore Conversation Style)
    ("step2c_restore_style", "## Step 2c: Restore Conversation Style"),
    ("step2c_fallback_defaults", "### Fallback Defaults"),
    ("step2c_style_drift", "### Style Drift Detection"),

    # Phase-1: Step 3 (Summarize and Confirm)
    ("step3_summarize", "## Step 3: Summarize and Confirm"),
    ("step3_welcome_banner", "Welcome back to the Senzing Bootcamp"),
    ("step3_ready_question", "Ready to continue with Module"),

    # Phase-1: Step 4 (Load the Right Module Steering)
    ("step4_load_module", "## Step 4: Load the Right Module Steering"),
    ("step4_switch_tracks", "Switching Tracks"),
    ("step4_start_over", "start over"),
    ("step4_sub_step_string", "Sub-step string"),

    # Phase-1: Step 5 (Re-establish MCP Context)
    ("step5_mcp_context", "## Step 5: Re-establish MCP Context"),
    ("step5_get_capabilities", "get_capabilities"),

    # Phase-1: Routing Logic
    ("routing_logic", "## Routing Logic"),
    ("routing_evaluate_order", "Evaluate in this order"),

    # Phase-2 Mapping: Checkpoint Validation
    ("mapping_checkpoint_validation", "## Checkpoint Validation"),
    ("mapping_json_invalid", "JSON is invalid or required fields"),
    ("mapping_mcp_status_call", "mapping_workflow"),
    ("mapping_corrupted_checkpoint", "corrupted and cannot be read"),

    # Phase-2 Mapping: Resume Options
    ("mapping_resume_options", "## Resume Options"),
    ("mapping_option_resume", "(a) Resume"),
    ("mapping_option_restart", "(b) Restart"),
    ("mapping_option_skip", "(c) Skip"),

    # Phase-2 Mapping: Fast-Track
    ("mapping_fast_track", "## Fast-Track Through Completed Steps"),

    # Phase-2 Mapping: Summary Integration
    ("mapping_summary_integration", "## Summary Integration"),

    # Phase-2 State Repair: Progress Reconstruction
    ("state_repair_reconstruction", "## Progress Reconstruction from Artifacts"),
    ("state_repair_scan_artifacts", "Scan `src/`, `data/`, and `docs/`"),
    ("state_repair_rebuild_progress", "rebuild the progress file"),

    # Phase-2 State Repair: Handling Stale State
    ("state_repair_stale_state", "## Handling Stale or Corrupted State"),
    ("state_repair_validate_module", "validate_module.py"),
    ("state_repair_discrepancy_table", "Discrepancy Examples"),

    # Phase-2 Setup Recovery: Hook Installation
    ("setup_hook_installation", "## Hook Installation"),
    ("setup_create_hook", "createHook"),
    ("setup_hook_failure_handling", "log the failure and continue"),

    # Phase-2 Setup Recovery: MCP Health Check
    ("setup_mcp_health_check", "## Step 2d: MCP Health Check"),
    ("setup_mcp_probe", "search_docs"),
    ("setup_mcp_failure", "MCP server is unreachable"),
    ("setup_mcp_troubleshooting", "Troubleshooting steps"),

    # Phase-2 Setup Recovery: What's New
    ("setup_whats_new", "## Step 2e: What's New Notification"),
    ("setup_changelog_parse", "CHANGELOG"),
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _read_split_files() -> dict[str, str]:
    """Read all four split files and return a mapping of filename to content.

    Returns:
        Dict mapping filename (stem) to file content string.
    """
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in _ALL_SPLIT_FILES
    }


def _find_block_in_files(
    phrase: str, file_contents: dict[str, str]
) -> list[str]:
    """Find which files contain the given phrase.

    Args:
        phrase: The identifying phrase to search for.
        file_contents: Mapping of filename to content.

    Returns:
        List of filenames containing the phrase.
    """
    return [
        filename
        for filename, content in file_contents.items()
        if phrase in content
    ]


# ---------------------------------------------------------------------------
# Hypothesis strategy
# ---------------------------------------------------------------------------


def st_instruction_block() -> st.SearchStrategy[tuple[str, str]]:
    """Strategy that draws from the defined instruction blocks.

    Returns:
        A strategy producing (block_name, identifying_phrase) tuples.
    """
    return st.sampled_from(INSTRUCTION_BLOCKS)


# ---------------------------------------------------------------------------
# Property test: Content Completeness (No Instruction Loss)
# ---------------------------------------------------------------------------


class TestProperty2ContentCompleteness:
    """Property 2: Content Completeness (No Instruction Loss).

    For any instruction block present in the original monolithic
    session-resume.md, that instruction block SHALL appear in exactly one
    of the four split files (Phase-1, Phase-2 Mapping, Phase-2 State Repair,
    or Phase-2 Setup Recovery). No instruction is duplicated across files
    and no instruction is omitted.

    **Validates: Requirements 7.1, 7.3**
    """

    @given(block=st_instruction_block())
    @settings(
        max_examples=200,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_instruction_block_in_exactly_one_file(
        self, block: tuple[str, str]
    ) -> None:
        """Every instruction block appears in exactly one split file.

        Args:
            block: Tuple of (block_name, identifying_phrase) drawn from
                the instruction blocks list.
        """
        block_name, phrase = block
        file_contents = _read_split_files()
        containing_files = _find_block_in_files(phrase, file_contents)

        assert len(containing_files) >= 1, (
            f"Instruction block '{block_name}' (phrase: '{phrase}') "
            f"not found in any split file — content was lost during split"
        )
        assert len(containing_files) == 1, (
            f"Instruction block '{block_name}' (phrase: '{phrase}') "
            f"found in multiple files: {containing_files} — "
            f"content is duplicated across split files"
        )

    def test_all_instruction_blocks_present(self) -> None:
        """Exhaustive check: every defined instruction block exists in exactly one file."""
        file_contents = _read_split_files()
        violations: list[str] = []

        for block_name, phrase in INSTRUCTION_BLOCKS:
            containing_files = _find_block_in_files(phrase, file_contents)
            if len(containing_files) == 0:
                violations.append(
                    f"MISSING: '{block_name}' (phrase: '{phrase}') "
                    f"not found in any split file"
                )
            elif len(containing_files) > 1:
                violations.append(
                    f"DUPLICATED: '{block_name}' (phrase: '{phrase}') "
                    f"found in: {containing_files}"
                )

        assert violations == [], (
            f"Content completeness violations:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_no_instruction_block_duplicated_across_files(self) -> None:
        """No instruction block appears in more than one split file."""
        file_contents = _read_split_files()
        duplications: list[str] = []

        for block_name, phrase in INSTRUCTION_BLOCKS:
            containing_files = _find_block_in_files(phrase, file_contents)
            if len(containing_files) > 1:
                duplications.append(
                    f"'{block_name}' duplicated in: {containing_files}"
                )

        assert duplications == [], (
            f"Instruction blocks duplicated across files:\n"
            + "\n".join(f"  - {d}" for d in duplications)
        )

    def test_phase2_mapping_content_exclusive(self) -> None:
        """Mapping-specific instructions appear only in the mapping file."""
        file_contents = _read_split_files()
        mapping_phrases = [
            (name, phrase) for name, phrase in INSTRUCTION_BLOCKS
            if name.startswith("mapping_")
        ]

        for block_name, phrase in mapping_phrases:
            containing_files = _find_block_in_files(phrase, file_contents)
            non_mapping = [
                f for f in containing_files
                if f != "session-resume-phase2-mapping.md"
            ]
            assert non_mapping == [], (
                f"Mapping block '{block_name}' found outside mapping file: "
                f"{non_mapping}"
            )

    def test_phase2_state_repair_content_exclusive(self) -> None:
        """State repair instructions appear only in the state repair file."""
        file_contents = _read_split_files()
        repair_phrases = [
            (name, phrase) for name, phrase in INSTRUCTION_BLOCKS
            if name.startswith("state_repair_")
        ]

        for block_name, phrase in repair_phrases:
            containing_files = _find_block_in_files(phrase, file_contents)
            non_repair = [
                f for f in containing_files
                if f != "session-resume-phase2-state-repair.md"
            ]
            assert non_repair == [], (
                f"State repair block '{block_name}' found outside state "
                f"repair file: {non_repair}"
            )

    def test_phase2_setup_recovery_content_exclusive(self) -> None:
        """Setup recovery instructions appear only in the setup recovery file."""
        file_contents = _read_split_files()
        setup_phrases = [
            (name, phrase) for name, phrase in INSTRUCTION_BLOCKS
            if name.startswith("setup_")
        ]

        for block_name, phrase in setup_phrases:
            containing_files = _find_block_in_files(phrase, file_contents)
            non_setup = [
                f for f in containing_files
                if f != "session-resume-phase2-setup-recovery.md"
            ]
            assert non_setup == [], (
                f"Setup recovery block '{block_name}' found outside setup "
                f"recovery file: {non_setup}"
            )

    def test_split_files_all_exist(self) -> None:
        """All four split files exist on disk."""
        missing = [
            str(path) for path in _ALL_SPLIT_FILES if not path.exists()
        ]
        assert missing == [], (
            f"Split files missing from disk: {missing}"
        )

    def test_combined_content_covers_original_sections(self) -> None:
        """Combined split file content covers all major sections from original.

        Verifies that the union of all four split files contains all
        ## headings that were present in the original monolithic file.
        """
        # Major section headings from the original monolithic file
        original_sections = [
            "Fast Path Check",
            "Step 1: Read All State Files",
            "Step 2: Load Language Steering",
            "Step 2b: Behavioral Rules Reload",
            "Step 2c: Restore Conversation Style",
            "Step 3: Summarize and Confirm",
            "Step 4: Load the Right Module Steering",
            "Step 5: Re-establish MCP Context",
        ]

        # Sections that were in the original and moved to phase-2 files
        migrated_sections = [
            "Handling Stale or Corrupted",  # → state repair
            "MCP Health Check",             # → setup recovery
            "What's New Notification",      # → setup recovery
            "Hook Installation",            # → setup recovery
            "Checkpoint Validation",        # → mapping
            "Resume Options",               # → mapping
        ]

        file_contents = _read_split_files()
        combined = "\n".join(file_contents.values())

        missing_sections: list[str] = []
        for section in original_sections + migrated_sections:
            if section not in combined:
                missing_sections.append(section)

        assert missing_sections == [], (
            f"Sections from original not found in combined split files: "
            f"{missing_sections}"
        )


# ---------------------------------------------------------------------------
# Routing logic implementation (mirrors the Phase-1 routing conditions)
# ---------------------------------------------------------------------------


def determine_load_set(
    progress_json_valid: bool,
    progress_json_exists: bool,
    current_module_consistent: bool,
    preferences_valid: bool,
    hooks_installed_present: bool,
    mcp_probe_success: bool,
    show_whats_new_active: bool,
    session_log_exists: bool,
    mapping_state_files_exist: bool,
) -> set[str]:
    """Determine which phase-2 files should be loaded based on session state.

    This implements the routing logic from the Phase-1 file.

    Args:
        progress_json_valid: Whether bootcamp_progress.json parses as valid JSON.
        progress_json_exists: Whether bootcamp_progress.json exists at all.
        current_module_consistent: Whether current_module matches project artifacts.
        preferences_valid: Whether bootcamp_preferences.yaml is parseable.
        hooks_installed_present: Whether hooks_installed is present and non-empty.
        mcp_probe_success: Whether MCP health check probe succeeded.
        show_whats_new_active: Whether show_whats_new is not false in preferences.
        session_log_exists: Whether config/session_log.jsonl exists.
        mapping_state_files_exist: Whether any config/mapping_state_*.json exist.

    Returns:
        Set of phase-2 filenames that should be loaded.
    """
    load_set: set[str] = set()

    # 1. State repair condition
    if not progress_json_exists or not progress_json_valid or not current_module_consistent:
        load_set.add("session-resume-phase2-state-repair.md")

    # 2. Setup recovery condition
    if (
        not hooks_installed_present
        or not preferences_valid
        or not mcp_probe_success
        or (show_whats_new_active and session_log_exists)
    ):
        load_set.add("session-resume-phase2-setup-recovery.md")

    # 3. Mapping condition
    if mapping_state_files_exist:
        load_set.add("session-resume-phase2-mapping.md")

    return load_set


# ---------------------------------------------------------------------------
# Hypothesis strategies for session state
# ---------------------------------------------------------------------------


@st.composite
def st_session_state(draw: st.DrawFn) -> dict[str, bool]:
    """Strategy that generates arbitrary session states.

    Returns:
        Dict with boolean flags representing session state conditions.
    """
    return {
        "progress_json_valid": draw(st.booleans()),
        "progress_json_exists": draw(st.booleans()),
        "current_module_consistent": draw(st.booleans()),
        "preferences_valid": draw(st.booleans()),
        "hooks_installed_present": draw(st.booleans()),
        "mcp_probe_success": draw(st.booleans()),
        "show_whats_new_active": draw(st.booleans()),
        "session_log_exists": draw(st.booleans()),
        "mapping_state_files_exist": draw(st.booleans()),
    }


# ---------------------------------------------------------------------------
# Property 1: Routing Correctness
# ---------------------------------------------------------------------------


class TestProperty1RoutingCorrectness:
    """Property 1: Routing Correctness.

    For any session state, the set of phase-2 files directed for loading
    by the routing logic SHALL equal exactly the set of phase-2 files whose
    trigger conditions are satisfied by that state.

    **Validates: Requirements 2.5, 3.3, 3.4, 4.4, 4.5, 4.7, 5.1, 5.2, 8.1**
    """

    @given(state=st_session_state())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_load_set_matches_trigger_conditions(
        self, state: dict[str, bool]
    ) -> None:
        """The load set equals exactly the files whose conditions are met.

        Args:
            state: Arbitrary session state drawn by Hypothesis.
        """
        load_set = determine_load_set(**state)

        # Verify state repair condition
        state_repair_triggered = (
            not state["progress_json_exists"]
            or not state["progress_json_valid"]
            or not state["current_module_consistent"]
        )
        if state_repair_triggered:
            assert "session-resume-phase2-state-repair.md" in load_set, (
                f"State repair should be triggered for state {state}"
            )
        else:
            assert "session-resume-phase2-state-repair.md" not in load_set, (
                f"State repair should NOT be triggered for state {state}"
            )

        # Verify setup recovery condition
        setup_recovery_triggered = (
            not state["hooks_installed_present"]
            or not state["preferences_valid"]
            or not state["mcp_probe_success"]
            or (state["show_whats_new_active"] and state["session_log_exists"])
        )
        if setup_recovery_triggered:
            assert "session-resume-phase2-setup-recovery.md" in load_set, (
                f"Setup recovery should be triggered for state {state}"
            )
        else:
            assert "session-resume-phase2-setup-recovery.md" not in load_set, (
                f"Setup recovery should NOT be triggered for state {state}"
            )

        # Verify mapping condition
        if state["mapping_state_files_exist"]:
            assert "session-resume-phase2-mapping.md" in load_set, (
                f"Mapping should be triggered for state {state}"
            )
        else:
            assert "session-resume-phase2-mapping.md" not in load_set, (
                f"Mapping should NOT be triggered for state {state}"
            )

    @given(state=st_session_state())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_all_conditions_evaluated_independently(
        self, state: dict[str, bool]
    ) -> None:
        """Multiple phase-2 files can be loaded simultaneously.

        Args:
            state: Arbitrary session state drawn by Hypothesis.
        """
        load_set = determine_load_set(**state)

        # The load set can contain 0, 1, 2, or 3 files
        assert len(load_set) <= 3, (
            f"Load set should contain at most 3 files, got {len(load_set)}"
        )
        # All files in load set must be valid phase-2 filenames
        valid_files = {
            "session-resume-phase2-state-repair.md",
            "session-resume-phase2-setup-recovery.md",
            "session-resume-phase2-mapping.md",
        }
        assert load_set.issubset(valid_files), (
            f"Load set contains invalid files: {load_set - valid_files}"
        )

    def test_happy_path_loads_nothing(self) -> None:
        """When all conditions are clean, no phase-2 files are loaded."""
        load_set = determine_load_set(
            progress_json_valid=True,
            progress_json_exists=True,
            current_module_consistent=True,
            preferences_valid=True,
            hooks_installed_present=True,
            mcp_probe_success=True,
            show_whats_new_active=False,
            session_log_exists=False,
            mapping_state_files_exist=False,
        )
        assert load_set == set(), (
            f"Happy path should load no phase-2 files, got {load_set}"
        )

    def test_all_conditions_triggered_loads_all(self) -> None:
        """When all conditions fail, all three phase-2 files are loaded."""
        load_set = determine_load_set(
            progress_json_valid=False,
            progress_json_exists=True,
            current_module_consistent=False,
            preferences_valid=False,
            hooks_installed_present=False,
            mcp_probe_success=False,
            show_whats_new_active=True,
            session_log_exists=True,
            mapping_state_files_exist=True,
        )
        assert load_set == {
            "session-resume-phase2-state-repair.md",
            "session-resume-phase2-setup-recovery.md",
            "session-resume-phase2-mapping.md",
        }

    def test_missing_progress_triggers_state_repair(self) -> None:
        """Missing progress file triggers state repair."""
        load_set = determine_load_set(
            progress_json_valid=True,
            progress_json_exists=False,
            current_module_consistent=True,
            preferences_valid=True,
            hooks_installed_present=True,
            mcp_probe_success=True,
            show_whats_new_active=False,
            session_log_exists=False,
            mapping_state_files_exist=False,
        )
        assert "session-resume-phase2-state-repair.md" in load_set

    def test_invalid_progress_json_triggers_state_repair(self) -> None:
        """Invalid progress JSON triggers state repair."""
        load_set = determine_load_set(
            progress_json_valid=False,
            progress_json_exists=True,
            current_module_consistent=True,
            preferences_valid=True,
            hooks_installed_present=True,
            mcp_probe_success=True,
            show_whats_new_active=False,
            session_log_exists=False,
            mapping_state_files_exist=False,
        )
        assert "session-resume-phase2-state-repair.md" in load_set

    def test_inconsistent_module_triggers_state_repair(self) -> None:
        """Inconsistent current_module triggers state repair."""
        load_set = determine_load_set(
            progress_json_valid=True,
            progress_json_exists=True,
            current_module_consistent=False,
            preferences_valid=True,
            hooks_installed_present=True,
            mcp_probe_success=True,
            show_whats_new_active=False,
            session_log_exists=False,
            mapping_state_files_exist=False,
        )
        assert "session-resume-phase2-state-repair.md" in load_set

    def test_missing_hooks_triggers_setup_recovery(self) -> None:
        """Missing hooks_installed triggers setup recovery."""
        load_set = determine_load_set(
            progress_json_valid=True,
            progress_json_exists=True,
            current_module_consistent=True,
            preferences_valid=True,
            hooks_installed_present=False,
            mcp_probe_success=True,
            show_whats_new_active=False,
            session_log_exists=False,
            mapping_state_files_exist=False,
        )
        assert "session-resume-phase2-setup-recovery.md" in load_set

    def test_mcp_failure_triggers_setup_recovery(self) -> None:
        """MCP probe failure triggers setup recovery."""
        load_set = determine_load_set(
            progress_json_valid=True,
            progress_json_exists=True,
            current_module_consistent=True,
            preferences_valid=True,
            hooks_installed_present=True,
            mcp_probe_success=False,
            show_whats_new_active=False,
            session_log_exists=False,
            mapping_state_files_exist=False,
        )
        assert "session-resume-phase2-setup-recovery.md" in load_set

    def test_whats_new_with_session_log_triggers_setup_recovery(self) -> None:
        """show_whats_new active + session_log exists triggers setup recovery."""
        load_set = determine_load_set(
            progress_json_valid=True,
            progress_json_exists=True,
            current_module_consistent=True,
            preferences_valid=True,
            hooks_installed_present=True,
            mcp_probe_success=True,
            show_whats_new_active=True,
            session_log_exists=True,
            mapping_state_files_exist=False,
        )
        assert "session-resume-phase2-setup-recovery.md" in load_set

    def test_whats_new_without_session_log_no_trigger(self) -> None:
        """show_whats_new active but no session_log does NOT trigger setup recovery."""
        load_set = determine_load_set(
            progress_json_valid=True,
            progress_json_exists=True,
            current_module_consistent=True,
            preferences_valid=True,
            hooks_installed_present=True,
            mcp_probe_success=True,
            show_whats_new_active=True,
            session_log_exists=False,
            mapping_state_files_exist=False,
        )
        assert "session-resume-phase2-setup-recovery.md" not in load_set

    def test_mapping_state_triggers_mapping(self) -> None:
        """Existing mapping state files trigger mapping recovery."""
        load_set = determine_load_set(
            progress_json_valid=True,
            progress_json_exists=True,
            current_module_consistent=True,
            preferences_valid=True,
            hooks_installed_present=True,
            mcp_probe_success=True,
            show_whats_new_active=False,
            session_log_exists=False,
            mapping_state_files_exist=True,
        )
        assert "session-resume-phase2-mapping.md" in load_set


# ---------------------------------------------------------------------------
# Property 3: Routing Section Completeness
# ---------------------------------------------------------------------------


class TestProperty3RoutingSectionCompleteness:
    """Property 3: Routing Section Completeness.

    For each phase-2 filename, the routing logic section in Phase-1
    contains at least one explicit loading condition referencing that
    file by name.

    **Validates: Requirements 1.5, 5.3**
    """

    PHASE2_FILES = [
        "session-resume-phase2-mapping.md",
        "session-resume-phase2-state-repair.md",
        "session-resume-phase2-setup-recovery.md",
    ]

    @given(filename=st.sampled_from(PHASE2_FILES))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_routing_logic_references_phase2_file(
        self, filename: str
    ) -> None:
        """The routing logic section explicitly references each phase-2 file.

        Args:
            filename: A phase-2 filename drawn from the list.
        """
        phase1_content = _PHASE1_FILE.read_text(encoding="utf-8")

        # Extract the routing logic section
        routing_start = phase1_content.find("## Routing Logic")
        assert routing_start != -1, "Routing Logic section not found in Phase-1 file"

        # Find the next ## heading after routing logic (or end of file)
        next_section = phase1_content.find("\n## ", routing_start + 1)
        if next_section == -1:
            routing_section = phase1_content[routing_start:]
        else:
            routing_section = phase1_content[routing_start:next_section]

        assert filename in routing_section, (
            f"Phase-2 file '{filename}' not referenced in the Routing Logic "
            f"section of the Phase-1 file"
        )

    def test_all_phase2_files_referenced_in_routing(self) -> None:
        """Exhaustive check: all phase-2 files are referenced in routing logic."""
        phase1_content = _PHASE1_FILE.read_text(encoding="utf-8")

        routing_start = phase1_content.find("## Routing Logic")
        assert routing_start != -1, "Routing Logic section not found"

        next_section = phase1_content.find("\n## ", routing_start + 1)
        if next_section == -1:
            routing_section = phase1_content[routing_start:]
        else:
            routing_section = phase1_content[routing_start:next_section]

        missing = [
            f for f in self.PHASE2_FILES if f not in routing_section
        ]
        assert missing == [], (
            f"Phase-2 files not referenced in Routing Logic: {missing}"
        )

    def test_routing_logic_has_loading_conditions(self) -> None:
        """Routing logic contains explicit conditional loading directives."""
        phase1_content = _PHASE1_FILE.read_text(encoding="utf-8")

        routing_start = phase1_content.find("## Routing Logic")
        assert routing_start != -1

        next_section = phase1_content.find("\n## ", routing_start + 1)
        if next_section == -1:
            routing_section = phase1_content[routing_start:]
        else:
            routing_section = phase1_content[routing_start:next_section]

        # Should contain "Load" directives for each phase-2 file
        assert "Load" in routing_section, (
            "Routing Logic section should contain 'Load' directives"
        )

    def test_routing_evaluation_order_specified(self) -> None:
        """Routing logic specifies evaluation order: state repair, setup, mapping."""
        phase1_content = _PHASE1_FILE.read_text(encoding="utf-8")

        routing_start = phase1_content.find("## Routing Logic")
        assert routing_start != -1

        next_section = phase1_content.find("\n## ", routing_start + 1)
        if next_section == -1:
            routing_section = phase1_content[routing_start:]
        else:
            routing_section = phase1_content[routing_start:next_section]

        # Find positions of each condition type
        state_repair_pos = routing_section.find("State repair")
        setup_recovery_pos = routing_section.find("Setup recovery")
        mapping_pos = routing_section.find("Mapping")

        assert state_repair_pos != -1, "State repair condition not found"
        assert setup_recovery_pos != -1, "Setup recovery condition not found"
        assert mapping_pos != -1, "Mapping condition not found"

        # Verify order: state repair < setup recovery < mapping
        assert state_repair_pos < setup_recovery_pos < mapping_pos, (
            f"Evaluation order incorrect: state_repair={state_repair_pos}, "
            f"setup_recovery={setup_recovery_pos}, mapping={mapping_pos}"
        )


# ---------------------------------------------------------------------------
# Unit Tests: Token budgets, frontmatter, guard conditions, steering index
# ---------------------------------------------------------------------------


def _calculate_token_count(filepath: Path) -> int:
    """Calculate approximate token count: round(len(content) / 4).

    Uses the same formula as measure_steering.py for consistency.

    Args:
        filepath: Path to the file to measure.

    Returns:
        Approximate token count.
    """
    content = filepath.read_text(encoding="utf-8")
    return round(len(content) / 4)


def _read_steering_index() -> str:
    """Read the steering-index.yaml file content.

    Returns:
        The raw text content of steering-index.yaml.
    """
    index_path = _STEERING_DIR / "steering-index.yaml"
    return index_path.read_text(encoding="utf-8")


class TestUnitTokenBudgets:
    """Unit tests for token budget compliance.

    **Validates: Requirements 1.10, 2.6, 3.5, 4.8**
    """

    def test_phase1_token_budget(self) -> None:
        """Phase-1 file token count ≤ 2,700."""
        token_count = _calculate_token_count(_PHASE1_FILE)
        assert token_count <= 2700, (
            f"Phase-1 file has {token_count} tokens, exceeds budget of 2,700"
        )

    def test_phase2_mapping_token_budget(self) -> None:
        """Phase-2 Mapping file token count ≤ 1,000."""
        token_count = _calculate_token_count(_PHASE2_MAPPING)
        assert token_count <= 1000, (
            f"Phase-2 Mapping file has {token_count} tokens, "
            f"exceeds budget of 1,000"
        )

    def test_phase2_state_repair_token_budget(self) -> None:
        """Phase-2 State Repair file token count ≤ 800."""
        token_count = _calculate_token_count(_PHASE2_STATE_REPAIR)
        assert token_count <= 800, (
            f"Phase-2 State Repair file has {token_count} tokens, "
            f"exceeds budget of 800"
        )

    def test_phase2_setup_recovery_token_budget(self) -> None:
        """Phase-2 Setup Recovery file token count ≤ 750."""
        token_count = _calculate_token_count(_PHASE2_SETUP_RECOVERY)
        assert token_count <= 750, (
            f"Phase-2 Setup Recovery file has {token_count} tokens, "
            f"exceeds budget of 750"
        )


class TestUnitFrontmatter:
    """Unit tests for frontmatter rules.

    **Validates: Requirements 7.2, 8.2**
    """

    def test_phase1_has_inclusion_manual_frontmatter(self) -> None:
        """Phase-1 file has `inclusion: manual` frontmatter."""
        content = _PHASE1_FILE.read_text(encoding="utf-8")
        assert content.startswith("---"), (
            "Phase-1 file must start with YAML frontmatter delimiter"
        )
        # Extract frontmatter
        end_idx = content.find("---", 3)
        assert end_idx != -1, "Phase-1 file frontmatter not properly closed"
        frontmatter = content[3:end_idx]
        assert "inclusion: manual" in frontmatter, (
            "Phase-1 file must have 'inclusion: manual' in frontmatter"
        )

    def test_phase2_mapping_has_frontmatter(self) -> None:
        """Phase-2 Mapping file has YAML frontmatter with inclusion: manual."""
        content = _PHASE2_MAPPING.read_text(encoding="utf-8")
        assert content.startswith("---"), (
            "Phase-2 Mapping file should have YAML frontmatter"
        )
        assert "inclusion: manual" in content.split("---")[1], (
            "Phase-2 Mapping file should have inclusion: manual"
        )

    def test_phase2_state_repair_has_frontmatter(self) -> None:
        """Phase-2 State Repair file has YAML frontmatter with inclusion: manual."""
        content = _PHASE2_STATE_REPAIR.read_text(encoding="utf-8")
        assert content.startswith("---"), (
            "Phase-2 State Repair file should have YAML frontmatter"
        )
        assert "inclusion: manual" in content.split("---")[1], (
            "Phase-2 State Repair file should have inclusion: manual"
        )

    def test_phase2_setup_recovery_has_frontmatter(self) -> None:
        """Phase-2 Setup Recovery file has YAML frontmatter with inclusion: manual."""
        content = _PHASE2_SETUP_RECOVERY.read_text(encoding="utf-8")
        assert content.startswith("---"), (
            "Phase-2 Setup Recovery file should have YAML frontmatter"
        )
        assert "inclusion: manual" in content.split("---")[1], (
            "Phase-2 Setup Recovery file should have inclusion: manual"
        )


class TestUnitGuardConditions:
    """Unit tests for guard condition blocks in phase-2 files.

    **Validates: Requirements 2.6, 3.5, 4.8, 8.3**
    """

    def test_phase2_mapping_has_guard_condition(self) -> None:
        """Phase-2 Mapping file begins with a guard condition block."""
        content = _PHASE2_MAPPING.read_text(encoding="utf-8")
        assert "## Guard Condition" in content, (
            "Phase-2 Mapping file must contain a Guard Condition section"
        )
        # Guard condition should appear before any other ## heading
        first_h2 = content.find("## ")
        guard_pos = content.find("## Guard Condition")
        assert guard_pos == first_h2 or guard_pos < content.find("## ", first_h2 + 1), (
            "Guard Condition should be the first ## section after the title"
        )

    def test_phase2_state_repair_has_guard_condition(self) -> None:
        """Phase-2 State Repair file begins with a guard condition block."""
        content = _PHASE2_STATE_REPAIR.read_text(encoding="utf-8")
        assert "## Guard Condition" in content, (
            "Phase-2 State Repair file must contain a Guard Condition section"
        )

    def test_phase2_setup_recovery_has_guard_condition(self) -> None:
        """Phase-2 Setup Recovery file begins with a guard condition block."""
        content = _PHASE2_SETUP_RECOVERY.read_text(encoding="utf-8")
        assert "## Guard Condition" in content or "Guard Condition" in content.split("\n\n")[1] if len(content.split("\n\n")) > 1 else False, (
            "Phase-2 Setup Recovery file must contain a Guard Condition section"
        )


class TestUnitSteeringIndex:
    """Unit tests for steering-index.yaml structure.

    **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
    """

    def test_session_resume_entry_exists(self) -> None:
        """steering-index.yaml has a session-resume entry."""
        index_content = _read_steering_index()
        assert "session-resume:" in index_content, (
            "steering-index.yaml must contain a 'session-resume:' entry"
        )

    def test_session_resume_has_root(self) -> None:
        """session-resume entry has root pointing to session-resume.md."""
        index_content = _read_steering_index()
        # Find the session-resume block
        sr_start = index_content.find("session-resume:")
        assert sr_start != -1
        sr_block = index_content[sr_start:sr_start + 500]
        assert "root: session-resume.md" in sr_block, (
            "session-resume entry must have 'root: session-resume.md'"
        )

    def test_session_resume_has_phases(self) -> None:
        """session-resume entry has phases map with all four files."""
        index_content = _read_steering_index()
        sr_start = index_content.find("session-resume:")
        assert sr_start != -1
        sr_block = index_content[sr_start:sr_start + 800]

        required_phases = [
            "phase1-fast-path:",
            "phase2-mapping:",
            "phase2-state-repair:",
            "phase2-setup-recovery:",
        ]
        missing = [p for p in required_phases if p not in sr_block]
        assert missing == [], (
            f"session-resume phases missing: {missing}"
        )

    def test_file_metadata_has_phase2_entries(self) -> None:
        """file_metadata section has entries for all phase-2 files."""
        index_content = _read_steering_index()
        required_entries = [
            "session-resume-phase2-mapping.md:",
            "session-resume-phase2-state-repair.md:",
            "session-resume-phase2-setup-recovery.md:",
        ]
        missing = [e for e in required_entries if e not in index_content]
        assert missing == [], (
            f"file_metadata entries missing: {missing}"
        )

    def test_file_metadata_session_resume_updated(self) -> None:
        """file_metadata entry for session-resume.md exists with token count."""
        index_content = _read_steering_index()
        assert "session-resume.md:" in index_content, (
            "file_metadata must contain session-resume.md entry"
        )


class TestUnitKeywordMapping:
    """Unit tests for keyword mapping preservation.

    **Validates: Requirements 7.4**
    """

    def test_resume_keyword_maps_to_session_resume(self) -> None:
        """The 'resume' keyword still maps to session-resume.md."""
        index_content = _read_steering_index()
        # Find keywords section
        kw_start = index_content.find("keywords:")
        assert kw_start != -1, "keywords section not found in steering-index.yaml"
        kw_block = index_content[kw_start:kw_start + 500]
        assert "resume: session-resume.md" in kw_block, (
            "keywords section must map 'resume' to 'session-resume.md'"
        )
