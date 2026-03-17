# Module 7: Multi-Source Orchestration

## Overview

Module 7 focuses on orchestrating the loading of multiple data sources with proper dependency management, load order optimization, and error handling.

## Purpose

After successfully loading a single data source in Module 6, Module 7 helps you:

1. **Manage dependencies** between data sources
2. **Optimize load order** for efficiency
3. **Implement parallel loading** strategies
4. **Handle errors** across multiple sources
5. **Track progress** for all sources
6. **Generate multi-source dashboard**

## When to Use This Module

- You have 2+ data sources to load
- Data sources have dependencies (e.g., customers before orders)
- You want to optimize loading performance
- You need coordinated error handling

**Skip this module if**: You only have one data source

## Key Concepts

### Load Order Optimization

Determine the optimal order to load sources:

```
Priority 1: Reference data (countries, states, products)
Priority 2: Master data (customers, vendors, employees)
Priority 3: Transactional data (orders, claims, transactions)
Priority 4: Derived data (aggregations, summaries)
```

### Dependency Management

Track dependencies between sources:

```yaml
dependencies:
  orders:
    requires: [customers, products]
  shipments:
    requires: [orders]
  returns:
    requires: [orders, shipments]
```

### Parallel Loading

Load independent sources in parallel:

```python
# Sequential (slow)
load_source('customers')  # 10 minutes
load_source('vendors')    # 10 minutes
# Total: 20 minutes

# Parallel (fast)
with ThreadPoolExecutor() as executor:
    executor.submit(load_source, 'customers')
    executor.submit(load_source, 'vendors')
# Total: 10 minutes
```

### Error Handling Strategies

1. **Fail Fast**: Stop all loading on first error
2. **Continue on Error**: Log errors, continue with other sources
3. **Retry with Backoff**: Retry failed sources with exponential backoff
4. **Partial Success**: Mark successful sources, retry only failed ones

## Orchestration Patterns

### Pattern 1: Sequential Loading

Simple, predictable, but slow:

```python
sources = ['customers', 'vendors', 'products', 'orders']
for source in sources:
    load_source(source)
```

### Pattern 2: Parallel Loading (Independent Sources)

Fast for independent sources:

```python
independent_sources = ['customers', 'vendors', 'products']
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(load_source, s) for s in independent_sources]
    wait(futures)
```

### Pattern 3: Dependency-Aware Loading

Respects dependencies:

```python
def load_with_dependencies(source, dependencies, loaded):
    # Wait for dependencies
    for dep in dependencies.get(source, []):
        if dep not in loaded:
            load_with_dependencies(dep, dependencies, loaded)
    
    # Load this source
    load_source(source)
    loaded.add(source)
```

### Pattern 4: Pipeline Loading

Streaming pipeline for large datasets:

```python
# Producer-consumer pattern
queue = Queue()

# Producer: Read and transform
def producer(source):
    for record in read_source(source):
        transformed = transform(record)
        queue.put(transformed)

# Consumer: Load to Senzing
def consumer():
    while True:
        record = queue.get()
        if record is None:
            break
        load_record(record)
```

## Multi-Source Dashboard

Track progress across all sources:

```
╔══════════════════════════════════════════════════════════╗
║           MULTI-SOURCE LOADING DASHBOARD                 ║
╠══════════════════════════════════════════════════════════╣
║ Source      │ Status    │ Progress │ Records │ Errors   ║
╠═════════════╪═══════════╪══════════╪═════════╪══════════╣
║ customers   │ ✅ Done   │ 100%     │ 50,000  │ 0        ║
║ vendors     │ ✅ Done   │ 100%     │ 2,500   │ 0        ║
║ products    │ 🔄 Loading│  67%     │ 33,500  │ 12       ║
║ orders      │ ⏸️ Waiting│   0%     │ 0       │ 0        ║
║ shipments   │ ⏸️ Waiting│   0%     │ 0       │ 0        ║
╚═════════════╧═══════════╧══════════╧═════════╧══════════╝

Total: 86,000 / 250,000 records (34%)
Estimated completion: 15 minutes
```

## Orchestration Script Template

