# Phase 4: Pipeline 구조 구현 (2)

**Status**: ✅ Completed
**Started**: 2025-01-28
**Last Updated**: 2025-01-29
**Completed**: 2025-01-29

---

**⚠️ CRITICAL INSTRUCTIONS**: 각 Phase 완료 후:
1. ✅ 완료된 task 체크박스 체크
2. 🧪 모든 Quality Gate 검증 명령어 실행
3. ⚠️ 모든 Quality Gate 항목 통과 확인
4. 📅 "Last Updated" 날짜 업데이트
5. 📝 Notes 섹션에 배운 점 기록
6. ➡️ 그 후에만 다음 Phase로 진행

⛔ **Quality Gate를 건너뛰거나 실패한 상태로 진행하지 마세요**

---

## 📋 개요

### Phase 목표
나머지 Pipeline Stage들(DiscoveryStage, AssetStage, RecurseStage)과 CrawlOrchestrator를 구현하여 파이프라인을 완성합니다.

### 성공 기준
- [x] DiscoveryStage가 자산 발견 모듈들 실행
- [x] AssetStage가 배치 저장 및 중복 제거 수행
- [x] RecurseStage가 자식 Task 생성
- [x] CrawlOrchestrator가 전체 파이프라인 조율
- [x] 전체 파이프라인 E2E 테스트 통과
- [x] 각 Stage의 단위 테스트 커버리지 ≥90%

### 사용자 영향
- 안정적인 Active Scan 실행
- 모듈화된 자산 발견
- 명확한 에러 복구

---

## 🏗️ 아키텍처 결정

| 결정 | 이유 | 트레이드오프 |
|------|------|------------|
| DiscoveryStage는 에러 시 계속 | Discovery 실패해도 이미 발견된 자산 저장 가능 | 일부 자산 누락 가능 |
| 배치 저장 + IntegrityError 복구 | 성능 최적화 + 동시성 문제 해결 | 복잡도 증가 |
| Orchestrator 패턴 | 파이프라인 흐름 제어 중앙화 | 단일 책임 주의 필요 |

---

## 📦 의존성

### 시작 전 필요 사항
- [ ] Phase 3 완료 (모든 Quality Gate 통과)
- [ ] PipelineStage, PipelineContext, GuardStage, CrawlStage 구현 완료

### 외부 의존성
- 기존 Discovery 모듈 (services/discovery/)

---

## 🧪 테스트 전략

### 테스트 접근법
**TDD 원칙**: 테스트를 먼저 작성하고, 테스트를 통과시키는 구현을 작성

### 이 Phase의 테스트 피라미드
| 테스트 유형 | 커버리지 목표 | 목적 |
|------------|--------------|------|
| **단위 테스트** | ≥90% | 각 Stage 로직 |
| **통합 테스트** | Critical paths | Stage 간 연동, DB 연동 |
| **E2E 테스트** | 1+ critical path | 전체 파이프라인 |

### 테스트 파일 구조
```
backend/tests/
├── unit/
│   └── application/
│       ├── stages/
│       │   ├── test_discovery_stage.py
│       │   ├── test_asset_stage.py
│       │   └── test_recurse_stage.py
│       └── orchestrators/
│           └── test_crawl_orchestrator.py
├── integration/
│   └── application/
│       └── test_pipeline_integration.py
└── e2e/
    └── test_crawl_e2e.py
```

### Mock 및 Helper 유틸리티 정의 (Phase 4 추가)

Phase 3의 mock 클래스에 추가하여 Phase 4 테스트에 필요한 mock 객체들입니다.

**File**: `tests/conftest.py` (Phase 3의 mock 클래스에 추가)

