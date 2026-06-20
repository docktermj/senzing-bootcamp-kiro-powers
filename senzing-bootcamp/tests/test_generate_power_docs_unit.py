"""Example-based unit tests for generate_power_docs.py.

Feature: generated-power-docs

Consolidated unit-test module for the POWER.md documentation generator. This
file pins down concrete behavior, structural facts, and error messages for the
generator's helpers, region renderers, marker handling, and CLI. Additional
test classes are appended here as later tasks land.
"""

import sys
from pathlib import Path

import pytest

# Make scripts importable (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import generate_power_docs
from generate_power_docs import (
    _BEGIN_MARKER_RE,
    _END_MARKER_RE,
    REGEN_COMMAND,
    TOOL_DESCRIPTIONS,
    GeneratorError,
    MarkerError,
    McpToolsRegion,
    ModuleInfo,
    ModulesRegion,
    SourcePaths,
    Sources,
    SteeringFileInfo,
    SteeringRegion,
    assemble,
    kiro_include,
    load_sources,
    locate_regions,
    main,
    normalize_newlines,
    verify,
    write_atomic,
)

# ---------------------------------------------------------------------------
# 1.3 normalize_newlines (Req 5.5, 5.6)
# ---------------------------------------------------------------------------


class TestNormalizeNewlines:
    """normalize_newlines converts CRLF/CR to LF and ensures one trailing LF."""

    def test_crlf_becomes_lf(self):
        """Windows CRLF line endings are converted to Unix LF."""
        result = normalize_newlines("a\r\nb\r\nc\n")
        assert result == "a\nb\nc\n"
        assert "\r" not in result

    def test_bare_cr_becomes_lf(self):
        """Classic-Mac bare CR line endings are converted to Unix LF."""
        result = normalize_newlines("a\rb\rc")
        assert result == "a\nb\nc\n"
        assert "\r" not in result

    def test_mixed_endings_all_become_lf(self):
        """A mix of CRLF, bare CR, and LF all normalize to LF."""
        result = normalize_newlines("a\r\nb\rc\nd")
        assert result == "a\nb\nc\nd\n"
        assert "\r" not in result

    def test_single_trailing_newline_added_when_absent(self):
        """Content without a trailing newline gains exactly one."""
        assert normalize_newlines("hello") == "hello\n"

    def test_multiple_trailing_newlines_collapsed_to_one(self):
        """A run of trailing newlines collapses to exactly one LF."""
        assert normalize_newlines("hello\n\n\n") == "hello\n"

    def test_trailing_crlf_run_collapsed_to_single_lf(self):
        """Trailing CRLF runs collapse to a single trailing LF."""
        result = normalize_newlines("hello\r\n\r\n\r\n")
        assert result == "hello\n"
        assert "\r" not in result

    def test_already_normalized_is_unchanged(self):
        """Text already ending in a single LF is returned unchanged."""
        assert normalize_newlines("a\nb\n") == "a\nb\n"

    def test_empty_string_unchanged(self):
        """Empty content gains no trailing newline."""
        assert normalize_newlines("") == ""

    def test_output_has_no_carriage_returns(self):
        """No carriage returns survive normalization (Req 5.6)."""
        result = normalize_newlines("x\r\ny\r\rz\r\n")
        assert "\r" not in result

    def test_output_ends_with_exactly_one_lf(self):
        """Non-empty output terminates with exactly one trailing LF (Req 5.5)."""
        result = normalize_newlines("line1\r\nline2\r\n\r\n")
        assert result.endswith("\n")
        assert not result.endswith("\n\n")


# ---------------------------------------------------------------------------
# 1.3 write_atomic (Req 5.5, 5.6)
# ---------------------------------------------------------------------------


class TestWriteAtomic:
    """write_atomic fully replaces content and leaves no temp file behind."""

    def test_creates_file_with_exact_content(self, tmp_path):
        """Writing to a fresh path creates it with the exact content."""
        target = tmp_path / "POWER.md"
        write_atomic(target, "hello world\n")
        assert target.read_text(encoding="utf-8") == "hello world\n"

    def test_replaces_existing_content_fully(self, tmp_path):
        """An existing file is replaced entirely, not appended to."""
        target = tmp_path / "POWER.md"
        target.write_text("OLD CONTENT that is much longer than the new\n", encoding="utf-8")
        write_atomic(target, "new\n")
        assert target.read_text(encoding="utf-8") == "new\n"

    def test_leaves_no_temp_file_behind(self, tmp_path):
        """After a successful write only the target remains in the directory."""
        target = tmp_path / "POWER.md"
        write_atomic(target, "content\n")
        remaining = sorted(p.name for p in tmp_path.iterdir())
        assert remaining == ["POWER.md"]

    def test_repeated_writes_leave_no_temp_files(self, tmp_path):
        """Multiple successive writes never accumulate temp artifacts."""
        target = tmp_path / "POWER.md"
        for i in range(5):
            write_atomic(target, f"content {i}\n")
        remaining = sorted(p.name for p in tmp_path.iterdir())
        assert remaining == ["POWER.md"]
        assert target.read_text(encoding="utf-8") == "content 4\n"

    def test_written_bytes_use_lf_not_crlf(self, tmp_path):
        """Written bytes preserve LF exactly and add no carriage returns."""
        target = tmp_path / "POWER.md"
        write_atomic(target, "a\nb\nc\n")
        raw = target.read_bytes()
        assert b"\r" not in raw
        assert raw == b"a\nb\nc\n"

    def test_failure_leaves_no_temp_file(self, tmp_path):
        """A write failure cleans up the temp file and leaves no artifact."""
        # Point at a path whose parent does not exist so mkstemp raises.
        bad_target = tmp_path / "missing-dir" / "POWER.md"
        raised = False
        try:
            write_atomic(bad_target, "content\n")
        except OSError:
            raised = True
        assert raised
        # The (nonexistent) parent directory was never created and no stray
        # temp file landed in tmp_path.
        assert sorted(p.name for p in tmp_path.iterdir()) == []
        assert not bad_target.exists()


