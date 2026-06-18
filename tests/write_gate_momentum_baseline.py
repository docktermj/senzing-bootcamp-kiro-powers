"""Captured hook-prompt baseline for the write-gate-momentum-preservation feature.

This module is the single source of truth for the *pre-change baseline* of the
live ``write-policy-gate`` hook prompt that Outcome B (task 2.1) must preserve:

- The FAST PATH GATE and CHECK 1-4 rule-delimited sections, snapshotted
  **byte-for-byte** as ``BASELINE_*`` constants. Property 5 (task 2.6) asserts
  the live prompt's corresponding sections stay identical to these snapshots,
  so any drift in the safety surface fails the build.
- The *pre-extension* INTERNAL-FILE PASS-THROUGH enumeration, reconstructed
  from the live enumeration by removing the two Outcome B additions
  (``config/data_sources.yaml`` and ``config/visualization_tracker.json``).
  The enumeration-diff example test (task 3.2) asserts the live enumeration
  gained exactly those two lines relative to this reconstructed baseline.

It reuses — and does not modify — the public contracts of the two shared
modules this feature depends on:

- ``tests/gate_decision_model.py``: ``WriteOperation``, ``GateDecision``,
  ``gate(op, prompt)``, ``load_gate_prompt()``.
- ``tests/hook_test_helpers.py``: ``load_hook()``, ``validate_required_fields()``,
  Hypothesis strategies.

Baseline accuracy note: the ``BASELINE_*`` constants are the verbatim section
text of the live hook prompt at capture time. They are intentionally embedded
as literals (not derived from the live file at import) so that the snapshot is
an independent frozen reference a drift check can compare against.
"""

from __future__ import annotations

import json
from pathlib import Path

HOOK_PATH: Path = Path("senzing-bootcamp/hooks/write-policy-gate.kiro.hook")

# The major prompt blocks are separated by a blank-line-delimited horizontal
# rule. Splitting on it yields, in order:
#   0: header + INTERNAL-FILE PASS-THROUGH block
#   1: FAST PATH GATE
#   2: CHECK 1
#   3: CHECK 2
#   4: CHECK 3
#   5: CHECK 4
#   6: OUTPUT FORMAT
SECTION_SEPARATOR: str = "\n\n---\n\n"
EXPECTED_SECTION_COUNT: int = 7

# Index of the header + INTERNAL-FILE PASS-THROUGH block within the split prompt.
PASSTHROUGH_SECTION_INDEX: int = 0

# The two new exact-match pass-through entries added by Outcome B (task 2.1).
# Already present in the live hook from the prior landed feature; the
# "pre-extension" baseline is the live enumeration with these two removed.
NEW_PASSTHROUGH_PATHS: tuple[str, str] = (
    "config/data_sources.yaml",
    "config/visualization_tracker.json",
)

# Header that introduces the exact-match enumeration, and the line that ends it
# (the NOT-guards preamble). The enumeration lives strictly between them.
ENUMERATION_HEADER: str = (
    "Routine power-managed internal files (the exact set — do not over-match):"
)
NOT_GUARD_HEADER: str = (
    "This pass-through applies ONLY when ALL of these NOT-guards hold:"
)


# ---------------------------------------------------------------------------
# Live prompt loading / splitting
# ---------------------------------------------------------------------------

def load_hook() -> dict:
    """Load and parse the full live hook JSON document.

    Returns:
        The parsed hook object.
    """
    return json.loads(HOOK_PATH.read_text(encoding="utf-8"))


def load_prompt() -> str:
    """Load the live ``then.prompt`` text from the hook file.

    Returns:
        The gate prompt string.
    """
    return load_hook()["then"]["prompt"]


def sections() -> list[str]:
    """Split the live prompt into its top-level rule-delimited sections.

    Returns:
        The ordered list of prompt sections.
    """
    return load_prompt().split(SECTION_SEPARATOR)


def passthrough_block() -> str:
    """Return the header + INTERNAL-FILE PASS-THROUGH section (index 0).

    Returns:
        The pass-through section text.
    """
    return sections()[PASSTHROUGH_SECTION_INDEX]


# ---------------------------------------------------------------------------
# Captured baseline section text (byte-for-byte). Outcome B must NOT change
# these — only the INTERNAL-FILE PASS-THROUGH enumeration (section 0) is edited.
# ---------------------------------------------------------------------------

