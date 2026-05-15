"""Structural invariant tests for the entity-resolution-intro.md refresh.

Validates the six correctness properties defined in
``.kiro/specs/entity-resolution-intro-refresh/requirements.md`` against the
refreshed Target_File
(``senzing-bootcamp/steering/entity-resolution-intro.md``), its loader
reference in ``onboarding-flow.md``, and its ``steering-index.yaml``
entry:

- Property 1: the ``#[[file:]]`` loader in ``onboarding-flow.md`` resolves
  to a file whose frontmatter declares ``inclusion: manual``.
- Property 2: the steering index records ``size_category: medium`` and a
  ``token_count`` strictly less than 2000 for the Target_File.
- Property 3: the Target_File cites both the Senzing public guide and the
  MCP ``search_docs`` tool in a ``## Sources`` footer.
- Property 4: the Target_File's ``##`` headings cover the six conceptual
  areas required by Requirement 10.2.
- Property 5: re-running ``measure_steering.update_index`` against the
  current Target_File is a no-op (idempotent refresh).
- Property 6: the pre-refresh core content (frequency, exclusivity,
  stability; matched entities, cross-source relationships, deduplication)
  is preserved.

The tests are stdlib-only (``pathlib``, ``re``, ``sys``, ``tempfile``)
and example-based — there is a single fixed input file, so
Hypothesis-style property-based testing would add noise without coverage.
Pytest discovers the class via standard collection.
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts importable so peer tasks can reuse
# ``measure_steering`` (see Property 5 / Task 4.6).
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# ---------------------------------------------------------------------------
# Module-level path constants
# ---------------------------------------------------------------------------
#: Repository root — parent of the ``senzing-bootcamp/`` power directory.
REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent

#: The steering file under refresh.
TARGET_FILE: Path = REPO_ROOT / "senzing-bootcamp" / "steering" / "entity-resolution-intro.md"

#: The onboarding flow that loads ``TARGET_FILE`` via ``#[[file:]]`` at Step 4a.
ONBOARDING_FLOW: Path = REPO_ROOT / "senzing-bootcamp" / "steering" / "onboarding-flow.md"

#: The steering directory whose ``.md`` files ``measure_steering.scan_steering_files``
#: enumerates to rebuild ``file_metadata``.
STEERING_DIR: Path = REPO_ROOT / "senzing-bootcamp" / "steering"

#: The steering index that records ``token_count`` / ``size_category`` for every
#: steering file, consumed by ``measure_steering.py``.
STEERING_INDEX: Path = REPO_ROOT / "senzing-bootcamp" / "steering" / "steering-index.yaml"


def _normalize_yaml(text: str) -> str:
    """Return ``text`` with per-line trailing whitespace and trailing empty lines stripped.

    The idempotence test (Property 5) compares the YAML emitted by
    ``measure_steering.update_index`` against the original
    ``steering-index.yaml``. The design calls for a whitespace-tolerant
    comparison so that trivial differences (e.g. an editor re-saving with
    or without a trailing newline, or stripping trailing spaces on a line)
    do not mask the content-meaningful invariant that a re-emit produces
    the same file.

    Args:
        text: The raw YAML text to normalize.

    Returns:
        The text with each line right-stripped of whitespace and any
        trailing blank lines removed, followed by a single ``\\n``.
    """
    stripped_lines = [line.rstrip() for line in text.splitlines()]
    while stripped_lines and stripped_lines[-1] == "":
        stripped_lines.pop()
    return "\n".join(stripped_lines) + "\n"


class TestEntityResolutionIntroStructure:
    """Structural invariants for the refreshed entity-resolution-intro.md.

    Each test method corresponds to one of the six correctness properties
    declared in ``requirements.md``.
    """

    def test_onboarding_loader_resolves(self) -> None:
        """Validates: Requirements 1.1, 1.2, 1.5 (Property 1).

        Property 1 — Integration Invariant: Onboarding Reference Preserved.
        Asserts ``onboarding-flow.md`` contains exactly one loader line
        referencing the Target_File (matching either the ``# [[file:...]]``
        heading form or the bare ``[[file:...]]`` form), and that the
        referenced Target_File declares ``inclusion: manual`` in its YAML
        frontmatter so ``#[[file:]]`` resolution continues to succeed at
        Step 4a of the onboarding flow.
        """
        flow_text = ONBOARDING_FLOW.read_text(encoding="utf-8")
        loader_pattern = re.compile(
            r"^#?\s*\[\[file:senzing-bootcamp/steering/entity-resolution-intro\.md\]\]\s*$",
            re.MULTILINE,
        )
        matches = loader_pattern.findall(flow_text)
        assert len(matches) == 1, (
            "Expected exactly one loader reference to "
            "entity-resolution-intro.md in "
            f"{ONBOARDING_FLOW.relative_to(REPO_ROOT)}, found {len(matches)}."
        )

        target_text = TARGET_FILE.read_text(encoding="utf-8")
        frontmatter_match = re.match(r"^---\n(.*?)\n---", target_text, re.DOTALL)
        assert frontmatter_match is not None, (
            f"Target_File {TARGET_FILE.relative_to(REPO_ROOT)} is missing "
            "YAML frontmatter delimited by '---' lines."
        )
        frontmatter = frontmatter_match.group(1)
        assert re.search(r"^inclusion:\s*manual\s*$", frontmatter, re.MULTILINE), (
            "Expected 'inclusion: manual' in YAML frontmatter of "
            f"{TARGET_FILE.relative_to(REPO_ROOT)}; found frontmatter:\n"
            f"{frontmatter}"
        )

    def test_token_count_in_medium_band(self) -> None:
        """Validates: Requirements 1.6, 10.3, 11.3 (Property 2).

        Property 2 — Token Budget Invariant: Steering_Index Consistency.
        Parses ``steering-index.yaml`` with a small regex (stdlib only,
        no PyYAML per the repo convention) and asserts the
        ``file_metadata.entity-resolution-intro.md`` entry declares
        ``size_category: medium`` and a ``token_count`` strictly less
        than 2000 (the medium-band ceiling enforced by Req 10.3 and
        exercised by ``measure_steering.py --check`` per Req 11.3).
        A defensive lower bound (> 0) guards against a zero-byte
        Target_File regression.
        """
        index_text = STEERING_INDEX.read_text(encoding="utf-8")
        entry_pattern = re.compile(
            r"entity-resolution-intro\.md:\s*\n"
            r"\s+token_count:\s*(\d+)\s*\n"
            r"\s+size_category:\s*(\w+)\s*$",
            re.MULTILINE,
        )
        match = entry_pattern.search(index_text)
        assert match is not None, (
            "Expected a 'file_metadata.entity-resolution-intro.md' entry "
            "with 'token_count' then 'size_category' sub-keys in "
            f"{STEERING_INDEX.relative_to(REPO_ROOT)}; none found."
        )
        token_count = int(match.group(1))
        size_category = match.group(2)

        assert size_category == "medium", (
            "Expected size_category 'medium' for entity-resolution-intro.md "
            f"in {STEERING_INDEX.relative_to(REPO_ROOT)}; got {size_category!r}."
        )
        assert token_count > 0, (
            "Expected a positive token_count for entity-resolution-intro.md "
            f"in {STEERING_INDEX.relative_to(REPO_ROOT)}; got {token_count}."
        )
        assert token_count < 2000, (
            "Expected token_count strictly less than 2000 (medium-band "
            "ceiling per Req 10.3) for entity-resolution-intro.md in "
            f"{STEERING_INDEX.relative_to(REPO_ROOT)}; got {token_count}."
        )

    def test_sources_footer_present(self) -> None:
        """Validates: Requirements 9.2, 9.4 (Property 3).

        Property 3 — Source Attribution Invariant. Reads the Target_File
        and asserts grep-level invariants so future edits cannot
        silently strip attribution:

        - At least one occurrence of the substring ``search_docs`` (the
          MCP_Server tool name cited for MCP-indexed Senzing facts per
          Req 9.2 and the agent-instruction comment per Req 9.4).
        - A ``## Sources`` heading exists as a dedicated footer section,
          matched via ``^## Sources\\s*$`` with :data:`re.MULTILINE` so
          the heading must be on its own line.
        """
        target_text = TARGET_FILE.read_text(encoding="utf-8")

        search_docs_occurrences = target_text.count("search_docs")
        assert search_docs_occurrences >= 1, (
            "Expected at least one reference to the MCP 'search_docs' tool "
            f"in {TARGET_FILE.relative_to(REPO_ROOT)} (Req 9.2, Req 9.4); "
            f"found {search_docs_occurrences}."
        )

        sources_heading = re.search(r"^## Sources\s*$", target_text, re.MULTILINE)
        assert sources_heading is not None, (
            "Expected a '## Sources' heading on its own line in "
            f"{TARGET_FILE.relative_to(REPO_ROOT)} (Req 9.2); none found."
        )

    def test_six_conceptual_sections_present(self) -> None:
        """Validates: Requirement 10.2 (Property 4).

        Property 4 — Section Coverage Invariant. Extracts all level-2
        (``^## ``) headings from the Target_File, excluding the
        ``## Sources`` footer, and asserts each of the six conceptual
        areas required by Req 10.2 is covered by at least one heading.
        The match is a case-insensitive keyword set per area (per
        Design §Mapping (Property 4)) rather than exact heading text,
        so minor wording improvements in future edits do not break the
        test while still catching a dropped section.
        """
        target_text = TARGET_FILE.read_text(encoding="utf-8")
        headings = [
            match.group(1).strip().lower()
            for match in re.finditer(r"^## (.+)$", target_text, re.MULTILINE)
            if match.group(1).strip().lower() != "sources"
        ]
        assert headings, (
            "Expected at least one '## ' body heading (excluding '## Sources') "
            f"in {TARGET_FILE.relative_to(REPO_ROOT)}; found none."
        )

        conceptual_areas: list[tuple[str, Callable[[str], bool]]] = [
            (
                "(a) what entity resolution is",
                lambda h: "what" in h and "entity resolution" in h,
            ),
            (
                "(b) why matching records is hard",
                lambda h: "hard" in h or "matching records" in h,
            ),
            (
                "(c) how entity resolution works",
                lambda h: "how" in h and ("works" in h or "entity resolution works" in h),
            ),
            (
                "(d) Senzing's approach",
                lambda h: "senzing" in h,
            ),
            (
                "(e) relationships and ambiguous matches",
                lambda h: "relationship" in h or "ambiguous" in h,
            ),
            (
                "(f) what entity resolution produces",
                lambda h: "produces" in h or "outputs" in h,
            ),
        ]

        for area_name, predicate in conceptual_areas:
            assert any(predicate(heading) for heading in headings), (
                f"No '## ' heading in {TARGET_FILE.relative_to(REPO_ROOT)} "
                f"covers conceptual area {area_name} (Req 10.2). "
                f"Headings found: {headings}"
            )

    def test_measure_steering_rerun_is_idempotent(self) -> None:
        """Validates: Requirement 1.6, Req 11.3 (idempotence proxy; Property 5).

        Property 5 — Idempotent Refresh. Imports ``measure_steering`` via
        the ``sys.path`` shim, rescans the steering directory to compute
        the current ``file_metadata`` and ``budget.total_tokens``, and
        invokes ``measure_steering.update_index(...)`` against a
        ``tempfile``-backed copy of the real ``steering-index.yaml``.
        Asserts the re-emitted YAML equals the original after
        whitespace-tolerant normalization (per-line trailing whitespace
        and trailing blank lines stripped), proving that a second run of
        the token-measurement tail of the refresh pipeline is a no-op —
        the ``f(f(x)) = f(x)`` property the design relies on.
        """
        import measure_steering  # noqa: PLC0415 — imported lazily after sys.path shim

        original_text = STEERING_INDEX.read_text(encoding="utf-8")

        file_metadata = measure_steering.scan_steering_files(STEERING_DIR)
        total_tokens = sum(meta["token_count"] for meta in file_metadata.values())

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_index = Path(tmp_dir) / "steering-index.yaml"
            tmp_index.write_text(original_text, encoding="utf-8")
            measure_steering.update_index(tmp_index, file_metadata, total_tokens)
            re_emitted_text = tmp_index.read_text(encoding="utf-8")

        assert _normalize_yaml(re_emitted_text) == _normalize_yaml(original_text), (
            "Expected measure_steering.update_index to be idempotent against the "
            f"current {STEERING_INDEX.relative_to(REPO_ROOT)} (Property 5); "
            "re-emitted YAML differs from the original after whitespace "
            "normalization. Run `python senzing-bootcamp/scripts/measure_steering.py` "
            "to resync the index."
        )

    def test_no_regression_of_core_content(self) -> None:
        """Validates: Req 7.1, Req 5.2 (Property 6).

        Property 6 — No Regression of Existing Core Content. Reads the
        Target_File once, lowercases it for a case-insensitive substring
        match, and issues six independent ``assert`` statements — one
        per pre-refresh anchor term — so a future edit that drops any
        single item fails with a diagnostic message naming the missing
        term and the property / requirement it protects.

        The six anchors map to the refreshed body as:

        - ``frequency`` / ``exclusivity`` / ``stability`` — the three
          attribute behaviors in ``## How Senzing handles it`` (Req 5.2).
        - ``matched entities`` / ``cross-source`` + ``relationship`` /
          ``deduplication`` — the three outputs in ``## What entity
          resolution produces`` (Req 7.1). ``cross-source`` is paired
          with ``relationship`` so the phrase "cross-source relationships"
          is preserved intact rather than either token alone.
        """
        target_text = TARGET_FILE.read_text(encoding="utf-8")
        lowered_text = target_text.lower()
        target_rel = TARGET_FILE.relative_to(REPO_ROOT)

        assert "frequency" in lowered_text, (
            f"Expected 'frequency' (case-insensitive) in {target_rel} "
            "(Property 6, Req 5.2 — attribute behavior). This anchor "
            "protects the 'Frequency' bullet in '## How Senzing handles it'."
        )
        assert "exclusivity" in lowered_text, (
            f"Expected 'exclusivity' (case-insensitive) in {target_rel} "
            "(Property 6, Req 5.2 — attribute behavior). This anchor "
            "protects the 'Exclusivity' bullet in '## How Senzing handles it'."
        )
        assert "stability" in lowered_text, (
            f"Expected 'stability' (case-insensitive) in {target_rel} "
            "(Property 6, Req 5.2 — attribute behavior). This anchor "
            "protects the 'Stability' bullet in '## How Senzing handles it'."
        )
        assert "matched entities" in lowered_text, (
            f"Expected 'matched entities' (case-insensitive) in {target_rel} "
            "(Property 6, Req 7.1 — ER output). This anchor protects the "
            "'Matched entities' bullet in '## What entity resolution produces'."
        )
        assert "cross-source" in lowered_text and "relationship" in lowered_text, (
            f"Expected both 'cross-source' and 'relationship' "
            f"(case-insensitive) in {target_rel} (Property 6, Req 7.1 — ER "
            "output). These anchors protect the 'Cross-source relationships' "
            "bullet in '## What entity resolution produces'."
        )
        assert "deduplication" in lowered_text, (
            f"Expected 'deduplication' (case-insensitive) in {target_rel} "
            "(Property 6, Req 7.1 — ER output). This anchor protects the "
            "'Deduplication' bullet in '## What entity resolution produces'."
        )
