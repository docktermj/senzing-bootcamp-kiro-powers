---
inclusion: manual
---

# Module 1 Phase 2: Document and Confirm

Steps 10–18 of Module 1. Continues from Phase 1 (discovery and gap-filling).

10. **Encourage visual explanations**: Ask for diagrams showing data architecture, data flows, or example records. If images contain placeholders like [variable], ask them to specify what each represents.

    **Checkpoint:** Write step 10 to `config/bootcamp_progress.json`.

11. **Identify the scenario**: Categorize as Customer 360, Fraud Detection, Data Migration, Compliance, or Marketing scenario. If they selected a pattern, this is already identified.

    **Checkpoint:** Write step 11 to `config/bootcamp_progress.json`.

12. **Create problem statement document**: Save to `docs/business_problem.md`:

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

   ## Deployment Target

   **Read** `config/bootcamp_preferences.yaml` and check whether `deployment_target` exists.

   **IF `deployment_target` IS present in `config/bootcamp_preferences.yaml`:**

   Use the following template (select the appropriate variant based on the value):

   **Platform**: [Selected deployment target]
   **Category**: [Cloud / Container Platform / Local / Undecided]
   **Note**: Development will proceed locally first; deployment infrastructure will be configured in Module 11.

   If the bootcamper selected "not sure yet" for deployment target, use this instead:

   **Platform**: To be determined
   **Category**: Undecided
   **Note**: Development will proceed locally first; deployment target can be chosen later.

   **IF `deployment_target` is NOT present in `config/bootcamp_preferences.yaml`:**

   Not applicable — current track does not include Module 11 (Deployment).

   ## Timeline
   **Target completion**: [Date]
   **Key milestones**: [List]

   ## Notes
   [Any additional context, constraints, or considerations]
   ```

   **Generated scenario (Business Case Offer accepted in Phase 1)**: When a Generated_Scenario is in effect — the bootcamper accepted the Business_Case_Offer in `module-01-phase1-discovery.md` rather than supplying or selecting a real case — produce the **same** artifacts a real case would (the template above and the `config/data_sources.yaml` registry), with these additions:

   - **Mark the document as generated.** Write the standard `docs/business_problem.md` template above, and immediately below the `# Business Problem Statement` title insert the observable bootcamp-generated marker on its own line, exactly: `> 🤖 Bootcamp-generated business case`. This is the same literal `GENERATED_MARKER` defined in `senzing-bootcamp/scripts/business_case_offer.py`, so the steering and helper agree. The marker identifies the case as bootcamp-generated rather than bootcamper-supplied.
   - **Record every data source.** Record each distinct Scenario_Data source into `config/data_sources.yaml` so the number of recorded entries equals the number of distinct Scenario_Data sources — exactly one registry entry per distinct source. Use the same `config/data_sources.yaml` registry a real case writes (via `scripts/data_sources.py`) so downstream modules read the generated sources through the identical code path.
   - **Keep the document self-contained.** The `docs/business_problem.md` document MUST contain the problem description, the use-case category, the data sources, and the definition of success of the Generated_Scenario, regardless of whether the data sources were recorded in `config/data_sources.yaml`. Do not rely on the registry to carry content the document is responsible for.

   Do not embed any CORD dataset names or record counts from training data — retrieve all CORD facts via the `get_sample_data` and `search_docs` MCP tools at runtime (see Phase 1, Step 5b).

   **If writing an artifact fails**: If writing `docs/business_problem.md` or `config/data_sources.yaml` fails (for example, a permission or I/O error), indicate **which** artifact failed and inform the bootcamper rather than proceeding silently. Do not report Module 1 complete until the bootcamper has been told which write failed.

   **If the artifacts are later missing or unreadable**: If a downstream module (after Module 1 completes) requests `docs/business_problem.md` or `config/data_sources.yaml` and the artifact is missing or unreadable, inform the bootcamper that the Generated_Scenario data is unavailable and allow them to supply real data to proceed. While the Generated_Scenario artifacts are present and readable, the bootcamper can complete every downstream module using only the Scenario_Data, without supplying real data.

   **Checkpoint:** Write step 12 to `config/bootcamp_progress.json`.

13. **Update README.md**: Fill in the Overview and Business Problem sections with the information gathered. If a design pattern was selected, mention it in the overview.

    **Checkpoint:** Write step 13 to `config/bootcamp_progress.json`.

14. **Propose solution approach**: Explain how Senzing can solve this and which modules will be most relevant. If they selected a pattern, reference how the bootcamp will implement that pattern.

    **If the user's problem involves search or lookup** (e.g., "find a customer by name", "search across systems"): Load `design-patterns.md` and present the "Where Senzing Fits in Your Architecture" section. Clarify the correct layering: Senzing first for entity resolution, then a search index (Elasticsearch/OpenSearch) for fast retrieval against resolved entities. This prevents a common architectural mistake.

    **If the bootcamper identified integration targets in Step 8**, reference them here and explain how Senzing fits into that architecture. Use `search_docs` to get Senzing's guidance on integrating with the specific systems mentioned.

    **Checkpoint:** Write step 14 to `config/bootcamp_progress.json`.

