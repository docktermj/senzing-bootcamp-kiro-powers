---
inclusion: manual
---

# Module 7 — Phase 2: Discover

> **Phase file:** This file implements Step 4 (Discover Phase) of Module 7.
> Load when the agent reaches step 4 in `module-07-query-visualize-discover.md`.
> When complete, return to the root file for the Query Completeness Gate.

> **Agent instruction (session resumption):** On load, read
> `config/bootcamp_progress.json` and check which step 4x sub-steps are
> already completed. Resume from the first incomplete step. Do not re-run
> completed demonstrations.

## Step 4: Discover Phase — Advanced Senzing Capabilities

The Discover phase introduces advanced Senzing capabilities using concrete
examples from the bootcamper's loaded data. It is opt-in — the bootcamper
can decline or exit early at any demonstration point.

### Introduction and Opt-in

> **Agent instruction:** Present a brief introduction explaining what the
> Discover phase covers: why analysis (understanding resolution decisions),
> how analysis (entity construction history), relationship networks (hidden
> connections), and data-specific visualizations. Ask the bootcamper if they
> want to proceed.
>
> If the bootcamper declines, write `discover_phase: "skipped"` to
> `config/bootcamp_progress.json` under `module_7_query` and return to the
> root file for the Query Completeness Gate.
>
> If the bootcamper agrees to proceed, write `discover_phase: "in_progress"`
> to `config/bootcamp_progress.json` under `module_7_query` and continue to
> step 4a.

### Step 4a: Data Pattern Analysis

> **Agent instruction:** Analyze the bootcamper's loaded data to identify
> interesting entities suitable for the Discover phase demonstrations. Use
> the bootcamper's known record IDs from their loaded data (available in
> `config/bootcamp_progress.json` under the module 5 loading results or
> from the data sources configured in `config/data_sources.yaml`).
>
> **1. Identify multi-record entities (3+ records):**
> Iterate over the bootcamper's loaded record IDs and call
> `get_entity_by_record_id(data_source, record_id)` for each record. Collect
> entities where `record_count >= 3`. These are candidates for the How
> Analysis demonstration (step 4c). Track the entity IDs and record counts.
>
> **2. Identify cross-source entities:**
> From the multi-record entities found in step 1, filter for entities whose
> constituent records originate from two or more distinct data sources. These
> are candidates for the Why Analysis demonstration (step 4b). An entity
> qualifies if its records array contains entries with different
> `DATA_SOURCE` values.
>
> **3. Identify relationship clusters:**
> From the entities found, check for disclosed relationships by examining
> the entity response for relationship data. Entities with one or more
> disclosed relationships are candidates for the Relationship Network
> demonstration (step 4d). Use relationship flags when calling
> `get_entity_by_record_id` to include relationship information in the
> response.
>
> **4. SDK flag usage:**
> Explain your flag choices to the bootcamper as you perform the analysis.
> For example: "I'm using `get_entity_by_record_id` with relationship flags
> so we can see which entities have connections to other entities — this
> helps me find good candidates for the relationship network demonstration."
>
> **5. Present a summary:**
> After completing the analysis, present a brief summary to the bootcamper:
> "I found N large entities (3+ records), M cross-source matches (records
> from multiple data sources), and K relationship clusters in your data."
> List the most interesting candidates by entity ID and briefly describe why
> each is interesting (e.g., "Entity 1234 has 5 records from 2 sources" or
> "Entity 5678 has 3 disclosed relationships").
>
> **6. Graceful fallback for limited data:**
> If fewer than 2 multi-record entities exist in the bootcamper's data,
> explain: "Your data has limited resolution results — most records resolved
> as singletons (one record per entity). This is common with small or
> homogeneous datasets." Adapt the remaining demonstrations to use whatever
> entities are available. If only single-record entities exist, use them to
> demonstrate the SDK methods while explaining what the output would look
> like with richer data. Skip demonstrations that require unavailable
> patterns (e.g., skip relationship networks if no relationships exist) and
> note which steps are being skipped and why.

