# Logging Quick Reference - TPRM Frameworks MCP

## Configuration

### Environment Variables
```bash
# Log level (default: INFO)
export TPRM_LOG_LEVEL=DEBUG|INFO|WARNING|ERROR|CRITICAL

# Log format (default: json)
export TPRM_LOG_FORMAT=json|text
```

## Usage in Code

### Import and Initialize
```python
from tprm_frameworks_mcp.logging_config import get_logger

# Get module-specific logger
logger = get_logger("storage")
logger = get_logger("evaluator")
logger = get_logger("data_loader")
```

### Basic Logging
```python
# Info level
logger.info("Database initialized")

# With structured context
logger.info(
    "Operation completed",
    extra={
        "operation": "vendor_assessment",
        "vendor_id": "12345",
        "duration_ms": 42.5
    }
)
```

### Error Logging
```python
try:
    perform_operation()
except Exception as e:
    logger.error(
        "Operation failed",
        extra={"operation": "generate_questionnaire", "error_type": type(e).__name__},
        exc_info=True  # Include stack trace
    )
```

### Performance Tracking
```python
import time

start = time.time()
# ... perform operation ...
duration_ms = round((time.time() - start) * 1000, 2)

logger.info(
    "Operation completed",
    extra={"operation": "evaluate_response", "duration_ms": duration_ms}
)
```

## Log Output Examples

### JSON Format (Production)
```json
{
  "timestamp": "2026-02-07T09:24:15.919232+00:00",
  "logger": "tprm_frameworks_mcp.storage",
  "level": "INFO",
  "message": "Database initialized",
  "database_path": "/var/lib/tprm/tprm.db",
  "total_vendors": 42
}
```

### Text Format (Development)
```
2026-02-07 09:24:15 [INFO] tprm_frameworks_mcp.storage: Database initialized
```

## Common Patterns

### Request Tracking
```python
import uuid

request_id = str(uuid.uuid4())[:8]

logger.info("Request started", extra={"request_id": request_id})
# ... process request ...
logger.info("Request completed", extra={"request_id": request_id})
```

### Conditional Logging
```python
if logger.isEnabledFor(logging.DEBUG):
    logger.debug("Detailed info", extra={"data": complex_object})
```

### Context Managers
```python
class LoggedOperation:
    def __init__(self, operation_name):
        self.operation_name = operation_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"{self.operation_name} started")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = round((time.time() - self.start_time) * 1000, 2)
        if exc_type:
            logger.error(
                f"{self.operation_name} failed",
                extra={"duration_ms": duration, "error": str(exc_val)},
                exc_info=True
            )
        else:
            logger.info(
                f"{self.operation_name} completed",
                extra={"duration_ms": duration}
            )

# Usage
with LoggedOperation("generate_questionnaire"):
    # ... operation code ...
    pass
```

## Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| DEBUG | Detailed diagnostic information | Variable values, function calls |
| INFO | General informational messages | Operation start/complete, state changes |
| WARNING | Unexpected but recoverable issues | Deprecated usage, fallback behavior |
| ERROR | Error events that might still allow the app to continue | Failed operations, validation errors |
| CRITICAL | Serious errors causing application failure | Database unavailable, configuration missing |

## Best Practices

1. **Use Structured Logging**: Always include context in `extra` dict
2. **Consistent Field Names**: Use standard fields like `request_id`, `duration_ms`, `status`
3. **Don't Log Secrets**: Never log passwords, API keys, or PII
4. **Include Stack Traces**: Use `exc_info=True` for error logs
5. **Log at Boundaries**: Log at entry/exit of major operations
6. **Performance**: Avoid expensive operations in log statements (use lazy evaluation)

## Query Examples

### Find Slow Operations
```bash
# JSON format (jq)
cat logs.json | jq 'select(.duration_ms > 1000)'

# ELK
duration_ms:>1000 AND status:success

# Splunk
index=tprm duration_ms>1000 status=success
```

### Track Request Flow
```bash
# Find all logs for a specific request
cat logs.json | jq 'select(.request_id == "a1b2c3d4")'

# ELK
request_id:"a1b2c3d4"
```

### Error Analysis
```bash
# Find all errors with stack traces
cat logs.json | jq 'select(.level == "ERROR")'

# ELK
level:ERROR AND tool_name:*

# Splunk
index=tprm level=ERROR | stats count by tool_name
```

## Troubleshooting

### No Log Output
```bash
# Check log level
echo $TPRM_LOG_LEVEL

# Set to DEBUG temporarily
export TPRM_LOG_LEVEL=DEBUG
python3 -m tprm_frameworks_mcp
```

### JSON Parsing Errors
```bash
# Validate JSON format
cat logs.json | jq empty

# Switch to text format for debugging
export TPRM_LOG_FORMAT=text
```

### Too Much Output
```bash
# Reduce verbosity
export TPRM_LOG_LEVEL=WARNING

# Filter specific modules (future feature)
export TPRM_LOG_MODULES=storage:WARNING,server:INFO
```

## Integration

### Systemd Journal
```bash
# View logs
journalctl -u tprm-frameworks-mcp -f

# With JSON parsing
journalctl -u tprm-frameworks-mcp -o json | jq
```

### Docker
```yaml
version: '3'
services:
  tprm-mcp:
    environment:
      - TPRM_LOG_LEVEL=INFO
      - TPRM_LOG_FORMAT=json
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Kubernetes
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: tprm-config
data:
  TPRM_LOG_LEVEL: "INFO"
  TPRM_LOG_FORMAT: "json"
```
