# Changelog

All notable changes to the Senzing Bootcamp power will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Versioning note.** An early `1.0.0` was set prematurely (see the
> `## [1.0.0] - 2026-06-24` section below) and then withdrawn. The Power's
> public versioning was re-based onto the `0.x` line for the Kiro 1.0 migration,
> so the current shipping version is `0.2.0` and the `0.x` releases dated after
> 2026-06-24 supersede that withdrawn `1.0.0` entry. The `1.0.0` section is kept
> for historical continuity, which is why the version numbers below are not
> strictly monotonic by date. `VERSION` and the POWER.md frontmatter are the
> authoritative current version.

## [Unreleased]

## [0.2.0] - 2026-07-15

Kiro 1.0 hook & permissions migration. The Power now targets the Kiro 1.0 `v1`
hook and permissions model and **requires Kiro 1.0 or later** — legacy
`*.kiro.hook` files do not execute under Kiro 1.0.

### Added

- `scripts/hook_matcher.py` — deterministic, stdlib-only Matcher_Translator
  (glob→regex over the workspace-relative path domain) plus the trigger/action
  rename tables that back the migration and validator accept-list
- `scripts/migrate_hooks.py` — one-time legacy→v1 migration transform that reads
  the legacy `hooks/*.kiro.hook` files and emits the `{"version":"v1","hooks":[...]}`
  wrapper per hook, preserving `name` and prompt/command text verbatim
- Three slash-command steering files replacing the former manual hooks —
  `steering/slash-backup-project.md`, `steering/slash-git-commit.md`, and
  `steering/slash-commonmark-validation.md` (`inclusion: manual`, legacy prompt
  text preserved)
- Kiro 1.0 permissions guide under `docs/guides/` documenting the write, shell,
  and Senzing MCP capabilities the bootcamp requests and the recommended
  approval scope for file writes, Python script executions, and MCP calls
- Write-gate governance guard and a stale-legacy-reference CI gate that fail if a
  required `PreToolUse` write gate is missing/disabled or any file still
  references the legacy schema

### Changed

- Converted the 26 non-manual hooks from legacy `*.kiro.hook` to the Kiro 1.0
  `v1` JSON schema with renamed triggers (`fileEdited`→`PostFileSave`,
  `agentStop`→`Stop`, `preToolUse`→`PreToolUse`, …), restructured actions
  (`askAgent`/`prompt`→`{type:agent,prompt}`, `runCommand`/`command`→
  `{type:command,command}`), and `when.patterns`/`when.toolTypes` folded into a
  single regex `matcher`; the three write gates (`write-policy-gate`,
  `enforce-mandatory-gate`, `gate-module3-visualization`) emit
  `trigger: PreToolUse` with the fixed `fs_write|str_replace|fs_append` matcher
- Updated the hook tooling to v1: validator (`validate_power.py` `check_hooks`
  and `test_hooks.py`), registry sync (`sync_hook_registry.py` +
  `hooks/hooks.lock.yaml`, 26 entries), prompt composer
  (`compose_hook_prompts.py`), and installer (`install_hooks.py`) now discover,
  read, and emit `*.json` v1 definitions
- Re-expressed the onboarding hook-creation path, steering files, and
  documentation (`hooks/README.md`, `docs/guides/HOOKS_INSTALLATION_GUIDE.md`,
  `steering/hook-architecture.md`, hook-registry slices) in 1.0
  trigger/matcher/action terminology, and repointed references to the removed
  manual hooks at their slash-command files
- Populated `mcp.json` `autoApprove` with the 12 read-only active Senzing MCP
  tools while keeping `submit_feedback` disabled and `mcp.json` the sole source
  of the server URL
- Bumped `VERSION` to `0.2.0` and set the `POWER.md` frontmatter version to match

### Removed

- Legacy `hooks/*.kiro.hook` files — only v1 `*.json` hook definitions ship now

## [0.1.3] - 2026-07-07

### Added