# ---------------------------------------------------------------------------
# 2.2 Marker regex matching (Req 2.1)
# ---------------------------------------------------------------------------


class TestMarkerRegex:
    """Begin/end markers match the HTML-comment regex and parse region ids."""

    def test_begin_marker_matches_and_parses_id(self):
        """A canonical begin marker matches and yields its region id."""
        match = _BEGIN_MARKER_RE.search("<!-- BEGIN GENERATED: mcp-tools -->")
        assert match is not None
        assert match.group("id") == "mcp-tools"

    def test_end_marker_matches_and_parses_id(self):
        """A canonical end marker matches and yields its region id."""
        match = _END_MARKER_RE.search("<!-- END GENERATED: mcp-tools -->")
        assert match is not None
        assert match.group("id") == "mcp-tools"

    def test_begin_marker_tolerates_extra_whitespace(self):
        """Surrounding/internal whitespace in the comment is tolerated."""
        match = _BEGIN_MARKER_RE.search("<!--   BEGIN GENERATED:   hooks   -->   ")
        assert match is not None
        assert match.group("id") == "hooks"

    def test_end_marker_tolerates_extra_whitespace(self):
        """Surrounding/internal whitespace in the end comment is tolerated."""
        match = _END_MARKER_RE.search("<!--  END GENERATED:  hooks  -->  ")
        assert match is not None
        assert match.group("id") == "hooks"

    def test_begin_marker_does_not_match_end_marker(self):
        """The begin regex does not match an end marker line."""
        assert _BEGIN_MARKER_RE.search("<!-- END GENERATED: mcp-tools -->") is None

    def test_end_marker_does_not_match_begin_marker(self):
        """The end regex does not match a begin marker line."""
        assert _END_MARKER_RE.search("<!-- BEGIN GENERATED: mcp-tools -->") is None

    def test_begin_marker_rejects_uppercase_id(self):
        """Region ids are lowercase/digits/hyphen only; uppercase is rejected."""
        assert _BEGIN_MARKER_RE.search("<!-- BEGIN GENERATED: McpTools -->") is None

    def test_region_ids_parsed_are_unique_across_markers(self):
        """All begin markers in a document parse to a unique set of ids."""
        doc = (
            "<!-- BEGIN GENERATED: mcp-tools -->\n"
            "<!-- END GENERATED: mcp-tools -->\n"
            "<!-- BEGIN GENERATED: hooks -->\n"
            "<!-- END GENERATED: hooks -->\n"
            "<!-- BEGIN GENERATED: steering -->\n"
            "<!-- END GENERATED: steering -->\n"
        )
        ids = [m.group("id") for m in _BEGIN_MARKER_RE.finditer(doc)]
        assert ids == ["mcp-tools", "hooks", "steering"]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# 2.2 locate_regions happy path and violations (Req 2.1, 2.4, 2.5, 2.6, 2.7)
# ---------------------------------------------------------------------------


def _doc(*lines: str) -> str:
    """Join marker/body lines into a newline-terminated document."""
    return "\n".join(lines) + "\n"


class TestLocateRegions:
    """locate_regions extracts region bodies and flags marker violations."""

    def test_happy_path_extracts_body_excluding_markers(self):
        """The body is the text strictly between begin and end marker lines."""
        doc = _doc(
            "intro prose",
            "<!-- BEGIN GENERATED: mcp-tools -->",
            "line one",
            "line two",
            "<!-- END GENERATED: mcp-tools -->",
            "outro prose",
        )
        spans = locate_regions(doc, {"mcp-tools"})
        assert set(spans) == {"mcp-tools"}
        span = spans["mcp-tools"]
        assert span.region_id == "mcp-tools"
        assert span.body == "line one\nline two\n"
        # Offsets reconstruct exactly the body and exclude both marker lines.
        assert doc[span.begin_marker_end : span.end_marker_start] == span.body
        assert "BEGIN GENERATED" not in span.body
        assert "END GENERATED" not in span.body

    def test_empty_body_between_adjacent_markers(self):
        """Adjacent begin/end markers yield an empty body."""
        doc = _doc(
            "<!-- BEGIN GENERATED: hooks -->",
            "<!-- END GENERATED: hooks -->",
        )
        spans = locate_regions(doc, {"hooks"})
        assert spans["hooks"].body == ""

    def test_multiple_regions_parsed_with_unique_ids(self):
        """Several regions are located and keyed by their unique ids."""
        doc = _doc(
            "<!-- BEGIN GENERATED: mcp-tools -->",
            "tools body",
            "<!-- END GENERATED: mcp-tools -->",
            "prose between",
            "<!-- BEGIN GENERATED: modules -->",
            "modules body",
            "<!-- END GENERATED: modules -->",
        )
        spans = locate_regions(doc, {"mcp-tools", "modules"})
        assert set(spans) == {"mcp-tools", "modules"}
        assert spans["mcp-tools"].body == "tools body\n"
        assert spans["modules"].body == "modules body\n"

    def test_duplicate_begin_marker_raises_naming_region(self):
        """A duplicated begin id raises MarkerError naming that region (Req 2.7)."""
        doc = _doc(
            "<!-- BEGIN GENERATED: mcp-tools -->",
            "first",
            "<!-- BEGIN GENERATED: mcp-tools -->",
            "second",
            "<!-- END GENERATED: mcp-tools -->",
        )
        with pytest.raises(MarkerError) as exc:
            locate_regions(doc, {"mcp-tools"})
        assert "mcp-tools" in exc.value.args

    def test_end_before_begin_raises_naming_region(self):
        """An end marker before its begin raises naming that region (Req 2.6)."""
        doc = _doc(
            "<!-- END GENERATED: hooks -->",
            "body",
            "<!-- BEGIN GENERATED: hooks -->",
        )
        with pytest.raises(MarkerError) as exc:
            locate_regions(doc, {"hooks"})
        assert "hooks" in exc.value.args

    def test_begin_without_end_raises_naming_region(self):
        """A begin marker with no matching end raises naming it (Req 2.5)."""
        doc = _doc(
            "<!-- BEGIN GENERATED: steering -->",
            "body that never closes",
        )
        with pytest.raises(MarkerError) as exc:
            locate_regions(doc, {"steering"})
        assert "steering" in exc.value.args

    def test_missing_expected_region_raises_naming_region(self):
        """An expected region absent from the doc raises naming it (Req 2.4)."""
        doc = _doc(
            "<!-- BEGIN GENERATED: mcp-tools -->",
            "tools",
            "<!-- END GENERATED: mcp-tools -->",
        )
        with pytest.raises(MarkerError) as exc:
            locate_regions(doc, {"mcp-tools", "modules"})
        assert "modules" in exc.value.args


