"""Explicit Gemini image editing; no silent pixel-composition fallback."""
import hashlib
import io
import os
from PIL import Image

def edit_image(source, background, previous, references, feedback, history, target):
    from google import genai
    from google.genai import types
    from config import GEMINI_API_KEY
    model=os.environ.get('BIS_IMAGE_MODEL','gemini-3.1-flash-image')
    if not GEMINI_API_KEY:
        raise ValueError('Chưa cấu hình Gemini API cho chỉnh ảnh')
    prompt=('Edit the original product photo into a truthful BIS studio product image. '
            'Preserve product identity, geometry, materials, exact text and logos. Never invent unreadable text. '
            'Improve exposure, neutral color and clarity. Use the supplied background and soft contact shadow. '
            'Product should fill the frame appropriately. References show quality/style only, never replace the product. '
            'Input order: original, background, previous rejected draft, optional approved references. '
            'Previous user feedback for this SKU: '+str(history)+'\nCurrent user request: '+feedback)
    contents=[prompt]
    for path in [source,background,previous,*references]:
        with Image.open(path) as im: contents.append(im.convert('RGB').copy())
    with genai.Client(api_key=GEMINI_API_KEY,http_options=types.HttpOptions(timeout=90000)) as client:
        response=client.models.generate_content(model=model,contents=contents,
            config=types.GenerateContentConfig(response_modalities=['TEXT','IMAGE']))
    for part in response.parts or []:
        inline=getattr(part,'inline_data',None)
        if inline and inline.mime_type.startswith('image/'):
            with Image.open(io.BytesIO(inline.data)) as im:
                im.load(); target.parent.mkdir(parents=True,exist_ok=True); im.convert('RGB').save(target,'PNG')
            return dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),engine=model,
                        status='PENDING_REVIEW',low_resolution=False,note='AI edited; verify text, identity and quality')
    raise ValueError('AI không trả ảnh; góp ý đã lưu, chưa tạo phiên bản mới')
