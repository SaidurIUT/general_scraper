#!/usr/bin/env python3
"""
Database Search Utility

Search scraped content using vector similarity search.

Usage:
    python search_database.py "privacy policy"
    python search_database.py "data protection" --threshold 0.7
    python search_database.py "cookie policy" --limit 5
"""

import sys
import argparse
from utils import DatabaseHandler


def search(query_text: str, threshold: float = 0.5, limit: int = 10):
    """
    Search for similar content in the database.

    Args:
        query_text: Text to search for
        threshold: Minimum similarity score (0-1)
        limit: Maximum number of results
    """
    print("=" * 80)
    print("VECTOR SIMILARITY SEARCH")
    print("=" * 80)
    print(f"Query: {query_text}")
    print(f"Threshold: {threshold}")
    print(f"Limit: {limit}")
    print("=" * 80)
    print()

    db_handler = DatabaseHandler()

    print("🔍 Searching database...")
    results = db_handler.search_similar(query_text, threshold, limit)

    if not results:
        print("❌ No results found")
        print("\nTips:")
        print("- Try lowering the threshold (--threshold 0.3)")
        print("- Make sure data has been scraped to the database")
        print("- Check that embeddings were generated successfully")
        return

    print(f"✅ Found {len(results)} matching pages:\n")

    for idx, result in enumerate(results, 1):
        print(f"{idx}. {result['title'] or 'No Title'}")
        print(f"   Type: {result['page_type']}")
        print(f"   URL: {result['url']}")
        print(f"   Similarity: {result['similarity']:.2%}")
        print(f"   Content preview: {result['content'][:200]}...")
        print()


def list_sessions():
    """List all scraping sessions."""
    print("=" * 80)
    print("SCRAPING SESSIONS")
    print("=" * 80)
    print()

    db_handler = DatabaseHandler()
    sessions = db_handler.get_session_stats()

    if not sessions:
        print("❌ No scraping sessions found")
        print("\nRun the scraper first:")
        print("  python main.py https://www.example.com")
        return

    print(f"Found {len(sessions)} sessions:\n")

    for session in sessions:
        print(f"ID: {session['id']}")
        print(f"Website: {session['website_url']}")
        print(f"Domain: {session['domain_name']}")
        print(f"Scraped: {session['scraped_at']}")
        print(f"Pages: {session['pages_scraped']}")
        print(f"Total Words: {session['total_words']:,}")
        print(f"Time: {session['total_time_seconds']:.2f}s")

        if session['page_types_breakdown']:
            print("Page Types:")
            for page_type, count in session['page_types_breakdown'].items():
                print(f"  - {page_type}: {count}")

        print("-" * 80)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Search scraped content using vector similarity'
    )

    parser.add_argument(
        'query',
        nargs='?',
        help='Search query text'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.5,
        help='Minimum similarity threshold (0-1, default: 0.5)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Maximum number of results (default: 10)'
    )
    parser.add_argument(
        '--list-sessions',
        action='store_true',
        help='List all scraping sessions'
    )

    args = parser.parse_args()

    if args.list_sessions:
        list_sessions()
    elif args.query:
        search(args.query, args.threshold, args.limit)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python search_database.py \"privacy policy\"")
        print("  python search_database.py \"data protection\" --threshold 0.7")
        print("  python search_database.py --list-sessions")


if __name__ == "__main__":
    main()
