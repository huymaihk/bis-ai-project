import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from gemini_fallback import generate_with_fallback
from config import PRIORITY_MODELS

class APIError(Exception):
    def __init__(self,code): self.code=code

class FallbackTests(unittest.TestCase):
    def test_transient_errors_switch_to_backup(self):
        for code in (503,504):
            call=Mock(side_effect=[APIError(code),SimpleNamespace(text='[]')])
            attempts=[]
            response,model=generate_with_fallback(SimpleNamespace(models=SimpleNamespace(generate_content=call)),['gemini-3.6-flash','gemini-3.5-flash-lite'],contents=['same'],config=None,attempts=attempts)
            self.assertEqual(model,'gemini-3.5-flash-lite')
            self.assertEqual([c.kwargs['model'] for c in call.call_args_list],['gemini-3.6-flash','gemini-3.5-flash-lite'])
            self.assertEqual(attempts[0]['code'],code)

    def test_auth_quota_and_other_errors_do_not_fallback(self):
        for code in (401,403,429,400,404):
            call=Mock(side_effect=APIError(code))
            with self.assertRaises(APIError):
                generate_with_fallback(SimpleNamespace(models=SimpleNamespace(generate_content=call)),['main','backup'],contents=[],config=None,attempts=[])
            self.assertEqual(call.call_count,1)

    def test_exhaustion_is_bounded(self):
        call=Mock(side_effect=APIError(503))
        with self.assertRaises(APIError):
            generate_with_fallback(SimpleNamespace(models=SimpleNamespace(generate_content=call)),['main','backup','backup'],contents=[],config=None,attempts=[])
        self.assertEqual(call.call_count,2)

    def test_extractor_uses_backup_and_records_provenance(self):
        from agent_technical import AgentTechnical
        agent=AgentTechnical.__new__(AgentTechnical)
        agent._build_prompt=lambda *a,**kw:'test'
        agent.client=SimpleNamespace(models=SimpleNamespace(generate_content=Mock(side_effect=[APIError(503),SimpleNamespace(text='[]')])))
        self.assertEqual(agent.extract_page(b'test',1,1,allow_local_fallback=False),[])
        self.assertEqual(agent.last_model_used, PRIORITY_MODELS[1])
        self.assertEqual(agent.last_extraction_status,'EMPTY_VALID')

    def test_exhausted_extractor_identifies_all_models(self):
        from agent_technical import AgentTechnical
        agent=AgentTechnical.__new__(AgentTechnical)
        agent._build_prompt=lambda *a,**kw:'test'
        agent.client=SimpleNamespace(models=SimpleNamespace(generate_content=Mock(side_effect=APIError(503))))
        self.assertEqual(agent.extract_page(b'test',15,36,allow_local_fallback=False),[])
        self.assertEqual(agent.client.models.generate_content.call_count, len(PRIORITY_MODELS))
        for m in PRIORITY_MODELS:
            self.assertIn(f'{m}: 503', agent.last_extraction_error)

    def test_local_fallback_on_ai_exhaustion(self):
        from agent_technical import AgentTechnical
        agent=AgentTechnical.__new__(AgentTechnical)
        agent.storage_dir=__import__('pathlib').Path('.')
        agent._build_prompt=lambda *a,**kw:'test'
        agent.client=SimpleNamespace(models=SimpleNamespace(generate_content=Mock(side_effect=APIError(503))))
        agent.learning_engine=SimpleNamespace(apply_auto_corrections=lambda r:r)
        agent.audit_6_steps=lambda r:{'status':'PASSED','passed':True}
        sample_text = '''15
AATCC GRAY SCALE FOR COLOR CHANGE
The AATCC Gray Scale for Color Change is used to visually evaluate change in color.
Item #28359C
AATCC GRAY SCALE FOR STAINING
Item #28360C
'''
        rows = agent.extract_page(b'test', 15, 36, page_text=sample_text, allow_local_fallback=True)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['sku'], '28359C')
        self.assertEqual(rows[1]['sku'], '28360C')
        self.assertEqual(rows[0]['analysis_model'], 'PyMuPDF-LocalFallback')
        self.assertEqual(rows[0]['audit_result']['status'], 'NEEDS_REVIEW')
        self.assertFalse(rows[0]['audit_result']['passed'])
        self.assertIsNone(rows[0]['unit'])
        self.assertIsNone(rows[0]['brand_evidence'])
        self.assertIn(rows[0]['evidence_quote'],sample_text)
        self.assertEqual(agent._extract_fallback_from_text(15,page_text=''),[])
        self.assertEqual(agent._extract_fallback_from_text(15,page_text='Order information Part description'),[])

    def test_hot_deploy_reloads_dependencies_before_api(self):
        from unittest.mock import patch
        import workspace_loader as loader
        modules={name:SimpleNamespace(name=name) for name in
                 ('bis_api','streamlit_react_host','config','gemini_fallback','agent_technical','technical_names','production_workspace')}
        modules['production_workspace'].render_workspace=lambda active_step=None:None
        modules['streamlit_react_host'].render_react_workspace=Mock()
        with patch.object(loader.importlib,'import_module',side_effect=lambda name:modules[name]), patch.object(loader.importlib,'reload',side_effect=lambda module:module) as reload:
            loader.render_current_workspace('root',())
        self.assertEqual([call.args[0].name for call in reload.call_args_list],
                         ['config','gemini_fallback','agent_technical','technical_names','bis_api','streamlit_react_host','production_workspace'])

    def test_stale_technical_instance_and_module_are_repaired(self):
        from unittest.mock import patch
        import technical_runtime as runtime
        class Old:
            def extract_page(self, image, page, total): return []
        class New:
            def __init__(self, root): self.root=root
            def _extract_fallback_from_text(self): pass
            def extract_page(self, image, page, total, page_text=None): return page_text
        stale=Old()
        module=SimpleNamespace(AgentTechnical=Old)
        config=SimpleNamespace()
        def reload(value):
            if value is module: module.AgentTechnical=New
            return value
        with patch.object(runtime.importlib,'import_module',side_effect=lambda name:module if name=='agent_technical' else config), patch.object(runtime.importlib,'reload',side_effect=reload):
            fixed=runtime.ensure_current_technical(stale,'root')
        self.assertEqual(fixed.extract_page(b'',15,36,page_text='source'),'source')
        self.assertIs(runtime.ensure_current_technical(fixed,'root'),fixed)

if __name__=='__main__': unittest.main()
