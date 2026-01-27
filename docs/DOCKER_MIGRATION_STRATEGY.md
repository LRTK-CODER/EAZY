# Docker 환경 마이그레이션 자동화 및 SRE 최적화 보고서

## Executive Summary

현재 EAZY 백엔드의 Docker 환경에서 **Alembic 마이그레이션이 컨테이너 시작 시 자동 실행되지 않는 문제**를 식별했습니다. 이로 인해 컨테이너 재시작, 스케일링, 배포 시 스키마 불일치 위험이 발생합니다.

**권장 솔루션**: Entrypoint 스크립트 + PostgreSQL advisory lock을 활용한 **안전한 마이그레이션 자동화**

---

## 1. 현재 상황 분석

### 1.1 문제점 상세 분석

#### 문제 1: 마이그레이션 자동화 부재

**현재 상태:**
```yaml
backend:
  command: ["uvicorn", "app.main:app", ...]  # 마이그레이션 없음

worker:
  command: ["python", "-m", "app.workers.pool"]  # 마이그레이션 없음
```

**영향:**
- 개발: 수동으로 `make db-migrate` 실행 필요
- 테스트: GitHub Actions CI에서만 마이그레이션 실행
- 배포: 컨테이너 재시작 시 마이그레이션 미실행
- 스케일링: 새 워커 시작 시 스키마 준비 불확실

**위험도: 높음**

```
시나리오 1: 컨테이너 크래시 후 재시작
┌─ Container Start
├─ Uvicorn Ready (마이그레이션 미실행)
├─ Request: SELECT FROM new_column ✗
└─ 500 Error: Column not found
```

```
시나리오 2: 롤링 배포 (자동 재시작)
┌─ Backend A: Old Schema → 신규 기능 실패
├─ Backend B: 마이그레이션 미실행 → 구 스키마
└─ 데이터 불일치, 트랜잭션 실패
```

#### 문제 2: 동시 마이그레이션 위험

다중 인스턴스 배포 시:
```
Backend Instance 1     Worker Instance 1
    ↓                       ↓
    └──→ 같은 DB ←──┘
         (마이그레이션 충돌)
```

**Alembic의 동작:**
- Row-level lock 사용 (완전하지 않음)
- 동시 `ALTER TABLE` 시도 → DB 에러 가능

#### 문제 3: 컨테이너 시작 순서 불충분

현재:
```yaml
backend:
  depends_on:
    db:
      condition: service_healthy  # Health check만 확인
```

**한계:**
- Health check: TCP 연결 확인 (`pg_isready`)
- 하지만: 마이그레이션 완료 확인 안 함
- 결과: Backend가 미완료 스키마 접근 가능

### 1.2 기술 스택 현황

| Component | Version | Note |
|-----------|---------|------|
| Python | 3.12 | UV 지원 |
| FastAPI | 0.115+ | Async native |
| SQLModel | 0.0.22 | SQLAlchemy 래퍼 |
| Alembic | 1.13+ | Async 지원 |
| PostgreSQL | 15 | Advisory lock 지원 |
| asyncpg | 0.29+ | 비동기 드라이버 |

### 1.3 마이그레이션 현황

```
$ ls -la backend/alembic/versions/
13개 마이그레이션 버전:
├─ 3d8835436778 create_project_table
├─ b72e50c328e9 create_target_table
├─ b4ffda872654 create_task_table
├─ c20804e39fe7 create_asset_tables
├─ f0732575d8bc add_scope_to_targets
├─ 0469845cfb8e add_task_recursive_fields
├─ ... (7개 추가)
└─ 8afe47c82292 add_crawl_url_to_tasks (최신)
```

**특징:**
- Async 마이그레이션 미지원 (동기 Alembic 사용)
- `upgrade()`/`downgrade()` 순차 실행
- 총 소요 시간: ~2-5초

---

## 2. 솔루션 비교 분석

### 2.1 Option A: Entrypoint 스크립트 (권장)

