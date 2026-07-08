# Implementation Plan: Kiro 1.0 Hook & Permissions Migration

## Overview

This plan converts the senzing-bootcamp Power from the legacy `*.kiro.hook`
model to the Kiro 1.0 `v1` hook and permissions model in a single coordinated
pass. Implementation language is **Python 3.11+, standard library only** (per
the project tech stack), with **pytest + Hypothesis** for property-based tests.

The build order is bottom-up so nothing is orphaned: the deterministic
`Matcher_Translator` and rename tables come first (with their property tests),
then the one-time migration transform that consumes them to emit the 27 v1 hook
files, then the validators that verify those files, then the tooling
(registry, composer, installer) that reads them, then steering/docs/permissions,
and finally versioning and the CI gates that hold the whole set consistent.

Two open details from the design are resolved inside the tasks that own them:
the exact Kiro 1.0 shell tool name for the `shell` toolType matcher
(`error-recovery-context`, Task 1.1) and whether the 1.0 action schema supports
a command timeout (`session-log-events`, Task 2.2).

## Tasks

- [x] 1. Build the Matcher_Translator module (`scripts/hook_matcher.py`)
  - [x] 1.1 Implement the stdlib-only Matcher_Translator
    - Create `scripts/hook_matcher.py` with `glob_to_regex`, `patterns_to_matcher`, `tooltypes_to_matcher`, `translate_scope`, and a `GlobTranslationError` exception
    - Implement the glob→regex algorithm over the forward-slash-normalized, workspace-relative path domain: escape metacharacters except glob wildcards; `**/`→`(?:.*/)?`; `**`→`.*`; `*`→`[^/]*`; `?`→`[^/]`; literal `.`→`\.`; preserve balanced `[...]`; reject unbalanced brackets; anchor+alternate as `^(?:frag1|frag2|...)$`
    - `patterns_to_matcher` combines globs into one anchored file-path matcher; `tooltypes_to_matcher` maps `write`→`fs_write|str_replace|fs_append` and `shell`→the 1.0 shell/command tool-name regex; `translate_scope` returns `None` for unscoped `when` blocks
    - **Resolve open detail (error-recovery-context):** confirm the exact Kiro 1.0 shell/command tool name against the 1.0 tool taxonomy and use it in the `shell` mapping
    - _Requirements: 3.1, 3.3, 3.4, 3.6_

  - [x] 1.2 Write property test for glob-to-regex match-set equivalence
    - **Property 1: Glob-to-regex match-set equivalence**
    - Use `st_glob()` / `st_path()` strategies with `fnmatch`/`PurePosixPath.match` as the oracle; consider a higher `@settings` example override for this property
    - **Validates: Requirements 3.1, 3.2**

  - [x] 1.3 Write property test for translation determinism and idempotence
    - **Property 2: Translation determinism and idempotence**
    - Assert repeated translation yields a byte-identical regex and preserves the matched-path set
    - **Validates: Requirements 3.5**

  - [x] 1.4 Write property test for the write tool-type matcher
    - **Property 3: Write tool-type produces the fixed write matcher**
    - Assert any `toolTypes` list containing `write` yields exactly `fs_write|str_replace|fs_append`
    - **Validates: Requirements 3.3, 5.2**

  - [x] 1.5 Write unit tests for Matcher_Translator error handling
    - Test empty/whitespace-only globs and unbalanced character classes raise `GlobTranslationError` naming the offending pattern
    - Test the representative glob table from the design (`src/**/*.py`, `src/load/*.*`, `config/*credentials*`, `.env*`, `data/transformed/*.jsonl`)
    - _Requirements: 3.6_

