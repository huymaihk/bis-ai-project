"""Repair stale Streamlit resource instances without clearing unrelated caches."""
import importlib
import inspect


def compatible(agent):
    try:
        return callable(getattr(agent, '_extract_fallback_from_text', None)) and 'page_text' in inspect.signature(agent.extract_page).parameters
    except (AttributeError, TypeError, ValueError):
        return False


def ensure_current_technical(agent, root):
    if compatible(agent):
        return agent
    module = importlib.import_module('agent_technical')
    if not compatible(module.AgentTechnical):
        importlib.reload(importlib.import_module('config'))
        module = importlib.reload(module)
    current = module.AgentTechnical(root)
    if not compatible(current):
        raise RuntimeError('Technical module is incompatible; restart application runtime')
    return current
