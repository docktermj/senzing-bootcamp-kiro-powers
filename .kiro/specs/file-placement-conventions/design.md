# File Placement Conventions Bugfix Design

## Overview

The senzing-bootcamp Kiro Power steering directs several generated artifacts to throwaway or inconsistent locations. Downloaded Senzing resources land in `data/temp/`, mapping-phase Markdown stays in the workspace directory permanently, the Module 1 stakeholder summary uses a `_module1` suffix that deviates from the template name, and there is no explicit boundary between transformed deliverables and mapping metadata. This fix updates six steering files and one Python script to codify a single, predictable file-placement contract that survives session compaction.

## Glossary

- **Bug_Condition (C)**: An artifact-producing action where the steering directs the artifact to a throwaway or incorrect location, or where the contract is not explicitly stated
- **Property (P)**: Each affected artifact kind lands at its canonical home per the file-placement contract
- **Preservation**: Existing placement behavior for non-affected artifacts (raw data in `data/raw/`, mapper code in `src/transform/`, config in `config/`, etc.) remains unchanged
- **`organize_mapping_files.py`**: The routing script in `senzing-bootcamp/scripts/` that moves mapping workflow output from a flat workspace directory into project subdirectories
- **`file-placement.md`**: The root file-placement reference steering file loaded on any file write
- **`workspace_dir`**: The directory passed to `mapping_workflow` as its working directory (currently resolves to `data/temp/`)
- **Canonical contract**: The six-row table defining where each artifact kind belongs

## Bug Details

### Bug Condition

The bug manifests when the bootcamp steering directs an artifact-producing action to write its output to a location that does not match the canonical file-placement contract. Six steering files and one script contain outdated or missing routing rules that cause artifacts to land in `data/temp/`, use wrong filenames, or mix transformed outputs with mapping metadata.

**Formal Specification:**
```
FUNCTION isBugCondition(X)
  INPUT: X = artifact-producing action { kind, origin, directedPath }
  OUTPUT: boolean

  RETURN
       (X.kind = STAKEHOLDER_SUMMARY AND X.origin = MODULE_1
          AND X.directedPath = "docs/stakeholder_summary_module1.md")
    OR (X.kind = DOWNLOADED_RESOURCE AND X.origin = SENZING_MCP_RESOURCES
          AND X.directedPath NOT IN "src/resources/")
    OR (X.kind = MAPPING_MARKDOWN
          AND X.directedPath NOT IN "docs/mapping/")
    OR (X.kind = MAPPING_WORKING_DATA
          AND X.directedPath NOT IN "data/mapping/")
    OR (X.kind = TRANSFORMED_OUTPUT
          AND X.directedPath NOT IN "data/transformed/"
          AND canonicalDestinationNotStated(X))
    OR (X.kind = ANY AND filePlacementContractNotCodified())
END FUNCTION
```

### Examples

- **Stakeholder summary**: Module 1 step 17 writes to `docs/stakeholder_summary_module1.md` → expected: `docs/stakeholder_summary.md`
- **Downloaded analyzer script**: `sz_json_analyzer.py` stays in `data/temp/` after download → expected: `src/resources/sz_json_analyzer.py`
- **Profile report**: `profile_report.md` stays permanently in `data/temp/` → expected: durable home at `docs/mapping/profile_report.md`
- **Mapping spec JSON**: `customers_mapping_spec.json` stays in `data/temp/` → expected: `data/mapping/customers_mapping_spec.json`
- **Transformed JSONL**: `customers.jsonl` (load-ready) routed to `data/` by organizer → expected: `data/transformed/customers.jsonl`
- **Entity specification download**: `senzing_entity_specification.md` downloaded from MCP → routing rule already correct (`docs/reference`), but other resources have no `src/resources/` route

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Raw source files continue to land in `data/raw/`
- Mapper/transformation code continues to land in `src/transform/`
- The entity specification (`senzing_entity_specification.md`) continues to route to `docs/reference/`
- Config JSON (e.g., `bootcamp_progress.json`) continues to route to `config/`
- `*_mapper.md` files continue to route to `docs/mapping/`
- Mouse/keyboard interactions with the organizer script (CLI interface, argparse, exit codes) remain unchanged
- The `mapping_workflow` MCP tool can still READ intermediate files during a run — the fix changes where files are written, not whether the workflow can access them
- Per-step progress checkpoints in `config/` are unaffected
- Modules other than 1 and 5 are unaffected in their artifact placement

