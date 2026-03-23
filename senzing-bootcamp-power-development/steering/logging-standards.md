---
inclusion: always
---

# Logging Standards

**Version**: 1.0  
**Last Updated**: 2026-03-17

This document defines logging standards for all Senzing Boot Camp code.

---

## Overview

Consistent logging enables:
- Easier debugging
- Better monitoring
- Audit trails
- Performance analysis
- Troubleshooting

---

## Log Levels

### DEBUG
**When**: Detailed diagnostic information  
**Examples**:
- Variable values
- Function entry/exit
- Detailed state information

```python
logger.debug(f"Processing record: {record_id}")
logger.debug(f"Batch size: {batch_size}, Current batch: {batch_num}")
```

### INFO
**When**: General informational messages  
**Examples**:
- Application start/stop
- Major milestones
- Progress updates

```python
logger.info("Starting data load")
logger.info(f"Loaded {count:,} records successfully")
logger.info("Application initialized")
```

### WARNING
**When**: Unexpected but recoverable situations  
**Examples**:
- Missing optional data
- Deprecated features
- Performance degradation

```python
logger.warning(f"Missing email for record {record_id}")
logger.warning("Batch size exceeds recommended maximum")
logger.warning("Database connection slow (>1s)")
```

### ERROR
**When**: Error conditions that don't stop execution  
**Examples**:
- Failed record processing
- Recoverable errors
- Invalid data

```python
logger.error(f"Failed to process record {record_id}: {error}")
logger.error(f"Database query failed, retrying: {error}")
```

### CRITICAL
**When**: Severe errors that may stop execution  
**Examples**:
- Database connection lost
- Configuration errors
- System failures

```python
logger.critical("Database connection failed after 3 retries")
logger.critical("Invalid configuration: missing required field")
```

---

## Structured Logging

### Standard Format

Use JSON for structured logs:

```python
import logging
import json
from datetime import datetime

def log_event(logger, level, event_type, **kwargs):
    """Log structured event"""
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        **kwargs
    }
    getattr(logger, level)(json.dumps(log_data))

# Usage
log_event(logger, 'info', 'record_loaded',
          data_source='CUSTOMERS',
          record_id='1001',
          duration_ms=15)
```

### Standard Fields

Include these fields in all structured logs:

- `timestamp` - ISO 8601 format (UTC)
- `event_type` - Event category
- `level` - Log level
- `message` - Human-readable message
- `module` - Python module name
- `function` - Function name

Optional fields:
- `data_source` - Senzing data source
- `record_id` - Record identifier
- `entity_id` - Entity identifier
- `duration_ms` - Operation duration
- `error` - Error message
- `stack_trace` - Stack trace (for errors)

---

## Configuration

### Basic Setup

```python
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/application.log')
    ]
)

logger = logging.getLogger(__name__)
```

### Advanced Setup

```python
import logging
import logging.handlers
from pathlib import Path

def setup_logging(log_dir='logs', log_level=logging.INFO):
    """Configure application logging"""
    
    # Create log directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('senzing_bootcamp')
    logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler (rotating)
    file_handler = logging.handlers.RotatingFileHandler(
        f'{log_dir}/application.log',
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - '
        '%(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
```

---

## Logging Patterns

### Application Lifecycle

```python
logger.info("Application starting")
logger.info(f"Configuration loaded from {config_file}")
logger.info(f"Connected to database: {db_name}")

# ... application logic ...

logger.info(f"Processed {total_records:,} records")
logger.info("Application completed successfully")
```

### Data Loading

```python
logger.info(f"Starting load: {data_source}")
logger.info(f"Input file: {input_file}, Records: {total_records:,}")

for i, record in enumerate(records, 1):
    try:
        # Load record
        logger.debug(f"Loading record {i}/{total_records}")
        
        if i % 1000 == 0:
            logger.info(f"Progress: {i:,}/{total_records:,} "
                       f"({i/total_records*100:.1f}%)")
    
    except Exception as e:
        logger.error(f"Failed to load record {record_id}: {e}")
        error_count += 1

logger.info(f"Load complete: {success_count:,} success, "
           f"{error_count:,} errors")
```

### Error Handling

```python
try:
    result = risky_operation()
    logger.info("Operation succeeded")
    
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    
except ConnectionError as e:
    logger.error(f"Connection failed: {e}", exc_info=True)
    
except Exception as e:
    logger.critical(f"Unexpected error: {e}", exc_info=True)
    raise
```

### Performance Logging

```python
import time

start_time = time.time()

# Operation
process_data()

elapsed = time.time() - start_time
logger.info(f"Operation completed in {elapsed:.2f}s")

if elapsed > 10:
    logger.warning(f"Operation slow: {elapsed:.2f}s (expected <10s)")
```

### Context Logging

