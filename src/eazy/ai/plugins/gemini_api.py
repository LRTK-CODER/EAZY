"""Gemini API key authentication plugin and provider."""

from __future__ import annotations

from typing import Any

import httpx

from eazy.ai.models import LLMError, LLMResponse, RateLimitError
from eazy.ai.plugins.base import AuthPlugin
from eazy.ai.plugins.gemini_common import (
    GEMINI_API_BASE,
    extract_error_message,
    parse_gemini_response,
)
from eazy.ai.provider import LLMProvider


class GeminiApiPlugin(AuthPlugin):
    """Authentication plugin using a Gemini API key.

    API keys do not expire and require no refresh.
    """

    def __init__(self) -> None:
        self._api_key: str | None = None

    async def authenticate(self, **kwargs: Any) -> bool:
        """Store API key if non-empty.

        Args:
            **kwargs: Must include 'api_key' string.

        Returns:
            True if key is non-empty, False otherwise.
        """
        api_key: str = kwargs.get("api_key", "")
        if not api_key:
            return False
        self._api_key = api_key
        return True

    async def refresh(self) -> bool:
        """No-op for API keys.

        Returns:
            Always True.
        """
        return True

    def is_expired(self) -> bool:
        """API keys never expire.

        Returns:
            Always False.
        """
        return False


class GeminiApiProvider(LLMProvider):
    """LLM provider using Gemini API with key authentication.

    Sends prompts to the Gemini generateContent endpoint
    using an API key query parameter.

    Attributes:
        _plugin: Authentication plugin holding the API key.
        _client: Optional shared httpx client.
    """

    def __init__(
        self,
        plugin: GeminiApiPlugin,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._plugin = plugin
        self._client = client

    @property
    def name(self) -> str:
        """Unique provider identifier."""
        return "gemini-api"

    async def send(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Send a prompt to Gemini and return the response.

        Args:
            prompt: Text prompt to send.
            **kwargs: Optional 'model' (default gemini-2.0-flash).

        Returns:
            Parsed LLM response.

        Raises:
            RateLimitError: On HTTP 429.
            LLMError: On other HTTP errors.
        """
        model = kwargs.get("model", "gemini-2.0-flash")
        url = f"{GEMINI_API_BASE}/v1beta/models/{model}:generateContent"
        params = {"key": self._plugin._api_key}
        body = {"contents": [{"parts": [{"text": prompt}]}]}

        client = self._client or httpx.AsyncClient()
        try:
            resp = await client.post(url, json=body, params=params)
            if resp.status_code == 429:
                msg = extract_error_message(resp)
                raise RateLimitError(msg)
            if resp.status_code >= 400:
                msg = extract_error_message(resp)
                raise LLMError(msg)
            return parse_gemini_response(resp.json(), model)
        finally:
            if not self._client:
                await client.aclose()

    def is_available(self) -> bool:
        """Check whether an API key is configured."""
        return self._plugin._api_key is not None
