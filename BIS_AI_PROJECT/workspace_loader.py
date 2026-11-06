"""Refresh incompatible cached modules during Streamlit hot deployment."""
import importlib

PROTOCOL = 'workflow-v2-24'


def render_current_workspace(root, services):
    api = importlib.import_module('bis_api')
    refresh_api = getattr(api, 'API_PROTOCOL', None) != PROTOCOL
    if refresh_api:
        # Refresh dependencies before recreating each session's API/agent.
        for name in ('config', 'gemini_fallback', 'agent_technical', 'technical_names', 'marketing_content', 'product_quality', 'media_quality', 'studio_ai', 'studio_api', 'completed_images', 'raw_image_store', 'pdf_analysis_cache', 'readonly_duplicates'):
            importlib.reload(importlib.import_module(name))
        importlib.reload(api)
    host = importlib.import_module('streamlit_react_host')
    if refresh_api or getattr(host, 'BRIDGE_PROTOCOL', None) != PROTOCOL:
        host = importlib.reload(host)
    # Native tools can remain cached across a deploy too.
    import inspect
    native = importlib.import_module('production_workspace')
    if refresh_api or 'active_step' not in inspect.signature(native.render_workspace).parameters:
        importlib.reload(native)
    host.render_react_workspace(root, services)

