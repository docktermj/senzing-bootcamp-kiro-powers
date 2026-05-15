---
inclusion: auto
description: "Entity resolution design pattern gallery — load during Module 1 or when discussing patterns"
---

# Entity Resolution Design Pattern Gallery

<!-- Agent instruction: Do NOT present hardcoded pattern details from this file.
     Call search_docs(query="entity resolution design patterns") to retrieve
     current pattern descriptions, use cases, and recommended matching attributes.
     Use the structural framework below to organize the MCP-returned content. -->

Offer this gallery during Module 1 to help users identify their use case.

## Patterns

Before presenting patterns, call `search_docs(query="entity resolution design patterns")` to retrieve the current list of patterns with their descriptions, use cases, key matching attributes, and typical ROI. Present the MCP-returned content in a table format.

The following pattern names serve as a structural index — always use `search_docs` for current details:

- Customer 360
- Fraud Detection
- Data Migration
- Compliance Screening
- Marketing Dedup
- Patient Matching
- Vendor MDM
- Claims Fraud
- KYC/Onboarding
- Supply Chain

## Which Pattern Fits?

Walk through these questions:

1. **What entities?** People → Q2. Organizations → Vendor MDM or Supply Chain. Both → Customer 360 or Data Migration.
2. **Primary goal?** Find duplicates → Marketing Dedup. Unify across systems → Customer 360 or Data Migration. Detect fraud → Fraud Detection or Claims Fraud. Regulatory → Compliance Screening or KYC. Patient care → Patient Matching.
3. **One-time or ongoing?** One-time → Data Migration or Marketing Dedup. Ongoing → Customer 360, Fraud Detection, Compliance Screening.

If the user's case spans multiple patterns, start with the one that delivers the most immediate business value.

## Agent Behavior

1. Call `search_docs(query="entity resolution design patterns")` to get current pattern details
2. Present the patterns in a table with use cases, key matching attributes, and typical ROI
3. Walk through the 3 questions above to narrow down the user's use case
4. Use the selected pattern to guide Module 2 problem definition
5. Call `search_docs` with the selected pattern name (e.g., `search_docs(query="customer 360 pattern")`) for deeper implementation guidance
6. Recommend key matching attributes for Module 4 data mapping based on MCP-returned content
7. If multiple patterns apply, help prioritize implementation order

## Where Senzing Fits in Your Architecture

When discussing how Senzing integrates with search engines, message queues, or other infrastructure, call `search_docs` with the relevant integration topic (e.g., `search_docs(query="elasticsearch integration")`, `search_docs(query="architecture patterns")`) to retrieve current guidance.

Present the MCP-returned architecture guidance when the user's problem involves search, lookup, or retrieval alongside entity resolution. Reference it again in Module 8 (Query & Visualize) when building query programs.
