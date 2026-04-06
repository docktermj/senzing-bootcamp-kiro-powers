# Senzing Information Policy — MCP Server Only

**Date**: 2026-03-31
**Status**: Active
**Applies To**: All modules (0–12)

## Overview

When running any module in the Senzing Bootcamp, the agent must never state Senzing facts from its training data. All Senzing-specific information must come from the Senzing MCP server's tools.

## Policy

### Rule

**All Senzing facts must be retrieved from the Senzing MCP server tools. Never rely on training data for Senzing-specific information.**

### What This Covers

- Senzing attribute names and their meanings
- SDK method signatures, parameters, and return values
- JSON mapping formats and field names
- Error codes and their explanations
- Configuration options and defaults
- Supported data source formats
- Entity resolution concepts specific to Senzing
- Version-specific behavior and features
- Pricing, licensing, and product details
- Any other factual claim about how Senzing works

### Why This Matters

- Training data may be outdated or inaccurate for Senzing specifics
- The MCP server provides authoritative, version-correct information
- Users depend on accurate guidance to build working solutions
- Incorrect attribute names or SDK calls waste time and cause errors

## Agent Behavior

### Do

- Use `mapping_workflow` for attribute names and JSON formats
- Use `get_sdk_reference` for method signatures
- Use `search_docs` for documentation lookups
- Use `explain_error_code` for error diagnosis
- Use `find_examples` for code examples
- Use `generate_scaffold` or `sdk_guide` for SDK code
- Use `get_capabilities` at session start to understand available tools
- Say "Let me look that up" when asked a Senzing-specific question

### Do Not

- State Senzing attribute names from memory
- Guess SDK method signatures or parameters
- Describe Senzing JSON formats without MCP verification
- Explain Senzing error codes without using `explain_error_code`
- Claim how Senzing features work without MCP tool confirmation
- Provide Senzing configuration values from training data
- Reuse a previous MCP response from earlier in the conversation — always make a fresh MCP call, even for repeated questions
- Present inferred or guessed answers as authoritative when MCP returns no definitive result

## No Fabrication Rule

If the MCP server does not return a definitive answer for a Senzing-specific question, the agent **must not** infer, guess, or construct an answer from general knowledge or pattern matching. This includes:

- Inferring the meaning of Senzing codes, acronyms, or terms from their letters (e.g., guessing "SNAME means Same Name")
- Combining partial MCP results with general knowledge to produce an answer that sounds authoritative
- Presenting any non-MCP-sourced information as if it came from Senzing documentation

**Instead, the agent must:**

1. Tell the user clearly: "I wasn't able to find definitive documentation for that in the Senzing knowledge base."
2. Suggest checking [docs.senzing.com](https://docs.senzing.com) or contacting [support@senzing.com](mailto:support@senzing.com).
3. If the agent has a reasonable guess, it may share it only if explicitly prefaced with: "This is not from Senzing documentation — it's my best guess, and I recommend verifying with Senzing support."

## Examples

### Correct

```text
User: "What attributes does Senzing use for addresses?"

Agent: "Let me look that up using the Senzing documentation."
→ Calls search_docs or mapping_workflow to get the authoritative list
→ Presents the MCP-sourced answer
```

### Incorrect

```text
User: "What attributes does Senzing use for addresses?"

Agent: "Senzing uses ADDR_FULL, ADDR_LINE1, ADDR_CITY..."
→ ❌ Stated from training data without MCP verification
```

## MCP Response Reuse

Within the same module, the agent may reuse MCP responses from earlier in the conversation for the same query. This avoids unnecessary latency and context window usage. However:

- Across module boundaries, always re-query the MCP server
- If the user explicitly asks to "look it up again" or "verify that," always make a fresh call
- If the question is about something that could have changed (e.g., after loading data, after configuration changes), make a fresh call

## Enforcement

- This policy is referenced in `steering/agent-instructions.md`
- Applies across all modules without exception
- Agents should proactively use MCP tools rather than waiting to be corrected
- Within the same module, agents may reuse earlier MCP responses for the same query
- Across module boundaries, always re-query

## Version History

- **v1.0** (2026-03-31): Initial policy created