- Module 1 Business Case Offer — `scripts/business_case_offer.py` models a
  Generated_Scenario for bootcampers who have no business case to share (or
  one they can't share), validates its invariants (multi-source, mapping
  complexity, recognized category, completeness), renders
  `docs/business_problem.md`, and records Scenario_Data sources into
  `config/data_sources.yaml`. Backed by a CORD dataset or synthetic data per
  the Step 5b MCP decision
- `scripts/generate_standalone_demo.py` — a minimal, TruthSet-backed
  standalone entity-resolution visualization (stdlib HTTP server + D3.js v7,
  single self-contained `index.html`) offered as the journey-level "first
  visualization" when a bootcamper opts out of Module 3
- `scripts/record_count_backfill.py` — Module 4 record-count license
  back-fill: infers the collected record total from the registry, compares it
  against the built-in 500-record evaluation limit, and surfaces the existing
  Module 1 license guidance when exceeded (non-blocking, delegates wording to
  `volume_utils.build_license_framing`)
- `scripts/baseline_status.py` — read-only ER baseline status summary
  reporting which registered data sources have an accepted baseline; never
  creates, modifies, or deletes any file
- `scripts/capture_hook_safeguard.py` — module-completion safeguard that
  detects any absent capture-critical hook (`session-log-events`,
  `module-recap-append`, `ask-bootcamper`) and renders an overridable
  Soft_Block reminder (never a Mandatory_Gate); shares its id list with
  `install_hooks.CAPTURE_CRITICAL`
- `scripts/recap_pdf_render.py` — canonical shared raw-Markdown→PDF renderer
  imported by both `generate_recap_pdf.py` and the new inline generator,
  eliminating a duplicated renderer; `fpdf` imported lazily, degrades
  gracefully when absent
- `scripts/generate_recap_pdf_inline.py` — self-contained inline recap-PDF
  fallback used by graduation when the bundled helper cannot be located or run
- `scripts/fpdf2_preflight.py` — non-blocking Track_Completion note that
  installing optional `fpdf2` produces a PDF (Markdown is produced regardless);
  shown only when `fpdf2` is absent
- `scripts/reconcile_transcript.py` — idempotent, non-blocking pre-render pass
  that backfills Q&A transcript shortfalls from the enforced recap source
  before `generate_transcript.py` renders
- `scripts/run_bundled_script.py` — guarded runner for bundled scripts so a
  script not materialized in the bootcamper's workspace degrades gracefully
  instead of surfacing a raw file-not-found error
- Advanced-track knowledge check, always-loaded steering-budget check, Module 2
  license-acquisition guidance, and a Module 6 SQLite volume prompt

### Changed

- Recommended model updated to Claude Opus 4.8
- CI workflow restructured; Hypothesis example counts centralized into
  registered profiles (`fast`/`thorough`/`bootcamp`) in the repo-root
  `hypothesis_profiles.py`; test suite parallelized (`pytest -n auto`)
- Graduation and module-completion flows now generate a docs index and route
  recap/transcript rendering through the shared renderer for content-complete
  output with or without `fpdf2`
- Steering split-threshold enforcement and shared-Markdown-renderer refactor;
  pytest now at 6,338 passed / 0 failed / 88 skipped

### Fixed

- Module 3 entity-graph edge-key mismatch — `drawGraph` maps
  `source_entity_id`/`target_entity_id` → `source`/`target` before `forceLink`
  so the rendered force-directed graph shows visible nodes
- TypeScript build-failure recovery guidance added for the SDK setup flow
- Recap completeness and PDF content-loss fixes, including Q&A pair merge and
  QR formatting, so no recap content is dropped in either the Markdown or PDF
  output paths

## [1.0.0] - 2026-06-24

> **Superseded / withdrawn.** This `1.0.0` was tagged prematurely and later
> withdrawn; the Power re-based to the `0.x` line (see the Versioning note near
> the top of this file). Retained for historical continuity only.

### Production release

