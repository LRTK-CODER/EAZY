import hashlib
from typing import Optional, Dict, Any, List, Tuple
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from urllib.parse import urlparse

from app.models.asset import Asset, AssetDiscovery, AssetType, AssetSource
from app.core.utils import utc_now
from app.core.constants import MAX_BODY_SIZE


class AssetService:
    BATCH_SIZE = 50

    def __init__(self, session: AsyncSession):
        self.session = session
        self._pending_assets: List[Asset] = []
        self._pending_discoveries: List[Tuple[int, Asset, Optional[int]]] = []

    async def __aenter__(self) -> "AssetService":
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager, flush pending data."""
        await self.flush()

    async def flush(self) -> None:
        """Flush pending assets and discoveries to database."""
        if not self._pending_assets:
            return

        # 1. Assets 저장
        self.session.add_all(self._pending_assets)
        await self.session.flush()  # ID 생성됨

        # 2. Discoveries 생성 (이제 asset.id 접근 가능)
        discoveries = []
        for task_id, asset, parent_id in self._pending_discoveries:
            discovery = AssetDiscovery(
                task_id=task_id,
                asset_id=asset.id,
                parent_asset_id=parent_id,
                discovered_at=utc_now(),
            )
            discoveries.append(discovery)

        self.session.add_all(discoveries)
        await self.session.commit()

        # 3. 버퍼 초기화
        self._pending_assets.clear()
        self._pending_discoveries.clear()

    def _generate_content_hash(self, method: str, url: str) -> str:
        """
        Generate a unique hash for the asset content.
        For MVP, we use Method + URL (excluding query params potentially, but for now full URL).
        """
        # Simple unique key: Method + URL
        # Robust deduplication might normalize URL (remove query params, sort them, etc.)
        identifier = f"{method.upper()}:{url}"
        return hashlib.sha256(identifier.encode()).hexdigest()

    def _truncate_body(
        self, spec: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Truncate body field in request/response spec if it exceeds MAX_BODY_SIZE.

        Args:
            spec: Request or response spec dictionary

        Returns:
            Spec with truncated body if needed
        """
        if spec is None:
            return None

        # Make a copy to avoid mutating the original
        spec = spec.copy()

        if "body" in spec and spec["body"]:
            body = spec["body"]
            # Convert to string if needed
            if isinstance(body, str):
                if len(body) > MAX_BODY_SIZE:
                    # Truncate to fit within MAX_BODY_SIZE including suffix
                    truncate_suffix = "... [TRUNCATED]"
                    truncate_at = MAX_BODY_SIZE - len(truncate_suffix)
                    spec["body"] = body[:truncate_at] + truncate_suffix

        return spec

    async def process_asset(
        self,
        target_id: int,
        task_id: int,
        url: str,
        method: str = "GET",
        type: AssetType = AssetType.URL,
        source: AssetSource = AssetSource.HTML,
        parent_asset_id: Optional[int] = None,
        # NEW PARAMETERS
        request_spec: Optional[Dict[str, Any]] = None,
        response_spec: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Asset:
        """
        Process a discovered asset with HTTP data and parameters.

        Args:
            target_id: Target ID
            task_id: Task ID
            url: Asset URL
            method: HTTP method (GET, POST, etc.)
            type: Asset type enum
            source: Asset source enum
            parent_asset_id: Parent asset ID (discovery chain)
            request_spec: HTTP request data (method, headers, body)
            response_spec: HTTP response data (status, headers, body)
            parameters: Parsed URL/form parameters

        Returns:
            Asset object (created or updated)
        """
        parsed = urlparse(url)
        path = parsed.path if parsed.path else "/"
        content_hash = self._generate_content_hash(method, url)

        # Truncate bodies if needed
        request_spec = self._truncate_body(request_spec)
        response_spec = self._truncate_body(response_spec)

        # Check for existing asset
        statement = select(Asset).where(Asset.content_hash == content_hash)
        result = await self.session.exec(statement)
        existing_asset = result.first()

        current_time = utc_now()

        if existing_asset:
            # Update existing asset
            asset = existing_asset
            asset.last_seen_at = current_time
            asset.last_task_id = task_id

            # Update HTTP data (overwrite with latest)
            if request_spec is not None:
                asset.request_spec = request_spec
            if response_spec is not None:
                asset.response_spec = response_spec
            if parameters is not None:
                asset.parameters = parameters
        else:
            # Create new asset
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
                last_seen_at=current_time,
                # NEW FIELDS
                request_spec=request_spec,
                response_spec=response_spec,
                parameters=parameters,
            )

        # Buffer asset and discovery info (defer commit)
        self._pending_assets.append(asset)
        self._pending_discoveries.append((task_id, asset, parent_asset_id))

        # Flush when batch size reached
        if len(self._pending_assets) >= self.BATCH_SIZE:
            await self.flush()

        return asset
