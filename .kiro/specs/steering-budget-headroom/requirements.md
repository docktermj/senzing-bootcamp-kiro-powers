# Requirements Document

## Introduction

The senzing-bootcamp steering corpus has a measured `budget.total_tokens` of 177,398 against a 200,000-token `reference_window`. With `warn_threshold_pct: 60` (120k) and `critical_threshold_pct: 80` (160k), the full corpus already exceeds both thresholds. Sessions stay safe today only because steering files use on-demand (manual) loading rather than always being resident. As releases have added content, the largest reference-style files have grown to the point where loading any one of them to answer a narrow question dominates the worst-case loaded footprint.

The largest single consumers are the hook registries and the module-completion workflow:

- `hook-registry-modules.md` — 10,631 tokens (full module-hook prompts)
- `hook-registry-critical.md` — 8,503 tokens (full critical-hook prompts)
- `hook-registry.md` — 1,772 tokens (summary tables)
- `module-completion.md` — 6,076 tokens (module-completion workflow prose)

When the agent needs the hooks for the current module, it must load the entire `hook-registry-modules.md` (10,631 tokens) even though it needs only one module's slice. When the agent needs completion guidance for a single concern (recap, journal, certificate, or track completion), it must load the entire `module-completion.md` (6,076 tokens). The hook-registry files are generated deterministically by `sync_hook_registry.py` from the machine-readable sources `hooks/*.kiro.hook` and `hooks/hook-categories.yaml`, and CI verifies them with `sync_hook_registry.py --verify`.

