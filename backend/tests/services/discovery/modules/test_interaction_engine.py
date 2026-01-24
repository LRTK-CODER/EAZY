"""InteractionEngineModule 테스트.

TDD RED Phase: 테스트 먼저 작성
- 클릭 가능 요소 탐지 및 클릭 시뮬레이션
- 호버 이벤트 처리 (드롭다운, 툴팁)
- 무한 스크롤, lazy loading 처리
- DOM 상태 변화 추적
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.discovery.models import DiscoveryContext, ScanProfile
from app.services.discovery.modules.interaction_engine import (
    ClickableElement,
    ClickHandler,
    HoverHandler,
    InteractionEngineModule,
    InteractionResult,
    ScrollHandler,
    StateTracker,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_http_client() -> MagicMock:
    """Mock HTTP client for testing."""
    client = MagicMock()
    client.get = AsyncMock()
    return client


@pytest.fixture
def discovery_context(mock_http_client: MagicMock) -> DiscoveryContext:
    """Create a test discovery context with FULL profile."""
    return DiscoveryContext(
        target_url="https://example.com",
        profile=ScanProfile.FULL,
        http_client=mock_http_client,
    )


@pytest.fixture
def interaction_engine_module() -> InteractionEngineModule:
    """Create InteractionEngineModule instance."""
    return InteractionEngineModule()


@pytest.fixture
def click_handler() -> ClickHandler:
    """Create ClickHandler instance."""
    return ClickHandler()


@pytest.fixture
def hover_handler() -> HoverHandler:
    """Create HoverHandler instance."""
    return HoverHandler()


@pytest.fixture
def scroll_handler() -> ScrollHandler:
    """Create ScrollHandler instance."""
    return ScrollHandler()


@pytest.fixture
def state_tracker() -> StateTracker:
    """Create StateTracker instance."""
    return StateTracker()


def create_clickable_element(
    selector: str,
    element_type: str = "button",
    has_event_listener: bool = True,
) -> Dict[str, Any]:
    """Create a mock clickable element data."""
    return {
        "selector": selector,
        "type": element_type,
        "has_event_listener": has_event_listener,
    }


def create_interaction_result(
    action: str,
    selector: str,
    triggered_requests: List[Dict[str, Any]] | None = None,
    new_dom_content: str = "",
    new_elements: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Create a mock interaction result data."""
    return {
        "action": action,
        "selector": selector,
        "triggered_requests": triggered_requests or [],
        "new_dom_content": new_dom_content,
        "new_elements": new_elements or [],
    }


# ============================================================================
# Test 1: Click Triggers API Request
# ============================================================================


class TestClickTriggersApiRequest:
    """클릭이 API 요청을 트리거하는 경우 테스트."""

    def test_click_handler_analyzes_clickable_element(
        self,
        click_handler: ClickHandler,
    ) -> None:
        """클릭 가능 요소 분석."""
        element_data = create_clickable_element(
            selector="button#load-more",
            element_type="button",
            has_event_listener=True,
        )

        result = click_handler.analyze(element_data)

        assert isinstance(result, ClickableElement)
        assert result.selector == "button#load-more"
        assert result.element_type == "button"
        assert result.has_event_listener is True

    def test_click_handler_processes_triggered_request(
        self,
        click_handler: ClickHandler,
    ) -> None:
        """클릭으로 트리거된 요청 처리."""
        interaction_data = create_interaction_result(
            action="click",
            selector="button#load-more",
            triggered_requests=[
                {"url": "https://api.example.com/items?page=2", "method": "GET"}
            ],
        )

        result = click_handler.process_result(interaction_data)

        assert isinstance(result, InteractionResult)
        assert result.action_type == "click"
        assert result.target_selector == "button#load-more"
        assert len(result.triggered_requests) == 1
        assert (
            result.triggered_requests[0]["url"]
            == "https://api.example.com/items?page=2"
        )

    def test_click_handler_extracts_api_endpoint(
        self,
        click_handler: ClickHandler,
    ) -> None:
        """클릭 결과에서 API 엔드포인트 추출."""
        interaction_data = create_interaction_result(
            action="click",
            selector="button.submit",
            triggered_requests=[
                {"url": "https://api.example.com/users", "method": "POST"},
                {"url": "https://api.example.com/audit", "method": "POST"},
            ],
        )

        result = click_handler.process_result(interaction_data)
        endpoints = click_handler.extract_endpoints(result)

        assert len(endpoints) == 2
        assert any(ep["url"] == "https://api.example.com/users" for ep in endpoints)
        assert any(ep["method"] == "POST" for ep in endpoints)


