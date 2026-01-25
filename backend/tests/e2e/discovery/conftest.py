"""E2E test fixtures for Discovery module.

Provides comprehensive fixtures for end-to-end testing of the Discovery service,
including sample crawl data, mock HTTP responses, full module registry, and
time measurement utilities.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generator, List, Optional
from unittest.mock import AsyncMock, MagicMock

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
