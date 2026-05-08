# Implementation Plan: Entity Resolution Intro Refresh

## Overview

This plan refreshes `senzing-bootcamp/steering/entity-resolution-intro.md`
(the Target_File), re-emits the `file_metadata` and `budget.total_tokens`
entries in `senzing-bootcamp/steering/steering-index.yaml`, and adds a new
structural pytest module asserting the six correctness properties from
`requirements.md`. The work is a content transformation plus one small
Python (stdlib-only) test module — no SDK code generation, no new hooks,
no new steering files. Tasks are ordered so that source gathering happens
first, each body section is authored in a buildable increment, the token
index is resynced, the structural test module is added, and the final
checkpoint runs every validator plus the new tests.

Task references use the short form:

- `Req N.M` — acceptance criterion M of Requirement N in `requirements.md`.
- `Property N` — correctness property N in `requirements.md`.
- `Design §Section` — a section heading in `design.md`.

## Tasks

- [x] 1. Gather authoritative source material for the refresh
  - Capture the MCP `search_docs` results and Senzing public-guide excerpts
    that will back every Senzing-specific claim in the refreshed body, so
    the authoring step in Task 2 never falls back to training-data content.
  - _Requirements: Req 9.1, Req 9.3; Design §Source-Grounding Plan_

  - [x] 1.1 Run the planned MCP `search_docs` query set
    - Call `search_docs` on `mcp.senzing.com` for each of the five queries
      in Design §Source-Grounding Plan: "Senzing principle-based entity
      resolution approach", "entity resolution relationships disclosed
      discovered", "entity resolution ambiguous match possible match",
      "Senzing differentiators real-time explainability attribution",
      "entity resolution pipeline standardization blocking scoring
      clustering".
    - Record the retrieved excerpts and which section of the Target_File
      each excerpt will back (principles, differentiators, relationships,
      ambiguous match, pipeline).
    - If MCP is unreachable, record that explicitly and route affected
      claims through Task 1.2 only, per Design §Error Handling (MCP
      Server Unavailable at Authoring Time).
    - _Requirements: Req 9.1, Req 9.3, Req 9.5; Design §Source-Grounding Plan_

  - [x] 1.2 Cross-check against the Senzing public guide
    - Read <https://senzing.com/what-is-entity-resolution/> and reconcile
      general-ER and differentiator claims with the MCP excerpts from
      Task 1.1.
    - Where MCP and the public guide disagree, prefer MCP content and note
      the divergence for the PR description.
    - Flag any hardcoded numerics or rebranded product names in the public
      guide so they can be omitted per Req 8.5.
    - _Requirements: Req 9.1, Req 8.5; Design §Source-Grounding Plan_

