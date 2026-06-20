---
inclusion: manual
---

# Hook Registry — Module 4 (Full Prompts)

Full hook prompts for Module 4, for use with the `createHook` tool when starting this module.

For a quick reference of all hooks, see `hook-registry.md`.
For critical hooks (created during onboarding), see `hook-registry-critical.md`.

## Module 4 Hooks

**validate-data-files** (fileCreated → askAgent, filePatterns: `data/raw/*.*`)

Prompt:

````text
A new data file was added to data/raw/. Before proceeding, do a quick sanity check: (1) Can the file be read without encoding errors? Try reading the first 10 lines. (2) Is the format recognizable (CSV, JSON, JSONL, XML, TSV)? (3) Does it contain at least a few records? (4) Are there obvious issues like binary content, empty file, or corrupted data? Report what you find to the bootcamper. If the file looks good, say so briefly. If there are issues, explain what's wrong and suggest how to fix it.
````

- id: `validate-data-files`
- name: `to validate data files`
- description: `When new data files are added to data/raw/, checks file format, encoding, and basic readability to catch issues early.`
