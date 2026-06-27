"""Preservation property tests for the steering-index token-count sync bugfix.

Property 2 (Preservation) — non-drifted entries and existing behavior are
unchanged by the fix.

These tests follow the observation-first methodology: the stable (non-phase)
regions of the live ``steering-index.yaml`` are snapshotted via SHA-256 on the
UNFIXED code and pinned as the ``_BASELINE_HASHES`` constant below. Every
assertion is structured to hold on the current unfixed ``measure_steering.py``,
capturing the baseline behavior that the fix must preserve.

The fix touches only ``phases.*.token_count`` and the dependent
``phases.*.size_category`` of drifted phase entries. Therefore:

- ``file_metadata`` validation (tolerance + missing/removed detection) is
  unchanged (Requirement 3.1).
- ``budget`` (incl. ``split_threshold_tokens``), ``keywords``, ``languages``,
  ``deployment``, and every module ``root`` / ``step_range`` are byte-preserved
  (Requirements 3.3, 3.4, 3.5).
- ``budget.total_tokens`` stays the sum of ``file_metadata`` counts; phase
  counts are excluded (Requirement 3.3).
- Phase entries already within the 10% tolerance are left unchanged and are
  not flagged by ``--check`` (Requirements 3.2, 3.6).

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
"""

from __future__ import annotations

import hashlib
import importlib
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import hypothesis.strategies as st
from hypothesis import example, given, settings

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_INDEX_PATH = _STEERING_DIR / "steering-index.yaml"
_SCRIPT_PATH = Path(_SCRIPTS_DIR) / "measure_steering.py"

# The same tolerance the script applies to file_metadata.
_TOLERANCE = 0.10

