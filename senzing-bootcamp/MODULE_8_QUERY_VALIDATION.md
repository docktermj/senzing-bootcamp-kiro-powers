# Module 8: Query and Validate Results

## Overview

Module 8 focuses on creating query programs to explore entity resolution results and validating that the solution meets business requirements through User Acceptance Testing (UAT).

**Focus**: Query resolved entities and validate results against business requirements.

**Time**: 1-2 hours

## Prerequisites

- ✅ Module 7 complete (all sources loaded) OR Module 6 complete (single source loaded)
- ✅ No critical loading errors
- ✅ Loading statistics reviewed
- ✅ Business requirements from Module 1 available

## Learning Objectives

By the end of this module, you will:

1. Understand Senzing query operations
2. Generate query programs for your use cases
3. Explore entity resolution results
4. Create User Acceptance Test (UAT) cases
5. Validate results against business requirements
6. Get stakeholder sign-off

## Key Concepts

### Query Types

Senzing provides several query operations:

**1. Get Entity by Record ID**
```python
# Find the entity that contains a specific record
entity = engine.getEntityByRecordID(DATA_SOURCE, RECORD_ID)
```
Use when: You have a specific record and want to see its resolved entity

**2. Search by Attributes**
```python
# Search for entities matching attributes
search_json = json.dumps({
    "NAME_FULL": "John Smith",
    "ADDR_FULL": "123 Main St"
})
results = engine.searchByAttributes(search_json)
```
Use when: You want to find entities matching certain criteria

**3. Get Entity by Entity ID**
```python
# Get a specific entity by its ID
entity = engine.getEntityByEntityID(entity_id)
```
Use when: You know the entity ID and want full details

**4. Why Entities**
```python
# Understand why two records resolved together
why = engine.whyEntities(entity_id_1, entity_id_2)
```
Use when: You want to understand matching logic

**5. How Entity**
```python
# See how an entity was built from records
how = engine.howEntityByEntityID(entity_id)
```
Use when: You want to see the resolution steps

## Workflow

### Step 1: Define Query Requirements

Based on Module 1 business problem, identify what queries you need:

**Customer 360 Example**:
- Find all records for a customer by name and email
- Get complete customer profile by customer ID
- Find potential duplicates for a new customer

**Fraud Detection Example**:
- Find all entities sharing an address
- Find entities with similar names but different SSNs
- Get relationship network for suspicious entity

**Data Migration Example**:
- Find which legacy records merged together
- Identify records that didn't match anything
- Get mapping from old IDs to new entity IDs

### Step 2: Generate Query Program

Generate a query program using the Senzing MCP server:

```
Use: generate_scaffold
Parameters:
  language: python (or java, csharp, rust)
  workflow: query
  version: current
```

The scaffold will include:
- SDK initialization
- Query operations
- Result formatting
- Error handling

### Step 3: Customize Query Program

Customize the generated scaffold for your use case:

```python
#!/usr/bin/env python3
"""
Customer 360 Query Program
Find complete customer profile by name and email
"""

import json
from senzing import SzEngine, SzEngineFlags

def find_customer(name, email):
    """Find customer entity by name and email"""
    
    # Initialize engine
    engine = SzEngine()
    engine.initialize(instance_name='senzing-bootcamp', settings=ENGINE_CONFIG)
    
    # Build search attributes
    search_attrs = {
        "NAME_FULL": name,
        "EMAIL_ADDRESS": email
    }
    
    # Search for matching entities
    results = engine.searchByAttributes(
        json.dumps(search_attrs),
        flags=SzEngineFlags.SZ_SEARCH_INCLUDE_RESOLVED
    )
    
    results_data = json.loads(results)
    
    if not results_data.get('RESOLVED_ENTITIES'):
        print(f"No customer found for {name} / {email}")
        return None
    
    # Get first match (highest confidence)
    entity_id = results_data['RESOLVED_ENTITIES'][0]['ENTITY']['RESOLVED_ENTITY']['ENTITY_ID']
    
    # Get full entity details
    entity = engine.getEntityByEntityID(
        entity_id,
        flags=SzEngineFlags.SZ_ENTITY_INCLUDE_ALL_FEATURES
    )
    
    entity_data = json.loads(entity)
    
    # Format output
    print(f"\n{'='*60}")
    print(f"CUSTOMER PROFILE - Entity ID: {entity_id}")
    print(f"{'='*60}")
    
    # Names
    print(f"\nNames:")
    for name_record in entity_data['RESOLVED_ENTITY'].get('NAME', []):
        print(f"  - {name_record['NAME_FULL']}")
    
    # Addresses
    print(f"\nAddresses:")
    for addr in entity_data['RESOLVED_ENTITY'].get('ADDRESS', []):
        print(f"  - {addr['ADDR_FULL']}")
    
    # Phones
    print(f"\nPhones:")
    for phone in entity_data['RESOLVED_ENTITY'].get('PHONE', []):
        print(f"  - {phone['PHONE_NUMBER']}")
    
    # Emails
    print(f"\nEmails:")
    for email_rec in entity_data['RESOLVED_ENTITY'].get('EMAIL', []):
        print(f"  - {email_rec['EMAIL_ADDRESS']}")
    
    # Data sources
    print(f"\nData Sources:")
    for record in entity_data['RESOLVED_ENTITY'].get('RECORDS', []):
        print(f"  - {record['DATA_SOURCE']}: {record['RECORD_ID']}")
    
    print(f"\n{'='*60}\n")
    
    # Cleanup
    engine.destroy()
    
    return entity_data

if __name__ == '__main__':
    # Example usage
    find_customer("John Smith", "john.smith@email.com")
```

