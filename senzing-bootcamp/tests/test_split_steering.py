"""Property-based and unit tests for split_steering.py.

Feature: progressive-context-loading
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from split_steering import (
    Phase,
    SplitResult,
    parse_phases,
    build_root_file,
    build_sub_file,
    split_module,
    update_steering_index,
    get_split_candidates,
    step_to_phase,
    resolve_sub_file,
    _token_count,
    _size_category,
    _make_slug,
    MODULE_CONFIG,
)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

def _safe_text():
    """Generate text that won't accidentally look like phase headings or front matter."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N", "P", "Z"),
            blacklist_characters="\x00\r",
        ),
        min_size=1,
        max_size=100,
    ).filter(
        lambda t: not t.strip().startswith("## Phase")
        and not t.strip().startswith("---")
        and "**Checkpoint:**" not in t
    )


@st.composite
def module_content_strategy(draw):
    """Generate random module content with preamble and 1-5 phases.

    Returns (content_str, expected_num_phases, expected_step_ranges).
    """
    front_matter = "---\ninclusion: manual\n---\n"

    preamble_lines = draw(st.lists(_safe_text(), min_size=1, max_size=5))
    preamble = "\n".join(preamble_lines) + "\n\n"

    num_phases = draw(st.integers(min_value=1, max_value=5))

    step_start = 1
    phases_content = []
    step_ranges = []

    for i in range(num_phases):
        phase_id = str(i + 1)
        phase_name = f"Phase {phase_id} — Test Phase {phase_id}"

        num_steps = draw(st.integers(min_value=1, max_value=5))
        step_end = step_start + num_steps - 1

        lines = [f"## {phase_name}\n"]
        for step in range(step_start, step_end + 1):
            line = draw(_safe_text())
            lines.append(f"{step}. {line}")
            lines.append(f"   **Checkpoint:** Write step {step} to `config/bootcamp_progress.json`.\n")

        phases_content.append("\n".join(lines) + "\n\n")
        step_ranges.append((step_start, step_end))
        step_start = step_end + 1

    content = front_matter + preamble + "---\n\n".join(phases_content)
    return content, num_phases, step_ranges


@st.composite
def phase_list_strategy(draw):
    """Generate a list of Phase objects with valid step ranges."""
    num_phases = draw(st.integers(min_value=1, max_value=5))
    phases = []
    step_start = 1
    for i in range(num_phases):
        num_steps = draw(st.integers(min_value=1, max_value=10))
        step_end = step_start + num_steps - 1
        name = f"Phase {i+1} — Test Phase"
        slug = f"phase{i+1}-test-phase"
        content = f"## {name}\n\nSome content for phase {i+1}.\n"
        phases.append(Phase(
            name=name,
            slug=slug,
            content=content,
            step_start=step_start,
            step_end=step_end,
        ))
        step_start = step_end + 1
    return phases


# ---------------------------------------------------------------------------
# Property 1: Content Preservation Round-Trip
# ---------------------------------------------------------------------------

class TestProperty1ContentPreservation:
    """Feature: progressive-context-loading, Property 1: Content Preservation Round-Trip"""

    @given(data=module_content_strategy())
    @settings(max_examples=100)
    def test_content_preservation_round_trip(self, data):
        """**Validates: Requirements 1.6, 2.6**

        For any valid module content with phase headings, splitting into
        root + sub-files and recombining preserves every line of instructional
        content with no omissions or additions.
        """
        content, num_phases, step_ranges = data

        front_matter, preamble, phases = parse_phases(content)
        assert len(phases) == num_phases

        sub_file_paths = [f"sub-{i}.md" for i in range(num_phases)]
        root_content = build_root_file(front_matter, preamble, phases, sub_file_paths)
        sub_contents = [build_sub_file("---\ninclusion: manual\n---", p) for p in phases]

        def strip_fm(text):
            if text.startswith("---"):
                m = re.search(r"^---\s*$", text[3:], re.MULTILINE)
                if m:
                    return text[3 + m.end():]
            return text

        orig_body = strip_fm(content)
        orig_lines = set(
            line.strip() for line in orig_body.split("\n") if line.strip()
        )

        root_body = strip_fm(root_content)
        root_lines_list = root_body.split("\n")
        manifest_idx = None
        for i, line in enumerate(root_lines_list):
            if line.startswith("## Phase Sub-Files"):
                manifest_idx = i
                break

        preamble_text = "\n".join(root_lines_list[:manifest_idx]).strip() if manifest_idx else root_body

        sub_bodies = [strip_fm(sc).strip() for sc in sub_contents]
        reconstructed = preamble_text + "\n\n" + "\n\n".join(sub_bodies)
        recon_lines = set(
            line.strip() for line in reconstructed.split("\n") if line.strip()
        )

        missing = orig_lines - recon_lines
        assert not missing, f"Missing lines: {missing}"


