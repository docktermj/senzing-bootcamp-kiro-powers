---
inclusion: manual
---

# Module 7 — Phase 2: Discover (Part B)

> **Phase file:** This file implements Steps 4d–4e (Discover Phase) of Module 7.
> Load after completing steps 4a–4c in `module-07-phase2-discover.md`.
> When complete, return to the root file for the Query Completeness Gate.

> **Agent instruction (session resumption):** On load, read
> `config/bootcamp_progress.json` and check which step 4x sub-steps are
> already completed. Resume from the first incomplete step. Do not re-run
> completed demonstrations.

## Steps 4d–4e: Discover (continued)

### Step 4d: Relationship Network Exploration

> **Agent instruction:** Demonstrate Relationship Network exploration using
> entities identified in step 4a that have disclosed relationships or shared
> attributes. This step teaches the bootcamper how to explore connections
> between entities using `find_network` and `find_path`.
>
> **1. Entity selection:**
> Use entities identified in step 4a that have disclosed relationships or
> shared attributes. State which entities you are using and why: "I'll use
> Entities [ID1], [ID2], and [ID3] which have disclosed relationships or
> shared attributes — these give us a connected set of entities to explore
> as a network."
>
> **2. Flag lookup:**
> Before calling `find_network` or `find_path`, look up available flags
> via the SDK reference:
>
> - Call `get_sdk_reference(method='find_network', topic='flags')` to
>   discover available flags for network exploration.
> - Call `get_sdk_reference(method='find_path', topic='flags')` to
>   discover available flags for path finding.
>
> Select flags appropriate for relationship exploration. Explain each flag
> choice to the bootcamper: "I'm using [flag] so we can see [what it
> provides]." For example: "I'm using [relationship detail flag] so we can
> see the full attribute information for each entity in the network — this
> helps us understand what connects them."
>
> **3. find_network demonstration:**
> Call `find_network` with a set of related entity IDs (at least 2–3
> entities from the relationship clusters identified in step 4a). Present
> the resulting network structure showing:
>
> - **Which entities are connected:** List each entity in the network and
>   its connections to other entities. Show the entity IDs and brief
>   identifying information (name, data source).
> - **What attributes they share:** For each connection, explain what
>   attributes the entities have in common — shared addresses, phone
>   numbers, names, or other features that create the link.
> - **Degrees of separation:** Show how many hops separate each pair of
>   entities in the network. For example: "Entity A is directly connected
>   to Entity B (1 degree), and Entity B connects to Entity C (so A and C
>   are 2 degrees apart)."
>
> Present this as a clear textual network diagram or structured list so
> the bootcamper can follow the connections.
>
> **4. find_path demonstration:**
> Demonstrate `find_path` between two entities that are indirectly
> connected (2+ degrees of separation if available). Show the shortest
> path of relationships between them:
>
> - State which two entities you are finding a path between and why:
>   "Let's find the shortest path between Entity [ID1] and Entity [ID2] —
>   these aren't directly connected, so we'll see the intermediate
>   entities that link them."
> - Present each step in the path: Entity A → Entity B → Entity C, with
>   the connecting attributes at each hop.
> - Explain what the path reveals about the relationship between the two
>   endpoint entities.
>
> **5. Network structure explanation:**
> Explain the network output clearly to the bootcamper:
>
> - **How entities connect through shared attributes:** "Entities in
>   Senzing connect through shared features — when two entities share an
>   address, phone number, or other attribute, that creates a relationship
>   link between them."
> - **What relationship types mean:** Explain disclosed relationships
>   (explicitly stated in source data, like 'spouse' or 'employer') versus
>   discovered relationships (inferred from shared attributes like a common
>   address).
> - **How to interpret degrees of separation:** "Degrees of separation
>   tell you how many entity-to-entity hops are needed to connect two
>   entities. Direct connections are 1 degree; connections through an
>   intermediary are 2 degrees, and so on."
>
> **6. Practical use cases:**
> Explain when relationship network exploration is useful in practice:
>
> - **Fraud ring detection:** "Find_network reveals clusters of connected
>   entities that share attributes — this is how investigators discover
>   fraud rings where multiple identities share addresses, phones, or
>   other features."
> - **Supply chain analysis:** "Tracing entity connections helps identify
>   hidden relationships between suppliers, intermediaries, and end
>   customers in complex supply chains."
> - **Beneficial ownership tracing:** "Find_path can trace the chain of
>   relationships from a company to its ultimate beneficial owners through
>   intermediate entities."
> - **Customer household grouping:** "Find_network identifies entities
>   that share a household address, helping group related customers for
>   marketing or risk assessment."
>
> **7. Graceful fallback (no relationships in data):**
> If the bootcamper's data contains no entity relationships or disclosed
> connections (as determined in step 4a), do NOT attempt the live
> demonstration. Instead:
>
> - State: "Your data doesn't contain disclosed relationships, so I'll
>   explain what this would look like with connected data."
> - Describe what `find_network` returns when entities are connected:
>   a graph structure showing entity nodes, relationship edges, shared
>   attributes at each connection, and degrees of separation.
> - Describe what `find_path` returns: an ordered list of entities
>   forming the shortest path between two endpoints, with the connecting
>   attributes at each hop.
> - Explain the SDK methods conceptually so the bootcamper understands
>   how to use them when they have relationship-rich data.
> - Write step 4d status as `"skipped"` with reason `"no_relationships"`
>   in the checkpoint.
>
> **8. Transition:**
> Ask the bootcamper: "Would you like to continue to the next
> demonstration (Visualization Suggestions — data-specific analytical
> views), or proceed to module completion?"
> If the bootcamper chooses to exit, write `discover_phase: "skipped"` to
> `config/bootcamp_progress.json` and return to the root file for the
> Query Completeness Gate.

