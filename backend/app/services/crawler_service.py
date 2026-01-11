from typing import List, Set, Dict, Any, Optional
from playwright.async_api import async_playwright, Request, Response
import json
import base64

from app.utils.url_parser import parse_query_params
from app.core.structured_logger import get_logger

logger = get_logger(__name__)


class CrawlerService:
    """Web crawler using Playwright with HTTP interception."""

    MAX_BODY_SIZE = 10 * 1024  # 10KB limit

    async def crawl(self, url: str) -> tuple[List[str], Dict[str, Dict[str, Any]]]:
        """
        Crawl a single page and capture HTTP data.

        Args:
            url: Target URL to crawl

        Returns:
            Tuple of:
            - List of unique URLs found
            - Dict mapping URL -> {request, response} data
        """
        links: Set[str] = set()
        http_data: Dict[str, Dict[str, Any]] = {}

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            # Request interceptor
            async def handle_request(request: Request) -> None:
                """Capture outgoing HTTP requests."""
                try:
                    req_url = request.url
                    headers = dict(request.headers)

                    # Extract body (POST/PUT/PATCH only)
                    body: Optional[str] = None
                    if request.method in ["POST", "PUT", "PATCH"]:
                        try:
                            post_data = request.post_data
                            if post_data:
                                # Truncate if too large
                                if len(post_data) > self.MAX_BODY_SIZE:
                                    body = (
                                        post_data[: self.MAX_BODY_SIZE]
                                        + "... [TRUNCATED]"
                                    )
                                else:
                                    body = post_data
                        except Exception:
                            pass

                    # Store request data
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

            # Response interceptor
            async def handle_response(response: Response) -> None:
                """Capture incoming HTTP responses."""
                try:
                    resp_url = response.url
                    headers = dict(response.headers)

                    # Capture all common web content types
                    body: Optional[Any] = None
                    content_type = headers.get("content-type", "")

                    # Handle text-based responses (JSON, HTML, CSS, JS)
                    if any(
                        ct in content_type
                        for ct in [
                            "application/json",
                            "text/html",
                            "text/css",
                            "text/javascript",
                            "application/javascript",
                            "application/x-javascript",
                        ]
                    ):
                        try:
                            body_text = await response.text()

                            # Truncate if too large
                            if len(body_text) > self.MAX_BODY_SIZE:
                                body = (
                                    body_text[: self.MAX_BODY_SIZE] + "... [TRUNCATED]"
                                )
                            else:
                                # Try to parse as JSON for API responses
                                if "application/json" in content_type:
                                    try:
                                        body = json.loads(body_text)
                                    except json.JSONDecodeError:
                                        body = body_text
                                else:
                                    # HTML, CSS, JS responses stored as plain text
                                    body = body_text
                        except Exception:
                            pass

                    # Handle binary responses (images) - encode as Base64
                    elif "image/" in content_type:
                        try:
                            body_bytes = await response.body()

                            # Truncate if too large
                            if len(body_bytes) > self.MAX_BODY_SIZE:
                                body_bytes = body_bytes[: self.MAX_BODY_SIZE]

                            # Encode as Base64 string for JSON serialization
                            body = base64.b64encode(body_bytes).decode("utf-8")
                        except Exception:
                            pass

                    # Store response data
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

            # Register event listeners
            page.on("request", handle_request)
            page.on("response", handle_response)

            try:
                # Navigate to page
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Extract all <a> hrefs (existing logic)
                elements = await page.locator("a").all()
                for element in elements:
                    href = await element.get_attribute("href")
                    if href:
                        links.add(href)

                        # Parse query parameters
                        params = parse_query_params(href)

                        # Store in http_data
                        if href not in http_data:
                            http_data[href] = {}
                        http_data[href]["parameters"] = params if params else None

            except Exception as e:
                logger.error("Crawl error", error=str(e), url=url)
            finally:
                await context.close()
                await browser.close()

        return list(links), http_data
