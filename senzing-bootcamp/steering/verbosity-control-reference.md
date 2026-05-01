---
inclusion: manual
---

# Verbosity Control — Detailed Reference

This is the detailed reference companion to the core `verbosity-control.md` steering file. It contains the full output category definitions with examples, content rules by level for all five categories, and framing pattern examples at all three levels. The agent loads this file on demand when applying level-specific content rules.

## Output Categories

### explanations

**Definition:** Conceptual "what and why" context around actions and decisions. This covers the reasoning the agent provides before, during, or after performing a substantive action.

**Examples of content in this category:**

- Why we're creating a mapping file
- What entity resolution means in this context
- Why a particular data source needs a specific attribute mapping
- How the current step relates to the overall ER workflow

**Content rules by level:**

- **Level 1 — "What" only:** Provide a single sentence describing the action being taken. Omit the rationale and workflow context entirely.
  > *Example:* "We're creating a mapping file for the customer data source."

- **Level 2 — "What" + "Why":** Provide the action description followed by the purpose or rationale for the action.
  > *Example:* "We're creating a mapping file for the customer data source. This tells Senzing how to interpret each field in your data so it can find matching entities across sources."

- **Level 3 — "What" + "Why" + workflow connection:** Provide the action description, the rationale, and how this step fits into the broader entity resolution pipeline.
  > *Example:* "We're creating a mapping file for the customer data source. This tells Senzing how to interpret each field in your data so it can find matching entities across sources. This mapping step feeds into the loading step in Module 6, where Senzing actually ingests records and begins resolving entities."

### code_walkthroughs

**Definition:** Line-by-line or block-by-block explanations of code. This covers any commentary the agent provides about what code does, how it works, or why specific SDK methods are used.

**Examples of content in this category:**

- Explaining what each section of a loading script does
- SDK method rationale (why `add_record` vs. `add_record_with_info`)
- Walking through a query script's logic
- Describing the structure of generated code

**Content rules by level:**

- **Level 1 — No walkthrough:** Let the code speak for itself. Do not add commentary explaining the code. Code comments within the generated code are still permitted.

- **Level 2 — Block-level summary:** Summarize what each logical section of the code does in one or two sentences per block. Do not explain individual lines.
  > *Example:* "The first section initializes the Senzing engine with your configuration. The second section reads records from the JSONL file and loads them one at a time. The final section prints a summary of how many records were loaded."

- **Level 3 — Detailed block or line-by-line explanation:** Explain each logical block in detail, including why specific SDK methods were chosen and what alternatives exist.
  > *Example:* "Line 12 calls `add_record()` rather than `add_record_with_info()` because at this stage we just need to load the data — we don't need the detailed resolution info that `with_info` returns. That saves processing time during bulk loading. We'll use `with_info` later in Module 7 when we need to inspect how entities resolved."

### step_recaps

**Definition:** Summaries of what a step accomplished and what changed. These appear after a numbered step completes and before the ask-bootcamper hook fires.

**Examples of content in this category:**

- "In this step we created the mapping file and validated it against the schema"
- A list of files created or modified with their paths
- What the bootcamper should understand before moving on

**Content rules by level:**

- **Level 1 — One-line summary + file paths:** Provide a single sentence summarizing what was accomplished, followed by a list of file paths created or modified.
  > *Example:*
  > "Created the data mapping for the customer source."
  > Files: `config/mappings/customers.json`

- **Level 2 — Accomplishment + files + understanding check:** Describe what was accomplished, list files with paths, and state what the bootcamper should understand before proceeding.
  > *Example:*
  > "We created the data mapping for the customer source, defining how each CSV column maps to Senzing entity attributes."
  > Files: `config/mappings/customers.json`
  > "Before moving on, make sure you understand that the mapping file tells Senzing which columns are names, addresses, and identifiers — this directly affects how well entities resolve in the next step."

- **Level 3 — Level 2 + next-step connection:** Include everything from Level 2, plus explain how this step's output connects to the next step and to the module's overall goal.
  > *Example:*
  > "We created the data mapping for the customer source, defining how each CSV column maps to Senzing entity attributes."
  > Files: `config/mappings/customers.json`
  > "Before moving on, make sure you understand that the mapping file tells Senzing which columns are names, addresses, and identifiers — this directly affects how well entities resolve in the next step."
  > "Next, we'll use this mapping to load the customer records into Senzing. This is the core of Module 6 — once the data is loaded, Senzing automatically resolves entities based on the mappings we just defined."

### technical_details

**Definition:** SDK internals, configuration specifics, and performance notes. This covers deeper technical content that goes beyond what the bootcamper needs to complete the step.

**Examples of content in this category:**

- How the Senzing engine processes records internally
- Configuration parameter explanations (e.g., what `SENZING_ENGINE_CONFIGURATION_JSON` contains)
- Performance characteristics (throughput, memory usage)
- Internal data structures or resolution algorithms

**Content rules by level:**

- **Level 1 — Omit:** Do not include SDK internals, configuration specifics, or performance notes. Keep the focus on what the bootcamper needs to do, not how the engine works under the hood.

