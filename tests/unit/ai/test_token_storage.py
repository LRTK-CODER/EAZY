"""Unit tests for TokenStorage class (TDD RED phase).

This module tests the secure token persistence layer for LLM providers.
TokenStorage encrypts and stores OAuth tokens and API keys in a local
file-based storage with proper isolation by provider and account.

The production code does NOT exist yet - these tests will FAIL until
eazy.ai.token_storage.TokenStorage is implemented.
"""

from __future__ import annotations

from pathlib import Path

from cryptography.fernet import Fernet

from eazy.ai.token_storage import TokenStorage


class TestTokenStorage:
    """Test suite for TokenStorage secure token persistence."""

    def test_token_storage_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        """Save token data and load it back — values match."""
        test_key = Fernet.generate_key()
        storage = TokenStorage(base_dir=tmp_path, encryption_key=test_key)
        token_data = {
            "access_token": "abc123",
            "refresh_token": "def456",
        }

        storage.save("gemini_oauth", "user@example.com", token_data)
        loaded = storage.load("gemini_oauth", "user@example.com")

        assert loaded == token_data

    def test_token_storage_returns_none_for_missing_token(self, tmp_path: Path) -> None:
        """Load nonexistent token returns None."""
        test_key = Fernet.generate_key()
        storage = TokenStorage(base_dir=tmp_path, encryption_key=test_key)

        loaded = storage.load("gemini_oauth", "nonexistent@example.com")

        assert loaded is None

    def test_token_storage_file_is_encrypted(self, tmp_path: Path) -> None:
        """Raw file bytes are not plaintext JSON."""
        test_key = Fernet.generate_key()
        storage = TokenStorage(base_dir=tmp_path, encryption_key=test_key)
        token_data = {"access_token": "secret_value_abc123"}

        storage.save("gemini_oauth", "user@example.com", token_data)

        file_path = tmp_path / "gemini_oauth" / "user@example.com.json.enc"
        raw_bytes = file_path.read_bytes()
        assert b"access_token" not in raw_bytes
        assert b"secret_value_abc123" not in raw_bytes

    def test_token_storage_handles_corrupted_file(self, tmp_path: Path) -> None:
        """Corrupted/garbage file returns None on load."""
        test_key = Fernet.generate_key()
        storage = TokenStorage(base_dir=tmp_path, encryption_key=test_key)

        provider_dir = tmp_path / "gemini_oauth"
        provider_dir.mkdir(parents=True, exist_ok=True)
        corrupted_file = provider_dir / "user@example.com.json.enc"
        corrupted_file.write_bytes(b"garbage_data_not_valid_encryption")

        loaded = storage.load("gemini_oauth", "user@example.com")

        assert loaded is None

    def test_token_storage_isolates_by_provider_and_account(
        self, tmp_path: Path
    ) -> None:
        """Different provider+account combos store independently."""
        test_key = Fernet.generate_key()
        storage = TokenStorage(base_dir=tmp_path, encryption_key=test_key)

        gemini_data = {"access_token": "gemini_token_123"}
        openai_data = {"api_key": "openai_key_456"}

        storage.save("gemini_oauth", "user@example.com", gemini_data)
        storage.save("openai_api", "admin@example.com", openai_data)

        loaded_gemini = storage.load("gemini_oauth", "user@example.com")
        loaded_openai = storage.load("openai_api", "admin@example.com")

        assert loaded_gemini == gemini_data
        assert loaded_openai == openai_data

    def test_token_storage_delete_token(self, tmp_path: Path) -> None:
        """Delete removes token, returns True. Load after returns None."""
        test_key = Fernet.generate_key()
        storage = TokenStorage(base_dir=tmp_path, encryption_key=test_key)
        token_data = {"access_token": "temp_token"}

        storage.save("gemini_oauth", "user@example.com", token_data)
        delete_result = storage.delete("gemini_oauth", "user@example.com")

        assert delete_result is True

        loaded = storage.load("gemini_oauth", "user@example.com")
        assert loaded is None

        delete_nonexistent = storage.delete("gemini_oauth", "nonexistent@example.com")
        assert delete_nonexistent is False

    def test_token_storage_list_stored_accounts(self, tmp_path: Path) -> None:
        """After saving 3 accounts for a provider, list returns 3 IDs."""
        test_key = Fernet.generate_key()
        storage = TokenStorage(base_dir=tmp_path, encryption_key=test_key)

        storage.save("gemini_oauth", "user1@example.com", {"token": "a"})
        storage.save("gemini_oauth", "user2@example.com", {"token": "b"})
        storage.save("gemini_oauth", "user3@example.com", {"token": "c"})
        storage.save("openai_api", "admin@example.com", {"key": "d"})

        gemini_accounts = storage.list_accounts("gemini_oauth")

        assert len(gemini_accounts) == 3
        assert "user1@example.com" in gemini_accounts
        assert "user2@example.com" in gemini_accounts
        assert "user3@example.com" in gemini_accounts

    def test_token_storage_uses_secure_file_permissions(self, tmp_path: Path) -> None:
        """Saved file has mode 0o600 (owner read/write only)."""
        test_key = Fernet.generate_key()
        storage = TokenStorage(base_dir=tmp_path, encryption_key=test_key)
        token_data = {"access_token": "secure_token"}

        storage.save("gemini_oauth", "user@example.com", token_data)

        file_path = tmp_path / "gemini_oauth" / "user@example.com.json.enc"
        mode = file_path.stat().st_mode & 0o777
        assert mode == 0o600
