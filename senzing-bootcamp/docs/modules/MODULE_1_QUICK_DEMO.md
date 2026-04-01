# Module 1: Quick Demo (Optional)

## Overview

Module 1 provides a demonstration of Senzing entity resolution using sample data. This optional module is perfect for first-time users who want to see entity resolution in action before working with their own data.

This module offers multiple demo options to ensure everyone can see entity resolution working, regardless of their environment.

**Time**: 10-15 minutes

**Output**: Working demo showing entity resolution results

## Prerequisites

- ✅ Module 0 complete (Senzing SDK installed)
- ✅ Python 3.10+ with senzing package

## Learning Objectives

By the end of this module, you will:

- See Senzing entity resolution working in real-time
- Watch duplicate records automatically match and merge
- Understand WHY records matched (match explanations)
- Observe the before/after transformation (5 records → X entities)
- Connect the demo to your own use case

## What You'll Do

1. Choose a sample dataset (Las Vegas, London, or Moscow)
2. Review sample records showing duplicates
3. Verify Senzing SDK is available (installed in Module 0)

4. Initialize an in-memory SQLite database
5. Load sample records into Senzing
6. Query the resolved entities
7. See match explanations showing WHY records matched
8. Compare before/after (5 records → X entities)

## Sample Datasets

### Las Vegas Dataset

- **Type:** Customer records
- **Records**: ~1,000
- **Use case**: Retail/hospitality customer deduplication
- **Duplicates**: Same customers with variations in names, addresses, phones

### London Dataset

- **Type:** Person records
- **Records**: ~1,000
- **Use case**: Identity management
- **Duplicates**: Same people with name variations and different contact info

### Moscow Dataset

- **Type:** Organization records
- **Records**: ~1,000
- **Use case**: B2B vendor/supplier matching
- **Duplicates**: Same companies with different names and addresses

## Demo Script Structure

The generated demo script will:

1. **Verify Senzing SDK** - Confirms SDK is installed from Module 0 (SDK Setup)
2. **Initialize Senzing** with in-memory SQLite database
3. **Load sample records** from the chosen dataset (with progress bar)
4. **Query resolved entities** to show which records matched
5. **Display match explanations** showing WHY records matched (name similarity, address match, etc.)
6. **Show statistics** (records loaded, entities created, match rate)
7. **Display example entities** with all matching records side-by-side
8. **Provide before/after comparison** (e.g., "5 records → 3 entities")

## Example Output

```text
Checking Senzing SDK installation...
✓ Senzing SDK found (version 3.8.0)

Initializing Senzing engine with in-memory database...
✓ Engine initialized

Loading sample records...
[====================] 100% (5/5 records loaded)

Resolving entities...
✓ Entity resolution complete

Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Records loaded:              5
Entities created:            3
Duplicates found:            2 (40% match rate)
Average records per entity:  1.67
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Example Resolved Entity:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Entity ID: 1
Records matched: 3

Record 1 (CRM_SYSTEM):
  Name:    John Smith
  Address: 123 Main St, Las Vegas, NV 89101
  Phone:   (555) 123-4567
  Email:   john.smith@email.com

Record 2 (SUPPORT_SYSTEM):
  Name:    J. Smith
  Address: 123 Main Street, Las Vegas, NV 89101
  Phone:   555-123-4567
  Email:   jsmith@email.com

Record 3 (SALES_SYSTEM):
  Name:    John R Smith
  Address: 123 Main St Apt 1, Las Vegas, NV 89101
  Phone:   (555) 123-4567
  Email:   john.smith@email.com

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
  ✓ Email match:        100%
  ✓ Overall confidence: 99% - STRONG MATCH

Record 2 ↔ Record 3:
  ✓ Name similarity:    90% (J. Smith ≈ John R Smith)
  ✓ Address match:      95%
  ✓ Phone match:        100%
  ✓ Overall confidence: 96% - STRONG MATCH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Key Insights:
• Senzing automatically recognized these as the same person
• No manual rules were required
• Different data formats were handled automatically
• Confidence scores show match strength
```

## Key Concepts Demonstrated

### Entity Resolution

- Multiple records about the same real-world entity are identified and linked
- No manual rules required - Senzing learns from the data
- Confidence scores show match strength

### Feature Extraction

- Names, addresses, phones are parsed into features
- Features are standardized (e.g., "St" → "Street")
- Features are scored and compared

### Entity-Centric Learning

- As more records are added, resolution improves
- The engine learns patterns from your data
- No training data required

### Understanding `get_stats()` vs. Record Counts

A common pitfall: `sz_engine.get_stats()` tracks per-process workload statistics for the current engine session, not the total records in the repository. It resets after each call and may return `-1` for fields like `loadedRecords` if stats haven't accumulated. To get accurate record counts, track them during loading (e.g., increment a counter per successful `add_record` call) rather than relying on `get_stats()`. The correct use of `get_stats()` is for monitoring ongoing operations, covered in Module 9 (Performance Testing).

## File Locations

All Module 1 demo code is saved in `src/quickstart_demo/`:

```text
src/quickstart_demo/
├── demo_las_vegas.py          # Demo script for Las Vegas dataset
├── demo_london.py              # Demo script for London dataset
├── demo_moscow.py              # Demo script for Moscow dataset
├── sample_data_las_vegas.jsonl # Sample data
├── sample_data_london.jsonl    # Sample data
└── sample_data_moscow.jsonl    # Sample data
```