# ---------------------------------------------------------------------------
# 3.2 load_sources error paths (Req 1.5)
# ---------------------------------------------------------------------------


def _write_world(tmp_path: Path) -> SourcePaths:
    """Build a valid throwaway source world under ``tmp_path``.

    Creates a hooks directory plus valid ``hook-categories.yaml``,
    ``steering-index.yaml``, and ``module-dependencies.yaml`` files so that
    ``load_sources`` succeeds. Individual files can then be broken by a test to
    exercise a specific error path. The ``power_md`` target is intentionally not
    created so tests can assert nothing was written.

    Args:
        tmp_path: The pytest temporary directory for this test.

    Returns:
        A :class:`SourcePaths` pointing entirely inside ``tmp_path``.
    """
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    hook_categories = hooks_dir / "hook-categories.yaml"
    hook_categories.write_text("critical: []\n", encoding="utf-8")

    steering_index = tmp_path / "steering" / "steering-index.yaml"
    steering_index.parent.mkdir()
    steering_index.write_text(
        "file_metadata: {}\nbudget:\n  total_tokens: 0\n", encoding="utf-8"
    )

    module_deps = tmp_path / "config" / "module-dependencies.yaml"
    module_deps.parent.mkdir()
    module_deps.write_text("modules: {}\n", encoding="utf-8")

    return SourcePaths(
        power_md=tmp_path / "POWER.md",
        hooks_dir=hooks_dir,
        hook_categories=hook_categories,
        steering_index=steering_index,
        module_deps=module_deps,
        repo_root=tmp_path,
    )


class TestLoadSourcesErrors:
    """load_sources surfaces read/parse failures naming the file and writes nothing."""

    def test_valid_world_loads_without_error(self, tmp_path):
        """The baseline world is valid so load_sources succeeds (guards the others)."""
        paths = _write_world(tmp_path)
        sources = load_sources(paths)
        assert sources.hooks == ()
        assert sources.steering == ()
        assert sources.modules == ()

    def test_missing_steering_index_names_path_and_writes_nothing(self, tmp_path):
        """A missing steering source raises GeneratorError naming the file path."""
        paths = _write_world(tmp_path)
        paths.steering_index.unlink()
        with pytest.raises(GeneratorError) as exc:
            load_sources(paths)
        assert str(paths.steering_index) in str(exc.value)
        # Nothing was written: the POWER.md target was never created.
        assert not paths.power_md.exists()

    def test_unparseable_module_yaml_names_path_and_writes_nothing(self, tmp_path):
        """A malformed YAML module source raises GeneratorError naming the file."""
        paths = _write_world(tmp_path)
        # Invalid YAML: unterminated flow mapping.
        paths.module_deps.write_text("modules: {unterminated: \n  - [a, b\n", encoding="utf-8")
        with pytest.raises(GeneratorError) as exc:
            load_sources(paths)
        message = str(exc.value)
        assert str(paths.module_deps) in message
        assert not paths.power_md.exists()

    def test_non_mapping_yaml_names_path_and_writes_nothing(self, tmp_path):
        """A YAML source that is not a top-level mapping names the file and aborts."""
        paths = _write_world(tmp_path)
        # A top-level sequence is valid YAML but not the expected mapping.
        paths.hook_categories.write_text("- not\n- a\n- mapping\n", encoding="utf-8")
        with pytest.raises(GeneratorError) as exc:
            load_sources(paths)
        assert str(paths.hook_categories) in str(exc.value)
        assert not paths.power_md.exists()

    def test_unreadable_source_includes_cause(self, tmp_path):
        """A read failure surfaces the offending path and the underlying cause."""
        paths = _write_world(tmp_path)
        # Replace the steering index file with a directory so read_text raises OSError.
        paths.steering_index.unlink()
        paths.steering_index.mkdir()
        with pytest.raises(GeneratorError) as exc:
            load_sources(paths)
        message = str(exc.value)
        assert str(paths.steering_index) in message
        assert not paths.power_md.exists()


# ---------------------------------------------------------------------------
# 3.2 kiro_include (Req 5.3)
# ---------------------------------------------------------------------------


class TestKiroInclude:
    """kiro_include emits a #[[file:<repo-relative-path>]] include directive."""

    def test_absolute_path_made_relative_to_repo_root(self):
        """An absolute path under the repo root becomes a repo-relative include."""
        result = kiro_include(
            Path("/repo"), Path("/repo/senzing-bootcamp/steering/x.md")
        )
        assert result == "#[[file:senzing-bootcamp/steering/x.md]]"

    def test_relative_path_used_as_given(self):
        """A repo-relative path is emitted unchanged inside the include."""
        result = kiro_include(Path("/repo"), Path("senzing-bootcamp/steering/x.md"))
        assert result == "#[[file:senzing-bootcamp/steering/x.md]]"

    def test_uses_posix_forward_slashes(self):
        """The emitted include path always uses POSIX forward slashes."""
        result = kiro_include(Path("/repo"), Path("/repo/config/module-dependencies.yaml"))
        assert result == "#[[file:config/module-dependencies.yaml]]"
        assert "\\" not in result

    def test_directly_nested_file(self):
        """A file directly under the repo root yields a bare filename include."""
        result = kiro_include(Path("/repo"), Path("/repo/POWER.md"))
        assert result == "#[[file:POWER.md]]"


# ---------------------------------------------------------------------------
# 4.2 McpToolsRegion error paths (Req 9.1, 9.4)
# ---------------------------------------------------------------------------


