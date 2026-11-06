import tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import pymupdf
from pdf_analysis_cache import page_input,cached_extract
class CacheTests(unittest.TestCase):
 def test_exact_reuse_force_and_version(self):
  with tempfile.TemporaryDirectory() as folder:
   agent=SimpleNamespace(extract_page=Mock(return_value=[{'sku':'03026A'}]),last_extraction_status='PARSED')
   args=(folder,'hash',7,'v1',agent,None,36,'Item #03026A')
   self.assertFalse(cached_extract(*args)[1]);self.assertTrue(cached_extract(*args)[1]);self.assertEqual(agent.extract_page.call_count,1)
   self.assertFalse(cached_extract(*args,force=True)[1]);self.assertEqual(agent.extract_page.call_count,2)
   self.assertFalse(cached_extract(folder,'newhash',7,'v1',agent,None,36,'Item #03026A')[1])
   self.assertFalse(cached_extract(folder,'hash',7,'v2',agent,None,36,'Item #03026A')[1])
 def test_failure_not_cached_and_image_recovery(self):
  with tempfile.TemporaryDirectory() as folder:
   agent=SimpleNamespace(extract_page=Mock(side_effect=[[],[{'sku':'03026A'}]]),last_extraction_status='PARSED')
   rows,hit=cached_extract(folder,'hash',7,'v1',agent,None,36,'Item #03026A',image_fallback=lambda:b'image')
   self.assertEqual(rows[0]['sku'],'03026A');self.assertTrue(agent.last_input_fallback)
   agent=SimpleNamespace(extract_page=Mock(return_value=[]),last_extraction_status='FAILED',last_extraction_error='429')
   for _ in range(2):self.assertFalse(cached_extract(folder,'fail',7,'v1',agent,None,36,'',image_fallback=Mock())[1])
   self.assertEqual(agent.extract_page.call_count,2)
 def test_text_and_scan_gate(self):
  with pymupdf.open() as d:
   p=d.new_page();p.insert_text((40,40),'Technical catalogue product details original text. '*4)
   self.assertIsNone(page_input(p)[1])
   blank=d.new_page();self.assertIsNotNone(page_input(blank)[1])

 def test_changed_context_and_corrupt_cache_recompute(self):
  with tempfile.TemporaryDirectory() as folder:
   agent=SimpleNamespace(extract_page=Mock(return_value=[{'sku':'03026A'}]),last_extraction_status='PARSED',_build_prompt=Mock(return_value='first context'))
   args=(folder,'hash',7,'v1',agent,None,36,'Item #03026A')
   cached_extract(*args)
   file=next(Path(folder).glob('*.json'));file.write_text('broken',encoding='utf-8')
   self.assertFalse(cached_extract(*args)[1]);self.assertEqual(agent.extract_page.call_count,2)
   agent._build_prompt.return_value='new correction'
   self.assertFalse(cached_extract(*args)[1]);self.assertEqual(agent.extract_page.call_count,3)
 def test_multi_column_gate(self):
  with pymupdf.open() as d:
   p=d.new_page()
   for x in (30,330):p.insert_textbox(pymupdf.Rect(x,40,x+180,300),'This is a multi column product catalogue with precise specifications and dimensions. '*4)
   self.assertEqual(page_input(p)[2],'MULTI_COLUMN')
