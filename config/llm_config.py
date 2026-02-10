# config/llm_config.py

"""LLM configuration for URL filtering."""
import os

def get_llm_config():
    base_url = os.getenv("OLLAMA_BASE_URL", "http://10.112.30.10:11434")
    model = os.getenv("OLLAMA_MODEL", "ollama/phi4-mini-reasoning")
    
    return {
        'provider': model,
        'base_url': base_url
    }

def get_default_search_prompt():
    return os.getenv("SEARCH_PROMPT", (
        "Build a comprehensive knowledge base for a website chatbot. "
        "Include pages about company information, services, locations, contact details, "
        "policies (privacy, terms, legal), support resources, FAQ, documentation, "
        "about pages, team information, news, blog posts, and any informational content "
        "that helps answer user questions. Exclude individual product listings, "
        "user account pages, shopping carts, and search/filter results."
    ))