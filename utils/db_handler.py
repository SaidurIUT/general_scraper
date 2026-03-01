"""Database handler for storing scraped data in PostgreSQL with pgvector."""
import psycopg2
from psycopg2.extras import execute_values
from typing import List, Dict, Optional
from datetime import datetime
from sentence_transformers import SentenceTransformer
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DatabaseConfig
from .text_chunker import TextChunker

class DatabaseHandler:
    """Handle database operations for scraped data with vector embeddings."""

    def __init__(self):
        """Initialize database handler with embedding model."""
        self.config = DatabaseConfig()
        self.conn = None
        self.embedding_model = None
        print(f"🔧 Loading embedding model: {self.config.EMBEDDING_MODEL}")
        try:
            self.embedding_model = SentenceTransformer(self.config.EMBEDDING_MODEL)
            print("✅ Embedding model loaded successfully")
        except Exception as e:
            print(f"⚠️  Warning: Could not load embedding model: {e}")
            print("   Embeddings will be stored as NULL")

    def connect(self) -> bool:
        """
        Connect to PostgreSQL database.

        Returns:
            bool: True if connected successfully
        """
        try:
            self.conn = psycopg2.connect(**self.config.get_connection_params())
            print(f"✅ Connected to database: {self.config.NAME}")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print(f"   Make sure PostgreSQL is running and database '{self.config.NAME}' exists")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate vector embedding for text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding, or None if model not loaded
        """
        if not self.embedding_model or not text:
            return None

        try:
            # Note: We no longer truncate here - chunking handles long text
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            print(f" Warning: Could not generate embedding: {e}")
            return None

    def save_scrape_session(
        self,
        website_url: str,
        domain_name: str,
        stats: Dict
    ) -> Optional[int]:
        """
        Save scraping session metadata.

        Args:
            website_url: The URL of the website scraped
            domain_name: Domain name extracted from URL
            stats: Dictionary containing scraping statistics

        Returns:
            Session ID if successful, None otherwise
        """
        if not self.conn:
            print(" No database connection")
            return None

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO scrape_sessions
                (website_url, domain_name, urls_discovered, relevant_urls,
                 pages_scraped, total_words, total_time_seconds)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                website_url,
                domain_name,
                stats.get('urls_discovered'),
                stats.get('relevant_urls'),
                stats.get('pages_scraped'),
                stats.get('total_words'),
                stats.get('total_time')
            ))

            session_id = cursor.fetchone()[0]
            self.conn.commit()
            cursor.close()

            return session_id
        except Exception as e:
            print(f"❌ Error saving scrape session: {e}")
            self.conn.rollback()
            return None

    def save_scraped_pages(
        self,
        session_id: int,
        pages: List[Dict]
    ) -> bool:
        """
        Save scraped pages with vector embeddings using semantic chunking.

        Args:
            session_id: ID of the scrape session
            pages: List of page dictionaries

        Returns:
            bool: True if successful
        """
        if not self.conn:
            print("❌ No database connection")
            return False

        try:
            cursor = self.conn.cursor()

            # Prepare data with embeddings and chunking
            print(f"🔄 Chunking and generating embeddings for {len(pages)} pages...")
            rows = []
            total_chunks = 0

            for page_idx, page in enumerate(pages, 1):
                content = page.get('content', '')

                # Chunk the content semantically
                chunks = TextChunker.semantic_chunk(content, chunk_size=1000, overlap=200)
                total_chunks += len(chunks)

                # Process each chunk
                for chunk_idx, chunk in enumerate(chunks, 1):
                    # Generate embedding for this chunk
                    embedding = self._generate_embedding(chunk)

                    # Modify title to indicate chunking (if multiple chunks)
                    original_title = page.get('title', 'Untitled')
                    if len(chunks) > 1:
                        title = f"{original_title} [Chunk {chunk_idx}/{len(chunks)}]"
                        description = f"Part {chunk_idx} of {len(chunks)}"
                    else:
                        title = original_title
                        description = page.get('description', '')

                    rows.append((
                        session_id,
                        page.get('url'),
                        title,
                        description,
                        page.get('page_type'),
                        chunk,  # Store chunk, not full content
                        len(chunk.split()),  # Word count for this chunk
                        embedding
                    ))

                if page_idx % 5 == 0 or page_idx == len(pages):
                    print(f"   Processed {page_idx}/{len(pages)} pages ({total_chunks} chunks so far)...")

            # Batch insert all chunks
            execute_values(
                cursor,
                """
                INSERT INTO scraped_pages
                (session_id, url, title, description, page_type,
                 content, word_count, content_embedding)
                VALUES %s
                """,
                rows,
                template="(%s, %s, %s, %s, %s, %s, %s, %s)"
            )

            self.conn.commit()
            cursor.close()

            print(f"✅ Saved {len(pages)} pages as {total_chunks} chunks to database")
            return True

        except Exception as e:
            print(f"❌ Error saving scraped pages: {e}")
            self.conn.rollback()
            return False

    def save_all(
        self,
        data: List[Dict],
        website_url: str,
        domain_name: str,
        stats: Dict
    ) -> bool:
        """
        Save complete scraping session (metadata + pages).

        Args:
            data: List of scraped page dictionaries
            website_url: URL of scraped website
            domain_name: Domain name
            stats: Scraping statistics

        Returns:
            bool: True if successful
        """
        if not self.connect():
            return False

        try:
            # Save session metadata
            print("💾 Saving to database...")
            session_id = self.save_scrape_session(website_url, domain_name, stats)

            if not session_id:
                return False

            # Save pages with embeddings
            success = self.save_scraped_pages(session_id, data)

            return success

        finally:
            self.disconnect()

    def search_similar(
        self,
        query_text: str,
        match_threshold: float = 0.5,
        match_count: int = 10
    ) -> List[Dict]:
        """
        Search for pages similar to query text using vector similarity.

        Args:
            query_text: Text to search for
            match_threshold: Minimum similarity score (0-1)
            match_count: Maximum number of results

        Returns:
            List of matching pages with similarity scores
        """
        if not self.embedding_model:
            print("❌ Embedding model not loaded, cannot search")
            return []

        if not self.connect():
            return []

        try:
            # Generate embedding for query
            query_embedding = self._generate_embedding(query_text)
            if not query_embedding:
                return []

            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM search_similar_content(%s::vector, %s, %s)
            """, (query_embedding, match_threshold, match_count))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'url': row[1],
                    'title': row[2],
                    'page_type': row[3],
                    'content': row[4],
                    'similarity': row[5]
                })

            cursor.close()
            return results

        except Exception as e:
            print(f"❌ Error searching similar content: {e}")
            return []

        finally:
            self.disconnect()

    def get_session_stats(self, session_id: Optional[int] = None) -> List[Dict]:
        """
        Get scraping session statistics.

        Args:
            session_id: Optional session ID, or None for all sessions

        Returns:
            List of session statistics
        """
        if not self.connect():
            return []

        try:
            cursor = self.conn.cursor()

            if session_id:
                cursor.execute("""
                    SELECT * FROM scraping_statistics WHERE id = %s
                """, (session_id,))
            else:
                cursor.execute("""
                    SELECT * FROM scraping_statistics
                    ORDER BY scraped_at DESC
                """)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'website_url': row[1],
                    'domain_name': row[2],
                    'scraped_at': row[3],
                    'pages_scraped': row[4],
                    'total_words': row[5],
                    'total_time_seconds': row[6],
                    'actual_pages_count': row[7],
                    'avg_word_count': row[8],
                    'page_types_breakdown': row[9]
                })

            cursor.close()
            return results

        except Exception as e:
            print(f"❌ Error getting session stats: {e}")
            return []

        finally:
            self.disconnect()