# SHA-256 of the stable (non-phase) regions of the live steering-index.yaml,
# snapshotted on the UNFIXED code. The fix must leave these byte-identical.
_BASELINE_HASHES: dict[str, str] = {
    # Re-baselined for the write-policy-gate-ux batch. NOTE: this baseline was
    # ALSO stale on main before this batch — a prior commit moved the live total
    # to 174709 without updating this constant (it still pinned 173650). This
    # batch makes two legitimate token changes: Change B added a "## 0a."
    # onboarding section to onboarding-flow.md (+247), and Change A's hook-prompt
    # edit regenerated hook-registry-critical.md (+318). measure_steering's
    # update_index recomputed file_metadata + budget.total_tokens to the live
    # consistent value (175274 = sum of file_metadata counts).
    #
    # Re-baselined again observation-first for the leading-question-continuity
    # spec (Tasks 6.1/6.2): conversation-protocol.md (+228) and
    # agent-behavior-rules.md (+72) grew from the Intercept-Recovery Continuity
    # additions, and hook-registry-critical.md (+15) was re-synced to mirror the
    # write-policy-gate prompt's two new pass-through entries. measure_steering's
    # update_index recomputed file_metadata + budget.total_tokens to the live
    # consistent value (175589 = sum of file_metadata counts).
    #
    # Re-baselined again observation-first for the module1-license-request-option
    # spec (Module 1 Step 6b/6d edits): module-01-business-problem.md grew from
    # the in-flow MCP License_Request_Option additions (4527 -> 5321 tokens),
    # which measure_steering recomputed into file_metadata and the budget total
    # (175589 -> 177312 = sum of file_metadata counts). Only the budget block
    # changed; keywords/languages/deployment/root_step_range are byte-identical.
    #
    # Re-baselined again observation-first for the module-router-standardization
    # spec: a new `router_ceiling: 1000` key was added to the budget block, and
    # the Module 1/7/11 root-doubles-as-phase content was relocated into new
    # dedicated phase files (module-01-phase1-discovery.md,
    # module-07-phase1-query-visualize.md, module-11-phase1-packaging.md) while
    # the content roots (3/6/8) were thinned. measure_steering recomputed
    # file_metadata and the budget total to the live consistent value
    # (177312 -> 178266 = sum of file_metadata counts). Only the budget block
    # changed; keywords/languages/deployment/root_step_range are byte-identical.
    # Re-baselined again observation-first for the steering-budget-headroom spec:
    # module-completion.md was sliced into a router plus concern slices and the
    # hook-registry-modules.md monolith was replaced by per-module slices, so new
    # file_metadata entries were added and the budget total moved
    # (178266 -> 179653 = sum of file_metadata counts). The keywords block also
    # gained completion-concern routes (recap/journal/certificate/etc. -> the new
    # completion slices). languages/deployment/root_step_range are byte-identical.
    # Re-baselined once more (179653 -> 179656) when the orphaned
    # hook-registry-modules.md references in agent-instructions.md,
    # onboarding-flow.md, and session-resume-phase2-setup-recovery.md were
    # repointed at the per-module slices; measure_steering.py recomputed the
    # affected file_metadata counts and the budget total.
    # Re-baselined once more (179656 -> 179803) for the bootcamp-consistency
    # fixes: module-05-phase2-data-mapping.md grew when its Step 13 transition
    # was made conditional (skip Module 2 / SDK setup when already complete),
    # which measure_steering.py recomputed into file_metadata and the budget
    # total. Only the budget block changed; keywords/languages/deployment/
    # root_step_range are byte-identical.
    # Re-baselined once more (179803 -> 180782) for the license-capacity-framing
    # spec: module-04-data-collection.md (3460 -> 4049) and
    # module-06-phaseA-build-loading.md (2034 -> 2424) grew when their license
    # guidance was reframed as a default evaluation license with expansion paths,
    # which measure_steering.py recomputed into file_metadata and the budget
    # total. Only the budget block changed; keywords/languages/deployment/
    # root_step_range are byte-identical.
    # Re-baselined once more (180782 -> 181773) for the turn-answer-handling
    # bugfix: module-06-phaseA-build-loading.md (2034 -> 2860) gained the
    # binding-first Volume Classification instruction, conversation-protocol.md
    # (4022 -> 4199) gained the final-message invariant, and
    # module-completion.md (1163 -> 1394) / module-completion-next-steps.md
    # (555 -> 702) gained the recap-before-transition ordering rule, all
    # recomputed by measure_steering.py into file_metadata and the budget total.
    # Only the budget block changed; keywords/languages/deployment/root_step_range
    # are byte-identical.
    # Re-baselined once more (181773 -> 185282) for the bootcamp-consistency-fixes
    # batch (qa-transcript, module-completion-artifacts, graduation-markdown,
    # onboarding-license-request-option, track-selection-drop-module2-note, etc.):
    # qa-transcript.md was added and several steering files changed size — most
    # notably module-03-phase2-visualization.md and onboarding-phase2-track-setup.md
    # — all recomputed to exact counts by measure_steering.py into file_metadata
    # and the budget total. Only the budget block changed;
    # keywords/languages/deployment/root_step_range are byte-identical.
    # Re-baselined once more (185282 -> 186004) for the
    # graduation-recap-pdf-resilience spec: graduation.md grew (4672 -> 5394)
    # when Step 0b.3 was rewritten into a resilient helper-first / inline-fallback
    # PDF-generation decision tree (graceful degradation + no-false-success
    # messaging), recomputed by measure_steering.py into file_metadata and the
    # budget total. Only the budget block changed;
    # keywords/languages/deployment/root_step_range are byte-identical.
    # Re-baselined once more (186004 -> 186556) for the
    # entity-graph-edge-key-mismatch bugfix: module-03-phase2-visualization.md
    # (4738 -> 5239) gained Critical Lesson 7 (edge-key mapping), a Step 9.3
    # edge-map note, and the Step 9.4 graph-render smoke check, and
    # module-03-visualization-api-reference.md (2050 -> 2101) gained the
    # client-side mapping cross-note, all recomputed by measure_steering.py into
    # file_metadata and the budget total. Only the budget block changed;
    # keywords/languages/deployment/root_step_range are byte-identical.
    # Re-baselined once more (186556 -> 187577) for the surface-mcp-license-request
    # spec: module-02-sdk-setup.md (4491 -> 5512) gained the Step 5c in-flow MCP
    # License_Request_Option (capability gate, three selectable licensing paths,
    # disabled-by-default enable instructions, single invocation, MCP-sourced
    # facts) mirroring the Module 1 Step 6d branch, recomputed by
    # measure_steering.py into file_metadata and the budget total. Only the budget
    # block changed; keywords/languages/deployment/root_step_range are byte-identical.
    "budget": "f3e0446d364e0d84dee199f9a162cef4e1801436a3f3f4316c56dfbe3aa8ffd4",
    "keywords": "a51b11ee3dfedc9f7da37640d24203b6ac40033e61ad11151dc27e4a67278a63",
    "languages": "ec5e570667ffcc01b044e4b41b0aec278efa05e2b280b53be1bee9e64153287c",
    "deployment": "f5547a687244fa65837874d87ef92e720a69f4b259ff785ead693b1a71781cf2",
    "root_step_range": "560fe6ad7e2b2b4e852bb6ad8515aca16846416084f9d204c83f2871764ffadd",
}

# Stable (non-phase) top-level blocks asserted byte-for-byte.
_STABLE_BLOCKS = ("budget", "keywords", "languages", "deployment")


