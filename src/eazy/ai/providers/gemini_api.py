"""Gemini API key-based LLM provider implementation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from eazy.ai.exceptions import (
    AuthenticationError,
    ProviderError,
    RateLimitError,
)
from eazy.ai.models import (
    BillingType,
    LLMRequest,
    LLMResponse,
    ProviderType,
    RateLimitInfo,
)
from eazy.ai.provider import LLMProvider


class GeminiAPIProvider(LLMProvider):
    """LLM provider for Gemini via API key authentication.

    Supports multiple API keys with automatic rotation when a key's
    rate limit is exhausted. Each key tracks its own per-minute and
    per-day request counters.

    Args:
        api_keys: Optional list of API keys to initialize with.
        endpoint_url: Custom API endpoint URL. Defaults to the
            official Gemini API base URL.
    """

    GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
    DEFAULT_RPM = 15
    DEFAULT_RPD = 1500

    def __init__(
        self,
        api_keys: list[str] | None = None,
        endpoint_url: str | None = None,
    ) -> None:
        self._api_keys: list[str] = list(api_keys) if api_keys else []
        self._endpoint_url = endpoint_url or self.GEMINI_API_BASE
        self._rate_limits: dict[str, RateLimitInfo] = {}
        for key in self._api_keys:
            self._init_rate_limit(key)

    @property
    def provider_type(self) -> ProviderType:
        """Get the provider type identifier."""
        return ProviderType.GEMINI_API

    @property
    def supports_oauth(self) -> bool:
        """API key provider does not support OAuth."""
        return False

    @property
    def supports_multi_account(self) -> bool:
        """API key provider supports multiple keys."""
        return True

    @property
    def billing_type(self) -> BillingType:
        """API key provider uses per-token billing."""
        return BillingType.PER_TOKEN

    @property
    def is_authenticated(self) -> bool:
        """Check if at least one API key is available."""
        return len(self._api_keys) > 0

    async def authenticate(self, **kwargs) -> bool:
        """Add an API key to the provider.

        Args:
            **kwargs: Must include 'api_key' with a non-empty string.

        Returns:
            True if the key was added, False if empty/invalid.
        """
        api_key = kwargs.get("api_key", "")
        if not api_key or not api_key.strip():
            return False
        self._api_keys.append(api_key)
        self._init_rate_limit(api_key)
        return True

    async def send(self, request: LLMRequest) -> LLMResponse:
        """Send a request to the Gemini API.

        Args:
            request: The LLMRequest containing prompt and parameters.

        Returns:
            LLMResponse with generated content and metadata.

        Raises:
            AuthenticationError: If no API keys are configured or
                the server returns HTTP 401.
            RateLimitError: If the server returns HTTP 429.
            ProviderError: If the server returns HTTP 5xx.
        """
        if not self.is_authenticated:
            raise AuthenticationError(
                "No API keys configured. Call authenticate() first."
            )

        api_key = self._get_current_key()
        url = f"{self._endpoint_url}/models/{request.model}:generateContent"
        body = self._build_request_body(request)

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                json=body,
                params={"key": api_key},
            )
            if resp.status_code == 401:
                raise AuthenticationError("Invalid or expired API key.")
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("retry-after", 0)) or None
                self.exhaust_key(api_key)
                if retry_after:
                    rl = self._rate_limits.get(api_key)
                    if rl:
                        rl.reset_at = datetime.now(timezone.utc) + timedelta(
                            seconds=retry_after
                        )
                raise RateLimitError(
                    "Rate limit exceeded.",
                    retry_after=retry_after,
                )
            if resp.status_code >= 500:
                raise ProviderError(f"Server error: {resp.status_code}")
            resp.raise_for_status()

        data = resp.json()
        response = self._parse_response(data, request.model)

        # Decrement rate limit counters
        rl = self._rate_limits[api_key]
        rl.remaining_minute -= 1
        rl.remaining_day -= 1

        return response

    def get_rate_limit(self, api_key: str) -> RateLimitInfo | None:
        """Get rate limit info for a specific API key.

        Args:
            api_key: The API key to look up.

        Returns:
            RateLimitInfo if key exists, None otherwise.
        """
        return self._rate_limits.get(api_key)

    def exhaust_key(self, api_key: str) -> None:
        """Mark a key as rate-limited by zeroing its counters.

        Args:
            api_key: The API key to exhaust.
        """
        if api_key in self._rate_limits:
            rl = self._rate_limits[api_key]
            rl.remaining_minute = 0
            rl.remaining_day = 0

    def _get_current_key(self) -> str:
        """Find the first non-exhausted API key.

        Returns:
            An API key that still has remaining quota.

        Raises:
            RateLimitError: If all keys are exhausted.
        """
        for key in self._api_keys:
            rl = self._rate_limits.get(key)
            if rl is None or not rl.is_exceeded:
                return key
        raise RateLimitError("All API keys have exceeded their rate limits.")

    def _init_rate_limit(self, api_key: str) -> None:
        """Initialize rate limit tracking for a key.

        Args:
            api_key: The API key to initialize counters for.
        """
        if api_key not in self._rate_limits:
            self._rate_limits[api_key] = RateLimitInfo(
                max_requests_per_minute=self.DEFAULT_RPM,
                max_requests_per_day=self.DEFAULT_RPD,
                remaining_minute=self.DEFAULT_RPM,
                remaining_day=self.DEFAULT_RPD,
            )

    def _build_request_body(self, request: LLMRequest) -> dict:
        """Build the Gemini API request body.

        Args:
            request: The LLMRequest to convert.

        Returns:
            Dictionary matching Gemini API expected format.
        """
        body: dict = {
            "contents": [{"parts": [{"text": request.prompt}]}],
        }

        generation_config: dict = {}
        if request.temperature is not None:
            generation_config["temperature"] = request.temperature
        if request.max_tokens is not None:
            generation_config["maxOutputTokens"] = request.max_tokens
        if generation_config:
            body["generationConfig"] = generation_config

        if request.system_prompt:
            body["system_instruction"] = {"parts": [{"text": request.system_prompt}]}

        return body

    def _parse_response(self, data: dict, model: str) -> LLMResponse:
        """Parse the Gemini API response into LLMResponse.

        Args:
            data: Raw JSON response from Gemini API.
            model: Model identifier used for the request.

        Returns:
            Parsed LLMResponse with content and usage metadata.
        """
        candidate = data["candidates"][0]
        content = candidate["content"]["parts"][0]["text"]
        finish_reason = candidate.get("finishReason")

        usage = data.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount", 0)
        output_tokens = usage.get("candidatesTokenCount", 0)

        model_version = data.get("modelVersion", model)

        return LLMResponse(
            content=content,
            model=model_version,
            provider_type=ProviderType.GEMINI_API,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            finish_reason=finish_reason,
        )
