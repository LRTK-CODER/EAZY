"""
Worker Registry for EAZY worker infrastructure.

Phase 3: Architecture Improvement

Provides a registry pattern for mapping task types to worker classes,
enabling easy extension of the worker system with new task types.
"""

from typing import Dict, Optional, Type, Union

from app.workers.base import BaseWorker, WorkerContext
from app.models.task import TaskType


# Worker Registry - maps task type to worker class
WORKER_REGISTRY: Dict[Union[TaskType, str], Type[BaseWorker]] = {}


def _register_default_workers():
    """Register default workers on module load."""
    from app.workers.crawl_worker import CrawlWorker

    WORKER_REGISTRY[TaskType.CRAWL] = CrawlWorker


def get_worker_class(task_type: Union[TaskType, str]) -> Optional[Type[BaseWorker]]:
    """
    Get worker class for a task type.

    Args:
        task_type: TaskType enum or string value

    Returns:
        Worker class or None if not found
    """
    # Try direct lookup first
    if task_type in WORKER_REGISTRY:
        return WORKER_REGISTRY[task_type]

    # Try to convert string to TaskType enum
    if isinstance(task_type, str):
        try:
            task_type_enum = TaskType(task_type)
            return WORKER_REGISTRY.get(task_type_enum)
        except ValueError:
            return None

    return None


def register_worker(task_type: Union[TaskType, str]):
    """
    Decorator to register a worker class for a task type.

    Usage:
        @register_worker(TaskType.ATTACK)
        class AttackWorker(BaseWorker):
            ...

    Args:
        task_type: The task type this worker handles

    Returns:
        Decorator function

    Raises:
        TypeError: If the class is not a BaseWorker subclass
    """

    def decorator(cls: Type[BaseWorker]) -> Type[BaseWorker]:
        if not issubclass(cls, BaseWorker):
            raise TypeError(f"{cls.__name__} must be a subclass of BaseWorker")
        WORKER_REGISTRY[task_type] = cls
        return cls

    return decorator


def create_worker(
    task_type: Union[TaskType, str], context: WorkerContext, **kwargs
) -> BaseWorker:
    """
    Factory function to create a worker instance.

    Args:
        task_type: Task type to create worker for
        context: WorkerContext with dependencies
        **kwargs: Additional arguments passed to worker constructor

    Returns:
        Worker instance

    Raises:
        ValueError: If task type is not registered
    """
    worker_class = get_worker_class(task_type)
    if worker_class is None:
        raise ValueError(f"Unknown task type: {task_type}")

    return worker_class(context, **kwargs)


# Register default workers when module is imported
_register_default_workers()
