# Design Document

## Overview

This design addresses the minimal-output bug where the agent produces only "." or a bare acknowledgment after a bootcamper confirms a module transition. The solution uses a two-layer defense: (1) strengthened steering language across three files to prevent the behavior, and (2) a detect-and-retry agentStop hook that catches violations and forces the agent to retry with proper module start content.

## Architecture

The feature modifies three existing steering files and adds one new hook file. No new scripts, no runtime dependencies, no code generation. All changes are to Markdown steering content and a JSON hook definition.

```text
┌─────────────────────────────────────────────────────────────┐
│                    Agent Response Pipeline                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Bootcamper sends Transition_Confirmation                 │
│                         │                                    │
│                         ▼                                    │
│  2. Agent reads steering rules (Layer 1 - Prevention)        │
│     ├── agent-instructions.md: Module Transition Execution   │
│     ├── conversation-protocol.md: Minimum Content Rule       │
│     └── module-transitions.md: Confirmation Response Reqs    │
│                         │                                    │
│                         ▼                                    │
│  3. Agent generates response                                 │
│                         │                                    │
│                         ▼                                    │
│  4. agentStop hook fires (Layer 2 - Enforcement)             │
│     └── detect-transition-retry.kiro.hook                    │
│         ├── Is message a Transition_Confirmation? ──No──→ "."│
│         ├── Is output > 50 chars + substantive? ──Yes──→ "." │
│         └── Output is minimal? ──Yes──→ RETRY instruction    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Component 1: Steering File Modifications

#### 1A: conversation-protocol.md — Module Transition Protocol Section

**Change**: Add a "Minimum Content Requirement" rule to the existing Module Transition Protocol section, after the existing paragraph and before the ⛔ PROHIBITED rule.

**New content to insert**:

```markdown
**📏 MINIMUM CONTENT REQUIREMENT:** After receiving a Transition_Confirmation, the agent response MUST contain:
1. The module start banner (━━━ header with module number and name)
2. The journey map table (Module | Name | Status)
3. The before/after framing
4. Step 1's introductory content (what and why)

Outputting only ".", empty content, single-word acknowledgments, or any response under 50 characters after a Transition_Confirmation is a **protocol violation**. The detect-and-retry hook will catch and correct such violations automatically.
```

**Constraint**: All existing rules (⛔ PROHIBITED, 🔒 COMMITMENT RULE, ⚠️ CONTEXT-LIMIT GUIDANCE) remain unchanged.

#### 1B: agent-instructions.md — Module Transition Execution Rule

**Change**: Add a new `## Module Transition Execution` section after the `## Communication` section.

```markdown
## Module Transition Execution

When a bootcamper responds affirmatively to a module transition question ("Ready for Module X?"), the ONLY valid response is to start that module immediately:

1. Display the module start banner
2. Display the journey map
3. Display the before/after framing
4. Begin Step 1 with its introductory content

**⛔ ZERO TOLERANCE:** Producing only ".", an empty response, a single-word acknowledgment, or any output under 50 characters after a Transition_Confirmation is a critical protocol violation. The detect-and-retry hook will force a retry, but the agent must not rely on the hook — produce correct output on the first attempt.

This rule takes precedence over any other agent-internal reasoning (context budget, token limits, perceived completion) when a Transition_Confirmation has been received.
```

#### 1C: module-transitions.md — Confirmation Response Requirements Section

**Change**: Add a new `## Confirmation Response Requirements` section after the existing `## Transition Integrity` section.

```markdown
## Confirmation Response Requirements

When the bootcamper confirms a module transition (responds affirmatively to "Ready for Module X?"), the agent response MUST include all of the following:

| Required Element | Description | Minimum |
|-----------------|-------------|---------|
| Module Start Banner | ━━━ header with 🚀🚀🚀 MODULE N: NAME 🚀🚀🚀 | Exact format from Module Start Banner section |
| Journey Map | Table with Module, Name, Status columns | All modules in selected path |
| Before/After Framing | What you have now / what you'll have when done | From module steering file |
| Step 1 Introduction | "Next up: [action]. This matters because [reason]." | At least one sentence |

**Total response must exceed 50 characters.** This is a hard minimum — the actual response will be significantly longer given the required elements above.

**Violations that trigger the detect-and-retry hook:**
- Output is only "." (single period)
- Output is empty or whitespace-only
- Output is a single-word acknowledgment ("OK", "Sure", "Got it")
- Output is fewer than 50 characters total
- Output lacks the module start banner

The hook will instruct the agent to retry with full module start content. The agent should produce correct output on the first attempt to avoid the retry overhead.
```

