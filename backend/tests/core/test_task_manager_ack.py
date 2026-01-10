"""
Phase 2 Day 2: BRPOPLPUSH + ACK 패턴 테스트

TDD RED 단계 - queue.py의 ACK/NACK 메서드 구현 전에 실패해야 함
"""

import json
import pytest
from redis.asyncio import Redis

from app.core.queue import TaskManager


@pytest.fixture
async def redis_client() -> Redis:
    """테스트용 Redis 클라이언트"""
    from app.core.config import settings

    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    yield redis
    await redis.aclose()


@pytest.fixture
async def task_manager(redis_client: Redis) -> TaskManager:
    """테스트용 TaskManager"""
    return TaskManager(redis_client)


@pytest.fixture
async def clean_queues(redis_client: Redis):
    """테스트 전후 큐 정리"""
    # 테스트 전 정리
    await redis_client.delete("eazy_task_queue")
    await redis_client.delete("eazy_task_queue:processing")
    await redis_client.delete("eazy_task_queue:dlq")

    yield

    # 테스트 후 정리
    await redis_client.delete("eazy_task_queue")
    await redis_client.delete("eazy_task_queue:processing")
    await redis_client.delete("eazy_task_queue:dlq")


class TestBrpoplpush:
    """BRPOPLPUSH 동작 테스트"""

    @pytest.mark.asyncio
    async def test_dequeue_moves_to_processing(
        self, task_manager: TaskManager, redis_client: Redis, clean_queues
    ):
        """dequeue 시 작업이 processing 큐로 이동해야 함"""
        # Given: 큐에 작업 추가
        task_id = await task_manager.enqueue_crawl_task(
            project_id=1, target_id=1, db_task_id=100
        )

        # When: 작업 dequeue
        task_data = await task_manager.dequeue_task(timeout=1)

        # Then: 작업이 processing 큐에 있어야 함
        assert task_data is not None
        processing_len = await redis_client.llen("eazy_task_queue:processing")
        assert processing_len == 1

        # 원래 큐는 비어있어야 함
        queue_len = await redis_client.llen("eazy_task_queue")
        assert queue_len == 0

    @pytest.mark.asyncio
    async def test_dequeue_returns_task_json(
        self, task_manager: TaskManager, redis_client: Redis, clean_queues
    ):
        """dequeue는 task_data와 task_json 튜플을 반환해야 함"""
        # Given: 큐에 작업 추가
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=2, db_task_id=200
        )

        # When: 작업 dequeue
        result = await task_manager.dequeue_task(timeout=1)

        # Then: 튜플 (task_data, task_json) 반환
        assert result is not None
        task_data, task_json = result
        assert isinstance(task_data, dict)
        assert isinstance(task_json, str)
        assert task_data["db_task_id"] == 200

    @pytest.mark.asyncio
    async def test_dequeue_empty_queue_returns_none(
        self, task_manager: TaskManager, clean_queues
    ):
        """빈 큐에서 dequeue 시 None 반환"""
        result = await task_manager.dequeue_task(timeout=1)
        assert result is None