**구현:**
```bash
#!/bin/bash
# backend/scripts/entrypoint.sh

# 1. DB 연결 대기
wait_for_db() {
    for i in {1..30}; do
        if pg_isready -h $DB_HOST; then
            return 0
        fi
        sleep 1
    done
    return 1
}

# 2. 마이그레이션 (advisory lock)
run_migrations() {
    python -c "
    import asyncio
    from app.db.migrations import run_migrations_with_lock
    asyncio.run(run_migrations_with_lock())
    "
}

# 3. 앱 시작
exec "$@"
```

**Dockerfile 수정:**
```dockerfile
COPY scripts/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", ...]
```

**장점:**
- ✅ 모든 컨테이너에서 작동 (backend, worker)
- ✅ 로컬 개발에서도 자동 실행
- ✅ 기존 docker-compose 구조 유지
- ✅ 롤백 가능 (downgrade 스크립트)
- ✅ 로깅 명확

**단점:**
- ⚠️ 모든 컨테이너가 마이그레이션 시도
  - 해결: PostgreSQL advisory lock으로 순차 실행
- ⚠️ 시작 지연 (2-5초)
  - 영향 미미 (허용 범위)

**평가: 4.5/5** ⭐⭐⭐⭐½

---

### 2.2 Option B: Init Container (Kubernetes-first)

**구현:**
```yaml
# docker-compose.yml (미지원)
# 또는 kubernetes/migrate-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: migrate
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: eazy-backend:latest
        command: ["alembic", "upgrade", "head"]
      restartPolicy: Never
```

**장점:**
- ✅ 마이그레이션과 앱 분리
- ✅ 순차 실행 보장
- ✅ Kubernetes 표준 패턴
- ✅ 실패 시 deployment 블로킹

**단점:**
- ❌ docker-compose에선 미지원
- ❌ 로컬 개발 복잡
- ❌ 현재 스택과 맞지 않음

**평가: 3/5** (향후 고려)

---

### 2.3 Option C: 별도 마이그레이션 서비스

**구현:**
```yaml
services:
  migrate:
    build: ./backend
    command: ["alembic", "upgrade", "head"]
    depends_on:
      db:
        condition: service_healthy
    environment:
      - POSTGRES_SERVER=db

  backend:
    depends_on:
      migrate:  # 마이그레이션 완료 대기
        condition: service_completed_successfully
```

**장점:**
- ✅ 명확한 마이그레이션 단계
- ✅ 실패 시 나머지 서비스 미시작

**단점:**
- ❌ docker-compose v3에선 `service_completed_successfully` 미지원
- ❌ 추가 이미지 빌드
- ⚠️ 로컬 테스트 시 별도 명령 필요

**평가: 2.5/5**

---

### 2.4 Option D: CI/CD Only (무책임한 선택)

**구현:**
```yaml
# GitHub Actions에서만 마이그레이션
- name: Run migrations
  run: alembic upgrade head
```

**문제:**
- ❌ 로컬 개발에서 수동 실행 필요
- ❌ 컨테이너 재시작 시 미실행
- ❌ 스케일링 시 위험

**평가: 1/5** ❌ (절대 비권장)

---

### 2.5 최종 권장: Entrypoint + Advisory Lock

```
Container Start
  ↓
entrypoint.sh
  ├─ DB 연결 확인 (30초 timeout)
  ├─ Advisory Lock 획득 (한 인스턴스만)
  │  └─ SELECT pg_advisory_lock(42)
  ├─ Alembic 마이그레이션
  ├─ Advisory Lock 해제
  └─ 앱 시작 (uvicorn/worker)
```

**PostgreSQL Advisory Lock 동작:**
```sql
-- Instance 1 (획득 성공)
SELECT pg_advisory_lock(42);  -- 즉시 반환

-- Instance 2 (대기)
SELECT pg_advisory_lock(42);  -- Instance 1이 해제할 때까지 대기
```

