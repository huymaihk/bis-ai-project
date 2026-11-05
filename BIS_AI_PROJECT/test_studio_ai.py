"""Image-provider boundary tests. No real provider calls or product writes."""
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock,patch
from PIL import Image
from studio_ai import edit_image,failure_info

class StudioProviderTests(unittest.TestCase):
    def test_allowlisted_error_diagnostics(self):
        for code,kind in [(401,'AUTH'),(403,'PERMISSION'),(404,'MODEL_NOT_FOUND'),(429,'QUOTA'),(503,'UNAVAILABLE'),(504,'TIMEOUT')]:
            error=RuntimeError('private provider request and credentials')
            error.code=code
            info=failure_info(error)
            self.assertEqual(info['code'],kind)
            self.assertNotIn('private',str(info))

    def test_timeout_and_no_image(self):
        self.assertEqual(failure_info(TimeoutError())['code'],'TIMEOUT')
        self.assertEqual(failure_info(ValueError())['code'],'NO_IMAGE')

    def test_image_response_and_prompt_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'source.png';reference=Path(tmp)/'reference.png'
            Image.new('RGB',(100,120),'red').save(source)
            Image.new('RGB',(600,600),'green').save(reference)
            buf=io.BytesIO();Image.new('RGB',(1024,1024),'blue').save(buf,'PNG')
            response=SimpleNamespace(parts=[SimpleNamespace(inline_data=SimpleNamespace(mime_type='image/png',data=buf.getvalue()))])
            client=MagicMock();client.__enter__.return_value=client
            client.models.generate_content.return_value=response
            with patch('config.GEMINI_API_KEY','test-key'),patch('google.genai.Client',return_value=client):
                result=edit_image(source,reference,source,[reference],'Preserve exact text',['Less dark'],Path(tmp)/'out.png')
            self.assertTrue(result['low_resolution'])
            self.assertEqual(result['generated_size'],[1024,1024])
            contents=client.models.generate_content.call_args.kwargs['contents']
            self.assertEqual(len(contents),5)
            self.assertIn('Less dark',contents[0]);self.assertIn('Preserve exact text',contents[0])

    def test_missing_key(self):
        with patch('config.GEMINI_API_KEY',''):
            with self.assertRaises(ValueError): edit_image(None,None,None,[],'',[],None)

    def test_text_only_not_success(self):
        client=MagicMock();client.__enter__.return_value=client
        client.models.generate_content.return_value=SimpleNamespace(parts=[])
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/'a.png';Image.new('RGB',(20,20)).save(src)
            out=Path(tmp)/'out.png'
            with patch('config.GEMINI_API_KEY','test-key'),patch('google.genai.Client',return_value=client):
                with self.assertRaises(ValueError): edit_image(src,src,src,[],'',[],out)
            self.assertFalse(out.exists())

if __name__=='__main__': unittest.main()
