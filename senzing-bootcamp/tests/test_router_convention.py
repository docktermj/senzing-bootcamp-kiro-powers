"""Property-based tests for the thin Router_Root convention in lint_steering.py.

Feature: module-router-standardization
"""

import shutil
import sys
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# Make scripts importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from lint_steering import parse_module_phase_files

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_module_router_index(draw):
    """Generate a steering-index ``modules:`` section with mixed phase shapes.

    Produces a list of ``(module_num, root, phase_files, use_simple_form)``
    tuples covering the three router-relevant shapes:

    - no ``phases`` map (empty ``phase_files``),
    - a single phase whose ``file`` equals the ``root``,
    - one or more phases where at least one ``file`` differs from the ``root``.

    Returns:
        list of ``(int, str, list[str], bool)`` module specs with unique numbers.
    """
    nums = sorted(draw(st.sets(st.integers(min_value=1, max_value=50),
                               min_size=1, max_size=8)))
    modules: list[tuple[int, str, list[str], bool]] = []
    for n in nums:
        root = f"module-{n:02d}-root.md"
        # Each phase is either the root itself ("root") or a distinct file.
        kinds = draw(st.lists(st.sampled_from(["root", "other"]),
                              min_size=0, max_size=4))
        phase_files: list[str] = []
        other_idx = 0
        for kind in kinds:
            if kind == "root":
                phase_files.append(root)
            else:
                phase_files.append(f"module-{n:02d}-phase{other_idx}.md")
                other_idx += 1
        # When there are no phases, randomly use the inline simple form
        # ("  N: root.md") or the complex form with a bare ``root:`` and no
        # ``phases`` map — both represent "no phases map".
        use_simple = draw(st.booleans()) if not phase_files else False
        modules.append((n, root, phase_files, use_simple))
    return modules


def _render_index(modules: list[tuple[int, str, list[str], bool]]) -> str:
    """Render module specs into steering-index.yaml ``modules:`` text.

    Args:
        modules: list of ``(module_num, root, phase_files, use_simple)`` specs.

    Returns:
        YAML text containing only the ``modules:`` section.
    """
    lines = ["modules:"]
    for module_num, root, phase_files, use_simple in modules:
        if not phase_files and use_simple:
            lines.append(f"  {module_num}: {root}")
            continue
        lines.append(f"  {module_num}:")
        lines.append(f"    root: {root}")
        if phase_files:
            lines.append("    phases:")
            for i, phase_file in enumerate(phase_files):
                lines.append(f"      phase{i}:")
                lines.append(f"        file: {phase_file}")
                lines.append("        token_count: 100")
                lines.append("        size_category: medium")
                lines.append("        step_range: [1, 2]")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Property 1: Router identification and scope
# ---------------------------------------------------------------------------


class TestProperty1RouterIdentificationAndScope:
    """Feature: module-router-standardization, Property 1: Router identification and scope

    For any generated module entry, the module's ``root`` is treated as an
    in-scope Router_Root if and only if the module has a ``phases`` map
    containing at least one phase ``file`` distinct from the ``root``; a module
    with no ``phases`` map, or whose only phase ``file`` equals the ``root``, is
    excluded.

    **Validates: Requirements 2.1, 2.2, 2.3, 6.1**
    """

    @given(modules=st_module_router_index())
    @settings(max_examples=100)
    def test_in_scope_iff_phase_file_differs_from_root(self, modules):
        """``in_scope`` is True iff a phase file differs from the root."""
        tmp = Path(tempfile.mkdtemp())
        try:
            index_path = tmp / "steering-index.yaml"
            index_path.write_text(_render_index(modules), encoding="utf-8")

            parsed = parse_module_phase_files(index_path)

            # Every generated module is parsed back exactly once.
            assert set(parsed) == {m[0] for m in modules}

            for module_num, root, phase_files, _use_simple in modules:
                info = parsed[module_num]
                assert info.root == root
                assert info.phase_files == phase_files

                expected_in_scope = any(pf != root for pf in phase_files)
                assert info.in_scope == expected_in_scope, (
                    f"module {module_num}: in_scope={info.in_scope} but expected "
                    f"{expected_in_scope} for root={root!r} phases={phase_files!r}"
                )

                # Excluded shapes (no phases, or only phase == root) never in scope.
                if not phase_files or all(pf == root for pf in phase_files):
                    assert not info.in_scope
                else:
                    assert info.in_scope
        finally:
            shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Property 2: Router_Ceiling enforcement
