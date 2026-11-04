"""Deterministic content contract and evidence-aware matching for BIS."""
import hashlib
import html
import json
import re
import unicodedata
from urllib.parse import urlparse
from bs4 import BeautifulSoup

VERSION = "bis-quality-2"

def plain(value):
    return BeautifulSoup(str(value or ""), "html.parser").get_text(" ", strip=True)

def token_present(code, text):
    return bool(code and re.search(r"(?<![A-Za-z0-9])"+re.escape(str(code).strip())+r"(?![A-Za-z0-9])", str(text or ""), re.I))

def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()

def match_product(product, items):
    """Only identity evidence is MATCH. Mentions, core codes and names need review."""
    sku = str(product.get("sku") or "").strip().upper()
    if not sku:
        return {"state":"REVIEW", "reason":"Thiếu SKU", "url":"", "id":None}
    reviews=[]
    name = plain(product.get("product_name_en")).casefold()
    for item in items:
        url=item.get("url") or "/products/"+str(item.get("handle") or "")
        skus=[str(x).strip().lstrip("#").upper() for x in (item.get("variants_skus") or [])]
        variants=item.get("variants") or []
        skus.extend(str(x.get("sku") or "").strip().lstrip("#").upper() for x in variants if isinstance(x,dict))
        identity=" ".join(str(item.get(k) or "") for k in ("title","handle"))
        variant_titles=" ".join(str(x.get("title") or "") for x in variants if isinstance(x,dict))
        tags=item.get("tags") or []
        tags=tags if isinstance(tags,list) else tags.split(",")
        if sku in skus or token_present(sku,identity) or any(sku==str(t).strip().upper() for t in tags):
            return {"state":"MATCH","reason":"Khớp SKU trong thông tin định danh","url":url,"id":item.get("id")}
        content=plain(item.get("body_html"))+" "+str(item.get("body_plain") or "")
        core=re.sub(r"[A-Z]+$","",sku)
        if (token_present(sku,content+" "+variant_titles)
            or (len(core)>=5 and token_present(core,identity+" "+content))
            or (len(name.split())>=3 and name in plain(identity+" "+content).casefold())):
            reviews.append({"state":"REVIEW","reason":"Chỉ thấy mã/tên liên quan; cần đối chiếu biến thể, phụ kiện",
                            "url":url,"id":item.get("id")})
    return reviews[0] if reviews else {"state":"NO_MATCH","reason":"Chưa thấy định danh trùng trong dữ liệu đã đọc","url":"","id":None}

def brand(product):
    return str(product.get("brand") or product.get("brand_evidence") or "").strip()

def spec_items(product):
    raw=product.get("specifications") or {}
    pairs=list(raw.items()) if isinstance(raw,dict) else []
    fields={"material":"Thành phần","color":"Màu sắc","width_cm":"Khổ rộng (cm)",
            "weight_gsm":"Định lượng (g/m²)","pattern":"Kiểu dệt","finish":"Hoàn tất"}
    pairs.extend((label,product[k]) for k,label in fields.items() if product.get(k) not in (None,"","N/A"))
    return [(plain(k),plain(v)) for k,v in pairs if str(k).strip().casefold() not in
            {"unit","đơn vị tính","source_page","trang nguồn tài liệu"} and v not in (None,"")]

