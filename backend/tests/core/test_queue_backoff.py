"""
Phase 2: Exponential Backoff 테스트

TDD Red-Green-Refactor 사이클:
1. RED: 이 테스트들이 먼저 실패해야 함
2. GREEN: queue.py 수정 후 통과해야 함
3. REFACTOR: 리팩토링 후에도 통과 유지

테스트 대상:
- queue.py의 nack_task에서 delayed queue(ZSET) 사용
- calculate_backoff를 사용한 지수 증가 delay
- process_delayed_tasks로 main queue로 이동
"""

import json
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.priority import TaskPriority
from app.core.queue import TaskManager
from app.core.retry import BASE_DELAY, JITTER_RANGE, MAX_DELAY, calculate_backoff


class TestDelayedQueueAttribute:
    """TaskManager의 delayed_key 속성 테스트"""

    @pytest.mark.asyncio
    async def test_delayed_key_initialized(self):
        """TaskManager에 delayed_key 속성이 존재해야 함"""
        mock_redis = MagicMock()
        task_manager = TaskManager(redis=mock_redis)

        # delayed_key 속성 확인
        assert hasattr(
            task_manager, "delayed_key"
        ), "TaskManager should have 'delayed_key' attribute"
        assert task_manager.delayed_key == "eazy_task_queue:delayed"


