"""Gate decision model for the write-policy-gate UX bugfix.

This module builds a decision model of the `write-policy-gate` `preToolUse`
hook from the *live* prompt text in
``senzing-bootcamp/hooks/write-policy-gate.kiro.hook``. The model mirrors the
prompt's four-check branch logic and, critically, whether the prompt contains
an INTERNAL-FILE PASS-THROUGH clause that excludes routine power-managed
internal files from the intercept-retry cycle.

The model is read from the live hook file on every call, so the same tests
exercise the *unfixed* prompt (no pass-through clause) before the fix and the
*fixed* prompt (with the clause) after it.

Key concepts (see `.kiro/specs/write-policy-gate-ux/design.md`):

- A `preToolUse` write hook *holds* (intercepts) the tool call before it runs.
  The IDE surfaces a held write as "Rejected creation of ..."; the agent then
  re-issues the identical write and it completes as "Accepted edits to ...".
  So *interception itself* — not the check outcome — is what produces the
  noisy "Rejected" message.
- A clean write that passes all four checks is still *intercepted* on the
  unfixed gate (there is no clause recognizing internal files as a class that
  never needs interception). It therefore still produces the "Rejected" pair.
- The fix adds an INTERNAL-FILE PASS-THROUGH clause that *excludes* such writes
  from interception entirely, so no "Rejected" message is produced.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Hook location
# ---------------------------------------------------------------------------

HOOK_PATH: Path = Path("senzing-bootcamp/hooks/write-policy-gate.kiro.hook")

# ---------------------------------------------------------------------------
# Decision outcomes
# ---------------------------------------------------------------------------

PASS_SILENT = "PASS_SILENT"
INTERCEPT_CORRECTIVE = "INTERCEPT_CORRECTIVE"


@dataclass(frozen=True)
class WriteOperation:
    """A write tool call the gate inspects."""

    path: str
    content: str
    tool: str = "fs_write"


@dataclass(frozen=True)
class GateDecision:
    """The modeled outcome of the gate for one write.

    Attributes:
        outcome: ``PASS_SILENT`` (no corrective output) or
            ``INTERCEPT_CORRECTIVE`` (a corrective STOP/redirect message).
        intercepted: Whether the `preToolUse` hook *held* the write before it
            ran. A held write is surfaced by the IDE as "Rejected creation of
            ...". This is True for every write the gate processes through the
            normal interception path, and False only when the write is excluded
            via the INTERNAL-FILE PASS-THROUGH clause.
        category: Corrective category when ``outcome`` is
            ``INTERCEPT_CORRECTIVE``; otherwise ``None``.
    """

    outcome: str
    intercepted: bool
    category: str | None = None


# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

def load_gate_prompt(hook_path: Path | None = None) -> str:
    """Load the ``then.prompt`` text from the live hook file.

    Args:
        hook_path: Optional override for the hook file path.

    Returns:
        The gate prompt string.
    """
    path = hook_path or HOOK_PATH
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["then"]["prompt"]


# ---------------------------------------------------------------------------
# Policy predicates (mirror the four checks in the prompt)
# ---------------------------------------------------------------------------

# Routine power-managed internal files (exact paths).
_INTERNAL_EXACT: frozenset[str] = frozenset(
    {
        "config/bootcamp_progress.json",
        "config/bootcamp_preferences.yaml",
    }
)

# Member-scoped progress / preference files (colocated team mode).
_MEMBER_PROGRESS_RE = re.compile(r"^config/progress_[A-Za-z0-9_-]+\.json$")
_MEMBER_PREFERENCES_RE = re.compile(r"^config/preferences_[A-Za-z0-9_-]+\.yaml$")

# Power-written session/recap log files (e.g., docs/progress/MODULE_*_COMPLETE.md).
_POWER_LOG_RE = re.compile(r"^docs/progress/MODULE_[^/]*_COMPLETE\.md$")

FEEDBACK_FILE = "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md"

# Senzing SQL detection.
_SQL_PATTERNS = (
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "CREATE TABLE",
    "DROP TABLE",
    "ALTER TABLE",
    "PRAGMA",
)
_SENZING_INDICATORS = (
    "G2C.db",
    "database/G2C.db",
    "RES_ENT",
    "OBS_ENT",
    "RES_FEAT_STAT",
    "DSRC_RECORD",
    "LIB_FEAT",
    "RES_REL",
    "SZ_",
    "sz_dm_",
)

# Root file-placement enforcement.
_ROOT_WHITELIST: frozenset[str] = frozenset(
    {
        ".gitignore",
        ".env",
        ".env.example",
        "README.md",
        "requirements.txt",
        "pom.xml",
        "Cargo.toml",
        "package.json",
    }
)
_ROOT_BLOCKED_EXTENSIONS = (".py", ".md", ".jsonl", ".csv", ".json")

# External-path indicators.
_EXTERNAL_PREFIXES = ("/tmp/", "%TEMP%", "~/Downloads", "/var/", "C:\\")


def is_power_managed_internal_file(path: str) -> bool:
    """Return True for routine power-managed internal bookkeeping files."""
    if path in _INTERNAL_EXACT:
        return True
    if _MEMBER_PROGRESS_RE.match(path):
        return True
    if _MEMBER_PREFERENCES_RE.match(path):
        return True
    if _POWER_LOG_RE.match(path):
        return True
    return False


def is_feedback_file(path: str) -> bool:
    """Return True for the append-only feedback file."""
    return path == FEEDBACK_FILE


def contains_senzing_sql(content: str) -> bool:
    """Return True if content has an SQL pattern AND a Senzing DB indicator."""
    upper = content.upper()
    has_sql = any(pat in upper for pat in _SQL_PATTERNS)
    if not has_sql:
        return False
    has_indicator = any(ind in content for ind in _SENZING_INDICATORS)
    return has_indicator


def is_external_path(path: str) -> bool:
    """Return True if the path is outside the working directory."""
    return any(path.startswith(prefix) for prefix in _EXTERNAL_PREFIXES)


def is_root_blocked_placement(path: str) -> bool:
    """Return True if path is a blocked file type placed in the project root."""
    if "/" in path or "\\" in path:
        return False  # has a subdirectory — not a root placement
    if path in _ROOT_WHITELIST:
        return False
    if path.endswith(".csproj"):
        return False  # whitelisted by pattern
    return any(path.endswith(ext) for ext in _ROOT_BLOCKED_EXTENSIONS)


def is_compound_question(content: str) -> bool:
    """Minimal compound-question detector for `.question_pending` content.

    Mirrors the prompt's single-question rule loosely: more than one question
    mark, or a conjunction joining choices, is a compound question.
    """
    if content.count("?") >= 2:
        return True
    joiners = (" and ", " or ", " also ", " but first ", " alternatively ")
    lowered = content.lower()
    return any(j in lowered for j in joiners) and "?" in content


def is_bug_condition(op: WriteOperation) -> bool:
    """Return True iff the write triggers the cosmetic intercept-noise defect.

    A routine power-managed internal file the gate has no genuine policy to
    enforce against — it would always pass all four checks.
    """
    return (
        is_power_managed_internal_file(op.path)
        and not op.path.endswith(".question_pending")
        and not is_feedback_file(op.path)
        and not contains_senzing_sql(op.content)
        and not is_root_blocked_placement(op.path)
    )


# ---------------------------------------------------------------------------
# Pass-through clause detection (present only after the fix)
# ---------------------------------------------------------------------------

_PASS_THROUGH_RE = re.compile(
    r"internal[-\s]?file\s+pass[-\s]?through", re.IGNORECASE
)


def prompt_has_internal_pass_through(prompt: str) -> bool:
    """Return True if the prompt contains an INTERNAL-FILE PASS-THROUGH clause.

    The fix (design Change A) inserts this clause at the top of the prompt so
    routine power-managed internal files are excluded from interception. The
    unfixed prompt has no such clause.
    """
    return _PASS_THROUGH_RE.search(prompt) is not None


# ---------------------------------------------------------------------------
# Gate decision model
# ---------------------------------------------------------------------------

def gate(op: WriteOperation, prompt: str) -> GateDecision:
    """Model the gate decision for a write under the given prompt.

    Args:
        op: The write operation being inspected.
        prompt: The live gate prompt text (unfixed or fixed).

    Returns:
        The modeled :class:`GateDecision`.
    """
    # INTERNAL-FILE PASS-THROUGH — present only after the fix. When the clause
    # exists and the write is a bug-condition internal file, the gate excludes
    # it from interception entirely (no "Rejected" message).
    if prompt_has_internal_pass_through(prompt) and is_bug_condition(op):
        return GateDecision(PASS_SILENT, intercepted=False)

    # Otherwise the preToolUse hook HOLDS (intercepts) the write before it runs.
    # The IDE surfaces every held write as "Rejected creation of ...".
    intercepted = True

    # Check 1 — Senzing SQL blocking.
    if contains_senzing_sql(op.content):
        return GateDecision(INTERCEPT_CORRECTIVE, intercepted, "senzing_sql")

    # Check 2 — single-question enforcement.
    if op.path.endswith(".question_pending") and is_compound_question(op.content):
        return GateDecision(INTERCEPT_CORRECTIVE, intercepted, "single_question")

    # Check 3 — feedback append-only guard.
    if is_feedback_file(op.path) and op.tool in ("fs_write", "str_replace"):
        return GateDecision(INTERCEPT_CORRECTIVE, intercepted, "feedback_append_only")

    # Check 3 — external-path redirect.
    if is_external_path(op.path):
        return GateDecision(INTERCEPT_CORRECTIVE, intercepted, "external_path")

    # Check 4 — root file placement.
    if is_root_blocked_placement(op.path):
        return GateDecision(INTERCEPT_CORRECTIVE, intercepted, "root_placement")

    # Fast path: all four checks pass, but the write was STILL held/intercepted
    # (no pass-through clause), so the cosmetic "Rejected" -> "Accepted" pair is
    # produced even though no corrective output is emitted.
    return GateDecision(PASS_SILENT, intercepted=True)


def produces_rejected_message(decision: GateDecision) -> bool:
    """Return True if the decision produces an IDE "Rejected" message.

    A held (intercepted) write is surfaced by the IDE as "Rejected creation of
    ...", regardless of whether a corrective message is also emitted. Only a
    write excluded via the pass-through clause avoids the "Rejected" message.
    """
    return decision.intercepted