**Checkpoint:** Write step 4a to `config/bootcamp_progress.json` under
`module_7_query.steps.4a`. Use this structure:
`{"status": "completed", "patterns_found": {"multi_record": N, "cross_source": M, "relationships": K}}`
where N, M, and K are the actual counts of multi-record entities, cross-source
entities, and relationship clusters found in the bootcamper's data.

### Step 4b: Why Analysis Introduction

> **Agent instruction:** Demonstrate Why Analysis using a concrete
> Cross_Source_Entity identified in step 4a. This step teaches the
> bootcamper how Senzing explains its resolution decisions.
>
> **1. Entity selection:**
> Select a cross-source entity identified during step 4a — one whose
> constituent records come from two or more distinct data sources. Use the
> specific record IDs from that entity to call `why_records`, or use the
> entity IDs to call `why_entities`. Prefer `why_records` for the initial
> demonstration because it shows the comparison between two specific source
> records, which is easier to follow. State which entity and records you
> are using: "I'll use Entity [ID] which contains records from [Source A]
> and [Source B] — let's see why Senzing decided these belong to the same
> real-world entity."
>
> **2. SDK method introduction:**
> Before calling the SDK, briefly explain the two Why Analysis methods:
>
> - `why_records` — compares two specific source records and explains why
>   they resolved together. Use this when you know exactly which two records
>   you want to compare.
> - `why_entities` — compares two resolved entities and explains why they
>   are (or are not) the same. Use this when investigating whether two
>   entities should merge or when auditing a split decision.
>
> **3. SDK flags:**
> Call `why_records` (or `why_entities`) with BOTH of these flags:
>
> - `SZ_INCLUDE_FEATURE_SCORES` — explain: "I'm using
>   SZ_INCLUDE_FEATURE_SCORES so we can see the numeric similarity scores
>   for each feature comparison — this tells us how closely each attribute
>   matched between the two records."
> - `SZ_INCLUDE_MATCH_KEY_DETAILS` — explain: "I'm using
>   SZ_INCLUDE_MATCH_KEY_DETAILS so we can see exactly which feature
>   combinations triggered the resolution — this is the match key that
>   Senzing used to decide these records belong together."
>
> **4. Plain-language explanation of the output:**
> After receiving the Why Analysis response, explain the output in plain
> language covering these three aspects:
>
> - **Features that matched:** List which features (NAME, ADDRESS, DOB,
>   PHONE, etc.) were compared between the two records and which ones
>   matched. For example: "The NAME and ADDRESS features both matched
>   between these records."
> - **Feature Scores:** For each feature comparison, explain the numeric
>   similarity score. For example: "The name comparison scored 95 out of
>   100, meaning the names are very similar but not identical — this is
>   because one record has 'Robert Smith' and the other has 'Bob Smith'."
>   Explain what the score range means (higher = more similar).
> - **Matching principle:** Explain which matching principle applied to
>   each feature comparison — exact match (identical values), close match
>   (very similar, like name variants), or likely match (similar enough to
>   contribute to resolution). For example: "The name matched on a 'close
>   match' principle because 'Robert' and 'Bob' are recognized name
>   variants."
>
> **5. Match key breakdown:**
> Present the match key string (e.g., `+NAME+ADDRESS`) and break it down:
>
> - Explain that each `+FEATURE` component represents a feature type that
>   contributed positively to the resolution decision.
> - Explain what each component means in context: "The `+NAME` means the
>   name features matched strongly enough to contribute. The `+ADDRESS`
>   means the address features also matched. Together, these two matching
>   features were sufficient for Senzing to resolve these records."
> - If the match key contains `-FEATURE` components (negative
>   contributions), explain those as well: "A `-` prefix means that feature
>   did NOT match, but the other matching features were strong enough to
>   override it."
>
> **6. Practical use cases:**
> After the demonstration, explain when Why Analysis is useful in practice:
>
> - **Auditing decisions:** "When a stakeholder asks 'why did you merge
>   these two customer records?', why analysis gives you the exact answer
>   with scores and matching principles."
> - **Debugging unexpected merges:** "If two records merged that shouldn't
>   have, why analysis shows you exactly which features caused it — helping
>   you decide whether to adjust your configuration or add a data fix."
> - **Compliance reporting:** "For regulated industries (KYC, AML, patient
>   matching), why analysis provides the auditable evidence trail showing
>   how each resolution decision was made."
>
> **7. Transition:**
> Ask the bootcamper: "Would you like to continue to the next
> demonstration (How Analysis — seeing how this entity was built step by
> step), or proceed to module completion?"
> If the bootcamper chooses to exit, write `discover_phase: "skipped"` to
> `config/bootcamp_progress.json` and return to the root file for the
> Query Completeness Gate.

