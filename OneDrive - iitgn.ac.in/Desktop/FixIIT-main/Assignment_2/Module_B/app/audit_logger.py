"""Audit and security logging for Module B."""

import logging
import os
from datetime import datetime


def _log_path():
    """Return absolute path for Module_B/logs/audit.log."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    module_b_dir = os.path.dirname(app_dir)
    logs_dir = os.path.join(module_b_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    return os.path.join(logs_dir, "audit.log")


def _get_logger():
    """Create/reuse logger configured for audit.log."""
    logger = logging.getLogger("module_b_audit")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(_log_path())
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def _format_line(endpoint, status, message, member_id=None):
    """Format one audit line in a readable, report-friendly style."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    actor = f"member_id={member_id}" if member_id is not None else "member_id=UNKNOWN"
    return f"[{ts}] {actor} | endpoint={endpoint} | status={status} | {message}"


def log_api_event(endpoint, status, message, member_id=None):
    """Write a generic API audit event."""
    logger = _get_logger()
    logger.info(_format_line(endpoint, status, message, member_id))


def log_security_event(endpoint, status, message, member_id=None):
    """Write security-related event to same audit log."""
    logger = _get_logger()
    logger.info(_format_line(endpoint, status, f"SECURITY: {message}", member_id))
