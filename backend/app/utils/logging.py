"""Structured logging utilities."""

import json
import logging
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    # Standard LogRecord attributes to exclude from custom fields
    _STANDARD_ATTRS = {
        "name",
        "msg",
        "args",
        "created",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "thread",
        "threadName",
        "exc_info",
        "exc_text",
        "stack_info",
    }

    # Structured fields that are explicitly handled above
    _STRUCTURED_FIELDS = {
        "job_id",
        "step",
        "event",
        "duration_ms",
        "status",
        "error",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
        }

        # Add structured fields if present
        if hasattr(record, "job_id"):
            log_data["job_id"] = record.job_id
        if hasattr(record, "step"):
            log_data["step"] = record.step
        if hasattr(record, "event"):
            log_data["event"] = record.event
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "status"):
            log_data["status"] = record.status
        if hasattr(record, "error"):
            log_data["error"] = record.error

        # Add any extra custom fields (exclude standard and structured fields)
        excluded = self._STANDARD_ATTRS | self._STRUCTURED_FIELDS
        for key, value in record.__dict__.items():
            if key not in excluded:
                log_data[key] = value

        return json.dumps(log_data)


def setup_logging(level: int = logging.INFO, json_format: bool = True) -> None:
    """
    Setup structured logging configuration.

    Args:
        level: Logging level (default: INFO)
        json_format: If True, use JSON formatter; otherwise use plain text
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(level)

    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

    root_logger.addHandler(handler)


def log_event(
    level: int,
    message: str,
    job_id: str | None = None,
    step: str | None = None,
    event: str | None = None,
    duration_ms: float | None = None,
    status: str | None = None,
    error: str | None = None,
    **kwargs: Any,
) -> None:
    """
    Log a structured event with optional metadata.

    Args:
        level: Logging level (logging.INFO, logging.ERROR, etc.)
        message: Log message
        job_id: Job ID (optional)
        step: Pipeline step (optional)
        event: Event type (optional, e.g., "job_created", "clone_start", etc.)
        duration_ms: Duration in milliseconds (optional)
        status: Status value (optional, e.g., "completed", "failed")
        error: Error message (optional)
        **kwargs: Additional structured fields
    """
    # Create a LogRecord with extra fields
    extra = {}
    if job_id:
        extra["job_id"] = job_id
    if step:
        extra["step"] = step
    if event:
        extra["event"] = event
    if duration_ms is not None:
        extra["duration_ms"] = duration_ms
    if status:
        extra["status"] = status
    if error:
        extra["error"] = error

    # Add any additional kwargs
    extra.update(kwargs)

    logger.log(level, message, extra=extra)


@contextmanager
def log_step(
    job_id: str | None,
    step: str,
    event: str | None = None,
    **kwargs: Any,
):
    """
    Context manager to log a step with duration.

    Args:
        job_id: Job ID (optional)
        step: Pipeline step name
        event: Event type (optional, defaults to step name)
        **kwargs: Additional structured fields
    """
    start_time = time.time()
    event_name = event or f"{step}_start"
    log_event(
        logging.INFO,
        f"Starting {step}",
        job_id=job_id,
        step=step,
        event=event_name,
        **kwargs,
    )
    try:
        yield
        duration_ms = (time.time() - start_time) * 1000
        log_event(
            logging.INFO,
            f"Completed {step}",
            job_id=job_id,
            step=step,
            event=f"{step}_end",
            duration_ms=duration_ms,
            status="success",
            **kwargs,
        )
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_event(
            logging.ERROR,
            f"Failed {step}: {str(e)}",
            job_id=job_id,
            step=step,
            event=f"{step}_error",
            duration_ms=duration_ms,
            status="failed",
            error=str(e),
            **kwargs,
        )
        raise
