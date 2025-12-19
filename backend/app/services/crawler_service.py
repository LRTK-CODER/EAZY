from app.services.semantic_parser import SemanticParser
from typing import Dict, Any, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import structlog

logger = structlog.get_logger()

class CrawlerService:
    """
    Service for active crawling using Playwright.
    Handles browser lifecycle, navigation, and DOM extraction.
    """

    def __init__(self):
        self.parser = SemanticParser()

    async def crawl(self, url: str) -> Dict[str, Any]:
        """
        Visits a URL, renders JavaScript, and extracts page data.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            
            try:
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ... EAZY-Crawler"
                )
                
                # Intercept logic
                captured_requests = []
                
                async def handle_request(request):
                    try:
                        # Filter out resources to reduce noise
                        if request.resource_type in ["image", "stylesheet", "font", "media"]:
                            return
                            
                        # Capture relevant details
                        captured_requests.append({
                            "method": request.method,
                            "url": request.url,
                            "headers": request.headers,
                            "body": request.post_data
                        })
                    except Exception:
                        pass # Ignore failing captures

                page = await context.new_page()
                page.on("request", handle_request)
                
                logger.info("crawler.visiting", url=url)
                
                # Navigate
                response = await page.goto(url, wait_until="networkidle", timeout=30000)
                
                if not response:
                    raise Exception("No response received from target")
                
                status_code = response.status
                title = await page.title()
                content = await page.content()
                
                # Advanced DOM Parsing... (Existing Code)
                dom_data = await page.evaluate("""
                    () => {
                        const forms = Array.from(document.forms).map(form => {
                            const inputs = Array.from(form.elements).filter(el => el.name).map(el => ({
                                name: el.name,
                                type: el.type || 'text',
                                value: el.value || ''
                            }));
                            return {
                                action: form.action || window.location.href,
                                method: form.method || 'GET',
                                inputs: inputs
                            };
                        });

                        const uniqueLinks = Array.from(new Set(
                            Array.from(document.querySelectorAll('a'))
                                .map(a => a.href)
                                .filter(href => href && !href.startsWith('javascript:') && !href.startsWith('mailto:'))
                        ));

                        // Collect standalone inputs (not in forms, common in SPAs)
                        const inputs = Array.from(document.querySelectorAll('input, textarea, select'))
                            .filter(el => !el.form && el.name)
                            .map(el => ({
                                name: el.name,
                                type: el.type || 'text',
                                value: el.value || ''
                            }));

                        return { forms, links: uniqueLinks, inputs };
                    }
                """)

                # Process Captured Requests with Semantic Parser
                endpoints = []
                seen_hashes = set()
                
                for req in captured_requests:
                    parsed = self.parser.parse_request(
                        method=req['method'],
                        url=req['url'],
                        headers=req['headers'],
                        body=req['body']
                    )
                    
                    if parsed['spec_hash'] not in seen_hashes:
                        seen_hashes.add(parsed['spec_hash'])
                        endpoints.append(parsed)

                logger.info("crawler.success", url=url, title=title, 
                            endpoints_count=len(endpoints))

                return {
                    "url": url,
                    "status": status_code,
                    "title": title,
                    "content_length": len(content),
                    "links": dom_data['links'],
                    "forms": dom_data['forms'],
                    "inputs": dom_data['inputs'],
                    "endpoints": endpoints  # New Semantic Endpoints
                }

            except Exception as e:
                logger.error("crawler.failed", url=url, error=str(e))
                raise e
            finally:
                await browser.close()