- [x] 2. Implement rename tables and the one-time migration transform
  - [x] 2.1 Implement the trigger and action rename mapping tables
    - Define the trigger rename table (`fileEdited`→`PostFileSave`, `fileCreated`→`PostFileCreate`, `fileDeleted`→`PostFileDelete`, `agentStop`→`Stop`, `promptSubmit`→`UserPromptSubmit`, `postTaskExecution`→`PostTaskExec`, `preToolUse`→`PreToolUse`, `postToolUse`→`PostToolUse`) and the action rename (`askAgent`+`prompt`→`{type:agent,prompt}`, `runCommand`+`command`→`{type:command,command}`) in one shared module reused by the validator accept-list
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10_

  - [x] 2.2 Implement the migration transform (`scripts/migrate_hooks.py`)
    - Read the 30 legacy `hooks/*.kiro.hook` files; classify manual (`userTriggered`) vs non-manual
    - For the 27 non-manual hooks: apply trigger/action rename (Task 2.1), derive the matcher via `translate_scope` (Task 1.1), preserve `name` and prompt/command text verbatim, and emit the `{"version":"v1","hooks":[...]}` wrapper per hook file
    - Omit the `matcher` key for unscoped triggers; fail with a message naming the hook id and unsupported construct if a hook cannot be represented as valid v1
    - **Resolve open detail (session-log-events):** determine whether the 1.0 action schema supports a command timeout; preserve the `timeout: 10` equivalent when supported, otherwise record the omission (command remains functionally equivalent)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 3.4_

  - [x] 2.3 Write property test for trigger and action rename totality and range
    - **Property 5: Trigger and action rename totality and range**
    - Use `st_legacy_hook()` across all trigger/action variants; assert every produced trigger is in the 1.0 set and every action type is `agent`/`command`
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10**

  - [x] 2.4 Write property test for verbatim name and action-text preservation
    - **Property 6: Name and action text are preserved verbatim**
    - Assert migrated `name` equals legacy `name` and migrated `prompt`/`command` equals `then.prompt`/`then.command` byte-for-byte
    - **Validates: Requirements 1.4, 1.5, 4.2, 5.3**

  - [x] 2.5 Write property test for unscoped-trigger matcher omission
    - **Property 4: Unscoped triggers omit the matcher**
    - Assert `agentStop`/`promptSubmit`/`postTaskExecution` hooks migrate with no `matcher` (or the empty value the 1.0 schema requires)
    - **Validates: Requirements 3.4**

- [x] 3. Generate the shipped v1 hook definitions
  - [x] 3.1 Emit the 27 v1 hook JSON files
    - Run the migration transform to write `hooks/<id>.json` for all 27 non-manual hooks (one hook per file, preserving the 1:1 file-to-id mapping)
    - Confirm the three write gates (`write-policy-gate`, `enforce-mandatory-gate`, `gate-module3-visualization`) emit `trigger: PreToolUse` with matcher `fs_write|str_replace|fs_append` and verbatim policy prompts
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 5.1, 5.2, 5.3_

  - [x] 3.2 Write example test for migration completeness
    - Assert exactly 27 `hooks/*.json` files exist, one per non-manual legacy id, and each write gate carries the fixed write matcher
    - _Requirements: 1.1, 5.1, 5.2_

- [x] 4. Update hook validation to the v1 schema
  - [x] 4.1 Update `validate_power.py` `check_hooks` to v1
    - Switch discovery glob to `*.json`; validate top-level `version == "v1"` + `hooks` array; require `name`/`trigger`/`action` and `matcher` where the trigger requires scoping; accept only 1.0 trigger names and action types `agent`/`command`; compile any present matcher with `re.compile`; report legacy `*.kiro.hook`/`when`/`then` files by name; reuse `check_registry_consistency` against v1 files
    - Re-express `FILE_EVENT_TYPES`/`TOOL_EVENT_TYPES`/`VALID_EVENT_TYPES` in 1.0 trigger names
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 14.5_

  - [x] 4.2 Update `test_hooks.py` to v1 discovery and schema
    - Switch discovery to `*.json`, parse the v1 wrapper, and validate the same 1.0 schema rules against the shipped hook files
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 4.3 Write property test for the migrate→validate round trip
    - **Property 7: Migration produces schema-valid V1 hooks (migrate → validate round trip)**
    - For any non-manual legacy hook, assert the migrated hook passes the updated validator (wrapper shape, required fields, matcher-when-required, matcher compiles)
    - **Validates: Requirements 1.2, 1.3, 6.1, 6.2, 6.5**

  - [x] 4.4 Write unit tests for validator rejection paths
    - Assert the validator rejects legacy trigger names, `askAgent`/`runCommand`, and any residual `*.kiro.hook`/`when`/`then` file
    - _Requirements: 6.3, 6.4, 6.6_

