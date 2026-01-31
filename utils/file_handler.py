# utils/file_handler.py

"""File handling utilities for saving scraped data."""
import os
import json
from typing import List, Dict
from datetime import datetime

class FileHandler:
    """Handle file operations for scraped data."""
    
    def __init__(self, output_dir: str = "scraped_data"):
        """
        Initialize file handler.
        
        Args:
            output_dir: Directory to save scraped data
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def _get_website_folder(self, website_name: str) -> str:
        """
        Create and return the folder path for a specific website.
        
        Args:
            website_name: Name of the website
            
        Returns:
            str: Path to the website folder
        """
        folder_path = os.path.join(self.output_dir, website_name)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path
    
    def save_json(self, data: List[Dict], filename: str) -> str:
        """
        Save data to JSON file in website-specific folder.
        
        Args:
            data: List of dictionaries to save
            filename: Name of the website (will be used as folder name)
            
        Returns:
            str: Full path to saved file
        """
        folder_path = self._get_website_folder(filename)
        filepath = os.path.join(folder_path, f"{filename}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def save_text(self, data: List[Dict], filename: str) -> str:
        """
        Save data to readable text file in website-specific folder.
        
        Args:
            data: List of dictionaries to save
            filename: Name of the website (will be used as folder name)
            
        Returns:
            str: Full path to saved file
        """
        folder_path = self._get_website_folder(filename)
        filepath = os.path.join(folder_path, f"{filename}.txt")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Scraped Data Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Pages: {len(data)}\n")
            f.write("=" * 80 + "\n\n")
            
            for idx, item in enumerate(data, 1):
                f.write(f"\n{'=' * 80}\n")
                f.write(f"Page {idx}: {item.get('page_type', 'Unknown')}\n")
                f.write(f"{'=' * 80}\n\n")
                f.write(f"URL: {item.get('url', 'N/A')}\n")
                f.write(f"Title: {item.get('title', 'N/A')}\n")
                f.write(f"Description: {item.get('description', 'N/A')}\n")
                f.write(f"Word Count: {item.get('word_count', 'N/A')}\n")
                f.write(f"\n{'-' * 80}\n")
                f.write("CONTENT:\n")
                f.write(f"{'-' * 80}\n\n")
                f.write(item.get('content', ''))
                f.write("\n\n")
        
        return filepath
    
    def save_markdown(self, data: List[Dict], filename: str) -> str:
        """
        Save data to Markdown file in website-specific folder.
        
        Args:
            data: List of dictionaries to save
            filename: Name of the website (will be used as folder name)
            
        Returns:
            str: Full path to saved file
        """
        folder_path = self._get_website_folder(filename)
        filepath = os.path.join(folder_path, f"{filename}.md")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Scraped Data Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
            f.write(f"**Total Pages:** {len(data)}\n\n")
            f.write("---\n\n")
            
            for idx, item in enumerate(data, 1):
                f.write(f"## {idx}. {item.get('page_type', 'Unknown')}\n\n")
                f.write(f"**URL:** [{item.get('url', 'N/A')}]({item.get('url', '#')})\n\n")
                f.write(f"**Title:** {item.get('title', 'N/A')}  \n")
                f.write(f"**Description:** {item.get('description', 'N/A')}  \n")
                f.write(f"**Word Count:** {item.get('word_count', 'N/A')}\n\n")
                f.write("### Content\n\n")
                f.write(item.get('content', ''))
                f.write("\n\n---\n\n")
        
        return filepath
    
    def save_summary(self, filename: str, stats: Dict) -> str:
        """
        Save scraping summary to a text file.
        
        Args:
            filename: Name of the website (will be used as folder name)
            stats: Dictionary containing scraping statistics
            
        Returns:
            str: Full path to saved summary file
        """
        folder_path = self._get_website_folder(filename)
        filepath = os.path.join(folder_path, "summary.txt")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("📊 SCRAPING SUMMARY\n")
            f.write("=" * 80 + "\n")
            f.write(f"Website: {stats.get('website', 'N/A')}\n")
            f.write(f"Scraped: {stats.get('timestamp', 'N/A')}\n")
            f.write(f"URLs Discovered: {stats.get('urls_discovered', 'N/A')}\n")
            f.write(f"Relevant URLs: {stats.get('relevant_urls', 0)}\n")
            f.write(f"Pages Scraped: {stats.get('pages_scraped', 0)}\n")
            f.write(f"Total Words: {stats.get('total_words', 0):,}\n")
            
            if stats.get('page_types'):
                f.write("\nPage Types:\n")
                for page_type, count in sorted(stats['page_types'].items()):
                    f.write(f"  - {page_type}: {count}\n")
            
            f.write("=" * 80 + "\n")
            f.write(f"⏱️  Total time: {stats.get('total_time', 0):.2f} seconds\n")
        
        return filepath
    
    def save_all_formats(self, data: List[Dict], filename: str, stats: Dict = None) -> Dict[str, str]:
        """
        Save data in all formats (JSON, TXT, MD) and summary in website-specific folder.
        
        Args:
            data: List of dictionaries to save
            filename: Base filename (website name, will be used as folder name)
            stats: Optional scraping statistics for summary file
            
        Returns:
            Dict with format names and their file paths
        """
        result = {
            'json': self.save_json(data, filename),
            'text': self.save_text(data, filename),
            'markdown': self.save_markdown(data, filename),
        }
        
        if stats:
            result['summary'] = self.save_summary(filename, stats)
        
        return result