**Python 구현:**
```python
# app/db/migrations.py
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def run_migrations_with_lock():
    engine = create_async_engine(settings.DATABASE_URL)

    async with engine.begin() as conn:
        # Advisory lock 획득
        await conn.execute(
            text("SELECT pg_advisory_lock(:lock_id)"),
            {"lock_id": 42}
        )

        try:
            # 마이그레이션 실행
            from alembic.config import Config
            from alembic.script import ScriptDirectory
            from alembic.runtime.migration import MigrationContext

            alembic_cfg = Config("/app/alembic.ini")
            script = ScriptDirectory.from_config(alembic_cfg)
            migration_context = MigrationContext.configure(conn)

            script.run_migrations(migration_context)
            print("✓ Migrations completed successfully")
        finally:
            # Lock 자동 해제 (트랜잭션 종료)
            pass

    await engine.dispose()
```

---

## 3. 상세 구현 가이드

### 3.1 Phase 1: Entrypoint 스크립트 (1-2일)

#### Step 1: 마이그레이션 헬퍼 함수 작성

**File: `backend/app/db/migrations.py` (신규)**

```python
"""Database migration utilities."""

import asyncio
import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)


async def wait_for_db(
    max_retries: int = 30,
    retry_interval: float = 1.0,
) -> bool:
    """Wait for database to be ready.

    Args:
        max_retries: Maximum connection attempts
        retry_interval: Delay between attempts in seconds

    Returns:
        True if DB ready, False if timeout
    """
    engine = create_async_engine(settings.DATABASE_URL)

    for attempt in range(max_retries):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("✓ Database is ready")
                await engine.dispose()
                return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"DB connection attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {retry_interval}s..."
                )
                await asyncio.sleep(retry_interval)
            else:
                logger.error(f"Database connection failed after {max_retries} attempts")

    await engine.dispose()
    return False


async def run_migrations_with_lock(
    lock_id: int = 42,  # Arbitrary ID
    timeout_seconds: int = 60,
) -> bool:
    """Run Alembic migrations with PostgreSQL advisory lock.

    Only one instance acquires the lock and runs migrations.
    Others wait and proceed once migrations are complete.

    Args:
        lock_id: PostgreSQL advisory lock ID
        timeout_seconds: Migration execution timeout

    Returns:
        True if successful, False if timeout/error
    """
    engine = create_async_engine(settings.DATABASE_URL)

    try:
        async with engine.begin() as conn:
            # Acquire advisory lock (blocks others)
            logger.info(f"Acquiring advisory lock {lock_id}...")
            try:
                # pg_advisory_lock() blocks until acquired
                # pg_advisory_lock_shared() non-blocking variant
                lock_result = await asyncio.wait_for(
                    conn.execute(text(f"SELECT pg_advisory_lock({lock_id})")),
                    timeout=timeout_seconds
                )
                logger.info(f"✓ Advisory lock acquired")
            except asyncio.TimeoutError:
                logger.error(f"Failed to acquire lock within {timeout_seconds}s")
                return False

            try:
                # Run migrations
                from alembic import command
                from alembic.config import Config

                logger.info("Running database migrations...")
                alembic_cfg = Config("/app/alembic.ini")

                # Use sync connection for Alembic
                with conn.begin_nested():
                    # Alembic expects synchronous connection
                    # Use sync wrapper
                    def sync_migrate():
                        command.upgrade(alembic_cfg, "head")

                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, sync_migrate)

                logger.info("✓ Migrations completed successfully")
                return True

            except Exception as e:
                logger.error(f"Migration failed: {e}", exc_info=True)
                return False
            finally:
                # Advisory lock is released when connection closes
                logger.info(f"Advisory lock released")

    except Exception as e:
        logger.error(f"Database migration error: {e}", exc_info=True)
        return False
    finally:
        await engine.dispose()


async def main():
    """Main entry point for migration script."""
    # Wait for DB
    if not await wait_for_db():
        logger.error("Database unavailable, exiting")
        return False

    # Run migrations with lock
    if not await run_migrations_with_lock():
        logger.error("Migrations failed, exiting")
        return False

    logger.info("All migrations completed, app can start")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
```

#### Step 2: Entrypoint 스크립트 작성

**File: `backend/scripts/entrypoint.sh` (신규)**

