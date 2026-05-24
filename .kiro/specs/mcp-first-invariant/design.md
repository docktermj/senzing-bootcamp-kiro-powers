# Design Document

## Overview

This design implements the MCP-First Invariant enforcement system through two complementary mechanisms: a strengthened MCP Rules section in `agent-instructions.md` with explicit invariant language, and a new `agentStop` hook (`mcp-first-invariant.kiro.hook`) that audits agent responses post-hoc using a fast-path/slow-path pattern.

## Architecture

The system operates as a two-layer defense:

1. **Preventive Layer** — Strengthened steering rules in `agent-instructions.md` that establish MCP-first as an unconditional invariant with the same precedence as mandatory gate rules.
2. **Detective Layer** — An `agentStop` hook that fires after every agent response, checks for Senzing content indicators, verifies MCP tool calls occurred, and triggers self-correction when violations are detected.

```
Agent Response Complete
        │
        ▼
┌─────────────────────────┐
│  mcp-first-invariant    │
│  agentStop hook fires   │
└─────────────────────────┘
        │
        ▼
┌─────────────────────────┐
│ FAST PATH: Does response│
│ contain Senzing content │
│ indicators?             │
└─────────────────────────┘
        │
   NO ──┼── YES
   │         │
   ▼         ▼
┌──────┐  ┌─────────────────────┐
│SILENT│  │ Was MCP tool called  │
│(zero │  │ in this turn?        │
│tokens)│  └─────────────────────┘
└──────┘        │
           YES ──┼── NO
           │         │
           ▼         ▼
        ┌──────┐  ┌──────────────────┐
        │SILENT│  │ SLOW PATH:       │
        │(zero │  │ Self-correction  │
        │tokens)│  │ instructions     │
        └──────┘  └──────────────────┘
```

## Components and Interfaces

### Component 1: Hook File (`senzing-bootcamp/hooks/mcp-first-invariant.kiro.hook`)

A JSON hook file following the project's established hook schema:

```json
{
  "name": "to verify MCP-first compliance",
  "version": "1.0.0",
  "description": "Audits every agent response for MCP-first invariant compliance. Silent when compliant; triggers self-correction when Senzing content is presented without prior MCP tool consultation.",
  "when": {
    "type": "agentStop"
  },
  "then": {
    "type": "askAgent",
    "prompt": "<hook prompt content>"
  }
}
```

The hook name follows the project convention: `"to {verb phrase}"` pattern used by all hooks in this project (e.g., "to wait for your answer", "to enforce mandatory gate execution on agent stop").

### Component 2: Hook Prompt Logic

The prompt implements a two-phase detection algorithm:

**Phase 1 — Senzing Content Detection:**

Check the most recent assistant response for Senzing content indicators:
- SDK method names: `add_record`, `get_entity`, `search_by_attributes`, `why_entities`, `how_entity`, `export_json_entity_report`, `get_record`, `delete_record`, `reevaluate_entity`, `reevaluate_record`, `find_interesting_entities_by_entity_id`, `find_interesting_entities_by_record_id`, `find_path_by_entity_id`, `find_network_by_entity_id`, `count_redo_records`, `get_redo_record`, `process_redo_record`
- Attribute names: `NAME_FULL`, `NAME_FIRST`, `NAME_LAST`, `ADDR_FULL`, `ADDR_LINE1`, `ADDR_CITY`, `ADDR_STATE`, `ADDR_POSTAL_CODE`, `PHONE_NUMBER`, `EMAIL_ADDR`, `DATE_OF_BIRTH`, `SSN_NUMBER`, `PASSPORT_NUMBER`, `DRIVERS_LICENSE_NUMBER`, `DATA_SOURCE`, `RECORD_ID`, `RECORD_TYPE`
- Configuration options: `ENTITY_TYPE`, `DSRC_ID`, `ETYPE_ID`, `FTYPE_ID`, `CFUNC_ID`, `EFCALL_ID`
- Error codes: pattern `SENZ` followed by 4 digits (e.g., `SENZ0001`, `SENZ7234`)
- Entity resolution terms in technical context: `resolved entity`, `entity resolution`, `candidate scoring`, `feature scoring`, `generic threshold`, `close match`, `possible match`, `name-only match`, `disclosed relationship`

**Phase 2 — MCP Tool Call Verification:**

If Senzing content is detected, check whether any MCP tool was called in the same turn. MCP tool call indicators:
- Tool call patterns: `search_docs`, `get_sdk_reference`, `generate_scaffold`, `sdk_guide`, `explain_error_code`, `find_examples`, `mapping_workflow`, `get_capabilities`, `reporting_guide`

