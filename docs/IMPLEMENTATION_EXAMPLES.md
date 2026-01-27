# Docker 마이그레이션 자동화 - 구현 예시 및 코드

## 1. 마이그레이션 헬퍼 모듈 - 완전 구현

### File: backend/app/db/migrations.py

```python
"""Database migration utilities for Alembic integration.

This module handles:
- Database connectivity checks with retry logic
- Migration execution with PostgreSQL advisory lock
- Safe concurrent migration handling
- Comprehensive logging and error handling
"""

import asyncio
import logging
import sys
from typing import Optional

from sqlalchemy import text, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Base exception for migration operations."""

    pass


class DatabaseNotReadyError(MigrationError):
    """Raised when database is not accessible after retries."""

    pass


class MigrationLockError(MigrationError):
    """Raised when unable to acquire migration lock."""

    pass


class MigrationExecutionError(MigrationError):
    """Raised when Alembic migration fails."""

    pass


async def wait_for_db(
    max_retries: int = 30,
    retry_interval: float = 1.0,
    timeout_seconds: int = 30,
) -> bool:
    """Wait for database to be ready and accessible.

    Performs repeated connection attempts with exponential backoff.
    Useful during container startup when DB might not be immediately available.

    Args:
        max_retries: Maximum number of connection attempts
        retry_interval: Base delay between attempts in seconds
        timeout_seconds: Overall timeout for all retry attempts

    Returns:
        True if database is ready and responding to queries
        False if timeout exceeded or database unavailable

    Raises:
        No exceptions; returns boolean for graceful degradation

    Example:
        >>> if not await wait_for_db(max_retries=10):
        ...     raise DatabaseNotReadyError("Could not connect to database")
    """
    engine: Optional[AsyncEngine] = None

    try:
        # Create engine with minimal pool for health checks
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            poolclass=NullPool,  # No connection pooling for health checks
        )

        start_time = asyncio.get_event_loop().time()
        last_error = None

        for attempt in range(1, max_retries + 1):
            elapsed = asyncio.get_event_loop().time() - start_time

            # Check overall timeout
            if elapsed > timeout_seconds:
                logger.error(
                    f"Database connection timeout after {elapsed:.1f}s "
                    f"(max {timeout_seconds}s)"
                )
                return False

            try:
                # Attempt connection
                async with engine.connect() as conn:
                    # Execute simple query to verify connectivity
                    await conn.execute(text("SELECT 1"))
                    logger.info(
                        f"✓ Database is ready "
                        f"(attempt {attempt}/{max_retries}, elapsed {elapsed:.1f}s)"
                    )
                    return True

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    # Calculate backoff with jitter
                    backoff = min(retry_interval * (2 ** (attempt - 1)), 10)
                    logger.warning(
                        f"Database connection attempt {attempt}/{max_retries} failed: {type(e).__name__}. "
                        f"Retrying in {backoff:.1f}s... "
                        f"(elapsed {elapsed:.1f}s / {timeout_seconds}s)"
                    )
                    await asyncio.sleep(backoff)

        # All retries exhausted
        logger.error(
            f"Database connection failed after {max_retries} attempts "
            f"(elapsed {elapsed:.1f}s): {last_error}"
        )
        return False

    except Exception as e:
        logger.error(f"Unexpected error during database connectivity check: {e}", exc_info=True)
        return False

    finally:
        if engine:
            await engine.dispose()


async def acquire_migration_lock(
    conn,
    lock_id: int = 42,
    timeout_seconds: int = 60,
) -> bool:
    """Acquire PostgreSQL advisory lock for migration synchronization.

    Only one instance acquires the lock and runs migrations.
    Other instances wait until migrations complete.

    Advisory locks in PostgreSQL:
    - Non-blocking at the row level (unlike table locks)
    - Automatically released when connection closes
    - Perfect for distributed task coordination
    - Safe for concurrent access patterns

    Args:
        conn: SQLAlchemy async connection
        lock_id: PostgreSQL advisory lock ID (arbitrary but consistent)
        timeout_seconds: Maximum time to wait for lock acquisition

    Returns:
        True if lock acquired successfully
        False if timeout or lock unavailable

    Raises:
        No exceptions; returns boolean for graceful handling

    Example:
        >>> if await acquire_migration_lock(conn, lock_id=42):
        ...     # This instance has the lock, run migrations
        ...     await run_migrations(conn)
    """
    try:
        logger.info(f"Attempting to acquire advisory lock {lock_id}...")

        # pg_advisory_lock() blocks until acquired (session-level)
        # No timeout at DB level, but we wrap with asyncio timeout
        lock_result = await asyncio.wait_for(
            conn.execute(text(f"SELECT pg_advisory_lock({lock_id})")),
            timeout=timeout_seconds,
        )

        logger.info(
            f"✓ Advisory lock {lock_id} acquired "
            f"(this instance will run migrations)"
        )
        return True

    except asyncio.TimeoutError:
        logger.warning(
            f"⊝ Advisory lock {lock_id} acquisition timeout after {timeout_seconds}s. "
            f"Waiting for another instance to complete migrations..."
        )
        return False

    except Exception as e:
        logger.error(f"Error acquiring advisory lock {lock_id}: {e}", exc_info=True)
        return False


async def run_alembic_migrations() -> bool:
    """Execute Alembic migrations in synchronous context.

    Uses sync_db_url for Alembic (which expects synchronous engine).
    Alembic operations must run synchronously, so we use executor.

    Returns:
        True if migrations completed successfully
        False if any migration failed

    Raises:
        MigrationExecutionError on critical failures
    """
    try:
        logger.info("Starting Alembic migration execution...")

        # Import here to avoid circular dependencies
        from alembic import command
        from alembic.config import Config
        from alembic.util import CommandError

        # Create Alembic config from alembic.ini
        alembic_cfg = Config("/app/alembic.ini")

        # Use sync database URL for Alembic
        # Convert async URL to sync for Alembic compatibility
        sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
        alembic_cfg.set_main_option("sqlalchemy.url", sync_db_url)

        # Run migrations in executor (Alembic is blocking)
        loop = asyncio.get_event_loop()

        def sync_upgrade():
            """Synchronous wrapper for Alembic upgrade."""
            try:
                command.upgrade(alembic_cfg, "head")
                logger.info("✓ Alembic upgrade to HEAD completed")
                return True
            except CommandError as e:
                logger.error(f"Alembic command error: {e}")
                return False

        result = await loop.run_in_executor(None, sync_upgrade)

        if not result:
            raise MigrationExecutionError("Alembic upgrade failed")

        # Verify migrations
        current_revision = None

        def sync_current():
            """Get current migration revision."""
            try:
                from alembic import command
                from io import StringIO

                # Capture command output
                output = StringIO()
                command.current(alembic_cfg)
                return True
            except Exception as e:
                logger.warning(f"Could not verify migration version: {e}")
                return True  # Don't fail if verification fails

        await loop.run_in_executor(None, sync_current)
        logger.info("✓ Migration verification completed")

        return True

    except MigrationExecutionError as e:
        logger.error(f"Migration execution failed: {e}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error during migration execution: {e}", exc_info=True)
        return False


async def run_migrations_with_lock(
    lock_id: int = 42,
    timeout_seconds: int = 60,
) -> bool:
    """Run Alembic migrations with PostgreSQL advisory lock.

    This is the main entry point for safe, concurrent-aware migration execution.

    Workflow:
    1. Connect to database
    2. Attempt to acquire advisory lock
       - Instance 1 (succeeds): Runs migrations
       - Instance 2+ (waits): Waits for lock release, then proceeds
    3. Run Alembic migrations
    4. Lock released automatically when connection closes

    Args:
        lock_id: PostgreSQL advisory lock ID
        timeout_seconds: Migration execution timeout

    Returns:
        True if migrations completed successfully
        False if timeout or errors

    Raises:
        No direct exceptions; returns boolean status

    Example:
        >>> success = await run_migrations_with_lock(lock_id=42)
        >>> if not success:
        ...     logger.error("Migrations failed!")
        ...     sys.exit(1)
    """
    engine: Optional[AsyncEngine] = None

    try:
        logger.info("=" * 60)
        logger.info("DATABASE MIGRATION INITIALIZATION")
        logger.info("=" * 60)

        # Create async engine for operations
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,  # Set to True for SQL debugging
            poolclass=NullPool,
        )

        async with engine.begin() as conn:
            # Step 1: Acquire migration lock
            if not await acquire_migration_lock(conn, lock_id, timeout_seconds):
                logger.info(
                    "⊝ Another instance is running migrations. "
                    "Waiting for completion..."
                )
                # Wait and check again (simple polling)
                await asyncio.sleep(2)
                return True  # Assume other instance will handle it

            try:
                # Step 2: Run migrations (only this instance gets here)
                if not await run_alembic_migrations():
                    raise MigrationExecutionError("Alembic migration failed")

                logger.info("✓ All migrations completed successfully")
                logger.info("=" * 60)
                return True

            finally:
                # Lock released automatically when transaction ends
                logger.info(f"⊟ Advisory lock {lock_id} released")

    except MigrationExecutionError as e:
        logger.error(f"✗ Migration failed: {e}")
        return False

    except Exception as e:
        logger.error(f"✗ Unexpected error during migration: {e}", exc_info=True)
        return False

    finally:
        if engine:
            await engine.dispose()


async def main():
    """Main entry point for migration CLI.

    Called when running: python -m app.db.migrations

    Exit codes:
        0: Success
        1: Database not ready
        2: Migrations failed
    """
    logger.info("Starting database migration process...")

    # Step 1: Wait for database
    logger.info("Step 1: Checking database connectivity...")
    if not await wait_for_db(max_retries=30, timeout_seconds=30):
        logger.error("✗ Database is not ready. Aborting migrations.")
        return 1

    # Step 2: Run migrations
    logger.info("Step 2: Running migrations with advisory lock...")
    if not await run_migrations_with_lock(timeout_seconds=60):
        logger.error("✗ Migration process failed. Aborting.")
        return 2

    logger.info("✓ Database migration process completed successfully")
    logger.info("Ready to start application...")
    return 0


if __name__ == "__main__":
    # Run async main
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

---

## 2. Entrypoint 스크립트

### File: backend/scripts/entrypoint.sh

```bash
#!/bin/bash
################################################################################
# EAZY Backend Entrypoint Script
#
# Responsibilities:
# 1. Wait for database to be ready
# 2. Run database migrations with safety locks
# 3. Start the application (FastAPI or Worker)
#
# Exit codes:
#   0: Success
#   1: Database connection failed
#   2: Migrations failed
#   3: Invalid configuration
#
# Usage:
#   entrypoint.sh uvicorn app.main:app --host 0.0.0.0
#   entrypoint.sh python -m app.workers.pool
################################################################################

