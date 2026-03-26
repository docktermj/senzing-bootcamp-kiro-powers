# Module 0 Agent Guide: Running the Live Demo

## Quick Reference for Agents

This guide provides step-by-step instructions for agents running Module 0 (Quick Demo) with the new live demonstration feature.

## Critical Requirements

🚨 **MUST DO**: Actually run the Senzing SDK - don't just describe what would happen
🚨 **MUST SHOW**: Match explanations with confidence scores
🚨 **MUST DISPLAY**: Before/after comparison (5 records → X entities)
🚨 **GOAL**: Create the "aha moment" that proves the technology works

## Quick Start Checklist

- [ ] Check if Senzing SDK is available
- [ ] Choose demo type based on availability (live SDK, Docker, or simulation)
- [ ] Show sample records BEFORE resolution
- [ ] Run the appropriate demo script (actually execute it!)
- [ ] Display resolved entities AFTER resolution
- [ ] Show match explanations with confidence scores
- [ ] Highlight key insights
- [ ] Connect results to user's use case

## Demo Type Decision Tree

```text
START: Module 0 Quick Demo
│
├─ Check: Is Senzing SDK installed?
│  ├─ YES → Use demo_quick_start.py (PREFERRED)
│  │        ✓ Real entity resolution
│  │        ✓ Actual SDK execution
│  │        ✓ True confidence scores
│  │
│  └─ NO → Check: Is Docker available?
│     ├─ YES → Offer Docker option
│     │        Ask: "Would you like to use Docker?"
│     │        ├─ YES → Use demo_quick_start.py with Docker
│     │        │        ✓ Real entity resolution
│     │        │        ✓ No installation required
│     │        │
│     │        └─ NO → Use demo_simulation.py (FALLBACK)
│     │                 ✓ No dependencies
│     │                 ✓ Shows concepts
│     │                 ⚠ Simulated results
│     │
│     └─ NO → Use demo_simulation.py (FALLBACK)
│              ✓ No dependencies
│              ✓ Shows concepts
│              ⚠ Simulated results
```

## Fallback Strategy

When SDK and Docker are unavailable:

1. **Acknowledge the limitation**: "I don't see Senzing SDK installed, and Docker isn't available. Let me show you a simulation instead."

2. **Set expectations**: "This simulation will show you how entity resolution works conceptually. For a live demo with real Senzing SDK, we can set that up later."

3. **Run simulation**: Execute `demo_simulation.py`

4. **Explain simulation**: "This was a simulation showing how Senzing would resolve these records. The actual SDK would provide real confidence scores and more detailed match explanations."

5. **Offer next steps**:
   - "Would you like to install Senzing SDK to see the real thing?"
   - "Would you like to continue with Module 1 using your own data?"
   - "Would you like to set up Docker for a live demo?"

## Step-by-Step Workflow

### 1. Check SDK Availability

```bash
# Check if Senzing SDK is installed
python -c "import senzing" 2>/dev/null && echo "SDK found" || echo "SDK not found"
```

**Decision tree**:

1. **If SDK found** → Use `demo_quick_start.py` (preferred path)
2. **If SDK not found** → Check Docker availability:

   ```bash
   docker --version 2>/dev/null && echo "Docker found" || echo "Docker not found"
   ```

   - **If Docker found** → Offer Docker option: "I can run a live demo using Docker (no installation required). Would you like to do that?"
     - If YES → Use `demo_quick_start.py` with Docker
     - If NO → Use `demo_simulation.py` (fallback)
   - **If Docker not found** → Use `demo_simulation.py` (fallback)

**When using simulation fallback**:

- Acknowledge: "I don't see Senzing SDK or Docker available. Let me show you a simulation instead."
- Set expectations: "This simulation demonstrates entity resolution concepts. For a live demo with real Senzing SDK, we can set that up later."
- After simulation: Offer to help install SDK or Docker for a live demo

### 2. Choose Sample Dataset

Ask user which scenario interests them:

- **Las Vegas**: Customer records (retail/hospitality)
- **London**: Person records (identity management)
- **Moscow**: Organization records (B2B)

Default to Las Vegas if user doesn't have a preference.

### 3. Show Sample Records BEFORE Resolution

Display 5 sample records with obvious duplicates:

```text
Here are 5 sample records we'll load into Senzing:

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

Record 4 (CRM_SYSTEM):
  Name:    Jane Doe
  Address: 456 Oak Ave, Las Vegas, NV 89102
  Phone:   (555) 987-6543

Record 5 (SUPPORT_SYSTEM):
  Name:    Jane M. Doe
  Address: 456 Oak Avenue, Las Vegas, NV 89102
  Phone:   555-987-6543

Notice how Records 1, 2, and 3 look like the same person?
And Records 4 and 5 also appear to be the same person?
Let's see if Senzing agrees!
```

### 4. Generate Demo Script

Use MCP server to generate demo script:

