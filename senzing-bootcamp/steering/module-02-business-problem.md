---
inclusion: manual
---

# Module 2: Discover the Business Problem

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_2_BUSINESS_PROBLEM.md`.

## Workflow: Discover the Business Problem (Module 2)

Use this workflow when starting the bootcamp or when a user wants to explore how Senzing can solve their specific challenge.

**Prerequisites**: None (or Module 1 complete if they did the demo)

**Before/After**: You may have seen the demo, but you don't yet have a defined problem or plan. After this module, you'll have a documented business problem, identified data sources, and clear success criteria — the roadmap for everything that follows.

1. **Initialize version control** (if not already done):

   Check if this is already a git repository:

   ```bash
   # Linux / macOS
   git rev-parse --git-dir 2>/dev/null
   ```

   ```powershell
   # Windows (PowerShell)
   git rev-parse --git-dir 2>$null
   ```

   If not, ask: "Would you like me to initialize a git repository for version control?"

   WAIT for response. If yes, initialize. If no or already a repo, proceed.

2. **Data privacy reminder** (statement, no question — do NOT combine with the next question):

   "Before we proceed, a quick reminder about data privacy. We'll be working with potentially sensitive data. Please ensure you have permission to use this data, and consider anonymizing any PII for testing purposes. We'll set up proper security measures as we go."

3. **Offer design pattern gallery** (separate question — do NOT combine with the privacy reminder):

   "Would you like to see examples of common business problems that entity resolution can solve? I can show you a gallery of entity resolution design patterns with real-world use cases."

   WAIT for response.

4. **If user wants to see patterns**: Present the Entity Resolution Design Pattern Gallery from POWER.md. For each pattern, explain:
   - What problem it solves
   - What the goal is
   - What data sources are typically involved
   - What business value it delivers

   Ask: "Do any of these patterns match your situation? You can use one as a starting point and customize it for your specific needs."

   If they select a pattern, use it as a template for their problem statement:
   - Pre-fill data source types based on the pattern
   - Suggest matching criteria from the pattern
   - Adapt the pattern to their specific context

5. **Set expectations**: "Let's start by understanding your business problem. This will help us tailor the bootcamp to your specific needs. We'll identify your data sources, define success criteria, and create a plan."

6. **Ask guided discovery questions**: Work through these questions systematically, ONE AT A TIME. Wait for the user's response to each question before asking the next one. This prevents overwhelming the user with multiple questions at once.

   **Note**: If user selected a design pattern, use it to guide these questions and pre-fill answers where applicable.

   **Question 1: What problem are you trying to solve?**
   - Ask: "What problem are you trying to solve? For example: deduplication, data matching, identity verification, fraud detection, relationship discovery, or master data management?"
   - If they selected a pattern: "You mentioned [pattern name]. Let's refine that for your specific situation..."
   - WAIT for their response before proceeding to Question 2

   **Question 2: What data sources are involved?**
   - Ask: "What data sources are involved? For each source, I'll need to know: name, type (database/CSV/API/etc.), approximate record count, update frequency, and how to access it."
   - If they selected a pattern: "The [pattern name] pattern typically involves [list sources]. Do you have similar data sources?"
   - WAIT for their response before proceeding to Question 3

   **Question 3: What types of entities?**
   - Ask: "What types of entities are we working with? People, organizations, both, or something else?"
   - If they selected a pattern: "For [pattern name], we typically work with [entity types]. Is that correct for you?"
   - WAIT for their response before proceeding to Question 4

   **Question 4: What matching criteria matter most?**
   - Ask: "What matching criteria matter most for your use case? For example: names, addresses, contact info, identifiers, dates, or other attributes?"
   - If they selected a pattern: "The [pattern name] pattern usually focuses on [matching criteria]. Are these the right attributes for your case?"
   - WAIT for their response before proceeding to Question 5

   **Question 5: What's the desired outcome?**
   - Ask: "What's the desired outcome? What format do you need (master list, API, reports, database export)? Is this one-time or ongoing? Any integration needs?"
   - If they selected a pattern: "The typical goal for [pattern name] is [goal]. What specific outcomes are you looking for?"
   - WAIT for their response before proceeding to step 7

7. **Encourage visual explanations**: Ask for diagrams showing data architecture, data flows, or example records. If images contain placeholders like [variable], ask them to specify what each represents.

8. **Identify the scenario**: Categorize as Customer 360, Fraud Detection, Data Migration, Compliance, or Marketing scenario. If they selected a pattern, this is already identified.

9. **Create problem statement document**: Save to `docs/business_problem.md`:

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

   ## Timeline
   **Target completion**: [Date]
   **Key milestones**: [List]

   ## Notes
   [Any additional context, constraints, or considerations]
   ```

10. **Update README.md**: Fill in the Overview and Business Problem sections with the information gathered. If a design pattern was selected, mention it in the overview.

11. **Propose solution approach**: Explain how Senzing can solve this and which modules will be most relevant. If they selected a pattern, reference how the bootcamp will implement that pattern.

    **If the user's problem involves search or lookup** (e.g., "find a customer by name", "search across systems"): Load `design-patterns.md` and present the "Where Senzing Fits in Your Architecture" section. Clarify the correct layering: Senzing first for entity resolution, then a search index (Elasticsearch/OpenSearch) for fast retrieval against resolved entities. This prevents a common architectural mistake.

12. **Get confirmation**: "Does this accurately capture your problem? Does the [pattern name] pattern seem like a good fit, or should we adjust anything?"

13. **Offer stakeholder summary**: Ask: "Would you like me to create a one-page executive summary you can share with your team or manager? It covers the problem, approach, data sources, key findings, next steps, and ROI considerations."

    If yes, read the template at `senzing-bootcamp/templates/stakeholder_summary.md`. Follow the **MODULE 2** guidance block in the template to fill each placeholder with Module 2 context (problem definition from `docs/business_problem.md`, identified data sources, planned approach, expected outcomes). Save the filled summary to `docs/stakeholder_summary_module2.md`.

14. **Transition to Module 3**: "Module 2 complete. Ready to collect your data sources?"

**Success indicator**: ✅ Clear problem statement + identified data sources + defined success metrics + user confirmation + `docs/business_problem.md` created
