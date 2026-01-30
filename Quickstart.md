# Policy Scraper - Quick Start Guide

## ✅ Version 1.2 - Organized Output!

**Latest Updates**: 
- ✨ Each website gets its own folder
- 📊 Summary file with scraping statistics
- 🔧 Fixed LLM URL filtering

## 📦 What You Have

A complete, modular web scraper that:
- ✅ Uses LLM ONLY for smart URL filtering
- ✅ Uses traditional parsing for fast content extraction
- ✅ Automatically finds sitemap.xml or scrapes homepage
- ✅ Exports to JSON, TXT, and Markdown formats
- ✅ Perfect for scraping company policies, documentation, etc.

## 🚀 Installation (3 Steps)

### Step 1: Navigate to Project
```bash
cd policy-scraper
```

### Step 2: Run Setup Script

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```batch
setup.bat
```

### Step 3: Configure LLM

Edit `.env` file:
```env
OLLAMA_BASE_URL=http://10.112.30.10:11434
OLLAMA_MODEL=ollama/phi4-mini-reasoning
```

## 🎯 Run Your First Scrape

```bash
# Activate environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate.bat  # Windows

# Scrape a website
python main.py https://www.anthropic.com

# Results will be in: scraped_data/anthropic.json
```

## 📁 Project Structure

```
policy-scraper/
├── main.py                    # ⭐ Main entry point
├── .env                       # ⚙️ Configuration
├── requirements.txt           # 📦 Dependencies
├── README.md                  # 📖 Full documentation
├── USAGE_GUIDE.md            # 📚 Detailed guide
│
├── config/                    # Configuration
│   ├── browser_config.py     # Browser settings
│   └── llm_config.py         # LLM settings
│
├── models/                    # Data schemas
│   └── schemas.py
│
├── scrapers/                  # Core scraping
│   ├── sitemap_parser.py     # Sitemap.xml handler
│   ├── url_filter.py         # LLM URL filtering
│   └── content_extractor.py  # Content extraction
│
├── utils/                     # Utilities
│   ├── file_handler.py       # Save files
│   └── url_utils.py          # URL helpers
│
└── scraped_data/             # 💾 Output folder
```

## 🎨 Common Use Cases

### 1. Scrape Privacy Policies
```bash
# Edit .env
SEARCH_PROMPT=Find privacy policy, terms of service, and data protection pages.

# Run
python main.py https://www.example.com
```

### 2. Scrape Documentation
```bash
# Edit .env
SEARCH_PROMPT=Find API documentation, developer guides, and tutorials.

# Run
python main.py https://docs.example.com --format markdown
```

### 3. Batch Scrape Multiple Sites
```bash
# Create urls.txt
cat > urls.txt << EOF
https://www.anthropic.com
https://openai.com
https://www.deepmind.com
EOF

# Run
python main.py urls.txt
```

### 4. Scrape Investor Relations
```bash
# Edit .env
SEARCH_PROMPT=Find investor relations, financial reports, and annual reports.

# Run
python main.py https://www.company.com
```

## 🔧 Key Features

### 1. Smart URL Discovery
- ✅ Checks for sitemap.xml first
- ✅ Falls back to homepage links
- ✅ Handles sitemap indexes

### 2. LLM Filtering
- ✅ AI selects relevant URLs only
- ✅ Customizable search prompts
- ✅ Fallback to keyword matching

### 3. Clean Content Extraction
- ✅ Removes navigation, footers, ads
- ✅ Auto-detects page types
- ✅ Counts words and metadata

### 4. Multiple Output Formats
- ✅ JSON for data processing
- ✅ TXT for reading
- ✅ Markdown for documentation

## 📊 Example Output

After running:
```bash
python main.py https://www.anthropic.com
```

You get:
```
scraped_data/
└── anthropic/              # Website-specific folder
    ├── anthropic.json      # Structured data
    ├── anthropic.txt       # Readable text
    ├── anthropic.md        # Markdown format
    └── summary.txt         # Scraping statistics ⭐ NEW
```

**anthropic.json:**
```json
[
  {
    "url": "https://www.anthropic.com/privacy",
    "title": "Privacy Policy",
    "page_type": "Privacy Policy",
    "content": "Full text...",
    "word_count": 2341
  }
]
```

**summary.txt:**
```
📊 SCRAPING SUMMARY
================================================================================
Website: https://www.anthropic.com
Scraped: 2024-01-29 10:30:00
URLs Discovered: 150
Relevant URLs: 8
Pages Scraped: 8
Total Words: 15,234

Page Types:
  - Privacy Policy: 1
  - Terms of Service: 1
================================================================================
⏱️  Total time: 45.23 seconds
```

## ⚙️ Customization

### Change What URLs to Find

Edit `.env`:
```env
# For policies (default)
SEARCH_PROMPT=Find company policies, privacy, terms, legal pages.

# For blog posts
SEARCH_PROMPT=Find blog posts, articles, and news.

# For careers
SEARCH_PROMPT=Find career pages, job listings, and benefits.
```

### Change Browser Visibility

Edit `config/browser_config.py`:
```python
headless=False  # See browser during scraping
```

### Change Output Format

```bash
python main.py URL --format json      # JSON only
python main.py URL --format text      # TXT only
python main.py URL --format markdown  # MD only
python main.py URL --format all       # All formats (default)
```

## 🐛 Troubleshooting

### "No relevant URLs found"
→ Adjust SEARCH_PROMPT in .env to be more general

### "LLM connection failed"
→ Check OLLAMA_BASE_URL and verify Ollama is running

### "Empty content extracted"
→ Set headless=False in browser_config.py to debug

### "Module not found"
→ Make sure you activated venv: `source venv/bin/activate`

## 📚 Documentation Files

1. **README.md** - Complete overview and features
2. **USAGE_GUIDE.md** - Detailed usage instructions
3. **This file** - Quick start guide

## 🎯 Next Steps

1. ✅ Run setup script
2. ✅ Configure .env
3. ✅ Try first scrape: `python main.py https://www.anthropic.com`
4. ✅ Check output in `scraped_data/`
5. ✅ Customize SEARCH_PROMPT for your needs
6. ✅ Process batch URLs with urls.txt

## 💡 Pro Tips

1. **Test with one URL first** before batch processing
2. **Review outputs** to verify quality
3. **Use sitemap when available** - much faster
4. **Customize search prompts** for each use case
5. **Save as JSON** if you only need structured data

---

## Command Cheat Sheet

```bash
# Setup
./setup.sh                           # Linux/Mac setup
setup.bat                            # Windows setup

# Activate environment
source venv/bin/activate             # Linux/Mac
venv\Scripts\activate.bat            # Windows

# Run scraper
python main.py URL                   # Single URL
python main.py urls.txt              # Multiple URLs
python main.py URL --format json     # JSON only

# Customize
nano .env                            # Edit configuration
nano config/browser_config.py        # Browser settings
```

---

Happy scraping! 🕷️

For detailed information, see:
- **README.md** - Full documentation
- **USAGE_GUIDE.md** - Advanced usage and examples