# ---------------------------------------------------------------------------

from lint_steering import ModuleRouterInfo, check_router_convention


@st.composite
def st_in_scope_root_and_ceiling(draw):
    """Generate an in-scope Router_Root, its token count, and a ceiling.

    Produces adversarial token counts clustered around the ceiling boundary
    (exactly at the ceiling, one under, one over) as well as far-off values, so
    the iff relationship ``token_count > ceiling`` is exercised at the edges.

    The generated root never doubles as a phase file (every phase file is
    distinct from the root), isolating the ceiling rule from the
    root-doubles-as-phase rule. The token count is always a non-negative int,
    so the "no measured token_count" path is never triggered.

    Returns:
        tuple of ``(module_num, root, phase_files, token_count, ceiling)``.
    """
    module_num = draw(st.integers(min_value=1, max_value=50))
    ceiling = draw(st.integers(min_value=0, max_value=5000))
    # Bias token_count toward the ceiling boundary to cover the iff edges.
    offset = draw(st.sampled_from([-2, -1, 0, 1, 2])
                  | st.integers(min_value=-ceiling, max_value=5000))
    token_count = max(0, ceiling + offset)
    # At least one phase file, all distinct from the root => in-scope, not
    # doubles-as-phase.
    num_phases = draw(st.integers(min_value=1, max_value=4))
    root = f"module-{module_num:02d}-root.md"
    phase_files = [f"module-{module_num:02d}-phase{i}.md" for i in range(num_phases)]
    return module_num, root, phase_files, token_count, ceiling


def _ceiling_violations(violations, root):
    """Return ceiling violations naming ``root`` (substring match on message)."""
    return [v for v in violations
            if root in v.message and "exceeds the Router_Ceiling" in v.message]


class TestProperty2RouterCeilingEnforcement:
    """Feature: module-router-standardization, Property 2: Router_Ceiling enforcement

    For any in-scope Router_Root and any non-negative router_ceiling, the router
    rule emits a ceiling violation if and only if the root's token_count is
    strictly greater than the ceiling, and when emitted the violation message
    names the root filename, its token count, and the ceiling.

    **Validates: Requirements 1.3, 1.6, 2.3, 2.4, 6.2**
    """

    @given(spec=st_in_scope_root_and_ceiling())
    @settings(max_examples=200)
    def test_ceiling_violation_iff_over_ceiling(self, spec):
        """A ceiling violation is emitted iff token_count > ceiling."""
        module_num, root, phase_files, token_count, ceiling = spec

        info = ModuleRouterInfo(
            module_num=module_num,
            root=root,
            phase_files=phase_files,
            root_token_count=token_count,
        )
        index_data = {module_num: info}
        # Supply token_count via file_metadata as well to mirror real usage.
        file_metadata = {root: {"token_count": token_count}}

        violations = check_router_convention(index_data, file_metadata, ceiling)
        ceiling_violations = _ceiling_violations(violations, root)

        expected_violation = token_count > ceiling
        assert bool(ceiling_violations) == expected_violation, (
            f"token_count={token_count} ceiling={ceiling}: "
            f"expected_violation={expected_violation} but got "
            f"{[v.message for v in ceiling_violations]}"
        )

        if expected_violation:
            # Exactly one ceiling violation, naming root, count, and ceiling.
            assert len(ceiling_violations) == 1
            message = ceiling_violations[0].message
            assert root in message
            assert str(token_count) in message
            assert str(ceiling) in message

    @given(
        ceiling=st.integers(min_value=0, max_value=5000),
        module_num=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=100)
    def test_boundary_at_ceiling_no_violation_one_over_violates(
        self, ceiling, module_num
    ):
        """Exactly at the ceiling: no violation; one token over: violation."""
        root = f"module-{module_num:02d}-root.md"
        phase_files = [f"module-{module_num:02d}-phase0.md"]

        def run(token_count):
            info = ModuleRouterInfo(
                module_num=module_num,
                root=root,
                phase_files=phase_files,
                root_token_count=token_count,
            )
            violations = check_router_convention(
                {module_num: info}, {root: {"token_count": token_count}}, ceiling
            )
            return _ceiling_violations(violations, root)

        # Boundary: token_count == ceiling => no ceiling violation.
        assert run(ceiling) == []

        # One over: token_count == ceiling + 1 => exactly one ceiling violation
        # naming root, count, and ceiling.
        over = run(ceiling + 1)
        assert len(over) == 1
        message = over[0].message
        assert root in message
        assert str(ceiling + 1) in message
        assert str(ceiling) in message