This feature reduces the **worst-case loaded steering footprint** by making the largest reference-style steering files load only the slice relevant to the current context (the current module's hooks, or the current completion concern) instead of loading an entire monolithic registry as a single unit. All information currently available to the agent is preserved and remains reachable — it is simply no longer loaded all at once. The change is distinct from the `module-router-standardization` spec, which standardizes module workflow root-versus-phase splits; this feature targets context-budget footprint reduction for large reference-style steering files.

## Glossary

- **Steering_Corpus**: All `*.md` files under `senzing-bootcamp/steering/`.
- **Steering_Index**: The `senzing-bootcamp/steering/steering-index.yaml` file, which holds `keywords`, `file_metadata`, the module/onboarding/session-resume maps, and the `budget` section.
- **Split_Threshold**: The `budget.split_threshold_tokens` value in Steering_Index, currently 5,000 tokens — the per-file size above which a steering file is considered too large to load as a single unit.
- **Worst_Case_Loaded_Footprint**: The maximum number of steering tokens the agent must load to answer a single context-relevant query (for example, the hooks for one module, or one module-completion concern).
- **In_Scope_Files**: `hook-registry.md`, `hook-registry-critical.md`, `hook-registry-modules.md`, and `module-completion.md`.
- **Hook_Registry_Summary**: The `hook-registry.md` file — the lightweight, routable summary of all hooks.
- **Hook_Registry_Module_Slice**: A generated per-module steering file containing the full prompt text only for the module hooks associated with one module (or the "any" module group).
- **Hook_Registry_Critical**: The `hook-registry-critical.md` file — full prompt text for the critical hooks created during onboarding.
- **Hook_Registry_Generator**: The `senzing-bootcamp/scripts/sync_hook_registry.py` script that generates and verifies the hook registry steering files.
- **Hook_Categories_Source**: The `senzing-bootcamp/hooks/hook-categories.yaml` file mapping each hook to its category (critical) or module number(s).
- **Hook_Source_Files**: The `senzing-bootcamp/hooks/*.kiro.hook` JSON files, the single source of truth for hook definitions and prompt text.
- **Module_Completion_Root**: The post-refactor `module-completion.md` file — a lightweight router containing the completion-step ordering overview and a manifest of completion slices.
- **Module_Completion_Slice**: A steering file containing one cohesive portion of the module-completion workflow (for example, artifact generation, error handling, or track completion).
- **Steering_Measurement_Tool**: The `senzing-bootcamp/scripts/measure_steering.py` script, whose `--check` mode validates stored token counts and the budget total against measured values.
- **CommonMark_Validator**: The `senzing-bootcamp/scripts/validate_commonmark.py` script run in CI.
- **CI_Pipeline**: The `.github/workflows/validate-power.yml` GitHub Actions workflow.

## Requirements

### Requirement 1: Scope and footprint-reduction target

**User Story:** As a power maintainer, I want a defined set of in-scope steering files and an explicit footprint-reduction target, so that the refactor has a clear, measurable boundary.

#### Acceptance Criteria

1. THE Steering_Corpus SHALL treat `hook-registry.md`, `hook-registry-critical.md`, `hook-registry-modules.md`, and `module-completion.md` as the In_Scope_Files for this feature.
2. WHEN the agent loads the module-hook prompt content for the single module whose hooks occupy the most tokens, THE Worst_Case_Loaded_Footprint for that load SHALL be at most the Split_Threshold of 5,000 tokens.
3. WHEN the agent loads the completion guidance for a single module-completion concern, THE Worst_Case_Loaded_Footprint for that load SHALL be at most the Split_Threshold of 5,000 tokens.
4. WHEN the agent loads the module-hook prompt content for any single module, THE Worst_Case_Loaded_Footprint for that load SHALL be at most 50 percent of the pre-refactor `hook-registry-modules.md` token count of 10,631 tokens.
5. THE Steering_Corpus SHALL preserve the total set of hook prompts and module-completion guidance such that the post-refactor `budget.total_tokens` reflects no removed guidance content.

### Requirement 2: Per-module hook slices

**User Story:** As the bootcamp agent, I want each module's hook prompts available as a small per-module file, so that I load only the current module's hooks instead of every module's hooks.

#### Acceptance Criteria

1. THE Hook_Registry_Generator SHALL emit one Hook_Registry_Module_Slice for each module number that has module hooks in the Hook_Categories_Source.
2. THE Hook_Registry_Generator SHALL emit one Hook_Registry_Module_Slice for the "any" module group.
3. WHERE a hook is associated with multiple modules in the Hook_Categories_Source, THE Hook_Registry_Generator SHALL include that hook's full prompt in the Hook_Registry_Module_Slice for each associated module.
4. THE Hook_Registry_Generator SHALL produce each Hook_Registry_Module_Slice with a token count at or below the Split_Threshold of 5,000 tokens.
5. THE Hook_Registry_Generator SHALL name each Hook_Registry_Module_Slice in kebab-case with a zero-padded two-digit module number for numbered modules and a distinct name for the "any" group.
6. THE Hook_Registry_Generator SHALL render every Hook_Registry_Module_Slice deterministically, producing byte-identical output for unchanged Hook_Source_Files and Hook_Categories_Source.

### Requirement 3: Information preservation and reachability

**User Story:** As a power maintainer, I want all hook and completion guidance to remain reachable after slicing, so that no instruction the agent relies on is lost.

#### Acceptance Criteria

1. THE Steering_Corpus SHALL make the full prompt text of every hook in the Hook_Source_Files reachable through Hook_Registry_Critical, a Hook_Registry_Module_Slice, or both (inclusive-or), so that a hook associated with multiple modules MAY appear in more than one slice.
2. THE union of hook IDs across Hook_Registry_Critical and all Hook_Registry_Module_Slices SHALL equal the set of hook IDs in the Hook_Source_Files.
3. THE Steering_Corpus SHALL make every section of the pre-refactor `module-completion.md` reachable through the Module_Completion_Root or a Module_Completion_Slice.
4. THE Hook_Registry_Summary SHALL list every hook by ID, event flow, module label, and one-line description.
5. IF a hook prompt or completion section would be removed by the refactor, THEN THE Steering_Corpus SHALL retain that content in another In_Scope_File or its replacement slice.

### Requirement 4: Module-completion slicing

**User Story:** As the bootcamp agent, I want module-completion guidance organized into a lightweight root plus cohesive slices, so that I load only the concern relevant to the current completion step.

#### Acceptance Criteria

1. THE Module_Completion_Root SHALL contain the completion-step ordering overview and a manifest that names each Module_Completion_Slice and its purpose.
2. THE Module_Completion_Root SHALL have a token count at or below the Split_Threshold of 5,000 tokens.
3. THE Steering_Corpus SHALL provide each Module_Completion_Slice with a token count at or below the Split_Threshold of 5,000 tokens.
4. THE Steering_Corpus SHALL organize Module_Completion_Slices by cohesive concern so that artifact generation, non-blocking error handling, and track-completion guidance are each loadable independently.
5. WHEN the agent needs guidance for a single completion concern, THE Module_Completion_Root SHALL identify the single Module_Completion_Slice that supplies that guidance.

### Requirement 5: Steering-index routing accuracy

**User Story:** As the bootcamp agent, I want the steering index to route narrow queries to the correct slice, so that the right slice loads for "hook", "completion", per-module hook questions, and per-concern completion questions.

#### Acceptance Criteria

1. THE Steering_Index SHALL route the `hook` and `hooks` keywords to the Hook_Registry_Summary.
2. THE Hook_Registry_Summary SHALL instruct the agent to resolve the current module from `config/bootcamp_progress.json` and load the matching Hook_Registry_Module_Slice for per-module hook prompts.
3. THE Steering_Index SHALL route the `completion` keyword to the Module_Completion_Root.
4. THE Steering_Index SHALL provide keyword routes that resolve completion-concern queries to the corresponding Module_Completion_Slice.
5. THE Steering_Index `file_metadata` section SHALL contain an entry for each Hook_Registry_Module_Slice, the Module_Completion_Root, and each Module_Completion_Slice, with a `token_count` within 10 percent of the measured count and a matching `size_category`.
6. WHERE a keyword route names a steering file, THE Steering_Index SHALL reference a file that exists in the Steering_Corpus.

### Requirement 6: Generator and CI synchronization

**User Story:** As a power maintainer, I want the generator and CI to keep the sliced registry consistent with the hook source files, so that drift is caught automatically.

#### Acceptance Criteria

1. THE Hook_Registry_Generator SHALL derive all Hook_Registry_Module_Slice content from the Hook_Source_Files and the Hook_Categories_Source rather than from hand-authored prose.
2. WHEN invoked with `--write`, THE Hook_Registry_Generator SHALL write the Hook_Registry_Summary, Hook_Registry_Critical, and every Hook_Registry_Module_Slice to the Steering_Corpus.
3. WHEN invoked with `--verify`, THE Hook_Registry_Generator SHALL exit with code 0 only if every generated registry file on disk is byte-identical to its freshly generated content.
4. IF any generated registry file is missing or differs from its freshly generated content, THEN THE Hook_Registry_Generator SHALL exit with a non-zero code under `--verify` and report which file differs.
5. WHILE every generated registry file on disk is byte-identical to its freshly generated content, THE Hook_Registry_Generator SHALL report no file as differing under `--verify`.
6. IF a write operation fails under `--write` due to a file-system or permission error, THEN THE Hook_Registry_Generator SHALL exit with a non-zero code.
7. THE CI_Pipeline SHALL pass the `sync_hook_registry.py --verify` step after the refactor.

### Requirement 7: Budget and measurement consistency

**User Story:** As a power maintainer, I want the steering index budget and metadata to stay accurate, so that `measure_steering.py --check` remains green in CI.

#### Acceptance Criteria

1. THE Steering_Index `budget.total_tokens` SHALL equal the sum of the `token_count` values across all `file_metadata` entries.
2. THE Steering_Index SHALL retain `reference_window: 200000`, `warn_threshold_pct: 60`, `critical_threshold_pct: 80`, and `split_threshold_tokens: 5000` in the `budget` section.
3. WHEN `measure_steering.py --check` runs against the refactored Steering_Corpus, THE Steering_Measurement_Tool SHALL exit with code 0.
4. THE Steering_Index `file_metadata` SHALL contain no entry for a steering file that no longer exists in the Steering_Corpus.
5. THE Steering_Corpus SHALL achieve the Worst_Case_Loaded_Footprint reductions in Requirement 1 without depending on a reduction in `budget.total_tokens`.

### Requirement 8: Steering file conformance

**User Story:** As a power maintainer, I want every new or modified steering file to follow power conventions, so that the distributed power stays valid and safe.

#### Acceptance Criteria

1. THE Steering_Corpus SHALL name every Hook_Registry_Module_Slice and Module_Completion_Slice in kebab-case with a `.md` extension.
2. THE Steering_Corpus SHALL begin every Hook_Registry_Module_Slice, Module_Completion_Root, and Module_Completion_Slice with YAML frontmatter declaring `inclusion: manual`.
3. WHEN the CI_Pipeline runs the CommonMark_Validator against the refactored Steering_Corpus, THE CommonMark_Validator SHALL run to completion and report no violations.
4. THE Steering_Corpus SHALL contain no external `http://` or `https://` URL in any Hook_Registry_Module_Slice, Module_Completion_Root, or Module_Completion_Slice.
5. THE Steering_Corpus SHALL place all new steering files under `senzing-bootcamp/steering/` so they ship with the power.

### Requirement 9: Tooling conventions

**User Story:** As a power maintainer, I want generator changes to follow the project's Python conventions, so that the tooling stays dependency-free and consistent.

#### Acceptance Criteria

1. THE Hook_Registry_Generator SHALL use only the Python standard library.
2. THE Hook_Registry_Generator SHALL parse the Hook_Categories_Source using the existing minimal in-script YAML parsing approach rather than introducing a third-party YAML dependency.
3. THE Hook_Registry_Generator SHALL run under Python 3.11, 3.12, and 3.13 as exercised by the CI_Pipeline matrix.
4. IF the Hook_Registry_Generator encounters any internal error during generation, verification, or writing, THEN THE Hook_Registry_Generator SHALL exit with a non-zero code regardless of how far the operation progressed.

### Requirement 10: Missing-slice fallback

**User Story:** As the bootcamp agent, I want a defined fallback when a slice is unavailable, so that I can still reach hook or completion guidance without failing.

#### Acceptance Criteria

1. IF the Hook_Registry_Module_Slice for the current module cannot be found at its expected path, THEN THE agent SHALL fall back to the Hook_Registry_Summary and report that the per-module slice is missing.
2. IF a referenced Module_Completion_Slice cannot be found at its expected path, THEN THE agent SHALL fall back to the Module_Completion_Root and report that the slice is missing.
3. WHERE a module has no module hooks in the Hook_Categories_Source, THE Hook_Registry_Generator SHALL omit a Hook_Registry_Module_Slice for that module rather than emitting an empty file.
