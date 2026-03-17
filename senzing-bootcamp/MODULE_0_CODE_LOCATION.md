# Module 0 (Quick Demo) Code Location Policy

## Policy

All code generated during Module 0 (Quick Demo) must be saved in the `src/quickstart_demo/` directory. This keeps demo code separate from the main boot camp project code.

## Why This Matters

Module 0 is optional and exploratory:
- Users may try multiple demo datasets
- Demo code is temporary/experimental
- Should not mix with production boot camp code
- Easy to clean up after demo
- Clear separation of concerns

## Directory Structure

```
my-senzing-project/
├── src/
│   ├── quickstart_demo/           # Module 0 demo code (optional)
│   │   ├── demo_las_vegas.py      # Demo script for Las Vegas dataset
│   │   ├── demo_london.py         # Demo script for London dataset
│   │   ├── demo_moscow.py         # Demo script for Moscow dataset
│   │   ├── sample_data_las_vegas.jsonl  # Sample data
│   │   ├── sample_data_london.jsonl     # Sample data
│   │   └── sample_data_moscow.jsonl     # Sample data
│   ├── transform/                 # Module 3 - Real transformation programs
│   ├── load/                      # Module 5 - Real loading programs
│   ├── query/                     # Module 6 - Real query programs
│   └── utils/                     # Shared utilities
```

## What Goes in src/quickstart_demo/

### Demo Scripts
- ✅ `demo_[dataset_name].py` - Complete demo script
- ✅ `demo_las_vegas.py` - Las Vegas dataset demo
- ✅ `demo_london.py` - London dataset demo
- ✅ `demo_moscow.py` - Moscow dataset demo

### Sample Data Files
- ✅ `sample_data_[dataset_name].jsonl` - Sample data from CORD
- ✅ `sample_data_las_vegas.jsonl` - Las Vegas sample data
- ✅ `sample_data_london.jsonl` - London sample data
- ✅ `sample_data_moscow.jsonl` - Moscow sample data

### Demo Output (optional)
- ✅ `demo_results_[dataset_name].json` - Query results from demo
- ✅ `demo_stats_[dataset_name].txt` - Statistics from demo run

## What Does NOT Go in src/quickstart_demo/

### Real Project Code
- ❌ Transformation programs for user's actual data
- ❌ Loading programs for user's actual data
- ❌ Query programs for user's actual data
- ❌ Production utilities

These belong in:
- `src/transform/` - Real transformation programs (Module 3)
- `src/load/` - Real loading programs (Module 5)
- `src/query/` - Real query programs (Module 6)
- `src/utils/` - Shared utilities

## Agent Behavior for Module 0

### Step 1: Create Directory
```bash
mkdir -p src/quickstart_demo
```

Always create this directory before generating any Module 0 code.

### Step 2: Generate Demo Script
```python
# Call generate_scaffold
generate_scaffold(language="python", workflow="full_pipeline", version="current")

# Save to src/quickstart_demo/
# Example: src/quickstart_demo/demo_las_vegas.py
```

### Step 3: Save Sample Data
```python
# Call get_sample_data
get_sample_data(dataset="las-vegas", limit=100)

# Save to src/quickstart_demo/
# Example: src/quickstart_demo/sample_data_las_vegas.jsonl
```

### Step 4: Run Demo
```bash
cd src/quickstart_demo
python demo_las_vegas.py
```

### Step 5: Explain Results
Show user the output and explain entity resolution concepts.

### Step 6: Transition
Ask if user wants to:
- Try another demo dataset (repeat in same directory)
- Start Module 1 with their own data (use main project structure)
- Learn more about entity resolution

## Naming Conventions

### Demo Scripts
Format: `demo_[dataset_name].py`

Examples:
- `demo_las_vegas.py`
- `demo_london.py`
- `demo_moscow.py`
- `demo_custom.py` (if user provides custom sample data)

### Sample Data Files
Format: `sample_data_[dataset_name].jsonl`

Examples:
- `sample_data_las_vegas.jsonl`
- `sample_data_london.jsonl`
- `sample_data_moscow.jsonl`

### Output Files (optional)
Format: `demo_results_[dataset_name].json` or `demo_stats_[dataset_name].txt`

Examples:
- `demo_results_las_vegas.json`
- `demo_stats_las_vegas.txt`

