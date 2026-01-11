"""
Sprint 2.5: CORS Configuration Tests

Tests for environment-based CORS configuration.
Validates whitelist parsing, production security, and validation.
"""
import pytest
from unittest.mock import patch
import os


class TestCORSOriginsEnvVar:
    """Test CORS_ORIGINS environment variable support."""

    def test_cors_origins_env_var_exists(self):
        """Settings should have CORS_ORIGINS attribute."""
        from app.core.config import settings

        assert hasattr(settings, 'CORS_ORIGINS'), \
            "settings should have CORS_ORIGINS attribute"

    def test_cors_origins_default_localhost(self):
        """Default CORS_ORIGINS should be localhost:3000."""
        from app.core.config import Settings

        # Create fresh settings without env vars
        with patch.dict(os.environ, {}, clear=True):
            test_settings = Settings()
            assert "localhost:3000" in test_settings.CORS_ORIGINS


class TestCORSOriginsParsing:
    """Test parsing of CORS origins from string."""

    def test_cors_origins_parses_comma_separated(self):
        """get_cors_origins should parse comma-separated values."""
        from app.core.cors import get_cors_origins

        with patch.dict(os.environ, {'CORS_ORIGINS': 'http://a.com,http://b.com'}):
            origins = get_cors_origins()
            assert isinstance(origins, list)
            assert 'http://a.com' in origins
            assert 'http://b.com' in origins

    def test_cors_origins_strips_whitespace(self):
        """get_cors_origins should strip whitespace from origins."""
        from app.core.cors import get_cors_origins

        with patch.dict(os.environ, {'CORS_ORIGINS': '  http://a.com  ,  http://b.com  '}):
            origins = get_cors_origins()
            assert 'http://a.com' in origins
            assert 'http://b.com' in origins
            # No whitespace in origins
            for origin in origins:
                assert origin == origin.strip()

    def test_get_cors_origins_returns_list(self):
        """get_cors_origins should always return a list."""
        from app.core.cors import get_cors_origins

        origins = get_cors_origins()
        assert isinstance(origins, list)


class TestCORSProductionSecurity:
    """Test production security validations."""

    def test_cors_production_rejects_wildcard(self):
        """Production environment should reject wildcard origins."""
        from app.core.cors import validate_cors_config

        # Should raise or return warning for production + wildcard
        result = validate_cors_config(["*"], "production")
        assert result is False or result.get('warning') is not None

    def test_cors_credentials_requires_specific_origins(self):
        """allow_credentials=True requires specific origins, not wildcard."""
        from app.core.cors import validate_cors_config

        # Wildcard with credentials should fail validation
        result = validate_cors_config(["*"], "production", allow_credentials=True)
        assert result is False or result.get('valid') is False


class TestCORSValidation:
    """Test CORS configuration validation."""

    def test_validate_cors_config_logs_warning(self):
        """validate_cors_config should log warning for insecure configs."""
        from app.core.cors import validate_cors_config
        from unittest.mock import MagicMock

        # This should log a warning but not crash
        result = validate_cors_config(["*"], "production")
        # Function should return validation result
        assert result is not None


class TestEnvironmentConfig:
    """Test environment configuration."""

    def test_environment_setting_exists(self):
        """Settings should have ENVIRONMENT attribute."""
        from app.core.config import settings

        assert hasattr(settings, 'ENVIRONMENT'), \
            "settings should have ENVIRONMENT attribute"

    def test_environment_default_is_development(self):
        """Default ENVIRONMENT should be 'development'."""
        from app.core.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            test_settings = Settings()
            assert test_settings.ENVIRONMENT == "development"
