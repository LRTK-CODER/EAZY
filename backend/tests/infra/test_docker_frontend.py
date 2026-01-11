"""
Phase 5 Day 3: Frontend Dockerfile + Nginx
TDD RED Phase - 테스트 작성

Frontend Dockerfile 및 Nginx 설정 검증
"""

from pathlib import Path


# 프로젝트 경로
BACKEND_ROOT = Path(__file__).parent.parent.parent  # backend/
PROJECT_ROOT = BACKEND_ROOT.parent  # EAZY/
FRONTEND_ROOT = PROJECT_ROOT / "frontend"


class TestFrontendDockerfileExists:
    """Frontend Dockerfile 존재 테스트"""

    def test_frontend_dockerfile_exists(self):
        """frontend/Dockerfile이 존재해야 함"""
        dockerfile = FRONTEND_ROOT / "Dockerfile"
        assert dockerfile.exists(), f"Dockerfile not found at {dockerfile}"

    def test_dockerfile_has_from_instruction(self):
        """Dockerfile에 FROM 명령어가 있어야 함"""
        dockerfile = FRONTEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "FROM" in content, "FROM instruction not found"

    def test_dockerfile_uses_node(self):
        """Dockerfile이 Node.js 이미지를 사용해야 함"""
        dockerfile = FRONTEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "node:" in content.lower(), "Node.js image not used"


class TestFrontendMultiStage:
    """Multi-stage build 테스트"""

    def test_dockerfile_has_builder_stage(self):
        """Dockerfile에 builder 스테이지가 있어야 함"""
        dockerfile = FRONTEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "as builder" in content.lower(), "builder stage not found"

    def test_dockerfile_has_runtime_stage(self):
        """Dockerfile에 runtime 또는 nginx 스테이지가 있어야 함"""
        dockerfile = FRONTEND_ROOT / "Dockerfile"
        content = dockerfile.read_text().lower()
        assert (
            "as runtime" in content or "nginx" in content
        ), "runtime/nginx stage not found"


class TestFrontendBuild:
    """Frontend 빌드 설정 테스트"""

    def test_dockerfile_runs_npm_ci(self):
        """Dockerfile이 npm ci를 실행해야 함"""
        dockerfile = FRONTEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert (
            "npm ci" in content or "npm install" in content
        ), "npm ci/install not found"

    def test_dockerfile_runs_npm_build(self):
        """Dockerfile이 npm run build를 실행해야 함"""
        dockerfile = FRONTEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "npm run build" in content, "npm run build not found"


class TestNginxConfig:
    """Nginx 설정 테스트"""

    def test_nginx_conf_exists(self):
        """frontend/nginx.conf가 존재해야 함"""
        nginx_conf = FRONTEND_ROOT / "nginx.conf"
        assert nginx_conf.exists(), f"nginx.conf not found at {nginx_conf}"

    def test_nginx_conf_has_server_block(self):
        """nginx.conf에 server 블록이 있어야 함"""
        nginx_conf = FRONTEND_ROOT / "nginx.conf"
        content = nginx_conf.read_text()
        assert "server {" in content or "server{" in content, "server block not found"

    def test_nginx_conf_has_spa_routing(self):
        """nginx.conf에 SPA 라우팅 설정이 있어야 함 (try_files)"""
        nginx_conf = FRONTEND_ROOT / "nginx.conf"
        content = nginx_conf.read_text()
        assert "try_files" in content, "SPA routing (try_files) not found"

    def test_nginx_conf_has_api_proxy(self):
        """nginx.conf에 API 프록시 설정이 있어야 함"""
        nginx_conf = FRONTEND_ROOT / "nginx.conf"
        content = nginx_conf.read_text()
        assert "proxy_pass" in content, "API proxy not found"

    def test_nginx_conf_proxies_to_backend(self):
        """nginx.conf가 backend 서비스로 프록시해야 함"""
        nginx_conf = FRONTEND_ROOT / "nginx.conf"
        content = nginx_conf.read_text()
        assert (
            "backend" in content or "8000" in content
        ), "backend proxy target not found"


class TestDockerfileExpose:
    """포트 노출 테스트"""

    def test_dockerfile_exposes_port_80(self):
        """Dockerfile이 포트 80을 노출해야 함"""
        dockerfile = FRONTEND_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "EXPOSE 80" in content, "Port 80 not exposed"
