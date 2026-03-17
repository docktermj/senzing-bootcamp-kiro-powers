# New Workflows for Phase 5

These workflows need to be added to steering.md after the existing Module 6 workflow and before the old Module 7 workflow (which becomes Module 8).

## Workflow: Multi-Source Orchestration (Module 7)

Use this workflow after loading at least one data source successfully (Module 6). The goal is to orchestrate loading of multiple data sources with proper dependency management, error handling, and progress tracking.

**Time**: 1-2 hours

**Prerequisites**: ✅ Module 6 complete (at least one data source loaded successfully)

**Purpose**: Manage loading of multiple data sources with dependencies, optimize load order, implement parallel loading where appropriate, and handle errors across sources.

### Step 1: Assess Multi-Source Requirements

1. **Review all data sources**: List all data sources from Module 2 that need to be loaded:
   - Which sources are already loaded (from Module 6)?
   - Which sources are pending?
   - How many total sources need orchestration?

2. **Identify dependencies**: Determine if there are dependencies between data sources:
   - **Reference data first**: Lookup tables, code tables, master data
   - **Parent before child**: Organizations before employees, customers before orders
   - **No dependencies**: Sources that can load in any order or in parallel

3. **Estimate data volumes**: For each source:
   - Record count
   - File size
   - Expected loading time (based on Module 6 experience)

### Step 2: Define Load Order

1. **Create dependency graph**: Document which sources must load before others:
   ```markdown
   Load Order:
   1. Reference Data (no dependencies)
      - Country codes
      - Product categories
   
   2. Master Data (depends on reference data)
      - Organizations
      - Locations
   
   3. Transactional Data (depends on master data)
      - Customers
      - Orders
      - Transactions
   ```

2. **Identify parallel opportunities**: Which sources can load simultaneously?
   - Sources with no dependencies can load in parallel
   - Sources in different dependency chains can load in parallel
   - Balance parallelism with system resources

3. **Document load strategy** in `docs/load_strategy.md`:
   ```markdown
   # Multi-Source Loading Strategy
   
   ## Load Order
   
   ### Phase 1: Reference Data (Parallel)
   - Country codes (5K records, ~30 seconds)
   - Product categories (2K records, ~15 seconds)
   
   ### Phase 2: Master Data (Sequential)
   - Organizations (50K records, ~5 minutes)
   - Locations (100K records, ~10 minutes)
   
   ### Phase 3: Transactional Data (Parallel)
   - Customers (500K records, ~45 minutes)
   - Orders (1M records, ~90 minutes)
   
   ## Total Estimated Time
   - Sequential: ~2.5 hours
   - With parallelism: ~1.5 hours
   
   ## Dependencies
   - Customers depend on Organizations
   - Orders depend on Customers
   ```

### Step 3: Create Orchestration Script

1. **Design orchestration approach**:
   - **Simple sequential**: Load sources one at a time
   - **Parallel batches**: Load independent sources in parallel
   - **Dynamic orchestration**: Adjust based on success/failure

2. **Create orchestration script** in `src/load/orchestrate_loading.py`:
   
   ```python
   #!/usr/bin/env python3
   """
   Multi-Source Loading Orchestration
   Manages loading of multiple data sources with dependencies
   """
   
   import json
   import time
   import logging
   from concurrent.futures import ThreadPoolExecutor, as_completed
   from typing import List, Dict
   from senzing import SzEngine
   
   # Configure logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(levelname)s - %(message)s'
   )
   logger = logging.getLogger(__name__)
   
   class LoadOrchestrator:
       def __init__(self, config_path='config/engine_config.json'):
           self.config_path = config_path
           self.results = {}
       
       def load_source(self, source_config: Dict) -> Dict:
           """Load a single data source"""
           source_name = source_config['name']
           input_file = source_config['file']
           data_source_code = source_config['data_source']
           
           logger.info(f"Starting load: {source_name}")
           start_time = time.time()
           
           try:
               # Initialize engine
               engine = SzEngine()
               with open(self.config_path) as f:
                   config = json.load(f)
               engine.initialize(instance_name=f'loader_{source_name}', settings=json.dumps(config))
               
               # Load records
               success_count = 0
               error_count = 0
               
               with open(input_file) as f:
                   for line_num, line in enumerate(f, 1):
                       try:
                           record = json.loads(line)
                           engine.addRecord(
                               data_source_code,
                               record['RECORD_ID'],
                               json.dumps(record)
                           )
                           success_count += 1
                           
                           if success_count % 1000 == 0:
                               logger.info(f"{source_name}: {success_count:,} records loaded")
                       
                       except Exception as e:
                           error_count += 1
                           if error_count <= 10:  # Log first 10 errors
                               logger.error(f"{source_name} error on line {line_num}: {e}")
               
               engine.destroy()
               
               duration = time.time() - start_time
               throughput = success_count / duration if duration > 0 else 0
               
               result = {
                   'source': source_name,
                   'status': 'success',
                   'records_loaded': success_count,
                   'errors': error_count,
                   'duration': duration,
                   'throughput': throughput
               }
               
               logger.info(f"✅ {source_name} complete: {success_count:,} records in {duration:.1f}s ({throughput:.0f} rec/s)")
               return result
           
           except Exception as e:
               duration = time.time() - start_time
               result = {
                   'source': source_name,
                   'status': 'failed',
                   'error': str(e),
                   'duration': duration
               }
               logger.error(f"❌ {source_name} failed: {e}")
               return result
       
       def load_sequential(self, sources: List[Dict]):
           """Load sources sequentially"""
           logger.info(f"Loading {len(sources)} sources sequentially...")
           
           for source in sources:
               result = self.load_source(source)
               self.results[source['name']] = result
               
               if result['status'] == 'failed':
                   logger.warning(f"Source {source['name']} failed, continuing with next source")
       
       def load_parallel(self, sources: List[Dict], max_workers=3):
           """Load sources in parallel"""
           logger.info(f"Loading {len(sources)} sources in parallel (max {max_workers} workers)...")
           
           with ThreadPoolExecutor(max_workers=max_workers) as executor:
               future_to_source = {
                   executor.submit(self.load_source, source): source
                   for source in sources
               }
               
               for future in as_completed(future_to_source):
                   source = future_to_source[future]
                   try:
                       result = future.result()
                       self.results[source['name']] = result
                   except Exception as e:
                       logger.error(f"Exception loading {source['name']}: {e}")
                       self.results[source['name']] = {
                           'source': source['name'],
                           'status': 'failed',
                           'error': str(e)
                       }
       
       def orchestrate(self, load_plan: Dict):
           """Execute complete load plan"""
           logger.info("="*60)
           logger.info("MULTI-SOURCE LOADING ORCHESTRATION")
           logger.info("="*60)
           
           overall_start = time.time()
           
           for phase_name, phase_config in load_plan.items():
               logger.info(f"\n--- {phase_name} ---")
               
               sources = phase_config['sources']
               parallel = phase_config.get('parallel', False)
               max_workers = phase_config.get('max_workers', 3)
               
               if parallel:
                   self.load_parallel(sources, max_workers)
               else:
                   self.load_sequential(sources)
           
           overall_duration = time.time() - overall_start
           
           # Generate summary
           self.print_summary(overall_duration)
       
       def print_summary(self, total_duration: float):
           """Print loading summary"""
           logger.info("\n" + "="*60)
           logger.info("LOADING SUMMARY")
           logger.info("="*60)
           
           total_records = 0
           total_errors = 0
           successful_sources = 0
           failed_sources = 0
           
           for source_name, result in self.results.items():
               status_icon = "✅" if result['status'] == 'success' else "❌"
               logger.info(f"{status_icon} {source_name}: {result.get('records_loaded', 0):,} records")
               
               if result['status'] == 'success':
                   successful_sources += 1
                   total_records += result.get('records_loaded', 0)
                   total_errors += result.get('errors', 0)
               else:
                   failed_sources += 1
           
           logger.info(f"\nTotal Sources: {len(self.results)}")
           logger.info(f"Successful: {successful_sources}")
           logger.info(f"Failed: {failed_sources}")
           logger.info(f"Total Records Loaded: {total_records:,}")
           logger.info(f"Total Errors: {total_errors:,}")
           logger.info(f"Total Duration: {total_duration:.1f} seconds")
           logger.info(f"Overall Throughput: {total_records/total_duration:.0f} records/second")
           logger.info("="*60)
   
   # Example load plan
   LOAD_PLAN = {
       'Phase 1: Reference Data': {
           'sources': [
               {
                   'name': 'Country Codes',
                   'file': 'data/transformed/country_codes.jsonl',
                   'data_source': 'REFERENCE_DATA'
               },
               {
                   'name': 'Product Categories',
                   'file': 'data/transformed/product_categories.jsonl',
                   'data_source': 'REFERENCE_DATA'
               }
           ],
           'parallel': True,
           'max_workers': 2
       },
       'Phase 2: Master Data': {
           'sources': [
               {
                   'name': 'Organizations',
                   'file': 'data/transformed/organizations.jsonl',
                   'data_source': 'ORGANIZATIONS'
               },
               {
                   'name': 'Locations',
                   'file': 'data/transformed/locations.jsonl',
                   'data_source': 'LOCATIONS'
               }
           ],
           'parallel': False  # Sequential due to dependencies
       },
       'Phase 3: Transactional Data': {
           'sources': [
               {
                   'name': 'Customers',
                   'file': 'data/transformed/customers.jsonl',
                   'data_source': 'CUSTOMERS'
               },
               {
                   'name': 'Orders',
                   'file': 'data/transformed/orders.jsonl',
                   'data_source': 'ORDERS'
               }
           ],
           'parallel': True,
           'max_workers': 2
       }
   }
   
   if __name__ == '__main__':
       orchestrator = LoadOrchestrator()
       orchestrator.orchestrate(LOAD_PLAN)
   ```

3. **Customize for user's sources**: Adapt the load plan to match their specific data sources and dependencies.

### Step 4: Implement Error Handling

1. **Per-source error handling**:
   - Continue loading other sources if one fails
   - Log errors for later review
   - Track which sources succeeded and which failed

2. **Retry logic** (optional):
   ```python
   def load_source_with_retry(self, source_config: Dict, max_retries=3) -> Dict:
       """Load source with retry logic"""
       for attempt in range(max_retries):
           result = self.load_source(source_config)
           if result['status'] == 'success':
               return result
           logger.warning(f"Retry {attempt + 1}/{max_retries} for {source_config['name']}")
           time.sleep(60)  # Wait before retry
       return result
   ```

