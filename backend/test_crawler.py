import asyncio
import sys
import os

# Add backend directory to path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.crawler_service import CrawlerService

async def main():
    crawler = CrawlerService()
    url = "http://host3.dreamhack.games:17560/"
    print(f"Crawling {url}...")
    try:
        result = await crawler.crawl(url)
        print("Crawl Success!")
        print(f"Title: {result['title']}")
        print(f"Status: {result['status']}")
        print(f"Content Length: {result['content_length']}")
        print(f"Links Found: {len(result['links'])}")
        for link in result['links']:
            print(f" - {link}")
        print(f"Forms Found: {len(result['forms'])}")
        if result['forms']:
            print(f"First Form: {result['forms'][0]}")
        print(f"Standalone Inputs: {len(result['inputs'])}")
        
        print("\n--- Semantic Endpoints ---")
        print(f"Endpoints Found: {len(result['endpoints'])}")
        for i, ep in enumerate(result['endpoints']):
            print(f"[{i+1}] {ep['method']} {ep['url']}")
            if ep['parameters']:
                print(f"    Params: {[f'{p['name']}({p['type']})' for p in ep['parameters']]}")
        print("--------------------------")
    except Exception as e:
        print(f"Crawl Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