### Step 4: Test Query Program

Run the query program with test cases:

```bash
python3 src/query/customer_360.py
```

Verify:
- Query returns expected results
- Output format is useful
- Performance is acceptable (< 100ms per query)
- Error handling works

### Step 5: Create UAT Test Cases

Create User Acceptance Test cases based on business requirements. See `steering/uat-framework.md` for detailed guidance.

**Quick UAT Template**:

```yaml
# docs/uat_test_cases.yaml
test_cases:
  - id: UAT-001
    scenario: Duplicate Customer Detection
    description: Verify duplicate customers are correctly identified
    test_data:
      - John Smith, 123 Main St, john@email.com
      - J. Smith, 123 Main Street, jsmith@email.com
    expected_result: Both records resolve to same entity
    acceptance_criteria: Confidence > 90%
    priority: High
    tester: jane.doe@company.com
    status: PENDING
  
  - id: UAT-002
    scenario: Different People Same Name
    description: Verify different people with same name stay separate
    test_data:
      - John Smith, 123 Main St, Boston, MA
      - John Smith, 456 Oak Ave, Seattle, WA
    expected_result: Two separate entities
    acceptance_criteria: Kept as separate entities
    priority: High
    tester: jane.doe@company.com
    status: PENDING
```

### Step 6: Execute UAT Tests

Execute each test case:

1. **Load test data** (if not already loaded)
2. **Run queries** to find test entities
3. **Compare results** to expected outcomes
4. **Document results** (PASS/FAIL)
5. **Log issues** for any failures

```python
#!/usr/bin/env python3
"""
UAT Test Executor
"""

import yaml
import json
from datetime import datetime

def execute_uat_test(test_case):
    """Execute a single UAT test case"""
    
    print(f"\nExecuting {test_case['id']}: {test_case['scenario']}")
    
    # TODO: Implement test execution logic
    # 1. Query for test data
    # 2. Verify results match expected
    # 3. Return PASS/FAIL
    
    result = {
        'test_id': test_case['id'],
        'scenario': test_case['scenario'],
        'status': 'PENDING',  # PASS, FAIL, PENDING
        'actual_result': None,
        'notes': '',
        'tester': test_case['tester'],
        'tested_date': datetime.now().isoformat()
    }
    
    return result

def run_all_uat_tests():
    """Run all UAT test cases"""
    
    # Load test cases
    with open('docs/uat_test_cases.yaml') as f:
        data = yaml.safe_load(f)
    
    results = []
    for test_case in data['test_cases']:
        result = execute_uat_test(test_case)
        results.append(result)
    
    # Generate report
    generate_uat_report(results)

def generate_uat_report(results):
    """Generate UAT results report"""
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    pending = sum(1 for r in results if r['status'] == 'PENDING')
    total = len(results)
    
    report = []
    report.append("# UAT Results Report\n\n")
    report.append("## Summary\n\n")
    report.append(f"- **Total Tests**: {total}\n")
    report.append(f"- **Passed**: {passed} ({passed/total*100:.1f}%)\n")
    report.append(f"- **Failed**: {failed} ({failed/total*100:.1f}%)\n")
    report.append(f"- **Pending**: {pending} ({pending/total*100:.1f}%)\n\n")
    
    if failed == 0 and pending == 0:
        report.append("✅ **All tests passed! Ready for production.**\n\n")
    elif failed > 0:
        report.append("❌ **Some tests failed. Issues must be resolved.**\n\n")
    else:
        report.append("⏳ **Testing in progress.**\n\n")
    
    # Write report
    with open('docs/uat_results.md', 'w') as f:
        f.writelines(report)
    
    print(f"\n✅ UAT report generated: docs/uat_results.md")

if __name__ == '__main__':
    run_all_uat_tests()
```