3. **Rollback strategy**: Document what to do if critical sources fail:
   - Can you continue without this source?
   - Should you rollback all sources?
   - Can you reload just the failed source later?

### Step 5: Add Progress Tracking

1. **Create progress dashboard** (optional):
   ```python
   def create_progress_dashboard(self):
       """Generate HTML progress dashboard"""
       html = f"""
       <html>
       <head><title>Loading Progress</title></head>
       <body>
       <h1>Multi-Source Loading Progress</h1>
       <table border="1">
       <tr><th>Source</th><th>Status</th><th>Records</th><th>Duration</th></tr>
       """
       
       for source_name, result in self.results.items():
           status = result.get('status', 'pending')
           records = result.get('records_loaded', 0)
           duration = result.get('duration', 0)
           
           html += f"""
           <tr>
           <td>{source_name}</td>
           <td>{status}</td>
           <td>{records:,}</td>
           <td>{duration:.1f}s</td>
           </tr>
           """
       
       html += "</table></body></html>"
       
       with open('logs/loading_progress.html', 'w') as f:
           f.write(html)
   ```

2. **Real-time logging**: Ensure logs show progress for each source

3. **Notification on completion** (optional):
   - Email notification
   - Slack message
   - Dashboard update

### Step 6: Test Orchestration

1. **Test with sample data first**:
   - Use small subsets of each source
   - Verify load order is correct
   - Check error handling works
   - Validate progress tracking

2. **Test failure scenarios**:
   - What happens if one source fails?
   - Can you recover and continue?
   - Are errors logged properly?

3. **Test parallel loading**:
   - Verify sources load simultaneously
   - Check for resource contention
   - Monitor system performance

### Step 7: Run Full Orchestration

1. **Backup database** before starting (see `steering/disaster-recovery.md`)

2. **Run orchestration script**:
   ```bash
   python src/load/orchestrate_loading.py
   ```

3. **Monitor progress**:
   - Watch logs for errors
   - Check system resources (CPU, memory, disk I/O)
   - Verify records are being loaded

4. **Review results**:
   - Check summary statistics
   - Verify all sources loaded successfully
   - Review any errors

### Step 8: Validate Multi-Source Results

1. **Check entity counts**:
   ```python
   # Get counts per data source
   stats = engine.getStats()
   print(json.dumps(stats, indent=2))
   ```

2. **Verify cross-source matching**:
   - Query for entities that span multiple sources
   - Verify relationships are correct
   - Check that dependencies were respected

3. **Review data quality**:
   - Are match rates as expected?
   - Any unexpected entity merges?
   - Data quality issues across sources?

### Step 9: Document Orchestration

1. **Update `docs/load_strategy.md`** with:
   - Actual load times
   - Any issues encountered
   - Lessons learned
   - Recommendations for future loads

2. **Save orchestration results**:
   ```bash
   cp logs/loading_progress.html docs/loading_results_$(date +%Y%m%d).html
   ```

3. **Document for operations**:
   - How to run orchestration
   - What to monitor
   - How to handle failures
   - When to reload sources

### Transition to Module 8

Once all sources are loaded successfully:

1. **Verify all sources present**:
   ```python
   # List all data sources
   config = engine.getActiveConfig()
   data_sources = config['G2_CONFIG']['CFG_DSRC']
   for ds in data_sources:
       print(f"- {ds['DSRC_CODE']}: {ds['DSRC_DESC']}")
   ```

2. **Check entity resolution statistics**:
   - Total entities created
   - Match rate across sources
   - Relationship counts

3. **Proceed to Module 8**: "Great! All data sources are loaded. Now let's create query programs to explore the results and validate they meet your business requirements."

**Success indicator**: ✅ All data sources loaded + orchestration script created + progress tracked + results documented

**Agent behavior**:
- Help identify dependencies between sources
- Create appropriate load order
- Implement error handling for each source
- Track progress across all sources
- Validate multi-source results

## Workflow: Query and Validate Results with UAT (Module 8)

This workflow replaces the old "Module 7: Query Results" workflow. Use this after all data sources are loaded (Modules 6-7).

**Time**: 1-2 hours

**Prerequisites**: ✅ Module 7 complete (all sources loaded) OR Module 6 complete (single source loaded)

**Purpose**: Create query programs to answer business questions and validate results through User Acceptance Testing (UAT).

### Step 1: Review Business Requirements

1. **Review Module 1**: Go back to `docs/business_problem.md` and review:
   - What problem was the user trying to solve?
   - What were their success criteria?
   - What questions need to be answered?

2. **Define query requirements**: Based on the business problem, list specific queries needed:
   - "Find all duplicate customers"
   - "Search for a person by name and address"
   - "Get complete customer 360 view"
   - "Identify potential fraud rings"
   - "Export master customer list"

3. **Prioritize queries**: Which queries are most critical for validating the solution?

### Step 2: Create Query Programs

1. **For each query requirement**, create a dedicated program in `src/query/`:

   **Example: Customer 360 Query**
   ```python
   #!/usr/bin/env python3
   """
   Customer 360 Query
   Find complete customer profile by name and email
   """
   
   import json
   from senzing import SzEngine, SzEngineFlags
   
   def find_customer(name, email):
       """Find customer entity by name and email"""
       
       engine = SzEngine()
       engine.initialize(instance_name='query', settings=ENGINE_CONFIG)
       
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
       
       # Get first match
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
       
       # Display details
       print(f"\nNames:")
       for name_record in entity_data['RESOLVED_ENTITY'].get('NAME', []):
           print(f"  - {name_record['NAME_FULL']}")
       
       print(f"\nAddresses:")
       for addr in entity_data['RESOLVED_ENTITY'].get('ADDRESS', []):
           print(f"  - {addr['ADDR_FULL']}")
       
       print(f"\nPhones:")
       for phone in entity_data['RESOLVED_ENTITY'].get('PHONE', []):
           print(f"  - {phone['PHONE_NUMBER']}")
       
       print(f"\nEmails:")
       for email_rec in entity_data['RESOLVED_ENTITY'].get('EMAIL', []):
           print(f"  - {email_rec['EMAIL_ADDRESS']}")
       
       print(f"\nData Sources:")
       for record in entity_data['RESOLVED_ENTITY'].get('RECORDS', []):
           print(f"  - {record['DATA_SOURCE']}: {record['RECORD_ID']}")
       
       print(f"\n{'='*60}\n")
       
       engine.destroy()
       return entity_data
   
   if __name__ == '__main__':
       find_customer("John Smith", "john.smith@email.com")
   ```

2. **Use MCP tools for code generation**:
   - Call `generate_scaffold` with workflow `query` for query code
   - Call `get_sdk_reference` with topic `functions` for method signatures
   - Call `get_sdk_reference` with topic `flags` for flag definitions

3. **Save each query program** in `src/query/` with descriptive names

### Step 3: Test Query Programs

1. **Run each query program** with test data:
   - Verify it returns expected results
   - Check output format is useful
   - Test error handling

2. **Review results with user**:
   - Do the results make sense?
   - Are there unexpected matches or non-matches?
   - Is the data quality sufficient?

3. **Investigate unexpected results**:
   - Use `whyEntities` to understand why records matched
   - Use `howEntityByEntityID` to see how entity was built
   - Review data quality from Module 3

### Step 4: Create UAT Test Cases

See `steering/uat-framework.md` for comprehensive UAT guidance.

1. **Define acceptance criteria** from Module 1 business requirements

