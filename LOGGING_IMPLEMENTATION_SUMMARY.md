# Production Logging System - Implementation Summary

## Overview
Successfully implemented a production-grade logging system for the TPRM Frameworks MCP server with JSON structured logging and comprehensive request tracking.

## Components Implemented

### 1. logging_config.py
**Location:** `src/tprm_frameworks_mcp/logging_config.py`

**Features:**
- Centralized logging configuration
- JSON structured logging using `python-json-logger`
- Environment variable configuration:
  - `TPRM_LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
  - `TPRM_LOG_FORMAT`: json or text (default: json)
- Field renaming for consistency (asctime → timestamp, levelname → level)
- Module-level logger support via `get_logger()`

**Key Functions:**
```python
def setup_logging() -> logging.Logger
def get_logger(name: str | None = None) -> logging.Logger
```

### 2. Updated pyproject.toml
**Added dependencies:**
- `python-json-logger>=2.0.7`
- `psutil>=5.9.0` (already present for health checks)

### 3. Updated server.py
**Changes:**
- Imported `setup_logging` from `.logging_config`
- Initialized module-level logger: `logger = setup_logging()`
- Replaced all print() statements with structured logger calls
- Added request logging wrapper to `call_tool()` function

**Print Statements Replaced (11 total):**
1. Health check failure warning → `logger.error()`
2. Server starting message → `logger.info()`
3. Frameworks loaded → `logger.info()`
4. Tools available → `logger.info()`
5. Memory status → `logger.info()`
6. Storage path → `logger.info()` (consolidated)
7. Questionnaires count → (part of storage info)
8. Assessments count → (part of storage info)
9. Vendors count → (part of storage info)
10. Database size → (part of storage info)
11. Storage warning → `logger.warning()`

### 4. Request Logging Implementation
Added comprehensive request tracking to all tool invocations:

```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]

    logger.info(
        "Tool invocation started",
        extra={
            "tool_name": name,
            "request_id": request_id,
            "arguments": arguments
        }
    )

    try:
        result = await _handle_tool_call(name, arguments)
        duration_ms = round((time.time() - start_time) * 1000, 2)

        logger.info(
            "Tool invocation completed",
            extra={
                "tool_name": name,
                "request_id": request_id,
                "duration_ms": duration_ms,
                "status": "success"
            }
        )

        return result
    except Exception as e:
        duration_ms = round((time.time() - start_time) * 1000, 2)

        logger.error(
            "Tool invocation failed",
            extra={
                "tool_name": name,
                "request_id": request_id,
                "duration_ms": duration_ms,
                "error": str(e),
                "status": "error"
            },
            exc_info=True
        )
        raise
```

## Log Output Format

### JSON Format (default)
```json
{
  "timestamp": "2026-02-07T09:24:15.919232+00:00",
  "logger": "tprm_frameworks_mcp",
  "level": "INFO",
  "message": "Tool invocation completed",
  "tool_name": "generate_questionnaire",
  "request_id": "a1b2c3d4",
  "duration_ms": 42.5,
  "status": "success"
}
```

### Text Format (for development)
Set `TPRM_LOG_FORMAT=text`:
```
2026-02-07 09:24:15 [INFO] tprm_frameworks_mcp: Tool invocation completed
```

## Benefits

### Production-Ready Features
1. **Structured Logging**: JSON format for easy parsing by log aggregators (Splunk, ELK, Datadog)
2. **Request Tracking**: Unique request_id for tracing requests through the system
3. **Performance Monitoring**: Duration tracking for all tool invocations
4. **Error Context**: Comprehensive error logging with stack traces
5. **Configuration Flexibility**: Environment-based log level and format control

### Operational Improvements
1. **Debugging**: Request IDs enable tracing specific requests
2. **Monitoring**: Duration metrics for performance analysis
3. **Alerting**: Structured errors enable automated alerting
4. **Compliance**: Complete audit trail of all tool invocations
5. **Troubleshooting**: Rich context in every log entry

## Testing Results

All tests passed successfully:
- ✓ Module imports correctly
- ✓ Logger initializes with correct configuration
- ✓ Structured logging works with extra fields
- ✓ Server module integrates seamlessly
- ✓ No print() statements remain in server.py

## Usage Examples

### Basic Logging
```python
from tprm_frameworks_mcp.logging_config import get_logger

logger = get_logger("storage")
logger.info("Database connection established", extra={"db_path": "/path/to/db"})
```

### Error Logging
```python
try:
    result = perform_operation()
except Exception as e:
    logger.error(
        "Operation failed",
        extra={"operation": "vendor_assessment", "vendor_id": "12345"},
        exc_info=True
    )
```

### Development vs Production
```bash
# Development (human-readable)
export TPRM_LOG_FORMAT=text
export TPRM_LOG_LEVEL=DEBUG

# Production (machine-parseable)
export TPRM_LOG_FORMAT=json
export TPRM_LOG_LEVEL=INFO
```

## Integration with Log Aggregators

### Splunk
```splunk
index=tprm sourcetype=json
| spath
| search tool_name="generate_questionnaire" status="error"
| stats avg(duration_ms) by request_id
```

### ELK Stack
```json
{
  "filter": {
    "bool": {
      "must": [
        { "match": { "tool_name": "evaluate_response" }},
        { "range": { "duration_ms": { "gte": 1000 }}}
      ]
    }
  }
}
```

### Datadog
Logs automatically tagged with:
- `service:tprm-frameworks-mcp`
- `tool_name:<tool>`
- `status:<success|error>`

## Next Steps (Future Enhancements)

1. **Log Rotation**: Add file-based logging with rotation
2. **Sampling**: Implement sampling for high-volume environments
3. **Metrics Integration**: Export duration metrics to Prometheus
4. **Distributed Tracing**: Add OpenTelemetry integration
5. **Log Levels per Module**: Fine-grained control over log verbosity

## Files Modified
- ✓ `src/tprm_frameworks_mcp/logging_config.py` (created)
- ✓ `pyproject.toml` (updated dependencies)
- ✓ `src/tprm_frameworks_mcp/server.py` (integrated logging)

## Verification
```bash
# Test logging system
python3 -c "from tprm_frameworks_mcp.logging_config import setup_logging; \
            logger = setup_logging(); \
            logger.info('Test', extra={'key': 'value'})"

# Verify no print statements remain
grep -r "print(" src/tprm_frameworks_mcp/server.py
# (should return no results)

# Run server
python3 -m tprm_frameworks_mcp
```

## Conclusion
The production logging system is fully implemented and tested. All print statements have been replaced with structured logging, comprehensive request tracking is in place, and the system is ready for production deployment with industry-standard log aggregators.
