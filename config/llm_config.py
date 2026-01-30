"""LLM configuration for URL filtering."""
import os

def get_llm_config():
    """
    Configure the LLM for URL filtering.
    
    Returns:
        dict: LLM configuration dictionary with 'base_url' and 'provider'
    """
    base_url = os.getenv("OLLAMA_BASE_URL", "http://10.112.30.10:11434")
    model = os.getenv("OLLAMA_MODEL", "ollama/phi4-mini-reasoning")
    
    return {
        'provider': model,
        'base_url': base_url
    }

def get_search_prompt():
    """
    Get the search prompt from environment or use default.
    
    Returns:
        str: The search prompt for URL filtering
    """
    default_prompt = (
        "Find URLs related to company policies, privacy policy, terms of service, "
        "data protection, cookie policy, acceptable use policy, and compliance documents."
    )
    return os.getenv("SEARCH_PROMPT", default_prompt)