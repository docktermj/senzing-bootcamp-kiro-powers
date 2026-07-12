"""Packaging and security conformance tests for ``session-handoff.md``.

Feature: session-handoff

This is an *example* (non-property) steering-content test. It reads the on-disk
steering file ``senzing-bootcamp/steering/session-handoff.md`` and asserts it
ships as conformant Kiro Power content: valid YAML frontmatter, no leaked
secrets / PII / external endpoints, correct packaging placement and naming, and
lightweight CommonMark cleanliness.

The assertions are deterministic (fixed on-disk content, no randomness, no
wall-clock, no network) and stdlib-only. The emoji code-point ranges are reused
from ``validate_handoff_summary`` so this test stays in lockstep with the
validator, and the canonical Handoff_Summary section headings are pulled from the
same module rather than hand-typed (the em-dash in the "Verification" heading is
never re-keyed here).

Validates: Requirements 11.1, 11.3, 11.4
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts are not a package) so the
# emoji ranges and canonical section headings come straight from the validator.
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_handoff_summary import BODY_SECTIONS, _EMOJI_RANGES  # noqa: E402

# ---------------------------------------------------------------------------
# Steering file under test (resolved relative to this file so the suite is
# location-independent: <repo>/senzing-bootcamp/tests/ -> ../steering/).
# ---------------------------------------------------------------------------
_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_SESSION_HANDOFF = _STEERING_DIR / "session-handoff.md"

# Recognized Kiro steering inclusion modes; Req 11.1 requires ``manual`` here.
_VALID_INCLUSION_MODES = frozenset({"always", "fileMatch", "manual"})

# Conversation-protocol markers the design explicitly sanctions in the invocation
# offer ("The invocation offer may carry the conversation protocol's
# question/stop markers"). Every *other* emoji code point is forbidden.
_POINTER = "\U0001f449"  # 👉
_STOP = "\U0001f6d1"  # 🛑
_SANCTIONED_MARKERS = frozenset({_POINTER, _STOP})

# The Senzing MCP host string. Per the security rules it must live only in
# ``mcp.json``; the steering file refers to the server by name/tool, not URL.
_MCP_HOST = "mcp.senzing.com"

# A kebab-case Markdown filename: lowercase words joined by single hyphens.
_KEBAB_CASE_MD = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.md$")

# Sibling steering files the handoff coordinates with. The repo convention cites
# them either as backticked filenames or via the ``#[[file:...]]`` include form.
_SIBLING_STEERING_FILES = (
    "conversation-protocol.md",
    "session-resume.md",
    "agent-context-management.md",
    "module-completion-artifacts.md",
)

# Credential / PII patterns that must never appear in shipped steering content.
# Kept conservative so ordinary prose (e.g. "connection description", "MCP:
# connected") is not misread as a secret.
_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("email address", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("PEM private key header", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("bearer token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{12,}")),
    (
        "hardcoded secret assignment",
        re.compile(
            r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token)\b"
            r"\s*[:=]\s*['\"]?[A-Za-z0-9/+_\-]{6,}"
        ),
    ),
)


def _read() -> str:
    """Return the steering file's UTF-8 text, failing clearly if it is absent.

    Returns:
        The full contents of ``session-handoff.md`` as a string.
    """
    assert _SESSION_HANDOFF.exists(), f"steering file not found: {_SESSION_HANDOFF}"
    return _SESSION_HANDOFF.read_text(encoding="utf-8")


def _frontmatter(text: str) -> dict[str, str]:
    """Parse the leading YAML frontmatter into a flat ``key -> value`` mapping.

    Uses a minimal stdlib parser (no PyYAML, per repo convention). Only the block
    between the opening ``---`` on the first line and the next ``---`` line is
    considered, and only simple ``key: value`` pairs are captured (surrounding
    single/double quotes are stripped from the value).

    Args:
        text: The full steering-file text.

    Returns:
        The parsed frontmatter mapping, or an empty mapping when no frontmatter
        fence is present.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    meta: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta


