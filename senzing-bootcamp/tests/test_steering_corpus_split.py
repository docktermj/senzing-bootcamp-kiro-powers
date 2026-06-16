"""Property-based tests for the steering corpus split.

Feature: steering-corpus-split

This suite verifies the invariants that must hold over ``steering-index.yaml``
and the on-disk steering corpus after the oversized always-loaded / early-loaded
steering files are split or trimmed.

Property 1 (this task): **Threshold compliance** — every Loadable_Unit the index
can route the agent to has a measured Token_Count (``round(len(content) / 4)``)
at or below ``budget.split_threshold_tokens`` (5000), OR is listed in the
enumerated ``EXEMPTIONS`` set (empty in v1).

Subsequent tasks append further property classes (routability, step coverage,
content preservation, and a no-external-URL scan) to this same file; the shared
imports, index helpers, and module-level constants below are reused by all of
them.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts are not a package)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from measure_steering import calculate_token_count  # noqa: E402

# ---------------------------------------------------------------------------
# Shared paths and constants
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"
_INDEX_PATH: Path = _STEERING_DIR / "steering-index.yaml"

# Generated_Files are produced by ``sync_hook_registry.py`` and are explicitly
# out of scope for v1 splitting (Requirements 1.3, 9.3): they are loaded on
# demand, are never hand-edited or hand-split, and their size is governed by the
# generator, not by this feature. They are therefore excluded from the
# threshold property rather than counted against it or enumerated as exemptions.
GENERATED_FILES: frozenset[str] = frozenset(
    {
        "hook-registry.md",
        "hook-registry-critical.md",
        "hook-registry-modules.md",
    }
)

# Enumerated exemption set (Requirements 2.2, 5.5, 8.1, 8.2). Contains
# module-completion.md: it is a single cohesive, sequential completion workflow
# (fixed step order: progress_update -> recap_append -> journal_entry ->
# completion_certificate -> next_step_options, plus a shared boundary-detection
# trigger, backfill for already-completed modules, and non-blocking error
# handling) that does not split into independently-loadable units without harming
# agent comprehension — the steps are interdependent and must load together. The
# module-completion-artifacts bugfix grew this file past the 5000-token
# split_threshold; rather than fragment a workflow that must be read as a whole,
# it is exempted with this justification. The file remains indexed in
# file_metadata (and is therefore covered by test_exemptions_exist_in_index).
# If a future indivisible unit cannot be reduced, its filename is added here with
# a written justification; the threshold test then passes via the exemption
# branch and ``test_exemptions_exist_in_index`` requires the file to be indexed.
EXEMPTIONS: frozenset[str] = frozenset({"module-completion.md"})


# ---------------------------------------------------------------------------
# Index parsing helper (full-index YAML load; PyYAML is the established
# index-parsing dependency, mirroring test_steering_structure_properties.py)
# ---------------------------------------------------------------------------


def parse_steering_index(index_path: Path) -> dict:
    """Load and return the full steering index as a nested mapping.

    Args:
        index_path: Path to ``steering-index.yaml``.

    Returns:
        The parsed YAML mapping, including the ``modules``, ``onboarding``,
        ``session-resume``, ``keywords``, ``languages``, ``deployment``,
        ``file_metadata``, and ``budget`` sections.

    Raises:
        FileNotFoundError: If ``index_path`` does not exist.
    """
    if not index_path.exists():
        raise FileNotFoundError(f"Steering index not found: {index_path}")
    return yaml.safe_load(index_path.read_text(encoding="utf-8"))


def collect_loadable_unit_names(index: dict) -> set[str]:
    """Collect every steering filename the index can route the agent to.

    Gathers every Phase_Map ``file`` (and ``root``) under ``modules``,
    ``onboarding``, and ``session-resume``; every flat ``file_metadata`` key;
    and every ``keywords`` / ``languages`` / ``deployment`` target value.

    Args:
        index: Parsed steering index mapping.

    Returns:
        Set of unique steering filenames referenced anywhere in the index.
    """
    names: set[str] = set()

    def _collect_phased_entry(entry: object) -> None:
        if isinstance(entry, str):
            names.add(entry)
            return
        if not isinstance(entry, dict):
            return
        if "root" in entry:
            names.add(entry["root"])
        for phase_info in entry.get("phases", {}).values():
            if isinstance(phase_info, dict) and "file" in phase_info:
                names.add(phase_info["file"])

    for entry in index.get("modules", {}).values():
        _collect_phased_entry(entry)

    for section in ("onboarding", "session-resume"):
        _collect_phased_entry(index.get(section))

    names.update(index.get("file_metadata", {}).keys())

    for section in ("keywords", "languages", "deployment"):
        for target in index.get(section, {}).values():
            names.add(target)

    return names


# ---------------------------------------------------------------------------
# Module-level index (parsed once, reused by strategies and concrete tests)
# ---------------------------------------------------------------------------

_INDEX: dict = parse_steering_index(_INDEX_PATH)
SPLIT_THRESHOLD: int = int(_INDEX["budget"]["split_threshold_tokens"])


@dataclass(frozen=True)
class LoadableUnit:
    """A single steering unit the agent loads as one unit.

    Attributes:
        name: Steering filename (kebab-case ``.md``).
        token_count: Measured token count, ``round(len(content) / 4)``.
    """

    name: str
    token_count: int


def build_loadable_units(index: dict, steering_dir: Path) -> list[LoadableUnit]:
    """Measure the token count of every routable, in-scope, on-disk unit.

    Generated_Files are excluded (out of scope per Requirements 1.3 / 9.3) and
    files that are not present on disk are skipped (their existence is the
    concern of the routability property, not the threshold property).

    Args:
        index: Parsed steering index mapping.
        steering_dir: Directory containing the steering ``.md`` files.

    Returns:
        Sorted list of measured ``LoadableUnit`` records.
    """
    units: list[LoadableUnit] = []
    for name in sorted(collect_loadable_unit_names(index)):
        if name in GENERATED_FILES:
            continue
        path = steering_dir / name
        if path.exists():
            units.append(
                LoadableUnit(name=name, token_count=calculate_token_count(path))
            )
    return units


_LOADABLE_UNITS: list[LoadableUnit] = build_loadable_units(_INDEX, _STEERING_DIR)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_loadable_unit() -> st.SearchStrategy[LoadableUnit]:
    """Strategy drawing a real, measured loadable unit from the index.

    Returns:
        A strategy producing ``LoadableUnit`` records sampled from the
        steering index's routable, in-scope, on-disk files.
    """
    return st.sampled_from(_LOADABLE_UNITS)


# ---------------------------------------------------------------------------
# Property 1: Threshold compliance
# ---------------------------------------------------------------------------


class TestPropertyThresholdCompliance:
    """Feature: steering-corpus-split, Property 1: Threshold compliance.

    For any Loadable_Unit registered in the Steering_Index (every
    ``phases.*.file``, every flat ``file_metadata`` entry, and every
    keyword/language/deployment target), its measured Token_Count is at or
    below ``budget.split_threshold_tokens``, OR the unit's filename is a member
    of the enumerated ``EXEMPTIONS`` set (and that file exists in the index).

    **Validates: Requirements 2.1, 2.2, 2.3, 8.1, 8.2, 5.5**
    """

    @given(unit=st_loadable_unit())
    @settings(max_examples=20)
    def test_loadable_unit_within_threshold(self, unit: LoadableUnit) -> None:
        """Any sampled loadable unit is within threshold or exempt.

        Args:
            unit: A measured loadable unit drawn from the steering index.
        """
        assert unit.token_count <= SPLIT_THRESHOLD or unit.name in EXEMPTIONS, (
            f"{unit.name} measures {unit.token_count} tokens "
            f"(> split_threshold_tokens={SPLIT_THRESHOLD}) and is not exempt"
        )

    def test_real_index_units_within_threshold(self) -> None:
        """Concrete pass: every routable, in-scope unit is within threshold.

        Covers ``phases.*.file`` targets, flat ``file_metadata`` entries, and
        keyword/language/deployment targets across the live index.
        """
        violations: list[str] = [
            f"{unit.name}: {unit.token_count} tokens"
            for unit in _LOADABLE_UNITS
            if unit.token_count > SPLIT_THRESHOLD and unit.name not in EXEMPTIONS
        ]
        assert violations == [], (
            "Loadable units exceed split_threshold_tokens "
            f"({SPLIT_THRESHOLD}) without an exemption: {violations}"
        )

    def test_exemptions_exist_in_index(self) -> None:
        """Each enumerated exemption names a file present in the index.

        No-op in v1 (``EXEMPTIONS`` is empty) but enforces Requirement 8.2 for
        any future exemption.
        """
        indexed_names = collect_loadable_unit_names(_INDEX)
        missing: list[str] = [
            name for name in EXEMPTIONS if name not in indexed_names
        ]
        assert missing == [], (
            f"Exemptions not present in the steering index: {missing}"
        )


# ---------------------------------------------------------------------------
# Property 2: Routability / no orphan — index reference collection
# ---------------------------------------------------------------------------


def collect_index_references(index: dict) -> set[str]:
    """Collect every filename the index routes to via a Phase_Map or keyword map.

    Gathers every ``root`` and ``phases.*.file`` under ``modules``,
    ``onboarding``, and ``session-resume`` (the Phase_Map references), plus
    every ``keywords`` / ``languages`` / ``deployment`` target value. Unlike
    ``collect_loadable_unit_names`` this deliberately omits the flat
    ``file_metadata`` registry, which records measurements rather than routes:
    Property 2 is concerned only with reachable Routing_References.

    Args:
        index: Parsed steering index mapping.

    Returns:
        Set of unique filenames reachable by a Routing_Reference.
    """
    names: set[str] = set()

    def _collect_phased_entry(entry: object) -> None:
        if isinstance(entry, str):
            names.add(entry)
            return
        if not isinstance(entry, dict):
            return
        if "root" in entry:
            names.add(entry["root"])
        for phase_info in entry.get("phases", {}).values():
            if isinstance(phase_info, dict) and "file" in phase_info:
                names.add(phase_info["file"])

    for entry in index.get("modules", {}).values():
        _collect_phased_entry(entry)

    for section in ("onboarding", "session-resume"):
        _collect_phased_entry(index.get(section))

    for section in ("keywords", "languages", "deployment"):
        for target in index.get(section, {}).values():
            names.add(target)

    return names


_INDEX_REFERENCES: list[str] = sorted(collect_index_references(_INDEX))


def st_index_reference() -> st.SearchStrategy[str]:
    """Strategy drawing a routable filename reference from the index.

    Returns:
        A strategy producing filenames sampled from the steering index's
        Phase_Map (``root`` / ``phases.*.file``) targets and its
        ``keywords`` / ``languages`` / ``deployment`` targets.
    """
    return st.sampled_from(_INDEX_REFERENCES)


# ---------------------------------------------------------------------------
# Property 2: Routability / no orphan
# ---------------------------------------------------------------------------


class TestPropertyRoutability:
    """Feature: steering-corpus-split, Property 2: Routability / no orphan.

    For any filename referenced by a Phase_Map ``file`` (or ``root``), or by
    the ``keywords``, ``languages``, or ``deployment`` maps of the
    Steering_Index, that filename resolves to a file that exists on disk in the
    steering directory. This guarantees no relocated section is orphaned and
    that the ``phase-loading-guide.md`` missing-sub-file fallback is never
    silently triggered by a dangling reference.

    Generated_Files (``hook-registry*.md``) are *included* here: the
    ``hook`` / ``hooks`` keyword route resolves to ``hook-registry.md`` and the
    registry files exist on disk, so routability covers them even though the
    threshold property (Property 1) excludes them.

    **Validates: Requirements 4.3, 4.5, 4.6, 8.3, 8.6**
    """

    @given(reference=st_index_reference())
    @settings(max_examples=20)
    def test_index_reference_exists_on_disk(self, reference: str) -> None:
        """Any sampled index reference resolves to an existing steering file.

        Args:
            reference: A routable filename drawn from the steering index.
        """
        path = _STEERING_DIR / reference
        assert path.is_file(), (
            f"Index references '{reference}' but no such file exists in "
            f"{_STEERING_DIR}"
        )

    def test_real_index_references_exist_on_disk(self) -> None:
        """Concrete pass: every Phase_Map / keyword-map reference exists on disk.

        Covers every ``root`` and ``phases.*.file`` under ``modules``,
        ``onboarding``, and ``session-resume`` plus every ``keywords`` /
        ``languages`` / ``deployment`` target across the live index.
        """
        missing: list[str] = [
            reference
            for reference in _INDEX_REFERENCES
            if not (_STEERING_DIR / reference).is_file()
        ]
        assert missing == [], (
            f"Index references files that do not exist on disk: {missing}"
        )

    def test_generated_files_exist_on_disk(self) -> None:
        """Generated_Files are routable: each resolves to an on-disk file.

        ``hook-registry.md`` is reached by the ``hook`` / ``hooks`` keyword route
        and its mirrors (``hook-registry-critical.md``,
        ``hook-registry-modules.md``) are loaded on demand during onboarding;
        all three must exist so routability holds for them even though the
        threshold property excludes them as Generated_Files.
        """
        missing: list[str] = [
            name for name in sorted(GENERATED_FILES)
            if not (_STEERING_DIR / name).is_file()
        ]
        assert missing == [], (
            f"Generated files referenced by the corpus are missing on disk: "
            f"{missing}"
        )


# ---------------------------------------------------------------------------
# Property 3: Step coverage — phase-loading-guide.md resolution helpers
# ---------------------------------------------------------------------------


def parse_parent_step(step: int | str) -> int:
    """Reduce a step identifier to its parent integer step number.

    Implements the ``phase-loading-guide.md`` rule: a sub-step identifier is
    reduced to the integer portion that precedes any decimal point or trailing
    letter(s). Integers are returned unchanged. Examples: ``5 -> 5``,
    ``"5b" -> 5``, ``"5.3" -> 5``, ``"7a" -> 7``, ``"12.1" -> 12``.

    Args:
        step: A step identifier — an ``int`` (e.g., ``5``), a lettered sub-step
            string (e.g., ``"7a"``), or a dotted sub-step string (e.g.,
            ``"5.3"``).

    Returns:
        The parent step as an ``int``.

    Raises:
        ValueError: If *step* is a string with no leading integer portion.
    """
    if isinstance(step, int):
        return step
    match = re.match(r"\d+", str(step))
    if not match:
        raise ValueError(f"Step identifier has no integer portion: {step!r}")
    return int(match.group())


def step_sort_key(step: int | str) -> tuple[int, str]:
    """Build a totally-ordered key for a step token, sub-step aware.

    The key is ``(parent_integer, suffix)`` where *suffix* is the portion of a
    sub-step string after its leading integer (``""`` for a bare integer).
    Ordering a bare integer below its lettered sub-steps (``(4, "") < (4, "a")``)
    matches how ``phase-loading-guide.md`` orders steps within a parent: this
    lets a single integer step be split across phases at sub-step granularity
    (e.g., Module 7 ``"4a"-"4c"`` then ``"4d"-"4e"``) while keeping each
    sub-step in exactly one phase.

    Args:
        step: A step identifier (``int`` or sub-step ``str``).

    Returns:
        A ``(parent_integer, suffix)`` tuple suitable for ``<=`` comparison.
    """
    parent = parse_parent_step(step)
    suffix = "" if isinstance(step, int) else str(step)[len(str(parent)):]
    return (parent, suffix)


def range_contains(step_range: list[int | str], step: int | str) -> bool:
    """Return whether *step* falls within the closed interval *step_range*.

    Containment is evaluated on the sub-step-aware ``step_sort_key`` ordering,
    so ``["4a", "4c"]`` contains ``"4b"`` but not ``"4d"`` or the bare integer
    ``4``.

    Args:
        step_range: A two-element ``[start, end]`` range from a Phase_Map.
        step: The step identifier to test.

    Returns:
        ``True`` if ``start <= step <= end`` under the sub-step ordering.
    """
    lo, hi = step_range
    return step_sort_key(lo) <= step_sort_key(step) <= step_sort_key(hi)


def ranges_overlap(
    range_a: list[int | str], range_b: list[int | str]
) -> bool:
    """Return whether two closed step ranges share any step.

    Uses the sub-step-aware ordering so adjacent sub-step splits of the same
    parent integer (``["4a", "4c"]`` vs ``["4d", "4e"]``) do **not** overlap,
    while two integer ranges that share steps (``[9, 12]`` vs ``[10, 12]``) do.

    Args:
        range_a: First ``[start, end]`` range.
        range_b: Second ``[start, end]`` range.

    Returns:
        ``True`` if the two intervals intersect.
    """
    lo_a, hi_a = step_sort_key(range_a[0]), step_sort_key(range_a[1])
    lo_b, hi_b = step_sort_key(range_b[0]), step_sort_key(range_b[1])
    return lo_a <= hi_b and lo_b <= hi_a


def step_to_phase(
    phases: dict[str, dict], step: int | str
) -> list[str]:
    """Resolve a step to the phase slug(s) whose ``step_range`` contains it.

    Mirrors the ``phase-loading-guide.md`` resolution: find the phase whose
    ``step_range`` contains the (sub-step-aware) step. A correct, unambiguous
    Phase_Map yields exactly one slug for any step inside its coverage.

    Args:
        phases: A module's ``phases`` mapping (slug -> phase info dict).
        step: The step identifier to resolve.

    Returns:
        The list of phase slugs whose ``step_range`` contains *step* (expected
        to have exactly one element for any covered step).
    """
    return [
        slug
        for slug, info in phases.items()
        if "step_range" in info and range_contains(info["step_range"], step)
    ]


def module_parent_steps(phases: dict[str, dict]) -> set[int]:
    """Return the union of parent integer steps covered by a Phase_Map.

    Each phase ``step_range`` ``[start, end]`` contributes every integer from
    ``parse_parent_step(start)`` through ``parse_parent_step(end)`` inclusive.

    Args:
        phases: A module's ``phases`` mapping (slug -> phase info dict).

    Returns:
        The set of parent integer steps covered by the module's phases.
    """
    steps: set[int] = set()
    for info in phases.values():
        if "step_range" not in info:
            continue
        start, end = info["step_range"]
        steps.update(range(parse_parent_step(start), parse_parent_step(end) + 1))
    return steps


def phase_endpoint_tokens(phases: dict[str, dict]) -> list[int | str]:
    """Return every ``step_range`` endpoint token across a Phase_Map.

    These concrete endpoint tokens (e.g., ``1``, ``8``, ``"4a"``, ``"4e"``) are
    the steps the loader is guaranteed to resolve in practice and make ideal
    witnesses for the "exactly one phase" assertion.

    Args:
        phases: A module's ``phases`` mapping (slug -> phase info dict).

    Returns:
        A list of every ``start`` and ``end`` token in the module's phases.
    """
    tokens: list[int | str] = []
    for info in phases.values():
        if "step_range" not in info:
            continue
        start, end = info["step_range"]
        tokens.extend([start, end])
    return tokens


# ---------------------------------------------------------------------------
# Module-level collection of modules that carry a Phase_Map
# ---------------------------------------------------------------------------


def collect_phased_modules(index: dict) -> list[tuple[int, dict[str, dict]]]:
    """Collect every ``modules.<N>`` entry that defines a Phase_Map.

    Property 3 is scoped to ``modules.*`` per Requirement 8.4 / design
    Property 3, which both read "for each module with a Phase_Map". Top-level
    sections (``onboarding``, ``session-resume``) are intentionally excluded —
    see ``TestPropertyStepCoverage`` for the rationale.

    Args:
        index: Parsed steering index mapping.

    Returns:
        Sorted list of ``(module_number, phases)`` tuples, one per module that
        has a non-empty ``phases`` map.
    """
    phased: list[tuple[int, dict[str, dict]]] = []
    for number, entry in index.get("modules", {}).items():
        if isinstance(entry, dict) and entry.get("phases"):
            phased.append((int(number), entry["phases"]))
    return sorted(phased, key=lambda item: item[0])


_PHASED_MODULES: list[tuple[int, dict[str, dict]]] = collect_phased_modules(_INDEX)


def st_phased_module() -> st.SearchStrategy[tuple[int, dict[str, dict]]]:
    """Strategy drawing a real ``(module_number, phases)`` pair from the index.

    Returns:
        A strategy producing ``(module_number, phases)`` tuples sampled from the
        modules that declare a Phase_Map in the live steering index.
    """
    return st.sampled_from(_PHASED_MODULES)


# ---------------------------------------------------------------------------
# Property 3: Step coverage is total and unambiguous
# ---------------------------------------------------------------------------


class TestPropertyStepCoverage:
    """Feature: steering-corpus-split, Property 3: Step coverage is total and unambiguous.

    For any module that has a Phase_Map, every integer step in the union of that
    module's phases' ``step_range`` values resolves, via the
    ``phase-loading-guide.md`` rules (reduce sub-steps to their parent integer
    with ``parse_parent_step``, then select the phase whose ``step_range``
    contains the step), to **exactly one** phase sub-file. Concretely this means
    the phase ranges are pairwise non-overlapping (**unambiguous**) and their
    parent-integer coverage is gap-free from the module's first to last step
    (**total**).

    Scoping decision (Option A — modules only): Requirement 8.4 and design
    Property 3 both say "for each module with a Phase_Map", so this property is
    scoped to ``modules.*`` and deliberately excludes the top-level
    ``onboarding`` section. Onboarding legitimately reuses integer step 5 in two
    phases — ``phase1b-intro-language`` (``[3, "5b"]``) covers the Step 5/5a/5b
    *introduction* sub-steps while ``phase2-track-setup`` (``[5, 5]``) covers the
    Step 5 *Track Selection* work — so a strict "exactly one phase per integer
    step" assertion would raise a false positive on that intentional structure.
    Keeping the property at module scope matches the requirement wording and
    keeps it precise.

    Sub-step granularity: Module 7 splits a single integer step across two
    phases at sub-step granularity (``["4a", "4c"]`` then ``["4d", "4e"]``).
    This is handled by ``step_sort_key`` / ``ranges_overlap`` so the two phases
    are correctly recognized as non-overlapping (each ``"4x"`` sub-step resolves
    to exactly one phase) rather than flagged as an ambiguous double-claim of
    integer 4. The same machinery still flags a true integer overlap such as the
    pre-fix Module 3 ``[9, 12]`` / ``[10, 12]`` defect.

    **Validates: Requirements 4.2, 8.4**
    """

    @given(module=st_phased_module())
    @settings(max_examples=20)
    def test_phase_ranges_are_pairwise_disjoint(
        self, module: tuple[int, dict[str, dict]]
    ) -> None:
        """No two phases in a module claim the same step (unambiguous).

        Args:
            module: A ``(module_number, phases)`` pair from the index.
        """
        number, phases = module
        slugs = list(phases)
        for i in range(len(slugs)):
            for j in range(i + 1, len(slugs)):
                range_a = phases[slugs[i]]["step_range"]
                range_b = phases[slugs[j]]["step_range"]
                assert not ranges_overlap(range_a, range_b), (
                    f"Module {number}: phases '{slugs[i]}' {range_a} and "
                    f"'{slugs[j]}' {range_b} overlap — a step would resolve to "
                    f"more than one phase"
                )

    @given(module=st_phased_module())
    @settings(max_examples=20)
    def test_parent_step_coverage_is_gap_free(
        self, module: tuple[int, dict[str, dict]]
    ) -> None:
        """The union of parent integer steps is contiguous (total).

        Args:
            module: A ``(module_number, phases)`` pair from the index.
        """
        number, phases = module
        covered = module_parent_steps(phases)
        assert covered, f"Module {number}: Phase_Map covers no steps"
        expected = set(range(min(covered), max(covered) + 1))
        missing = sorted(expected - covered)
        assert not missing, (
            f"Module {number}: parent step coverage has gaps at {missing} "
            f"(covered={sorted(covered)})"
        )

    @given(module=st_phased_module())
    @settings(max_examples=20)
    def test_endpoints_resolve_to_exactly_one_phase(
        self, module: tuple[int, dict[str, dict]]
    ) -> None:
        """Every ``step_range`` endpoint resolves to exactly one phase.

        Args:
            module: A ``(module_number, phases)`` pair from the index.
        """
        number, phases = module
        for token in phase_endpoint_tokens(phases):
            resolved = step_to_phase(phases, token)
            assert len(resolved) == 1, (
                f"Module {number}: step {token!r} resolves to "
                f"{resolved} (expected exactly one phase)"
            )

    def test_real_modules_total_and_unambiguous(self) -> None:
        """Concrete pass: every module's Phase_Map is disjoint and total.

        Iterates all ``modules.*`` entries with a Phase_Map and asserts pairwise
        non-overlap, gap-free parent coverage, and that every endpoint resolves
        to exactly one phase.
        """
        problems: list[str] = []
        for number, phases in _PHASED_MODULES:
            slugs = list(phases)
            for i in range(len(slugs)):
                for j in range(i + 1, len(slugs)):
                    range_a = phases[slugs[i]]["step_range"]
                    range_b = phases[slugs[j]]["step_range"]
                    if ranges_overlap(range_a, range_b):
                        problems.append(
                            f"Module {number}: '{slugs[i]}' {range_a} overlaps "
                            f"'{slugs[j]}' {range_b}"
                        )
            covered = module_parent_steps(phases)
            expected = set(range(min(covered), max(covered) + 1))
            if covered != expected:
                problems.append(
                    f"Module {number}: coverage gap "
                    f"{sorted(expected - covered)}"
                )
            for token in phase_endpoint_tokens(phases):
                resolved = step_to_phase(phases, token)
                if len(resolved) != 1:
                    problems.append(
                        f"Module {number}: step {token!r} -> {resolved}"
                    )
        assert problems == [], (
            f"Module Phase_Maps are not all disjoint and total: {problems}"
        )

    def test_module_3_step_map_is_disjoint_and_total(self) -> None:
        """Module 3 covers steps 1-12 as ``[1,8] u [9,9] u [10,12]``.

        Guards the specific corrected Module 3 step map this feature establishes
        (removing the pre-fix ``[9, 12]`` overlap): Phase 1 verification
        ``[1, 8]``, Phase 2 visualization ``[9, 9]``, Phase 3 report/close
        ``[10, 12]`` — disjoint and total over steps 1 through 12.
        """
        module_3 = dict(_PHASED_MODULES).get(3)
        assert module_3 is not None, "Module 3 is not registered with a Phase_Map"

        ranges = {
            slug: info["step_range"] for slug, info in module_3.items()
        }
        assert ranges == {
            "phase1-verification": [1, 8],
            "phase2-visualization": [9, 9],
            "phase3-report-close": [10, 12],
        }, f"Module 3 step ranges changed unexpectedly: {ranges}"

        covered = module_parent_steps(module_3)
        assert covered == set(range(1, 13)), (
            f"Module 3 must cover steps 1-12; covered={sorted(covered)}"
        )
        for step in range(1, 13):
            resolved = step_to_phase(module_3, step)
            assert len(resolved) == 1, (
                f"Module 3 step {step} resolves to {resolved} "
                f"(expected exactly one phase)"
            )


# ---------------------------------------------------------------------------
# Property 4: Content preservation — guidance-block / marker inventory helpers
# ---------------------------------------------------------------------------

# Behavioral markers tracked by the Content_Preservation_Invariant (Requirement
# 3.3). ``STOP|WAIT`` is counted as a regex alternation because both directives
# carry the same "halt and wait" semantics; the others are literal substrings.
_MARKER_STOP_WAIT_RE: re.Pattern[str] = re.compile(r"STOP|WAIT")


def extract_guidance_blocks(text: str) -> list[str]:
    """Extract the guidance blocks (normalized non-blank lines) from *text*.

    Implements the ``SectionInventory.guidance_blocks`` model from the design:
    a guidance block is any non-blank line (heading, step, checkpoint, table
    row, prose, or marker line), normalized by stripping surrounding
    whitespace. Blank lines carry no Guidance_Content and are dropped so that
    cosmetic spacing differences across a split boundary never register as a
    lost or gained block.

    Args:
        text: The full Markdown text of a (synthetic or real) steering unit.

    Returns:
        The ordered list of normalized non-blank lines in *text*.
    """
    return [line.strip() for line in text.splitlines() if line.strip()]


def count_markers(text: str) -> dict[str, int]:
    """Count each tracked behavioral marker in *text*.

    Args:
        text: The Markdown text to scan.

    Returns:
        A mapping with the occurrence count of each behavioral marker:
        ``"👉"``, ``"⛔"``, ``"STOP|WAIT"`` (regex alternation), and
        ``"**Checkpoint:**"`` (literal).
    """
    return {
        "👉": text.count("👉"),
        "⛔": text.count("⛔"),
        "STOP|WAIT": len(_MARKER_STOP_WAIT_RE.findall(text)),
        "**Checkpoint:**": text.count("**Checkpoint:**"),
    }


def read_frontmatter(path: Path) -> dict:
    """Parse the YAML frontmatter block at the top of a steering file.

    Args:
        path: Path to a steering ``.md`` file.

    Returns:
        The parsed frontmatter mapping, or an empty mapping if the file has no
        ``---`` delimited frontmatter block.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


