"""Property-based tests for test-data terminology invariants.

These tests verify that the senzing-bootcamp power does not contain
any residual references to the old "mock" + "data" terminology.

Feature: test-data-terminology
"""

from __future__ import annotations

from pathlib import Path

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent

# The forbidden phrase, constructed to avoid self-matching
_FORBIDDEN_PHRASE = "mock" + " " + "data"


# ---------------------------------------------------------------------------
# File collection helpers
# ---------------------------------------------------------------------------


def _collect_files(extensions: tuple[str, ...]) -> list[Path]:
    """Collect all files with given extensions under the bootcamp directory.

    Args:
        extensions: Tuple of file extensions to match (e.g., (".md", ".py")).

    Returns:
        Sorted list of Path objects matching the extensions.
    """
    files: list[Path] = []
    for ext in extensions:
        files.extend(_BOOTCAMP_DIR.rglob(f"*{ext}"))
    # Exclude __pycache__ and .pytest_cache directories
    files = [
        f for f in files
        if "__pycache__" not in str(f) and ".pytest_cache" not in str(f)
    ]
    return sorted(files)


_TARGET_EXTENSIONS = (".md", ".py", ".yaml")
_TARGET_FILES = _collect_files(_TARGET_EXTENSIONS)


def _collect_all_files() -> list[Path]:
    """Collect all files under the bootcamp directory regardless of extension.

    Returns:
        Sorted list of all file Path objects.
    """
    files = [
        f for f in _BOOTCAMP_DIR.rglob("*")
        if f.is_file()
        and "__pycache__" not in str(f)
        and ".pytest_cache" not in str(f)
    ]
    return sorted(files)


_ALL_FILES = _collect_all_files()


# ---------------------------------------------------------------------------
# Property 1 — No old terminology in file content
# ---------------------------------------------------------------------------


class TestNoMockDataInContent:
    """PBT — No file contains the forbidden old terminology (case-insensitive).

    **Validates: Requirements 1.1, 1.3, 2.1, 2.2, 2.3, 3.2, 4.2, 5.1**

    For any file with extension .md, .py, or .yaml within the
    senzing-bootcamp/ directory, the file content SHALL NOT contain
    the old terminology phrase (case-insensitive).
    """

    @given(file_path=st.sampled_from(_TARGET_FILES))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_no_mock_data_phrase_in_file_content(self, file_path: Path) -> None:
        """For any sampled file, the forbidden phrase must not appear."""
        content = file_path.read_text(encoding="utf-8").lower()
        assert _FORBIDDEN_PHRASE not in content, (
            f"File contains forbidden phrase '{_FORBIDDEN_PHRASE}': "
            f"{file_path.relative_to(_BOOTCAMP_DIR)}"
        )


# ---------------------------------------------------------------------------
# Property 2 — No old terminology in filenames
# ---------------------------------------------------------------------------

# Forbidden filename substrings, constructed to avoid self-matching
_FORBIDDEN_UNDERSCORE = "mock" + "_" + "data"
_FORBIDDEN_HYPHEN = "mock" + "-" + "data"


class TestNoMockDataInFilenames:
    """PBT — No filename contains the forbidden old terminology (case-insensitive).

    **Validates: Requirements 3.1, 5.2**

    For any file path within the senzing-bootcamp/ directory, the filename
    component SHALL NOT contain the substring mock_data or mock-data
    (case-insensitive).
    """

    @given(file_path=st.sampled_from(_ALL_FILES))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_no_mock_data_in_filename(self, file_path: Path) -> None:
        """For any sampled file, the filename must not contain forbidden substrings."""
        filename_lower = file_path.name.lower()
        assert _FORBIDDEN_UNDERSCORE not in filename_lower, (
            f"Filename contains forbidden substring '{_FORBIDDEN_UNDERSCORE}': "
            f"{file_path.relative_to(_BOOTCAMP_DIR)}"
        )
        assert _FORBIDDEN_HYPHEN not in filename_lower, (
            f"Filename contains forbidden substring '{_FORBIDDEN_HYPHEN}': "
            f"{file_path.relative_to(_BOOTCAMP_DIR)}"
        )
