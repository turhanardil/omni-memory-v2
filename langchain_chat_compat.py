# langchain_chat_compat.py
"""
Compatibility wrapper for ChatOpenAI to handle import changes.
"""

import warnings

# Suppress the specific deprecation warning
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain.chat_models")

try:
    # Try the new import first
    from langchain_openai import ChatOpenAI
except ImportError:
    try:
        # Fall back to community import
        from langchain_community.chat_models import ChatOpenAI
    except ImportError:
        # Final fallback to old import
        from langchain.chat_models import ChatOpenAI

# Re-export
__all__ = ['ChatOpenAI']