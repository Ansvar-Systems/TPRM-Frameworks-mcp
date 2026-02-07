"""Custom exception hierarchy for TPRM Frameworks MCP server.

This module provides a structured exception hierarchy for better error handling
and reporting throughout the TPRM system. All exceptions inherit from TPRMError
and include error codes and optional details for structured logging.

Exception Hierarchy:
    TPRMError (base)
    ├── DataLoadError
    │   ├── FrameworkNotFoundError
    │   ├── InvalidFrameworkDataError
    │   └── SchemaValidationError
    ├── EvaluationError
    │   ├── InvalidRubricError
    │   ├── QuestionNotFoundError
    │   └── InvalidResponseError
    ├── IntegrationError
    │   ├── EURegulationsError
    │   ├── SecurityControlsError
    │   └── VendorIntelError
    └── StorageError (defined in storage.py)
        ├── QuestionnaireNotFoundError
        └── AssessmentNotFoundError

Usage:
    from .exceptions import FrameworkNotFoundError, EvaluationError

    # Raise with details
    raise FrameworkNotFoundError(
        framework="sig_full",
        available_frameworks=["sig_lite", "caiq_v4"]
    )

    # Catch specific exceptions
    try:
        result = operation()
    except FrameworkNotFoundError as e:
        logger.warning("Framework not found", extra={"error": e.to_dict()})
        return error_response(e.message)
    except TPRMError as e:
        logger.error("TPRM operation failed", extra={"error": e.to_dict()})
        return error_response(e.message)
"""

from typing import Any, Optional


