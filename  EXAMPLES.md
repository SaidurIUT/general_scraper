# 📚 Usage Examples

## Quick Start Examples

### 1. Standard Scrape (Recommended)
```bash
python main.py https://example.com
```
- Uses sitemap if available
- Falls back to BFS if sitemap missing/too large
- Stores in database with embeddings
- Saves all file formats

### 2. Small Website (Fast)
```bash
python main.py https://smallsite.com --max-pages 50 --max-depth 2 --no-db
```
- Limits crawling to 50 pages
- Maximum depth of 2 links
- Skips database (files only)
- Completes in ~2-5 minutes

### 3. Large Website (Comprehensive)
```bash
python main.py https://bigsite.com --max-pages 1000 --max-depth 5
```
- Crawls up to 1000 pages
- Goes 5 levels deep
- Full database storage
- May take 30-60 minutes

## Filtering Examples

### 4. Manual Keyword Filtering (No LLM)
```bash
python main.py https://example.com --filter-manual
```
Uses default keywords: about, contact, faq, policy, etc.

### 5. Custom Keywords
```bash
python main.py https://example.com --filter-manual team culture values careers
```
Only extracts pages matching your specific keywords

### 6. Custom LLM Prompt
```bash
python main.py https://example.com --filter-llm "Find pages about sustainability and environmental initiatives"
```
LLM focuses on specific topics you care about

## Discovery Method Examples

### 7. Force BFS (Skip Sitemap)
```bash
python main.py https://example.com --bfs-only
```
Useful when:
- Sitemap is outdated
- You want consistent crawling behavior
- Site has no sitemap

### 8. Homepage Links Only
```bash
# Trigger homepage fallback by setting very low limits
python main.py https://example.com --max-sitemap 5 --max-pages 1
```
Quick extraction from just the homepage

## Output Format Examples

### 9. JSON Only
```bash
python main.py https://example.com --format json
```
Creates: `scraped_data/example/example.json`

### 10. Markdown Only
```bash
python main.py https://example.com --format markdown
```
Creates: `scraped_data/example/example.md`

### 11. All Formats
```bash
python main.py https://example.com --format all
```
Creates: JSON, Markdown, and Text files

## Batch Processing Examples

### 12. Multiple Websites
Create `websites.txt`:
```
https://company1.com
https://company2.com
https://company3.com
```

Run:
```bash
python main.py websites.txt
```

### 13. Batch with Custom Settings
```bash
python main.py websites.txt --max-pages 100 --format json --no-db
```
Applies settings to all websites in the file

## Real-World Scenarios

### 14. Customer Support Knowledge Base
```bash
python main.py https://support.company.com \
  --filter-llm "Find FAQ, help docs, troubleshooting guides, and support resources" \
  --max-pages 300 \
  --max-depth 3
```

### 15. Company Information Scraper
```bash
python main.py https://company.com \
  --filter-manual about team leadership contact location office \
  --max-pages 50 \
  --format markdown
```

### 16. Policy Documentation
```bash
python main.py https://company.com \
  --filter-manual privacy terms legal policy compliance gdpr \
  --format all
```

### 17. Blog/News Archive
```bash
python main.py https://company.com/blog \
  --max-pages 500 \
  --max-depth 2 \
  --format json
```

### 18. Documentation Site
```bash
python main.py https://docs.product.com \
  --filter-manual docs guide tutorial api reference \
  --max-pages 200 \
  --max-depth 4
```

## Performance Tuning Examples

### 19. Fast & Light
```bash
python main.py https://example.com \
  --max-pages 30 \
  --max-depth 2 \
  --filter-manual \
  --format json \
  --no-db
```
Best for: Quick testing, small sites, CI/CD

### 20. Comprehensive & Deep
```bash
python main.py https://example.com \
  --max-pages 2000 \
  --max-depth 6 \
  --max-sitemap 2000 \
  --format all
```
Best for: Building complete knowledge bases

## Troubleshooting Examples

### 21. LLM Not Available
```bash
# Fallback to manual mode
python main.py https://example.com --filter-manual
```

### 22. Database Issues
```bash
# Skip database entirely
python main.py https://example.com --no-db
```

### 23. Site Blocking Crawler
```bash
# Reduce crawl speed by limiting pages and using manual mode
python main.py https://example.com \
  --max-pages 20 \
  --max-depth 2 \
  --filter-manual
```

## Testing & Development Examples

### 24. Test Run (Minimal)
```bash
python main.py https://example.com \
  --max-pages 5 \
  --max-depth 1 \
  --no-db \
  --format json
```
Quick test to verify everything works

### 25. Debug Mode
```bash
# Check what URLs are discovered
python main.py https://example.com --max-pages 10 --max-depth 1
# Review: scraped_data/example/summary.txt for statistics
```

## Integration Examples

### 26. RAG Pipeline Preparation
```bash
# Scrape with embeddings enabled
python main.py https://docs.product.com \
  --max-pages 500 \
  --format json

# Later query with SQL:
# SELECT * FROM pages 
# ORDER BY embedding <=> query_embedding 
# LIMIT 5;
```

### 27. Data Export for Fine-tuning
```bash
python main.py https://example.com \
  --format json \
  --no-db

# Process JSON for model training
```

### 28. Chatbot Training Data
```bash
# Create comprehensive QA dataset
python main.py https://support.company.com \
  --filter-llm "Find all FAQ, help articles, and how-to guides" \
  --max-pages 300 \
  --format all
```

## Advanced Combinations

### 29. Multi-Site Research Project
```bash
# Collect data from competitors
cat > competitors.txt << EOF
https://competitor1.com
https://competitor2.com
https://competitor3.com
EOF

python main.py competitors.txt \
  --filter-manual about services pricing contact \
  --max-pages 100 \
  --format markdown
```

### 30. Incremental Updates
```bash
# Initial scrape
python main.py https://example.com --format all

# Later: re-scrape with same settings
# (Database will update existing entries)
python main.py https://example.com --format all
```

## Tips & Best Practices

1. **Start Small**: Begin with `--max-pages 20` to test
2. **Use Manual Mode First**: Faster and more predictable
3. **Check Output**: Review `summary.txt` after each scrape
4. **Respect Robots.txt**: The scraper respects rate limits
5. **Monitor Resources**: Large scrapes use significant memory
6. **Save Progress**: Files are saved even if scraping is interrupted

## Common Command Patterns

```bash
# Quick test
python main.py <URL> --max-pages 10 --no-db

# Production scrape
python main.py <URL> --max-pages 500 --format all

# Manual fallback
python main.py <URL> --filter-manual --no-db

# Batch job
python main.py urls.txt --max-pages 100 --format json
```