"""Property-based tests for TypeScript/Node.js language maturity alignment.

Validates structural parity across language steering files and ensures
TypeScript-specific maturity notes, pitfall coverage, and onboarding
disclaimers are present.

Feature: typescript-language-maturity
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"

_LANGUAGE_FILES: list[str] = [
    "lang-python.md",
    "lang-java.md",
    "lang-csharp.md",
    "lang-rust.md",
    "lang-typescript.md",
]

_REQUIRED_SECTION_HEADINGS: list[str] = [
    "## Senzing SDK Best Practices",
    "## Common Pitfalls",
    "## Performance Considerations",
    "## Code Style for Generated Code",
    "## Platform Notes",
    "## Common Environment Issues",
]

_REQUIRED_PLATFORMS: list[str] = ["linux", "windows", "macos"]


# ---------------------------------------------------------------------------
# Property 1: Language steering file structural parity
# ---------------------------------------------------------------------------


class TestLanguageSteeringStructuralParity:
    """Feature: typescript-language-maturity, Property 1: Language steering file structural parity

    For any language steering file in the set {lang-python.md, lang-java.md,
    lang-csharp.md, lang-rust.md, lang-typescript.md}, it SHALL contain all
    required section headings AND the Platform Notes section SHALL reference
    at least Linux, Windows, and macOS.

    **Validates: Requirements 1, 5**
    """

    @given(lang_file=st.sampled_from(_LANGUAGE_FILES))
    @settings(max_examples=10)
    def test_required_section_headings_present(self, lang_file: str) -> None:
        """Every language file contains all required section headings.

        Args:
            lang_file: Language steering filename drawn from the set.
        """
        file_path = _STEERING_DIR / lang_file
        content = file_path.read_text(encoding="utf-8")

        missing_headings: list[str] = []
        for heading in _REQUIRED_SECTION_HEADINGS:
            if heading not in content:
                missing_headings.append(heading)

        assert missing_headings == [], (
            f"{lang_file} is missing required section headings: "
            f"{missing_headings}"
        )

    @given(lang_file=st.sampled_from(_LANGUAGE_FILES))
    @settings(max_examples=10)
    def test_platform_notes_references_all_platforms(self, lang_file: str) -> None:
        """Platform Notes section references Linux, Windows, and macOS.

        Args:
            lang_file: Language steering filename drawn from the set.
        """
        file_path = _STEERING_DIR / lang_file
        content = file_path.read_text(encoding="utf-8")

        # Extract the Platform Notes section content
        platform_section_match = re.search(
            r"## Platform Notes\s*\n(.*?)(?=\n## |\Z)",
            content,
            re.DOTALL,
        )

        assert platform_section_match is not None, (
            f"{lang_file} is missing ## Platform Notes section"
        )

        platform_content = platform_section_match.group(1).lower()

        missing_platforms: list[str] = []
        for platform in _REQUIRED_PLATFORMS:
            if platform not in platform_content:
                missing_platforms.append(platform)

        assert missing_platforms == [], (
            f"{lang_file} Platform Notes section is missing references to: "
            f"{missing_platforms}"
        )


# ---------------------------------------------------------------------------
# Path constants (Property 2)
# ---------------------------------------------------------------------------

_POWER_ROOT: Path = Path(__file__).resolve().parent.parent

_MATURITY_NOTE_FILES: dict[str, Path] = {
    "lang-typescript.md": _STEERING_DIR / "lang-typescript.md",
    "POWER.md": _POWER_ROOT / "POWER.md",
}


# ---------------------------------------------------------------------------
# Property 2: Maturity notes presence in designated files
# ---------------------------------------------------------------------------


class TestMaturityNotesPresence:
    """Feature: typescript-language-maturity, Property 2: Maturity notes presence in designated files

    For any file in the set {lang-typescript.md, POWER.md}, it SHALL contain
    a support depth or maturity note that acknowledges varying `find_examples`
    coverage across languages.

    **Validates: Requirements 2**
    """

    @given(file_name=st.sampled_from(list(_MATURITY_NOTE_FILES.keys())))
    @settings(max_examples=10)
    def test_find_examples_coverage_note_present(self, file_name: str) -> None:
        """Each designated file contains a maturity/coverage note referencing find_examples.

        Args:
            file_name: Filename drawn from the maturity note file set.
        """
        file_path = _MATURITY_NOTE_FILES[file_name]
        content = file_path.read_text(encoding="utf-8")

        # Must reference find_examples
        assert re.search(r"find_examples", content), (
            f"{file_name} does not reference `find_examples`"
        )

        # Must contain coverage/maturity/depth language acknowledging variation
        coverage_pattern = re.compile(
            r"(coverage|maturity|depth)\b.*\b(var|differ|fewer|extensive)",
            re.IGNORECASE | re.DOTALL,
        )
        assert coverage_pattern.search(content), (
            f"{file_name} does not contain coverage/maturity/depth language "
            f"acknowledging varying find_examples support"
        )


# ---------------------------------------------------------------------------
# Unit Test: common-pitfalls.md TypeScript section heading
# ---------------------------------------------------------------------------


class TestCommonPitfallsTypeScriptSection:
    """Unit test verifying common-pitfalls.md contains a TypeScript/Node.js Pitfalls heading.

    **Validates: Requirements 4**
    """

    def test_typescript_section_heading_present(self) -> None:
        """common-pitfalls.md contains the ## TypeScript/Node.js Pitfalls heading."""
        file_path = _STEERING_DIR / "common-pitfalls.md"
        content = file_path.read_text(encoding="utf-8")

        assert "## TypeScript/Node.js Pitfalls" in content, (
            "common-pitfalls.md is missing the '## TypeScript/Node.js Pitfalls' heading"
        )