```python
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import IntegrityError

from app.services.discovery.models import DiscoveredAsset, DiscoveryContext

# ============================================================
# Mock Services for Phase 4
# ============================================================

class MockDiscoveryService:
    """
    테스트용 DiscoveryService mock.

    기존 DiscoveryService.run() 메서드를 모방합니다.
    """
    def __init__(
        self,
        assets: List[DiscoveredAsset] = None,
        raises: Exception = None,
    ):
        self.assets = assets or []
        self.raises = raises
        self.run_called = False
        self.last_context: Optional[DiscoveryContext] = None

    async def run(self, context: DiscoveryContext) -> List[DiscoveredAsset]:
        """기존 DiscoveryService.run() 시그니처 그대로"""
        self.run_called = True
        self.last_context = context
        if self.raises:
            raise self.raises
        return self.assets


class MockAssetRepository:
    """
    테스트용 IAssetRepository mock.

    배치 저장과 IntegrityError 시나리오를 지원합니다.
    """
    def __init__(
        self,
        batch_raises: Exception = None,
        individual_succeeds: bool = True,
    ):
        self.batch_raises = batch_raises
        self.individual_succeeds = individual_succeeds
        self.saved_assets: List[Any] = []
        self.save_batch = AsyncMock(side_effect=self._save_batch)
        self.save_individual = AsyncMock(side_effect=self._save_individual)
        self.find_by_hash = AsyncMock(return_value=None)

    async def _save_batch(self, assets: List[Any], task_id: int) -> int:
        if self.batch_raises:
            raise self.batch_raises
        self.saved_assets.extend(assets)
        return len(assets)

    async def _save_individual(self, asset: Any, task_id: int) -> bool:
        if self.individual_succeeds:
            self.saved_assets.append(asset)
            return True
        return False


class MockDataTransformer:
    """테스트용 DataTransformer mock"""
    def __init__(self):
        self.to_discovery_context = MagicMock(return_value=DiscoveryContext(
            target_url="https://example.com",
            crawl_data={},
        ))
        self.map_source = MagicMock(return_value="HTML")
        self.map_type = MagicMock(return_value="URL")


class MockTaskQueue:
    """
    테스트용 ITaskQueue mock.

    Task enqueue/dequeue를 추적합니다.
    """
    def __init__(self):
        self.enqueue = AsyncMock(return_value="task-id-123")
        self.dequeue = AsyncMock(return_value=None)
        self.ack = AsyncMock(return_value=True)
        self.nack = AsyncMock(return_value=True)
        self.enqueued_tasks: List[dict] = []

    async def _enqueue(self, task_data: dict, priority) -> str:
        self.enqueued_tasks.append(task_data)
        return f"task-{len(self.enqueued_tasks)}"


class MockVisitedTracker:
    """테스트용 URL 방문 추적기 mock"""
    def __init__(self, visited: List[str] = None):
        self.visited = set(visited or [])

    async def is_visited(self, url: str) -> bool:
        return url in self.visited

    async def mark_visited(self, url: str) -> None:
        self.visited.add(url)


class MockCancellation:
    """테스트용 ICancellation mock"""
    def __init__(self, is_cancelled: bool = False):
        self._is_cancelled = is_cancelled

    async def is_cancelled(self, task_id: int) -> bool:
        return self._is_cancelled


class MockStage:
    """
    테스트용 PipelineStage mock.

    CrawlOrchestrator 테스트에서 사용합니다.
    """
    def __init__(
        self,
        name: str,
        result: "StageResult" = None,
        can_continue: bool = False,
        raises: Exception = None,
    ):
        self._name = name
        self._result = result
        self._can_continue = can_continue
        self._raises = raises
        self.process_called = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def can_continue_on_error(self) -> bool:
        return self._can_continue

    async def process(self, context) -> "StageResult":
        self.process_called = True
        if self._raises:
            raise self._raises
        return self._result or StageResult.ok()


# ============================================================
# Test Environment Helpers
# ============================================================

async def run_worker_until_task_complete(
    task_id: int,
    timeout_seconds: float = 30.0,
    poll_interval: float = 0.5,
) -> None:
    """
    Task가 완료될 때까지 Worker를 실행하는 헬퍼.

    통합/E2E 테스트에서 사용합니다.
    """
    import asyncio
    from app.models.task import TaskStatus

    start_time = asyncio.get_event_loop().time()
    while True:
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed > timeout_seconds:
            raise TimeoutError(f"Task {task_id} did not complete within {timeout_seconds}s")

        # Task 상태 확인 (실제 구현에서 session 주입 필요)
        # task = await session.get(Task, task_id)
        # if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
        #     return

        await asyncio.sleep(poll_interval)
```

