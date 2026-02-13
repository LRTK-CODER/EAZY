"""Integration tests for the smart crawler engine."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import respx

from eazy.crawler.smart_engine import SmartCrawlerEngine
from eazy.models.crawl_types import (
    ButtonInfo,
    CrawlConfig,
    EndpointInfo,
    FormData,
    PageAnalysisResult,
)


def _setup_browser(mock_cls: MagicMock, goto_map: dict[str, int]) -> None:
    """Configure BrowserManager mock.

    Args:
        mock_cls: The mock_browser_manager class mock.
        goto_map: Maps URL to HTTP status code for page.goto().

    Sets up:
    - mock_cls.return_value = async context manager returning itself
    - new_page() returns a new AsyncMock page each call
    - page.goto(url) returns AsyncMock with .status = goto_map[url]
    - page.close() is an async no-op
    """
    browser_instance = AsyncMock()
    mock_cls.return_value = browser_instance
    browser_instance.__aenter__ = AsyncMock(return_value=browser_instance)
    browser_instance.__aexit__ = AsyncMock(return_value=False)

    def _make_page():
        page = AsyncMock()

        async def _goto(url, **kwargs):
            status = goto_map.get(url, 200)
            resp = MagicMock()
            resp.status = status
            return resp

        page.goto = AsyncMock(side_effect=_goto)
        page.close = AsyncMock()
        return page

    browser_instance.new_page = AsyncMock(side_effect=lambda: _make_page())


def _setup_analyzer(
    mock_cls: MagicMock, analysis_map: dict[str, PageAnalysisResult]
) -> None:
    """Configure PageAnalyzer mock.

    Args:
        mock_cls: The mock_page_analyzer class mock.
        analysis_map: Maps base_url to PageAnalysisResult.

    Sets up:
    - PageAnalyzer(base_url=url) → instance with analyze(page)
      returning analysis_map[url]
    """

    def _make_analyzer(base_url: str):
        instance = AsyncMock()
        result = analysis_map.get(base_url)
        if result is None:
            result = PageAnalysisResult()
        instance.analyze = AsyncMock(return_value=result)
        return instance

    mock_cls.side_effect = _make_analyzer


def _setup_interceptor(
    mock_cls: MagicMock, endpoint_lists: list[list[EndpointInfo]]
) -> None:
    """Configure NetworkInterceptor mock.

    Args:
        mock_cls: The mock_network_interceptor class mock.
        endpoint_lists: Per-visit list of EndpointInfo lists.

    Sets up:
    - Each NetworkInterceptor() call returns a new mock
    - interceptor.start(page) is a no-op
    - interceptor.stop() returns the next endpoint_lists item
    """
    instances = []
    for endpoints in endpoint_lists:
        inst = MagicMock()
        inst.start = MagicMock()
        inst.stop = MagicMock(return_value=endpoints)
        instances.append(inst)
    # If more pages than endpoint_lists, extras return empty
    while len(instances) < 20:
        extra = MagicMock()
        extra.start = MagicMock()
        extra.stop = MagicMock(return_value=[])
        instances.append(extra)
    mock_cls.side_effect = instances


class TestSmartBasicCrawling:
    """Test basic crawling functionality."""

    @pytest.mark.asyncio
    @respx.mock
    @patch("eazy.crawler.smart_engine.NetworkInterceptor")
    @patch("eazy.crawler.smart_engine.PageAnalyzer")
    @patch("eazy.crawler.smart_engine.BrowserManager")
    async def test_crawl_single_page_returns_page_result(
        self, mock_browser_manager, mock_page_analyzer, mock_network_interceptor
    ):
        """Test crawling a single page returns correct PageResult."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
            enable_pattern_normalization=False,
        )
        goto_map = {"https://example.com": 200}
        analysis_map = {
            "https://example.com": PageAnalysisResult(
                title="Home", links=[], forms=[], buttons=[]
            )
        }
        endpoint_lists = [[]]

        _setup_browser(mock_browser_manager, goto_map)
        _setup_analyzer(mock_page_analyzer, analysis_map)
        _setup_interceptor(mock_network_interceptor, endpoint_lists)

        engine = SmartCrawlerEngine(config)

        # Act
        result = await engine.crawl()
        pages = result.pages

        # Assert
        assert len(pages) == 1
        assert pages[0].url == "https://example.com"
        assert pages[0].status_code == 200
        assert pages[0].title == "Home"
        assert pages[0].depth == 0
        assert pages[0].parent_url is None
        assert pages[0].error is None

    @pytest.mark.asyncio
    @respx.mock
    @patch("eazy.crawler.smart_engine.NetworkInterceptor")
    @patch("eazy.crawler.smart_engine.PageAnalyzer")
    @patch("eazy.crawler.smart_engine.BrowserManager")
    async def test_crawl_follows_links_to_next_page(
        self, mock_browser_manager, mock_page_analyzer, mock_network_interceptor
    ):
        """Test crawling follows links to next page."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
            enable_pattern_normalization=False,
        )
        goto_map = {
            "https://example.com": 200,
            "https://example.com/about": 200,
        }
        analysis_map = {
            "https://example.com": PageAnalysisResult(
                title="Home", links=["https://example.com/about"]
            ),
            "https://example.com/about": PageAnalysisResult(title="About", links=[]),
        }
        endpoint_lists = [[], []]

        _setup_browser(mock_browser_manager, goto_map)
        _setup_analyzer(mock_page_analyzer, analysis_map)
        _setup_interceptor(mock_network_interceptor, endpoint_lists)

        engine = SmartCrawlerEngine(config)

        # Act
        result = await engine.crawl()
        pages = result.pages

        # Assert
        assert len(pages) == 2
        urls = {p.url for p in pages}
        assert "https://example.com" in urls
        assert "https://example.com/about" in urls

        about_page = next(p for p in pages if "about" in p.url)
        assert about_page.depth == 1
        assert about_page.parent_url == "https://example.com"

    @pytest.mark.asyncio
    @respx.mock
    @patch("eazy.crawler.smart_engine.NetworkInterceptor")
    @patch("eazy.crawler.smart_engine.PageAnalyzer")
    @patch("eazy.crawler.smart_engine.BrowserManager")
    async def test_crawl_extracts_forms_and_buttons(
        self, mock_browser_manager, mock_page_analyzer, mock_network_interceptor
    ):
        """Test crawling extracts forms and buttons."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
            enable_pattern_normalization=False,
        )
        goto_map = {"https://example.com": 200}
        analysis_map = {
            "https://example.com": PageAnalysisResult(
                title="Form Page",
                links=[],
                forms=[
                    FormData(
                        action="https://example.com/login",
                        method="POST",
                        inputs=[{"name": "username", "type": "text"}],
                    )
                ],
                buttons=[ButtonInfo(text="Submit", type="submit")],
            )
        }
        endpoint_lists = [[]]

        _setup_browser(mock_browser_manager, goto_map)
        _setup_analyzer(mock_page_analyzer, analysis_map)
        _setup_interceptor(mock_network_interceptor, endpoint_lists)

        engine = SmartCrawlerEngine(config)

        # Act
        result = await engine.crawl()
        pages = result.pages

        # Assert
        assert len(pages[0].forms) == 1
        assert pages[0].forms[0].action == "https://example.com/login"
        assert len(pages[0].buttons) == 1
        assert pages[0].buttons[0].text == "Submit"

    @pytest.mark.asyncio
    @respx.mock
    @patch("eazy.crawler.smart_engine.NetworkInterceptor")
    @patch("eazy.crawler.smart_engine.PageAnalyzer")
    @patch("eazy.crawler.smart_engine.BrowserManager")
    async def test_crawl_captures_api_endpoints(
        self, mock_browser_manager, mock_page_analyzer, mock_network_interceptor
    ):
        """Test crawling captures API endpoints."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
            enable_pattern_normalization=False,
        )
        goto_map = {"https://example.com": 200}
        analysis_map = {
            "https://example.com": PageAnalysisResult(title="API Page", links=[])
        }
        endpoint_lists = [
            [
                EndpointInfo(
                    url="https://example.com/api/users",
                    method="GET",
                    source="fetch",
                )
            ]
        ]

        _setup_browser(mock_browser_manager, goto_map)
        _setup_analyzer(mock_page_analyzer, analysis_map)
        _setup_interceptor(mock_network_interceptor, endpoint_lists)

        engine = SmartCrawlerEngine(config)

        # Act
        result = await engine.crawl()
        pages = result.pages

        # Assert
        assert len(pages[0].api_endpoints) == 1
        assert pages[0].api_endpoints[0].url == "https://example.com/api/users"

    @pytest.mark.asyncio
    @respx.mock
    @patch("eazy.crawler.smart_engine.NetworkInterceptor")
    @patch("eazy.crawler.smart_engine.PageAnalyzer")
    @patch("eazy.crawler.smart_engine.BrowserManager")
    async def test_crawl_spa_javascript_rendered_content(
        self, mock_browser_manager, mock_page_analyzer, mock_network_interceptor
    ):
        """Test crawling SPA with JavaScript-rendered content."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
            enable_pattern_normalization=False,
        )
        goto_map = {
            "https://example.com": 200,
            "https://example.com/dashboard": 200,
        }
        analysis_map = {
            "https://example.com": PageAnalysisResult(
                title="SPA App",
                links=["https://example.com/dashboard"],
                is_spa=True,
            ),
            "https://example.com/dashboard": PageAnalysisResult(
                title="Dashboard", links=[], is_spa=True
            ),
        }
        endpoint_lists = [[], []]

        _setup_browser(mock_browser_manager, goto_map)
        _setup_analyzer(mock_page_analyzer, analysis_map)
        _setup_interceptor(mock_network_interceptor, endpoint_lists)

        engine = SmartCrawlerEngine(config)

        # Act
        result = await engine.crawl()
        pages = result.pages

        # Assert
        assert len(pages) == 2
        urls = {p.url for p in pages}
        assert "https://example.com" in urls
        assert "https://example.com/dashboard" in urls

    @pytest.mark.asyncio
    @respx.mock
    @patch("eazy.crawler.smart_engine.NetworkInterceptor")
    @patch("eazy.crawler.smart_engine.PageAnalyzer")
    @patch("eazy.crawler.smart_engine.BrowserManager")
    async def test_crawl_returns_crawl_result_with_statistics(
        self, mock_browser_manager, mock_page_analyzer, mock_network_interceptor
    ):
        """Test crawl returns CrawlResult with statistics."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
            enable_pattern_normalization=False,
        )
        goto_map = {
            "https://example.com": 200,
            "https://example.com/about": 200,
        }
        analysis_map = {
            "https://example.com": PageAnalysisResult(
                title="Home", links=["https://example.com/about"]
            ),
            "https://example.com/about": PageAnalysisResult(title="About", links=[]),
        }
        endpoint_lists = [[], []]

        _setup_browser(mock_browser_manager, goto_map)
        _setup_analyzer(mock_page_analyzer, analysis_map)
        _setup_interceptor(mock_network_interceptor, endpoint_lists)

        engine = SmartCrawlerEngine(config)

        # Act
        result = await engine.crawl()

        # Assert
        assert result.target_url == "https://example.com"
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.config == config
        assert "total_pages" in result.statistics
        assert "total_links" in result.statistics
        assert "total_forms" in result.statistics
        assert "total_endpoints" in result.statistics
        assert result.statistics["total_pages"] == 2


class TestSmartCrawlConstraints:
    """Test crawl constraint handling."""

    @pytest.mark.asyncio
    @respx.mock
    @patch("eazy.crawler.smart_engine.NetworkInterceptor")
    @patch("eazy.crawler.smart_engine.PageAnalyzer")
    @patch("eazy.crawler.smart_engine.BrowserManager")
    async def test_crawl_respects_max_depth(
        self, mock_browser_manager, mock_page_analyzer, mock_network_interceptor
    ):
        """Test crawl respects max_depth configuration."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            max_depth=0,
            respect_robots=False,
            enable_pattern_normalization=False,
        )
        goto_map = {"https://example.com": 200}
        analysis_map = {
            "https://example.com": PageAnalysisResult(
                title="Root", links=["https://example.com/deep"]
            )
        }
        endpoint_lists = [[]]

        _setup_browser(mock_browser_manager, goto_map)
        _setup_analyzer(mock_page_analyzer, analysis_map)
        _setup_interceptor(mock_network_interceptor, endpoint_lists)

        engine = SmartCrawlerEngine(config)

        # Act
        result = await engine.crawl()
        pages = result.pages

        # Assert
        assert len(pages) == 1
        assert pages[0].url == "https://example.com"

    @pytest.mark.asyncio
    @respx.mock
    @patch("eazy.crawler.smart_engine.NetworkInterceptor")
    @patch("eazy.crawler.smart_engine.PageAnalyzer")
    @patch("eazy.crawler.smart_engine.BrowserManager")
    async def test_crawl_respects_max_pages(
        self, mock_browser_manager, mock_page_analyzer, mock_network_interceptor
    ):
        """Test crawl respects max_pages configuration."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            max_pages=1,
            respect_robots=False,
            enable_pattern_normalization=False,
        )
        goto_map = {
            "https://example.com": 200,
            "https://example.com/about": 200,
        }
        analysis_map = {
            "https://example.com": PageAnalysisResult(
                title="Root", links=["https://example.com/about"]
            )
        }
        endpoint_lists = [[]]

        _setup_browser(mock_browser_manager, goto_map)
        _setup_analyzer(mock_page_analyzer, analysis_map)
        _setup_interceptor(mock_network_interceptor, endpoint_lists)

        engine = SmartCrawlerEngine(config)

        # Act
        result = await engine.crawl()
        pages = result.pages

        # Assert
        assert len(pages) == 1

    @pytest.mark.asyncio
    @respx.mock
    @patch("eazy.crawler.smart_engine.NetworkInterceptor")
    @patch("eazy.crawler.smart_engine.PageAnalyzer")
    @patch("eazy.crawler.smart_engine.BrowserManager")
    async def test_crawl_respects_robots_txt(
        self, mock_browser_manager, mock_page_analyzer, mock_network_interceptor
    ):
        """Test crawl respects robots.txt disallow rules."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=True,
            enable_pattern_normalization=False,
        )
        respx.get("https://example.com/robots.txt").mock(
            return_value=httpx.Response(200, text="User-agent: *\nDisallow: /secret\n")
        )
        goto_map = {
            "https://example.com": 200,
            "https://example.com/public": 200,
        }
        analysis_map = {
            "https://example.com": PageAnalysisResult(
                title="Root",
                links=[
                    "https://example.com/public",
                    "https://example.com/secret",
                ],
            )
        }
        endpoint_lists = [[], []]

        _setup_browser(mock_browser_manager, goto_map)
        _setup_analyzer(mock_page_analyzer, analysis_map)
        _setup_interceptor(mock_network_interceptor, endpoint_lists)

        engine = SmartCrawlerEngine(config)

        # Act
        result = await engine.crawl()
        pages = result.pages

        # Assert
        urls = {p.url for p in pages}
        assert "https://example.com/public" in urls
        assert "https://example.com/secret" not in urls

    @pytest.mark.asyncio
    @respx.mock
    @patch("eazy.crawler.smart_engine.NetworkInterceptor")
    @patch("eazy.crawler.smart_engine.PageAnalyzer")
    @patch("eazy.crawler.smart_engine.BrowserManager")
    async def test_crawl_enforces_scope(
        self, mock_browser_manager, mock_page_analyzer, mock_network_interceptor
    ):
        """Test crawl enforces same-domain scope."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
            enable_pattern_normalization=False,
        )
        goto_map = {
            "https://example.com": 200,
            "https://example.com/internal": 200,
        }
        analysis_map = {
            "https://example.com": PageAnalysisResult(
                title="Root",
                links=[
                    "https://example.com/internal",
                    "https://external.com/page",
                ],
            )
        }
        endpoint_lists = [[], []]

        _setup_browser(mock_browser_manager, goto_map)
        _setup_analyzer(mock_page_analyzer, analysis_map)
        _setup_interceptor(mock_network_interceptor, endpoint_lists)

        engine = SmartCrawlerEngine(config)

        # Act
        result = await engine.crawl()
        pages = result.pages

        # Assert
        urls = {p.url for p in pages}
        assert "https://example.com/internal" in urls
        assert "https://external.com/page" not in urls

    @pytest.mark.asyncio
    @respx.mock
    @patch("eazy.crawler.smart_engine.NetworkInterceptor")
    @patch("eazy.crawler.smart_engine.PageAnalyzer")
    @patch("eazy.crawler.smart_engine.BrowserManager")
    async def test_crawl_handles_navigation_timeout(
        self, mock_browser_manager, mock_page_analyzer, mock_network_interceptor
    ):
        """Test crawl handles navigation timeout error."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
            enable_pattern_normalization=False,
        )

        # Custom browser mock where goto raises exception
        browser_instance = AsyncMock()
        mock_browser_manager.return_value = browser_instance
        browser_instance.__aenter__ = AsyncMock(return_value=browser_instance)
        browser_instance.__aexit__ = AsyncMock(return_value=False)

        page = AsyncMock()
        page.goto = AsyncMock(side_effect=Exception("Navigation timeout"))
        page.close = AsyncMock()
        browser_instance.new_page = AsyncMock(return_value=page)

        _setup_analyzer(mock_page_analyzer, {})
        _setup_interceptor(mock_network_interceptor, [[]])

        engine = SmartCrawlerEngine(config)

        # Act
        result = await engine.crawl()
        pages = result.pages

        # Assert
        assert len(pages) == 1
        assert pages[0].error is not None
        assert "Navigation timeout" in pages[0].error
        assert pages[0].status_code == 0

    @pytest.mark.asyncio
    @respx.mock
    @patch("eazy.crawler.smart_engine.NetworkInterceptor")
    @patch("eazy.crawler.smart_engine.PageAnalyzer")
    @patch("eazy.crawler.smart_engine.BrowserManager")
    async def test_crawl_handles_page_error(
        self, mock_browser_manager, mock_page_analyzer, mock_network_interceptor
    ):
        """Test crawl handles HTTP error status codes."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
            enable_pattern_normalization=False,
        )
        goto_map = {"https://example.com": 404}
        analysis_map = {"https://example.com": PageAnalysisResult(title="", links=[])}
        endpoint_lists = [[]]

        _setup_browser(mock_browser_manager, goto_map)
        _setup_analyzer(mock_page_analyzer, analysis_map)
        _setup_interceptor(mock_network_interceptor, endpoint_lists)

        engine = SmartCrawlerEngine(config)

        # Act
        result = await engine.crawl()
        pages = result.pages

        # Assert
        assert pages[0].status_code == 404
        assert pages[0].error == "HTTP 404"

    @pytest.mark.asyncio
    @respx.mock
    @patch("eazy.crawler.smart_engine.NetworkInterceptor")
    @patch("eazy.crawler.smart_engine.PageAnalyzer")
    @patch("eazy.crawler.smart_engine.BrowserManager")
    async def test_crawl_deduplicates_with_url_pattern_normalizer(
        self, mock_browser_manager, mock_page_analyzer, mock_network_interceptor
    ):
        """Test crawl deduplicates URLs with pattern normalization."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            enable_pattern_normalization=True,
            max_samples_per_pattern=2,
            respect_robots=False,
        )
        goto_map = {
            "https://example.com": 200,
            "https://example.com/posts/1": 200,
            "https://example.com/posts/2": 200,
        }
        analysis_map = {
            "https://example.com": PageAnalysisResult(
                title="Root",
                links=[
                    "https://example.com/posts/1",
                    "https://example.com/posts/2",
                    "https://example.com/posts/3",
                ],
            ),
            "https://example.com/posts/1": PageAnalysisResult(title="Post 1", links=[]),
            "https://example.com/posts/2": PageAnalysisResult(title="Post 2", links=[]),
        }
        endpoint_lists = [[], [], []]

        _setup_browser(mock_browser_manager, goto_map)
        _setup_analyzer(mock_page_analyzer, analysis_map)
        _setup_interceptor(mock_network_interceptor, endpoint_lists)

        engine = SmartCrawlerEngine(config)

        # Act
        result = await engine.crawl()

        # Assert
        assert result.pattern_groups is not None
        assert result.pattern_groups.total_patterns_found >= 1

    @pytest.mark.asyncio
    @respx.mock
    @patch("eazy.crawler.smart_engine.NetworkInterceptor")
    @patch("eazy.crawler.smart_engine.PageAnalyzer")
    @patch("eazy.crawler.smart_engine.BrowserManager")
    async def test_crawl_excludes_urls_matching_exclude_patterns(
        self, mock_browser_manager, mock_page_analyzer, mock_network_interceptor
    ):
        """Test crawl excludes URLs matching exclude patterns."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            exclude_patterns=["*.pdf"],
            respect_robots=False,
            enable_pattern_normalization=False,
        )
        goto_map = {
            "https://example.com": 200,
            "https://example.com/page": 200,
        }
        analysis_map = {
            "https://example.com": PageAnalysisResult(
                title="Root",
                links=[
                    "https://example.com/page",
                    "https://example.com/doc.pdf",
                ],
            )
        }
        endpoint_lists = [[], []]

        _setup_browser(mock_browser_manager, goto_map)
        _setup_analyzer(mock_page_analyzer, analysis_map)
        _setup_interceptor(mock_network_interceptor, endpoint_lists)

        engine = SmartCrawlerEngine(config)

        # Act
        result = await engine.crawl()
        pages = result.pages

        # Assert
        urls = {p.url for p in pages}
        assert "https://example.com/page" in urls
        assert "https://example.com/doc.pdf" not in urls


class TestSmartCrawlKnowledgeGraph:
    """Tests for knowledge graph integration in smart crawler."""

    @pytest.mark.asyncio
    @respx.mock
    @patch("eazy.crawler.smart_engine.NetworkInterceptor")
    @patch("eazy.crawler.smart_engine.PageAnalyzer")
    @patch("eazy.crawler.smart_engine.BrowserManager")
    async def test_smart_crawl_result_includes_knowledge_graph(
        self, mock_browser_manager, mock_page_analyzer, mock_network_interceptor
    ):
        """Test smart crawl result includes a populated knowledge graph."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
            enable_pattern_normalization=False,
        )
        goto_map = {"https://example.com": 200}
        analysis_map = {
            "https://example.com": PageAnalysisResult(
                title="Home",
                links=["https://example.com/about"],
                forms=[
                    FormData(
                        action="https://example.com/login",
                        method="POST",
                        inputs=[{"name": "user", "type": "text"}],
                    )
                ],
            )
        }
        endpoint_lists = [
            [
                EndpointInfo(
                    url="https://example.com/api/data",
                    method="GET",
                    source="fetch",
                )
            ]
        ]

        _setup_browser(mock_browser_manager, goto_map)
        _setup_analyzer(mock_page_analyzer, analysis_map)
        _setup_interceptor(mock_network_interceptor, endpoint_lists)

        engine = SmartCrawlerEngine(config)

        # Act
        result = await engine.crawl()

        # Assert
        assert result.knowledge_graph is not None
        graph = result.knowledge_graph
        # PAGE node for example.com
        assert "https://example.com" in graph.nodes
        assert graph.nodes["https://example.com"].node_type.value == "page"
        # API node for /api/data
        assert "https://example.com/api/data" in graph.nodes
        assert graph.nodes["https://example.com/api/data"].node_type.value == "api"
        # Edges: hyperlink + form_action + api_call = 3
        assert len(graph.edges) == 3

    @pytest.mark.asyncio
    @respx.mock
    @patch("eazy.crawler.smart_engine.NetworkInterceptor")
    @patch("eazy.crawler.smart_engine.PageAnalyzer")
    @patch("eazy.crawler.smart_engine.BrowserManager")
    async def test_smart_crawl_end_to_end_workflow(
        self, mock_browser_manager, mock_page_analyzer, mock_network_interceptor
    ):
        """Test smart crawl → graph → JSON end-to-end workflow."""
        import json

        from eazy.crawler.graph_builder import GraphBuilder

        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            respect_robots=False,
            enable_pattern_normalization=False,
        )
        goto_map = {
            "https://example.com": 200,
            "https://example.com/about": 200,
        }
        analysis_map = {
            "https://example.com": PageAnalysisResult(
                title="Home",
                links=["https://example.com/about"],
            ),
            "https://example.com/about": PageAnalysisResult(
                title="About",
                links=[],
            ),
        }
        endpoint_lists = [[], []]

        _setup_browser(mock_browser_manager, goto_map)
        _setup_analyzer(mock_page_analyzer, analysis_map)
        _setup_interceptor(mock_network_interceptor, endpoint_lists)

        engine = SmartCrawlerEngine(config)

        # Act
        result = await engine.crawl()
        graph_json = GraphBuilder.to_json(result.knowledge_graph)

        # Assert
        parsed = json.loads(graph_json)
        assert "nodes" in parsed
        assert "edges" in parsed
        assert len(parsed["nodes"]) == 2
        assert len(parsed["edges"]) == 1  # one hyperlink edge

    @pytest.mark.asyncio
    @respx.mock
    @patch("eazy.crawler.smart_engine.NetworkInterceptor")
    @patch("eazy.crawler.smart_engine.PageAnalyzer")
    @patch("eazy.crawler.smart_engine.BrowserManager")
    async def test_smart_crawl_with_pattern_normalization(
        self, mock_browser_manager, mock_page_analyzer, mock_network_interceptor
    ):
        """Test smart crawl populates both pattern_groups and knowledge_graph."""
        # Arrange
        config = CrawlConfig(
            target_url="https://example.com",
            enable_pattern_normalization=True,
            max_samples_per_pattern=2,
            respect_robots=False,
        )
        goto_map = {
            "https://example.com": 200,
            "https://example.com/posts/1": 200,
        }
        analysis_map = {
            "https://example.com": PageAnalysisResult(
                title="Root",
                links=[
                    "https://example.com/posts/1",
                    "https://example.com/posts/2",
                ],
            ),
            "https://example.com/posts/1": PageAnalysisResult(
                title="Post 1",
                links=[],
            ),
        }
        endpoint_lists = [[], []]

        _setup_browser(mock_browser_manager, goto_map)
        _setup_analyzer(mock_page_analyzer, analysis_map)
        _setup_interceptor(mock_network_interceptor, endpoint_lists)

        engine = SmartCrawlerEngine(config)

        # Act
        result = await engine.crawl()

        # Assert
        assert result.pattern_groups is not None
        assert result.knowledge_graph is not None
        assert len(result.knowledge_graph.nodes) >= 2
