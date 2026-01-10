"""
Phase 4.5: Priority Queue System

Task priority levels and queue routing utilities.
Supports 4 priority levels: CRITICAL, HIGH, NORMAL, LOW.

Aging mechanism to prevent starvation of low priority tasks.
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Optional


class TaskPriority(IntEnum):
    """
    Task priority levels for queue processing order.

    Higher values = higher priority = processed first.

    Usage:
        from app.core.priority import TaskPriority

        # Enqueue with priority
        await task_manager.enqueue_crawl_task(
            project_id=1,
            target_id=1,
            db_task_id=100,
            priority=TaskPriority.HIGH
        )
    """

    LOW = 0  # Background tasks, can wait
    NORMAL = 1  # Default priority (backward compatible)
    HIGH = 2  # Important targets
    CRITICAL = 3  # Urgent scans (security issues)


# Queue key suffixes for each priority level
# NORMAL uses empty suffix for backward compatibility with existing queue
PRIORITY_QUEUE_SUFFIXES: Dict[TaskPriority, str] = {
    TaskPriority.CRITICAL: ":critical",
    TaskPriority.HIGH: ":high",
    TaskPriority.NORMAL: "",  # Default queue (backward compatible)
    TaskPriority.LOW: ":low",
}

# Processing order: CRITICAL first, LOW last
PRIORITY_ORDER = [
    TaskPriority.CRITICAL,
    TaskPriority.HIGH,
    TaskPriority.NORMAL,
    TaskPriority.LOW,
]


def get_queue_key(base_key: str, priority: TaskPriority) -> str:
    """
    Get the Redis queue key for a given priority.

    Args:
        base_key: Base queue key (e.g., 'eazy_task_queue')
        priority: Task priority level

    Returns:
        Full queue key with priority suffix

    Example:
        >>> get_queue_key('eazy_task_queue', TaskPriority.CRITICAL)
        'eazy_task_queue:critical'
        >>> get_queue_key('eazy_task_queue', TaskPriority.NORMAL)
        'eazy_task_queue'
    """
    suffix = PRIORITY_QUEUE_SUFFIXES.get(priority, "")
    return f"{base_key}{suffix}"


@dataclass
class AgingConfig:
    """
    Configuration for task aging/starvation prevention.

    Tasks waiting in lower priority queues beyond these thresholds
    will be promoted to the next higher priority level.

    Default values are conservative to prevent starvation while
    maintaining priority ordering benefits.
    """

    low_to_normal_seconds: int = 300  # 5 minutes
    normal_to_high_seconds: int = 600  # 10 minutes
    high_to_critical_seconds: int = 1800  # 30 minutes


def get_next_priority(priority: TaskPriority) -> Optional[TaskPriority]:
    """
    Get the next higher priority level.

    Args:
        priority: Current priority level

    Returns:
        Next higher priority or None if already CRITICAL
    """
    if priority == TaskPriority.LOW:
        return TaskPriority.NORMAL
    elif priority == TaskPriority.NORMAL:
        return TaskPriority.HIGH
    elif priority == TaskPriority.HIGH:
        return TaskPriority.CRITICAL
    return None  # CRITICAL has no higher level
