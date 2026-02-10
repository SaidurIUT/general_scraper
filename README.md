# 🤖 Knowledge Base Scraper for Website Chatbots

A powerful, intelligent web scraper designed to build comprehensive knowledge bases from websites for chatbot applications. Uses smart URL discovery (sitemap → BFS → homepage), LLM-powered filtering, and PostgreSQL with vector embeddings for semantic search.

## 🎯 Purpose

Build a complete knowledge base from any website to power chatbots that can answer questions about:
- Company information and background
- Services and offerings  
- Locations and contact details
- Policies (privacy, terms, legal)
- Support resources and FAQs
- Team and leadership
- News and updates
- Any other informational content

**Note:** This scraper focuses on **static informational content** and excludes:
- Individual product listings (dynamic/frequently changing)
- Shopping carts and checkouts
- User account pages
- Search results and filters

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     URL DISCOVERY                            │
├─────────────────────────────────────────────────────────────┤
│  1. Sitemap.xml → 2. BFS Crawling → 3. Homepage Links       │
│                                                               │
│  ✅ Sitemap: Fast, complete coverage (if available)         │
│  ✅ BFS: Comprehensive crawling (depth & breadth control)   │
│  ✅ Homepage: Quick fallback                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     URL FILTERING                            │
├─────────────────────────────────────────────────────────────┤
│  Pre-filter: Remove carts, search, user pages                │
│  Main filter: LLM or keyword-based                           │
│                                                               │
│  LLM Mode: Intelligent context-aware filtering               │
│  Manual Mode: Fast keyword matching                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  CONTENT EXTRACTION                          │
├─────────────────────────────────────────────────────────────┤
│  • Extract main content (remove nav, footer, ads)           │
│  • Detect page type (About, Contact, Policy, etc.)          │
│  • Clean and structure text                                 │
│  • Calculate metadata (word count, etc.)                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                        STORAGE                               │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL + pgvector: Semantic search with embeddings     │
│  Files: JSON, Markdown, Text formats                        │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Features

- **🔍 Smart URL Discovery**: Sitemap → BFS → Homepage fallback
- **🤖 LLM-Powered Filtering**: Intelligent URL selection using local LLM (Ollama)
- **⚙️ Manual Keyword Mode**: Fast filtering without LLM dependency
- **🌊 BFS Crawling**: Configurable depth and page limits
- **🎯 Content Extraction**: Removes noise, extracts main content
- **🗄️ PostgreSQL + pgvector**: Store with semantic embeddings for RAG
- **📁 Multiple Formats**: JSON, Markdown, Text outputs
- **🚀 Async/Concurrent**: Fast parallel processing
- **📊 Detailed Statistics**: Track discovery, filtering, and extraction metrics

## 🛠️ Installation

### Prerequisites

```bash
# Python 3.8+
python --version

# PostgreSQL with pgvector extension
psql --version

# Ollama (for LLM filtering)
ollama --version
```

### Setup

```bash
# Clone repository
git clone <your-repo-url>
cd knowledge-base-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (required for crawl4ai)
playwright install chromium
```

### Configuration

Create a `.env` file:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=scraper_db
DB_USER=postgres
DB_PASSWORD=your_password

# LLM Configuration (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=ollama/phi4-mini-reasoning

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Custom Search Prompt (optional)
SEARCH_PROMPT="Build comprehensive knowledge base..."
```

### Database Setup

```sql
-- Create database
CREATE DATABASE scraper_db;

-- Connect to database
\c scraper_db

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Tables are created automatically on first run
```

## 🚀 Usage

### Basic Usage

```bash
# Scrape a website (uses sitemap → BFS → homepage)
python main.py https://example.com

# Scrape with custom BFS limits
python main.py https://example.com --max-pages 500 --max-depth 4

# Use BFS only (skip sitemap)
python main.py https://example.com --bfs-only

# Use manual keyword filtering (faster, no LLM)
python main.py https://example.com --filter-manual

# Skip database storage (files only)
python main.py https://example.com --no-db

# Save only JSON format
python main.py https://example.com --format json
```

### Advanced Examples

```bash
# Large website with aggressive crawling
python main.py https://bigcompany.com \
  --max-pages 1000 \
  --max-depth 5 \
  --max-sitemap 1000

# Quick scrape for small site
python main.py https://smallsite.com \
  --max-pages 50 \
  --max-depth 2 \
  --no-db

# Manual filtering with custom keywords
python main.py https://example.com \
  --filter-manual about team contact faq

# LLM filtering with custom prompt
python main.py https://example.com \
  --filter-llm "Find pages about company culture and values"

# Batch processing from file
python main.py urls.txt
```

### URL File Format (urls.txt)

```
https://company1.com
https://company2.com
https://company3.com
```

## 📊 Output Structure

```
scraped_data/
└── example/
    ├── example.json        # Structured JSON data
    ├── example.md          # Markdown format
    ├── example.txt         # Plain text format
    └── summary.txt         # Scraping statistics
