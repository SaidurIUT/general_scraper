# scrapers/url_filter.py

"""URL filter using LLM to identify relevant pages."""
import json
import aiohttp
from typing import List, Optional
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup
from config import get_browser_config, get_llm_config, get_default_search_prompt

class URLFilter:
    def __init__(self, mode="llm", custom_prompt=None, manual_keywords=None):
        self.mode = mode
        self.search_prompt = custom_prompt or get_default_search_prompt()
        self.manual_keywords = manual_keywords or [
            # Policies & Legal
            'privacy', 'policy', 'policies', 'terms', 'legal', 'tos',
            'terms-of-service', 'terms-and-conditions', 'cookie',
            'gdpr', 'compliance', 'data-protection', 'acceptable-use',
            
            # Company Information
            'about', 'about-us', 'who-we-are', 'our-story', 'mission',
            'vision', 'values', 'team', 'leadership', 'company',
            'history', 'careers', 'culture',
            
            # Services & Products
            'services', 'what-we-do', 'solutions', 'offerings',
            'features', 'plans', 'pricing',
            
            # Support & Resources
            'contact', 'faq', 'help', 'support', 'resources',
            'documentation', 'docs', 'guide', 'tutorial',
            'how-to', 'getting-started', 'knowledge-base', 'kb',
            
            # Locations & Contact
            'location', 'locations', 'office', 'offices', 'branch',
            'store', 'stores', 'find-us', 'address', 'map',
            
            # Media & News
            'news', 'blog', 'press', 'media', 'updates',
            'announcements', 'events',
            
            # Community & Testimonials
            'testimonials', 'reviews', 'case-studies', 'success-stories',
            'community', 'partners', 'partnership',
            
            # Security & Trust
            'security', 'safety', 'trust', 'certification',
            'accreditation', 'compliance',
        ]
        
        # Exclusion patterns - URLs to always skip
        self.exclusion_patterns = [
            # E-commerce & Variable Content
            '/cart', '/checkout', '/order', '/purchase', '/buy',
            '/product/', '/item/', '/sku/', '/catalog/',
            
            # User-specific pages
            '/login', '/signup', '/register', '/logout', '/account',
            '/profile', '/dashboard', '/user/', '/my-',
            
            # Search & Filters
            '/search', '?search=', '?query=', '?filter=', '?sort=',
            '?page=', '?p=', '/page/', '/p/',
            
            # Media & Downloads
            '/download/', '/file/', '/attachment/', '/media/',
            
            # Admin & Backend
            '/admin/', '/wp-admin/', '/backend/', '/api/',
            
            # Social & External
            '/share/', '/redirect/', '/goto/', '/out/',
            
            # Duplicate content indicators
            '?utm_', '?ref=', '#', '/tag/', '/category/',
        ]
    
    def _extract_links_from_html(self, html_content: str, base_url: str) -> List[str]:
        soup = BeautifulSoup(html_content, 'lxml')
        links = []
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            if href.startswith('/'):
                href = base_url.rstrip('/') + href
            elif not href.startswith('http'):
                continue
            if href.startswith(('http://', 'https://')):
                links.append(href)
        return list(dict.fromkeys(links))
    
    def _should_exclude_url(self, url: str) -> bool:
        """
        Check if URL matches exclusion patterns.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if should exclude, False otherwise
        """
        url_lower = url.lower()
        return any(pattern in url_lower for pattern in self.exclusion_patterns)

    async def filter_urls(self, urls: List[str]) -> List[str]:
        if not urls:
            return []
        
        # First pass: Remove excluded URLs
        print(f"🔍 Pre-filtering {len(urls)} URLs...")
        filtered_urls = [url for url in urls if not self._should_exclude_url(url)]
        excluded_count = len(urls) - len(filtered_urls)
        
        if excluded_count > 0:
            print(f"   ✂️  Excluded {excluded_count} URLs (user pages, search, cart, etc.)")
        
        if not filtered_urls:
            print("   ⚠️  No URLs left after exclusion filtering")
            return []
        
        if self.mode == "manual":
            print(f"⚙️  Manual filtering with {len(self.manual_keywords)} keywords...")
            return self._keyword_fallback(filtered_urls)
        
        return await self._filter_urls_with_llm(filtered_urls)

    async def _filter_urls_with_llm(self, urls: List[str]) -> List[str]:
        batch_size = 100
        all_relevant_urls = []
        
        print(f"🤖 LLM filtering {len(urls)} URLs in batches of {batch_size}...")
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            try:
                relevant_urls = await self._call_llm_api(batch)
                if relevant_urls:
                    all_relevant_urls.extend(relevant_urls)
                    print(f"   ✅ Batch {i//batch_size + 1}: {len(relevant_urls)} relevant URLs")
            except Exception as e:
                print(f"   ⚠️  Batch {i//batch_size + 1} LLM failed, using keyword fallback...")
                fallback_urls = self._keyword_fallback(batch)
                all_relevant_urls.extend(fallback_urls)
                print(f"   ✅ Fallback: {len(fallback_urls)} relevant URLs")
        
        return list(set(all_relevant_urls))

    async def _call_llm_api(self, urls: List[str]) -> List[str]:
        llm_config = get_llm_config()
        prompt = f"""You are helping build a comprehensive knowledge base for a website chatbot.
The chatbot needs to answer ANY questions users might ask about the website, including:
- Company information (who they are, mission, history)
- Services and offerings
- Locations and contact information
- Policies (privacy, terms, legal)
- Support and FAQ content
- News and updates

Review these URLs and identify which ones contain INFORMATIONAL content that would help answer user questions.

INCLUDE URLs that contain:
- Company information and background
- Service/product descriptions (not individual items)
- Location and contact pages
- Policy and legal pages
- Support, help, FAQ, and documentation
- About pages, team, mission, values
- News, blog, press releases
- Guides, tutorials, resources

EXCLUDE URLs that are:
- Individual product/item pages
- User account pages
- Shopping cart/checkout
- Search results or filters
- Duplicate content with query parameters

URLs to review:
{chr(10).join(f"- {url}" for url in urls)}

Return ONLY a JSON object with this exact structure:
{{"relevant_urls": ["url1", "url2"], "reasoning": "brief explanation"}}
"""

        base_url = llm_config.get('base_url', 'http://localhost:11434')
        model = llm_config.get('provider', 'phi4-mini-reasoning').replace('ollama/', '')
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False, "format": "json"},
                timeout=aiohttp.ClientTimeout(total=90)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    data = json.loads(result.get('response', '{}'))
                    return data.get('relevant_urls', [])
                return []

    def _keyword_fallback(self, urls: List[str]) -> List[str]:
        """
        Fallback keyword-based filtering.
        
        Args:
            urls: List of URLs to filter
            
        Returns:
            List of relevant URLs based on keywords
        """
        filtered = []
        for url in urls:
            url_lower = url.lower()
            if any(kw.lower() in url_lower for kw in self.manual_keywords):
                filtered.append(url)
        return filtered

    async def get_homepage_links(self, start_url: str) -> List[str]:
        """Get links from homepage only."""
        async with AsyncWebCrawler(config=get_browser_config()) as crawler:
            result = await crawler.arun(url=start_url, config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS))
            if result.success:
                return self._extract_links_from_html(result.html, start_url)
            return []