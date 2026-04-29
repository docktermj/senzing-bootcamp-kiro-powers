# Tasks

## Task 1: Create the `split_steering.py` script with core parsing and splitting logic

- [x] 1.1 Create `senzing-bootcamp/scripts/split_steering.py` with `Phase` and `SplitResult` dataclasses, and implement `parse_phases(content)` that extracts YAML front matter, preamble (everything before the first `## Phase` heading), and a list of `Phase` objects (name, slug, content, step_start, step_end) by parsing `## Phase` headings and checkpoint step numbers from the markdown
- [x] 1.2 Implement `build_root_file(front_matter, preamble, phases, sub_file_paths)` that produces a root file containing the YAML front matter, the preamble text, and a manifest section listing each phase name with its sub-file path
- [x] 1.3 Implement `build_sub_file(front_matter, phase)` that produces a sub-file containing YAML front matter (`inclusion: manual`) followed by the complete phase content
- [x] 1.4 Implement `split_module(module_path, output_dir, sub_file_names)` that reads the original module file, calls `parse_phases`, writes the root file (at the original filename) and each sub-file, calculates token counts (`round(len(content)/4)`), and returns a `SplitResult`
- [x] 1.5 Implement `update_steering_index(index_path, module_number, split_result)` that reads `steering-index.yaml`, replaces the module's simple string entry with the `root` + `phases` map (including `file`, `token_count`, `size_category`, `step_range` per phase), updates `file_metadata` with root and sub-file entries (removing any stale monolithic entry if different from root), and recalculates `budget.total_tokens` as the sum of all `file_metadata` token counts

## Task 2: Add `split_threshold_tokens` support and CLI entry point

- [x] 2.1 Add a `split_threshold_tokens` field (value: `5000`) to the `budget` section of `steering-index.yaml` and implement a `get_split_candidates(index_path)` function in `split_steering.py` that reads the index and returns filenames whose `token_count` exceeds the threshold
  _Requirements: 5.1, 5.2, 5.3_
- [x] 2.2 Add a `__main__` CLI entry point to `split_steering.py` that accepts `--module` (module number), `--steering-dir`, and `--index-path` arguments, runs the split for the specified module, and prints a summary of files created and token counts

## Task 3: Split Module 5 into phase-level sub-files

- [x] 3.1 Run `split_steering.py` (or call `split_module` directly) on `module-05-data-quality-mapping.md` to produce the root file and three sub-files: `module-05-phase1-quality-assessment.md`, `module-05-phase2-data-mapping.md`, `module-05-phase3-test-load.md`
  _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_
- [x] 3.2 Verify the root file contains only preamble (title, purpose, prerequisites, before/after, quality scoring reference) and manifest, retains `inclusion: manual` front matter, and that each sub-file contains its complete phase content with `inclusion: manual` front matter
- [x] 3.3 Verify the combined content of root + sub-files preserves all content from the original file with no omissions or additions

## Task 4: Split Module 6 into phase-level sub-files

- [x] 4.1 Run `split_steering.py` on `module-06-load-data.md` to produce the root file and four sub-files: `module-06-phaseA-build-loading.md`, `module-06-phaseB-load-first-source.md`, `module-06-phaseC-multi-source.md`, `module-06-phaseD-validation.md` (with shared reference/recovery content appended to the appropriate sub-file)
  _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
- [x] 4.2 Verify the root file contains only preamble (title, purpose, prerequisites, before/after, conditional workflow check) and manifest, and that each sub-file contains its complete phase content
- [x] 4.3 Verify the combined content of root + sub-files preserves all content from the original file with no omissions or additions

## Task 5: Update `steering-index.yaml` with sub-file metadata

- [x] 5.1 Run `update_steering_index` for both Module 5 and Module 6, producing the expanded `root` + `phases` map format under `modules.5` and `modules.6`, with `file`, `token_count`, `size_category`, and `step_range` per phase
  _Requirements: 3.1_
- [x] 5.2 Verify `file_metadata` contains entries for both root files and all seven sub-files with accurate `token_count` and `size_category` values, and that the original monolithic entries are replaced
  _Requirements: 3.2, 3.3_
- [x] 5.3 Verify `budget.total_tokens` equals the sum of all `file_metadata` token counts after the update
  _Requirements: 3.4_
- [x] 5.4 Run `measure_steering.py --check` and confirm it passes (no mismatches >10%)

## Task 6: Update `agent-instructions.md` for phase-level loading

