"""Preservation test: module-transitions.md must use inclusion: always.

This file is needed on every module start and completion to render banners,
journey maps, and before/after framing. Changing it to fileMatch or auto
causes missed banners when the progress file isn't the interaction trigger.

The 0.9.0 changelog records a change to fileMatch that was later reverted.
This test pins the current correct state to prevent accidental regression.
"""

from __future__ import annotations

from pathlib import Path

STEERING_DIR = Path("senzing-bootcamp/steering")
TARGET_FILE = STEERING_DIR / "module-transitions.md"


class TestModuleTransitionsAlwaysInclusion:
    """Preservation tests for module-transitions.md inclusion mode."""

    def test_file_exists(self):
        """module-transitions.md must exist in the steering directory."""
        assert TARGET_FILE.is_file(), (
            f"Expected {TARGET_FILE} to exist"
        )

    def test_inclusion_is_always(self):
        """module-transitions.md must have inclusion: always in frontmatter.

        This was reverted from fileMatch because the file is needed on every
        module start/completion, not just when bootcamp_progress.json is read.
        """
        content = TARGET_FILE.read_text(encoding="utf-8")
        # Parse YAML frontmatter (between --- delimiters)
        assert content.startswith("---"), (
            "module-transitions.md must have YAML frontmatter"
        )
        end_idx = content.index("---", 3)
        frontmatter = content[3:end_idx]

        assert "inclusion: always" in frontmatter, (
            f"module-transitions.md must have 'inclusion: always' in frontmatter. "
            f"Found frontmatter: {frontmatter.strip()}"
        )

    def test_inclusion_is_not_file_match(self):
        """module-transitions.md must NOT use fileMatch inclusion.

        fileMatch was tried in 0.9.0 and caused missed module banners.
        """
        content = TARGET_FILE.read_text(encoding="utf-8")
        end_idx = content.index("---", 3)
        frontmatter = content[3:end_idx]

        assert "inclusion: fileMatch" not in frontmatter, (
            "module-transitions.md must NOT use fileMatch — "
            "this was reverted because it caused missed banners"
        )

    def test_inclusion_is_not_auto(self):
        """module-transitions.md must NOT use auto inclusion.

        auto would load it on file-match triggers which is insufficient —
        it must be present on every interaction during active modules.
        """
        content = TARGET_FILE.read_text(encoding="utf-8")
        end_idx = content.index("---", 3)
        frontmatter = content[3:end_idx]

        assert "inclusion: auto" not in frontmatter, (
            "module-transitions.md must NOT use auto — "
            "it must be always-loaded for module banners"
        )
