# Senzing Boot Camp Templates

Ready-to-use templates for common data transformation and loading patterns.

## Available Templates

### Transformation Templates
- `csv_mapping_template.py` - Transform CSV files to Senzing format
- `json_mapping_template.py` - Transform JSON files to Senzing format
- `database_extract_template.py` - Extract and transform from databases
- `api_extract_template.py` - Extract and transform from REST APIs

### Loading Templates
- `batch_loader_template.py` - Load data in batches
- `streaming_loader_template.py` - Load data in real-time
- `incremental_loader_template.py` - Load only new/changed records

### Query Templates
- `find_duplicates_template.py` - Find entities with multiple records
- `search_by_name_template.py` - Search for entities by name
- `get_entity_network_template.py` - Get entity relationships
- `export_entities_template.py` - Export resolved entities

### Utility Templates
- `data_quality_checker.py` - Validate data quality
- `config_manager.py` - Manage Senzing configuration
- `error_handler.py` - Handle errors and logging
- `performance_monitor.py` - Monitor performance metrics

## Using Templates

### Option 1: Copy and Customize

```bash
# Copy template to your project
cp senzing-bootcamp/templates/csv_mapping_template.py src/transform/transform_customers.py

# Edit the file
# - Update DATA_SOURCE name
# - Modify field mappings
# - Adjust file paths
```

### Option 2: Ask the Agent

```
"Create a transformation program for my CSV file using the template"
"Generate a batch loader based on the template"
```

The agent will customize the template for your specific needs.

### Option 3: Use as Reference

Browse templates to understand:
- Code structure
- Best practices
- Error handling patterns
- Documentation style

## Template Structure

Each template includes:
- **Header comments**: Purpose and usage
- **Configuration section**: Easy-to-modify settings
- **Core logic**: Well-documented implementation
- **Error handling**: Robust error management
- **Logging**: Progress and debugging output
- **Usage examples**: How to run the program

## Quick Reference

### CSV Transformation
```python
# Customize these sections:
DATA_SOURCE = "YOUR_SOURCE_NAME"
INPUT_FILE = "data/raw/your_file.csv"
OUTPUT_FILE = "data/transformed/your_file.jsonl"

def transform_record(source_record):
    # Map your fields here
    return {
        "DATA_SOURCE": DATA_SOURCE,
        "RECORD_ID": source_record["id"],
        "NAME_FULL": source_record["name"],
        # Add more mappings...
    }
```

### Batch Loading
```python
# Customize these sections:
DATA_SOURCE = "YOUR_SOURCE_NAME"
INPUT_FILE = "data/transformed/your_file.jsonl"
BATCH_SIZE = 1000

# Rest is handled by template
```

### Finding Duplicates
```python
# Customize these sections:
MIN_RECORDS = 2  # Minimum records to be considered duplicate
OUTPUT_FILE = "results/duplicates.json"

# Rest is handled by template
```

## Best Practices

### When Using Templates

1. **Always customize**: Don't use templates as-is
2. **Test with samples**: Use small data samples first
3. **Add error handling**: Enhance for your specific needs
4. **Document changes**: Note what you modified
5. **Version control**: Commit template-based code

### Template Modifications

**Do**:
- ✅ Change DATA_SOURCE names
- ✅ Modify field mappings
- ✅ Adjust batch sizes
- ✅ Add custom validation
- ✅ Enhance error messages

**Don't**:
- ❌ Remove error handling
- ❌ Skip logging
- ❌ Ignore configuration section
- ❌ Hard-code credentials
- ❌ Remove documentation

## Template Catalog

### csv_mapping_template.py
**Purpose**: Transform CSV files to Senzing JSON  
**Use when**: Source data is in CSV format  
**Customization**: Field mappings, data cleaning  
**Complexity**: Beginner

### json_mapping_template.py
**Purpose**: Transform JSON files to Senzing JSON  
**Use when**: Source data is in JSON format  
**Customization**: JSON path mappings, nested data  
**Complexity**: Beginner

### database_extract_template.py
**Purpose**: Extract from database and transform  
**Use when**: Source data is in a database  
**Customization**: SQL queries, connection strings  
**Complexity**: Intermediate

### api_extract_template.py
**Purpose**: Extract from REST API and transform  
**Use when**: Source data is from an API  
**Customization**: API endpoints, authentication  
**Complexity**: Intermediate

### batch_loader_template.py
**Purpose**: Load data in batches for performance  
**Use when**: Loading large datasets  
**Customization**: Batch size, error handling  
**Complexity**: Beginner

### streaming_loader_template.py
**Purpose**: Load data in real-time  
**Use when**: Continuous data ingestion  
**Customization**: Stream source, buffer size  
**Complexity**: Advanced

### incremental_loader_template.py
**Purpose**: Load only new/changed records  
**Use when**: Updating existing data  
**Customization**: Change detection logic  
**Complexity**: Intermediate

### find_duplicates_template.py
**Purpose**: Find entities with multiple records  
**Use when**: Identifying duplicates  
**Customization**: Duplicate criteria, output format  
**Complexity**: Beginner

### search_by_name_template.py
**Purpose**: Search for entities by name  
**Use when**: Looking up specific entities  
**Customization**: Search parameters  
**Complexity**: Beginner

### get_entity_network_template.py
**Purpose**: Get entity relationships  
**Use when**: Analyzing connections  
**Customization**: Relationship depth, filters  
**Complexity**: Intermediate

### export_entities_template.py
**Purpose**: Export resolved entities  
**Use when**: Creating master data file  
**Customization**: Export format, filters  
**Complexity**: Beginner

## Common Customizations

### Change Data Source Name
```python
# Find this line in template:
DATA_SOURCE = "TEMPLATE_SOURCE"

# Change to:
DATA_SOURCE = "CUSTOMERS"
```

### Modify Field Mappings
```python
# Find the transform_record function
def transform_record(source_record):
    return {
        "DATA_SOURCE": DATA_SOURCE,
        "RECORD_ID": source_record["id"],  # Change field name
        "NAME_FULL": source_record["name"],  # Change field name
        # Add more fields as needed
    }
```

### Adjust Batch Size
```python
# Find this line:
BATCH_SIZE = 1000

# Adjust based on your needs:
BATCH_SIZE = 5000  # Larger for better performance
BATCH_SIZE = 100   # Smaller for testing
```

### Add Custom Validation
```python
# Add to transform_record function:
def transform_record(source_record):
    # Custom validation
    if not source_record.get("email"):
        logger.warning(f"Missing email for record {source_record['id']}")
    
    # Rest of transformation...
```

## Troubleshooting

**Template doesn't work**:
- Check you've customized all required sections
- Verify file paths are correct
- Ensure DATA_SOURCE is registered

**Performance issues**:
- Adjust BATCH_SIZE
- Add multiprocessing (see advanced templates)
- Optimize transformation logic

**Data quality problems**:
- Add validation in transform_record
- Use data_quality_checker template
- Review mapping logic

**Import errors**:
- Install required packages: `pip install -r requirements.txt`
- Check Python version (3.8+)
- Verify Senzing is installed

## Contributing Templates

Have a useful template? Contribute it!

1. Follow existing template structure
2. Include comprehensive documentation
3. Add usage examples
4. Test with sample data
5. Submit a pull request

## Support

- Ask the agent to help customize templates
- Review `docs/modules/` for detailed guidance
- Check `examples/` for complete implementations
- Use `search_docs` for Senzing-specific questions

## Version History

- **v3.0.0** (2026-03-17): Templates directory created with 12 templates