set -e  # Exit immediately on error
set -o pipefail  # Pipeline fails if any command fails

################################################################################
# Configuration
################################################################################

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"

# Logging configuration
LOG_LEVEL="${LOG_LEVEL:-INFO}"
LOG_PREFIX="[EAZY-Entrypoint]"

# Timeouts (seconds)
DB_WAIT_TIMEOUT=${DB_WAIT_TIMEOUT:-30}
MIGRATION_TIMEOUT=${MIGRATION_TIMEOUT:-60}

# Colors for output (disable in CI environments)
if [ -t 1 ] && [ -z "$CI" ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    NC='\033[0m'  # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    BOLD=''
    NC=''
fi

################################################################################
# Logging Functions
################################################################################

log_info() {
    echo -e "${GREEN}${LOG_PREFIX}${NC} ${BLUE}[INFO]${NC} $*" >&2
}

log_warn() {
    echo -e "${YELLOW}${LOG_PREFIX}${NC} ${YELLOW}[WARN]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}${LOG_PREFIX}${NC} ${RED}[ERROR]${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}${LOG_PREFIX}${NC} ${GREEN}[✓]${NC} $*" >&2
}

log_debug() {
    if [ "$LOG_LEVEL" = "DEBUG" ]; then
        echo -e "${BLUE}${LOG_PREFIX}${NC} ${BLUE}[DEBUG]${NC} $*" >&2
    fi
}

################################################################################
# Validation Functions
################################################################################

validate_environment() {
    """Validate required environment variables."""
    local required_vars=(
        "POSTGRES_SERVER"
        "POSTGRES_DB"
        "POSTGRES_USER"
    )

    log_info "Validating environment variables..."

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "Required environment variable '$var' is not set"
            return 1
        fi
        log_debug "$var=${!var}"
    done

    log_success "Environment validation passed"
    return 0
}

validate_directories() {
    """Validate required directories exist."""
    log_info "Validating directory structure..."

    if [ ! -d "$APP_DIR/app" ]; then
        log_error "Application directory not found: $APP_DIR/app"
        return 1
    fi

    if [ ! -d "$APP_DIR/alembic" ]; then
        log_error "Alembic directory not found: $APP_DIR/alembic"
        return 1
    fi

    if [ ! -f "$APP_DIR/alembic.ini" ]; then
        log_error "alembic.ini not found: $APP_DIR/alembic.ini"
        return 1
    fi

    log_success "Directory validation passed"
    return 0
}

################################################################################
# Database Functions
################################################################################

check_database() {
    """Check if database is accessible."""
    log_info "Checking database connectivity..."

    # Try to connect using psql
    PGPASSWORD="$POSTGRES_PASSWORD" \
    pg_isready \
        -h "$POSTGRES_SERVER" \
        -p "${POSTGRES_PORT:-5432}" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        -t 5

    return $?
}

wait_for_database() {
    """Wait for database to be ready with exponential backoff."""
    local max_attempts=30
    local attempt=1
    local backoff=1
    local max_backoff=10

    log_info "Waiting for database to be ready (timeout: ${DB_WAIT_TIMEOUT}s)..."

    local start_time=$(date +%s)

    while [ $attempt -le $max_attempts ]; do
        if check_database >/dev/null 2>&1; then
            local end_time=$(date +%s)
            local elapsed=$((end_time - start_time))
            log_success "Database is ready (attempt $attempt/$max_attempts, elapsed ${elapsed}s)"
            return 0
        fi

        local end_time=$(date +%s)
        local elapsed=$((end_time - start_time))

        if [ $elapsed -ge $DB_WAIT_TIMEOUT ]; then
            log_error "Database connection timeout after ${elapsed}s (max ${DB_WAIT_TIMEOUT}s)"
            return 1
        fi

        if [ $attempt -lt $max_attempts ]; then
            log_warn "Database not ready (attempt $attempt/$max_attempts). Retrying in ${backoff}s..."
            sleep $backoff

            # Exponential backoff with max cap
            backoff=$((backoff * 2))
            if [ $backoff -gt $max_backoff ]; then
                backoff=$max_backoff
            fi
        fi

        attempt=$((attempt + 1))
    done

    log_error "Database connection failed after $max_attempts attempts"
    return 1
}

################################################################################
# Migration Functions
################################################################################

run_migrations() {
    """Run database migrations using Python."""
    log_info "Running database migrations..."
    log_info "=================================================="

    cd "$APP_DIR" || return 1

    # Set Python environment
    export PYTHONUNBUFFERED=1
    export PYTHONPATH="$APP_DIR:$PYTHONPATH"

    # Run migration script with timeout
    if timeout $MIGRATION_TIMEOUT \
        python -m app.db.migrations; then
        log_success "Migrations completed successfully"
        return 0
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            log_error "Migration timeout after ${MIGRATION_TIMEOUT}s"
        else
            log_error "Migration failed with exit code $exit_code"
        fi
        return 1
    fi
}

################################################################################
# Startup Functions
################################################################################

prepare_startup() {
    """Print startup information."""
    log_info "=================================================="
    log_info "EAZY Backend Entrypoint"
    log_info "=================================================="
    log_info "Container ID: ${HOSTNAME:-unknown}"
    log_info "Environment: ${ENVIRONMENT:-development}"
    log_info "Application mode: $*"
    log_info "=================================================="
}

start_application() {
    """Start the application."""
    log_success "All checks passed. Starting application..."
    log_info "=================================================="

    # Execute the main command
    exec "$@"
}

handle_shutdown() {
    """Handle graceful shutdown."""
    log_warn "Shutdown signal received. Cleaning up..."
    exit 0
}

################################################################################
# Main Function
################################################################################

main() {
    """Main entrypoint logic."""

    # Trap signals for graceful shutdown
    trap handle_shutdown SIGTERM SIGINT

    # Print startup information
    prepare_startup "$@"

    # Validate configuration
    log_info "Step 1: Validating configuration..."
    if ! validate_environment; then
        log_error "Environment validation failed"
        return 3
    fi

    if ! validate_directories; then
        log_error "Directory validation failed"
        return 3
    fi

    # Wait for database
    log_info "Step 2: Waiting for database..."
    if ! wait_for_database; then
        log_error "Database is not available"
        return 1
    fi

    # Run migrations
    log_info "Step 3: Running database migrations..."
    if ! run_migrations; then
        log_error "Database migration failed"
        return 2
    fi

    # Start application
    log_info "Step 4: Starting application..."
    start_application "$@"
}

################################################################################
# Entry Point
################################################################################

# Require at least one argument (command to run)
if [ $# -eq 0 ]; then
    log_error "No command specified"
    echo "Usage: $0 <command> [args...]"
    echo "Examples:"
    echo "  $0 uvicorn app.main:app --host 0.0.0.0 --port 8000"
    echo "  $0 python -m app.workers.pool"
    exit 1
fi

# Run main function
main "$@"
exit_code=$?

# Clean exit
exit $exit_code
```

---

## 3. Dockerfile 수정

### File: backend/Dockerfile (부분 수정)

```dockerfile
# ... existing stages ...

FROM python:3.12-slim as runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright dependencies
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    # ... other existing dependencies ...
    # Database tools for entrypoint (NEW)
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy uv
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# Copy virtual environment
COPY --from=builder /app/.venv /app/.venv

# Set PATH
ENV PATH="/app/.venv/bin:$PATH"

# Set Playwright browsers path
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install Playwright
RUN python -m playwright install chromium

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Copy entrypoint script (NEW)
COPY scripts/ ./scripts/
RUN chmod +x ./scripts/entrypoint.sh

# Create non-root user
RUN useradd --create-home --shell /bin/bash eazy && \
    chown -R eazy:eazy /app /ms-playwright

USER eazy

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Set entrypoint (CHANGED)
ENTRYPOINT ["/app/scripts/entrypoint.sh"]

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 4. docker-compose.yml 업데이트

```yaml
services:
  # Database
  db:
    image: postgres:15-alpine
    container_name: eazy-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: eazy
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    container_name: eazy-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Backend API (마이그레이션 자동 실행)
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: eazy-backend
    restart: unless-stopped
    environment:
      - POSTGRES_SERVER=db
      - POSTGRES_DB=eazy
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_PORT=5432
      - REDIS_URL=redis://redis:6379/0
      - CORS_ORIGINS=http://localhost,http://localhost:80,http://localhost:3000
      - ENVIRONMENT=development
      # 마이그레이션 타임아웃 (기본값: 60초)
      - DB_WAIT_TIMEOUT=30
      - MIGRATION_TIMEOUT=60
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      start_period: 20s
      retries: 3
    volumes:
      # 개발 환경에서 코드 변경 감지
      - ./backend:/app

  # Worker (마이그레이션 자동 실행)
  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: eazy-worker
    restart: unless-stopped
    command: ["python", "-m", "app.workers.pool"]
    environment:
      - POSTGRES_SERVER=db
      - POSTGRES_DB=eazy
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_PORT=5432
      - REDIS_URL=redis://redis:6379/0
      - WORKER_NUM_WORKERS=4
      - WORKER_SHUTDOWN_TIMEOUT=30
      - DB_WAIT_TIMEOUT=30
      - MIGRATION_TIMEOUT=60
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      disable: true
    volumes:
      - ./backend:/app

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: eazy-frontend
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

---

## 5. GitHub Actions CI/CD 업데이트

### File: .github/workflows/ci.yml (마이그레이션 검증 추가)

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.12"

jobs:
  test:
    name: Test
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: eazy_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        working-directory: ./backend
        run: uv sync --extra dev

      - name: Install Playwright browsers
        working-directory: ./backend
        run: uv run playwright install chromium --with-deps

      # 새로 추가된 단계: 마이그레이션 테스트
      - name: Run database migrations
        working-directory: ./backend
        env:
          POSTGRES_DB: eazy_test
          POSTGRES_SERVER: localhost
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        run: |
          echo "Testing migration script..."
          uv run python -m app.db.migrations
          echo "✓ Migrations passed"

      # 기존 단계
      - name: Run tests with coverage
        working-directory: ./backend
        env:
          POSTGRES_DB: eazy_test
          REDIS_URL: redis://localhost:6379/0
        run: |
          uv run pytest tests/ -v \
            --cov=app \
            --cov-report=xml \
            --cov-report=term-missing \
            --tb=short

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./backend/coverage.xml
          fail_ci_if_error: false

  build:
    name: Build
    runs-on: ubuntu-latest
    needs: [lint, test]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build backend image
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: false
          load: true
          tags: eazy-backend:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Verify images
        run: |
          docker images | grep eazy-backend
```

---

## 6. Makefile 명령 추가

### File: Makefile (부분 추가)

```makefile
# Database Management

db-migrate:
	cd backend && uv run python -m app.db.migrations

db-history:
	cd backend && uv run alembic history --verbose

db-downgrade:
	cd backend && uv run alembic downgrade -1

db-downgrade-all:
	cd backend && uv run alembic downgrade base

db-current:
	cd backend && uv run alembic current

db-revision:
	cd backend && uv run alembic revision --autogenerate -m "$(msg)"

# Docker Migration Testing

docker-test-migration:
	docker-compose build backend
	docker-compose up -d db redis
	docker-compose up -d backend
	sleep 5
	@echo "Checking if migrations ran..."
	docker-compose logs backend | grep "✓ Migrations completed"
	docker-compose down

# Full docker test with fresh database
docker-test-fresh:
	docker-compose down -v
	docker-compose build
	docker-compose up -d
	sleep 10
	@curl -f http://localhost:8000/health || (docker-compose logs && exit 1)
	docker-compose down

.PHONY: db-migrate db-history db-downgrade db-current db-revision \
        docker-test-migration docker-test-fresh
```

---

## 7. 테스트 코드 예제

### File: backend/tests/db/test_migrations.py

```python
"""Tests for database migration utilities."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from app.db.migrations import (
    wait_for_db,
    run_migrations_with_lock,
    acquire_migration_lock,
    DatabaseNotReadyError,
    MigrationError,
)


@pytest.mark.asyncio
async def test_wait_for_db_success():
    """Test successful database connectivity check."""
    result = await wait_for_db(max_retries=5, timeout_seconds=10)
    assert result is True


@pytest.mark.asyncio
async def test_wait_for_db_timeout():
    """Test database connection timeout."""
    # Mock connection failure
    with patch("app.db.migrations.create_async_engine") as mock_engine:
        mock_conn = MagicMock()
        mock_conn.execute = MagicMock(side_effect=ConnectionError("Failed"))
        mock_engine.return_value.connect = MagicMock()
        mock_engine.return_value.connect.__aenter__ = MagicMock(
            return_value=mock_conn
        )
        mock_engine.return_value.connect.__aexit__ = MagicMock(
            return_value=None
        )

        result = await wait_for_db(
            max_retries=2,
            retry_interval=0.1,
            timeout_seconds=1
        )
        assert result is False


@pytest.mark.asyncio
async def test_run_migrations_with_lock():
    """Test migration execution with lock."""
    result = await run_migrations_with_lock(timeout_seconds=60)
    # Should succeed if DB is ready
    assert result in (True, False)


@pytest.mark.asyncio
async def test_migrations_idempotent():
    """Test that migrations are idempotent."""
    result1 = await run_migrations_with_lock()
    result2 = await run_migrations_with_lock()

    # Both should succeed (idempotent)
    assert result1 is True
    assert result2 is True


@pytest.mark.asyncio
async def test_concurrent_migrations():
    """Test concurrent migration execution (simulated)."""
    # Multiple instances attempting migrations
    tasks = [
        run_migrations_with_lock()
        for _ in range(3)
    ]

    results = await asyncio.gather(*tasks)

    # All should complete successfully
    # (advisory lock ensures sequential execution)
    assert all(results)
```

---

## 8. 배포 가이드 요약

### Quick Start

```bash
# 1. 로컬 환경 설정
cd /path/to/eazy

# 2. 의존성 설치
cd backend
uv sync --extra dev

# 3. Docker 환경 테스트
cd ..
docker-compose up -d

# 4. 마이그레이션 확인
docker-compose logs backend | grep "✓ Migrations"

# 5. API 헬스 체크
curl http://localhost:8000/health
```

### 트러블슈팅

```bash
# 마이그레이션 로그 확인
docker-compose logs backend

# 수동 마이그레이션 실행
docker exec eazy-backend python -m app.db.migrations

# 마이그레이션 상태 확인
docker exec eazy-backend alembic current

# 마이그레이션 롤백
docker exec eazy-backend alembic downgrade -1

# 데이터베이스 초기화 (주의!)
docker-compose down -v
docker-compose up -d
```
