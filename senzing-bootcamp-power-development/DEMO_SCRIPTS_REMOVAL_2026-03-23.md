# Demo Scripts Removal Summary

**Date**: 2026-03-23  
**Purpose**: Remove static demo scripts, leverage MCP server for dynamic code generation

## Executive Summary

Removed 3 static demo scripts from `src/quickstart_demo/` because the Senzing MCP Server can generate them dynamically with always-current code in 5 languages.

## Files Removed (3 files)

**Location:** `src/quickstart_demo/`

1. **demo_customer_360.py** - Customer 360 / deduplication demo
2. **demo_fraud_detection.py** - Fraud detection demo
3. **demo_vendor_mdm.py** - Vendor MDM demo

## Why Removed

### Problem with Static Demo Scripts

- Become outdated when SDK changes
- Only available in Python
- Require maintenance when SDK updates
- Don't teach users how to generate code
- Add to distribution size

### MCP Server Solution

The Senzing MCP Server provides two tools that replace static demos:

#### 1. `get_sample_data` - Dynamic Sample Data

```python
get_sample_data(
    dataset="las-vegas",  # or "london", "moscow"  
    limit=100
)
```

**Provides:**
- Las Vegas, London, Moscow datasets
- Always current data format
- Configurable sample size
- Ready-to-use Senzing JSON

#### 2. `generate_scaffold` - Dynamic Demo Code

```python
generate_scaffold(
    language="python",  # or "java", "csharp", "rust", "typescript"
    workflow="full_pipeline",
    version="current"
)
```

**Provides:**
- Complete demo script with initialization, loading, querying
- Always current SDK version
- 5 language options
- Follows latest best practices

## How Module 0 Works Now

### Old Approach (Static Scripts)
1. User starts Module 0
2. Agent points to pre-existing demo script
3. User runs `python src/quickstart_demo/demo_customer_360.py`
4. Demo uses hardcoded sample data

**Problems:**
- Demo script may be outdated
- Only Python available
- Can't customize easily

### New Approach (MCP-Generated)
1. User starts Module 0
2. Agent creates `src/quickstart_demo/` directory
3. Agent calls `get_sample_data(dataset="las-vegas", limit=100)`
4. Agent calls `generate_scaffold(language="python", workflow="full_pipeline")`
5. Agent saves both to `src/quickstart_demo/`
6. User runs freshly-generated demo

**Benefits:**
- Always current SDK version
- Can generate in Python, Java, C#, Rust, TypeScript
- User learns how to generate code
- Customizable on-demand

## References Updated

### Files Modified

1. **docs/policies/PEP8_COMPLIANCE.md**
   - Removed demo scripts from compliance list
   - Updated count from 14 to 11 scripts

### Files That Still Reference `src/quickstart_demo/`

These files correctly reference the directory (which agent creates) but not the specific demo files:

- POWER.md - Directory structure
- README.md - File organization policy
- docs/modules/MODULE_0_QUICK_DEMO.md - Module 0 workflow
- docs/modules/MODULE_1_BUSINESS_PROBLEM.md - Directory structure
- docs/policies/MODULE_0_CODE_LOCATION.md - Policy document
- docs/policies/README.md - Policy summary
- docs/policies/FILE_STORAGE_POLICY.md - File organization
- docs/policies/PYTHON_REQUIREMENTS_POLICY.md - Requirements location
- steering/agent-instructions.md - Module 0 workflow
- steering/quick-reference.md - Module 0 quick reference

**These references are correct** - they describe where the agent should save MCP-generated demo code, not pre-existing files.

## Benefits

### 1. Always Current
- Demo code uses latest SDK version automatically
- No risk of outdated examples
- Follows current best practices

### 2. Multi-Language Support
- Can generate demos in 5 languages
- Users can try their preferred language
- Better learning experience

### 3. Reduced Maintenance
- No static demo scripts to update
- MCP server handles SDK changes
- Fewer files to maintain

### 4. Better Learning
- Users see how to generate code
- Teaches MCP tool usage
- More practical for real projects

### 5. Smaller Distribution
- 3 fewer files in Power package
- Cleaner, more focused distribution
- Faster downloads

## Comparison

| Aspect | Old (Static Scripts) | New (MCP-Generated) |
|--------|---------------------|---------------------|
| **Languages** | Python only | Python, Java, C#, Rust, TypeScript |
| **SDK Version** | Fixed at creation time | Always current |
| **Maintenance** | Manual updates needed | Automatic via MCP |
| **Customization** | Edit static file | Generate with parameters |
| **Learning Value** | Run pre-made script | Learn to generate code |
| **Distribution Size** | +3 files | 0 files |

## Agent Behavior

### Module 0 Workflow (Updated)

When user starts Module 0:

1. **Create directory**:
   ```bash
   mkdir -p src/quickstart_demo
   ```

2. **Get sample data**:
   ```python
   # Agent calls MCP tool
   get_sample_data(dataset="las-vegas", limit=100)
   # Save to src/quickstart_demo/sample_data_las_vegas.jsonl
   ```

3. **Generate demo code**:
   ```python
   # Agent calls MCP tool
   generate_scaffold(
       language="python",
       workflow="full_pipeline", 
       version="current"
   )
   # Save to src/quickstart_demo/demo_las_vegas.py
   ```

4. **User runs demo**:
   ```bash
   cd src/quickstart_demo
   python demo_las_vegas.py
   ```

## For Future Maintainers

**Do NOT add static demo scripts back.** The MCP server approach is superior because:

1. Always current with SDK changes
2. Supports multiple languages
3. Teaches users how to generate code
4. Reduces maintenance burden
5. Smaller distribution

If users need demo scripts, the agent generates them on-demand using MCP tools.

## Verification

### Files Removed
```bash
# Verified demo scripts moved to development
ls senzing-bootcamp-development/quickstart_demo/
# demo_customer_360.py
# demo_fraud_detection.py
# demo_vendor_mdm.py
# README.md
```

### Directory Still Created
The `src/quickstart_demo/` directory is still created by the agent during Module 0, but it's populated with MCP-generated code rather than pre-existing files.

### References Updated
- ✅ PEP8_COMPLIANCE.md updated (removed demo scripts from list)
- ✅ All other references correctly point to directory, not specific files
- ✅ No broken links

## Related Documentation

- **REORGANIZATION_SUMMARY.md** - Overall documentation reorganization
- **GUIDES_REORGANIZATION_2026-03-23.md** - Guide files reorganization
- **senzing-bootcamp-development/quickstart_demo/README.md** - Removed demo scripts index

## Version History

- **2026-03-23**: Removed static demo scripts
  - Moved 3 demo files to development repository
  - Updated PEP8_COMPLIANCE.md
  - Created removal summary documentation
  - Verified all references