# ---------------------------------------------------------------------------
# Required pitfall topics and their keyword patterns
# ---------------------------------------------------------------------------

_PITFALL_TOPICS: list[str] = [
    "async patterns",
    "type definitions",
    "ESM/CJS module resolution",
]

_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "async patterns": ["promise", "async", "event loop"],
    "type definitions": ["any", "type", "strict"],
    "ESM/CJS module resolution": ["esm", "cjs", "import", "require", "module"],
}


# ---------------------------------------------------------------------------
# Property 3: TypeScript pitfall topic coverage
# ---------------------------------------------------------------------------


class TestTypeScriptPitfallTopicCoverage:
    """Feature: typescript-language-maturity, Property 3: TypeScript pitfall topic coverage

    For any required TypeScript pitfall topic in the set {async patterns,
    type definitions, ESM/CJS module resolution}, the common-pitfalls.md
    TypeScript/Node.js section SHALL contain an entry addressing that topic.

    **Validates: Requirements 4**
    """

    @given(topic=st.sampled_from(_PITFALL_TOPICS))
    @settings(max_examples=10)
    def test_pitfall_section_covers_topic(self, topic: str) -> None:
        """TypeScript/Node.js pitfall section contains an entry for each topic.

        Args:
            topic: Required pitfall topic drawn from the set.
        """
        pitfalls_path = _STEERING_DIR / "common-pitfalls.md"
        content = pitfalls_path.read_text(encoding="utf-8")

        # Extract the TypeScript/Node.js Pitfalls section
        ts_section_match = re.search(
            r"## TypeScript/Node\.js Pitfalls\s*\n(.*?)(?=\n## |\Z)",
            content,
            re.DOTALL,
        )

        assert ts_section_match is not None, (
            "common-pitfalls.md is missing ## TypeScript/Node.js Pitfalls section"
        )

        section_content = ts_section_match.group(1).lower()

        # Check that at least one keyword for this topic appears in the section
        keywords = _TOPIC_KEYWORDS[topic]
        matched = [kw for kw in keywords if kw in section_content]

        assert matched, (
            f"TypeScript/Node.js Pitfalls section does not cover topic "
            f"'{topic}'. Expected at least one of {keywords} to appear."
        )


# ---------------------------------------------------------------------------
# Unit Test: Onboarding disclaimer presence (Task 6.4)
# ---------------------------------------------------------------------------


class TestOnboardingDisclaimerPresence:
    """Unit test verifying onboarding-flow.md Step 2 contains the support depth disclaimer.

    The disclaimer must appear within the Step 2 (Programming Language Selection)
    section and acknowledge that `find_examples` depth varies across languages
    while `generate_scaffold` produces working code for all.

    **Validates: Requirements 6**
    """

    def _get_step2_content(self) -> str:
        """Extract Step 2 section content from onboarding-flow.md."""
        file_path = _STEERING_DIR / "onboarding-flow.md"
        content = file_path.read_text(encoding="utf-8")

        step2_match = re.search(
            r"## 2\. Programming Language Selection\s*\n(.*?)(?=\n## \d|\Z)",
            content,
            re.DOTALL,
        )
        assert step2_match is not None, (
            "onboarding-flow.md is missing '## 2. Programming Language Selection' section"
        )
        return step2_match.group(1)

    def test_disclaimer_contains_find_examples_reference(self) -> None:
        """Step 2 disclaimer mentions find_examples tool."""
        step2_content = self._get_step2_content()
        assert "find_examples" in step2_content, (
            "Step 2 disclaimer must reference `find_examples`"
        )

    def test_disclaimer_contains_generate_scaffold_reference(self) -> None:
        """Step 2 disclaimer mentions generate_scaffold tool."""
        step2_content = self._get_step2_content()
        assert "generate_scaffold" in step2_content, (
            "Step 2 disclaimer must reference `generate_scaffold`"
        )

    def test_disclaimer_contains_coverage_variation_language(self) -> None:
        """Step 2 disclaimer acknowledges coverage variation across languages."""
        step2_content = self._get_step2_content()
        # Match phrases indicating coverage varies (e.g., "may vary", "varies",
        # "most extensive example coverage")
        coverage_pattern = re.compile(
            r"(vary|varies|coverage|depth of supplementary examples)",
            re.IGNORECASE,
        )
        assert coverage_pattern.search(step2_content), (
            "Step 2 disclaimer must contain language about coverage variation "
            "(e.g., 'vary', 'coverage', 'depth of supplementary examples')"
        )
