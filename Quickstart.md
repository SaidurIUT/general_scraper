# 🚀 Quick Start Guide

## Prerequisites
- Python 3.8+
- PostgreSQL 12+ with pgvector extension
- Ollama (for LLM filtering) or use --filter-manual

## Installation (5 minutes)

### 1. Run Setup Script
```bash
chmod +x setup.sh
./setup.sh
```

### 2. Configure Environment
Edit `.env` file:
```bash
nano .env
```

Update database credentials and Ollama settings.

### 3. Setup Database (Optional)
```bash
# Create database
createdb scraper_db

# Enable pgvector
psql scraper_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 4. Test Installation
```bash
source venv/bin/activate
python main.py https://example.com --max-pages 10 --no-db
```

## Common Use Cases

### 1. Build Chatbot Knowledge Base
```bash
python main.py https://yourcompany.com --max-pages 300
```

### 2. Quick Scrape (No Database)
```bash
python main.py https://site.com --max-pages 50 --no-db --filter-manual
```

### 3. Comprehensive Deep Crawl
```bash
python main.py https://site.com --max-pages 1000 --max-depth 5
```

### 4. Batch Process Multiple Sites
```bash
echo "https://site1.com
https://site2.com
https://site3.com" > urls.txt

python main.py urls.txt
```

## Troubleshooting

### Ollama Not Available
Use manual filtering:
```bash
python main.py https://site.com --filter-manual
```

### Database Issues
Skip database:
```bash
python main.py https://site.com --no-db
```

### Slow Crawling
Reduce limits:
```bash
python main.py https://site.com --max-pages 50 --max-depth 2
```

## Next Steps
1. Check output in `scraped_data/` folder
2. Review `summary.txt` for statistics
3. Use JSON data for chatbot training
4. Query database with vector similarity search

For full documentation, see README.md