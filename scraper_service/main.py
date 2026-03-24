# scraper_service/main.py
#
# Lightweight FastAPI microservice that receives scrape jobs from Rails
# and runs them in the background via asyncio — fire-and-forget.
#
# Run with:
#   uvicorn main:app --host 0.0.0.0 --port 8088
#
# Install deps (inside your existing policy-scraper venv):
#   pip install fastapi uvicorn aiohttp

import asyncio
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

SCRAPER_DIR = os.environ.get("SCRAPER_DIR", os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, SCRAPER_DIR)

from worker import ScrapeWorker

# ── In-memory job registry ────────────────────────────────────────────────────
# Maps account_id (str) → { status, message }
# Status values: "pending" | "running" | "done" | "failed"
jobs: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Scraper Service", version="1.0.0", lifespan=lifespan)


# ── Request / Response models ─────────────────────────────────────────────────

class ScrapeRequest(BaseModel):
    account_id: int
    website_url: str
    rails_api_url: str        # e.g. "http://localhost:3000"
    rails_api_token: str      # api_access_token of the requesting admin user


class ScrapeStatusResponse(BaseModel):
    account_id: int
    status: str               # idle | pending | running | done | failed
    message: str | None = None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/scrape", status_code=202)
async def trigger_scrape(req: ScrapeRequest):
    """
    Accepts a scrape job and starts it immediately in the background.
    Returns 202 Accepted — Rails does NOT wait for scraping to finish.

    100 accounts clicking simultaneously = 100 concurrent asyncio tasks.
    If a job for this account is already running, returns 409.
    """
    key = str(req.account_id)

    if jobs.get(key, {}).get("status") in ("pending", "running"):
        raise HTTPException(
            status_code=409,
            detail=f"Scrape already running for account {req.account_id}"
        )

    jobs[key] = {"status": "pending", "message": "Job accepted, starting…"}

    worker = ScrapeWorker(
        account_id=req.account_id,
        website_url=req.website_url,
        rails_api_url=req.rails_api_url,
        rails_api_token=req.rails_api_token,
        jobs=jobs,
    )

    # Fire and forget — asyncio task runs independently
    asyncio.create_task(worker.run())

    return {"status": "accepted", "account_id": req.account_id}


@app.get("/scrape/{account_id}/status", response_model=ScrapeStatusResponse)
def scrape_status(account_id: int):
    """
    Vue polls this (via Rails proxy) every 3 seconds for live progress.
    Returns idle if no job has been triggered for this account yet.
    """
    key = str(account_id)
    job = jobs.get(key)

    if not job:
        return ScrapeStatusResponse(account_id=account_id, status="idle")

    return ScrapeStatusResponse(
        account_id=account_id,
        status=job["status"],
        message=job.get("message"),
    )