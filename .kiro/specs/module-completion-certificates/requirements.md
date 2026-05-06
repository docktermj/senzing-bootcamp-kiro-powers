# Requirements: Module Completion Certificates

## Overview

Individual module completions are only tracked in JSON. This feature generates a brief per-module completion summary documenting what was built, key concepts mastered, and artifacts produced — giving bootcampers tangible evidence of progress.

## Requirements

1. When a module is marked complete (via the module-completion workflow), the agent generates a completion certificate at `docs/progress/MODULE_N_COMPLETE.md`
2. Each certificate contains: module title, completion date (ISO 8601), time spent (from session analytics if available, otherwise "not tracked"), key concepts learned (3-5 bullet points), artifacts produced (file paths with descriptions), and a "What This Enables" section listing what the bootcamper can now do
3. The certificate format is consistent across all modules — a Markdown template with fixed sections
4. The `docs/progress/` directory is created automatically on first certificate generation
5. Certificates are cumulative — completing Module 6 does not remove or modify the Module 5 certificate
6. The module-completion steering file (`module-completion.md`) is updated to include certificate generation as a step in the completion workflow
7. A summary index file `docs/progress/README.md` is maintained listing all completed modules with links to their certificates, track progress, and total time invested
8. The certificate content is derived from the module's steering file (concepts) and the bootcamper's actual work (artifacts) — not generic boilerplate
9. If session analytics are available, the certificate includes a "Session Stats" section: total turns, corrections made, time per step
10. The `export_results.py` script includes certificates in the export bundle under an "achievements" section
11. Certificates use the bootcamper's chosen language in code-related descriptions (e.g., "Built a Python loading script" not "Built a loading script")

## Non-Requirements

- This does not generate visual certificates (PDF, images) — Markdown only
- This does not integrate with external credentialing systems
- This does not block module transitions if certificate generation fails
- This does not require the bootcamper to review or approve the certificate