def _emoji_chars(text: str) -> set[str]:
    """Return the distinct emoji characters present in ``text``.

    Classification reuses :data:`validate_handoff_summary._EMOJI_RANGES` so this
    test flags exactly the code points the validator treats as emoji.

    Args:
        text: The text to scan.

    Returns:
        The set of emoji characters found (empty when none are present).
    """
    return {
        char
        for char in text
        if any(low <= ord(char) <= high for low, high in _EMOJI_RANGES)
    }


class TestSessionHandoffSteering:
    """Packaging + security conformance for the ``session-handoff.md`` steering file.

    Validates: Requirements 11.1, 11.3, 11.4
    """

    # -- Frontmatter validity (Req 11.1) ------------------------------------

    def test_file_exists_and_is_nonempty(self) -> None:
        """The steering file exists, is a file, and has content (Req 11.1)."""
        assert _SESSION_HANDOFF.exists(), f"missing steering file: {_SESSION_HANDOFF}"
        assert _SESSION_HANDOFF.is_file(), f"not a file: {_SESSION_HANDOFF}"
        assert _read().strip(), "steering file is empty"

    def test_has_delimited_yaml_frontmatter(self) -> None:
        """The file opens with a ``---`` fence and carries a closing ``---`` (Req 11.1)."""
        text = _read()
        assert text.lstrip().startswith("---"), "steering file lacks opening frontmatter fence"
        fence_lines = [i for i, line in enumerate(text.splitlines()) if line.strip() == "---"]
        assert len(fence_lines) >= 2, "frontmatter is not closed with a second '---' fence"

    def test_frontmatter_inclusion_is_manual(self) -> None:
        """Frontmatter carries an ``inclusion`` key set to a valid ``manual`` value (Req 11.1)."""
        meta = _frontmatter(_read())
        assert "inclusion" in meta, "frontmatter is missing the 'inclusion' key"
        assert meta["inclusion"] in _VALID_INCLUSION_MODES, (
            f"invalid inclusion mode: {meta['inclusion']!r}"
        )
        assert meta["inclusion"] == "manual", (
            f"session-handoff must be manual-inclusion, got {meta['inclusion']!r}"
        )

    def test_frontmatter_has_nonempty_description(self) -> None:
        """Frontmatter carries a non-empty ``description`` key (Req 11.1)."""
        meta = _frontmatter(_read())
        assert "description" in meta, "frontmatter is missing the 'description' key"
        assert meta["description"].strip(), "frontmatter 'description' is empty"

    # -- Security conformance (Req 11.3, 11.4) ------------------------------

    def test_no_emoji_beyond_sanctioned_protocol_markers(self) -> None:
        """No emoji appear except the sanctioned 👉 / 🛑 conversation-protocol markers.

        The design's Tone & Discipline section permits the invocation offer to
        carry the conversation protocol's question/stop markers; every other emoji
        code point is disallowed in shipped steering content.

        Validates: Requirements 11.3
        """
        offenders = _emoji_chars(_read()) - _SANCTIONED_MARKERS
        assert not offenders, (
            "unexpected emoji in steering file: "
            + ", ".join(sorted(f"U+{ord(ch):04X}" for ch in offenders))
        )

    def test_no_external_urls(self) -> None:
        """The file references no external ``http(s)`` URLs (Req 11.4).

        Steering files reach external systems through MCP tools or ``#[[file:]]``
        references, never hardcoded links (workspace security rules).
        """
        urls = re.findall(r"https?://\S+", _read())
        assert not urls, f"steering file must not contain external URLs: {urls}"

    def test_no_hardcoded_mcp_host(self) -> None:
        """The MCP host string is not hardcoded in the steering file (Req 11.4).

        Per the security rules the ``mcp.senzing.com`` host lives only in
        ``mcp.json``; the steering file refers to the server by name/tool.
        """
        assert _MCP_HOST not in _read(), (
            f"steering file must not hardcode the MCP host {_MCP_HOST!r}; "
            "reference the server by name/tool instead"
        )

    def test_references_senzing_mcp_by_name_and_tool(self) -> None:
        """The Senzing MCP server is referenced by name and tool, not URL (Req 11.4).

        Confirms the only external endpoint is the Senzing MCP server and that it
        is surfaced the conformant way: named in prose and reached via the
        ``get_capabilities`` tool call.
        """
        text = _read()
        assert "Senzing MCP server" in text, "steering file must name the Senzing MCP server"
        assert "get_capabilities" in text, (
            "steering file must reference the MCP by tool (get_capabilities)"
        )

    def test_no_pii_or_credentials(self) -> None:
        """No credentials, tokens, keys, or PII-like values appear (Req 11.3)."""
        text = _read()
        hits = [label for label, pattern in _SECRET_PATTERNS if pattern.search(text)]
        assert not hits, f"steering file appears to contain secrets/PII: {hits}"

    # -- Packaging / structure (Req 11.1) -----------------------------------

    def test_lives_under_steering_directory(self) -> None:
        """The file ships under ``senzing-bootcamp/steering/`` (Req 11.1)."""
        assert _SESSION_HANDOFF.parent == _STEERING_DIR, (
            f"steering file must live in {_STEERING_DIR}, found {_SESSION_HANDOFF.parent}"
        )
        assert _STEERING_DIR.name == "steering"
        assert _STEERING_DIR.parent.name == "senzing-bootcamp"

    def test_filename_is_kebab_case_markdown(self) -> None:
        """The filename is kebab-case with a ``.md`` extension (Req 11.1)."""
        name = _SESSION_HANDOFF.name
        assert _KEBAB_CASE_MD.match(name), f"filename is not kebab-case markdown: {name!r}"

    def test_cross_file_references_use_repo_convention(self) -> None:
        """Sibling steering references use backticks or ``#[[file:]]``, never bare links.

        Every coordinated sibling steering file must be cited either as a
        backticked filename or via the ``#[[file:...]]`` include form; no ``.md``
        reference may appear as a bare Markdown link to an external URL.

        Validates: Requirements 11.1
        """
        text = _read()
        assert "](http" not in text, "steering file must not use bare external Markdown links"
        for sibling in _SIBLING_STEERING_FILES:
            backticked = f"`{sibling}`" in text
            included = "#[[file:" in text and sibling in text
            assert backticked or included, (
                f"sibling steering reference {sibling!r} must be backticked or a "
                "#[[file:]] include"
            )

    def test_canonical_handoff_section_headings_present(self) -> None:
        """The documented Title template plus the seven body headings appear (Req 11.1).

        The file documents the fixed Handoff_Summary skeleton, so the Title
        template (``# Handoff:``) and each canonical ``## `` body heading — pulled
        verbatim from the validator, including the em-dash in "Verification — how
        to confirm things still work" — must be present.
        """
        text = _read()
        assert "# Handoff:" in text, "missing the Title template '# Handoff:'"
        for heading in BODY_SECTIONS:
            assert f"## {heading}" in text, f"missing canonical section heading: {heading!r}"

    # -- Lightweight CommonMark cleanliness ---------------------------------

    def test_fenced_code_blocks_are_balanced(self) -> None:
        """Every fenced code block is opened and closed (even fence count)."""
        fence_lines = [
            line for line in _read().splitlines() if line.lstrip().startswith("```")
        ]
        assert len(fence_lines) % 2 == 0, (
            f"unbalanced code fences: found {len(fence_lines)} fence lines"
        )

    def test_bold_emphasis_uses_asterisks(self) -> None:
        """Bold emphasis uses ``**`` consistently, never ``__`` (markdownlint MD049).

        Guards emphasis-style consistency without tripping on the single
        underscores in glossary terms such as ``Handoff_Summary``.
        """
        assert "__" not in _read(), "steering file must use '**' for bold, not '__'"
