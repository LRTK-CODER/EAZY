# Phase 1: 인프라 계층 분리

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
Redis Queue, Distributed Lock, Session Manager를 새로운 인터페이스 기반으로 재구현하여 안정성과 테스트 용이성을 확보합니다.

### 성공 기준
- [x] SessionManager가 안전한 세션 생명주기 관리
- [x] TaskQueueV2가 Lua 스크립트 기반 원자적 연산 제공
- [x] DistributedLockV2가 Fencing token으로 안전성 보장
- [x] 각 컴포넌트의 단위 테스트 커버리지 ≥90%
- [x] 통합 테스트에서 동시성 문제 없음

### 사용자 영향
- Task Stuck 문제 해결
- Lock 경합으로 인한 무한 재시도 방지
- 시스템 안정성 향상

---

## 🏗️ 아키텍처 결정

| 결정 | 이유 | 트레이드오프 |
|------|------|------------|
| Lua 스크립트 사용 | 원자적 연산 보장, Race condition 방지 | Redis 버전 의존성, 디버깅 복잡도 |
| Fencing token | Lock 안전성 향상, Split-brain 방지 | 추가 Redis 키 사용 |
| Visibility timeout | Orphan task 자동 복구 | 복잡도 증가 |
| Connection pool | 성능 최적화, 리소스 관리 | 메모리 사용량 증가 |

---

## 📦 의존성

### 시작 전 필요 사항
- [ ] Git 브랜치 `feature/active-scan-v2` 생성
- [ ] Redis Docker 컨테이너 실행 확인
- [ ] PostgreSQL 연결 확인

### 외부 의존성
- redis>=5.0.0 (이미 설치됨)
- sqlmodel>=0.0.22 (이미 설치됨)

---

## 🧪 테스트 전략

### 테스트 접근법
**TDD 원칙**: 테스트를 먼저 작성하고, 테스트를 통과시키는 구현을 작성

### 이 Phase의 테스트 피라미드
| 테스트 유형 | 커버리지 목표 | 목적 |
|------------|--------------|------|
| **단위 테스트** | ≥90% | SessionManager, Queue, Lock 로직 |
| **통합 테스트** | Critical paths | Redis 연동, DB 연동 |
| **동시성 테스트** | Lock 경합 시나리오 | Race condition 검증 |

### 테스트 파일 구조
```
backend/tests/
├── unit/
│   └── core/
│       ├── test_session_manager.py
│       ├── test_queue_v2.py
│       └── test_lock_v2.py
└── integration/
    └── core/
        ├── test_queue_redis.py
        └── test_lock_concurrency.py
```

---

## 🚀 구현 작업

### Day 1-2: SessionManager 구현

> **기존 세션 패턴 참조**:
> - `core/db.py:21-24`: `get_session()` - FastAPI 의존성 주입용 async generator
> - `workers/pool.py:126-130`: `async_sessionmaker` - WorkerPool에서 세션 생성
> - `workers/pool.py:300-302`: `async with async_session() as session` - 워커에서 세션 사용
>
> **SessionManager**는 이 패턴들을 통합하여 일관된 세션 관리 API를 제공합니다.

**🔴 RED: 실패하는 테스트 먼저 작성**

- [ ] **Test 1.1**: SessionManager 단위 테스트 작성
  - File(s): `tests/unit/core/test_session_manager.py`
  - Expected: 테스트 FAIL (SessionManager가 아직 없음)
  - 테스트 케이스:
    ```python
    class TestSessionManager:
        async def test_session_commits_on_success(self):
            """성공 시 자동 커밋"""
            pass

        async def test_session_rollbacks_on_exception(self):
            """예외 시 자동 롤백"""
            pass

        async def test_session_closes_after_use(self):
            """사용 후 세션 닫힘"""
            pass

        async def test_nested_transaction_with_savepoint(self):
            """SAVEPOINT를 사용한 중첩 트랜잭션"""
            pass

        async def test_connection_pool_configuration(self):
            """Connection pool 설정 적용"""
            pass
    ```

- [ ] **Test 1.2**: SessionManager 통합 테스트 작성
  - File(s): `tests/integration/core/test_session_integration.py`
  - Expected: 테스트 FAIL
  - 테스트 케이스:
    - 실제 DB와의 트랜잭션
    - Rollback 후 데이터 무결성

