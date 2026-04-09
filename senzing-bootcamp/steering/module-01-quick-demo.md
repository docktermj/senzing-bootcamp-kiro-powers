---
inclusion: manual
---

# Module 1: Quick Demo (Optional)

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_1_QUICK_DEMO.md`.

## Workflow: Quick Demo (Module 1 - Optional)

Use this workflow when a user wants to see entity resolution in action before working with their own data. This is perfect for first-time users who want to understand what Senzing does.

**IMPORTANT:** This module must actually run the Senzing SDK to demonstrate real entity resolution, not just describe it. The goal is to create an "aha moment" where users see the technology working.

**Language:** Use the bootcamper's chosen programming language from the language selection step. All code generation, scaffold calls, and examples in this module must use that language.

**IMPORTANT:** Before starting Module 1, ensure the project directory structure exists. If the user is starting with Module 1 (before Module 2), create the full project structure first.

1. **Create project structure (if needed):** Follow the directory creation commands from the agent-instructions steering file. If the structure doesn't exist, create it before proceeding. After creation, tell the user: "I've created the project directory structure for you. All demo files will be saved in `src/quickstart_demo/`."

2. **Explain the demo:** "Let's run a demo using sample data so you can see entity resolution in action. We'll run the Senzing SDK to load duplicate records and watch them automatically resolve into unique entities."

3. **Verify Senzing SDK is available:** The SDK should already be installed from Module 0. Verify using a language-appropriate check (see Module 0 Step 1 for examples).

   **If SDK found** → Proceed with the live demo.

   **If SDK not found** → Direct user to complete Module 0 (SDK Setup) first. Do not proceed without the SDK.

4. **Choose sample dataset:** Call `get_sample_data` to retrieve one of the CORD datasets:
   - **Las Vegas:** Customer records with duplicates (good for retail/hospitality use cases)
   - **London:** Person records with variations (good for identity management)
   - **Moscow:** Organization records (good for B2B use cases)

   Ask the user which scenario interests them most, or default to Las Vegas.

   **IMPORTANT:** Present the `download_url` from the `get_sample_data` response to the user so they can download the full JSONL dataset if they want to explore further. Do not dump raw records into the conversation — the inline records are a small preview only.

   **IMPORTANT:** Use a small sample (5-10 records) for the quick demo to ensure fast execution and clear results. The goal is to show the concept, not process large volumes.

   **Fallback if `get_sample_data` fails:** If the MCP server is unreachable or `get_sample_data` returns an error, use this minimal inline dataset so the demo can still proceed:

   ```json
   {"DATA_SOURCE": "CRM_SYSTEM", "RECORD_ID": "DEMO-001", "NAME_FULL": "John Smith", "ADDR_FULL": "123 Main St, Las Vegas, NV 89101", "PHONE_NUMBER": "555-123-4567", "EMAIL_ADDRESS": "john.smith@example.com"}
   {"DATA_SOURCE": "SUPPORT_SYSTEM", "RECORD_ID": "DEMO-002", "NAME_FULL": "J. Smith", "ADDR_FULL": "123 Main Street, Las Vegas, NV 89101", "PHONE_NUMBER": "5551234567", "EMAIL_ADDRESS": "jsmith@example.com"}
   {"DATA_SOURCE": "SALES_SYSTEM", "RECORD_ID": "DEMO-003", "NAME_FULL": "John R Smith", "ADDR_FULL": "123 Main St Apt 1, Las Vegas, NV 89101", "PHONE_NUMBER": "(555) 123-4567", "EMAIL_ADDRESS": "john.smith@example.com"}
   {"DATA_SOURCE": "CRM_SYSTEM", "RECORD_ID": "DEMO-004", "NAME_FULL": "Jane Doe", "ADDR_FULL": "456 Oak Ave, Las Vegas, NV 89102", "PHONE_NUMBER": "555-987-6543", "EMAIL_ADDRESS": "jane.doe@example.com"}
   {"DATA_SOURCE": "SUPPORT_SYSTEM", "RECORD_ID": "DEMO-005", "NAME_FULL": "Jane M. Doe", "ADDR_FULL": "456 Oak Avenue, Las Vegas, NV 89102", "PHONE_NUMBER": "5559876543", "EMAIL_ADDRESS": "j.doe@example.com"}
   ```

   Save this to `src/quickstart_demo/sample_data_fallback.jsonl` and use it for the demo. Tell the user: "I couldn't reach the Senzing sample data server, so I'm using a small built-in dataset. The demo will work the same way."

5. **Show sample records BEFORE resolution:** Display 3-5 sample records from the dataset. Point out:
   - How the same person/organization appears multiple times
   - Variations in names, addresses, phone numbers
   - Different data quality levels
   - How a human would recognize these as duplicates

   Example:

   ```text
   Here are 5 sample records we'll load into Senzing:

   Record 1 (CRM_SYSTEM):
     Name: John Smith
     Address: 123 Main St, Las Vegas, NV 89101
     Phone: (555) 123-4567

   Record 2 (SUPPORT_SYSTEM):
     Name: J. Smith
     Address: 123 Main Street, Las Vegas, NV 89101
     Phone: 555-123-4567

   Record 3 (SALES_SYSTEM):
     Name: John R Smith
     Address: 123 Main St Apt 1, Las Vegas, NV 89101
     Phone: (555) 123-4567

   Record 4 (CRM_SYSTEM):
     Name: Jane Doe
     Address: 456 Oak Ave, Las Vegas, NV 89102
     Phone: (555) 987-6543

   Record 5 (SUPPORT_SYSTEM):
     Name: Jane M. Doe
     Address: 456 Oak Avenue, Las Vegas, NV 89102
     Phone: 555-987-6543

   Notice how Records 1, 2, and 3 look like the same person?
   And Records 4 and 5 also appear to be the same person?
   Let's see if Senzing agrees!
   ```

6. **Generate demo script:** Call `generate_scaffold` with workflow `full_pipeline` and the bootcamper's chosen language to create a complete demo script that:
   - Initializes Senzing with a project-local SQLite database at `database/G2C.db` (never `/tmp/` or in-memory — see `docs/policies/FILE_STORAGE_POLICY.md`)
   - Creates the `database/` directory if it doesn't exist (using the language-appropriate directory creation method)
   - Loads the sample records (with progress indicator)
   - Queries the resolved entities
   - Shows match explanations using `why_entity_by_entity_id` or `how_entity_by_entity_id`
   - Displays before/after comparison

   **Save the generated script to:** `src/quickstart_demo/demo_[dataset_name].[ext]` where `[ext]` is the appropriate file extension for the chosen language (`.py`, `.java`, `.cs`, `.rs`, `.ts`).

   Example: `src/quickstart_demo/demo_las_vegas.py` (Python), `demo_las_vegas.java` (Java), etc.

   **CRITICAL:** The script must include:
   - SDK initialization code using `database/G2C.db` as the database path (never `/tmp/` or in-memory)
   - Record loading with error handling
   - Entity querying to show resolved results
   - Match explanation retrieval (why/how records matched)
   - Clear output formatting showing before/after

7. **Save sample data:** Save the sample data retrieved from `get_sample_data` to:
   - `src/quickstart_demo/sample_data_[dataset_name].jsonl`

   Example: `src/quickstart_demo/sample_data_las_vegas.jsonl`

8. **Run the demo:** Execute the script and show:
   - SDK initialization confirmation
   - Records being loaded (with progress)
   - Entity resolution happening
   - How many entities were created from the records
   - Example of resolved entities showing all matching records

   **CRITICAL:** Actually execute the script - don't just show what it would do! Use the appropriate run command for the chosen language.

9. **Display results with match explanations:** After the demo runs, show:

   a) **Summary statistics** (use the count tracked during loading, NOT `get_stats()`):

   ```text
   Results:
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Records loaded:              5
   Entities created:            3
   Duplicates found:            2 (40% match rate)
   Average records per entity:  1.67
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

   b) **Resolved entities** (show at least one complete entity):

   ```text
   Entity ID: 1
   Records matched: 3

   Record 1 (CRM_SYSTEM):
     Name:    John Smith
     Address: 123 Main St, Las Vegas, NV 89101
     Phone:   (555) 123-4567

   Record 2 (SUPPORT_SYSTEM):
     Name:    J. Smith
     Address: 123 Main Street, Las Vegas, NV 89101
     Phone:   555-123-4567

   Record 3 (SALES_SYSTEM):
     Name:    John R Smith
     Address: 123 Main St Apt 1, Las Vegas, NV 89101
     Phone:   (555) 123-4567
   ```

   c) **Match explanations** (WHY records matched):

   ```text
   Match Explanation:
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Why these records matched:

   Record 1 ↔ Record 2:
     ✓ Name similarity:    92% (John Smith ≈ J. Smith)
     ✓ Address match:      100% (same address, different format)
     ✓ Phone match:        100% (same number, different format)
     ✓ Overall confidence: 98% - STRONG MATCH

   Record 1 ↔ Record 3:
     ✓ Name similarity:    95% (John Smith ≈ John R Smith)
     ✓ Address match:      95% (123 Main St ≈ 123 Main St Apt 1)
     ✓ Phone match:        100%
     ✓ Overall confidence: 99% - STRONG MATCH
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

10. **Explain the results:** Walk through one resolved entity:
    - "These 3 records all matched because they share the same name (with variations), address (with formatting differences), and phone number."
    - Show the features that drove the match (name, address, phone)
    - Explain confidence scores: "98% confidence means Senzing is very certain these are the same person"
    - Show how Senzing combined the information: "Notice how Senzing recognized '123 Main St' and '123 Main Street' as the same address"

11. **Highlight key insights:**
    - "Senzing automatically recognized these as the same person - no manual rules required"
    - "Different data formats were handled automatically (phone number formatting, street abbreviations)"
    - "Confidence scores show match strength, helping you trust the results"
    - "This happened in real-time as records were loaded"

12. **Connect to their use case:** "Now imagine this with your data. Instead of [sample data], you'd have [their data sources]. The same process would find duplicates, match records across systems, and give you a unified view. What you just saw is exactly how Senzing will work with your data."

13. **Transition:** Ask if they want to:
    - Start Module 2 with their own data
    - Try another sample dataset
    - Learn more about how entity resolution works
    - See the match explanations in more detail

**Success indicator:** ✅ Senzing SDK ran successfully + Sample data loaded + Entities resolved + Match explanations displayed + User understands what entity resolution does + User is excited to try with their own data

**Agent behavior:**

- MUST actually run Senzing SDK - not just describe what would happen
- MUST use `database/G2C.db` for the SQLite database path — never `/tmp/`, never in-memory. If `generate_scaffold` or `ExampleEnvironment` defaults to `/tmp/`, override the database path to `database/G2C.db`. Create the `database/` directory first using the language-appropriate method, or `mkdir -p database` on Linux/macOS, or `New-Item -ItemType Directory -Force -Path database` on PowerShell.
- Show real match explanations with confidence scores
- Display clear before/after comparison
- Make the "aha moment" obvious
- Be enthusiastic about the results
- Connect demo results to user's use case