- [x] 2. Author the refreshed Target_File body
  - Rewrite `senzing-bootcamp/steering/entity-resolution-intro.md` in place
    so the six body sections plus the Sources footer match Design
    §Section-by-Section Outline, while preserving every integration point
    in Design §Preserved Integration Points (Non-Negotiable).
  - Each sub-task below lands one section (or the footer / header scaffold)
    as a self-contained, buildable increment. Keep each section 60–150
    words so the total file stays under the medium threshold (Req 10.3).
  - _Requirements: Req 1.1–1.4, Req 10.1, Req 10.2, Req 10.4, Req 10.5, Req 11.4, Req 11.5_

  - [x] 2.1 Preserve the frontmatter, title, Step 4a loader note, and
    update the agent-instruction HTML comment query list
    - Keep the YAML frontmatter with exactly `inclusion: manual`, the
      `# What Is Entity Resolution?` top-level heading, and the
      "Loaded via `#[[file:]]` from `onboarding-flow.md` during Step 4a."
      line.
    - Replace the existing two-query agent-instruction HTML comment with
      the updated five-query list from Design §Refreshed Target_File
      Structure and §Source-Grounding Plan (principle-based approach;
      relationships disclosed / discovered; ambiguous match / possible
      match; differentiators real-time / explainability / attribution;
      ER pipeline standardization / blocking / scoring / clustering).
    - Keep the `mcp-offline-fallback.md` reference in the comment.
    - _Requirements: Req 1.2, Req 1.3, Req 1.4, Req 9.4, Req 9.5_

  - [x] 2.2 Write `## What entity resolution is`
    - Define ER as determining when records refer to the same real-world
      entity, when they refer to different entities, and when they are
      related.
    - State ER covers multiple entity types (people and organizations) and
      frame it as underlying accurate counting ("is this one person or
      three?").
    - Distinguish ER from fuzzy matching by emphasizing ER must tell
      similar records apart, not only find matches.
    - _Requirements: Req 2.1, Req 2.2, Req 2.3, Req 2.4; Design §Section-by-Section Outline_

  - [x] 2.3 Write `## Why matching records is hard`
    - Bullet list of at least four concrete challenges: name variations,
      address changes over time, format inconsistencies (phone / date
      formats), and data entry errors.
    - Close with the two failure modes: false-negative (one person treated
      as two, lost 360-degree view) and false-positive using the
      father/son same-name-and-address example.
    - State that simplistic or purely fuzzy matching cannot reliably
      distinguish these cases.
    - _Requirements: Req 3.1, Req 3.2, Req 3.3, Req 3.4; Design §Section-by-Section Outline_

  - [x] 2.4 Write `## How entity resolution works`
    - Describe the vendor-neutral pipeline: ingestion / standardization,
      candidate selection (blocking / indexing), comparison and scoring,
      classification (match / no match / possible match), entity
      clustering.
    - Keep it strictly conceptual — no Senzing SDK calls, no code, no
      implementation specifics (those belong in later bootcamp modules).
    - Note that the most capable engines compare each inbound record
      against everything already known about an entity, not only pairwise.
    - _Requirements: Req 4.1, Req 4.2, Req 4.3; Design §Section-by-Section Outline_

  - [x] 2.5 Write `## How Senzing handles it` (principles + differentiators)
    - State Senzing uses principle-based matching — not hand-coded rules
      or trained ML.
    - Cover the three attribute behaviors with one concrete example each:
      frequency (common vs rare name), exclusivity (SSN vs phone), and
      stability (DOB vs address).
    - State Senzing is preconfigured for people and organizations so the
      Bootcamper can load and resolve without writing rules or training
      a model.
    - Add the differentiators at a conceptual level: real-time /
      continuous, no training / fine-tuning / ER experts needed, full
      attribution and explainability ("why matched" / "why not matched"),
      scales from laptop to billions of records.
    - Omit hardcoded numerics and specific customer or deployment sizes;
      point to docs.senzing.com / MCP for current figures.
    - _Requirements: Req 5.1, Req 5.2, Req 5.3, Req 5.4, Req 8.1, Req 8.2, Req 8.3, Req 8.4, Req 8.5; Design §Section-by-Section Outline_

  - [x] 2.6 Write `## Relationships and ambiguous matches`
    - Introduce relationship awareness — capable ER engines track
      connections between resolved entities, not only whether records
      match.
    - Distinguish disclosed relationships ("Person A is CEO of Company B",
      explicitly stated) from discovered relationships (shared address
      or phone number).
    - Define "ambiguous match" inline on first use per Req 11.5, and
      explain that arbitrarily resolving such a record creates an
      invisible false positive.
    - State that a well-designed engine flags the case as "possible match"
      rather than forcing an arbitrary merge.
    - _Requirements: Req 6.1, Req 6.2, Req 6.3, Req 6.4, Req 11.5; Design §Section-by-Section Outline_

  - [x] 2.7 Write `## What entity resolution produces`
    - Bullet list of the three outputs framed in business-value terms:
      matched entities (360-degree / golden record), cross-source
      relationships (vendor-in-procurement = supplier-in-ERP), and
      deduplication (duplicate records consolidated).
    - Name at least two representative use case areas (fraud detection,
      compliance / KYC, customer 360, investigations).
    - Close with one sentence connecting the three outputs to the rest
      of the bootcamp — producing, querying, and operationalizing them
      is what later modules teach.
    - _Requirements: Req 7.1, Req 7.2, Req 7.3, Req 7.4; Design §Section-by-Section Outline_

  - [x] 2.8 Write the `## Sources` footer
    - Append a `## Sources` section listing the Senzing public guide URL
      (`https://senzing.com/what-is-entity-resolution/`) and a reference
      to the Senzing MCP `search_docs` tool on `mcp.senzing.com`.
    - Ensure both citation strings appear verbatim (they are the grep
      targets for Property 3).
    - _Requirements: Req 9.2, Req 9.4; Design §Section-by-Section Outline, §Refreshed Target_File Structure_

  - [x] 2.9 Enforce terminology and pacing consistency
    - Scan the refreshed body for terminology alignment with neighboring
      steering files: `DATA_SOURCE` (all caps), *Senzing Entity
      Specification* (title case), *entity resolution* (lowercase),
      *principle-based matching* (lowercase, hyphenated).
    - Confirm no duplication of the Step 4 module overview, licensing,
      or mock-data callouts already in `onboarding-flow.md`.
    - Confirm no new 👉 / 🛑 gates, checkpoint prompts, or blocking
      questions were introduced.
    - _Requirements: Req 10.1, Req 10.4, Req 10.5, Req 11.4_

- [x] 3. Resync the steering index
  - Run the token-measurement script so `file_metadata` and
    `budget.total_tokens` in `steering-index.yaml` reflect the refreshed
    Target_File, then verify with `--check`.
  - _Requirements: Req 1.6, Req 10.3, Req 11.3; Design §Steering Index Update Plan_

  - [x] 3.1 Rerun `measure_steering.py` to rewrite `steering-index.yaml`
    - Run `python senzing-bootcamp/scripts/measure_steering.py` from the
      repo root.
    - Confirm the rewritten `file_metadata.entity-resolution-intro.md`
      has `size_category: medium` and `token_count` strictly less than
      2000 (medium-band ceiling per Req 10.3).
    - Confirm `budget.total_tokens` has been recalculated and that
      sections above `file_metadata:` (module table, keywords,
      languages, deployment) are unchanged.
    - _Requirements: Req 1.6, Req 10.3; Design §Steering Index Update Plan, §Data Models_

  - [x] 3.2 Verify drift with `measure_steering.py --check`
    - Run `python senzing-bootcamp/scripts/measure_steering.py --check`.
    - Confirm the script reports no drift for
      `entity-resolution-intro.md` (within the 10% tolerance).
    - _Requirements: Req 11.3; Property 2; Design §Validation Layers_

- [x] 4. Add the structural pytest module
  - Create `senzing-bootcamp/tests/test_entity_resolution_intro_structure.py`
    as a stdlib-only pytest module (no Hypothesis) with one class
    `TestEntityResolutionIntroStructure` and one test method per
    correctness property from `requirements.md`. Use the `sys.path` shim
    pattern from Design §Test Location and Repo Convention so
    `measure_steering` can be imported for Property 5.
  - _Requirements: Req 1.5, Req 1.6, Req 9.2, Req 9.4, Req 10.2, Req 10.3, Req 11.3; Design §New Test Module, §Mapping: Correctness Properties → Validators / Tests_

  - [x] 4.1 Scaffold the test module
    - Create the file with imports limited to `pathlib`, `re`, `sys`
      from the standard library.
    - Add the `sys.path` shim that inserts
      `senzing-bootcamp/scripts` so `measure_steering` can be imported
      by Task 4.6.
    - Declare `class TestEntityResolutionIntroStructure:` and module-level
      constants for the Target_File path and the `onboarding-flow.md`
      path.
    - _Requirements: Design §Test Location and Repo Convention, §New Test Module_

  - [x] 4.2 Implement `test_onboarding_loader_resolves` (Property 1)
    - **Property 1: Integration Invariant — Onboarding Reference Preserved**
    - **Validates: Req 1.1, Req 1.2, Req 1.5**
    - Read `senzing-bootcamp/steering/onboarding-flow.md`, assert the
      loader line
      `# [[file:senzing-bootcamp/steering/entity-resolution-intro.md]]`
      is present exactly once (matching the current form, with or
      without the leading `#`).
    - Open the referenced Target_File and assert its YAML frontmatter
      contains `inclusion: manual`.
    - _Requirements: Req 1.1, Req 1.2, Req 1.5; Property 1; Design §Mapping (Property 1)_

  - [x] 4.3 Implement `test_token_count_in_medium_band` (Property 2)
    - **Property 2: Token Budget Invariant — Steering_Index Consistency**
    - **Validates: Req 1.6, Req 10.3, Req 11.3**
    - Parse `senzing-bootcamp/steering/steering-index.yaml` with a small
      regex (stdlib only, no PyYAML) and assert
      `file_metadata.entity-resolution-intro.md.size_category` is
      exactly `medium` and `token_count` is strictly less than 2000.
    - _Requirements: Req 1.6, Req 10.3, Req 11.3; Property 2; Design §Mapping (Property 2)_

  - [x] 4.4 Implement `test_sources_footer_present` (Property 3)
    - **Property 3: Source Attribution Invariant**
    - **Validates: Req 9.2, Req 9.4**
    - Read the Target_File and assert: at least one occurrence of
      `senzing.com/what-is-entity-resolution`, at least one occurrence
      of `search_docs`, and a `## Sources` heading exists.
    - _Requirements: Req 9.2, Req 9.4; Property 3; Design §Mapping (Property 3)_

  - [x] 4.5 Implement `test_six_conceptual_sections_present` (Property 4)
    - **Property 4: Section Coverage Invariant**
    - **Validates: Req 10.2**
    - Extract all `^##` headings from the Target_File (excluding
      `## Sources`) and assert each of the six conceptual areas is
      covered by at least one heading, using the keyword match sets
      defined in Design §Mapping (Property 4): (a) "what" + "entity
      resolution", (b) "hard" or "matching records", (c) "how" plus
      "works" or "entity resolution works", (d) "Senzing", (e)
      "relationship" or "ambiguous", (f) "produces" or "outputs".
    - _Requirements: Req 10.2; Property 4; Design §Mapping (Property 4)_

  - [x] 4.6 Implement `test_measure_steering_rerun_is_idempotent` (Property 5)
    - **Property 5: Idempotent Refresh**
    - **Validates: Req 1.6, Req 11.3 (idempotence proxy)**
    - Import `measure_steering` via the `sys.path` shim from Task 4.1.
    - Read the current `steering-index.yaml`, invoke
      `measure_steering.update_index(...)` programmatically against the
      current Target_File contents, and assert the re-emitted YAML is
      byte-identical (whitespace-tolerant) to the original.
    - _Requirements: Req 1.6; Property 5; Design §Mapping (Property 5)_

  - [x] 4.7 Implement `test_no_regression_of_core_content` (Property 6)
    - **Property 6: No Regression of Existing Core Content**
    - **Validates: pre-refresh content preservation**
    - Read the Target_File and assert (case-insensitive substring):
      `frequency`, `exclusivity`, `stability`, `matched entities`,
      `cross-source` (paired with `relationship`), and `deduplication`
      are all present.
    - Use six independent assertions so a future edit that drops any
      single item fails with a clear message.
    - _Requirements: Req 7.1, Req 5.2; Property 6; Design §Mapping (Property 6)_

- [x] 5. Checkpoint — Run all validators and the new test module
  - Ensure all tests pass, ask the user if questions arise.
  - Run `python senzing-bootcamp/scripts/validate_commonmark.py` and
    confirm the Target_File reports no errors (watch MD022 / MD032 /
    MD040 / MD024 per Design §Error Handling).
  - Run `python senzing-bootcamp/scripts/validate_power.py` and confirm
    no structural errors are reported for the senzing-bootcamp power.
  - Run `python senzing-bootcamp/scripts/measure_steering.py --check`
    one more time to confirm zero drift after the test module was added.
  - Run `pytest senzing-bootcamp/tests/test_entity_resolution_intro_structure.py -v`
    and confirm all six property tests pass.
  - _Requirements: Req 11.1, Req 11.2, Req 11.3; Properties 1–6; Design §Validation Layers_

## Notes

- This workflow creates planning and content artifacts only. Executing
  these tasks will: refresh one markdown steering file, rewrite two
  YAML sections in `steering-index.yaml`, and add one Python test
  module. No SDK code is generated — the Senzing MCP server remains the
  source of any SDK code elsewhere in the bootcamp.
- No tasks are marked optional (`*`). The structural test module is the
  verification mechanism the design depends on and is explicitly part of
  the feature deliverable; its six property sub-tasks are therefore
  required, not optional.
- Each leaf task references the requirement(s) and design section(s) it
  fulfills. Property sub-tasks additionally cite their property number
  and the requirements clauses they validate.
- Checkpoint tasks run the same validators CI runs, so passing Task 5
  locally implies the change is CI-green.

## Workflow Completion

This task list completes the requirements-first spec workflow for
`entity-resolution-intro-refresh`. Open `tasks.md` and click
"Start task" next to any task to begin execution.
