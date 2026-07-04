"""Tests for the TypeScript build-from-source failure recovery branch (Module 2).

Feature: typescript-build-failure-recovery

Module 2 (SDK Setup) installs the Senzing SDK for the bootcamper's chosen language.
On the TypeScript path, the ``sz-napi`` binding may require building from source
(Rust toolchain, ``node-gyp``, a C++ compiler, ``napi-rs``) — the most failure-prone
install path in the bootcamp. This feature adds a dedicated **Recovery_Branch** to
``module-02-sdk-setup.md`` Step 3 Phase 3 that, on a Mid_Build_Failure, routes to
recovery instead of the generic error handling, summarizes the failure in plain
language against a known-cause table, offers a fix / retry / Fallback_Path triad,
resumes or continues Module 2, and guarantees a non-looping continuation so a build
failure is never a dead end.

Because the shipped surface is steering content (not a runtime script or hook), the
testable specification is a small pure **reference model** of the recovery decision
graph — failure-cause classes -> recovery options -> continuations — encoded here,
test-only. The model-level properties (1-6) exercise this reference model; the
content properties (7-8) read the **real** steering files
(``module-02-sdk-setup.md``, ``lang-typescript.md``).

This module holds the reference-model types and function stubs (task 1.1). Function
bodies, strategies, and the property/unit tests are added by subsequent tasks.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable (scripts aren't packages)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# ---------------------------------------------------------------------------
# Reference model (test-only): the recovery decision graph
#
# This is NOT shipped steering or a runtime script. It is the machine-checkable
# specification the steering-content tests are validated against.
# ---------------------------------------------------------------------------


class CauseClass(Enum):
    """Known common causes of a TypeScript Mid_Build_Failure (plus UNKNOWN)."""

    NODE_VERSION = auto()
    NATIVE_ADDON = auto()
    TOOLCHAIN = auto()
    MODULE_SYSTEM = auto()
    PKG_MANAGER = auto()
    UNKNOWN = auto()  # unrecognized Mid_Build_Failure signal


class Option(Enum):
    """Recovery options offered inside the Recovery_Branch."""

    FIX = auto()
    RETRY = auto()
    FALLBACK = auto()


class State(Enum):
    """States of the recovery decision graph."""

    RECOVERY = auto()  # inside the Recovery_Branch, options offered
    RESUME_MODULE2 = auto()  # normal SDK-setup sequence resumed (retry success)
    CONTINUE_MODULE2 = auto()  # continued via Fallback_Path (no from-source build)
    BLOCKED_WITH_SUPPORT = auto()  # options exhausted: blocker + support, non-looping


@dataclass(frozen=True)
class Recovery:
    """A recovery presentation for a classified Mid_Build_Failure.

    Attributes:
        cause: The classified cause of the failure.
        summary: Plain-language summary that names the cause.
        fix_reference: The ``lang-typescript.md`` "Common Environment Issues" entry title.
        options: The recovery options offered (always includes FIX, RETRY, FALLBACK).
    """

    cause: CauseClass
    summary: str
    fix_reference: str
    options: frozenset[Option]


# ---------------------------------------------------------------------------
# Known-cause table (design.md: "Known-cause table")
#
# Each cause class maps to the distinctive substrings that identify it in a raw
# build-failure signal. classify_failure checks these in priority order so that
# overlapping tokens (e.g. "ERR!") resolve to the most specific cause.
# ---------------------------------------------------------------------------

# Ordered most-specific-first so overlapping tokens resolve deterministically.
_CAUSE_PATTERNS: tuple[tuple[CauseClass, tuple[str, ...]], ...] = (
    (CauseClass.NATIVE_ADDON, ("gyp ERR! build error", "gyp ERR!", ".node'")),
    (
        CauseClass.MODULE_SYSTEM,
        ("ERR_REQUIRE_ESM", "Cannot use import statement outside a module"),
    ),
    (
        CauseClass.NODE_VERSION,
        ("ERR_UNSUPPORTED_ESM_URL_SCHEME", "SyntaxError", "Node.js version 18"),
    ),
    (
        CauseClass.TOOLCHAIN,
        ("C++ compiler", "Rust toolchain", "Visual Studio Build Tools"),
    ),
    (CauseClass.PKG_MANAGER, ("ERESOLVE", "lockfile")),
)

# Representative known-pattern signals per cause class, used by the st_failure_signal
# strategy. Each must classify to its own cause class via classify_failure.
_KNOWN_SIGNALS: dict[CauseClass, tuple[str, ...]] = {
    CauseClass.NODE_VERSION: (
        "SyntaxError: Unexpected token '?'",
        "ERR_UNSUPPORTED_ESM_URL_SCHEME",
        "engine requires Node.js version 18 or higher (found v16.20.2)",
    ),
    CauseClass.NATIVE_ADDON: (
        "gyp ERR! build error",
        "Error: Cannot find module '../build/Release/sz-napi.node'",
    ),
    CauseClass.TOOLCHAIN: (
        "error: no C++ compiler found on this system",
        "error: Rust toolchain not found; install rustup",
        "Visual Studio Build Tools are required to compile native addons",
    ),
    CauseClass.MODULE_SYSTEM: (
        "Error [ERR_REQUIRE_ESM]: require() of ES Module not supported",
        "SyntaxError: Cannot use import statement outside a module",
    ),
    CauseClass.PKG_MANAGER: (
        "npm ERR! code ERESOLVE unable to resolve dependency tree",
        "npm ERR! lockfile conflict detected",
    ),
}

# Flat list of every distinctive substring, used to filter arbitrary strategy inputs
# so generated "non-matching" signals genuinely classify as UNKNOWN.
_ALL_PATTERN_TOKENS: tuple[str, ...] = tuple(
    token for _, tokens in _CAUSE_PATTERNS for token in tokens
)

# ---------------------------------------------------------------------------
# Recovery presentation tables (design.md: "Known-cause table" and
# "Recovery presentation")
#
# Each known cause maps to a human-readable name (used in the plain-language
# summary) and the title of the corresponding lang-typescript.md "Common
# Environment Issues" entry (used as the fix reference). UNKNOWN names an
# unrecognized failure and points at the whole section plus MCP search_docs.
# ---------------------------------------------------------------------------

_CAUSE_NAMES: dict[CauseClass, str] = {
    CauseClass.NODE_VERSION: "Node.js version conflict",
    CauseClass.NATIVE_ADDON: "native addon (node-gyp) build failure",
    CauseClass.TOOLCHAIN: "missing build toolchain",
    CauseClass.MODULE_SYSTEM: "ESM vs CommonJS module resolution",
    CauseClass.PKG_MANAGER: "package manager conflict",
    CauseClass.UNKNOWN: "an unrecognized build failure",
}

_FIX_REFERENCES: dict[CauseClass, str] = {
    CauseClass.NODE_VERSION: "Node.js Version Conflicts",
    CauseClass.NATIVE_ADDON: "Native Addon Build Failures (node-gyp)",
    CauseClass.TOOLCHAIN: (
        "Native Addon Build Failures (node-gyp)"
        " (see also the Module 2 Windows build-tools note)"
    ),
    CauseClass.MODULE_SYSTEM: "ESM vs CommonJS Module Resolution",
    CauseClass.PKG_MANAGER: "Package Manager Conflicts",
    CauseClass.UNKNOWN: (
        'the "Common Environment Issues" section, plus MCP search_docs'
    ),
}


# ---------------------------------------------------------------------------
# Reference-model functions
# ---------------------------------------------------------------------------


def classify_failure(signal: str) -> CauseClass:
    """Map a raw build-failure signal to a CauseClass (total; UNKNOWN otherwise).

    Args:
        signal: The salient token from the build output.

    Returns:
        The matched CauseClass, or CauseClass.UNKNOWN if no known pattern matches.
    """
    for cause, tokens in _CAUSE_PATTERNS:
        if any(token in signal for token in tokens):
            return cause
    return CauseClass.UNKNOWN


def route(signal: str) -> State:
    """Route any Mid_Build_Failure signal to the Recovery_Branch.

    Args:
        signal: The salient token from the build output.

    Returns:
        State.RECOVERY for every Mid_Build_Failure signal.
    """
    return State.RECOVERY


def build_recovery(cause: CauseClass) -> Recovery:
    """Build the recovery presentation (summary, fix reference, options) for a cause.

    Args:
        cause: The classified cause of the failure.

    Returns:
        A Recovery whose options always include FIX, RETRY, and FALLBACK.
    """
    name = _CAUSE_NAMES[cause]
    summary = f"The build failed due to {name}."
    return Recovery(
        cause=cause,
        summary=summary,
        fix_reference=_FIX_REFERENCES[cause],
        options=frozenset({Option.FIX, Option.RETRY, Option.FALLBACK}),
    )


def transition(state: State, option: Option | None, retry_ok: bool) -> State:
    """Compute the next state given the current state, chosen option, and retry result.

    Exhaustion is modeled with a sentinel: passing ``option=None`` means every
    recovery option has been exhausted, which transitions the active branch to the
    distinct, non-looping ``BLOCKED_WITH_SUPPORT`` terminal state. Terminal states
    (``RESUME_MODULE2``, ``CONTINUE_MODULE2``, ``BLOCKED_WITH_SUPPORT``) are
    absorbing so the branch never loops back into the originating error.

    Transition table (design.md: "State transitions"):
        (RECOVERY, RETRY, retry_ok=True)  -> RESUME_MODULE2
        (RECOVERY, RETRY, retry_ok=False) -> RECOVERY
        (RECOVERY, FIX, _)                -> RECOVERY
        (RECOVERY, FALLBACK, _)           -> CONTINUE_MODULE2
        (RECOVERY, exhausted, _)          -> BLOCKED_WITH_SUPPORT

    Args:
        state: The current state.
        option: The chosen recovery option, or ``None`` when options are exhausted.
        retry_ok: Whether a retried build succeeded.

    Returns:
        The next state per the design's transition table.
    """
    # Terminal states are absorbing: never re-enter the originating error.
    if state is not State.RECOVERY:
        return state

    # Options exhausted -> distinct, non-looping terminal state.
    if option is None:
        return State.BLOCKED_WITH_SUPPORT

    if option is Option.FALLBACK:
        return State.CONTINUE_MODULE2
    if option is Option.FIX:
        return State.RECOVERY
    if option is Option.RETRY:
        return State.RESUME_MODULE2 if retry_ok else State.RECOVERY

    # Defensive default: remain in the branch (still offering continuations).
    return State.RECOVERY


def continuations(recovery: Recovery) -> frozenset[Option]:
    """Return the available continuation options (never empty while the branch is active).

    Args:
        recovery: The current recovery presentation.

    Returns:
        The subset of options that continue Module 2 (RETRY and/or FALLBACK).
    """
    return recovery.options & {Option.RETRY, Option.FALLBACK}


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_failure_signal(draw: st.DrawFn) -> str:
    """Generate a Mid_Build_Failure signal string.

    Produces either a known-pattern signal for one of the recognized cause classes
    (which classify to that class) or an arbitrary non-matching string (which must
    classify as ``CauseClass.UNKNOWN``). Arbitrary strings are filtered to exclude
    every known distinctive substring so their UNKNOWN classification is guaranteed.

    Returns:
        A raw build-failure signal string.
    """
    known = [signal for signals in _KNOWN_SIGNALS.values() for signal in signals]
    arbitrary = st.text().filter(
        lambda s: not any(token in s for token in _ALL_PATTERN_TOKENS)
    )
    return draw(st.one_of(st.sampled_from(known), arbitrary))


def st_cause_class() -> st.SearchStrategy[CauseClass]:
    """Generate a CauseClass, including UNKNOWN.

    Returns:
        A strategy sampling from every member of the CauseClass enum.
    """
    return st.sampled_from(list(CauseClass))


@st.composite
def st_retry_sequence(draw: st.DrawFn) -> list[bool]:
    """Generate a sequence of retry outcomes: failures followed by an optional success.

    Each element is a retry result (``False`` = the retried build failed again,
    ``True`` = it eventually succeeded). Sequences model the "failed-then-eventual"
    outcomes the Recovery_Branch must survive: zero or more failed retries, optionally
    capped by a single successful retry. The empty sequence (no retries attempted) is
    included, and a success — when present — is always the terminal element.

    Returns:
        A list of booleans representing successive retry results.
    """
    failures = draw(st.integers(min_value=0, max_value=5))
    eventual_success = draw(st.booleans())
    sequence = [False] * failures
    if eventual_success:
        sequence.append(True)
    return sequence


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestRoutingToRecoveryBranch:
    """Property tests for routing a Mid_Build_Failure to the Recovery_Branch.

    Validates: Requirements 1.1
    """

    # Feature: typescript-build-failure-recovery, Property 1: Every
    # Mid_Build_Failure routes to the Recovery_Branch
    @given(st_failure_signal())
    def test_every_mid_build_failure_routes_to_recovery(self, signal: str) -> None:
        """Any Mid_Build_Failure signal routes to State.RECOVERY, not generic error handling.

        Validates: Requirements 1.1
        """
        assert route(signal) is State.RECOVERY


class TestSummaryNamesMatchedCause:
    """Property tests for the summary naming the matched common cause.

    Validates: Requirements 1.2, 1.3
    """

    # Feature: typescript-build-failure-recovery, Property 2: The summary names
    # the matched common cause
    @given(st_cause_class())
    def test_summary_names_the_matched_cause(self, cause: CauseClass) -> None:
        """build_recovery(cause) yields a non-empty summary naming that cause.

        For any cause class the summary is non-empty and names the cause (its
        human-readable name appears in the summary text). For every known common
        cause (non-UNKNOWN) the recovery also maps to a known-cause fix_reference
        entry drawn from lang-typescript.md "Common Environment Issues".

        Validates: Requirements 1.2, 1.3
        """
        recovery = build_recovery(cause)

        # Summary is a non-empty plain-language string.
        assert isinstance(recovery.summary, str)
        assert recovery.summary.strip()

        # The summary names the cause (its human-readable name is present).
        assert _CAUSE_NAMES[cause] in recovery.summary

        # Every known common cause maps to a known-cause fix_reference entry.
        if cause is not CauseClass.UNKNOWN:
            assert recovery.fix_reference == _FIX_REFERENCES[cause]
            assert recovery.fix_reference.strip()


class TestRecoveryOffersTriad:
    """Property tests for the fix / retry / fallback triad on every recovery.

    Validates: Requirements 2.1
    """

    # Feature: typescript-build-failure-recovery, Property 3: Every recovery
    # offers the fix / retry / fallback triad
    @given(st_cause_class())
    def test_recovery_offers_fix_retry_fallback_triad(self, cause: CauseClass) -> None:
        """build_recovery(cause).options is a superset of {FIX, RETRY, FALLBACK}.

        For any cause class (including UNKNOWN), the offered options include, at
        minimum, fix-the-common-cause guidance, a retry of the build, and a
        Fallback_Path — so every recognized or unrecognized Mid_Build_Failure gets
        the full recovery triad.

        Validates: Requirements 2.1
        """
        recovery = build_recovery(cause)
        assert recovery.options >= {Option.FIX, Option.RETRY, Option.FALLBACK}


class TestChosenPathsContinueModule2:
    """Property tests for chosen recovery paths continuing Module 2.

    Validates: Requirements 2.2, 2.3
    """

    # Feature: typescript-build-failure-recovery, Property 4: Chosen recovery
    # paths continue Module 2
    @given(st.booleans())
    def test_chosen_paths_continue_module2(self, retry_ok: bool) -> None:
        """Retry-on-success resumes Module 2; Fallback_Path continues it regardless of retry.

        Choosing retry after a successful build (retry_ok=True) transitions the
        active Recovery_Branch to RESUME_MODULE2 (the normal SDK-setup sequence).
        Choosing the Fallback_Path transitions to CONTINUE_MODULE2 for any retry
        outcome — it never requires a successful from-source build.

        Validates: Requirements 2.2, 2.3
        """
        # Retry after a successful build resumes the normal Module 2 sequence.
        assert (
            transition(State.RECOVERY, Option.RETRY, retry_ok=True)
            is State.RESUME_MODULE2
        )

        # The Fallback_Path continues Module 2 regardless of the retry outcome.
        assert (
            transition(State.RECOVERY, Option.FALLBACK, retry_ok)
            is State.CONTINUE_MODULE2
        )


class TestBuildFailureNeverADeadEnd:
    """Property tests for the never-a-dead-end guarantee.

    Validates: Requirements 4.1
    """

    # Feature: typescript-build-failure-recovery, Property 5: A build failure is never a dead end
    @given(st_cause_class(), st_retry_sequence())
    def test_build_failure_is_never_a_dead_end(
        self, cause: CauseClass, retry_sequence: list[bool]
    ) -> None:
        """continuations(recovery) is non-empty for any cause and any retry sequence.

        For any cause class (recognized or UNKNOWN) and any sequence of failed
        (and optionally eventually-successful) retries, the Recovery_Branch always
        leaves at least one way forward while active: continuations(recovery) is
        non-empty and offers at least one of RETRY / FALLBACK. The retry outcomes
        never strip the branch of a continuation, so a build failure is never a
        dead end.

        Validates: Requirements 4.1
        """
        recovery = build_recovery(cause)
        available = continuations(recovery)

        # There is always a way forward while the branch is active.
        assert available
        # And that way forward is one of retry-after-fix or the Fallback_Path.
        assert available <= {Option.RETRY, Option.FALLBACK}
        assert available & {Option.RETRY, Option.FALLBACK}


class TestExhaustionTerminalState:
    """Property tests for the exhaustion terminal state.

    Validates: Requirements 4.2
    """

    # Feature: typescript-build-failure-recovery, Property 6: Exhausting options
    # reaches a distinct, non-looping terminal state
    @given(st.booleans())
    def test_exhausting_options_reaches_distinct_non_looping_terminal_state(
        self, retry_ok: bool
    ) -> None:
        """Exhausting options lands in BLOCKED_WITH_SUPPORT: distinct and non-looping.

        For any recovery whose options are all exhausted (modeled by the
        ``option=None`` sentinel), the active Recovery_Branch transitions to
        BLOCKED_WITH_SUPPORT — a state distinct from RECOVERY. That terminal state
        is absorbing: no chosen option (or further exhaustion) transitions it back
        into RECOVERY, so it never re-enters the originating error.

        Validates: Requirements 4.2
        """
        # Exhausting options transitions the active branch to the terminal state.
        assert (
            transition(State.RECOVERY, None, retry_ok) is State.BLOCKED_WITH_SUPPORT
        )

        # The terminal state is distinct from the active RECOVERY state.
        assert State.BLOCKED_WITH_SUPPORT is not State.RECOVERY

        # BLOCKED_WITH_SUPPORT is absorbing / non-looping: no option (or further
        # exhaustion) re-enters the originating RECOVERY error.
        for option in (Option.FIX, Option.RETRY, Option.FALLBACK, None):
            next_state = transition(State.BLOCKED_WITH_SUPPORT, option, retry_ok)
            assert next_state is State.BLOCKED_WITH_SUPPORT
            assert next_state is not State.RECOVERY


# ---------------------------------------------------------------------------
# Real-steering helpers (content properties read the shipped steering files)
#
# Property 7 reads the *real* module-02-sdk-setup.md and asserts over the lines
# of the Recovery_Branch subsection. These helpers locate that file and extract
# the subsection text robustly.
# ---------------------------------------------------------------------------

_MODULE_02_PATH = (
    Path(__file__).resolve().parent.parent / "steering" / "module-02-sdk-setup.md"
)

# The exact heading authored in task 6.1 (Step 3, Phase 3).
_RECOVERY_HEADING = "### Recovery: build-from-source failures (TypeScript)"

# The subsection ends before this Phase 3 note, which follows it but is not part
# of the Recovery_Branch.
_SHELL_CONFIG_NOTE = "NEVER modify the user's global shell configuration"


def _extract_recovery_subsection(text: str) -> list[str]:
    """Extract the Recovery_Branch subsection lines from module-02-sdk-setup.md.

    The subsection begins at the "### Recovery: build-from-source failures
    (TypeScript)" heading and ends before whichever comes first: the next
    Markdown heading of equal or higher level (a line whose first non-space
    character is ``#``) or the "NEVER modify the user's global shell
    configuration" note that follows it in Phase 3.

    Args:
        text: The full contents of ``module-02-sdk-setup.md``.

    Returns:
        The subsection lines, including the heading line.

    Raises:
        AssertionError: If the Recovery_Branch heading is not found.
    """
    lines = text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == _RECOVERY_HEADING:
            start = index
            break
    assert start is not None, (
        "Recovery_Branch heading not found in module-02-sdk-setup.md"
    )

    subsection = [lines[start]]
    for line in lines[start + 1 :]:
        # Stop at the next heading of equal/higher level.
        if line.lstrip().startswith("#"):
            break
        # Stop at the shell-config note that follows the subsection.
        if _SHELL_CONFIG_NOTE in line:
            break
        subsection.append(line)
    return subsection


def _load_recovery_subsection_lines() -> list[str]:
    """Read the real steering file and return the Recovery_Branch subsection lines.

    Returns:
        The subsection lines extracted from the real ``module-02-sdk-setup.md``.
    """
    text = _MODULE_02_PATH.read_text(encoding="utf-8")
    return _extract_recovery_subsection(text)


# Extracted once at import time from the real, shipped steering file.
_RECOVERY_SUBSECTION_LINES = _load_recovery_subsection_lines()
_RECOVERY_SUBSECTION_TEXT = "\n".join(_RECOVERY_SUBSECTION_LINES)


class TestRecoverySourcingNoHardcodedUrls:
    """Property tests for MCP/lang-typescript sourcing with no hardcoded URLs.

    Reads the *real* ``module-02-sdk-setup.md`` Recovery_Branch subsection.

    Validates: Requirements 2.4
    """

    # Feature: typescript-build-failure-recovery, Property 7: Recovery guidance
    # is MCP/lang-typescript-sourced with no hardcoded URLs
    @given(st.sampled_from(_RECOVERY_SUBSECTION_LINES))
    def test_no_hardcoded_urls_in_recovery_subsection(self, line: str) -> None:
        """No line of the real Recovery_Branch subsection contains an http(s):// URL.

        For any line sampled from the extracted subsection of the real
        ``module-02-sdk-setup.md``, the text contains no hardcoded external
        ``http://`` or ``https://`` URL — all external/toolchain knowledge is
        sourced via the MCP tools or ``lang-typescript.md`` rather than pasted URLs.

        Validates: Requirements 2.4
        """
        assert "http://" not in line
        assert "https://" not in line

    def test_recovery_subsection_references_mcp_and_lang_typescript(self) -> None:
        """The subsection references sdk_guide, search_docs, and lang-typescript.md.

        The Recovery_Branch sources its detailed fixes from the Senzing MCP tools
        (``sdk_guide`` / ``search_docs``) and the ``lang-typescript.md`` "Common
        Environment Issues" content — this companion assertion confirms those
        references are present in the real subsection text.

        Validates: Requirements 2.4
        """
        assert "sdk_guide" in _RECOVERY_SUBSECTION_TEXT
        assert "search_docs" in _RECOVERY_SUBSECTION_TEXT
        assert "lang-typescript.md" in _RECOVERY_SUBSECTION_TEXT


# ---------------------------------------------------------------------------
# Real-steering helpers (Property 8 reads the shipped lang-typescript.md)
#
# Property 8 asserts that every known common cause named by the branch maps to
# a real entry in the lang-typescript.md "Common Environment Issues" section, so
# the Recovery_Branch references — rather than duplicates — the reactive
# TypeScript troubleshooting content.
# ---------------------------------------------------------------------------

_LANG_TYPESCRIPT_PATH = (
    Path(__file__).resolve().parent.parent / "steering" / "lang-typescript.md"
)

# The exact heading of the reactive-troubleshooting section in lang-typescript.md.
_COMMON_ISSUES_HEADING = "## Common Environment Issues"


def _core_fix_title(fix_reference: str) -> str:
    """Strip the parenthetical Module 2 note from a fix_reference to get the entry title.

    The TOOLCHAIN fix reference reuses the node-gyp entry and appends a "(see also
    the Module 2 Windows build-tools note)" pointer. The lang-typescript.md entry
    heading is the core title without that pointer, so this returns the text before
    the " (see also" marker (and leaves other references, including the
    "(node-gyp)" that is part of the real heading, intact).

    Args:
        fix_reference: A ``_FIX_REFERENCES`` value.

    Returns:
        The core lang-typescript.md entry title to look for as a heading.
    """
    marker = " (see also"
    index = fix_reference.find(marker)
    if index != -1:
        return fix_reference[:index].strip()
    return fix_reference.strip()


def _extract_common_issues_entry_titles(text: str) -> list[str]:
    """Extract the entry (``### ``) titles of the "Common Environment Issues" section.

    The section begins at the "## Common Environment Issues" heading and ends
    before the next section heading of equal or higher level (a line beginning
    with ``## `` or ``# ``). Each ``### `` heading within it is an entry title.

    Args:
        text: The full contents of ``lang-typescript.md``.

    Returns:
        The entry titles (heading text without the ``### `` prefix), in order.

    Raises:
        AssertionError: If the "Common Environment Issues" heading is not found.
    """
    lines = text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == _COMMON_ISSUES_HEADING:
            start = index
            break
    assert start is not None, (
        "'Common Environment Issues' heading not found in lang-typescript.md"
    )

    entry_titles: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        # Stop at the next section heading of equal/higher level.
        if stripped.startswith("## ") or stripped.startswith("# "):
            break
        if stripped.startswith("### "):
            entry_titles.append(stripped[len("### ") :].strip())
    return entry_titles


# Read the real lang-typescript.md once and extract its section entry titles.
_LANG_TYPESCRIPT_TEXT = _LANG_TYPESCRIPT_PATH.read_text(encoding="utf-8")
_COMMON_ISSUES_ENTRY_TITLES = _extract_common_issues_entry_titles(_LANG_TYPESCRIPT_TEXT)


class TestNamedCauseMapsToLangTypescriptEntry:
    """Property tests for the named-cause -> lang-typescript.md mapping.

    Reads the *real* ``lang-typescript.md`` "Common Environment Issues" section.

    Validates: Requirements 3.1
    """

    # Feature: typescript-build-failure-recovery, Property 8: Every named cause
    # maps to a lang-typescript.md troubleshooting entry
    @given(st_cause_class())
    def test_named_cause_maps_to_troubleshooting_entry(
        self, cause: CauseClass
    ) -> None:
        """Every known cause's fix reference matches a real "Common Environment Issues" entry.

        For any known common cause (a non-UNKNOWN ``CauseClass``), the core entry
        title of its ``_FIX_REFERENCES`` value appears as an entry heading in the
        real ``lang-typescript.md`` "Common Environment Issues" section — so the
        Recovery_Branch references, rather than duplicates, the reactive
        TypeScript troubleshooting content. For UNKNOWN, the general section itself
        exists (it has at least one entry to point at).

        Validates: Requirements 3.1
        """
        # The general section exists and has troubleshooting entries.
        assert _COMMON_ISSUES_HEADING in _LANG_TYPESCRIPT_TEXT
        assert _COMMON_ISSUES_ENTRY_TITLES

        if cause is CauseClass.UNKNOWN:
            # UNKNOWN points at the whole section, not a specific entry.
            return

        core_title = _core_fix_title(_FIX_REFERENCES[cause])
        assert core_title in _COMMON_ISSUES_ENTRY_TITLES, (
            f"Fix reference {core_title!r} for {cause.name} is not a "
            "'Common Environment Issues' entry in lang-typescript.md"
        )


# ---------------------------------------------------------------------------
# Content / flow unit and example tests over the real steering (task 8.3)
#
# These are concrete example/unit checks (not @given properties) asserting the
# authored Recovery_Branch subsection and its consistency with the module's
# TypeScript-maturity framing. They read the *real* shipped steering via the
# module-level helpers/constants defined above (_RECOVERY_SUBSECTION_TEXT,
# _RECOVERY_SUBSECTION_LINES, _MODULE_02_PATH) and the reference model
# (classify_failure / route / CauseClass / State). Assertions prefer
# case-insensitive substring checks on distinctive phrases to avoid brittleness.
# ---------------------------------------------------------------------------

# Case-insensitive view of the real subsection text, computed once, so the
# content assertions below are robust to capitalization/markdown emphasis.
_RECOVERY_SUBSECTION_TEXT_LOWER = _RECOVERY_SUBSECTION_TEXT.lower()

# The full, real module text (not just the subsection) — used to confirm the
# maturity-framing warning the fallback option must stay consistent with.
_MODULE_02_FULL_TEXT_LOWER = _MODULE_02_PATH.read_text(encoding="utf-8").lower()


class TestRecoveryContentAndFlow:
    """Content/flow example tests over the real Recovery_Branch steering.

    Concrete (non-property) checks that the authored subsection in the real
    ``module-02-sdk-setup.md`` routes a mid-build failure into the branch,
    orders the plain-language summary before the options, lists the fix / retry
    / Fallback_Path triad, resumes vs. continues Module 2 correctly, keeps the
    TypeScript-maturity framing consistent, and describes a non-looping terminal
    state. Fixtures are synthetic and PII-free.

    Validates: Requirements 1.1, 1.2, 2.1, 2.2, 2.3, 3.2, 4.2
    """

    def test_routing_preempts_generic_error_handling(self) -> None:
        """A gyp ERR! failure enters the Recovery_Branch, not the generic SENZ path.

        The reference model classifies a synthetic ``gyp ERR!`` signal as
        NATIVE_ADDON and routes it to State.RECOVERY, and the real subsection
        text instructs the agent NOT to fall through to the module's generic
        Error Handling (SENZ-code / ``common-pitfalls.md``) block.

        Validates: Requirements 1.1
        """
        # Synthetic, PII-free failure signal.
        signal = "gyp ERR! build error"

        # The reference model pre-empts: recognized native-addon cause, routed
        # to the Recovery_Branch (never the module's generic error handling).
        assert classify_failure(signal) is CauseClass.NATIVE_ADDON
        assert route(signal) is State.RECOVERY

        # The authored subsection lists the gyp ERR! signal in its known-cause
        # table and instructs against falling through to the generic path.
        assert "gyp err! build error" in _RECOVERY_SUBSECTION_TEXT_LOWER
        assert "fall through" in _RECOVERY_SUBSECTION_TEXT_LOWER
        assert "generic error handling" in _RECOVERY_SUBSECTION_TEXT_LOWER
        assert "common-pitfalls.md" in _RECOVERY_SUBSECTION_TEXT_LOWER

    def test_summary_appears_before_options(self) -> None:
        """The plain-language summary instruction precedes the options list.

        In the real subsection, the "summarize before offering options"
        instruction appears at an earlier position than the "offer targeted
        options" list, so the failure is explained before choices are given.

        Validates: Requirements 1.2
        """
        summary_index = _RECOVERY_SUBSECTION_TEXT_LOWER.find(
            "summarize before offering options"
        )
        options_index = _RECOVERY_SUBSECTION_TEXT_LOWER.find(
            "offer targeted options"
        )

        # Both instructions are present in the subsection.
        assert summary_index != -1, "summary instruction not found in subsection"
        assert options_index != -1, "options instruction not found in subsection"

        # And the summary is ordered before the options.
        assert summary_index < options_index

    def test_option_triad_present(self) -> None:
        """The branch lists the fix / retry / Fallback_Path option triad.

        The real subsection text names all three recovery options: fix the
        common cause, retry the build, and the Fallback_Path.

        Validates: Requirements 2.1
        """
        assert "fix the common cause" in _RECOVERY_SUBSECTION_TEXT_LOWER
        assert "retry the build" in _RECOVERY_SUBSECTION_TEXT_LOWER
        assert "fallback_path" in _RECOVERY_SUBSECTION_TEXT_LOWER

    def test_resume_on_retry_success_vs_continue_on_fallback(self) -> None:
        """Retry-success resumes Phase 3 -> Step 4; Fallback_Path continues Module 2.

        The subsection instructs that a successful retry resumes the normal
        sequence (Phase 3 bindings, then Step 4 verification), while the
        Fallback_Path continues Module 2 without requiring a successful
        from-source build. The reference-model transitions mirror this split.

        Validates: Requirements 2.2, 2.3
        """
        # Retry-success resumption wording: names the successful retry and the
        # Phase 3 -> Step 4 resumption target.
        assert "successful retry" in _RECOVERY_SUBSECTION_TEXT_LOWER
        assert "phase 3" in _RECOVERY_SUBSECTION_TEXT_LOWER
        assert "step 4" in _RECOVERY_SUBSECTION_TEXT_LOWER

        # Fallback continuation wording: continue Module 2 without a from-source build.
        assert (
            "without a successful from-source build"
            in _RECOVERY_SUBSECTION_TEXT_LOWER
        )

        # The reference model agrees: retry-on-success resumes, fallback continues.
        assert (
            transition(State.RECOVERY, Option.RETRY, retry_ok=True)
            is State.RESUME_MODULE2
        )
        assert (
            transition(State.RECOVERY, Option.FALLBACK, retry_ok=False)
            is State.CONTINUE_MODULE2
        )

    def test_maturity_framing_consistency(self) -> None:
        """The fallback framing is consistent with the TypeScript-maturity warning.

        The module's existing warning frames TypeScript setup as "more involved"
        and notes "Java or C# typically have simpler install paths". The
        Recovery_Branch's Fallback_Path option must align with — not contradict —
        that framing: it offers switching to a simpler-install language using the
        same phrasing.

        Validates: Requirements 3.2
        """
        # The maturity warning exists in the real module text (the framing the
        # fallback must stay consistent with).
        assert "more involved" in _MODULE_02_FULL_TEXT_LOWER
        assert (
            "java or c# typically have simpler install paths"
            in _MODULE_02_FULL_TEXT_LOWER
        )

        # The Recovery_Branch fallback aligns with that framing: switching to a
        # language with a simpler install path, using the same phrasing.
        assert "simpler install path" in _RECOVERY_SUBSECTION_TEXT_LOWER
        assert "java or c#" in _RECOVERY_SUBSECTION_TEXT_LOWER

    def test_terminal_state_states_blocker_and_does_not_reloop(self) -> None:
        """The exhaustion path states a blocker + next steps, not a re-run of the same command.

        When every option is exhausted, the subsection instructs stating the
        current blocker and the support / next-step options, and explicitly
        instructs NOT to re-run the same failing command — a distinct,
        non-looping terminal state. The reference model reaches the matching
        BLOCKED_WITH_SUPPORT terminal state.

        Validates: Requirements 4.2
        """
        # Names a blocker and support / next-step options.
        assert "state the current blocker" in _RECOVERY_SUBSECTION_TEXT_LOWER
        assert "support / next-step" in _RECOVERY_SUBSECTION_TEXT_LOWER

        # Does NOT instruct re-running the same failing command; instead the
        # subsection explicitly forbids it.
        assert (
            "do not re-run the same failing command"
            in _RECOVERY_SUBSECTION_TEXT_LOWER
        )

        # The reference model reaches the distinct, non-looping terminal state
        # when options are exhausted (modeled by the option=None sentinel).
        assert (
            transition(State.RECOVERY, None, retry_ok=False)
            is State.BLOCKED_WITH_SUPPORT
        )
        assert State.BLOCKED_WITH_SUPPORT is not State.RECOVERY


# ---------------------------------------------------------------------------
# Steering-index token-sync smoke check (task 8.4)
#
# A single deterministic check (not a property) that the shipped
# steering-index.yaml token_count for module-02-sdk-setup.md is in sync with the
# real file's measured count in BOTH entries (the module-tree phase entry and
# the flat file_metadata entry) and, equivalently, that the maintained
# measure_steering.py --check validation passes. This guards Requirement 3.3
# (the feature updates any affected steering-file token counts).
# ---------------------------------------------------------------------------

# Absolute paths to the real steering dir and index, derived from the real
# module-02 steering file location so cwd never affects the check.
_STEERING_DIR = _MODULE_02_PATH.parent
_STEERING_INDEX_PATH = _STEERING_DIR / "steering-index.yaml"


class TestSteeringIndexTokenSync:
    """Deterministic smoke check that steering-index token counts stay in sync.

    Reads the *real* ``module-02-sdk-setup.md`` and ``steering-index.yaml`` and
    invokes the maintained ``measure_steering.py`` check in-process. Not a
    property test.

    Validates: Requirements 3.3
    """

    def test_measure_steering_check_passes(self) -> None:
        """Both module-02 index entries match the measured count and --check passes.

        Asserts the stored ``token_count`` for ``module-02-sdk-setup.md`` in both
        the flat ``file_metadata`` entry and the module-tree phase entry match the
        real file's freshly measured count (within the tool's 10% sync tolerance),
        then invokes ``measure_steering.py --check`` in-process against the real
        steering dir/index and asserts a clean exit (code 0 / no mismatches).

        Validates: Requirements 3.3
        """
        import pytest

        import measure_steering

        module_name = _MODULE_02_PATH.name  # "module-02-sdk-setup.md"
        measured = measure_steering.calculate_token_count(_MODULE_02_PATH)
        content = measure_steering.load_yaml_content(_STEERING_INDEX_PATH)

        # Flat file_metadata entry (near line 470) is in sync with the real file.
        stored_metadata = measure_steering._parse_stored_metadata(content) or {}
        assert module_name in stored_metadata, (
            f"{module_name} missing from file_metadata in steering-index.yaml"
        )
        flat_count = stored_metadata[module_name].get("token_count")
        assert flat_count is not None, (
            f"{module_name} file_metadata entry has no token_count"
        )
        assert abs(flat_count - measured) / max(measured, 1) <= 0.10, (
            f"file_metadata token_count {flat_count} out of sync with "
            f"measured {measured} for {module_name}"
        )

        # Module-tree phase entry (near line 22) is in sync with the real file.
        phase_entries = [
            entry
            for entry in measure_steering._parse_phase_entries(content)
            if entry.filename == module_name
        ]
        assert phase_entries, (
            f"no module-tree phase entry for {module_name} in steering-index.yaml"
        )
        for entry in phase_entries:
            assert entry.token_count is not None, (
                f"phase entry for {module_name} has no token_count"
            )
            assert abs(entry.token_count - measured) / max(measured, 1) <= 0.10, (
                f"phase token_count {entry.token_count} out of sync with "
                f"measured {measured} for {module_name}"
            )

        # Equivalently, measure_steering.py --check passes end-to-end. main()
        # reads sys.argv and calls sys.exit(), so drive it with absolute paths
        # (cwd-independent) and assert a clean exit code of 0.
        argv = [
            "measure_steering.py",
            "--check",
            "--steering-dir",
            str(_STEERING_DIR),
            "--index-path",
            str(_STEERING_INDEX_PATH),
        ]
        saved_argv = sys.argv
        sys.argv = argv
        try:
            with pytest.raises(SystemExit) as excinfo:
                measure_steering.main()
        finally:
            sys.argv = saved_argv
        assert excinfo.value.code == 0, (
            "measure_steering.py --check reported token-count mismatches"
        )
