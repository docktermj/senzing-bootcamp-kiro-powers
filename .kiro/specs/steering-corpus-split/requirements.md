# Requirements Document

## Introduction

The senzing-bootcamp power's steering corpus is approaching its context ceiling. The
authoritative measured token counts in `senzing-bootcamp/steering/steering-index.yaml`
(`file_metadata.<file>.token_count`, computed by `measure_steering.py` as
`round(len(content) / 4)`) record `budget.total_tokens` of 166,655 against a
`reference_window` of 200,000 (~83%), and several steering files exceed the power's own
documented `split_threshold_tokens` of 5,000. The most impactful are files that load
every session or early in a session, which inflate the agent's baseline context cost
before any module-specific work begins.

This feature splits and/or trims the oversized, always-loaded and early-loaded steering
files so that each individually-loadable steering unit is at or under the documented
`split_threshold_tokens` (5,000) where feasible, and the always/early-loaded footprint
is materially smaller — without losing any guidance content and without breaking the
existing phase-loading and keyword-routing machinery.

The corpus already has split machinery (the `modules.<N>.phases` and `onboarding.*` /
`session-resume.*` maps in `steering-index.yaml`, `phase-loading-guide.md`, and
`split_steering.py`) and a set of generated, mirrored files (`hook-registry.md`,
`hook-registry-critical.md`, `hook-registry-modules.md`, produced by
`sync_hook_registry.py`, verified in CI with `--verify`). This feature must operate
within those mechanisms rather than around them. The `agent-instructions.md` file is
`inclusion: always` and therefore loads on every session; reducing it has outsized
benefit, but its always-needed core cannot be moved to a manual file.

This work depends on accurate token counts. The separate `steering-index-token-count-sync`
spec reconciles drifted `phases.*.token_count` values against the authoritative
`file_metadata` measurements; this feature should be implemented after that spec is
complete, or the affected files must be re-measured before split decisions are made.

### Confirmed measured counts (authoritative `file_metadata`, at time of writing)

| File | `file_metadata` token_count | inclusion / load timing | Exceeds 5,000? |
|---|---|---|---|
| `hook-registry-modules.md` | 8476 | manual; keyword-routed (`hook`/`hooks` to `hook-registry.md`) | yes (generated) |
| `hook-registry-critical.md` | 8169 | manual; loaded during onboarding hook creation | yes (generated) |
| `module-03-system-verification.md` | 6419 | manual; module-3 phase1 root | yes |
| `onboarding-flow.md` | 5438 | manual; loaded at session start for new users | yes |
| `module-03-phase2-visualization.md` | 5312 | manual; module-3 phase2 | yes |
| `agent-instructions.md` | 5013 | **always** (every session) | yes |

These values must be re-verified against the live `steering-index.yaml` during design,
because they may shift (and the `steering-index-token-count-sync` spec is actively
correcting drift in the parallel `phases.*.token_count` values).

## Glossary

- **Steering_Corpus**: The set of `*.md` files under `senzing-bootcamp/steering/`,
  catalogued in `steering-index.yaml`.
- **Steering_Index**: The file `senzing-bootcamp/steering/steering-index.yaml`, the
  machine-readable mapping the agent uses for file selection and context-budget
  decisions. Contains `modules`, `onboarding`, `session-resume`, `keywords`,
  `languages`, `deployment`, `file_metadata`, and `budget` sections.
- **Loadable_Unit**: A single steering file that the agent loads as one unit — either
  a standalone file, a split root file, or a split phase sub-file referenced in the
  `Steering_Index`.
- **Split_Threshold**: The `budget.split_threshold_tokens` value in the `Steering_Index`
  (currently 5,000), the documented maximum token count for a single Loadable_Unit.
- **Token_Count**: The approximate token measure `round(len(content) / 4)` computed by
  `measure_steering.py` (`calculate_token_count`).