**Decision Logic:**
- No Senzing content detected → produce zero output tokens (silent fast path)
- Senzing content detected AND MCP tool called → produce zero output tokens (compliant)
- Senzing content detected AND NO MCP tool called → produce self-correction instructions (violation)

### Component 3: Self-Correction Output Template

When a violation is detected, the hook outputs agent-directed instructions (not user-facing text):

```
MCP-FIRST INVARIANT VIOLATION: Your response contains Senzing content
([detected indicators]) but no MCP tool was consulted this turn.

REQUIRED ACTION:
1. Call the appropriate MCP tool(s) for the content type:
   - SDK methods/signatures → get_sdk_reference or sdk_guide
   - Attribute names/mapping → mapping_workflow
   - Error codes → explain_error_code
   - Documentation/concepts → search_docs
   - Code generation → generate_scaffold or sdk_guide
   - Examples → find_examples
2. Regenerate your response using the MCP-verified information.
3. Do NOT repeat the previous response verbatim — rebuild it from MCP facts.
```

### Component 4: Strengthened MCP Rules in `agent-instructions.md`

The existing MCP Rules section is extended with:

1. **Invariant declaration** — Explicit statement that MCP-first is an unconditional invariant with the same precedence as mandatory gate rules.
2. **Violation examples** — Concrete examples of what constitutes a breach.
3. **Pre-response checklist** — A numbered checklist the agent evaluates before presenting Senzing content.
4. **No-bypass clause** — Explicit prohibition of all agent-internal justifications for bypassing MCP consultation.

```markdown
### MCP-First Invariant

**This rule has the same absolute precedence as ⛔ mandatory gates.** No agent-internal reasoning — context pressure, perceived simplicity, cached knowledge from training data, session length, or token budget — can justify bypassing MCP consultation.

**Pre-response checklist** (evaluate before presenting ANY Senzing content):
1. Does my response contain Senzing SDK method names, attribute names, config options, error codes, or entity resolution technical details?
2. If YES: Did I call at least one MCP tool (search_docs, get_sdk_reference, generate_scaffold, sdk_guide, explain_error_code, find_examples, mapping_workflow, get_capabilities) in this turn to retrieve that information?
3. If NO to #2: STOP. Call the appropriate MCP tool before continuing.

**Violation examples** (each is a breach of the MCP-first invariant):
- Stating that `add_record` accepts a `LOAD_ID` parameter without calling `get_sdk_reference`
- Generating code with `sz_engine.add_record(...)` without calling `generate_scaffold` or `sdk_guide`
- Explaining that `NAME_FULL` maps to a person's full name without calling `mapping_workflow` or `search_docs`
- Describing error code SENZ0002 without calling `explain_error_code`
- Recommending entity resolution thresholds without calling `search_docs`
```

### Component 5: Hook Categories Registration

Add `mcp-first-invariant` to the `critical` list in `senzing-bootcamp/hooks/hook-categories.yaml`:

```yaml
critical:
  - ask-bootcamper
  - code-style-check
  - commonmark-validation
  - mcp-first-invariant
  - question-format-gate
  - review-bootcamper-input
  - write-policy-gate
```

The list remains alphabetically sorted. Critical hooks are created during onboarding and remain active across all modules.

## Data Models

### Senzing Content Indicators (Detection Set)

```python
SENZING_SDK_METHODS: list[str] = [
    "add_record", "get_entity", "search_by_attributes", "why_entities",
    "how_entity", "export_json_entity_report", "get_record", "delete_record",
    "reevaluate_entity", "reevaluate_record",
    "find_interesting_entities_by_entity_id",
    "find_interesting_entities_by_record_id",
    "find_path_by_entity_id", "find_network_by_entity_id",
    "count_redo_records", "get_redo_record", "process_redo_record",
]

SENZING_ATTRIBUTE_NAMES: list[str] = [
    "NAME_FULL", "NAME_FIRST", "NAME_LAST", "ADDR_FULL", "ADDR_LINE1",
    "ADDR_CITY", "ADDR_STATE", "ADDR_POSTAL_CODE", "PHONE_NUMBER",
    "EMAIL_ADDR", "DATE_OF_BIRTH", "SSN_NUMBER", "PASSPORT_NUMBER",
    "DRIVERS_LICENSE_NUMBER", "DATA_SOURCE", "RECORD_ID", "RECORD_TYPE",
]

SENZING_CONFIG_OPTIONS: list[str] = [
    "ENTITY_TYPE", "DSRC_ID", "ETYPE_ID", "FTYPE_ID", "CFUNC_ID", "EFCALL_ID",
]

SENZING_ERROR_CODE_PATTERN: str = r"SENZ\d{4}"

SENZING_ER_TERMS: list[str] = [
    "resolved entity", "entity resolution", "candidate scoring",
    "feature scoring", "generic threshold", "close match",
    "possible match", "name-only match", "disclosed relationship",
]

MCP_TOOL_NAMES: list[str] = [
    "search_docs", "get_sdk_reference", "generate_scaffold", "sdk_guide",
    "explain_error_code", "find_examples", "mapping_workflow",
    "get_capabilities", "reporting_guide",
]
```

