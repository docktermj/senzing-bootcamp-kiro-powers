# Design Document

## Overview

The module-recap-document feature adds a persistent recap file (`docs/bootcamp_recap.md`) that accumulates a structured record of each module's experience, and a PDF generation script for sharing at graduation. The design integrates into the existing module-completion workflow via steering file updates and a new hook, using a standalone Python script for PDF rendering.

## Architecture

The feature consists of four components: a steering integration for the recap append logic, a hook for automatic detection, a standalone PDF script, and a graduation workflow update. These components interact through the file system (`docs/bootcamp_recap.md`) as the shared state.

## Components and Interfaces

### 1. Recap Append Logic (Steering Integration)

**Location:** `senzing-bootcamp/steering/module-completion.md` (modified)

Executes as part of the module completion workflow, after progress file update and before journal entry. Derives recap content from the session context (steering topics, conversation history, file operations) and appends a structured Recap_Section to `docs/bootcamp_recap.md`.

**Interface:**
- Input: Session context (conversation history, file operations, steering topics covered)
- Input: `config/bootcamp_progress.json` (module completion state)
- Input: `config/bootcamp_preferences.yaml` (bootcamper name)
- Output: Appended section in `docs/bootcamp_recap.md`

### 2. Module Recap Hook

**Location:** `senzing-bootcamp/hooks/module-recap-append.kiro.hook`

A `postTaskExecution` hook that detects module completion boundaries and triggers the recap append logic.

**Interface:**
```json
{
  "name": "to append module recap on completion",
  "version": "1.0.0",
  "description": "Appends a structured recap section to docs/bootcamp_recap.md when a module is completed.",
  "when": {
    "type": "postTaskExecution"
  },
  "then": {
    "type": "askAgent",
    "prompt": "<recap-append-instructions>"
  }
}
```

### 3. PDF Generation Script

**Location:** `senzing-bootcamp/scripts/generate_recap_pdf.py`

Standalone CLI script with `main()` entry point and argparse interface. Parses recap markdown using stdlib (`re` module) and renders PDF using `fpdf2`.

**Interface:**
```
usage: generate_recap_pdf.py [-h] [--input INPUT] [--output OUTPUT]

options:
  --input INPUT    Path to recap markdown (default: docs/bootcamp_recap.md)
  --output OUTPUT  Path for output PDF (default: docs/bootcamp_recap.pdf)
```

**Exit codes:**
- 0: Success
- 1: Error (missing dependency, file not found, render failure)

### 4. Graduation Integration

**Location:** `senzing-bootcamp/steering/graduation.md` (modified)

Adds a PDF generation step (Step 0) after pre-checks and before Step 1 of the existing graduation workflow.

## Data Models

### Recap Document Structure

```markdown
# Senzing Bootcamp Recap

**Bootcamper:** [Name or "Bootcamper"]
**Started:** 2026-05-23T10:30:00-05:00
**Total Duration:** 4h 32m

---

## Module N: [Module Name] — [ISO 8601 Timestamp]

### Information Shared
- [Concept or explanation presented]
- [Reference material shared]

### Questions Asked
1. [Agent question to bootcamper]
2. [Agent question to bootcamper]

### Answers Given
1. [Bootcamper response to question 1]
2. [Bootcamper response to question 2]

### Actions Taken
- Created `[file path]`
- Modified `[file path]`
- Ran `[command]`

### Duration
[elapsed time for module]

---
```

### Parsed Recap Model (Internal to PDF Script)

```python
@dataclass
class RecapHeader:
    bootcamper: str          # Name or "Bootcamper"
    started: str             # ISO 8601 timestamp
    total_duration: str      # Human-readable duration

@dataclass
class RecapSection:
    module_number: int
    module_name: str
    timestamp: str           # ISO 8601 timestamp
    information_shared: list[str]
    questions_asked: list[str]
    answers_given: list[str]
    actions_taken: list[str]
    duration: str

@dataclass
class RecapDocument:
    header: RecapHeader
    sections: list[RecapSection]
```

## Data Flow

```text
Module Completion
       │
       ▼
┌─────────────────────┐
│ Progress File Update │  (existing: marks module complete)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Recap Section Append │  (NEW: appends to docs/bootcamp_recap.md)
│  - Info Shared       │
│  - Questions Asked   │
│  - Answers Given     │
│  - Actions Taken     │
│  - Duration          │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Journal Entry        │  (existing: appends to docs/bootcamp_journal.md)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Certificate + Next   │  (existing: certificate, next-step options)
└─────────────────────┘


Graduation
       │
       ▼
┌─────────────────────┐
│ Pre-checks           │  (existing)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ PDF Generation       │  (NEW: scripts/generate_recap_pdf.py)
│  Input:  docs/bootcamp_recap.md
│  Output: docs/bootcamp_recap.pdf
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Graduation Steps 1-5 │  (existing)
└─────────────────────┘
```

## Error Handling

