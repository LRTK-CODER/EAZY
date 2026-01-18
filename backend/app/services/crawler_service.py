"""CrawlerService - Web crawler with HTTP interception and parser delegation."""

from typing import Any, Dict, List, Optional, Set

from playwright.async_api import Request, Response, async_playwright

from app.core.constants import MAX_BODY_SIZE, PAGE_TIMEOUT_MS
from app.core.structured_logger import get_logger
from app.services.parsers import (
    HtmlResponseParser,
    ImageResponseParser,
    JsonResponseParser,
    ResponseData,
    ResponseParserRegistry,
)
from app.types.http import HttpData
from app.utils.url_parser import parse_query_params

logger = get_logger(__name__)


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

    async def crawl(self, url: str) -> tuple[List[str], Dict[str, HttpData]]:
        """Crawl a single page and capture HTTP data.

        Args:
            url: Target URL to crawl

        Returns:
            Tuple of:
            - List of unique URLs found
            - Dict mapping URL -> HttpData (request, response, parameters)
        """
        links: Set[str] = set()
        http_data: Dict[str, HttpData] = {}

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            async def handle_request(request: Request) -> None:
                """Capture outgoing HTTP requests."""
                req_url = request.url
                try:
                    headers = dict(request.headers)

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

                    # Create ResponseData for parser
                    response_data = ResponseData(
                        url=resp_url,
                        status=response.status,
                        content_type=content_type,
                        headers=headers,
                        body=await response.body(),
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

        return list(links), http_data
