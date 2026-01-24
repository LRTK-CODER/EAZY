"""Interaction Engine Module.

동적 상호작용(클릭, 호버, 스크롤)으로 숨겨진 콘텐츠 및 API 엔드포인트를 발견합니다:
- 클릭 가능 요소 탐지 및 클릭 시뮬레이션
- 호버 이벤트 처리 (드롭다운, 툴팁)
- 무한 스크롤, lazy loading 처리
- DOM 상태 변화 추적
"""

import hashlib
import json
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from app.services.discovery.base import BaseDiscoveryModule
from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile
from app.services.discovery.modules.network_capturer import (
    GraphQLDetector,
    RequestInterceptor,
)

# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class InteractionResult:
    """상호작용 결과 정보."""

    action_type: str  # click, hover, scroll
    target_selector: str
    triggered_requests: List[Dict[str, Any]] = field(default_factory=list)
    new_elements: List[Dict[str, Any]] = field(default_factory=list)
    new_dom_content: str = ""


@dataclass
class ClickableElement:
    """클릭 가능 요소 정보."""

    selector: str
    element_type: str  # button, link, dropdown, etc.
    has_event_listener: bool = True


# ============================================================================
# ClickHandler
# ============================================================================


class ClickHandler:
    """클릭 가능 요소 탐지 및 클릭 시뮬레이션 처리."""

    def __init__(self) -> None:
        """Initialize ClickHandler."""
        self._processed_selectors: Set[str] = set()

    def analyze(self, element_data: Dict[str, Any]) -> ClickableElement:
        """클릭 가능 요소 분석.

        Args:
            element_data: 요소 데이터 딕셔너리

        Returns:
            ClickableElement 객체
        """
        return ClickableElement(
            selector=element_data.get("selector", ""),
            element_type=element_data.get("type", "unknown"),
            has_event_listener=element_data.get("has_event_listener", True),
        )

    def process_result(self, interaction_data: Dict[str, Any]) -> InteractionResult:
        """클릭 상호작용 결과 처리.

        Args:
            interaction_data: 상호작용 결과 데이터

        Returns:
            InteractionResult 객체
        """
        return InteractionResult(
            action_type=interaction_data.get("action", "click"),
            target_selector=interaction_data.get("selector", ""),
            triggered_requests=interaction_data.get("triggered_requests", []),
            new_elements=interaction_data.get("new_elements", []),
            new_dom_content=interaction_data.get("new_dom_content", ""),
        )

    def extract_endpoints(self, result: InteractionResult) -> List[Dict[str, Any]]:
        """클릭 결과에서 API 엔드포인트 추출.

        Args:
            result: InteractionResult 객체

        Returns:
            엔드포인트 정보 리스트
        """
        endpoints: List[Dict[str, Any]] = []
        for req in result.triggered_requests:
            endpoints.append(
                {
                    "url": req.get("url", ""),
                    "method": req.get("method", "GET"),
                    "trigger_element": result.target_selector,
                }
            )
        return endpoints

    def extract_links(self, result: InteractionResult) -> List[Dict[str, Any]]:
        """클릭 결과에서 발견된 링크 추출.

        Args:
            result: InteractionResult 객체

        Returns:
            링크 정보 리스트
        """
        links: List[Dict[str, Any]] = []
        for element in result.new_elements:
            if element.get("type") == "link" or element.get("href"):
                links.append(
                    {
                        "selector": element.get("selector", ""),
                        "href": element.get("href", ""),
                    }
                )
        return links


# ============================================================================
# HoverHandler
# ============================================================================


class HoverHandler:
    """호버 이벤트 처리 (드롭다운, 툴팁)."""

    def __init__(self) -> None:
        """Initialize HoverHandler."""
        self._processed_selectors: Set[str] = set()

    def process_result(self, hover_data: Dict[str, Any]) -> InteractionResult:
        """호버 상호작용 결과 처리.

        Args:
            hover_data: 호버 결과 데이터

        Returns:
            InteractionResult 객체
        """
        return InteractionResult(
            action_type=hover_data.get("action", "hover"),
            target_selector=hover_data.get("selector", ""),
            triggered_requests=hover_data.get("triggered_requests", []),
            new_elements=hover_data.get("new_elements", []),
            new_dom_content=hover_data.get("new_dom_content", ""),
        )

    def extract_links(self, result: InteractionResult) -> List[Dict[str, Any]]:
        """호버 결과에서 발견된 링크 추출.

        Args:
            result: InteractionResult 객체

        Returns:
            링크 정보 리스트
        """
        links: List[Dict[str, Any]] = []
        for element in result.new_elements:
            if element.get("type") == "link" or element.get("href"):
                links.append(
                    {
                        "selector": element.get("selector", ""),
                        "href": element.get("href", ""),
                    }
                )
        return links

    def extract_endpoints(self, result: InteractionResult) -> List[Dict[str, Any]]:
        """호버 결과에서 API 엔드포인트 추출.

        Args:
            result: InteractionResult 객체

        Returns:
            엔드포인트 정보 리스트
        """
        endpoints: List[Dict[str, Any]] = []
        for req in result.triggered_requests:
            endpoints.append(
                {
                    "url": req.get("url", ""),
                    "method": req.get("method", "GET"),
                    "trigger_element": result.target_selector,
                }
            )
        return endpoints


