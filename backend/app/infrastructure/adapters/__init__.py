"""Infrastructure adapters package.

Adapters wrap existing services to match port interfaces.
"""

from app.infrastructure.adapters.asset_repository_adapter import AssetRepositoryAdapter
from app.infrastructure.adapters.cancellation_adapter import CancellationAdapter
from app.infrastructure.adapters.crawler_adapter import CrawlerAdapter
from app.infrastructure.adapters.task_queue_adapter import TaskQueueAdapter

__all__ = [
    "CrawlerAdapter",
    "AssetRepositoryAdapter",
    "TaskQueueAdapter",
    "CancellationAdapter",
]
