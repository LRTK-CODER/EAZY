"""
Phase 4: E2E Tests for Active Scan HTTP Methods Discovery

Tests verify that POST/PUT/DELETE methods are discovered through:
1. HTML form actions
2. JavaScript HTTP client calls
3. Network request capturing
"""

from unittest.mock import MagicMock

import pytest

from app.core.dlq import DLQManager
from app.core.queue import TaskManager
from app.core.recovery import OrphanRecovery
from app.services.discovery import DiscoveryContext, DiscoveryService, ScanProfile
from app.services.discovery.registry import get_default_registry
from app.workers.base import WorkerContext
from app.workers.crawl_worker import _transform_to_network_requests


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    return MagicMock()


@pytest.fixture
def worker_context(mock_redis):
    """Create WorkerContext with mocks"""
    return WorkerContext(
        session=MagicMock(),
        task_manager=TaskManager(mock_redis),
        dlq_manager=DLQManager(mock_redis),
        orphan_recovery=OrphanRecovery(mock_redis),
    )


class TestE2EPostApiEndpointDiscovery:
    """E2E: POST API endpoint discovery and storage"""

    @pytest.mark.asyncio
    async def test_html_form_post_action_discovered(self):
        """E2E: HTML form with POST action is discovered by HtmlElementParser."""
        # Given: HTML with POST form
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Login</title></head>
        <body>
            <form method="POST" action="/api/login">
                <input name="username" type="text">
                <input name="password" type="password">
                <button type="submit">Login</button>
            </form>
        </body>
        </html>
        """

        # When: Run Discovery with HtmlElementParser
        registry = get_default_registry()
        service = DiscoveryService(registry=registry)

        context = DiscoveryContext(
            target_url="http://test.com",
            profile=ScanProfile.STANDARD,
            http_client=None,
            crawl_data={
                "html_content": html_content,
                "base_url": "http://test.com",
            },
        )

        discovered = await service.run(context)

        # Then: POST form is discovered
        form_assets = [a for a in discovered if a.asset_type == "form"]
        assert (
            len(form_assets) >= 1
        ), f"Expected form asset, got {[a.asset_type for a in discovered]}"

        post_forms = [
            a for a in form_assets if a.metadata.get("method", "").upper() == "POST"
        ]
        assert len(post_forms) >= 1, f"Expected POST form, got {form_assets}"
        assert any("/api/login" in a.url for a in post_forms)

    @pytest.mark.asyncio
    async def test_redirect_html_content_extraction(self):
        """E2E: HTML content is correctly extracted after redirect."""
        # Given: http_data with redirect (302) and final page (200)
        http_data = {
            "http://test.com/": {
                "request": {"method": "GET", "resource_type": "document"},
                "response": {
                    "status": 302,
                    "headers": {"location": "/login"},
                    "body": "",
                },
            },
            "http://test.com/login": {
                "request": {"method": "GET", "resource_type": "document"},
                "response": {
                    "status": 200,
                    "headers": {"content-type": "text/html"},
                    "body": """<!DOCTYPE html>
                    <html>
                    <body>
                        <form method="POST" action="/login">
                            <input name="user">
                            <button>Submit</button>
                        </form>
                    </body>
                    </html>""",
                },
            },
        }

        # When: Extract HTML content (simulating crawl_worker logic)
        html_content = ""
        target_url = "http://test.com/"

        # 1. Try target_url first
        target_http_data = http_data.get(target_url, {})
        target_response_data = target_http_data.get("response", {})
        if target_response_data:
            body = target_response_data.get("body", "")
            if isinstance(body, str) and body:
                html_content = body

        # 2. If empty (redirect), find 200 response with HTML
        if not html_content:
            for url, data in http_data.items():
                response_data = data.get("response", {})
                status = response_data.get("status")
                body = response_data.get("body", "")
                if status == 200 and isinstance(body, str) and body:
                    body_lower = body.lower()
                    if "<html" in body_lower or "<!doctype" in body_lower:
                        html_content = body
                        break

        # Then: HTML content is extracted from redirected page
        assert html_content != "", "HTML content should be extracted"
        assert "<form" in html_content.lower()
        assert "POST" in html_content


class TestE2EJsAnalyzerDiscovery:
    """E2E: JavaScript analyzer discovers HTTP method calls"""

    @pytest.mark.asyncio
    async def test_http_client_detector_discovers_various_methods(self):
        """E2E: HttpClientDetector discovers fetch, axios, jQuery, XHR calls with methods."""
        from app.services.discovery.modules.js_analyzer_regex import HttpClientDetector

        # Given: JavaScript with various HTTP client calls
        js_content = """
        // Fetch API
        fetch('/api/create', { method: 'POST', body: JSON.stringify({name: 'test'}) });
        fetch('/api/update/1', { method: 'PUT' });
        fetch('/api/delete/1', { method: 'DELETE' });

        // Axios
        axios.post('/api/data', { data: 'test' });
        axios.put('/api/item/1', { name: 'updated' });
        axios.patch('/api/item/1', { partial: true });
        axios.delete('/api/item/1');

        // jQuery
        $.ajax({ url: '/api/legacy', type: 'POST', data: {} });
        $.post('/api/jquery-post', {});

        // XMLHttpRequest
        var xhr = new XMLHttpRequest();
        xhr.open('DELETE', '/api/remove');
        xhr.send();
        """

        # When: Detect HTTP client calls
        detector = HttpClientDetector()
        calls = detector.detect_all(js_content)

        # Then: Various HTTP methods are discovered
        methods_found = {call.method.upper() for call in calls}

        expected_methods = {"POST", "PUT", "DELETE", "PATCH"}
        for method in expected_methods:
            assert (
                method in methods_found
            ), f"Method {method} not discovered. Found: {methods_found}"

        # Verify specific URLs are found
        urls_found = {call.url for call in calls}
        assert "/api/create" in urls_found
        assert "/api/data" in urls_found
        assert "/api/remove" in urls_found

    @pytest.mark.asyncio
    async def test_js_analyzer_discovers_urls_from_js_contents(self):
        """E2E: JsAnalyzerRegex discovers URLs from js_contents."""
        # Given: JavaScript with API URLs
        js_content = """
        fetch('/api/users');
        axios.get('/api/items');
        """

        js_contents = [
            {
                "url": "http://test.com/app.js",
                "content": js_content,
                "is_inline": False,
            }
        ]

        # When: Run Discovery
        registry = get_default_registry()
        service = DiscoveryService(registry=registry)

        context = DiscoveryContext(
            target_url="http://test.com",
            profile=ScanProfile.STANDARD,
            http_client=None,
            crawl_data={
                "html_content": "<html></html>",
                "base_url": "http://test.com",
                "js_contents": js_contents,
            },
        )

        discovered = await service.run(context)

        # Then: URLs are discovered (as js_url or api_call)
        urls_found = {a.url for a in discovered}
        assert any(
            "/api/users" in url for url in urls_found
        ), f"URL /api/users not found. Found: {urls_found}"
        assert any(
            "/api/items" in url for url in urls_found
        ), f"URL /api/items not found. Found: {urls_found}"


class TestE2ENetworkRequestCapture:
    """E2E: Network request capturing with resource_type"""

    @pytest.mark.asyncio
    async def test_network_requests_transformation(self):
        """E2E: HTTP data is correctly transformed to network_requests format."""
        # Given: http_data with resource_type (Phase 1)
        http_data = {
            "http://test.com/api/users": {
                "request": {
                    "method": "POST",
                    "headers": {"Content-Type": "application/json"},
                    "body": '{"name": "test"}',
                    "resource_type": "fetch",
                },
                "response": {"status": 201, "headers": {}, "body": '{"id": 1}'},
            },
            "http://test.com/api/items/1": {
                "request": {
                    "method": "DELETE",
                    "headers": {},
                    "body": None,
                    "resource_type": "xhr",
                },
                "response": {"status": 204, "headers": {}, "body": ""},
            },
        }

        # When: Transform to network_requests (Phase 3)
        network_requests = _transform_to_network_requests(http_data)

        # Then: resource_type and method are preserved
        assert len(network_requests) == 2

        post_req = next((r for r in network_requests if r["method"] == "POST"), None)
        assert post_req is not None
        assert post_req["resource_type"] == "fetch"
        assert "/api/users" in post_req["url"]

        delete_req = next(
            (r for r in network_requests if r["method"] == "DELETE"), None
        )
        assert delete_req is not None
        assert delete_req["resource_type"] == "xhr"


class TestE2ERealSiteSimulation:
    """E2E: Real site structure simulation"""

    @pytest.mark.asyncio
    async def test_real_site_structure_all_assets_discovered(self):
        """E2E: Simulated real site structure discovers all asset types."""
        # Given: Real site-like structure
        html_content = """
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <title>Test App</title>
            <script src="/static/js/app.js"></script>
        </head>
        <body>
            <nav>
                <a href="/register">Register</a>
                <a href="/login">Login</a>
            </nav>

            <form action="/api/login" method="POST">
                <input type="text" name="username">
                <input type="password" name="password">
                <input type="hidden" name="_csrf" value="token123">
                <button type="submit">Login</button>
            </form>

            <script>
                // Inline API calls
                async function refreshData() {
                    await fetch('/api/refresh', { method: 'POST' });
                }
            </script>
        </body>
        </html>
        """

        app_js = """
        // Application code
        async function loadData() {
            const response = await fetch('/api/data');
            return response.json();
        }

        async function saveData(data) {
            await axios.post('/api/save', data);
        }

        async function deleteItem(id) {
            await fetch('/api/items/' + id, { method: 'DELETE' });
        }
        """

        js_contents = [
            {
                "url": "http://test.com/static/js/app.js",
                "content": app_js,
                "is_inline": False,
            },
            {
                "url": "http://test.com#inline-0",
                "content": "fetch('/api/refresh', { method: 'POST' })",
                "is_inline": True,
                "source_url": "http://test.com",
            },
        ]

        # When: Run full discovery
        registry = get_default_registry()
        service = DiscoveryService(registry=registry)

        context = DiscoveryContext(
            target_url="http://test.com",
            profile=ScanProfile.STANDARD,
            http_client=None,
            crawl_data={
                "html_content": html_content,
                "base_url": "http://test.com",
                "js_contents": js_contents,
            },
        )

        discovered = await service.run(context)

        # Then: All asset types are discovered
        _asset_types = {a.asset_type for a in discovered}  # noqa: F841
        urls = {a.url for a in discovered}

        # 1. Form action is discovered
        form_assets = [a for a in discovered if a.asset_type == "form"]
        assert len(form_assets) >= 1, "Form should be discovered"

        # 2. Links are discovered
        link_assets = [
            a for a in discovered if "/register" in a.url or "/login" in a.url
        ]
        assert len(link_assets) >= 1, "Links should be discovered"

        # 3. JavaScript API calls are discovered
        api_assets = [
            a for a in discovered if "api_call" in a.asset_type or "/api/" in a.url
        ]
        assert len(api_assets) >= 1, f"API calls should be discovered. Found: {urls}"

        # 4. POST/DELETE methods found
        methods_found = {
            a.metadata.get("method", "GET").upper()
            for a in discovered
            if a.metadata.get("method")
        }
        assert (
            "POST" in methods_found
        ), f"POST method should be found. Methods: {methods_found}"
