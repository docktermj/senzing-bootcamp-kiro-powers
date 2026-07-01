"""Property-based test for the absent/whitespace response placeholder.

Feature: recap-qr-formatting

Validates Property 3 from the design against the Paired_Schema formatting
helper ``format_qr_pair`` in ``recap_pdf_render.py``. When a QR_Pair's response
is absent (empty/``None``) or contains only whitespace, the emitted
Response_Item must carry the literal ``(no response recorded)`` placeholder
immediately after the ``- **R:**`` prefix.

**Validates: Requirements 1.6**
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from recap_pdf_render import format_qr_pair

# The literals the Paired_Schema Response_Item must carry for absent/whitespace
# responses (Requirement 1.6).
_RESPONSE_PREFIX = "- **R:** "
_NO_RESPONSE_PLACEHOLDER = "(no response recorded)"


# ---------------------------------------------------------------------------
# Strategies (st_ prefix per python-conventions)
# ---------------------------------------------------------------------------


def st_substantive_question() -> st.SearchStrategy[str]:
    """Generate a substantive, Latin-1-safe question.

    A substantive question has at least one non-whitespace character after
    leading/trailing whitespace is stripped. Text is constrained to the
    Latin-1 range (0..255) so it matches the renderer's core-font contract.

    Returns:
        A strategy producing non-whitespace-only, Latin-1-safe question text.
    """
    return st.text(
        alphabet=st.characters(min_codepoint=0x21, max_codepoint=0xFF),
        min_size=1,
        max_size=120,
    )


def st_whitespace_response() -> st.SearchStrategy[str | None]:
    """Generate an absent or whitespace-only response.

    Covers ``None`` (absent), the empty string, and strings composed solely of
    ASCII/Unicode whitespace characters that ``str.strip()`` removes entirely.

    Returns:
        A strategy producing absent or whitespace-only responses.
    """
    whitespace_text = st.text(
        alphabet=st.sampled_from([" ", "\t", "\n", "\r", "\f", "\v", "\u00a0"]),
        min_size=0,
        max_size=20,
    )
    return st.one_of(st.none(), whitespace_text)


# ---------------------------------------------------------------------------
# Property 3: Absent or whitespace responses render the placeholder
# ---------------------------------------------------------------------------


class TestQRPlaceholder:
    """Absent/whitespace responses render the ``(no response recorded)`` placeholder.

    **Validates: Requirements 1.6**

    For any QR_Pair whose response is absent or contains only whitespace, the
    emitted Response_Item — after its leading indentation — is exactly
    ``- **R:** (no response recorded)``.
    """

    # Feature: recap-qr-formatting, Property 3: Absent or whitespace responses
    # render the placeholder.
    @given(question=st_substantive_question(), response=st_whitespace_response())
    def test_absent_or_whitespace_response_renders_placeholder(
        self, question: str, response: str | None
    ) -> None:
        """The Response_Item carries ``(no response recorded)`` after the prefix.

        **Validates: Requirements 1.6**
        """
        lines = format_qr_pair(question, response)

        # A whitespace-only/absent response collapses to the single-line
        # placeholder, so the pair is exactly the Question_Item + one
        # Response_Item.
        assert len(lines) == 2

        response_line = lines[1]
        # Strip only the leading indentation (ASCII spaces) before inspecting
        # the Response_Item content.
        content = response_line.lstrip(" ")
        assert content == f"{_RESPONSE_PREFIX}{_NO_RESPONSE_PLACEHOLDER}"
        # The placeholder appears immediately after the `- **R:**` prefix.
        assert content == "- **R:** (no response recorded)"
