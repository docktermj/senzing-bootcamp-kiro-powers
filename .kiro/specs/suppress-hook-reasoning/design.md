# Design Document

## Overview

This feature eliminates hook reasoning narration from the bootcamper-facing conversation by restructuring both hook prompts (`write-policy-gate.kiro.hook` and `question-format-gate.kiro.hook`) with dual suppression reinforcement and strengthening the hook silence rule in `agent-instructions.md`. The approach uses a "sandwich" prompt engineering technique: a front-loaded suppression preamble at the top (within the first 200 characters) and a strict OUTPUT FORMAT section at the bottom, with explicit anti-narration directives enumerating forbidden phrases.

## Architecture

### Prompt Restructuring Strategy

Both hook prompts are restructured with three layers of suppression:

1. **Suppression Preamble (Top)** — Within the first 200 characters, an unconditional directive stating the zero-output requirement. This ensures the LLM processes the constraint before encountering any evaluation logic.

2. **Inline Zero-Output Directives (Middle)** — Existing "Do not acknowledge. Do not explain. Do not print anything." directives remain at each check's fast-path branch, reinforcing silence at the point of decision.

3. **OUTPUT FORMAT Section (Bottom)** — A closing section after all check definitions that restates the output constraints and enumerates specific forbidden phrases. This catches any tendency to narrate after completing evaluation.

### Agent Instructions Reinforcement

The `agent-instructions.md` steering file's existing hook silence rule is strengthened with:
- Enumerated forbidden output patterns
- Explicit zero-visible-tokens language
- Coverage of all hook types (preToolUse, agentStop, future hooks)
- Corrective-output-only rule for slow-path cases

## Components and Interfaces

### 1. Write Policy Gate Prompt (`write-policy-gate.kiro.hook`)

**Changes:**
- Add suppression preamble as the first line of the prompt (before "WRITE POLICY GATE — Three checks in one pass")
- Add explicit anti-narration directive with enumerated forbidden phrases in the FAST PATH GATE section
- Add edge-case instruction for non-SQL content referencing Senzing indicators (JSON configs with connection strings)
- Add closing OUTPUT FORMAT section after CHECK 3
- Preserve all existing CHECK 1 (SQL blocking), CHECK 2 (single-question enforcement), and CHECK 3 (file path policies) logic verbatim

**Prompt Structure (after restructuring):**

```text
⚠️ SILENCE RULE: When all checks pass, produce ZERO tokens. No output. No acknowledgment. Re-invoke the tool silently.

WRITE POLICY GATE — Three checks in one pass.

FAST PATH GATE: If ALL of the following are true, produce no output at all:
- [existing conditions]

Your response when fast path passes: [empty — produce zero tokens]
OUTPUT: (none)
Do NOT output phrases like 'Fast path passes', 'Proceeding', 'All checks pass',
'This is a JSON configuration file', 'Not SQL', or any summary of your evaluation.
Zero tokens means zero tokens.

---

CHECK 1: SENZING SQL BLOCKING
[preserved verbatim — all SQL patterns, Senzing indicators, STOP instruction, SDK alternatives]

IMPORTANT: Only flag content that contains BOTH SQL patterns AND Senzing database indicators.
Content referencing Senzing indicators WITHOUT SQL patterns (e.g., JSON configuration files
with database connection strings) passes silently — zero tokens, no explanation.

---

CHECK 2: SINGLE-QUESTION ENFORCEMENT
[preserved verbatim — all five validation rules, violation output format]

---

CHECK 3: FILE PATH POLICIES
[preserved verbatim — Q1/Q2 quick check, fast path, slow path, content check]

---

OUTPUT FORMAT (STRICT):
- All checks pass → ZERO tokens. Re-invoke the original tool call with same parameters.
- Violation detected → Output ONLY the corrective instruction (STOP message, rewrite, redirect).
FORBIDDEN output (never produce these):
  • "Fast path passes"
  • "Proceeding"
  • "All checks pass"
  • "This is a JSON configuration file"
  • "Not SQL"
  • "The file is inside the working directory"
  • Any text describing, summarizing, or narrating the evaluation process
```

### 2. Question Format Gate Prompt (`question-format-gate.kiro.hook`)

**Changes:**
- Add suppression preamble as the first line of the prompt (before "QUESTION FORMAT GATE")
- Add explicit anti-narration directive with enumerated forbidden phrases
- Add closing OUTPUT FORMAT section after the RULES section
- Preserve all existing detection logic (three patterns), NOT COMPOUND exclusions, and rewrite format

**Prompt Structure (after restructuring):**

