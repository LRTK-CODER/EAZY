"""
Database migration utilities with distributed locking.

This module provides safe migration execution with:
- Database connection retry logic
- PostgreSQL advisory locks for concurrent safety
- Alembic migration execution
"""

import os
import sys
import time
from contextlib import contextmanager
from typing import Generator

from alembic import command
from alembic.config import Config

# Migration lock ID (consistent across all instances)
MIGRATION_LOCK_ID = 42
MIGRATION_LOCK_TIMEOUT = 60  # seconds
DB_CONNECT_TIMEOUT = 30  # seconds
DB_CONNECT_RETRY_INTERVAL = 2  # seconds


def get_database_url() -> str:
    """Get database URL from environment variables."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # Build from individual components
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    server = os.getenv("POSTGRES_SERVER", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "eazy")

    return f"postgresql://{user}:{password}@{server}:{port}/{db}"


def get_asyncpg_url() -> str:
    """Get asyncpg-compatible database URL."""
    url = get_database_url()
    # Remove driver prefix if present
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    return url


def wait_for_db(timeout: int = DB_CONNECT_TIMEOUT) -> bool:
    """
    Wait for database to be available.

    Args:
        timeout: Maximum time to wait in seconds

    Returns:
        True if database is available, False otherwise
    """
    import psycopg2

    url = get_database_url()
    # Parse URL for psycopg2
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")

    start_time = time.time()
    last_error = None

    print(f"Waiting for database connection (timeout: {timeout}s)...")

    while time.time() - start_time < timeout:
        try:
            conn = psycopg2.connect(url, connect_timeout=5)
            conn.close()
            print("Database connection established.")
            return True
        except psycopg2.OperationalError as e:
            last_error = e
            elapsed = int(time.time() - start_time)
            print(f"  Waiting for database... ({elapsed}s)")
            time.sleep(DB_CONNECT_RETRY_INTERVAL)

    print(f"Failed to connect to database after {timeout}s: {last_error}")
    return False


@contextmanager
def advisory_lock(
    lock_id: int = MIGRATION_LOCK_ID,
    timeout: int = MIGRATION_LOCK_TIMEOUT,
) -> Generator[bool, None, None]:
    """
    Acquire PostgreSQL advisory lock for migration.

    Uses pg_advisory_lock which blocks until lock is available.
    This ensures only one instance runs migrations at a time.

    Args:
        lock_id: Unique lock identifier
        timeout: Maximum time to wait for lock in seconds

    Yields:
        True if lock acquired, False otherwise
    """
    import psycopg2

    url = get_database_url()
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")

    conn = None
    lock_acquired = False

    try:
        conn = psycopg2.connect(url)
        conn.autocommit = True
        cursor = conn.cursor()

        # Try to acquire lock with timeout
        cursor.execute(f"SET lock_timeout = '{timeout}s'")
        cursor.execute(f"SELECT pg_advisory_lock({lock_id})")
        lock_acquired = True
        print(f"Advisory lock {lock_id} acquired.")

        yield True

    except psycopg2.OperationalError as e:
        print(f"Failed to acquire advisory lock: {e}")
        yield False

    finally:
        if lock_acquired and conn:
            try:
                cursor = conn.cursor()
                cursor.execute(f"SELECT pg_advisory_unlock({lock_id})")
                print(f"Advisory lock {lock_id} released.")
            except Exception as e:
                print(f"Warning: Failed to release lock: {e}")

        if conn:
            conn.close()


def run_alembic_migrations() -> bool:
    """
    Run Alembic migrations.

    Returns:
        True if migrations successful, False otherwise
    """
    try:
        # Find alembic.ini
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        alembic_ini = os.path.join(base_dir, "alembic.ini")

        if not os.path.exists(alembic_ini):
            print(f"alembic.ini not found at {alembic_ini}")
            return False

        # Configure Alembic
        config = Config(alembic_ini)
        config.set_main_option("script_location", os.path.join(base_dir, "alembic"))

        # Override sqlalchemy.url with environment variable
        db_url = get_database_url()
        config.set_main_option("sqlalchemy.url", db_url)

        print("Running Alembic migrations...")
        command.upgrade(config, "head")
        print("Migrations completed successfully.")
        return True

    except Exception as e:
        print(f"Migration failed: {e}")
        return False


def run_migrations_with_lock() -> bool:
    """
    Run migrations with distributed locking.

    This is the main entry point for migration execution.
    It ensures:
    1. Database is available
    2. Only one instance runs migrations (via advisory lock)
    3. Alembic migrations are applied

    Returns:
        True if migrations successful, False otherwise
    """
    # Step 1: Wait for database
    if not wait_for_db():
        print("ERROR: Database not available. Aborting.")
        return False

    # Step 2: Acquire lock and run migrations
    with advisory_lock() as locked:
        if not locked:
            print("ERROR: Could not acquire migration lock. Aborting.")
            return False

        # Step 3: Run migrations
        return run_alembic_migrations()


def main() -> int:
    """CLI entry point."""
    success = run_migrations_with_lock()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
