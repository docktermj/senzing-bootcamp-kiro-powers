---
inclusion: manual
---
<!-- Frontmatter: Every module steering file must begin with YAML frontmatter
     containing "inclusion: manual". This ensures the agent framework only loads
     the module when explicitly requested. -->

# Module NN — [Module Title]

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.
<!-- First-read instruction: Must appear within the first 10 non-blank lines
     after frontmatter. Must reference both config/bootcamp_progress.json and
     module-transitions.md so the agent displays the correct banner. -->

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_NN_[MODULE_TITLE].md`.
<!-- User reference line: Points the bootcamper to the companion documentation
     for this module. Replace NN and [MODULE_TITLE] with the actual values. -->

**Before/After:** [Description of state before this module] → [Description of state after completing this module]
<!-- Before/After block: Describes the bootcamper's state before and after
     completing this module. Must appear before the first workflow step.
     Can use a table format instead:
     | Before | After |
     |--------|-------|
     | [description] | [description] |
-->

**Prerequisites:** [List any modules or conditions that must be met before starting]
<!-- Prerequisites block: List modules that must be completed first, or "None"
     if this is an entry-point module. -->

## Workflow Steps

1. **[Step 1 description]**

   [Detailed instructions for step 1]

   **Checkpoint:** Write step 1 to `config/bootcamp_progress.json`.
   <!-- Each numbered workflow step must have a checkpoint instruction that
        writes the step number to bootcamp_progress.json. The step number
        in the checkpoint must match the parent step number. -->

2. **[Step 2 description]**

   [Detailed instructions for step 2]

   **Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.
   <!-- Repeat for every top-level numbered step in the module. -->

**Success indicator:** ✅ [Completion criteria description — what the bootcamper should have achieved]
<!-- Success indicator: Must appear after all workflow steps. Summarises the
     completion criteria for the module. -->
