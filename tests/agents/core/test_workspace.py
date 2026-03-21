"""Tests for WorkspaceManager — session workspace CRUD."""

import re
from pathlib import Path

import pytest
import yaml

from src.agents.core.models import SessionConfig
from src.agents.core.workspace import WorkspaceManager


def _make_config(
    name: str = "test-session",
    target: str = "https://example.com",
) -> SessionConfig:
    """Factory helper for SessionConfig."""
    return SessionConfig(session_name=name, target_url=target)


class TestCreateSession:
    async def test_create_session(self, tmp_path: Path) -> None:
        mgr = WorkspaceManager(base_dir=str(tmp_path))
        sid = await mgr.create(_make_config())
        session_dir = tmp_path / sid
        assert session_dir.is_dir()
        assert (session_dir / "config.yaml").is_file()

    async def test_create_session_directory_structure(self, tmp_path: Path) -> None:
        mgr = WorkspaceManager(base_dir=str(tmp_path))
        sid = await mgr.create(_make_config())
        expected = [
            "recon/scanner_results",
            "planning",
            "exploit/findings",
            "exploit/reflexion",
            "analysis",
            "http_history",
            "logs",
        ]
        for subdir in expected:
            assert (tmp_path / sid / subdir).is_dir(), f"Missing subdir: {subdir}"

    async def test_create_session_returns_hex_id(self, tmp_path: Path) -> None:
        mgr = WorkspaceManager(base_dir=str(tmp_path))
        sid = await mgr.create(_make_config())
        assert re.fullmatch(r"[0-9a-f]{8}", sid), f"Not 8-char hex: {sid}"

    async def test_create_session_config_persisted(self, tmp_path: Path) -> None:
        mgr = WorkspaceManager(base_dir=str(tmp_path))
        cfg = _make_config(name="persist-test", target="https://target.io")
        sid = await mgr.create(cfg)
        raw = yaml.safe_load((tmp_path / sid / "config.yaml").read_text())
        restored = SessionConfig.model_validate(raw)
        assert restored.session_name == cfg.session_name
        assert restored.target_url == cfg.target_url


class TestListSessions:
    async def test_list_sessions_empty(self, tmp_path: Path) -> None:
        mgr = WorkspaceManager(base_dir=str(tmp_path))
        result = await mgr.list_sessions()
        assert result == []

    async def test_list_sessions_multiple(self, tmp_path: Path) -> None:
        mgr = WorkspaceManager(base_dir=str(tmp_path))
        await mgr.create(_make_config(name="s1"))
        await mgr.create(_make_config(name="s2"))
        result = await mgr.list_sessions()
        assert len(result) == 2
        names = {item["session_name"] for item in result}
        assert names == {"s1", "s2"}


class TestGetSession:
    async def test_get_session(self, tmp_path: Path) -> None:
        mgr = WorkspaceManager(base_dir=str(tmp_path))
        cfg = _make_config(name="get-test")
        sid = await mgr.create(cfg)
        restored = await mgr.get(sid)
        assert restored.session_name == "get-test"
        assert restored.target_url == cfg.target_url

    async def test_get_session_not_found(self, tmp_path: Path) -> None:
        mgr = WorkspaceManager(base_dir=str(tmp_path))
        with pytest.raises(FileNotFoundError):
            await mgr.get("deadbeef")


class TestDeleteSession:
    async def test_delete_session(self, tmp_path: Path) -> None:
        mgr = WorkspaceManager(base_dir=str(tmp_path))
        sid = await mgr.create(_make_config())
        await mgr.delete(sid)
        assert not (tmp_path / sid).exists()

    async def test_delete_session_not_found(self, tmp_path: Path) -> None:
        mgr = WorkspaceManager(base_dir=str(tmp_path))
        with pytest.raises(FileNotFoundError):
            await mgr.delete("deadbeef")


class TestSessionIsolation:
    async def test_session_isolation(self, tmp_path: Path) -> None:
        mgr = WorkspaceManager(base_dir=str(tmp_path))
        sid_a = await mgr.create(_make_config(name="A"))
        sid_b = await mgr.create(_make_config(name="B"))
        await mgr.delete(sid_a)
        restored_b = await mgr.get(sid_b)
        assert restored_b.session_name == "B"


class TestSaveConfig:
    async def test_save_config_update(self, tmp_path: Path) -> None:
        mgr = WorkspaceManager(base_dir=str(tmp_path))
        sid = await mgr.create(_make_config())
        updated = _make_config(name="updated-name", target="https://new.target")
        await mgr.save_config(sid, updated)
        restored = await mgr.get(sid)
        assert restored.session_name == "updated-name"
        assert restored.target_url == "https://new.target"


class TestGetWorkspacePath:
    async def test_get_workspace_path(self, tmp_path: Path) -> None:
        mgr = WorkspaceManager(base_dir=str(tmp_path))
        path = mgr.get_workspace_path("abcd1234")
        assert path == tmp_path / "abcd1234"
