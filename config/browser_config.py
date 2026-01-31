# config/browser_config.py

"""Browser configuration for web crawling."""
from crawl4ai import BrowserConfig

def get_browser_config():
    """
    Configure the browser settings.
    
    Returns:
        BrowserConfig: Browser configuration object
    """
    return BrowserConfig(
        browser_type="chromium",
        headless=True,  # Set to False to see browser UI during debugging
        verbose=True
    )