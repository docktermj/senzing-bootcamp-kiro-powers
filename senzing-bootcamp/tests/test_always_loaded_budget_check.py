"""Tests for the always-loaded steering budget check in measure_steering.py.

Property-based tests (Hypothesis) for the always-loaded-steering-budget-check
feature. This module currently implements Property 1 (Task 2.3): the
Always_Loaded_Set is exactly the ``inclusion: always`` files, and a single
authoritative source drives both ``collect_always_loaded_set`` and
``simulate_context_load``.

Fixtures are synthetic, PII-free steering files written into a throwaway temp
directory per example (power-distribution safety). Property example counts come
from the active Hypothesis profile (``fast`` locally, ``thorough`` in CI); no
inline ``@settings(max_examples=...)`` is set.
"""

from __future__ import annotations

import contextlib
import io
import re
import shutil
import sys
import tempfile
from pathlib import Path

import hypothesis.strategies as st
from hypothesis import given

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages).
# conftest.py already inserts this, but keep it explicit per convention.
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import measure_steering  # noqa: E402


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# The observed frontmatter inclusion values across the corpus, plus None to
# represent a file with no frontmatter block at all.
_INCLUSION_VALUES = ("always", "fileMatch", "manual", "auto")

# Unique steering filenames of the form "<stem>.md".
_st_filename = st.from_regex(r"[a-z][a-z0-9\-]{0,19}\.md", fullmatch=True)


@st.composite
def st_inclusion_value(draw) -> str | None:
    """Draw a frontmatter ``inclusion`` value, or None for no frontmatter.

    Returns one of ``always`` / ``fileMatch`` / ``manual`` / ``auto``, or
    ``None`` to signal that the file should have no frontmatter block at all.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        One of the inclusion value strings, or ``None`` for no frontmatter.
    """
    return draw(st.sampled_from((*_INCLUSION_VALUES, None)))


def _render_steering_file(inclusion: str | None, quoted: bool, pad: bool) -> str:
    """Render a synthetic, PII-free steering markdown file.

    When ``inclusion`` is None the file has no frontmatter block (its first line
    is body text). Otherwise a leading ``---``-fenced frontmatter block declares
    the ``inclusion`` value, optionally wrapped in quotes and/or padded with
    surrounding whitespace — all forms ``parse_inclusion`` is documented to
    tolerate.

    Args:
        inclusion: The inclusion value, or None for no frontmatter.
        quoted: Whether to wrap the value in double quotes.
        pad: Whether to add extra whitespace around the value/key.

    Returns:
        The full file text.
    """
    body = "# Synthetic steering file\n\nSynthetic PII-free body text.\n"
    if inclusion is None:
        return body

    value = f'"{inclusion}"' if quoted else inclusion
    indent = "  " if pad else ""
    spacing = "  " if pad else " "
    trailing = "   " if pad else ""
    return (
        "---\n"
        f"{indent}inclusion:{spacing}{value}{trailing}\n"
        "---\n"
        + body
    )


@st.composite
def st_steering_corpus(draw):
    """Draw a synthetic steering corpus and materialize it in a temp directory.

    Writes one synthetic ``*.md`` file per drawn entry, each with a chosen
    ``inclusion`` frontmatter (or none), into a throwaway temp directory. Also
    records the expected always-subset — the sorted filenames whose inclusion is
    exactly ``always``.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A tuple ``(steering_dir, expected_always)`` where ``steering_dir`` is a
        ``Path`` to the materialized corpus and ``expected_always`` is the sorted
        list of filenames declaring ``inclusion: always``. The caller is
        responsible for cleaning up ``steering_dir``.
    """
    filenames = draw(
        st.lists(_st_filename, min_size=0, max_size=8, unique=True)
    )

    steering_dir = Path(tempfile.mkdtemp(prefix="always_loaded_corpus_"))
    expected_always: list[str] = []
    for name in filenames:
        inclusion = draw(st_inclusion_value())
        quoted = draw(st.booleans())
        pad = draw(st.booleans())
        (steering_dir / name).write_text(
            _render_steering_file(inclusion, quoted, pad), encoding="utf-8"
        )
        if inclusion == "always":
            expected_always.append(name)

    return steering_dir, sorted(expected_always)


@st.composite
def st_token_metadata(draw, names: list[str]):
    """Draw a ``file_metadata``-shaped map of non-negative token counts.

    Builds a dict shaped like the output of ``scan_steering_files`` — mapping a
    filename to a metadata dict carrying a non-negative ``token_count`` — for a
    subset of ``names``. Some names are optionally omitted from the map so the
    test exercises the "absent files contribute 0" behavior of
    ``compute_baseline_footprint``.

    Args:
        draw: The Hypothesis draw callable.
        names: The candidate filenames (the always-loaded set) to assign counts
            to. Any subset may be omitted from the returned map.

    Returns:
        A dict mapping each included filename to
        ``{"token_count": <int>=0, "size_category": "small"}``.
    """
    metadata: dict[str, dict] = {}
    for name in names:
        if draw(st.booleans()):
            # Omit this name from file_metadata (contributes 0 to the footprint).
            continue
        count = draw(st.integers(min_value=0, max_value=100_000))
        metadata[name] = {"token_count": count, "size_category": "small"}
    return metadata


