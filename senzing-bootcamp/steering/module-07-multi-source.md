---
inclusion: manual
---

# Module 7: Multi-Source Orchestration

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_7_MULTI_SOURCE_ORCHESTRATION.md`.

**Purpose**: Coordinate loading of multiple data sources with dependencies, conflict resolution, and optimization.

**Before/After**: You have one source loaded. After this module, all your sources are loaded with cross-source matching — Senzing is finding connections between records from different systems.

**Prerequisites**:

- ✅ Module 6 complete (first source loaded successfully)
- ✅ Multiple data sources mapped and transformed (Module 5)
- ✅ Loading statistics reviewed for first source
- ✅ Redo queue drained for first source

## Agent Workflow

> **Agent instruction:** Before starting multi-source orchestration, check for anti-patterns:
> `search_docs(query="multi-source loading orchestration", category="anti_patterns", version="current")`.
> Key pitfalls include threading issues, redo processing, and load order dependencies.

1. **Check anti-patterns and prepare**:

   Call `search_docs(query="multi-source loading orchestration", category="anti_patterns", version="current")` and review results. Flag any pitfalls relevant to the bootcamper's data sources and chosen language.

2. **Inventory all data sources**:

   Enumerate every data source from previous modules. For each source, gather:
   - Source name and DATA_SOURCE identifier
   - Record count (from Module 3/4)
   - Data quality score (from Module 4)
   - Mapping status (from Module 5 — complete, partial, or pending)
   - Whether it was already loaded in Module 6

   Present a summary table to the bootcamper:

   ```text
   Source           | Records | Quality | Mapped | Loaded
   -----------------+---------+---------+--------+-------
   CUSTOMERS_CRM    |  50,000 |   92%   |   ✅   |   ✅
   ECOMMERCE_ACCTS  |  35,000 |   85%   |   ✅   |   ❌
   SUPPORT_TICKETS  |  20,000 |   78%   |   ✅   |   ❌
   ```

   👉 "Here are all the data sources from your project. Are there any sources missing, or any changes to this list?"

   WAIT for response.

3. **Analyze dependencies**:

   👉 "Do any of your data sources depend on others being loaded first? For example, do orders reference customers, or do transactions reference accounts?"

   WAIT for response.

   Common dependency patterns:
   - **Parent-child**: Load parents first (customers before orders)
   - **Reference data**: Load lookups first (countries, product catalogs)
   - **Temporal ordering**: Load historical data first for baseline
   - **No dependencies**: Sources are independent (can load in any order or in parallel)

   **Circular dependency detection**: If the bootcamper describes dependencies where A depends on B and B depends on A, flag this: "These sources have a circular dependency — A needs B loaded first, but B also needs A. In Senzing, this usually means neither truly depends on the other for entity resolution. Senzing resolves entities as records arrive, so load order affects which entity IDs form first but not the final resolution quality. I'd recommend loading the higher-quality source first."

   Create a dependency map and save to `docs/loading_strategy.md`.

4. **Determine load order**:

   Apply these ordering heuristics (in priority order) to recommend a sequence:

   1. **Reference before transactional**: Load reference/master data (products, countries) before transactional data (orders, claims)
   2. **Quality-first**: Load the highest-quality source first to establish a strong entity baseline — better initial entities mean better matching for subsequent sources
   3. **Attribute-density-first**: Load sources with the most identifying attributes (name + email + phone + address) before sparse sources (name only)
   4. **Volume-first**: When quality is similar, load the largest source first for maximum baseline coverage

   Present the recommended order with rationale:

   👉 "Based on your data, I recommend this load order: [order with reasons]. Does this look right, or would you prefer a different sequence?"

   WAIT for response.

5. **Select loading strategy**:

   👉 "How would you like to load the remaining sources?"

   Present options with trade-offs:
   - **Sequential**: One source at a time. Safer, easier to debug, lower resource usage. Best for first-time orchestration or when sources have dependencies.
   - **Parallel**: Multiple sources at once. Faster, but requires more memory and CPU. Best when sources are independent and you want speed.
   - **Hybrid**: Sequential for dependent sources, parallel for independent ones. Best balance of safety and speed.

   WAIT for response.

6. **Pre-load validation checklist**:

   Before starting orchestration, verify:
   - [ ] All source JSONL files exist in `data/transformed/` and are non-empty
   - [ ] Each source has a unique DATA_SOURCE name matching Module 0 configuration
   - [ ] RECORD_IDs are unique within each DATA_SOURCE
   - [ ] Database backup exists (run `python scripts/backup_project.py` if not)
   - [ ] Sufficient disk space for the database to grow (estimate ~2x current size per additional source)
   - [ ] Loading program from Module 6 works as a template for the orchestrator

   If any check fails, fix it before proceeding. Tell the bootcamper what failed and how to fix it.

7. **Create orchestrator program**:

   > **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')` for the loading pattern.
   > Use `find_examples(query="queue loading", language="<chosen_language>")` or `find_examples(query="multi-source")` for real-world orchestration patterns.

   **CRITICAL**: If the generated scaffold uses `/tmp/`, `ExampleEnvironment`, or any path outside the working directory, override the database path to `database/G2C.db` and ensure all output files use project-relative paths.

   Save to `src/load/orchestrator.[ext]` (using the appropriate file extension for the chosen language).

   The orchestrator must handle:
   - Loading sources in the determined order
   - Dependency enforcement (don't start a source until its dependencies are loaded)
   - Parallel execution if selected (language-appropriate concurrency)
   - Per-source progress tracking (records loaded, errors, duration)
   - Per-source error isolation (one source failing does not stop others)
   - Statistics aggregation across all sources
   - A summary report at completion

8. **Test with sample data**:

   Before running on full data, test the orchestrator with a small subset (10-100 records per source).

   Verify:
   - All sources load without errors
   - Dependencies are respected (dependent sources wait)
   - Progress tracking works
   - Error handling triggers correctly (intentionally introduce a bad record to test)

   👉 "The orchestrator ran successfully on sample data. Ready to run on the full dataset?"

   WAIT for response.

9. **Run full orchestration**:

   Run the orchestrator on the complete dataset. Monitor and report:
   - Per-source progress (records loaded / total, percentage)
   - Per-source error count and error rate
   - Overall completion percentage
   - Elapsed time and estimated time remaining
   - Resource utilization notes (if loading is slow, suggest reducing parallelism)

   **⚠️ SQLite performance note:** With multiple sources on SQLite, loading gets progressively slower as the database grows. If total records across all sources exceed 1,000, recommend loading a subset first: "Let's load the first 500 records per source to validate cross-source matching. Once we confirm results in Module 8, we can load more — or switch to PostgreSQL for better performance (Module 9 covers this)."

10. **Process redo queue**:

    After all sources are loaded, drain the redo queue. Redos are especially important after multi-source loading because cross-source matches generate additional re-evaluations.

    Use `generate_scaffold(language='<chosen_language>', workflow='redo', version='current')` for the redo processing pattern.

    **CRITICAL**: Override any `/tmp/` or `ExampleEnvironment` paths to `database/G2C.db`.

    Tell the bootcamper: "Processing the redo queue now. This refines cross-source entity resolution — without it, some matches between your sources would be incomplete."

11. **Validate cross-source results**:

    After redo processing completes, validate:
    - Record counts per source match expectations
    - Cross-source entities exist (entities with records from multiple DATA_SOURCEs)
    - No unexpected data loss (total records in ≈ total records loaded)
    - Error logs are clean or errors are understood

    > **Agent instruction:** Use `reporting_guide(topic='graph', version='current')` to get network graph export patterns for visualizing cross-source entity relationships.

    👉 "Would you like me to visualize the cross-source entity relationships as a web page? It'll show how entities connect across your data sources."

    WAIT for response.

    If yes, generate an HTML visualization and save to `docs/multi_source_results.html`.

12. **Document results**:

    Update `docs/loading_strategy.md` with:
    - Final load order and rationale
    - Per-source statistics (records, duration, error rate)
    - Cross-source match summary
    - Any issues encountered and how they were resolved
    - Recommendations for future loads (e.g., switch to PostgreSQL, adjust parallelism)

## Reference Material

For source ordering examples, conflict resolution guidance, error handling procedures, and troubleshooting, load `module-07-reference.md`.

## Success Criteria

- ✅ All sources loaded successfully (or failures documented with resolution plan)
- ✅ Redo queue drained after all sources loaded
- ✅ Dependencies respected (dependent sources loaded after their prerequisites)
- ✅ Cross-source matches identified and reviewed
- ✅ Error rate < 1% per source
- ✅ Loading statistics documented in `docs/loading_strategy.md`
- ✅ Orchestrator program saved in `src/load/orchestrator.[ext]`

## Common Issues

- **Dependency cycles**: Flag to bootcamper, explain that Senzing handles load order gracefully — load the higher-quality source first
- **Resource exhaustion**: Reduce parallelism, check disk space, consider PostgreSQL
- **Slow performance**: Optimize transformations, reduce record count for bootcamp, or use PostgreSQL
- **Missing sources**: Check Module 5 — all sources must be mapped before orchestration
- **Inconsistent mappings**: Different sources map the same real-world field to different Senzing attributes — re-run Module 5 for consistency
