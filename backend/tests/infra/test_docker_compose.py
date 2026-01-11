"""
Phase 5 Day 4: Docker Compose 통합
TDD RED Phase - 테스트 작성

Docker Compose 파일의 모든 서비스 정의 검증
"""

from pathlib import Path

import pytest
import yaml

# 프로젝트 경로
BACKEND_ROOT = Path(__file__).parent.parent.parent  # backend/
PROJECT_ROOT = BACKEND_ROOT.parent  # EAZY/


@pytest.fixture
def compose_config():
    """docker-compose.yml 파일 로드"""
    compose_file = PROJECT_ROOT / "docker-compose.yml"
    content = compose_file.read_text()
    return yaml.safe_load(content)


class TestComposeFileExists:
    """Docker Compose 파일 존재 테스트"""

    def test_compose_file_exists(self):
        """프로젝트 루트에 docker-compose.yml이 존재해야 함"""
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        assert compose_file.exists(), f"docker-compose.yml not found at {compose_file}"

    def test_compose_file_valid_yaml(self):
        """docker-compose.yml이 유효한 YAML이어야 함"""
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        content = compose_file.read_text()
        try:
            config = yaml.safe_load(content)
            assert config is not None, "Empty YAML file"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML: {e}")


class TestComposeServices:
    """Docker Compose 서비스 정의 테스트"""

    def test_has_services_key(self, compose_config):
        """services 키가 존재해야 함"""
        assert "services" in compose_config, "services key not found"

    def test_has_db_service(self, compose_config):
        """db 서비스가 정의되어야 함"""
        services = compose_config.get("services", {})
        assert "db" in services, "db service not found"

    def test_has_redis_service(self, compose_config):
        """redis 서비스가 정의되어야 함"""
        services = compose_config.get("services", {})
        assert "redis" in services, "redis service not found"

    def test_has_backend_service(self, compose_config):
        """backend 서비스가 정의되어야 함"""
        services = compose_config.get("services", {})
        assert "backend" in services, "backend service not found"

    def test_has_worker_service(self, compose_config):
        """worker 서비스가 정의되어야 함"""
        services = compose_config.get("services", {})
        assert "worker" in services, "worker service not found"

    def test_has_frontend_service(self, compose_config):
        """frontend 서비스가 정의되어야 함"""
        services = compose_config.get("services", {})
        assert "frontend" in services, "frontend service not found"


class TestDbService:
    """Database 서비스 설정 테스트"""

    def test_db_uses_postgres(self, compose_config):
        """db 서비스가 PostgreSQL 이미지를 사용해야 함"""
        db = compose_config["services"]["db"]
        assert "postgres" in db.get("image", ""), "PostgreSQL image not used"

    def test_db_has_healthcheck(self, compose_config):
        """db 서비스에 healthcheck가 있어야 함"""
        db = compose_config["services"]["db"]
        assert "healthcheck" in db, "db healthcheck not found"


class TestRedisService:
    """Redis 서비스 설정 테스트"""

    def test_redis_uses_redis_image(self, compose_config):
        """redis 서비스가 Redis 이미지를 사용해야 함"""
        redis = compose_config["services"]["redis"]
        assert "redis" in redis.get("image", ""), "Redis image not used"

    def test_redis_has_healthcheck(self, compose_config):
        """redis 서비스에 healthcheck가 있어야 함"""
        redis = compose_config["services"]["redis"]
        assert "healthcheck" in redis, "redis healthcheck not found"


class TestBackendService:
    """Backend 서비스 설정 테스트"""

    def test_backend_builds_from_backend(self, compose_config):
        """backend 서비스가 ./backend에서 빌드해야 함"""
        backend = compose_config["services"]["backend"]
        build = backend.get("build", {})
        context = build.get("context", "") if isinstance(build, dict) else ""
        assert "backend" in context, "backend build context not found"

    def test_backend_has_database_config(self, compose_config):
        """backend 서비스에 데이터베이스 설정이 있어야 함 (DATABASE_URL 또는 POSTGRES_SERVER)"""
        backend = compose_config["services"]["backend"]
        env = backend.get("environment", [])
        env_str = str(env)
        has_db_config = "DATABASE_URL" in env_str or "POSTGRES_SERVER" in env_str
        assert has_db_config, "Database config not in backend environment"

    def test_backend_has_redis_url(self, compose_config):
        """backend 서비스에 REDIS_URL이 설정되어야 함"""
        backend = compose_config["services"]["backend"]
        env = backend.get("environment", [])
        env_str = str(env)
        assert "REDIS_URL" in env_str, "REDIS_URL not in backend environment"

    def test_backend_depends_on_db(self, compose_config):
        """backend 서비스가 db에 의존해야 함"""
        backend = compose_config["services"]["backend"]
        depends_on = backend.get("depends_on", {})
        depends_str = str(depends_on)
        assert "db" in depends_str, "backend does not depend on db"

    def test_backend_depends_on_redis(self, compose_config):
        """backend 서비스가 redis에 의존해야 함"""
        backend = compose_config["services"]["backend"]
        depends_on = backend.get("depends_on", {})
        depends_str = str(depends_on)
        assert "redis" in depends_str, "backend does not depend on redis"


class TestWorkerService:
    """Worker 서비스 설정 테스트"""

    def test_worker_builds_from_backend(self, compose_config):
        """worker 서비스가 ./backend에서 빌드해야 함"""
        worker = compose_config["services"]["worker"]
        build = worker.get("build", {})
        context = build.get("context", "") if isinstance(build, dict) else ""
        assert "backend" in context, "worker build context not found"

    def test_worker_has_command(self, compose_config):
        """worker 서비스에 command가 설정되어야 함"""
        worker = compose_config["services"]["worker"]
        assert "command" in worker, "worker command not found"

    def test_worker_runs_pool(self, compose_config):
        """worker 서비스가 workers.pool을 실행해야 함"""
        worker = compose_config["services"]["worker"]
        command = str(worker.get("command", ""))
        assert "pool" in command or "worker" in command, "worker does not run pool"


class TestFrontendService:
    """Frontend 서비스 설정 테스트"""

    def test_frontend_builds_from_frontend(self, compose_config):
        """frontend 서비스가 ./frontend에서 빌드해야 함"""
        frontend = compose_config["services"]["frontend"]
        build = frontend.get("build", {})
        context = build.get("context", "") if isinstance(build, dict) else ""
        assert "frontend" in context, "frontend build context not found"

    def test_frontend_depends_on_backend(self, compose_config):
        """frontend 서비스가 backend에 의존해야 함"""
        frontend = compose_config["services"]["frontend"]
        depends_on = frontend.get("depends_on", [])
        depends_str = str(depends_on)
        assert "backend" in depends_str, "frontend does not depend on backend"


class TestVolumes:
    """볼륨 설정 테스트"""

    def test_has_postgres_volume(self, compose_config):
        """postgres_data 볼륨이 정의되어야 함"""
        volumes = compose_config.get("volumes", {})
        assert "postgres_data" in volumes, "postgres_data volume not found"