- [x] 5. Checkpoint - core migration and validation
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Convert manual hooks to slash-command steering files
  - [x] 6.1 Create the three Slash_Command_Files
    - Create `steering/slash-backup-project.md`, `steering/slash-git-commit.md`, and `steering/slash-commonmark-validation.md` with `inclusion: manual` frontmatter and the legacy prompt instruction text preserved in the body
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 6.2 Update `steering/steering-index.yaml`
    - Add token count and size category for the three new slash-command files; remove any stale `file_metadata` entries for the three removed manual hooks
    - _Requirements: 4.6_

  - [x] 6.3 Remove manual hook ids from `hooks/hook-categories.yaml`
    - Delete `backup-project-on-request`, `git-commit-reminder`, and `commonmark-validation` from the category and `agentstop_order` mappings
    - _Requirements: 4.4, 4.5_

- [x] 7. Add the write-gate governance guard
  - [x] 7.1 Implement the write-gate governance guard
    - Extend `validate_governance_rules.py` (or add a dedicated check) to assert `write-policy-gate`, `enforce-mandatory-gate`, and `gate-module3-visualization` remain present as `PreToolUse` hooks with the `fs_write|str_replace|fs_append` matcher; fail and block when any is missing/disabled unless the guard's expected set is updated in the same change (the approval signal)
    - _Requirements: 5.4, 5.5_

  - [x] 7.2 Write unit tests for the governance guard
    - Assert the guard fails when a gate is absent/disabled and passes when the expected set is updated to match
    - _Requirements: 5.4, 5.5_

- [x] 8. Regenerate the registry and lockfile in v1 terms
  - [x] 8.1 Update `sync_hook_registry.py` to v1
    - Switch discovery to `*.json`; make `parse_hook_file` read the v1 wrapper and map `trigger`/`action.type`/`matcher` onto `HookEntry`; update `_format_event_flow`/`format_hook_entry` to render 1.0 triggers and the single matcher; emit full v1 prompt text + 1.0 `createHook` params; list exactly the 27 migrated hooks (exclude the 3 manual ids)
    - _Requirements: 7.1, 7.2, 7.3, 7.6_

  - [x] 8.2 Regenerate registry slices and lockfile
    - Run `sync_hook_registry.py --write` to regenerate `steering/hook-registry-critical.md`, the per-module `hook-registry-module-*.md` slices, and `hooks/hooks.lock.yaml` (27 entries, each `event_type` carrying its 1.0 trigger)
    - _Requirements: 7.3, 7.4_

  - [x] 8.3 Write property test for registry generation round-trip and id consistency
    - **Property 8: Registry generation round-trip and identifier consistency**
    - Assert `--write` then `--verify` succeeds (stable fixed point), the lockfile records each id with its 1.0 trigger, and registry ids equal shipped hook ids
    - **Validates: Requirements 7.1, 7.2, 7.4, 7.5, 14.4**

  - [x] 8.4 Write unit test for `--verify` success against committed output
    - Assert `sync_hook_registry.py --verify` exits 0 against the committed registry/lockfile and the lockfile has 27 entries
    - _Requirements: 7.5_

- [x] 9. Update the prompt composer for v1 output
  - [x] 9.1 Update `compose_hook_prompts.py` to compose v1 gate hooks
    - Compose `gate-module3-visualization`, `enforce-mandatory-gate`, and `enforce-gate-on-stop` as v1 hooks: read static `name`/`trigger`/`matcher` from the on-disk v1 file and swap only `action.prompt`; keep `serialize_hook` byte-identical; preserve fragment text from `hook_prompt_fragments.py` verbatim
    - _Requirements: 8.1, 8.2_

  - [x] 9.2 Recompose the Module 3 gate hooks
    - Run `compose_hook_prompts.py --write` to produce byte-stable v1 gate hook files
    - _Requirements: 8.3_

  - [x] 9.3 Write property test for composer byte-stability round-trip
    - **Property 9: Prompt composer byte-stability round-trip**
    - Assert `--write` is deterministic on repeat and equals the committed v1 gate files
    - **Validates: Requirements 8.2, 8.3, 8.4**

  - [x] 9.4 Write unit test for `--verify` and CI ordering
    - Assert `compose_hook_prompts.py --verify` exits 0 against committed files and runs before `sync_hook_registry.py --verify` in CI
    - _Requirements: 8.4, 8.5_

