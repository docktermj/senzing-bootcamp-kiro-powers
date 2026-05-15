# Design Document: Disambiguate Compound Questions

## Overview

This design eliminates compound questions from the bootcamp's steering files and conversation protocol. A compound question is one where a short answer ("yes"/"no") has multiple valid interpretations because the prompt contains two or more semantically distinct sub-questions.

The fix has three parts:

1. **Protocol update**: Add a "Question Disambiguation" rule to `conversation-protocol.md` and reinforce it in `agent-instructions.md`.
2. **Steering file sweep**: Rewrite all compound questions found in steering files to be single, unambiguous questions.
3. **Automated guard**: Add a property-based test that scans steering files for compound question patterns and fails if any are found.

### Design Decisions

- **Confirmation-first pattern**: When the agent needs both confirmation and correction input, it asks confirmation first. If the bootcamper says "no" (or equivalent), the agent asks "What would you like to change?" in the next turn. This eliminates the need to combine "Does this look right?" with "Anything to fix?"
- **Test uses regex heuristics**: The automated test uses pattern matching (question mark followed by another question starter) rather than NLP. This is sufficient because steering file questions are structured and predictable.
- **No structural changes**: Unlike the `standardize-multi-question-steps` spec (which splits steps into sub-steps), this spec only rewrites question text within existing steps. The step structure remains unchanged.
- **Existing STOP markers preserved**: All rewritten questions retain their existing `🛑 STOP` markers and `config/.question_pending` behavior.

## Architecture

No new files or components are created. Changes are limited to:

```
senzing-bootcamp/steering/
├── conversation-protocol.md          # MODIFIED: add Question Disambiguation section
├── agent-instructions.md             # MODIFIED: add disambiguation bullet
├── module-01-business-problem.md     # MODIFIED: rewrite Step 9 question
├── module-01-phase2-document-confirm.md  # MODIFIED: rewrite Step 16 question
└── [other files identified by audit] # MODIFIED: rewrite compound questions

senzing-bootcamp/tests/
└── test_question_disambiguation.py   # NEW: automated compound question detector
```

## Components and Interfaces

### Conversation Protocol Update

Add a new section "Question Disambiguation" after the existing "Choice Formatting" section:

```markdown
## Question Disambiguation

Every 👉 question must have exactly one unambiguous meaning for each possible short answer. A "yes" must map to one interpretation. A "no" must map to one interpretation.

**Compound Question anti-pattern:** A 👉 prompt that combines a Confirmation Question with a Follow-Up Question. Example: "Does that look right? Anything I missed?" — "yes" could mean "yes it's right" OR "yes you missed something."

**Rule:** When you need both confirmation and correction input:
1. Ask the confirmation question alone: "👉 Does that capture your situation accurately?"
2. If the bootcamper says yes → proceed to the next step.
3. If the bootcamper says no → ask "👉 What would you like me to change?" in the next turn.

Never append "or should we adjust anything?" or "Anything I missed?" to a confirmation question. Never combine "Would you like X?" with "Or would you prefer Y?" in prose — use a numbered choice list instead.
```

### Violation Examples Addition

Add to the existing Violation Examples section:

```markdown
### Compound Confirmation (WRONG)

> 👉 Does that summary sound right? Anything I missed or got wrong?

### Compound Confirmation (CORRECT)

> 👉 Does that summary capture your situation accurately?

### Compound Either/Or (WRONG)

> 👉 Would you like me to create a one-page executive summary, or would you prefer to skip that and move on to Module 2?

### Compound Either/Or (CORRECT)

> 👉 What would you like to do next?
>
> 1. Create a one-page executive summary
> 2. Move on to Module 2
```

### Agent Instructions Update

Add to the Communication section bullet list:

```markdown
- Every 👉 question must have one unambiguous meaning for "yes" and one for "no." Never append a follow-up question to a confirmation (see conversation-protocol.md Question Disambiguation). When both confirmation and correction are needed: confirm first, ask for corrections only if the answer is no.
```

### Steering File Rewrites

**`module-01-business-problem.md` Step 9:**

Before:
```
Does that sound right? Anything I missed or got wrong?"
```

After:
```
Does that summary capture your situation accurately?"
```

**`module-01-phase2-document-confirm.md` Step 16:**

Before:
```
"Does this accurately capture your problem? Does the [pattern name] pattern seem like a good fit, or should we adjust anything?"
```

After:
```
"Does this accurately capture your problem and approach?"
```

Additional files will be identified by the audit (Requirement 4) and rewritten following the same pattern.

### Automated Test