```text
⚠️ SILENCE RULE: No-rewrite → output exactly ".". Rewrite → output ONLY the corrected question. Never output reasoning.

QUESTION FORMAT GATE — Inspect the most recent assistant message for compound 👉 questions.

DETECTION: [preserved verbatim — three detection patterns]

NOT COMPOUND (do not flag): [preserved verbatim — exclusion list]

ACTION:
- If NO compound question detected: output only a single period character: .
  Do NOT output "The question is not compound", "No rewrite needed",
  "Scanning for compound questions", or any description of your detection process.
- If a compound question IS detected: rewrite using correct format.
  Do NOT output "This is a compound question", "Let me rewrite",
  "The question contains 'or' joining alternatives", or any explanation of the detection.
  Output ONLY the corrected question text.

RULES: [preserved verbatim — non-interference, no explanations, preserve content]

---

OUTPUT FORMAT (STRICT):
- No compound question found → Output exactly: .
- Compound question found → Output ONLY the rewritten question (neutral lead + numbered list).
  Preserve all non-question content from the original message.
FORBIDDEN output (never produce these):
  • "The question is not compound"
  • "No rewrite needed"
  • "Scanning for compound questions"
  • "This is a compound question"
  • "Let me rewrite"
  • "The question contains 'or' joining alternatives"
  • Any text describing, summarizing, or narrating the detection process
```

### 3. Agent Instructions Hook Silence Rule (`agent-instructions.md`)

**Changes to the existing `🔇 Hook silence rule` paragraph:**

Replace the current single-paragraph rule with a strengthened multi-line rule:

```markdown
**🔇 Hook silence rule:** When a hook check passes with no action needed, produce zero visible
tokens — no acknowledgment, no reasoning, no status, no summary. Only produce output when the
hook identifies a problem requiring corrective action. When a hook produces corrective output
(e.g., a rewritten question, a STOP message), output ONLY the corrective content with no
preamble or explanation of why the correction was made. This applies to ALL hook types:
preToolUse hooks, agentStop hooks, and any future hook types added to the power.

FORBIDDEN hook reasoning output (never produce these after any hook fires):
- "Fast path passes"
- "Proceeding"
- "All checks pass"
- "The question is not compound"
- "No rewrite needed"
- "This is a JSON configuration file"
- "Not SQL"
- "The file is inside the working directory"
- "Scanning for compound questions"
- Any text that describes, summarizes, or narrates the hook's internal evaluation process
```

### Hook File JSON Schema (unchanged)

Both hook files maintain the existing JSON schema:

```json
{
  "name": "string (user-facing, 'to {verb phrase}' pattern)",
  "version": "1.0.0",
  "description": "string",
  "when": {
    "type": "preToolUse | agentStop",
    "toolTypes": ["write"]  // only for preToolUse
  },
  "then": {
    "type": "askAgent",
    "prompt": "string (restructured prompt text)"
  }
}
```

### Prompt Output Contract

| Scenario | Write Policy Gate Output | Question Format Gate Output |
|----------|--------------------------|----------------------------|
| Fast path (all checks pass) | Zero tokens + silent re-invocation | Single period: `.` |
| SQL violation detected | STOP message + SDK alternatives | N/A |
| Compound question in `.question_pending` | Violation message + rewrite instruction | N/A |
| External path detected | STOP message + project-relative redirect | N/A |
| Misrouted feedback | STOP message + canonical path redirect | N/A |
| Compound 👉 question detected | N/A | Rewritten question only |

## Data Models

No new data models are introduced. The feature modifies prompt text within existing JSON hook files and markdown steering files.

### Modified Files

| File | Change Type |
|------|-------------|
| `senzing-bootcamp/hooks/write-policy-gate.kiro.hook` | Prompt restructured with dual reinforcement |
| `senzing-bootcamp/hooks/question-format-gate.kiro.hook` | Prompt restructured with dual reinforcement |
| `senzing-bootcamp/steering/agent-instructions.md` | Hook silence rule strengthened |
| `tests/test_suppress_policy_pass_output.py` | Extended with new property tests |
| `tests/test_hook_silent_fast_path_properties.py` | Extended with new property tests |

## Error Handling

### Prompt Parsing Edge Cases

- **Empty content writes**: The fast path still applies — zero tokens output.
- **Content with Senzing indicators but no SQL**: Explicitly handled as fast-path edge case — zero tokens output, no explanation about why it's not SQL.
- **Mixed content (SQL + non-Senzing tables)**: The existing "IMPORTANT: Only flag content that contains BOTH SQL patterns AND Senzing database indicators" rule is preserved verbatim.

### Test Failure Modes

- If the suppression preamble is accidentally removed, tests checking the first 200 characters will fail.
- If the OUTPUT FORMAT section is removed, structural position tests will fail.
- If forbidden phrases are removed from the anti-narration directives, enumeration tests will fail.
- If slow-path logic is altered, baseline comparison tests will fail.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Write Policy Gate front-loaded suppression preamble

*For any* valid Write_Policy_Gate prompt, the first 200 characters of the prompt text SHALL contain an explicit zero-output directive (such as "ZERO tokens", "No output", or "produce no output").

**Validates: Requirements 1.2, 6.1, 6.5**