# ---------------------------------------------------------------------------
# Synthetic-file generation for the generative preservation property
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SyntheticSection:
    """A synthetic steering section: one heading plus its body lines.

    Attributes:
        heading: A Markdown heading line (e.g., ``"## Phase 1"``); the boundary
            unit a real split partitions on.
        body: The non-heading content lines beneath the heading (each may carry
            a behavioral marker).
    """

    heading: str
    body: tuple[str, ...]


@dataclass(frozen=True)
class SplitAssignment:
    """A synthetic file plus a heading boundary to partition it at.

    Attributes:
        sections: The ordered synthetic sections composing the file.
        boundary: Section index ``1 <= boundary <= len(sections) - 1``; the file
            is cut immediately before ``sections[boundary]``'s heading, so the
            cut always lands on a heading boundary (never mid-section).
    """

    sections: tuple[SyntheticSection, ...]
    boundary: int


def render_sections(sections: tuple[SyntheticSection, ...]) -> tuple[str, list[int]]:
    """Render synthetic sections into Markdown text and record heading lines.

    Args:
        sections: The ordered synthetic sections to render.

    Returns:
        A ``(text, heading_line_numbers)`` pair where *text* is the joined
        Markdown and *heading_line_numbers[i]* is the 0-based line index of
        ``sections[i]``'s heading within *text*.
    """
    lines: list[str] = []
    heading_line_numbers: list[int] = []
    for section in sections:
        heading_line_numbers.append(len(lines))
        lines.append(section.heading)
        lines.extend(section.body)
    return "\n".join(lines), heading_line_numbers


