import asyncio
import sys
import os

# Add backend directory to path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.crawler_service import CrawlerService

async def main():
    crawler = CrawlerService()
    url = "http://host8.dreamhack.games:17113/"
    print(f"Crawling {url}...")
    try:
        result = await crawler.crawl(url)
        print(f"Crawl Finished! Total Pages: {result['pages_crawled']}")
        
        for i, page_res in enumerate(result['results']):
            print(f"\n[Page {i+1}] {page_res['url']}")
            print(f"  Title: {page_res.get('title', 'N/A')}")
            print(f"  Status: {page_res.get('status', 'Error')}")
            print(f"  Links: {len(page_res.get('links', []))}")
            
            endpoints = page_res.get('endpoints', [])
            if endpoints:
                print(f"  Endpoints: {len(endpoints)}")
                for ep in endpoints:
                    print(f"    - {ep['method']} {ep['url']}")
        
    except Exception as e:
        print(f"Crawl Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