- **Level 2 — Relevant details when they aid understanding:** Include SDK details and configuration specifics when they help the bootcamper understand why something works the way it does. Omit details that are purely internal.
  > *Example:* "The `SENZING_ENGINE_CONFIGURATION_JSON` environment variable points Senzing to your database and configuration. If you change databases later (e.g., SQLite to PostgreSQL), you'll need to update this value."

- **Level 3 — Full technical depth:** Include SDK internals, configuration deep-dives, and performance characteristics. Explain how the engine processes records, what happens during resolution, and what affects throughput.
  > *Example:* "When `add_record()` is called, Senzing first extracts features (name, address, DOB, etc.) from the record using the mapping you defined. It then compares these features against existing entities using a candidate-selection algorithm that narrows the search space before doing detailed comparison. For a database with 1M entities, this typically processes 1,000–3,000 records per second on a single thread."

### code_execution_framing

**Definition:** Before/during/after framing around code execution runs. This provides structured context so the bootcamper understands the state of the system before code runs and what changed after.

**Examples of content in this category:**

- State before running a load script (e.g., "Database has 0 records")
- What the code does in plain language
- State after execution (e.g., "Database now has 500 records")
- Specific metric changes

**Content rules by level:**

- **Level 1 — "What this code does" + one-line result:** Before execution, provide a plain-language summary of what the code does. After execution, provide a one-line result.
  > *Before:* "This script loads customer records from the JSONL file into Senzing."
  > *After:* "Result: 500 records loaded successfully."

- **Level 2 — "Before" + "What this code does" + "After":** Before execution, describe the current state of relevant files, databases, or configurations. Summarize what the code does. After execution, describe what changed.
  > *Before:* "The Senzing database currently has no records loaded. The customer JSONL file contains 500 records."
  > *What this code does:* "This script reads each record from the JSONL file and loads it into Senzing using the mapping we defined."
  > *After:* "The Senzing database now contains 500 customer records. Senzing has automatically resolved entities based on matching names and addresses."

- **Level 3 — Level 2 + specific metric values:** Include everything from Level 2, plus specific before/after values for key metrics or state.
  > *Before:* "Records in database: 0. Entity count: 0. Source file: `data/customers.jsonl` (500 records, 12 fields per record)."
  > *What this code does:* "This script reads each record from the JSONL file and loads it into Senzing using the mapping we defined."
  > *After:* "Records in database: 0 → 500. Entity count: 0 → 423. Load time: 12.3 seconds (40.6 records/sec). New file created: `logs/load_customers.log` (500 lines)."

## Framing Patterns

These patterns show how the agent structures output for the three main framing types. Apply the pattern matching the bootcamper's current level for each category.

### "What and Why" Framing (explanations category)

**Level 1 — What only:**
> We're adding the customer data source to the Senzing configuration.

**Level 2 — What + Why:**
> We're adding the customer data source to the Senzing configuration. This registers the source so Senzing knows where records come from when it resolves entities across multiple datasets.

**Level 3 — What + Why + Workflow connection:**
> We're adding the customer data source to the Senzing configuration. This registers the source so Senzing knows where records come from when it resolves entities across multiple datasets. Once registered, we'll use this data source name in the mapping file (Module 5) and the loading script (Module 6) — it's the thread that connects your raw data to resolved entities.

### Code Execution Framing (code_execution_framing category)

**Level 1 — Summary + Result:**
> **What this code does:** Loads 500 customer records from the JSONL file into Senzing.
>
> **Result:** 500 records loaded successfully.

**Level 2 — Before + What + After:**
> **Before:** The Senzing database has no records loaded. The file `data/customers.jsonl` contains 500 records.
>
> **What this code does:** Reads each record from the JSONL file and loads it into Senzing using the customer mapping.
>
> **After:** 500 customer records are now in the Senzing database. Senzing has automatically resolved entities based on matching names and addresses.

**Level 3 — Before + What + After + Metrics:**
> **Before:** Records in database: 0. Entity count: 0. Source file: `data/customers.jsonl` (500 records, 12 fields per record).
>
> **What this code does:** Reads each record from the JSONL file and loads it into Senzing using the customer mapping.
>
> **After:** Records in database: 0 → 500. Entity count: 0 → 423. Load time: 12.3s (40.6 records/sec). New file: `logs/load_customers.log`.

### Step Recap Framing (step_recaps category)

**Level 1 — One-line + files:**
> Created the customer data mapping.
> Files: `config/mappings/customers.json`

**Level 2 — Accomplishment + files + understanding:**
> We created the data mapping for the customer source, defining how each CSV column maps to Senzing entity attributes.
> Files: `config/mappings/customers.json`
> Before moving on, make sure you understand that the mapping file tells Senzing which columns are names, addresses, and identifiers.

**Level 3 — Level 2 + next-step connection:**
> We created the data mapping for the customer source, defining how each CSV column maps to Senzing entity attributes.
> Files: `config/mappings/customers.json`
> Before moving on, make sure you understand that the mapping file tells Senzing which columns are names, addresses, and identifiers.
> Next, we'll use this mapping to load the customer records into Senzing. This is the core of Module 6 — once the data is loaded, Senzing automatically resolves entities.