```python
"""Test that no steering file contains compound 👉 questions.

Feature: disambiguate-compound-questions
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"

# Pattern: a question mark followed (within 80 chars) by a question-starting word
_COMPOUND_PATTERN = re.compile(
    r"\?\s*.{0,80}?\b(Does|Is|Are|Would|Should|Could|Can|Will|Anything|Or\s)\b",
    re.IGNORECASE,
)

# Only check lines that are part of a 👉 question block
_QUESTION_PREFIX = "👉"


class TestQuestionDisambiguation:
    """Feature: disambiguate-compound-questions

    For any 👉 question in any steering file, the question text must not
    contain a compound pattern (two or more question marks indicating
    multiple sub-questions within a single prompt).
    """

    def _find_compound_questions(self) -> list[tuple[str, int, str]]:
        """Scan all steering files for compound 👉 questions.

        Returns:
            List of (filename, line_number, offending_text) tuples.
        """
        violations: list[tuple[str, int, str]] = []

        for md_file in sorted(_STEERING_DIR.glob("*.md")):
            lines = md_file.read_text(encoding="utf-8").splitlines()
            in_question_block = False
            question_text = ""
            question_start_line = 0

            for i, line in enumerate(lines, start=1):
                if _QUESTION_PREFIX in line:
                    in_question_block = True
                    question_text = line
                    question_start_line = i
                elif in_question_block:
                    # Question blocks end at blank lines or STOP markers
                    if line.strip() == "" or "🛑" in line or "STOP" in line:
                        # Check the accumulated question text
                        if question_text.count("?") >= 2:
                            if _COMPOUND_PATTERN.search(question_text):
                                violations.append(
                                    (md_file.name, question_start_line, question_text.strip())
                                )
                        in_question_block = False
                        question_text = ""
                    else:
                        question_text += " " + line

            # Check final block if file doesn't end with blank line
            if in_question_block and question_text.count("?") >= 2:
                if _COMPOUND_PATTERN.search(question_text):
                    violations.append(
                        (md_file.name, question_start_line, question_text.strip())
                    )

        return violations

    def test_no_compound_questions_in_steering_files(self) -> None:
        """All 👉 questions in steering files must be single, unambiguous questions."""
        violations = self._find_compound_questions()

        if violations:
            msg_parts = ["Compound questions found in steering files:\n"]
            for filename, line_num, text in violations:
                msg_parts.append(f"  {filename}:{line_num}: {text[:120]}")
            pytest.fail("\n".join(msg_parts))
```

## Correctness Properties

### Property 1: Question Disambiguation Completeness

*For any* 👉 question in any steering file, the question text SHALL contain at most one question mark, OR if it contains multiple question marks, they must not match the compound pattern (a question mark followed by another question-starting word within 80 characters).

**Validates: Requirements 1.1, 4.4, 6.1**

### Property 2: Confirmation Question Singularity

*For any* rewritten confirmation question, a "yes" answer SHALL have exactly one interpretation (confirmed/approved) and a "no" answer SHALL have exactly one interpretation (needs changes).

**Validates: Requirements 1.1, 3.3**

### Property 3: Protocol Section Presence

*For any* required protocol section (Question Disambiguation, Compound Confirmation violation example, Compound Either/Or violation example), the `conversation-protocol.md` file SHALL contain that section.

**Validates: Requirements 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4**

## Error Handling

| Scenario | Handling |
|----------|----------|
| Audit finds compound questions in phase files | Rewrite them following the same pattern as root steering files |
| Rewritten question changes token count significantly | Run `measure_steering.py` and update `steering-index.yaml` if needed |
| Test produces false positives (legitimate multi-question-mark text that isn't a compound question) | Add the specific pattern to an allowlist in the test, with a comment explaining why it's not a violation |
| Steering file contains a compound question inside a code block or example section | Test should skip content inside fenced code blocks (``` or ~~~) |

## Testing Strategy

### Automated Test (Property-Based)

**Location:** `senzing-bootcamp/tests/test_question_disambiguation.py`

The test scans all `*.md` files in `senzing-bootcamp/steering/` for 👉 question blocks containing compound patterns. It uses regex heuristics rather than NLP, which is appropriate because steering file questions follow predictable patterns.

**False positive mitigation:**
- Skip content inside fenced code blocks
- Skip lines that are part of "WRONG" violation examples (they intentionally show bad patterns)
- The 80-character window between question marks prevents matching across unrelated sentences

### Manual Verification

After all rewrites:
1. Read each rewritten question and verify "yes" has one meaning and "no" has one meaning.
2. Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to verify token budgets.
3. Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` to verify markdown validity.
4. Run `pytest senzing-bootcamp/tests/` to verify all tests pass including the new one.
