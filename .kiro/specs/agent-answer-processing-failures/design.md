# Design Document

## Overview

This design addresses three manifestations of the agent failing to process bootcamper answers to 👉 questions: (1) track selection answers lost during onboarding, (2) module transition confirmations lost between modules, and (3) the agent proceeding without waiting for the bootcamper's answer. The fix broadens the existing `enforce-step-and-transition` hook's Phase 2 detection, adds answer-processing priority directives to steering files, and introduces a structured `config/.question_pending` file schema with type-specific retry instructions.

## Architecture

The fix touches three layers of the bootcamp power:

1. **Steering Layer** — `agent-instructions.md` and `conversation-protocol.md` gain answer-processing priority directives that instruct the agent to always process pending answers first.
2. **Hook Layer** — `enforce-step-and-transition.kiro.hook` Phase 2 is broadened from module-transition-only detection to all-question-type detection with type-specific retry instructions.
3. **Data Layer** — `config/.question_pending` gains a structured schema (type on first line, question text on subsequent lines) enabling the hook to issue targeted recovery.

```
┌─────────────────────────────────────────────────────────┐
│                   Agent Turn Lifecycle                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Turn starts                                          │
│  2. Agent reads config/.question_pending (if exists)     │
│  3. Agent deletes .question_pending                      │
│  4. Agent processes bootcamper's answer (HIGHEST PRIO)   │
│  5. Agent produces substantive output                    │
│  6. If ending with 👉 question → writes .question_pending│
│  7. Turn ends → agentStop fires                          │
│                                                          │
├─────────────────────────────────────────────────────────┤
│            enforce-step-and-transition hook               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Phase 1: Sequential Step Enforcement (unchanged)        │
│    - Detects step-skipping violations                    │
│    - Detects question-pending + step-advance violations  │
│                                                          │
│  Phase 2: ANSWER PROCESSING RETRY (broadened)            │
│    - Checks: .question_pending exists + minimal output   │
│    - Reads question type from .question_pending          │
│    - Issues type-specific retry instructions             │
│                                                          │
│  Phase 3: NOT-WAITING DETECTION (new)                    │
│    - Checks: .question_pending exists + substantive      │
│      workflow-advancing output (without deletion)        │
│    - Issues discard + wait instructions                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Component 1: Steering File Updates

#### agent-instructions.md — Answer Processing Priority Section

A new section added near the top of the file (after the session-start rule) containing:

- Absolute precedence directive: processing a pending 👉 answer takes priority over all other actions
- Delete-and-process instruction: when `config/.question_pending` exists and bootcamper responded, delete the file and process the answer first
- Protocol violation statement: minimal output after a pending answer = ⛔ mandatory gate violation

#### conversation-protocol.md — Answer Processing Priority Section

A new "Answer Processing Priority" section added before the existing "End-of-Turn Protocol" containing:

- Highest-priority action declaration
- Substantive output requirement when processing an answer
- Treat-as-answer rule: if `.question_pending` exists, treat any bootcamper message as an answer
- No-substantive-output-while-pending rule: while `.question_pending` exists, produce only answer-processing output

### Component 2: Hook Phase 2 Broadening

The `enforce-step-and-transition.kiro.hook` Phase 2 is restructured:

**Removed:**
- Transition_Confirmation detection logic (pattern matching for "Ready for Module", affirmative phrases)
- The prerequisite that the bootcamper's message must be a transition confirmation

**Replaced with:**
- Simple two-condition activation: `config/.question_pending` exists AND agent output is Minimal_Output
- Question type extraction from the file's first line
- Type-specific retry instruction dispatch

**Phase 2 renamed:** "MODULE TRANSITION RETRY" → "ANSWER PROCESSING RETRY"

### Component 3: Not-Waiting Detection (New Phase 3)

A new Phase 3 added to the hook that detects when the agent advances the workflow while a question is still pending:

**Activation conditions:**
- `config/.question_pending` exists
- Agent output is NOT minimal (it's substantive)
- Agent output contains workflow-advancing content (step content, module banners, new 👉 questions)
- The `.question_pending` file was NOT deleted during the turn

**Recovery instructions:**
- Discard premature output
- Acknowledge the pending question
- Wait for bootcamper's response

### Component 4: Question_Pending File Schema

#### Current format (unstructured):
```
What track would you like to follow?
```

#### New format (structured):
```
track_selection
What track would you like to follow?
1. Quick Start (Modules 1-3)
2. Full Bootcamp (Modules 1-11)
```

**Schema:**
- Line 1: Question type (one of: `track_selection`, `module_transition`, `step_question`, `confirmation`, `choice`)
- Lines 2+: Full question text (may be multi-line)
- Default type when undetermined: `step_question`

## Interfaces

### Question_Pending File Format

```python
# Serialization
def write_question_pending(question_type: str, question_text: str) -> str:
    """Serialize a question to the .question_pending file format.
    
    Args:
        question_type: One of 'track_selection', 'module_transition', 
                       'step_question', 'confirmation', 'choice'
        question_text: The full question text (may contain newlines)
    
    Returns:
        File content string with type on first line, text on subsequent lines.
    """
    return f"{question_type}\n{question_text}"


# Deserialization
def parse_question_pending(content: str) -> tuple[str, str]:
    """Parse a .question_pending file into type and text.
    
    Args:
        content: Raw file content
    
    Returns:
        Tuple of (question_type, question_text).
        If type is not recognized, returns ('step_question', full_content).
    """
    lines = content.split('\n', 1)
    if len(lines) >= 2 and lines[0].strip() in VALID_TYPES:
        return (lines[0].strip(), lines[1])
    return ('step_question', content)


