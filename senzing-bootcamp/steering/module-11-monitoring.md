---
inclusion: manual
---

# Module 11: Monitoring and Observability

**Purpose**: Set up comprehensive monitoring for production operations.

**Prerequisites**:

- ✅ Module 10 complete (security hardened)
- ✅ Monitoring tools selected
- ✅ Production environment identified

**Agent Workflow**:

1. **Select monitoring stack**:

   Ask: "What monitoring tools do you want to use?"

   Common stacks:
   - Prometheus + Grafana
   - CloudWatch (AWS)
   - Azure Monitor
   - Datadog
   - New Relic

   WAIT for response.

2. **Implement metrics collection**:

   Create `src/monitoring/metrics_collector.py`:

   ```python
   from prometheus_client import Counter, Histogram, Gauge

   # Define metrics
   records_loaded = Counter('records_loaded_total', 'Total records loaded')
   load_duration = Histogram('load_duration_seconds', 'Load duration')
   active_loaders = Gauge('active_loaders', 'Active loaders')

   # Use in code
   records_loaded.inc()
   load_duration.observe(duration)
   active_loaders.set(count)
   ```

3. **Implement structured logging**:

   Create `src/utils/logging_config.py`:

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
               'function': record.funcName
           }
           return json.dumps(log_data)
   ```

4. **Create dashboards**:

   Create Grafana dashboards in `monitoring/grafana/dashboards/`:
   - `loading_dashboard.json` - Loading metrics
   - `query_dashboard.json` - Query performance
   - `system_dashboard.json` - System resources
   - `error_dashboard.json` - Error rates

5. **Configure alerts**:

   Create alert rules in `monitoring/alerts/alert_rules.yml`:

   ```yaml
   groups:
     - name: senzing_alerts
       rules:
         - alert: HighErrorRate
           expr: rate(load_errors_total[5m]) > 0.01
           annotations:
             summary: "High error rate detected"

         - alert: SlowQueries
           expr: query_duration_seconds > 1.0
           annotations:
             summary: "Queries are slow"

         - alert: HighMemoryUsage
           expr: memory_usage_percent > 90
           annotations:
             summary: "Memory usage critical"
   ```

6. **Implement health checks**:

   Create `src/monitoring/health_checks.py`:

   ```python
   def check_database():
       """Check database connectivity"""
       try:
           # Test connection
           return True
       except:
           return False

   def check_senzing():
       """Check Senzing engine"""
       try:
           # Test engine
           return True
       except:
           return False

   def health_check():
       """Overall health check"""
       checks = {
           'database': check_database(),
           'senzing': check_senzing()
       }
       return all(checks.values()), checks
   ```

7. **Set up distributed tracing** (optional):

   For microservices:
   - OpenTelemetry
   - Jaeger
   - Zipkin

8. **Create runbooks**:

   Document in `docs/operations/runbooks/`:
   - `high_cpu.md` - What to do when CPU is high
   - `slow_queries.md` - How to diagnose slow queries
   - `data_quality_issues.md` - Handling data quality problems
   - `system_outage.md` - Incident response

9. **Test monitoring**:

   Trigger alerts intentionally:
   - Cause high error rate
   - Generate slow queries
   - Simulate resource exhaustion

   Verify alerts fire and runbooks work.

**Success Criteria**:

- ✅ Metrics collection implemented
- ✅ Dashboards created
- ✅ Alerts configured
- ✅ Health checks working
- ✅ Runbooks documented
- ✅ Monitoring tested
