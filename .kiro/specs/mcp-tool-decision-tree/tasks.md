# Implementation Plan: MCP Tool Decision Tree

## Overview

Create a dedicated decision tree steering file that maps bootcamp tasks to the correct MCP tool, register it in the steering index, and cross-reference it from agent-instructions.md. All work is Markdown and YAML content — no Python logic modules. Tests use pytest to validate structural requirements.

## Tasks

- [x] 1. Create the MCP tool decision tree steering file
  - [x] 1.1 Create `senzing-bootcamp/steering/mcp-tool-decision-tree.md` with YAML frontmatter and purpose summary
    - Add YAML frontmatter with `inclusion: manual`
    - Write a summary paragraph explaining the file's purpose: mapping bootcamp tasks to the correct MCP tool
    - Add a "Session Start" section directing the agent to call `get_capabilities` first before using any other tool
    - _Requirements: 1.1, 1.2, 1.3, 2.2_

  - [x] 1.2 Write the top-level decision tree and Data Preparation category
    - Add the top-level decision node: "What is the bootcamper trying to do?" with branches for each task category (Data Preparation, SDK Development, Troubleshooting, Reference & Reporting)
    - Use ASCII tree diagrams matching the `troubleshooting-decision-tree.md` convention (`├─→`, `└─→`, `│`)
    - Write the Data Preparation subsection with decision nodes distinguishing between:
      - Mapping raw data to Senzing format → `mapping_workflow`
      - Validating mapped records → `analyze_record`
      - Getting sample datasets → `get_sample_data`
      - Downloading entity spec or analyzer script → `download_resource`
    - _Requirements: 2.1, 2.3, 3.1, 3.2, 8.1, 8.3_

  - [x] 1.3 Write the SDK Development and Troubleshooting category decision nodes
    - Write the SDK Development subsection with decision nodes distinguishing between:
      - Generating code scaffolds → `generate_scaffold`
      - Getting installation/configuration guidance → `sdk_guide`
      - Looking up method signatures or flags → `get_sdk_reference`
      - Finding working code examples → `find_examples`
    - Write the Troubleshooting subsection with decision nodes distinguishing between:
      - Diagnosing a Senzing error code → `explain_error_code`
      - Searching documentation for solutions → `search_docs`
    - _Requirements: 2.1, 3.3, 3.4, 8.1, 8.3_

  - [x] 1.4 Write the Reference & Reporting category decision nodes
    - Write the Reference and Reporting subsection with decision nodes distinguishing between:
      - Searching documentation → `search_docs`
      - Getting reporting/visualization guidance → `reporting_guide`
      - Discovering available tools → `get_capabilities`
    - Verify all 12 MCP tools appear in at least one decision node path: `get_capabilities`, `mapping_workflow`, `generate_scaffold`, `get_sample_data`, `search_docs`, `explain_error_code`, `analyze_record`, `sdk_guide`, `find_examples`, `get_sdk_reference`, `reporting_guide`, `download_resource`
    - _Requirements: 2.1, 3.5, 8.1, 8.3_

  - [x] 1.5 Write the anti-pattern guidance section
    - Add an "Anti-Patterns: When NOT to Use" section with entries for each required anti-pattern:
      1. Use `mapping_workflow` instead of hand-coding Senzing JSON mappings — consequence: wrong attribute names, silent data loss
      2. Use `generate_scaffold` or `sdk_guide` instead of guessing SDK method names/signatures — consequence: non-existent methods, wrong parameters, runtime errors
      3. Use `get_sdk_reference` instead of relying on training data for SDK method signatures and flags — consequence: outdated or incorrect signatures, missing flags
      4. Call `search_docs` with `category='anti_patterns'` before recommending Senzing integration approaches — consequence: recommending deprecated or harmful patterns
      5. Use `explain_error_code` instead of guessing Senzing error code meanings — consequence: misdiagnosis, wrong fix applied
      6. Use `get_sample_data` instead of fabricating sample datasets — consequence: invalid record structures, wrong attribute names
    - Each entry must include the consequence of the incorrect approach
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [x] 1.6 Write the call-pattern examples section
    - Add a "Call Pattern Examples" section with at least one code-block example for each of the 12 MCP tools
    - Each example shows the tool name, required parameters, and representative parameter values matching a common bootcamp scenario
    - For tools with optional parameters, include at least one example showing optional parameters with an explanation of when to use them
    - Use a consistent format: tool name as H3 heading, code block with invocation, brief description of when to use
    - Tools to cover: `get_capabilities`, `mapping_workflow`, `generate_scaffold`, `get_sample_data`, `search_docs`, `explain_error_code`, `analyze_record`, `sdk_guide`, `find_examples`, `get_sdk_reference`, `reporting_guide`, `download_resource`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 8.1, 8.3_

