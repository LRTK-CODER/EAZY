#!/bin/bash
# EAZY Backend Entrypoint Script
#
# This script handles:
# 1. Database connection waiting
# 2. Automatic Alembic migrations (with distributed lock)
# 3. Application startup (uvicorn or worker)
#
# Usage:
#   ./entrypoint.sh              # Run as API server (default)
#   ./entrypoint.sh worker       # Run as worker
#   ./entrypoint.sh migrate      # Run migrations only
#   ./entrypoint.sh <command>    # Run custom command

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
MIGRATION_TIMEOUT=${MIGRATION_TIMEOUT:-60}
DB_WAIT_TIMEOUT=${DB_WAIT_TIMEOUT:-30}
SKIP_MIGRATIONS=${SKIP_MIGRATIONS:-false}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Wait for database to be ready
wait_for_db() {
    log_info "Waiting for database connection..."

    local timeout=${DB_WAIT_TIMEOUT}
    local elapsed=0

    while [ $elapsed -lt $timeout ]; do
        if python -c "
import psycopg2
import os

url = os.getenv('DATABASE_URL', '')
if not url:
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    server = os.getenv('POSTGRES_SERVER', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    db = os.getenv('POSTGRES_DB', 'eazy')
    url = f'postgresql://{user}:{password}@{server}:{port}/{db}'

if url.startswith('postgresql+asyncpg://'):
    url = url.replace('postgresql+asyncpg://', 'postgresql://')

conn = psycopg2.connect(url, connect_timeout=5)
conn.close()
" 2>/dev/null; then
            log_info "Database connection established."
            return 0
        fi

        echo "  Waiting for database... (${elapsed}s/${timeout}s)"
        sleep 2
        elapsed=$((elapsed + 2))
    done

    log_error "Database connection timeout after ${timeout}s"
    return 1
}

# Run database migrations with advisory lock
run_migrations() {
    if [ "$SKIP_MIGRATIONS" = "true" ]; then
        log_warn "Skipping migrations (SKIP_MIGRATIONS=true)"
        return 0
    fi

    log_info "Running database migrations..."

    python -m app.db.migrations
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        log_info "Migrations completed successfully."
        return 0
    else
        log_error "Migration failed with exit code $exit_code"
        return 1
    fi
}

# Start the API server
start_api() {
    log_info "Starting API server..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
}

# Start the worker
start_worker() {
    log_info "Starting worker pool..."
    exec python -m app.workers.pool
}

# Main entrypoint logic
main() {
    local command="${1:-api}"

    log_info "========================================="
    log_info "EAZY Backend Entrypoint"
    log_info "Command: $command"
    log_info "========================================="

    # Step 1: Wait for database
    if ! wait_for_db; then
        log_error "Failed to connect to database. Exiting."
        exit 1
    fi

    # Step 2: Run migrations (unless running custom command)
    case "$command" in
        api|worker|migrate)
            if ! run_migrations; then
                log_error "Migration failed. Exiting."
                exit 1
            fi
            ;;
        *)
            log_warn "Skipping migrations for custom command"
            ;;
    esac

    # Step 3: Start application
    case "$command" in
        api)
            start_api
            ;;
        worker)
            start_worker
            ;;
        migrate)
            log_info "Migration-only mode. Exiting."
            exit 0
            ;;
        *)
            log_info "Running custom command: $@"
            exec "$@"
            ;;
    esac
}

# Handle signals for graceful shutdown
trap 'log_info "Received SIGTERM, shutting down..."; exit 0' SIGTERM
trap 'log_info "Received SIGINT, shutting down..."; exit 0' SIGINT

# Run main function with all arguments
main "$@"