@st.composite
def st_budget_yaml_with_ceiling(draw):
    """Draw ``steering-index.yaml`` budget text declaring a ceiling, plus N.

    Renders a synthetic ``budget`` block whose ``always_loaded_ceiling_pct`` key
    is set to a drawn non-negative integer ``N``, optionally surrounded by other
    budget keys and arbitrary indentation the localized regex tolerates.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A tuple ``(content, n)`` where ``content`` is the YAML text declaring
        ``always_loaded_ceiling_pct: N`` and ``n`` is that integer value.
    """
    n = draw(st.integers(min_value=0, max_value=100))
    # Extra spaces after the colon are tolerated by the ``\s*`` in the regex.
    spacing = " " * draw(st.integers(min_value=1, max_value=4))
    content = (
        "budget:\n"
        "  total_tokens: 196855\n"
        "  reference_window: 200000\n"
        "  warn_threshold_pct: 60\n"
        "  critical_threshold_pct: 80\n"
        f"  always_loaded_ceiling_pct:{spacing}{n}\n"
        "  split_threshold_tokens: 5000\n"
    )
    return content, n


@st.composite
def st_budget_yaml_without_ceiling(draw):
    """Draw ``steering-index.yaml`` budget text that omits the ceiling key.

    Renders a synthetic ``budget`` block with the usual authority keys but no
    ``always_loaded_ceiling_pct`` line, exercising the documented-default path of
    ``parse_always_loaded_ceiling_pct``.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        YAML text for a budget block lacking ``always_loaded_ceiling_pct``.
    """
    total = draw(st.integers(min_value=0, max_value=1_000_000))
    return (
        "budget:\n"
        f"  total_tokens: {total}\n"
        "  reference_window: 200000\n"
        "  warn_threshold_pct: 60\n"
        "  critical_threshold_pct: 80\n"
        "  split_threshold_tokens: 5000\n"
    )


@st.composite
def st_budget_params(draw):
    """Draw ``(footprint, ceiling_pct, warn_pct, reference_window)`` at boundaries.

    Draws the ceiling/warn/window parameters first, computes the resulting
    ceiling in tokens exactly as ``check_always_loaded_budget`` does
    (``round(ceiling_pct/100 * round(warn_pct/100 * reference_window))``), then
    draws a footprint biased to span below, at, and above that ceiling so the
    pass/fail boundary is exercised on both sides.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A tuple ``(footprint, always_loaded_ceiling_pct, warn_threshold_pct,
        reference_window)`` of non-negative integers.
    """
    ceiling_pct = draw(st.integers(min_value=0, max_value=100))
    warn_pct = draw(st.integers(min_value=0, max_value=100))
    reference_window = draw(st.integers(min_value=0, max_value=500_000))

    # Mirror the implementation's rounding exactly to pin the boundary token.
    warn_threshold_tokens = round(warn_pct / 100 * reference_window)
    ceiling_tokens = round(ceiling_pct / 100 * warn_threshold_tokens)

    # Bias the footprint to span below / at / above the ceiling boundary.
    offset = draw(st.sampled_from((-2, -1, 0, 1, 2)))
    base = draw(
        st.sampled_from(
            (
                max(0, ceiling_tokens + offset),
                draw(st.integers(min_value=0, max_value=500_000)),
            )
        )
    )
    footprint = max(0, base)
    return footprint, ceiling_pct, warn_pct, reference_window


