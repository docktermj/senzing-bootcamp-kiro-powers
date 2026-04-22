# Design Document

## Overview

This feature adds a visually prominent banner block to the top of each of the 13 module documentation files in `senzing-bootcamp/docs/modules/`. The banner follows the established pattern from `senzing-bootcamp/steering/module-transitions.md` — a three-line bordered text block with 🚀 emoji, wrapped in a fenced code block. This is a static text insertion task with no runtime logic, APIs, or code generation involved.

## Architecture

There is no runtime architecture. The change is a one-time edit to 13 existing markdown files. Each file receives an identical structural addition (a fenced code block containing a three-line banner) prepended before the existing `# Module N: Title` heading.

### Change Flow

```mermaid
flowchart LR
    A[Read module file] --> B[Construct banner from heading]
    B --> C[Prepend banner + blank line]
    C --> D[Preserve all existing content]
```

### Design Decision: Static Insertion vs. Script

A script could parse headings and generate banners automatically. However, with only 13 files and fixed, known content, direct manual insertion is simpler, less error-prone, and avoids introducing tooling dependencies. The banner text for each module is explicitly specified in the requirements, so there is no ambiguity to resolve programmatically.

## Components and Interfaces

There are no software components or interfaces. The deliverable is 13 modified markdown files.

### File Modification Specification

Each of the 13 files in `senzing-bootcamp/docs/modules/` will be modified identically in structure:

**Before:**

```markdown
# Module N: Title

> **Agent workflow:** ...
```

**After:**

````markdown
```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀🚀🚀  MODULE N: TITLE IN CAPS  🚀🚀🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

# Module N: Title

> **Agent workflow:** ...
````

### Banner-to-File Mapping

| File | Banner Title Line |
| --- | --- |
| `MODULE_0_SDK_SETUP.md` | `🚀🚀🚀  MODULE 0: SET UP SDK  🚀🚀🚀` |
| `MODULE_1_QUICK_DEMO.md` | `🚀🚀🚀  MODULE 1: QUICK DEMO  🚀🚀🚀` |
| `MODULE_2_BUSINESS_PROBLEM.md` | `🚀🚀🚀  MODULE 2: UNDERSTAND BUSINESS PROBLEM  🚀🚀🚀` |
| `MODULE_3_DATA_COLLECTION.md` | `🚀🚀🚀  MODULE 3: DATA COLLECTION POLICY  🚀🚀🚀` |
| `MODULE_4_DATA_QUALITY_SCORING.md` | `🚀🚀🚀  MODULE 4: EVALUATE DATA QUALITY WITH AUTOMATED SCORING  🚀🚀🚀` |
| `MODULE_5_DATA_MAPPING.md` | `🚀🚀🚀  MODULE 5: MAP YOUR DATA  🚀🚀🚀` |
| `MODULE_6_SINGLE_SOURCE_LOADING.md` | `🚀🚀🚀  MODULE 6: LOAD SINGLE DATA SOURCE  🚀🚀🚀` |
| `MODULE_7_MULTI_SOURCE_ORCHESTRATION.md` | `🚀🚀🚀  MODULE 7: MULTI-SOURCE ORCHESTRATION  🚀🚀🚀` |
| `MODULE_8_QUERY_VALIDATION.md` | `🚀🚀🚀  MODULE 8: QUERY AND VALIDATE RESULTS  🚀🚀🚀` |
| `MODULE_9_PERFORMANCE_TESTING.md` | `🚀🚀🚀  MODULE 9: PERFORMANCE TESTING AND BENCHMARKING  🚀🚀🚀` |
| `MODULE_10_SECURITY_HARDENING.md` | `🚀🚀🚀  MODULE 10: SECURITY HARDENING  🚀🚀🚀` |
| `MODULE_11_MONITORING_OBSERVABILITY.md` | `🚀🚀🚀  MODULE 11: MONITORING AND OBSERVABILITY  🚀🚀🚀` |
| `MODULE_12_DEPLOYMENT_PACKAGING.md` | `🚀🚀🚀  MODULE 12: PACKAGE AND DEPLOY  🚀🚀🚀` |

### Key Rules

- The banner title drops parenthetical suffixes like "(Optional)" from the heading — e.g., `# Module 1: Quick Demo (Optional)` becomes `MODULE 1: QUICK DEMO`.
- The border lines use exactly 56 `━` characters, matching the template in `module-transitions.md`.
- Two spaces separate the emoji group from the title text on each side.

## Data Models

Not applicable. No data is stored, transformed, or transmitted. The only artifact is the modified markdown text within each file.

## Error Handling

Not applicable in the traditional sense. The only risk is human error during insertion:

- **Wrong module number or name**: Mitigated by the explicit mapping table above and the requirements document specifying each banner's exact text.
- **Missing blank line separator**: Each banner block must be followed by exactly one blank line before the `# Module` heading.
- **Corrupted existing content**: Each edit only prepends content; no existing lines are modified or deleted.

## Testing Strategy

Property-based testing does not apply to this feature. There are no functions, no input/output transformations, no parsers, and no runtime logic. The deliverable is 13 static text edits to markdown files.

### Verification Approach

Verification is done through manual inspection and simple structural checks:

1. **Visual inspection**: Open each modified file and confirm the banner appears correctly at the top, followed by a blank line, followed by the original heading.
2. **Structural grep checks**: Use `grep` or similar to verify:
   - Each module file starts with the fenced code block opening (`` ```text ``).
   - Each file contains the correct `MODULE N: TITLE` string in uppercase.
   - The original `# Module N:` heading still exists in each file.
   - No content after the heading has been altered (diff check against the original, excluding the prepended banner).
3. **Count check**: Confirm exactly 13 files were modified.

### What NOT to Test

- No unit tests — there is no code to unit test.
- No property-based tests — there are no functions or transformations.
- No integration tests — there are no services or APIs involved.
