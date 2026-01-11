"""
Phase 5 Day 2: Backend Dockerfile
TDD RED Phase - 테스트 작성

Backend Dockerfile 존재 및 유효성 검증
"""

from pathlib import Path


# 프로젝트 경로
BACKEND_ROOT = Path(__file__).parent.parent.parent  # backend/
PROJECT_ROOT = BACKEND_ROOT.parent  # EAZY/


class TestDockerfileExists:
    """Backend Dockerfile 존재 테스트"""

    def test_backend_dockerfile_exists(self):
        """backend/Dockerfile이 존재해야 함"""
        dockerfile = BACKEND_ROOT / "Dockerfile"
        assert dockerfile.exists(), f"Dockerfile not found at {dockerfile}"

    def test_dockerfile_has_from_instruction(self):
        """Dockerfile에 FROM 명령어가 있어야 함"""
        dockerfile = BACKEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "FROM" in content, "FROM instruction not found"

    def test_dockerfile_uses_python_312(self):
        """Dockerfile이 Python 3.12를 사용해야 함"""
        dockerfile = BACKEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "python:3.12" in content, "Python 3.12 image not used"


class TestDockerfileMultiStage:
    """Multi-stage build 테스트"""

    def test_dockerfile_has_builder_stage(self):
        """Dockerfile에 builder 스테이지가 있어야 함"""
        dockerfile = BACKEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "as builder" in content.lower(), "builder stage not found"

    def test_dockerfile_has_runtime_stage(self):
        """Dockerfile에 runtime 스테이지가 있어야 함"""
        dockerfile = BACKEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "as runtime" in content.lower(), "runtime stage not found"


class TestDockerfileUV:
    """uv 패키지 매니저 사용 테스트"""

    def test_dockerfile_copies_uv(self):
        """Dockerfile이 uv를 복사해야 함"""
        dockerfile = BACKEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "uv" in content, "uv not found in Dockerfile"

    def test_dockerfile_copies_pyproject(self):
        """Dockerfile이 pyproject.toml을 복사해야 함"""
        dockerfile = BACKEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "pyproject.toml" in content, "pyproject.toml not copied"


class TestDockerfilePlaywright:
    """Playwright 설정 테스트"""

    def test_dockerfile_installs_playwright_deps(self):
        """Dockerfile에 Playwright 시스템 의존성 설치가 있어야 함"""
        dockerfile = BACKEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        # Playwright에 필요한 주요 라이브러리 중 하나 확인
        assert (
            "libnss3" in content or "playwright install" in content
        ), "Playwright dependencies not found"

    def test_dockerfile_sets_playwright_path(self):
        """Dockerfile에 PLAYWRIGHT_BROWSERS_PATH가 설정되어야 함"""
        dockerfile = BACKEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "PLAYWRIGHT_BROWSERS_PATH" in content, "PLAYWRIGHT_BROWSERS_PATH not set"


class TestDockerfileExpose:
    """포트 및 실행 설정 테스트"""

    def test_dockerfile_exposes_port_8000(self):
        """Dockerfile이 포트 8000을 노출해야 함"""
        dockerfile = BACKEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "EXPOSE 8000" in content, "Port 8000 not exposed"

    def test_dockerfile_has_cmd(self):
        """Dockerfile에 CMD 명령어가 있어야 함"""
        dockerfile = BACKEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "CMD" in content, "CMD instruction not found"

    def test_dockerfile_runs_uvicorn(self):
        """Dockerfile CMD가 uvicorn을 실행해야 함"""
        dockerfile = BACKEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "uvicorn" in content, "uvicorn not in CMD"


class TestDockerfileHealthcheck:
    """Health check 설정 테스트"""

    def test_dockerfile_has_healthcheck(self):
        """Dockerfile에 HEALTHCHECK가 있어야 함"""
        dockerfile = BACKEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "HEALTHCHECK" in content, "HEALTHCHECK not found"
