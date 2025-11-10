"""Structured logging for Travel Photo Organization Workflow."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Global error log storage
ERROR_LOG: List[Dict[str, Any]] = []


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add extra fields if present
        if hasattr(record, 'agent'):
            log_data['agent'] = record.agent
        if hasattr(record, 'error_type'):
            log_data['error_type'] = record.error_type
        if hasattr(record, 'severity'):
            log_data['severity'] = record.severity

        return json.dumps(log_data)


def setup_logger(
    name: str = "travel_photo_workflow",
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = True
) -> logging.Logger:
    """
    Set up structured logger.

    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        json_format: Use JSON formatting

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if json_format:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        if json_format:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
        logger.addHandler(file_handler)

    return logger


def log_error(
    logger: logging.Logger,
    agent: str,
    error_type: str,
    summary: str,
    severity: str = "error",
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Log structured error and add to global error log.

    Args:
        logger: Logger instance
        agent: Agent name
        error_type: Type of error
        summary: Error summary
        severity: Severity level (info, warning, error, critical)
        details: Additional error details

    Returns:
        Error log entry
    """
    error_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent": agent,
        "error_type": error_type,
        "summary": summary,
        "severity": severity
    }

    if details:
        error_entry["details"] = details

    # Add to global error log
    ERROR_LOG.append(error_entry)

    # Log using appropriate level
    log_level = {
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }.get(severity.lower(), logging.ERROR)

    logger.log(
        log_level,
        f"{agent} - {error_type}: {summary}",
        extra={"agent": agent, "error_type": error_type, "severity": severity}
    )

    return error_entry


def log_info(logger: logging.Logger, message: str, agent: Optional[str] = None):
    """Log info message with optional agent context."""
    extra = {"agent": agent} if agent else {}
    logger.info(message, extra=extra)


def log_warning(logger: logging.Logger, message: str, agent: Optional[str] = None):
    """Log warning message with optional agent context."""
    extra = {"agent": agent} if agent else {}
    logger.warning(message, extra=extra)


def get_error_log() -> List[Dict[str, Any]]:
    """Get all logged errors."""
    return ERROR_LOG.copy()


def clear_error_log():
    """Clear error log."""
    ERROR_LOG.clear()


def save_error_log(output_path: Path):
    """Save error log to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(ERROR_LOG, f, indent=2)
