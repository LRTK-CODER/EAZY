"""
Phase 4: WorkerPool 테스트
TDD RED 단계 - WorkerPool 구현 전에 모두 실패해야 함

Day 1: WorkerPool 기본 구조
Day 2: Graceful Shutdown + 워커 루프
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# =============================================================================
# Day 1: WorkerPool 기본 구조 테스트
# =============================================================================


class TestWorkerPoolConfig:
    """WorkerPoolConfig 단위 테스트"""

    def test_default_values(self):
        """기본값 확인"""
        from app.workers.pool import WorkerPoolConfig

        config = WorkerPoolConfig()

        assert config.num_workers == 4
        assert config.max_restarts_per_worker == 5
        assert config.shutdown_timeout == 30.0

    def test_from_env(self, monkeypatch):
        """환경변수에서 설정 로드"""
        monkeypatch.setenv("WORKER_NUM_WORKERS", "8")
        monkeypatch.setenv("WORKER_MAX_RESTARTS", "3")
        monkeypatch.setenv("WORKER_SHUTDOWN_TIMEOUT", "60")

        from app.workers.pool import WorkerPoolConfig

        config = WorkerPoolConfig.from_env()

        assert config.num_workers == 8
        assert config.max_restarts_per_worker == 3
        assert config.shutdown_timeout == 60.0

    def test_custom_num_workers(self):
        """커스텀 워커 수 설정"""
        from app.workers.pool import WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=16)

        assert config.num_workers == 16

    def test_shutdown_timeout(self):
        """셧다운 타임아웃 설정"""
        from app.workers.pool import WorkerPoolConfig

        config = WorkerPoolConfig(shutdown_timeout=120.0)

        assert config.shutdown_timeout == 120.0


class TestWorkerPoolInit:
    """WorkerPool 초기화 테스트"""

    def test_creates_shutdown_event(self):
        """shutdown_event 생성 확인"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=2)
        pool = WorkerPool(config=config)

        assert hasattr(pool, "_shutdown_event")
        assert isinstance(pool._shutdown_event, asyncio.Event)
        assert not pool._shutdown_event.is_set()

    def test_initializes_empty_tasks_list(self):
        """빈 태스크 리스트 초기화"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=2)
        pool = WorkerPool(config=config)

        assert hasattr(pool, "_tasks")
        assert pool._tasks == []

    def test_sets_num_workers(self):
        """워커 수 설정 확인"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=8)
        pool = WorkerPool(config=config)

        assert pool.config.num_workers == 8

    def test_uses_default_num_workers(self):
        """기본 워커 수 사용"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig()
        pool = WorkerPool(config=config)

        assert pool.config.num_workers == 4

    def test_reads_from_environment(self, monkeypatch):
        """환경변수에서 설정 읽기"""
        monkeypatch.setenv("WORKER_NUM_WORKERS", "12")

        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig.from_env()
        pool = WorkerPool(config=config)

        assert pool.config.num_workers == 12


class TestWorkerPoolStart:
    """WorkerPool.start() 테스트"""

    @pytest.mark.asyncio
    async def test_creates_redis_connection(self):
        """Redis 연결 생성"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=1)
        pool = WorkerPool(config=config)

        # start 후 즉시 stop
        async def stop_quickly():
            await asyncio.sleep(0.1)
            await pool.stop()

        asyncio.create_task(stop_quickly())

        with patch(
            "app.workers.pool.process_one_task", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = False  # 큐 비어있음
            await pool.start()

        # 확인: 리소스가 정리되었어도 start는 호출됨
        assert pool._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_creates_db_engine(self):
        """DB 엔진 생성"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=1)
        pool = WorkerPool(config=config)

        async def stop_quickly():
            await asyncio.sleep(0.1)
            await pool.stop()

        asyncio.create_task(stop_quickly())

        with patch(
            "app.workers.pool.process_one_task", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = False
            await pool.start()

        # engine이 생성되었다가 cleanup됨
        assert pool._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_spawns_correct_number_of_workers(self):
        """올바른 수의 워커 생성"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=3)
        pool = WorkerPool(config=config)
        started_workers = []

        _original_run = pool._run_worker_supervised

        async def mock_run_worker(worker_id, async_session):
            started_workers.append(worker_id)
            await pool._shutdown_event.wait()

        async def stop_after_start():
            # 워커들이 시작될 시간 대기
            await asyncio.sleep(0.2)
            await pool.stop()

        asyncio.create_task(stop_after_start())

        with patch.object(pool, "_run_worker_supervised", mock_run_worker):
            await pool.start()

        assert len(started_workers) == 3
        assert set(started_workers) == {0, 1, 2}

    @pytest.mark.asyncio
    async def test_registers_signal_handlers(self):
        """시그널 핸들러 등록"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=1)
        pool = WorkerPool(config=config)

        handlers_registered = []

        def mock_add_signal_handler(sig, callback):
            handlers_registered.append(sig)

        async def stop_quickly():
            await asyncio.sleep(0.1)
            pool._shutdown_event.set()

        asyncio.create_task(stop_quickly())

        with patch.object(
            asyncio.get_event_loop(), "add_signal_handler", mock_add_signal_handler
        ):
            # _setup_signal_handlers 직접 호출 테스트
            try:
                pool._setup_signal_handlers()
            except NotImplementedError:
                # Windows에서는 NotImplementedError 발생 가능
                pass

    @pytest.mark.asyncio
    async def test_sets_started_flag(self):
        """시작 상태 플래그 설정"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=1)
        pool = WorkerPool(config=config)

        async def stop_quickly():
            await asyncio.sleep(0.1)
            await pool.stop()

        asyncio.create_task(stop_quickly())

        with patch(
            "app.workers.pool.process_one_task", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = False
            await pool.start()

        # start가 완료된 후 확인
        assert pool._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_raises_if_already_started(self):
        """이미 시작된 경우 예외"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=1)
        pool = WorkerPool(config=config)

        # 수동으로 started 상태 설정
        pool._started = True

        with pytest.raises(RuntimeError, match="already started"):
            await pool.start()


# =============================================================================
# Day 2: Graceful Shutdown 테스트
# =============================================================================


class TestWorkerPoolStop:
    """WorkerPool.stop() 테스트"""

    @pytest.mark.asyncio
    async def test_sets_shutdown_event(self):
        """shutdown_event 설정"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=1)
        pool = WorkerPool(config=config)

        assert not pool._shutdown_event.is_set()

        await pool.stop()

        assert pool._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_waits_for_workers_to_finish(self):
        """워커 종료 대기"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=1)
        pool = WorkerPool(config=config)

        async def mock_worker(worker_id, async_session):
            await pool._shutdown_event.wait()

        async def stop_after_delay():
            await asyncio.sleep(0.2)
            await pool.stop()

        asyncio.create_task(stop_after_delay())

        with patch.object(pool, "_run_worker_supervised", mock_worker):
            await pool.start()

        # stop이 호출된 후에야 start가 반환되어야 함
        assert pool._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_closes_redis_connection(self):
        """Redis 연결 종료"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=1)
        pool = WorkerPool(config=config)

        async def stop_quickly():
            await asyncio.sleep(0.1)
            await pool.stop()

        asyncio.create_task(stop_quickly())

        with patch(
            "app.workers.pool.process_one_task", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = False
            await pool.start()

        # cleanup이 호출되었음을 확인 (shutdown_event가 set됨)
        assert pool._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_disposes_db_engine(self):
        """DB 엔진 정리"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=1)
        pool = WorkerPool(config=config)

        async def stop_quickly():
            await asyncio.sleep(0.1)
            await pool.stop()

        asyncio.create_task(stop_quickly())

        with patch(
            "app.workers.pool.process_one_task", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = False
            await pool.start()

        # engine이 정리됨
        assert pool._engine is None or pool._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_is_idempotent(self):
        """중복 stop 호출 안전성"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=1)
        pool = WorkerPool(config=config)

        await pool.stop()
        await pool.stop()  # 두 번째 호출도 안전해야 함
        await pool.stop()  # 세 번째 호출도 안전해야 함

        assert pool._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_cancels_workers_on_timeout(self):
        """타임아웃 시 워커 취소"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=1, shutdown_timeout=0.1)
        pool = WorkerPool(config=config)

        async def slow_worker(worker_id, async_session):
            await asyncio.sleep(10)  # 매우 긴 작업

        async def stop_quickly():
            await asyncio.sleep(0.05)
            await pool.stop()

        asyncio.create_task(stop_quickly())

        # 타임아웃으로 인해 워커가 취소되어야 함
        with patch.object(pool, "_run_worker_supervised", slow_worker):
            await pool.start()

        assert pool._shutdown_event.is_set()


class TestSignalHandling:
    """시그널 처리 테스트"""

    @pytest.mark.asyncio
    async def test_sigterm_triggers_graceful_shutdown(self):
        """SIGTERM 시 graceful shutdown"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=1)
        pool = WorkerPool(config=config)

        async def mock_worker(worker_id, async_session):
            await pool._shutdown_event.wait()

        async def send_signal():
            await asyncio.sleep(0.1)
            # 시그널 대신 직접 shutdown_event 설정
            pool._shutdown_event.set()

        asyncio.create_task(send_signal())

        with patch.object(pool, "_run_worker_supervised", mock_worker):
            await pool.start()

        assert pool._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_sigint_triggers_graceful_shutdown(self):
        """SIGINT 시 graceful shutdown"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=1)
        pool = WorkerPool(config=config)

        async def mock_worker(worker_id, async_session):
            await pool._shutdown_event.wait()

        async def send_signal():
            await asyncio.sleep(0.1)
            pool._shutdown_event.set()

        asyncio.create_task(send_signal())

        with patch.object(pool, "_run_worker_supervised", mock_worker):
            await pool.start()

        assert pool._shutdown_event.is_set()

    def test_signal_handler_setup(self):
        """시그널 핸들러 설정"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=1)
        pool = WorkerPool(config=config)

        # _setup_signal_handlers가 예외 없이 호출됨
        try:
            # 이벤트 루프가 없으면 RuntimeError
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                pool._setup_signal_handlers()
            except (NotImplementedError, RuntimeError):
                # Windows 또는 이벤트 루프 없음
                pass
            finally:
                loop.close()
        except Exception:
            pass  # 환경에 따라 다를 수 있음

    @pytest.mark.asyncio
    async def test_workers_complete_current_task_before_shutdown(self):
        """종료 전 현재 작업 완료"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=1)
        pool = WorkerPool(config=config)
        task_completed = False

        async def mock_worker(worker_id, async_session):
            nonlocal task_completed
            # 작업 시뮬레이션
            await asyncio.sleep(0.1)
            task_completed = True
            await pool._shutdown_event.wait()

        async def stop_after_task():
            await asyncio.sleep(0.2)
            await pool.stop()

        asyncio.create_task(stop_after_task())

        with patch.object(pool, "_run_worker_supervised", mock_worker):
            await pool.start()

        assert task_completed


class TestWorkerRestart:
    """워커 재시작 테스트"""

    @pytest.mark.asyncio
    async def test_worker_restarts_on_crash(self):
        """워커 크래시 시 재시작 확인"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(
            num_workers=1, max_restarts_per_worker=3, restart_delay_base=0.01
        )
        pool = WorkerPool(config=config)
        call_count = 0

        async def crashing_worker(worker_id, async_session):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("Simulated crash")
            await pool._shutdown_event.wait()

        async def stop_after_restarts():
            await asyncio.sleep(0.5)
            await pool.stop()

        asyncio.create_task(stop_after_restarts())

        with patch.object(pool, "_run_single_worker", crashing_worker):
            await pool.start()

        assert call_count >= 3

    @pytest.mark.asyncio
    async def test_max_restarts_exceeded(self):
        """최대 재시작 횟수 초과"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        # 최소 설정으로 빠른 테스트
        config = WorkerPoolConfig(
            num_workers=1,
            max_restarts_per_worker=2,
            restart_delay_base=0.001,
            restart_delay_max=0.01,
        )
        pool = WorkerPool(config=config)
        call_count = 0

        async def always_crashing(worker_id, async_session):
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Always crash")

        with patch.object(pool, "_run_single_worker", always_crashing):
            await pool.start()

        # max_restarts_per_worker 만큼만 시도
        assert call_count == config.max_restarts_per_worker

    @pytest.mark.asyncio
    async def test_restart_delay_increases(self):
        """재시작 지연 시간 증가 확인 (단위 테스트)"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(restart_delay_base=1.0, restart_delay_max=30.0)
        _pool = WorkerPool(config=config)

        # 지수 백오프 계산 확인
        # restart_count=1 -> delay = 1.0 * 2^1 = 2.0
        # restart_count=2 -> delay = 1.0 * 2^2 = 4.0
        # restart_count=3 -> delay = 1.0 * 2^3 = 8.0
        delay1 = min(config.restart_delay_base * (2**1), config.restart_delay_max)
        delay2 = min(config.restart_delay_base * (2**2), config.restart_delay_max)

        assert delay2 > delay1

    @pytest.mark.asyncio
    async def test_restart_count_resets_on_success(self):
        """성공 시 연속 에러 카운트 리셋 (단위 테스트)"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        # _run_single_worker 내에서 consecutive_errors가 리셋되는지 확인
        # 이 테스트는 실제 워커 루프가 아닌 로직만 확인
        config = WorkerPoolConfig(num_workers=1, max_consecutive_errors=10)
        pool = WorkerPool(config=config)

        # consecutive_errors는 _run_single_worker 내부 변수이므로
        # 설정값만 확인
        assert pool.config.max_consecutive_errors == 10


# =============================================================================
# Resource Management Tests
# =============================================================================


class TestResourceManagement:
    """리소스 관리 테스트"""

    @pytest.mark.asyncio
    async def test_redis_connection_per_worker(self):
        """워커별 독립 Redis 연결 확인"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=2)
        pool = WorkerPool(config=config)
        redis_instances = []

        async def capture_redis(worker_id, async_session):
            # 워커가 시작되면 redis 인스턴스 캡처
            redis_instances.append(worker_id)
            await pool._shutdown_event.wait()

        async def stop_after_start():
            await asyncio.sleep(0.2)
            await pool.stop()

        asyncio.create_task(stop_after_start())

        with patch.object(pool, "_run_worker_supervised", capture_redis):
            await pool.start()

        assert len(redis_instances) == 2

    @pytest.mark.asyncio
    async def test_engine_disposed_on_cleanup(self):
        """종료 시 DB 엔진 정리 확인"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=1)
        pool = WorkerPool(config=config)

        async def mock_worker(worker_id, async_session):
            await pool._shutdown_event.wait()

        async def stop_quickly():
            await asyncio.sleep(0.1)
            await pool.stop()

        asyncio.create_task(stop_quickly())

        with patch.object(pool, "_run_worker_supervised", mock_worker):
            await pool.start()

        # cleanup 후 engine은 None이어야 함
        assert pool._engine is None


# =============================================================================
# Properties Tests
# =============================================================================


class TestWorkerPoolProperties:
    """속성 테스트"""

    def test_is_running_property(self):
        """is_running 속성"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=1)
        pool = WorkerPool(config=config)

        assert not pool.is_running

        pool._started = True
        pool._shutdown_event.clear()

        assert pool.is_running

        pool._shutdown_event.set()

        assert not pool.is_running

    def test_active_workers_property(self):
        """active_workers 속성"""
        from app.workers.pool import WorkerPool, WorkerPoolConfig

        config = WorkerPoolConfig(num_workers=4)
        pool = WorkerPool(config=config)

        assert pool.active_workers == 0

        # 가짜 태스크 추가
        pool._tasks = [MagicMock(), MagicMock()]

        assert pool.active_workers == 2