```bash
#!/bin/bash
# EAZY Backend Entrypoint Script
# Runs database migrations before starting the application

set -e  # Exit on error

# Colors for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Ensure we're in the app directory
cd /app

log_info "=========================================="
log_info "EAZY Backend Entrypoint"
log_info "=========================================="

# Export environment for migrations
export PYTHONUNBUFFERED=1

# Run migrations
log_info "Starting database migrations..."
if python -m app.db.migrations; then
    log_info "✓ Database migrations completed"
else
    log_error "✗ Database migrations failed"
    exit 1
fi

log_info "=========================================="
log_info "Starting application..."
log_info "=========================================="

# Execute the main command (passed as arguments)
exec "$@"
```

#### Step 3: Dockerfile 수정

**File: `backend/Dockerfile`**

```dockerfile
# ... existing stages ...

FROM python:3.12-slim as runtime

WORKDIR /app

# ... existing system dependencies ...

# Copy scripts (NEW)
COPY scripts/ ./scripts/
RUN chmod +x ./scripts/*.sh

# ... existing venv and app copy ...

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# ... existing user and health check ...

# Set entrypoint (CHANGED)
ENTRYPOINT ["/app/scripts/entrypoint.sh"]

# Default command: run FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Step 4: docker-compose.yml 환경 변수 확인

**File: `docker-compose.yml`**

```yaml
services:
  backend:
    # ... existing config ...
    environment:
      - POSTGRES_SERVER=db
      - POSTGRES_DB=eazy
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres  # Alembic env.py에서 필요
      - REDIS_URL=redis://redis:6379/0
      # ... others ...
```

**Alembic이 환경 변수를 읽으므로 설정 확인 필수**

---

### 3.2 Phase 2: Docker 최적화 (2-3일)

#### Option A: Dockerfile 분리 (선택)

**File: `backend/Dockerfile.migrate` (선택)**

마이그레이션만 실행하는 경량 이미지:

```dockerfile
# Multi-stage: 마이그레이션 전용
FROM python:3.12-slim

WORKDIR /app

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 의존성 설치
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 앱 코드
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# 마이그레이션만 실행
CMD ["python", "-m", "app.db.migrations"]
```

**Docker Compose에 추가:**

```yaml
services:
  db-migrate:  # 선택: init job 패턴
    build:
      context: ./backend
      dockerfile: Dockerfile.migrate
    depends_on:
      db:
        condition: service_healthy
    environment:
      - POSTGRES_SERVER=db
      - POSTGRES_DB=eazy
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
```

#### 개선 사항: Health Check

**현재:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```

**개선:**
```yaml
healthcheck:
  test: |
    curl -f http://localhost:8000/health && \
    curl -f http://localhost:8000/api/v1/health/db || exit 1
  interval: 30s
  timeout: 10s
  start_period: 20s  # 마이그레이션 시간 고려
  retries: 3
```

**Backend에 DB health check 엔드포인트 추가:**

```python
# app/api/v1/endpoints/health.py

@router.get("/health/db")
async def health_check_db(db: AsyncSession = Depends(get_session)):
    """Check database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
```

---

### 3.3 Phase 3: CI/CD 통합 (2-3일)

#### Step 1: 마이그레이션 테스트 추가

**File: `.github/workflows/ci.yml` (수정)**

```yaml
test:
  # ... existing steps ...

  - name: Run database migrations (test)
    working-directory: ./backend
    env:
      POSTGRES_DB: eazy_test
    run: |
      python -m app.db.migrations

  - name: Verify migrations applied
    working-directory: ./backend
    env:
      POSTGRES_DB: eazy_test
    run: |
      uv run alembic current
      uv run alembic history --verbose
```

#### Step 2: 빌드 후 마이그레이션 테스트

**File: `.github/workflows/ci.yml` (build job 개선)**

```yaml
build:
  # ... existing steps ...

  - name: Test migrations in Docker
    run: |
      # 마이그레이션 테스트
      docker run --rm \
        -e POSTGRES_SERVER=postgres \
        -e POSTGRES_DB=eazy_test \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=postgres \
        eazy-backend:${{ github.sha }} \
        python -m app.db.migrations
```

