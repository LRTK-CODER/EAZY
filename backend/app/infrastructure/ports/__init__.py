"""Port interfaces for hexagonal architecture."""

from app.infrastructure.ports.asset_repository import IAssetRepository
from app.infrastructure.ports.cancellation import ICancellation
from app.infrastructure.ports.crawler import CrawlData, ICrawler
from app.infrastructure.ports.discovery import IDiscoveryService
from app.infrastructure.ports.task_queue import ITaskQueue

__all__ = [
    "CrawlData",
    "ICrawler",
    "IAssetRepository",
    "IDiscoveryService",
    "ICancellation",
    "ITaskQueue",
]
