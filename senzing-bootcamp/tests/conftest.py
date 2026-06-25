"""Shared fixtures for senzing-bootcamp script tests."""

import json
import os
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Hypothesis profile — centralized in the repo-root ``hypothesis_profiles``
# ---------------------------------------------------------------------------
# Profile registration and selection live in the repo-root ``hypothesis_profiles``
# module so both collection roots (``senzing-bootcamp/tests/`` and ``tests/``)
# stay in sync. It registers the profiles, resolves the active one from the
# ``HYPOTHESIS_PROFILE`` environment variable, and loads it. Every profile sets
# ``deadline=None`` and suppresses the ``too_slow`` health check, preserving the
# previous timing behavior under variable CI/local machine load. Per-test
# ``@settings`` still take precedence for any key they specify.
_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import hypothesis_profiles

hypothesis_profiles.load_active_profile()

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)


@pytest.fixture(autouse=True)
def _recover_stale_cwd():
    """Recover from a stale cwd before every test.

    Some tests use raw ``os.chdir`` in try/finally blocks. If the
    restored directory was a temp dir that got cleaned up, the cwd
    becomes invalid and subsequent ``monkeypatch.chdir`` calls fail.
    Also restores to the project root if cwd was changed to a temp dir.
    """
    try:
        cwd = os.getcwd()
    except (FileNotFoundError, OSError):
        os.chdir(_PROJECT_ROOT)
        return
    # If cwd is inside /tmp (left over from a previous test), restore to project root
    if cwd.startswith("/tmp") or cwd.startswith("/var"):
        os.chdir(_PROJECT_ROOT)