2. **Create test cases** in `docs/uat_test_cases.yaml`:
   ```yaml
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

3. **Create UAT executor** in `src/testing/uat_executor.py` (see `steering/uat-framework.md` for complete example)

### Step 5: Execute UAT Tests

1. **Run UAT test cases**:
   ```bash
   python src/testing/uat_executor.py
   ```

2. **Document results** for each test:
   - PASS: Result matches expected outcome
   - FAIL: Result doesn't match expected outcome
   - PENDING: Not yet tested

3. **Track issues** in `docs/uat_issues.yaml`:
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

### Step 6: Resolve Issues

1. **For each failed test**:
   - Analyze why it failed
   - Identify root cause (data quality, configuration, expectations)
   - Implement fix
   - Retest

2. **Common resolutions**:
   - Improve data quality (go back to Module 3/4)
   - Adjust transformation logic (Module 4)
   - Tune matching configuration
   - Adjust expectations (if unrealistic)

### Step 7: Get Stakeholder Sign-Off

1. **Generate UAT report**:
   ```bash
   python src/testing/uat_executor.py --generate-report
   ```

2. **Create sign-off document** in `docs/uat_signoff.md`:
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

3. **Get formal approval** from stakeholders before proceeding to production

### Step 8: Document Query Specifications

1. **Create `docs/query_specifications.md`**:
   ```markdown
   # Query Specifications
   
   ## Customer 360 Query
   **Purpose**: Find complete customer profile
   **Input**: Name, email
   **Output**: Entity with all attributes and source records
   **Program**: `src/query/customer_360.py`
   **Usage**: `python src/query/customer_360.py "John Smith" "john@email.com"`
   
   ## Duplicate Detection Query
   **Purpose**: Find all duplicate records
   **Input**: Data source code
   **Output**: List of entities with multiple records
   **Program**: `src/query/find_duplicates.py`
   **Usage**: `python src/query/find_duplicates.py CUSTOMERS`
   ```

### Transition to Module 9

Once UAT is complete and stakeholders have signed off:

1. **If deploying to production**: Proceed to Module 9 (Performance Testing)
2. **If not deploying to production**: Boot camp complete! User has working solution.

**Success indicator**: ✅ Query programs created + UAT tests passed + Stakeholder sign-off obtained

**Agent behavior**:
- Create query programs tailored to business requirements
- Guide UAT test case creation
- Help execute and document UAT results
- Assist with issue resolution
- Obtain stakeholder sign-off before production


## Workflow: Performance Testing and Benchmarking (Module 9)

Use this workflow after query validation (Module 8) and before production deployment. The goal is to test performance and scalability to ensure the solution meets production requirements.

**Time**: 1-2 hours

**Prerequisites**: ✅ Module 8 complete (queries working, UAT passed)

**Purpose**: Benchmark transformation, loading, and query performance; test scalability; identify bottlenecks; validate production readiness.

### Step 1: Define Performance Requirements

1. **Review business requirements**: What are the performance expectations?
   - Transformation throughput: Records per second
   - Loading throughput: Records per second
   - Query response time: Milliseconds
   - Concurrent users: Number of simultaneous queries
   - Data volume: Total records in production

2. **Set performance targets**:
   ```markdown
   Performance Targets:
   - Transformation: > 1,000 records/second
   - Loading: > 100 records/second
   - Query response: < 100ms (95th percentile)
   - Concurrent queries: 50 simultaneous users
   - Data volume: 10M records
   ```

3. **Identify critical paths**: Which operations are most important?
   - Real-time queries (highest priority)
   - Batch loading (medium priority)
   - Transformation (can be offline)

### Step 2: Benchmark Transformation Performance

1. **Create benchmark script** in `src/testing/benchmark_transform.py`:
   ```python
   #!/usr/bin/env python3
   """
   Benchmark transformation performance
   """
   
   import time
   import json
   from pathlib import Path
   
   def benchmark_transformation(transformer, input_file, sample_size=10000):
       """Benchmark transformation performance"""
       
       print(f"Benchmarking transformation with {sample_size:,} records...")
       
       records_processed = 0
       start_time = time.time()
       
       with open(input_file) as f:
           for line in f:
               if records_processed >= sample_size:
                   break
               
               source_record = json.loads(line)
               senzing_record = transformer.transform(source_record)
               records_processed += 1
       
       duration = time.time() - start_time
       throughput = records_processed / duration if duration > 0 else 0
       
       print(f"\nTransformation Benchmark Results:")
       print(f"  Records: {records_processed:,}")
       print(f"  Duration: {duration:.2f} seconds")
       print(f"  Throughput: {throughput:.0f} records/second")
       
       return {
           'records': records_processed,
           'duration': duration,
           'throughput': throughput
       }
   ```

2. **Run benchmarks** with different data volumes:
   - 1K records (quick test)
   - 10K records (standard test)
   - 100K records (scale test)

3. **Document results** in `docs/performance_report.md`

### Step 3: Benchmark Loading Performance

1. **Create benchmark script** in `src/testing/benchmark_loading.py`:
   ```python
   #!/usr/bin/env python3
   """
   Benchmark loading performance
   """
   
   import time
   import json
   from senzing import SzEngine
   
   def benchmark_loading(input_file, data_source, sample_size=10000):
       """Benchmark loading performance"""
       
       print(f"Benchmarking loading with {sample_size:,} records...")
       
       engine = SzEngine()
       engine.initialize(instance_name='benchmark', settings=ENGINE_CONFIG)
       
       records_loaded = 0
       start_time = time.time()
       
       with open(input_file) as f:
           for line in f:
               if records_loaded >= sample_size:
                   break
               
               record = json.loads(line)
               engine.addRecord(
                   data_source,
                   record['RECORD_ID'],
                   json.dumps(record)
               )
               records_loaded += 1
               
               if records_loaded % 1000 == 0:
                   elapsed = time.time() - start_time
                   current_throughput = records_loaded / elapsed
                   print(f"  {records_loaded:,} records ({current_throughput:.0f} rec/s)")
       
       duration = time.time() - start_time
       throughput = records_loaded / duration if duration > 0 else 0
       
       engine.destroy()
       
       print(f"\nLoading Benchmark Results:")
       print(f"  Records: {records_loaded:,}")
       print(f"  Duration: {duration:.2f} seconds")
       print(f"  Throughput: {throughput:.0f} records/second")
       
       return {
           'records': records_loaded,
           'duration': duration,
           'throughput': throughput
       }
   ```

2. **Test with different configurations**:
   - SQLite vs PostgreSQL
   - Different batch sizes
   - With/without indexes

3. **Identify bottlenecks**:
   - CPU bound?
   - I/O bound?
   - Database bound?

### Step 4: Benchmark Query Performance

1. **Create benchmark script** in `src/testing/benchmark_queries.py`:
   ```python
   #!/usr/bin/env python3
   """
   Benchmark query performance
   """
   
   import time
   import json
   import statistics
   from senzing import SzEngine, SzEngineFlags
   
   def benchmark_query(query_func, iterations=100):
       """Benchmark a query function"""
       
       print(f"Benchmarking query with {iterations} iterations...")
       
       engine = SzEngine()
       engine.initialize(instance_name='benchmark', settings=ENGINE_CONFIG)
       
       response_times = []
       
       for i in range(iterations):
           start = time.time()
           query_func(engine)
           duration = (time.time() - start) * 1000  # Convert to ms
           response_times.append(duration)
           
           if (i + 1) % 10 == 0:
               print(f"  {i + 1}/{iterations} queries complete")
       
       engine.destroy()
       
       # Calculate statistics
       avg_time = statistics.mean(response_times)
       median_time = statistics.median(response_times)
       p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
       p99_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
       min_time = min(response_times)
       max_time = max(response_times)
       
       print(f"\nQuery Benchmark Results:")
       print(f"  Iterations: {iterations}")
       print(f"  Average: {avg_time:.2f} ms")
       print(f"  Median: {median_time:.2f} ms")
       print(f"  95th percentile: {p95_time:.2f} ms")
       print(f"  99th percentile: {p99_time:.2f} ms")
       print(f"  Min: {min_time:.2f} ms")
       print(f"  Max: {max_time:.2f} ms")
       
       return {
           'iterations': iterations,
           'avg': avg_time,
           'median': median_time,
           'p95': p95_time,
           'p99': p99_time,
           'min': min_time,
           'max': max_time
       }
   
   # Example query functions
   def search_by_name(engine):
       search_attrs = {"NAME_FULL": "John Smith"}
       engine.searchByAttributes(json.dumps(search_attrs))
   
   def get_entity_by_id(engine):
       engine.getEntityByEntityID(12345)
   ```

2. **Test different query types**:
   - Search by attributes
   - Get entity by ID
   - Get entity by record ID
   - Why entities
   - Find path

3. **Test concurrent queries**:
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   def benchmark_concurrent_queries(query_func, concurrent_users=10, queries_per_user=10):
       """Benchmark concurrent query performance"""
       
       def user_queries():
           for _ in range(queries_per_user):
               query_func()
       
       start = time.time()
       
       with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
           futures = [executor.submit(user_queries) for _ in range(concurrent_users)]
           for future in futures:
               future.result()
       
       duration = time.time() - start
       total_queries = concurrent_users * queries_per_user
       throughput = total_queries / duration
       
       print(f"\nConcurrent Query Results:")
       print(f"  Concurrent users: {concurrent_users}")
       print(f"  Queries per user: {queries_per_user}")
       print(f"  Total queries: {total_queries}")
       print(f"  Duration: {duration:.2f} seconds")
       print(f"  Throughput: {throughput:.1f} queries/second")
   ```

### Step 5: Profile Resource Utilization

1. **Monitor system resources** during benchmarks:
   ```python
   import psutil
   
   def monitor_resources(duration=60):
       """Monitor system resources"""
       
       print(f"Monitoring resources for {duration} seconds...")
       
       cpu_samples = []
       memory_samples = []
       
       start = time.time()
       while time.time() - start < duration:
           cpu_samples.append(psutil.cpu_percent(interval=1))
           memory_samples.append(psutil.virtual_memory().percent)
       
       print(f"\nResource Utilization:")
       print(f"  CPU: {statistics.mean(cpu_samples):.1f}% (avg), {max(cpu_samples):.1f}% (max)")
       print(f"  Memory: {statistics.mean(memory_samples):.1f}% (avg), {max(memory_samples):.1f}% (max)")
   ```

2. **Check database performance**:
   - Connection pool usage
   - Query execution times
   - Index usage
   - Lock contention

3. **Identify resource bottlenecks**:
   - CPU saturation?
   - Memory pressure?
   - Disk I/O limits?
   - Network bandwidth?

### Step 6: Test Scalability

1. **Test with increasing data volumes**:
   - 10K records
   - 100K records
   - 1M records
   - 10M records (if feasible)

2. **Measure performance degradation**:
   - Does throughput decrease with volume?
   - Do query times increase?
   - At what point does performance become unacceptable?

3. **Project production performance**:
   ```python
   def project_production_performance(benchmark_results, production_volume):
       """Project production performance based on benchmarks"""
       
       # Linear extrapolation (simplified)
       benchmark_volume = benchmark_results['records']
       benchmark_duration = benchmark_results['duration']
       
       projected_duration = (production_volume / benchmark_volume) * benchmark_duration
       projected_hours = projected_duration / 3600
       
       print(f"\nProduction Performance Projection:")
       print(f"  Production volume: {production_volume:,} records")
       print(f"  Projected duration: {projected_hours:.1f} hours")
       print(f"  Projected throughput: {production_volume/projected_duration:.0f} rec/s")
   ```

### Step 7: Generate Performance Report

1. **Create comprehensive report** in `docs/performance_report.md`:
   ```markdown
   # Performance Testing Report
   
   **Date**: 2026-03-17
   **Environment**: PostgreSQL 15, 8 vCPU, 32GB RAM
   
   ## Summary
   
   All performance targets met ✅
   
   ## Transformation Performance
   
   | Data Volume | Duration | Throughput |
   |-------------|----------|------------|
   | 1K records  | 0.8s     | 1,250 rec/s |
   | 10K records | 7.5s     | 1,333 rec/s |
   | 100K records| 75s      | 1,333 rec/s |
   
   **Result**: ✅ Exceeds target of 1,000 rec/s
   
   ## Loading Performance
   
   | Data Volume | Duration | Throughput |
   |-------------|----------|------------|
   | 1K records  | 8s       | 125 rec/s |
   | 10K records | 80s      | 125 rec/s |
   | 100K records| 800s     | 125 rec/s |
   
   **Result**: ✅ Meets target of 100 rec/s
   
   ## Query Performance
   
   | Query Type | Avg | P95 | P99 |
   |------------|-----|-----|-----|
   | Search by attributes | 45ms | 78ms | 95ms |
   | Get entity by ID | 12ms | 18ms | 25ms |
   | Get entity by record | 15ms | 22ms | 30ms |
   
   **Result**: ✅ All queries < 100ms at P95
   
   ## Concurrent Query Performance
   
   - Concurrent users: 50
   - Queries per user: 10
   - Total queries: 500
   - Duration: 8.5 seconds
   - Throughput: 58.8 queries/second
   
   **Result**: ✅ Handles 50 concurrent users
   
   ## Resource Utilization
   
   - CPU: 45% average, 78% peak
   - Memory: 62% average, 75% peak
   - Disk I/O: Moderate
   
   **Result**: ✅ Adequate headroom for production
   
   ## Scalability
   
   Performance remains consistent up to 1M records.
   Projected production performance (10M records):
   - Loading time: ~22 hours
   - Query performance: No degradation expected
   
   ## Recommendations
   
   1. Use PostgreSQL for production (not SQLite)
   2. Allocate 8+ vCPU, 32GB+ RAM
   3. Enable connection pooling
   4. Monitor query performance in production
   5. Consider read replicas for query scaling
   
   ## Bottlenecks Identified
   
   - Loading is database-bound (expected)
   - No CPU or memory bottlenecks
   - Query performance excellent
   
   ## Production Readiness
   
   ✅ System is ready for production deployment
   ```

