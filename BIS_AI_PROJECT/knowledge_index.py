"""Local document indexing with page provenance, no OCR claims."""
import hashlib
from pathlib import Path
import pymupdf
from persistent_memory import MemoryStore
from product_quality import token_present

def index_pdf(workspace,path,max_pages=100):
    root=Path(workspace).resolve()
    path=Path(path).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Tài liệu phải nằm trong dự án")
    store=MemoryStore(root)
    relative=path.relative_to(root).as_posix()
    # Hash identity is recorded as provenance, while path/page keys allow revisions.
    file_hash=hashlib.sha256(path.read_bytes()).hexdigest()
    count=0;scanned=[];seen=set()
    with pymupdf.open(path) as doc:
        total=len(doc)
        for n in range(min(total,max_pages)):
            text=doc[n].get_text().strip()
            if len(text)<10:
                scanned.append(n+1)
                continue
            for offset in range(0,len(text),3000):
                key=f"knowledge:{relative}:page:{n+1}:chunk:{offset//3000}"
                content=f"Nguồn {relative} | trang {n+1} | SHA256 {file_hash}\n"+text[offset:offset+3000]
                seen.add(key)
                store.revise(key,content,kind="source",actor="document_index",
                             source=f"{relative}#page={n+1}")
                count+=1
    for row in store.current():
        if row["key"].startswith("knowledge:"+relative+":") and row["key"] not in seen:
            heads=row["heads"]
            if not row["conflict"] and heads[0]["actor"]=="document_index" and file_hash not in heads[0]["content"]:
                store.revise(row["key"],"",kind="source",actor="document_index",source=relative,deleted=True)
    return {"chunks":count,"pages_indexed":min(total,max_pages),"total_pages":total,
            "pages_need_ocr":scanned,"state":"PARTIAL" if total>max_pages or scanned else "INDEXED",
            "note":"Đã lập chỉ mục văn bản; chưa thẩm định tính đúng của tài liệu."}
