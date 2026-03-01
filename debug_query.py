#!/usr/bin/env python3
"""
Debug script to check why specific content isn't being retrieved.
"""
import sys
from utils import DatabaseHandler
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

load_dotenv()

def debug_query(query: str, keyword: str = None):
    """
    Debug why a query isn't retrieving expected content.

    Args:
        query: The search query
        keyword: Keyword to search for in content (e.g., "contact", "email")
    """
    print("=" * 80)
    print("QUERY DEBUG TOOL")
    print("=" * 80)
    print(f"Query: {query}")
    if keyword:
        print(f"Looking for keyword: '{keyword}' in content")
    print("=" * 80)
    print()

    db = DatabaseHandler()

    # Step 1: Check if chunked data exists
    print("Step 1: Checking database for chunked data...")
    if not db.connect():
        print("❌ Cannot connect to database")
        return

    try:
        cursor = db.conn.cursor()

        # Check for chunks
        cursor.execute("SELECT COUNT(*) FROM scraped_pages WHERE title LIKE '%Chunk%'")
        chunk_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM scraped_pages")
        total_count = cursor.fetchone()[0]

        print(f"Total pages/chunks in DB: {total_count}")
        print(f"Pages with [Chunk X/Y] format: {chunk_count}")

        if chunk_count == 0:
            print()
            print("⚠️  WARNING: No chunked data found!")
            print("   Your database still has old (unchunked) data.")
            print("   Solution: Re-scrape the website after implementing chunking.")
            print()
        print()

        # Step 2: Search for keyword in content if provided
        if keyword:
            print(f"Step 2: Searching for keyword '{keyword}' in content...")
            cursor.execute(
                "SELECT id, url, title, LEFT(content, 200) as preview FROM scraped_pages WHERE content ILIKE %s LIMIT 5",
                (f'%{keyword}%',)
            )
            results = cursor.fetchall()

            if results:
                print(f"✅ Found {len(results)} pages containing '{keyword}':")
                for row in results:
                    print(f"\n  ID: {row[0]}")
                    print(f"  URL: {row[1]}")
                    print(f"  Title: {row[2]}")
                    print(f"  Preview: {row[3]}...")
            else:
                print(f"❌ No pages found containing '{keyword}'")
                print()
                print("Possible reasons:")
                print("1. Content wasn't scraped (check if URL was in sitemap)")
                print("2. Content extractor filtered it out (footer, nav, etc.)")
                print("3. Page wasn't scraped due to filters")
                print()
            print()

        # Step 3: Run similarity search
        print("Step 3: Running similarity search...")
        db.disconnect()

        # Search with very low threshold to see all results
        results = db.search_similar(query, match_threshold=0.0, match_count=10)

        if not results:
            print("❌ No results found at all")
            print("   Database might be empty")
            return

        print(f"Top 10 results (showing all similarities):")
        print()

        for idx, result in enumerate(results, 1):
            print(f"{idx}. Similarity: {result['similarity']:.4f} ({result['similarity']:.2%})")
            print(f"   Title: {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   Preview: {result['content'][:150]}...")

            # Highlight if this contains the keyword
            if keyword and keyword.lower() in result['content'].lower():
                print(f"   ✅ Contains keyword '{keyword}'!")
            print()

        # Step 4: Show highest similarity
        highest = results[0]
        print("=" * 80)
        print("DIAGNOSIS")
        print("=" * 80)
        print(f"Highest similarity score: {highest['similarity']:.4f} ({highest['similarity']:.2%})")
        print()

        if keyword:
            # Check if keyword page is in results
            keyword_in_top = any(keyword.lower() in r['content'].lower() for r in results)
            if keyword_in_top:
                keyword_result = [r for r in results if keyword.lower() in r['content'].lower()][0]
                print(f"✅ Page with '{keyword}' found in results!")
                print(f"   Its similarity: {keyword_result['similarity']:.4f}")
                print()

                if keyword_result['similarity'] < 0.5:
                    print("⚠️  ISSUE: Similarity too low (< 0.5)")
                    print()
                    print("Possible solutions:")
                    print("1. Adjust query wording to match content better")
                    print("2. Lower the retrieval threshold (--threshold 0.3)")
                    print("3. Content chunk might be too short/generic")
                    print()

                    # Show the actual content
                    print("Actual content in database:")
                    print("-" * 80)
                    print(keyword_result['content'])
                    print("-" * 80)
                    print()

            else:
                print(f"❌ Page with '{keyword}' NOT in top 10 results")
                print()
                print("Possible reasons:")
                print("1. Content wasn't scraped at all")
                print("2. Semantic mismatch between query and content")
                print("3. Try searching with threshold=0.0 and limit=50")

        if highest['similarity'] < 0.4:
            print("⚠️  Very low similarity scores overall")
            print("   This suggests semantic mismatch or database has unrelated content")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.disconnect()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_query.py 'your query' [keyword]")
        print()
        print("Examples:")
        print("  python debug_query.py 'where should we call' contact")
        print("  python debug_query.py 'what is the refund policy' refund")
        sys.exit(1)

    query = sys.argv[1]
    keyword = sys.argv[2] if len(sys.argv) > 2 else None

    debug_query(query, keyword)
