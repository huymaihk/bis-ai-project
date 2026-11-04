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