# ---------------------------------------------------------------------------
# Property 3: Root-doubles-as-phase enforcement
# ---------------------------------------------------------------------------


@st.composite
def st_in_scope_root_doubles_spec(draw):
    """Generate an in-scope module whose root may or may not double as a phase.

    Every generated module is in-scope: it always has at least one phase file
    distinct from the root. With ``doubles`` True the root filename is also
    inserted among the phase files (the root-doubles-as-phase pattern); with
    ``doubles`` False every phase file differs from the root.

    The token count is held well below the ceiling (and a large ceiling is
    supplied) so the ceiling rule never fires, isolating the
    root-doubles-as-phase rule.

    Returns:
        tuple of ``(module_num, root, phase_files, doubles)``.
    """
    module_num = draw(st.integers(min_value=1, max_value=50))
    root = f"module-{module_num:02d}-root.md"
    # At least one distinct phase file guarantees the module is in-scope.
    num_distinct = draw(st.integers(min_value=1, max_value=4))
    distinct = [f"module-{module_num:02d}-phase{i}.md" for i in range(num_distinct)]

    doubles = draw(st.booleans())
    if doubles:
        # Insert the root among the phase files at a random position.
        insert_at = draw(st.integers(min_value=0, max_value=len(distinct)))
        phase_files = distinct[:insert_at] + [root] + distinct[insert_at:]
    else:
        phase_files = distinct

    return module_num, root, phase_files, doubles


def _doubles_violations(violations, root):
    """Return doubles-as-phase violations naming ``root``.

    A violation qualifies when its message names the root filename and contains
    the ``root-doubles-as-phase`` phrase.
    """
    return [v for v in violations
            if root in v.message and "root-doubles-as-phase" in v.message]


class TestProperty3RootDoublesAsPhaseEnforcement:
    """Feature: module-router-standardization, Property 3: Root-doubles-as-phase enforcement

    For any in-scope module, the router rule emits a root-doubles-as-phase
    violation if and only if the module's ``root`` filename appears among that
    module's phase ``file`` values, and the violation names the offending root.

    **Validates: Requirements 2.5, 4.3, 6.3**
    """

    @given(spec=st_in_scope_root_doubles_spec())
    @settings(max_examples=200)
    def test_doubles_violation_iff_root_among_phase_files(self, spec):
        """A doubles-as-phase violation is emitted iff root is a phase file."""
        module_num, root, phase_files, doubles = spec

        # Large ceiling + small token_count so the ceiling rule never fires.
        ceiling = 10000
        token_count = 100

        info = ModuleRouterInfo(
            module_num=module_num,
            root=root,
            phase_files=phase_files,
            root_token_count=token_count,
        )
        index_data = {module_num: info}
        file_metadata = {root: {"token_count": token_count}}

        violations = check_router_convention(index_data, file_metadata, ceiling)
        doubles_violations = _doubles_violations(violations, root)

        expected_violation = root in phase_files
        # Cross-check the generator's intent matches the actual membership.
        assert expected_violation == doubles

        assert bool(doubles_violations) == expected_violation, (
            f"root={root!r} phase_files={phase_files!r}: "
            f"expected_violation={expected_violation} but got "
            f"{[v.message for v in doubles_violations]}"
        )

        if expected_violation:
            # Exactly one doubles-as-phase violation, naming the offending root.
            assert len(doubles_violations) == 1
            message = doubles_violations[0].message
            assert root in message
            assert "root-doubles-as-phase" in message

    @given(
        module_num=st.integers(min_value=1, max_value=50),
        num_distinct=st.integers(min_value=1, max_value=4),
    )
    @settings(max_examples=100)
    def test_no_doubles_when_all_phase_files_distinct(self, module_num, num_distinct):
        """An in-scope root distinct from every phase file emits no doubles violation."""
        root = f"module-{module_num:02d}-root.md"
        phase_files = [f"module-{module_num:02d}-phase{i}.md"
                       for i in range(num_distinct)]

        info = ModuleRouterInfo(
            module_num=module_num,
            root=root,
            phase_files=phase_files,
            root_token_count=100,
        )
        violations = check_router_convention(
            {module_num: info}, {root: {"token_count": 100}}, 10000
        )
        assert _doubles_violations(violations, root) == []


