"""
WorkerPool for EAZY worker infrastructure.

Phase 4: Scalability Improvement

Provides multi-worker management with:
- asyncio.TaskGroup for structured concurrency
- Graceful shutdown (SIGTERM/SIGINT)
- Worker restart with exponential backoff
- Per-worker Redis connections
"""
from __future__ import annotations

import asyncio
import logging
import os
import signal
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.errors import classify_error, ErrorCategory
from app.workers.runner import create_worker_context, process_one_task

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class WorkerPoolConfig:
    """
    워커 풀 설정.

    Attributes:
        num_workers: 동시에 실행할 워커 수
        max_restarts_per_worker: 워커당 최대 재시작 횟수
        restart_delay_base: 재시작 지연 기본값 (초)
        restart_delay_max: 재시작 지연 최대값 (초)
        max_consecutive_errors: 최대 연속 에러 허용 횟수
        shutdown_timeout: Graceful shutdown 타임아웃 (초)
    """

    num_workers: int = 4
    max_restarts_per_worker: int = 5
    restart_delay_base: float = 2.0
    restart_delay_max: float = 30.0
    max_consecutive_errors: int = 10
    shutdown_timeout: float = 30.0

    @classmethod
    def from_env(cls) -> WorkerPoolConfig:
        """환경변수에서 설정 로드."""
        return cls(
            num_workers=int(os.getenv("WORKER_NUM_WORKERS", "4")),
            max_restarts_per_worker=int(os.getenv("WORKER_MAX_RESTARTS", "5")),
            shutdown_timeout=float(os.getenv("WORKER_SHUTDOWN_TIMEOUT", "30.0")),
        )


