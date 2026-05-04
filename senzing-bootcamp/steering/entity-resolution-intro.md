---
inclusion: manual
---

# What Is Entity Resolution?

Loaded via `#[[file:]]` from `onboarding-flow.md` during Step 4a.

<!-- AGENT INSTRUCTION — not shown to the bootcamper.
Before presenting this section, call `search_docs` from the Senzing MCP server:
1. search_docs("Senzing principle-based entity resolution approach")
2. search_docs("entity resolution outputs matched entities relationships deduplication")
Use retrieved content to fill in Senzing-specific claims. If MCP unavailable,
present static content as-is and note you'll verify later. See mcp-offline-fallback.md.
-->

## Why matching records is hard

When the same person or organization exists in multiple systems, their records almost never look identical:

- **Name variations.** "John Smith" / "J. Smith" / "Jonathan Smith" — same person or three different people?
- **Address changes over time.** People move. CRM address may be two apartments ago.
- **Format inconsistencies.** Phone: `(555) 867-5309` vs `5558675309` vs `+1-555-867-5309`. Dates, postal codes, identifiers all vary.
- **Data entry errors.** Typos, transposed digits, abbreviations ("St" vs "Street," "Rob" vs "Robert").
- **The false-positive problem.** Father and son share name and address — matching them would be wrong. Simple fuzzy matching can't tell the difference.

These challenges compound across millions of records and dozens of sources.

## How Senzing handles it

Senzing uses **principle-based matching** — not hand-coded rules or ML models. Three observable behaviors of data attributes:

- **Frequency** — Common name = weak evidence. Rare name = strong evidence.
- **Exclusivity** — SSN is exclusive (one person, one SSN). Phone is less exclusive (shared, changed).
- **Stability** — DOB never changes (stable). Address changes often (unstable).

Senzing weighs evidence automatically across all features — names, addresses, identifiers, phones, dates. Preconfigured for people and organizations. No matching rules or model training needed.

## What entity resolution produces

Three outputs with direct business value:

- **Matched entities.** Records from different sources referring to the same person/org grouped together — a "golden record" or "360-degree view."
- **Cross-source relationships.** Connections discovered across data sources (e.g., vendor in procurement = supplier in ERP).
- **Deduplication.** Duplicate records within and across sources identified and consolidated.

These outputs are what the bootcamp teaches you to produce, query, and put into production.
