"""E2E test fixtures for Discovery module.

Provides comprehensive fixtures for end-to-end testing of the Discovery service,
including sample crawl data, mock HTTP responses, full module registry, and
time measurement utilities.
"""

from __future__ import annotations

import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile
from app.services.discovery.modules import (
    ApiSchemaGeneratorModule,
    ConfigDiscoveryModule,
    HtmlElementParserModule,
    InteractionEngineModule,
    JsAnalyzerAstModule,
    JsAnalyzerRegexModule,
    NetworkCapturerModule,
    ResponseAnalyzerModule,
    TechFingerprintModule,
    ThirdPartyDetectorModule,
)
from app.services.discovery.registry import DiscoveryModuleRegistry

# ============================================================================
# Profile Time Limits
# ============================================================================

PROFILE_TIME_LIMITS: Dict[ScanProfile, float] = {
    ScanProfile.QUICK: 30.0,  # 30 seconds
    ScanProfile.STANDARD: 120.0,  # 2 minutes
    ScanProfile.FULL: 300.0,  # 5 minutes
}


# ============================================================================
# Sample Crawl Data
# ============================================================================

SAMPLE_HTML_CONTENT: str = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta property="og:title" content="Example Site">
    <meta property="og:image" content="https://example.com/og-image.png">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:image" content="https://example.com/twitter-image.png">
    <title>Example Website</title>
    <base href="https://example.com/">
    <link rel="stylesheet" href="/css/main.css">
    <link rel="preload" href="/fonts/roboto.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="icon" href="/favicon.ico">
    <script src="https://cdn.example.com/analytics.js" defer></script>
</head>
<body>
    <header>
        <nav>
            <a href="/">Home</a>
            <a href="/about">About</a>
            <a href="/products">Products</a>
            <a href="/api/docs">API</a>
            <a href="https://blog.example.com">Blog</a>
        </nav>
    </header>

    <main>
        <section id="hero">
            <img src="/images/hero.jpg" alt="Hero image"
                 srcset="/images/hero-1x.jpg 1x, /images/hero-2x.jpg 2x">
            <video poster="/images/video-poster.jpg">
                <source src="/videos/intro.mp4" type="video/mp4">
                <source src="/videos/intro.webm" type="video/webm">
                <track src="/subtitles/intro.vtt" kind="subtitles" srclang="en">
            </video>
        </section>

        <section id="forms">
            <form action="/api/login" method="POST">
                <input type="hidden" name="csrf_token" value="abc123xyz">
                <input type="email" name="email" required>
                <input type="password" name="password" required>
                <button type="submit">Login</button>
            </form>

            <form action="/api/search" method="GET">
                <input type="text" name="q" placeholder="Search...">
                <button type="submit">Search</button>
            </form>

            <form action="/api/contact" method="POST">
                <input type="hidden" name="_token" value="def456uvw">
                <textarea name="message"></textarea>
                <button type="submit">Send</button>
            </form>
        </section>

        <section id="data-elements">
            <div data-api-url="/api/users" data-endpoint="/api/v2/data"></div>
            <button data-action-url="https://api.example.com/actions/submit">Submit</button>
            <script type="application/json" id="config">
                {
                    "apiBase": "https://api.example.com/v1",
                    "wsEndpoint": "wss://ws.example.com/socket",
                    "cdnUrl": "https://cdn.example.com"
                }
            </script>
        </section>
    </main>

    <footer>
        <a href="/privacy">Privacy Policy</a>
        <a href="/terms">Terms of Service</a>
    </footer>

    <script src="/js/main.js"></script>
    <script src="/js/vendor.js" integrity="sha384-abc123"></script>
    <script>
        // Inline script with URLs
        const API_BASE = "https://api.example.com";
        fetch("/api/users").then(r => r.json());
        const wsUrl = "wss://ws.example.com/realtime";
    </script>
</body>
</html>"""


SAMPLE_JAVASCRIPT_CONTENT: str = """
// Main application JavaScript
import React from 'react';
import { BrowserRouter, Route, Switch } from 'react-router-dom';

// API Configuration
const config = {
    apiUrl: 'https://api.example.com/v1',
    wsEndpoint: 'wss://ws.example.com/socket',
    graphqlEndpoint: 'https://api.example.com/graphql',
    cdnUrl: process.env.REACT_APP_CDN_URL || 'https://cdn.example.com',
};

// Router paths
const routes = [
    { path: '/', component: Home },
    { path: '/users', component: UserList },
    { path: '/users/:id', component: UserDetail },
    { path: '/products/:category/:id', component: ProductDetail },
    { path: '/api/v1/data', component: DataPage },
    { path: '/admin/*', component: AdminPanel },
];

// API calls
async function fetchUsers() {
    const response = await fetch('/api/users');
    return response.json();
}

async function fetchUserById(id) {
    const url = `/api/users/${id}`;
    return fetch(url).then(r => r.json());
}

// Axios usage
axios.get('/api/products')
    .then(response => console.log(response.data));

axios.post('https://api.example.com/orders', { items: [] });

// jQuery AJAX
$.ajax({
    url: '/api/legacy/data',
    method: 'GET',
    success: function(data) {}
});

$.get('/api/jquery/endpoint');
$.post('/api/jquery/submit', { data: 'value' });

// XHR
var xhr = new XMLHttpRequest();
xhr.open('POST', '/api/xhr/upload');
xhr.send();

// Template literals with URLs
const userId = 123;
const endpoint = `https://api.example.com/users/${userId}/profile`;
const dynamicUrl = `/api/v2/items/${itemId}/details`;

// Potential secrets (for testing detection)
const API_KEY = 'sk_live_1234567890abcdef';
const AWS_SECRET = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY';
const JWT_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U';

// WebSocket
const socket = new WebSocket('wss://ws.example.com/realtime');
socket.onmessage = (event) => console.log(event.data);

// GraphQL
const query = `
    query GetUser($id: ID!) {
        user(id: $id) {
            id
            name
            email
        }
    }
`;