**🟢 GREEN: 테스트를 통과시키는 구현**

- [ ] **Task 1.3**: SessionManager 클래스 구현
  - File(s): `backend/app/core/session.py`
  - 목표: Test 1.1 통과
  - 구현 내용:
    ```python
    class SessionManager:
        def __init__(self, database_url: str, pool_size: int = 5):
            ...

        @asynccontextmanager
        async def session(self) -> AsyncGenerator[AsyncSession, None]:
            """자동 commit/rollback/close 세션"""
            ...

        @asynccontextmanager
        async def transaction(self, session: AsyncSession):
            """SAVEPOINT를 사용한 중첩 트랜잭션"""
            ...
    ```

- [ ] **Task 1.4**: FastAPI 의존성 함수 구현
  - File(s): `backend/app/core/session.py`
  - 목표: Test 1.2 통과
  - 구현 내용:
    ```python
    from app.core.config import settings

    # Singleton SessionManager 인스턴스
    _session_manager: SessionManager | None = None

    def get_session_manager() -> SessionManager:
        """SessionManager 싱글톤 인스턴스 반환."""
        global _session_manager
        if _session_manager is None:
            _session_manager = SessionManager(
                database_url=settings.DATABASE_URL,
                pool_size=5,
            )
        return _session_manager

    async def get_session() -> AsyncGenerator[AsyncSession, None]:
        """FastAPI 의존성 주입용 세션 (기존 db.py:get_session() 대체)."""
        manager = get_session_manager()
        async with manager.session() as session:
            yield session

    # WorkerPool 통합
    def create_worker_session_factory(num_workers: int) -> async_sessionmaker:
        """
        WorkerPool용 세션 팩토리 생성.

        기존 workers/pool.py:126-130의 패턴을 SessionManager로 통합.
        """
        manager = get_session_manager()
        return manager.create_session_factory(pool_size=num_workers + 2)
    ```

**🔵 REFACTOR: 코드 정리**

- [ ] **Task 1.5**: 코드 품질 개선
  - 체크리스트:
    - [ ] 중복 코드 제거
    - [ ] 명명 규칙 개선
    - [ ] 타입 힌트 추가
    - [ ] Docstring 추가

---

### Day 3-4: TaskQueueV2 구현

**🔴 RED: 실패하는 테스트 먼저 작성**

- [ ] **Test 2.1**: TaskQueueV2 단위 테스트 작성
  - File(s): `tests/unit/core/test_queue_v2.py`
  - Expected: 테스트 FAIL
  - 테스트 케이스:
    ```python
    from app.core.priority import TaskPriority

    class TestTaskQueueV2:
        async def test_enqueue_with_priority(self):
            """우선순위별 enqueue (기존 TaskPriority 사용)"""
            queue = TaskQueueV2(redis)
            await queue.enqueue({"task": 1}, TaskPriority.HIGH)
            await queue.enqueue({"task": 2}, TaskPriority.NORMAL)
            # ...

        async def test_dequeue_respects_priority_order(self):
            """CRITICAL → HIGH → NORMAL → LOW 순서 (TaskPriority 값 기준)"""
            pass

        async def test_ack_removes_from_processing(self):
            """ACK 시 processing queue에서 제거"""
            pass

        async def test_nack_with_retry_adds_to_delayed(self):
            """NACK with retry 시 delayed queue로"""
            pass

        async def test_nack_without_retry_adds_to_dlq(self):
            """NACK without retry 시 DLQ로"""
            pass

        async def test_visibility_timeout_handling(self):
            """Visibility timeout 초과 시 복구"""
            pass

        async def test_exponential_backoff_calculation(self):
            """지수 백오프 계산"""
            pass
    ```

- [ ] **Test 2.2**: TaskQueueV2 통합 테스트 작성
  - File(s): `tests/integration/core/test_queue_redis.py`
  - Expected: 테스트 FAIL
  - 테스트 케이스:
    - 실제 Redis와의 연동
    - Lua 스크립트 실행
    - 동시 enqueue/dequeue

**🟢 GREEN: 테스트를 통과시키는 구현**

