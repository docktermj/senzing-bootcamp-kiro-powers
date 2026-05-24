# SDK Method Discovery Bugfix Design

## Overview

When a bootcamper's request could map to multiple SDK methods (e.g., "explain why entity 74 resolved" could use `how_entity`, `why_entities`, `why_records`, or `why_record_in_entity`), the agent immediately picks one method without first calling `get_sdk_reference` to discover all available methods in that category and without asking the bootcamper which level of detail they want. The root cause is that the steering files instruct the agent to use specific methods for specific tasks (a direct mapping) but never instruct the agent to first discover the full set of available methods when the request is ambiguous. The fix adds an "SDK Method Discovery Protocol" to `agent-instructions.md` that requires a discover-then-disambiguate flow for ambiguous SDK method requests, while preserving direct method usage for explicit or unambiguous requests.

## Glossary

- **Bug_Condition (C)**: The bootcamper requests an SDK operation that could map to multiple methods in the same category (e.g., "explain why entity 74 resolved" maps to `how_entity`, `why_entities`, `why_records`, `why_record_in_entity`), and the agent selects one method without first discovering all available methods via `get_sdk_reference` and without asking a clarifying question
- **Property (P)**: The agent calls `get_sdk_reference` to discover available methods in the relevant category BEFORE selecting one, and when multiple methods could satisfy the request, asks a single 👉 clarifying question presenting the options as a numbered choice list — only then proceeds with the bootcamper's chosen method
- **Preservation**: All behavior when the bootcamper explicitly names a method, when the request unambiguously maps to one method, when the agent has already discovered methods for a category in the current session, and all existing `get_sdk_reference` usage for flag/signature lookups
- **`agent-instructions.md`**: The always-loaded steering file at `senzing-bootcamp/steering/agent-instructions.md` that defines core agent rules including MCP tool usage
- **`mcp-tool-decision-tree.md`**: The manually-loaded steering file at `senzing-bootcamp/steering/mcp-tool-decision-tree.md` that maps tasks to MCP tools and defines the Flag Selection Protocol
- **SDK method category**: A group of related SDK methods that address the same general concern at different granularity levels (e.g., the "why/how" category contains `how_entity`, `why_entities`, `why_records`, `why_record_in_entity`)
- **Discovery step**: A call to `get_sdk_reference` with a category or topic filter to enumerate all available methods before selecting one

## Bug Details

### Bug Condition

The bug manifests when the bootcamper makes a request that could be satisfied by multiple SDK methods in the same category. The current steering files provide direct mappings (e.g., "why did these match" → `why_entities`/`why_records`) but never instruct the agent to first discover ALL methods in the category and then disambiguate. The agent picks the first matching method from its training data or the steering file's suggestion list without considering alternatives.

**Formal Specification:**

```pseudocode
FUNCTION isBugCondition(input)
  INPUT: input of type SDKMethodRequest
  OUTPUT: boolean

  RETURN input.requestIsAmbiguous = true
         AND input.availableMethodsInCategory > 1
         AND (input.agentSkippedDiscovery = true
              OR input.agentSkippedClarification = true)
END FUNCTION
```

### Examples

- Bootcamper says "explain why entity 74 resolved" → agent immediately uses `why_entities` without discovering that `how_entity`, `why_records`, and `why_record_in_entity` also exist and might better match the intent → **Bug**: skipped discovery, skipped clarification
- Bootcamper says "show me how entity 42 was built" → agent uses `how_entity` which is the only method for entity construction → **Correct**: unambiguous, no alternatives in this specific sub-category
- Bootcamper says "use why_records on records A and B" → agent uses `why_records` directly → **Correct**: bootcamper explicitly named the method
- Bootcamper says "why did these two entities match?" → agent picks `why_entities` without noting that `why_records` provides record-level detail → **Bug**: skipped discovery, missed teaching opportunity
- Agent already discovered "why/how" methods earlier in the module session → bootcamper asks another "why" question → agent reuses cached knowledge → **Correct**: no re-query needed

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- When the bootcamper explicitly names a specific SDK method, the agent uses it directly without discovery or clarification
- When the agent has already discovered methods for a category in the current module session, it reuses that knowledge without re-querying
- When the request unambiguously maps to exactly one method with no alternatives, the agent proceeds directly
- All existing `get_sdk_reference` usage for flag lookups and signature lookups continues unchanged
- The Flag Selection Protocol in `mcp-tool-decision-tree.md` is unaffected
- The `block-direct-sql.kiro.hook` and all other hooks are unmodified
- Module-specific steering files (module-07, etc.) retain their existing agent instructions about flag lookups
- The SQL-tempting question redirects in `agent-instructions.md` continue to work as direct mappings for unambiguous cases

