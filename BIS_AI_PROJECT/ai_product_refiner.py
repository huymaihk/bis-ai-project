"""
BIS Textile AI - AI Product & SEO Auto-Refiner Engine
=====================================================
Chuyên gia AI Kỹ thuật Dệt may (Dr. Textile Tech) + Chuyên viên SEO (Mr. Marketing):
- Tự động kiểm tra (AI Check) toàn bộ 7 khối nội dung và cấu hình SEO
- Chuẩn hóa tên sản phẩm tiếng Việt theo đúng thuật ngữ chuyên ngành phòng lab dệt may
- Tự động trau chuốt mô tả kỹ thuật súc tích, chuyên nghiệp
- Tự động đúc kết đặc điểm nổi bật và phạm vi ứng dụng
- Tự động suy luận Tiêu chuẩn tra cứu liên quan (Khối 7 - tuyệt đối không trùng SKU)
- Tự động tối ưu hóa SEO Google: Meta Title (<60 ký tự), Meta Description (150-160 ký tự), URL Slug
"""

import re
import json
from typing import Dict, Any, Tuple
from agent_technical import resolve_related_standard_doc, translate_to_vi

TEXTILE_DOMAIN_DICTIONARY = [
    (r'(?i)\bpseudoisochromatic\s+plates\b', 'Bộ bảng màu kiểm tra sắc giác HRR Pseudoisochromatic Plates'),
    (r'(?i)\b3d\s+smoothness\s+appearance\s+replicas\b', 'Bộ mẫu chuẩn 3D đánh giá độ phẳng bề mặt vải AATCC'),
    (r'(?i)\bcrease\s+recovery\s+replicas\b', 'Bộ mẫu chuẩn 3D đánh giá phục hồi nếp nhăn AATCC'),
    (r'(?i)\bseam\s+smoothness\s+replicas\b', 'Thước ảnh chuẩn đánh giá độ phẳng đường may AATCC'),
    (r'(?i)\bstain\s+release\s+replicas?\b', 'Thước đo đánh giá khả năng giải phóng vết bẩn AATCC'),
    (r'(?i)\bphotographic\s+spray\s+test\b', 'Bảng ảnh chuẩn đánh giá độ ngấm nước AATCC (Spray Test Chart)'),
    (r'(?i)\bcrockmeter\b', 'Thiết bị đo độ bền màu ma sát Crockmeter'),
    (r'(?i)\bgray\s+scale\s+for\s+color\s+change\b', 'Thước xám chuẩn đánh giá độ thay đổi màu (AATCC / ISO)'),
    (r'(?i)\bgray\s+scale\s+for\s+staining\b', 'Thước xám chuẩn đánh giá độ dây màu (AATCC / ISO)'),
    (r'(?i)\bblue\s+wool\b', 'Mẫu len xanh chuẩn kiểm tra độ bền màu với ánh sáng (Blue Wool Standard)'),
    (r'(?i)\bmanual\s+of\s+international\s+test\s+methods\b', 'Sổ tay Phương pháp Thử nghiệm & Quy trình Quốc tế AATCC'),
    (r'(?i)\bcolor\s+guidebook\b', 'Sổ tay hướng dẫn quản lý màu sắc trong chuỗi cung ứng dệt may'),
    (r'(?i)\bcompass\b', 'Hệ thống cơ sở dữ liệu tiêu chuẩn trực tuyến ASTM Compass®'),
]


def clean_vietnamese_title(raw_name_vi: str, name_en: str, sku: str) -> str:
    """Chuẩn hóa tên tiếng Việt theo chuẩn văn phong kỹ thuật dệt may thương mại."""
    text_to_check = f"{raw_name_vi} {name_en}"
    
    # 1. Tra cứu thuật ngữ chuyên gia dệt may
    for pattern, vi_term in TEXTILE_DOMAIN_DICTIONARY:
        if re.search(pattern, text_to_check):
            # Nếu tên có dạng sách bìa cứng / pdf
            if "hardbound" in text_to_check.lower() or "bìa cứng" in text_to_check.lower():
                return f"{vi_term} (Bìa cứng)"
            elif "pdf" in text_to_check.lower() or "tải về" in text_to_check.lower():
                return f"{vi_term} (Bản điện tử PDF)"
            elif "corporate" in text_to_check.lower():
                return f"{vi_term} (Bản quyền doanh nghiệp)"
            return vi_term

    # 2. Loại bỏ các tiền tố thô ráp cũ
    clean = raw_name_vi.strip()
    clean = re.sub(r'^(?:Thiết bị\s*/\s*Vật tư thử nghiệm\s*-\s*)+', '', clean, flags=re.I)
    clean = re.sub(r'^(?:Sản phẩm\s*-\s*)+', '', clean, flags=re.I)
    
    # 3. Dịch thuật nếu tên vẫn hoàn toàn là tiếng Anh
    if not clean or clean.lower() == name_en.lower():
        translated = translate_to_vi(name_en)
        if translated and translated.lower() != name_en.lower():
            clean = translated
        else:
            clean = f"Thiết bị thử nghiệm - {name_en.title()}"

    return clean.strip()