class TPRMError(Exception):
    """Base exception for all TPRM errors.

    All TPRM exceptions inherit from this base class and include:
    - message: Human-readable error message
    - error_code: Machine-readable error identifier
    - details: Optional dictionary with additional context

    Attributes:
        message: Human-readable error description
        error_code: Unique error code (e.g., "DATA_LOAD_ERROR")
        details: Additional error context as dictionary
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[dict[str, Any]] = None
    ):
        """Initialize TPRM exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Optional dictionary with additional context
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for structured logging.

        Returns:
            Dictionary with error_code, message, and details
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        """String representation of the exception."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


# ============================================================================
# Data Loading Errors
# ============================================================================

class DataLoadError(TPRMError):
    """Failed to load framework data.

    Raised when:
    - Framework JSON files cannot be read
    - JSON parsing fails
    - Data directory is missing
    - Required data files are missing
    """

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, "DATA_LOAD_ERROR", details)


class FrameworkNotFoundError(DataLoadError):
    """Requested framework not found.

    Raised when a user requests a framework that doesn't exist or hasn't
    been loaded. Includes available frameworks in details for better UX.

    Example:
        raise FrameworkNotFoundError(
            framework="sig_full",
            available=["sig_lite", "caiq_v4"]
        )
    """

    def __init__(
        self,
        framework: str,
        available_frameworks: Optional[list[str]] = None
    ):
        """Initialize framework not found error.

        Args:
            framework: The framework key that was not found
            available_frameworks: Optional list of available frameworks
        """
        details = {"framework": framework}
        if available_frameworks:
            details["available_frameworks"] = available_frameworks

        message = f"Framework '{framework}' not found"
        if available_frameworks:
            message += f". Available: {', '.join(available_frameworks)}"

        super().__init__(message, details)


class InvalidFrameworkDataError(DataLoadError):
    """Framework data file contains invalid data.

    Raised when:
    - JSON structure doesn't match expected schema
    - Required fields are missing
    - Field types are incorrect
    """

    def __init__(
        self,
        framework: str,
        reason: str,
        file_path: Optional[str] = None
    ):
        """Initialize invalid framework data error.

        Args:
            framework: Framework key with invalid data
            reason: Description of what's invalid
            file_path: Optional path to the invalid file
        """
        details = {"framework": framework, "reason": reason}
        if file_path:
            details["file_path"] = file_path

        message = f"Invalid data in framework '{framework}': {reason}"
        super().__init__(message, details)


class SchemaValidationError(DataLoadError):
    """Data failed schema validation.

    Raised when questionnaire or question data doesn't conform to
    expected schema (missing required fields, wrong types, etc.).
    """

    def __init__(
        self,
        schema_name: str,
        validation_errors: list[str],
        data_sample: Optional[dict[str, Any]] = None
    ):
        """Initialize schema validation error.

        Args:
            schema_name: Name of schema that failed (e.g., "Question")
            validation_errors: List of specific validation errors
            data_sample: Optional sample of invalid data
        """
        details = {
            "schema": schema_name,
            "errors": validation_errors
        }
        if data_sample:
            details["data_sample"] = data_sample

        message = f"Schema validation failed for {schema_name}: {', '.join(validation_errors)}"
        super().__init__(message, details)


# ============================================================================
# Evaluation Errors
# ============================================================================

class EvaluationError(TPRMError):
    """Failed to evaluate vendor response.

    Raised when:
    - Evaluation rubric is invalid
    - Question cannot be evaluated
    - Response format is invalid
    - Required evaluation data is missing
    """

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, "EVALUATION_ERROR", details)


class InvalidRubricError(EvaluationError):
    """Evaluation rubric is invalid or malformed.

    Raised when a question's evaluation_rubric field is missing required
    patterns or contains invalid regex patterns.
    """

    def __init__(
        self,
        question_id: str,
        reason: str,
        rubric_data: Optional[dict[str, Any]] = None
    ):
        """Initialize invalid rubric error.

        Args:
            question_id: ID of question with invalid rubric
            reason: Description of the rubric issue
            rubric_data: Optional rubric data for debugging
        """
        details = {"question_id": question_id, "reason": reason}
        if rubric_data:
            details["rubric"] = rubric_data

        message = f"Invalid evaluation rubric for question '{question_id}': {reason}"
        super().__init__(message, details)


class QuestionNotFoundError(EvaluationError):
    """Question not found in questionnaire.

    Raised when attempting to evaluate a response for a question ID
    that doesn't exist in the questionnaire.
    """

    def __init__(
        self,
        question_id: str,
        questionnaire_id: str
    ):
        """Initialize question not found error.

        Args:
            question_id: ID of question that wasn't found
            questionnaire_id: ID of questionnaire being evaluated
        """
        details = {
            "question_id": question_id,
            "questionnaire_id": questionnaire_id
        }
        message = f"Question '{question_id}' not found in questionnaire '{questionnaire_id}'"
        super().__init__(message, details)


class InvalidResponseError(EvaluationError):
    """Vendor response is invalid or malformed.

    Raised when:
    - Response is missing required fields
    - Response format doesn't match expected type
    - Response data is corrupted
    """

    def __init__(
        self,
        question_id: str,
        reason: str,
        response_data: Optional[Any] = None
    ):
        """Initialize invalid response error.

        Args:
            question_id: ID of question with invalid response
            reason: Description of what's invalid
            response_data: Optional response data for debugging
        """
        details = {"question_id": question_id, "reason": reason}
        if response_data:
            details["response"] = str(response_data)

        message = f"Invalid response for question '{question_id}': {reason}"
        super().__init__(message, details)


# ============================================================================
# Integration Errors
# ============================================================================

class IntegrationError(TPRMError):
    """Failed to integrate with external service.

    Raised when:
    - External MCP server is unavailable
    - API calls to external services fail
    - Data format from external service is unexpected
    - Network/connection issues
    """

    def __init__(
        self,
        message: str,
        service: str,
        details: Optional[dict[str, Any]] = None
    ):
        """Initialize integration error.

        Args:
            message: Error message
            service: Name of external service (e.g., "eu-regulations-mcp")
            details: Optional additional context
        """
        details = details or {}
        details["service"] = service
        super().__init__(message, "INTEGRATION_ERROR", details)


class EURegulationsError(IntegrationError):
    """Failed to integrate with EU Regulations MCP server.

    Raised when DORA/NIS2 requirement fetching fails or returns
    unexpected data format.
    """

    def __init__(
        self,
        operation: str,
        reason: str,
        regulation: Optional[str] = None
    ):
        """Initialize EU regulations error.

        Args:
            operation: Operation that failed (e.g., "get_dora_requirements")
            reason: Description of failure
            regulation: Optional regulation name (DORA/NIS2)
        """
        details = {"operation": operation, "reason": reason}
        if regulation:
            details["regulation"] = regulation

        message = f"EU Regulations integration failed during '{operation}': {reason}"
        super().__init__(message, "eu-regulations-mcp", details)


class SecurityControlsError(IntegrationError):
    """Failed to integrate with Security Controls MCP server.

    Raised when SCF control lookups or framework mappings fail.
    """

    def __init__(
        self,
        operation: str,
        reason: str,
        control_id: Optional[str] = None
    ):
        """Initialize security controls error.

        Args:
            operation: Operation that failed (e.g., "get_control")
            reason: Description of failure
            control_id: Optional SCF control ID
        """
        details = {"operation": operation, "reason": reason}
        if control_id:
            details["control_id"] = control_id

        message = f"Security Controls integration failed during '{operation}': {reason}"
        super().__init__(message, "security-controls-mcp", details)


class VendorIntelError(IntegrationError):
    """Failed to integrate with Vendor Intelligence MCP server.

    Raised when vendor data lookups or breach history queries fail.
    """

    def __init__(
        self,
        operation: str,
        reason: str,
        vendor_name: Optional[str] = None
    ):
        """Initialize vendor intel error.

        Args:
            operation: Operation that failed (e.g., "get_company_profile")
            reason: Description of failure
            vendor_name: Optional vendor name
        """
        details = {"operation": operation, "reason": reason}
        if vendor_name:
            details["vendor_name"] = vendor_name

        message = f"Vendor Intelligence integration failed during '{operation}': {reason}"
        super().__init__(message, "vendor-intel-mcp", details)


# ============================================================================
# Validation Error
# ============================================================================

class ValidationError(TPRMError):
    """Input validation failed.

    Raised when:
    - Required parameters are missing
    - Parameter values are out of range
    - Parameter types are incorrect
    - Parameter combinations are invalid
    """

    def __init__(
        self,
        parameter: str,
        reason: str,
        provided_value: Optional[Any] = None,
        expected_value: Optional[Any] = None
    ):
        """Initialize validation error.

        Args:
            parameter: Name of parameter that failed validation
            reason: Description of validation failure
            provided_value: Optional actual value that was provided
            expected_value: Optional expected value or format
        """
        details = {"parameter": parameter, "reason": reason}
        if provided_value is not None:
            details["provided"] = str(provided_value)
        if expected_value is not None:
            details["expected"] = str(expected_value)

        message = f"Validation failed for parameter '{parameter}': {reason}"
        super().__init__(message, "VALIDATION_ERROR", details)


# ============================================================================
# Configuration Error
# ============================================================================

class ConfigurationError(TPRMError):
    """Server configuration is invalid or missing.

    Raised when:
    - Required configuration values are missing
    - Configuration file cannot be read
    - Environment variables are invalid
    """

    def __init__(
        self,
        config_key: str,
        reason: str,
        suggestion: Optional[str] = None
    ):
        """Initialize configuration error.

        Args:
            config_key: Configuration key that is problematic
            reason: Description of the issue
            suggestion: Optional suggestion for fixing the issue
        """
        details = {"config_key": config_key, "reason": reason}
        if suggestion:
            details["suggestion"] = suggestion

        message = f"Configuration error for '{config_key}': {reason}"
        super().__init__(message, "CONFIGURATION_ERROR", details)
