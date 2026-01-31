# config/__init__.py

from .browser_config import get_browser_config
from .llm_config import get_llm_config, get_default_search_prompt

__all__ = ['get_browser_config', 'get_llm_config', 'get_default_search_prompt']