**Scope:**
All inputs that do NOT involve the six affected artifact kinds (stakeholder summary from Module 1, downloaded Senzing resources, mapping-phase Markdown, mapping working data, transformed output, or the contract codification itself) should be completely unaffected by this fix. This includes:
- Raw data ingestion (`data/raw/`)
- Query and load scripts (`src/query/`, `src/load/`)
- Database placement (`database/G2C.db`)
- License files (`licenses/`)
- Test fixtures and monitoring artifacts

## Hypothesized Root Cause

Based on the bug description, the root causes are:

1. **Stakeholder summary naming drift**: `module-01-phase2-document-confirm.md` step 17 hard-codes `docs/stakeholder_summary_module1.md` and the template's MODULE 1 guidance block echoes `Output: docs/stakeholder_summary_module1.md`. The `_module1` suffix was likely a future-proofing decision that conflicts with the template's actual filename (`stakeholder_summary.md`).

2. **Missing `src/resources/` directory and routing**: The project structure (`project-structure.md`) does not list `src/resources/`. The organizer routes `.py` files to `src/mapping/` (not `src/resources/`), and no rule exists for downloaded non-`.py` resources from the MCP server. The `file-placement.md` and `agent-instructions.md` tables have no row for downloaded Senzing resources.

3. **"Leave transient run artifacts in the workspace" is too permanent**: The `module-05-phase2-data-mapping.md` steering block instructs the agent to leave `profile_report.md`, `schema_hints.md`, `JOURNAL.md`, and generated JSONL in `<workspace_dir>` without any follow-up relocation step. The intent was to keep them accessible during the run, but there is no post-run step that moves them to their durable homes (`docs/mapping/` for Markdown, `data/mapping/` for working data, `data/transformed/` for load-ready JSONL).

4. **Missing `data/mapping/` directory**: The project structure and create-structure commands do not include `data/mapping/`. Working data (`*_mapping_spec.json`, `{source}_sample.jsonl`, intermediate analyzer output) has no dedicated home distinct from `data/temp/`.

5. **Organizer routes `.jsonl` to `data/` without distinguishing purpose**: The `ROUTING_RULE_LIST` sends all `.jsonl` to `data/` — it cannot distinguish a mapping sample (`{source}_sample.jsonl`) from a final transformed deliverable (`{source}.jsonl`). The `ROUTING_RULES` compat table mirrors this.

6. **No single codified contract**: The placement rules are scattered across `file-placement.md`, `agent-instructions.md`, `project-structure.md`, and the organizer script, with no authoritative table that explicitly maps each artifact kind to its canonical location.

## Correctness Properties

Property 1: Bug Condition - Misplaced Artifacts Reach Canonical Home

_For any_ artifact-producing action where the bug condition holds (isBugCondition returns true), the fixed steering and organizer SHALL direct that artifact to its canonical home: stakeholder summary → `docs/stakeholder_summary.md`, downloaded resources → `src/resources/`, mapping Markdown → `docs/mapping/`, mapping working data → `data/mapping/`, transformed JSONL → `data/transformed/`.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

Property 2: Preservation - Non-Affected Artifacts Unchanged

_For any_ artifact-producing action where the bug condition does NOT hold (isBugCondition returns false), the fixed steering and organizer SHALL produce the same routing result as the original, preserving all existing correct placements (raw data in `data/raw/`, entity spec in `docs/reference/`, mapper code in `src/transform/`, config in `config/`, `*_mapper.md` in `docs/mapping/`).

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File 1**: `senzing-bootcamp/steering/module-01-phase2-document-confirm.md`

**Location**: Step 17 text

**Specific Changes**:
1. **Replace output path**: Change `docs/stakeholder_summary_module1.md` to `docs/stakeholder_summary.md` in the instruction text at step 17.

---

**File 2**: `senzing-bootcamp/templates/stakeholder_summary.md`

**Location**: MODULE 1 guidance block `Output:` line

**Specific Changes**:
1. **Replace output path**: Change `Output: docs/stakeholder_summary_module1.md` to `Output: docs/stakeholder_summary.md` in the MODULE 1 agent instructions block.

---

**File 3**: `senzing-bootcamp/steering/module-05-phase2-data-mapping.md`

**Location**: "Leave transient run artifacts in the workspace" agent instruction block

