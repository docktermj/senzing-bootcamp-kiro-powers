# Removed Demo Scripts

These demo scripts were removed from the Senzing Bootcamp Power distribution because the MCP server can generate them dynamically.

## Files in This Directory (3 files)

1. **demo_customer_360.py** - Customer 360 / deduplication demo
2. **demo_fraud_detection.py** - Fraud detection demo
3. **demo_vendor_mdm.py** - Vendor MDM demo

## Why Removed

The Senzing MCP Server provides two tools that replace these static demo scripts:

### 1. `get_sample_data` - Dynamic Sample Data

```python
# Get sample data from CORD datasets
get_sample_data(
    dataset="las-vegas",  # or "london", "moscow"
    limit=100
)
```

**Benefits:**

- Always current data format
- Multiple datasets available
- Configurable sample size
- No static files to maintain

### 2. `generate_scaffold` - Dynamic Demo Code

```python
# Generate demo script in any language
generate_scaffold(
    language="python",  # or "java", "csharp", "rust", "typescript"
    workflow="full_pipeline",
    version="current"
)
```

**Benefits:**

- Always current SDK version
- Supports 5 languages
- Follows latest best practices
- Never outdated

## How Module 0 Works Now

Instead of using pre-existing demo scripts, the agent:

1. Creates `src/quickstart_demo/` directory
2. Calls `get_sample_data` to get sample records
3. Calls `generate_scaffold` to generate demo code
4. Saves both to `src/quickstart_demo/`
5. User runs the freshly-generated demo

## Benefits of Removal

1. **Always Current** - Demo code uses latest SDK version
2. **Multi-Language** - Can generate demos in Python, Java, C#, Rust, TypeScript
3. **No Maintenance** - No static demo scripts to update when SDK changes
4. **Smaller Distribution** - Power package is more focused
5. **Better Learning** - Users see how to generate code, not just run pre-made scripts

## For Maintainers

These demo scripts are preserved here for reference, but should not be added back to the Power distribution. The MCP server approach is superior because:

- Demo code stays current with SDK changes
- Supports multiple programming languages
- Teaches users how to generate code
- Reduces maintenance burden

## Version History

- **2026-03-23**: Moved demo scripts from Power distribution to development repository
- **2026-03-17**: Original demo scripts created (customer_360, fraud_detection, vendor_mdm)