- [x] 10. Update the hook installer for v1
  - [x] 10.1 Update `install_hooks.py` to v1
    - `discover_hooks` globs `*.json` and reads `name` from `hooks[0].name`; change `HOOK_METADATA` keys to `<id>.json`; re-derive `ESSENTIAL`/`CAPTURE_CRITICAL` from the migrated `hook-categories.yaml`, excluding `commonmark-validation` from the critical set; report the actual installed `*.json` count
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [x] 10.2 Write property test for no-manual-hook invariant
    - **Property 10: No shipped hook is manual**
    - Assert no shipped v1 file uses `userTriggered`/manual and none of the three manual ids appears in any install set
    - **Validates: Requirements 4.4, 9.4**

  - [x] 10.3 Write integration test for the installer
    - Install into a temp `.kiro/hooks/`, assert v1 files copied, sets derived from files, manual ids and `commonmark-validation` excluded from the right sets, and reported count equals installed count
    - _Requirements: 9.1, 9.2, 9.3, 9.5, 9.6_

- [x] 11. Checkpoint - tooling in lockstep
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Update the onboarding hook-creation path
  - [x] 12.1 Update onboarding steering to 1.0
    - Re-express hook-creation instructions in `onboarding-flow.md`, `onboarding-phase2-track-setup.md`, `agent-instructions.md`, and `session-resume-phase2-setup-recovery.md` using 1.0 `trigger`/`matcher`/`action` terminology sourced from the registry; create `ask-bootcamper`, `module-recap-append`, `session-log-events` as v1 hooks; remove `commonmark-validation` from the critical-creation list and its failure-impact messages; point bootcampers to the slash command; make session-start presence checks look for `<id>.json`
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [x] 12.2 Write example test for onboarding steering
    - Assert onboarding steering uses 1.0 trigger names, checks `.json` presence, creates the three capture-critical hooks, and routes former manual hooks to slash commands
    - _Requirements: 10.2, 10.3, 10.5, 10.6_

- [x] 13. Update documentation and steering to v1
  - [x] 13.1 Update `hooks/README.md`
    - Describe the migrated hook set with 1.0 trigger names, the migrated count, and `.json` v1 installation instead of `*.kiro.hook`
    - _Requirements: 11.1, 11.2_

  - [x] 13.2 Update the hook guides
    - Update `docs/guides/HOOKS_INSTALLATION_GUIDE.md` (1.0 creation path, accurate counts, 1.0 triggers) and `steering/hook-architecture.md` (`Stop`-trigger precedence and guard rules in 1.0 terms)
    - _Requirements: 11.3, 11.4_

  - [x] 13.3 Sweep remaining steering references to 1.0 terminology
    - Update all remaining steering references to hook triggers/actions to 1.0 terms and repoint any doc/steering reference to a removed manual hook to its Slash_Command_File
    - _Requirements: 11.5, 11.6_

  - [x] 13.4 Write example test for docs/steering terminology
    - Assert docs and steering use 1.0 trigger names and the migrated count, and contain no reference to a removed manual hook as an automatic hook
    - _Requirements: 11.1, 11.3, 11.6_

- [x] 14. Document permissions and MCP auto-approve
  - [x] 14.1 Create the Permissions_Doc
    - Add a guide under `docs/guides/` describing the 1.0 write, shell, and MCP capabilities the bootcamp requests and the recommended approval scope for file writes, Python script executions, and Senzing MCP calls
    - _Requirements: 12.1, 12.2_

  - [x] 14.2 Populate `mcp.json` auto-approve
    - Add the 12 read-only active Senzing MCP tools (`get_capabilities`, `mapping_workflow`, `analyze_record`, `download_resource`, `explain_error_code`, `search_docs`, `find_examples`, `generate_scaffold`, `get_sample_data`, `get_sdk_reference`, `sdk_guide`, `reporting_guide`) to `autoApprove`; keep `submit_feedback` in `disabledTools`; keep `mcp.json` the sole source of the server URL
    - _Requirements: 12.3, 12.4, 12.5_

  - [x] 14.3 Write unit test for the MCP config
    - Assert `autoApprove` lists the 12 active tools, `submit_feedback` stays disabled, and no hardcoded MCP URL exists outside `mcp.json`
    - _Requirements: 12.3, 12.4, 12.5_

