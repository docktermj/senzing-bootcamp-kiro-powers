# Bugfix Requirements Document

## Introduction

The Senzing Bootcamp Power has a governing rule (rule 6): **"If the current Senzing license is insufficient, consult the Senzing MCP server for a temporary Senzing license."**

The implementation violates this rule. When a bootcamper's data exceeds the built-in 500-record evaluation license limit (the "insufficient license" condition) — or when a `SENZ9000` license-capacity error occurs — the power's steering files only *mention in prose* that the bootcamper "can request a larger evaluation license directly through the Senzing MCP server." This prose appears alongside email contacts (`support@senzing.com` / `sales@senzing.com`) and is framed as passive awareness, not as an enforced action.

The agent never actually *consults* an MCP server tool to obtain guidance on a temporary or larger license. Two places exhibit the defect:

- `senzing-bootcamp/steering/module-02-sdk-setup.md` — Step 5a (built-in evaluation license explanation) and Step 5c "no license" path mention the MCP server in prose only.
- `senzing-bootcamp/steering/module-01-business-problem.md` — Step 6d ("does not have license" branch, triggered when total records exceed 500) directs the bootcamper to email `support@senzing.com` and contains no MCP consultation step at all.

This also breaches the **MCP-First Invariant** in `senzing-bootcamp/steering/agent-instructions.md`, which requires that all Senzing facts (including licensing guidance) be retrieved through an MCP tool call rather than emitted as hardcoded prose from training data. License guidance is a Senzing fact and is currently presented without any MCP tool consultation.

The prior `licensing-guidance` spec intentionally added the MCP mention as prose only (acceptance criterion 4.2 explicitly avoided hardcoding MCP tool names), so this bug is a known gap between the documented rule and the implemented behavior.

The fix makes MCP consultation a defined, enforced step in the license-insufficient workflow path. The exact MCP tool to consult (e.g., `search_docs` for license guidance) must be confirmed against `senzing-bootcamp/steering/mcp-usage-reference.md` and `mcp-tool-decision-tree.md` rather than invented. No MCP server URL is hardcoded outside `mcp.json`.

## Bug Analysis

### Current Behavior (Defect)

When the current Senzing license is insufficient, the steering files only describe MCP availability in prose and never instruct the agent to consult an MCP tool.

1.1 WHEN the bootcamper's total record count exceeds the 500-record evaluation limit (Module 1, Step 6d "does not have license" branch) THEN the steering file directs the bootcamper to email `support@senzing.com` for an evaluation license and provides NO instruction to consult the Senzing MCP server.

1.2 WHEN the agent presents the built-in evaluation license explanation (Module 2, Step 5a) THEN the steering file states the bootcamper "can request a larger evaluation license directly through the Senzing MCP server" as passive prose, with no defined MCP tool call the agent must perform.

1.3 WHEN the bootcamper indicates they have no license (Module 2, Step 5c "no license" path) THEN the steering file lists the MCP server alongside `support@senzing.com` / `sales@senzing.com` as awareness prose, with no enforced step that consults an MCP tool for temporary/larger-license guidance.

1.4 WHEN a `SENZ9000` license-capacity error occurs (record limit exceeded at record 501) THEN the license-insufficient handling provides license guidance as hardcoded prose rather than retrieving it through an MCP tool, breaching the MCP-First Invariant for licensing facts.

### Expected Behavior (Correct)

When the current Senzing license is insufficient, the agent must consult the Senzing MCP server (via an MCP tool call) to obtain temporary/larger-license guidance as a defined, enforced step.

2.1 WHEN the bootcamper's total record count exceeds the 500-record evaluation limit (Module 1, Step 6d "does not have license" branch) THEN the steering file SHALL instruct the agent to consult the Senzing MCP server (via a named, file-confirmed MCP tool such as `search_docs`) for temporary/larger-license guidance, in addition to the existing email contact path.

2.2 WHEN the agent presents the built-in evaluation license explanation (Module 2, Step 5a) THEN the steering file SHALL define an MCP consultation step (a named MCP tool call) the agent performs to obtain larger/temporary evaluation license guidance, rather than only mentioning MCP availability in prose.

2.3 WHEN the bootcamper indicates they have no license (Module 2, Step 5c "no license" path) THEN the steering file SHALL instruct the agent to consult the Senzing MCP server via an MCP tool to obtain temporary/larger-license guidance, presented as an enforced step alongside the existing email contacts.

