"""CrawlerService - Web crawler with HTTP interception and parser delegation."""

from typing import Any, Dict, List, Optional, Set

from playwright.async_api import Page, Request, Response, async_playwright

from app.core.constants import (
    JS_CONTENT_TYPES,
    MAX_BODY_SIZE,
    MAX_JS_CONTENT_SIZE,
    PAGE_TIMEOUT_MS,
)
from app.core.structured_logger import get_logger
from app.services.parsers import (
    HtmlResponseParser,
    ImageResponseParser,
    JsonResponseParser,
    ResponseData,
    ResponseParserRegistry,
)
from app.types.http import HttpData, JsContent
from app.utils.url_parser import parse_query_params

logger = get_logger(__name__)


class JsContentCollector:
    """JavaScript content collector.

    HTTP 응답과 인라인 스크립트에서 JavaScript content를 수집합니다.
    """

    def __init__(self) -> None:
        """JsContentCollector 초기화."""
        self._contents: List[JsContent] = []
        self._seen_urls: Set[str] = set()

    def add_from_response(self, url: str, content_type: str, body: bytes) -> None:
        """HTTP 응답에서 JS content 추가.

        Args:
            url: JavaScript 파일 URL
            content_type: HTTP Content-Type 헤더
            body: 응답 body (bytes)
        """
        if not self._is_javascript(url, content_type):
            return
        if url in self._seen_urls:
            return

        self._seen_urls.add(url)
        try:
            content = body.decode("utf-8", errors="ignore")
            # 크기 제한 적용
            if len(content) > MAX_JS_CONTENT_SIZE:
                content = content[:MAX_JS_CONTENT_SIZE]

            self._contents.append(
                {
                    "url": url,
                    "content": content,
                    "content_type": content_type,
                    "is_inline": False,
                }
            )
        except Exception as e:
            logger.warning("JS content decode error", error=str(e), url=url)

    async def collect_inline(self, page: Page, source_url: str) -> None:
        """인라인 스크립트 수집.

        Args:
            page: Playwright Page 객체
            source_url: 부모 페이지 URL
        """
        try:
            scripts = await page.locator("script:not([src])").all()
            for i, script in enumerate(scripts):
                try:
                    content = await script.text_content()
                    if content and content.strip():
                        self._contents.append(
                            {
                                "url": f"{source_url}#inline-{i}",
                                "content": content,
                                "content_type": "text/javascript",
                                "is_inline": True,
                                "source_url": source_url,
                            }
                        )
                except Exception:
                    pass
        except Exception as e:
            logger.warning("Inline script collection error", error=str(e))

    def get_contents(self) -> List[JsContent]:
        """수집된 JS contents 반환.

        Returns:
            수집된 JsContent 리스트의 복사본
        """
        return self._contents.copy()

    def _is_javascript(self, url: str, content_type: str) -> bool:
        """응답이 JavaScript인지 확인.

        Args:
            url: 응답 URL
            content_type: HTTP Content-Type 헤더

        Returns:
            JavaScript 여부
        """
        # URL 확장자 확인
        if url.endswith(".js"):
            return True
        # Content-Type 확인
        content_type_lower = content_type.lower()
        return any(jt in content_type_lower for jt in JS_CONTENT_TYPES)


class CrawlerService:
    """Web crawler using Playwright with HTTP interception.

    Uses ResponseParserRegistry to delegate content-type specific parsing
    to specialized parsers (JSON, HTML, Image, Default).

    Args:
        parser_registry: Optional ResponseParserRegistry. If not provided,
            creates a default registry with standard parsers.
    """

    def __init__(
        self,
        parser_registry: Optional[ResponseParserRegistry] = None,
    ) -> None:
        """Initialize CrawlerService with optional parser registry.

        Args:
            parser_registry: Optional ResponseParserRegistry for content parsing.
                If not provided, creates a default registry with standard parsers.
        """
        if parser_registry is None:
            parser_registry = ResponseParserRegistry()
            parser_registry.register(JsonResponseParser())
            parser_registry.register(HtmlResponseParser())
            parser_registry.register(ImageResponseParser())
        self._parser_registry = parser_registry

    async def crawl(
        self, url: str
    ) -> tuple[List[str], Dict[str, HttpData], List[JsContent]]:
        """Crawl a single page and capture HTTP data.

        Args:
            url: Target URL to crawl

        Returns:
            Tuple of:
            - List of unique URLs found
            - Dict mapping URL -> HttpData (request, response, parameters)
            - List of JavaScript file contents
        """
        links: Set[str] = set()
        http_data: Dict[str, HttpData] = {}
        js_collector = JsContentCollector()

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            async def handle_request(request: Request) -> None:
                """Capture outgoing HTTP requests."""
                req_url = request.url
                try:
                    headers = dict(request.headers)
                    resource_type = getattr(request, "resource_type", "") or ""

                    body: Optional[str] = None
                    if request.method in ["POST", "PUT", "PATCH"]:
                        try:
                            post_data = request.post_data
                            if post_data:
                                if len(post_data) > MAX_BODY_SIZE:
                                    body = post_data[:MAX_BODY_SIZE] + "... [TRUNCATED]"
                                else:
                                    body = post_data
                        except Exception:
                            pass

                    if req_url not in http_data:
                        http_data[req_url] = {}

                    http_data[req_url]["request"] = {
                        "method": request.method,
                        "headers": headers,
                        "body": body,
                        "resource_type": resource_type,
                    }
                except Exception as e:
                    logger.warning(
                        "Request interception error", error=str(e), url=req_url
                    )

            async def handle_response(response: Response) -> None:
                """Capture incoming HTTP responses using parser registry."""
                resp_url = response.url
                try:
                    headers = dict(response.headers)
                    content_type = headers.get("content-type", "")

                    # Read body once
                    body_bytes = await response.body()

                    # Collect JavaScript content
                    js_collector.add_from_response(resp_url, content_type, body_bytes)

                    # Create ResponseData for parser
                    response_data = ResponseData(
                        url=resp_url,
                        status=response.status,
                        content_type=content_type,
                        headers=headers,
                        body=body_bytes,
                    )

                    # Get appropriate parser and parse
                    parser = self._parser_registry.get_parser(content_type)
                    parsed = await parser.parse(response_data)

                    # Extract body from parsed result
                    body: Optional[Any] = parsed["body"] if parsed else None

                    if resp_url not in http_data:
                        http_data[resp_url] = {}

                    http_data[resp_url]["response"] = {
                        "status": response.status,
                        "headers": headers,
                        "body": body,
                    }
                except Exception as e:
                    logger.warning(
                        "Response interception error", error=str(e), url=resp_url
                    )

            page.on("request", handle_request)
            page.on("response", handle_response)

            try:
                await page.goto(url, wait_until="networkidle", timeout=PAGE_TIMEOUT_MS)

                # Collect inline scripts
                await js_collector.collect_inline(page, url)

                elements = await page.locator("a").all()
                for element in elements:
                    href = await element.get_attribute("href")
                    if href:
                        links.add(href)
                        params = parse_query_params(href)
                        if href not in http_data:
                            http_data[href] = {}
                        http_data[href]["parameters"] = params if params else None

            except Exception as e:
                logger.error("Crawl error", error=str(e), url=url)
            finally:
                await context.close()
                await browser.close()

        return list(links), http_data, js_collector.get_contents()
