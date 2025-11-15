"""LLM client for Gemini API."""

import logging
import os
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# Try to import google-generativeai
try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not available, LLM features will be disabled")


def get_llm_client():
    """
    Get configured Gemini LLM client.

    Supports API key authentication for Gemini API.
    For Vertex AI, use GOOGLE_APPLICATION_CREDENTIALS env var.

    Returns:
        Configured genai client or None if not available
    """
    if not GEMINI_AVAILABLE:
        return None

    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY not set, LLM features disabled")
        return None

    try:
        # Configure with API key
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        return model
    except Exception as e:
        logger.error(f"Failed to configure Gemini client: {e}")
        return None


def generate_text(prompt: str, temperature: float = 0.3, max_tokens: int = 2000) -> str | None:
    """
    Generate text using Gemini API.

    Args:
        prompt: Input prompt
        temperature: Temperature for generation (0.0-1.0)
        max_tokens: Maximum tokens to generate

    Returns:
        Generated text or None if LLM not available
    """
    if not settings.llm_enabled:
        return None

    client = get_llm_client()
    if not client:
        return None

    try:
        response = client.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )
        return response.text
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        # Log more details for debugging
        error_msg = str(e)
        if "401" in error_msg or "CREDENTIALS" in error_msg:
            logger.warning(
                "Gemini API authentication failed. "
                "For Vertex AI, set GOOGLE_APPLICATION_CREDENTIALS env var. "
                "For API key, ensure GEMINI_API_KEY is valid."
            )
        return None


def generate_structured_output(prompt: str, output_format: str = "json") -> dict[str, Any] | None:
    """
    Generate structured output (JSON) from LLM.

    Args:
        prompt: Input prompt with instructions for JSON output
        output_format: Output format (currently only "json")

    Returns:
        Parsed JSON dict or None if generation failed
    """
    import json

    text = generate_text(prompt, temperature=0.2)
    if not text:
        return None

    try:
        # Try to extract JSON from response
        # Remove markdown code blocks if present
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON output: {e}")
        logger.debug(f"LLM output: {text}")
        return None
