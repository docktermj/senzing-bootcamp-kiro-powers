"""Banner-presence tests for the preface-flow-and-banners feature.

Validates that the two new Banner_Blocks introduced by the
``.kiro/specs/preface-flow-and-banners`` feature are present, correctly
titled, and correctly bordered in their steering files:

- **ER_Concepts_Banner** — appears at the START of
  ``senzing-bootcamp/steering/entity-resolution-intro.md`` (Req 6.2).
- **Graduation_Banner** — appears in BOTH
  ``senzing-bootcamp/steering/graduation.md`` AND
  ``senzing-bootcamp/steering/module-completion-track.md`` (Req 6.3).

Each banner must follow the Banner_Block structure from Requirement 4:
exactly three lines — a top border, an emoji-decorated title, and a bottom
border (Req 4.1); each border is exactly 56 ``\u2501`` (U+2501 heavy
horizontal) characters (Req 4.2); the title uses a three-emoji prefix and
suffix separated from the title text by two spaces on each side (Req 4.3);
and when shown as a display template the block is wrapped in a ``text``
fenced code block (Req 4.4).

The tests are stdlib-only (``pathlib``, ``re``) and example-based — there is
a single fixed input file per assertion, so Hypothesis-style property-based
testing would add noise without coverage. Pytest discovers the class via
standard collection.
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Module-level path constants (resolved relative to this test file, never
# hardcoded absolute paths). This file lives at
# ``senzing-bootcamp/tests/test_preface_banners.py`` so ``parents[2]`` is the
# repository root — matching the pattern used by peer tests such as
# ``test_entity_resolution_intro_structure.py``.
# ---------------------------------------------------------------------------
#: Repository root — parent of the ``senzing-bootcamp/`` power directory.
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

#: The steering directory that holds the banner-bearing ``.md`` files.
STEERING_DIR: Path = REPO_ROOT / "senzing-bootcamp" / "steering"

#: The entity-resolution introduction file that opens with the ER_Concepts_Banner.
ER_INTRO_FILE: Path = STEERING_DIR / "entity-resolution-intro.md"

#: The graduation workflow file that opens with the Graduation_Banner.
GRADUATION_FILE: Path = STEERING_DIR / "graduation.md"

#: The track-completion file that also displays the Graduation_Banner, so a
#: bootcamper who declines graduation still sees it.
TRACK_COMPLETION_FILE: Path = STEERING_DIR / "module-completion-track.md"

# ---------------------------------------------------------------------------
# Banner literals (Requirement 4). The border is exactly 56 U+2501 characters
# (Req 4.2). The title lines use a three-emoji prefix/suffix separated from the
# title by two spaces on each side (Req 4.3).
# ---------------------------------------------------------------------------
#: The exact 56-character heavy-horizontal border line (Req 4.2).
BORDER: str = "\u2501" * 56

#: The ER_Concepts_Banner title line (Req 4.3): three puzzle emoji, two spaces,
#: ``ENTITY RESOLUTION CONCEPTS``, two spaces, three puzzle emoji.
ER_TITLE: str = (
    "\U0001f9e9\U0001f9e9\U0001f9e9  ENTITY RESOLUTION CONCEPTS  "
    "\U0001f9e9\U0001f9e9\U0001f9e9"
)

#: The Graduation_Banner title line (Req 4.3): three graduation-cap emoji, two
#: spaces, ``GRADUATION``, two spaces, three graduation-cap emoji.
GRAD_TITLE: str = "\U0001f393\U0001f393\U0001f393  GRADUATION  \U0001f393\U0001f393\U0001f393"


def _fenced_block(title: str) -> str:
    """Return the exact ``text``-fenced Banner_Block for the given title.

    The returned string is the full four-structural-element display template
    that must appear verbatim in a steering file: an opening ````text`` fence,
    the top border, the title line, the bottom border, and the closing fence.
    Asserting this whole block is present (rather than the pieces separately)
    exercises Req 4.1 (three lines: border / title / border), Req 4.2 (56-char
    borders), Req 4.3 (emoji-decorated title), and Req 4.4 (``text`` fence) at
    once, and fails if a banner is removed, mis-titled, or has a wrong-length
    border.

    Args:
        title: The banner title line (``ER_TITLE`` or ``GRAD_TITLE``).

    Returns:
        The exact fenced Banner_Block string, including the enclosing fences.
    """
    return f"```text\n{BORDER}\n{title}\n{BORDER}\n```"


class TestBannerPresence:
    """Banner-presence invariants for the preface-flow-and-banners feature.

    Guards the two new Banner_Blocks so a future edit cannot silently drop a
    banner, mistype its title, or break its 56-character border geometry.
    """

    def test_er_concepts_banner_present(self) -> None:
        """Validates: Requirements 6.2, 4.1, 4.2, 4.3, 4.4.

        Asserts the ER_Concepts_Banner appears in
        ``entity-resolution-intro.md`` as a complete ``text``-fenced
        Banner_Block: a 56-``\u2501`` top border, the exact title line
        ``\U0001f9e9\U0001f9e9\U0001f9e9  ENTITY RESOLUTION CONCEPTS
        \U0001f9e9\U0001f9e9\U0001f9e9``, and a 56-``\u2501`` bottom border,
        in that order and adjacency.
        """
        text = ER_INTRO_FILE.read_text(encoding="utf-8")
        rel = ER_INTRO_FILE.relative_to(REPO_ROOT)

        assert BORDER in text, (
            f"Expected a 56-character U+2501 border line in {rel} "
            "(Req 4.2); none found — the ER_Concepts_Banner border is "
            "missing or the wrong length."
        )
        assert ER_TITLE in text, (
            f"Expected the exact ER_Concepts_Banner title line "
            f"{ER_TITLE!r} in {rel} (Req 4.3); not found."
        )
        assert _fenced_block(ER_TITLE) in text, (
            "Expected the complete text-fenced ER_Concepts_Banner block "
            f"(border / title / border in a ```text fence) in {rel} "
            "(Req 4.1, 4.2, 4.3, 4.4); the block is missing, out of order, "
            "or has a wrong-length border."
        )

    def test_er_concepts_banner_at_start_before_first_heading(self) -> None:
        """Validates: Requirement 6.2 (banner at the START of ER_Introduction).

        Asserts the ER_Concepts_Banner title line appears BEFORE the first
        ``## `` conceptual prose heading (e.g. ``## What entity resolution
        is``) in ``entity-resolution-intro.md``, so the banner is the first
        signposted output of the entity-resolution introduction rather than
        buried below the prose.
        """
        text = ER_INTRO_FILE.read_text(encoding="utf-8")
        rel = ER_INTRO_FILE.relative_to(REPO_ROOT)

        title_index = text.find(ER_TITLE)
        assert title_index != -1, (
            f"Expected the ER_Concepts_Banner title line in {rel} "
            "(Req 6.2); not found."
        )

        first_heading = re.search(r"^## .+$", text, re.MULTILINE)
        assert first_heading is not None, (
            f"Expected at least one '## ' conceptual heading in {rel} "
            "to anchor the 'banner comes first' check."
        )

        assert title_index < first_heading.start(), (
            "Expected the ER_Concepts_Banner to appear at the START of "
            f"{rel} — before the first '## ' heading "
            f"({first_heading.group(0)!r}) (Req 6.2); the banner title was "
            f"found at index {title_index}, after the heading at index "
            f"{first_heading.start()}."
        )

    def test_graduation_banner_in_graduation_workflow(self) -> None:
        """Validates: Requirements 6.3, 4.1, 4.2, 4.3, 4.4.

        Asserts the Graduation_Banner appears in ``graduation.md`` as a
        complete ``text``-fenced Banner_Block: a 56-``\u2501`` top border,
        the exact title line
        ``\U0001f393\U0001f393\U0001f393  GRADUATION
        \U0001f393\U0001f393\U0001f393``, and a 56-``\u2501`` bottom border,
        in that order and adjacency.
        """
        text = GRADUATION_FILE.read_text(encoding="utf-8")
        rel = GRADUATION_FILE.relative_to(REPO_ROOT)

        assert BORDER in text, (
            f"Expected a 56-character U+2501 border line in {rel} "
            "(Req 4.2); none found — the Graduation_Banner border is "
            "missing or the wrong length."
        )
        assert GRAD_TITLE in text, (
            f"Expected the exact Graduation_Banner title line "
            f"{GRAD_TITLE!r} in {rel} (Req 4.3); not found."
        )
        assert _fenced_block(GRAD_TITLE) in text, (
            "Expected the complete text-fenced Graduation_Banner block "
            f"(border / title / border in a ```text fence) in {rel} "
            "(Req 4.1, 4.2, 4.3, 4.4); the block is missing, out of order, "
            "or has a wrong-length border."
        )

    def test_graduation_banner_in_track_completion(self) -> None:
        """Validates: Requirements 6.3, 4.1, 4.2, 4.3, 4.4.

        Asserts the Graduation_Banner also appears in
        ``module-completion-track.md`` as a complete ``text``-fenced
        Banner_Block, so a bootcamper who declines graduation (or has
        ``skip_graduation`` set) still sees the banner at track completion.
        """
        text = TRACK_COMPLETION_FILE.read_text(encoding="utf-8")
        rel = TRACK_COMPLETION_FILE.relative_to(REPO_ROOT)

        assert BORDER in text, (
            f"Expected a 56-character U+2501 border line in {rel} "
            "(Req 4.2); none found — the Graduation_Banner border is "
            "missing or the wrong length."
        )
        assert GRAD_TITLE in text, (
            f"Expected the exact Graduation_Banner title line "
            f"{GRAD_TITLE!r} in {rel} (Req 4.3); not found."
        )
        assert _fenced_block(GRAD_TITLE) in text, (
            "Expected the complete text-fenced Graduation_Banner block "
            f"(border / title / border in a ```text fence) in {rel} "
            "(Req 4.1, 4.2, 4.3, 4.4); the block is missing, out of order, "
            "or has a wrong-length border."
        )
