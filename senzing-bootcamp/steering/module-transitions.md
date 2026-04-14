---
inclusion: auto
---

# Module Transitions

Rules for starting and completing modules. Kiro loads this when module work is happening.

## Journey Map (at module start)

Show the bootcamper a compact journey map with their current position. Use the path from `config/bootcamp_preferences.yaml` to show only modules in their path:

```text
✅ Module 0: Installed the SDK — Senzing is ready to use
✅ Module 1: Ran the demo — saw entity resolution in action
→  Module 2: Define your business problem — so we know what to solve
   Module 3: Collect data — get your data into the project
   Module 5: Map data — translate your fields into Senzing format
```

Mark completed with ✅, current with →, upcoming plain. Include the one-line "why" for each.

## Before/After Framing (at module start)

Each module steering file has a `Before/After` line. Present it to the user so they know what they have now and what they'll have when the module is done.

## Step-Level Progress Communication

**CRITICAL:** Users have reported feeling lost when the agent says "Working..." without context. Every time you perform a step within a module, communicate three things:

### 1. Before starting a step — What and Why

Tell the user what you're about to do and why:

```text
Next up: I'm going to [action]. This is important because [reason / how it connects to the goal].
```

Examples:

- "Next up: I'm going to profile your CSV file to understand its columns, data types, and quality. This tells us what we're working with before we start mapping fields."
- "Next up: I'm going to generate the transformation program. This is the code that will convert your raw data into Senzing's JSON format."
- "Next up: I'm going to run the transformation on a small sample (10 records). This lets us catch any issues before processing the full dataset."

### 2. While working — Status Updates

If a step takes more than a few seconds, provide status updates rather than silence. Instead of just "Working...", say what's happening:

```text
Running the profiler on your data file... analyzing 15 columns across 1,000 rows.
```

```text
Calling the Senzing mapping workflow to determine the right attribute mappings for your name fields...
```

```text
Generating the transformation program in Python — this will read your CSV and output Senzing JSON...
```

### 3. After completing a step — What Changed and Where

After each step, summarize what happened, what was produced, and where to find it:

```text
Done. Here's what changed:
- Discovered 15 columns in your data, 12 of which map to Senzing attributes
- 3 columns (internal_id, created_date, status) don't map to entity features — they'll be skipped
- Data completeness: 94% of rows have names, 87% have addresses, 72% have phone numbers
- Next: We'll plan the entity structure based on what we found
```

```text
Done. Here's what was produced:
- Transformation program: src/transform/transform_customers.py
- It reads from: data/raw/customers.csv
- It writes to: data/transformed/customers.jsonl
- Next: Let's test it on a small sample to make sure it works
```

**File references:** Always mention the specific file paths when files are created or modified. Users need to know where things are.

## Module Completion Summary

When a module is complete, provide a clear completion summary before transitioning:

```text
✅ Module 5 complete!

What we accomplished:
- Created transformation programs for 2 data sources (customers, transactions)
- Mapped 24 source fields to 18 Senzing attributes
- Quality scores: customers 87/100, transactions 79/100

Files produced:
- src/transform/transform_customers.py
- src/transform/transform_transactions.py
- data/transformed/customers.jsonl (1,247 records)
- data/transformed/transactions.jsonl (3,891 records)
- docs/mapping_customers.md
- docs/mapping_transactions.md

Why this matters: Your data is now in Senzing's format and ready to load. Next up is Module 6, where we'll load it into Senzing and see entity resolution run on your actual data.
```

## Bootcamp Journal (at module completion)

After each module completes, append a short entry to `docs/bootcamp_journal.md`:

```markdown
## Module N: [Name] — Completed [date]
**What we did:** [1-2 sentences]
**What was produced:** [files/artifacts created]
**Why it matters:** [how this enables the next step]
**Bootcamper's takeaway:** [user's response to the reflection question]
```

Create the file if it doesn't exist.

### Reflection Question

After writing the journal entry's factual sections, ask the user one reflective question before closing the module:

> "What's your main takeaway from this module — anything that surprised you, or something you want to remember?"

Append their response to the journal entry under "Bootcamper's takeaway." If they decline or say "nothing," write "No additional notes." and move on. Don't push — one question is enough.

This makes the journal a genuine record of the bootcamp experience (not just an agent activity log) and is useful for teams where multiple people review the project later.

## Path Completion Celebration

When the user completes the last module in their chosen path, recognize it with a distinct celebration. This is different from a normal module completion — it's the end of their bootcamp journey on this path.

**Detect path completion:** After each module completion, check `config/bootcamp_preferences.yaml` for the user's path and `config/bootcamp_progress.json` for completed modules. The path endpoints are:

- **Path A:** Complete after Module 1
- **Path B:** Complete after Module 8
- **Path C:** Complete after Module 8
- **Path D:** Complete after Module 12

**When the path is complete, present:**

```text
🎉 You've completed Path [letter] of the Senzing Bootcamp!

Here's what you built:
- [summary of all artifacts — code, data, documentation]
- [total files in src/, data/transformed/, docs/]

Where everything lives:
- Source code: src/
- Transformed data: data/transformed/
- Documentation: docs/
- Configuration: config/
- Database: database/

Your bootcamp journal: docs/bootcamp_journal.md — a complete record of what you did and why.

What's next? You have options:
- [If Path A]: Try Path C to work with your own data, or Path D for the full production journey
- [If Path B]: Add more data sources (Module 7), or harden for production (Modules 9-12)
- [If Path C]: Consider production readiness (Modules 9-12) if you're deploying this
- [If Path D]: You're production-ready! Review docs/operations_guide.md for day-to-day operations

All completed modules carry forward if you switch paths.

Say "bootcamp feedback" to share your experience — it helps improve the bootcamp for future users.
```

**Also:** Load `lessons-learned.md` and offer the retrospective: "Would you like to do a quick retrospective on the bootcamp? It takes 5 minutes and helps capture what worked well and what could be improved."
