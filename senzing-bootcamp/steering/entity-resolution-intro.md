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
Use retrieved content to fill in Senzing-specific claims. If MCP unavailable,
present static content as-is and note you'll verify later. See mcp-offline-fallback.md.
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

Senzing uses principle-based matching — not hand-coded rules, not trained ML. The engine reasons about three attribute behaviors:

- **Frequency** — how common the value is. Two "John Smith" records are weak evidence; two rare-name matches are strong.
- **Exclusivity** — whether one value belongs to one entity. A Social Security number does; a phone number gets shared and reassigned.
- **Stability** — whether the value changes over time. Date of birth never moves; an address changes often.

Senzing ships preconfigured for people and organizations — no rules to write, no model to train.

Differentiators worth flagging:

- **Real-time and continuous**, not batch-only.
- **No training, fine-tuning, or ER experts** required to onboard a source.
- **Full attribution and explainability** — every resolved record traces to source system and record ID, with "why matched" / "why not matched" on demand.
- **Scales from laptop to billions of records** on the same engine.

Send Bootcampers to docs.senzing.com or MCP `search_docs` for current figures; don't hardcode numerics here.

## Relationships and ambiguous matches

Matching records is half the job. Relationship awareness — tracking how resolved entities connect to one another — turns the match graph into something investigators, compliance analysts, and KYC workflows can reason over.

Two flavors show up:

- **Disclosed relationships** are stated in the source data — "Person A is CEO of Company B," a listed beneficial owner, a next-of-kin field.
- **Discovered relationships** surface through shared attributes — two entities share an address, or a phone number threads them together.

An **ambiguous match** is a record that could legitimately belong to more than one entity — think two people with the same name in the same household. Resolving it arbitrarily is an invisible false positive: the record looks resolved but is quietly wrong. A well-designed engine flags the case as "possible match" and waits for a distinguishing attribute rather than forcing a merge.

## What entity resolution produces

A capable ER engine delivers three outputs the business cares about:

- **Matched entities** — a 360-degree view, a golden record per person or organization, assembled from every source system that touches them.
- **Cross-source relationships** — the vendor in procurement turns out to be the supplier in the ERP, and two previously disconnected graphs merge into one.
- **Deduplication** — duplicate records within and across sources collapse into a single resolved entity, so counts, segments, and downstream reports stop double-counting.

Those outputs underpin use cases like fraud detection, compliance and KYC, customer 360, and investigations — anywhere a decision hinges on whether two records point at the same entity. Producing, querying, and operationalizing these three outputs is exactly what the later bootcamp modules teach.

## Sources

- Senzing, *What Is Entity Resolution?* — <https://senzing.com/what-is-entity-resolution/>
- Senzing MCP documentation (`search_docs` tool on `mcp.senzing.com`) —
  queried at authoring time for principle-based matching, relationship
  awareness, ambiguous matches, and Senzing differentiators.
