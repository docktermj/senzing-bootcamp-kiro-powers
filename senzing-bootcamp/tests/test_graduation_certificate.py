"""Unit tests for generate_graduation_certificate.py."""

from __future__ import annotations

import html
import html
import json
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from generate_graduation_certificate import (
    MODULE_NAMES,
    MODULE_SKILLS,
    CertificateData,
    ERMetrics,
    JournalData,
    JournalEntry,
    ModuleRecord,
    PreferencesData,
    ProgressData,
    assemble_certificate,
    derive_next_steps,
    derive_skills,
    load_journal,
    load_preferences,
    load_progress,
    main,
    parse_args,
    parse_simple_yaml,
    render_html,
    render_markdown,
)


class TestArgumentParsing:
    """Tests for parse_args function.

    Validates: Requirements 2.3, 2.4, 2.5, 2.6
    """

    def test_default_progress_file(self) -> None:
        """Default --progress-file is config/bootcamp_progress.json."""
        args = parse_args([])
        assert args.progress_file == "config/bootcamp_progress.json"

    def test_default_preferences_file(self) -> None:
        """Default --preferences-file is config/bootcamp_preferences.yaml."""
        args = parse_args([])
        assert args.preferences_file == "config/bootcamp_preferences.yaml"

    def test_default_journal_file(self) -> None:
        """Default --journal-file is docs/bootcamp_journal.md."""
        args = parse_args([])
        assert args.journal_file == "docs/bootcamp_journal.md"

    def test_default_output_dir(self) -> None:
        """Default --output-dir is docs/graduation/."""
        args = parse_args([])
        assert args.output_dir == "docs/graduation/"

    def test_override_progress_file(self) -> None:
        """--progress-file can be overridden."""
        args = parse_args(["--progress-file", "custom/progress.json"])
        assert args.progress_file == "custom/progress.json"

    def test_override_preferences_file(self) -> None:
        """--preferences-file can be overridden."""
        args = parse_args(["--preferences-file", "custom/prefs.yaml"])
        assert args.preferences_file == "custom/prefs.yaml"

    def test_override_journal_file(self) -> None:
        """--journal-file can be overridden."""
        args = parse_args(["--journal-file", "custom/journal.md"])
        assert args.journal_file == "custom/journal.md"

    def test_override_output_dir(self) -> None:
        """--output-dir can be overridden."""
        args = parse_args(["--output-dir", "custom/output/"])
        assert args.output_dir == "custom/output/"


