"""Pytest configuration and fixtures."""

import pytest


def pytest_addoption(parser):
    """Add custom pytest options."""
    try:
        parser.addoption(
            "--test-llm",
            action="store_true",
            default=False,
            help="Run LLM-dependent tests (requires GEMINI_API_KEY)",
        )
    except (ValueError, AttributeError):
        # Option already exists or parser does not support addoption
        pass

