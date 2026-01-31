"""Database configuration for PostgreSQL with pgvector."""
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:
    """Database configuration settings."""

    HOST = os.getenv('DB_HOST', 'localhost')
    PORT = int(os.getenv('DB_PORT', 5432))
    NAME = os.getenv('DB_NAME', 'scraper_db')
    USER = os.getenv('DB_USER', 'postgres')
    PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')

    @classmethod
    def get_connection_string(cls) -> str:
        """
        Get PostgreSQL connection string.

        Returns:
            str: PostgreSQL connection string
        """
        return f"dbname={cls.NAME} user={cls.USER} password={cls.PASSWORD} host={cls.HOST} port={cls.PORT}"

    @classmethod
    def get_connection_params(cls) -> dict:
        """
        Get connection parameters as dictionary.

        Returns:
            dict: Connection parameters
        """
        return {
            'host': cls.HOST,
            'port': cls.PORT,
            'dbname': cls.NAME,
            'user': cls.USER,
            'password': cls.PASSWORD
        }
