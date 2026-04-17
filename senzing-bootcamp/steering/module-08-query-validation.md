---
inclusion: manual
---

# Module 8: Query and Validate Results

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_8_QUERY_VALIDATION.md`.

**Purpose:** Create query programs and conduct user acceptance testing.

**Before/After**: Your data is loaded and entities are resolved, but you haven't examined the results yet. After this module, you'll have query programs that answer your business questions and validated results you can trust.

**Prerequisites:**

- ✅ Module 7 complete (all sources loaded) OR Module 6 complete (single source)
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

   WAIT for response.

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

   **Do NOT use `exportJSONEntityReport()` or `export_report`** — these do not scale. Use per-entity queries (`get_entity_by_entity_id`, `get_entity_by_record_id`, `search_by_attributes`) or streaming patterns instead.

3. **Run exploratory queries**:

   Execute queries to understand results. Use the appropriate run command for the chosen language.

   **If entity resolution found zero or very few matches:** This is a valid result — don't assume something is broken. Tell the user: "Entity resolution found very few matches. This could mean: (a) your records are genuinely distinct with no duplicates, (b) the matching criteria need adjustment — perhaps key fields weren't mapped or data quality is too low, or (c) you're working with a single source that has no internal duplicates. Let's investigate which one." Check: are name/address/phone fields populated? Were they mapped correctly in Module 5? Is the data quality score from Module 4 above 70%? If the data genuinely has no duplicates, that's a valid finding — document it.

4. **Create UAT test cases**:

   Document in `docs/uat_test_cases.md`:

   ```markdown
   # User Acceptance Test Cases

   ## Test Case 1: Duplicate Detection
   **Scenario:** Find John Smith duplicates
   **Expected:** 3 records resolve to 1 entity
   **Actual:** [To be filled]
   **Status:** [Pass/Fail]

   ## Test Case 2: Cross-Source Matching
   **Scenario:** Customer in CRM and E-commerce
   **Expected:** Records linked to same entity
   **Actual:** [To be filled]
   **Status:** [Pass/Fail]
   ```

5. **Execute UAT with business users**:

   Ask: "Would you like to involve business users in testing?"

   If yes:
   - Share query programs
   - Provide sample queries
   - Collect feedback
   - Document results

6. **Validate results quality**:

   > **Agent instruction:** Use `reporting_guide(topic='evaluation', version='current')` to get
   > the 4-point ER evaluation framework with evidence requirements. Use
   > `reporting_guide(topic='quality', version='current')` for precision/recall metrics,
   > split/merge detection, and review queue strategies. These provide structured evaluation
   > approaches rather than ad-hoc quality checks.

   Check:
   - Match accuracy (are correct records matched?)
   - False positives (are incorrect records matched?)
   - False negatives (are matches missed?)
   - Data completeness (is all data present?)

7. **Document findings**:

   Create `docs/results_validation.md`:

   ```markdown
   # Results Validation

   ## Match Quality
   - True positives: 95%
   - False positives: 2%
   - False negatives: 3%

   ## Business Validation
   - Test cases passed: 45/50
   - Issues identified: 5
   - Resolution plan: [describe]
   ```

   **Offer visualization:** "Would you like me to create a web page showing the query results and validation metrics? It'll have entity tables, match explanations, and UAT results." If yes, generate HTML and save to `docs/results_dashboard.html`.

**Success Criteria:**

- ✅ Query programs created and tested
- ✅ UAT test cases defined
- ✅ Business users validated results
- ✅ Match quality meets requirements (>90% accuracy)
- ✅ Issues documented with resolution plan

## Iterate vs. Proceed Decision Gate

After presenting validation results, guide the decision:

- **UAT pass rate ≥90% and match accuracy ≥90%:** "Results look strong. Ready to proceed to Module 9 (performance) or stop here if you're on Path B/C."
- **UAT pass rate 80-89%:** "Most tests pass but there are some gaps. You can proceed, or review the failures with stakeholders first. Would you like to iterate on the failing cases, or move forward?"
- **UAT pass rate <80%:** "Results need improvement. The failing test cases suggest issues with [mapping quality / data quality / missing data sources]. I'd recommend going back to [Module 5 or 6] to address the root causes. Would you like to investigate, or proceed anyway?"

WAIT for response.

## Stakeholder Summary

After validation is complete, offer: "Would you like me to create a summary of these results to share with your team or stakeholders?"

If yes, create `docs/stakeholder_summary_module8.md`:

```markdown
# Entity Resolution Results — Validation Summary

**Date**: [date] | **Status**: Results validated

## What We Did
Loaded [N] records from [N] data sources into Senzing and ran entity resolution.

## Results
- Records loaded: [N]
- Entities resolved: [N]
- Match rate: [N]%
- UAT pass rate: [N/N] test cases

## Key Findings
- [Finding 1 — e.g., "85% of CRM duplicates were automatically detected"]
- [Finding 2 — e.g., "Cross-source matching linked 340 records across CRM and billing"]
- [Finding 3 — e.g., "5 false positives identified and documented for review"]

## Business Impact
[How this addresses the problem defined in Module 2]

## Next Steps
[Performance testing / Production deployment / Additional data sources]
```