### 테스트 환경 구성

**docker-compose.test.yml** (테스트 전용 환경):
```yaml
# docker-compose.test.yml
version: "3.8"

services:
  postgres-test:
    image: postgres:15
    environment:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: eazy_test
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test -d eazy_test"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis-test:
    image: redis:7
    ports:
      - "6380:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  mock-http-server:
    image: mockserver/mockserver:latest
    ports:
      - "1080:1080"
    environment:
      MOCKSERVER_INITIALIZATION_JSON_PATH: /config/expectations.json
    volumes:
      - ./tests/fixtures/mock-server:/config
```

**mock_http_server fixture** (`tests/e2e/conftest.py`):
```python
import pytest
from dataclasses import dataclass

@dataclass
class MockHttpServer:
    """Mock HTTP 서버 정보"""
    host: str
    port: int

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


@pytest.fixture(scope="session")
def mock_http_server() -> MockHttpServer:
    """
    E2E 테스트용 Mock HTTP 서버.

    docker-compose.test.yml의 mock-http-server 서비스 사용.
    """
    return MockHttpServer(host="localhost", port=1080)


@pytest.fixture(scope="function")
async def setup_mock_expectations(mock_http_server):
    """
    테스트별 Mock 응답 설정.

    각 테스트 전에 MockServer expectations를 초기화합니다.
    """
    import httpx

    # Reset all expectations
    async with httpx.AsyncClient() as client:
        await client.put(f"{mock_http_server.url}/mockserver/reset")

    yield

    # Cleanup after test
    async with httpx.AsyncClient() as client:
        await client.put(f"{mock_http_server.url}/mockserver/reset")
```

---

## 🚀 구현 작업

### Day 1-2: DiscoveryStage 및 AssetStage 구현

**🔴 RED: 실패하는 테스트 먼저 작성**

- [ ] **Test 1.1**: DiscoveryStage 단위 테스트 작성
  - File(s): `tests/unit/application/stages/test_discovery_stage.py`
  - Expected: 테스트 FAIL
  - 테스트 케이스:
    ```python
    class TestDiscoveryStage:
        async def test_runs_discovery_service_and_stores_results(self):
            """Discovery 서비스 실행 후 결과 저장"""
            mock_discovery = MockDiscoveryService(
                assets=[
                    DiscoveredAsset(url="/api/users", type="api_endpoint"),
                    DiscoveredAsset(url="/form/login", type="form"),
                ]
            )
            mock_transformer = MockDataTransformer()
            stage = DiscoveryStage(
                discovery_service=mock_discovery,
                data_transformer=mock_transformer,
            )

            context = MockPipelineContext(crawl_data=MockCrawlData())
            result = await stage.process(context)

            assert result.success is True
            assert len(context.discovered_assets) == 2

        async def test_continues_on_discovery_error(self):
            """Discovery 에러 시에도 계속 진행"""
            mock_discovery = MockDiscoveryService(raises=Exception("Module error"))
            stage = DiscoveryStage(discovery_service=mock_discovery)

            context = MockPipelineContext(crawl_data=MockCrawlData())
            result = await stage.process(context)

            # can_continue_on_error=True이므로 success=True
            assert result.success is True
            assert len(context.errors) == 1

        async def test_transforms_crawl_data_to_discovery_context(self):
            """CrawlData → DiscoveryContext 변환"""
            mock_discovery = MockDiscoveryService(assets=[])
            mock_transformer = MockDataTransformer()
            stage = DiscoveryStage(
                discovery_service=mock_discovery,
                data_transformer=mock_transformer,
            )

            context = MockPipelineContext(crawl_data=MockCrawlData())
            await stage.process(context)

            mock_transformer.to_discovery_context.assert_called_once()

        async def test_stage_name_is_discovery(self):
            """Stage name은 'discovery'"""
            stage = DiscoveryStage(MockDiscoveryService())
            assert stage.name == "discovery"

        async def test_can_continue_on_error_is_true(self):
            """DiscoveryStage 에러 시 계속 가능"""
            stage = DiscoveryStage(MockDiscoveryService())
            assert stage.can_continue_on_error is True
    ```

