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

    def test_workflow_review_is_authenticated_and_never_grants_publish(self):
        path='/api/workflow/03026A/check'
        self.assertEqual(self.client.get(path).status_code,401)
        self.login()
        row=self.client.get('/api/state').json()['products'][0]
        from unittest.mock import patch
        with patch('requests.sessions.Session.request', side_effect=AssertionError('No external calls')):
            result=self.client.post(path,json={'revision':row['_revision']})
        self.assertEqual(result.status_code,200,result.text)
        report=result.json()
        self.assertFalse(report['publish_allowed'])
        self.assertIn('BLOCKED',[c['state'] for c in report['checks']])
        self.assertEqual(self.client.get('/api/state').json()['products'][0]['_revision'],row['_revision'])
        self.client.put('/api/products/03026A',json={'revision':row['_revision'],'fields':{'description':'changed'}})
        self.assertTrue(self.client.get(path).json()['stale'])
        self.assertEqual(self.client.post(path,json={'revision':row['_revision']}).status_code,409)

    def test_workspace_route_validates_step_and_sku(self):
        self.login()
        for payload in [{'step':5,'sku':'03026A'},{'step':-1},{'step':2,'sku':'missing'}]:
            self.assertIn(self.client.post('/api/workspace/open',json=payload).status_code,[422,404])
        self.assertEqual(self.client.post('/api/workspace/open',json={'step':2,'sku':'03026A'}).json(),{'step':2,'sku':'03026A'})
        self.assertEqual(self.client.get('/api/state').json()['preferred_sku'],'03026A')

    def test_changed_image_fails_review(self):
        from PIL import Image
        import hashlib
        self.login()
        folder=self.root/'Google_Drive_Storage'
        image=folder/'approved.png'
        Image.new('RGB',(1254,1254),'white').save(image)
        manifest={'03026A':{'final_image':str(image),'status':'APPROVED','approved_sha256':hashlib.sha256(image.read_bytes()).hexdigest()}}
        (folder/'image_review_manifest.json').write_text(json.dumps(manifest))
        row=self.client.get('/api/state').json()['products'][0]
        path='/api/workflow/03026A/check'
        def image_state():
            report=self.client.post(path,json={'revision':row['_revision']}).json()
            return next(c['state'] for c in report['checks'] if c['key']=='images')
        self.assertEqual(image_state(),'PASS')
        Image.new('RGB',(1254,1254),'black').save(image)
        self.assertEqual(image_state(),'BLOCKED')

    def test_catalogue_scan_analyse_confirm_and_changed_file(self):
        from types import SimpleNamespace
        import shutil
        folder=self.root/'Google_Drive_Storage'/'1_Catalogues'
        folder.mkdir(parents=True)
        path=folder/'test.pdf'
        shutil.copyfile(self.root/'catalogue_sample.pdf',path)
        self.assertEqual(self.client.get('/api/catalogues').status_code,401)
        self.login()
        row=self.client.post('/api/catalogues/scan',json={}).json()['files'][0]
        self.assertEqual(row['state'],'NEW')
        self.client.app.state.catalogue_agent=SimpleNamespace(extract_page=lambda *args:[dict(self.row)])
        base='/api/catalogues/'+row['id']
        run=self.client.post(base+'/start',json={'sha256':row['sha256']}).json()
        result=self.client.post(base+'/page',json={'run':run['run'],'page':1})
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(result.json()['state'],'COMPLETED')
        self.assertEqual(self.client.post(base+'/start',json={'sha256':row['sha256']}).status_code,409)
        self.assertEqual(self.client.post(base+'/start',json={'sha256':row['sha256'],'confirm':True}).status_code,200)
        path.write_bytes(path.read_bytes()+b'\n% changed')
        self.assertEqual(self.client.get('/api/catalogues').json()['files'][0]['state'],'NEW')
        self.assertEqual(self.client.post(base+'/start',json={'sha256':row['sha256']}).status_code,409)

    def test_catalogue_names_reject_only_known_test_approval(self):
        from persistent_memory import MemoryStore
        from technical_names import name_review, name_key
        memory=MemoryStore(self.root)
        row=dict(sku='08336A',product_name_en='DYEING PRIMER',product_name='Sai',_source_sha256='hash')
        import json
        memory.revise(name_key('doc',row),json.dumps(dict(name='Sách Vỡ Lòng Về Nhuộm Vải (Đã duyệt kỹ thuật)',sha256='hash')))
        review=name_review(memory,'doc',row)
        self.assertEqual(review['state'],'NEEDS_REVIEW')
        self.assertEqual(review['display_name'],'Sách nhập môn kỹ thuật nhuộm (bìa cứng)')
        memory.revise(name_key('doc',row),json.dumps(dict(name='Tên do chuyên viên sửa',sha256='hash')))
        self.assertEqual(name_review(memory,'doc',row)['display_name'],'Tên do chuyên viên sửa')
        row['product_name_en']='Other product'
        self.assertEqual(name_review(memory,'doc',row)['suggested_name'],'')

    def test_name_review_source_and_stale_document(self):
        from types import SimpleNamespace
        import shutil
        folder=self.root/'Google_Drive_Storage'/'1_Catalogues'
        folder.mkdir(parents=True)
        path=folder/'test.pdf'
        shutil.copyfile(self.root/'catalogue_sample.pdf',path)
        self.login()
        file=self.client.get('/api/catalogues').json()['files'][0]
        base='/api/catalogues/'+file['id']
        self.client.app.state.catalogue_agent=SimpleNamespace(extract_page=lambda *args:[dict(self.row,product_name_en='DYEING PRIMER (Hardbound)',sku='08336A')])
        run=self.client.post(base+'/start',json={'sha256':file['sha256']}).json()
        self.assertEqual(self.client.post(base+'/page',json={'run':run['run'],'page':1}).status_code,200)
        row=self.client.get(base+'/results').json()['products'][0]
        self.assertEqual(row['name_review']['state'],'NEEDS_REVIEW')
        self.assertTrue(row['name_review']['suggested_name'])
        payload=dict(product_name_en='DYEING PRIMER (Hardbound)',sku='08336A',sha256=file['sha256'],name='Sách Nhập môn Kỹ thuật Nhuộm',revision=[])
        response=self.client.post(base+'/name',json=payload)
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['state'],'NAME_APPROVED')
        self.assertEqual(self.client.post(base+'/name',json=payload).status_code,409)
        self.assertEqual(self.client.get(base+'/results').json()['products'][0]['name_review']['suggested_name'],payload['name'])
        self.assertEqual(self.client.get(base+'/source/1',params={'sha256':file['sha256']}).status_code,200)
        self.assertEqual(self.client.get(base+'/source/999',params={'sha256':file['sha256']}).status_code,422)
        path.write_bytes(path.read_bytes()+b'\n% changed')
        self.assertEqual(self.client.get(base+'/results').json()['products'],[])
        self.assertEqual(self.client.post(base+'/name',json=payload).status_code,409)

    def test_empty_ai_result_never_marks_catalogue_green(self):
        from types import SimpleNamespace
        import shutil
        folder=self.root/'Google_Drive_Storage'/'1_Catalogues'
        folder.mkdir(parents=True)
        shutil.copyfile(self.root/'catalogue_sample.pdf',folder/'test.pdf')
        self.login()
        row=self.client.get('/api/catalogues').json()['files'][0]
        self.client.app.state.catalogue_agent=SimpleNamespace(extract_page=lambda *args:[])
        base='/api/catalogues/'+row['id']
        run=self.client.post(base+'/start',json={'sha256':row['sha256']}).json()
        self.assertEqual(self.client.post(base+'/page',json={'run':run['run'],'page':1}).status_code,422)
        self.assertEqual(self.client.get('/api/catalogues').json()['files'][0]['state'],'FAILED')

    def test_local_fallback_requires_review_not_green(self):
        from types import SimpleNamespace
        import shutil
        folder=self.root/'Google_Drive_Storage'/'1_Catalogues'
        folder.mkdir(parents=True)
        shutil.copyfile(self.root/'catalogue_sample.pdf',folder/'test.pdf')
        self.login()
        row=self.client.get('/api/catalogues').json()['files'][0]
        self.client.app.state.catalogue_agent=SimpleNamespace(extract_page=lambda *args:[dict(self.row,analysis_model='PyMuPDF-LocalFallback')])
        base='/api/catalogues/'+row['id']
        run=self.client.post(base+'/start',json={'sha256':row['sha256']}).json()
        self.assertEqual(self.client.post(base+'/page',json={'run':run['run'],'page':1}).status_code,200)
        self.assertEqual(self.client.get('/api/catalogues').json()['files'][0]['state'],'NEEDS_REVIEW')

    def test_valid_empty_cover_is_processed_without_false_green(self):
        from types import SimpleNamespace
        import shutil
        folder=self.root/'Google_Drive_Storage'/'1_Catalogues'
        folder.mkdir(parents=True)
        shutil.copyfile(self.root/'catalogue_sample.pdf',folder/'cover.pdf')
        self.login()
        row=self.client.get('/api/catalogues').json()['files'][0]
        self.client.app.state.catalogue_agent=SimpleNamespace(extract_page=lambda *a:[],last_extraction_status='EMPTY_VALID')
        base='/api/catalogues/'+row['id']
        run=self.client.post(base+'/start',json={'sha256':row['sha256']}).json()
        result=self.client.post(base+'/page',json={'run':run['run'],'page':1})
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(result.json()['empty_pages'],[1])
        self.assertEqual(result.json()['state'],'NEEDS_REVIEW')

    def test_catalogue_range_results_and_sku_reanalysis(self):
        from types import SimpleNamespace
        folder=self.root/'Google_Drive_Storage'/'1_Catalogues'
        folder.mkdir(parents=True)
        with pymupdf.open() as doc:
            for _ in range(3): doc.new_page().insert_text((40,40),'03026A Manual')
            doc.save(folder/'range.pdf')
        self.login()
        row=self.client.get('/api/catalogues').json()['files'][0]
        base='/api/catalogues/'+row['id']
        self.client.app.state.catalogue_agent=SimpleNamespace(extract_page=lambda *a:[dict(self.row)])
        self.assertEqual(self.client.post(base+'/start',json={'sha256':row['sha256'],'start_page':3,'end_page':2}).status_code,422)
        run=self.client.post(base+'/start',json={'sha256':row['sha256'],'start_page':2,'end_page':2}).json()
        self.assertEqual(self.client.post(base+'/page',json={'run':run['run'],'page':1}).status_code,409)
        result=self.client.post(base+'/page',json={'run':run['run'],'page':2}).json()
        self.assertEqual(result['state'],'PARTIAL')
        products=self.client.get(base+'/results').json()['products']
        self.assertEqual(products[0]['sku'],'03026A')
        self.assertEqual(products[0]['source_page'],2)
        self.assertEqual(self.client.post(base+'/start',json={'sha256':row['sha256'],'start_page':2,'end_page':2,'sku':'03026A'}).status_code,409)

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
