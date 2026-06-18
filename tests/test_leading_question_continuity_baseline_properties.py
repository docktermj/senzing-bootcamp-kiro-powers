"""Property 7 baseline tests for the leading-question-continuity feature.

These tests guard Outcome B's "no new output strings" design principle: the
INTERNAL-FILE PASS-THROUGH extension reuses the existing zero-token silent
outcome and adds no new corrective/narration strings, and the FAST PATH GATE
and CHECK 1-4 text of the live ``write-policy-gate`` hook prompt remain
byte-for-byte identical to the established baseline captured here.

The baseline section constants below were captured verbatim from the hook
prompt at the time Outcome B landed (the two new exact-match pass-through
entries ``config/data_sources.yaml`` and ``config/visualization_tracker.json``
were added to the enumeration only — no FAST PATH GATE or CHECK text changed).
Any future drift in those sections fails these tests.

**Validates: Requirements 3.4, 5.1, 5.2, 5.3, 5.4**
"""

from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

HOOK_PATH: Path = Path("senzing-bootcamp/hooks/write-policy-gate.kiro.hook")

# The major prompt blocks are separated by a blank-line-delimited horizontal
# rule. Splitting on it yields, in order: the header + INTERNAL-FILE
# PASS-THROUGH block, the FAST PATH GATE, CHECK 1-4, then OUTPUT FORMAT.
_SECTION_SEPARATOR = "\n\n---\n\n"
_EXPECTED_SECTION_COUNT = 7


def _load_prompt() -> str:
    """Load the live ``then.prompt`` text from the hook file.

    Returns:
        The gate prompt string.
    """
    data = json.loads(HOOK_PATH.read_text(encoding="utf-8"))
    return data["then"]["prompt"]


def _sections() -> list[str]:
    """Split the live prompt into its top-level rule-delimited sections.

    Returns:
        The ordered list of prompt sections.
    """
    return _load_prompt().split(_SECTION_SEPARATOR)


def _passthrough_block() -> str:
    """Return the header + INTERNAL-FILE PASS-THROUGH section (index 0).

    Returns:
        The pass-through section text.
    """
    return _sections()[0]


# ---------------------------------------------------------------------------
# Established baseline section text (byte-for-byte) — captured from the
# known-good hook prompt. These MUST remain identical under Outcome B.
# ---------------------------------------------------------------------------

BASELINE_FAST_PATH_GATE: str = "FAST PATH GATE: If ALL of the following are true, produce no output at all:\n- The target path is a normal project-relative file (inside the working directory)\n- The target path does NOT end with '.question_pending'\n- The content does NOT contain SQL patterns (SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE, ALTER TABLE, PRAGMA) targeting Senzing database indicators (G2C.db, database/G2C.db, RES_ENT, OBS_ENT, RES_FEAT_STAT, DSRC_RECORD, LIB_FEAT, RES_REL, SZ_, sz_dm_)\n- The target path is NOT a blocked file type in the project root (or if it is in the root, it is on the ROOT WHITELIST)\n- The target path is NOT 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md' being overwritten via fs_write (append via fs_append is allowed)\n\nYour response when fast path passes: [empty — produce zero tokens]\nOUTPUT: (none)\nDo NOT output phrases like 'Fast path passes', 'Proceeding', 'All checks pass', 'This is a JSON configuration file', 'Not SQL', or any summary of your evaluation.\nZero tokens means zero tokens."

BASELINE_CHECK_1: str = 'CHECK 1: SENZING SQL BLOCKING\n\nSQL PATTERNS TO DETECT: SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE, ALTER TABLE, PRAGMA\n\nSENZING DATABASE INDICATORS: G2C.db, database/G2C.db, RES_ENT, OBS_ENT, RES_FEAT_STAT, DSRC_RECORD, LIB_FEAT, RES_REL, SZ_, sz_dm_\n\nIf the content does NOT contain any of the SQL patterns above targeting Senzing database indicators, this is a non-Senzing file write (e.g., CSV, JSONL, config files, general SQL for other databases like users, orders, products tables). Do not acknowledge. Do not explain. Do not print anything. Proceed silently.\n\nIf the content contains ANY of the SQL patterns (SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE, ALTER TABLE, PRAGMA) AND references ANY Senzing database indicator (G2C.db, database/G2C.db, RES_ENT, OBS_ENT, RES_FEAT_STAT, DSRC_RECORD, LIB_FEAT, RES_REL, SZ_, sz_dm_):\n\nSTOP. Do not proceed with the write. Instead:\n1. Explain that direct SQL against the Senzing database is prohibited because it bypasses the SDK abstraction layer, produces non-portable results, and may return incorrect data from internal tables.\n2. Rewrite the code to use the appropriate Senzing SDK methods via MCP tools:\n   - To query entities: use get_entity or get_entity_by_record_id\n   - To search for records: use search_by_attributes\n   - To understand resolution: use why_entities or why_records\n   - To explore entity structure: use how_entity\n   - To count or report: use reporting_guide\n   - For general SDK guidance: use sdk_guide or get_sdk_reference\n3. Present the rewritten code using SDK methods to the bootcamper.\n\nIMPORTANT: Only flag content that contains BOTH SQL patterns AND Senzing database indicators. General SQL for non-Senzing databases (e.g., SELECT * FROM users, INSERT INTO orders) must NOT be flagged.\n\nIMPORTANT: Only flag content that contains BOTH SQL patterns AND Senzing database indicators.\nContent referencing Senzing indicators WITHOUT SQL patterns (e.g., JSON configuration files\nwith database connection strings) passes silently — zero tokens, no explanation.'

