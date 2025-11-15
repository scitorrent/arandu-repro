"""Metrics API routes."""

import logging

from fastapi import APIRouter

from app.utils.metrics import get_metrics_summary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def get_metrics():
    """
    Get metrics summary.

    Returns:
        JSON with aggregated metrics
    """
    summary = get_metrics_summary()
    return summary

