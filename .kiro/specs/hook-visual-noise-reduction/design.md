# Design Document: Hook Visual Noise Reduction

## Overview

This design consolidates four `agentStop` hooks (`ask-bootcamper`, `enforce-step-and-transition`, `mcp-first-invariant`, `question-format-gate`) into a single `ask-bootcamper.kiro.hook` file with four internal phases. It also strengthens the `write-policy-gate.kiro.hook` silence directives to suppress "Fast path passes" narration, and introduces silent self-correction for compound question rewrites so bootcampers only see the clean version.

## Architecture

### Current State (4 agentStop hooks)

```text
Agent Response
  ├── ask-bootcamper.kiro.hook        (closing question + feedback reminder)
  ├── enforce-step-and-transition.kiro.hook  (step sequencing + transition retry)
  ├── mcp-first-invariant.kiro.hook   (MCP-first compliance audit)
  └── question-format-gate.kiro.hook  (compound question detection)
```

Each hook fires independently on every `agentStop` event, producing up to 4 visible outputs in the IDE (even when most are just `.`).

### Target State (1 consolidated agentStop hook)

```text
Agent Response
  └── ask-bootcamper.kiro.hook (v4.0.0)
        ├── Phase 1: Closing_Question_Phase  (existing logic preserved)
        ├── Phase 2: Step_Sequencing_Phase   (from enforce-step-and-transition)
        ├── Phase 3: MCP_First_Phase         (from mcp-first-invariant)
        └── Phase 4: Question_Format_Phase   (from question-format-gate + silent self-correction)
```

A single hook firing produces at most one combined output. When all phases produce no output, the complete response is a single period character: `.`

## Components and Interfaces

### 1. Consolidated Ask_Bootcamper_Hook (`senzing-bootcamp/hooks/ask-bootcamper.kiro.hook`)

**JSON Structure:**

```json
{
  "name": "to wait for your answer",
  "version": "4.0.0",
  "description": "Consolidated agentStop hook with four phases: (1) closing question with feedback nudge, (2) step sequencing enforcement, (3) MCP-first compliance audit, (4) compound question detection with silent self-correction.",
  "when": {
    "type": "agentStop"
  },
  "then": {
    "type": "askAgent",
    "prompt": "<consolidated prompt text>"
  }
}
```

**Phase Execution Order:**

1. **Phase 1 — Closing Question**: Checks if a closing 👉 question is needed. Produces a recap + question only when no question is pending and no 👉 already present.
2. **Phase 2 — Step Sequencing**: Reads `config/bootcamp_progress.json`, detects step-skipping violations and module transition failures.
3. **Phase 3 — MCP-First Compliance**: Scans the most recent assistant response for Senzing content indicators and verifies MCP tool calls were made.
4. **Phase 4 — Question Format**: Detects compound 👉 questions and instructs silent self-correction (regenerate the entire response with the corrected question inline).

**Output Rules:**
- If ALL four phases produce no output → complete response is `.`
- If any phase produces output → that output is the complete response (phases are evaluated in order; first violation wins)
- Phase 4 uses silent self-correction: instructs the agent to regenerate its last response with the corrected question replacing the compound one, so the bootcamper never sees the original compound question

### 2. Silent Self-Correction Mechanism (Question_Format_Phase)

The key behavioral change from the original `question-format-gate.kiro.hook`:

**Original behavior:** Output the rewritten question as a separate message (bootcamper sees both the original compound question and the rewrite).

**New behavior:** Instruct the agent to regenerate its entire last response with the corrected question inline. The bootcamper only sees the clean version.

**Prompt logic for Phase 4:**

```text
PHASE 4: QUESTION FORMAT (SILENT SELF-CORRECTION)

Scan the most recent assistant message for any 👉 question with prose-joined alternatives.

DETECTION PATTERNS:
1. Sentence-starter 'Or': "? Or shall we...", "? Or would you...", "? Or should we..."
2. Inline prose 'or': "[option A] or [option B]?" in a single sentence
3. Appended alternative: ", or would you rather...", ", or shall we..."

NOT COMPOUND (do not flag):
- Simple yes/no with single action
- Already formatted as numbered list
- 'or' inside a numbered list item

If NO compound question detected: Phase 4 output is none.

If compound question IS detected:
REGENERATE your entire last response. Replace the compound 👉 question with a
neutral lead question followed by a numbered list. The bootcamper must only see
the clean version — suppress the original compound question entirely.
Do NOT output the rewrite as a separate message. Rebuild the full response inline.
```

