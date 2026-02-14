"""Base class for OAuth-based Gemini LLM providers."""

from __future__ import annotations

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
    OAuthTokens,
    ProviderType,
)
from eazy.ai.oauth_flow import OAuthFlowEngine
from eazy.ai.provider import LLMProvider
from eazy.ai.token_storage import TokenStorage


class BaseOAuthProvider(LLMProvider):
    """Base class for OAuth-based Gemini LLM providers.

    Provides shared logic for OAuth authentication, token management,
    and Gemini API request/response handling. Subclasses only need to
    set class-level constants for endpoint URL, provider type, and
    OAuth configuration.

    Args:
        token_storage: Storage backend for persisting tokens.
        oauth_engine: OAuth flow engine for token exchange.
            If None, created lazily from DEFAULT_* constants.
        account_id: Account identifier. If provided, attempts to
            load an existing token from storage on init.
    """

    ENDPOINT_URL: str
    PROVIDER_TYPE: ProviderType
    DEFAULT_CLIENT_ID: str
    DEFAULT_CLIENT_SECRET: str = ""
    DEFAULT_AUTH_URL: str = "https://accounts.google.com/o/oauth2/v2/auth"
    DEFAULT_TOKEN_URL: str = "https://oauth2.googleapis.com/token"
    DEFAULT_SCOPES: list[str]

    def __init__(
        self,
        token_storage: TokenStorage,
        oauth_engine: OAuthFlowEngine | None = None,
        account_id: str | None = None,
    ) -> None:
        self._token_storage = token_storage
        self._oauth_engine = oauth_engine
        self._account_id = account_id
        self._tokens: OAuthTokens | None = None
        if account_id:
            self._load_existing_token()

    @property
    def provider_type(self) -> ProviderType:
        """Get the provider type identifier."""
        return self.PROVIDER_TYPE

    @property
    def supports_oauth(self) -> bool:
        """OAuth providers always support OAuth."""
        return True

    @property
    def supports_multi_account(self) -> bool:
        """OAuth providers support multiple accounts."""
        return True

    @property
    def billing_type(self) -> BillingType:
        """OAuth providers use subscription billing."""
        return BillingType.SUBSCRIPTION

    @property
    def is_authenticated(self) -> bool:
        """Check if tokens are available."""
        return self._tokens is not None

    async def authenticate(self, **kwargs) -> bool:
        """Exchange an OAuth authorization code for tokens.

        Args:
            **kwargs: Must include:
                code: Authorization code from OAuth callback.
                redirect_uri: Redirect URI used in auth request.
                account_id: Account identifier for token storage.

        Returns:
            True if authentication succeeded.
        """
        code = kwargs.get("code", "")
        redirect_uri = kwargs.get("redirect_uri", "")
        account_id = kwargs.get("account_id") or self._account_id

        engine = self._get_oauth_engine()
        tokens = await engine.exchange_code(
            code=code,
            redirect_uri=redirect_uri,
        )

        self._tokens = tokens
        self._account_id = account_id

        if account_id:
            self._token_storage.save(
                self.PROVIDER_TYPE.value,
                account_id,
                tokens.model_dump(mode="json"),
            )

        return True

    async def send(self, request: LLMRequest) -> LLMResponse:
        """Send a request to the Gemini API via OAuth Bearer token.

        Args:
            request: The LLMRequest containing prompt and parameters.

        Returns:
            LLMResponse with generated content and metadata.

        Raises:
            AuthenticationError: If not authenticated or the server
                returns HTTP 401.
            RateLimitError: If the server returns HTTP 429.
            ProviderError: If the server returns HTTP 5xx.
        """
        if not self.is_authenticated:
            raise AuthenticationError("Not authenticated. Call authenticate() first.")

        await self._ensure_valid_token()

        url = f"{self.ENDPOINT_URL}/models/{request.model}:generateContent"
        headers = {
            "Authorization": f"Bearer {self._tokens.access_token}",
        }
        body = self._build_request_body(request)

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                json=body,
                headers=headers,
            )
            if resp.status_code == 401:
                raise AuthenticationError("OAuth token invalid or expired.")
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("retry-after", 0)) or None
                raise RateLimitError(
                    "Rate limit exceeded.",
                    retry_after=retry_after,
                )
            if resp.status_code >= 500:
                raise ProviderError(f"Server error: {resp.status_code}")
            resp.raise_for_status()

        data = resp.json()
        return self._parse_response(data, request.model)

    async def _ensure_valid_token(self) -> None:
        """Refresh the access token if expired."""
        if self._tokens and OAuthFlowEngine.is_token_expired(
            self._tokens.expires_at,
        ):
            engine = self._get_oauth_engine()
            self._tokens = await engine.refresh_token(
                self._tokens.refresh_token,
            )
            if self._account_id:
                self._token_storage.save(
                    self.PROVIDER_TYPE.value,
                    self._account_id,
                    self._tokens.model_dump(mode="json"),
                )

    def _load_existing_token(self) -> None:
        """Load a previously saved token from storage."""
        data = self._token_storage.load(
            self.PROVIDER_TYPE.value,
            self._account_id,
        )
        if data:
            self._tokens = OAuthTokens(**data)

    def _get_oauth_engine(self) -> OAuthFlowEngine:
        """Get or create the OAuth flow engine."""
        if self._oauth_engine is None:
            self._oauth_engine = OAuthFlowEngine(
                client_id=self.DEFAULT_CLIENT_ID,
                client_secret=self.DEFAULT_CLIENT_SECRET,
                auth_url=self.DEFAULT_AUTH_URL,
                token_url=self.DEFAULT_TOKEN_URL,
                scopes=self.DEFAULT_SCOPES,
            )
        return self._oauth_engine

    def _build_request_body(self, request: LLMRequest) -> dict:
        """Build the Gemini API request body.

        Args:
            request: The LLMRequest to convert.

        Returns:
            Dictionary matching Gemini API expected format.
        """
        body: dict = {
            "contents": [
                {"parts": [{"text": request.prompt}]},
            ],
        }

        generation_config: dict = {}
        if request.temperature is not None:
            generation_config["temperature"] = request.temperature
        if request.max_tokens is not None:
            generation_config["maxOutputTokens"] = request.max_tokens
        if generation_config:
            body["generationConfig"] = generation_config

        if request.system_prompt:
            body["system_instruction"] = {
                "parts": [{"text": request.system_prompt}],
            }

        return body

    def _parse_response(
        self,
        data: dict,
        model: str,
    ) -> LLMResponse:
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
            provider_type=self.PROVIDER_TYPE,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            finish_reason=finish_reason,
        )