# ---------------------------------------------------------------------------
# Helper: import (or reload) measure_steering
# ---------------------------------------------------------------------------


def _load_measure_steering():
    """Import and reload the measure_steering module for a fresh instance."""
    import measure_steering

    importlib.reload(measure_steering)
    return measure_steering


# ---------------------------------------------------------------------------
# Local, dependency-free YAML region helpers (stdlib only, no PyYAML)
# ---------------------------------------------------------------------------


def _sha256(text: str) -> str:
    """Return the hex SHA-256 digest of *text* encoded as UTF-8."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _find_top_section(content: str, name: str) -> int:
    """Return the start offset of a top-level YAML section, or -1 if absent."""
    match = re.search(rf"^{re.escape(name)}:\s*$", content, re.MULTILINE)
    return match.start() if match else -1


def _extract_top_block(content: str, name: str) -> str:
    """Return the text of a top-level YAML block, trailing newlines stripped.

    Args:
        content: Full YAML text.
        name: Top-level section name (e.g. ``budget``).

    Returns:
        The block from its header up to (excluding) the next top-level key.
    """
    start = _find_top_section(content, name)
    assert start >= 0, f"section {name!r} not found"
    after = content[start:]
    nxt = re.search(r"^\S", after[len(name) + 1:], re.MULTILINE)
    if nxt:
        return after[: len(name) + 1 + nxt.start()].rstrip("\n")
    return after.rstrip("\n")


def _root_step_range_blob(content: str) -> str:
    """Return all module ``root:`` and ``step_range:`` lines above file_metadata."""
    fm_pos = _find_top_section(content, "file_metadata")
    region = content if fm_pos < 0 else content[:fm_pos]
    lines = [
        ln
        for ln in region.splitlines()
        if re.match(r"^\s+root:\s", ln) or re.match(r"^\s+step_range:\s", ln)
    ]
    return "\n".join(lines)


def _parse_total_tokens(content: str) -> int:
    """Return the ``budget.total_tokens`` value from YAML text."""
    match = re.search(r"total_tokens:\s*(\d+)", content)
    assert match is not None, "total_tokens not found"
    return int(match.group(1))


def _sum_file_metadata(content: str) -> int:
    """Return the sum of every ``token_count`` inside the file_metadata block."""
    fm_pos = _find_top_section(content, "file_metadata")
    assert fm_pos >= 0, "file_metadata section not found"
    after = content[fm_pos:]
    nxt = re.search(r"^\S", after[len("file_metadata") + 1:], re.MULTILINE)
    block = after[: len("file_metadata") + 1 + nxt.start()] if nxt else after
    return sum(int(m) for m in re.findall(r"token_count:\s*(\d+)", block))


@dataclass
class PhaseRecord:
    """A parsed phase entry from the region above file_metadata."""

    section: str | None
    file: str
    token_count: int | None
    size_category: str | None
    line: int


def _parse_phase_records(content: str) -> list[PhaseRecord]:
    """Parse every phase entry (a ``file:`` block) above the file_metadata section.

    Phase entries are uniquely identifiable by their ``file:`` line; this covers
    ``modules.*.phases.*``, ``onboarding.*.phases.*`` and
    ``session-resume.*.phases.*`` uniformly. ``root:`` and ``file_metadata``
    entries have no ``file:`` line and are excluded.

    Args:
        content: Full YAML text.

    Returns:
        Ordered list of PhaseRecord, one per phase ``file:`` entry.
    """
    fm_pos = _find_top_section(content, "file_metadata")
    region = content if fm_pos < 0 else content[:fm_pos]
    lines = region.splitlines()

    records: list[PhaseRecord] = []
    current_top: str | None = None
    for i, line in enumerate(lines):
        top = re.match(r"^([A-Za-z][\w-]*):\s*$", line)
        if top:
            current_top = top.group(1)
            continue
        file_match = re.match(r"^(\s+)file:\s+([\w.-]+\.md)\s*$", line)
        if not file_match:
            continue
        indent = len(file_match.group(1))
        fname = file_match.group(2)
        token_count: int | None = None
        size_category: str | None = None
        for j in range(i + 1, len(lines)):
            nxt = lines[j]
            if not nxt.strip():
                continue
            if len(nxt) - len(nxt.lstrip()) < indent:
                break
            tc_match = re.match(r"^\s+token_count:\s*(\d+)\s*$", nxt)
            if tc_match:
                token_count = int(tc_match.group(1))
                continue
            sc_match = re.match(r"^\s+size_category:\s*(\w+)\s*$", nxt)
            if sc_match:
                size_category = sc_match.group(1)
        records.append(PhaseRecord(current_top, fname, token_count, size_category, i))
    return records


def _is_within_tolerance(mod, record: PhaseRecord) -> bool:
    """Return True if a phase entry's stored count is within tolerance of measured."""
    fpath = _STEERING_DIR / record.file
    if not fpath.exists() or record.token_count is None:
        return False
    measured = mod.calculate_token_count(fpath)
    return abs(record.token_count - measured) / max(measured, 1) <= _TOLERANCE


