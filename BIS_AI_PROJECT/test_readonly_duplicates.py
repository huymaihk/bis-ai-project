import unittest
from unittest.mock import Mock, patch
from readonly_duplicates import scan_website, check_sources

class DuplicateTests(unittest.TestCase):
    def test_public_pagination_get_only(self):
        session=Mock(spec=['get']); first=[{'id':i} for i in range(1,51)]
        session.get.side_effect=[Mock(json=lambda:{'products':first},raise_for_status=lambda:None),Mock(json=lambda:{'products':[{'id':51}]},raise_for_status=lambda:None)]
        self.assertEqual(len(scan_website(session,pause=lambda _:None)),51)
        self.assertEqual(session.get.call_count,2)
        self.assertNotIn('headers',session.get.call_args.kwargs)
    def test_repeated_page_not_complete(self):
        rows=[{'id':i} for i in range(1,51)]; session=Mock(spec=['get'])
        session.get.return_value=Mock(json=lambda:{'products':rows},raise_for_status=lambda:None)
        with self.assertRaises(ValueError): scan_website(session,pause=lambda _:None)
    def test_partial_failure_never_clean(self):
        with patch('safe_publish.scan_store',side_effect=Exception('SECRET')),patch('readonly_duplicates.scan_website',return_value=[]):
            result=check_sources({'sku':'03026A'}, {})
        self.assertEqual(result['state'],'UNVERIFIED');self.assertTrue(result['blocked']);self.assertNotIn('SECRET',str(result))
    def test_web_match_even_if_haravan_fails(self):
        product={'sku':'03026A'};original=dict(product)
        with patch('safe_publish.scan_store',side_effect=Exception()),patch('readonly_duplicates.scan_website',return_value=[{'id':1,'variants':[{'sku':'03026A'}]}]):
            result=check_sources(product,{})
        self.assertEqual(result['state'],'MATCH');self.assertFalse(result['complete']);self.assertTrue(result['blocked']);self.assertEqual(product,original)
    def test_related_not_exact_and_both_clean(self):
        with patch('safe_publish.scan_store',return_value=[]),patch('readonly_duplicates.scan_website',return_value=[{'id':1,'title':'03026 manual'}]):
            result=check_sources({'sku':'03026A'}, {})
        self.assertEqual(result['state'],'REVIEW');self.assertTrue(result['blocked'])
        with patch('safe_publish.scan_store',return_value=[]),patch('readonly_duplicates.scan_website',return_value=[]):
            result=check_sources({'sku':'03026A'}, {})
        self.assertEqual(result['state'],'NO_MATCH');self.assertTrue(result['complete']);self.assertFalse(result['blocked'])
