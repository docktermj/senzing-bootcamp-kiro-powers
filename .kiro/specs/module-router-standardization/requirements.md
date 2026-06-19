# Requirements Document

## Introduction

The `senzing-bootcamp` Kiro Power splits large module steering files into phase-level
sub-files to keep the agent's loaded context within budget. Each phase-split module also
keeps a "root" steering file. The intended role of that root is to act as a thin
**router**: a navigation and overview entry point that the agent loads first, which then
points to the correct phase file for the bootcamper's current step.

Today this convention is applied inconsistently. Some roots are already thin routers
(for example, `module-05-data-quality-mapping.md` at 689 tokens, `module-09-security.md`
at 571, `module-10-monitoring.md` at 568), while others still carry substantial workflow
content alongside their phase files (for example, `module-06-data-processing.md` at 1583,
`module-03-system-verification.md` at 1448, `module-08-performance.md` at 1359). A third
group uses the root file as both the router and the first phase
(`module-01-business-problem.md` at 5321, `module-07-query-visualize-discover.md` at 3591,
`module-11-deployment.md` at 3289, where the root doubles as `phase1-packaging`).

Because the convention is inconsistent, the worst-case loaded footprint of a module is
unpredictable and the loading rules in `phase-loading-guide.md` are harder to reason
about. This feature defines a single, precise convention for what a thin router root must
contain, establishes a measurable token ceiling that distinguishes a router from a content
file, specifies the target end-state for every phase-split module, keeps `steering-index.yaml`
and `phase-loading-guide.md` accurate, and adds automated enforcement (via the existing
stdlib-only steering scripts) so future module roots cannot regress into content files.
All existing workflow guidance is preserved — content moves from a root into phase files
rather than being deleted.

## Glossary

- **Phase_Split_Module**: A bootcamp module whose steering content is divided across two
  or more phase sub-files, as recorded by a `root` plus `phases` map under that module's
  entry in `steering-index.yaml`.
- **Router_Root**: The single root steering file for a Phase_Split_Module that serves as
  the navigation and overview entry point. The agent loads the Router_Root first when
  entering the module.
- **Phase_File**: A steering sub-file that contains the substantive numbered workflow
  steps for one phase of a Phase_Split_Module, referenced by a `file:` entry under that
  module's `phases` map.
- **Router_Ceiling**: The maximum approximate token count permitted for a Router_Root,
  recorded as a configuration value in `steering-index.yaml`. A root at or below the
  Router_Ceiling is treated as a router; a root above it is treated as a content file.
- **Router_Content_Set**: The defined set of element types a Router_Root is permitted to
  contain (overview, prerequisites, navigation manifest, and similar pointers).
- **Steering_Index**: The `steering-index.yaml` file, which records the module → root →
  phases structure plus per-file `token_count` and `size_category` metadata and the
  `budget` block.
- **Steering_Measurer**: The `measure_steering.py` script, which computes approximate
  token counts (`round(len(content) / 4)`), classifies `size_category`, updates
  Steering_Index, and validates stored counts in `--check` mode.
- **Steering_Linter**: The `lint_steering.py` script, which checks steering files and the
  Steering_Index for structural consistency and emits ERROR/WARNING violations.
- **Phase_Loading_Guide**: The `phase-loading-guide.md` steering file, which governs how
  the agent selects and loads the root and phase files on demand.
- **Phase_Manifest**: The section of a Router_Root that lists each phase, its step range,
  and its Phase_File path (for example, the "Phase Sub-Files" list in
  `module-05-data-quality-mapping.md`).
- **Token_Count**: The approximate token measure used throughout the power, defined as
  `round(len(content) / 4)` over a file's full UTF-8 content.

## Requirements

### Requirement 1: Define the thin router root convention

**User Story:** As a power maintainer, I want a precise definition of what a thin router
root must and must not contain, so that every phase-split module's root has a consistent,
predictable role and footprint.

#### Acceptance Criteria

1. THE Router_Standardization_Convention SHALL define the Router_Content_Set as the only
   element types permitted in a Router_Root: YAML frontmatter, the module title heading,
   the sequential-execution rule banner, the module-start banner instruction, user-reference
   and companion-doc pointers, the before/after framing, the prerequisites statement, the
   success indicator, the error-handling pointer block, and the Phase_Manifest.
2. THE Router_Standardization_Convention SHALL require that every Router_Root contains a
   Phase_Manifest listing each phase of the module with the phase name, the step range,
   and the Phase_File path.