2. **Share report with stakeholders**

### Step 8: Optimize if Needed

1. **If performance targets not met**:
   - Optimize transformation code
   - Tune database configuration
   - Add indexes
   - Increase resources
   - Implement caching
   - Use batch processing

2. **Common optimizations**:
   - Database: Increase shared_buffers, work_mem
   - Loading: Use batch inserts, disable indexes during load
   - Queries: Add database indexes, use connection pooling
   - System: Increase CPU/memory, use SSD storage

3. **Retest after optimizations**

### Transition to Module 10

Once performance testing is complete and targets are met:

1. **Document performance baselines** for production monitoring
2. **Proceed to Module 10**: "Performance looks good! Now let's harden the security before production deployment."

**Success indicator**: ✅ Performance targets met + Benchmarks documented + Bottlenecks identified + Production readiness confirmed

**Agent behavior**:
- Help create benchmark scripts
- Run performance tests
- Analyze results
- Identify bottlenecks
- Recommend optimizations
- Generate performance report

## Workflow: Security Hardening (Module 10)

Use this workflow after performance testing (Module 9) and before production deployment. The goal is to secure the application and data for production use.

**Time**: 1-2 hours

**Prerequisites**: ✅ Module 9 complete (performance validated)

**Purpose**: Implement secrets management, authentication/authorization, encryption, PII handling, security scanning, and vulnerability assessment.

### Step 1: Assess Security Requirements

1. **Review compliance requirements**:
   - GDPR, CCPA, HIPAA, SOX, PCI-DSS?
   - Industry-specific regulations?
   - Company security policies?

2. **Identify sensitive data**:
   - PII (names, addresses, SSN, etc.)
   - Financial data
   - Health information
   - Credentials and secrets

3. **Define security requirements**:
   ```markdown
   Security Requirements:
   - Secrets management (no hardcoded credentials)
   - API authentication (API keys or JWT)
   - Data encryption at rest
   - Data encryption in transit (TLS)
   - PII access logging
   - Regular security scanning
   ```

### Step 2: Implement Secrets Management

1. **Remove hardcoded credentials** from code:
   ```python
   # BAD - Hardcoded credentials
   DATABASE_URL = "postgresql://user:password@localhost/db"
   
   # GOOD - Environment variables
   import os
   DATABASE_URL = os.getenv('DATABASE_URL')
   ```

2. **Use environment variables** for development:
   ```bash
   # .env (not committed to git)
   DATABASE_URL=postgresql://user:password@localhost/db
   SENZING_ENGINE_CONFIG=/path/to/config.json
   API_KEY=your_api_key_here
   ```

3. **Use secrets manager** for production:
   
   **AWS Secrets Manager**:
   ```python
   import boto3
   import json
   
   def get_secret(secret_name):
       client = boto3.client('secretsmanager', region_name='us-east-1')
       response = client.get_secret_value(SecretId=secret_name)
       return json.loads(response['SecretString'])
   
   # Usage
   secrets = get_secret('senzing/prod/database')
   DATABASE_URL = secrets['url']
   DATABASE_PASSWORD = secrets['password']
   ```
   
   **Azure Key Vault**:
   ```python
   from azure.identity import DefaultAzureCredential
   from azure.keyvault.secrets import SecretClient
   
   def get_secret(vault_url, secret_name):
       credential = DefaultAzureCredential()
       client = SecretClient(vault_url=vault_url, credential=credential)
       return client.get_secret(secret_name).value
   
   # Usage
   vault_url = "https://company-vault.vault.azure.net/"
   DATABASE_PASSWORD = get_secret(vault_url, "database-password")
   ```

4. **Update deployment scripts** to use secrets manager

### Step 3: Implement Authentication and Authorization

1. **Add API authentication** (if exposing REST API):
   
   **API Key Authentication**:
   ```python
   from flask import Flask, request, jsonify
   from functools import wraps
   
   app = Flask(__name__)
   
   # Load API keys from secrets manager
   VALID_API_KEYS = get_secret('senzing/api-keys')
   
   def require_api_key(f):
       @wraps(f)
       def decorated_function(*args, **kwargs):
           api_key = request.headers.get('X-API-Key')
           
           if not api_key or api_key not in VALID_API_KEYS:
               return jsonify({'error': 'Invalid API key'}), 401
           
           return f(*args, **kwargs)
       return decorated_function
   
   @app.route('/api/search', methods=['POST'])
   @require_api_key
   def search():
       # Search logic here
       pass
   ```
   
   **JWT Authentication**:
   ```python
   import jwt
   from datetime import datetime, timedelta
   
   SECRET_KEY = get_secret('senzing/jwt-secret')
   
   def generate_token(user_id):
       payload = {
           'user_id': user_id,
           'exp': datetime.utcnow() + timedelta(hours=24)
       }
       return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
   
   def require_jwt(f):
       @wraps(f)
       def decorated_function(*args, **kwargs):
           token = request.headers.get('Authorization', '').replace('Bearer ', '')
           
           try:
               payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
               request.user_id = payload['user_id']
           except jwt.ExpiredSignatureError:
               return jsonify({'error': 'Token expired'}), 401
           except jwt.InvalidTokenError:
               return jsonify({'error': 'Invalid token'}), 401
           
           return f(*args, **kwargs)
       return decorated_function
   ```

2. **Implement role-based access control** (RBAC):
   ```python
   ROLES = {
       'admin': ['read', 'write', 'delete', 'admin'],
       'user': ['read', 'write'],
       'readonly': ['read']
   }
   
   def require_permission(permission):
       def decorator(f):
           @wraps(f)
           def decorated_function(*args, **kwargs):
               user_role = request.user_role  # From JWT or session
               
               if permission not in ROLES.get(user_role, []):
                   return jsonify({'error': 'Insufficient permissions'}), 403
               
               return f(*args, **kwargs)
           return decorated_function
       return decorator
   ```

3. **Add audit logging**:
   ```python
   import logging
   
   audit_logger = logging.getLogger('audit')
   audit_logger.setLevel(logging.INFO)
   handler = logging.FileHandler('logs/audit.log')
   audit_logger.addHandler(handler)
   
   def log_access(user_id, action, resource):
       audit_logger.info(f"User {user_id} performed {action} on {resource}")
   ```

### Step 4: Enable Encryption

1. **Encrypt data at rest**:
   
   **Database encryption** (PostgreSQL):
   ```sql
   -- Enable transparent data encryption
   ALTER SYSTEM SET ssl = on;
   ALTER SYSTEM SET ssl_cert_file = '/path/to/server.crt';
   ALTER SYSTEM SET ssl_key_file = '/path/to/server.key';
   ```
   
   **File encryption**:
   ```python
   from cryptography.fernet import Fernet
   
   # Generate key (store in secrets manager)
   key = Fernet.generate_key()
   cipher = Fernet(key)
   
   # Encrypt sensitive files
   def encrypt_file(input_file, output_file):
       with open(input_file, 'rb') as f:
           data = f.read()
       encrypted = cipher.encrypt(data)
       with open(output_file, 'wb') as f:
           f.write(encrypted)
   ```

2. **Encrypt data in transit**:
   
   **Enable TLS/SSL**:
   ```python
   # Flask with TLS
   if __name__ == '__main__':
       app.run(
           host='0.0.0.0',
           port=443,
           ssl_context=('cert.pem', 'key.pem')
       )
   ```
   
   **Nginx TLS configuration**:
   ```nginx
   server {
       listen 443 ssl;
       server_name api.company.com;
       
       ssl_certificate /etc/ssl/certs/server.crt;
       ssl_certificate_key /etc/ssl/private/server.key;
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers HIGH:!aNULL:!MD5;
       
       location / {
           proxy_pass http://localhost:8080;
       }
   }
   ```

### Step 5: Implement PII Handling

1. **Identify PII fields**:
   - Names, addresses, phone numbers
   - Email addresses
   - SSN, passport numbers
   - Date of birth
   - Financial information

2. **Add PII access controls**:
   ```python
   def mask_pii(data, user_role):
       """Mask PII based on user role"""
       if user_role != 'admin':
           if 'SSN_NUMBER' in data:
               data['SSN_NUMBER'] = 'XXX-XX-' + data['SSN_NUMBER'][-4:]
           if 'EMAIL_ADDRESS' in data:
               email = data['EMAIL_ADDRESS']
               data['EMAIL_ADDRESS'] = email[0] + '***@' + email.split('@')[1]
       return data
   ```

3. **Log PII access**:
   ```python
   def log_pii_access(user_id, entity_id, fields_accessed):
       audit_logger.info(
           f"PII_ACCESS: User {user_id} accessed entity {entity_id} "
           f"fields: {', '.join(fields_accessed)}"
       )
   ```

4. **Implement data retention policies**:
   ```python
   def delete_old_records(days=365):
       """Delete records older than retention period"""
       cutoff_date = datetime.now() - timedelta(days=days)
       # Delete logic here
   ```

### Step 6: Run Security Scanning

1. **Scan dependencies for vulnerabilities**:
   ```bash
   # Python
   pip install safety
   safety check
   
   # Or use pip-audit
   pip install pip-audit
   pip-audit
   
   # Java
   mvn dependency-check:check
   
   # Node.js
   npm audit
   ```

2. **Scan code for security issues**:
   ```bash
   # Python - Bandit
   pip install bandit
   bandit -r src/
   
   # Python - Semgrep
   pip install semgrep
   semgrep --config=auto src/
   ```

