# langchain_compat.py
"""
Compatibility layer for different LangChain versions.
"""

try:
    # Try new import structure first
    from langchain_openai import ChatOpenAI
except ImportError:
    # Fall back to old structure
    from langchain.chat_models import ChatOpenAI

try:
    from langchain_community import *
except ImportError:
    from langchain import *

# Export for other modules
__all__ = ['ChatOpenAI']
