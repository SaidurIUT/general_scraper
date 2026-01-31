# main.py

import sys
import argparse
import asyncio
import time
from datetime import datetime
from dotenv import load_dotenv
from scrapers import SitemapParser, URLFilter, ContentExtractor
from utils import FileHandler, URLUtils

load_dotenv()

class PolicyScraper:
    def __init__(self, args):
        self.args = args
        # Check if filter_manual was used. 
        # args.filter_manual is a list if provided, None if flag not used.
        is_manual = args.filter_manual is not None
        
        self.url_filter = URLFilter(
            mode="manual" if is_manual else "llm",
            custom_prompt=args.filter_llm if isinstance(args.filter_llm, str) else None,
            manual_keywords=args.filter_manual if (is_manual and len(args.filter_manual) > 0) else None
        )
        self.content_extractor = ContentExtractor()
        self.file_handler = FileHandler()

    async def scrape(self, url: str) -> None:
        scrape_start_time = time.time()
        domain_name = URLUtils.get_domain_name(url)
        
        print("\n" + "=" * 80)
        print(f"🕷️  Starting scrape for: {url}")
        print("=" * 80)

        # PHASE 1: URL Discovery
        sitemap_parser = SitemapParser(url)
        all_urls = await sitemap_parser.get_all_urls()
        
        source_name = "Sitemap"
        if not all_urls or len(all_urls) > self.args.max_sitemap:
            if len(all_urls) > self.args.max_sitemap:
                print(f"⚠️  Sitemap too large ({len(all_urls)} URLs). Max limit is {self.args.max_sitemap}.")
            print("🌐 Falling back to Homepage link extraction...")
            all_urls = await self.url_filter.get_homepage_links(url)
            source_name = "Homepage"

        print(f"📋 Found {len(all_urls)} potential links from {source_name}")
        
        relevant_urls = await self.url_filter.filter_urls(all_urls)
        print(f"✨ {len(relevant_urls)} relevant URLs identified")

        # PHASE 2: Content Extraction
        scraped_data = []
        for idx, target_url in enumerate(relevant_urls, 1):
            print(f"📥 [{idx}/{len(relevant_urls)}] Extracting: {target_url}")
            content = await self.content_extractor.extract(target_url)
            if content:
                scraped_data.append(content)

        # PHASE 3: Saving
        if scraped_data:
            stats = {
                'website': url,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'urls_discovered': len(all_urls),
                'relevant_urls': len(relevant_urls),
                'pages_scraped': len(scraped_data),
                'total_time': time.time() - scrape_start_time
            }
            self.file_handler.save_all_formats(scraped_data, domain_name, stats)
            print(f"\n✅ Success! Files saved in scraped_data/{domain_name}/")
        else:
            print("\n❌ No content was extracted from relevant URLs.")

async def main():
    parser = argparse.ArgumentParser(description="Policy Scraper v2 - Intelligent & Scalable")
    
    parser.add_argument("target", help="Website URL or .txt file containing URLs")
    
    parser.add_argument("--max-sitemap", type=int, default=500, 
                        help="Max allowed sitemap links before switching to homepage crawl (default: 500)")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--filter-llm", nargs='?', const=True, 
                        help="Use LLM for filtering. Can optionally pass a custom prompt string.")
    group.add_argument("--filter-manual", nargs='*', 
                        help="Skip LLM, use keyword filtering. Optional: pass specific keywords to use.")
    
    parser.add_argument("--format", choices=['json', 'text', 'markdown', 'all'], default='all',
                        help="Output file format")

    args = parser.parse_args()

    scraper = PolicyScraper(args)
    
    if args.target.endswith('.txt'):
        if not os.path.exists(args.target):
            print(f"❌ File not found: {args.target}")
            return
        with open(args.target, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        for url in urls:
            await scraper.scrape(url)
    else:
        await scraper.scrape(args.target)

if __name__ == "__main__":
    asyncio.run(main())