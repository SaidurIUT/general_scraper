"""
Policy Scraper - Main Entry Point

This scraper intelligently extracts company policies and documents from websites.
It uses LLM only for URL filtering, and traditional parsing for content extraction.

Usage:
    python main.py <URL>                    # Scrape single URL
    python main.py urls.txt                 # Scrape multiple URLs from file
    python main.py <URL> --format json      # Save as JSON only
    python main.py <URL> --format all       # Save in all formats
"""

import sys
import os
import asyncio
import time
from datetime import datetime
from dotenv import load_dotenv
from scrapers import SitemapParser, URLFilter, ContentExtractor
from utils import FileHandler, URLUtils

# Load environment variables
load_dotenv()

class PolicyScraper:
    """Main scraper orchestrator."""
    
    def __init__(self, output_format='all'):
        """
        Initialize scraper.
        
        Args:
            output_format: 'json', 'text', 'markdown', or 'all'
        """
        self.url_filter = URLFilter()
        self.content_extractor = ContentExtractor()
        self.file_handler = FileHandler()
        self.output_format = output_format
    
    async def scrape(self, url: str) -> None:
        """
        Scrape a single website.
        
        Args:
            url: The website URL to scrape
        """
        # Start timing for this website
        scrape_start_time = time.time()
        
        print("\n" + "=" * 80)
        print(f"🕷️  Starting scrape for: {url}")
        print("=" * 80)
        
        if not URLUtils.is_valid_url(url):
            print(f"❌ Invalid URL: {url}")
            return
        
        # Get domain name for file naming
        domain_name = URLUtils.get_domain_name(url)
        
        # PHASE 1: Check for sitemap and get URLs
        print("\n📋 PHASE 1: URL Discovery")
        print("-" * 80)
        
        sitemap_parser = SitemapParser(url)
        sitemap_urls = await sitemap_parser.get_all_urls()
        
        if sitemap_urls:
            print(f"✅ Using sitemap with {len(sitemap_urls)} URLs")
            relevant_urls = await self.url_filter.filter_from_sitemap(sitemap_urls)
        else:
            print("📄 No sitemap found, using homepage links")
            relevant_urls = await self.url_filter.filter_from_homepage(url)
        
        if not relevant_urls:
            print("\n❌ No relevant URLs found. Try adjusting SEARCH_PROMPT in .env")
            return
        
        print(f"\n✨ Found {len(relevant_urls)} relevant URLs to scrape")
        
        # PHASE 2: Extract content from relevant URLs
        print("\n📥 PHASE 2: Content Extraction")
        print("-" * 80)
        
        scraped_data = []
        for idx, target_url in enumerate(relevant_urls, 1):
            print(f"\n[{idx}/{len(relevant_urls)}]")
            
            content = await self.content_extractor.extract(target_url)
            if content:
                scraped_data.append(content)
        
        if not scraped_data:
            print("\n❌ No content extracted")
            return
        
        # Calculate statistics
        page_types = {}
        for item in scraped_data:
            ptype = item.get('page_type', 'Unknown')
            page_types[ptype] = page_types.get(ptype, 0) + 1
        
        total_words = sum(item.get('word_count', 0) for item in scraped_data)
        scrape_elapsed = time.time() - scrape_start_time
        
        # Prepare statistics dictionary
        stats = {
            'website': url,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'urls_discovered': len(sitemap_urls) if sitemap_urls else 'N/A',
            'relevant_urls': len(relevant_urls),
            'pages_scraped': len(scraped_data),
            'total_words': total_words,
            'page_types': page_types,
            'total_time': scrape_elapsed
        }
        
        # PHASE 3: Save results
        print("\n💾 PHASE 3: Saving Results")
        print("-" * 80)
        
        if self.output_format == 'all':
            files = self.file_handler.save_all_formats(scraped_data, domain_name, stats)
            print(f"\n✅ Saved to folder: scraped_data/{domain_name}/")
            print("\n📄 Files created:")
            for format_name, filepath in files.items():
                # Get just the filename for cleaner display
                filename = os.path.basename(filepath)
                print(f"   - {filename}")
        elif self.output_format == 'json':
            filepath = self.file_handler.save_json(scraped_data, domain_name)
            summary_path = self.file_handler.save_summary(domain_name, stats)
            print(f"\n✅ Saved to folder: scraped_data/{domain_name}/")
            print(f"   - {os.path.basename(filepath)}")
            print(f"   - {os.path.basename(summary_path)}")
        elif self.output_format == 'text':
            filepath = self.file_handler.save_text(scraped_data, domain_name)
            summary_path = self.file_handler.save_summary(domain_name, stats)
            print(f"\n✅ Saved to folder: scraped_data/{domain_name}/")
            print(f"   - {os.path.basename(filepath)}")
            print(f"   - {os.path.basename(summary_path)}")
        elif self.output_format == 'markdown':
            filepath = self.file_handler.save_markdown(scraped_data, domain_name)
            summary_path = self.file_handler.save_summary(domain_name, stats)
            print(f"\n✅ Saved to folder: scraped_data/{domain_name}/")
            print(f"   - {os.path.basename(filepath)}")
            print(f"   - {os.path.basename(summary_path)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 SCRAPING SUMMARY")
        print("=" * 80)
        print(f"URLs Discovered: {stats['urls_discovered']}")
        print(f"Relevant URLs: {stats['relevant_urls']}")
        print(f"Pages Scraped: {stats['pages_scraped']}")
        print(f"Total Words: {stats['total_words']:,}")
        print("\nPage Types:")
        for ptype, count in sorted(page_types.items()):
            print(f"  - {ptype}: {count}")
        print("=" * 80)
        print(f"⏱️  Total time: {scrape_elapsed:.2f} seconds")

async def main():
    """Main function."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    # Parse arguments
    arg = sys.argv[1]
    output_format = 'all'
    
    if '--format' in sys.argv:
        format_idx = sys.argv.index('--format')
        if format_idx + 1 < len(sys.argv):
            output_format = sys.argv[format_idx + 1]
    
    # Validate format
    if output_format not in ['json', 'text', 'markdown', 'all']:
        print(f"❌ Invalid format: {output_format}")
        print("Valid formats: json, text, markdown, all")
        sys.exit(1)
    
    scraper = PolicyScraper(output_format=output_format)
    
    # Start timer
    start_time = time.time()
    
    # Handle file input or single URL
    if arg.endswith('.txt'):
        with open(arg, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        print(f"📚 Processing {len(urls)} URLs from file")
        for url in urls:
            await scraper.scrape(url)
    else:
        await scraper.scrape(arg)
    
    # Print total time
    elapsed = time.time() - start_time
    print(f"\n⏱️  Total time: {elapsed:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())