def _sources(tools: tuple[str, ...], total_count: int) -> Sources:
    """Build a minimal Sources for MCP-tools rendering.

    Only ``tools`` and ``total_count`` matter to :class:`McpToolsRegion`; the
    remaining fields are filled with empty/zero values.

    Args:
        tools: The tool ids to render.
        total_count: The reported ``TOTAL_COUNT`` for the inventory.

    Returns:
        A :class:`Sources` carrying the given tools and count.
    """
    return Sources(
        tools=tools,
        total_count=total_count,
        hooks=(),
        steering=(),
        steering_budget_total=0,
        modules=(),
    )


class TestMcpToolsRegion:
    """McpToolsRegion validates the tool inventory before rendering bullets."""

    def test_total_count_mismatch_reports_both_values_and_raises(self):
        """A TOTAL_COUNT that disagrees with len(tools) names BOTH numbers (Req 9.1)."""
        tools = tuple(TOOL_DESCRIPTIONS)
        wrong_count = len(tools) + 1
        sources = _sources(tools, wrong_count)
        with pytest.raises(GeneratorError) as exc:
            McpToolsRegion().render(sources)
        message = str(exc.value)
        assert str(wrong_count) in message
        assert str(len(tools)) in message

    def test_tool_missing_description_names_offending_tool(self):
        """A tool with no TOOL_DESCRIPTIONS entry is named in the error (Req 9.4)."""
        tools = tuple(TOOL_DESCRIPTIONS) + ("phantom_tool",)
        sources = _sources(tools, len(tools))
        with pytest.raises(GeneratorError) as exc:
            McpToolsRegion().render(sources)
        assert "phantom_tool" in str(exc.value)

    def test_happy_path_renders_one_bullet_per_tool(self):
        """A matching inventory renders without error, one bullet per tool."""
        tools = tuple(TOOL_DESCRIPTIONS)
        sources = _sources(tools, len(tools))
        body = McpToolsRegion().render(sources)
        bullets = [line for line in body.splitlines() if line.startswith("- `")]
        assert len(bullets) == len(tools)
        for tool in tools:
            assert f"- `{tool}`" in body


# ---------------------------------------------------------------------------
# 5.2 Hooks region cross-check error paths (Req 10.4, 10.5)
# ---------------------------------------------------------------------------


def _hooks_world(
    tmp_path: Path, categories_yaml: str, hook_ids: tuple[str, ...]
) -> SourcePaths:
    """Build a valid source world with a specific hook-categories file and hooks.

    Reuses :func:`_write_world` for the surrounding (valid) steering and module
    sources, then overwrites ``hook-categories.yaml`` with ``categories_yaml``
    and creates one minimal ``<id>.kiro.hook`` file per id in ``hook_ids``. The
    cross-check only inspects filenames, so the hook bodies are intentionally
    trivial (``{}``).

    Args:
        tmp_path: The pytest temporary directory for this test.
        categories_yaml: Raw YAML content for ``hook-categories.yaml``.
        hook_ids: Hook ids for which to create ``<id>.kiro.hook`` files.

    Returns:
        A :class:`SourcePaths` pointing entirely inside ``tmp_path``.
    """
    paths = _write_world(tmp_path)
    paths.hook_categories.write_text(categories_yaml, encoding="utf-8")
    for hook_id in hook_ids:
        (paths.hooks_dir / f"{hook_id}.kiro.hook").write_text("{}\n", encoding="utf-8")
    return paths


class TestHooksRegionCrossCheck:
    """load_sources cross-checks category lists against hook files (Req 10.4, 10.5)."""

    def test_category_critical_id_without_file_names_hook_and_aborts(self, tmp_path):
        """A critical-listed hook with no file names the hook and aborts (Req 10.4)."""
        paths = _hooks_world(
            tmp_path,
            categories_yaml="critical:\n  - phantom-hook\nmodules: {}\n",
            hook_ids=(),
        )
        with pytest.raises(GeneratorError) as exc:
            load_sources(paths)
        message = str(exc.value)
        assert "phantom-hook" in message
        assert not paths.power_md.exists()

    def test_category_module_id_without_file_names_hook_and_aborts(self, tmp_path):
        """A module-listed hook with no file names the hook and aborts (Req 10.4)."""
        paths = _hooks_world(
            tmp_path,
            categories_yaml="critical: []\nmodules:\n  3:\n    - ghost-hook\n",
            hook_ids=(),
        )
        with pytest.raises(GeneratorError) as exc:
            load_sources(paths)
        message = str(exc.value)
        assert "ghost-hook" in message
        assert not paths.power_md.exists()

    def test_category_any_id_without_file_names_hook_and_aborts(self, tmp_path):
        """An ``any:``-listed hook with no file names the hook and aborts (Req 10.4)."""
        paths = _hooks_world(
            tmp_path,
            categories_yaml="critical: []\nmodules:\n  any:\n    - vanished-hook\n",
            hook_ids=(),
        )
        with pytest.raises(GeneratorError) as exc:
            load_sources(paths)
        message = str(exc.value)
        assert "vanished-hook" in message
        assert not paths.power_md.exists()

    def test_discovered_file_in_no_category_names_hook_and_aborts(self, tmp_path):
        """A discovered hook file in no category list names the hook and aborts (Req 10.5)."""
        paths = _hooks_world(
            tmp_path,
            categories_yaml="critical: []\nmodules: {}\n",
            hook_ids=("some-hook",),
        )
        with pytest.raises(GeneratorError) as exc:
            load_sources(paths)
        message = str(exc.value)
        assert "some-hook" in message
        assert not paths.power_md.exists()

    def test_consistent_categories_and_files_load_without_error(self, tmp_path):
        """When every file is categorized and every category has a file, loading succeeds."""
        paths = _hooks_world(
            tmp_path,
            categories_yaml=(
                "critical:\n  - guard-hook\n"
                "modules:\n  2:\n    - helper-hook\n  any:\n    - helper-hook\n"
            ),
            hook_ids=("guard-hook", "helper-hook"),
        )
        sources = load_sources(paths)
        ids = {hook.hook_id for hook in sources.hooks}
        assert ids == {"guard-hook", "helper-hook"}
        # The critical-listed hook is flagged critical; the other is not.
        critical = {hook.hook_id for hook in sources.hooks if hook.is_critical}
        assert critical == {"guard-hook"}


