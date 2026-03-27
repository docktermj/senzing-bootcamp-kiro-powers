---
inclusion: manual
---

# Module 2: Discover the Business Problem

## Workflow: Discover the Business Problem (Module 1)

Use this workflow when starting the boot camp or when a user wants to explore how Senzing can solve their specific challenge.

**Time**: 15-30 minutes

**Prerequisites**: None (or Module 0 complete if they did the demo)

1. **Set up project directory structure**: Follow the directory creation commands from the agent-instructions steering file. After creating the structure, explain the purpose of each folder to the user.

   **Initialize version control**:

   First, check if this is already a git repository:

   ```bash
   git rev-parse --git-dir 2>/dev/null
   ```

   If not a git repository, ask the user if they want to initialize one. If yes:

   ```bash
   git init
   echo "# [Project Name] - Senzing Entity Resolution" > README.md
   ```

   If already a git repository, acknowledge and proceed.

2. **Data privacy reminder**: "Before we proceed, a quick reminder about data privacy. We'll be working with potentially sensitive data. Please ensure you have permission to use this data, and consider anonymizing any PII for testing purposes. We'll set up proper security measures as we go."

3. **Offer design pattern gallery**: "Would you like to see examples of common business problems that entity resolution can solve? I can show you a gallery of entity resolution design patterns with real-world use cases. This might help you articulate your specific problem or give you ideas."

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

5. **Set expectations**: "Let's start by understanding your business problem. This will help us tailor the boot camp to your specific needs. We'll identify your data sources, define success criteria, and create a plan."

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

11. **Propose solution approach**: Explain how Senzing can solve this and which modules will be most relevant. If they selected a pattern, reference how the boot camp will implement that pattern.

12. **Get confirmation**: "Does this accurately capture your problem? Does the [pattern name] pattern seem like a good fit, or should we adjust anything?"

13. **Transition to Module 2**:

    "Great! Module 1 is complete. You now have a clear problem statement and project structure.

    **Module 1 Complete ✅**
    - ✅ Business problem defined
    - ✅ Data sources identified
    - ✅ Success criteria set
    - ✅ Cost estimate created
    - ✅ Project structure ready

    **Common Issues to Watch For**:
    - If data sources are hard to access, document access requirements now
    - If stakeholder approval needed, use cost estimate document
    - If timeline is tight, consider starting with one data source

    Ready to move to Module 2 and collect your data sources?"

**Success indicator**: ✅ Clear problem statement + identified data sources + defined success metrics + user confirmation + `docs/business_problem.md` created