- First production (`1.0.0`) release. Full CI validation suite green across all
  gates; pytest at 5,708 passed / 0 failed / 88 skipped. Ruff gate confirmed
  clean against current ruff (0.15.19). MCP tool inventory re-confirmed live
  against `sz-mcp-coworker` v1.26.8 (13 tools, names matching the pinned
  inventory in `scripts/mcp_tool_inventory.py`).

### Added

- `scripts/mcp_tool_inventory.py` — canonical single source of truth for the
  13-tool MCP inventory (ALL_TOOLS + TOTAL_COUNT), confirmed live against
  get_capabilities(version="current") on sz-mcp-coworker v1.24.0
- `tests/test_mcp_tool_inventory.py` — pins the 13-tool inventory and the
  absence of any lint_record tool
- `check_mcp_tool_inventory()` gate in `scripts/validate_power.py` — fails CI if
  POWER.md / ARCHITECTURE.md tool listings drift from mcp_tool_inventory.py
- `check_module_inventory()` gate in `scripts/validate_power.py` — cross-checks
  the POWER.md generated module table and every script module-name map against
  `config/module-dependencies.yaml` (the single source of truth); fails CI on a
  renamed module, a wrong name for a number, or a stale "Module 12"
- `tests/test_module_inventory.py` — pins the canonical 11-module roster and
  asserts all eight script module-name maps and the POWER.md table match it

### Fixed

- CI green-up after the post-0.12.1 spec batch (qa-transcript, graduation-markdown
  normalization, module3-entity-graph-relationships, onboarding-license-request-option,
  recap-pdf-content-loss-fix, session-log-hook-performance, track-selection-drop-module2-note)
  left four gates red:
  - Regenerated the POWER.md generated regions (`generate_power_docs.py --write`) —
    the steering-files table was missing `qa-transcript.md` and carried stale token
    counts; resynced `steering/steering-index.yaml` to exact counts via
    `measure_steering.py` (budget total 182394 → 185282) and re-baselined the budget
    block hash / total assertion in `test_steering_index_token_count_sync_preservation.py`
  - Regenerated `.kiro/SPEC_CATALOG.md` (`generate_spec_catalog.py`) — 7 new specs
    (224 → 231 implemented) were unindexed
  - Cleared 3 ruff violations in new test files (`test_generate_transcript.py` E501;
    `test_normalize_markdown.py`, `test_normalize_recap_pdf_integration.py` I001)
  - Fixed 21 failing tests: generalized the generic hook-structural/schema validators
    to accept the new `session-log-events` `runCommand` hook (askAgent→prompt,
    runCommand→command) via a new action-aware `required_fields_for_action()` helper
    in `tests/hook_test_helpers.py`, and refreshed onboarding preservation tests to the
    current copy ("500-record evaluation license"; Module 2 auto-insertion note removed
    from track selection per the bugfix). pytest now at 5708 passed / 0 failed
- Module numbering/naming drift across docs and scripts: corrected the POWER.md
  "Module Progression" narrative (the stale `1 → 4 → 5 → 2 → 6 → 7` order and
  "topic labels" framing now read as the canonical ascending `1 → 2 → … → 7`),
  and refreshed `docs/diagrams/module-flow.md`, `docs/diagrams/module-prerequisites.md`,
  `docs/diagrams/data-flow.md`, `docs/diagrams/system-architecture.md`,
  `docs/guides/PROGRESS_TRACKER.md`, and `templates/stakeholder_summary.md` to the
  current roster (6 = Data Processing, 7 = Query/Visualize/Discover, 8 = Performance,
  9 = Security, 10 = Monitoring, 11 = Package & Deploy)
- Stale module-name maps and a phantom "Module 12" in `scripts/export_results.py`,
  `scripts/repair_progress.py`, and `scripts/team_dashboard.py`; normalized the
  display names in `status.py`, `rollback_module.py`, `assess_entry_point.py`,
  `validate_module.py`, and `visualize_dependencies.py` to the canonical roster
- HTML dashboards (`status.py`, `export_results.py`, `team_dashboard.py`) computed
  completion against 12 modules (so all 11 done showed 91%) and rendered a phantom
  12th card; the count is now derived from the module roster (`len(MODULE_NAMES)` /
  `TOTAL_MODULES`) so it stays correct