- [ ] **Task 2.3**: TaskQueueV2 클래스 구현
  - File(s): `backend/app/core/queue_v2.py`
  - 목표: Test 2.1 통과
  - **중요**: 기존 `TaskPriority` (`core/priority.py`) **재사용**. 새로운 QueuePriority 정의하지 않음!
  - 구현 내용:
    ```python
    # 기존 TaskPriority 재사용 (새로 정의하지 않음!)
    from app.core.priority import TaskPriority, PRIORITY_ORDER, get_queue_key

    class TaskQueueV2:
        # Lua 스크립트 (원자적 dequeue)
        DEQUEUE_SCRIPT = """..."""

        # Lua 스크립트 (안전한 ACK)
        ACK_SCRIPT = """..."""

        async def enqueue(self, task_data, priority) -> str:
            ...

        async def dequeue(self, timeout) -> Optional[Tuple]:
            ...

        async def ack(self, task_json) -> bool:
            ...

        async def nack(self, task_json, error, retry) -> bool:
            ...

        async def process_delayed(self) -> int:
            ...

        async def recover_orphans(self) -> int:
            ...
    ```

**🔵 REFACTOR: 코드 정리**

- [ ] **Task 2.4**: 코드 품질 개선
  - 체크리스트:
    - [ ] Lua 스크립트 분리 및 문서화
    - [ ] 에러 메시지 개선
    - [ ] 로깅 추가

---

### Day 5: DistributedLockV2 구현

**🔴 RED: 실패하는 테스트 먼저 작성**

- [ ] **Test 3.1**: DistributedLockV2 단위 테스트 작성
  - File(s): `tests/unit/core/test_lock_v2.py`
  - Expected: 테스트 FAIL
  - 테스트 케이스:
    ```python
    class TestDistributedLockV2:
        async def test_acquire_returns_fence_token(self):
            """획득 시 fence token 반환"""
            pass

        async def test_release_requires_matching_token(self):
            """해제 시 token 검증"""
            pass

        async def test_only_one_can_acquire(self):
            """동시 획득 시 하나만 성공"""
            pass

        async def test_lock_renewal_extends_ttl(self):
            """갱신 시 TTL 연장"""
            pass

        async def test_fence_token_increases_monotonically(self):
            """fence token 단조 증가"""
            pass
    ```

- [ ] **Test 3.2**: 동시성 테스트 작성
  - File(s): `tests/integration/core/test_lock_concurrency.py`
  - Expected: 테스트 FAIL
  - 테스트 케이스:
    - 100개 동시 Lock 획득 시도
    - Lock 해제 후 다른 worker 획득

**🟢 GREEN: 테스트를 통과시키는 구현**

- [ ] **Task 3.3**: DistributedLockV2 클래스 구현
  - File(s): `backend/app/core/lock_v2.py`
  - 목표: Test 3.1 통과
  - 구현 내용:
    ```python
    class LockLevel(Enum):
        TASK = "task"
        URL = "url"
        TARGET = "target"

    class DistributedLockV2:
        # Lua 스크립트 (fence token 포함 획득)
        ACQUIRE_SCRIPT = """..."""

        # Lua 스크립트 (token 검증 후 해제)
        RELEASE_SCRIPT = """..."""

        async def acquire(self, timeout) -> bool:
            ...

        async def release(self) -> bool:
            ...

        def _start_renewal(self) -> None:
            ...

        async def __aenter__(self):
            ...

        async def __aexit__(self, ...):
            ...
    ```

- [ ] **Task 3.4**: URLLock 헬퍼 클래스 구현
  - File(s): `backend/app/core/lock_v2.py`
  - 목표: URL 레벨 Lock 제공

**🔵 REFACTOR: 코드 정리**

- [ ] **Task 3.5**: 코드 품질 개선
  - 체크리스트:
    - [ ] 비동기 컨텍스트 매니저 패턴 적용
    - [ ] 로깅 추가
    - [ ] 예외 클래스 정의

---

## ✋ Quality Gate

**⚠️ STOP: 모든 체크가 통과할 때까지 Phase 2로 진행하지 마세요**

### TDD 준수 (CRITICAL)
- [ ] **Red Phase**: 테스트를 먼저 작성하고 실패 확인
- [ ] **Green Phase**: 테스트를 통과시키는 최소 코드 작성
- [ ] **Refactor Phase**: 테스트 통과 상태에서 코드 개선
- [ ] **Coverage Check**: 테스트 커버리지 ≥90%

