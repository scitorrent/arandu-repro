"""Pytest configuration and fixtures."""

import pytest


def pytest_addoption(parser):
    """Add custom pytest options."""
    parser.addoption(
        "--test-llm",
        action="store_true",
        default=False,
        help="Run LLM-dependent tests (requires GEMINI_API_KEY)",
    )