# ---------------------------------------------------------------------------
# 6.2 SteeringRegion error paths (Req 5.4, 11.5)
# ---------------------------------------------------------------------------


def _steering_sources(steering: tuple[SteeringFileInfo, ...]) -> Sources:
    """Build a minimal Sources for steering-region rendering.

    Only ``steering`` and ``steering_budget_total`` matter to
    :class:`SteeringRegion`; the remaining fields are filled with empty/zero
    values.

    Args:
        steering: The per-file steering records to render.

    Returns:
        A :class:`Sources` carrying the given steering records and a fixed
        budget total.
    """
    return Sources(
        tools=(),
        total_count=0,
        hooks=(),
        steering=steering,
        steering_budget_total=12345,
        modules=(),
    )


class TestSteeringRegion:
    """SteeringRegion validates each entry before rendering its table row."""

    def test_missing_token_count_names_file_and_field_and_aborts(self, tmp_path):
        """An entry with no token_count names the file and field (Req 11.5)."""
        (tmp_path / "x.md").write_text("steering body\n", encoding="utf-8")
        sources = _steering_sources(
            (SteeringFileInfo(filename="x.md", token_count=None, size_category="medium"),)
        )
        with pytest.raises(GeneratorError) as exc:
            SteeringRegion(steering_dir=tmp_path).render(sources)
        message = str(exc.value)
        assert "x.md" in message
        assert "token_count" in message

    def test_missing_size_category_names_file_and_field_and_aborts(self, tmp_path):
        """An entry with no size_category names the file and field (Req 11.5)."""
        (tmp_path / "x.md").write_text("steering body\n", encoding="utf-8")
        sources = _steering_sources(
            (SteeringFileInfo(filename="x.md", token_count=100, size_category=None),)
        )
        with pytest.raises(GeneratorError) as exc:
            SteeringRegion(steering_dir=tmp_path).render(sources)
        message = str(exc.value)
        assert "x.md" in message
        assert "size_category" in message

    def test_missing_referenced_file_names_path_and_aborts(self, tmp_path):
        """A listed steering file with no file on disk names the path (Req 5.4)."""
        # Intentionally do NOT create tmp_path/missing.md.
        sources = _steering_sources(
            (
                SteeringFileInfo(
                    filename="missing.md", token_count=100, size_category="medium"
                ),
            )
        )
        with pytest.raises(GeneratorError) as exc:
            SteeringRegion(steering_dir=tmp_path).render(sources)
        assert "missing.md" in str(exc.value)

    def test_happy_path_renders_table_row_and_budget_footer(self, tmp_path):
        """A valid existing file renders a table row and the budget footer."""
        (tmp_path / "intro.md").write_text("steering body\n", encoding="utf-8")
        sources = _steering_sources(
            (
                SteeringFileInfo(
                    filename="intro.md", token_count=100, size_category="medium"
                ),
            )
        )
        body = SteeringRegion(steering_dir=tmp_path).render(sources)
        assert "| `intro.md` | 100 | medium |" in body
        assert "**Total budget:** 12345 tokens" in body
        assert body.endswith("\n")


# ---------------------------------------------------------------------------
# 7.2 ModulesRegion error paths and ordering (Req 12.3, 12.5)
# ---------------------------------------------------------------------------


def _modules_sources(modules: tuple[ModuleInfo, ...]) -> Sources:
    """Build a minimal Sources for modules-region rendering.

    Only ``modules`` matters to :class:`ModulesRegion`; the remaining fields are
    filled with empty/zero values.

    Args:
        modules: The per-module records to render.

    Returns:
        A :class:`Sources` carrying the given module records.
    """
    return Sources(
        tools=(),
        total_count=0,
        hooks=(),
        steering=(),
        steering_budget_total=0,
        modules=modules,
    )


class TestModulesRegion:
    """ModulesRegion validates each module and emits rows in ascending order."""

    def test_missing_name_names_module_number_and_field_and_aborts(self):
        """A module with no name names its number and the 'name' field (Req 12.5)."""
        sources = _modules_sources((ModuleInfo(number=3, name=None),))
        with pytest.raises(GeneratorError) as exc:
            ModulesRegion().render(sources)
        message = str(exc.value)
        assert "3" in message
        assert "name" in message

    def test_missing_number_names_module_and_field_and_aborts(self):
        """A module with no number names the 'number' field and the module (Req 12.5)."""
        sources = _modules_sources((ModuleInfo(number=None, name="Foo"),))
        with pytest.raises(GeneratorError) as exc:
            ModulesRegion().render(sources)
        message = str(exc.value)
        assert "number" in message
        assert "Foo" in message

    def test_rows_emitted_in_ascending_numeric_order(self):
        """Rows appear in ascending numeric order, not lexical (Req 12.3)."""
        sources = _modules_sources(
            (
                ModuleInfo(number=2, name="B"),
                ModuleInfo(number=1, name="A"),
                ModuleInfo(number=11, name="K"),
                ModuleInfo(number=3, name="C"),
            )
        )
        body = ModulesRegion().render(sources)
        # Extract the leading numbers from data rows (skip the header separator).
        row_numbers = [
            int(line.split("|")[1].strip())
            for line in body.splitlines()
            if line.startswith("| ") and line.split("|")[1].strip().isdigit()
        ]
        assert row_numbers == [1, 2, 3, 11]
        # The count line reflects the number of modules.
        assert "Total: 4 modules." in body


# ---------------------------------------------------------------------------
# 9.3 assemble prose/marker preservation (Req 2.2, 2.3)
# ---------------------------------------------------------------------------


