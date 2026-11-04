"""Refresh incompatible cached modules during Streamlit hot deployment."""
import importlib

PROTOCOL = 'workflow-v2-1'


def render_current_workspace(root, services):
    api = importlib.import_module('bis_api')
    refresh_api = getattr(api, 'API_PROTOCOL', None) != PROTOCOL
    if refresh_api:
        importlib.reload(api)
    host = importlib.import_module('streamlit_react_host')
    if refresh_api or getattr(host, 'BRIDGE_PROTOCOL', None) != PROTOCOL:
        host = importlib.reload(host)
    host.render_react_workspace(root, services)