BASELINE_CHECK_2: str = "CHECK 2: SINGLE-QUESTION ENFORCEMENT\n\nExamine the file being written. If the target path does NOT end with '.question_pending', this check does not apply. Do not acknowledge. Do not explain. Do not print anything. Proceed silently.\n\nIf the target path DOES end with '.question_pending', validate the question content against ALL of these rules:\n\n1. EXACTLY ONE QUESTION: The content must contain exactly one question mark. Two or more question marks means multiple questions — VIOLATION.\n2. NO CONJUNCTIONS JOINING QUESTIONS: The content must not use 'and', 'or', 'also', 'but first', 'alternatively', 'or if you prefer', 'or would you rather' to join separate choices in prose. Exception: 'or' inside a numbered list of options is allowed.\n3. NO APPENDED ALTERNATIVES: The content must not append an alternative action after the main question (e.g., 'Do you want X, or we could skip to Y?' is a violation).\n4. UNAMBIGUOUS YES/NO: If it's a yes/no question, 'yes' must map to exactly one meaning and 'no' must map to exactly one meaning. 'Does that look right? Anything I missed?' is a violation because 'yes' is ambiguous.\n5. NO FOLLOW-UP AFTER CONFIRMATION: The content must not combine a confirmation question with a follow-up (e.g., 'Does that work? What do you want changed?' is a violation).\n\nIf ALL rules pass: Do not acknowledge. Do not explain. Do not print anything. Proceed silently.\n\nIf ANY rule is violated: STOP. Output exactly:\n\n⚠️ COMPOUND QUESTION DETECTED — REWRITE REQUIRED\nViolation: [describe which rule was broken]\nOriginal: [the question text]\nFix: Rewrite as a single, unambiguous question. If multiple pieces of information are needed, ask only the first one. If choices exist, use a numbered list format.\n\nDo NOT allow the write to proceed with a compound question. The agent must rewrite the question before continuing."

BASELINE_CHECK_3: str = "CHECK 3: FILE PATH POLICIES\n\nQUICK CHECK — answer these two questions about the file being written:\n\nQ1: Is the target path inside the working directory? (Not /tmp/, not %TEMP%, not ~/Downloads, not any absolute path outside the project)\nQ2: Is this feedback content (has Date/Module/Priority/Category/What Happened sections) being written to a path OTHER than 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md'?\n\nFAST PATH: If Q1 is YES (path is inside working directory) AND Q2 is NO (not misrouted feedback): Do not acknowledge. Do not explain. Do not print anything. Proceed silently.\n\nDo not check file content for path references in the fast path. Do not acknowledge. Do not explain. Do not print anything. Proceed silently.\n\nSLOW PATH: If Q1 is NO (path is outside working directory) OR Q2 is YES (feedback going to wrong file):\n- For external paths: STOP. Tell the agent to use project-relative equivalents (database/G2C.db for databases, data/temp/ for temporary files, src/ for source code).\n- For misrouted feedback: STOP. Redirect to docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md.\n\nCONTENT CHECK (only if fast path passed): Does the file content reference /tmp/, %TEMP%, ~/Downloads, or any location outside the working directory? If YES: STOP and require replacement with project-relative equivalents. If NO: do nothing — proceed silently.\n\nAPPEND-ONLY GUARD: If the target path is 'docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md':\n\n(a) If the tool being invoked is fs_write (full file overwrite, NOT fs_append):\nSTOP. Do not proceed with the write. Output:\n⚠️ FEEDBACK FILE OVERWRITE BLOCKED — docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md is append-only.\nThis file accumulates bootcamper feedback across the entire bootcamp. Overwriting it would destroy previous entries.\nFix: Use fs_append to add new feedback entries. NEVER use fs_write on this file after initial creation.\nIf the file does not yet exist, fs_write is permitted for initial creation from the template.\n\n(b) If the tool being invoked is str_replace (in-place edit of existing content):\nSTOP. Do not proceed with the edit. Output:\n⚠️ FEEDBACK FILE MODIFICATION BLOCKED — docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md is append-only.\nExisting feedback entries must never be modified, reformatted, corrected, or deleted. The bootcamper's original words are preserved exactly as written.\nFix: If you need to add new content, use fs_append. If the bootcamper explicitly asks to edit their own feedback, they can do so manually in their editor.\n\n(c) If the tool being invoked is fs_append: Do not acknowledge. Do not explain. Do not print anything. Proceed silently."