VALID_TYPES = {
    'track_selection',
    'module_transition', 
    'step_question',
    'confirmation',
    'choice',
}
```

### Hook Prompt Structure (Phase 2)

```json
{
  "phase2_activation": {
    "condition_1": "config/.question_pending exists",
    "condition_2": "agent output is Minimal_Output"
  },
  "type_dispatch": {
    "track_selection": "Read track choice → update bootcamp_progress.json → save bootcamp_preferences.yaml → begin Module 1",
    "module_transition": "Display module start banner → journey map → before/after framing → begin Step 1",
    "step_question": "Read answer → incorporate into workflow → update progress → present next action",
    "confirmation": "Treat response as confirmation → proceed with confirmed action",
    "choice": "Read selection from numbered list → acknowledge choice → proceed with selected option",
    "unknown": "Re-read bootcamper's message → treat as answer → produce substantive response"
  }
}
```

### Minimal_Output Detection (unchanged from current hook)

Output is Minimal_Output if ANY of these are true:
- Output is exactly "."
- Output is empty or whitespace-only
- Output length is fewer than 50 characters
- Output is a single-word acknowledgment (e.g., "OK", "Sure", "Got it", "Understood", "Great")

## Data Models

### Question_Pending File

| Field | Location | Type | Required | Description |
|-------|----------|------|----------|-------------|
| type | Line 1 | string enum | Yes | One of: `track_selection`, `module_transition`, `step_question`, `confirmation`, `choice` |
| text | Lines 2+ | string | Yes | Full question text, may be multi-line |

### Retry Instructions by Type

| Question Type | Required Recovery Actions |
|---------------|--------------------------|
| `track_selection` | Read track choice, update `bootcamp_progress.json` with selected track, save preferences to `bootcamp_preferences.yaml`, begin Module 1 |
| `module_transition` | Display module start banner (━━━ 🚀🚀🚀 format), journey map table, before/after framing, begin Step 1 |
| `step_question` | Read answer, incorporate into current step workflow, update progress, present next action or question |
| `confirmation` | Treat response as confirmation, proceed with confirmed action |
| `choice` | Read selection from numbered choice list, acknowledge choice, proceed with selected option |
| (unknown/fallback) | Re-read bootcamper's most recent message, treat as answer to pending question, produce substantive response |

## Error Handling

### Malformed Question_Pending File

If `config/.question_pending` exists but cannot be parsed (empty file, no recognizable type on first line):
- Default to `step_question` type
- Use the entire file content as the question text
- Issue generic retry instructions

### Missing Question_Pending File

If `config/.question_pending` does not exist when the hook fires:
- Phase 2 (Answer Processing Retry) produces no output
- Phase 3 (Not-Waiting Detection) produces no output
- Only Phase 1 (Sequential Step Enforcement) evaluates

### Hook Prompt Size Constraints

The hook prompt must remain within reasonable token limits. The type-specific retry instructions are kept concise (1-2 sentences each) to avoid bloating the prompt. The full prompt structure follows the existing pattern of conditional evaluation with early-exit "no output" paths.

## Testing Strategy

### Property-Based Tests (pytest + Hypothesis)

Property-based tests validate the core logic that can be exercised programmatically:

1. **Question_Pending round-trip** — Generate random question types and multi-line question texts, serialize to the file format, parse back, and verify identity. This validates the schema is unambiguous and lossless.
2. **Hook prompt structural validation** — Parse the hook JSON and verify Phase 2 activation conditions, type-specific retry blocks, and absence of old Transition_Confirmation prerequisites across generated question types.
3. **Minimal_Output classification** — Generate strings and verify the minimal output detection logic correctly classifies them (empty, ".", whitespace-only, <50 chars, single-word acks).

### Example-Based Tests (pytest)

Example-based tests verify static content requirements in steering files and hook JSON:

- `agent-instructions.md` contains the answer-processing priority directive
- `conversation-protocol.md` contains the "Answer Processing Priority" section
- Hook Phase 2 is named "ANSWER PROCESSING RETRY" (not "MODULE TRANSITION RETRY")
- Hook prompt contains all five type-specific retry instruction blocks plus the fallback
- Hook prompt contains not-waiting violation detection logic

### Test Location

Per project conventions:
- Hook prompt validation tests → `tests/` (repo-level, validates real hook files)
- Question_pending schema tests → `senzing-bootcamp/tests/` (power tests)

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Phase 2 Activation Broadening

For any valid question type stored in `config/.question_pending`, the hook's Phase 2 activation logic SHALL trigger on the combination of (question_pending file exists AND minimal output detected) without requiring a Transition_Confirmation pattern match as a prerequisite. The old patterns ("Ready for Module", "move on to Module", "proceed to Module" + affirmative response matching) SHALL NOT appear as Phase 2 activation conditions.

**Validates: Requirements 3.1, 3.3, 3.4**

### Property 2: Type-Specific Retry Instruction Completeness

For any known question type in the set {`track_selection`, `module_transition`, `step_question`, `confirmation`, `choice`}, the hook prompt SHALL contain a distinct retry instruction block that references the required recovery actions for that type. Additionally, for any content where the question type cannot be determined (not in the valid set), the hook prompt SHALL contain a generic fallback retry instruction.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**

### Property 3: Question_Pending File Round-Trip

For any valid question type and any non-empty question text, serializing to the question_pending format (type on first line, text on subsequent lines) and then parsing back SHALL yield the original question type and original question text.

**Validates: Requirements 5.1, 5.2, 5.3**

### Property 4: Not-Waiting Violation Detection

For any agent output that contains workflow-advancing content (step headers, module banners, or new 👉 questions) while `config/.question_pending` exists and was not deleted, the hook SHALL flag this as a not-waiting violation and issue instructions to discard the premature output and wait for the bootcamper's response.

**Validates: Requirements 6.1, 6.2**