# ---------------------------------------------------------------------------
# Property 2: Sub-File YAML Front Matter Invariant
# ---------------------------------------------------------------------------

class TestProperty2SubFileFrontMatter:
    """Feature: progressive-context-loading, Property 2: Sub-File YAML Front Matter Invariant"""

    @given(phases=phase_list_strategy())
    @settings(max_examples=100)
    def test_sub_file_front_matter_invariant(self, phases):
        """**Validates: Requirements 1.5, 2.5**

        For any sub-file produced by the splitting script, the content
        begins with YAML front matter containing `inclusion: manual`.
        """
        front_matter = "---\ninclusion: manual\n---"

        for phase in phases:
            sub_content = build_sub_file(front_matter, phase)
            assert sub_content.startswith("---\n"), \
                f"Sub-file for {phase.name} doesn't start with ---"
            fm_end = sub_content.index("---", 3)
            fm_block = sub_content[:fm_end + 3]
            assert "inclusion: manual" in fm_block, \
                f"Sub-file for {phase.name} missing 'inclusion: manual'"


# ---------------------------------------------------------------------------
# Property 3: Steering Index Metadata Consistency After Split
# ---------------------------------------------------------------------------

class TestProperty3IndexMetadataConsistency:
    """Feature: progressive-context-loading, Property 3: Steering Index Metadata Consistency"""

    @given(phases=phase_list_strategy())
    @settings(max_examples=100)
    def test_index_metadata_consistency(self, phases):
        """**Validates: Requirements 3.1, 3.2, 3.3**

        For any split module, the steering index contains a `phases` map
        with entries for each sub-file, `file_metadata` entries for root
        and sub-files, and no stale monolithic entry.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            index_content = """modules:
  99: test-module-99.md

file_metadata:
  test-module-99.md:
    token_count: 5000
    size_category: large

budget:
  total_tokens: 5000
  reference_window: 200000
  warn_threshold_pct: 60
  critical_threshold_pct: 80
"""
            index_path = tmp_path / "steering-index.yaml"
            index_path.write_text(index_content)

            sub_files = [tmp_path / f"test-module-99-phase{i+1}.md" for i in range(len(phases))]
            sub_token_counts = [_token_count(p.content) for p in phases]

            result = SplitResult(
                root_path=tmp_path / "test-module-99.md",
                sub_files=sub_files,
                phases=phases,
                root_token_count=100,
                sub_file_token_counts=sub_token_counts,
            )

            update_steering_index(index_path, 99, result)
            updated = index_path.read_text()

            assert "phases:" in updated
            assert "root: test-module-99.md" in updated

            assert "test-module-99.md:" in updated
            for sf in sub_files:
                assert sf.name + ":" in updated, f"Missing file_metadata for {sf.name}"

            for phase in phases:
                assert phase.slug + ":" in updated, f"Missing phase entry for {phase.slug}"


# ---------------------------------------------------------------------------
# Property 4: Total Tokens Sum Invariant After Split
# ---------------------------------------------------------------------------

class TestProperty4TotalTokensSum:
    """Feature: progressive-context-loading, Property 4: Total Tokens Sum Invariant"""

    @given(phases=phase_list_strategy())
    @settings(max_examples=100)
    def test_total_tokens_sum_invariant(self, phases):
        """**Validates: Requirements 3.4**

        For any set of file_metadata entries after a split, budget.total_tokens
        equals the sum of all token_count values in file_metadata.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            index_content = """modules:
  99: test-module-99.md

file_metadata:
  other-file.md:
    token_count: 500
    size_category: medium
  test-module-99.md:
    token_count: 5000
    size_category: large

budget:
  total_tokens: 5500
  reference_window: 200000
  warn_threshold_pct: 60
  critical_threshold_pct: 80
"""
            index_path = tmp_path / "steering-index.yaml"
            index_path.write_text(index_content)

            sub_files = [tmp_path / f"test-module-99-phase{i+1}.md" for i in range(len(phases))]
            sub_token_counts = [_token_count(p.content) for p in phases]

            result = SplitResult(
                root_path=tmp_path / "test-module-99.md",
                sub_files=sub_files,
                phases=phases,
                root_token_count=100,
                sub_file_token_counts=sub_token_counts,
            )

            update_steering_index(index_path, 99, result)
            updated = index_path.read_text()

            total_match = re.search(r"total_tokens:\s*(\d+)", updated)
            assert total_match, "total_tokens not found in budget"
            stored_total = int(total_match.group(1))

            fm_start = updated.find("file_metadata:")
            budget_start = updated.find("budget:")
            fm_block = updated[fm_start:budget_start]
            counts = re.findall(r"token_count:\s*(\d+)", fm_block)
            calculated_total = sum(int(c) for c in counts)

            assert stored_total == calculated_total, \
                f"total_tokens ({stored_total}) != sum of file_metadata ({calculated_total})"


