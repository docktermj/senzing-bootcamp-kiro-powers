---
inclusion: manual
---

# Module 7: Query and Visualize

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_7_QUERY_VALIDATION.md`.

**Purpose:** Create query programs and visualizations.

**Before/After**: Your data is loaded and entities are resolved, but you haven't examined the results yet. After this module, you'll have query programs that answer your business questions and visualizations of your resolved entities.

**Prerequisites:**

- ✅ Module 6 complete (all sources loaded, single or multi-source)
- ✅ No critical loading errors

**Agent Workflow:**

1. **Define query requirements**:

   Ask: "What questions do you need to answer with your data?"

   Common queries:
   - Find duplicates within a source
   - Find cross-source matches
   - Search for specific entities
   - Get entity 360 view
   - Retrieve and format resolved entities

   **Checkpoint:** Write step 1 to `config/bootcamp_progress.json`.

2. **Create query programs**:

   For each query type, create a program in `src/query/` using the bootcamper's chosen language.

   Use `generate_scaffold` with `workflow='query'` and the chosen language, or use a query template.

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
   Load `visualization-protocol.md` and execute the offer for checkpoint `m7_exploratory_queries`.

   **Checkpoint:** Write step 3c to `config/bootcamp_progress.json`.

3d. **Results dashboard visualization checkpoint:**

   **Visualization checkpoint:** Follow the Visualization Protocol.
   Load `visualization-protocol.md` and execute the offer for checkpoint `m7_findings_documented`.

   **Checkpoint:** Write step 3d to `config/bootcamp_progress.json`.

**Success Criteria:**

- ✅ Query programs created and tested
- ✅ Visualizations offered (entity graph and results dashboard)

## Query Completeness Gate

Before wrapping up this module, confirm:

1. **Query programs created and tested?** — At least one query program runs successfully against the resolved data.
2. **Visualizations offered?** — Both the entity graph and results dashboard were offered to the bootcamper.
3. **Ready to proceed?**
   - **Path A (full bootcamp):** Proceed to Module 8 (Performance Testing).
   - **Path B/C (shorter paths):** This is a natural stopping point. The bootcamper has working query programs and can stop here.

Present the query completion status and path options to the bootcamper:

   - **Path A (full bootcamp):** Proceed to Module 8 (Performance Testing).
   - **Path B/C (shorter paths):** This is a natural stopping point. The bootcamper has working query programs and can stop here.

The bootcamper can continue to Module 8 (Performance Testing) or stop here if this is a good stopping point for their project.

**Success indicator**: ✅ Query programs created and tested + queries answer business problem + visualizations offered (entity graph and results dashboard)

## Error Handling

When the bootcamper encounters an error during this module:

1. **Check for SENZ error code** — if the error message contains a code matching `SENZ` followed by digits (e.g., `SENZ2027`):
   - Call `explain_error_code(error_code="<code>", version="current")`
   - Present the explanation and recommended fix to the bootcamper
   - If `explain_error_code` returns no result, continue to step 2
2. **Load `common-pitfalls.md`** — navigate to this module's section and present only the matching pitfall and fix
3. **Check cross-module resources** — if no match in the module section, check the Troubleshooting by Symptom table and General Pitfalls section

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
