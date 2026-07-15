"""Example test for docs/steering Kiro 1.0 hook terminology (task 13.4).

Feature: kiro-1-0-migration

Validates that the *real shipped* documentation and steering describe the
migrated Kiro 1.0 hook model — 1.0 trigger names and the migrated hook count
(27) — and that no removed manual hook is presented as an automatic hook. This
is a concrete example/edge test over the shipped Markdown under
``senzing-bootcamp/`` (not a Hypothesis property test).

**Validates: Requirements 11.1, 11.3, 11.6**

Scope and false-positive avoidance
----------------------------------
The migration is complete, so these assertions PASS against the current tree.
They are written to be robust rather than brittle, and deliberately scoped so
they do not fire on legitimate historical / migration prose:

* Positive checks (1.0 trigger names present + accurate migrated count) run only
  against the two target files this task owns: ``hooks/README.md`` (Req 11.1)
  and ``docs/guides/HOOKS_INSTALLATION_GUIDE.md`` (Req 11.3). The count is tied
  to the real number of shipped ``hooks/*.json`` files so the docs cannot drift
  from reality.
* The "no legacy trigger presented as the current schema" check is a *targeted*
  negative applied only to those two target files — NOT a blanket "no legacy
  substring anywhere" scan. It forbids the unambiguous legacy trigger/action
  identifiers (``fileEdited``, ``agentStop``, ``askAgent`` ...) outright, and
  allows the single legacy word that legitimately appears as removal prose
  (``userTriggered``) only on lines that also carry a removal marker
  (``removed``/``legacy``/``former`` ...). This is why the following are correct
  and do NOT fail: CHANGELOG migration entries (``fileEdited→PostFileSave``),
  POWER.md's "legacy ``*.kiro.hook`` files do not execute", hook-architecture.md's
  "the legacy ``agentStop`` event renamed", README.md's "Kiro 1.0 removed the
  legacy manual (``userTriggered``) trigger", and the slash files' "replaces the
  former ``commonmark-validation`` hook" — none of these are target-file legacy
  identifiers presented as the current schema.
* The removed-manual-hook check (Req 11.6) scans all docs + steering Markdown and
  flags a manual hook id only when it is presented *as an automatic hook* — i.e.
  a line naming the id that carries no slash-command / "former"-style routing
  context. Lines that route to the ``/backup-project``, ``/git-commit``, or
  ``/commonmark-validation`` slash command (or use "former"/"replaces"/"removed"/
  "no longer") are the intended, compliant form and pass.

Intentionally NOT scanned here (owned by other tasks / requirements):

* ``senzing-bootcamp/scripts/`` and ``senzing-bootcamp/tests/`` — the migration
  tooling and its tests legitimately name legacy ids (e.g. the installer's
  ``MANUAL_HOOK_IDS`` exclusion list). This task is about docs and steering only.
* ``CHANGELOG.md`` and ``POWER.md`` — versioning / power-config files carrying
  deliberate migration history (covered by the task 15.3 versioning test).
* Residual *legacy schema* prose beyond the two target files (e.g. the wider
  ``when``/``then``/``askAgent`` description still in ``docs/guides/ARCHITECTURE.md``)
  — that is the domain of the CI stale-reference gate (Req 14.5, task 16.1), not
  this terminology test. This test only asserts that ARCHITECTURE.md (and every
  other doc/steering file) does not present a *removed manual hook* as an
  automatic hook.
* ``config/`` YAML — machine-readable config is the stale-reference gate's job.
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (resolved absolutely so the test is cwd-independent)
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
_POWER_ROOT = _REPO_ROOT / "senzing-bootcamp"

HOOKS_DIR: Path = _POWER_ROOT / "hooks"
DOCS_DIR: Path = _POWER_ROOT / "docs"
STEERING_DIR: Path = _POWER_ROOT / "steering"

README: Path = HOOKS_DIR / "README.md"
INSTALL_GUIDE: Path = DOCS_DIR / "guides" / "HOOKS_INSTALLATION_GUIDE.md"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The shipped hook count: 30 legacy hooks minus the 3 manual hooks = 27 migrated,
# minus ``module-recap-append`` (folded into ``ask-bootcamper`` Phase 0 by the
# stop-hook-ux bugfix) = 26 (Req 1.1).
EXPECTED_V1_HOOK_COUNT: int = 26

# The 1.0 trigger names that the shipped hook set actually uses. Both target
# files describe hooks that fire on every one of these, so each must appear.
# (PostFileDelete is not used by any shipped hook and is intentionally omitted.)
V1_TRIGGER_NAMES: tuple[str, ...] = (
    "PostFileSave",
    "PostFileCreate",
    "PostToolUse",
    "PreToolUse",
    "Stop",
    "UserPromptSubmit",
    "PostTaskExec",
)

# Unambiguous legacy trigger / action identifiers. None of these may appear in
# the two target files at all — they are never part of legitimate removal prose
# there (the only legacy word that legitimately appears is ``userTriggered``,
# handled separately). Matched case-sensitively so the 1.0 ``PreToolUse`` /
# ``PostToolUse`` names are not confused with the legacy ``preToolUse`` /
# ``postToolUse`` spellings.
LEGACY_FORBIDDEN_IDENTIFIERS: tuple[str, ...] = (
    "fileEdited",
    "fileCreated",
    "fileDeleted",
    "agentStop",
    "promptSubmit",
    "postTaskExecution",
    "preToolUse",
    "postToolUse",
    "askAgent",
    "runCommand",
)

# The legacy word that DOES appear in the target files, but only as removal
# prose. Every line mentioning it must carry a removal marker below.
LEGACY_REMOVAL_WORD: str = "userTriggered"

# The three removed manual hooks (now slash commands) and their slash names.
MANUAL_HOOK_IDS: tuple[str, ...] = (
    "backup-project-on-request",
    "git-commit-reminder",
    "commonmark-validation",
)
SLASH_COMMANDS: tuple[str, ...] = (
    "/backup-project",
    "/git-commit",
    "/commonmark-validation",
)

# Context markers (case-insensitive) that mark a line referencing a legacy hook
# id / word as *historical / routed to a slash command* rather than presenting
# it as a current automatic hook.
_SLASH_OR_HISTORICAL_MARKERS: tuple[str, ...] = (
    "/backup-project",
    "/git-commit",
    "/commonmark-validation",
    "slash",
    "former",
    "replace",  # replaces / replaced / replacement
    "no longer",
    "remove",  # remove / removes / removed
    "legacy",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    """Read a UTF-8 text file, asserting it exists first."""
    assert path.is_file(), f"expected file not found: {path}"
    return path.read_text(encoding="utf-8")


def _shipped_v1_hook_count() -> int:
    """Return the number of shipped ``hooks/*.json`` v1 hook files."""
    assert HOOKS_DIR.is_dir(), f"hooks directory not found at {HOOKS_DIR}"
    return len(list(HOOKS_DIR.glob("*.json")))


def _mentions_count_in_hook_context(text: str, count: int) -> bool:
    """Return True if some line states ``count`` alongside the word "hook".

    Requiring both the standalone number and "hook" on the same line keeps the
    match specific (e.g. "There are 27 hooks total", "27 pre-configured V1 hooks")
    while ignoring unrelated numbers.
    """
    number = re.compile(rf"\b{count}\b")
    return any(number.search(line) and "hook" in line.lower() for line in text.splitlines())


def _line_has_marker(line: str) -> bool:
    """Return True if the line carries a slash-command / historical marker."""
    lowered = line.lower()
    return any(marker in lowered for marker in _SLASH_OR_HISTORICAL_MARKERS)


def _docs_and_steering_md_files() -> list[Path]:
    """Return every docs + steering Markdown file to scan for Req 11.6.

    Covers all Markdown under ``docs/`` (recursively) and ``steering/`` plus
    ``hooks/README.md``. CHANGELOG.md / POWER.md live at the power root and are
    intentionally excluded (see the module docstring).
    """
    files: list[Path] = []
    files.extend(sorted(DOCS_DIR.rglob("*.md")))
    files.extend(sorted(STEERING_DIR.glob("*.md")))
    files.append(README)
    # De-duplicate while preserving order.
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in files:
        resolved = path.resolve()
        if resolved not in seen and path.is_file():
            seen.add(resolved)
            unique.append(path)
    return unique


def _manual_hook_violations(path: Path) -> list[tuple[int, str, str]]:
    """Return manual-hook-as-automatic offences in ``path``.

    Each offence is ``(line_number, manual_hook_id, line_text)``: a line that
    names a removed manual hook id without any slash-command / historical marker
    that would route it to its slash command (Req 11.6).
    """
    offences: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if _line_has_marker(line):
            continue
        for hook_id in MANUAL_HOOK_IDS:
            if hook_id in line:
                offences.append((lineno, hook_id, line.strip()))
    return offences


# ===========================================================================
# TestReadmeTerminology  (Requirement 11.1)
# ===========================================================================


class TestReadmeTerminology:
    """``hooks/README.md`` uses 1.0 trigger names and the migrated count.

    Feature: kiro-1-0-migration
    **Validates: Requirements 11.1**
    """

    def test_readme_exists(self) -> None:
        """The hooks README exists."""
        assert README.is_file(), f"README not found at {README}"

    def test_readme_uses_all_v1_trigger_names(self) -> None:
        """Every 1.0 trigger the shipped set uses is named in the README."""
        text = _read(README)
        missing = [name for name in V1_TRIGGER_NAMES if name not in text]
        assert not missing, (
            f"hooks/README.md must describe the migrated hooks with 1.0 trigger "
            f"names; missing: {missing}"
        )

    def test_readme_states_migrated_count(self) -> None:
        """The README states the migrated count (27) in a hook context.

        The stated count is also tied to the real number of shipped v1 hook
        files so the doc and the shipped set cannot drift apart.
        """
        actual = _shipped_v1_hook_count()
        assert actual == EXPECTED_V1_HOOK_COUNT, (
            f"expected {EXPECTED_V1_HOOK_COUNT} shipped hooks/*.json files, "
            f"found {actual}"
        )
        text = _read(README)
        assert _mentions_count_in_hook_context(text, EXPECTED_V1_HOOK_COUNT), (
            f"hooks/README.md must state the migrated hook count "
            f"({EXPECTED_V1_HOOK_COUNT}) in a hook context"
        )

    def test_readme_has_no_legacy_trigger_identifiers(self) -> None:
        """The README never presents legacy trigger/action identifiers.

        Legacy identifiers like ``fileEdited`` / ``agentStop`` / ``askAgent``
        must not appear as the current schema (Req 11.1). ``userTriggered`` may
        appear only as removal prose (checked separately).
        """
        text = _read(README)
        present = [ident for ident in LEGACY_FORBIDDEN_IDENTIFIERS if ident in text]
        assert not present, (
            f"hooks/README.md must not present legacy identifiers as the current "
            f"schema; found: {present}"
        )

    def test_readme_legacy_removal_word_only_in_removal_prose(self) -> None:
        """Any ``userTriggered`` mention sits on a removal-context line."""
        text = _read(README)
        bad = [
            line.strip()
            for line in text.splitlines()
            if LEGACY_REMOVAL_WORD in line and not _line_has_marker(line)
        ]
        assert not bad, (
            "hooks/README.md may reference 'userTriggered' only as removal prose "
            f"(e.g. 'Kiro 1.0 removed ...'); offending lines: {bad}"
        )


# ===========================================================================
# TestInstallationGuideTerminology  (Requirement 11.3)
# ===========================================================================


class TestInstallationGuideTerminology:
    """``HOOKS_INSTALLATION_GUIDE.md`` uses 1.0 triggers and accurate counts.

    Feature: kiro-1-0-migration
    **Validates: Requirements 11.3**
    """

    def test_guide_exists(self) -> None:
        """The hooks installation guide exists."""
        assert INSTALL_GUIDE.is_file(), f"install guide not found at {INSTALL_GUIDE}"

    def test_guide_uses_all_v1_trigger_names(self) -> None:
        """Every 1.0 trigger the shipped set uses is named in the guide."""
        text = _read(INSTALL_GUIDE)
        missing = [name for name in V1_TRIGGER_NAMES if name not in text]
        assert not missing, (
            f"HOOKS_INSTALLATION_GUIDE.md must describe the 1.0 hook-creation "
            f"path with 1.0 trigger names; missing: {missing}"
        )

    def test_guide_states_migrated_count(self) -> None:
        """The guide states the migrated count (27) in a hook context.

        Tied to the real number of shipped v1 hook files.
        """
        actual = _shipped_v1_hook_count()
        assert actual == EXPECTED_V1_HOOK_COUNT, (
            f"expected {EXPECTED_V1_HOOK_COUNT} shipped hooks/*.json files, "
            f"found {actual}"
        )
        text = _read(INSTALL_GUIDE)
        assert _mentions_count_in_hook_context(text, EXPECTED_V1_HOOK_COUNT), (
            f"HOOKS_INSTALLATION_GUIDE.md must state an accurate migrated hook "
            f"count ({EXPECTED_V1_HOOK_COUNT})"
        )

    def test_guide_has_no_legacy_trigger_identifiers(self) -> None:
        """The guide never presents legacy trigger/action identifiers."""
        text = _read(INSTALL_GUIDE)
        present = [ident for ident in LEGACY_FORBIDDEN_IDENTIFIERS if ident in text]
        assert not present, (
            f"HOOKS_INSTALLATION_GUIDE.md must not present legacy identifiers as "
            f"the current schema; found: {present}"
        )

    def test_guide_legacy_removal_word_only_in_removal_prose(self) -> None:
        """Any ``userTriggered`` mention sits on a removal-context line."""
        text = _read(INSTALL_GUIDE)
        bad = [
            line.strip()
            for line in text.splitlines()
            if LEGACY_REMOVAL_WORD in line and not _line_has_marker(line)
        ]
        assert not bad, (
            "HOOKS_INSTALLATION_GUIDE.md may reference 'userTriggered' only as "
            f"removal prose; offending lines: {bad}"
        )


# ===========================================================================
# TestNoRemovedManualHookAsAutomatic  (Requirement 11.6)
# ===========================================================================


class TestNoRemovedManualHookAsAutomatic:
    """No doc/steering file presents a removed manual hook as an automatic hook.

    Every reference to ``backup-project-on-request``, ``git-commit-reminder``, or
    ``commonmark-validation`` in the docs + steering must route to the
    corresponding slash command (``/backup-project``, ``/git-commit``,
    ``/commonmark-validation``) rather than list it as an active hook.

    Feature: kiro-1-0-migration
    **Validates: Requirements 11.6**
    """

    def test_docs_and_steering_present(self) -> None:
        """There is a non-empty set of docs + steering Markdown to scan."""
        files = _docs_and_steering_md_files()
        assert files, "no docs/steering Markdown files found to scan"
        assert README in files, "hooks/README.md must be part of the scan set"
        assert INSTALL_GUIDE in files, "install guide must be part of the scan set"

    def test_no_manual_hook_referenced_as_automatic(self) -> None:
        """No doc/steering line names a removed manual hook without slash routing."""
        all_offences: dict[str, list[tuple[int, str, str]]] = {}
        for path in _docs_and_steering_md_files():
            offences = _manual_hook_violations(path)
            if offences:
                rel = path.relative_to(_REPO_ROOT).as_posix()
                all_offences[rel] = offences
        assert not all_offences, (
            "docs/steering must not present removed manual hooks as automatic "
            "hooks; each reference should route to its slash command "
            f"({', '.join(SLASH_COMMANDS)}). Offences: {all_offences}"
        )

    def test_manual_hook_ids_never_appear_as_hook_filenames(self) -> None:
        """No doc/steering references a manual hook as a shipped hook file.

        A removed manual hook must never be cited as a ``<id>.kiro.hook`` or
        ``<id>.json`` shipped hook file (it is a slash-command steering file now).
        """
        bad: dict[str, list[str]] = {}
        for path in _docs_and_steering_md_files():
            text = path.read_text(encoding="utf-8")
            hits: list[str] = []
            for hook_id in MANUAL_HOOK_IDS:
                for ext in (".kiro.hook", ".json"):
                    if f"{hook_id}{ext}" in text:
                        hits.append(f"{hook_id}{ext}")
            if hits:
                bad[path.relative_to(_REPO_ROOT).as_posix()] = hits
        assert not bad, (
            "removed manual hooks must not be cited as shipped hook files; "
            f"found: {bad}"
        )

    def test_target_files_route_manual_hooks_to_slash_commands(self) -> None:
        """README and the install guide name each replacement slash command.

        Confirms the positive side of Req 11.6 in the primary hook docs: the
        three slash commands that replaced the manual hooks are documented.
        """
        for path in (README, INSTALL_GUIDE):
            text = _read(path)
            missing = [cmd for cmd in SLASH_COMMANDS if cmd not in text]
            assert not missing, (
                f"{path.name} must route former manual hooks to their slash "
                f"commands; missing: {missing}"
            )
