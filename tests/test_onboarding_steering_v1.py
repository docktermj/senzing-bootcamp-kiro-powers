"""Example test for the Kiro 1.0 onboarding / session-resume hook path (task 12.2).

Feature: kiro-1-0-migration

Validates that the *real shipped* onboarding and session-resume steering
(updated in task 12.1) instructs the agent to create the capture-critical hooks
as Kiro 1.0 ``v1`` hooks, expresses hook creation in 1.0
``trigger`` / ``matcher`` / ``action`` terms, checks hook presence with the 1.0
``<id>.json`` file layout, and no longer presents ``commonmark-validation`` as a
critical/automatic hook (it is a ``/commonmark-validation`` slash command now).

This is a concrete example/edge test over the shipped steering Markdown under
``senzing-bootcamp/steering/`` — not a Hypothesis property test. The migration
is complete, so every assertion below PASSES against the current tree.

**Validates: Requirements 10.3, 10.5, 10.6**

Scope and false-positive avoidance
----------------------------------
Task 12.1 updated exactly four steering files, and this test scopes its checks
to those files rather than scanning the whole repo:

* ``onboarding-flow.md`` and ``session-resume-phase2-setup-recovery.md`` own the
  capture-critical hook-creation / presence-verification behaviour, so the
  Assertion-1 (capture-critical as v1) and Assertion-3 (commonmark routing)
  checks read those.
* ``agent-instructions.md`` and ``session-resume-phase2-setup-recovery.md`` also
  carry ``createHook`` instructions, so the positive 1.0-terminology checks run
  against the subset of files that actually instruct hook creation
  (``HOOK_CREATION_FILES``). ``onboarding-phase2-track-setup.md`` is track-setup
  prose that references the ``Stop`` trigger and existing hooks but does not
  itself instruct ``createHook``, so it is exempt from the *positive* terminology
  requirement while still being subject to the *negative* legacy-identifier ban.
* The legacy-identifier ban (Assertion 2) is a **targeted, case-sensitive**
  negative applied only to these four files — not a repo-wide scan. It forbids
  the unambiguous legacy trigger/action identifiers
  (``agentStop`` / ``preToolUse`` / ``postToolUse`` / ``fileEdited`` /
  ``fileCreated`` / ``fileDeleted`` / ``promptSubmit`` / ``postTaskExecution`` /
  ``askAgent`` / ``runCommand``) and the legacy ``.kiro.hook`` extension. The
  check is case-sensitive so the 1.0 ``PreToolUse`` / ``PostToolUse`` /
  ``UserPromptSubmit`` names are never confused with their legacy lowercase
  spellings (``preToolUse`` / ``postToolUse`` / ``promptSubmit``). The legacy
  word ``userTriggered`` is tolerated only on a line that also carries a removal
  marker; it does not currently appear in any of the four files, so that guard
  passes vacuously.
* The ``commonmark-validation`` check (Assertion 3) flags the id only when it is
  presented *as a hook* — every line naming the exact ``commonmark-validation``
  id must carry a slash-command / removal marker (``/commonmark-validation``,
  ``slash``, ``not a hook``, ``no longer``, ``on demand``, ``removed`` ...). The
  current single reference ("point them to the ``/commonmark-validation`` slash
  command ... which runs the same checks on demand") carries several such
  markers and is the intended, compliant form. A bare ``/commonmark-validation``
  slash reference is explicitly tolerated.

Intentionally NOT scanned here (owned by other tasks / requirements):

* Any steering / docs file outside the four task-12.1 files — the broader
  terminology sweep is task 13.4 (``test_docs_steering_terminology.py``) and the
  CI stale-reference gate is task 16.1 (Req 14.5).
* The hook registry files themselves — the registry is the source of truth the
  onboarding path *reads from* (tasks 8.x), not the subject of this test.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (resolved absolutely so the test is cwd-independent)
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
_POWER_ROOT = _REPO_ROOT / "senzing-bootcamp"
STEERING_DIR: Path = _POWER_ROOT / "steering"

ONBOARDING_FLOW: Path = STEERING_DIR / "onboarding-flow.md"
ONBOARDING_PHASE2: Path = STEERING_DIR / "onboarding-phase2-track-setup.md"
AGENT_INSTRUCTIONS: Path = STEERING_DIR / "agent-instructions.md"
SESSION_RESUME: Path = STEERING_DIR / "session-resume-phase2-setup-recovery.md"

# All four steering files updated by task 12.1.
ALL_FOUR_FILES: tuple[Path, ...] = (
    ONBOARDING_FLOW,
    ONBOARDING_PHASE2,
    AGENT_INSTRUCTIONS,
    SESSION_RESUME,
)

# The subset that actually instructs the agent to create hooks. Only these are
# required to carry the positive 1.0 trigger/matcher/action terminology.
HOOK_CREATION_FILES: tuple[Path, ...] = (
    ONBOARDING_FLOW,
    AGENT_INSTRUCTIONS,
    SESSION_RESUME,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The two capture-critical hooks the completion summary + journey recap depend
# on. Onboarding/resume must create and verify both as v1 hooks (Req 10.3). The
# stop-hook-ux bugfix folded the former ``module-recap-append`` recap hook into
# ``ask-bootcamper`` Phase 0, so ``ask-bootcamper`` now owns recap capture too.
CAPTURE_CRITICAL_HOOK_IDS: tuple[str, ...] = (
    "ask-bootcamper",
    "session-log-events",
)

# The 1.0 hook-schema concept words the createHook instructions must use (Req 10.2).
V1_CONCEPT_TERMS: tuple[str, ...] = ("trigger", "matcher", "action")

# Unambiguous legacy trigger/action identifiers. None may appear in the four
# task-12.1 files. Matched case-sensitively so the 1.0 ``PreToolUse`` /
# ``PostToolUse`` / ``UserPromptSubmit`` names are not confused with the legacy
# ``preToolUse`` / ``postToolUse`` / ``promptSubmit`` spellings.
LEGACY_FORBIDDEN_IDENTIFIERS: tuple[str, ...] = (
    "agentStop",
    "preToolUse",
    "postToolUse",
    "fileEdited",
    "fileCreated",
    "fileDeleted",
    "promptSubmit",
    "postTaskExecution",
    "askAgent",
    "runCommand",
)

# The legacy hook file extension that must never appear (1.0 uses ``.json``).
LEGACY_HOOK_EXTENSION: str = ".kiro.hook"

# Legacy word tolerated only as removal prose (guarded by a removal marker).
LEGACY_REMOVAL_WORD: str = "userTriggered"

# The removed manual hook now shipped as a slash command.
COMMONMARK_HOOK_ID: str = "commonmark-validation"
COMMONMARK_SLASH_COMMAND: str = "/commonmark-validation"

# Context markers (case-insensitive) that mark a line as historical / routed to
# a slash command rather than presenting an id as a current automatic hook.
_SLASH_OR_HISTORICAL_MARKERS: tuple[str, ...] = (
    COMMONMARK_SLASH_COMMAND,
    "slash",
    "not a hook",
    "no longer",
    "on demand",
    "former",
    "replace",  # replaces / replaced / replacement
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


def _line_has_marker(line: str) -> bool:
    """Return True if the line carries a slash-command / historical marker."""
    lowered = line.lower()
    return any(marker in lowered for marker in _SLASH_OR_HISTORICAL_MARKERS)


# ===========================================================================
# TestSteeringFilesPresent
# ===========================================================================


class TestSteeringFilesPresent:
    """The four task-12.1 steering files exist and are readable.

    Feature: kiro-1-0-migration
    """

    def test_all_four_files_exist(self) -> None:
        """Each of the four updated steering files is present."""
        missing = [p.name for p in ALL_FOUR_FILES if not p.is_file()]
        assert not missing, f"missing task-12.1 steering files: {missing}"


# ===========================================================================
# TestCaptureCriticalHooksCreatedAsV1  (Requirements 10.3, 10.6)
# ===========================================================================


class TestCaptureCriticalHooksCreatedAsV1:
    """Onboarding/resume creates + verifies the capture-critical hooks as v1.

    The two capture-critical hooks (``ask-bootcamper`` and ``session-log-events``)
    must be referenced and created as v1 ``.json`` hooks, with session-start
    presence checks looking for ``<id>.json`` in ``.kiro/hooks/`` (never the
    legacy ``.kiro.hook`` layout). The former ``module-recap-append`` recap hook
    was folded into ``ask-bootcamper`` Phase 0 by the stop-hook-ux bugfix.

    Feature: kiro-1-0-migration
    **Validates: Requirements 10.3, 10.6**
    """

    def test_onboarding_flow_names_all_capture_critical_ids(self) -> None:
        """onboarding-flow.md references both capture-critical hook ids."""
        text = _read(ONBOARDING_FLOW)
        missing = [hid for hid in CAPTURE_CRITICAL_HOOK_IDS if hid not in text]
        assert not missing, (
            "onboarding-flow.md must reference every capture-critical hook id; "
            f"missing: {missing}"
        )

    def test_session_resume_names_all_capture_critical_ids(self) -> None:
        """session-resume steering references both capture-critical ids."""
        text = _read(SESSION_RESUME)
        missing = [hid for hid in CAPTURE_CRITICAL_HOOK_IDS if hid not in text]
        assert not missing, (
            "session-resume steering must reference every capture-critical hook "
            f"id; missing: {missing}"
        )

    def test_onboarding_flow_creates_capture_critical_as_v1(self) -> None:
        """onboarding-flow.md instructs creating the hooks as v1 via createHook."""
        text = _read(ONBOARDING_FLOW)
        assert "createHook" in text, (
            "onboarding-flow.md must instruct hook creation via the createHook "
            "capability"
        )
        assert "v1" in text, (
            "onboarding-flow.md must describe hooks as v1 definitions"
        )

    def test_presence_check_uses_json_filenames(self) -> None:
        """The presence-verification step names each ``<id>.json`` file.

        Session-start verification must look for the 1.0 ``<id>.json`` files, so
        both concrete filenames must appear in the onboarding steering.
        """
        text = _read(ONBOARDING_FLOW)
        missing = [
            f"{hid}.json" for hid in CAPTURE_CRITICAL_HOOK_IDS if f"{hid}.json" not in text
        ]
        assert not missing, (
            "onboarding-flow.md presence check must verify each capture-critical "
            f"hook's <id>.json file; missing: {missing}"
        )

    def test_session_resume_presence_check_uses_json(self) -> None:
        """session-resume warn-on-absence inspects for ``<id>.json`` files."""
        text = _read(SESSION_RESUME)
        assert "<id>.json" in text or ".json" in text, (
            "session-resume steering must check hook presence via the 1.0 "
            ".json file layout"
        )
        assert ".kiro/hooks" in text, (
            "session-resume steering must inspect the .kiro/hooks/ directory"
        )

    def test_presence_checks_never_use_legacy_extension(self) -> None:
        """Neither onboarding nor resume checks for the legacy ``.kiro.hook``."""
        for path in (ONBOARDING_FLOW, SESSION_RESUME):
            text = _read(path)
            assert LEGACY_HOOK_EXTENSION not in text, (
                f"{path.name} must not reference the legacy {LEGACY_HOOK_EXTENSION} "
                "extension in presence checks"
            )


# ===========================================================================
# TestOneZeroTerminology  (Requirement 10.2)
# ===========================================================================


class TestOneZeroTerminology:
    """Hook-creation instructions use 1.0 trigger/matcher/action terminology.

    The ``createHook`` instructions must be expressed in 1.0 terms, and none of
    the four task-12.1 files may present a legacy trigger/action identifier or
    the legacy ``.kiro.hook`` extension.

    Feature: kiro-1-0-migration
    **Validates: Requirements 10.2**
    """

    def test_createhook_files_use_v1_concept_terms(self) -> None:
        """Each hook-creation file references trigger, matcher, and action."""
        for path in HOOK_CREATION_FILES:
            text = _read(path)
            assert "createHook" in text, (
                f"{path.name} must instruct hook creation via createHook"
            )
            missing = [term for term in V1_CONCEPT_TERMS if term not in text]
            assert not missing, (
                f"{path.name} createHook instructions must use 1.0 hook-schema "
                f"terms; missing: {missing}"
            )

    def test_no_legacy_trigger_or_action_identifiers(self) -> None:
        """No task-12.1 file presents a legacy trigger/action identifier."""
        offenders: dict[str, list[str]] = {}
        for path in ALL_FOUR_FILES:
            text = _read(path)
            present = [ident for ident in LEGACY_FORBIDDEN_IDENTIFIERS if ident in text]
            if present:
                offenders[path.name] = present
        assert not offenders, (
            "task-12.1 steering must not present legacy trigger/action "
            f"identifiers as the current schema; found: {offenders}"
        )

    def test_no_legacy_hook_extension(self) -> None:
        """No task-12.1 file references the legacy ``.kiro.hook`` extension."""
        offenders = [p.name for p in ALL_FOUR_FILES if LEGACY_HOOK_EXTENSION in _read(p)]
        assert not offenders, (
            f"task-12.1 steering must not reference {LEGACY_HOOK_EXTENSION}; "
            f"offending files: {offenders}"
        )

    def test_legacy_removal_word_only_in_removal_prose(self) -> None:
        """Any ``userTriggered`` mention sits on a removal-context line.

        Passes vacuously today (the word is absent from all four files) but
        guards against a future reintroduction outside removal prose.
        """
        bad: dict[str, list[str]] = {}
        for path in ALL_FOUR_FILES:
            offending = [
                line.strip()
                for line in _read(path).splitlines()
                if LEGACY_REMOVAL_WORD in line and not _line_has_marker(line)
            ]
            if offending:
                bad[path.name] = offending
        assert not bad, (
            "task-12.1 steering may reference 'userTriggered' only as removal "
            f"prose; offending lines: {bad}"
        )


# ===========================================================================
# TestCommonmarkNotCriticalHook  (Requirements 10.5)
# ===========================================================================


class TestCommonmarkNotCriticalHook:
    """``commonmark-validation`` is routed to a slash command, not a hook.

    The onboarding critical-hook creation list / failure-impact messaging must
    not present ``commonmark-validation`` as a critical (automatic) hook. Every
    line naming the exact id must carry a slash-command / removal marker; a
    ``/commonmark-validation`` slash-command reference is the intended form.

    Feature: kiro-1-0-migration
    **Validates: Requirements 10.5**
    """

    def test_commonmark_not_in_capture_critical_set(self) -> None:
        """commonmark-validation is not one of the capture-critical hooks."""
        assert COMMONMARK_HOOK_ID not in CAPTURE_CRITICAL_HOOK_IDS, (
            "commonmark-validation must not be treated as a capture-critical hook"
        )

    def test_commonmark_id_only_appears_with_slash_or_removal_marker(self) -> None:
        """Every ``commonmark-validation`` line routes to the slash command.

        A line presenting the id as a plain critical/automatic hook (no slash /
        removal marker) is a violation of Req 10.5.
        """
        offenders: dict[str, list[str]] = {}
        for path in ALL_FOUR_FILES:
            bad = [
                line.strip()
                for line in _read(path).splitlines()
                if COMMONMARK_HOOK_ID in line and not _line_has_marker(line)
            ]
            if bad:
                offenders[path.name] = bad
        assert not offenders, (
            "commonmark-validation must never be presented as a critical/"
            "automatic hook; each mention must route to the /commonmark-validation "
            f"slash command. Offending lines: {offenders}"
        )

    def test_onboarding_flow_routes_to_slash_command(self) -> None:
        """onboarding-flow.md points bootcampers to /commonmark-validation."""
        text = _read(ONBOARDING_FLOW)
        assert COMMONMARK_SLASH_COMMAND in text, (
            "onboarding-flow.md must route Markdown validation to the "
            f"{COMMONMARK_SLASH_COMMAND} slash command"
        )