- **Always_Loaded_File**: A steering file with `inclusion: always` in its YAML
  frontmatter, loaded on every session. `agent-instructions.md` is the in-scope
  Always_Loaded_File.
- **Early_Loaded_File**: A steering file loaded at or near session start in the normal
  flow before module-specific work — specifically `onboarding-flow.md` (loaded for new
  users) and the Module 3 phase files (the first split module reached in the core
  track).
- **Generated_File**: A steering file produced by a generator script rather than edited
  by hand. The Generated_Files in scope are `hook-registry.md`,
  `hook-registry-critical.md`, and `hook-registry-modules.md`, all produced by
  `sync_hook_registry.py`.
- **Phase_Map**: A `phases` mapping under a `modules.<N>`, `onboarding`, or
  `session-resume` entry in the `Steering_Index` that maps phase slugs to a `file`,
  `token_count`, `size_category`, and `step_range`.
- **Keyword_Route**: An entry in the `keywords`, `languages`, or `deployment` map of the
  `Steering_Index` mapping a trigger term to a steering filename.
- **Routing_Reference**: Any mechanism by which a Loadable_Unit is reached — a
  Phase_Map `file`, a Keyword_Route, a `#[[file:]]` reference, or a documented load
  instruction in another steering file.
- **Guidance_Content**: The instructional substance of a steering file — behavioral
  rules, steps, checkpoints, tables, examples, and the markers `👉`, `⛔`, `STOP`/`WAIT`,
  and checkpoint directives.
- **Content_Preservation_Invariant**: The property that, after a split or trim, the
  union of the resulting Loadable_Units contains every piece of Guidance_Content present
  before the change; splitting relocates content and adds routing, and trimming removes
  only redundant duplication.
- **In_Scope_Set**: The specific set of steering files this feature commits to reducing
  in v1 (defined in Requirement 1).
- **Sync_Spec**: The `steering-index-token-count-sync` spec, which reconciles
  `phases.*.token_count` drift against `file_metadata`; a prerequisite for accurate
  split decisions.
- **CI_Pipeline**: The GitHub Actions workflow `.github/workflows/validate-power.yml`,
  which runs `validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`,
  `sync_hook_registry.py --verify`, and the pytest suite.

## Requirements

### Requirement 1: Define the v1 in-scope file set and selection criteria

**User Story:** As a power maintainer, I want a clear, prioritized set of files to split
or trim in v1, so that the work targets the files with the highest context-budget impact
and avoids destabilizing generated or always-loaded files.

#### Acceptance Criteria

1. THE Steering_Corpus_Split SHALL define the In_Scope_Set for v1 as exactly the
   Always_Loaded_File and the Early_Loaded_Files that exceed the Split_Threshold:
   `agent-instructions.md`, `onboarding-flow.md`, `module-03-system-verification.md`, and
   `module-03-phase2-visualization.md`.
2. WHERE a file in the Steering_Corpus has `inclusion: always`, THE Steering_Corpus_Split
   SHALL prioritize that file ahead of all manual-inclusion files in the In_Scope_Set.
3. THE Steering_Corpus_Split SHALL classify the Generated_Files
   (`hook-registry-modules.md`, `hook-registry-critical.md`, `hook-registry.md`) as
   out of scope for v1 splitting, on the basis that they are loaded on demand via the
   `hook`/`hooks` Keyword_Route or during onboarding hook creation and are not
   Always_Loaded or Early_Loaded.
4. IF a Generated_File is added to scope in a later iteration, THEN THE
   Steering_Corpus_Split SHALL require that the split be produced by changing
   `sync_hook_registry.py` and regenerating, and SHALL prohibit hand-editing the
   Generated_File.
5. THE Steering_Corpus_Split SHALL document, for each file in the Steering_Corpus that
   exceeds the Split_Threshold but is excluded from the In_Scope_Set, the reason for
   exclusion.