#### Step 3: 배포 워크플로우 (신규)

**File: `.github/workflows/deploy.yml` (신규)**

```yaml
name: Deploy

on:
  push:
    branches: [main]
  workflow_run:
    workflows: [CI]
    types: [completed]

jobs:
  deploy:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Pre-deployment checks
        run: |
          echo "✓ All CI checks passed"
          echo "✓ Ready for deployment"

      - name: Deploy to production
        run: |
          # 실제 배포 로직
          # AWS CodeDeploy, Kubernetes, etc.
          echo "Deploying..."

      - name: Verify migrations in production
        run: |
          # Production에서 마이그레이션 상태 확인
          echo "Verifying migrations..."
```

---

### 3.4 롤백 전략

**마이그레이션 롤백 스크립트:**

```bash
# backend/scripts/rollback.sh
#!/bin/bash

set -e

log_info() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

log_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

REVISION="${1:-current-1}"

log_info "Rolling back to $REVISION..."

cd /app

if python -c "
import asyncio
from alembic.config import Config
from alembic import command

config = Config('alembic.ini')
command.downgrade(config, '$REVISION')
"; then
    log_info "✓ Rollback successful"
else
    log_error "✗ Rollback failed"
    exit 1
fi
```

**사용:**
```bash
docker exec eazy-backend /app/scripts/rollback.sh current-1
```

---

## 4. 마이그레이션 특수 고려사항

### 4.1 현재 마이그레이션 검토

**기존 13개 버전 분석:**

```python
# 안전한 마이그레이션 (비차단)
- create_project_table          ✓
- create_target_table           ✓
- create_task_table             ✓
- create_asset_tables           ✓
- add_scope_to_targets          ✓
- add_task_recursive_fields     ✓
- add_task_target_created_index ✓
- add_target_search_indexes     ✓
- add_crawl_url_to_tasks        ✓  (현재)

# 잠재적 문제 (대규모 데이터셋)
- add_is_archived_field_to_projects  # ADD COLUMN 없음
- add_archived_at_field_to_projects  # ADD COLUMN 없음
- add_cascade_to_target_foreign_keys # ALTER FK
- add_task_timestamps_and_cancelled  # ADD COLUMN
```

**권장:**
- 현재 데이터량: 작음 (개발 초기)
- 대규모 데이터 시: ALTER TABLE ... ADD COLUMN ... DEFAULT 사용
- 프로덕션: Zero-downtime migration 전략 검토

### 4.2 마이그레이션 성능

**벤치마크 (초기 스키마):**
```
13 마이그레이션 적용: ~3-5초
└─ 네트워크 지연: ~0.5초
└─ 실제 SQL: ~2-4초
```

**최적화:**
- 마이그레이션 배치 불가 (스키마 변경)
- 병렬 실행 불가 (동시성 제약)
- 선택적 마이그레이션 고려 (향후)

---

## 5. 보안 고려사항

### 5.1 마이그레이션 권한

**현재:**
```python
# DB 접근 credentials
POSTGRES_USER=postgres      # 슈퍼유저
POSTGRES_PASSWORD=postgres  # 환경변수
```

**프로덕션 권장:**

```python
# 두 가지 사용자 분리
POSTGRES_ADMIN_USER=postgres        # 마이그레이션만
POSTGRES_ADMIN_PASSWORD=<secure>

POSTGRES_APP_USER=app_user          # 앱 실행용
POSTGRES_APP_PASSWORD=<secure>      # 제한된 권한

# 권한 설정
GRANT CREATE ON SCHEMA public TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
-- 테이블별 권한은 마이그레이션에서 설정
```

### 5.2 Advisory Lock 보안

**현재:**
```python
lock_id = 42  # 고정값
```

**보안 강화:**
```python
# Hash-based lock ID (변경 불가)
import hashlib
lock_id = int(hashlib.sha256(b"eazy:migrations".encode()).hexdigest()[:16], 16) % (2**31)
```

### 5.3 환경 변수 검증