### Changed

- Normalized the `analyze_record` call signature to
  `analyze_record(file_paths=[...], workspace_dir="<dir>", version="current")`
  across `steering/mcp-tool-decision-tree.md`,
  `docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md`, and
  `steering/troubleshooting-commands.md`

## [0.12.1] - 2026-06-08

### Changed

- `validate_links.py` external-link check wired into the CI gate sequence (after `validate_yaml_schemas`); intentional example endpoints, XML-namespace identifiers, and bot-blocking hosts added to its ignore list so the gate flags only genuine breakage
- `module-transitions.md` reverted from `inclusion: fileMatch` back to `inclusion: always` — the file is needed on every module start/completion, and conditional loading caused missed banners when progress file wasn't the trigger
- Renamed `tests/test_module12_phase_gate.py` → `tests/test_hook_schema_conformance.py` — the test validates hook JSON schema generically, not Module-12-specific logic (Module 12 was collapsed into Module 11 in 0.11.0)
- `steering-index.yaml` Module 4 entry expanded from bare string to phases map with `token_count` and `size_category` for consistency with all other modules
- `lint_steering.py` now resolves registered hooks against the **union** of registry sources (`hook-categories.yaml` plus the `hooks/` directory) instead of a single source, so hooks present in either place are recognized and stop producing false "unregistered hook" findings
- `measure_steering.py --check` gained an additive aggregate check: a new `parse_budget_total` helper reads `budget.total_tokens` and the run now emits a `Budget total mismatch` line (and exits non-zero) when the declared aggregate diverges from `sum(file_metadata)` token counts — per-file and per-phase verdicts are unchanged
- Onboarding-split test target re-pointed to the current 147-test layout after the onboarding-question suite was split, so the count assertion tracks the live 147 tests
- Remediated 435 style-only ruff violations to drive the "Lint Python (ruff)" CI gate from 438 violations to 0: E501 long lines reflowed to ≤100 chars (source layout only, emitted strings/output unchanged), E402 module-import-not-at-top suppressed for the documented `sys.path`-before-import pattern via scoped `per-file-ignores` / `# noqa: E402`, F841 unused assignments and W293 whitespace auto-fixed, and E741 ambiguous single-char names renamed to descriptive identifiers — no runtime behavior change to any script

### Fixed

- Resolved 3 correctness defects surfaced by the "Lint Python (ruff)" gate: 2× F811 duplicate test functions in `test_module_closing_question_ownership.py` that silently shadowed the earlier `test_module_07_no_inline_questions` / `test_module_07_no_wait_instructions` definitions (both now execute) and 1× F601 duplicate dict key `6` in `test_validate_module.py` that dropped a fixture entry (collapsed to the complete 3-lambda superset including `loading_strategy.md`); 4,830 passing tests and all other CI gates preserved with no runtime behavior changes to scripts
- Added preservation test `tests/test_module_transitions_always_inclusion.py` pinning `module-transitions.md` to `inclusion: always` — prevents accidental regression
- `steering-index.yaml` `budget.total_tokens` corrected from `169633` to `169576` to match the live `sum(file_metadata)` token total, clearing the aggregate drift now enforced by `measure_steering.py`
- `preferences_utils.py` boolean-string round-trip fidelity (A1): values that serialize to `"true"`/`"false"` now survive a write-then-read cycle without being coerced to native booleans or altered casing, so persisted preferences round-trip exactly
- `validate_mandatory_gates.py` mandatory-gate parsing made non-vacuous (B): the parser now recognizes gates declared under H2/H3 headings, inside blockquotes, and in section preambles, so the validator detects the shipped gates instead of passing on an empty set — covered by a new regression test that runs the validator's own parser against the real steering corpus and fails if zero gates are found
- `validate_prerequisites.py` no longer emits the spurious `3 -> 4` prerequisites keyword-mismatch warning (D); the false positive for the Module 3→4 gate is removed
- Stabilized property tests (A2–A5): tightened test-logic and generators and de-flaked timing-sensitive assertions so the previously failing/flaky property tests run deterministically
- Corrected the broken Senzing support URL (`https://senzing.com/support/` returned 404) to `https://senzing.com/contact/` in `POWER.md` and `licenses/README.md`
- Updated the recommended-model note in `POWER.md` (Claude Opus 4.6 → 4.8)
- Reattributed the "lint (ruff) green" milestone to `0.12.1` in the `POWER.md` "What's New" section; the `0.12.0` entry no longer claims the ruff gate was green (it was still red at 0.12.0)