### 빌드 & 테스트
- [ ] **Build**: 프로젝트 빌드/컴파일 에러 없음
- [ ] **All Tests Pass**: 100% 테스트 통과 (스킵 없음)
- [ ] **Test Performance**: 테스트 스위트 30초 이내 완료
- [ ] **No Flaky Tests**: 3회 이상 실행해도 일관된 결과

### 코드 품질
- [ ] **Linting**: ruff check 에러/경고 없음
- [ ] **Formatting**: ruff format으로 포맷팅됨
- [ ] **Type Safety**: mypy 통과
- [ ] **Static Analysis**: 심각한 이슈 없음

### 보안 & 성능
- [ ] **Dependencies**: 알려진 보안 취약점 없음
- [ ] **Performance**: 성능 저하 없음
- [ ] **Memory**: 메모리 누수 없음
- [ ] **Error Handling**: 적절한 에러 핸들링 구현

### 문서화
- [ ] **Code Comments**: 복잡한 로직 문서화
- [ ] **API Docs**: 공개 인터페이스 문서화
- [ ] **README**: 필요시 사용법 업데이트

### 수동 테스트
- [ ] **기능**: 기능이 예상대로 동작
- [ ] **Edge Cases**: 경계 조건 테스트됨
- [ ] **Error States**: 에러 핸들링 검증됨

### 검증 명령어

```bash
# 테스트 실행
uv run pytest tests/unit/core/ -v

# 커버리지 확인
uv run pytest tests/unit/core/ --cov=app/core --cov-report=term-missing

# 통합 테스트 (Redis 필요)
docker-compose up -d redis
uv run pytest tests/integration/core/ -v

# 코드 품질
uv run ruff check app/core/
uv run ruff format --check app/core/
uv run mypy app/core/

# 빌드 확인
uv pip install -e . --dry-run
```

### 수동 테스트 체크리스트
- [ ] Redis CLI로 Queue 키 확인
- [ ] Lock 획득/해제 시 Redis 키 상태 확인
- [ ] 동시 Worker 실행 시 Lock 동작 확인

---

## ⚠️ 리스크 평가

| 리스크 | 확률 | 영향 | 완화 전략 |
|--------|------|------|----------|
| Redis Lua 스크립트 버그 | 중 | 높음 | 단위 테스트로 각 스크립트 검증 |
| 동시성 문제 | 높음 | 높음 | 동시성 테스트, Load 테스트 |
| Session 누수 | 중 | 중 | Context manager 패턴 강제 |

---

## 🔄 Rollback 전략

### Phase 1 실패 시
- 새로 생성된 파일 삭제:
  - `app/core/session.py`
  - `app/core/queue_v2.py`
  - `app/core/lock_v2.py`
- 테스트 파일 삭제
- 기존 `queue.py`, `lock.py` 유지

---

## 📊 진행 상황

### 완료 상태
- **Day 1-2 (SessionManager)**: ✅ 100%
- **Day 3-4 (TaskQueueV2)**: ✅ 100%
- **Day 5 (DistributedLockV2)**: ✅ 100%

### 시간 추적
| 작업 | 예상 | 실제 | 차이 |
|------|------|------|------|
| SessionManager | 16시간 | 완료 | - |
| TaskQueueV2 | 16시간 | 완료 | - |
| DistributedLockV2 | 8시간 | 완료 | - |
| **합계** | 40시간 | 완료 | - |

---

## 📝 Notes & Learnings

### 구현 노트
- SessionManager: 196줄 (core/session.py)
- TaskQueueV2: 537줄 (core/queue_v2.py) - Lua 스크립트 기반 원자적 연산
- DistributedLockV2: 333줄 (core/lock_v2.py) - Fencing token 패턴

### 발생한 Blockers
- 없음

### 향후 개선 사항
- 기존 queue.py, lock.py에서 마이그레이션 필요 (Phase 5에서 처리)

---

## 📚 참고 자료

### 문서
- [Redis Lua scripting](https://redis.io/docs/manual/programmability/eval-intro/)
- [SQLAlchemy async session](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

### 관련 이슈
- (관련 GitHub 이슈 링크)

---

**Phase Status**: ✅ Completed
**Completed**: 2025-01-29
**Next Phase**: Phase 2 (Domain 계층 추출)