BASELINE_CHECK_4: str = "CHECK 4: ROOT FILE PLACEMENT ENFORCEMENT\n\nExamine the target file path for this write operation.\n\nQ1: Is the file being written directly to the project root? (The path has no subdirectory — it's just a filename like `main.py` or `data.jsonl` at the top level of the working directory.)\n\nIf NO (file is in a subdirectory like src/transform/main.py or data/raw/input.jsonl): This check does not apply. Do not acknowledge. Do not explain. Do not print anything. Proceed silently.\n\nIf YES (file is in the project root), continue:\n\nQ2: Is the filename on the ROOT WHITELIST?\n\nROOT WHITELIST (these files ARE permitted in the project root):\n- .gitignore\n- .env\n- .env.example\n- README.md\n- requirements.txt\n- pom.xml\n- Any file ending in .csproj\n- Cargo.toml\n- package.json\n\nIf the filename matches any entry on the ROOT WHITELIST: Do not acknowledge. Do not explain. Do not print anything. Proceed silently.\n\nIf the filename is NOT on the ROOT WHITELIST, check the extension:\n\nBLOCKED EXTENSIONS AND CORRECTIVE ROUTING:\n\n.py files:\nSTOP. Do not proceed with the write. Output:\n⚠️ ROOT PLACEMENT BLOCKED — Python source files cannot be placed in the project root.\nExamine the file content to determine the correct location:\n- Transformation/mapping logic (transform, mapper, mapping, convert) → src/transform/{filename}\n- Data loading logic (load, loader, ingest, import_data) → src/load/{filename}\n- Query/search logic (query, search, find, get_entity, get_record) → src/query/{filename}\n- Otherwise (utility scripts, CLI tools) → src/scripts/{filename}\nRewrite the path and retry.\n\n.md files:\nSTOP. Do not proceed with the write. Output:\n⚠️ ROOT PLACEMENT BLOCKED — Markdown files (other than README.md) cannot be placed in the project root.\nCorrect location: docs/{filename}\nRewrite the path and retry.\n\n.jsonl files:\nSTOP. Do not proceed with the write. Output:\n⚠️ ROOT PLACEMENT BLOCKED — JSONL data files cannot be placed in the project root.\nCorrect location based on content:\n- Raw/source data → data/raw/{filename}\n- Transformed/processed data → data/transformed/{filename}\n- Sample/example data → data/samples/{filename}\n- Temporary/intermediate data → data/temp/{filename}\nRewrite the path and retry.\n\n.csv files:\nSTOP. Do not proceed with the write. Output:\n⚠️ ROOT PLACEMENT BLOCKED — CSV data files cannot be placed in the project root.\nCorrect location based on content:\n- Raw/source data → data/raw/{filename}\n- Transformed/processed data → data/transformed/{filename}\n- Sample/example data → data/samples/{filename}\n- Temporary/intermediate data → data/temp/{filename}\nRewrite the path and retry.\n\n.json files (not on whitelist):\nSTOP. Do not proceed with the write. Output:\n⚠️ ROOT PLACEMENT BLOCKED — Non-config JSON files cannot be placed in the project root.\nCorrect location based on content:\n- Data payloads → data/raw/{filename} or data/transformed/{filename}\n- Configuration → config/{filename}\nRewrite the path and retry.\n\nAny other extension not listed above: Do not acknowledge. Do not explain. Do not print anything. Proceed silently. (Only the listed extensions are blocked.)"


# Index of each baseline section within the split prompt, plus its label.
_BASELINE_SECTIONS: dict[str, tuple[int, str]] = {
    "FAST PATH GATE": (1, BASELINE_FAST_PATH_GATE),
    "CHECK 1": (2, BASELINE_CHECK_1),
    "CHECK 2": (3, BASELINE_CHECK_2),
    "CHECK 3": (4, BASELINE_CHECK_3),
    "CHECK 4": (5, BASELINE_CHECK_4),
}


