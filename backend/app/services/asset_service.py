import hashlib
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from urllib.parse import urlparse

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.constants import MAX_BODY_SIZE
from app.core.utils import utc_now
from app.models.asset import Asset, AssetDiscovery, AssetSource, AssetType
from app.types.http import HttpRequestData, HttpResponseData


class AssetService:
    BATCH_SIZE = 50

    def __init__(self, session: AsyncSession):
        self.session = session
        self._pending_assets: List[Asset] = []
        self._pending_discoveries: List[Tuple[int, Asset, Optional[int]]] = []
        # Track content_hash -> Asset for deduplication within batch
        self._pending_hash_map: Dict[str, Asset] = {}

    async def __aenter__(self) -> "AssetService":
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager, flush pending data."""
        await self.flush()

    async def flush(self) -> None:
        """Flush pending assets and discoveries to database.

        Uses PostgreSQL upsert (INSERT ... ON CONFLICT DO UPDATE) to handle
        race conditions when parallel workers try to insert assets with the
        same content_hash simultaneously.
        """
        # Early return only if BOTH buffers are empty
        # (existing DB assets may have been modified and need commit via dirty tracking)
        if not self._pending_assets and not self._pending_discoveries:
            return

        # 1. Upsert new assets using PostgreSQL ON CONFLICT DO UPDATE
        # This handles race conditions where parallel workers insert same content_hash
        if self._pending_assets:
            for asset in self._pending_assets:
                stmt = (
                    pg_insert(Asset)
                    .values(
                        target_id=asset.target_id,
                        content_hash=asset.content_hash,
                        type=asset.type,
                        source=asset.source,
                        method=asset.method,
                        url=asset.url,
                        path=asset.path,
                        last_task_id=asset.last_task_id,
                        first_seen_at=asset.first_seen_at,
                        last_seen_at=asset.last_seen_at,
                        request_spec=asset.request_spec,
                        response_spec=asset.response_spec,
                        parameters=asset.parameters,
                    )
                    .on_conflict_do_update(
                        index_elements=["content_hash"],
                        set_={
                            "last_seen_at": asset.last_seen_at,
                            "last_task_id": asset.last_task_id,
                            "request_spec": asset.request_spec,
                            "response_spec": asset.response_spec,
                            "parameters": asset.parameters,
                        },
                    )
                    .returning(Asset.id)
                )
                result = await self.session.execute(stmt)
                asset.id = result.scalar_one()
            # After all upserts, flush to ensure IDs are committed
            await self.session.flush()

        # 2. Discoveries 생성 (이제 asset.id 접근 가능)
        if self._pending_discoveries:
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

        # 3. Commit all changes (new assets + modified existing assets + discoveries)
        await self.session.commit()

        # 4. 버퍼 초기화
        self._pending_assets.clear()
        self._pending_discoveries.clear()
        self._pending_hash_map.clear()

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
        self, spec: Optional[Union[HttpRequestData, HttpResponseData, Dict[str, Any]]]
    ) -> Optional[Union[HttpRequestData, HttpResponseData, Dict[str, Any]]]:
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
        # HTTP data parameters (TypedDict types)
        request_spec: Optional[HttpRequestData] = None,
        response_spec: Optional[HttpResponseData] = None,
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
        truncated_request = self._truncate_body(request_spec)
        truncated_response = self._truncate_body(response_spec)

        # First check pending buffer (same batch deduplication)
        existing_asset = self._pending_hash_map.get(content_hash)

        # If not in buffer, check database
        if not existing_asset:
            statement = select(Asset).where(Asset.content_hash == content_hash)
            result = await self.session.exec(statement)
            existing_asset = result.first()

            # FIX: Add DB-loaded asset to hash_map to prevent duplicate loads
            # This prevents StaleDataError when the same asset is processed multiple times
            if existing_asset:
                self._pending_hash_map[content_hash] = existing_asset

        current_time = utc_now()

        if existing_asset:
            # Update existing asset
            asset = existing_asset
            asset.last_seen_at = current_time
            asset.last_task_id = task_id

            # Update HTTP data (overwrite with latest)
            if truncated_request is not None:
                asset.request_spec = cast(Dict[str, Any], truncated_request)
            if truncated_response is not None:
                asset.response_spec = cast(Dict[str, Any], truncated_response)
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
                # HTTP data fields (truncated if needed)
                request_spec=cast(Optional[Dict[str, Any]], truncated_request),
                response_spec=cast(Optional[Dict[str, Any]], truncated_response),
                parameters=parameters,
            )

        # Buffer asset and discovery info (defer commit)
        # Only add NEW assets to _pending_assets (for session.add_all)
        # Existing DB assets are already tracked by SQLAlchemy's dirty tracking
        if not existing_asset:
            self._pending_assets.append(asset)
            self._pending_hash_map[content_hash] = asset
        self._pending_discoveries.append((task_id, asset, parent_asset_id))

        # Flush when batch size reached
        if len(self._pending_assets) >= self.BATCH_SIZE:
            await self.flush()

        return asset