## [0.12.0] - 2026-05-18

### Added

- Repo-root `tests/conftest.py` that snaps cwd to the project root before every test — eliminated cross-suite cwd drift that caused 115 collection errors when running both `senzing-bootcamp/tests/` and `tests/` in a single pytest invocation
- `.example` template files for user-state configs (`bootcamp_progress.json.example`, `bootcamp_preferences.yaml.example`, `er_baseline_vendors.json.example`) — user-state files are no longer tracked in git
- Consolidated visualization steering: merged `visualization-protocol.md` and `visualization-reference.md` into `visualization-guide.md` (saves ~3,000 tokens of context budget)

### Changed

- CommonMark configuration (`.markdownlint.json`) tuned for Kiro's `#[[file:...]]` include syntax — disabled MD018/MD025/MD028/MD046 and scoped MD024 to `siblings_only`
- `sync_hook_registry.py` now wraps hook prompts in four-backtick ```` ````text ```` fences so prompts containing their own triple-backtick code blocks (e.g. `deployment-phase-gate`) render without breaking the outer fence
- `lint_steering.py` now recognizes H3-nested step headings (`### Step N:`) used by `module-03-system-verification.md` and accepts any `**Checkpoint:**` marker (not only `**Checkpoint:** Write step N`)
- `test_hook_categories_sync.py` uniqueness check rewritten to allow a single hook in multiple module sub-categories (e.g. `enforce-visualization-offers` in Modules 3, 5, 7, 8) while still enforcing no crossing of the critical/modules/any top-level boundary
- `test_hook_structural_validation.py::test_hook_file_count_matches_categories` compares against unique hook IDs rather than total list entries
- `test_hook_gaps_modules_1_and_3_properties.py::_load_modules_mapping` parses `hook-categories.yaml` directly instead of using `load_category_mapping`, which overwrites multi-module hook entries
- `test_steering_structure_properties.py` regex broadened to match `#{2,}\s+Step\s+(\d+)` headings and any `**Checkpoint:**` marker
- `CRITICAL_HOOKS` constant in `tests/hook_test_helpers.py` updated to reflect the 5 current critical hooks (removed stale `verify-senzing-facts`, `enforce-feedback-path`, `enforce-working-directory`)
- `test_hook_prompt_logic.py` — replaced `TestVerifySenzingFacts`, `TestEnforceWorkingDirectory`, and `TestEnforceFeedbackPath` classes with a single `TestEnforceFilePathPolicies` class matching the consolidated hook
- `module-03-system-verification.md` — added Step 10/11/12 checkpoint instructions, added success indicator, condensed Error Handling section to fit the 15-line lint budget, added explicit timeout declaration to Step 7
- Preservation snapshot hashes refreshed in `test_module2_license_question.py` and `test_module_closing_question_ownership.py` for edits made in the Module 3 rename pass
- Onboarding step sequence baseline updated in `test_onboarding_question_ownership.py` to include `0c. Version Display`
- `test_merge_mapping_validation_hooks.py` expected description updated to drop the obsolete Module 12 reference
- `test_cord_data_priority.py` `SYNTHESIZED_DATA_PATTERN` regex updated to match "test data can also be generated"
- `test_bootcamp_ux_feedback_unit.py` `_TEST_DATA_BULLET` fragment updated to match current CORD-first onboarding copy

### Fixed