def render_product(product):
    """Seven sections, escaped values, no inferred specs/origin/certificates."""
    esc=lambda x:html.escape(str(x or ""))
    sku=str(product.get("sku") or "")
    title=str(product.get("product_name") or "")
    vendor=brand(product)
    if not token_present(sku,title):
        title+=" "+sku
    if vendor and vendor.casefold() not in title.casefold():
        title+=" "+vendor
    description=esc(product.get("description"))
    specs=spec_items(product)
    if len(specs)<2 and specs:
        description+="<p>"+esc(specs[0][0])+": "+esc(specs[0][1])+"</p>"
    highlights=product.get("highlights") or []
    if isinstance(highlights,str):
        highlights=highlights.splitlines()
    features="".join("<li>✨ "+esc(x)+"</li>" for x in highlights if str(x).strip())
    table=""
    if len(specs)>=2:
        table='<table style="width:100%;border-collapse:collapse">'
        for key,value in specs:
            table+='<tr><td style="width:39%;background:#f8fafc;padding:10px;border:1px solid #cbd5e1">'+esc(key)+'</td><td style="width:61%;padding:10px;border:1px solid #cbd5e1">'+esc(value)+"</td></tr>"
        table+="</table>"
    links=[]
    for doc in product.get("related_documents") or []:
        if not isinstance(doc,dict):
            continue
        url=str(doc.get("url") or "")
        if urlparse(url).scheme in {"https","http"}:
            links.append('<a href="'+esc(url)+'" rel="noopener noreferrer" target="_blank">'+esc(doc.get("title") or url)+"</a>")
    body=[
        '<h1 style="font-size:20px;color:#0f172a">'+esc(title.strip())+"</h1>",
        '<h2 style="font-size:15px;color:#0284c7">'+esc(str(product.get("product_name_en") or "").upper())+"</h2>",
        "<p>Hãng sản xuất / Tổ chức: "+esc(vendor or "Chưa có chứng cứ")+"</p>",
        "<div>"+description+"</div>",
        "<ul>"+features+"</ul>",
        table,
        "<div>"+"<br>".join(links)+"</div>",
    ]
    return '<div class="bis-product-card" style="background:white;color:#334155;padding:24px;font-family:Segoe UI,sans-serif;line-height:1.6">'+"".join(
        f'<section data-bis-block="{i}">{value}</section>' for i,value in enumerate(body,1))+"</div>"

def validate_product(product, source_text=None):
    errors=[]
    for key in ("sku","product_name","product_name_en","description","evidence_quote"):
        if not str(product.get(key) or "").strip():
            errors.append("Thiếu "+key)
    page=product.get("source_page")
    if not str(page or "").isdigit() or int(page or 0)<1:
        errors.append("Trang nguồn không hợp lệ")
    if not brand(product):
        errors.append("Thiếu chứng cứ hãng")
    if source_text is None:
        errors.append("Chưa đối chiếu tài liệu gốc")
    else:
        normalize=lambda s:re.sub(r"\s+"," ",str(s)).strip().casefold()
        if not token_present(product.get("sku"),source_text):
            errors.append("Trang nguồn không chứa đúng SKU")
        quote=normalize(product.get("evidence_quote") or "")
        if len(quote)<10 or quote not in normalize(source_text):
            errors.append("Trích dẫn chưa khớp tài liệu gốc")
    text=plain(product.get("custom_html") or render_product(product))
    if re.search(r"đơn vị phân phối|chính ngạch|trang nguồn tài liệu|đơn vị tính",text,re.I):
        errors.append("Nội dung chứa thông tin bị loại khỏi bài")
    if re.search(r"CO\s*/\s*CQ|chính hãng|ủy quyền",text,re.I) and not product.get("certificate_evidence"):
        errors.append("Cam kết thương mại thiếu chứng cứ")
    markup=product.get("custom_html") or render_product(product)
    soup=BeautifulSoup(markup,"html.parser")
    if [x.get("data-bis-block") for x in soup.select("[data-bis-block]")]!=list(map(str,range(1,8))):
        errors.append("HTML chưa đủ cấu trúc 7 khối")
    if soup.select("script,iframe,object") or re.search(r"\bon\w+\s*=|javascript:",markup,re.I):
        errors.append("HTML chứa mã không được phép")
    return {"passed":not errors,"errors":errors,"version":VERSION}

def seo_draft(product):
    """Constrained draft; length conflicts remain visible, never silently lose SKU/name."""
    sku=str(product.get("sku") or "")
    vi=plain(product.get("product_name"))
    en=plain(product.get("product_name_en"))
    vendor=plain(brand(product))
    meta=f"{vi} - {en} ({sku}). {vendor}. Thông tin và tư vấn kỹ thuật tại BIS Textile."
    slug=unicodedata.normalize("NFKD",en+" "+sku).encode("ascii","ignore").decode().lower()
    slug=re.sub(r"[^a-z0-9]+","-",slug).strip("-")
    issues=[]
    if not 140<=len(meta)<=160:
        issues.append(f"Meta description dài {len(meta)} ký tự; cần biên tập về 140–160")
    return {"meta_title":f"{vi} {sku} | BIS Textile","meta_description":meta,
            "url_slug":slug,"focus_keywords":[x for x in (vi,en,sku) if x],
            "secondary_keywords":[],"selling_points":[],"target_audience":"",
            "_quality":{"state":"NEEDS_REVIEW","issues":issues,"version":VERSION}}
