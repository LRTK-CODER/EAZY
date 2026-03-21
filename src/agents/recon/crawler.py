"""AuthenticatedCrawler — 인증된 세션으로 타겟 웹 앱을 크롤링."""

from __future__ import annotations

import contextlib
import json
import re
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

from pydantic import BaseModel, Field

from src.agents.core.models import CryptoContext, Endpoint
from src.agents.recon.scan_interpreter import LLMClient


class ApiCallRelation(BaseModel):
    """API call relationship between pages."""

    source_url: str
    target_url: str
    method: str
    trigger: str = ""


class DataFlowPath(BaseModel):
    """Data flow path tracking parameter movement across endpoints."""

    param_name: str
    source_url: str
    sink_url: str
    location: str = "body"


class CrawlResult(BaseModel):
    """Structured result of authenticated crawling."""

    discovered_endpoints: list[Endpoint] = Field(default_factory=list)
    api_calls: list[ApiCallRelation] = Field(default_factory=list)
    data_flows: list[DataFlowPath] = Field(default_factory=list)
    crypto_contexts: list[CryptoContext] = Field(default_factory=list)
    pages_visited: list[str] = Field(default_factory=list)
    raw_responses: list[dict[str, Any]] = Field(default_factory=list)
    is_fallback: bool = False
    error: str | None = None


class AuthenticatedCrawler:
    """인증된 세션으로 타겟 웹 앱을 크롤링.

    BFS 기반으로 페이지를 탐색하고, LLM이 탐색 우선순위를 결정한다.
    """

    def __init__(
        self,
        session: Any,  # SessionMiddleware or compatible mock
        llm_client: LLMClient,
    ) -> None:
        self._session = session
        self._llm_client = llm_client

    async def crawl(
        self,
        start_url: str,
        *,
        max_depth: int = 3,
    ) -> CrawlResult:
        """BFS 기반 인증 크롤링. LLM이 탐색 우선순위 결정."""
        queue: list[tuple[str, int]] = [(start_url, 0)]
        visited: set[str] = set()

        all_endpoints: list[Endpoint] = []
        all_api_calls: list[ApiCallRelation] = []
        all_crypto: list[CryptoContext] = []
        pages_visited: list[str] = []
        raw_responses: list[dict[str, Any]] = []
        # Track params per URL for data flow analysis
        param_registry: dict[str, list[tuple[str, str]]] = {}

        try:
            while queue:
                url, depth = queue.pop(0)
                normalized = _normalize_url(url)

                if normalized in visited:
                    continue
                if depth > max_depth:
                    continue
                if not self._session.scope.is_in_scope(url):
                    continue

                visited.add(normalized)
                response = await self._session.request("GET", url)
                body = response.text
                pages_visited.append(url)
                raw_responses.append(_serialize_response(response, url))

                # Extract endpoints from HTML
                endpoints = _extract_endpoints_from_html(body, url)
                all_endpoints.extend(endpoints)

                # Extract API call relations from JS
                api_calls = _extract_api_calls_from_body(body, url)
                all_api_calls.extend(api_calls)

                # Extract crypto contexts from JS
                crypto = _extract_crypto_from_js(body)
                all_crypto.extend(crypto)

                # Track parameters for data flow
                _register_params(param_registry, url, body)

                # Collect new URLs to visit
                new_urls = [
                    ep.url
                    for ep in endpoints
                    if ep.method == "GET"
                    and _normalize_url(ep.url) not in visited
                    and self._session.scope.is_in_scope(ep.url)
                ]

                if new_urls:
                    prioritized = await self._ask_llm_priority(new_urls)
                    queue.extend((u, depth + 1) for u in prioritized)

            # Build data flows from param registry
            data_flows = _extract_data_flows(param_registry)

            return CrawlResult(
                discovered_endpoints=all_endpoints,
                api_calls=all_api_calls,
                data_flows=data_flows,
                crypto_contexts=all_crypto,
                pages_visited=pages_visited,
                raw_responses=raw_responses,
            )
        except Exception:  # noqa: BLE001
            return CrawlResult(
                discovered_endpoints=all_endpoints,
                api_calls=all_api_calls,
                crypto_contexts=all_crypto,
                pages_visited=pages_visited,
                raw_responses=raw_responses,
                is_fallback=True,
                error="Crawl failed — partial results attached",
            )

    async def _ask_llm_priority(self, urls: list[str]) -> list[str]:
        """Ask LLM to prioritize URLs for crawling."""
        prompt = _build_priority_prompt(urls)
        try:
            response = await self._llm_client.interpret(prompt)
            return _parse_priority_response(response, urls)
        except Exception:  # noqa: BLE001
            return urls