- POWER.md `What's New (Unreleased)` bullets reorganized — items actually in 0.11.0 moved to a `What's New in 0.11.0` section; new Unreleased section summarizes the production-readiness pass
- POWER.md stale `~79 lines` claim for `agent-instructions.md` corrected to `~101 lines` (and `module-transitions.md` from `~59` to `~71`)
- `docs/guides/ARCHITECTURE.md` Critical Hooks table updated from 7 obsolete hooks (including deleted `verify-senzing-facts`, `enforce-feedback-path`, `enforce-working-directory`) to the 5 current critical hooks; Module Hooks table updated to reflect `enforce-visualization-offers` in Modules 3/5/7/8, `offer-visualization` removed from Module 7, and `module-completion-celebration` added to Any module
- `steering/onboarding-flow.md` Critical Hook failure-impact table merged `enforce-feedback-path` and `enforce-working-directory` rows into a single `enforce-file-path-policies` row
- `steering/module-03-system-verification.md` — fixed 96 `lint_steering` errors (missing checkpoints, missing success indicator, overly long Error Handling section)
- All shipped markdown files now pass `validate_commonmark.py` — fixed MD040 (missing language tags), MD028 (blank lines in blockquotes), MD056 (malformed tables) in `hook-registry.md` and `inline-status.md`
- Full test suite now at 2,603 passed / 0 failed / 0 errors / 0 collection errors (from 154 failed / 115 errors at the start of this pass)

## [0.11.0] - 2026-05-13

### Added

- AWS deployment reference steering file (`deployment-aws.md`) — dedicated guidance for ECS/Fargate, RDS, Secrets Manager, CloudWatch, IAM best practices, and cost optimization
- Skip Step Protocol (`skip-step-protocol.md`) — escape hatch for stuck bootcampers with step-level skip tracking, consequence assessment, and revisit workflow
- Module 8 phase-split into 3 phases: A (requirements/baselines), B (benchmarking), C (optimization/reporting)
- Module 9 phase-split into 2 phases: A (assessment/secrets), B (hardening/validation)
- Module 10 phase-split into 2 phases: A (monitoring setup), B (operations/validation)
- New hooks for Modules 2, 8, 9, 10: `verify-sdk-setup`, `validate-benchmark-results`, `security-scan-on-save`, `validate-alert-config`
- Integration test (`test_module_flow_integration.py`) validating multi-module state transitions across all tracks
- Enhanced `validate_module.py` checks for Modules 8–11 (benchmark environment, security utilities, monitoring utilities, runbooks, Dockerfile)
- Conversation protocol extracted to `conversation-protocol.md` (auto-included)
- Windows support improvements — Visual Studio Build Tools check in `preflight.py`, Windows-specific pitfalls section in `common-pitfalls.md`, PowerShell execution policy guidance, Windows Terminal recommendation

### Changed

- Module 3 renamed from Quick Demo to System Verification — now uses the Senzing TruthSet with MCP-generated verification code and compares results against expected TruthSet output; authoritative steering file is `module-03-system-verification.md` (replaces `module-03-quick-demo.md`); companion doc is `MODULE_3_SYSTEM_VERIFICATION.md`
- Hook consolidation — `feedback-submission-reminder` and `capture-feedback` merged into `ask-bootcamper` and `review-bootcamper-input` respectively; `enforce-feedback-path` and `enforce-working-directory` consolidated into `enforce-file-path-policies`; `verify-senzing-facts` and `offer-visualization` removed (25 hooks total)
- `hooks/README.md` regenerated to reflect the current 25-hook set
- `scripts/install_hooks.py` HOOKS list and ESSENTIAL set regenerated to match the current 25-hook set
- `deployment-phase-gate.kiro.hook` no longer references Module 12 (collapsed into Module 11)
- `steering-index.yaml` now includes full phase maps with `token_count` and `size_category` for Modules 7–10 (previously bare strings)
- `steering-index.yaml` deployment section now includes `aws` key
- `hook-categories.yaml` now includes hooks for Modules 2, 8, 9, 10
- `structure.md` steering file changed from `auto` to `always` inclusion
- `common-pitfalls.md` changed to manual inclusion
- `.gitignore` now covers `.hypothesis/` and `.pytest_cache/` directories
- Removed stale `__pycache__/`, `.hypothesis/`, `.pytest_cache/` directories from `scripts/` and `tests/`
- VERSION bumped from 0.1.0 to 0.11.0 to reconcile with CHANGELOG history