@dataclass
class WorkerPool:
    """
    AsyncIO 기반 워커 풀.

    특징:
    - asyncio.TaskGroup으로 구조적 동시성 구현
    - Graceful Shutdown (SIGTERM/SIGINT)
    - 워커별 독립 Redis 연결
    - 자동 재시작 및 지수 백오프
    - 예외 분류 기반 처리

    사용 예시:
        pool = WorkerPool(config=WorkerPoolConfig(num_workers=4))
        await pool.start()
    """

    config: WorkerPoolConfig = field(default_factory=WorkerPoolConfig)
    _shutdown_event: asyncio.Event = field(default_factory=asyncio.Event, init=False)
    _engine: Optional[AsyncEngine] = field(default=None, init=False)
    _tasks: list = field(default_factory=list, init=False)
    _started: bool = field(default=False, init=False)

    @property
    def is_running(self) -> bool:
        """워커 풀이 실행 중인지 확인."""
        return self._started and not self._shutdown_event.is_set()

    @property
    def active_workers(self) -> int:
        """현재 활성 워커 수."""
        return len(self._tasks)

    async def start(self) -> None:
        """워커 풀 시작."""
        if self._started:
            raise RuntimeError("WorkerPool already started")

        logger.info(f"Starting WorkerPool with {self.config.num_workers} workers")

        # DB 엔진 초기화 (모든 워커 공유)
        self._engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            future=True,
            pool_size=self.config.num_workers + 2,
            max_overflow=5,
        )
        async_session = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self._started = True

        # 시그널 핸들러 설정
        self._setup_signal_handlers()

        try:
            # 워커 태스크 생성
            for worker_id in range(self.config.num_workers):
                task = asyncio.create_task(
                    self._run_worker_supervised(
                        worker_id=worker_id,
                        async_session=async_session,
                    ),
                    name=f"worker-{worker_id}",
                )
                self._tasks.append(task)

            # shutdown_event 대기 태스크
            shutdown_wait = asyncio.create_task(self._shutdown_event.wait())

            # 모든 워커 태스크 + shutdown 대기 태스크
            wait_tasks = self._tasks + [shutdown_wait]

            while True:
                done, pending = await asyncio.wait(
                    wait_tasks,
                    return_when=asyncio.FIRST_COMPLETED,
                )

                # shutdown_event가 설정됨
                if shutdown_wait in done:
                    logger.info("Shutdown event received, cancelling workers...")
                    for task in self._tasks:
                        if not task.done():
                            task.cancel()
                    # 취소 완료 대기
                    await asyncio.gather(*self._tasks, return_exceptions=True)
                    break

                # 모든 워커가 종료됨 (shutdown 전)
                if all(task.done() for task in self._tasks):
                    logger.info("All workers stopped")
                    shutdown_wait.cancel()
                    try:
                        await shutdown_wait
                    except asyncio.CancelledError:
                        pass
                    break

                # 일부 워커만 종료됨, 나머지 대기
                wait_tasks = [t for t in wait_tasks if not t.done()]

        except Exception as e:
            logger.error(f"Worker pool error: {e}")
        finally:
            await self._cleanup()

    async def stop(self) -> None:
        """워커 풀 정지."""
        if self._shutdown_event.is_set():
            return  # 이미 종료 중

        logger.info("Stopping WorkerPool...")
        self._shutdown_event.set()

    def _setup_signal_handlers(self) -> None:
        """시그널 핸들러 설정."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.warning("No running event loop, skipping signal handlers")
            return

        def handle_shutdown() -> None:
            if not self._shutdown_event.is_set():
                logger.info("Shutdown signal received")
                self._shutdown_event.set()

        try:
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, handle_shutdown)
        except NotImplementedError:
            # Windows 폴백
            logger.warning("Using fallback signal handling (Windows)")
            signal.signal(signal.SIGINT, lambda s, f: handle_shutdown())

    async def _run_worker_supervised(
        self,
        worker_id: int,
        async_session: async_sessionmaker,
    ) -> None:
        """워커 실행 (재시작 감독)."""
        restart_count = 0

        while (
            not self._shutdown_event.is_set()
            and restart_count < self.config.max_restarts_per_worker
        ):
            try:
                await self._run_single_worker(worker_id, async_session)
                break  # 정상 종료

            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                raise

            except Exception as e:
                restart_count += 1
                delay = min(
                    self.config.restart_delay_base * (2 ** restart_count),
                    self.config.restart_delay_max,
                )
                logger.error(
                    f"Worker {worker_id} crashed "
                    f"({restart_count}/{self.config.max_restarts_per_worker}), "
                    f"restarting in {delay:.1f}s: {e}"
                )

                if restart_count < self.config.max_restarts_per_worker:
                    try:
                        await asyncio.wait_for(
                            self._shutdown_event.wait(),
                            timeout=delay,
                        )
                        break  # Shutdown 중이면 재시작 취소
                    except asyncio.TimeoutError:
                        pass  # 대기 완료, 재시작 진행

        if restart_count >= self.config.max_restarts_per_worker:
            logger.critical(f"Worker {worker_id} exceeded max restarts")

    async def _run_single_worker(
        self,
        worker_id: int,
        async_session: async_sessionmaker,
    ) -> None:
        """단일 워커 실행."""
        # 워커별 독립 Redis 연결
        redis = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            single_connection_client=True,
        )

        consecutive_errors = 0
        logger.info(f"Worker {worker_id} started")

        try:
            while not self._shutdown_event.is_set():
                try:
                    async with async_session() as session:
                        context = create_worker_context(session, redis)
                        processed = await process_one_task(context)

                        if processed:
                            consecutive_errors = 0
                        else:
                            # 큐가 비었을 때 shutdown 체크 가능하도록 짧은 대기
                            await asyncio.sleep(0.1)

                except asyncio.CancelledError:
                    raise

                except Exception as e:
                    consecutive_errors += 1
                    category = classify_error(e)

                    if consecutive_errors >= self.config.max_consecutive_errors:
                        raise RuntimeError(
                            f"Too many consecutive errors ({consecutive_errors})"
                        ) from e

                    delay = self._calculate_error_delay(category, consecutive_errors)
                    logger.warning(
                        f"Worker {worker_id} error ({category.name}): {e}, "
                        f"waiting {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
        finally:
            await redis.aclose()
            logger.info(f"Worker {worker_id} stopped")

    def _calculate_error_delay(
        self,
        category: ErrorCategory,
        consecutive_errors: int,
    ) -> float:
        """에러 종류별 대기 시간 계산."""
        if category == ErrorCategory.PERMANENT:
            return 0.1
        elif category == ErrorCategory.TRANSIENT:
            return 1.0
        elif category == ErrorCategory.RETRYABLE:
            return min(2 ** consecutive_errors, 60)
        else:
            return 1.0

    async def _cleanup(self) -> None:
        """리소스 정리."""
        logger.info("Cleaning up WorkerPool resources...")

        if self._engine:
            await self._engine.dispose()
            self._engine = None

        self._tasks.clear()
        logger.info("WorkerPool cleanup completed")


async def run_worker_pool() -> None:
    """워커 풀 실행 진입점."""
    config = WorkerPoolConfig.from_env()
    pool = WorkerPool(config=config)
    await pool.start()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(run_worker_pool())