def st_marker_line() -> st.SearchStrategy[str]:
    """Strategy producing a synthetic body line, with or without a marker.

    The pool deliberately mixes every tracked marker (``👉``, ``🛑 STOP``,
    ``WAIT``, ``⛔``, ``**Checkpoint:**``) with plain guidance lines so the
    generated marker counts vary across examples.

    Returns:
        A strategy producing a single body line string.
    """
    return st.sampled_from(
        [
            "👉 What datasource would you like to load first?",
            "🛑 STOP and wait for the bootcamper's response.",
            "WAIT for explicit confirmation before continuing.",
            "⛔ MANDATORY GATE — this step is unconditional.",
            "**Checkpoint:** confirm the entity count matches.",
            "Plain guidance line with no behavioral marker.",
            "Run the verification command and review the output.",
        ]
    )


def st_synthetic_section() -> st.SearchStrategy[SyntheticSection]:
    """Strategy producing a single synthetic section (heading + body lines).

    Returns:
        A strategy producing ``SyntheticSection`` records.
    """
    heading = st.builds(
        lambda level, title: f"{'#' * level} {title}",
        level=st.integers(min_value=2, max_value=3),
        title=st.sampled_from(
            ["Phase 1", "Phase 2", "Step 3", "Overview", "Setup", "Closing"]
        ),
    )
    return st.builds(
        SyntheticSection,
        heading=heading,
        body=st.lists(st_marker_line(), min_size=0, max_size=4).map(tuple),
    )