class TestAssemble:
    """assemble replaces only region bodies, leaving markers and prose intact."""

    def test_replaces_bodies_and_preserves_markers_and_prose(self):
        """Only the region bodies change; markers and surrounding prose are intact."""
        doc = _doc(
            "intro prose line",
            "<!-- BEGIN GENERATED: mcp-tools -->",
            "old tools body",
            "<!-- END GENERATED: mcp-tools -->",
            "prose between regions",
            "<!-- BEGIN GENERATED: modules -->",
            "old modules body",
            "<!-- END GENERATED: modules -->",
            "outro prose line",
        )
        spans = locate_regions(doc, {"mcp-tools", "modules"})
        bodies = {
            "mcp-tools": "new tools body\nsecond tools line\n",
            "modules": "new modules body\n",
        }
        result = assemble(doc, spans, bodies)

        expected = _doc(
            "intro prose line",
            "<!-- BEGIN GENERATED: mcp-tools -->",
            "new tools body",
            "second tools line",
            "<!-- END GENERATED: mcp-tools -->",
            "prose between regions",
            "<!-- BEGIN GENERATED: modules -->",
            "new modules body",
            "<!-- END GENERATED: modules -->",
            "outro prose line",
        )
        assert result == expected
        # Markers and prose survive byte-for-byte.
        assert "<!-- BEGIN GENERATED: mcp-tools -->" in result
        assert "<!-- END GENERATED: mcp-tools -->" in result
        assert "<!-- BEGIN GENERATED: modules -->" in result
        assert "<!-- END GENERATED: modules -->" in result
        assert "intro prose line" in result
        assert "prose between regions" in result
        assert "outro prose line" in result
        # Old bodies are gone, new bodies are present.
        assert "old tools body" not in result
        assert "old modules body" not in result
        assert "new tools body" in result
        assert "second tools line" in result
        assert "new modules body" in result

    def test_subset_leaves_other_region_body_unchanged(self):
        """A bodies dict with one region leaves the other region's body intact."""
        doc = _doc(
            "<!-- BEGIN GENERATED: mcp-tools -->",
            "old tools body",
            "<!-- END GENERATED: mcp-tools -->",
            "<!-- BEGIN GENERATED: modules -->",
            "untouched modules body",
            "<!-- END GENERATED: modules -->",
        )
        spans = locate_regions(doc, {"mcp-tools", "modules"})
        result = assemble(doc, spans, {"mcp-tools": "fresh tools body\n"})

        expected = _doc(
            "<!-- BEGIN GENERATED: mcp-tools -->",
            "fresh tools body",
            "<!-- END GENERATED: mcp-tools -->",
            "<!-- BEGIN GENERATED: modules -->",
            "untouched modules body",
            "<!-- END GENERATED: modules -->",
        )
        assert result == expected
        assert "untouched modules body" in result
        assert "old tools body" not in result

    def test_empty_bodies_returns_doc_unchanged(self):
        """An empty bodies dict returns the document byte-for-byte unchanged."""
        doc = _doc(
            "intro",
            "<!-- BEGIN GENERATED: hooks -->",
            "hooks body",
            "<!-- END GENERATED: hooks -->",
            "outro",
        )
        spans = locate_regions(doc, {"hooks"})
        assert assemble(doc, spans, {}) == doc


# ---------------------------------------------------------------------------
# 9.3 verify drift/missing reporting (Req 3.1, 3.7)
# ---------------------------------------------------------------------------


class TestVerify:
    """verify reports exactly the drifted/missing region ids with a matching count."""

    def test_no_drift_reports_ok(self):
        """Bodies equal to the committed spans yield ok with zero drift."""
        doc = _doc(
            "<!-- BEGIN GENERATED: mcp-tools -->",
            "tools body",
            "<!-- END GENERATED: mcp-tools -->",
            "<!-- BEGIN GENERATED: modules -->",
            "modules body",
            "<!-- END GENERATED: modules -->",
        )
        spans = locate_regions(doc, {"mcp-tools", "modules"})
        bodies = {region_id: span.body for region_id, span in spans.items()}
        result = verify(doc, spans, bodies)
        assert result.ok is True
        assert result.drift_count == 0
        assert result.drifted_region_ids == ()
        assert result.missing_region_ids == ()

    def test_subset_drift_reports_exactly_that_region(self):
        """A single mutated body is reported as the only drifted region."""
        doc = _doc(
            "<!-- BEGIN GENERATED: mcp-tools -->",
            "tools body",
            "<!-- END GENERATED: mcp-tools -->",
            "<!-- BEGIN GENERATED: modules -->",
            "modules body",
            "<!-- END GENERATED: modules -->",
        )
        spans = locate_regions(doc, {"mcp-tools", "modules"})
        bodies = {region_id: span.body for region_id, span in spans.items()}
        bodies["modules"] = bodies["modules"] + "drifted extra line\n"
        result = verify(doc, spans, bodies)
        assert result.ok is False
        assert result.drifted_region_ids == ("modules",)
        assert result.missing_region_ids == ()
        assert result.drift_count == 1

    def test_missing_region_reported_in_missing_ids(self):
        """A body id absent from spans is reported as missing (Req 3.7)."""
        doc = _doc(
            "<!-- BEGIN GENERATED: mcp-tools -->",
            "tools body",
            "<!-- END GENERATED: mcp-tools -->",
        )
        spans = locate_regions(doc, {"mcp-tools"})
        bodies = {
            "mcp-tools": spans["mcp-tools"].body,
            "steering": "steering body the doc never committed\n",
        }
        result = verify(doc, spans, bodies)
        assert result.ok is False
        assert result.missing_region_ids == ("steering",)
        assert result.drifted_region_ids == ()
        assert result.drift_count == 1

    def test_combined_drift_and_missing_reported_together(self):
        """Drift and missing are both reported and counted together."""
        doc = _doc(
            "<!-- BEGIN GENERATED: mcp-tools -->",
            "tools body",
            "<!-- END GENERATED: mcp-tools -->",
            "<!-- BEGIN GENERATED: modules -->",
            "modules body",
            "<!-- END GENERATED: modules -->",
        )
        spans = locate_regions(doc, {"mcp-tools", "modules"})
        bodies = {
            "mcp-tools": spans["mcp-tools"].body + "drifted\n",
            "modules": spans["modules"].body,
            "steering": "never committed\n",
        }
        result = verify(doc, spans, bodies)
        assert result.ok is False
        assert result.drifted_region_ids == ("mcp-tools",)
        assert result.missing_region_ids == ("steering",)
        assert result.drift_count == 2