6. WHERE a candidate file's authoritative `file_metadata.token_count` in the
   Steering_Index is at or below the Split_Threshold, THE Steering_Corpus_Split SHALL
   exclude that file from the In_Scope_Set.

### Requirement 2: Per-unit token target

**User Story:** As an agent operating within a context budget, I want every steering
file I load as a unit to be at or under the documented threshold, so that I can predict
and control load cost.

#### Acceptance Criteria

1. WHEN the work for a file in the In_Scope_Set is complete, THE Steering_Corpus_Split
   SHALL ensure each resulting Loadable_Unit derived from that file has a Token_Count at
   or below the Split_Threshold.
2. WHERE a resulting Loadable_Unit cannot be reduced to at or below the Split_Threshold
   without violating the Content_Preservation_Invariant or splitting an indivisible
   section, THE Steering_Corpus_Split SHALL record that unit as an explicit exemption
   with a written justification.
3. THE Steering_Corpus_Split SHALL measure Token_Count using the `calculate_token_count`
   formula in `measure_steering.py` (`round(len(content) / 4)`), the same measure the
   CI_Pipeline uses.
4. WHEN the In_Scope_Set work is complete, THE Steering_Corpus_Split SHALL reduce the
   combined Token_Count of the Always_Loaded_File plus the Early_Loaded_Files below their
   combined Token_Count before the change.
5. THE Steering_Corpus_Split SHALL reduce the Always_Loaded_File (`agent-instructions.md`)
   Token_Count below the Split_Threshold.

### Requirement 3: No guidance content is lost

**User Story:** As a bootcamper, I want every behavioral rule and instruction to still
apply after the corpus is reorganized, so that the bootcamp behaves identically.

#### Acceptance Criteria

1. WHEN a file in the In_Scope_Set is split, THE Steering_Corpus_Split SHALL relocate
   every piece of Guidance_Content from the original file into exactly one of the
   resulting Loadable_Units, such that the union of those units contains all of the
   original Guidance_Content and no Guidance_Content is dropped.
2. WHEN a file in the In_Scope_Set is trimmed, THE Steering_Corpus_Split SHALL remove
   only content that is redundant with content retained elsewhere in the Steering_Corpus,
   and SHALL preserve all unique Guidance_Content.
3. THE Steering_Corpus_Split SHALL preserve every behavioral marker — `👉`, `⛔`,
   `STOP`/`WAIT` directives, and `**Checkpoint:**` directives — present in the original
   file across the resulting Loadable_Units.
4. THE Steering_Corpus_Split SHALL preserve the structural rules validated by
   `test_steering_structure_properties.py` for any module file it modifies: Before/After
   framing, step-checkpoint correspondence, pointing-question-followed-by-STOP, single
   question per step, prerequisites listed (root file), and YAML frontmatter with
   `inclusion: manual` (for non-always files).
5. IF splitting a numbered-step file would separate a `👉` question from its required
   `STOP`/`WAIT` instruction or a numbered step from its `**Checkpoint:**` directive,
   THEN THE Steering_Corpus_Split SHALL choose a split boundary that keeps each such pair
   within the same Loadable_Unit.

### Requirement 4: Registration in the steering index and loadability

**User Story:** As an agent selecting files to load, I want every new or relocated
steering unit registered in the steering index and reachable by the documented routing
rules, so that no relocated content becomes orphaned.

#### Acceptance Criteria

1. WHEN the Steering_Corpus_Split creates a new Loadable_Unit, THE Steering_Corpus_Split
   SHALL register that unit in the Steering_Index, either in a Phase_Map (`file`,
   `token_count`, `size_category`, `step_range`) or in `file_metadata`, following the
   format `split_steering.py` produces.
2. WHEN the Steering_Corpus_Split splits a module file that already has a Phase_Map, THE
   Steering_Corpus_Split SHALL update that module's Phase_Map so the resolved phase for
   each `step_range` points to the correct sub-file per the rules in
   `phase-loading-guide.md`.