fetch('/graphql', {
    method: 'POST',
    body: JSON.stringify({ query, variables: { id: '123' } })
});

export default App;
"""


SAMPLE_ROBOTS_TXT: str = """# robots.txt for example.com
User-agent: *
Disallow: /admin/
Disallow: /private/
Disallow: /api/internal/
Disallow: /tmp/
Allow: /api/public/

User-agent: Googlebot
Disallow: /no-google/

Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap-pages.xml
"""


SAMPLE_SITEMAP_XML: str = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://example.com/</loc>
        <lastmod>2024-01-01</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://example.com/about</loc>
        <lastmod>2024-01-01</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://example.com/products</loc>
        <lastmod>2024-01-15</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://example.com/blog</loc>
        <lastmod>2024-01-20</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.7</priority>
    </url>
</urlset>"""


SAMPLE_SECURITY_TXT: str = """Contact: security@example.com
Expires: 2025-12-31T23:59:59.000Z
Encryption: https://example.com/.well-known/pgp-key.txt
Acknowledgments: https://example.com/security/hall-of-fame
Policy: https://example.com/security/policy
Hiring: https://example.com/careers/security
"""


SAMPLE_OPENID_CONFIG: Dict[str, Any] = {
    "issuer": "https://auth.example.com",
    "authorization_endpoint": "https://auth.example.com/oauth/authorize",
    "token_endpoint": "https://auth.example.com/oauth/token",
    "userinfo_endpoint": "https://auth.example.com/oauth/userinfo",
    "jwks_uri": "https://auth.example.com/.well-known/jwks.json",
    "response_types_supported": ["code", "token", "id_token"],
    "scopes_supported": ["openid", "profile", "email"],
}


def create_full_crawl_data(
    target_url: str = "https://example.com",
) -> Dict[str, Any]:
    """Create comprehensive crawl data for E2E testing.

    Args:
        target_url: Base target URL

    Returns:
        Complete crawl data dictionary
    """
    return {
        "target_url": target_url,
        "base_url": target_url,
        "html_content": SAMPLE_HTML_CONTENT,
        "scripts": [
            f"{target_url}/js/main.js",
            f"{target_url}/js/vendor.js",
            "https://cdn.example.com/analytics.js",
        ],
        "script_contents": {
            f"{target_url}/js/main.js": SAMPLE_JAVASCRIPT_CONTENT,
        },
        "stylesheets": [
            f"{target_url}/css/main.css",
        ],
        "http_data": {
            target_url: {
                "request": {
                    "method": "GET",
                    "headers": {"User-Agent": "EAZY-Scanner/1.0"},
                    "body": "",
                },
                "response": {
                    "status": 200,
                    "headers": {
                        "Content-Type": "text/html; charset=utf-8",
                        "Server": "nginx/1.21.0",
                        "X-Powered-By": "Express",
                        "Content-Security-Policy": "default-src 'self'; script-src 'self' https://cdn.example.com; style-src 'self' 'unsafe-inline'",
                        "Access-Control-Allow-Origin": "*",
                        "Set-Cookie": "session=abc123; HttpOnly; Secure; SameSite=Strict",
                    },
                    "body": SAMPLE_HTML_CONTENT,
                },
            },
            f"{target_url}/robots.txt": {
                "request": {"method": "GET", "headers": {}, "body": ""},
                "response": {
                    "status": 200,
                    "headers": {"Content-Type": "text/plain"},
                    "body": SAMPLE_ROBOTS_TXT,
                },
            },
            f"{target_url}/sitemap.xml": {
                "request": {"method": "GET", "headers": {}, "body": ""},
                "response": {
                    "status": 200,
                    "headers": {"Content-Type": "application/xml"},
                    "body": SAMPLE_SITEMAP_XML,
                },
            },
        },
        "responses": [
            {
                "url": target_url,
                "status_code": 200,
                "headers": {
                    "Content-Type": "text/html; charset=utf-8",
                    "Server": "nginx/1.21.0",
                    "X-Powered-By": "Express",
                    "Content-Security-Policy": "default-src 'self'; script-src 'self' https://cdn.example.com",
                    "Access-Control-Allow-Origin": "*",
                    "Set-Cookie": "session=abc123; HttpOnly; Secure; SameSite=Strict",
                },
                "body": SAMPLE_HTML_CONTENT,
            },
            {
                "url": f"{target_url}/api/error",
                "status_code": 500,
                "headers": {"Content-Type": "text/html"},
                "body": """
                    <html>
                    <h1>Internal Server Error</h1>
                    <pre>
                    Traceback (most recent call last):
                        File "/var/www/app/views.py", line 42, in index
                            raise Exception("Database error")
                    Exception: Database error
                    </pre>
                    </html>
                """,
            },
        ],
        "network_requests": [
            {
                "url": f"{target_url}/api/users",
                "method": "GET",
                "headers": {"Accept": "application/json"},
                "resource_type": "xhr",
                "is_xhr": True,
            },
            {
                "url": f"{target_url}/api/products",
                "method": "GET",
                "headers": {"Accept": "application/json"},
                "resource_type": "fetch",
                "is_fetch": True,
            },
            {
                "url": f"{target_url}/graphql",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": '{"query": "{ users { id name } }"}',
                "resource_type": "fetch",
                "is_fetch": True,
            },
        ],
        "websocket_connections": [
            {
                "url": "wss://ws.example.com/socket",
                "protocols": ["graphql-ws"],
            },
        ],
        "interaction_results": [
            {
                "action": "click",
                "selector": "button.load-more",
                "triggered_requests": [
                    {"url": f"{target_url}/api/items?page=2", "method": "GET"},
                ],
                "new_elements": [],
            },
        ],
    }


# ============================================================================
# Mock HTTP Responses
# ============================================================================