# ---------------------------------------------------------------------------
# 10.3 CLI behavior and drift/verify messaging
# (Req 3.5, 3.6, 6.5, 6.6, 6.7, 8.3, 8.4, 8.6)
# ---------------------------------------------------------------------------


def _power_md_skeleton() -> str:
    """Return a lint-clean POWER.md skeleton carrying the four marker pairs.

    Each Generated_Region (``mcp-tools``, ``hooks``, ``steering-files``,
    ``modules``) is delimited by an empty begin/end marker pair; Write_Mode
    fills the bodies. Headings are surrounded by blank lines and the document
    ends with a single trailing newline so the skeleton is itself CommonMark
    clean.

    Returns:
        The POWER.md skeleton text.
    """
    return (
        "# Senzing Bootcamp Power\n"
        "\n"
        "Hand-written intro prose that the generator must preserve.\n"
        "\n"
        "## Available MCP Tools\n"
        "\n"
        "<!-- BEGIN GENERATED: mcp-tools -->\n"
        "<!-- END GENERATED: mcp-tools -->\n"
        "\n"
        "## Hooks\n"
        "\n"
        "<!-- BEGIN GENERATED: hooks -->\n"
        "<!-- END GENERATED: hooks -->\n"
        "\n"
        "## Steering Files\n"
        "\n"
        "<!-- BEGIN GENERATED: steering-files -->\n"
        "<!-- END GENERATED: steering-files -->\n"
        "\n"
        "## Modules\n"
        "\n"
        "<!-- BEGIN GENERATED: modules -->\n"
        "<!-- END GENERATED: modules -->\n"
    )


def _full_world(tmp_path: Path) -> SourcePaths:
    """Build a complete, internally consistent world so ``main([])`` succeeds.

    Creates a hooks directory with two ``*.kiro.hook`` files and a
    ``hook-categories.yaml`` that names exactly those two ids (one critical, one
    under ``modules: any:``), a ``steering-index.yaml`` with two ``file_metadata``
    entries (plus the matching ``.md`` files so the existence check passes) and a
    budget total, a ``module-dependencies.yaml`` with two modules, and a POWER.md
    skeleton with the four marker pairs. Every source is mutually consistent so a
    Write_Mode run can complete end to end.

    The ``mcp-tools`` region is sourced from the real ``mcp_tool_inventory``
    module (there is no override for it), so Write_Mode fills that region with
    the real tool bullets regardless of this throwaway world.

    Args:
        tmp_path: The pytest temporary directory for this test.

    Returns:
        A :class:`SourcePaths` pointing entirely inside ``tmp_path``, with a
        POWER.md skeleton already written.
    """
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    hook_categories = hooks_dir / "hook-categories.yaml"
    hook_categories.write_text(
        "critical:\n  - alpha-hook\nmodules:\n  any:\n    - beta-hook\n",
        encoding="utf-8",
    )
    for hook_id in ("alpha-hook", "beta-hook"):
        (hooks_dir / f"{hook_id}.kiro.hook").write_text("{}\n", encoding="utf-8")

    steering_dir = tmp_path / "steering"
    steering_dir.mkdir()
    steering_index = steering_dir / "steering-index.yaml"
    steering_index.write_text(
        "file_metadata:\n"
        "  guide.md:\n"
        "    token_count: 250\n"
        "    size_category: medium\n"
        "  intro.md:\n"
        "    token_count: 100\n"
        "    size_category: small\n"
        "budget:\n"
        "  total_tokens: 350\n",
        encoding="utf-8",
    )
    (steering_dir / "intro.md").write_text("# Intro\n", encoding="utf-8")
    (steering_dir / "guide.md").write_text("# Guide\n", encoding="utf-8")

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    module_deps = config_dir / "module-dependencies.yaml"
    module_deps.write_text(
        "modules:\n"
        "  1:\n"
        "    name: First Module\n"
        "  2:\n"
        "    name: Second Module\n",
        encoding="utf-8",
    )

    power_md = tmp_path / "POWER.md"
    power_md.write_text(_power_md_skeleton(), encoding="utf-8")

    return SourcePaths(
        power_md=power_md,
        hooks_dir=hooks_dir,
        hook_categories=hook_categories,
        steering_index=steering_index,
        module_deps=module_deps,
        repo_root=tmp_path,
    )


def _argv(paths: SourcePaths) -> list[str]:
    """Build the path-override argv pointing main at a throwaway world.

    Args:
        paths: The :class:`SourcePaths` for the throwaway world.

    Returns:
        The argv list of ``--power-md``/source-path overrides (no mode flag).
    """
    return [
        "--power-md", str(paths.power_md),
        "--hooks-dir", str(paths.hooks_dir),
        "--hook-categories", str(paths.hook_categories),
        "--steering-index", str(paths.steering_index),
        "--module-deps", str(paths.module_deps),
        "--repo-root", str(paths.repo_root),
    ]


