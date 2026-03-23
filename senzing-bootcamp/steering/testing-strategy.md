---
inclusion: manual
---

# Testing Strategy

Implement testing at each module to ensure quality and reliability.

## Test Types

### 1. Unit Tests (Module 4 - Transformation)

Test individual transformation functions:

```python
# tests/test_transform_customer.py
import unittest
from src.transform.transform_customer_crm import transform_record

class TestCustomerTransform(unittest.TestCase):
    def test_name_mapping(self):
        source_record = {"customer_name": "John Doe"}
        result = transform_record(source_record)
        self.assertEqual(result["NAME_FULL"], "John Doe")
    
    def test_missing_fields(self):
        source_record = {"customer_id": "123"}
        result = transform_record(source_record)
        self.assertIn("RECORD_ID", result)
        self.assertEqual(result["RECORD_ID"], "123")
    
    def test_data_cleansing(self):
        source_record = {"phone": "  (555) 123-4567  "}
        result = transform_record(source_record)
        self.assertEqual(result["PHONE_NUMBER"], "555-123-4567")
```

### 2. Integration Tests (Module 6-7 - Loading)

Test the complete loading process:

```python
# tests/test_load_customer.py
import unittest
from src.load.load_customer_crm import load_records
from senzing import G2Engine

class TestCustomerLoad(unittest.TestCase):
    def setUp(self):
        self.engine = G2Engine()
        # Initialize with test database
    
    def test_load_sample_records(self):
        result = load_records("data/samples/customer_sample.jsonl", "TEST_CRM")
        self.assertEqual(result["success_count"], 10)
        self.assertEqual(result["error_count"], 0)
    
    def test_duplicate_record_handling(self):
        # Load same record twice
        load_records("data/samples/duplicate_test.jsonl", "TEST_CRM")
        # Verify only one entity created
```

### 3. Data Quality Tests (Module 4)

Validate data quality metrics:

```python
# tests/test_data_quality.py
import unittest
from src.utils.data_quality import analyze_quality

class TestDataQuality(unittest.TestCase):
    def test_attribute_coverage(self):
        records = load_transformed_records("data/transformed/customer_crm_senzing.jsonl")
        quality = analyze_quality(records)
        self.assertGreater(quality["name_coverage"], 0.95)
        self.assertGreater(quality["address_coverage"], 0.80)
    
    def test_data_completeness(self):
        records = load_transformed_records("data/transformed/customer_crm_senzing.jsonl")
        quality = analyze_quality(records)
        self.assertGreater(quality["overall_score"], 70)
```

### 4. Query Validation Tests (Module 8)

Verify query results:

```python
# tests/test_query_duplicates.py
import unittest
from src.query.find_duplicates import find_duplicates_for_datasource

class TestDuplicateQuery(unittest.TestCase):
    def test_finds_known_duplicates(self):
        # Load test data with known duplicates
        duplicates = find_duplicates_for_datasource("TEST_CRM")
        self.assertGreater(len(duplicates), 0)
    
    def test_no_false_positives(self):
        # Load test data with no duplicates
        duplicates = find_duplicates_for_datasource("TEST_UNIQUE")
        self.assertEqual(len(duplicates), 0)
```

## Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_transform_customer.py

# Run with coverage
python -m pytest --cov=src tests/
```

## Test-Driven Development Workflow

1. Write tests before implementing transformation logic
2. Run tests to verify they fail (red)
3. Implement the transformation
4. Run tests to verify they pass (green)
5. Refactor and optimize (refactor)
6. Repeat for each data source

## When to Load This Guide

Load this steering file when:
- Starting Module 4 (before creating transformation programs)
- User asks about testing or quality assurance
- Generating transformation or loading programs
- User wants to implement CI/CD
- Troubleshooting data quality issues
