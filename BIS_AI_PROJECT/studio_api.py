"""Inline local composition and explicit, version-bound final-image approval."""
import hashlib
import json
import secrets
import shutil
from pathlib import Path
from typing import Literal
from datetime import datetime, timezone
from fastapi import HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from persistent_memory import atomic_json
from media_quality import studio_draft, safe_name

class DraftBody(BaseModel):
    background: str
    remove_white: bool = False
    mode: Literal['ai','quick'] = 'ai'
    reference: str = ''

class ApprovalBody(BaseModel):
    preview_id: str
    sha256: str
    confirm: bool = False

class RetryBody(BaseModel):
    preview_id: str
    sha256: str
    feedback: str = Field(min_length=3, max_length=2000)
    background: str
    reference: str = ''

def register_studio(app, root, memory, products, assets, lock):
    ledger=memory.root/'studio_previews.json'
    attempts=memory.root/'studio_attempts.json'
    def attempt(sku, **values):
        rows=json.loads(attempts.read_text(encoding='utf-8')) if attempts.exists() else {}
        rows[sku]=dict(values,at=datetime.now(timezone.utc).isoformat())
        atomic_json(attempts,rows)
    def selected_references(value):
        if not value: return []
        for ident,(path,rel) in assets().items():
            if value in (ident,asset_url(path)) and '/6_Final_Composites/' in '/'+rel and path.suffix.lower()!='.pdf': return [path]
        raise HTTPException(422,'Ảnh mẫu không còn có trong thư mục thành phẩm; chọn lại')
    def failed(sku,exc):
        from studio_ai import failure_info
        info=failure_info(exc)
        attempt(sku,status='FAILED',**info)
        raise HTTPException(502,info['message']+' Chưa có phiên bản mới; ảnh cũ được giữ nguyên.')
    def read():
        return json.loads(ledger.read_text(encoding='utf-8')) if ledger.exists() else {}
    def source(sku):
        heads=memory.heads('image-source:'+sku)
        if len(heads)!=1 or heads[0]['deleted']: return None
        data=json.loads(heads[0]['content'])
        path=(root/data['path']).resolve()
        if not path.is_relative_to((root/'Google_Drive_Storage'/'4_Product_Images').resolve()) or not path.is_file(): return None
        return path
    def asset_url(path):
        rel=path.relative_to(root).as_posix()
        return '/api/assets/'+hashlib.sha256(rel.encode()).hexdigest()[:24]
    @app.get('/api/products/{sku}/studio')
    def state(sku: str):
        if sku not in products(): raise HTTPException(404,'Không tìm thấy SKU')
        src=source(sku)
        previews=[dict(row,url=asset_url(root/row['path'])) for row in read().values() if row['sku']==sku and (root/row['path']).is_file()]
        all_assets=assets()
        backgrounds=[dict(id=i,name=p.name,url=asset_url(p)) for i,(p,rel) in all_assets.items() if '/5_Studio_Backgrounds/' in '/'+rel and p.suffix.lower()!='.pdf']
        backgrounds.sort(key=lambda a:(a['name']!='BIS_BACKDROP_1254.png',a['name']))
        references=[dict(name=p.name,url=asset_url(p)) for p,rel in all_assets.values() if '/6_Final_Composites/' in '/'+rel and p.suffix.lower()!='.pdf']
        references.sort(key=lambda a:(not a['name'].startswith(sku),a['name']))
        previews.sort(key=lambda row:row.get('created_at',''),reverse=True)
        last=json.loads(attempts.read_text(encoding='utf-8')).get(sku) if attempts.exists() else None
        return dict(source_url=asset_url(src) if src else None, backgrounds=backgrounds,references=references[:24],previews=previews[:12],last_attempt=last)
    @app.post('/api/products/{sku}/studio/package')
    def package(sku: str, body: DraftBody):
        """Local download for web editing when API quota is unavailable."""
        import io,zipfile
        from studio_ai import image_edit_prompt
        with lock:
            if sku not in products(): raise HTTPException(404,'Không tìm thấy SKU')
            src=source(sku);bg=assets().get(body.background)
            if src is None: raise HTTPException(422,'Xác nhận nguồn trước')
            if not bg or '/5_Studio_Backgrounds/' not in '/'+bg[1]: raise HTTPException(422,'Chọn nền hợp lệ')
            refs=selected_references(body.reference)
            history=[json.loads(e['content']).get('feedback','') for e in memory.events() if e.get('key')=='image-feedback:'+sku][-8:]
            buf=io.BytesIO()
            with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as archive:
                archive.write(src,'01_original'+src.suffix)
                archive.write(bg[0],'02_background'+bg[0].suffix)
                for i,path in enumerate(refs): archive.write(path,f'03_reference_{i}'+path.suffix)
                archive.writestr('PROMPT.txt',image_edit_prompt('Create a truthful product studio image. SKU: '+sku,history).replace('original, background, previous draft, optional approved reference.','original, background, optional approved reference.'))
                archive.writestr('README.txt','Upload original, background and reference to your web image editor with PROMPT.txt. No previous draft is included in this package. Inspect every word and product detail before use. This download does not create or approve an image.')
            return Response(buf.getvalue(),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="bis-image-inputs.zip"'})
    @app.post('/api/products/{sku}/studio/draft')
    def draft(sku: str, body: DraftBody):
        with lock:
            if sku not in products(): raise HTTPException(404,'Không tìm thấy SKU')
            src=source(sku)
            if src is None: raise HTTPException(422,'Xác nhận ảnh nguồn trước khi ghép')
            asset=assets().get(body.background)
            if not asset or '/5_Studio_Backgrounds/' not in '/'+asset[1]: raise HTTPException(422,'Chọn nền studio hợp lệ')
            refs=selected_references(body.reference)
            source_hash=hashlib.sha256(src.read_bytes()).hexdigest()
            ident=secrets.token_hex(12)
            target=root/'Google_Drive_Storage'/'5_Draft_Previews'/(safe_name(sku)+'_'+ident+'.png')
            try:
                if body.mode=='quick':
                    result=studio_draft(src,asset[0],target,remove_white=body.remove_white,allow_low_resolution=True)
                    result['engine']='quick'
                else:
                    from studio_ai import edit_image
                    history=[e['content'] for e in memory.events() if e.get('key')=='image-feedback:'+sku][-8:]
                    result=edit_image(src,asset[0],src,refs,'Create a large, well-lit truthful product image; product occupies about 75% of frame. Preserve exact lettering.',history,target)
            except Exception as exc:
                failed(sku,exc)
            if source(sku)!=src or hashlib.sha256(src.read_bytes()).hexdigest()!=source_hash:
                raise HTTPException(409,'Nguồn đã thay đổi trong khi xử lý; chọn lại nguồn')
            row=dict(result,id=ident,sku=sku,created_at=datetime.now(timezone.utc).isoformat(),reference=body.reference,path=str(target.relative_to(root)),source_path=str(src.relative_to(root)),sha256=hashlib.sha256(target.read_bytes()).hexdigest())
            rows=read();rows[ident]=row;atomic_json(ledger,rows)
            memory.append('update',json.dumps(row,ensure_ascii=False),source='Studio draft; not approved')
            attempt(sku,status='SUCCEEDED',preview_id=ident)
            return row
    @app.post('/api/products/{sku}/studio/approve')
    def approve(sku: str, body: ApprovalBody):
        with lock:
            rows=read();row=rows.get(body.preview_id)
            if not row or row['sku']!=sku: raise HTTPException(404,'Không tìm thấy bản ghép của SKU')
            if not body.confirm: raise HTTPException(422,'Cần xác nhận đúng SKU, chữ, logo và chất lượng')
            path=root/row['path'];src=source(sku)
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=body.sha256 or row['sha256']!=body.sha256:
                raise HTTPException(409,'Ảnh đã thay đổi; tạo hoặc tải lại bản xem trước')
            if src is None or hashlib.sha256(src.read_bytes()).hexdigest()!=row['source_sha256']:
                raise HTTPException(409,'Ảnh nguồn đã thay đổi; tạo lại bản ghép')
            final=root/'Google_Drive_Storage'/'6_Final_Composites'/(safe_name(sku)+'_approved_'+body.sha256[:12]+'.png')
            final.parent.mkdir(parents=True,exist_ok=True)
            if not final.exists(): shutil.copy2(path,final)
            manifest_path=root/'Google_Drive_Storage'/'image_review_manifest.json'
            manifest=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
            manifest[sku]=dict(row,status='APPROVED',final_image=str(final),preview_image=str(path),approved_sha256=body.sha256)
            atomic_json(manifest_path,manifest)
            row['status']='APPROVED';rows[body.preview_id]=row;atomic_json(ledger,rows)
            memory.append('update',json.dumps(dict(sku=sku,sha256=body.sha256,status='APPROVED'),ensure_ascii=False),source='User approved studio image')
            return {'status':'APPROVED','url':asset_url(final)}

    @app.post('/api/products/{sku}/studio/retry')
    def retry(sku: str, body: RetryBody):
        from studio_ai import edit_image
        with lock:
            row=read().get(body.preview_id)
            if not row or row['sku']!=sku: raise HTTPException(404,'Không tìm thấy bản ảnh')
            previous=root/row['path']; src=source(sku)
            if not previous.is_file() or hashlib.sha256(previous.read_bytes()).hexdigest()!=body.sha256 or row['sha256']!=body.sha256:
                raise HTTPException(409,'Phiên bản ảnh đã thay đổi')
            if src is None or hashlib.sha256(src.read_bytes()).hexdigest()!=row['source_sha256']:
                raise HTTPException(409,'Nguồn đã thay đổi; chọn lại ảnh nguồn')
            bg=assets().get(body.background)
            if not bg or '/5_Studio_Backgrounds/' not in '/'+bg[1]: raise HTTPException(422,'Chọn nền hợp lệ')
            references=selected_references(body.reference)
            history=[e['content'] for e in memory.events() if e.get('key')=='image-feedback:'+sku][-8:]
            feedback=body.feedback.strip()
            if len(feedback)<3: raise HTTPException(422,'Nhập góp ý cụ thể')
            memory.append('note',json.dumps(dict(preview_id=body.preview_id,sha256=body.sha256,feedback=feedback),ensure_ascii=False),key='image-feedback:'+sku,source='User image feedback')
            ident=secrets.token_hex(12)
            target=root/'Google_Drive_Storage'/'5_Draft_Previews'/(safe_name(sku)+'_'+ident+'.png')
            try: result=edit_image(src,bg[0],previous,references,feedback,history,target)
            except Exception as exc:
                failed(sku,exc)
            if source(sku)!=src or hashlib.sha256(src.read_bytes()).hexdigest()!=row['source_sha256']:
                raise HTTPException(409,'Nguồn thay đổi khi AI xử lý; chưa lưu kết quả')
            result.update(id=ident,sku=sku,created_at=datetime.now(timezone.utc).isoformat(),reference=body.reference,path=str(target.relative_to(root)),source_path=str(src.relative_to(root)),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),parent_id=body.preview_id,feedback=feedback)
            rows=read();rows[ident]=result;atomic_json(ledger,rows)
            attempt(sku,status='SUCCEEDED',preview_id=ident)
            return result