- [x] 15. Record the back-compat decision and version bump
  - [x] 15.1 Remove the legacy hook files
    - Delete all `hooks/*.kiro.hook` files so only v1 definitions ship
    - _Requirements: 13.1_

  - [x] 15.2 Update version and back-compat metadata
    - Set `senzing-bootcamp/VERSION` to `0.2.0`; set the `POWER.md` frontmatter version equal to `VERSION`; state in `POWER.md` that the Power requires Kiro 1.0 or later; add a new released `CHANGELOG.md` section (Keep a Changelog format) recording the migration
    - _Requirements: 13.2, 13.3, 13.4, 13.5_

  - [x] 15.3 Write example test for versioning and back-compat
    - Assert no `*.kiro.hook` files remain, `POWER.md` declares Kiro 1.0+, `CHANGELOG.md` has a new released section, `VERSION` > `0.1.3`, and the `POWER.md` frontmatter version equals `VERSION`
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 16. Add the stale-reference gate and wire CI green
  - [x] 16.1 Implement the stale-legacy-reference CI gate
    - Add a check that scans hook files, configs, steering, and docs for residual legacy schema references (`*.kiro.hook`, `when`/`then`, legacy trigger/action names) and fails identifying the stale reference
    - _Requirements: 14.5_

  - [x] 16.2 Wire the new gates into `validate-power.yml`
    - Add the write-gate governance guard and the stale-reference gate to the workflow while preserving the existing sequence (`validate_power.py`, `test_hooks.py`, `compose_hook_prompts.py --verify` before `sync_hook_registry.py --verify`, `measure_steering.py --check`, pytest)
    - _Requirements: 14.1, 14.5_

  - [x] 16.3 Verify the full CI suite is green
    - Run `validate_power.py`, `test_hooks.py`, `compose_hook_prompts.py --verify`, `sync_hook_registry.py --verify`, `measure_steering.py --check`, the governance guard, the stale-reference gate, and pytest with `HYPOTHESIS_PROFILE=thorough`; confirm all pass and shipped hooks/categories/registry/lockfile stay mutually consistent
    - _Requirements: 14.1, 14.2, 14.3, 14.4_

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP; core implementation sub-tasks are never optional.
- Each task references the specific requirement clauses it satisfies for traceability.
- Property tests are placed next to the code they validate and are tagged in-source as **Feature: kiro-1-0-migration, Property {N}: {property text}**; each of Properties 1-10 is implemented by exactly one property-based test.
- All tooling changes use the Python standard library only; property tests use pytest + Hypothesis with the repo's registered profiles (`fast` locally, `thorough` in CI).
- Repo-level tests that validate the real shipped hook files live in the repo-root `tests/`; pure-logic unit/property tests for the Matcher_Translator and generators live in `senzing-bootcamp/tests/`.
- Two open details are resolved in the tasks that own them: the 1.0 shell tool name in Task 1.1 and the 1.0 command-timeout capability in Task 2.2.
- Checkpoints (Tasks 5, 11, 17) ensure incremental validation before moving on.

- [x] 17. Final checkpoint - full migration verified
  - Ensure all tests pass, ask the user if questions arise.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "14.1", "14.2"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4", "1.5", "2.2"] },
    { "id": 2, "tasks": ["2.3", "2.4", "2.5", "3.1"] },
    { "id": 3, "tasks": ["3.2", "4.1", "4.2", "6.1", "6.2", "6.3", "7.1", "8.1", "9.1", "14.3"] },
    { "id": 4, "tasks": ["4.3", "4.4", "7.2", "9.2", "10.1"] },
    { "id": 5, "tasks": ["8.2", "9.3", "9.4", "10.2", "10.3", "13.1", "13.2", "13.3", "15.1", "15.2"] },
    { "id": 6, "tasks": ["8.3", "8.4", "12.1", "13.4", "15.3", "16.1"] },
    { "id": 7, "tasks": ["12.2", "16.2"] },
    { "id": 8, "tasks": ["16.3"] }
  ]
}
```