```

### JSON Output Example

```json
[
  {
    "url": "https://example.com/about",
    "title": "About Us - Example Company",
    "description": "Learn about our mission and team",
    "page_type": "About Us",
    "content": "We are a company that...",
    "word_count": 450
  },
  {
    "url": "https://example.com/contact",
    "title": "Contact Us",
    "description": "Get in touch with our team",
    "page_type": "Contact",
    "content": "Our offices are located...",
    "word_count": 200
  }
]
```

## ⚙️ Configuration Options

### URL Discovery

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--max-sitemap` | 500 | Max sitemap URLs before switching to BFS |
| `--max-pages` | 200 | Maximum pages to crawl with BFS |
| `--max-depth` | 3 | Maximum crawl depth for BFS |
| `--bfs-only` | False | Skip sitemap, use BFS only |

### Filtering

| Parameter | Description |
|-----------|-------------|
| `--filter-llm` | Use LLM filtering (default, requires Ollama) |
| `--filter-llm "prompt"` | LLM with custom prompt |
| `--filter-manual` | Keyword filtering (no LLM needed) |
| `--filter-manual kw1 kw2` | Manual with custom keywords |

### Output

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--format` | all | Output format: json, text, markdown, all |
| `--no-db` | False | Skip database storage |

## 🎯 Filtering Logic

### Pre-filtering (Automatic)

Always excludes:
- Shopping carts and checkouts
- User account pages
- Search results and filters
- Login/signup pages
- API endpoints
- Media downloads
- Social redirects

### LLM Filtering

Uses local LLM (Ollama) to intelligently identify informational pages:

```python
# Includes:
- Company information
- Services/offerings
- Locations and contact
- Policies and legal
- Support and FAQ
- News and blog

# Excludes:
- Individual products
- Dynamic content
- User-specific pages
```

### Manual Keyword Filtering

Fast pattern matching on URLs using keywords:

```python
keywords = [
    'about', 'contact', 'faq', 'help', 'support',
    'privacy', 'terms', 'legal', 'policy',
    'location', 'office', 'team', 'services',
    'news', 'blog', 'press'
    # ... and more
]
```

## 🗄️ Database Schema

```sql
-- Websites table
CREATE TABLE websites (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    domain_name TEXT NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    stats JSONB
);

-- Pages table with vector embeddings
CREATE TABLE pages (
    id SERIAL PRIMARY KEY,
    website_id INTEGER REFERENCES websites(id),
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    description TEXT,
    page_type TEXT,
    content TEXT,
    word_count INTEGER,
    embedding vector(384),  -- 384-dimensional for all-MiniLM-L6-v2
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast search
CREATE INDEX idx_pages_website ON pages(website_id);
CREATE INDEX idx_pages_embedding ON pages USING ivfflat (embedding vector_cosine_ops);
```

## 🔧 Troubleshooting

### LLM Filtering Fails

```bash
# Use manual keyword filtering
python main.py https://example.com --filter-manual

# Check Ollama is running
ollama list
ollama pull phi4-mini-reasoning
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify pgvector extension
psql -d scraper_db -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Run without database
python main.py https://example.com --no-db
```

### BFS Crawling Too Slow

```bash
# Reduce limits
python main.py https://example.com --max-pages 50 --max-depth 2

# Use sitemap instead
python main.py https://example.com  # Auto-detects sitemap

# Use homepage links only
# (Set very low limits to trigger fallback)
python main.py https://example.com --max-sitemap 10 --max-pages 1
```

## 🎓 Use Cases

### 1. Customer Support Chatbot
Scrape company website for FAQ, support docs, policies:
```bash
python main.py https://support.company.com --max-depth 4
```

### 2. Internal Knowledge Base
Build searchable knowledge base from internal docs:
```bash
python main.py https://internal.company.com \
  --filter-manual docs guide how-to tutorial
```

### 3. Competitive Analysis
Gather public information from competitor sites:
```bash
python main.py urls.txt --format all --no-db
```

### 4. RAG Pipeline
Generate embeddings for retrieval-augmented generation:
```bash
python main.py https://example.com
# Data is stored in PostgreSQL with pgvector embeddings
# Query with: SELECT * FROM pages ORDER BY embedding <=> query_vector LIMIT 5
```

## 📝 Development

### Project Structure

```
.
├── config/
│   ├── browser_config.py    # Playwright/browser settings
│   ├── llm_config.py         # Ollama LLM configuration
│   └── db_config.py          # PostgreSQL configuration
├── scrapers/
│   ├── sitemap_parser.py     # Sitemap.xml parsing
│   ├── bfs_crawler.py        # BFS web crawling
│   ├── url_filter.py         # LLM/keyword filtering
│   └── content_extractor.py  # Content extraction
├── utils/
│   ├── file_handler.py       # File I/O operations
│   ├── url_utils.py          # URL utilities
│   └── db_handler.py         # Database operations
├── models/
│   └── schemas.py            # Pydantic models
├── main.py                   # Main entry point
└── README.md
```

## 🔮 Future Enhancements

- [ ] Support for JavaScript-heavy SPAs
- [ ] PDF and document extraction
- [ ] Image and video content analysis
- [ ] Multi-language support
- [ ] Incremental updates (detect changes)
- [ ] Cloud storage integration (S3, GCS)
- [ ] GraphQL/REST API endpoint
- [ ] Web UI for configuration and monitoring
- [ ] Docker containerization
- [ ] Distributed crawling with Celery

## 📄 License

MIT License - feel free to use for any purpose

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 💬 Support

For issues and questions:
- Open a GitHub issue
- Check existing issues for solutions
- Review the troubleshooting section

---

**Built for creating intelligent, context-aware chatbots 🤖**