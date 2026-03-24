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
            'privacy', 'policy', 'policies', 'terms', 'legal',
            'about', 'contact', 'faq', 'help', 'support',
            'cookie', 'gdpr', 'compliance', 'data-protection',
            'acceptable-use', 'tos', 'terms-of-service'
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

    async def filter_urls(self, urls: List[str]) -> List[str]:
        if not urls:
            return []

        if self.mode == "manual":
            print(f"⚙️  Manual filtering with {len(self.manual_keywords)} keywords...")
            return self._keyword_fallback(urls)

        return await self._filter_urls_with_llm(urls)

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
                else:
                    # LLM returned empty — fall back for this batch
                    print(f"⚠️  Batch {i // batch_size + 1} LLM returned empty, using keyword fallback...")
                    all_relevant_urls.extend(self._keyword_fallback(batch))
            except Exception as e:
                print(f"⚠️  Batch {i // batch_size + 1} LLM failed ({e}), using keyword fallback...")
                all_relevant_urls.extend(self._keyword_fallback(batch))

        return list(set(all_relevant_urls))

    async def _call_llm_api(self, urls: List[str]) -> List[str]:
        llm_config = get_llm_config()
        prompt = f"""Identify relevant URLs for: {self.search_prompt}

        URLs:
        {chr(10).join(f"- {url}" for url in urls)}

        Return JSON structure: {{"relevant_urls": ["url1", "url2"], "reasoning": "str"}}
        """

        base_url = llm_config.get('base_url', 'http://localhost:11434')
        model = llm_config.get('provider', 'phi4-mini-reasoning').replace('ollama/', '')

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False, "format": "json"},
                timeout=aiohttp.ClientTimeout(total=10, connect=3)  # fail fast when LLM is down
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    data = json.loads(result.get('response', '{}'))
                    return data.get('relevant_urls', [])
                return []

    def _keyword_fallback(self, urls: List[str]) -> List[str]:
        filtered = []
        for url in urls:
            url_lower = url.lower()
            if any(kw.lower() in url_lower for kw in self.manual_keywords):
                filtered.append(url)

        # If nothing matched keywords, return all URLs so content extraction can decide
        if not filtered:
            print("⚠️  No keyword matches found — returning all URLs for content-based filtering")
            return urls

        return filtered

    async def get_homepage_links(self, start_url: str) -> List[str]:
        async with AsyncWebCrawler(config=get_browser_config()) as crawler:
            result = await crawler.arun(url=start_url, config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS))
            if result.success:
                return self._extract_links_from_html(result.html, start_url)
            return []