# ============================================================================
# ScrollHandler
# ============================================================================


class ScrollHandler:
    """무한 스크롤, lazy loading 처리."""

    # 페이지네이션 파라미터 패턴
    PAGINATION_PARAMS = ["page", "offset", "cursor", "skip", "start", "after", "before"]

    def __init__(self) -> None:
        """Initialize ScrollHandler."""
        self._processed_urls: Set[str] = set()

    def process(self, scroll_data: Dict[str, Any]) -> InteractionResult:
        """스크롤 데이터 처리.

        Args:
            scroll_data: 스크롤 데이터

        Returns:
            InteractionResult 객체
        """
        triggered_requests = scroll_data.get("scroll_triggered_requests", [])
        lazy_elements = scroll_data.get("lazy_loaded_elements", [])

        return InteractionResult(
            action_type="scroll",
            target_selector="window",
            triggered_requests=triggered_requests,
            new_elements=lazy_elements,
        )

    def extract_endpoints(self, result: InteractionResult) -> List[Dict[str, Any]]:
        """스크롤 결과에서 API 엔드포인트 추출.

        Args:
            result: InteractionResult 객체

        Returns:
            엔드포인트 정보 리스트
        """
        endpoints: List[Dict[str, Any]] = []
        for req in result.triggered_requests:
            endpoints.append(
                {
                    "url": req.get("url", ""),
                    "method": req.get("method", "GET"),
                }
            )
        return endpoints

    def detect_pagination_pattern(
        self, result: InteractionResult
    ) -> Optional[Dict[str, Any]]:
        """페이지네이션 패턴 탐지.

        Args:
            result: InteractionResult 객체

        Returns:
            패턴 정보 또는 None
        """
        if not result.triggered_requests:
            return None

        for req in result.triggered_requests:
            url = req.get("url", "")
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)

            for param in self.PAGINATION_PARAMS:
                if param in query_params:
                    return {
                        "param_name": param,
                        "values": query_params[param],
                        "base_url": self._strip_pagination_param(url, param),
                    }

        return None

    def _strip_pagination_param(self, url: str, param: str) -> str:
        """URL에서 페이지네이션 파라미터 제거.

        Args:
            url: URL 문자열
            param: 제거할 파라미터 이름

        Returns:
            파라미터가 제거된 URL
        """
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)

        if param in query_params:
            del query_params[param]

        # 재구성
        new_query = urlencode(query_params, doseq=True)
        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment,
            )
        )

    def extract_base_url(self, result: InteractionResult) -> str:
        """API 베이스 URL 추출.

        Args:
            result: InteractionResult 객체

        Returns:
            베이스 URL 문자열
        """
        if not result.triggered_requests:
            return ""

        url = result.triggered_requests[0].get("url", "")
        parsed = urlparse(url)

        # 쿼리 파라미터 제거
        return str(
            urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    "",
                    "",
                    "",
                )
            )
        )


# ============================================================================
# StateTracker
# ============================================================================