3. WHEN the Steering_Corpus_Split relocates a section that was reached by a
   Keyword_Route, THE Steering_Corpus_Split SHALL update the affected Keyword_Route so
   the trigger term resolves to the Loadable_Unit that now contains that section.
4. WHEN the Steering_Corpus_Split relocates a section that was reached by a `#[[file:]]`
   reference or a documented load instruction in another steering file, THE
   Steering_Corpus_Split SHALL update that Routing_Reference to point to the new location.
5. THE Steering_Corpus_Split SHALL ensure every Loadable_Unit referenced in the
   Steering_Index exists on disk, satisfying the index-file-existence property in
   `test_steering_structure_properties.py`.
6. WHEN the Steering_Corpus_Split completes, THE Steering_Corpus_Split SHALL ensure
   every relocated section of Guidance_Content is reachable by at least one
   Routing_Reference.
7. WHEN `measure_steering.py` is run in update mode after the splits, THE
   Steering_Corpus_Split SHALL ensure `file_metadata` and `budget.total_tokens` reflect
   the new set of files.

### Requirement 5: Special handling of the always-loaded agent-instructions file

**User Story:** As a power maintainer, I want `agent-instructions.md` reduced without
losing any always-present rule, so that the session baseline shrinks while every
always-on behavior still applies.

#### Acceptance Criteria

1. THE Steering_Corpus_Split SHALL keep the resulting `agent-instructions.md` as an
   `inclusion: always` file containing the core rules that must be present in every
   session.
2. WHEN the Steering_Corpus_Split reduces `agent-instructions.md`, THE
   Steering_Corpus_Split SHALL relocate only sections that are needed on demand rather
   than on every turn, moving each such section into a manual-inclusion Loadable_Unit
   reachable by a Routing_Reference.
3. THE Steering_Corpus_Split SHALL NOT move content whose absence on any given turn would
   change always-on agent behavior (for example, the Answer Processing Priority rule, the
   MCP-First Invariant, Mandatory Gate Precedence, and the Question Stop Protocol) out of
   the Always_Loaded_File.
4. WHEN a section is relocated out of `agent-instructions.md`, THE Steering_Corpus_Split
   SHALL leave a brief pointer in `agent-instructions.md` that names the trigger and the
   Routing_Reference for the relocated content.
5. IF reducing `agent-instructions.md` below the Split_Threshold would require moving
   content that satisfies criterion 3 (always-on), THEN THE Steering_Corpus_Split SHALL
   retain that content in the Always_Loaded_File and record the resulting size as an
   exemption per Requirement 2.2.

### Requirement 6: Dependency on the token-count-sync spec

**User Story:** As a power maintainer, I want split decisions based on accurate token
counts, so that I do not split or skip a file based on a stale count.

#### Acceptance Criteria

1. THE Steering_Corpus_Split SHALL treat the Sync_Spec
   (`steering-index-token-count-sync`) as a prerequisite and SHALL document that this
   feature is to be implemented after the Sync_Spec is complete.
2. IF the Sync_Spec is not yet complete when split work begins, THEN THE
   Steering_Corpus_Split SHALL re-measure each In_Scope_Set file with `measure_steering.py`
   and base split decisions on the freshly measured counts rather than the stored
   `phases.*.token_count` values.
3. WHEN the Steering_Corpus_Split selects or excludes a file based on the Split_Threshold,
   THE Steering_Corpus_Split SHALL use the authoritative `file_metadata.token_count`
   measure, not a potentially stale Phase_Map `token_count`.

### Requirement 7: CI and test suite remain green

**User Story:** As a maintainer relying on CI, I want all existing validations and tests
to pass after the reorganization, so that the corpus stays internally consistent and
shippable.

#### Acceptance Criteria

