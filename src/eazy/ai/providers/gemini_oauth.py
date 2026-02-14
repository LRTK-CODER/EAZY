"""Gemini OAuth-based LLM provider via Cloud AI Companion endpoint."""

from __future__ import annotations

from eazy.ai.models import ProviderType
from eazy.ai.providers.base_oauth import BaseOAuthProvider


class GeminiOAuthProvider(BaseOAuthProvider):
    """LLM provider for Gemini via Google OAuth (Cloud AI Companion).

    Uses the cloudaicompanion.googleapis.com endpoint for Gemini
    access through Google account OAuth authentication.
    """

    ENDPOINT_URL = "https://cloudaicompanion.googleapis.com/v1beta"
    PROVIDER_TYPE = ProviderType.GEMINI_OAUTH
    DEFAULT_CLIENT_ID = "936475272427.apps.googleusercontent.com"
    DEFAULT_CLIENT_SECRET = ""
    DEFAULT_SCOPES = [
        "https://www.googleapis.com/auth/cloud-platform",
    ]