class StateTracker:
    """DOM 상태 변화 추적, 해싱."""

    def __init__(self) -> None:
        """Initialize StateTracker."""
        self._visited_hashes: Set[str] = set()
        self._state_history: List[str] = []

    def compute_hash(self, content: str) -> str:
        """DOM 상태 해시 계산.

        Args:
            content: DOM 콘텐츠 문자열

        Returns:
            해시 문자열
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def record_state(self, content: str) -> str:
        """DOM 상태 기록.

        Args:
            content: DOM 콘텐츠 문자열

        Returns:
            상태 해시
        """
        state_hash = self.compute_hash(content)
        self._visited_hashes.add(state_hash)
        self._state_history.append(state_hash)
        return state_hash

    def has_changed(self, new_content: str) -> bool:
        """DOM 상태 변화 여부 확인.

        Args:
            new_content: 새로운 DOM 콘텐츠

        Returns:
            변화 여부
        """
        new_hash = self.compute_hash(new_content)
        return new_hash not in self._visited_hashes

    def is_visited(self, content: str) -> bool:
        """이미 방문한 상태인지 확인.

        Args:
            content: DOM 콘텐츠 문자열

        Returns:
            방문 여부
        """
        content_hash = self.compute_hash(content)
        return content_hash in self._visited_hashes

    @property
    def state_count(self) -> int:
        """기록된 상태 수."""
        return len(self._state_history)

    def clear(self) -> None:
        """상태 초기화."""
        self._visited_hashes.clear()
        self._state_history.clear()


# ============================================================================
# InteractionEngineModule
# ============================================================================


class InteractionEngineModule(BaseDiscoveryModule):
    """동적 상호작용 Discovery 모듈.

    동적 상호작용(클릭, 호버, 스크롤)으로 숨겨진 콘텐츠 및
    API 엔드포인트를 발견합니다. FULL 프로필에서만 활성화됩니다.
    """

    # 최대 상호작용 횟수
    DEFAULT_MAX_INTERACTIONS = 100

    def __init__(self, max_interactions: int | None = None) -> None:
        """Initialize InteractionEngineModule.

        Args:
            max_interactions: 최대 상호작용 횟수 (기본값: 100)
        """
        self._request_interceptor = RequestInterceptor()
        self._graphql_detector = GraphQLDetector()
        self._click_handler = ClickHandler()
        self._hover_handler = HoverHandler()
        self._scroll_handler = ScrollHandler()
        self._state_tracker = StateTracker()
        self._max_interactions = max_interactions or self.DEFAULT_MAX_INTERACTIONS

    @property
    def name(self) -> str:
        """모듈 고유 이름."""
        return "interaction_engine"

    @property
    def profiles(self) -> Set[ScanProfile]:
        """지원하는 스캔 프로필 집합."""
        return {ScanProfile.FULL}

    @property
    def max_interactions(self) -> int:
        """최대 상호작용 횟수."""
        return self._max_interactions

    def filter_by_limit(
        self,
        elements: List[Dict[str, Any]],
        max_count: int | None = None,
    ) -> List[Dict[str, Any]]:
        """상호작용 횟수 제한에 따라 요소 필터링.

        이벤트 리스너가 있는 요소를 우선 처리합니다.

        Args:
            elements: 요소 리스트
            max_count: 최대 개수 (기본값: max_interactions)

        Returns:
            필터링된 요소 리스트
        """
        limit = max_count if max_count is not None else self._max_interactions

        # 이벤트 리스너 있는 요소 우선
        with_listener = [e for e in elements if e.get("has_event_listener", True)]
        without_listener = [
            e for e in elements if not e.get("has_event_listener", True)
        ]

        # 우선순위에 따라 결합
        prioritized = with_listener + without_listener

        return prioritized[:limit]

    def detect_graphql_requests(
        self, requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """요청 목록에서 GraphQL 요청 탐지.

        Args:
            requests: 요청 데이터 리스트

        Returns:
            GraphQL 요청 정보 리스트
        """
        graphql_requests: List[Dict[str, Any]] = []

        for req in requests:
            url = req.get("url", "")
            body = req.get("body", "")

            # GraphQL 엔드포인트 확인
            is_endpoint = self._graphql_detector.is_graphql_endpoint(url)

            # Body에서 GraphQL 쿼리 확인
            if body:
                try:
                    body_data = json.loads(body) if isinstance(body, str) else body
                    query = body_data.get("query", "")

                    if query:
                        # Operation 타입 추출
                        operation_type = "query"  # 기본값
                        operation_match = re.search(
                            r"(query|mutation|subscription)\s+\w*",
                            query,
                            re.IGNORECASE,
                        )
                        if operation_match:
                            operation_type = operation_match.group(1).lower()

                        graphql_requests.append(
                            {
                                "url": url,
                                "is_graphql": True,
                                "is_graphql_endpoint": is_endpoint,
                                "operation_type": operation_type,
                                "query": query,
                            }
                        )
                except (json.JSONDecodeError, TypeError, AttributeError):
                    pass

        return graphql_requests

    async def discover(
        self, context: DiscoveryContext
    ) -> AsyncIterator[DiscoveredAsset]:
        """자산 발견 수행.

        Args:
            context: Discovery 실행 컨텍스트

        Yields:
            발견된 자산
        """
        crawl_data = context.crawl_data

        # 중복 제거용 집합
        seen_urls: Set[str] = set()

        # 1. 클릭 상호작용 결과 처리
        interaction_results = crawl_data.get("interaction_results", [])
        for interaction_data in interaction_results:
            if not isinstance(interaction_data, dict):
                continue

            action = interaction_data.get("action", "")
            selector = interaction_data.get("selector", "")
            triggered_requests = interaction_data.get("triggered_requests", [])

            # 트리거된 요청 처리
            for req in triggered_requests:
                url = req.get("url", "")
                method = req.get("method", "GET")

                if not url or url in seen_urls:
                    continue

                # GraphQL 체크
                graphql_results = self.detect_graphql_requests([req])
                if graphql_results:
                    graphql_info = graphql_results[0]
                    seen_urls.add(url)
                    yield DiscoveredAsset(
                        url=url,
                        asset_type="graphql_endpoint",
                        source=self.name,
                        metadata={
                            "discovered_by": action,
                            "trigger_element": selector,
                            "method": method,
                            "operation_type": graphql_info.get("operation_type"),
                        },
                    )
                else:
                    # 일반 API 엔드포인트
                    seen_urls.add(url)

                    # 쿼리 파라미터 추출
                    parsed = urlparse(url)
                    query_params = dict(parse_qs(parsed.query))
                    # 값을 단일 값으로 변환
                    query_params_simple = {
                        k: v[0] if v else "" for k, v in query_params.items()
                    }

                    yield DiscoveredAsset(
                        url=url,
                        asset_type="api_endpoint",
                        source=self.name,
                        metadata={
                            "discovered_by": action,
                            "trigger_element": selector,
                            "method": method,
                            "query_params": query_params_simple,
                        },
                    )

        # 2. 스크롤 데이터 처리
        scroll_data = crawl_data.get("scroll_data", {})
        if isinstance(scroll_data, dict):
            scroll_requests = scroll_data.get("scroll_triggered_requests", [])
            has_infinite_scroll = scroll_data.get("has_infinite_scroll", False)

            for req in scroll_requests:
                url = req.get("url", "")
                method = req.get("method", "GET")

                if not url or url in seen_urls:
                    continue

                seen_urls.add(url)

                # 쿼리 파라미터 추출
                parsed = urlparse(url)
                query_params = dict(parse_qs(parsed.query))
                query_params_simple = {
                    k: v[0] if v else "" for k, v in query_params.items()
                }

                content_type = (
                    "infinite_scroll" if has_infinite_scroll else "lazy_loaded"
                )

                yield DiscoveredAsset(
                    url=url,
                    asset_type="api_endpoint",
                    source=self.name,
                    metadata={
                        "discovered_by": "scroll",
                        "content_type": content_type,
                        "method": method,
                        "query_params": query_params_simple,
                    },
                )

        # 3. 호버 상호작용 결과 처리 (interaction_results에 포함된 경우)
        for interaction_data in interaction_results:
            if not isinstance(interaction_data, dict):
                continue

            action = interaction_data.get("action", "")
            if action != "hover":
                continue

            selector = interaction_data.get("selector", "")
            triggered_requests = interaction_data.get("triggered_requests", [])
            new_elements = interaction_data.get("new_elements", [])

            # 트리거된 요청 처리
            for req in triggered_requests:
                url = req.get("url", "")
                method = req.get("method", "GET")

                if not url or url in seen_urls:
                    continue

                seen_urls.add(url)
                yield DiscoveredAsset(
                    url=url,
                    asset_type="api_endpoint",
                    source=self.name,
                    metadata={
                        "discovered_by": "hover",
                        "trigger_element": selector,
                        "method": method,
                    },
                )

            # 새로 발견된 링크 요소 처리
            for element in new_elements:
                href = element.get("href", "")
                if href and href not in seen_urls and href.startswith(("http", "/")):
                    seen_urls.add(href)
                    yield DiscoveredAsset(
                        url=href,
                        asset_type="dynamic_content",
                        source=self.name,
                        metadata={
                            "discovered_by": "hover",
                            "trigger_element": selector,
                            "element_selector": element.get("selector", ""),
                        },
                    )