- [x] 2. Register in the steering index
  - [x] 2.1 Add `file_metadata` entry to `senzing-bootcamp/steering/steering-index.yaml`
    - Add `mcp-tool-decision-tree.md` to the `file_metadata` section
    - Run `python3 senzing-bootcamp/scripts/measure_steering.py` to get the accurate token count
    - Set `token_count` and `size_category` based on measured values
    - Verify the token count is under the 5,000-token `split_threshold_tokens` policy; if over, review for splitting
    - _Requirements: 6.1, 8.4_

  - [x] 2.2 Add keyword entries to `senzing-bootcamp/steering/steering-index.yaml`
    - Add keyword mappings in the `keywords` section:
      - `mcp tool` → `mcp-tool-decision-tree.md`
      - `tool selection` → `mcp-tool-decision-tree.md`
      - `which tool` → `mcp-tool-decision-tree.md`
      - `decision tree` → `mcp-tool-decision-tree.md`
      - `map data` → `mcp-tool-decision-tree.md`
    - Keywords must enable the agent to find the file when a bootcamper asks "which tool should I use" or "how do I map data"
    - _Requirements: 6.2, 6.3_

- [x] 3. Add cross-reference in agent-instructions.md
  - [x] 3.1 Add a directive in the MCP Rules section of `senzing-bootcamp/steering/agent-instructions.md`
    - Add a line directing the agent to load `mcp-tool-decision-tree.md` when uncertain which MCP tool to use
    - Place it after the existing one-liner tool mapping (`Attribute names → mapping_workflow | SDK code → ...`)
    - Do NOT duplicate decision tree content — point to the file as the authoritative source
    - Keep the existing one-liner as a quick-reference summary
    - _Requirements: 7.1, 7.2, 7.3_

- [ ] 4. Measure token count and update budget
  - [x] 4.1 Run `measure_steering.py` and update `steering-index.yaml` with accurate token count
    - Run `python3 senzing-bootcamp/scripts/measure_steering.py` to measure the actual token count of the new file
    - Update the `file_metadata` entry with the measured `token_count` and correct `size_category`
    - Update the `budget.total_tokens` value to include the new file
    - _Requirements: 6.1, 8.4_

- [x] 5. Write structural validation tests
  - [x] 5.1 Create `senzing-bootcamp/tests/test_mcp_tool_decision_tree.py` with structural tests
    - Test: file exists at `senzing-bootcamp/steering/mcp-tool-decision-tree.md`
    - Test: YAML frontmatter contains `inclusion: manual`
    - Test: all 12 MCP tool names appear in the file (`get_capabilities`, `mapping_workflow`, `generate_scaffold`, `get_sample_data`, `search_docs`, `explain_error_code`, `analyze_record`, `sdk_guide`, `find_examples`, `get_sdk_reference`, `reporting_guide`, `download_resource`)
    - Test: anti-pattern entries are present for the six required scenarios (check for key phrases: "hand-cod", "guessing SDK", "training data", "anti_patterns", "guessing.*error", "fabricat")
    - Test: each of the 12 tools has at least one code-block call-pattern example
    - Test: `steering-index.yaml` contains `mcp-tool-decision-tree.md` in `file_metadata`
    - Test: `steering-index.yaml` contains at least 3 keyword entries pointing to `mcp-tool-decision-tree.md`
    - Test: `agent-instructions.md` contains a reference to `mcp-tool-decision-tree.md`
    - Test: file token count is under 5,000 (the split threshold)
    - _Requirements: 1.1, 1.2, 2.1, 4.1–4.7, 5.1, 6.1, 6.2, 7.1, 8.4_

- [x] 6. Run CI validation and all tests
  - [x] 6.1 Run the full test suite and CI validation scripts
    - Run `python3 senzing-bootcamp/scripts/validate_power.py` to verify power integrity
    - Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to verify token counts
    - Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` to verify Markdown validity
    - Run `pytest senzing-bootcamp/tests/test_mcp_tool_decision_tree.py -v` to run structural tests
    - Ensure all validations and tests pass; ask the user if questions arise
    - _Requirements: 1.1, 1.2, 2.1, 6.1, 8.1, 8.2, 8.3, 8.4_

## Notes

- No Python logic modules are needed — this feature is pure content (Markdown + YAML)
- Property-based testing does not apply (no pure functions or algorithmic logic)
- Tests use pytest for structural validation of file contents
- The existing CI pipeline (`validate-power.yml`) provides additional validation coverage
- Token budget: current total is ~92K tokens; the new file should add ~2K–4K tokens, staying well under the 60% warn threshold
- If the file exceeds 5,000 tokens, it must be reviewed for splitting per the steering index budget policy
