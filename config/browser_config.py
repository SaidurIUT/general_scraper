# config/browser_config.py

from crawl4ai import BrowserConfig

def get_browser_config():
    return BrowserConfig(
        browser_type="chromium",
        headless=True,
        verbose=True
    )