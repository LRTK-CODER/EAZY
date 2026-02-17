"""Authentication plugins for LLM providers."""

from eazy.ai.plugins.base import AuthPlugin
from eazy.ai.plugins.gemini_api import GeminiApiPlugin, GeminiApiProvider
from eazy.ai.plugins.gemini_oauth import (
    GeminiOAuthPlugin,
    GeminiOAuthProvider,
)

__all__ = [
    "AuthPlugin",
    "GeminiApiPlugin",
    "GeminiApiProvider",
    "GeminiOAuthPlugin",
    "GeminiOAuthProvider",
]