### Component 2: Detect-and-Retry Hook

**File**: `senzing-bootcamp/hooks/detect-transition-retry.kiro.hook`

**Hook ID**: `detect-transition-retry`

**Structure**:

```json
{
  "name": "to detect minimal output after module transition confirmation and force retry",
  "version": "1.0.0",
  "description": "agentStop hook that checks if the bootcamper's last message was a module transition confirmation. If so, validates that the agent produced substantive output (>50 chars with module start content). If output is minimal, instructs the agent to retry with full module banner, journey map, and Step 1 content.",
  "when": {
    "type": "agentStop"
  },
  "then": {
    "type": "askAgent",
    "prompt": "<prompt-content>"
  }
}
```

**Hook Prompt Logic** (structured pseudocode):

```text
DETECT-AND-RETRY — Module Transition Confirmation Enforcement

STEP 1: Determine if the bootcamper's most recent message is a Transition_Confirmation.

A message is a Transition_Confirmation if BOTH conditions are true:
  A) The conversation context contains a recent question matching:
     - "Ready for Module" OR "move on to Module" OR "proceed to Module"
  B) The bootcamper's response is an affirmative phrase matching any of:
     - "yes", "sure", "ready", "let's go", "let's do it", "yep", "yeah",
       "absolutely", "go ahead", "proceed", "ok", "okay", "sounds good",
       "let's", "do it", "I'm ready", "go for it"
     (Case-insensitive. May appear with surrounding text.)

If the message is NOT a Transition_Confirmation:
  → Output only: .

STEP 2: If the message IS a Transition_Confirmation, evaluate the agent's output.

The output is Minimal_Output if ANY of these are true:
  - Output is exactly "."
  - Output is empty or whitespace-only
  - Output length is fewer than 50 characters
  - Output is a single-word acknowledgment (e.g., "OK", "Sure", "Got it",
    "Understood", "Great")

If the output is NOT Minimal_Output (exceeds 50 characters with substantive content):
  → Output only: .

STEP 3: If the output IS Minimal_Output after a Transition_Confirmation:
  → Output retry instructions telling the agent to start the confirmed module
     with full Module_Banner, journey map, before/after framing, and Step 1.
```

### Component 3: Hook Registration

**File**: `senzing-bootcamp/hooks/hook-categories.yaml`

**Change**: Add `detect-transition-retry` to the `critical` category, since this hook must be active during all module sessions (not tied to a specific module).

```yaml
critical:
  - ask-bootcamper
  - code-style-check
  - commonmark-validation
  - detect-transition-retry
  - question-format-gate
  - review-bootcamper-input
  - write-policy-gate
```

### Interfaces

#### Hook Input/Output Interface

The detect-and-retry hook operates on the implicit conversation context available to agentStop hooks:

| Input | Source | Description |
|-------|--------|-------------|
| Bootcamper's last message | Conversation history | The most recent user message |
| Agent's last output | Conversation history | The response that just completed |
| Prior assistant message | Conversation history | Used to detect if a transition question was asked |

| Output | Condition | Description |
|--------|-----------|-------------|
| `"."` | No transition confirmation detected | Pass-through, no action |
| `"."` | Confirmation detected, output is substantive | Pass-through, output acceptable |
| Retry instructions | Confirmation detected, output is minimal | Full instructions to start the module |

#### Steering File Interface

The three steering files work together through shared terminology:

- `agent-instructions.md` defines the **rule** (Module Transition Execution)
- `conversation-protocol.md` defines the **protocol** (Minimum Content Requirement within Module Transition Protocol)
- `module-transitions.md` defines the **specification** (Confirmation Response Requirements with exact content expectations)

All three reference the same 50-character threshold and the same list of violation patterns.

## Data Models

No persistent data models are introduced. The hook operates statelessly on conversation context. The only data structures are:

### Transition Confirmation Pattern Set

```python
TRANSITION_QUESTION_PATTERNS = [
    "Ready for Module",
    "move on to Module",
    "proceed to Module",
]

AFFIRMATIVE_PHRASES = [
    "yes", "sure", "ready", "let's go", "let's do it",
    "yep", "yeah", "absolutely", "go ahead", "proceed",
    "ok", "okay", "sounds good", "let's", "do it",
    "I'm ready", "go for it",
]

MINIMAL_OUTPUT_THRESHOLD = 50  # characters
```

### Minimal Output Classification

```python
def is_minimal_output(output: str) -> bool:
    """Classify agent output as minimal (violation) or substantive (acceptable)."""
    stripped = output.strip()
    if stripped == ".":
        return True
    if stripped == "":
        return True
    if len(stripped) < MINIMAL_OUTPUT_THRESHOLD:
        return True
    # Single-word acknowledgments
    single_word_acks = {"ok", "okay", "sure", "got it", "understood", "great", "thanks"}
    if stripped.lower() in single_word_acks:
        return True
    return False
```