@dataclass
class MockHttpResponse:
    """Mock HTTP response for testing."""

    status_code: int
    headers: Dict[str, str]
    text: str
    content: bytes = b""

    def __post_init__(self) -> None:
        if not self.content and self.text:
            self.content = self.text.encode("utf-8")

    def json(self) -> Any:
        """Parse response as JSON."""
        import json

        return json.loads(self.text)


MOCK_HTTP_RESPONSES: Dict[str, MockHttpResponse] = {
    # Success responses
    "https://example.com": MockHttpResponse(
        status_code=200,
        headers={
            "Content-Type": "text/html; charset=utf-8",
            "Server": "nginx/1.21.0",
            "X-Powered-By": "Express",
        },
        text=SAMPLE_HTML_CONTENT,
    ),
    "https://example.com/robots.txt": MockHttpResponse(
        status_code=200,
        headers={"Content-Type": "text/plain"},
        text=SAMPLE_ROBOTS_TXT,
    ),
    "https://example.com/sitemap.xml": MockHttpResponse(
        status_code=200,
        headers={"Content-Type": "application/xml"},
        text=SAMPLE_SITEMAP_XML,
    ),
    "https://example.com/.well-known/security.txt": MockHttpResponse(
        status_code=200,
        headers={"Content-Type": "text/plain"},
        text=SAMPLE_SECURITY_TXT,
    ),
    "https://example.com/.well-known/openid-configuration": MockHttpResponse(
        status_code=200,
        headers={"Content-Type": "application/json"},
        text='{"issuer": "https://auth.example.com", "authorization_endpoint": "https://auth.example.com/oauth/authorize", "token_endpoint": "https://auth.example.com/oauth/token", "userinfo_endpoint": "https://auth.example.com/oauth/userinfo", "jwks_uri": "https://auth.example.com/.well-known/jwks.json"}',
    ),
    "https://example.com/js/main.js": MockHttpResponse(
        status_code=200,
        headers={"Content-Type": "application/javascript"},
        text=SAMPLE_JAVASCRIPT_CONTENT,
    ),
    "https://example.com/api/users": MockHttpResponse(
        status_code=200,
        headers={"Content-Type": "application/json"},
        text='[{"id": 1, "name": "User 1"}, {"id": 2, "name": "User 2"}]',
    ),
    # Redirect responses
    "https://example.com/old-page": MockHttpResponse(
        status_code=301,
        headers={
            "Location": "https://example.com/new-page",
            "Content-Type": "text/html",
        },
        text="<html><body>Moved Permanently</body></html>",
    ),
    "https://example.com/temp-redirect": MockHttpResponse(
        status_code=302,
        headers={
            "Location": "https://example.com/target",
            "Content-Type": "text/html",
        },
        text="<html><body>Found</body></html>",
    ),
    # Error responses
    "https://example.com/not-found": MockHttpResponse(
        status_code=404,
        headers={"Content-Type": "text/html"},
        text="<html><body><h1>404 Not Found</h1></body></html>",
    ),
    "https://example.com/server-error": MockHttpResponse(
        status_code=500,
        headers={"Content-Type": "text/html"},
        text="""<html><body>
            <h1>Internal Server Error</h1>
            <pre>Traceback (most recent call last):
                File "/var/www/app/views.py", line 42
            Exception: Database connection failed</pre>
        </body></html>""",
    ),
    "https://example.com/forbidden": MockHttpResponse(
        status_code=403,
        headers={"Content-Type": "text/html"},
        text="<html><body><h1>403 Forbidden</h1></body></html>",
    ),
    # Various content types
    "https://example.com/api/data.json": MockHttpResponse(
        status_code=200,
        headers={"Content-Type": "application/json"},
        text='{"status": "ok", "data": []}',
    ),
    "https://example.com/api/data.xml": MockHttpResponse(
        status_code=200,
        headers={"Content-Type": "application/xml"},
        text='<?xml version="1.0"?><data><status>ok</status></data>',
    ),
    "https://example.com/graphql": MockHttpResponse(
        status_code=200,
        headers={"Content-Type": "application/json"},
        text='{"data": {"users": []}}',
    ),
}


def create_mock_http_client(
    responses: Optional[Dict[str, MockHttpResponse]] = None,
) -> MagicMock:
    """Create a mock HTTP client with predefined responses.

    Args:
        responses: Custom response mapping (URL -> MockHttpResponse)

    Returns:
        Mock HTTP client
    """
    response_map = responses or MOCK_HTTP_RESPONSES

    async def mock_get(url: str, **kwargs: Any) -> MockHttpResponse:
        if url in response_map:
            return response_map[url]
        # Default 404 response for unknown URLs
        return MockHttpResponse(
            status_code=404,
            headers={"Content-Type": "text/html"},
            text="<html><body>Not Found</body></html>",
        )

    async def mock_post(url: str, **kwargs: Any) -> MockHttpResponse:
        if url in response_map:
            return response_map[url]
        return MockHttpResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            text='{"status": "ok"}',
        )

    client = MagicMock()
    client.get = AsyncMock(side_effect=mock_get)
    client.post = AsyncMock(side_effect=mock_post)
    client.head = AsyncMock(
        return_value=MockHttpResponse(
            status_code=200,
            headers={"Content-Type": "text/html"},
            text="",
        )
    )

    return client


# ============================================================================
# Time Measurement Utilities
# ============================================================================


@dataclass
class TimingResult:
    """Result of a timed operation."""

    elapsed_seconds: float
    profile: ScanProfile
    time_limit: float
    is_within_limit: bool

    @property
    def elapsed_ms(self) -> float:
        """Elapsed time in milliseconds."""
        return self.elapsed_seconds * 1000

    @property
    def margin_seconds(self) -> float:
        """Time remaining before limit."""
        return self.time_limit - self.elapsed_seconds

    @property
    def usage_percent(self) -> float:
        """Percentage of time limit used."""
        return (self.elapsed_seconds / self.time_limit) * 100