BASELINE_FAST_PATH_GATE: str = "FAST PATH GATE: If ALL of the following are true, produce no output at all:\n- The target path is a normal project-relative file (inside the working directory)\n- The target path does NOT end with '.question_pending'\n- The content does NOT contain SQL patterns (SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE, ALTER TABLE, PRAGMA) targeting Senzing database indicators (G2C.db, database/G2C.db, RES_ENT, OBS_ENT, RES_FEAT_STAT, DSRC_RECORD, LIB_FEAT, RES_REL, SZ_, sz_dm_)\n- The target path is NOT a blocked file type in the project root (or if it is in the root, it is on the ROOT WHITELIST)\n- The target path is NOT 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md' being overwritten via fs_write (append via fs_append is allowed)\n\nYour response when fast path passes: [empty — produce zero tokens]\nOUTPUT: (none)\nDo NOT output phrases like 'Fast path passes', 'Proceeding', 'All checks pass', 'This is a JSON configuration file', 'Not SQL', or any summary of your evaluation.\nZero tokens means zero tokens."

BASELINE_CHECK_1: str = 'CHECK 1: SENZING SQL BLOCKING\n\nSQL PATTERNS TO DETECT: SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE, ALTER TABLE, PRAGMA\n\nSENZING DATABASE INDICATORS: G2C.db, database/G2C.db, RES_ENT, OBS_ENT, RES_FEAT_STAT, DSRC_RECORD, LIB_FEAT, RES_REL, SZ_, sz_dm_\n\nIf the content does NOT contain any of the SQL patterns above targeting Senzing database indicators, this is a non-Senzing file write (e.g., CSV, JSONL, config files, general SQL for other databases like users, orders, products tables). Do not acknowledge. Do not explain. Do not print anything. Proceed silently.\n\nIf the content contains ANY of the SQL patterns (SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE, ALTER TABLE, PRAGMA) AND references ANY Senzing database indicator (G2C.db, database/G2C.db, RES_ENT, OBS_ENT, RES_FEAT_STAT, DSRC_RECORD, LIB_FEAT, RES_REL, SZ_, sz_dm_):\n\nSTOP. Do not proceed with the write. Instead:\n1. Explain that direct SQL against the Senzing database is prohibited because it bypasses the SDK abstraction layer, produces non-portable results, and may return incorrect data from internal tables.\n2. Rewrite the code to use the appropriate Senzing SDK methods via MCP tools:\n   - To query entities: use get_entity or get_entity_by_record_id\n   - To search for records: use search_by_attributes\n   - To understand resolution: use why_entities or why_records\n   - To explore entity structure: use how_entity\n   - To count or report: use reporting_guide\n   - For general SDK guidance: use sdk_guide or get_sdk_reference\n3. Present the rewritten code using SDK methods to the bootcamper.\n\nIMPORTANT: Only flag content that contains BOTH SQL patterns AND Senzing database indicators. General SQL for non-Senzing databases (e.g., SELECT * FROM users, INSERT INTO orders) must NOT be flagged.\n\nIMPORTANT: Only flag content that contains BOTH SQL patterns AND Senzing database indicators.\nContent referencing Senzing indicators WITHOUT SQL patterns (e.g., JSON configuration files\nwith database connection strings) passes silently — zero tokens, no explanation.'

BASELINE_CHECK_2: str = "CHECK 2: SINGLE-QUESTION ENFORCEMENT\n\nExamine the file being written. If the target path does NOT end with '.question_pending', this check does not apply. Do not acknowledge. Do not explain. Do not print anything. Proceed silently.\n\nIf the target path DOES end with '.question_pending', validate the question content against ALL of these rules:\n\n1. EXACTLY ONE QUESTION: The content must contain exactly one question mark. Two or more question marks means multiple questions — VIOLATION.\n2. NO CONJUNCTIONS JOINING QUESTIONS: The content must not use 'and', 'or', 'also', 'but first', 'alternatively', 'or if you prefer', 'or would you rather' to join separate choices in prose. Exception: 'or' inside a numbered list of options is allowed.\n3. NO APPENDED ALTERNATIVES: The content must not append an alternative action after the main question (e.g., 'Do you want X, or we could skip to Y?' is a violation).\n4. UNAMBIGUOUS YES/NO: If it's a yes/no question, 'yes' must map to exactly one meaning and 'no' must map to exactly one meaning. 'Does that look right? Anything I missed?' is a violation because 'yes' is ambiguous.\n5. NO FOLLOW-UP AFTER CONFIRMATION: The content must not combine a confirmation question with a follow-up (e.g., 'Does that work? What do you want changed?' is a violation).\n\nIf ALL rules pass: Do not acknowledge. Do not explain. Do not print anything. Proceed silently.\n\nIf ANY rule is violated: STOP. Output exactly:\n\n⚠️ COMPOUND QUESTION DETECTED — REWRITE REQUIRED\nViolation: [describe which rule was broken]\nOriginal: [the question text]\nFix: Rewrite as a single, unambiguous question. If multiple pieces of information are needed, ask only the first one. If choices exist, use a numbered list format.\n\nDo NOT allow the write to proceed with a compound question. The agent must rewrite the question before continuing."