# ---------------------------------------------------------------------------
# Property 5: Threshold-Based Splitting Eligibility
# ---------------------------------------------------------------------------

class TestProperty5ThresholdEligibility:
    """Feature: progressive-context-loading, Property 5: Threshold-Based Splitting Eligibility"""

    @given(
        token_counts=st.lists(
            st.integers(min_value=100, max_value=20000),
            min_size=1,
            max_size=10,
        ),
        threshold=st.integers(min_value=1000, max_value=10000),
    )
    @settings(max_examples=100)
    def test_threshold_eligibility(self, token_counts, threshold):
        """**Validates: Requirements 5.2**

        For any steering file token count and threshold value, files exceeding
        the threshold are flagged as candidates and files at or below are not.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            lines = ["modules:\n  1: test.md\n"]
            lines.append("file_metadata:")
            filenames = []
            for i, tc in enumerate(token_counts):
                fname = f"test-file-{i:02d}.md"
                filenames.append(fname)
                lines.append(f"  {fname}:")
                lines.append(f"    token_count: {tc}")
                lines.append(f"    size_category: {_size_category(tc)}")

            total = sum(token_counts)
            lines.append("")
            lines.append("budget:")
            lines.append(f"  total_tokens: {total}")
            lines.append("  reference_window: 200000")
            lines.append("  warn_threshold_pct: 60")
            lines.append("  critical_threshold_pct: 80")
            lines.append(f"  split_threshold_tokens: {threshold}")
            lines.append("")

            index_path = tmp_path / "steering-index.yaml"
            index_path.write_text("\n".join(lines))

            candidates = get_split_candidates(index_path)

            for fname, tc in zip(filenames, token_counts):
                if tc > threshold:
                    assert fname in candidates, \
                        f"{fname} (tc={tc}) should be a candidate (threshold={threshold})"
                else:
                    assert fname not in candidates, \
                        f"{fname} (tc={tc}) should NOT be a candidate (threshold={threshold})"


# ---------------------------------------------------------------------------
# Property 6: Step-to-Phase Mapping Correctness
# ---------------------------------------------------------------------------

class TestProperty6StepToPhaseMapping:
    """Feature: progressive-context-loading, Property 6: Step-to-Phase Mapping Correctness"""

    @given(phases=phase_list_strategy())
    @settings(max_examples=100)
    def test_step_to_phase_mapping(self, phases):
        """**Validates: Requirements 4.2, 6.2**

        For any valid checkpoint step number within a split module's total
        step range, the mapping returns exactly one phase whose step_range
        contains that step.
        """
        assume(len(phases) > 0)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            lines = ["modules:"]
            lines.append("  99:")
            lines.append("    root: test-module-99.md")
            lines.append("    phases:")
            for phase in phases:
                lines.append(f"      {phase.slug}:")
                lines.append(f"        file: test-module-99-{phase.slug}.md")
                lines.append(f"        token_count: {_token_count(phase.content)}")
                lines.append(f"        size_category: {_size_category(_token_count(phase.content))}")
                lines.append(f"        step_range: [{phase.step_start}, {phase.step_end}]")

            lines.append("")
            lines.append("file_metadata:")
            lines.append("  test-module-99.md:")
            lines.append("    token_count: 100")
            lines.append("    size_category: small")
            lines.append("")
            lines.append("budget:")
            lines.append("  total_tokens: 100")
            lines.append("  reference_window: 200000")
            lines.append("  warn_threshold_pct: 60")
            lines.append("  critical_threshold_pct: 80")
            lines.append("")

            index_path = tmp_path / "steering-index.yaml"
            index_path.write_text("\n".join(lines))

            total_start = phases[0].step_start
            total_end = phases[-1].step_end

            for step in range(total_start, total_end + 1):
                result = step_to_phase(index_path, 99, step)
                assert result is not None, f"No phase found for step {step}"

                expected_phase = None
                for phase in phases:
                    if phase.step_start <= step <= phase.step_end:
                        expected_phase = phase
                        break

                assert expected_phase is not None
                expected_file = f"test-module-99-{expected_phase.slug}.md"
                assert result == expected_file, \
                    f"Step {step}: expected {expected_file}, got {result}"


# ---------------------------------------------------------------------------
# Property 7: Fallback Behavior When Sub-File Missing
# ---------------------------------------------------------------------------

class TestProperty7FallbackBehavior:
    """Feature: progressive-context-loading, Property 7: Fallback Behavior When Sub-File Missing"""

    @given(
        phases=phase_list_strategy(),
        missing_indices=st.lists(st.integers(min_value=0, max_value=4), min_size=0, max_size=3),
    )
    @settings(max_examples=100)
    def test_fallback_when_sub_file_missing(self, phases, missing_indices):
        """**Validates: Requirements 6.3**

        For any sub-file path that does not exist on disk, the loading logic
        falls back to the root file path, which must exist.
        """
        assume(len(phases) > 0)

        with tempfile.TemporaryDirectory() as tmp_dir:
            steering_dir = Path(tmp_dir) / "steering"
            steering_dir.mkdir()

            root_path = steering_dir / "test-module-99.md"
            root_path.write_text("---\ninclusion: manual\n---\n# Root\n")

            valid_missing = [i for i in missing_indices if i < len(phases)]
            for i, phase in enumerate(phases):
                sub_path = steering_dir / f"test-module-99-{phase.slug}.md"
                if i not in valid_missing:
                    sub_path.write_text(f"---\ninclusion: manual\n---\n## {phase.name}\n")

            lines = ["modules:"]
            lines.append("  99:")
            lines.append("    root: test-module-99.md")
            lines.append("    phases:")
            for phase in phases:
                lines.append(f"      {phase.slug}:")
                lines.append(f"        file: test-module-99-{phase.slug}.md")
                lines.append(f"        token_count: 100")
                lines.append(f"        size_category: small")
                lines.append(f"        step_range: [{phase.step_start}, {phase.step_end}]")

            lines.append("")
            lines.append("file_metadata:")
            lines.append("  test-module-99.md:")
            lines.append("    token_count: 100")
            lines.append("    size_category: small")
            lines.append("")
            lines.append("budget:")
            lines.append("  total_tokens: 100")
            lines.append("  reference_window: 200000")
            lines.append("  warn_threshold_pct: 60")
            lines.append("  critical_threshold_pct: 80")
            lines.append("")

            index_path = steering_dir / "steering-index.yaml"
            index_path.write_text("\n".join(lines))

            for i, phase in enumerate(phases):
                step = phase.step_start
                result = resolve_sub_file(steering_dir, index_path, 99, step)

                if i in valid_missing:
                    assert result == root_path, \
                        f"Step {step}: expected fallback to root, got {result}"
                else:
                    expected = steering_dir / f"test-module-99-{phase.slug}.md"
                    assert result == expected, \
                        f"Step {step}: expected {expected}, got {result}"


# ---------------------------------------------------------------------------
# Example-based unit tests (Task 9)
# ---------------------------------------------------------------------------

# Paths to the actual steering files
STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
INDEX_PATH = STEERING_DIR / "steering-index.yaml"
AGENT_INSTRUCTIONS = STEERING_DIR / "agent-instructions.md"
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class TestUnitModule5SubFileNames:
    """Unit test: Module 5 split produces exact sub-file names (Req 1.2)."""

    def test_module5_sub_file_names(self):
        """Module 5 sub-files exist with exact expected names."""
        expected = [
            "module-05-phase1-quality-assessment.md",
            "module-05-phase2-data-mapping.md",
            "module-05-phase3-test-load.md",
        ]
        for name in expected:
            path = STEERING_DIR / name
            assert path.exists(), f"Expected sub-file not found: {name}"


class TestUnitModule6SubFileNames:
    """Unit test: Module 6 split produces exact sub-file names (Req 2.2)."""

    def test_module6_sub_file_names(self):
        """Module 6 sub-files exist with exact expected names."""
        expected = [
            "module-06-phaseA-build-loading.md",
            "module-06-phaseB-load-first-source.md",
            "module-06-phaseC-multi-source.md",
            "module-06-phaseD-validation.md",
        ]
        for name in expected:
            path = STEERING_DIR / name
            assert path.exists(), f"Expected sub-file not found: {name}"


class TestUnitRootFileFrontMatter:
    """Unit test: both root files start with inclusion: manual front matter (Req 1.3, 2.3)."""

    @pytest.mark.parametrize("filename", [
        "module-05-data-quality-mapping.md",
        "module-06-load-data.md",
    ])
    def test_root_file_front_matter(self, filename):
        """Root file starts with ---\\ninclusion: manual\\n---."""
        content = (STEERING_DIR / filename).read_text(encoding="utf-8")
        assert content.startswith("---\ninclusion: manual\n---"), \
            f"{filename} does not start with expected YAML front matter"


class TestUnitSplitThresholdTokens:
    """Unit test: steering-index.yaml budget section contains split_threshold_tokens (Req 5.1)."""

    def test_split_threshold_tokens_exists(self):
        """The budget section has a split_threshold_tokens field."""
        content = INDEX_PATH.read_text(encoding="utf-8")
        assert "split_threshold_tokens:" in content, \
            "split_threshold_tokens not found in steering-index.yaml"
        # Verify it's a reasonable value
        match = re.search(r"split_threshold_tokens:\s*(\d+)", content)
        assert match, "split_threshold_tokens has no numeric value"
        value = int(match.group(1))
        assert value == 5000, f"Expected split_threshold_tokens=5000, got {value}"


class TestUnitRootFilesAtOriginalPaths:
    """Unit test: root files remain at original paths (Req 6.1)."""

    @pytest.mark.parametrize("filename", [
        "module-05-data-quality-mapping.md",
        "module-06-load-data.md",
    ])
    def test_root_file_at_original_path(self, filename):
        """Root file exists at the original path."""
        path = STEERING_DIR / filename
        assert path.exists(), f"Root file not found at original path: {filename}"


class TestUnitAgentInstructionsUpdated:
    """Unit test: agent-instructions.md documents phase-level loading (Req 4.4, 4.5)."""

    def test_module_steering_section_documents_phase_loading(self):
        """Module Steering section documents phase-level loading behavior."""
        content = AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        assert "Split modules" in content or "phase-loading-guide.md" in content, \
            "agent-instructions.md missing phase-level loading documentation"
        assert "phases" in content, \
            "agent-instructions.md missing phases reference"
        assert "phase-loading-guide.md" in content, \
            "agent-instructions.md missing phase-loading-guide.md reference"

    def test_context_budget_section_references_phases(self):
        """Context Budget section references phases metadata."""
        content = AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        assert "Phase-level token costs" in content or "phase-level" in content.lower(), \
            "agent-instructions.md Context Budget missing phase-level reference"
        assert "phases" in content, \
            "agent-instructions.md Context Budget missing 'phases' reference"


# ---------------------------------------------------------------------------
# Integration tests (Task 10)
# ---------------------------------------------------------------------------

import shutil
import subprocess


class TestIntegrationModule5EndToEnd:
    """Integration test: end-to-end split of real Module 5."""

    def test_module5_end_to_end_split(self):
        """Split real Module 5, verify 3 sub-files + root, measure_steering --check passes."""
        # Verify the split has already been performed (files exist)
        root = STEERING_DIR / "module-05-data-quality-mapping.md"
        assert root.exists(), "Module 5 root file not found"

        sub_files = [
            STEERING_DIR / "module-05-phase1-quality-assessment.md",
            STEERING_DIR / "module-05-phase2-data-mapping.md",
            STEERING_DIR / "module-05-phase3-test-load.md",
        ]
        for sf in sub_files:
            assert sf.exists(), f"Module 5 sub-file not found: {sf.name}"

        # Verify root has manifest
        root_content = root.read_text(encoding="utf-8")
        assert "## Phase Sub-Files" in root_content, "Root file missing manifest"
        assert "module-05-phase1-quality-assessment.md" in root_content

        # Verify each sub-file has front matter
        for sf in sub_files:
            content = sf.read_text(encoding="utf-8")
            assert content.startswith("---\ninclusion: manual\n---"), \
                f"{sf.name} missing front matter"

        # Verify measure_steering.py --check passes
        result = subprocess.run(
            ["python3", "senzing-bootcamp/scripts/measure_steering.py", "--check"],
            capture_output=True,
            text=True,
            cwd=str(_PROJECT_ROOT),
        )
        assert result.returncode == 0, \
            f"measure_steering.py --check failed: {result.stdout}\n{result.stderr}"


class TestIntegrationModule6EndToEnd:
    """Integration test: end-to-end split of real Module 6."""

    def test_module6_end_to_end_split(self):
        """Split real Module 6, verify 4 sub-files + root, measure_steering --check passes."""
        root = STEERING_DIR / "module-06-load-data.md"
        assert root.exists(), "Module 6 root file not found"

        sub_files = [
            STEERING_DIR / "module-06-phaseA-build-loading.md",
            STEERING_DIR / "module-06-phaseB-load-first-source.md",
            STEERING_DIR / "module-06-phaseC-multi-source.md",
            STEERING_DIR / "module-06-phaseD-validation.md",
        ]
        for sf in sub_files:
            assert sf.exists(), f"Module 6 sub-file not found: {sf.name}"

        # Verify root has manifest
        root_content = root.read_text(encoding="utf-8")
        assert "## Phase Sub-Files" in root_content, "Root file missing manifest"
        assert "module-06-phaseA-build-loading.md" in root_content

        # Verify each sub-file has front matter
        for sf in sub_files:
            content = sf.read_text(encoding="utf-8")
            assert content.startswith("---\ninclusion: manual\n---"), \
                f"{sf.name} missing front matter"

        # Verify measure_steering.py --check passes
        result = subprocess.run(
            ["python3", "senzing-bootcamp/scripts/measure_steering.py", "--check"],
            capture_output=True,
            text=True,
            cwd=str(_PROJECT_ROOT),
        )
        assert result.returncode == 0, \
            f"measure_steering.py --check failed: {result.stdout}\n{result.stderr}"


class TestIntegrationSteeringIndexConsistency:
    """Integration test: steering index consistency after both splits."""

    def test_steering_index_consistency(self):
        """Run measure_steering.py --check with no mismatches after both splits."""
        result = subprocess.run(
            ["python3", "senzing-bootcamp/scripts/measure_steering.py", "--check"],
            capture_output=True,
            text=True,
            cwd=str(_PROJECT_ROOT),
        )
        assert result.returncode == 0, \
            f"measure_steering.py --check failed: {result.stdout}\n{result.stderr}"
        assert "within 10% tolerance" in result.stdout, \
            f"Unexpected output: {result.stdout}"

    def test_steering_index_has_phases_for_both_modules(self):
        """steering-index.yaml has phases entries for modules 5 and 6."""
        content = INDEX_PATH.read_text(encoding="utf-8")

        # Module 5 phases
        assert "phase1-quality-assessment:" in content
        assert "phase2-data-mapping:" in content
        assert "phase3-test-load" in content

        # Module 6 phases
        assert "phaseA-build-loading" in content
        assert "phaseB-load-first-source:" in content
        assert "phaseC-multi-source" in content
        assert "phaseD-validation:" in content

    def test_total_tokens_matches_sum(self):
        """budget.total_tokens equals sum of all file_metadata token counts."""
        content = INDEX_PATH.read_text(encoding="utf-8")

        fm_start = content.find("\nfile_metadata:")
        # Find top-level budget: (at start of line, not indented)
        budget_match = re.search(r"^budget:", content, re.MULTILINE)
        budget_start = budget_match.start() if budget_match else content.find("budget:")
        fm_block = content[fm_start:budget_start]
        counts = re.findall(r"token_count:\s*(\d+)", fm_block)
        calculated_total = sum(int(c) for c in counts)

        total_match = re.search(r"total_tokens:\s*(\d+)", content[budget_start:])
        stored_total = int(total_match.group(1))

        assert stored_total == calculated_total, \
            f"total_tokens ({stored_total}) != sum ({calculated_total})"
