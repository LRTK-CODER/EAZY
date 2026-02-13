"""Fernet-based encrypted token storage for LLM provider credentials."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import uuid
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class TokenStorage:
    """Encrypted file-based storage for OAuth tokens and API credentials.

    Stores token data as Fernet-encrypted JSON files organized by
    provider type and account ID. Files are created with restrictive
    permissions (0o600) for security.

    Args:
        base_dir: Directory for token files.
        encryption_key: Fernet key bytes. If None, derived from machine-id.
    """

    def __init__(self, base_dir: Path, encryption_key: bytes | None = None) -> None:
        self._base_dir = base_dir
        self._encryption_key = encryption_key or self._derive_key()
        self._fernet = Fernet(self._encryption_key)

    def save(self, provider_type: str, account_id: str, token_data: dict) -> None:
        """Encrypt and save token data to disk.

        Args:
            provider_type: Provider identifier (e.g., "gemini_oauth").
            account_id: Account identifier (e.g., email address).
            token_data: Token dictionary to encrypt and save.
        """
        token_path = self._token_path(provider_type, account_id)
        token_path.parent.mkdir(parents=True, exist_ok=True)

        json_data = json.dumps(token_data).encode("utf-8")
        encrypted_data = self._fernet.encrypt(json_data)

        token_path.write_bytes(encrypted_data)
        os.chmod(token_path, 0o600)

    def load(self, provider_type: str, account_id: str) -> dict | None:
        """Load and decrypt token data. Returns None if missing or corrupted.

        Args:
            provider_type: Provider identifier (e.g., "gemini_oauth").
            account_id: Account identifier (e.g., email address).

        Returns:
            Decrypted token dictionary, or None if file missing or corrupted.
        """
        token_path = self._token_path(provider_type, account_id)

        try:
            encrypted_data = token_path.read_bytes()
            decrypted_data = self._fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode("utf-8"))
        except FileNotFoundError:
            return None
        except InvalidToken:
            return None

    def delete(self, provider_type: str, account_id: str) -> bool:
        """Delete token file. Returns True if deleted, False if not found.

        Args:
            provider_type: Provider identifier (e.g., "gemini_oauth").
            account_id: Account identifier (e.g., email address).

        Returns:
            True if file was deleted, False if file did not exist.
        """
        token_path = self._token_path(provider_type, account_id)

        try:
            token_path.unlink()
            return True
        except FileNotFoundError:
            return False

    def list_accounts(self, provider_type: str) -> list[str]:
        """List account IDs for a provider type.

        Args:
            provider_type: Provider identifier (e.g., "gemini_oauth").

        Returns:
            List of account IDs (filenames with .json.enc suffix removed).
        """
        provider_dir = self._base_dir / provider_type

        if not provider_dir.exists():
            return []

        accounts = []
        for file_path in provider_dir.glob("*.json.enc"):
            account_id = file_path.name[: -len(".json.enc")]
            accounts.append(account_id)

        return sorted(accounts)

    def _token_path(self, provider_type: str, account_id: str) -> Path:
        """Build file path: {base_dir}/{provider_type}/{account_id}.json.enc

        Args:
            provider_type: Provider identifier.
            account_id: Account identifier.

        Returns:
            Full path to encrypted token file.
        """
        return self._base_dir / provider_type / f"{account_id}.json.enc"

    def _derive_key(self) -> bytes:
        """Derive encryption key from machine-specific identifier.

        Uses PBKDF2-HMAC-SHA256 with 480,000 iterations to derive a Fernet
        key from the machine ID.

        Returns:
            32-byte Fernet-compatible encryption key.
        """
        machine_id = self._get_machine_id()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"eazy-token-storage-v1",
            iterations=480_000,
        )
        key = kdf.derive(machine_id.encode("utf-8"))
        return base64.urlsafe_b64encode(key)

    def _get_machine_id(self) -> str:
        """Get machine-specific identifier for key derivation.

        Tries in order:
        1. /etc/machine-id (Linux)
        2. macOS IOPlatformUUID via ioreg
        3. uuid.getnode() as fallback

        Returns:
            Machine identifier string.
        """
        machine_id_path = Path("/etc/machine-id")
        if machine_id_path.exists():
            return machine_id_path.read_text().strip()

        try:
            result = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            for line in result.stdout.splitlines():
                if "IOPlatformUUID" in line:
                    uuid_value = line.split('"')[3]
                    return uuid_value
        except (subprocess.SubprocessError, FileNotFoundError, IndexError):
            pass

        return str(uuid.getnode())