class TestNackTaskBackoff:
    """NACK 재시도 시 backoff delay 적용 테스트"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        redis = MagicMock()
        redis.lrem = AsyncMock(return_value=1)
        redis.lpush = AsyncMock(return_value=1)
        redis.rpush = AsyncMock(return_value=1)
        redis.zadd = AsyncMock(return_value=1)
        redis.zrangebyscore = AsyncMock(return_value=[])
        redis.zrem = AsyncMock(return_value=1)
        return redis

    @pytest.fixture
    def task_manager(self, mock_redis):
        """테스트용 TaskManager"""
        return TaskManager(redis=mock_redis)

    @pytest.mark.asyncio
    async def test_nack_task_applies_backoff_delay(self, task_manager, mock_redis):
        """NACK 시 delayed queue(ZSET)에 추가되어야 함"""
        task_data = {
            "id": "test-backoff-1",
            "db_task_id": 1,
            "retry_count": 0,
            "priority": TaskPriority.NORMAL.value,  # IntEnum value (1)
        }
        task_json = json.dumps(task_data)

        await task_manager.nack_task(task_json, retry=True)

        # delayed queue에 zadd로 추가되었는지 확인
        # 현재 구현은 lpush를 사용하므로 이 테스트는 실패해야 함
        mock_redis.zadd.assert_called_once()

        # zadd 호출 인자 확인: zadd(key, {task_json: score})
        call_args = mock_redis.zadd.call_args
        assert call_args is not None, "zadd should be called"

        # 첫 번째 위치 인자가 delayed_key
        delayed_key = call_args[0][0]
        assert delayed_key == task_manager.delayed_key

    @pytest.mark.asyncio
    async def test_nack_task_score_is_future_timestamp(self, task_manager, mock_redis):
        """NACK 시 score가 미래 timestamp여야 함 (현재 시간 + delay)"""
        task_data = {
            "id": "test-backoff-2",
            "db_task_id": 2,
            "retry_count": 1,
            "priority": TaskPriority.NORMAL.value,  # IntEnum value (1)
        }
        task_json = json.dumps(task_data)

        before_time = time.time()
        await task_manager.nack_task(task_json, retry=True)
        _ = time.time()  # after_time - used for timing reference

        # zadd 호출 확인
        mock_redis.zadd.assert_called_once()

        # score (execute_at) 추출
        call_args = mock_redis.zadd.call_args
        score_mapping = call_args[0][1]  # {task_json: score}
        score = list(score_mapping.values())[0]

        # score는 현재 시간보다 미래여야 함
        assert score > before_time, "Score should be in the future"
        # retry_count=1이면 약 2초 delay (jitter 포함)
        expected_min_delay = BASE_DELAY * 2 * (1 - JITTER_RANGE)
        assert score >= before_time + expected_min_delay


class TestBackoffCalculation:
    """Exponential Backoff 계산 테스트"""

    def test_backoff_increases_exponentially(self):
        """retry_count 증가에 따라 delay가 지수적으로 증가"""
        # Jitter를 제거하고 평균값으로 테스트
        # 여러 번 계산해서 평균을 확인
        samples = 100

        avg_delay_0 = sum(calculate_backoff(0) for _ in range(samples)) / samples
        avg_delay_1 = sum(calculate_backoff(1) for _ in range(samples)) / samples
        avg_delay_2 = sum(calculate_backoff(2) for _ in range(samples)) / samples

        # 평균적으로 지수 증가해야 함
        # retry_count=0: ~1초, retry_count=1: ~2초, retry_count=2: ~4초
        assert avg_delay_1 > avg_delay_0 * 1.5, "Delay should roughly double"
        assert avg_delay_2 > avg_delay_1 * 1.5, "Delay should roughly double"

    def test_backoff_has_jitter(self):
        """동일 retry_count에서 jitter로 delay가 다름"""
        delays = [calculate_backoff(1) for _ in range(20)]

        # 모든 delay가 동일하지 않아야 함 (jitter 적용)
        unique_delays = set(delays)
        assert len(unique_delays) > 1, "Delays should vary due to jitter"

    def test_backoff_respects_max_delay(self):
        """MAX_DELAY를 초과하지 않아야 함"""
        # 매우 높은 retry_count에서도 MAX_DELAY 제한
        for _ in range(50):
            delay = calculate_backoff(100)
            # jitter 최대값 포함
            max_possible = MAX_DELAY * (1 + JITTER_RANGE)
            assert delay <= max_possible, f"Delay {delay} exceeds max {max_possible}"

    def test_backoff_base_delay(self):
        """retry_count=0일 때 BASE_DELAY 근처값이어야 함"""
        delays = [calculate_backoff(0) for _ in range(50)]
        avg_delay = sum(delays) / len(delays)

        # 평균이 BASE_DELAY 근처여야 함
        assert abs(avg_delay - BASE_DELAY) < BASE_DELAY * JITTER_RANGE * 2


class TestProcessDelayedTasks:
    """Delayed Queue에서 Main Queue로 이동하는 테스트"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        redis = MagicMock()
        redis.lrem = AsyncMock(return_value=1)
        redis.lpush = AsyncMock(return_value=1)
        redis.rpush = AsyncMock(return_value=1)
        redis.zadd = AsyncMock(return_value=1)
        redis.zrangebyscore = AsyncMock(return_value=[])
        redis.zrem = AsyncMock(return_value=1)
        return redis

    @pytest.fixture
    def task_manager(self, mock_redis):
        """테스트용 TaskManager"""
        return TaskManager(redis=mock_redis)

    @pytest.mark.asyncio
    async def test_process_delayed_tasks_method_exists(self, task_manager):
        """TaskManager에 process_delayed_tasks 메서드가 존재해야 함"""
        assert hasattr(
            task_manager, "process_delayed_tasks"
        ), "TaskManager should have 'process_delayed_tasks' method"
        assert callable(
            task_manager.process_delayed_tasks
        ), "process_delayed_tasks should be callable"

    @pytest.mark.asyncio
    async def test_process_delayed_tasks_moves_to_main_queue(
        self, task_manager, mock_redis
    ):
        """실행 시간이 된 작업이 main queue로 이동해야 함"""
        # 실행 시간이 지난 작업 (과거 timestamp)
        task_data = {
            "id": "test-delayed-1",
            "db_task_id": 1,
            "priority": TaskPriority.NORMAL.value,  # IntEnum value (1)
        }
        task_json = json.dumps(task_data)

        # zrangebyscore가 task 반환하도록 설정
        mock_redis.zrangebyscore = AsyncMock(return_value=[task_json])

        count = await task_manager.process_delayed_tasks()

        # 작업이 처리되었는지 확인
        assert count == 1, "Should process 1 delayed task"

        # main queue로 rpush 되었는지 확인
        mock_redis.rpush.assert_called_once()

        # delayed queue에서 제거되었는지 확인
        mock_redis.zrem.assert_called_once_with(task_manager.delayed_key, task_json)

    @pytest.mark.asyncio
    async def test_process_delayed_tasks_respects_priority(
        self, task_manager, mock_redis
    ):
        """작업이 원래 priority queue로 이동해야 함"""
        task_data = {
            "id": "test-delayed-2",
            "db_task_id": 2,
            "priority": TaskPriority.HIGH.value,  # IntEnum value (2)
        }
        task_json = json.dumps(task_data)

        mock_redis.zrangebyscore = AsyncMock(return_value=[task_json])

        await task_manager.process_delayed_tasks()

        # high priority queue로 이동했는지 확인
        call_args = mock_redis.rpush.call_args
        queue_key = call_args[0][0]
        assert (
            "high" in queue_key
        ), f"Should move to high priority queue, got {queue_key}"

    @pytest.mark.asyncio
    async def test_process_delayed_tasks_returns_zero_when_empty(
        self, task_manager, mock_redis
    ):
        """처리할 작업이 없으면 0을 반환해야 함"""
        mock_redis.zrangebyscore = AsyncMock(return_value=[])

        count = await task_manager.process_delayed_tasks()

        assert count == 0, "Should return 0 when no delayed tasks"

    @pytest.mark.asyncio
    async def test_process_delayed_tasks_uses_current_time(
        self, task_manager, mock_redis
    ):
        """zrangebyscore 호출 시 현재 시간을 score 상한으로 사용해야 함"""
        mock_redis.zrangebyscore = AsyncMock(return_value=[])

        before_time = time.time()
        await task_manager.process_delayed_tasks()
        after_time = time.time()

        # zrangebyscore 호출 확인
        mock_redis.zrangebyscore.assert_called_once()

        call_args = mock_redis.zrangebyscore.call_args
        # zrangebyscore(key, min, max, ...)
        max_score = (
            call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get("max")
        )

        # max_score는 현재 시간 범위 내여야 함
        assert (
            before_time <= max_score <= after_time
        ), f"Max score {max_score} should be current time"


