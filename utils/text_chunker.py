"""Text chunking utilities for semantic text splitting."""
import re
from typing import List


class TextChunker:
    """Handles semantic chunking of text for embedding generation."""

    @staticmethod
    def semantic_chunk(
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[str]:
        """
        Split text into semantic chunks based on paragraphs and sentences.

        Args:
            text: Text to chunk
            chunk_size: Target size of each chunk in characters
            overlap: Number of characters to overlap between chunks

        Returns:
            List of text chunks
        """
        if not text or len(text) <= chunk_size:
            return [text] if text else []

        # Split by paragraphs first (double newline or single newline)
        
        paragraphs = re.split(r'\n\s*\n|\n', text)

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph exceeds chunk_size, save current chunk
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())

                # Create overlap by keeping last 'overlap' characters
                if overlap > 0 and len(current_chunk) > overlap:
                    current_chunk = current_chunk[-overlap:] + " " + para
                else:
                    current_chunk = para
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # Handle edge case: if a single paragraph is too large, split by sentences
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > chunk_size * 1.5:  # 50% tolerance
                # Split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', chunk)
                sub_chunk = ""
                for sent in sentences:
                    if len(sub_chunk) + len(sent) > chunk_size and sub_chunk:
                        final_chunks.append(sub_chunk.strip())
                        sub_chunk = sent
                    else:
                        sub_chunk += " " + sent if sub_chunk else sent
                if sub_chunk.strip():
                    final_chunks.append(sub_chunk.strip())
            else:
                final_chunks.append(chunk)

        return final_chunks if final_chunks else [text]