```python
# Call generate_scaffold with full_pipeline workflow
generate_scaffold(
    language="python",
    workflow="full_pipeline",
    version="current"
)
```

Save to: `src/quickstart_demo/demo_las_vegas.py`

**IMPORTANT**: Customize the generated script to:

- Use in-memory SQLite database
- Load the 5 sample records
- Query resolved entities
- Display match explanations
- Show before/after comparison

### 5. Save Sample Data

Save sample records to: `src/quickstart_demo/sample_data_las_vegas.jsonl`

Format: One JSON object per line (JSONL)

### 6. Run the Demo

**CRITICAL**: Actually execute the script!

```bash
cd src/quickstart_demo
python demo_las_vegas.py
```

Or with Docker:

```bash
docker run -v $(pwd)/src/quickstart_demo:/data \
  senzing/senzing-tools \
  python /data/demo_las_vegas.py
```

### 7. Display Results

Show the output in this order:

#### a) Summary Statistics

```text
Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Records loaded:              5
Entities created:            3
Duplicates found:            2 (40% match rate)
Average records per entity:  1.67
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### b) Resolved Entities

```text
Entity 1: John Smith
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

#### c) Match Explanations

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

### 8. Explain the Results

Walk through the resolved entity:

"These 3 records all matched because they share:

- The same name (with variations: John Smith, J. Smith, John R Smith)
- The same address (with formatting differences: Main St vs Main Street)
- The same phone number (with formatting differences)

The 98-99% confidence scores mean Senzing is very certain these are the same person."

### 9. Highlight Key Insights

```text
Key Insights:
✓ Senzing automatically recognized duplicates - no manual rules required
✓ Different data formats handled automatically:
    • Phone: (555) 123-4567 ≈ 555-123-4567
    • Address: Main St ≈ Main Street
    • Name: J. Smith ≈ John Smith
✓ Confidence scores show match strength (98-99% = very confident)
✓ This happened in real-time as records were loaded
```

### 10. Connect to User's Use Case

"Now imagine this with your data. Instead of these sample customer records, you'd have [their data sources]. The same process would find duplicates, match records across systems, and give you a unified view. What you just saw is exactly how Senzing will work with your data."

### 11. Transition

Ask what they'd like to do next:

- Start Module 1 with their own data
- Try another sample dataset
- Learn more about entity resolution
- See match explanations in more detail

## Common Issues

### SDK Not Found

**Solution**: Offer Docker option

```bash
docker run -v $(pwd):/data senzing/senzing-tools python /data/demo.py
```

### Demo Script Fails

**Check**:

- Python version (3.8+)
- File paths are correct
- Sample data is in JSONL format

### No Matches Found

**This shouldn't happen** with sample data - the records are designed to match.
If it does happen, check:

- Sample data loaded correctly
- Senzing engine initialized properly
- Records have required fields (DATA_SOURCE, RECORD_ID)

## Agent Behavior Guidelines

### DO

✅ Actually run the Senzing SDK
✅ Show match explanations with confidence scores
✅ Display before/after comparison
✅ Be enthusiastic about the results
✅ Connect demo to user's use case
✅ Create the "aha moment"

### DON'T

❌ Just describe what would happen
❌ Skip the match explanations
❌ Forget the before/after comparison
❌ Be dry or technical
❌ Rush through the results
❌ Miss the opportunity to excite the user

## Success Indicators

✅ Senzing SDK ran successfully
✅ Sample data loaded without errors
✅ Entities resolved correctly
✅ Match explanations displayed with confidence scores
✅ User understands what entity resolution does
✅ User understands WHY records matched
✅ User can see the before/after transformation
✅ User is excited to try with their own data

## Quick Reference: MCP Tools

### Get Sample Data

```python
get_sample_data(dataset="las_vegas")
```

### Generate Demo Script

```python
generate_scaffold(
    language="python",
    workflow="full_pipeline",
    version="current"
)
```

### Validate Output

```python
lint_record(record_json)
```

## Template Location

Pre-built demo template: `senzing-bootcamp/templates/demo_quick_start.py`

This template includes:

- SDK availability check
- In-memory database initialization
- Sample data loading
- Entity resolution
- Match explanation display
- Before/after comparison
- Error handling

## Related Documentation

- Module 0 Documentation: `docs/modules/MODULE_0_QUICK_DEMO.md`
- Steering Workflow: `steering/steering.md` (search for "Module 0")
- Template Documentation: `templates/README.md`
- Improvement Details: `docs/feedback/IMPROVEMENT_MODULE_0_LIVE_DEMO.md`

## Version

- **Current**: v0.26.0 (live demo)
- **Previous**: v0.25.3 (static demo)
- **Release Date**: 2026-03-24

---

**Remember**: The goal is to create an "aha moment" that proves entity resolution works and excites users to continue with their own data. Make it real, make it clear, make it exciting!
