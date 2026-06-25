"""Property-based tests for sync_hook_registry.py using Hypothesis.

Feature: hook-registry-source-of-truth
"""

import json
import sys
import tempfile
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from sync_hook_registry import (
    CategoryMapping,
    HookEntry,
    categorize_hooks,
    format_hook_entry,
    generate_registry_summary,
    parse_hook_file,
    verify_registry,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Valid hook IDs: lowercase letters and hyphens, 3-20 chars
def st_hook_id():
    """Generate valid hook-style IDs (lowercase + hyphens)."""
    return st.from_regex(r"[a-z][a-z0-9\-]{2,15}", fullmatch=True)


# Event types from the real hook files
EVENT_TYPES = [
    "promptSubmit", "agentStop", "fileEdited", "fileCreated",
    "preToolUse", "postTaskExecution", "userTriggered",
]

ACTION_TYPES = ["askAgent", "runCommand"]


def st_event_type():
    return st.sampled_from(EVENT_TYPES)


def st_action_type():
    return st.sampled_from(ACTION_TYPES)


def st_safe_text():
    """Generate safe text strings (no null bytes, reasonable length)."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N", "P", "Z"),
            blacklist_characters="\x00",
        ),
        min_size=1,
        max_size=80,
    )


def st_hook_entry():
    """Generate a random HookEntry."""
    return st.builds(
        HookEntry,
        hook_id=st_hook_id(),
        name=st_safe_text(),
        description=st_safe_text(),
        event_type=st_event_type(),
        action_type=st_action_type(),
        prompt=st.one_of(st.none(), st_safe_text()),
        file_patterns=st.one_of(st.none(), st.just("*.py"), st.just("src/*.ts, src/*.js")),
        tool_types=st.one_of(st.none(), st.just("write"), st.just("read, write")),
    )


def st_unique_hook_entries(min_size=1, max_size=10):
    """Generate a list of HookEntry objects with unique hook_ids."""
    return st.lists(
        st_hook_entry(),
        min_size=min_size,
        max_size=max_size,
        unique_by=lambda e: e.hook_id,
    )


MODULE_NUMBERS = [1, 2, 3, 5, 6, 8, 11, 12]


@st.composite
def st_category_mapping(draw, hooks):
    """Build a category mapping dict for a given list of hooks.

    Each hook is randomly assigned: critical, module (with number), or unmapped.
    """
    mapping = {}
    for hook in hooks:
        choice = draw(st.sampled_from(["critical", "module", "unmapped"]))
        if choice == "critical":
            mapping[hook.hook_id] = CategoryMapping(
                hook_id=hook.hook_id, category="critical"
            )
        elif choice == "module":
            mod_num = draw(st.sampled_from(MODULE_NUMBERS))
            mapping[hook.hook_id] = CategoryMapping(
                hook_id=hook.hook_id, category="module", module_number=mod_num
            )
        # else: unmapped → will default to "any module"
    return mapping


# ---------------------------------------------------------------------------
# Property 1: Hook Field Extraction Completeness
# Validates: Requirements 1.2, 1.3, 1.4, 1.5
# ---------------------------------------------------------------------------


@given(
    hook_id=st_hook_id(),
    name=st_safe_text(),
    description=st_safe_text(),
    event_type=st_event_type(),
    action_type=st_action_type(),
    prompt=st.one_of(st.none(), st_safe_text()),
    file_patterns=st.one_of(st.none(), st.just(["*.py"]), st.just(["src/*.ts", "src/*.js"])),
    tool_types=st.one_of(st.none(), st.just(["write"]), st.just(["read", "write"])),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property_1_hook_field_extraction_completeness(
    hook_id, name, description, event_type, action_type, prompt, file_patterns, tool_types,
):
    """Feature: hook-registry-source-of-truth, Property 1: Hook Field Extraction Completeness

    For any valid hook JSON dict with required and optional fields, the parser
    extracts all present fields correctly and hook_id equals the filename stem.

    **Validates: Requirements 1.2, 1.3, 1.4, 1.5**
    """
    # Build the JSON structure
    hook_data = {
        "name": name,
        "description": description,
        "when": {"type": event_type},
        "then": {"type": action_type},
    }
    if prompt is not None:
        hook_data["then"]["prompt"] = prompt
    if file_patterns is not None:
        hook_data["when"]["patterns"] = file_patterns
    if tool_types is not None:
        hook_data["when"]["toolTypes"] = tool_types

    # Write to a temp file
    with tempfile.TemporaryDirectory() as tmp_dir:
        hook_file = Path(tmp_dir) / f"{hook_id}.kiro.hook"
        hook_file.write_text(json.dumps(hook_data), encoding="utf-8")

        # Parse
        entry = parse_hook_file(hook_file)

    # Verify all fields
    assert entry.hook_id == hook_id
    assert entry.name == name
    assert entry.description == description
    assert entry.event_type == event_type
    assert entry.action_type == action_type

    if prompt is not None:
        assert entry.prompt == prompt
    else:
        assert entry.prompt is None

    if file_patterns is not None:
        assert entry.file_patterns == ", ".join(file_patterns)
    else:
        assert entry.file_patterns is None

    if tool_types is not None:
        assert entry.tool_types == ", ".join(tool_types)
    else:
        assert entry.tool_types is None


# ---------------------------------------------------------------------------
# Property 2: Category Placement Correctness
# Validates: Requirements 2.2, 2.3, 2.4
# ---------------------------------------------------------------------------


@given(data=st.data())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property_2_category_placement_correctness(data):
    """Feature: hook-registry-source-of-truth, Property 2: Category Placement Correctness

    For any set of hooks and category mapping, Critical hooks appear in Critical
    section, Module hooks appear under correct module, unmapped hooks appear
    under "any module".

    **Validates: Requirements 2.2, 2.3, 2.4**
    """
    hooks = data.draw(st_unique_hook_entries(min_size=1, max_size=8))
    mapping = data.draw(st_category_mapping(hooks))

    critical, modules = categorize_hooks(hooks, mapping)

    # Check critical hooks
    critical_ids = {h.hook_id for h in critical}
    for hook in hooks:
        cat = mapping.get(hook.hook_id)
        if cat is not None and cat.category == "critical":
            assert hook.hook_id in critical_ids, (
                f"{hook.hook_id} should be in critical section"
            )

    # Check module hooks
    for hook in hooks:
        cat = mapping.get(hook.hook_id)
        if cat is not None and cat.category == "module" and cat.module_number is not None:
            assert cat.module_number in modules, (
                f"Module {cat.module_number} should exist"
            )
            mod_ids = {h.hook_id for h in modules[cat.module_number]}
            assert hook.hook_id in mod_ids, (
                f"{hook.hook_id} should be in module {cat.module_number}"
            )

    # Check unmapped hooks → "any module"
    for hook in hooks:
        cat = mapping.get(hook.hook_id)
        if cat is None:
            assert "any" in modules, "Unmapped hooks should go to 'any' module"
            any_ids = {h.hook_id for h in modules["any"]}
            assert hook.hook_id in any_ids, (
                f"{hook.hook_id} should be in 'any module' section"
            )


# ---------------------------------------------------------------------------
# Property 3: Alphabetical Sort Within Sections
# Validates: Requirements 3.3, 3.4
# ---------------------------------------------------------------------------


@given(data=st.data())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property_3_alphabetical_sort_within_sections(data):
    """Feature: hook-registry-source-of-truth, Property 3: Alphabetical Sort Within Sections

    For any set of hooks within a section, entries are sorted alphabetically
    by hook_id.

    **Validates: Requirements 3.3, 3.4**
    """
    hooks = data.draw(st_unique_hook_entries(min_size=2, max_size=10))
    mapping = data.draw(st_category_mapping(hooks))

    critical, modules = categorize_hooks(hooks, mapping)

    # Critical hooks should be sorted alphabetically
    critical_ids = [h.hook_id for h in critical]
    assert critical_ids == sorted(critical_ids), (
        f"Critical hooks not sorted: {critical_ids}"
    )

    # Each module bucket should be sorted alphabetically
    for key, mod_hooks in modules.items():
        mod_ids = [h.hook_id for h in mod_hooks]
        assert mod_ids == sorted(mod_ids), (
            f"Module {key} hooks not sorted: {mod_ids}"
        )


# ---------------------------------------------------------------------------
# Property 4: Registry Frontmatter and Structure
# Validates: Requirements 3.1, 3.2
# ---------------------------------------------------------------------------


@given(data=st.data())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property_4_registry_frontmatter_and_structure(data):
    """Feature: hook-registry-source-of-truth, Property 4: Registry Frontmatter and Structure

    For any generated registry output, content starts with frontmatter and
    contains required headings.

    **Validates: Requirements 3.1, 3.2**
    """
    hooks = data.draw(st_unique_hook_entries(min_size=1, max_size=8))
    mapping = data.draw(st_category_mapping(hooks))

    critical, modules = categorize_hooks(hooks, mapping)
    total_count = len(hooks)

    content = generate_registry_summary(critical, modules, total_count)

    # Must start with frontmatter
    assert content.startswith("---\ninclusion: manual\n---\n"), (
        "Registry must start with YAML frontmatter"
    )

    # Must contain title
    assert "# Hook Registry" in content

    # Must contain both section headings
    assert "## Critical Hooks" in content
    assert "## Module Hooks" in content


# ---------------------------------------------------------------------------
# Property 5: Hook Entry Format Correctness
# Validates: Requirements 3.5, 3.6
# ---------------------------------------------------------------------------


@given(entry=st_hook_entry())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property_5_hook_entry_format_correctness(entry):
    """Feature: hook-registry-source-of-truth, Property 5: Hook Entry Format Correctness

    For any HookEntry, formatted markdown contains bold hook_id, event flow,
    and bullet list with id/name/description; filePatterns and toolTypes appear
    when present.

    **Validates: Requirements 3.5, 3.6**
    """
    md = format_hook_entry(entry)

    # Bold hook_id
    assert f"**{entry.hook_id}**" in md

    # Event flow
    assert f"{entry.event_type} → {entry.action_type}" in md

    # Bullet list
    assert f"- id: `{entry.hook_id}`" in md
    assert f"- name: `{entry.name}`" in md
    assert f"- description: `{entry.description}`" in md

    # filePatterns when present
    if entry.file_patterns:
        assert f"filePatterns: `{entry.file_patterns}`" in md
    else:
        assert "filePatterns:" not in md

    # toolTypes when present
    if entry.tool_types:
        assert f"toolTypes: {entry.tool_types}" in md
    else:
        assert "toolTypes:" not in md


# ---------------------------------------------------------------------------
# Property 6: Deterministic Generation (Idempotence)
# Validates: Requirements 6.1
# ---------------------------------------------------------------------------


@given(data=st.data())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property_6_deterministic_generation(data):
    """Feature: hook-registry-source-of-truth, Property 6: Deterministic Generation

    For any set of hook data and category mapping, generating twice produces
    byte-identical output.

    **Validates: Requirements 6.1**
    """
    hooks = data.draw(st_unique_hook_entries(min_size=1, max_size=8))
    mapping = data.draw(st_category_mapping(hooks))

    critical1, modules1 = categorize_hooks(hooks, mapping)
    content1 = generate_registry_summary(critical1, modules1, len(hooks))

    critical2, modules2 = categorize_hooks(hooks, mapping)
    content2 = generate_registry_summary(critical2, modules2, len(hooks))

    assert content1 == content2, "Two generations from same input must be byte-identical"


# ---------------------------------------------------------------------------
# Property 7: Stable Sort Order Independence
# Validates: Requirements 6.2
# ---------------------------------------------------------------------------


@given(data=st.data())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property_7_stable_sort_order_independence(data):
    """Feature: hook-registry-source-of-truth, Property 7: Stable Sort Order Independence

    For any set of hooks in any input order, the generated output is identical.

    **Validates: Requirements 6.2**
    """
    hooks = data.draw(st_unique_hook_entries(min_size=2, max_size=8))
    mapping = data.draw(st_category_mapping(hooks))

    # Generate from original order
    critical1, modules1 = categorize_hooks(hooks, mapping)
    content1 = generate_registry_summary(critical1, modules1, len(hooks))

    # Reverse the input order
    reversed_hooks = list(reversed(hooks))
    critical2, modules2 = categorize_hooks(reversed_hooks, mapping)
    content2 = generate_registry_summary(critical2, modules2, len(reversed_hooks))

    assert content1 == content2, (
        "Output must be identical regardless of input order"
    )


# ---------------------------------------------------------------------------
# Property 8: Verify Mode Correctness
# Validates: Requirements 4.2, 4.3, 4.4, 4.5
# ---------------------------------------------------------------------------


@given(
    content=st_safe_text(),
    existing=st.one_of(st.none(), st_safe_text()),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property_8_verify_mode_correctness(content, existing):
    """Feature: hook-registry-source-of-truth, Property 8: Verify Mode Correctness

    For any generated content and existing content, verify returns True iff
    byte-identical, False when differing or file missing.

    **Validates: Requirements 4.2, 4.3, 4.4, 4.5**
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = Path(tmp_dir) / "registry.md"

        if existing is None:
            # File does not exist
            matches, msg = verify_registry(content, file_path)
            assert not matches, "Verify should return False when file is missing"
            assert "missing" in msg.lower()
        else:
            file_path.write_text(existing, encoding="utf-8")
            matches, msg = verify_registry(content, file_path)
            if content == existing:
                assert matches, "Verify should return True when content matches"
            else:
                assert not matches, "Verify should return False when content differs"


# ---------------------------------------------------------------------------
# Property 9: Unix Line Ending Normalization
# Validates: Requirements 6.3
# ---------------------------------------------------------------------------


@given(data=st.data())
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property_9_unix_line_ending_normalization(data):
    """Feature: hook-registry-source-of-truth, Property 9: Unix Line Ending Normalization

    For any generated output, content contains only \\n line endings and no
    \\r characters.

    **Validates: Requirements 6.3**
    """
    hooks = data.draw(st_unique_hook_entries(min_size=1, max_size=8))
    mapping = data.draw(st_category_mapping(hooks))

    critical, modules = categorize_hooks(hooks, mapping)
    content = generate_registry_summary(critical, modules, len(hooks))

    assert "\r" not in content, "Generated output must not contain \\r characters"
    # All line endings should be \n only
    for i, char in enumerate(content):
        if char == "\n":
            # Check there's no \r before it
            if i > 0:
                assert content[i - 1] != "\r", (
                    f"Found \\r\\n at position {i-1}"
                )


# ---------------------------------------------------------------------------
# Feature: steering-budget-headroom
# Property 5: Slice frontmatter and content integrity
# Validates: Requirements 8.2, 3.1, 8.4
# ---------------------------------------------------------------------------

from sync_hook_registry import generate_module_slice


# Module bucket keys: numbered modules plus the unmapped "any" group.
def st_module_bucket_key():
    """Generate a module bucket key — a numbered module or the 'any' group."""
    return st.one_of(st.sampled_from(MODULE_NUMBERS), st.just("any"))


def _expected_module_label(key):
    """Return the human-readable module label for a bucket *key*.

    Mirrors the generator's labelling: ``"Module N"`` for a numbered module and
    ``"any module"`` for the unmapped group.
    """
    return f"Module {key}" if isinstance(key, int) else "any module"


class TestSliceFrontmatterAndContentIntegrity:
    """Property 5: Slice frontmatter and content integrity.

    Validates that ``generate_module_slice`` renders a well-formed slice for any
    non-empty module bucket: ``inclusion: manual`` frontmatter, the module label
    heading, and — for every member hook — its bold ID, event flow, full prompt
    text (when present), and id/name/description bullets, with only ``\\n`` line
    endings.

    **Validates: Requirements 8.2, 3.1, 8.4**
    """

    @given(key=st_module_bucket_key(), hooks=st_unique_hook_entries(min_size=1, max_size=8))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_5_slice_frontmatter_and_content_integrity(self, key, hooks):
        """Feature: steering-budget-headroom, Property 5: Slice frontmatter and content integrity

        For any non-empty bucket, the slice begins with the ``inclusion: manual``
        frontmatter block, contains the module label heading, and for each member
        hook contains its bold ID, event flow, full prompt text (when present),
        and the id/name/description bullet lines, with only ``\\n`` line endings.

        **Validates: Requirements 8.2, 3.1, 8.4**
        """
        # categorize_hooks delivers each bucket sorted by hook_id; mirror that.
        sorted_hooks = sorted(hooks, key=lambda h: h.hook_id)

        content = generate_module_slice(key, sorted_hooks, total_count=len(sorted_hooks))

        # Frontmatter: must begin with the inclusion: manual block (Req 8.2).
        assert content.startswith("---\ninclusion: manual\n---\n"), (
            "Slice must begin with inclusion: manual frontmatter"
        )

        # Module label heading present (Req 3.1).
        label = _expected_module_label(key)
        assert f"## {label} Hooks" in content, (
            f"Slice must contain the '{label}' module label heading"
        )

        # Line endings: only \n, never \r (Req 8.4).
        assert "\r" not in content, "Slice must contain only \\n line endings"

        # Each member hook is fully represented (Req 3.1).
        for hook in sorted_hooks:
            # Bold hook ID.
            assert f"**{hook.hook_id}**" in content, (
                f"Slice must contain bold ID for {hook.hook_id}"
            )
            # Event flow.
            assert f"{hook.event_type} → {hook.action_type}" in content, (
                f"Slice must contain event flow for {hook.hook_id}"
            )
            # Full prompt text when present.
            if hook.prompt:
                assert hook.prompt in content, (
                    f"Slice must contain full prompt text for {hook.hook_id}"
                )
            # id / name / description bullets.
            assert f"- id: `{hook.hook_id}`" in content, (
                f"Slice must contain id bullet for {hook.hook_id}"
            )
            assert f"- name: `{hook.name}`" in content, (
                f"Slice must contain name bullet for {hook.hook_id}"
            )
            assert f"- description: `{hook.description}`" in content, (
                f"Slice must contain description bullet for {hook.hook_id}"
            )


# ---------------------------------------------------------------------------
# Feature: steering-budget-headroom
# Property 4: Slice naming convention
# Validates: Requirements 2.5, 8.1
# ---------------------------------------------------------------------------

import re

from sync_hook_registry import module_slice_filename

# Kebab-case stem: lowercase alphanumerics in hyphen-separated segments.
_KEBAB_CASE_STEM = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class TestSliceNamingConvention:
    """Property 4: Slice naming convention.

    Validates that ``module_slice_filename`` produces deterministic kebab-case
    filenames ending in ``.md``: numbered modules yield
    ``hook-registry-module-NN.md`` with a zero-padded two-digit number, and the
    unmapped group yields exactly ``hook-registry-module-any.md``.

    **Validates: Requirements 2.5, 8.1**
    """

    @given(key=st_module_bucket_key())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_4_slice_naming_convention(self, key):
        """Feature: steering-budget-headroom, Property 4: Slice naming convention

        For any module bucket key, the slice filename is kebab-case ending in
        ``.md``; a numbered module produces ``hook-registry-module-NN.md`` with a
        zero-padded two-digit number, and the unmapped group produces exactly
        ``hook-registry-module-any.md``.

        **Validates: Requirements 2.5, 8.1**
        """
        filename = module_slice_filename(key)

        # Ends in .md (Req 8.1).
        assert filename.endswith(".md"), f"Filename must end in .md: {filename!r}"

        # The stem (filename without the .md extension) is kebab-case (Req 8.1).
        stem = filename[: -len(".md")]
        assert _KEBAB_CASE_STEM.fullmatch(stem), (
            f"Filename stem must be kebab-case: {stem!r}"
        )

        if isinstance(key, int):
            # Numbered modules: zero-padded two-digit number (Req 2.5).
            expected = f"hook-registry-module-{key:02d}.md"
            assert filename == expected, (
                f"Numbered module {key} must yield {expected!r}, got {filename!r}"
            )
            # The numeric suffix is exactly two digits and zero-padded.
            number_part = stem[len("hook-registry-module-"):]
            assert len(number_part) == 2 and number_part.isdigit(), (
                f"Module number must be a zero-padded two-digit string: {number_part!r}"
            )
            assert int(number_part) == key, (
                f"Encoded number {number_part!r} must equal the key {key}"
            )
        else:
            # The unmapped group: exactly hook-registry-module-any.md (Req 2.5).
            assert filename == "hook-registry-module-any.md", (
                f"'any' group must yield 'hook-registry-module-any.md', got {filename!r}"
            )


# ---------------------------------------------------------------------------
# Feature: steering-budget-headroom
# Property 6: Slice size is the composition of its members
# Validates: Requirements 2.4, 1.2, 1.4
# ---------------------------------------------------------------------------


class TestSliceSizeComposition:
    """Property 6: Slice size is the composition of its members.

    Validates that a slice's token estimate is exactly its fixed, bounded header
    plus the sum of its member ``format_hook_entry`` renderings (each joined with
    a constant two-character newline overhead), and that the estimate is
    monotonically non-decreasing as hooks are added to the bucket. The token
    model mirrors ``measure_steering.py``'s ``round(len(content) / 4)``.

    **Validates: Requirements 2.4, 1.2, 1.4**
    """

    # Each member hook is joined into the document with two "\n" separators
    # (the separator after the header/previous part plus the trailing blank
    # line that follows every entry), so it contributes ``len(entry) + 2``.
    _SEPARATOR_OVERHEAD = 2

    @staticmethod
    def _tokens(content: str) -> int:
        """Token estimate using the chars/4 model from ``measure_steering.py``."""
        return round(len(content) / 4)

    @given(
        key=st_module_bucket_key(),
        hooks=st_unique_hook_entries(min_size=1, max_size=8),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_6_slice_size_composition(self, key, hooks):
        """Feature: steering-budget-headroom, Property 6: Slice size is the composition
        of its members

        For any module bucket, the rendered slice's token estimate equals the sum
        of its member hook-entry renderings plus a fixed, bounded header, and is
        monotonically non-decreasing as hooks are added to the bucket.

        **Validates: Requirements 2.4, 1.2, 1.4**
        """
        # categorize_hooks delivers each bucket sorted by hook_id; mirror that.
        sorted_hooks = sorted(hooks, key=lambda h: h.hook_id)

        content = generate_module_slice(
            key, sorted_hooks, total_count=len(sorted_hooks)
        )

        # The fixed, bounded header is the slice rendered with no member hooks.
        header = generate_module_slice(key, [], total_count=0)

        # The header is fixed (independent of the member hooks) and is a literal
        # prefix of every slice, so adding hooks only ever extends the document.
        assert content.startswith(header), (
            "The header must be a fixed prefix of the slice"
        )

        # The header is bounded — a small, constant preamble well under the
        # per-slice split threshold (5,000 tokens).
        assert self._tokens(header) <= 500, (
            "The fixed header must be a small, bounded preamble"
        )

        # Composition: the slice length equals the header length plus each
        # member's full format_hook_entry rendering plus its join overhead.
        expected_len = len(header) + sum(
            len(format_hook_entry(h)) + self._SEPARATOR_OVERHEAD
            for h in sorted_hooks
        )
        assert len(content) == expected_len, (
            "Slice length must be the composition of header + member renderings"
        )

        # The token estimate (chars/4) is the composition of the same parts.
        assert self._tokens(content) == round(expected_len / 4), (
            "Slice token estimate must compose from header + member renderings"
        )

        # Monotonic non-decrease: building the bucket up one hook at a time never
        # reduces the slice length or its token estimate.
        prev_len = -1
        prev_tokens = -1
        for i in range(len(sorted_hooks) + 1):
            prefix = sorted_hooks[:i]
            prefix_content = generate_module_slice(
                key, prefix, total_count=len(prefix)
            )
            prefix_len = len(prefix_content)
            prefix_tokens = self._tokens(prefix_content)

            assert prefix_len >= prev_len, (
                "Slice length must be monotonically non-decreasing as hooks are added"
            )
            assert prefix_tokens >= prev_tokens, (
                "Slice token estimate must be monotonically non-decreasing"
            )

            prev_len = prefix_len
            prev_tokens = prefix_tokens


# ---------------------------------------------------------------------------
# Feature: steering-budget-headroom
# Property 1: Slice coverage matches non-empty buckets
# Validates: Requirements 2.1, 2.2, 10.3
# ---------------------------------------------------------------------------

from sync_hook_registry import build_module_slices, load_category_mapping


@st.composite
def st_multi_module_categories(draw, hooks):
    """Build a ``hook-categories.yaml`` text exercising multi-module membership.

    Each hook is independently assigned to exactly one of:

    - ``critical`` — listed under the ``critical:`` key.
    - ``modules`` — listed under one or more numbered modules (more than one
      exercises multi-module membership, so the hook is filed under every
      bucket it belongs to).
    - ``any`` — listed under the ``any`` module group.
    - ``unmapped`` — omitted entirely (``categorize_hooks`` files it under the
      ``any`` bucket).

    Args:
        draw: Hypothesis draw callable.
        hooks: The hook entries the categories file should describe.

    Returns:
        The ``hook-categories.yaml`` text consumable by ``load_category_mapping``
        and the multi-module-aware ``categorize_hooks``.
    """
    critical_ids: list[str] = []
    module_assignments: dict[int, list[str]] = {}
    any_ids: list[str] = []

    for hook in hooks:
        choice = draw(st.sampled_from(["critical", "modules", "any", "unmapped"]))
        if choice == "critical":
            critical_ids.append(hook.hook_id)
        elif choice == "modules":
            mods = draw(
                st.lists(
                    st.sampled_from(MODULE_NUMBERS),
                    min_size=1,
                    max_size=4,
                    unique=True,
                )
            )
            for mod in mods:
                module_assignments.setdefault(mod, []).append(hook.hook_id)
        elif choice == "any":
            any_ids.append(hook.hook_id)
        # "unmapped": deliberately omitted from the categories file.

    lines: list[str] = []
    if critical_ids:
        lines.append("critical:")
        for hook_id in critical_ids:
            lines.append(f"  - {hook_id}")
    if module_assignments or any_ids:
        lines.append("modules:")
        for mod in sorted(module_assignments):
            lines.append(f"  {mod}:")
            for hook_id in module_assignments[mod]:
                lines.append(f"    - {hook_id}")
        if any_ids:
            lines.append("  any:")
            for hook_id in any_ids:
                lines.append(f"    - {hook_id}")

    return "\n".join(lines) + "\n"


class TestSliceCoverageMatchesNonEmptyBuckets:
    """Property 1: Slice coverage matches non-empty buckets.

    Validates that ``build_module_slices`` emits exactly one slice per non-empty
    module bucket produced by ``categorize_hooks`` (every numbered module that
    has hooks, plus ``any`` when it has hooks) and never emits a slice for a
    bucket with zero hooks. Multi-module membership and the ``any`` bucket are
    exercised through a synthetic ``hook-categories.yaml`` consumed by the
    multi-module-aware ``categorize_hooks``.

    **Validates: Requirements 2.1, 2.2, 10.3**
    """

    @given(data=st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_1_slice_coverage_matches_non_empty_buckets(self, data):
        """Feature: steering-budget-headroom, Property 1: Slice coverage matches non-empty buckets

        For any set of hooks and category mapping, the emitted slice-key set
        equals exactly ``{steering_dir / module_slice_filename(k)}`` for every
        non-empty bucket from ``categorize_hooks``, and no slice is emitted for a
        zero-hook bucket.

        **Validates: Requirements 2.1, 2.2, 10.3**
        """
        hooks = data.draw(st_unique_hook_entries(min_size=1, max_size=8))
        categories_text = data.draw(st_multi_module_categories(hooks))

        with tempfile.TemporaryDirectory() as tmp_dir:
            cat_path = Path(tmp_dir) / "hook-categories.yaml"
            cat_path.write_text(categories_text, encoding="utf-8")
            steering_dir = Path(tmp_dir) / "steering"

            # Multi-module-aware categorization reads membership from the file.
            mapping = load_category_mapping(cat_path)
            critical, module_hooks = categorize_hooks(hooks, mapping, cat_path)

            slices = build_module_slices(module_hooks, steering_dir, len(hooks))

        # Coverage: the emitted slice keys equal exactly the non-empty buckets.
        expected_keys = {
            steering_dir / module_slice_filename(key) for key in module_hooks
        }
        assert set(slices.keys()) == expected_keys, (
            "Slice keys must equal exactly the non-empty bucket slice paths"
        )

        # One slice per non-empty bucket (no duplicates, no extras).
        assert len(slices) == len(module_hooks), (
            "There must be exactly one slice per non-empty bucket"
        )

        # Every bucket that produced a slice is genuinely non-empty (Req 10.3).
        for key, bucket_hooks in module_hooks.items():
            assert len(bucket_hooks) >= 1, (
                f"Bucket {key!r} must be non-empty to emit a slice"
            )

        # No slice is emitted for a numbered module with zero hooks (Req 10.3).
        for mod in MODULE_NUMBERS:
            if mod not in module_hooks:
                assert (steering_dir / module_slice_filename(mod)) not in slices, (
                    f"Module {mod} has no hooks and must not emit a slice"
                )


# ---------------------------------------------------------------------------
# Feature: steering-budget-headroom
# Property 2: Hook-ID union completeness and multi-module presence
# Validates: Requirements 2.3, 3.1, 3.2
# ---------------------------------------------------------------------------

from sync_hook_registry import generate_registry_critical


class TestHookIdUnionCompletenessAndMultiModulePresence:
    """Property 2: Hook-ID union completeness and multi-module presence.

    Validates two complementary reachability guarantees over the generated
    registry. First, every source hook is reachable: the union of hook IDs whose
    full entry appears in the critical file or in any module slice equals the
    source hook-ID set (Requirements 3.1, 3.2). Second, a hook whose membership
    spans multiple module buckets has its full prompt rendered in the slice for
    each associated module (Requirement 2.3). Multi-module membership and the
    ``any`` bucket are exercised through a synthetic ``hook-categories.yaml``
    consumed by the multi-module-aware ``categorize_hooks``.

    **Validates: Requirements 2.3, 3.1, 3.2**
    """

    @given(data=st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_2_hook_id_union_completeness_and_multi_module_presence(self, data):
        """Feature: steering-budget-headroom, Property 2: Hook-ID union completeness and
        multi-module presence

        For any set of hooks and category mapping, the union of hook IDs across
        the critical file and all module slices equals the source hook-ID set,
        and any hook associated with multiple modules has its full prompt present
        in the slice for each of its associated modules.

        **Validates: Requirements 2.3, 3.1, 3.2**
        """
        hooks = data.draw(st_unique_hook_entries(min_size=1, max_size=8))
        categories_text = data.draw(st_multi_module_categories(hooks))

        with tempfile.TemporaryDirectory() as tmp_dir:
            cat_path = Path(tmp_dir) / "hook-categories.yaml"
            cat_path.write_text(categories_text, encoding="utf-8")
            steering_dir = Path(tmp_dir) / "steering"

            # Multi-module-aware categorization reads membership from the file.
            mapping = load_category_mapping(cat_path)
            critical, module_hooks = categorize_hooks(hooks, mapping, cat_path)

            critical_content = generate_registry_critical(critical, len(hooks))
            slices = build_module_slices(module_hooks, steering_dir, len(hooks))

        source_ids = {hook.hook_id for hook in hooks}

        # A hook is "present" in a registry file when its full ``format_hook_entry``
        # rendering appears verbatim. Checking the whole entry block (not just the
        # bold ID) avoids false positives from prompt text that happens to contain
        # another hook's marker, and confirms the full prompt is reachable.
        entry_by_id = {hook.hook_id: format_hook_entry(hook) for hook in hooks}
        all_contents = [critical_content, *slices.values()]

        found_ids = {
            hook_id
            for hook_id, entry in entry_by_id.items()
            if any(entry in content for content in all_contents)
        }

        # Union completeness: every source hook is reachable through the critical
        # file or a module slice, and nothing extra is introduced (Reqs 3.1, 3.2).
        assert found_ids == source_ids, (
            "Union of hook IDs across critical + all slices must equal the source set"
        )

        # Multi-module presence: a hook filed under more than one module bucket
        # has its full prompt rendered in EACH associated slice (Req 2.3).
        membership: dict[str, list[int | str]] = {}
        for key, bucket_hooks in module_hooks.items():
            for hook in bucket_hooks:
                membership.setdefault(hook.hook_id, []).append(key)

        for hook_id, keys in membership.items():
            entry = entry_by_id[hook_id]
            for key in keys:
                slice_content = slices[steering_dir / module_slice_filename(key)]
                assert entry in slice_content, (
                    f"{hook_id} must have its full prompt in the slice for module {key!r}"
                )
            # When a hook spans multiple module buckets, it is genuinely present
            # in more than one distinct slice (Req 2.3).
            if len(keys) > 1:
                assert len(set(keys)) == len(keys), (
                    f"{hook_id} multi-module bucket keys must be distinct"
                )


# ---------------------------------------------------------------------------
# Feature: steering-budget-headroom
# Property 3: Deterministic, order-independent rendering
# Validates: Requirements 2.6, 6.1
# ---------------------------------------------------------------------------


class TestDeterministicOrderIndependentRendering:
    """Property 3: Deterministic, order-independent rendering.

    Validates that ``build_module_slices`` is a pure, deterministic function of
    the hook set and category mapping: rendering the slice set twice from the
    same input (idempotence) and again from a reordered input list produces the
    exact same set of slice paths and byte-identical content for every path.
    Multi-module membership and the ``any`` bucket are exercised through a
    synthetic ``hook-categories.yaml`` consumed by the multi-module-aware
    ``categorize_hooks``.

    **Validates: Requirements 2.6, 6.1**
    """

    @staticmethod
    def _render_slices(hooks, categories_text, steering_dir):
        """Categorize *hooks* and render the full slice map under *steering_dir*.

        Args:
            hooks: The hook entries to categorize and render.
            categories_text: The ``hook-categories.yaml`` text describing the
                category/module membership of *hooks*.
            steering_dir: The steering directory the slice paths are derived from.

        Returns:
            The ``{slice_path: content}`` map produced by ``build_module_slices``.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            cat_path = Path(tmp_dir) / "hook-categories.yaml"
            cat_path.write_text(categories_text, encoding="utf-8")

            mapping = load_category_mapping(cat_path)
            _critical, module_hooks = categorize_hooks(hooks, mapping, cat_path)
            return build_module_slices(module_hooks, steering_dir, len(hooks))

    @given(data=st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_3_deterministic_order_independent_rendering(self, data):
        """Feature: steering-budget-headroom, Property 3: Deterministic, order-independent rendering

        For any set of hooks and category mapping, rendering the slice set twice
        — and rendering it again from a reordered input list — produces
        byte-identical content for every slice path.

        **Validates: Requirements 2.6, 6.1**
        """
        hooks = data.draw(st_unique_hook_entries(min_size=1, max_size=8))
        categories_text = data.draw(st_multi_module_categories(hooks))

        # A fixed steering directory so slice paths are comparable across renders.
        steering_dir = Path("/steering")

        # First render from the original input order.
        slices_first = self._render_slices(hooks, categories_text, steering_dir)

        # Second render from the identical input order (idempotence).
        slices_again = self._render_slices(hooks, categories_text, steering_dir)

        # Third render from a reversed/reordered input list (order independence).
        reordered = list(reversed(hooks))
        slices_reordered = self._render_slices(reordered, categories_text, steering_dir)

        # The exact same set of slice paths is emitted every time.
        assert set(slices_first) == set(slices_again), (
            "Re-rendering the same input must emit the same slice paths"
        )
        assert set(slices_first) == set(slices_reordered), (
            "Reordering the input must emit the same slice paths"
        )

        # Every slice path renders byte-identical content across all three renders.
        for path, content in slices_first.items():
            assert slices_again[path] == content, (
                f"Re-rendering must be byte-identical for {path}"
            )
            assert slices_reordered[path] == content, (
                f"Reordered rendering must be byte-identical for {path}"
            )


# ---------------------------------------------------------------------------
# Feature: steering-budget-headroom
# Example test: summary routing instruction (Task 5.3)
# Validates: Requirements 5.1, 5.2, 3.4
# ---------------------------------------------------------------------------


class TestSummaryRoutingInstruction:
    """Example test for the ``hook-registry.md`` summary routing instruction.

    A concrete (non-property) check that ``generate_registry_summary`` produces a
    summary that:

    - instructs the agent to resolve ``current_module`` from
      ``config/bootcamp_progress.json`` (Requirement 5.2),
    - instructs loading the matching per-module slice
      (``hook-registry-module-<NN>.md`` / ``-any.md``) for module hook prompts
      (Requirement 5.2),
    - lists every hook by ID (Requirements 5.1, 3.4),
    - and does NOT reference the deprecated monolithic ``hook-registry-modules.md``.

    **Validates: Requirements 5.1, 5.2, 3.4**
    """

    def test_summary_routes_to_per_module_slice_and_lists_every_hook(self):
        """Feature: steering-budget-headroom, Example: summary routing instruction

        Build a small fixed set of hooks plus a category mapping, generate the
        summary, and assert the routing instruction and full hook listing.

        **Validates: Requirements 5.1, 5.2, 3.4**
        """
        # A small fixed set of hooks: two critical, two module hooks (one in a
        # numbered module, one unmapped -> the "any" group).
        hooks = [
            HookEntry(
                hook_id="alpha-critical",
                name="Alpha Critical",
                description="Critical onboarding hook alpha.",
                event_type="promptSubmit",
                action_type="askAgent",
                prompt="Do the alpha critical thing.",
            ),
            HookEntry(
                hook_id="beta-critical",
                name="Beta Critical",
                description="Critical onboarding hook beta.",
                event_type="agentStop",
                action_type="askAgent",
                prompt="Do the beta critical thing.",
            ),
            HookEntry(
                hook_id="gamma-module",
                name="Gamma Module",
                description="Module 3 hook gamma.",
                event_type="fileEdited",
                action_type="runCommand",
                prompt="Do the gamma module thing.",
            ),
            HookEntry(
                hook_id="delta-any",
                name="Delta Any",
                description="Any-module hook delta.",
                event_type="userTriggered",
                action_type="askAgent",
                prompt="Do the delta any thing.",
            ),
        ]

        mapping = {
            "alpha-critical": CategoryMapping(
                hook_id="alpha-critical", category="critical"
            ),
            "beta-critical": CategoryMapping(
                hook_id="beta-critical", category="critical"
            ),
            "gamma-module": CategoryMapping(
                hook_id="gamma-module", category="module", module_number=3
            ),
            # delta-any is left unmapped -> categorize_hooks files it under "any".
        }

        critical, modules = categorize_hooks(hooks, mapping)
        content = generate_registry_summary(critical, modules, total_count=len(hooks))

        # (1) Instructs resolving current_module from the progress file (Req 5.2).
        assert "current_module" in content, (
            "Summary must mention resolving current_module"
        )
        assert "config/bootcamp_progress.json" in content, (
            "Summary must instruct resolving current_module from "
            "config/bootcamp_progress.json"
        )

        # (2) Instructs loading the matching per-module slice (Req 5.2).
        assert "hook-registry-module-" in content, (
            "Summary must instruct loading the per-module slice "
            "(hook-registry-module-<NN>.md)"
        )

        # (3) Every hook appears in the summary, listed by ID (Reqs 5.1, 3.4).
        for hook in hooks:
            assert hook.hook_id in content, (
                f"Summary must list hook {hook.hook_id} by ID"
            )

        # The deprecated monolithic registry is no longer referenced.
        assert "hook-registry-modules.md" not in content, (
            "Summary must not reference the deprecated hook-registry-modules.md"
        )


# ---------------------------------------------------------------------------
# Feature: steering-budget-headroom
# Property 7: Verify semantics including orphan detection
# Validates: Requirements 6.3, 6.4, 6.5
# ---------------------------------------------------------------------------

import contextlib

import sync_hook_registry as _shr
from sync_hook_registry import main as _sync_main


def _hook_entry_to_hook_json(entry: HookEntry) -> dict:
    """Build a ``.kiro.hook`` JSON dict from a :class:`HookEntry`.

    Reconstructs the on-disk JSON shape ``parse_hook_file`` consumes: ``name`` /
    ``description`` top-level, ``when.type`` / ``then.type``, and the optional
    ``then.prompt``, ``when.patterns`` and ``when.toolTypes`` fields. The
    comma-joined display strings on the entry (``file_patterns`` / ``tool_types``)
    are split back into the JSON arrays they came from so the round trip is exact.

    Args:
        entry: The hook entry to serialise.

    Returns:
        A JSON-serialisable dict for a single ``*.kiro.hook`` file.
    """
    data: dict = {
        "name": entry.name,
        "description": entry.description,
        "version": "1.0.0",
        "when": {"type": entry.event_type},
        "then": {"type": entry.action_type},
    }
    if entry.prompt is not None:
        data["then"]["prompt"] = entry.prompt
    if entry.file_patterns is not None:
        data["when"]["patterns"] = entry.file_patterns.split(", ")
    if entry.tool_types is not None:
        data["when"]["toolTypes"] = entry.tool_types.split(", ")
    return data


def _write_synthetic_hooks(hooks: list[HookEntry], hooks_dir: Path) -> None:
    """Write *hooks* as ``{hook_id}.kiro.hook`` JSON files under *hooks_dir*."""
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for entry in hooks:
        hook_file = hooks_dir / f"{entry.hook_id}.kiro.hook"
        hook_file.write_text(
            json.dumps(_hook_entry_to_hook_json(entry)), encoding="utf-8"
        )


@contextlib.contextmanager
def _patched_module_paths(
    hooks_dir: Path, lockfile_path: Path, deprecated_paths: tuple[Path, ...]
):
    """Temporarily redirect the module-level real-repo paths into a tempdir.

    ``sync_hook_registry`` hardcodes ``HOOKS_DIR`` (used by ``generate_lockfile``
    to read hook versions), ``LOCKFILE_PATH`` (read during ``--verify`` and
    written during ``--write``), and ``DEPRECATED_REGISTRY_PATHS`` (the orphan
    set) as module globals pointing at the real repo. The verify test exercises
    ``main()`` in process, so these are redirected into the per-example tempdir
    to keep the real repo files untouched and the orphan path testable. Originals
    are restored on exit.

    Args:
        hooks_dir: Temp hooks directory for ``HOOKS_DIR``.
        lockfile_path: Temp lockfile path for ``LOCKFILE_PATH``.
        deprecated_paths: Temp orphan paths for ``DEPRECATED_REGISTRY_PATHS``.
    """
    saved = (_shr.HOOKS_DIR, _shr.LOCKFILE_PATH, _shr.DEPRECATED_REGISTRY_PATHS)
    _shr.HOOKS_DIR = hooks_dir
    _shr.LOCKFILE_PATH = lockfile_path
    _shr.DEPRECATED_REGISTRY_PATHS = deprecated_paths
    try:
        yield
    finally:
        (_shr.HOOKS_DIR, _shr.LOCKFILE_PATH, _shr.DEPRECATED_REGISTRY_PATHS) = saved


def _run_cli(argv: list[str]) -> int:
    """Invoke ``sync_hook_registry.main()`` in process with *argv*.

    Monkeypatches ``sys.argv`` for the call (``main`` reads ``parse_args()`` with
    no argv parameter) and normalises the result to an exit code: ``--write``
    returns normally on success (treated as ``0``) while ``--verify`` always
    raises ``SystemExit`` with ``0`` (all match) or ``1`` (mismatch / orphan).

    Args:
        argv: CLI arguments (excluding the program name).

    Returns:
        The process exit code (``0`` on success, non-zero on failure).
    """
    old_argv = sys.argv
    sys.argv = ["sync_hook_registry.py", *argv]
    try:
        _sync_main()
        return 0
    except SystemExit as exc:
        code = exc.code
        return 0 if code is None else int(code)
    finally:
        sys.argv = old_argv


class TestVerifySemanticsIncludingOrphanDetection:
    """Property 7: Verify semantics including orphan detection.

    Validates the end-to-end ``--verify`` contract by driving ``main()`` in
    process against a synthetic hook corpus written entirely inside a tempdir
    (the real-repo ``HOOKS_DIR`` / ``LOCKFILE_PATH`` / ``DEPRECATED_REGISTRY_PATHS``
    globals are redirected into that tempdir, so no real repo file is touched and
    ``--write`` is safe). For a freshly written corpus ``--verify`` exits 0; after
    deleting a slice it exits non-zero (missing); after corrupting a slice it
    exits non-zero (differs); and after planting the deprecated
    ``hook-registry-modules.md`` it exits non-zero (orphan).

    **Validates: Requirements 6.3, 6.4, 6.5**
    """

    @given(data=st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_7_verify_semantics_including_orphan_detection(self, data):
        """Feature: steering-budget-headroom, Property 7: Verify semantics including
        orphan detection

        For any generated content and on-disk state, ``--verify`` reports a match
        iff the file exists and is byte-identical, a non-match when missing or
        differing, and a non-match (orphan) when a deprecated registry path still
        exists on disk.

        **Validates: Requirements 6.3, 6.4, 6.5**
        """
        hooks = data.draw(st_unique_hook_entries(min_size=1, max_size=5))
        categories_text = data.draw(st_multi_module_categories(hooks))

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            hooks_dir = tmp / "hooks"
            steering_dir = tmp / "steering"
            cat_path = hooks_dir / "hook-categories.yaml"
            summary_path = steering_dir / "hook-registry.md"
            critical_path = steering_dir / "hook-registry-critical.md"
            lockfile_path = tmp / "hooks.lock.yaml"
            deprecated_path = steering_dir / "hook-registry-modules.md"

            _write_synthetic_hooks(hooks, hooks_dir)
            cat_path.write_text(categories_text, encoding="utf-8")

            write_argv = [
                "--write",
                "--hooks-dir", str(hooks_dir),
                "--output", str(summary_path),
                "--output-critical", str(critical_path),
                "--steering-dir", str(steering_dir),
                "--categories", str(cat_path),
            ]
            verify_argv = [
                "--verify",
                "--hooks-dir", str(hooks_dir),
                "--output", str(summary_path),
                "--output-critical", str(critical_path),
                "--steering-dir", str(steering_dir),
                "--categories", str(cat_path),
            ]

            with _patched_module_paths(
                hooks_dir, lockfile_path, (deprecated_path,)
            ):
                # Determine the module slice set the generator will emit so the
                # mutation cases can target a real slice path.
                mapping = load_category_mapping(cat_path)
                _critical, module_hooks = categorize_hooks(hooks, mapping, cat_path)
                slice_paths = sorted(
                    build_module_slices(module_hooks, steering_dir, len(hooks)).keys()
                )

                # Fresh write, then verify: every file matches and no orphan
                # exists, so verify exits 0 (Req 6.3, 6.5).
                assert _run_cli(write_argv) == 0, "Initial --write must succeed"
                assert _run_cli(verify_argv) == 0, (
                    "Freshly written corpus must verify clean (exit 0)"
                )

                if slice_paths:
                    target = slice_paths[0]

                    # Missing: deleting a generated slice makes verify fail
                    # (Req 6.4). Re-write restores the clean state afterwards.
                    target.unlink()
                    assert _run_cli(verify_argv) != 0, (
                        "Verify must fail when a generated slice is missing"
                    )
                    assert _run_cli(write_argv) == 0
                    assert _run_cli(verify_argv) == 0, (
                        "Re-write must restore the clean state"
                    )

                    # Differs: corrupting a slice's bytes makes verify fail
                    # (Req 6.4). Re-write restores the clean state afterwards.
                    target.write_text(
                        target.read_text(encoding="utf-8") + "\ndrift marker\n",
                        encoding="utf-8",
                    )
                    assert _run_cli(verify_argv) != 0, (
                        "Verify must fail when a generated slice differs"
                    )
                    assert _run_cli(write_argv) == 0
                    assert _run_cli(verify_argv) == 0, (
                        "Re-write must restore the clean state"
                    )

                # Orphan: a lingering deprecated registry file makes verify fail
                # even though every generated file still matches (Req 6.5).
                deprecated_path.write_text(
                    "# deprecated monolith\n", encoding="utf-8"
                )
                assert _run_cli(verify_argv) != 0, (
                    "Verify must fail (orphan) when a deprecated registry path exists"
                )

                # --write removes the orphan, restoring a clean verify (Req 6.5).
                assert _run_cli(write_argv) == 0
                assert not deprecated_path.exists(), (
                    "--write must remove the deprecated orphan file"
                )
                assert _run_cli(verify_argv) == 0, (
                    "Verify must pass once the orphan is removed"
                )


# ---------------------------------------------------------------------------
# Feature: steering-budget-headroom
# Example test: deprecated-monolith handling (Task 6.5)
# Validates: Requirements 6.2, 6.3
# ---------------------------------------------------------------------------


class TestDeprecatedMonolithHandling:
    """Example test for deprecated ``hook-registry-modules.md`` handling.

    A concrete (non-property) end-to-end check that drives ``main()`` in process
    against a small fixed synthetic hook corpus written entirely inside a tempdir
    (the real-repo ``HOOKS_DIR`` / ``LOCKFILE_PATH`` / ``DEPRECATED_REGISTRY_PATHS``
    globals are redirected into that tempdir, so no real repo file is touched).
    It asserts that:

    - ``--verify`` fails (exit non-zero) when the deprecated monolithic
      ``hook-registry-modules.md`` is present as an orphan (Requirement 6.3), and
    - ``--write`` removes that pre-existing orphan and a subsequent ``--verify``
      passes (exit 0) (Requirement 6.2).

    **Validates: Requirements 6.2, 6.3**
    """

    def test_write_removes_orphan_and_verify_fails_when_present(self):
        """Feature: steering-budget-headroom, Example: deprecated-monolith handling

        Run ``--write`` on a fixed corpus, plant a deprecated
        ``hook-registry-modules.md`` orphan and confirm ``--verify`` returns
        non-zero, then run ``--write`` again and confirm the orphan is removed and
        ``--verify`` returns 0.

        **Validates: Requirements 6.2, 6.3**
        """
        # A small fixed set of hooks: one critical, one numbered-module hook, and
        # one "any" module hook, so --write emits the critical file plus at least
        # one numbered slice and the "any" slice.
        hooks = [
            HookEntry(
                hook_id="alpha-critical",
                name="Alpha Critical",
                description="Critical onboarding hook alpha.",
                event_type="promptSubmit",
                action_type="askAgent",
                prompt="Do the alpha critical thing.",
            ),
            HookEntry(
                hook_id="gamma-module",
                name="Gamma Module",
                description="Module 3 hook gamma.",
                event_type="fileEdited",
                action_type="runCommand",
                prompt="Do the gamma module thing.",
            ),
            HookEntry(
                hook_id="delta-any",
                name="Delta Any",
                description="Any-module hook delta.",
                event_type="userTriggered",
                action_type="askAgent",
                prompt="Do the delta any thing.",
            ),
        ]

        # A concrete hook-categories.yaml: alpha is critical, gamma is filed under
        # module 3, and delta is filed under the "any" module group.
        categories_text = (
            "critical:\n"
            "  - alpha-critical\n"
            "modules:\n"
            "  3:\n"
            "    - gamma-module\n"
            "  any:\n"
            "    - delta-any\n"
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            hooks_dir = tmp / "hooks"
            steering_dir = tmp / "steering"
            cat_path = hooks_dir / "hook-categories.yaml"
            summary_path = steering_dir / "hook-registry.md"
            critical_path = steering_dir / "hook-registry-critical.md"
            lockfile_path = tmp / "hooks.lock.yaml"
            deprecated_path = steering_dir / "hook-registry-modules.md"

            _write_synthetic_hooks(hooks, hooks_dir)
            cat_path.write_text(categories_text, encoding="utf-8")

            write_argv = [
                "--write",
                "--hooks-dir", str(hooks_dir),
                "--output", str(summary_path),
                "--output-critical", str(critical_path),
                "--steering-dir", str(steering_dir),
                "--categories", str(cat_path),
            ]
            verify_argv = [
                "--verify",
                "--hooks-dir", str(hooks_dir),
                "--output", str(summary_path),
                "--output-critical", str(critical_path),
                "--steering-dir", str(steering_dir),
                "--categories", str(cat_path),
            ]

            with _patched_module_paths(
                hooks_dir, lockfile_path, (deprecated_path,)
            ):
                # Fresh write of the sliced registry, then a clean verify.
                assert _run_cli(write_argv) == 0, "Initial --write must succeed"
                assert _run_cli(verify_argv) == 0, (
                    "Freshly written corpus must verify clean (exit 0)"
                )

                # Plant the deprecated monolith: --verify must now fail (orphan).
                deprecated_path.write_text(
                    "# deprecated monolith\n", encoding="utf-8"
                )
                assert deprecated_path.exists()
                assert _run_cli(verify_argv) != 0, (
                    "Verify must fail when hook-registry-modules.md is present"
                )

                # --write removes the pre-existing orphan...
                assert _run_cli(write_argv) == 0, (
                    "--write must succeed and remove the orphan"
                )
                assert not deprecated_path.exists(), (
                    "--write must remove the pre-existing hook-registry-modules.md"
                )

                # ...and a subsequent --verify passes once the orphan is gone.
                assert _run_cli(verify_argv) == 0, (
                    "Verify must pass once the deprecated monolith is removed"
                )


# ---------------------------------------------------------------------------
# Feature: steering-budget-headroom
# Real-corpus slice size bound (example test, not iterated over random hooks)
# Validates: Requirements 2.4, 1.2, 1.4
# ---------------------------------------------------------------------------

from sync_hook_registry import parse_all_hooks

# Repo-relative paths to the live hook corpus. The test file lives at
# ``<repo>/senzing-bootcamp/tests/``, so ``parents[2]`` is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_HOOKS_DIR = _REPO_ROOT / "senzing-bootcamp" / "hooks"
_CATEGORIES_PATH = _HOOKS_DIR / "hook-categories.yaml"

# Per-slice split threshold (tokens) and the 50%-of-monolith ceiling.
_SPLIT_THRESHOLD_TOKENS = 5000
_PRE_REFACTOR_MONOLITH_TOKENS = 10631
_HALF_MONOLITH_TOKENS = round(_PRE_REFACTOR_MONOLITH_TOKENS * 0.5)  # 5315


def _estimate_tokens(content: str) -> int:
    """Token estimate using the chars/4 model from ``measure_steering.py``."""
    return round(len(content) / 4)


class TestRealCorpusSliceSizeBound:
    """Real-corpus slice size bound.

    Runs the generator against the actual ``hooks/`` directory and
    ``hook-categories.yaml`` and asserts every emitted Hook_Registry_Module_Slice
    is at or below the 5,000-token Split_Threshold and that the largest slice is
    at or below 5,315 tokens (50% of the pre-refactor 10,631-token
    ``hook-registry-modules.md``). This concrete bound is data-dependent, so it
    is an example test rather than a property over random hooks. No files are
    written to disk — ``build_module_slices`` returns content in memory and the
    test measures the dict values directly.

    **Validates: Requirements 2.4, 1.2, 1.4**
    """

    def test_every_real_slice_is_within_the_size_bounds(self):
        """Feature: steering-budget-headroom, real-corpus slice size bound

        Every emitted slice is <= 5,000 tokens (chars/4) and the largest slice
        is <= 5,315 tokens (50% of the 10,631-token monolith).

        **Validates: Requirements 2.4, 1.2, 1.4**
        """
        # The live corpus must be present.
        assert _HOOKS_DIR.is_dir(), f"Hooks directory not found: {_HOOKS_DIR}"
        assert _CATEGORIES_PATH.is_file(), (
            f"Categories file not found: {_CATEGORIES_PATH}"
        )

        # Run the real parse -> categorize -> slice pipeline.
        hooks, errors = parse_all_hooks(_HOOKS_DIR)
        assert not errors, f"Hook parse errors against the real corpus: {errors}"
        assert hooks, "Expected at least one hook in the real corpus"

        mapping = load_category_mapping(_CATEGORIES_PATH)
        _critical, module_hooks = categorize_hooks(
            hooks, mapping, _CATEGORIES_PATH
        )

        # Emit the in-memory slice set (no disk writes). The steering_dir only
        # informs slice key paths, so any path works for measuring content.
        slices = build_module_slices(
            module_hooks, _HOOKS_DIR, total_count=len(hooks)
        )
        assert slices, "Expected at least one emitted module slice"

        # Measure every emitted slice's token estimate.
        token_counts = {
            slice_path: _estimate_tokens(content)
            for slice_path, content in slices.items()
        }

        # Every slice is at or below the 5,000-token Split_Threshold (Req 2.4, 1.2).
        for slice_path, tokens in token_counts.items():
            assert tokens <= _SPLIT_THRESHOLD_TOKENS, (
                f"Slice {slice_path.name} is {tokens} tokens, "
                f"over the {_SPLIT_THRESHOLD_TOKENS}-token split threshold"
            )

        # The largest slice is at or below 50% of the monolith (Req 1.4).
        largest_path = max(token_counts, key=token_counts.get)
        largest_tokens = token_counts[largest_path]
        assert largest_tokens <= _HALF_MONOLITH_TOKENS, (
            f"Largest slice {largest_path.name} is {largest_tokens} tokens, "
            f"over the {_HALF_MONOLITH_TOKENS}-token (50% of {_PRE_REFACTOR_MONOLITH_TOKENS}) ceiling"  # noqa: E501
        )
