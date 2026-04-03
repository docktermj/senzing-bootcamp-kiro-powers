---
inclusion: manual
---

# Module 8: Query and Validate Results

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_8_QUERY_VALIDATION.md`.

**Purpose**: Create query programs and conduct user acceptance testing.

**Prerequisites**:

- ✅ Module 7 complete (all sources loaded) OR Module 6 complete (single source)
- ✅ No critical loading errors

**Agent Workflow**:

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

   Example queries (file extensions depend on chosen language):
   - `find_duplicates` - Find entities with multiple records
   - `search_entities` - Search by name, email, phone
   - `customer_360` - Get complete customer view
   - `query_results` - Retrieve and format resolved entities

3. **Run exploratory queries**:

   Execute queries to understand results. Use the appropriate run command for the chosen language.

4. **Create UAT test cases**:

   Document in `docs/uat_test_cases.md`:

   ```markdown
   # User Acceptance Test Cases

   ## Test Case 1: Duplicate Detection
   **Scenario**: Find John Smith duplicates
   **Expected**: 3 records resolve to 1 entity
   **Actual**: [To be filled]
   **Status**: [Pass/Fail]

   ## Test Case 2: Cross-Source Matching
   **Scenario**: Customer in CRM and E-commerce
   **Expected**: Records linked to same entity
   **Actual**: [To be filled]
   **Status**: [Pass/Fail]
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

**Success Criteria**:

- ✅ Query programs created and tested
- ✅ UAT test cases defined
- ✅ Business users validated results
- ✅ Match quality meets requirements (>90% accuracy)
- ✅ Issues documented with resolution plan