### Step 7: Resolve Issues

For any failed tests:

1. **Analyze failure**: Why didn't it meet expectations?
2. **Identify root cause**: Data quality? Configuration? Logic?
3. **Implement fix**: Adjust transformation, configuration, or expectations
4. **Retest**: Run test again to verify fix
5. **Document resolution**: Record what was changed

Track issues in `docs/uat_issues.yaml`:

```yaml
issues:
  - id: UAT-ISSUE-001
    test_case: UAT-001
    severity: High
    description: False negative - duplicates not matched
    root_cause: Name abbreviation not handled
    resolution: Adjusted name matching configuration
    status: Resolved
    resolved_date: 2026-03-18
```

### Step 8: Get Sign-Off

Once all tests pass, get formal sign-off from stakeholders:

```markdown
# UAT Sign-Off Document

## Project
Senzing Entity Resolution - Customer 360

## UAT Summary
- **Test Period**: March 17-20, 2026
- **Total Test Cases**: 25
- **Passed**: 25 (100%)
- **Failed**: 0 (0%)

## Acceptance Criteria Met
✅ All duplicate customers correctly identified
✅ Different people with same name kept separate
✅ Query response time < 100ms
✅ Data quality score > 85%

## Sign-Off

**Business Owner**: _________________ Date: _______

**Technical Lead**: _________________ Date: _______

**Approval for Production**: ☐ Approved ☐ Conditional ☐ Rejected
```

## User Acceptance Testing (UAT)

UAT validates that the solution meets business requirements. See `steering/uat-framework.md` for comprehensive guidance.

### UAT Process Overview

1. **Planning**: Define acceptance criteria from Module 1
2. **Test Case Creation**: Create test cases for each scenario
3. **Test Execution**: Run tests and document results
4. **Issue Resolution**: Fix any failures
5. **Sign-Off**: Get stakeholder approval

### When to Load UAT Framework

Load `steering/uat-framework.md` when:
- Starting Module 8
- User asks about UAT or testing
- Preparing for production deployment
- Need stakeholder sign-off

**Agent behavior**: Mention UAT framework in Module 8. Load full guide if user wants detailed UAT process.

## Query Examples

### Example 1: Find Duplicates

```python
def find_duplicates_for_record(data_source, record_id):
    """Find all records that resolved with this record"""
    
    entity = engine.getEntityByRecordID(data_source, record_id)
    entity_data = json.loads(entity)
    
    records = entity_data['RESOLVED_ENTITY']['RECORDS']
    
    print(f"\nEntity ID: {entity_data['RESOLVED_ENTITY']['ENTITY_ID']}")
    print(f"Total Records: {len(records)}")
    print(f"\nRecords:")
    
    for record in records:
        print(f"  - {record['DATA_SOURCE']}: {record['RECORD_ID']}")
```

### Example 2: Search for Customer

```python
def search_customer(name, phone):
    """Search for customer by name and phone"""
    
    search_attrs = {
        "NAME_FULL": name,
        "PHONE_NUMBER": phone
    }
    
    results = engine.searchByAttributes(json.dumps(search_attrs))
    results_data = json.loads(results)
    
    for entity in results_data.get('RESOLVED_ENTITIES', []):
        entity_id = entity['ENTITY']['RESOLVED_ENTITY']['ENTITY_ID']
        match_score = entity['MATCH_INFO']['MATCH_SCORE']
        print(f"Entity {entity_id}: Match Score {match_score}")
```

### Example 3: Explain Match