### Removed

- Deprecated `preflight_check.py` script (was a thin wrapper around `preflight.py`)
- Stale `MODULE_3_QUICK_DEMO.md` references from `docs/README.md`, `docs/modules/README.md`, `docs/guides/README.md`, and POWER.md
- Stale references to deleted hooks (`verify-senzing-facts`, `enforce-feedback-path`, `enforce-working-directory`, `offer-visualization`) from POWER.md and `scripts/install_hooks.py`
- Obsolete "Module 12" references in FAQ, `docs/guides/README.md`, and `deployment-phase-gate.kiro.hook`

## [0.10.0] - 2026-04-22

### Added in 0.10.0

- Visualization steering file (`steering/visualization-guide.md`) — guides the agent through helping bootcampers build their own interactive D3.js entity graph with detail panels, clustering, search/filter, and optional web server, in their chosen language
- Progress repair tool (`scripts/repair_progress.py`) — reconstructs `bootcamp_progress.json` from project artifacts when state is corrupted
- Steering file index (`steering/steering-index.yaml`) — machine-readable mapping of all steering files for faster agent file selection
- GitHub Actions CI workflow (`.github/workflows/validate-power.yml`) for power integrity, CommonMark validation, and test execution
- "What's New in 0.10.0" section in POWER.md for quick orientation
- Offer Entity Graph Visualization hook (`offer-visualization.kiro.hook`) — prompts visualization offer when query files are created in Module 8
- MCP offline fallback steering file (removed in 0.12.0 — MCP is now required)
- Troubleshooting commands steering file (`steering/troubleshooting-commands.md`) — extracted from troubleshooting-decision-tree.md
- Review Bootcamper Input hook (`review-bootcamper-input.kiro.hook`) — deterministic feedback capture via promptSubmit trigger with automatic context capture
- Module 11 Phase Gate hook (`deployment-phase-gate.kiro.hook`) — enforces packaging-to-deployment decision gate in Module 11
- Enforce Module 8 Visualization Offers hook (`enforce-visualization-offers.kiro.hook`) — catches missed visualization offers before Module 8 closes
- Feedback workflow rewritten with Step 0 (automatic context capture) and Step 7 (return to previous activity)
- Module 8 steering file updated with mandatory ⛔ WAIT blocks for both visualization offers
- Module 11 steering file updated with prominent ⛔ PHASE GATE section between packaging and deployment

### Changed in 0.10.0

- FAQ feedback section updated with direct link to feedback template file
- Module 8 steering file updated with visualization steering file reference (replaces script approach)
- Hooks README updated with entry #14 for offer-visualization hook
- `#[[file:]]` references added to module-04, module-05, and module-08 steering files for template access
- Multi-language project note added to agent-instructions.md
- PowerShell directory creation command added to project-structure.md
- common-pitfalls.md reduced from 312 to 212 lines (MCP section extracted)
- troubleshooting-decision-tree.md reduced from 299 to 224 lines (commands section extracted)

## [0.9.0] - 2026-04-21

### Added in 0.9.0

