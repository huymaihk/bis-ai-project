"""Authenticated, single-worker bridge for BIS React and existing local stores."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import threading
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from persistent_memory import MemoryStore, atomic_json
from product_quality import fingerprint, render_product
from quality_jobs import JobRunner


def create_app(workspace=None, pin=None):
    root = Path(workspace or Path(__file__).parent).resolve()
    memory = MemoryStore(root)
    drafts = memory.root / 'product_drafts'
    drafts.mkdir(exist_ok=True)
    lock = threading.RLock()
    sessions, attempts = {}, {}
    if pin is None:
        from config import BIS_ACCESS_PIN
        pin = str(BIS_ACCESS_PIN or '')
    app = FastAPI(title='BIS local bridge', docs_url=None, redoc_url=None)

    @app.middleware('http')
    async def authenticate(request: Request, call_next):
        if request.url.path.startswith('/api/'):
            if request.method not in ('GET', 'HEAD') and request.headers.get('X-BIS-Request') != '1':
                return JSONResponse({'detail':'Thiếu mã xác nhận yêu cầu'}, status_code=403)
            origin = request.headers.get('origin')
            if origin and origin.rstrip('/') != str(request.base_url).rstrip('/'):
                return JSONResponse({'detail':'Nguồn yêu cầu không hợp lệ'}, status_code=403)
            if request.url.path != '/api/login':
                token = request.cookies.get('bis_session', '')
                if sessions.get(token, 0) < time.time():
                    return JSONResponse({'detail':'Cần đăng nhập'}, status_code=401)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    class Login(BaseModel):
        pin: str = Field(max_length=128)

    @app.post('/api/login')
    def login(body: Login, request: Request):
        host = request.client.host if request.client else 'unknown'
        recent = [t for t in attempts.get(host, []) if time.time()-t < 300]
        attempts[host] = recent
        if len(recent) >= 10:
            raise HTTPException(429, 'Thử lại sau 5 phút')
        if not pin or not hmac.compare_digest(body.pin, pin):
            recent.append(time.time())
            raise HTTPException(401, 'PIN không đúng')
        attempts.pop(host, None)
        token = secrets.token_urlsafe(32)
        sessions[token] = time.time()+28800
        response = JSONResponse({'ok':True})
        response.set_cookie('bis_session', token, httponly=True, samesite='strict',
                            secure=request.url.scheme == 'https', max_age=28800)
        return response

    @app.post('/api/logout')
    def logout(request: Request):
        sessions.pop(request.cookies.get('bis_session',''), None)
        response = JSONResponse({'ok':True})
        response.delete_cookie('bis_session')
        return response

    def products():
        result = {}
        cache = root/'extracted_products_cache.json'
        if cache.exists():
            for row in json.loads(cache.read_text(encoding='utf-8')):
                if row.get('sku'):
                    result[str(row['sku'])] = row
        for path in drafts.glob('*.json'):
            row = json.loads(path.read_text(encoding='utf-8'))
            result[str(row['sku'])] = row
        return result

    @app.get('/api/state')
    def state():
        rows = products()
        return {'products':[dict(p, _revision=fingerprint(p)) for p in rows.values()],
                'jobs':JobRunner(root).list_jobs(),
                'sync':{'state':'unverified','detail':'Đã lưu cục bộ; chưa xác minh đồng bộ Google trong phiên này.'},
                'capabilities':{'publish':False,'extraction':False,'agent_meetings':False}}

    class ProductEdit(BaseModel):
        revision: str
        fields: dict

    @app.put('/api/products/{sku}')
    def edit_product(sku: str, body: ProductEdit):
        from media_quality import safe_name
        with lock:
            current = products().get(sku)
            if current is None:
                raise HTTPException(404, 'Không tìm thấy SKU')
            if fingerprint(current) != body.revision:
                raise HTTPException(409, 'Dữ liệu đã thay đổi; tải lại trước khi sửa')
            allowed = {'product_name','product_name_en','brand','description','evidence_quote',
                       'source_page','source_file','specifications','highlights','meta_description'}
            if set(body.fields)-allowed:
                raise HTTPException(422, 'Trường không được phép sửa')
            if len(json.dumps(body.fields)) > 50000:
                raise HTTPException(413, 'Nội dung quá dài')
            for key, value in body.fields.items():
                if key == 'specifications':
                    valid = isinstance(value, dict)
                elif key == 'highlights':
                    valid = isinstance(value, list) and all(isinstance(v,str) for v in value)
                elif key == 'source_page':
                    valid = isinstance(value,int) and not isinstance(value,bool) and value > 0
                else:
                    valid = isinstance(value,str)
                if not valid:
                    raise HTTPException(422, 'Kiểu dữ liệu không hợp lệ: '+key)
            updated = dict(current, **body.fields)
            updated['status'] = 'EXTRACTED_UNVERIFIED'
            updated.pop('_review_hash', None)
            updated['custom_html'] = render_product(updated)
            memory.revise('product:'+sku, json.dumps(updated,ensure_ascii=False),
                          kind='correction', source='React editor; cần kiểm tra chứng cứ')
            atomic_json(drafts/(safe_name(sku)+'.json'), updated)
            return dict(updated, _revision=fingerprint(updated))

    def assets():
        found = {}
        folders = ['1_Catalogues','2_Manuals_Standards','4_Product_Images','6_Final_Composites']
        paths = [root/'catalogue_sample.pdf']
        for folder in folders:
            paths.extend((root/'Google_Drive_Storage'/folder).rglob('*'))
        for path in paths:
            resolved = path.resolve()
            if not resolved.is_relative_to(root) or not path.is_file() or path.suffix.lower() not in {'.pdf','.png','.jpg','.jpeg','.webp'}:
                continue
            rel = path.relative_to(root).as_posix()
            ident = hashlib.sha256(rel.encode()).hexdigest()[:24]
            found[ident] = (path, rel)
        return found

    @app.get('/api/assets')
    def list_assets():
        return [dict(id=i,name=p.name,folder=rel.rsplit('/',1)[0] if '/' in rel else 'Catalogue',
                     type='pdf' if p.suffix.lower()=='.pdf' else 'image',url='/api/assets/'+i)
                for i,(p,rel) in assets().items()]

    @app.get('/api/assets/{ident}')
    def read_asset(ident: str):
        row = assets().get(ident)
        if not row:
            raise HTTPException(404,'Không tìm thấy tài liệu/ảnh')
        return FileResponse(row[0])

    @app.get('/api/assets/{ident}/page/{page}')
    def pdf_page(ident: str, page: int):
        import pymupdf
        row = assets().get(ident)
        if not row or row[0].suffix.lower() != '.pdf':
            raise HTTPException(404,'Không tìm thấy PDF')
        with pymupdf.open(row[0]) as doc:
            if page < 1 or page > len(doc):
                raise HTTPException(422,'Số trang không hợp lệ')
            return Response(doc[page-1].get_pixmap(matrix=pymupdf.Matrix(1.3,1.3)).tobytes('png'), media_type='image/png')

    @app.get('/api/memory')
    def get_memory():
        return memory.current()

    @app.get('/api/memory/history')
    def memory_history(key: str):
        return [e for e in memory.events() if e['key']==key]

    class MemoryEdit(BaseModel):
        key: str = Field(min_length=1,max_length=200)
        content: str = Field(max_length=18000)
        expected: list[str]
        deleted: bool = False

    @app.post('/api/memory')
    def edit_memory(body: MemoryEdit):
        if not body.key.startswith('user:'):
            raise HTTPException(422,'Ghi chú giao diện cần có tiền tố user:')
        try:
            return memory.revise(body.key, body.content, expected=body.expected,
                                 deleted=body.deleted,kind='correction',source='React memory editor')
        except ValueError as exc:
            raise HTTPException(409,str(exc))

    @app.post('/api/sync')
    def sync():
        from persistent_memory import sync_configured
        return sync_configured(memory)

    @app.get('/api/knowledge/search')
    def knowledge_search(q: str = ''):
        return {'text':memory.context(q,max_chars=12000)}

    @app.get('/api/{path:path}')
    def missing_api(path: str):
        raise HTTPException(404,'API chưa có')

    dist = root/'frontend'/'dist'
    if dist.exists():
        app.mount('/',StaticFiles(directory=dist,html=True),name='frontend')
    return app


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(create_app(),host='127.0.0.1',port=8765)
