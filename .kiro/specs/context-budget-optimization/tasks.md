# Tasks

- [x] 1. Update `module-transitions.md` frontmatter
  - [x] 1.1 Replace `inclusion: auto` with `inclusion: fileMatch` and add `fileMatchPattern: "config/bootcamp_progress.json"` and a `description` field in the YAML frontmatter
  - [x] 1.2 Verify the body content (all sections after frontmatter) is unchanged
- [x] 2. Update `agent-instructions.md` module transitions reference
  - [x] 2.1 Update the Communication section line referencing `module-transitions.md` to note it is conditionally loaded when `config/bootcamp_progress.json` is accessed
  - [x] 2.2 Verify all other content in `agent-instructions.md` is preserved