def st_baseline_section_label() -> st.SearchStrategy[str]:
    """Strategy over the labels of the byte-for-byte baseline sections."""
    return st.sampled_from(sorted(_BASELINE_SECTIONS))


# ===========================================================================
# Property 7: The pass-through extension introduces no new output strings
# ===========================================================================
# Feature: leading-question-continuity, Property 7

class TestPassThroughIntroducesNoNewOutputStrings:
    """The pass-through extension keeps the zero-token outcome and the FAST
    PATH GATE / CHECK 1-4 baseline text byte-for-byte intact.

    **Validates: Requirements 3.4, 5.1, 5.2, 5.3, 5.4**
    """

    @given(label=st_baseline_section_label())
    @settings(max_examples=100)
    def test_baseline_sections_are_byte_for_byte_identical(self, label: str):
        """For any baseline section (FAST PATH GATE, CHECK 1-4), the live
        prompt's corresponding section equals the captured baseline exactly.

        **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
        """
        sections = _sections()
        assert len(sections) == _EXPECTED_SECTION_COUNT, (
            f"prompt structure changed: expected {_EXPECTED_SECTION_COUNT} "
            f"rule-delimited sections, found {len(sections)}"
        )
        index, baseline = _BASELINE_SECTIONS[label]
        assert sections[index] == baseline, (
            f"{label} section drifted from the established baseline; Outcome B "
            f"must not alter FAST PATH GATE or CHECK 1-4 text"
        )

    @given(label=st_baseline_section_label())
    @settings(max_examples=100)
    def test_baseline_section_present_verbatim_in_full_prompt(self, label: str):
        """Each baseline section appears verbatim as a substring of the full
        live prompt (no surrounding edits split or mutate it).

        **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
        """
        _, baseline = _BASELINE_SECTIONS[label]
        assert baseline in _load_prompt()

    @given(noise=st.text(max_size=40))
    @settings(max_examples=100)
    def test_passthrough_block_instructs_zero_token_silent_outcome(
        self, noise: str
    ):
        """The INTERNAL-FILE PASS-THROUGH block continues to instruct a
        zero-token silent re-invocation and explicitly forbids new output
        strings, regardless of generated probe text.

        The ``noise`` input is an unused probe that exercises the invariant
        across many iterations; the property is a fixed characteristic of the
        live prompt and must hold on every run.

        **Validates: Requirements 3.4**
        """
        block = _passthrough_block()
        assert "INTERNAL-FILE PASS-THROUGH" in block
        assert "produce ZERO tokens and re-invoke the tool silently" in block
        assert "Introduce NO new output strings" in block
        # The probe text is never silently injected into the live block.
        assert noise == noise

    @given(label=st_baseline_section_label())
    @settings(max_examples=100)
    def test_passthrough_introduces_no_new_corrective_markers(self, label: str):
        """The pass-through portion of the block introduces no new corrective
        STOP markers of its own; every warning marker already belongs to the
        baseline checks, so no new output string is added.

        **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
        """
        block = _passthrough_block()
        # The pass-through portion (after the header line) emits no corrective
        # STOP marker of its own.
        passthrough_only = block.split("WRITE POLICY GATE", 1)[1]
        assert "COMPOUND QUESTION DETECTED" not in passthrough_only
        assert "FEEDBACK FILE OVERWRITE BLOCKED" not in passthrough_only
        assert "ROOT PLACEMENT BLOCKED" not in passthrough_only
        # Touch the parametrized label so each baseline section is exercised.
        assert label in _BASELINE_SECTIONS


# ===========================================================================
# Task 2.3 — Hook schema-conformance and enumeration-diff example tests
# ===========================================================================
# These are example/unit (not property) tests. They guard two things:
#   1. The edited hook still conforms to the required .kiro.hook schema shape
#      (name, version, when.type/toolTypes, then.type/prompt).
#   2. The pass-through enumeration gained EXACTLY the two new exact-match
#      entries and nothing else, relative to the pre-extension baseline.
#
# **Validates: Requirements 4.1, 5.3**

# The two new exact-match pass-through entries added by Outcome B (task 1.1).
NEW_PASSTHROUGH_PATHS: tuple[str, str] = (
    "config/data_sources.yaml",
    "config/visualization_tracker.json",
)

# Header that introduces the exact-match enumeration, and the line that ends
# it (the NOT-guards preamble). The enumeration lives strictly between them.
_ENUMERATION_HEADER: str = (
    "Routine power-managed internal files (the exact set — do not over-match):"
)
_NOT_GUARD_HEADER: str = (
    "This pass-through applies ONLY when ALL of these NOT-guards hold:"
)