3. THE Router_Standardization_Convention SHALL require that all substantive numbered
   workflow steps for a Phase_Split_Module reside in Phase_Files and not in the
   Router_Root.
4. WHERE a Router_Root would otherwise contain a substantive workflow section (numbered
   steps, conditional workflow logic, pre-load procedures, or advanced-reading
   instructions), THE Router_Standardization_Convention SHALL require that section to be
   relocated into the appropriate Phase_File.
5. THE Router_Standardization_Convention SHALL define a Router_Ceiling token value and
   SHALL record the Router_Ceiling in the `budget` section of the Steering_Index.
6. THE Router_Standardization_Convention SHALL set the default Router_Ceiling to 1000
   tokens, a value that classifies the existing thin routers
   (`module-05-data-quality-mapping.md` at 689, `module-09-security.md` at 571,
   `module-10-monitoring.md` at 568) as routers and the existing substantial roots
   (`module-06-data-processing.md` at 1583, `module-03-system-verification.md` at 1448,
   `module-08-performance.md` at 1359) as content files requiring remediation.

### Requirement 2: Specify in-scope modules and target end-state

**User Story:** As a power maintainer, I want the modules in scope and each root's target
end-state enumerated, so that the standardization work is unambiguous and verifiable.

#### Acceptance Criteria

1. THE Router_Standardization_Convention SHALL apply to every Phase_Split_Module recorded
   in the Steering_Index — the modules whose entry has a `root` plus a `phases` map.
2. WHERE a module's Steering_Index entry has no `phases` map or has a single phase whose
   `file` equals the `root`, THE Router_Standardization_Convention SHALL exclude that
   module from the router-remediation scope.
3. THE Router_Standardization_Convention SHALL classify each in-scope Router_Root into one
   of two end-states: "compliant router" (Token_Count at or below the Router_Ceiling and
   contents limited to the Router_Content_Set) or "requires remediation" (Token_Count
   above the Router_Ceiling or contents outside the Router_Content_Set).
4. WHERE an in-scope Router_Root is in the "requires remediation" end-state because it
   exceeds the Router_Ceiling, THE Router_Standardization_Convention SHALL require its
   substantive content to be relocated into Phase_Files until the Router_Root is at or
   below the Router_Ceiling.
5. WHERE a Phase_Split_Module uses its `root` file as both the Router_Root and a
   Phase_File (the root-doubles-as-phase pattern, as in `module-01-business-problem.md`,
   `module-07-query-visualize-discover.md`, and `module-11-deployment.md`), THE
   Router_Standardization_Convention SHALL require a dedicated Router_Root file distinct
   from every Phase_File, with the former root content moved into a separately named
   Phase_File.
6. THE Router_Standardization_Convention SHALL define the target end-state for each
   in-scope module as a compliant router and SHALL record the per-module target in the
   design document.

### Requirement 3: Preserve all workflow content and step coverage

**User Story:** As a bootcamper, I want every existing step and piece of guidance to
remain available after standardization, so that no learning content is lost when roots are
thinned.

#### Acceptance Criteria

1. WHEN content is moved out of a Router_Root, THE Router_Standardization_Convention SHALL
   require that content to be added to a Phase_File rather than deleted.
2. THE Router_Standardization_Convention SHALL require that the union of step numbers
   covered by a module's Phase_Files after remediation equals the set of step numbers
   covered before remediation.
3. THE Router_Standardization_Convention SHALL require that every phase `step_range`
   recorded in the Steering_Index remains contiguous and non-overlapping across a module's
   phases after remediation.
4. IF relocating content would leave a step number uncovered by any Phase_File, THEN THE
   Router_Standardization_Convention SHALL require the relocation to be revised so that the
   step remains covered.
5. WHEN a Router_Root is remediated, THE Router_Standardization_Convention SHALL require
   the Phase_Manifest to reference every Phase_File that exists for that module.

### Requirement 4: Keep the steering index accurate

**User Story:** As a power maintainer, I want `steering-index.yaml` to reflect the true
token counts and structure after standardization, so that loading decisions and budget
reporting stay correct.

#### Acceptance Criteria

1. WHEN a Router_Root or Phase_File is added, removed, or has its content changed, THE
   Steering_Measurer SHALL update the affected `token_count` and `size_category` values in
   the Steering_Index to within 10 percent of the measured Token_Count.