@pytest.fixture()
def project_root(tmp_path, monkeypatch):
    """Create an isolated project root and chdir into it."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture(scope="session")
def sample_progress_data():
    """Factory that returns valid bootcamp_progress.json content.

    Parameters are optional — sensible defaults are provided.
    """

    def _factory(
        modules_completed=None,
        current_module=1,
        language="python",
    ):
        return {
            "modules_completed": modules_completed if modules_completed is not None else [],
            "current_module": current_module,
            "language": language,
            "database_type": "sqlite",
            "data_sources": [],
            "current_step": 1,
            "step_history": {},
        }

    return _factory


@pytest.fixture()
def write_progress_file(project_root):
    """Write *data* dict as ``config/bootcamp_progress.json`` inside *project_root*."""

    def _write(data: dict):
        cfg = project_root / "config"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "bootcamp_progress.json").write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    return _write


@pytest.fixture()
def mock_no_color(monkeypatch):
    """Set NO_COLOR=1 so scripts disable ANSI colour codes."""
    monkeypatch.setenv("NO_COLOR", "1")


# ---------------------------------------------------------------------------
# generated-power-docs: shared property-test strategies and world materializer
# ---------------------------------------------------------------------------
#
# The generate_power_docs.py generator reads a self-consistent set of sources
# (the real MCP tool inventory, discovered ``*.kiro.hook`` files plus
# ``hook-categories.yaml``, a ``steering-index.yaml`` with per-file metadata,
# and a ``module-dependencies.yaml`` module map) and regenerates four marker-
# delimited regions in ``POWER.md``. These helpers let property tests build an
# arbitrary-but-valid such world under a throwaway directory.
#
# The split is deliberate: ``st_world_spec()`` is a pure Hypothesis strategy
# producing a plain :class:`WorldSpec` (no filesystem effects), and
# ``materialize_world(spec, base_dir)`` writes every source file plus a
# ``POWER.md`` skeleton with the four marker pairs and returns a
# :class:`MaterializedWorld`. Tests draw a ``WorldSpec`` with ``@given`` and
# materialize it into a fresh per-example directory (``tempfile.mkdtemp``),
# matching the established pattern in this suite.

from dataclasses import dataclass

from hypothesis import assume
from hypothesis import strategies as st
from hypothesis.strategies import composite

# The four region identifiers the generator regenerates, in document order.
REGION_IDS: tuple[str, ...] = ("mcp-tools", "hooks", "steering-files", "modules")

# Allowed steering size categories recorded in ``steering-index.yaml``.
SIZE_CATEGORIES: tuple[str, ...] = ("small", "medium", "large")

_HOOK_ID_ALPHABET = "abcdefghijklmnopqrstuvwxyz-"
_FILENAME_STEM_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789-"
_MODULE_NAME_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
)
_PROSE_WORD = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=8)


@dataclass(frozen=True)
class SteeringEntry:
    """One steering file's recorded metadata for a generated world.

    Attributes:
        filename: The steering file name (always ends in ``.md``).
        token_count: The recorded token count.
        size_category: One of :data:`SIZE_CATEGORIES`.
    """

    filename: str
    token_count: int
    size_category: str


@dataclass(frozen=True)
class ModuleEntry:
    """One bootcamp module's number and name for a generated world.

    Attributes:
        number: The module number (a distinct positive integer).
        name: The module display name (no pipes or newlines).
    """

    number: int
    name: str


@dataclass(frozen=True)
class WorldSpec:
    """A pure description of a self-consistent generator source world.

    Carries everything ``materialize_world`` needs to write the sources and the
    ``POWER.md`` skeleton. Holds no filesystem state, so it is safe to draw with
    ``@given`` and materialize into many different directories.

    Attributes:
        hook_ids: Unique hook ids; each gets a ``<id>.kiro.hook`` file.
        critical_ids: Subset of ``hook_ids`` listed under ``critical:``.
        steering: Per-file steering metadata records.
        modules: Module records with distinct numbers.
        budget_total: The ``budget.total_tokens`` value for the steering index.
        prose: Surrounding hand-written prose lines for the skeleton (length 5).
    """

    hook_ids: tuple[str, ...]
    critical_ids: tuple[str, ...]
    steering: tuple[SteeringEntry, ...]
    modules: tuple[ModuleEntry, ...]
    budget_total: int
    prose: tuple[str, ...]


@dataclass(frozen=True)
class MaterializedWorld:
    """A :class:`WorldSpec` written to disk, ready to feed the generator.

    Attributes:
        paths: The ``SourcePaths`` pointing at the written world.
        spec: The originating :class:`WorldSpec` (the expected sources).
        world_dir: The root directory the world was written under.
    """

    paths: object
    spec: WorldSpec
    world_dir: Path


# ---------------------------------------------------------------------------
# Element strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------


@composite
def st_hook_id(draw) -> str:
    """Draw a valid hook id: lowercase letters/hyphens, no leading/trailing ``-``.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A non-empty hook id usable as a ``*.kiro.hook`` filename stem.
    """
    raw = draw(st.text(alphabet=_HOOK_ID_ALPHABET, min_size=1, max_size=12))
    cleaned = raw.strip("-")
    assume(cleaned)
    return cleaned


@composite
def st_steering_filename(draw) -> str:
    """Draw a steering filename of the form ``<stem>.md``.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A non-empty steering filename ending in ``.md``.
    """
    stem = draw(st.text(alphabet=_FILENAME_STEM_ALPHABET, min_size=1, max_size=12))
    stem = stem.strip("-")
    assume(stem)
    return f"{stem}.md"


@composite
def st_module_name(draw) -> str:
    """Draw a simple module name (letters/digits/spaces, trimmed, non-empty).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A module name with no pipe or newline characters.
    """
    raw = draw(st.text(alphabet=_MODULE_NAME_ALPHABET, min_size=1, max_size=30))
    name = raw.strip()
    assume(name)
    return name


@composite
def st_prose_line(draw) -> str:
    """Draw a single lint-safe prose line (a space-joined run of words).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A one-line paragraph of lowercase words separated by single spaces.
    """
    words = draw(st.lists(_PROSE_WORD, min_size=1, max_size=8))
    return " ".join(words)


@composite
def st_world_spec(draw) -> WorldSpec:
    """Draw a self-consistent :class:`WorldSpec` for the docs generator.

    The drawn world always satisfies the generator's cross-source invariants:
    every hook id maps to exactly one category bucket, every steering entry has
    both a token count and size category, and module numbers are distinct. Sizes
    are kept small (<=6 hooks, <=8 steering files, <=5 modules) so
    materialization and a full Write_Mode run stay fast.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A :class:`WorldSpec` describing a valid generator source world.
    """
    hook_ids = draw(st.lists(st_hook_id(), min_size=0, max_size=6, unique=True))
    if hook_ids:
        flags = draw(
            st.lists(st.booleans(), min_size=len(hook_ids), max_size=len(hook_ids))
        )
        critical_ids = tuple(h for h, flag in zip(hook_ids, flags) if flag)
    else:
        critical_ids = ()

    steering_names = draw(
        st.lists(st_steering_filename(), min_size=0, max_size=8, unique=True)
    )
    steering = tuple(
        SteeringEntry(
            filename=name,
            token_count=draw(st.integers(min_value=0, max_value=100_000)),
            size_category=draw(st.sampled_from(SIZE_CATEGORIES)),
        )
        for name in steering_names
    )

    module_numbers = draw(
        st.lists(
            st.integers(min_value=1, max_value=99),
            min_size=0,
            max_size=5,
            unique=True,
        )
    )
    modules = tuple(
        ModuleEntry(number=number, name=draw(st_module_name()))
        for number in module_numbers
    )

    budget_total = draw(st.integers(min_value=0, max_value=1_000_000))
    prose = tuple(draw(st_prose_line()) for _ in range(5))

    return WorldSpec(
        hook_ids=tuple(hook_ids),
        critical_ids=critical_ids,
        steering=steering,
        modules=modules,
        budget_total=budget_total,
        prose=prose,
    )


# ---------------------------------------------------------------------------
# Source-file serializers (minimal, deterministic, YAML-safe)
# ---------------------------------------------------------------------------


def _yaml_double_quote(value: str) -> str:
    """Return ``value`` as a double-quoted YAML scalar with safe escaping.

    Args:
        value: The raw string to quote.

    Returns:
        A double-quoted YAML scalar safe to embed in a mapping value.
    """
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _hook_categories_yaml(spec: WorldSpec) -> str:
    """Render ``hook-categories.yaml`` placing each hook id in exactly one bucket.

    Critical hooks go under ``critical:``; every other discovered hook goes
    under ``modules: any:``. This guarantees the generator's cross-checks pass:
    every categorized id has a file and every file is categorized.

    Args:
        spec: The world description.

    Returns:
        The YAML text for ``hook-categories.yaml``.
    """
    critical = sorted(spec.critical_ids)
    critical_set = set(spec.critical_ids)
    regular = sorted(h for h in spec.hook_ids if h not in critical_set)

    # Hook ids are emitted as double-quoted scalars so YAML never coerces a
    # boolean-like id (``true``, ``no``, ``on``, ...) or a digit-like id into a
    # non-string type; the generator compares them against ``.kiro.hook``
    # filename stems, which are always strings.
    lines: list[str] = []
    if critical:
        lines.append("critical:")
        lines.extend(f"  - {_yaml_double_quote(hook_id)}" for hook_id in critical)
    else:
        lines.append("critical: []")

    if regular:
        lines.append("modules:")
        lines.append("  any:")
        lines.extend(f"    - {_yaml_double_quote(hook_id)}" for hook_id in regular)
    else:
        lines.append("modules: {}")

    return "\n".join(lines) + "\n"


def _steering_index_yaml(spec: WorldSpec) -> str:
    """Render ``steering-index.yaml`` with per-file metadata and a budget total.

    Args:
        spec: The world description.

    Returns:
        The YAML text for ``steering-index.yaml``.
    """
    lines: list[str] = []
    if spec.steering:
        lines.append("file_metadata:")
        for entry in spec.steering:
            lines.append(f"  {entry.filename}:")
            lines.append(f"    token_count: {entry.token_count}")
            lines.append(f"    size_category: {entry.size_category}")
    else:
        lines.append("file_metadata: {}")
    lines.append("budget:")
    lines.append(f"  total_tokens: {spec.budget_total}")
    return "\n".join(lines) + "\n"


def _module_deps_yaml(spec: WorldSpec) -> str:
    """Render ``module-dependencies.yaml`` as a ``modules`` map of number -> name.

    Args:
        spec: The world description.

    Returns:
        The YAML text for ``module-dependencies.yaml``.
    """
    lines: list[str] = []
    if spec.modules:
        lines.append("modules:")
        for module in spec.modules:
            lines.append(f"  {module.number}:")
            lines.append(f"    name: {_yaml_double_quote(module.name)}")
    else:
        lines.append("modules: {}")
    return "\n".join(lines) + "\n"


def build_power_md_skeleton(spec: WorldSpec) -> str:
    """Build a ``POWER.md`` skeleton with the four marker pairs and prose.

    The skeleton interleaves the drawn prose lines with empty marker-delimited
    regions for ``mcp-tools``, ``hooks``, ``steering-files``, and ``modules``.
    Every marker sits on its own line with blank lines around the surrounding
    headings and prose so the document stays CommonMark-clean before the
    generator fills the region bodies.

    Args:
        spec: The world description supplying the surrounding prose.

    Returns:
        The full ``POWER.md`` skeleton text.
    """
    prose = list(spec.prose) + ["fixture prose"] * 5
    return (
        "# Generated Power Docs Fixture\n"
        "\n"
        f"{prose[0]}\n"
        "\n"
        "## MCP Tools\n"
        "\n"
        f"{prose[1]}\n"
        "\n"
        "<!-- BEGIN GENERATED: mcp-tools -->\n"
        "<!-- END GENERATED: mcp-tools -->\n"
        "\n"
        "## Hooks\n"
        "\n"
        f"{prose[2]}\n"
        "\n"
        "<!-- BEGIN GENERATED: hooks -->\n"
        "<!-- END GENERATED: hooks -->\n"
        "\n"
        "## Steering Files\n"
        "\n"
        f"{prose[3]}\n"
        "\n"
        "<!-- BEGIN GENERATED: steering-files -->\n"
        "<!-- END GENERATED: steering-files -->\n"
        "\n"
        "## Modules\n"
        "\n"
        f"{prose[4]}\n"
        "\n"
        "<!-- BEGIN GENERATED: modules -->\n"
        "<!-- END GENERATED: modules -->\n"
    )


def materialize_world(spec: WorldSpec, base_dir: Path | str) -> MaterializedWorld:
    """Write ``spec`` to disk under ``base_dir`` and return the located sources.

    Creates the hooks directory (with one ``<id>.kiro.hook`` file per hook id
    and a consistent ``hook-categories.yaml``), the steering directory (with one
    ``.md`` file per steering entry and a ``steering-index.yaml``), the config
    directory (with ``module-dependencies.yaml``), and a ``POWER.md`` skeleton.
    The caller is responsible for providing a fresh ``base_dir`` per example
    (for example via :func:`tempfile.mkdtemp`) so worlds never overlap.

    Args:
        spec: The world description to write.
        base_dir: A directory to write the world into (used as the repo root).

    Returns:
        A :class:`MaterializedWorld` whose ``paths`` feed ``load_sources`` and
        the Write/Verify CLI.
    """
    import generate_power_docs as gpd

    world = Path(base_dir)

    hooks_dir = world / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for hook_id in spec.hook_ids:
        (hooks_dir / f"{hook_id}.kiro.hook").write_text("{}\n", encoding="utf-8")
    hook_categories = hooks_dir / "hook-categories.yaml"
    hook_categories.write_text(_hook_categories_yaml(spec), encoding="utf-8")

    steering_dir = world / "steering"
    steering_dir.mkdir(parents=True, exist_ok=True)
    for entry in spec.steering:
        (steering_dir / entry.filename).write_text(
            "# Steering fixture\n", encoding="utf-8"
        )
    steering_index = steering_dir / "steering-index.yaml"
    steering_index.write_text(_steering_index_yaml(spec), encoding="utf-8")

    config_dir = world / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    module_deps = config_dir / "module-dependencies.yaml"
    module_deps.write_text(_module_deps_yaml(spec), encoding="utf-8")

    power_md = world / "POWER.md"
    power_md.write_text(build_power_md_skeleton(spec), encoding="utf-8")

    paths = gpd.SourcePaths(
        power_md=power_md,
        hooks_dir=hooks_dir,
        hook_categories=hook_categories,
        steering_index=steering_index,
        module_deps=module_deps,
        repo_root=world,
    )
    return MaterializedWorld(paths=paths, spec=spec, world_dir=world)


def disable_commonmark(monkeypatch) -> None:
    """Monkeypatch the generator's CommonMark validation to a no-op.

    Property tests that are not specifically exercising CommonMark compliance
    use this so a Write_Mode run never depends on the ``markdownlint`` CLI being
    installed or on incidental table/prose lint rules. Property 11 deliberately
    does *not* call this so it validates the real output.

    Args:
        monkeypatch: The pytest ``monkeypatch`` fixture for the calling test.
    """
    import generate_power_docs as gpd

    monkeypatch.setattr(gpd, "validate_commonmark_text", lambda content: None)


@pytest.fixture()
def patch_commonmark(monkeypatch):
    """Fixture form of :func:`disable_commonmark` for example-based tests.

    Args:
        monkeypatch: The pytest ``monkeypatch`` fixture.
    """
    disable_commonmark(monkeypatch)
    return None
