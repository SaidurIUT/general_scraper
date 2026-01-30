# scrapers/url_filter.py

"""URL filter using LLM to identify relevant pages."""
import json
from typing import List
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup
from config import get_browser_config, get_llm_config, get_search_prompt

class URLFilter:
    """Filter URLs using LLM based on relevance to search prompt."""
    
    def __init__(self):
        """Initialize URL filter."""
        self.search_prompt = get_search_prompt()
    
    def _extract_links_from_html(self, html_content: str, base_url: str) -> List[str]:
        """
        Extract all links from HTML content.
        
        Args:
            html_content: Raw HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            List[str]: List of absolute URLs
        """
        soup = BeautifulSoup(html_content, 'lxml')
        links = []
        
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = base_url.rstrip('/') + href
            elif not href.startswith('http'):
                continue
            
            # Filter out anchors, mailto, tel, etc.
            if href.startswith(('http://', 'https://')):
                links.append(href)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        return unique_links
    
    
    async def filter_from_homepage(self, start_url: str) -> List[str]:
        """
        Extract links from homepage and filter using LLM.
        
        Args:
            start_url: The homepage URL
            
        Returns:
            List[str]: Filtered list of relevant URLs
        """
        print("🌐 Fetching homepage links...")
        
        async with AsyncWebCrawler(config=get_browser_config()) as crawler:
            result = await crawler.arun(
                url=start_url,
                config=CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                )
            )
            
            if not result.success:
                print("❌ Failed to fetch homepage")
                return []
            
            # Extract all links from HTML
            all_links = self._extract_links_from_html(result.html, start_url)
            print(f"📋 Found {len(all_links)} total links on homepage")
            
            if not all_links:
                return []
            
            # Use LLM to filter relevant URLs
            return await self._filter_urls_with_llm(all_links)
    
    async def filter_from_sitemap(self, sitemap_urls: List[str]) -> List[str]:
        """
        Filter URLs from sitemap using LLM.
        
        Args:
            sitemap_urls: List of URLs from sitemap
            
        Returns:
            List[str]: Filtered list of relevant URLs
        """
        print(f"🔍 Filtering {len(sitemap_urls)} URLs from sitemap...")
        return await self._filter_urls_with_llm(sitemap_urls)
    
    async def _filter_urls_with_llm(self, urls: List[str]) -> List[str]:
        """
        Use LLM to filter URLs based on relevance.
        
        Args:
            urls: List of URLs to filter
            
        Returns:
            List[str]: Filtered URLs
        """
        if not urls:
            return []
        
        # If too many URLs, process in batches
        batch_size = 100
        all_relevant_urls = []
        
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            
            try:
                # Call LLM directly without using crawler
                relevant_urls = await self._call_llm_api(batch)
                
                if relevant_urls:
                    print(f"🤖 LLM selected {len(relevant_urls)} URLs from batch {i//batch_size + 1}")
                    all_relevant_urls.extend(relevant_urls)
                        
            except Exception as e:
                print(f"⚠️  LLM filtering failed: {e}")
                # Fallback: use simple keyword matching
                all_relevant_urls.extend(self._keyword_fallback(batch))
        
        return list(set(all_relevant_urls))  # Remove duplicates
    
    async def _call_llm_api(self, urls: List[str]) -> List[str]:
        """
        Call LLM API directly to filter URLs.
        
        Args:
            urls: List of URLs to filter
            
        Returns:
            List[str]: Filtered relevant URLs
        """
        import aiohttp
        from config import get_llm_config
        
        llm_config = get_llm_config()
        
        # Create prompt
        prompt = f"""You are given a list of URLs from a website. Your task is to identify which URLs are relevant to this search criteria:

{self.search_prompt}

From the following URLs, select ONLY those that are relevant:

{chr(10).join(f"- {url}" for url in urls)}

Return your response as a JSON object with this exact structure:
{{
  "relevant_urls": ["url1", "url2", ...],
  "reasoning": "brief explanation of why these URLs were selected"
}}

Return ONLY the JSON object, no other text."""

        try:
            # Prepare API request
            base_url = llm_config.get('base_url', 'http://localhost:11434')
            model = llm_config.get('provider', 'phi4-mini-reasoning')
            
            # Remove "ollama/" prefix if present
            if model.startswith('ollama/'):
                model = model[7:]
            
            # Call Ollama API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get('response', '{}')
                        
                        # Parse JSON response
                        data = json.loads(response_text)
                        relevant_urls = data.get('relevant_urls', [])
                        reasoning = data.get('reasoning', '')
                        
                        if reasoning:
                            print(f"💭 Reasoning: {reasoning[:100]}...")
                        
                        return relevant_urls
                    else:
                        print(f"⚠️  LLM API returned status {response.status}")
                        return []
                        
        except Exception as e:
            print(f"⚠️  LLM API call failed: {e}")
            raise
    
    def _keyword_fallback(self, urls: List[str]) -> List[str]:
        """
        Fallback keyword-based filtering if LLM fails.
        
        Args:
            urls: List of URLs
            
        Returns:
            List[str]: URLs matching keywords
        """
        keywords = [
            'privacy', 'policy', 'policies', 'terms', 'legal', 
            'about', 'contact', 'faq', 'help', 'support',
            'cookie', 'gdpr', 'compliance', 'data-protection',
            'acceptable-use', 'tos', 'terms-of-service'
        ]
        
        filtered = []
        for url in urls:
            url_lower = url.lower()
            if any(keyword in url_lower for keyword in keywords):
                filtered.append(url)
        
        print(f"⚙️  Fallback: matched {len(filtered)} URLs by keywords")
        return filtered