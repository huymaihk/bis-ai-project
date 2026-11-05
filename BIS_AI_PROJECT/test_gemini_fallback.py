import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from gemini_fallback import generate_with_fallback
class APIError(Exception):
    def __init__(self,code): self.code=code
class FallbackTests(unittest.TestCase):
    def test_transient_errors_switch_to_backup(self):
        for code in (503,504):
            call=Mock(side_effect=[APIError(code),SimpleNamespace(text='[]')])
            attempts=[]
            response,model=generate_with_fallback(SimpleNamespace(models=SimpleNamespace(generate_content=call)),['gemini-3.8-flash','gemini-3.5-flash'],contents=['same'],config=None,attempts=attempts)
            self.assertEqual(model,'gemini-3.5-flash')
            self.assertEqual([c.kwargs['model'] for c in call.call_args_list],['gemini-3.8-flash','gemini-3.5-flash'])
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
        self.assertEqual(agent.extract_page(b'test',1,1),[])
        self.assertEqual(agent.last_model_used,'gemini-3.5-flash')
        self.assertEqual(agent.last_extraction_status,'EMPTY_VALID')
if __name__=='__main__': unittest.main()