3. **Scan Docker images**:
   ```bash
   # Trivy
   trivy image my-senzing-project:latest
   
   # Snyk
   snyk container test my-senzing-project:latest
   ```

4. **Fix identified vulnerabilities**:
   - Update dependencies
   - Patch security issues
   - Remove vulnerable code
   - Rescan to verify fixes

### Step 7: Create Security Audit Document

1. **Document security measures** in `docs/security_audit.md`:
   ```markdown
   # Security Audit Report
   
   **Date**: 2026-03-17
   **Auditor**: Security Team
   
   ## Summary
   
   All security requirements met ✅
   
   ## Secrets Management
   
   ✅ No hardcoded credentials
   ✅ Environment variables for development
   ✅ AWS Secrets Manager for production
   ✅ Secrets rotation policy in place
   
   ## Authentication & Authorization
   
   ✅ API key authentication implemented
   ✅ JWT tokens for user sessions
   ✅ Role-based access control (RBAC)
   ✅ Audit logging enabled
   
   ## Encryption
   
   ✅ TLS 1.3 for data in transit
   ✅ Database encryption at rest
   ✅ Sensitive file encryption
   
   ## PII Handling
   
   ✅ PII fields identified
   ✅ Access controls implemented
   ✅ PII access logging
   ✅ Data retention policy (365 days)
   
   ## Vulnerability Scanning
   
   ✅ Dependency scan: 0 high/critical vulnerabilities
   ✅ Code scan: 0 security issues
   ✅ Container scan: 0 high/critical vulnerabilities
   
   ## Compliance
   
   ✅ GDPR compliant
   ✅ CCPA compliant
   ✅ Company security policy compliant
   
   ## Recommendations
   
   1. Enable MFA for admin accounts
   2. Implement rate limiting on API
   3. Set up intrusion detection
   4. Schedule quarterly security audits
   5. Conduct penetration testing
   
   ## Security Checklist
   
   - [x] Secrets management
   - [x] Authentication/authorization
   - [x] Encryption (at rest and in transit)
   - [x] PII handling
   - [x] Vulnerability scanning
   - [x] Audit logging
   - [x] Access controls
   - [x] Data retention policy
   - [ ] Penetration testing (scheduled)
   - [ ] Security training (scheduled)
   
   ## Production Readiness
   
   ✅ System is security-hardened for production
   ```

2. **Get security team approval** before production

### Step 8: Document Security Procedures

1. **Create security runbook** in `docs/security_procedures.md`:
   - Incident response procedures
   - Security monitoring
   - Vulnerability management
   - Access request process
   - Data breach response

2. **Train operations team** on security procedures

### Transition to Module 11

Once security hardening is complete:

1. **Verify all security measures** are in place
2. **Get security sign-off** from security team
3. **Proceed to Module 11**: "Security is hardened! Now let's set up monitoring and observability for production."

**Success indicator**: ✅ Secrets managed + Authentication implemented + Encryption enabled + PII protected + Vulnerabilities fixed + Security audit complete

**Agent behavior**:
- Help implement secrets management
- Guide authentication setup
- Enable encryption
- Implement PII controls
- Run security scans
- Generate security audit
- Get security approval


## Workflow: Monitoring and Observability (Module 11)

Use this workflow after security hardening (Module 10) and before final deployment. The goal is to set up comprehensive monitoring, logging, and alerting for production operations.

**Time**: 1-2 hours

**Prerequisites**: ✅ Module 10 complete (security hardened)

**Purpose**: Implement distributed tracing, structured logging, metrics collection, APM integration, alerting rules, health checks, and monitoring dashboards.

### Step 1: Choose Monitoring Stack

1. **Review monitoring options**:
   - **Prometheus + Grafana**: Open source, self-hosted
   - **ELK Stack**: Elasticsearch, Logstash, Kibana for logs
   - **Cloud-native**: CloudWatch (AWS), Application Insights (Azure), Cloud Monitoring (GCP)
   - **Commercial APM**: DataDog, New Relic, Dynatrace

2. **Consider factors**:
   - Budget (open source vs commercial)
   - Existing infrastructure
   - Team expertise
   - Integration requirements
   - Scalability needs

3. **Make decision** and document in `docs/monitoring_strategy.md`:
   ```markdown
   # Monitoring Strategy
   
   **Stack**: Prometheus + Grafana
   **Rationale**: Open source, cost-effective, team has experience
   
   **Components**:
   - Prometheus: Metrics collection and storage
   - Grafana: Visualization and dashboards
   - Alertmanager: Alert routing and notification
   - Node Exporter: System metrics
   - Postgres Exporter: Database metrics
   ```

### Step 2: Implement Metrics Collection

1. **Install Prometheus client library**:
   ```bash
   pip install prometheus-client
   ```

2. **Add metrics to application** in `src/utils/metrics.py`:
   ```python
   #!/usr/bin/env python3
   """
   Application metrics for Prometheus
   """
   
   from prometheus_client import Counter, Histogram, Gauge, start_http_server
   import time
   
   # Transformation metrics
   transformation_records_total = Counter(
       'transformation_records_total',
       'Total records transformed',
       ['data_source']
   )
   transformation_errors_total = Counter(
       'transformation_errors_total',
       'Total transformation errors',
       ['data_source', 'error_type']
   )
   transformation_duration_seconds = Histogram(
       'transformation_duration_seconds',
       'Time spent transforming records',
       ['data_source']
   )
   
   # Loading metrics
   loading_records_total = Counter(
       'loading_records_total',
       'Total records loaded',
       ['data_source']
   )
   loading_errors_total = Counter(
       'loading_errors_total',
       'Total loading errors',
       ['data_source', 'error_type']
   )
   loading_duration_seconds = Histogram(
       'loading_duration_seconds',
       'Time spent loading records',
       ['data_source']
   )
   loading_queue_size = Gauge(
       'loading_queue_size',
       'Records waiting to be loaded'
   )
   
   # Query metrics
   query_requests_total = Counter(
       'query_requests_total',
       'Total query requests',
       ['query_type', 'status']
   )
   query_duration_seconds = Histogram(
       'query_duration_seconds',
       'Query response time',
       ['query_type']
   )
   
   # System metrics
   cpu_usage_percent = Gauge('cpu_usage_percent', 'CPU utilization')
   memory_usage_percent = Gauge('memory_usage_percent', 'Memory utilization')
   disk_usage_percent = Gauge('disk_usage_percent', 'Disk utilization')
   
   # Entity resolution metrics
   entities_created_total = Counter('entities_created_total', 'Total entities created')
   entities_resolved_total = Counter('entities_resolved_total', 'Total entities resolved')
   match_rate = Gauge('match_rate', 'Percentage of records that matched existing entities')
   
   def start_metrics_server(port=8000):
       """Start Prometheus metrics HTTP server"""
       start_http_server(port)
       print(f"Metrics server started on port {port}")
   
   # Usage example
   if __name__ == '__main__':
       start_metrics_server()
       
       # Keep server running
       while True:
           time.sleep(1)
   ```

3. **Instrument application code**:
   ```python
   # In transformation code
   from src.utils.metrics import transformation_records_total, transformation_duration_seconds
   
   with transformation_duration_seconds.labels(data_source='CUSTOMERS').time():
       transformed_record = transform(source_record)
       transformation_records_total.labels(data_source='CUSTOMERS').inc()
   
   # In loading code
   from src.utils.metrics import loading_records_total, loading_duration_seconds
   
   with loading_duration_seconds.labels(data_source='CUSTOMERS').time():
       engine.addRecord(data_source, record_id, record_json)
       loading_records_total.labels(data_source='CUSTOMERS').inc()
   
   # In query code
   from src.utils.metrics import query_requests_total, query_duration_seconds
   
   with query_duration_seconds.labels(query_type='search').time():
       results = engine.searchByAttributes(search_attrs)
       query_requests_total.labels(query_type='search', status='success').inc()
   ```

### Step 3: Configure Structured Logging

1. **Create structured logger** in `src/utils/structured_logger.py`:
   ```python
   #!/usr/bin/env python3
   """
   Structured logging for searchable, analyzable logs
   """
   
   import logging
   import json
   from datetime import datetime
   import traceback
   
   class JSONFormatter(logging.Formatter):
       """Format logs as JSON for easy parsing"""
       
       def format(self, record):
           log_data = {
               'timestamp': datetime.utcnow().isoformat() + 'Z',
               'level': record.levelname,
               'logger': record.name,
               'message': record.getMessage(),
               'module': record.module,
               'function': record.funcName,
               'line': record.lineno,
           }
           
           # Add custom fields
           if hasattr(record, 'user_id'):
               log_data['user_id'] = record.user_id
           if hasattr(record, 'request_id'):
               log_data['request_id'] = record.request_id
           if hasattr(record, 'data_source'):
               log_data['data_source'] = record.data_source
           if hasattr(record, 'entity_id'):
               log_data['entity_id'] = record.entity_id
           
           # Add exception info
           if record.exc_info:
               log_data['exception'] = {
                   'type': record.exc_info[0].__name__,
                   'message': str(record.exc_info[1]),
                   'traceback': traceback.format_exception(*record.exc_info)
               }
           
           return json.dumps(log_data)
   
   def setup_logging(log_file='logs/application.log', level=logging.INFO):
       """Configure structured logging"""
       
       # Create logger
       logger = logging.getLogger()
       logger.setLevel(level)
       
       # Console handler (human-readable)
       console_handler = logging.StreamHandler()
       console_handler.setLevel(level)
       console_formatter = logging.Formatter(
           '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
       )
       console_handler.setFormatter(console_formatter)
       logger.addHandler(console_handler)
       
       # File handler (JSON)
       file_handler = logging.FileHandler(log_file)
       file_handler.setLevel(level)
       file_handler.setFormatter(JSONFormatter())
       logger.addHandler(file_handler)
       
       return logger
   
   # Usage example
   logger = setup_logging()
   
   # Log with custom fields
   logger.info('Record loaded', extra={
       'data_source': 'CUSTOMERS',
       'record_id': '12345',
       'entity_id': 67890,
       'duration_ms': 25
   })
   ```

2. **Update application to use structured logging**:
   ```python
   from src.utils.structured_logger import setup_logging
   
   logger = setup_logging()
   
   # Throughout application
   logger.info('Starting transformation', extra={'data_source': 'CUSTOMERS'})
   logger.error('Loading failed', extra={'data_source': 'CUSTOMERS', 'error': str(e)})
   ```