**Specific Changes**:
1. **Add post-run relocation guidance**: After the existing block that says "do NOT relocate... while the mapping_workflow run is in progress", add a new agent instruction block that fires after the mapping run completes (i.e., after step 8 quality verdict or step 10 iteration). This block SHALL instruct:
   - Move `profile_report.md`, `schema_hints.md`, `JOURNAL.md` from `<workspace_dir>` to `docs/mapping/`
   - Move `*_mapping_spec.json`, `{source}_sample.jsonl`, and intermediate analyzer JSONL from `<workspace_dir>` to `data/mapping/`
   - Final transformed, load-ready JSONL remains in `data/transformed/` (already handled by step 5 organize call — but the organizer needs the updated rule)
2. **Clarify the transient block scope**: Add a sentence to the existing block: "Once the mapping_workflow run for a source is complete (after the iterate/finalize step), relocate these artifacts to their durable homes per the file-placement contract."

---

**File 4**: `senzing-bootcamp/steering/file-placement.md`

**Location**: Root prohibitions table and after it

**Specific Changes**:
1. **Add canonical contract table**: Add a new `## Canonical File-Placement Contract` section with the six-row artifact→location table so the contract is explicitly codified in one authoritative location.
2. **Update the `.jsonl` correct location**: In the Root Prohibitions table, change `data/raw/`, `data/transformed/`, `data/samples/`, `data/temp/` to include `data/mapping/` as a valid JSONL location.
3. **Add `src/resources/` as a valid `.py` location**: Update the `.py` row's "Correct Location" to include `src/resources/` for downloaded Senzing tooling scripts.

---

**File 5**: `senzing-bootcamp/steering/agent-instructions.md`

**Location**: `## File Placement` table

**Specific Changes**:
1. **Add rows for new locations**: Add `Resources` → `src/resources/` and `Mapping data` → `data/mapping/` to the compact summary table.
2. **Update existing rows**: Ensure `Transformed data` → `data/transformed/` is explicit (currently implied by `Data` → `data/`).

---

**File 6**: `senzing-bootcamp/steering/project-structure.md`

**Location**: Directory tree, rules, and create-structure commands

**Specific Changes**:
1. **Add `src/resources` to tree**: Under `src/`, add `resources` to the brace expansion.
2. **Add `data/mapping` to tree**: Under `data/`, add `mapping` to the brace expansion.
3. **Update Python `os.makedirs` list**: Add `"src/resources"` and `"data/mapping"` entries.
4. **Update Linux/macOS `mkdir -p` command**: Add `resources` to the `src/` brace expansion and `mapping` to the `data/` brace expansion.
5. **Update PowerShell command**: Add `'src/resources'` and `'data/mapping'` to the array.

---

**File 7**: `senzing-bootcamp/scripts/organize_mapping_files.py`

**Location**: `ROUTING_RULE_LIST`, `ROUTING_RULES`, and supporting logic

**Specific Changes**:
1. **Distinguish mapping JSONL from transformed JSONL**: Add a suffix-based rule before the generic `.jsonl` rule:
   - `*_sample.jsonl` → `data/mapping` (mapping working data)
   - `*_mapping_spec.json` → `data/mapping` (mapping metadata — this is JSON but should go to `data/mapping/` not `config/`)
   - Generic `.jsonl` (not `_sample`) → `data/transformed` (final deliverable)
2. **Route downloaded resources**: Add a rule for known resource filenames (`sz_json_analyzer.py`, `sz_verbatim_check.py`, `sz_routing_report.py`) to route to `src/resources` instead of `src/mapping`. Use a `match_name` or `match_suffix` rule placed before the generic `.py` extension rule.
3. **Update the `ROUTING_RULES` compat dict**: Update `.jsonl` → `data/transformed` and `.json` → keep as `config` (the `_mapping_spec.json` is handled by a name-specific rule above it).
4. **Add `data/mapping` routing for intermediate analyzer JSONL**: The analyzer produces JSONL with a predictable naming pattern (e.g., `{source}_analysis.jsonl` or similar). If not distinguishable by name, the post-run relocation in the steering handles it. The organizer handles what it can distinguish by filename convention.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that exercise the `organize_mapping_files.py` routing logic and inspect the steering file content for incorrect paths. Run these tests on the UNFIXED code to observe failures and confirm the root cause.