**Scope:**

All inputs where the bootcamper explicitly names a method, where the request is unambiguous, or where discovery has already been performed in the current session should be completely unaffected. The fix only adds behavior for the case where the request is ambiguous AND discovery has not yet been performed.

## Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **No Discovery-First Rule for Ambiguous Requests**: The MCP Rules in `agent-instructions.md` say "Signatures → `get_sdk_reference`" and "Never hand-code Senzing JSON mappings or SDK method names" but never explicitly instruct the agent to discover ALL available methods in a category before selecting one when the request is ambiguous. The agent interprets "Never guess SDK method signatures" as "look up the signature of the method I've already chosen" rather than "discover what methods exist before choosing."

2. **Direct Mappings Without Disambiguation**: The SQL-tempting question redirects provide direct mappings like `"why did these match" → why_entities/why_records` — listing alternatives but not instructing the agent to present them as choices to the bootcamper. The agent picks the first one listed.

3. **No Clarification Protocol for Method Selection**: The communication rules require 👉 for input-required questions and one-question-at-a-time flow, but there's no specific protocol for when to ask a method-selection clarifying question vs. when to proceed directly. The agent defaults to proceeding without asking.

4. **Missing Category Awareness**: The steering files list individual methods but don't group them into categories with explicit "these are alternatives for the same general task at different granularity levels" framing. The agent doesn't recognize that `how_entity` and `why_entities` are related alternatives.

## Correctness Properties

Property 1: Bug Condition - Agent Discovers Methods Before Selecting for Ambiguous Requests

_For any_ request where the bootcamper's intent could map to multiple SDK methods in the same category AND the bootcamper has not explicitly named a method AND the agent has not already discovered methods for this category in the current session, the agent SHALL call `get_sdk_reference` to discover available methods BEFORE selecting one, AND if multiple methods could satisfy the request, SHALL ask a single 👉 clarifying question presenting the options.

**Validates: Requirements 2.1, 2.2**

Property 2: Unambiguous Requests Proceed Without Unnecessary Questions

_For any_ request where the discovered methods show exactly one method matching the bootcamper's intent, OR where the bootcamper explicitly named a method, OR where discovery was already performed in this session, the agent SHALL proceed directly without asking an unnecessary clarifying question.

**Validates: Requirements 2.3, 3.1, 3.2, 3.3**

Property 3: Preservation - Existing get_sdk_reference Usage Unchanged

_For any_ existing usage of `get_sdk_reference` for flag lookups, signature lookups, or other non-discovery purposes, the behavior SHALL remain identical. The fix adds a new discovery use case without modifying existing ones.

**Validates: Requirements 3.4**

## Fix Implementation

### Changes Required

**File 1**: `senzing-bootcamp/steering/agent-instructions.md`

**Section**: MCP Rules (add new subsection after the existing MCP rules)

**Specific Changes**:

1. **Add SDK Method Discovery Protocol**: Insert a new subsection in the MCP Rules section titled "SDK Method Discovery" that defines the discover-then-disambiguate flow. This protocol:
   - Triggers when the bootcamper's request could map to multiple SDK methods in the same category
   - Requires calling `get_sdk_reference` with a category/topic filter to discover all available methods
   - Requires a 👉 clarifying question when multiple discovered methods could satisfy the request
   - Allows direct proceed when only one method matches or when the bootcamper explicitly named a method
   - Allows reuse of previously discovered methods within the same module session

2. **Define SDK method categories**: Add a brief taxonomy of SDK method categories that have multiple alternatives (the "ambiguous" categories):
   - **Why/How category**: `how_entity`, `why_entities`, `why_records`, `why_record_in_entity`
   - **Entity retrieval category**: `get_entity`, `get_entity_by_record_id`
   - **Search category**: `search_by_attributes`, `search_by_record_id`