class TimeLimitChecker:
    """Utility for checking profile-based time limits."""

    def __init__(self, time_limits: Optional[Dict[ScanProfile, float]] = None) -> None:
        """Initialize TimeLimitChecker.

        Args:
            time_limits: Custom time limits per profile
        """
        self._time_limits = time_limits or PROFILE_TIME_LIMITS
        self._start_time: Optional[float] = None
        self._profile: Optional[ScanProfile] = None

    def get_limit(self, profile: ScanProfile) -> float:
        """Get time limit for a profile.

        Args:
            profile: Scan profile

        Returns:
            Time limit in seconds
        """
        return self._time_limits.get(profile, 120.0)

    @contextmanager
    def measure(
        self, profile: ScanProfile
    ) -> Generator[Callable[[], TimingResult], None, None]:
        """Context manager for measuring execution time.

        Args:
            profile: Scan profile for time limit

        Yields:
            Callable that returns the current timing result
        """
        start_time = time.perf_counter()
        time_limit = self.get_limit(profile)

        def get_result() -> TimingResult:
            elapsed = time.perf_counter() - start_time
            return TimingResult(
                elapsed_seconds=elapsed,
                profile=profile,
                time_limit=time_limit,
                is_within_limit=elapsed <= time_limit,
            )

        yield get_result

    def check_elapsed(
        self,
        elapsed_seconds: float,
        profile: ScanProfile,
    ) -> TimingResult:
        """Check if elapsed time is within profile limit.

        Args:
            elapsed_seconds: Elapsed time in seconds
            profile: Scan profile

        Returns:
            Timing result
        """
        time_limit = self.get_limit(profile)
        return TimingResult(
            elapsed_seconds=elapsed_seconds,
            profile=profile,
            time_limit=time_limit,
            is_within_limit=elapsed_seconds <= time_limit,
        )

    def assert_within_limit(
        self,
        elapsed_seconds: float,
        profile: ScanProfile,
        message: str = "",
    ) -> None:
        """Assert that elapsed time is within profile limit.

        Args:
            elapsed_seconds: Elapsed time in seconds
            profile: Scan profile
            message: Optional message for assertion

        Raises:
            AssertionError: If time limit exceeded
        """
        result = self.check_elapsed(elapsed_seconds, profile)
        if not result.is_within_limit:
            msg = (
                f"{message + ': ' if message else ''}"
                f"Time limit exceeded for {profile.value} profile. "
                f"Elapsed: {result.elapsed_seconds:.2f}s, "
                f"Limit: {result.time_limit:.2f}s"
            )
            raise AssertionError(msg)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_http_client() -> MagicMock:
    """Mock HTTP client with predefined responses."""
    return create_mock_http_client()


@pytest.fixture
def full_crawl_data() -> Dict[str, Any]:
    """Complete crawl data for E2E testing."""
    return create_full_crawl_data()


@pytest.fixture
def full_registry() -> DiscoveryModuleRegistry:
    """Registry with all 10 real Discovery modules registered.

    Registered modules:
    1. ConfigDiscoveryModule - robots.txt, sitemap, well-known files
    2. HtmlElementParserModule - HTML element parsing
    3. ResponseAnalyzerModule - HTTP response analysis
    4. NetworkCapturerModule - XHR/Fetch, CORS, GraphQL, WebSocket
    5. JsAnalyzerAstModule - JavaScript AST analysis
    6. JsAnalyzerRegexModule - JavaScript regex analysis
    7. InteractionEngineModule - Dynamic interaction simulation
    8. TechFingerprintModule - Technology stack fingerprinting
    9. ThirdPartyDetectorModule - Third-party service detection
    10. ApiSchemaGeneratorModule - OpenAPI schema generation
    """
    registry = DiscoveryModuleRegistry()

    # Phase 2 - Basic modules
    registry.register(ConfigDiscoveryModule())
    registry.register(HtmlElementParserModule())
    registry.register(ResponseAnalyzerModule())

    # Phase 3 - Network capture
    registry.register(NetworkCapturerModule())

    # Phase 4 - JavaScript analysis
    registry.register(JsAnalyzerAstModule())
    registry.register(JsAnalyzerRegexModule())

    # Phase 5 - Advanced modules
    registry.register(InteractionEngineModule())
    registry.register(TechFingerprintModule())
    registry.register(ThirdPartyDetectorModule())
    registry.register(ApiSchemaGeneratorModule())

    return registry


@pytest.fixture
def quick_registry() -> DiscoveryModuleRegistry:
    """Registry with modules active for QUICK profile only.

    Active modules for QUICK:
    - HtmlElementParserModule
    - JsAnalyzerRegexModule
    """
    registry = DiscoveryModuleRegistry()
    registry.register(HtmlElementParserModule())
    registry.register(JsAnalyzerRegexModule())
    return registry


@pytest.fixture
def standard_registry() -> DiscoveryModuleRegistry:
    """Registry with modules active for STANDARD profile.

    Active modules for STANDARD:
    - ConfigDiscoveryModule
    - HtmlElementParserModule
    - ResponseAnalyzerModule
    - NetworkCapturerModule
    - JsAnalyzerRegexModule
    - TechFingerprintModule
    - ThirdPartyDetectorModule
    """
    registry = DiscoveryModuleRegistry()
    registry.register(ConfigDiscoveryModule())
    registry.register(HtmlElementParserModule())
    registry.register(ResponseAnalyzerModule())
    registry.register(NetworkCapturerModule())
    registry.register(JsAnalyzerRegexModule())
    registry.register(TechFingerprintModule())
    registry.register(ThirdPartyDetectorModule())
    return registry


@pytest.fixture
def e2e_discovery_context(
    mock_http_client: MagicMock,
    full_crawl_data: Dict[str, Any],
) -> DiscoveryContext:
    """E2E discovery context with mock client and full crawl data.

    Uses STANDARD profile by default.
    """
    return DiscoveryContext(
        target_url="https://example.com",
        profile=ScanProfile.STANDARD,
        http_client=mock_http_client,
        crawl_data=full_crawl_data,
    )


