---
inclusion: manual
---

# What Is Entity Resolution?

Loaded via `#[[file:]]` from `onboarding-flow.md` during Step 3.

<!-- AGENT INSTRUCTION (not shown to bootcamper): Display the banner below
VERBATIM as the FIRST output, before any prose (Req 1.1). Show it once per
Preface run; do NOT re-display when re-presenting the gate (Req 1.4). -->

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧩🧩🧩  ENTITY RESOLUTION CONCEPTS  🧩🧩🧩
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

<!-- AGENT INSTRUCTION (not shown to bootcamper): Source Senzing claims below
from `search_docs` (Senzing MCP), not training data. -->

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
From `search_docs` (Senzing MCP) results (not training data), present:
- Principle-based matching (frequency, exclusivity, stability)
- Pre-configured for people and organizations
- Differentiators (real-time, no training, explainability, scalability)
-->

## Relationships and ambiguous matches

<!-- AGENT INSTRUCTION — not shown to the bootcamper.
From `search_docs` (Senzing MCP) results (not training data), present:
- Disclosed vs discovered relationships
- Ambiguous matches and possible-match handling
-->

Matching records is half the job. Relationship awareness — tracking how resolved entities connect to one another — turns the match graph into something investigators, compliance analysts, and KYC workflows can reason over.

## What entity resolution produces

A capable ER engine delivers three outputs the business cares about:

- **Matched entities** — a 360-degree view, a golden record per person or organization, assembled from every source system that touches them.
- **Cross-source relationships** — the vendor in procurement turns out to be the supplier in the ERP, and two previously disconnected graphs merge into one.
- **Deduplication** — duplicate records within and across sources collapse into a single resolved entity, so counts, segments, and downstream reports stop double-counting.

Those outputs underpin use cases like fraud detection, compliance and KYC, customer 360, and investigations — anywhere a decision hinges on whether two records point at the same entity. Producing, querying, and operationalizing these three outputs is exactly what the later bootcamp modules teach.

## Explore Further

<!-- AGENT INSTRUCTION — not shown to the bootcamper.
Mandatory gate — the agent MUST stop and wait for a follow-up or readiness
signal. Rules:
- If the bootcamper asks a follow-up question: answer it using search_docs
  (Senzing MCP), then re-present this gate.
- Readiness signal ("ready", "let's go", "continue", "next"): continue.
- Ambiguous response: treat as a follow-up question, answer via MCP, re-present.
- If search_docs returns no relevant results or fails: say no documentation was
  found, suggest a rephrase, then re-present.
-->

<!-- AGENT INSTRUCTION — not shown to the bootcamper.
OPEN_QUESTIONS_PROMPT (Req 1.2, 1.5, 1.6, 2.3-2.6). End this gate turn with the
single 👉 Open_Questions_Prompt ("Do you have any questions about Entity
Resolution?") — non-compound (exactly one 👉, one ?), verbosity-aware. Do NOT
present the ILLUSTRATION_OFFER in the same turn as this prompt.
- Follow-ups, ambiguity, and search_docs failures: defer to the gate wait/answer
  directive above (answer MCP-first via search_docs, then re-present the gate;
  never re-display the banner).
- Any question the bootcamper asks is ANSWERED before the ILLUSTRATION_OFFER is
  presented.
- Once this open prompt is handled — a readiness signal or "no questions" — the
  agent presents the ILLUSTRATION_OFFER (below) as the single 👉 of the NEXT turn.
-->

<!-- AGENT INSTRUCTION — not shown to the bootcamper.
ILLUSTRATION_OFFER (Req 3.1-3.7) — PHASE B. Do NOT present this in the same turn
as the Open_Questions_Prompt. Present it only AFTER the Open_Questions_Prompt has
been handled — i.e. the bootcamper signaled readiness / "no questions" and any
asked question has already been ANSWERED (Req 3.1). When that condition is met,
open its own later turn with this as the SINGLE 👉 call-to-action — an OPTIONAL,
non-compound (one 👉, one ?), verbosity-aware offer to view the ER_Illustration
(a tiny match + non-match teaser), e.g. "Want to see a quick two-record example
of a match and a non-match before we move on?" (Req 3.2, 3.3). One 👉 only; never
changes the gate's wait semantics:
- Accept: render the ER_Illustration inline, then re-present the gate (Req 3.6);
  never re-display the banner.
- Decline or a readiness signal: proceed past the gate, no penalty (Req 3.4).
- Ask-Once: once the offer has been answered (accept / decline / readiness), do
  NOT offer it again (Req 3.5).
- Unrecognized response (not an accept, decline, or readiness signal): re-present
  this offer ONCE as the single 👉, indicating an accept-or-decline response is
  expected, and do NOT proceed past the gate until a recognized response is
  received (Req 3.7).
-->

⛔ **MANDATORY GATE** — Entity Resolution Exploration

That covers the foundations of entity resolution. Before we move on, this is a good moment to dig deeper if anything sparked your curiosity.

Here are some questions other bootcampers have found useful:

- "How does Senzing match records without rules?"
- "What's the difference between matching and relating?"
- "What kinds of data does entity resolution work with?"

You can ask any question about entity resolution — not just these examples. When you're ready to move on, just say so.

👉 **Do you have any questions about Entity Resolution?**

🛑 **STOP — End your response here.** Do not proceed. Do not assume a response. Wait for the bootcamper's real input.

<!-- AGENT INSTRUCTION — not shown to the bootcamper.
ER_ILLUSTRATION (Req 1.2-1.4, 2.4, 3.1, 3.2, 4.1-4.4). Render INLINE only on
ACCEPT, then re-present the gate (banner once-only). Conceptual teaser ONLY —
static, text-based, NO MORE THAN 25 lines (Req 4.1); no SDK, data, code, server,
or graph; do NOT reproduce the Module 3 "wow" visualization. End with a PREVIEW
line pointing to that hands-on Module 3 visualization on their own data. If the
bootcamper requests the interactive entity graph or full visualization while the
illustration is displayed: DECLINE to render it, leave the conceptual preview
unchanged, and DIRECT them to the Module 3 hands-on visualization (Req 4.4).
Sourcing (MCP-first, Req 1.4): prefer records + reasoning via find_examples
/ search_docs; else a GENERIC FALLBACK (label "illustrative, not Senzing data"):
- MATCH: "Robert Smith, 12 Oak St" vs "Bob Smith, 48 Elm Ave (prior)" — name
  variation + prior address; same entity; missing it = FALSE NEGATIVE.
- NON-MATCH / POSSIBLE MATCH: "William Jones b.1958" vs "William Jones b.1985"
  (father/son, shared name+address) — different entities; merging = FALSE
  POSITIVE (keep apart/flag).
-->

## Sources

<!-- AGENT INSTRUCTION — not shown to the bootcamper.
Senzing claims come from `search_docs` (Senzing MCP) at presentation time; cite
"Senzing documentation via MCP" for sources.
-->
