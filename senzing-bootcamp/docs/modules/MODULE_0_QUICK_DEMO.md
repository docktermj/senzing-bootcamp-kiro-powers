# Module 0: Quick Demo (Optional)

## Overview

Module 0 provides a quick demonstration of Senzing entity resolution using sample data. This optional module is perfect for first-time users who want to see entity resolution in action before working with their own data.

**Time**: 10-15 minutes  
**Prerequisites**: None  
**Output**: Working demo script with sample data

## Learning Objectives

By the end of this module, you will:
- Understand what entity resolution does
- See how Senzing automatically matches duplicate records
- Observe entity resolution in real-time
- Connect the demo to your own use case

## What You'll Do

1. Choose a sample dataset (Las Vegas, London, or Moscow)
2. Review sample records showing duplicates
3. Run a demo script that loads and resolves the data
4. Examine the resolved entities
5. Understand why records matched

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

1. **Initialize Senzing** with SQLite (no installation required if using Docker)
2. **Load sample records** from the chosen dataset
3. **Show progress** as records are processed
4. **Query results** to show resolved entities
5. **Display statistics** (records loaded, entities created, match rate)
6. **Show example entity** with all matching records

## Example Output

```
Loading records...
[====================] 100% (1000/1000 records)

Results:
- Records loaded: 1,000
- Entities created: 750
- Match rate: 25%
- Average records per entity: 1.33

Example resolved entity:
Entity ID: 1
Records matched: 3
  - Record 1 (CRM): John Smith, 123 Main St, (555) 123-4567
  - Record 2 (Support): J. Smith, 123 Main Street, (555) 123-4567
  - Record 3 (Sales): John R Smith, 123 Main St Apt 1, 555-123-4567

Match reasons:
  - Name similarity: 95%
  - Address match: 100%
  - Phone match: 100%
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

### Using Python

```bash
# Navigate to demo directory
cd src/quickstart_demo

# Run the demo
python demo_las_vegas.py
```

### Using Docker

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
A: No, if using Docker. The demo can run in a container with no installation.

**Q: Can I use my own data for the demo?**  
A: The demo uses sample data. You'll work with your data starting in Module 2.

**Q: How accurate is entity resolution?**  
A: Accuracy depends on data quality. Typical match rates: 90-99% precision, 85-95% recall.

**Q: Can I skip this module?**  
A: Yes, it's optional. Skip to Module 1 if you're ready to start with your data.

## Success Criteria

✅ Demo script runs successfully  
✅ Sample data loads without errors  
✅ Entities are resolved and displayed  
✅ You understand what entity resolution does  
✅ You can explain why records matched

## Troubleshooting

**Demo script fails to run**:
- Check Python version (3.8+)
- Verify Senzing is installed or Docker is available
- Check file paths are correct

**No matches found**:
- Verify sample data loaded correctly
- Check data format (should be JSONL)
- Ensure records have matching attributes

**Unexpected matches**:
- This is normal - entity resolution is probabilistic
- Review match reasons to understand why
- Adjust thresholds if needed (advanced topic)

## Related Documentation

- `../../POWER.md` - Boot camp overview
- `../../steering/steering.md` - Module 0 workflow
- `QUICK_START.md` - Quick start guide

## Version History

- **v3.0.0** (2026-03-17): Module 0 documentation created
