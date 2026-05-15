---
inclusion: manual
---

# Module 1: Discover the Business Problem

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_1_BUSINESS_PROBLEM.md`.

## Workflow: Discover the Business Problem (Module 1)

Use this workflow when starting the bootcamp or when a user wants to explore how Senzing can solve their specific challenge.

**Prerequisites**: None (or Module 3 complete if they did the demo)

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

   **If already a repo:** Skip the question, write the checkpoint, and proceed to Step 2.

   **If not a repo:** Ask the bootcamper:

   👉 "This is optional, but would you like me to initialize a git repository for version control? You can skip this without affecting the bootcamp."

   > **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

   Once the bootcamper responds, act on their answer:
   - If yes, initialize the git repository.
   - If no, skip initialization.

   After the bootcamper responds and you act on the response, write the checkpoint and proceed.

   **Checkpoint:** Write step 1 to `config/bootcamp_progress.json`.

2. **Data privacy reminder** (statement, no question — do NOT combine with the next question):

   "Before we proceed, a quick reminder about data privacy. We'll be working with potentially sensitive data. Please ensure you have permission to use this data, and consider anonymizing any PII for testing purposes. We'll set up proper security measures as we go."

   **Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.

3. **Offer design pattern gallery** (separate question — do NOT combine with the privacy reminder):

   "Would you like to see examples of common business problems that entity resolution can solve? I can show you a gallery of entity resolution design patterns with real-world use cases."

   **Checkpoint:** Write step 3 to `config/bootcamp_progress.json`.

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

   **Checkpoint:** Write step 4 to `config/bootcamp_progress.json`.

5. **Open-ended discovery prompt**:

   Ask a single open-ended question:

   "Tell me about the problem you're trying to solve — what data do you have, where does it come from, and what would success look like?"

   If the user selected a design pattern in Step 4:

   "You picked [pattern name]. Tell me how that applies to your situation — what data do you have, where does it come from, and what would success look like?"

   > **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

   **Checkpoint:** Write step 5 to `config/bootcamp_progress.json`.

6. **Infer details from response**:

   Parse the user's response to extract the following five categories:

   **A. RECORD TYPES** (people / organizations / both)

   Look for signals:
   - People: mentions of customers, patients, employees, members, contacts, individuals, names, SSN, DOB, phone numbers, email addresses
   - Organizations: mentions of companies, vendors, suppliers, businesses, firms, EIN, DUNS, corporate entities
   - Both: mentions of both categories, or phrases like "customers and their employers", "people and the companies they work for"
   - If unclear: default to "not yet determined"

   **B. SOURCE COUNT AND NAMES**

   Look for signals:
   - Explicit mentions: "three systems", "CRM and billing", "we have 5 feeds"
   - Implicit mentions: each named system counts as a source (e.g., "Salesforce, our billing database, and a CSV export" = 3 sources)
   - If only one system mentioned: note it, but don't assume there aren't others
   - If unclear: default to "not yet determined"

   **C. PROBLEM CATEGORY**

   Map to: Customer 360, Fraud Detection, Data Migration, Compliance, Marketing, Healthcare, Supply Chain, KYC, Insurance, Vendor MDM

   Look for signals:
   - "duplicates across systems" → Customer 360
   - "fraud", "suspicious", "identity theft" → Fraud Detection
   - "migrating", "consolidating databases" → Data Migration
   - "compliance", "regulatory", "KYC", "AML" → Compliance / KYC
   - If unclear: default to "not yet categorized"

   **D. MATCHING CRITERIA**

   Look for signals:
   - Attributes mentioned: names, addresses, phone, email, SSN, DOB, etc.
   - Quality concerns: "messy data", "inconsistent formats", "typos"
   - If unclear: will be determined during data mapping (Module 5)

   **E. DESIRED OUTCOME**

   Look for signals:
   - Output format: "master list", "golden record", "API", "report", "export"
   - Frequency: "one-time cleanup", "ongoing", "real-time"
   - Integration: mentions of downstream systems (CRM, search engine, data warehouse, API)
   - If unclear: default to "not yet determined"

   **F. INTEGRATION TARGETS**

   Look for signals:
   - Mentions of specific software: Elasticsearch, Salesforce, Snowflake, Kafka, etc.
   - Phrases like "feed into", "sync with", "push to", "integrate with", "connect to"
   - Architecture mentions: "microservices", "data pipeline", "ETL", "API layer"
   - If unclear: will be asked explicitly in Step 8

   **Checkpoint:** Write step 6 to `config/bootcamp_progress.json`.

7. **Confirm inferred details and fill gaps**:

   Ask about only one undetermined item per turn. After the bootcamper responds, ask about the next undetermined item in a subsequent turn. Do NOT ask about items the user already covered. Queue remaining questions for subsequent turns.

7a. **Present summary and ask for confirmation**:

   Present what was inferred in a concise summary:

   "Based on what you've described, here's what I'm picking up:

   - **Problem:** [inferred category / description]
   - **Record types:** [people / organizations / both / not yet determined]
   - **Data sources:** [count and names, or 'not yet determined']
   - **Key attributes:** [matching criteria mentioned, or 'we'll figure this out during data mapping']
   - **Desired outcome:** [format/frequency, or 'not yet determined']

   Does that summary capture your situation accurately?"

   > **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

   **Checkpoint:** Write step 7a to `config/bootcamp_progress.json`.

7b. **Ask about record types** (if undetermined):

   After confirmation, ask ONLY about items marked "not yet determined".

   If record types unknown: "Are you working with people records, organization records, or both?"

   > **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

   **Checkpoint:** Write step 7b to `config/bootcamp_progress.json`.

7c. **Ask about source count** (if undetermined):

   If source count unknown: "How many distinct data sources or systems will we be working with?"

   > **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

   **Checkpoint:** Write step 7c to `config/bootcamp_progress.json`.

7d. **Ask about desired outcome** (if undetermined):

   If desired outcome unknown: "What does the end result look like for you — a clean master list, an API, reports, or something else?"

   > **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

   **Checkpoint:** Write step 7d to `config/bootcamp_progress.json`.

8. **Ask about software integration** (separate question — do NOT combine with gap-filling):

   "Will the entity resolution results need to interface with other software — for example, a CRM, search engine, data warehouse, API gateway, or downstream application? If so, which systems?"

   Record the answer. If the bootcamper mentions specific systems (e.g., Elasticsearch, Salesforce, a data lake), note them for the problem statement and the solution approach in Step 13. If no integration is needed (standalone use), note that too.

   > **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

   **Checkpoint:** Write step 8 to `config/bootcamp_progress.json`.

9. **Ask about deployment target** (conditional — Advanced Topics track only):

   **Read** `config/bootcamp_preferences.yaml` and check the `track` value.

   **IF `track` is `advanced_topics`:**

   Ask the bootcamper (separate question — do NOT combine with the integration question):

   "Where do you plan to deploy the final entity resolution solution? Here are some common options:

   **Cloud hyperscalers:**
   - AWS
   - Azure
   - GCP

   **Container platforms:**
   - Kubernetes
   - Docker Swarm

   **Local / on-premises:**
   - Current machine
   - Other internal infrastructure

   Or if you're **not sure yet**, that's perfectly fine too."

   > **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

   Reassure the bootcamper: "No matter what you choose, we'll develop everything locally first. Deployment-specific code and configuration will be created later in Module 11 — so there's no pressure to commit right now."

   Once the bootcamper responds, persist their choice to `config/bootcamp_preferences.yaml` as `deployment_target`:

   - **Cloud hyperscaler selected** (AWS, Azure, or GCP): persist `deployment_target` with the value (`aws`, `azure`, or `gcp`). Also persist `cloud_provider` in `config/bootcamp_preferences.yaml` using the same value format as `cloud-provider-setup.md` — `aws` for AWS, `azure` for Azure, `gcp` for GCP.
   - **Container platform selected** (Kubernetes or Docker Swarm): persist `deployment_target` as `kubernetes` or `docker_swarm`.
   - **Local / on-premises selected**: persist `deployment_target` as `local` or `on_premises`.
   - **"Not sure yet" selected**: persist `deployment_target: undecided` in `config/bootcamp_preferences.yaml` and reassure the bootcamper that the choice can be revisited later in Module 11.

   **Checkpoint:** Write step 9 to `config/bootcamp_progress.json` with status "completed".

   **IF `track` is NOT `advanced_topics` (or `track` is not set):**

   Skip this question — deployment is not part of the current track. Do NOT persist any `deployment_target` value to `config/bootcamp_preferences.yaml`.

   **Checkpoint:** Write step 9 to `config/bootcamp_progress.json` with status "skipped_not_applicable" and reason "Track does not include Module 11 (Deployment)".

   Proceed to Phase 2.

**Success indicator:** ✅ Business problem documented in `docs/business_problem.md` + data sources identified + success criteria defined

## Error Handling

When the bootcamper encounters an error during this module:

1. **Check for SENZ error code** — if the error message contains a code matching `SENZ` followed by digits (e.g., `SENZ2027`):
   - Call `explain_error_code(error_code="<code>", version="current")`
   - Present the explanation and recommended fix to the bootcamper
   - If `explain_error_code` returns no result, continue to step 2
2. **Load `common-pitfalls.md`** — navigate to this module's section and present only the matching pitfall and fix
3. **Check cross-module resources** — if no match in the module section, check the Troubleshooting by Symptom table and General Pitfalls section

**Phase 2 (Steps 10–18):** Loaded from `module-01-phase2-document-confirm.md` via the phase system.
