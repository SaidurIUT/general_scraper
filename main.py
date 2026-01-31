"""
Policy Scraper - Main Entry Point

This scraper intelligently extracts company policies and documents from websites.
It uses LLM or manual keyword filtering for URL selection, and traditional parsing 
for content extraction. Scraped data is stored in PostgreSQL with pgvector embeddings 
for similarity search.

Usage:
    python main.py <URL>                    # Scrape single URL
    python main.py urls.txt                 # Scrape multiple URLs from file
    python main.py <URL> --format json      # Save as JSON only
    python main.py <URL> --format all       # Save in all formats
    python main.py <URL> --no-db            # Skip database storage (files only)
    python main.py <URL> --filter-manual    # Use keyword filtering instead of LLM
    python main.py <URL> --filter-llm "custom prompt"  # Use LLM with custom prompt
"""

import sys
import os
import argparse
import asyncio
import time
from datetime import datetime
from dotenv import load_dotenv
from scrapers import SitemapParser, URLFilter, ContentExtractor
from utils import FileHandler, URLUtils, DatabaseHandler

load_dotenv()


class PolicyScraper:
    """Main scraper orchestrator."""
    
    def __init__(self, args):
        """
        Initialize scraper.

        Args:
            args: Parsed command line arguments
        """
        self.args = args
        
        # Check if filter_manual was used
        # args.filter_manual is a list if provided, None if flag not used
        is_manual = args.filter_manual is not None
        
        self.url_filter = URLFilter(
            mode="manual" if is_manual else "llm",
            custom_prompt=args.filter_llm if isinstance(args.filter_llm, str) else None,
            manual_keywords=args.filter_manual if (is_manual and len(args.filter_manual) > 0) else None
        )
        self.content_extractor = ContentExtractor()
        self.file_handler = FileHandler()
        self.db_handler = DatabaseHandler() if args.use_database else None
    
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
            if all_urls and len(all_urls) > self.args.max_sitemap:
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
            'urls_discovered': len(all_urls),
            'relevant_urls': len(relevant_urls),
            'pages_scraped': len(scraped_data),
            'total_words': total_words,
            'page_types': page_types,
            'total_time': scrape_elapsed
        }
        
        # PHASE 3: Save results
        print("\n💾 PHASE 3: Saving Results")
        print("-" * 80)

        # Save to database if enabled
        if self.args.use_database and self.db_handler:
            print("\n📊 Saving to PostgreSQL database...")
            db_success = self.db_handler.save_all(scraped_data, url, domain_name, stats)
            if db_success:
                print("✅ Successfully saved to database with vector embeddings")
            else:
                print("⚠️  Database save failed, data will only be saved to files")

        # Save to files (always save as backup or if database disabled)
        print("\n📁 Saving to files...")
        output_format = self.args.format
        
        if output_format == 'all':
            files = self.file_handler.save_all_formats(scraped_data, domain_name, stats)
            print(f"✅ Saved to folder: scraped_data/{domain_name}/")
            print("\n📄 Files created:")
            for format_name, filepath in files.items():
                filename = os.path.basename(filepath)
                print(f"   - {filename}")
        elif output_format == 'json':
            filepath = self.file_handler.save_json(scraped_data, domain_name)
            summary_path = self.file_handler.save_summary(domain_name, stats)
            print(f"✅ Saved to folder: scraped_data/{domain_name}/")
            print(f"   - {os.path.basename(filepath)}")
            print(f"   - {os.path.basename(summary_path)}")
        elif output_format == 'text':
            filepath = self.file_handler.save_text(scraped_data, domain_name)
            summary_path = self.file_handler.save_summary(domain_name, stats)
            print(f"✅ Saved to folder: scraped_data/{domain_name}/")
            print(f"   - {os.path.basename(filepath)}")
            print(f"   - {os.path.basename(summary_path)}")
        elif output_format == 'markdown':
            filepath = self.file_handler.save_markdown(scraped_data, domain_name)
            summary_path = self.file_handler.save_summary(domain_name, stats)
            print(f"✅ Saved to folder: scraped_data/{domain_name}/")
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
    parser = argparse.ArgumentParser(
        description="Policy Scraper - Intelligent & Scalable",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("target", help="Website URL or .txt file containing URLs")
    
    parser.add_argument("--max-sitemap", type=int, default=500, 
                        help="Max allowed sitemap links before switching to homepage crawl (default: 500)")
    
    # Filter mode options (mutually exclusive)
    filter_group = parser.add_mutually_exclusive_group()
    filter_group.add_argument("--filter-llm", nargs='?', const=True, 
                              help="Use LLM for filtering. Can optionally pass a custom prompt string.")
    filter_group.add_argument("--filter-manual", nargs='*', 
                              help="Skip LLM, use keyword filtering. Optional: pass specific keywords to use.")
    
    # Output options
    parser.add_argument("--format", choices=['json', 'text', 'markdown', 'all'], default='all',
                        help="Output file format (default: all)")
    
    # Database options
    parser.add_argument("--no-db", dest='use_database', action='store_false',
                        help="Skip database storage (files only)")
    parser.set_defaults(use_database=True)

    args = parser.parse_args()
    
    if not args.use_database:
        print("ℹ️  Database storage disabled (--no-db flag)")

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