**Checkpoint:** Write step 4d to `config/bootcamp_progress.json` under
`module_7_query.steps.4d`. Use this structure:

- If relationships were demonstrated: `{"status": "completed"}`
- If no relationships exist in data: `{"status": "skipped", "reason": "no_relationships"}`

Include the `reason` field only when the step is skipped.

### Step 4e: Data-Specific Visualization Suggestions

> **Agent instruction:** Suggest at least two visualizations tailored to the
> bootcamper's data structure and resolution results. Select from the
> visualization catalog below based on what was found in step 4a.
>
> **1. Visualization catalog — select based on the bootcamper's data:**
>
> - **Cross-source overlap heatmap** — suggest when 2+ data sources are
>   loaded. Reveals which sources share the most resolved entities. Example
>   framing: "Since you have records from [Source A] and [Source B], a
>   cross-source overlap heatmap would show you which sources share the most
>   resolved entities — helping you see where your data sources agree."
> - **Entity size distribution chart** — suggest for any data. Shows the
>   distribution of records per entity (singletons vs. small merges vs.
>   large merges). Example framing: "An entity size distribution chart would
>   show you how your records clustered — how many entities are singletons
>   versus multi-record merges."
> - **Relationship network graph** — suggest when relationships exist (as
>   found in step 4a). Shows how entities connect through shared attributes.
>   Example framing: "Since your data has relationship clusters, a network
>   graph would visualize how entities connect through shared attributes."
> - **Match key frequency analysis** — suggest when multi-record entities
>   exist. Shows which feature combinations (match keys) drive the most
>   resolutions. Example framing: "A match key frequency chart would show
>   you which feature combinations — like NAME+ADDRESS or NAME+DOB — are
>   driving the most resolutions in your data."
> - **Feature score distribution** — suggest when multi-record entities
>   exist. Shows how closely features match across resolved records.
>   Example framing: "A feature score distribution would show you how
>   tightly your resolved records match — whether most merges are near-exact
>   or fuzzy matches."
>
> **2. Selection logic:**
> Select at least 2 visualizations that are relevant to the bootcamper's
> specific data structure based on the patterns found in step 4a. Do not
> suggest visualizations that require data patterns not present in the
> bootcamper's data. For example:
>
> - Do not suggest the cross-source heatmap if only one data source is
>   loaded.
> - Do not suggest the relationship network graph if no relationships were
>   found in step 4a.
> - Do not suggest match key frequency or feature score distribution if no
>   multi-record entities exist.
> - The entity size distribution chart is always applicable.
>
> **3. Relevance explanation:**
> For each suggested visualization, explain concretely what it would reveal
> about the bootcamper's specific data. Reference their actual data sources,
> entity counts, and patterns found in step 4a. Be specific rather than
> generic — use the bootcamper's source names and counts. For example:
> "Since you have 5 cross-source entities spanning CUSTOMERS and WATCHLIST,
> a cross-source overlap heatmap would show you exactly how much overlap
> exists between those two sources."
>
> **4. Generation:**
> When the bootcamper selects a visualization to explore, generate it using
> the bootcamper's chosen language and the visualization patterns from
> `visualization-guide.md`. Reference that steering file for code structure,
> charting library selection, and output format. Generate working code that
> queries the bootcamper's actual data and produces the selected
> visualization.
>
> **5. Handle decline:**
> If the bootcamper declines all visualization suggestions, acknowledge the
> decision gracefully and proceed to the module completion gate. Do not push
> or re-offer visualizations after a decline.
>
> **6. Transition:**
> After visualization generation (or decline), return to the root file
> (`module-07-query-visualize-discover.md`) for the Query Completeness Gate.

**Checkpoint:** Write step 4e to `config/bootcamp_progress.json` under
`module_7_query.steps.4e`. Use this structure:

- If visualizations were offered: `{"status": "completed", "visualizations_offered": N}`
  where N is the number of visualizations suggested to the bootcamper.
- If the step was skipped: `{"status": "skipped", "visualizations_offered": 0}`

### Discover Phase Completion

> **Agent instruction:** After step 4e is complete (or after any early exit),
> update the top-level `discover_phase` status in `config/bootcamp_progress.json`
> under `module_7_query`:
>
> - Set `"discover_phase": "completed"` when all steps 4a–4e have been
>   checkpointed (whether completed or individually skipped due to data
>   limitations).
> - Set `"discover_phase": "skipped"` when the bootcamper declines the
>   Discover phase at the opt-in prompt or exits early at any transition
>   point.
>
> The full checkpoint structure in `config/bootcamp_progress.json` is:
>
> ```json
> {
>   "module_7_query": {
>     "steps": {
>       "4a": {"status": "completed", "patterns_found": {"multi_record": 5, "cross_source": 3, "relationships": 2}},
>       "4b": {"status": "completed", "entity_demonstrated": 1234},
>       "4c": {"status": "completed", "entity_demonstrated": 5678},
>       "4d": {"status": "completed"},
>       "4e": {"status": "completed", "visualizations_offered": 2}
>     },
>     "discover_phase": "completed"
>   }
> }
> ```
>
> After updating the `discover_phase` status, return to the root file
> (`module-07-query-visualize-discover.md`) for the Query Completeness Gate.

**Success:** Discover phase completed (or explicitly skipped) — data patterns analyzed, why/how analysis demonstrated, relationship networks explored, and visualization suggestions offered.