class TestNackTaskNoDelayForDLQ:
    """DLQ 이동 시 delay 미적용 테스트"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        redis = MagicMock()
        redis.lrem = AsyncMock(return_value=1)
        redis.lpush = AsyncMock(return_value=1)
        redis.rpush = AsyncMock(return_value=1)
        redis.zadd = AsyncMock(return_value=1)
        return redis

    @pytest.fixture
    def task_manager(self, mock_redis):
        """테스트용 TaskManager"""
        return TaskManager(redis=mock_redis)

    @pytest.mark.asyncio
    async def test_nack_task_dlq_does_not_use_delayed_queue(
        self, task_manager, mock_redis
    ):
        """retry=False (DLQ 이동)일 때 delayed queue를 사용하지 않아야 함"""
        task_data = {
            "id": "test-dlq-1",
            "db_task_id": 1,
            "priority": TaskPriority.NORMAL.value,  # IntEnum value (1)
        }
        task_json = json.dumps(task_data)

        await task_manager.nack_task(task_json, retry=False)

        # zadd가 호출되지 않아야 함 (DLQ는 즉시 이동)
        mock_redis.zadd.assert_not_called()

        # lpush로 DLQ에 추가되어야 함
        mock_redis.lpush.assert_called_once()
        call_args = mock_redis.lpush.call_args
        assert task_manager.dlq_key == call_args[0][0]