2. THE Steering_Index SHALL contain a `file_metadata` entry with a `token_count` and a
   `size_category` for every steering `.md` file on disk after standardization.
3. THE Steering_Index SHALL record, for every in-scope module, a `root` filename distinct
   from each `file` listed under that module's `phases` map.
4. WHEN the Steering_Measurer runs in `--check` mode, THE Steering_Measurer SHALL exit with
   a non-zero status IF any stored root or phase `token_count` differs from the measured
   Token_Count by more than 10 percent.
5. THE Steering_Index `budget` section SHALL retain its existing keys (`total_tokens`,
   `reference_window`, `warn_threshold_pct`, `critical_threshold_pct`,
   `split_threshold_tokens`) in addition to the Router_Ceiling value.

### Requirement 5: Preserve and clarify phase-loading behavior

**User Story:** As a power maintainer, I want the phase-loading rules to remain correct and
clearly state the router's role, so that the agent loads the right files after roots are
standardized.

#### Acceptance Criteria

1. THE Router_Standardization_Convention SHALL preserve the existing Phase_Loading_Guide
   behavior in which the agent loads the Router_Root first, resolves the current phase from
   `current_step`, and then loads only the matching Phase_File.
2. THE Phase_Loading_Guide SHALL state that the Router_Root provides navigation and
   overview content and that substantive workflow steps reside in Phase_Files.
3. WHERE a module is converted from the root-doubles-as-phase pattern to a dedicated
   Router_Root, THE Phase_Loading_Guide SHALL describe phase resolution for that module
   using the new Router_Root and Phase_File names.
4. IF the current step resolves outside every phase `step_range`, THEN the
   Phase_Loading_Guide SHALL retain the existing fallback of loading the Router_Root only.

### Requirement 6: Provide automated enforcement of the convention

**User Story:** As a power maintainer, I want an automated check that flags any module root
that exceeds the ceiling or carries workflow content, so that future roots cannot regress
into content files.

#### Acceptance Criteria

1. THE Steering_Linter SHALL identify each Router_Root from the Steering_Index as the
   `root` file of a module that also has a `phases` map with a Phase_File distinct from the
   root.
2. IF a Router_Root has a Token_Count above the Router_Ceiling, THEN THE Steering_Linter
   SHALL emit a violation naming the Router_Root, its Token_Count, and the Router_Ceiling.
3. IF an in-scope module's `root` filename equals one of its Phase_File filenames, THEN THE
   Steering_Linter SHALL emit a violation indicating the root-doubles-as-phase pattern.
4. THE enforcement check SHALL be implemented in Python 3.11+ using only the standard
   library (PyYAML permitted only where YAML is already parsed with it), consistent with
   the existing steering scripts.
5. WHEN no Router_Root violates the convention AND the runtime is Python 3.11 or later
   with all required standard-library modules available, THE Steering_Linter SHALL complete
   without emitting a router-related violation and exit with a zero status.
6. IF the runtime is earlier than Python 3.11 or a required standard-library module is
   unavailable, THEN THE Steering_Linter SHALL report the environment error and exit with a
   non-zero status rather than reporting success.
7. THE enforcement check SHALL run as part of the `validate-power.yml` CI workflow so that
   a regressing Router_Root fails the pull-request checks.

### Requirement 7: Maintain power distribution and formatting constraints

**User Story:** As a power maintainer, I want all standardized steering files to satisfy
the power's distribution and formatting rules, so that the shipped power stays valid and
safe.

#### Acceptance Criteria

1. THE Router_Standardization_Convention SHALL require every Router_Root and Phase_File to
   be a kebab-case `.md` file with valid YAML frontmatter.
2. THE Router_Standardization_Convention SHALL require every Router_Root and Phase_File to
   remain CommonMark-compliant as validated by `validate_commonmark.py`.
3. THE Router_Standardization_Convention SHALL require that no Router_Root or Phase_File
   contains an external URL, consistent with the steering security rule.
4. WHERE a new dedicated Router_Root or renamed Phase_File is created, THE
   Router_Standardization_Convention SHALL require all `#[[file:]]` and backtick filename
   references to the changed files to be updated so that no orphaned reference remains.
5. THE Router_Standardization_Convention SHALL require all files created or renamed under
   standardization to reside in `senzing-bootcamp/steering/`, since everything under
   `senzing-bootcamp/` ships to users.