```python
import logging
from contextlib import contextmanager

@contextmanager
def log_context(operation, **kwargs):
    """Log operation with context"""
    logger.info(f"Starting: {operation}", extra=kwargs)
    start = time.time()
    
    try:
        yield
        elapsed = time.time() - start
        logger.info(f"Completed: {operation} ({elapsed:.2f}s)", extra=kwargs)
    
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"Failed: {operation} ({elapsed:.2f}s): {e}",
                    extra=kwargs, exc_info=True)
        raise

# Usage
with log_context('load_data', data_source='CUSTOMERS', file='data.csv'):
    load_data_from_file('data.csv')
```

---

## What to Log

### DO Log

✅ Application start/stop  
✅ Configuration loaded  
✅ Database connections  
✅ Major operations (load, query, export)  
✅ Progress milestones (every 1000 records)  
✅ Errors and exceptions  
✅ Performance metrics  
✅ Security events (authentication, authorization)  
✅ Data quality issues  

### DON'T Log

❌ Sensitive data (passwords, SSN, credit cards)  
❌ Full record contents (use record IDs)  
❌ Every single record (use sampling)  
❌ Redundant information  
❌ Debug logs in production (unless needed)  

### Sanitize Sensitive Data

```python
def sanitize_record(record):
    """Remove sensitive data from record for logging"""
    safe_record = record.copy()
    
    # Mask sensitive fields
    if 'SSN_NUMBER' in safe_record:
        safe_record['SSN_NUMBER'] = 'XXX-XX-' + safe_record['SSN_NUMBER'][-4:]
    
    if 'CREDIT_CARD' in safe_record:
        safe_record['CREDIT_CARD'] = 'XXXX-XXXX-XXXX-' + \
                                     safe_record['CREDIT_CARD'][-4:]
    
    return safe_record

# Usage
logger.debug(f"Processing record: {sanitize_record(record)}")
```

---

## Log Rotation

### File-based Rotation

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/application.log',
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5  # Keep 5 backup files
)
```

### Time-based Rotation

```python
from logging.handlers import TimedRotatingFileHandler

handler = TimedRotatingFileHandler(
    'logs/application.log',
    when='midnight',  # Rotate at midnight
    interval=1,  # Every day
    backupCount=30  # Keep 30 days
)
```

---

## Production Logging

### Configuration

```python
# Production settings
PRODUCTION_LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'json',
            'filename': 'logs/application.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}

import logging.config
logging.config.dictConfig(PRODUCTION_LOG_CONFIG)
```

### Centralized Logging

For production, send logs to centralized system:

```python
# Example: Send to syslog
from logging.handlers import SysLogHandler

syslog_handler = SysLogHandler(address=('localhost', 514))
logger.addHandler(syslog_handler)

# Example: Send to cloud logging (AWS CloudWatch, etc.)
# Use appropriate cloud SDK
```

---

## Monitoring Integration

### Metrics Logging

```python
class MetricsLogger:
    """Log metrics for monitoring"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def log_metric(self, metric_name, value, unit='count', **tags):
        """Log metric in structured format"""
        metric_data = {
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            'timestamp': datetime.utcnow().isoformat(),
            **tags
        }
        self.logger.info(f"METRIC: {json.dumps(metric_data)}")

# Usage
metrics = MetricsLogger(logger)
metrics.log_metric('records_loaded', 1000, unit='count',
                  data_source='CUSTOMERS')
metrics.log_metric('load_duration', 45.2, unit='seconds',
                  data_source='CUSTOMERS')
```

---

## Testing Logging

### Capture Logs in Tests

```python
import logging
import pytest

def test_logging(caplog):
    """Test that logging works correctly"""
    with caplog.at_level(logging.INFO):
        logger.info("Test message")
    
    assert "Test message" in caplog.text
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "INFO"
```

---

## Best Practices

1. **Use appropriate log levels** - Don't log everything as INFO
2. **Include context** - Add relevant identifiers (record_id, data_source)
3. **Be concise** - Log messages should be clear and brief
4. **Use structured logging** - JSON format for production
5. **Sanitize sensitive data** - Never log passwords, SSN, etc.
6. **Log exceptions with stack traces** - Use `exc_info=True`
7. **Monitor log volume** - Don't log too much in production
8. **Rotate logs** - Prevent disk space issues
9. **Test logging** - Verify logs in unit tests
10. **Document log format** - Help operations team understand logs

---

## Example: Complete Logging Setup

```python
#!/usr/bin/env python3
"""
Example application with proper logging.
"""

import logging
import logging.handlers
import sys
import json
from pathlib import Path
from datetime import datetime

def setup_logging(log_dir='logs', log_level=logging.INFO):
    """Configure application logging"""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger('my_app')
    logger.setLevel(log_level)
    
    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    
    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        f'{log_dir}/app.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - '
        '%(funcName)s:%(lineno)d - %(message)s'
    ))
    
    logger.addHandler(console)
    logger.addHandler(file_handler)
    
    return logger

def main():
    """Main application"""
    logger = setup_logging()
    
    logger.info("Application starting")
    
    try:
        # Application logic
        logger.info("Processing data")
        
        # Success
        logger.info("Application completed successfully")
        return 0
        
    except Exception as e:
        logger.critical(f"Application failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

**Document Owner**: Boot Camp Team  
**Last Updated**: 2026-03-17  
**Next Review**: 2026-06-17