- Module 7 steering file expanded from ~100 to 323 lines with 12-step orchestration workflow, source ordering heuristics, conflict resolution guidance, error handling, and troubleshooting
- MCP failure recovery section in `common-pitfalls.md` with blocked/continuable operation tables, per-operation fallback instructions, reconnection procedures, and connectivity troubleshooting
- Module 2 license step completed with license priority order, `SENZING_LICENSE_PATH` discovery, acquisition contacts, and `licenses/README.md` reference
- Data collection checklist template at `templates/data_collection_checklist.md` with 9-column inventory table and validation checklist
- Quality scoring methodology guide at `docs/guides/QUALITY_SCORING_METHODOLOGY.md` with weighted formula, threshold bands, and worked examples
- Quick navigation with anchor links in `common-pitfalls.md` for module-specific troubleshooting
- Language steering files expanded from ~10 to ~55 lines each with SDK best practices, common pitfalls, performance considerations, code style, and platform notes
- Stakeholder summary template at `templates/stakeholder_summary.md` with module-aware placeholder guidance for Modules 1, 8, and 12
- Performance baselines guide at `docs/guides/PERFORMANCE_BASELINES.md` with throughput tables, hardware requirements, SQLite vs PostgreSQL comparison, and profiling tools
- UAT test case template at `templates/uat_test_cases.md` with functional, performance, and data quality test sections
- Module 11 deployment expanded with on-premises, Azure, GCP, and Kubernetes platform reference sections
- Offline mode guide (removed in 0.12.0 — MCP is now required)
- Transformation lineage template at `templates/transformation_lineage.md` with field mappings, format changes, filters, and quality improvements
- Integration patterns section in Module 8 steering file with 6 patterns (batch report, REST API, streaming, database sync, duplicate detection, watchlist screening)
- Disaster recovery subsection in Module 11 Step 15 with RTO/RPO, 3-2-1 backup rule, DR scenarios, and backup scripts
- Concrete SQLite pragma and PostgreSQL config snippets in performance baselines guide
- Profiling and monitoring section in performance baselines guide with bottleneck patterns and language-specific tools
- Common mistakes guide at `docs/guides/COMMON_MISTAKES.md`
- Getting help guide at `docs/guides/GETTING_HELP.md`
- Lessons learned template at `templates/lessons_learned.md`
- Module prerequisites Mermaid diagram in `docs/diagrams/module-prerequisites.md`

### Changed in 0.9.0

- `module-transitions.md` changed from `inclusion: auto` to `inclusion: fileMatch` on `config/bootcamp_progress.json` — reduces context waste on non-module-boundary interactions
- `agent-instructions.md` updated to note `module-transitions.md` is conditionally loaded
- Module 3 visualization offer promoted to its own numbered step (Step 5) before module close
- Module 3 completion Explore option now mentions visualization and interactive features
- Module 5 quality thresholds aligned to ≥80%/70-79%/<70% bands
- `data-lineage.md` steering file expanded with lineage file structure, example entries, tracker utility, and compliance guidance
- `COLLABORATION_GUIDE.md` expanded with bootcamp-specific collaboration examples
- Cross-references added between related guides (quality scoring ↔ performance baselines ↔ offline mode)
- Template references added to module docs (Module 4, 5, 8)
- POWER.md updated with references to new guides, templates, and offline mode
- Module 11 split into main workflow (296 lines) + 4 separate platform steering files (`deployment-onpremises.md`, `deployment-azure.md`, `deployment-gcp.md`, `deployment-kubernetes.md`) per Kiro steering best practices
- Module 7 split into main workflow (205 lines) + `load-data-reference.md` (130 lines) for ordering examples, conflict resolution, and troubleshooting
- Module 2 Step 5 (license) condensed from ~80 to ~20 prescriptive lines
- Generic language standards removed from all 5 language steering files — kept only Senzing SDK-specific content
- `agent-instructions.md` updated with Module 11 platform file references and Module 7 reference guidance
- POWER.md Advanced Topics section updated with 5 new steering file references
- Repository organization steering file simplified after development directory removal
- `docs/development.md` simplified after development directory removal
- `MODULE_8_QUERY_VALIDATION.md` fixed `uat_test_cases.yaml` → `uat_test_cases.md` references

### Removed in 0.9.0

- `senzing-bootcamp-power-development/` directory — historical development archive removed; useful content incorporated into distributed power
- `powers/git-best-practices/` — unrelated generic power removed

## Earlier Versions

See [CHANGELOG-ARCHIVE.md](CHANGELOG-ARCHIVE.md) for releases prior to 0.9.0.