class TestMainCli:
    """main() dispatches modes, defaults to write, and rejects bad arguments."""

    def test_default_mode_is_write_and_returns_zero(self, tmp_path, monkeypatch):
        """main([overrides]) with no mode flag writes and returns 0 (Req 8.3, 6.6)."""
        # CommonMark validation is covered by its own tests/property 11; stub it
        # to a no-op so a hand-built skeleton cannot make this test brittle.
        monkeypatch.setattr(generate_power_docs, "validate_commonmark_text", lambda content: None)
        paths = _full_world(tmp_path)

        rc = main(_argv(paths))

        assert rc == 0
        written = paths.power_md.read_text(encoding="utf-8")
        # The mcp-tools region is filled from the real 13-tool inventory.
        tool_bullets = [
            line for line in written.splitlines() if line.startswith("- `")
        ]
        assert len(tool_bullets) == 13
        assert "- `get_capabilities`" in written
        # The hooks region states the count and lists both discovered hooks,
        # with the critical hook marked.
        assert "Available (2 hooks):" in written
        assert "`alpha-hook`" in written
        assert "`beta-hook`" in written
        # Hand-written prose outside the regions is preserved.
        assert "Hand-written intro prose that the generator must preserve." in written

    def test_write_then_verify_is_clean(self, tmp_path, monkeypatch):
        """A freshly written world verifies clean and returns 0 (Req 8.4, 6.6)."""
        monkeypatch.setattr(generate_power_docs, "validate_commonmark_text", lambda content: None)
        paths = _full_world(tmp_path)
        argv = _argv(paths)

        assert main(argv) == 0
        assert main(argv + ["--verify"]) == 0

    def test_bogus_argument_returns_nonzero_with_stderr(self, capsys):
        """An unrecognized argument exits non-zero with a stderr message (Req 6.7, 8.6)."""
        rc = main(["--bogus"])
        captured = capsys.readouterr()
        assert rc == 2
        assert captured.err != ""

    def test_write_and_verify_are_mutually_exclusive(self, tmp_path, capsys):
        """--write and --verify together are rejected non-zero (Req 8.3, 8.4, 6.7)."""
        paths = _full_world(tmp_path)
        rc = main(_argv(paths) + ["--write", "--verify"])
        captured = capsys.readouterr()
        assert rc == 2
        assert captured.err != ""


class TestVerifyMessaging:
    """Verify_Mode messaging on drift and on a missing POWER.md (Req 3.5, 3.6)."""

    def test_drift_prints_exact_regen_command_and_region(self, tmp_path, monkeypatch, capsys):
        """Forced drift returns 1 and prints the exact --write command (Req 3.5)."""
        monkeypatch.setattr(generate_power_docs, "validate_commonmark_text", lambda content: None)
        paths = _full_world(tmp_path)
        argv = _argv(paths)

        # Write a clean world, then mutate one region body to force drift.
        assert main(argv) == 0
        clean = paths.power_md.read_text(encoding="utf-8")
        mutated = clean.replace(
            "<!-- BEGIN GENERATED: modules -->\n",
            "<!-- BEGIN GENERATED: modules -->\nDRIFTED LINE\n",
        )
        assert mutated != clean
        paths.power_md.write_text(mutated, encoding="utf-8")

        rc = main(argv + ["--verify"])
        captured = capsys.readouterr()

        assert rc == 1
        # The exact runnable regeneration command appears verbatim.
        assert REGEN_COMMAND == "python3 senzing-bootcamp/scripts/generate_power_docs.py --write"
        assert REGEN_COMMAND in captured.out
        # The drifted region id and a drift count are reported.
        assert "modules" in captured.out
        assert "1 region" in captured.out

    def test_verify_missing_power_md_returns_nonzero_and_touches_nothing(self, tmp_path, capsys):
        """Verify on a missing POWER.md fails and creates nothing (Req 3.6)."""
        paths = _full_world(tmp_path)
        missing = tmp_path / "NOPE.md"
        assert not missing.exists()
        argv = [
            "--power-md", str(missing),
            "--hooks-dir", str(paths.hooks_dir),
            "--hook-categories", str(paths.hook_categories),
            "--steering-index", str(paths.steering_index),
            "--module-deps", str(paths.module_deps),
            "--repo-root", str(paths.repo_root),
        ]

        rc = main(argv + ["--verify"])
        captured = capsys.readouterr()

        assert rc != 0
        # The error names the missing/unreadable POWER.md path.
        assert "NOPE.md" in captured.err
        # Verify_Mode never created the file.
        assert not missing.exists()


# ---------------------------------------------------------------------------
# 13.1 Smoke / structure tests (Req 6.1, 6.2, 8.5)
# ---------------------------------------------------------------------------


import ast


class TestSmokeStructure:
    """Structural facts about the generator script and its documentation."""

    def test_generator_script_exists(self):
        """The generator script exists at the expected scripts path (Req 6.1)."""
        script = Path(_SCRIPTS_DIR) / "generate_power_docs.py"
        assert script.is_file()

    def test_only_stdlib_top_level_imports_and_yaml_imported_lazily(self):
        """Top-level imports are stdlib only and ``yaml`` is imported lazily (Req 6.2).

        The design requires the generator to import only Python standard-library
        modules at module top level and to import ``yaml`` exclusively inside
        functions. This walks the module-level AST nodes, collects the root
        module name of every top-level ``import``/``from ... import``, and
        asserts each is a stdlib module and that ``yaml`` is not among them.
        """
        script = Path(_SCRIPTS_DIR) / "generate_power_docs.py"
        source = script.read_text(encoding="utf-8")
        tree = ast.parse(source)

        top_level_names: set[str] = set()
        for node in tree.body:  # direct children of Module == top-level only
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_level_names.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                # Skip relative imports (module is None for ``from . import x``).
                if node.level == 0 and node.module:
                    top_level_names.add(node.module.split(".")[0])

        # ``yaml`` (the sole permitted third-party dependency) must be imported
        # only inside functions, never at module top level.
        assert "yaml" not in top_level_names

        # Every top-level import must be a Python standard-library module.
        stdlib = sys.stdlib_module_names  # available in Python 3.11+
        non_stdlib = sorted(name for name in top_level_names if name not in stdlib)
        assert non_stdlib == [], f"unexpected non-stdlib top-level imports: {non_stdlib}"

    def test_readme_documents_regenerate_and_verify_invocations(self):
        """The scripts README documents both --write and --verify invocations (Req 8.5)."""
        readme = Path(_SCRIPTS_DIR) / "README.md"
        assert readme.is_file()
        text = readme.read_text(encoding="utf-8")
        # The README must reference the generator and document both modes.
        assert "generate_power_docs.py" in text
        assert "generate_power_docs.py --write" in text
        assert "generate_power_docs.py --verify" in text