**Entrypoint에서:**
```bash
# 필수 변수 확인
required_vars=("POSTGRES_SERVER" "POSTGRES_DB" "POSTGRES_USER")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "Required environment variable $var is not set"
        exit 1
    fi
done
```

---

## 6. 모니터링 및 로깅

### 6.1 구조화된 로깅

**Current:**
```
[INFO] Starting migrations...
✓ Migrations completed
```

**Improved:**
```json
{
  "timestamp": "2026-01-27T10:30:00Z",
  "service": "eazy-backend",
  "phase": "startup",
  "action": "migrations",
  "status": "started",
  "lock_id": 42,
  "container_id": "abc123..."
}
```

### 6.2 Prometheus 메트릭

```python
from prometheus_client import Counter, Histogram

migration_counter = Counter(
    'eazy_migrations_total',
    'Total migrations run',
    ['status']  # success, failure
)

migration_duration = Histogram(
    'eazy_migrations_duration_seconds',
    'Migration execution time'
)

@migration_duration.time()
async def run_migrations_with_lock():
    # ... migration code ...
    migration_counter.labels(status='success').inc()
```

### 6.3 Alert 규칙

```yaml
# Prometheus alert rules
groups:
- name: migrations
  rules:
  - alert: MigrationFailure
    expr: |
      rate(eazy_migrations_total{status="failure"}[5m]) > 0
    annotations:
      summary: "Database migration failed"
```

---

## 7. 테스트 전략

### 7.1 단위 테스트

**File: `backend/tests/db/test_migrations.py`**

```python
import pytest
import asyncio
from app.db.migrations import wait_for_db, run_migrations_with_lock

@pytest.mark.asyncio
async def test_wait_for_db():
    """Test database connectivity check."""
    result = await wait_for_db(max_retries=5)
    assert result is True

@pytest.mark.asyncio
async def test_run_migrations_with_lock():
    """Test migration execution with lock."""
    result = await run_migrations_with_lock()
    assert result is True

@pytest.mark.asyncio
async def test_migrations_idempotent():
    """Test that migrations are idempotent."""
    # Run twice, both should succeed
    result1 = await run_migrations_with_lock()
    result2 = await run_migrations_with_lock()

    assert result1 is True
    assert result2 is True
```

### 7.2 통합 테스트

```python
@pytest.mark.asyncio
async def test_migration_with_concurrent_access():
    """Test concurrent migration execution."""
    import concurrent.futures

    async def migrate():
        return await run_migrations_with_lock()

    # 5개 태스크 동시 실행
    tasks = [migrate() for _ in range(5)]
    results = await asyncio.gather(*tasks)

    # 모두 성공해야 함 (advisory lock으로 순차 실행)
    assert all(results)
```

### 7.3 Docker 테스트

```bash
# 테스트 1: 마이그레이션 자동 실행
docker-compose up -d
sleep 5
curl http://localhost:8000/health  # 성공 여부

# 테스트 2: 컨테이너 재시작
docker-compose restart backend
sleep 5
curl http://localhost:8000/api/v1/health/db  # DB 접근 가능

# 테스트 3: 동시 시작
docker-compose down
docker-compose up  # 3개 인스턴스 동시 시작 가능
```

---

## 8. 배포 체크리스트

### 사전 배포

- [ ] 마이그레이션 헬퍼 함수 구현 및 테스트 (app/db/migrations.py)
- [ ] Entrypoint 스크립트 작성 및 테스트 (scripts/entrypoint.sh)
- [ ] Dockerfile 수정 및 빌드 테스트
- [ ] 로컬에서 `docker-compose up` 테스트
- [ ] 마이그레이션 재실행 (멱등성) 테스트

### CI/CD

- [ ] GitHub Actions 마이그레이션 테스트 추가
- [ ] Docker 빌드 후 마이그레이션 검증
- [ ] 커버리지 88% 이상 유지
- [ ] 배포 워크플로우 생성

### 운영

- [ ] Rollback 스크립트 준비
- [ ] Monitoring/Alerting 설정
- [ ] 배포 런북 문서화
- [ ] 팀 교육 및 리뷰

