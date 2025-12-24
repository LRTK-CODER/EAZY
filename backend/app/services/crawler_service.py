from typing import List, Set
from playwright.async_api import async_playwright

class CrawlerService:
    async def crawl(self, url: str) -> List[str]:
        """
        Crawls a single page and returns unique links found on that page.
        """
        links: Set[str] = set()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                # Basic navigation
                await page.goto(url, wait_until="networkidle")
                
                # Extract all hrefs
                elements = await page.locator("a").all()
                for element in elements:
                    href = await element.get_attribute("href")
                    if href:
                        # Simple normalization (MVP: just adding raw hrefs)
                        # In real world, we'd handle relative URLs here.
                        links.add(href)
                        
            except Exception as e:
                print(f"Crawl error: {e}")
            finally:
                await browser.close()
                
        return list(links)
