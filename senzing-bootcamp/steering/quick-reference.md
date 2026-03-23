---
inclusion: always
---

# Quick Reference Card

Fast reference for common Senzing MCP tool calls and workflows.

## Essential First Call

```
get_capabilities(version="current")
```
Always call this first to discover available tools and confirm MCP server connectivity.

## Module 0: Quick Demo

```
# Get sample data
get_sample_data(dataset="las-vegas", limit=100)

# Generate demo script
generate_scaffold(language="python", workflow="full_pipeline", version="current")
```

**IMPORTANT**: 
- Create `src/quickstart_demo/` directory for all Module 0 demo code
- Save demo script to `src/quickstart_demo/demo_[dataset_name].py`
- Save sample data to `src/quickstart_demo/sample_data_[dataset_name].jsonl`
- Keep demo code separate from main boot camp project code

## Module 1: Business Problem

No MCP calls required - focus on discovery questions and documentation.

## Module 2: Identify and Collect Data Sources

No MCP calls required - focus on collecting data files.

**Actions**:
- Help user upload files to `data/raw/`
- Document data source locations in `docs/data_source_locations.md`
- Handle different source types: files, databases, APIs
- Create sample files if datasets are too large
- Verify files are accessible

## Module 3: Evaluate Data Quality

```
# Analyze data quality
analyze_record(file_paths=["data/transformed/customers.jsonl"], version="current")

# Get quality scoring guidance
search_docs(query="data quality", category="data_analysis", version="current")
```

## Module 4: Map Your Data

```
# Start mapping workflow
mapping_workflow(action="start", file_paths=["data/raw/customers.csv"], version="current")

# Advance through steps (remember to pass state!)
mapping_workflow(action="advance", data={...}, state={...}, version="current")

# Validate output
lint_record(file_paths=["data/transformed/customers.jsonl"], version="current")

# Analyze quality
analyze_record(file_paths=["data/transformed/customers.jsonl"], version="current")
```

**CRITICAL**: Always pass the exact `state` object from the previous response back in the next call.

## Module 5: Set Up SDK

```
# FIRST: Check if already installed
python -c "import senzing; print('Senzing version:', senzing.__version__)" 2>/dev/null

# If not installed, get installation commands
sdk_guide(topic="install", platform="linux_apt", version="current")
sdk_guide(topic="install", platform="macos_arm", version="current")
sdk_guide(topic="install", platform="docker", version="current")

# Get configuration guidance
sdk_guide(topic="configure", data_sources=["CUSTOMER_DB", "VENDOR_API"], version="current")

# Check for anti-patterns
search_docs(query="installation best practices", category="anti_patterns", version="current")
```

**IMPORTANT**: Always verify Senzing is not already installed before running installation commands.

## Module 6: Load Single Data Source

```
# Generate loading code
generate_scaffold(language="python", workflow="add_records", version="current")

# Get loading guidance
sdk_guide(topic="load", input_file="data/transformed/customers.jsonl", version="current")

# Get full pipeline example
sdk_guide(topic="full_pipeline", language="python", platform="docker", version="current")
```

## Module 7: Multi-Source Orchestration

No specific MCP calls - focus on orchestration logic.

**Actions**:
- Define load order based on dependencies
- Create orchestration scripts
- Implement error handling across sources

## Module 8: Query and Validate Results

```
# Generate query code
generate_scaffold(language="python", workflow="query", version="current")
generate_scaffold(language="python", workflow="search", version="current")

# Get SDK reference for methods
get_sdk_reference(topic="functions", filter="searchByAttributes", version="current")
get_sdk_reference(topic="flags", version="current")
```

## Modules 9-12: Production Readiness

**Module 9: Performance Testing**
- Benchmark transformation and loading
- Test query response times
- Profile resource utilization

**Module 10: Security Hardening**
- Implement secrets management
- Set up authentication/authorization
- Enable encryption

**Module 11: Monitoring**
- Set up logging and metrics
- Configure alerting
- Create dashboards

**Module 12: Deployment**
- Package application
- Set up multi-environment strategy
- Implement disaster recovery

## Troubleshooting

```
# Explain error codes
explain_error_code(error_code="SENZ0005", version="current")
explain_error_code(error_code="0042", version="current")

# Search documentation
search_docs(query="resolution principles", version="current")
search_docs(query="database tuning", category="database", version="current")
search_docs(query="performance optimization", category="performance", version="current")

# Find code examples
find_examples(query="batch loading python")
find_examples(repo="brianmacy/sz_mem-v4", list_files=true)
find_examples(repo="brianmacy/sz_mem-v4", file_path="sz_mem.py")
```

## SDK Reference

```
# Get method signatures
get_sdk_reference(topic="functions", filter="addRecord", version="current")

# Get flag definitions
get_sdk_reference(topic="flags", filter="G2_EXPORT", version="current")

# Response schemas
get_sdk_reference(topic="response_schemas", version="current")
```

## Common Patterns

### Check Before Recommending Architecture
```
search_docs(query="[your approach]", category="anti_patterns", version="current")
```

### Never Guess Attribute Names
```
# WRONG: Hand-coding {"BUSINESS_NAME_ORG": "Acme Corp"}
# RIGHT: Use mapping_workflow to get correct attribute names
```

### Never Guess Method Names
```
# WRONG: engine.close_export(handle)
# RIGHT: Use generate_scaffold or get_sdk_reference
```

## Version Parameter

All MCP tools accept a `version` parameter:
- `"current"` - Latest Senzing version (default, recommended)
- `"4.0"` - Senzing V4 specific

## When to Load This Reference

Load this quick reference when:
- Starting any module
- User asks "what MCP tool should I use?"
- Need a fast reminder of tool signatures
- Troubleshooting workflow issues
