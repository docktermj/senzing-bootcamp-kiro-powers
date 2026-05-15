# Bugfix Requirements Document

## Introduction

When the agent displays JSON output in chat — record previews, API responses, configuration snippets, MCP tool results, or command output containing JSON — it sometimes renders the JSON as raw unformatted text on a single line or without a language-tagged code block. This makes the output hard to read, especially for large records with many fields. The IDE supports syntax-highlighted rendering via markdown ` ```json ` code blocks, which makes keys, values, nesting, and structure immediately visible. The agent should always use this formatting for JSON content.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent displays JSON content in chat (record previews, API responses, MCP tool output, configuration files) THEN the agent sometimes renders it as raw inline text or in an untagged code block without the `json` language identifier

1.2 WHEN JSON output is a single long line (e.g., JSONL records, compact API responses) THEN the agent sometimes displays it without pretty-printing or wrapping in a ` ```json ` block, making it unreadable

1.3 WHEN the agent shows multiple JSON records (e.g., previewing transformed JSONL output) THEN the agent inconsistently formats some records with highlighting and others without

### Expected Behavior (Correct)

2.1 WHEN the agent displays any JSON content in chat THEN the agent SHALL wrap it in a markdown ` ```json ` code block so the IDE renders it with syntax highlighting (color-coded keys, values, brackets)

2.2 WHEN JSON content is compact/single-line (e.g., JSONL records) THEN the agent SHALL pretty-print it with indentation (2-space indent) inside the ` ```json ` code block to make the structure readable

2.3 WHEN the agent displays multiple JSON records in sequence THEN the agent SHALL format each record consistently in its own ` ```json ` code block (or all in one block separated by blank lines if they're part of the same logical output)

2.4 WHEN JSON content is very large (more than 50 lines when pretty-printed) THEN the agent SHALL still use ` ```json ` formatting but MAY truncate with a note ("showing first 3 records of 50" or "key fields shown, full output in file")

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent displays non-JSON code (Python, Java, YAML, shell commands) THEN the system SHALL CONTINUE TO use the appropriate language tag for that content (` ```python `, ` ```java `, ` ```yaml `, ` ```bash `)

3.2 WHEN the agent references a JSON field name or value inline within prose text THEN the system SHALL CONTINUE TO use inline code formatting (single backticks) rather than a full code block

3.3 WHEN the agent writes JSON to a file (not displaying in chat) THEN the system SHALL CONTINUE TO write it in whatever format is appropriate for the file (compact JSONL for data files, pretty-printed for config files) — this rule only applies to chat display

3.4 WHEN the bootcamper's verbosity preference is set to "concise" THEN the system SHALL CONTINUE TO respect that by showing less JSON content, but what IS shown must still be properly formatted in ` ```json ` blocks
