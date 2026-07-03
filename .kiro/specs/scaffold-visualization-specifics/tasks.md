# Implementation Plan: Scaffold Visualization Specifics

## Overview

Relocate Module 3's client-side visualization specifics out of always-loaded steering prose and into
the one local artifact that already emits working code — `scripts/generate_standalone_demo.py` — so
those specifics are correct by construction, then shrink `steering/module-03-phase2-visualization.md`
to a Steering_Pointer that retains every constraint not guaranteed by the generated output. A
test-owned `RELOCATION_MANIFEST` declares, for each Visualization_Specific, whether it is guaranteed
by the generated output, retained in steering, or both, and the test suite enforces that split so
nothing is dropped from both places.

Work proceeds source-first: add stable provenance comments to the already-baked embedded blocks in
`generate_standalone_demo.py` (additive, no output change) so detectors anchor on stable text; define
the `RELOCATION_MANIFEST` + `Specific` dataclass and its guard test; reduce the steering file to a
Steering_Pointer while retaining the ⛔ mandatory gate, Rule 15, the render smoke check, and the
dashboard/`/api/*`/SDK specifics; update `steering-index.yaml` token counts and verify with
`measure_steering.py --check`; then write the property tests (Properties 1–4) and the example/smoke
tests. All code targets Python 3.11+ stdlib only and follows the project script/test conventions
(pytest + Hypothesis, class-based, `sys.path` import of `scripts/`). Visualization runtime behavior,
the Step 9 gate, and Rule 15 do not change.

## Tasks

- [x] 1. Anchor the embedding site with provenance comments
  - [x] 1.1 Add provenance comments to the embedded blocks in `generate_standalone_demo.py`
    - Edit `senzing-bootcamp/scripts/generate_standalone_demo.py` to add one-line provenance
      comments (e.g. `# Specific: edge-key-mapping`, `# Specific: explicit-svg-dimensions`) above
      each embedded block in `_INDEX_HTML` and `_SERVER_PY` that satisfies a Visualization_Specific:
      the D3 v7 CDN `<script src>`, the `drawGraph` edge map (`source_entity_id`/`target_entity_id`
      → `source`/`target`) before `forceLink`, the `function(){}` callbacks, the SVG
      `width`/`height` attributes, the `COLORS` source-color map, the `nodeRadius` formula, and the
      stdlib `http.server` import / localhost bind
    - Changes MUST be additive comments only — the generated `index.html`, `server.py`, and
      `write_html.py` output bytes MUST NOT change, and no runtime behavior changes
    - _Requirements: 1.1, 1.2_

- [x] 2. Define the relocation manifest and its guard
  - [x] 2.1 Create the test module skeleton with `Specific` dataclass and `RELOCATION_MANIFEST`
    - Create `senzing-bootcamp/tests/test_scaffold_visualization_specifics.py` with
      `from __future__ import annotations`, a module docstring, stdlib-only imports, the `sys.path`
      insertion to import `generate_standalone_demo` from `scripts/`, and the pytest + Hypothesis
      profile registration convention used by the existing test suite (no hand-set `max_examples`)
    - Define the frozen `Specific` dataclass (`id`, `description`, `coverage`, `output_marker`,
      `steering_anchor`) exactly as specified in the design's Data Models section
    - Define the module-level `RELOCATION_MANIFEST` constant listing every specific from the design's
      Relocation_Manifest table with its `coverage` (`output` | `steering` | `both`) and detector
      markers/anchors
    - _Requirements: 4.1, 4.2_

  - [x] 2.2 Write the manifest guard test
    - Assert `RELOCATION_MANIFEST` lists every specific named in the design's Data Models table (so
      the manifest itself cannot silently shrink), and that every entry's `coverage` is one of
      `output`/`steering`/`both` with the detector fields required by that coverage present
    - _Requirements: 4.1_

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Reduce the steering file to a Steering_Pointer
  - [x] 4.1 Rewrite `module-03-phase2-visualization.md` as a Steering_Pointer
    - Edit `senzing-bootcamp/steering/module-03-phase2-visualization.md`: replace the duplicated
      seven "CRITICAL LESSONS" list and the "D3.js Code Style Constraints" block with a short
      Steering_Pointer section stating the client-rendering intent and pointing to the artifact
      emitted by `scripts/generate_standalone_demo.py` (its `drawGraph` as the correct-by-construction
      reference for the edge-key mapping)
    - Retain verbatim the ⛔ MANDATORY GATE block, the Governing Rule 15 scope note, the render smoke
      check (generated-code check + rendered/data check) with its Fix_Instruction, the Step 9
      four-tab dashboard spec, the four `/api/*` endpoint summaries, SDK relationship discovery
      (`find_network_by_entity_id` / relationship-inclusion flag), and the `#[[file:...]]` reference
      to `module-03-visualization-api-reference.md`
    - Remove the external D3 CDN URL from steering prose (it now lives only in the generated artifact
      code) to clear the MEDIUM external-URL security finding
    - _Requirements: 2.1, 2.3, 3.1_

  - [x] 4.2 Write the Steering_Pointer and gate-retention example tests
    - Assert the reduced steering references `generate_standalone_demo.py` as the client-rendering
      reference and no longer contains the duplicated seven-lesson / D3-code-style block, and that it
      no longer references the external D3 CDN URL (Req 2.1)
    - Assert the ⛔ MANDATORY GATE block and the Rule 15 scope note remain (Req 3.1)
    - Assert the render smoke check (generated-code check) and its Fix_Instruction remain (Req 2.3)
    - _Requirements: 2.1, 2.3, 3.1_

