"""Tests for LLM client (Gemini)."""

import os

import pytest
from unittest.mock import patch

from app.worker.llm_client import generate_text, get_llm_client


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "llm: marks tests as requiring LLM (deselect with '-m \"not llm\"')")


@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="LLM tests require GEMINI_API_KEY environment variable",
)
def test_llm_client_available():
    """Test that LLM client can be initialized."""
    client = get_llm_client()
    assert client is not None


@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="LLM tests require GEMINI_API_KEY environment variable",
)
def test_generate_text_simple():
    """Test simple text generation."""
    response = generate_text("Say 'Hello, Arandu!' in one sentence.", temperature=0.1)
    assert response is not None
    assert "Arandu" in response or "arandu" in response.lower()


@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="LLM tests require GEMINI_API_KEY environment variable",
)
def test_generate_text_narrative():
    """Test narrative generation for quality score."""
    prompt = """Generate a brief executive summary (2-3 bullets) for a research paper quality score of 75/100 (Tier B).

Focus on:
- Why the score is reasonable
- One key strength
- One area for improvement

Format as JSON:
{
  "summary": ["bullet 1", "bullet 2", "bullet 3"]
}
"""

    response = generate_text(prompt, temperature=0.3)
    assert response is not None
    assert len(response) > 50  # Should be substantial


def test_llm_client_fallback_when_disabled():
    """Test that LLM gracefully degrades when disabled."""
    with patch("app.worker.llm_client.settings") as mock_settings:
        mock_settings.llm_enabled = False
        response = generate_text("test")
        assert response is None


def test_llm_client_fallback_when_no_key():
    """Test that LLM gracefully degrades when API key not set."""
    with patch("app.worker.llm_client.settings") as mock_settings:
        mock_settings.llm_enabled = True
        mock_settings.gemini_api_key = ""
        response = generate_text("test")
        assert response is None