## Cleanup After Demo

After completing Module 0, users can optionally clean up demo files:

```bash
# Remove all demo code (optional)
rm -rf src/quickstart_demo/

# Or keep for reference
# Demo code won't interfere with main boot camp
```

**Agent behavior**: Don't automatically delete demo code. Let users decide if they want to keep it for reference.

## Multiple Demo Runs

Users may run multiple demos:

```
src/quickstart_demo/
├── demo_las_vegas.py
├── sample_data_las_vegas.jsonl
├── demo_london.py
├── sample_data_london.jsonl
├── demo_moscow.py
└── sample_data_moscow.jsonl
```

This is fine! All demos stay in the same directory.

## Transition to Real Project

When user moves from Module 0 to Module 1:

**Module 0 (Demo)**:
- Code in: `src/quickstart_demo/`
- Data: Sample CORD datasets
- Purpose: Learning and exploration

**Module 1+ (Real Project)**:
- Code in: `src/transform/`, `src/load/`, `src/query/`
- Data: User's actual data sources
- Purpose: Production entity resolution

The separation is clear and intentional.

## Documentation Updates

All documentation has been updated:

### steering/steering.md - Module 0 Workflow
- ✅ Step 4: Create `src/quickstart_demo/` directory
- ✅ Step 5: Save demo script to `src/quickstart_demo/demo_[dataset_name].py`
- ✅ Step 6: Save sample data to `src/quickstart_demo/sample_data_[dataset_name].jsonl`

### steering/agent-instructions.md - Module 0
- ✅ Create `src/quickstart_demo/` directory for all demo code
- ✅ Save demo script to `src/quickstart_demo/demo_[dataset_name].py`
- ✅ Save sample data to `src/quickstart_demo/sample_data_[dataset_name].jsonl`

### steering/quick-reference.md - Module 0
- ✅ Important note about creating `src/quickstart_demo/`
- ✅ File naming conventions
- ✅ Keep demo code separate from main project

### POWER.md - Project Directory Structure
- ✅ Added `src/quickstart_demo/` to directory tree
- ✅ Marked as "(optional)" since Module 0 is optional

### steering/steering.md - Project Directory Structure
- ✅ Added `src/quickstart_demo/` to directory listing
- ✅ Marked as "Module 0 demo code (optional)"

## Example Module 0 Session

```bash
# User starts Module 0
$ mkdir -p src/quickstart_demo

# Agent generates demo script
$ cat src/quickstart_demo/demo_las_vegas.py
#!/usr/bin/env python3
"""
Quick Demo: Las Vegas Dataset
Generated for Senzing Boot Camp Module 0
"""
import json
from senzing import G2Engine
# ... demo code ...

# Agent saves sample data
$ head -3 src/quickstart_demo/sample_data_las_vegas.jsonl
{"DATA_SOURCE":"CUSTOMERS","RECORD_ID":"1001","NAME_FULL":"John Smith",...}
{"DATA_SOURCE":"CUSTOMERS","RECORD_ID":"1002","NAME_FULL":"J. Smith",...}
{"DATA_SOURCE":"CUSTOMERS","RECORD_ID":"1003","NAME_FULL":"John A Smith",...}

# User runs demo
$ cd src/quickstart_demo
$ python demo_las_vegas.py
Loading 100 sample records...
✅ Loaded 100 records
✅ Created 87 entities
✅ Found 13 duplicates
...

# User moves to Module 1
# Demo code stays in src/quickstart_demo/
# Real project code goes in src/transform/, src/load/, src/query/
```

## Benefits

1. **Clear Separation**: Demo code doesn't mix with production code
2. **Easy Cleanup**: Can delete entire directory if desired
3. **Multiple Demos**: Can run multiple demos without conflicts
4. **Organization**: Clear where demo code lives
5. **No Confusion**: Users know demo vs. real project code

## Summary

✅ All Module 0 code → `src/quickstart_demo/`  
✅ Demo scripts → `src/quickstart_demo/demo_[dataset].py`  
✅ Sample data → `src/quickstart_demo/sample_data_[dataset].jsonl`  
✅ Keep separate from main project code  
✅ Optional cleanup after demo  
✅ All documentation updated  
✅ Clear naming conventions  
✅ Agent instructions include this requirement