@st.composite
def st_always_loaded_result(draw):
    """Draw an ``AlwaysLoadedResult`` spanning over-/under-budget states.

    Builds the dataclass directly (via ``measure_steering.AlwaysLoadedResult``)
    with arbitrary non-negative figures and a varied ``always_loaded`` filename
    list, so the report renderer is exercised across both ``over_budget`` True
    and False. The ``pct_of_warn`` value is drawn independently as a
    non-negative float, decoupling the report-formatting property from the
    footprint/threshold arithmetic (covered by other properties).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        An ``AlwaysLoadedResult`` instance.
    """
    always_loaded = draw(
        st.lists(_st_filename, min_size=0, max_size=8, unique=True)
    )
    footprint_tokens = draw(st.integers(min_value=0, max_value=1_000_000))
    warn_threshold_tokens = draw(st.integers(min_value=0, max_value=1_000_000))
    ceiling_pct = draw(st.integers(min_value=0, max_value=100))
    ceiling_tokens = draw(st.integers(min_value=0, max_value=1_000_000))
    pct_of_warn = draw(
        st.floats(
            min_value=0.0,
            max_value=1_000.0,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    over_budget = draw(st.booleans())
    return measure_steering.AlwaysLoadedResult(
        always_loaded=sorted(always_loaded),
        footprint_tokens=footprint_tokens,
        warn_threshold_tokens=warn_threshold_tokens,
        ceiling_pct=ceiling_pct,
        ceiling_tokens=ceiling_tokens,
        pct_of_warn=pct_of_warn,
        over_budget=over_budget,
    )


def _write_index_with_budget(
    steering_dir: Path,
    ceiling_pct: int,
    warn_pct: int,
    reference_window: int,
) -> Path:
    """Write a steering-index.yaml whose budget block declares the given params.

    Args:
        steering_dir: Directory to place the index in.
        ceiling_pct: The ``always_loaded_ceiling_pct`` value to declare.
        warn_pct: The ``warn_threshold_pct`` value to declare.
        reference_window: The ``reference_window`` value to declare.

    Returns:
        Path to the written ``steering-index.yaml``.
    """
    index_path = steering_dir / "steering-index.yaml"
    index_path.write_text(
        "budget:\n"
        "  total_tokens: 0\n"
        f"  reference_window: {reference_window}\n"
        f"  warn_threshold_pct: {warn_pct}\n"
        "  critical_threshold_pct: 80\n"
        f"  always_loaded_ceiling_pct: {ceiling_pct}\n",
        encoding="utf-8",
    )
    return index_path


def _write_minimal_index(steering_dir: Path) -> Path:
    """Write a minimal steering-index.yaml with a budget block for --simulate.

    Args:
        steering_dir: The corpus directory to place the index in.

    Returns:
        Path to the written ``steering-index.yaml``.
    """
    index_path = steering_dir / "steering-index.yaml"
    index_path.write_text(
        "budget:\n"
        "  total_tokens: 0\n"
        "  reference_window: 200000\n"
        "  warn_threshold_pct: 60\n",
        encoding="utf-8",
    )
    return index_path


def _write_steering_file(
    steering_dir: Path, name: str, inclusion: str | None, approx_tokens: int
) -> None:
    """Write a synthetic, PII-free steering file targeting a token count.

    ``calculate_token_count`` approximates tokens as ``round(len(content) / 4)``,
    so the body is sized to ``approx_tokens * 4`` characters. When ``inclusion``
    is provided a leading ``---``-fenced frontmatter block declares it; the small
    frontmatter overhead is negligible for the coarse under/over-ceiling margins
    used by these example tests.

    Args:
        steering_dir: Directory to write the file into.
        name: Filename (``*.md``).
        inclusion: The frontmatter ``inclusion`` value, or None for no frontmatter.
        approx_tokens: Approximate desired ``token_count`` for the file.
    """
    body = "a" * max(0, approx_tokens * 4)
    if inclusion is None:
        text = f"# {name}\n\n{body}\n"
    else:
        text = f"---\ninclusion: {inclusion}\n---\n# {name}\n\n{body}\n"
    (steering_dir / name).write_text(text, encoding="utf-8")


def _build_consistent_index(steering_dir: Path) -> Path:
    """Scan the corpus and build a consistent steering-index.yaml via update_index.

    Running ``update_index`` keeps ``file_metadata`` and ``budget.total_tokens``
    consistent with the measured files, so ``check_counts`` / ``check_phase_counts``
    / the budget-total check all pass and only the always-loaded ceiling governs
    the ``--check`` outcome. The rebuilt budget block carries the documented
    default ``always_loaded_ceiling_pct: 25`` unless a prior value is preserved.

    Args:
        steering_dir: Directory containing the synthetic ``*.md`` corpus.

    Returns:
        Path to the written ``steering-index.yaml``.
    """
    index_path = steering_dir / "steering-index.yaml"
    file_metadata = measure_steering.scan_steering_files(steering_dir)
    total_tokens = sum(m["token_count"] for m in file_metadata.values())
    measure_steering.update_index(
        index_path, file_metadata, total_tokens, steering_dir
    )
    return index_path


def _adjust_ceiling(index_path: Path, ceiling_pct: int) -> None:
    """Rewrite the ``always_loaded_ceiling_pct`` value in an existing index.

    Mirrors the "build via update_index, then adjust the ceiling" approach: the
    index is first built consistently, then its ceiling is lowered/raised in
    place so the always-loaded footprint can be driven under or over the ceiling
    without disturbing ``file_metadata`` or the budget total.

    Args:
        index_path: Path to the steering-index.yaml to edit.
        ceiling_pct: The new ``always_loaded_ceiling_pct`` value to write.
    """
    content = index_path.read_text(encoding="utf-8")
    content = re.sub(
        r"always_loaded_ceiling_pct:\s*\d+",
        f"always_loaded_ceiling_pct: {ceiling_pct}",
        content,
    )
    index_path.write_text(content, encoding="utf-8")


class TestAlwaysLoadedBudgetCheck:
    """Property/example tests for the always-loaded steering budget check."""

    # Feature: always-loaded-steering-budget-check, Property 1: The always-loaded
    # set is exactly the `inclusion: always` files, and one source drives both
    # paths (collect_always_loaded_set and simulate_context_load).
    # Validates: Requirements 1.1, 1.2
    @given(corpus=st_steering_corpus())
    def test_authoritative_set_and_shared_definition(self, corpus):
        """collect_always_loaded_set returns exactly the ``inclusion: always``
        files, and simulate_context_load draws its always-loaded list from that
        same set."""
        steering_dir, expected_always = corpus
        # Spy on the shared function without a function-scoped fixture, since
        # those are not reset between @given inputs. Save/restore manually.
        original = measure_steering.collect_always_loaded_set
        try:
            # Requirement 1.1: the authoritative set is exactly the
            # inclusion: always files (sorted).
            actual = measure_steering.collect_always_loaded_set(steering_dir)
            assert actual == expected_always

            # Requirement 1.2: simulate_context_load sources its always-loaded
            # list from the same collect_always_loaded_set. Spy on the shared
            # function to capture what the simulation actually uses.
            captured: dict[str, list[str]] = {}

            def _spy(arg):
                result = original(arg)
                captured["always_loaded"] = result
                return result

            measure_steering.collect_always_loaded_set = _spy

            index_path = _write_minimal_index(steering_dir)
            file_metadata = {
                name: {"token_count": 0, "size_category": "small"}
                for name in expected_always
            }
            with contextlib.redirect_stdout(io.StringIO()):
                measure_steering.simulate_context_load(
                    index_path, file_metadata, steering_dir
                )

            assert captured.get("always_loaded") == expected_always
        finally:
            measure_steering.collect_always_loaded_set = original
            shutil.rmtree(steering_dir, ignore_errors=True)

    # Feature: always-loaded-steering-budget-check, Property 2: Baseline
    # footprint equals the sum of measured counts — compute_baseline_footprint
    # returns the sum of token_count over exactly the always-loaded set, with
    # files absent from file_metadata contributing 0, independent of set order.
    # Validates: Requirements 2.1
    @given(data=st.data())
    def test_footprint_equals_sum_of_measured_counts(self, data):
        """compute_baseline_footprint sums token_count over exactly the set,
        absent files contribute 0, and the result is order-independent."""
        always_loaded = data.draw(
            st.lists(_st_filename, min_size=0, max_size=8, unique=True),
            label="always_loaded",
        )
        file_metadata = data.draw(
            st_token_metadata(always_loaded), label="file_metadata"
        )

        # Expected: sum over exactly the always-loaded set, absent files -> 0.
        expected = sum(
            file_metadata.get(name, {}).get("token_count", 0)
            for name in always_loaded
        )

        result = measure_steering.compute_baseline_footprint(
            always_loaded, file_metadata
        )
        assert result == expected

        # Absent files contribute 0: names not in file_metadata add nothing.
        present_sum = sum(
            meta["token_count"]
            for name, meta in file_metadata.items()
            if name in always_loaded
        )
        assert result == present_sum

        # Order-independence: shuffling the set yields the same footprint.
        shuffled = data.draw(st.permutations(always_loaded), label="shuffled")
        assert (
            measure_steering.compute_baseline_footprint(shuffled, file_metadata)
            == result
        )

    # Feature: always-loaded-steering-budget-check, Property 4: The ceiling is
    # read from configuration — for any budget YAML declaring
    # always_loaded_ceiling_pct: N, parse_always_loaded_ceiling_pct returns
    # exactly N; when the key is absent it returns the documented default, so no
    # ceiling value is ever a magic number inside the decision logic.
    # Validates: Requirements 2.4
    @given(spec=st_budget_yaml_with_ceiling())
    def test_ceiling_read_from_configuration(self, spec):
        """parse_always_loaded_ceiling_pct returns exactly the declared N."""
        content, n = spec
        assert measure_steering.parse_always_loaded_ceiling_pct(content) == n

    # Feature: always-loaded-steering-budget-check, Property 4: The ceiling is
    # read from configuration — the documented default governs when the key is
    # absent.
    # Validates: Requirements 2.4
    @given(
        content=st_budget_yaml_without_ceiling(),
        default=st.integers(min_value=0, max_value=100),
    )
    def test_ceiling_absent_returns_documented_default(self, content, default):
        """When the key is absent the parser returns the documented default."""
        # The documented default is 25 when not overridden.
        assert measure_steering.parse_always_loaded_ceiling_pct(content) == 25
        # An explicit default argument is honored when the key is absent.
        assert (
            measure_steering.parse_always_loaded_ceiling_pct(
                content, default=default
            )
            == default
        )

    # Feature: always-loaded-steering-budget-check, Property 3: The pass/fail
    # decision matches the ceiling boundary — check_always_loaded_budget reports
    # over_budget true iff the footprint exceeds
    # always_loaded_ceiling_pct/100 * warn_threshold_pct/100 * reference_window
    # (with the implementation's rounding); at or below the ceiling it is false.
    # Validates: Requirements 2.2, 2.3
    @given(params=st_budget_params())
    def test_pass_fail_decision_matches_ceiling_boundary(self, params):
        """over_budget is true iff footprint exceeds the configured ceiling."""
        footprint, ceiling_pct, warn_pct, reference_window = params

        steering_dir = Path(tempfile.mkdtemp(prefix="always_loaded_boundary_"))
        try:
            # One inclusion: always file carrying the drawn footprint count.
            always_name = "always-baseline.md"
            (steering_dir / always_name).write_text(
                _render_steering_file("always", quoted=False, pad=False),
                encoding="utf-8",
            )
            index_path = _write_index_with_budget(
                steering_dir, ceiling_pct, warn_pct, reference_window
            )
            file_metadata = {
                always_name: {
                    "token_count": footprint,
                    "size_category": "small",
                }
            }

            result = measure_steering.check_always_loaded_budget(
                index_path, steering_dir, file_metadata
            )

            # Compute the expected ceiling the same way the implementation does
            # (nested round()) to avoid float boundary flakiness.
            warn_threshold_tokens = round(warn_pct / 100 * reference_window)
            ceiling_tokens = round(ceiling_pct / 100 * warn_threshold_tokens)

            assert result.footprint_tokens == footprint
            assert result.ceiling_tokens == ceiling_tokens
            # The pass/fail boundary: strictly-greater-than is over budget.
            assert result.over_budget == (footprint > ceiling_tokens)
        finally:
            shutil.rmtree(steering_dir, ignore_errors=True)

    # Feature: always-loaded-steering-budget-check, Property 5: The report
    # states the required figures and names contributors on failure — the
    # rendered report always contains the Baseline_Footprint in tokens, the
    # Warn_Threshold in tokens, and the percentage of the Warn_Threshold
    # consumed; and whenever over budget, it names every file in the
    # Always_Loaded_Set.
    # Validates: Requirements 3.1, 3.2
    @given(result=st_always_loaded_result())
    def test_report_states_figures_and_names_contributors(self, result):
        """The report always states footprint, warn-threshold, and percent
        consumed; on over_budget it names every always-loaded file."""
        lines = measure_steering.format_always_loaded_report(result)
        text = "\n".join(lines)

        # Requirement 3.1: the required figures are always present.
        assert str(result.footprint_tokens) in text
        assert str(result.warn_threshold_tokens) in text
        assert f"{result.pct_of_warn:.1f}%" in text

        # Requirement 3.2: on failure, every contributing file is named.
        if result.over_budget:
            for name in result.always_loaded:
                assert name in text

    # -----------------------------------------------------------------------
    # Example / regression tests (Task 6.2). Plain pytest methods over fixed
    # synthetic corpora — complementing the property tests above.
    # -----------------------------------------------------------------------

    # Under-ceiling pass: a corpus whose always-files sum well below the ceiling
    # reports "within budget" and main(["--check"]) exits 0.
    # Validates: Requirements 5.1, 2.3, 4.1
    def test_under_ceiling_baseline_passes_and_main_exits_zero(self):
        """always-files below the ceiling → not over budget and --check exits 0."""
        steering_dir = Path(tempfile.mkdtemp(prefix="always_loaded_under_"))
        try:
            _write_steering_file(steering_dir, "agent-instructions.md", "always", 500)
            _write_steering_file(steering_dir, "module-transitions.md", "always", 400)
            _write_steering_file(steering_dir, "lang-python.md", "fileMatch", 1800)
            _write_steering_file(steering_dir, "faq.md", "auto", 300)
            index_path = _build_consistent_index(steering_dir)
            # Default ceiling 25% of 120,000 warn tokens = 30,000 — far above ~900.
            file_metadata = measure_steering.scan_steering_files(steering_dir)

            result = measure_steering.check_always_loaded_budget(
                index_path, steering_dir, file_metadata
            )
            assert result.always_loaded == [
                "agent-instructions.md",
                "module-transitions.md",
            ]
            assert result.over_budget is False
            assert result.footprint_tokens < result.ceiling_tokens

            report = "\n".join(
                measure_steering.format_always_loaded_report(result, file_metadata)
            )
            assert "within budget" in report

            exit_code, out = _run_main_check(steering_dir, index_path)
            assert exit_code == 0
            assert "within budget" in out
        finally:
            shutil.rmtree(steering_dir, ignore_errors=True)

    # Over-ceiling fail with naming: a corpus whose always-files exceed the
    # ceiling sets over_budget, the report names each contributing file, and
    # main(["--check"]) exits non-zero.
    # Validates: Requirements 5.1, 3.2, 2.2, 4.1
    def test_over_ceiling_baseline_fails_with_naming_and_main_exits_nonzero(self):
        """always-files above the ceiling → over budget, named, and --check exits 1."""
        steering_dir = Path(tempfile.mkdtemp(prefix="always_loaded_over_"))
        try:
            _write_steering_file(steering_dir, "agent-instructions.md", "always", 1000)
            _write_steering_file(steering_dir, "module-transitions.md", "always", 1000)
            _write_steering_file(steering_dir, "lang-python.md", "fileMatch", 1800)
            index_path = _build_consistent_index(steering_dir)
            # Lower the ceiling to 1% of 120,000 = 1,200 tokens; footprint ~2,000.
            _adjust_ceiling(index_path, 1)
            file_metadata = measure_steering.scan_steering_files(steering_dir)

            result = measure_steering.check_always_loaded_budget(
                index_path, steering_dir, file_metadata
            )
            assert result.over_budget is True
            assert result.footprint_tokens > result.ceiling_tokens

            report = "\n".join(
                measure_steering.format_always_loaded_report(result, file_metadata)
            )
            assert "OVER BUDGET" in report
            for name in ("agent-instructions.md", "module-transitions.md"):
                assert name in report

            # main --check exits non-zero and prints the naming report.
            exit_code, out = _run_main_check(steering_dir, index_path)
            assert exit_code == 1
            assert "OVER BUDGET" in out
            assert "agent-instructions.md" in out
            assert "module-transitions.md" in out
        finally:
            shutil.rmtree(steering_dir, ignore_errors=True)

    # Config-driven ceiling: an explicit always_loaded_ceiling_pct in the index
    # is honored by the check; when the key is absent the documented default (25)
    # governs — never a magic number in the decision logic.
    # Validates: Requirements 2.4
    def test_config_driven_ceiling_honored_vs_documented_default(self):
        """The check honors an explicit ceiling and falls back to the default."""
        steering_dir = Path(tempfile.mkdtemp(prefix="always_loaded_cfg_"))
        try:
            _write_steering_file(steering_dir, "agent-instructions.md", "always", 500)
            index_path = _build_consistent_index(steering_dir)
            file_metadata = measure_steering.scan_steering_files(steering_dir)

            # Explicit ceiling honored: adjust to 40 and confirm the check uses it.
            _adjust_ceiling(index_path, 40)
            honored = measure_steering.check_always_loaded_budget(
                index_path, steering_dir, file_metadata
            )
            assert honored.ceiling_pct == 40
            assert honored.ceiling_tokens == round(
                40 / 100 * honored.warn_threshold_tokens
            )

            # Documented default when the key is absent: strip the line entirely.
            content = index_path.read_text(encoding="utf-8")
            content = re.sub(
                r"\n\s*always_loaded_ceiling_pct:\s*\d+", "", content
            )
            index_path.write_text(content, encoding="utf-8")
            defaulted = measure_steering.check_always_loaded_budget(
                index_path, steering_dir, file_metadata
            )
            assert defaulted.ceiling_pct == 25
        finally:
            shutil.rmtree(steering_dir, ignore_errors=True)

    # Authoritative derivation: collect_always_loaded_set returns exactly the
    # inclusion: always files, and simulate_context_load draws its always-loaded
    # list from that same source.
    # Validates: Requirements 1.1, 1.2
    def test_authoritative_derivation_and_shared_definition(self):
        """The set is exactly the always-files and simulate uses the same source."""
        steering_dir = Path(tempfile.mkdtemp(prefix="always_loaded_auth_"))
        original = measure_steering.collect_always_loaded_set
        try:
            _write_steering_file(steering_dir, "agent-instructions.md", "always", 200)
            _write_steering_file(steering_dir, "module-transitions.md", "always", 150)
            _write_steering_file(steering_dir, "lang-python.md", "fileMatch", 1800)
            _write_steering_file(steering_dir, "faq.md", "auto", 100)
            _write_steering_file(steering_dir, "manual-guide.md", "manual", 100)
            _write_steering_file(steering_dir, "no-frontmatter.md", None, 100)

            expected = ["agent-instructions.md", "module-transitions.md"]
            assert (
                measure_steering.collect_always_loaded_set(steering_dir) == expected
            )

            # simulate_context_load draws its always-loaded list from the same
            # collect_always_loaded_set. Spy on the shared function.
            captured: dict[str, list[str]] = {}

            def _spy(arg):
                result = original(arg)
                captured["always_loaded"] = result
                return result

            measure_steering.collect_always_loaded_set = _spy
            index_path = _write_minimal_index(steering_dir)
            file_metadata = measure_steering.scan_steering_files(steering_dir)
            with contextlib.redirect_stdout(io.StringIO()):
                measure_steering.simulate_context_load(
                    index_path, file_metadata, steering_dir
                )
            assert captured.get("always_loaded") == expected
        finally:
            measure_steering.collect_always_loaded_set = original
            shutil.rmtree(steering_dir, ignore_errors=True)

    # Non-interference regression: with an in-budget baseline, the existing
    # check_counts / check_phase_counts / budget-total checks still pass and
    # main(["--check"]) exits 0 — the always-loaded check only adds failures.
    # Validates: Requirements 4.1, 4.2
    def test_non_interference_regression_existing_checks_still_pass(self):
        """Existing checks pass unchanged and an in-budget baseline exits 0."""
        steering_dir = Path(tempfile.mkdtemp(prefix="always_loaded_regress_"))
        try:
            _write_steering_file(steering_dir, "agent-instructions.md", "always", 500)
            _write_steering_file(steering_dir, "module-transitions.md", "always", 400)
            _write_steering_file(steering_dir, "lang-python.md", "fileMatch", 1800)
            index_path = _build_consistent_index(steering_dir)
            file_metadata = measure_steering.scan_steering_files(steering_dir)

            # Existing checks: no drift, no phase entries, budget total matches.
            assert measure_steering.check_counts(index_path, file_metadata) == []
            assert (
                measure_steering.check_phase_counts(index_path, steering_dir) == []
            )
            content = measure_steering.load_yaml_content(index_path)
            declared_total = measure_steering.parse_budget_total(content)
            stored = measure_steering._parse_stored_metadata(content) or {}
            expected_total = sum(
                m.get("token_count", 0) for m in stored.values()
            )
            assert declared_total == expected_total

            # In-budget baseline → aggregate exit is clean.
            exit_code, out = _run_main_check(steering_dir, index_path)
            assert exit_code == 0
            assert "All token counts are within 10% tolerance." in out
        finally:
            shutil.rmtree(steering_dir, ignore_errors=True)

    # update_index preserves the ceiling key across a rebuild — both an existing
    # value and the documented default when absent.
    # Validates: Requirements 2.4
    def test_update_index_retains_always_loaded_ceiling_pct(self):
        """The rebuilt budget block retains always_loaded_ceiling_pct."""
        steering_dir = Path(tempfile.mkdtemp(prefix="always_loaded_update_"))
        try:
            _write_steering_file(steering_dir, "agent-instructions.md", "always", 300)
            index_path = _build_consistent_index(steering_dir)

            # Documented default emitted on first build (no prior value).
            first = index_path.read_text(encoding="utf-8")
            assert re.search(r"always_loaded_ceiling_pct:\s*25", first)

            # An explicit value is preserved across a subsequent rebuild.
            _adjust_ceiling(index_path, 42)
            file_metadata = measure_steering.scan_steering_files(steering_dir)
            total_tokens = sum(m["token_count"] for m in file_metadata.values())
            measure_steering.update_index(
                index_path, file_metadata, total_tokens, steering_dir
            )
            rebuilt = index_path.read_text(encoding="utf-8")
            assert re.search(r"always_loaded_ceiling_pct:\s*42", rebuilt)
            assert measure_steering.parse_always_loaded_ceiling_pct(rebuilt) == 42
        finally:
            shutil.rmtree(steering_dir, ignore_errors=True)


def _write_synthetic_corpus(steering_dir: Path) -> None:
    """Materialize a realistic, PII-free steering corpus in ``steering_dir``.

    Writes two ``inclusion: always`` files (the baseline), one ``manual`` file,
    and one ``fileMatch`` file. Bodies are synthetic and contain no PII,
    credentials, or connection strings (power-distribution safety). The two
    always-files carry enough body text that their measured ``token_count``
    (``round(len/4)``) is a nontrivial, positive footprint.

    Args:
        steering_dir: Directory to write the ``*.md`` files into.
    """
    always_body = (
        "# Synthetic always-loaded steering\n\n"
        + ("Synthetic PII-free baseline guidance sentence. " * 60)
        + "\n"
    )
    (steering_dir / "agent-baseline.md").write_text(
        "---\ninclusion: always\n---\n" + always_body, encoding="utf-8"
    )
    (steering_dir / "session-baseline.md").write_text(
        "---\ninclusion: always\n---\n" + always_body, encoding="utf-8"
    )
    (steering_dir / "manual-guide.md").write_text(
        "---\ninclusion: manual\n---\n# Synthetic manual guide\n\n"
        "Synthetic PII-free manual content.\n",
        encoding="utf-8",
    )
    (steering_dir / "lang-python.md").write_text(
        '---\ninclusion: fileMatch\nfileMatchPattern: "*.py"\n---\n'
        "# Synthetic language file\n\nSynthetic PII-free language content.\n",
        encoding="utf-8",
    )


def _run_main_check(steering_dir: Path, index_path: Path) -> tuple[int, str]:
    """Run ``measure_steering.main()`` in ``--check`` mode over the temp corpus.

    ``main()`` reads ``sys.argv`` (it takes no argv parameter) and calls
    ``sys.exit(...)``. This helper sets ``sys.argv`` to point ``--steering-dir``
    / ``--index-path`` at the temp corpus, captures stdout, catches the
    ``SystemExit`` raised by ``main``, and returns the exit code and captured
    report text.

    Args:
        steering_dir: The temp steering directory to check.
        index_path: The temp ``steering-index.yaml`` to validate against.

    Returns:
        A tuple ``(exit_code, stdout_text)``.
    """
    argv = [
        "measure_steering.py",
        "--check",
        "--steering-dir",
        str(steering_dir),
        "--index-path",
        str(index_path),
    ]
    saved_argv = sys.argv
    buffer = io.StringIO()
    sys.argv = argv
    try:
        with contextlib.redirect_stdout(buffer):
            measure_steering.main()
        # main() always calls sys.exit(); reaching here would be unexpected.
        exit_code = 0
    except SystemExit as exc:
        code = exc.code
        exit_code = 0 if code is None else int(code)
    finally:
        sys.argv = saved_argv
    return exit_code, buffer.getvalue()


class TestAlwaysLoadedBudgetCheckIntegration:
    """End-to-end integration test wiring the real script against a temp corpus.

    Exercises the same path CI runs (``measure_steering.py --check``) over a
    synthetic, PII-free steering directory and a ``steering-index.yaml`` built by
    ``update_index`` (so file_metadata/budget-total stay consistent and only the
    always-loaded ceiling governs pass/fail). Validates Requirements 4.1 (the
    existing ``--check`` invocation exercises the always-loaded check), 5.1, and
    5.2 (under-ceiling passes; over-ceiling fails naming the files).
    """

    def test_end_to_end_under_and_over_ceiling(self):
        """--check exits 0 under the ceiling and non-zero (naming files) over it."""
        steering_dir = Path(tempfile.mkdtemp(prefix="always_loaded_e2e_"))
        try:
            _write_synthetic_corpus(steering_dir)

            # Build steering-index.yaml from the measured corpus so the
            # file_metadata / phase / budget-total checks all agree and only the
            # always-loaded ceiling decides the outcome.
            index_path = steering_dir / "steering-index.yaml"
            file_metadata = measure_steering.scan_steering_files(steering_dir)
            total_tokens = sum(
                m["token_count"] for m in file_metadata.values()
            )
            measure_steering.update_index(
                index_path, file_metadata, total_tokens, steering_dir
            )

            always_loaded = measure_steering.collect_always_loaded_set(
                steering_dir
            )
            footprint = measure_steering.compute_baseline_footprint(
                always_loaded, file_metadata
            )
            # Sanity: the always-set is exactly our two always-files and the
            # footprint is a nontrivial positive baseline.
            assert always_loaded == ["agent-baseline.md", "session-baseline.md"]
            assert footprint > 0

            # --- Under-budget scenario: default ceiling (25% of warn) ---------
            # update_index writes always_loaded_ceiling_pct: 25 -> ceiling is
            # 0.25 * (0.60 * 200000) = 30000 tokens, far above our footprint.
            exit_code, out = _run_main_check(steering_dir, index_path)
            assert exit_code == 0
            assert "within budget" in out
            assert f"Baseline footprint: {footprint} tokens" in out
            assert "Warn threshold: 120000 tokens" in out
            assert "All token counts are within 10% tolerance." in out

            # --- Over-budget scenario: drop the ceiling below the footprint ---
            # Rewrite the ceiling so ceiling_tokens < footprint (0% -> 0 tokens),
            # forcing over_budget while leaving every other check consistent.
            content = index_path.read_text(encoding="utf-8")
            content = content.replace(
                "always_loaded_ceiling_pct: 25",
                "always_loaded_ceiling_pct: 0",
            )
            index_path.write_text(content, encoding="utf-8")

            exit_code, out = _run_main_check(steering_dir, index_path)
            assert exit_code != 0
            assert "OVER BUDGET" in out
            assert f"Baseline footprint: {footprint} tokens" in out
            # Requirement 3.2 / 5.1: the report names each contributing file.
            for name in always_loaded:
                assert name in out
            # The over-budget exit is driven by the always-loaded check, not a
            # spurious count/phase/budget mismatch.
            assert "mismatch" not in out.lower()
        finally:
            shutil.rmtree(steering_dir, ignore_errors=True)

