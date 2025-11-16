"""LLM client for Gemini API (supports both API key and Vertex AI)."""

import logging
import os
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# Try to import google-generativeai (for API key)
try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not available, LLM features will be disabled")

# Try to import Vertex AI (for service account)
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel

    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logger.debug("vertexai not available, will use API key only")


def get_llm_client():
    """
    Get configured Gemini LLM client.

    Tries API key first (direct Gemini API), then falls back to Vertex AI
    if GOOGLE_APPLICATION_CREDENTIALS is set.

    Returns:
        Configured model client or None if not available
    """
    # Try API key first (direct Gemini API - simpler, no project ID needed)
    if GEMINI_AVAILABLE and settings.gemini_api_key:
        try:
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel(settings.gemini_model)
            logger.info("Using direct Gemini API with API key")
            return model
        except Exception as e:
            logger.warning(f"Direct Gemini API initialization failed: {e}, trying Vertex AI")

    # Fallback to Vertex AI (if credentials available)
    if VERTEX_AI_AVAILABLE and os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            vertexai.init(project=settings.gcp_project_id, location="us-central1")
            model = GenerativeModel(settings.gemini_model)
            logger.info("Using Vertex AI authentication for Gemini")
            return model
        except Exception as e:
            logger.warning(f"Vertex AI initialization failed: {e}")

    logger.warning("No Gemini authentication available (neither API key nor Vertex AI)")
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

        # Check if it's a Vertex AI model (has different API structure)
        # Direct Gemini API returns response.text directly
        if hasattr(response, "text"):
            return response.text
        # Vertex AI returns response.candidates[0].content.parts[0].text
        elif hasattr(response, "candidates") and response.candidates:
            return response.candidates[0].content.parts[0].text
        else:
            logger.error(f"Unexpected response format: {type(response)}")
            return None
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        # Log more details for debugging
        error_msg = str(e)
        if "401" in error_msg or "CREDENTIALS" in error_msg or "PERMISSION_DENIED" in error_msg or "403" in error_msg:
            logger.warning(
                "Gemini API authentication failed. "
                "For Vertex AI, ensure GOOGLE_APPLICATION_CREDENTIALS points to valid service account key "
                f"and project {settings.gcp_project_id} has Vertex AI API enabled. "
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
