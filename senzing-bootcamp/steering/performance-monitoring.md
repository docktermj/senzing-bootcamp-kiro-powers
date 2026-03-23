---
inclusion: manual
---

# Performance Benchmarking and Monitoring

Track performance metrics to optimize and scale your entity resolution system.

## Key Metrics to Track

### 1. Transformation Performance
- Records processed per second
- Memory usage
- Error rate
- Data quality score

### 2. Loading Performance
- Records loaded per second
- Entity resolution time
- Database write throughput
- Match rate (entities created vs records loaded)

### 3. Query Performance
- Query response time
- Result accuracy
- Cache hit rate

## Performance Benchmarks Document

Create `docs/performance_benchmarks.md`:

```markdown
# Performance Benchmarks

## Baseline Metrics (Date: YYYY-MM-DD)

### Transformation Performance
- **Data Source**: Customer CRM
- **Record Count**: 50,000
- **Processing Time**: 5 minutes
- **Throughput**: 166 records/second
- **Memory Usage**: 512 MB
- **Error Rate**: 0.1%
- **Quality Score**: 85%

### Loading Performance
- **Data Source**: Customer CRM
- **Record Count**: 50,000
- **Loading Time**: 15 minutes
- **Throughput**: 55 records/second
- **Entities Created**: 42,000
- **Match Rate**: 16% (8,000 duplicates found)
- **Database Size**: 2.5 GB

### Query Performance
- **Query Type**: Find duplicates
- **Response Time**: 2.3 seconds
- **Results**: 4,200 duplicate entities
- **Accuracy**: 98% (manual validation of sample)

## Optimization Notes
- Batch size of 1000 records optimal for loading
- Index on DATA_SOURCE improves query performance by 40%
- PostgreSQL performs 3x faster than SQLite for >100K records

## Scaling Projections
- 1M records: ~2 hours transformation, ~6 hours loading
- 10M records: ~20 hours transformation, ~60 hours loading
- Recommend: Parallel processing for >1M records
```

## Performance Monitoring Script

Create `src/utils/performance_monitor.py`:

```python
import time
import psutil
import json

class PerformanceMonitor:
    def __init__(self):
        self.start_time = None
        self.metrics = {}
    
    def start(self, operation_name):
        self.start_time = time.time()
        self.metrics[operation_name] = {
            "start_time": self.start_time,
            "start_memory": psutil.Process().memory_info().rss / 1024 / 1024  # MB
        }
    
    def end(self, operation_name, record_count=0):
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        duration = end_time - self.metrics[operation_name]["start_time"]
        throughput = record_count / duration if duration > 0 else 0
        
        self.metrics[operation_name].update({
            "end_time": end_time,
            "duration_seconds": duration,
            "record_count": record_count,
            "throughput_per_second": throughput,
            "memory_used_mb": end_memory - self.metrics[operation_name]["start_memory"]
        })
        
        return self.metrics[operation_name]
    
    def save_metrics(self, filepath="monitoring/metrics.json"):
        with open(filepath, "w") as f:
            json.dump(self.metrics, f, indent=2)
```

## Monitoring Dashboard

Create `src/utils/generate_dashboard.py` (all source code must be in `src/`) to generate `monitoring/dashboard.html` for visualizing metrics in real-time. The dashboard should display:
- Total records loaded per data source
- Total entities created
- Match rate percentage
- Error rate and error details
- Loading performance over time
- Data quality metrics

## Health Checks

Create `src/utils/health_check.py`:

```python
import psutil
import json
from datetime import datetime

def check_system_health():
    health = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "checks": {}
    }
    
    # Disk space
    disk = psutil.disk_usage('/')
    health["checks"]["disk_space"] = {
        "free_gb": disk.free / (1024**3),
        "percent_used": disk.percent,
        "status": "ok" if disk.percent < 90 else "warning"
    }
    
    # Memory
    memory = psutil.virtual_memory()
    health["checks"]["memory"] = {
        "available_gb": memory.available / (1024**3),
        "percent_used": memory.percent,
        "status": "ok" if memory.percent < 90 else "warning"
    }
    
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    health["checks"]["cpu"] = {
        "percent_used": cpu_percent,
        "status": "ok" if cpu_percent < 80 else "warning"
    }
    
    # Overall status
    if any(check["status"] == "warning" for check in health["checks"].values()):
        health["status"] = "warning"
    
    return health

if __name__ == "__main__":
    health = check_system_health()
    print(json.dumps(health, indent=2))
    
    # Save to monitoring directory
    with open("monitoring/health_status.json", "w") as f:
        json.dump(health, f, indent=2)
```

## Monitoring Configuration

Create `config/monitoring_config.yaml`:

```yaml
monitoring:
  enabled: true
  interval_seconds: 300  # Check every 5 minutes
  
  metrics:
    - name: records_loaded
      query: "SELECT COUNT(*) FROM records"
      threshold: 1000000
      alert_on: exceeds
      
    - name: error_rate
      query: "SELECT COUNT(*) FROM errors / COUNT(*) FROM records"
      threshold: 0.05  # 5%
      alert_on: exceeds
      
    - name: loading_throughput
      query: "SELECT COUNT(*) FROM records WHERE loaded_at > NOW() - INTERVAL '1 hour'"
      threshold: 1000
      alert_on: below
      
    - name: data_quality_score
      query: "SELECT AVG(quality_score) FROM data_quality_metrics"
      threshold: 70
      alert_on: below

  alerts:
    email:
      enabled: true
      recipients:
        - admin@example.com
      smtp_server: smtp.example.com
      
    slack:
      enabled: false
      webhook_url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
      
    log:
      enabled: true
      log_file: logs/monitoring.log

  health_checks:
    - name: database_connection
      type: database
      connection_string: ${DATABASE_URL}
      
    - name: senzing_engine
      type: senzing
      config: ${SENZING_CONFIG}
      
    - name: disk_space
      type: system
      path: /var/opt/senzing
      threshold_gb: 10
```

## When to Load This Guide

Load this steering file when:
- Starting Module 6 (before loading data)
- Starting Module 9 (performance testing)
- User asks about performance optimization
- Setting up production monitoring (Module 11)
- Troubleshooting performance issues
- Planning for scale (large datasets)