- [ ] **Test 1.2**: AssetStage 단위 테스트 작성
  - File(s): `tests/unit/application/stages/test_asset_stage.py`
  - Expected: 테스트 FAIL
  - 테스트 케이스:
    ```python
    class TestAssetStage:
        async def test_saves_discovered_assets(self):
            """발견된 자산 저장"""
            mock_repo = MockAssetRepository()
            stage = AssetStage(asset_repository=mock_repo)

            context = MockPipelineContext(
                discovered_assets=[
                    DiscoveredAsset(url="/api/users"),
                    DiscoveredAsset(url="/api/posts"),
                ]
            )
            result = await stage.process(context)

            assert result.success is True
            assert context.saved_count == 2
            mock_repo.save_batch.assert_called_once()

        async def test_saves_links_from_crawl_data(self):
            """크롤 데이터의 링크 저장"""
            mock_repo = MockAssetRepository()
            stage = AssetStage(asset_repository=mock_repo)

            context = MockPipelineContext(
                crawl_data=MockCrawlData(links=["/page1", "/page2"]),
                discovered_assets=[],
            )
            result = await stage.process(context)

            assert result.success is True
            assert context.saved_count >= 2

        async def test_handles_integrity_error_with_individual_save(self):
            """IntegrityError 시 개별 저장으로 fallback"""
            mock_repo = MockAssetRepository(
                batch_raises=IntegrityError(),
                individual_succeeds=True,
            )
            stage = AssetStage(asset_repository=mock_repo)

            context = MockPipelineContext(
                discovered_assets=[DiscoveredAsset(url="/api/users")],
            )
            result = await stage.process(context)

            assert result.success is True
            mock_repo.save_individual.assert_called()

        async def test_deduplicates_assets_by_content_hash(self):
            """content_hash로 중복 제거"""
            mock_repo = MockAssetRepository()
            stage = AssetStage(asset_repository=mock_repo)

            context = MockPipelineContext(
                discovered_assets=[
                    DiscoveredAsset(url="/api/users", method="GET"),
                    DiscoveredAsset(url="/api/users", method="GET"),  # 중복
                ],
            )
            result = await stage.process(context)

            # 중복 제거되어 1개만 저장
            assert context.saved_count == 1

        async def test_stage_name_is_asset(self):
            """Stage name은 'asset'"""
            stage = AssetStage(MockAssetRepository())
            assert stage.name == "asset"
    ```

**🟢 GREEN: 테스트를 통과시키는 구현**

