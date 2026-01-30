# scrapers/content_extractor.py

"""Content extractor - extracts and cleans text without LLM."""
from typing import Dict, Optional
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from config import get_browser_config

class ContentExtractor:
    """Extract and clean content from web pages using traditional parsing."""
    
    def __init__(self):
        """Initialize content extractor."""
        pass
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.
        
        Args:
            text: Raw text
            
        Returns:
            str: Cleaned text
        """
        # Remove extra whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]
        return '\n'.join(lines)
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, str]:
        """
        Extract metadata from HTML.
        
        Args:
            soup: BeautifulSoup object
            url: Page URL
            
        Returns:
            Dict with metadata
        """
        metadata = {
            'url': url,
            'title': '',
            'description': '',
        }
        
        # Get title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()
        
        # Get meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            metadata['description'] = meta_desc['content'].strip()
        
        return metadata
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main content from HTML, removing navigation, footer, etc.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            str: Main content text
        """
        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 
                         'aside', 'iframe', 'noscript']):
            tag.decompose()
        
        # Remove elements with common class/id names for non-content
        unwanted_selectors = [
            {'class': lambda x: x and any(word in ' '.join(x).lower() 
                                         for word in ['nav', 'menu', 'sidebar', 
                                                     'footer', 'header', 'cookie',
                                                     'banner', 'ad', 'social'])},
            {'id': lambda x: x and any(word in x.lower() 
                                       for word in ['nav', 'menu', 'sidebar', 
                                                   'footer', 'header', 'cookie',
                                                   'banner'])},
        ]
        
        for selector in unwanted_selectors:
            for element in soup.find_all(**selector):
                element.decompose()
        
        # Try to find main content area
        main_content = None
        
        # Look for common content containers
        for selector in [
            soup.find('main'),
            soup.find('article'),
            soup.find('div', class_=lambda x: x and 'content' in x.lower()),
            soup.find('div', id=lambda x: x and 'content' in x.lower()),
        ]:
            if selector:
                main_content = selector
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body')
        
        if not main_content:
            return ""
        
        # Extract text
        text = main_content.get_text(separator='\n', strip=True)
        return self._clean_text(text)
    
    def _detect_page_type(self, url: str, title: str, content: str) -> str:
        """
        Detect the type of page based on URL and content.
        
        Args:
            url: Page URL
            title: Page title
            content: Page content
            
        Returns:
            str: Detected page type
        """
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()[:500]  # Check first 500 chars
        
        # Define patterns for different page types
        patterns = {
            'Privacy Policy': ['privacy', 'privacy-policy'],
            'Terms of Service': ['terms', 'tos', 'terms-of-service', 'terms-and-conditions'],
            'Cookie Policy': ['cookie', 'cookies'],
            'About Us': ['about', 'about-us'],
            'Contact': ['contact', 'contact-us'],
            'FAQ': ['faq', 'frequently-asked'],
            'Data Protection': ['data-protection', 'gdpr', 'data-privacy'],
            'Acceptable Use': ['acceptable-use', 'aup'],
            'Legal': ['legal', 'compliance'],
        }
        
        for page_type, keywords in patterns.items():
            if any(keyword in url_lower or keyword in title_lower 
                   for keyword in keywords):
                return page_type
        
        return 'General'
    
    async def extract(self, url: str) -> Optional[Dict]:
        """
        Extract content from a URL.
        
        Args:
            url: URL to extract content from
            
        Returns:
            Dict with extracted content or None if failed
        """
        print(f"   📥 Extracting: {url}")
        
        async with AsyncWebCrawler(config=get_browser_config()) as crawler:
            result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                )
            )
            
            if not result.success:
                print(f"     ❌ Failed to fetch page")
                return None
            
            try:
                soup = BeautifulSoup(result.html, 'lxml')
                
                # Extract metadata
                metadata = self._extract_metadata(soup, url)
                
                # Extract main content
                content = self._extract_main_content(soup)
                
                if not content or len(content) < 50:
                    print(f"     ⚠️  Content too short or empty")
                    return None
                
                # Detect page type
                page_type = self._detect_page_type(
                    url, 
                    metadata['title'], 
                    content
                )
                
                data = {
                    'url': url,
                    'title': metadata['title'],
                    'description': metadata['description'],
                    'page_type': page_type,
                    'content': content,
                    'word_count': len(content.split()),
                }
                
                print(f"     ✅ Extracted: {page_type} ({data['word_count']} words)")
                return data
                
            except Exception as e:
                print(f"     ❌ Extraction error: {e}")
                return None