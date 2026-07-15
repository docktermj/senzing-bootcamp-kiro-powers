# Bugfix Requirements Document

## Introduction

The senzing-bootcamp Kiro Power steering directs several generated artifacts to
throwaway or inconsistent locations. Downloaded Senzing resources, mapping-phase
Markdown, and mapping working data land in `data/temp` (which reads as scratch
storage), the Module 1 stakeholder summary is written with a `_module1` suffix
that deviates from the power's own template name, and the boundary between a
transformed deliverable and its mapping metadata is not stated explicitly. The
net effect is poor discoverability, artifacts split across two directories, and
placement decisions that do not survive session compaction.

This bugfix consolidates five related file-placement feedback items into a single,
predictable file-placement contract codified in the bootcamp steering, so the
correct destination is applied from the start of each module and is not lost when
a session is compacted. The change is primarily to steering Markdown under
`senzing-bootcamp/`. It does not change the bootcamp's behavior for artifacts that
are already placed correctly, and it must preserve the mapping workflow's ability
to read its own intermediate files while a mapping run is in progress.

The correct end-state file-placement contract is:

| Artifact | Canonical location |
|---|---|
| Transformation / mapper code | `src/transform/` |
| Downloaded Senzing resources (from `mcp.senzing.com/resources`) | `src/resources/` |
| Mapping-phase Markdown (profile reports, schema hints, journals, mapper specs, quality reports) | `docs/mapping/` |
| Mapping working data / metadata (`*_mapping_spec.json`, `{source}_sample.jsonl`, intermediate analyzer output) | `data/mapping/` |
| Final transformed, load-ready JSONL (the durable deliverable Module 6 loads) | `data/transformed/` |
| Stakeholder summary | `docs/stakeholder_summary.md` (matches `templates/stakeholder_summary.md`, no module suffix) |

## Bug Analysis

### Bug Condition and Properties

The buggy input `X` is an artifact-producing action that the bootcamp steering
directs during a run, described by its artifact kind, its origin, and the
destination path the steering currently directs it to.

- **F** — the original (unfixed) steering: for the affected artifact kinds it
  directs the artifact to a throwaway/incorrect location.
- **F'** — the fixed steering: it directs each affected artifact kind to its
  canonical home per the contract above and codifies that contract explicitly so
  it survives session compaction.

**Bug Condition** — identifies the artifact-producing actions that are misplaced:

```pascal
FUNCTION isBugCondition(X)
  INPUT: X = artifact-producing action { kind, origin, directedPath }
  OUTPUT: boolean

  RETURN
       (X.kind = STAKEHOLDER_SUMMARY AND X.origin = MODULE_1
          AND X.directedPath = "docs/stakeholder_summary_module1.md")
    OR (X.kind = DOWNLOADED_RESOURCE AND X.origin = "mcp.senzing.com/resources"
          AND X.directedPath IN workspace_or_temp)          // e.g. data/temp/
    OR (X.kind = MAPPING_MARKDOWN
          AND X.directedPath IN data_temp)                  // profile_report.md, schema_hints.md, JOURNAL.md
    OR (X.kind = MAPPING_WORKING_DATA
          AND X.directedPath IN data_temp)                  // *_mapping_spec.json, {source}_sample.jsonl, analyzer JSONL
    OR (X.kind = TRANSFORMED_OUTPUT
          AND canonicalDestinationNotStated(X))             // transformed vs. metadata boundary undefined
END FUNCTION
```

**Property: Fix Checking** — every misplaced artifact is directed to its canonical home:

```pascal
FOR ALL X WHERE isBugCondition(X) DO
  path <- F'(X)
  ASSERT path = canonicalHome(X.kind)
  // canonicalHome:
  //   STAKEHOLDER_SUMMARY   -> "docs/stakeholder_summary.md"
  //   DOWNLOADED_RESOURCE   -> "src/resources/"
  //   MAPPING_MARKDOWN      -> "docs/mapping/"
  //   MAPPING_WORKING_DATA  -> "data/mapping/"
  //   TRANSFORMED_OUTPUT    -> "data/transformed/"  (metadata stays in "data/mapping/")
END FOR
```

**Property: Preservation Checking** — every other placement decision is unchanged:

```pascal
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

### Current Behavior (Defect)

1.1 WHEN Module 1 writes the stakeholder summary THEN the steering (`module-01-phase2-document-confirm.md` step 17, and the MODULE 1 guidance block in `templates/stakeholder_summary.md`) directs it to `docs/stakeholder_summary_module1.md`, adding a `_module1` suffix that deviates from the canonical template name `templates/stakeholder_summary.md`.

1.2 WHEN a resource is downloaded from `https://mcp.senzing.com/resources` (e.g., the `sz_json_analyzer.py` analyzer script via `analyze_record`, or the Entity Specification via `download_resource`) THEN the steering leaves it in the workspace/temp directory (`data/temp/`) instead of a stable, predictable location.