@pytest.fixture
def quick_discovery_context(
    mock_http_client: MagicMock,
    full_crawl_data: Dict[str, Any],
) -> DiscoveryContext:
    """E2E discovery context with QUICK profile."""
    return DiscoveryContext(
        target_url="https://example.com",
        profile=ScanProfile.QUICK,
        http_client=mock_http_client,
        crawl_data=full_crawl_data,
    )


@pytest.fixture
def full_discovery_context(
    mock_http_client: MagicMock,
    full_crawl_data: Dict[str, Any],
) -> DiscoveryContext:
    """E2E discovery context with FULL profile."""
    return DiscoveryContext(
        target_url="https://example.com",
        profile=ScanProfile.FULL,
        http_client=mock_http_client,
        crawl_data=full_crawl_data,
    )


@pytest.fixture
def time_limit_checker() -> TimeLimitChecker:
    """Time limit checker utility for profile-based validation."""
    return TimeLimitChecker()


@pytest.fixture
def profile_time_limits() -> Dict[ScanProfile, float]:
    """Profile time limit constants."""
    return PROFILE_TIME_LIMITS.copy()


# ============================================================================
# Helper Functions
# ============================================================================


def create_test_asset(
    url: str,
    asset_type: str = "endpoint",
    source: str = "e2e_test",
    metadata: Optional[Dict[str, Any]] = None,
) -> DiscoveredAsset:
    """Factory function to create test assets.

    Args:
        url: Asset URL
        asset_type: Type of asset
        source: Discovery source
        metadata: Optional metadata

    Returns:
        DiscoveredAsset instance
    """
    return DiscoveredAsset(
        url=url,
        asset_type=asset_type,
        source=source,
        metadata=metadata or {},
    )


async def collect_all_assets(
    registry: DiscoveryModuleRegistry,
    context: DiscoveryContext,
) -> List[DiscoveredAsset]:
    """Collect all assets from all active modules.

    Args:
        registry: Module registry
        context: Discovery context

    Returns:
        List of all discovered assets
    """
    assets: List[DiscoveredAsset] = []

    for module in registry.get_by_profile(context.profile):
        async for asset in module.discover(context):
            assets.append(asset)

    return assets


def count_assets_by_type(assets: List[DiscoveredAsset]) -> Dict[str, int]:
    """Count assets grouped by type.

    Args:
        assets: List of assets

    Returns:
        Dictionary of type -> count
    """
    counts: Dict[str, int] = {}
    for asset in assets:
        counts[asset.asset_type] = counts.get(asset.asset_type, 0) + 1
    return counts


def count_assets_by_source(assets: List[DiscoveredAsset]) -> Dict[str, int]:
    """Count assets grouped by source module.

    Args:
        assets: List of assets

    Returns:
        Dictionary of source -> count
    """
    counts: Dict[str, int] = {}
    for asset in assets:
        counts[asset.source] = counts.get(asset.source, 0) + 1
    return counts


# ============================================================================
# Phase 7: Performance & Edge Case Testing Fixtures
# ============================================================================

# Performance thresholds in seconds
PERFORMANCE_THRESHOLDS: Dict[str, float] = {
    "html_parse_1mb": 2.0,  # Parse 1MB HTML under 2 seconds
    "js_analyze_1mb": 3.0,  # Analyze 1MB JS under 3 seconds
    "full_discovery_1mb": 10.0,  # Full discovery pipeline under 10 seconds
    "memory_peak_mb": 500.0,  # Peak memory under 500MB
    "url_extraction_per_mb": 1.0,  # URL extraction per MB under 1 second
}

# CI environments may be slower, apply buffer multiplier
CI_BUFFER_MULTIPLIER: float = 1.5


# Edge case sample data
OBFUSCATED_JS_SAMPLES: Dict[str, str] = {
    "hex_escape": 'const url = "\\x2f\\x61\\x70\\x69\\x2f\\x68\\x69\\x64\\x64\\x65\\x6e";',  # /api/hidden
    "unicode_escape": 'const endpoint = "\\u002f\\u0061\\u0070\\u0069\\u002f\\u0073\\u0065\\u0063\\u0072\\u0065\\u0074";',  # /api/secret
    "base64_url": 'const config = atob("L2FwaS9lbmNvZGVkL2VuZHBvaW50");',  # /api/encoded/endpoint
    "split_concat": 'const api = "/a" + "pi" + "/sp" + "lit";',
    "array_join": 'const path = ["/api", "array", "join"].join("/");',
    "char_code": "const url = String.fromCharCode(47, 97, 112, 105, 47, 99, 104, 97, 114);",  # /api/char
    "reverse_string": 'const hidden = "terces/ipa/".split("").reverse().join("");',  # /api/secret
    "template_complex": 'const base = "/api"; const ver = "v1"; const url = `${base}/${ver}/${"data"}`;',
}

SHADOW_DOM_SAMPLES: Dict[str, str] = {
    "basic_shadow": """
        <div id="host"></div>
        <script>
            const host = document.getElementById('host');
            const shadow = host.attachShadow({mode: 'open'});
            shadow.innerHTML = '<a href="/api/shadow/link">Shadow Link</a>';
        </script>
    """,
    "nested_shadow": """
        <custom-element>
            <template shadowroot="open">
                <inner-element>
                    <template shadowroot="open">
                        <a href="/api/nested/shadow">Nested</a>
                    </template>
                </inner-element>
            </template>
        </custom-element>
    """,
    "closed_shadow": """
        <div id="closed-host"></div>
        <script>
            const host = document.getElementById('closed-host');
            const shadow = host.attachShadow({mode: 'closed'});
            shadow.innerHTML = '<form action="/api/closed/form" method="POST"></form>';
        </script>
    """,
}

