import pymupdf
import re
import json
import uuid
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path("g:/My Drive/BIS_AI_PROJECT")
pdf_path = PROJECT_DIR / "catalogue_sample.pdf"
doc = pymupdf.open(str(pdf_path))

existing_cache_path = PROJECT_DIR / "extracted_products_cache.json"
products = []
if existing_cache_path.exists():
    try:
        products = json.load(open(existing_cache_path, encoding="utf-8"))
    except Exception:
        products = []

existing_skus = {p.get("sku") for p in products if p.get("sku")}

# Common textile title dictionary for accurate Vietnamese translations
TRANSLATIONS = {
    "DETERGENT": "Chất tẩy rửa chuẩn",
    "GRAY SCALE": "Thang xám chuẩn đánh giá độ bền màu",
    "STAINING": "Đánh giá dây màu / bám bẩn",
    "COLOR CHANGE": "Đánh giá thay đổi màu sắc",
    "CROCK": "Vải thử độ bền ma sát",
    "BLOTTER": "Giấy thấm thử nghiệm",
    "CHART": "Bảng biểu đồ chuẩn thử nghiệm",
    "MANUAL": "Sách hướng dẫn tiêu chuẩn quốc tế",
    "SUPPLEMENT": "Tài liệu kỹ thuật bổ trợ",
    "REVIEW": "Tạp chí nghiên cứu dệt may chuyên ngành",
    "JOURNAL": "Kỷ yếu nghiên cứu dệt may AATCC",
    "MICROSCOPY": "Bộ mẫu soi kính hiển vi",
    "WEIGHT": "Khối chuẩn kiểm định",
    "CARPET": "Mẫu thử thảm sàn",
    "BLEACH": "Thuốc thử độ bền tẩy trắng",
    "STAINLESS": "Vật liệu thép không gỉ thử nghiệm",
    "RING": "Vòng đệm thử nghiệm",
    "BALL": "Bi thép thử nghiệm độ bền",
}

def translate_title(en_title: str) -> str:
    en_upper = en_title.upper()
    prefix = ""
    for k, v in TRANSLATIONS.items():
        if k in en_upper:
            prefix = v
            break
    if not prefix:
        prefix = "Thiết bị / Vật tư thử nghiệm"
    return f"{prefix} - {en_title.title()}"

now = datetime.utcnow().isoformat() + "Z"
new_count = 0

for p_num in range(1, len(doc) + 1):
    text = doc[p_num - 1].get_text()
    if len(text.strip()) < 50:
        continue
    
    # Find all Item # patterns (e.g. Item #03000A, Item #28359C, #08336A)
    # Match patterns like: Item #12345A, Item #03000, Item#09616A, #08400A
    matches = re.finditer(r'(?:Item\s*#|#)\s*([0-9]{4,6}[A-Z]?)', text, re.IGNORECASE)
    found_items = []
    for m in matches:
        sku = m.group(1).upper()
        if sku not in existing_skus and sku not in found_items:
            found_items.append((sku, m.start()))

    # If no "Item #" found, look for standalone SKU patterns (5 digits + letter)
    if not found_items:
        raw_skus = re.findall(r'\b([0-9]{5}[A-Z])\b', text)
        for sku in raw_skus:
            sku = sku.upper()
            if sku not in existing_skus and sku not in [x[0] for x in found_items]:
                found_items.append((sku, text.find(sku)))

    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for sku, pos in found_items:
        # Extract title from lines before/after SKU
        title_candidates = [l for l in lines if len(l) > 6 and not l.isdigit() and "PAGE" not in l.upper() and "AATCC.ORG" not in l.upper() and "HTTP" not in l.upper()]
        en_title = title_candidates[0] if title_candidates else f"AATCC Product {sku}"
        if len(en_title) > 60:
            en_title = en_title[:60].strip()

        vi_title = translate_title(en_title)

        desc = text.replace("\n", " ").strip()[:350] + "..."

        unit = "bộ"
        if any(w in en_title.upper() for w in ["MANUAL", "BOOK", "SUPPLEMENT", "MAGAZINE"]):
            unit = "cuốn"
        elif any(w in en_title.upper() for w in ["FABRIC", "CLOTH", "PAPER"]):
            unit = "hộp"
        elif any(w in en_title.upper() for w in ["DETERGENT", "POWDER"]):
            unit = "thùng"

        rec = {
            "product_id": str(uuid.uuid4()),
            "status": "EXTRACTED_UNVERIFIED",
            "source_page": str(p_num),
            "product_name": vi_title,
            "product_name_en": en_title,
            "sku": sku,
            "brand": "AATCC (Hoa Kỳ)",
            "brand_evidence": "AATCC (Hoa Kỳ)",
            "category": "Vật tư & Tiêu chuẩn dệt may",
            "material": None,
            "color": None,
            "width_cm": None,
            "weight_gsm": None,
            "pattern": None,
            "finish": None,
            "description": desc,
            "price_vnd": None,
            "price_usd": None,
            "min_order_qty": "1",
            "unit": unit,
            "image_urls": None,
            "haravan_product_id": None,
            "created_at": now,
            "updated_at": now,
            "notes": f"Trích xuất trực tiếp từ Catalogue AATCC Trang {p_num}. SKU: {sku}."
        }
        products.append(rec)
        existing_skus.add(sku)
        new_count += 1
        print(f"  ✓ Bóc tách [Trang {p_num}] SKU: {sku} - {en_title}")

doc.close()

with open(existing_cache_path, "w", encoding="utf-8") as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

print(f"\n🎉 HOÀN THÀNH: Thêm mới {new_count} sản phẩm! Tổng số sản phẩm trong cache hiện tại: {len(products)}")

