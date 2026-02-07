# Error Handling Implementation Summary

## Overview

Implemented a robust error handling system with custom exception hierarchy for the TPRM Frameworks MCP server. The system provides structured error reporting, proper logging integration, and graceful error recovery.

## Files Created/Modified

### 1. **src/tprm_frameworks_mcp/exceptions.py** (NEW)

Created comprehensive custom exception hierarchy with:

#### Base Exception
- `TPRMError`: Base class for all TPRM exceptions with structured error reporting

#### Specialized Exceptions

**Data Loading Errors:**
- `DataLoadError`: Base for data loading issues
- `FrameworkNotFoundError`: Framework not found or not loaded
- `InvalidFrameworkDataError`: Framework data is malformed
- `SchemaValidationError`: Data doesn't match expected schema

**Evaluation Errors:**
- `EvaluationError`: Base for evaluation issues
- `InvalidRubricError`: Evaluation rubric is invalid
- `QuestionNotFoundError`: Question ID not found in questionnaire
- `InvalidResponseError`: Vendor response is malformed

**Integration Errors:**
- `IntegrationError`: Base for external service issues
- `EURegulationsError`: EU Regulations MCP integration failures
- `SecurityControlsError`: Security Controls MCP integration failures
- `VendorIntelError`: Vendor Intelligence MCP integration failures

**Other Errors:**
- `ValidationError`: Input validation failures
- `ConfigurationError`: Server configuration issues

#### Key Features
- `to_dict()` method for structured logging
- Error codes for machine-readable identification
- Optional details dictionary for additional context
- Human-readable error messages
- Proper inheritance hierarchy

### 2. **src/tprm_frameworks_mcp/server.py** (MODIFIED)

Updated tool handlers with specific exception handling:

#### Import Section
- Added exception imports
- Added storage exception imports (QuestionnaireNotFoundError, AssessmentNotFoundError, StorageError)

#### Tool Handlers Updated

**generate_questionnaire:**
```python
try:
    # Generate questionnaire logic
except FrameworkNotFoundError as e:
    logger.warning("Framework not found", extra={"error": e.to_dict()})
    return [TextContent(type="text", text=f"Error: {e.message}")]
except StorageError as e:
    logger.error("Failed to save questionnaire", extra={"error": e.to_dict()}, exc_info=True)
    return [TextContent(type="text", text=f"Error: Failed to save questionnaire - {e.message}")]
except (ValueError, KeyError) as e:
    logger.error("Invalid questionnaire parameters", extra={"error": str(e)}, exc_info=True)
    return [TextContent(type="text", text=f"Error: Invalid parameters - {str(e)}")]
except Exception as e:
    logger.error("Unexpected error generating questionnaire", exc_info=True)
    return [TextContent(type="text", text=f"Error: Unexpected error - {str(e)}")]
```

**evaluate_response:**
```python
try:
    # Evaluation logic
except QuestionnaireNotFoundError as e:
    logger.warning("Questionnaire not found for evaluation", extra={"error": str(e)})
    return [TextContent(type="text", text=f"Error: {str(e)}")]
except StorageError as e:
    logger.error("Storage error during evaluation", extra={"error": str(e)}, exc_info=True)
    return [TextContent(type="text", text=f"Error: Failed to save assessment - {str(e)}")]
except (ValueError, KeyError) as e:
    logger.error("Invalid evaluation parameters", extra={"error": str(e)}, exc_info=True)
    return [TextContent(type="text", text=f"Error: Invalid parameters - {str(e)}")]
except Exception as e:
    logger.error("Unexpected error during evaluation", exc_info=True)
    return [TextContent(type="text", text=f"Error: Unexpected error - {str(e)}")]
```

**compare_assessments:**
```python
try:
    comparison = storage.compare_assessments(vendor_name, assessment_id_1, assessment_id_2)
except AssessmentNotFoundError as e:
    logger.warning("Assessment not found for comparison", extra={"error": str(e)})
    return [TextContent(type="text", text=f"Error: Assessment not found - {str(e)}")]
except StorageError as e:
    logger.error("Storage error during comparison", extra={"error": str(e)}, exc_info=True)
    return [TextContent(type="text", text=f"Error: Failed to compare assessments - {str(e)}")]
except Exception as e:
    logger.error("Unexpected error comparing assessments", exc_info=True)
    return [TextContent(type="text", text=f"Error: Unexpected error - {str(e)}")]
```