2.4 WHEN a `SENZ9000` license-capacity error occurs THEN the license-insufficient handling SHALL route the agent to an MCP tool consultation for license guidance, satisfying the MCP-First Invariant (the guidance comes from an MCP tool, not hardcoded prose).

2.5 WHERE an MCP tool name is referenced for license consultation, the steering files SHALL use a tool confirmed to exist in `mcp-usage-reference.md` / `mcp-tool-decision-tree.md` (e.g., `search_docs`), and SHALL NOT introduce any MCP server URL outside `mcp.json`.

### Unchanged Behavior (Regression Prevention)

For inputs where the license is sufficient (record count at or below the 500-record evaluation limit), and for all structural invariants the existing tests enforce, behavior must be preserved.

3.1 WHEN the bootcamper's total record count is 500 or fewer (Module 1, Step 6a check) THEN the steering file SHALL CONTINUE TO skip the license guidance sub-steps (6b–6e) and proceed directly to Step 7, with no MCP license consultation triggered.

3.2 WHEN the bootcamper provides a Base64-encoded license string or a `.lic` file (Module 2, Step 5c "has license" branches) THEN the steering file SHALL CONTINUE TO guide decoding/placement to `licenses/g2.lic` and configuring `LICENSEFILE`, unchanged.

3.3 WHEN Module 2 Step 5 is reached THEN it SHALL CONTINUE TO be marked as a ⛔ MANDATORY GATE with the "Never skip this step, even if the SDK is already installed" instruction, the 👉 license question in 5b, and the STOP marker (per `test_license_step_mandatory.py`).

3.4 WHEN the steering files are loaded THEN they SHALL CONTINUE TO retain their YAML frontmatter with `inclusion: manual`, exactly one pointing question (👉) per sub-step boundary, the checkpoint instructions, and the existing email contacts (`support@senzing.com` / `sales@senzing.com`) and `licenses/README.md` reference.

3.5 WHEN the steering files reference MCP capabilities THEN they SHALL CONTINUE TO comply with security rules — no MCP server URL outside `mcp.json` and no external `http://`/`https://` URLs introduced into steering files.

3.6 WHEN the agent presents non-license Senzing content (SDK install, configuration, verification, mapping) THEN those steps SHALL CONTINUE TO behave exactly as before, unaffected by the license-consultation fix.

## Bug Condition Derivation

**Key Definitions:**

- **F** — the original (unfixed) license-handling workflow described by the steering files, where MCP license guidance is prose-only.
- **F'** — the fixed workflow, where an insufficient license routes the agent to a defined MCP tool consultation.
- **X** — a license-handling situation encountered during the bootcamp, characterized by record count, license possession, and any license-capacity error.

### Bug Condition C(X)

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type LicenseSituation
  OUTPUT: boolean

  // The license is "insufficient" when capacity is exceeded or a
  // capacity error has occurred, AND no sufficient custom license is present.
  RETURN (X.totalRecordCount > 500 OR X.errorCode = "SENZ9000")
         AND NOT X.hasSufficientLicense
END FUNCTION
```

### Property — Fix Checking

For every license-insufficient situation, the fixed workflow must define an MCP tool consultation step for temporary/larger-license guidance (not prose-only).

```pascal
// Property: Fix Checking — MCP consultation on insufficient license
FOR ALL X WHERE isBugCondition(X) DO
  workflow ← F'(X)
  ASSERT mentionsMcpConsultationStep(workflow)            // a named MCP tool call is present
     AND mcpToolNameConfirmedInReference(workflow)        // tool exists in mcp-usage-reference / decision-tree
     AND NOT isProseOnlyMention(workflow)                 // not passive "can request via MCP" prose
     AND noMcpUrlOutsideMcpJson(workflow)
END FOR
```

### Property — Preservation Checking

For every situation that is not license-insufficient, the fixed workflow must behave identically to the original.

```pascal
// Property: Preservation Checking — sufficient-license paths unchanged
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

### Counterexample (demonstrates the bug under F)

```pascal
// Module 1, Step 6d: bootcamper has 10,000 records and no license.
X ← { totalRecordCount: 10000, hasSufficientLicense: false, errorCode: null }
// isBugCondition(X) = true
// F(X): steering directs the bootcamper to email support@senzing.com only;
//       no MCP tool consultation step exists  →  rule 6 violated.
```
