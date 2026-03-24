# 🌐 Universal Web Scraper (UWS)

A high-performance, asynchronous web scraping framework and microservice. It uses **LLM-powered URL filtering** for intelligence and **traditional parsing** for speed, reliability, and cost-efficiency.

---

## 🎯 Features

- **Dual-Mode Operation** — Use as a CLI tool or a background FastAPI microservice
- **Smart URL Discovery** — Parses `sitemap.xml` automatically; falls back to homepage crawling if the sitemap is too large (>500 URLs) or missing
- **LLM-Powered Filtering** — Uses AI (Ollama/Phi-4) to identify only the most relevant URLs based on your prompt
- **Keyword Fallback** — If the LLM is unreachable, automatically falls back to keyword-based URL filtering. If no keywords match, all discovered URLs are passed to extraction
- **Manual Mode** — Skip the AI entirely and use lightning-fast keyword matching
- **Rails Integration** — Built-in worker to POST scraped content directly to a Rails API as Knowledge Base entries
- **Clean Extraction** — Automatically strips navbars, footers, and ads to return pure, high-quality content

---

## 🚀 Setup: From Zero to Running

### Step 1 — Clone & Enter the Project

```bash
git clone <your-repo-url>
cd universal-scraper
```

### Step 2 — Create a Virtual Environment

```bash
python -m venv venv

# Activate it:
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

You should see `(venv)` at the start of your terminal prompt.

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure Environment Variables

Create a `.env` file in the project root:

```env
# LLM Settings (Ollama) — optional, scraper works without it via keyword fallback
OLLAMA_BASE_URL=http://your-ollama-ip:11434
OLLAMA_MODEL=phi4-mini-reasoning
SEARCH_PROMPT=Find URLs related to company policies, privacy, terms of service, and compliance documents.

# Paths
SCRAPER_DIR=/absolute/path/to/universal-scraper

# Rails API (used by the microservice only)
RAILS_API_URL=http://localhost:3000
PORT=8088
```

> **Note:** If `OLLAMA_BASE_URL` is unreachable, the scraper automatically falls back to keyword filtering — no crash, no hang.

---

## 🖥️ Usage

### Mode A — CLI Tool (Manual / Batch Scrapes)

```bash
# Make sure your venv is active
source venv/bin/activate

# Standard AI-powered scrape
python main.py https://example.com

# High-speed manual scrape (no LLM required)
python main.py https://example.com --filter-manual

# Manual scrape with custom keywords
python main.py https://example.com --filter-manual privacy terms gdpr

# Custom AI prompt
python main.py https://example.com --filter-llm "Find only pricing and feature pages"

# Batch scrape from a .txt file (one URL per line)
python main.py urls.txt

# Limit sitemap size before falling back to homepage crawl
python main.py https://example.com --max-sitemap 300

# Choose output format
python main.py https://example.com --format markdown   # json | text | markdown | all
```

**Output** is saved to `scraped_data/<domain>/`:
| File | Contents |
|---|---|
| `data.json` | Structured JSON with URL, title, metadata, word counts |
| `data.md` | Clean Markdown — great for LLM training or documentation |
| `summary.txt` | High-level stats: time elapsed, page types found |

---

### Mode B — FastAPI Microservice (Rails / Background Jobs)

#### Start the server

```bash
# Make sure your venv is active
source venv/bin/activate

# Enter the service directory
cd scraper_service

# Start the server (with auto-reload for development)
uvicorn main:app --host 0.0.0.0 --port 8088 --reload

# Production (no reload)
uvicorn main:app --host 0.0.0.0 --port 8088
```

The server starts at `http://0.0.0.0:8088`. You should see:
```
INFO: Application startup complete.
```

#### Trigger a scrape job

```bash
curl -X POST http://localhost:8088/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "website_url": "https://yoursite.com",
    "rails_api_url": "http://localhost:3000",
    "rails_api_token": "your_rails_api_access_token"
  }'
```

Returns `202 Accepted` immediately — scraping runs in the background.

#### Poll for live status

```bash
curl http://localhost:8088/scrape/1/status
```

Example responses:

```json
{ "account_id": 1, "status": "running", "message": "Extracting page 2/5: https://yoursite.com/privacy-policy" }
{ "account_id": 1, "status": "done",    "message": "Saved 5 page(s) as knowledge entries in 18.3s." }
{ "account_id": 1, "status": "failed",  "message": "No relevant pages found on https://yoursite.com." }
```

**Status values:**
| Status | Meaning |
|---|---|
| `idle` | No job triggered yet for this account |
| `pending` | Job accepted, not started yet |
| `running` | Actively scraping — message shows current step |
| `done` | Completed successfully |
| `failed` | Something went wrong — check the message |

#### Health check

```bash
curl http://localhost:8088/health
# → { "status": "ok" }
```

---

## 📁 Project Structure

```
.
├── main.py                     # CLI entry point & argument handler
├── .env                        # Your environment config (not committed)
├── requirements.txt
│
├── scraper_service/
│   ├── main.py                 # FastAPI microservice (endpoints)
│   └── worker.py               # Async background worker (Rails sync)
│
├── scrapers/
│   ├── __init__.py
│   ├── sitemap_parser.py       # XML & sitemap index discovery
│   ├── url_filter.py           # LLM vs keyword filtering logic
│   └── content_extractor.py   # BeautifulSoup content cleaner & page type detector
│
├── config/
│   ├── browser_config.py       # Crawl4AI / Chromium settings
│   └── llm_config.py           # Ollama endpoint & prompt settings
│
├── models/
│   ├── __init__.py
│   └── schemas.py              # Pydantic schemas
│
├── utils/                      # File I/O & URL normalization helpers
└── scraped_data/               # CLI output (auto-created, gitignored)
```

---

## 🔧 Troubleshooting

**LLM is offline / unreachable**
The scraper detects the connection failure within 3 seconds and automatically falls back to keyword filtering. No manual intervention needed.

**No URLs matched keywords**
If keyword filtering also finds nothing, all discovered URLs are forwarded to content extraction. The extractor will skip pages with fewer than 50 words.

**Large sitemaps (10,000+ URLs)**
Use `--max-sitemap 500` in CLI mode. The scraper will skip the sitemap and only analyze links found on the homepage.

**401 Invalid Access Token (microservice)**
Ensure `rails_api_token` in your POST body matches a valid `api_access_token` for an admin user in your Rails app.

**409 Conflict on POST /scrape**
A job for that `account_id` is already running. Wait for it to reach `done` or `failed` before triggering a new one.

**Browser/Chromium issues**
Ensure `headless=True` is set in `config/browser_config.py`. Setting it to `False` will cause hangs in any server or headless environment.