**health_check:**
```python
except DataLoadError as e:
    logger.error("Data loading error in health check", extra={"error": e.to_dict()}, exc_info=True)
    return {
        "status": "unhealthy",
        "error": f"Data loading error: {e.message}",
        "timestamp": datetime.now(UTC).isoformat()
    }
except StorageError as e:
    logger.error("Storage error in health check", extra={"error": str(e)}, exc_info=True)
    return {
        "status": "degraded",
        "error": f"Storage error: {str(e)}",
        "timestamp": datetime.now(UTC).isoformat()
    }
except Exception as e:
    logger.critical("Health check failed", exc_info=True)
    return {
        "status": "unhealthy",
        "error": str(e),
        "timestamp": datetime.now(UTC).isoformat()
    }
```

### 3. **test_error_handling.py** (NEW)

Created comprehensive test suite for exception handling:
- Tests all custom exception types
- Verifies exception hierarchy
- Tests to_dict() method for structured logging
- Validates error codes and messages
- All tests passing

## Error Handling Pattern

### 1. **Catch Specific Exceptions First**
Always catch specific exceptions before generic ones:

```python
try:
    operation()
except FrameworkNotFoundError as e:
    # Handle specific case
    logger.warning("Framework not found", extra={"error": e.to_dict()})
    return error_response(e.message)
except DataLoadError as e:
    # Handle broader case
    logger.error("Data load error", extra={"error": e.to_dict()}, exc_info=True)
    return error_response(e.message)
except Exception as e:
    # Catch all unexpected errors
    logger.error("Unexpected error", exc_info=True)
    return error_response(str(e))
```

### 2. **Use Appropriate Log Levels**
- `logger.warning()`: Expected errors (e.g., framework not found, invalid input)
- `logger.error()`: Unexpected errors that need investigation
- `logger.critical()`: System-level failures (e.g., health check failures)

### 3. **Never Raise to MCP Layer**
All tool handlers catch exceptions and return TextContent error messages:

```python
return [TextContent(type="text", text=f"Error: {error_message}")]
```

### 4. **Structured Logging**
Use `extra` parameter for structured logging:

```python
logger.error(
    "Operation failed",
    extra={"error": e.to_dict()},
    exc_info=True  # Include stack trace
)
```

## Benefits

### 1. **Better Error Messages**
- Specific exception types provide clear error messages
- Additional context in details dictionary
- Suggestions for fixes (e.g., available frameworks)

### 2. **Improved Debugging**
- Structured logging with error codes
- Stack traces for unexpected errors
- Context preservation in exception details

### 3. **Graceful Degradation**
- Health check can report "degraded" status for storage issues
- Operations fail gracefully without crashing the server
- User-friendly error messages returned to clients

### 4. **Maintainability**
- Clear exception hierarchy
- Consistent error handling patterns
- Easy to add new exception types
- Self-documenting error codes

## Testing

Run the error handling tests:

```bash
python3 test_error_handling.py
```

Expected output:
```
Testing TPRM Error Handling
==================================================
✓ FrameworkNotFoundError caught
✓ EvaluationError caught
✓ StorageError caught
✓ ValidationError caught
✓ Exception to_dict method works
✓ Exception hierarchy is correct
==================================================
✓ All error handling tests passed!
```

## Future Enhancements

### Phase 3.5: Enhanced Error Recovery
1. **Retry Logic**: Automatic retry for transient errors
2. **Circuit Breaker**: Prevent cascading failures
3. **Error Metrics**: Track error rates and types
4. **Error Aggregation**: Group similar errors for reporting

### Phase 4: Integration Error Handling
1. **Timeout Handling**: Graceful timeout for external services
2. **Fallback Strategies**: Default behavior when integrations fail
3. **Error Propagation**: Pass errors from integrated services
4. **Service Health Monitoring**: Track integration health

## Best Practices

### DO:
- ✅ Catch specific exceptions first
- ✅ Log with appropriate severity levels
- ✅ Include context in exception details
- ✅ Return user-friendly error messages
- ✅ Use structured logging (extra parameter)
- ✅ Add exc_info=True for unexpected errors

### DON'T:
- ❌ Catch generic Exception first
- ❌ Raise exceptions from tool handlers
- ❌ Log sensitive data (passwords, keys)
- ❌ Use print() instead of logger
- ❌ Ignore exceptions silently
- ❌ Return stack traces to users

## Integration with Existing Code

The error handling system integrates with:

1. **Logging System** (`logging_config.py`): Structured logging with JSON support
2. **Storage Layer** (`storage.py`): Uses existing StorageError hierarchy
3. **Data Loader** (`data_loader.py`): FrameworkNotFoundError for missing frameworks
4. **Evaluation Engine** (`evaluation/rubric.py`): EvaluationError for scoring issues

## Conclusion

The robust error handling system provides:
- Clear error messages for users
- Detailed context for debugging
- Graceful error recovery
- Consistent error patterns
- Structured logging support
- Maintainable exception hierarchy

All tool handlers now follow the error handling pattern and never raise exceptions to the MCP layer.
