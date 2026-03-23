---
inclusion: always
---

# Data Source Complexity Estimator

Estimate time and effort based on data characteristics.

## Quick Complexity Assessment

Answer these questions for each data source to estimate complexity:

### 1. Data Format
- ✅ **Simple** (1 point): CSV, JSON, single table
- ⚠️ **Medium** (2 points): Multiple tables, XML, API
- 🔴 **Complex** (3 points): Nested JSON, multiple APIs, real-time streams

### 2. Data Volume
- ✅ **Small** (1 point): < 10,000 records
- ⚠️ **Medium** (2 points): 10,000 - 100,000 records
- 🔴 **Large** (3 points): > 100,000 records

### 3. Data Quality
- ✅ **Good** (1 point): Clean, consistent, few nulls
- ⚠️ **Fair** (2 points): Some inconsistencies, moderate nulls
- 🔴 **Poor** (3 points): Messy, inconsistent formats, many nulls

### 4. Field Mapping
- ✅ **Direct** (1 point): Fields map 1:1 to SGES
- ⚠️ **Moderate** (2 points): Some field combinations needed
- 🔴 **Complex** (3 points): Extensive transformation, parsing, lookups

### 5. Entity Structure
- ✅ **Simple** (1 point): Flat records, one entity type
- ⚠️ **Moderate** (2 points): Some nested data, 2 entity types
- 🔴 **Complex** (3 points): Hierarchical, relationships, multiple types

### 6. Data Access
- ✅ **Easy** (1 point): Local file, direct database access
- ⚠️ **Moderate** (2 points): API with good docs, VPN required
- 🔴 **Difficult** (3 points): Complex API, authentication issues, rate limits

## Complexity Score

Add up the points:

### 6-9 Points: Low Complexity ✅
**Estimated Time**: 1-2 hours for Module 4
**Characteristics**:
- Simple CSV or JSON file
- Clean, well-structured data
- Direct field mappings
- Small to medium volume

**Example**: Customer CSV with columns that map directly to NAME_FULL, ADDR_FULL, PHONE_NUMBER

**Approach**:
- Use mapping_workflow for quick mapping
- Minimal data cleansing needed
- Test with 100 records
- Should complete in one session

### 10-14 Points: Medium Complexity ⚠️
**Estimated Time**: 2-4 hours for Module 4
**Characteristics**:
- Multiple tables or moderate API
- Some data quality issues
- Field combinations needed
- Medium to large volume

**Example**: Database with separate name, address, phone tables that need joining

**Approach**:
- Plan entity structure carefully
- Add data cleansing logic
- Test incrementally (100, 1000, 10000 records)
- May need multiple iterations
- Consider data quality improvements

### 15-18 Points: High Complexity 🔴
**Estimated Time**: 4-8 hours for Module 4
**Characteristics**:
- Complex nested data or difficult API
- Poor data quality
- Extensive transformation needed
- Large volume or real-time

**Example**: Nested JSON from API with inconsistent formats, missing data, and complex relationships

**Approach**:
- Break into smaller sub-tasks
- Focus on data quality first
- Consider data enrichment
- May need custom utilities
- Plan for multiple iterations
- Consider phased approach (subset first)

## Detailed Estimator

### Module 4: Data Mapping Time Estimate

```
Base Time: 1 hour

+ Data Format Complexity:
  • Simple format: +0 hours
  • Medium format: +0.5 hours
  • Complex format: +1 hour

+ Data Volume:
  • < 10K records: +0 hours
  • 10K-100K records: +0.5 hours
  • > 100K records: +1 hour

+ Data Quality:
  • Good quality: +0 hours
  • Fair quality: +0.5 hours
  • Poor quality: +1-2 hours

+ Field Mapping:
  • Direct mapping: +0 hours
  • Moderate mapping: +0.5 hours
  • Complex mapping: +1-2 hours

+ Testing & Iteration:
  • First try works: +0 hours
  • 1-2 iterations: +0.5 hours
  • 3+ iterations: +1-2 hours

Total: Sum all components
```

### Module 6: Loading Time Estimate

```
Base Time: 30 minutes

+ Data Volume:
  • < 10K records: +0 minutes
  • 10K-100K records: +30 minutes
  • 100K-1M records: +2 hours
  • > 1M records: +4-8 hours

+ Database Type:
  • SQLite: +0 (but slow for >100K)
  • PostgreSQL: +0 (faster)

+ Error Rate:
  • < 1% errors: +0
  • 1-5% errors: +30 minutes (investigation)
  • > 5% errors: +1-2 hours (fix and reload)

Total: Sum all components
```