- [ ] **Task 1.3**: DiscoveryStage 클래스 구현
  - File(s): `backend/app/application/stages/discovery_stage.py`
  - 목표: Test 1.1 통과
  - **중요**: 기존 `DiscoveryService.run()` 메서드를 사용 (어댑터 또는 직접 호출)
  - 구현 내용:
    ```python
    from app.services.discovery import DiscoveryService, DiscoveryContext, get_default_registry

    class DiscoveryStage(PipelineStage):
        """자산 발견 Stage"""

        def __init__(
            self,
            discovery_service: DiscoveryService | None = None,
            data_transformer: DataTransformer | None = None,
        ):
            # 기존 DiscoveryService 직접 사용 (run() 메서드 호출)
            self._discovery = discovery_service or DiscoveryService(
                registry=get_default_registry()
            )
            self._transformer = data_transformer or DataTransformer()

        @property
        def name(self) -> str:
            return "discovery"

        @property
        def can_continue_on_error(self) -> bool:
            return True  # Discovery 실패해도 계속

        async def process(self, context: PipelineContext) -> StageResult:
            try:
                discovery_context = self._transformer.to_discovery_context(
                    crawl_data=context.crawl_data,
                    target_url=context.crawl_url,
                )
                # 기존 DiscoveryService.run() 메서드 호출
                # (IDiscoveryService.discover()가 아님!)
                assets = await self._discovery.run(discovery_context)
                context.set_discovered_assets(assets)
                return StageResult.ok()
            except Exception as e:
                context.add_error(self.name, e)
                return StageResult.ok()  # can_continue_on_error=True
    ```

  **IDiscoveryService 어댑터 (optional, Port 인터페이스 사용 시)**:
  ```python
  # infrastructure/adapters/discovery_adapter.py
  from app.services.discovery import DiscoveryService

  class DiscoveryServiceAdapter:
      """기존 DiscoveryService를 IDiscoveryService Protocol로 래핑"""

      def __init__(self, service: DiscoveryService):
          self._service = service

      async def discover(self, context: DiscoveryContext) -> List[DiscoveredAsset]:
          # run() → discover() 매핑
          return await self._service.run(context)
  ```

- [ ] **Task 1.4**: AssetStage 클래스 구현
  - File(s): `backend/app/application/stages/asset_stage.py`
  - 목표: Test 1.2 통과

**🔵 REFACTOR: 코드 정리**

- [ ] **Task 1.5**: 코드 품질 개선
  - 체크리스트:
    - [ ] 로깅 추가
    - [ ] 에러 분류 개선

---

### Day 3-4: RecurseStage 및 CrawlOrchestrator 구현

**🔴 RED: 실패하는 테스트 먼저 작성**

- [ ] **Test 2.1**: RecurseStage 단위 테스트 작성
  - File(s): `tests/unit/application/stages/test_recurse_stage.py`
  - Expected: 테스트 FAIL
  - 테스트 케이스:
    ```python
    class TestRecurseStage:
        async def test_spawns_child_tasks_for_links(self):
            """링크에 대한 자식 Task 생성"""
            mock_task_queue = MockTaskQueue()
            stage = RecurseStage(task_queue=mock_task_queue)

            context = MockPipelineContext(
                task=MockTask(depth=0, max_depth=3),
                crawl_data=MockCrawlData(links=["/page1", "/page2"]),
            )
            result = await stage.process(context)

            assert result.success is True
            assert context.child_tasks_spawned == 2
            assert mock_task_queue.enqueue.call_count == 2

        async def test_respects_max_depth(self):
            """max_depth 도달 시 자식 Task 미생성"""
            mock_task_queue = MockTaskQueue()
            stage = RecurseStage(task_queue=mock_task_queue)

            context = MockPipelineContext(
                task=MockTask(depth=3, max_depth=3),
                crawl_data=MockCrawlData(links=["/page1"]),
            )
            result = await stage.process(context)

            assert result.success is True
            assert context.child_tasks_spawned == 0
            mock_task_queue.enqueue.assert_not_called()

        async def test_filters_visited_urls(self):
            """이미 방문한 URL 필터링"""
            mock_task_queue = MockTaskQueue()
            mock_visited_tracker = MockVisitedTracker(
                visited=["/page1"]
            )
            stage = RecurseStage(
                task_queue=mock_task_queue,
                visited_tracker=mock_visited_tracker,
            )

            context = MockPipelineContext(
                task=MockTask(depth=0, max_depth=3),
                crawl_data=MockCrawlData(links=["/page1", "/page2"]),
            )
            result = await stage.process(context)

            assert context.child_tasks_spawned == 1  # /page1 제외

        async def test_normalizes_urls(self):
            """URL 정규화"""
            mock_task_queue = MockTaskQueue()
            stage = RecurseStage(task_queue=mock_task_queue)

            context = MockPipelineContext(
                task=MockTask(depth=0, max_depth=3),
                crawl_url="https://example.com/base/",
                crawl_data=MockCrawlData(links=["../page1", "./page2"]),
            )
            await stage.process(context)

            # 상대 URL이 절대 URL로 변환되었는지 확인
            enqueued_urls = [call.args[0]["crawl_url"] for call in mock_task_queue.enqueue.call_args_list]
            assert all(url.startswith("https://") for url in enqueued_urls)

        async def test_stage_name_is_recurse(self):
            """Stage name은 'recurse'"""
            stage = RecurseStage(MockTaskQueue())
            assert stage.name == "recurse"
    ```