### Step 4: Set Up Distributed Tracing (Optional)

1. **Install OpenTelemetry** (if using distributed architecture):
   ```bash
   pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-flask
   ```

2. **Configure tracing** in `src/utils/tracing.py`:
   ```python
   from opentelemetry import trace
   from opentelemetry.sdk.trace import TracerProvider
   from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
   from opentelemetry.instrumentation.flask import FlaskInstrumentor
   
   def setup_tracing(app):
       """Configure distributed tracing"""
       
       # Set up tracer provider
       trace.set_tracer_provider(TracerProvider())
       tracer = trace.get_tracer(__name__)
       
       # Add span processor
       span_processor = BatchSpanProcessor(ConsoleSpanExporter())
       trace.get_tracer_provider().add_span_processor(span_processor)
       
       # Instrument Flask
       FlaskInstrumentor().instrument_app(app)
       
       return tracer
   ```

3. **Add tracing to critical paths**:
   ```python
   from opentelemetry import trace
   
   tracer = trace.get_tracer(__name__)
   
   with tracer.start_as_current_span("load_records") as span:
       span.set_attribute("data_source", data_source)
       span.set_attribute("record_count", len(records))
       
       # Loading logic here
   ```

### Step 5: Create Health Check Endpoints

1. **Implement health checks** in `src/api/health.py`:
   ```python
   #!/usr/bin/env python3
   """
   Health check endpoints for monitoring
   """
   
   from flask import Flask, jsonify
   import psycopg2
   from senzing import SzEngine
   import psutil
   
   app = Flask(__name__)
   
   @app.route('/health')
   def health():
       """Basic health check - is service running?"""
       return jsonify({
           'status': 'healthy',
           'service': 'senzing-entity-resolution'
       }), 200
   
   @app.route('/health/ready')
   def readiness():
       """Readiness check - can service accept traffic?"""
       checks = {
           'database': check_database(),
           'senzing': check_senzing_engine(),
           'disk_space': check_disk_space(),
       }
       
       all_ready = all(checks.values())
       status_code = 200 if all_ready else 503
       
       return jsonify({
           'status': 'ready' if all_ready else 'not_ready',
           'checks': checks
       }), status_code
   
   @app.route('/health/live')
   def liveness():
       """Liveness check - should service be restarted?"""
       # Check if process is responsive
       return jsonify({
           'status': 'alive',
           'uptime_seconds': get_uptime()
       }), 200
   
   def check_database():
       """Check database connectivity"""
       try:
           conn = psycopg2.connect(DATABASE_URL)
           cursor = conn.cursor()
           cursor.execute('SELECT 1')
           cursor.close()
           conn.close()
           return True
       except Exception as e:
           logger.error(f"Database health check failed: {e}")
           return False
   
   def check_senzing_engine():
       """Check Senzing engine"""
       try:
           engine = SzEngine()
           engine.initialize(instance_name='health_check', settings=ENGINE_CONFIG)
           # Try a simple operation
           stats = engine.getStats()
           engine.destroy()
           return True
       except Exception as e:
           logger.error(f"Senzing health check failed: {e}")
           return False
   
   def check_disk_space():
       """Check available disk space"""
       disk = psutil.disk_usage('/')
       free_gb = disk.free / (1024**3)
       return free_gb > 10  # At least 10GB free
   
   def get_uptime():
       """Get process uptime in seconds"""
       import time
       return time.time() - psutil.Process().create_time()
   
   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=8080)
   ```

2. **Test health checks**:
   ```bash
   curl http://localhost:8080/health
   curl http://localhost:8080/health/ready
   curl http://localhost:8080/health/live
   ```

### Step 6: Configure Alerting Rules

1. **Create Prometheus alerting rules** in `config/alerting_rules.yml`:
   ```yaml
   groups:
     - name: critical_alerts
       interval: 30s
       rules:
         - alert: ServiceDown
           expr: up == 0
           for: 1m
           labels:
             severity: critical
           annotations:
             summary: "Service {{ $labels.instance }} is down"
             description: "Service has been down for more than 1 minute"
         
         - alert: HighErrorRate
           expr: rate(loading_errors_total[5m]) > 10
           for: 5m
           labels:
             severity: critical
           annotations:
             summary: "High error rate detected"
             description: "Error rate is {{ $value }} errors/second"
         
         - alert: DatabaseDown
           expr: pg_up == 0
           for: 1m
           labels:
             severity: critical
           annotations:
             summary: "Database is down"
             description: "PostgreSQL database is not responding"
     
     - name: warning_alerts
       interval: 1m
       rules:
         - alert: HighCPUUsage
           expr: cpu_usage_percent > 80
           for: 10m
           labels:
             severity: warning
           annotations:
             summary: "High CPU usage"
             description: "CPU usage is {{ $value }}%"
         
         - alert: HighMemoryUsage
           expr: memory_usage_percent > 85
           for: 10m
           labels:
             severity: warning
           annotations:
             summary: "High memory usage"
             description: "Memory usage is {{ $value }}%"
         
         - alert: SlowQueries
           expr: histogram_quantile(0.95, query_duration_seconds) > 1
           for: 5m
           labels:
             severity: warning
           annotations:
             summary: "Slow queries detected"
             description: "95th percentile query time is {{ $value }}s"
         
         - alert: LowDiskSpace
           expr: disk_usage_percent > 85
           for: 5m
           labels:
             severity: warning
           annotations:
             summary: "Low disk space"
             description: "Disk usage is {{ $value }}%"
   ```

2. **Configure Alertmanager** in `config/alertmanager.yml`:
   ```yaml
   global:
     resolve_timeout: 5m
   
   route:
     group_by: ['alertname', 'severity']
     group_wait: 10s
     group_interval: 10s
     repeat_interval: 12h
     receiver: 'default'
     routes:
       - match:
           severity: critical
         receiver: 'pagerduty'
       - match:
           severity: warning
         receiver: 'email'
   
   receivers:
     - name: 'default'
       email_configs:
         - to: 'ops-team@company.com'
           from: 'alertmanager@company.com'
           smarthost: 'smtp.company.com:587'
           auth_username: 'alertmanager@company.com'
           auth_password: '${SMTP_PASSWORD}'
     
     - name: 'pagerduty'
       pagerduty_configs:
         - service_key: '${PAGERDUTY_SERVICE_KEY}'
     
     - name: 'email'
       email_configs:
         - to: 'ops-team@company.com'
   ```

### Step 7: Create Monitoring Dashboards

1. **Create Grafana dashboard** in `config/grafana_dashboards/senzing_overview.json`:
   ```json
   {
     "dashboard": {
       "title": "Senzing Entity Resolution - Overview",
       "panels": [
         {
           "title": "Records Loaded (per second)",
           "targets": [
             {
               "expr": "rate(loading_records_total[5m])",
               "legendFormat": "{{data_source}}"
             }
           ],
           "type": "graph"
         },
         {
           "title": "Query Performance (95th percentile)",
           "targets": [
             {
               "expr": "histogram_quantile(0.95, query_duration_seconds)",
               "legendFormat": "{{query_type}}"
             }
           ],
           "type": "graph"
         },
         {
           "title": "Error Rate",
           "targets": [
             {
               "expr": "rate(loading_errors_total[5m])",
               "legendFormat": "Loading Errors"
             },
             {
               "expr": "rate(transformation_errors_total[5m])",
               "legendFormat": "Transformation Errors"
             }
           ],
           "type": "graph"
         },
         {
           "title": "System Resources",
           "targets": [
             {
               "expr": "cpu_usage_percent",
               "legendFormat": "CPU %"
             },
             {
               "expr": "memory_usage_percent",
               "legendFormat": "Memory %"
             },
             {
               "expr": "disk_usage_percent",
               "legendFormat": "Disk %"
             }
           ],
           "type": "graph"
         },
         {
           "title": "Entity Resolution Stats",
           "targets": [
             {
               "expr": "entities_created_total",
               "legendFormat": "Entities Created"
             },
             {
               "expr": "match_rate",
               "legendFormat": "Match Rate %"
             }
           ],
           "type": "stat"
         }
       ]
     }
   }
   ```

2. **Import dashboard into Grafana**:
   ```bash
   # Via API
   curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
     -H "Content-Type: application/json" \
     -d @config/grafana_dashboards/senzing_overview.json
   ```

### Step 8: Deploy Monitoring Stack

1. **Create Docker Compose for monitoring** in `docker-compose.monitoring.yml`:
   ```yaml
   version: '3.8'
   
   services:
     prometheus:
       image: prom/prometheus:latest
       ports:
         - "9090:9090"
       volumes:
         - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
         - ./config/alerting_rules.yml:/etc/prometheus/alerting_rules.yml
         - prometheus_data:/prometheus
       command:
         - '--config.file=/etc/prometheus/prometheus.yml'
         - '--storage.tsdb.path=/prometheus'
       restart: unless-stopped
     
     grafana:
       image: grafana/grafana:latest
       ports:
         - "3000:3000"
       environment:
         - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
         - GF_USERS_ALLOW_SIGN_UP=false
       volumes:
         - grafana_data:/var/lib/grafana
         - ./config/grafana_dashboards:/etc/grafana/provisioning/dashboards
       restart: unless-stopped
     
     alertmanager:
       image: prom/alertmanager:latest
       ports:
         - "9093:9093"
       volumes:
         - ./config/alertmanager.yml:/etc/alertmanager/alertmanager.yml
       command:
         - '--config.file=/etc/alertmanager/alertmanager.yml'
       restart: unless-stopped
     
     node-exporter:
       image: prom/node-exporter:latest
       ports:
         - "9100:9100"
       restart: unless-stopped
     
     postgres-exporter:
       image: prometheuscommunity/postgres-exporter:latest
       ports:
         - "9187:9187"
       environment:
         - DATA_SOURCE_NAME=${DATABASE_URL}
       restart: unless-stopped
   
   volumes:
     prometheus_data:
     grafana_data:
   ```

2. **Create Prometheus configuration** in `config/prometheus.yml`:
   ```yaml
   global:
     scrape_interval: 15s
     evaluation_interval: 15s
   
   alerting:
     alertmanagers:
       - static_configs:
           - targets: ['alertmanager:9093']
   
   rule_files:
     - '/etc/prometheus/alerting_rules.yml'
   
   scrape_configs:
     - job_name: 'senzing-app'
       static_configs:
         - targets: ['host.docker.internal:8000']
     
     - job_name: 'node-exporter'
       static_configs:
         - targets: ['node-exporter:9100']
     
     - job_name: 'postgres'
       static_configs:
         - targets: ['postgres-exporter:9187']
   ```

