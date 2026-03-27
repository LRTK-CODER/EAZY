"""벤치마크 환경 검증 테스트.

SPEC-000 Feature 3: 벤치마크 환경 디렉토리 구조 + Docker Compose
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

# -- L2 벤치마크 디렉토리 목록 (parametrize용) --
L2_BENCHMARKS = [
    "benchmarks/l2/owasp-benchmark",
    "benchmarks/l2/wivet",
    "benchmarks/l2/conduit",
]


class TestBenchmarkDirectoriesExist:
    """SPEC 검증: benchmarks/ 디렉토리 구조 존재."""

    EXPECTED_DIRS = [
        "benchmarks/l1",
        "benchmarks/l2/owasp-benchmark",
        "benchmarks/l2/wivet",
        "benchmarks/l2/conduit",
    ]

    @pytest.mark.parametrize("rel_path", EXPECTED_DIRS)
    def test_benchmark_directories_exist(
        self, project_root: Path, rel_path: str
    ) -> None:
        """벤치마크 하위 디렉토리가 존재한다."""
        target = project_root / rel_path
        assert target.is_dir(), f"디렉토리가 존재하지 않음: {target}"


class TestDockerComposeConfigValid:
    """SPEC 검증: 각 L2 docker-compose.yml 유효성."""

    @pytest.mark.docker
    @pytest.mark.parametrize("rel_path", L2_BENCHMARKS)
    def test_docker_compose_config_valid(
        self, project_root: Path, rel_path: str
    ) -> None:
        """docker compose config가 exit 0으로 통과한다."""
        compose_dir = project_root / rel_path
        compose_file = compose_dir / "docker-compose.yml"
        assert compose_file.is_file(), f"docker-compose.yml이 존재하지 않음: {compose_file}"

        result = subprocess.run(
            ["docker", "compose", "config", "--quiet"],
            cwd=str(compose_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"docker compose config 실패 ({rel_path}):\n{result.stderr}"
        )


class TestDockerComposeUpHealthcheck:
    """SPEC 검증: docker compose up 헬스체크 통과."""

    @pytest.mark.slow
    @pytest.mark.docker
    @pytest.mark.parametrize("rel_path", L2_BENCHMARKS)
    def test_docker_compose_up_healthcheck(
        self, project_root: Path, rel_path: str
    ) -> None:
        """docker compose up -d 후 모든 컨테이너가 healthy 상태이다."""
        compose_dir = project_root / rel_path

        try:
            # 환경 기동
            up_result = subprocess.run(
                ["docker", "compose", "up", "-d", "--wait"],
                cwd=str(compose_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
            assert up_result.returncode == 0, (
                f"docker compose up 실패 ({rel_path}):\n{up_result.stderr}"
            )

            # 컨테이너 상태 확인
            ps_result = subprocess.run(
                ["docker", "compose", "ps", "--format", "json"],
                cwd=str(compose_dir),
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert ps_result.returncode == 0, "docker compose ps 실패"
            assert ps_result.stdout.strip(), "실행 중인 컨테이너가 없음"
        finally:
            # 환경 정리
            subprocess.run(
                ["docker", "compose", "down", "-v", "--remove-orphans"],
                cwd=str(compose_dir),
                capture_output=True,
                timeout=60,
            )


class TestL1ConftestFixtureStructure:
    """SPEC 검증: benchmarks/l1/conftest.py 존재 + 픽스처 구조."""

    def test_l1_conftest_fixture_structure(self, project_root: Path) -> None:
        """L1 conftest.py가 존재하고 pytest 픽스처 함수가 정의되어 있다."""
        conftest_path = project_root / "benchmarks" / "l1" / "conftest.py"
        assert conftest_path.is_file(), f"conftest.py가 존재하지 않음: {conftest_path}"

        source = conftest_path.read_text(encoding="utf-8")

        # pytest import 확인
        assert "import pytest" in source or "from pytest" in source, (
            "conftest.py에 pytest import가 없음"
        )

        # @pytest.fixture 데코레이터 존재 확인
        assert "@pytest.fixture" in source, (
            "conftest.py에 @pytest.fixture가 정의되지 않음"
        )