## Running the Demo

The demo runs automatically when you start Module 1 (Quick Demo). The agent will:

1. Verify Senzing SDK is installed (from Module 0 SDK Setup)
2. Generate and run the demo script
3. Display results in real-time

### Manual Execution

If you want to run the demo again later:

```bash
cd src/quickstart_demo
python demo_las_vegas.py
```

## What to Look For

### Good Matches

- Same person/organization with minor variations
- Different data quality levels matched correctly
- Nicknames and abbreviations handled properly

### Interesting Cases

- Records that almost match but don't (different people with similar names)
- Records that match despite significant differences (poor data quality)
- Multiple records from same source matched together

### Statistics

- Match rate: What percentage of records are duplicates?
- Entity distribution: How many records per entity on average?
- Data quality: How consistent is the data?

## Connecting to Your Use Case

After the demo, consider:

- How does this compare to your data?
- What matching criteria matter most for you?
- What data quality issues might you have?
- How many duplicates do you expect?

## Next Steps

After completing the demo:

- **Ready to start?** → Proceed to Module 2 (Business Problem)
- **Want to try another dataset?** → Run another demo
- **Have questions?** → Ask about specific entity resolution concepts

## Common Questions

**Q: Do I need to install Senzing to run the demo?**
A: Yes. Complete Module 0 (SDK Setup) first.

**Q: Does this actually run Senzing?**
A: Yes. This runs the real Senzing SDK with actual entity resolution.

**Q: Can I use my own data for the demo?**
A: The demo uses sample data to ensure a quick, successful experience. You'll work with your data starting in Module 3.

**Q: How accurate is entity resolution?**
A: Accuracy depends on data quality. Typical match rates: 90-99% precision, 85-95% recall. The demo shows real match confidence scores.

**Q: Can I skip this module?**
A: Yes, it's optional. Skip to Module 2 if you're ready to start with your data. But we recommend the demo - it only takes 10 minutes and shows the value immediately.

## Troubleshooting Module 1

### Issue: SDK Not Found

**Symptoms**:

- "ModuleNotFoundError: No module named 'senzing'"
- SDK check returns "SDK not found"

**Solutions**:

1. **Complete Module 0 first** (SDK Setup)
   - Module 0 installs the SDK natively
   - Return to Module 1 after installation

2. **Check Python environment**

   ```bash
   pip list | grep senzing
   python3 -c "import senzing; print(senzing.__version__)"
   ```

---

### Issue: Database Initialization Failed

**Symptoms**:

- Error: "unable to open database file"
- Error: "SzDatabaseError - SENZ1001"

**Solutions**:

1. **Check database directory exists**

   ```bash
   mkdir -p database
   ```

2. **Check file permissions**

   ```bash
   ls -la database/
   ```

---

### Issue: Demo Runs But No Matches Found

**This shouldn't happen** with sample data - the records are designed to match.

**If it does happen**:

1. **Check sample data loaded correctly**
   - Verify 5 records were loaded
   - Check for error messages during loading

2. **Verify Senzing engine initialized**
   - Look for "Engine initialized" message
   - Check for initialization errors

3. **Contact support** - This indicates a bug
   - Share error messages with agent
   - Provide full output log
   - This is unexpected behavior

---

### Issue: Module 1 Taking Longer Than Expected

**Expected time**: 10-15 minutes

**If taking longer**:

1. **Check what's taking time**
   - Database initialization? (Should be <1 minute)
   - Demo execution? (Should be <2 minutes)

2. **Continue anyway**
   - First-time setup is one-time cost
   - Subsequent runs will be faster

---

### Issue: Permission Denied Errors

**Symptoms**:

- "Permission denied" when creating files
- "Cannot write to directory"

**Causes**:

- Insufficient permissions in project directory
- Running in protected directory

**Solutions**:

1. **Check project directory permissions**

   ```bash
   ls -la
   ```

2. **Move to user directory**

   ```bash
   # Create project in home directory
   cd ~
   mkdir my-senzing-project
   cd my-senzing-project
   ```

3. **Fix permissions** (if needed)

   ```bash
   chmod 755 .
   ```

---

### Getting Help

**If none of these solutions work**:

1. **Share error messages with agent**
   - Copy full error output
   - Describe what you tried
   - Agent can provide specific guidance

2. **Skip to Module 2**
   - Continue learning with your business problem
   - Return to Module 0 and 1 later when setup is resolved

3. **Contact Senzing support**
   - Provide error details
   - Share environment info (OS, Python version)
   - Include steps to reproduce

---

### Pre-Flight Check

**Before starting Module 1, verify your environment**:

Run the pre-flight check script:

```bash
./scripts/preflight_check.sh
```

This will check:

- ✓ Senzing SDK installation
- ✓ Disk space
- ✓ Network connectivity
- ✓ Python installation

And provide recommendations based on your environment.

---

## Success Criteria

✅ Senzing SDK is installed and working (from Module 0)
✅ Demo script executes successfully
✅ Sample data loads without errors
✅ Entities are resolved and displayed with match explanations
✅ You understand what entity resolution does and WHY records matched
✅ You can see the before/after transformation
✅ You're excited to try it with your own data!

## Related Documentation

- `../../POWER.md` - Boot camp overview
- `../../steering/module-01-quick-demo.md` - Module 1 workflow
- `QUICK_START.md` - Quick start guide

## Version History

- **v3.0.0** (2026-03-17): Module 1 documentation created
