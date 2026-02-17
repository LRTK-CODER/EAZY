"""Shared constants and helpers for Gemini providers."""

from __future__ import annotations

import httpx

from eazy.ai.models import LLMResponse

GEMINI_API_BASE = "https://generativelanguage.googleapis.com"


def parse_gemini_response(data: dict, model: str) -> LLMResponse:
    """Parse Gemini generateContent response into LLMResponse.

    Args:
        data: Raw JSON response from Gemini API.
        model: Model identifier used for the request.

    Returns:
        Parsed LLM response.
    """
    candidate = data["candidates"][0]
    usage = data.get("usageMetadata", {})
    return LLMResponse(
        content=candidate["content"]["parts"][0]["text"],
        model=model,
        input_tokens=usage.get("promptTokenCount", 0),
        output_tokens=usage.get("candidatesTokenCount", 0),
        finish_reason=candidate.get("finishReason"),
    )


def extract_error_message(resp: httpx.Response) -> str:
    """Extract error message from Gemini API error response.

    Args:
        resp: HTTP response from Gemini API.

    Returns:
        Error message string.
    """
    try:
        return resp.json()["error"]["message"]
    except (KeyError, ValueError):
        return f"HTTP {resp.status_code}"
