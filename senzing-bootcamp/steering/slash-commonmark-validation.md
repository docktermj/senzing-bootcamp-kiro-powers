---
inclusion: manual
description: "Manual slash command (/commonmark-validation): validate and fix Markdown CommonMark compliance in one pass. Replaces the former commonmark-validation manual hook."
---

# Check Markdown Style

Manually invoke this command by name when you want to validate Markdown style
across the project in one pass. It replaces the former `commonmark-validation`
manual hook. When invoked, follow the instruction below verbatim:

```text
The user wants to validate Markdown style across the project in one pass. Review every Markdown file (all *.md files) for CommonMark compliance. For each file, check for:

1. MD022: Headings should be surrounded by blank lines
2. MD040: Fenced code blocks should have a language specified
3. Bold text followed by colons should use format: **Label:** (with space before colon)
4. MD031: Fenced code blocks should be surrounded by blank lines
5. MD032: Lists should be surrounded by blank lines

EXCEPTION: If the file is CHANGELOG.md, ignore MD024 (duplicate headings) — repeated ### Added, ### Changed, ### Fixed, ### Removed headings under different version sections are standard Keep a Changelog format and should not be flagged.

If any issues are found, fix them automatically to maintain CommonMark compliance across all documentation. Apply the fixes across all Markdown files in this single pass rather than one file at a time.

After fixing issues: briefly summarize what was corrected across the files (one sentence), then end with a contextual 👉 forward-moving question that guides the bootcamper to the next step in the current workflow. Check `config/bootcamp_progress.json` for the current module and step to determine what comes next.

If no issues are found: output nothing. Proceed silently.
```