### Transition Confirmation Detection

```python
def is_transition_confirmation(message: str, prior_assistant_message: str) -> bool:
    """Detect if a message is an affirmative response to a module transition question."""
    # Check if prior assistant message contained a transition question
    has_transition_question = any(
        pattern.lower() in prior_assistant_message.lower()
        for pattern in TRANSITION_QUESTION_PATTERNS
    )
    if not has_transition_question:
        return False
    
    # Check if the bootcamper's message is affirmative
    message_lower = message.lower().strip()
    return any(
        phrase in message_lower
        for phrase in AFFIRMATIVE_PHRASES
    )
```

## Error Handling

### Hook Failure Modes

| Scenario | Behavior | Rationale |
|----------|----------|-----------|
| Hook cannot determine conversation context | Output "." (pass-through) | Fail open — don't block the agent |
| Hook misidentifies a non-transition message as confirmation | Output "." if output is substantive | Only triggers retry on minimal output, limiting false positive impact |
| Hook fires but agent already produced correct output | Output "." (pass-through) | No-op when output exceeds threshold |
| Multiple hooks fire on same agentStop | Each hook operates independently | Standard hook behavior — no conflicts with existing hooks |

### Steering Conflict Resolution

The new rules are additive — they don't contradict existing rules. Priority order if ambiguity arises:

1. `agent-instructions.md` Module Transition Execution (highest — always-loaded)
2. `conversation-protocol.md` Minimum Content Requirement (auto-loaded during active modules)
3. `module-transitions.md` Confirmation Response Requirements (always-loaded)
4. Hook enforcement (last resort — catches what steering missed)

## Testing Strategy

### Property-Based Tests (pytest + Hypothesis)

Property-based tests validate the core detection logic using randomized inputs:

1. **Minimal output classifier** — Generate random strings of varying lengths, content types (periods, whitespace, words, multi-line text), and verify the classifier boundary at 50 characters is correct.
2. **Transition confirmation recognizer** — Generate random (prior_message, response) pairs mixing transition question patterns with affirmative/non-affirmative phrases, verify correct classification.
3. **Hook decision matrix** — Generate all combinations of (confirmation/non-confirmation) × (minimal/substantive output) and verify the hook produces the correct action (retry vs ".").

### Example-Based Tests (pytest)

Example-based tests verify structural and content requirements:

1. **Hook file schema** — Parse `detect-transition-retry.kiro.hook` as JSON, verify required fields exist with correct values.
2. **Hook naming convention** — Verify the `name` field starts with "to ".
3. **Hook registration** — Verify `detect-transition-retry` appears in `hook-categories.yaml` under `critical`.
4. **Steering file content** — Verify each modified steering file contains the required new sections/rules while retaining existing content.

### Test Location

Tests live in `tests/` (repo-level) since they validate hook files and steering content that ships with the power.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Minimal Output Classification Correctness

*For any* string, the minimal output classifier SHALL return `True` if and only if the string is empty, whitespace-only, exactly ".", a single-word acknowledgment, or fewer than 50 characters in length; and SHALL return `False` for all strings that are 50 or more characters and not a single-word acknowledgment.

**Validates: Requirements 1.2, 1.3, 2.1**

### Property 2: Transition Confirmation Recognition

*For any* pair of (prior_assistant_message, bootcamper_message), the transition confirmation detector SHALL return `True` if and only if the prior assistant message contains a transition question pattern ("Ready for Module", "move on to Module", or "proceed to Module") AND the bootcamper message contains an affirmative phrase from the recognized set; and SHALL return `False` otherwise.

**Validates: Requirements 4.2, 4.6**

### Property 3: Hook Decision Logic Completeness

*For any* combination of (is_transition_confirmation, is_minimal_output), the hook decision logic SHALL produce retry instructions if and only if `is_transition_confirmation` is `True` AND `is_minimal_output` is `True`; and SHALL produce "." in all other cases (not a confirmation, or confirmation with substantive output).

**Validates: Requirements 4.3, 4.4, 4.5**

### Property 4: Hook File Schema Validity

*For any* valid hook file in the `senzing-bootcamp/hooks/` directory, the JSON SHALL parse successfully and contain all required fields (`name`, `version`, `description`, `when`, `then`) with `when.type` being a valid hook event type and `then.type` being a valid action type.

**Validates: Requirements 5.2, 5.4, 5.5**
