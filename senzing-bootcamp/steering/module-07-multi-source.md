---
inclusion: manual
---

# Module 7: Multi-Source Orchestration

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_7_MULTI_SOURCE_ORCHESTRATION.md`.

**Purpose**: Coordinate loading of multiple data sources with dependencies and optimization.

**Prerequisites**:

- ✅ Module 6 complete (first source loaded successfully)
- ✅ Multiple data sources to orchestrate
- ✅ Loading statistics reviewed for first source

**Agent Workflow**:

> **Agent instruction:** Before starting multi-source orchestration, check for anti-patterns:
> `search_docs(query="multi-source loading orchestration", category="anti_patterns", version="current")`.
> Key pitfalls include threading issues, redo processing, and load order dependencies.

1. **Analyze data sources and dependencies**:

   Ask: "Do any of your data sources depend on others being loaded first?"

   WAIT for response.

   Common dependency patterns:
   - Parent-child relationships (load parents first)
   - Reference data (load lookups first)
   - Temporal ordering (load historical first)

2. **Determine loading strategy**:

   Ask: "Would you like to load sources sequentially or in parallel?"

   Options:
   - **Sequential**: One at a time, safer, easier to debug
   - **Parallel**: Multiple at once, faster, requires more resources
   - **Hybrid**: Some parallel, some sequential based on dependencies

   WAIT for response.

3. **Create orchestration plan**:

   Document in `docs/loading_strategy.md`:

   ```markdown
   # Loading Strategy

   ## Load Order
   1. Reference data (COUNTRIES, STATES)
   2. Core entities (CUSTOMERS, PRODUCTS)
   3. Transactions (ORDERS, SUPPORT_TICKETS)

   ## Parallel Groups
   - Group 1: CUSTOMERS, PRODUCTS (no dependencies)
   - Group 2: ORDERS, SUPPORT_TICKETS (depend on Group 1)

   ## Resource Allocation
   - Max parallel loaders: 4
   - Memory per loader: 2GB
   - Expected duration: 2-3 hours
   ```

4. **Create orchestrator program**:

   Use `generate_scaffold` with `workflow='add_records'` and the bootcamper's chosen language for loading patterns.
   Use `find_examples(query="queue loading", language="<chosen_language>")` or `find_examples(query="multi-source")` for real-world orchestration patterns from GitHub repos.

   **CRITICAL**: If the generated scaffold uses `/tmp/`, `ExampleEnvironment`, or any path outside the working directory, override the database path to `database/G2C.db` and ensure all output files use project-relative paths. No files may be placed outside the working directory.

   Save to `src/load/orchestrator.[ext]` (using the appropriate file extension for the chosen language).

   Key features:
   - Dependency management
   - Parallel execution (language-appropriate concurrency: threads, async, etc.)
   - Progress tracking across sources
   - Error handling and recovery
   - Statistics aggregation

5. **Test orchestration with samples**:

   Before running on full data, run the orchestrator with a small test limit. Use the appropriate run command for the chosen language.

6. **Run full orchestration**:

   Run the orchestrator program using the appropriate command for the chosen language.

   Monitor:
   - Progress for each source
   - Overall completion percentage
   - Error rates
   - Resource utilization

7. **Validate results**:

   After loading:
   - Check record counts for each source
   - Verify cross-source matches
   - Review error logs
   - Confirm no data loss

   > **Agent instruction:** Use `reporting_guide(topic='graph', version='current')` to get
   > network graph export patterns for visualizing cross-source entity relationships.
   > This helps users see how entities connect across their data sources.

**Error Recovery**:

> **Agent instruction:** When a source fails during orchestration, use
> `explain_error_code(error_code="<code>", version="current")` to diagnose the error
> before deciding whether to continue with remaining sources. Document the error and
> resolution in `docs/loading_strategy.md`.

**Success Criteria**:

- ✅ All sources loaded successfully
- ✅ Dependencies respected
- ✅ Cross-source matches identified
- ✅ Error rate < 1%
- ✅ Loading statistics documented

**Common Issues**:

- Dependency cycles: Redesign load order
- Resource exhaustion: Reduce parallelism
- Slow performance: Optimize transformations or use PostgreSQL