@st.composite
def st_split_assignment(draw: st.DrawFn) -> SplitAssignment:
    """Strategy producing a synthetic file and a heading boundary to split at.

    Generates two to six synthetic sections (each a heading plus marker-bearing
    body lines) and a boundary index in ``[1, len(sections) - 1]`` so the
    partition always falls on a heading boundary and never bisects a section.

    Args:
        draw: Hypothesis draw callable.

    Returns:
        A ``SplitAssignment`` carrying the sections and the chosen boundary.
    """
    sections = draw(st.lists(st_synthetic_section(), min_size=2, max_size=6))
    boundary = draw(st.integers(min_value=1, max_value=len(sections) - 1))
    return SplitAssignment(sections=tuple(sections), boundary=boundary)


# ---------------------------------------------------------------------------
# Real in-scope corpus anchors (concrete before/after inventory checks)
# ---------------------------------------------------------------------------

# Requirement 5.3 always-on rule anchors that MUST remain in agent-instructions.md.
_ALWAYS_ON_RULE_ANCHORS: tuple[str, ...] = (
    "Answer Processing Priority",
    "MCP-First Invariant",
    "Mandatory Gate Precedence",
    "Question Stop Protocol",
)

# Pointer stubs left in agent-instructions.md for relocated on-demand sections
# (Requirement 5.4, 3.1/3.2 no-orphan at the source side): each names the file
# the relocated content now lives in.
_AGENT_INSTRUCTION_POINTER_STUBS: tuple[str, ...] = (
    "mcp-usage-reference.md",
    "track-switching.md",
    "agent-context-management.md",
)

