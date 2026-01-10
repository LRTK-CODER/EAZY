"""
Phase 2 Day 4: 고아 작업 복구 테스트

TDD RED 단계 - recovery.py 구현 전에 실패해야 함
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock
from redis.asyncio import Redis


@pytest.fixture
async def redis_client() -> Redis:
    """테스트용 Redis 클라이언트"""
    from app.core.config import settings

    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    yield redis
    await redis.aclose()


@pytest.fixture
async def clean_queues(redis_client: Redis):
    """테스트 전후 큐 및 하트비트 정리"""
    # 테스트 전 정리
    await redis_client.delete("eazy_task_queue")
    await redis_client.delete("eazy_task_queue:processing")
    await redis_client.delete("eazy_task_queue:dlq")

    # 하트비트 키 정리
    keys = await redis_client.keys("eazy:heartbeat:*")
    if keys:
        await redis_client.delete(*keys)

    # DLQ 메타데이터 정리
    keys = await redis_client.keys("eazy:dlq:meta:*")
    if keys:
        await redis_client.delete(*keys)

    yield

    # 테스트 후 정리
    await redis_client.delete("eazy_task_queue")
    await redis_client.delete("eazy_task_queue:processing")
    await redis_client.delete("eazy_task_queue:dlq")

    keys = await redis_client.keys("eazy:heartbeat:*")
    if keys:
        await redis_client.delete(*keys)

    keys = await redis_client.keys("eazy:dlq:meta:*")
    if keys:
        await redis_client.delete(*keys)


class TestOrphanDetection:
    """고아 작업 감지 테스트"""

    @pytest.mark.asyncio
    async def test_orphan_detected_without_heartbeat(
        self, redis_client: Redis, clean_queues
    ):
        """하트비트가 없는 작업은 고아로 감지되어야 함"""
        from app.core.recovery import OrphanRecovery

        recovery = OrphanRecovery(redis_client)

        # Given: processing 큐에 작업이 있지만 하트비트 없음
        task_data = {"id": "orphan-1", "db_task_id": 100}
        task_json = json.dumps(task_data)
        await redis_client.lpush("eazy_task_queue:processing", task_json)

        # When: 고아 작업 확인
        orphans = await recovery.find_orphan_tasks()

        # Then: 고아로 감지
        assert len(orphans) == 1
        assert orphans[0]["id"] == "orphan-1"

    @pytest.mark.asyncio
    async def test_orphan_detected_after_timeout(
        self, redis_client: Redis, clean_queues
    ):
        """하트비트가 타임아웃된 작업은 고아로 감지되어야 함"""
        from app.core.recovery import OrphanRecovery, ORPHAN_TIMEOUT

        recovery = OrphanRecovery(redis_client)

        # Given: processing 큐에 작업과 오래된 하트비트
        task_data = {"id": "orphan-2", "db_task_id": 200}
        task_json = json.dumps(task_data)
        await redis_client.lpush("eazy_task_queue:processing", task_json)

        # 오래된 하트비트 설정 (타임아웃 초과)
        old_time = (
            datetime.now(timezone.utc) - timedelta(seconds=ORPHAN_TIMEOUT + 60)
        ).isoformat()
        await redis_client.set("eazy:heartbeat:orphan-2", old_time)

        # When: 고아 작업 확인
        orphans = await recovery.find_orphan_tasks()

        # Then: 고아로 감지
        assert len(orphans) == 1

    @pytest.mark.asyncio
    async def test_heartbeat_prevents_orphan_detection(
        self, redis_client: Redis, clean_queues
    ):
        """유효한 하트비트가 있는 작업은 고아로 감지되지 않아야 함"""
        from app.core.recovery import OrphanRecovery

        recovery = OrphanRecovery(redis_client)

        # Given: processing 큐에 작업과 최신 하트비트
        task_data = {"id": "active-1", "db_task_id": 300}
        task_json = json.dumps(task_data)
        await redis_client.lpush("eazy_task_queue:processing", task_json)

        # 최신 하트비트 설정
        await recovery.send_heartbeat("active-1")

        # When: 고아 작업 확인
        orphans = await recovery.find_orphan_tasks()

        # Then: 고아 아님
        assert len(orphans) == 0


class TestOrphanRecovery:
    """고아 작업 복구 테스트"""

    @pytest.mark.asyncio
    async def test_orphan_recovered_to_queue(
        self, redis_client: Redis, clean_queues
    ):
        """고아 작업이 원래 큐로 복구되어야 함"""
        from app.core.recovery import OrphanRecovery

        recovery = OrphanRecovery(redis_client)

        # Given: processing 큐에 고아 작업
        task_data = {"id": "recover-1", "db_task_id": 100}
        task_json = json.dumps(task_data)
        await redis_client.lpush("eazy_task_queue:processing", task_json)

        # When: 복구 실행
        recovered_count = await recovery.recover_orphan_tasks()

        # Then: 원래 큐로 이동
        assert recovered_count == 1

        queue_len = await redis_client.llen("eazy_task_queue")
        assert queue_len == 1

        processing_len = await redis_client.llen("eazy_task_queue:processing")
        assert processing_len == 0

    @pytest.mark.asyncio
    async def test_recovery_count_increments(
        self, redis_client: Redis, clean_queues
    ):
        """복구 시 recovery_count가 증가해야 함"""
        from app.core.recovery import OrphanRecovery

        recovery = OrphanRecovery(redis_client)

        # Given: 이미 1번 복구된 작업
        task_data = {"id": "recover-2", "db_task_id": 200, "recovery_count": 1}
        task_json = json.dumps(task_data)
        await redis_client.lpush("eazy_task_queue:processing", task_json)

        # When: 다시 복구
        await recovery.recover_orphan_tasks()

        # Then: recovery_count 증가
        recovered_json = await redis_client.lindex("eazy_task_queue", 0)
        recovered_data = json.loads(recovered_json)
        assert recovered_data["recovery_count"] == 2

    @pytest.mark.asyncio
    async def test_excessive_recovery_sends_to_dlq(
        self, redis_client: Redis, clean_queues
    ):
        """복구 횟수 초과 시 DLQ로 이동"""
        from app.core.recovery import OrphanRecovery, MAX_RECOVERY_COUNT

        recovery = OrphanRecovery(redis_client)

        # Given: 이미 최대 복구 횟수에 도달한 작업
        task_data = {
            "id": "recover-3",
            "db_task_id": 300,
            "recovery_count": MAX_RECOVERY_COUNT,
        }
        task_json = json.dumps(task_data)
        await redis_client.lpush("eazy_task_queue:processing", task_json)

        # When: 복구 시도
        await recovery.recover_orphan_tasks()

        # Then: DLQ로 이동
        dlq_len = await redis_client.llen("eazy_task_queue:dlq")
        assert dlq_len == 1

        # 원래 큐에는 없어야 함
        queue_len = await redis_client.llen("eazy_task_queue")
        assert queue_len == 0


class TestHeartbeat:
    """하트비트 테스트"""

    @pytest.mark.asyncio
    async def test_send_heartbeat_sets_key(
        self, redis_client: Redis, clean_queues
    ):
        """send_heartbeat가 Redis 키를 설정해야 함"""
        from app.core.recovery import OrphanRecovery

        recovery = OrphanRecovery(redis_client)

        # When: 하트비트 전송
        await recovery.send_heartbeat("task-hb-1")

        # Then: 키가 설정됨
        value = await redis_client.get("eazy:heartbeat:task-hb-1")
        assert value is not None

    @pytest.mark.asyncio
    async def test_heartbeat_expires_after_timeout(
        self, redis_client: Redis, clean_queues
    ):
        """하트비트 키가 자동으로 만료되어야 함"""
        from app.core.recovery import OrphanRecovery

        recovery = OrphanRecovery(redis_client)

        # When: 하트비트 전송
        await recovery.send_heartbeat("task-hb-2")

        # Then: TTL이 설정됨
        ttl = await redis_client.ttl("eazy:heartbeat:task-hb-2")
        assert ttl > 0

    @pytest.mark.asyncio
    async def test_clear_heartbeat_removes_key(
        self, redis_client: Redis, clean_queues
    ):
        """clear_heartbeat가 키를 삭제해야 함"""
        from app.core.recovery import OrphanRecovery

        recovery = OrphanRecovery(redis_client)

        # Given: 하트비트 존재
        await recovery.send_heartbeat("task-hb-3")

        # When: 하트비트 삭제
        await recovery.clear_heartbeat("task-hb-3")

        # Then: 키 삭제됨
        value = await redis_client.get("eazy:heartbeat:task-hb-3")
        assert value is None