3. **Start monitoring stack**:
   ```bash
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

4. **Verify monitoring**:
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000
   - Alertmanager: http://localhost:9093

### Step 9: Create Runbooks

1. **Document alert response procedures** in `docs/runbooks/`:

   **docs/runbooks/high_error_rate.md**:
   ```markdown
   # Runbook: High Error Rate Alert
   
   ## Alert
   `HighErrorRate`: Error rate exceeds 10 errors/second for 5 minutes
   
   ## Severity
   Critical
   
   ## Impact
   - Data loading may be failing
   - Data quality issues
   - Potential data loss
   
   ## Investigation Steps
   
   1. Check error logs:
      ```bash
      tail -f logs/application.log | grep ERROR
      ```
   
   2. Identify error types:
      ```bash
      grep ERROR logs/application.log | jq '.error_type' | sort | uniq -c
      ```
   
   3. Check affected data sources:
      ```bash
      grep ERROR logs/application.log | jq '.data_source' | sort | uniq -c
      ```
   
   4. Review recent changes:
      - Code deployments
      - Configuration changes
      - Data source updates
   
   ## Resolution Steps
   
   1. **If data quality issue**:
      - Review source data
      - Fix transformation logic
      - Reload affected records
   
   2. **If database issue**:
      - Check database connectivity
      - Check disk space
      - Review database logs
   
   3. **If configuration issue**:
      - Verify Senzing configuration
      - Check environment variables
      - Restart services
   
   ## Escalation
   
   If unresolved after 30 minutes, escalate to:
   - Technical Lead: [name]
   - Database Admin: [name]
   ```

2. **Create runbooks for each alert type**

### Step 10: Test Monitoring

1. **Test metrics collection**:
   ```bash
   # Check metrics endpoint
   curl http://localhost:8000/metrics
   
   # Verify metrics in Prometheus
   # Go to http://localhost:9090 and query: loading_records_total
   ```

2. **Test health checks**:
   ```bash
   curl http://localhost:8080/health/ready
   ```

3. **Test alerts** (trigger test alert):
   ```bash
   # Simulate high error rate
   for i in {1..100}; do
     # Trigger errors in application
   done
   
   # Check Alertmanager
   curl http://localhost:9093/api/v2/alerts
   ```

4. **Verify dashboards** show real-time data

### Step 11: Document Monitoring Setup

1. **Create monitoring guide** in `docs/monitoring_guide.md`:
   ```markdown
   # Monitoring Guide
   
   ## Overview
   
   Monitoring stack: Prometheus + Grafana + Alertmanager
   
   ## Access
   
   - **Prometheus**: http://prometheus.company.com:9090
   - **Grafana**: http://grafana.company.com:3000
   - **Alertmanager**: http://alertmanager.company.com:9093
   
   ## Key Metrics
   
   ### Application Metrics
   - `loading_records_total`: Total records loaded
   - `loading_errors_total`: Total loading errors
   - `query_duration_seconds`: Query response time
   - `entities_created_total`: Total entities created
   - `match_rate`: Percentage of records matched
   
   ### System Metrics
   - `cpu_usage_percent`: CPU utilization
   - `memory_usage_percent`: Memory utilization
   - `disk_usage_percent`: Disk utilization
   
   ### Database Metrics
   - `pg_up`: Database availability
   - `pg_stat_database_*`: Database statistics
   
   ## Dashboards
   
   ### Senzing Overview
   - Records loaded per second
   - Query performance (P95)
   - Error rates
   - System resources
   - Entity resolution stats
   
   ### System Health
   - CPU, memory, disk usage
   - Network I/O
   - Database connections
   
   ## Alerts
   
   ### Critical (Page immediately)
   - ServiceDown: Service is not responding
   - HighErrorRate: Error rate > 10/second
   - DatabaseDown: Database is not responding
   
   ### Warning (Investigate soon)
   - HighCPUUsage: CPU > 80% for 10 minutes
   - HighMemoryUsage: Memory > 85% for 10 minutes
   - SlowQueries: P95 query time > 1 second
   - LowDiskSpace: Disk > 85% full
   
   ## Runbooks
   
   See `docs/runbooks/` for alert response procedures:
   - `high_error_rate.md`
   - `service_down.md`
   - `database_down.md`
   - `high_cpu_usage.md`
   - `slow_queries.md`
   
   ## Maintenance
   
   ### Daily
   - Review dashboards for anomalies
   - Check alert history
   
   ### Weekly
   - Review error logs
   - Analyze performance trends
   - Update runbooks if needed
   
   ### Monthly
   - Review and adjust alert thresholds
   - Archive old metrics data
   - Update dashboards
   ```

### Transition to Module 12

Once monitoring is fully operational:

1. **Verify all monitoring components** are working
2. **Test alert notifications** are being received
3. **Train operations team** on monitoring tools
4. **Proceed to Module 12**: "Monitoring is live! Now let's package everything for production deployment."

**Success indicator**: ✅ Monitoring stack deployed + Metrics collected + Logs structured + Alerts configured + Dashboards created + Runbooks documented + Team trained

**Agent behavior**:
- Help choose appropriate monitoring stack
- Implement metrics collection
- Configure structured logging
- Set up distributed tracing (if needed)
- Create health check endpoints
- Configure alerting rules
- Build monitoring dashboards
- Create runbooks for alerts
- Test monitoring end-to-end
- Train team on monitoring tools


## Workflow: Package and Deploy (Module 12) - UPDATED

This workflow has been updated to reference the new modules 9, 10, and 11.

Use this workflow after monitoring setup (Module 11) to package and deploy your production-ready solution.

**Time**: 2-3 hours

**Prerequisites**: 
- ✅ Module 9 complete (performance tested)
- ✅ Module 10 complete (security hardened)
- ✅ Module 11 complete (monitoring configured)

**Purpose**: Refactor code into production package structure, add comprehensive tests, apply language-specific packaging, generate deployment documentation, and create deployment artifacts.

### Step 1: Review Production Readiness

1. **Verify all prerequisites**:
   - [ ] Performance benchmarks meet targets (Module 9)
   - [ ] Security audit passed (Module 10)
   - [ ] Monitoring operational (Module 11)
   - [ ] UAT sign-off obtained (Module 8)

2. **Review deployment requirements**:
   - Target environment (on-prem, cloud, containers)
   - Database (PostgreSQL, MySQL, MS SQL, Oracle)
   - Programming language (Python, Java, C#, Rust)
   - Integration pattern (batch, API, streaming, microservice)

3. **Document deployment configuration** in `docs/deployment_config.md`:
   ```markdown
   # Deployment Configuration
   
   **Environment**: AWS ECS (Production)
   **Database**: PostgreSQL 15 (RDS)
   **Language**: Python 3.11
   **Integration**: REST API + Batch Processing
   
   **Infrastructure**:
   - Application: 4 vCPU, 16GB RAM (ECS Fargate)
   - Database: db.r6g.2xlarge (8 vCPU, 64GB RAM)
   - Storage: 500GB SSD
   
   **Monitoring**: Prometheus + Grafana (from Module 11)
   **Security**: AWS Secrets Manager, TLS 1.3 (from Module 10)
   **Performance**: 125 rec/s loading, <100ms queries (from Module 9)
   ```

### Step 2: Refactor Code Structure

1. **Review current code organization**:
   - Transformation scripts from Module 4
   - Loading scripts from Modules 6-7
   - Query programs from Module 8
   - Performance tests from Module 9
   - Security implementations from Module 10
   - Monitoring code from Module 11

2. **Create production package structure**:
   ```
   my-senzing-project/
   ├── setup.py / pyproject.toml
   ├── requirements.txt
   ├── README.md
   ├── LICENSE
   ├── Dockerfile
   ├── docker-compose.yml
   ├── src/
   │   ├── __init__.py
   │   ├── config.py
   │   ├── transform/          # From Module 4
   │   ├── load/               # From Modules 6-7
   │   ├── query/              # From Module 8
   │   ├── api/                # REST API (if applicable)
   │   ├── utils/
   │   │   ├── metrics.py      # From Module 11
   │   │   ├── structured_logger.py  # From Module 11
   │   │   ├── security.py     # From Module 10
   │   │   └── health.py       # From Module 11
   ├── tests/                  # From Module 9
   │   ├── test_transform/
   │   ├── test_load/
   │   ├── test_query/
   │   ├── test_performance/
   │   └── test_security/
   ├── config/
   │   ├── prometheus.yml      # From Module 11
   │   ├── alerting_rules.yml  # From Module 11
   │   ├── grafana_dashboards/ # From Module 11
   │   └── logging.yaml
   ├── docs/
   │   ├── deployment.md
   │   ├── performance_report.md    # From Module 9
   │   ├── security_audit.md        # From Module 10
   │   ├── monitoring_guide.md      # From Module 11
   │   ├── runbooks/                # From Module 11
   │   └── disaster_recovery.md     # Reference steering/disaster-recovery.md
   └── scripts/
       ├── deploy.sh
       ├── backup.sh
       └── health_check.sh
   ```

3. **Refactor code into package**:
   - Extract common utilities
   - Apply design patterns
   - Add configuration management
   - Implement proper error handling

### Step 3: Integrate Security, Performance, and Monitoring

1. **Ensure security measures are integrated**:
   ```python
   # src/config.py
   import os
   from src.utils.security import get_secret
   
   class Config:
       # Secrets from Module 10
       DATABASE_URL = get_secret('senzing/database-url')
       API_KEY = get_secret('senzing/api-key')
       
       # Performance settings from Module 9
       BATCH_SIZE = 1000
       MAX_WORKERS = 4
       CONNECTION_POOL_SIZE = 10
       
       # Monitoring settings from Module 11
       METRICS_PORT = 8000
       HEALTH_CHECK_PORT = 8080
       LOG_LEVEL = 'INFO'
   ```

2. **Integrate monitoring into all components**:
   ```python
   # src/load/loader.py
   from src.utils.metrics import loading_records_total, loading_duration_seconds
   from src.utils.structured_logger import setup_logging
   
   logger = setup_logging()
   
   class Loader:
       def load_record(self, record):
           with loading_duration_seconds.labels(data_source=self.data_source).time():
               try:
                   # Loading logic
                   loading_records_total.labels(data_source=self.data_source).inc()
                   logger.info('Record loaded', extra={
                       'data_source': self.data_source,
                       'record_id': record['RECORD_ID']
                   })
               except Exception as e:
                   logger.error('Loading failed', extra={
                       'data_source': self.data_source,
                       'error': str(e)
                   })
                   raise
   ```

3. **Add performance optimizations from Module 9**:
   - Connection pooling
   - Batch processing
   - Caching (if applicable)
   - Database indexes

### Step 4: Create Comprehensive Test Suite

1. **Organize tests by module**:
   ```
   tests/
   ├── test_transform/         # Unit tests
   ├── test_load/              # Integration tests
   ├── test_query/             # API tests
   ├── test_performance/       # From Module 9
   │   ├── test_benchmark_transform.py
   │   ├── test_benchmark_loading.py
   │   └── test_benchmark_queries.py
   ├── test_security/          # From Module 10
   │   ├── test_authentication.py
   │   ├── test_authorization.py
   │   └── test_encryption.py
   └── test_monitoring/        # From Module 11
       ├── test_metrics.py
       ├── test_health_checks.py
       └── test_logging.py
   ```

2. **Run full test suite**:
   ```bash
   pytest tests/ --cov=src --cov-report=html
   ```

3. **Verify test coverage** > 80%

### Step 5: Create Deployment Artifacts

1. **Create Dockerfile** with security and monitoring:
   ```dockerfile
   FROM python:3.11-slim
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       postgresql-client \
       && rm -rf /var/lib/apt/lists/*
   
   WORKDIR /app
   
   # Copy requirements
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Copy application
   COPY src/ ./src/
   COPY config/ ./config/
   
   # Create non-root user (security from Module 10)
   RUN useradd -m -u 1000 senzing && chown -R senzing:senzing /app
   USER senzing
   
   # Expose ports
   EXPOSE 8000 8080
   
   # Health check (from Module 11)
   HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
     CMD curl -f http://localhost:8080/health || exit 1
   
   # Start application
   CMD ["python", "-m", "src.api.server"]
   ```

2. **Create docker-compose.yml** with full stack:
   ```yaml
   version: '3.8'
   
   services:
     app:
       build: .
       ports:
         - "8000:8000"  # Metrics
         - "8080:8080"  # API + Health checks
       environment:
         - DATABASE_URL=${DATABASE_URL}
         - SENZING_CONFIG=${SENZING_CONFIG}
       depends_on:
         - postgres
         - prometheus
       restart: unless-stopped
     
     postgres:
       image: postgres:15
       environment:
         - POSTGRES_DB=senzing
         - POSTGRES_USER=senzing
         - POSTGRES_PASSWORD=${DB_PASSWORD}
       volumes:
         - postgres_data:/var/lib/postgresql/data
       restart: unless-stopped
     
     # Monitoring stack from Module 11
     prometheus:
       image: prom/prometheus:latest
       ports:
         - "9090:9090"
       volumes:
         - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
         - ./config/alerting_rules.yml:/etc/prometheus/alerting_rules.yml
       restart: unless-stopped
     
     grafana:
       image: grafana/grafana:latest
       ports:
         - "3000:3000"
       environment:
         - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
       volumes:
         - ./config/grafana_dashboards:/etc/grafana/provisioning/dashboards
       restart: unless-stopped
   
   volumes:
     postgres_data:
   ```

3. **Create Kubernetes manifests** (if deploying to K8s):
   - Deployment
   - Service
   - ConfigMap
   - Secret
   - Ingress
   - HorizontalPodAutoscaler

### Step 6: Generate Deployment Documentation

1. **Create comprehensive deployment guide** in `docs/deployment.md`:
   ```markdown
   # Deployment Guide
   
   ## Prerequisites
   
   - Python 3.11+
   - PostgreSQL 15+
   - Senzing SDK 4.0+
   - Docker (optional)
   - Kubernetes (optional)
   
   ## Pre-Deployment Checklist
   
   - [ ] Performance benchmarks met (see `performance_report.md`)
   - [ ] Security audit passed (see `security_audit.md`)
   - [ ] Monitoring configured (see `monitoring_guide.md`)
   - [ ] UAT sign-off obtained
   - [ ] Disaster recovery plan reviewed (see `disaster_recovery.md`)
   - [ ] Multi-environment strategy defined (see `steering/multi-environment-strategy.md`)
   
   ## Deployment Steps
   
   ### 1. Prepare Environment
   
   \`\`\`bash
   # Set up secrets (from Module 10)
   aws secretsmanager create-secret --name senzing/database-url --secret-string "postgresql://..."
   aws secretsmanager create-secret --name senzing/api-key --secret-string "..."
   \`\`\`
   
   ### 2. Deploy Database
   
   \`\`\`bash
   # Create database
   createdb senzing_prod
   
   # Run migrations
   python scripts/migrate_db.py
   \`\`\`
   
   ### 3. Deploy Application
   
   \`\`\`bash
   # Docker
   docker-compose up -d
   
   # Or Kubernetes
   kubectl apply -f k8s/
   \`\`\`
   
   ### 4. Deploy Monitoring (from Module 11)
   
   \`\`\`bash
   docker-compose -f docker-compose.monitoring.yml up -d
   \`\`\`
   
   ### 5. Verify Deployment
   
   \`\`\`bash
   # Health checks
   curl http://localhost:8080/health/ready
   
   # Metrics
   curl http://localhost:8000/metrics
   
   # Run smoke tests
   pytest tests/smoke/
   \`\`\`
   
   ## Post-Deployment
   
   - [ ] Verify monitoring dashboards
   - [ ] Test alert notifications
   - [ ] Run performance tests
   - [ ] Verify security measures
   - [ ] Update documentation
   
   ## Rollback Procedure
   
   See `disaster_recovery.md` for rollback procedures.
   
   ## API Gateway Integration
   
   See `steering/api-gateway-patterns.md` for API gateway setup.
   
   ## Multi-Environment Strategy
   
   See `steering/multi-environment-strategy.md` for dev/staging/prod setup.
   ```

2. **Reference related documentation**:
   - `steering/disaster-recovery.md` - Backup and recovery procedures
   - `steering/api-gateway-patterns.md` - API gateway integration
   - `steering/multi-environment-strategy.md` - Environment management

### Step 7: Create Deployment Scripts

1. **Create deployment script** in `scripts/deploy.sh`:
   ```bash
   #!/bin/bash
   set -e
   
   ENVIRONMENT=$1
   
   if [ -z "$ENVIRONMENT" ]; then
       echo "Usage: ./deploy.sh <environment>"
       exit 1
   fi
   
   echo "Deploying to $ENVIRONMENT..."
   
   # Load environment-specific configuration
   source config/env.$ENVIRONMENT.sh
   
   # Run pre-deployment checks
   echo "Running pre-deployment checks..."
   python scripts/pre_deploy_check.py
   
   # Backup database (from disaster recovery plan)
   echo "Backing up database..."
   ./scripts/backup.sh
   
   # Deploy application
   echo "Deploying application..."
   if [ "$ENVIRONMENT" == "production" ]; then
       # Blue-green deployment
       kubectl apply -f k8s/blue-green/
   else
       # Standard deployment
       kubectl apply -f k8s/
   fi
   
   # Wait for deployment
   kubectl rollout status deployment/senzing-app
   
   # Run smoke tests
   echo "Running smoke tests..."
   pytest tests/smoke/
   
   # Verify monitoring
   echo "Verifying monitoring..."
   curl -f http://prometheus:9090/-/healthy
   curl -f http://grafana:3000/api/health
   
   echo "Deployment complete!"
   ```

### Step 8: Final Validation

1. **Run complete validation**:
   ```bash
   # All tests
   pytest tests/
   
   # Performance tests (from Module 9)
   python src/testing/benchmark_loading.py
   python src/testing/benchmark_queries.py
   
   # Security scan (from Module 10)
   safety check
   bandit -r src/
   
   # Monitoring check (from Module 11)
   curl http://localhost:8000/metrics
   curl http://localhost:8080/health/ready
   ```

2. **Generate final deployment report**:
   ```markdown
   # Deployment Readiness Report
   
   **Date**: 2026-03-17
   **Version**: 1.0.0
   
   ## Validation Results
   
   ### Tests
   - ✅ Unit tests: 150/150 passed
   - ✅ Integration tests: 45/45 passed
   - ✅ Performance tests: All benchmarks met
   - ✅ Security tests: No vulnerabilities
   - ✅ Test coverage: 87%
   
   ### Performance (Module 9)
   - ✅ Loading: 125 rec/s (target: 100 rec/s)
   - ✅ Queries: 45ms P95 (target: <100ms)
   - ✅ Concurrent users: 50 (target: 50)
   
   ### Security (Module 10)
   - ✅ Secrets management: AWS Secrets Manager
   - ✅ Authentication: JWT tokens
   - ✅ Encryption: TLS 1.3
   - ✅ Vulnerability scan: 0 high/critical
   
   ### Monitoring (Module 11)
   - ✅ Metrics collection: Operational
   - ✅ Logging: Structured JSON logs
   - ✅ Alerts: Configured and tested
   - ✅ Dashboards: Created and verified
   
   ### Documentation
   - ✅ Deployment guide
   - ✅ Performance report
   - ✅ Security audit
   - ✅ Monitoring guide
   - ✅ Runbooks
   - ✅ Disaster recovery plan
   
   ## Production Readiness
   
   ✅ **APPROVED FOR PRODUCTION DEPLOYMENT**
   
   Signed: _______________ Date: ___________
   ```

### Transition to Production

1. **Schedule deployment window**
2. **Notify stakeholders**
3. **Execute deployment**
4. **Monitor closely** for first 24-48 hours
5. **Document lessons learned**

**Success indicator**: ✅ Code packaged + Tests passing + Deployment artifacts created + Documentation complete + Validation passed + Production deployed

**Agent behavior**:
- Review all previous modules (9, 10, 11)
- Refactor code into production structure
- Integrate security, performance, and monitoring
- Create comprehensive test suite
- Generate deployment artifacts
- Create deployment documentation
- Reference disaster recovery, API gateway, and multi-environment strategies
- Validate production readiness
- Support deployment execution