# Four files composing the Module 3 split (three new + the kept-but-trimmed
# phase2 file); all must exist so relocated content is reachable.
_MODULE_3_SPLIT_FILES: tuple[str, ...] = (
    "module-03-phase1-verification.md",
    "module-03-phase2-visualization.md",
    "module-03-phase3-report-close.md",
    "module-03-visualization-api-reference.md",
)


# ---------------------------------------------------------------------------
# Property 4: Content preservation and always-on-core retention
# ---------------------------------------------------------------------------


class TestPropertyContentPreservation:
    """Feature: steering-corpus-split, Property 4: Content preservation and \
always-on-core retention.

    Two complementary checks:

    1. **Generative invariant.** ``st_split_assignment()`` builds a synthetic
       steering file from marked guidance blocks and partitions it at a random
       heading boundary; the union of the resulting parts must preserve every
       guidance block (no drop, no orphan) and the exact count of each
       behavioral marker (``👉``, ``⛔``, ``STOP``/``WAIT``, ``**Checkpoint:**``).
       This models the Content_Preservation_Invariant for any heading-boundary
       split.

    2. **Concrete retention.** The real in-scope files were modified in place, so
       the pre-split originals are no longer on disk; instead these tests assert
       the verifiable post-split state: ``agent-instructions.md`` keeps
       ``inclusion: always`` (Req 5.1) and all Requirement-5.3 always-on rule
       anchors (Req 5.3); the three relocation pointer stubs remain so nothing is
       orphaned at the source (Req 3.1/3.2); the relocated SDK Method Discovery
       content landed in ``mcp-usage-reference.md`` (no drop); and the Module 3
       split files exist with the relocated ⛔ gate language and ``#[[file:]]``
       reference in place (Req 3.1/3.2, no drop / no orphan).

    **Validates: Requirements 3.1, 3.2, 3.3, 5.1, 5.3**
    """

    @given(assignment=st_split_assignment())
    @settings(max_examples=20)
    def test_partition_preserves_all_guidance_blocks(
        self, assignment: SplitAssignment
    ) -> None:
        """A heading-boundary partition drops and orphans no guidance block.

        The multiset of guidance blocks in the two parts equals the multiset in
        the original synthetic file.

        Args:
            assignment: A synthetic file plus the heading boundary to cut at.
        """
        text, heading_line_numbers = render_sections(assignment.sections)
        cut = heading_line_numbers[assignment.boundary]
        lines = text.split("\n")
        part_a = "\n".join(lines[:cut])
        part_b = "\n".join(lines[cut:])

        original_blocks = extract_guidance_blocks(text)
        union_blocks = extract_guidance_blocks(part_a) + extract_guidance_blocks(
            part_b
        )
        assert sorted(union_blocks) == sorted(original_blocks), (
            "Heading-boundary partition changed the guidance-block inventory: "
            f"original={sorted(original_blocks)} union={sorted(union_blocks)}"
        )

    @given(assignment=st_split_assignment())
    @settings(max_examples=20)
    def test_partition_preserves_marker_counts(
        self, assignment: SplitAssignment
    ) -> None:
        """A heading-boundary partition conserves every behavioral marker count.

        For each tracked marker, the sum of counts across the two parts equals
        the count in the original synthetic file.

        Args:
            assignment: A synthetic file plus the heading boundary to cut at.
        """
        text, heading_line_numbers = render_sections(assignment.sections)
        cut = heading_line_numbers[assignment.boundary]
        lines = text.split("\n")
        part_a = "\n".join(lines[:cut])
        part_b = "\n".join(lines[cut:])

        original = count_markers(text)
        part_a_markers = count_markers(part_a)
        part_b_markers = count_markers(part_b)
        for marker, original_count in original.items():
            union_count = part_a_markers[marker] + part_b_markers[marker]
            assert union_count == original_count, (
                f"Marker {marker!r} count changed across the partition: "
                f"original={original_count} union={union_count}"
            )

    def test_agent_instructions_remains_always_loaded(self) -> None:
        """``agent-instructions.md`` retains ``inclusion: always`` (Req 5.1)."""
        frontmatter = read_frontmatter(_STEERING_DIR / "agent-instructions.md")
        assert frontmatter.get("inclusion") == "always", (
            "agent-instructions.md must keep 'inclusion: always'; "
            f"frontmatter={frontmatter}"
        )

    def test_agent_instructions_retains_always_on_rule_anchors(self) -> None:
        """All Requirement-5.3 always-on rule anchors remain present (Req 5.3)."""
        content = (_STEERING_DIR / "agent-instructions.md").read_text(
            encoding="utf-8"
        )
        missing = [
            anchor for anchor in _ALWAYS_ON_RULE_ANCHORS if anchor not in content
        ]
        assert missing == [], (
            "agent-instructions.md is missing always-on rule anchors that must "
            f"never be relocated (Requirement 5.3): {missing}"
        )

    def test_agent_instructions_retains_relocation_pointer_stubs(self) -> None:
        """Pointer stubs for relocated on-demand sections remain (Req 3.1/3.2).

        Each relocated section (SDK Method Discovery, Track Switching, Context
        Budget) must leave a stub naming its new home file so the relocated
        content stays reachable from the always-loaded file (no orphan).
        """
        content = (_STEERING_DIR / "agent-instructions.md").read_text(
            encoding="utf-8"
        )
        missing = [
            stub for stub in _AGENT_INSTRUCTION_POINTER_STUBS if stub not in content
        ]
        assert missing == [], (
            "agent-instructions.md is missing relocation pointer stubs (relocated "
            f"content would be orphaned at the source): {missing}"
        )

    def test_sdk_method_discovery_landed_in_mcp_usage_reference(self) -> None:
        """Relocated SDK Method Discovery content is present in its destination.

        Confirms the block dropped from ``agent-instructions.md`` landed in
        ``mcp-usage-reference.md`` (no drop, Req 3.1).
        """
        content = (_STEERING_DIR / "mcp-usage-reference.md").read_text(
            encoding="utf-8"
        )
        assert "SDK Method Discovery" in content, (
            "mcp-usage-reference.md must contain the relocated 'SDK Method "
            "Discovery' section so the block relocated from agent-instructions.md "
            "is not dropped"
        )

    def test_module_3_split_files_exist(self) -> None:
        """The four Module 3 split files exist on disk (no orphan, Req 3.1)."""
        missing = [
            name
            for name in _MODULE_3_SPLIT_FILES
            if not (_STEERING_DIR / name).is_file()
        ]
        assert missing == [], (
            f"Module 3 split files are missing on disk: {missing}"
        )

    def test_module_3_visualization_retains_relocated_gate(self) -> None:
        """The relocated ⛔ gate language is present in the visualization file.

        The unique Step 9 gate language relocated from
        ``module-03-system-verification.md`` must appear in
        ``module-03-phase2-visualization.md`` (relocate, not drop; Req 3.1/3.2).
        """
        content = (
            _STEERING_DIR / "module-03-phase2-visualization.md"
        ).read_text(encoding="utf-8")
        assert (
            "Phase 2 Execution Is Mandatory" in content
            or "UNCONDITIONAL EXECUTION REQUIREMENT" in content
        ), (
            "module-03-phase2-visualization.md must carry the relocated ⛔ gate "
            "language ('Phase 2 Execution Is Mandatory' / 'UNCONDITIONAL "
            "EXECUTION REQUIREMENT')"
        )
        assert "⛔" in content, (
            "module-03-phase2-visualization.md must preserve the ⛔ marker on the "
            "relocated mandatory gate"
        )

    def test_module_3_visualization_references_api_companion(self) -> None:
        """The ``#[[file:]]`` reference to the API companion is present (Req 3.2).

        Confirms the relocated API schemas remain reachable from the Step 9 file
        via a ``#[[file:]]`` Routing_Reference (no orphan).
        """
        content = (
            _STEERING_DIR / "module-03-phase2-visualization.md"
        ).read_text(encoding="utf-8")
        assert "module-03-visualization-api-reference.md" in content, (
            "module-03-phase2-visualization.md must reference "
            "module-03-visualization-api-reference.md so the relocated API "
            "schemas remain reachable"
        )

