---
inclusion: manual
---

# Module 1 Phase 2: Document and Confirm

Steps 9–16 of Module 1. Continues from Phase 1 (discovery and gap-filling).

9. **Encourage visual explanations**: Ask for diagrams showing data architecture, data flows, or example records. If images contain placeholders like [variable], ask them to specify what each represents.

   **Checkpoint:** Write step 9 to `config/bootcamp_progress.json`.

10. **Identify the scenario**: Categorize as Customer 360, Fraud Detection, Data Migration, Compliance, or Marketing scenario. If they selected a pattern, this is already identified.

    **Checkpoint:** Write step 10 to `config/bootcamp_progress.json`.

11. **Create problem statement document**: Save to `docs/business_problem.md`:

   ```markdown
   # Business Problem Statement

   **Date**: [Current date]
   **Project**: [Project name]
   **Design Pattern**: [Pattern name if selected, or "Custom"]

   ## Problem Description
   [One sentence description]

   ## Use Case Category
   [Customer 360 / Fraud Detection / Data Migration / Compliance / Marketing / Healthcare / Supply Chain / KYC / Insurance / Vendor MDM]

   ## Design Pattern Reference
   [If a pattern was selected, include:]
   - **Pattern**: [Pattern name]
   - **Standard Goal**: [Pattern's typical goal]
   - **Customizations**: [How this differs from the standard pattern]

   ## Data Sources
   1. **[Source name]**
      - Type: [Database/CSV/API/etc.]
      - Records: ~[count]
      - Entity type: [People/Organizations/Both]
      - Update frequency: [Static/Daily/Real-time]
      - Access: [How to access]

   2. **[Source name]**
      - [Same structure]

   ## Entity Types
   [People / Organizations / Both / Other]

   ## Key Matching Criteria
   - **[Attribute 1]** (High priority) - [Why important]
   - **[Attribute 2]** (Medium priority) - [Why important]
   - **[Attribute 3]** (Low priority) - [Why important]

   ## Success Criteria
   - [Measurable outcome 1]
   - [Measurable outcome 2]
   - [Measurable outcome 3]

   ## Desired Output
   **Format**: [Master list / API / Reports / Database export]
   **Use case**: [One-time / Ongoing / Real-time]
   **Integration**: [Standalone / Integrated with [systems]]

   ## Integration Requirements
   **Downstream systems**: [List systems the results need to feed into, or "None — standalone"]
   **Integration method**: [API / Database sync / File export / Message queue / Not applicable]
   **Systems mentioned**: [Specific systems from Step 8, e.g., Elasticsearch, Salesforce, data warehouse]

   ## Timeline
   **Target completion**: [Date]
   **Key milestones**: [List]

   ## Notes
   [Any additional context, constraints, or considerations]
   ```

   **Checkpoint:** Write step 11 to `config/bootcamp_progress.json`.

12. **Update README.md**: Fill in the Overview and Business Problem sections with the information gathered. If a design pattern was selected, mention it in the overview.

    **Checkpoint:** Write step 12 to `config/bootcamp_progress.json`.

13. **Propose solution approach**: Explain how Senzing can solve this and which modules will be most relevant. If they selected a pattern, reference how the bootcamp will implement that pattern.

    **If the user's problem involves search or lookup** (e.g., "find a customer by name", "search across systems"): Load `design-patterns.md` and present the "Where Senzing Fits in Your Architecture" section. Clarify the correct layering: Senzing first for entity resolution, then a search index (Elasticsearch/OpenSearch) for fast retrieval against resolved entities. This prevents a common architectural mistake.

    **If the bootcamper identified integration targets in Step 8**, reference them here and explain how Senzing fits into that architecture. Use `search_docs` to get Senzing's guidance on integrating with the specific systems mentioned.

    **Checkpoint:** Write step 13 to `config/bootcamp_progress.json`.

14. **Get confirmation**: "Does this accurately capture your problem? Does the [pattern name] pattern seem like a good fit, or should we adjust anything?"

    **Checkpoint:** Write step 14 to `config/bootcamp_progress.json`.

15. **Offer stakeholder summary**: Ask: "Would you like me to create a one-page executive summary you can share with your team or manager? It covers the problem, approach, data sources, key findings, next steps, and ROI considerations."

    If yes, read the template: #[[file:senzing-bootcamp/templates/stakeholder_summary.md]] Follow the **MODULE 1** guidance block in the template to fill each placeholder with Module 1 context (problem definition from `docs/business_problem.md`, identified data sources, planned approach, expected outcomes). Save the filled summary to `docs/stakeholder_summary_module1.md`.

    **Checkpoint:** Write step 15 to `config/bootcamp_progress.json`.

16. **Transition to Module 4**: "Module 1 complete. Ready to collect your data sources?"

    **Checkpoint:** Write step 16 to `config/bootcamp_progress.json`.

**Success indicator**: ✅ Clear problem statement + identified data sources + defined success metrics + user confirmation + `docs/business_problem.md` created
