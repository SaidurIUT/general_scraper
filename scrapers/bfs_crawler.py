# scrapers/bfs_crawler.py

"""BFS (Breadth-First Search) crawler for comprehensive website exploration."""
import asyncio
from typing import List, Set, Dict, Optional
from collections import deque
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from config import get_browser_config

class BFSCrawler:
    """Breadth-First Search crawler for discovering all pages on a website."""
    
    def __init__(self, max_pages: int = 200, max_depth: int = 3):
        """
        Initialize BFS crawler.
        
        Args:
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum depth to crawl from start URL
        """
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.visited: Set[str] = set()
        self.discovered: Set[str] = set()
    
    def _is_same_domain(self, url: str, base_url: str) -> bool:
        """
        Check if URL belongs to the same domain as base URL.
        
        Args:
            url: URL to check
            base_url: Base URL to compare against
            
        Returns:
            bool: True if same domain, False otherwise
        """
        url_domain = urlparse(url).netloc
        base_domain = urlparse(base_url).netloc
        
        # Remove www. for comparison
        url_domain = url_domain.replace('www.', '')
        base_domain = base_domain.replace('www.', '')
        
        return url_domain == base_domain
    
    def _should_skip_url(self, url: str) -> bool:
        """
        Determine if URL should be skipped (binary files, non-HTML, etc.).
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if should skip, False otherwise
        """
        skip_extensions = {
            # Documents
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico',
            # Media
            '.mp4', '.mp3', '.avi', '.mov', '.wav',
            # Archives
            '.zip', '.tar', '.gz', '.rar',
            # Other
            '.css', '.js', '.xml', '.json'
        }
        
        url_lower = url.lower()
        
        # Check file extensions
        if any(url_lower.endswith(ext) for ext in skip_extensions):
            return True
        
        # Skip common non-content paths
        skip_patterns = [
            '/cdn-cgi/', '/wp-content/', '/wp-includes/',
            '/assets/', '/static/', '/media/', '/images/',
            '/css/', '/js/', '/fonts/',
            'mailto:', 'tel:', 'javascript:', '#'
        ]
        
        return any(pattern in url_lower for pattern in skip_patterns)
    
    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract all links from HTML content.
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            List of absolute URLs
        """
        soup = BeautifulSoup(html, 'lxml')
        links = []
        
        for anchor in soup.find_all('a', href=True):
            href = anchor['href'].strip()
            
            # Skip empty hrefs and anchors
            if not href or href.startswith('#'):
                continue
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                absolute_url = urljoin(base_url, href)
            elif href.startswith('http'):
                absolute_url = href
            else:
                # Handle relative paths
                absolute_url = urljoin(base_url, href)
            
            # Remove fragments
            absolute_url = absolute_url.split('#')[0]
            
            # Remove trailing slash for consistency
            if absolute_url.endswith('/') and absolute_url.count('/') > 3:
                absolute_url = absolute_url[:-1]
            
            links.append(absolute_url)
        
        return links
    
    async def crawl(self, start_url: str) -> List[str]:
        """
        Perform BFS crawl starting from the given URL.
        
        Args:
            start_url: Starting URL for crawl
            
        Returns:
            List of discovered URLs
        """
        print(f"\n🔍 Starting BFS crawl from: {start_url}")
        print(f"   Max pages: {self.max_pages}, Max depth: {self.max_depth}")
        
        # Queue: (url, depth)
        queue: deque = deque([(start_url, 0)])
        self.discovered.add(start_url)
        
        base_domain = urlparse(start_url).netloc
        
        async with AsyncWebCrawler(config=get_browser_config()) as crawler:
            while queue and len(self.visited) < self.max_pages:
                current_url, depth = queue.popleft()
                
                # Skip if already visited
                if current_url in self.visited:
                    continue
                
                # Skip if max depth reached
                if depth > self.max_depth:
                    continue
                
                # Skip if should skip URL
                if self._should_skip_url(current_url):
                    continue
                
                print(f"   🌐 [{len(self.visited) + 1}/{self.max_pages}] Depth {depth}: {current_url}")
                
                try:
                    result = await crawler.arun(
                        url=current_url,
                        config=CrawlerRunConfig(
                            cache_mode=CacheMode.BYPASS,
                            page_timeout=30000,
                        )
                    )
                    
                    if not result.success:
                        print(f"      ⚠️  Failed to fetch")
                        continue
                    
                    self.visited.add(current_url)
                    
                    # Extract links from page
                    links = self._extract_links(result.html, current_url)
                    new_links_count = 0
                    
                    for link in links:
                        # Only follow links on same domain
                        if not self._is_same_domain(link, start_url):
                            continue
                        
                        # Skip if already discovered
                        if link in self.discovered:
                            continue
                        
                        self.discovered.add(link)
                        queue.append((link, depth + 1))
                        new_links_count += 1
                    
                    print(f"      ✅ Found {new_links_count} new links")
                    
                    # Small delay to be respectful
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"      ❌ Error: {e}")
                    continue
        
        discovered_urls = list(self.discovered)
        print(f"\n✨ BFS crawl complete: {len(discovered_urls)} URLs discovered")
        
        return discovered_urls
    
    async def get_limited_homepage_links(self, start_url: str, limit: int = 50) -> List[str]:
        """
        Get limited links from homepage only (no BFS, just one page).
        Used as fallback when sitemap has too many URLs.
        
        Args:
            start_url: Homepage URL
            limit: Maximum number of links to extract
            
        Returns:
            List of URLs from homepage
        """
        print(f"\n🏠 Extracting links from homepage only (limit: {limit})")
        
        async with AsyncWebCrawler(config=get_browser_config()) as crawler:
            result = await crawler.arun(
                url=start_url,
                config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
            )
            
            if not result.success:
                print("   ❌ Failed to fetch homepage")
                return []
            
            links = self._extract_links(result.html, start_url)
            
            # Filter to same domain and remove unwanted URLs
            filtered_links = [
                link for link in links
                if self._is_same_domain(link, start_url)
                and not self._should_skip_url(link)
            ]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_links = []
            for link in filtered_links:
                if link not in seen:
                    seen.add(link)
                    unique_links.append(link)
            
            # Limit to requested number
            result_links = unique_links[:limit]
            
            print(f"   ✅ Extracted {len(result_links)} unique links from homepage")
            return result_links