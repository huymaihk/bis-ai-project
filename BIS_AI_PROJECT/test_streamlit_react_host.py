import base64
import json
import tempfile
import unittest
from pathlib import Path
from streamlit_react_host import SessionBridge


class ComponentBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.bridge=SessionBridge(Path(self.tmp.name))

    def tearDown(self):
        self.bridge.client.close()
        self.tmp.cleanup()

    def test_hot_deploy_reloads_old_one_argument_renderer(self):
        import bis_api
        import streamlit_react_host as host
        import inspect
        from workspace_loader import render_current_workspace, PROTOCOL
        from unittest.mock import patch
        with patch.object(bis_api,'API_PROTOCOL','old'), patch.object(host,'BRIDGE_PROTOCOL','old'), patch.object(host,'render_react_workspace',lambda root:None):
            with patch.object(host.st,'session_state',{'authenticated':False}), patch.object(host.st,'error'):
                render_current_workspace(Path(self.tmp.name),(None,)*5)
            self.assertIn('services',inspect.signature(host.render_react_workspace).parameters)
            self.assertEqual(bis_api.API_PROTOCOL,PROTOCOL)
            self.assertEqual(host.BRIDGE_PROTOCOL,PROTOCOL)

    def test_old_session_bridge_is_recreated(self):
        import streamlit_react_host as host
        from types import SimpleNamespace
        from unittest.mock import Mock,patch
        root=Path(self.tmp.name)
        folder=root/'frontend'/'streamlit_dist'
        folder.mkdir(parents=True)
        (folder/'index.html').write_text('test')
        old=SimpleNamespace(client=Mock())
        state={'authenticated':True,'_bis_react_bridge':old,'_bis_react_response':{'old':True},'_bis_native_step':2}
        with patch.object(host.st,'session_state',state), patch.object(host.st,'markdown'), patch.object(host.components,'declare_component',return_value=lambda **kw:None):
            host.render_react_workspace(root)
        old.client.close.assert_called_once()
        self.assertNotIn('_bis_react_response',state)
        self.assertNotIn('_bis_native_step',state)
        self.assertEqual(state['_bis_react_bridge'].protocol,host.BRIDGE_PROTOCOL)
        state['_bis_react_bridge'].client.close()

    def test_authenticated_state_transport(self):
        result=self.bridge.dispatch({'id':'state','url':'/api/state','method':'GET'})
        self.assertEqual(result['status'],200)
        self.assertEqual(json.loads(base64.b64decode(result['body']))['products'],[])

    def test_block_external_urls_and_auth_changes(self):
        for url in ['https://evil.test/api/state','//evil.test/api/state','/api/login','/api/logout','/config.py']:
            self.assertIn('error',self.bridge.dispatch({'id':url,'url':url,'method':'GET'}))

    def test_write_replay_does_not_duplicate_event(self):
        request={'id':'write','url':'/api/memory','method':'POST','body':json.dumps({'key':'user:test','content':'Verified note','expected':[]})}
        result=self.bridge.dispatch(request)
        self.assertEqual(result['status'],200)
        self.assertEqual(self.bridge.dispatch(request),result)
        history=self.bridge.client.get('/api/memory/history',params={'key':'user:test'}).json()
        self.assertEqual(len(history),1)

if __name__=='__main__':
    unittest.main()