3. **Add skip conditions**: Explicitly list when discovery is NOT needed:
   - Bootcamper explicitly names a method
   - Request unambiguously maps to one method (no alternatives in category)
   - Methods for this category already discovered in current module session

**File 2**: `senzing-bootcamp/steering/mcp-tool-decision-tree.md`

**Section**: After "Flag Selection Protocol" (add new section)

**Specific Changes**:

1. **Add Method Discovery Protocol section**: A companion section to the Flag Selection Protocol that defines the step-by-step discovery flow with examples. This provides the detailed reference that `agent-instructions.md` can point to (similar to how `agent-instructions.md` says "Load `mcp-tool-decision-tree.md` for the full decision tree").

2. **Add ambiguous request examples**: Show concrete examples of ambiguous vs. unambiguous requests and the expected agent behavior for each.

## Testing Strategy

### Validation Approach

Since this bug is in steering file content (not executable code), testing focuses on structural and content properties of the markdown files. Tests parse the steering files and verify the presence of discovery protocol instructions, category definitions, and skip conditions.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm the root cause.

**Test Cases**:

1. **Missing Discovery Protocol Test**: Parse `agent-instructions.md` MCP Rules section and check for an SDK method discovery protocol (will fail on unfixed code — no protocol exists)
2. **Missing Category Taxonomy Test**: Parse `agent-instructions.md` and check for SDK method category definitions grouping related methods (will fail on unfixed code — no categories defined)
3. **Missing Clarification Instruction Test**: Parse `agent-instructions.md` and check for an instruction to ask a 👉 clarifying question when multiple methods match (will fail on unfixed code — no such instruction exists)

### Fix Checking

**Goal**: Verify the fixed files contain the necessary discovery protocol.

**Pseudocode:**

```pseudocode
FOR ALL section WHERE isMCPRulesSection(section) DO
  content := parseSteeringSection(section)
  ASSERT containsDiscoveryProtocol(content)
  ASSERT containsCategoryTaxonomy(content)
  ASSERT containsClarificationInstruction(content)
  ASSERT containsSkipConditions(content)
END FOR
```

### Preservation Checking

**Goal**: Verify existing MCP rules, flag protocol, and other steering content is unchanged.

**Test Cases**:

1. **Existing MCP Rules Preserved**: Verify all existing MCP rule bullet points in `agent-instructions.md` are unchanged
2. **Flag Selection Protocol Preserved**: Verify the Flag Selection Protocol section in `mcp-tool-decision-tree.md` is unchanged
3. **SQL Redirects Preserved**: Verify the SQL-tempting question redirects are unchanged
4. **Module-07 Agent Instructions Preserved**: Verify `module-07-query-validation.md` agent instructions about flag lookups are unchanged
5. **Communication Rules Preserved**: Verify the Communication section's 👉 and one-question-at-a-time rules are unchanged

### Unit Tests

- Test that `agent-instructions.md` contains an "SDK Method Discovery" subsection in the MCP Rules area
- Test that the discovery protocol mentions `get_sdk_reference` as the discovery mechanism
- Test that the protocol includes a 👉 clarifying question instruction for ambiguous cases
- Test that the protocol defines skip conditions (explicit method name, unambiguous request, already discovered)
- Test that `mcp-tool-decision-tree.md` contains a Method Discovery Protocol section
- Test that the method categories include the why/how group (`how_entity`, `why_entities`, `why_records`, `why_record_in_entity`)

### Property-Based Tests

- Generate random SDK method names from the known set and verify that methods in the same category are grouped together in the taxonomy
- Parse both fixed and unfixed `agent-instructions.md` and verify all non-MCP-Discovery sections are identical
- Verify the total number of MCP rule bullet points is preserved (new content is additive, not replacing)
- Generate random section headings from `mcp-tool-decision-tree.md` and verify all pre-existing sections are unchanged

### Integration Tests

- Parse `agent-instructions.md` and verify the document structure is valid markdown with correct heading hierarchy
- Verify the discovery protocol references `get_sdk_reference` consistently with existing MCP tool references
- Verify the 👉 marker usage in the discovery protocol is consistent with the Communication rules' 👉 convention
