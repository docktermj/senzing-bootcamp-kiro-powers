"""Property-based tests for sync_hook_registry.py using Hypothesis.

Feature: hook-registry-source-of-truth
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from sync_hook_registry import (
    HookEntry,
    CategoryMapping,
    parse_hook_file,
    categorize_hooks,
    format_hook_entry,
    generate_registry_summary,
    generate_registry_detail,
    verify_registry,
    write_registry,
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