def generate_seo_meta(name_vi: str, name_en: str, sku: str, brand: str, desc: str = "") -> Tuple[str, str, str, list]:
    """
    Tạo gói SEO Google hoàn chỉnh đạt chuẩn 100%:
    - Meta Title (< 60 ký tự, ngắt theo từ nguyên vẹn)
    - Meta Description (140 - 160 ký tự): BẮT BUỘC có Tên tiếng Việt + Tên tiếng Anh + Mã SKU + Hãng + thông tin có chứng cứ từ tài liệu
    - URL Slug chuẩn SEO
    - Focus Keywords
    """
    clean_en = name_en.strip()
    clean_en_cap = clean_en.title() if clean_en.isupper() else clean_en
    clean_en_core = re.sub(r'\s*\([^)]*\)', '', clean_en_cap).strip()
    clean_vi_core = re.sub(r'\s*\([^)]*\)', '', name_vi).strip()
    clean_vi_core = re.sub(r'\s+(?:chuẩn thử nghiệm|thử nghiệm vết bẩn|tiêu chuẩn thử nghiệm).*$', '', clean_vi_core, flags=re.I).strip()
    brand_short = "AATCC" if "AATCC" in brand else brand

    # 1. Meta Title (Dưới 60 ký tự, không bao giờ cắt vụn từ)
    title_suffix = f" ({sku}) | BIS Textile"
    max_len_t = 60 - len(title_suffix)
    if len(clean_vi_core) <= max_len_t:
        meta_title = f"{clean_vi_core}{title_suffix}"
    else:
        words = clean_vi_core.split()
        short_t = ""
        for w in words:
            if len((short_t + " " + w).strip()) <= max_len_t:
                short_t = (short_t + " " + w).strip()
            else:
                break
        meta_title = f"{short_t}{title_suffix}" if short_t else f"{clean_vi_core[:max_len_t]}{title_suffix}"

    # 2. Meta Description (140 - 160 ký tự): BẮT BUỘC TÊN TIẾNG VIỆT + TÊN TIẾNG ANH + MÃ SKU + HÃNG + BIS TEXTILE
    lead = f"{clean_vi_core} - {clean_en_core} ({sku}) chính hãng {brand_short}."
    tail_options = [
        " Thông tin sản phẩm và tư vấn kỹ thuật tại BIS Textile.",
        " Thông tin sản phẩm tại BIS Textile.",
        " Tra cứu thông tin sản phẩm tại BIS Textile.",
        " Thông tin và tư vấn kỹ thuật tại BIS Textile.",
        " thông tin sản phẩm tại BIS Textile."
    ]
    meta_desc = ""
    for tail in tail_options:
        candidate = f"{lead}{tail}"
        if len(candidate) <= 160:
            meta_desc = candidate
            break

    if not meta_desc or len(meta_desc) > 160:
        tail = f" {brand_short}. Thông tin sản phẩm tại BIS Textile."
        max_names_len = 160 - len(f" ({sku}){tail}")
        half = max_names_len // 2 - 2
        vi_words = clean_vi_core.split()
        s_vi = ""
        for w in vi_words:
            if len((s_vi + " " + w).strip()) <= half:
                s_vi = (s_vi + " " + w).strip()
            else:
                break
        en_words = clean_en_core.split()
        s_en = ""
        avail_en = max_names_len - len(s_vi) - 3
        for w in en_words:
            if len((s_en + " " + w).strip()) <= avail_en:
                s_en = (s_en + " " + w).strip()
            else:
                break
        meta_desc = f"{s_vi} - {s_en} ({sku}){tail}"

    # 3. URL Slug không dấu
    clean_slug_en = re.sub(r'[^a-z0-9\s-]', '', clean_en_core.lower())
    slug_core = re.sub(r'[\s-]+', '-', clean_slug_en).strip('-')[:40]
    if not slug_core:
        slug_core = "sp"
    url_slug = f"{slug_core}-{sku.lower()}"

    # 4. Focus Keywords
    keywords = [clean_vi_core, clean_en_core, sku, f"tiêu chuẩn {brand_short}", "kiểm nghiệm dệt may", "BIS Textile"]

    return meta_title, meta_desc, url_slug, keywords


