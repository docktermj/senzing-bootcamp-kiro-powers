# Senzing Bootcamp Power Feedback

## Improvement: Generated files placed in project root instead of proper subdirectories

**Module:** 7 (also affects earlier modules)
**Context:** Completing Module 7 Query, Visualize & Discover phase. Noticed \*.jsonl, \*.md, and \*.py files in the project root.
**Open files:** src/load/load_sources.py
**Severity:** Medium
**Description:** The bootcamp placed generated files (\*.jsonl, \*.md, \*.py) in the project root directory instead of the appropriate subdirectories (data/, docs/, src/). Generated files of these types should NEVER be placed in the project root — they belong in their proper locations per the project structure.
**Affected files in root:**

- blacklist_sample.jsonl → should be in data/samples/
- suppliers_sample.jsonl → should be in data/samples/
- profile_report_blacklist.md → should be in docs/
- profile_report_suppliers.md → should be in docs/
- sz_json_analyzer.py → should be in scripts/
- sz_schema_generator.py → should be in scripts/
- senzing_entity_specification.md → should be in docs/
- senzing_mapping_examples.md → should be in docs/
- identifier_crosswalk.json → should be in config/

**Suggestion:** Enforce a rule that generated files are always placed in the correct subdirectory based on their type. The write-policy-gate hook should catch this.
**Date:** 2026-05-23

## Improvement: Add module-by-module recap document with PDF export

**Module:** 7 (end of core bootcamp)
**Context:** Completing the core bootcamp track. Bootcamper wants a running account of what happened.
**Open files:** src/load/load_sources.py
**Severity:** Medium
**Description:** At the end of every module, before moving to the next module, the bootcamp should append a "recap" section to `docs/bootcamp_recap.md` containing: (1) information shared with the bootcamper, (2) questions asked of the bootcamper, (3) answers given by the bootcamper, and (4) actions taken. This creates a module-by-module account of the entire bootcamp experience. At the end of the bootcamp, generate a PDF of this markdown file that can be shared with others. Include the date and time of the bootcamp.
**Suggestion:** Add a module-completion hook or step that appends to docs/bootcamp_recap.md before transitioning. At graduation/completion, auto-generate a PDF from the recap file using fpdf or similar.
**Date:** 2026-05-23
