# Module 11: Monitoring and Observability

## Overview

Module 11 focuses on setting up comprehensive monitoring, logging, and alerting for production operations.

## Purpose

After security hardening in Module 10, Module 11 helps you:

1. **Set up distributed tracing** (request flow visibility)
2. **Configure structured logging** (searchable, analyzable logs)
3. **Implement metrics collection** (performance, health)
4. **Integrate APM** (Application Performance Monitoring)
5. **Configure alerting rules** (proactive issue detection)
6. **Create health check endpoints**
7. **Build monitoring dashboards**

## The Three Pillars of Observability

### 1. Metrics (What is happening?)

Quantitative measurements over time:

```python
from prometheus_client import Counter, Histogram, Gauge

# Counters
records_loaded = Counter('records_loaded_total', 'Total records loaded')
errors_total = Counter('errors_total', 'Total errors', ['error_type'])

# Histograms
query_duration = Histogram('query_duration_seconds', 'Query duration')
load_duration = Histogram('load_duration_seconds', 'Load duration')

# Gauges
active_connections = Gauge('active_connections', 'Active database connections')
queue_size = Gauge('queue_size', 'Records in queue')
```

### 2. Logs (What happened?)

Structured, searchable event records:

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
        }
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        return json.dumps(log_data)

# Configure structured logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger()
logger.addHandler(handler)
```

### 3. Traces (Why did it happen?)

Request flow through distributed systems:

```python
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor

tracer = trace.get_tracer(__name__)

@app.route('/api/search')
def search():
    with tracer.start_as_current_span("search_request") as span:
        span.set_attribute("user.id", get_user_id())
        
        with tracer.start_as_current_span("database_query"):
            results = query_database()
        
        with tracer.start_as_current_span("format_results"):
            formatted = format_results(results)
        
        return formatted
```

## Monitoring Stack Options

### Option 1: Prometheus + Grafana (Open Source)

**Prometheus**: Metrics collection and storage
**Grafana**: Visualization and dashboards

```yaml
# docker-compose.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Option 2: ELK Stack (Elasticsearch, Logstash, Kibana)

**Elasticsearch**: Log storage and search
**Logstash**: Log processing
**Kibana**: Log visualization

### Option 3: Cloud-Native

**AWS**: CloudWatch, X-Ray
**Azure**: Application Insights, Monitor
**GCP**: Cloud Monitoring, Cloud Trace

### Option 4: Commercial APM

**DataDog**: Full-stack monitoring
**New Relic**: Application performance
**Dynatrace**: AI-powered monitoring

## Key Metrics to Monitor

### Application Metrics

```python
# Transformation metrics
transformation_records_per_second = Gauge('transformation_throughput', 'Records/second')
transformation_errors = Counter('transformation_errors_total', 'Transformation errors')

# Loading metrics
loading_records_per_second = Gauge('loading_throughput', 'Records/second')
loading_errors = Counter('loading_errors_total', 'Loading errors')
loading_queue_size = Gauge('loading_queue_size', 'Records waiting to load')

# Query metrics
query_count = Counter('queries_total', 'Total queries')
query_duration = Histogram('query_duration_seconds', 'Query duration')
query_errors = Counter('query_errors_total', 'Query errors')
```

### System Metrics

```python
import psutil

# CPU
cpu_percent = Gauge('cpu_percent', 'CPU utilization')
cpu_percent.set(psutil.cpu_percent())

# Memory
memory_percent = Gauge('memory_percent', 'Memory utilization')
memory_percent.set(psutil.virtual_memory().percent)

# Disk
disk_percent = Gauge('disk_percent', 'Disk utilization')
disk_percent.set(psutil.disk_usage('/').percent)

# Network
network_bytes_sent = Counter('network_bytes_sent', 'Network bytes sent')
network_bytes_recv = Counter('network_bytes_recv', 'Network bytes received')
```

### Database Metrics

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Database size
SELECT pg_size_pretty(pg_database_size('senzing'));

-- Slow queries
SELECT query, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

## Alerting Rules

### Critical Alerts (Page immediately)

