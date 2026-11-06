"""Conservative text-first PDF extraction and exact, versioned page cache."""
import hashlib
import json
import copy
import re
from pathlib import Path
from persistent_memory import atomic_json

PIPELINE_VERSION='text-first-v1'

def parser_version():
    import pymupdf
    sources=[Path(__file__),Path(__file__).with_name('agent_technical.py'),Path(__file__).with_name('gemini_fallback.py')]
    data=b''.join(p.read_bytes() for p in sources)+str(pymupdf.VersionBind).encode()
    return PIPELINE_VERSION+':'+hashlib.sha256(data).hexdigest()

def page_input(page):
    text=page.get_text('text',sort=True)
    reason='TEXT_OK'
    if len(text.strip())<100 or sum(c.isalpha() for c in text)<50: reason='INSUFFICIENT_TEXT'
    elif '\ufffd' in text or '\x00' in text: reason='BROKEN_ENCODING'
    # Multiple text columns can mix product/spec associations; retain image context.
    blocks=[b for b in page.get_text('blocks') if len(b)>6 and b[6]==0 and len(str(b[4]).strip())>50]
    if reason=='TEXT_OK':
        for a in blocks:
            for b in blocks:
                overlap=min(a[3],b[3])-max(a[1],b[1])
                if overlap>20 and (a[2]+10<b[0] or b[2]+10<a[0]): reason='MULTI_COLUMN'
    image=None if reason=='TEXT_OK' else page.get_pixmap(matrix=__import__('pymupdf').Matrix(1.5,1.5)).tobytes('jpeg')
    return text,image,reason

def cached_extract(folder, pdf_hash, page, version, agent, image, total, text, *, force=False, image_fallback=None):
    prompt=agent._build_prompt(page,total,brand='AATCC') if hasattr(agent,'_build_prompt') else ''
    context_hash=hashlib.sha256((prompt+text).encode()).hexdigest()
    key=hashlib.sha256(json.dumps([pdf_hash,page,version,context_hash,image is not None],ensure_ascii=True).encode()).hexdigest()
    path=Path(folder)/(key+'.json')
    agent.last_input_fallback=False
    if not force and path.is_file():
        try:
            entry=json.loads(path.read_text(encoding='utf-8'))
            payload={k:entry[k] for k in ('rows','status')}
            digest=hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            if entry.get('sha256')==digest and entry['status'] in ('PARSED','EMPTY_VALID','NEEDS_REVIEW') and isinstance(entry['rows'],list) and (entry['rows'] or entry['status']=='EMPTY_VALID'):
                agent.last_extraction_status=entry['status']
                agent.last_input_fallback=False
                return copy.deepcopy(entry['rows']),True
        except (ValueError,KeyError,OSError): pass
    agent.last_input_fallback=False
    rows=agent.extract_page(image,page,total,'AATCC',text)
    expected=set(re.findall(r'Item\s*#\s*(\d{4,6}[A-Za-z]?)(?![A-Za-z0-9])',text,re.I))
    found={str(row.get('sku','')) for row in rows} if isinstance(rows,list) else set()
    # Avoid spending another request when the provider has already reported quota/auth failure.
    error=str(getattr(agent,'last_extraction_error',''))
    bad = not isinstance(rows,list) or (not rows and getattr(agent,'last_extraction_status','')!='EMPTY_VALID') or not expected.issubset(found)
    if image is None and bad and image_fallback and not any(code in error for code in ('429','401','403')):
        agent.last_input_fallback=True
        rows=agent.extract_page(image_fallback(),page,total,'AATCC',text)
        found={str(row.get('sku','')) for row in rows} if isinstance(rows,list) else set()
    if image is None and expected and not expected.issubset(found):
        agent.last_extraction_status='FAILED'
        if not any(code in error for code in ('429','401','403')):
            agent.last_extraction_error='Chưa trích đủ mã Item trong văn bản PDF; cần đối chiếu nguồn'
        return [],False
    status=getattr(agent,'last_extraction_status','')
    if status in ('PARSED','EMPTY_VALID','NEEDS_REVIEW') and isinstance(rows,list) and (rows or status=='EMPTY_VALID'):
        payload={'rows':rows,'status':status}
        digest=hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        atomic_json(path,dict(payload,sha256=digest))
    return rows,False