| Component | Condition | Behavior |
|-----------|-----------|----------|
| Recap Hook | No new module completion detected | Produce no output, do nothing |
| Recap Hook | `config/bootcamp_progress.json` missing | Produce no output, do nothing |
| Recap Hook | File system write error on `docs/bootcamp_recap.md` | Log warning, continue module completion flow |
| Recap Hook | `config/bootcamp_preferences.yaml` missing | Use "Bootcamper" as default name |
| PDF Script | `fpdf2` not installed | Exit code 1, message: "fpdf2 is required. Install with: pip install fpdf2" |
| PDF Script | Input file not found | Exit code 1, message: "Recap file not found: {path}" |
| PDF Script | Input file empty | Exit code 1, message: "Recap file is empty: {path}" |
| PDF Script | PDF write failure | Exit code 1, message: "Failed to write PDF: {error}" |
| PDF Script | Success | Exit code 0, message: "PDF generated: {output_path}" |
| Graduation | `docs/bootcamp_recap.md` missing | Skip PDF generation silently, proceed to Step 1 |
| Graduation | PDF generation fails | Inform bootcamper, suggest `pip install fpdf2`, proceed to Step 1 |

## Testing Strategy

### Unit Tests (`senzing-bootcamp/tests/test_generate_recap_pdf.py`)

1. **Markdown parsing tests**: Verify the parser correctly extracts header, sections, and subsections from valid recap markdown
2. **Edge case parsing**: Empty sections, special characters, unicode content, very long content
3. **CLI argument tests**: Default paths, custom paths, missing input file
4. **Error handling tests**: Missing fpdf2, empty file, malformed markdown

### Property-Based Tests (Hypothesis)

1. **Append preservation**: Generate arbitrary existing recap content + new sections, verify existing content preserved
2. **Structural completeness**: Generate module data, verify all required subsections present
3. **Timestamp format**: Generate dates, verify ISO 8601 compliance
4. **Q&A pairing**: Generate Q&A pairs, verify 1:1 correspondence in output
5. **Round-trip**: Generate recap markdown, parse it, verify structure matches
6. **Duration monotonicity**: Generate sequences of appends, verify total duration non-decreasing
7. **Module ordering**: Generate completion sequences, verify chronological order in output

### Integration Tests

1. **Hook detection**: Verify hook fires only on new module completions
2. **Workflow ordering**: Verify recap appears before journal entry in output
3. **Graduation flow**: Verify PDF generation step executes at correct point

## Correctness Properties

### Property 1: Append Preserves Existing Content

For all valid existing Recap_Document content and all valid new Recap_Sections, appending a section to the document preserves all previously written content byte-for-byte. The new content appears only after the existing content.

**Validates: Requirements 1.2, 3.2**

### Property 2: Recap Section Structural Completeness

For all valid module completion data (module number, name, timestamp, information list, Q&A pairs, actions list, duration), the generated Recap_Section contains exactly the required subsections in order: "Information Shared", "Questions Asked", "Answers Given", "Actions Taken", "Duration".

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

### Property 3: ISO 8601 Timestamp Format Validity

For all generated timestamps in the Recap_Document (header start date, per-module completion dates, duration updates), each timestamp matches the ISO 8601 format with timezone offset (`YYYY-MM-DDTHH:MM:SS±HH:MM`).

**Validates: Requirements 7.1, 7.2**

### Property 4: Question-Answer Pairing Integrity

For all sets of questions and answers provided to the recap generator, the output "Answers Given" section contains exactly one answer per question, and the ordering of answers corresponds to the ordering of questions in the "Questions Asked" section.

**Validates: Requirements 2.4, 4.2, 4.3**

### Property 5: PDF Round-Trip Semantic Preservation

For all valid Recap_Document markdown content, converting to PDF and extracting the text content preserves the semantic structure: all module headings appear in order, all subsection headings appear within their parent module, and all list items are present.

**Validates: Requirements 5.2, 6.7**

### Property 6: Duration Monotonic Increase

For all sequences of Recap_Section appends, the "Total Duration" value in the document header is monotonically non-decreasing — each append results in a total duration greater than or equal to the previous value.

**Validates: Requirements 7.4**

### Property 7: Module Ordering Preservation

For all sequences of module completions appended to the Recap_Document, the module sections appear in the document in chronological order of their completion timestamps.

**Validates: Requirements 3.1, 7.2**

## Edge Cases

1. **Empty module session**: A module completed with no questions asked (e.g., a skipped module) — sections should still be present but may contain "None" or be empty lists
2. **Very long session**: A module with 50+ questions and extensive actions — the recap should handle arbitrary-length content without truncation
3. **Special characters in answers**: Bootcamper responses containing markdown special characters (`#`, `*`, `|`, backticks) — must be escaped or handled correctly
4. **Concurrent file access**: If the recap file is open in an editor while being appended — the append should still succeed
5. **Module re-completion**: If a module is completed again (quality feedback loop from Module 7 back to Module 5) — a new section should be appended, not replacing the original
6. **Missing preferences file**: If `config/bootcamp_preferences.yaml` doesn't exist — use "Bootcamper" as default name
7. **Unicode content**: Bootcamper names and answers containing non-ASCII characters — must render correctly in both markdown and PDF

## Dependencies

- **Runtime (PDF generation only)**: `fpdf2` — optional, graceful degradation if missing
- **Runtime (recap append)**: Python 3.11+ stdlib only (datetime, pathlib, re)
- **Test**: pytest + Hypothesis (existing test infrastructure)

## Security Considerations

- The recap file may contain bootcamper responses — it should be listed in `.gitignore` recommendations for the user's project (not the power repo)
- The PDF generation script processes only local files — no network access
- No secrets or credentials should appear in recap content (the hook should not capture environment variable values or connection strings)
