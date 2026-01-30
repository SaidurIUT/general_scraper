# Policy Scraper

A smart web scraper that uses LLM only for intelligent URL filtering, while traditional parsing handles content extraction. Perfect for extracting company policies, terms of service, privacy policies, and other documentation.

## 🎯 Features

- **Smart URL Discovery**: Automatically finds sitemap.xml or scrapes homepage links
- **LLM-Powered Filtering**: Uses AI to identify relevant policy pages
- **Traditional Parsing**: Fast, reliable content extraction without LLM overhead
- **Multiple Output Formats**: JSON, Text, and Markdown
- **Modular Architecture**: Easy to extend and customize
- **Batch Processing**: Process multiple websites from a file

## 📋 How It Works

1. **URL Discovery**: Checks for sitemap.xml, falls back to homepage links
2. **LLM Filtering**: AI selects only relevant URLs based on your search criteria
3. **Content Extraction**: Traditional BeautifulSoup parsing extracts clean text
4. **Smart Cleaning**: Removes navigation, footers, ads automatically
5. **Multi-Format Export**: Saves as JSON, readable text, and Markdown

## 🚀 Quick Start

### 1. Setup

```bash
# Create project directory
mkdir policy-scraper
cd policy-scraper

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Create directory structure
mkdir config models scrapers utils scraped_data
touch config/__init__.py models/__init__.py scrapers/__init__.py utils/__init__.py
```

### 2. Install Dependencies

Create `requirements.txt`:
```
crawl4ai
pydantic
python-dotenv
beautifulsoup4
lxml
aiohttp
```

Install:
```bash
pip install -r requirements.txt
```

### 3. Configure

Edit `.env` file:
```env
# LLM Configuration
OLLAMA_BASE_URL=http://10.112.30.10:11434
OLLAMA_MODEL=ollama/phi4-mini-reasoning

# Search Prompt (customize for your needs)
SEARCH_PROMPT=Find URLs related to company policies, privacy policy, terms of service, data protection, cookie policy, acceptable use policy, and compliance documents.
```

### 4. Run

```bash
# Scrape single website
python main.py https://www.anthropic.com

# Scrape multiple websites
python main.py urls.txt

# Save as JSON only
python main.py https://www.anthropic.com --format json

# Save in all formats (default)
python main.py https://www.anthropic.com --format all
```

## 📁 Project Structure

```
policy-scraper/
├── .env                          # Configuration
├── requirements.txt              # Dependencies
├── main.py                       # Entry point
├── urls.txt                      # Example URL list
│
├── config/                       # Configuration modules
│   ├── __init__.py
│   ├── browser_config.py        # Browser settings
│   └── llm_config.py            # LLM settings
│
├── models/                       # Data models
│   ├── __init__.py
│   └── schemas.py               # Pydantic schemas
│
├── scrapers/                     # Core scraping logic
│   ├── __init__.py
│   ├── sitemap_parser.py        # Sitemap.xml parser
│   ├── url_filter.py            # LLM-based URL filtering
│   └── content_extractor.py     # Content extraction
│
├── utils/                        # Utilities
│   ├── __init__.py
│   ├── file_handler.py          # File I/O operations
│   └── url_utils.py             # URL manipulation
│
└── scraped_data/                 # Output directory
    ├── anthropic.json
    ├── anthropic.txt
    └── anthropic.md
```

## 🎨 Customization

### Change Search Criteria

Edit `.env`:
```env
SEARCH_PROMPT=Find URLs related to investor relations, financial reports, annual reports, and SEC filings.
```

### Change LLM Provider

Edit `.env`:
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=ollama/llama3.2
```

### Adjust Browser Visibility

Edit `config/browser_config.py`:
```python
headless=False  # Show browser UI (useful for debugging)
```

### Customize Content Cleaning

Edit `scrapers/content_extractor.py` in the `_extract_main_content()` method to add/remove HTML elements.

## 📊 Output Formats

All files are saved in website-specific folders: `scraped_data/website_name/`

### JSON Format (website_name.json)
```json
[
  {
    "url": "https://example.com/privacy",
    "title": "Privacy Policy",
    "description": "Our privacy policy",
    "page_type": "Privacy Policy",
    "content": "Full text content...",
    "word_count": 1234
  }
]
```

### Text Format (website_name.txt)
Clean, readable text file with clear sections for each page.

### Markdown Format (website_name.md)
Well-formatted Markdown with headers, links, and metadata.

### Summary File (summary.txt)
Scraping statistics including:
```
📊 SCRAPING SUMMARY
================================================================================
Website: https://example.com
Scraped: 2024-01-29 10:30:00
URLs Discovered: 150
Relevant URLs: 8
Pages Scraped: 8
Total Words: 15,234

