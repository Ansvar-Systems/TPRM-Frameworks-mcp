"""Centralized logging configuration with JSON structured logging."""

import logging
import os
from pythonjsonlogger import jsonlogger


def setup_logging() -> logging.Logger:
    """
    Configure JSON structured logging for production.

    Returns:
        logging.Logger: Configured logger instance for TPRM Frameworks MCP.

    Environment Variables:
        TPRM_LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Defaults to INFO.
        TPRM_LOG_FORMAT: Toggle JSON (json) or plain text (text) format. Defaults to json.
    """
    log_level = os.getenv("TPRM_LOG_LEVEL", "INFO").upper()
    log_format_type = os.getenv("TPRM_LOG_FORMAT", "json").lower()

    # Create logger
    logger = logging.getLogger("tprm_frameworks_mcp")
    logger.setLevel(log_level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # Configure formatter based on environment
    if log_format_type == "json":
        # JSON formatter for structured logs (production)
        log_format = "%(asctime)s %(name)s %(levelname)s %(message)s"
        formatter = jsonlogger.JsonFormatter(
            log_format,
            rename_fields={
                "asctime": "timestamp",
                "name": "logger",
                "levelname": "level",
            },
            timestamp=True,
        )
    else:
        # Plain text formatter for development
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Optional name for the logger (e.g., 'server', 'storage', 'evaluator').
              If None, returns the root TPRM logger.

    Returns:
        logging.Logger: Logger instance.
    """
    if name:
        return logging.getLogger(f"tprm_frameworks_mcp.{name}")
    return logging.getLogger("tprm_frameworks_mcp")