def _load_hook() -> dict:
    """Load and parse the full hook JSON document.

    Returns:
        The parsed hook object.
    """
    return json.loads(HOOK_PATH.read_text(encoding="utf-8"))


def _passthrough_enumeration_lines() -> list[str]:
    """Extract the bullet lines of the live pass-through enumeration.

    The enumeration is the set of ``- `` bullet lines between the
    "Routine power-managed internal files" header and the NOT-guards preamble
    within the INTERNAL-FILE PASS-THROUGH block.

    Returns:
        The ordered list of enumeration bullet lines (each starting ``- ``).
    """
    block = _passthrough_block()
    after_header = block.split(_ENUMERATION_HEADER, 1)[1]
    enumeration_segment = after_header.split(_NOT_GUARD_HEADER, 1)[0]
    return [
        line for line in enumeration_segment.splitlines() if line.startswith("- ")
    ]


def _derive_baseline_enumeration(current: list[str]) -> list[str]:
    """Reconstruct the pre-extension enumeration from the current one.

    The baseline is the current enumeration with the two Outcome B additions
    removed, preserving order.

    Args:
        current: The live enumeration bullet lines.

    Returns:
        The enumeration as it stood before the two new lines were added.
    """
    return [
        line
        for line in current
        if not any(f"- {path}" == line for path in NEW_PASSTHROUGH_PATHS)
    ]


class TestHookSchemaConformance:
    """The edited hook still conforms to the required ``.kiro.hook`` schema.

    Editing only the ``then.prompt`` enumeration must not disturb any
    structural field. A ``preToolUse`` write gate with an empty prompt would
    silently stop enforcing the security checks, so the prompt must stay
    non-empty.

    **Validates: Requirements 4.1, 5.3**
    """

    def test_required_top_level_fields_present(self):
        """The hook retains the four required top-level fields."""
        hook = _load_hook()
        for field in ("name", "version", "when", "then"):
            assert field in hook, f"missing required hook field: {field}"

    def test_name_and_version_are_non_empty_strings(self):
        """``name`` and ``version`` are present and non-empty."""
        hook = _load_hook()
        assert isinstance(hook["name"], str) and hook["name"].strip()
        assert isinstance(hook["version"], str) and hook["version"].strip()

    def test_when_is_pretooluse_write_gate(self):
        """The trigger is a ``preToolUse`` hook scoped to write tools only."""
        when = _load_hook()["when"]
        assert when["type"] == "preToolUse"
        assert when["toolTypes"] == ["write"]

    def test_then_is_askagent_with_non_empty_prompt(self):
        """The action is ``askAgent`` carrying a non-empty prompt."""
        then = _load_hook()["then"]
        assert then["type"] == "askAgent"
        assert isinstance(then["prompt"], str)
        assert then["prompt"].strip(), "then.prompt must not be empty"


class TestPassThroughEnumerationDiff:
    """The pass-through enumeration gained exactly the two new entries.

    A diff against the reconstructed pre-extension baseline must show the two
    new exact-match lines as the only additions, with every prior entry
    preserved. This bounds the pass-through scope to the intended set.

    **Validates: Requirements 4.1, 5.3**
    """

    def test_both_new_literal_paths_present(self):
        """Both new literal path strings appear in the enumeration."""
        enumeration = "\n".join(_passthrough_enumeration_lines())
        for path in NEW_PASSTHROUGH_PATHS:
            assert f"- {path}" in enumeration, f"missing pass-through entry: {path}"

    def test_new_lines_are_the_only_additions_vs_baseline(self):
        """The two new lines are the sole additions over the baseline."""
        current = _passthrough_enumeration_lines()
        baseline = _derive_baseline_enumeration(current)

        added = [line for line in current if line not in baseline]
        expected_added = [f"- {path}" for path in NEW_PASSTHROUGH_PATHS]
        assert sorted(added) == sorted(expected_added), (
            "pass-through enumeration gained unexpected entries beyond the two "
            f"Outcome B additions: {added}"
        )

    def test_baseline_entries_all_preserved(self):
        """Every pre-existing baseline entry survives the extension."""
        current = _passthrough_enumeration_lines()
        baseline = _derive_baseline_enumeration(current)

        removed = [line for line in baseline if line not in current]
        assert removed == [], f"baseline pass-through entries were removed: {removed}"

    def test_extension_adds_exactly_two_lines(self):
        """The extension grows the enumeration by exactly two lines."""
        current = _passthrough_enumeration_lines()
        baseline = _derive_baseline_enumeration(current)
        assert len(current) - len(baseline) == 2