def _normalize_url(url: str) -> str:
    """Normalize URL by removing fragment and trailing slash."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def _extract_endpoints_from_html(body: str, base_url: str) -> list[Endpoint]:
    """Extract endpoints from HTML <a> and <form> tags."""
    endpoints: list[Endpoint] = []

    # Extract <a href="...">
    href_re = r'<a\s+[^>]*href=["\']([^"\']+)["\']'
    for match in re.finditer(href_re, body, re.IGNORECASE):
        href = match.group(1)
        full_url = urljoin(base_url, href)
        endpoints.append(Endpoint(url=full_url, method="GET"))

    # Extract <form action="..." method="...">
    for match in re.finditer(
        r'<form\s+[^>]*action=["\']([^"\']+)["\']'
        r'(?:\s+[^>]*method=["\']([^"\']+)["\'])?',
        body,
        re.IGNORECASE,
    ):
        action = match.group(1)
        method_str = (match.group(2) or "GET").upper()
        if method_str not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
            method_str = "POST"
        full_url = urljoin(base_url, action)
        endpoints.append(
            Endpoint(url=full_url, method=method_str)  # type: ignore[arg-type]
        )

    return endpoints


def _extract_api_calls_from_body(body: str, current_url: str) -> list[ApiCallRelation]:
    """Extract API call relations from fetch/XHR patterns in JS."""
    relations: list[ApiCallRelation] = []

    # fetch("url", {method: "..."})
    for match in re.finditer(
        r'fetch\(["\']([^"\']+)["\']' r'(?:\s*,\s*\{[^}]*method:\s*["\'](\w+)["\'])?',
        body,
    ):
        target = match.group(1)
        method = (match.group(2) or "GET").upper()
        if method not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
            method = "GET"
        full_target = urljoin(current_url, target)
        relations.append(
            ApiCallRelation(
                source_url=current_url,
                target_url=full_target,
                method=method,
                trigger="fetch",
            )
        )

    # XMLHttpRequest.open("METHOD", "url")
    for match in re.finditer(
        r'\.open\(["\'](\w+)["\'],\s*["\']([^"\']+)["\']',
        body,
    ):
        method = match.group(1).upper()
        target = match.group(2)
        if method not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
            method = "GET"
        full_target = urljoin(current_url, target)
        relations.append(
            ApiCallRelation(
                source_url=current_url,
                target_url=full_target,
                method=method,
                trigger="xhr",
            )
        )

    return relations


def _extract_crypto_from_js(body: str) -> list[CryptoContext]:
    """Extract crypto contexts from JavaScript using regex patterns."""
    contexts: list[CryptoContext] = []

    # CryptoJS.<Algorithm>.encrypt(...)
    for match in re.finditer(
        r"CryptoJS\.(AES|DES|TripleDES|RC4|Rabbit)\.encrypt\(",
        body,
    ):
        algo = match.group(1)
        # Try to extract key from nearby string literal
        key: str | None = None
        surrounding = body[match.start() : match.start() + 200]
        key_re = r"['\"]([a-fA-F0-9]{6,64}|[^'\"]{3,32})['\"]"
        key_match = re.search(key_re, surrounding)
        if key_match:
            key = key_match.group(1)
        contexts.append(
            CryptoContext(
                detected=True,
                algorithm=algo,
                key=key,
            )
        )

    # crypto.subtle.encrypt(...)
    for match in re.finditer(
        r"crypto\.subtle\.encrypt\(\s*\{[^}]*name:\s*['\"]([^'\"]+)['\"]",
        body,
    ):
        algo = match.group(1)
        contexts.append(CryptoContext(detected=True, algorithm=algo))

    return contexts


def _register_params(
    registry: dict[str, list[tuple[str, str]]],
    url: str,
    body: str,
) -> None:
    """Register parameters found in URL query strings, links, and form inputs."""
    # Query string params from current URL
    parsed = urlparse(url)
    for name in parse_qs(parsed.query):
        registry.setdefault(name, []).append((url, "query"))

    # Query string params from <a href="...?param=val"> links
    for href_match in re.finditer(
        r'<a\s+[^>]*href=["\']([^"\']+)["\']', body, re.IGNORECASE
    ):
        href = href_match.group(1)
        href_parsed = urlparse(href)
        for name in parse_qs(href_parsed.query):
            full_url = urljoin(url, href)
            registry.setdefault(name, []).append((full_url, "query"))

    # Form input params — attribute to the form action URL
    form_action = url  # default if no form found
    for form_match in re.finditer(
        r'<form\s+[^>]*action=["\']([^"\']+)["\']', body, re.IGNORECASE
    ):
        form_action = urljoin(url, form_match.group(1))

    for match in re.finditer(
        r'<input\s+[^>]*name=["\']([^"\']+)["\']',
        body,
        re.IGNORECASE,
    ):
        param_name = match.group(1)
        registry.setdefault(param_name, []).append((form_action, "body"))


def _extract_data_flows(
    registry: dict[str, list[tuple[str, str]]],
) -> list[DataFlowPath]:
    """Build data flow paths from parameter registry.

    A flow exists when the same parameter appears on multiple URLs.
    """
    flows: list[DataFlowPath] = []
    for param_name, locations in registry.items():
        if len(locations) < 2:  # noqa: PLR2004
            continue
        source_url, _ = locations[0]
        for sink_url, location in locations[1:]:
            if source_url != sink_url:
                flows.append(
                    DataFlowPath(
                        param_name=param_name,
                        source_url=source_url,
                        sink_url=sink_url,
                        location=location,
                    )
                )
    return flows


def _build_priority_prompt(urls: list[str]) -> str:
    """Build LLM prompt for URL prioritization."""
    url_list = json.dumps(urls)
    return (
        "You are a security-focused web crawler. Prioritize the following "
        "URLs for crawling based on their likelihood of exposing API "
        "endpoints, authentication flows, or sensitive data.\n"
        "Return a JSON array of URLs in priority order (highest first).\n"
        "Return ONLY valid JSON, no markdown.\n\n"
        f"URLs:\n{url_list}"
    )


def _parse_priority_response(response: str, original_urls: list[str]) -> list[str]:
    """Parse LLM priority response. Falls back to original order."""
    with contextlib.suppress(Exception):
        parsed = json.loads(response)
        if isinstance(parsed, list):
            # Only keep URLs that are in the original list
            valid = [u for u in parsed if u in original_urls]
            # Add any missing URLs at the end
            seen = set(valid)
            for u in original_urls:
                if u not in seen:
                    valid.append(u)
            return valid
    return original_urls


def _serialize_response(response: Any, url: str) -> dict[str, Any]:
    """Serialize a response to a JSON-safe dict."""
    body: str | None = None
    with contextlib.suppress(Exception):
        body = response.text

    status_code: int = 0
    with contextlib.suppress(Exception):
        status_code = response.status_code

    headers: dict[str, str] = {}
    with contextlib.suppress(Exception):
        headers = dict(response.headers)

    return {
        "status_code": status_code,
        "headers": headers,
        "url": url,
        "body": body,
    }