# ---------------------------------------------------------------------------
# Property 4: Compliant index produces no router violations
# ---------------------------------------------------------------------------


@st.composite
def st_compliant_index(draw):
    """Generate a compliant index plus its file_metadata and ceiling.

    Every module in the returned ``index_data`` satisfies the compliant
    convention, so ``check_router_convention`` must report zero violations:

    - In-scope modules (at least one phase file distinct from the root) have a
      root ``token_count`` at or below the ceiling and a root filename distinct
      from every one of that module's phase files (never doubles-as-phase).
    - A randomly mixed-in subset of excluded modules (no phases, or a single
      phase whose file equals the root) is also included; excluded modules never
      produce a router violation regardless of token count, so they may sit at,
      below, or above the ceiling.

    Token counts for in-scope roots are biased toward the ceiling boundary
    (exactly at the ceiling, one or two under) to exercise the ``<=`` edge.

    Returns:
        tuple of ``(index_data, file_metadata, ceiling)`` where ``index_data``
        maps module number to ``ModuleRouterInfo`` and ``file_metadata`` maps
        each root filename to ``{"token_count": int}``.
    """
    ceiling = draw(st.integers(min_value=0, max_value=5000))
    nums = sorted(draw(st.sets(st.integers(min_value=1, max_value=50),
                               min_size=1, max_size=8)))

    index_data: dict[int, ModuleRouterInfo] = {}
    file_metadata: dict[str, dict] = {}

    for module_num in nums:
        root = f"module-{module_num:02d}-root.md"
        shape = draw(st.sampled_from(["in_scope", "no_phases", "single_eq_root"]))

        if shape == "no_phases":
            phase_files: list[str] = []
            # Excluded modules may carry any token count (including over ceiling).
            token_count = draw(st.integers(min_value=0, max_value=ceiling + 5000))
        elif shape == "single_eq_root":
            phase_files = [root]
            token_count = draw(st.integers(min_value=0, max_value=ceiling + 5000))
        else:  # in_scope: phase files all distinct from root, count <= ceiling
            num_phases = draw(st.integers(min_value=1, max_value=4))
            phase_files = [f"module-{module_num:02d}-phase{i}.md"
                           for i in range(num_phases)]
            # Bias toward the ceiling boundary while staying at or below it.
            offset = draw(st.sampled_from([0, -1, -2])
                          | st.integers(min_value=-ceiling, max_value=0))
            token_count = max(0, ceiling + offset)

        index_data[module_num] = ModuleRouterInfo(
            module_num=module_num,
            root=root,
            phase_files=phase_files,
            root_token_count=token_count,
        )
        file_metadata[root] = {"token_count": token_count}

    return index_data, file_metadata, ceiling


class TestProperty4CompliantIndexNoViolations:
    """Feature: module-router-standardization, Property 4: Compliant index produces no router violations

    For any generated index in which every in-scope Router_Root has a
    token_count at or below the router_ceiling and a filename distinct from all
    of its module's phase files, check_router_convention returns no violations.

    **Validates: Requirements 6.5**
    """

    @given(spec=st_compliant_index())
    @settings(max_examples=200)
    def test_compliant_index_yields_no_violations(self, spec):
        """A fully compliant index (mixed with excluded modules) has zero violations."""
        index_data, file_metadata, ceiling = spec

        # Sanity-check the generator: every in-scope root is compliant.
        for info in index_data.values():
            if info.in_scope:
                assert not info.doubles_as_phase
                assert info.root_token_count <= ceiling

        violations = check_router_convention(index_data, file_metadata, ceiling)
        assert violations == [], (
            f"expected no violations for compliant index but got "
            f"{[v.message for v in violations]}"
        )
