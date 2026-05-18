# Bugfix Design: JSON Syntax Highlighting in Chat Output

## Overview

This fix addresses the agent's inconsistent formatting of JSON content in chat. When displaying JSON (record previews, API responses, MCP tool results, configuration snippets), the agent sometimes renders it as raw inline text or in untagged code blocks, losing the IDE's syntax highlighting. The fix adds an explicit "JSON Display Formatting" rule to `agent-instructions.md` in the Communication section, ensuring all JSON shown in chat uses ` ```json ` fenced code blocks with pretty-printing.

## Bug Details

### Bug Condition

The bug manifests when the agent displays JSON content in chat — record previews from MCP tools, API response examples, configuration file contents, or command output containing JSON — and renders it as:
- Raw inline text on a single line
- An untagged code block (` ``` ` without the `json` language identifier)
- Compact/minified JSON without indentation

This makes the output hard to read, especially for large Senzing records with many nested fields.

### Root Cause

1. **No explicit JSON formatting rule**: The Communication section in `agent-instructions.md` has no rule requiring JSON content to use ` ```json ` code blocks with pretty-printing. The agent has general guidance about showing file paths and status updates, but nothing specific to structured data display.
2. **No pretty-print requirement**: When JSON arrives as a single line (common with JSONL records and compact MCP responses), there's no rule telling the agent to expand it with indentation before displaying.
3. **No consistency requirement**: When showing multiple records, there's no rule requiring uniform formatting across all of them.

## Expected Behavior

When displaying JSON content in chat, the agent must:
1. Always wrap JSON in a ` ```json ` fenced code block (enabling IDE syntax highlighting)
2. Pretty-print compact JSON with 2-space indentation
3. Format multiple records consistently (each in its own block, or all in one block separated by blank lines)
4. For very large JSON (>50 lines when pretty-printed), still use ` ```json ` but may truncate with a note

## Fix Implementation

### Changes Required

**File**: `senzing-bootcamp/steering/agent-instructions.md`

**Section**: Communication

**Specific Changes**:

Add a "JSON Display Formatting" rule after the existing output guidance ("Before each step: what and why. During: status updates. After: what changed, files with paths."):

- "When displaying JSON content in chat (record previews, API responses, MCP tool results, configuration snippets, command output containing JSON), always wrap it in a ` ```json ` fenced code block. Pretty-print compact or single-line JSON with 2-space indentation. When showing multiple JSON records, format each consistently. For JSON exceeding 50 pretty-printed lines, truncate with a note (e.g., 'showing first 3 of 50 records')."
- "Inline references to JSON field names or short values within prose remain in single backticks (e.g., `DATA_SOURCE`). This rule applies only to JSON blocks displayed in chat, not to JSON written to files."

---

**File**: `senzing-bootcamp/steering/conversation-protocol.md`

**Section**: Add a new "Code Block Formatting" section (after the existing "No Dead-End Responses" section)

**Specific Changes**:

Add a brief reinforcement with examples:

- Rule: "All JSON displayed in chat must use ` ```json ` code blocks with 2-space indentation. Never display JSON as raw text or in untagged code blocks."
- Include a WRONG/CORRECT example pair showing compact JSON without highlighting vs. properly formatted JSON in a tagged block.

## Scope Boundaries

- This fix does NOT change how JSON is written to files (JSONL stays compact for data files, pretty-printed for config files)
- This fix does NOT affect non-JSON code blocks (Python, Java, YAML, bash continue using their own language tags)
- This fix does NOT override verbosity preferences — "concise" mode still shows less JSON, but what IS shown must be properly formatted
- No hook is needed — this is a formatting rule enforced by the agent's steering, similar to the 👉 prefix rule

## Testing Strategy

- Verify `agent-instructions.md` Communication section contains the JSON Display Formatting rule
- Verify the rule requires ` ```json ` code blocks for all JSON in chat
- Verify the rule requires 2-space pretty-printing for compact JSON
- Verify the rule addresses multi-record consistency
- Verify the rule includes the >50 line truncation guidance
- Verify `conversation-protocol.md` contains the reinforcement section with examples
- Verify inline field name references are explicitly excluded (single backticks remain correct)
- Verify no regression: non-JSON code blocks and file-write behavior are explicitly preserved