- [ ] **Test 2.2**: CrawlOrchestrator 단위 테스트 작성
  - File(s): `tests/unit/application/orchestrators/test_crawl_orchestrator.py`
  - Expected: 테스트 FAIL
  - 테스트 케이스:
    ```python
    class TestCrawlOrchestrator:
        async def test_executes_all_stages_in_order(self):
            """모든 Stage 순서대로 실행"""
            stages = [
                MockStage(name="guard"),
                MockStage(name="crawl"),
                MockStage(name="discovery"),
                MockStage(name="asset"),
                MockStage(name="recurse"),
            ]
            orchestrator = CrawlOrchestrator(stages=stages)

            result = await orchestrator.execute(
                task=MockTask(id=1),
                target_id=10,
            )

            assert result.success is True
            assert all(stage.process_called for stage in stages)

        async def test_stops_on_should_stop_result(self):
            """should_stop=True 시 파이프라인 중지"""
            stages = [
                MockStage(name="guard", result=StageResult.stop("blocked")),
                MockStage(name="crawl"),  # 실행되면 안됨
            ]
            orchestrator = CrawlOrchestrator(stages=stages)

            result = await orchestrator.execute(MockTask(id=1), target_id=10)

            assert stages[0].process_called is True
            assert stages[1].process_called is False

        async def test_stops_on_failure(self):
            """Stage 실패 시 파이프라인 중지"""
            stages = [
                MockStage(name="guard"),
                MockStage(name="crawl", result=StageResult.fail("error")),
                MockStage(name="discovery"),  # 실행되면 안됨
            ]
            orchestrator = CrawlOrchestrator(stages=stages)

            result = await orchestrator.execute(MockTask(id=1), target_id=10)

            assert result.success is False
            assert stages[2].process_called is False

        async def test_continues_on_error_if_stage_allows(self):
            """can_continue_on_error=True Stage는 에러 시에도 계속"""
            stages = [
                MockStage(name="guard"),
                MockStage(name="discovery", can_continue=True, raises=Exception("error")),
                MockStage(name="asset"),  # 실행되어야 함
            ]
            orchestrator = CrawlOrchestrator(stages=stages)

            result = await orchestrator.execute(MockTask(id=1), target_id=10)

            assert stages[2].process_called is True

        async def test_checks_cancellation_between_stages(self):
            """Stage 간 취소 확인"""
            mock_cancellation = MockCancellation(is_cancelled=True)
            stages = [
                MockStage(name="guard"),
                MockStage(name="crawl"),  # 실행되면 안됨
            ]
            orchestrator = CrawlOrchestrator(
                stages=stages,
                cancellation=mock_cancellation,
            )

            result = await orchestrator.execute(MockTask(id=1), target_id=10)

            assert result.cancelled is True
            assert stages[1].process_called is False

        async def test_returns_orchestrator_result(self):
            """OrchestratorResult 반환"""
            stages = [MockStage(name="guard")]
            orchestrator = CrawlOrchestrator(stages=stages)

            result = await orchestrator.execute(MockTask(id=1), target_id=10)

            assert isinstance(result, OrchestratorResult)
    ```

**🟢 GREEN: 테스트를 통과시키는 구현**

- [ ] **Task 2.3**: RecurseStage 클래스 구현
  - File(s): `backend/app/application/stages/recurse_stage.py`
  - 목표: Test 2.1 통과

