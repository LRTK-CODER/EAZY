"""Antigravity OAuth-based LLM provider via sandbox endpoint."""

from __future__ import annotations

from eazy.ai.models import ProviderType
from eazy.ai.providers.base_oauth import BaseOAuthProvider


class AntigravityOAuthProvider(BaseOAuthProvider):
    """LLM provider for Gemini via Antigravity IDE OAuth.

    Uses the autopush-cloudaicompanion.sandbox.googleapis.com
    endpoint for Gemini access through Antigravity OAuth flow.
    """

    ENDPOINT_URL = "https://autopush-cloudaicompanion.sandbox.googleapis.com/v1beta"
    PROVIDER_TYPE = ProviderType.ANTIGRAVITY
    DEFAULT_CLIENT_ID = "anthropic-antigravity-client"
    DEFAULT_CLIENT_SECRET = ""
    DEFAULT_SCOPES = [
        "https://www.googleapis.com/auth/generative-language",
    ]
