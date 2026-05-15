# Requirements: Split hook-registry.md Below Token Threshold

## Overview

Split `hook-registry.md` (currently 8,307 tokens) to comply with the 5,000-token split threshold defined in `steering-index.yaml`, improving context budget efficiency.

## Requirements

1. Split `hook-registry.md` into two files: `hook-registry.md` (summary) and `hook-registry-detail.md` (full prompts)
2. The summary file must contain: hook ID, event type, one-line description, and category for all 24 hooks — target under 2,500 tokens
3. The detail file must contain: full hook prompts, detailed descriptions, and cross-references — this file uses manual inclusion
4. Update `steering-index.yaml` `file_metadata` with token counts for both new files
5. Both files must remain under the 5,000-token split threshold
6. Update keyword routing in `steering-index.yaml` to point `hook`/`hooks` keywords to the summary file
7. Update any `#[[file:]]` references to `hook-registry.md` in other steering files
8. Update `sync_hook_registry.py` to generate/validate both files
9. Run `sync_hook_registry.py --verify` to confirm the split files are consistent with actual hook files
10. Ensure `validate_commonmark.py` passes on both new files
11. Update tests that reference `hook-registry.md` to account for the split