# ============================================================================
# Test 2: Click Reveals Hidden Content
# ============================================================================


class TestClickRevealsHiddenContent:
    """클릭이 숨겨진 콘텐츠를 표시하는 경우 테스트."""

    def test_click_handler_detects_new_dom_content(
        self,
        click_handler: ClickHandler,
    ) -> None:
        """클릭 후 새로운 DOM 콘텐츠 탐지."""
        interaction_data = create_interaction_result(
            action="click",
            selector="button#show-details",
            triggered_requests=[],
            new_dom_content='<div class="details">Hidden content revealed</div>',
        )

        result = click_handler.process_result(interaction_data)

        assert result.new_elements is not None or result.action_type == "click"
        # New DOM content should be tracked

    def test_click_handler_tracks_new_elements(
        self,
        click_handler: ClickHandler,
    ) -> None:
        """클릭 후 새로 나타난 요소 추적."""
        interaction_data = create_interaction_result(
            action="click",
            selector="button#expand",
            triggered_requests=[],
            new_dom_content="",
            new_elements=[
                {"selector": "div.expanded-panel", "type": "panel"},
                {"selector": "a.hidden-link", "type": "link"},
            ],
        )

        result = click_handler.process_result(interaction_data)

        assert len(result.new_elements) == 2

    def test_click_handler_identifies_dynamic_links(
        self,
        click_handler: ClickHandler,
    ) -> None:
        """클릭으로 나타난 동적 링크 식별."""
        interaction_data = create_interaction_result(
            action="click",
            selector="button#load-nav",
            triggered_requests=[],
            new_elements=[
                {
                    "selector": "a.nav-item[href='/admin']",
                    "type": "link",
                    "href": "/admin",
                },
                {
                    "selector": "a.nav-item[href='/settings']",
                    "type": "link",
                    "href": "/settings",
                },
            ],
        )

        result = click_handler.process_result(interaction_data)
        links = click_handler.extract_links(result)

        assert len(links) >= 2


# ============================================================================
# Test 3: Hover Shows Dropdown Menu
# ============================================================================


class TestHoverShowsDropdownMenu:
    """호버가 드롭다운 메뉴를 표시하는 경우 테스트."""

    def test_hover_handler_processes_dropdown(
        self,
        hover_handler: HoverHandler,
    ) -> None:
        """드롭다운 메뉴 호버 처리."""
        hover_data = {
            "action": "hover",
            "selector": ".nav-dropdown",
            "triggered_requests": [],
            "new_elements": [
                {"selector": ".dropdown-item[href='/profile']", "type": "link"},
                {"selector": ".dropdown-item[href='/logout']", "type": "link"},
            ],
        }

        result = hover_handler.process_result(hover_data)

        assert isinstance(result, InteractionResult)
        assert result.action_type == "hover"
        assert len(result.new_elements) == 2

    def test_hover_handler_extracts_dropdown_links(
        self,
        hover_handler: HoverHandler,
    ) -> None:
        """드롭다운에서 링크 추출."""
        hover_data = {
            "action": "hover",
            "selector": ".user-menu",
            "triggered_requests": [],
            "new_elements": [
                {"selector": "a.menu-item", "type": "link", "href": "/dashboard"},
                {"selector": "a.menu-item", "type": "link", "href": "/api/logout"},
            ],
        }

        result = hover_handler.process_result(hover_data)
        links = hover_handler.extract_links(result)

        assert len(links) >= 1

    def test_hover_handler_detects_api_trigger(
        self,
        hover_handler: HoverHandler,
    ) -> None:
        """호버로 트리거된 API 요청 탐지."""
        hover_data = {
            "action": "hover",
            "selector": ".user-avatar",
            "triggered_requests": [
                {"url": "https://api.example.com/user/preview", "method": "GET"}
            ],
            "new_elements": [],
        }

        result = hover_handler.process_result(hover_data)

        assert len(result.triggered_requests) == 1
        assert (
            result.triggered_requests[0]["url"]
            == "https://api.example.com/user/preview"
        )


# ============================================================================
# Test 4: Hover Reveals Tooltip Links
# ============================================================================


