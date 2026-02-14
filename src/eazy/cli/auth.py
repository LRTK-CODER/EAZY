"""Auth CLI sub-app for managing LLM provider authentication."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import typer

from eazy.ai.models import OAuthTokens, ProviderType
from eazy.ai.oauth_flow import OAuthError, OAuthFlowEngine
from eazy.ai.token_storage import TokenStorage

auth_app = typer.Typer(
    name="auth",
    help="Manage LLM provider authentication.",
)

VALID_PROVIDERS = [p.value for p in ProviderType]

OAUTH_PROVIDERS = {
    ProviderType.GEMINI_OAUTH.value,
    ProviderType.ANTIGRAVITY.value,
}

_OAUTH_CONFIGS: dict[str, dict] = {
    ProviderType.GEMINI_OAUTH.value: {
        "client_id_env": "EAZY_GEMINI_OAUTH_CLIENT_ID",
        "client_secret_env": "EAZY_GEMINI_OAUTH_CLIENT_SECRET",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": [
            "https://www.googleapis.com/auth/cloudaicompanion",
        ],
    },
    ProviderType.ANTIGRAVITY.value: {
        "client_id_env": "EAZY_ANTIGRAVITY_CLIENT_ID",
        "client_secret_env": "EAZY_ANTIGRAVITY_CLIENT_SECRET",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": [
            "https://www.googleapis.com/auth/cloudaicompanion",
        ],
    },
}


def _get_token_storage() -> TokenStorage:
    """Create a TokenStorage instance with default path.

    Returns:
        TokenStorage configured at ~/.eazy/tokens.
    """
    return TokenStorage(Path.home() / ".eazy" / "tokens")


@auth_app.command("login")
def login(
    provider: str = typer.Option(..., "--provider", help="LLM provider type."),
) -> None:
    """Authenticate with an LLM provider.

    Supports OAuth browser flow (gemini_oauth, antigravity)
    and API key input (gemini_api).

    Args:
        provider: Provider identifier string.
    """
    if provider not in VALID_PROVIDERS:
        typer.echo(f"Invalid provider: {provider}. Valid: {', '.join(VALID_PROVIDERS)}")
        raise typer.Exit(1)

    storage = _get_token_storage()

    if provider in OAUTH_PROVIDERS:
        _login_oauth(provider, storage)
    else:
        _login_api_key(provider, storage)


def _login_oauth(provider: str, storage: TokenStorage) -> None:
    """Run OAuth browser flow and save tokens.

    Args:
        provider: OAuth provider identifier.
        storage: Token storage instance.
    """
    config = _OAUTH_CONFIGS[provider]
    client_id = os.environ.get(config["client_id_env"], "")
    client_secret = os.environ.get(config["client_secret_env"], "")
    if not client_id or not client_secret:
        typer.echo(
            f"Missing OAuth credentials. Set "
            f"{config['client_id_env']} and "
            f"{config['client_secret_env']} env vars."
        )
        raise typer.Exit(1)

    engine = OAuthFlowEngine(
        client_id=client_id,
        client_secret=client_secret,
        auth_url=config["auth_url"],
        token_url=config["token_url"],
        scopes=config["scopes"],
    )

    try:
        tokens: OAuthTokens = asyncio.run(engine.run_interactive_flow())
    except OAuthError as e:
        typer.echo(f"Authentication failed: {e}")
        raise typer.Exit(1)

    storage.save(provider, "default", tokens.model_dump(mode="json"))
    typer.echo(f"Successfully authenticated with {provider}.")


def _login_api_key(provider: str, storage: TokenStorage) -> None:
    """Prompt for API key and save it.

    Args:
        provider: API key provider identifier.
        storage: Token storage instance.
    """
    api_key = typer.prompt("Enter API key", hide_input=True)
    storage.save(provider, "default", {"api_key": api_key})
    typer.echo(f"API key saved for {provider}.")
