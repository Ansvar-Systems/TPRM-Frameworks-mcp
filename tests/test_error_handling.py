#!/usr/bin/env python3
"""Test error handling in TPRM Frameworks MCP server."""

from src.tprm_frameworks_mcp.exceptions import (
    FrameworkNotFoundError,
    EvaluationError,
    TPRMError,
    ValidationError,
)
from src.tprm_frameworks_mcp.storage import StorageError


def test_framework_not_found_error():
    """Test FrameworkNotFoundError exception."""
    try:
        raise FrameworkNotFoundError("sig_full", ["sig_lite", "caiq_v4"])
    except FrameworkNotFoundError as e:
        print(f"✓ FrameworkNotFoundError caught: {e.message}")
        print(f"  Error code: {e.error_code}")
        print(f"  Details: {e.details}")
        assert e.error_code == "DATA_LOAD_ERROR"
        assert "sig_full" in e.message
        assert "available_frameworks" in e.details


def test_evaluation_error():
    """Test EvaluationError exception."""
    try:
        raise EvaluationError(
            "Failed to evaluate response",
            details={"question_id": "Q1", "reason": "Invalid rubric"}
        )
    except EvaluationError as e:
        print(f"\n✓ EvaluationError caught: {e.message}")
        print(f"  Error code: {e.error_code}")
        print(f"  Details: {e.details}")
        assert e.error_code == "EVALUATION_ERROR"


def test_storage_error():
    """Test StorageError exception."""
    try:
        raise StorageError("Database connection failed")
    except StorageError as e:
        print(f"\n✓ StorageError caught: {str(e)}")
        assert "Database" in str(e)


def test_validation_error():
    """Test ValidationError exception."""
    try:
        raise ValidationError(
            parameter="framework",
            reason="Framework key is required",
            provided_value=None,
            expected_value="sig_lite"
        )
    except ValidationError as e:
        print(f"\n✓ ValidationError caught: {e.message}")
        print(f"  Error code: {e.error_code}")
        print(f"  Details: {e.details}")
        assert e.error_code == "VALIDATION_ERROR"
        assert "framework" in e.message


def test_exception_to_dict():
    """Test exception to_dict method for structured logging."""
    error = FrameworkNotFoundError("test_framework")
    error_dict = error.to_dict()

    print(f"\n✓ Exception to_dict method works:")
    print(f"  {error_dict}")

    assert "error_code" in error_dict
    assert "message" in error_dict
    assert "details" in error_dict


def test_tprm_error_hierarchy():
    """Test TPRM error exception hierarchy."""
    # All custom exceptions should inherit from TPRMError
    assert issubclass(FrameworkNotFoundError, TPRMError)
    assert issubclass(EvaluationError, TPRMError)
    assert issubclass(ValidationError, TPRMError)
    print("\n✓ Exception hierarchy is correct")


if __name__ == "__main__":
    print("Testing TPRM Error Handling\n" + "=" * 50)

    test_framework_not_found_error()
    test_evaluation_error()
    test_storage_error()
    test_validation_error()
    test_exception_to_dict()
    test_tprm_error_hierarchy()

    print("\n" + "=" * 50)
    print("✓ All error handling tests passed!")
