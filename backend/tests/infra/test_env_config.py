"""
Phase 5 Day 1: 환경 설정 + Makefile
TDD RED Phase - 테스트 작성

환경 설정 파일과 Makefile 존재 및 필수 내용 검증
"""

import os
from pathlib import Path

import pytest

# 프로젝트 루트 경로
# tests/infra/test_env_config.py → backend/tests/infra/test_env_config.py
# parent.parent.parent = backend/
# parent.parent.parent.parent = EAZY/
BACKEND_ROOT = Path(__file__).parent.parent.parent  # backend/
PROJECT_ROOT = BACKEND_ROOT.parent  # EAZY/
FRONTEND_ROOT = PROJECT_ROOT / "frontend"


class TestEnvExample:
    """Backend .env.example 파일 테스트"""

    def test_env_example_exists(self):
        """backend/.env.example 파일이 존재해야 함"""
        env_example = BACKEND_ROOT / ".env.example"
        assert env_example.exists(), f".env.example not found at {env_example}"

    def test_env_example_has_database_url(self):
        """backend/.env.example에 DATABASE_URL이 포함되어야 함"""
        env_example = BACKEND_ROOT / ".env.example"
        content = env_example.read_text()
        assert "DATABASE_URL" in content, "DATABASE_URL not found in .env.example"

    def test_env_example_has_redis_url(self):
        """backend/.env.example에 REDIS_URL이 포함되어야 함"""
        env_example = BACKEND_ROOT / ".env.example"
        content = env_example.read_text()
        assert "REDIS_URL" in content, "REDIS_URL not found in .env.example"

    def test_env_example_has_worker_config(self):
        """backend/.env.example에 WORKER 설정이 포함되어야 함"""
        env_example = BACKEND_ROOT / ".env.example"
        content = env_example.read_text()
        assert "WORKER_NUM_WORKERS" in content, "WORKER_NUM_WORKERS not found"


class TestFrontendEnvExample:
    """Frontend .env.example 파일 테스트"""

    def test_frontend_env_example_exists(self):
        """frontend/.env.example 파일이 존재해야 함"""
        env_example = FRONTEND_ROOT / ".env.example"
        assert env_example.exists(), f".env.example not found at {env_example}"

    def test_frontend_env_example_has_api_url(self):
        """frontend/.env.example에 VITE_API_URL이 포함되어야 함"""
        env_example = FRONTEND_ROOT / ".env.example"
        content = env_example.read_text()
        assert "VITE_API_URL" in content, "VITE_API_URL not found"


class TestMakefile:
    """프로젝트 루트 Makefile 테스트"""

    def test_makefile_exists(self):
        """프로젝트 루트에 Makefile이 존재해야 함"""
        makefile = PROJECT_ROOT / "Makefile"
        assert makefile.exists(), f"Makefile not found at {makefile}"

    def test_makefile_has_dev_target(self):
        """Makefile에 dev 타겟이 존재해야 함"""
        makefile = PROJECT_ROOT / "Makefile"
        content = makefile.read_text()
        assert "dev:" in content, "dev target not found in Makefile"

    def test_makefile_has_test_target(self):
        """Makefile에 test 타겟이 존재해야 함"""
        makefile = PROJECT_ROOT / "Makefile"
        content = makefile.read_text()
        assert "test:" in content, "test target not found in Makefile"

    def test_makefile_has_lint_target(self):
        """Makefile에 lint 타겟이 존재해야 함"""
        makefile = PROJECT_ROOT / "Makefile"
        content = makefile.read_text()
        assert "lint:" in content, "lint target not found in Makefile"

    def test_makefile_has_build_target(self):
        """Makefile에 build 타겟이 존재해야 함"""
        makefile = PROJECT_ROOT / "Makefile"
        content = makefile.read_text()
        assert "build:" in content, "build target not found in Makefile"

    def test_makefile_has_up_target(self):
        """Makefile에 up 타겟이 존재해야 함"""
        makefile = PROJECT_ROOT / "Makefile"
        content = makefile.read_text()
        assert "up:" in content, "up target not found in Makefile"

    def test_makefile_has_down_target(self):
        """Makefile에 down 타겟이 존재해야 함"""
        makefile = PROJECT_ROOT / "Makefile"
        content = makefile.read_text()
        assert "down:" in content, "down target not found in Makefile"

    def test_makefile_uses_uv(self):
        """Makefile이 uv 명령어를 사용해야 함"""
        makefile = PROJECT_ROOT / "Makefile"
        content = makefile.read_text()
        assert "uv run" in content, "uv run not found in Makefile"