15. **Senzing value restatement**: Before confirming the problem statement, reinforce why Senzing entity resolution is valuable for this specific problem.

    Use `search_docs(query='value proposition <use_case_category>', version='current')` from the Senzing MCP server to retrieve current value proposition content relevant to the bootcamper's use case category.

    Tie the value explanation to the bootcamper's specific problem, data sources, and desired outcomes rather than presenting generic marketing content. Explain what entity resolution does — matching, relating, and deduplicating records across sources without manual rules or model training — in terms of the bootcamper's data and goals.

    **If the bootcamper identified integration targets in Step 8**, explain how Senzing fits into their broader architecture alongside those systems, reinforcing that entity resolution is a foundational layer that enhances the value of downstream tools and workflows.

    **Checkpoint:** Write step 15 to `config/bootcamp_progress.json`.

16. **Get confirmation**: "Does this accurately capture your problem and approach?"

    > **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

    **Checkpoint:** Write step 16 to `config/bootcamp_progress.json`.

17. **Offer stakeholder summary**: Ask: "Would you like me to create a one-page executive summary you can share with your team or manager? It covers the problem, approach, data sources, key findings, next steps, and ROI considerations."

    > **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

    If yes, read the template: #[[file:senzing-bootcamp/templates/stakeholder_summary.md]] Follow the **MODULE 1** guidance block in the template to fill each placeholder with Module 1 context (problem definition from `docs/business_problem.md`, identified data sources, planned approach, expected outcomes). Save the filled summary to `docs/stakeholder_summary.md`.

    **Checkpoint:** Write step 17 to `config/bootcamp_progress.json`.

17a. **fpdf2 early hint** (module-completion recap — a natural, non-interrupting point):

    At Module 1 completion, surface the optional-`fpdf2` upgrade hint *early* — with ample time to act before graduation — but **at most once per project**, so it never nags across session resumes or module revisits.

    **Guard first (skip if already shown).** Read `config/bootcamp_preferences.yaml` and check the `fpdf2_hint_shown` flag (e.g., via `preferences_utils.load_preferences`). **If `fpdf2_hint_shown` is already `true`, do nothing** — surface no hint and do not run the preflight — and continue to Step 18.

    Otherwise, run the preflight helper to learn whether installing the optional `fpdf2` dependency will upgrade the final recap PDF:

    ```bash
    python3 senzing-bootcamp/scripts/fpdf2_preflight.py
    ```

    - **If it prints a line** (`fpdf2` is absent): surface it as a single orientation-only line — installing `fpdf2` (`pip install fpdf2`) upgrades the end-of-bootcamp recap PDF to the professionally designed version, and a valid recap PDF is produced either way, so it is an upgrade and never a requirement. **After surfacing the hint**, record that it has been shown by setting `fpdf2_hint_shown: true` in `config/bootcamp_preferences.yaml` via `preferences_utils.write_preference("fpdf2_hint_shown", True)` so it is never repeated in later modules.
    - **If it prints nothing** (`fpdf2` is present): stay silent — surface nothing and write **no** flag (there is nothing to show; if `fpdf2` is later removed, the graduation-time preflight remains the backstop).
    - **If the preflight cannot run** (the script is missing, or running it errors): proceed silently — surface nothing, write **no** flag, and do not block or retry. The hint may surface at the next natural opportunity (the flag stays unset), and the graduation-time preflight (`module-completion-track.md` and graduation Step 0b.0) remains the backstop, so nothing is lost.

    This hint is **non-blocking and orientation-only**: it never adds a 👉 question, never gates progress, requires no action, and **does not auto-install `fpdf2`** — it only informs. `fpdf2` stays an optional, lazily-imported dependency: the preflight helper merely *detects* availability (it does not import `fpdf` at module top level), and the best-effort auto-install remains solely in the graduation-time tiered render path (`generate_recap_pdf.py` and friends), unchanged. It mirrors how `module-completion-track.md` and graduation Step 0b.0 invoke the same helper — the only new things are surfacing it this early and bounding it to once per project via the `fpdf2_hint_shown` flag. Continue to Step 18.

    **Checkpoint:** Write step 17a to `config/bootcamp_progress.json`.

18. **Transition to Module 4**: "Module 1 complete. Ready to collect your data sources?"

    **Checkpoint:** Write step 18 to `config/bootcamp_progress.json`.

**Success indicator**: ✅ Clear problem statement + identified data sources + defined success metrics + user confirmation + `docs/business_problem.md` created
