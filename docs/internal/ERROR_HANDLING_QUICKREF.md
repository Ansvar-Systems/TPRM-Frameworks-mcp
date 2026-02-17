# Error Handling Quick Reference

## Import Exceptions

```python
from .exceptions import (
    DataLoadError,
    FrameworkNotFoundError,
    EvaluationError,
    IntegrationError,
    TPRMError,
    ValidationError,
)
from .storage import (
    AssessmentNotFoundError,
    QuestionnaireNotFoundError,
    StorageError,
)
from .logging_config import get_logger

logger = get_logger("module_name")
```

## Common Patterns

### 1. Framework Not Found

```python
try:
    fw_metadata = data_loader.get_framework_metadata(framework)
    if not fw_metadata:
        available = list(data_loader.frameworks.keys())
        raise FrameworkNotFoundError(framework, available)
except FrameworkNotFoundError as e:
    logger.warning("Framework not found", extra={"error": e.to_dict()})
    return [TextContent(type="text", text=f"Error: {e.message}")]
```

### 2. Questionnaire Not Found

```python
try:
    questionnaire = storage.get_questionnaire(questionnaire_id)
except QuestionnaireNotFoundError as e:
    logger.warning("Questionnaire not found", extra={"error": str(e)})
    return [TextContent(type="text", text=f"Error: {str(e)}")]
```

### 3. Storage Operations

```python
try:
    storage.save_questionnaire(questionnaire)
except StorageError as e:
    logger.error("Storage error", extra={"error": str(e)}, exc_info=True)
    return [TextContent(type="text", text=f"Error: Failed to save - {str(e)}")]
```

### 4. Validation Errors

```python
try:
    if not framework:
        raise ValidationError(
            parameter="framework",
            reason="Framework parameter is required",
            expected_value="sig_lite, caiq_v4, etc."
        )
except ValidationError as e:
    logger.warning("Validation failed", extra={"error": e.to_dict()})
    return [TextContent(type="text", text=f"Error: {e.message}")]
```

### 5. Integration Errors

```python
try:
    requirements = await get_dora_requirements(category)
    if not requirements:
        raise EURegulationsError(
            operation="get_dora_requirements",
            reason="No requirements returned",
            regulation="DORA"
        )
except EURegulationsError as e:
    logger.error("EU regulations integration failed", extra={"error": e.to_dict()}, exc_info=True)
    return [TextContent(type="text", text=f"Error: {e.message}")]
```

### 6. Catch-All Pattern (Tool Handlers)

```python
try:
    # Your operation logic here
    result = do_operation()
    return [TextContent(type="text", text=format_result(result))]

except SpecificError1 as e:
    logger.warning("Specific error 1", extra={"error": e.to_dict()})
    return [TextContent(type="text", text=f"Error: {e.message}")]

except SpecificError2 as e:
    logger.error("Specific error 2", extra={"error": str(e)}, exc_info=True)
    return [TextContent(type="text", text=f"Error: {str(e)}")]

except (ValueError, KeyError) as e:
    logger.error("Invalid parameters", extra={"error": str(e)}, exc_info=True)
    return [TextContent(type="text", text=f"Error: Invalid parameters - {str(e)}")]

except Exception as e:
    logger.error("Unexpected error", exc_info=True)
    return [TextContent(type="text", text=f"Error: Unexpected error - {str(e)}")]
```

## Exception Quick Reference

| Exception | Use Case | Parent |
|-----------|----------|--------|
| `TPRMError` | Base for all TPRM exceptions | `Exception` |
| `DataLoadError` | Data loading failures | `TPRMError` |
| `FrameworkNotFoundError` | Framework not found | `DataLoadError` |
| `InvalidFrameworkDataError` | Malformed framework data | `DataLoadError` |
| `SchemaValidationError` | Schema validation failure | `DataLoadError` |
| `EvaluationError` | Evaluation failures | `TPRMError` |
| `InvalidRubricError` | Invalid evaluation rubric | `EvaluationError` |
| `QuestionNotFoundError` | Question ID not found | `EvaluationError` |
| `InvalidResponseError` | Malformed vendor response | `EvaluationError` |
| `IntegrationError` | External service failures | `TPRMError` |
| `EURegulationsError` | EU regulations MCP issues | `IntegrationError` |
| `SecurityControlsError` | Security controls MCP issues | `IntegrationError` |
| `VendorIntelError` | Vendor intel MCP issues | `IntegrationError` |
| `ValidationError` | Input validation failures | `TPRMError` |
| `ConfigurationError` | Configuration issues | `TPRMError` |
| `StorageError` | Storage/database failures | `Exception` |
| `QuestionnaireNotFoundError` | Questionnaire not found | `StorageError` |
| `AssessmentNotFoundError` | Assessment not found | `StorageError` |

## Log Levels

| Level | Use Case | Include Stack Trace? |
|-------|----------|---------------------|
| `logger.warning()` | Expected errors, user mistakes | No |
| `logger.error()` | Unexpected errors needing investigation | Yes (`exc_info=True`) |
| `logger.critical()` | System-level failures | Yes (`exc_info=True`) |

## Structured Logging

```python
# For TPRMError subclasses
logger.error("Operation failed", extra={"error": e.to_dict()}, exc_info=True)

# For standard exceptions
logger.error("Operation failed", extra={"error": str(e)}, exc_info=True)

# Add additional context
logger.error(
    "Operation failed",
    extra={
        "error": e.to_dict(),
        "vendor": vendor_name,
        "questionnaire_id": questionnaire_id
    },
    exc_info=True
)
```

## Creating New Exceptions

```python
# In exceptions.py
class MyNewError(TPRMError):
    """Description of when this error occurs."""

    def __init__(
        self,
        param1: str,
        param2: Optional[str] = None
    ):
        """Initialize error with parameters."""
        details = {"param1": param1}
        if param2:
            details["param2"] = param2

        message = f"My new error occurred with {param1}"
        super().__init__(message, "MY_NEW_ERROR_CODE", details)
```

## Testing Exceptions

```python
def test_my_exception():
    """Test custom exception."""
    try:
        raise MyNewError("test_value", "optional_value")
    except MyNewError as e:
        assert e.error_code == "MY_NEW_ERROR_CODE"
        assert "test_value" in e.message
        assert "param1" in e.details
        error_dict = e.to_dict()
        assert "error_code" in error_dict
        assert "message" in error_dict
        assert "details" in error_dict
```

## Error Response Format

Always return errors as TextContent:

```python
return [TextContent(type="text", text=f"Error: {error_message}")]
```

**DO NOT:**
```python
raise Exception("This will crash the MCP server")
```

**DO:**
```python
return [TextContent(type="text", text=f"Error: {str(e)}")]
```

## Cheat Sheet

1. **Import exceptions at top of file**
2. **Use try-except in all tool handlers**
3. **Catch specific exceptions first**
4. **Log with appropriate level and extra context**
5. **Always return TextContent, never raise**
6. **Include exc_info=True for unexpected errors**
7. **Never log sensitive data**
8. **Use to_dict() for TPRMError subclasses**
