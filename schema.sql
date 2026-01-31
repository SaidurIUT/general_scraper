-- Database schema for scraper with pgvector support

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS scraped_pages CASCADE;
DROP TABLE IF EXISTS scrape_sessions CASCADE;

-- Table to track scraping sessions (one per website scrape)
CREATE TABLE scrape_sessions (
    id SERIAL PRIMARY KEY,
    website_url TEXT NOT NULL,
    domain_name VARCHAR(255) NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    urls_discovered INTEGER,
    relevant_urls INTEGER,
    pages_scraped INTEGER,
    total_words INTEGER,
    total_time_seconds NUMERIC(10, 2)
);

-- Table to store scraped page content with vector embeddings
CREATE TABLE scraped_pages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES scrape_sessions(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title TEXT,
    description TEXT,
    page_type VARCHAR(100),
    content TEXT NOT NULL,
    word_count INTEGER,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Vector embedding of the content (384 dimensions for all-MiniLM-L6-v2)
    content_embedding vector(384)
);

-- Create indexes for better query performance
CREATE INDEX idx_scraped_pages_session_id ON scraped_pages(session_id);
CREATE INDEX idx_scraped_pages_url ON scraped_pages(url);
CREATE INDEX idx_scraped_pages_page_type ON scraped_pages(page_type);
CREATE INDEX idx_scrape_sessions_domain ON scrape_sessions(domain_name);
CREATE INDEX idx_scrape_sessions_scraped_at ON scrape_sessions(scraped_at);

-- Create vector similarity search index (IVFFlat index for faster similarity search)
-- This index will be created after data is inserted (requires at least 1000 rows for optimal performance)
-- For now, we'll use the default index
CREATE INDEX ON scraped_pages USING ivfflat (content_embedding vector_cosine_ops) WITH (lists = 100);

-- Create a function to search similar content
CREATE OR REPLACE FUNCTION search_similar_content(
    query_embedding vector(384),
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    url TEXT,
    title TEXT,
    page_type VARCHAR(100),
    content TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        scraped_pages.id,
        scraped_pages.url,
        scraped_pages.title,
        scraped_pages.page_type,
        scraped_pages.content,
        1 - (scraped_pages.content_embedding <=> query_embedding) AS similarity
    FROM scraped_pages
    WHERE 1 - (scraped_pages.content_embedding <=> query_embedding) > match_threshold
    ORDER BY scraped_pages.content_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- View to get scraping statistics
CREATE OR REPLACE VIEW scraping_statistics AS
SELECT
    ss.id,
    ss.website_url,
    ss.domain_name,
    ss.scraped_at,
    ss.pages_scraped,
    ss.total_words,
    ss.total_time_seconds,
    COUNT(sp.id) as actual_pages_count,
    AVG(sp.word_count) as avg_word_count,
    jsonb_object_agg(sp.page_type, page_type_count) as page_types_breakdown
FROM scrape_sessions ss
LEFT JOIN scraped_pages sp ON ss.id = sp.session_id
LEFT JOIN (
    SELECT session_id, page_type, COUNT(*) as page_type_count
    FROM scraped_pages
    GROUP BY session_id, page_type
) pt ON ss.id = pt.session_id
GROUP BY ss.id, ss.website_url, ss.domain_name, ss.scraped_at, ss.pages_scraped, ss.total_words, ss.total_time_seconds;
