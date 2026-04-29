# Tasks

## Task 1: Create sync script with data structures and hook file parser

- [x] 1.1 Create `senzing-bootcamp/scripts/sync_hook_registry.py` with the `HookEntry` dataclass (`hook_id`, `name`, `description`, `event_type`, `action_type`, `prompt`, `file_patterns`, `tool_types`) and `CategoryMapping` dataclass (`hook_id`, `category`, `module_number`), plus module-level constants for default paths (`HOOKS_DIR`, `REGISTRY_PATH`, `CATEGORIES_PATH`)
- [x] 1.2 Implement `discover_hook_files(hooks_dir)` that returns all `*.kiro.hook` file paths sorted by name, and `parse_hook_file(hook_path)` that parses a single hook JSON file into a `HookEntry` (extracting `hook_id` from filename stem, required fields `name`/`description`/`when.type`/`then.type`, and optional fields `then.prompt`/`when.filePatterns`/`when.toolTypes`), raising `ValueError` for invalid JSON or missing required fields
  _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_
- [x] 1.3 Implement `parse_all_hooks(hooks_dir)` that calls `parse_hook_file` for each discovered file and returns `(list[HookEntry], list[str])` where the second list contains error messages for files that failed to parse
  _Requirements: 1.1, 1.6_

## Task 2: Create category configuration and categorization logic

- [x] 2.1 Create `senzing-bootcamp/hooks/hook-categories.yaml` with the category mapping for all 18 hooks, organized as `critical:` (list of hook IDs) and `modules:` (dict of module number → list of hook IDs)
  _Requirements: 2.5_
- [x] 2.2 Implement `load_category_mapping(config_path)` that parses `hook-categories.yaml` and returns a `dict[str, CategoryMapping]` mapping each hook_id to its category and optional module number
  _Requirements: 2.1, 2.5_
- [x] 2.3 Implement `categorize_hooks(hooks, mapping)` that splits hooks into `(critical_hooks_sorted_alpha, module_hooks_by_number_sorted)`, defaulting unmapped hooks to module category with "any module" label
  _Requirements: 2.2, 2.3, 2.4_

## Task 3: Implement markdown generation

- [x] 3.1 Implement `format_hook_entry(entry)` that produces the markdown for a single hook: bold Hook_ID, parenthesized event flow (including `filePatterns` and `toolTypes` when present), prompt text as paragraph, and bullet list with `id`, `name`, `description` fields
  _Requirements: 3.5, 3.6_
- [x] 3.2 Implement `generate_registry(critical_hooks, module_hooks, total_count)` that produces the complete `hook-registry.md` content: frontmatter (`---\ninclusion: manual\n---`), title (`# Hook Registry`), intro paragraph with total count, `## Critical Hooks` section (alphabetical), `## Module Hooks` section (sorted by module number, then alphabetical within module), with Unix line endings (`\n`)
  _Requirements: 3.1, 3.2, 3.3, 3.4, 6.3_

## Task 4: Implement write/verify modes and CLI

- [x] 4.1 Implement `write_registry(content, output_path)` that writes generated content to the registry file path, and `verify_registry(content, existing_path)` that compares generated content against the existing file byte-for-byte, returning `(matches: bool, message: str)` with appropriate messages for matching, differing, and missing file cases
  _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
- [x] 4.2 Implement `main()` CLI entry point with `argparse` supporting `--write` (default), `--verify`, `--hooks-dir`, `--output`, and `--categories` flags. In write mode, generate and write the registry. In verify mode, compare and exit with code 0 (match) or 1 (differ/missing). Print error messages for parse failures. Depend only on Python standard library
  _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.4_

## Task 5: Verify on real hook files

- [x] 5.1 Run `python senzing-bootcamp/scripts/sync_hook_registry.py --write` to generate the registry from real hook files, then run `--verify` to confirm the generated output matches
- [x] 5.2 Run the script twice on the same hook files and verify the output is byte-identical (deterministic generation)
  _Requirements: 6.1, 6.2_

## Task 6: CI integration

- [x] 6.1 Add a CI pipeline step (or document the command) that runs `python scripts/sync_hook_registry.py --verify` and fails the build on exit code 1, with a message instructing the developer to run `python scripts/sync_hook_registry.py --write` locally
  _Requirements: 5.1, 5.2, 5.3_

## Task 7: Property-based tests (Hypothesis)

- [x] 7.1 Create `senzing-bootcamp/tests/test_sync_hook_registry_properties.py` with Hypothesis strategies for generating random `HookEntry` objects (with random hook_ids, names, descriptions, event types, action types, and optional fields), random category mappings, and random registry content strings
- [x] 7.2 PBT: Property 1 — Hook Field Extraction Completeness: for any valid hook JSON dict with required and optional fields, the parser extracts all present fields correctly and hook_id equals the filename stem (Req 1.2, 1.3, 1.4, 1.5)
- [x] 7.3 PBT: Property 2 — Category Placement Correctness: for any set of hooks and category mapping, Critical hooks appear in Critical section, Module hooks appear under correct module, unmapped hooks appear under "any module" (Req 2.2, 2.3, 2.4)
- [x] 7.4 PBT: Property 3 — Alphabetical Sort Within Sections: for any set of hooks within a section, entries are sorted alphabetically by hook_id (Req 3.3, 3.4)
- [x] 7.5 PBT: Property 4 — Registry Frontmatter and Structure: for any generated output, content starts with frontmatter and contains required headings (Req 3.1, 3.2)
- [x] 7.6 PBT: Property 5 — Hook Entry Format Correctness: for any HookEntry, formatted markdown contains bold hook_id, event flow, and bullet list with id/name/description; filePatterns and toolTypes appear when present (Req 3.5, 3.6)
- [x] 7.7 PBT: Property 6 — Deterministic Generation: for any set of hook data and category mapping, generating twice produces byte-identical output (Req 6.1)
- [x] 7.8 PBT: Property 7 — Stable Sort Order Independence: for any set of hooks in any input order, the generated output is identical (Req 6.2)
- [x] 7.9 PBT: Property 8 — Verify Mode Correctness: for any generated content and existing content, verify returns True iff byte-identical, False when differing or file missing (Req 4.2, 4.3, 4.4, 4.5)
- [x] 7.10 PBT: Property 9 — Unix Line Ending Normalization: for any generated output, content contains only `\n` line endings and no `\r` characters (Req 6.3)

## Task 8: Example-based unit tests

- [x] 8.1 Unit test: parse real `ask-bootcamper.kiro.hook` and verify correct field extraction (Req 1.2)
- [x] 8.2 Unit test: parse all 18 real hook files without errors (Req 1.1)
- [x] 8.3 Unit test: invalid JSON file is skipped with error message containing filename (Req 1.6)
- [x] 8.4 Unit test: category mapping loads correctly from real `hook-categories.yaml` (Req 2.5)
- [x] 8.5 Unit test: `--verify` exits 0 when generated registry matches current `hook-registry.md` (Req 4.3)
- [x] 8.6 Unit test: `--verify` exits 1 when registry file is missing (Req 4.5)
- [x] 8.7 Unit test: script uses only Python standard library imports (Req 5.4)
- [x] 8.8 Unit test: generated registry for real hooks is byte-identical when regenerated (Req 6.1)

## Task 9: Integration tests

- [x] 9.1 Integration test: end-to-end generate from real hooks, verify matches existing `hook-registry.md`
- [x] 9.2 Integration test: `python scripts/sync_hook_registry.py --verify` exits 0 on current state
- [x] 9.3 Integration test: regenerate twice from real hooks, compare output byte-for-byte (Req 6.1)
