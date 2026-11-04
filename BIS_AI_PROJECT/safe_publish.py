"""One guarded creation path. No delete or update operations."""
import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
import requests
from persistent_memory import atomic_json, MemoryStore, sync_configured
from product_quality import fingerprint, match_product, validate_product, render_product, brand

LOCK=threading.RLock()
API="https://apis.haravan.com/com"

def scan_store(headers, session=requests):
    items=[]
    for page in range(1,1001):
        response=session.get(API+"/products.json",headers=headers,params={"page":page,"limit":50},timeout=20)
        response.raise_for_status()
        data=response.json()
        if not isinstance(data.get("products"),list):
            raise ValueError("Invalid products response")
        rows=data["products"]
        items.extend(rows)
        if len(rows)<50:
            return items
    raise RuntimeError("Pagination incomplete")

def source_text(workspace, product):
    import pymupdf
    root=Path(workspace).resolve()
    source=Path(product.get("source_file") or "catalogue_sample.pdf")
    path=(root/source).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Source outside project")
    with pymupdf.open(path) as doc:
        number=int(product.get("source_page") or 0)
        if not 1<=number<=len(doc):
            raise ValueError("Invalid source page")
        return doc[number-1].get_text()

def _publish_one(product, workspace, *, enabled, headers, session=requests):
    """Persist SUBMITTING before POST. Ambiguous failures require reconciliation, never blind retry."""
    if not enabled:
        return {"sku":product.get("sku"),"status":"BLOCKED","error":"Chưa bật HARAVAN_PUSH_ENABLED"}
    if product.get("status")!="APPROVED":
        return {"sku":product.get("sku"),"status":"BLOCKED","error":"Chưa duyệt sản phẩm"}
    root=Path(workspace)
    sku=str(product.get("sku") or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}",sku):
        return {"sku":sku,"status":"BLOCKED","error":"SKU không hợp lệ"}
    try:
        report=validate_product(product,source_text(root,product))
    except Exception:
        report={"passed":False,"errors":["Không đọc được tài liệu nguồn"]}
    if not report["passed"]:
        return {"sku":sku,"status":"BLOCKED","error":"; ".join(report["errors"])}
    reviewed={k:v for k,v in product.items() if not k.startswith("_")}
    if product.get("_review_hash") != fingerprint(reviewed):
        return {"sku":sku,"status":"BLOCKED","error":"Nội dung đã đổi hoặc chưa duyệt đúng phiên bản"}
    if not 140<=len(product.get("meta_description") or "")<=160:
        return {"sku":sku,"status":"BLOCKED","error":"SEO cần 140–160 ký tự"}
    # Require human image approval tied to immutable file content.
    manifest_path=root/"Google_Drive_Storage"/"image_review_manifest.json"
    try:
        manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
        image=manifest[sku]
        image_path=Path(image["final_image"])
        import hashlib,base64
        digest=hashlib.sha256(image_path.read_bytes()).hexdigest()
        if image.get("status")!="APPROVED" or image.get("approved_sha256")!=digest:
            raise ValueError("Image not approved or changed")
        from PIL import Image
        with Image.open(image_path) as im:
            if im.size!=(1254,1254):
                raise ValueError("Image dimensions")
    except Exception:
        return {"sku":sku,"status":"BLOCKED","error":"Cần duyệt ảnh 1254×1254 và kiểm tra hash ảnh"}
    ledger_path=root/"Google_Drive_Storage"/"8_AI_Memory"/"publish_ledger.json"
    with LOCK:
        try:
            ledger=json.loads(ledger_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            ledger={}
        except (ValueError,OSError):
            return {"sku":sku,"status":"BLOCKED","error":"Không đọc được nhật ký xuất bản"}
        old=ledger.get(sku,{})
        if old.get("state")=="SUCCESS":
            return {"sku":sku,"status":"ALREADY_CREATED","haravan_id":old["haravan_id"]}
        memory=MemoryStore(root)
        durable=sync_configured(memory)
        if durable.get("state")!="synced":
            return {"sku":sku,"status":"BLOCKED","error":"Bộ nhớ xuất bản chưa đồng bộ bền vững; sửa kết nối Google trước"}
        remote_heads=memory.heads("publish:"+sku)
        if remote_heads and not old:
            return {"sku":sku,"status":"RECONCILE_REQUIRED","error":"Có lịch sử gửi từ phiên/máy khác; đối soát trước khi tạo mới"}
        try:
            live=scan_store(headers,session)
        except Exception as exc:
            return {"sku":sku,"status":"BLOCKED","error":"Đối soát live chưa hoàn tất: "+type(exc).__name__}
        match=match_product(product,live)
        if match["state"]!="NO_MATCH":
            return {"sku":sku,"status":"BLOCKED","error":match["reason"],"match":match}
        if old.get("state") in {"SUBMITTING","UNCERTAIN"}:
            return {"sku":sku,"status":"RECONCILE_REQUIRED","error":"Lần gửi trước chưa rõ kết quả; kiểm tra Haravan trước khi thử lại"}
        ledger[sku]={"state":"SUBMITTING","input_hash":fingerprint(product),"at":datetime.now(timezone.utc).isoformat()}
        atomic_json(ledger_path,ledger)
        memory.revise("publish:"+sku,json.dumps(ledger[sku]),kind="update",actor="publisher",source="publish_checkpoint")
        if sync_configured(memory).get("state")!="synced":
            return {"sku":sku,"status":"RECONCILE_REQUIRED","error":"Chưa xác nhận lưu checkpoint; chưa gọi API tạo sản phẩm"}
        from PIL import Image
        import io
        image_buffer=io.BytesIO()
        with Image.open(image_path) as im:
            im.convert("RGB").save(image_buffer,format="JPEG",quality=95)
        payload={"product":{
            "title":product["product_name"]+" "+sku,
            "handle":"bis-"+sku.lower().replace(".","-"),
            "body_html":product.get("custom_html") or render_product(product),
            "vendor":brand(product),"product_type":product.get("category") or "",
            "published":False,
            "variants":[{"sku":sku,"price":str(product.get("price_vnd") or 0),
                         "inventory_management":None,"inventory_quantity":0}],
            "images":[{"attachment":base64.b64encode(image_buffer.getvalue()).decode(),"filename":sku+".jpg"}],
        }}
        try:
            response=session.post(API+"/products.json",headers=headers,json=payload,timeout=30)
            response.raise_for_status()
            created=response.json().get("product") or {}
            if not created.get("id") or created.get("published_at") or created.get("published") is True:
                raise ValueError("Unexpected create response")
            # Readback verifies that the returned ID exists and contains this SKU.
            verify=session.get(API+f"/products/{created['id']}.json",headers=headers,timeout=20)
            verify.raise_for_status()
            checked=verify.json().get("product") or {}
            if (str(checked.get("id"))!=str(created["id"]) or checked.get("published_at")
                or checked.get("published") is True or not checked.get("images") or not any(str(v.get("sku") or "").upper()==sku.upper() for v in checked.get("variants",[]))):
                raise ValueError("Readback mismatch")
            ledger[sku].update(state="SUCCESS",haravan_id=str(created["id"]))
            atomic_json(ledger_path,ledger)
            memory.revise("publish:"+sku,json.dumps(ledger[sku]),kind="update",actor="publisher",source="publish_checkpoint")
            synced=sync_configured(memory).get("state")
            return {"sku":sku,"status":"SUCCESS","haravan_id":str(created["id"]),"memory_sync":synced}
        except Exception as exc:
            ledger[sku].update(state="UNCERTAIN",error=type(exc).__name__)
            atomic_json(ledger_path,ledger)
            memory.revise("publish:"+sku,json.dumps(ledger[sku]),kind="update",actor="publisher",source="publish_checkpoint")
            sync_configured(memory)
            return {"sku":sku,"status":"RECONCILE_REQUIRED","error":type(exc).__name__}

def publish_batch(products, workspace):
    from config import HARAVAN_PUSH_ENABLED, HARAVAN_TOKEN, HARAVAN_SHOP
    headers={"Authorization":"Bearer "+HARAVAN_TOKEN,"Content-Type":"application/json","X-Haravan-Shop":HARAVAN_SHOP}
    return [publish_one(p,workspace,enabled=HARAVAN_PUSH_ENABLED,headers=headers) for p in products]



def publish_one(product,workspace,*,enabled,headers,session=requests):
    import os
    lock_dir=Path(workspace)/"Google_Drive_Storage"/"8_AI_Memory"
    lock_dir.mkdir(parents=True,exist_ok=True)
    lock=lock_dir/"publish.lock"
    try:
        fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:
        return {"sku":product.get("sku"),"status":"BLOCKED",
                "error":"Có tác vụ đăng đang chạy hoặc đã dừng bất thường; cần kiểm tra nhật ký trước"}
    try:
        os.close(fd)
        return _publish_one(product,workspace,enabled=enabled,headers=headers,session=session)
    finally:
        lock.unlink(missing_ok=True)