**Test Cases**:
1. **Stakeholder summary path test**: Assert that `module-01-phase2-document-confirm.md` step 17 directs to `docs/stakeholder_summary.md` (will fail on unfixed code — currently directs to `docs/stakeholder_summary_module1.md`)
2. **Resource routing test**: Call `route("sz_json_analyzer.py")` and assert result is `"src/resources"` (will fail on unfixed code — currently routes to `"src/mapping"`)
3. **Sample JSONL routing test**: Call `route("customers_sample.jsonl")` and assert result is `"data/mapping"` (will fail on unfixed code — currently routes to `"data"`)
4. **Transformed JSONL routing test**: Call `route("customers.jsonl")` and assert result is `"data/transformed"` (will fail on unfixed code — currently routes to `"data"`)
5. **Mapping spec JSON routing test**: Call `route("customers_mapping_spec.json")` and assert result is `"data/mapping"` (will fail on unfixed code — currently routes to `"config"`)
6. **Project structure directories test**: Assert `project-structure.md` lists `src/resources` and `data/mapping` (will fail on unfixed code — these directories are missing)

**Expected Counterexamples**:
- `route("sz_json_analyzer.py")` returns `"src/mapping"` instead of `"src/resources"`
- `route("customers_sample.jsonl")` returns `"data"` instead of `"data/mapping"`
- `route("customers.jsonl")` returns `"data"` instead of `"data/transformed"`
- `route("customers_mapping_spec.json")` returns `"config"` instead of `"data/mapping"`
- Possible causes: generic extension-only routing without filename awareness for these categories

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL X WHERE isBugCondition(X) DO
  result := route_fixed(X.filename)
  ASSERT result = canonicalHome(X.kind)
END FOR
```

Specifically:
- For all filenames matching known resource scripts → assert routes to `src/resources`
- For all filenames matching `*_sample.jsonl` → assert routes to `data/mapping`
- For all filenames matching `*_mapping_spec.json` → assert routes to `data/mapping`
- For all filenames matching generic `.jsonl` (not `_sample`) → assert routes to `data/transformed`

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT route_original(X.filename) = route_fixed(X.filename)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many filenames automatically across the input domain (arbitrary `.py`, `.md`, `.json` files that do not match the new specific rules)
- It catches edge cases that manual unit tests might miss (e.g., a `.py` file whose name happens to start with `sz_` but is not a known resource)
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for all non-affected file types, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Entity spec preservation**: Verify `route("senzing_entity_specification.md")` still returns `"docs/reference"` after fix
2. **Mapper MD preservation**: Verify `route("customers_mapper.md")` still returns `"docs/mapping"` after fix
3. **Generic MD preservation**: Verify `route("any_report.md")` still returns `"docs/mapping"` after fix
4. **Non-resource .py preservation**: Verify `route("transform_customers.py")` still returns `"src/mapping"` after fix
5. **Config JSON preservation**: Verify `route("bootcamp_progress.json")` still returns `"config"` after fix (when filename does not end in `_mapping_spec.json`)

### Unit Tests

- Test `route()` for each new filename-specific rule (resource scripts, sample JSONL, mapping spec JSON)
- Test `route()` for the updated generic `.jsonl` rule (now routes to `data/transformed`)
- Test edge cases: filenames that partially match (e.g., `not_a_sample.jsonl`, `my_mapping_spec.json.bak`)
- Test `plan_moves()` with mixed file sets to verify correct routing of each file type
- Test that the `ROUTING_RULES` compat dict is updated consistently

### Property-Based Tests

- Generate random filenames with known-good extensions (`.py`, `.md`, `.jsonl`, `.json`) that do NOT match the new specific rules, and assert `route()` returns the same result as the original routing for those extensions
- Generate random filenames matching the new rules (`sz_*.py`, `*_sample.jsonl`, `*_mapping_spec.json`) and assert they route to their new canonical homes
- Generate random filenames with unknown extensions and assert `route()` returns `None` (unrouted) — same as before
- Test that `ROUTING_RULE_LIST` ordering is consistent: filename-specific rules always precede extension-only rules (structural property)

### Integration Tests

- End-to-end test: create a temp directory with a mix of resource scripts, sample JSONL, transformed JSONL, mapping spec JSON, mapper MD, and generic MD files. Run `main()` with `--source` and `--project-root` and verify each file lands in the correct subdirectory.
- Test the `--dry-run` flag still reports planned moves correctly with the new routing
- Test deduplication behavior is unchanged for `senzing_entity_specification.md`
- Verify that the create-structure commands in `project-structure.md` produce `src/resources/` and `data/mapping/` directories