IFRAME_SAMPLES: Dict[str, str] = {
    "basic_iframe": '<iframe src="/api/iframe/basic" id="basic"></iframe>',
    "srcdoc_iframe": "<iframe srcdoc=\"<a href='/api/iframe/srcdoc'>Link</a>\"></iframe>",
    "sandboxed_iframe": '<iframe src="/api/iframe/sandboxed" sandbox="allow-scripts"></iframe>',
    "nested_iframes": """
        <iframe srcdoc="
            <iframe srcdoc='<a href=&quot;/api/iframe/nested&quot;>Nested</a>'></iframe>
        "></iframe>
    """,
    "blob_iframe": """
        <script>
            const blob = new Blob(['<a href="/api/iframe/blob">Blob Link</a>'], {type: 'text/html'});
            document.write('<iframe src="' + URL.createObjectURL(blob) + '"></iframe>');
        </script>
    """,
}

SVG_LINK_SAMPLES: Dict[str, str] = {
    "xlink_href": """
        <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
            <a xlink:href="/api/svg/xlink"><text>XLink</text></a>
        </svg>
    """,
    "svg_anchor_href": '<svg><a href="/api/svg/anchor"><rect/></a></svg>',
    "svg_use_xlink": '<svg><use xlink:href="/icons.svg#icon1"/></svg>',
    "svg_use_href": '<svg><use href="/icons-modern.svg#icon2"/></svg>',
    "svg_image_href": '<svg><image href="/api/svg/image.png"/></svg>',
    "svg_image_xlink": '<svg><image xlink:href="/api/svg/legacy-image.png"/></svg>',
    "inline_svg_multiple": """
        <div>
            <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
                <a xlink:href="/api/svg/link1"><text>1</text></a>
                <a href="/api/svg/link2"><text>2</text></a>
                <use xlink:href="#local-icon"/>
                <use href="/external-icons.svg#ext-icon"/>
                <image href="/api/svg/img1.png"/>
                <image xlink:href="/api/svg/img2.png"/>
            </svg>
        </div>
    """,
    "svg_with_fragment": '<svg><use xlink:href="#internal-symbol"/></svg>',
    "svg_external_reference": """
        <object data="/external.svg" type="image/svg+xml"></object>
        <embed src="/embedded.svg" type="image/svg+xml">
        <img src="/image.svg" alt="SVG Image">
    """,
    "svg_with_data_uri": """
        <svg>
            <image href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA"/>
        </svg>
    """,
}

MALFORMED_HTML_SAMPLES: Dict[str, str] = {
    "unclosed_tags": '<div><a href="/api/unclosed"><span>Link</div>',
    "missing_quotes": "<a href=/api/noquotes>No Quotes</a>",
    "mixed_quotes": "<a href='/api/mixed\" data-url=\"/api/mixed2'>Mixed</a>",
    "nested_invalid": '<a href="/outer"><a href="/inner">Nested Links</a></a>',
    "script_in_attr": '<div data-url="/api/normal" onclick="fetch(\'/api/onclick\')">Click</div>',
    "null_bytes": '<a href="/api/null\x00byte">Null</a>',
    "unicode_bom": '\ufeff<a href="/api/bom">BOM</a>',
    "cdata_section": '<![CDATA[<a href="/api/cdata">CDATA Link</a>]]>',
}

ENCODING_SAMPLES: Dict[str, bytes] = {
    "utf8": '<a href="/api/utf8">UTF-8 Link</a>'.encode("utf-8"),
    "utf16": '<a href="/api/utf16">UTF-16 Link</a>'.encode("utf-16"),
    "latin1": '<a href="/api/latin1">Latin-1: cafe</a>'.encode("latin-1"),
    "mixed_encoding": b'<a href="/api/mixed">\xff\xfe Mixed</a>',
}

CIRCULAR_REFERENCE_SAMPLES: Dict[str, Any] = {
    "redirect_loop": [
        ("/page-a", "/page-b"),
        ("/page-b", "/page-c"),
        ("/page-c", "/page-a"),
    ],
    "self_reference": "/api/self?redirect=/api/self",
    "deep_chain": [f"/api/chain/{i}" for i in range(100)],
}


@pytest.fixture
def large_html_content() -> str:
    """Load 1MB realistic HTML fixture for performance testing."""
    fixture_path = (
        Path(__file__).parent.parent.parent
        / "fixtures/performance/html/1mb_realistic.html"
    )
    if fixture_path.exists():
        return fixture_path.read_text(encoding="utf-8")
    # Fallback: generate minimal large content
    return "<html><body>" + "<div>" * 50000 + "</div>" * 50000 + "</body></html>"


@pytest.fixture
def large_js_content() -> str:
    """Load 1MB realistic JavaScript fixture for performance testing."""
    fixture_path = (
        Path(__file__).parent.parent.parent / "fixtures/performance/js/1mb_realistic.js"
    )
    if fixture_path.exists():
        return fixture_path.read_text(encoding="utf-8")
    # Fallback: generate minimal large content
    return "const data = {};\n" * 30000


@pytest.fixture
def obfuscated_js_samples() -> Dict[str, str]:
    """Obfuscated JavaScript samples for edge case testing."""
    return OBFUSCATED_JS_SAMPLES.copy()


@pytest.fixture
def shadow_dom_samples() -> Dict[str, str]:
    """Shadow DOM HTML samples for edge case testing."""
    return SHADOW_DOM_SAMPLES.copy()


@pytest.fixture
def iframe_samples() -> Dict[str, str]:
    """Iframe HTML samples for edge case testing."""
    return IFRAME_SAMPLES.copy()


@pytest.fixture
def svg_link_samples() -> Dict[str, str]:
    """SVG link samples for edge case testing."""
    return SVG_LINK_SAMPLES.copy()


@pytest.fixture
def malformed_html_samples() -> Dict[str, str]:
    """Malformed HTML samples for error handling tests."""
    return MALFORMED_HTML_SAMPLES.copy()


@pytest.fixture
def encoding_samples() -> Dict[str, bytes]:
    """Various encoding samples for robustness testing."""
    return ENCODING_SAMPLES.copy()


@pytest.fixture
def circular_reference_samples() -> Dict[str, Any]:
    """Circular reference samples for loop detection testing."""
    return CIRCULAR_REFERENCE_SAMPLES.copy()