class TestHoverRevealsTooltipLinks:
    """호버가 툴팁 링크를 표시하는 경우 테스트."""

    def test_hover_handler_processes_tooltip(
        self,
        hover_handler: HoverHandler,
    ) -> None:
        """툴팁 호버 처리."""
        hover_data = {
            "action": "hover",
            "selector": ".info-icon",
            "triggered_requests": [],
            "new_elements": [
                {"selector": ".tooltip-content a", "type": "link", "href": "/help"},
            ],
        }

        result = hover_handler.process_result(hover_data)

        assert result.action_type == "hover"
        assert len(result.new_elements) >= 1

    def test_hover_handler_identifies_tooltip_type(
        self,
        hover_handler: HoverHandler,
    ) -> None:
        """툴팁 유형 식별."""
        hover_data = {
            "action": "hover",
            "selector": "[data-tooltip]",
            "triggered_requests": [
                {"url": "https://api.example.com/tooltip/content", "method": "GET"}
            ],
            "new_elements": [],
            "tooltip_type": "dynamic",
        }

        result = hover_handler.process_result(hover_data)

        # Should identify that tooltip loaded content dynamically
        assert len(result.triggered_requests) > 0


# ============================================================================
# Test 5: Scroll Triggers Lazy Loading
# ============================================================================


class TestScrollTriggersLazyLoading:
    """스크롤이 lazy loading을 트리거하는 경우 테스트."""

    def test_scroll_handler_detects_lazy_load(
        self,
        scroll_handler: ScrollHandler,
    ) -> None:
        """Lazy loading 요청 탐지."""
        scroll_data = {
            "has_infinite_scroll": False,
            "scroll_triggered_requests": [
                {"url": "https://api.example.com/images?lazy=true", "method": "GET"}
            ],
            "lazy_loaded_elements": [
                {"selector": "img.lazy", "type": "image"},
            ],
        }

        result = scroll_handler.process(scroll_data)

        assert isinstance(result, InteractionResult)
        assert result.action_type == "scroll"
        assert len(result.triggered_requests) == 1

    def test_scroll_handler_tracks_loaded_images(
        self,
        scroll_handler: ScrollHandler,
    ) -> None:
        """스크롤로 로드된 이미지 추적."""
        scroll_data = {
            "has_infinite_scroll": False,
            "scroll_triggered_requests": [
                {"url": "https://cdn.example.com/image1.jpg", "method": "GET"},
                {"url": "https://cdn.example.com/image2.jpg", "method": "GET"},
            ],
            "lazy_loaded_elements": [],
        }

        result = scroll_handler.process(scroll_data)
        endpoints = scroll_handler.extract_endpoints(result)

        assert len(endpoints) >= 2


# ============================================================================
# Test 6: Scroll Detects Infinite Scroll
# ============================================================================


class TestScrollDetectsInfiniteScroll:
    """스크롤이 무한 스크롤을 탐지하는 경우 테스트."""

    def test_scroll_handler_detects_infinite_scroll(
        self,
        scroll_handler: ScrollHandler,
    ) -> None:
        """무한 스크롤 패턴 탐지."""
        scroll_data = {
            "has_infinite_scroll": True,
            "scroll_triggered_requests": [
                {"url": "https://api.example.com/feed?offset=20", "method": "GET"},
                {"url": "https://api.example.com/feed?offset=40", "method": "GET"},
            ],
            "lazy_loaded_elements": [],
        }

        result = scroll_handler.process(scroll_data)

        assert result.action_type == "scroll"
        assert len(result.triggered_requests) == 2

    def test_scroll_handler_extracts_pagination_pattern(
        self,
        scroll_handler: ScrollHandler,
    ) -> None:
        """페이지네이션 패턴 추출."""
        scroll_data = {
            "has_infinite_scroll": True,
            "scroll_triggered_requests": [
                {"url": "https://api.example.com/items?page=2", "method": "GET"},
                {"url": "https://api.example.com/items?page=3", "method": "GET"},
            ],
            "lazy_loaded_elements": [],
        }

        result = scroll_handler.process(scroll_data)
        pattern = scroll_handler.detect_pagination_pattern(result)

        assert pattern is not None
        assert "page" in pattern.get("param_name", "") or "page" in str(pattern)

    def test_scroll_handler_identifies_api_base(
        self,
        scroll_handler: ScrollHandler,
    ) -> None:
        """API 베이스 URL 식별."""
        scroll_data = {
            "has_infinite_scroll": True,
            "scroll_triggered_requests": [
                {
                    "url": "https://api.example.com/v1/posts?cursor=abc123",
                    "method": "GET",
                },
            ],
            "lazy_loaded_elements": [],
        }

        result = scroll_handler.process(scroll_data)
        base_url = scroll_handler.extract_base_url(result)

        assert base_url == "https://api.example.com/v1/posts"