1. WHEN the Steering_Corpus_Split is complete, THE CI_Pipeline SHALL pass
   `measure_steering.py --check` (with the updated `file_metadata` and `budget`),
   `validate_power.py`, `validate_commonmark.py`, and `validate_dependencies.py`.
2. WHEN the Steering_Corpus_Split leaves the Generated_Files unchanged, THE CI_Pipeline
   SHALL pass `sync_hook_registry.py --verify`.
3. WHEN the Steering_Corpus_Split is complete, THE existing steering test suites
   (`test_steering_structure_properties.py`, `test_steering_optimization_properties.py`,
   `test_steering_optimization_unit.py`, `test_split_steering.py`,
   `test_token_budget_optimization.py`) SHALL pass.
4. IF the Steering_Corpus_Split modifies a file whose structure is asserted by an
   existing test (for example onboarding or Module 3 structure tests), THEN THE
   Steering_Corpus_Split SHALL update those tests to reflect the new structure while
   preserving their original intent.
5. THE Steering_Corpus_Split SHALL NOT introduce a third-party Python dependency, keeping
   all scripts standard-library-only per `tech.md`.
6. THE Steering_Corpus_Split SHALL NOT introduce any external clickable URL into a
   steering file, and SHALL NOT introduce an MCP server URL outside
   `senzing-bootcamp/mcp.json`, per the security rules.

### Requirement 8: Threshold compliance and routability test coverage

**User Story:** As a maintainer, I want automated tests that fail if any steering unit
exceeds the threshold without exemption or if any relocated section becomes unroutable,
so that regressions are caught in CI.

#### Acceptance Criteria

1. THE Steering_Corpus_Split SHALL add a test asserting that every Loadable_Unit in the
   Steering_Index has a Token_Count at or below the Split_Threshold, or is listed in an
   explicit, enumerated exemption set.
2. WHERE a Loadable_Unit is in the exemption set, THE threshold test SHALL require that
   the exemption entry name the file and that the file exist in the Steering_Index.
3. THE Steering_Corpus_Split SHALL add a test asserting that every `file` referenced in
   any Phase_Map and every filename referenced in the `keywords`, `languages`, and
   `deployment` maps of the Steering_Index resolves to a file that exists on disk.
4. THE Steering_Corpus_Split SHALL add a test asserting that, for each module with a
   Phase_Map, every integer step in the union of the phases' `step_range` values resolves
   to exactly one phase sub-file via the `phase-loading-guide.md` rules.
5. THE Steering_Corpus_Split SHALL implement the new tests with pytest and Hypothesis
   following the workspace conventions: class-based organization, `st_`-prefixed
   strategies, `@settings(max_examples=20)`, `from __future__ import annotations`, and
   type hints on all signatures.
6. WHEN a future change relocates a section without updating its Routing_Reference, THE
   routability test SHALL fail.

### Requirement 9: Out of scope

**User Story:** As a maintainer, I want the boundaries of this feature stated explicitly,
so that unrelated changes are not bundled in.

#### Acceptance Criteria

1. THE Steering_Corpus_Split SHALL NOT change the agent's runtime context-budget
   thresholds (`warn_threshold_pct`, `critical_threshold_pct`, `split_threshold_tokens`,
   `reference_window`) in the Steering_Index.
2. THE Steering_Corpus_Split SHALL NOT rewrite or restate the semantics of any
   Guidance_Content beyond the relocation and redundancy-trimming permitted by
   Requirement 3.
3. THE Steering_Corpus_Split SHALL NOT modify the Generated_Files by hand and SHALL NOT
   change `sync_hook_registry.py` in v1; automated regeneration of the Generated_Files
   via `sync_hook_registry.py` remains permitted as the only sanctioned way those files
   change.
4. THE Steering_Corpus_Split SHALL NOT change module step numbering, `step_range`
   semantics, or the meaning of any `Keyword_Route` trigger term beyond repointing it to
   a relocated Loadable_Unit.