- [x] 6.1 Update the "Module Steering" section in `agent-instructions.md` to document phase-level loading: when entering a split module, load the root file first; determine the current phase from `bootcamp_progress.json` `current_step` using `step_ranges` in `steering-index.yaml`; load only the sub-file for that phase; on phase transition, unload the previous sub-file before loading the next; if a sub-file is missing, fall back to the root file and log a warning
  _Requirements: 4.1, 4.2, 4.3, 4.4, 6.3_
- [x] 6.2 Update the "Context Budget" section in `agent-instructions.md` to reference the `steering-index.yaml` `phases` metadata as the source for phase-level token costs, noting that the root file token count is always loaded and the phase sub-file token count is additive
  _Requirements: 4.5_
- [x] 6.3 Verify that existing cross-references to `module-05-data-quality-mapping.md` and `module-06-load-data.md` in other steering files still resolve correctly (root files remain at original paths)
  _Requirements: 6.1_

## Task 7: Update session resume for phase-aware loading

- [x] 7.1 Verify that `session-resume.md` Step 4 logic is compatible with the new phase-level loading: when `current_step` is present for a split module, the agent should check `steering-index.yaml` for a `phases` entry and load only the corresponding sub-file. Add a note to `agent-instructions.md` if needed to clarify this behavior
  _Requirements: 6.2_

## Task 8: Property-based tests (Hypothesis)

- [x] 8.1 Create `senzing-bootcamp/tests/test_split_steering.py` with Hypothesis strategies for generating random module content (preamble text + 1–5 phases with random content, step numbers, and YAML front matter)
- [x] 8.2 PBT: Property 1 — Content Preservation Round-Trip: for any valid module content with phase headings, splitting into root + sub-files and recombining preserves every line of instructional content with no omissions or additions (Req 1.6, 2.6)
- [x] 8.3 PBT: Property 2 — Sub-File YAML Front Matter Invariant: for any sub-file produced by the splitting script, the content begins with YAML front matter containing `inclusion: manual` (Req 1.5, 2.5)
- [x] 8.4 PBT: Property 3 — Steering Index Metadata Consistency: for any split module, the steering index contains a `phases` map with entries for each sub-file (including `token_count` and `size_category`), `file_metadata` entries for root and sub-files, and no stale monolithic entry (Req 3.1, 3.2, 3.3)
- [x] 8.5 PBT: Property 4 — Total Tokens Sum Invariant: for any set of file_metadata entries after a split, `budget.total_tokens` equals the sum of all `token_count` values (Req 3.4)
- [x] 8.6 PBT: Property 5 — Threshold-Based Splitting Eligibility: for any steering file token count and threshold value, files exceeding the threshold are flagged as candidates and files at or below are not (Req 5.2)
- [x] 8.7 PBT: Property 6 — Step-to-Phase Mapping Correctness: for any valid checkpoint step number within a split module's total step range, the mapping returns exactly one phase whose `step_range` contains that step (Req 4.2, 6.2)
- [x] 8.8 PBT: Property 7 — Fallback Behavior When Sub-File Missing: for any sub-file path that does not exist on disk, the loading logic falls back to the root file path (Req 6.3)

## Task 9: Example-based unit tests

- [x] 9.1 Unit test: Module 5 split produces exact sub-file names `module-05-phase1-quality-assessment.md`, `module-05-phase2-data-mapping.md`, `module-05-phase3-test-load.md` (Req 1.2)
- [x] 9.2 Unit test: Module 6 split produces exact sub-file names `module-06-phaseA-build-loading.md`, `module-06-phaseB-load-first-source.md`, `module-06-phaseC-multi-source.md`, `module-06-phaseD-validation.md` (Req 2.2)
- [x] 9.3 Unit test: both root files start with `---\ninclusion: manual\n---` (Req 1.3, 2.3)
- [x] 9.4 Unit test: `steering-index.yaml` budget section contains `split_threshold_tokens` field (Req 5.1)
- [x] 9.5 Unit test: root files remain at original paths (`module-05-data-quality-mapping.md`, `module-06-load-data.md`) (Req 6.1)
- [x] 9.6 Unit test: `agent-instructions.md` Module Steering section documents phase-level loading and Context Budget section references phases metadata (Req 4.4, 4.5)

## Task 10: Integration tests

- [x] 10.1 Integration test: end-to-end split of real Module 5 — verify 3 sub-files + root created, `measure_steering.py --check` passes
- [x] 10.2 Integration test: end-to-end split of real Module 6 — verify 4 sub-files + root created, `measure_steering.py --check` passes
- [x] 10.3 Integration test: steering index consistency after both splits — run `measure_steering.py --check` with no mismatches