```python
def explain_why_matched(entity_id_1, entity_id_2):
    """Explain why two entities matched"""
    
    why = engine.whyEntities(entity_id_1, entity_id_2)
    why_data = json.loads(why)
    
    print(f"\nWhy Entities {entity_id_1} and {entity_id_2} Matched:")
    
    for match in why_data['WHY_RESULTS'][0]['MATCH_INFO']['WHY_RESULT']:
        print(f"  - {match['WHY_KEY']}: {match['WHY_RESULT']}")
```

## Validation Gates

Before proceeding to Module 9, verify:

- [ ] Query programs generated and tested
- [ ] All query types work correctly
- [ ] Query performance is acceptable (< 100ms)
- [ ] UAT test cases created
- [ ] All UAT tests executed
- [ ] All critical tests pass
- [ ] Issues documented and resolved
- [ ] Stakeholder sign-off obtained (if required)

## Success Indicators

Module 8 is complete when:

- Query programs work correctly
- UAT tests pass
- Results meet business requirements
- Stakeholders approve solution
- Ready for performance testing (Module 9) or production (if skipping 9-11)

## Common Issues

### Issue: Query Returns No Results
**Symptoms**: Search returns empty results
**Solutions**:
- Verify data was loaded successfully
- Check search attributes match loaded data
- Try broader search criteria
- Verify data source names are correct

### Issue: Too Many Results
**Symptoms**: Search returns hundreds of matches
**Solutions**:
- Add more specific search criteria
- Increase match threshold
- Use more distinguishing features

### Issue: Unexpected Matches
**Symptoms**: Records match that shouldn't
**Solutions**:
- Use `whyEntities` to understand matching logic
- Review data quality from Module 3
- Check for missing or incorrect data
- Adjust matching configuration if needed

### Issue: UAT Tests Fail
**Symptoms**: Results don't meet expectations
**Solutions**:
- Analyze root cause (data quality, configuration, expectations)
- Review transformation logic from Module 4
- Check data quality scores from Module 3
- Adjust expectations if they were unrealistic

## Integration with Other Modules

- **From Module 7**: Queries loaded data from all sources
- **From Module 6**: Queries loaded data from single source
- **From Module 1**: Validates against business requirements
- **To Module 9**: Performance testing uses query programs
- **To Module 12**: Query programs included in deployment package

## File Locations

```
project/
├── src/
│   └── query/
│       ├── customer_360.py           # Customer lookup query
│       ├── find_duplicates.py        # Duplicate detection
│       ├── fraud_detection.py        # Fraud queries
│       └── uat_executor.py           # UAT test runner
├── docs/
│   ├── uat_test_cases.yaml           # UAT test cases
│   ├── uat_results.md                # UAT results report
│   ├── uat_issues.yaml               # Issues found during UAT
│   ├── uat_signoff.md                # Sign-off document
│   └── query_specifications.md       # Query requirements
└── logs/
    └── uat_execution.log             # UAT execution log
```

## Agent Behavior

When a user is in Module 8:

1. **Review business requirements**: Load Module 1 business problem
2. **Define query requirements**: What queries are needed?
3. **Generate query programs**: Use `generate_scaffold` with `query` workflow
4. **Customize programs**: Add specific query logic
5. **Save programs**: Save to `src/query/`
6. **Test queries**: Help user run and verify queries
7. **Create UAT test cases**: Generate `docs/uat_test_cases.yaml`
8. **Execute UAT tests**: Run tests and document results
9. **Track issues**: Log any failures in `docs/uat_issues.yaml`
10. **Generate reports**: Create UAT results report
11. **Get sign-off**: Create sign-off document if needed
12. **Validate gates**: Verify all gates before proceeding

**If user asks about UAT**: Load `steering/uat-framework.md` for detailed guidance.

**If user wants to skip UAT**: Explain importance but allow skipping for non-production projects.

## Related Documentation

- `POWER.md` - Module 8 overview
- `steering/steering.md` - Detailed Module 8 workflow
- `steering/agent-instructions.md` - Agent behavior for Module 8
- `steering/uat-framework.md` - Comprehensive UAT guidance (load on demand)
- `steering/testing-strategy.md` - Overall testing approach

## Version History

- **v3.0.0** (2026-03-17): Module 8 refocused on query and validation with UAT framework enhancement