```python
#!/usr/bin/env python3
"""
Multi-Source Orchestration Script
Coordinates loading of multiple data sources
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiSourceOrchestrator:
    def __init__(self, config: Dict):
        self.config = config
        self.sources = config['sources']
        self.dependencies = config.get('dependencies', {})
        self.loaded = set()
        self.failed = set()
        self.stats = {}
    
    def load_all(self, strategy='dependency-aware'):
        """Load all sources using specified strategy"""
        if strategy == 'sequential':
            self._load_sequential()
        elif strategy == 'parallel':
            self._load_parallel()
        elif strategy == 'dependency-aware':
            self._load_dependency_aware()
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _load_sequential(self):
        """Load sources sequentially"""
        for source in self.sources:
            self._load_source(source)
    
    def _load_parallel(self):
        """Load sources in parallel"""
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._load_source, source): source
                for source in self.sources
            }
            
            for future in as_completed(futures):
                source = futures[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Failed to load {source}: {e}")
                    self.failed.add(source)
    
    def _load_dependency_aware(self):
        """Load sources respecting dependencies"""
        for source in self.sources:
            self._load_with_dependencies(source)
    
    def _load_with_dependencies(self, source: str):
        """Load source after its dependencies"""
        if source in self.loaded or source in self.failed:
            return
        
        # Load dependencies first
        deps = self.dependencies.get(source, [])
        for dep in deps:
            if dep not in self.loaded:
                logger.info(f"{source} waiting for dependency: {dep}")
                self._load_with_dependencies(dep)
        
        # Load this source
        self._load_source(source)
    
    def _load_source(self, source: str):
        """Load a single source"""
        logger.info(f"Loading source: {source}")
        start_time = time.time()
        
        try:
            # TODO: Implement actual loading logic
            # load_records_from_source(source)
            
            # Simulate loading
            time.sleep(2)
            
            duration = time.time() - start_time
            self.stats[source] = {
                'status': 'success',
                'duration': duration,
                'records': 10000  # TODO: Get actual count
            }
            self.loaded.add(source)
            logger.info(f"✅ Loaded {source} in {duration:.1f}s")
            
        except Exception as e:
            logger.error(f"❌ Failed to load {source}: {e}")
            self.failed.add(source)
            self.stats[source] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def print_summary(self):
        """Print loading summary"""
        print("\n" + "="*60)
        print("MULTI-SOURCE LOADING SUMMARY")
        print("="*60)
        print(f"Total sources: {len(self.sources)}")
        print(f"Loaded: {len(self.loaded)}")
        print(f"Failed: {len(self.failed)}")
        
        if self.loaded:
            print("\n✅ Successfully loaded:")
            for source in self.loaded:
                stats = self.stats[source]
                print(f"  - {source}: {stats['records']:,} records in {stats['duration']:.1f}s")
        
        if self.failed:
            print("\n❌ Failed to load:")
            for source in self.failed:
                print(f"  - {source}: {self.stats[source]['error']}")
        
        print("="*60)

# Example configuration
config = {
    'sources': ['customers', 'vendors', 'products', 'orders'],
    'dependencies': {
        'orders': ['customers', 'products']
    }
}

if __name__ == '__main__':
    orchestrator = MultiSourceOrchestrator(config)
    orchestrator.load_all(strategy='dependency-aware')
    orchestrator.print_summary()
```

## Agent Behavior

When a user is in Module 7, the agent should:

1. **Identify all data sources** from previous modules
2. **Determine dependencies** between sources
3. **Recommend load order** based on dependencies
4. **Generate orchestration script** in `src/orchestration/`
5. **Configure parallel loading** if sources are independent
6. **Set up error handling** strategy
7. **Create progress dashboard**
8. **Test orchestration** with small samples first
9. **Document orchestration** in `docs/orchestration_strategy.md`

## Validation Gates

Before completing Module 7:

- [ ] All data sources identified
- [ ] Dependencies documented
- [ ] Load order determined
- [ ] Orchestration script created
- [ ] Error handling configured
- [ ] Progress tracking implemented
- [ ] Tested with sample data
- [ ] All sources loaded successfully

## Success Indicators

Module 7 is complete when:

- All data sources loaded successfully
- Dependencies respected
- Error handling working
- Progress tracking functional
- Multi-source dashboard generated
- Loading statistics documented

## Output Files

- `src/orchestration/load_all_sources.py` - Orchestration script
- `docs/orchestration_strategy.md` - Strategy documentation
- `docs/multi_source_dashboard.html` - Progress dashboard
- `logs/orchestration.log` - Loading logs

## Related Documentation

- `POWER.md` - Module 7 overview
- `steering/steering.md` - Module 7 workflow (to be added)
- `MODULE_6_SINGLE_SOURCE_LOADING.md` - Single source loading

## Version History

- **v3.0.0** (2026-03-17): Module 7 created for multi-source orchestration
