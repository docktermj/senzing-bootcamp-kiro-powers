# Module 0: Quick Demo (Optional)

## Overview

Module 0 provides a live demonstration of Senzing entity resolution using sample data. This optional module is perfect for first-time users who want to see entity resolution in action before working with their own data.

Unlike a static demo, this module actually runs the Senzing SDK to demonstrate real entity resolution, showing you the "aha moment" of watching duplicate records automatically resolve into unique entities.

**Time**: 10-15 minutes  
**Prerequisites**: None (Senzing SDK will be set up automatically)  
**Output**: Working demo with actual entity resolution results

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
3. Set up Senzing SDK (automatic - uses Docker or local installation)
4. Initialize an in-memory SQLite database
5. Load sample records into Senzing
6. Query the resolved entities
7. See match explanations showing WHY records matched
8. Compare before/after (5 records → X entities)

## Sample Datasets

### Las Vegas Dataset
- **Type**: Customer records
- **Records**: ~1,000
- **Use case**: Retail/hospitality customer deduplication
- **Duplicates**: Same customers with variations in names, addresses, phones

### London Dataset
- **Type**: Person records
- **Records**: ~1,000
- **Use case**: Identity management
- **Duplicates**: Same people with name variations and different contact info

### Moscow Dataset
- **Type**: Organization records
- **Records**: ~1,000
- **Use case**: B2B vendor/supplier matching
- **Duplicates**: Same companies with different names and addresses

## Demo Script Structure

The generated demo script will:

1. **Check for Senzing SDK** - Detects if SDK is installed, offers Docker alternative
2. **Initialize Senzing** with in-memory SQLite database
3. **Load sample records** from the chosen dataset (with progress bar)
4. **Query resolved entities** to show which records matched
5. **Display match explanations** showing WHY records matched (name similarity, address match, etc.)
6. **Show statistics** (records loaded, entities created, match rate)
7. **Display example entities** with all matching records side-by-side
8. **Provide before/after comparison** (e.g., "5 records → 3 entities")

This is a real, working demonstration - not a simulation!

## Example Output

```
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

## File Locations

All Module 0 demo code is saved in `src/quickstart_demo/`:

```
src/quickstart_demo/
├── demo_las_vegas.py          # Demo script for Las Vegas dataset
├── demo_london.py              # Demo script for London dataset
├── demo_moscow.py              # Demo script for Moscow dataset
├── sample_data_las_vegas.jsonl # Sample data
├── sample_data_london.jsonl    # Sample data
└── sample_data_moscow.jsonl    # Sample data
```

## Running the Demo

The demo runs automatically when you start Module 0. The agent will:

1. Check if Senzing SDK is installed
2. If not installed, offer to:
   - Use Docker (recommended for quick demo)
   - Guide you through SDK installation
3. Generate and run the demo script
4. Display results in real-time

### Manual Execution

If you want to run the demo again later:

```bash
# Navigate to demo directory
cd src/quickstart_demo

# Run the demo
python demo_las_vegas.py
```

### Using Docker (No Installation Required)

```bash
# Run demo in Docker container
docker run -v $(pwd)/src/quickstart_demo:/data \
  senzing/senzing-tools \
  python /data/demo_las_vegas.py
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
- **Ready to start?** → Proceed to Module 1 (Business Problem)
- **Want to try another dataset?** → Run another demo
- **Have questions?** → Ask about specific entity resolution concepts

## Common Questions

**Q: Do I need to install Senzing to run the demo?**  
A: No! The demo can run in Docker with no installation. If you want to install the SDK, the agent will guide you through it.

**Q: Does this actually run Senzing, or is it a simulation?**  
A: This runs the real Senzing SDK! You'll see actual entity resolution happening, not a simulation or mock-up.

**Q: Can I use my own data for the demo?**  
A: The demo uses sample data to ensure a quick, successful experience. You'll work with your data starting in Module 2.

**Q: How accurate is entity resolution?**  
A: Accuracy depends on data quality. Typical match rates: 90-99% precision, 85-95% recall. The demo shows real match confidence scores.

**Q: Can I skip this module?**  
A: Yes, it's optional. Skip to Module 1 if you're ready to start with your data. But we recommend the demo - it only takes 10 minutes and shows the value immediately.

## Success Criteria

✅ Senzing SDK is running (Docker or local installation)  
✅ Demo script executes successfully  
✅ Sample data loads without errors  
✅ Entities are resolved and displayed with match explanations  
✅ You understand what entity resolution does and WHY records matched  
✅ You can see the before/after transformation  
✅ You're excited to try it with your own data!

## Troubleshooting

**Senzing SDK not found**:
- Use Docker option (no installation required)
- Or follow SDK installation guide provided by agent
- Check PATH if SDK is installed but not detected

**Demo script fails to run**:
- Check Python version (3.8+)
- Verify dependencies: `pip install senzing`
- Check file paths are correct

**No matches found**:
- This shouldn't happen with sample data - contact support
- Verify sample data loaded correctly
- Check Senzing engine initialized properly

**Unexpected matches**:
- This is normal - entity resolution is probabilistic
- Review match explanations to understand why
- Different confidence thresholds can be adjusted (advanced topic)

## Related Documentation

- `../../POWER.md` - Boot camp overview
- `../../steering/steering.md` - Module 0 workflow
- `QUICK_START.md` - Quick start guide

## Version History

- **v3.0.0** (2026-03-17): Module 0 documentation created