# ============================================================================
# Test 7: State Change Detection
# ============================================================================


class TestStateChangeDetection:
    """DOM 상태 변화 탐지 테스트."""

    def test_state_tracker_computes_hash(
        self,
        state_tracker: StateTracker,
    ) -> None:
        """DOM 상태 해시 계산."""
        dom_content = "<html><body><div>Content</div></body></html>"

        hash_value = state_tracker.compute_hash(dom_content)

        assert hash_value is not None
        assert len(hash_value) > 0

    def test_state_tracker_detects_change(
        self,
        state_tracker: StateTracker,
    ) -> None:
        """DOM 상태 변화 탐지."""
        dom_before = "<html><body><div>Before</div></body></html>"
        dom_after = "<html><body><div>After</div><div>New element</div></body></html>"

        state_tracker.record_state(dom_before)
        changed = state_tracker.has_changed(dom_after)

        assert changed is True

    def test_state_tracker_no_change_same_content(
        self,
        state_tracker: StateTracker,
    ) -> None:
        """동일한 콘텐츠는 변화 없음 판정."""
        dom_content = "<html><body><div>Same content</div></body></html>"

        state_tracker.record_state(dom_content)
        changed = state_tracker.has_changed(dom_content)

        assert changed is False

    def test_state_tracker_tracks_multiple_states(
        self,
        state_tracker: StateTracker,
    ) -> None:
        """여러 상태 추적."""
        states = [
            "<div>State 1</div>",
            "<div>State 2</div>",
            "<div>State 3</div>",
        ]

        for state in states:
            state_tracker.record_state(state)

        assert state_tracker.state_count >= 3


# ============================================================================
# Test 8: Loop Prevention
# ============================================================================


class TestLoopPrevention:
    """무한 루프 방지 테스트."""

    def test_state_tracker_prevents_revisit(
        self,
        state_tracker: StateTracker,
    ) -> None:
        """이미 방문한 상태 재방문 방지."""
        dom_state = "<div>Already visited</div>"

        state_tracker.record_state(dom_state)
        is_visited = state_tracker.is_visited(dom_state)

        assert is_visited is True

    def test_state_tracker_new_state_not_visited(
        self,
        state_tracker: StateTracker,
    ) -> None:
        """새로운 상태는 미방문 상태."""
        state_tracker.record_state("<div>State A</div>")
        is_visited = state_tracker.is_visited("<div>State B</div>")

        assert is_visited is False

    def test_click_handler_skips_visited_states(
        self,
        click_handler: ClickHandler,
        state_tracker: StateTracker,
    ) -> None:
        """방문한 상태로 가는 클릭 스킵."""
        state_tracker.record_state("<div>Visited state</div>")

        interaction_data = create_interaction_result(
            action="click",
            selector="button#back",
            triggered_requests=[],
            new_dom_content="<div>Visited state</div>",
        )

        _result = click_handler.process_result(interaction_data)
        should_skip = state_tracker.is_visited(
            interaction_data.get("new_dom_content", "")
        )

        assert _result is not None
        assert should_skip is True


# ============================================================================
# Test 9: Max Interaction Limit
# ============================================================================


class TestMaxInteractionLimit:
    """최대 상호작용 횟수 제한 테스트."""

    def test_interaction_engine_has_max_limit(
        self,
        interaction_engine_module: InteractionEngineModule,
    ) -> None:
        """최대 상호작용 횟수 설정 확인."""
        assert hasattr(interaction_engine_module, "max_interactions")
        assert interaction_engine_module.max_interactions > 0

    def test_interaction_engine_respects_limit(
        self,
        interaction_engine_module: InteractionEngineModule,
    ) -> None:
        """최대 상호작용 횟수 준수."""
        # Create many clickable elements
        elements = [
            create_clickable_element(f"button#btn-{i}", "button", True)
            for i in range(200)
        ]

        processed = interaction_engine_module.filter_by_limit(elements)

        assert len(processed) <= interaction_engine_module.max_interactions

    def test_interaction_engine_prioritizes_elements(
        self,
        interaction_engine_module: InteractionEngineModule,
    ) -> None:
        """중요한 요소 우선 처리."""
        elements = [
            create_clickable_element("button#load-more", "button", True),
            create_clickable_element("a.pagination", "link", True),
            create_clickable_element(
                "div.decoration", "div", False
            ),  # No event listener
        ]

        processed = interaction_engine_module.filter_by_limit(elements, max_count=2)

        # Should prioritize elements with event listeners
        assert len(processed) == 2
        assert all(e.get("has_event_listener", True) for e in processed)


