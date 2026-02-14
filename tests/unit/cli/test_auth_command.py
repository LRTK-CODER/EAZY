"""Unit tests for the auth CLI command."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from eazy.ai.models import OAuthTokens
from eazy.cli.app import app

runner = CliRunner()


class TestAuthCommandStructure:
    """Tests for auth command group structure."""

    def test_auth_help_shows_usage(self):
        """auth --help shows usage text with exit_code 0."""
        result = runner.invoke(app, ["auth", "--help"])
        assert result.exit_code == 0
        assert "login" in result.output

    def test_auth_login_help_shows_provider_option(self):
        """auth login --help shows --provider option."""
        result = runner.invoke(app, ["auth", "login", "--help"])
        assert result.exit_code == 0
        assert "--provider" in result.output

    def test_auth_login_requires_provider_option(self):
        """auth login without --provider fails."""
        result = runner.invoke(app, ["auth", "login"])
        assert result.exit_code != 0

    def test_auth_login_rejects_unknown_provider(self):
        """auth login --provider unknown shows error."""
        result = runner.invoke(app, ["auth", "login", "--provider", "unknown"])
        assert result.exit_code != 0
        assert "Invalid provider" in result.output or "unknown" in result.output


class TestAuthLoginOAuth:
    """Tests for OAuth login flow."""

    _OAUTH_ENV = {
        "EAZY_GEMINI_OAUTH_CLIENT_ID": "test-client-id",
        "EAZY_GEMINI_OAUTH_CLIENT_SECRET": "test-client-secret",
    }

    @patch.dict(os.environ, _OAUTH_ENV)
    @patch("eazy.cli.auth.TokenStorage")
    @patch("eazy.cli.auth.OAuthFlowEngine")
    def test_auth_login_gemini_oauth_triggers_interactive_flow(
        self, mock_flow_cls, mock_storage_cls
    ):
        """gemini_oauth provider triggers OAuthFlowEngine flow."""
        mock_flow = AsyncMock()
        mock_flow.run_interactive_flow.return_value = OAuthTokens(
            access_token="test-token",
            refresh_token="test-refresh",
            expires_at=datetime.now(timezone.utc),
            scope="test-scope",
        )
        mock_flow_cls.return_value = mock_flow

        result = runner.invoke(app, ["auth", "login", "--provider", "gemini_oauth"])

        assert result.exit_code == 0
        mock_flow.run_interactive_flow.assert_called_once()

    @patch.dict(os.environ, _OAUTH_ENV)
    @patch("eazy.cli.auth.TokenStorage")
    @patch("eazy.cli.auth.OAuthFlowEngine")
    def test_auth_login_gemini_oauth_saves_token(self, mock_flow_cls, mock_storage_cls):
        """Successful OAuth login saves tokens via TokenStorage.save()."""
        mock_flow = AsyncMock()
        mock_flow.run_interactive_flow.return_value = OAuthTokens(
            access_token="test-token",
            refresh_token="test-refresh",
            expires_at=None,
            scope="test-scope",
        )
        mock_flow_cls.return_value = mock_flow
        mock_storage = mock_storage_cls.return_value

        result = runner.invoke(app, ["auth", "login", "--provider", "gemini_oauth"])

        assert result.exit_code == 0
        mock_storage.save.assert_called_once()
        call_args = mock_storage.save.call_args
        assert call_args[0][0] == "gemini_oauth"  # provider_type
        assert call_args[0][1] == "default"  # account_id

    @patch.dict(os.environ, _OAUTH_ENV)
    @patch("eazy.cli.auth.TokenStorage")
    @patch("eazy.cli.auth.OAuthFlowEngine")
    def test_auth_login_gemini_oauth_shows_success_message(
        self, mock_flow_cls, mock_storage_cls
    ):
        """Successful OAuth login shows success message."""
        mock_flow = AsyncMock()
        mock_flow.run_interactive_flow.return_value = OAuthTokens(
            access_token="test-token",
            refresh_token=None,
            expires_at=None,
            scope="",
        )
        mock_flow_cls.return_value = mock_flow

        result = runner.invoke(app, ["auth", "login", "--provider", "gemini_oauth"])

        assert result.exit_code == 0
        assert "Successfully authenticated" in result.output


class TestAuthLoginApiKey:
    """Tests for API key login flow."""

    @patch("eazy.cli.auth.TokenStorage")
    def test_auth_login_gemini_api_prompts_for_key(self, mock_storage_cls):
        """gemini_api provider prompts for API key input."""
        result = runner.invoke(
            app,
            ["auth", "login", "--provider", "gemini_api"],
            input="test-api-key\n",
        )
        assert result.exit_code == 0

    @patch("eazy.cli.auth.TokenStorage")
    def test_auth_login_gemini_api_saves_key(self, mock_storage_cls):
        """API key is saved via TokenStorage.save()."""
        mock_storage = mock_storage_cls.return_value

        result = runner.invoke(
            app,
            ["auth", "login", "--provider", "gemini_api"],
            input="test-api-key\n",
        )

        assert result.exit_code == 0
        mock_storage.save.assert_called_once()
        call_args = mock_storage.save.call_args
        assert call_args[0][0] == "gemini_api"  # provider_type
        assert call_args[0][1] == "default"  # account_id
        token_data = call_args[0][2]
        assert token_data["api_key"] == "test-api-key"

    @patch("eazy.cli.auth.TokenStorage")
    def test_auth_login_gemini_api_shows_success_message(self, mock_storage_cls):
        """Successful API key save shows confirmation message."""
        result = runner.invoke(
            app,
            ["auth", "login", "--provider", "gemini_api"],
            input="test-api-key\n",
        )
        assert result.exit_code == 0
        assert "API key saved" in result.output
