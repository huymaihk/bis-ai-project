"""Real HTTP boundary against temporary storage; no external APIs or production writes."""
import json
from pathlib import Path
import tempfile
import unittest
import pymupdf
from fastapi.testclient import TestClient
from bis_api import create_app

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.row={'sku':'03026A','product_name':'Sổ tay','product_name_en':'Manual','status':'APPROVED','_review_hash':'old'}
        (self.root/'extracted_products_cache.json').write_text(json.dumps([self.row]),encoding='utf-8')
        with pymupdf.open() as d:
            d.new_page().insert_text((40,40),'03026A Manual')
            d.save(self.root/'catalogue_sample.pdf')
        (self.root/'service_account.json').write_text('{"private":"secret"}')
        self.client=TestClient(create_app(self.root,pin='test-pin'))
        self.client.headers['X-BIS-Request']='1'

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def login(self):
        self.assertEqual(self.client.post('/api/login',json={'pin':'test-pin'}).status_code,200)

    def test_login_required_and_logout(self):
        for route in ['state','assets','memory','knowledge/search']:
            self.assertEqual(self.client.get('/api/'+route).status_code,401)
        self.login()
        self.assertEqual(self.client.get('/api/state').status_code,200)
        self.client.post('/api/logout')
        self.assertEqual(self.client.get('/api/state').status_code,401)

    def test_cross_origin_and_missing_header_blocked(self):
        self.assertEqual(self.client.post('/api/login',json={'pin':'test-pin'},headers={'Origin':'https://evil.test'}).status_code,403)
        del self.client.headers['X-BIS-Request']
        self.assertEqual(self.client.post('/api/login',json={'pin':'test-pin'}).status_code,403)

    def test_pin_rate_limit(self):
        for _ in range(10):
            self.assertEqual(self.client.post('/api/login',json={'pin':'wrong'}).status_code,401)
        self.assertEqual(self.client.post('/api/login',json={'pin':'test-pin'}).status_code,429)

    def test_edit_persists_revokes_approval_and_rejects_stale_writer(self):
        self.login()
        row=self.client.get('/api/state').json()['products'][0]
        edit={'revision':row['_revision'],'fields':{'product_name':'Tên đã sửa'}}
        result=self.client.put('/api/products/03026A',json=edit)
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(result.json()['status'],'EXTRACTED_UNVERIFIED')
        self.assertNotIn('_review_hash',result.json())
        self.assertEqual(self.client.put('/api/products/03026A',json=edit).status_code,409)
        other=TestClient(create_app(self.root,pin='test-pin'))
        other.post('/api/login',json={'pin':'test-pin'},headers={'X-BIS-Request':'1'})
        self.assertEqual(other.get('/api/state').json()['products'][0]['product_name'],'Tên đã sửa')
        other.close()
        self.assertEqual(json.loads((self.root/'extracted_products_cache.json').read_text())[0]['product_name'],'Sổ tay')

    def test_cannot_set_approval(self):
        self.login()
        row=self.client.get('/api/state').json()['products'][0]
        result=self.client.put('/api/products/03026A',json={'revision':row['_revision'],'fields':{'status':'APPROVED'}})
        self.assertEqual(result.status_code,422)

    def test_asset_allowlist_and_pdf(self):
        self.login()
        assets=self.client.get('/api/assets').json()
        self.assertEqual(len(assets),1)
        url=assets[0]['url']
        self.assertEqual(self.client.get(url).headers['content-type'],'application/pdf')
        self.assertEqual(self.client.get(url+'/page/1').headers['content-type'],'image/png')
        self.assertEqual(self.client.get(url+'/page/99').status_code,422)
        self.assertEqual(self.client.get('/api/assets/service_account.json').status_code,404)

    def test_memory_revision_history_conflict_and_revoke(self):
        self.login()
        first={'key':'user:rule','content':'Nội dung đầu','expected':[]}
        result=self.client.post('/api/memory',json=first)
        self.assertEqual(result.status_code,200)
        version=result.json()['id']
        self.assertEqual(self.client.post('/api/memory',json=first).status_code,409)
        self.assertEqual(self.client.post('/api/memory',json={**first,'expected':[version],'deleted':True}).status_code,200)
        self.assertFalse(any(r['key']=='user:rule' for r in self.client.get('/api/memory').json()))
        history=self.client.get('/api/memory/history',params={'key':'user:rule'}).json()
        self.assertEqual(len(history),2)

    def test_publish_not_exposed(self):
        self.login()
        self.assertFalse(self.client.get('/api/state').json()['capabilities']['publish'])
        self.assertNotEqual(self.client.post('/api/operations/haravan/create-draft',json={}).status_code,200)
        self.assertNotEqual(self.client.delete('/api/products/03026A').status_code,200)

if __name__=='__main__':
    unittest.main()