## Complexity Factors Detail

### Data Format Complexity

**Simple (1 point)**:
- Single CSV file
- Flat JSON (one object per record)
- Single database table
- Well-documented structure

**Medium (2 points)**:
- Multiple related tables
- XML with moderate nesting
- REST API with pagination
- Some documentation gaps

**Complex (3 points)**:
- Deeply nested JSON/XML
- Multiple APIs to combine
- Real-time streaming data
- GraphQL with complex queries
- Poor or no documentation

### Data Quality Issues

**Good (1 point)**:
- < 5% null values in key fields
- Consistent formats
- Valid data types
- Few duplicates within source

**Fair (2 points)**:
- 5-20% null values
- Some format inconsistencies
- Occasional invalid data
- Moderate duplicates

**Poor (3 points)**:
- > 20% null values
- Highly inconsistent formats
- Many invalid values
- Extensive duplicates
- Mixed data types in fields

### Field Mapping Complexity

**Direct (1 point)**:
- Fields already named like SGES
- One source field → one SGES attribute
- No parsing or transformation needed
- Example: "full_name" → NAME_FULL

**Moderate (2 points)**:
- Combine multiple fields
- Some parsing needed
- Conditional logic
- Example: "first_name" + "last_name" → NAME_FULL

**Complex (3 points)**:
- Extensive parsing (addresses, names)
- Lookups or enrichment needed
- Complex conditional logic
- Multiple entity types
- Example: Parse "123 Main St, Apt 4B, Springfield, IL 62701" into separate ADDR fields

## Risk Factors

Add extra time for these risk factors:

### High Risk (+1-2 hours each)
- 🔴 No sample data available
- 🔴 Data owner unavailable for questions
- 🔴 Tight deadline pressure
- 🔴 Production system (can't test freely)
- 🔴 Compliance requirements (PII, HIPAA, etc.)
- 🔴 First time using Senzing

### Medium Risk (+0.5-1 hour each)
- ⚠️ Limited sample data (< 100 records)
- ⚠️ Unclear business requirements
- ⚠️ Multiple stakeholders
- ⚠️ Legacy system with poor docs
- ⚠️ Data access restrictions

## Optimization Strategies

### For High Complexity Sources

1. **Phased Approach**
   - Start with subset of fields
   - Add complexity incrementally
   - Validate at each step

2. **Data Quality First**
   - Clean data before mapping
   - Fix source data if possible
   - Document quality issues

3. **Parallel Processing**
   - Map multiple sources simultaneously
   - Different team members per source
   - Share learnings across sources

4. **Tooling**
   - Build reusable utilities
   - Create data quality scripts
   - Automate repetitive tasks

### For Large Volume Sources

1. **Sampling Strategy**
   - Test with 100 records
   - Then 1,000 records
   - Then 10,000 records
   - Finally full dataset

2. **Performance Optimization**
   - Use batch processing
   - Optimize database queries
   - Consider parallel loading

3. **Monitoring**
   - Track progress
   - Monitor error rates
   - Watch system resources

## Example Assessments

### Example 1: Simple Customer CSV
- Format: CSV (1 point)
- Volume: 5,000 records (1 point)
- Quality: Clean (1 point)
- Mapping: Direct (1 point)
- Structure: Flat (1 point)
- Access: Local file (1 point)
**Total: 6 points - Low Complexity**
**Estimate: 1-2 hours**

### Example 2: CRM Database
- Format: Multiple tables (2 points)
- Volume: 50,000 records (2 points)
- Quality: Fair (2 points)
- Mapping: Moderate (2 points)
- Structure: Some nesting (2 points)
- Access: Database (1 point)
**Total: 11 points - Medium Complexity**
**Estimate: 2-4 hours**

### Example 3: Legacy System API
- Format: Complex API (3 points)
- Volume: 200,000 records (3 points)
- Quality: Poor (3 points)
- Mapping: Complex (3 points)
- Structure: Hierarchical (3 points)
- Access: Difficult API (3 points)
**Total: 18 points - High Complexity**
**Estimate: 4-8 hours**

## When to Load This Guide

Load this steering file when:
- Starting Module 1 (planning)
- User asks "how long will this take?"
- Evaluating multiple data sources
- Prioritizing which sources to map first
- Setting project timelines
- Managing stakeholder expectations
