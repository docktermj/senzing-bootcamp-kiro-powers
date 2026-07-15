"""Relative-order tests for the preface-flow-and-banners feature.

Validates the reordered Preface sequence introduced by the
``.kiro/specs/preface-flow-and-banners`` feature. After tasks 2.1-2.4,
``Track_Selection``, ``Language_Selection``, and the ``Any_Questions_Step``
(comprehension check) all live in
``senzing-bootcamp/steering/onboarding-phase2-track-setup.md`` in that order.
The core invariant this module guards is the RELATIVE ORDER of those three
prompts (Req 3.1, 3.3, 3.4, 6.1):

    Track_Selection  <  Language_Selection  <  Any_Questions_Step

Because all three now live in the same phase-2 file, the ordering is asserted
by comparing the character index of each heading within that single file
(Req 3.3: Track before Language; Req 3.4: Any_Questions after Language). A
supplementary cross-file check (Req 6.1) guards against a regression that
reintroduces ``Language_Selection`` into phase 1b (before the welcome banner),
by asserting the phase-1b file no longer carries a "Programming Language
Selection" heading.

Matching choice: each prompt is located by an anchored heading regex
(``re.MULTILINE``) that matches the descriptive heading text
("Track Selection", "Programming Language Selection", "Comprehension Check")
with an OPTIONAL numeric/letter prefix (e.g. ``5.``, ``5a.``, ``5b.``). This
matches on the heading LINE — not incidental prose — while staying resilient
to future heading-number changes; the ordering assertion is the key invariant
and fails clearly if the sequence regresses.

The tests are stdlib-only (``pathlib``, ``re``) and example-based — there is a
single fixed input file per assertion, so Hypothesis-style property-based
testing would add noise without coverage. Pytest discovers the class via
standard collection.
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Module-level path constants (resolved relative to this test file, never
# hardcoded absolute paths). This file lives at
# ``senzing-bootcamp/tests/test_preface_order.py`` so ``parents[2]`` is the
# repository root — matching the pattern used by peer tests such as
# ``test_preface_banners.py`` and ``test_entity_resolution_intro_structure.py``.
# ---------------------------------------------------------------------------
#: Repository root — parent of the ``senzing-bootcamp/`` power directory.
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

#: The steering directory that holds the reordered phase ``.md`` files.
STEERING_DIR: Path = REPO_ROOT / "senzing-bootcamp" / "steering"

#: Phase 2 — now owns Track_Selection, Language_Selection, and the
#: Any_Questions_Step (comprehension check), in that order.
PHASE2_FILE: Path = STEERING_DIR / "onboarding-phase2-track-setup.md"

#: Phase 1b — after the reorder, no longer owns Language_Selection; it holds
#: the ER intro handoff, the Welcome_Banner, and the verbosity step.
PHASE1B_FILE: Path = STEERING_DIR / "onboarding-phase1b-intro-language.md"

# ---------------------------------------------------------------------------
# Anchored heading patterns (Req 3.3, 3.4). Each matches a level-2/3 heading
# line whose descriptive text names the prompt, with an OPTIONAL numeric/letter
# prefix (``5.``, ``5a.``, ``5b.``) so a future renumbering does not break the
# order assertion. ``re.MULTILINE`` anchors ``^``/``$`` to line boundaries so
# the match is on the heading line, not incidental prose.
# ---------------------------------------------------------------------------
#: Optional heading numbering such as ``5. `` or ``5a. `` before the title.
_NUM_PREFIX = r"(?:[0-9]+[a-z]?\.\s+)?"

#: Track_Selection heading (e.g. ``## 5. Track Selection``).
TRACK_HEADING = re.compile(
    rf"^#{{2,3}}\s+{_NUM_PREFIX}Track Selection\s*$", re.MULTILINE
)

#: Language_Selection heading (e.g. ``## 5a. Programming Language Selection``).
LANGUAGE_HEADING = re.compile(
    rf"^#{{2,3}}\s+{_NUM_PREFIX}Programming Language Selection\s*$", re.MULTILINE
)

#: Any_Questions_Step / comprehension-check heading (e.g. ``### 5b. Comprehension Check``).
COMPREHENSION_HEADING = re.compile(
    rf"^#{{2,3}}\s+{_NUM_PREFIX}Comprehension Check\s*$", re.MULTILINE
)


class TestPrefaceOrder:
    """Relative-order invariants for the reordered Preface sequence.

    Guards the ``Track_Selection < Language_Selection < Any_Questions_Step``
    ordering so a future edit cannot silently regress the sequence (e.g. by
    moving language selection back ahead of track selection, or the
    comprehension check ahead of language selection).
    """

    def test_track_before_language_before_comprehension(self) -> None:
        """Validates: Requirements 3.1, 3.3, 3.4, 6.1.

        Asserts that within ``onboarding-phase2-track-setup.md`` the
        Track_Selection heading precedes the Language_Selection heading
        (Req 3.3), which precedes the Comprehension Check / Any_Questions_Step
        heading (Req 3.4) — capturing the "Track before Language before
        Any_Questions" invariant of the reordered Preface (Req 3.1, 6.1).

        Each prompt is located by its anchored descriptive heading regex
        (``re.MULTILINE``), so the check matches on the heading line and is
        resilient to future heading-number changes.
        """
        text = PHASE2_FILE.read_text(encoding="utf-8")
        rel = PHASE2_FILE.relative_to(REPO_ROOT)

        track = TRACK_HEADING.search(text)
        language = LANGUAGE_HEADING.search(text)
        comprehension = COMPREHENSION_HEADING.search(text)

        assert track is not None, (
            f"Expected a 'Track Selection' heading in {rel} "
            "(Req 3.3); none found on its own line."
        )
        assert language is not None, (
            f"Expected a 'Programming Language Selection' heading in {rel} "
            "(Req 3.3); none found on its own line."
        )
        assert comprehension is not None, (
            f"Expected a 'Comprehension Check' heading (Any_Questions_Step) in "
            f"{rel} (Req 3.4); none found on its own line."
        )

        assert track.start() < language.start(), (
            "Expected Track_Selection to precede Language_Selection in "
            f"{rel} (Req 3.3); Track Selection heading at index "
            f"{track.start()} is not before Programming Language Selection "
            f"heading at index {language.start()}."
        )
        assert language.start() < comprehension.start(), (
            "Expected Language_Selection to precede the Any_Questions_Step "
            f"(Comprehension Check) in {rel} (Req 3.4); Programming Language "
            f"Selection heading at index {language.start()} is not before the "
            f"Comprehension Check heading at index {comprehension.start()}."
        )

    def test_phase1b_no_longer_owns_language_selection(self) -> None:
        """Validates: Requirement 6.1 (cross-file regression guard).

        Asserts that ``onboarding-phase1b-intro-language.md`` no longer carries
        a "Programming Language Selection" heading, guarding against a
        regression that reintroduces Language_Selection into phase 1b (before
        the Welcome_Banner). Since Track, Language, and the comprehension check
        now all live in phase 2, this cross-file check backstops the within-file
        order assertion for the "Language after the Welcome_Banner" invariant.
        """
        text = PHASE1B_FILE.read_text(encoding="utf-8")
        rel = PHASE1B_FILE.relative_to(REPO_ROOT)

        match = LANGUAGE_HEADING.search(text)
        assert match is None, (
            "Expected NO 'Programming Language Selection' heading in "
            f"{rel} (Req 6.1) — Language_Selection moved to phase 2; found one "
            f"at index {match.start() if match else -1}, which would reintroduce "
            "language selection ahead of the welcome banner."
        )