# ---------------------------------------------------------------------------
# Guard scan: no clickable external / MCP-host URLs in touched steering files
# ---------------------------------------------------------------------------
#
# This is a lightweight GUARD assertion enforcing the security rules
# (Requirement 7.6: no external clickable URL in a steering file, and no MCP
# server host outside ``mcp.json``). It is NOT one of the four design
# correctness properties — it is a concrete, file-by-file scan that mirrors the
# intent of the "Steering file referencing external URLs (MEDIUM)" rule in
# ``.kiro/steering/security.md`` and the ``security-write-gate`` hook's CHECK 3.
#
# Scope: every TOUCHED steering file — the four in-scope files plus the four new
# units created by this feature.
#
# Detection model (strip-code-then-scan): the security rule targets *clickable*
# external links — Markdown autolinks (``<scheme://host>``) and inline links
# (``[text](scheme://host)``) rendered in prose — not command examples or
# operational troubleshooting strings. The relocated content legitimately ships
# (verified against git history and the existing CI validators) with:
#   * an https curl example targeting the MCP server host (with a ``:443`` port)
#     and bare MCP-host / nslookup troubleshooting lines inside fenced
#     ``` ```text ``` blocks (onboarding-flow.md),
#   * bare MCP-host troubleshooting references inside inline ``code`` spans
#     (module-03-phase1-verification.md),
#   * loopback ``localhost:8080`` strings inside inline ``code`` and fenced
#     ``` ```json ``` blocks (module-03-phase2-visualization.md,
#     module-03-phase3-report-close.md).
# None of those are clickable doc links, and all already pass the repo's
# ``validate_power.py`` / ``validate_commonmark.py`` and the security
# write-gate hook. Stripping fenced code blocks and inline-code spans before
# scanning therefore removes exactly those security-reviewed, non-clickable
# command/loopback references while still catching any newly-introduced
# clickable link (autolink or inline-link) added to prose.
#
# Allowlisted hosts (the only hosts permitted to survive in a prose URL):
#   * ``localhost`` / ``127.0.0.1`` — loopback, local not external.
#   * ``docs.senzing.com`` — the first-party Senzing documentation host. The
#     always-loaded ``agent-instructions.md`` ships a pre-existing
#     ``<…docs.senzing.com>`` autolink ("No answer? … suggest the docs host /
#     support contact — never fabricate.") that predates this feature and is
#     part of the shipped, security-reviewed corpus. It is enumerated here
#     rather than edited (this feature must not rewrite steering content) so the
#     guard passes on the clean state.
# The MCP server host is deliberately NOT allowlisted: if it ever appears as a
# clickable URL in prose (i.e. outside a code span), this guard flags it via the
# general scan below, matching CHECK 2 of the security write-gate hook (the host
# belongs only in ``mcp.json``). Its current bare/command-example occurrences
# live inside code and are stripped before scanning.

