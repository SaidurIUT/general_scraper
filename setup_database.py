#!/usr/bin/env python3
"""
Database Setup Script

This script initializes the PostgreSQL database with pgvector extension
and creates the required tables for the scraper.

Usage:
    python setup_database.py
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
from config.db_config import DatabaseConfig


def create_database():
    """Create the database if it doesn't exist."""
    config = DatabaseConfig()

    print(f"🔧 Setting up database: {config.NAME}")
    print(f"   Host: {config.HOST}:{config.PORT}")
    print(f"   User: {config.USER}")
    print()

    try:
        # Connect to PostgreSQL server (not to specific database)
        conn = psycopg2.connect(
            host=config.HOST,
            port=config.PORT,
            user=config.USER,
            password=config.PASSWORD,
            dbname='postgres'  # Connect to default database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (config.NAME,)
        )
        exists = cursor.fetchone()

        if exists:
            print(f"✅ Database '{config.NAME}' already exists")
        else:
            # Create database
            cursor.execute(f'CREATE DATABASE {config.NAME}')
            print(f"✅ Created database '{config.NAME}'")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error creating database: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is installed and running")
        print("2. Check your database credentials in .env file")
        print("3. Ensure your user has permission to create databases")
        sys.exit(1)


def setup_schema():
    """Create tables and extensions using schema.sql."""
    config = DatabaseConfig()

    try:
        # Connect to the specific database
        conn = psycopg2.connect(**config.get_connection_params())
        cursor = conn.cursor()

        print("📋 Reading schema.sql...")

        # Read and execute schema.sql
        with open('schema.sql', 'r') as f:
            schema_sql = f.read()

        print("🔧 Creating extensions and tables...")
        cursor.execute(schema_sql)
        conn.commit()

        print("✅ Schema created successfully")

        # Verify tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)

        tables = cursor.fetchall()
        print(f"\n📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")

        # Verify pgvector extension
        cursor.execute("""
            SELECT extname, extversion
            FROM pg_extension
            WHERE extname = 'vector'
        """)

        vector_ext = cursor.fetchone()
        if vector_ext:
            print(f"\n✅ pgvector extension installed (version {vector_ext[1]})")
        else:
            print("\n⚠️  pgvector extension not found!")
            print("   Install it with: CREATE EXTENSION vector;")

        cursor.close()
        conn.close()

    except FileNotFoundError:
        print("❌ Error: schema.sql file not found")
        print("   Make sure you're running this script from the project root directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error setting up schema: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure pgvector extension is installed in PostgreSQL")
        print("   Ubuntu/Debian: apt install postgresql-16-pgvector")
        print("   macOS: brew install pgvector")
        print("   Or build from source: https://github.com/pgvector/pgvector")
        print("2. Check if your user has permission to create extensions")
        sys.exit(1)


def test_connection():
    """Test database connection and vector operations."""
    config = DatabaseConfig()

    try:
        conn = psycopg2.connect(**config.get_connection_params())
        cursor = conn.cursor()

        # Test basic query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"\n✅ Connection test successful")
        print(f"   PostgreSQL version: {version.split(',')[0]}")

        # Test vector operations
        cursor.execute("SELECT '[1,2,3]'::vector")
        print("✅ Vector operations working")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n❌ Connection test failed: {e}")
        sys.exit(1)


def main():
    """Main setup function."""
    print("=" * 80)
    print("POLICY SCRAPER - DATABASE SETUP")
    print("=" * 80)
    print()

    # Step 1: Create database
    create_database()
    print()

    # Step 2: Create schema
    setup_schema()
    print()

    # Step 3: Test connection
    test_connection()

    print()
    print("=" * 80)
    print("✅ DATABASE SETUP COMPLETE!")
    print("=" * 80)
    print()
    print("You can now run the scraper:")
    print("  python main.py https://www.example.com")
    print()
    print("To skip database storage:")
    print("  python main.py https://www.example.com --no-db")
    print()


if __name__ == "__main__":
    main()
