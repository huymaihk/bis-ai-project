"""
BIS Textile AI - Agent Marketing (SEO & Content Research Department)
Responsible for:
- Textile SEO keyword research (AATCC, ISO, ASTM, Fabric Testing, QA/QC Lab)
- Bilingual SEO Meta Title, Meta Description, URL Slug generation
- Commercial e-commerce product pitch, Value propositions & Buyer persona targeting
- Social media snippets / Google Search Snippet preview
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from google import genai

from config import GEMINI_API_KEY, GEMINI_MODEL

class AgentMarketing:
    def __init__(self, workspace_dir: str | Path | None = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path(__file__).parent.resolve()
        self.cache_dir = self.workspace_dir / "marketing_cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def generate_seo_package(self, product: dict) -> dict:
        """
        Generate full SEO & Content package for a product.
        Includes:
        - Meta Title (< 60 chars)
        - Meta Description (150-160 chars)
        - Friendly URL Slug
        - Primary & Secondary SEO Keywords
        - E-commerce Selling Pitch (Lý do chọn mua)
        - Google Search Preview
        """
        sku = product.get("sku", "")
        name_vi = product.get("product_name", "")
        name_en = product.get("product_name_en", "")
        desc = product.get("description", "")
        category = product.get("category", "Tài liệu tiêu chuẩn")
        brand = product.get("brand_evidence", "AATCC (Hoa Kỳ)")

        cache_path = self.cache_dir / f"seo_{sku}.json"
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        prompt = f"""Bạn là Trưởng phòng SEO & Marketing của BIS Textile Việt Nam (nhà cung cấp thiết bị, tài liệu thử nghiệm dệt may hàng đầu).
Hãy lập kế hoạch SEO và nội dung bán hàng cho sản phẩm sau:

Mã SKU: {sku}
Tên tiếng Việt: {name_vi}
Tên tiếng Anh: {name_en}
Danh mục: {category}
Hãng sản xuất / Tổ chức: {brand}
Mô tả kỹ thuật: {desc}

Yêu cầu xuất ra JSON chính xác theo cấu trúc:
{{
  "meta_title": "Tiêu đề SEO ngắn gọn dưới 60 ký tự kèm mã {sku} và thương hiệu BIS Textile",
  "meta_description": "Mô tả SEO hấp dẫn từ 150-160 ký tự, chứa từ khóa chính, thúc đẩy click xem chi tiết",
  "url_slug": "slug-than-thien-khong-dau-co-sku",
  "focus_keywords": ["Từ khóa chính 1", "Từ khóa chính 2", "Từ khóa 3"],
  "secondary_keywords": ["Từ khóa ngách 1", "Từ khóa ngách 2"],
  "selling_points": [
    "Điểm bán hàng nổi bật 1 (Lợi ích cho phòng lab QA/QC)",
    "Điểm bán hàng nổi bật 2 (Độ tin cậy chính hãng có CO/CQ)",
    "Điểm bán hàng nổi bật 3 (Hỗ trợ kỹ thuật chuyên sâu từ BIS)"
  ],
  "target_audience": "Đối tượng khách hàng mục tiêu (ví dụ: Nhà máy dệt nhuộm, Phòng kiểm nghiệm dệt may, Chuyên viên QA/QC)"
}}
Chỉ trả về JSON thuần túy, không có thẻ markdown ```json.
"""
        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )
            raw = response.text.strip()
            if raw.startswith("```json"): raw = raw[7:]
            if raw.startswith("```"): raw = raw[3:]
            if raw.endswith("```"): raw = raw[:-3]
            data = json.loads(raw.strip())
        except Exception as e:
            # Fallback nếu API bận
            slug = name_en.lower().replace(" ", "-").replace("/", "-")
            slug = "".join(c for c in slug if c.isalnum() or c == "-")[:50]
            data = {
                "meta_title": f"{name_vi} ({sku}) | BIS Textile Việt Nam",
                "meta_description": f"Cung cấp chính ngạch {name_vi} mã {sku} từ {brand}. Tiêu chuẩn kiểm nghiệm dệt may quốc tế, đầy đủ CO/CQ và hỗ trợ kỹ thuật tại BIS Textile.",
                "url_slug": f"{slug}-{sku.lower()}",
                "focus_keywords": [name_vi, sku, f"tiêu chuẩn {brand}", "kiểm nghiệm dệt may"],
                "secondary_keywords": ["AATCC manual", "tài liệu QA dệt may", "BIS Textile"],
                "selling_points": [
                    "Ấn bản chính hãng chuẩn hóa quốc tế mới nhất",
                    "Đầy đủ chứng từ nguồn gốc CO/CQ và hóa đơn VAT",
                    "Tư vấn kỹ thuật kiểm nghiệm phòng lab chuyên sâu từ BIS Textile"
                ],
                "target_audience": "Trưởng phòng QA/QC dệt may, Kỹ thuật viên phòng thí nghiệm, Nhà máy may xuất khẩu"
            }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return data

