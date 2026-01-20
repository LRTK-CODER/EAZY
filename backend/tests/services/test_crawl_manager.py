"""
CrawlManager 테스트 - TDD Red Phase

재귀 크롤링 로직(BFS) 테스트:
- spawn_child_tasks(): 발견된 URL에 대해 자식 Task 생성
- mark_visited(): Redis SET에 방문 URL 저장
- is_visited(): 방문 여부 확인
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.target import TargetScope
from app.models.task import Task, TaskStatus, TaskType
from app.services.crawl_manager import CrawlManager


@pytest.fixture
def mock_session():
    """Mock AsyncSession"""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()

    # Track task IDs for refresh
    task_id_counter = [1]

    async def mock_refresh(task):
        """Set task.id when refresh is called"""
        if task.id is None:
            task.id = task_id_counter[0]
            task_id_counter[0] += 1

    session.refresh = AsyncMock(side_effect=mock_refresh)
    return session


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock()
    redis.sismember = AsyncMock(return_value=False)
    redis.sadd = AsyncMock()
    redis.expire = AsyncMock()
    redis.delete = AsyncMock()

    # Pipeline mock - track sismember calls to return correct number of False values
    pipeline = MagicMock()
    pipeline.sadd = MagicMock(return_value=pipeline)
    pipeline.sismember = MagicMock(return_value=pipeline)
    pipeline.expire = MagicMock(return_value=pipeline)

    # Dynamic return based on number of sismember calls
    sismember_call_count = [0]

    def track_sismember(*args, **kwargs):
        sismember_call_count[0] += 1
        return pipeline

    pipeline.sismember = MagicMock(side_effect=track_sismember)

    async def dynamic_execute():
        # Return False for each sismember call (not visited)
        count = sismember_call_count[0]
        sismember_call_count[0] = 0  # Reset for next batch
        return [False] * count if count > 0 else []

    pipeline.execute = AsyncMock(side_effect=dynamic_execute)
    redis.pipeline = MagicMock(return_value=pipeline)

    return redis


@pytest.fixture
def crawl_manager(mock_session, mock_redis):
    """CrawlManager instance with mocked dependencies"""
    return CrawlManager(mock_session, mock_redis)


class TestCrawlManagerCreatesChildTasks:
    """spawn_child_tasks() 기본 동작 테스트"""

    @pytest.mark.asyncio
    async def test_creates_child_task_for_discovered_url(
        self, crawl_manager, mock_session
    ):
        """Given: 발견된 URL, When: spawn_child_tasks 호출, Then: 자식 Task 생성"""
        # Given
        discovered_urls = ["https://example.com/page1", "https://example.com/page2"]

        # When
        result = await crawl_manager.spawn_child_tasks(
            parent_task_id=1,
            target_id=10,
            project_id=100,
            discovered_urls=discovered_urls,
            current_depth=0,
            max_depth=3,
        )

        # Then
        assert len(result) == 2
        assert mock_session.add.call_count == 2
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_sets_correct_depth_and_parent(self, crawl_manager, mock_session):
        """자식 Task: depth=parent+1, parent_task_id=부모ID"""
        # Given
        discovered_urls = ["https://example.com/page1"]
        parent_task_id = 5
        current_depth = 1

        # When
        result = await crawl_manager.spawn_child_tasks(
            parent_task_id=parent_task_id,
            target_id=10,
            project_id=100,
            discovered_urls=discovered_urls,
            current_depth=current_depth,
            max_depth=3,
        )

        # Then
        assert len(result) == 1
        # Verify the Task was added with correct properties
        add_call_args = mock_session.add.call_args[0][0]
        assert isinstance(add_call_args, Task)
        assert add_call_args.depth == current_depth + 1
        assert add_call_args.parent_task_id == parent_task_id
        assert add_call_args.status == TaskStatus.PENDING
        assert add_call_args.type == TaskType.CRAWL

    @pytest.mark.asyncio
    async def test_enqueues_child_task_to_redis(self, crawl_manager, mock_redis):
        """생성된 Task가 Redis 큐에 enqueue됨"""
        # Given
        discovered_urls = ["https://example.com/page1"]

        # When
        with patch.object(
            crawl_manager.task_manager, "enqueue_crawl_task", new_callable=AsyncMock
        ) as mock_enqueue:
            await crawl_manager.spawn_child_tasks(
                parent_task_id=1,
                target_id=10,
                project_id=100,
                discovered_urls=discovered_urls,
                current_depth=0,
                max_depth=3,
            )

            # Then
            assert mock_enqueue.called
            assert mock_enqueue.call_count == 1


class TestCrawlManagerRespectsMaxDepth:
    """max_depth 제한 테스트"""

    @pytest.mark.asyncio
    async def test_no_child_tasks_at_max_depth(self, crawl_manager, mock_session):
        """Given: depth == max_depth, When: spawn, Then: 빈 리스트 반환"""
        # Given
        discovered_urls = ["https://example.com/page1"]
        current_depth = 3
        max_depth = 3

        # When
        result = await crawl_manager.spawn_child_tasks(
            parent_task_id=1,
            target_id=10,
            project_id=100,
            discovered_urls=discovered_urls,
            current_depth=current_depth,
            max_depth=max_depth,
        )

        # Then
        assert result == []
        assert not mock_session.add.called

    @pytest.mark.asyncio
    async def test_allows_child_tasks_below_max_depth(
        self, crawl_manager, mock_session
    ):
        """Given: depth < max_depth, When: spawn, Then: Task 생성됨"""
        # Given
        discovered_urls = ["https://example.com/page1"]
        current_depth = 2
        max_depth = 3

        # When
        result = await crawl_manager.spawn_child_tasks(
            parent_task_id=1,
            target_id=10,
            project_id=100,
            discovered_urls=discovered_urls,
            current_depth=current_depth,
            max_depth=max_depth,
        )

        # Then
        assert len(result) == 1
        assert mock_session.add.called


class TestCrawlManagerDeduplicatesUrls:
    """중복 URL 제거 테스트"""

    @pytest.mark.asyncio
    async def test_filters_already_visited_urls(self, crawl_manager, mock_redis):
        """이미 방문한 URL은 제외됨"""
        # Given
        discovered_urls = [
            "https://example.com/visited",
            "https://example.com/new",
        ]

        # Setup: first URL is visited, second is not
        pipeline = mock_redis.pipeline()
        pipeline.execute = AsyncMock(return_value=[True, False])  # visited, not visited

        # When
        result = await crawl_manager.spawn_child_tasks(
            parent_task_id=1,
            target_id=10,
            project_id=100,
            discovered_urls=discovered_urls,
            current_depth=0,
            max_depth=3,
        )

        # Then - only unvisited URL should create task
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_marks_urls_as_visited_after_spawn(self, crawl_manager, mock_redis):
        """spawn 후 URL이 visited로 마킹됨"""
        # Given
        discovered_urls = ["https://example.com/page1"]

        # When
        await crawl_manager.spawn_child_tasks(
            parent_task_id=1,
            target_id=10,
            project_id=100,
            discovered_urls=discovered_urls,
            current_depth=0,
            max_depth=3,
        )

        # Then
        pipeline = mock_redis.pipeline()
        assert pipeline.sadd.called or pipeline.execute.called

    @pytest.mark.asyncio
    async def test_deduplicates_within_same_batch(self, crawl_manager, mock_session):
        """동일 배치 내 중복 URL 제거"""
        # Given - same URL with different fragments/formats
        discovered_urls = [
            "https://example.com/page",
            "https://example.com/page#section",  # Same after normalization
            "HTTPS://EXAMPLE.COM/page",  # Same after normalization
        ]

        # When
        result = await crawl_manager.spawn_child_tasks(
            parent_task_id=1,
            target_id=10,
            project_id=100,
            discovered_urls=discovered_urls,
            current_depth=0,
            max_depth=3,
        )

        # Then - should only create 1 task (duplicates removed)
        assert len(result) == 1


class TestCrawlManagerAppliesScopeFilter:
    """Scope 필터링 테스트"""

    @pytest.mark.asyncio
    async def test_filters_out_of_scope_urls(self, crawl_manager, mock_session):
        """out-of-scope URL 제외됨"""
        # Given
        discovered_urls = [
            "https://example.com/page1",
            "https://other.com/page2",  # Out of scope
        ]

        # When
        result = await crawl_manager.spawn_child_tasks(
            parent_task_id=1,
            target_id=10,
            project_id=100,
            discovered_urls=discovered_urls,
            current_depth=0,
            max_depth=3,
            target_url="https://example.com",
            scope=TargetScope.DOMAIN,
        )

        # Then - only in-scope URL should create task
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_domain_scope_blocks_subdomain(self, crawl_manager, mock_session):
        """DOMAIN scope: subdomain 차단"""
        # Given
        discovered_urls = [
            "https://api.example.com/page",  # Subdomain - should be blocked
        ]

        # When
        result = await crawl_manager.spawn_child_tasks(
            parent_task_id=1,
            target_id=10,
            project_id=100,
            discovered_urls=discovered_urls,
            current_depth=0,
            max_depth=3,
            target_url="https://example.com",
            scope=TargetScope.DOMAIN,
        )

        # Then
        assert len(result) == 0
        assert not mock_session.add.called

    @pytest.mark.asyncio
    async def test_subdomain_scope_allows_subdomain(self, crawl_manager, mock_session):
        """SUBDOMAIN scope: subdomain 허용"""
        # Given
        discovered_urls = [
            "https://api.example.com/page",  # Subdomain - should be allowed
        ]

        # When
        result = await crawl_manager.spawn_child_tasks(
            parent_task_id=1,
            target_id=10,
            project_id=100,
            discovered_urls=discovered_urls,
            current_depth=0,
            max_depth=3,
            target_url="https://example.com",
            scope=TargetScope.SUBDOMAIN,
        )

        # Then
        assert len(result) == 1
        assert mock_session.add.called


class TestCrawlManagerRedisOperations:
    """Redis SET 연산 테스트"""

    @pytest.mark.asyncio
    async def test_mark_visited_uses_redis_set(self, crawl_manager, mock_redis):
        """mark_visited가 Redis SADD 사용"""
        # Given
        target_id = 10
        urls = ["https://example.com/page1", "https://example.com/page2"]

        # When
        await crawl_manager.mark_visited(target_id, urls)

        # Then
        pipeline = mock_redis.pipeline()
        assert pipeline.sadd.called
        assert pipeline.execute.called

    @pytest.mark.asyncio
    async def test_is_visited_uses_redis_sismember(self, crawl_manager, mock_redis):
        """is_visited가 Redis SISMEMBER 사용"""
        # Given
        target_id = 10
        url = "https://example.com/page1"
        mock_redis.sismember = AsyncMock(return_value=True)

        # When
        result = await crawl_manager.is_visited(target_id, url)

        # Then
        assert result is True
        mock_redis.sismember.assert_called_once()

    @pytest.mark.asyncio
    async def test_visited_key_has_ttl(self, crawl_manager, mock_redis):
        """visited 키에 TTL 설정됨"""
        # Given
        target_id = 10
        urls = ["https://example.com/page1"]

        # When
        await crawl_manager.mark_visited(target_id, urls)

        # Then
        pipeline = mock_redis.pipeline()
        assert pipeline.expire.called

    @pytest.mark.asyncio
    async def test_visited_key_format(self, crawl_manager, mock_redis):
        """visited 키 형식: eazy:crawl:visited:{target_id}"""
        # Given
        target_id = 10
        url = "https://example.com/page1"

        # When
        await crawl_manager.is_visited(target_id, url)

        # Then
        call_args = mock_redis.sismember.call_args
        key = call_args[0][0]
        assert key == f"eazy:crawl:visited:{target_id}"


class TestCrawlManagerClearVisited:
    """clear_visited() 테스트"""

    @pytest.mark.asyncio
    async def test_clear_visited_deletes_redis_key(self, crawl_manager, mock_redis):
        """clear_visited가 Redis 키 삭제"""
        # Given
        target_id = 10

        # When
        await crawl_manager.clear_visited(target_id)

        # Then
        mock_redis.delete.assert_called_once_with(f"eazy:crawl:visited:{target_id}")


class TestCrawlManagerEmptyInput:
    """빈 입력 처리 테스트"""

    @pytest.mark.asyncio
    async def test_empty_discovered_urls_returns_empty(
        self, crawl_manager, mock_session
    ):
        """빈 URL 목록 → 빈 결과"""
        # When
        result = await crawl_manager.spawn_child_tasks(
            parent_task_id=1,
            target_id=10,
            project_id=100,
            discovered_urls=[],
            current_depth=0,
            max_depth=3,
        )

        # Then
        assert result == []
        assert not mock_session.add.called

    @pytest.mark.asyncio
    async def test_mark_visited_with_empty_urls_does_nothing(
        self, crawl_manager, mock_redis
    ):
        """빈 URL 목록으로 mark_visited 호출 → Redis 호출 없음"""
        # When
        await crawl_manager.mark_visited(target_id=10, urls=[])

        # Then
        assert not mock_redis.pipeline.called