- [ ] **Task 2.4**: CrawlOrchestrator 클래스 구현
  - File(s): `backend/app/application/orchestrators/crawl_orchestrator.py`
  - 목표: Test 2.2 통과
  - 구현 내용:
    ```python
    @dataclass
    class OrchestratorResult:
        success: bool
        found_links: int
        saved_assets: int
        discovered_assets: int
        child_tasks_spawned: int
        errors: list[str]
        cancelled: bool = False
        skipped: bool = False

    class CrawlOrchestrator:
        """파이프라인 조율자"""

        def __init__(
            self,
            stages: list[PipelineStage],
            cancellation: ICancellation | None = None,
        ):
            self._stages = stages
            self._cancellation = cancellation

        async def execute(
            self,
            task: Task,
            target_id: int,
        ) -> OrchestratorResult:
            context = PipelineContext(task=task, target_id=target_id)
            await context.load_target()

            for stage in self._stages:
                # 취소 확인
                if self._cancellation and await self._cancellation.is_cancelled(task.id):
                    context.mark_cancelled()
                    break

                # Stage 실행
                try:
                    result = await stage.process(context)
                    if result.should_stop:
                        break
                except Exception as e:
                    context.add_error(stage.name, e)
                    if not stage.can_continue_on_error:
                        break

            return context.to_result()
    ```

**🔵 REFACTOR: 코드 정리**

- [ ] **Task 2.5**: 코드 품질 개선
  - 체크리스트:
    - [ ] 로깅 추가
    - [ ] 메트릭 수집 추가

---

### Day 5: E2E 테스트 및 통합

**🔴 RED: 실패하는 테스트 먼저 작성**

- [ ] **Test 3.1**: 파이프라인 통합 테스트 작성
  - File(s): `tests/integration/application/test_pipeline_integration.py`
  - 테스트 케이스:
    ```python
    class TestPipelineIntegration:
        async def test_full_pipeline_execution(self, db_session, redis_client):
            """전체 파이프라인 실행 통합 테스트"""
            # Setup
            target = await create_target(db_session, url="https://example.com")
            task = await create_task(db_session, target_id=target.id)

            # Execute
            orchestrator = create_crawl_orchestrator(
                session=db_session,
                redis=redis_client,
            )
            result = await orchestrator.execute(task=task, target_id=target.id)

            # Verify
            assert result.success is True
            assert result.saved_assets > 0
    ```

- [ ] **Test 3.2**: E2E 테스트 작성
  - File(s): `tests/e2e/test_crawl_e2e.py`
  - 테스트 케이스:
    ```python
    class TestCrawlE2E:
        async def test_crawl_flow_from_api_to_completion(
            self, test_client, db_session, redis_client, mock_http_server
        ):
            """API → Worker → 완료까지 전체 흐름"""
            # 1. Target 생성
            response = await test_client.post(
                "/api/v1/projects/1/targets",
                json={"url": mock_http_server.url},
            )
            target_id = response.json()["id"]

            # 2. Scan 시작
            response = await test_client.post(
                f"/api/v1/projects/1/targets/{target_id}/scan"
            )
            task_id = response.json()["task_id"]

            # 3. Worker 실행
            await run_worker_until_task_complete(task_id)

            # 4. 결과 확인
            task = await db_session.get(Task, task_id)
            assert task.status == TaskStatus.COMPLETED

            assets = await get_assets_for_target(db_session, target_id)
            assert len(assets) > 0
    ```

**🟢 GREEN: 테스트를 통과시키는 통합**

- [ ] **Task 3.3**: 통합 테스트 통과를 위한 수정
- [ ] **Task 3.4**: E2E 테스트 통과를 위한 수정

---

## ✋ Quality Gate

**⚠️ STOP: 모든 체크가 통과할 때까지 Phase 5로 진행하지 마세요**

### TDD 준수 (CRITICAL)
- [ ] **Red Phase**: 테스트를 먼저 작성하고 실패 확인
- [ ] **Green Phase**: 테스트를 통과시키는 최소 코드 작성
- [ ] **Refactor Phase**: 테스트 통과 상태에서 코드 개선
- [ ] **Coverage Check**: 테스트 커버리지 ≥90%

