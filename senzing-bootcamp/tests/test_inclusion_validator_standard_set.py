"""Property-based test for the inclusion validators' standard-set enforcement.

Feature: steering-inclusion-auto-audit, Property 1: Inclusion validator acceptance
and failure naming

The audit removed the non-standard ``inclusion: auto`` value and tightened both
project validators so each accepts exactly the standard Kiro set
``{always, fileMatch, manual}`` (compared case-sensitively) and nothing else:

- ``lint_steering.check_frontmatter`` scans a steering directory and returns a
  list of ``LintViolation`` objects. A rejected inclusion value yields a
  violation whose ``file`` field names the offending file and whose ``message``
  names the offending value.
- ``validate_power.check_steering_files`` scans ``POWER_DIR / "steering"`` and
  records failures through the module-level ``check`` helper into the module
  ``errors`` list. Each failure message is ``"{file}: ..."`` naming the file, and
  for an out-of-set token the message additionally names the value.

This suite materializes a synthetic, PII-free steering file in a throwaway temp
directory for each drawn candidate inclusion value and asserts that BOTH
validators accept the file iff the value is exactly a standard value, and
otherwise report a failure naming the offending file (and, for a concrete
non-empty token, the offending value).

Validates: Requirements 4.1, 4.2
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path

from hypothesis import assume, given
from hypothesis import strategies as st
from hypothesis.strategies import composite

# Make senzing-bootcamp/scripts/ importable (scripts aren't packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import validate_power  # noqa: E402
from lint_steering import check_frontmatter, run_all_checks  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The standard Kiro inclusion set, compared case-sensitively (Requirement 4.1).
STANDARD_VALUES: tuple[str, ...] = ("always", "fileMatch", "manual")

# Sentinel marking "no inclusion key at all" in a materialized frontmatter block.
MISSING = object()

# The synthetic steering file name used in every materialized corpus.
STEERING_FILENAME = "synthetic-inclusion-test.md"

# Kinds whose value is a concrete, non-empty token that both validators name in
# their failure output (Requirement 4.2). Empty/whitespace/missing kinds are
# reported by file only, so value-naming is not asserted for them.
NAMED_VALUE_KINDS: frozenset[str] = frozenset({"auto", "mixed_case", "unicode_word"})

# Mixed-case variants of the standard/auto values. Every entry differs from a
# standard value only by case, so a case-sensitive validator must reject them.
MIXED_CASE_VALUES: tuple[str, ...] = (
    "Always",
    "ALWAYS",
    "alwayS",
    "FileMatch",
    "filematch",
    "FILEMATCH",
    "Manual",
    "MANUAL",
    "manuaL",
    "Auto",
    "AUTO",
)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_unicode_word_token() -> st.SearchStrategy[str]:
    """Draw a non-empty token consisting solely of Unicode word characters.

    Both branches yield strings that ``\\w+`` matches in full, so the
    ``validate_power`` regex (``inclusion:\\s*(\\w+)``) captures the entire value
    rather than a partial token. This keeps the two validators' verdicts aligned
    for the drawn value while still exercising non-ASCII input.

    Returns:
        A strategy producing all-word-character strings (ASCII and Unicode
        letters/digits/underscore).
    """
    ascii_words = st.from_regex(r"\w{1,15}", fullmatch=True)
    unicode_letters = st.text(
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Lt", "Lm", "Lo", "Nd"),
        ),
        min_size=1,
        max_size=10,
    )
    return st.one_of(ascii_words, unicode_letters)


@composite
def st_inclusion_value(draw) -> tuple[str, object]:
    """Draw a ``(kind, value)`` candidate inclusion value for the validators.

    The drawn kinds cover the full input space named by the design: the standard
    values, the removed ``auto`` value, mixed-case variants, empty and
    whitespace-only values, arbitrary Unicode word tokens, and a "missing"
    sentinel (no inclusion key at all).

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(kind, value)`` pair. ``value`` is a ``str`` for every kind except
        ``"missing"``, whose value is the :data:`MISSING` sentinel.
    """
    kind = draw(
        st.sampled_from(
            [
                "standard",
                "auto",
                "mixed_case",
                "unicode_word",
                "empty",
                "whitespace",
                "missing",
            ]
        )
    )
    if kind == "standard":
        return (kind, draw(st.sampled_from(STANDARD_VALUES)))
    if kind == "auto":
        return (kind, "auto")
    if kind == "mixed_case":
        return (kind, draw(st.sampled_from(MIXED_CASE_VALUES)))
    if kind == "unicode_word":
        value = draw(st_unicode_word_token())
        # Exclude accidental exact standard matches and guarantee the whole
        # token is a single word-character run both validators fully capture.
        assume(value not in STANDARD_VALUES)
        assume(re.fullmatch(r"\w+", value) is not None)
        return (kind, value)
    if kind == "empty":
        return (kind, "")
    if kind == "whitespace":
        return (kind, draw(st.sampled_from([" ", "   ", "\t", " \t "])))
    return ("missing", MISSING)


# ---------------------------------------------------------------------------
# Materialization and validator invocation helpers
# ---------------------------------------------------------------------------


def _materialize_steering_file(
    steering_dir: Path, kind: str, value: object
) -> Path:
    """Write a synthetic, PII-free steering file exercising one inclusion value.

    For the ``"missing"`` kind the ``inclusion:`` key is omitted entirely
    (leaving only a placeholder ``description``); otherwise the value is written
    verbatim on the ``inclusion:`` line. A standard ``fileMatch`` value also gets
    a non-empty ``fileMatchPattern`` so the accepted case is clean under
    ``lint_steering`` (which independently requires a pattern for ``fileMatch``).

    Args:
        steering_dir: The directory to create and write the file into.
        kind: The candidate kind from :func:`st_inclusion_value`.
        value: The candidate value (a ``str`` or the :data:`MISSING` sentinel).

    Returns:
        The path to the written steering file.
    """
    steering_dir.mkdir(parents=True, exist_ok=True)
    lines = ["---"]
    if kind == "missing":
        lines.append("description: synthetic placeholder")
    else:
        lines.append(f"inclusion: {value}")
        if kind == "standard" and value == "fileMatch":
            lines.append('fileMatchPattern: "**/*.py"')
    lines.append("---")
    lines.append("")
    lines.append("# Synthetic Steering File")
    lines.append("")
    lines.append("Synthetic, PII-free body content used only to exercise validators.")
    lines.append("")
    path = steering_dir / STEERING_FILENAME
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _lint_failures_for_file(steering_dir: Path, path: Path) -> list:
    """Return the ``lint_steering`` frontmatter violations naming ``path``.

    Args:
        steering_dir: The steering directory to lint.
        path: The materialized file whose violations are of interest.

    Returns:
        The list of ``LintViolation`` objects whose ``file`` field is ``path``.
    """
    return [v for v in check_frontmatter(steering_dir) if v.file == str(path)]


def _validate_power_failures(power_dir: Path) -> list[str]:
    """Run ``validate_power.check_steering_files`` and return recorded failures.

    Temporarily points the validator's module globals at ``power_dir`` and a
    fresh error buffer, runs the steering-file check, and restores the originals.
    The module-level ``check`` helper resolves ``errors``/``POWER_DIR`` from
    module globals at call time, so rebinding them here redirects its output into
    the throwaway buffer.

    Args:
        power_dir: The temp directory acting as the power root; it must contain a
            ``steering/`` subdirectory.

    Returns:
        The list of failure messages recorded during the check.
    """
    saved_dir = validate_power.POWER_DIR
    saved_errors = validate_power.errors
    saved_warnings = validate_power.warnings
    validate_power.POWER_DIR = power_dir
    validate_power.errors = []
    validate_power.warnings = []
    try:
        validate_power.check_steering_files()
        return list(validate_power.errors)
    finally:
        validate_power.POWER_DIR = saved_dir
        validate_power.errors = saved_errors
        validate_power.warnings = saved_warnings


# ---------------------------------------------------------------------------
# Property 1: Inclusion validator acceptance and failure naming
# ---------------------------------------------------------------------------


class TestProperty1InclusionValidatorStandardSet:
    """Feature: steering-inclusion-auto-audit, Property 1: Inclusion validator
    acceptance and failure naming.

    For any candidate inclusion value (the standard values, ``auto``, mixed-case
    variants, empty/whitespace, arbitrary Unicode, and a missing sentinel), each
    validator accepts the file iff the value is exactly one of
    ``{always, fileMatch, manual}`` compared case-sensitively; every non-accepted
    value yields a failure naming the offending file (and, for a concrete
    non-empty token, the offending value).

    Validates: Requirements 4.1, 4.2
    """

    @given(case=st_inclusion_value())
    def test_validators_accept_only_standard_set_and_name_failures(
        self, case: tuple[str, object]
    ) -> None:
        """Both validators enforce the standard set and name their failures."""
        kind, value = case
        accepted = kind == "standard"
        expect_value_named = kind in NAMED_VALUE_KINDS

        tmp = Path(tempfile.mkdtemp())
        try:
            steering_dir = tmp / "steering"
            path = _materialize_steering_file(steering_dir, kind, value)

            # --- lint_steering.check_frontmatter ---
            lint_failures = _lint_failures_for_file(steering_dir, path)
            if accepted:
                assert not lint_failures, (
                    f"lint_steering rejected accepted value {value!r}: "
                    f"{[v.message for v in lint_failures]}"
                )
            else:
                assert lint_failures, (
                    f"lint_steering accepted non-standard value {value!r} "
                    f"(kind={kind})"
                )
                if expect_value_named:
                    assert any(str(value) in v.message for v in lint_failures), (
                        f"lint_steering failure did not name value {value!r}: "
                        f"{[v.message for v in lint_failures]}"
                    )

            # --- validate_power.check_steering_files ---
            vp_failures = _validate_power_failures(tmp)
            file_failures = [m for m in vp_failures if STEERING_FILENAME in m]
            if accepted:
                assert not vp_failures, (
                    f"validate_power rejected accepted value {value!r}: {vp_failures}"
                )
            else:
                assert file_failures, (
                    f"validate_power did not report a failure naming "
                    f"{STEERING_FILENAME} for value {value!r} (kind={kind}): "
                    f"{vp_failures}"
                )
                if expect_value_named:
                    assert any(str(value) in m for m in file_failures), (
                        f"validate_power failure did not name value {value!r}: "
                        f"{file_failures}"
                    )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 2: Validator parity across both scripts
# ---------------------------------------------------------------------------


def _lint_accepts(steering_dir: Path, path: Path) -> bool:
    """Return whether ``lint_steering`` accepts the materialized steering file.

    Args:
        steering_dir: The steering directory to lint.
        path: The materialized file whose verdict is of interest.

    Returns:
        ``True`` when ``lint_steering.check_frontmatter`` records no violation
        naming ``path`` (the file is accepted), ``False`` otherwise.
    """
    return not _lint_failures_for_file(steering_dir, path)


def _validate_power_accepts(power_dir: Path) -> bool:
    """Return whether ``validate_power`` accepts the materialized steering file.

    Args:
        power_dir: The temp directory acting as the power root; it must contain a
            ``steering/`` subdirectory holding the synthetic file.

    Returns:
        ``True`` when ``validate_power.check_steering_files`` records no failure
        naming the synthetic steering file (the file is accepted), ``False``
        otherwise.
    """
    failures = _validate_power_failures(power_dir)
    return not [m for m in failures if STEERING_FILENAME in m]


class TestProperty2ValidatorParity:
    """Feature: steering-inclusion-auto-audit, Property 2: Validator parity
    across both scripts.

    For any candidate inclusion value, ``validate_power.py`` and
    ``lint_steering.py`` reach the same accept/reject verdict, so their two
    independently-maintained accepted sets can never silently drift apart.

    The two scripts tokenize the raw ``inclusion:`` value differently
    (``lint_steering`` keeps the whole post-colon value; ``validate_power``'s
    ``inclusion:\\s*(\\w+)`` regex captures only the leading word-character run).
    The shared ``st_inclusion_value`` strategy constrains its arbitrary-Unicode
    candidates to ``\\w+`` full-matches and its remaining kinds to single tokens,
    the empty string, whitespace, or a missing key — so the value both scripts
    parse is identical, and parity of the accept/reject verdict is asserted on
    exactly the value each script actually evaluates (the intent of Req 4.3: the
    accepted set ``{always, fileMatch, manual}`` is identical across both).

    Validates: Requirements 4.3
    """

    @given(case=st_inclusion_value())
    def test_both_validators_reach_the_same_verdict(
        self, case: tuple[str, object]
    ) -> None:
        """Both validators accept or reject each candidate value identically."""
        kind, value = case

        tmp = Path(tempfile.mkdtemp())
        try:
            steering_dir = tmp / "steering"
            path = _materialize_steering_file(steering_dir, kind, value)

            lint_accepted = _lint_accepts(steering_dir, path)
            vp_accepted = _validate_power_accepts(tmp)

            assert lint_accepted == vp_accepted, (
                f"validator verdicts diverged for value {value!r} (kind={kind}): "
                f"lint_steering {'accepted' if lint_accepted else 'rejected'} but "
                f"validate_power {'accepted' if vp_accepted else 'rejected'}"
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Req 4.4: validator exit code / non-passing result on an invalid corpus
# ---------------------------------------------------------------------------

# A concrete non-standard inclusion value (the removed ``auto``) used to build
# the invalid corpus so each validator's failure output names a definite value.
INVALID_INCLUSION_VALUE = "auto"


def _stage_lint_corpus(root: Path) -> tuple[Path, Path, Path]:
    """Stage a minimal lint corpus whose only steering file is invalid.

    Creates a ``steering/`` directory holding a single synthetic, PII-free file
    that declares the removed ``inclusion: auto`` value, an empty ``hooks/``
    directory, and a minimal ``steering-index.yaml`` so ``run_all_checks`` runs
    to completion (computing a real exit code) rather than bailing out early on a
    missing directory or index.

    Args:
        root: The temp directory to stage the corpus under.

    Returns:
        A ``(steering_dir, hooks_dir, index_path)`` triple suitable for
        ``lint_steering.run_all_checks``.
    """
    steering_dir = root / "steering"
    _materialize_steering_file(steering_dir, "auto", INVALID_INCLUSION_VALUE)
    hooks_dir = root / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    index_path = steering_dir / "steering-index.yaml"
    index_path.write_text("# minimal synthetic steering index\n", encoding="utf-8")
    return steering_dir, hooks_dir, index_path


class TestValidatorExitCodeOnInvalidCorpus:
    """Exit code / non-passing result when a steering corpus contains an invalid
    inclusion value.

    Requirement 4.4 states that when the inclusion validator reports one or more
    inclusion-mode failures it must produce an unsuccessful overall result so the
    CI gate does not pass. This suite runs each validator over a corpus whose
    single steering file declares the removed ``inclusion: auto`` value and
    asserts the validator's overall verdict is non-passing:

    - ``lint_steering.run_all_checks`` is the exact routine ``main()`` wraps with
      ``sys.exit(exit_code)``; a returned ``exit_code`` of ``0`` would let CI
      pass, so a non-zero code is asserted and the inclusion failure is confirmed
      present among the reported violations.
    - ``validate_power.check_steering_files`` records failures into the module
      ``errors`` list; a non-empty ``errors`` list is precisely the condition
      under which ``validate_power.main()`` calls ``sys.exit(1)``, so recording a
      failure that names the offending file (and value) demonstrates the
      non-passing result.

    These are example/unit checks (no generated inputs), complementing the
    property-based acceptance/parity suites above.

    Validates: Requirements 4.4
    """

    def test_lint_steering_returns_nonzero_exit_on_invalid_file(self) -> None:
        """``run_all_checks`` yields a non-zero exit code for an invalid file."""
        tmp = Path(tempfile.mkdtemp())
        try:
            steering_dir, hooks_dir, index_path = _stage_lint_corpus(tmp)

            violations, exit_code = run_all_checks(steering_dir, hooks_dir, index_path)

            assert exit_code != 0, (
                "lint_steering.run_all_checks returned a passing exit code for a "
                f"corpus containing an inclusion: {INVALID_INCLUSION_VALUE} file"
            )
            invalid_path = str(steering_dir / STEERING_FILENAME)
            inclusion_errors = [
                v
                for v in violations
                if v.level == "ERROR"
                and v.file == invalid_path
                and INVALID_INCLUSION_VALUE in v.message
            ]
            assert inclusion_errors, (
                "lint_steering did not report an ERROR naming the offending file "
                f"and value {INVALID_INCLUSION_VALUE!r}: "
                f"{[v.format() for v in violations]}"
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_validate_power_records_failure_forcing_nonzero_exit(self) -> None:
        """``check_steering_files`` records a failure that forces a non-passing run."""
        tmp = Path(tempfile.mkdtemp())
        try:
            steering_dir = tmp / "steering"
            _materialize_steering_file(steering_dir, "auto", INVALID_INCLUSION_VALUE)

            failures = _validate_power_failures(tmp)

            file_failures = [m for m in failures if STEERING_FILENAME in m]
            assert file_failures, (
                "validate_power recorded no failure naming "
                f"{STEERING_FILENAME} for an inclusion: {INVALID_INCLUSION_VALUE} "
                f"file (a non-empty errors list is what drives main()'s "
                f"sys.exit(1)): {failures}"
            )
            assert any(INVALID_INCLUSION_VALUE in m for m in file_failures), (
                "validate_power failure did not name the offending value "
                f"{INVALID_INCLUSION_VALUE!r}: {file_failures}"
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
