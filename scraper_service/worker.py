# scraper_service/worker.py
#
# ScrapeWorker runs the full scraper pipeline for one account,
# then POSTs each scraped page as a separate knowledge_base_entry row
# via the existing Rails entries API.

import asyncio
import sys
import os
import time
import aiohttp
from datetime import datetime

SCRAPER_DIR = os.environ.get("SCRAPER_DIR", os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, SCRAPER_DIR)

from scrapers import SitemapParser, URLFilter, ContentExtractor  # noqa: E402
from utils import URLUtils                                        # noqa: E402


class ScrapeWorker:
    """
    Runs one full scrape job for a single account.

    Flow:
      1. Discover URLs (sitemap → homepage fallback)
      2. LLM-filter relevant URLs
      3. Extract content from each URL
      4. POST each page as a knowledge_base_entry row:
           level       = page_type  (e.g. "Privacy Policy", "Terms of Service")
           description = full page content text
      5. Update the in-memory jobs dict throughout so the status endpoint
         reflects real-time progress back to the Vue polling.
    """

    MAX_SITEMAP_URLS = 500

    def __init__(
        self,
        account_id: int,
        website_url: str,
        rails_api_url: str,
        rails_api_token: str,
        jobs: dict,
    ):
        self.account_id = account_id
        self.website_url = website_url.rstrip("/")
        self.rails_api_url = rails_api_url.rstrip("/")
        self.rails_api_token = rails_api_token
        self.jobs = jobs
        self.key = str(account_id)

    # ── Public entry point ────────────────────────────────────────────────────

    async def run(self):
        self._set_status("running", "Starting scrape…")
        start = time.time()

        try:
            scraped_pages = await self._scrape()

            if not scraped_pages:
                self._set_status("failed", "No content could be extracted from the website.")
                return

            await self._save_entries_to_rails(scraped_pages)

            elapsed = round(time.time() - start, 1)
            self._set_status(
                "done",
                f"Saved {len(scraped_pages)} page(s) as knowledge entries in {elapsed}s."
            )

        except Exception as exc:  # noqa: BLE001
            self._set_status("failed", str(exc))

    # ── Scraping pipeline ─────────────────────────────────────────────────────

    async def _scrape(self) -> list[dict]:
        url_filter = URLFilter(mode="llm")
        content_extractor = ContentExtractor()

        # Phase 1 — URL discovery
        sitemap_parser = SitemapParser(self.website_url)
        all_urls = await sitemap_parser.get_all_urls()

        if not all_urls or len(all_urls) > self.MAX_SITEMAP_URLS:
            if len(all_urls) > self.MAX_SITEMAP_URLS:
                self._set_status(
                    "running",
                    f"Sitemap too large ({len(all_urls)} URLs), falling back to homepage links…"
                )
            all_urls = await url_filter.get_homepage_links(self.website_url)

        if not all_urls:
            self._set_status(
                "failed",
                f"Could not discover any URLs from {self.website_url}. "
                "Check that the site is accessible."
            )
            return []

        self._set_status("running", f"Discovered {len(all_urls)} URLs. Filtering…")

        # Phase 2 — LLM filtering
        relevant_urls = await url_filter.filter_urls(all_urls)

        print(f"DEBUG relevant_urls ({len(relevant_urls)}): {relevant_urls}")

        if not relevant_urls:
            self._set_status(
                "failed",
                f"No relevant pages found on {self.website_url}. "
                "The site may not have policy/legal pages, or try adjusting your search prompt."
            )
            return []

        self._set_status("running", f"Found {len(relevant_urls)} relevant pages. Extracting content…")

        # Phase 3 — Content extraction
        scraped_pages = []
        for idx, url in enumerate(relevant_urls, 1):
            self._set_status(
                "running",
                f"Extracting page {idx}/{len(relevant_urls)}: {url}"
            )
            page = await content_extractor.extract(url)
            if page:
                scraped_pages.append(page)

        if not scraped_pages:
            self._set_status(
                "failed",
                f"Found {len(relevant_urls)} relevant URL(s) but could not extract content from any of them."
            )
            return []

        return scraped_pages

    # ── Save to Rails as knowledge_base_entry rows ────────────────────────────

    async def _save_entries_to_rails(self, pages: list[dict]):
        """
        POST each scraped page to:
          POST /api/v1/accounts/:account_id/knowledge_base_entries
          Body: { knowledge_base_entry: { level, description } }

        level       → page_type from the scraper (e.g. "Privacy Policy")
        description → full content text + source URL header
        """
        entries_url = (
            f"{self.rails_api_url}/api/v1/accounts/{self.account_id}/knowledge_base_entries"
        )
        headers = {
            "Content-Type": "application/json",
            "api_access_token": self.rails_api_token,
        }

        saved = 0
        async with aiohttp.ClientSession() as session:
            for idx, page in enumerate(pages, 1):
                self._set_status(
                    "running",
                    f"Saving entry {idx}/{len(pages)}: {page.get('page_type', 'General')}"
                )

                # Build a rich description so the KB entry is self-contained
                description = self._build_description(page)

                payload = {
                    "knowledge_base_entry": {
                        "level": page.get("page_type") or "General",
                        "description": description,
                    }
                }

                async with session.post(
                    entries_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status in (200, 201):
                        saved += 1
                    else:
                        body = await resp.text()
                        # Log but continue — don't abort the whole job for one failure
                        print(
                            f"[worker] Failed to save entry for {page.get('url')}: "
                            f"HTTP {resp.status} — {body[:200]}"
                        )

        if saved == 0:
            raise RuntimeError("All entry saves failed. Check Rails API token and URL.")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build_description(self, page: dict) -> str:
        """
        Format a single page into a readable description string for the entry.
        Includes source URL and title so the KB entry is self-contained.
        """
        lines = []

        if page.get("title"):
            lines.append(f"Title: {page['title']}")

        if page.get("url"):
            lines.append(f"Source: {page['url']}")

        if page.get("description"):
            lines.append(f"Summary: {page['description']}")

        lines.append("")  # blank line before body
        lines.append(page.get("content", "").strip())

        return "\n".join(lines)

    def _set_status(self, status: str, message: str = ""):
        print(f"[worker] [{status.upper()}] {message}")
        self.jobs[self.key] = {"status": status, "message": message}