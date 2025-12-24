import hashlib
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from urllib.parse import urlparse

from app.models.asset import Asset, AssetDiscovery, AssetType, AssetSource, utc_now

class AssetService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _generate_content_hash(self, method: str, url: str) -> str:
        """
        Generate a unique hash for the asset content.
        For MVP, we use Method + URL (excluding query params potentially, but for now full URL).
        """
        # Simple unique key: Method + URL
        # Robust deduplication might normalize URL (remove query params, sort them, etc.)
        identifier = f"{method.upper()}:{url}"
        return hashlib.sha256(identifier.encode()).hexdigest()

    async def process_asset(
        self,
        target_id: int,
        task_id: int,
        url: str,
        method: str = "GET",
        type: AssetType = AssetType.URL,
        source: AssetSource = AssetSource.HTML,
        parent_asset_id: Optional[int] = None
    ) -> Asset:
        """
        Process a discovered asset:
        1. Calculate content hash.
        2. Check if Asset exists (by hash).
        3. If exists -> Update last_seen_at.
        4. If new -> Create Asset.
        5. Create AssetDiscovery record (History).
        """
        parsed = urlparse(url)
        path = parsed.path if parsed.path else "/"
        content_hash = self._generate_content_hash(method, url)
        
        # Check for existing asset
        statement = select(Asset).where(Asset.content_hash == content_hash)
        result = await self.session.exec(statement)
        existing_asset = result.first()
        
        current_time = utc_now()
        
        if existing_asset:
            asset = existing_asset
            asset.last_seen_at = current_time
            asset.last_task_id = task_id
            self.session.add(asset)
        else:
            asset = Asset(
                target_id=target_id,
                content_hash=content_hash,
                type=type,
                source=source,
                method=method,
                url=url,
                path=path,
                last_task_id=task_id,
                first_seen_at=current_time,
                last_seen_at=current_time
            )
            self.session.add(asset)
        
        # Determine Asset ID (Need flush if new)
        await self.session.commit()
        await self.session.refresh(asset)
        
        # Create History Record (Always)
        discovery = AssetDiscovery(
            task_id=task_id,
            asset_id=asset.id,
            parent_asset_id=parent_asset_id,
            discovered_at=current_time
        )
        self.session.add(discovery)
        await self.session.commit()
        
        return asset