### 빌드 & 테스트
- [ ] **Build**: 프로젝트 빌드/컴파일 에러 없음
- [ ] **All Tests Pass**: 100% 테스트 통과 (스킵 없음)
- [ ] **E2E Pass**: E2E 테스트 통과
- [ ] **No Flaky Tests**: 3회 이상 실행해도 일관된 결과

### 코드 품질
- [ ] **Linting**: ruff check 에러/경고 없음
- [ ] **Formatting**: ruff format으로 포맷팅됨
- [ ] **Type Safety**: mypy 통과

### 검증 명령어

```bash
# 단위 테스트
uv run pytest tests/unit/application/ -v

# 통합 테스트 (Redis + DB 필요)
docker-compose up -d redis postgres
uv run pytest tests/integration/application/ -v

# E2E 테스트
uv run pytest tests/e2e/ -v

# 전체 커버리지
uv run pytest --cov=app --cov-report=html

# 코드 품질
uv run ruff check app/
uv run mypy app/
```

### 수동 테스트 체크리스트
- [ ] API로 Scan 시작 후 Task 상태 확인
- [ ] Asset 저장 결과 DB에서 확인
- [ ] 자식 Task 생성 확인

---

## 📊 진행 상황

### 완료 상태
- **Day 1-2 (Discovery + Asset)**: ✅ 100%
- **Day 3-4 (Recurse + Orchestrator)**: ✅ 100%
- **Day 5 (E2E)**: ✅ 100%

### 시간 추적
| 작업 | 예상 | 실제 | 차이 |
|------|------|------|------|
| Discovery + Asset | 16시간 | 완료 | - |
| Recurse + Orchestrator | 16시간 | 완료 | - |
| E2E | 8시간 | 완료 | - |
| **합계** | 40시간 | 완료 | - |

---

## 🔄 Phase 4 롤백 절차

Phase 4에서 문제 발생 시 롤백 절차:

### 롤백이 필요한 경우
- CrawlOrchestrator 통합 실패
- E2E 테스트 지속적 실패
- IntegrityError 복구 로직 문제
- 심각한 성능 저하

### 롤백 단계

1. **코드 롤백**:
   ```bash
   git revert --no-commit HEAD~N..HEAD  # N = Phase 4 커밋 수
   git commit -m "revert: rollback Phase 4 Orchestrator and remaining stages"
   ```

2. **삭제 대상** (Phase 4에서 생성된 파일):
   ```
   backend/app/application/stages/discovery_stage.py
   backend/app/application/stages/asset_stage.py
   backend/app/application/stages/recurse_stage.py
   backend/app/application/orchestrators/
   backend/tests/unit/application/stages/test_discovery_stage.py
   backend/tests/unit/application/stages/test_asset_stage.py
   backend/tests/unit/application/stages/test_recurse_stage.py
   backend/tests/unit/application/orchestrators/
   backend/tests/e2e/test_crawl_e2e.py
   ```

3. **유지 대상**:
   - Phase 1 인프라
   - Phase 2 Domain 계층
   - Phase 3 기본 Stage (GuardStage, CrawlStage, PipelineContext)
   - 기존 `workers/crawl_worker.py` (아직 변경 안 함)

4. **검증**:
   ```bash
   uv run pytest tests/unit/ -v
   uv run pytest tests/integration/ -v
   ```

### 영향 범위
- Phase 4만 롤백: Phase 1-3은 유지됨
- Phase 5 진행 불가 (Orchestrator 필요)
- 기존 CrawlWorker는 계속 동작

### 부분 롤백 옵션

특정 Stage만 문제인 경우:
```bash
# 예: AssetStage만 롤백
git revert <asset_stage_commit_hash>
```

---

**Phase Status**: ✅ Completed
**Completed**: 2025-01-29
**Next Phase**: Phase 5 (Worker 단순화 & 마무리)
