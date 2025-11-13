"""Structured logging utilities."""

import logging
import time
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)


def setup_logging(level: int = logging.INFO) -> None:
    """Setup structured logging configuration."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def log_event(
    level: int,
    message: str,
    job_id: str | None = None,
    step: str | None = None,
    duration_ms: float | None = None,
    **kwargs: Any,
) -> None:
    """Log a structured event with optional metadata."""
    log_data: dict[str, Any] = {}
    if job_id:
        log_data["job_id"] = job_id
    if step:
        log_data["step"] = step
    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms

    # Add any additional kwargs
    log_data.update(kwargs)

    # Format message with metadata
    if log_data:
        metadata_str = " ".join(f"{k}={v}" for k, v in log_data.items())
        full_message = f"{message} | {metadata_str}"
    else:
        full_message = message

    logger.log(level, full_message)


@contextmanager
def log_step(job_id: str | None, step: str, **kwargs: Any):
    """Context manager to log a step with duration."""
    start_time = time.time()
    log_event(logging.INFO, f"Starting {step}", job_id=job_id, step=step, **kwargs)
    try:
        yield
        duration_ms = (time.time() - start_time) * 1000
        log_event(
            logging.INFO,
            f"Completed {step}",
            job_id=job_id,
            step=step,
            duration_ms=duration_ms,
            **kwargs,
        )
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_event(
            logging.ERROR,
            f"Failed {step}: {str(e)}",
            job_id=job_id,
            step=step,
            duration_ms=duration_ms,
            error=str(e),
            **kwargs,
        )
        raise
