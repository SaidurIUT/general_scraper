# config/llm_config.py

"""LLM configuration for URL filtering."""
import os

def get_llm_config():
    """Configure the LLM for URL filtering."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://10.112.30.10:11434")
    model = os.getenv("OLLAMA_MODEL", "ollama/phi4-mini-reasoning")
    
    return {
        'provider': model,
        'base_url': base_url
    }

def get_default_search_prompt():
    """Get the default search prompt for URL filtering."""
    return os.getenv("SEARCH_PROMPT", (
        "Find URLs related to company policies, privacy policy, terms of service, "
        "data protection, cookie policy, acceptable use policy, and compliance documents."
    ))