### 3. Write_Policy_Gate Silence Strengthening (`senzing-bootcamp/hooks/write-policy-gate.kiro.hook`)

The existing `write-policy-gate.kiro.hook` already contains silence directives. This change ensures:

1. **Front-loaded preamble** (first 200 chars): `⚠️ SILENCE RULE: When all checks pass, produce ZERO tokens. No output. No acknowledgment.`
2. **FORBIDDEN output list** explicitly includes `"Fast path passes"` as a prohibited phrase
3. **Closing OUTPUT FORMAT section** reiterates zero-token directive and enumerates all forbidden narration phrases

No structural changes to the hook JSON — only prompt text refinements to the existing silence directives (which are already in place per the current file).

### 4. File Deletions

The following files are removed from the repository:
- `senzing-bootcamp/hooks/question-format-gate.kiro.hook`
- `senzing-bootcamp/hooks/enforce-step-and-transition.kiro.hook`
- `senzing-bootcamp/hooks/mcp-first-invariant.kiro.hook`

### 5. Registry Updates

**hook-categories.yaml** — Remove `question-format-gate`, `enforce-step-and-transition`, `mcp-first-invariant` from the `critical` list. `ask-bootcamper` remains.

**hooks.lock.yaml** — Remove entries for the three deleted hooks. Update `ask-bootcamper` entry to version `4.0.0`.

### 6. Steering & Documentation Updates

| File | Change |
|------|--------|
| `steering/hook-registry-critical.md` | Remove standalone entries for deleted hooks; update ask-bootcamper entry with full four-phase prompt |
| `steering/hook-registry.md` | Remove rows for deleted hooks from the quick-reference table |
| `hooks/README.md` | Remove entries for deleted hooks |
| `POWER.md` | Remove references to deleted hooks; adjust hook count |

### 7. Test Migration

Tests that reference the deleted hook files are updated to point at the consolidated hook:

| Original Test File | Change |
|---|---|
| `tests/test_mcp_first_invariant_properties.py` | Update `HOOK_PATH` to `ask-bootcamper.kiro.hook`; extract MCP_First_Phase section from prompt |
| `tests/test_single_question_format.py` | Update `QUESTION_FORMAT_GATE_HOOK` path to `ask-bootcamper.kiro.hook` |
| `tests/test_detect_transition_retry.py` | Update `_HOOK_FILE` path to `ask-bootcamper.kiro.hook` |
| `tests/hook_test_helpers.py` | Update `CRITICAL_HOOKS` list to remove deleted hook IDs |

## Data Models

### Hook JSON Schema (unchanged)

```json
{
  "name": "string (starts with 'to ')",
  "version": "string (semver: major.minor.patch)",
  "description": "string",
  "when": {
    "type": "agentStop | preToolUse | postToolUse | fileEdited | fileCreated | ..."
  },
  "then": {
    "type": "askAgent",
    "prompt": "string (the full prompt text)"
  }
}
```

### hook-categories.yaml (post-consolidation critical section)

```yaml
critical:
  - ask-bootcamper
  - code-style-check
  - commonmark-validation
  - review-bootcamper-input
  - write-policy-gate
```

### hooks.lock.yaml (ask-bootcamper entry)

```yaml
  - id: ask-bootcamper
    version: "4.0.0"
    category: critical
    event_type: agentStop
```

### Hook Prompt Interface

The consolidated hook prompt follows this interface contract:

```text
INPUT:  Agent's most recent response + conversation context + config files
OUTPUT: One of:
  - "." (all phases silent)
  - Closing question text (Phase 1 triggered)
  - Step violation warning (Phase 2 triggered)
  - MCP-first self-correction instructions (Phase 3 triggered)
  - Full response regeneration instruction (Phase 4 triggered)
```

### Phase Priority

Phases are evaluated in order. If Phase 2 or 3 detects a violation, that takes priority over Phase 1's closing question. Phase 4 (question format) operates on the output that would be shown to the bootcamper, so it runs last.

## Error Handling