BASELINE_CHECK_3: str = "CHECK 3: FILE PATH POLICIES\n\nQUICK CHECK — answer these two questions about the file being written:\n\nQ1: Is the target path inside the working directory? (Not /tmp/, not %TEMP%, not ~/Downloads, not any absolute path outside the project)\nQ2: Is this feedback content (has Date/Module/Priority/Category/What Happened sections) being written to a path OTHER than 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md'?\n\nFAST PATH: If Q1 is YES (path is inside working directory) AND Q2 is NO (not misrouted feedback): Do not acknowledge. Do not explain. Do not print anything. Proceed silently.\n\nDo not check file content for path references in the fast path. Do not acknowledge. Do not explain. Do not print anything. Proceed silently.\n\nSLOW PATH: If Q1 is NO (path is outside working directory) OR Q2 is YES (feedback going to wrong file):\n- For external paths: STOP. Tell the agent to use project-relative equivalents (database/G2C.db for databases, data/temp/ for temporary files, src/ for source code).\n- For misrouted feedback: STOP. Redirect to docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md.\n\nCONTENT CHECK (only if fast path passed): Does the file content reference /tmp/, %TEMP%, ~/Downloads, or any location outside the working directory? If YES: STOP and require replacement with project-relative equivalents. If NO: do nothing — proceed silently.\n\nAPPEND-ONLY GUARD: If the target path is 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md':\n\n(a) If the tool being invoked is fs_write (full file overwrite, NOT fs_append):\nSTOP. Do not proceed with the write. Output:\n⚠️ FEEDBACK FILE OVERWRITE BLOCKED — docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md is append-only.\nThis file accumulates bootcamper feedback across the entire bootcamp. Overwriting it would destroy previous entries.\nFix: Use fs_append to add new feedback entries. NEVER use fs_write on this file after initial creation.\nIf the file does not yet exist, fs_write is permitted for initial creation from the template.\n\n(b) If the tool being invoked is str_replace (in-place edit of existing content):\nSTOP. Do not proceed with the edit. Output:\n⚠️ FEEDBACK FILE MODIFICATION BLOCKED — docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md is append-only.\nExisting feedback entries must never be modified, reformatted, corrected, or deleted. The bootcamper's original words are preserved exactly as written.\nFix: If you need to add new content, use fs_append. If the bootcamper explicitly asks to edit their own feedback, they can do so manually in their editor.\n\n(c) If the tool being invoked is fs_append: Do not acknowledge. Do not explain. Do not print anything. Proceed silently."