- [x] 5. Update the steering token counts
  - [x] 5.1 Recompute `steering-index.yaml` token counts and verify
    - Update `senzing-bootcamp/steering/steering-index.yaml`: recompute
      `file_metadata['module-03-phase2-visualization.md'].token_count` and
      `modules.3.phases.phase2-visualization.token_count` via `scripts/measure_steering.py`, and
      decrement `budget.total_tokens` by the same delta; keep the file in `split_allowlist`
    - Run `python senzing-bootcamp/scripts/measure_steering.py --check` and confirm it passes
    - _Requirements: 2.2_

  - [x] 5.2 Write the token-count consistency test
    - Smoke test asserting the recorded `token_count` for `module-03-phase2-visualization.md` in
      `steering-index.yaml` matches the value measured by `measure_steering.py` for the reduced file
    - _Requirements: 2.2_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Property tests for the relocation invariants
  - [x] 7.1 Write property test for no-constraint-silently-dropped
    - **Property 1: No relocated constraint is silently dropped** — strategy
      `st_manifest_specific()` draws a `Specific` from `RELOCATION_MANIFEST`; generate the artifacts
      once (module-scoped fixture) and assert the drawn specific is covered per its `coverage`
      (`output` marker in the generated artifacts, `steering` anchor in the reduced steering / its
      api-reference companion, `both` satisfies both sides, none covered by neither). Also run as a
      parametrized sweep over the full manifest so every entry is checked at least once
    - **Validates: Requirements 1.3, 2.3, 4.1**

  - [x] 7.2 Write property test for edge-key mapping correct by construction
    - **Property 2: Edge-key mapping is correct by construction (blank graph impossible)** — strategy
      `st_generation_params()` draws `output_dir` names and `port` values; generate into `tmp_path`,
      assert the `source`/`target` mapping precedes `forceLink` in the emitted `index.html`, parse the
      embedded `DATA`, and assert every edge endpoint resolves to an embedded node `entity_id`
    - **Validates: Requirements 1.2, 3.2, 4.1**

  - [x] 7.3 Write property test for required structural elements always emitted
    - **Property 3: Required client-rendering structural elements are always emitted** — reuse
      `st_generation_params()`; assert each `output`-covered marker is present (stdlib `http.server`
      import with localhost bind and no third-party HTTP framework, exactly one D3 v7 CDN `<script>`,
      single self-contained `index.html`, explicit SVG `width`/`height`, TruthSet source-color map,
      node-radius formula) and that no arrow function is used as a D3 callback
    - **Validates: Requirements 1.1, 3.2, 4.1**

  - [x] 7.4 Write property test for deterministic regeneration
    - **Property 4: Regeneration is deterministic** — reuse `st_generation_params()`; generate,
      capture bytes, re-run the emitted `write_html.py` N times (N drawn small), and assert
      byte-identical `index.html`, `server.py`, and `write_html.py` on every run
    - **Validates: Requirements 1.1**

- [x] 8. First-visualization consistency example test
  - [x] 8.1 Write the first-visualization guarantee consistency test
    - Example test asserting `generate_demo` clears the owed marker
      (`satisfied_by="standalone_demo"`) on success and leaves it on a simulated write failure,
      reusing the existing first-visualization progress helpers
    - _Requirements: 3.3_

- [x] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Property tests use Hypothesis with the project's registered profiles (`fast`=5 local,
  `thorough`=100 CI); do not hand-set `@settings(max_examples=...)` to restate the baseline.
- Tests live in `senzing-bootcamp/tests/test_scaffold_visualization_specifics.py`, are class-based,
  and import scripts via the `sys.path` convention. `RELOCATION_MANIFEST` is a module-level,
  test-owned constant.
- Each property task references its property number and the requirement clause it validates for
  traceability.
- The provenance-comment edit (Task 1.1) and the steering reduction (Task 4.1) must not change any
  generated output bytes or weaken the Step 9 gate / Rule 15; the D3 CDN URL is removed from steering
  prose and lives only in the generated artifact code.
- Fixtures are synthetic and PII-free; the generator's embedded TruthSet-shaped sample carries no PII
  (power-distribution safety rule). No new CI wiring is required — `measure_steering.py --check` and
  `validate_commonmark.py` in `validate-power.yml` cover the steering-index and Markdown consistency.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1"] },
    { "id": 1, "tasks": ["2.2", "4.1"] },
    { "id": 2, "tasks": ["4.2", "5.1"] },
    { "id": 3, "tasks": ["5.2", "7.1", "7.2", "7.3", "7.4", "8.1"] }
  ]
}
```