| Scenario | Behavior |
|----------|----------|
| `config/bootcamp_progress.json` missing | Phase 2 (Step Sequencing) produces no output — skips to next phase |
| `config/.question_pending` missing | Phase 1 condition passes (no question pending) |
| Hook JSON parse failure | Kiro framework reports error; hook does not fire |
| Prompt exceeds token limit | Kiro framework truncates; phases at end may be cut — critical phases (2, 3) placed before Phase 4 |

## Testing Strategy

**Property-based tests** (pytest + Hypothesis, `@settings(max_examples=20)`):
- Validate prompt content preservation by sampling from sets of key phrases (SDK methods, detection patterns, forbidden phrases) and asserting each appears in the consolidated prompt
- Validate structural invariants (JSON schema, phase markers, silence directives) across generated hook variations

**Example-based tests** (pytest):
- File deletion assertions (deleted hooks do not exist on disk)
- Registry entry assertions (lock file and categories file reflect consolidation)
- Version number assertions (ask-bootcamper version > 3.0.0)
- Steering/documentation assertions (deleted hooks absent from reference files)

**Smoke tests**:
- Full test suite passes after all changes (`pytest` exit code 0)

Tests live in `tests/` (repo-level hook tests) per project conventions. Test files reference the consolidated hook path (`senzing-bootcamp/hooks/ask-bootcamper.kiro.hook`) and use `hook_test_helpers.py` for shared utilities.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Consolidated hook contains all four phase markers

*For any* valid Ask_Bootcamper_Hook file, the `then.prompt` field SHALL contain identifiable section markers for all four phases: Closing_Question_Phase (or "PHASE 1"), Step_Sequencing_Phase (or "PHASE 2" with step sequencing logic), MCP_First_Phase (or "PHASE 3" with MCP-first logic), and Question_Format_Phase (or "PHASE 4" with question format logic).

**Validates: Requirements 1.1, 9.4**

### Property 2: Consolidated hook structural validity

*For any* valid Ask_Bootcamper_Hook file, it SHALL parse as valid JSON containing all required keys (`name`, `version`, `description`, `when`, `then`), with `when.type` equal to `"agentStop"` and `then.type` equal to `"askAgent"`, and the `then.prompt` field SHALL be a non-empty string.

**Validates: Requirements 1.3, 9.1, 9.2, 9.3**

### Property 3: Step sequencing and MCP-first logic preservation

*For any* key detection phrase from the original `enforce-step-and-transition.kiro.hook` (transition question patterns, affirmative phrases, step violation output format) and *for any* Senzing content indicator from the original `mcp-first-invariant.kiro.hook` (SDK method names, attribute names, config options, ER terms, MCP tool names), those phrases SHALL appear in the consolidated Ask_Bootcamper_Hook prompt.

**Validates: Requirements 1.4, 1.5**

### Property 4: Question format detection patterns preserved with silent self-correction

*For any* compound-question detection pattern from the original `question-format-gate.kiro.hook` (sentence-starter Or, inline prose or, appended alternative), that pattern description SHALL appear in the consolidated Ask_Bootcamper_Hook prompt, AND the prompt SHALL contain silent self-correction language instructing response regeneration rather than separate-message output.

**Validates: Requirements 1.6, 2.4**

### Property 5: Silent self-correction instructs regeneration and suppression

*For any* valid Ask_Bootcamper_Hook prompt, the Question_Format_Phase section SHALL contain both (a) an instruction to regenerate the entire last response with the corrected question inline, and (b) an instruction to suppress the original compound question from the bootcamper's view.

**Validates: Requirements 2.1, 2.2**

### Property 6: Non-compound case produces no phase output

*For any* valid Ask_Bootcamper_Hook prompt, the Question_Format_Phase section SHALL contain an explicit directive that when no compound question is detected, that phase produces no output (contributing to the default "." response).

**Validates: Requirements 2.3**

### Property 7: Deleted hooks absent from categories file

*For any* deleted hook ID in the set {`question-format-gate`, `enforce-step-and-transition`, `mcp-first-invariant`} and *for any* category in `hook-categories.yaml`, that hook ID SHALL NOT appear in that category's list.

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 8: Write-policy-gate dual-reinforcement suppression structure

*For any* valid Write_Policy_Gate prompt: (a) the first 200 characters SHALL contain an explicit zero-output directive, (b) an OUTPUT FORMAT section SHALL exist after all CHECK sections containing a zero-token directive, and (c) the phrase "Fast path passes" SHALL appear in a FORBIDDEN output list.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4**
