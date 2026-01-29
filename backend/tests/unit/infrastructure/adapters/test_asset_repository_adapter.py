"""AssetRepositoryAdapter 테스트."""

from unittest.mock import AsyncMock

import pytest

from app.infrastructure.adapters.asset_repository_adapter import AssetRepositoryAdapter


class MockDiscoveredAsset:
    """테스트용 DiscoveredAsset Mock."""

    def __init__(self, url: str, asset_type: str, source: str, metadata=None):
        self.url = url
        self.asset_type = asset_type
        self.source = source
        self.metadata = metadata or {}


class MockAssetService:
    """테스트용 AssetService Mock."""

    def __init__(self):
        self.process_asset = AsyncMock()


class MockTarget:
    """테스트용 Target Mock."""

    def __init__(self, id: int):
        self.id = id


class MockDataTransformer:
    """테스트용 DataTransformer Mock."""

    def map_source(self, source: str) -> str:
        return source.upper()

    def map_type(self, asset_type: str) -> str:
        return asset_type.upper()


@pytest.mark.asyncio
async def test_save_batch_success():
    """배치 저장이 성공적으로 수행되는지 테스트."""
    mock_service = MockAssetService()
    mock_target = MockTarget(id=1)
    mock_transformer = MockDataTransformer()

    adapter = AssetRepositoryAdapter(
        asset_service=mock_service,
        target=mock_target,
        transformer=mock_transformer,
    )

    assets = [
        MockDiscoveredAsset(
            url="http://example.com/page1",
            asset_type="html",
            source="http",
            metadata={"method": "GET"},
        ),
        MockDiscoveredAsset(
            url="http://example.com/page2",
            asset_type="html",
            source="http",
            metadata={"method": "POST"},
        ),
    ]

    saved_count = await adapter.save_batch(assets, task_id=100)

    assert saved_count == 2
    assert mock_service.process_asset.call_count == 2


@pytest.mark.asyncio
async def test_save_batch_propagates_error():
    """배치 저장 중 에러가 전파되는지 테스트."""
    mock_service = MockAssetService()
    mock_service.process_asset.side_effect = ValueError("Integrity error")
    mock_target = MockTarget(id=1)
    mock_transformer = MockDataTransformer()

    adapter = AssetRepositoryAdapter(
        asset_service=mock_service,
        target=mock_target,
        transformer=mock_transformer,
    )

    assets = [
        MockDiscoveredAsset(
            url="http://example.com/page1",
            asset_type="html",
            source="http",
        ),
    ]

    with pytest.raises(ValueError, match="Integrity error"):
        await adapter.save_batch(assets, task_id=100)


@pytest.mark.asyncio
async def test_save_individual_success():
    """개별 저장이 성공하는지 테스트."""
    mock_service = MockAssetService()
    mock_target = MockTarget(id=1)
    mock_transformer = MockDataTransformer()

    adapter = AssetRepositoryAdapter(
        asset_service=mock_service,
        target=mock_target,
        transformer=mock_transformer,
    )

    asset = MockDiscoveredAsset(
        url="http://example.com/page1",
        asset_type="html",
        source="http",
        metadata={"method": "GET"},
    )

    result = await adapter.save_individual(asset, task_id=100)

    assert result is True
    mock_service.process_asset.assert_called_once()


@pytest.mark.asyncio
async def test_save_individual_silences_error():
    """개별 저장 중 에러를 무시하는지 테스트."""
    mock_service = MockAssetService()
    mock_service.process_asset.side_effect = ValueError("Integrity error")
    mock_target = MockTarget(id=1)
    mock_transformer = MockDataTransformer()

    adapter = AssetRepositoryAdapter(
        asset_service=mock_service,
        target=mock_target,
        transformer=mock_transformer,
    )

    asset = MockDiscoveredAsset(
        url="http://example.com/page1",
        asset_type="html",
        source="http",
    )

    result = await adapter.save_individual(asset, task_id=100)

    assert result is False
    mock_service.process_asset.assert_called_once()


@pytest.mark.asyncio
async def test_save_batch_with_default_method():
    """metadata.method가 없을 때 기본값 GET을 사용하는지 테스트."""
    mock_service = MockAssetService()
    mock_target = MockTarget(id=1)
    mock_transformer = MockDataTransformer()

    adapter = AssetRepositoryAdapter(
        asset_service=mock_service,
        target=mock_target,
        transformer=mock_transformer,
    )

    # metadata 없는 asset
    asset = MockDiscoveredAsset(
        url="http://example.com/page1",
        asset_type="html",
        source="http",
    )
    # metadata에 method 키가 없음
    asset.metadata = {}

    saved_count = await adapter.save_batch([asset], task_id=100)

    assert saved_count == 1
    call_args = mock_service.process_asset.call_args
    assert call_args.kwargs["method"] == "GET"


@pytest.mark.asyncio
async def test_save_batch_with_crawler_links():
    """crawler_links도 함께 저장되는지 테스트."""
    mock_service = MockAssetService()
    mock_target = MockTarget(id=1)
    mock_transformer = MockDataTransformer()

    adapter = AssetRepositoryAdapter(
        asset_service=mock_service,
        target=mock_target,
        transformer=mock_transformer,
    )

    assets = []  # No discovered assets
    crawler_links = ["http://example.com/link1", "http://example.com/link2"]
    http_data = {
        "http://example.com/link1": {
            "request": {"method": "GET"},
            "response": {"status": 200},
        },
        "http://example.com/link2": {
            "request": {"method": "POST"},
            "response": {"status": 200},
        },
    }

    saved_count = await adapter.save_batch(
        assets, task_id=100, crawler_links=crawler_links, http_data=http_data
    )

    assert saved_count == 2
    assert mock_service.process_asset.call_count == 2