**Checkpoint:** Write step 4b to `config/bootcamp_progress.json` under
`module_7_query.steps.4b`. Use this structure:
`{"status": "completed", "entity_demonstrated": <entity_id>}`
where `<entity_id>` is the numeric entity ID used in the Why Analysis
demonstration.

### Step 4c: How Analysis Introduction

> **Agent instruction:** Demonstrate How Analysis using a concrete
> Multi_Record_Entity (3+ records) identified in step 4a. This step teaches
> the bootcamper how Senzing constructs entities over time as records are
> added.
>
> **1. Entity selection:**
> Select a multi-record entity with 3+ records identified during step 4a.
> State which entity you are using and why it is a good candidate: "I'll
> use Entity [ID] which has [N] records — this gives us enough construction
> steps to see a meaningful history of how Senzing built this entity over
> time."
>
> **2. SDK flag:**
> Call `how_entity` with the `SZ_INCLUDE_FEATURE_SCORES` flag. Explain:
> "I'm using SZ_INCLUDE_FEATURE_SCORES so we can see the scoring at each
> construction step — this shows how closely features matched each time a
> new record was added to this entity."
>
> **3. Chronological narrative presentation:**
> Present the How Analysis output as a chronological narrative showing the
> entity's construction history step by step:
>
> - Each step where a new record was added to the entity
> - Which features caused the merge at that step
> - The feature scores at each step
>
> Use a narrative format like:
> "Step 1: Record A from [Source] was the first record — it established
> the entity. Step 2: Record B from [Source] was added because [features
> matched with scores]. Step 3: Record C from [Source] was added because
> [features matched with scores]."
>
> Walk through each step so the bootcamper can follow the entity's growth
> from a single record to its current multi-record state.
>
> **4. Why-vs-How comparison:**
> After the demonstration, explain the difference between Why Analysis and
> How Analysis:
>
> - **Why Analysis:** Compares two specific records or entities and explains
>   the current resolution decision — "why are these together right now?"
> - **How Analysis:** Shows the full construction history of one entity —
>   the chronological sequence of merges as records were added over time.
>
> Use this analogy: "Why is like asking 'why are these two people in the
> same room?' — How is like watching the security camera footage of
> everyone entering the room in order."
>
> **5. Practical use cases:**
> Explain when How Analysis is useful in practice:
>
> - **Understanding entity growth over time:** "How analysis lets you see
>   the timeline of an entity's construction — when each record was added
>   and what triggered each merge."
> - **Investigating over-merging:** "If an entity has too many records
>   merged into it, how analysis shows you exactly where the chain of
>   merges went wrong — which step introduced the problematic record."
> - **Data stewardship:** "When deciding whether to split an entity, how
>   analysis shows you the merge sequence so you can identify the weakest
>   link in the chain and make an informed split decision."
>
> **6. Transition:**
> Ask the bootcamper: "Would you like to continue to the next
> demonstration (Relationship Networks — exploring how entities connect
> to each other), or proceed to module completion?"
> If the bootcamper chooses to exit, write `discover_phase: "skipped"` to
> `config/bootcamp_progress.json` and return to the root file for the
> Query Completeness Gate.

**Checkpoint:** Write step 4c to `config/bootcamp_progress.json` under
`module_7_query.steps.4c`. Use this structure:
`{"status": "completed", "entity_demonstrated": <entity_id>}`
where `<entity_id>` is the numeric entity ID used in the How Analysis
demonstration.

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