BASELINE_CHECK_4: str = "CHECK 4: ROOT FILE PLACEMENT ENFORCEMENT\n\nExamine the target file path for this write operation.\n\nQ1: Is the file being written directly to the project root? (The path has no subdirectory — it's just a filename like `main.py` or `data.jsonl` at the top level of the working directory.)\n\nIf NO (file is in a subdirectory like src/transform/main.py or data/raw/input.jsonl): This check does not apply. Do not acknowledge. Do not explain. Do not print anything. Proceed silently.\n\nIf YES (file is in the project root), continue:\n\nQ2: Is the filename on the ROOT WHITELIST?\n\nROOT WHITELIST (these files ARE permitted in the project root):\n- .gitignore\n- .env\n- .env.example\n- README.md\n- requirements.txt\n- pom.xml\n- Any file ending in .csproj\n- Cargo.toml\n- package.json\n\nIf the filename matches any entry on the ROOT WHITELIST: Do not acknowledge. Do not explain. Do not print anything. Proceed silently.\n\nIf the filename is NOT on the ROOT WHITELIST, check the extension:\n\nBLOCKED EXTENSIONS AND CORRECTIVE ROUTING:\n\n.py files:\nSTOP. Do not proceed with the write. Output:\n⚠️ ROOT PLACEMENT BLOCKED — Python source files cannot be placed in the project root.\nExamine the file content to determine the correct location:\n- Transformation/mapping logic (transform, mapper, mapping, convert) → src/transform/{filename}\n- Data loading logic (load, loader, ingest, import_data) → src/load/{filename}\n- Query/search logic (query, search, find, get_entity, get_record) → src/query/{filename}\n- Otherwise (utility scripts, CLI tools) → src/scripts/{filename}\nRewrite the path and retry.\n\n.md files:\nSTOP. Do not proceed with the write. Output:\n⚠️ ROOT PLACEMENT BLOCKED — Markdown files (other than README.md) cannot be placed in the project root.\nCorrect location: docs/{filename}\nRewrite the path and retry.\n\n.jsonl files:\nSTOP. Do not proceed with the write. Output:\n⚠️ ROOT PLACEMENT BLOCKED — JSONL data files cannot be placed in the project root.\nCorrect location based on content:\n- Raw/source data → data/raw/{filename}\n- Transformed/processed data → data/transformed/{filename}\n- Sample/example data → data/samples/{filename}\n- Temporary/intermediate data → data/temp/{filename}\nRewrite the path and retry.\n\n.csv files:\nSTOP. Do not proceed with the write. Output:\n⚠️ ROOT PLACEMENT BLOCKED — CSV data files cannot be placed in the project root.\nCorrect location based on content:\n- Raw/source data → data/raw/{filename}\n- Transformed/processed data → data/transformed/{filename}\n- Sample/example data → data/samples/{filename}\n- Temporary/intermediate data → data/temp/{filename}\nRewrite the path and retry.\n\n.json files (not on whitelist):\nSTOP. Do not proceed with the write. Output:\n⚠️ ROOT PLACEMENT BLOCKED — Non-config JSON files cannot be placed in the project root.\nCorrect location based on content:\n- Data payloads → data/raw/{filename} or data/transformed/{filename}\n- Configuration → config/{filename}\nRewrite the path and retry.\n\nAny other extension not listed above: Do not acknowledge. Do not explain. Do not print anything. Proceed silently. (Only the listed extensions are blocked.)"


# Ordered map: baseline section label -> (index in the split prompt, baseline text).
BASELINE_SECTIONS: dict[str, tuple[int, str]] = {
    "FAST PATH GATE": (1, BASELINE_FAST_PATH_GATE),
    "CHECK 1": (2, BASELINE_CHECK_1),
    "CHECK 2": (3, BASELINE_CHECK_2),
    "CHECK 3": (4, BASELINE_CHECK_3),
    "CHECK 4": (5, BASELINE_CHECK_4),
}

# Convenience tuple of the baseline section labels, in prompt order.
BASELINE_SECTION_LABELS: tuple[str, ...] = tuple(BASELINE_SECTIONS)


# ---------------------------------------------------------------------------
# Pass-through enumeration: live extraction + pre-extension reconstruction
# ---------------------------------------------------------------------------

def live_enumeration_lines() -> list[str]:
    """Extract the bullet lines of the live pass-through enumeration.

    The enumeration is the set of ``- `` bullet lines between the
    "Routine power-managed internal files" header and the NOT-guards preamble
    within the INTERNAL-FILE PASS-THROUGH block.

    Returns:
        The ordered list of enumeration bullet lines (each starting ``- ``).
    """
    block = passthrough_block()
    after_header = block.split(ENUMERATION_HEADER, 1)[1]
    enumeration_segment = after_header.split(NOT_GUARD_HEADER, 1)[0]
    return [
        line for line in enumeration_segment.splitlines() if line.startswith("- ")
    ]


def reconstruct_baseline_enumeration(current: list[str] | None = None) -> list[str]:
    """Reconstruct the pre-extension enumeration from the live one.

    The pre-extension baseline is the current enumeration with the two
    Outcome B additions (``NEW_PASSTHROUGH_PATHS``) removed, preserving order.

    Args:
        current: The live enumeration bullet lines. Defaults to
            ``live_enumeration_lines()``.

    Returns:
        The enumeration as it stood before the two new lines were added.
    """
    if current is None:
        current = live_enumeration_lines()
    return [
        line
        for line in current
        if not any(f"- {path}" == line for path in NEW_PASSTHROUGH_PATHS)
    ]
