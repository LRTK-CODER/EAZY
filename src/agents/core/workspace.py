"""Workspace manager for session-level directory CRUD."""

from __future__ import annotations

import asyncio
import secrets
import shutil
from pathlib import Path
from typing import Any, ClassVar

import yaml

from src.agents.core.models import SessionConfig


class WorkspaceManager:
    """Manages per-session workspace directories and config persistence."""

    _SUBDIRS: ClassVar[list[str]] = [
        "recon/scanner_results",
        "planning",
        "exploit/findings",
        "exploit/reflexion",
        "analysis",
        "http_history",
        "logs",
    ]

    def __init__(self, base_dir: str = "workspaces") -> None:
        self._base_dir = Path(base_dir)

    async def create(self, config: SessionConfig) -> str:
        """Create a new session workspace and persist config."""
        session_id = secrets.token_hex(4)
        session_dir = self._base_dir / session_id

        def _create() -> None:
            session_dir.mkdir(parents=True, exist_ok=True)
            for subdir in self._SUBDIRS:
                (session_dir / subdir).mkdir(parents=True, exist_ok=True)
            self._write_config(session_dir, config)

        await asyncio.to_thread(_create)
        return session_id

    async def list_sessions(self) -> list[dict[str, Any]]:
        """List all sessions with their config summaries."""

        def _list() -> list[dict[str, Any]]:
            if not self._base_dir.exists():
                return []
            results: list[dict[str, Any]] = []
            for entry in sorted(self._base_dir.iterdir()):
                config_path = entry / "config.yaml"
                if entry.is_dir() and config_path.is_file():
                    data = yaml.safe_load(config_path.read_text())
                    data["session_id"] = entry.name
                    results.append(data)
            return results

        return await asyncio.to_thread(_list)

    async def get(self, session_id: str) -> SessionConfig:
        """Load a session's config by ID."""

        def _get() -> SessionConfig:
            config_path = self._base_dir / session_id / "config.yaml"
            if not config_path.is_file():
                msg = f"Session not found: {session_id}"
                raise FileNotFoundError(msg)
            data = yaml.safe_load(config_path.read_text())
            return SessionConfig.model_validate(data)

        return await asyncio.to_thread(_get)

    async def delete(self, session_id: str) -> None:
        """Delete a session workspace entirely."""

        def _delete() -> None:
            session_dir = self._base_dir / session_id
            if not session_dir.is_dir():
                msg = f"Session not found: {session_id}"
                raise FileNotFoundError(msg)
            shutil.rmtree(session_dir)

        await asyncio.to_thread(_delete)

    async def save_config(self, session_id: str, config: SessionConfig) -> None:
        """Overwrite a session's config."""

        def _save() -> None:
            session_dir = self._base_dir / session_id
            if not session_dir.is_dir():
                msg = f"Session not found: {session_id}"
                raise FileNotFoundError(msg)
            self._write_config(session_dir, config)

        await asyncio.to_thread(_save)

    def get_workspace_path(self, session_id: str) -> Path:
        """Return the workspace path for a session (no I/O)."""
        return self._base_dir / session_id

    @staticmethod
    def _write_config(session_dir: Path, config: SessionConfig) -> None:
        """Serialize config to YAML using JSON-mode for datetime compat."""
        data = config.model_dump(mode="json")
        (session_dir / "config.yaml").write_text(
            yaml.safe_dump(data, default_flow_style=False)
        )