class TestAckTask:
    """ack_task() 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_ack_removes_from_processing(
        self, task_manager: TaskManager, redis_client: Redis, clean_queues
    ):
        """ack 시 processing 큐에서 작업 제거"""
        # Given: 작업을 dequeue하여 processing 큐로 이동
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=1, db_task_id=100
        )
        task_data, task_json = await task_manager.dequeue_task(timeout=1)

        # When: ACK 호출
        await task_manager.ack_task(task_json)

        # Then: processing 큐가 비어있어야 함
        processing_len = await redis_client.llen("eazy_task_queue:processing")
        assert processing_len == 0

    @pytest.mark.asyncio
    async def test_ack_does_not_affect_other_tasks(
        self, task_manager: TaskManager, redis_client: Redis, clean_queues
    ):
        """ack는 해당 작업만 제거해야 함"""
        # Given: 여러 작업을 processing 큐로 이동
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=1, db_task_id=100
        )
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=2, db_task_id=200
        )

        task_data_1, task_json_1 = await task_manager.dequeue_task(timeout=1)
        task_data_2, task_json_2 = await task_manager.dequeue_task(timeout=1)

        # When: 첫 번째 작업만 ACK
        await task_manager.ack_task(task_json_1)

        # Then: 두 번째 작업은 여전히 processing 큐에 있어야 함
        processing_len = await redis_client.llen("eazy_task_queue:processing")
        assert processing_len == 1


class TestNackTask:
    """nack_task() 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_nack_retry_moves_back_to_queue(
        self, task_manager: TaskManager, redis_client: Redis, clean_queues
    ):
        """nack(retry=True) 시 원래 큐로 다시 이동"""
        # Given: 작업을 dequeue하여 processing 큐로 이동
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=1, db_task_id=100
        )
        task_data, task_json = await task_manager.dequeue_task(timeout=1)

        # When: NACK (retry=True)
        await task_manager.nack_task(task_json, retry=True)

        # Then: 원래 큐에 다시 추가되어야 함
        queue_len = await redis_client.llen("eazy_task_queue")
        assert queue_len == 1

        # processing 큐는 비어있어야 함
        processing_len = await redis_client.llen("eazy_task_queue:processing")
        assert processing_len == 0

    @pytest.mark.asyncio
    async def test_nack_dlq_moves_to_dead_letter(
        self, task_manager: TaskManager, redis_client: Redis, clean_queues
    ):
        """nack(retry=False) 시 DLQ로 이동"""
        # Given: 작업을 dequeue하여 processing 큐로 이동
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=1, db_task_id=100
        )
        task_data, task_json = await task_manager.dequeue_task(timeout=1)

        # When: NACK (retry=False)
        await task_manager.nack_task(task_json, retry=False)

        # Then: DLQ에 추가되어야 함
        dlq_len = await redis_client.llen("eazy_task_queue:dlq")
        assert dlq_len == 1

        # processing 큐는 비어있어야 함
        processing_len = await redis_client.llen("eazy_task_queue:processing")
        assert processing_len == 0

        # 원래 큐에는 없어야 함
        queue_len = await redis_client.llen("eazy_task_queue")
        assert queue_len == 0

    @pytest.mark.asyncio
    async def test_nack_preserves_task_data(
        self, task_manager: TaskManager, redis_client: Redis, clean_queues
    ):
        """nack 시 원본 작업 데이터가 보존되어야 함"""
        # Given: 작업을 dequeue
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=1, db_task_id=100
        )
        task_data, task_json = await task_manager.dequeue_task(timeout=1)
        original_db_task_id = task_data["db_task_id"]

        # When: NACK (retry=True)
        await task_manager.nack_task(task_json, retry=True)

        # Then: 다시 dequeue하면 같은 데이터
        new_task_data, _ = await task_manager.dequeue_task(timeout=1)
        assert new_task_data["db_task_id"] == original_db_task_id


class TestProcessingQueuePersistence:
    """Processing 큐 영속성 테스트"""

    @pytest.mark.asyncio
    async def test_processing_queue_persists_on_crash(
        self, task_manager: TaskManager, redis_client: Redis, clean_queues
    ):
        """Worker 크래시 시뮬레이션 - processing 큐의 작업이 유지되어야 함"""
        # Given: 작업을 dequeue (processing 큐로 이동)
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=1, db_task_id=100
        )
        task_data, task_json = await task_manager.dequeue_task(timeout=1)

        # When: Worker "크래시" (ACK 없이 종료 시뮬레이션)
        # 새로운 TaskManager 인스턴스 생성 (Worker 재시작 시뮬레이션)
        new_task_manager = TaskManager(redis_client)

        # Then: processing 큐에 작업이 여전히 있어야 함
        processing_len = await redis_client.llen("eazy_task_queue:processing")
        assert processing_len == 1

        # 작업 데이터도 유지되어야 함
        task_json_in_queue = await redis_client.lindex(
            "eazy_task_queue:processing", 0
        )
        recovered_data = json.loads(task_json_in_queue)
        assert recovered_data["db_task_id"] == 100

    @pytest.mark.asyncio
    async def test_get_processing_tasks(
        self, task_manager: TaskManager, redis_client: Redis, clean_queues
    ):
        """processing 큐의 작업 목록을 조회할 수 있어야 함"""
        # Given: 여러 작업을 processing 큐로 이동
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=1, db_task_id=100
        )
        await task_manager.enqueue_crawl_task(
            project_id=1, target_id=2, db_task_id=200
        )
        await task_manager.dequeue_task(timeout=1)
        await task_manager.dequeue_task(timeout=1)

        # When: processing 작업 목록 조회
        processing_tasks = await task_manager.get_processing_tasks()

        # Then: 2개의 작업이 있어야 함
        assert len(processing_tasks) == 2
        db_task_ids = [t["db_task_id"] for t in processing_tasks]
        assert 100 in db_task_ids
        assert 200 in db_task_ids