# ============================================================================
# Test 10: GraphQL Detection on Interaction
# ============================================================================


class TestGraphQLDetectionOnInteraction:
    """상호작용 중 GraphQL 탐지 테스트."""

    def test_interaction_engine_detects_graphql(
        self,
        interaction_engine_module: InteractionEngineModule,
    ) -> None:
        """상호작용으로 트리거된 GraphQL 요청 탐지."""
        interaction_data = create_interaction_result(
            action="click",
            selector="button#fetch-data",
            triggered_requests=[
                {
                    "url": "https://api.example.com/graphql",
                    "method": "POST",
                    "body": '{"query": "query GetUser { user { id name } }"}',
                }
            ],
        )

        graphql_requests = interaction_engine_module.detect_graphql_requests(
            interaction_data["triggered_requests"]
        )

        assert len(graphql_requests) == 1
        assert graphql_requests[0]["is_graphql"] is True

    def test_interaction_engine_extracts_graphql_operation(
        self,
        interaction_engine_module: InteractionEngineModule,
    ) -> None:
        """GraphQL operation 정보 추출."""
        requests = [
            {
                "url": "https://api.example.com/graphql",
                "method": "POST",
                "body": '{"query": "mutation CreateItem { createItem(name: \\"Test\\") { id } }"}',
            }
        ]

        graphql_requests = interaction_engine_module.detect_graphql_requests(requests)

        assert len(graphql_requests) == 1
        assert graphql_requests[0]["operation_type"] == "mutation"


# ============================================================================
# Test 11: Module Properties
# ============================================================================


class TestModuleProperties:
    """모듈 속성 테스트."""

    def test_module_name(
        self,
        interaction_engine_module: InteractionEngineModule,
    ) -> None:
        """모듈 이름 확인."""
        assert interaction_engine_module.name == "interaction_engine"

    def test_module_profiles(
        self,
        interaction_engine_module: InteractionEngineModule,
    ) -> None:
        """모듈 프로필 확인."""
        assert ScanProfile.FULL in interaction_engine_module.profiles
        # FULL profile only - interaction engine is heavy
        assert ScanProfile.QUICK not in interaction_engine_module.profiles
        assert ScanProfile.STANDARD not in interaction_engine_module.profiles

    def test_module_is_active_for_full_profile(
        self,
        interaction_engine_module: InteractionEngineModule,
    ) -> None:
        """FULL 프로필에서 활성화 확인."""
        assert interaction_engine_module.is_active_for(ScanProfile.FULL) is True
        assert interaction_engine_module.is_active_for(ScanProfile.STANDARD) is False
        assert interaction_engine_module.is_active_for(ScanProfile.QUICK) is False


# ============================================================================
# Test 12: Discover Yields Assets
# ============================================================================