Page Types:
  - Privacy Policy: 1
  - Terms of Service: 1
  - Cookie Policy: 1
================================================================================
⏱️  Total time: 45.23 seconds
```

## 🔧 Advanced Usage

### Process Multiple Sites
Create `urls.txt`:
```
https://www.anthropic.com
https://openai.com
https://www.google.com
```

Run:
```bash
python main.py urls.txt
```

### Custom Page Type Detection

Edit `scrapers/content_extractor.py` in `_detect_page_type()`:
```python
patterns = {
    'Privacy Policy': ['privacy', 'privacy-policy'],
    'Your Custom Type': ['custom', 'keyword'],
}
```

## 🐛 Troubleshooting

### LLM Connection Issues
- Check `OLLAMA_BASE_URL` in `.env`
- Verify Ollama is running: `curl http://10.112.30.10:11434`
- Test model: `ollama run phi4-mini-reasoning`

### No URLs Found
- Check if sitemap.xml exists manually
- Verify SEARCH_PROMPT matches the content you're looking for
- Try with `headless=False` to see what the browser sees

### Empty Content
- Some sites use JavaScript rendering - check browser view
- Adjust content selectors in `content_extractor.py`
- Check if site blocks automated access

## 🔍 How LLM is Used

The LLM is used **ONLY** for URL filtering:

1. **Input**: List of URLs from sitemap or homepage
2. **Task**: Identify which URLs match the search criteria
3. **Output**: Filtered list of relevant URLs
4. **Fallback**: Keyword matching if LLM fails

Content extraction uses traditional BeautifulSoup parsing - no LLM needed!

## 📝 Example Output

```
🕷️  Starting scrape for: https://www.anthropic.com

📋 PHASE 1: URL Discovery
✅ Found sitemap: https://www.anthropic.com/sitemap.xml
📄 Parsed 150 URLs from sitemap
🤖 LLM selected 8 URLs
💭 Reasoning: Selected URLs containing privacy, terms, legal...

📥 PHASE 2: Content Extraction
[1/8] 📥 Extracting: https://www.anthropic.com/privacy
      ✅ Extracted: Privacy Policy (2,341 words)
[2/8] 📥 Extracting: https://www.anthropic.com/terms
      ✅ Extracted: Terms of Service (1,876 words)

💾 PHASE 3: Saving Results
✅ Saved to folder: scraped_data/anthropic/

📄 Files created:
   - anthropic.json
   - anthropic.txt
   - anthropic.md
   - summary.txt

📊 SCRAPING SUMMARY
================================================================================
URLs Discovered: 150
Relevant URLs: 8
Pages Scraped: 8
Total Words: 15,234

Page Types:
  - Privacy Policy: 1
  - Terms of Service: 1
  - Cookie Policy: 1
  - About Us: 1
  - Contact: 1
  - Legal: 3
================================================================================
⏱️  Total time: 45.23 seconds
```

### Output Folder Structure

```
scraped_data/
├── anthropic/
│   ├── anthropic.json      # Structured data
│   ├── anthropic.txt       # Readable text
│   ├── anthropic.md        # Markdown format
│   └── summary.txt         # Scraping statistics
└── openai/
    ├── openai.json
    ├── openai.txt
    ├── openai.md
    └── summary.txt
```

## 🤝 Contributing

Feel free to extend this scraper:
- Add new output formats
- Improve content extraction
- Add more page type patterns
- Enhance error handling

## 📄 License

MIT License - feel free to use and modify!

## 💡 Tips

1. **Start small**: Test with one URL before batch processing
2. **Check outputs**: Review JSON/TXT to verify quality
3. **Customize prompts**: Adjust SEARCH_PROMPT for different use cases
4. **Debug mode**: Set `headless=False` to see browser behavior
5. **Rate limiting**: Add delays between requests for large batches

---

Built with ❤️ using crawl4ai, BeautifulSoup, and minimal LLM usage for maximum efficiency!