def _run_update_on_copy(mod) -> str:
    """Copy the live index to a temp dir, run update mode, return the result text."""
    td = tempfile.mkdtemp()
    try:
        tmp_index = Path(td) / "steering-index.yaml"
        tmp_index.write_text(_INDEX_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        metadata = mod.scan_steering_files(_STEERING_DIR)
        total = sum(m["token_count"] for m in metadata.values())
        mod.update_index(tmp_index, metadata, total)
        return tmp_index.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(td, ignore_errors=True)


# ---------------------------------------------------------------------------
# Strategies (st_-prefixed per python-conventions.md)
# ---------------------------------------------------------------------------


def st_filename():
    """Generate steering-style markdown filenames."""
    return st.from_regex(r"[a-z][a-z0-9\-]{0,19}\.md", fullmatch=True)


def st_filename_set():
    """Generate a set of 1-8 unique markdown filenames."""
    return st.lists(st_filename(), min_size=1, max_size=8, unique=True)


def st_token_count():
    """Generate a non-negative token count."""
    return st.integers(min_value=0, max_value=200_000)


# ---------------------------------------------------------------------------
# Test 1 — file_metadata validation is unchanged (Requirement 3.1)
# ---------------------------------------------------------------------------


class TestFileMetadataValidationUnchanged:
    """check_counts keeps the 10% tolerance and missing/removed detection.

    Mirrors TestProperty7 / TestProperty8 in test_measure_steering.py to pin the
    existing file_metadata validation behavior that the fix must not alter.

    **Validates: Requirements 3.1**
    """

    @given(
        stored=st.integers(min_value=0, max_value=100_000),
        calculated=st.integers(min_value=1, max_value=100_000),
    )
    @settings(max_examples=20)
    def test_threshold_detection_preserved(self, stored, calculated):
        mod = _load_measure_steering()

        fname = "test-file.md"
        diff_pct = abs(stored - calculated) / max(calculated, 1)
        yaml_content = (
            "file_metadata:\n"
            f"  {fname}:\n"
            f"    token_count: {stored}\n"
            "    size_category: medium\n"
            "\n"
            "budget:\n"
            f"  total_tokens: {stored}\n"
            "  reference_window: 200000\n"
            "  warn_threshold_pct: 60\n"
            "  critical_threshold_pct: 80\n"
        )

        td = tempfile.mkdtemp()
        try:
            index_path = Path(td) / "steering-index.yaml"
            index_path.write_text(yaml_content, encoding="utf-8")
            calc_metadata = {
                fname: {"token_count": calculated, "size_category": "medium"}
            }
            mismatches = mod.check_counts(index_path, calc_metadata)

            if diff_pct > _TOLERANCE:
                assert len(mismatches) > 0, (
                    f"expected mismatch for stored={stored}, calc={calculated} "
                    f"(diff={diff_pct:.2%})"
                )
            else:
                assert len(mismatches) == 0, (
                    f"unexpected mismatch for stored={stored}, calc={calculated} "
                    f"(diff={diff_pct:.2%})"
                )
        finally:
            shutil.rmtree(td, ignore_errors=True)

    @given(filenames=st_filename_set(), missing_idx=st.integers(min_value=0, max_value=9))
    @settings(max_examples=20)
    def test_missing_entry_detection_preserved(self, filenames, missing_idx):
        mod = _load_measure_steering()

        td = tempfile.mkdtemp()
        try:
            steering_dir = Path(td) / "steering"
            steering_dir.mkdir()
            for fname in filenames:
                (steering_dir / fname).write_text("content", encoding="utf-8")

            skipped_file = filenames[missing_idx % len(filenames)]

            lines = ["file_metadata:"]
            for fname in sorted(filenames):
                if fname == skipped_file:
                    continue
                count = mod.calculate_token_count(steering_dir / fname)
                lines.append(f"  {fname}:")
                lines.append(f"    token_count: {count}")
                lines.append(f"    size_category: {mod.classify_size(count)}")

            total = sum(
                mod.calculate_token_count(steering_dir / f)
                for f in filenames
                if f != skipped_file
            )
            lines.extend(
                [
                    "",
                    "budget:",
                    f"  total_tokens: {total}",
                    "  reference_window: 200000",
                    "  warn_threshold_pct: 60",
                    "  critical_threshold_pct: 80",
                ]
            )

            index_path = steering_dir / "steering-index.yaml"
            index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

            calculated = mod.scan_steering_files(steering_dir)
            mismatches = mod.check_counts(index_path, calculated)

            mismatch_files = [m[0] for m in mismatches]
            assert skipped_file in mismatch_files, (
                f"expected '{skipped_file}' reported as mismatch, got {mismatch_files}"
            )
        finally:
            shutil.rmtree(td, ignore_errors=True)


# ---------------------------------------------------------------------------
# Test 2 — non-phase blocks are byte-preserved by update mode (Reqs 3.3-3.5)
# ---------------------------------------------------------------------------


class TestNonPhaseBlocksBytePreserved:
    """budget / keywords / languages / deployment / root / step_range unchanged.

    Extends TestProperty5 (update preserves existing YAML) by asserting exact
    byte preservation via SHA-256 against the observed baseline.

    **Validates: Requirements 3.3, 3.4, 3.5**
    """

    def test_baseline_hashes_match_live_index(self):
        content = _INDEX_PATH.read_text(encoding="utf-8")
        for name in _STABLE_BLOCKS:
            assert _sha256(_extract_top_block(content, name)) == _BASELINE_HASHES[name], (
                f"baseline drift in {name!r} block of the live index"
            )
        assert _sha256(_root_step_range_blob(content)) == _BASELINE_HASHES["root_step_range"]

    def test_budget_block_content_matches_baseline_hash(self):
        """Independent content assertion paired with the budget-block hash.

        The budget hash is re-baselined observation-first from the corrected
        bytes. Prior re-baseline: token-count-sync bugfix (169633 -> 169576). This
        batch (bootcamp-consistency-fixes) re-baselined again (169576 -> 171159):
        the generated ``hook-registry-modules.md`` grew (a multi-module hook is now
        listed under each of its modules) and two steering edits
        (``phase-loading-guide.md``, ``onboarding-flow.md``) changed size, all
        reflected in ``file_metadata`` and the budget total. Most recently, the
        mcp-tool-inventory-drift bugfix re-baselines again (171208 -> 171227):
        normalizing the ``analyze_record`` signature in ``mcp-tool-decision-tree.md``
        and ``troubleshooting-commands.md`` increased their token counts, recomputed
        by ``measure_steering.py`` into ``file_metadata`` and the budget total.
        Most recently, the docs-file-placement bugfix re-baselines again
        (171227 -> 171518): Change 3 corrected the write-policy-gate hook's Check 4
        .py fallback (regenerating ``hook-registry-critical.md``, +1 token) and
        Change 4/5 realigned ``project-structure.md`` and
        ``module-05-phase2-data-mapping.md`` to the ``src/``-rooted convention with
        ``docs/`` subdirectories, all recomputed by ``measure_steering.py`` into
        ``file_metadata`` and the budget total.
        Most recently, the module-completion-artifacts bugfix re-baselines again
        (171518 -> 173650): the bugfix grew ``module-completion.md`` (added the
        shared boundary-detection trigger and backfill sections) and regenerated the
        ``hook-registry-modules.md`` file (the module-recap-append and
        module-completion-celebration hook prompts changed), all recomputed by
        ``measure_steering.py`` into ``file_metadata`` and the budget total.
        Most recently, the license-capacity-framing spec re-baselines again
        (179803 -> 180782): ``module-04-data-collection.md`` (3460 -> 4049) and
        ``module-06-phaseA-build-loading.md`` (2034 -> 2424) grew when their
        license guidance was reframed as a default evaluation license with
        expansion paths, all recomputed by ``measure_steering.py`` into
        ``file_metadata`` and the budget total.
        Pinning the hash alone could
        silently lock in a future regression, so this asserts the budget block's
        actual contents (the corrected aggregate plus every other budget
        sub-key) line by line. The two assertions together guarantee the
        re-baselined hash corresponds to the intended content and nothing else.

        **Validates: Requirements 3.3, 3.5**
        """
        content = _INDEX_PATH.read_text(encoding="utf-8")
        budget_block = _extract_top_block(content, "budget")

        # Hash side: must equal the re-baselined constant.
        assert _sha256(budget_block) == _BASELINE_HASHES["budget"]

        # Content side: the corrected aggregate and the unchanged sub-keys. The
        # aggregate equals the live sum of file_metadata token_count entries
        # (187577), so the hash cannot silently re-pin a stale value.
        assert _parse_total_tokens(budget_block) == _sum_file_metadata(content)
        assert "total_tokens: 187577" in budget_block
        assert "reference_window: 200000" in budget_block
        assert "warn_threshold_pct: 60" in budget_block
        assert "critical_threshold_pct: 80" in budget_block
        assert "split_threshold_tokens: 5000" in budget_block
        assert "router_ceiling: 1000" in budget_block

    def test_update_mode_preserves_non_phase_blocks(self):
        mod = _load_measure_steering()
        updated = _run_update_on_copy(mod)

        for name in _STABLE_BLOCKS:
            assert _sha256(_extract_top_block(updated, name)) == _BASELINE_HASHES[name], (
                f"update mode altered the {name!r} block"
            )
        assert (
            _sha256(_root_step_range_blob(updated)) == _BASELINE_HASHES["root_step_range"]
        ), "update mode altered a module root/step_range line"


# ---------------------------------------------------------------------------
# Test 3 — budget.total_tokens unchanged by phase reconciliation (Req 3.3)
# ---------------------------------------------------------------------------


class TestBudgetTotalUnchangedByPhaseReconciliation:
    """budget.total_tokens stays the sum of file_metadata counts (phases excluded).

    **Validates: Requirements 3.3**
    """

    def test_total_equals_file_metadata_sum_before_and_after(self):
        mod = _load_measure_steering()

        live = _INDEX_PATH.read_text(encoding="utf-8")
        before_total = _parse_total_tokens(live)
        before_sum = _sum_file_metadata(live)
        assert before_total == before_sum, (
            f"live total_tokens {before_total} != file_metadata sum {before_sum}"
        )

        updated = _run_update_on_copy(mod)
        after_total = _parse_total_tokens(updated)
        after_sum = _sum_file_metadata(updated)

        assert after_total == after_sum, (
            f"updated total_tokens {after_total} != file_metadata sum {after_sum}"
        )
        assert after_total == before_total, (
            f"total_tokens changed: {before_total} -> {after_total}"
        )


# ---------------------------------------------------------------------------
# Test 4 — already-in-tolerance phases are untouched (Reqs 3.2, 3.6)
# ---------------------------------------------------------------------------


class TestInTolerancePhasesUntouched:
    """In-tolerance phase entries are unchanged by update mode and not flagged.

    The in-tolerance set is derived live (observation-first) rather than
    hardcoded. On the unfixed code update mode leaves all phases untouched, so
    in-tolerance phases are trivially unchanged; the fix must keep that true.

    **Validates: Requirements 3.2, 3.6**
    """

    def test_in_tolerance_phases_unchanged_by_update_mode(self):
        mod = _load_measure_steering()

        live = _INDEX_PATH.read_text(encoding="utf-8")
        live_records = _parse_phase_records(live)
        assert live_records, "no phase entries parsed from the live index"

        # Observe-first: the in-tolerance set is non-empty and includes the
        # named-stable entries (module 11 packaging phase, all onboarding +
        # session phases) without hardcoding their exact counts. The
        # module-router-standardization spec gave Module 11 a dedicated router
        # (module-11-deployment.md) and moved the packaging phase content into
        # module-11-phase1-packaging.md, so the named packaging phase file is now
        # module-11-phase1-packaging.md.
        in_tolerance = [r for r in live_records if _is_within_tolerance(mod, r)]
        in_tolerance_files = {r.file for r in in_tolerance}
        assert "module-11-phase1-packaging.md" in in_tolerance_files

        onboarding = [r for r in live_records if r.section == "onboarding"]
        session = [r for r in live_records if r.section == "session-resume"]
        assert onboarding, "no onboarding phase entries found"
        assert session, "no session-resume phase entries found"
        assert all(_is_within_tolerance(mod, r) for r in onboarding)
        assert all(_is_within_tolerance(mod, r) for r in session)

        updated_records = _parse_phase_records(_run_update_on_copy(mod))
        assert len(updated_records) == len(live_records)

        for before, after in zip(live_records, updated_records):
            assert before.file == after.file
            if _is_within_tolerance(mod, before):
                assert after.token_count == before.token_count, (
                    f"in-tolerance phase {before.file} token_count changed "
                    f"{before.token_count} -> {after.token_count}"
                )
                assert after.size_category == before.size_category, (
                    f"in-tolerance phase {before.file} size_category changed "
                    f"{before.size_category} -> {after.size_category}"
                )

    def test_in_tolerance_phases_not_flagged_by_check(self):
        mod = _load_measure_steering()

        live = _INDEX_PATH.read_text(encoding="utf-8")
        in_tolerance_files = sorted(
            {r.file for r in _parse_phase_records(live) if _is_within_tolerance(mod, r)}
        )
        assert in_tolerance_files, "expected at least one in-tolerance phase file"

        td = tempfile.mkdtemp()
        try:
            tmp_index = Path(td) / "steering-index.yaml"
            tmp_index.write_text(live, encoding="utf-8")
            # Normalize file_metadata first so --check can only report phase
            # drift. On unfixed code phases aren't validated; after the fix the
            # update reconciles them. Either way exit 0 and no in-tolerance
            # phase file appears as a mismatch.
            metadata = mod.scan_steering_files(_STEERING_DIR)
            total = sum(m["token_count"] for m in metadata.values())
            mod.update_index(tmp_index, metadata, total)

            result = subprocess.run(
                [
                    sys.executable,
                    str(_SCRIPT_PATH),
                    "--check",
                    "--steering-dir",
                    str(_STEERING_DIR),
                    "--index-path",
                    str(tmp_index),
                ],
                capture_output=True,
                text=True,
            )
        finally:
            shutil.rmtree(td, ignore_errors=True)

        assert result.returncode == 0, (
            f"--check failed unexpectedly:\n{result.stdout}\n{result.stderr}"
        )
        mismatch_lines = [ln for ln in result.stdout.splitlines() if "stored=" in ln]
        for fname in in_tolerance_files:
            assert all(fname not in ln for ln in mismatch_lines), (
                f"in-tolerance phase {fname} was flagged by --check"
            )

# ---------------------------------------------------------------------------
# Test 5 — BUG 2 Property 4: per-file / per-phase checks are independent of the
# aggregate budget.total_tokens value (bootcamp-consistency-fixes spec, Task 5)
# ---------------------------------------------------------------------------


def _replace_total_tokens(content: str, new_total: int) -> str:
    """Return *content* with budget.total_tokens set to *new_total*.

    Only the aggregate line changes; every per-file ``token_count`` and every
    per-phase ``token_count`` is left byte-identical so the perturbation isolates
    the aggregate value.

    Args:
        content: Raw YAML text of steering-index.yaml.
        new_total: Replacement value for the ``budget.total_tokens`` line.

    Returns:
        The YAML text with exactly the ``budget.total_tokens`` value replaced.
    """
    new_content, count = re.subn(
        r"^(  total_tokens:\s*)\d+\s*$",
        rf"\g<1>{new_total}",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    assert count == 1, "expected exactly one budget.total_tokens line to replace"
    return new_content


def st_total_tokens():
    """Generate arbitrary non-negative aggregate totals (including the drifted one)."""
    return st.integers(min_value=0, max_value=1_000_000)


class TestPerFilePerPhaseChecksIndependentOfAggregate:
    """Per-file +/-10% and per-phase checks ignore budget.total_tokens.

    Bug-condition-2 preservation companion (Property 4): for an index whose
    per-file ``token_count`` values are unchanged, ``check_counts`` (per-file
    +/-10% tolerance) and ``check_phase_counts`` (per-phase tolerance) behave
    identically regardless of the declared aggregate ``budget.total_tokens``.
    This pins the existing ``--check`` semantics that the BUG 2 fix must
    preserve: correcting the aggregate (169633 -> 169576) and adding an additive
    aggregate check must NOT alter the per-file or per-phase verdicts.

    Captured on the UNFIXED tree, where ``--check`` already exits 0 and both
    mismatch lists are empty for the live index.

    **Validates: Requirements 3.5, 3.7**
    """

    def test_baseline_check_passes_on_live_index(self):
        """On the live (UNFIXED) index both checks report no mismatches."""
        mod = _load_measure_steering()
        calculated = mod.scan_steering_files(_STEERING_DIR)

        file_mismatches = mod.check_counts(_INDEX_PATH, calculated)
        phase_mismatches = mod.check_phase_counts(_INDEX_PATH, _STEERING_DIR)

        assert file_mismatches == [], (
            f"expected no per-file mismatch on the live index, got {file_mismatches}"
        )
        assert phase_mismatches == [], (
            f"expected no per-phase mismatch on the live index, got {phase_mismatches}"
        )

    @given(new_total=st_total_tokens())
    @settings(max_examples=20)
    def test_perfile_and_perphase_checks_ignore_aggregate(self, new_total):
        """Mutating only budget.total_tokens leaves both check verdicts unchanged.

        **Validates: Requirements 3.5, 3.7**
        """
        mod = _load_measure_steering()
        calculated = mod.scan_steering_files(_STEERING_DIR)

        # Baseline verdicts on the unmodified live index.
        base_file = mod.check_counts(_INDEX_PATH, calculated)
        base_phase = mod.check_phase_counts(_INDEX_PATH, _STEERING_DIR)

        live = _INDEX_PATH.read_text(encoding="utf-8")
        perturbed = _replace_total_tokens(live, new_total)

        td = tempfile.mkdtemp()
        try:
            tmp_index = Path(td) / "steering-index.yaml"
            tmp_index.write_text(perturbed, encoding="utf-8")

            # Per-file token_count and per-phase token_count lines are untouched,
            # so both checks must return exactly the baseline verdict regardless
            # of the aggregate value we injected.
            file_mismatches = mod.check_counts(tmp_index, calculated)
            phase_mismatches = mod.check_phase_counts(tmp_index, _STEERING_DIR)
        finally:
            shutil.rmtree(td, ignore_errors=True)

        assert file_mismatches == base_file, (
            f"per-file check changed with aggregate={new_total}: "
            f"{file_mismatches} != baseline {base_file}"
        )
        assert phase_mismatches == base_phase, (
            f"per-phase check changed with aggregate={new_total}: "
            f"{phase_mismatches} != baseline {base_phase}"
        )

    @given(new_total=st_total_tokens())
    @settings(max_examples=20)
    @example(new_total=177312)  # equals the live per-file sum -> --check exits 0
    @example(new_total=169633)  # a value != the live sum        -> --check exits 1
    def test_check_cli_exit_code_enforces_aggregate(self, new_total):
        """``--check`` enforces the aggregate while leaving per-file/per-phase verdicts intact.

        This is the BUG 2 Property 3 enforcement / Property 4 preservation
        boundary. Task 8.2 added an *additive* aggregate check (not a
        replacement) to ``measure_steering.py --check``: the declared
        ``budget.total_tokens`` must now equal the sum of the per-file
        ``token_count`` values.

        Post-fix contract (derived observation-first by running the script):

        - When ``budget.total_tokens`` is perturbed AWAY from the per-file sum,
          ``--check`` MUST exit non-zero AND print a ``Budget total mismatch``
          line. This is the new enforced behavior; the earlier baseline that
          ``--check`` "still exits 0 ... aggregate not checked" encoded the
          UNFIXED behavior and no longer holds.
        - When ``budget.total_tokens`` EQUALS the per-file sum (the unperturbed
          live index, or a perturbed-then-set-equal value), ``--check`` exits 0.
        - PRESERVATION (Property 4): the per-file +/-10% and per-phase verdicts are
          UNCHANGED by the aggregate value. When the aggregate is perturbed the
          ONLY new failure is the aggregate mismatch; no per-file or per-phase
          mismatch detail lines (``stored=...``) are introduced.

        **Validates: Requirements 3.5, 3.7**
        """
        live = _INDEX_PATH.read_text(encoding="utf-8")
        live_sum = _sum_file_metadata(live)
        perturbed = _replace_total_tokens(live, new_total)

        td = tempfile.mkdtemp()
        try:
            tmp_index = Path(td) / "steering-index.yaml"
            tmp_index.write_text(perturbed, encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(_SCRIPT_PATH),
                    "--check",
                    "--steering-dir",
                    str(_STEERING_DIR),
                    "--index-path",
                    str(tmp_index),
                ],
                capture_output=True,
                text=True,
            )
        finally:
            shutil.rmtree(td, ignore_errors=True)

        # Preservation invariant (holds for ANY aggregate value): perturbing only
        # budget.total_tokens introduces no per-file or per-phase mismatch. Those
        # detail lines are the only lines containing "stored="; the additive
        # "Budget total mismatch" line does not.
        detail_lines = [ln for ln in result.stdout.splitlines() if "stored=" in ln]
        assert detail_lines == [], (
            f"perturbing the aggregate to {new_total} introduced per-file/per-phase "
            f"mismatch lines (Property 4 preservation violated):\n{detail_lines}"
        )

        if new_total == live_sum:
            # Declared == sum: aggregate is satisfied, --check passes.
            assert result.returncode == 0, (
                f"--check exited {result.returncode} for aggregate={new_total} "
                f"which equals the per-file sum {live_sum}:\n"
                f"{result.stdout}\n{result.stderr}"
            )
            assert "Budget total mismatch" not in result.stdout, (
                f"unexpected budget mismatch when aggregate equals the sum:\n{result.stdout}"
            )
        else:
            # Declared != sum: the additive aggregate check must now fail.
            assert result.returncode != 0, (
                f"--check exited 0 for aggregate={new_total} != per-file sum {live_sum}; "
                f"the additive aggregate check must catch this drift:\n"
                f"{result.stdout}\n{result.stderr}"
            )
            assert "Budget total mismatch" in result.stdout, (
                f"expected a 'Budget total mismatch' line for aggregate={new_total} "
                f"(sum={live_sum}):\n{result.stdout}\n{result.stderr}"
            )
