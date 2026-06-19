---
inclusion: manual
---

# Module 7 — Phase 1: Query and Visualize

> **Phase file:** This file implements Steps 1–3d (Query and Visualize) of Module 7.
> Load when the agent begins Module 7. When steps 1–3d are complete, load
> `module-07-phase2-discover.md` for steps 4a–4c.

> **Agent instruction (session resumption):** On load, read
> `config/bootcamp_progress.json` and resume from the first incomplete step.
> Do not re-run completed steps.

**Agent Workflow:**

1. **Define query requirements**:

   > **Agent instruction:** Read `docs/business_problem.md` as the first action before any bootcamper interaction in this step.

   **IF** `docs/business_problem.md` exists AND contains at least one success criterion or at least one non-empty desired output field:

   - Derive between 1 and 10 query requirements from the success criteria and desired outputs in the document. Each derived requirement must reference the specific success criterion or desired output it addresses.
   - Present the derived requirements to the bootcamper with this attribution: "Based on your business problem from Module 1, here are the query requirements I've derived:"
   - List each requirement with its source (e.g., "From your success criterion about [X]..." or "From your desired output format of [Y]...")

   👉 "Is there anything you'd like to add or change?"

   🛑 STOP — Wait for bootcamper response before proceeding.

   - **If the bootcamper accepts or modifies:** Proceed with the confirmed requirements.
   - **If the bootcamper rejects all derived requirements:** Ask a fresh open-ended question without referencing the rejected items: "What questions do you need to answer with your data?"

   **ELSE** (file does not exist, OR both success criteria and desired outputs sections are missing or empty):

   Ask: "What questions do you need to answer with your data?"

   ---

   Common queries (guidance for both paths):
   - Find duplicates within a source
   - Find cross-source matches
   - Search for specific entities
   - Get entity 360 view
   - Retrieve and format resolved entities

   **Checkpoint:** Write step 1 to `config/bootcamp_progress.json`.

2. **Create query programs**:

   For each query type, create a program in `src/query/` using the bootcamper's chosen language.

   Use `generate_scaffold` with `workflow='query'` and the chosen language, or use a query template.

   > **Agent instruction:** When generating query code that calls SDK methods accepting flags (get_entity, search_by_attributes, how_entity, why_entities, why_records, why_record_in_entity), look up available flags via `get_sdk_reference(method='<method>', topic='flags')` and select flags matching the bootcamper's query intent. Explain the flag choice: "I'm using [flag] so we can see [what it provides]." For visualization queries, include `SZ_INCLUDE_FEATURE_SCORES` and/or `SZ_INCLUDE_MATCH_KEY_DETAILS`.

   **CRITICAL:** If the generated scaffold uses `/tmp/`, `ExampleEnvironment`, or any path outside the working directory, override the database path to `database/G2C.db` and ensure all output files use project-relative paths. No files may be placed outside the working directory.

   Example queries (file extensions depend on chosen language):
   - `find_duplicates` - Find entities with multiple records
   - `search_entities` - Search by name, email, phone
   - `customer_360` - Get complete customer view
   - `query_results` - Retrieve and format resolved entities

   **Iterate over records, not entity IDs.** The caller knows the record IDs and data source codes of the records they loaded — they do NOT know entity IDs (those are internal to Senzing). Query programs should iterate over loaded records (from the input JSONL file or a record manifest) and use `get_entity_by_record_id(data_source, record_id)` to look up each record's entity. Never iterate over a guessed range of entity IDs.

   **Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.

3. **Run exploratory queries**:

   Execute queries to understand results. Use the appropriate run command for the chosen language.

3a. **Present query results and matching concepts**:

   **If entity resolution found zero or very few matches:** This is a valid result — don't assume something is broken. Tell the user: "Entity resolution found very few matches. This could mean: (a) your records are genuinely distinct with no duplicates, (b) the matching criteria need adjustment — perhaps key fields weren't mapped or data quality is too low, or (c) you're working with a single source that has no internal duplicates. Let's investigate which one." Check: are name/address/phone fields populated? Were they mapped correctly in Module 5? Is the data quality score from Module 5 above 70%? If the data genuinely has no duplicates, that's a valid finding — document it.

   **Matching concepts reminder:**

   > **Agent instruction:** When presenting query results, include a brief reminder of the matching concepts the bootcamper learned in Module 3. Cover these three points concisely — a sentence or two each, not a full re-explanation:
   >
   > - **Features** — the categories of identifying information (NAME, ADDRESS, PHONE, etc.) that Senzing extracts and compares, and how to read match key strings like `+NAME+ADDRESS+PHONE`
   > - **Confidence scores** — numeric indicators of match strength reflecting how many features agreed between records (higher means more evidence), not absolute probabilities
   > - **Cross-source connections** — matches between records from different data sources, revealing the same entity exists in multiple systems
   >
   > Adapt these reminders to the bootcamper's own data context — reference the feature types, scores, and data sources present in their current query results, not the Module 3 sample data. If the bootcamper's data involves different feature types or sources than the demo, use those instead.
   >
   > After the reminder, tell the bootcamper: "If you'd like a deeper refresher on how Senzing matching works — features, scoring, or cross-source connections — just ask and I'll walk through it again."

   > **Agent instruction:** When presenting results from `how_entity` or `why_*` methods (`why_entities`, `why_records`, `why_record_in_entity`), ensure the query was called with `SZ_INCLUDE_FEATURE_SCORES` and/or `SZ_INCLUDE_MATCH_KEY_DETAILS` flags. These flags provide the scoring detail needed for informative output. If the query used default flags, note what additional detail would be available with feature score and match key detail flags.

   **Checkpoint:** Write step 3a to `config/bootcamp_progress.json`.

