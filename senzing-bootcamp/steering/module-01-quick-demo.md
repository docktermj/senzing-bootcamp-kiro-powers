---
inclusion: manual
---

# Module 1: Quick Demo (Optional)

> **User reference:** `docs/modules/MODULE_1_QUICK_DEMO.md`

**Language:** Use the bootcamper's chosen language for all code generation.

**Before/After:** SDK installed but untested. After: you've seen Senzing match duplicate records across sources — and understand why it's useful.

**IMPORTANT:** Must actually run the Senzing SDK. The goal is an "aha moment," not a description.

## Phase 1: Setup

1. **Create project structure** if needed (load `project-structure.md`). Tell user files go in `src/quickstart_demo/`.

2. **Verify SDK** from Module 0. If not found → direct to Module 0 first.

3. **Choose sample dataset** via `get_sample_data`:
   - Las Vegas, London, Moscow
   - Ask user preference, default to Las Vegas. **Use 50-200 records** (not just 5-10) to produce interesting entity clusters, relationship paths, and meaningful search results. Stay under the 500-record evaluation limit. Download a subset from the full CORD dataset via `get_sample_data`.
   - Present `download_url` for full dataset. Don't dump raw records into chat.

   **MCP fallback:** If `get_sample_data` fails, use the inline 5-record dataset below as a minimal fallback. Tell the user: "I couldn't reach the Senzing sample data server, so I'm using a small built-in dataset. The demo will work but with fewer records — we can try again with more data later." Save to `src/quickstart_demo/sample_data_fallback.jsonl`:

   ```json
   {"DATA_SOURCE":"CRM_SYSTEM","RECORD_ID":"DEMO-001","NAME_FULL":"John Smith","ADDR_FULL":"123 Main St, Las Vegas, NV 89101","PHONE_NUMBER":"555-123-4567","EMAIL_ADDRESS":"john.smith@example.com"}
   {"DATA_SOURCE":"SUPPORT_SYSTEM","RECORD_ID":"DEMO-002","NAME_FULL":"J. Smith","ADDR_FULL":"123 Main Street, Las Vegas, NV 89101","PHONE_NUMBER":"5551234567","EMAIL_ADDRESS":"jsmith@example.com"}
   {"DATA_SOURCE":"SALES_SYSTEM","RECORD_ID":"DEMO-003","NAME_FULL":"John R Smith","ADDR_FULL":"123 Main St Apt 1, Las Vegas, NV 89101","PHONE_NUMBER":"(555) 123-4567","EMAIL_ADDRESS":"john.smith@example.com"}
   {"DATA_SOURCE":"CRM_SYSTEM","RECORD_ID":"DEMO-004","NAME_FULL":"Jane Doe","ADDR_FULL":"456 Oak Ave, Las Vegas, NV 89102","PHONE_NUMBER":"555-987-6543","EMAIL_ADDRESS":"jane.doe@example.com"}
   {"DATA_SOURCE":"SUPPORT_SYSTEM","RECORD_ID":"DEMO-005","NAME_FULL":"Jane M. Doe","ADDR_FULL":"456 Oak Avenue, Las Vegas, NV 89102","PHONE_NUMBER":"5559876543","EMAIL_ADDRESS":"j.doe@example.com"}
   ```

4. **Generate demo script** via `generate_scaffold(workflow='full_pipeline')`. Must include: SDK init with `database/G2C.db` (never `/tmp/`), record loading with progress, entity querying, match explanations (`why_entity`/`how_entity`), before/after comparison. Save to `src/quickstart_demo/demo_[dataset].[ext]`.

5. **Save sample data** to `src/quickstart_demo/sample_data_[dataset].jsonl`.

## Phase 2: Demo

1. **Show records BEFORE resolution:** Display 3-5 records, point out same person appearing with name/address/phone variations.

2. **Run the demo:** Actually execute the script. Show SDK init, loading progress, resolution results, entity count.

3. **Display results:** Summary stats (records loaded, entities created, match rate — use loading counter, NOT `get_stats()`), resolved entities with all matching records, match explanations with confidence scores showing WHY records matched.

4. **Explain results:** Walk through one entity — which features drove the match, what confidence scores mean, how Senzing handled format variations automatically.

   **Offer visualization:** "Would you like me to create a web page showing these results?" If yes, ask: "Would you like any interactive features? For example: (a) 'how' entity explanations, (b) 'why' match analysis, (c) search by attributes, (d) find paths between entities — or just a static summary?" Generate accordingly and save to `src/quickstart_demo/demo_results.html`.

5. **Close Module 1 explicitly.** Before asking any use-case questions, mark the module as done and state its purpose:

   "That's Module 1 complete! The purpose of this demo was to verify that your entire system works end-to-end — SDK, database, data loading, and entity resolution. The sample data and results were just a test, not the real work."

   Follow the `module-completion.md` workflow (journal entry, reflection question, next-step options).

6. **Transition to Module 2.** Only after Module 1 is closed, introduce Module 2 with a clear contrast:

   "Starting with Module 2, we shift to YOUR use case — your data, your problem, your success criteria. This is where the real work begins."

   Then ask the use-case discovery questions one at a time (wait for each response):
   - "What kind of records do you work with — people, organizations, or both?"
   - "How many distinct source systems or feeds will you be ingesting from?"
   - "What does a 'duplicate' look like in your world?"

   Personalize the transition based on their answers. If no specific use case: "The bootcamp works great with sample data too."

## Agent Rules

- MUST run the SDK — not just describe what would happen
- Database path: `database/G2C.db` only. Override any `/tmp/` or `ExampleEnvironment` paths.
- Track record counts during loading — `get_stats()` is per-process stats, not totals
- If the user wants to explore more data after the demo (e.g., load the full CORD dataset), suggest staying under 1,000 records on SQLite: "For the best experience on SQLite, I'd recommend loading up to 1,000 records. Larger datasets work better with PostgreSQL, which we can set up later."
- Data mart distinction: if `reporting_guide` returns `sz_dm_*` tables, flag as separate project requiring additional setup — not built-in SDK
