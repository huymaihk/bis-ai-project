"""Explicit Gemini image editing; no silent pixel-composition fallback."""
import hashlib
import io
import os
from PIL import Image

def image_edit_prompt(feedback,history):
    return ('Edit the original product photo into a truthful BIS studio product image. '
            'Preserve product identity, geometry, materials, exact text and logos. Never invent unreadable text. '
            'For books preserve the entire rectangular cover including white areas, all words, author and edition. '
            'Improve exposure, neutral color and clarity. Use the supplied background and soft contact shadow. '
            'Product should occupy about 75% of frame. References show quality/style only, never replace the product. '
            'Input order: original, background, previous draft, optional approved reference. '
            'Previous user feedback for this SKU: '+str(history)+'\nCurrent user request: '+feedback)

def failure_info(exc):
    """Return allowlisted diagnostics; never expose provider bodies or credentials."""
    code=getattr(exc,'code',None)
    try: code=int(code)
    except (TypeError,ValueError): code=None
    cases={401:('AUTH','Khóa Gemini API không được chấp nhận.'),
           403:('PERMISSION','Project chưa có quyền sử dụng model ảnh.'),
           404:('MODEL_NOT_FOUND','Model ảnh không tồn tại hoặc không có trong project.'),
           429:('QUOTA','Gemini giới hạn quota/tốc độ (429). Kiểm tra quota và billing trong AI Studio; không bấm tạo liên tục.'),
           503:('UNAVAILABLE','Model ảnh đang quá tải (503). Thử lại sau.'),
           504:('TIMEOUT','Model ảnh xử lý quá thời gian (504).')}
    kind,message=cases.get(code,('PROVIDER_ERROR','Chưa nhận được ảnh từ Gemini. Kiểm tra cấu hình model và kết nối.'))
    if 'timeout' in type(exc).__name__.lower(): kind,message='TIMEOUT','Kết nối AI quá thời gian; chưa có ảnh mới.'
    if isinstance(exc,ValueError): kind,message='NO_IMAGE','AI chưa trả ảnh hợp lệ hoặc thiếu cấu hình API.'
    return dict(code=kind,http_code=code,message=message)

def edit_image(source, background, previous, references, feedback, history, target):
    from google import genai
    from google.genai import types
    from config import GEMINI_API_KEY
    from config import _secrets
    model=os.environ.get('BIS_IMAGE_MODEL') or _secrets.get('BIS_IMAGE_MODEL') or 'gemini-3.1-flash-image'
    if not GEMINI_API_KEY:
        raise ValueError('Chưa cấu hình Gemini API cho chỉnh ảnh')
    prompt=image_edit_prompt(feedback,history)
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
                generated_size=list(im.size)
            with Image.open(source) as original: source_size=list(original.size)
            return dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),engine=model,
                        status='PENDING_REVIEW',low_resolution=min(source_size)<500,source_size=source_size,
                        generated_size=generated_size,note='AI edited; verify text, identity and quality')
    raise ValueError('AI không trả ảnh; góp ý đã lưu, chưa tạo phiên bản mới')