### Hook Output States

| State | Condition | Output |
|-------|-----------|--------|
| Silent (fast path) | No Senzing content detected | Zero tokens |
| Silent (compliant) | Senzing content + MCP tool called | Zero tokens |
| Violation (slow path) | Senzing content + NO MCP tool called | Self-correction instructions |

## Error Handling

### Hook Prompt Robustness

- The hook prompt uses explicit conditional logic ("If NONE... produce no output") to prevent false positives on non-Senzing content.
- The Senzing content indicator list is intentionally specific (exact method names, exact attribute names) rather than broad pattern matching to minimize false positives.
- The error code pattern (`SENZ` + 4 digits) is specific enough to avoid matching unrelated text.
- Entity resolution terms are only flagged "in technical context" — the prompt instructs the agent to distinguish between casual mention and technical usage.

### Self-Correction Failure

- If the agent fails to self-correct after the first violation detection, the hook will fire again on the next response. This creates a natural retry loop.
- The hook does not implement a retry counter — it relies on the agent's compliance with the self-correction instructions.

### MCP Server Unavailability

- The hook does not override the existing MCP Failure rules in `agent-instructions.md`. If the MCP server is unreachable, the existing "retry once, then tell the bootcamper" rule applies.
- The hook's violation detection still fires even if MCP is down — the agent should not present Senzing content at all when MCP is unavailable (per existing rules).

## Testing Strategy

### Test Location

Per project conventions:
- Hook prompt validation tests go in repo-root `tests/` (since they validate real hook files)
- Tests extend existing patterns from `tests/test_hook_silent_fast_path_properties.py` and `tests/hook_test_helpers.py`

### Test File

New test file: `tests/test_mcp_first_invariant_properties.py`

### Test Approach

Property-based tests using Hypothesis verify:
1. The hook prompt correctly references all Senzing content indicators
2. The hook prompt contains silent fast-path directives
3. The hook prompt contains MCP tool verification logic
4. The hook prompt contains self-correction instructions
5. The agent-instructions.md contains invariant-strength language
6. The hook-categories.yaml registers the hook as critical
7. The hook output is agent-directed only (no user-facing text)

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Senzing indicator detection coverage

*For any* Senzing content indicator (SDK method name, attribute name, config option, or ER term) from the defined indicator sets, the hook prompt SHALL contain that indicator or a pattern that matches it, ensuring no indicator goes undetected.

**Validates: Requirements 1.3, 2.3, 3.1**

### Property 2: Silent fast-path for compliant scenarios

*For any* response scenario where either (a) no Senzing content is present, or (b) Senzing content is present and an MCP tool was called, the hook prompt SHALL contain explicit zero-output directives instructing the agent to produce zero tokens.

**Validates: Requirements 3.3, 7.1, 7.2**

### Property 3: MCP tool call verification coverage

*For any* MCP tool name from the defined tool set, the hook prompt SHALL reference that tool name in its tool-call detection logic, ensuring all valid MCP consultations are recognized as compliant.

**Validates: Requirements 3.2**

### Property 4: Self-correction instructions on violation

*For any* Senzing content category (SDK methods, attributes, error codes, config options, ER concepts), the hook prompt's violation output SHALL contain self-correction instructions that map that category to the appropriate MCP tool(s) for re-consultation.

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 5: No-bypass invariant language

*For any* agent-internal bypass justification (context pressure, perceived simplicity, cached knowledge, session length, token budget), the `agent-instructions.md` MCP Rules section SHALL explicitly prohibit that justification as a reason to skip MCP consultation.

**Validates: Requirements 5.1, 5.4**

### Property 6: Critical-only registration

*For any* module-specific category in `hook-categories.yaml`, the `mcp-first-invariant` hook SHALL NOT appear in that module's list, AND it SHALL appear in the `critical` category — ensuring it is active across all modules without per-module activation.

**Validates: Requirements 6.1, 6.3**

### Property 7: Agent-directed output only

*For any* output produced by the hook on the slow path (violation detected), the output SHALL be structured as agent-directed instructions (containing action verbs like "Call", "Regenerate", "Do NOT") and SHALL NOT contain user-facing explanatory text or conversational language directed at the bootcamper.

**Validates: Requirements 7.3**
