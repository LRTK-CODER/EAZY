"""
EAZY Workers Package

This package provides the worker infrastructure for processing async tasks.

Usage:
    from app.workers import run_worker
    asyncio.run(run_worker())

    # Or for custom workers:
    from app.workers import BaseWorker, WorkerContext, TaskResult
    from app.workers import CrawlWorker
    from app.workers import WORKER_REGISTRY, register_worker, create_worker
"""

from app.workers.base import BaseWorker, TaskResult, WorkerContext
from app.workers.crawl_worker import CrawlWorker
from app.workers.registry import (
    WORKER_REGISTRY,
    create_worker,
    get_worker_class,
    register_worker,
)
from app.workers.runner import create_worker_context, process_one_task, run_worker

__all__ = [
    # Base classes
    "BaseWorker",
    "WorkerContext",
    "TaskResult",
    # Workers
    "CrawlWorker",
    # Registry
    "WORKER_REGISTRY",
    "get_worker_class",
    "register_worker",
    "create_worker",
    # Runner
    "run_worker",
    "process_one_task",
    "create_worker_context",
]
