from __future__ import annotations

from pathlib import Path

from eazy.ai.credentials import TokenStorage
from eazy.ai.models import ApiKeyEntry, AuthEntry, OAuthTokens


class TestTokenStorage:
    def test_load_no_file_returns_empty_dict(self, tmp_path: Path) -> None:
        """Loading when no file exists returns empty dict."""
        storage = TokenStorage(path=tmp_path / "auth.json")
        result = storage.load()
        assert result == {}

    def test_save_and_load_oauth_entry(self, tmp_path: Path) -> None:
        """Save OAuth entry then load returns matching entry."""
        storage = TokenStorage(path=tmp_path / "auth.json")
        entry = AuthEntry(
            type="oauth",
            oauth=OAuthTokens(
                access_token="acc123",
                refresh_token="ref456",
                expires_at=1700000000,
            ),
        )
        storage.save("gemini", entry)
        loaded = storage.load()
        assert "gemini" in loaded
        assert loaded["gemini"].type == "oauth"
        assert loaded["gemini"].oauth.access_token == "acc123"

    def test_save_and_load_api_entry(self, tmp_path: Path) -> None:
        """Save API key entry then load returns matching entry."""
        storage = TokenStorage(path=tmp_path / "auth.json")
        entry = AuthEntry(type="api", api=ApiKeyEntry(key="my-api-key"))
        storage.save("gemini-api", entry)
        loaded = storage.load()
        assert loaded["gemini-api"].type == "api"
        assert loaded["gemini-api"].api.key == "my-api-key"

    def test_directory_auto_creation(self, tmp_path: Path) -> None:
        """Saving creates parent directories automatically."""
        path = tmp_path / "nested" / "deep" / "auth.json"
        storage = TokenStorage(path=path)
        entry = AuthEntry(type="api", api=ApiKeyEntry(key="k"))
        storage.save("test", entry)
        assert path.exists()

    def test_get_existing_key(self, tmp_path: Path) -> None:
        """Get returns entry for existing key."""
        storage = TokenStorage(path=tmp_path / "auth.json")
        entry = AuthEntry(type="api", api=ApiKeyEntry(key="k"))
        storage.save("test", entry)
        result = storage.get("test")
        assert result is not None
        assert result.api.key == "k"

    def test_get_nonexistent_key_returns_none(self, tmp_path: Path) -> None:
        """Get returns None for nonexistent key."""
        storage = TokenStorage(path=tmp_path / "auth.json")
        assert storage.get("missing") is None

    def test_remove_entry(self, tmp_path: Path) -> None:
        """Remove deletes entry, subsequent get returns None."""
        storage = TokenStorage(path=tmp_path / "auth.json")
        entry = AuthEntry(type="api", api=ApiKeyEntry(key="k"))
        storage.save("test", entry)
        storage.remove("test")
        assert storage.get("test") is None
