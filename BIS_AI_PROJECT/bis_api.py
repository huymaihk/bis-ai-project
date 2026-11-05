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

API_PROTOCOL = 'workflow-v2-10'


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
        elif (root/'catalog_master_data.py').exists():
            from catalog_master_data import CATALOG_MASTER
            for sku, item in CATALOG_MASTER.items():
                result[sku] = dict(sku=sku,product_name=item.get('vi',''),
                    product_name_en=item.get('en',''),description=item.get('desc',''),
                    source_file='catalogue_sample.pdf',source_page=int(item.get('page') or 1),
                    status='EXTRACTED_UNVERIFIED',evidence_quote='',
                    provenance='Danh mục có trong mã nguồn; cần đối chiếu PDF, chưa nghiệm thu')
        for path in drafts.glob('*.json'):
            row = json.loads(path.read_text(encoding='utf-8'))
            result[str(row['sku'])] = row
        return result

    @app.get('/api/state')
    def state():
        rows = products()
        return {'products':[dict(p, _revision=fingerprint(p)) for p in rows.values()],
                'jobs':JobRunner(root).list_jobs(),
                'preferred_sku':getattr(app.state, 'preferred_sku', ''),
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

    @app.get('/api/assets/{ident}/thumbnail')
    def thumbnail(ident: str):
        import io
        from PIL import Image
        row=assets().get(ident)
        if not row or row[0].suffix.lower()=='.pdf':
            raise HTTPException(404,'Không tìm thấy ảnh')
        with Image.open(row[0]) as image:
            image.thumbnail((400,400))
            output=io.BytesIO()
            image.convert('RGB').save(output,format='JPEG',quality=80)
            return Response(output.getvalue(),media_type='image/jpeg')

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

    catalogue_lock = threading.RLock()
    catalogue_folder = root/'Google_Drive_Storage'/'1_Catalogues'
    catalogue_ledger = memory.root/'catalogue_analysis.json'

    def catalogue_files():
        catalogue_folder.mkdir(parents=True, exist_ok=True)
        return {hashlib.sha256(str(p.relative_to(root)).encode()).hexdigest()[:24]:p
                for p in catalogue_folder.rglob('*') if p.is_file() and p.suffix.lower()=='.pdf'
                and p.resolve().is_relative_to(catalogue_folder.resolve())}

    def catalogue_records():
        try:
            return json.loads(catalogue_ledger.read_text(encoding='utf-8'))
        except FileNotFoundError:
            return {}

    @app.get('/api/catalogues')
    @app.post('/api/catalogues/scan')
    def scan_catalogues():
        records = catalogue_records()
        result=[]
        for ident,path in catalogue_files().items():
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            record=records.get(str(path.relative_to(root)),{})
            state=record.get('state','NEW') if record.get('sha256')==digest else 'NEW'
            result.append(dict(id=ident,name=path.name,path=str(path.relative_to(catalogue_folder)),
                               sha256=digest,size=path.stat().st_size,state=state,
                               completed_pages=record.get('completed_pages',0) if record.get('sha256')==digest else 0))
        return {'files':sorted(result,key=lambda x:x['name'].lower()),
                'location':'Google_Drive_Storage/1_Catalogues',
                'desktop_access':os.name=='nt',
                'detail':'Quét thư mục trên máy đang chạy BIS. Website Cloud chưa tự đồng bộ ổ G của máy cá nhân.'}

    class CatalogueRun(BaseModel):
        sha256: str
        confirm: bool = False
        start_page: int = Field(default=1,ge=1)
        end_page: int | None = Field(default=None,ge=1)
        sku: str = Field(default='',max_length=100)

    @app.post('/api/catalogues/{ident}/start')
    def start_catalogue(ident: str, body: CatalogueRun):
        import pymupdf
        with catalogue_lock:
            path=catalogue_files().get(ident)
            if path is None:
                raise HTTPException(404,'Không tìm thấy tài liệu; quét lại thư mục')
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            if digest!=body.sha256:
                raise HTTPException(409,'Tài liệu đã thay đổi; hãy quét lại')
            records=catalogue_records()
            old=records.get(str(path.relative_to(root)),{})
            if old.get('state')=='COMPLETED' and old.get('sha256')==digest and not body.confirm:
                raise HTTPException(409,'Bạn có muốn phân tích lại tài liệu này không?')
            with pymupdf.open(path) as document:
                if document.needs_pass:
                    raise HTTPException(422,'PDF cần mật khẩu')
                pages=len(document)
            end=body.end_page or pages
            if not body.start_page<=end<=pages:
                raise HTTPException(422,'Khoảng trang vượt tài liệu hoặc không hợp lệ')
            if body.sku and not body.confirm:
                raise HTTPException(409,'Cần xác nhận phân tích lại sản phẩm')
            run=secrets.token_hex(16)
            record=dict(sha256=digest,state='RUNNING',run=run,pages=pages,start_page=body.start_page,end_page=end,sku=body.sku,completed_pages=body.start_page-1,products=0)
            records[str(path.relative_to(root))]=record
            atomic_json(catalogue_ledger,records)
            return record

    class CataloguePage(BaseModel):
        run: str
        page: int = Field(ge=1)

    @app.post('/api/catalogues/{ident}/page')
    def analyse_catalogue_page(ident: str, body: CataloguePage):
        import pymupdf
        from media_quality import safe_name
        with catalogue_lock:
            path=catalogue_files().get(ident)
            if path is None:
                raise HTTPException(404,'Không tìm thấy tài liệu')
            key=str(path.relative_to(root))
            records=catalogue_records()
            record=records.get(key,{})
            if record.get('run')!=body.run or record.get('state')!='RUNNING':
                raise HTTPException(409,'Lần phân tích không còn hiệu lực')
            if body.page!=record.get('completed_pages',0)+1 or body.page>record.get('end_page',record['pages']):
                raise HTTPException(409,'Thứ tự trang không hợp lệ')
            try:
                if hashlib.sha256(path.read_bytes()).hexdigest()!=record['sha256']:
                    raise ValueError('Tài liệu đã thay đổi')
                if not hasattr(app.state,'catalogue_agent'):
                    from agent_technical import AgentTechnical
                    app.state.catalogue_agent=AgentTechnical(root)
                with pymupdf.open(path) as document:
                    page_obj=document[body.page-1]
                    image=page_obj.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).tobytes('jpeg')
                    page_text=page_obj.get_text()
                rows=JobRunner(root).run('catalogue_page',{'file':key,'page':body.page,'sha256':record['sha256']},
                    lambda:app.state.catalogue_agent.extract_page(image,body.page,record['pages'],'AATCC',page_text))
                if not isinstance(rows,list) or (not rows and getattr(app.state.catalogue_agent,'last_extraction_status','')!='EMPTY_VALID'):
                    reason=getattr(app.state.catalogue_agent,'last_extraction_error','') or 'Chưa xác định được trang không có sản phẩm hay lỗi AI'
                    raise ValueError(reason)
                record['empty_pages']=record.get('empty_pages',[])
                if not rows:
                    record['empty_pages'].append(body.page)
                if record.get('sku'):
                    rows=[row for row in rows if str(row.get('sku','')).upper()==record['sku'].upper()]
                    if not rows:
                        raise ValueError('Không tìm thấy SKU được yêu cầu trên trang nguồn')
                if any(row.get('analysis_model') == 'PyMuPDF-LocalFallback' for row in rows):
                    record['needs_review'] = True
                for row in rows:
                    row.update(source_file=key,source_page=body.page,status='EXTRACTED_UNVERIFIED')
                    row['custom_html']=render_product(row)
                    result_path=memory.root/'catalogue_results'/ident/(safe_name(row['sku'])+'.json')
                    atomic_json(result_path,dict(row,_source_sha256=record['sha256']))
                    target=drafts/(safe_name(row['sku'])+'.json')
                    if not target.exists():
                        atomic_json(target,row)
                record['completed_pages']=body.page
                record['products']+=len(rows)
                if body.page==record.get('end_page',record['pages']):
                    record['state']=('COMPLETED' if record.get('start_page',1)==1 and body.page==record['pages'] and not record.get('sku') else 'PARTIAL') if record['products'] else 'NEEDS_REVIEW'
                if body.page==record.get('end_page',record['pages']) and record.get('needs_review'):
                    record['state']='NEEDS_REVIEW'
                atomic_json(catalogue_ledger,records)
                return record
            except Exception as exc:
                record['state']='FAILED'
                reason=str(exc) if isinstance(exc,ValueError) else 'Lỗi xử lý '+type(exc).__name__
                record['failed_page']=body.page
                record['error']=reason
                atomic_json(catalogue_ledger,records)
                raise HTTPException(422,f'Trang {body.page}/{record["pages"]}: {reason}. Các bản làm việc đã lưu được giữ lại.')

    def current_catalogue_rows(ident):
        path=catalogue_files().get(ident)
        if path is None:
            raise HTTPException(404,'Không tìm thấy tài liệu')
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        rows=[]
        for result_path in (memory.root/'catalogue_results'/ident).glob('*.json'):
            row=json.loads(result_path.read_text(encoding='utf-8'))
            if row.get('_source_sha256')==digest:
                rows.append(row)
        return path, digest, rows

    @app.get('/api/catalogues/{ident}/results')
    def catalogue_results(ident: str):
        from technical_names import name_review
        _, _, rows=current_catalogue_rows(ident)
        for row in rows:
            row['name_review']=name_review(memory,ident,row)
        return {'products':sorted(rows,key=lambda x:str(x.get('sku','')))}

    @app.get('/api/catalogues/{ident}/source/{page}')
    def catalogue_source(ident: str, page: int, sha256: str):
        import pymupdf, base64
        path,digest,_=current_catalogue_rows(ident)
        if digest!=sha256:
            raise HTTPException(409,'Tài liệu đã thay đổi; quét lại')
        with pymupdf.open(path) as doc:
            if page<1 or page>len(doc):
                raise HTTPException(422,'Trang không hợp lệ')
            source=doc[page-1]
            return {'text':source.get_text(),'image':'data:image/jpeg;base64,'+base64.b64encode(source.get_pixmap(matrix=pymupdf.Matrix(1,1)).tobytes('jpeg')).decode()}

    class NameApproval(BaseModel):
        product_name_en: str
        sku: str
        sha256: str
        name: str = Field(min_length=1,max_length=300)
        revision: list[str] = Field(default_factory=list)

    @app.post('/api/catalogues/{ident}/name')
    def approve_catalogue_name(ident: str, body: NameApproval):
        from technical_names import name_key, name_review
        with catalogue_lock:
            _,digest,rows=current_catalogue_rows(ident)
            if digest!=body.sha256:
                raise HTTPException(409,'Tài liệu đã thay đổi; quét lại')
            row=next((r for r in rows if r.get('sku')==body.sku),None)
            if row is None:
                raise HTTPException(404,'Không tìm thấy kết quả hiện hành')
            if body.product_name_en != row.get('product_name_en'):
                raise HTTPException(409,'Tên nguồn đã thay đổi; tải lại kết quả')
            if not body.name.strip() or not row.get('product_name_en'):
                raise HTTPException(422,'Cần tên tiếng Việt và tên nguồn tiếng Anh')
            try:
                memory.revise(name_key(ident,row),json.dumps({'name':body.name.strip(),'sha256':digest},ensure_ascii=False),kind='correction',source='Technical name review',expected=body.revision)
            except ValueError:
                raise HTTPException(409,'Hiệu chỉnh đã thay đổi; tải lại kết quả')
            return name_review(memory,ident,row)

    class WorkspaceOpen(BaseModel):
        step: int = Field(ge=0, le=4)
        sku: str = Field(default='', max_length=100)

    @app.post('/api/workspace/open')
    def open_workspace(body: WorkspaceOpen):
        if body.sku and body.sku not in products():
            raise HTTPException(404, 'Không tìm thấy SKU')
        app.state.preferred_sku = body.sku
        return {'step':body.step, 'sku':body.sku}

    class WorkflowCheck(BaseModel):
        revision: str

    @app.post('/api/workflow/{sku}/check')
    def check_workflow(sku: str, body: WorkflowCheck):
        from workflow_review import review_product
        with lock:
            product = products().get(sku)
            if product is None:
                raise HTTPException(404, 'Không tìm thấy SKU')
            if fingerprint(product) != body.revision:
                raise HTTPException(409, 'Dữ liệu đã đổi; tải lại trước khi kiểm tra')
            result = JobRunner(root).run('workflow_check', {'sku':sku,'revision':body.revision},
                                         lambda: review_product(root, product))
            # Diagnostic reports are not approved knowledge or publishing approvals.
            atomic_json(memory.root/'workflow_checks'/(hashlib.sha256(sku.encode()).hexdigest()+'.json'), result)
            return result

    @app.get('/api/workflow/{sku}/check')
    def last_workflow_check(sku: str):
        product = products().get(sku)
        if product is None:
            raise HTTPException(404, 'Không tìm thấy SKU')
        path = memory.root/'workflow_checks'/(hashlib.sha256(sku.encode()).hexdigest()+'.json')
        if not path.exists():
            return {'checks':[], 'state':'NOT_RUN'}
        report = json.loads(path.read_text(encoding='utf-8'))
        report['stale'] = report.get('revision') != fingerprint(product)
        report['detail'] = 'Báo cáo lần kiểm tra trước; chạy lại để xác minh ảnh và nguồn hiện tại.'
        return report

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

