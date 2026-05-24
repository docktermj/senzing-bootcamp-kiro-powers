# Bugfix Requirements Document

## Introduction

The `write-policy-gate` hook contains Check 4 (Root File Placement Enforcement) which is designed to block writes of `.py`, `.md`, `.jsonl`, `.csv`, and non-config `.json` files to the project root. Despite this check existing in the hook prompt, generated files of these types are still being placed in the project root during bootcamp execution (observed in Module 7 and potentially earlier modules). The bug condition is that the hook's root-detection logic fails to correctly identify root-level writes under certain path representations, allowing blocked file types to bypass enforcement.

Affected files observed in the project root include: `blacklist_sample.jsonl`, `suppliers_sample.jsonl`, `profile_report_blacklist.md`, `profile_report_suppliers.md`, `sz_json_analyzer.py`, `sz_schema_generator.py`, `senzing_entity_specification.md`, `senzing_mapping_examples.md`, and `identifier_crosswalk.json`.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent writes a `.jsonl` file (e.g., `blacklist_sample.jsonl`) to the project root THEN the `write-policy-gate` hook fails to block the write and the file is created in the root directory

1.2 WHEN the agent writes a `.md` file other than `README.md` (e.g., `profile_report_blacklist.md`) to the project root THEN the `write-policy-gate` hook fails to block the write and the file is created in the root directory

1.3 WHEN the agent writes a `.py` file (e.g., `sz_json_analyzer.py`) to the project root THEN the `write-policy-gate` hook fails to block the write and the file is created in the root directory

1.4 WHEN the agent writes a non-config `.json` file (e.g., `identifier_crosswalk.json`) to the project root THEN the `write-policy-gate` hook fails to block the write and the file is created in the root directory

1.5 WHEN the hook's Check 4 evaluates a file path that uses an absolute path representation or a path without an explicit subdirectory prefix THEN the root-detection heuristic ("the path has no subdirectory") fails to trigger the blocking logic

1.6 WHEN the hook prompt relies on the agent's self-evaluation to determine "project root" without explicit path-matching rules THEN the agent inconsistently applies the root check, especially under context pressure or when MCP-generated paths are used directly

### Expected Behavior (Correct)

2.1 WHEN the agent writes a `.jsonl` file to the project root THEN the `write-policy-gate` hook SHALL block the write and output corrective routing to the appropriate `data/` subdirectory (e.g., `data/samples/`)

2.2 WHEN the agent writes a `.md` file other than `README.md` to the project root THEN the `write-policy-gate` hook SHALL block the write and output corrective routing to `docs/`

2.3 WHEN the agent writes a `.py` file to the project root THEN the `write-policy-gate` hook SHALL block the write and output corrective routing to `src/transform/`, `src/load/`, `src/query/`, or `scripts/` based on file content

2.4 WHEN the agent writes a non-config `.json` file (not on the Root Whitelist) to the project root THEN the `write-policy-gate` hook SHALL block the write and output corrective routing to `config/` or `data/` based on content type

2.5 WHEN the hook evaluates a target file path THEN it SHALL determine root placement by checking whether the path (after resolving to project-relative form) contains zero directory separators before the filename, regardless of whether the path is absolute or relative

2.6 WHEN the hook's Check 4 fires THEN it SHALL apply deterministic extension-matching rules that do not depend on the agent's subjective interpretation of "project root" — any file whose project-relative path equals just a filename (no `/` before it) with a blocked extension is a violation

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent writes a file to a proper subdirectory (e.g., `data/samples/blacklist_sample.jsonl`) THEN the `write-policy-gate` hook SHALL CONTINUE TO allow the write silently with zero output

3.2 WHEN the agent writes a Root Whitelist file (`.gitignore`, `.env`, `.env.example`, `README.md`, `requirements.txt`, `pom.xml`, `*.csproj`, `Cargo.toml`, `package.json`) to the project root THEN the `write-policy-gate` hook SHALL CONTINUE TO allow the write silently

3.3 WHEN the agent writes any file type not in the blocked extensions list (e.g., `.yaml`, `.toml`, `.lock`) to the project root THEN the `write-policy-gate` hook SHALL CONTINUE TO allow the write silently

3.4 WHEN Check 1 (SQL blocking), Check 2 (single-question enforcement), or Check 3 (file path policies) detect a violation THEN those checks SHALL CONTINUE TO produce their respective corrective output unchanged

3.5 WHEN all four checks pass for a normal write to a subdirectory THEN the hook SHALL CONTINUE TO produce zero tokens of output
