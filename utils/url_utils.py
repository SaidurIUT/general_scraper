"""URL utility functions."""
from urllib.parse import urlparse

class URLUtils:
    """Utility functions for URL manipulation."""
    
    @staticmethod
    def get_domain_name(url: str) -> str:
        """
        Extract clean domain name from URL.
        
        Args:
            url: Full URL
            
        Returns:
            str: Clean domain name
            
        Examples:
            https://www.example.com/page -> example
            https://subdomain.example.com -> example
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Remove www. if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Get the main domain name (before first dot)
        parts = domain.split('.')
        if len(parts) > 1:
            # Handle cases like co.uk, com.au
            if parts[-2] in ['co', 'com', 'org', 'gov', 'ac']:
                return parts[-3] if len(parts) > 2 else parts[0]
            return parts[-2]
        
        return parts[0]
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Check if URL is valid.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """
        Normalize URL (remove trailing slash, fragments, etc.).
        
        Args:
            url: URL to normalize
            
        Returns:
            str: Normalized URL
        """
        parsed = urlparse(url)
        
        # Rebuild URL without fragment
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        if parsed.query:
            normalized += f"?{parsed.query}"
        
        # Remove trailing slash
        if normalized.endswith('/') and parsed.path != '/':
            normalized = normalized[:-1]
        
        return normalized