"""UI regression tests use a temporary workspace; no live credentials or API."""
import json
import tempfile
import unittest
from pathlib import Path
import pymupdf
from product_quality import render_product
from streamlit.testing.v1 import AppTest

class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        with pymupdf.open() as d:
            p=d.new_page()
            p.insert_text((40,40),"03026A AATCC Technical Manual")
            d.save(self.root/"catalogue_sample.pdf")
        record=dict(sku="03026A",product_name="Sổ tay",product_name_en="AATCC Technical Manual",
                    brand="AATCC",description="Mô tả có nguồn",evidence_quote="03026A AATCC Technical Manual",source_page=1)
        (self.root/"extracted_products_cache.json").write_text(json.dumps([record]),encoding="utf-8")
        code=f'''
from pathlib import Path
from types import SimpleNamespace
from persistent_memory import MemoryStore
from production_workspace import render_workspace
root=Path({str(self.root)!r})
class Media:
    manifest={{}}
    final_dir=root
    preview_dir=root
    def get_backgrounds(self): return []
    def get_product_image_for_sku(self,sku): return None
media=Media()
render_workspace(root,None,media,None,None,MemoryStore(root))
'''
        self.code=code
        self.app=AppTest.from_string(code).run(timeout=30)
    def tearDown(self):
        self.tmp.cleanup()
    def test_selected_tools_show_only_the_requested_step(self):
        for step, expected in [(0,'Xem trang'),(1,'Lưu và kiểm tra'),(2,'Tìm ảnh ứng viên'),(3,'Duyệt phiên bản sản phẩm'),(4,'Ghi')]:
            code=self.code.replace('None,None,MemoryStore(root))',f'None,None,MemoryStore(root),active_step={step})')
            app=AppTest.from_string(code).run(timeout=30)
            self.assertFalse(app.exception, str(app.exception))
            self.assertEqual(len(app.tabs),0)
            labels=[b.label for b in app.button]
            if step<4:
                self.assertIn(expected,labels)
            if step!=3:
                self.assertNotIn('Tạo bản nháp trên Haravan',labels)

    def test_react_bridge_opens_selected_tool_and_returns_with_sku(self):
        code=self.code[:self.code.index('render_workspace(root,None,media')]
        code+='''
import streamlit as st
from unittest.mock import patch
from streamlit_react_host import render_react_workspace
import json
st.session_state.authenticated=True
req={'id':'open-image','url':'/api/workspace/open','method':'POST','body':json.dumps({'step':2,'sku':'03026A'})}
(root/'frontend'/'streamlit_dist').mkdir(parents=True,exist_ok=True)
(root/'frontend'/'streamlit_dist'/'index.html').write_text('test')
with patch('streamlit_react_host.components.declare_component', return_value=lambda **kwargs:req):
    render_react_workspace(root,(None,media,None,None,MemoryStore(root)))
'''
        app=AppTest.from_string(code).run(timeout=30)
        self.assertFalse(app.exception,str(app.exception))
        self.assertEqual(app.session_state['_bis_native_step'],2)
        self.assertEqual(app.selectbox(key='q_sku').value,'03026A')
        self.assertIn('Tìm ảnh ứng viên',[b.label for b in app.button])
        app.button(key='bis_back_react').click().run(timeout=30)
        self.assertFalse(app.exception,str(app.exception))
        bridge=app.session_state['_bis_react_bridge']
        self.assertEqual(bridge.client.get('/api/state').json()['preferred_sku'],'03026A')
        bridge.client.close()

    def test_five_steps(self):
        self.assertFalse(self.app.exception)
        self.assertEqual(len(self.app.tabs),5)
        self.assertTrue(any("Nội dung" in t.label for t in self.app.tabs))
    def test_edit_invalidates_approval_and_persists(self):
        self.assertFalse(self.app.exception)
        next(x for x in self.app.text_input if x.label=="Tên tiếng Việt").input("Sổ tay đã sửa")
        next(x for x in self.app.button if x.label=="Lưu và kiểm tra").click()
        self.app.run(timeout=30)
        self.assertFalse(self.app.exception)
        drafts=self.root/"Google_Drive_Storage"/"8_AI_Memory"/"product_drafts"
        result=json.loads((drafts/"03026A.json").read_text(encoding="utf-8"))
        self.assertEqual(result["product_name"],"Sổ tay đã sửa")
        self.assertEqual(result["status"],"EXTRACTED_UNVERIFIED")
        self.assertEqual(next(x for x in self.app.text_input if x.label=="Tên tiếng Việt").value,"Sổ tay đã sửa")
    def test_publish_disabled_without_approval(self):
        self.assertTrue(next(x for x in self.app.button if x.label=="Tạo bản nháp trên Haravan").disabled)

    def test_theme_change_keeps_product_and_review_gate(self):
        self.app.toggle(key="bis_light_theme").set_value(True).run(timeout=30)
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.selectbox(key="q_sku").value,"03026A")
        self.assertEqual(len(self.app.tabs),5)
        self.assertTrue(next(x for x in self.app.button if x.label=="Tạo bản nháp trên Haravan").disabled)

if __name__=="__main__":
    unittest.main()