3b. **Quality evaluation:**

   > **Agent instruction:** Call `reporting_guide(topic='quality', language='<chosen_language>', version='current')` to get the quality evaluation methodology. Then call `search_docs(query='entity resolution quality evaluation', version='current')` for additional context on interpreting results.

   Present a quality summary to the bootcamper:

   | Indicator | Value | Assessment |
   |-----------|-------|------------|
   | Entity-to-record ratio | [computed] | [interpretation] |
   | Possible matches | [count] ([%] of entities) | [interpretation] |
   | Cross-source match rate | [%] | [interpretation] |

   **Quality assessment:**

   - **Acceptable** (proceed): Ratio is reasonable, possible matches < 5%, no split/merge signals
   - **Marginal** (review): Possible matches 5-15% or some split/merge signals detected
   - **Poor** (iterate): Possible matches > 15%, clear split/merge patterns, or no matching occurring

   Based on the assessment:

   - **Acceptable:** "Your entity resolution quality looks good. Let's proceed to visualizations."
   - **Marginal:** "I see some potential issues. Let me show you a few specific entities to review." [Present examples, then ask if they want to proceed or iterate]
   - **Poor:** "The entity resolution results suggest mapping improvements would help. Here's what I recommend..." [Present specific recommendations and offer the Module 5 feedback loop]

   **Module 5 feedback loop (when quality is poor or bootcamper requests iteration):**

   👉 "Would you like to return to Module 5 to refine your data mapping? Your loaded data and query programs will be preserved — after remapping, you'll reload the affected sources and re-evaluate here."

   🛑 STOP — Wait for bootcamper response before proceeding.

   If accepted:

   1. Note which data sources need remapping in `config/bootcamp_progress.json` under a `quality_iteration` key
   2. Set `current_module` to 5 and `current_step` to the Phase 2 start step
   3. Load `module-05-data-quality-mapping.md` and begin at Phase 2

   **Checkpoint:** Write step 3b to `config/bootcamp_progress.json`.

3c. **Entity graph visualization checkpoint:**

   **Visualization checkpoint:** Follow the Visualization Protocol.
   Load `visualization-guide.md` and execute the offer for checkpoint `m7_exploratory_queries`.

   **Checkpoint:** Write step 3c to `config/bootcamp_progress.json`.

3d. **Results dashboard visualization checkpoint:**

   **Visualization checkpoint:** Follow the Visualization Protocol.
   Load `visualization-guide.md` and execute the offer for checkpoint `m7_findings_documented`.

   **Checkpoint:** Write step 3d to `config/bootcamp_progress.json`.

## Next: Discover Phase

4. **Discover Phase — Advanced Senzing Capabilities**:

   > **Phase files:** Load `module-07-phase2-discover.md` for steps 4a–4c
   > (data pattern analysis, why analysis, how analysis). Then load
   > `module-07-phase2b-discover.md` for steps 4d–4e (relationship networks,
   > visualization suggestions, and Discover Phase Completion).

   The Discover phase introduces advanced Senzing capabilities using concrete
   examples from the bootcamper's loaded data. It is opt-in — the bootcamper
   can decline or exit early at any demonstration point.

   **Checkpoint:** Steps 4a–4e each write individually to
   `config/bootcamp_progress.json`.

**Success Criteria:**

- ✅ Query programs created and tested
- ✅ Visualizations offered (entity graph and results dashboard)
- ✅ Discover phase completed or explicitly skipped

## Query Completeness Gate

Before wrapping up this module, confirm:

1. **Query programs created and tested?** — At least one query program runs successfully against the resolved data.
2. **Visualizations offered?** — Both the entity graph and results dashboard were offered to the bootcamper.
3. **Discover phase status?** — The Discover phase was either completed
   (all steps 4a–4e checkpointed) or explicitly skipped by the bootcamper.
4. **Ready to proceed?**
   - **Path A (full bootcamp):** Proceed to Module 8 (Performance Testing).
   - **Path B/C (shorter paths):** This is a natural stopping point. The bootcamper has working query programs and can stop here.

Present the query completion status and path options to the bootcamper:

   - **Path A (full bootcamp):** Proceed to Module 8 (Performance Testing).
   - **Path B/C (shorter paths):** This is a natural stopping point. The bootcamper has working query programs and can stop here.

The bootcamper can continue to Module 8 (Performance Testing) or stop here if this is a good stopping point for their project.

## Integration Patterns

After running queries, the bootcamper may ask "how do I use these results in my application?" Present these common integration patterns and help them choose:

| Pattern | Real-time | Complexity | Best For |
|---------|-----------|------------|----------|
| Batch Report | No | Low | Reports, analytics, data warehouse feeds |
| REST API | Yes | Medium | Web apps, microservices, customer lookup |
| Streaming/Event-Driven | Yes | High | Real-time fraud detection, alerts, Kafka integration |
| Database Sync | No | Medium | Data warehouses, BI tools, legacy system integration |
| Duplicate Detection | No | Low | Data quality initiatives, stewardship, cleanup projects |
| Watchlist Screening | Yes | Medium | Compliance (KYC/AML), risk management |

> **Agent instruction:** When the bootcamper asks about integration, use `find_examples(query='REST API')` or `find_examples(query='batch report')` for implementation patterns. Use `generate_scaffold` for code generation. Always iterate over known record IDs (from loaded data) rather than guessing entity IDs — the caller knows their records, not Senzing's internal IDs.

**Key implementation principle:** Query programs should iterate over loaded records using `get_entity_by_record_id(data_source, record_id)` — never iterate over a guessed range of entity IDs. The caller knows the record IDs and data source codes they loaded; entity IDs are internal to Senzing.

Present the integration options and help the bootcamper choose the pattern that fits their use case: batch reports, a REST API, streaming events, database sync, or duplicate detection.
