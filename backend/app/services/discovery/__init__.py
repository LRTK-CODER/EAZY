"""Discovery 서비스 모듈.

Active Scan Discovery 시스템의 핵심 컴포넌트를 제공합니다.

Example:
    >>> from app.services.discovery import (
    ...     ScanProfile,
    ...     DiscoveredAsset,
    ...     DiscoveryContext,
    ...     BaseDiscoveryModule,
    ...     DiscoveryModuleRegistry,
    ... )
"""

from .base import BaseDiscoveryModule
from .models import DEFAULT_SCAN_PROFILE, DiscoveredAsset, DiscoveryContext, ScanProfile
from .registry import DiscoveryModuleRegistry, DuplicateModuleError
from .service import DiscoveryService

__all__ = [
    # Enums
    "ScanProfile",
    "DEFAULT_SCAN_PROFILE",
    # Data Classes
    "DiscoveredAsset",
    "DiscoveryContext",
    # Base Class
    "BaseDiscoveryModule",
    # Registry
    "DiscoveryModuleRegistry",
    "DuplicateModuleError",
    # Service
    "DiscoveryService",
]
