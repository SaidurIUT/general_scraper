# scrapers/sitemap_parser.py

"""Sitemap parser for extracting URLs from sitemap.xml files."""
import aiohttp
import xml.etree.ElementTree as ET
from typing import List, Optional
from urllib.parse import urljoin

class SitemapParser:
    """Parse sitemap.xml files to extract URLs."""
    
    def __init__(self, base_url: str):
        """
        Initialize sitemap parser.
        
        Args:
            base_url: The base URL of the website
        """
        self.base_url = base_url.rstrip('/')
        
    async def fetch_sitemap(self) -> Optional[str]:
        """
        Fetch sitemap.xml content.
        
        Returns:
            Optional[str]: Sitemap content or None if not found
        """
        sitemap_urls = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap_index.xml",
            f"{self.base_url}/sitemap-index.xml",
        ]
        
        async with aiohttp.ClientSession() as session:
            for sitemap_url in sitemap_urls:
                try:
                    async with session.get(sitemap_url, timeout=10) as response:
                        if response.status == 200:
                            content = await response.text()
                            print(f"✅ Found sitemap: {sitemap_url}")
                            return content
                except Exception as e:
                    continue
        
        print("❌ No sitemap.xml found")
        return None
    
    def parse_sitemap(self, sitemap_content: str) -> List[str]:
        """
        Parse sitemap XML and extract URLs.
        
        Args:
            sitemap_content: XML content of the sitemap
            
        Returns:
            List[str]: List of URLs found in sitemap
        """
        urls = []
        
        try:
            root = ET.fromstring(sitemap_content)
            
            # Handle sitemap index (contains references to other sitemaps)
            namespaces = {
                'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                'xhtml': 'http://www.w3.org/1999/xhtml'
            }
            
            # Look for <loc> tags in both regular sitemaps and sitemap indexes
            for loc in root.findall('.//sm:loc', namespaces):
                url = loc.text.strip() if loc.text else None
                if url:
                    urls.append(url)
            
            # Fallback: try without namespace
            if not urls:
                for loc in root.findall('.//loc'):
                    url = loc.text.strip() if loc.text else None
                    if url:
                        urls.append(url)
            
            print(f"📄 Parsed {len(urls)} URLs from sitemap")
            
        except ET.ParseError as e:
            print(f"❌ Error parsing sitemap XML: {e}")
            
        return urls
    
    async def get_all_urls(self) -> List[str]:
        """
        Fetch and parse sitemap to get all URLs.
        
        Returns:
            List[str]: List of all URLs from sitemap, or empty list if no sitemap
        """
        sitemap_content = await self.fetch_sitemap()
        
        if not sitemap_content:
            return []
        
        urls = self.parse_sitemap(sitemap_content)
        
        # If we got sitemap index, fetch individual sitemaps
        if urls and all('.xml' in url for url in urls[:5]):
            print("🔗 Sitemap index detected, fetching individual sitemaps...")
            all_urls = []
            
            async with aiohttp.ClientSession() as session:
                for sitemap_url in urls:
                    try:
                        async with session.get(sitemap_url, timeout=10) as response:
                            if response.status == 200:
                                content = await response.text()
                                sub_urls = self.parse_sitemap(content)
                                all_urls.extend(sub_urls)
                    except Exception as e:
                        print(f"⚠️  Failed to fetch {sitemap_url}: {e}")
                        continue
            
            return all_urls
        
        return urls