"""Pydantic models for LLM responses."""
from pydantic import BaseModel
from typing import List

class FilteredURLs(BaseModel):
    """Schema for LLM to return filtered URLs."""
    relevant_urls: List[str]
    reasoning: str  # Why these URLs were selected