"""Streamlit authenticated session -> local ASGI calls. No publicly exposed API port."""
import base64
import json
from pathlib import Path
import secrets
from urllib.parse import urlsplit
import streamlit as st
import streamlit.components.v1 as components
from fastapi.testclient import TestClient
from bis_api import create_app

BRIDGE_PROTOCOL = 'workflow-v2-7'


class SessionBridge:
    def __init__(self,root):
        self.protocol = BRIDGE_PROTOCOL
        pin=secrets.token_urlsafe(32)
        self.client=TestClient(create_app(root,pin=pin))
        self.client.headers['X-BIS-Request']='1'
        self.client.post('/api/login',json={'pin':pin}).raise_for_status()
        self.responses={}

    def dispatch(self,request):
        ident=request.get('id')
        if not isinstance(ident,str) or len(ident)>100:
            return {'id':ident,'error':'Mã yêu cầu không hợp lệ'}
        if ident in self.responses:
            return self.responses[ident]
        url=request.get('url','')
        method=request.get('method','GET')
        parts=urlsplit(url)
        if parts.scheme or parts.netloc or not parts.path.startswith('/api/') or parts.path in {'/api/login','/api/logout'} or method not in {'GET','POST','PUT'}:
            result={'id':ident,'error':'Yêu cầu không được phép'}
        elif len(request.get('body') or '')>100000:
            result={'id':ident,'error':'Yêu cầu quá dài'}
        else:
            try:
                response=self.client.request(method,url,content=request.get('body'),headers={'Content-Type':'application/json'})
                if response.status_code==401:
                    result={'id':ident,'error':'Phiên đã hết hạn. Tải lại trang để đăng nhập lại.'}
                elif len(response.content)>20*1024*1024:
                    result={'id':ident,'error':'Tệp vượt 20 MB; dùng công cụ Streamlit để đọc tệp lớn.'}
                else:
                    result={'id':ident,'status':response.status_code,'content_type':response.headers.get('content-type','application/json'),
                            'body':base64.b64encode(response.content).decode()}
            except Exception as exc:
                result={'id':ident,'error':'Chưa xử lý được yêu cầu: '+type(exc).__name__}
        self.responses[ident]=result
        # Retain request IDs to prevent replay of writes; keep large payloads only for current reply.
        for key in list(self.responses)[:-1]:
            self.responses[key]={'id':key,'error':'Yêu cầu đã xử lý; vui lòng tải lại dữ liệu.'}
        return result


def render_react_workspace(root, services=None):
    if not st.session_state.get('authenticated'):
        st.error('Cần đăng nhập trước khi mở BIS.')
        return
    folder=Path(root)/'frontend'/'streamlit_dist'
    if not (folder/'index.html').exists():
        st.error('Thiếu bản build giao diện React.')
        return
    existing = st.session_state.get('_bis_react_bridge')
    if existing is not None and getattr(existing, 'protocol', None) != BRIDGE_PROTOCOL:
        existing.client.close()
        for key in ['_bis_react_bridge', '_bis_react_response', '_bis_react_last_request', '_bis_native_step']:
            st.session_state.pop(key, None)
    if '_bis_react_bridge' not in st.session_state:
        st.session_state['_bis_react_bridge']=SessionBridge(root)
    bridge=st.session_state['_bis_react_bridge']
    if services and '_bis_native_step' in st.session_state:
        from production_workspace import render_workspace
        if st.button('← Quay lại trung tâm BIS', key='bis_back_react'):
            bridge.client.app.state.preferred_sku = st.session_state.get('q_sku', '')
            st.session_state.pop('_bis_native_step', None)
            st.session_state.pop('_bis_react_response', None)
            st.rerun()
        st.caption('Công cụ nghiệp vụ BIS · cùng hồ sơ sản phẩm và bộ nhớ · kết quả cần nghiệm thu')
        render_workspace(root, *services, active_step=st.session_state['_bis_native_step'])
        return
    component=components.declare_component('bis_workspace',path=str(folder))
    st.markdown('''<style>
    section[data-testid="stMain"] .block-container,
    [data-testid="stMainBlockContainer"]{width:100%!important;max-width:none!important;padding:3.25rem 0 0!important;}
    iframe[title="streamlit_react_host.bis_workspace"]{border:0;display:block;width:100%!important;}
    </style>''',unsafe_allow_html=True)
    request=component(response=st.session_state.get('_bis_react_response'),key='bis_live_workspace',default=None)
    if isinstance(request,dict) and request.get('id')!=st.session_state.get('_bis_react_last_request'):
        if request.get('url')=='/api/logout' and request.get('method')=='POST':
            bridge.client.close()
            st.session_state.authenticated=False
            for key in ['_bis_react_bridge','_bis_react_response','_bis_react_last_request']:
                st.session_state.pop(key,None)
            st.rerun()
        st.session_state['_bis_react_response']=bridge.dispatch(request)
        response = st.session_state['_bis_react_response']
        if services and request.get('url') == '/api/workspace/open' and request.get('method') == 'POST' and response.get('status') == 200:
            selected = json.loads(base64.b64decode(response['body']))
            st.session_state['_bis_native_step'] = selected['step']
            if selected['sku']:
                st.session_state['q_sku'] = selected['sku']
        st.session_state['_bis_react_last_request']=request.get('id')
        st.rerun()