class TestDiscoverYieldsAssets:
    """discover 메서드 자산 생성 테스트."""

    @pytest.mark.asyncio
    async def test_discover_yields_api_endpoint_assets(
        self,
        interaction_engine_module: InteractionEngineModule,
        mock_http_client: MagicMock,
    ) -> None:
        """API 엔드포인트 DiscoveredAsset 생성."""
        crawl_data = {
            "clickable_elements": [
                {"selector": "button#load-more", "type": "button"},
            ],
            "interaction_results": [
                {
                    "action": "click",
                    "selector": "button#load-more",
                    "triggered_requests": [
                        {"url": "https://api.example.com/items?page=2", "method": "GET"}
                    ],
                    "new_dom_content": "",
                }
            ],
            "scroll_data": {
                "has_infinite_scroll": False,
                "scroll_triggered_requests": [],
            },
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.FULL,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in interaction_engine_module.discover(context)]

        assert len(assets) > 0
        api_assets = [a for a in assets if a.asset_type == "api_endpoint"]
        assert len(api_assets) > 0

        # Check asset properties
        api_asset = api_assets[0]
        assert api_asset.source == "interaction_engine"
        assert "api.example.com" in api_asset.url
        assert api_asset.metadata.get("discovered_by") == "click"

    @pytest.mark.asyncio
    async def test_discover_yields_dynamic_content_assets(
        self,
        interaction_engine_module: InteractionEngineModule,
        mock_http_client: MagicMock,
    ) -> None:
        """동적 콘텐츠 DiscoveredAsset 생성."""
        crawl_data = {
            "clickable_elements": [],
            "interaction_results": [],
            "scroll_data": {
                "has_infinite_scroll": True,
                "scroll_triggered_requests": [
                    {"url": "https://api.example.com/feed?offset=20", "method": "GET"}
                ],
            },
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.FULL,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in interaction_engine_module.discover(context)]

        assert len(assets) > 0
        # Should have api_endpoint from scroll
        scroll_assets = [
            a for a in assets if a.metadata.get("discovered_by") == "scroll"
        ]
        assert len(scroll_assets) > 0

    @pytest.mark.asyncio
    async def test_discover_handles_empty_crawl_data(
        self,
        interaction_engine_module: InteractionEngineModule,
        mock_http_client: MagicMock,
    ) -> None:
        """빈 crawl_data 처리."""
        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.FULL,
            http_client=mock_http_client,
            crawl_data={},
        )

        assets = [asset async for asset in interaction_engine_module.discover(context)]

        # Should handle gracefully without errors
        assert isinstance(assets, list)

    @pytest.mark.asyncio
    async def test_discover_deduplicates_assets(
        self,
        interaction_engine_module: InteractionEngineModule,
        mock_http_client: MagicMock,
    ) -> None:
        """중복 자산 제거."""
        crawl_data = {
            "clickable_elements": [],
            "interaction_results": [
                {
                    "action": "click",
                    "selector": "button#btn1",
                    "triggered_requests": [
                        {"url": "https://api.example.com/data", "method": "GET"}
                    ],
                    "new_dom_content": "",
                },
                {
                    "action": "click",
                    "selector": "button#btn2",
                    "triggered_requests": [
                        {
                            "url": "https://api.example.com/data",
                            "method": "GET",
                        }  # Duplicate
                    ],
                    "new_dom_content": "",
                },
            ],
            "scroll_data": {
                "has_infinite_scroll": False,
                "scroll_triggered_requests": [],
            },
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.FULL,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in interaction_engine_module.discover(context)]

        # Should deduplicate
        api_assets = [a for a in assets if a.asset_type == "api_endpoint"]
        urls = [a.url for a in api_assets]
        assert len(urls) == len(set(urls))

    @pytest.mark.asyncio
    async def test_discover_includes_metadata(
        self,
        interaction_engine_module: InteractionEngineModule,
        mock_http_client: MagicMock,
    ) -> None:
        """메타데이터 포함 확인."""
        crawl_data = {
            "clickable_elements": [],
            "interaction_results": [
                {
                    "action": "click",
                    "selector": "button#load-more",
                    "triggered_requests": [
                        {
                            "url": "https://api.example.com/items?page=2&limit=10",
                            "method": "GET",
                        }
                    ],
                    "new_dom_content": "",
                }
            ],
            "scroll_data": {
                "has_infinite_scroll": False,
                "scroll_triggered_requests": [],
            },
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.FULL,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in interaction_engine_module.discover(context)]

        api_assets = [a for a in assets if a.asset_type == "api_endpoint"]
        assert len(api_assets) > 0

        asset = api_assets[0]
        assert "discovered_by" in asset.metadata
        assert "trigger_element" in asset.metadata
        assert "method" in asset.metadata

    @pytest.mark.asyncio
    async def test_discover_graphql_from_interaction(
        self,
        interaction_engine_module: InteractionEngineModule,
        mock_http_client: MagicMock,
    ) -> None:
        """상호작용으로 발견된 GraphQL 엔드포인트."""
        crawl_data = {
            "clickable_elements": [],
            "interaction_results": [
                {
                    "action": "click",
                    "selector": "button#fetch-users",
                    "triggered_requests": [
                        {
                            "url": "https://api.example.com/graphql",
                            "method": "POST",
                            "body": '{"query": "query GetUsers { users { id } }"}',
                        }
                    ],
                    "new_dom_content": "",
                }
            ],
            "scroll_data": {
                "has_infinite_scroll": False,
                "scroll_triggered_requests": [],
            },
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.FULL,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in interaction_engine_module.discover(context)]

        graphql_assets = [a for a in assets if a.asset_type == "graphql_endpoint"]
        assert len(graphql_assets) > 0
        assert graphql_assets[0].metadata.get("operation_type") == "query"