@pytest.fixture
def performance_thresholds() -> Dict[str, float]:
    """Performance threshold values for benchmark tests."""
    return PERFORMANCE_THRESHOLDS.copy()


@pytest.fixture
def error_http_client() -> Callable[[int, Optional[str]], MagicMock]:
    """Factory fixture for creating HTTP clients that return specific errors.

    Returns:
        Factory function that creates mock HTTP clients with specified error behavior
    """

    def _create_error_client(
        status_code: int = 500,
        error_message: Optional[str] = None,
        raise_exception: Optional[Exception] = None,
    ) -> MagicMock:
        """Create a mock HTTP client that returns errors.

        Args:
            status_code: HTTP status code to return
            error_message: Optional error message in response body
            raise_exception: Optional exception to raise instead of returning response

        Returns:
            Mock HTTP client configured for error responses
        """
        default_messages = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            429: "Too Many Requests",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout",
        }

        message = error_message or default_messages.get(status_code, "Error")

        async def mock_request(url: str, **kwargs: Any) -> MockHttpResponse:
            if raise_exception:
                raise raise_exception
            return MockHttpResponse(
                status_code=status_code,
                headers={"Content-Type": "text/html"},
                text=f"<html><body><h1>{status_code} {message}</h1></body></html>",
            )

        client = MagicMock()
        client.get = AsyncMock(side_effect=mock_request)
        client.post = AsyncMock(side_effect=mock_request)
        client.head = AsyncMock(side_effect=mock_request)
        client.request = AsyncMock(side_effect=mock_request)

        return client

    return _create_error_client


@pytest.fixture
def timeout_http_client() -> MagicMock:
    """HTTP client that simulates timeout errors."""

    async def mock_timeout(url: str, **kwargs: Any) -> None:
        raise httpx.TimeoutException(f"Request to {url} timed out")

    client = MagicMock()
    client.get = AsyncMock(side_effect=mock_timeout)
    client.post = AsyncMock(side_effect=mock_timeout)
    client.head = AsyncMock(side_effect=mock_timeout)

    return client


@pytest.fixture
def connection_error_http_client() -> MagicMock:
    """HTTP client that simulates connection errors."""

    async def mock_connection_error(url: str, **kwargs: Any) -> None:
        raise httpx.ConnectError(f"Failed to connect to {url}")

    client = MagicMock()
    client.get = AsyncMock(side_effect=mock_connection_error)
    client.post = AsyncMock(side_effect=mock_connection_error)
    client.head = AsyncMock(side_effect=mock_connection_error)

    return client


@pytest.fixture
def memory_tracker() -> Generator[Callable[[], Dict[str, float]], None, None]:
    """Context manager fixture for tracking memory usage.

    Yields:
        Function that returns current memory statistics
    """
    tracemalloc.start()

    def get_memory_stats() -> Dict[str, float]:
        current, peak = tracemalloc.get_traced_memory()
        return {
            "current_mb": current / 1024 / 1024,
            "peak_mb": peak / 1024 / 1024,
        }

    yield get_memory_stats

    tracemalloc.stop()


@pytest.fixture
def slow_http_client() -> Callable[[float], MagicMock]:
    """Factory fixture for creating HTTP clients with artificial delays.

    Returns:
        Factory function that creates mock HTTP clients with specified delays
    """
    import asyncio

    def _create_slow_client(delay_seconds: float = 1.0) -> MagicMock:
        """Create a mock HTTP client with artificial delay.

        Args:
            delay_seconds: Delay in seconds before returning response

        Returns:
            Mock HTTP client with delay
        """

        async def mock_slow_request(url: str, **kwargs: Any) -> MockHttpResponse:
            await asyncio.sleep(delay_seconds)
            return MockHttpResponse(
                status_code=200,
                headers={"Content-Type": "text/html"},
                text="<html><body>Delayed Response</body></html>",
            )

        client = MagicMock()
        client.get = AsyncMock(side_effect=mock_slow_request)
        client.post = AsyncMock(side_effect=mock_slow_request)
        client.head = AsyncMock(side_effect=mock_slow_request)

        return client

    return _create_slow_client


# ============================================================================
# Phase 7.2: Edge Case Testing Fixtures - Unicode and Relative URLs
# ============================================================================

# Unicode URL samples for edge case testing
UNICODE_URL_SAMPLES: Dict[str, Dict[str, Any]] = {
    "idn_japanese": {
        "original": "https://\u4f8b\u3048.jp/path",
        "description": "Japanese IDN domain",
        "expected_normalized": "https://xn--r8jz45g.jp/path",
    },
    "idn_chinese": {
        "original": "https://\u4e2d\u6587.\u4e2d\u56fd/\u8def\u5f84",
        "description": "Chinese IDN domain with Chinese path",
        "expected_normalized": "https://xn--fiq228c.xn--fiqs8s/%E8%B7%AF%E5%BE%84",
    },
    "idn_cyrillic": {
        "original": "https://\u043f\u0440\u0438\u043c\u0435\u0440.\u0440\u0444/test",
        "description": "Cyrillic IDN domain",
        "expected_normalized": "https://xn--e1afmkfd.xn--p1ai/test",
    },
    "idn_arabic": {
        "original": "https://\u0645\u062b\u0627\u0644.\u0645\u0635\u0631/api",
        "description": "Arabic IDN domain",
        "expected_normalized": "https://xn--mgbh0fb.xn--wgbh1c/api",
    },
    "utf8_path_japanese": {
        "original": "https://example.com/\u30d1\u30b9/\u30d5\u30a1\u30a4\u30eb",
        "description": "UTF-8 encoded Japanese path",
        "expected_normalized": "https://example.com/%E3%83%91%E3%82%B9/%E3%83%95%E3%82%A1%E3%82%A4%E3%83%AB",
    },
    "utf8_path_korean": {
        "original": "https://example.com/\uacbd\ub85c/\ud30c\uc77c",
        "description": "UTF-8 encoded Korean path",
        "expected_normalized": "https://example.com/%EA%B2%BD%EB%A1%9C/%ED%8C%8C%EC%9D%BC",
    },
    "utf8_query_params": {
        "original": "https://example.com/search?q=\u691c\u7d22\u8a9e",
        "description": "UTF-8 query parameters",
        "expected_normalized": "https://example.com/search?q=%E6%A4%9C%E7%B4%A2%E8%AA%9E",
    },
    "percent_encoded_unicode": {
        "original": "https://example.com/%E3%83%91%E3%82%B9",
        "description": "Already percent-encoded Unicode",
        "expected_normalized": "https://example.com/%E3%83%91%E3%82%B9",
    },
    "mixed_encoding": {
        "original": "https://example.com/api/\u30c7\u30fc\u30bf/%E3%83%86%E3%82%B9%E3%83%88",
        "description": "Mixed raw Unicode and percent-encoded",
        "expected_normalized": "https://example.com/api/%E3%83%87%E3%83%BC%E3%82%BF/%E3%83%86%E3%82%B9%E3%83%88",
    },
    "emoji_path": {
        "original": "https://example.com/\ud83d\ude00/page",
        "description": "Emoji in path",
        "expected_normalized": "https://example.com/%F0%9F%98%80/page",
    },
    "idn_with_utf8_path": {
        "original": "https://\u4f8b\u3048.jp/\u30d1\u30b9/\u30c6\u30b9\u30c8",
        "description": "IDN domain with UTF-8 path",
        "expected_normalized": "https://xn--r8jz45g.jp/%E3%83%91%E3%82%B9/%E3%83%86%E3%82%B9%E3%83%88",
    },
}