class TestLoadProgress:
    """Tests for load_progress function.

    Validates: Requirements 9.1, 9.4
    """

    def test_valid_json(self, tmp_path: Path) -> None:
        """Valid progress JSON returns ProgressData with sorted modules."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(json.dumps({"modules_completed": [3, 1, 2]}))

        result = load_progress(progress_file)

        assert isinstance(result, ProgressData)
        assert result.modules_completed == [1, 2, 3]
        assert result.module_names[1] == "Business Problem"
        assert result.module_names[2] == "SDK Setup"
        assert result.module_names[3] == "System Verification"

    def test_valid_json_all_modules(self, tmp_path: Path) -> None:
        """All 11 modules are recognized with correct names."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(
            json.dumps({"modules_completed": list(range(1, 12))})
        )

        result = load_progress(progress_file)

        assert len(result.modules_completed) == 11
        assert result.module_names[11] == "Package & Deploy"

    def test_valid_json_empty_modules(self, tmp_path: Path) -> None:
        """Empty modules_completed list returns empty ProgressData."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(json.dumps({"modules_completed": []}))

        result = load_progress(progress_file)

        assert result.modules_completed == []
        assert result.module_names == {}

    def test_missing_file_exits(self, tmp_path: Path) -> None:
        """Missing progress file raises SystemExit."""
        missing_file = tmp_path / "nonexistent.json"

        with pytest.raises(SystemExit):
            load_progress(missing_file)

    def test_malformed_json_exits(self, tmp_path: Path) -> None:
        """Malformed JSON raises SystemExit."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text("{not valid json!!!")

        with pytest.raises(SystemExit):
            load_progress(progress_file)

    def test_non_object_json_exits(self, tmp_path: Path) -> None:
        """JSON that is not an object raises SystemExit."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(json.dumps([1, 2, 3]))

        with pytest.raises(SystemExit):
            load_progress(progress_file)

    def test_modules_completed_not_list_exits(self, tmp_path: Path) -> None:
        """modules_completed that is not a list raises SystemExit."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(json.dumps({"modules_completed": "not a list"}))

        with pytest.raises(SystemExit):
            load_progress(progress_file)

    def test_string_module_numbers_converted(self, tmp_path: Path) -> None:
        """String digit module numbers are converted to integers."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(json.dumps({"modules_completed": ["1", "2", 3]}))

        result = load_progress(progress_file)

        assert result.modules_completed == [1, 2, 3]


class TestLoadPreferences:
    """Tests for load_preferences and parse_simple_yaml functions.

    Validates: Requirements 9.2, 9.4
    """

    def test_valid_yaml(self, tmp_path: Path) -> None:
        """Valid preferences YAML returns correct PreferencesData."""
        prefs_file = tmp_path / "prefs.yaml"
        prefs_file.write_text("track: Core Bootcamp\nlanguage: Python\n")

        result = load_preferences(prefs_file)

        assert isinstance(result, PreferencesData)
        assert result.track == "Core Bootcamp"
        assert result.language == "Python"

    def test_valid_yaml_quoted_values(self, tmp_path: Path) -> None:
        """Quoted values in YAML are parsed correctly."""
        prefs_file = tmp_path / "prefs.yaml"
        prefs_file.write_text('track: "Advanced Topics"\nlanguage: \'Java\'\n')

        result = load_preferences(prefs_file)

        assert result.track == "Advanced Topics"
        assert result.language == "Java"

    def test_missing_file_returns_defaults(self, tmp_path: Path) -> None:
        """Missing preferences file returns defaults without error."""
        missing_file = tmp_path / "nonexistent.yaml"

        result = load_preferences(missing_file)

        assert result.track == "Unknown"
        assert result.language == "Unknown"

    def test_empty_file_returns_defaults(self, tmp_path: Path) -> None:
        """Empty preferences file returns defaults."""
        prefs_file = tmp_path / "prefs.yaml"
        prefs_file.write_text("")

        result = load_preferences(prefs_file)

        assert result.track == "Unknown"
        assert result.language == "Unknown"

    def test_missing_keys_returns_defaults(self, tmp_path: Path) -> None:
        """YAML without track/language keys returns defaults."""
        prefs_file = tmp_path / "prefs.yaml"
        prefs_file.write_text("other_key: some_value\n")

        result = load_preferences(prefs_file)

        assert result.track == "Unknown"
        assert result.language == "Unknown"

    def test_comments_and_blank_lines_ignored(self, tmp_path: Path) -> None:
        """Comments and blank lines are ignored in YAML parsing."""
        prefs_file = tmp_path / "prefs.yaml"
        prefs_file.write_text(
            "# This is a comment\n\ntrack: Core Bootcamp\n\n# Another comment\nlanguage: Python\n"
        )

        result = load_preferences(prefs_file)

        assert result.track == "Core Bootcamp"
        assert result.language == "Python"

    def test_parse_simple_yaml_boolean_values(self) -> None:
        """Boolean values are stored as lowercase strings."""
        content = "skip_graduation: true\nenabled: false\n"

        result = parse_simple_yaml(content)

        assert result["skip_graduation"] == "true"
        assert result["enabled"] == "false"

    def test_parse_simple_yaml_null_values_skipped(self) -> None:
        """Null/empty values are skipped."""
        content = "track: Core Bootcamp\nempty_key: null\ntilde_key: ~\nblank_key:\n"

        result = parse_simple_yaml(content)

        assert result["track"] == "Core Bootcamp"
        assert "empty_key" not in result
        assert "tilde_key" not in result
        assert "blank_key" not in result


class TestLoadJournal:
    """Tests for load_journal function.

    Validates: Requirements 9.3, 9.4
    """

    def test_valid_markdown(self, tmp_path: Path) -> None:
        """Valid journal markdown returns entries with outcomes."""
        journal_file = tmp_path / "journal.md"
        journal_file.write_text(
            "# Bootcamp Journal\n\n"
            "## Module 1: Business Problem —\n\n"
            "**What we did:** Defined the business problem for entity resolution.\n\n"
            "## Module 2: SDK Setup —\n\n"
            "**What we did:** Installed and configured the Senzing SDK.\n"
        )

        result = load_journal(journal_file)

        assert isinstance(result, JournalData)
        assert 1 in result.entries
        assert 2 in result.entries
        assert result.entries[1].module_number == 1
        assert result.entries[1].outcome == "Defined the business problem for entity resolution."
        assert result.entries[2].module_number == 2
        assert result.entries[2].outcome == "Installed and configured the Senzing SDK."

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        """Missing journal file returns empty JournalData without error."""
        missing_file = tmp_path / "nonexistent.md"

        result = load_journal(missing_file)

        assert isinstance(result, JournalData)
        assert result.entries == {}
        assert result.er_metrics is None

    def test_partial_entries(self, tmp_path: Path) -> None:
        """Journal with some modules missing outcomes still parses available entries."""
        journal_file = tmp_path / "journal.md"
        journal_file.write_text(
            "# Bootcamp Journal\n\n"
            "## Module 1: Business Problem —\n\n"
            "**What we did:** Defined the problem.\n\n"
            "## Module 3: System Verification —\n\n"
            "Some notes without the What we did pattern.\n"
        )

        result = load_journal(journal_file)

        assert 1 in result.entries
        assert result.entries[1].outcome == "Defined the problem."
        assert 3 in result.entries
        assert result.entries[3].outcome == ""

    def test_er_metrics_extracted(self, tmp_path: Path) -> None:
        """ER metrics are extracted from journal content."""
        journal_file = tmp_path / "journal.md"
        journal_file.write_text(
            "# Bootcamp Journal\n\n"
            "## Module 7: Query, Visualize, and Discover —\n\n"
            "**What we did:** Queried resolved entities.\n\n"
            "Entity count: 1,234\n"
            "Match rate: 95.5%\n"
            "Data sources loaded: 3\n"
        )

        result = load_journal(journal_file)

        assert result.er_metrics is not None
        assert result.er_metrics.entity_count == "1,234"
        assert result.er_metrics.match_rate == "95.5%"
        assert result.er_metrics.data_sources_loaded == "3"

    def test_no_er_metrics_returns_none(self, tmp_path: Path) -> None:
        """Journal without ER metrics returns er_metrics=None."""
        journal_file = tmp_path / "journal.md"
        journal_file.write_text(
            "# Bootcamp Journal\n\n"
            "## Module 1: Business Problem —\n\n"
            "**What we did:** Defined the problem.\n"
        )

        result = load_journal(journal_file)

        assert result.er_metrics is None

    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        """Empty journal file returns empty JournalData."""
        journal_file = tmp_path / "journal.md"
        journal_file.write_text("")

        result = load_journal(journal_file)

        assert result.entries == {}
        assert result.er_metrics is None


class TestDeriveNextSteps:
    """Tests for derive_next_steps function.

    Validates: Requirements 7.2, 7.3, 7.4
    """

    def test_core_bootcamp_recommends_advanced_topics(self) -> None:
        """Core Bootcamp track recommends performance, security, monitoring, deployment."""
        result = derive_next_steps("Core Bootcamp")

        assert len(result) == 4
        assert "Explore performance tuning and benchmarking" in result
        assert "Implement security hardening" in result
        assert "Set up monitoring and alerting" in result
        assert "Plan production deployment" in result

    def test_advanced_topics_recommends_production(self) -> None:
        """Advanced Topics track recommends production deployment and operations."""
        result = derive_next_steps("Advanced Topics")

        assert len(result) == 4
        assert "Deploy to production environment" in result
        assert "Establish ongoing operations procedures" in result
        assert "Set up CI/CD pipeline for entity resolution" in result
        assert "Monitor and optimize resolution quality" in result

    def test_unknown_track_returns_generic_steps(self) -> None:
        """Unknown track returns generic next steps."""
        result = derive_next_steps("Unknown")

        assert len(result) == 3
        assert "Review completed modules for deeper understanding" in result
        assert "Explore additional Senzing documentation" in result
        assert "Consider advanced entity resolution topics" in result

    def test_arbitrary_string_returns_generic_steps(self) -> None:
        """Any unrecognized track string returns generic next steps."""
        result = derive_next_steps("Something Else Entirely")

        assert result == derive_next_steps("Unknown")

    def test_empty_string_returns_generic_steps(self) -> None:
        """Empty string track returns generic next steps."""
        result = derive_next_steps("")

        assert result == derive_next_steps("Unknown")

    def test_assemble_certificate_populates_next_steps(self) -> None:
        """assemble_certificate uses derive_next_steps to populate next_steps field."""
        progress = ProgressData(
            modules_completed=[1, 2],
            module_names={1: "Business Problem", 2: "SDK Setup"},
        )
        prefs = PreferencesData(track="Core Bootcamp", language="Python")
        journal = JournalData(entries={}, er_metrics=None)

        cert = assemble_certificate(progress, prefs, journal, "test-project")

        assert cert.next_steps == derive_next_steps("Core Bootcamp")


class TestAssembleCertificate:
    """Tests for assemble_certificate function.

    Validates: Requirements 4.1, 4.2, 4.3, 5.1, 5.2, 5.3
    """

    def test_project_name_from_parameter(self) -> None:
        """project_name is set from the function parameter."""
        progress = ProgressData(modules_completed=[1], module_names={1: "Business Problem"})
        prefs = PreferencesData(track="Core Bootcamp", language="Python")
        journal = JournalData(entries={}, er_metrics=None)

        cert = assemble_certificate(progress, prefs, journal, "my-workspace")

        assert cert.project_name == "my-workspace"

    def test_completion_date_is_today_iso(self) -> None:
        """completion_date is today's date in ISO 8601 YYYY-MM-DD format."""
        import datetime

        progress = ProgressData(modules_completed=[1], module_names={1: "Business Problem"})
        prefs = PreferencesData(track="Unknown", language="Unknown")
        journal = JournalData(entries={}, er_metrics=None)

        cert = assemble_certificate(progress, prefs, journal, "proj")

        assert cert.completion_date == datetime.date.today().isoformat()

    def test_track_from_preferences(self) -> None:
        """track is set from preferences.track."""
        progress = ProgressData(modules_completed=[1], module_names={1: "Business Problem"})
        prefs = PreferencesData(track="Advanced Topics", language="Java")
        journal = JournalData(entries={}, er_metrics=None)

        cert = assemble_certificate(progress, prefs, journal, "proj")

        assert cert.track == "Advanced Topics"

    def test_modules_combined_with_journal_outcomes(self) -> None:
        """Modules are built from progress with journal outcomes where available."""
        progress = ProgressData(
            modules_completed=[1, 2, 3],
            module_names={1: "Business Problem", 2: "SDK Setup", 3: "System Verification"},
        )
        prefs = PreferencesData(track="Core Bootcamp", language="Python")
        journal = JournalData(
            entries={
                1: JournalEntry(module_number=1, outcome="Defined the problem"),
                3: JournalEntry(module_number=3, outcome="Verified setup"),
            },
            er_metrics=None,
        )

        cert = assemble_certificate(progress, prefs, journal, "proj")

        assert len(cert.modules) == 3
        assert cert.modules[0].number == 1
        assert cert.modules[0].name == "Business Problem"
        assert cert.modules[0].outcome == "Defined the problem"
        assert cert.modules[1].number == 2
        assert cert.modules[1].name == "SDK Setup"
        assert cert.modules[1].outcome == ""
        assert cert.modules[2].number == 3
        assert cert.modules[2].name == "System Verification"
        assert cert.modules[2].outcome == "Verified setup"

    def test_missing_journal_entry_gives_empty_outcome(self) -> None:
        """Modules without journal entries get empty string outcome."""
        progress = ProgressData(
            modules_completed=[1, 2],
            module_names={1: "Business Problem", 2: "SDK Setup"},
        )
        prefs = PreferencesData(track="Core Bootcamp", language="Python")
        journal = JournalData(entries={}, er_metrics=None)

        cert = assemble_certificate(progress, prefs, journal, "proj")

        assert all(m.outcome == "" for m in cert.modules)

    def test_er_metrics_from_journal(self) -> None:
        """er_metrics is set from journal.er_metrics."""
        progress = ProgressData(modules_completed=[1], module_names={1: "Business Problem"})
        prefs = PreferencesData(track="Core Bootcamp", language="Python")
        er = ERMetrics(entity_count="500", match_rate="92%", data_sources_loaded="2")
        journal = JournalData(entries={}, er_metrics=er)

        cert = assemble_certificate(progress, prefs, journal, "proj")

        assert cert.er_metrics is not None
        assert cert.er_metrics.entity_count == "500"
        assert cert.er_metrics.match_rate == "92%"
        assert cert.er_metrics.data_sources_loaded == "2"

    def test_er_metrics_none_when_journal_has_none(self) -> None:
        """er_metrics is None when journal has no ER metrics."""
        progress = ProgressData(modules_completed=[1], module_names={1: "Business Problem"})
        prefs = PreferencesData(track="Core Bootcamp", language="Python")
        journal = JournalData(entries={}, er_metrics=None)

        cert = assemble_certificate(progress, prefs, journal, "proj")

        assert cert.er_metrics is None

    def test_empty_progress_gives_empty_modules(self) -> None:
        """Empty modules_completed produces empty modules list."""
        progress = ProgressData(modules_completed=[], module_names={})
        prefs = PreferencesData(track="Core Bootcamp", language="Python")
        journal = JournalData(entries={}, er_metrics=None)

        cert = assemble_certificate(progress, prefs, journal, "proj")

        assert cert.modules == []


# ---------------------------------------------------------------------------
# Strategies for Property 8
# ---------------------------------------------------------------------------

st_file_content = st.one_of(st.text(), st.binary())
"""Strategy generating random text or binary content for file writing."""


class TestPropertyNoUnhandledExceptions:
    """Property 8: No unhandled exceptions for any input.

    For any combination of input files (including malformed JSON, invalid content,
    empty files, and binary data), the Certificate_Generator shall not raise an
    unhandled exception. It shall either produce a certificate or exit with a
    non-zero code and an error message to stderr.

    Validates: Requirements 9.4
    """

    @given(
        progress_content=st_file_content,
        preferences_content=st_file_content,
        journal_content=st_file_content,
    )
    @settings(max_examples=20)
    def test_no_unhandled_exceptions_all_random(
        self,
        progress_content: str | bytes,
        preferences_content: str | bytes,
        journal_content: str | bytes,
    ) -> None:
        """main() never raises an unhandled exception for any file content."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            progress_file = tmp_path / "progress.json"
            preferences_file = tmp_path / "preferences.yaml"
            journal_file = tmp_path / "journal.md"
            output_dir = tmp_path / "output"

            # Write progress file content
            if isinstance(progress_content, bytes):
                progress_file.write_bytes(progress_content)
            else:
                progress_file.write_text(progress_content, encoding="utf-8")

            # Write preferences file content
            if isinstance(preferences_content, bytes):
                preferences_file.write_bytes(preferences_content)
            else:
                preferences_file.write_text(preferences_content, encoding="utf-8")

            # Write journal file content
            if isinstance(journal_content, bytes):
                journal_file.write_bytes(journal_content)
            else:
                journal_file.write_text(journal_content, encoding="utf-8")

            argv = [
                "--progress-file", str(progress_file),
                "--preferences-file", str(preferences_file),
                "--journal-file", str(journal_file),
                "--output-dir", str(output_dir),
            ]

            try:
                result = main(argv)
            except SystemExit as exc:
                # SystemExit is acceptable — load_progress calls sys.exit(1)
                # on missing/malformed files
                result = exc.code if isinstance(exc.code, int) else 1

            assert result in (0, 1), f"Unexpected exit code: {result}"

    @given(
        preferences_content=st_file_content,
        journal_content=st_file_content,
    )
    @settings(max_examples=20)
    def test_no_unhandled_exceptions_missing_progress(
        self,
        preferences_content: str | bytes,
        journal_content: str | bytes,
    ) -> None:
        """main() handles missing progress file without unhandled exception."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            # Progress file intentionally not created
            progress_file = tmp_path / "nonexistent_progress.json"
            preferences_file = tmp_path / "preferences.yaml"
            journal_file = tmp_path / "journal.md"
            output_dir = tmp_path / "output"

            # Write preferences file content
            if isinstance(preferences_content, bytes):
                preferences_file.write_bytes(preferences_content)
            else:
                preferences_file.write_text(preferences_content, encoding="utf-8")

            # Write journal file content
            if isinstance(journal_content, bytes):
                journal_file.write_bytes(journal_content)
            else:
                journal_file.write_text(journal_content, encoding="utf-8")

            argv = [
                "--progress-file", str(progress_file),
                "--preferences-file", str(preferences_file),
                "--journal-file", str(journal_file),
                "--output-dir", str(output_dir),
            ]

            try:
                result = main(argv)
            except SystemExit as exc:
                # SystemExit is acceptable — load_progress calls sys.exit(1)
                result = exc.code if isinstance(exc.code, int) else 1

            assert result in (0, 1), f"Unexpected exit code: {result}"


# ---------------------------------------------------------------------------
# Strategies for Property 7
# ---------------------------------------------------------------------------

st_module_numbers = st.lists(
    st.integers(min_value=1, max_value=11), unique=True, min_size=1
)
"""Strategy generating a random non-empty subset of module numbers (1-11)."""

st_track_name = st.sampled_from(["Core Bootcamp", "Advanced Topics", "Unknown"])
"""Strategy generating a valid track name."""


class TestPropertySkillsAndNextSteps:
    """Property 7: Skills and next-steps derived from completed track and modules.

    For any set of completed modules and a valid track name, the certificate
    SHALL contain a skills section with at least one skill per completed module,
    and a next-steps section with recommendations appropriate to the track.

    Validates: Requirements 7.1, 7.2
    """

    @given(modules=st_module_numbers, track=st_track_name)
    @settings(max_examples=20)
    def test_at_least_one_skill_per_module_with_mapping(
        self, modules: list[int], track: str
    ) -> None:
        """For each completed module in MODULE_SKILLS, at least one skill appears."""
        module_names = {num: f"Module {num}" for num in modules}
        progress = ProgressData(modules_completed=sorted(modules), module_names=module_names)
        prefs = PreferencesData(track=track, language="Python")
        journal = JournalData(entries={}, er_metrics=None)

        cert = assemble_certificate(progress, prefs, journal, "test-project")

        for num in modules:
            if num in MODULE_SKILLS:
                module_skills = MODULE_SKILLS[num]
                assert any(
                    skill in cert.skills for skill in module_skills
                ), f"No skill from module {num} found in certificate skills"

    @given(modules=st_module_numbers, track=st_track_name)
    @settings(max_examples=20)
    def test_next_steps_non_empty(self, modules: list[int], track: str) -> None:
        """The certificate's next_steps list is always non-empty."""
        module_names = {num: f"Module {num}" for num in modules}
        progress = ProgressData(modules_completed=sorted(modules), module_names=module_names)
        prefs = PreferencesData(track=track, language="Python")
        journal = JournalData(entries={}, er_metrics=None)

        cert = assemble_certificate(progress, prefs, journal, "test-project")

        assert len(cert.next_steps) > 0, "next_steps should not be empty"

    @given(modules=st_module_numbers)
    @settings(max_examples=20)
    def test_core_bootcamp_next_steps_match(self, modules: list[int]) -> None:
        """For Core Bootcamp track, next_steps match derive_next_steps('Core Bootcamp')."""
        module_names = {num: f"Module {num}" for num in modules}
        progress = ProgressData(modules_completed=sorted(modules), module_names=module_names)
        prefs = PreferencesData(track="Core Bootcamp", language="Python")
        journal = JournalData(entries={}, er_metrics=None)

        cert = assemble_certificate(progress, prefs, journal, "test-project")

        assert cert.next_steps == derive_next_steps("Core Bootcamp")

    @given(modules=st_module_numbers)
    @settings(max_examples=20)
    def test_advanced_topics_next_steps_match(self, modules: list[int]) -> None:
        """For Advanced Topics track, next_steps match derive_next_steps('Advanced Topics')."""
        module_names = {num: f"Module {num}" for num in modules}
        progress = ProgressData(modules_completed=sorted(modules), module_names=module_names)
        prefs = PreferencesData(track="Advanced Topics", language="Python")
        journal = JournalData(entries={}, er_metrics=None)

        cert = assemble_certificate(progress, prefs, journal, "test-project")

        assert cert.next_steps == derive_next_steps("Advanced Topics")


# ---------------------------------------------------------------------------
# Strategies for Property 2
# ---------------------------------------------------------------------------

st_project_name = st.text(
    min_size=1, max_size=50,
    alphabet=st.characters(whitelist_categories=("L", "N", "P")),
)
"""Strategy generating random project names from letters, numbers, and punctuation."""

st_completion_date = st.dates().map(lambda d: d.isoformat())
"""Strategy generating random ISO 8601 date strings."""

st_track = st.sampled_from(["Core Bootcamp", "Advanced Topics", "Unknown"])
"""Strategy generating a valid track name."""

st_module_record = st.builds(
    ModuleRecord,
    number=st.integers(min_value=1, max_value=11),
    name=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N", "P"))),
    outcome=st.text(min_size=0, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z"))),
)
"""Strategy generating a random ModuleRecord."""

st_skill = st.text(
    min_size=1, max_size=40,
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
)
"""Strategy generating a random skill string."""

st_next_step = st.text(
    min_size=1, max_size=60,
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
)
"""Strategy generating a random next-step string."""


class TestPropertyHtmlStructure:
    """Property 2: HTML output is valid HTML5 structure.

    For any valid input that produces a successful generation, the HTML output
    SHALL contain a <!DOCTYPE html> declaration, <html> root element, <head>
    section with <style> block, and <body> section with content.

    Validates: Requirements 3.5
    """

    @given(
        project_name=st_project_name,
        completion_date=st_completion_date,
        track=st_track,
        modules=st.lists(st_module_record, min_size=0, max_size=5),
        skills=st.lists(st_skill, min_size=0, max_size=5),
        next_steps=st.lists(st_next_step, min_size=0, max_size=4),
    )
    @settings(max_examples=20)
    def test_html_starts_with_doctype(
        self,
        project_name: str,
        completion_date: str,
        track: str,
        modules: list,
        skills: list[str],
        next_steps: list[str],
    ) -> None:
        """HTML output starts with <!DOCTYPE html>."""
        data = CertificateData(
            project_name=project_name,
            completion_date=completion_date,
            track=track,
            modules=modules,
            er_metrics=None,
            skills=skills,
            next_steps=next_steps,
        )

        result = render_html(data)

        assert result.startswith("<!DOCTYPE html>"), (
            f"HTML output must start with <!DOCTYPE html>, got: {result[:50]!r}"
        )

    @given(
        project_name=st_project_name,
        completion_date=st_completion_date,
        track=st_track,
        modules=st.lists(st_module_record, min_size=0, max_size=5),
        skills=st.lists(st_skill, min_size=0, max_size=5),
        next_steps=st.lists(st_next_step, min_size=0, max_size=4),
    )
    @settings(max_examples=20)
    def test_html_contains_html_tag(
        self,
        project_name: str,
        completion_date: str,
        track: str,
        modules: list,
        skills: list[str],
        next_steps: list[str],
    ) -> None:
        """HTML output contains <html tag."""
        data = CertificateData(
            project_name=project_name,
            completion_date=completion_date,
            track=track,
            modules=modules,
            er_metrics=None,
            skills=skills,
            next_steps=next_steps,
        )

        result = render_html(data)

        assert "<html" in result, "HTML output must contain <html tag"

    @given(
        project_name=st_project_name,
        completion_date=st_completion_date,
        track=st_track,
        modules=st.lists(st_module_record, min_size=0, max_size=5),
        skills=st.lists(st_skill, min_size=0, max_size=5),
        next_steps=st.lists(st_next_step, min_size=0, max_size=4),
    )
    @settings(max_examples=20)
    def test_html_contains_head_section(
        self,
        project_name: str,
        completion_date: str,
        track: str,
        modules: list,
        skills: list[str],
        next_steps: list[str],
    ) -> None:
        """HTML output contains <head> and </head>."""
        data = CertificateData(
            project_name=project_name,
            completion_date=completion_date,
            track=track,
            modules=modules,
            er_metrics=None,
            skills=skills,
            next_steps=next_steps,
        )

        result = render_html(data)

        assert "<head>" in result, "HTML output must contain <head>"
        assert "</head>" in result, "HTML output must contain </head>"

    @given(
        project_name=st_project_name,
        completion_date=st_completion_date,
        track=st_track,
        modules=st.lists(st_module_record, min_size=0, max_size=5),
        skills=st.lists(st_skill, min_size=0, max_size=5),
        next_steps=st.lists(st_next_step, min_size=0, max_size=4),
    )
    @settings(max_examples=20)
    def test_html_contains_style_within_head(
        self,
        project_name: str,
        completion_date: str,
        track: str,
        modules: list,
        skills: list[str],
        next_steps: list[str],
    ) -> None:
        """HTML output contains <style> and </style> within head section."""
        data = CertificateData(
            project_name=project_name,
            completion_date=completion_date,
            track=track,
            modules=modules,
            er_metrics=None,
            skills=skills,
            next_steps=next_steps,
        )

        result = render_html(data)

        head_start = result.index("<head>")
        head_end = result.index("</head>")
        head_section = result[head_start:head_end]

        assert "<style>" in head_section, "HTML <head> must contain <style>"
        assert "</style>" in head_section, "HTML <head> must contain </style>"

    @given(
        project_name=st_project_name,
        completion_date=st_completion_date,
        track=st_track,
        modules=st.lists(st_module_record, min_size=0, max_size=5),
        skills=st.lists(st_skill, min_size=0, max_size=5),
        next_steps=st.lists(st_next_step, min_size=0, max_size=4),
    )
    @settings(max_examples=20)
    def test_html_contains_body_section(
        self,
        project_name: str,
        completion_date: str,
        track: str,
        modules: list,
        skills: list[str],
        next_steps: list[str],
    ) -> None:
        """HTML output contains <body> and </body>."""
        data = CertificateData(
            project_name=project_name,
            completion_date=completion_date,
            track=track,
            modules=modules,
            er_metrics=None,
            skills=skills,
            next_steps=next_steps,
        )

        result = render_html(data)

        assert "<body>" in result, "HTML output must contain <body>"
        assert "</body>" in result, "HTML output must contain </body>"


# ---------------------------------------------------------------------------
# Strategies for Property 5
# ---------------------------------------------------------------------------

st_outcome_text = st.text(
    min_size=3, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N", "Zs"))
)
"""Strategy generating simple alphanumeric outcome text (avoids HTML escaping issues)."""


class TestPropertyJournalOutcomes:
    """Property 5: Journal outcomes appear for matching modules.

    For any journal file containing outcome entries for a subset of completed
    modules, the generated certificate SHALL include the outcome text for each
    module that has a matching journal entry.

    Validates: Requirements 5.2
    """

    @given(
        modules=st.lists(
            st.integers(min_value=1, max_value=11), unique=True, min_size=1
        ),
        data=st.data(),
    )
    @settings(max_examples=20)
    def test_outcome_text_appears_in_markdown(
        self, modules: list[int], data: st.DataObject
    ) -> None:
        """For each module with a non-empty outcome, that text appears in Markdown output."""
        # Pick a random non-empty subset of modules to have outcomes
        subset_size = data.draw(
            st.integers(min_value=1, max_value=len(modules)), label="subset_size"
        )
        modules_with_outcomes = data.draw(
            st.lists(
                st.sampled_from(modules), min_size=subset_size, max_size=subset_size, unique=True
            ),
            label="modules_with_outcomes",
        )

        # Generate outcome text for each module in the subset
        outcomes: dict[int, str] = {}
        for mod_num in modules_with_outcomes:
            outcome = data.draw(st_outcome_text, label=f"outcome_{mod_num}")
            outcomes[mod_num] = outcome

        # Build CertificateData
        module_names = {num: f"Module {num}" for num in modules}
        module_records = [
            ModuleRecord(
                number=num,
                name=f"Module {num}",
                outcome=outcomes.get(num, ""),
            )
            for num in sorted(modules)
        ]
        cert_data = CertificateData(
            project_name="test-project",
            completion_date="2024-01-15",
            track="Core Bootcamp",
            modules=module_records,
            er_metrics=None,
            skills=["Skill A"],
            next_steps=["Next step"],
        )

        md_output = render_markdown(cert_data)

        # Assert each non-empty outcome appears in the Markdown output
        for mod_num, outcome in outcomes.items():
            if outcome.strip():
                assert outcome in md_output, (
                    f"Outcome '{outcome}' for module {mod_num} not found in Markdown output"
                )

    @given(
        modules=st.lists(
            st.integers(min_value=1, max_value=11), unique=True, min_size=1
        ),
        data=st.data(),
    )
    @settings(max_examples=20)
    def test_outcome_text_appears_in_html(
        self, modules: list[int], data: st.DataObject
    ) -> None:
        """For each module with a non-empty outcome, that text (html-escaped) appears in HTML."""
        # Pick a random non-empty subset of modules to have outcomes
        subset_size = data.draw(
            st.integers(min_value=1, max_value=len(modules)), label="subset_size"
        )
        modules_with_outcomes = data.draw(
            st.lists(
                st.sampled_from(modules), min_size=subset_size, max_size=subset_size, unique=True
            ),
            label="modules_with_outcomes",
        )

        # Generate outcome text for each module in the subset
        outcomes: dict[int, str] = {}
        for mod_num in modules_with_outcomes:
            outcome = data.draw(st_outcome_text, label=f"outcome_{mod_num}")
            outcomes[mod_num] = outcome

        # Build CertificateData
        module_records = [
            ModuleRecord(
                number=num,
                name=f"Module {num}",
                outcome=outcomes.get(num, ""),
            )
            for num in sorted(modules)
        ]
        cert_data = CertificateData(
            project_name="test-project",
            completion_date="2024-01-15",
            track="Core Bootcamp",
            modules=module_records,
            er_metrics=None,
            skills=["Skill A"],
            next_steps=["Next step"],
        )

        html_output = render_html(cert_data)

        # Assert each non-empty outcome (html-escaped) appears in the HTML output
        for mod_num, outcome in outcomes.items():
            if outcome.strip():
                escaped_outcome = html.escape(outcome)
                assert escaped_outcome in html_output, (
                    f"Escaped outcome '{escaped_outcome}' for module {mod_num} "
                    f"not found in HTML output"
                )


# ---------------------------------------------------------------------------
# Strategies for Property 3
# ---------------------------------------------------------------------------

st_identity_project_name = st.text(
    min_size=1, max_size=30,
    alphabet=st.characters(whitelist_categories=("L", "N")),
)
"""Strategy generating alphanumeric project names (avoids HTML escaping issues)."""

st_identity_completion_date = st.dates().map(lambda d: d.isoformat())
"""Strategy generating random ISO 8601 date strings."""

st_identity_track = st.sampled_from(["Core Bootcamp", "Advanced Topics", "Unknown"])
"""Strategy generating a valid track name."""


class TestPropertyIdentityMetadata:
    """Property 3: Certificate contains identity metadata.

    For any valid input, the generated certificate (both Markdown and HTML) SHALL
    contain the project name, a completion date in ISO 8601 format (YYYY-MM-DD),
    and the track name from the preferences file (or "Unknown" if preferences
    are missing).

    Validates: Requirements 4.1, 4.2, 4.3
    """

    @given(
        project_name=st_identity_project_name,
        completion_date=st_identity_completion_date,
        track=st_identity_track,
    )
    @settings(max_examples=20)
    def test_markdown_contains_project_name(
        self,
        project_name: str,
        completion_date: str,
        track: str,
    ) -> None:
        """Markdown output contains the project name."""
        data = CertificateData(
            project_name=project_name,
            completion_date=completion_date,
            track=track,
            modules=[ModuleRecord(number=1, name="Business Problem", outcome="")],
            er_metrics=None,
            skills=["SDK Installation"],
            next_steps=["Explore advanced topics"],
        )

        result = render_markdown(data)

        assert project_name in result, (
            f"Project name {project_name!r} not found in Markdown output"
        )

    @given(
        project_name=st_identity_project_name,
        completion_date=st_identity_completion_date,
        track=st_identity_track,
    )
    @settings(max_examples=20)
    def test_markdown_contains_completion_date(
        self,
        project_name: str,
        completion_date: str,
        track: str,
    ) -> None:
        """Markdown output contains the ISO 8601 completion date."""
        data = CertificateData(
            project_name=project_name,
            completion_date=completion_date,
            track=track,
            modules=[ModuleRecord(number=1, name="Business Problem", outcome="")],
            er_metrics=None,
            skills=["SDK Installation"],
            next_steps=["Explore advanced topics"],
        )

        result = render_markdown(data)

        assert completion_date in result, (
            f"Completion date {completion_date!r} not found in Markdown output"
        )

    @given(
        project_name=st_identity_project_name,
        completion_date=st_identity_completion_date,
        track=st_identity_track,
    )
    @settings(max_examples=20)
    def test_markdown_contains_track_name(
        self,
        project_name: str,
        completion_date: str,
        track: str,
    ) -> None:
        """Markdown output contains the track name."""
        data = CertificateData(
            project_name=project_name,
            completion_date=completion_date,
            track=track,
            modules=[ModuleRecord(number=1, name="Business Problem", outcome="")],
            er_metrics=None,
            skills=["SDK Installation"],
            next_steps=["Explore advanced topics"],
        )

        result = render_markdown(data)

        assert track in result, (
            f"Track name {track!r} not found in Markdown output"
        )

    @given(
        project_name=st_identity_project_name,
        completion_date=st_identity_completion_date,
        track=st_identity_track,
    )
    @settings(max_examples=20)
    def test_html_contains_project_name(
        self,
        project_name: str,
        completion_date: str,
        track: str,
    ) -> None:
        """HTML output contains the project name (escaped for HTML)."""
        data = CertificateData(
            project_name=project_name,
            completion_date=completion_date,
            track=track,
            modules=[ModuleRecord(number=1, name="Business Problem", outcome="")],
            er_metrics=None,
            skills=["SDK Installation"],
            next_steps=["Explore advanced topics"],
        )

        result = render_html(data)
        escaped_project_name = html.escape(project_name)

        assert escaped_project_name in result, (
            f"Project name {escaped_project_name!r} not found in HTML output"
        )

    @given(
        project_name=st_identity_project_name,
        completion_date=st_identity_completion_date,
        track=st_identity_track,
    )
    @settings(max_examples=20)
    def test_html_contains_completion_date(
        self,
        project_name: str,
        completion_date: str,
        track: str,
    ) -> None:
        """HTML output contains the ISO 8601 completion date."""
        data = CertificateData(
            project_name=project_name,
            completion_date=completion_date,
            track=track,
            modules=[ModuleRecord(number=1, name="Business Problem", outcome="")],
            er_metrics=None,
            skills=["SDK Installation"],
            next_steps=["Explore advanced topics"],
        )

        result = render_html(data)
        escaped_date = html.escape(completion_date)

        assert escaped_date in result, (
            f"Completion date {escaped_date!r} not found in HTML output"
        )

    @given(
        project_name=st_identity_project_name,
        completion_date=st_identity_completion_date,
        track=st_identity_track,
    )
    @settings(max_examples=20)
    def test_html_contains_track_name(
        self,
        project_name: str,
        completion_date: str,
        track: str,
    ) -> None:
        """HTML output contains the track name (escaped for HTML)."""
        data = CertificateData(
            project_name=project_name,
            completion_date=completion_date,
            track=track,
            modules=[ModuleRecord(number=1, name="Business Problem", outcome="")],
            er_metrics=None,
            skills=["SDK Installation"],
            next_steps=["Explore advanced topics"],
        )

        result = render_html(data)
        escaped_track = html.escape(track)

        assert escaped_track in result, (
            f"Track name {escaped_track!r} not found in HTML output"
        )


# ---------------------------------------------------------------------------
# Strategies for Property 4
# ---------------------------------------------------------------------------

st_module_numbers_p4 = st.lists(
    st.integers(min_value=1, max_value=11), unique=True, min_size=1
)
"""Strategy generating a random non-empty subset of module numbers (1-11)."""


class TestPropertyAllModulesAppear:
    """Property 4: All completed modules appear in certificate.

    For any valid progress file listing N completed modules, the generated
    certificate SHALL contain all N module numbers and their corresponding names.

    Validates: Requirements 5.1
    """

    @given(modules=st_module_numbers_p4)
    @settings(max_examples=20)
    def test_all_module_numbers_appear_in_markdown(
        self, modules: list[int]
    ) -> None:
        """Every module number (as string) appears in the Markdown output."""
        sorted_modules = sorted(modules)
        module_names = {num: MODULE_NAMES.get(num, f"Module {num}") for num in sorted_modules}
        progress = ProgressData(modules_completed=sorted_modules, module_names=module_names)
        prefs = PreferencesData(track="Core Bootcamp", language="Python")
        journal = JournalData(entries={}, er_metrics=None)

        cert = assemble_certificate(progress, prefs, journal, "test-project")
        md_output = render_markdown(cert)

        for num in sorted_modules:
            assert str(num) in md_output, (
                f"Module number {num} not found in Markdown output"
            )

    @given(modules=st_module_numbers_p4)
    @settings(max_examples=20)
    def test_all_module_names_appear_in_markdown(
        self, modules: list[int]
    ) -> None:
        """Every module name appears in the Markdown output."""
        sorted_modules = sorted(modules)
        module_names = {num: MODULE_NAMES.get(num, f"Module {num}") for num in sorted_modules}
        progress = ProgressData(modules_completed=sorted_modules, module_names=module_names)
        prefs = PreferencesData(track="Core Bootcamp", language="Python")
        journal = JournalData(entries={}, er_metrics=None)

        cert = assemble_certificate(progress, prefs, journal, "test-project")
        md_output = render_markdown(cert)

        for num in sorted_modules:
            name = module_names[num]
            assert name in md_output, (
                f"Module name '{name}' (module {num}) not found in Markdown output"
            )

    @given(modules=st_module_numbers_p4)
    @settings(max_examples=20)
    def test_all_module_numbers_appear_in_html(
        self, modules: list[int]
    ) -> None:
        """Every module number appears in the HTML output."""
        sorted_modules = sorted(modules)
        module_names = {num: MODULE_NAMES.get(num, f"Module {num}") for num in sorted_modules}
        progress = ProgressData(modules_completed=sorted_modules, module_names=module_names)
        prefs = PreferencesData(track="Core Bootcamp", language="Python")
        journal = JournalData(entries={}, er_metrics=None)

        cert = assemble_certificate(progress, prefs, journal, "test-project")
        html_output = render_html(cert)

        for num in sorted_modules:
            assert str(num) in html_output, (
                f"Module number {num} not found in HTML output"
            )

    @given(modules=st_module_numbers_p4)
    @settings(max_examples=20)
    def test_all_module_names_appear_in_html(
        self, modules: list[int]
    ) -> None:
        """Every module name (html-escaped) appears in the HTML output."""
        import html as html_mod

        sorted_modules = sorted(modules)
        module_names = {num: MODULE_NAMES.get(num, f"Module {num}") for num in sorted_modules}
        progress = ProgressData(modules_completed=sorted_modules, module_names=module_names)
        prefs = PreferencesData(track="Core Bootcamp", language="Python")
        journal = JournalData(entries={}, er_metrics=None)

        cert = assemble_certificate(progress, prefs, journal, "test-project")
        html_output = render_html(cert)

        for num in sorted_modules:
            name = module_names[num]
            escaped_name = html_mod.escape(name)
            assert escaped_name in html_output, (
                f"Module name '{escaped_name}' (module {num}) not found in HTML output"
            )


# ---------------------------------------------------------------------------
# Strategies for Property 6
# ---------------------------------------------------------------------------

st_entity_count = st.one_of(
    st.none(),
    st.from_regex(r'[0-9]{1,3}(,[0-9]{3})*', fullmatch=True),
)
"""Strategy generating optional entity count strings (e.g. '1,234' or None)."""

st_match_rate = st.one_of(
    st.none(),
    st.from_regex(r'[0-9]{1,3}(\.[0-9]{1,2})?%?', fullmatch=True),
)
"""Strategy generating optional match rate strings (e.g. '95.5%' or None)."""

st_data_sources_loaded = st.one_of(
    st.none(),
    st.from_regex(r'[0-9]{1,2}', fullmatch=True),
)
"""Strategy generating optional data sources loaded strings (e.g. '3' or None)."""


class TestPropertyERMetrics:
    """Property 6: ER metrics from journal appear in certificate.

    For any journal file containing ER-related metrics (entity counts, match rates,
    data sources loaded), the generated certificate SHALL include those metrics in
    the ER results summary section. When no ER metrics are present, the certificate
    SHALL contain a placeholder statement.

    Validates: Requirements 6.1, 6.2
    """

    @given(
        entity_count=st_entity_count,
        match_rate=st_match_rate,
        data_sources_loaded=st_data_sources_loaded,
    )
    @settings(max_examples=20)
    def test_entity_count_appears_in_output(
        self,
        entity_count: str | None,
        match_rate: str | None,
        data_sources_loaded: str | None,
    ) -> None:
        """When er_metrics has entity_count, that value appears in both outputs."""
        er_metrics = ERMetrics(
            entity_count=entity_count,
            match_rate=match_rate,
            data_sources_loaded=data_sources_loaded,
        )
        cert_data = CertificateData(
            project_name="test-project",
            completion_date="2024-01-15",
            track="Core Bootcamp",
            modules=[ModuleRecord(number=1, name="Business Problem", outcome="Done")],
            er_metrics=er_metrics,
            skills=["Skill A"],
            next_steps=["Next step"],
        )

        md_output = render_markdown(cert_data)
        html_output = render_html(cert_data)

        if entity_count is not None:
            assert entity_count in md_output, (
                f"entity_count '{entity_count}' not found in Markdown output"
            )
            assert html.escape(entity_count) in html_output, (
                f"entity_count '{entity_count}' not found in HTML output"
            )

    @given(
        entity_count=st_entity_count,
        match_rate=st_match_rate,
        data_sources_loaded=st_data_sources_loaded,
    )
    @settings(max_examples=20)
    def test_match_rate_appears_in_output(
        self,
        entity_count: str | None,
        match_rate: str | None,
        data_sources_loaded: str | None,
    ) -> None:
        """When er_metrics has match_rate, that value appears in both outputs."""
        er_metrics = ERMetrics(
            entity_count=entity_count,
            match_rate=match_rate,
            data_sources_loaded=data_sources_loaded,
        )
        cert_data = CertificateData(
            project_name="test-project",
            completion_date="2024-01-15",
            track="Core Bootcamp",
            modules=[ModuleRecord(number=1, name="Business Problem", outcome="Done")],
            er_metrics=er_metrics,
            skills=["Skill A"],
            next_steps=["Next step"],
        )

        md_output = render_markdown(cert_data)
        html_output = render_html(cert_data)

        if match_rate is not None:
            assert match_rate in md_output, (
                f"match_rate '{match_rate}' not found in Markdown output"
            )
            assert html.escape(match_rate) in html_output, (
                f"match_rate '{match_rate}' not found in HTML output"
            )

    @given(
        entity_count=st_entity_count,
        match_rate=st_match_rate,
        data_sources_loaded=st_data_sources_loaded,
    )
    @settings(max_examples=20)
    def test_data_sources_loaded_appears_in_output(
        self,
        entity_count: str | None,
        match_rate: str | None,
        data_sources_loaded: str | None,
    ) -> None:
        """When er_metrics has data_sources_loaded, that value appears in both outputs."""
        er_metrics = ERMetrics(
            entity_count=entity_count,
            match_rate=match_rate,
            data_sources_loaded=data_sources_loaded,
        )
        cert_data = CertificateData(
            project_name="test-project",
            completion_date="2024-01-15",
            track="Core Bootcamp",
            modules=[ModuleRecord(number=1, name="Business Problem", outcome="Done")],
            er_metrics=er_metrics,
            skills=["Skill A"],
            next_steps=["Next step"],
        )

        md_output = render_markdown(cert_data)
        html_output = render_html(cert_data)

        if data_sources_loaded is not None:
            assert data_sources_loaded in md_output, (
                f"data_sources_loaded '{data_sources_loaded}' not found in Markdown output"
            )
            assert html.escape(data_sources_loaded) in html_output, (
                f"data_sources_loaded '{data_sources_loaded}' not found in HTML output"
            )

    @given(
        modules=st.lists(
            st.integers(min_value=1, max_value=11), unique=True, min_size=1
        ),
    )
    @settings(max_examples=20)
    def test_placeholder_when_er_metrics_none(
        self, modules: list[int]
    ) -> None:
        """When er_metrics is None, placeholder text appears in both outputs."""
        module_records = [
            ModuleRecord(number=num, name=f"Module {num}", outcome="")
            for num in sorted(modules)
        ]
        cert_data = CertificateData(
            project_name="test-project",
            completion_date="2024-01-15",
            track="Core Bootcamp",
            modules=module_records,
            er_metrics=None,
            skills=["Skill A"],
            next_steps=["Next step"],
        )

        md_output = render_markdown(cert_data)
        html_output = render_html(cert_data)

        placeholder = "Entity resolution results were not recorded."
        assert placeholder in md_output, (
            f"Placeholder '{placeholder}' not found in Markdown output"
        )
        assert placeholder in html_output, (
            f"Placeholder '{placeholder}' not found in HTML output"
        )


# ---------------------------------------------------------------------------
# Strategies for Property 1
# ---------------------------------------------------------------------------

st_completed_modules_p1 = st.lists(
    st.integers(min_value=1, max_value=11), unique=True, min_size=1
)
"""Strategy generating a random non-empty subset of module numbers (1-11)."""


class TestPropertyBothFilesProduced:
    """Property 1: Successful generation produces both output files.

    For any valid progress file (with at least one completed module), valid or
    missing preferences file, and valid or missing journal file, invoking the
    Certificate_Generator SHALL produce both graduation_certificate.md and
    graduation_certificate.html in the output directory and exit with code 0.

    Validates: Requirements 2.7, 3.1, 3.2
    """

    @given(modules=st_completed_modules_p1)
    @settings(max_examples=20)
    def test_both_files_produced_and_exit_zero(
        self, modules: list[int]
    ) -> None:
        """main() returns 0 and produces both .md and .html files for valid input."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            progress_file = tmp_path / "progress.json"
            output_dir = tmp_path / "output"

            # Create valid progress JSON
            progress_data = {"modules_completed": sorted(modules)}
            progress_file.write_text(json.dumps(progress_data), encoding="utf-8")

            argv = [
                "--progress-file", str(progress_file),
                "--preferences-file", str(tmp_path / "nonexistent_prefs.yaml"),
                "--journal-file", str(tmp_path / "nonexistent_journal.md"),
                "--output-dir", str(output_dir),
            ]

            result = main(argv)

            assert result == 0, f"Expected exit code 0, got {result}"
            assert (output_dir / "graduation_certificate.md").exists(), (
                "graduation_certificate.md was not created"
            )
            assert (output_dir / "graduation_certificate.html").exists(), (
                "graduation_certificate.html was not created"
            )

    @given(modules=st_completed_modules_p1)
    @settings(max_examples=20)
    def test_both_files_are_non_empty(
        self, modules: list[int]
    ) -> None:
        """Both output files are non-empty when generation succeeds."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            progress_file = tmp_path / "progress.json"
            output_dir = tmp_path / "output"

            # Create valid progress JSON
            progress_data = {"modules_completed": sorted(modules)}
            progress_file.write_text(json.dumps(progress_data), encoding="utf-8")

            argv = [
                "--progress-file", str(progress_file),
                "--preferences-file", str(tmp_path / "nonexistent_prefs.yaml"),
                "--journal-file", str(tmp_path / "nonexistent_journal.md"),
                "--output-dir", str(output_dir),
            ]

            result = main(argv)

            assert result == 0
            md_file = output_dir / "graduation_certificate.md"
            html_file = output_dir / "graduation_certificate.html"
            assert md_file.stat().st_size > 0, (
                "graduation_certificate.md is empty"
            )
            assert html_file.stat().st_size > 0, (
                "graduation_certificate.html is empty"
            )

    @given(modules=st_completed_modules_p1)
    @settings(max_examples=20)
    def test_both_files_produced_with_preferences(
        self, modules: list[int]
    ) -> None:
        """main() produces both files when preferences file is also present."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            progress_file = tmp_path / "progress.json"
            preferences_file = tmp_path / "preferences.yaml"
            output_dir = tmp_path / "output"

            # Create valid progress JSON
            progress_data = {"modules_completed": sorted(modules)}
            progress_file.write_text(json.dumps(progress_data), encoding="utf-8")

            # Create valid preferences YAML
            preferences_file.write_text(
                "track: Core Bootcamp\nlanguage: Python\n", encoding="utf-8"
            )

            argv = [
                "--progress-file", str(progress_file),
                "--preferences-file", str(preferences_file),
                "--journal-file", str(tmp_path / "nonexistent_journal.md"),
                "--output-dir", str(output_dir),
            ]

            result = main(argv)

            assert result == 0, f"Expected exit code 0, got {result}"
            assert (output_dir / "graduation_certificate.md").exists(), (
                "graduation_certificate.md was not created"
            )
            assert (output_dir / "graduation_certificate.html").exists(), (
                "graduation_certificate.html was not created"
            )

    @given(modules=st_completed_modules_p1)
    @settings(max_examples=20)
    def test_both_files_produced_with_journal(
        self, modules: list[int]
    ) -> None:
        """main() produces both files when journal file is also present."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            progress_file = tmp_path / "progress.json"
            journal_file = tmp_path / "journal.md"
            output_dir = tmp_path / "output"

            # Create valid progress JSON
            progress_data = {"modules_completed": sorted(modules)}
            progress_file.write_text(json.dumps(progress_data), encoding="utf-8")

            # Create a simple journal file
            journal_content = "# Bootcamp Journal\n\n"
            for num in modules[:2]:
                journal_content += (
                    f"## Module {num}: Module {num} —\n\n"
                    f"**What we did:** Completed module {num} tasks.\n\n"
                )
            journal_file.write_text(journal_content, encoding="utf-8")

            argv = [
                "--progress-file", str(progress_file),
                "--preferences-file", str(tmp_path / "nonexistent_prefs.yaml"),
                "--journal-file", str(journal_file),
                "--output-dir", str(output_dir),
            ]

            result = main(argv)

            assert result == 0, f"Expected exit code 0, got {result}"
            assert (output_dir / "graduation_certificate.md").exists(), (
                "graduation_certificate.md was not created"
            )
            assert (output_dir / "graduation_certificate.html").exists(), (
                "graduation_certificate.html was not created"
            )


# ---------------------------------------------------------------------------
# Strategies for Property 9
# ---------------------------------------------------------------------------

st_idempotent_modules = st.lists(
    st.integers(min_value=1, max_value=11), unique=True, min_size=1
)
"""Strategy generating a random non-empty subset of module numbers (1-11) for idempotency test."""


class TestPropertyIdempotentOutput:
    """Property 9: Idempotent output.

    For any valid input set, running the Certificate_Generator twice with
    identical inputs SHALL produce byte-identical output files.

    Validates: Requirements 10.2
    """

    @given(modules=st_idempotent_modules)
    @settings(max_examples=20)
    def test_idempotent_markdown_output(self, modules: list[int]) -> None:
        """Running main() twice with same inputs produces identical Markdown files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create valid progress JSON
            progress_file = tmp_path / "progress.json"
            progress_file.write_text(
                json.dumps({"modules_completed": sorted(modules)}), encoding="utf-8"
            )

            output_dir = tmp_path / "output"

            argv = [
                "--progress-file", str(progress_file),
                "--preferences-file", str(tmp_path / "prefs.yaml"),
                "--journal-file", str(tmp_path / "journal.md"),
                "--output-dir", str(output_dir),
            ]

            # First run
            result1 = main(argv)
            assert result1 == 0, f"First run failed with exit code {result1}"

            md_file = output_dir / "graduation_certificate.md"
            md_content_run1 = md_file.read_text(encoding="utf-8")

            # Second run (same inputs, same output directory)
            result2 = main(argv)
            assert result2 == 0, f"Second run failed with exit code {result2}"

            md_content_run2 = md_file.read_text(encoding="utf-8")

            assert md_content_run1 == md_content_run2, (
                "Markdown output differs between two runs with identical inputs"
            )

    @given(modules=st_idempotent_modules)
    @settings(max_examples=20)
    def test_idempotent_html_output(self, modules: list[int]) -> None:
        """Running main() twice with same inputs produces identical HTML files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create valid progress JSON
            progress_file = tmp_path / "progress.json"
            progress_file.write_text(
                json.dumps({"modules_completed": sorted(modules)}), encoding="utf-8"
            )

            output_dir = tmp_path / "output"

            argv = [
                "--progress-file", str(progress_file),
                "--preferences-file", str(tmp_path / "prefs.yaml"),
                "--journal-file", str(tmp_path / "journal.md"),
                "--output-dir", str(output_dir),
            ]

            # First run
            result1 = main(argv)
            assert result1 == 0, f"First run failed with exit code {result1}"

            html_file = output_dir / "graduation_certificate.html"
            html_content_run1 = html_file.read_text(encoding="utf-8")

            # Second run (same inputs, same output directory)
            result2 = main(argv)
            assert result2 == 0, f"Second run failed with exit code {result2}"

            html_content_run2 = html_file.read_text(encoding="utf-8")

            assert html_content_run1 == html_content_run2, (
                "HTML output differs between two runs with identical inputs"
            )
