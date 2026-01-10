"""
Phase 5 Day 5: CI Pipeline (GitHub Actions)
TDD RED Phase - 테스트 작성

GitHub Actions CI 워크플로우 파일 검증
"""

from pathlib import Path

import pytest
import yaml

# 프로젝트 경로
BACKEND_ROOT = Path(__file__).parent.parent.parent  # backend/
PROJECT_ROOT = BACKEND_ROOT.parent  # EAZY/
WORKFLOWS_DIR = PROJECT_ROOT / ".github" / "workflows"


@pytest.fixture
def ci_workflow():
    """CI 워크플로우 파일 로드"""
    ci_file = WORKFLOWS_DIR / "ci.yml"
    content = ci_file.read_text()
    return yaml.safe_load(content)


class TestWorkflowExists:
    """CI 워크플로우 파일 존재 테스트"""

    def test_github_workflows_dir_exists(self):
        """.github/workflows 디렉토리가 존재해야 함"""
        assert WORKFLOWS_DIR.exists(), f"workflows dir not found at {WORKFLOWS_DIR}"

    def test_ci_workflow_exists(self):
        """.github/workflows/ci.yml이 존재해야 함"""
        ci_file = WORKFLOWS_DIR / "ci.yml"
        assert ci_file.exists(), f"ci.yml not found at {ci_file}"

    def test_ci_workflow_valid_yaml(self):
        """ci.yml이 유효한 YAML이어야 함"""
        ci_file = WORKFLOWS_DIR / "ci.yml"
        content = ci_file.read_text()
        try:
            config = yaml.safe_load(content)
            assert config is not None, "Empty YAML file"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML: {e}")


class TestWorkflowTriggers:
    """워크플로우 트리거 테스트"""

    def test_has_name(self, ci_workflow):
        """워크플로우에 name이 있어야 함"""
        assert "name" in ci_workflow, "workflow name not found"

    def test_has_on_trigger(self, ci_workflow):
        """on 트리거가 정의되어야 함 (YAML에서 'on'은 True로 파싱됨)"""
        # YAML에서 'on'은 boolean True로 파싱됨
        assert "on" in ci_workflow or True in ci_workflow, "on trigger not found"

    def test_triggers_on_push_main(self, ci_workflow):
        """main 브랜치 push에서 트리거되어야 함"""
        # YAML에서 'on'은 True로 파싱됨
        on_trigger = ci_workflow.get("on", ci_workflow.get(True, {}))
        push = on_trigger.get("push", {})
        branches = push.get("branches", [])
        assert "main" in branches, "push to main not in triggers"

    def test_triggers_on_pull_request(self, ci_workflow):
        """pull_request에서 트리거되어야 함"""
        # YAML에서 'on'은 True로 파싱됨
        on_trigger = ci_workflow.get("on", ci_workflow.get(True, {}))
        assert "pull_request" in on_trigger, "pull_request not in triggers"


class TestLintJob:
    """Lint Job 테스트"""

    def test_has_lint_job(self, ci_workflow):
        """lint job이 존재해야 함"""
        jobs = ci_workflow.get("jobs", {})
        assert "lint" in jobs, "lint job not found"

    def test_lint_runs_on_ubuntu(self, ci_workflow):
        """lint job이 ubuntu에서 실행되어야 함"""
        lint = ci_workflow["jobs"]["lint"]
        runs_on = lint.get("runs-on", "")
        assert "ubuntu" in runs_on, "lint does not run on ubuntu"

    def test_lint_has_steps(self, ci_workflow):
        """lint job에 steps가 있어야 함"""
        lint = ci_workflow["jobs"]["lint"]
        assert "steps" in lint, "lint steps not found"

    def test_lint_uses_ruff(self, ci_workflow):
        """lint job에서 ruff를 실행해야 함"""
        lint = ci_workflow["jobs"]["lint"]
        steps_str = str(lint.get("steps", []))
        assert "ruff" in steps_str.lower(), "ruff not in lint job"


class TestTestJob:
    """Test Job 테스트"""

    def test_has_test_job(self, ci_workflow):
        """test job이 존재해야 함"""
        jobs = ci_workflow.get("jobs", {})
        assert "test" in jobs, "test job not found"

    def test_test_has_postgres_service(self, ci_workflow):
        """test job에 postgres 서비스가 있어야 함"""
        test = ci_workflow["jobs"]["test"]
        services = test.get("services", {})
        assert "postgres" in services, "postgres service not found"

    def test_test_has_redis_service(self, ci_workflow):
        """test job에 redis 서비스가 있어야 함"""
        test = ci_workflow["jobs"]["test"]
        services = test.get("services", {})
        assert "redis" in services, "redis service not found"

    def test_test_runs_pytest(self, ci_workflow):
        """test job에서 pytest를 실행해야 함"""
        test = ci_workflow["jobs"]["test"]
        steps_str = str(test.get("steps", []))
        assert "pytest" in steps_str.lower(), "pytest not in test job"

    def test_test_has_coverage(self, ci_workflow):
        """test job에서 커버리지를 측정해야 함"""
        test = ci_workflow["jobs"]["test"]
        steps_str = str(test.get("steps", []))
        assert "cov" in steps_str.lower(), "coverage not in test job"


class TestBuildJob:
    """Build Job 테스트"""

    def test_has_build_job(self, ci_workflow):
        """build job이 존재해야 함"""
        jobs = ci_workflow.get("jobs", {})
        assert "build" in jobs, "build job not found"

    def test_build_needs_lint_and_test(self, ci_workflow):
        """build job이 lint, test에 의존해야 함"""
        build = ci_workflow["jobs"]["build"]
        needs = build.get("needs", [])
        needs_str = str(needs)
        assert "lint" in needs_str, "build does not need lint"
        assert "test" in needs_str, "build does not need test"

    def test_build_builds_docker_images(self, ci_workflow):
        """build job에서 Docker 이미지를 빌드해야 함"""
        build = ci_workflow["jobs"]["build"]
        steps_str = str(build.get("steps", []))
        assert "docker" in steps_str.lower(), "docker build not in build job"


class TestUvUsage:
    """uv 패키지 매니저 사용 테스트"""

    def test_workflow_uses_uv(self, ci_workflow):
        """워크플로우에서 uv를 사용해야 함"""
        workflow_str = str(ci_workflow)
        assert "uv" in workflow_str.lower(), "uv not used in workflow"

    def test_workflow_installs_uv(self, ci_workflow):
        """워크플로우에서 uv를 설치해야 함"""
        workflow_str = str(ci_workflow)
        assert "setup-uv" in workflow_str or "uv" in workflow_str, \
            "uv installation not found"