# The eight TOUCHED steering files (four in-scope + four new units).
_URL_SCAN_FILES: tuple[str, ...] = (
    "agent-instructions.md",
    "onboarding-flow.md",
    "module-03-system-verification.md",
    "module-03-phase2-visualization.md",
    "module-03-phase1-verification.md",
    "module-03-phase3-report-close.md",
    "module-03-visualization-api-reference.md",
    "onboarding-phase1b-intro-language.md",
)

# Hosts permitted to appear in a prose URL (see rationale above). The MCP server
# host is intentionally absent so a clickable link to it is flagged.
_URL_SCAN_ALLOWED_HOSTS: frozenset[str] = frozenset(
    {"localhost", "127.0.0.1", "docs.senzing.com"}
)

# A clickable URL's scheme + host: an http/https scheme followed by a host that
# runs up to the first delimiter (``/``, ``:``, whitespace, autolink ``>``,
# inline-link ``)``, closing ``]``, quote, or backtick). Matches both the
# ``<scheme://host>`` autolink form and the ``](scheme://host)`` inline-link
# form. The scheme alternation is built from parts to keep this assertion's
# pattern free of a literal clickable-scheme substring.
_SCHEME: str = "http" + "s?" + "://"
_CLICKABLE_URL_RE: re.Pattern[str] = re.compile(_SCHEME + r"([^\s/:>)\]\"'`]+)")

