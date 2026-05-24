# Implementation Plan: JSON Syntax Highlighting in Chat Output

## Overview

Add an explicit JSON display formatting rule to the agent's Communication section and reinforce it in the conversation protocol with examples, ensuring all JSON shown in chat uses syntax-highlighted code blocks with pretty-printing.

## Tasks

- [x] 1. Add "JSON Display Formatting" rule to agent-instructions.md
  - [x] 1.1 Add a new rule to the Communication section in `senzing-bootcamp/steering/agent-instructions.md`
    - Place it after the line: "Before each step: what and why. During: status updates. After: what changed, files with paths. Offer to visualize data results as a web page."
    - Rule text: "When displaying JSON in chat (record previews, API responses, MCP tool results, configuration snippets, command output), always use a ` ```json ` fenced code block. Pretty-print compact or single-line JSON with 2-space indentation. Format multiple JSON records consistently — each in its own ` ```json ` block. For JSON exceeding 50 pretty-printed lines, truncate with a note (e.g., 'showing first 3 of 50 records'). Inline references to JSON field names or short values in prose use single backticks (e.g., `DATA_SOURCE`)."
    - Do NOT modify any existing rules in the Communication section
    - Do NOT add a hook for this — it is a formatting convention like the 👉 prefix
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.2, 3.3_

- [x] 2. Add "Code Block Formatting" section to conversation-protocol.md
  - [x] 2.1 Add a new section to `senzing-bootcamp/steering/conversation-protocol.md` after the "No Dead-End Responses" section
    - Section heading: `## Code Block Formatting`
    - Rule text: "All JSON displayed in chat must use ` ```json ` code blocks with 2-space indentation. Never display JSON as raw text or in untagged code blocks."
    - Include a WRONG example: JSON shown as raw inline text or in an untagged ` ``` ` block
    - Include a CORRECT example: the same JSON in a ` ```json ` block with proper indentation
    - Preserve all existing sections — insert the new section between "No Dead-End Responses" and "One Question Rule"
    - Do NOT modify any other section in the file
    - _Requirements: 2.1, 2.2, 3.1, 3.2_

- [x] 3. Verify the fix
  - Confirm `agent-instructions.md` contains the JSON Display Formatting rule in the Communication section
  - Confirm the rule requires ` ```json ` fenced code blocks
  - Confirm the rule requires 2-space pretty-printing for compact JSON
  - Confirm the rule addresses multi-record consistency
  - Confirm the rule includes truncation guidance for large JSON (>50 lines)
  - Confirm the rule preserves inline backtick usage for field names in prose
  - Confirm `conversation-protocol.md` contains the Code Block Formatting section with WRONG/CORRECT examples
  - Confirm no existing rules were modified or removed in either file
  - Run steering validation: `python3 senzing-bootcamp/scripts/validate_commonmark.py senzing-bootcamp/steering/agent-instructions.md senzing-bootcamp/steering/conversation-protocol.md`

## Notes

- This fix is purely steering — no Python code, no hooks, no config changes
- The rule mirrors how the 👉 prefix works: a formatting convention enforced by agent awareness, not by a validation hook
- Verbosity preferences ("concise" mode) still control HOW MUCH JSON is shown, but this rule ensures whatever IS shown is properly formatted
- Non-JSON code blocks (Python, Java, YAML, bash) are unaffected — they already use appropriate language tags
- JSON written to files is unaffected — JSONL data files stay compact, config files stay pretty-printed