### Property 2: Write Policy Gate closing OUTPUT FORMAT section

*For any* valid Write_Policy_Gate prompt, there SHALL exist an "OUTPUT FORMAT" section that appears after all CHECK sections (CHECK 1, CHECK 2, CHECK 3) and contains both a zero-output directive for passing checks and a list of forbidden narration patterns.

**Validates: Requirements 1.3, 6.2**

### Property 3: Write Policy Gate anti-narration directives

*For any* valid Write_Policy_Gate prompt, the prompt text SHALL contain explicit anti-narration directives that enumerate forbidden phrases including "Fast path passes", "Proceeding", and "All checks pass".

**Validates: Requirements 1.4, 1.5**

### Property 4: Write Policy Gate edge-case Senzing indicator suppression

*For any* valid Write_Policy_Gate prompt, the prompt text SHALL contain an explicit instruction that content referencing Senzing database indicators WITHOUT SQL patterns passes silently with zero tokens and no explanation.

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 5: Question Format Gate front-loaded suppression preamble

*For any* valid Question_Format_Gate prompt, the first 200 characters of the prompt text SHALL contain an explicit output constraint directive (referencing "." for no-rewrite and "corrected question" for rewrite, with "never" reasoning).

**Validates: Requirements 3.2, 6.3, 6.5**

### Property 6: Question Format Gate closing OUTPUT FORMAT section

*For any* valid Question_Format_Gate prompt, there SHALL exist an "OUTPUT FORMAT" section that appears after the RULES section and contains both the period-only directive for no-rewrite and the corrected-question-only directive for rewrite, plus a list of forbidden narration patterns.

**Validates: Requirements 3.3, 3.4, 6.4**

### Property 7: Question Format Gate rewrite-only output directive

*For any* valid Question_Format_Gate prompt, the prompt text SHALL contain explicit instructions forbidding preamble or explanation when outputting a rewritten question, and SHALL instruct preservation of non-question content.

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 8: Agent Instructions strengthened hook silence rule

*For any* valid Agent_Instructions file, the hook silence rule SHALL enumerate specific forbidden output patterns (including "Fast path passes", "Proceeding", "The question is not compound", "All checks pass", "This is a JSON configuration file"), state zero-visible-tokens for passing checks, state corrective-only output for violations, and explicitly apply to all hook types (preToolUse, agentStop).

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

### Property 9: Write Policy Gate SQL blocking preservation

*For any* Senzing database indicator in the set {G2C.db, RES_ENT, OBS_ENT, DSRC_RECORD, LIB_FEAT, RES_FEAT_STAT, RES_REL, SZ_, sz_dm_}, the Write_Policy_Gate prompt SHALL contain that indicator, a STOP instruction, and SDK method alternatives (get_entity, search_by_attributes, why_entities, how_entity).

**Validates: Requirements 7.1**

### Property 10: Write Policy Gate single-question enforcement preservation

*For any* valid Write_Policy_Gate prompt, the prompt SHALL contain all five single-question validation rules (exactly one question mark, no conjunctions joining questions, no appended alternatives, unambiguous yes/no, no follow-up after confirmation) and the compound question violation output format.

**Validates: Requirements 7.2**

### Property 11: Write Policy Gate file path policy preservation

*For any* valid Write_Policy_Gate prompt, the SLOW PATH section SHALL remain character-for-character identical to the established baseline, preserving external path blocking, feedback redirect to the canonical path, and content path checking.

**Validates: Requirements 7.3**

### Property 12: Question Format Gate detection logic preservation

*For any* valid Question_Format_Gate prompt, the prompt SHALL contain all three compound question detection patterns (sentence-starter Or, inline prose or, appended alternative) and the complete NOT COMPOUND exclusion list.

**Validates: Requirements 7.4, 7.5**

## Testing Strategy

### Test File Organization

Tests extend two existing files in `tests/`:

| Test File | New Test Classes | Validates |
|-----------|-----------------|-----------|
| `test_suppress_policy_pass_output.py` | `TestDualReinforcementStructure`, `TestAgentInstructionsHookSilence` | Properties 1, 2, 8 |
| `test_hook_silent_fast_path_properties.py` | `TestQuestionFormatGateSuppression`, `TestAntiNarrationDirectives` | Properties 3, 4, 5, 6, 7 |

### Test Configuration

- All new property tests use `@settings(max_examples=20)`
- Class-based organization with docstrings documenting validated requirements
- Hypothesis strategies parameterize over file paths, Senzing indicators, and forbidden phrases
- Existing preservation tests (Properties 9-12) are already covered by the current test classes

### Dual Testing Approach

- **Property tests**: Validate structural invariants of prompt text (preamble position, OUTPUT FORMAT existence, forbidden phrase enumeration) across generated inputs
- **Unit tests**: Existing tests already cover specific examples (external paths, feedback redirect, SQL blocking) — no new unit tests needed
