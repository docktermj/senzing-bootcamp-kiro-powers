# Design Document

## Overview

This design describes the changes to `senzing-bootcamp/steering/module-05-phase1-quality-assessment.md` to remove hardcoded Entity Specification attribute lists from Steps 3, 4, and 5, replacing them with an explicit MCP `download_resource` call instruction. The change enforces the project's MCP-first principle: all Senzing facts come from MCP tools at runtime, never from static content embedded in steering files.

## Architecture

The change is a content edit to a single Markdown steering file. No new components, services, or modules are introduced. The architecture remains:

```text
Agent → reads steering file → encounters Step 3 → calls download_resource MCP tool
                                                → receives Entity Specification
                                                → uses it for Steps 3, 4, 5
```

**Before:** The steering file contained inline attribute lists that the agent could use directly, bypassing MCP entirely.

**After:** The steering file contains only a `download_resource` call instruction. The agent must call the MCP tool to obtain attribute information.

## Components and Interfaces

### Modified Component: `module-05-phase1-quality-assessment.md`

**Location:** `senzing-bootcamp/steering/module-05-phase1-quality-assessment.md`

**Changes by step:**

#### Step 3 — "Understand the Senzing Generic Entity Specification"

- **Remove:** The entire bulleted list of identity attributes, contact attributes, required fields, and relationship attributes.
- **Remove:** The `search_docs` call instruction (replaced by `download_resource`).
- **Add:** An explicit instruction to call `download_resource(filename="senzing_entity_specification.md")`.
- **Add:** Language directing the agent to use the downloaded content as the authoritative source for all attribute names, types, and structures in this and subsequent steps.

#### Step 4 — "Compare each data source with the Entity Specification"

- **Remove:** Hardcoded attribute name examples in parenthetical mappings (e.g., `"full_name" → NAME_FULL`, `"company" → NAME_ORG`).
- **Retain:** The general workflow structure (identify direct maps, transformations, non-standard names, missing fields, required fields).
- **Add:** A reference directing the agent to use the Entity Specification retrieved in Step 3 for field comparisons.

#### Step 5 — "Categorize each data source"

- **Remove:** The phrase "standard Senzing attribute names" where it implies a known static list.
- **Retain:** The three categories (Entity Specification-compliant, Needs mapping, Needs enrichment).
- **Add:** Generic language referencing "the Entity Specification retrieved in Step 3" as the source of truth for what constitutes compliant attribute names.

### Interfaces

No programmatic interfaces are introduced. The "interface" is the steering file's textual contract with the agent:

### MCP Call Instruction Format

The steering file uses this format to instruct the agent:

```markdown
Call `download_resource(filename="senzing_entity_specification.md")` to retrieve the current
Senzing Generic Entity Specification. Use this as the authoritative reference for all attribute
names, types, and structures in this step and subsequent steps.
```

### Constraints

- Exactly one `download_resource` call instruction across Steps 3–5.
- The call instruction appears in Step 3 before any reference to Entity Specification content.
- No inline attribute names appear anywhere in Steps 3–5.
- No fallback content is provided if the MCP call fails.

## Data Models

No data models are introduced or modified. The steering file is a Markdown document with YAML frontmatter — its structure is unchanged.

## Error Handling

The steering file intentionally provides **no fallback** if `download_resource` fails. This is by design:

- If the MCP server is unreachable, the agent cannot proceed with quality assessment (it lacks the specification).
- The agent's standard error handling (retry, report to user) applies.
- No cached or inline attribute data is provided as an alternative, ensuring the MCP-first principle is never bypassed.

## Testing Strategy

Testing validates the structural properties of the modified steering file content using Python with pytest and Hypothesis.

### Test Approach

Tests read the actual `module-05-phase1-quality-assessment.md` file and verify:
1. No hardcoded Entity Specification attributes exist in Steps 3–5.
2. The `download_resource` call instruction appears exactly once and in the correct location.
3. The general workflow structure in Step 4 is preserved.

### Step Extraction

A helper function extracts individual step content from the steering file by parsing numbered step boundaries (`N. **Title**`). This enables per-step assertions.

### Attribute Detection

A regex pattern detects Entity Specification attribute names. The pattern matches the known format: uppercase letters with underscores, specifically the Senzing attribute naming convention (e.g., `NAME_FULL`, `ADDR_LINE1`, `PHONE_NUMBER`, `DATA_SOURCE`, `RECORD_ID`). A curated set of known Senzing attributes is used for detection rather than a broad regex, to avoid false positives on general uppercase identifiers.

```python
# Known Entity Specification attributes that should NOT appear inline
KNOWN_ENTITY_SPEC_ATTRIBUTES = {
    "NAME_FULL", "NAME_FIRST", "NAME_LAST", "NAME_ORG",
    "DATE_OF_BIRTH", "PASSPORT_NUMBER", "DRIVERS_LICENSE_NUMBER",
    "SSN_NUMBER", "NATIONAL_ID_NUMBER",
    "ADDR_FULL", "ADDR_LINE1", "ADDR_CITY", "ADDR_STATE",
    "ADDR_POSTAL_CODE", "PHONE_NUMBER", "EMAIL_ADDRESS",
    "WEBSITE_ADDRESS",
    "REL_ANCHOR_DOMAIN", "REL_ANCHOR_KEY",
    "REL_POINTER_DOMAIN", "REL_POINTER_KEY", "REL_POINTER_ROLE",
}

# Attributes that ARE allowed because they are structural/required field names
# referenced generically (e.g., "check if DATA_SOURCE and RECORD_ID are present")
ALLOWED_STRUCTURAL_REFS = {"DATA_SOURCE", "RECORD_ID"}
```

**Note:** `DATA_SOURCE` and `RECORD_ID` are allowed in Step 4 because they are required structural fields that the agent must check for — they are not part of the Entity Specification attribute enumeration being removed. The requirement (2.3) explicitly states the workflow should check for "required fields."

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: No hardcoded Entity Specification attributes in Steps 3–5

*For any* step content extracted from Steps 3, 4, or 5 of the steering file, the content shall not contain any Entity Specification attribute names from the known attribute set (excluding the allowed structural references `DATA_SOURCE` and `RECORD_ID` in Step 4's required-fields check).

**Validates: Requirements 1.1, 2.1, 3.1, 5.1**

### Property 2: Exactly one download_resource instruction

*For any* content spanning Steps 3 through 5 of the steering file, the count of `download_resource` call instructions shall equal exactly one.

**Validates: Requirements 4.1**

### Property 3: download_resource placement precedes Entity Specification references

*For any* content in Step 3 of the steering file, the `download_resource` call instruction shall appear before any reference to Entity Specification content usage (i.e., the instruction to use the specification as authoritative must come after the call instruction).

**Validates: Requirements 4.2**