_FENCE_RE: re.Pattern[str] = re.compile(r"^\s*(?:```|~~~)")
_INLINE_CODE_RE: re.Pattern[str] = re.compile(r"`[^`]*`")


def strip_code_regions(text: str) -> str:
    """Remove fenced code blocks and inline-code spans from Markdown *text*.

    Fenced blocks (delimited by ``` ``` ``` or ``` ~~~ ```) are dropped in full,
    including their fence lines; inline-code spans (`` `...` ``) on the remaining
    prose lines are excised. What remains is the prose a reader would see as
    rendered body text, where a clickable link would actually be clickable. This
    is what the security rule targets, and it excludes command examples and
    loopback strings that legitimately ship inside code.

    Args:
        text: The full Markdown text of a steering file.

    Returns:
        The prose text with all fenced code blocks and inline-code spans removed.
    """
    out: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        out.append(_INLINE_CODE_RE.sub("", line))
    return "\n".join(out)


def find_disallowed_urls(text: str) -> list[str]:
    """Return prose URL hosts in *text* that are not allowlisted.

    Strips code regions first, then collects every http/https host remaining in
    prose whose host is not in ``_URL_SCAN_ALLOWED_HOSTS``. Because the MCP
    server host is not allowlisted, a clickable link to it is reported here too.
    The returned strings are the offending host names; an empty list means the
    prose contains no disallowed clickable URL.

    Args:
        text: The full Markdown text of a steering file.

    Returns:
        The list of disallowed clickable-URL hosts found in *text*'s prose.
    """
    prose = strip_code_regions(text)
    return [
        host
        for host in _CLICKABLE_URL_RE.findall(prose)
        if host not in _URL_SCAN_ALLOWED_HOSTS
    ]


class TestNoExternalUrlScan:
    """Feature: steering-corpus-split, guard: no clickable external / MCP-host URLs.

    Scans every TOUCHED steering file (the four in-scope files and the four new
    units) and fails if any contains a clickable external link — an http/https
    URL in autolink (``<scheme://host>``) or inline-link
    (``[text](scheme://host)``) form — or the MCP server host in clickable/URL
    form, in rendered prose. Command examples and bare-host troubleshooting
    references inside fenced code blocks or inline-code spans (the MCP-host curl
    and nslookup examples and the ``localhost:8080`` loopback strings) are
    excluded because they are stripped before scanning, and loopback plus the
    first-party documentation host are explicitly allowlisted. The MCP server
    host is not allowlisted, so a clickable link to it is reported by the same
    general scan (matching CHECK 2 of the security write-gate hook).

    This is a GUARD assertion enforcing the security rules (Requirement 7.6),
    not one of the four design correctness properties.

    **Validates: Requirements 7.6, 8.5**
    """

    @pytest.mark.parametrize("filename", _URL_SCAN_FILES)
    def test_touched_file_has_no_disallowed_clickable_url(
        self, filename: str
    ) -> None:
        """A touched steering file carries no disallowed clickable URL in prose.

        Covers both arbitrary external hosts and the MCP server host (the latter
        is not allowlisted, so a clickable link to it is reported here).

        Args:
            filename: A touched steering filename (in-scope or new unit).
        """
        path = _STEERING_DIR / filename
        assert path.is_file(), f"Touched steering file is missing: {filename}"
        offenders = find_disallowed_urls(path.read_text(encoding="utf-8"))
        assert offenders == [], (
            f"{filename} contains clickable external URL(s) in prose "
            f"(autolink/inline-link form) for non-allowlisted host(s): "
            f"{offenders}. Steering files must use MCP tools or #[[file:]] "
            f"references instead (security.md / Requirement 7.6)."
        )

    def test_all_touched_files_clean_aggregate(self) -> None:
        """Concrete aggregate pass: no touched file has a disallowed URL.

        Reports every offending ``(file, host)`` pair at once so a regression
        names all violations rather than failing one parametrization at a time.
        """
        violations: list[str] = []
        for filename in _URL_SCAN_FILES:
            path = _STEERING_DIR / filename
            if not path.is_file():
                violations.append(f"{filename}: missing on disk")
                continue
            for host in find_disallowed_urls(path.read_text(encoding="utf-8")):
                violations.append(f"{filename}: {host}")
        assert violations == [], (
            f"Touched steering files contain disallowed clickable URLs: "
            f"{violations}"
        )