1.3 WHEN the `mapping_workflow` produces mapping-phase Markdown artifacts (`profile_report.md`, `schema_hints.md`, `JOURNAL.md`) THEN the steering (`module-05-phase2-data-mapping.md`) instructs keeping them in the workspace (`data/temp`) so the workflow can read them, which leaves durable mapping documentation in throwaway storage and split from the mapper specs and quality reports that already land in `docs/mapping`.

1.4 WHEN the `mapping_workflow` produces working data artifacts (`mapping_spec.json`, the per-source `{source}_sample.jsonl`, and the analyzer's intermediate output JSONL) THEN the steering leaves them in `data/temp`, where meaningful intermediate metadata is easy to lose and inconsistent with the durable mapping locations.

1.5 WHEN a source file in `data/raw` is mapped/transformed THEN the steering does not state an explicit destination convention distinguishing the transformed deliverable from its mapping metadata, so the transformed load-ready JSONL and the `*_mapping_spec.json` metadata can be mixed in the same location.

1.6 WHEN a bootcamp session is compacted mid-run THEN the full file-placement contract is not codified explicitly in one steering location, so the correct destinations are not reliably reapplied after compaction and artifacts drift back to throwaway locations.

### Expected Behavior (Correct)

2.1 WHEN Module 1 writes the stakeholder summary THEN the system SHALL write it to `docs/stakeholder_summary.md` (no module suffix), matching the canonical template name `templates/stakeholder_summary.md`.

2.2 WHEN a resource is downloaded from `https://mcp.senzing.com/resources` THEN the system SHALL save it under `src/resources/`; for `analyze_record` the system SHALL set `workspace_dir` to `src/resources` or relocate the downloaded script there after retrieval, and SHALL apply the same convention to `download_resource` outputs.

2.3 WHEN the `mapping_workflow` produces mapping-phase Markdown artifacts (`profile_report.md`, `schema_hints.md`, `JOURNAL.md`, mapper specs, quality reports) THEN the system SHALL ensure their durable destination is `docs/mapping/` — written there from the start or relocated as soon as each is produced — and the `module-05-phase2-data-mapping.md` steering SHALL be reconciled so the "keep in the workspace during the run" guidance still resolves to a `docs/mapping/` durable home.

2.4 WHEN the `mapping_workflow` produces working data artifacts (`*_mapping_spec.json`, the per-source `{source}_sample.jsonl`, and the analyzer's intermediate output JSONL) THEN the system SHALL place them under `data/mapping/`.

2.5 WHEN a source file in `data/raw` is mapped/transformed THEN the system SHALL write the resulting transformed, load-ready file to `data/transformed/` and SHALL keep mapping metadata (e.g., `*_mapping_spec.json`) in `data/mapping/`.

2.6 WHEN the bootcamp steering defines file placement THEN the system SHALL codify the full contract explicitly in steering so it survives session compaction: transformation/mapper code -> `src/transform/`, downloaded Senzing resources -> `src/resources/`, mapping-phase Markdown -> `docs/mapping/`, mapping working data/metadata -> `data/mapping/`, final transformed JSONL -> `data/transformed/`, and stakeholder summary -> `docs/stakeholder_summary.md`.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN historical Module 1 recap and completion logs reference the old `stakeholder_summary_module1.md` name THEN the system SHALL CONTINUE TO leave those historical references unchanged and SHALL NOT rewrite them.

3.2 WHEN a `mapping_workflow` run is in progress and needs to READ its intermediate files THEN the system SHALL CONTINUE TO keep those files readable by the workflow during the run, while ensuring their durable destinations are `docs/mapping/` (Markdown) and `data/mapping/` (working data).

3.3 WHEN an artifact is not one of the affected kinds (Module 1 stakeholder summary, a `mcp.senzing.com/resources` download, mapping-phase Markdown, mapping working data/metadata, or a transformed output) THEN the system SHALL CONTINUE TO place it at its existing location — including raw source files in `data/raw/`, mapper code in `src/transform/`, per-step progress checkpoints in `config/`, and other unrelated artifacts.

3.4 WHEN a source's provenance means it does not go through the mapping phase, or when other bootcamp modules write their own artifacts THEN the system SHALL CONTINUE TO behave as before, since the contract only governs the artifact kinds named above and only where those kinds are currently misplaced.
