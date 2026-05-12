---
inclusion: manual
---

# What Is Entity Resolution?

Loaded via `#[[file:]]` from `onboarding-flow.md` during Step 4a.

<!-- AGENT INSTRUCTION — not shown to the bootcamper.
Before presenting this section, call `search_docs` from the Senzing MCP server:
1. search_docs("Senzing principle-based entity resolution approach")
2. search_docs("entity resolution relationships disclosed discovered")
3. search_docs("entity resolution ambiguous match possible match")
4. search_docs("Senzing differentiators real-time explainability attribution")
5. search_docs("entity resolution pipeline standardization blocking scoring clustering")
Use retrieved content to fill in Senzing-specific claims dynamically.
-->

## What entity resolution is

Entity resolution (ER) is the discipline of figuring out, from a pile of records, which refer to the same real-world entity, which refer to different ones, and which are related. It spans multiple entity types — people and organizations alike — and underlies the counting question every downstream analytic depends on: is this one person or three? One company or five? When the count is wrong, every metric built on it drifts with it.

ER is more than fuzzy matching. Finding look-alike records is only half the job; a capable engine must also tell similar records apart, so records that happen to share attributes but belong to distinct entities are not collapsed into one.

## Why matching records is hard

Records that describe the same entity rarely arrive the same way. Source data is messy, incomplete, and often contradictory:

- **Name variations** — nicknames, initials, middle names, and transliterations ("John Smith" vs "J. Smith" vs "Jonathan Smith").
- **Address changes over time** — people move, and historical records keep stale addresses alongside current ones.
- **Format inconsistencies** — phone numbers and dates arrive in half a dozen layouts across source systems.
- **Data entry errors** — typos, transposed digits, and abbreviations the source never normalizes.

Two failure modes dominate. A false negative misses a true match, so one person ends up treated as two and the 360-degree view falls apart. A false positive overmatches the other way — a father and son who share a name and a home address get collapsed into one entity, quietly corrupting every downstream decision. Simplistic or purely fuzzy matching cannot reliably tell these cases apart.

## How entity resolution works

Capable engines share a conceptual pipeline, independent of any vendor:

- **Ingestion and standardization** — records arrive from source systems and are mapped to a common shape so later steps compare like against like.
- **Candidate selection** — blocking or indexing narrows the search space so every inbound record is compared only against a small, plausible set rather than everything on disk.
- **Comparison and scoring** — attribute-by-attribute similarity is scored across names, addresses, dates, and identifiers.
- **Classification** — each candidate pair lands as match, no match, or possible match.
- **Entity clustering** — matched records are grouped into a single resolved entity.

The most capable engines go one step further: each inbound record is compared against everything already known about an entity, not only pairwise against other records. That catches matches a purely pairwise pass would miss.

## How Senzing handles it

<!-- AGENT INSTRUCTION — not shown to the bootcamper.
Call `search_docs("Senzing principle-based entity resolution approach")` and
`search_docs("Senzing differentiators real-time explainability attribution")`
to retrieve current Senzing-specific claims. Present the retrieved content to
the bootcamper covering:
- Senzing's principle-based matching approach (frequency, exclusivity, stability)
- Pre-configured for people and organizations
- Key differentiators (real-time, no training required, explainability, scalability)
Do NOT present hardcoded facts from training data. All Senzing claims must come
from the MCP search_docs results.
-->

## Relationships and ambiguous matches

<!-- AGENT INSTRUCTION — not shown to the bootcamper.
Call `search_docs("entity resolution relationships disclosed discovered")` and
`search_docs("entity resolution ambiguous match possible match")` to retrieve
current content. Present the retrieved content covering:
- Disclosed vs discovered relationships
- Ambiguous matches and possible-match handling
Do NOT present hardcoded Senzing facts from training data.
-->

Matching records is half the job. Relationship awareness — tracking how resolved entities connect to one another — turns the match graph into something investigators, compliance analysts, and KYC workflows can reason over.

## What entity resolution produces

A capable ER engine delivers three outputs the business cares about:

- **Matched entities** — a 360-degree view, a golden record per person or organization, assembled from every source system that touches them.
- **Cross-source relationships** — the vendor in procurement turns out to be the supplier in the ERP, and two previously disconnected graphs merge into one.
- **Deduplication** — duplicate records within and across sources collapse into a single resolved entity, so counts, segments, and downstream reports stop double-counting.

Those outputs underpin use cases like fraud detection, compliance and KYC, customer 360, and investigations — anywhere a decision hinges on whether two records point at the same entity. Producing, querying, and operationalizing these three outputs is exactly what the later bootcamp modules teach.

## Sources

<!-- AGENT INSTRUCTION — not shown to the bootcamper.
All Senzing-specific claims in this file are retrieved dynamically via
`search_docs` from the Senzing MCP server at presentation time.
Cite "Senzing documentation via MCP" when the bootcamper asks for sources.
-->