```yaml
# Prometheus alerting rules
groups:
  - name: critical
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"
      
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate: {{ $value }} errors/sec"
      
      - alert: DatabaseDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database is down"
```

### Warning Alerts (Investigate soon)

```yaml
  - name: warnings
    rules:
      - alert: HighCPU
        expr: cpu_percent > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage: {{ $value }}%"
      
      - alert: HighMemory
        expr: memory_percent > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage: {{ $value }}%"
      
      - alert: SlowQueries
        expr: query_duration_seconds > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow queries detected"
```

## Health Check Endpoints

```python
from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)

@app.route('/health')
def health():
    """Basic health check"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/health/ready')
def readiness():
    """Readiness check - can accept traffic?"""
    checks = {
        'database': check_database(),
        'senzing': check_senzing(),
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return jsonify({
        'status': 'ready' if all_healthy else 'not ready',
        'checks': checks
    }), status_code

@app.route('/health/live')
def liveness():
    """Liveness check - is process alive?"""
    return jsonify({'status': 'alive'}), 200

def check_database():
    """Check database connectivity"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        return True
    except:
        return False

def check_senzing():
    """Check Senzing engine"""
    try:
        # TODO: Implement Senzing health check
        return True
    except:
        return False
```

## Monitoring Dashboard

Create Grafana dashboard:

```json
{
  "dashboard": {
    "title": "Senzing Entity Resolution",
    "panels": [
      {
        "title": "Records Loaded",
        "targets": [
          {
            "expr": "rate(records_loaded_total[5m])"
          }
        ]
      },
      {
        "title": "Query Performance",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, query_duration_seconds)"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(errors_total[5m])"
          }
        ]
      },
      {
        "title": "System Resources",
        "targets": [
          {
            "expr": "cpu_percent"
          },
          {
            "expr": "memory_percent"
          }
        ]
      }
    ]
  }
}
```

## Log Aggregation

### Structured Logging Example

```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def log(self, level, message, **kwargs):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            **kwargs
        }
        self.logger.log(getattr(logging, level), json.dumps(log_entry))
    
    def info(self, message, **kwargs):
        self.log('INFO', message, **kwargs)
    
    def error(self, message, **kwargs):
        self.log('ERROR', message, **kwargs)
    
    def warning(self, message, **kwargs):
        self.log('WARNING', message, **kwargs)

# Usage
logger = StructuredLogger('senzing')
logger.info('Record loaded', 
    record_id='12345',
    data_source='CUSTOMERS',
    duration_ms=25)
```

## Agent Behavior

When a user is in Module 11, the agent should:

1. **Choose monitoring stack** (Prometheus/Grafana, ELK, Cloud, APM)
2. **Implement metrics collection**
3. **Configure structured logging**
4. **Set up distributed tracing** (if applicable)
5. **Create health check endpoints**
6. **Configure alerting rules**
7. **Build monitoring dashboards**
8. **Test alerts** (trigger test alerts)
9. **Document monitoring setup** in `docs/monitoring_guide.md`
10. **Create runbooks** for common alerts

## Validation Gates

Before completing Module 11:

- [ ] Monitoring stack deployed
- [ ] Metrics being collected
- [ ] Logs being aggregated
- [ ] Tracing configured (if applicable)
- [ ] Health checks working
- [ ] Alerts configured
- [ ] Dashboards created
- [ ] Runbooks documented
- [ ] Monitoring tested

## Success Indicators

Module 11 is complete when:

- All metrics being collected
- Logs searchable and analyzable
- Dashboards showing real-time data
- Alerts triggering correctly
- Health checks responding
- Runbooks documented
- Team trained on monitoring tools

## Output Files

- `config/prometheus.yml` - Prometheus configuration
- `config/grafana_dashboards/` - Dashboard definitions
- `config/alerting_rules.yml` - Alert rules
- `docs/monitoring_guide.md` - Monitoring documentation
- `docs/runbooks/` - Alert runbooks

## Related Documentation

- `POWER.md` - Module 11 overview
- `steering/steering.md` - Module 11 workflow (to be added)
- `steering/performance-monitoring.md` - Performance monitoring details

## Version History

- **v3.0.0** (2026-03-17): Module 11 created for monitoring and observability