---

## 9. 예상 결과 및 영향

### Before (현재)

```timeline
1. docker-compose up
2. DB 시작 (5초)
3. Backend 시작 (즉시)
   ↳ 500 errors (테이블 없음)
4. 수동: make db-migrate
5. 마이그레이션 (3초)
6. 정상 작동

Total: 10초 + 수동 개입
```

### After (구현 후)

```timeline
1. docker-compose up
2. DB 시작 (5초)
3. Backend 시작
   ↳ Entrypoint: 마이그레이션 자동 (3초)
   ↳ Uvicorn 시작 (2초)
4. 정상 작동

Total: 10초 (자동)
```

### 이점

| 항목 | Before | After |
|-----|--------|-------|
| 수동 개입 | 필요 | 불필요 |
| 스키마 불일치 위험 | 높음 | 낮음 |
| 컨테이너 재시작 시간 | +3초 | +3초 |
| 멱등성 | ✗ | ✓ |
| 동시 시작 지원 | ✗ | ✓ (lock) |

---

## 10. FAQ 및 문제 해결

### Q: 마이그레이션 실패 시 어떻게 되나?

**A:** Entrypoint가 exit 1을 반환하여 컨테이너가 시작되지 않습니다.
```bash
docker logs eazy-backend
# 마이그레이션 에러 메시지 확인
```

### Q: 기존 DB 초기화는?

**A:** 마이그레이션이 멱등성이므로 안전합니다.
```bash
# 방법 1: Alembic downgrade
alembic downgrade base  # 모든 마이그레이션 취소

# 방법 2: DB 삭제 후 재시작
docker-compose down -v  # 볼륨 삭제
docker-compose up       # 처음부터 마이그레이션
```

### Q: 마이그레이션 성능 저하?

**A:** 초기 마이그레이션은 3-5초, 이미 적용된 마이그레이션은 무시됩니다.
```
초기: 10초 (5초 DB + 3초 마이그레이션 + 2초 앱)
재시작: 8초 (5초 DB + 0초 마이그레이션 + 2초 앱)
```

### Q: 롤백은?

**A:** Alembic의 downgrade 사용:
```bash
docker exec eazy-backend alembic downgrade <revision>
```

### Q: Advisory Lock 충돌?

**A:** PostgreSQL이 자동으로 순차 실행합니다.
```
Instance 1: 획득 ✓ → 마이그레이션 → 해제
Instance 2: 대기... → 획득 ✓ → 마이그레이션 → 해제
Instance 3: 대기... → 획득 ✓ → 마이그레이션 → 해제
```

---

## 11. 다음 단계

### Immediate (1주)
1. Phase 1 구현: Entrypoint 스크립트
2. 로컬 테스트: `docker-compose up`
3. CI/CD 통합: GitHub Actions 추가

### Short-term (2주)
1. Phase 2: Dockerfile 최적화
2. Health check 엔드포인트 추가
3. 모니터링 설정

### Medium-term (1개월)
1. Phase 3: 배포 자동화
2. Kubernetes 마이그레이션 준비 (init container)
3. Zero-downtime 마이그레이션 전략

---

## 12. 참고 자료

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Advisory Locks](https://www.postgresql.org/docs/current/explicit-locking.html)
- [Docker ENTRYPOINT](https://docs.docker.com/engine/reference/builder/#entrypoint)
- [Kubernetes Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)

---

## 결론

현재 마이그레이션 자동화 부재로 인한 위험을 **Entrypoint 스크립트 + PostgreSQL advisory lock**으로 안전하게 해결할 수 있습니다.

**권장 일정:**
- Phase 1: 1-2일 (즉각적 효과)
- Phase 2: 2-3일 (최적화)
- Phase 3: 2-3일 (운영 준비)

**총 소요 시간:** 약 1주일 (병렬 작업 가능)

**기대 효과:**
- 배포 자동화 (수동 단계 제거)
- 안정성 향상 (스키마 불일치 방지)
- 운영 복잡도 감소