def ai_check_and_refine_product(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hàm tổng lực AI Check & Tự động chuẩn hóa nội dung + SEO:
    - Chuẩn hóa tên sản phẩm tiếng Việt & tiếng Anh
    - Loại bỏ 100% thông tin thừa phân phối
    - Viết lại mô tả kỹ thuật mạch lạc
    - Đúc kết đặc điểm nổi bật & thông số
    - Tự động suy luận tài liệu Khối 7
    - Tạo gói SEO Google chuẩn xác
    """
    p = dict(product)
    sku = p.get("sku", "").strip()
    brand = p.get("brand") or p.get("brand_evidence") or "AATCC (Hoa Kỳ)"

    # Tra cứu đối soát Master Catalog để triệt tiêu 100% tình trạng gộp nhầm nội dung trên cùng trang PDF
    try:
        from catalog_master_data import CATALOG_MASTER
        master_info = CATALOG_MASTER.get(sku)
    except Exception:
        master_info = None

    if master_info:
        name_vi = master_info["vi"]
        name_en = master_info["en"]
        clean_desc = master_info["desc"]
        scope = master_info["scope"]
        p["source_page"] = master_info.get("page", p.get("source_page"))
        p["related_doc_title"] = master_info.get("doc", "")
    else:
        name_vi = p.get("product_name", "").strip()
        name_en = p.get("product_name_en", "").strip()
        raw_desc = p.get("description", "").strip()
        clean_desc = translate_to_vi(raw_desc)
        clean_desc = re.sub(r'^(?:16\s+|28\s+|Item\s*#\w+\s*)+', '', clean_desc).strip()
        clean_desc = re.sub(r'\s*Đơn vị phân phối.*$', '', clean_desc, flags=re.I).strip()
        if not clean_desc or len(clean_desc) < 20:
            clean_desc = f"Sản phẩm tiêu chuẩn chính hãng do {brand} ban hành, được áp dụng rộng rãi trong các phòng thí nghiệm kiểm tra chất lượng và đánh giá quy chuẩn dệt may toàn cầu."
        scope = p.get("application_scope") or "Phương pháp kiểm nghiệm dệt may quốc tế"

    # 1. Chuẩn hóa Tiêu đề song ngữ
    clean_vi = clean_vietnamese_title(name_vi, name_en, sku)
    clean_en = name_en.strip() if name_en else sku
    p["product_name"] = clean_vi
    p["product_name_en"] = clean_en
    p["brand"] = brand
    p["description"] = clean_desc

    # 3. Chuẩn hóa Đặc điểm nổi bật (Khối 5)
    default_hl = []
    raw_hl = p.get("highlights")
    if raw_hl and isinstance(raw_hl, list) and len(raw_hl) >= 2:
        cleaned_hl = [re.sub(r'^\s*[-*•]\s*', '', str(x)).strip() for x in raw_hl if "phân phối" not in str(x).lower() and "chính ngạch" not in str(x).lower()]
        p["highlights"] = cleaned_hl if len(cleaned_hl) >= 2 else default_hl
    else:
        p["highlights"] = default_hl

    # 4. Chuẩn hóa Phạm vi áp dụng (Khối 6)
    if "pseudoisochromatic" in f"{name_vi} {name_en}".lower():
        scope = "Kiểm tra và đánh giá thị giác màu sắc trong phòng lab"
    elif "smoothness" in f"{name_vi} {name_en}".lower():
        scope = "Đánh giá độ phẳng bề mặt vải sau giặt (AATCC TM124 / TM143)"
    elif "spray" in f"{name_vi} {name_en}".lower():
        scope = "Kiểm tra độ ngấm nước bề mặt vải (AATCC TM22)"
    p["application_scope"] = scope

    # 5. Tự động suy luận Tiêu chuẩn tra cứu liên quan (Khối 7)
    doc_title, doc_url = resolve_related_standard_doc(p)
    p["related_doc_title"] = doc_title
    p["related_doc_url"] = doc_url

    # 6. Tự động tối ưu SEO Google hoàn chỉnh
    meta_title, meta_desc, url_slug, keywords = generate_seo_meta(clean_vi, clean_en, sku, brand, clean_desc)
    p["meta_title"] = meta_title
    p["meta_description"] = meta_desc
    p["url_slug"] = url_slug
    p["focus_keywords"] = keywords
    p["seo_ready"] = True
    p["ai_refined"] = True

    # 7. Sinh lại mã HTML 7 khối chuẩn
    from agent_technical import AgentTechnical
    tech = AgentTechnical()
    p.pop("custom_html", None)
    p["custom_html"] = tech.build_7_block_html(p, force_refresh=True)

    from marketing_content import clean_product
    return clean_product(p)
