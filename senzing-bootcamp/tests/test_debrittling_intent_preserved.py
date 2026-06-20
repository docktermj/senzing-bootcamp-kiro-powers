"""Documentation-review tests that remediated assertions preserve original intent.

Task 11.2 of the ``test-suite-debrittling`` spec. The remediation tasks (7.1, 8.1,
8.2, 9.1) replaced brittle assertions — exact total-test counts, whole-file/section
SHA-256 snapshots, and exact heading/line-sequence snapshots — with structural
assertions. Each remediation was required to **preserve the original guarded intent**
as a comment or docstring (Requirements 4.2 and 6.2) rather than silently dropping it.

These tests are a non-automated documentation review turned into an executable guard:
for each remediated file they assert that the file still carries (a) the
structural-replacement markers it now uses and (b) intent-preserving documentation that
names what the original count/snapshot/sequence assertion was protecting and why the
structural check replaced it. The phrase checks are tolerant of benign wording changes
(each required concept is satisfied by any one of several alternative phrasings) but
specific enough to fail if the intent-preserving documentation were stripped out.

**Validates: Requirements 4.2, 6.2**
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# This file lives in senzing-bootcamp/tests/; remediated files are siblings.
_TESTS_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class RemediatedFile:
    """A remediated test file and the intent-preservation it must document.

    Attributes:
        filename: The remediated test file's name (resolved under ``_TESTS_DIR``).
        kind: A short label for the remediation category (for readable test ids).
        intent_groups: A tuple of phrase groups. Each group is a tuple of
            alternative phrases; the file must contain at least one phrase from
            every group (case-insensitively). Grouping the alternatives keeps the
            check tolerant of wording changes while still failing if a whole
            intent-preservation concept is removed.
    """

    filename: str
    kind: str
    intent_groups: tuple[tuple[str, ...], ...]


# Each entry was derived by reading the remediated file and recording the
# structural-replacement markers and intent-preserving documentation the
# remediation actually left behind. Groups read as: "the file must explain
# <this concept> using at least one of these phrasings".
_REMEDIATED_FILES: tuple[RemediatedFile, ...] = (
    # Task 7.1 (count) + Task 8.1 (whole-file snapshot) remediation.
    RemediatedFile(
        filename="test_onboarding_split_preservation.py",
        kind="count+whole_file",
        intent_groups=(
            # Names the structural replacement that took over from the snapshot.
            ("structural replacement", "asserted structurally", "structural check"),
            # Names the brittle thing being replaced.
            ("whole-file sha-256 snapshot", "byte-for-byte", "byte-identical"),
            # Count remediation: non-regression floor preserves the count intent.
            ("non-regression floor", "non-regression", "below the floor"),
            # Original intent is explicitly named.
            ("original intent", "the real invariant", "tests-only"),
        ),
    ),
    # Task 8.1 (whole-file snapshot) remediation.
    RemediatedFile(
        filename="test_module3_visualization_no_skip_preservation.py",
        kind="whole_file",
        intent_groups=(
            ("structural replacement", "structural marker", "structural markers"),
            ("whole-file sha-256 digest", "byte-for-byte"),
            # Names what the snapshot was guarding (a fix reaching out of scope).
            ("out-of-scope", "out of scope", "outside its scope"),
            ("the original guard", "the bug condition guarded", "still detected",
             "still caught"),
        ),
    ),
    # Task 8.2 (section snapshot) remediation.
    RemediatedFile(
        filename="test_always_create_completion_summary_preservation.py",
        kind="section_snapshot",
        intent_groups=(
            ("section content invariant", "section-content invariant"),
            ("sha-256 byte-identity", "sha-256 snapshot", "byte-identity"),
            # Cites the taxonomy policy that defines the replacement form.
            ("brittle_assertion_taxonomy.md",),
            ("original intent", "baseline behavior", "guarded behavior",
             "the behavior the original"),
        ),
    ),
    # Task 9.1 (exact heading-sequence snapshot) + Task 8.1 (whole-file) remediation.
    RemediatedFile(
        filename="test_onboarding_question_ownership.py",
        kind="sequence+whole_file",
        intent_groups=(
            ("ordered-subsequence",),
            ("exact_sequence_snapshot", "full-list", "whole-file sha-256 snapshot"),
            ("required relative order", "relative order"),
            ("original intent", "the structural invariant being protected",
             "structural replacement"),
        ),
    ),
    # Task 9.1 (exact heading-sequence snapshot) + Task 8.1 (whole-file) remediation.
    RemediatedFile(
        filename="test_module_closing_question_ownership.py",
        kind="sequence+whole_file",
        intent_groups=(
            ("ordered-subsequence",),
            ("exact_sequence_snapshot", "full-list", "whole-file sha-256 snapshot"),
            ("required relative order", "relative order"),
            ("original intent", "the behavioral invariants those snapshots were",
             "structural replacement", "structural marker"),
        ),
    ),
    # Task 9.1 (exact heading-sequence snapshot) remediation.
    RemediatedFile(
        filename="test_module2_license_question.py",
        kind="sequence",
        intent_groups=(
            ("ordered-subsequence",),
            ("exact_sequence_snapshot", "full-list"),
            ("required relative order", "relative order"),
            ("original intent", "the protected", "the protected invariant"),
        ),
    ),
)


def _read(filename: str) -> str:
    """Return the lower-cased UTF-8 text of a remediated test file.

    Args:
        filename: The file name under ``_TESTS_DIR``.

    Returns:
        The file's contents, lower-cased for case-insensitive phrase matching.
    """
    return (_TESTS_DIR / filename).read_text(encoding="utf-8").lower()


# Flattened (file, group) pairs so each missing concept is a distinct failure.
_FILE_GROUP_PARAMS = [
    pytest.param(rf, group, id=f"{rf.filename}::{rf.kind}::group{idx}")
    for rf in _REMEDIATED_FILES
    for idx, group in enumerate(rf.intent_groups)
]


class TestRemediatedFilesExist:
    """Every remediated file named in the review is present and readable.

    A misnamed or deleted target would silently skip its intent checks, so the
    set of files is pinned here first.

    **Validates: Requirements 4.2, 6.2**
    """

    @pytest.mark.parametrize(
        "filename", sorted({rf.filename for rf in _REMEDIATED_FILES})
    )
    def test_remediated_file_present(self, filename: str) -> None:
        """The remediated file exists under the tests directory."""
        path = _TESTS_DIR / filename
        assert path.is_file(), f"Remediated test file missing: {filename}"
        assert path.read_text(encoding="utf-8").strip(), (
            f"Remediated test file is empty: {filename}"
        )


class TestPreservedIntentDocumented:
    """Each remediated assertion documents the original guarded intent.

    For every remediated file, each required intent-preservation concept (a phrase
    group) must be present via at least one of its accepted phrasings. This is the
    executable form of the Req 4.2 / Req 6.2 documentation review: removing the
    comment/docstring that names what the original count/snapshot/sequence assertion
    guarded makes the matching group fail.

    **Validates: Requirements 4.2, 6.2**
    """

    @pytest.mark.parametrize("rf, group", _FILE_GROUP_PARAMS)
    def test_intent_phrase_group_present(
        self, rf: RemediatedFile, group: tuple[str, ...]
    ) -> None:
        """At least one phrasing of each required intent concept is documented."""
        text = _read(rf.filename)
        assert any(phrase in text for phrase in group), (
            f"{rf.filename}: intent-preservation documentation missing.\n"
            f"Expected at least one of these phrasings: {list(group)}\n"
            "The remediation must preserve the original guarded intent as a "
            "comment or docstring (Req 4.2, 6.2)."
        )


class TestRemediationNamesReplacedAssertionKind:
    """Each remediated file names the brittle assertion kind it replaced.

    A lighter cross-cutting check: beyond the per-concept groups, every remediated
    file must explain *why* a structural check replaced the original — i.e. it must
    reference the snapshot / count / sequence (and the ``==`` equality it dropped or
    the SHA-256 digest it no longer pins). This guards against a future edit that
    keeps the structural markers but strips the "this replaced a brittle X" rationale.

    **Validates: Requirements 4.2, 6.2**
    """

    @pytest.mark.parametrize("rf", _REMEDIATED_FILES, ids=lambda rf: rf.filename)
    def test_names_original_brittle_assertion(self, rf: RemediatedFile) -> None:
        """The file references the original snapshot / count / sequence it replaced."""
        text = _read(rf.filename)
        rationale_phrases = (
            "snapshot",
            "sha-256",
            "non-regression",
            "exact_sequence_snapshot",
            "full-list",
            "baseline",
        )
        assert any(phrase in text for phrase in rationale_phrases), (
            f"{rf.filename}: missing the rationale naming the original brittle "
            "assertion (snapshot / count / sequence) that the structural check "
            "replaced (Req 4.2, 6.2)."
        )