# Relative URL samples for edge case testing
RELATIVE_URL_SAMPLES: Dict[str, Dict[str, Any]] = {
    "parent_single": {
        "relative": "../parent/file.html",
        "base": "https://example.com/dir/subdir/page.html",
        "expected": "https://example.com/dir/parent/file.html",
        "description": "Single parent directory traversal",
    },
    "parent_multiple": {
        "relative": "../../root/file.html",
        "base": "https://example.com/a/b/c/page.html",
        "expected": "https://example.com/a/root/file.html",
        "description": "Multiple parent directory traversal",
    },
    "parent_excessive": {
        "relative": "../../../../../etc/passwd",
        "base": "https://example.com/a/b/page.html",
        "expected": "https://example.com/etc/passwd",
        "description": "Excessive parent traversal (clamped to root)",
    },
    "protocol_relative_https": {
        "relative": "//cdn.example.com/script.js",
        "base": "https://example.com/page.html",
        "expected": "https://cdn.example.com/script.js",
        "description": "Protocol-relative URL with HTTPS base",
    },
    "protocol_relative_http": {
        "relative": "//cdn.example.com/script.js",
        "base": "http://example.com/page.html",
        "expected": "http://cdn.example.com/script.js",
        "description": "Protocol-relative URL with HTTP base",
    },
    "query_only": {
        "relative": "?page=2&sort=desc",
        "base": "https://example.com/products/list",
        "expected": "https://example.com/products/list?page=2&sort=desc",
        "description": "Query string only URL",
    },
    "query_replace": {
        "relative": "?newparam=value",
        "base": "https://example.com/page?oldparam=old",
        "expected": "https://example.com/page?newparam=value",
        "description": "Query string replaces existing query",
    },
    "fragment_only": {
        "relative": "#section-3",
        "base": "https://example.com/docs/guide.html",
        "expected": "https://example.com/docs/guide.html#section-3",
        "description": "Fragment only URL",
    },
    "fragment_replace": {
        "relative": "#new-section",
        "base": "https://example.com/page#old-section",
        "expected": "https://example.com/page#new-section",
        "description": "Fragment replaces existing fragment",
    },
    "current_dir_explicit": {
        "relative": "./local/file.js",
        "base": "https://example.com/scripts/",
        "expected": "https://example.com/scripts/local/file.js",
        "description": "Explicit current directory path",
    },
    "current_dir_implicit": {
        "relative": "sibling.html",
        "base": "https://example.com/dir/page.html",
        "expected": "https://example.com/dir/sibling.html",
        "description": "Implicit current directory (relative path)",
    },
    "root_relative": {
        "relative": "/absolute/path.html",
        "base": "https://example.com/any/where/page.html",
        "expected": "https://example.com/absolute/path.html",
        "description": "Root-relative path",
    },
    "complex_mixed": {
        "relative": "../api/./v2/../v1/endpoint?key=val#hash",
        "base": "https://example.com/app/pages/page.html",
        "expected": "https://example.com/app/api/v1/endpoint?key=val#hash",
        "description": "Complex path with mixed . and .. and query/fragment",
    },
    "dot_segments_normalization": {
        "relative": "./a/./b/../c/./d",
        "base": "https://example.com/base/",
        "expected": "https://example.com/base/a/c/d",
        "description": "Path with multiple dot segments for normalization",
    },
    "empty_path_segments": {
        "relative": "a//b///c",
        "base": "https://example.com/dir/",
        "expected": "https://example.com/dir/a//b///c",
        "description": "Path with empty segments (double slashes)",
    },
    "trailing_slash_preservation": {
        "relative": "../other/",
        "base": "https://example.com/dir/page/",
        "expected": "https://example.com/dir/other/",
        "description": "Trailing slash preserved in relative path",
    },
}


@pytest.fixture
def unicode_url_samples() -> Dict[str, Dict[str, Any]]:
    """Unicode URL samples for edge case testing.

    Returns:
        Dictionary of Unicode URL test cases with expected normalization
    """
    return UNICODE_URL_SAMPLES.copy()


@pytest.fixture
def relative_url_samples() -> Dict[str, Dict[str, Any]]:
    """Relative URL samples for edge case testing.

    Returns:
        Dictionary of relative URL test cases with base URLs and expected resolutions
    """
    return RELATIVE_URL_SAMPLES.copy()
